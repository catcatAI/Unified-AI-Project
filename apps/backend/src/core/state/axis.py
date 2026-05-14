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
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any, Callable

from core.state.axis_field import AxisField, AxisFieldRegistry


@dataclass
class Axis:
    """
    軸 — 持有一組 field，坐標空間中的位置，語義描述

    與舊 DimensionState 的區別：
    - field 有 schema（AxisField），帶類型/範圍/描述
    - 支援 field-level 存取（typed）和字串存取（向後兼容）
    - 有統計方法（average, variance, trend）
    - 座標操作封裝
    """

    name: str
    label: str
    coordinate: Tuple[float, float, float] = field(default_factory=lambda: (0.0, 0.0, 0.0))
    weight: float = 1.0
    description: str = ""

    _values: Dict[str, float] = field(default_factory=dict)
    _timestamp: datetime = field(default_factory=datetime.now)

    _registry: AxisFieldRegistry = field(default_factory=AxisFieldRegistry)

    def __post_init__(self):
        if not self._values:
            self._init_from_registry()

    def _init_from_registry(self) -> None:
        """從註冊表初始化 field 值"""
        for field_def in self._registry.fields_for(self.name):
            self._values[field_def.name] = field_def.default

    # === 值存取 ===

    def get(self, field_def: AxisField, default: Optional[float] = None) -> float:
        """取得 field 值（typed）"""
        return self._values.get(field_def.name, default if default is not None else field_def.default)

    def set(self, field_def: AxisField, value: float, clamp: bool = True) -> float:
        """設定 field 值（typed）"""
        if clamp:
            value = field_def.clamp(value)
        self._values[field_def.name] = value
        self._timestamp = datetime.now()
        return value

    def modify(self, field_def: AxisField, delta: float) -> float:
        """對 field 值做增量修改"""
        current = self.get(field_def)
        new_val = field_def.clamp(current + delta)
        self._values[field_def.name] = new_val
        self._timestamp = datetime.now()
        return new_val

    def get_str(self, name: str, default: float = 0.0) -> float:
        """取得 field 值（字串，向後兼容）"""
        return self._values.get(name, default)

    def set_str(self, name: str, value: float, clamp: bool = True) -> float:
        """設定 field 值（字串，向後兼容）"""
        field_def = self._registry.get(self.name, name)
        if clamp and field_def:
            value = field_def.clamp(value)
        self._values[name] = value
        self._timestamp = datetime.now()
        return value

    def update(self, **kwargs) -> None:
        """批量更新（字串 key，向後兼容 DimensionState.update()）"""
        for name, value in kwargs.items():
            self.set_str(name, value, clamp=True)

    # === 統計 ===

    def average(self) -> float:
        """取得所有 field 的平均值"""
        if not self._values:
            return 0.0
        return sum(self._values.values()) / len(self._values)

    def dominant(self) -> Tuple[str, float]:
        """取得主導 field（值最大的）"""
        if not self._values:
            return ("", 0.0)
        return max(self._values.items(), key=lambda x: x[1])

    def variance(self) -> float:
        """取得 field 值的方差"""
        if len(self._values) < 2:
            return 0.0
        mean = self.average()
        return sum((v - mean) ** 2 for v in self._values.values()) / len(self._values)

    def field_count(self) -> int:
        """field 數量"""
        return len(self._values)

    def field_names(self) -> List[str]:
        """所有 field 名稱"""
        return list(self._values.keys())

    # === 坐標操作 ===

    def shift(self, dx: float = 0.0, dy: float = 0.0, dz: float = 0.0) -> None:
        """沿坐標軸移動"""
        x, y, z = self.coordinate
        self.coordinate = (x + dx, y + dy, z + dz)

    def distance_to(self, other: "Axis") -> float:
        """歐氏距離到另一個軸"""
        dx = self.coordinate[0] - other.coordinate[0]
        dy = self.coordinate[1] - other.coordinate[1]
        dz = self.coordinate[2] - other.coordinate[2]
        return (dx * dx + dy * dy + dz * dz) ** 0.5

    def influence_factor_to(self, other: "Axis", softening: float = 10.0) -> float:
        """計算對另一軸的影響因子（逆平方定律）"""
        dist = self.distance_to(other)
        return max(0.5, min(2.0, 25.0 / (dist * dist + softening)))

    # === 快照 ===

    def snapshot(self) -> Dict[str, float]:
        """取得當前值快照"""
        return self._values.copy()

    def load_snapshot(self, snapshot: Dict[str, float]) -> None:
        """從快照恢復"""
        for name, value in snapshot.items():
            self._values[name] = value
        self._timestamp = datetime.now()

    # === 配置 ===

    @classmethod
    def from_config(
        cls,
        name: str,
        label: str,
        coordinate: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        weight: float = 1.0,
        description: str = "",
        initial_values: Optional[Dict[str, float]] = None,
    ) -> "Axis":
        """從配置創建軸"""
        axis = cls(
            name=name,
            label=label,
            coordinate=coordinate,
            weight=weight,
            description=description,
        )
        if initial_values:
            for name_, value in initial_values.items():
                axis.set_str(name_, value)
        return axis

    # === 工廠方法 ===

    @classmethod
    def create_alpha(cls, weight: float = 1.0) -> "Axis":
        """創建 α 軸"""
        return cls.from_config(
            name="alpha", label="生理",
            coordinate=(0.0, -5.0, 0.0),
            weight=weight,
            description="Physiological dimension: energy, comfort, arousal",
        )

    @classmethod
    def create_beta(cls, weight: float = 1.0) -> "Axis":
        """創建 β 軸"""
        return cls.from_config(
            name="beta", label="認知",
            coordinate=(0.0, 10.0, 0.0),
            weight=weight,
            description="Cognitive dimension: curiosity, focus, learning",
        )

    @classmethod
    def create_gamma(cls, weight: float = 1.0) -> "Axis":
        """創建 γ 軸"""
        return cls.from_config(
            name="gamma", label="情感",
            coordinate=(0.0, 2.0, 2.0),
            weight=weight,
            description="Emotional dimension: happiness, sadness, anger, fear",
        )

    @classmethod
    def create_delta(cls, weight: float = 1.0) -> "Axis":
        """創建 δ 軸"""
        return cls.from_config(
            name="delta", label="社交",
            coordinate=(0.0, 0.0, 10.0),
            weight=weight,
            description="Social dimension: attention, bond, trust, presence",
        )

    @classmethod
    def create_epsilon(cls, weight: float = 0.3) -> "Axis":
        """創建 ε 軸"""
        return cls.from_config(
            name="epsilon", label="數理",
            coordinate=(0.0, 0.0, 0.0),
            weight=weight,
            description="Mathematical dimension: logic, precision, abstraction",
        )

    @classmethod
    def create_theta(cls, weight: float = 0.8) -> "Axis":
        """創建 θ 軸"""
        return cls.from_config(
            name="theta", label="元認知",
            coordinate=(0.0, 5.0, 5.0),
            weight=weight,
            description="Meta-cognitive dimension: novelty, complexity, ambiguity",
        )

    def __repr__(self) -> str:
        avg = self.average()
        dom_name, dom_val = self.dominant()
        return f"Axis({self.name}, avg={avg:.2f}, dominant={dom_name}({dom_val:.2f}))"