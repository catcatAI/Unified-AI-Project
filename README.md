# Unified-AI-Project

## Overview

The **Unified-AI-Project** aims to create a versatile and intelligent conversational AI framework. It consolidates and enhances capabilities from previous projects like MikoAI, Fragmenta, and other CatAI initiatives. The primary goal is to build a modular, maintainable, and extensible system capable of rich dialogue, context understanding, learning, and tool usage.

For a comprehensive guide to all documentation, please see the [Project Table of Contents](docs/CONTENTS.md).

For details on the initial project structure, merge strategy, and architectural principles that guided the consolidation, please refer to the [MERGE_AND_RESTRUCTURE_PLAN.md](docs/project/MERGE_AND_RESTRUCTURE_PLAN.md). For a summary of the current implementation status of various components, see [Project Status Summary](docs/project/STATUS_SUMMARY.md), and for an overview of how project files are organized, see [Project Content Organization](docs/project/CONTENT_ORGANIZATION.md).

### Current Project Status & Critical Merge Information

**Important:** As detailed in the `docs/project/MERGE_AND_RESTRUCTURE_PLAN.md` (Section 8, "Post-Merge Status Update"), the project's `master` branch is currently impacted by significant merge challenges. Due to sandbox environment limitations, a number of feature branches containing substantial structural and foundational code (including initial setup, data migration, and configuration migration) could not be successfully merged. This means the remote `master` branch may not fully reflect all intended features or the complete project structure. Development and integration efforts for these branches are ongoing and require an environment not constrained by these limitations.

### Future Vision

Beyond the currently implemented features, the project holds a long-term vision inspired by concepts of "Language as Life," aiming for an AI that is deeply self-aware, adaptive, and capable of semantic evolution. This includes exploring advanced ideas such as a "Linguistic Immune System" and "MetaFormulas" to guide its development towards a "Polydimensional Semantic Entity." These philosophical underpinnings and future conceptual goals are further elaborated in project documentation (see `docs/project/STATUS_SUMMARY.md` and `docs/architecture/`).

## Key Features & Modules

This project integrates and is developing several core AI components:

*   **Dialogue Management (`src/core_ai/dialogue/dialogue_manager.py`):** Orchestrates conversation flow, integrates with other AI components, and generates responses. It leverages personality profiles, memory systems, and formula-based logic.

*   **Personality Management (`src/core_ai/personality/personality_manager.py`):** Manages different AI personalities, influencing tone, response style, and core values. Profiles are configurable (see `configs/personality_profiles/`).

*   **Hierarchical Associative Memory (HAM) (`src/core_ai/memory/ham_memory_manager.py`):** A custom memory system designed for storing and retrieving experiences, learned facts, and dialogue context.

*   **Learning System (`src/core_ai/learning/`):**
    *   **Fact Extractor Module:** Extracts structured facts from dialogue.
    *   **Self-Critique Module:** Evaluates AI responses for quality and coherence.
    *   **Learning Manager:** Coordinates the learning process and storage of new knowledge into HAM.
    *   **Content Analyzer Module:**
        *   **Purpose:** Achieves deeper context understanding by analyzing text content (e.g., from documents, user inputs, HSP facts) to create and maintain a structured knowledge graph.
        *   **Functionality:** Extracts named entities, identifies relationships (including from semantic triples), and integrates this information into a NetworkX knowledge graph. Supports basic ontology mapping.
        *   **Technologies:** Utilizes `spaCy` for Natural Language Processing tasks (NER, dependency parsing) and `NetworkX`.
        *   **Status:** A functional prototype (Phase 2) is integrated, capable of generating and updating a knowledge graph with entity and rule-based relationship extraction, including processing structured HSP facts. Ongoing work focuses on refining extraction, enhancing ontology use, and deepening its integration with the `DialogueManager` for richer contextual awareness.

*   **Formula Engine (`src/core_ai/formula_engine/`):** Implements a rule-based system where predefined "formulas" (see `configs/formula_configs/`) can trigger specific actions or responses based on input conditions. This allows for deterministic behaviors and tool dispatch.

*   **Tool Dispatcher (`src/tools/tool_dispatcher.py`):** Enables the AI to use external or internal "tools" (e.g., calculators, information retrieval functions) to augment its capabilities. Tools can be triggered by the Formula Engine or other AI logic.

