# HotReloadService: Dynamic Hot-Reload and Hot-Drain for Core AI Services

## Overview

This document provides an overview of the `HotReloadService` module (`src/services/hot_reload_service.py`). Its primary function is to offer minimal, safe primitives for hot-reloading and hot-draining core AI services within the Unified-AI-Project, particularly those managed as global singletons.

This module is crucial for enabling continuous development, deployment, and maintenance in a production environment. It allows for dynamic updates and graceful restarts of critical AI components (like LLM services and HSP connectors) without requiring a full application restart, thereby minimizing downtime and disruption.

## Key Responsibilities and Features

*   **Hot-Draining Primitives (`begin_draining`, `end_draining`)**: Provides an advisory flag (`_draining`) that components can check. When `begin_draining` is called, this flag is set, signaling to other parts of the system that the service is preparing for a reload or shutdown. Components can then gracefully complete ongoing work and refuse new tasks, ensuring a smooth transition.
*   **Service Status Reporting (`status`)**: Returns the current draining status of the service and indicates which core services are currently initialized, providing real-time operational insights.
*   **LLM Service Hot-Reload (`reload_llm`)**: Implements a safe hot-reload mechanism for the `MultiLLMService`. This involves:
    *   Gracefully closing the existing LLM interface instance.
    *   Instantiating a new `MultiLLMService` instance (potentially with updated configurations).
    *   Atomically swapping the global reference to the LLM service.
    *   Rewiring dependent components (such as `ToolDispatcher` and `DialogueManager`) to ensure they use the newly loaded LLM service.
    *   Includes robust error handling to prevent failures during the reload process.
*   **HSP Connector Hot-Reload (`reload_hsp`)**: Provides a "blue/green" style hot-reload for the `HSPConnector`. This process involves:
    *   Constructing a new `HSPConnector` instance using the existing AI ID and broker settings.
    *   Connecting the new connector and re-subscribing to all essential HSP topics.
    *   Swapping the global reference to the HSP connector to the new instance.
    *   Gracefully disconnecting the old connector, ensuring no messages are lost during the transition.
    *   Rewiring `ServiceDiscoveryModule` callbacks to the new connector.

## How it Works

The `HotReloadService` utilizes an `asyncio.Lock` to ensure thread-safe operations during reloads, preventing race conditions. The core principle for both LLM and HSP reloads is to instantiate and prepare the new service instance *before* swapping it with the old one. This minimizes the window of unavailability and ensures that the system remains functional throughout the reload process. The service manages global singleton references, making the swap effective across the application.

## Integration with Other Modules

*   **`src.core_services`**: Directly interacts with the global singleton instances managed by `src.core_services`, including `llm_interface_instance`, `hsp_connector_instance`, `tool_dispatcher_instance`, and `dialogue_manager_instance`.
*   **`MultiLLMService`**: The primary target for LLM hot-reloads, allowing its underlying models or configurations to be updated dynamically.
*   **`HSPConnector`**: The primary target for HSP hot-reloads, enabling updates to communication parameters or underlying MQTT connections.
*   **`ToolDispatcher`, `DialogueManager`, `ServiceDiscoveryModule`**: These components are explicitly rewired by the `HotReloadService` to ensure they correctly reference the newly loaded service instances.
*   **`asyncio`**: Provides the asynchronous primitives necessary for non-blocking operations and managing concurrent tasks during reloads.

## Code Location

`src/services/hot_reload_service.py`