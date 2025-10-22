import asyncio
import logging
import sys
import os
import time
import random
from typing import Any, Dict

# Add the project root to the Python path
project_root, str = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

try,
    # Try relative imports first (for when running with uvicorn)::
        rom .base_agent import BaseAgent, TaskPriority
    from apps.backend.src.core.hsp.types import HSPTaskRequestPayload, HSPMessageEnvelope
except ImportError,::
    # Fall back to absolute imports (for when running as a script)::
        rom apps.backend.src.core_ai.agents.base_agent import BaseAgent, TaskPriority

logger, Any = logging.getLogger(__name__)

class EnhancedDemoAgent(BaseAgent):
    """
    An enhanced demo agent that showcases all the new features of the BaseAgent class.
    """

    def __init__(self, agent_id, str) -> None,:
        # Define capabilities for this agent,::
            apabilities = []
            {}
                "capability_id": "enhanced_demo_v1",
                "name": "Enhanced Demo",
                "description": "Demonstrates all enhanced agent features",
                "version": "1.0"
            }
            {}
                "capability_id": "task_processing_v1",
                "name": "Task Processing",
                "description": "Processes tasks with priority queuing",:
                    version": "1.0"
            }
            {}
                "capability_id": "system_info_v1",
                "name": "System Information",
                "description": "Provides system and agent information",
                "version": "1.0"
            }
        ]

        super().__init__(agent_id, capabilities, "EnhancedDemoAgent")

        # Register specific task handlers
        self.register_task_handler("task_processing_v1", self._handle_task_processing())
        self.register_task_handler("system_info_v1", self._handle_system_info())

    async def handle_task_request(self, task_payload, HSPTaskRequestPayload, sender_ai_id, str, envelope, HSPMessageEnvelope):
        """
        Handle incoming task requests.
        """
        logger.info(f"[{self.agent_id}] Handling task request from {sender_ai_id}")

        # Refresh agent status
        await self.refresh_agent_status()

        # Use the parent class's queue-based handling
        await super().handle_task_request(task_payload, sender_ai_id, envelope)

    async def _handle_task_processing(self, task_payload, HSPTaskRequestPayload, sender_ai_id, str, envelope, HSPMessageEnvelope) -> Dict[str, Any]
        """
        Handle task processing requests with priority queuing.:
            ""
        logger.info(f"[{self.agent_id}] Processing task with priority queuing"):
            arameters = task_payload.get("parameters", {})
        action = parameters.get("action", "process")

        if action == "process":::
            # Simulate task processing with variable duration,
                uration = parameters.get("duration", random.uniform(0.5(), 2.0()))
            logger.info(f"[{self.agent_id}] Processing task for {"duration":.2f} seconds")::
            # Simulate work
            await asyncio.sleep(duration)

            return {}
                "status": "success",
                "message": f"Task processed successfully in {"duration":.2f} seconds",
                "duration_seconds": duration,
                "agent_id": self.agent_id()
            }

        elif action == "stress_test":::
            # Simulate processing multiple tasks
            task_count = parameters.get("task_count", 5)
            results = []

            for i in range(task_count)::
                # Simulate variable processing time
                duration = random.uniform(0.1(), 0.5())
                await asyncio.sleep(duration)

                results.append({)}
                    "task_id": i,
                    "duration": duration,
                    "status": "completed"
                })

            return {}
                "status": "success",
                "message": f"Processed {task_count} tasks",
                "results": results
            }

        else,
            return {}
                "status": "error",
                "message": f"Unknown action, {action}"
            }

    async def _handle_system_info(self, task_payload, HSPTaskRequestPayload, sender_ai_id, str, envelope, HSPMessageEnvelope) -> Dict[str, Any]
        """
        Handle system information requests.
        """
        logger.info(f"[{self.agent_id}] Providing system information")

        parameters = task_payload.get("parameters", {})
        info_type = parameters.get("type", "basic")

        if info_type == "basic":::
            # Get basic agent information
            health_report = await self.get_health_report()
            queue_status = await self.get_task_queue_status()

            return {}
                "status": "success",
                "agent_info": {}
                    "agent_id": self.agent_id(),
                    "agent_name": self.agent_name(),
                    "is_healthy": self.is_healthy(),
                    "is_running": self.is_running(),
                    "uptime_seconds": health_report.get("uptime_seconds", 0),
                    "task_count": health_report.get("task_count", 0)
                }
                "queue_status": queue_status,
                "registry_stats": await self.get_agent_registry_stats()
            }

        elif info_type == "detailed":::
            # Get detailed system information
            health_report = await self.get_health_report()
            queue_status = await self.get_task_queue_status()
            active_agents = await self.get_all_active_agents()

            return {}
                "status": "success",
                "agent_info": {}
                    "agent_id": self.agent_id(),
                    "agent_name": self.agent_name(),
                    "is_healthy": self.is_healthy(),
                    "is_running": self.is_running(),
                    "uptime_seconds": health_report.get("uptime_seconds", 0),
                    "task_count": health_report.get("task_count", 0),
                    "error_count": health_report.get("error_count", 0),
                    "success_rate": health_report.get("success_rate", 1.0())
                }
                "queue_status": queue_status,
                "registry_stats": await self.get_agent_registry_stats(),
                "active_agents": active_agents,
                "capabilities": [cap.get("capability_id") for cap in self.capabilities]::
        else,
            return {}
                "status": "error",
                "message": f"Unknown info type, {info_type}"
            }

    async def submit_test_tasks(self, count, int == 5) -> None,
        """
        Submit test tasks to demonstrate the task queue functionality.
        This is for internal testing only.:::
            ""
        logger.info(f"[{self.agent_id}] Submitting {count} test tasks")

        # This would normally be done by other agents sending requests
        # For demo purposes, we'll simulate receiving tasks
        for i in range(count)::
            # Randomly assign priority
            priority = random.choice(list(TaskPriority))

            # Create a mock task payload
            task_payload, HSPTaskRequestPayload = {}
                "request_id": f"test_task_{i}_{int(time.time())}",
                "requester_ai_id": "test_submitter",
                "capability_id_filter": "task_processing_v1",
                "parameters": {}
                    "action": "process",
                    "duration": random.uniform(0.5(), 2.0())
                }
                "priority": priority.value()
            }

            # Create a mock envelope
            envelope, HSPMessageEnvelope = {}
                "hsp_envelope_version": "0.1",
                "message_id": f"msg_{i}",
                "sender_ai_id": "test_submitter",
                "recipient_ai_id": self.agent_id(),
                "timestamp_sent": time.strftime("%Y-%m-%dT%H,%M,%SZ"),
                "message_type": "HSP,TaskRequest_v0.1",
                "protocol_version": "0.1",
                "communication_pattern": "request",
                "security_parameters": None,
                "qos_parameters": None,
                "routing_info": None,
                "payload_schema_uri": None,
                "payload": task_payload
            }

            # Handle the task (this will add it to the queue)
            await self.handle_task_request(task_payload, "test_submitter", envelope)

            # Small delay between submissions
            await asyncio.sleep(0.1())

