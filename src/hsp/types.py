from typing import Optional, List, Dict, Any, Literal, Union # Added Union back
from typing_extensions import TypedDict # Import TypedDict from typing_extensions
from typing_extensions import Required, NotRequired # For Required/NotRequired fields in TypedDict

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

# Let's use `total=False` for payloads where many fields are optional, and `total=True` (default) for envelope parts that are mostly required.

class HSPFactStatementStructured(TypedDict, total=False):
    subject_uri: str # Required if this structure is used
    predicate_uri: str # Required if this structure is used
    object_literal: Any
    object_uri: str
    object_datatype: str

class HSPOriginalSourceInfo(TypedDict, total=False):
    type: str # Required if this structure is used, e.g., "url", "document_id"
    identifier: str # Required if this structure is used

class HSPFactPayload(TypedDict, total=False):
    id: str  # UUID, considered required for a fact instance
    statement_type: Literal["natural_language", "semantic_triple", "json_ld"] # Required
    statement_nl: str
    statement_structured: HSPFactStatementStructured | Dict[str, Any] # Dict for json_ld
    source_ai_id: str # DID or URI, Required
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
    encryption_details: Any # Placeholder

class HSPQoSParameters(TypedDict, total=False):
    priority: Literal["low", "medium", "high"]
    requires_ack: bool
    time_to_live_sec: int

class HSPRoutingInfo(TypedDict, total=False):
    hops: List[str]
    final_destination_ai_id: str

class HSPMessageEnvelope(TypedDict): # total=True by default, all keys are required
    hsp_envelope_version: str
    message_id: str  # UUID
    correlation_id: Optional[str]  # UUID
    sender_ai_id: str  # DID or URI
    recipient_ai_id: str  # DID, URI, or Topic URI
    timestamp_sent: str  # ISO 8601 UTC
    message_type: str  # e.g., "HSP::Fact_v0.1"
    protocol_version: str # HSP specification version
    communication_pattern: Literal[
        "publish", "request", "response",
        "stream_data", "stream_ack",
        "acknowledgement", "negative_acknowledgement"
    ]
    security_parameters: Optional[HSPSecurityParameters]
    qos_parameters: Optional[HSPQoSParameters]
    routing_info: Optional[HSPRoutingInfo]
    payload_schema_uri: Optional[str]
    payload: Dict[str, Any] # Generic payload, specific types like HSPFactPayload for actual data

# Example of a more specific envelope if needed, though payload typing is usually sufficient
# class HSPFactMessage(HSPMessageEnvelope):
#     payload: HSPFactPayload
# This helps if you want to type hint the entire message including a specific payload.

# Other payload types from HSP_SPECIFICATION.md would be defined here similarly:
# HSPBeliefPayload, HSPCapabilityAdvertisementPayload, HSPTaskRequestPayload, etc.
# For now, HSPFactPayload is the primary one for Step 1.2.

class HSPBeliefPayload(HSPFactPayload, total=False): # Inherits from HSPFactPayload, most fields are similar
    belief_holder_ai_id: str # Required, defaults to source_ai_id if not specified by sender
    justification_type: Optional[Literal["text", "inference_chain_id", "evidence_ids_list"]]
    justification: Optional[str | List[str]] # Text, or ID, or list of IDs

class HSPCapabilityAdvertisementPayload(TypedDict, total=False):
    capability_id: str # Required, unique ID for this capability offering
    ai_id: str # Required, DID or URI of the AI offering
    name: str # Required, human-readable name
    description: str # Required
    version: str # Required
    input_schema_uri: Optional[str]
    input_schema_example: Optional[Dict[str, Any]]
    output_schema_uri: Optional[str]
    output_schema_example: Optional[Dict[str, Any]]
    data_format_preferences: Optional[List[str]] # e.g., ["application/json", "image/jpeg", "text/plain"]
    hsp_protocol_requirements: Optional[Dict[str, Any]] # e.g., {"requires_streaming_input": True}
    cost_estimate_template: Optional[Dict[str, Any]]
    availability_status: Required[Literal["online", "offline", "degraded", "maintenance"]]
    access_policy_id: Optional[str]
    tags: Optional[List[str]]

class HSPTaskRequestPayload(TypedDict, total=False):
    request_id: str # Required, UUID
    requester_ai_id: str # Required, DID or URI
    target_ai_id: Optional[str] # DID or URI
    capability_id_filter: Optional[str]
    capability_name_filter: Optional[str] # Alternative to id_filter
    parameters: Required[Dict[str, Any]] # Input parameters for the capability
    requested_output_data_format: Optional[str] # Requester can hint preferred output format
    priority: Optional[int] # e.g., 1-10
    deadline_timestamp: Optional[str] # ISO 8601 UTC
    callback_address: Optional[str] # URI/topic where TaskResult should be sent

class HSPErrorDetails(TypedDict, total=False):
    error_code: Required[str]
    error_message: Required[str]
    error_context: Optional[Dict[str, Any]]

class HSPTaskResultPayload(TypedDict, total=False):
    result_id: str # Required, UUID
    request_id: str # Required, UUID of the TaskRequest
    executing_ai_id: str # Required, DID or URI
    status: Required[Literal["success", "failure", "in_progress", "queued", "rejected"]]
    payload: Optional[Dict[str, Any]] # The actual result data if status is "success"
    output_data_format: Optional[str] # Confirms the format of the payload, e.g., "application/json", "image/png"
    error_details: Optional[HSPErrorDetails] # If status is "failure" or "rejected"
    timestamp_completed: Optional[str] # ISO 8601 UTC
    execution_metadata: Optional[Dict[str, Any]] # e.g., {"time_taken_ms": 150}

class HSPEnvironmentalStatePayload(TypedDict, total=False): # Also known as ContextUpdate
    update_id: str # Required, UUID
    source_ai_id: str # Required, DID or URI
    phenomenon_type: str # Required, URI/namespaced string (e.g., "hsp:event:UserMoodShift")
    parameters: Required[Dict[str, Any]] # Specifics of the state/context
    timestamp_observed: str # Required, ISO 8601 UTC
    scope_type: Optional[Literal["global", "session", "project", "custom_group"]]
    scope_id: Optional[str] # Identifier for the scope
    relevance_decay_rate: Optional[float]

# Placeholder for Acknowledgement/NegativeAcknowledgement payloads if they need specific structure beyond a simple status
class HSPAcknowledgementPayload(TypedDict):
    status: Literal["received", "processed"] # Example statuses
    ack_timestamp: str # ISO 8601 UTC
    target_message_id: str # ID of the message being acknowledged

class HSPNegativeAcknowledgementPayload(TypedDict):
    status: Literal["error", "rejected", "validation_failed"] # Example statuses
    nack_timestamp: str # ISO 8601 UTC
    target_message_id: str # ID of the message being NACKed
    error_details: HSPErrorDetails
