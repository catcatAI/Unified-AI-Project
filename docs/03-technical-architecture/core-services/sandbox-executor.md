# SandboxExecutor: Secure and Isolated Code Execution

## Overview

This document provides an overview of the `SandboxExecutor` module (`src/services/sandbox_executor.py`). Its primary function is to safely execute provided Python code strings within an isolated, sandboxed environment, utilizing a separate subprocess.

This module is crucial for the security and stability of the AI system, particularly when dealing with dynamically generated code, user-submitted scripts, or potentially untrusted external tools. It prevents malicious or erroneous code from affecting the main application process and allows for controlled execution with defined resource limits like timeouts.

## Key Responsibilities and Features

*   **Process Isolation**: Ensures that the execution of the target Python code is completely isolated from the main AI application process by running it in a separate subprocess. This provides a strong security boundary.
*   **Dynamic Code Loading and Execution**: Accepts a `code_string` (raw Python code), writes it to a temporary file, and then dynamically imports and executes it within the sandboxed subprocess. This enables on-the-fly execution of code.
*   **Method Invocation**: Instantiates a specified `class_name` from the provided `code_string` and calls a designated `method_name` on that instance, passing a dictionary of `method_params` as arguments.
*   **Timeout Control**: Enforces a strict `timeout_seconds` limit on the execution duration of the sandboxed code. If the code exceeds this limit, the subprocess is automatically terminated, preventing infinite loops or runaway processes.
*   **Comprehensive Error Handling and Reporting**: Captures standard output (`stdout`), standard error (`stderr`), and any exceptions raised within the sandboxed process. It returns structured error messages, including full tracebacks, to the calling module for detailed debugging. It also handles cases where the execution result is not JSON serializable.
*   **Integration with Execution Monitoring**: Optionally integrates with the `ExecutionManager` (if available in the environment). This integration provides more advanced monitoring capabilities, adaptive timeouts, and resource management for the sandboxed process, enhancing its robustness.
*   **`SANDBOX_RUNNER_SCRIPT_TEMPLATE`**: An internal, self-contained Python script template that is written to a temporary file and executed by the subprocess. This runner script is responsible for handling the dynamic import, class instantiation, method invocation, and structured JSON output of results or errors from the sandboxed code.

## How it Works

The `SandboxExecutor` operates by creating a temporary, isolated environment. It writes the user-provided Python `code_string` into a Python file within this temporary directory. Concurrently, it writes a small `_sandbox_runner.py` script (derived from `SANDBOX_RUNNER_SCRIPT_TEMPLATE`) into the same location. It then launches a new Python subprocess, instructing it to execute this `_sandbox_runner.py` script. The runner script, in turn, dynamically loads and executes the user's code, captures its output or any errors, and prints them as a JSON string to its standard output. The `SandboxExecutor` in the main process captures this JSON output, parses it, and returns the result or error details.

## Integration with Other Modules

*   **`ExecutionManager`**: An optional but highly recommended dependency that provides robust process management, monitoring, and adaptive timeout capabilities for the sandboxed execution.
*   **Standard Python Libraries**: Heavily relies on `tempfile`, `subprocess`, `json`, `os`, `sys`, `importlib.util`, and `traceback` for its core functionalities related to process management, temporary file operations, and dynamic code execution.
*   **`ToolDispatcher`**: Would likely be a primary consumer of this service, using it to safely execute dynamically generated or untrusted tools and plugins within the AI system.
*   **`CreationEngine`**: Could use the `SandboxExecutor` to test newly generated code snippets or tools in isolation before integrating them into the main system.

## Code Location

`src/services/sandbox_executor.py`