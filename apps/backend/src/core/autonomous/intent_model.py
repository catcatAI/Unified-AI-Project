
import logging
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

logger = logging.getLogger(__name__)

# =============================================================================
# ANGELA-MATRIX: [L4] [αβγδ] [A] [L10+]
# [Task N.21.1] 原生意圖表徵 (Native Intent Representation)
# =============================================================================

class IntentCategory(Enum):
    HOMEOSTASIS = auto()   # 穩態驅動 (生存、休息、能量平衡)
    EXPLORATION = auto()   # 探索驅動 (學習、求知、新奇感)
    SOCIAL_BOND = auto()   # 社交驅動 (信任、親密度、互動)
    SELF_PRESERVATION = auto() # 自我防衛 (壓力緩解、情緒穩定)

@dataclass
class SelfIntent:
    """
    Angela 的自我意圖，表現為 4D 空間中的一個位能目標點。
    Represented as a potential target point in 4D coordinate space.
    """
    id: str
    category: IntentCategory
    target_dimension: str      # 目標維度 (alpha, beta, gamma, delta)
    target_coordinate: Tuple[float, float, float] # 目標座標 [x, y, z]
    urgency: float = 0.5       # 緊急程度 (0~1)
    strength: float = 1.0      # 意圖強度/重力權重
    created_at: datetime = field(default_factory=datetime.now)
    decay_rate: float = 0.01   # 每秒衰減速度
    
    def is_expired(self) -> bool:
        return self.strength <= 0

class IntentManager:
    """
    意圖管理器：負責生成、維持與衰減 Angela 的內在驅動力。
    """
    def __init__(self):
        self.intents: List[SelfIntent] = []
        self.active_intent_vector: Dict[str, Tuple[float, float, float]] = {
            "alpha": (0.0, 0.0, 0.0),
            "beta": (0.0, 0.0, 0.0),
            "gamma": (0.0, 0.0, 0.0),
            "delta": (0.0, 0.0, 0.0)
        }

    def add_intent(self, intent: SelfIntent):
        """新增一個意圖點"""
        self.intents.append(intent)
        logger.info(f"🎯 [Intent] New intent added: {intent.category.name} -> {intent.target_dimension} @ {intent.target_coordinate}")

    def update_intents(self, delta_time: float = 1.0):
        """更新意圖強度並移除過期意圖"""
        for intent in self.intents:
            intent.strength -= intent.decay_rate * delta_time
        
        # 移除失效意圖
        self.intents = [i for i in self.intents if not i.is_expired()]
        
        # 重新計算當前意圖合力向量 (Weighted average of intent targets)
        self._calculate_active_vectors()

    def _calculate_active_vectors(self):
        """計算所有活躍意圖對各個維度的合成重力場"""
        new_vectors = {dim: [0.0, 0.0, 0.0] for dim in ["alpha", "beta", "gamma", "delta"]}
        counts = {dim: 0 for dim in ["alpha", "beta", "gamma", "delta"]}
        
        for intent in self.intents:
            dim = intent.target_dimension
            target = intent.target_coordinate
            weight = intent.strength * intent.urgency
            
            for i in range(3):
                new_vectors[dim][i] += target[i] * weight
            counts[dim] += weight

        # 正規化
        for dim in new_vectors:
            if counts[dim] > 0:
                self.active_intent_vector[dim] = tuple([v / counts[dim] for v in new_vectors[dim]])
            else:
                self.active_intent_vector[dim] = (0.0, 0.0, 0.0)

    def get_intent_influence(self, dimension: str) -> Tuple[float, float, float]:
        """獲取特定維度受到的意圖吸引力方向"""
        return self.active_intent_vector.get(dimension, (0.0, 0.0, 0.0))

    def generate_homeostatic_intents(self, state_matrix_summary: Dict[str, Any]):
        """
        根據當前狀態自動生成維護穩態的意圖。
        (例如：能量低時生成去休息的意圖)
        """
        # 範例邏輯：如果 Wellbeing 太低，生成自我修復意圖
        wellbeing = state_matrix_summary.get("wellbeing", 1.0)
        if wellbeing < 0.3:
            recovery_intent = SelfIntent(
                id=f"recover_{datetime.now().timestamp()}",
                category=IntentCategory.SELF_PRESERVATION,
                target_dimension="alpha",
                target_coordinate=(0.0, 0.0, 0.0), # 回歸原點(穩定)
                urgency=0.9,
                strength=2.0,
                decay_rate=0.05
            )
            self.add_intent(recovery_intent)
