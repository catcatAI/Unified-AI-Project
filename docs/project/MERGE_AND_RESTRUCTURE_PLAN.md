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

## Phase 2 Development Highlights (Post-Initial Merge)

Following the initial structural merge, Phase 2 focused on significant feature development, primarily around inter-AI communication and knowledge management:

*   **Heterogeneous Synchronization Protocol (HSP) Implementation:**
    *   Designed and implemented core HSP functionalities (`src/hsp/`), including message envelopes and payloads for Facts, Capability Advertisements, Task Requests/Results.
    *   Integrated `paho-mqtt` for MQTT transport via the `HSPConnector` service.
    *   Enabled `LearningManager` to publish facts and process incoming facts via HSP.
    *   Developed `ServiceDiscoveryModule` and integrated task brokering capabilities into `DialogueManager` for HSP-based task offloading.
    *   Implemented basic `TrustManager` to influence fact processing and capability selection.
    *   Exposed HSP functionalities (service listing, task initiation/polling) via the FastAPI server and integrated basic UI elements in the Electron app.

*   **Advanced Conflict Resolution for HSP Facts:**
    *   Enhanced `LearningManager` to handle conflicting facts received via HSP.
    *   Implemented Type 1 (same fact ID) and Type 2 (semantic: same subject/predicate, different value) conflict detection.
    *   Developed resolution strategies including:
        *   Superseding based on confidence.
        *   Trust/recency-based tie-breaking.
        *   Numerical value merging (PoC).
        *   Logging of unresolved contradictions.
    *   `ContentAnalyzerModule` was updated to provide semantic identifiers used in Type 2 conflict detection.

*   **Semantic Processing and Knowledge Graph:**
    *   `ContentAnalyzerModule` further developed to process structured HSP facts (semantic triples) and integrate them into its internal knowledge graph, including basic ontology mapping from `configs/ontology_mappings.yaml`.

These Phase 2 developments significantly expand the AI's ability to interact with peers and manage knowledge more intelligently.

## 8. Post-Merge Status Update (Reflecting Current Understanding)

**Critical Note on Merge Integration:** The initial merge plan encountered significant obstacles during execution, primarily due to sandbox environment limitations (e.g., errors related to processing large file counts or sizes, timeouts during push operations).

**Observed Outcomes from Prior Merge Attempts:**
*   Most of the foundational feature branches, crucial for establishing the complete project structure and migrating core components, **could not be successfully merged into the `master` branch.** These include (but are not limited to):
    *   `feat/initial-project-setup`
    *   `feat/initial-project-structure`
    *   `feat/data-migration`
    *   `feat/config-migration`
    *   `feat/integrate-config-management`
    *   `refactor/electron-app-reloc-deps`
    *   `feature/initial-setup-and-fixes`
    *   `Jules` (a general development branch likely containing a mix of these)
*   Only very specific, smaller branches like `feat/add-personality-profile-types` (which was already part of the `master` baseline for some sessions) and potentially `feat/consolidate-project-structure` were reported as locally processed or merged in some contexts. However, even pushing these limited changes to the remote `master` often failed.

**Consequences:**
*   The `Unified-AI-Project` on the remote `master` branch **does not accurately reflect the fully merged and integrated state** envisioned in this plan. Many core structural elements, data migrations, and configuration setups planned in early phases (Sections 4.1, 4.2, 4.3) are likely missing or incomplete on `master`.
*   The iterative code migration for Core AI Logic, Services, Tools, and Interfaces (Sections 4.4) has been severely hampered.
*   Path resolution and basic integration (Section 4.5) across the entire codebase cannot be considered complete.

**Path Forward:**
*   Further merging and integration efforts for the listed problematic branches, and indeed for the project as a whole to reach the state described in this plan, **must be conducted in an environment free from the previously encountered sandbox limitations.**
*   The "Potential Challenges" outlined in Section 7, particularly "Path Hell" and "Dependency Management," are likely to be more pronounced once a proper merge can be attempted due to the prolonged period of disjointed development on numerous unmerged branches.

This revised status underscores that while the plan provides a valuable roadmap, its execution is currently blocked, and the project's actual state on `master` is significantly behind the plan's intended progression.
```

## 9. Post-Merge Learnings and Future Architectural Considerations

While the primary merge and restructure activities are concluded, the process of integrating and testing various components has highlighted several areas pertinent to future development and architectural robustness:

*   **Mocking Strategies for Complex Systems:**
    *   **Challenge:** Testing components that rely on external services (like LLMs) or deeply nested module calls (e.g., `DialogueManager` -> `FactExtractorModule` -> `LLMInterface`) revealed that simple mock responses can be insufficient. Failures can occur if a mock doesn't return data in the precise format expected by an intermediate module (e.g., JSON for the `FactExtractorModule`), even if the final output being asserted appears correct.
    *   **Consideration:** Future testing strategies should emphasize context-aware mocks that can adapt their responses based on the calling module or the specifics of the input prompt. This will improve the reliability of unit and integration tests for complex interaction chains.

*   **Asynchronous Operations and Control Flow:**
    *   **Observation:** Test runs have produced warnings related to `async` coroutines not being properly `await`ed (e.g., `RuntimeWarning: coroutine ... was never awaited`).
    *   **Consideration:** As the application increasingly uses asynchronous operations (for I/O, API calls, etc.), rigorous adherence to `async/await` patterns is crucial. Unawaited asynchronous calls can lead to unpredictable behavior, race conditions, or resource leaks. Future development should include careful review of asynchronous code paths and potentially leverage async-specific testing tools more extensively.

*   **Inter-Module Data Consistency and Synchronization:**
    *   **Principle:** A core principle of robust systems is ensuring that when one module (Module A) produces data or state changes that another module (Module B) depends on, Module B accesses this information only when it is complete and consistent.
    *   **Consideration:** For sequential operations, this means careful design of data flow and state management. For concurrent operations (e.g., if different parts of the AI were to operate in parallel threads or tasks), explicit synchronization mechanisms (like mutexes, semaphores, or locks) would be essential for any shared mutable data structures. This prevents race conditions, data corruption, and ensures that modules operate on reliable information.

*   **Concurrency Control for Scalability:**
    *   **Observation:** While current test failures have not been directly attributed to multi-threading issues (as tests largely run sequentially), the system's architecture should anticipate future needs for handling concurrent requests (e.g., in the API server) or background processing tasks.
    *   **Consideration:** Key components, especially those managing shared state (e.g., `HAMMemoryManager`, `ContentAnalyzerModule`'s knowledge graph if globally shared and mutable), would need to be designed or augmented with concurrency controls (e.g., mutexes) to ensure thread safety and data integrity under concurrent load. This is vital for stability and predictable behavior as the system scales.

These learnings are valuable for guiding ongoing development, refactoring efforts, and ensuring the long-term stability and maintainability of the `Unified-AI-Project`.
