# HAMTypes: Core Data Structures for Hierarchical Associative Memory

## Overview

This document provides an overview of the `ham_types.py` module (`src/core_ai/memory/ham_types.py`). This module defines the core data structures used within the Hierarchical Associative Memory (HAM) system, including representations for individual memory records, recall results, and detailed metadata for dialogue-related memory entries.

## Purpose

The primary purpose of `ham_types.py` is to establish a standardized and clear schema for representing memories within the HAM system. This ensures consistency and facilitates interoperability between different HAM components (e.g., storage, retrieval, processing) and other AI modules that interact with HAM. By providing well-defined data models, it enhances the clarity and maintainability of the memory system.

## Key Responsibilities and Features

*   **`HAMMemory` Class**:
    *   Represents a single, fundamental memory entry stored within the HAM system.
    *   **Attributes**: `id` (a unique identifier for the memory), `content` (the actual data or information stored in the memory), `timestamp` (the creation or recording time of the memory), and `metadata` (an optional dictionary for storing additional, searchable attributes about the memory).
    *   **Serialization Methods**: Includes `to_dict()` and `from_dict()` class methods for easy conversion to and from dictionary representations, which are essential for persistence and data exchange.
*   **`HAMRecallResult` Class**:
    *   Represents the structured outcome of a memory recall operation from HAM.
    *   **Attributes**: `memory_id` (the ID of the recalled memory), `content` (the retrieved memory data), `score` (a relevance or similarity score indicating how well the memory matched the query), `timestamp` (the original timestamp of the recalled memory), and `metadata` (the metadata associated with the original memory).
    *   **Serialization Methods**: Also includes `to_dict()` and `from_dict()` class methods for convenient data handling.
*   **`DialogueMemoryEntryMetadata` Class**:
    *   A comprehensive class designed for storing rich, detailed metadata specifically associated with dialogue-related memory entries. This allows for deep contextual understanding of conversational turns.
    *   **Attributes**: Includes fields such as `timestamp`, `speaker`, `dialogue_id`, `turn_id`, `language`, `sentiment`, `emotion` (a dictionary of emotional scores), `topic` (list of relevant topics), `keywords`, `summary`, `context_history` (list of previous turn IDs), `action_taken` (by the AI), `is_sensitive` (boolean flag), `source_module`, `external_references`, `user_feedback`, and `additional_metadata` for custom, extensible fields.
    *   **Serialization Methods**: Provides `to_dict()` and `from_dict()` methods for converting metadata objects to and from dictionaries.

## How it Works

This module primarily serves as a definition layer for data models. It does not contain any operational logic for memory management, storage, or retrieval itself. Instead, other HAM components (such as the `HAMMemoryManager` and its various storage backends) would import and utilize these classes to structure the data they store, retrieve, and process. The `to_dict()` and `from_dict()` methods are crucial for converting these structured objects to and from dictionary representations, which is often a necessary step for persistence in databases or transmission across different parts of the AI system.

## Integration with Other Modules

*   **`HAMMemoryManager`**: This is the primary consumer of these types, using them internally to manage the HAM's data, including storing new memories and returning recall results.
*   **`datetime`**: The standard Python library used for handling `timestamp` attributes within these data structures.
*   **Other AI Modules**: Various AI modules (e.g., `DialogueManager`, `EmotionSystem`, `PersonalityManager`) would populate the `DialogueMemoryEntryMetadata` with relevant information before storing conversational turns in HAM, enriching the memory context.

## Code Location

`src/core_ai/memory/ham_types.py`