import asyncio
from typing import Any
import ray

from apps.backend.src.ai.agents.base_agent import BaseAgent
from apps.backend.src.ai.agent_manager_actor import AgentManagerActor # Import the Actor

class AgentManager:
    """
    Client for the AgentManagerActor.
    Delegates calls to the remote AgentManagerActor instance.
    """

    def __init__(self):
        """Initializes the AgentManager client and creates the remote actor."""
        # Initialize Ray if not already done (for safety)
        if not ray.is_initialized():
            ray.init(ignore_reinit_error=True)
            
        self.actor = AgentManagerActor.remote() # Create the remote actor
        print("AgentManager client initialized, AgentManagerActor created.")

    def register_agent_type(self, agent_type_name: str, agent_class: type[BaseAgent]):
        return ray.get(self.actor.register_agent_type.remote(agent_type_name, agent_class))

    async def launch_agent(
        self,
        agent_type_name: str,
        agent_id: str | None = None,
        **kwargs: Any,
    ) -> BaseAgent | None:
        return await self.actor.launch_agent.remote(agent_type_name, agent_id, **kwargs)

    async def stop_agent(self, agent_id: str):
        return await self.actor.stop_agent.remote(agent_id)

    def get_running_agents(self) -> dict[str, BaseAgent]:
        return ray.get(self.actor.get_running_agents.remote())

    def get_agent_status(self, agent_id: str) -> bool | None:
        return ray.get(self.actor.get_agent_status.remote(agent_id))

    async def route_message(
        self,
        sending_agent_id: str,
        target_agent_id: str,
        message: dict[str, Any],
    ):
        return await self.actor.route_message.remote(sending_agent_id, target_agent_id, message)

    async def shutdown(self):
        return await self.actor.shutdown.remote()
