import asyncio
import logging
import uuid
from typing import Any

from apps.backend.src.ai.agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class DynamicAgentRegistry(BaseAgent):
    """A specialized AI agent for dynamically registering, discovering, and managing other agents."""

    def __init__(
        self,
        agent_id: str = None,
        name: str = "DynamicAgentRegistry",
        **kwargs: Any,
    ):
        super().__init__(agent_id=agent_id, name=name, **kwargs)
        print(f"DynamicAgentRegistry {self.name} initialized.")
        self.registered_agents: dict[
            str,
            dict[str, Any],
        ] = {}  # Stores metadata of registered agents

    async def perceive(
        self,
        task: dict[str, Any],
        retrieved_memories: list[dict[str, Any]],
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """Perceives the registry task."""
        logger.debug(
            f"DynamicAgentRegistry {self.name} perceiving task: {task.get('operation')}",
        )
        return task

    async def decide(self, perceived_info: dict[str, Any]) -> dict[str, Any]:
        """Decides which registry operation to perform."""
        operation = perceived_info.get("operation", "discover")
        payload = perceived_info.get("payload", {})
        logger.debug(
            f"DynamicAgentRegistry {self.name} deciding to perform operation: '{operation}'",
        )
        return {"action": operation, "payload": payload}

    async def act(self, decision: dict[str, Any]) -> dict[str, Any]:
        """Acts on the registry decision."""
        operation = decision.get("action")
        payload = decision.get("payload")
        logger.info(
            f"DynamicAgentRegistry {self.name} acting on operation: '{operation}' with payload: {payload}",
        )
        await asyncio.sleep(0.3)  # Simulate registry operation
        return self._simulate_registry_operation(operation, payload)

    async def feedback(self, original_task: dict[str, Any], action_result: Any) -> None:
        """Processes feedback from the registry action."""
        logger.debug(f"DynamicAgentRegistry {self.name} received feedback for task.")

    def _simulate_registry_operation(
        self,
        operation: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Internal method to simulate dynamic agent registry operations."""
        if operation == "register":
            agent_id = payload.get("agent_id", str(uuid.uuid4()))
            agent_name = payload.get("agent_name", "Unnamed Agent")
            capabilities = payload.get("capabilities", [])
            self.registered_agents[agent_id] = {
                "id": agent_id,
                "name": agent_name,
                "capabilities": capabilities,
                "status": "active",
                "last_heartbeat": asyncio.get_event_loop().time(),  # Using event loop time for simulation
            }
            return {
                "status": "success",
                "message": f"Agent '{agent_name}' registered with ID '{agent_id}'.",
            }
        if operation == "discover":
            capability_filter = payload.get("capability_filter")
            discovered_agents = []
            for agent_id, agent_info in self.registered_agents.items():
                if not capability_filter or capability_filter in agent_info.get(
                    "capabilities",
                    [],
                ):
                    discovered_agents.append(agent_info)
            return {"status": "success", "discovered_agents": discovered_agents}
        if operation == "deregister":
            agent_id = payload.get("agent_id")
            if agent_id in self.registered_agents:
                del self.registered_agents[agent_id]
                return {
                    "status": "success",
                    "message": f"Agent '{agent_id}' deregistered.",
                }
            return {"status": "failed", "message": f"Agent '{agent_id}' not found."}
        return {"message": f"Unknown registry operation: {operation}"}


if __name__ == "__main__":

    async def main():
        print("--- Running DynamicAgentRegistry Test ---")
        registry = DynamicAgentRegistry(name="AgentHub")

        # Start the registry in the background
        registry_task = asyncio.create_task(registry.start())

        # Register some agents
        register_task1 = {
            "operation": "register",
            "payload": {
                "agent_name": "WriterBot",
                "capabilities": ["creative_writing", "nlp"],
            },
        }
        register_task2 = {
            "operation": "register",
            "payload": {
                "agent_name": "ImageBot",
                "capabilities": ["image_generation", "vision"],
            },
        }

        await registry.submit_task(register_task1)
        await registry.submit_task(register_task2)

        # Give some time for registration to process
        await asyncio.sleep(1)

        # Discover agents
        discover_all_task = {"operation": "discover"}
        discover_image_task = {
            "operation": "discover",
            "payload": {"capability_filter": "image_generation"},
        }

        await registry.submit_task(discover_all_task)
        await registry.submit_task(discover_image_task)

        # Give some time for discovery to process
        await asyncio.sleep(1)

        # Deregister an agent
        # First, get its ID from the registry (simulated)
        writer_agent_id = None
        for agent_id, agent_info in registry.registered_agents.items():
            if agent_info["name"] == "WriterBot":
                writer_agent_id = agent_id
                break

        if writer_agent_id:
            deregister_task = {
                "operation": "deregister",
                "payload": {"agent_id": writer_agent_id},
            }
            await registry.submit_task(deregister_task)
            await asyncio.sleep(0.5)  # Give time for deregistration
            print(
                f"WriterBot deregistered. Current registered agents: {registry.registered_agents}",
            )
        else:
            print("WriterBot ID not found for deregistration.")

        await asyncio.sleep(1)  # Final sleep before stopping

        await registry.stop()
        await registry_task  # Wait for the registry to fully stop
        print("--- DynamicAgentRegistry Test Finished ---")

    asyncio.run(main())
