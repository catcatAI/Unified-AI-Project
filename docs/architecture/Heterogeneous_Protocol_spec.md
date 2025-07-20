# Heterogeneous Service Protocol (HSP) - Design Specification v1.0

## 1. Introduction

This document has been **rewritten** to reflect the actual implemented protocol, the **Heterogeneous Service Protocol (HSP)**, which has superseded the conceptual AHAP.

HSP is a lightweight, message-oriented protocol designed for real-time communication, service discovery, task delegation, and knowledge sharing among independent, decentralized AI agents. It operates over a message bus (like MQTT) and provides a standardized structure for interoperability within the Unified-AI-Project's multi-agent ecosystem.

## 2. Core Concepts

### 2.1. Message Envelope (`HSPMessageEnvelope`)

All communication under HSP is wrapped in a standard message envelope. This ensures that every message, regardless of its content, has a consistent structure for routing, security, and metadata.

```json
{
  "hsp_envelope_version": "1.0",
  "message_id": "uuid-string",
  "correlation_id": "optional-uuid-string",
  "sender_ai_id": "did:hsp:agent_A",
  "recipient_ai_id": "did:hsp:agent_B or hsp/tasks/general",
  "timestamp_sent": "2025-07-20T12:00:00Z",
  "message_type": "HSP::TaskRequest_v1.0",
  "protocol_version": "1.0",
  "communication_pattern": "request",
  "payload": {
    "...": "..."
  }
}
```

- **`message_id`**: A unique identifier for this specific message.
- **`correlation_id`**: Used to link messages together, such as a `response` to a `request`.
- **`sender_ai_id` / `recipient_ai_id`**: Decentralized Identifiers (DIDs) or topic URIs for routing.
- **`message_type`**: A namespaced string indicating the type and version of the payload (e.g., `HSP::Fact_v1.0`).
- **`communication_pattern`**: Defines the interaction model (`publish`, `request`, `response`).
- **`payload`**: A JSON object containing the specific data for the message type.

### 2.2. Communication Patterns

- **Publish**: A fire-and-forget pattern used for broadcasting information, such as capability advertisements or general facts.
- **Request/Response**: A two-way pattern used for task delegation. The requester sends a message and expects a direct response, linked by a `correlation_id`.

## 3. Core Payload Types

HSP defines several standard payload types that are carried within the `HSPMessageEnvelope`.

### 3.1. Capability Advertisement (`HSPCapabilityAdvertisementPayload`)

Used by agents to announce their services to the network.

- **Purpose**: Service Discovery.
- **Communication Pattern**: `publish`.
- **Key Fields**:
  - `capability_id`: A unique ID for the service (e.g., `did:hsp:data_agent_1_analyze_csv_data_v1.0`).
  - `name`: Human-readable name (e.g., "CSV Data Analyzer").
  - `description`: What the service does.
  - `parameters`: A schema describing the required input parameters.
  - `returns`: A schema describing the expected output.

### 3.2. Task Request (`HSPTaskRequestPayload`)

Used by a "manager" agent (like Angela) to delegate a task to a "specialist" agent.

- **Purpose**: Task Delegation.
- **Communication Pattern**: `request`.
- **Key Fields**:
  - `request_id`: A unique ID for this specific task request.
  - `capability_id_filter`: The ID of the desired capability.
  - `parameters`: A dictionary containing the actual input data for the task.
  - `callback_address`: The topic/address where the result should be sent.

### 3.3. Task Result (`HSPTaskResultPayload`)

Used by a specialist agent to return the outcome of a task to the original requester.

- **Purpose**: Return results of a delegated task.
- **Communication Pattern**: `response`.
- **Key Fields**:
  - `request_id`: The ID of the original `HSPTaskRequestPayload` this result corresponds to.
  - `status`: `success` or `failure`.
  - `payload`: The actual result data if the task was successful.
  - `error_details`: A dictionary with error information if the task failed.

### 3.4. Fact (`HSPFactPayload`)

Used by agents to share knowledge or learned information across the network.

- **Purpose**: Knowledge Sharing.
- **Communication Pattern**: `publish`.
- **Key Fields**:
  - `id`: A unique ID for the fact.
  - `statement_type`: The format of the fact (e.g., `natural_language`, `semantic_triple`).
  - `statement_nl` / `statement_structured`: The content of the fact.
  - `source_ai_id`: The original discoverer of the fact.
  - `confidence_score`: The originator's confidence in the fact's accuracy (0.0 to 1.0).

## 4. Relation to Implemented Code

The payload structures defined in this document directly correspond to the `TypedDict` definitions found in `src/hsp/types.py`. The logic for sending, receiving, and handling these messages is implemented across several key modules:

- **`src/hsp/connector.py`**: Handles the low-level connection to the message bus (MQTT) and the wrapping/unwrapping of `HSPMessageEnvelope`.
- **`src/core_ai/dialogue/project_coordinator.py`**: Orchestrates the sending of `HSPTaskRequestPayload` and the handling of `HSPTaskResultPayload` for complex projects.
- **`src/agents/base_agent.py`**: Provides the framework for specialist agents to listen for `HSPTaskRequestPayload` and send back `HSPTaskResultPayload`.
- **`src/core_ai/learning/learning_manager.py`**: Listens for and processes incoming `HSPFactPayload` messages, applying trust and quality filters.
- **`src/core_ai/service_discovery/service_discovery_module.py`**: Listens for and registers `HSPCapabilityAdvertisementPayload` messages.
