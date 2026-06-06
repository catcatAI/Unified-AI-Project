"""
Angela AI v6.0 - Endocrine System Types
内分泌系统类型定义

Defines the core data types for the endocrine system:
- HormoneType enum (12 hormone types)
- Hormone dataclass (hormone entity with pharmacokinetics)
- HormonalEffect dataclass (hormonal effects on systems)

Author: Angela AI Development Team
Version: 6.0.0
"""

# =============================================================================
# ANGELA-MATRIX: L1[生物层] α [A] L2+
# =============================================================================
#
# 职责: 定义内分泌系统的核心数据类型
# 维度: 主要影响生理维度 (α) 的能量、舒适度、唤醒度、活力等
# 安全: 使用 Key A (后端控制) 进行激素状态管理
# 成熟度: L2+ 等级开始理解内分泌系统对行为的影响
#
# 激素类型:
# - 肾上腺素 (Adrenaline): 压力反应、能量提升
# - 皮质醇 (Cortisol): 压力管理、代谢调节
# - 多巴胺 (Dopamine): 奖励机制、动机驱动
# - 血清素 (Serotonin): 情绪稳定、幸福感
# - 催产素 (Oxytocin): 社交纽带、信任感
# - 内啡肽 (Endorphin): 疼痛缓解、愉悦感
# - 甲状腺素 (Thyroxine): 代谢调节、能量调节
# - 雌激素/睾酮 (Estrogen/Testosterone): 生殖系统、活力
# - 生长激素 (Growth Hormone): 生长、修复
# - 胰岛素 (Insulin): 葡萄糖调节、能量存储
# - 褪黑素 (Melatonin): 睡眠调节、昼夜节律
# - 去甲肾上腺素 (Norepinephrine): 警觉性、专注度
#
# =============================================================================

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import math


class HormoneType(Enum):
    """12种激素类型 / 12 hormone types"""

    ADRENALINE = ("肾上腺素", "Adrenaline", "stress_response", "energy_boost")
    CORTISOL = ("皮质醇", "Cortisol", "stress_management", "metabolism")
    DOPAMINE = ("多巴胺", "Dopamine", "reward", "motivation")
    SEROTONIN = ("血清素", "Serotonin", "mood_stability", "wellbeing")
    OXYTOCIN = ("催产素", "Oxytocin", "bonding", "social_trust")
    ENDORPHIN = ("内啡肽", "Endorphin", "pain_relief", "pleasure")
    THYROXINE = ("甲状腺素", "Thyroxine", "metabolism", "energy_regulation")
    ESTROGEN_TESTOSTERONE = ("雌激素/睾酮", "Estrogen/Testosterone", "reproductive", "vitality")
    GROWTH_HORMONE = ("生长激素", "Growth Hormone", "growth", "repair")
    INSULIN = ("胰岛素", "Insulin", "glucose_regulation", "energy_storage")
    MELATONIN = ("褪黑素", "Melatonin", "sleep_regulation", "circadian_rhythm")
    NOREPINEPHRINE = ("去甲肾上腺素", "Norepinephrine", "alertness", "focus")

    def __init__(self, cn_name: str, en_name: str, primary_role: str, secondary_role: str):
        self.cn_name = cn_name
        self.en_name = en_name
        self.primary_role = primary_role
        self.secondary_role = secondary_role


@dataclass
class Hormone:
    """
    激素實體 / Hormone Entity
    使用一室藥代動力學模型 (First-order Elimination Kinetics)
    """

    hormone_type: HormoneType
    base_level: float  # 穩態水平 (Steady-state level, 0-100)
    current_level: float  # 當前水平 / Current level
    half_life_minutes: float  # 半衰期 (分鐘) / Half-life in minutes
    production_rate: float = 0.0  # 基礎產生速率 (單位/分鐘) / Basal production rate
    min_level: float = 0.0
    max_level: float = 100.0
    last_update: datetime = field(default_factory=datetime.now)

    def __post_init__(self) -> None:
        """Execute the   post init   operation."""
        self.current_level = max(self.min_level, min(self.max_level, self.current_level))
        # 計算消除常數 k = ln(2) / t1/2
        self._k = math.log(2) / max(0.1, self.half_life_minutes)

    def get_normalized_level(self) -> float:
        """獲取歸一化水平 (0-1)"""
        return (self.current_level - self.min_level) / (self.max_level - self.min_level)

    def update(self, dt_minutes: float = 1.0) -> None:
        """
        使用指數衰減模型更新激素水平
        公式: C(t) = C_ss + (C0 - C_ss) * e^(-k * t)
        其中 C_ss 是穩態水平 (base_level)
        """
        # 1. 計算自然代謝後的水平 (指數衰減至穩態)
        # 即使 current_level < base_level，此公式也會讓其平滑回歸至 base_level
        self.current_level = self.base_level + (self.current_level - self.base_level) * math.exp(-self._k * dt_minutes)

        # 2. 應用邊界限制
        self.current_level = max(self.min_level, min(self.max_level, self.current_level))
        self.last_update = datetime.now()

    def adjust(self, amount: float) -> None:
        """瞬時調整激素水平 (例如情緒衝擊)"""
        self.current_level = max(self.min_level, min(self.max_level, self.current_level + amount))


@dataclass
class HormonalEffect:
    """激素效果 / Hormonal effect"""

    target_system: str  # 目标系统 / Target system (emotion, energy, social, etc.)
    effect_type: str  # 效果类型 / Effect type
    magnitude: float  # 效果强度 (-1 to 1) / Effect magnitude
    duration: float  # 持续时间(分钟) / Duration in minutes
