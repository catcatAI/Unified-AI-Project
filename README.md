# Unified-AI-Project

## Overview

The **Unified-AI-Project** aims to create a versatile and intelligent conversational AI framework. It consolidates and enhances capabilities from previous projects like MikoAI, Fragmenta, and other CatAI initiatives. The primary goal is to build a modular, maintainable, and extensible system capable of rich dialogue, context understanding, learning, and tool usage.

For details on the initial project structure, merge strategy, and architectural principles that guided the consolidation, please refer to the [MERGE_AND_RESTRUCTURE_PLAN.md](MERGE_AND_RESTRUCTURE_PLAN.md).

## Key Features & Modules

This project integrates and is developing several core AI components:

*   **Dialogue Management (`src/core_ai/dialogue_manager.py`):** Orchestrates conversation flow, integrates with other AI components, and generates responses. It leverages personality profiles, memory systems, and formula-based logic.

*   **Personality Management (`src/core_ai/personality/personality_manager.py`):** Manages different AI personalities, influencing tone, response style, and core values. Profiles are configurable (see `configs/personality_profiles/`).

*   **Hierarchical Associative Memory (HAM) (`src/core_ai/memory/ham_memory_manager.py`):** A custom memory system designed for storing and retrieving experiences, learned facts, and dialogue context.

*   **Learning System (`src/core_ai/learning/`):**
    *   **Fact Extractor Module:** Extracts structured facts from dialogue.
    *   **Self-Critique Module:** Evaluates AI responses for quality and coherence.
    *   **Learning Manager:** Coordinates the learning process and storage of new knowledge into HAM.
    *   **Content Analyzer Module (New - In Development):**
        *   **Purpose:** Aims to achieve deep context understanding by analyzing text content (e.g., from documents, user inputs) to create a structured knowledge graph.
        *   **Functionality:** Extracts named entities and identifies relationships between them.
        *   **Technologies:** Utilizes `spaCy` for Natural Language Processing tasks (NER, dependency parsing) and `NetworkX` for constructing and representing the knowledge graph.
        *   **Status:** A prototype (Phase 2) is complete, capable of generating a NetworkX knowledge graph with initial entity and rule-based relationship extraction. Further development will focus on refining extraction techniques and integrating this graph into the `DialogueManager` for richer contextual awareness.

*   **Formula Engine (`src/core_ai/formula_engine/`):** Implements a rule-based system where predefined "formulas" (see `configs/formula_configs/`) can trigger specific actions or responses based on input conditions. This allows for deterministic behaviors and tool dispatch.

*   **Tool Dispatcher (`src/tools/tool_dispatcher.py`):** Enables the AI to use external or internal "tools" (e.g., calculators, information retrieval functions) to augment its capabilities. Tools can be triggered by the Formula Engine or other AI logic.

*   **LLM Interface (`src/services/llm_interface.py`):** Provides a standardized interface to interact with various Large Language Models (e.g., Ollama, OpenAI), managing API calls and model configurations.

*   **Configuration System (`configs/`):** Centralized YAML and JSON files for system behavior, personality profiles, API keys, formulas, etc.

## Getting Started

(To be added: Instructions on setup, running the application/API, key scripts.)

## Contributing

(To be added: Guidelines for contributing to the project.)