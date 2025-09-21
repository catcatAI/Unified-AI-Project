# MCP Types: Management Control Protocol Message Definitions

## Overview

This document provides a comprehensive overview of the data structures and message formats defined in the `src/mcp/types.py` module. These TypedDicts and dataclasses form the backbone of the Management Control Protocol (MCP), supporting both legacy and enhanced (Context7) versions of the protocol.

This module is crucial for enabling standardized, type-safe, and extensible communication related to management, control, and contextual information exchange between AI entities within the Unified-AI-Project. It ensures interoperability and consistent interpretation of commands and data across different components.

## Key Responsibilities and Features

### Original MCP Types (Legacy)

*   **`MCPEnvelope`**: The top-level structure for legacy MCP messages. It includes essential metadata such as `mcp_envelope_version`, `message_id`, `sender_id`, `recipient_id`, `timestamp_sent`, `message_type`, `protocol_version`, and a generic `payload` field.
*   **`MCPCommandRequest`**: Defines the payload structure for requesting a command execution. It specifies the `command_name` to be executed and a dictionary of `parameters` for that command.
*   **`MCPCommandResponse`**: Defines the payload structure for responding to a command request. It includes the `request_id` of the original command, its `status` (e.g., "success", "failure", "in_progress"), an optional `payload` for the result data, and an `error_message` if the command failed.

### Context7 MCP Types (Enhanced)

These types are designed for integration with Context7's advanced context management capabilities:

*   **`MCPMessage`**: An enhanced message format for Context7 integration. It includes `type` (e.g., "context_update", "context_query", "capability_discovery"), an optional `session_id`, a `payload` dictionary, and optional `timestamp` and `priority` fields.
*   **`MCPResponse`**: An enhanced response format for Context7. It indicates `success` status, the `message_id` of the request it's responding to, a `data` dictionary for the response payload, and an optional `error` message.
*   **`MCPCapability`**: Defines the structure for capabilities advertised by MCP services. It includes `name`, `version`, an optional `description`, and `parameters`.
*   **`MCPContextItem`**: Represents a single item of contextual information exchanged via MCP. It includes `id`, `content`, `context_type`, and optional `relevance_score` and `metadata`.
*   **`MCPCollaborationRequest`**: Defines a request for collaboration between AI models. It specifies the `source_model` and `target_model`, a `task_description`, `shared_context`, `collaboration_mode` (sync/async), and an optional `timeout`.

## How it Works

These TypedDicts serve as the formal contract for all MCP messages. When an AI entity sends a message, it constructs an appropriate TypedDict structure and populates it with data. Receiving AIs can then parse and validate these messages against the defined types, ensuring consistent interpretation of management commands and contextual information. The module supports both simple command-response patterns (legacy) and more complex context-aware interactions (Context7 enhanced), allowing for flexible communication strategies within the AI ecosystem.

## Integration with Other Modules

*   **`MCPConnector`**: The primary module that handles the serialization, deserialization, and validation of messages based on these types for communication over MQTT.
*   **`Context7MCPConnector`**: Specifically uses the enhanced Context7 MCP types for its interactions with the Context7 service.
*   **`MCPFallbackProtocolManager`**: Utilizes the `MCPMessage` type for its internal fallback communication mechanisms.
*   **AI Management Tools**: External tools or internal AI components that issue control commands or exchange contextual information construct and consume messages that adhere to these defined types.

## Code Location

`src/mcp/types.py`