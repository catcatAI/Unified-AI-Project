# src/shared/types/common_types.py
from enum import Enum
from typing import TypedDict, Optional, List, Any, Dict, Literal, Union, Callable, Tuple # Added Tuple
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

# --- Types for ResourceAwarenessService ---
class SimulatedDiskConfig(TypedDict, total=False):
    space_gb: Required[float]
    warning_threshold_percent: Required[float] # Percentage (0-100)
    critical_threshold_percent: Required[float] # Percentage (0-100)
    lag_factor_warning: float # Multiplier for perceived time lag
    lag_factor_critical: float # Multiplier for perceived time lag

class SimulatedCPUConfig(TypedDict, total=False):
    cores: Required[int]
    # Future: base_mhz, current_load_percent, lag_factor_high_load

class SimulatedRAMConfig(TypedDict, total=False):
    ram_gb: Required[float]
    # Future: warning_threshold_percent, critical_threshold_percent, lag_factor_warning, lag_factor_critical

class SimulatedHardwareProfile(TypedDict, total=False):
    profile_name: Required[str]
    disk: Required[SimulatedDiskConfig]
    cpu: Required[SimulatedCPUConfig]
    ram: Required[SimulatedRAMConfig]
    gpu_available: Required[bool]
    # Future: network_config: SimulatedNetworkConfig

class SimulatedResourcesRoot(TypedDict): # For the root of the YAML file
    simulated_hardware_profile: SimulatedHardwareProfile

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

# --- Virtual Input Types for AIVirtualInputService ---
VirtualInputPermissionLevel = Literal[
    "simulation_only",      # Default: Only simulate, no real input.
    "requires_approval",    # Future: Actions require user approval.
    "full_control_dangerous" # Future: AI has direct input control (use with extreme caution).
]

VirtualMouseEventType = Literal[
    "move_relative_to_window", # Moves cursor to (x_ratio, y_ratio) relative to abstract window (0-1, 0-1)
    "click",                   # Simulates a mouse click (left, right, middle)
    "scroll",                  # Simulates mouse wheel scrolling
    "drag_start",              # Future: For drag-and-drop simulation
    "drag_end",                # Future: For drag-and-drop simulation
    "hover"                    # Simulates hovering over an element or point
]

VirtualKeyboardActionType = Literal[
    "type_string",             # Types a given string.
    "press_keys",              # Presses a combination of keys (e.g., Ctrl+C).
    "special_key"              # Presses a special key (e.g., Enter, Esc, F1).
]

class VirtualMouseCommand(TypedDict, total=False):
    action_type: Required[VirtualMouseEventType]
    # For move_relative_to_window:
    relative_x: Optional[float]
    relative_y: Optional[float]
    # For click:
    target_element_id: Optional[str] # Optional, click can be at coordinates
    click_type: Optional[Literal["left", "right", "middle"]]
    # For scroll:
    scroll_direction: Optional[Literal["up", "down", "left", "right"]]
    scroll_amount_pixels: Optional[int] # For pixel-based scrolling
    scroll_amount_ratio: Optional[float] # For ratio-based scrolling (0-1 of scrollable area)
    scroll_pages: Optional[float] # For page-based scrolling (e.g. 1 page, 0.5 pages)
    # For hover:
    # target_element_id already covered, relative_x/y also covered

class VirtualKeyboardCommand(TypedDict, total=False):
    action_type: Required[VirtualKeyboardActionType]
    # For type_string:
    text_to_type: Optional[str]
    target_element_id: Optional[str] # Element to focus before typing (optional)
    # For press_keys:
    keys: Optional[List[str]] # List of key names (e.g., ["control", "alt", "delete"])
    # For special_key:
    # keys: Optional[List[str]] # e.g. ["enter"], used by press_keys for special keys too.
                               # special_key might just use one key from the list.

