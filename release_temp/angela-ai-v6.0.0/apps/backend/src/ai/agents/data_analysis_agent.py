import asyncio
from typing import Any  # Added Optional

from apps.backend.src.ai.agents.base_agent import BaseAgent

from ...services.data_analysis_service import (
    data_analysis_manager,
)  # Import the shared singleton instance


class DataAnalysisAgent(BaseAgent):
    """A specialized AI agent for performing data analysis tasks."""

    def __init__(
        self,
        agent_id: str = None,
        name: str = "DataAnalysisAgent",
        **kwargs: Any,
    ):
        super().__init__(agent_id=agent_id, name=name, **kwargs)
        print(f"DataAnalysisAgent {self.name} initialized.")

    async def perceive(
        self,
        task: dict[str, Any],
        retrieved_memories: list[dict[str, Any]],
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """Extracts data analysis parameters from the task."""
        data = task.get("data", [])
        analysis_type = task.get("analysis_type", "summary")
        parameters = task.get("parameters", {})
        print(
            f"DataAnalysisAgent {self.name} perceiving task: '{analysis_type}' on {len(data)} data points.",
        )
        return {"data": data, "analysis_type": analysis_type, "parameters": parameters}

    async def decide(
        self,
        perceived_info: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Decides to perform data analysis."""
        print(
            f"DataAnalysisAgent {self.name} deciding to perform {perceived_info['analysis_type']} analysis.",
        )
        return {"action": "analyze", "parameters": perceived_info}

    async def act(
        self,
        decision: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Performs the data analysis."""
        if decision.get("action") == "analyze":
            parameters = decision["parameters"]
            data = parameters["data"]
            analysis_type = parameters["analysis_type"]
            parameters = parameters["parameters"]
            print(
                f"DataAnalysisAgent {self.name} acting on analysis type: '{analysis_type}'",
            )
            await asyncio.sleep(
                1.5,
            )  # Simulate data analysis process (can be removed if data_analysis_manager is fast)

            # Use the singleton data_analysis_manager to perform the analysis
            analysis_result = await data_analysis_manager.analyze_data(
                data,
                analysis_type,
                parameters,
            )
            return analysis_result
        return {}

    async def feedback(
        self,
        original_task: dict[str, Any],
        action_result: Any,
        context: dict[str, Any] | None = None,
    ) -> None:
        """Processes the feedback from the data analysis action."""
        print(f"DataAnalysisAgent {self.name} received feedback for task.")


if __name__ == "__main__":

    async def main():
        print("--- Running DataAnalysisAgent Test ---")
        agent = DataAnalysisAgent(name="DataScientist")
        sample_data = [
            {"id": 1, "value_a": 10, "value_b": 20},
            {"id": 2, "value_a": 15, "value_b": 25},
            {"id": 3, "value_a": 12, "value_b": 22},
        ]
        task1 = {"data": sample_data, "analysis_type": "summary"}
        task2 = {
            "data": sample_data,
            "analysis_type": "correlation",
            "parameters": {"fields": ["value_a", "value_b"]},
        }

        # Start the agent in the background
        agent_task = asyncio.create_task(agent.start())

        await agent.submit_task(task1)
        await agent.submit_task(task2)

        # Give some time for tasks to be processed
        await asyncio.sleep(4)

        await agent.stop()
        await agent_task  # Wait for the agent to fully stop
        print("--- DataAnalysisAgent Test Finished ---")

    asyncio.run(main())
