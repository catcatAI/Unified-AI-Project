# Unified-AI-Project: Content Organization

## Introduction

This document provides an organized overview of the Unified-AI-Project's content, categorizing key directories and files to aid in understanding the project's structure and the purpose of its various components. This is based on the file structure available as of July 8, 2024.

## 1. Root Directory Files

Key files at the project root:

*   `README.md`: Main entry point for project information, overview, setup, and contribution guidelines.
*   `MERGE_AND_RESTRUCTURE_PLAN.md`: Documents the initial project structure, merge strategy, and architectural principles.
*   `.gitignore`: Specifies intentionally untracked files that Git should ignore.
*   `requirements.txt`: Lists Python dependencies for the project.
*   `package.json`: Defines Node.js dependencies and scripts for the project (e.g., for Electron app).
*   `.env.example`: Example environment variable file; a `.env` file should be created from this for local configuration.

## 2. Source Code (`src/`)

Contains the core Python source code for the AI and its services.

*   `core_services.py`: Provides central initialization (dependency injection) and access to core AI service instances. Responsible for instantiating and wiring together major components like DialogueManager, Memory, LLMInterface, etc.

### 2.1. Agents (`src/agents/`)

Hosts implementations or placeholders for various AI agents.
*   `simple_coding_agent.py`: A basic scripted agent for testing AVIS code execution.
*   `jules_dev_agent.py`: Placeholder for the Jules Asynchronous Development Agent.

### 2.1.1. Core AI Logic and Modules (`src/core_ai/`)

Houses the central intelligence and decision-making components of the AI.

*   **`dialogue/`**:
*   `dialogue/dialogue_manager.py`: Orchestrates conversation flow, integrates various AI components, and generates responses.
*   **`memory/`**:
    *   `ham_memory_manager.py`: Implements the Hierarchical Associative Memory for storing and retrieving experiences, learned facts, and dialogue context.
*   **`learning/`**:
    *   `learning_manager.py`: Coordinates the learning process, including fact extraction and storage.
    *   `fact_extractor_module.py`: Extracts structured facts from dialogue.
    *   `self_critique_module.py`: Evaluates AI responses for quality and coherence.
    *   `content_analyzer_module.py`: Aims for deep context understanding by analyzing text to create knowledge graphs (utilizes spaCy and NetworkX).
*   **`personality/`**:
    *   `personality_manager.py`: Manages different AI personalities and their profiles.
*   **`formula_engine/`**: Contains the logic for the rule-based formula engine that can trigger actions or responses.
*   **`code_understanding/`**:
    *   `lightweight_code_model.py`: Provides basic static analysis of Python code, particularly for understanding tool structures.
*   **`service_discovery/`**:
    *   `service_discovery_module.py`: Contains a service discovery implementation. **Note:** Its current code defines a generic service registry with TTL-based expiry and its own `ServiceAdvertisement` type. This differs from the HSP-specific capability discovery mechanism (expected to handle `HSPCapabilityAdvertisementPayload`, integrate with `TrustManager`, and have a `process_capability_advertisement` method) that is anticipated by `core_services.py` for HSP integration. This module requires refactoring or replacement to fulfill the HSP-related role.
*   **`trust_manager/`**:
    *   `trust_manager_module.py`: Manages trust scores for interactions with other AI peers in the HSP network.
*   **`lis/`**: Contains early placeholders (`lis_cache_interface.py`) for the Linguistic Immune System (LIS), a conceptual system for advanced error processing and linguistic evolution (see `docs/architecture/Linguistic_Immune_System_spec.md`).
*   `emotion_system.py`: Manages and simulates the AI's emotional state.
*   `crisis_system.py`: Assesses input for crisis situations and can trigger appropriate responses.
*   `time_system.py`: Provides time-related context (e.g., time of day).

### 2.2. Heterogeneous Synchronization Protocol (`src/hsp/`)

Defines the protocol and connector for inter-AI communication.