class VirtualInputElementDescription(TypedDict, total=False):
    element_id: Required[str]
    element_type: Required[str] # e.g., "button", "text_field", "label", "window", "panel", "list_item"
    value: Optional[Any] # Current value (e.g. text in input, state of checkbox)
    label_text: Optional[str] # Visible text label
    is_enabled: Optional[bool]
    is_focused: Optional[bool] # Whether this element currently has virtual focus
    children: Optional[List['VirtualInputElementDescription']] # For nested elements
    # Bounding box for coarse hit detection, relative to parent or window if top-level
    # (x_ratio_start, y_ratio_start, width_ratio, height_ratio)
    bounding_box_ratios: Optional[Tuple[float, float, float, float]]
    properties: Optional[Dict[str, Any]] # Other type-specific properties


# --- Types for AI Code Execution in AVIS ---
class AIPermissionSet(TypedDict, total=False):
    """
    Defines the set of permissions for an AI operating within AVIS,
    particularly concerning code execution and resource access.
    """
    can_execute_code: Required[bool]          # General permission to execute code
    can_read_sim_hw_status: Required[bool]    # Permission to read simulated hardware status
    allowed_execution_paths: Optional[List[str]] # Future: Specific paths AI code can run from
    allowed_service_imports: Optional[List[str]] # Future: Python modules AI code can import
    max_execution_time_ms: Optional[int]         # Future: Max execution time for AI-generated code

class ExecutionRequest(TypedDict):
    """
    Represents a request to execute code, including the code itself
    and the permissions context under which it should run.
    """
    request_id: str
    code_to_execute: str
    permissions_context: AIPermissionSet
    # Future: Add resource_requirements: Optional[Dict[str, Any]]

class ExecutionResult(TypedDict):
    """
    Represents the outcome of an AI code execution attempt.
    """
    request_id: str
    execution_success: bool        # True if execution proceeded (even if script had errors), False if pre-execution checks failed (e.g. permissions)
    script_exit_code: Optional[int] # Exit code of the executed script (if execution_success was True)
    stdout: str
    stderr: str
    status_message: str            # e.g., "Execution denied: Insufficient permissions", "Execution completed", "Script error"
    # Future: Add execution_time_ms: Optional[float]

# --- Types for HAMMemoryManager ---
class HAMDataPackageInternal(TypedDict):
    timestamp: str
    data_type: str
    encrypted_package: bytes
    metadata: DialogueMemoryEntryMetadata

class HAMRecallResult(TypedDict):
    id: str
    timestamp: str
    data_type: str
    rehydrated_gist: Any
    metadata: DialogueMemoryEntryMetadata

# --- Types for LLMInterface ---
class LLMInterfaceConfig(TypedDict, total=False):
    default_provider: Required[str]
    default_model: Required[str]
    providers: Required[Dict[str, Any]] # e.g., {"ollama": {"base_url": "http://localhost:11434"}}
    default_generation_params: Optional[Dict[str, Any]]
    operational_configs: Optional[Dict[str, Any]] # Could point to OperationalConfig if that's fully defined too

class LLMProviderConfigEntry(TypedDict, total=False): # Base for provider-specific configs
    api_key_env_var: Optional[str]
    # Add other common provider config fields here if they arise

class LLMProviderOllamaConfig(LLMProviderConfigEntry): # Inherits, though Ollama doesn't use api_key_env_var typically
    base_url: Required[str]
    default_model: Optional[str] # Model to use if not specified in request for this provider
    default_keep_alive: Optional[Union[str, int]] # e.g., "5m" or 300 (seconds)

class LLMProviderAnthropicConfig(LLMProviderConfigEntry):
    # anthropic_version: Optional[str] # Example if needed later
    default_model: Optional[str]

class LLMProviderOpenAIConfig(LLMProviderConfigEntry):
    default_model: Optional[str]
    # Add fields like 'organization_id', 'project_id' if needed by implementation

class LLMModelInfo(TypedDict, total=False):
    model_id: Required[str] # e.g., "ollama/llama2" or "openai/gpt-3.5-turbo"
    description: Optional[str]
    provider: Optional[str]
    context_length: Optional[int]
    # Add other metadata like creator, type (chat, completion), etc.

