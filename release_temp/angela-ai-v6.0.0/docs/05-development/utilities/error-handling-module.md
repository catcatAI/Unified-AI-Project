# ErrorHandlingModule: Centralized Error Management for Unified-AI-Project

## Overview

This document provides an overview of the `error.py` module (`src/shared/error.py`). Its primary function is to define custom exception classes for project-specific errors and to provide a central error handling function for the Unified-AI-Project.

This module is crucial for establishing a standardized and centralized mechanism for handling errors across the entire AI system. This approach ensures consistent error reporting, facilitates structured logging, and enables the implementation of robust recovery actions, thereby significantly improving the overall reliability and maintainability of the codebase.

## Key Responsibilities and Features

*   **`ProjectError`**: This is the base custom exception class for all errors that are specific to the Unified-AI-Project's logic or its integrations. It extends Python's built-in `Exception` class and allows for:
    *   A descriptive `message` to explain the error.
    *   An optional `code` (integer, defaulting to 500) to categorize the error, often mapping to HTTP status codes or internal error codes.
*   **`HSPConnectionError`**: A specialized exception class that inherits directly from `ProjectError`. It is specifically designed to represent errors related to connections or communication issues within the Heterogeneous Service Protocol (HSP). It defaults to a 503 status code, indicating a service unavailable issue.
*   **`project_error_handler(error: ProjectError)`**: A central, top-level function intended to process instances of `ProjectError` (or its subclasses). In a production environment, this function would be the integration point for:
    *   **Logging**: Sending detailed error information to a centralized logging system.
    *   **Monitoring**: Triggering alerts in monitoring dashboards.
    *   **Reporting**: Sending error reports to development teams.
    *   **Graceful Degradation**: Initiating fallback mechanisms or graceful shutdown procedures. (Currently, it simply prints the error to the console for development purposes).

## How it Works

When an error condition arises that is specific to the Unified-AI-Project's domain (e.g., a configuration issue, a failed external API call, or an internal logical inconsistency), developers are encouraged to raise a `ProjectError` or a more specific subclass like `HSPConnectionError`. This exception can then be caught by higher-level components using standard Python `try-except` blocks. Once caught, the `ProjectError` instance is passed to the `project_error_handler` function. This centralized handler ensures that all project-specific errors are processed uniformly, providing a consistent approach to error management throughout the application's lifecycle.

## Integration with Other Modules

*   **All Project Modules**: Any module within the Unified-AI-Project that encounters a defined project-specific error condition should raise an instance of `ProjectError` or one of its specialized subclasses.
*   **Communication Modules**: Modules interacting with external protocols like HSP (e.g., `HSPConnector`, `MessageBridge`) would specifically raise `HSPConnectionError` for connectivity issues.
*   **Service Layers and API Endpoints**: Components responsible for exposing services or API endpoints would typically catch these `ProjectError` exceptions and translate them into appropriate API responses or user-friendly error messages.
*   **Logging and Monitoring Systems**: The `project_error_handler` serves as the primary integration point for external logging, monitoring, and alerting infrastructure.

## Code Location

`src/shared/error.py`