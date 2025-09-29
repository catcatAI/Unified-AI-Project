import json
import os
import subprocess
import tempfile
import traceback # For the runner script's exception formatting
from typing import Tuple, Optional, Dict, Any
import sys # For sys.executable

# 整合執行監控系統
try:
    from ..managers.execution_manager import (
ExecutionManager, ExecutionManagerConfig, 
execute_with_smart_monitoring, ExecutionResult, ExecutionStatus
)
EXECUTION_MONITORING_AVAILABLE = True
except ImportError:
EXECUTION_MONITORING_AVAILABLE = False

# Default timeout for sandbox execution in seconds
# 增加沙箱執行的默認超時時間從10秒到60秒
DEFAULT_SANDBOX_TIMEOUT = 60

# Template for the runner script that executes inside the sandbox
# This script will be written to a temporary file and run by a subprocess.
# It takes tool_module_path, class_name, method_name, and params_json_str as command line arguments.
SANDBOX_RUNNER_SCRIPT_TEMPLATE = '''
import importlib.util
import json
import sys
import traceback # For capturing exception details
import os # For os.path.basename, os.path.splitext

def run_sandboxed_tool():
output = {"result": None, "error": None, "traceback": None}
    try:
        if len(sys.argv) != 5:
            # Use proper f-string formatting here
            raise ValueError(f"Runner script expects 4 arguments: tool_module_path, class_name, method_name, params_json_string. Got: {len(sys.argv)-1} args: {sys.argv}")

tool_module_path = sys.argv[1]
        class_name_to_run = sys.argv[2]
method_name_to_run = sys.argv[3]
params_json_str = sys.argv[4]

        # Dynamically import the generated tool module
        # Create a unique module name to avoid conflicts if run multiple times quickly
module_file_basename = os.path.splitext(os.path.basename(tool_module_path))[0]
module_name = f"sandboxed_tool_module_{module_file_basename}"

spec = importlib.util.spec_from_file_location(module_name, tool_module_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not create module spec for {tool_module_path}")

sandboxed_module = importlib.util.module_from_spec(spec)
sys.modules[module_name] = sandboxed_module
spec.loader.exec_module(sandboxed_module)

ToolClass = getattr(sandboxed_module, class_name_to_run)

tool_instance = None
        try:
tool_instance = ToolClass(config=)
        except TypeError:
            try:
tool_instance = ToolClass
            except Exception as init_e:
                raise type(init_e)(f"Failed to initialize '{class_name_to_run}' with default attempts (config= or no args): {init_e}")

method_to_call = getattr(tool_instance, method_name_to_run)

method_params_dict = json.loads(params_json_str)

result = method_to_call(**method_params_dict)
output["result"] = result

    except Exception as e:
output["error"] = str(e)
output["traceback"] = traceback.format_exc

    try:
final_json_output = json.dumps(output)
    except TypeError as te:
original_error = output.get("error")
original_traceback = output.get("traceback")

output["result"] = f"Result of type {type(output.get('result')).__name__} is not JSON serializable."
output["error"] = f"Non-serializable result. Serialization error: {te}"
        if original_error:
output["error"] += f" | Original execution error: {original_error}"
        if original_traceback:
output["traceback"] = original_traceback # No need for or traceback.format_exc here
        else:
output["traceback"] = traceback.format_exc

final_json_output = json.dumps(output)

print(final_json_output)

if __name__ == "__main__":
run_sandboxed_tool
'''


class SandboxExecutor:
    """
Executes provided Python code strings in a sandboxed environment
using a separate subprocess.
    """

    def __init__(self, timeout_seconds: int = DEFAULT_SANDBOX_TIMEOUT, use_execution_monitoring: bool = False) -> None:
self.timeout_seconds = timeout_seconds
        # Default to False so tests that mock subprocess.run can intercept
self.use_execution_monitoring = use_execution_monitoring and EXECUTION_MONITORING_AVAILABLE
        
        # 初始化執行管理器（如果可用）
        if self.use_execution_monitoring:
