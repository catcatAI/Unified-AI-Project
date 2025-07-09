# Heterogeneous Synchronization Protocol (HSP) Specification - Version 0.1.1

## 1. Introduction

### 1.1. Purpose
The Heterogeneous Synchronization Protocol (HSP) is designed to enable communication, data sharing, and collaborative task execution among diverse and independently developed AI entities (HSP Participant AIs). It aims to foster a robust, scalable, and intelligent ecosystem of interconnected AIs.

### 1.2. Goals
*   **Interoperability:** Allow AIs with different internal architectures and capabilities to exchange information and services meaningfully.
*   **Robustness:** Enhance overall system resilience through distributed knowledge, potential for consensus, and fault isolation.
*   **Scalability:** Support a growing network of AIs and increasing information flow.
*   **Collaboration:** Enable AIs to work together on complex tasks that may be beyond the capability of a single AI.
*   **Extensibility:** Design the protocol to be adaptable to future advancements in AI and communication technologies.

### 1.3. Scope (Version 0.1.1)
This version (0.1.1) focuses on establishing the foundational elements of the HSP, including:
*   Core information types for knowledge sharing and tasking, with clarification on required fields.
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
*Default data format for payloads in v0.1.1 is JSON. JSON Schema should be used for validation where possible.*
*For payload fields, "Required" means the field must be present for a valid v0.1.1 message of this type.*

### 3.1. `Fact` / `Assertion`
*   **Purpose:** Represents a statement about the world, an entity, or a relationship, believed to be true by the originating AI to some degree.
*   **Key Fields (v0.1.1):**
    *   `id` (string, UUID): **Required.** Unique identifier for this fact instance.
    *   `statement_type` (string, enum: "natural_language", "semantic_triple", "json_ld"): **Required.** Specifies the representation of the core assertion.
    *   `statement_nl` (string, optional if `statement_structured` present): The assertion in natural language.
    *   `statement_structured` (object, optional if `statement_nl` present): Structured representation.
    *   `source_ai_id` (string, DID/URI): **Required.** ID of the AI originating or asserting this fact.
    *   `timestamp_created` (string, ISO 8601 UTC): **Required.** When this fact was asserted/created by `source_ai_id`.
    *   `confidence_score` (float, 0.0-1.0): **Required.** The AI's confidence in the truth of this fact.
*   **Optional Fields:**
    *   `original_source_info` (object): Information about the ultimate source if learned externally.
        *   `type` (string, e.g., "url", "document_id", "user_id", "sensor_id").
        *   `identifier` (string).
    *   `timestamp_observed` (string, ISO 8601 UTC): If the fact describes an event, when that event was observed or occurred.
    *   `weight` (float, default: 1.0): General-purpose weight (relevance, importance, priority).
    *   `valid_from` (string, ISO 8601 UTC): Timestamp from which the fact is considered valid.
    *   `valid_until` (string, ISO 8601 UTC): Timestamp until which the fact is considered valid.
    *   `context` (object): Key-value pairs describing the context in which this fact is true.
    *   `tags` (array of strings): Keywords or categories.
    *   `access_policy_id` (string): Identifier for a policy governing sharing/use.
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
*   **Key Fields (v0.1.1):** Inherits required fields from `Fact` (`id`, `statement_type`, `source_ai_id`, `timestamp_created`, `confidence_score`). Additionally:
    *   `belief_holder_ai_id` (string, DID/URI): **Required.** The AI holding this belief (defaults to `source_ai_id` if not explicitly provided by sender).
*   **Optional Fields:** Inherits optional fields from `Fact`. Additional/modified optional fields:
    *   `justification_type` (string, enum: "text", "inference_chain_id", "evidence_ids_list").
    *   `justification` (string or array): Reasoning, link to an inference chain, or list of supporting fact/belief IDs.
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
*   **Key Fields (v0.1.1):**
    *   `capability_id` (string, unique): **Required.**
    *   `ai_id` (string, DID/URI): **Required.**
    *   `name` (string): **Required.** Human-readable name.
    *   `description` (string): **Required.** Detailed description.
    *   `version` (string, e.g., "1.2.0"): **Required.**
    *   `availability_status` (string, enum: "online", "offline", "degraded", "maintenance"): **Required.**
*   **Optional Fields:** `input_schema_uri`, `input_schema_example`, `output_schema_uri`, `output_schema_example`, `data_format_preferences`, `hsp_protocol_requirements`, `cost_estimate_template`, `access_policy_id`, `tags`.
*   **Example (JSON):**
    ```json
    {
      "capability_id": "ai_gamma_translate_v1.2",
      "ai_id": "did:hsp:ai_gamma",
      "name": "Text Translation Service",
      "description": "Translates text between English and French.",
      "version": "1.2.0",
      "availability_status": "online",
      "tags": ["nlp", "translation", "text"]
    }
    ```

