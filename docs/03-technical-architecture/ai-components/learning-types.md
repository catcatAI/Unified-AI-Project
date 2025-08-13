# Learning System Data Structures

## Overview

This document provides an overview of the data structures defined in `src/core_ai/learning/types.py`. This file is crucial for maintaining data consistency across the AI's learning architecture, providing standardized `TypedDict` definitions for facts and learned records.

## Purpose

The primary purpose of this module is to define clear, explicit data contracts for the information that flows through the AI's learning systems. By using these shared `TypedDict` structures, modules like the `FactExtractorModule`, `LearningManager`, and `HAMMemoryManager` can communicate with each other reliably, ensuring that data is structured, consistent, and type-checked.

## Key Data Structures

### Fact Extractor Types

These structures are primarily used by the `FactExtractorModule`.

*   **`ExtractedFact`**: This is the main data structure representing a single piece of information extracted from text.
    *   `fact_type` (str): The general category of the extracted fact (e.g., `user_preference`, `user_statement`).
    *   `content` (dict): A dictionary containing the specific details of the fact.
    *   `confidence` (float): A score from 0.0 to 1.0 representing the extractor's confidence in the accuracy of the extracted information.

*   **`UserPreferenceContent`**: A specialized `content` dictionary for facts related to user preferences (e.g., likes, dislikes).
    *   `category` (str): The category of the preference (e.g., "music", "food").
    *   `preference` (str): The specific preference (e.g., "rock", "sushi").
    *   `liked` (bool, optional): Whether the preference is positive or negative.

*   **`UserStatementContent`**: A specialized `content` dictionary for direct statements of fact about the user.
    *   `attribute` (str): The attribute being described (e.g., "name", "location").
    *   `value` (Any): The value of the attribute (e.g., "John Doe", "New York").

### Learning Manager Types

This structure is used by the `LearningManager` and stored in the `HAMMemoryManager`.

*   **`LearnedFactRecord`**: This is a comprehensive data structure for a fact that has been processed by the `LearningManager` and stored in long-term memory. It extends the basic extracted fact with rich metadata about its origin, history, and relationships to other memories.
    *   **Core Fields**: Includes the `fact_type`, `confidence`, and the original `source_text`.
    *   **Provenance Metadata**: Contains fields to track the source of the fact, such as `user_id`, `session_id`, and detailed HSP (Heterogeneous Service Protocol) information if the fact was received from another AI (`hsp_originator_ai_id`, `hsp_fact_id`, etc.).
    *   **Conflict and Resolution Metadata**: Includes fields like `supersedes_ham_records`, `conflicts_with_ham_records`, and `merged_from_ham_records` to track how the system resolves contradictory or duplicate information.
    *   **Semantic/Knowledge Graph Fields**: Contains fields like `hsp_semantic_subject`, `hsp_semantic_predicate`, and `hsp_semantic_object` to facilitate integration with a knowledge graph.

## How it Works

This file contains no executable logic. It solely consists of `TypedDict` definitions. Other Python modules import these types and use them as type hints for variables, function arguments, and return values. This allows static analysis tools like `mypy` to catch data consistency errors before runtime and provides developers with clear, self-documenting code.

## Integration with Other Modules

*   **`FactExtractorModule`**: The primary producer of `ExtractedFact` objects.
*   **`LearningManager`**: The primary consumer of `ExtractedFact` objects and the producer of `LearnedFactRecord` objects.
*   **`HAMMemoryManager`**: The system responsible for the persistent storage and retrieval of `LearnedFactRecord` objects.

## Code Location

`apps/backend/src/core_ai/learning/types.py`
