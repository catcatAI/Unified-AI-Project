# MessageBridge: Seamless Communication Between Internal and External HSP

## Overview

This document provides an overview of the `MessageBridge` module (`src/hsp/bridge/message_bridge.py`). This module acts as a crucial intermediary, bridging messages between the external Heterogeneous Service Protocol (HSP) network (via MQTT) and the AI's internal message bus.

## Purpose

The primary purpose of the `MessageBridge` is to ensure seamless, validated, and structured communication between the AI's internal components and the external HSP network. It handles the complexities of message parsing, validation against schemas, and intelligent routing, allowing internal modules to communicate with external AIs without needing to understand the underlying network protocols.

## Key Responsibilities and Features

*   **External to Internal Routing (`handle_external_message`)**:
    *   Receives raw messages (topic and payload as a string) from the `ExternalConnector` (which interfaces with MQTT).
    *   Parses the incoming JSON message into a Python dictionary.
    *   Utilizes a `DataAligner` to validate and align the message against predefined HSP schemas, ensuring data integrity and conformity.
    *   If the message is valid, it routes the message to the appropriate internal channel on the `InternalBus` based on the message's `message_type` (e.g., a "HSP::Fact_v0.1" message is routed to the "hsp.external.fact" channel).
*   **Internal to External Routing (`handle_internal_message`)**:
    *   Receives messages from the `InternalBus` (specifically from the "hsp.internal.message" channel, which is where internal components publish messages intended for the external network).
    *   Publishes these messages to the `ExternalConnector` (MQTT) for transmission to the external HSP network.
*   **Message Type Mapping**: Maintains a clear mapping (`_message_type_to_internal_topic_map`) between official HSP message types (as defined in the HSP specification, e.g., "HSP::Fact_v0.1") and their corresponding internal topic suffixes (e.g., "fact"). This ensures consistent and predictable routing.

## How it Works

The `MessageBridge` is initialized with instances of the `ExternalConnector`, `InternalBus`, and `DataAligner`. It sets its `handle_external_message` method as the callback for incoming messages from the `ExternalConnector`, establishing the flow from external to internal. Concurrently, it subscribes to a specific internal channel (`hsp.internal.message`) on the `InternalBus` to handle messages originating from internal components that are destined for the external network. This dual-direction handling ensures that messages flow correctly and are properly processed between the AI's internal logic and the external communication layers.

## Integration with Other Modules

*   **`ExternalConnector`**: Provides the low-level interface to the external MQTT network.
*   **`InternalBus`**: Provides the in-memory message bus for internal communication within the AI's process.
*   **`DataAligner`**: Essential for message validation and schema alignment, ensuring that all messages conform to the HSP specification.
*   **`HSPConnector`**: The `HSPConnector` uses this `MessageBridge` as a core component of its overall communication architecture, orchestrating the flow of messages.

## Code Location

`src/hsp/bridge/message_bridge.py`