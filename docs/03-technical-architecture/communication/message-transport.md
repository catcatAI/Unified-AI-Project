# Message Transport Mechanisms

This document provides an overview of the different message transport mechanisms
used in the Unified AI Project.

## HTTP

The project uses HTTP for communication between the frontend and the backend, as
well as for communication between different services. The following libraries
are used to create HTTP servers:

- **Flask:** A lightweight web framework for Python.
- **FastAPI:** A modern, fast (high-performance) web framework for Python.

The main API server is located in `src/services/main_api_server.py`.

## MQTT

The project uses the Message Queuing Telemetry Transport (MQTT) protocol for the
Heterogeneous Synchronization Protocol (HSP), which allows different AI
instances to communicate with each other. The `paho-mqtt` library is used to
communicate with an MQTT broker.

The HSP implementation is located in the `src/hsp/` directory.



## Standard Input/Output

The command-line interface (CLI) in `src/interfaces/cli/main.py` uses standard
input and output to communicate with the user.

## Fallback Protocol System

### Overview
To address the error handling and reliability issues mentioned above, we have implemented a comprehensive fallback protocol system.

### Protocol Architecture
```
┌─────────────┐    失敗    ┌─────────────┐
│ MQTT (HSP)  │ ────────→  │ HTTP協議    │
└─────────────┘            └─────────────┘
                                 │ 失敗
                                 ▼
                           ┌─────────────┐
                           │ 文件協議    │
                           └─────────────┘
                                 │ 失敗
                                 ▼
                           ┌─────────────┐
                           │ 內存協議    │
                           └─────────────┘
```

### Error Handling Improvements
- ✅ Automatic failure detection and protocol switching
- ✅ Connection retry with exponential backoff
- ✅ Message retransmission and deduplication
- ✅ Comprehensive error logging and monitoring

## Follow-up Development and Implementation Plan

### Error Handling (IMPLEMENTED)

The HSP protocol now has robust error handling through the fallback system:

**Implemented Features:**

- ✅ Automatic detection when an AI instance goes offline
- ✅ Automatic re-establishment of connections with fallback protocols
- ✅ Comprehensive error handling during message processing
- ✅ Health monitoring and status reporting

### Security

The communication between the AI instances is not currently encrypted. This
could be a security risk, as it would be possible for an attacker to intercept
the messages and learn sensitive information about the AI.

**Recommendations:**

- Encrypt all communication between the AI instances using a technology such as
  TLS.
- Implement a mechanism for authenticating AI instances to ensure that only
  authorized instances can connect to the network.

### Security (ENHANCED)

Communication security has been improved with the fallback system:

**Implemented Features:**
- ✅ Message integrity verification
- ✅ Secure protocol selection
- 🔄 Planned: TLS encryption for all protocols
- 🔄 Planned: Authentication mechanisms

### Scalability (IMPROVED)

The fallback protocol system improves scalability:

**Implemented Features:**
- ✅ Multi-protocol load distribution
- ✅ Dynamic protocol selection based on load
- ✅ Configuration-driven protocol management
- ✅ Horizontal scaling support through HTTP protocol

**Future Recommendations:**
- Use more scalable message brokers (RabbitMQ, Kafka) as additional protocols
- Implement advanced load balancing across protocol instances
