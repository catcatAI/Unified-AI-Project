# MCP Types: Multi-Agent Communication Protocol Data Structures

## Overview

The `types.py` (`src/mcp/types.py`) module defines the **data structures and message formats** used within the Multi-Agent Communication Protocol (MCP) of the Unified-AI-Project. It provides the foundational types for inter-agent communication, supporting both legacy MCP implementations and enhanced Context7 integrations.

This module is critical for ensuring structured and consistent data exchange between different AI models and components within the ecosystem, facilitating collaboration and coordinated task execution.

## Key Type Definitions

### 1. Original MCP Types (Legacy)

These types represent the initial or legacy message formats used in the MCP.

-   **`MCPEnvelope` (TypedDict)**:
    *   The basic message envelope for legacy MCP communications.
    *   Includes fields such as `mcp_envelope_version`, `message_id`, `sender_id`, `recipient_id`, `timestamp_sent`, `message_type`, `protocol_version`, `payload` (generic dictionary), and `correlation_id`.

-   **`MCPCommandRequest` (TypedDict)**:
    *   Defines the structure for requesting a command execution from another agent.
    *   Contains `command_name` and `parameters` (a dictionary of arguments).

-   **`MCPCommandResponse` (TypedDict)**:
    *   Defines the structure for responding to a command request.
    *   Includes `request_id` (linking to the original request), `status` (e.g., "success", "failure", "in_progress"), `payload` (the result), and `error_message`.

### 2. Context7 MCP Types (Enhanced)

These types represent enhanced message formats designed for deeper integration with Context7, providing more granular control and richer context.

-   **`MCPMessage` (TypedDict)**:
    *   An enhanced MCP message format for Context7 integration.
    *   Fields include: `type`, `session_id` (optional), `payload` (generic dictionary), `timestamp` (optional), and `priority` (optional).

-   **`MCPResponse` (TypedDict)**:
    *   An enhanced MCP response format.
    *   Includes: `success` (boolean), `message_id`, `data` (result data), `error` (optional error message), and `timestamp` (optional).

-   **`MCPCapability` (TypedDict)**:
    *   Defines the structure for an MCP capability, similar to HSP capabilities but specific to MCP.
    *   Fields: `name`, `version`, `description` (optional), and `parameters` (optional dictionary).

-   **`MCPContextItem` (TypedDict)**:
    *   Represents an item of context shared within MCP communication.
    *   Fields: `id`, `content`, `context_type`, `relevance_score` (optional), and `metadata` (optional dictionary).

-   **`MCPCollaborationRequest` (TypedDict)**:
    *   Defines a request for collaboration between AI models.
    *   Fields: `source_model`, `target_model`, `task_description`, `shared_context` (dictionary), `collaboration_mode` (e.g., "sync", "async"), and `timeout` (optional).

## Importance and Usage

`mcp/types.py` is crucial for:

-   **Standardized Communication**: Provides a common language and structure for all MCP messages, ensuring that different AI components can understand and process each other's communications.
-   **Inter-Agent Collaboration**: Facilitates complex interactions and task delegation between AI models by defining clear request and response formats.
-   **Extensibility**: The use of `TypedDict` allows for easy extension and modification of message types as the protocol evolves.
-   **Type Safety**: Enhances code reliability and reduces errors by providing explicit type hints for all message fields.

## Code Location

`src/mcp/types.py`
