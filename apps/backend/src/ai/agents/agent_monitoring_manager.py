"""
Agent Monitoring Manager for Unified AI Project.
Manages monitoring and health checking for AI agents.
"""

# =============================================================================
# ANGELA-MATRIX: [L3] [βγδ] [B] [L2]
# =============================================================================

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class AgentHealthReport:
    agent_id: str
    status: str
    last_heartbeat: Optional[str] = None
    task_count: int = 0
    error_count: int = 0
    metrics: Dict[str, Any] = field(default_factory=dict)


class AgentMonitoringManager:
    def __init__(self):
        self._reports: Dict[str, AgentHealthReport] = {}
        logger.debug("AgentMonitoringManager initialized")

    def register_agent(self, agent_id: str) -> None:
        self._reports[agent_id] = AgentHealthReport(
            agent_id=agent_id,
            status="registered",
            last_heartbeat=datetime.now().isoformat(),
        )

    def heartbeat(self, agent_id: str) -> bool:
        if agent_id in self._reports:
            self._reports[agent_id].last_heartbeat = datetime.now().isoformat()
            self._reports[agent_id].status = "active"
            return True
        return False

    def get_report(self, agent_id: str) -> Optional[AgentHealthReport]:
        return self._reports.get(agent_id)

    def get_all_reports(self) -> Dict[str, AgentHealthReport]:
        return self._reports
