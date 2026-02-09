import asyncio
import logging
import os
import sys
import hashlib # Added missing import
import json # Added missing import
import time # Added missing import
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field # Added field import
from enum import Enum

from core.hsp.connector import HSPConnector
from core.hsp.types import HSPTaskRequestPayload, HSPTaskResultPayload, HSPMessageEnvelope

logger = logging.getLogger(__name__)


class CollaborationStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class CollaborationTask:
    task_id: str
    requester_agent_id: str
    target_agent_id: str
    capability_id: str
    parameters: Dict[str, Any]
    status: CollaborationStatus = CollaborationStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class AgentCollaborationManager:
    """
    Manages collaboration between different AI agents in the Unified AI Project.
    This class handles task delegation, result aggregation,
    and inter-agent communication.
    """

    def __init__(self, hsp_connector: HSPConnector) -> None:
        self.hsp_connector = hsp_connector
        self.active_collaborations: Dict[str, CollaborationTask] = {}
        self.agent_capabilities: Dict[str, List[str]] = {}
        self.collaboration_lock = asyncio.Lock()

        # Register callbacks for task results
        if self.hsp_connector:
            self.hsp_connector.register_on_task_result_callback(self._handle_task_result)

    async def register_agent_capability(self, agent_id: str, capability_id: str):
        """Register an agent's capability for collaboration."""
        async with self.collaboration_lock:
            if agent_id not in self.agent_capabilities:
                self.agent_capabilities[agent_id] = []

            if capability_id not in self.agent_capabilities[agent_id]:
                self.agent_capabilities[agent_id].append(capability_id)
                logger.info(f"Registered capability '{capability_id}' for agent '{agent_id}'")
    async def find_agent_for_capability(self, capability_id: str) -> Optional[str]:
        """Find an agent that can handle the specified capability."""
        async with self.collaboration_lock:
            for agent_id, capabilities in self.agent_capabilities.items():
                if capability_id in capabilities:
                    return agent_id
            return None

    async def delegate_task(self, requester_agent_id: str, target_agent_id: str,
                            capability_id: str, parameters: Dict[str, Any]) -> str:
        """
        Delegate a task from one agent to another.

        Args:
                requester_agent_id: ID of the agent requesting the task
                target_agent_id: ID of the agent to handle the task
                capability_id: The capability needed to handle the task
                parameters: Parameters for the task
        Returns: str Task ID for tracking the collaboration
        """
        task_id = f"collab_task_{len(self.active_collaborations) + 1}"

        # Create collaboration task
        collaboration_task = CollaborationTask(
            task_id=task_id,
            requester_agent_id=requester_agent_id,
            target_agent_id=target_agent_id,
            capability_id=capability_id,
            parameters=parameters
        )

        # Store the task
        async with self.collaboration_lock:
            self.active_collaborations[task_id] = collaboration_task

        # Send task request via HSP
        task_payload = HSPTaskRequestPayload(
            request_id=task_id,
            requester_ai_id=requester_agent_id,
            target_ai_id=target_agent_id,
            capability_id_filter=capability_id,
            parameters=parameters,
            status="pending"
        )

        try:
            # Send the task request
            success = await self.hsp_connector.send_task_request(
                payload=task_payload,
                target_ai_id_or_topic=target_agent_id
            )

            if success:
                collaboration_task.status = CollaborationStatus.IN_PROGRESS
                logger.info(f"Delegated task '{task_id}' from '{requester_agent_id}' to '{target_agent_id}'")
            else:
                collaboration_task.status = CollaborationStatus.FAILED
                collaboration_task.error_message = "Failed to send task request via HSP"
                logger.error(f"Failed to delegate task '{task_id}' from '{requester_agent_id}' to '{target_agent_id}'")

        except Exception as e:
            collaboration_task.status = CollaborationStatus.FAILED
            collaboration_task.error_message = str(e)
            logger.error(f"Exception while delegating task '{task_id}': {e}")
        return task_id

    async def _handle_task_result(self, result_payload: HSPTaskResultPayload,
                                  sender_ai_id: str, envelope: HSPMessageEnvelope):
        """Handle task results from collaborating agents."""
        task_id = result_payload.get("request_id", "")

        async with self.collaboration_lock:
            if task_id in self.active_collaborations:
                collaboration_task = self.active_collaborations[task_id]

                if result_payload.get("status") == "success":
                    collaboration_task.status = CollaborationStatus.COMPLETED
                    collaboration_task.result = result_payload.get("payload", {})
                    logger.info(f"Task '{task_id}' completed successfully")
                else:
                    collaboration_task.status = CollaborationStatus.FAILED
                    collaboration_task.error_message = result_payload.get("error_details", {}).get("error_message", "Unknown error")
                    logger.error(f"Task '{task_id}' failed: {collaboration_task.error_message}")

    async def get_collaboration_status(self, task_id: str) -> Optional[CollaborationTask]:
        """Get the status of a collaboration task."""
        async with self.collaboration_lock:
            return self.active_collaborations.get(task_id)

    async def orchestrate_multi_agent_task(self, requester_agent_id: str, task_sequence: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Orchestrate a sequence of tasks across multiple agents.
        """
        results = {}

        for i, task_def in enumerate(task_sequence):
            capability_id = task_def["capability_id"]
            parameters = task_def.get("parameters", {})

            # Replace placeholders with previous results
            for key, value in parameters.items():
                if isinstance(value, str) and " < output_of_task_" in value:
                    try:
                        task_index_str = value.split(" < output_of_task_")[1].split(" > ")[0]
                        task_index = int(task_index_str)
                        if task_index in results:
                            parameters[key] = results[task_index]
                    except (ValueError, IndexError):
                        logger.warning(f"Failed to parse dependency placeholder: {value}")

            # Find an agent for this capability
            target_agent_id = await self.find_agent_for_capability(capability_id)

            if not target_agent_id:
                logger.error(f"No agent found for capability '{capability_id}'")
                return {"status": "failed", "error": f"No agent found for capability '{capability_id}'"}
            
            # Delegate the task
            task_id = await self.delegate_task(
                requester_agent_id=requester_agent_id,
                target_agent_id=target_agent_id,
                capability_id=capability_id,
                parameters=parameters
            )

            # Wait for task completion (with timeout)
            timeout = task_def.get("timeout", 30)
            start_time = asyncio.get_event_loop().time()

            while asyncio.get_event_loop().time() - start_time < timeout:
                task_status = await self.get_collaboration_status(task_id)
                if task_status and task_status.status in [CollaborationStatus.COMPLETED, CollaborationStatus.FAILED]:
                    break
                await asyncio.sleep(0.5)

            # Check final status
            task_status = await self.get_collaboration_status(task_id)
            if task_status and task_status.status == CollaborationStatus.COMPLETED:
                results[i] = task_status.result
            else:
                error_msg = task_status.error_message if task_status else "Task timed out"
                logger.error(f"Task {i} failed: {error_msg}")
                return {"status": "failed", "error": f"Task {i} failed: {error_msg}"}

        return {"status": "success", "results": results}

    async def shutdown(self):
        """Shutdown the collaboration manager and clean up resources."""
        logger.info("Shutting down AgentCollaborationManager")
        # In a more complex implementation, we might want to cancel pending tasks
        # or notify other agents about shutdown