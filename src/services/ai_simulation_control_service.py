# src/services/ai_simulation_control_service.py
"""
AI Simulation Control Service (ASCS)

This service is responsible for managing and controlling AI actions within
the simulation environment, particularly focusing on:
- AI Permissions: Loading, checking, and enforcing permissions for AI operations.
- Resource Awareness: Interfacing with the ResourceAwarenessService to provide
  simulated hardware status to the AI and potentially influence AI action feasibility.
- AI Code Execution: Securely executing code generated or provided by the AI,
  subject to permissions and resource constraints.
"""

import uuid
from typing import Dict, Any, Optional

# Assuming common_types.py contains AIPermissionSet, ExecutionResult
from src.shared.types.common_types import (
    AIPermissionSet,
    ExecutionResult
)
# Assuming ResourceAwarenessService is in the same directory or correctly pathed
from src.services.resource_awareness_service import ResourceAwarenessService

# Placeholder for run_in_bash_session - this will be provided by the Jules environment
# For local testing, one might create a mock.
class MockBashSessionRunner:
    def run_in_bash_session(self, command: str) -> Dict[str, Any]:
        print(f"MockBashSessionRunner: Would run '{command}'")
        # Simulate a successful python script execution
        if command.startswith("python"):
            return {
                "stdout": "Mock script output\n",
                "stderr": "",
                "exit_code": 0
            }
        return {
            "stdout": f"Mock output for {command}\n",
            "stderr": "",
            "exit_code": 0
        }

