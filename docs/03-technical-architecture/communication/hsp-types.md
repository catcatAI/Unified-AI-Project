# HSP Types: Heterogeneous Service Protocol Data Structures

## Overview

The `types.py` (`src/hsp/types.py`) module is the definitive source for **all data structures and message formats** used within the Heterogeneous Service Protocol (HSP) of the Unified-AI-Project. It leverages Python's `TypedDict` and `Literal` types to provide clear, explicit, and type-safe definitions for the various messages exchanged between AI entities.

This module is crucial for ensuring interoperability, data consistency, and robust communication across the entire HSP network, serving as the blueprint for how AI agents understand and interact with each other's data.

## Key Type Definitions

### 1. Core Message Envelope

-   **`HSPMessageEnvelope` (TypedDict)**:
    *   The fundamental wrapper for all HSP messages. It defines the metadata and routing information common to every message.
    *   Key fields include: `hsp_envelope_version`, `message_id` (UUID), `correlation_id` (for request-response patterns), `sender_ai_id`, `recipient_ai_id`, `timestamp_sent`, `message_type` (e.g., "HSP::Fact_v0.1"), `protocol_version`, `communication_pattern` (e.g., "publish", "request", "response"), `security_parameters`, `qos_parameters`, `routing_info`, `payload_schema_uri`, and the `payload` itself.

### 2. Payload Types

These TypedDicts define the structure of the `payload` within the `HSPMessageEnvelope` for different types of HSP communication.

-   **`HSPFactPayload` (TypedDict)**:
    *   Represents a factual statement or piece of knowledge being shared.
    *   Includes fields like `id`, `statement_type` (e.g., "natural_language", "semantic_triple"), `statement_nl` (natural language), `statement_structured` (for structured data like semantic triples), `source_ai_id`, `original_source_info`, `timestamp_created`, `confidence_score`, `weight`, `valid_from`, `valid_until`, `context`, `tags`, and `access_policy_id`.

-   **`HSPBeliefPayload` (TypedDict)**:
    *   Extends `HSPFactPayload` to represent a belief held by an AI, including `belief_holder_ai_id` and optional `justification`.

-   **`HSPCapabilityAdvertisementPayload` (TypedDict)**:
    *   Used by AI agents to advertise their available capabilities to the network.
    *   Includes `capability_id`, `ai_id` (of the advertiser), `agent_name`, `name`, `description`, `version`, `input_schema_uri`, `output_schema_uri`, `availability_status`, and `tags`.

-   **`HSPTaskRequestPayload` (TypedDict)**:
    *   Defines the structure for one AI to request a task from another.
    *   Includes `request_id`, `requester_ai_id`, `target_ai_id`, `capability_id_filter`, `parameters`, `requested_output_data_format`, `priority`, `deadline_timestamp`, and `callback_address`.

-   **`HSPTaskResultPayload` (TypedDict)**:
    *   Defines the structure for an AI to send back the result of a task request.
    *   Includes `result_id`, `request_id` (of the original task), `executing_ai_id`, `status` (e.g., "success", "failure"), `payload` (the result data), `output_data_format`, `error_details`, `timestamp_completed`, and `execution_metadata`.

-   **`HSPAcknowledgementPayload` (TypedDict)**:
    *   For acknowledging receipt or processing of a message.

-   **`HSPNegativeAcknowledgementPayload` (TypedDict)**:
    *   For indicating an error or rejection of a message, including `error_details`.

-   **`HSPEnvironmentalStatePayload` (TypedDict)**:
    *   Also known as ContextUpdate, for sharing environmental observations or state changes.

### 3. Supporting Types

-   **`HSPSecurityParameters` (TypedDict)**:
    *   Defines parameters related to message security (e.g., `signature_algorithm`, `signature`, `encryption_details`).

-   **`HSPQoSParameters` (TypedDict)**:
    *   Defines parameters related to Quality of Service (QoS) for messages (e.g., `priority`, `requires_ack`, `time_to_live_sec`).

-   **`HSPRoutingInfo` (TypedDict)**:
    *   Provides information about message routing (e.g., `hops`, `final_destination_ai_id`).

## Importance and Usage

`hsp/types.py` is fundamental because it:

-   **Enforces Protocol Compliance**: Ensures all messages adhere to the HSP specification, enabling seamless communication between diverse AI components.
-   **Enhances Type Safety**: Provides strong type hints for message structures, reducing runtime errors and improving code quality.
-   **Facilitates Development**: Developers can easily understand the expected format of HSP messages, simplifying integration and debugging.
-   **Supports Interoperability**: Acts as a common language for AI entities, regardless of their internal implementation details.

## Code Location

`src/hsp/types.py`
