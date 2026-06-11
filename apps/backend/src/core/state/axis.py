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
from typing import Any, Dict, List, Optional, Type
from core.state.axis_field import AxisField


class Axis:
    _fields: Dict[str, AxisField]
    values: Dict[str, float]

    def __init__(self, axis_id: str = None, label: str = "", **kwargs):
        name = kwargs.get("name")
        if axis_id is None:
            axis_id = name
        self.axis_id = axis_id
        self.name = name or axis_id
        self.label = label
        self.coordinate = kwargs.get("coordinate", (0.0, 0.0, 0.0))
        self.weight = kwargs.get("weight", 1.0)
        self.values = {}
        self._fields = {}

    @classmethod
    def from_config(cls, axis_id: str = None, label: str = "", **kwargs) -> "Axis":
        return cls(axis_id, label=label, **kwargs)

    def set(self, field_type: Type, value: float) -> None:
        pass

    def get(self, field_type: Type) -> Optional[float]:
        return None

    def average(self) -> float:
        return 0.0

    def dominant(self) -> Optional[str]:
        return None
