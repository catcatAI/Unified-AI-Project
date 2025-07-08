# examples/run_simple_coding_agent.py
"""
Driver script to instantiate and run the SimpleCodingAgent.
This script sets up the necessary services (AIVIS, ResourceAwarenessService)
and a basic virtual UI for the agent to interact with.
"""
import os
import sys
from typing import Dict, Any, List

# Adjust path to import from src
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.insert(0, project_root)

from src.services.resource_awareness_service import ResourceAwarenessService
from src.services.ai_virtual_input_service import AIVirtualInputService
from src.services.sandbox_executor import SandboxExecutor # Import SandboxExecutor
from src.agents.simple_coding_agent import SimpleCodingAgent
from src.shared.types.common_types import VirtualInputElementDescription

def main():
    print("--- Setting up environment for SimpleCodingAgent ---")

    # 0. Instantiate SandboxExecutor
    # This will use its default timeout.
    print("Initializing SandboxExecutor...")
    sandbox_executor = SandboxExecutor()

    # 1. Instantiate ResourceAwarenessService
    # Ensure 'configs/simulated_resources.yaml' exists or provide a valid path.
    # For this example, let's assume it can find the default or use a safe default.
    try:
        config_path = os.path.join(project_root, "configs", "simulated_resources.yaml")
        if not os.path.exists(config_path):
            print(f"Warning: Config file not found at {config_path}. ResourceAwarenessService might use defaults.")
            # Create a dummy one if it absolutely needs to exist for the service not to fail init hard
            if not os.path.exists(os.path.join(project_root, "configs")):
                 os.makedirs(os.path.join(project_root, "configs"))
            with open(config_path, 'w') as f:
                f.write("""
simulated_hardware_profile:
  profile_name: ExampleDefaultProfileFromDriver
  disk:
    space_gb: 100.0
    warning_threshold_percent: 80.0
    critical_threshold_percent: 95.0
    lag_factor_warning: 1.0
    lag_factor_critical: 1.0
  cpu:
    cores: 2
  ram:
    ram_gb: 4.0
  gpu_available: false
""")
            print(f"Created a dummy config file at {config_path}")
        resource_service = ResourceAwarenessService(config_filepath=config_path)
    except Exception as e:
        print(f"Failed to initialize ResourceAwarenessService: {e}")
        print("Continuing with ResourceAwarenessService as None, ASCS might use defaults for HW status.")
        resource_service = None


    # 2. Instantiate AIVirtualInputService
    # Pass the real SandboxExecutor instance
    print("Initializing AIVirtualInputService...")
    avis_service = AIVirtualInputService(
        resource_awareness_service=resource_service,
        sandbox_executor=sandbox_executor # Pass the actual SandboxExecutor
    )

    # 3. Define and load the virtual UI
    # These IDs must match what SimpleCodingAgent expects
    virtual_ui: List[VirtualInputElementDescription] = [
        {"element_id": "code_editor", "element_type": "text_area", "value": "", "label_text": "Code Editor"}, #type: ignore
        {"element_id": "run_code_button", "element_type": "button", "label_text": "Run Code"}, #type: ignore
        {"element_id": "code_output_display", "element_type": "text_area", "value": "--- Output ---", "read_write": False, "label_text": "Output"}, #type: ignore
        {"element_id": "ai_permissions_display", "element_type": "text_area", "value": "Permissions: Pending...", "read_write": False, "label_text": "AI Permissions"}, #type: ignore
        {"element_id": "sim_hw_status_display", "element_type": "text_area", "value": "HW Status: Pending...", "read_write": False, "label_text": "Simulated HW Status"} #type: ignore
    ]
    avis_service.load_virtual_ui(virtual_ui)

    # Manually trigger a refresh so the permission/hw displays get populated before agent runs
    # (In a real scenario, agent might need to wait or be robust to initial empty states)
    print("\nDriver: Refreshing AVIS simulation status before agent run...")
    avis_service.refresh_simulation_status()


    # 4. Instantiate SimpleCodingAgent
    print("\n--- Initializing SimpleCodingAgent ---")
    agent = SimpleCodingAgent(avis_service=avis_service)

    # 5. Call the agent's run_task() method
    print("\n--- Running SimpleCodingAgent Task ---")
    agent.run_task()

    print("\n--- SimpleCodingAgent Task Finished ---")

    # Optional: Inspect final AVIS state
    # print("\nFinal AVIS UI State:")
    # for element in avis_service.get_current_virtual_ui():
    #     print(f"  Element ID: {element.get('element_id')}, Value: {element.get('value')}")
    # print("\nFinal AVIS Action Log:")
    # for log_entry in avis_service.get_action_log():
    #     print(log_entry)

if __name__ == "__main__":
    main()
