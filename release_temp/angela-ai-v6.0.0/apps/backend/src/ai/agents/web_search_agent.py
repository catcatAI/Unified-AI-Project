import asyncio
from typing import Any

from apps.backend.src.ai.agents.base_agent import BaseAgent

from ...services.search_service import (
    search_manager,
)  # Import the shared singleton instance


class WebSearchAgent(BaseAgent):
    """A specialized AI agent for performing web searches and retrieving information."""

    def __init__(
        self,
        agent_id: str = None,
        name: str = "WebSearchAgent",
        **kwargs: Any,
    ):
        super().__init__(agent_id=agent_id, name=name, **kwargs)
        print(f"WebSearchAgent {self.name} initialized.")

    async def perceive(
        self,
        task: dict[str, Any],
        retrieved_memories: list[dict[str, Any]],
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """Extracts search parameters from the task."""
        query = task.get("query", "latest AI news")
        num_results = task.get("num_results", 5)
        print(
            f"WebSearchAgent {self.name} perceiving task with query: '{query}' (num_results: {num_results})",
        )
        return {"query": query, "num_results": num_results}

    async def decide(
        self,
        perceived_info: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Decides to perform the web search."""
        print(
            f"WebSearchAgent {self.name} deciding to search for: '{perceived_info['query']}'",
        )
        return {"action": "search", "parameters": perceived_info}

    async def act(
        self,
        decision: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Performs the web search."""
        if decision.get("action") == "search":
            parameters = decision["parameters"]
            query = parameters["query"]
            num_results = parameters["num_results"]
            print(f"WebSearchAgent {self.name} acting on search for: '{query}'")
            await asyncio.sleep(
                0.7,
            )  # Simulate web search process (can be removed if search_manager is fast)

            # Use the singleton search_manager to perform the search
            search_results = await search_manager.search(query, num_results)
            return {"query": query, "results": search_results}
        return {}

    async def feedback(
        self,
        original_task: dict[str, Any],
        action_result: Any,
        context: dict[str, Any] | None = None,
    ) -> None:
        """Processes the feedback from the search action."""
        print(f"WebSearchAgent {self.name} received feedback for task.")
        # In a real scenario, this could be used to learn from the search results


if __name__ == "__main__":

    async def main():
        print("--- Running WebSearchAgent Test ---")
        agent = WebSearchAgent(name="SearchBot")
        task1 = {"query": "current AI trends", "num_results": 3}
        task2 = {"query": "history of neural networks", "num_results": 2}

        # Start the agent in the background
        agent_task = asyncio.create_task(agent.start())

        await agent.submit_task(task1)
        await agent.submit_task(task2)

        # Give some time for tasks to be processed
        await asyncio.sleep(2)

        await agent.stop()
        await agent_task  # Wait for the agent to fully stop
        print("--- WebSearchAgent Test Finished ---")

    asyncio.run(main())
