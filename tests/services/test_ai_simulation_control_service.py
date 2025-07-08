# tests/services/test_ai_simulation_control_service.py
import unittest
from unittest.mock import MagicMock, patch

from src.services.ai_simulation_control_service import AISimulationControlService
from src.services.resource_awareness_service import ResourceAwarenessService # For type mocking
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

        # Mock bash_runner (simulates run_in_bash_session tool)
        self.mock_bash_runner = MagicMock(return_value={
            "stdout": "Script executed successfully.",
            "stderr": "",
            "exit_code": 0
        })

        self.control_service = AISimulationControlService(
            resource_awareness_service=self.mock_resource_service,
            bash_runner=self.mock_bash_runner
        )

    def test_initialization(self):
        self.assertIsNotNone(self.control_service)
        self.assertEqual(self.control_service.resource_awareness_service, self.mock_resource_service)
        self.assertEqual(self.control_service.bash_runner, self.mock_bash_runner)
        default_perms = self.control_service.get_current_ai_permissions()
        self.assertTrue(default_perms["can_execute_code"]) # Based on current default in ASCS
        self.assertTrue(default_perms["can_read_sim_hw_status"])

    def test_load_ai_permissions(self):
        initial_perms = self.control_service.get_current_ai_permissions()
        self.assertTrue(initial_perms["can_execute_code"])

        new_perm_config = {"can_execute_code": False, "can_read_sim_hw_status": False}
        updated_perms = self.control_service.load_ai_permissions(new_perm_config) # type: ignore

        self.assertFalse(updated_perms["can_execute_code"])
        self.assertFalse(updated_perms["can_read_sim_hw_status"])
        # Ensure it doesn't add new keys not in AIPermissionSet (implicit test by structure)
        self.assertNotIn("new_unwanted_key", updated_perms)

    def test_get_sim_hardware_status(self):
        hw_status = self.control_service.get_sim_hardware_status()
        self.assertIsNotNone(hw_status)
        self.assertEqual(hw_status.get("profile_name"), "TestProfile")
        self.assertEqual(hw_status.get("disk_space_gb"), 100.0)
        self.assertEqual(hw_status.get("cpu_cores"), 4)
        self.assertEqual(hw_status.get("ram_gb"), 16.0)
        self.assertTrue(hw_status.get("gpu_available"))
        self.mock_resource_service.get_simulated_hardware_profile.assert_called_once()

    def test_get_sim_hardware_status_no_service(self):
        service_no_ras = AISimulationControlService(resource_awareness_service=None, bash_runner=self.mock_bash_runner)
        hw_status = service_no_ras.get_sim_hardware_status()
        self.assertEqual(hw_status, {"status": "ResourceAwarenessService not configured."})

    def test_get_sim_hardware_status_service_returns_none(self):
        self.mock_resource_service.get_simulated_hardware_profile.return_value = None
        hw_status = self.control_service.get_sim_hardware_status()
        self.assertEqual(hw_status, {"error": "Hardware profile is None."})


    def test_execute_ai_code_success(self):
        code_to_run = "print('Hello from AI')"
        permissions = self.control_service.get_current_ai_permissions() # Use current (default true)

        result = self.control_service.execute_ai_code(code_to_run, permissions)

        self.assertTrue(result["execution_success"])
        self.assertEqual(result["script_exit_code"], 0)
        self.assertEqual(result["stdout"], "Script executed successfully.")
        self.assertEqual(result["status_message"], "Execution completed.")
        self.mock_bash_runner.assert_called_once()
        # Check that the command passed to bash_runner is correct
        args, _ = self.mock_bash_runner.call_args
        command_str = args[0]
        # Account for single quote escaping in the command
        escaped_code_to_run = code_to_run.replace("'", "'\\''")
        self.assertIn(f"echo '{escaped_code_to_run}' > /tmp/ai_script_", command_str)
        self.assertIn(f"&& python /tmp/ai_script_", command_str)
        self.assertIn(f"&& rm /tmp/ai_script_", command_str)


    def test_execute_ai_code_permission_denied(self):
        code_to_run = "print('This should not run')"
        permissions: AIPermissionSet = {
            "can_execute_code": False, # Explicitly deny
            "can_read_sim_hw_status": True
        }

        result = self.control_service.execute_ai_code(code_to_run, permissions)

        self.assertFalse(result["execution_success"])
        self.assertIsNone(result["script_exit_code"])
        self.assertIn("Execution denied", result["stderr"])
        self.assertIn("Insufficient permissions", result["status_message"])
        self.mock_bash_runner.assert_not_called()

    def test_execute_ai_code_script_error(self):
        code_to_run = "raise ValueError('AI script error')"
        permissions = self.control_service.get_current_ai_permissions()

        self.mock_bash_runner.return_value = {
            "stdout": "",
            "stderr": "Traceback...\nValueError: AI script error",
            "exit_code": 1
        }

        result = self.control_service.execute_ai_code(code_to_run, permissions)

        self.assertTrue(result["execution_success"]) # System executed it, script failed
        self.assertEqual(result["script_exit_code"], 1)
        self.assertIn("AI script error", result["stderr"])
        self.assertIn("Script execution failed with exit code 1", result["status_message"])
        self.mock_bash_runner.assert_called_once()

    def test_execute_ai_code_bash_runner_exception(self):
        code_to_run = "print('test')"
        permissions = self.control_service.get_current_ai_permissions()

        self.mock_bash_runner.side_effect = Exception("Bash runner system failure")

        result = self.control_service.execute_ai_code(code_to_run, permissions)

        self.assertFalse(result["execution_success"])
        self.assertIsNone(result["script_exit_code"])
        self.assertIn("System error during execution: Bash runner system failure", result["stderr"])
        self.assertEqual(result["status_message"], "System error prevented or interrupted execution.")

    def test_execute_ai_code_non_callable_bash_runner(self):
        code_to_run = "print('hello')"
        permissions = self.control_service.get_current_ai_permissions()

        service_bad_runner = AISimulationControlService(
            resource_awareness_service=self.mock_resource_service,
            bash_runner="not_a_callable" # type: ignore
        )
        result = service_bad_runner.execute_ai_code(code_to_run, permissions)

        self.assertFalse(result["execution_success"])
        self.assertIsNone(result["script_exit_code"])
        # The str(e) for TypeError in this case is just the message, not "TypeError(...)".
        self.assertEqual(result["stderr"], "System error during execution: bash_runner is not callable. It must be a function or a callable object.")
        self.assertEqual(result["status_message"], "System error prevented or interrupted execution.")


if __name__ == '__main__':
    unittest.main()
