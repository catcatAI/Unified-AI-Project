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
class VirtualInputElementDescription(TypedDict, total=False): # Revised
    element_id: Required[str]
    element_type: Required[str] # e.g., "button", "text_field", "checkbox", "link", "container"
    label: Optional[str]      # Visible text or aria-label
    value: Optional[str]      # For input fields, textareas
    is_focused: Optional[bool]
    is_enabled: Optional[bool]
    is_visible: Optional[bool]
    attributes: Optional[Dict[str, Any]] # Other relevant HTML attributes
    children: Optional[List['VirtualInputElementDescription']] # For nested structure

VirtualInputPermissionLevel = Literal[
    "simulation_only",
    "requires_user_confirmation", # Future use
    "full_control_trusted"        # Future use
]

VirtualMouseEventType = Literal[
    "move_relative_to_window", "move_to_element", "click", "double_click",
    "right_click", "hover", "drag_start", "drag_end", "scroll"
]

class VirtualMouseCommand(TypedDict, total=False):
    action_type: Required[VirtualMouseEventType]
    target_element_id: Optional[str]
    relative_x: Optional[float]
    relative_y: Optional[float]
    click_type: Optional[Literal["left", "right", "middle"]]
    scroll_direction: Optional[Literal["up", "down", "left", "right"]]
    scroll_amount_ratio: Optional[float]
    scroll_pages: Optional[int]
    drag_target_element_id: Optional[str]
    drag_target_x: Optional[float]
    drag_target_y: Optional[float]

VirtualKeyboardActionType = Literal[
    "type_string", "press_keys", "release_keys", "special_key"
]

class VirtualKeyboardCommand(TypedDict, total=False):
    action_type: Required[VirtualKeyboardActionType]
    target_element_id: Optional[str]
    text_to_type: Optional[str]
    keys: Optional[List[str]]


# --- HAM (Hierarchical Associative Memory) Types ---
class HAMDataPackageInternal(TypedDict):
    timestamp: str  # ISO 8601 UTC string
    data_type: str
    encrypted_package: bytes # The actual encrypted data
    metadata: Dict[str, Any]

class HAMRecallResult(TypedDict):
    id: str # Memory ID
    timestamp: str # ISO 8601 UTC string of original storage
    data_type: str
    rehydrated_gist: Any # Could be str for text, or other types
    metadata: Dict[str, Any]

# Potentially other HAM related types if needed by other modules

# --- LLM Interface Types ---
class LLMProviderOllamaConfig(TypedDict):
    base_url: Required[str]
    # Potentially other Ollama specific params like default_keep_alive, etc.

class LLMProviderOpenAIConfig(TypedDict):
    api_key: Required[str]
    # Potentially other OpenAI specific params like organization, project_id

class LLMModelInfo(TypedDict, total=False):
    id: Required[str]           # Model ID, typically how it's called/identified
    provider: Required[str]     # e.g., "ollama", "openai", "mock"
    name: Optional[str]         # Human-readable name, might be same as ID or more descriptive
    description: Optional[str]
    modified_at: Optional[str]  # ISO 8601 timestamp
    size_bytes: Optional[int]
    # Future: capabilities (e.g., ["chat", "completion", "embedding"]), context_length, etc.



# --- Knowledge Graph Types (for ContentAnalyzerModule) ---
class KGEntityAttributes(TypedDict, total=False):
    start_char: int
    end_char: int
    is_conceptual: bool
    source_text: str
    rule_added: str
    # Other attributes can be added as needed

class KGEntity(TypedDict):
    id: Required[str]
    label: Required[str]
    type: Required[str] # e.g., "ORG", "PERSON", "GPE", "LOC", "CONCEPT", etc.
    attributes: KGEntityAttributes
    # Optional: description: Optional[str], confidence: Optional[float]

class KGRelationshipAttributes(TypedDict, total=False):
    pattern: str # Name of the pattern or rule that extracted this
    trigger_token: Optional[str]
    trigger_text: Optional[str]
    # Optional: confidence: Optional[float], sentence_id: Optional[int]

class KGRelationship(TypedDict):
    source_id: Required[str] # ID of the source KGEntity
    target_id: Required[str] # ID of the target KGEntity
    type: Required[str]      # Type of the relationship (e.g., "is_a", "works_for", verb_lemma)
    weight: Optional[float]  # Or confidence score
    attributes: KGRelationshipAttributes

