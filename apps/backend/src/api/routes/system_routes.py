"""
ANGELA-MATRIX: [L5] [β] [B] [L3]
System discovery API — single endpoint returning all system state for UI consumption.

GET /system/discovery — deployment mode, backends, intents, memory, state summary
"""

import logging
import time
from typing import Any, Dict, Optional

from core.utils import safe_error
from fastapi import APIRouter, HTTPException

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


async def _detailed_state_matrix() -> Dict[str, Any]:
    """The state matrix axes (means + values), or None."""
    from api.routes.chat_routes import _get_state_matrix

    matrix = _get_state_matrix()
    axes: Dict[str, Any] = {}
    for axis_name in ("alpha", "beta", "gamma", "delta", "epsilon", "theta", "zeta"):
        axis = getattr(matrix, axis_name, None)
        values = getattr(axis, "values", None)
        if isinstance(values, dict):
            axes[axis_name] = {
                "mean": round(sum(values.values()) / len(values), 3) if values else 0.5,
                "values": {k: round(float(v), 3) for k, v in values.items()},
            }
    return axes


async def _detailed_emotion_and_phase() -> Dict[str, Any]:
    """The emotion summary and the current life phase."""
    from api.lifespan import get_emotion_system, get_lifecycle

    emotion = get_emotion_system()
    lifecycle = get_lifecycle()
    phase = getattr(lifecycle, "current_phase", None)
    return {
        "emotion": emotion.get_emotion_summary() if emotion is not None else None,
        "life_phase": getattr(phase, "value", phase),
    }


async def _detailed_backends() -> Dict[str, Any]:
    """The registered LLM backends with their last known health."""
    from services.angela_llm_service import get_llm_service

    service = await get_llm_service()
    backends = getattr(service, "backends", {}) or {}
    return {
        "backends": {
            str(getattr(btype, "value", btype)): service.backend_health(btype) for btype in backends
        },
        "active_backend": str(
            getattr(getattr(service, "active_backend_type", None), "value", "none")
        ),
    }


def _detailed_memory() -> Dict[str, Any]:
    """The HAM memory statistics."""
    from ai.memory.ham_memory.ham_manager import HAMMemoryManager

    return HAMMemoryManager(auto_save=False).get_stats()


def _detailed_al_state() -> Dict[str, Any]:
    """The AL read-only snapshot (contract §9's only exchange quantity).

    This is the dump surface for ALState under a running server: the
    ``source`` column names each value's provenance (``provider:*`` /
    ``core.*`` / ``None``), and an unobserved quantity is null — never a
    fake 0.0 (D11).
    """
    from core.life.al_state import get_al_state

    return get_al_state().as_dict()


@router.get("/status/detailed")
async def system_status_detailed() -> Dict[str, Any]:
    """Detailed system status (the contract the INVOCATION_MATRIX documents).

    The matrix listed ``GET /api/v1/system/status/detailed`` with the
    verification ``curl :8000/api/v1/system/status/detailed`` — the endpoint
    did not exist, so the documented call answered 404. It is here now, and it
    reports the parts an operator actually needs: the state matrix axes, the
    emotion and life phase, the registered backends, and the memory status.

    Everything is best-effort: a missing subsystem is reported as null, never
    as an error (a status endpoint that 500s is useless).
    """
    result: Dict[str, Any] = {
        "timestamp": time.time(),
        "uptime_seconds": int(time.time() - _start_time),
    }

    # Each part is best-effort: a missing subsystem is reported as null,
    # never as an error (a status endpoint that 500s is useless).
    try:
        result["state_matrix"] = await _detailed_state_matrix()
    except Exception as exc:
        result["state_matrix"] = None
        result["state_matrix_error"] = safe_error(exc)

    try:
        result.update(await _detailed_emotion_and_phase())
    except Exception as exc:
        result["emotion"] = None
        result["life_phase"] = None
        result["emotion_error"] = safe_error(exc)

    try:
        result.update(await _detailed_backends())
    except Exception as exc:
        result["backends"] = {}
        result["active_backend"] = None
        result["backends_error"] = safe_error(exc)

    try:
        result["memory"] = _detailed_memory()
    except Exception as exc:
        result["memory"] = None
        result["memory_error"] = safe_error(exc)

    # AL 唯讀快照（契約 §9 的唯一交換量）— 這是在 server 執行下 dump
    # ALState 的面：``source`` 欄逐鍵顯示 provenance（provider:* / core.*
    # / None），未觀測就是 null，不會有假 0.0（D11）。
    try:
        result["al_state"] = _detailed_al_state()
    except Exception as exc:
        result["al_state"] = None
        result["al_state_error"] = safe_error(exc)

    return result


