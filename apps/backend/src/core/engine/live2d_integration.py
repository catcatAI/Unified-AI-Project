"""
Angela AI v6.0 - Live2D Integration
Live2D集成系统

Manages Live2D model control, expression parameters, motion control,
and lip-sync for Angela AI's visual representation.

Features:
- Live2D model loading and control
- Facial expression parameter management
- Motion and animation control
- Lip synchronization with speech
- Parameter interpolation
- C2 state broadcast (get_live2d_state → registry → websocket)

Author: Angela AI Development Team
Version: 6.0.0
Date: 2026-02-02
"""

from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional, Callable, Any


# =============================================================================
# ANGELA-MATRIX: [L3] [β] [B] [L4]
# =============================================================================


class ExpressionType(str, Enum):
    """面部表情类型 / Facial expression types"""
    NEUTRAL = "neutral"
    HAPPY = "happy"
    SAD = "sad"
    ANGRY = "angry"
    SURPRISED = "surprised"
    DISGUSTED = "disgusted"
    FEARFUL = "fearful"


class Live2DIntegration:
    """
    Live2D Integration — runtime model state manager.

    Wraps Live2DAvatarGenerator for the C2 state broadcast chain:
    live2d_integration → registry → websocket_manager → desktop handler.

    Instantiable without arguments for service registration.
    Delegates generator methods to the underlying Live2DAvatarGenerator.
    """

    def __init__(
        self,
        image_generator: Optional[Any] = None,
        config: Optional[Dict[str, Any]] = None,
    ):
        from .live2d_avatar_generator import Live2DAvatarGenerator

        self._generator = Live2DAvatarGenerator(
            image_generator=image_generator,
            config=config or {},
        )

        # Runtime state
        self._expression: str = "neutral"
        self._motion: str = "idle"
        self._parameters: Dict[str, float] = {
            k: v["default"] for k, v in Live2DAvatarGenerator.STANDARD_PARAMETERS.items()
        }
        self._state_callbacks: List[Callable[[Dict[str, Any]], None]] = []

    # ------------------------------------------------------------------
    # C2 State Broadcast API
    # ------------------------------------------------------------------

    def get_live2d_state(self) -> Dict[str, Any]:
        """Return current Live2D model state for WebSocket broadcast."""
        return {
            "expression": self._expression,
            "motion": self._motion,
            "parameters": dict(self._parameters),
        }

    def set_expression(self, expr_name: str) -> bool:
        """Set a named expression and fire state callbacks."""
        if hasattr(expr_name, "value"):
            expr_name = expr_name.value
        self._expression = str(expr_name)
        self._notify_state_change()
        return True

    def get_all_parameters(self) -> Dict[str, float]:
        """Return all current model parameter values."""
        return dict(self._parameters)

    def register_live2d_state_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Register a callback invoked on every state change."""
        if callback not in self._state_callbacks:
            self._state_callbacks.append(callback)

    def _notify_state_change(self) -> None:
        """Fire all registered state callbacks."""
        state = self.get_live2d_state()
        for cb in self._state_callbacks:
            try:
                cb(state)
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"State callback error: {e}", exc_info=True)