*   `connector.py`: Manages MQTT-based communication with the HSP network, handles message serialization/deserialization, and implements features like automatic reconnection and ACK sending.
*   `types.py`: Defines `TypedDict` structures for various HSP message envelopes and payloads.

### 2.3. Tools (`src/tools/`)

Contains internal "tools" that the AI can use to augment its capabilities.

*   `tool_dispatcher.py`: Enables the AI to select and use various tools.
*   `math_tool.py`, `logic_tool.py`, `translation_tool.py`: Example or actual implementations of specific tools.
*   `code_understanding_tool.py`: A callable tool providing code understanding capabilities.
*   Subdirectories like `math_model/`, `logic_model/`, `translation_model/` likely contain machine learning models or data related to these tools.
*   `js_tool_dispatcher/`: Appears to be for dispatching tools implemented in JavaScript.

### 2.4. Fragmenta Meta-Orchestration (`src/fragmenta/` and `src/modules_fragmenta/`)

System for managing complex tasks and large data.

*   `fragmenta/fragmenta_orchestrator.py`: Placeholder and basic implementation for the system that will manage complex tasks, chunk data, and coordinate modules.
*   `modules_fragmenta/`: Contains specialized processing modules potentially used by Fragmenta:
    *   `element_layer.py`: Placeholder for processing data at an elemental level.
    *   `vision_tone_inverter.py`: Placeholder for adjusting visual representations based on tone.

### 2.5. Services (`src/services/`)

Backend services, including API servers and interfaces to external systems.

*   `main_api_server.py`: FastAPI application providing API endpoints for interacting with the AI.
*   `llm_interface.py`: Standardized interface for interacting with various Large Language Models (e.g., Ollama, OpenAI).
*   `sandbox_executor.py`: For safely executing code, likely used in tool drafting or other dynamic code execution scenarios.
*   `audio_service.py`, `vision_service.py`: Placeholders or implementations for audio and vision processing capabilities.
*   `resource_awareness_service.py`: Manages and provides information about the AI's simulated hardware resources, configured via `configs/simulated_resources.yaml`.
*   `ai_virtual_input_service.py`: Implements the AI Virtual Input Service (AVIS) for simulated GUI interaction (e.g., virtual mouse/keyboard). (See `docs/architecture/AI_Virtual_Input_System_spec.md`).
*   `node_services/`: Contains a Node.js server, possibly for supporting JavaScript-based tools or UI backend components.
*   `api_models.py`: Defines Pydantic models for API request/response validation.

### 2.6. Shared Utilities (`src/shared/`)

Common utilities, types, and configurations used across different parts of the project.

*   `types/common_types.py`: Central repository for common `TypedDict` data structures used for internal data exchange.
*   Likely contains other shared helper functions or constants.

### 2.7. User Interfaces (Implementations) (`src/interfaces/`)

Code for different ways users can interact with the AI.

*   **`cli/`**:
    *   `main.py`: Implementation for the Command Line Interface (CLI).
*   **`electron_app/`**: Contains the source code for the Electron-based desktop application (HTML, CSS, JavaScript for frontend; `main.js` for Electron main process, `preload.js` for context bridge, `renderer.js` for frontend logic).

## 3. Documentation (`docs/`)

Contains project documentation, design specifications, and architectural notes.

*   `README.md` (in root, but effectively project documentation)
*   `HSP_SPECIFICATION.md`: Detailed specification for the Heterogeneous Synchronization Protocol.
*   `INTERNAL_DATA_STANDARDS.md`: Guidelines for using `TypedDict` for internal data structures.
*   `PROJECT_STATUS_SUMMARY.md`: This document, summarizing implemented vs. pending features.
*   `PROJECT_CONTENT_ORGANIZATION.md`: This document, providing an overview of file organization.
*   **`architecture/`**: Subdirectory for more detailed architectural documents:
    *   `DEEP_MAPPING_AND_PERSONALITY_SIMULATION.md`: Discussion on advanced data mapping and personality concepts. Contains an important clarification regarding a previous misinterpretation of "XXX" substrings in HAM data.
    *   `ENHANCED_DECOUPLING_STRATEGIES.md`: Identifies areas and strategies for improving module decoupling.
    *   `Fragmenta_design_spec.md`: Design specification for the Fragmenta meta-orchestration system.
    *   `HAM_design_spec.md`: Design specification for the Hierarchical Associative Memory.
    *   `Heterogeneous_Protocol_spec.md`: Conceptual design for the "AI Heterogeneous Architecture Protocol (AHAP)" (v0.1), distinct from HSP, aimed at transferring AI characteristics (personality, roles) between MikoAI and external AI systems. Its implementation status is conceptual.
    *   `MEMORY_SYSTEM.md`: Brief overview of the HAM memory system, pointing to the detailed `HAM_design_spec.md`.
