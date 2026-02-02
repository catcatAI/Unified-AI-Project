import asyncio
import random
import time
import uuid
from typing import Any

from apps.backend.src.ai.agents.base_agent import BaseAgent


class MonitoringDemoAgent(BaseAgent):
    """A specialized AI agent designed to demonstrate basic monitoring capabilities.
    This agent will simulate monitoring the status and activity of other (simulated) agents.
    """

    def __init__(
        self,
        agent_id: str = None,
        name: str = "MonitoringDemoAgent",
        **kwargs: Any,
    ):
        super().__init__(agent_id=agent_id, name=name, **kwargs)
        print(f"MonitoringDemoAgent {self.name} initialized.")
        self.simulated_agents_to_monitor: dict[str, dict[str, Any]] = {}

    async def perceive(
        self,
        task: dict[str, Any],
        retrieved_memories: list[dict[str, Any]],
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """Perceives the monitoring task."""
        operation = task.get("operation", "get_agent_status")
        payload = task.get("payload", {})
        print(
            f"MonitoringDemoAgent {self.name} perceiving task: '{operation}' with payload: {payload}",
        )
        return {"operation": operation, "payload": payload}

    async def decide(self, perceived_info: dict[str, Any]) -> dict[str, Any]:
        """Decides which monitoring operation to perform."""
        print(
            f"MonitoringDemoAgent {self.name} deciding to perform operation: '{perceived_info['operation']}'",
        )
        return {
            "action": perceived_info["operation"],
            "payload": perceived_info["payload"],
        }

    async def act(self, decision: dict[str, Any]) -> dict[str, Any]:
        """Acts on the monitoring decision."""
        operation = decision.get("action")
        payload = decision.get("payload")
        print(f"MonitoringDemoAgent {self.name} acting on operation: '{operation}'")
        await asyncio.sleep(0.7)  # Simulate monitoring process
        return self._simulate_monitoring_operation(operation, payload)

    async def feedback(self, original_task: dict[str, Any], action_result: Any) -> None:
        """Processes feedback from the monitoring action."""
        print(f"MonitoringDemoAgent {self.name} received feedback for task.")

    def _simulate_monitoring_operation(
        self,
        operation: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Internal method to simulate monitoring operations."""
        if operation == "start_monitoring":
            agent_id = payload.get("agent_id", str(uuid.uuid4()))
            agent_name = payload.get("agent_name", "Simulated Agent")
            self.simulated_agents_to_monitor[agent_id] = {
                "name": agent_name,
                "status": random.choice(["active", "idle"]),
                "last_heartbeat": time.time(),
                "tasks_completed": random.randint(0, 50),
                "error_rate": round(random.uniform(0.0, 0.1), 2),
            }
            return {
                "status": "success",
                "message": f"Started monitoring '{agent_name}' ({agent_id}).",
            }
        if operation == "get_agent_status":
            agent_id = payload.get("agent_id")
            if agent_id and agent_id in self.simulated_agents_to_monitor:
                # Simulate updating status
                self.simulated_agents_to_monitor[agent_id]["status"] = random.choice(
                    ["active", "idle", "error"],
                )
                self.simulated_agents_to_monitor[agent_id]["last_heartbeat"] = (
                    time.time()
                )
                self.simulated_agents_to_monitor[agent_id]["tasks_completed"] += (
                    random.randint(0, 5)
                )
                return {
                    "status": "success",
                    "agent_status": self.simulated_agents_to_monitor[agent_id],
                }
            if not agent_id:
                return {
                    "status": "success",
                    "all_agents_status": self.simulated_agents_to_monitor,
                }
            return {
                "status": "failed",
                "message": f"Agent '{agent_id}' not found for status check.",
            }
        return {"message": f"Unknown monitoring operation: {operation}"}


if __name__ == "__main__":

    async def main():
        print("--- Running MonitoringDemoAgent Test ---")
        monitor_demo = MonitoringDemoAgent(name="DemoMonitor")

        # Start the demo monitor in the background
        monitor_demo_task = asyncio.create_task(monitor_demo.start())

        # Simulate starting to monitor some agents
        agent_id_1 = str(uuid.uuid4())
        agent_id_2 = str(uuid.uuid4())

        start_monitor_task1 = {
            "operation": "start_monitoring",
            "payload": {"agent_id": agent_id_1, "agent_name": "AgentX"},
        }
        start_monitor_task2 = {
            "operation": "start_monitoring",
            "payload": {"agent_id": agent_id_2, "agent_name": "AgentY"},
        }

        await monitor_demo.submit_task(start_monitor_task1)
        await monitor_demo.submit_task(start_monitor_task2)

        await asyncio.sleep(1)  # Give time for monitoring to start

        # Get status of a specific agent
        get_status_task1 = {
            "operation": "get_agent_status",
            "payload": {"agent_id": agent_id_1},
        }
        await monitor_demo.submit_task(get_status_task1)

        await asyncio.sleep(1)  # Give time for status update

        # Get status of all monitored agents
        get_all_status_task = {"operation": "get_agent_status"}
        await monitor_demo.submit_task(get_all_status_task)

        await asyncio.sleep(2)  # Final sleep before stopping

        await monitor_demo.stop()
        await monitor_demo_task  # Wait for the demo monitor to fully stop
        print("--- MonitoringDemoAgent Test Finished ---")

    asyncio.run(main())
