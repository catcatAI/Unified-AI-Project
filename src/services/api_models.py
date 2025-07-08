from typing import Optional, Literal # Added Literal
from pydantic import BaseModel

class UserInput(BaseModel):
    text: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None

class AIOutput(BaseModel):
    response_text: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    timestamp: str

class SessionStartRequest(BaseModel):
    user_id: Optional[str] = None

from typing import Optional, Dict, Any # Added Dict, Any
from pydantic import BaseModel, Field # Added Field

class SessionStartResponse(BaseModel):
    greeting: str
    session_id: str
    timestamp: str

# --- HSP Task Brokering API Models ---

class HSPTaskRequestInput(BaseModel):
    target_capability_id: str = Field(..., description="The unique ID of the capability to be invoked on the target HSP peer.")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="A dictionary of parameters to be sent to the target capability.")
    # Optional: could add user_id, session_id if the API needs to pass this context for the task
    # user_id: Optional[str] = None
    # session_id: Optional[str] = None

class HSPTaskRequestOutput(BaseModel):
    status_message: str # e.g., "Request sent" or "Error: Capability not found"
    correlation_id: Optional[str] = None
    target_capability_id: str
    error: Optional[str] = None

class HSPTaskStatusOutput(BaseModel):
    correlation_id: str
    status: Literal["pending", "completed", "failed", "unknown_or_expired"]
    result_payload: Optional[Dict[str, Any]] = None # Actual payload if status is "completed"
    error_details: Optional[Dict[str, Any]] = None  # Error details if status is "failed"
    message: Optional[str] = None # Optional message, e.g. for unknown status
