# Heterogeneous Synchronization Protocol (HSP) Specification - Version 0.1

## 1. Introduction

### 1.1. Purpose
The Heterogeneous Synchronization Protocol (HSP) is designed to enable communication, data sharing, and collaborative task execution among diverse and independently developed AI entities (HSP Participant AIs). It aims to foster a robust, scalable, and intelligent ecosystem of interconnected AIs.

### 1.2. Goals
*   **Interoperability:** Allow AIs with different internal architectures and capabilities to exchange information and services meaningfully.
*   **Robustness:** Enhance overall system resilience through distributed knowledge, potential for consensus, and fault isolation.
*   **Scalability:** Support a growing network of AIs and increasing information flow.
*   **Collaboration:** Enable AIs to work together on complex tasks that may be beyond the capability of a single AI.
*   **Extensibility:** Design the protocol to be adaptable to future advancements in AI and communication technologies.

### 1.3. Scope (Version 0.1)
This version (0.1) focuses on establishing the foundational elements of the HSP, including:
*   Core information types for knowledge sharing and tasking.
*   Basic communication patterns (Publish/Subscribe, Request/Response).
*   A standardized message envelope.
*   Initial concepts for AI discovery, capability advertisement, and trust.
Advanced features like complex consensus mechanisms, comprehensive semantic translation services, and detailed state synchronization are planned for future versions.

### 1.4. Guiding Principles
*   **Decentralization:** Favor decentralized mechanisms where feasible to enhance resilience and avoid single points of failure.
*   **Clarity & Simplicity:** Strive for clear and understandable specifications, especially in early versions.
*   **Security & Trust:** Build in considerations for security and trust from the ground up.
*   **Flexibility:** Allow for various underlying network topologies and transport protocols.
*   **Evolvability:** Design with future extensions and versioning in mind.

## 2. Core Concepts

### 2.1. HSP Participant AI (HPA)
An HSP Participant AI (HPA), or simply "AI," is any software entity capable of sending and receiving messages according to this HSP specification. Each HPA is expected to have a unique identifier (see Sender/Recipient AI ID in Message Envelope).

### 2.2. Overview of Key Information Types
HSP defines several core types of information that can be exchanged (detailed in Section 3):
*   `Fact`/`Assertion`: Statements about the world or entities.
*   `Belief`: Subjective or uncertain statements.
*   `CapabilityAdvertisement`: Descriptions of services an AI can offer.
*   `TaskRequest`: Requests for an AI to perform a task.
*   `TaskResult`: Outcomes of task requests.
*   `EnvironmentalState`/`ContextUpdate`: Information about shared contexts.
*   `AIStateSynchronization` (Conceptual for v0.1): For sharing internal AI states.

### 2.3. High-Level Architectural Overview
HSP is designed to be flexible regarding network architecture. It can support:
*   **Peer-to-Peer (P2P) interactions:** Direct communication between AIs.
*   **Broker-mediated communication:** For patterns like Publish/Subscribe, potentially using message brokers (e.g., MQTT, Kafka).
*   **Federated systems:** Groups of AIs forming local networks connected via gateways.
The specific network topology is an implementation choice, but HSP messages are designed to be routable across different configurations.

## 3. Information Types & Data Payloads

This section details the structure of the primary data objects exchanged via HSP.
*Default data format for payloads in v0.1 is JSON. JSON Schema should be used for validation where possible.*

### 3.1. `Fact` / `Assertion`
*   **Purpose:** Represents a statement about the world, an entity, or a relationship, believed to be true by the originating AI to some degree.
*   **Fields:**
    *   `id` (string, UUID): Unique identifier for this fact instance.
    *   `statement_type` (string, enum: "natural_language", "semantic_triple", "json_ld"): Specifies the representation of the core assertion.
    *   `statement_nl` (string, optional): The assertion in natural language (if `statement_type` is "natural_language").
    *   `statement_structured` (object, optional): Structured representation (e.g., subject, predicate, object URIs if "semantic_triple"; JSON-LD object if "json_ld").
    *   `source_ai_id` (string, DID/URI): ID of the AI originating or asserting this fact.
    *   `original_source_info` (object, optional): Information about the ultimate source if learned externally.
        *   `type` (string, e.g., "url", "document_id", "user_id", "sensor_id").
        *   `identifier` (string).
    *   `timestamp_created` (string, ISO 8601 UTC): When this fact was asserted/created by `source_ai_id`.
    *   `timestamp_observed` (string, ISO 8601 UTC, optional): If the fact describes an event, when that event was observed or occurred.
    *   `confidence_score` (float, 0.0-1.0): The AI's confidence in the truth of this fact.
    *   `weight` (float, default: 1.0): General-purpose weight (relevance, importance, priority).
    *   `valid_from` (string, ISO 8601 UTC, optional): Timestamp from which the fact is considered valid.
    *   `valid_until` (string, ISO 8601 UTC, optional): Timestamp until which the fact is considered valid (for temporal facts).
    *   `context` (object, optional): Key-value pairs describing the context in which this fact is true (e.g., `{"location": "New York", "condition": "sunny"}`).
    *   `tags` (array of strings, optional): Keywords or categories.
    *   `access_policy_id` (string, optional): Identifier for a policy governing sharing/use.
