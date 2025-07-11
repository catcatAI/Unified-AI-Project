# Technical Bus Controller & Tech Block Library: Detailed Design

**Version:** 0.1
**Date:** July 11, 2024
**Parent Plan:** `docs/implementation_guides/Fragmenta_Bus_Implementation_Plan.md`
**Core Definitions:** `docs/detailed_design/fragmenta_bus/tech_block_core_definitions.md`
**Authors:** Jules (AI Agent)

## 1. Introduction

This document provides the detailed design for two critical components of the Fragmenta Multi-Bus System's lower tier: the `TechBlockLibrary` and the `TechnicalBusController`.
*   The **`TechBlockLibrary`** is responsible for registering, storing, and retrieving Tech Block types.
*   The **`TechnicalBusController`** is responsible for instantiating and executing Tech Blocks, managing their immediate operational context, and orchestrating simple sequences of Tech Blocks.

These components build upon the core definitions in `tech_block_core_definitions.md`.

## 2. `TechBlockLibrary` Detailed Design

**Proposed Filepath:** `src/fragmenta_bus/tech_blocks/library.py`

### 2.1. Purpose

To serve as a central registry for all available `TechBlock` classes. It allows the bus system to discover and instantiate specific Tech Blocks based on their ID and version.

### 2.2. Class Definition: `TechBlockLibrary`

```python
from typing import Dict, Type, Optional, List
# Assuming TechBlock and TechBlockManifest are in a commonly accessible place
# For example: from ..common.tech_block_interface import TechBlock, TechBlockManifest
# For this example, let's assume they are imported correctly.
# This path might need adjustment based on actual project structure.
from ...common.tech_block_interface import TechBlock
from ...common.data_models import TechBlockManifest


class TechBlockRegistrationError(Exception):
    pass

class TechBlockNotFoundError(Exception):
    pass

class TechBlockLibrary:
    """
    Manages the registration and retrieval of TechBlock classes.
    It stores TechBlock classes, not instances.
    The key for the registry is the TechBlock manifest ID.
    """
    _registry: Dict[str, Type[TechBlock]]

    def __init__(self):
        self._registry = {}

    @staticmethod
    def get_manifest_id_from_class(block_class: Type[TechBlock]) -> str:
        """
        Helper static method to retrieve the manifest ID from a TechBlock class.
        This assumes TechBlock classes have a way to expose their manifest's ID,
        ideally via a class method like `get_class_manifest()`.
        """
        if not hasattr(block_class, 'get_class_manifest'):
            raise TechBlockRegistrationError(
                f"TechBlock class {block_class.__name__} must have a 'get_class_manifest' class method."
            )
        manifest = block_class.get_class_manifest()
        block_id = manifest.get("id")
        if not block_id:
            raise TechBlockRegistrationError(
                f"TechBlock class {block_class.__name__} manifest is missing an 'id'."
            )
        return block_id

    def register_block(self, block_class: Type[TechBlock]) -> None:
        """
        Registers a TechBlock class with the library.
        The manifest ID is used as the key.

        Args:
            block_class (Type[TechBlock]): The TechBlock class to register.

        Raises:
            TechBlockRegistrationError: If the class is not a valid TechBlock,
                                        if its manifest ID cannot be retrieved,
                                        or if a block with the same ID is already registered.
        """
        if not issubclass(block_class, TechBlock):
            raise TechBlockRegistrationError(
                f"Class {block_class.__name__} is not a subclass of TechBlock."
            )

        try:
            block_id = self.get_manifest_id_from_class(block_class)
        except TechBlockRegistrationError as e: # Catch errors from helper
            raise e
        except Exception as e: # Catch other unexpected errors
            raise TechBlockRegistrationError(
                f"Unexpected error getting manifest ID for {block_class.__name__}: {e}"
            )

        if block_id in self._registry:
            raise TechBlockRegistrationError(
                f"TechBlock with ID '{block_id}' (from class {block_class.__name__}) is already registered."
            )

        self._registry[block_id] = block_class
        # print(f"TechBlock '{block_id}' registered successfully.") # Optional logging

    def get_block_class(self, block_id: str) -> Type[TechBlock]:
        """
        Retrieves a registered TechBlock class by its manifest ID.

        Args:
            block_id (str): The manifest ID of the TechBlock class to retrieve.

        Returns:
            Type[TechBlock]: The registered TechBlock class.

        Raises:
            TechBlockNotFoundError: If no TechBlock with the given ID is found.
        """
        block_class = self._registry.get(block_id)
        if not block_class:
            raise TechBlockNotFoundError(f"TechBlock with ID '{block_id}' not found in library.")
        return block_class

    def list_available_blocks(self) -> List[TechBlockManifest]:
        """
        Lists the manifests of all available Tech Blocks.
        """
        available_manifests = []
        for block_class in self._registry.values():
            try:
                manifest = block_class.get_class_manifest()
                available_manifests.append(manifest)
            except Exception:
                # Fallback if manifest retrieval fails for some reason
                # This case should ideally not happen if registration was successful
                available_manifests.append(TechBlockManifest(id=f"error_retrieving_manifest_for_{block_class.__name__}", name="Error", version="N/A", description="Could not retrieve manifest", input_schema={}, output_schema={}))
        return available_manifests

    def clear(self) -> None:
        """Clears all registered blocks. Useful for testing."""
        self._registry.clear()
```

