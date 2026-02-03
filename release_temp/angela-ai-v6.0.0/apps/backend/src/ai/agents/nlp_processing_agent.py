import asyncio
from typing import Any  # Added Optional

from apps.backend.src.ai.agents.base_agent import BaseAgent

from ...services.nlp_service import nlp_manager  # Import the shared singleton instance


class NLPProcessingAgent(BaseAgent):
    """A specialized AI agent for Natural Language Processing tasks."""

    def __init__(
        self,
        agent_id: str = None,
        name: str = "NLPProcessingAgent",
        **kwargs: Any,
    ):
        super().__init__(agent_id=agent_id, name=name, **kwargs)
        print(f"NLPProcessingAgent {self.name} initialized.")

    async def perceive(
        self,
        task: dict[str, Any],
        retrieved_memories: list[dict[str, Any]],
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """Extracts NLP processing parameters from the task."""
        text = task.get("text", "")
        processing_type = task.get("processing_type", "sentiment")
        parameters = task.get("parameters", {})
        if not text:
            raise ValueError("No text provided for NLP processing.")
        print(
            f"NLPProcessingAgent {self.name} perceiving task: '{processing_type}' for text: {text[:50]}...",
        )
        return {
            "text": text,
            "processing_type": processing_type,
            "parameters": parameters,
        }

    async def decide(
        self,
        perceived_info: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Decides to perform NLP processing."""
        print(
            f"NLPProcessingAgent {self.name} deciding to perform {perceived_info['processing_type']}.",
        )
        return {"action": "process", "parameters": perceived_info}

    async def act(
        self,
        decision: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Performs the NLP processing."""
        if decision.get("action") == "process":
            parameters = decision["parameters"]
            text = parameters["text"]
            processing_type = parameters["processing_type"]
            parameters = parameters["parameters"]
            print(
                f"NLPProcessingAgent {self.name} acting on processing type: '{processing_type}'",
            )
            await asyncio.sleep(
                1.5,
            )  # Simulate NLP processing process (can be removed if nlp_manager is fast)

            # Use the singleton nlp_manager to perform the processing
            processing_result = await nlp_manager.process_text(
                text,
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
        """Processes the feedback from the NLP processing action."""
        print(f"NLPProcessingAgent {self.name} received feedback for task.")


if __name__ == "__main__":

    async def main():
        print("--- Running NLPProcessingAgent Test ---")
        agent = NLPProcessingAgent(name="TextAnalyzer")
        task1 = {
            "text": "This is a wonderful day, I feel great!",
            "processing_type": "sentiment",
        }
        task2 = {
            "text": "The quick brown fox jumps over the lazy dog. This is a classic pangram used for testing typefaces and keyboards.",
            "processing_type": "summarization",
        }

        # Start the agent in the background
        agent_task = asyncio.create_task(agent.start())

        await agent.submit_task(task1)
        await agent.submit_task(task2)

        # Give some time for tasks to be processed
        await asyncio.sleep(4)

        await agent.stop()
        await agent_task  # Wait for the agent to fully stop
        print("--- NLPProcessingAgent Test Finished ---")

    asyncio.run(main())
