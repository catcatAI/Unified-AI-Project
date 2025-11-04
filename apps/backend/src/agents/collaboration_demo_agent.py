import asyncio
import logging
import os
import sys
import uuid # Added missing import
from typing import Any, Dict, List, Optional, Union

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

try:
    from .base_agent import BaseAgent
    from apps.backend.src.core.hsp.types import HSPTaskRequestPayload, HSPMessageEnvelope
except ImportError:
    from apps.backend.src.agents.base_agent import BaseAgent
    from apps.backend.src.core.hsp.types import HSPTaskRequestPayload, HSPMessageEnvelope

logger = logging.getLogger(__name__)

class CollaborationDemoAgent(BaseAgent):
    """
    A demo agent that showcases the collaboration features between agents.
    """

    def __init__(self, agent_id: str) -> None:
        # Define capabilities for this agent
        capabilities = [
            {
                "capability_id": "collaboration_demo_v1",
                "name": "Collaboration Demo",
                "description": "Demonstrates agent collaboration features",
                "version": "1.0"
            },
            {
                "capability_id": "data_processing_v1",
                "name": "Data Processing",
                "description": "Processes data from other agents",
                "version": "1.0"
            }
        ]

        super().__init__(agent_id, capabilities, "CollaborationDemoAgent")

    async def handle_task_request(self, task_payload: HSPTaskRequestPayload,
                                  sender_ai_id: str, envelope: HSPMessageEnvelope):
        """
        Handle incoming task requests.
        """
        logger.info(f"[{self.agent_id}] Handling task request from {sender_ai_id}")

        request_id = task_payload.get("request_id", "")
        capability_id = task_payload.get("capability_id_filter", "")
        parameters = task_payload.get("parameters", {})

        try:
            # Process based on capability
            if capability_id == "collaboration_demo_v1":
                result = await self._handle_collaboration_demo(parameters)
            elif capability_id == "data_processing_v1":
                result = await self._handle_data_processing(parameters)
            else:
                # Default behavior for unhandled capabilities
                await self.send_task_failure(
                    request_id,
                    sender_ai_id,
                    task_payload.get("callback_address", ""),
                    f"Unsupported capability: {capability_id}"
                )
                return

            # Send success response
            await self.send_task_success(
                request_id,
                sender_ai_id,
                task_payload.get("callback_address", ""),
                result
            )

        except Exception as e:
            logger.error(f"[{self.agent_id}] Error handling task: {e}")
            await self.send_task_failure(
                request_id,
                sender_ai_id,
                task_payload.get("callback_address", ""),
                str(e)
            )

    async def _handle_collaboration_demo(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle collaboration demo requests.
        """
        logger.info(f"[{self.agent_id}] Handling collaboration demo request")

        # Example Orchestrate a multi-agent task
        if parameters.get("orchestrate_tasks"):
            task_sequence = [
                {
                    "capability_id": "data_analysis_v1",
                    "parameters": {
                        "action": "analyze",
                        "data": parameters.get("data", [])
                    }
                },
                {
                    "capability_id": "report_generation_v1",
                    "parameters": {
                        "action": "generate",
                        "input": "<output_of_task_0>",  # Placeholder for previous task result
                        "format": "summary"
                    }
                }
            ]

            # Try to orchestrate the task sequence
            try:
                result = await self.orchestrate_multi_agent_task(task_sequence)
                return {
                    "status": "success",
                    "result": result,
                    "message": "Multi-agent task orchestration completed"
                }
            except Exception as e:
                return {
                    "status": "error",
                    "message": f"Failed to orchestrate tasks: {str(e)}"
                }

        # Simple collaboration example
        elif parameters.get("delegate_task"):
            target_agent = parameters.get("target_agent", "")
            task_params = parameters.get("task_parameters", {})

            if target_agent and task_params:
                try:
                    task_id = await self.delegate_task_to_agent(
                        target_agent_id=target_agent,
                        capability_id=task_params.get("capability_id", ""),
                        parameters=task_params
                    )

                    return {
                        "status": "delegated",
                        "task_id": task_id,
                        "message": f"Task delegated to {target_agent}"
                    }
                except Exception as e:
                    return {
                        "status": "error",
                        "message": f"Failed to delegate task: {str(e)}"
                    }

        # Default response
        return {
            "status": "success",
            "message": "Collaboration demo agent is working",
            "agent_id": self.agent_id
        }

    async def _handle_data_processing(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle data processing requests.
        """
        logger.info(f"[{self.agent_id}] Handling data processing request")

        # Simple data processing example
        data = parameters.get("data", [])
        operation = parameters.get("operation", "count")

        result: Union[int, float, str]
        if operation == "count":
            result = len(data)
        elif operation == "sum":
            result = sum(data) if all(isinstance(x, (int, float)) for x in data) else 0
        elif operation == "average":
            result = sum(data) / len(data) if data and all(isinstance(x, (int, float)) for x in data) else 0
        else:
            result = f"Unsupported operation: {operation}"

        return {
            "status": "success",
            "result": result,
            "operation": operation
        }

async def main() -> None:
    """
    Main function to run the collaboration demo agent.
    """
    # Create agent with a unique ID
    agent_id = f"did:hsp:collaboration_demo_agent_{uuid.uuid4().hex[:8]}"
    agent = CollaborationDemoAgent(agent_id)

    try:
        # Start the agent
        await agent.start()
        logger.info(f"Collaboration Demo Agent {agent_id} started successfully")

        # Keep the agent running
        while agent.is_running:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error(f"Error in main: {e}")
    finally:
        # Stop the agent
        await agent.stop()
        logger.info("Collaboration Demo Agent stopped")

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Run the agent
    asyncio.run(main())