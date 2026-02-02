import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional
import ray

from .bt_engine import Selector, Sequence, Action, Condition, NodeStatus
from .governance.vdaf import VDAFManager
from .governance.m6_security import CheckVDAFNode, ExecuteM6LockNode, ConsequenceSimulationNode
from .llm.hybrid_brain import HybridBrain
from apps.backend.src.ai.meta.adaptive_learning_controller import AdaptiveLearningController
from apps.backend.src.ai.evaluation.task_evaluator import TaskExecutionEvaluator
from apps.backend.src.core.orchestrator_actor import CognitiveOrchestratorActor # Import the Actor

logger = logging.getLogger(__name__)

class CognitiveOrchestrator:
    """
    Client for the CognitiveOrchestratorActor.
    Delegates calls to the remote CognitiveOrchestratorActor instance.
    """
    
    def __init__(self, experience_buffer=None, ham_memory_manager=None, learning_controller: Optional[AdaptiveLearningController] = None):
        # Initialize Ray if not already done (for safety, though main.py/SystemManager should do it)
        if not ray.is_initialized():
            ray.init(ignore_reinit_error=True)

        self.actor = CognitiveOrchestratorActor.remote(experience_buffer, ham_memory_manager, learning_controller)
        logger.info("CognitiveOrchestrator client initialized, CognitiveOrchestratorActor created.")

    async def _perform_self_reflection(self) -> Dict[str, Any]:
        return await self.actor._perform_self_reflection.remote()

    async def process_user_input(self, user_input: str) -> Dict[str, Any]:
        return await self.actor.process_user_input.remote(user_input)

    # Note: _set_response, _build_behavior_tree are internal methods of the Actor and not exposed via client.
    # If direct access is needed, define specific remote methods in the Actor.
