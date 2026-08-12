# Memory Types: Internal Data Structures for Hierarchical Abstractive Memory

## Overview

This document provides an overview of the internal data structures defined in the `src/core_ai/memory/types.py` module. These TypedDicts (`HAMDataPackageInternal`, `HAMRecallResult`) are fundamental for representing how data is internally packaged for storage and how results are structured upon retrieval within the Hierarchical Abstractive Memory (HAM) system.

This module is crucial for ensuring consistency, type safety, and clarity in the internal operations of HAM, particularly concerning data persistence, encryption, and the reconstruction of recalled information.

## Key Responsibilities and Features

*   **`HAMDataPackageInternal` (TypedDict)**: Defines the internal structure of a data package that HAM prepares for storage. It includes:
    *   `timestamp`: An ISO 8601 UTC string indicating the creation time of the data package.
    *   `data_type`: A string that categorizes the type of data being stored (e.g., "dialogue_turn", "fact", "incident_record"). This allows for type-specific handling and querying.
    *   `encrypted_package`: The actual data content, stored as `bytes`. This field implies that data within HAM is typically encrypted or otherwise processed into a binary format before persistence, emphasizing data security and abstraction from its original form.
    *   `metadata`: A dictionary for storing additional, searchable attributes associated with the data package. This metadata is crucial for efficient querying and contextual retrieval.

*   **`HAMRecallResult` (TypedDict)**: Defines the structured format for the result of a memory recall operation from HAM. It includes:
    *   `id`: The unique identifier of the recalled memory.
    *   `timestamp`: The ISO 8601 UTC string of the original storage timestamp of the memory.
    *   `data_type`: The category of the recalled data, mirroring the `data_type` used during storage.
    *   `rehydrated_gist`: The "rehydrated" or reconstructed content of the memory. This field is typed as `Any`, indicating that HAM handles the deserialization or reconstruction of the stored `encrypted_package` back into a usable format (e.g., a string for text, a dictionary for structured data, or a Python object).
    *   `metadata`: The metadata associated with the recalled memory, providing context and searchable attributes.

## How it Works

These TypedDicts serve as the internal contracts for data flow within the HAM system. `HAMDataPackageInternal` specifies how raw data, along with its type and metadata, is encapsulated and potentially encrypted before being handed off to HAM's persistence layer. `HAMRecallResult` defines the format in which HAM returns data after a query, ensuring that consuming modules receive not only the original metadata but also a reconstructed, usable version of the stored content. This design promotes a clear separation between the raw, stored data and its logical, usable representation.

## Integration with Other Modules

*   **`HAMMemoryManager`**: The primary consumer and producer of these types, using them extensively for its internal storage, retrieval, and data processing logic.
*   **`VectorMemoryStore`**: Would interact with these types, particularly for extracting metadata and `data_type` for indexing, and for handling the `rehydrated_gist` during semantic search results.
*   **Internal HAM Components**: Any internal HAM modules responsible for encryption/decryption, data serialization/deserialization, or data integrity would rely on these defined structures.
*   **Other AI Components**: While typically interacting with `HAMMemoryManager` directly, understanding these internal types provides insight into how HAM manages its data.

## Code Location

`src/core_ai/memory/types.py`