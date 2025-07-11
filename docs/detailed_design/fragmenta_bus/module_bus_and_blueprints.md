# Module Bus Controller & Module Blueprints: Detailed Design

**Version:** 0.1
**Date:** July 11, 2024
**Parent Plan:** `docs/implementation_guides/Fragmenta_Bus_Implementation_Plan.md`
**Depends on:**
*   `docs/detailed_design/fragmenta_bus/tech_block_core_definitions.md`
*   `docs/detailed_design/fragmenta_bus/technical_bus_controller_and_library.md`
**Authors:** Jules (AI Agent)

## 1. Introduction

This document provides the detailed design for the `ModuleBusController` and the refined `ModuleBlueprint` data structures. The `ModuleBusController` is responsible for assembling "Modules" from Tech Blocks according to `ModuleBlueprint` definitions and managing their execution. A Module represents a higher-level, cohesive AI functionality. This layer sits above the `TechnicalBusController`.

## 2. Refined `ModuleBlueprint` Data Structures

These data structures will likely reside in `src/fragmenta_bus/common/data_models.py`.

### 2.1. `InputSourceMappingValue` (`TypedDict`)

Defines how a single input field for a `TechBlock` is constructed.

```python
from typing import TypedDict, List, Dict, Any, Optional, Literal, Union, Required # Added Required for Python 3.9+

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
```
*   **`source_step_id`**: ID of a previous step in the blueprint (its `step_id`). Used with `source_step_output_field`.
*   **`source_step_output_field`**: Path to the field in the source step's `TechBlockOutput.result` (e.g., "summary.text", "entities[0].name"). Uses dot notation for nesting and brackets for list indices.
*   **`initial_module_input_field`**: Path to field in the Module's initial input data.
*   **`literal_value`**: A direct literal value.
*   **`transform`**: Optional transformation function to apply (e.g., "to_string", "extract_length").
*   **`default_value`**: Value to use if the source field is not found or is None.
    *Logic must ensure only one primary source key (`source_step_output_field`, `initial_module_input_field`, `literal_value`) is used.*

### 2.2. `ModuleBlueprintStep` (`TypedDict`) - Refined

Defines a single step within a `ModuleBlueprint`. Each step typically executes one Tech Block.

```python
class ModuleBlueprintStep(TypedDict):
    """
    Defines a single step in a ModuleBlueprint.
    """
    step_id: str                # Unique identifier for this step within the blueprint (e.g., "summarize_text_step")
    block_manifest_id: str      # Manifest ID of the TechBlock to execute (e.g., "text.summarization.abstractive_v1")

    instance_config: Optional[Dict[str, Any]] # Static config for this TechBlock instance

    runtime_config_mapping: Optional[Dict[str, Union[InputSourceMappingValue, Any]]] # For TechBlockInput.config

    input_data_mapping: Union[InputSourceMappingValue, Dict[str, Union[InputSourceMappingValue, Any]]] # For TechBlockInput.data

    # condition: Optional[str] # Future: Conditions for executing this step
```
*   **`step_id`**: Crucial for referencing outputs of this step.
*   **`instance_config`**: Static configuration for the Tech Block instance.
*   **`runtime_config_mapping`**: Defines `TechBlockInput.config`. Values can be literals or mapped using `InputSourceMappingValue`.
*   **`input_data_mapping`**: Defines `TechBlockInput.data`. Can be a single `InputSourceMappingValue` or a dictionary to construct a complex object.

### 2.3. `ModuleBlueprint` (`TypedDict`) - Refined

Defines the structure and execution flow of an entire Module.

```python
class ModuleBlueprint(TypedDict):
    """
    Defines the blueprint for assembling and executing a Module.
    """
    id: str
    name: str
    version: str
    description: str

    input_schema: Dict[str, Any] # JSON Schema for the Module's initial input
    output_schema: Dict[str, Any] # JSON Schema for the Module's final output

    steps: List[ModuleBlueprintStep] # Ordered list of steps (sequential for now)

    final_output_mapping: Union[InputSourceMappingValue, Dict[str, Union[InputSourceMappingValue, Any]]]

    metadata: Optional[Dict[str, Any]]
```
*   **`final_output_mapping`**: Defines how the Module's final result is constructed from step outputs or initial inputs.

## 3. `ModuleBusController` Detailed Design

**Proposed Filepath:** `src/fragmenta_bus/module_bus/controller.py`

