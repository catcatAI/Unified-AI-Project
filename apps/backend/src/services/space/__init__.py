# =============================================================================
# ANGELA-MATRIX: [L4] [βγδ] [B] [L3]
# =============================================================================
"""Space stage state + WebSocket transport (S1 backend half)."""

from services.space.space_service import (
    DEFAULT_ROOM_ID,
    SpaceService,
    get_space_service,
    reset_space_service,
)

__all__ = [
    "DEFAULT_ROOM_ID",
    "SpaceService",
    "get_space_service",
    "reset_space_service",
]
