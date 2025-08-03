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

class HSPTaskStatusOutput(BaseModel):
    correlation_id: str
    status: str # pending, completed, failed, unknown_or_expired
    message: Optional[str] = None
    result_payload: Optional[Dict[str, Any]] = None
    error_details: Optional[Dict[str, Any]] = None

# --- Atlassian API Models ---
class AtlassianConfigModel(BaseModel):
    domain: str
    userEmail: str
    apiToken: str
    cloudId: str

class ConfluencePageModel(BaseModel):
    spaceKey: str
    title: str
    content: str
    parentId: Optional[str] = None

class JiraIssueModel(BaseModel):
    projectKey: str
    summary: str
    description: str
    issueType: str = "Task"
    priority: str = "Medium"

class RovoDevTaskModel(BaseModel):
    capability: str
    parameters: Dict[str, Any]

class JQLSearchModel(BaseModel):
    jql: str