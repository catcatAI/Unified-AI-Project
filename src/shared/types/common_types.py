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

print("common_types.py (debug version) finished definitions.")
