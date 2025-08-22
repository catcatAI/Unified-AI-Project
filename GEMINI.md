# Project Analysis: Unified AI Project

This document provides an overview of the `Unified-AI-Project` codebase, intended to serve as instructional context for future interactions with the Gemini CLI.

## Project Overview

The `Unified-AI-Project` is a sophisticated monorepo designed as a **hybrid AI ecosystem**. Its primary purpose is to power an internal AI system, notably the AI character "Angela" within a simulation game called "Angela's World". Beyond this, a key architectural design is its ability to **integrate with and orchestrate various external AI agents and development tools** (e.g., Rovo Dev Agent, Gemini). This allows the project to leverage specialized external capabilities while maintaining a modular and extensible core.

The project is structured into:
*   **Applications (`apps/`)**:
    *   `desktop-app`: The Electron-based game client for "Angela's World".
    *   `backend`: The core Python backend, responsible for AI models, APIs, and game logic, driving Angela.
    *   `frontend-dashboard`: A Next.js/React web dashboard for developers to manage, monitor, and debug the AI and game systems.
*   **Packages (`packages/`)**:
    *   `cli`: Command-line interface tools for backend interaction.
    *   `ui`: Shared UI components for frontend applications.

## Building and Running

The project utilizes `pnpm` for monorepo management.

**1. Install pnpm (if not already installed):**
```bash
npm install -g pnpm
```

**2. Install Dependencies:**
From the root of the repository (`D:\Projects\Unified-AI-Project`), run:
```bash
pnpm install
```

**3. Start Development Servers:**
To concurrently start the backend and frontend development servers:
```bash
pnpm dev
```
(The backend API typically runs on `http://localhost:8000`, and the frontend dashboard on `http://localhost:3000`.)

## Testing

To run all tests across the monorepo:
```bash
pnpm test
```

To run tests with coverage reports:
```bash
pnpm test:coverage
```

## Development Conventions

*   **Monorepo Structure**: The project is organized as a monorepo using `pnpm` workspaces.
*   **Documentation**: Comprehensive documentation is maintained in the `docs/` directory, with a central `UNIFIED_DOCUMENTATION_INDEX.md` for navigation.
*   **External Tool Integration**: The project is designed to integrate with external AI development tools, and this integration is managed through specific modules within `apps/backend/src/integrations`.
*   **Testing Practices**: The project includes dedicated `tests/` directories within each application and package, indicating a focus on unit and integration testing. Python tests likely use `pytest` (inferred from `conftest.py` in `apps/backend/tests`).

## Development Log

### 2025-08-10

*   **Task**: Infrastructure Repair - HSP Connection Reliability.
*   **Action**: Modified `apps/backend/src/hsp/connector.py` to implement a connection retry mechanism in the `connect` method, as per the `technical-implementation-roadmap.md`. This change adds a 3-attempt retry loop with exponential backoff to improve the stability of the HSP connection.
*   **Status**:
    *   **Completed**: Code modification is done.
    *   **Blocked**: Unable to verify the fix by running the `pnpm test` command due to a persistent tool environment error: `Directory 'Unified-AI-Project' is not a registered workspace directory.` A manual testing task has been created in `MANUAL_TESTING_REQUIRED.md`.

*   **Task**: Infrastructure Repair - Memory System Upgrade (Vector Database Integration).
*   **Action**:
    *   Created `apps/backend/src/core_ai/memory/vector_store.py` to encapsulate ChromaDB logic.
    *   Modified `apps/backend/src/core_ai/memory/ham_memory_manager.py` to integrate `VectorMemoryStore` and `ImportanceScorer`, and to enhance its memory storage and retrieval capabilities.
*   **Status**:
    *   **Completed**: Code modification is done.
    *   **Verification**: Requires manual testing as automated tests cannot be run.

*   **Task**: Infrastructure Repair - HAM Date Range Query Fix.
*   **Action**: Modified `apps/backend/src/core_ai/memory/ham_memory_manager.py` to improve the date range filtering logic within `query_core_memory`, using a new `_normalize_date` helper method and enhancing error handling.
*   **Status**:
    *   **Completed**: Code modification is done.
    *   **Verification**: Requires manual testing as automated tests cannot be run.

*   **Task**: Infrastructure Repair - Async Code Standardization.
*   **Action**: Attempted to create `apps/backend/src/utils/async_utils.py` and its parent directory.
*   **Status**:
    *   **Skipped**: Unable to complete due to persistent tool environment error: `Directory 'Unified-AI-Project' is not a registered workspace directory.` This prevents creating new directories or files within the project structure via shell commands.

*   **Task**: Infrastructure Repair - HSP Protocol Optimization.
*   **Action**: Attempted to locate `src/core/hsp/hsp_protocol.py` as suggested by the `technical-implementation-roadmap.md`.
*   **Status**:
    *   **Skipped**: The file `hsp_protocol.py` does not exist in the project, indicating a discrepancy between the roadmap and the actual codebase. Therefore, the suggested optimization cannot be applied.

*   **Task**: Continuous Learning Framework - Experience Replay Mechanism.
*   **Action**: Created `apps/backend/src/core_ai/learning/experience_replay.py` with the `ExperienceReplayBuffer` class.
*   **Status**:
    *   **Completed**: File created.
    *   **Verification**: Requires manual testing as automated tests cannot be run.

*   **Task**: Continuous Learning Framework - Knowledge Distillation Framework.
*   **Action**: Created `apps/backend/src/core_ai/learning/knowledge_distillation.py` with the `KnowledgeDistillationManager` class.
*   **Status**:
    *   **Completed**: File created.
    *   **Verification**: Requires manual testing as automated tests cannot be run.

*   **Task**: Continuous Learning Framework - Task Execution Evaluator.
*   **Action**: Created `apps/backend/src/core_ai/evaluation/task_evaluator.py` and fixed a bug in the `_assess_output_quality` method.
*   **Status**:
    *   **Completed**: File created and bug fixed.

*   **Task**: Continuous Learning Framework - Adaptive Learning Controller.
*   **Action**: Attempted to create `apps/backend/src/core_ai/meta/adaptive_learning_controller.py` and its parent directory.
*   **Status**:
    *   **Skipped**: Unable to complete due to persistent tool environment error: `Directory 'Unified-AI-Project' is not a registered workspace directory.` This prevents creating new directories or files within the project structure via shell commands.
