# KnowledgeGraphTypes: Data Structures for Knowledge Graph Representation

## Overview

This document provides an overview of the `types.py` module (`src/core_ai/knowledge_graph/types.py`), which defines the fundamental data structures for representing entities, relationships, and metadata within a knowledge graph.

## Purpose

The primary purpose of this module is to establish a standardized and type-hinted schema for building and interacting with a knowledge graph. This ensures consistency in how knowledge is represented across the AI system, making it easier for different AI components to share, process, and reason with structured information. It acts as a common language for knowledge representation.

## Key Responsibilities and Features

*   **`KGEntityAttributes`**: A `TypedDict` defining optional attributes that can be associated with a knowledge graph entity. Examples include `start_char`, `end_char` (for text spans), `is_conceptual` (indicating abstractness), `source_text`, and `rule_added` (for provenance).
*   **`KGEntity`**: A `TypedDict` representing a node in the knowledge graph. It includes:
    *   `id` (Required[str]): A unique identifier for the entity.
    *   `label` (Required[str]): The human-readable name of the entity.
    *   `type` (Required[str]): The category or class of the entity (e.g., "ORG" for organization, "PERSON", "GPE" for geopolitical entity, "LOC" for location, "CONCEPT").
    *   `attributes` (KGEntityAttributes): A dictionary for additional, optional attributes.
*   **`KGRelationshipAttributes`**: A `TypedDict` defining optional attributes for a knowledge graph relationship. Examples include `pattern` (the rule that extracted it), `trigger_token`, `trigger_text`, and `confidence`.
*   **`KGRelationship`**: A `TypedDict` representing an edge (connection) between two entities in the knowledge graph. It includes:
    *   `source_id` (Required[str]): The ID of the originating `KGEntity`.
    *   `target_id` (Required[str]): The ID of the destination `KGEntity`.
    *   `type` (Required[str]): The nature of the relationship (e.g., "is_a", "works_for", a verb lemma).
    *   `weight` (Optional[float]): An optional numerical value indicating the strength or confidence of the relationship.
    *   `attributes` (KGRelationshipAttributes): A dictionary for additional, optional attributes.
*   **`KnowledgeGraphMetadata`**: A `TypedDict` defining metadata about the knowledge graph instance itself. This includes `source_text_length`, `processed_with_model`, `entity_count`, and `relationship_count`.
*   **`KnowledgeGraph`**: The top-level `TypedDict` structure that encapsulates the entire knowledge graph. It contains a dictionary of `entities` (keyed by their IDs), a list of `relationships`, and `metadata` about the graph.

## How it Works

This module primarily defines the "blueprint" or schema for knowledge graph data. It does not contain any operational logic for building, storing, or querying a knowledge graph. Instead, other modules within the AI system (e.g., a `KnowledgeGraphManager`, `ContentAnalyzerModule`, or `FactExtractorModule`) would utilize these `TypedDict` definitions to ensure that the knowledge graph data they produce or consume conforms to the expected, standardized structure. This adherence to a common schema is vital for interoperability and maintainability.

## Integration with Other Modules

*   **`KnowledgeGraph` (Conceptual Module)**: A future or existing module that would implement the core logic for building, storing, and querying knowledge graphs, directly using these type definitions.
*   **`ContentAnalyzerModule`**: Could use these types to structure information extracted from various content sources.
*   **`FactExtractorModule`**: Would rely on these types to represent extracted facts and beliefs as entities and relationships.
*   **`typing`**: The standard Python library that provides `TypedDict` and other type-hinting utilities, which are fundamental to the definitions within this module.

## Code Location

`src/core_ai/knowledge_graph/types.py`