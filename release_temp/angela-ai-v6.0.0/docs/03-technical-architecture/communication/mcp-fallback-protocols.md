# MCP Fallback Protocols: Resilient Multi-Agent Communication

## Overview

The `mcp_fallback_protocols.py` (`src/mcp/fallback/mcp_fallback_protocols.py`) module implements the **Model Context Protocol (MCP) Fallback System**. This system is designed to ensure continuous and reliable communication between AI entities within the Unified-AI-Project, even when the primary MCP communication channels are unavailable or degraded.

It provides a robust mechanism for maintaining basic communication support through a hierarchy of alternative protocols, ensuring the system's resilience and operational continuity in adverse conditions.

## Key Responsibilities and Features

1.  **Fallback Protocol System**: 
    *   Offers a layered approach to communication, allowing the system to gracefully degrade to alternative protocols if higher-priority ones fail.
    *   Ensures that critical commands and messages can still be exchanged, preventing complete communication blackouts.

2.  **Multiple Protocol Implementations**: 
    *   **`MCPInMemoryProtocol`**: For intra-process communication, ideal for asynchronous tasks within a single Python process. (Lowest priority)
    *   **`MCPProcessSharedMemoryProtocol`**: Designed for inter-process communication within the same machine, leveraging shared memory concepts (though implemented with `asyncio.Queue` for asynchronous handling).
    *   **`MCPFileProtocol`**: Enables inter-process communication by writing and reading messages to/from the filesystem. This is a robust option for persistent and cross-process messaging. (Medium priority)
    *   **`MCPHTTPProtocol`**: Provides communication over HTTP, allowing for network-based communication between different machines or services. Includes node discovery via UDP broadcast. (Highest priority)

3.  **Protocol Prioritization and Health Checks**: 
    *   **`MCPFallbackManager`**: The central orchestrator that manages all registered fallback protocols.
    *   Protocols are assigned a `priority`, and the manager attempts to use the highest-priority active and healthy protocol.
    *   Regular `health_check` mechanisms are implemented for each protocol to determine its operational status (`ACTIVE`, `DEGRADED`, `FAILED`, `DISABLED`).
    *   The manager automatically switches to a lower-priority protocol if the active one becomes unhealthy.

4.  **Message Format (`MCPFallbackMessage`)**: 
    *   Defines a standardized message format for all fallback communications, including `id` (UUID), `sender_id`, `recipient_id`, `command_name`, `parameters`, `timestamp`, `priority`, `correlation_id`, `retry_count`, `max_retries`, and `ttl` (time-to-live).

5.  **Command Handling**: 
    *   The `BaseMCPFallbackProtocol` provides an abstract interface for `send_command`, `start_listening`, `stop_listening`, and `health_check`.
    *   It also includes a `register_command_handler` mechanism, allowing different parts of the system to register callbacks for specific command names.

## How it Works

Upon initialization, the `MCPFallbackManager` attempts to initialize and start listening on all registered protocols, prioritizing them. It continuously monitors the health of the active protocol. When a command needs to be sent, the manager selects the highest-priority healthy protocol and attempts to send the message. If sending fails, it retries and, if necessary, attempts to switch to a lower-priority protocol. Received messages are dispatched to registered command handlers.

## Integration with Other Modules

-   **`mcp/connector.py`**: The MCP Connector would likely utilize the `MCPFallbackManager` to send and receive messages, especially when the primary MCP channel is not available.
-   **Core AI Components**: Various AI modules that need to communicate with each other can leverage this fallback system for robust messaging.
-   **`mcp/types.py`**: Defines the data structures that are used within the MCP, including the fallback messages.

## Code Location

`src/mcp/fallback/mcp_fallback_protocols.py`
