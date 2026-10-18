"""
ANGELA-MATRIX: [L5] [β] [B] [L3]
LLM management API — backend status and switching.

GET  /llm/status         — Backend list with health, active, stats
POST /llm/switch         — Switch active backend
GET  /llm/config         — Effective settings subset (Desktop Settings prefill)
POST /llm/config         — Persist whitelisted settings to llm.user.yaml
GET  /llm/solution-rules — 規則沉澱層統計（rule store stats）
"""

import logging
from typing import Any, Dict, Optional, Tuple

from fastapi import APIRouter, Body

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/llm", tags=["LLM Management"])


async def _get_llm():
    """Get LLM service instance."""
    from services.angela_llm_service import get_llm_service

    return await get_llm_service()


def _llm_backend_category(llm_svc: Any, btype: Any) -> str:
    """Classify a backend as local/cloud using the router's own rule when available."""
    resolver = getattr(llm_svc, "backend_category", None)
    if resolver is not None:
        try:
            return str(resolver(btype))
        except Exception as exc:
            logger.debug("backend_category failed: %s", exc)
    value = str(getattr(btype, "value", btype)).lower()
    return "cloud" if value in {"openai", "anthropic", "google"} else "local"


def _llm_backend_health(llm_svc: Any, btype: Any) -> str:
    """Get backend health via the router's resolver when available."""
    resolver = getattr(llm_svc, "backend_health", None)
    if resolver is not None:
        try:
            return str(resolver(btype))
        except Exception as exc:
            logger.debug("backend_health failed: %s", exc)
    return "unknown"


@router.get("/status")
async def llm_status() -> Dict[str, Any]:
    """Return LLM backend status with health indicators."""
    try:
        llm_svc = await _get_llm()
        backends = []
        active_type = getattr(llm_svc, "active_backend_type", None)

        def _append(btype: Any, present: bool) -> None:
            name = btype.name if hasattr(btype, "name") else str(btype)
            backends.append(
                {
                    "name": name,
                    "available": present,
                    "active": active_type is not None and btype == active_type,
                    "health": _llm_backend_health(llm_svc, btype),
                    "type": _llm_backend_category(llm_svc, btype),
                }
            )

        for btype in getattr(llm_svc, "backends", {}):
            _append(btype, True)
        # Configured-but-pruned backends (failed the boot health check or were
        # demoted at runtime) used to vanish from this list entirely, so an
        # operator could not tell "never configured" from "configured, down".
        for btype in getattr(llm_svc, "_pruned_backends", {}):
            if btype not in getattr(llm_svc, "backends", {}):
                _append(btype, False)

        return {
            "available": getattr(llm_svc, "is_available", False),
            "mode": getattr(llm_svc, "llm_mode", "unknown"),
            "active": active_type.name if active_type else None,
            "backends": backends,
            "stats": getattr(llm_svc, "stats", {}),
        }
    except Exception as e:
        logger.warning("LLM status failed: %s", e, exc_info=True)
        return {"available": False, "mode": "unknown", "backends": [], "error": str(e)}


# Whitelist for persisted LLM settings (Desktop Settings → backend user.yaml).
# Anything outside this schema is rejected with 400 (no silent misconfig).
_LLM_CONFIG_ENUMS = {
    "deployment.mode": ("local", "local+llm", "llm", "auto"),
    "deployment.selection": ("available", "per-vendor"),
    "settings.llm_mode": ("standard", "auto"),
}
_LLM_CONFIG_RANGES = {
    "settings.defaults.temperature": (0.0, 2.0),
    "settings.defaults.max_tokens": (1, 8192),
    "settings.memory.max_history": (1, 100),
}
_LLM_CONFIG_BOOLS = (
    "web_search.enabled",
    "settings.enable_memory_enhancement",
)
_LLM_CONFIG_STRS = ("settings.preferred_backend",)


@router.get("/solution-rules")
async def llm_solution_rules_stats() -> Dict[str, Any]:
    """規則沉澱層統計（獨立於 LLM service — 供 ops/桌面即時監控）。"""
    try:
        from ai.rules import get_rule_store

        return {"ok": True, **get_rule_store().stats()}
    except Exception as exc:
        logger.warning("solution rule stats unavailable: %s", exc)
        return {"ok": False, "error": str(exc)}


def _get_path(d: Dict[str, Any], dotted: str):
    cur: Any = d
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


@router.get("/config")
async def llm_config_get() -> Dict[str, Any]:
    """Return the currently effective (merged) LLM settings subset.

    Used by the Desktop Settings panel to prefill fields with backend truth.
    """
    from core.system.config.tiered_loader import get_config

    merged = get_config("system/llm") or {}
    out: Dict[str, Any] = {}
    for dotted in (
        *_LLM_CONFIG_ENUMS.keys(),
        *_LLM_CONFIG_RANGES.keys(),
        *_LLM_CONFIG_BOOLS,
        *_LLM_CONFIG_STRS,
    ):
        val = _get_path(merged, dotted)
        if val is not None:
            out[dotted] = val
    return {"ok": True, "config": out, "restart_required": True}


