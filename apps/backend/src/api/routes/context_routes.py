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


def _render_memory_content(content: Any) -> str:
    """Render a stored memory for the MemoryViewer panel.

    Conversation entries are stored as ``{"user": ..., "assistant": ...}``;
    stringifying that dict would render Python repr (escaped quotes, braces)
    straight into the UI. Fall back to ``str(content)`` for any other shape.
    """
    if content is None:
        return ""
    if isinstance(content, dict):
        user_part = str(content.get("user") or "").strip()
        assistant_part = str(content.get("assistant") or "").strip()
        rendered = " | ".join(part for part in (user_part, assistant_part) if part)
        if rendered:
            return rendered[:200]
    return str(content)[:200]


async def _summary_state_section(result: Dict[str, Any]) -> None:
    """Fill result['state'] and result['eta'] from chat service state matrix."""
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

        # Eta — None for anything without an observation behind it (see
        # measured_eta_metrics); execution_count stays a real count, 0 or not.
        eta = service.eta_state
        if eta:
            from core.engine.eta_axis import measured_eta_metrics

            result["eta"] = measured_eta_metrics(eta)
    except Exception as e:
        logger.warning("State matrix unavailable: %s", e, exc_info=True)
        result["state"] = {}
        result["eta"] = None


async def _summary_memory_section(result: Dict[str, Any]) -> None:
    """Fill result['memory'] with initialization status + recent count."""
    try:
        from api.lifespan import _get_chat_service

        service = await _get_chat_service()
        has_memory = hasattr(service, "memory_manager") and service.memory_manager is not None
        result["memory"] = {"initialized": has_memory}

        if has_memory:
            try:
                # 死路徑 #19 修復：原在 async 端點內以 loop.is_running() 判定——
                # 永遠 False 導致 recent_count 永不填充；改為直接 await 查詢。
                results = await service.memory_manager.query_core_memory(
                    keywords=["experience"], limit=5
                )
                result["memory"]["recent_count"] = len(results)
            except Exception:
                result["memory"]["recent_count"] = None
    except Exception:
        result["memory"] = {"initialized": False}


def _summary_intents_section(result: Dict[str, Any]) -> None:
    """Fill result['intents'] with configured intent names."""
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


async def _summary_llm_section(result: Dict[str, Any]) -> None:
    """Fill result['llm'] with quick backend status."""
    try:
        from services.angela_llm_service import get_llm_service

        llm_svc = await get_llm_service()
        active = getattr(llm_svc, "active_backend_type", None)
        result["llm"] = {
            "available": getattr(llm_svc, "is_available", False),
            "active": active.name if active is not None else None,
            "mode": getattr(llm_svc, "llm_mode", "unknown"),
        }
    except Exception:
        result["llm"] = {"available": False}


@router.get("/summary")
async def context_summary() -> Dict[str, Any]:
    """Return context overview: state matrix, memory status, intent list."""
    result: Dict[str, Any] = {"timestamp": time.time()}

    await _summary_state_section(result)
    await _summary_memory_section(result)
    _summary_intents_section(result)
    await _summary_llm_section(result)

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
                    "content": _render_memory_content(content),
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
