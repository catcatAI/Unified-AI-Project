# ExternalConnector: Low-Level MQTT Connectivity for HSP

## Overview

This document provides an overview of the `ExternalConnector` module (`src/hsp/external/external_connector.py`). This module is responsible for managing the low-level connection to an external MQTT broker, serving as the primary transport layer for the Heterogeneous Service Protocol (HSP).

## Purpose

The `ExternalConnector` provides the fundamental connectivity to the MQTT network, enabling the AI to send and receive messages from other AI agents and services. It abstracts away the complexities of MQTT client management, including establishing and terminating connections, publishing messages to topics, subscribing to topics, and handling incoming message reception.

## Key Responsibilities and Features

*   **MQTT Client Management**: Utilizes the `gmqtt` library to create and manage an MQTT client instance. This client handles the underlying network communication with the MQTT broker.
*   **Connection Handling**: Provides `connect` and `disconnect` methods to establish and terminate connections with the MQTT broker. It includes built-in callbacks (`on_connect` and `on_disconnect`) that are triggered upon successful connection or disconnection, allowing for higher-level logic to react to connection status changes.
*   **Publish/Subscribe Functionality**: Offers `publish` and `subscribe` methods for sending messages to specific MQTT topics and receiving messages from subscribed topics. This forms the core of the message-oriented middleware pattern.
*   **Message Reception**: When a message is received from a subscribed topic, the `ExternalConnector` invokes a registered `on_message_callback`. This callback mechanism allows higher-level modules (like the `MessageBridge`) to process the incoming data.
*   **TLS/SSL Support**: Can be configured to use TLS/SSL for secure communication with the MQTT broker. It supports loading CA certificates, client certificates, and key files, ensuring encrypted and authenticated connections.
*   **Authentication**: Supports username and password authentication for connecting to the MQTT broker, adding another layer of security.

## How it Works

The `ExternalConnector` initializes a `gmqtt.Client` instance with a unique client ID. It then sets up event handlers for connection, disconnection, and message reception. When the `connect` method is called, it attempts to establish a connection to the specified MQTT broker. Once connected, the `ExternalConnector` can publish messages to designated topics and subscribe to topics of interest. Any messages received on subscribed topics are then passed to the `on_message_callback` for further processing by other components of the AI system.

## Integration with Other Modules

*   **`HSPConnector`**: This is the primary consumer of the `ExternalConnector`. The `HSPConnector` uses the `ExternalConnector` to send and receive all messages over the MQTT network, forming the backbone of the HSP communication.
*   **`gmqtt`**: The core external library used for all MQTT communication operations.

## Code Location

`src/hsp/external/external_connector.py`