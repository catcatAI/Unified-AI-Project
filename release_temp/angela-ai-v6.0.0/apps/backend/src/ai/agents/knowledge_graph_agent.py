import asyncio
from typing import Any

from apps.backend.src.ai.agents.base_agent import BaseAgent


class KnowledgeGraphAgent(BaseAgent):
    """A specialized AI agent for interacting with and managing a knowledge graph."""

    def __init__(
        self,
        agent_id: str = None,
        name: str = "KnowledgeGraphAgent",
        **kwargs: Any,
    ):
        super().__init__(agent_id=agent_id, name=name, **kwargs)
        print(f"KnowledgeGraphAgent {self.name} initialized.")

    async def perceive(
        self,
        task: dict[str, Any],
        retrieved_memories: list[dict[str, Any]],
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """Extracts knowledge graph operation parameters from the task."""
        operation = task.get("operation", "query")
        data = task.get("data", {})
        parameters = task.get("parameters", {})
        print(
            f"KnowledgeGraphAgent {self.name} perceiving task: '{operation}' with data: {data}",
        )
        return {"operation": operation, "data": data, "parameters": parameters}

    async def decide(self, perceived_info: dict[str, Any]) -> dict[str, Any]:
        """Decides to perform a knowledge graph operation."""
        print(
            f"KnowledgeGraphAgent {self.name} deciding to perform operation: {perceived_info['operation']}",
        )
        return {"action": "operate", "parameters": perceived_info}

    async def act(self, decision: dict[str, Any]) -> dict[str, Any]:
        """Performs the knowledge graph operation."""
        if decision.get("action") == "operate":
            parameters = decision["parameters"]
            operation = parameters["operation"]
            data = parameters["data"]
            parameters = parameters["parameters"]
            print(f"KnowledgeGraphAgent {self.name} acting on operation: '{operation}'")
            await asyncio.sleep(1.0)  # Simulate knowledge graph operation

            # Simulate knowledge graph operation result
            operation_result = self._simulate_kg_operation(operation, data, parameters)
            return operation_result
        return {}

    async def feedback(self, original_task: dict[str, Any], action_result: Any) -> None:
        """Processes the feedback from the knowledge graph operation."""
        print(f"KnowledgeGraphAgent {self.name} received feedback for task.")

    def _simulate_kg_operation(
        self,
        operation: str,
        data: Any,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:
        """Internal method to simulate knowledge graph operations and return placeholder results."""
        if operation == "query":
            query_string = data.get("query_string", "What is AI?")
            if "AI" in query_string:
                return {
                    "query_result": [
                        {"entity": "AI", "relation": "is_a", "value": "field_of_study"},
                        {
                            "entity": "AI",
                            "relation": "goal",
                            "value": "simulate_intelligence",
                        },
                    ],
                    "source": "Simulated KG",
                }
            return {"query_result": [], "message": "No results found for query."}
        if operation == "add":
            return {"status": "success", "message": f"Added data to KG: {data}"}
        if operation == "update":
            return {"status": "success", "message": f"Updated data in KG: {data}"}
        return {"message": f"Unknown KG operation: {operation}"}


if __name__ == "__main__":

    async def main():
        print("--- Running KnowledgeGraphAgent Test ---")
        agent = KnowledgeGraphAgent(name="KG_Master")
        task1 = {"operation": "query", "data": {"query_string": "What is AI?"}}
        task2 = {
            "operation": "add",
            "data": {"entity": "Gemini", "relation": "is_a", "value": "AI_model"},
        }

        # Start the agent in the background
        agent_task = asyncio.create_task(agent.start())

        await agent.submit_task(task1)
        await agent.submit_task(task2)

        # Give some time for tasks to be processed
        await asyncio.sleep(3)

        await agent.stop()
        await agent_task  # Wait for the agent to fully stop
        print("--- KnowledgeGraphAgent Test Finished ---")

    asyncio.run(main())
