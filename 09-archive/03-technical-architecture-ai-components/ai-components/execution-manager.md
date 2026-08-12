# ExecutionManager: Unified Execution Management System

## Overview

This document provides an overview of the `ExecutionManager` module (`src/core_ai/execution_manager.py`). Its primary function is to provide a unified and intelligent system for managing command execution, integrating monitoring, adaptive timeout control, and automatic recovery mechanisms within the Unified-AI-Project.

This module is crucial for ensuring the robustness, reliability, and efficiency of AI operations, especially when executing external commands, interacting with system resources, or running potentially long-running tasks.

## Key Responsibilities and Features

*   **Comprehensive Configuration (`ExecutionManagerConfig`)**: A detailed dataclass that allows for extensive configuration of the manager's behavior, including enabling/disabling features, setting timeout parameters, defining resource usage thresholds (CPU, memory, disk), configuring adaptive timeout parameters, specifying retry and recovery strategies, and controlling logging verbosity.
*   **Intelligent Command Execution (`execute_command`, `execute_async_command`)**: Provides both synchronous and asynchronous methods to execute commands. These methods wrap the core execution logic with advanced features like adaptive timeouts, automatic retries on failure, and real-time monitoring.
*   **Adaptive Timeout Control**: Dynamically adjusts the timeout duration for commands based on historical execution data, terminal responsiveness, and current system load. This prevents premature termination of legitimate long-running tasks while still catching stuck processes.
*   **System Resource Monitoring**: Continuously monitors critical system resources (CPU, memory, disk usage) against configurable warning and critical thresholds. If thresholds are exceeded, it can trigger alerts or automatic recovery actions.
*   **Automatic Recovery Mechanisms**: Implements strategies to recover from common execution issues, such as triggering garbage collection for high memory usage, or suggesting CPU/disk optimization. It also supports configurable retry attempts and delays for failed commands.
*   **Execution Statistics and Health Reporting**: Collects and maintains detailed statistics on command executions (total, successful, failed, timeouts, recovered). It can generate a comprehensive system health report that includes resource usage, execution metrics, and logs of recent issues and recovery actions.
*   **Context Manager Integration**: Can be used as a Python context manager (`with ExecutionManager() as manager:`) to automatically start and stop its continuous health monitoring thread, simplifying its integration into application lifecycles.
*   **Global Singleton Access**: Provides a `get_execution_manager()` function to ensure a single, globally accessible instance of the manager, promoting consistent behavior and resource management across the application.

## How it Works

The `ExecutionManager` loads its operational parameters from a system configuration file (e.g., `configs/system_config.yaml`) or uses default values. It initializes an `ExecutionMonitor` (from `execution_monitor.py`) to handle the low-level process management and basic monitoring. A separate daemon thread is launched for continuous system health monitoring, which periodically checks resource usage and triggers configured recovery actions or logs issues. When a command is executed via `execute_command`, the manager applies adaptive timeout logic, handles retries based on configured strategies, and updates its internal execution statistics.

## Integration with Other Modules

*   **`ExecutionMonitor`**: The core underlying component responsible for the actual process execution, timeout enforcement, and basic system health checks.
*   **Configuration System**: Relies on external YAML configuration files for its operational parameters.
*   **Logging**: Integrates with the standard Python logging system for detailed operational insights and error reporting.
*   **Core AI Components**: Other AI modules (e.g., `ProjectCoordinator`, `ToolDispatcher`) would utilize the `execute_with_smart_monitoring` or `execute_async_with_smart_monitoring` convenience functions to ensure robust and monitored execution of their tasks.

## Code Location

`src/core_ai/execution_manager.py`