class KnowledgeGraphMetadata(TypedDict):
    source_text_length: Required[int]
    processed_with_model: Required[str]
    entity_count: Required[int]
    relationship_count: Required[int]
    # Optional: processing_time_ms: Optional[float], source_document_id: Optional[str]

class KnowledgeGraph(TypedDict):
    entities: Required[Dict[str, KGEntity]]
    relationships: Required[List[KGRelationship]]
    metadata: Required[KnowledgeGraphMetadata]

# --- Simulated Resource Types (for ResourceAwarenessService) ---
class SimulatedDiskConfig(TypedDict):
    space_gb: Required[float]
    warning_threshold_percent: Required[Union[int, float]]
    critical_threshold_percent: Required[Union[int, float]]
    lag_factor_warning: Required[float]
    lag_factor_critical: Required[float]

class SimulatedCPUConfig(TypedDict):
    cores: Required[int]
    # Optional: base_clock_ghz: float, current_load_percent: float, lag_factor_high_load: float

class SimulatedRAMConfig(TypedDict):
    ram_gb: Required[float]
    # Optional: current_usage_gb: float, lag_factor_high_usage: float

class SimulatedHardwareProfile(TypedDict):
    profile_name: Required[str]
    disk: Required[SimulatedDiskConfig]
    cpu: Required[SimulatedCPUConfig]
    ram: Required[SimulatedRAMConfig]
    gpu_available: Required[bool]
    # Optional: gpu_name: Optional[str], gpu_vram_gb: Optional[float], network_bandwidth_mbps: Optional[float]

class SimulatedResourcesRoot(TypedDict): # For the root of the YAML config file
    simulated_hardware_profile: Required[SimulatedHardwareProfile]

# --- Fact Extractor Types ---
class UserPreferenceContent(TypedDict, total=False):
    category: Required[str]
    preference: Required[str]
    liked: Optional[bool]

class UserStatementContent(TypedDict, total=False):
    attribute: Required[str]
    value: Required[Any]

ExtractedFactContent = Union[UserPreferenceContent, UserStatementContent, Dict[str, Any]]

class ExtractedFact(TypedDict):
    fact_type: Required[str]
    content: Required[ExtractedFactContent]
    confidence: Required[float]

# --- Formula Engine Types ---
class FormulaConfigEntry(TypedDict, total=False):
    name: Required[str]
    conditions: Required[List[str]]
    action: Required[str]
    description: Optional[str]
    parameters: Optional[Dict[str, Any]]
    priority: Optional[int]
    enabled: Optional[bool]
    version: Optional[str]
    # Other potential fields: id, tags, scope, etc.

# --- Learning Manager Types ---
class LearnedFactRecord(TypedDict, total=False):
    # Core fields
    record_id: Required[str]
    timestamp: Required[str]        # ISO 8601, when this HAM record was created
    fact_type: Required[str]
    confidence: Required[float]
    source_text: Optional[str]

    # Context from user interaction
    user_id: Optional[str]
    session_id: Optional[str]
    source_interaction_ref: Optional[str]

    # HSP specific fields
    hsp_originator_ai_id: Optional[str]
    hsp_sender_ai_id: Optional[str]
    hsp_fact_id: Optional[str]
    hsp_fact_timestamp_created: Optional[str]

    # Conflict resolution metadata
    resolution_strategy: Optional[str]
    supersedes_ham_records: Optional[List[str]]
    superseded_reason: Optional[str]
    conflicts_with_ham_records: Optional[List[str]]
    conflicting_values: Optional[List[str]]
    merged_from_ham_records: Optional[List[str]]
    original_values: Optional[List[Any]]
    merged_value: Optional[Any]
    merged_confidence: Optional[float]

    # Semantic identifiers from ContentAnalyzer
    hsp_semantic_subject: Optional[str]
    hsp_semantic_predicate: Optional[str]
    hsp_semantic_object: Optional[Any]
    ca_subject_id: Optional[str]
    ca_predicate_type: Optional[str]
    ca_object_id: Optional[str]


print("common_types.py (debug version) finished definitions.")
