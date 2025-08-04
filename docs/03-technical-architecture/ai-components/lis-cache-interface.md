# Linguistic Immune System (LIS) Cache Interface

## Overview

The `LISCacheInterface` (`src/core_ai/lis/lis_cache_interface.py`) defines the contract for the **Immuno-Narrative Cache**, a critical component of the Linguistic Immune System (LIS) within the Unified-AI-Project. This cache serves as the memory and learning repository for LIS, enabling the AI to detect, analyze, and respond to semantic anomalies and inconsistencies in its knowledge and interactions.

The LIS, as described in `PHILOSOPHY_AND_VISION.md`, is designed to protect the AI from "model collapse" by evaluating the quality and consistency of information. The `LISCacheInterface` provides the necessary mechanisms for LIS to store incident reports, track interventions, and learn effective "narrative antibodies" (successful response patterns).

## Key Responsibilities and Features

The `LISCacheInterface` specifies methods for:

1.  **Storing Incidents (`store_incident`)**:
    *   Records detailed `LIS_IncidentRecord` objects, which capture semantic anomalies, their context, and initial analysis.

2.  **Retrieving Incidents (`get_incident_by_id`)**:
    *   Allows for the retrieval of specific incident records by their unique ID.

3.  **Querying Incidents (`query_incidents`)**:
    *   Enables searching for incidents based on various criteria such as anomaly type, severity, status, tags, and time window.

4.  **Finding Related Incidents (`find_related_incidents`)**:
    *   Identifies past incidents that are semantically similar or related to a newly detected anomaly, providing historical context for analysis and response.

5.  **Retrieving Learned Antibodies (`get_learned_antibodies`)**:
    *   Fetches `NarrativeAntibodyObject` instances, which represent successful strategies or patterns learned from past incidents. These antibodies are crucial for LIS's adaptive capabilities.

6.  **Updating Incident Status (`update_incident_status`)**:
    *   Allows for updating the status of an incident (e.g., from "OPEN" to "RESOLVED") and adding notes or intervention reports.

7.  **Adding Antibodies (`add_antibody`)**:
    *   Stores new `NarrativeAntibodyObject` instances into the cache, expanding the AI's repertoire of effective responses to anomalies.

## Concrete Implementation: `HAMLISCache`

The `HAMLISCache` is a concrete implementation of the `LISCacheInterface` that leverages the `HAMMemoryManager` for persistence. This integration highlights the foundational role of HAM in storing various types of AI knowledge, including the specialized data required by LIS.

### Design Considerations for `HAMLISCache`:

-   **HAM Data Types**: LIS incident records and narrative antibodies are stored as distinct entries in HAM using specific `data_type` prefixes (e.g., `lis_incident_v0.1_`, `lis_antibody_v0.1_`).
-   **Metadata for Querying**: Key fields from LIS objects (e.g., `anomaly_type`, `status`, `severity`, `effectiveness`) are extracted and stored in HAM's metadata. This allows `HAMMemoryManager`'s powerful querying capabilities to be used for LIS data.
-   **Serialization**: LIS objects are serialized (e.g., to JSON strings) before being stored as `raw_data` in HAM entries.
-   **Updates**: Updates to LIS incidents or antibodies involve retrieving the HAM entry, modifying its content/metadata, and re-storing it. The system handles potential immutability of HAM entries by storing new versions or updating metadata fields.
-   **Semantic Similarity**: For `find_related_incidents`, the conceptual design involves storing embeddings or feature vectors within HAM metadata to support semantic similarity queries, an advanced feature for future development.

## Integration with Other Modules

-   **`LinguisticImmuneSystem` (Conceptual)**: The higher-level LIS logic would interact with this cache to manage its operations.
-   **`HAMMemoryManager`**: Provides the underlying storage and querying infrastructure.
-   **`LearningManager`**: May interact with LIS to feed new anomaly detections or learn from LIS interventions.

## Code Location

`src/core_ai/lis/lis_cache_interface.py`
