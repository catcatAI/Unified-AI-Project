import logging
import json
from typing import Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

class EvolutionEngine:
    """
    Angela AI 演化引擎 (M5/M6 Module)
    負責將交互經驗與反思轉化為性格權重的永久性優化
    """
    def __init__(self, personality_manager):
        self.pm = personality_manager
        self.learning_rate = 0.05 # 演化步伐

    async def reflect_and_evolve(self, interaction_result: Dict[str, Any]):
        """
        核心演化函數：根據互動結果動態調整性格權重 (2030 Persistent Standard).
        """
        if not self.pm:
            logger.warning("⚠️ [Evolution] PersonalityManager not available. Skipping evolution.")
            return

        feedback = interaction_result.get("feedback", {})
        sentiment = interaction_result.get("sentiment", 0.0)
        
        # 演化邏輯：如果用戶滿意度高 (sentiment > 0.5)，則強化對話策略
        if sentiment > 0.5:
            # 增強 Angela 的活躍度與好奇心 (持久化)
            current_arousal = self.pm.get_current_personality_trait("traits.arousal_gain", 0.1)
            current_curiosity = self.pm.get_current_personality_trait("traits.curiosity", 0.7)
            
            adjustment = {
                "traits.arousal_gain": min(0.3, current_arousal + 0.01),
                "traits.curiosity": min(1.0, current_curiosity + 0.02)
            }
            self.pm.apply_personality_adjustment(adjustment, persist=True)
            logger.info(f"📈 [Evolution] Angela evolved: Positive reinforcement applied. New curiosity: {adjustment['traits.curiosity']:.2f}")
        
        # 如果觸發了護盾 (EgoGuard)，則演化保護權重
        if interaction_result.get("security_hit", False):
            current_ego = self.pm.get_current_personality_trait("traits.ego_strength", 0.5)
            adjustment = {"traits.ego_strength": min(1.0, current_ego + 0.05)}
            self.pm.apply_personality_adjustment(adjustment, persist=True)
            logger.info(f"🛡️ [Evolution] Angela evolved: Ego strength increased to {adjustment['traits.ego_strength']:.2f}")

    def get_evolution_metrics(self) -> Dict[str, Any]:
        """查看 Angela 的演化指標"""
        return {
            "current_learning_rate": self.learning_rate,
            "traits": self.pm.current_personality.get("traits", {})
        }
