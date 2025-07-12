from typing import Dict, Any, Optional, List
from ..common.data_models import TechBlockInput, TechBlockOutput, ModuleBlueprintStep, TechBlockManifest
from ..common.tech_block_interface import TechBlock
from ..tech_blocks.library import TechBlockLibrary, TechBlockNotFoundError, TechBlockRegistrationError

class TechnicalBusExecutionError(Exception):
    pass

class TechnicalBusController:
    """
    Controls the instantiation and execution of TechBlocks.
    Manages data flow for sequences of TechBlocks defined by ModuleBlueprintSteps.
    """
    _library: TechBlockLibrary

    def __init__(self, library: TechBlockLibrary):
        if not isinstance(library, TechBlockLibrary):
            raise TypeError("library must be an instance of TechBlockLibrary")
        self._library = library

    def _instantiate_block(self, block_manifest_id: str, instance_run_id: str, version_override: Optional[str] = None, instance_config: Optional[Dict[str, Any]] = None) -> TechBlock:
        """
        Helper to get class from library and instantiate a TechBlock.
        """
        try:
            block_class = self._library.get_block_class(block_manifest_id)

            actual_version = version_override
            if not actual_version:
                class_manifest = block_class.get_class_manifest()
                actual_version = class_manifest.get("version", "0.0.0")

            block_instance = block_class(
                block_id=instance_run_id,
                version=actual_version,
                config=instance_config or {}
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
        # import jsonschema # Uncomment if jsonschema is used
        if schema:
            # try:
            #     jsonschema.validate(instance=data_instance, schema=schema)
            # except jsonschema.exceptions.ValidationError as e:
            #     raise TechnicalBusExecutionError(f"Schema validation failed for {block_id_for_error} {validation_context}: {e.message}")
            pass
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
        """
        effective_instance_run_id = instance_run_id or f"{block_manifest_id}_exec_{abs(hash(str(input_payload)))}"

        try:
            block_instance = self._instantiate_block(block_manifest_id, effective_instance_run_id, instance_config=instance_config)
            manifest = block_instance.get_manifest()

            self._validate_data_with_schema(input_payload.get('data'), manifest.get('input_schema'), block_manifest_id, "input")
            self._validate_data_with_schema(input_payload.get('config'), manifest.get('config_schema'), block_manifest_id, "runtime config")

            output = await block_instance.execute(input_payload, execution_context)

            self._validate_data_with_schema(output.get('result'), manifest.get('output_schema'), block_manifest_id, "output")

            return output

        except TechBlockNotFoundError:
            return TechBlockOutput(result=None, status="error", error_message=f"TechBlock type '{block_manifest_id}' not found in library.", metadata={"block_id": block_manifest_id, "instance_run_id": effective_instance_run_id})
        except TechnicalBusExecutionError as e:
             return TechBlockOutput(result=None, status="error", error_message=str(e), metadata={"block_id": block_manifest_id, "instance_run_id": effective_instance_run_id})
        except Exception as e:
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
        """
        current_block_data_payload = initial_sequence_input

        for i, step_def in enumerate(blueprint_steps):
            block_manifest_id = step_def["block_manifest_id"]
            runtime_config_override = step_def.get("config_override")
            instance_config_for_step = step_def.get("instance_config") # Use instance_config from step_def

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
                return step_output

            current_block_data_payload = step_output.get("result")

        if 'step_output' in locals():
            return step_output
        else:
            return TechBlockOutput(result=initial_sequence_input if not blueprint_steps else None,
                                   status="success" if not blueprint_steps else "error",
                                   error_message="No steps in blueprint." if blueprint_steps else None,
                                   metadata={})
