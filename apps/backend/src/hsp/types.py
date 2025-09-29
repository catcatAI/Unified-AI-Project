# HSP Types Definition

from typing import Optional, List, Dict, Any, Literal
from typing_extensions import TypedDict, Required

# Let's use `total=False` for payloads where many fields are optional, and `total=True` (default) for envelope parts that are mostly required.

class HSPMessage(TypedDict, total=False):
    payload: Dict[str, Any]
    message_type: str
    sender_ai_id: str
    recipient_ai_id: str
    timestamp_sent: str
    correlation_id: Optional[str]

class HSPFactStatementStructured(TypedDict, total=False):
    subject_uri: str  # Required if this structure is used
    predicate_uri: str  # Required if this structure is used
    object_literal: Any
    object_uri: str
    object_datatype: str

class HSPOriginalSourceInfo(TypedDict, total=False):
    type: str  # Required if this structure is used, e.g., "url", "document_id"
    identifier: str  # Required if this structure is used

class HSPFactPayload(TypedDict, total=False):
    id: str  # UUID, considered required for a fact instance
    statement_type: Literal["natural_language", "semantic_triple", "json_ld"]  # Required
    statement_nl: str
    statement_structured: Dict[str, Any]  # Dict for json_ld
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
    encryption_details: Any  # Placeholder

class HSPQoSParameters(TypedDict, total=False):
    priority: Literal["low", "medium", "high"]
    requires_ack: bool
    time_to_live_sec: int

class HSPRoutingInfo(TypedDict, total=False):
    hops: List[str]
    final_destination_ai_id: str

class HSPMessageEnvelope(TypedDict):  # total=True by default, all keys are required
    hsp_envelope_version: str
    message_id: str  # UUID
    correlation_id: Optional[str]  # UUID
    sender_ai_id: str  # DID or URI
    recipient_ai_id: str  # DID, URI, or Topic URI
    timestamp_sent: str  # ISO 8601 UTC
    message_type: str  # e.g., "HSP::Fact_v0.1"
    protocol_version: str  # HSP specification version
    communication_pattern: Literal[
        "publish", "request", "response",
        "stream_data", "stream_ack",
        "acknowledgement", "negative_acknowledgement",
        "broadcast", "multicast", "unicast",
        "notification", "event", "command",
        "query", "reply"
    ]
    security_parameters: Optional[HSPSecurityParameters]
    qos_parameters: Optional[HSPQoSParameters]
    routing_info: Optional[HSPRoutingInfo]
    payload_schema_uri: Optional[str]
    payload: Dict[str, Any]  # Generic payload, specific types like HSPFactPayload for actual data

class HSPBeliefPayload(HSPFactPayload, total=False):  # Inherits from HSPFactPayload, most fields are similar
    belief_holder_ai_id: str  # Required, defaults to source_ai_id if not specified by sender
    justification_type: Optional[Literal["text", "inference_chain_id", "evidence_ids_list"]]
    justification: Optional[str]  # Text, or ID, or list of IDs

class HSPCapabilityAdvertisementPayload(TypedDict, total=False):
    capability_id: str  # Required, unique ID for this capability offering
    ai_id: str  # Required, DID or URI of the AI offering
    agent_name: Optional[str]  # The name of the agent script, e.g., 'data_analysis_agent'
    name: str  # Required, human-readable name
    description: str  # Required
    version: str  # Required
    input_schema_uri: Optional[str]
    input_schema_example: Optional[Dict[str, Any]]
    output_schema_uri: Optional[str]
    output_schema_example: Optional[Dict[str, Any]]
    data_format_preferences: Optional[List[str]]  # e.g., ["application/json", "image/jpeg", "text/plain"]
    hsp_protocol_requirements: Optional[Dict[str, Any]]  # e.g., {"requires_streaming_input": True}
    cost_estimate_template: Optional[Dict[str, Any]]
    availability_status: Required[Literal["online", "offline", "degraded", "maintenance"]]
    access_policy_id: Optional[str]
    tags: Optional[List[str]]

class HSPTaskRequestPayload(TypedDict, total=False):
    request_id: str  # Required, UUID
    requester_ai_id: str  # Required, DID or URI
    target_ai_id: Optional[str]  # DID or URI
    capability_id_filter: Optional[str]
    capability_name_filter: Optional[str]  # Alternative to id_filter
    parameters: Required[Dict[str, Any]]  # Input parameters for the capability
    requested_output_data_format: Optional[str]  # Requester can hint preferred output format
    priority: Optional[int]  # e.g., 1-10
    deadline_timestamp: Optional[str]  # ISO 8601 UTC
    callback_address: Optional[str]  # URI/topic where TaskResult should be sent