*   **AI Virtual Input System (AVIS) (`src/services/ai_virtual_input_service.py` and `docs/architecture/specifications/AI_Virtual_Input_System_spec.md`):** A system enabling the AI to simulate GUI interactions (mouse, keyboard) and execute code within a controlled virtual environment. Works with the `AISimulationControlService` for permissions and execution.

*   **LLM Interface (`src/services/llm_interface.py`):** Provides a standardized interface to interact with various Large Language Models (e.g., Ollama, OpenAI), managing API calls and model configurations.

*   **Configuration System (`configs/`):** Centralized YAML and JSON files for system behavior, personality profiles, API keys, formulas, etc.

*   **Heterogeneous Synchronization Protocol (HSP) (`src/hsp/`):**
    *   **Purpose:** Enables different AI instances (peers) to communicate, share knowledge, and collaborate on tasks.
    *   **Functionality:** Defines message types (Facts, Capability Advertisements, Task Requests/Results, etc.) and communication patterns (Publish/Subscribe, Request/Reply) for inter-AI interaction. Core functionalities like message transport (MQTT via `HSPConnector`), fact publishing/processing, and basic task brokering are implemented.
    *   **Transport:** Currently uses MQTT for message transport.
    *   **Key Features:** Includes mechanisms for basic service discovery, basic trust management, and strategies for handling conflicting information. The `ServiceDiscoveryModule` (`src/core_ai/service_discovery/service_discovery_module.py`) provides some HSP-specific capability management but requires further refactoring for full alignment with the HSP specification and deeper `TrustManager` integration.
    *   **Status:** Core HSP components for message transport and basic payload exchange are functional. However, full adherence to the specification, advanced QoS, robust error handling, and complete service discovery capabilities are ongoing. See `docs/project/STATUS_SUMMARY.md` and `docs/architecture/specifications/HSP_SPECIFICATION.md` (Appendix A) for more details on current status and gaps.
    *   **Specification:** See `docs/architecture/specifications/HSP_SPECIFICATION.md`.

*   **Fragmenta Orchestrator (`src/fragmenta/fragmenta_orchestrator.py`):**
    *   **Purpose:** Designed to manage complex tasks, coordinate data flow between modules, and apply sophisticated processing strategies.
    *   **Status:** Has undergone significant enhancements (as of July 2024). It now employs an advanced state management system (`EnhancedComplexTaskState`, `EnhancedStrategyPlan`) supporting sequential and foundational parallel step execution, explicit input/output mapping between steps, and robust HSP task lifecycle management (including retries and timeouts). While many advanced features from its original design specification (like dynamic strategy generation or complex dependency graphs) are still conceptual, the current implementation provides a much more capable orchestration engine. See `docs/architecture/specifications/Fragmenta_design_spec.md` (especially the July 2024 implementation notes) and `docs/project/STATUS_SUMMARY.md` for details.

*   **Jules - Asynchronous Development Capability (`src/agents/jules_dev_agent.py` module):**
    *   **Purpose:** A specialized capability set, orchestrated by the core AI persona (Angela), to handle software development tasks like fixing bugs and implementing small features. This involves interacting with a simulated development environment.
    *   **Status:** Conceptual design phase. The `JulesDevelopmentCapability` class structure and an updated design specification (`docs/architecture/specifications/Jules_Development_Capability_spec.md`) frame Jules as a set of functions Angela can utilize. Core functionalities like task understanding, code comprehension, planning, and simulated environment interaction are envisioned to be managed by Angela through this capability.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

*   **Python:** Version 3.9 or higher is recommended.
*   **Node.js:** Version 16.x or higher is recommended, along with npm.
*   **Git:** For cloning the repository.

### Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd Unified-AI-Project
    ```

2.  **Set up Python Environment:**
    It's highly recommended to use a virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```
    Install Python dependencies:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Set up Node.js Environment:**
    Install root project Node.js dependencies:
    ```bash
    npm install
    ```
    Install Electron app specific dependencies:
    ```bash
    cd src/interfaces/electron_app
    npm install
    cd ../../..  # Return to project root
    ```

4.  **Environment Variables:**
    The project uses a `.env` file for sensitive configurations like API keys.
    Copy the example file and fill in your details:
    ```bash
    cp .env.example .env
    ```
    Now, edit `.env` with your specific keys and settings.

