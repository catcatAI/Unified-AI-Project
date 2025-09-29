# src/security/enhanced_sandbox.py
"""
Enhanced Sandbox Environment for AI Operations
Provides isolated execution environment with enhanced security controls
"""

import json
import os
import subprocess
import tempfile
import traceback
import threading
import time
import psutil
import sys
import signal
from typing import Tuple, Optional, Dict, Any, List
from dataclasses import dataclass, field
import logging
import hashlib
import re


logger: Any = logging.getLogger(__name__)

@dataclass
class SandboxConfig:
    """Configuration for the enhanced sandbox"""
    timeout_seconds: int = 30
    max_memory_mb: int = 256
    max_cpu_percent: int = 50
    allowed_modules: List[str] = field(default_factory=lambda: [
        "json", "re", "datetime", "collections", "itertools", "math", "random"
    ])
    restricted_modules: List[str] = field(default_factory=lambda: [
        "os", "sys", "subprocess", "socket", "threading", "multiprocessing"
    ])
    allowed_paths: List[str] = field(default_factory=lambda: [
        "/tmp", "/var/tmp", "./sandbox_temp"
    ])
    restricted_paths: List[str] = field(default_factory=lambda: [
        "/etc", "/usr", "/root", "/home", "/var/log"
    ])
    max_file_size_mb: int = 10
    max_network_connections: int = 5

@dataclass
class ResourceLimits:
    """Resource limits for sandbox execution"""
    cpu_percent: float = 50.0
    memory_mb: int = 256
    execution_time_seconds: int = 30
    network_connections: int = 5

class ResourceMonitor:
    """Monitor resource usage during sandbox execution"""
    
    def __init__(self, limits: ResourceLimits) -> None:
        self.limits = limits
        self.monitoring = False
        self.monitor_thread = None
        self.process = None
        self.violations = 
        
    def start_monitoring(self, process: subprocess.Popen):
        """Start monitoring a process"""
        self.process = process
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start
        
    def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join
            
    def _monitor_loop(self):
        """Monitoring loop"""
        try:
            ps_process = psutil.Process(self.process.pid)
            
            while self.monitoring and self.process.poll is None:
                try:
                    # Check CPU usage
                    cpu_percent = ps_process.cpu_percent
                    if cpu_percent > self.limits.cpu_percent:
                        self.violations.append(f"CPU usage exceeded limit: {cpu_percent}% > {self.limits.cpu_percent}%")
                        self._terminate_process
                        break
                        
                    # Check memory usage
                    memory_mb = ps_process.memory_info.rss / 1024 / 1024
                    if memory_mb > self.limits.memory_mb:
                        self.violations.append(f"Memory usage exceeded limit: {memory_mb}MB > {self.limits.memory_mb}MB")
                        self._terminate_process
                        break
                        
                except psutil.NoSuchProcess:
                    break
                except Exception as e:
                    logger.warning(f"Error monitoring process: {e}")
                    
                time.sleep(1)
                
        except Exception as e:
            logger.error(f"Error in monitor loop: {e}")
            
    def _terminate_process(self):
        """Terminate the monitored process"""
        try:
            self.process.terminate
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.process.kill
        except Exception as e:
            logger.error(f"Error terminating process: {e}")

