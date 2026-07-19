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

    @property
    def trend(self) -> Optional[float]:
        if not self._records:
            return None
        recent = self._records[-10:]
        values = [r["value"] for r in recent]
        if len(values) < 2:
            return 0.0
        return sum(values[-1] - values[0] for _ in [0]) / (len(values) - 1)

    @property
    def anomalies(self) -> List[Dict[str, Any]]:
        if len(self._records) < 5:
            return []
        recent_vals = [r["value"] for r in self._records[-20:]]
        mean = sum(recent_vals) / len(recent_vals)
        std = (sum((v - mean) ** 2 for v in recent_vals) / len(recent_vals)) ** 0.5
        if std < 1e-6:
            return []
        return [
            {
                "axis": r["axis"],
                "field": r["field"],
                "value": r["value"],
                "deviation": abs(r["value"] - mean) / std,
            }
            for r in self._records[-20:]
            if abs(r["value"] - mean) / std > 2.0
        ]


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

    def decide(self, **kwargs) -> Dict[str, Any]:
        return {"action": "none", "reason": "no policy configured"}

    @property
    def compute_gradient(self):
        return lambda **kw: {"gradient": {}, "gradient_strength": 0.0, "nearest_attractors": []}

    @property
    def navigate(self):
        return lambda **kw: {"navigation_steps": 0, "new_state": {}, "nearest_attractors": []}


class _GradientFieldProxy:
    """Proxy for gradient field computation."""

    def compute_gradient(self, **kwargs) -> Dict[str, Any]:
        return {"gradient": {}, "gradient_strength": 0.0, "nearest_attractors": []}

    def navigate(self, **kwargs) -> Dict[str, Any]:
        return {"navigation_steps": 0, "new_state": {}, "nearest_attractors": []}


class _GradientFieldProperty:
    """Property object for gradient_field access."""

    def compute_gradient(self, **kwargs) -> Dict[str, Any]:
        return {
            "gradient": {},
            "gradient_strength": 0.0,
            "nearest_attractors": [{"coord": (0.5, 0.5, 0.5, 0.5, 0.0), "behavior": "default"}],
        }

    def navigate(self, **kwargs) -> Dict[str, Any]:
        return {"navigation_steps": 1, "new_state": {}, "nearest_attractors": []}


