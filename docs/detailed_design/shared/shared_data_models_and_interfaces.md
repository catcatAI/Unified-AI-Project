# Shared Core Data Models & Interfaces

**Version:** 0.1
**Date:** July 11, 2024
**Purpose:** To consolidate key `TypedDict` definitions and Abstract Base Class (ABC) proposals from the detailed designs of the Fragmenta Bus System, ContextCore Module, Actuarion Module, and Semantic Multiplication Tables. This provides a unified view of core data contracts.
**Authors:** Jules (AI Agent)

## 1. Introduction

As we develop multiple interconnected systems for the Unified-AI-Project, it's crucial to have a clear and consistent set of shared data models and interfaces. This document brings together the core `TypedDict` definitions and ABCs proposed across the new architectural components. These would typically reside in shared Python modules like `src/fragmenta_bus/common/data_models.py`, `src/core_ai/memory/context_core/models.py`, `src/common_models/`, etc.

## 2. Fragmenta Bus System: Core Definitions

**Source:** `docs/detailed_design/fragmenta_bus/tech_block_core_definitions.md`
**Target Python Modules (Conceptual):**
*   `src/fragmenta_bus/common/data_models.py`
*   `src/fragmenta_bus/common/tech_block_interface.py`

### 2.1. `TechBlockInput` (`TypedDict`)

```python
from typing import TypedDict, Any, Optional, Dict, List, Literal, Union, Required # Added Required
# For ABC:
from abc import ABC, abstractmethod

class TechBlockInput(TypedDict):
    """
    Standardized input structure for a Tech Block.
    """
    data: Any
    config: Optional[Dict[str, Any]]
```

### 2.2. `TechBlockOutput` (`TypedDict`)

```python
class TechBlockOutput(TypedDict):
    """
    Standardized output structure for a Tech Block.
    """
    result: Optional[Any]
    status: Literal["success", "error", "warning"]
    error_message: Optional[str]
    warning_messages: Optional[List[str]]
    metadata: Optional[Dict[str, Any]]
```

### 2.3. `TechBlockManifest` (`TypedDict`)

```python
class TechBlockManifest(TypedDict):
    """
    Metadata manifest describing a Tech Block.
    """
    id: str
    name: str
    version: str
    description: str
    input_schema: Dict[str, Any]  # JSON Schema
    output_schema: Dict[str, Any] # JSON Schema
    config_schema: Optional[Dict[str, Any]] # JSON Schema for TechBlockInput.config
    dependencies: Optional[List[str]]
    resource_requirements: Optional[Dict[str, Any]]
    tags: Optional[List[str]]
    author: Optional[str]
    created_at: Optional[str] # ISO 8601 datetime string
```

### 2.4. `TechBlock` (ABC)

```python
class TechBlock(ABC):
    """
    Abstract Base Class for all Tech Blocks.
    """
    def __init__(self, block_id: str, version: str, config: Optional[Dict[str, Any]] = None):
        self._block_id = block_id
        self._version = version
        self._instance_config = config or {}

    @property
    def id(self) -> str:
        return self._block_id

    @property
    def version(self) -> str:
        return self._version

    @classmethod
    @abstractmethod
    def get_class_manifest(cls) -> TechBlockManifest:
        """Returns the TechBlockManifest for this specific TechBlock class."""
        pass

    @abstractmethod
    async def execute(self, input_data: TechBlockInput, context: Optional[Dict[str, Any]] = None) -> TechBlockOutput:
        """Executes the core logic of the Tech Block."""
        pass

    def get_manifest(self) -> TechBlockManifest: # Instance method
        return self.__class__.get_class_manifest()
```

### 2.5. `InputSourceMappingValue` (`TypedDict`)

**Source:** `docs/detailed_design/fragmenta_bus/module_bus_and_blueprints.md`

```python
class InputSourceMappingValue(TypedDict, total=False):
    """
    Defines the source for a specific field in a TechBlock's input data or config.
    """
    source_step_id: Required[str]
    source_step_output_field: Required[str]
    initial_module_input_field: Required[str]
    literal_value: Required[Any]
    transform: Optional[str]
    default_value: Optional[Any]
```

### 2.6. `ModuleBlueprintStep` (`TypedDict`)

**Source:** `docs/detailed_design/fragmenta_bus/module_bus_and_blueprints.md`

```python
class ModuleBlueprintStep(TypedDict):
    """
    Defines a single step in a ModuleBlueprint.
    """
    step_id: str
    block_manifest_id: str
    instance_config: Optional[Dict[str, Any]]
    runtime_config_mapping: Optional[Dict[str, Union[InputSourceMappingValue, Any]]]
    input_data_mapping: Union[InputSourceMappingValue, Dict[str, Union[InputSourceMappingValue, Any]]]
    # condition: Optional[str] # Future
```

