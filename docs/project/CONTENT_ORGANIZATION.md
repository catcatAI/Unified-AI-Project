# Unified-AI-Project: Content Organization

## Introduction

This document provides an organized overview of the Unified-AI-Project's content. Its purpose is to help contributors and users understand the project's structure, navigate the codebase and documentation, and locate relevant information efficiently.

The project structure and documentation are subject to ongoing evolution. This document describes the organization as of the last major documentation restructuring (July 10, 2024). For the most current status of individual components and features, please refer to the [Project Status Summary](STATUS_SUMMARY.md).

## 1. Top-Level Project Files

These files are located in the root directory of the project:

*   `README.md`: The main entry point for the project. Provides a general overview, setup instructions, contribution guidelines, and links to key documentation.
*   `.gitignore`: Specifies intentionally untracked files that Git should ignore.
*   `requirements.txt`: Lists Python dependencies required for the project.
*   `package.json`: Defines Node.js dependencies and scripts, primarily for the Electron application and other Node.js-based services or tools.
*   `.env.example`: An example environment variable file. Users should copy this to `.env` and fill in their specific configurations (e.g., API keys).
*   `babel.cfg`: Configuration file for Babel, used for internationalization (i18n) to extract translatable strings from Python source code.
*   Other configuration files (e.g., for linters, formatters, CI/CD) may also be present.

## 2. Source Code (`src/`)

The `src/` directory contains all the core Python source code for the AI, its services, tools, and interfaces. Key subdirectories include:

*   `agents/`: Contains specialized capability modules, such as `JulesDevelopmentCapability` for AI-assisted software development tasks. These are typically orchestrated by the core AI persona.
*   `core_ai/`: Houses the central intelligence and decision-making components of the AI, including dialogue management, memory (HAM), learning systems, personality, formula engine, and more.
*   `fragmenta/`: Home of the Fragmenta Orchestrator, a system designed for managing complex tasks and coordinating data flow between modules.
*   `hsp/`: Implements the Heterogeneous Synchronization Protocol (HSP) for inter-AI communication and collaboration.
*   `interfaces/`: Contains code for different user interaction points, such as the Command Line Interface (`cli/`) and the Electron desktop application (`electron_app/`).
*   `modules_fragmenta/`: Contains specialized processing modules that can be utilized by the Fragmenta system.
*   `services/`: Backend services, including the main API server (FastAPI), interfaces to Large Language Models (LLMs), AIVirtualInputService (AVIS), SandboxExecutor, and other utility services.
*   `shared/`: Common utilities, type definitions (`TypedDict`s), and constants used across different parts of the project.
*   `tools/`: Contains internal "tools" that the AI can use to augment its capabilities, such as mathematical tools, logical reasoners, or translation tools, along with their respective models or dispatchers.

Many modules within `src/` have their own `README.md` or `*_readme.md` files providing specific details about their functionality and usage.

## 3. Documentation (`docs/`)

The `docs/` directory is the central repository for all detailed design documents, specifications, guides, background information, and project management documentation.

### 3.1. `docs/project/`
Purpose: Contains project-level management, status, and organizational documents.
Key Files:
*   `STATUS_SUMMARY.md`: Summarizes the implementation status of various components, features, and conceptual goals. **This is a crucial document for understanding the current state of the project.**
*   `CONTENT_ORGANIZATION.md` (This file): Describes the organization of project content.
*   `MERGE_AND_RESTRUCTURE_PLAN.md`: Historical document detailing the initial project merge and restructuring strategy.
*   `TODO_PLACEHOLDERS.md`: Historical list of TODO items and placeholders identified in the codebase.

### 3.2. `docs/architecture/`
Purpose: Contains all documents related to the AI system's architecture and design.
*   **`docs/architecture/specifications/`**
    *   Purpose: Formal technical specification documents for core components, protocols, and capabilities.
    *   Key Files: `HSP_SPECIFICATION.md`, `Fragmenta_design_spec.md`, `HAM_design_spec.md`, `AI_Virtual_Input_System_spec.md`, `Linguistic_Immune_System_spec.md` (draft), `MetaFormulas_spec.md` (draft), `Jules_Development_Capability_spec.md`.