def _validate_enum(dotted: str, value: Any) -> Optional[str]:
    """Validate enum membership; returns error message or None."""
    if dotted not in _LLM_CONFIG_ENUMS:
        return None
    if value not in _LLM_CONFIG_ENUMS[dotted]:
        return f"Invalid {dotted}={value!r}. Allowed: {list(_LLM_CONFIG_ENUMS[dotted])}"
    return None


def _validate_range(dotted: str, value: Any) -> Tuple[bool, Any, Optional[str]]:
    """Validate numeric range; returns (ok, normalized_value, error)."""
    if dotted not in _LLM_CONFIG_RANGES:
        return True, value, None
    lo, hi = _LLM_CONFIG_RANGES[dotted]
    try:
        num = float(value)
    except (TypeError, ValueError):
        return False, value, f"Invalid {dotted}={value!r}: must be a number"
    if not (lo <= num <= hi):
        return False, value, f"Invalid {dotted}={value!r}: must be within [{lo}, {hi}]"
    return True, (int(num) if dotted != "settings.defaults.temperature" else num), None


def _validate_bool(dotted: str, value: Any) -> Optional[str]:
    """Validate boolean type; returns error message or None."""
    if dotted not in _LLM_CONFIG_BOOLS:
        return None
    if not isinstance(value, bool):
        return f"Invalid {dotted}={value!r}: must be true/false"
    return None


def _validate_str(dotted: str, value: Any) -> Tuple[bool, Any, Optional[str]]:
    """Validate string type; returns (ok, normalized_value, error)."""
    if dotted not in _LLM_CONFIG_STRS:
        return True, value, None
    if not isinstance(value, str) or not value.strip() or len(value) > 64:
        return False, value, f"Invalid {dotted}={value!r}: must be a non-empty string ≤64 chars"
    return True, value.strip(), None


def _validate_config_value(dotted: str, value: Any) -> Tuple[bool, Any, Optional[str]]:
    """Validate a single config value; returns (ok, normalized_value, error_msg)."""
    err = _validate_enum(dotted, value)
    if err:
        return False, value, err
    ok, value, err = _validate_range(dotted, value)
    if not ok:
        return False, value, err
    err = _validate_bool(dotted, value)
    if err:
        return False, value, err
    return _validate_str(dotted, value)


def _set_nested(patch: Dict[str, Any], dotted: str, value: Any) -> None:
    """Insert a dotted key path into a nested dict patch."""
    node = patch
    parts = dotted.split(".")
    for part in parts[:-1]:
        node = node.setdefault(part, {})
    node[parts[-1]] = value


@router.post("/config")
async def llm_config_set(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    """Persist LLM settings to the user config layer (``llm.user.yaml``).

    Only whitelisted keys are accepted; anything else → 400 with the
    allowed-key list. Takes effect after backend restart (deployment/mode
    values are read at startup), except ``preferred_backend`` which is
    honoured on the next router init.
    """
    if not isinstance(payload, dict) or not payload:
        return {"ok": False, "error": "Body must be a non-empty object"}

    allowed = (
        set(_LLM_CONFIG_ENUMS)
        | set(_LLM_CONFIG_RANGES)
        | set(_LLM_CONFIG_BOOLS)
        | set(_LLM_CONFIG_STRS)
    )
    unknown = sorted(k for k in payload if k not in allowed)
    if unknown:
        return {
            "ok": False,
            "error": f"Unknown keys: {unknown}. Allowed: {sorted(allowed)}",
        }

    patch: Dict[str, Any] = {}
    for dotted, value in payload.items():
        ok, normalized, err = _validate_config_value(dotted, value)
        if not ok:
            return {"ok": False, "error": err}
        _set_nested(patch, dotted, normalized)

    from core.system.config.tiered_loader import write_user_config

    ok, msg = write_user_config("system/llm", patch)
    if not ok:
        return {"ok": False, "error": msg}
    logger.info("LLM user config updated via API: %s", sorted(payload.keys()))
    return {"ok": True, "updated": sorted(payload.keys()), "detail": msg, "restart_required": True}


@router.post("/switch")
async def llm_switch(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    """Switch active LLM backend.

    Body: {"backend": "ollama-llama3"}
    """
    backend_name = payload.get("backend", "")
    if not backend_name:
        return {"ok": False, "error": "Missing 'backend' field"}

    try:
        llm_svc = await _get_llm()
        for btype, bobj in getattr(llm_svc, "backends", {}).items():
            name = btype.name if hasattr(btype, "name") else str(btype)
            if backend_name.lower() in name.lower():
                llm_svc.active_backend = bobj
                llm_svc.active_backend_type = btype
                return {"ok": True, "switched_to": name}

        available = [
            btype.name if hasattr(btype, "name") else str(btype)
            for btype in getattr(llm_svc, "backends", {}).keys()
        ]
        return {"ok": False, "error": f"Backend '{backend_name}' not found", "available": available}
    except Exception as e:
        logger.warning("LLM switch failed: %s", e, exc_info=True)
        return {"ok": False, "error": str(e)}
