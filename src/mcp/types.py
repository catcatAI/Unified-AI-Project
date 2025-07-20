from typing import TypedDict, Literal, Any, Optional, Dict

class MCPEnvelope(TypedDict):
    mcp_envelope_version: str
    message_id: str
    sender_id: str
    recipient_id: str
    timestamp_sent: str
    message_type: str
    protocol_version: str
    payload: Dict[str, Any]
    correlation_id: Optional[str]

class MCPCommandRequest(TypedDict):
    command_name: str
    parameters: Dict[str, Any]

class MCPCommandResponse(TypedDict):
    request_id: str
    status: Literal["success", "failure", "in_progress"]
    payload: Optional[Any]
    error_message: Optional[str]