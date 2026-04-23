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
        核心演化函數：根據互動結果動態調整性格權重
        """
        feedback = interaction_result.get("feedback", {})
        sentiment = interaction_result.get("sentiment", 0.0)
        
        # 演化邏輯：如果用戶滿意度高 (sentiment > 0.5)，則強化對話策略
        if sentiment > 0.5:
            # 增強 Angela 的自信心或活躍度
            adjustment = {"arousal_gain": 0.01, "confidence_boost": 0.02}
            self.pm.apply_personality_adjustment(adjustment)
            logger.info("📈 [Evolution] Angela evolved: Positive reinforcement applied.")
        
        # 如果觸發了護盾 (EgoGuard)，則演化保護權重
        if interaction_result.get("security_hit", False):
            adjustment = {"ego_strength": 0.05}
            self.pm.apply_personality_adjustment(adjustment)
            logger.info("🛡️ [Evolution] Angela evolved: Ego strength increased.")

    def get_evolution_metrics(self) -> Dict[str, Any]:
        """查看 Angela 的演化指標"""
        return {
            "current_learning_rate": self.learning_rate,
            "traits": self.pm.current_personality.get("traits", {})
        }
