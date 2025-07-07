# src/shared/types/common_types.py
from enum import Enum
from typing import TypedDict, Optional, List, Any, Dict, Literal, Union, Callable # Added Literal, Union, Callable back for other types
from typing_extensions import Required

print("common_types.py (debug version) is being imported and defining ServiceStatus...")

class ServiceStatus(Enum):
    UNKNOWN = 0
    STARTING = 1
    HEALTHY = 2
    UNHEALTHY = 3
    STOPPING = 4
    STOPPED = 5
    DEGRADED = 6

class ServiceType(Enum):
    UNKNOWN = "unknown"
    CORE_AI_COMPONENT = "core_ai_component"
    EXTERNAL_API = "external_api"
    DATA_STORE = "data_store"
    INTERNAL_TOOL = "internal_tool"
    HSP_NODE = "hsp_node"

class ServiceAdvertisement(TypedDict):
    service_id: str
    service_name: str
    service_type: ServiceType
    service_version: str
    endpoint_url: Optional[str]
    metadata: Dict[str, Any]
    status: ServiceStatus
    last_seen_timestamp: float
    ttl: int

class ServiceQuery(TypedDict, total=False):
    service_type: Optional[ServiceType]
    service_name: Optional[str]
    min_version: Optional[str]
    required_capabilities: Optional[List[str]]
    status_filter: Optional[List[ServiceStatus]]

class ServiceInstanceHealth(TypedDict):
    service_id: str
    instance_id: str
    status: ServiceStatus
    last_heartbeat: float
    metrics: Optional[Dict[str, Any]]

# --- Minimal other types that might be needed immediately downstream ---
# For ToolDispatcherResponse as used by ToolDispatcher, imported by DialogueManager
class ToolDispatcherResponse(TypedDict):
    status: Literal[
        "success",
        "failure_tool_not_found",
        "failure_tool_error",
        "failure_parsing_query",
        "error_dispatcher_issue",
        "unhandled_by_local_tool"
    ]
    payload: Optional[Any]
    tool_name_attempted: Optional[str]
    original_query_for_tool: Optional[str]
    error_message: Optional[str]

class LLMConfig(TypedDict): # For ToolDispatcher
    model_name: str
    api_key: Optional[str]
    base_url: Optional[str]
    temperature: float
    max_tokens: int

class DialogueTurn(TypedDict): # For DialogueManager
    speaker: Literal["user", "ai", "system"]
    text: str
    timestamp: str
    metadata: Optional[Dict[str, Any]]

class PendingHSPTaskInfo(TypedDict): # For DialogueManager
    user_id: Optional[str]
    session_id: Optional[str]
    original_query_text: str
    request_timestamp: str
    capability_id: str
    target_ai_id: str
    expected_callback_topic: str
    request_type: str

class OperationalConfig(TypedDict, total=False): # For DialogueManager
    timeouts: Optional[Any]
    learning_thresholds: Optional[Any]
    default_hsp_fact_topic: Optional[str]
    max_dialogue_history: Optional[int]
    operational_configs: Optional[Dict[str,Any]]

class CritiqueResult(TypedDict): # For DialogueMemoryEntryMetadata
    score: float
    reason: Optional[str]
    suggested_alternative: Optional[str]

class DialogueMemoryEntryMetadata(TypedDict): # For DialogueManager
    speaker: str
    timestamp: str
    user_input_ref: Optional[str]
    sha256_checksum: Optional[str]
    critique: Optional[CritiqueResult]
    user_feedback_explicit: Optional[str]
    learning_weight: Optional[float]

class ParsedToolIODetails(TypedDict, total=False): # For DialogueManager
    suggested_method_name: Required[str]
    class_docstring_hint: Required[str]
    method_docstring_hint: Required[str]
    parameters: Required[List[Dict[str, Any]]]# Simplified from ToolParameterDetail for this test
    return_type: Required[str]
    return_description: Required[str]

class OverwriteDecision(Enum): # For HAMMemoryManager -> DialogueManager
    PREVENT_OVERWRITE = "prevent_overwrite"
    OVERWRITE_EXISTING = "overwrite_existing"
    ASK_USER = "ask_user"
    MERGE_IF_APPLICABLE = "merge_if_applicable"

class SimulatedResourceConfig(TypedDict): # For HAMMemoryManager -> DialogueManager
    name: str
    current_level: float
    capacity: float
    lag_factor_at_max: float
    failure_threshold: Optional[float]

# LIS types - keeping minimal but ensuring what HAMLISCache might need is present
LIS_AnomalyType = Literal["RHYTHM_BREAK", "LOW_DIVERSITY", "UNEXPECTED_TONE_SHIFT"] # Simplified
LIS_SeverityScore = float
LIS_InterventionOutcome = Literal["SUCCESS", "FAILURE"] # Simplified

class LIS_SemanticAnomalyDetectedEvent(TypedDict):
    anomaly_type: LIS_AnomalyType
    severity: LIS_SeverityScore
    # ... other fields if absolutely necessary for import

class LIS_InterventionReport(TypedDict):
    outcome: LIS_InterventionOutcome
    # ...

class LIS_IncidentRecord(TypedDict):
    incident_id: str
    anomaly_event: LIS_SemanticAnomalyDetectedEvent # This was missing in a previous version of this minimal file
    intervention_reports: Optional[List[LIS_InterventionReport]]
    # ...

class NarrativeAntibodyObject(TypedDict): # Renamed from LIS_AntibodyObject
    antibody_id: str
    # ...

# Virtual Input types - minimal for AIVirtualInputService -> DialogueManager
class VirtualInputElementDescription(TypedDict, total=False):
    element_id: Required[str]
    element_type: Required[str]

print("common_types.py (debug version) finished definitions.")
