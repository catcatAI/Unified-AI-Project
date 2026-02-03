import asyncio
import logging
from typing import TYPE_CHECKING, Any

from .base_agent import BaseAgent

if TYPE_CHECKING:
    from ..agent_manager import AgentManager

logger = logging.getLogger(__name__)


class AgentCollaborationManager(BaseAgent):
    """An agent responsible for routing messages and tasks between other agents.
    It acts as a central hub for inter-agent communication, ensuring that
    communication is traceable and managed.
    """

    def __init__(self, agent_manager: "AgentManager", **kwargs: Any):
        # Correctly pass the agent_manager to the parent class constructor.
        super().__init__(agent_manager=agent_manager, **kwargs)
        if not self.agent_manager:
            raise ValueError(
                "AgentCollaborationManager requires an instance of AgentManager.",
            )
        logger.info("AgentCollaborationManager initialized with AgentManager.")
        self.agent_response_queues: dict[str, asyncio.Queue] = {}

    async def _response_handler(self, message: dict[str, Any]):
        """Placeholder response handler for messages received from the HSP connector.
        In a real implementation, this would process incoming responses.
        """
        logger.debug(f"AgentCollaborationManager received response: {message}")

    async def perceive(
        self,
        task: dict[str, Any],
        retrieved_memories: list[dict[str, Any]],
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Perceives a task and extracts relevant information based on its operation type.
        This agent ignores retrieved memories as it is purely reactive.
        """
        logger.debug(f"{self.name} perceiving task: {task}")
        if retrieved_memories:
            logger.debug(
                f"Ignoring {len(retrieved_memories)} retrieved memories as they are not needed for this agent.",
            )

        operation = task.get("operation")
        task_type = task.get("type")

        if operation == "register_agent":
            return {"operation": "register_agent", "payload": task.get("payload", {})}
        if operation == "orchestrate":
            return {"operation": "orchestrate", "payload": task.get("payload", {})}
        if task_type == "route_message":
            return {"operation": "route_message", "data": task.get("data", {})}
        logger.warning(
            f"Received unexpected task operation or type: {operation or task_type}",
        )
        return {}

    async def decide(
        self,
        perceived_info: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Decides to act based on the perceived information."""
        logger.debug(f"{self.name} deciding based on: {perceived_info}")
        operation = perceived_info.get("operation")

        if operation == "register_agent":
            return {
                "action": "register_agent",
                "details": perceived_info.get("payload", {}),
            }
        if operation == "orchestrate":
            return {
                "action": "orchestrate",
                "details": perceived_info.get("payload", {}),
            }
        if operation == "route_message":
            return {
                "action": "route_message",
                "details": perceived_info.get("data", {}),
            }
        logger.warning(f"No decision made for perceived info: {perceived_info}")
        return {"action": "no_op", "details": {}}

    async def act(
        self,
        decision: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Executes actions based on the decision, including agent registration,
        task orchestration, and message routing.
        """
        action = decision.get("action")
        details = decision.get("details", {})

        if action == "register_agent":
            agent_name = details.get("agent_name")
            agent_id = details.get("agent_id")
            if not all([agent_name, agent_id]):
                error_msg = (
                    "Registration failed: 'agent_name' and 'agent_id' are required."
                )
                logger.error(error_msg)
                return {"status": "failed", "error": error_msg}

            # Assuming agent_manager has a method to register agents
            self.agent_manager.register_agent(agent_id, agent_name)
            # Initialize a queue for this agent's responses
            self.agent_response_queues[agent_id] = asyncio.Queue()
            logger.info(f"Agent '{agent_name}' registered with ID '{agent_id}'.")
            return {
                "status": "completed",
                "result": {
                    "message": f"Agent '{agent_name}' registered with ID '{agent_id}'.",
                },
            }

        if action == "orchestrate":
            subtasks = details.get("subtasks", [])
            orchestration_results = []
            overall_status = "completed"  # Assume completed unless a subtask fails

            for subtask in subtasks:
                target_agent_id = subtask.get("target_agent_id")
                task_payload = subtask

                if not target_agent_id:
                    orchestration_results.append(
                        {
                            "status": "failed",
                            "error": "Subtask missing target_agent_id.",
                        },
                    )
                    overall_status = "failed"
                    continue

                running_agents = self.agent_manager.get_running_agents()
                target_agent = self.agent_manager.get_agent(
                    target_agent_id,
                )  # Use get_agent to ensure it's a managed agent

                if not target_agent:
                    orchestration_results.append(
                        {
                            "status": "failed",
                            "error": f"Target agent '{target_agent_id}' not found or not running.",
                        },
                    )
                    overall_status = "failed"
                    continue

                try:
                    # Prepare the message to send to the target agent via HSP
                    message_to_send = {
                        **task_payload,  # Include original subtask details
                        "response_topic": f"collab_manager/{self.agent_id}/responses",
                        "manager_id": self.agent_id,
                    }
                    await self.hsp_connector.send_message(
                        f"agent/{target_agent_id}/tasks",
                        message_to_send,
                    )

                    # Wait for the response from the target agent
                    response = await asyncio.wait_for(
                        self.agent_response_queues[target_agent_id].get(),
                        timeout=self.task_timeout,  # Use the manager's task_timeout for subtask responses
                    )
                    orchestration_results.append(
                        {
                            "status": "completed",
                            "agent_id": target_agent_id,
                            "result": response,
                        },
                    )
                except asyncio.TimeoutError:
                    orchestration_results.append(
                        {
                            "status": "failed",
                            "agent_id": target_agent_id,
                            "error": f"Subtask timed out after {self.task_timeout} seconds.",
                        },
                    )
                    overall_status = "failed"
                except Exception as e:
                    orchestration_results.append(
                        {
                            "status": "failed",
                            "agent_id": target_agent_id,
                            "error": str(e),
                        },
                    )
                    overall_status = (
                        "failed"  # Mark overall as failed if any subtask fails
                    )

            return {
                "status": overall_status,
                "result": {"orchestration_summary": orchestration_results},
            }

        if action == "route_message":
            target_agent_id = details.get("target_agent_id")
            message = details.get("message")

            if not all([target_agent_id, message]):
                error_msg = (
                    "Routing failed: 'target_agent_id' and 'message' are required."
                )
                logger.error(error_msg)
                return {"status": "failed", "error": error_msg}

            logger.info(
                f"{self.name} routing message from '{details.get('sending_agent_id')}' to '{target_agent_id}'",
            )

            running_agents = self.agent_manager.get_running_agents()
            target_agent = self.agent_manager.get_agent(
                target_agent_id,
            )  # Use get_agent to ensure it's a managed agent

            if not target_agent:
                error_msg = f"Routing failed: Target agent '{target_agent_id}' not found or not running."
                logger.error(error_msg)
                return {"status": "failed", "error": error_msg}

            try:
                await target_agent.submit_task(message)
                return {
                    "status": "success",
                    "detail": f"Message successfully routed to agent {target_agent_id}.",
                }
            except Exception as e:
                error_msg = f"Routing failed: An error occurred while submitting task to agent '{target_agent_id}': {e}"
                logger.error(error_msg, exc_info=True)
                return {"status": "failed", "error": error_msg}
        else:
            logger.warning(f"Unknown action: {action}")
            return {"status": "failed", "error": f"Unknown action: {action}"}

    async def feedback(
        self,
        original_task: dict[str, Any],
        action_result: Any,
        context: dict[str, Any] | None = None,
    ) -> None:
        """Logs the result of the routing action."""
        logger.debug(f"Feedback for routing task: {action_result}")
        # This agent's feedback loop is simple, as it only cares about whether the routing was successful.