*   **`conceptual_agents/`**: Subdirectory for design specifications of conceptual AI agents.
    *   `Jules_Async_Development_Agent_spec.md`: Design specification for the Jules agent.
    *   `SimpleLoginAgent_with_AVIS.md`: Design for a simple agent using AVIS for login simulation.
*   `1.0.txt`, `1.0en.txt`: Stylized, narrative/philosophical texts discussing AI evolution concepts, internal project metaphors (e.g., "Angela", "Fragmenta" as entities), and potential future ideas. Their content is more conceptual and brainstorming-oriented than formal technical specification.

## 4. Configuration Files (`configs/`)

Centralized configuration for various aspects of the AI system.

*   `system_config.yaml`: General system-wide configurations.
*   `api_keys.yaml`: Structure and placeholders for external API keys (actual keys typically via `.env`).
*   `ontology_mappings.yaml`: Mappings for ontologies, likely used by `ContentAnalyzerModule`.
*   `simulated_resources.yaml`: Defines profiles for simulated hardware resources, used by the `ResourceAwarenessService`.
*   `version_manifest.json`: Manages versions of different components or data schemas.
*   **`formula_configs/`**:
    *   `default_formulas.json`: Defines rules for the Formula Engine.
*   **`personality_profiles/`**:
    *   `miko_base.json`: Base personality profile for an AI instance. Other JSON files would define different personalities.

## 5. Test Suites (`tests/`)

Contains unit and integration tests for the project. The directory structure generally mirrors `src/`.

*   `tests/core_ai/`: Tests for core AI components (dialogue, memory, learning, etc.).
    *   `memory/test_ham_memory_manager.py`: Tests for HAM.
    *   `dialogue/test_dialogue_manager.py`: Tests for Dialogue Manager.
*   `tests/fragmenta/`: Tests for Fragmenta.
*   `tests/hsp/`: Tests for HSP components.
*   `tests/services/`: Tests for backend services.
*   `tests/tools/`: Tests for AI tools.
*   ... and so on for other modules.

## 6. Scripts (`scripts/`)

Utility scripts for various tasks like data processing, setup, or prototyping.

*   **`data_processing/`**:
    *   `ingest_processed_logs_to_ham.py`: Script to ingest processed log data into HAM.
    *   `process_copilot_logs.py`: Script to process Copilot activity logs.
*   **`data_migration/`**: Placeholder for data migration scripts.
*   **`prototypes/`**: Contains prototype code, e.g., `miko_core_ham_prototype.py`.
*   `project_setup_utils.py`: Utilities for project setup.
*   `mock_hsp_peer.py`: A script to mock an HSP peer for testing communication.

## 7. Data Storage (`data/`)

Contains various data used by or generated by the AI. This directory is typically in `.gitignore` for large datasets or sensitive information but contains subdirectories for different data types.

*   **`chat_histories/`**: Stores chat logs (e.g., `ollama_chat_histories.json`).
*   **`firebase/`**: Configuration files related to Firebase integration.
*   **`knowledge_bases/`**: Stores structured knowledge data (e.g., emotion maps, personality definitions, formulas).
*   **`processed_data/`**: For data that has been processed from raw sources, including HAM memory files (e.g., `dialogue_context_memory.json`).
*   **`raw_datasets/`**: For raw input data before processing.

This organization should help in navigating the project and understanding where different functionalities reside.
