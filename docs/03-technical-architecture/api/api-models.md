# API Models: Data Structures for API Interactions

## Overview

The `api_models.py` (`src/services/api_models.py`) module defines the **Pydantic models** used for structuring and validating data exchanged via the Unified-AI-Project's API. These models ensure data consistency, provide clear documentation of expected inputs and outputs, and enable automatic data validation and serialization/deserialization.

This module is crucial for maintaining a robust and predictable API, facilitating seamless integration with frontend applications, external services, and internal AI components.

## Key Models and Their Purpose

### 1. Core Interaction Models

-   **`UserInput`**:
    *   Represents the structure of data received from a user.
    *   Fields: `user_id` (string), `session_id` (string), `text` (string).

-   **`AIOutput`**:
    *   Defines the structure of responses sent back to the user from the AI.
    *   Fields: `response_text` (string), `user_id` (string), `session_id` (string), `timestamp` (string).

-   **`SessionStartRequest`**:
    *   Used when a client initiates a new session.
    *   Fields: `user_id` (string).

-   **`SessionStartResponse`**:
    *   The response returned upon successful session initiation.
    *   Fields: `greeting` (string), `session_id` (string), `timestamp` (string).

### 2. HSP Task Models

-   **`HSPTaskRequestInput`**:
    *   Defines the structure for requesting a task from an HSP-enabled AI agent.
    *   Fields: `target_capability_id` (string), `parameters` (dictionary of any type).

-   **`HSPTaskRequestOutput`**:
    *   The response indicating the status of an HSP task request.
    *   Fields: `status_message` (string), `correlation_id` (optional string), `target_capability_id` (string), `error` (optional string).

-   **`HSPTaskStatusOutput`**:
    *   Provides updates on the status of an ongoing HSP task.
    *   Fields: `correlation_id` (string), `status` (string, e.g., "pending", "completed", "failed", "unknown_or_expired"), `message` (optional string), `result_payload` (optional dictionary), `error_details` (optional dictionary).

### 3. Atlassian Integration Models

-   **`AtlassianConfigModel`**:
    *   Represents the configuration parameters required for connecting to Atlassian services.
    *   Fields: `domain` (string), `userEmail` (string), `apiToken` (string), `cloudId` (string).

-   **`ConfluencePageModel`**:
    *   Defines the structure for creating or updating a Confluence page.
    *   Fields: `spaceKey` (string), `title` (string), `content` (string), `parentId` (optional string).

-   **`JiraIssueModel`**:
    *   Defines the structure for creating a Jira issue.
    *   Fields: `projectKey` (string), `summary` (string), `description` (string), `issueType` (string, default "Task"), `priority` (string, default "Medium").

### 4. Rovo Dev Task Model

-   **`RovoDevTaskModel`**:
    *   Represents a task to be delegated to the Rovo Dev Agent.
    *   Fields: `capability` (string), `parameters` (dictionary of any type).

### 5. JQL Search Model

-   **`JQLSearchModel`**:
    *   Defines the structure for performing a JQL (Jira Query Language) search.
    *   Fields: `jql` (string).

## How it Works

These Pydantic models are used throughout the API layer to define the expected shape of JSON data. When an API endpoint receives data, Pydantic automatically validates it against the corresponding model, raising errors if the data does not conform. This ensures that only well-formed data enters the system. Similarly, when the API sends data, Pydantic serializes the Python objects into JSON, ensuring the output adheres to the defined schema.

## Integration and Importance

-   **API Endpoints**: Directly used by FastAPI (or similar web frameworks) to define request bodies and response models for API endpoints.
-   **Data Validation**: Provides automatic data validation, reducing boilerplate code and improving reliability.
-   **Documentation**: Pydantic models automatically generate OpenAPI (Swagger) documentation, making the API easier to understand and consume for external clients and internal developers.
-   **Type Safety**: Enhances type safety within the Python codebase, making development more robust.

## Code Location

`src/services/api_models.py`
