
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
        """更新意圖強度 (非線性衰減) 並移除過期意圖"""
        for intent in self.intents:
            # [Task N.21.5] 非線性衰減 (Exponential Decay)
            # 讓強烈意圖在初期保持，隨後緩慢消逝
            intent.strength *= (1.0 - intent.decay_rate) ** delta_time
        
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

    def generate_homeostatic_intents(self, state_summary: Dict[str, Any]):
        """
        [N.21.2] 根據當前狀態自動生成維護穩態與探索的意圖。
        Generate self-drive intents based on state matrix summary.
        """
        # 1. 生理穩態 (Alpha Drive) - 能量低落時產生休息意圖
        alpha_stats = state_summary.get("alpha", {})
        energy = alpha_stats.get("energy", 1.0)
        if energy < 0.3:
            self.add_intent(SelfIntent(
                id=f"rest_{datetime.now().timestamp()}",
                category=IntentCategory.HOMEOSTASIS,
                target_dimension="alpha",
                target_coordinate=(0.0, 0.0, 0.0), # 回歸穩定原點
                urgency=1.0 - energy,
                strength=1.5
            ))

        # 2. 認知探索 (Beta/Gamma Drive) - 幸福感低或無聊時產生探索意圖
        gamma_stats = state_summary.get("gamma", {})
        happiness = gamma_stats.get("happiness", 1.0)
        if happiness < 0.4:
            self.add_intent(SelfIntent(
                id=f"explore_{datetime.now().timestamp()}",
                category=IntentCategory.EXPLORATION,
                target_dimension="gamma",
                target_coordinate=(8.0, 2.0, 0.0), # 移向高刺激區
                urgency=0.6,
                strength=1.2
            ))

        # 3. 社交連結 (Delta Drive) - 孤獨感或親密度下降時產生社交意圖
        delta_stats = state_summary.get("delta", {})
        bond = delta_stats.get("bond", 0.5)
        if bond < 0.3:
            self.add_intent(SelfIntent(
                id=f"bond_{datetime.now().timestamp()}",
                category=IntentCategory.SOCIAL_BOND,
                target_dimension="delta",
                target_coordinate=(5.0, 5.0, 5.0), # 移向互動中心
                urgency=0.7,
                strength=1.3
            ))

        logger.debug(f"🧬 [IntentManager] Homeostatic check complete. Active intents: {len(self.intents)}")

    def scan_memory_proximity(self, memory_bridge: Any, current_states: Dict[str, Any]):
        """
        [Task N.21.6] 空間記憶自動激活
        當座標接近某個記憶錨點時，自動產生「聯想意圖」。
        """
        for dim_name, state_values in current_states.items():
            # 假設 DimensionState 已經有 coordinate (我們從 state_matrix 傳入)
            coord = state_values.get("coordinate", (0.0, 0.0, 0.0))
            x, y, z = coord
            
            # 使用記憶橋接器的空間檢索 (半徑 5.0)
            nearby_ids = memory_bridge.retrieve_by_spatial_proximity(x, y, z, radius=5.0)
            
            for mem_id in nearby_ids:
                # 如果已經有相同記憶的意圖，跳過
                if any(str(mem_id) in i.id for i in self.intents):
                    continue
                
                # 獲取記憶座標 (從 metadata)
                meta = memory_bridge._memory_metadata.get(mem_id, {})
                mem_coord = meta.get("coordinate", (0.0, 0.0, 0.0))
                
                # 產生「聯想/回憶」意圖
                self.add_intent(SelfIntent(
                    id=f"recall_{mem_id}",
                    category=IntentCategory.EXPLORATION,
                    target_dimension=dim_name,
                    target_coordinate=mem_coord,
                    urgency=0.4,
                    strength=0.8,
                    decay_rate=0.02
                ))



