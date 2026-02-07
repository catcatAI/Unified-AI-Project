"""
Agent Monitoring Manager for Unified AI Project.
Manages monitoring and health checking for AI agents.
"""

import asyncio
import logging
import time
import psutil
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from ...core.hsp.types import HSPCapabilityAdvertisementPayload
from ...core.hsp.connector import HSPConnector

logger = logging.getLogger(__name__)


class AgentStatus(Enum):
    UNKNOWN = "unknown"
    STARTING = "starting"
    RUNNING = "running"
    DEGRADED = "degraded"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class AgentHealthReport:
    agent_id: str
    agent_name: str
    status: AgentStatus
    cpu_usage: float  # Percentage
    memory_usage: float  # Percentage
    last_heartbeat: float  # Timestamp
    capabilities: List[str]
    error_count: int
    last_error: Optional[str] = None
    response_time_ms: Optional[float] = None
    task_count: int = 0
    success_rate: float = 1.0  # Percentage of successful tasks


class AgentMonitoringManager:


    """


    Manages monitoring and health checking for AI agents in the Unified AI Project.


    This class tracks agent status, collects health metrics,


    and provides alerts for issues.


    """





    def __init__(self, hsp_connector: HSPConnector) -> None:


        self.hsp_connector = hsp_connector


        self.agent_health_reports: Dict[str, AgentHealthReport] = {}


        self.monitoring_lock = asyncio.Lock()


        self.monitoring_interval: int = 10  # seconds


        self.is_monitoring: bool = False


        self.monitoring_task: Optional[asyncio.Task] = None





        # Register callbacks for capability advertisements (to track agent capabilities)


        if self.hsp_connector:


            self.hsp_connector.register_on_capability_advertisement_callback(self._handle_capability_advertisement)

    async def start_monitoring(self) -> None:
        """Start the monitoring process."""
        if not self.is_monitoring:
            self.is_monitoring = True
            self.monitoring_task = asyncio.create_task(self._monitoring_loop())
            logger.info("Agent monitoring started")

    async def stop_monitoring(self) -> None:
        """Stop the monitoring process."""
        if self.is_monitoring:
            self.is_monitoring = False
            if self.monitoring_task:
                self.monitoring_task.cancel()
                try:
                    await self.monitoring_task
                except asyncio.CancelledError:
                    pass
            logger.info("Agent monitoring stopped")

    async def _monitoring_loop(self) -> None:
        """Main monitoring loop that periodically checks agent health."""
        while self.is_monitoring:
            try:
                await self._collect_health_metrics()
                await self._check_agent_status()
                await self._generate_alerts()
                await asyncio.sleep(self.monitoring_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")

    async def _collect_health_metrics(self) -> None:
        """Collect health metrics for all tracked agents."""
        async with self.monitoring_lock:
            # Collect system-level metrics
            system_cpu = psutil.cpu_percent(interval=1)
            system_memory = psutil.virtual_memory().percent

            # Update metrics for each agent
            for agent_id, report in self.agent_health_reports.items():
                try:
                    # In a real implementation, we would collect actual metrics from the agent
                    # For now, we'll simulate with system metrics
                    report.cpu_usage = system_cpu
                    report.memory_usage = system_memory
                    report.last_heartbeat = time.time()

                    # Simulate task count and success rate changes
                    if report.status == AgentStatus.RUNNING:
                        report.task_count += 1
                        # Randomly simulate success or failure
                        if random.random() < 0.95:  # 95% success rate
                            report.success_rate = (report.success_rate * report.task_count + 1) / (report.task_count + 1)
                        else:
                            report.success_rate = (report.success_rate * report.task_count) / (report.task_count + 1)
                            report.error_count += 1
                            report.last_error = "Simulated task failure"

                except Exception as e:
                    logger.error(f"Error collecting metrics for agent {agent_id}: {e}")
    async def _check_agent_status(self) -> None:
        """Check and update the status of all agents."""
        async with self.monitoring_lock:
            current_time = time.time()

            for agent_id, report in self.agent_health_reports.items():
                # Check if we've received a heartbeat recently
                time_since_heartbeat = current_time - report.last_heartbeat
                # Update status based on metrics
                if time_since_heartbeat > 30:  # No heartbeat for 30 seconds
                    report.status = AgentStatus.ERROR
                    if not report.last_error:
                        report.last_error = "No heartbeat received"
                elif report.cpu_usage > 90:  # High CPU usage
                    report.status = AgentStatus.DEGRADED
                    if not report.last_error:
                        report.last_error = "High CPU usage"
                elif report.memory_usage > 90:  # High memory usage
                    report.status = AgentStatus.DEGRADED
                    if not report.last_error:
                        report.last_error = "High memory usage"
                elif report.success_rate < 0.8:  # Low success rate
                    report.status = AgentStatus.DEGRADED
                    report.last_error = "Low task success rate"
                elif report.status == AgentStatus.UNKNOWN:
                    # If status is unknown but we're getting metrics, assume running
                    report.status = AgentStatus.RUNNING
    async def _generate_alerts(self) -> None:
        """Generate alerts for agents with issues."""
        async with self.monitoring_lock:
            for agent_id, report in self.agent_health_reports.items():
                # Generate alerts for degraded or error status
                if report.status in [AgentStatus.DEGRADED, AgentStatus.ERROR]:
                    alert_message = f"Agent {report.agent_name} ({agent_id}) is {report.status.value}"
                    if report.last_error:
                        alert_message += f": {report.last_error}"

                    logger.warning(alert_message)

                    # In a real implementation, we might send this to a monitoring system
                    # or notify administrators

    async def _handle_capability_advertisement(self, capability_payload: HSPCapabilityAdvertisementPayload,
                                               sender_ai_id: str, envelope: Dict[str, Any]) -> None:
        """Handle capability advertisements to track agent capabilities."""
        async with self.monitoring_lock:
            agent_id = capability_payload.get("ai_id", sender_ai_id)
            agent_name = capability_payload.get("agent_name", "Unknown")
            capability_id = capability_payload.get("capability_id", "")

            # Create or update agent health report
            if agent_id not in self.agent_health_reports:
                self.agent_health_reports[agent_id] = AgentHealthReport(
                    agent_id=agent_id,
                    agent_name=agent_name,
                    status=AgentStatus.UNKNOWN,
                    cpu_usage=0.0,
                    memory_usage=0.0,
                    last_heartbeat=0.0,
                    capabilities=[],
                    error_count=0,
                    success_rate=1.0,
                    task_count=0
                )

            # Add capability if not already present
            if capability_id and capability_id not in self.agent_health_reports[agent_id].capabilities:
                self.agent_health_reports[agent_id].capabilities.append(capability_id)

            # If this is the first capability, update status to STARTING
            if len(self.agent_health_reports[agent_id].capabilities) == 1:
                self.agent_health_reports[agent_id].status = AgentStatus.STARTING
    async def register_agent(self, agent_id: str, agent_name: str, capabilities: List[str]) -> None:
        """Register an agent for monitoring."""
        async with self.monitoring_lock:
            if agent_id not in self.agent_health_reports:
                self.agent_health_reports[agent_id] = AgentHealthReport(
                    agent_id=agent_id,
                    agent_name=agent_name,
                    status=AgentStatus.UNKNOWN,
                    cpu_usage=0.0,
                    memory_usage=0.0,
                    last_heartbeat=time.time(),
                    capabilities=capabilities,
                    error_count=0,
                    success_rate=1.0,
                    task_count=0
                )

    async def report_error(self, agent_id: str, error_message: str) -> None:
        """Report an error for an agent."""
        async with self.monitoring_lock:
            if agent_id in self.agent_health_reports:
                report = self.agent_health_reports[agent_id]
                report.error_count += 1
                report.last_error = error_message
                report.status = AgentStatus.ERROR

    async def report_task_result(self, agent_id: str, success: bool, response_time_ms: Optional[float] = None) -> None:
        """Report the result of a task for an agent."""
        async with self.monitoring_lock:
            if agent_id in self.agent_health_reports:
                report = self.agent_health_reports[agent_id]
                report.task_count += 1
                if response_time_ms is not None:
                    report.response_time_ms = response_time_ms

                if success:
                    report.success_rate = (report.success_rate * (report.task_count - 1) + 1) / report.task_count
                else:
                    report.success_rate = (report.success_rate * (report.task_count - 1)) / report.task_count
                    report.error_count += 1

    async def get_agent_health_report(self, agent_id: str) -> Optional[AgentHealthReport]:
        """Get the health report for a specific agent."""
        async with self.monitoring_lock:
            return self.agent_health_reports.get(agent_id)

    async def get_all_health_reports(self) -> Dict[str, AgentHealthReport]:
        """Get health reports for all agents."""
        async with self.monitoring_lock:
            return self.agent_health_reports.copy()

    async def shutdown(self) -> None:
        """Shutdown the monitoring manager."""
        await self.stop_monitoring()
        logger.info("Agent monitoring manager shutdown complete")
