# Main API Server: External Interface to the Unified AI

## Overview

The `main_api_server.py` (`src/services/main_api_server.py`) defines the **FastAPI application** that serves as the primary external interface to the Unified-AI-Project. It exposes a comprehensive set of RESTful API endpoints, allowing external clients (such as web frontends, mobile applications, or other services) to interact with the AI's core functionalities, including chat, session management, HSP-related tasks, and integrations with Atlassian and Rovo Dev.

This module is crucial for making the AI's capabilities accessible and consumable by a wide range of applications, providing a structured, validated, and well-documented entry point into the AI ecosystem.

## Key Responsibilities and Features

1.  **FastAPI Application**: 
    *   Built using the FastAPI framework, providing automatic OpenAPI (Swagger UI) documentation, data validation (via Pydantic models), and high performance.

2.  **Service Lifecycle Management**: 
    *   Utilizes FastAPI's `lifespan` context manager to gracefully initialize and shut down all core AI services (e.g., `DialogueManager`, `HAMMemoryManager`, `HSPConnector`) when the API server starts and stops.

3.  **CORS Middleware**: 
    *   Includes Cross-Origin Resource Sharing (CORS) middleware, enabling secure communication from web browsers hosted on different origins (e.g., a React frontend).

4.  **Dependency Injection**: 
    *   Leverages FastAPI's dependency injection system (`Depends`) to provide instances of core services like `AtlassianBridge` and `RovoDevAgent` to API endpoints, promoting modularity and testability.

5.  **Comprehensive API Endpoints**: 
    *   **Core AI Interaction**: `/chat`, `/api/v1/chat` (for general AI conversation), `/api/v1/session/start` (for session management).
    *   **System Monitoring**: `/status`, `/services/health`, `/metrics` (for real-time insights into AI system health and performance).
    *   **HSP Integration**: `/api/v1/hsp/services` (list available HSP capabilities), `/api/v1/hsp/tasks` (request a task from another HSP AI), `/api/v1/hsp/tasks/{correlation_id}` (get task status).
    *   **Atlassian Integration**: Endpoints for configuring Atlassian connections, testing connections, and performing operations on Confluence (e.g., create/get pages, list spaces) and Jira (e.g., create/search issues, list projects).
    *   **Rovo Dev Agent Integration**: Endpoints for getting Rovo Dev Agent status, submitting tasks, and retrieving task history.

6.  **Integration with Core Services**: 
    *   Relies heavily on the `get_services()` utility to access and orchestrate interactions with various core AI components, demonstrating how the API server acts as a facade for the entire AI system.

## How it Works

The `main_api_server.py` initializes the FastAPI application and defines all the API routes. When a request comes in, FastAPI handles routing, data validation (using Pydantic models defined in `api_models.py`), and then calls the appropriate asynchronous endpoint function. These functions interact with the core AI services (retrieved via `get_services()`) to process the request and return a structured JSON response. The `lifespan` context manager ensures that all necessary AI services are properly set up before the server starts accepting requests and cleanly shut down when it stops.

## Code Location

`src/services/main_api_server.py`
