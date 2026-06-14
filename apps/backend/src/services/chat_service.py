# =============================================================================
# ANGELA-MATRIX: [L2] [αβγδ] [A] [L3+]
# =============================================================================
# 職責: 聊天與對話服務 (Chat Service)
# 管理 Angela 的對話邏輯、意圖識別與回應合成。
# =============================================================================

import logging
import os
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class ChatService:
    """聊天服務 — 透過 AngelaLLMService 生成回應。"""

    def __init__(self, llm_service=None):
        self._llm_service = llm_service
        self._initialized = False
        self._continuous_learning = None
        self._cl_state_dir = os.path.join(
            os.path.dirname(__file__), "..", "..", "..", "..", "data", "cl_state"
        )

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
            state_path = os.path.join(self._cl_state_dir, "cl_state.json")
            if os.path.exists(state_path):
                self._continuous_learning = ContinuousLearningPipeline.load(
                    self._cl_state_dir, engine=engine
                )
                logger.info("Loaded CL state from %s", state_path)
            else:
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

    async def generate_response(self, user_message: str, user_name: str = "", context: dict = None):
        """Generate Angela's response to a user message."""
        if not self._initialized:
            await self.initialize()

        merged_context = context or {}
        merged_context.setdefault("user_name", user_name)

        response = await self._llm_service.generate_response(user_message, merged_context)

        response = self._post_process_response(response, merged_context)

        if self._continuous_learning:
            try:
                await self._continuous_learning.process_interaction_async(
                    user_message, response.text, merged_context
                )
            except Exception as e:
                logger.warning("Continuous learning interaction failed: %s", e)

        return response

    def _post_process_response(self, response, context: dict):
        """Enrich response with biological/emotional state context.

        Ensures template-matched responses also carry emotional flavor
        instead of being returned as raw template text.
        """
        if not response or not response.text:
            return response

        bio_state = context.get("bio_state")
        emotion = context.get("emotion")
        user_name = context.get("user_name", "")

        if not bio_state and not emotion:
            return response

        mood = bio_state.get("mood", 0.5) if bio_state else 0.5
        stress = bio_state.get("stress_level", 0.0) if bio_state else 0.0
        dominant = bio_state.get("dominant_emotion", "calm") if bio_state else "calm"
        emo = emotion.get("emotion", "neutral") if emotion else "neutral"

        route = response.metadata.get("route", "") if response.metadata else ""

        if route in ("COMPOSED", "HYBRID") and bio_state:
            mood_hint = ""
            if mood > 0.7:
                mood_hint = "（心情很好）"
            elif mood < 0.3:
                mood_hint = "（心情有點低落）"

            stress_hint = ""
            if stress > 0.7:
                stress_hint = "（壓力有點大）"

            emo_map = {
                "happy": "😊", "calm": "😌", "sad": "😔",
                "angry": "😠", "fear": "😟", "surprise": "😲",
            }
            emo_suffix = emo_map.get(emo, "")

            if mood_hint or stress_hint or emo_suffix:
                suffix_parts = [s for s in [mood_hint, stress_hint, emo_suffix] if s]
                new_text = response.text.rstrip() + " " + "".join(suffix_parts)
                response = type(response)(
                    text=new_text,
                    backend=response.backend,
                    model=response.model,
                    tokens_used=response.tokens_used,
                    response_time_ms=response.response_time_ms,
                    confidence=response.confidence,
                    metadata={**(response.metadata or {}), "bio_enriched": True},
                )

        return response

    async def shutdown(self) -> None:
        self._initialized = False
        if self._continuous_learning:
            report = self._continuous_learning.get_learning_report()
            logger.info("Continuous learning final report:\n%s", report)
            try:
                self._continuous_learning.save(self._cl_state_dir)
            except Exception as e:
                logger.warning("Failed to save CL state: %s", e)
        logger.info("ChatService shutdown")