# Enhanced sandbox runner script template
ENHANCED_SANDBOX_RUNNER_TEMPLATE = '''
import importlib.util
import json
import sys
import traceback
import os
import hashlib

# Security restrictions
import builtins

# Remove dangerous builtins
dangerous_builtins = [
    'exec', 'eval', 'compile', 'open', 'file', 'input', '__import__',
    'globals', 'locals', 'vars', 'dir', 'help'
]

for builtin in dangerous_builtins:
    if hasattr(builtins, builtin):
        delattr(builtins, builtin)

def run_enhanced_sandboxed_tool():
    output = {{"result": None, "error": None, "traceback": None}}
    try:
        if len(sys.argv) != 5:
            raise ValueError(f"Runner script expects 4 arguments. Got: {{len(sys.argv)-1}} args")

        tool_module_path = sys.argv[1]
        class_name_to_run = sys.argv[2]
        method_name_to_run = sys.argv[3]
        params_json_str = sys.argv[4]

        # Validate module path
        if not tool_module_path.endswith('_sandboxed_tool.py'):
            raise ValueError("Invalid module path")

        # Dynamically import the generated tool module
        module_file_basename = os.path.splitext(os.path.basename(tool_module_path))[0]
        module_name = f"sandboxed_tool_module_{{module_file_basename}}"

        spec = importlib.util.spec_from_file_location(module_name, tool_module_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not create module spec for {{tool_module_path}}")

        sandboxed_module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = sandboxed_module
        spec.loader.exec_module(sandboxed_module)

        ToolClass = getattr(sandboxed_module, class_name_to_run)

        tool_instance = None
        try:
            tool_instance = ToolClass(config=
)
        except TypeError:
            try:
                tool_instance = ToolClass
            except Exception as init_e:
                raise type(init_e)(f"Failed to initialize '{{class_name_to_run}}': {{init_e}}")

        method_to_call = getattr(tool_instance, method_name_to_run)

        method_params_dict = json.loads(params_json_str)

        result = method_to_call(**method_params_dict)
        output["result"] = result

    except Exception as e:
        output["error"] = str(e)
        output["traceback"] = traceback.format_exc

    try:
        # Ensure result is JSON serializable
        json.dumps(output["result"])
    except TypeError as te:
        original_error = output.get("error")
        original_traceback = output.get("traceback")

        output["result"] = f"Result of type {{type(output.get('result')).__name__}} is not JSON serializable."
        output["error"] = f"Non-serializable result. Serialization error: {{te}}"
        if original_error:
            output["error"] += f" | Original execution error: {{original_error}}"
        if original_traceback:
             output["traceback"] = original_traceback
        else:
            output["traceback"] = traceback.format_exc

    print(json.dumps(output))

if __name__ == "__main__":
    run_enhanced_sandboxed_tool
'''

