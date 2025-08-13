# HAMMemoryManager: Hierarchical Abstractive Memory Manager

## Overview

This document provides an overview of the `HAMMemoryManager` module (`src/core_ai/memory/ham_memory_manager.py`). This is a sophisticated memory management system that handles the storage, retrieval, and processing of the AI's experiences. It is a cornerstone of the AI's ability to learn and adapt over time.

## Purpose

The purpose of the `HAMMemoryManager` is to provide the AI with a long-term memory system that goes beyond a simple key-value store. It is designed to be hierarchical, abstractive, and resilient, enabling the AI to learn from past experiences, recall relevant information in a context-aware manner, and manage its memory resources effectively.

## Key Responsibilities and Features

*   **Hierarchical Storage**: While the current implementation is a flat store, the "Hierarchical" aspect of HAM is a design goal, implying that memories can be organized in a structured and layered manner.
*   **Abstraction (`_abstract_text`)**: Instead of storing raw data, particularly text, the HAM creates an "abstracted gist" of the information. This gist includes a summary, keywords, and placeholders for more advanced linguistic features (like Part-of-Speech tags or Chinese radicals). This approach saves storage space and facilitates more efficient and meaningful retrieval.
*   **Data Integrity and Security**:
    *   **Encryption (`_encrypt`, `_decrypt`)**: Utilizes the Fernet symmetric encryption algorithm to protect the contents of stored memories. It relies on the `MIKO_HAM_KEY` environment variable for the encryption key, ensuring that sensitive data is secure.
    *   **Compression (`_compress`, `decompress`)**: Employs `zlib` to compress memory data before storage, significantly reducing the memory footprint.
    *   **Checksums**: Calculates and verifies a SHA256 checksum for each memory upon storage and retrieval, ensuring that the data has not been corrupted.
*   **Vector-Based Semantic Search**:
    *   Integrates with a `VectorMemoryStore` (which is backed by ChromaDB) to store vector embeddings of memories. This enables powerful semantic search capabilities.
    *   Uses an `ImportanceScorer` to assign an importance score to each memory, allowing for more nuanced retrieval and retention policies.
    *   The `retrieve_relevant_memories` method finds memories that are semantically similar to a given query, going beyond simple keyword matching.
*   **Rich Querying Capabilities**: Provides flexible query methods, including `query_core_memory` and `query_by_date_range`, which allow for filtering memories based on keywords, date ranges, data types, and other metadata.
*   **Resource Awareness**: Can be integrated with a `ResourceAwarenessService` to simulate disk space limitations and I/O lag. This makes the AI aware of its resource constraints and enables it to adapt its memory management strategies accordingly.
*   **Persistence**: Saves the core memory store to a JSON file, ensuring that the AI's memories persist across sessions and restarts.
*   **Automatic Cleanup**: Includes a background task (`_delete_old_experiences`) that periodically prunes old and irrelevant memories. This process is guided by the AI's personality traits (e.g., `memory_retention`) and the current memory usage, preventing the memory store from growing indefinitely.

## How it Works

When a new experience is stored, it is processed through a pipeline: abstraction -> checksumming -> compression -> encryption. The resulting data package is then stored in an in-memory dictionary and persisted to a file. For retrieval, the `HAMMemoryManager` can use traditional metadata-based filtering or modern vector-based semantic search to find the most relevant memories for a given context.

## Integration with Other Modules

*   **`VectorMemoryStore` and `ImportanceScorer`**: These are core components that provide the foundation for semantic search and memory ranking.
*   **`ResourceAwarenessService`**: An optional integration for simulated resource management.
*   **`PersonalityManager`**: An optional integration that can influence memory cleanup behavior.
*   **External Libraries**: Relies on a variety of libraries, including `Fernet` for encryption, `zlib` for compression, `hashlib` for checksums, `json` and `os` for file I/O, `asyncio` for asynchronous operations, `numpy` for numerical computations, and `chromadb` for vector storage.

## Code Location

`src/core_ai/memory/ham_memory_manager.py`