import hashlib
import json
import time
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class CollaborationTask:
    task_id: str
    agent_id: str
    task_type: str
    payload: Dict[str, Any]
    status: str = "pending"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


class AgentCollaborationManager:
    def __init__(self):
        self._tasks: Dict[str, CollaborationTask] = {}
        self._agents: Dict[str, List[str]] = {}
        logger.debug("AgentCollaborationManager initialized")

    def register_agent(self, agent_id: str, capabilities: List[str]) -> None:
        self._agents[agent_id] = capabilities

    def assign_task(self, agent_id: str, task_type: str, payload: Dict[str, Any]) -> Optional[str]:
        if agent_id not in self._agents:
            return None
        task_id = hashlib.md5(f"{agent_id}{task_type}{time.time()}".encode()).hexdigest()[:12]
        task = CollaborationTask(task_id=task_id, agent_id=agent_id, task_type=task_type, payload=payload)
        self._tasks[task_id] = task
        return task_id

    def get_agent_tasks(self, agent_id: str) -> List[CollaborationTask]:
        return [t for t in self._tasks.values() if t.agent_id == agent_id]

    def update_task_status(self, task_id: str, status: str) -> bool:
        if task_id in self._tasks:
            self._tasks[task_id].status = status
            return True
        return False