*   **Example (JSON, with `statement_type: "semantic_triple"`):**
    ```json
    {
      "id": "fact_uuid_12345",
      "statement_type": "semantic_triple",
      "statement_structured": {
        "subject_uri": "hsp:entity:Sky",
        "predicate_uri": "hsp:property:hasColor",
        "object_literal": "blue",
        "object_datatype": "xsd:string"
      },
      "source_ai_id": "did:hsp:ai_alpha",
      "timestamp_created": "2024-07-05T10:00:00Z",
      "confidence_score": 0.95,
      "weight": 1.0
    }
    ```

### 3.2. `Belief`
*   **Purpose:** Similar to `Fact`, but for statements with higher subjectivity, uncertainty, or representing hypotheses.
*   **Fields:** Inherits most fields from `Fact`. Additional/modified fields:
    *   `belief_holder_ai_id` (string, DID/URI): The AI holding this belief (defaults to `source_ai_id`).
    *   `justification_type` (string, enum: "text", "inference_chain_id", "evidence_ids_list", optional).
    *   `justification` (string or array, optional): Reasoning, link to an inference chain, or list of supporting fact/belief IDs.
    *   `confidence_score` (float, 0.0-1.0): Represents subjective belief strength or probability.
*   **Example (JSON):**
    ```json
    {
      "id": "belief_uuid_67890",
      "statement_type": "natural_language",
      "statement_nl": "It might rain tomorrow.",
      "belief_holder_ai_id": "did:hsp:ai_beta",
      "source_ai_id": "did:hsp:ai_beta",
      "timestamp_created": "2024-07-05T11:00:00Z",
      "confidence_score": 0.60,
      "justification_type": "text",
      "justification": "Weather model X showed a 60% chance."
    }
    ```

### 3.3. `CapabilityAdvertisement`
*   **Purpose:** An AI advertises a skill, service, or tool it can offer.
*   **Fields:**
    *   `capability_id` (string, unique): Unique ID for this capability offering (e.g., `ai_gamma_translate_v1.2`).
    *   `ai_id` (string, DID/URI): ID of the AI offering the capability.
    *   `name` (string): Human-readable name (e.g., "Text Translation Service").
    *   `description` (string): Detailed description.
    *   `version` (string, e.g., "1.2.0").
    *   `input_schema_uri` (string, optional): URI to a schema (e.g., JSON Schema) defining the input parameters object.
    *   `input_schema_example` (object, optional): An example of the input parameters object.
    *   `output_schema_uri` (string, optional): URI to a schema for the output data.
    *   `output_schema_example` (object, optional): An example of the output data object.
    *   `data_format_preferences` (array of strings, optional): Preferred or supported data formats for input/output (e.g., `["application/json", "image/jpeg"]`).
    *   `hsp_protocol_requirements` (object, optional): Specific HSP features required by this capability (e.g., `{"requires_streaming_input": true}`).
    *   `cost_estimate_template` (object, optional): Template describing potential costs (e.g., `{"metric": "compute_units", "value_per_call": 10}`).
    *   `availability_status` (string, enum: "online", "offline", "degraded", "maintenance").
    *   `access_policy_id` (string, optional): Who can use this capability.
    *   `tags` (array of strings, optional): Keywords for discovery.
*   **Example (JSON):**
    ```json
    {
      "capability_id": "ai_gamma_translate_v1.2",
      "ai_id": "did:hsp:ai_gamma",
      "name": "Text Translation Service",
      "description": "Translates text between English and French.",
      "version": "1.2.0",
      "input_schema_uri": "hsp:schemas:translation_input_v1",
      "output_schema_uri": "hsp:schemas:translation_output_v1",
      "availability_status": "online",
      "tags": ["nlp", "translation", "text"]
    }
    ```

