# Knowledge Graph

## Overview

The Knowledge Graph component within the Unified-AI-Project is designed to represent and store the AI's understanding of the world in a structured, interconnected format. Unlike raw data storage, a knowledge graph captures relationships between entities, enabling more sophisticated reasoning, inference, and contextual understanding.

While there isn't a single `knowledge_graph.py` file containing a monolithic implementation, the concepts and data structures for the knowledge graph are defined and utilized across various modules, particularly within the `LearningManager` and `ContentAnalyzerModule`.

## Core Data Structures

The fundamental building blocks of the knowledge graph are defined in `src/core_ai/knowledge_graph/types.py`:

1.  **Entities (`KGEntity`)**:
    *   Represent nodes in the graph, corresponding to real-world objects, concepts, people, organizations, locations, etc.
    *   Each entity has a unique `id`, a `label` (human-readable name), a `type` (e.g., "PERSON", "ORG", "CONCEPT"), and `attributes` (e.g., character offsets in source text, conceptual status).

2.  **Relationships (`KGRelationship`)**:
    *   Represent the directed connections or predicates between entities.
    *   Each relationship links a `source_id` entity to a `target_id` entity with a specific `type` (e.g., "is_a", "works_for", a verb lemma).
    *   Relationships can also have `weight` (or confidence scores) and `attributes` (e.g., the pattern or rule that extracted them).

3.  **Knowledge Graph (`KnowledgeGraph`)**:
    *   A composite structure that holds a collection of `KGEntity` objects (as a dictionary mapped by ID) and a list of `KGRelationship` objects.
    *   Includes `metadata` about the graph itself, such as the length of the source text, the model used for processing, and entity/relationship counts.

## Role in the Unified-AI-Project

The knowledge graph serves several critical functions:

-   **Enhanced Understanding**: Provides a rich, semantic representation of information, allowing the AI to go beyond keyword matching to understand the meaning and context of data.
-   **Reasoning and Inference**: Enables the AI to perform logical deductions and infer new facts based on existing relationships in the graph.
-   **Contextual Awareness**: Helps the AI maintain a deeper understanding of the current conversation or task by linking new information to existing knowledge.
-   **Learning and Memory**: The `LearningManager` is responsible for integrating new facts and relationships into the knowledge graph, effectively building and refining Angela's understanding of the world.
-   **Content Analysis**: The `ContentAnalyzerModule` likely plays a role in extracting entities and relationships from raw text to populate the knowledge graph.

## Implementation Notes

While there isn't a single class named `KnowledgeGraph` that directly implements graph operations (like adding nodes/edges, querying paths), the `types.py` file provides the schema for how this knowledge is structured. The actual manipulation and querying of this graph data are likely handled by other modules that interact with the `HAMMemoryManager` (which stores these structured facts) and potentially specialized graph processing libraries.

## Code Location

`src/core_ai/knowledge_graph/types.py` (Data Structures)

(Actual graph manipulation logic is distributed across modules like `LearningManager` and `ContentAnalyzerModule`.)