### 2.7. `ModuleBlueprint` (`TypedDict`)

**Source:** `docs/detailed_design/fragmenta_bus/module_bus_and_blueprints.md`

```python
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
    final_output_mapping: Union[InputSourceMappingValue, Dict[str, Union[InputSourceMappingValue, Any]]]
    metadata: Optional[Dict[str, Any]]
```

### 2.8. `AssembledModuleInstanceID` (Type Alias)

**Source:** `docs/detailed_design/fragmenta_bus/module_bus_and_blueprints.md`
This is typically a string, so a type alias is appropriate.
```python
from typing import NewType
AssembledModuleInstanceID = NewType('AssembledModuleInstanceID', str)
```

### 2.9. `UserContext` (`TypedDict`)

**Source:** `docs/detailed_design/fragmenta_bus/semantic_bus_controller.md`

```python
class UserContext(TypedDict, total=False):
    user_id: Required[str]
    session_id: Optional[str]
    persona_id: Optional[str]
    preferences: Optional[Dict[str, Any]]
    # Other relevant user/session state
```

### 2.10. `SemanticTaskRequest` (`TypedDict`)

**Source:** `docs/detailed_design/fragmenta_bus/semantic_bus_controller.md`

```python
class SemanticTaskRequest(TypedDict):
    task_id: str
    intent: str
    data: Any
    user_id: str
    session_id: Optional[str]
    # priority: Optional[int]
    # required_capabilities: Optional[List[str]]
    # response_format_preferences: Optional[Dict]
```

### 2.11. `SemanticTaskResponse` (`TypedDict`)

**Source:** `docs/detailed_design/fragmenta_bus/semantic_bus_controller.md`

```python
class SemanticTaskResponse(TypedDict):
    task_id: str
    status: Literal["success", "error", "partial_success"]
    result: Optional[Any]
    error_message: Optional[str]
    metadata: Optional[Dict[str, Any]]
```

## 3. ContextCore Module: Core Data Models

**Source:** `docs/implementation_guides/ContextCore_Implementation_Plan.md`
**Target Python Module (Conceptual):** `src/core_ai/memory/context_core/models.py`

### 3.1. `ContextItemMetadata` (`TypedDict`)

```python
class ContextItemMetadata(TypedDict):
    created_at: float
    updated_at: float
    source_module: str
    source_interaction_id: Optional[str]
    confidence: Optional[float]
    tags: Optional[List[str]]
    custom_properties: Optional[Dict[str, Any]]
```

### 3.2. `ContextItem` (`TypedDict`)

```python
class ContextItem(TypedDict):
    item_id: str
    item_type: str
    content: Any
    scopes: List[str]
    metadata: ContextItemMetadata
```

### 3.3. `KnowledgeGraphTriple` (`TypedDict`)

```python
class KnowledgeGraphTriple(TypedDict):
    subject_id: str # Typically a URI or a ContextItem ID
    predicate: str  # Typically a URI representing the relationship
    object_id_or_literal: Union[str, Any] # URI for entity, or literal value with datatype
```

### 3.4. `RetrievedContextChunk` (`TypedDict`)

```python
class RetrievedContextChunk(TypedDict):
    item_id: str
    content: Any
    score: float # Relevance score
    source_store: Literal["graph", "vector", "document", "smt"]
    metadata: ContextItemMetadata
```

### 3.5. `UserProfileContent` (`TypedDict`)
(Content for a `ContextItem` of `item_type="user_profile"`)
```python
class UserProfileContent(TypedDict):
    preferences: Dict[str, Any]
    history_summary: str
    derived_traits: List[str]
    # Other structured user data
```

## 4. Actuarion Module: Core Data Models

**Source:** `docs/implementation_guides/Actuarion_Module_Implementation_Plan.md`
**Target Python Module (Conceptual):** `src/core_ai/validation/actuarion/models.py`

### 4.1. `ValidationContent` (`TypedDict`)

```python
class ValidationContent(TypedDict, total=False):
    text_content: Optional[str]
    structured_data: Optional[Dict]
    code_snippet: Optional[str]
```

### 4.2. `ActuationValidationContext` (`TypedDict`)

```python
class ActuationValidationContext(TypedDict):
    user_id: Optional[str]
    session_id: Optional[str]
    task_type: Optional[str]
    source_module: Optional[str]
```

### 4.3. `ValidationInput` (`TypedDict`)

```python
class ValidationInput(TypedDict):
    content_id: str
    content_data: ValidationContent
    content_type: Literal["text", "json", "python_code", "narrative"]
    context: ActuationValidationContext
    policy_ids: Optional[List[str]]
```

