# Unified-AI-Project

## Overview

The **Unified-AI-Project** aims to create a versatile and intelligent conversational AI framework. It consolidates and enhances capabilities from previous projects like MikoAI, Fragmenta, and other CatAI initiatives. The primary goal is to build a modular, maintainable, and extensible system capable of rich dialogue, context understanding, learning, and tool usage.

**For a comprehensive guide to all documentation, including detailed architectural documents, module specifications, and project status, please see the [Project Table of Contents](docs/CONTENTS.md).**

### Current Project Status & Critical Merge Information

**Important:** The project's `master` branch is currently impacted by significant merge challenges due to sandbox environment limitations. Several feature branches with foundational code could not be successfully merged. This means the remote `master` branch may not fully reflect all intended features or the complete project structure. For more details, see the [MERGE_AND_RESTRUCTURE_PLAN.md](docs/project/MERGE_AND_RESTRUCTURE_PLAN.md) and [Project Status Summary](docs/project/STATUS_SUMMARY.md).

### Future Vision

The project envisions an AI capable of deep self-awareness, semantic evolution, and adaptive learning, guided by concepts like "Language as Life." This includes exploring advanced ideas such as a "Linguistic Immune System" and "MetaFormulas." For more on the philosophical underpinnings and future conceptual goals, please refer to the [Project Overview](docs/project/project_overview.md) and documents within the [Core Architecture & Design section of our Table of Contents](docs/CONTENTS.md#1-core-architecture--design).

## Key Features & Modules

This project integrates and is developing several core AI components. For detailed information on each, please refer to their respective specifications or the [Project Table of Contents](docs/CONTENTS.md).

*   **Dialogue Management:** Orchestrates conversation flow.
*   **Personality Management:** Manages different AI personalities.
*   **Hierarchical Associative Memory (HAM):** Custom memory system. See [HAM Design Specification](docs/architecture/specifications/HAM_design_spec.md).
*   **Learning System:** Includes fact extraction, self-critique, and content analysis (knowledge graph generation).
*   **Formula Engine:** Rule-based system. See [MetaFormulas Design Specification](docs/architecture/specifications/MetaFormulas_spec.md).
*   **Tool Dispatcher:** Enables AI to use external/internal "tools".
*   **AI Virtual Input System (AVIS):** Allows AI to simulate GUI interactions. See [AVIS Design Specification](docs/architecture/specifications/AI_Virtual_Input_System_spec.md).
*   **LLM Interface:** Standardized interface for Large Language Models.
*   **Configuration System:** Centralized YAML/JSON files in `configs/`.
*   **Heterogeneous Synchronization Protocol (HSP):** Enables AI instances to communicate. See [HSP Specification](docs/architecture/specifications/HSP_SPECIFICATION.md).
*   **Fragmenta Orchestrator:** Manages complex tasks and data flow. See [Fragmenta Design Specification](docs/architecture/specifications/Fragmenta_design_spec.md).
*   **Jules - Asynchronous Development Capability:** Specialized capability for software development tasks. See [Jules Capability Specification](docs/architecture/specifications/Jules_Development_Capability_spec.md).

## Getting Started

These instructions provide a basic guide to get the project running. For detailed setup, refer to specific documents linked in the [Project Table of Contents](docs/CONTENTS.md).

### Prerequisites

*   Python 3.9+
*   Node.js 16.x+ (with npm)
*   Git

### Basic Setup Steps

1.  Clone the repository.
2.  Set up Python virtual environment and install dependencies from `requirements.txt`.
3.  Install Node.js dependencies (root and for Electron app).
4.  Configure environment variables by copying `.env.example` to `.env` and editing.
5.  Ensure `PYTHONPATH` is set correctly if needed; running from project root is recommended.

### Running the Application

*   **CLI:** Use `src/interfaces/cli/main.py`.
*   **Electron App:** Start via `npm start` in `src/interfaces/electron_app`.
*   **API Server (FastAPI):** Run `src/services/main_api_server.py` (e.g., with `uvicorn`). API docs at `/docs`.

## Contributing

Contributions are welcome! Key guidelines:

### Development Workflow

1.  Work in feature/fix branches.
2.  Write code and include tests.
3.  Run tests (Python: `pytest`, JS: see `package.json`).
4.  Format and lint your code (e.g., Black, Prettier).
5.  Commit using Conventional Commits format.

### Code Style & Data Standards

*   Python: PEP 8.
*   Internal Data: Use `TypedDict` ([Internal Data Standards](docs/guides/INTERNAL_DATA_STANDARDS.md)).
*   Translations: ([Translation Guide](docs/guides/TRANSLATION_GUIDE.md)).
*   General: Aim for clear, readable, well-documented code.

## Architectural Notes & Known Issues

For the most current status on known issues, testing, and ongoing development, please refer to the [Project Status Summary](docs/project/STATUS_SUMMARY.md). Key general considerations include:

*   **Critical Merge Status:** The `master` branch is impacted by incomplete merges (see Overview).
*   **Inter-Module Data Flow and Synchronization:** Ensure data integrity. Shared mutable data in concurrent contexts **must use explicit synchronization mechanisms**.
*   **Mocking Strategy for Tests:** Mocks should return data in the precise format expected by the direct client.
*   **Environment and Setup (PYTHONPATH):** Ensure `PYTHONPATH` is correctly set.

---
*This README provides a high-level overview. For detailed information, please consult the [Project Table of Contents](docs/CONTENTS.md).*