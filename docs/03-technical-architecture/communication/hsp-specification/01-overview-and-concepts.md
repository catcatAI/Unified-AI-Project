# Heterogeneous Service Protocol (HSP) Specification - Part 1: Overview and Core Concepts

## 1. Introduction

The Heterogeneous Service Protocol (HSP) is a lightweight, message-based communication protocol designed to facilitate real-time, asynchronous interaction between diverse AI agents and services within the Unified AI Project ecosystem. Built upon MQTT, HSP provides a flexible and scalable mechanism for agents to discover each other, advertise capabilities, request tasks, and exchange information.

This document, Part 1 of the HSP Specification, provides a high-level overview of the protocol's philosophy, core principles, and fundamental concepts. Subsequent parts will delve into message structures, communication patterns, and advanced features.

## 2. Philosophy and Design Principles

HSP is guided by the following core principles:

-   **Heterogeneity**: Accommodate a wide range of agent types, programming languages, and underlying technologies. Agents should be able to communicate without needing to know the internal implementation details of their peers.
-   **Asynchronicity**: Support non-blocking communication, allowing agents to perform other tasks while waiting for responses. This is crucial for maintaining responsiveness in a distributed AI system.
-   **Decoupling**: Minimize direct dependencies between agents. Communication should primarily occur through a central message broker, promoting modularity and reducing the impact of changes to individual agents.
-   **Scalability**: Enable the system to grow by easily adding new agents and services without significant architectural changes. MQTT's publish/subscribe model inherently supports this.
-   **Resilience**: Design for fault tolerance, allowing the system to continue operating even if individual agents or network components fail. This includes mechanisms for message retransmission and fallback protocols (detailed in Part 2).
-   **Discoverability**: Provide mechanisms for agents to dynamically discover the capabilities of other agents within the network.
-   **Simplicity**: Keep the core protocol simple and easy to understand, while allowing for complexity to be built on top through message payloads.

## 3. Core Concepts

### 3.1. Agents

In the context of HSP, an **Agent** is any independent computational entity that can send or receive HSP messages. Agents can be:

-   **Meta-Agent (Angela)**: The central orchestrator and primary interface for user interaction. Angela delegates complex tasks to sub-agents.
-   **Sub-Agents**: Specialized agents designed to perform specific tasks (e.g., Data Analysis Agent, Creative Writing Agent). They advertise their capabilities and respond to task requests from the Meta-Agent or other Sub-Agents.
-   **External Agents**: AI tools or services external to the Unified AI Project (e.g., Rovo Dev Agent, third-party LLMs) that integrate via an HSP bridge.

### 3.2. Message Broker (MQTT)

HSP leverages **MQTT (Message Queuing Telemetry Transport)** as its underlying transport layer. MQTT is a lightweight publish/subscribe messaging protocol ideal for IoT and distributed systems.

-   **Topics**: Agents communicate by publishing messages to and subscribing to specific MQTT topics. Topics are hierarchical strings (e.g., `hsp/agent/data_analysis/requests`, `hsp/agent/creative_writing/responses`).
-   **Quality of Service (QoS)**: HSP messages typically utilize QoS 1 (At Least Once) or QoS 2 (Exactly Once) to ensure reliable message delivery, depending on the criticality of the message.
-   **Retained Messages**: Agents can publish retained messages to topics to advertise their presence or capabilities, allowing new agents to immediately discover existing services upon connection.

### 3.3. Message Envelope (`HSPMessageEnvelope`)

All HSP communications are encapsulated within a standardized **`HSPMessageEnvelope`**. This envelope provides metadata about the message, ensuring consistent routing, processing, and error handling across heterogeneous agents.

Key fields in the `HSPMessageEnvelope` include:

-   `message_id`: Unique identifier for the message.
-   `sender_id`: Identifier of the sending agent.
-   `recipient_id`: Identifier of the intended recipient agent (optional, for direct messages).
-   `timestamp`: Time of message creation.
-   `message_type`: Categorization of the message (e.g., `CAPABILITY_ADVERTISEMENT`, `TASK_REQUEST`, `TASK_RESULT`, `FACT`, `ERROR`).
-   `payload_type`: Specifies the type of data contained within the `payload` field (e.g., `HSPCapabilityPayload`, `HSPTaskRequestPayload`).
-   `payload_schema_uri`: URI pointing to the JSON schema defining the structure of the `payload`. This enables dynamic validation.
-   `payload`: The actual data content of the message, structured according to `payload_type` and `payload_schema_uri`.

### 3.4. Communication Patterns

HSP supports several fundamental communication patterns:

-   **Publish/Subscribe**: Agents publish messages to topics, and any agent subscribed to that topic receives the message. This is the primary mechanism for broadcasting information (e.g., capability advertisements, facts).
-   **Request/Response**: An agent sends a task request to another agent and expects a specific result. This is typically implemented by the requesting agent subscribing to a response topic specific to the task or the recipient.
-   **Fact Broadcasting**: Agents can publish facts (pieces of information or knowledge) to a general fact topic, which can be consumed and integrated by other agents (e.g., `LearningManager`, `HAMMemoryManager`).

## 4. Security Considerations

HSP, being built on MQTT, inherits its security features. Implementations should consider:

-   **Authentication**: Using MQTT username/password or client certificates.
-   **Authorization**: Implementing Access Control Lists (ACLs) on the MQTT broker to restrict topic access.
-   **Encryption**: Utilizing TLS/SSL for secure communication channels.
-   **Payload Integrity**: Employing digital signatures for critical payloads to ensure data integrity and authenticity.

## 5. Future Enhancements (Out of Scope for Part 1)

-   Detailed message payload schemas.
-   Advanced error handling and retry mechanisms.
-   Integration with external identity and access management systems.
-   Performance optimization strategies.

---

**Note**: Consider adding more diagrams and concrete examples to further simplify complex concepts for a broader audience.