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

Contributions are welcome and greatly appreciated! Here are some guidelines to help you get started.

### Getting Code

1.  Fork the repository on GitHub.
2.  Clone your fork locally:
    ```bash
    git clone https://github.com/YOUR_USERNAME/Unified-AI-Project.git
    cd Unified-AI-Project
    ```
3.  Add the upstream remote:
    ```bash
    git remote add upstream https://github.com/ORIGINAL_OWNER/Unified-AI-Project.git
    ```

### Development Workflow

1.  **Create a branch:**
    Create a new branch for your feature or bug fix from an up-to-date `master` (or `main`) branch:
    ```bash
    git checkout master
    git pull upstream master
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

6.  **Push to your fork:**
    ```bash
    git push origin feat/your-feature-name
    ```

7.  **Create a Pull Request (PR):**
    Go to the original repository on GitHub and create a Pull Request from your forked branch to the `master` (or `main`) branch of the upstream repository.
    *   Provide a clear title and description for your PR.
    *   Link any relevant issues.
    *   Ensure all automated checks (CI/CD, if configured) pass.

### Code Style

*   **Python:** Follow PEP 8.
*   **JavaScript/TypeScript:** Follow standard community practices. Consider using Prettier for consistent formatting.
*   **General:** Aim for clear, readable, and well-documented code.

### Questions or Issues

If you have questions, find a bug, or want to suggest an enhancement, please open an issue on GitHub.