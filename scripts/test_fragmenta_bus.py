import asyncio
import os
import sys

# Add project root to sys.path for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from src.fragmenta_bus.tech_blocks.library import TechBlockLibrary, TechBlockNotFoundError, TechBlockRegistrationError
from src.fragmenta_bus.technical_bus.controller import TechnicalBusController, TechnicalBusExecutionError
from src.fragmenta_bus.module_bus.controller import ModuleBusController, ModuleAssemblyError, ModuleExecutionError
from src.fragmenta_bus.tech_blocks.implementations.echo_block import EchoBlock
from src.fragmenta_bus.tech_blocks.implementations.concatenate_block import StringConcatenateBlock
from src.fragmenta_bus.common.data_models import ModuleBlueprint, TechBlockInput, TechBlockOutput, SemanticTaskRequest, UserContext

async def main_test_fragmenta_bus():
    print("--- Fragmenta Bus System Integration Test ---")

    # 1. Initialize TechBlockLibrary and register blocks
    tech_block_library = TechBlockLibrary()
    try:
        tech_block_library.register_block(EchoBlock)
        tech_block_library.register_block(StringConcatenateBlock)
        print("TechBlocks registered successfully.")
    except TechBlockRegistrationError as e:
        print(f"Error registering TechBlock: {e}")
        return

    # 2. Initialize TechnicalBusController
    technical_bus = TechnicalBusController(library=tech_block_library)
    print("TechnicalBusController initialized.")

    # 3. Initialize ModuleBusController
    module_bus = ModuleBusController(technical_bus=technical_bus)
    print("ModuleBusController initialized.")

    # 4. Define and register a simple ModuleBlueprint
    # This blueprint will echo a string, then concatenate it with itself
    simple_module_blueprint: ModuleBlueprint = {
        "id": "test.simple_echo_concat.v1",
        "name": "Test Echo and Concatenate Module",
        "version": "1.0.0",
        "description": "Echoes input and then concatenates it with a separator.",
        "input_schema": {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]},
        "output_schema": {"type": "object", "properties": {"result": {"type": "string"}}, "required": ["result"]},
        "steps": [
            {
                "step_id": "echo_step",
                "block_manifest_id": "core.echo.v1",
                "input_data_mapping": {"data": {"initial_module_input_field": "text"}},
                "instance_config": {"prefix": "Echoed: "}
            },
            {
                "step_id": "concat_step",
                "block_manifest_id": "core.string.concatenate.v1",
                "input_data_mapping": {
                    "string1": {"source_step_id": "echo_step", "source_step_output_field": "result"},
                    "string2": {"literal_value": " (processed)"}
                },
                "instance_config": {"separator": "--"}
            }
        ],
        "final_output_mapping": {"source_step_id": "concat_step", "source_step_output_field": "result"}
    }

    try:
        module_bus.register_blueprint(simple_module_blueprint)
        print(f"ModuleBlueprint '{simple_module_blueprint['id']}' registered successfully.")
    except ModuleAssemblyError as e:
        print(f"Error registering blueprint: {e}")
        return

    # 5. Invoke the module
    test_input_text = "Hello Fragmenta"
    print(f"\nInvoking module with input: '{test_input_text}'")
    module_result = await module_bus.invoke_module(
        blueprint_id=simple_module_blueprint['id'],
        initial_module_input_data={"text": test_input_text},
        module_execution_context={
            "user_id": "test_user_1",
            "session_id": "test_session_1"
        }
    )

    print("\nModule Invocation Result:")
    print(f"  Status: {module_result['status']}")
    print(f"  Result: {module_result.get('result')}")
    print(f"  Error: {module_result.get('error_message')}")

    # Assertions
    assert module_result['status'] == "success"
    assert module_result.get('result') == "Echoed: Hello Fragmenta--(processed)"
    print("Assertion PASSED: Module output is as expected.")

    print("\n--- Fragmenta Bus System Integration Test Finished Successfully ---")

if __name__ == "__main__":
    asyncio.run(main_test_fragmenta_bus())