@router.get("/pet")
async def system_pet_state() -> Dict[str, Any]:
    """The digital life's real state, for the dashboard's pet panel.

    The dashboard used to show a *local* simulation (an in-memory object in
    the Next.js API route that decayed on its own and answered "pet"/"feed"
    with hard-coded deltas). The numbers on screen were therefore unrelated
    to the system they claimed to describe.

    This endpoint reports the real state matrix and the real life phase, and
    names the source of every field so the panel can say where a number comes
    from. The mapping (documented, not hidden):

      happiness ← gamma.happiness   (情緒軸)
      energy    ← alpha.energy      (生理軸)
      health    ← alpha.comfort     (生理軸)
      hunger    ← alpha.rest_need   (生理軸的休息需求)
    """
    result: Dict[str, Any] = {
        "timestamp": time.time(),
        "source": "state_matrix",
        "happiness": 0.5,
        "hunger": 0.5,
        "energy": 0.5,
        "health": 1.0,
        "life_phase": None,
        "emotion": None,
    }
    try:
        from api.routes.chat_routes import _get_state_matrix

        matrix = _get_state_matrix()

        def _value(axis_name: str, key: str, default: float) -> float:
            axis = getattr(matrix, axis_name, None)
            values = getattr(axis, "values", None)
            if isinstance(values, dict) and key in values:
                try:
                    return float(values[key])
                except (TypeError, ValueError):
                    return default
            return default

        result["happiness"] = _value("gamma", "happiness", 0.5)
        result["energy"] = _value("alpha", "energy", 0.5)
        result["health"] = _value("alpha", "comfort", 1.0)
        result["hunger"] = _value("alpha", "rest_need", 0.5)
    except Exception as exc:
        result["source"] = "unavailable"
        result["error"] = safe_error(exc)

    try:
        from api.lifespan import get_emotion_system, get_lifecycle

        emotion = get_emotion_system()
        if emotion is not None:
            result["emotion"] = emotion.get_emotion_summary().get("dominant_emotion")
        lifecycle = get_lifecycle()
        result["life_phase"] = _phase_label(getattr(lifecycle, "current_phase", None))
    except Exception as exc:
        result["error"] = safe_error(exc)

    return result


# The pet panel's interactions, applied to the REAL state matrix.
_PET_ACTIONS: Dict[str, Dict[str, float]] = {
    "pet": {"happiness": 0.1, "energy": -0.05},
    "feed": {"hunger": -0.2, "happiness": 0.05},
    "play": {"happiness": 0.15, "energy": -0.15, "hunger": 0.05},
    "rest": {"energy": 0.3, "happiness": -0.05},
}


@router.post("/pet/interact")
async def system_pet_interact(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Apply a pet interaction to the real state matrix and report the result.

    The panel used to mutate a local object; now the interaction reaches the
    system it claims to describe. Unknown actions are rejected (400) instead
    of being silently ignored.
    """
    action = str((payload or {}).get("action") or "").strip()
    effects = _PET_ACTIONS.get(action)
    if effects is None:
        raise HTTPException(
            status_code=400,
            detail=f"unknown action '{action}'; expected one of {sorted(_PET_ACTIONS)}",
        )

    from api.routes.chat_routes import _get_state_matrix

    matrix = _get_state_matrix()
    try:
        _apply_pet_effects(matrix, effects)
    except Exception as exc:
        logger.error("Pet interaction failed: %s", safe_error(exc))
        raise HTTPException(status_code=500, detail="Pet interaction failed") from exc

    return await system_pet_state()


def _apply_pet_effects(matrix: Any, effects: Dict[str, float]) -> None:
    """Apply the interaction deltas to the alpha/gamma axes of the matrix."""
    alpha = getattr(matrix, "alpha", None)
    gamma = getattr(matrix, "gamma", None)

    if alpha is not None and ("hunger" in effects or "energy" in effects or "health" in effects):
        rest_need = float(alpha.values.get("rest_need", 0.5))
        energy = float(alpha.values.get("energy", 0.5))
        comfort = float(alpha.values.get("comfort", 1.0))
        if "hunger" in effects:
            rest_need = _clamp01(rest_need + effects["hunger"])
        if "energy" in effects:
            energy = _clamp01(energy + effects["energy"])
        if "health" in effects:
            comfort = _clamp01(comfort + effects["health"])
        if hasattr(alpha, "update"):
            alpha.update(rest_need=rest_need, energy=energy, comfort=comfort)

    if gamma is not None and "happiness" in effects:
        happiness = _clamp01(float(gamma.values.get("happiness", 0.5)) + effects["happiness"])
        if hasattr(gamma, "update"):
            gamma.update(happiness=happiness)


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _phase_label(phase: Any) -> Optional[str]:
    """A readable label for a life phase (its value is a (cn, en) tuple)."""
    if phase is None:
        return None
    name = getattr(phase, "name", None)
    if name:
        return str(name)
    value = getattr(phase, "value", phase)
    if isinstance(value, (tuple, list)) and value:
        return str(value[0])
    return str(value)


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
