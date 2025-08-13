# CoreServices: Centralized Service Initialization and Management

## Overview

This document provides an overview of the `core_services.py` module (`src/core_services.py`). This module acts as the central nervous system of the AI, responsible for instantiating, connecting, and providing access to all major components of the system.

## Purpose

The primary purpose of `core_services.py` is to ensure that all parts of the AI have access to the same, single instances of core services. It manages the lifecycle of these services, from initialization to shutdown, preventing state inconsistencies and promoting a clean, modular architecture.

## Key Responsibilities and Features

*   **Singleton Management**: Defines and manages global singleton instances for all core services and modules, such as `llm_interface_instance`, `ham_manager_instance`, `hsp_connector_instance`, and `dialogue_manager_instance`. This ensures that there is only one instance of each critical component, which is essential for maintaining a consistent state.
*   **Comprehensive Service Initialization (`initialize_services`)**: Provides a single, asynchronous function that initializes all services in a specific, dependency-aware order. This function handles:
    *   Loading configurations.
    *   Connecting to external services (like MQTT brokers for HSP and MCP).
    *   Wiring up callbacks and dependencies between different modules.
*   **Dependency Injection**: Performs dependency injection by passing initialized service instances to other services that depend on them. For example, it passes the `MultiLLMService` instance to the `DialogueManager` and the `HAMMemoryManager` to the `LearningManager`, ensuring that all components are correctly interconnected.
*   **Configuration Management**: Accepts a configuration dictionary that allows for the customization of service initialization, including the AI's unique ID, HSP broker details, and other operational parameters.
*   **Graceful Shutdown (`shutdown_services`)**: Provides a dedicated function to gracefully shut down all active services. This includes disconnecting from the HSP broker, terminating any running agents, and closing the LLM interface, ensuring a clean exit.
*   **Centralized Service Access (`get_services`)**: Offers a convenient helper function that returns a dictionary of all initialized service instances. This provides a single, consistent way for any part of the application to access the services it needs.
*   **Demo Mode Detection**: Includes logic to detect if the application is running in a demo mode (based on the presence of certain credentials) and activates a `DemoLearningManager` accordingly, which can alter the AI's learning behavior for demonstration purposes.

## How it Works

At application startup, the `initialize_services` function is called. This function systematically instantiates each core service, passing the necessary configurations and dependencies to their respective constructors. It establishes connections to external systems like the HSP and MCP brokers and registers callbacks for inter-service communication (e.g., routing HSP messages to the appropriate handlers). The initialized service instances are stored in global singleton variables, which can then be accessed by other parts of the application via the `get_services` function.

## Integration with Other Modules

This module is the central integration point for nearly all other modules in the system. It imports and initializes services and modules from:

*   `core_ai` (including `AgentManager`, `DialogueManager`, `LearningManager`, etc.)
*   `services` (including `MultiLLMService`, `AIVirtualInputService`, `VisionService`, etc.)
*   `hsp` (the `HSPConnector`)
*   `mcp` (the `MCPConnector`)
*   `tools` (the `ToolDispatcher`)

## Code Location

`src/core_services.py`