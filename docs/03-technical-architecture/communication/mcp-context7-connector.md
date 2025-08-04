# MCP Context7 Connector: Enhanced AI Collaboration and Context Management

## Overview

The `context7_connector.py` (`src/mcp/context7_connector.py`) module is a pivotal component for integrating the Unified AI Project with **Context7's Model Context Protocol (MCP)**. This integration significantly enhances the AI ecosystem's capabilities by providing advanced context management, seamless model communication, and robust collaborative AI functionalities.

It acts as a bridge, allowing various AI models within the Unified AI Project to leverage Context7's powerful context-aware features for more intelligent and coordinated operations.

## Key Responsibilities and Features

### 1. `Context7MCPConnector`

This class is the primary interface for direct communication with the Context7 MCP service.

-   **Connection Management**: Handles establishing and disconnecting from the Context7 MCP service, including session initialization.
-   **Context Operations**: 
    *   `send_context`: Sends context data (e.g., dialogue, memory, task-related information) to Context7 for storage and processing.
    *   `request_context`: Queries Context7 for relevant contextual information based on a given query.
-   **Model Collaboration (`collaborate_with_model`)**: Facilitates direct collaboration with other AI models registered with Context7, enabling task delegation and shared understanding.
-   **Context Compression (`compress_context`)**: Utilizes Context7's algorithms to compress context data, optimizing storage and transmission, especially for large datasets.
-   **Capability Discovery (`_discover_capabilities`)**: Discovers and registers the capabilities offered by Context7, allowing the Unified AI Project to understand and utilize available services.
-   **Message Handling (`_send_message`)**: Manages the sending of MCP messages to Context7 and handles the responses, including mock responses for development purposes.

### 2. `UnifiedAIMCPIntegration`

This class provides a higher-level integration layer, adapting Context7 MCP capabilities to existing Unified AI Project components.

-   **Dialogue Manager Integration (`integrate_with_dialogue_manager`)**: Enhances the DialogueManager's context awareness by sending current dialogue context to Context7 and retrieving historical context for richer conversations.
-   **HAM Memory Integration (`integrate_with_ham_memory`)**: Integrates with the Hierarchical Abstractive Memory (HAM) system for distributed memory management, including compressing memory data and sending it to Context7 for storage.

### 3. `Context7Config`

A dataclass for configuring the Context7 MCP integration, including:

-   `endpoint`: The URL of the Context7 MCP service.
-   `api_key`: Optional API key for authentication.
-   `timeout`: Request timeout for communications.
-   `max_retries`: Maximum number of retries for failed requests.
-   `enable_context_caching`: Flag to enable/disable local context caching.
-   `context_window_size`: Defines the size of the context window.
-   `compression_threshold`: Threshold for triggering context compression.

## How it Works

The `Context7MCPConnector` establishes a connection to the Context7 MCP service. Once connected, it can send and receive various MCP messages, such as context updates, context queries, and collaboration requests. The `UnifiedAIMCPIntegration` then wraps these functionalities, providing a convenient interface for core AI components like the DialogueManager and HAM Memory to seamlessly interact with Context7, enriching their operations with external context and collaborative intelligence.

## Integration with Other Modules

-   **`mcp/types.py`**: Relies on the MCP message and data structure definitions from `mcp/types.py`.
-   **`DialogueManager`**: Leverages Context7 for enhanced dialogue context.
-   **`HAMMemoryManager`**: Utilizes Context7 for distributed memory management and compression.
-   **Backend API**: The connector would typically interact with a Context7 backend service via HTTP or other protocols.

## Code Location

`src/mcp/context7_connector.py`
