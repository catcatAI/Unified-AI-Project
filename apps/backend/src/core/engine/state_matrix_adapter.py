"""
State Matrix Adapter — Phase 7 整合適配器
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

from core.interfaces.persistence import JsonFileStateStore

logger = logging.getLogger(__name__)


class _AxisProxy:
    """Proxy that wraps a dict and exposes it with .values for axis-like access."""
    def __init__(self, values: Optional[Dict[str, Any]] = None):
        self.values = values or {}

class _TemporalProxy:
    """Proxy for temporal record/query access."""
    def __init__(self):
        self._records: List[Dict[str, Any]] = []

    def record(self, axis: str, field: str, value: float) -> None:
        self._records.append({"axis": axis, "field": field, "value": value})

class _InfluenceSpaceProxy:
    """Proxy for influence space computation."""
    def compute(self, **kwargs) -> Dict[str, float]:
        return {}

class _EtaProxy:
    """Proxy for ETA module registry access."""
    def __init__(self):
        self.module_registry = {}

class _AnchorLearningProxy:
    """Proxy for anchor learning access."""
    def get_best_axis(self, **kwargs) -> Optional[str]:
        return None

class _ResonanceEngineProxy:
    """Proxy for resonance engine access."""
    def compute_profile(self, **kwargs) -> Dict[str, Any]:
        return {}

class _AllocationPolicyProxy:
    """Proxy for allocation policy access."""
    def __init__(self):
        self.stages = []


class StateMatrixAdapter(JsonFileStateStore):
    """Bridges old StateMatrix4D API with refactored modules."""

    def __init__(self, data_dir: str = "data/state/"):
        super().__init__(data_dir)
        self._state: Dict[str, Any] = {}
        self._history: List[Dict[str, Any]] = []
        self._temporal_proxy = _TemporalProxy()
        self._influence_space = _InfluenceSpaceProxy()
        self._eta = _EtaProxy()
        self._anchor_learning = _AnchorLearningProxy()
        self._resonance_engine = _ResonanceEngineProxy()
        self._allocation_policy = _AllocationPolicyProxy()

    # --- Axis properties ---

    @property
    def alpha(self) -> _AxisProxy:
        return _AxisProxy(self._state.get("alpha", {}))

    @property
    def beta(self) -> _AxisProxy:
        return _AxisProxy(self._state.get("beta", {}))

    @property
    def gamma(self) -> _AxisProxy:
        return _AxisProxy(self._state.get("gamma", {}))

    @property
    def delta(self) -> _AxisProxy:
        return _AxisProxy(self._state.get("delta", {}))

    @property
    def theta(self) -> _AxisProxy:
        return _AxisProxy(self._state.get("theta", {}))

    @property
    def zeta(self) -> _AxisProxy:
        return _AxisProxy(self._state.get("zeta", {}))

    @property
    def history(self) -> List[Dict[str, Any]]:
        return self._history

    # --- Temporal ---

    @property
    def temporal(self) -> _TemporalProxy:
        return self._temporal_proxy

    def temporal_trend(self, axis: str, field: str, window: int = 5) -> Optional[float]:
        return 0.0

    # --- New API properties ---

    @property
    def influence_space(self) -> _InfluenceSpaceProxy:
        return self._influence_space

    @property
    def eta(self) -> _EtaProxy:
        return self._eta

    @property
    def anchor_learning(self) -> _AnchorLearningProxy:
        return self._anchor_learning

    @property
    def resonance_engine(self) -> _ResonanceEngineProxy:
        return self._resonance_engine

    @property
    def allocation_policy(self) -> _AllocationPolicyProxy:
        return self._allocation_policy

    # --- Update methods ---

    def update_alpha(self, **kwargs) -> None:
        self._state.setdefault("alpha", {}).update(kwargs)

    def update_beta(self, **kwargs) -> None:
        self._state.setdefault("beta", {}).update(kwargs)

    def update_gamma(self, **kwargs) -> None:
        self._state.setdefault("gamma", {}).update(kwargs)

    def update_delta(self, **kwargs) -> None:
        self._state.setdefault("delta", {}).update(kwargs)

    def update_epsilon(self, **kwargs) -> None:
        self._state.setdefault("epsilon", {}).update(kwargs)

    def update_theta(self, **kwargs) -> None:
        self._state.setdefault("theta", {}).update(kwargs)

    def update_zeta(self, **kwargs) -> None:
        self._state.setdefault("zeta", {}).update(kwargs)

    def compute_influences(self) -> Dict[str, Any]:
        return {
            "alpha": 0.5,
            "beta": 0.4,
            "gamma": 0.3,
            "delta": 0.2,
        }

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
