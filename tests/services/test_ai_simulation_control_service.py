# tests/services/test_ai_simulation_control_service.py
import unittest
from unittest.mock import MagicMock, patch

from src.services.ai_simulation_control_service import AISimulationControlService
from src.services.resource_awareness_service import ResourceAwarenessService # For type mocking
from src.services.sandbox_executor import SandboxExecutor # Import SandboxExecutor
from src.shared.types.common_types import AIPermissionSet, ExecutionResult, SimulatedHardwareProfile

class TestAISimulationControlService(unittest.TestCase):

    def setUp(self):
        # Mock ResourceAwarenessService
        self.mock_resource_service = MagicMock(spec=ResourceAwarenessService)
        self.sample_hardware_profile: SimulatedHardwareProfile = { # type: ignore
            "profile_name": "TestProfile",
            "disk": {"space_gb": 100.0, "warning_threshold_percent": 80, "critical_threshold_percent": 95, "lag_factor_warning": 1.2, "lag_factor_critical": 2.0},
            "cpu": {"cores": 4},
            "ram": {"ram_gb": 16.0},
            "gpu_available": True
        }
        self.mock_resource_service.get_simulated_hardware_profile.return_value = self.sample_hardware_profile

        # Mock SandboxExecutor
        self.mock_sandbox_executor = MagicMock(spec=SandboxExecutor)
        # Default successful execution result from SandboxExecutor
        self.mock_sandbox_executor.execute_python_code.return_value = {
            "stdout": "Script executed successfully.",
            "stderr": "",
            "exit_code": 0,
            "is_compilation_error": False,
            "is_runtime_error": False
        }

        self.control_service = AISimulationControlService(
            resource_awareness_service=self.mock_resource_service,
            sandbox_executor=self.mock_sandbox_executor # Pass mock_sandbox_executor
        )

    def test_initialization(self):
        self.assertIsNotNone(self.control_service)
        self.assertEqual(self.control_service.resource_awareness_service, self.mock_resource_service)
        self.assertEqual(self.control_service.sandbox_executor, self.mock_sandbox_executor) # Check sandbox_executor
        default_perms = self.control_service.get_current_ai_permissions()
        self.assertTrue(default_perms["can_execute_code"])
        self.assertTrue(default_perms["can_read_sim_hw_status"])

    def test_initialization_raises_error_if_no_sandbox_executor(self):
        with self.assertRaises(ValueError) as context:
            AISimulationControlService(
                resource_awareness_service=self.mock_resource_service,
                sandbox_executor=None # type: ignore
            )
        self.assertIn("SandboxExecutor instance is required", str(context.exception))


    def test_load_ai_permissions(self):
        initial_perms = self.control_service.get_current_ai_permissions()
        self.assertTrue(initial_perms["can_execute_code"])

        new_perm_config = {"can_execute_code": False, "can_read_sim_hw_status": False}
        updated_perms = self.control_service.load_ai_permissions(new_perm_config) # type: ignore

        self.assertFalse(updated_perms["can_execute_code"])
        self.assertFalse(updated_perms["can_read_sim_hw_status"])
        self.assertNotIn("new_unwanted_key", updated_perms)

    def test_get_sim_hardware_status(self):
        hw_status = self.control_service.get_sim_hardware_status()
        self.assertIsNotNone(hw_status)
        self.assertEqual(hw_status.get("profile_name"), "TestProfile")
        # ... (other assertions remain the same)
        self.mock_resource_service.get_simulated_hardware_profile.assert_called_once()

    def test_get_sim_hardware_status_no_service(self):
        # Need to instantiate with mock_sandbox_executor for this test too
        service_no_ras = AISimulationControlService(
            resource_awareness_service=None,
            sandbox_executor=self.mock_sandbox_executor
        )
        hw_status = service_no_ras.get_sim_hardware_status()
        self.assertEqual(hw_status, {"status": "ResourceAwarenessService not configured."})

    def test_get_sim_hardware_status_service_returns_none(self):
        self.mock_resource_service.get_simulated_hardware_profile.return_value = None
        hw_status = self.control_service.get_sim_hardware_status()
        self.assertEqual(hw_status, {"error": "Hardware profile is None."})


    def test_execute_ai_code_success(self):
        code_to_run = "print('Hello from AI')"
        permissions = self.control_service.get_current_ai_permissions()

        result = self.control_service.execute_ai_code(code_to_run, permissions)

        self.assertTrue(result["execution_success"])
        self.assertEqual(result["script_exit_code"], 0)
        self.assertEqual(result["stdout"], "Script executed successfully.")
        self.assertEqual(result["status_message"], "Execution completed.")
        self.mock_sandbox_executor.execute_python_code.assert_called_once_with(code_to_run)


    def test_execute_ai_code_permission_denied(self):
        code_to_run = "print('This should not run')"
        permissions: AIPermissionSet = {
            "can_execute_code": False,
            "can_read_sim_hw_status": True
        }

        result = self.control_service.execute_ai_code(code_to_run, permissions)

        self.assertFalse(result["execution_success"])
        self.assertIsNone(result["script_exit_code"])
        self.assertIn("Execution denied", result["stderr"])
        self.assertIn("Insufficient permissions", result["status_message"])
        self.mock_sandbox_executor.execute_python_code.assert_not_called()

    def test_execute_ai_code_script_compilation_error(self):
        code_to_run = "print 'bad syntax'" # Python 2 syntax
        permissions = self.control_service.get_current_ai_permissions()

        self.mock_sandbox_executor.execute_python_code.return_value = {
            "stdout": "",
            "stderr": "SyntaxError: Missing parentheses in call to 'print'",
            "exit_code": 1, # Or another non-zero code
            "is_compilation_error": True,
            "is_runtime_error": False
        }

        result = self.control_service.execute_ai_code(code_to_run, permissions)

        self.assertTrue(result["execution_success"]) # ASCS attempted execution
        self.assertEqual(result["script_exit_code"], 1)
        self.assertIn("SyntaxError", result["stderr"])
        self.assertEqual(result["status_message"], "Script compilation error.")
        self.mock_sandbox_executor.execute_python_code.assert_called_once_with(code_to_run)

    def test_execute_ai_code_script_runtime_error(self):
        code_to_run = "raise ValueError('AI script error')"
        permissions = self.control_service.get_current_ai_permissions()

        self.mock_sandbox_executor.execute_python_code.return_value = {
            "stdout": "",
            "stderr": "Traceback...\nValueError: AI script error",
            "exit_code": 1,
            "is_compilation_error": False,
            "is_runtime_error": True
        }

        result = self.control_service.execute_ai_code(code_to_run, permissions)

        self.assertTrue(result["execution_success"])
        self.assertEqual(result["script_exit_code"], 1)
        self.assertIn("AI script error", result["stderr"])
        self.assertEqual(result["status_message"], "Script execution failed with exit code 1.")
        self.mock_sandbox_executor.execute_python_code.assert_called_once_with(code_to_run)

    def test_execute_ai_code_sandbox_timeout(self):
        code_to_run = "while True: pass"
        permissions = self.control_service.get_current_ai_permissions()

        self.mock_sandbox_executor.execute_python_code.return_value = {
            "stdout": "",
            "stderr": "Sandbox execution timed out after 5 seconds.",
            "exit_code": -1, # Example timeout exit code from SandboxExecutor
            "is_compilation_error": False,
            "is_runtime_error": True
        }

        result = self.control_service.execute_ai_code(code_to_run, permissions)

        self.assertTrue(result["execution_success"])
        self.assertEqual(result["script_exit_code"], -1)
        self.assertIn("timed out", result["stderr"].lower())
        self.assertEqual(result["status_message"], "Script execution timed out.")
        self.mock_sandbox_executor.execute_python_code.assert_called_once_with(code_to_run)


    def test_execute_ai_code_sandbox_executor_system_error(self):
        code_to_run = "print('test')"
        permissions = self.control_service.get_current_ai_permissions()

        # Simulate SandboxExecutor itself raising an unhandled exception
        self.mock_sandbox_executor.execute_python_code.side_effect = Exception("Sandbox system failure")

        result = self.control_service.execute_ai_code(code_to_run, permissions)

        self.assertFalse(result["execution_success"]) # ASCS failed to get a proper result
        self.assertIsNone(result["script_exit_code"])
        self.assertEqual(result["stderr"], "System error during execution: Sandbox system failure")
        self.assertEqual(result["status_message"], "System error prevented or interrupted execution.")


if __name__ == '__main__':
    unittest.main()
