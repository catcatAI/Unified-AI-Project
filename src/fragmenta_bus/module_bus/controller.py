from typing import Dict, Any, Optional, List, Union, Literal, cast, Tuple
from src.fragmenta_bus.common.data_models import (
    ModuleBlueprint, ModuleBlueprintStep, TechBlockInput, TechBlockOutput,
    InputSourceMappingValue, AssembledModuleInstanceID
)
from src.fragmenta_bus.technical_bus.controller import TechnicalBusController

class ModuleAssemblyError(Exception):
    pass

class ModuleExecutionError(Exception):
    pass

class AssembledModuleInstance:
    """
    Represents an executable instance of a Module for a single invocation.
    Holds the state of that specific run (initial inputs, intermediate step outputs).
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
        """
        Helper to resolve a dot-and-bracket notation path from a source object.
        Supports nested dicts and list indices.
        """
        current = source
        try:
            parts = path_str.replace("[", ".[").split(".")
            for part in parts:
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

            if is_single_source_map:
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

    def __init__(self, technical_bus: TechnicalBusController):
        self._technical_bus = technical_bus
        self._blueprint_registry = {}

    def register_blueprint(self, blueprint: ModuleBlueprint) -> None:
        blueprint_id = blueprint.get("id")
        if not blueprint_id:
            raise ModuleAssemblyError("ModuleBlueprint must have an 'id'.")
        if blueprint_id in self._blueprint_registry:
            raise ModuleAssemblyError(f"ModuleBlueprint with ID '{blueprint_id}' already registered.")
        self._blueprint_registry[blueprint_id] = blueprint

    def get_blueprint(self, blueprint_id: str) -> Optional[ModuleBlueprint]:
        return self._blueprint_registry.get(blueprint_id)

    def _validate_module_data(self, data: Any, schema: Optional[Dict[str, Any]], blueprint_id_for_error: str, context_msg: str) -> None:
        """
        Validates module's initial input or final output against its schema.
        """
        # import jsonschema # Uncomment if jsonschema is used
        if schema:
            # try:
            #     jsonschema.validate(instance=data, schema=schema)
            # except jsonschema.exceptions.ValidationError as e:
            #     raise ModuleExecutionError(f"Module '{blueprint_id_for_error}' {context_msg} schema validation failed: {e.message}")
            pass
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
                    return step_output

            final_module_result = module_instance._build_payload_from_mapping(blueprint["final_output_mapping"])
            self._validate_module_data(final_module_result, blueprint.get("output_schema"), blueprint_id, "final output")

            module_instance.final_result = final_module_result
            module_instance.status = "completed"

            return TechBlockOutput(result=final_module_result, status="success", error_message=None, metadata={"module_id": blueprint_id, "instance_id": module_instance.instance_id})

        except ModuleExecutionError as e:
            return TechBlockOutput(result=None, status="error", error_message=str(e), metadata={"module_id": blueprint_id})
        except Exception as e:
            error_type = type(e).__name__
            return TechBlockOutput(result=None, status="error", error_message=f"Unexpected error in module '{blueprint_id}': {error_type} - {str(e)}", metadata={"module_id": blueprint_id})