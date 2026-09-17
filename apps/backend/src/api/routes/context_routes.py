"""
ANGELA-MATRIX: [L5] [β] [B] [L3]
Context summary API — state matrix, memory, intents for UI panels.

GET /context/summary — Full context overview
"""

import logging
import time
from typing import Any, Dict

from fastapi import APIRouter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/context", tags=["Context"])


@router.get("/summary")
async def context_summary() -> Dict[str, Any]:
    """Return context overview: state matrix, memory status, intent list."""
    result: Dict[str, Any] = {"timestamp": time.time()}

    # ── 8D State Matrix ──
    try:
        from api.lifespan import _get_chat_service

        service = await _get_chat_service()
        sm = service.state_matrix
        state = {}
        for axis_name in ("alpha", "beta", "gamma", "delta", "epsilon", "theta"):
            ax = getattr(sm, axis_name, None)
            if ax and hasattr(ax, "values"):
                state[axis_name] = {k: round(v, 4) for k, v in ax.values.items()}
        result["state"] = state

        # Eta
        eta = service.eta_state
        if eta:
            result["eta"] = {
                "execution_count": eta.execution_count,
                "success_rate": round(eta.success_rate, 4),
                "structural_drift": round(eta.structural_drift, 4),
            }
    except Exception as e:
        logger.warning("State matrix unavailable: %s", e, exc_info=True)
        result["state"] = {}
        result["eta"] = None

    # ── Memory ──
    try:
        from api.lifespan import _get_chat_service

        service = await _get_chat_service()
        has_memory = hasattr(service, "memory_manager") and service.memory_manager is not None
        result["memory"] = {"initialized": has_memory}

        if has_memory:
            import asyncio

            try:
                loop = asyncio.get_event_loop()
                if not loop.is_running():
                    results = await service.memory_manager.query_core_memory(
                        keywords=["experience"], limit=5
                    )
                    result["memory"]["recent_count"] = len(results)
            except Exception:
                result["memory"]["recent_count"] = None
    except Exception:
        result["memory"] = {"initialized": False}

    # ── Intents ──
    try:
        from core.config_loader import get_angela_config

        cfg = get_angela_config()
        intents = cfg.get_intents()
        result["intents"] = {
            "count": len(intents),
            "names": list(intents.keys()),
        }
    except Exception:
        result["intents"] = {"count": 0, "names": []}

    # ── LLM quick status ──
    try:
        from services.angela_llm_service import get_llm_service

        llm_svc = await get_llm_service()
        result["llm"] = {
            "available": getattr(llm_svc, "is_available", False),
            "active": (
                llm_svc.active_backend_type.name
                if getattr(llm_svc, "active_backend_type", None)
                else None
            ),
            "mode": getattr(llm_svc, "llm_mode", "unknown"),
        }
    except Exception:
        result["llm"] = {"available": False}

    return result


@router.get("/memory/recent")
async def context_memory_recent(limit: int = 10) -> Dict[str, Any]:
    """Return recent core memories from HAM (real data, for MemoryViewer panel)."""
    try:
        from api.lifespan import _get_chat_service

        service = await _get_chat_service()
        mm = getattr(service, "memory_manager", None)
        if mm is None:
            return {
                "initialized": False,
                "memories": [],
                "hint": "Memory manager not initialized (install vector extras?)",
            }
        results = await mm.query_core_memory(limit=max(1, min(limit, 50)))
        memories = []
        for r in results:
            content = getattr(r, "content", None)
            meta = getattr(r, "metadata", None) or {}
            memories.append(
                {
                    "content": str(content)[:200] if content is not None else "",
                    "type": getattr(r, "data_type", None) or meta.get("type", ""),
                    "importance": float(meta.get("importance", 0.0) or 0.0),
                    "emotion": meta.get("emotion", ""),
                    "timestamp": meta.get("timestamp", None),
                }
            )
        return {"initialized": True, "memories": memories, "count": len(memories)}
    except Exception as e:
        logger.warning("Memory recent query failed: %s", e, exc_info=True)
        return {"initialized": False, "memories": [], "error": str(e)}
