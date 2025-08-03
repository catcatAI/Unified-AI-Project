from typing import TypedDict, Required, Optional, List, Dict, Any, Literal

# Virtual Input types
class VirtualInputElementDescription(TypedDict, total=False):
    element_id: Required[str]
    element_type: Required[str]
    label: Optional[str]
    value: Optional[str]
    is_focused: Optional[bool]
    is_enabled: Optional[bool]
    is_visible: Optional[bool]
    attributes: Optional[Dict[str, Any]]
    children: Optional[List['VirtualInputElementDescription']]

VirtualInputPermissionLevel = Literal[
    "simulation_only",
    "requires_user_confirmation",
    "full_control_trusted"
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

# Simulated Resource Types
class SimulatedDiskConfig(TypedDict):
    space_gb: Required[float]
    warning_threshold_percent: Required[float]
    critical_threshold_percent: Required[float]
    lag_factor_warning: Required[float]
    lag_factor_critical: Required[float]

class SimulatedCPUConfig(TypedDict):
    cores: Required[int]

class SimulatedRAMConfig(TypedDict):
    ram_gb: Required[float]

class SimulatedHardwareProfile(TypedDict):
    profile_name: Required[str]
    disk: Required[SimulatedDiskConfig]
    cpu: Required[SimulatedCPUConfig]
    ram: Required[SimulatedRAMConfig]
    gpu_available: Required[bool]

class SimulatedResourcesRoot(TypedDict):
    simulated_hardware_profile: Required[SimulatedHardwareProfile]
