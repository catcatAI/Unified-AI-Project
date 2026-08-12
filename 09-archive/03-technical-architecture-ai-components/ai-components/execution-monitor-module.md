# ExecutionMonitor: Intelligent Execution Monitoring and Adaptive Timeout Management

## Overview

This document provides an overview of the `ExecutionMonitor` module (`src/core_ai/execution_monitor.py`). This module offers intelligent execution monitoring capabilities, encompassing terminal responsiveness detection, process health monitoring, and adaptive timeout management for various commands and processes.

## Purpose

The primary purpose of the `ExecutionMonitor` is to significantly enhance the reliability and efficiency of executing external commands or processes within the AI system. It aims to prevent commands from hanging indefinitely, detect unresponsive environments, and dynamically adapt execution parameters based on real-time system health and historical performance data. This ensures smoother operations and more robust AI behavior.

## Key Responsibilities and Features

*   **Command Execution (`execute_command`, `execute_async_command`)**:
    *   Provides robust methods for executing shell commands, supporting both synchronous and asynchronous operations.
    *   Captures standard output (`stdout`) and standard error (`stderr`) for detailed logging and analysis.
    *   Manages the full process lifecycle, including graceful termination attempts and forceful killing if a command exceeds its allocated time or becomes unresponsive.
*   **Adaptive Timeout Calculation (`calculate_adaptive_timeout`)**:
    *   Dynamically adjusts command timeouts based on a sophisticated algorithm that considers historical execution times, current terminal responsiveness, and configurable minimum/maximum limits.
    *   Utilizes an in-memory cache to store calculated timeouts for frequently executed commands, optimizing performance.
*   **Terminal Responsiveness Check (`check_terminal_responsiveness`)**:
    *   Periodically assesses the responsiveness of the underlying terminal or shell environment by running a simple command and measuring its execution time.
    *   Categorizes terminal status as `RESPONSIVE`, `SLOW`, `STUCK`, or `UNRESPONSIVE`, providing critical insights into environmental health.
*   **Resource Monitoring (`_monitor_resources`)**:
    *   Continuously monitors key system resources, including CPU, memory, and disk usage, leveraging the `psutil` library.
    *   Logs warnings when resource utilization exceeds predefined thresholds, alerting to potential performance bottlenecks.
*   **Process Health Check (`is_process_stuck`)**: Offers a method to determine if a specific process is stuck or unresponsive by analyzing its CPU time over a defined duration.
*   **System Health Reporting (`get_system_health`)**: Provides a comprehensive snapshot of the overall system health, including real-time metrics for CPU, memory, disk, and the current terminal status.
*   **Global Instance**: Exposes a global, singleton `ExecutionMonitor` instance (`get_execution_monitor`) for convenient and consistent access across different parts of the application.

## How it Works

The `ExecutionMonitor` acts as an intelligent wrapper around standard `subprocess` calls. It operates by initiating separate background threads for continuous terminal responsiveness and system resource monitoring. Before executing any command, it dynamically calculates an adaptive timeout based on its collected data. During command execution, it actively monitors the process and overall system health. If a command times out or a process is detected as unresponsive, the monitor attempts a graceful termination, escalating to a forceful kill if necessary.

## Integration with Other Modules

*   **`subprocess`**: The core Python module that `ExecutionMonitor` uses to interact with and control external processes.
*   **`psutil`**: An essential third-party library utilized for detailed system and process monitoring, providing metrics like CPU and memory usage.
*   **`threading` and `asyncio`**: Employed for managing concurrent and asynchronous operations, allowing the monitor to perform its checks without blocking the main application flow.
*   **System Components**: Any module within the AI system that needs to execute external commands reliably and with intelligent oversight would integrate with this `ExecutionMonitor`.

## Code Location

`src/core_ai/execution_monitor.py`