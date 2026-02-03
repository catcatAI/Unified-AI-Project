# MCPConnector: Management Control Protocol Connector

## Overview

This document provides an overview of the `MCPConnector` module (`src/mcp/connector.py`). This module is responsible for managing the connection for the Management Control Protocol (MCP), providing a robust and reliable way to send and receive control commands between AI entities.

## Purpose

The `MCPConnector` enables efficient and resilient command and control communication within the AI ecosystem. It allows one AI entity (e.g., a central orchestrator or a human operator) to send specific commands to another AI entity (e.g., a specialized agent) and receive responses. A key feature is its ability to leverage fallback mechanisms, ensuring communication even in the presence of network issues.

## Key Responsibilities and Features

*   **Primary MQTT Communication**: Utilizes the `paho.mqtt.client` library for its primary communication channel over MQTT. This provides a standard, lightweight, and efficient messaging protocol.
*   **Command Handling**:
    *   **`send_command`**: Provides a method to send a control command to a target AI. Commands include a `command_name` (e.g., "shutdown", "reboot", "update_config") and associated `parameters`.
    *   **`register_command_handler`**: Allows other modules to register callback functions that will be invoked when a specific incoming command is received. This enables a flexible and extensible command processing system.
*   **Fallback Protocols**: 
    *   Integrates with and manages fallback communication protocols (handled by `mcp_fallback_protocols`). If the primary MQTT connection is unavailable, the connector can automatically attempt to send commands via these alternative channels.
    *   Supports operation in multi-process environments with fallback, enhancing its robustness in complex deployments.
*   **Connection Management**: Handles the lifecycle of the MQTT connection, including connecting to and disconnecting from the MQTT broker.
*   **Health Check**: Provides a `health_check` method that reports the operational status of both the primary MQTT connection and the configured fallback protocols, offering insights into the communication health.

## How it Works

Upon initialization, the `MCPConnector` creates an MQTT client and attempts to connect to a specified broker. It subscribes to MQTT topics relevant to its `ai_id` to receive incoming control commands. When a `send_command` request is made, the connector first attempts to publish the command via the primary MQTT connection. If this connection is not available or fails, it transparently attempts to send the command via the configured fallback protocols. Incoming commands, whether from MQTT or a fallback channel, are parsed, and if a handler is registered for that command, the corresponding callback function is invoked.

## Integration with Other Modules

*   **`paho.mqtt.client`**: The core external library used for MQTT communication.
*   **`mcp_fallback_protocols`**: Manages the alternative communication channels, providing resilience to the MCP.
*   **`core_services`**: Likely initializes and manages the singleton instance of the `MCPConnector` as part of the overall system startup.
*   **`ProjectCoordinator` and `AgentManager`**: These modules would be primary consumers of the `MCPConnector`, using it to send and receive control commands to manage the behavior and state of various AI components and agents.

## Code Location

`src/mcp/connector.py`