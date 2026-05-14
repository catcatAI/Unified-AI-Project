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
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any


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

    def __post_init__(self):
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

    _instance: Optional["AxisFieldRegistry"] = None
    _fields: Dict[str, Dict[str, AxisField]] = {}
    _by_name: Dict[str, AxisField] = {}

    def __new__(cls) -> "AxisFieldRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
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
        """註冊所有預定義的 field"""

        # === α (Alpha) — 生理維度 ===
        self._register(AxisField(
            axis="alpha", name="energy", label="能量",
            default=0.5, description="生理能量水平"
        ))
        self._register(AxisField(
            axis="alpha", name="comfort", label="舒適",
            default=0.5, description="身體舒適程度"
        ))
        self._register(AxisField(
            axis="alpha", name="arousal", label="喚醒",
            default=0.5, description="生理喚醒水平"
        ))
        self._register(AxisField(
            axis="alpha", name="rest_need", label="休息需求",
            default=0.5, description="需要休息的程度"
        ))
        self._register(AxisField(
            axis="alpha", name="vitality", label="活力",
            default=0.5, description="生命力與活力"
        ))
        self._register(AxisField(
            axis="alpha", name="tension", label="張力",
            default=0.0, description="肌肉/生理緊張程度"
        ))

        # === β (Beta) — 認知維度 ===
        self._register(AxisField(
            axis="beta", name="curiosity", label="好奇心",
            default=0.5, description="對新事物的探索慾望"
        ))
        self._register(AxisField(
            axis="beta", name="focus", label="專注",
            default=0.5, description="注意力集中程度"
        ))
        self._register(AxisField(
            axis="beta", name="confusion", label="困惑",
            default=0.0, description="認知模糊/不理解程度"
        ))
        self._register(AxisField(
            axis="beta", name="learning", label="學習",
            default=0.5, description="學習狀態與意願"
        ))
        self._register(AxisField(
            axis="beta", name="clarity", label="清晰",
            default=0.5, description="思維清晰程度"
        ))
        self._register(AxisField(
            axis="beta", name="creativity", label="創造",
            default=0.5, description="創造性思維活躍度"
        ))

        # === γ (Gamma) — 情感維度 ===
        self._register(AxisField(
            axis="gamma", name="happiness", label="快樂",
            default=0.5, description="正向情感"
        ))
        self._register(AxisField(
            axis="gamma", name="sadness", label="悲傷",
            default=0.0, description="悲傷程度"
        ))
        self._register(AxisField(
            axis="gamma", name="anger", label="憤怒",
            default=0.0, description="憤怒程度"
        ))
        self._register(AxisField(
            axis="gamma", name="fear", label="恐懼",
            default=0.0, description="恐懼程度"
        ))
        self._register(AxisField(
            axis="gamma", name="disgust", label="厭惡",
            default=0.0, description="厭惡程度"
        ))
        self._register(AxisField(
            axis="gamma", name="surprise", label="驚訝",
            default=0.0, description="驚訝程度"
        ))
        self._register(AxisField(
            axis="gamma", name="trust", label="信任",
            default=0.5, description="對人或事的信任程度"
        ))
        self._register(AxisField(
            axis="gamma", name="anticipation", label="期待",
            default=0.5, description="對未來的期待程度"
        ))
        self._register(AxisField(
            axis="gamma", name="love", label="愛",
            default=0.0, description="愛/親密情感"
        ))
        self._register(AxisField(
            axis="gamma", name="calm", label="平靜",
            default=0.5, description="內心平靜程度"
        ))

        # === δ (Delta) — 社交維度 ===
        self._register(AxisField(
            axis="delta", name="attention", label="注意力",
            default=0.5, description="對環境/他人的關注程度"
        ))
        self._register(AxisField(
            axis="delta", name="bond", label="連結",
            default=0.5, description="社交連結/依附程度"
        ))
        self._register(AxisField(
            axis="delta", name="trust", label="社交信任",
            default=0.5, description="社交場景中的信任"
        ))
        self._register(AxisField(
            axis="delta", name="presence", label="存在",
            default=0.5, description="社交存在感"
        ))
        self._register(AxisField(
            axis="delta", name="intimacy", label="親密",
            default=0.0, description="社交親密程度"
        ))
        self._register(AxisField(
            axis="delta", name="engagement", label="投入",
            default=0.5, description="社交活動投入程度"
        ))

        # === ε (Epsilon) — 數理維度 ===
        self._register(AxisField(
            axis="epsilon", name="logic", label="邏輯",
            default=0.5, description="邏輯推理能力"
        ))
        self._register(AxisField(
            axis="epsilon", name="precision", label="精確",
            default=0.5, description="精確計算程度"
        ))
        self._register(AxisField(
            axis="epsilon", name="abstraction", label="抽象",
            default=0.5, description="抽象思維能力"
        ))
        self._register(AxisField(
            axis="epsilon", name="certainty", label="確定",
            default=0.5, description="對結論的確信程度"
        ))
        self._register(AxisField(
            axis="epsilon", name="complexity", label="複雜",
            default=0.0, description="處理的複雜度水平"
        ))
        self._register(AxisField(
            axis="epsilon", name="fatigue", label="認知疲勞",
            default=0.0, description="數學運算帶來的疲勞"
        ))

        # === θ (Theta) — 元認知維度 ===
        self._register(AxisField(
            axis="theta", name="novelty", label="新穎",
            default=0.5, description="對新事物的感知程度"
        ))
        self._register(AxisField(
            axis="theta", name="complexity", label="認知複雜",
            default=0.5, description="任務/輸入的認知複雜度"
        ))
        self._register(AxisField(
            axis="theta", name="ambiguity", label="模糊",
            default=0.5, description="輸入的不確定程度"
        ))
        self._register(AxisField(
            axis="theta", name="abstraction_level", label="抽象層",
            default=0.5, description="處理的抽象層次"
        ))
        self._register(AxisField(
            axis="theta", name="dimension_fit", label="維度匹配",
            default=0.5, description="與現有軸的匹配程度"
        ))
        self._register(AxisField(
            axis="theta", name="creation_urge", label="創造慾",
            default=0.0, description="創建新軸的驅動程度"
        ))
        self._register(AxisField(
            axis="theta", name="theta_negativity", label="負值懷疑",
            default=0.0, description="對當前分配的懷疑程度"
        ))
        self._register(AxisField(
            axis="theta", name="correction_urge", label="修正慾",
            default=0.0, description="驅動自動修正的程度"
        ))
        self._register(AxisField(
            axis="theta", name="audit_intensity", label="審計強度",
            default=0.0, description="歷史掃描的深度"
        ))

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
        return cls._registry.get(axis, name)