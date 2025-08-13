# BaseAgent: The Foundation for Specialized Sub-Agents

## Overview

This document provides an overview of the `BaseAgent` class (`src/agents/base_agent.py`). This class serves as the foundation for all specialized sub-agents within the Unified-AI-Project.

## Purpose

The `BaseAgent` is designed to provide a common foundation and boilerplate code for all specialized agents. It handles the common tasks of initializing core services, connecting to the Heterogeneous Service Protocol (HSP) network, and advertising capabilities. This allows developers to focus on implementing the unique logic of their specific agent without needing to rewrite the same setup and teardown code.

## Key Responsibilities and Features

*   **Service Initialization (`_ainit`)**: Asynchronously initializes the core services that are required by the agent, such as the `HSPConnector`. This ensures that the agent has access to all the necessary infrastructure.
*   **Lifecycle Management (`start`, `stop`)**:
    *   **`start`**: Connects the agent to the HSP network and automatically advertises its capabilities to other agents and services.
    *   **`stop`**: Gracefully disconnects the agent from the HSP network and shuts down its services.
*   **Capability Advertising**: Automatically advertises the agent's capabilities on the HSP network upon startup. This makes the agent's services discoverable by other components of the AI ecosystem.
*   **Task Handling (`handle_task_request`)**: Provides a placeholder method for handling incoming HSP task requests. Subclasses are expected to override this method to implement their specific task-handling logic. The base implementation simply acknowledges the request and reports that the feature is not implemented.
*   **Health Checking (`is_healthy`)**: Provides a basic health check method to determine if the agent is running and connected to the HSP network. This can be used by the `AgentManager` or other monitoring systems to ensure the agent is functioning correctly.

## How it Works

A specialized agent class should inherit from `BaseAgent`. In its `__init__` method, it should call the parent's `__init__` method, providing its own unique `agent_id` and a list of its `capabilities`. The `AgentManager` is then responsible for creating an instance of the specialized agent and calling its `start` method. Once started, the agent will be connected to the HSP network and will be ready to receive task requests, which will be routed to its `handle_task_request` method.

## Integration with Other Modules

*   **`core_services`**: Used to initialize and access the core services that the agent depends on.
*   **`HSPConnector`**: The primary interface for all communication on the HSP network.
*   **`HSPTaskRequestPayload` and `HSPTaskResultPayload`**: The standardized data structures for receiving task requests and sending back results.
*   **`AgentManager`**: The `AgentManager` is responsible for the lifecycle management of all `BaseAgent` subclasses, including launching, monitoring, and shutting them down.

## Code Location

`src/agents/base_agent.py`