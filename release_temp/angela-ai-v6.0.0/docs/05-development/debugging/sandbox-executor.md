# Sandbox Executor: Secure Code Execution Environment

## Overview

The `SandboxExecutor` (`src/services/sandbox_executor.py`) is a critical security and isolation component within the Unified-AI-Project. Its primary function is to **execute arbitrary Python code strings within a controlled, isolated subprocess environment**. This capability is essential for safely running code from potentially untrusted sources, dynamically generated code, or operations that require strict resource limits or error containment.

This module is crucial for enabling the AI to extend its capabilities through code generation and execution without compromising the stability or security of the main AI system.

## Key Responsibilities and Features

1.  **Isolated Code Execution**: 
    *   Executes Python code in a separate subprocess, ensuring that any errors, resource consumption, or malicious operations are contained within that isolated environment.
    *   Prevents the sandboxed code from directly affecting the main AI process or its resources.

2.  **Dynamic Module Execution**: 
    *   Takes a Python `code_string` (representing a class and its method) and dynamically loads and executes it within the sandbox.
    *   This allows the AI to generate new tools or functionalities on the fly and test them safely.

3.  **Time-based Termination (Timeout)**: 
    *   Enforces a configurable `timeout_seconds` for each execution.
    *   Automatically terminates the sandboxed process if it exceeds the time limit, preventing infinite loops or runaway processes.

4.  **Comprehensive Error Handling**: 
    *   Captures and reports various types of errors from the sandboxed process, including:
        *   Runtime exceptions (e.g., `NotImplementedError`).
        *   Syntax errors or import errors within the sandboxed code.
        *   Non-JSON serializable return values.
        *   Timeout exceptions.
    *   Provides detailed error messages and full tracebacks from the sandboxed environment.

5.  **Integration with Execution Monitoring**: 
    *   (If `EXECUTION_MONITORING_AVAILABLE` is True) Integrates with the `ExecutionManager` for more advanced monitoring capabilities, including adaptive timeouts, resource monitoring, and auto-recovery mechanisms.

6.  **Secure Input/Output**: 
    *   Communicates with the sandboxed process via standard input/output streams, using JSON for structured data exchange.

## How it Works

When `run` is called, the `SandboxExecutor` performs the following steps:

1.  **Temporary File Creation**: It creates temporary Python files for the provided `code_string` and a small `SANDBOX_RUNNER_SCRIPT_TEMPLATE`.
2.  **Subprocess Launch**: It launches a new Python subprocess, instructing it to execute the `_sandbox_runner.py` script. This runner script then dynamically imports and executes the user-provided code within the isolated environment.
3.  **Parameter Passing**: Method parameters are serialized to JSON and passed as command-line arguments to the runner script.
4.  **Output Capture**: The `SandboxExecutor` captures the standard output and standard error streams of the subprocess.
5.  **Result Parsing**: The runner script is designed to print a JSON-formatted result (or error) to stdout. The `SandboxExecutor` parses this JSON to extract the execution result or detailed error information.
6.  **Resource Management**: Temporary files and directories are automatically cleaned up after execution.

## Integration and Importance

-   **`ToolDispatcher`**: Can use the `SandboxExecutor` to safely run dynamically loaded or generated tools, ensuring that tool execution does not destabilize the main AI system.
-   **`CreationEngine`**: After the `CreationEngine` generates new tool or model code, the `SandboxExecutor` can be used to test and validate this code in isolation.
-   **Security**: Provides a crucial layer of security by isolating potentially untrusted or experimental code execution.
-   **Reliability**: Prevents crashes or resource exhaustion in the main AI process due to errors in dynamically executed code.
-   **Development and Testing**: Offers a controlled environment for testing new AI functionalities without affecting the core system.

## Code Location

`src/services/sandbox_executor.py`
