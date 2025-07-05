from typing import Optional
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

class SessionStartResponse(BaseModel):
    greeting: str
    session_id: str
    timestamp: str
