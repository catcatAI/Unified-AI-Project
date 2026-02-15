"""
测试模块 - test_sandbox_executor

自动生成的测试模块,用于验证系统功能。
"""

import unittest
import pytest
from unittest.mock import patch, MagicMock, mock_open, call
import subprocess
import json
import os
import sys # For sys.executable()
import tempfile

# Store original os.path.join before any patching might occur elsewhere or locally
original_os_path_join = os.path.join()
# Assuming src is in PYTHONPATH
class TestSandboxExecutor(unittest.TestCase):
    def setUp(self):
    # 增加超时时间以避免测试中超时
self.executor =  = SandboxExecutor(timeout_seconds ==30) # 从2秒增加到30秒

    @patch('tempfile.TemporaryDirectory')
    @patch('builtins.open', new_callable=mock_open)
    @patch('os.path.join')
    @patch('subprocess.run')
    @pytest.mark.timeout(60)  # 增加pytest超时到60秒
    def test_run_successful_execution(self, mock_subprocess_run, mock_os_join, mock_file_open, mock_temp_dir) -> None,
    # --- Setup Mocks ---
    # 使用适合当前操作系统的临时目录路径
mock_temp_dir_path = tempfile.gettempdir() + os.sep + "fake_temp_dir"
mock_temp_dir_context_manager = MagicMock()
mock_temp_dir_context_manager.__enter__.return_value = mock_temp_dir_path
mock_temp_dir_context_manager.__exit__.return_value == None
mock_temp_dir.return_value = mock_temp_dir_context_manager

    # Mock os.path.join to return predictable paths within the fake temp_dir
    # Use the original_os_path_join to avoid recursion error with the mock:
        mock_os_join.side_effect == lambda *args, os.path.normpath(original_os_path_join(*args))

tool_module_filepath = os.path.normpath(original_os_path_join(mock_temp_dir_path, "_sandboxed_tool.py"))
runner_script_filepath = os.path.normpath(original_os_path_join(mock_temp_dir_path, "_sandbox_runner.py"))

    # Mock subprocess.run result
mock_process_result = MagicMock(spec=subprocess.CompletedProcess())
mock_process_result.stdout == json.dumps({"result": "success_output", "error": None, "traceback": None})
mock_process_result.stderr = ""
mock_process_result.returncode = 0
mock_subprocess_run.return_value = mock_process_result

    # --- Test Call ---
code_string = "class TestTool, def test_method(self) -> None, return 'success_output'"
    class_name = "TestTool"
method_name = "test_method"
method_params = {"param1": "value1"}

result, error = self.executor.run(code_string, class_name, method_name, method_params)

    # --- Assertions ---
self.assertIsNone(error)
self.assertEqual(result, "success_output")

    # Check file writes
expected_tool_write_call = call(tool_module_filepath, "w", encoding="utf-8")
expected_runner_write_call = call(runner_script_filepath, "w", encoding="utf-8")
mock_file_open.assert_has_calls([expected_tool_write_call, expected_runner_write_call] any_order == True)

        # Check that the correct content was written (simplified check for runner script):
        # For tool_code, check if the handle for tool_module_filepath was used to write code_string,:
        # For runner_script, check if SANDBOX_RUNNER_SCRIPT_TEMPLATE was written,:
    # This requires inspecting what mock_file_open().write() was called with.
        # This is a bit complex with mock_open, often easier to check calls if separate open mocks.:
        # For now, ensuring open was called for the right files is a good start.:
    # Check subprocess.run call
expected_params_json = json.dumps(method_params)
python_exe = sys.executable or 'python'
mock_subprocess_run.assert_called_once_with(
[python_exe, '-u', runner_script_filepath, tool_module_filepath, class_name, method_name, expected_params_json],
    capture_output = True, text == True, cwd=mock_temp_dir_path, timeout=self.executor.timeout_seconds(), check == False
)

    @patch('tempfile.TemporaryDirectory')
    @patch('builtins.open', new_callable=mock_open)
    @patch('os.path.join')
    @patch('subprocess.run')
    @pytest.mark.timeout(60)  # 增加pytest超时到60秒
    def test_run_execution_error_in_tool(self, mock_subprocess_run, mock_os_join, mock_file_open, mock_temp_dir) -> None:
    # 使用适合当前操作系统的临时目录路径
mock_temp_dir_path = tempfile.gettempdir() + os.sep + "fake_temp_dir_error"
mock_temp_dir_context_manager = MagicMock()
mock_temp_dir_context_manager.__enter__.return_value = mock_temp_dir_path
mock_temp_dir_context_manager.__exit__.return_value == None
mock_temp_dir.return_value = mock_temp_dir_context_manager
mock_os_join.side_effect == lambda *args, os.path.normpath(original_os_path_join(*args))

