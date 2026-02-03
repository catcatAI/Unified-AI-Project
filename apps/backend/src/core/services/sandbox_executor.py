import os
import sys
import json
import subprocess
import tempfile
import importlib.util
import traceback
from typing import Tuple, Optional, Dict, Any

# Conditional import for execution monitoring
EXECUTION_MONITORING_AVAILABLE = False
try:
    from src.core.services.execution_manager import (
        ExecutionManager,
        ExecutionManagerConfig,
        execute_with_smart_monitoring,
        ExecutionResult,
        ExecutionStatus
    )
    EXECUTION_MONITORING_AVAILABLE = True
except ImportError:
    # If ExecutionManager is not available, define dummy classes/functions
    # to prevent errors in SandboxExecutor.
    class ExecutionManager:
        def __init__(self, config):
            pass
        def execute_command(self, command, timeout, cwd, shell):
            # Simulate subprocess.run output for compatibility
            process = subprocess.run(
                command,
                capture_output=True,
                text=True,
                cwd=cwd,
                shell=shell,
                timeout=timeout
            )
            return type('obj', (object,), {
                'stdout': lambda: process.stdout,
                'stderr': lambda: process.stderr,
                'return_code': process.returncode,
                'status': ExecutionStatus.COMPLETED if process.returncode == 0 else ExecutionStatus.FAILED
            })()

    class ExecutionManagerConfig:
        pass

    class ExecutionResult:
        def __init__(self, stdout, stderr, return_code, status):
            self._stdout = stdout
            self._stderr = stderr
            self._return_code = return_code
            self._status = status
        def stdout(self): return self._stdout
        def stderr(self): return self._stderr
        @property
        def return_code(self): return self._return_code
        @property
        def status(self): return self._status

    class ExecutionStatus:
        COMPLETED = "completed"
        FAILED = "failed"
        TIMEOUT = "timeout"

    def execute_with_smart_monitoring(*args, **kwargs):
        raise NotImplementedError("Execution monitoring is not available.")


# Default timeout for sandbox execution in seconds
DEFAULT_SANDBOX_TIMEOUT = 60

# Template for the runner script that executes inside the sandbox
# This script will be written to a temporary file and run by a subprocess.
# It takes tool_module_path, class_name, method_name, and params_json_str as command line arguments.
SANDBOX_RUNNER_SCRIPT_TEMPLATE = """
import os
import sys
import json
import importlib.util
import traceback

def run_sandboxed_tool():
    output = {"result": None, "error": None, "traceback": None}
    try:
        if len(sys.argv) != 5:
            raise ValueError(
                f"Runner script expects 4 arguments: tool_module_path, class_name, method_name, "
                f"params_json_string. Got {len(sys.argv) - 1} args: {sys.argv[1:]}"
            )

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
            tool_instance = ToolClass(config=None) # Attempt with config=None
        except TypeError:
            try:
                tool_instance = ToolClass() # Attempt without config
            except Exception as init_e:
                raise type(init_e)(f"Failed to initialize '{class_name_to_run}' with default attempts (config=None or no args): {init_e}")

        method_to_call = getattr(tool_instance, method_name_to_run)
        method_params_dict = json.loads(params_json_str)

        result = method_to_call(**method_params_dict)
        output["result"] = result

    except Exception as e:
        output["error"] = str(e)
        output["traceback"] = traceback.format_exc()
    
    final_json_output = ""
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
            output["traceback"] = original_traceback # No need for traceback.format_exc here
        else:
            output["traceback"] = traceback.format_exc()
        final_json_output = json.dumps(output)

    print(final_json_output)

if __name__ == '__main__':
    run_sandboxed_tool()
"""


