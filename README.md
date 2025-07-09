# Unified-AI-Project

## Overview

The **Unified-AI-Project** aims to create a versatile and intelligent conversational AI framework. It consolidates and enhances capabilities from previous projects like MikoAI, Fragmenta, and other CatAI initiatives. The primary goal is to build a modular, maintainable, and extensible system capable of rich dialogue, context understanding, learning, and tool usage.

For details on the initial project structure, merge strategy, and architectural principles that guided the consolidation, please refer to the [MERGE_AND_RESTRUCTURE_PLAN.md](MERGE_AND_RESTRUCTURE_PLAN.md). For a summary of the current implementation status of various components, see [Project Status Summary](docs/PROJECT_STATUS_SUMMARY.md), and for an overview of how project files are organized, see [Project Content Organization](docs/PROJECT_CONTENT_ORGANIZATION.md).

### Current Project Status & Critical Merge Information

**Important:** As detailed in the `MERGE_AND_RESTRUCTURE_PLAN.md` (Section 8, "Post-Merge Status Update"), the project's `master` branch is currently impacted by significant merge challenges. Due to sandbox environment limitations, a number of feature branches containing substantial structural and foundational code (including initial setup, data migration, and configuration migration) could not be successfully merged. This means the remote `master` branch may not fully reflect all intended features or the complete project structure. Development and integration efforts for these branches are ongoing and require an environment not constrained by these limitations.

### Future Vision

Beyond the currently implemented features, the project holds a long-term vision inspired by concepts of "Language as Life," aiming for an AI that is deeply self-aware, adaptive, and capable of semantic evolution. This includes exploring advanced ideas such as a "Linguistic Immune System" and "MetaFormulas" to guide its development towards a "Polydimensional Semantic Entity." These philosophical underpinnings and future conceptual goals are further elaborated in project documentation (see `docs/PROJECT_STATUS_SUMMARY.md` and `docs/architecture/`).

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

*   **AI Virtual Input System (AVIS) (`src/services/ai_virtual_input_service.py` and `docs/architecture/AI_Virtual_Input_System_spec.md`):** A system enabling the AI to simulate GUI interactions (mouse, keyboard) and execute code within a controlled virtual environment. Works with the `AISimulationControlService` for permissions and execution.

*   **LLM Interface (`src/services/llm_interface.py`):** Provides a standardized interface to interact with various Large Language Models (e.g., Ollama, OpenAI), managing API calls and model configurations.

*   **Configuration System (`configs/`):** Centralized YAML and JSON files for system behavior, personality profiles, API keys, formulas, etc.

*   **Heterogeneous Synchronization Protocol (HSP) (`src/hsp/`):**
    *   **Purpose:** Enables different AI instances (peers) to communicate, share knowledge, and collaborate on tasks.
    *   **Functionality:** Defines message types (Facts, Capability Advertisements, Task Requests/Results, etc.) and communication patterns (Publish/Subscribe, Request/Reply) for inter-AI interaction. Core functionalities like message transport (MQTT via `HSPConnector`), fact publishing/processing, and basic task brokering are implemented.
    *   **Transport:** Currently uses MQTT for message transport.
    *   **Key Features:** Includes mechanisms for basic service discovery (though the `ServiceDiscoveryModule` requires significant rework for full HSP alignment), basic trust management, and strategies for handling conflicting information.
    *   **Status:** Core components are functional. However, full adherence to the specification, advanced QoS, and robust error handling are ongoing. The `ServiceDiscoveryModule` in particular needs refactoring to fully support HSP capability advertisements and integration with the `TrustManager`. See `docs/PROJECT_STATUS_SUMMARY.md` for more details.
    *   **Specification:** See `docs/HSP_SPECIFICATION.md`.

*   **Fragmenta Orchestrator (`src/fragmenta/fragmenta_orchestrator.py`):**
    *   **Purpose:** Designed to manage complex tasks, coordinate data flow between modules, and apply sophisticated processing strategies.
    *   **Status:** A basic class structure and a rudimentary `process_complex_task` method (with simple chunking and LLM/tool dispatch) are implemented. However, most advanced features outlined in its design specification (e.g., sophisticated task analysis, advanced pre/post-processing, parallelism, self-evaluation) are currently conceptual and pending full implementation. See `docs/architecture/Fragmenta_design_spec.md` and `docs/PROJECT_STATUS_SUMMARY.md`.

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
*   **Internal Data Structures:** For data exchanged between internal Python modules, adhere to the standards outlined in [Internal Data Standards (`docs/INTERNAL_DATA_STANDARDS.md`)](docs/INTERNAL_DATA_STANDARDS.md). This primarily involves using `TypedDict` for clarity and static type checking.
*   **General:** Aim for clear, readable, and well-documented code.

### Questions or Issues

If you have questions, find a bug, or want to suggest an enhancement, please consider documenting them or discussing with your team as appropriate for your project management style.

## Architectural Notes & Known Issues

This section highlights some current observations, known issues from testing, and architectural considerations for ongoing development.

### Current Project State & Development Observations

*   **Critical Merge Status:** As mentioned in the Overview, the `master` branch is impacted by incomplete merges of several foundational feature branches due to sandbox limitations. This affects the overall stability and completeness of the current codebase on `master`.
*   **Known Failing Tests:** Some automated tests consistently fail. Current hypotheses point towards limitations in mock LLM responses for deeply nested module calls and potential subtle data handling or string manipulation issues. These are under investigation.
*   **Asynchronous Code Warnings:** Test runs have surfaced `RuntimeWarning: coroutine ... was never awaited` for some `async def` test methods. Developers should ensure correct implementation and testing of asynchronous code using appropriate `async/await` patterns.

### Inter-Module Data Flow and Synchronization

*   **Data Integrity:** When designing interactions where one module (Module A) produces data or state that another module (Module B) consumes, it's crucial to ensure that Module B accesses this data only when it is complete, consistent, and in the expected format.
*   **Future Concurrency:** For any parts of the system that might involve concurrent processing (e.g., multiple API requests handled simultaneously, background learning tasks), shared mutable data structures (e.g., global caches, shared knowledge graphs, stateful managers) **must be protected with explicit synchronization mechanisms** (e.g., `threading.Lock` in Python, or equivalent). This is vital to prevent race conditions and ensure data integrity.

### Mocking Strategy for Tests

*   **Context-Aware Mocks:** When testing modules that interact with services like the `LLMInterface`, ensure that mocks are configured to return data in the precise format expected by the *direct client* of that service. For instance, if `FactExtractorModule` calls `LLMInterface` and expects a JSON string, the mock for `LLMInterface` should provide that, even if the higher-level test is asserting a final user-facing string.
*   **Complexity:** As the system grows, mock setups may need to become more sophisticated to accurately simulate different scenarios and responses, especially for integration-style tests.

### Environment and Setup
*   **PYTHONPATH:** Ensure `PYTHONPATH` is set up correctly (as mentioned in "Getting Started") to avoid import errors, especially when running scripts or tests from subdirectories or with certain IDE configurations.