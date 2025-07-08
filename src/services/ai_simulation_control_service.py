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
# Import SandboxExecutor
from src.services.sandbox_executor import SandboxExecutor


class AISimulationControlService:
    def __init__(self,
                 resource_awareness_service: Optional[ResourceAwarenessService],
                 sandbox_executor: SandboxExecutor):
        self.resource_awareness_service = resource_awareness_service
        self.current_permissions: AIPermissionSet = self._load_default_permissions()

        if sandbox_executor is None:
            raise ValueError("SandboxExecutor instance is required for AISimulationControlService.")
        self.sandbox_executor: SandboxExecutor = sandbox_executor

        print("AISimulationControlService initialized with SandboxExecutor.")

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


        print(f"ASCS: Executing AI code via SandboxExecutor for request_id: {request_id}")
        try:
            # Use SandboxExecutor to run the code string directly
            exec_details = self.sandbox_executor.execute_python_code(code_string)

            stdout = exec_details.get("stdout", "")
            stderr = exec_details.get("stderr", "")
            exit_code = exec_details.get("exit_code", -1) # Default to -1 if not present

            # Determine status message based on outcome
            status_message = "Execution completed."
            if exec_details.get("is_compilation_error"):
                status_message = "Script compilation error."
            elif exec_details.get("is_runtime_error"): # Covers script runtime errors and timeouts
                if "timed out" in stderr.lower(): # Check if timeout was the cause
                    status_message = "Script execution timed out."
                else:
                    status_message = f"Script execution failed with exit code {exit_code}."
            elif exit_code != 0 : # Other non-zero exits without specific error flags
                 status_message = f"Script execution finished with non-zero exit code {exit_code}."


            print(f"ASCS: Code execution result - Exit Code: {exit_code}, Stdout: {stdout[:100]}..., Stderr: {stderr[:100]}...")

            # Note: 'execution_success' in ExecutionResult means the system *attempted* execution.
            # Script errors (non-zero exit code, stderr) are part of a "successful" system attempt.
            # System errors in SandboxExecutor (e.g., timeout, setup failure) will result in specific negative exit_codes
            # and error messages in stderr from SandboxExecutor itself.
            return {
                "request_id": request_id,
                "execution_success": True, # ASCS successfully invoked SandboxExecutor
                "script_exit_code": exit_code,
                "stdout": stdout,
                "stderr": stderr,
                "status_message": status_message
            }

        except Exception as e:
            # This catches unexpected errors within ASCS itself or if SandboxExecutor raises an unhandled exception
            print(f"ASCS: System error during AI code execution orchestration: {e}")
            return {
                "request_id": request_id,
                "execution_success": False, # System error before/during script attempt
                "script_exit_code": None,
                "stdout": "",
                "stderr": f"System error during execution: {str(e)}",
                "status_message": "System error prevented or interrupted execution."
            }

print("AISimulationControlService module loaded.")