class HSPErrorDetails(TypedDict, total=False):
    error_code: Required[str]
    error_message: Required[str]
    error_context: Optional[Dict[str, Any]]

class HSPTaskResultPayload(TypedDict, total=False):
    result_id: str  # Required, UUID
    request_id: str  # Required, UUID of the TaskRequest
    executing_ai_id: str  # Required, DID or URI
    status: Required[Literal["success", "failure", "in_progress", "queued", "rejected"]]
    payload: Optional[Dict[str, Any]]  # The actual result data if status is "success"
    output_data_format: Optional[str]  # Confirms the format of the payload, e.g., "application/json", "image/png"
    error_details: Optional[HSPErrorDetails]  # If status is "failure" or "rejected"
    timestamp_completed: Optional[str]  # ISO 8601 UTC
    execution_metadata: Optional[Dict[str, Any]]  # e.g., {"time_taken_ms": 150}

class HSPTask(TypedDict, total=False):
    task_id: str
    capability: str
    parameters: Dict[str, Any]
    requester_id: str
    priority: Optional[int]
    timeout: Optional[int]

class HSPEnvironmentalStatePayload(TypedDict, total=False):  # Also known as ContextUpdate
    update_id: str  # Required, UUID
    source_ai_id: str  # Required, DID or URI
    phenomenon_type: str  # Required, URI/namespaced string (e.g., "hsp:event:UserMoodShift")
    parameters: Required[Dict[str, Any]]  # Specifics of the state/context
    timestamp_observed: str  # Required, ISO 8601 UTC
    scope_type: Optional[Literal["global", "session", "project", "custom_group"]]
    scope_id: Optional[str]  # Identifier for the scope
    relevance_decay_rate: Optional[float]

class HSPAcknowledgementPayload(TypedDict):
    status: Literal["received", "processed"]  # Example statuses
    ack_timestamp: str  # ISO 8601 UTC
    target_message_id: str  # ID of the message being acknowledged

class HSPNegativeAcknowledgementPayload(TypedDict):
    status: Literal["error", "rejected", "validation_failed"]  # Example statuses
    nack_timestamp: str  # ISO 8601 UTC
    target_message_id: str  # ID of the message being NACKed
    error_details: HSPErrorDetails

class HSPEventPayload(TypedDict, total=False):
    event_id: str  # Required, UUID
    event_type: str  # Required, namespaced string (e.g., "hsp:event:SystemShutdown")
    source_ai_id: str  # Required, DID or URI
    timestamp_occurred: str  # Required, ISO 8601 UTC
    payload: Optional[Dict[str, Any]]  # Event-specific data
    severity: Optional[Literal["info", "warning", "error", "critical"]]
    tags: Optional[List[str]]

class HSPCommandPayload(TypedDict, total=False):
    command_id: str  # Required, UUID
    command_type: str  # Required, namespaced string (e.g., "hsp:command:RestartService")
    target_ai_id: Optional[str]  # DID or URI of target AI
    requester_ai_id: str  # Required, DID or URI of requester
    parameters: Optional[Dict[str, Any]]  # Command-specific parameters
    timestamp_issued: str  # Required, ISO 8601 UTC
    deadline_timestamp: Optional[str]  # ISO 8601 UTC
    priority: Optional[int]  # e.g., 1-10

class HSPNotificationPayload(TypedDict, total=False):
    notification_id: str  # Required, UUID
    notification_type: str  # Required, namespaced string (e.g., "hsp:notification:TaskCompleted")
    source_ai_id: str  # Required, DID or URI
    target_ai_id: Optional[str]  # DID or URI of target AI (None for broadcast)
    timestamp_sent: str  # Required, ISO 8601 UTC
    title: str  # Required, brief title
    content: str  # Required, detailed content
    priority: Optional[Literal["low", "normal", "high", "urgent"]]
    actions: Optional[List[Dict[str, Any]]]  # Possible actions the recipient can take
    metadata: Optional[Dict[str, Any]]  # Additional metadata

class HSPOpinionPayload(TypedDict, total=False):
    id: str
    statement_type: Literal["natural_language", "semantic_triple", "json_ld"]
    statement_nl: str
    source_ai_id: str
    timestamp_created: str
    confidence_score: float
    reasoning_chain: Optional[List[str]]
    tags: Optional[List[str]]