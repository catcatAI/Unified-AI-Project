"""
MCP (Model Context Protocol) Type Definitions for Unified AI Project.
This module provides type definitions for the Model Context Protocol integration,
with Context7 and other MCP-compatible services.
"""

from typing import Any, Dict, Optional, TypedDict, Literal, List
import logging
logger = logging.getLogger(__name__)

# Original MCP Types (Legacy)
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

# Context7 MCP Types (Enhanced)
class MCPMessage(TypedDict):
    """Enhanced MCP message format for Context7 integration."""
    type: str
    session_id: Optional[str]
    payload: Dict[str, Any]
    timestamp: Optional[str]
    priority: Optional[int]

class MCPResponse(TypedDict):
    """Enhanced MCP response format."""
    success: bool
    message_id: str
    data: Dict[str, Any]
    error: Optional[str]
    timestamp: Optional[str]

class MCPCapability(TypedDict):
    """MCP capability definition."""
    name: str
    version: str
    description: Optional[str]
    parameters: Optional[Dict[str, Any]]

class MCPContextItem(TypedDict):
    """Context item for MCP communication."""
    id: str
    content: Any
    context_type: str
    relevance_score: Optional[float]
    metadata: Optional[Dict[str, Any]]

class MCPCollaborationRequest(TypedDict):
    """Collaboration request between AI models."""
    source_model: str
    target_model: str
    task_description: str
    shared_context: Dict[str, Any]
    collaboration_mode: Literal["sync", "async"]
    timeout: Optional[int]