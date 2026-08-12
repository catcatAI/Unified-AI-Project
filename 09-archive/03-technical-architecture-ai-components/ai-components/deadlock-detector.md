# DeadlockDetector: Concurrency and Resource Leak Detection for AI Systems

## Overview

This document provides an overview of the `DeadlockDetector` module (`src/core_ai/test_utils/deadlock_detector.py`). This module offers a suite of utilities designed to detect deadlocks, infinite loops, and various types of resource leaks (threads, file descriptors, memory, asynchronous tasks) within Python applications, making it particularly useful for testing and debugging complex AI systems.

## Purpose

The primary purpose of the `DeadlockDetector` module is to enhance the reliability, stability, and performance of complex AI systems by proactively identifying and reporting common concurrency and resource management issues. By pinpointing problematic code sections that might lead to system hangs, crashes, or performance degradation, it helps developers build more robust and efficient AI applications.

## Key Responsibilities and Features

*   **Deadlock Detection (`DeadlockDetector` class)**:
    *   Monitors active threads and their execution frames in real-time.
    *   Detects potential deadlocks by identifying threads that remain stuck at the same code location for an extended period.
    *   Provides detailed reports of potential deadlocks, including relevant stack traces, to aid in debugging.
*   **Loop Detection (`LoopDetector` class)**:
    *   Tracks iteration counts for specific code locations within loops.
    *   Identifies potential infinite loops if the iteration count for a given location exceeds a predefined `max_iterations` threshold.
*   **Resource Leak Detection (`ResourceLeakDetector` class)**:
    *   Monitors critical system resources such as the number of active threads, open file descriptors, and memory usage.
    *   Reports potential resource leaks if resource consumption significantly increases from an initial baseline, indicating unreleased resources.
*   **Async Leak Detection (`AsyncLoopDetector` class)**:
    *   Specifically designed for asynchronous Python applications, it monitors the number of pending asynchronous tasks in the `asyncio` event loop.
    *   Detects potential async leaks if the number of pending tasks exceeds a `max_pending_tasks` threshold, which can indicate unawaited coroutines or improperly managed async operations.
*   **Convenient Integration (Context Managers and Decorators)**:
    *   `deadlock_detection` (context manager): Provides a straightforward way to enable comprehensive deadlock, resource, and async leak detection for a specific block of code.
    *   `loop_detection` (decorator): Can be applied to both synchronous and asynchronous functions to automatically monitor for infinite loops within their execution.
    *   `timeout_with_detection` (decorator): Combines standard function timeout functionality with optional integrated deadlock detection, offering a robust solution for preventing hangs.
*   **Detection Results**: Utilizes a `DetectionResult` dataclass to encapsulate the outcome of each detection. This includes the `detection_type`, a boolean `detected` flag, a `details` string, and optional `stack_trace`, `thread_info`, or `resource_info` for in-depth analysis.

## How it Works

The module employs a variety of monitoring techniques. For deadlock detection, it periodically inspects the stack frames of active threads to identify prolonged inactivity at specific code points. Loop detection relies on manual instrumentation (developers insert calls to `check_iteration` within loops). Resource leaks are identified by taking snapshots of resource usage at different times and comparing them against a baseline. Asynchronous leaks are detected by monitoring the state of the `asyncio` event loop and its pending tasks.

## Integration with Other Modules

*   **Standard Python Libraries**: Leverages `asyncio`, `threading`, `signal`, `inspect`, and `traceback` for its core monitoring and introspection capabilities.
*   **`psutil`**: A third-party library used for more detailed system and process-level resource monitoring.
*   **Testing Frameworks**: This module is primarily intended to be integrated with unit testing frameworks (e.g., `pytest`, `unittest`) to automatically detect and report concurrency and resource issues during test runs, ensuring code quality and stability.

## Code Location

`src/core_ai/test_utils/deadlock_detector.py`