### 3.4. `TaskRequest`
*   **Purpose:** An AI requests another AI to perform a task using an advertised capability.
*   **Key Fields (v0.1.1):**
    *   `request_id` (string, UUID): **Required.**
    *   `requester_ai_id` (string, DID/URI): **Required.**
    *   `parameters` (object): **Required.** Input parameters.
*   **Optional Fields:** `target_ai_id`, `capability_id_filter`, `capability_name_filter`, `requested_output_data_format`, `priority`, `deadline_timestamp`, `callback_address`.
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
*   **Key Fields (v0.1.1):**
    *   `result_id` (string, UUID): **Required.**
    *   `request_id` (string, UUID): **Required.** ID of the `TaskRequest`.
    *   `executing_ai_id` (string, DID/URI): **Required.**
    *   `status` (string, enum: "success", "failure", "in_progress", "queued", "rejected"): **Required.**
*   **Optional Fields:** `payload` (if status is "success"), `output_data_format`, `error_details` (if status is "failure"/"rejected"), `timestamp_completed`, `execution_metadata`.
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
*   **Key Fields (v0.1.1):**
    *   `update_id` (string, UUID): **Required.**
    *   `source_ai_id` (string, DID/URI): **Required.**
    *   `phenomenon_type` (string, URI/namespaced string): **Required.**
    *   `parameters` (object): **Required.** Specifics of the state/context.
    *   `timestamp_observed` (string, ISO 8601 UTC): **Required.**