### 3.1. Purpose

The `ModuleBusController` loads `ModuleBlueprint`s, "assembles" Module instances (execution plans), orchestrates their execution via the `TechnicalBusController`, and manages complex data flow between Tech Blocks within a Module.

### 3.2. Class Definition: `ModuleBusController`

```python
from typing import Dict, Any, Optional, List, Union, Literal, cast
# Assuming common types are correctly imported
from ...common.data_models import (
    ModuleBlueprint, ModuleBlueprintStep, TechBlockInput, TechBlockOutput,
    InputSourceMappingValue, AssembledModuleInstanceID
)
from ..technical_bus.controller import TechnicalBusController # Removed , TechnicalBusExecutionError
# Assuming TechBlockOutput is a TypedDict and can be instantiated directly

class ModuleAssemblyError(Exception):
    pass

class ModuleExecutionError(Exception):
    pass

class AssembledModuleInstance:
    """
    Represents an executable instance of a Module for a single invocation.
    """
    def __init__(self, instance_id: AssembledModuleInstanceID, blueprint: ModuleBlueprint,
                 initial_input_data: Any, module_execution_context: Optional[Dict[str, Any]]):
        self.instance_id = instance_id
        self.blueprint = blueprint
        self.initial_input_data = initial_input_data
        self.module_execution_context = module_execution_context or {}
        self.step_outputs: Dict[str, TechBlockOutput] = {} # Stores output of each step_id
        self.status: Literal["pending", "running", "completed", "failed"] = "pending"
        self.final_result: Optional[Any] = None
        self.error_message: Optional[str] = None

    def _resolve_path(self, source: Any, path_str: str) -> Tuple[Any, bool]:
        """Helper to resolve a dot-and-bracket notation path from a source object."""
        current = source
        try:
            for part in path_str.replace("[", ".[").split("."):
                if not part: continue
                if part.startswith("[") and part.endswith("]"):
                    idx = int(part[1:-1])
                    if not isinstance(current, list) or idx >= len(current): return None, False
                    current = current[idx]
                else:
                    if not isinstance(current, dict) or part not in current: return None, False
                    current = current[part]
            return current, True
        except (IndexError, KeyError, TypeError, ValueError):
            return None, False

    def get_source_value(self, mapping_value_dict: InputSourceMappingValue) -> Any:
        """
        Resolves an InputSourceMappingValue (which is a dict) to an actual value.
        """
        value: Any = None
        found: bool = False

        if "literal_value" in mapping_value_dict:
            return mapping_value_dict["literal_value"]

        if mapping_value_dict.get("initial_module_input_field"):
            path = mapping_value_dict["initial_module_input_field"]
            value, found = self._resolve_path(self.initial_input_data, path)

        elif mapping_value_dict.get("source_step_id") and mapping_value_dict.get("source_step_output_field"):
            step_id = mapping_value_dict["source_step_id"]
            path = mapping_value_dict["source_step_output_field"]

            if step_id not in self.step_outputs:
                 raise ModuleExecutionError(f"Missing source_step_id '{step_id}' in step_outputs for mapping: {mapping_value_dict}")

            source_step_output = self.step_outputs[step_id]
            if source_step_output["status"] == "success":
                source_result = source_step_output.get("result")
                value, found = self._resolve_path(source_result, path)
            else: # Source step failed
                 raise ModuleExecutionError(f"Dependency step '{step_id}' failed, cannot use its output for: {mapping_value_dict}")

        if not found:
            if "default_value" in mapping_value_dict:
                return mapping_value_dict["default_value"]
            raise ModuleExecutionError(f"Failed to resolve input source: {mapping_value_dict}. Path not found or source error.")

        # TODO: Implement registered 'transform' functions if mapping_value_dict.get('transform')
        return value

    def _build_payload_from_mapping(self, mapping_definition: Union[InputSourceMappingValue, Dict[str, Union[InputSourceMappingValue, Any]], Any]) -> Any:
        """
        Constructs a data payload (e.g., for TechBlockInput.data or .config, or final module output)
        based on its mapping definition.
        """
        if isinstance(mapping_definition, dict):
            is_single_source_map = "source_step_id" in mapping_definition or \
                                   "initial_module_input_field" in mapping_definition or \
                                   "literal_value" in mapping_definition

            if is_single_source_map and not any(isinstance(v, dict) and ("source_step_id" in v or "initial_module_input_field" in v or "literal_value" in v) for v in mapping_definition.values()):
                # It's a single InputSourceMappingValue
                return self.get_source_value(cast(InputSourceMappingValue, mapping_definition))
            else:
                # It's a dictionary of target_field: (InputSourceMappingValue or literal)
                constructed_object = {}
                for target_key, source_mapping_or_literal in mapping_definition.items():
                    if isinstance(source_mapping_or_literal, dict) and \
                       ("source_step_id" in source_mapping_or_literal or \
                        "initial_module_input_field" in source_mapping_or_literal or \
                        "literal_value" in source_mapping_or_literal):
                        constructed_object[target_key] = self.get_source_value(cast(InputSourceMappingValue, source_mapping_or_literal))
                    else: # It's a literal
                        constructed_object[target_key] = source_mapping_or_literal
                return constructed_object
        else:
            # It's a direct literal value not requiring resolution (e.g. simple string, number)
            return mapping_definition

class ModuleBusController:
    _technical_bus: TechnicalBusController
    _blueprint_registry: Dict[str, ModuleBlueprint]
    # _active_module_instances: Dict[AssembledModuleInstanceID, AssembledModuleInstance] # Might not be needed if invoke is blocking

    def __init__(self, technical_bus: TechnicalBusController):
        self._technical_bus = technical_bus
        self._blueprint_registry = {}
        # self._active_module_instances = {}
        # Placeholder for schema validation utility
        # self._validator = jsonschema.Draft7Validator


    def register_blueprint(self, blueprint: ModuleBlueprint) -> None:
        blueprint_id = blueprint.get("id")
        if not blueprint_id:
            raise ModuleAssemblyError("ModuleBlueprint must have an 'id'.")
        if blueprint_id in self._blueprint_registry:
            raise ModuleAssemblyError(f"ModuleBlueprint with ID '{blueprint_id}' already registered.")
        # TODO: Full validation of blueprint structure (e.g., step_ids are unique, source_step_ids exist)
        self._blueprint_registry[blueprint_id] = blueprint

    def get_blueprint(self, blueprint_id: str) -> Optional[ModuleBlueprint]:
        return self._blueprint_registry.get(blueprint_id)

    def _validate_module_data(self, data: Any, schema: Optional[Dict[str, Any]], blueprint_id_for_error: str, context_msg: str) -> None:
        """Validates module's initial input or final output against its schema."""
        if schema:
            # print(f"Module schema validation for {blueprint_id_for_error} {context_msg} - SKIPPED (jsonschema not implemented)")
            # try:
            #     jsonschema.validate(instance=data, schema=schema)
            # except jsonschema.exceptions.ValidationError as e:
            #     raise ModuleExecutionError(f"Module '{blueprint_id_for_error}' {context_msg} schema validation failed: {e.message}")
            pass # Placeholder for actual jsonschema validation
        return

    async def invoke_module(
        self,
        blueprint_id: str,
        initial_module_input_data: Any,
        module_execution_context: Optional[Dict[str, Any]] = None,
        instance_id_prefix: Optional[str] = None
    ) -> TechBlockOutput:
        """
        Assembles and executes a Module instance based on a blueprint.
        Returns a TechBlockOutput-like structure representing the module's execution result.
        """
        blueprint = self.get_blueprint(blueprint_id)
        if not blueprint:
            # Return a TechBlockOutput compatible error
            return TechBlockOutput(result=None, status="error", error_message=f"ModuleBlueprint '{blueprint_id}' not found.", metadata={"module_id": blueprint_id})

        try:
            self._validate_module_data(initial_module_input_data, blueprint.get("input_schema"), blueprint_id, "initial input")

            instance_id_str = f"{instance_id_prefix or blueprint_id}_run_{abs(hash(str(initial_module_input_data)) + hash(str(module_execution_context)))}"
            module_instance = AssembledModuleInstance(
                AssembledModuleInstanceID(instance_id_str),
                blueprint,
                initial_module_input_data,
                module_execution_context
            )
            module_instance.status = "running"

            for i, step_def in enumerate(blueprint["steps"]):
                # TODO: Implement condition checking for step_def.get("condition")

                step_runtime_config = module_instance._build_payload_from_mapping(step_def.get("runtime_config_mapping", {}))
                step_data_payload = module_instance._build_payload_from_mapping(step_def["input_data_mapping"])

                tech_block_input = TechBlockInput(data=step_data_payload, config=step_runtime_config if step_runtime_config else None)
                tech_block_instance_config = step_def.get("instance_config")

                step_output = await self._technical_bus.execute_single_block(
                    block_manifest_id=step_def["block_manifest_id"],
                    input_payload=tech_block_input,
                    execution_context=module_instance.module_execution_context,
                    instance_run_id=f"{module_instance.instance_id}_step_{step_def['step_id']}",
                    instance_config=tech_block_instance_config
                )

                module_instance.step_outputs[step_def["step_id"]] = step_output

                if step_output["status"] == "error":
                    error_msg = f"Module '{blueprint_id}' failed at step '{step_def['step_id']}' ({step_def['block_manifest_id']}): {step_output['error_message']}"
                    module_instance.status = "failed"
                    module_instance.error_message = error_msg
                    # Return the error output from the failing TechBlock
                    return step_output

            final_module_result = module_instance._build_payload_from_mapping(blueprint["final_output_mapping"])
            self._validate_module_data(final_module_result, blueprint.get("output_schema"), blueprint_id, "final output")

            module_instance.final_result = final_module_result
            module_instance.status = "completed"

            return TechBlockOutput(result=final_module_result, status="success", error_message=None, metadata={"module_id": blueprint_id, "instance_id": module_instance.instance_id})

        except ModuleExecutionError as e:
            return TechBlockOutput(result=None, status="error", error_message=str(e), metadata={"module_id": blueprint_id})
        except Exception as e: # Catch-all for unexpected errors during module orchestration
            # Log actual exception e with traceback for debugging
            error_type = type(e).__name__
            return TechBlockOutput(result=None, status="error", error_message=f"Unexpected error in module '{blueprint_id}': {error_type} - {str(e)}", metadata={"module_id": blueprint_id})

```

