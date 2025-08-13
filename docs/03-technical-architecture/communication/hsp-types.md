# HSP Type Definitions

## Overview

This document provides an overview of the core data structures and message formats for the Heterogeneous Service Protocol (HSP), as defined in `src/hsp/types.py`.

## Purpose

The primary purpose of this module is to establish a standardized, type-safe contract for all messages exchanged between AI entities within the Unified AI Project. By defining these structures using `TypedDict`, it ensures data consistency, facilitates interoperability, and enables robust validation and parsing of HSP messages across different components and services.

## Key Data Structures

*   **`HSPMessageEnvelope`**: The foundational structure for any HSP message. It encapsulates metadata about the message itself and its communication context.
    *   **Core Fields**: `hsp_envelope_version`, `message_id`, `sender_ai_id`, `recipient_ai_id`, `timestamp_sent`, `message_type`, `protocol_version`, `communication_pattern`.
    *   **Optional Fields**: `correlation_id`, `security_parameters`, `qos_parameters`, `routing_info`, `payload_schema_uri`.
    *   `payload`: A generic dictionary (`Dict[str, Any]`) that holds the specific message content, whose structure is defined by other payload types.

*   **`HSPFactPayload`**: Defines the structure for messages conveying factual statements or learned information.
    *   Includes fields for the statement itself (in natural language or structured semantic triples), `confidence_score`, `source_ai_id`, `timestamp_created`, and various contextual metadata.

*   **`HSPBeliefPayload`**: Extends `HSPFactPayload` to represent beliefs, adding fields like `belief_holder_ai_id` and `justification` for the belief.

*   **`HSPCapabilityAdvertisementPayload`**: Defines the structure for messages where an AI advertises its available capabilities (e.g., tools, services, functions).
    *   Includes `capability_id`, `ai_id` (of the offering AI), `name`, `description`, `version`, input/output schemas, `cost_estimate_template`, `availability_status`, and `tags`.

*   **`HSPTaskRequestPayload`**: Defines the structure for messages used to request another AI to perform a specific task or execute a capability.
    *   Includes `request_id`, `requester_ai_id`, `target_ai_id`, `capability_id_filter` (or `capability_name_filter`), `parameters` (input for the capability), and optional fields for `priority`, `deadline`, and `callback_address`.

*   **`HSPTaskResultPayload`**: Defines the structure for messages conveying the outcome of a task execution.
    *   Includes `result_id`, `request_id` (linking to the original request), `executing_ai_id`, `status` (success, failure, in_progress, etc.), `payload` (the actual result data), and `error_details` if the task failed.

*   **`HSPErrorDetails`**: A standardized structure for conveying detailed error information within HSP messages, including `error_code`, `error_message`, and `error_context`.

*   **`HSPEnvironmentalStatePayload`**: Defines the structure for messages that update other AIs about changes in the shared environment or context.

*   **`HSPAcknowledgementPayload` / `HSPNegativeAcknowledgementPayload`**: Structures for confirming message receipt or indicating a rejection/error in processing a message.

## How it Works

This module primarily serves as a collection of `TypedDict` definitions. These definitions are imported and used throughout the backend codebase to ensure that data objects conform to the HSP specification. When messages are constructed for sending or parsed upon reception, these types provide strong type hints, enabling static analysis tools to catch potential data mismatches and improving code readability and maintainability.

## Integration with Other Modules

*   **`DataAligner`**: Heavily relies on these `TypedDict` definitions to validate the structure and content of incoming HSP messages.
*   **`HSPConnector`**: Uses these types when constructing outgoing HSP messages and when parsing incoming raw messages from the network.
*   **Various AI Components**: Modules such as `LearningManager` (for `HSPFactPayload`), `ServiceDiscoveryModule` (for `HSPCapabilityAdvertisementPayload`), and `ProjectCoordinator` (for `HSPTaskRequestPayload` and `HSPTaskResultPayload`) directly utilize these types for their communication needs.

## Code Location

`apps/backend/src/hsp/types.py`