class SandboxExecutor:
    """
    Executes provided Python code strings in a sandboxed environment
    using a separate subprocess.
    """

    def __init__(self, timeout_seconds: int = DEFAULT_SANDBOX_TIMEOUT,
                 use_execution_monitoring: bool = True) -> None:
        self.timeout_seconds = timeout_seconds
        self.use_execution_monitoring = use_execution_monitoring and \
                                        EXECUTION_MONITORING_AVAILABLE

        # Initialize execution manager if available
        if self.use_execution_monitoring:
            self.execution_manager = ExecutionManager(
                ExecutionManagerConfig(
                    default_timeout=timeout_seconds,
                    adaptive_timeout=True,
                    terminal_monitoring=True,
                    resource_monitoring=True,
                    auto_recovery=True
                )
            )
        else:
            self.execution_manager = None # Ensure it's explicitly None if not used

    def run(self, code_string: str, class_name: str, method_name: str,
            method_params: Dict[str, Any]) -> Tuple[Optional[Any], Optional[str]]:
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
            'error_message' is a string containing error details if an exception occurred or
            output wasn't serializable.
        """
        # Create a temporary directory that will be automatically cleaned up
        with tempfile.TemporaryDirectory() as temp_dir:
            tool_module_filename = "_sandboxed_tool.py"
            runner_script_filename = "_sandbox_runner.py"

            tool_module_filepath = os.path.join(temp_dir, tool_module_filename)
            runner_script_filepath = os.path.join(temp_dir, runner_script_filename)

            try:
                with open(tool_module_filepath, "w", encoding="utf-8") as f_tool:
                    f_tool.write(code_string)

                with open(runner_script_filepath, "w", encoding="utf-8") as f_runner:
                    f_runner.write(SANDBOX_RUNNER_SCRIPT_TEMPLATE)

                params_json_string = json.dumps(method_params)

                python_executable = sys.executable or 'python'

                command = [
                    python_executable,
                    '-u', # Unbuffered output
                    runner_script_filepath,
                    tool_module_filepath,
                    class_name,
                    method_name,
                    params_json_string
                ]

                process_result = None
                if self.use_execution_monitoring and self.execution_manager:
                    exec_result = self.execution_manager.execute_command(
                        command=command,
                        timeout=self.timeout_seconds,
                        cwd=temp_dir,
                        shell=False
                    )
                    # Convert execution manager result to a format similar to subprocess.run
                    process_result = type('obj', (object,), {
                        'stdout': lambda: exec_result.stdout(),
                        'stderr': lambda: exec_result.stderr(),
                        'returncode': exec_result.return_code,
                        'timeout_occurred': exec_result.status == ExecutionStatus.TIMEOUT
                    })()
                else:
                    process_result = subprocess.run(
                        command,
                        capture_output=True,
                        text=True,
                        cwd=temp_dir,
                        timeout=self.timeout_seconds,
                        check=False
                    )

                # Debugging output from subprocess
                # print(f"Sandbox STDOUT\n{process_result.stdout}")
                # print(f"Sandbox STDERR\n{process_result.stderr}")

                if process_result.timeout_occurred if self.use_execution_monitoring else False:
                    return None, f"Sandbox execution timed out after {self.timeout_seconds} seconds."

                stdout_str = process_result.stdout.strip()
                stderr_str = process_result.stderr.strip()

                if stdout_str:
                    try:
                        output_json = json.loads(stdout_str)
                        if output_json.get("error") or output_json.get("traceback"):
                            full_error_msg = f"Error during sandboxed tool execution: {output_json.get('error', 'Unknown error')}"
                            if output_json.get("traceback"):
                                full_error_msg += f"\nTraceback:\n{output_json['traceback']}"
                            if stderr_str: # Append stderr if it exists, as it might contain additional context
                                full_error_msg += f"\nStderr:\n{stderr_str}"
                            return None, full_error_msg
                        
                        # If no error in JSON but stderr exists, this is an odd case.
                        # Let's assume the JSON result is primary if present and valid without error fields.
                        # And append stderr as a warning.
                        if stderr_str:
                            return output_json.get("result"), f"Sandbox execution had stderr output (but valid JSON result from stdout):\n{stderr_str}"
                        return output_json.get("result"), None # Success
                    except json.JSONDecodeError:
                        # stdout was not JSON, combine with stderr
                        error_msg = f"Sandbox execution produced non-JSON output:\n{stdout_str}"
                        if stderr_str:
                            error_msg += f"\nStderr:\n{stderr_str}"
                        return None, error_msg
                elif stderr_str:
                    # Only stderr, or stdout was empty
                    return None, f"Sandbox execution error (stderr):\n{stderr_str}"
                elif process_result.returncode != 0:
                    return None, f"Sandbox execution failed with return code {process_result.returncode} and no specific error output captured."
                else:
                    return None, "Sandbox execution completed with no output."

            except subprocess.TimeoutExpired:
                return None, f"Sandbox execution timed out after {self.timeout_seconds} seconds."
            except Exception as e:
                return None, f"Error in sandbox executor system: {str(e)}\n{traceback.format_exc()}"

    def _validate_code(self, code_string: str) -> Tuple[bool, str]:
        """
        Performs basic validation on the code string to prevent obvious security risks.
        Returns (is_valid, error_message).
        """
        # Example: Prevent importing 'os' or 'sys' directly in the sandboxed code
        # This is a basic check; a real sandbox would need more robust security.
        if re.search(r"^\s*import\s+(os|sys|subprocess|shutil)", code_string, re.MULTILINE):
            return False, "Import of restricted modules (os, sys, subprocess, shutil) is not allowed."
        if re.search(r"os\.(system|popen|exec|fork)", code_string):
            return False, "Direct calls to os.system, os.popen, etc., are not allowed."
        if re.search(r"subprocess\.(run|call|check_call|check_output|Popen)", code_string):
            return False, "Direct calls to subprocess functions are not allowed."
        
        # Basic syntax check
        try:
            compile(code_string, '<string>', 'exec')
        except SyntaxError as e:
            return False, f"Syntax error in provided code: {e}"

        return True, ""


if __name__ == '__main__':
    # This block is for direct testing of sandbox_executor.py
    print("---""SandboxExecutor Self-Test Block""---")
    executor = SandboxExecutor(timeout_seconds=5)

    good_code_main = """
