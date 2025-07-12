from typing import TypedDict, Any, Optional, Dict, List, Literal, Union, Required, NewType

class TechBlockInput(TypedDict):
    """
    Standardized input structure for a Tech Block.
    """
    data: Any
    config: Optional[Dict[str, Any]]

class TechBlockOutput(TypedDict):
    """
    Standardized output structure for a Tech Block.
    """
    result: Optional[Any]
    status: Literal["success", "error", "warning"]
    error_message: Optional[str]
    warning_messages: Optional[List[str]]
    metadata: Optional[Dict[str, Any]]

class TechBlockManifest(TypedDict):
    """
    Metadata manifest describing a Tech Block.
    Used for registration, discovery, and validation.
    """
    id: str
    name: str
    version: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    config_schema: Optional[Dict[str, Any]]
    dependencies: Optional[List[str]]
    resource_requirements: Optional[Dict[str, Any]]
    tags: Optional[List[str]]
    author: Optional[str]
    created_at: Optional[str]

class InputSourceMappingValue(TypedDict, total=False):
    """
    Defines the source for a specific field in a TechBlock's input data or config.
    Provides one of 'source_step_output_field', 'initial_module_input_field',
    or 'literal_value'.
    """
    source_step_id: Required[str]
    source_step_output_field: Required[str]

    initial_module_input_field: Required[str]

    literal_value: Required[Any]

    transform: Optional[str]
    default_value: Optional[Any]

class ModuleBlueprintStep(TypedDict):
    """
    Defines a single step in a ModuleBlueprint.
    """
    step_id: str
    block_manifest_id: str

    instance_config: Optional[Dict[str, Any]]

    runtime_config_mapping: Optional[Dict[str, Union['InputSourceMappingValue', Any]]]

    input_data_mapping: Union['InputSourceMappingValue', Dict[str, Union['InputSourceMappingValue', Any]]]

class ModuleBlueprint(TypedDict):
    """
    Defines the blueprint for assembling and executing a Module.
    """
    id: str
    name: str
    version: str
    description: str

    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]

    steps: List[ModuleBlueprintStep]

    final_output_mapping: Union['InputSourceMappingValue', Dict[str, Union['InputSourceMappingValue', Any]]]

    metadata: Optional[Dict[str, Any]]

AssembledModuleInstanceID = NewType('AssembledModuleInstanceID', str)

class UserContext(TypedDict, total=False):
    user_id: Required[str]
    session_id: Optional[str]
    persona_id: Optional[str]
    preferences: Optional[Dict[str, Any]]

class SemanticTaskRequest(TypedDict):
    task_id: str
    intent: str
    data: Any
    user_id: str
    session_id: Optional[str]

class SemanticTaskResponse(TypedDict):
    task_id: str
    status: Literal["success", "error", "partial_success"]
    result: Optional[Any]
    error_message: Optional[str]
    metadata: Optional[Dict[str, Any]]
