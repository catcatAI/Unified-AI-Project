import asyncio
from typing import Any
import ray

from apps.backend.src.ai.agents.base_agent import BaseAgent


@ray.remote
class AgentManagerActor:
    """Manages the lifecycle of AI agents, including registration, launching, and monitoring, as a Ray Actor."""

    def __init__(self):
        self._registered_agent_types: dict[str, type[BaseAgent]] = {}
        self._running_agents: dict[str, BaseAgent] = {}
        self.collaboration_manager_id: str | None = None
        print("AgentManagerActor initialized.")

    def register_agent_type(self, agent_type_name: str, agent_class: type[BaseAgent]):
        """Registers a new type of agent that can be launched by the manager."""
        if not issubclass(agent_class, BaseAgent):
            raise ValueError("Registered agent class must inherit from BaseAgent.")
        self._registered_agent_types[agent_type_name] = agent_class
        print(f"Agent type '{agent_type_name}' registered.")

    async def launch_agent(
        self,
        agent_type_name: str,
        agent_id: str | None = None,
        **kwargs: Any,
    ) -> BaseAgent | None:
        """Launches an agent of a registered type.
        Injects self (the AgentManagerActor) into the agent's constructor for collaboration purposes.
        """
        agent_class = self._registered_agent_types.get(agent_type_name)
        if not agent_class:
            print(f"Error: Agent type '{agent_type_name}' not registered.")
            return None

        agent_name = kwargs.pop("name", agent_type_name)

        # Inject the manager instance into all agents for potential collaboration.
        # Note: When injecting an Actor, it should be an ActorHandle, not the Actor itself.
        # For now, we'll pass 'self' (the actor handle) but this might need refinement
        # depending on how agents interact with their manager.
        agent = agent_class(
            agent_manager=self, # This will pass the actor handle to the agent
            agent_id=agent_id,
            name=agent_name,
            **kwargs,
        )

        # If this is the collaboration manager, store its ID for direct access.
        # Using a string check to avoid circular import issues with isinstance.
        if "AgentCollaborationManager" in agent.__class__.__name__:
            if self.collaboration_manager_id:
                print(
                    f"Warning: A Collaboration Manager is already running. Overwriting with new instance {agent.agent_id}.",
                )
            self.collaboration_manager_id = agent.agent_id
            print(f"AgentCollaborationManager registered with ID: {agent.agent_id}")

        self._running_agents[agent.agent_id] = agent
        asyncio.create_task(agent.start())  # Start agent in background
        print(f"Agent '{agent.name}' ({agent.agent_id}) launched.")
        return agent

    async def stop_agent(self, agent_id: str):
        """Stops a running agent by its ID."""
        agent = self._running_agents.get(agent_id)
        if agent:
            await agent.stop()
            # If we are stopping the collaboration manager, clear its ID.
            if agent_id == self.collaboration_manager_id:
                self.collaboration_manager_id = None
                print("AgentCollaborationManager has been stopped and deregistered.")
            del self._running_agents[agent_id]
            print(f"Agent '{agent.name}' ({agent.agent_id}) stopped.")
        else:
            print(f"Warning: Agent with ID '{agent_id}' not found.")

    def get_running_agents(self) -> dict[str, BaseAgent]:
        """Returns a dictionary of all currently running agents."""
        return self._running_agents

    def get_agent_status(self, agent_id: str) -> bool | None:
        """Returns the running status of a specific agent."""
        agent = self._running_agents.get(agent_id)
        return agent.is_running if agent else None

    async def route_message(
        self,
        sending_agent_id: str,
        target_agent_id: str,
        message: dict[str, Any],
    ):
        """Routes a message from a sending agent to a target agent via the collaboration manager."""
        if not self.collaboration_manager_id:
            print(
                "Error: AgentCollaborationManager is not running or not registered. Cannot route message.",
            )
            return

        collaborator = self._running_agents.get(self.collaboration_manager_id)
        if not collaborator:
            print(
                f"Error: AgentCollaborationManager with ID '{self.collaboration_manager_id}' not found in running agents. Cannot route message.",
            )
            return

        # Create a routing task for the collaboration manager
        routing_task = {
            "type": "route_message",
            "data": {
                "sending_agent_id": sending_agent_id,
                "target_agent_id": target_agent_id,
                "message": message,
            },
        }
        await collaborator.submit_task(routing_task)
        print(
            f"Message from {sending_agent_id} to {target_agent_id} submitted to collaboration manager for routing.",
        )

    async def shutdown(self):
        """Shuts down all running agents and clears the manager's state."""
        print("AgentManagerActor shutting down all running agents...")
        # Create a list of agent_ids to avoid RuntimeError due to dictionary size change during iteration
        agents_to_stop = list(self._running_agents.keys())
        for agent_id in agents_to_stop:
            await self.stop_agent(agent_id)
        self._running_agents.clear()
        self.collaboration_manager_id = None
        print("AgentManagerActor shutdown complete.")
