# NetworkResilience: Building Robust Networked Applications

## Overview

This document provides an overview of the `network_resilience.py` module (`src/shared/network_resilience.py`). Its primary function is to provide a suite of utilities for building network resilience into applications, including retry policies with exponential backoff and the circuit breaker pattern.

This module is crucial for enhancing the robustness and reliability of AI components that interact with external services or networks. It provides a standardized way to gracefully handle transient network failures, prevent cascading failures, and improve the overall stability and availability of the system.

## Key Responsibilities and Features

*   **Custom Network Exceptions**:
    *   **`NetworkError`**: A custom exception class that indicates a network-related failure that might be transient and, therefore, suitable for retries.
    *   **`ProtocolError`**: A custom exception class that indicates a protocol-level error that is likely not transient and should not be retried.
*   **`RetryPolicy`**: 
    *   Implements a sophisticated retry mechanism with exponential backoff, designed as a decorator for asynchronous functions.
    *   It is highly configurable, allowing for the setting of `max_attempts`, `backoff_factor`, and `max_delay`.
    *   Intelligently retries on `NetworkError` but re-raises `ProtocolError` or other unexpected exceptions immediately, preventing retries on non-transient errors.
*   **`CircuitBreaker`**:
    *   Implements the Circuit Breaker design pattern to prevent an application from repeatedly attempting to execute an operation that is likely to fail.
    *   It is configurable with a `failure_threshold` (the number of consecutive failures before opening the circuit) and a `recovery_timeout` (the time to wait before attempting to close the circuit).
    *   Manages three distinct states: `"CLOSED"` (normal operation), `"OPEN"` (failures have exceeded the threshold, and requests fail fast), and `"HALF_OPEN"` (after the recovery timeout, a single request is allowed to test the health of the service).
    *   Raises a `CircuitBreason` when in the `"OPEN"` state, providing immediate feedback to the caller.
    *   It is also designed as a decorator for asynchronous functions.

## How it Works

*   **Retry Policy**: When an asynchronous function decorated with `@RetryPolicy` encounters a `NetworkError`, the decorator catches the exception and, instead of failing immediately, waits for an exponentially increasing delay before retrying the function. This process is repeated up to a maximum number of attempts.
*   **Circuit Breaker**: The `@CircuitBreaker` decorator monitors the success and failure of calls to a service. If the number of consecutive failures exceeds a defined threshold, it "opens" the circuit. While the circuit is open, all subsequent calls to the decorated function will fail immediately without attempting to reach the service. After a specified timeout, the circuit transitions to a "half-open" state, allowing a single test request to determine if the service has recovered. A successful call will close the circuit, while a failure will keep it open.

## Integration with Other Modules

*   **External Service Integrations**: Any AI component that makes external network calls (e.g., to LLM APIs, external data sources, or databases) should use these decorators to enhance resilience.
*   **`MultiLLMService`**: Could leverage the `@RetryPolicy` decorator for individual LLM API calls to handle transient network issues.
*   **`HSPConnector`**: Could use the `@CircuitBreaker` decorator to manage connections to external brokers, preventing repeated connection attempts to a faulty or unavailable broker.

## Code Location

`src/shared/network_resilience.py`