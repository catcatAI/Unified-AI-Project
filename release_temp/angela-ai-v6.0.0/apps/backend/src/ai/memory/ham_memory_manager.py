import datetime
from typing import Any
import ray

from .vector_store import VectorStore
from apps.backend.src.ai.memory.ham_memory_manager_actor import HAMMemoryManagerActor # Import the Actor

class HAMMemoryManager:
    """
    Client for the HAMMemoryManagerActor.
    Delegates calls to the remote HAMMemoryManagerActor instance.
    """

    def __init__(self):
        """Initializes the HAMMemoryManager client and creates the remote actor."""
        # Initialize Ray if not already done (for safety, though main.py/SystemManager should do it)
        if not ray.is_initialized():
            ray.init(ignore_reinit_error=True)
            
        self.actor = HAMMemoryManagerActor.remote() # Create the remote actor
        print("HAMMemoryManager client initialized, HAMMemoryManagerActor created.")

    async def store_experience(self, experience: dict[str, Any]) -> str:
        return await self.actor.store_experience.remote(experience)

    async def retrieve_relevant_memories(
        self,
        query: str,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        return await self.actor.retrieve_relevant_memories.remote(query, limit)

    def get_memory_by_id(self, memory_id: str) -> dict[str, Any] | None:
        # Note: get_memory_by_id is not async, will need to be careful with ray.get() here.
        # For now, calling it as remote, but in a real scenario, consider if this should be remote
        # or if an async version is needed on the actor.
        return ray.get(self.actor.get_memory_by_id.remote(memory_id))

    def get_all_memories(self) -> list[dict[str, Any]]:
        # Same note as get_memory_by_id regarding sync/async.
        return ray.get(self.actor.get_all_memories.remote())