### 3.4. `TaskRequest`
*   **Purpose:** An AI requests another AI to perform a task using an advertised capability.
*   **Fields:**
    *   `request_id` (string, UUID): Unique ID for this task request.
    *   `requester_ai_id` (string, DID/URI): ID of the AI making the request.
    *   `target_ai_id` (string, DID/URI, optional): Specific AI to perform the task. If null/absent, any capable AI can pick it up (requires discovery/brokering).
    *   `capability_id_filter` (string, optional): The ID of the capability being requested (e.g., "ai_gamma_translate_v1.2").
    *   `capability_name_filter` (string, optional): Alternative to `capability_id_filter`, can be used for discovery if specific ID unknown.
    *   `parameters` (object): Input parameters conforming to the capability's input schema.
    *   `requested_output_data_format` (string, optional): Requester can specify a preferred output format if the capability supports multiple (from its `data_format_preferences`).
    *   `priority` (integer, e.g., 1-10, optional): Task priority.
    *   `deadline_timestamp` (string, ISO 8601 UTC, optional): When the task should be completed by.
    *   `callback_address` (string, URI/topic, optional): Where to send the `TaskResult`.
*   **Example (JSON):**
    ```json
    {
      "request_id": "taskreq_uuid_abcde",
      "requester_ai_id": "did:hsp:ai_delta",
      "target_ai_id": "did:hsp:ai_gamma",
      "capability_id_filter": "ai_gamma_translate_v1.2",
      "parameters": {
        "text_to_translate": "Hello world",
        "source_language": "en",
        "target_language": "fr"
      },
      "priority": 5
    }
    ```

### 3.5. `TaskResult`
*   **Purpose:** The outcome of a `TaskRequest`.
*   **Fields:**
    *   `result_id` (string, UUID): Unique ID for this result.
    *   `request_id` (string, UUID): ID of the `TaskRequest` this is a result for.
    *   `executing_ai_id` (string, DID/URI): ID of the AI that performed the task.
    *   `status` (string, enum: "success", "failure", "in_progress", "queued", "rejected").
    *   `payload` (object, optional): The actual result data (if status is "success"), conforming to the capability's output schema.
    *   `output_data_format` (string, optional): Confirms the format of the `payload` (e.g., "application/json", "image/png", "text/plain").
    *   `error_details` (object, optional): If status is "failure" or "rejected".
        *   `error_code` (string).
        *   `error_message` (string).
        *   `error_context` (object, optional).
    *   `timestamp_completed` (string, ISO 8601 UTC, optional): When the task was completed or final status determined.
    *   `execution_metadata` (object, optional): Metrics (e.g., `{"time_taken_ms": 150}`).
*   **Example (JSON):**
    ```json
    {
      "result_id": "taskres_uuid_fghij",
      "request_id": "taskreq_uuid_abcde",
      "executing_ai_id": "did:hsp:ai_gamma",
      "status": "success",
      "payload": {
        "translated_text": "Bonjour le monde",
        "detected_source_language": "en"
      },
      "timestamp_completed": "2024-07-05T12:05:00Z"
    }
    ```

### 3.6. `EnvironmentalState` / `ContextUpdate`
*   **Purpose:** Information about the shared environment or a relevant contextual shift.
*   **Fields:**
    *   `update_id` (string, UUID): Unique ID for this update.
    *   `source_ai_id` (string, DID/URI): AI reporting the update.
    *   `phenomenon_type` (string, URI/namespaced string): Type of phenomenon observed (e.g., `hsp:event:UserMoodShift`, `hsp:state:SystemLoad`).
    *   `parameters` (object): Specifics of the state/context (e.g., `{"user_id": "user_X", "new_mood": "anxious", "confidence": 0.7}`).
    *   `timestamp_observed` (string, ISO 8601 UTC): When this state was observed/became true.
    *   `scope_type` (string, enum: "global", "session", "project", "custom_group", optional).
    *   `scope_id` (string, optional): Identifier for the scope (e.g., session ID, project ID).
    *   `relevance_decay_rate` (float, optional): How quickly this information loses relevance.
*   **Example (JSON):**
    ```json
    {
      "update_id": "ctxupd_uuid_klmno",
      "source_ai_id": "did:hsp:ai_epsilon",
      "phenomenon_type": "hsp:event:UserMoodShift",
      "parameters": {
        "user_id": "user_alice",
        "session_id": "session_123",
        "previous_mood": "neutral",
        "current_mood": "happy",
        "confidence": 0.85
      },
      "timestamp_observed": "2024-07-05T13:00:00Z",
      "scope_type": "session",
      "scope_id": "session_123"
    }
    ```

