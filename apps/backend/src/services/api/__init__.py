# =============================================================================
# ANGELA-MATRIX: [L2] [α] [B] [L3]
# =============================================================================
"""
API services package — REST/WebSocket API layer.

Contains state_matrix_api routes and API-related utilities.
"""

from services.api.state_matrix_api import state_matrix_router

__all__ = [
    "state_matrix_router",
]