class StateMatrixAdapter(JsonFileStateStore):
    """Bridges old StateMatrix4D API with refactored modules."""

    def __init__(self, data_dir: str = "data/state/"):
        super().__init__(data_dir)
        self._state: Dict[str, Any] = {}
        self._history: List[Dict[str, Any]] = []
        self._attractors: List[Dict[str, Any]] = []
        self._update_count: int = 0
        self._temporal_proxy = _TemporalProxy()
        self._influence_space = _InfluenceSpaceProxy()
        self._eta = _EtaProxy()
        self._anchor_learning = _AnchorLearningProxy()
        self._resonance_engine = _ResonanceEngineProxy()
        self._allocation_policy = _AllocationPolicyProxy()
        self._gradient_field = _GradientFieldProperty()

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
    def epsilon(self) -> _AxisProxy:
        return _AxisProxy(self._state.get("epsilon", {}))

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
        """Compute rolling trend for a specific axis/field from temporal records."""
        matching = [
            r for r in self._temporal_proxy._records if r["axis"] == axis and r["field"] == field
        ]
        if len(matching) < 2:
            return 0.0
        recent = matching[-window:]
        values = [r["value"] for r in recent]
        if len(values) < 2:
            return 0.0
        return round((values[-1] - values[0]) / (len(values) - 1), 4)

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

    def _update_axis(self, name: str, **kwargs) -> None:
        self._state.setdefault(name, {}).update(kwargs)
        self._update_count += 1

    def update_alpha(self, **kwargs) -> None:
        self._update_axis("alpha", **kwargs)

    def update_beta(self, **kwargs) -> None:
        self._update_axis("beta", **kwargs)

    def update_gamma(self, **kwargs) -> None:
        self._update_axis("gamma", **kwargs)

    def update_delta(self, **kwargs) -> None:
        self._update_axis("delta", **kwargs)

    def update_epsilon(self, **kwargs) -> None:
        self._update_axis("epsilon", **kwargs)

    def update_theta(self, **kwargs) -> None:
        self._update_axis("theta", **kwargs)

    def update_zeta(self, **kwargs) -> None:
        self._update_axis("zeta", **kwargs)

    def compute_influences(self) -> Dict[str, Any]:
        """Compute inter-axis influence based on actual state values."""
        axes = ["alpha", "beta", "gamma", "delta"]
        influences: Dict[str, float] = {}
        for src in axes:
            src_vals = self._state.get(src, {})
            if not src_vals:
                influences[src] = 0.0
                continue
            src_avg = sum(v for v in src_vals.values() if isinstance(v, (int, float))) / max(
                len(src_vals), 1
            )
            influence = 0.0
            for tgt in axes:
                if tgt == src:
                    continue
                tgt_vals = self._state.get(tgt, {})
                if not tgt_vals:
                    continue
                tgt_avg = sum(v for v in tgt_vals.values() if isinstance(v, (int, float))) / max(
                    len(tgt_vals), 1
                )
                influence += src_avg * tgt_avg
            influences[src] = round(influence / max(len(axes) - 1, 1), 4)
        return influences

    # --- Gradient / Attractor ---

    @property
    def gradient_field(self) -> _GradientFieldProperty:
        return self._gradient_field

    def compute_gradient(self) -> Dict[str, Any]:
        nearest = (
            self._attractors[:3]
            if self._attractors
            else [
                {
                    "coord": (0.5, 0.5, 0.5, 0.5, 0.0),
                    "behavior": "default",
                    "tone": "calm",
                    "mass": 1.0,
                }
            ]
        )
        return {"gradient": {}, "gradient_strength": 0.0, "nearest_attractors": nearest}

    def navigate_to_attractor(self, max_steps: int = 3) -> Dict[str, Any]:
        return {
            "navigation_steps": 1,
            "new_state": {},
            "nearest_attractors": self._attractors[:1] if self._attractors else [],
        }

    def add_attractor(
        self,
        coord: tuple,
        behavior: str = "",
        tone: str = "calm",
        mass: float = 1.0,
        tags: Optional[List[str]] = None,
    ) -> bool:
        self._attractors.append(
            {"coord": coord, "behavior": behavior, "tone": tone, "mass": mass, "tags": tags or []}
        )
        return True

    def remove_attractor_by_tags(self, tags: List[str]) -> int:
        before = len(self._attractors)
        self._attractors = [
            a for a in self._attractors if not any(t in a.get("tags", []) for t in tags)
        ]
        return before - len(self._attractors)

    # --- Persistence ---

    def save_state(self) -> Dict[str, Any]:
        return {
            "dimensions": dict(self._state),
            "update_count": self._update_count,
        }

    def load_state(self, data: Dict[str, Any]) -> None:
        dims = data.get("dimensions", {})
        if isinstance(dims, dict):
            self._state.update(dims)
        self._update_count = data.get("update_count", 0)

    # --- Code inspect / report ---

    def integrate_code_inspect(self, report: Dict[str, Any]) -> Dict[str, str]:
        return {"status": "skip"}

    def code_inspect_report(self) -> Dict[str, float]:
        return {"epsilon_complexity": 0.0, "theta_negativity": 0.0}

    def full_report(self) -> Dict[str, Any]:
        return {
            "state_matrix": dict(self._state),
            "temporal": {"records": len(self._temporal_proxy._records)},
            "influence": self.compute_influences(),
            "allocation": {"stages": self._allocation_policy.stages},
            "negativity": 0.0,
            "port_routing": {},
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
