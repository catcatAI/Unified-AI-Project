import asyncio
from typing import Any  # Added Optional

from apps.backend.src.ai.agents.base_agent import BaseAgent

from ...services.code_analysis_service import (
    code_analysis_manager,
)  # Import the shared singleton instance


class CodeUnderstandingAgent(BaseAgent):
    """A specialized AI agent for understanding, analyzing, and explaining code."""

    def __init__(
        self,
        agent_id: str = None,
        name: str = "CodeUnderstandingAgent",
        **kwargs: Any,
    ):
        super().__init__(agent_id=agent_id, name=name, **kwargs)
        print(f"CodeUnderstandingAgent {self.name} initialized.")

    async def perceive(
        self,
        task: dict[str, Any],
        retrieved_memories: list[dict[str, Any]],
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """Extracts code understanding parameters from the task."""
        code = task.get("code", "def hello_world():\n    print('Hello, World!')")
        request_type = task.get(
            "request_type",
            "explain",
        )  # e.g., 'explain', 'refactor', 'debug'
        language = task.get("language", "python")
        print(
            f"CodeUnderstandingAgent {self.name} perceiving task: '{request_type}' for code in {language}",
        )
        return {"code": code, "request_type": request_type, "language": language}

    async def decide(
        self,
        perceived_info: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Decides to analyze the code."""
        print(
            f"CodeUnderstandingAgent {self.name} deciding to {perceived_info['request_type']} the code.",
        )
        return {"action": "analyze", "parameters": perceived_info}

    async def act(
        self,
        decision: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Analyzes the code."""
        if decision.get("action") == "analyze":
            parameters = decision["parameters"]
            code = parameters["code"]
            request_type = parameters["request_type"]
            language = parameters["language"]
            print(
                f"CodeUnderstandingAgent {self.name} acting on request: '{request_type}'",
            )
            await asyncio.sleep(
                1.2,
            )  # Simulate code analysis process (can be removed if code_analysis_manager is fast)

            # Use the singleton code_analysis_manager to perform the analysis
            analysis_result = await code_analysis_manager.analyze_code(
                code,
                request_type,
                language,
            )
            return analysis_result
        return {}

    async def feedback(
        self,
        original_task: dict[str, Any],
        action_result: Any,
        context: dict[str, Any] | None = None,
    ) -> None:
        """Processes the feedback from the code analysis action."""
        print(f"CodeUnderstandingAgent {self.name} received feedback for task.")


if __name__ == "__main__":

    async def main():
        print("--- Running CodeUnderstandingAgent Test ---")
        agent = CodeUnderstandingAgent(name="CodeGuru")
        task1 = {
            "code": "def add(a, b): return a + b",
            "request_type": "explain",
            "language": "python",
        }
        task2 = {
            "code": "function greet() { console.log('Hi'); }",
            "request_type": "refactor",
            "language": "javascript",
        }

        # Start the agent in the background
        agent_task = asyncio.create_task(agent.start())

        await agent.submit_task(task1)
        await agent.submit_task(task2)

        # Give some time for tasks to be processed
        await asyncio.sleep(3)

        await agent.stop()
        await agent_task  # Wait for the agent to fully stop
        print("--- CodeUnderstandingAgent Test Finished ---")

    asyncio.run(main())
