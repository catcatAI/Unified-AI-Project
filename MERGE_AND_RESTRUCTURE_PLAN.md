```markdown
# MikoAI & Fragmenta Project Merge and Restructure Plan

## 1. Introduction and Rationale

This document outlines the plan to merge the MikoAI, Fragmenta, and various related CatAI projects into a single, unified codebase: `Unified-AI-Project/`.

**Goals:**

*   **Reduce Redundancy:** Consolidate multiple disparate project folders containing similar or overlapping functionalities.
*   **Improve Clarity:** Establish a clear, logical, and well-documented project structure.
*   **Enhance Maintainability:** Make the codebase easier to understand, manage, and extend.
*   **Leverage Fragmenta Architecture:** Organize the merged project according to the modular and data-flow principles of the Fragmenta architecture.
*   **Data Lifecycle Organization:** Structure the project to clearly reflect how data is created, read, modified, stored, and deleted.

The current state involves numerous scattered folders, making it difficult to get a holistic view of the project, identify canonical versions of modules, and manage dependencies. This restructure aims to address these challenges.

## 2. Guiding Architectural Principles

*   **Fragmenta Influence:** The new structure will be heavily inspired by Fragmenta's modular design, emphasizing clear separation of concerns for:
    *   Core AI Logic
    *   Services (APIs, external communications)
    *   Interfaces (Electron App, CLI)
    *   Shared Utilities
    *   Data Management
    *   Configuration
    *   Fragmenta-specific "tone" processing modules.
*   **Data Lifecycle Focus:** Directories and module responsibilities will be organized around the lifecycle of data:
    *   **Creation:** Where new data (user inputs, AI responses, logs, learned knowledge) originates.
    *   **Reading:** Accessing configurations, datasets, existing knowledge, and context.
    *   **Modification/Processing:** Transforming data, applying AI logic, updating states.
    *   **Storage/Deletion:** How and where data is persisted and eventually removed.
*   **Modularity & Reusability:** Core functionalities will be encapsulated in well-defined modules to promote reuse and independent development.

## 3. Proposed Merged Project Structure (`Unified-AI-Project/`)

```
Unified-AI-Project/
├── .env.example                # Example environment variables
├── .gitignore
├── README.md                   # Main project README
├── MERGE_AND_RESTRUCTURE_PLAN.md # This document
├── package.json                # For top-level Node.js dependencies
├── requirements.txt            # For Python dependencies

├── configs/                    # Centralized configurations
│   ├── system_config.yaml
│   ├── api_keys.yaml
│   ├── personality_profiles/
│   │   └── miko_base.json
│   ├── formula_configs/
│   │   └── default_formulas.json
│   └── version_manifest.json

├── data/                       # All project data
│   ├── raw_datasets/
│   ├── processed_data/
│   ├── knowledge_bases/
│   ├── chat_histories/
│   ├── logs/
│   ├── models/
│   ├── firebase/
│   │   ├── firestore.rules
│   │   └── firestore.indexes.json
│   └── temp/

├── src/                        # Source code
│   ├── core_ai/                # Core AI logic (Python)
│   │   ├── personality/
│   │   ├── memory/
│   │   ├── dialogue/
│   │   ├── learning/
│   │   ├── formula_engine/
│   │   ├── emotion_system.py
│   │   ├── time_system.py
│   │   └── crisis_system.py
│   ├── services/               # Backend services (Python APIs, Node.js services)
│   │   ├── main_api_server.py
│   │   ├── llm_interface.py
│   │   ├── audio_service.py
│   │   ├── vision_service.py
│   │   └── node_services/
│   │       ├── package.json
│   │       └── server.js
│   ├── tools/                  # Tool dispatcher and individual tools
│   │   ├── tool_dispatcher.py
│   │   └── js_tool_dispatcher/
│   │       ├── index.js
│   │       └── tool_registry.json
│   ├── interfaces/             # User/system interaction points
│   │   ├── electron_app/       # Main Electron Application
│   │   │   ├── main.js
│   │   │   ├── preload.js
│   │   │   ├── package.json
│   │   │   ├── src/
│   │   │   └── config/
│   │   └── cli/
│   │       └── main.py
│   ├── shared/                 # Shared utilities, constants, types (Python & JS)
│   │   ├── js/
│   │   └── types/
│   └── modules_fragmenta/      # Fragmenta-specific "tone" processing modules (JS or Python)
│       ├── element_layer.js    # Or .py
│       └── vision_tone_inverter.js # Or .py

