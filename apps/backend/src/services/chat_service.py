# =============================================================================
# ANGELA-MATRIX: [L2] [αβγδ] [A] [L3+]
# =============================================================================
# 職責: 聊天與對話服務 (Chat Service)
# 管理 Angela 的對話邏輯、意圖識別與回應合成。
# =============================================================================

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class ChatService:
    """聊天服務 — 透過 AngelaLLMService 生成回應。"""

    def __init__(self, llm_service=None):
        self._llm_service = llm_service
        self._initialized = False
        self._continuous_learning = None

    async def initialize(self) -> None:
        if self._initialized:
            return
        if self._llm_service is None:
            from services.llm.router import AngelaLLMService
            self._llm_service = AngelaLLMService()
            await self._llm_service.initialize()
        try:
            from ai.ed3n.continuous_learning import ContinuousLearningPipeline
            from ai.ed3n.ed3n_engine import ED3NEngine
            engine = ED3NEngine()
            engine.load_presets()
            self._continuous_learning = ContinuousLearningPipeline(
                engine=engine,
                growth_interval=15,
                train_interval=50,
                min_examples_for_train=30,
            )
        except Exception as e:
            logger.warning("Continuous learning init skipped: %s", e)
        self._initialized = True
        logger.info("ChatService initialized")

    async def generate_response(self, user_message: str, user_name: str = "") -> str:
        """Generate Angela's response to a user message. Returns response text string."""
        if not self._initialized:
            await self.initialize()
        context: Dict[str, Any] = {"user_name": user_name}
        response = await self._llm_service.generate_response(user_message, context)
        if self._continuous_learning and response and response.text:
            try:
                await self._continuous_learning.process_interaction_async(
                    user_message, response.text, context
                )
            except Exception as e:
                logger.warning("Continuous learning interaction failed: %s", e)
        return response.text

    async def shutdown(self) -> None:
        self._initialized = False
        if self._continuous_learning:
            report = self._continuous_learning.get_learning_report()
            logger.info("Continuous learning final report:\n%s", report)
        logger.info("ChatService shutdown")

