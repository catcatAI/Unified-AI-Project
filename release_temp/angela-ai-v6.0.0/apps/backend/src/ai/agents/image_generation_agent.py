import asyncio
from typing import Any  # Added Optional

from apps.backend.src.ai.agents.base_agent import BaseAgent

from ...services.image_service import (
    image_manager,
)  # Import the shared singleton instance


class ImageGenerationAgent(BaseAgent):
    """A specialized AI agent for generating images based on textual prompts."""

    def __init__(
        self,
        agent_id: str = None,
        name: str = "ImageGenerationAgent",
        **kwargs: Any,
    ):
        super().__init__(agent_id=agent_id, name=name, **kwargs)
        print(f"ImageGenerationAgent {self.name} initialized.")

    async def perceive(
        self,
        task: dict[str, Any],
        retrieved_memories: list[dict[str, Any]],
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """Extracts image generation parameters from the task."""
        prompt = task.get("prompt", "A beautiful landscape.")
        style = task.get("style", "photorealistic")
        size = task.get("size", "1024x1024")
        print(
            f"ImageGenerationAgent {self.name} perceiving task with prompt: '{prompt}' (style: {style}, size: {size})",
        )
        return {"prompt": prompt, "style": style, "size": size}

    async def decide(
        self,
        perceived_info: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Decides to generate an image."""
        print(
            f"ImageGenerationAgent {self.name} deciding to generate an image for: '{perceived_info['prompt']}'",
        )
        return {"action": "generate", "parameters": perceived_info}

    async def act(
        self,
        decision: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Generates the image."""
        if decision.get("action") == "generate":
            parameters = decision["parameters"]
            prompt = parameters["prompt"]
            style = parameters["style"]
            size = parameters["size"]
            print(f"ImageGenerationAgent {self.name} acting on prompt: '{prompt}'")
            await asyncio.sleep(
                1.0,
            )  # Simulate image generation process (can be removed if image_manager is fast)

            # Use the singleton image_manager to generate the image
            generated_image_url = await image_manager.generate_image(
                prompt,
                style,
                size,
            )
            return {"image_url": generated_image_url}
        return {}

    async def feedback(
        self,
        original_task: dict[str, Any],
        action_result: Any,
        context: dict[str, Any] | None = None,
    ) -> None:
        """Processes the feedback from the image generation action."""
        print(f"ImageGenerationAgent {self.name} received feedback for task.")


if __name__ == "__main__":

    async def main():
        print("--- Running ImageGenerationAgent Test ---")
        agent = ImageGenerationAgent(name="ArtBot")
        task1 = {
            "prompt": "a futuristic city at sunset",
            "style": "cyberpunk",
            "size": "512x512",
        }
        task2 = {
            "prompt": "a serene forest with a hidden waterfall",
            "style": "watercolor",
            "size": "1024x768",
        }

        # Start the agent in the background
        agent_task = asyncio.create_task(agent.start())

        await agent.submit_task(task1)
        await agent.submit_task(task2)

        # Give some time for tasks to be processed
        await asyncio.sleep(3)

        await agent.stop()
        await agent_task  # Wait for the agent to fully stop
        print("--- ImageGenerationAgent Test Finished ---")

    asyncio.run(main())