5.  **PYTHONPATH (if needed):**
    The project uses absolute imports from the `src` directory (e.g., `from core_ai...`). If you encounter import errors, ensure your `PYTHONPATH` includes the project root directory or the `src` directory. Many IDEs handle this automatically. Alternatively, you can set it temporarily in your shell:
    ```bash
    export PYTHONPATH="${PYTHONPATH}:$(pwd)"  # For Linux/macOS
    # For Windows (cmd.exe): set PYTHONPATH=%PYTHONPATH%;%CD%
    # For Windows (PowerShell): $env:PYTHONPATH += ";${pwd}"
    ```
    It's often better to run Python scripts from the project root to avoid import issues.

### Running the Application

You can interact with the Unified-AI-Project in several ways:

1.  **Command Line Interface (CLI):**
    To send a query to the AI via the CLI:
    ```bash
    python src/interfaces/cli/main.py query "Hello AI, how are you?"
    ```
    (Ensure you are in the project root directory or have `PYTHONPATH` set up correctly.)

2.  **Electron Desktop Application:**
    To launch the Electron app:
    ```bash
    cd src/interfaces/electron_app
    npm start
    ```

3.  **API Server (FastAPI):**
    To start the backend API server:
    ```bash
    python src/services/main_api_server.py
    ```
    Or, for development with auto-reload (run from project root):
    ```bash
    uvicorn src.services.main_api_server:app --reload --host 0.0.0.0 --port 8000
    ```
    The API will then be accessible at `http://localhost:8000` (or `http://0.0.0.0:8000`). You can find Swagger UI documentation at `http://localhost:8000/docs`.

### Key Configuration Files

*   `configs/system_config.yaml`: General system-wide configurations.
*   `configs/api_keys.yaml`: Configuration for external API keys (though `.env` might be preferred for local overrides).
*   `configs/personality_profiles/`: Contains JSON files defining different AI personalities.
*   `configs/formula_configs/`: Contains JSON files for the formula engine.

## Contributing

Contributions are welcome and greatly appreciated! Here are some guidelines to help you get started with local development.

### Development Workflow

1.  **Create a branch:**
    It's good practice to work on new features or bug fixes in separate branches.
    ```bash
    # Ensure you are on your main development branch (e.g., master)
    # git checkout master
    # git pull # If you are collaborating and need to update

    git checkout -b feat/your-feature-name  # Example: feat/new-dialogue-intent
    # or
    git checkout -b fix/issue-description   # Example: fix/incorrect-api-response
    ```

2.  **Make your changes:**
    Write your code and add new tests if applicable.

3.  **Test your changes:**
    *   **Python Tests:** Run Python unit tests using `pytest`. Ensure you have it installed (`pip install pytest`).
        ```bash
        pytest tests/
        ```
        Or, to run specific tests:
        ```bash
        pytest tests/core_ai/test_dialogue_manager.py
        ```
    *   **JavaScript Tests:** (Placeholder - to be defined more clearly as JS tests are added)
        The root `package.json` and `src/interfaces/electron_app/package.json` have placeholder test scripts. As these are developed, specific commands will be added here. For now, ensure your changes don't break existing JS functionality.

4.  **Format and Lint your code:**
    *   **Python:** Adhere to PEP 8 guidelines. Consider using a formatter like Black and a linter like Flake8.
        ```bash
        # Example (if Black and Flake8 are installed)
        # black .
        # flake8 .
        ```
    *   **JavaScript/TypeScript:** Use a formatter like Prettier.
        ```bash
        # Example (if Prettier is set up in package.json scripts)
        # npm run format
        ```