*   **`docs/architecture/blueprints/`**
    *   Purpose: Documents describing high-level architectural designs, core component compositions, overviews of systems, and significant architectural concepts.
    *   Key Files: `Core_Composition.md`, `DEEP_MAPPING_AND_PERSONALITY_SIMULATION.md`, `LLM_World_Model_Integration.md`, `MEMORY_SYSTEM.md`.
*   **`docs/architecture/advanced_concepts/`**
    *   Purpose: Collection of documents exploring more advanced, forward-looking, or specific technical/architectural concepts that might be experimental or in early stages of consideration.
    *   Key Files: `Self_Correction_Immune_System.md`, `Asynchronous_Reasoning.md`, `QR_Code_Like_Code.md`, `Self_Healing_Code_Cells.md`.

### 3.3. `docs/guides/`
Purpose: Provides practical guides, standards, and guidelines for development, usage, and contribution.
Key Files:
*   `INTERNAL_DATA_STANDARDS.md`: Standards for internal data structures (e.g., using `TypedDict`).
*   `TRANSLATION_GUIDE.md`: Guide for adding and managing translations (i18n).
*   `message_processing_guidelines.md`: Guidelines for how messages are processed within the system.

### 3.4. `docs/reference_and_analysis/`
Purpose: Contains background reference materials, comparative analyses, philosophical discussions, security considerations, and system analyses.
Key Files:
*   `Model_Taxonomy.md`: Classification of large models.
*   `Similar_Systems_Comparison.md`: Comparison with other AI systems.
*   `Potential_Project_Gaps.md`: Analysis of potential gaps in the project.
*   `AI_Brain_Analogy.md`: Philosophical exploration of AI using brain analogies.
*   `CC_vs_DDoS_Defense.md`: Discussion on security aspects.

### 3.5. `docs/archive/`
Purpose: For archived documents or meta-documentation about specific types of historical files.
Key Files:
*   `TXT_FILES_README.md`: Explains the nature, purpose, and reference value of the various `.txt` files (e.g., `1.0.txt`, `EX.txt`) found in the `docs/` directory, which often contain early conceptual and narrative explorations. Note: The `.txt` files themselves may still reside in the parent `docs/` directory or be moved here in the future.

## 4. Configuration (`configs/`)

This directory holds configuration files for the system, including:
*   System-wide settings (`system_config.yaml`).
*   API key templates/placeholders (`api_keys.yaml`).
*   AI personality profiles (`personality_profiles/`).
*   Formula engine rules (`formula_configs/`).
*   Ontology mappings (`ontology_mappings.yaml`).
*   Simulated hardware resources (`simulated_resources.yaml`).

## 5. Data (`data/`)

The `data/` directory is intended for various data used by or generated by the AI. This includes:
*   Raw datasets for training or knowledge ingestion.
*   Processed data.
*   Knowledge bases.
*   Chat histories.
*   Firebase related data.
Typically, large data files or sensitive data within this directory are excluded from version control via `.gitignore`, but the directory structure and example files might be included.

## 6. Scripts (`scripts/`)

Contains utility scripts for various tasks, such as:
*   Data processing and ingestion (e.g., `data_processing/`).
*   Project setup utilities (`project_setup_utils.py`).
*   Translation management (`translation_helper.py`).
*   Prototyping (`prototypes/`).

## 7. Tests (`tests/`)

This directory contains all automated tests for the project, including unit tests and integration tests. The structure within `tests/` generally mirrors the `src/` directory structure.

## How to Find Information

*   **Starting Point:** Begin with the main `README.md` (in the project root) for a general overview and setup instructions.
*   **Current Status:** Refer to `docs/project/STATUS_SUMMARY.md` for the latest on feature implementation and component status.
*   **Technical Details:** For in-depth technical specifications of core components and protocols, consult the documents in `docs/architecture/specifications/`.
*   **High-Level Design:** For architectural overviews and design principles, see `docs/architecture/blueprints/`.
*   **Development Guides:** Check `docs/guides/` for coding standards, translation processes, etc.
*   **Conceptual Background:** The `.txt` files (see `docs/archive/TXT_FILES_README.md`) and documents in `docs/reference_and_analysis/` provide context on the project's vision and advanced concepts.

## Contributing to Documentation

Clear, accurate, and up-to-date documentation is crucial. Contributions to improving the documentation are welcome. Please ensure that any significant changes to code or architecture are reflected in the relevant documents.
