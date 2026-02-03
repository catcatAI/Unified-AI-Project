import asyncio
import logging
import random
import time
import uuid
from typing import Any

from apps.backend.src.ai.agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


class AgentMonitoringManager(BaseAgent):
    """A specialized AI agent for monitoring the status, performance, and activities of other agents."""

    def __init__(
        self,
        agent_id: str = None,
        name: str = "AgentMonitoringManager",
        **kwargs: Any,
    ):
        super().__init__(agent_id=agent_id, name=name, **kwargs)
        logger.info(f"AgentMonitoringManager {self.name} initialized.")
        self.monitored_agents: dict[
            str,
            dict[str, Any],
        ] = {}  # Stores status of monitored agents

    async def perceive(
        self,
        task: dict[str, Any],
        retrieved_memories: list[dict[str, Any]],
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """Perceives the monitoring task."""
        logger.debug(
            f"AgentMonitoringManager {self.name} perceiving task: {task.get('operation')}",
        )
        return task

    async def decide(self, perceived_info: dict[str, Any]) -> dict[str, Any]:
        """Decides which monitoring operation to perform."""
        operation = perceived_info.get("operation", "get_status_report")
        payload = perceived_info.get("payload", {})
        logger.debug(
            f"AgentMonitoringManager {self.name} deciding to perform operation: '{operation}'",
        )
        return {"action": operation, "payload": payload}

    async def act(self, decision: dict[str, Any]) -> dict[str, Any]:
        """Acts on the monitoring decision."""
        operation = decision.get("action")
        payload = decision.get("payload")
        logger.info(
            f"AgentMonitoringManager {self.name} acting on operation: '{operation}' with payload: {payload}",
        )
        await asyncio.sleep(0.5)  # Simulate monitoring process
        return self._simulate_monitoring_operation(operation, payload)

    async def feedback(self, original_task: dict[str, Any], action_result: Any) -> None:
        """Processes feedback from the monitoring action."""
        logger.debug(f"AgentMonitoringManager {self.name} received feedback for task.")

    def _simulate_monitoring_operation(
        self,
        operation: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Internal method to simulate agent monitoring operations."""
        if operation == "monitor_agent":
            agent_id = payload.get("agent_id")
            agent_name = payload.get("agent_name", "Unknown Agent")
            if agent_id:
                self.monitored_agents[agent_id] = {
                    "name": agent_name,
                    "status": random.choice(["active", "idle", "error"]),
                    "last_update": time.time(),
                    "tasks_processed": random.randint(0, 100),
                    "cpu_usage": round(random.uniform(0.1, 10.0), 2),
                    "memory_usage": round(random.uniform(50, 500), 2),  # MB
                }
                logger.info(
                    f"Monitoring started for agent '{agent_name}' ({agent_id}).",
                )
                return {
                    "status": "success",
                    "message": f"Monitoring started for agent '{agent_name}' ({agent_id}).",
                }
            logger.warning("Agent ID not provided for monitoring.")
            return {
                "status": "failed",
                "message": "Agent ID not provided for monitoring.",
            }
        if operation == "get_status_report":
            target_agent_id = payload.get("agent_id")
            if target_agent_id and target_agent_id in self.monitored_agents:
                logger.info(f"Generated status report for agent '{target_agent_id}'.")
                return {
                    "status": "success",
                    "report": self.monitored_agents[target_agent_id],
                }
            if not target_agent_id:
                logger.info("Generated status report for all monitored agents.")
                return {"status": "success", "report": self.monitored_agents}
            logger.warning(f"Agent '{target_agent_id}' not found in monitored list.")
            return {
                "status": "failed",
                "message": f"Agent '{target_agent_id}' not found in monitored list.",
            }
        logger.warning(f"Unknown monitoring operation: {operation}")
        return {"message": f"Unknown monitoring operation: {operation}"}


if __name__ == "__main__":

    async def main():
        print("--- Running AgentMonitoringManager Test ---")
        monitor = AgentMonitoringManager(name="MonitorBot")

        # Start the monitor in the background
        monitor_task = asyncio.create_task(monitor.start())

        # Simulate monitoring some agents
        agent_to_monitor_id_1 = str(uuid.uuid4())
        agent_to_monitor_id_2 = str(uuid.uuid4())

        monitor_task1 = {
            "operation": "monitor_agent",
            "payload": {
                "agent_id": agent_to_monitor_id_1,
                "agent_name": "CreativeWriter",
            },
        }
        monitor_task2 = {
            "operation": "monitor_agent",
            "payload": {
                "agent_id": agent_to_monitor_id_2,
                "agent_name": "ImageGenerator",
            },
        }

        await monitor.submit_task(monitor_task1)
        await monitor.submit_task(monitor_task2)

        # Give some time for monitoring to update
        await asyncio.sleep(1)

        # Get status reports
        report_task1 = {
            "operation": "get_status_report",
            "payload": {"agent_id": agent_to_monitor_id_1},
        }
        report_task2 = {"operation": "get_status_report"}  # Get report for all

        await monitor.submit_task(report_task1)
        await monitor.submit_task(report_task2)

        # Give some time for reports to process
        await asyncio.sleep(2)

        await monitor.stop()
        await monitor_task  # Wait for the monitor to fully stop
        print("--- AgentMonitoringManager Test Finished ---")

    asyncio.run(main())
