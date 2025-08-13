# Context7MCPConnector: Enhanced Model Context Protocol Integration

## Overview

This document provides an overview of the `Context7MCPConnector` module (`src/mcp/context7_connector.py`). This module is designed to provide integration with Context7's Model Context Protocol (MCP), enabling enhanced AI model communication and context management within the unified AI ecosystem.

## Purpose

The `Context7MCPConnector` aims to facilitate advanced context awareness and collaborative AI capabilities. It allows AI models to seamlessly share and retrieve rich contextual information, and to collaborate on complex tasks, moving beyond simple message passing to a more integrated understanding of shared operational context.

## Key Responsibilities and Features

*   **Context Management**:
    *   **`send_context`**: Sends various types of context data (e.g., dialogue context, memory context, task context) to the Context7 MCP service. This allows for real-time updates and synchronization of the AI's operational environment.
    *   **`request_context`**: Requests relevant contextual information from the Context7 MCP service based on a specific query. This enables the AI to retrieve historical or external context pertinent to its current task.
    *   **`compress_context`**: Utilizes Context7's algorithms to compress context data, optimizing it for efficient storage and transmission, especially for large or complex contexts.
*   **Model Collaboration (`collaborate_with_model`)**: Provides a mechanism to initiate and manage collaboration with other AI models through the Context7 MCP. This enables models to work together on shared tasks by exchanging and leveraging common contextual understanding.
*   **Capability Discovery (`_discover_capabilities`, `get_capabilities`)**: Discovers and lists the capabilities that are available from the Context7 MCP service itself, allowing the AI to understand the services offered by the protocol.
*   **Connection Management (`connect`, `disconnect`, `is_connected`)**: Handles the establishment and termination of connections with the Context7 MCP service endpoint.
*   **Configuration (`Context7Config`)**: Uses a dedicated dataclass (`Context7Config`) to define configuration settings for the Context7 MCP integration, including the service endpoint, API key, timeouts, context caching preferences, and compression thresholds.

## How it Works

The `Context7MCPConnector` establishes a connection to a specified Context7 MCP service endpoint. Once connected, it can send and request various types of context data, facilitating a shared understanding across different AI components. The current implementation uses a mock `_send_message` method to simulate communication with the MCP service. In a real-world scenario, this communication would typically occur over protocols like HTTP, WebSocket, or gRPC, depending on the Context7 MCP's actual implementation.

## Integration with Other Modules

*   **`UnifiedAIMCPIntegration`**: A separate class within this module demonstrates how to integrate Context7 MCP capabilities with existing Unified AI components like `DialogueManager` and `HAMMemoryManager`, showcasing practical application patterns.
*   **`DialogueManager`**: Can leverage this connector for enhanced context awareness during conversational interactions.
*   **`HAMMemoryManager`**: Can utilize this connector for distributed memory management and for compressing memory contexts before storage or transmission.
*   **MCP Data Structures**: Relies on `MCPMessage`, `MCPCapability`, and `MCPResponse` (defined in `src/mcp/types.py`) for structuring all MCP communication.

## Code Location

`src/mcp/context7_connector.py`