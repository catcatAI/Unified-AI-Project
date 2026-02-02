# HSP: 2. Message Envelope and Communication Patterns

## 2.1. HSP Message Envelope

All HSP messages are wrapped in a standard envelope. This ensures consistency
and provides essential metadata for routing, security, and processing.

**Envelope Structure (JSON):**

```json
{
  "hsp_envelope_version": "0.1",
  "message_id": "msg_uuid_example_789",
  "sender_ai_id": "did:hsp:ai_alpha",
  "recipient_ai_id": "hsp/knowledge/facts/general",
  "timestamp_sent": "2024-07-05T14:00:00Z",
  "message_type": "HSP::Fact_v0.1",
  "protocol_version": "0.1",
  "communication_pattern": "publish",
  "correlation_id": null,
  "security_parameters": null,
  "qos_parameters": {
    "priority": "medium",
    "requires_ack": false
  },
  "routing_info": null,
  "payload_schema_uri": null,
  "payload": { ... }
}
```

### 2.1.1. Envelope Fields

- **Required:**
  - `hsp_envelope_version`: Version of the envelope structure itself.
  - `message_id`: Unique identifier for this specific message.
  - `sender_ai_id`: Unique ID of the sending AI.
  - `recipient_ai_id`: Target address. Can be a specific AI's ID or a topic.
  - `timestamp_sent`: ISO 8601 UTC timestamp of when the message was sent.
  - `message_type`: A string identifying the type of the payload (e.g.,
    `HSP::Fact_v0.1`).
  - `protocol_version`: The overall HSP version this message conforms to.
  - `communication_pattern`: The pattern used (e.g., `publish`, `request`).
  - `payload`: The actual data object.
- **Optional:**
  - `correlation_id`: Links a response to a request.
  - `security_parameters`: For signatures or encryption details.
  - `qos_parameters`: Quality of Service settings (e.g., priority,
    acknowledgement requirements).
  - `routing_info`: Additional hints for network routing.
  - `payload_schema_uri`: A link to the schema defining the payload's structure.

## 2.2. Communication Patterns

### 2.2.1. Publish/Subscribe (Pub/Sub)

- **Use:** Disseminating information broadly, such as `Fact`s,
  `CapabilityAdvertisement`s, and `EnvironmentalState`s.
- **Mechanism:** AIs publish messages to topics. Other AIs subscribe to these
  topics to receive the messages.
- **Topic Naming Convention:** A hierarchical structure is recommended, e.g.,
  `hsp/{domain}/{subdomain}/{focus}`.
  - `hsp/knowledge/facts/general`
  - `hsp/capabilities/advertisements/all`

### 2.2.2. Request/Response (Req/Rep)

- **Use:** Direct, targeted interactions, such as `TaskRequest`/`TaskResult` or
  specific queries.
- **Mechanism:** The requester sends a message with a unique `correlation_id`.
  The responder's message includes the same `correlation_id` to link the two.

### 2.2.3. Streaming

- **Use:** For continuous data flows like large file transfers or sensor data.
- **Mechanism:** Typically involves a session-based, sequential message flow.
  (Details to be expanded in future versions).

## 2.3. Message Acknowledgements (ACKs/NACKs)

- If `qos_parameters.requires_ack` is set to `true`, the recipient must send an
  acknowledgement.
- **ACK Message:**
  - `message_type`: `HSP::Acknowledgement_v0.1`
  - `correlation_id`: The ID of the message being acknowledged.
  - `payload`: `{"status": "received", "ack_timestamp": "..."}`
- **NACK (Negative Acknowledgement) Message:**
  - `message_type`: `HSP::NegativeAcknowledgement_v0.1`
  - `correlation_id`: The ID of the message being rejected.
  - `payload`:
    `{"status": "error", "error_code": "...", "error_message": "..."}`
