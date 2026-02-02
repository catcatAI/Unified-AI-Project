import ray
from apps.backend.src.core.orchestrator import CognitiveOrchestrator # Original class
import logging

logger = logging.getLogger(__name__)

@ray.remote
class CognitiveOrchestratorActor:
    def __init__(self, **kwargs):
        logger.info(f"CognitiveOrchestratorActor initialized with kwargs: {kwargs}")
        self.orchestrator = CognitiveOrchestrator(**kwargs)

    async def initialize(self, system_manager_client, ham_memory_manager_client, agent_manager_client,
                         desktop_pet_client, economy_manager_client):
        logger.info("CognitiveOrchestratorActor: Initializing internal CognitiveOrchestrator.")
        await self.orchestrator.initialize(
            system_manager_client=system_manager_client,
            ham_memory_manager_client=ham_memory_manager_client,
            agent_manager_client=agent_manager_client,
            desktop_pet_client=desktop_pet_client,
            economy_manager_client=economy_manager_client
        )
        logger.info("CognitiveOrchestratorActor: Internal CognitiveOrchestrator initialized.")

    async def process_user_input(self, user_input: str):
        # Delegate the call to the actual CognitiveOrchestrator instance
        return await self.orchestrator.process_user_input(user_input)

    async def _perform_self_reflection(self):
        # Delegate the call to the actual CognitiveOrchestrator instance
        return await self.orchestrator._perform_self_reflection()

    async def shutdown(self):
        logger.info("CognitiveOrchestratorActor: Shutting down internal CognitiveOrchestrator.")
        await self.orchestrator.shutdown()
        logger.info("CognitiveOrchestratorActor: Internal CognitiveOrchestrator shut down.")
