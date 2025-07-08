# AI Simulation Control Service (ASCS)

## Overview

The `AISimulationControlService` (ASCS) is a crucial component within the Unified-AI-Project's simulated environment infrastructure. It acts as a gatekeeper and orchestrator for potentially sensitive AI actions, primarily focusing on:

1.  **AI Permissions Management:**
    *   Loads, manages, and enforces operational permissions for the AI. These permissions dictate what the AI is allowed to do within the simulation, such as executing code or accessing certain information.
    *   Permissions are defined by the `AIPermissionSet` TypedDict (see `src/shared/types/common_types.py`).
    *   Currently, permissions like `can_execute_code` and `can_read_sim_hw_status` are supported.
    *   Permissions can be loaded from a configuration (future) or set to defaults.

2.  **Simulated Hardware Status Reporting:**
    *   Interfaces with the `ResourceAwarenessService` to fetch the current status of the simulated hardware environment (e.g., CPU, disk space, memory).
    *   Provides this information to other services (like AVIS) so it can be displayed to the AI, allowing the AI to make resource-aware decisions.

3.  **AI-Generated Code Execution (Python):**
    *   Provides a mechanism to execute Python code strings provided by the AI.
    *   Before execution, it checks the AI's `can_execute_code` permission.
    *   If permitted, it utilizes the `SandboxExecutor` service (`src/services/sandbox_executor.py`) to run the Python code. The `SandboxExecutor` handles:
        *   Writing the code to a temporary script file.
        *   Executing the script in a separate subprocess, providing a degree of isolation.
        *   Capturing `stdout`, `stderr`, and the script's exit code.
        *   Handling execution timeouts.
    *   ASCS returns the execution outcome as an `ExecutionResult` TypedDict, derived from the results provided by `SandboxExecutor`.

## Key Responsibilities

*   **Security Gateway:** Prevents unauthorized actions by enforcing AI permissions.
*   **Execution Orchestration:** Manages the lifecycle of executing AI-provided code in a controlled manner.
*   **Information Brokering:** Relays simulated hardware status from `ResourceAwarenessService`.
*   **Decoupling:** Separates the concerns of input simulation (AVIS) from the control and execution of potentially powerful AI actions.

## Interaction with Other Services

*   **`AIVirtualInputService` (AVIS):**
    *   ASCS is typically instantiated and used by AVIS.
    *   AVIS queries ASCS for current AI permissions and simulated hardware status to display them in its virtual UI.
    *   When an AI user triggers a "run code" action in the AVIS UI, AVIS passes the code string and its current understanding of AI permissions to ASCS's `execute_ai_code` method.
*   **`ResourceAwarenessService`:**
    *   ASCS takes an instance of `ResourceAwarenessService` during initialization.
    *   It calls methods on this service (e.g., `get_simulated_hardware_profile()`) to retrieve hardware status information.
*   **`SandboxExecutor`:**
    *   ASCS requires an instance of `SandboxExecutor` during its initialization.
    *   It calls `sandbox_executor.execute_python_code()` to run AI-provided Python scripts.

## Future Enhancements

*   Loading AI permissions from a dynamic configuration file.
*   More granular permissions (e.g., allowed importable Python modules, specific file system access controls within the sandbox).
*   Resource-based queuing or rejection of code execution requests (e.g., if simulated CPU is overloaded).
*   Timeouts for AI code execution.
*   Support for executing code in different languages/environments if needed.

This service is vital for enabling more advanced AI agency within the simulated world while maintaining necessary controls and safety measures.
