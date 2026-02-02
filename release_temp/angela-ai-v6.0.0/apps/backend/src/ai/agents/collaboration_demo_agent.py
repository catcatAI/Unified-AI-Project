import asyncio
from typing import Any

from apps.backend.src.ai.agents.base_agent import BaseAgent


class ConcreteSimulatedAgent(BaseAgent):
    """A simple concrete agent for simulation."""

    async def perceive(self, task: dict[str, Any]) -> Any:
        await asyncio.sleep(0.01)
        return {"perceived_data": f"Data for {task.get('description', 'N/A')}"}

    async def decide(self, perceived_info: Any) -> dict[str, Any]:
        await asyncio.sleep(0.01)
        return {
            "action_type": "process",
            "target": perceived_info.get("perceived_data"),
        }

    async def act(self, decision: dict[str, Any]) -> Any:
        await asyncio.sleep(0.05)
        return {"action_status": "success", "processed_item": decision.get("target")}

    async def feedback(self, original_task: dict[str, Any], action_result: Any) -> None:
        await asyncio.sleep(0.01)


class CollaborationDemoAgent(BaseAgent):
    """A specialized AI agent designed to demonstrate basic collaboration capabilities.
    This agent will simulate receiving a task and delegating parts of it to other (simulated) agents.
    """

    def __init__(
        self,
        agent_id: str = None,
        name: str = "CollaborationDemoAgent",
        **kwargs: Any,
    ):
        super().__init__(agent_id=agent_id, name=name, **kwargs)
        print(f"CollaborationDemoAgent {self.name} initialized.")
        # Simulate other agents this demo agent might collaborate with
        self.simulated_collaborators = {
            "writer_agent": ConcreteSimulatedAgent(name="SimulatedWriter"),
            "image_agent": ConcreteSimulatedAgent(name="SimulatedImageGenerator"),
        }

    async def perceive(
        self,
        task: dict[str, Any],
        retrieved_memories: List[dict[str, Any]],
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """Perceives the collaboration task."""
        main_goal = task.get("main_goal", "Create a collaborative output.")
        subtask_instructions = task.get("subtask_instructions", {})
        print(f"CollaborationDemoAgent {self.name} perceiving main goal: '{main_goal}'")
        return {"main_goal": main_goal, "subtask_instructions": subtask_instructions}

    async def decide(self, perceived_info: dict[str, Any]) -> dict[str, Any]:
        """Decides to delegate subtasks."""
        print(
            f"CollaborationDemoAgent {self.name} deciding to delegate subtasks for: '{perceived_info['main_goal']}'",
        )
        return {"action": "delegate", "parameters": perceived_info}

    async def act(self, decision: dict[str, Any]) -> dict[str, Any]:
        """Acts on the delegation decision."""
        if decision.get("action") == "delegate":
            parameters = decision["parameters"]
            main_goal = parameters["main_goal"]
            subtask_instructions = parameters["subtask_instructions"]
            print(
                f"CollaborationDemoAgent {self.name} acting on main goal: '{main_goal}'",
            )

            results = {}

            # Simulate delegating to a writer agent
            if "write_story" in subtask_instructions:
                writer_task = {
                    "prompt": subtask_instructions["write_story"],
                    "style": "neutral",
                    "length": "short",
                }
                print(
                    f"  -> Delegating writing task to SimulatedWriter: {writer_task['prompt']}",
                )
                # In a real scenario, this would be an actual call to another agent
                await asyncio.sleep(1.0)
                results["story_output"] = (
                    f"Simulated story: '{subtask_instructions['write_story']}'"
                )

            # Simulate delegating to an image generation agent
            if "generate_image" in subtask_instructions:
                image_task = {
                    "prompt": subtask_instructions["generate_image"],
                    "style": "photorealistic",
                    "size": "512x512",
                }
                print(
                    f"  -> Delegating image generation task to SimulatedImageGenerator: {image_task['prompt']}",
                )
                # In a real scenario, this would be an actual call to another agent
                await asyncio.sleep(1.5)
                results["image_output"] = (
                    f"Simulated image URL for: '{subtask_instructions['generate_image']}'"
                )

            return {"main_goal": main_goal, "collaboration_results": results}
        return {}

    async def feedback(self, original_task: dict[str, Any], action_result: Any) -> None:
        """Processes feedback from the collaboration action."""
        print(f"CollaborationDemoAgent {self.name} received feedback for task.")


if __name__ == "__main__":

    async def main():
        print("--- Running CollaborationDemoAgent Test ---")
        demo_agent = CollaborationDemoAgent(name="Collaborator")

        # Start the demo agent in the background
        demo_agent_task = asyncio.create_task(demo_agent.start())

        # Start simulated collaborators (optional, for more realistic output)
        for _, agent in demo_agent.simulated_collaborators.items():
            asyncio.create_task(agent.start())

        collaboration_task = {
            "main_goal": "Create a short illustrated story about a space cat.",
            "subtask_instructions": {
                "write_story": "A brave space cat explores a new galaxy.",
                "generate_image": "A cute cat in a spacesuit floating in space.",
            },
        }

        await demo_agent.submit_task(collaboration_task)

        # Give some time for tasks to be processed
        await asyncio.sleep(4)

        await demo_agent.stop()
        for _, agent in demo_agent.simulated_collaborators.items():
            await agent.stop()
        await demo_agent_task  # Wait for the demo agent to fully stop
        print("--- CollaborationDemoAgent Test Finished ---")

    asyncio.run(main())