### 3.3. Key Logic and Considerations

*   **`AssembledModuleInstance`:** This class is crucial. It's instantiated for each `invoke_module` call and holds the state of that specific run (initial inputs, intermediate step outputs). This makes the `ModuleBusController` itself stateless regarding individual module executions.
*   **Input/Output Resolution (`get_source_value`, `_build_payload_from_mapping`):** These methods in `AssembledModuleInstance` are the core of the data-flow logic. They interpret the `InputSourceMappingValue` dictionaries to fetch data from the correct source (initial module input or a previous step's output) and construct the input for the current Tech Block. The path resolution (`_resolve_path`) is basic and might need a more robust JSONPath-like implementation.
*   **Error Handling:** If any Tech Block execution within a module fails, or if data mapping fails, the module execution stops, and an error `TechBlockOutput` is returned.
*   **Sequential Execution:** The current design executes steps sequentially. Parallel execution of steps (e.g., a fan-out/fan-in pattern) would require significant additions to `ModuleBlueprint` (to define parallel groups) and `ModuleBusController` logic (using `asyncio.gather` for Tech Block calls).
*   **Schema Validation:** Placeholders for `jsonschema` validation of the module's overall input and output, as well as Tech Block inputs/outputs (delegated to `TechnicalBusController`).
*   **Caching:** Caching of fully assembled and executed module instances (if inputs and blueprint are identical) is a potential future optimization but not included in this initial design.
*   **Blueprint Validation:** `register_blueprint` should ideally perform comprehensive validation of the blueprint structure (e.g., all `source_step_id`s are valid, no circular dependencies in simple sequences).

## 4. Configuration

*   `ModuleBlueprint` definitions (YAML or JSON files) would reside in a designated directory, e.g., `configs/fragmenta_bus/module_blueprints/`.
*   The `ModuleBusController` would need to be initialized with a `TechnicalBusController` instance.

## 5. Next Steps in Detailed Design

*   **SemanticBusController:** Design the top-level bus controller that interprets high-level intents and invokes modules via the `ModuleBusController`.
*   **Advanced Blueprint Features:** Consider how to define and implement parallel execution, conditional steps, and looping within `ModuleBlueprint`s.
*   **Transformation Functions:** Design a registry and invocation mechanism for `transform` functions specified in `InputSourceMappingValue`.
*   **Implement JSON Schema Validation:** Replace placeholder comments with actual validation logic.

This design for `ModuleBusController` and `ModuleBlueprint` provides the mechanisms for creating complex, reusable AI functionalities by orchestrating sequences of granular Tech Blocks with sophisticated data flow management.
