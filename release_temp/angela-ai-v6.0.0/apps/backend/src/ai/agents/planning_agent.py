import asyncio
from typing import Any  # Added Optional

from apps.backend.src.ai.agents.base_agent import BaseAgent

from ...services.planning_service import (
    planning_manager,
)  # Import the shared singleton instance


class PlanningAgent(BaseAgent):
    """A specialized AI agent for generating and optimizing plans based on goals and constraints."""

    def __init__(
        self,
        agent_id: str = None,
        name: str = "PlanningAgent",
        **kwargs: Any,
    ):
        super().__init__(agent_id=agent_id, name=name, **kwargs)
        print(f"PlanningAgent {self.name} initialized.")

    async def perceive(
        self,
        task: dict[str, Any],
        retrieved_memories: list[dict[str, Any]],
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """Extracts planning parameters from the task."""
        goal = task.get("goal", "achieve a specific objective")
        constraints = task.get("constraints", [])
        context = task.get("context", "")
        print(
            f"PlanningAgent {self.name} perceiving task: 'Plan for {goal}' with {len(constraints)} constraints.",
        )
        return {"goal": goal, "constraints": constraints, "context": context}

    async def decide(
        self,
        perceived_info: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Decides to generate a plan."""
        print(
            f"PlanningAgent {self.name} deciding to generate a plan for: '{perceived_info['goal']}'",
        )
        return {"action": "plan", "parameters": perceived_info}

    async def act(
        self,
        decision: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Generates the plan."""
        if decision.get("action") == "plan":
            parameters = decision["parameters"]
            goal = parameters["goal"]
            constraints = parameters["constraints"]
            context = parameters["context"]
            print(f"PlanningAgent {self.name} acting on goal: '{goal}'")
            await asyncio.sleep(
                1.7,
            )  # Simulate planning process (can be removed if planning_manager is fast)

            # Use the singleton planning_manager to generate the plan
            generated_plan = await planning_manager.generate_plan(
                goal,
                constraints,
                context,
            )
            return generated_plan
        return {}

    async def feedback(
        self,
        original_task: dict[str, Any],
        action_result: Any,
        context: dict[str, Any] | None = None,
    ) -> None:
        """Processes the feedback from the planning action."""
        print(f"PlanningAgent {self.name} received feedback for task.")


if __name__ == "__main__":

    async def main():
        print("--- Running PlanningAgent Test ---")
        agent = PlanningAgent(name="Strategist")
        task1 = {
            "goal": "launch new product",
            "constraints": ["budget_limit", "time_limit"],
            "context": "urgent project",
        }
        task2 = {
            "goal": "learn a new skill",
            "constraints": [],
            "context": "personal development",
        }

        # Start the agent in the background
        agent_task = asyncio.create_task(agent.start())

        await agent.submit_task(task1)
        await agent.submit_task(task2)

        # Give some time for tasks to be processed
        await asyncio.sleep(4)

        await agent.stop()
        await agent_task  # Wait for the agent to fully stop
        print("--- PlanningAgent Test Finished ---")

    asyncio.run(main())
