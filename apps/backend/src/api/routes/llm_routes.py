"""
ANGELA-MATRIX: [L5] [β] [B] [L3]
LLM management API — backend status and switching.

GET  /llm/status   — Backend list with health, active, stats
POST /llm/switch   — Switch active backend
"""

import logging
from typing import Any, Dict

from fastapi import APIRouter, Body

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/llm", tags=["LLM Management"])


async def _get_llm():
    """Get LLM service instance."""
    from services.angela_llm_service import get_llm_service

    return await get_llm_service()


@router.get("/status")
async def llm_status() -> Dict[str, Any]:
    """Return LLM backend status with health indicators."""
    try:
        llm_svc = await _get_llm()
        backends = []
        for btype, bobj in getattr(llm_svc, "backends", {}).items():
            name = btype.name if hasattr(btype, "name") else str(btype)
            is_active = (
                getattr(llm_svc, "active_backend_type", None) is not None
                and btype == llm_svc.active_backend_type
            )
            # Attempt health check (skip if event loop is running to avoid blocking)
            health = "unknown"
            try:
                import asyncio

                loop = asyncio.get_event_loop()
                if not loop.is_running():
                    health = "ok" if await bobj.check_health() else "fail"
            except Exception:
                pass

            backends.append(
                {
                    "name": name,
                    "active": is_active,
                    "health": health,
                    "type": getattr(bobj, "_backend_type", "unknown"),
                }
            )

        return {
            "available": getattr(llm_svc, "is_available", False),
            "mode": getattr(llm_svc, "llm_mode", "unknown"),
            "active": (
                llm_svc.active_backend_type.name
                if getattr(llm_svc, "active_backend_type", None)
                else None
            ),
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
        if dotted in _LLM_CONFIG_ENUMS:
            if value not in _LLM_CONFIG_ENUMS[dotted]:
                return {
                    "ok": False,
                    "error": f"Invalid {dotted}={value!r}. Allowed: {list(_LLM_CONFIG_ENUMS[dotted])}",
                }
        elif dotted in _LLM_CONFIG_RANGES:
            lo, hi = _LLM_CONFIG_RANGES[dotted]
            try:
                num = float(value)
            except (TypeError, ValueError):
                return {"ok": False, "error": f"Invalid {dotted}={value!r}: must be a number"}
            if not (lo <= num <= hi):
                return {
                    "ok": False,
                    "error": f"Invalid {dotted}={value!r}: must be within [{lo}, {hi}]",
                }
            value = int(num) if dotted != "settings.defaults.temperature" else num
        elif dotted in _LLM_CONFIG_BOOLS:
            if not isinstance(value, bool):
                return {"ok": False, "error": f"Invalid {dotted}={value!r}: must be true/false"}
        elif dotted in _LLM_CONFIG_STRS:
            if not isinstance(value, str) or not value.strip() or len(value) > 64:
                return {
                    "ok": False,
                    "error": f"Invalid {dotted}={value!r}: must be a non-empty string ≤64 chars",
                }
            value = value.strip()
        # dotted → nested patch
        node = patch
        parts = dotted.split(".")
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node[parts[-1]] = value

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
