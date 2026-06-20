# =============================================================================
# ANGELA-MATRIX: [L2] [αβγδ] [A] [L3+]
# =============================================================================
# 職責: 聊天與對話服務 (Chat Service)
# 管理 Angela 的對話邏輯、意圖識別與回應合成。
# =============================================================================

import asyncio
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
        self._garden_engine = None
        self._garden_learn_count = 0
        self._ed3n_learning_integration = None
        self._ham_sync_task: Optional[asyncio.Task] = None
        self._ham_sync_interval: int = 3600
        self._cl_state_dir = os.path.join(
            os.path.dirname(__file__), "..", "..", "..", "..", "data", "cl_state"
        )

    @property
    def model_bus(self):
        """Return the ModelBus from the underlying LLM router, if available."""
        if self._llm_service and hasattr(self._llm_service, 'model_bus'):
            return self._llm_service.model_bus
        return None

    async def _ham_sync_loop(self) -> None:
        """Background task: sync ED3N dictionary to HAM memory periodically."""
        while True:
            try:
                await asyncio.sleep(self._ham_sync_interval)
                if self._ed3n_learning_integration:
                    result = self._ed3n_learning_integration.synchronize_knowledge()
                    synced = result.get("synced", 0)
                    errors = result.get("errors", [])
                    if synced > 0:
                        logger.info("HAM sync: %d ED3N entries synchronized", synced)
                    if errors:
                        logger.warning("HAM sync errors: %s", errors[:3])
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.debug("HAM sync loop error: %s", e)

    async def initialize(self) -> None:
        if self._initialized:
            return
        if self._llm_service is None:
            from services.llm.router import get_llm_service
            self._llm_service = await get_llm_service()
        try:
            from ai.ed3n.continuous_learning import ContinuousLearningPipeline
            from ai.ed3n.ed3n_engine import ED3NEngine
            engine = ED3NEngine.get_shared()
            from ai.ed3n.ed3n_trainer import ED3NTrainer
            trainer = ED3NTrainer(engine)
            state_path = os.path.join(self._cl_state_dir, "cl_state.json")
            if await asyncio.to_thread(os.path.exists, state_path):
                self._continuous_learning = ContinuousLearningPipeline.load(
                    self._cl_state_dir, engine=engine, trainer=trainer
                )
                logger.info("Loaded CL state from %s", state_path)
            else:
                self._continuous_learning = ContinuousLearningPipeline(
                    engine=engine,
                    trainer=trainer,
                    growth_interval=15,
                    train_interval=50,
                    min_examples_for_train=30,
                )
            # Wire CLP back into ED3NEngine so _maybe_learn() works for direct engine calls
            engine._continuous_learning = self._continuous_learning
            logger.info("CLP wired into ED3NEngine for _maybe_learn()")
        except Exception as e:
            logger.warning("Continuous learning init skipped: %s", e)
        # Initialize GARDEN engine for continuous learning (Phase 4.5)
        try:
            from ai.garden.garden_engine import GARDENEngine
            self._garden_engine = GARDENEngine(compatibility_mode=True)
            self._garden_engine.load_presets()
            logger.info("GARDEN engine initialized for continuous learning")
        except Exception as e:
            logger.warning("GARDEN engine init skipped: %s", e)
        # Initialize ED3N learning integration for HAM sync (Phase 5.2)
        try:
            from ai.ed3n.learning_integration import ED3NLearningIntegration
            cl_engine = self._continuous_learning.engine if self._continuous_learning else None
            self._ed3n_learning_integration = ED3NLearningIntegration(engine=cl_engine)
            logger.info("ED3N learning integration initialized")
        except Exception as e:
            logger.warning("ED3N learning integration init skipped: %s", e)
        self._initialized = True
        logger.info("ChatService initialized")
        # Start periodic HAM sync background task (Phase 5.2)
        if self._ed3n_learning_integration:
            self._ham_sync_task = asyncio.create_task(self._ham_sync_loop())

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

        # GARDEN continuous learning (Phase 4.5)
        if self._garden_engine:
            try:
                self._garden_engine.learn_from_interaction(user_message, response.text)
                self._garden_learn_count += 1
                # Auto-save every 100 interactions
                if self._garden_learn_count % 100 == 0:
                    garden_state_dir = os.path.join(self._cl_state_dir, "garden_state")
                    await asyncio.to_thread(os.makedirs, garden_state_dir, exist_ok=True)
                    await asyncio.to_thread(self._garden_engine.save, garden_state_dir)
                    logger.info("GARDEN engine saved after %d interactions", self._garden_learn_count)
            except Exception as e:
                logger.debug("GARDEN learning failed: %s", e)

        if getattr(self._llm_service, 'enable_memory_enhancement', False):
            try:
                mm = getattr(self._llm_service, 'memory_manager', None)
                if mm:
                    await mm.store_experience(
                        raw_data={"user": user_message, "assistant": response.text},
                        data_type="conversation",
                    )
            except Exception as e:
                logger.debug("Memory store failed: %s", e)

        return response

    def _post_process_response(self, response, context: dict):
        """Enrich response with biological/emotional state context.

        Stores bio_state snapshot in response metadata for all routes.
        Does NOT modify the response text — enrichment is metadata-only.
        """
        if not response or not response.text:
            return response

        bio_state = context.get("bio_state")
        emotion = context.get("emotion")

        if bio_state and hasattr(response, 'bio_state'):
            response.bio_state = bio_state

        if emotion:
            if hasattr(response, 'emotion'):
                response.emotion = emotion.get("emotion", "neutral")
            if hasattr(response, 'emotion_confidence'):
                response.emotion_confidence = emotion.get("confidence", 0.5)
            if hasattr(response, 'emotion_intensity'):
                response.emotion_intensity = emotion.get("intensity", 0.5)

        if response.metadata is None:
            response.metadata = {}
        response.metadata["bio_enriched"] = bool(bio_state)

        return response

    async def shutdown(self) -> None:
        self._initialized = False
        # Stop HAM sync background task (Phase 5.2)
        if self._ham_sync_task:
            self._ham_sync_task.cancel()
            try:
                await self._ham_sync_task
            except asyncio.CancelledError:
                pass
        # Final HAM sync on shutdown
        if self._ed3n_learning_integration:
            try:
                result = self._ed3n_learning_integration.synchronize_knowledge()
                logger.info("Final HAM sync on shutdown: %d entries", result.get("synced", 0))
            except Exception as e:
                logger.debug("Final HAM sync failed: %s", e)
        if self._continuous_learning:
            report = self._continuous_learning.get_learning_report()
            logger.info("Continuous learning final report:\n%s", report)
            try:
                await asyncio.to_thread(self._continuous_learning.save, self._cl_state_dir)
            except Exception as e:
                logger.warning("Failed to save CL state: %s", e)
        # Save GARDEN engine state
        if self._garden_engine:
            try:
                garden_state_dir = os.path.join(self._cl_state_dir, "garden_state")
                await asyncio.to_thread(os.makedirs, garden_state_dir, exist_ok=True)
                await asyncio.to_thread(self._garden_engine.save, garden_state_dir)
                logger.info("GARDEN engine saved on shutdown")
            except Exception as e:
                logger.warning("Failed to save GARDEN state: %s", e)
        logger.info("ChatService shutdown")

