# =============================================================================
# ANGELA-MATRIX: [L3] [βγδ] [B] [L3]
# =============================================================================

"""
Unified Learning Orchestrator
Single entry point that coordinates all learning subsystems:
- ContinuousLearningPipeline (interaction-level learning)
- ED3NTrainer (weight updates)
- ED3NLearningIntegration (knowledge sync)
- LearningLoop (linguistic evolution)
- LearningOrchestrator (evaluate-adapt cycle)
- ExperienceReplayBuffer (replay-based training)
"""

import logging
import threading
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class UnifiedLearningOrchestrator:
    """
    Coordinates all learning subsystems into a single unified loop.

    Flow:
    1. User interaction arrives
    2. ContinuousLearningPipeline processes it (dictionary growth, training buffer)
    3. LearningLoop extracts novel phrases from LLM response
    4. ED3NLearningIntegration syncs knowledge to HAM
    5. LearningOrchestrator evaluates and adapts strategy
    6. ExperienceReplayBuffer stores for replay-based training
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._initialized = False

        # Subsystem references (lazy-init)
        self._continuous_learning = None
        self._learning_loop = None
        self._learning_integration = None
        self._learning_orchestrator = None
        self._replay_buffer = None

        # Stats
        self._interaction_count = 0
        self._learning_cycles = 0

    def initialize(
        self,
        ed3n_engine=None,
        garden_engine=None,
        continuous_learning=None,
        learning_loop=None,
        learning_integration=None,
        learning_orchestrator=None,
        replay_buffer=None,
    ) -> None:
        """Initialize with available subsystems. Missing subsystems are skipped."""
        with self._lock:
            self._continuous_learning = continuous_learning
            self._learning_loop = learning_loop
            self._learning_integration = learning_integration
            self._learning_orchestrator = learning_orchestrator
            self._replay_buffer = replay_buffer

            # Bind engines to learning loop
            if self._learning_loop and ed3n_engine:
                self._learning_loop.bind_ed3n_engine(ed3n_engine)
            if self._learning_loop and garden_engine:
                self._learning_loop.bind_garden_engine(garden_engine)

            # Connect learning integration
            if self._learning_integration and ed3n_engine:
                self._learning_integration.connect_to_replay_buffer(self._replay_buffer)

            self._initialized = True
            logger.info("UnifiedLearningOrchestrator initialized")

    async def process_interaction(
        self,
        user_text: str,
        response_text: str,
        context: Optional[Dict[str, Any]] = None,
        positive: bool = True,
    ) -> Dict[str, Any]:
        """
        Process a user-assistant interaction through all learning subsystems.

        Returns a summary of what was learned.
        """
        with self._lock:
            self._interaction_count += 1

        results: Dict[str, Any] = {
            "interaction_id": self._interaction_count,
            "subsystems": {},
        }

        # 1. ContinuousLearningPipeline — dictionary growth + training buffer
        if self._continuous_learning:
            try:
                await self._continuous_learning.process_interaction_async(
                    user_text, response_text, context or {}
                )
                results["subsystems"]["continuous_learning"] = "processed"
            except Exception as e:
                logger.debug(f"ContinuousLearning failed: {e}")
                results["subsystems"]["continuous_learning"] = f"error: {e}"

        # 2. LearningLoop — extract novel phrases from LLM response
        if self._learning_loop:
            try:
                novel_count = self._learning_loop.process_llm_response(
                    response_text, {"user_message": user_text}
                )
                results["subsystems"]["learning_loop"] = f"{novel_count} novel items"
            except Exception as e:
                logger.debug(f"LearningLoop failed: {e}")
                results["subsystems"]["learning_loop"] = f"error: {e}"

        # 3. LearningLoop — process user feedback
        if self._learning_loop:
            try:
                self._learning_loop.process_user_feedback(
                    user_text, response_text, positive
                )
                results["subsystems"]["feedback"] = "processed"
            except Exception as e:
                logger.debug(f"Feedback processing failed: {e}")
                results["subsystems"]["feedback"] = f"error: {e}"

        # 4. ED3NLearningIntegration — sync knowledge to HAM (periodic)
        if self._learning_integration and self._interaction_count % 50 == 0:
            try:
                self._learning_integration.synchronize_knowledge()
                results["subsystems"]["ham_sync"] = "synchronized"
            except Exception as e:
                logger.debug(f"HAM sync failed: {e}")
                results["subsystems"]["ham_sync"] = f"error: {e}"

        # 5. ExperienceReplayBuffer — store experience
        if self._replay_buffer:
            try:
                self._replay_buffer.add_experience(
                    state=user_text,
                    action="respond",
                    reward=1.0 if positive else -1.0,
                    next_state=response_text,
                    done=False,
                )
                results["subsystems"]["replay_buffer"] = "stored"
            except Exception as e:
                logger.debug(f"ReplayBuffer failed: {e}")
                results["subsystems"]["replay_buffer"] = f"error: {e}"

        # 6. LearningOrchestrator — evaluate and adapt (periodic)
        if self._learning_orchestrator and self._interaction_count % 20 == 0:
            try:
                task = {"task_id": f"interaction_{self._interaction_count}", "type": "chat"}
                execution_result = {"success": positive, "output": response_text}
                cycle_result = self._learning_orchestrator.process_learning_cycle(
                    task, execution_result
                )
                self._learning_cycles += 1
                results["subsystems"]["orchestrator"] = cycle_result
            except Exception as e:
                logger.debug(f"Orchestrator failed: {e}")
                results["subsystems"]["orchestrator"] = f"error: {e}"

        return results

    def get_stats(self) -> Dict[str, Any]:
        """Return learning statistics."""
        stats: Dict[str, Any] = {
            "initialized": self._initialized,
            "interaction_count": self._interaction_count,
            "learning_cycles": self._learning_cycles,
            "subsystems": {},
        }

        if self._continuous_learning:
            try:
                stats["subsystems"]["continuous_learning"] = self._continuous_learning.get_stats()
            except Exception:
                stats["subsystems"]["continuous_learning"] = "unavailable"

        if self._learning_orchestrator:
            try:
                stats["subsystems"]["orchestrator"] = self._learning_orchestrator.get_learning_status()
            except Exception:
                stats["subsystems"]["orchestrator"] = "unavailable"

        return stats