**Note on `get_class_manifest()` for `TechBlock` subclasses:**
As mentioned in `tech_block_core_definitions.md` and emphasized here, each concrete `TechBlock` subclass **must** implement a `classmethod` called `get_class_manifest()` that returns its `TechBlockManifest`.

Example in `TechBlock` ABC (add to `tech_block_interface.py`):
```python
# In TechBlock ABC in tech_block_interface.py
from abc import ABC, abstractmethod

class TechBlock(ABC):
    # ... (existing __init__, id, version) ...

    @classmethod
    @abstractmethod
    def get_class_manifest(cls) -> TechBlockManifest:
        """
        Returns the TechBlockManifest for this specific TechBlock class.
        This should be implemented by all concrete TechBlock subclasses.
        """
        pass

    @abstractmethod
    async def execute(self, input_data: TechBlockInput, context: Optional[Dict[str, Any]] = None) -> TechBlockOutput:
        pass

    # get_manifest() instance method is fine as is, returning self.get_class_manifest() perhaps or instance specific one
    def get_manifest(self) -> TechBlockManifest:
        return self.__class__.get_class_manifest()

```

### 2.3. Usage Example

```python
# Assuming TechBlockLibrary is in src.fragmenta_bus.tech_blocks.library
# Assuming MySampleTechBlock is a concrete TechBlock implementation
# from src.fragmenta_bus.tech_blocks.implementations.sample_block import MySampleTechBlock

# library = TechBlockLibrary()
# library.register_block(MySampleTechBlock)

# Later, to get the class:
# SampleBlockClass = library.get_block_class("domain.sample.my_sample_block_v1")
# block_instance = SampleBlockClass(block_id="instance_001", version="1.0.0")
```

## 3. `TechnicalBusController` Detailed Design

**Proposed Filepath:** `src/fragmenta_bus/technical_bus/controller.py`

### 3.1. Purpose

The `TechnicalBusController` orchestrates the execution of individual Tech Blocks and sequences of Tech Blocks. It uses the `TechBlockLibrary` to find and instantiate blocks, validates inputs/outputs against their manifests, and manages the data flow in simple sequences.

### 3.2. Class Definition: `TechnicalBusController`