*   **Optional Fields:** `scope_type`, `scope_id`, `relevance_decay_rate`.
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
*   Default for v0.1.1: JSON.
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
  "message_id": "msg_uuid_example_789",
  "sender_ai_id": "did:hsp:ai_alpha",
  "recipient_ai_id": "hsp/knowledge/facts/general", // Can be a topic or specific AI ID
  "timestamp_sent": "2024-07-05T14:00:00Z",
  "message_type": "HSP::Fact_v0.1",
  "protocol_version": "0.1", // Refers to the HSP Specification version, e.g., "0.1.1"
  "communication_pattern": "publish",
  // Optional fields below: correlation_id, security_parameters, qos_parameters, routing_info, payload_schema_uri
  "correlation_id": null, // Or absent if not applicable
  "security_parameters": null, // Or absent if not used
  "qos_parameters": {
    "priority": "medium", // "low", "medium", "high"
    "requires_ack": false,
    "time_to_live_sec": null // Or an integer if set
  },
  "routing_info": null, // Or absent, or {"hops": [], "final_destination_ai_id": "..."}
  "payload_schema_uri": null, // Or absent, or "hsp:schema:payload/Fact/0.1"
  "payload": {
    "id": "fact_uuid_envelope_example",
    "statement_type": "natural_language",
    "statement_nl": "This is an example fact within an envelope.",
    "source_ai_id": "did:hsp:ai_alpha",
    "timestamp_created": "2024-07-05T13:59:00Z",
    "confidence_score": 0.90
  }
}
```
**Note on Envelope Fields:**
*   **Required:** `hsp_envelope_version`, `message_id`, `sender_ai_id`, `recipient_ai_id`, `timestamp_sent`, `message_type`, `protocol_version`, `communication_pattern`, `payload`.
*   **Optional:** `correlation_id`, `security_parameters`, `qos_parameters`, `routing_info`, `payload_schema_uri`.
    *   If `security_parameters`, `qos_parameters`, or `routing_info` are present, their internal fields also have their own optionality as defined in their respective `TypedDict` structures. For `qos_parameters`, `priority` and `requires_ack` typically have defaults if the object is present, while `time_to_live_sec` is optional.

### 4.3. Message Acknowledgements (ACKs/NACKs)
*   If `qos_parameters.requires_ack` is true, the recipient should send an ACK.
*   **ACK Message:** `message_type: "HSP::Acknowledgement_v0.1"`, `correlation_id` (of message being ACKed), `payload: {"status": "received" or "processed", "ack_timestamp": "...", "target_message_id": "original_message_id"}`.
*   **NACK Message:** `message_type: "HSP::NegativeAcknowledgement_v0.1"`, `correlation_id`, `payload: {"status": "error", "error_code": "...", "error_message": "...", "nack_timestamp": "...", "target_message_id": "original_message_id"}`.

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

#### 5.4.1. Recommended Practices for Handling Conflicting Information (Receiver-Side)
While HSP provides the basic data fields, the consuming AI is responsible for robust conflict resolution. When storing or processing facts received via HSP, especially from multiple peers, AIs may benefit from maintaining additional local metadata associated with the ingested information. This metadata is not part of the HSP payload itself but aids the AI's internal knowledge management.

Recommended local metadata fields for a receiver to consider storing:
*   `internal_storage_id`: The unique ID of the fact/belief within the AI's own memory system.
*   `hsp_sender_ai_id`: The `sender_ai_id` from the HSP envelope (the direct peer who sent the message). This is crucial for applying trust scores.
*   `effective_confidence`: A score calculated by the receiver, often combining the fact's `confidence_score` with the trust score of the `hsp_sender_ai_id` (e.g., `original_confidence * trust_in_sender`).
*   `processing_timestamp`: When this HSP message was processed by the receiver.
*   `resolution_strategy_applied`: A string indicating how any conflict involving this piece of information was resolved (e.g., "NEWEST_WINS", "HIGHEST_CONFIDENCE_SUPERSEDE", "TRUST_WEIGHTED_MERGE", "LOGGED_CONTRADICTION", "USER_VERIFIED").
*   `superseded_internal_ids`: A list of `internal_storage_id`s of other facts/beliefs in the AI's memory that this information has superseded.
*   `conflicts_with_internal_ids`: A list of `internal_storage_id`s of other facts/beliefs that this information directly contradicts but has not superseded (e.g., due to similar confidence and no clear tie-breaker).
*   `merged_from_internal_ids`: If this information is the result of a merge (e.g., numerical averaging), a list of `internal_storage_id`s of the source facts.
*   `merged_value_details`: If applicable, details about the merged value (e.g., the calculated average).
*   `extracted_semantic_subject_uri`, `extracted_semantic_predicate_uri`, `extracted_semantic_object_representation`: Standardized URIs or representations of the fact's core semantic components, extracted by the receiver's content analysis/mapping modules. These are vital for detecting Type 2 (semantic) conflicts where different fact IDs make claims about the same entity-attribute pair.

By maintaining such metadata, an AI can build a more nuanced understanding of its knowledge base, track provenance, and make more informed decisions when faced with conflicting data from the HSP network. The specific conflict resolution algorithms (e.g., how to perform a numerical merge, how to weigh trust vs. recency) remain internal to each AI.

### 5.5. Data Synchronization Strategies
*   **Pub/Sub for updates:** `Fact`s, `EnvironmentalState`s are published as they occur.
*   **Req/Rep for specific queries:** To get current state of a specific item.
*   Delta/full sync for `AIStateSynchronization` is complex and deferred beyond v0.1 basics.

### 5.6. Role of Meta-Formulas (Internal AI Logic)
*   HSP is designed to be usable by AIs that employ internal rule-based systems (meta-formulas) to govern their network interactions, policy enforcement, and dynamic responses to HSP messages. HSP itself does not define these meta-formulas but provides the structured messages and clear protocol states that such engines can act upon.

## 6. Network & Transport Considerations
*   HSP v0.1.1 is transport-agnostic. Messages are defined as data structures (e.g., JSON).
*   Common transports could include:
    *   **WebSockets:** For persistent bidirectional connections.
    *   **HTTP/2 or HTTP/3:** For Req/Rep, potentially with Server-Sent Events (SSE) for some Pub/Sub.
    *   **gRPC:** For high-performance P2P or client-server interactions (requires Protobuf).
    *   **MQTT:** For lightweight Pub/Sub, especially with a broker. (Current reference implementation uses MQTT).
*   The choice of transport will affect how connections are managed and how the HSP envelope is framed for transmission.

## 7. Future Considerations & Versioning
*   **Versioning:**
    *   `hsp_envelope_version`: For changes to the envelope structure.
    *   `protocol_version` (in envelope): For overall HSP specification version (e.g., "0.1.1").
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

---

## Appendix A: Current Implementation Status Notes (as of July 2024)

This appendix provides a brief overview of the current implementation status of certain HSP components, which may differ from the ideal state described in the main specification. This is intended to provide context for developers working with the current codebase.

*   **`ServiceDiscoveryModule` (`src/core_ai/service_discovery/service_discovery_module.py`):**
    *   The current implementation of the `ServiceDiscoveryModule` is a generic service registry. It **does not yet fully align with the HSP-specific requirements** for processing `HSPCapabilityAdvertisementPayload`, integrating with the `TrustManager` for capability assessment, or managing the lifecycle of HSP capabilities as envisioned in this specification (e.g., Section 5.1).
    *   Significant refactoring or replacement of this module is required to meet the HSP specification. Logic for capability staleness, while prototyped, will need to be integrated into an HSP-compliant version.

*   **`payload_schema_uri` in HSP Message Envelope:**
    *   As per Section 4.2, the `payload_schema_uri` field is intended to point to a resolvable schema for the message payload.
    *   In the current implementation (`src/hsp/connector.py`), this field is populated with **conventional placeholder URIs** (e.g., `hsp:schema:payload/Fact/0.1`) based on message type and version.
    *   The formal definition, publication, and hosting of these schemas at resolvable URIs are pending future architectural work. For now, developers should be aware that these URIs are placeholders and do not resolve to actual schemas.

*   **General Completeness:**
    *   While core message types and MQTT-based transport are functional, advanced features like comprehensive semantic translation services, complex consensus mechanisms, and detailed state synchronization (`AIStateSynchronization`) are still conceptual or in early stages of consideration.
    *   Robust error handling and advanced QoS features beyond basic MQTT support are areas for ongoing development.

These notes are intended to bridge the gap between the specification and the current codebase. Refer to `docs/PROJECT_STATUS_SUMMARY.md` for a more comprehensive status of all project components.
