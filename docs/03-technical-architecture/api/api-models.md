# API Models: Data Structures for Backend Services

## Overview

This document provides a comprehensive overview of the Pydantic models defined in the `src/services/api_models.py` module. These models serve as the standardized data structures for API requests and responses across various backend services and integrations within the Unified-AI-Project.

This module is crucial for ensuring clear, validated, and type-safe data exchange through the RESTful APIs. It facilitates robust API development, enables automatic documentation generation (e.g., via FastAPI), and provides strong data validation, minimizing errors and improving system reliability.

## Key Responsibilities and Features

*   **Data Validation**: Leverages Pydantic's powerful capabilities for automatic data validation. Models enforce type hints, required fields, and can include custom validators, ensuring that all incoming and outgoing data conforms to expected formats.
*   **Serialization and Deserialization**: Provides built-in methods for easy conversion of Python objects to and from JSON (or other formats), which is essential for API communication.
*   **API Request/Response Models**: Defines specific models for common API interactions:
    *   **`UserInput`**: Represents the structure for user input text.
    *   **`AIOutput`**: Defines the structure for AI-generated text responses, including associated metadata.
    *   **`SessionStartRequest`**: For initiating a new conversational session.
    *   **`SessionStartResponse`**: The response returned upon successful session initiation.
    *   **`HSPTaskRequestInput`**: The input structure for requesting a task via the Heterogeneous Service Protocol (HSP).
    *   **`HSPTaskRequestOutput`**: The output structure confirming a task request submission.
    *   **`HSPTaskStatusOutput`**: Provides the status and results of an HSP task, including correlation ID, status, and optional payload or error details.
*   **Integration-Specific Models**: Includes models tailored for specific external service integrations:
    *   **`AtlassianConfigModel`**: For configuring connections to Atlassian services.
    *   **`ConfluencePageModel`**: Represents data for creating or updating Confluence pages.
    *   **`JiraIssueModel`**: Defines the structure for creating Jira issues.
    *   **`RovoDevTaskModel`**: For specifying tasks to be executed by the Rovo Dev agent.
    *   **`JQLSearchModel`**: For performing searches using Jira Query Language (JQL).

## How it Works

All classes in this module inherit from Pydantic's `BaseModel`. When data (e.g., from an incoming HTTP request body) is received by a FastAPI endpoint, Pydantic automatically attempts to parse and validate it against the corresponding model. If the data matches the model's schema, an instance of the model is created, providing type-hinted and validated access to the data. If validation fails (e.g., missing required fields, incorrect data types), Pydantic raises a detailed validation error, which FastAPI can automatically convert into a standardized API error response.

## Integration with Other Modules

*   **`main_api_server.py`**: The primary consumer of these models, using them to define the request and response schemas for its FastAPI endpoints, enabling automatic OpenAPI documentation.
*   **Service Implementations**: Various backend services (e.g., `MultiLLMService`, `HSPConnector`, `AtlassianBridge`, `RovoDevAgent`) consume or produce data that conforms to these models, ensuring consistent data contracts.
*   **FastAPI**: Integrates seamlessly with Pydantic for automatic request body parsing, response serialization, and OpenAPI documentation generation.

## Code Location

`src/services/api_models.py`