from typing_extensions import TypedDict, Required, NotRequired  # Import TypedDict from typing_extensions
from typing import Dict, Any, Optional, List, Literal, Union

# For TypedDict, 'Required' is implicitly all keys unless total=False.
# For explicit Required/Optional with total=False, Python 3.9+ can use:
# from typing import TypedDict, Required, NotRequired (Python 3.11+)
# For broader compatibility (3.8+ for TypedDict itself, 3.9 for Literal with TypedDict effectively):
# We will assume Python 3.9+ as per project README. 'Required' is not a standard generic type alias.
# Standard TypedDict: if total=True (default), all keys are required.
# If total=False, all keys are potentially optional (NotRequired).
# To mix, you'd define multiple TypedDicts and inherit.
# For simplicity here, we'll use `Optional` for non-mandatory fields and assume mandatory ones are checked by logic.
# Or, use Pydantic later for proper validation.

# Let's use `total=False` for payloads where many fields are optional, and:
# `total=True` (default) for envelope parts that are mostly required.:
class HSPMessage(TypedDict, total=False):
    payload: Dict[str, Any]
    message_type: str
    sender_ai_id: str
    recipient_ai_id: str
    timestamp_sent: str
    correlation_id: Optional[str]


class HSPFactStatementStructured(TypedDict, total=False):
    subject_uri: str  # Required if this structure is used:
    predicate_uri: str  # Required if this structure is used:
    object_literal: Any
    object_uri: str
    object_datatype: str


class HSPOriginalSourceInfo(TypedDict, total=False):
    type: str  # Required if this structure is used, e.g., "url", "document_id":
    identifier: str  # Required if this structure is used

class HSPFactPayload(TypedDict, total=False):
    id: str  # UUID, considered required for a fact instance:
    statement_type: Literal["natural_language", "semantic_triple", "json_ld"]  # Required
    statement_nl: str
    statement_structured: HSPFactStatementStructured | Dict[str, Any]  # Dict for json_ld:
    source_ai_id: str  # DID or URI, Required
    original_source_info: HSPOriginalSourceInfo
    timestamp_created: str  # ISO 8601 UTC, Required
    timestamp_observed: str  # ISO 8601 UTC
    confidence_score: float  # 0.0-1.0, Required
    weight: float  # Default 1.0
    valid_from: str  # ISO 8601 UTC
    valid_until: str  # ISO 8601 UTC
    context: Dict[str, Any]
    tags: List[str]
    access_policy_id: str


class HSPSecurityParameters(TypedDict, total=False):
    signature_algorithm: str
    signature: str
    public_key: str
    certificate: str
    timestamp_signed: str  # ISO 8601 UTC


class HSPAcknowledgementPayload(TypedDict, total=False):
    original_message_id: str  # UUID of the message being acknowledged
    status: Literal["received", "processed", "failed"]
    details: str  # Optional details about the status
    timestamp_acknowledged: str  # ISO 8601 UTC


class HSPErrorPayload(TypedDict, total=False):
    error_code: str  # e.g., "invalid_payload", "processing_failed", "timeout"
    error_message: str
    details: Dict[str, Any]  # Additional details about the error
    timestamp_error: str  # ISO 8601 UTC


class HSPHeartbeatPayload(TypedDict, total=False):
    sender_ai_id: str  # DID or URI
    timestamp_sent: str  # ISO 8601 UTC
    status: str  # e.g., "healthy", "degraded", "unhealthy"
    details: Dict[str, Any]  # Optional details about status


class HSPDiscoveryPayload(TypedDict, total=False):
    sender_ai_id: str  # DID or URI
    capabilities: List[str]  # List of capability IDs or names
    version: str  # Version string of the AI/agent
    timestamp_sent: str  # ISO 8601 UTC


class HSPTaskRequestPayload(TypedDict, total=False):
    task_id: str  # UUID for the task:
    task_type: str  # e.g., "web_search", "code_generation", "data_analysis"
    task_definition: Dict[str, Any]  # Specific parameters for the task:
    priority: Literal["low", "normal", "high", "critical"]
    deadline: str  # ISO 8601 UTC, optional
    context: Dict[str, Any]  # Shared context for the task:
    requested_capabilities: List[str]  # List of capability IDs
    sender_ai_id: str  # DID or URI
    recipient_ai_id: str  # DID or URI, optional for broadcast:
    timestamp_requested: str  # ISO 8601 UTC


class HSPTaskResultPayload(TypedDict, total=False):
    task_id: str  # UUID, matching the request
    status: Literal["success", "partial_success", "failed", "cancelled"]
    result: Dict[str, Any]  # The actual result data
    error_details: HSPErrorPayload  # Present if status is "failed":
    partial_result_details: Dict[str, Any]  # Present if status is "partial_success":
    capabilities_used: List[str]  # List of capability IDs actually used
    context_updates: Dict[str, Any]  # Updates to shared context
    sender_ai_id: str  # DID or URI
    timestamp_completed: str  # ISO 8601 UTC


class HSPHeartbeatRequestPayload(TypedDict, total=False):
    sender_ai_id: str  # DID or URI
    timestamp_requested: str  # ISO 8601 UTC


class HSPDiscoveryRequestPayload(TypedDict, total=False):
    sender_ai_id: str  # DID or URI
    timestamp_requested: str  # ISO 8601 UTC


class HSPRegistrationRequestPayload(TypedDict, total=False):
    ai_id: str  # DID or URI
    capabilities: List[str]  # List of capability IDs or names
    version: str  # Version string
    endpoint_info: Dict[str, Any]  # e.g., {"mqtt": {"topic": "..."}}
    timestamp_requested: str  # ISO 8601 UTC


