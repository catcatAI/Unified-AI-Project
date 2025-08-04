# MCP Connector: Management Control Protocol Communication

## Overview

The `MCPConnector` (`src/mcp/connector.py`) is a specialized communication component within the Unified-AI-Project responsible for handling the **Management Control Protocol (MCP)**. MCP is designed for low-level control, coordination, and direct command execution between AI entities, often bypassing the higher-level HSP for critical or direct operational instructions.

This module ensures that AI instances can reliably send and receive commands, even in challenging network conditions, by leveraging MQTT as the primary transport and implementing robust fallback mechanisms.

## Key Responsibilities and Features

1.  **MQTT Communication**: 
    *   Utilizes the `paho.mqtt.client` library to establish and maintain connections with an MQTT broker.
    *   Handles publishing MCP command requests and subscribing to relevant topics for command responses and broadcasts.

2.  **Command Handling and Registration**: 
    *   Allows other modules to `register_command_handler` functions for specific MCP command names.
    *   When an MCP command is received, the `MCPConnector` dispatches it to the appropriate registered handler.

3.  **Robust Fallback Mechanisms**: 
    *   A critical feature that ensures communication resilience. If the primary MQTT connection is unavailable, the `MCPConnector` can initialize and use various fallback protocols (managed by `MCPFallbackManager`).
    *   This guarantees that critical control commands can still be delivered, even in degraded network environments.

4.  **MCP Message Encapsulation**: 
    *   Handles the creation and parsing of `MCPEnvelope` messages, which encapsulate `MCPCommandRequest` and `MCPCommandResponse` payloads.
    *   Ensures messages conform to the defined MCP schema (`src/mcp/types.py`).

5.  **Communication Status and Health Checks**: 
    *   Provides methods (`get_communication_status`, `health_check`) to monitor the current state of the MCP connection and the health of the fallback protocols.

## How it Works

The `MCPConnector` connects to an MQTT broker and subscribes to topics relevant to its AI instance (e.g., `mcp/broadcast`, `mcp/unicast/{ai_id}`). When an AI needs to send a control command, it calls `send_command`, which constructs an MCP message and attempts to publish it via MQTT. If MQTT is unavailable, it seamlessly switches to a configured fallback protocol to ensure delivery. Incoming MCP messages are received, parsed, and then dispatched to the appropriate registered command handlers within the AI system.

## Integration with Other Modules

-   **`ProjectCoordinator`**: May use the `MCPConnector` for direct control and coordination of sub-agents or external systems.
-   **`AgentManager`**: Could potentially receive MCP commands to manage the lifecycle of agents (e.g., start, stop, restart).
-   **`HSPConnector`**: While HSP handles higher-level semantic communication, MCP provides a complementary channel for direct operational control.
-   **`MCPFallbackManager`**: The underlying system that provides the various fallback communication channels (e.g., in-memory, file-based) when MQTT is not available.

## Code Location

`src/mcp/connector.py`
