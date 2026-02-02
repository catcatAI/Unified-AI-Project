import asyncio
from typing import Any  # Added Optional

from apps.backend.src.ai.agents.base_agent import BaseAgent

from ...services.audio_service import (
    audio_manager,
)  # Import the shared singleton instance


class AudioProcessingAgent(BaseAgent):
    """A specialized AI agent for processing and analyzing audio data."""

    def __init__(
        self,
        agent_id: str = None,
        name: str = "AudioProcessingAgent",
        **kwargs: Any,
    ):
        super().__init__(agent_id=agent_id, name=name, **kwargs)
        print(f"AudioProcessingAgent {self.name} initialized.")

    async def perceive(
        self,
        task: dict[str, Any],
        retrieved_memories: list[dict[str, Any]],
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """Extracts audio processing parameters from the task."""
        audio_source = task.get("audio_url") or task.get("audio_data")
        processing_type = task.get("processing_type", "speech_to_text")
        parameters = task.get("parameters", {})
        if not audio_source:
            raise ValueError("No audio source provided.")
        print(
            f"AudioProcessingAgent {self.name} perceiving task: '{processing_type}' for audio source: {audio_source[:50]}...",
        )
        return {
            "audio_source": audio_source,
            "processing_type": processing_type,
            "parameters": parameters,
        }

    async def decide(
        self,
        perceived_info: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Decides to perform audio processing."""
        print(
            f"AudioProcessingAgent {self.name} deciding to perform {perceived_info['processing_type']}.",
        )
        return {"action": "process", "parameters": perceived_info}

    async def act(
        self,
        decision: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Performs the audio processing."""
        if decision.get("action") == "process":
            parameters = decision["parameters"]
            audio_source = parameters["audio_source"]
            processing_type = parameters["processing_type"]
            parameters = parameters["parameters"]
            print(
                f"AudioProcessingAgent {self.name} acting on processing type: '{processing_type}'",
            )
            await asyncio.sleep(
                1.8,
            )  # Simulate audio processing process (can be removed if audio_manager is fast)

            # Use the singleton audio_manager to perform the processing
            processing_result = await audio_manager.process_audio(
                audio_source,
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
        """Processes the feedback from the audio processing action."""
        print(f"AudioProcessingAgent {self.name} received feedback for task.")


if __name__ == "__main__":

    async def main():
        print("--- Running AudioProcessingAgent Test ---")
        agent = AudioProcessingAgent(name="SoundBot")
        task1 = {
            "audio_url": "https://example.com/audio1.wav",
            "processing_type": "speech_to_text",
        }
        task2 = {
            "audio_data": "base64encodedaudiodata...",
            "processing_type": "sentiment_analysis",
        }

        # Start the agent in the background
        agent_task = asyncio.create_task(agent.start())

        await agent.submit_task(task1)
        await agent.submit_task(task2)

        # Give some time for tasks to be processed
        await asyncio.sleep(4)

        await agent.stop()
        await agent_task  # Wait for the agent to fully stop
        print("--- AudioProcessingAgent Test Finished ---")

    asyncio.run(main())