### 3.7. `AIStateSynchronization` (Conceptual for v0.1, details for future versions)
*   **Purpose:** An AI shares parts of its internal model or state. Highly sensitive and complex.
*   **Potential Fields (High-Level):** `sync_id`, `source_ai_id`, `target_ai_id`, `model_component_name`, `state_data_format`, `state_data_chunk`, `sequence_number`, `is_last_chunk`, `version`, `sync_type`.

### 3.8. Semantic Representation and Deep Mapping
*   **Semantic Representation:** For `Fact` and `Belief` payloads, `statement_type` allows for "natural_language", "semantic_triple" (using URIs for subject, predicate, object), or "json_ld". This provides flexibility. HPAs should strive to use structured representations where possible.
*   **Deep Mapping:**
    *   HPAs may publish links to their primary ontologies/schemas (e.g., as part of their `AIRegistration` or a dedicated `OntologyAdvertisement` message type - TBD).
    *   The HSP network may eventually support a "Mapping Broker" service where AIs can register and query for semantic mappings between different ontologies or terms. For v0.1, mapping is largely the responsibility of the communicating AIs.

### 3.9. Payload Data Format
*   Default for v0.1: JSON.
*   It is highly recommended that publishers of data also publish or link to a JSON Schema defining the structure of their payloads (e.g., in `CapabilityAdvertisement` or a schema registry).

## 4. Communication Patterns & Message Envelope

### 4.1. Communication Patterns
*   **Publish/Subscribe (Pub/Sub):**
    *   **Use:** Disseminating information broadly (e.g., `Fact`s, `CapabilityAdvertisement`s, `EnvironmentalState`s).
    *   **Mechanism:** AIs publish messages to topics. Subscribers receive messages on subscribed topics.
*   **Request/Response (Req/Rep):**
    *   **Use:** Direct interaction for tasks, queries (e.g., `TaskRequest`/`TaskResult`, specific `Fact` queries).
    *   **Mechanism:** Requester sends message with `correlation_id`; Responder includes same `correlation_id` in response.
*   **Streaming:**
    *   **Use:** Continuous data (e.g., large `AIStateSynchronization` chunks, sensor feeds).
    *   **Mechanism:** Session-based, sequential message flow.

### 4.2. HSP Message Envelope
All HSP messages are wrapped in the following envelope:
```json
{
  "hsp_envelope_version": "0.1",
  "message_id": "<UUID_for_this_message>",
  "correlation_id": "<UUID_linking_req_to_rep_or_message_sequence_optional>",
  "sender_ai_id": "<DID_or_URI_of_sending_AI>",
  "recipient_ai_id": "<DID_or_URI_of_target_AI_or_topic_URI>",
  "timestamp_sent": "<ISO_8601_timestamp_UTC>",
  "message_type": "<String_identifying_payload_type_e.g.,_HSP::Fact_v0.1>",
  "protocol_version": "0.1", // HSP specification version
  "communication_pattern": "<String_enum_publish|request|response|stream_data|stream_ack>",
  "security_parameters": {
    "signature_algorithm": "<String_e.g.,_ES256K_optional_for_v0.1_early_dev>",
    "signature": "<String_digital_signature_optional_for_v0.1_early_dev>",
    "encryption_details": null // Placeholder for future use
  },
  "qos_parameters": {
    "priority": "<String_enum_low|medium|high_optional>",
    "requires_ack": "<boolean_default_false>",
    "time_to_live_sec": "<integer_optional>"
  },
  "routing_info": { // Optional
      "hops": ["<array_of_ai_ids_optional>"],
      "final_destination_ai_id": "<DID_or_URI_optional>"
  },
  "payload_schema_uri": "<URI_to_JSON_schema_for_payload_optional>",
  "payload": {
    // One of the data structures from Section 3
  }
}
```

### 4.3. Message Acknowledgements (ACKs/NACKs)
*   If `qos_parameters.requires_ack` is true, the recipient should send an ACK.
*   **ACK Message:** `message_type: "HSP::Acknowledgement_v0.1"`, `correlation_id` (of message being ACKed), `payload: {"status": "received", "ack_timestamp": "..."}`.
*   **NACK Message:** `message_type: "HSP::NegativeAcknowledgement_v0.1"`, `correlation_id`, `payload: {"status": "error", "error_code": "...", "error_message": "...", "nack_timestamp": "..."}`.