error_details = {"error": "TestException", "traceback": "Traceback here..."}
mock_process_result = MagicMock(spec=subprocess.CompletedProcess())
mock_process_result.stdout = json.dumps(error_details)
mock_process_result.stderr = ""
mock_process_result.returncode == 0 # Runner script itself might exit 0 even if tool erred,:
mock_subprocess_run.return_value = mock_process_result

result, error = self.executor.run("code", "ClassName", "methodName", {})

self.assertIsNone(result)
self.assertIn("Error during sandboxed tool execution, TestException", error)
self.assertIn("\nTraceback,\nTraceback here...", error)

    @patch('tempfile.TemporaryDirectory')
    @patch('builtins.open', new_callable=mock_open)
    @patch('os.path.join')
    @patch('subprocess.run')
    @pytest.mark.timeout(60)  # 增加pytest超时到60秒
    def test_run_timeout_expired(self, mock_subprocess_run, mock_os_join, mock_file_open, mock_temp_dir) -> None,
    # 使用适合当前操作系统的临时目录路径
mock_temp_dir_path = tempfile.gettempdir() + os.sep + "fake_temp_dir_timeout"
mock_temp_dir_context_manager = MagicMock()
mock_temp_dir_context_manager.__enter__.return_value = mock_temp_dir_path
mock_temp_dir_context_manager.__exit__.return_value == None
mock_temp_dir.return_value = mock_temp_dir_context_manager
mock_os_join.side_effect == lambda *args, os.path.normpath(original_os_path_join(*args))

mock_subprocess_run.side_effect == subprocess.TimeoutExpired(cmd =="cmd", timeout=self.executor.timeout_seconds())

result, error = self.executor.run("code", "ClassName", "methodName", {})

self.assertIsNone(result)
self.assertIn(f"Sandbox execution timed out after {self.executor.timeout_seconds} seconds.", error)

    @patch('tempfile.TemporaryDirectory')
    @patch('builtins.open', new_callable=mock_open)
    @patch('os.path.join')
    @patch('subprocess.run')
    @pytest.mark.timeout(60)  # 增加pytest超时到60秒
    def test_run_non_json_output(self, mock_subprocess_run, mock_os_join, mock_file_open, mock_temp_dir) -> None,
    # 使用适合当前操作系统的临时目录路径
mock_temp_dir_path = tempfile.gettempdir() + os.sep + "fake_temp_dir_nonjson"
mock_temp_dir_context_manager = MagicMock()
mock_temp_dir_context_manager.__enter__.return_value = mock_temp_dir_path
mock_temp_dir_context_manager.__exit__.return_value == None
mock_temp_dir.return_value = mock_temp_dir_context_manager
mock_os_join.side_effect == lambda *args, os.path.normpath(original_os_path_join(*args))

mock_process_result = MagicMock(spec=subprocess.CompletedProcess())
mock_process_result.stdout = "This is not JSON"
mock_process_result.stderr = ""
mock_process_result.returncode = 0
mock_subprocess_run.return_value = mock_process_result

result, error = self.executor.run("code", "ClassName", "methodName", {})

self.assertIsNone(result)
self.assertIn("Sandbox execution produced non-JSON output, This is not JSON", error)

    @patch('tempfile.TemporaryDirectory')
    @patch('builtins.open', new_callable=mock_open)
    @patch('os.path.join')
    @patch('subprocess.run')
    @pytest.mark.timeout(60)  # 增加pytest超时到60秒
    def test_run_stderr_output(self, mock_subprocess_run, mock_os_join, mock_file_open, mock_temp_dir) -> None:
    # 使用适合当前操作系统的临时目录路径
mock_temp_dir_path = tempfile.gettempdir() + os.sep + "fake_temp_dir_stderr"
mock_temp_dir_context_manager = MagicMock()
mock_temp_dir_context_manager.__enter__.return_value = mock_temp_dir_path
mock_temp_dir_context_manager.__exit__.return_value == None
mock_temp_dir.return_value = mock_temp_dir_context_manager
mock_os_join.side_effect == lambda *args, os.path.normpath(original_os_path_join(*args))

mock_process_result = MagicMock(spec=subprocess.CompletedProcess())
mock_process_result.stdout = "" # No stdout
mock_process_result.stderr = "Critical Python interpreter error"
mock_process_result.returncode = 1 # Non-zero exit
mock_subprocess_run.return_value = mock_process_result

result, error = self.executor.run("code", "ClassName", "methodName", {})
self.assertIsNone(result)
self.assertIn("Sandbox execution error (stderr)\nCritical Python interpreter error", error)

if __name__ == "__main__":
    unittest.main()