class AISimulationControlService:
    def __init__(self,
                 resource_awareness_service: Optional[ResourceAwarenessService],
                 bash_runner: Optional[Any] = None): # bash_runner for run_in_bash_session
        self.resource_awareness_service = resource_awareness_service
        self.current_permissions: AIPermissionSet = self._load_default_permissions()

        # This is where the actual run_in_bash_session tool will be used.
        # If not provided (e.g. in some unit tests), use a mock.
        self.bash_runner = bash_runner if bash_runner else MockBashSessionRunner()

        print("AISimulationControlService initialized.")

    def _load_default_permissions(self) -> AIPermissionSet:
        """Loads a default set of AI permissions. For now, hardcoded."""
        # In the future, this could load from a config file or dynamic source.
        permissions: AIPermissionSet = {
            "can_execute_code": True,  # Defaulting to True for development, review for production
            "can_read_sim_hw_status": True,
            "allowed_execution_paths": None, # Not yet implemented
            "allowed_service_imports": None, # Not yet implemented
            "max_execution_time_ms": None    # Not yet implemented
        }
        print(f"ASCS: Default AI permissions loaded: {permissions}")
        return permissions

    def load_ai_permissions(self, config: Dict[str, Any]) -> AIPermissionSet:
        """
        Loads AI permissions from a given configuration dictionary.
        This allows dynamic updating of permissions.
        """
        # Basic implementation: overwrite known keys if present in config
        # More robust implementation would involve validation
        new_permissions = self.current_permissions.copy()
        for key, value in config.items():
            if key in new_permissions: # type: ignore # TODO: Fix this TypedDict key check
                new_permissions[key] = value # type: ignore

        self.current_permissions = new_permissions
        print(f"ASCS: AI permissions updated: {self.current_permissions}")
        return self.current_permissions

    def get_current_ai_permissions(self) -> AIPermissionSet:
        """Returns the currently active AI permission set."""
        return self.current_permissions.copy() # Return a copy to prevent direct modification

    def get_sim_hardware_status(self) -> Dict[str, Any]:
        """
        Retrieves the current simulated hardware status from the ResourceAwarenessService.
        Returns an empty dict if the service is not available.
        """
        if self.resource_awareness_service:
            # Assuming ResourceAwarenessService has a method like get_all_resource_statuses()
            # or specific methods to get CPU, memory, disk, etc.
            # For now, let's assume it has a simple method returning a dict.
            # This part needs to align with ResourceAwarenessService's actual interface.
            try:
                # The actual method in ResourceAwarenessService is get_simulated_hardware_profile()
                # which returns a SimulatedHardwareProfile TypedDict.
                profile = self.resource_awareness_service.get_simulated_hardware_profile()
                if profile:
                    # Extract relevant parts into a simpler dict for AVIS display
                    hw_status: Dict[str, Any] = {
                        "profile_name": profile.get("profile_name", "Unknown"),
                        "disk_space_gb": profile.get("disk", {}).get("space_gb"),
                        "cpu_cores": profile.get("cpu", {}).get("cores"),
                        "ram_gb": profile.get("ram", {}).get("ram_gb"),
                        "gpu_available": profile.get("gpu_available", False)
                        # Add more details as needed for the AI to see
                    }
                    return hw_status
                else:
                    return {"error": "Hardware profile is None."}
            except Exception as e:
                print(f"ASCS: Error getting hardware status from ResourceAwarenessService: {e}")
                return {"error": "Failed to retrieve hardware status."}
        else:
            print("ASCS: ResourceAwarenessService not available.")
            return {"status": "ResourceAwarenessService not configured."}

    def execute_ai_code(self, code_string: str, permissions_context: AIPermissionSet) -> ExecutionResult:
        """
        Executes a string of Python code provided by the AI, subject to permissions.

        Args:
            code_string (str): The Python code to execute.
            permissions_context (AIPermissionSet): The permissions under which to run the code.

        Returns:
            ExecutionResult: An object containing the outcome of the execution.
        """
        request_id = str(uuid.uuid4())

        if not permissions_context.get("can_execute_code", False):
            print("ASCS: Code execution denied due to permissions.")
            return {
                "request_id": request_id,
                "execution_success": False,
                "script_exit_code": None,
                "stdout": "",
                "stderr": "Execution denied: 'can_execute_code' permission is false.",
                "status_message": "Execution denied: Insufficient permissions."
            }

        # Basic check for Python code (very naive)
        if not ("def " in code_string or "print(" in code_string or "import " in code_string or "=" in code_string):
             # This is a weak check, can be improved or made language-specific if needed
            print(f"ASCS: Code execution attempted with potentially non-Python or trivial code: {code_string[:100]}")
            # Depending on policy, we might reject or proceed. For now, proceed but log.

        temp_script_name = f"/tmp/ai_script_{request_id}.py" # Using /tmp for sandbox

        try:
            # This is where I (Jules) would use my 'create_file_with_block' tool.
            # Since ASCS is being written by me, it can't directly call that tool.
            # The simulation here is that the file gets created.
            # In a real scenario, the agent controlling Jules would make the file.
            # For now, we'll assume the bash_runner handles file creation implicitly if needed,
            # or that the python command can take a string directly (which it can't for complex scripts).
            # So, we MUST simulate writing the file for the `python <filepath>` command to work.

            # Simulating file creation for the bash runner:
            # The bash_runner will execute `python /tmp/ai_script_{request_id}.py`
            # It needs the file to exist. The `run_in_bash_session` tool operates within a sandbox
            # that has its own filesystem. I need to ensure the file is created there.
            # This is a bit meta: I am writing code that will later use a tool I provide.
            # The `self.bash_runner.create_file(temp_script_name, code_string)` is conceptual
            # if `bash_runner` is the actual Jules tool proxy.
            # Let's assume for now the tool can handle `echo "..." > file && python file`.

            # A safer way for run_in_bash_session:
            # 1. Escape the code_string for shell injection.
            # 2. Use echo to write to file.
            # This is still tricky. The best way is if `run_in_bash_session` had a companion
            # `create_file_in_session_sandbox(filepath, content)` method.
            # Lacking that, constructing the command:

            # Simplified approach for now: Assume self.bash_runner is a proxy to Jules's tools
            # and it can handle a "run_python_script_from_string" abstraction or we build it here.
            # For now, let's stick to the plan of writing to a temp file then executing.
            # This implies the AISimulationControlService needs a way to tell Jules to make the file.
            # This is a gap. For now, the `self.bash_runner` will be a mock that doesn't *actually*
            # use Jules's real tools, but simulates the outcome.
            # When Jules *uses* AISimulationControlService, Jules will provide its *actual* bash_runner.

            # If self.bash_runner is the actual tool, it doesn't have a 'create_file' method.
            # I must use the tools I have.
            # This means AISimulationControlService cannot *itself* call create_file_with_block.
            # This service is being *written by* me.
            # The entity *calling* execute_ai_code would need to ensure the script exists,
            # or this service needs to return a structure that tells the caller to create it.
            # This is getting too complex for this step.
            # Plan: For this step, `execute_ai_code` will *prepare* the command, but the
            # `run_in_bash_session` call will be made by the code that *uses* this service,
            # or we assume the bash_runner mock handles it.
            # For now, the mock `self.bash_runner` will simulate this.

            # Let's assume the bash_runner is sophisticated enough or is a stand-in for Jules's capabilities
            # For the real implementation where Jules provides its `run_in_bash_session`:
            # Command to create file and run:
            # Need to escape single quotes in code_string if using single quotes for echo
            escaped_code_string = code_string.replace("'", "'\\''") # Basic escape for `echo '...'`
            command = f"echo '{escaped_code_string}' > {temp_script_name} && python {temp_script_name} && rm {temp_script_name}"

            print(f"ASCS: Executing AI code via bash_runner. Command (simplified for log): python {temp_script_name}")
            # The real command is more complex due to file creation.

            # If self.bash_runner is a direct proxy to Jules's `run_in_bash_session` tool:

            # The bash_runner is expected to be a callable that takes a command string
            # and returns a dictionary with 'stdout', 'stderr', and 'exit_code'.
            # This aligns with how Jules's `run_in_bash_session` tool behaves
            # when wrapped or passed as a function.
            if not callable(self.bash_runner):
                raise TypeError("bash_runner is not callable. It must be a function or a callable object.")

            result_dict = self.bash_runner(command) # Directly call the provided bash_runner

            stdout = result_dict.get("stdout", "")
            stderr = result_dict.get("stderr", "")
            exit_code = result_dict.get("exit_code", -1)

            print(f"ASCS: Code execution result - Exit Code: {exit_code}, Stdout: {stdout[:100]}..., Stderr: {stderr[:100]}...")

            return {
                "request_id": request_id,
                "execution_success": True, # Script was attempted
                "script_exit_code": exit_code,
                "stdout": stdout,
                "stderr": stderr,
                "status_message": "Execution completed." if exit_code == 0 else f"Script execution failed with exit code {exit_code}."
            }

        except Exception as e:
            print(f"ASCS: Error during AI code execution process: {e}")
            return {
                "request_id": request_id,
                "execution_success": False, # System error before/during script attempt
                "script_exit_code": None,
                "stdout": "",
                "stderr": f"System error during execution: {str(e)}",
                "status_message": "System error prevented or interrupted execution."
            }

print("AISimulationControlService module loaded.")