### 4.4. Topic Naming Conventions (for Pub/Sub)
Hierarchical, e.g.: `hsp/{domain}/{subdomain}/{specific_focus}`
*   `hsp/knowledge/facts/general`
*   `hsp/capabilities/advertisements/all`
*   `hsp/context/session/{session_id}`

## 5. Interaction Logic, Network Services & Meta-Formulas

### 5.1. AI Registration & Discovery
*   **Mechanism (v0.1 proposal):** AIs can publish their `CapabilityAdvertisement`s. A simple network "directory" service (itself an HPA) could subscribe to all capability advertisements and allow other AIs to query it for available capabilities.
    *   Query: `message_type: "HSP::CapabilityDiscoveryQuery_v0.1"`, `payload: {"capability_tags": ["nlp", "translation"], "min_trust_score": 0.7}`.
    *   Response: `message_type: "HSP::CapabilityDiscoveryResponse_v0.1"`, `payload: {"capabilities": [CapabilityAdvertisement_object_1, ...]}`.
*   Direct P2P discovery via gossip is a future consideration.

### 5.2. Capability Negotiation
*   Implicitly handled by versioning in `CapabilityAdvertisement`.
*   Direct query for specific `CapabilityAdvertisement` details is possible using its ID.

### 5.3. Trust Establishment & Management (Conceptual for v0.1)
*   **Signatures:** `security_parameters.signature` in the envelope verifies sender authenticity if public keys are managed/discoverable (e.g., via a DID registry or published by AIs).
*   **Reputation:** Not formally part of v0.1 protocol but AIs can implement local reputation tracking based on interaction history.
*   **VCs:** Future versions may incorporate Verifiable Credentials.

### 5.4. Conflict Resolution & Consensus (HSP Facilitates, AI Implements)
*   HSP transports `Fact`s/`Belief`s with `source_ai_id`, `timestamp_created`, `confidence_score`.
*   AIs are responsible for their own conflict resolution logic (e.g., preferring newer data, higher confidence, more trusted sources).
*   HSP could support a `KnowledgePollRequest`/`KnowledgePollResponse` message type in the future for explicit consensus-seeking.

### 5.5. Data Synchronization Strategies
*   **Pub/Sub for updates:** `Fact`s, `EnvironmentalState`s are published as they occur.
*   **Req/Rep for specific queries:** To get current state of a specific item.
*   Delta/full sync for `AIStateSynchronization` is complex and deferred beyond v0.1 basics.

### 5.6. Role of Meta-Formulas (Internal AI Logic)
*   HSP is designed to be usable by AIs that employ internal rule-based systems (meta-formulas) to govern their network interactions, policy enforcement, and dynamic responses to HSP messages. HSP itself does not define these meta-formulas but provides the structured messages and clear protocol states that such engines can act upon.

## 6. Network & Transport Considerations
*   HSP v0.1 is transport-agnostic. Messages are defined as data structures (e.g., JSON).
*   Common transports could include:
    *   **WebSockets:** For persistent bidirectional connections.
    *   **HTTP/2 or HTTP/3:** For Req/Rep, potentially with Server-Sent Events (SSE) for some Pub/Sub.
    *   **gRPC:** For high-performance P2P or client-server interactions (requires Protobuf).
    *   **MQTT:** For lightweight Pub/Sub, especially with a broker.
*   The choice of transport will affect how connections are managed and how the HSP envelope is framed for transmission.

## 7. Future Considerations & Versioning
*   **Versioning:**
    *   `hsp_envelope_version`: For changes to the envelope structure.
    *   `protocol_version` (in envelope): For overall HSP specification version.
    *   `message_type` strings should include versions (e.g., `HSP::Fact_v0.1`, `HSP::Fact_v0.2`).
    *   Semantic versioning (MAJOR.MINOR.PATCH) is recommended.
*   **Future Enhancements:**
    *   Advanced security (end-to-end encryption, detailed access control).
    *   Formalized semantic mapping/translation services.
    *   More sophisticated consensus algorithms.
    *   Distributed ledger for tracking critical transactions or AI reputations.
    *   Standardized error code ontology.

## 8. Glossary
*   **HSP:** Heterogeneous Synchronization Protocol.
*   **HPA (HSP Participant AI):** An AI entity participating in the HSP network.
*   **DID:** Decentralized Identifier.
*   **VC:** Verifiable Credential.
*   **JSON Schema:** A vocabulary that allows you to annotate and validate JSON documents.
*   **(Other terms as they become solidified)**

---
This initial draft captures the core ideas. It will need significant refinement, examples for all message types, and more detailed sequence diagrams for interactions. However, this forms the basis for `docs/HSP_SPECIFICATION.md`.
