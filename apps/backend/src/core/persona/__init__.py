"""
ANGELA-MATRIX: [L3] [βγ] [B] [L0-L11]
Persona layer — who the user is talking to, and what that role may claim.

Currently one character: 露茜法埃拉 (Lucifaella), the 天使工房 business
department host who greets new users and hands them an Angela of their own.
"""

from core.persona.lucifaella import (
    LUCIFAELLA_PROFILE,
    PERSONA_STATE_HANDOVER,
    PERSONA_STATE_HOST,
    WORKSHOP_NAME,
    WORKSHOP_NAME_EN,
    build_persona_block,
    get_persona_state,
    perform_handover,
)

__all__ = [
    "LUCIFAELLA_PROFILE",
    "PERSONA_STATE_HOST",
    "PERSONA_STATE_HANDOVER",
    "WORKSHOP_NAME",
    "WORKSHOP_NAME_EN",
    "build_persona_block",
    "get_persona_state",
    "perform_handover",
]
