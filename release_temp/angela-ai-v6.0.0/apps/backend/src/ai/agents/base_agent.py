import asyncio
import logging
import uuid
from abc import ABC, abstractmethod
from typing import Any

# Import for type hinting, will be defined in its own module
from apps.backend.src.ai.memory.ham_memory_manager import HAMMemoryManager
from apps.backend.src.tools.tool_registry import get_tool

# Configure logging for the module
logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Base class for all AI agents in the Unified AI Project.
    Provides fundamental functionalities like unique identification and task handling,
    and defines the core "Perception-Decision-Action-Feedback" loop for AGI.
    """

    def __init__(
        self,
        agent_id: str | None = None,
        name: str = "BaseAgent",
        task_timeout: int = 300,
        memory_manager: HAMMemoryManager | None = None,
        agent_manager: Any | None = None,
        **kwargs: Any,
    ):
        """Initializes the BaseAgent.

        Args:
            agent_id (Optional[str]): A unique identifier for the agent. If None, a new UUID is generated.
            name (str): The name of the agent.
            task_timeout (int): The maximum time (in seconds) allowed for a task to complete. Defaults to 300 seconds (5 minutes).
            memory_manager (Optional[HAMMemoryManager]): An optional memory manager instance for the agent to use.
            agent_manager (Optional[Any]): An optional agent manager instance for inter-agent communication.
            **kwargs (Any): Additional keyword arguments for specialized agent configurations.

        """
        self.agent_id: str = agent_id if agent_id else str(uuid.uuid4())
        self.name: str = name
        self.is_running: bool = False
        self.task_queue = asyncio.Queue()
        self.extra_config = kwargs
        self.task_timeout = task_timeout
        self.memory_manager = memory_manager
        self.agent_manager = agent_manager
        logger.info(
            f"BaseAgent {self.name} initialized. Memory Manager: {'Available' if self.memory_manager else 'Not Available'}",
        )

    @abstractmethod
    async def perceive(
        self,
        task: dict[str, Any],
        retrieved_memories: list[dict[str, Any]],
        context: dict[str, Any] | None = None,
    ) -> Any:
        """Abstract method for the perception phase.
        Specialized agents must implement this to gather and interpret information relevant to the task.

        Args:
            task (Dict[str, Any]): The incoming task.
            retrieved_memories (List[Dict[str, Any]]): Memories retrieved based on the task query.
            context (Optional[Dict[str, Any]]): The shared context dictionary for the task.

        Returns:
            Any: Perceived information or context.

        """

    @abstractmethod
    async def decide(
        self,
        perceived_info: Any,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Abstract method for the decision-making phase.
        Specialized agents must implement this to formulate a plan or action based on perceived information.

        Args:
            perceived_info (Any): Information gathered during the perception phase.
            context (Optional[Dict[str, Any]]): The shared context dictionary for the task.

        Returns:
            Dict[str, Any]: A dictionary representing the decision or plan.

        """

    @abstractmethod
    async def act(
        self,
        decision: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> Any:
        """Abstract method for the action phase.
        Specialized agents must implement this to execute the decided plan or action.

        Args:
            decision (Dict[str, Any]): The decision or plan formulated in the decision phase.
            context (Optional[Dict[str, Any]]): The shared context dictionary for the task.

        Returns:
            Any: The result or outcome of the action.

        """

    async def _execute_tool(self, tool_name: str, **kwargs: Any) -> Any:
        """A helper method to find and execute a tool from the registry.

        Args:
            tool_name (str): The name of the tool to execute.
            **kwargs: The arguments to pass to the tool's execute method.

        Returns:
            The result of the tool's execution.

        Raises:
            ValueError: If the tool is not found in the registry.
            Exception: Propagates exceptions from the tool's execution.

        """
        logger.debug(
            f"Agent {self.name} attempting to execute tool '{tool_name}' with args: {kwargs}",
        )
        tool = get_tool(tool_name)
        if not tool:
            error_msg = f"Tool '{tool_name}' not found in the registry."
            logger.error(error_msg)
            raise ValueError(error_msg)

        try:
            result = await tool.execute(**kwargs)
            logger.debug(
                f"Tool '{tool_name}' executed successfully with result: {result}",
            )
            return result
        except Exception as e:
            logger.error(f"Error executing tool '{tool_name}': {e}", exc_info=True)
            # Re-raise the exception to be handled by the agent's main error handler
            raise e

    @abstractmethod
    async def feedback(
        self,
        original_task: dict[str, Any],
        action_result: Any,
        context: dict[str, Any] | None = None,
    ) -> None:
        """Abstract method for the feedback phase.
        Specialized agents must implement this to process the outcome of their actions,
        learn from it, and potentially trigger memory storage. The actual storage
        is handled by the BaseAgent's handle_task method after this is called.

        Args:
            original_task (Dict[str, Any]): The original task that initiated the cycle.
            action_result (Any): The result or outcome of the action phase.
            context (Optional[Dict[str, Any]]): The shared context dictionary for the task.

        """

    async def handle_task(
        self,
        task: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Orchestrates the "Perception-Decision-Action-Feedback" loop for a given task,
        now with integrated memory retrieval and storage.

        Args:
            task (Dict[str, Any]): The task to be handled.
            context (Optional[Dict[str, Any]]): An optional dictionary to maintain and share state
                                                 within the task's lifecycle.

        Returns:
            Dict[str, Any]: The final result of the task processing.

        """
        if context is None:
            context = {}
        context["agent_id"] = self.agent_id
        context["agent_name"] = self.name
        context["task_id"] = task.get(
            "task_id",
            str(uuid.uuid4()),
        )  # Assign a task_id if not present

        logger.info(
            f"Agent {self.name} ({self.agent_id}) received task: {task.get('type', 'unknown')} (Task ID: {context['task_id']})",
        )

        async def _execute_lifecycle():
            # 0. Memory Retrieval (before Perception)
            retrieved_memories = []
            if self.memory_manager:
                query = task.get("description", str(task.get("user_input", "")))
                if query:
                    retrieved_memories = self.memory_manager.retrieve_relevant_memories(
                        query,
                    )
                    logger.debug(
                        f"Agent {self.name} retrieved {len(retrieved_memories)} memories for query '{query}'.",
                    )
            context["retrieved_memories"] = retrieved_memories

            # 1. Perception
            perceived_info = await self.perceive(task, retrieved_memories, context)
            context["perceived_info"] = (
                perceived_info  # Store in context for later stages
            )
            logger.debug(
                f"Agent {self.name} perceived (Task ID: {context['task_id']}): {perceived_info}",
            )

            # 2. Decision
            decision = await self.decide(perceived_info, context)
            context["decision"] = decision  # Store in context
            logger.debug(
                f"Agent {self.name} decided (Task ID: {context['task_id']}): {decision}",
            )

            # 3. Action
            action_result = await self.act(decision, context)
            context["action_result"] = action_result  # Store in context
            logger.debug(
                f"Agent {self.name} acted, result (Task ID: {context['task_id']}): {action_result}",
            )

            # 4. Feedback (Agent-specific processing of the result)
            await self.feedback(task, action_result, context)
            logger.debug(
                f"Agent {self.name} processed feedback (Task ID: {context['task_id']}).",
            )

            # Determine final status based on action_result
            if isinstance(action_result, dict) and "status" in action_result:
                final_status = action_result
            else:
                final_status = {"status": "completed", "result": action_result}
            context["final_status"] = final_status

            # 5. Memory Storage (after Feedback)
            if self.memory_manager:
                # Create a comprehensive experience record
                experience_to_store = {
                    "type": "task_completion",
                    "task": task,
                    "outcome": final_status,
                    "full_context": context,  # Store the entire context for rich memory
                }
                self.memory_manager.store_experience(experience_to_store)
                logger.debug(
                    f"Agent {self.name} stored experience for task {context['task_id']}.",
                )

            return final_status  # Return the simplified final_status

        try:
            return await asyncio.wait_for(
                _execute_lifecycle(),
                timeout=self.task_timeout,
            )
        except asyncio.TimeoutError:
            logger.error(
                f"Agent {self.name} ({self.agent_id}) task (ID: {context['task_id']}) timed out after {self.task_timeout} seconds.",
                exc_info=True,
            )
            return {
                "status": "failed",
                "error": f"Task timed out after {self.task_timeout} seconds.",
                "context": context,
            }
        except Exception as e:
            logger.error(
                f"Agent {self.name} ({self.agent_id}) task (ID: {context['task_id']}) failed to handle task: {e}",
                exc_info=True,
            )
            return {"status": "failed", "error": str(e), "context": context}

    async def start(self):
        """Starts the agent's task processing loop.
        The agent will continuously fetch and handle tasks from its queue until stopped.
        """
        self.is_running = True
        logger.info(f"Agent {self.name} ({self.agent_id}) started.")
        while self.is_running:
            try:
                task = await self.task_queue.get()
                if task is None:  # Sentinel to stop the agent
                    self.is_running = False
                    break
                await self.handle_task(task)
            except asyncio.CancelledError:
                logger.info(f"Agent {self.name} ({self.agent_id}) task loop cancelled.")
                break
            except Exception as e:
                logger.error(
                    f"Agent {self.name} ({self.agent_id}) encountered an error: {e}",
                    exc_info=True,
                )

    async def stop(self):
        """Stops the agent gracefully.
        It sends a sentinel to the task queue to signal the processing loop to terminate.
        """
        if self.is_running:
            await self.task_queue.put(None)  # Send sentinel to stop the loop
            logger.info(f"Agent {self.name} ({self.agent_id}) stopping...")
        self.is_running = False

    async def submit_task(self, task: dict[str, Any]):
        """Submits a task to the agent's internal queue for asynchronous processing.

        Args:
            task (Dict[str, Any]): The task to be submitted.

        """
        await self.task_queue.put(task)
        logger.info(f"Task submitted to agent {self.name} ({self.agent_id}).")

    async def send_message(self, target_agent_id: str, message_content: dict[str, Any]):
        """Sends a message to another agent via the AgentManager.

        Args:
            target_agent_id (str): The unique ID of the agent to receive the message.
            message_content (Dict[str, Any]): The content of the message, which will be submitted
                                               as a task to the target agent.

        """
        if not self.agent_manager:
            logger.error(
                f"Agent {self.name} cannot send message: AgentManager is not available.",
            )
            return

        logger.debug(f"Agent {self.name} sending message to {target_agent_id}.")
        await self.agent_manager.route_message(
            sending_agent_id=self.agent_id,
            target_agent_id=target_agent_id,
            message=message_content,
        )


if __name__ == "__main__":
    # We need a mock/stub for the HAMMemoryManager to test this in isolation
    class MockMemoryManager(HAMMemoryManager):
        def __init__(self):
            super().__init__()
            logger.info("MockMemoryManager initialized.")

        def retrieve_relevant_memories(
            self,
            query: str,
            limit: int = 5,
        ) -> list[dict[str, Any]]:
            print(f"\n--- MOCK MEMORY: Retrieving memories for query: '{query}' ---")
            # Simulate retrieval
            if "data_1" in query:
                return [{"content": "Previously saw data_1 and it was important."}]
            return []

        def store_experience(self, experience: dict[str, Any]) -> int:
            print(
                f"--- MOCK MEMORY: Storing experience of type '{experience.get('type')}' ---",
            )
            super().store_experience(experience)
            return 1  # Dummy ID

    class ConcreteAgent(BaseAgent):
        async def perceive(
            self,
            task: dict[str, Any],
            retrieved_memories: list[dict[str, Any]],
            context: dict[str, Any] | None = None,
        ) -> Any:
            logger.info(f"ConcreteAgent perceiving task: {task.get('type')}")
            if retrieved_memories:
                logger.info(f"Found {len(retrieved_memories)} relevant memories.")
                print(f"Retrieved memories: {retrieved_memories}")
            await asyncio.sleep(0.05)
            return {"perceived_data": f"Data from {task.get('data', 'N/A')}"}

        async def decide(
            self,
            perceived_info: Any,
            context: dict[str, Any] | None = None,
        ) -> dict[str, Any]:
            logger.info(f"ConcreteAgent deciding based on: {perceived_info}")
            await asyncio.sleep(0.05)
            return {
                "action_type": "process",
                "target": perceived_info.get("perceived_data"),
            }

        async def act(
            self,
            decision: dict[str, Any],
            context: dict[str, Any] | None = None,
        ) -> Any:
            logger.info(
                f"ConcreteAgent acting: {decision.get('action_type')} on {decision.get('target')}",
            )
            await asyncio.sleep(0.1)
            return {
                "action_status": "success",
                "processed_item": decision.get("target"),
            }

        async def feedback(
            self,
            original_task: dict[str, Any],
            action_result: Any,
            context: dict[str, Any] | None = None,
        ) -> None:
            logger.info(
                f"ConcreteAgent receiving feedback for task {original_task.get('type')}: {action_result}",
            )
            # This is where an agent might decide if a memory is worth keeping, but storage is handled by base class
            print("--- AGENT FEEDBACK: Processing feedback before memory storage ---")
            await asyncio.sleep(0.05)

    async def main():
        # Setup logging to see the output clearly
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
        )

        mock_memory = MockMemoryManager()
        agent = ConcreteAgent(
            name="TestConcreteAgentWithMemory",
            memory_manager=mock_memory,
        )

        task1 = {
            "type": "process_data",
            "data": "sample_data_1",
            "description": "process sample_data_1",
        }
        task2 = {
            "type": "analyze_report",
            "report_id": "R123",
            "description": "analyze report R123",
        }

        agent_task = asyncio.create_task(agent.start())

        await agent.submit_task(task1)
        await agent.submit_task(task2)

        await asyncio.sleep(2)

        await agent.stop()
        await agent_task

        print("\n--- FINAL MOCK MEMORY STATE ---")
        for mem in mock_memory.get_all_memories():
            print(mem)

    asyncio.run(main())
