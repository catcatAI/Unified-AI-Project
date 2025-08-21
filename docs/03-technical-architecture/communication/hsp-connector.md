# HSPConnector: The AI's Communication Backbone

## Overview

This document provides an overview of the `HSPConnector` module (`src/hsp/connector.py`). This module is the main connector for the Heterogeneous Service Protocol (HSP) and serves as the primary communication layer for the entire AI ecosystem.

## Purpose

The `HSPConnector` is designed to provide a unified and resilient communication layer that abstracts the underlying transport mechanism (MQTT). It enables different AI agents and services to communicate with each other in a structured and reliable way, allowing them to share information, delegate tasks, and advertise their capabilities.

## Key Responsibilities and Features

*   **External and Internal Communication**:
    *   **`ExternalConnector`**: Manages the connection to the external MQTT broker, which is the primary transport for HSP messages.
    *   **`InternalBus`**: An in-memory message bus that facilitates communication between different components within the AI's own process.
    *   **`MessageBridge`**: A key component that bridges messages between the external MQTT broker and the internal bus, allowing for seamless communication between the AI's internal components and the external network.
*   **Structured Messaging**: Defines high-level methods for publishing and subscribing to specific HSP message types, each with a well-defined payload structure (e.g., `HSPFactPayload`, `HSPCapabilityAdvertisementPayload`, `HSPTaskRequestPayload`, `HSPTaskResultPayload`, `HSPAcknowledgementPayload`).
*   **Resilience and Reliability**:
    *   **Retry Policy**: Implements a sophisticated retry mechanism with exponential backoff for publishing messages, ensuring that transient network issues do not lead to message loss.
    *   **Circuit Breaker**: Utilizes a circuit breaker pattern to prevent the system from repeatedly attempting to publish messages to a failing service, thus preventing cascading failures.
    *   **Acknowledgements (ACKs)**: Supports a Quality of Service (QoS) parameter (`requires_ack`) to ensure guaranteed message delivery for critical messages.
    *   **Fallback Protocols**: Can initialize and use a suite of fallback communication protocols (including in-memory, file-based, and HTTP) if the primary HSP (MQTT) connection fails, ensuring that the AI can maintain communication even in adverse network conditions.
*   **Callback-Based Architecture**: Employs a callback-based system that allows different modules to register their interest in specific message types. When a message of a certain type is received, the `HSPConnector` dispatches it to all registered callbacks for that type.
*   **Connection Management**: Handles the process of connecting to and disconnecting from the MQTT broker. The `connect` method includes a built-in retry mechanism, attempting to connect up to 3 times with exponential backoff to enhance connection stability.
*   **Post-Connection Synchronization**: After a successful connection is established, it can re-advertise the AI's capabilities to the network, ensuring that other agents are aware of its services.

## How it Works

The `HSPConnector` initializes an `ExternalConnector` for handling MQTT communication and an `InternalBus` for in-process messaging. The `MessageBridge` acts as the intermediary, routing messages between these two components. When a message is published through the `HSPConnector`, it first passes through the resilience layer (which includes the circuit breaker and retry policy) and is then sent to the `ExternalConnector` for transmission over MQTT. Incoming messages are received by the `ExternalConnector`, passed to the `MessageBridge`, placed on the `InternalBus`, and finally dispatched to any registered callbacks. If the primary MQTT connection fails, the `FallbackManager` can be activated to use alternative communication channels, providing a high degree of fault tolerance.

## Integration with Other Modules

The `HSPConnector` is a central communication hub that integrates with numerous other components:

*   **`core_services`**: Initializes and holds the singleton instance of the `HSPConnector`.
*   **`DialogueManager`, `LearningManager`, `ServiceDiscoveryModule`**: These modules register callbacks with the `HSPConnector` to receive and process various types of HSP messages.
*   **`paho-mqtt`**: The underlying MQTT client library that is used by the `ExternalConnector`.
*   **`RetryPolicy` and `CircuitBreaker`**: These components from `shared.network_resilience` provide the core resilience features.
*   **`FallbackManager`**: Provides the fallback communication mechanisms for enhanced fault tolerance.

## Code Location

`src/hsp/connector.py`