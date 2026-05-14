"""
State Config Loader — 配置外部化
=================================

從 angela_state.yaml 載入所有配置，提供類型安全的訪問介面。
替換 state_matrix.py 中的所有硬編碼值。

使用方式:
    from core.state.config_loader import StateConfig

    config = StateConfig()
    assign_thresh = config.allocation.assign_threshold
    matrix = config.influence.matrix
    axes = config.axes

Author: Angela AI v6.2
Version: 6.2.1
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Union
try:
    import yaml
    _HAS_YAML = True
except Exception:
    _HAS_YAML = False
    import json as _json

import math
import os


@dataclass
class AxisFieldConfig:
    name: str
    label: str
    default: float
    min_val: float
    max_val: float
    description: str = ""

    def in_range(self, value: float) -> bool:
        return self.min_val <= value <= self.max_val

    def clamp(self, value: float) -> float:
        return max(self.min_val, min(self.max_val, value))


@dataclass
class AxisConfig:
    name: str
    label: str
    weight: float
    coordinate: Tuple[float, float, float]
    description: str
    fields: List[AxisFieldConfig]

    def get_field(self, name: str) -> Optional[AxisFieldConfig]:
        for f in self.fields:
            if f.name == name:
                return f
        return None


@dataclass
class AllocationConfig:
    assign_threshold: float
    composite_threshold: float
    composite_min_axes: int
    create_novelty_threshold: float
    create_complexity_min: int
    create_confidence: float
    defer_confidence: float
    high_similarity_threshold: float
    buffer_max_size: int
    buffer_track_threshold: int
    buffer_creation_urge_boost: float


@dataclass
class NegativityConfig:
    trigger_threshold: float
    correction_urge_threshold: float
    audit_intensity_base: float
    max_misallocation_log: int
    max_audit_trail: int
    drift_threshold_base: float
    drift_threshold_min: float
    drift_threshold_max: float
    min_window: int
    max_window: int
    correction_delta: float
    correction_negativity_reduction: float
    correction_urge_reduction: float


@dataclass
class IntentGravityConfig:
    base_strength: float
    max_shift_per_update: float
    decay_rate: float
    stability_threshold: float


@dataclass
class InterDimensionalDragConfig:
    drag_coefficient: float
    min_weight: float
    max_cascade_depth: int


@dataclass
class EpsilonRippleConfig:
    surprise_weight: float
    happiness_weight: float
    fatigue_threshold: float
    focus_drain_per_fatigue: float
    calm_drain_per_fatigue: float


@dataclass
class SpatialConfig:
    gravity_constant: float
    softening_parameter: float
    influence_min: float
    influence_max: float


@dataclass
class StateMatrixConfig:
    max_history: int
    max_misallocation_log: int
    max_audit_trail: int
    default_precision: float


class StateConfig:
    """
    配置管理單例

    從 YAML 檔案載入，解析為強類型 dataclass 結構。
    """

    _instance: Optional["StateConfig"] = None

    def __new__(cls, config_path: Optional[str] = None) -> "StateConfig":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._loaded = False
        return cls._instance

    def __init__(self, config_path: Optional[str] = None):
        if self._loaded:
            return
        self._loaded = True

        if config_path is None:
            d = os.path.dirname(os.path.abspath(__file__))
            for _ in range(5):
                d = os.path.dirname(d)
            config_path = os.path.join(d, "configs", "angela_state.yaml")

        with open(config_path, "r", encoding="utf-8") as f:
            if _HAS_YAML:
                data = yaml.safe_load(f)
            else:
                data = _json.load(f)

        sm_data = data.get("state_matrix", {})
        self.state_matrix = StateMatrixConfig(
            max_history=sm_data.get("max_history", 500),
            max_misallocation_log=sm_data.get("max_misallocation_log", 100),
            max_audit_trail=sm_data.get("max_audit_trail", 50),
            default_precision=sm_data.get("default_precision", 1.0),
        )

        self.axes: Dict[str, AxisConfig] = {}
        for axis_name, axis_data in data.get("axes", {}).items():
            fields = [
                AxisFieldConfig(
                    name=f["name"],
                    label=f.get("label", f["name"]),
                    default=f.get("default", 0.5),
                    min_val=f.get("range", [0.0, 1.0])[0],
                    max_val=f.get("range", [0.0, 1.0])[1],
                    description=f.get("description", ""),
                )
                for f in axis_data.get("fields", [])
            ]
            self.axes[axis_name] = AxisConfig(
                name=axis_name,
                label=axis_data.get("label", axis_name),
                weight=axis_data.get("weight", 1.0),
                coordinate=tuple(axis_data.get("coordinate", [0.0, 0.0, 0.0])),
                description=axis_data.get("description", ""),
                fields=fields,
            )

        alloc_data = data.get("allocation", {})
        buffer_data = alloc_data.get("buffer", {})
        self.allocation = AllocationConfig(
            assign_threshold=alloc_data.get("assign_threshold", 0.7),
            composite_threshold=alloc_data.get("composite_threshold", 0.3),
            composite_min_axes=alloc_data.get("composite_min_axes", 2),
            create_novelty_threshold=alloc_data.get("create_novelty_threshold", 0.6),
            create_complexity_min=alloc_data.get("create_complexity_min", 2),
            create_confidence=alloc_data.get("create_confidence", 0.5),
            defer_confidence=alloc_data.get("defer_confidence", 0.3),
            high_similarity_threshold=alloc_data.get("high_similarity_threshold", 0.5),
            buffer_max_size=buffer_data.get("max_size", 50),
            buffer_track_threshold=buffer_data.get("track_threshold", 5),
            buffer_creation_urge_boost=buffer_data.get("creation_urge_boost", 0.05),
        )

        neg_data = data.get("negativity", {})
        det_data = neg_data.get("detection", {})
        cor_data = neg_data.get("correction", {})
        self.negativity = NegativityConfig(
            trigger_threshold=neg_data.get("trigger_threshold", 0.5),
            correction_urge_threshold=neg_data.get("correction_urge_threshold", 0.6),
            audit_intensity_base=neg_data.get("audit_intensity_base", 0.5),
            max_misallocation_log=neg_data.get("max_misallocation_log", 100),
            max_audit_trail=neg_data.get("max_audit_trail", 50),
            drift_threshold_base=det_data.get("drift_threshold_base", 0.3),
            drift_threshold_min=det_data.get("drift_threshold_min", 0.15),
            drift_threshold_max=det_data.get("drift_threshold_max", 0.4),
            min_window=det_data.get("min_window", 3),
            max_window=det_data.get("max_window", 50),
            correction_delta=cor_data.get("delta_amount", 0.1),
            correction_negativity_reduction=cor_data.get("negativity_reduction", 0.05),
            correction_urge_reduction=cor_data.get("correction_urge_reduction", 0.10),
        )

        ig_data = data.get("intent_gravity", {})
        self.intent_gravity = IntentGravityConfig(
            base_strength=ig_data.get("base_strength", 0.05),
            max_shift_per_update=ig_data.get("max_shift_per_update", 0.1),
            decay_rate=ig_data.get("decay_rate", 0.95),
            stability_threshold=ig_data.get("stability_threshold", 0.01),
        )

        idd_data = data.get("inter_dimensional_drag", {})
        self.inter_dimensional_drag = InterDimensionalDragConfig(
            drag_coefficient=idd_data.get("drag_coefficient", 0.02),
            min_weight=idd_data.get("min_weight", 0.001),
            max_cascade_depth=idd_data.get("max_cascade_depth", 3),
        )

        eps_data = data.get("epsilon_ripple", {})
        self.epsilon_ripple = EpsilonRippleConfig(
            surprise_weight=eps_data.get("surprise_weight", 0.2),
            happiness_weight=eps_data.get("happiness_weight", 0.15),
            fatigue_threshold=eps_data.get("fatigue_threshold", 0.7),
            focus_drain_per_fatigue=eps_data.get("focus_drain_per_fatigue", 0.1),
            calm_drain_per_fatigue=eps_data.get("calm_drain_per_fatigue", 0.05),
        )

        sp_data = data.get("spatial", {})
        self.spatial = SpatialConfig(
            gravity_constant=sp_data.get("gravity_constant", 25.0),
            softening_parameter=sp_data.get("softening_parameter", 10.0),
            influence_min=sp_data.get("influence_min", 0.5),
            influence_max=sp_data.get("influence_max", 2.0),
        )

        self.influence_matrix: Dict[str, Dict[str, float]] = data.get("influence", {}).get("matrix", {})

        self._raw = data

    def get_axis(self, name: str) -> Optional[AxisConfig]:
        return self.axes.get(name)

    def get_all_axis_names(self) -> List[str]:
        return list(self.axes.keys())

    def to_dict(self) -> Dict[str, Any]:
        """Export full config as dict (for serialization)"""
        return self._raw

    @classmethod
    def reload(cls, config_path: Optional[str] = None) -> "StateConfig":
        """Force reload from file"""
        cls._instance = None
        return cls(config_path=config_path)


def load_state_config(config_path: Optional[str] = None) -> StateConfig:
    """Convenience function to load state config"""
    return StateConfig(config_path=config_path)