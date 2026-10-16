"""
ANGELA-MATRIX: [L5] [β] [B] [L3]
System discovery API — single endpoint returning all system state for UI consumption.

GET /system/discovery — deployment mode, backends, intents, memory, state summary
"""

import logging
import time
from typing import Any, Dict

from fastapi import APIRouter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/system", tags=["System Discovery"])

_start_time = time.time()


async def _discovery_deployment(result: Dict[str, Any]) -> None:
    """Fill result["deployment"] + result["web_search"] from the LLM authority config."""
    try:
        from core.config_loader import get_angela_config

        cfg = get_angela_config()
        llm_authority = cfg.get_authority("llm", {})
        deployment = llm_authority.get("deployment", {})
        result["deployment"] = {
            "mode": deployment.get("mode", "local"),
            "selection": deployment.get("selection", "available"),
        }
        # Web search
        ws = llm_authority.get("web_search", {})
        result["web_search"] = {
            "enabled": ws.get("enabled", True),
            "provider": ws.get("provider", "duckduckgo"),
        }
    except Exception as e:
        logger.warning("Config load failed: %s", e, exc_info=True)
        result["deployment"] = {"mode": "unknown", "selection": "unknown"}


async def _discovery_llm(result: Dict[str, Any]) -> None:
    """Fill result["llm"] with backend list + health from the live LLM service."""
    try:
        from services.angela_llm_service import get_llm_service

        llm_svc = await get_llm_service()
        backends_list = []
        for btype, bobj in getattr(llm_svc, "backends", {}).items():
            name = btype.name if hasattr(btype, "name") else str(btype)
            is_active = (
                getattr(llm_svc, "active_backend_type", None) is not None
                and btype == llm_svc.active_backend_type
            )
            backends_list.append(
                {
                    "name": name,
                    "active": is_active,
                    "type": getattr(bobj, "_backend_type", "unknown"),
                }
            )
        active = getattr(llm_svc, "active_backend_type", None)
        result["llm"] = {
            "available": getattr(llm_svc, "is_available", False),
            "mode": getattr(llm_svc, "llm_mode", "unknown"),
            "active": active.name if active is not None else None,
            "backends": backends_list,
        }
    except Exception as e:
        logger.warning("LLM service unavailable: %s", e, exc_info=True)
        result["llm"] = {"available": False, "mode": "unknown", "backends": []}


async def _discovery_intents(result: Dict[str, Any]) -> None:
    """Fill result["intents"] with configured intent names + count."""
    try:
        from core.config_loader import get_angela_config

        cfg = get_angela_config()
        intents = list(cfg.get_intents().keys())
        result["intents"] = {"count": len(intents), "names": intents}
    except Exception:
        result["intents"] = {"count": 0, "names": []}


async def _discovery_memory(result: Dict[str, Any]) -> None:
    """Fill result["memory"] with whether the chat service has a memory manager."""
    try:
        from api.lifespan import _get_chat_service

        service = await _get_chat_service()
        has_memory = hasattr(service, "memory_manager") and service.memory_manager is not None
        result["memory"] = {"initialized": has_memory}
    except Exception:
        result["memory"] = {"initialized": False}


async def _discovery_state(result: Dict[str, Any]) -> None:
    """Fill result["state"] with per-axis 8D state means rounded to 3 decimals."""
    try:
        from api.lifespan import _get_chat_service

        service = await _get_chat_service()
        sm = service.state_matrix
        state = {}
        for axis_name in ("alpha", "beta", "gamma", "delta", "epsilon", "theta"):
            ax = getattr(sm, axis_name, None)
            if ax and hasattr(ax, "values"):
                vals = ax.values
                avg = sum(vals.values()) / len(vals) if vals else 0.5
                state[axis_name] = round(avg, 3)
        result["state"] = state
    except Exception:
        result["state"] = {}


@router.get("/discovery")
async def system_discovery() -> Dict[str, Any]:
    """All-in-one system info for UI panels.

    Returns deployment mode, LLM backend list with health,
    intent count, memory status, and 8D state summary.
    """
    result: Dict[str, Any] = {
        "timestamp": time.time(),
        "uptime_seconds": int(time.time() - _start_time),
    }

    # ── Deployment config ──
    await _discovery_deployment(result)
    # ── LLM backends ──
    await _discovery_llm(result)
    # ── Intents ──
    await _discovery_intents(result)
    # ── Memory ──
    await _discovery_memory(result)
    # ── 8D State summary ──
    await _discovery_state(result)

    return result