# --- Formula Engine Types ---
class FormulaConfigEntry(TypedDict):
    name: str
    conditions: List[str]
    action: str
    description: str
    parameters: Dict[str, Any]
    priority: int
    enabled: bool
    version: str
    response_template: Optional[str]

# --- Knowledge Graph Types (for ContentAnalyzerModule) ---
class KGEntity(TypedDict):
    id: str
    label: str
    type: str
    attributes: Dict[str, Any]

class KGRelationship(TypedDict):
    source_id: str
    target_id: str
    type: str
    weight: Optional[float]
    attributes: Dict[str, Any]

class KnowledgeGraph(TypedDict):
    entities: Dict[str, KGEntity]
    relationships: List[KGRelationship]
    metadata: Dict[str, Any]

# --- Fact Extractor Types ---
class UserPreferenceContent(TypedDict, total=False):
    category: Required[str]
    preference: Required[str]
    liked: Optional[bool]

class UserStatementContent(TypedDict):
    attribute: str
    value: str

# A fallback for less structured content, though specific types are preferred.
ExtractedFactContent = Union[UserPreferenceContent, UserStatementContent, Dict[str, Any]]

class ExtractedFact(TypedDict):
    fact_type: str # e.g., "user_preference", "user_statement"
    content: ExtractedFactContent
    confidence: float

# --- Learning Manager Types ---
class LearnedFactRecord(TypedDict, total=False):
    """
    Represents the metadata associated with a fact learned and stored by the LearningManager.
    This structure is typically stored as the 'metadata' part of a HAM entry for learned facts.
    """
    record_id: Required[str] # Unique ID for this learning record instance
    timestamp: Required[str] # ISO timestamp of when this record was created/processed by LearningManager
    fact_type: Required[str] # Type of fact (e.g., "user_preference", "hsp_derived_statement")
    confidence: Required[float] # Confidence score of this fact
    source_text: Required[str] # Original text or representation from which fact was derived

    # Optional fields depending on source and context
    user_id: Optional[str]
    session_id: Optional[str]
    source_interaction_ref: Optional[str] # e.g., a message ID, HSP envelope ID

    # HSP-specific fields (if the fact originated from or was processed via HSP)
    hsp_originator_ai_id: Optional[str] # The AI that originally asserted the fact
    hsp_sender_ai_id: Optional[str]     # The AI that directly sent this fact to us via HSP
    hsp_fact_id: Optional[str]          # The original ID of the fact from the HSP network
    hsp_fact_timestamp_created: Optional[str] # Original creation timestamp from HSP payload

    # Fields for conflict resolution metadata
    supersedes_ham_records: Optional[List[str]] # List of HAM record IDs this fact supersedes
    resolution_strategy: Optional[str]          # Strategy used for conflict resolution (e.g., "confidence_supersede_type1")
    superseded_reason: Optional[str]            # Brief reason for superseding
    conflicts_with_ham_records: Optional[List[str]] # List of HAM record IDs this fact contradicts
    conflicting_values: Optional[List[str]]         # Snippets of conflicting values
    merged_from_ham_records: Optional[List[str]]    # List of HAM record IDs this fact was merged from
    original_values: Optional[List[Any]]            # Original values before a merge
    merged_value: Optional[Any]                     # The result of a merge (e.g., numerical average)
    merged_confidence: Optional[float]              # Confidence of the merged fact

    # Semantic identifiers (often from ContentAnalyzerModule processing of HSP facts)
    hsp_semantic_subject: Optional[str]
    hsp_semantic_predicate: Optional[str]
    hsp_semantic_object: Optional[Any] # Can be URI or literal
    ca_subject_id: Optional[str]       # ContentAnalyzer's internal ID for the subject
    ca_predicate_type: Optional[str]   # ContentAnalyzer's internal type for the predicate
    ca_object_id: Optional[str]        # ContentAnalyzer's internal ID for the object


print("common_types.py (debug version) finished definitions.")