```python
from typing import Dict, Any, Optional, List
# Assuming common types are correctly imported from ..common.data_models and ..common.tech_block_interface
from ...common.data_models import TechBlockInput, TechBlockOutput, ModuleBlueprintStep, TechBlockManifest
from ...common.tech_block_interface import TechBlock
from ..tech_blocks.library import TechBlockLibrary, TechBlockNotFoundError, TechBlockRegistrationError

# Optional: For schema validation if used (e.g., jsonschema)
# import jsonschema

class TechnicalBusExecutionError(Exception):
    pass

class TechnicalBusController:
    """
    Controls the instantiation and execution of TechBlocks.
    Manages data flow for sequences of TechBlocks defined by ModuleBlueprintSteps.
    """
    _library: TechBlockLibrary
    # _cache: Optional[Any] # Placeholder for a future caching mechanism
    # _resource_manager: Optional[Any] # Placeholder for future resource management

    def __init__(self, library: TechBlockLibrary): #, cache=None, resource_manager=None):
        if not isinstance(library, TechBlockLibrary):
            raise TypeError("library must be an instance of TechBlockLibrary")
        self._library = library
        # self._cache = cache
        # self._resource_manager = resource_manager

        # Placeholder for JSON schema validation utility if used
        # self._validator = jsonschema.Draft7Validator # or other version

    def _instantiate_block(self, block_manifest_id: str, instance_run_id: str, version_override: Optional[str] = None, instance_config: Optional[Dict[str, Any]] = None) -> TechBlock:
        """
        Helper to get class from library and instantiate a TechBlock.
        """
        try:
            block_class = self._library.get_block_class(block_manifest_id)

            # Determine version: Use override, then class manifest, then default
            actual_version = version_override
            if not actual_version:
                class_manifest = block_class.get_class_manifest()
                actual_version = class_manifest.get("version", "0.0.0") # Default if not in manifest

            block_instance = block_class(
                block_id=instance_run_id, # ID for this specific instance for its lifetime
                version=actual_version,
                config=instance_config or {} # Instance-level static config
            )
            return block_instance
        except TechBlockNotFoundError:
            raise
        except Exception as e:
            raise TechnicalBusExecutionError(f"Failed to instantiate TechBlock with manifest ID '{block_manifest_id}': {e}")

    def _validate_data_with_schema(self, data_instance: Any, schema: Optional[Dict[str, Any]], block_id_for_error: str, validation_context: str) -> None:
        """
        Validates data against a JSON schema. Raises TechnicalBusExecutionError on failure.
        This is a placeholder for actual jsonschema validation.
        """
        if schema:
            # print(f"Schema validation for {block_id_for_error} {validation_context} - SKIPPED (jsonschema not implemented)")
            # try:
            #     jsonschema.validate(instance=data_instance, schema=schema)
            # except jsonschema.exceptions.ValidationError as e:
            #     raise TechnicalBusExecutionError(f"Schema validation failed for {block_id_for_error} {validation_context}: {e.message}")
            pass # Placeholder: no actual validation for now
        return

    async def execute_single_block(
        self,
        block_manifest_id: str,
        input_payload: TechBlockInput,
        execution_context: Optional[Dict[str, Any]] = None,
        instance_run_id: Optional[str] = None,
        instance_config: Optional[Dict[str, Any]] = None
    ) -> TechBlockOutput:
        """
        Instantiates and executes a single TechBlock.

        Args:
            block_manifest_id (str): The manifest ID of the TechBlock class to execute.
            input_payload (TechBlockInput): The input for the TechBlock.
            execution_context (Optional[Dict[str, Any]]): Context for the execution run.
            instance_run_id (Optional[str]): A unique ID for this execution instance (for logging/tracing).
                                           If None, a default one will be generated.
            instance_config (Optional[Dict[str,Any]]): Configuration specific to this instance of the block.

        Returns:
            TechBlockOutput: The output from the TechBlock.
        """
        effective_instance_run_id = instance_run_id or f"{block_manifest_id}_exec_{abs(hash(str(input_payload)))}"

        try:
            block_instance = self._instantiate_block(block_manifest_id, effective_instance_run_id, instance_config=instance_config)
            manifest = block_instance.get_manifest() # This should be the class manifest

            # Validate input_payload.data against manifest.input_schema
            self._validate_data_with_schema(input_payload.get('data'), manifest.get('input_schema'), block_manifest_id, "input")
            # Validate input_payload.config against manifest.config_schema
            self._validate_data_with_schema(input_payload.get('config'), manifest.get('config_schema'), block_manifest_id, "runtime config")

            # TODO: Future: Check manifest.resource_requirements via _resource_manager

            output = await block_instance.execute(input_payload, execution_context)

            # Validate output.result against manifest.output_schema
            self._validate_data_with_schema(output.get('result'), manifest.get('output_schema'), block_manifest_id, "output")

            # TODO: Future: Cache result if applicable via _cache
            return output

        except TechBlockNotFoundError: # From _instantiate_block
            return TechBlockOutput(result=None, status="error", error_message=f"TechBlock type '{block_manifest_id}' not found in library.", metadata={"block_id": block_manifest_id, "instance_run_id": effective_instance_run_id})
        except TechnicalBusExecutionError as e: # From validation or instantiation
             return TechBlockOutput(result=None, status="error", error_message=str(e), metadata={"block_id": block_manifest_id, "instance_run_id": effective_instance_run_id})
        except Exception as e:
            # Log actual exception e with traceback for debugging
            error_type = type(e).__name__
            return TechBlockOutput(result=None, status="error", error_message=f"Unexpected error executing TechBlock '{block_manifest_id}': {error_type} - {str(e)}", metadata={"block_id": block_manifest_id, "instance_run_id": effective_instance_run_id})

    async def execute_block_sequence(
        self,
        blueprint_steps: List[ModuleBlueprintStep],
        initial_sequence_input: Any,
        execution_context: Optional[Dict[str, Any]] = None,
        sequence_run_id: Optional[str] = "seq_default_run"
    ) -> TechBlockOutput:
        """
        Executes a sequence of TechBlocks as defined by ModuleBlueprintSteps.
        Manages simple sequential data flow: output of one block becomes input 'data' for the next.
        Input mapping from multiple sources is NOT handled here; that's for ModuleBus.

        Args:
            blueprint_steps (List[ModuleBlueprintStep]): Ordered list of steps.
            initial_sequence_input (Any): The initial data for the 'data' field of the first block's TechBlockInput.
            execution_context (Optional[Dict[str, Any]]): Context for the entire sequence execution.
            sequence_run_id (Optional[str]): An ID for this sequence execution run.

        Returns:
            TechBlockOutput: The output of the final block in the sequence, or an error output from the first failing block.
        """
        current_block_data_payload = initial_sequence_input

        for i, step_def in enumerate(blueprint_steps):
            block_manifest_id = step_def["block_id"]
            # Runtime config for this step in the sequence
            runtime_config_override = step_def.get("config_override")
            # Instance config (static for the block type in this sequence, not currently in ModuleBlueprintStep)
            # This might come from a higher-level blueprint definition if a block type is used multiple times
            # with different static configs. For now, assume instance_config is None or passed via execution_context.
            instance_config_for_step = None # Placeholder

            current_block_input = TechBlockInput(data=current_block_data_payload, config=runtime_config_override)

            step_instance_run_id = f"{sequence_run_id}_step_{i}_{block_manifest_id}"

            step_output = await self.execute_single_block(
                block_manifest_id=block_manifest_id,
                input_payload=current_block_input,
                execution_context=execution_context,
                instance_run_id=step_instance_run_id,
                instance_config=instance_config_for_step
            )

            if step_output["status"] == "error":
                # If any block fails, the sequence fails and returns that block's error output.
                return step_output

            current_block_data_payload = step_output.get("result") # Output 'result' of current becomes 'data' for next.

        # If loop completes, return the output of the last successfully executed block
        if 'step_output' in locals(): # Check if loop ran at least once
            return step_output
        else: # Empty blueprint_steps list
            # Return a "success" but with no result, or an error indicating empty sequence?
            # For now, treat as success with None result if initial_payload was the intended output.
            # Or, more logically, an error if steps were expected.
            return TechBlockOutput(result=initial_sequence_input if not blueprint_steps else None,
                                   status="success" if not blueprint_steps else "error",
                                   error_message="No steps in blueprint." if blueprint_steps else None,
                                   metadata={})
```

