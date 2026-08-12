# ContentAnalyzerModule: Knowledge Graph Construction and Text Analysis

## Overview

This document provides an overview of the `ContentAnalyzerModule` (`src/core_ai/learning/content_analyzer_module.py`). This module is designed to analyze text content to extract entities and relationships, constructing both a structured `KnowledgeGraph` TypedDict and a NetworkX `DiGraph`. It also processes `HSPFactPayload` objects and integrates their content into its evolving knowledge graph.

## Purpose

The primary purpose of the `ContentAnalyzerModule` is to build and maintain a structured understanding of information derived from various text sources, including natural language statements and structured facts. This knowledge graph serves as a foundational component for the AI's reasoning, memory, and continuous learning capabilities, enabling it to make more informed decisions and generate more contextually relevant responses.

## Key Responsibilities and Features

*   **Entity Extraction (`_extract_entities`)**:
    *   Leverages spaCy's powerful Named Entity Recognition (NER) capabilities to identify and categorize entities (e.g., PERSON, ORG, GPE, LOC).
    *   Includes rule-based augmentation to identify specific known entities that might be missed by general NER models, enhancing precision.
*   **Relationship Extraction (`_extract_relationships_prototype`, `_extract_relationships_with_matcher`)**:
    *   Employs dependency parsing heuristics to identify fundamental relationships such as Subject-Verb-Object (SVO) and "is_a" relationships.
    *   Extracts relationships from prepositional phrases (e.g., "located in", "works for").
    *   Identifies possessive relationships (e.g., "Google's CEO").
    *   Utilizes spaCy's `Matcher` with predefined patterns to identify and extract specific, complex relationship types with higher confidence.
*   **Knowledge Graph Construction (`analyze_content`)**:
    *   Takes raw text content as input.
    *   Outputs two representations of the extracted knowledge: a `KnowledgeGraph` TypedDict (a structured, serializable representation of entities, relationships, and metadata) and a NetworkX `DiGraph` (a graph data structure optimized for traversal, querying, and graph algorithms).
*   **HSP Fact Processing (`process_hsp_fact_content`)**:
    *   Designed to process `HSPFactPayload` objects, which can contain either natural language statements or pre-structured semantic triples.
    *   If a natural language statement is provided, it re-analyzes the text and merges the newly extracted knowledge into the module's internal NetworkX graph.
    *   If a structured semantic triple is provided, it directly integrates it into the graph, applying ontology mappings for standardization.
    *   Updates the internal NetworkX graph (`self.graph`) directly, ensuring the knowledge base is always current.
*   **Ontology Mapping**: Loads and applies ontology mappings from a YAML configuration file (`configs/ontology_mappings.yaml`). This feature is crucial for normalizing and standardizing entity types and relationship types across different data sources, ensuring a coherent knowledge representation.
*   **SpaCy Integration**: Heavily relies on the spaCy library for various natural language processing tasks, including tokenization, part-of-speech tagging, named entity recognition, and dependency parsing, which are foundational for its analytical capabilities.

## How it Works

The `ContentAnalyzerModule` processes incoming text by first performing named entity recognition using spaCy. Subsequently, it identifies relationships between these entities through a combination of dependency parsing heuristics and carefully defined spaCy `Matcher` patterns. The extracted information is then used to populate both a structured `KnowledgeGraph` object and a NetworkX graph. The module can also ingest pre-structured facts from `HSPFactPayload` objects, merging them into its existing knowledge base and applying ontology mappings to maintain consistency.

## Integration with Other Modules

*   **`spacy`**: The core NLP library providing the foundational text analysis capabilities.
*   **`networkx`**: Used for representing and manipulating the knowledge graph as a graph data structure, enabling graph-based queries and algorithms.
*   **Knowledge Graph Type Definitions**: Relies on `KGEntity`, `KGRelationship`, and `KnowledgeGraph` TypedDicts (from `src.core_ai.knowledge_graph.types`) to ensure data consistency and type safety.
*   **`HSPFactPayload`**: Consumes structured fact data defined by `hsp.types`.
*   **`ontology_mappings.yaml`**: A configuration file that defines how various terms and concepts map to standardized ontology elements.
*   **`LearningManager`**: This module could be a key component used by the `LearningManager` to extract and integrate knowledge from diverse sources for continuous learning and knowledge base expansion.

## Code Location

`src/core_ai/learning/content_analyzer_module.py`