from typing import Dict, Any, Optional

class MyEchoTool:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.prefix = "Echo: "
        if config and "prefix" in config:
            self.prefix = config["prefix"]

    def execute(self, message: str, times: int = 1) -> str:
        return self.prefix + (message + " ") * times
"""
    print("\nTesting good_code (MyEchoTool)...")
    result, error = executor.run(
        code_string=good_code_main,
        class_name="MyEchoTool",
        method_name="execute",
        method_params={"message": "hello", "times": 2}
    )
    if error:
        print(f"  Error: {error}")
    else:
        print(f"  Result: {result}")
    assert result == "Echo: hello hello ", f"Expected 'Echo: hello hello ' but got '{result}'"

    error_code_main = """
class ErrorTool:
    def run(self):
        raise NotImplementedError("This tool is not implemented yet!")
"""
    print("\nTesting error_code (ErrorTool)...")
    result, error = executor.run(error_code_main, "ErrorTool", "run", {})
    if error:
        print(f"  Error (expected):\n{error}")
        assert "NotImplementedError" in error, "Error was expected"
    else:
        print(f"  Result: {result}")
        assert False, "Error was expected"

    non_json_code_main = """
class NonJsonTool:
    def get_data(self):
        return object() # object() is not JSON serializable
"""
    print("\nTesting non_json_code (NonJsonTool)...")
    result, error = executor.run(non_json_code_main, "NonJsonTool", "get_data", {})
    if error:
        print(f"  Error (expected):\n{error}")
        assert "not JSON serializable" in error, "Error was expected"
    else:
        print(f"  Result: {result}")
        assert False, "Error was expected"

    infinite_loop_code_main = """
class LoopTool:
    def loop_forever(self):
        while True:
            pass
"""
    print("\nTesting infinite_loop_code (LoopTool)...")
    result, error = executor.run(infinite_loop_code_main, "LoopTool", "loop_forever", {})
    if error:
        print(f"  Error (expected timeout):\n{error}")
        assert "timed out" in error.lower(), "Timeout error was expected"
    else:
        print(f"  Result: {result}")
        assert False, "Timeout error was expected"

    syntax_error_code_main = "class BadSyntaxTool:\n  def func(self)\n    pass"
    print("\nTesting syntax_error_code (BadSyntaxTool - sandbox will see ImportError / SyntaxError)...")
    result, error = executor.run(syntax_error_code_main, "BadSyntaxTool", "func", {})
    if error:
        print(f"  Error (expected):\n{error}")
        assert "SyntaxError" in error or "IndentationError" in error, f"Unexpected error type: {error}"
    else:
        print(f"  Result: {result}")
        assert False, "Error was expected"

    print("\nSandboxExecutor self-test block finished.")