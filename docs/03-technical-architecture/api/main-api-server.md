# MainAPIServer: Exposing AI Services via a RESTful API

## Overview

This document provides an overview of the `main_api_server.py` module (`src/services/main_api_server.py`). This module serves as the main entry point for the FastAPI application, defining all API endpoints and managing the application's lifecycle.

## Purpose

The primary purpose of the `main_api_server` is to expose the AI's capabilities and services through a RESTful API. This allows external clients, such as a web dashboard, mobile applications, or other third-party services, to interact with the AI, send commands, retrieve information, and monitor its status in a standardized way.

## Key Responsibilities and Features

*   **FastAPI Application**: The core of the module is a `FastAPI` application instance, which provides a modern, high-performance framework for building APIs.
*   **Lifecycle Management (`lifespan`)**: Utilizes FastAPI's `lifespan` context manager to ensure that all core services are initialized (`initialize_services`) when the application starts up and are gracefully shut down (`shutdown_services`) when the application stops. This is crucial for managing resources and connections effectively.
*   **CORS Middleware**: Configures Cross-Origin Resource Sharing (CORS) to allow requests from specific origins, such as a frontend development server, ensuring secure communication between the frontend and backend.
*   **Comprehensive API Endpoints**: Defines a rich set of API endpoints to expose the AI's functionalities:
    *   **Chat and Session Management**: Includes `/api/v1/chat` for real-time user interaction and `/api/v1/session/start` for managing conversational sessions.
    *   **HSP Interaction**: Provides endpoints for listing discovered HSP services (`/api/v1/hsp/services`), requesting tasks from other AIs on the network (`/api/v1/hsp/tasks`), and polling for the status of those tasks (`/api/v1/hsp/tasks/{correlation_id}`).
    *   **External Integrations**: Offers endpoints for configuring and interacting with external services like Atlassian (Jira, Confluence) and the `RovoDevAgent`.
    *   **System Health and Monitoring**: Exposes endpoints like `/api/v1/health`, `/api/v1/system/services`, and `/api/v1/system/metrics/detailed` for monitoring the AI's health, the status of its internal services, and detailed system performance metrics.
    *   **Model and Agent Management**: Includes endpoints for listing available models, routing model requests based on policies, and getting the status of various AI agents.
    *   **Tool Endpoints**: Provides direct access to the AI's tools for tasks like code analysis, web search, and image generation, which are internally routed through the `ToolDispatcher`.
    *   **Hot Reload/Drain**: Exposes endpoints under the `/api/v1/hot` route to allow for the dynamic reloading and draining of services without a full server restart.
*   **Dependency Injection**: Leverages FastAPI's `Depends` system to inject necessary service instances (e.g., `AtlassianBridge`, `RovoDevAgent`) into endpoint functions, promoting clean and testable code.
*   **Pydantic Models**: Utilizes Pydantic models defined in `api_models.py` to structure and validate the request and response bodies for all API endpoints. This ensures data consistency and automatically generates OpenAPI documentation.

## How it Works

The `main_api_server.py` script defines a FastAPI application that is run by an ASGI server like `uvicorn`. The `lifespan` function is a critical component that ensures all backend services are initialized before the server begins to accept requests. When an HTTP request is received, it is routed to the appropriate endpoint function. This function then interacts with the relevant core services (e.g., `DialogueManager`, `ToolDispatcher`, `HAMMemoryManager`) to process the request and generate a response.

## Integration with Other Modules

*   **`core_services`**: This is the most critical integration, as the API server relies on it for initializing, accessing, and shutting down all backend services.
*   **`api_models`**: Used extensively to define the data structures for all API requests and responses.
*   **All Core Services**: The API server acts as the primary interface to a wide range of core services, including `DialogueManager`, `ToolDispatcher`, `AtlassianBridge`, `RovoDevAgent`, and many others.
*   **`fastapi` and `uvicorn`**: The web framework and ASGI server that power the API.

## Code Location

`src/services/main_api_server.py`