"""
ANGELA-MATRIX: [L2] [α] [A] [L2]
Canonical Pydantic models for API I/O.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class UserInput(BaseModel):
    user_id: str
    session_id: str
    text: str


class AIOutput(BaseModel):
    response_text: str
    user_id: str
    session_id: str
    timestamp: str


class SessionStartRequest(BaseModel):
    user_id: str


class SessionStartResponse(BaseModel):
    greeting: str
    session_id: str
    timestamp: str


class HSPTaskRequestInput(BaseModel):
    target_capability_id: str
    parameters: Dict[str, Any]


class HSPTaskRequestOutput(BaseModel):
    status_message: str
    correlation_id: Optional[str] = None
    target_capability_id: str
    error: Optional[str] = None


# --- Atlassian Models ---
class AtlassianConfigModel(BaseModel):
    base_url: str
    username: str
    api_token: str


class ConfluencePageModel(BaseModel):
    space_key: str
    title: str
    content: str


class JiraIssueModel(BaseModel):
    project_key: str
    summary: str
    description: str


class RovoDevTaskModel(BaseModel):
    capability: str
    parameters: Dict[str, Any]


class JQLSearchModel(BaseModel):
    jql: str


# --- Hot Status Models ---
class HotStatusModel(BaseModel):
    draining: bool
    services_initialized: Dict[str, bool]
    hsp: Dict[str, Any]
    mcp: Dict[str, Any]
    metrics: Dict[str, Any]


# --- Health Models ---
class HealthStatusModel(BaseModel):
    status: str
    timestamp: str
    services_initialized: Dict[str, bool]
    components: Dict[str, Any] = {}


# --- Readiness Models ---
class ReadinessStatusModel(BaseModel):
    ready: bool
    timestamp: str
    services_initialized: Dict[str, bool]
    signals: Dict[str, Any] = {}
    reason: Optional[str] = None


# --- HSP Service Discovery Models ---
class HSPCapabilityModel(BaseModel):
    capability_id: str
    name: str
    description: str
    version: str
    ai_id: str
    availability_status: str
    tags: List[str] = []
    supported_interfaces: List[str] = []
    metadata: Dict[str, Any] = {}


__all__ = [
    "UserInput",
    "AIOutput",
    "SessionStartRequest",
    "SessionStartResponse",
    "HSPTaskRequestInput",
    "HSPTaskRequestOutput",
    "AtlassianConfigModel",
    "ConfluencePageModel",
    "JiraIssueModel",
    "RovoDevTaskModel",
    "JQLSearchModel",
    "HotStatusModel",
    "HealthStatusModel",
    "ReadinessStatusModel",
    "HSPCapabilityModel",
]