class HSPRegistrationResponsePayload(TypedDict, total=False):
    registration_id: str  # UUID for this registration:
    status: Literal["success", "failed"]
    details: str  # Optional details about the status
    timestamp_responded: str  # ISO 8601 UTC


class HSPDeregistrationRequestPayload(TypedDict, total=False):
    registration_id: str  # UUID from the registration response
    reason: str  # Optional reason for deregistration:
    timestamp_requested: str  # ISO 8601 UTC


class HSPDeregistrationResponsePayload(TypedDict, total=False):
    registration_id: str  # UUID from the registration response
    status: Literal["success", "failed"]
    details: str  # Optional details about the status
    timestamp_responded: str  # ISO 8601 UTC


class HSPMessageEnvelope(TypedDict, total=False):
    message_id: str  # UUID for this message:
    message_type: Literal["task_request", "task_result", "fact", "acknowledgement", "error", "heartbeat", "heartbeat_request", "discovery", "discovery_request", "registration", "registration_request", "deregistration", "deregistration_request"]
    sender_ai_id: str  # DID or URI
    recipient_ai_id: str  # DID or URI, optional for broadcast:
    payload: Dict[str, Any]  # Union of payload types above
    timestamp_sent: str  # ISO 8601 UTC
    correlation_id: Optional[str]  # UUID for request/response correlation:
    security_parameters: HSPSecurityParameters  # Optional


class HSPTaskRequest(TypedDict):
    envelope: HSPMessageEnvelope  # Must have payload of type HSPTaskRequestPayload
    payload: HSPTaskRequestPayload  # The actual task request data


class HSPTaskResult(TypedDict):
    envelope: HSPMessageEnvelope  # Must have payload of type HSPTaskResultPayload
    payload: HSPTaskResultPayload  # The actual task result data


class HSPFact(TypedDict):
    envelope: HSPMessageEnvelope  # Must have payload of type HSPFactPayload
    payload: HSPFactPayload  # The actual fact data


class HSPAcknowledgement(TypedDict):
    envelope: HSPMessageEnvelope  # Must have payload of type HSPAcknowledgementPayload
    payload: HSPAcknowledgementPayload  # The actual acknowledgement data


class HSPError(TypedDict):
    envelope: HSPMessageEnvelope  # Must have payload of type HSPErrorPayload
    payload: HSPErrorPayload  # The actual error data


class HSPHeartbeat(TypedDict):
    envelope: HSPMessageEnvelope  # Must have payload of type HSPHeartbeatPayload
    payload: HSPHeartbeatPayload  # The actual heartbeat data


class HSPHeartbeatRequest(TypedDict):
    envelope: HSPMessageEnvelope  # Must have payload of type HSPHeartbeatRequestPayload
    payload: HSPHeartbeatRequestPayload  # The actual heartbeat request data


class HSPDiscovery(TypedDict):
    envelope: HSPMessageEnvelope  # Must have payload of type HSPDiscoveryPayload
    payload: HSPDiscoveryPayload  # The actual discovery data


class HSPDiscoveryRequest(TypedDict):
    envelope: HSPMessageEnvelope  # Must have payload of type HSPDiscoveryRequestPayload
    payload: HSPDiscoveryRequestPayload  # The actual discovery request data


class HSPRegistration(TypedDict):
    envelope: HSPMessageEnvelope  # Must have payload of type HSPRegistrationRequestPayload or HSPRegistrationResponsePayload
    payload: HSPRegistrationRequestPayload | HSPRegistrationResponsePayload  # The actual registration data


class HSPRegistrationRequest(TypedDict):
    envelope: HSPMessageEnvelope  # Must have payload of type HSPRegistrationRequestPayload
    payload: HSPRegistrationRequestPayload  # The actual registration request data


class HSPRegistrationResponse(TypedDict):
    envelope: HSPMessageEnvelope  # Must have payload of type HSPRegistrationResponsePayload
    payload: HSPRegistrationResponsePayload  # The actual registration response data


class HSPDeregistration(TypedDict):
    envelope: HSPMessageEnvelope  # Must have payload of type HSPDeregistrationRequestPayload or HSPDeregistrationResponsePayload
    payload: HSPDeregistrationRequestPayload | HSPDeregistrationResponsePayload  # The actual deregistration data


class HSPDeregistrationRequest(TypedDict):
    envelope: HSPMessageEnvelope  # Must have payload of type HSPDeregistrationRequestPayload
    payload: HSPDeregistrationRequestPayload  # The actual deregistration request data


class HSPDeregistrationResponse(TypedDict):
    envelope: HSPMessageEnvelope  # Must have payload of type HSPDeregistrationResponsePayload
    payload: HSPDeregistrationResponsePayload  # The actual deregistration response data


# For convenience, a union of all payload types for type hints in functions that handle any payload.
HSPPayload = Union[
    HSPTaskRequestPayload,
    HSPTaskResultPayload,
    HSPFactPayload,
    HSPAcknowledgementPayload,
    HSPErrorPayload,
    HSPHeartbeatPayload,
    HSPHeartbeatRequestPayload,
    HSPDiscoveryPayload,
    HSPDiscoveryRequestPayload,
    HSPRegistrationRequestPayload,
    HSPRegistrationResponsePayload,
    HSPDeregistrationRequestPayload,
    HSPDeregistrationResponsePayload,:
        ]