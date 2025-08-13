# HSP Fallback Protocols

## Overview

This document provides an overview of the `fallback_protocols.py` module, located at `src/hsp/fallback/fallback_protocols.py`. This module implements a robust and flexible fallback communication system for the AI, designed to ensure message delivery even when the primary Heterogeneous Service Protocol (HSP) communication channel (e.g., MQTT) is unavailable.

## Purpose

The primary purpose of the HSP Fallback Protocols system is to enhance the fault tolerance and reliability of the AI's internal and inter-process communication. In a complex AI ecosystem, continuous communication is critical. This module provides alternative communication channels that can be automatically activated if the primary one fails, preventing system-wide disruptions and ensuring that critical messages can still be exchanged.

## Key Responsibilities and Features

*   **`FallbackMessage` Dataclass**: Defines a standardized message format that all fallback protocols must adhere to. This ensures consistency regardless of the underlying transport mechanism. It includes fields for message ID, sender, recipient, type, payload, timestamp, priority, and retry information.
*   **`BaseFallbackProtocol` (Abstract Base Class)**: Serves as the blueprint for all concrete fallback protocol implementations. It defines the essential methods that each protocol must implement, such as `initialize()`, `send_message()`, `start_listening()`, `stop_listening()`, and `health_check()`.
*   **`InMemoryProtocol`**: A concrete implementation that uses Python's `asyncio.Queue` for message passing. This protocol is extremely fast but is limited to communication within the same process.
*   **`FileBasedProtocol`**: A concrete implementation that uses the local file system as a message queue. Messages are written to and read from designated directories. This protocol enables inter-process communication on the same machine.
*   **`HTTPProtocol`**: A concrete implementation that uses HTTP for message exchange. It sets up a simple web server to receive messages and uses an `aiohttp.ClientSession` to send messages. This protocol allows for communication across different machines.
*   **`FallbackProtocolManager`**: The central orchestrator of the entire fallback system.
    *   **Priority System**: Protocols can be added with a defined priority. The manager always attempts to use the highest-priority protocol that is currently active and healthy.
    *   **Health Monitoring**: Periodically performs health checks on all registered protocols. If the active protocol becomes unhealthy, it automatically switches to the next available healthy protocol.
    *   **Message Routing**: Provides a unified `send_message` interface that routes messages through the currently active fallback protocol.
    *   **Retry Mechanism**: Includes a basic retry logic for messages that fail to send, attempting to resend them and potentially switching protocols if necessary.

## How it Works

Upon initialization, the `FallbackProtocolManager` attempts to initialize all registered fallback protocols. It then starts a background health monitoring task. When a message needs to be sent, the manager selects the highest-priority protocol that passes its health check. If the message fails to send via the selected protocol, the manager will attempt to retry and, if configured, switch to a lower-priority protocol. Incoming messages are handled by the respective protocol's listener and then passed to a central queue for processing by other modules.

## Integration with Other Modules

*   **`HSPConnector`**: The `HSPConnector` (the primary HSP communication module) would be the main consumer of the `FallbackProtocolManager`, using it to send messages when its direct MQTT connection is unavailable.
*   **`asyncio`**: The entire module is built around Python's `asyncio` framework, leveraging coroutines, tasks, and queues for asynchronous operations.

## Code Location

`apps/backend/src/hsp/fallback/fallback_protocols.py`
