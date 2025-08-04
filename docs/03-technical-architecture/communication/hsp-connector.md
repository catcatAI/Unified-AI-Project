# HSP Connector: Heterogeneous Service Protocol Communication Hub

## Overview

The `HSPConnector` (`src/hsp/connector.py`) is the central communication hub for the Heterogeneous Service Protocol (HSP) within the Unified-AI-Project. It acts as the primary interface for all inter-AI and external system communication, abstracting away the complexities of underlying messaging protocols (like MQTT) and providing a unified, resilient communication layer.

This module is critical for enabling seamless interaction between various AI components, specialized agents, and external services, ensuring that messages are delivered reliably and efficiently, even in challenging network conditions.

## Key Responsibilities and Features

1.  **External Communication Management**: 
    *   Connects to and manages interactions with an external message broker (e.g., MQTT) via the `ExternalConnector`.
    *   Handles publishing and subscribing to various HSP topics.

2.  **Internal Message Bus Integration**: 
    *   Utilizes an `InternalBus` to route messages within the AI system, decoupling internal components from the external communication layer.
    *   Messages received from the external network are published to the internal bus, and messages intended for external transmission are picked up from the internal bus.

3.  **Message Bridging and Data Alignment**: 
    *   The `MessageBridge` component translates and routes messages between the `ExternalConnector` and the `InternalBus`.
    *   `DataAligner` ensures that message payloads conform to expected schemas, maintaining data integrity across the HSP network.

4.  **Robust Fallback Protocols**: 
    *   A cornerstone feature, the `HSPConnector` can initialize and leverage various fallback protocols (e.g., in-memory, file-based, HTTP) via the `FallbackManager` when the primary HSP connection (MQTT) is unavailable or unreliable.
    *   This ensures continuous communication and operational resilience, critical for maintaining AI functionality in diverse environments.

5.  **HSP Message Type Handling**: 
    *   Provides dedicated methods for publishing and sending different types of HSP messages, each with its specific payload structure and schema:
        *   `publish_fact`: For broadcasting factual information.
        *   `publish_capability_advertisement`: For agents to announce their available functionalities.
        *   `send_task_request`: For one AI to request a task from another.
        *   `send_task_result`: For an AI to send back the result of a task.

6.  **Callback Registration**: 
    *   Allows other modules to register callbacks for specific incoming HSP message types (facts, capability advertisements, task requests, task results).
    *   This promotes a modular and event-driven architecture, where components react to relevant messages.

7.  **Schema Validation**: 
    *   References JSON schemas (e.g., `HSP_Fact_v0.1.schema.json`) for message payloads, ensuring that all communication adheres to a predefined, validated structure.

8.  **Mock Mode for Testing**: 
    *   Supports a `mock_mode` for development and testing, allowing the `HSPConnector` to simulate external communication without requiring a live message broker.

## How it Works

The `HSPConnector` establishes a connection to the configured message broker. It subscribes to relevant topics to receive incoming HSP messages. These messages are then processed by the `MessageBridge`, which validates their structure and publishes them to the `InternalBus`. Internal components can then subscribe to specific message types on the `InternalBus` to receive and process them. Conversely, when an internal component needs to send an HSP message, it calls the appropriate `HSPConnector` method, which constructs the message envelope, potentially serializes the payload, and publishes it to the external broker. If the primary connection fails, the fallback protocols are activated to ensure message delivery through alternative channels.

## Code Location

`src/hsp/connector.py`