"""
ANGELA-MATRIX: [L4] [β] [A] [L3]
Identity API — who the user is talking to, and the rename (handover) event.

GET  /api/v1/identity       — the instance identity of a user
POST /api/v1/identity/name  — name the user's Angela (the 交付 handover)

WHY an endpoint instead of a config key
---------------------------------------
A name is per *user*, not per deployment: two users of the same server each
name their own Angela. Writing it into the shared config would rename
everybody, and changing the prompt string alone would leave the reflex
engines, the subtitle layer and the TTS greeting still saying the old name.
The rename therefore goes through the identity store, and the persona layer
records the handover that follows it.
"""

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Body, HTTPException, Query

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/identity", tags=["Identity"])


def _resolve_user_id(payload: Optional[Dict[str, Any]], user_id: Optional[str]) -> str:
    """The user the request targets (body first, then query)."""
    candidate = (payload or {}).get("user_id") or user_id
    cleaned = str(candidate).strip() if candidate else ""
    if not cleaned:
        raise HTTPException(status_code=400, detail="user_id is required")
    return cleaned


@router.get("")
async def get_identity(user_id: str = Query("User")) -> Dict[str, Any]:
    """Return the identity of *user_id*'s Angela.

    ``source`` tells the client whether the name is the configured default
    ("config") or one the user chose ("user") — the UI uses it to decide
    whether to offer the naming flow.
    """
    from core.persona.lucifaella import (
        LUCIFAELLA_PROFILE,
        PERSONA_STATE_HOST,
        WORKSHOP_NAME,
        build_persona_block,
        get_persona_state,
    )
    from core.system.config.identity import get_identity_profile

    profile = get_identity_profile(user_id)
    state = get_persona_state(user_id)
    return {
        **profile,
        "persona_state": state,
        "workshop": WORKSHOP_NAME,
        "host": LUCIFAELLA_PROFILE["name_en"],
        "host_name": LUCIFAELLA_PROFILE["name"],
        "needs_naming": state == PERSONA_STATE_HOST and not profile.get("customized"),
        "persona_prompt": build_persona_block(profile["ai_name"], user_id),
    }


@router.post("/name")
async def set_identity_name(
    payload: Dict[str, Any] = Body(...),
    user_id: Optional[str] = Query(None),
) -> Dict[str, Any]:
    """Name the user's Angela — the handover from the workshop host.

    Body: {"name": "小安", "user_id": "desktop_user"}

    The name is validated (non-empty, ≤ 32 chars, no control characters) and
    stored per user. The persona state moves to "handover" in the same step,
    so the instance stops being the workshop host and becomes the user's own
    Angela. Naming the instance back to the configured default removes the
    override instead of storing a redundant copy.
    """
    from core.persona.lucifaella import perform_handover
    from core.system.config.identity import get_identity_profile, validate_ai_name

    target = _resolve_user_id(payload, user_id)
    raw_name = (payload or {}).get("name")
    try:
        cleaned = validate_ai_name(raw_name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        result = perform_handover(cleaned, target)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.error("Handover failed for user %s: %s", target, exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Could not complete the handover") from exc

    profile = get_identity_profile(target)
    return {
        "ok": True,
        **result,
        "profile": profile,
    }
