import asyncio
import random
from typing import Any

from apps.backend.src.ai.agents.base_agent import BaseAgent


class CreativeWritingAgent(BaseAgent):
    """A specialized AI agent for creative writing and content generation."""

    def __init__(
        self,
        agent_id: str = None,
        name: str = "CreativeWritingAgent",
        **kwargs: Any,
    ):
        super().__init__(agent_id=agent_id, name=name, **kwargs)
        print(f"CreativeWritingAgent {self.name} initialized.")

    async def perceive(
        self,
        task: dict[str, Any],
        retrieved_memories: List[dict[str, Any]],
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """Extracts creative writing parameters from the task."""
        prompt = task.get("prompt", "Write something creative.")
        style = task.get("style", "neutral")
        length = task.get("length", "short")
        print(
            f"CreativeWritingAgent {self.name} perceiving task with prompt: '{prompt}' (style: {style}, length: {length})",
        )
        return {"prompt": prompt, "style": style, "length": length}

    async def decide(self, perceived_info: dict[str, Any]) -> dict[str, Any]:
        """Decides to generate creative content."""
        print(
            f"CreativeWritingAgent {self.name} deciding to write about: '{perceived_info['prompt']}'",
        )
        return {"action": "generate", "parameters": perceived_info}

    async def act(self, decision: dict[str, Any]) -> str:
        """Generates the creative content."""
        if decision.get("action") == "generate":
            parameters = decision["parameters"]
            prompt = parameters["prompt"]
            style = parameters["style"]
            length = parameters["length"]
            print(f"CreativeWritingAgent {self.name} acting on prompt: '{prompt}'")
            await asyncio.sleep(0.5)  # Simulate creative process

            # Simulate content generation
            generated_content = self._generate_creative_content(prompt, style, length)
            return generated_content
        return ""

    async def feedback(self, original_task: dict[str, Any], action_result: Any) -> None:
        """Processes the feedback from the content generation action."""
        print(f"CreativeWritingAgent {self.name} received feedback for task.")
        # In a real scenario, this could be used to learn from the feedback on the generated content

    def _generate_creative_content(self, prompt: str, style: str, length: str) -> str:
        """Internal method to simulate creative content generation."""
        templates = {
            "short": [
                f"A {style} story about {prompt}.",
                f"A {style} poem inspired by {prompt}.",
                f"A brief {style} description of {prompt}.",
            ],
            "medium": [
                f"A compelling {style} narrative exploring {prompt}.",
                f"An insightful {style} essay on the themes of {prompt}.",
                f"A detailed {style} report about {prompt}.",
            ],
        }

        chosen_template = random.choice(templates.get(length, templates["short"]))
        return chosen_template


if __name__ == "__main__":

    async def main():
        print("--- Running CreativeWritingAgent Test ---")
        agent = CreativeWritingAgent(name="Storyteller")
        task1 = {"prompt": "a lonely robot", "style": "melancholic", "length": "short"}
        task2 = {
            "prompt": "the future of AI",
            "style": "optimistic",
            "length": "medium",
        }

        # Start the agent in the background
        agent_task = asyncio.create_task(agent.start())

        await agent.submit_task(task1)
        await agent.submit_task(task2)

        # Give some time for tasks to be processed
        await asyncio.sleep(2)

        await agent.stop()
        await agent_task  # Wait for the agent to fully stop
        print("--- CreativeWritingAgent Test Finished ---")

    asyncio.run(main())
