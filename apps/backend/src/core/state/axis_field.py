"""
Axis Field Registry — 軸域註冊表
==================================

所有軸的 field 定義集中於此。
每個 AxisField 知道自己屬於哪個軸、名稱、類型、範圍、描述。

使用方式:
    from core.state.axis_field import AxisField, AxisFieldRegistry

    # 取得某個軸的所有 field
    alpha_fields = AxisFieldRegistry.fields_for('alpha')

    # 設定值（typed，IDE自動完成）
    axis.set(FocusField, 0.8)

    # 驗證範圍
    is_valid = FocusField.in_range(0.5)  # True
    is_valid = FocusField.in_range(2.0)  # False

Author: Angela AI v6.2
Version: 6.2.1
"""

from __future__ import annotations
import json
import logging
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AxisField:
    """
    軸域定義（不可變）— 代表某個軸上的一個具名測量

    每個 field 知道：
    - 自己屬於哪個軸
    - 名稱與中文標籤
    - 值的有效範圍 [min, max]
    - 預設值
    - 描述

    使用 frozen=True 確保 field 作為 dict key 或 set 元素是安全的。
    """

    axis: str
    name: str
    label: str
    min_val: float = 0.0
    max_val: float = 1.0
    default: float = 0.5
    description: str = ""

    def __post_init__(self) -> None:
        """Execute the   post init   operation."""
        if self.min_val >= self.max_val:
            raise ValueError(f"AxisField '{self.name}': min_val ({self.min_val}) >= max_val ({self.max_val})")

    def in_range(self, value: float) -> bool:
        """檢查值是否在有效範圍內"""
        return self.min_val <= value <= self.max_val

    def clamp(self, value: float) -> float:
        """將值限制在有效範圍內"""
        return max(self.min_val, min(self.max_val, value))

    def normalize(self, value: float) -> float:
        """將值正規化到 [0, 1] 區間"""
        if self.max_val == self.min_val:
            return 0.0
        return (value - self.min_val) / (self.max_val - self.min_val)

    def __repr__(self) -> str:
        return f"AxisField({self.axis}.{self.name}, default={self.default})"

    def __hash__(self) -> int:
        return hash((self.axis, self.name))

    def __eq__(self, other: object) -> bool:
        """Check equality based on axis and field name."""
        if not isinstance(other, AxisField):
            return NotImplemented
        return self.axis == other.axis and self.name == other.name


class AxisFieldRegistry:
    """
    全局軸域註冊表
    ===============

    所有 AxisField 實例在此註冊，提供快速查詢：
    - 某個軸的所有 field
    - 某個 field 的定義
    - 所有 field 按軸分組

    單例模式，確保全局只有一個註冊表。
    """

    _fields: Dict[str, Dict[str, AxisField]] = {}
    _by_name: Dict[str, AxisField] = {}

    def __init__(self):
        if getattr(self, "_initialized", False):
            return
        self._initialized = True
        self._register_all_fields()

    def _register(self, field: AxisField) -> None:
        """註冊一個 field"""
        axis = field.axis
        name = field.name
        if axis not in self._fields:
            self._fields[axis] = {}
        self._fields[axis][name] = field
        self._by_name[f"{axis}.{name}"] = field

    def _register_all_fields(self) -> None:
        _dir = os.path.dirname(os.path.abspath(__file__))
        _path = os.path.join(_dir, "axis_fields.json")
        try:
            with open(_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning("axis_fields.json not found or invalid: %s", e)
            data = []
        for item in data:
            self._register(AxisField(**item))

    def get(self, axis: str, name: str) -> Optional[AxisField]:
        """取得特定軸的特定 field"""
        return self._fields.get(axis, {}).get(name)

    def get_by_key(self, key: str) -> Optional[AxisField]:
        """以 'axis.name' 格式取得 field（用於歷史快照解析）"""
        return self._by_name.get(key)

    def fields_for(self, axis: str) -> List[AxisField]:
        """取得某個軸的所有 field"""
        return list(self._fields.get(axis, {}).values())

    def all_axes(self) -> List[str]:
        """取得所有已註冊的軸名"""
        return list(self._fields.keys())

    def all_fields(self) -> List[AxisField]:
        """取得所有 field"""
        return list(self._by_name.values())

    def count(self) -> int:
        """總 field 數"""
        return len(self._by_name)

    def validate_axis_values(self, axis: str, values: Dict[str, float]) -> Dict[str, Tuple[bool, Optional[str]]]:
        """
        驗證某個軸的一組值，返回每個 key 的驗證結果

        Returns:
            Dict[key -> (is_valid, error_message)]
        """
        results = {}
        axis_fields = self._fields.get(axis, {})
        for key, value in values.items():
            field = axis_fields.get(key)
            if field is None:
                results[key] = (True, None)
                continue
            if not field.in_range(value):
                results[key] = (False, f"{key} value {value} outside range [{field.min_val}, {field.max_val}]")
            else:
                results[key] = (True, None)
        return results

    def schema_for(self, axis: str) -> Dict[str, Dict[str, Any]]:
        """取得某個軸的完整 schema（用於配置序列化）"""
        fields = self.fields_for(axis)
        return {
            f.name: {
                "label": f.label,
                "min": f.min_val,
                "max": f.max_val,
                "default": f.default,
                "description": f.description,
            }
            for f in fields
        }


class AxisFieldEnum(Enum):
    """
    便捷的 AxisField 枚舉包裝。

    使用方式：
        EnergyField = AxisFieldEnum.get("alpha", "energy")
        axis.set(EnergyField, 0.8)

    但推薦直接用 AxisFieldRegistry.fields_for('alpha') 返回的列表。
    """

    _registry: AxisFieldRegistry = field(default_factory=AxisFieldRegistry)

    @classmethod
    def get(cls, axis: str, name: str) -> Optional[AxisField]:
        """Execute the get operation."""
        return cls._registry.get(axis, name)