├── scripts/                    # Utility and maintenance scripts
│   ├── project_setup_utils.py  # Adapted from restructure_phase1.py for setup
│   └── data_migration/
└── tests/                      # All tests
```

*(A more detailed breakdown of `src/` subdirectories is in the planning phase for "Develop a Merged Project Structure")*

## 4. Merge Process Execution Plan

The merge will be executed in phases:

**Note on Current Merge Scope:** As detailed in Section 8 ("Post-Merge Status Update and Current Strategy"), the immediate merging of several feature branches originally anticipated as part of the "Code Migration" and subsequent phases has been deferred due to persistent environmental limitations and a strategic decision to stabilize the current codebase. The following execution plan, therefore, describes the original intent, and ongoing work will focus on leveraging the successfully integrated components while deferring the integration of the specifically listed problematic branches until further notice.

1.  **Initial Setup:**
    *   Create the `Unified-AI-Project/` root directory and the basic top-level directory structure (`configs`, `data`, `src`, `scripts`, `tests`).
    *   Initialize a new `README.md` (briefly pointing to this plan) and `.gitignore` (merged from existing projects).
    *   Initialize `package.json` (for Electron/Node scripts) and `requirements.txt` (for Python).
    *   Adapt the directory creation logic from `MikoAI-Project-Codebase/scripts/restructure_phase1.py` into a new utility script `scripts/project_setup_utils.py` to help automate the creation of the detailed internal structure of `src/`.
    *   Implement a backup function in `project_setup_utils.py`, inspired by `restructure_phase1.py`, to backup key source directories before migration.

2.  **Configuration Migration:**
    *   Identify canonical configuration files from `MikoAI-Project-Codebase/`, `Fragmenta/`, and other sources.
    *   Merge these into the new `Unified-AI-Project/configs/` structure as defined.
    *   Create a comprehensive `.env.example`.

3.  **Data Migration:**
    *   Consolidate all identified data files (JSON, YAML, TXT datasets, rules) into the appropriate subdirectories under `Unified-AI-Project/data/`.
    *   Handle duplicates by manual inspection, merging, or choosing the most relevant version.

4.  **Code Migration (Iterative by Module/Component):**
    *   **Core AI Logic (`src/core_ai/`):**
        *   Migrate Python modules for personality, memory, dialogue, learning, formula engine, emotion, time, and crisis systems from `MikoAI-Project-Codebase/modules/`, `MikoAI-Project-Codebase/src/core/`, `CatAI-MikoAI-Project/shared/`, and `LingCat/`.
        *   **Conflict Resolution:** For modules with multiple sources (e.g., `personality_module.py`), prioritize the version from `MikoAI-Project-Codebase`, then diff and merge unique, valuable logic from other versions.
        *   **Ongoing Development (Post-Merge):** New core AI modules are being developed within this structure. For example, the `src/core_ai/learning/` directory now includes a `ContentAnalyzerModule` focused on deep context understanding through knowledge graph creation using `spaCy` and `NetworkX`. This reflects the project's evolution beyond simple migration.
    *   **Services (`src/services/`):**
        *   Migrate Python API server code from `MikoAI-Project-Codebase/src/api/`.
        *   Migrate LLM, audio, and vision service wrappers.
        *   If necessary, migrate specific Node.js backend services (e.g., from `ollama/` or `CatAI_Archive/catAIpc/`) into `src/services/node_services/`.
    *   **Tools (`src/tools/`):**
        *   Migrate Python tool dispatcher from `MikoAI-Project-Codebase/modules/`.
        *   Migrate JS tool dispatcher from `MikoAI-Project-Codebase/src/core/tool_dispatcher/`.
        *   Merge `tool_registry.json` from all relevant sources.
    *   **Interfaces (`src/interfaces/`):**
        *   **Electron App:** This is a significant integration. Start with the most complete Electron app version (likely from `MikoAI-Project-Codebase/src/interfaces/electron_app/` or `src/versions/miko-v3/`, which itself was a result of prior merges). Integrate UI elements or specific functionalities from `Fragmenta/frontend/` and `mikage_rei_electron/` if they offer distinct advantages.
        *   **CLI:** Adapt `MikoAI-Project-Codebase/main.py` if it serves as a CLI.
    *   **Shared Utilities (`src/shared/`):**
        *   Collect and consolidate utility functions and type definitions from all projects.
    *   **Fragmenta Modules (`src/modules_fragmenta/`):**
        *   Migrate modules from `Fragmenta/modules/` and relevant parts of `Fragmenta/shared/` (like `vision_tone_inverter.js`, `tone_analyzer.js`).
        *   Initially, these will likely remain as JavaScript modules. Future work might involve translating critical parts to Python for tighter integration if beneficial.

5.  **Path Resolution and Basic Integration:**
    *   Systematically update all import paths and file references within the migrated code to reflect the new structure. This will be a major task.
    *   Ensure basic module interactions are functional (e.g., core AI modules can be imported by services).

6.  **Testing and Refinement:**
    *   Migrate existing tests into the `Unified-AI-Project/tests/` directory, updating paths.
    *   Run tests and begin debugging runtime errors.
    *   Refine the structure and code as integration challenges arise.

## 5. Role of the Chosen "Tool" (`restructure_phase1.py` logic)

The script `MikoAI-Project-Codebase/scripts/restructure_phase1.py` will not be run directly. Instead, its useful components will be adapted:

*   **Directory Creation Logic (`_create_directories` method):** This logic will be extracted and modified within a new script (`scripts/project_setup_utils.py`) to automate the creation of the more complex `Unified-AI-Project` directory tree. This ensures consistency and saves manual effort.
*   **Backup Logic (`create_backup` method):** This function will be incorporated into `scripts/project_setup_utils.py` to provide a safety net before significant file operations begin during the migration.
*   **Boilerplate Code Reference:** The way `restructure_phase1.py` generates skeleton JavaScript classes for modules, interfaces, config managers, and loggers serves as a valuable reference for structuring new JS components or for understanding the intended architecture of some of the MikoAI JS parts.

This approach leverages existing automation while adapting it to the specific needs of this larger merge.

## 6. Application of Fragmenta Architecture

The Fragmenta architecture's principles are applied as follows:

*   **Modularity:** The `src/` directory is divided into `core_ai`, `services`, `tools`, `interfaces`, `shared`, and `modules_fragmenta`, reflecting Fragmenta's separation of concerns.
*   **Layered Processing:** The `modules_fragmenta/` directory is specifically reserved for Fragmenta's unique layered "tone" processing. `core_ai` also implies layered processing for general AI tasks.
*   **Data Flow:**
    *   **Input:** Handled by `interfaces` (Electron, CLI) and `services` (APIs).
    *   **Processing:** Occurs in `core_ai`, `services` (for request handling), `tools`, and `modules_fragmenta`.
    *   **Output:** Delivered through `interfaces` and `services`.
    *   **Configuration:** Centralized in `configs/`, influencing all processing stages, similar to Fragmenta's `configs/config.yaml`.
    *   **Data Storage & Management:** Centralized in `data/`, analogous to Fragmenta's `data/` directory (though our `data/` is more comprehensive).
*   **Shared Components:** The `shared/` directory mirrors Fragmenta's `shared/` for common utilities and types.
*   **Frontend/Backend Separation:** The `interfaces/electron_app/` (frontend) and `services/` (backend APIs) maintain a clear distinction, as seen in Fragmenta.

## 7. Potential Challenges

*   **Resolving Code Conflicts:** Merging different versions of the same module (e.g., multiple `personality_module.py` files) will require careful diffing and logical integration.
*   **Path Hell:** Updating all internal imports and file references will be time-consuming and error-prone.
*   **Dependency Management:** Consolidating Python (`requirements.txt`) and Node.js (`package.json`) dependencies from many projects might lead to version conflicts.
*   **Python vs. JavaScript Integration:** Deciding how Python and JavaScript components will interact (e.g., Python calling JS tools or Fragmenta modules) will need clear patterns.
*   **Testing:** Ensuring the merged codebase is stable and all functionalities are preserved will require extensive testing.

This plan provides a roadmap for the merge. Flexibility will be needed as unforeseen issues arise.

## 8. Post-Merge Status Update and Current Strategy

Subsequent attempts to merge a broader set of feature branches into the `master` branch (which had incorporated `feat/add-personality-profile-types` leading to commit `2c39060`) encountered significant sandbox environment limitations. 

Specifically, the following branches could not be checked out or merged due to errors related to processing large file counts or sizes within the sandbox:
*   `feat/initial-project-setup`
*   `feat/initial-project-structure`
*   `feat/data-migration`
*   `feat/config-migration`
*   `feat/integrate-config-management`
*   `refactor/electron-app-reloc-deps`
*   `feature/initial-setup-and-fixes`
*   `Jules`

Only `feat/add-personality-profile-types` (already part of `master` at `2c39060`) and `feat/consolidate-project-structure` were successfully processed locally in this session. However, attempts to push the `master` branch even with just `feat/add-personality-profile-types` (which was already part of the base `master` for this session's work) and a subsequent local merge of `feat/consolidate-project-structure` also faced push failures (timeout or other sandbox errors).

As a result, the `Unified-AI-Project` on the remote `master` does not reflect the full integration of all initially intended feature branches. **Current Strategy Update:** Based on these persistent challenges and a decision to prioritize stability and focused development on the currently integrated codebase, the merging and integration efforts for the specifically listed problematic branches:
*   `feat/initial-project-setup`
*   `feat/initial-project-structure`
*   `feat/data-migration`
*   `feat/config-migration`
*   `feat/integrate-config-management`
*   `refactor/electron-app-reloc-deps`
*   `feature/initial-setup-and-fixes`
*   `Jules`
are **on hold indefinitely**. These branches will not be merged into the main codebase at this time. Future development will proceed based on the current state of the `master` branch, which incorporates `feat/add-personality-profile-types` and `feat/consolidate-project-structure`. This is the current "latest status" and accepted state of the project's structure regarding these branches. Any future consideration to integrate functionalities from these deferred branches will require a new assessment and plan.
```
