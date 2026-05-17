"""
EvolutionEngine — 性格演化引擎
===============================

B17 修復：原本 chat_service.py:38 引用了不存在的檔案，
創建此 stub 以修復 RuntimeError。

職責：根據情感/安全性反饋調整人格參數（ PersonalityManager）。

Author: Angela AI v6.2.5
"""

import logging
from typing import Any, Dict, Optional

from ai.personality.personality_manager import PersonalityManager

logger = logging.getLogger(__name__)


class EvolutionEngine:
    """
    性格演化引擎。

    根據反饋數據（情感、安全性）調整人格狀態。
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

        if security_hit:
            logger.debug(
                f"[EvolutionEngine] Security violation feedback "
                f"(evolution #{self._evolution_count})"
            )
        else:
            logger.debug(
                f"[EvolutionEngine] Evolved personality "
                f"(sentiment={sentiment:.2f}, #{self._evolution_count})"
            )