### 4.4. `ValidationIssue` (`TypedDict`)

```python
class ValidationIssue(TypedDict):
    issue_id: str
    assessor_id: str
    rule_id: Optional[str]
    issue_type: str
    severity: Literal["info", "warning", "error", "critical"]
    confidence: float
    location_start: Optional[int]
    location_end: Optional[int]
    description: str
    explanation: Optional[str]
    suggested_fix: Optional[str]
```

### 4.5. `ValidationReport` (`TypedDict`)

```python
class ValidationReport(TypedDict):
    report_id: str
    content_id: str
    overall_assessment: Literal["pass", "pass_with_warnings", "fail"]
    overall_confidence: float
    risk_score: Optional[float]
    issues: List[ValidationIssue]
    summary: str
    timestamp: float
```

### 4.6. `ValidationRuleCondition` (`TypedDict`)

```python
class ValidationRuleCondition(TypedDict):
    type: str
    pattern: Optional[str]
    keywords: Optional[List[str]]
    # ... other condition fields
```

### 4.7. `ValidationRule` (`TypedDict`)

```python
class ValidationRule(TypedDict):
    rule_id: str
    description: str
    conditions: List[ValidationRuleCondition]
    issue_type_to_raise: str
    default_severity: Literal["info", "warning", "error", "critical"]
```

### 4.8. `ValidationPolicy` (`TypedDict`)

```python
class ValidationPolicy(TypedDict):
    policy_id: str
    description: str
    active_assessors: List[str]
    active_rule_sets: List[str]
    thresholds: Optional[Dict[str, float]]
```

## 5. Semantic Multiplication Tables (SMTs): Core Data Models

**Source:** `docs/implementation_guides/Semantic_Tables_Implementation_Plan.md`
**Target Python Module (Conceptual):** `src/core_ai/knowledge/semantic_tables/models.py` (or part of `ContextCore` models)

### 5.1. `SMTMetadata` (`TypedDict`)

```python
class SMTMetadata(TypedDict):
    version: str
    description: str
    source: Optional[str]
    author: Optional[str]
    created_at: str
    updated_at: str
    applicability_conditions: Optional[List[str]]
    confidence_level: Optional[float]
```

### 5.2. `KeyValueSMTEntry` (`TypedDict`)

```python
class KeyValueSMTEntry(TypedDict):
    key: str
    value: Any
    explanation: Optional[str]
```
### 5.3. `SMTFactPattern` and `SMTAction` (`TypedDict`s)

```python
class SMTFactPattern(TypedDict):
    subject: str
    predicate: str
    object_var: str # Variable placeholder, or direct value

class SMTAction(TypedDict):
    # Example: could assert a new fact or trigger another SMT lookup
    action_type: Literal["assert_fact", "trigger_query"]
    action_data: Dict[str, Any] # Content depends on action_type
```

### 5.4. `RuleSMTEntry` (`TypedDict`)

```python
class RuleSMTEntry(TypedDict):
    rule_id: str
    if_conditions: List[Union[str, SMTFactPattern]]
    then_actions: List[SMTAction]
    explanation: Optional[str]
```

### 5.5. `SemanticTable` (`TypedDict`)

```python
class SemanticTable(TypedDict):
    table_id: str
    domain: str
    table_type: Literal["key_value", "rule_set", "decision_tree", "graph_snippet", "faq"]
    metadata: SMTMetadata
    entries: Union[List[KeyValueSMTEntry], List[RuleSMTEntry], Dict, List[Dict]]
```

### 5.6. `SMTQuery` (`TypedDict`)

```python
class SMTQuery(TypedDict):
    table_id: str
    query_data: Dict # Input for the query, structure depends on table_type
    context: Optional[Dict]
```

### 5.7. `SMTQueryResult` (`TypedDict`)

```python
class SMTQueryResult(TypedDict):
    found: bool
    result: Optional[Any]
    explanation: Optional[str]
    source_entry_ids: Optional[List[str]]
```

## 6. Conclusion

This document consolidates the primary data structures (`TypedDict`s) and Abstract Base Classes (ABCs) proposed for the new core systems: Fragmenta Bus System, ContextCore, Actuarion Module, and Semantic Multiplication Tables. These definitions establish the fundamental contracts for data exchange and component interaction. They are intended to guide the actual implementation in Python, ensuring consistency and clarity. Further refinements may occur as detailed implementation of each module progresses.
The use of `Required` (from `typing_extensions` for Python <3.9, or `typing` for 3.9+) in `TypedDict`s with `total=False` is recommended for fields that are optional in the Python sense but must be provided if the `TypedDict` is used for specific scenarios. For simplicity in this document, `Required` is noted but full usage would depend on Python version and desired strictness.
