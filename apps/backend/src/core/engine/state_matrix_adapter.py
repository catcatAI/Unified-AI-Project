"""
State Matrix Adapter — Phase 7 整合適配器
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

from core.interfaces.persistence import JsonFileStateStore

logger = logging.getLogger(__name__)


class StateMatrixAdapter(JsonFileStateStore):
    """Bridges old StateMatrix4D API with refactored modules."""

    def __init__(self, data_dir: str = "data/state/"):
        super().__init__(data_dir)
        self._state: Dict[str, Any] = {}

    def update_alpha(self, **kwargs) -> None:
        self._state.update(kwargs)

    def update_beta(self, **kwargs) -> None:
        self._state.update(kwargs)

    def compute_influences(self) -> Dict[str, Any]:
        return {}

    def export_to_dict(self) -> Dict[str, Any]:
        """Export current state as a dictionary."""
        return {
            "state": dict(self._state),
            "dimensions": {},
        }

    def import_from_dict(self, data: Dict[str, Any]) -> None:
        """Import state from a dictionary."""
        state = data.get("state", {})
        if isinstance(state, dict):
            self._state.update(state)
        else:
            logger.warning("import_from_dict: 'state' is not a dict, got %s", type(state).__name__)
