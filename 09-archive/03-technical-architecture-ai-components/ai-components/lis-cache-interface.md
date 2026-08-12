# LISCacheInterface & HAMLISCache: Linguistic Immune System Memory Component

## Overview

This document provides an overview of the `LISCacheInterface` (an Abstract Base Class) and its concrete implementation, `HAMLISCache`, found in `src/core_ai/lis/lis_cache_interface.py`. This module defines the interface for the Linguistic Immune System (LIS) Cache, also known as the IMMUNO-NARRATIVE CACHE, which is responsible for storing, retrieving, and querying records of linguistic/semantic incidents, their analyses, interventions, and outcomes.

## Purpose

The primary purpose of the LIS Cache is to serve as the memory component of the Linguistic Immune System, directly supporting its learning and adaptive capabilities. It provides a persistent store for "incidents" (detected semantic anomalies or linguistic challenges) and "antibodies" (learned successful response patterns or strategies). This enables the AI to learn from past linguistic challenges, recognize recurring issues, and apply effective, previously learned solutions, thereby enhancing its robustness and adaptability in communication.

## Key Responsibilities and Features

### `LISCacheInterface` (Abstract Base Class)

Defines the contract for any LIS cache implementation, ensuring a consistent API for managing LIS data:

*   **`store_incident`**: Abstract method to store a new `LIS_IncidentRecord`.
*   **`get_incident_by_id`**: Abstract method to retrieve a specific `LIS_IncidentRecord` by its unique ID.
*   **`query_incidents`**: Abstract method to query `LIS_IncidentRecord`s based on various criteria (e.g., anomaly type, severity, status, tags, time window).
*   **`find_related_incidents`**: Abstract method to find past incidents that are semantically similar or related to a new detected event, crucial for contextual recall.
*   **`get_learned_antibodies`**: Abstract method to retrieve learned successful response patterns (`NarrativeAntibodyObject`s).
*   **`update_incident_status`**: Abstract method to update the status and optionally add notes or an intervention report to an existing incident record.
*   **`add_antibody`**: Abstract method to store a new `NarrativeAntibodyObject`.

### `HAMLISCache` (Concrete Implementation)

Provides a concrete implementation of the `LISCacheInterface` using the Hierarchical Associative Memory (HAM) for persistence:

*   **HAM Integration**: Utilizes an instance of `HAMMemoryManager` as its backend for all storage and retrieval operations.
*   **Data Type Prefixes**: Stores `LIS_IncidentRecord` and `NarrativeAntibodyObject` as distinct entries in HAM, using specific `data_type` prefixes (`LIS_INCIDENT_DATA_TYPE_PREFIX`, `LIS_ANTIBODY_DATA_TYPE_PREFIX`) to allow for targeted querying within HAM.
*   **Metadata Leveraging**: Extracts key queryable fields from LIS objects (e.g., `anomaly_type`, `status`, `tags` for incidents; `anomaly_type`, `effectiveness` for antibodies) and stores them in the HAM metadata of the corresponding entry. This leverages HAM's metadata-based querying capabilities for efficient filtering.
*   **Serialization**: Serializes the full `LIS_IncidentRecord` or `NarrativeAntibodyObject` into JSON strings before storing them as the `raw_data` content of the HAM entry, ensuring compatibility and data integrity.
*   **Querying and Post-filtering**: Implements the query methods by building appropriate `metadata_filters` for HAM. It also includes post-filtering logic for criteria that HAM's native querying might not fully support (e.g., range queries for severity or time windows, or complex tag matching).
*   **Conceptual Semantic Search**: The `find_related_incidents` method includes conceptual outlines for semantic similarity search, indicating that a more advanced implementation would require HAM to support storing and querying embeddings or feature vectors.

## How it Works

`LISCacheInterface` establishes the blueprint for the LIS's memory. `HAMLISCache` brings this blueprint to life by interfacing with the `HAMMemoryManager`. When an LIS object (incident or antibody) needs to be stored, `HAMLISCache` serializes it and stores it in HAM, populating HAM's metadata with key LIS attributes for efficient lookup. When data is retrieved, `HAMLISCache` queries HAM, deserializes the results, and performs any necessary post-filtering to match the requested criteria. This design allows the LIS to leverage HAM's robust memory capabilities for its specialized needs.

## Integration with Other Modules

*   **LIS Type Definitions**: Relies heavily on `LIS_IncidentRecord`, `LIS_SemanticAnomalyDetectedEvent`, `LIS_AnomalyType`, `LIS_InterventionReport`, and `NarrativeAntibodyObject` (all imported from `src.core_ai.lis.types`) for defining the structure of the data it handles.
*   **`HAMMemoryManager`**: The core dependency for `HAMLISCache`, providing the underlying persistent memory storage.
*   **`json`**: Used for serializing and deserializing LIS objects to and from JSON strings for storage.
*   **`datetime`, `timezone`**: Used for timestamping and time-based filtering of records.
*   **`LIS_TonalRepairEngine`**: Modules like the `LIS_TonalRepairEngine` would likely interact with this cache to retrieve relevant antibodies (solutions) when a semantic anomaly is detected.

## Code Location

`src/core_ai/lis/lis_cache_interface.py`