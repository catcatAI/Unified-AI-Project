# Common Types: Shared Data Structures

## Overview

The `common_types.py` (`src/shared/types/common_types.py`) module serves as a central repository for **reusable TypedDicts and Enums** that define the structure of data objects exchanged across various components and services within the Unified-AI-Project. By centralizing these definitions, the module ensures data consistency, enhances type safety, and improves code readability and maintainability throughout the codebase.

This module is crucial for facilitating clear communication and integration between different parts of the AI system, from core AI components to external service interfaces.

## Key Type Definitions

### 1. Service-Related Types

These types are used for defining and managing the status and advertisements of various services within the AI ecosystem.

-   **`ServiceStatus` (Enum)**:
    *   Defines the possible operational states of a service (e.g., `UNKNOWN`, `STARTING`, `HEALTHY`, `UNHEALTHY`, `STOPPING`, `STOPPED`, `DEGRADED`).

-   **`ServiceType` (Enum)**:
    *   Categorizes services based on their function (e.g., `UNKNOWN`, `CORE_AI_COMPONENT`, `EXTERNAL_API`, `DATA_STORE`, `INTERNAL_TOOL`, `HSP_NODE`).

-   **`ServiceAdvertisement` (TypedDict)**:
    *   Describes a service that is being advertised, including its `service_id`, `service_name`, `service_type`, `service_version`, `endpoint_url`, `metadata`, `status`, `last_seen_timestamp`, and `ttl` (time-to-live).

-   **`ServiceQuery` (TypedDict)**:
    *   Defines parameters for querying available services, allowing filtering by `service_type`, `service_name`, `min_version`, `required_capabilities`, and `status_filter`.

-   **`ServiceInstanceHealth` (TypedDict)**:
    *   Provides health information for a specific service instance, including its `service_id`, `instance_id`, `status`, `last_heartbeat`, and `metrics`.

### 2. Dialogue-Related Types

These types are used by the `DialogueManager` and related components to structure conversational data and operational configurations.

-   **`DialogueTurn` (TypedDict)**:
    *   Represents a single turn in a dialogue, specifying the `speaker` (user, ai, system), `text`, `timestamp`, and optional `metadata`.

-   **`PendingHSPTaskInfo` (TypedDict)**:
    *   Stores information about an HSP task that is awaiting a result, including `user_id`, `session_id`, `original_query_text`, `request_timestamp`, `capability_id`, `target_ai_id`, `expected_callback_topic`, and `request_type`.

-   **`OperationalConfig` (TypedDict)**:
    *   Defines various operational configurations for the AI, such as `timeouts`, `learning_thresholds`, `default_hsp_fact_topic`, `max_dialogue_history`, and general `operational_configs`.

-   **`CritiqueResult` (TypedDict)**:
    *   Represents the result of a critique, including a `score`, `reason`, and `suggested_alternative`.

-   **`DialogueMemoryEntryMetadata` (TypedDict)**:
    *   Metadata associated with a dialogue memory entry, including `speaker`, `timestamp`, `user_input_ref`, `sha256_checksum`, `critique`, `user_feedback_explicit`, and `learning_weight`.

-   **`ParsedToolIODetails` (TypedDict)**:
    *   Details about a parsed tool's input/output, including `suggested_method_name`, `class_docstring_hint`, `method_docstring_hint`, `parameters`, `return_type`, and `return_description`.

-   **`OverwriteDecision` (Enum)**:
    *   Defines strategies for handling data overwrites in memory (e.g., `PREVENT_OVERWRITE`, `OVERWRITE_EXISTING`, `ASK_USER`, `MERGE_IF_APPLICABLE`).

### 3. LLM Interface Types

These types are used by the `MultiLLMService` for configuring and describing LLM providers and models.

-   **`LLMProviderOllamaConfig` (TypedDict)**:
    *   Configuration specific to the Ollama LLM provider, including `base_url`.

-   **`LLMProviderOpenAIConfig` (TypedDict)**:
    *   Configuration specific to the OpenAI LLM provider, including `api_key`.

-   **`LLMModelInfo` (TypedDict)**:
    *   Provides information about an LLM model, including its `id`, `provider`, `name`, `description`, `modified_at` timestamp, and `size_bytes`.

### 4. HAM Memory Types

These types are used by the `HAMMemoryManager` for structuring memory recall results and internal data packages.

-   **`HAMRecallResult` (dataclass)**:
    *   Represents the result of a HAM memory recall operation, including `memories`, `confidence_scores`, `total_count`, and `query_metadata`.

-   **`HAMDataPackageInternal` (TypedDict)**:
    *   Defines the structure of an internal HAM data package, including `package_id`, `data_type`, `content`, `metadata`, `timestamp`, `source_ai_id`, and `confidence_score`.

## Importance and Usage

By centralizing these common type definitions, `common_types.py` plays a vital role in:

-   **Ensuring Data Consistency**: All modules use the same definitions for shared data structures, preventing discrepancies.
-   **Improving Type Safety**: Provides clear type hints, enabling static analysis tools to catch potential errors early in the development cycle.
-   **Enhancing Readability and Maintainability**: Developers can quickly understand the structure of data objects without needing to infer them from context.
-   **Facilitating Integration**: Simplifies the process of integrating new modules or services by providing well-defined interfaces.

## Code Location

`src/shared/types/common_types.py`