### 3.3. Key Design Points & Future Considerations for `TechnicalBusController`

*   **Simplicity of Sequence Execution:** The `execute_block_sequence` in `TechnicalBusController` is intentionally simple (linear piping of `result` to `data`). More complex data aggregation, conditional logic, or parallelism between blocks would be orchestrated by the `ModuleBusController` using this Technical Bus as a primitive.
*   **Schema Validation:** Actual implementation of `_validate_data_with_schema` using `jsonschema` is crucial for robustness.
*   **Error Propagation:** Errors from `execute_single_block` (including schema validation failures) are propagated up.
*   **Instance vs. Runtime Config:**
    *   `instance_config` (passed to `_instantiate_block`): Static configuration for a block instance, set when it's conceptually "created" for a sequence/module.
    *   `input_payload.config` (passed to `execute_single_block`): Dynamic, per-execution configuration.
    *   The `ModuleBlueprintStep`'s `config_override` maps to `input_payload.config`. The source of `instance_config` for blocks within a sequence needs to be clarified in `ModuleBlueprint` if blocks need distinct static configs.
*   **Resource Management & Caching:** These are placeholders for significant future features. A `TechBlockResourceManager` would check `manifest.resource_requirements` and manage pools (e.g., GPU). A `TechBlockCache` would store results of deterministic blocks.
*   **Context (`execution_context`):** This dictionary needs a well-defined structure. It could provide access to shared services (like a configured `LLMInterface` instance, `ContextCore` client), user/session IDs, tracing IDs, etc., to avoid re-initializing them in every block.

## 4. Summary & Next Steps

This document details the `TechBlockLibrary` for managing Tech Block types and the `TechnicalBusController` for executing them.
The immediate next steps for detailed design within the Bus system would be:
1.  **Refine `TechBlock` ABC and concrete examples:** Ensure `get_class_manifest()` is well-defined and create a few sample Tech Blocks.
2.  **Design `ModuleBlueprint` in more detail:** Specify how `instance_config` for blocks within a blueprint step is defined, and how `input_mapping` from multiple prior steps will work.
3.  **Design `ModuleBusController`:** This controller will use `TechnicalBusController.execute_block_sequence` and handle the more complex assembly and data flow logic defined in `ModuleBlueprint`s.
4.  Implement actual schema validation.

These components form the foundational execution layer for the dynamic and modular Fragmenta architecture.
