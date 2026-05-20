# =============================================================================
# ANGELA-MATRIX: L3 βδ A L3
# =============================================================================

"""
EvolutionEngine — 性格演化引擎
===============================

B17 修復：原本 chat_service.py:38 引用了不存在的檔案，
創建此 stub 以修復 RuntimeError。

P0.2-D 修復：將 stub 串入實體人格管理器 (PersonalityManager) 學習與演化迴路。

職責：根據情感/安全性反饋調整人格參數（ PersonalityManager）。

Author: Angela AI v6.4.0
"""

import logging
from typing import Any, Dict, Optional

from ai.personality.personality_manager import PersonalityManager

logger = logging.getLogger(__name__)


class EvolutionEngine:
    """
    性格演化引擎。

    根據反饋數據（情感、安全性）調整人格狀態並持久化。
    """

    def __init__(self, personality_manager: PersonalityManager):
        self._personality = personality_manager
        self._evolution_count: int = 0

    async def reflect_and_evolve(self, feedback: Dict[str, Any]) -> None:
        """
        根據反饋反思並演化人格。

        Args:
            feedback: 包含 sentiment、security_hit 等鍵的字典
        """
        self._evolution_count += 1
        sentiment = feedback.get("sentiment", 0.5)
        security_hit = feedback.get("security_hit", False)

        adjustments = {}

        # 讀取當前的 values 做增量計算，避免覆蓋寫入 ad-hoc values
        curiosity_base = self._personality.get_current_personality_trait(
            "traits.personality.curiosity_base", 0.8
        )
        social_trust = self._personality.get_current_personality_trait(
            "traits.personality.social_trust", 0.7
        )
        ego_strength = self._personality.get_current_personality_trait(
            "traits.personality.ego_strength", 0.6
        )

        if security_hit:
            logger.debug(
                f"[EvolutionEngine] Security violation feedback "
                f"(evolution #{self._evolution_count})"
            )
            # 安全防衛被觸發，調高自我防護，降低社交信任
            adjustments["traits.personality.ego_strength"] = min(1.0, ego_strength + 0.05)
            adjustments["traits.personality.social_trust"] = max(0.0, social_trust - 0.05)
        else:
            logger.debug(
                f"[EvolutionEngine] Evolved personality "
                f"(sentiment={sentiment:.2f}, #{self._evolution_count})"
            )
            # 正向情感，稍微增加信任和好奇心；負向則稍微調降
            sentiment_delta = (sentiment - 0.5) * 0.02
            adjustments["traits.personality.social_trust"] = min(
                1.0, max(0.0, social_trust + sentiment_delta)
            )
            adjustments["traits.personality.curiosity_base"] = min(
                1.0, max(0.0, curiosity_base + sentiment_delta * 0.5)
            )

        if adjustments:
            try:
                # 調用 PersonalityManager 的 apply_personality_adjustment 來進行演化並持久化
                self._personality.apply_personality_adjustment(adjustments, persist=True)
                logger.info(
                    f"[EvolutionEngine] Evolution #{self._evolution_count} applied traits adjustments: {adjustments}"
                )
            except Exception as e:
                logger.error(f"[EvolutionEngine] Failed to apply personality adjustments: {e}")