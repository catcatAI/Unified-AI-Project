"""
Axis — 軸的統一抽象
===================

軸是狀態空間的基本單位。
每個軸持有一組 AxisField，有坐標，有語義錨點，可以查詢/更新/統計。

使用方式:
    from core.state.axis import Axis

    # 創建軸
    alpha = Axis.from_config('alpha', label='生理')

    # 設定值（typed）
    axis.set(FocusField, 0.8)
    value = axis.get(FocusField)  # → 0.8

    # 或字串方式（向後兼容）
    axis.values['focus'] = 0.8

    # 統計
    avg = axis.average()
    dominant = axis.dominant()

    # 座標操作
    coord = axis.coordinate
    axis.shift(dx=0.1, dy=-0.2, dz=0.0)

Author: Angela AI v6.2
Version: 6.2.1
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Type

from core.state.axis_field import AxisField

logger = logging.getLogger(__name__)


class Axis:
    _fields: Dict[str, AxisField]
    values: Dict[str, float]

    def __init__(self, axis_id: Optional[str] = None, label: str = "", **kwargs):
        name = kwargs.get("name")
        if axis_id is None:
            axis_id = name
        self.axis_id = axis_id
        self.name = name or axis_id
        self.label = label
        self.coordinate = kwargs.get("coordinate", (0.0, 0.0, 0.0))
        self.weight = kwargs.get("weight", 1.0)
        self.values = {}
        if self.name:
            try:
                from core.state.axis_field import AxisFieldRegistry

                for field in AxisFieldRegistry().fields_for(self.name):
                    self.values.setdefault(field.name, field.default)
            except Exception as e:
                logger.debug(f"AxisFieldRegistry lookup failed for {self.name}: {e}")
        initial = kwargs.get("initial_values") or kwargs.get("_values")
        if initial:
            self.values.update(initial)
        self._fields = {}

    @classmethod
    def from_config(cls, axis_id: Optional[str] = None, label: str = "", **kwargs) -> "Axis":
        label = kwargs.pop("label", label)
        return cls(axis_id, label=label, **kwargs)

    def set(self, field_type, value, clamp=True):
        key = field_type.name if hasattr(field_type, "name") else str(field_type)
        if clamp and hasattr(field_type, "clamp"):
            value = field_type.clamp(value)
        self.values[key] = value
        return value

    def get(self, field_type):
        key = field_type.name if hasattr(field_type, "name") else str(field_type)
        if key in self.values:
            return self.values[key]
        if hasattr(field_type, "default"):
            return field_type.default
        return None

    def average(self):
        vals = list(self.values.values())
        return sum(vals) / len(vals) if vals else 0.0

    def dominant(self):
        if not self.values:
            return ("", 0.0)
        max_key = max(self.values, key=self.values.get)
        return (max_key, self.values[max_key])

    # --- Category A: Storable / State -------------------------------------------------
    def modify(self, field, delta):
        current = self.get(field)
        new_val = current + delta if current is not None else delta
        return self.set(field, new_val)

    def update(self, **kwargs):
        self.values.update(kwargs)

    def snapshot(self):
        return dict(self.values)

    def load_snapshot(self, snap):
        self.values.update(snap)

    def set_str(self, name, value):
        self.values[name] = value

    def get_str(self, name, default=None):
        return self.values.get(name, default)

    # --- Category B: Factory classmethods ---------------------------------------------
    @classmethod
    def create_alpha(cls, weight=1.0):
        return cls(name="alpha", label="生理", coordinate=(0.0, -5.0, 0.0), weight=weight)

    @classmethod
    def create_beta(cls, weight=1.0):
        return cls(name="beta", label="認知", coordinate=(0.0, 10.0, 0.0), weight=weight)

    @classmethod
    def create_gamma(cls, weight=1.0):
        return cls(name="gamma", label="情感", coordinate=(0.0, 0.0, -10.0), weight=weight)

    @classmethod
    def create_delta(cls, weight=1.0):
        return cls(name="delta", label="社會", coordinate=(0.0, 0.0, 10.0), weight=weight)

    @classmethod
    def create_epsilon(cls, weight=1.0):
        return cls(name="epsilon", label="感知", coordinate=(10.0, 0.0, 0.0), weight=weight)

    @classmethod
    def create_theta(cls, weight=1.0):
        return cls(name="theta", label="元認知", coordinate=(-10.0, 0.0, 0.0), weight=weight)

    @classmethod
    def create_all(cls, config=None):
        config = config or {}
        return [
            cls.create_alpha(config.get("alpha_weight", 1.0)),
            cls.create_beta(config.get("beta_weight", 1.0)),
            cls.create_gamma(config.get("gamma_weight", 1.0)),
            cls.create_delta(config.get("delta_weight", 1.0)),
            cls.create_epsilon(config.get("epsilon_weight", 1.0)),
            cls.create_theta(config.get("theta_weight", 1.0)),
        ]

    # --- Category C: Math / geometry --------------------------------------------------
    def shift(self, dx=0.0, dy=0.0, dz=0.0):
        x, y, z = self.coordinate
        self.coordinate = (x + dx, y + dy, z + dz)

    def distance_to(self, other):
        import math

        return math.sqrt(sum((a - b) ** 2 for a, b in zip(self.coordinate, other.coordinate)))

    def influence_factor_to(self, other):
        d = self.distance_to(other)
        return 2.0 / (1.0 + d)

    # --- Category D: Dunder / meta ----------------------------------------------------
    def __repr__(self):
        items = ", ".join(f"{k}={v:.2f}" for k, v in self.values.items())
        return f"Axis({self.name}, {{{items}}})" if items else f"Axis({self.name})"

    def field_count(self):
        return len(self.values)

    def variance(self):
        vals = list(self.values.values())
        if len(vals) < 2:
            return 0.0
        mean = sum(vals) / len(vals)
        return sum((v - mean) ** 2 for v in vals) / len(vals)

    def field_names(self):
        return list(self.values.keys())