class EnhancedSandboxExecutor:
    """Enhanced sandbox executor with security controls"""
    
    def __init__(self, config: SandboxConfig = None, 
                 permission_system: PermissionControlSystem = None,
                 audit_logger: AuditLogger = None):
        self.config = config or SandboxConfig
        self.permission_system = permission_system or PermissionControlSystem
        self.audit_logger = audit_logger or AuditLogger
        self.resource_limits = ResourceLimits(
            cpu_percent=self.config.max_cpu_percent,
            memory_mb=self.config.max_memory_mb,
            execution_time_seconds=self.config.timeout_seconds
        )
        
        logger.info("EnhancedSandboxExecutor initialized")
        
    def execute(self, user_id: str, code_string: str, class_name: str, 
                method_name: str, method_params: Dict[str, Any]) -> Tuple[Optional[Any], Optional[str]]:
        """
        Execute code in enhanced sandbox environment
        
        Args:
            user_id: ID of the user executing the code
            code_string: Python code to execute
            class_name: Name of the class to instantiate
            method_name: Name of the method to call
            method_params: Parameters to pass to the method
            
        Returns:
            _ = Tuple of (result, error_message)
        """
        # Generate script hash for auditing
        script_hash = hashlib.sha256(code_string.encode).hexdigest[:16]
        
        # Check permissions
        permission_context = PermissionContext(
            user_id=user_id,
            operation=PermissionType.SANDBOX_EXECUTION.value,
            resource=f"script_{script_hash}",
            action="execute",
            metadata={
                "class_name": class_name,
                "method_name": method_name,
                "param_count": len(method_params)
            }
        )
        
        if not self.permission_system.check_permission(permission_context):
            error_msg = f"Permission denied for sandbox execution by user {user_id}"
            self.audit_logger.log_permission_check(
                user_id=user_id,
                permission_type=PermissionType.SANDBOX_EXECUTION.value,
                resource=f"script_{script_hash}",
                action="execute",
                granted=False,
                details={"reason": "Permission check failed"}
            )
            return None, error_msg
            
        # Log execution attempt
        self.audit_logger.log_sandbox_execution(
            user_id=user_id,
            script_hash=script_hash,
            success=False,  # Will update later
            details={
                "class_name": class_name,
                "method_name": method_name,
                "param_count": len(method_params)
            }
        )
        
        try:
            # Validate code safety
            validation_result = self._validate_code(code_string)
            if not validation_result[0]:
                error_msg = f"Code validation failed: {validation_result[1]}"
                self.audit_logger.log_security_violation(
                    user_id=user_id,
                    violation_type="code_validation_failed",
                    resource=f"script_{script_hash}",
                    details={"validation_error": validation_result[1]}
                )
                return None, error_msg
                
            # Execute in sandbox
            result, error = self._run_in_sandbox(code_string, class_name, method_name, method_params)
            
            # Log execution result
            self.audit_logger.log_sandbox_execution(
                user_id=user_id,
                script_hash=script_hash,
                success=error is None,
                details={
                    "class_name": class_name,
                    "method_name": method_name,
                    "param_count": len(method_params),
                    "has_result": result is not None,
                    "has_error": error is not None
                }
            )
            
            return result, error
            
        except Exception as e:
            error_msg = f"Error in sandbox execution: {str(e)}"
            logger.error(error_msg)
            
            # Log error
            self.audit_logger.log_error(
                user_id=user_id,
                error_type="sandbox_execution_error",
                resource=f"script_{script_hash}",
                error_message=str(e),
                details={"traceback": traceback.format_exc}
            )
            
            return None, error_msg
            
    def _validate_code(self, code_string: str) -> Tuple[bool, str]:
        """Validate code for security issues"""
        try:
            # Check for restricted modules
            for module in self.config.restricted_modules:
                if module in code_string:
                    return False, f"Restricted module '{module}' found in code"
                    
            # Check for dangerous patterns
            dangerous_patterns = [
                r'(__import__\s*\',
                r'(exec\s*\',
                r'(eval\s*\',
                r'(open\s*\',
                r'(file\s*\',
                r'(subprocess\.)',
                r'(os\.)',
                r'(sys\.)',
                r'(socket\.)',
                r'(import\s+os)',
                r'(import\s+sys)',
                r'(import\s+subprocess)',
            ]
            
            for pattern in dangerous_patterns:
                if re.search(pattern, code_string):
                    return False, f"Dangerous pattern '{pattern}' found in code"
                    
            # Check for file operations
            file_patterns = [
                r'(\.read\s*\',
                r'(\.write\s*\',
                r'(\.open\s*\',
            ]
            
            for pattern in file_patterns:
                if re.search(pattern, code_string):
                    return False, f"File operation pattern '{pattern}' found in code"
                    
            return True, "Code validation passed"
            
        except Exception as e:
            return False, f"Error during code validation: {str(e)}"
            
    def _run_in_sandbox(self, code_string: str, class_name: str, 
                       method_name: str, method_params: Dict[str, Any]) -> Tuple[Optional[Any], Optional[str]]:
        """Run code in sandbox environment"""
        # Create a temporary directory that will be automatically cleaned up
        with tempfile.TemporaryDirectory as temp_dir:
            tool_module_filename = "_sandboxed_tool.py"
            runner_script_filename = "_enhanced_sandbox_runner.py"

            tool_module_filepath = os.path.join(temp_dir, tool_module_filename)
            runner_script_filepath = os.path.join(temp_dir, runner_script_filename)

            try:
                # Write tool module
                with open(tool_module_filepath, "w", encoding="utf-8") as f_tool:
                    f_tool.write(code_string)

                # Write runner script
                with open(runner_script_filepath, "w", encoding="utf-8") as f_runner:
                    f_runner.write(ENHANCED_SANDBOX_RUNNER_TEMPLATE)

                # Prepare parameters
                params_json_string = json.dumps(method_params)
                
                # Get Python executable
                python_executable = sys.executable or 'python'

                # Start resource monitor
                resource_monitor = ResourceMonitor(self.resource_limits)
                
                try:
                    # Execute in subprocess with timeout
                    process = subprocess.Popen(
                        [python_executable, '-u', runner_script_filepath, 
                         tool_module_filepath, class_name, method_name, params_json_string],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        cwd=temp_dir,
                        start_new_session=True  # Create new process group
                    )
                    
                    # Start monitoring
                    resource_monitor.start_monitoring(process)
                    
                    # Wait for completion or timeout
                    try:
                        stdout, stderr = process.communicate(timeout=self.config.timeout_seconds)
                    except subprocess.TimeoutExpired:
                        # Kill the process group
                        try:
                            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                        except:
                            process.kill
                        process.wait
                        return None, f"Sandbox execution timed out after {self.config.timeout_seconds} seconds"
                        
                finally:
                    # Stop monitoring
                    resource_monitor.stop_monitoring
                    
                # Check for resource violations
                if resource_monitor.violations:
                    return None, f"Resource limit violation: {'; '.join(resource_monitor.violations)}"
                    
                # Process results
                if stderr:
                    if stdout and stdout.strip:
                        try:
                            output_json = json.loads(stdout.strip)
                            if output_json.get("error") or output_json.get("traceback"):
                                full_error_msg = f"Error during sandboxed tool execution: {output_json.get('error', 'Unknown error')}"
                                if output_json.get("traceback"):
                                    full_error_msg += f"\nTraceback:\n{output_json['traceback']}"
                                return None, full_error_msg
                            return output_json.get("result"), f"Sandbox execution had stderr output: {stderr.strip}"
                        except json.JSONDecodeError:
                            return None, f"Sandbox execution error: {stderr.strip}\nSandbox stdout (non-JSON): {stdout.strip}"
                    else:
                        return None, f"Sandbox execution error: {stderr.strip}"

                if stdout and stdout.strip:
                    try:
                        output_json = json.loads(stdout.strip)
                        if output_json.get("error") or output_json.get("traceback"):
                            full_error_msg = f"Error during sandboxed tool execution: {output_json.get('error', 'Unknown error')}"
                            if output_json.get("traceback"):
                                full_error_msg += f"\nTraceback:\n{output_json['traceback']}"
                            return None, full_error_msg
                        return output_json.get("result"), None
                    except json.JSONDecodeError:
                        return None, f"Sandbox execution produced non-JSON output: {stdout.strip}"

                return None, "Sandbox execution completed with no output"

            except Exception as e:
                return None, f"Error in sandbox executor system: {str(e)}\n{traceback.format_exc}"

# Example usage and testing
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Create enhanced sandbox executor
    sandbox = EnhancedSandboxExecutor
    
    # Test code
    test_code = '''
class DataTransformer:
    def __init__(self, config=None) -> None:
        pass
        
    def transform(self, data):
        # Simple transformation
        if isinstance(data, dict):
            return {k: str(v).upper for k, v in data.items}
        elif isinstance(data, list):
            return [str(item).upper for item in data]
        else:
            return str(data).upper
'''
    
    # Execute test
    result, error = sandbox.execute(
        user_id="test_user",
        code_string=test_code,
        class_name="DataTransformer",
        method_name="transform",
        method_params={"data": {"name": "test", "value": 123}}
    )
    
    if error:
        print(f"Error: {error}")
    else:
        print(f"Result: {result}")
        
    print("Enhanced sandbox test completed")