5.  **Commit your changes:**
    Use clear and descriptive commit messages. We encourage using [Conventional Commits](https://www.conventionalcommits.org/) format. For example:
    *   `feat: Add user authentication for API`
    *   `fix: Correct personality loading error for custom profiles`
    *   `docs: Update API endpoint documentation`
    *   `style: Format code with Black`
    *   `refactor: Simplify dialogue state management`
    *   `test: Add unit tests for new calculation tool`
    ```bash
    git add .
    git commit -m "feat: Describe your change"
    ```

### Code Style & Data Standards

*   **Python:** Follow PEP 8.
*   **JavaScript/TypeScript:** Follow standard community practices. Consider using Prettier for consistent formatting.
*   **Internal Data Structures:** For data exchanged between internal Python modules, adhere to the standards outlined in [Internal Data Standards (`docs/guides/INTERNAL_DATA_STANDARDS.md`)](docs/guides/INTERNAL_DATA_STANDARDS.md). This primarily involves using `TypedDict` for clarity and static type checking.
*   **Translations:** For information on how to add or update translations for the project, please see the [Translation Guide (`docs/guides/TRANSLATION_GUIDE.md`)](docs/guides/TRANSLATION_GUIDE.md).
*   **General:** Aim for clear, readable, and well-documented code.

### Questions or Issues

If you have questions, find a bug, or want to suggest an enhancement, please consider documenting them or discussing with your team as appropriate for your project management style.

## Architectural Notes & Known Issues

This section highlights some current observations, known issues from testing, and architectural considerations for ongoing development.

### Current Project State & Development Observations

*   **Critical Merge Status:** As mentioned in the Overview, the `master` branch is impacted by incomplete merges of several foundational feature branches due to sandbox limitations. This affects the overall stability and completeness of the current codebase on `master`.
*   **Test Status Update (July 2024):**
    *   **Resolved `FragmentaOrchestrator` Test Failures:** Previously noted `AttributeError`s in `tests/fragmenta/test_fragmenta_orchestrator.py` (related to missing helper methods) have been resolved by ensuring the correct, updated version of `src/fragmenta/fragmenta_orchestrator.py` is loaded during test execution. All tests in this suite now pass.
    *   **Resolved Asynchronous Code Warnings:** `RuntimeWarning: coroutine ... was never awaited` in `tests/core_ai/dialogue/test_dialogue_manager.py` have been fixed by refactoring async tests to use `asyncio.run()`. Subsequent assertion failures in these tests due to output changes were also corrected. All tests in this suite now pass.
    *   **Remaining Known Issues:**
        *   **HSP Integration Tests:** Tests in `tests/hsp/test_hsp_integration.py` and `tests/services/test_main_api_server_hsp.py` consistently error out due to `ConnectionRefusedError`. These tests require an active MQTT broker. They are now marked with `pytest.mark.skipif` to automatically skip if a broker is not detected at `localhost:1883`, preventing test suite errors in environments without a broker.
        *   **Mock LLM Dependent Failures:** A few tests in `tests/interfaces/test_cli.py` and `tests/tools/test_translation_model.py` fail due to current mock LLM responses not aligning with the specific JSON or intent formats expected by the modules under test. These require refinement of the mock LLM setups for those specific test cases.
*   **(Original) Known Failing Tests:** Some automated tests consistently fail. Current hypotheses point towards limitations in mock LLM responses for deeply nested module calls and potential subtle data handling or string manipulation issues. These are under investigation. *(This is now superseded by the more specific points above but kept for historical context if needed)*
*   **(Original) Asynchronous Code Warnings:** Test runs have surfaced `RuntimeWarning: coroutine ... was never awaited` for some `async def` test methods. Developers should ensure correct implementation and testing of asynchronous code using appropriate `async/await` patterns. *(This is now superseded by the more specific points above)*


### Inter-Module Data Flow and Synchronization

*   **Data Integrity:** When designing interactions where one module (Module A) produces data or state that another module (Module B) consumes, it's crucial to ensure that Module B accesses this data only when it is complete, consistent, and in the expected format.
*   **Future Concurrency:** For any parts of the system that might involve concurrent processing (e.g., multiple API requests handled simultaneously, background learning tasks), shared mutable data structures (e.g., global caches, shared knowledge graphs, stateful managers) **must be protected with explicit synchronization mechanisms** (e.g., `threading.Lock` in Python, or equivalent). This is vital to prevent race conditions and ensure data integrity.

### Mocking Strategy for Tests

*   **Context-Aware Mocks:** When testing modules that interact with services like the `LLMInterface`, ensure that mocks are configured to return data in the precise format expected by the *direct client* of that service. For instance, if `FactExtractorModule` calls `LLMInterface` and expects a JSON string, the mock for `LLMInterface` should provide that, even if the higher-level test is asserting a final user-facing string.
*   **Complexity:** As the system grows, mock setups may need to become more sophisticated to accurately simulate different scenarios and responses, especially for integration-style tests.

### Environment and Setup
*   **PYTHONPATH:** Ensure `PYTHONPATH` is set up correctly (as mentioned in "Getting Started") to avoid import errors, especially when running scripts or tests from subdirectories or with certain IDE configurations.