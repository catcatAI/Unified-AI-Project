import asyncio
from typing import Any

from apps.backend.src.ai.agents.base_agent import BaseAgent
from apps.backend.src.services.audio_service import audio_manager
from apps.backend.src.services.code_analysis_service import code_analysis_manager
from apps.backend.src.services.data_analysis_service import data_analysis_manager
from apps.backend.src.services.image_service import image_manager

# Import all service managers
from apps.backend.src.services.llm_service import llm_manager
from apps.backend.src.services.nlp_service import nlp_manager
from apps.backend.src.services.planning_service import planning_manager
from apps.backend.src.services.search_service import search_manager
from apps.backend.src.services.vision_service import vision_manager


class ToolUsingAgent(BaseAgent):
    """A specialized AI agent that can utilize various external tools/services
    to accomplish complex tasks. This agent acts as an orchestrator,
    dispatching sub-tasks to other specialized service managers.
    """

    def __init__(
        self,
        agent_id: str = None,
        name: str = "ToolUsingAgent",
        **kwargs: Any,
    ):
        super().__init__(agent_id=agent_id, name=name, **kwargs)
        print(f"ToolUsingAgent {self.name} initialized.")

    async def perceive(
        self,
        task: dict[str, Any],
        retrieved_memories: list[dict[str, Any]],
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """Perceives the task and extracts parameters for tool usage.
        The task should specify which tool to use and its parameters.
        Example task: {"tool": "search", "query": "latest AI models"}
        """
        tool_name = task.get("tool")
        tool_parameters = task.get("parameters", {})
        print(
            f"ToolUsingAgent {self.name} perceiving task to use tool: '{tool_name}' with parameters: {tool_parameters}",
        )
        return {"tool_name": tool_name, "tool_parameters": tool_parameters}

    async def decide(
        self,
        perceived_info: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Decides which tool to use based on perceived information."""
        tool_name = perceived_info.get("tool_name")
        if tool_name:
            print(f"ToolUsingAgent {self.name} deciding to use tool: '{tool_name}'")
            return {
                "action": "use_tool",
                "tool_name": tool_name,
                "tool_parameters": perceived_info.get("tool_parameters", {}),
            }
        print(f"ToolUsingAgent {self.name} decided no tool to use for task.")
        return {"action": "no_tool"}

    async def act(
        self,
        decision: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> Any:
        """Executes the chosen tool/service."""
        action = decision.get("action")
        if action == "use_tool":
            tool_name = decision["tool_name"]
            tool_parameters = decision["tool_parameters"]
            print(
                f"ToolUsingAgent {self.name} acting: Using tool '{tool_name}' with parameters: {tool_parameters}",
            )

            # Dispatch to appropriate service manager based on tool_name
            if tool_name == "llm":
                response = await llm_manager.generate(
                    model=tool_parameters.get(
                        "model",
                        "simulated-llm",
                    ),  # Added model parameter
                    prompt=tool_parameters.get("prompt", "Say hello."),
                )
                return {"tool_name": tool_name, "response": response}
            if tool_name == "search":
                response = await search_manager.search(
                    query=tool_parameters.get("query", "AI news"),
                    num_results=tool_parameters.get("num_results", 3),
                )
                return {"tool_name": tool_name, "response": response}
            if tool_name == "image_generation":
                response = await image_manager.generate_image(
                    prompt=tool_parameters.get("prompt", "A cat"),
                    style=tool_parameters.get("style", "photorealistic"),
                    size=tool_parameters.get("size", "512x512"),
                )
                return {"tool_name": tool_name, "response": response}
            if tool_name == "code_analysis":
                response = await code_analysis_manager.analyze_code(
                    code=tool_parameters.get("code", "print('hello')"),
                    request_type=tool_parameters.get("request_type", "explain"),
                    language=tool_parameters.get("language", "python"),
                )
                return {"tool_name": tool_name, "response": response}
            if tool_name == "data_analysis":
                response = await data_analysis_manager.analyze_data(
                    data=tool_parameters.get("data", []),
                    analysis_type=tool_parameters.get("analysis_type", "summary"),
                    parameters=tool_parameters.get("parameters", {}),
                )
                return {"tool_name": tool_name, "response": response}
            if tool_name == "nlp_processing":
                response = await nlp_manager.process_text(
                    text=tool_parameters.get("text", "Hello world"),
                    processing_type=tool_parameters.get("processing_type", "sentiment"),
                    parameters=tool_parameters.get("parameters", {}),
                )
                return {"tool_name": tool_name, "response": response}
            if tool_name == "vision_processing":
                response = await vision_manager.process_image(
                    image_source=tool_parameters.get(
                        "image_source",
                        "http://example.com/img.jpg",
                    ),
                    processing_type=tool_parameters.get(
                        "processing_type",
                        "object_detection",
                    ),
                    parameters=tool_parameters.get("parameters", {}),
                )
                return {"tool_name": tool_name, "response": response}
            if tool_name == "audio_processing":
                response = await audio_manager.process_audio(
                    audio_source=tool_parameters.get(
                        "audio_source",
                        "http://example.com/audio.wav",
                    ),
                    processing_type=tool_parameters.get(
                        "processing_type",
                        "speech_to_text",
                    ),
                    parameters=tool_parameters.get("parameters", {}),
                )
                return {"tool_name": tool_name, "response": response}
            if tool_name == "planning":
                response = await planning_manager.generate_plan(
                    goal=tool_parameters.get("goal", "achieve objective"),
                    constraints=tool_parameters.get("constraints", []),
                    context=tool_parameters.get("context", ""),
                )
                return {"tool_name": tool_name, "response": response}
            print(
                f"ToolUsingAgent {self.name}: Unknown tool '{tool_name}'. Simulating generic response.",
            )
            await asyncio.sleep(0.5)
            return {
                "tool_name": tool_name,
                "response": f"Simulated response for unknown tool '{tool_name}'",
            }
        return {}

    async def feedback(
        self,
        original_task: dict[str, Any],
        action_result: Any,
        context: dict[str, Any] | None = None,
    ) -> None:
        """Processes the feedback from the tool usage action."""
        print(
            f"ToolUsingAgent {self.name} received feedback for task. Tool used: {action_result.get('tool_name')}",
        )
        # In a real scenario, this could be used to learn from tool results


if __name__ == "__main__":

    async def main():
        print("--- Running ToolUsingAgent Test ---")
        agent = ToolUsingAgent(name="Orchestrator")

        # Start the agent in the background
        agent_task = asyncio.create_task(agent.start())

        # Test LLM tool
        task1 = {
            "tool": "llm",
            "parameters": {"prompt": "What is the capital of France?"},
        }
        await agent.submit_task(task1)
        await asyncio.sleep(1)

        # Test Search tool
        task2 = {
            "tool": "search",
            "parameters": {"query": "latest space discoveries", "num_results": 2},
        }
        await agent.submit_task(task2)
        await asyncio.sleep(1)

        # Test Image Generation tool
        task3 = {
            "tool": "image_generation",
            "parameters": {"prompt": "A futuristic cat", "style": "cartoon"},
        }
        await agent.submit_task(task3)
        await asyncio.sleep(1)

        # Test Code Analysis tool
        task4 = {
            "tool": "code_analysis",
            "parameters": {"code": "def foo(): pass", "request_type": "explain"},
        }
        await agent.submit_task(task4)
        await asyncio.sleep(1)

        # Test Data Analysis tool
        sample_data = [{"x": 1, "y": 2}, {"x": 3, "y": 4}]
        task5 = {
            "tool": "data_analysis",
            "parameters": {"data": sample_data, "analysis_type": "summary"},
        }
        await agent.submit_task(task5)
        await asyncio.sleep(1)

        # Test NLP Processing tool
        task6 = {
            "tool": "nlp_processing",
            "parameters": {
                "text": "I love this product!",
                "processing_type": "sentiment",
            },
        }
        await agent.submit_task(task6)
        await asyncio.sleep(1)

        # Test Vision Processing tool
        task7 = {
            "tool": "vision_processing",
            "parameters": {
                "image_source": "url_to_image.jpg",
                "processing_type": "object_detection",
            },
        }
        await agent.submit_task(task7)
        await asyncio.sleep(1)

        # Test Audio Processing tool
        task8 = {
            "tool": "audio_processing",
            "parameters": {
                "audio_source": "url_to_audio.wav",
                "processing_type": "speech_to_text",
            },
        }
        await agent.submit_task(task8)
        await asyncio.sleep(1)

        # Test Planning tool
        task9 = {
            "tool": "planning",
            "parameters": {"goal": "organize event", "constraints": ["budget", "time"]},
        }
        await agent.submit_task(task9)
        await asyncio.sleep(1)

        await agent.stop()
        await agent_task  # Wait for the agent to fully stop
        print("--- ToolUsingAgent Test Finished ---")

    asyncio.run(main())