self.execution_manager = ExecutionManager(ExecutionManagerConfig(
                default_timeout=timeout_seconds,
adaptive_timeout=True,
terminal_monitoring=True,
resource_monitoring=True,
auto_recovery=True
))

    def run(self,
code_string: str,
            class_name: str,
method_name: str,
method_params: Dict[str, Any]
) -> Tuple[Optional[Any], Optional[str]]:
        """
Runs a method of a class defined in code_string in a sandbox.

Args:
code_string: The Python code defining the tool class.
    class_name: The name of the class to instantiate.
method_name: The name of the method to call on the class instance.
method_params: A dictionary of parameters to pass to the method.

Returns:
A tuple (result, error_message).
'result' is the output from the method if successful and JSON serializable.
'error_message' is a string containing error details if an exception occurred or output wasn't serializable.
        """
        # Create a temporary directory that will be automatically cleaned up
        with tempfile.TemporaryDirectory as temp_dir:
tool_module_filename = "_sandboxed_tool.py"
runner_script_filename = "_sandbox_runner.py" # Changed from leading underscore

tool_module_filepath = os.path.join(temp_dir, tool_module_filename)
runner_script_filepath = os.path.join(temp_dir, runner_script_filename)

            try:
                with open(tool_module_filepath, "w", encoding="utf-8") as f_tool:
f_tool.write(code_string)

                with open(runner_script_filepath, "w", encoding="utf-8") as f_runner:
f_runner.write(SANDBOX_RUNNER_SCRIPT_TEMPLATE)

params_json_string = json.dumps(method_params)

python_executable = sys.executable or 'python' # Prefer sys.executable

                # 使用執行監控系統（如果可用）
                if self.use_execution_monitoring:
command = [python_executable, '-u', runner_script_filepath, tool_module_filepath, class_name, method_name, params_json_string]
exec_result = self.execution_manager.execute_command(
command,
timeout=self.timeout_seconds,
cwd=temp_dir,
shell=False
)
                    
                    # 轉換執行結果為subprocess格式
                    class ProcessResult:
                        def __init__(self, exec_result: ExecutionResult) -> None:
self.stdout = exec_result.stdout
self.stderr = exec_result.stderr
self.returncode = exec_result.return_code or 0
                    
process_result = ProcessResult(exec_result)
                    
                    # 處理超時情況
                    if exec_result.status == ExecutionStatus.TIMEOUT:
                        raise subprocess.TimeoutExpired(command, self.timeout_seconds)
                else:
                    # 使用原始subprocess執行
process_result = subprocess.run(
[python_executable, '-u', runner_script_filepath, tool_module_filepath, class_name, method_name, params_json_string],
capture_output=True,
text=True,
cwd=temp_dir, # Run script from within temp_dir for relative imports if any
timeout=self.timeout_seconds,
check=False
)

                # Debugging output from subprocess
                # print(f"Sandbox STDOUT:\n{process_result.stdout}")
                # print(f"Sandbox STDERR:\n{process_result.stderr}")

                if process_result.returncode != 0:
error_msg = f"Sandbox execution failed with return code {process_result.returncode}"
                    if process_result.stderr:
error_msg += f"\nSTDERR: {process_result.stderr}"
                    return None, error_msg

                if not process_result.stdout:
                    return None, "Sandbox execution completed but produced no output"

                try:
output_data = json.loads(process_result.stdout)
                except json.JSONDecodeError as e:
                    return None, f"Failed to parse sandbox output as JSON: {e}\nOutput: {process_result.stdout}"

                if output_data.get("error"):
                    return None, f"Sandbox execution error: {output_data['error']}\nTraceback:\n{output_data.get('traceback', 'No traceback')}"

                return output_data.get("result"), None

            except subprocess.TimeoutExpired:
                return None, f"Sandbox execution timed out after {self.timeout_seconds} seconds"
            except Exception as e:
                return None, f"Unexpected error during sandbox execution: {str(e)}\nTraceback:\n{traceback.format_exc}"