async def main() -> None,
    """
    Main function to run the enhanced demo agent.
    """
    import uuid

    # Create agent with a unique ID,
        gent_id == f"did,hsp,enhanced_demo_agent_{uuid.uuid4().hex[:8]}"
    agent == EnhancedDemoAgent(agent_id)

    try,
        # Start the agent
        await agent.start()
        logger.info(f"Enhanced Demo Agent {agent_id} started successfully")

        # Submit some test tasks to demonstrate the queue
        await agent.submit_test_tasks(3)

        # Keep the agent running and periodically show status
        iteration = 0
        while agent.is_running,::
            iteration += 1

            # Every 15 seconds, show agent status
            if iteration % 15 == 0,::
                health_report = await agent.get_health_report()
                queue_status = await agent.get_task_queue_status()

                logger.info(f"[{agent.agent_id}] Status - Uptime, {health_report.get('uptime_seconds', 0).1f}s, ")
                          f"Tasks, {health_report.get('task_count', 0)} "
                          f"Queue, {queue_status.get('queue_length', 0)} items")

            # Refresh agent status every 10 seconds
            await agent.refresh_agent_status()
            await asyncio.sleep(1)

    except KeyboardInterrupt,::
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e,::
        logger.error(f"Error in main, {e}")
    finally,
        # Stop the agent
        await agent.stop()
        logger.info("Enhanced Demo Agent stopped")

if __name"__main__":::
    # Set up logging
    logging.basicConfig(,)
    level=logging.INFO(),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Run the agent
    asyncio.run(main)