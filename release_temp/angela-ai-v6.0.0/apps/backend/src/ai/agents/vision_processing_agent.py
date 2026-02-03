import asyncio
from typing import Any  # Added Optional

from apps.backend.src.ai.agents.base_agent import BaseAgent

from ...services.vision_service import (
    vision_manager,
)  # Import the shared singleton instance


class VisionProcessingAgent(BaseAgent):
    """A specialized AI agent for processing and analyzing visual data (images, video frames)."""

    def __init__(
        self,
        agent_id: str = None,
        name: str = "VisionProcessingAgent",
        **kwargs: Any,
    ):
        super().__init__(agent_id=agent_id, name=name, **kwargs)
        print(f"VisionProcessingAgent {self.name} initialized.")

    async def perceive(
        self,
        task: dict[str, Any],
        retrieved_memories: list[dict[str, Any]],
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """Extracts vision processing parameters from the task."""
        image_source = task.get("image_url") or task.get("image_data")
        processing_type = task.get("processing_type", "object_detection")
        parameters = task.get("parameters", {})
        if not image_source:
            raise ValueError("No image source provided.")
        print(
            f"VisionProcessingAgent {self.name} perceiving task: '{processing_type}' for image source: {image_source[:50]}...",
        )
        return {
            "image_source": image_source,
            "processing_type": processing_type,
            "parameters": parameters,
        }

    async def decide(
        self,
        perceived_info: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Decides to perform vision processing."""
        print(
            f"VisionProcessingAgent {self.name} deciding to perform {perceived_info['processing_type']}.",
        )
        return {"action": "process", "parameters": perceived_info}

    async def act(
        self,
        decision: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Performs the vision processing."""
        if decision.get("action") == "process":
            parameters = decision["parameters"]
            image_source = parameters["image_source"]
            processing_type = parameters["processing_type"]
            parameters = parameters["parameters"]
            print(
                f"VisionProcessingAgent {self.name} acting on processing type: '{processing_type}'",
            )
            await asyncio.sleep(
                2.0,
            )  # Simulate vision processing process (can be removed if vision_manager is fast)

            # Use the singleton vision_manager to perform the processing
            processing_result = await vision_manager.process_image(
                image_source,
                processing_type,
                parameters,
            )
            return processing_result
        return {}

    async def feedback(
        self,
        original_task: dict[str, Any],
        action_result: Any,
        context: dict[str, Any] | None = None,
    ) -> None:
        """Processes the feedback from the vision processing action."""
        print(f"VisionProcessingAgent {self.name} received feedback for task.")


if __name__ == "__main__":

    async def main():
        print("--- Running VisionProcessingAgent Test ---")
        agent = VisionProcessingAgent(name="EyeBot")
        task1 = {
            "image_url": "https://example.com/image1.jpg",
            "processing_type": "object_detection",
        }
        task2 = {
            "image_data": "base64encodedimagedata...",
            "processing_type": "face_recognition",
        }

        # Start the agent in the background
        agent_task = asyncio.create_task(agent.start())

        await agent.submit_task(task1)
        await agent.submit_task(task2)

        # Give some time for tasks to be processed
        await asyncio.sleep(5)

        await agent.stop()
        await agent_task  # Wait for the agent to fully stop
        print("--- VisionProcessingAgent Test Finished ---")

    asyncio.run(main())
