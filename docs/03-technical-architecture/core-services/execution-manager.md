# ExecutionManager: Unified Execution Monitoring and Management

## Overview

This document provides an overview of the `ExecutionManager` module (`src/core_ai/execution_manager.py`). This module provides a unified execution management system that integrates monitoring, timeout control, and automatic recovery mechanisms for running external commands and processes.

## Purpose

The `ExecutionManager` is designed to provide a robust and intelligent way to execute external commands. It goes beyond a simple `subprocess.run` by adding layers of monitoring, resilience, and adaptive control. This is crucial for a reliable AI system that needs to interact with external tools, environments, and potentially unpredictable processes.

## Key Responsibilities and Features

*   **Intelligent Timeout Control**:
    *   Utilizes an `ExecutionMonitor` to enforce strict timeouts on command execution.
    *   Supports adaptive timeouts, where the timeout duration can be automatically adjusted based on the historical execution times of similar commands and the current system load.
*   **System Resource Monitoring**:
    *   Actively monitors system resources, including CPU, memory, and disk usage.
    *   Can be configured to trigger warnings or critical alerts if resource usage exceeds predefined thresholds, which can help in preventing system-wide failures.
    *   Provides the option to log resource usage for performance analysis and debugging.
*   **Terminal Monitoring**: Can monitor the responsiveness of the terminal to detect if a process has become stuck or unresponsive, even if it hasn't timed out.
*   **Automatic Recovery Mechanisms**:
    *   Can be configured to automatically retry failed commands based on defined policies (e.g., retry on timeout or if the terminal is unresponsive).
    *   Includes logic for attempting resource recovery, such as triggering Python's garbage collection when memory usage is critically high.
*   **Execution History and Statistics**:
    *   Tracks detailed statistics on all command executions, including the total number of executions, success and failure counts, timeouts, and recoveries.
    *   Calculates and maintains the average execution time and success/failure rates.
    *   Maintains a log of all detected issues and the recovery actions taken.
*   **Comprehensive Configuration**: Loads its configuration from `system_config.yaml`, which allows for fine-grained control over all its features, including timeouts, resource thresholds, and recovery strategies.
*   **Global Singleton Instance**: Provides a `get_execution_manager()` function for easy, global access to a singleton instance of the manager.

## How it Works

The `ExecutionManager` acts as a high-level wrapper around the `ExecutionMonitor`. When a command is to be executed, it is passed to the `ExecutionManager`. The manager first applies its configured policies, such as setting an adaptive timeout. It then delegates the actual execution to the `ExecutionMonitor`. After the command completes, the `ExecutionManager` analyzes the `ExecutionResult`, updates its internal statistics, and, if necessary, decides whether to retry the command or take other recovery actions based on its configuration. It also runs a background thread to continuously monitor the overall system health.

## Integration with Other Modules

*   **`ExecutionMonitor`**: The core component that the `ExecutionManager` uses to perform the actual command execution and low-level monitoring.
*   **`PyYAML`**: Used for loading the detailed configuration from `system_config.yaml`.
*   **`threading`**: Used to run the background health monitoring loop.
*   **`SandboxExecutor` and `AgentManager`**: Any module that needs to execute external commands in a safe, reliable, and monitored manner would be a primary consumer of the `ExecutionManager`.

## Code Location

`src/core_ai/execution_manager.py`