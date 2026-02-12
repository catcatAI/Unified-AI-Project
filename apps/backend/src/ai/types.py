from typing import TypedDict, Dict, Any, List, Optional
from typing_extensions import Required
from enum import Enum
import logging
logger = logging.getLogger(__name__)

class AgentStatus(Enum):
    """Enumeration of different agent statuses."""
    UNKNOWN = "unknown"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"
    DEGRADED = "degraded"

class RegisteredAgent(TypedDict):
    """Type definition for a registered AI agent."""
    agent_id: Required[str]
    agent_name: Required[str]
    capabilities: Required[List[Dict[str, Any]]]
    registration_time: Required[float]
    last_seen: Required[float]
    status: Required[str]
    metadata: Required[Dict[str, Any]]

class CollaborationTask(TypedDict):
    """Type definition for a collaboration task between agents."""
    task_id: Required[str]
    requester_agent_id: Required[str]
    target_agent_id: Required[str]
    capability_id: Required[str]
    parameters: Required[Dict[str, Any]]
    status: Required[str]
    result: Optional[Dict[str, Any]]
    error_message: Optional[str]

class AgentHealthReport(TypedDict):
    """Type definition for an agent health report."""
    agent_id: Required[str]
    agent_name: Required[str]
    status: Required[AgentStatus]
    cpu_usage: Required[float]
    memory_usage: Required[float]
    last_heartbeat: Required[float]
    capabilities: Required[List[str]]
    error_count: Required[int]
    last_error: Optional[str]
    response_time_ms: Optional[float]
    task_count: Required[int]
    success_rate: Required[float]
