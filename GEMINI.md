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
## Recent Problem-Solving Log

### Problem-Solving Method Applied

The following structured approach was used to identify and resolve recent issues:

1.  **Understand the Problem**: Analyze error messages (e.g., `TypeError: 'coroutine' object is not subscriptable`), understand the context of the failure, and review recent code changes (`git diff`).
2.  **Identify Implemented vs. Documented Features**: Scan code and documentation files to understand the project's current state and identify gaps. This involves reading key documentation and corresponding code files to verify actual implementation against documented status (e.g., "Conceptual," "Partial," "Placeholder").
3.  **Document Findings**: Create new Markdown documents to formally record identified gaps (e.g., `UNIMPLEMENTED_FEATURES_SUMMARY.md`).
4.  **Update Project Documentation**: Integrate new documents into the main project index (e.g., `UNIFIED_DOCUMENTATION_INDEX.md`) to ensure discoverability.
5.  **Plan the Fix**: For specific code issues, pinpoint exact problematic lines, identify failing tests, and formulate precise code changes.
6.  **Implement the Fix**: Apply code changes (e.g., adding `await` to `async` calls) and corresponding test changes (e.g., correcting `await` usage, using `patch.object` for mocking, addressing timing issues with `asyncio.create_task` and `await`ing tasks).
7.  **Verify the Fix**: Run affected tests to confirm resolution and absence of new regressions.
8.  **Update Related Documentation (Post-Fix)**: Review and update documentation directly related to the fixed code to ensure it accurately reflects the current implementation.

### 2025-08-23

*   **Task**: Resolve `TypeError: 'coroutine' object is not subscriptable` in `ProjectCoordinator` and related test failures.
*   **Action**:
    *   Modified `apps/backend/src/core_ai/dialogue/project_coordinator.py`: Added `await` to calls to `self.service_discovery.find_capabilities`.
    *   Modified `apps/backend/tests/core_ai/dialogue/test_project_coordinator.py`:
        *   Awaited `pc.service_discovery.get_all_capabilities()` in `test_handle_project_happy_path` assertion.
        *   Corrected mocking of `agent_manager.launch_agent` and `agent_manager.wait_for_agent_ready` in `test_dispatch_single_subtask_agent_launch_and_discovery`.
        *   Used `patch.object` for `sdm.find_capabilities` and adjusted timing with `await advertisement_task` in `test_dispatch_launches_and_discovers_with_real_components` to resolve timing issues.
*   **Status**:
    *   **Completed**: Code and test modifications are done.
    *   **Verification**: All tests in `test_project_coordinator.py` passed.

*   **Task**: Identify unimplemented/partially implemented core features.
*   **Action**:
    *   Scanned Python files in `apps/backend/src`.
    *   Scanned Markdown files in `docs/`.
    *   Reviewed `UNIFIED_DOCUMENTATION_INDEX.md` and specific technical architecture documents (`linguistic-immune-system.md`, `deep-mapping-personality.md`, `ai-virtual-input.md`, `knowledge-graph.md`, `meta-formulas.md`, `alpha-deep-model.md`, `fragmenta-orchestrator.md`, `simultaneous-translation.md`, `audio-processing.md`, `task_evaluator.py`, `adaptive_learning_controller.py`).
    *   Compiled a comprehensive list of unimplemented/partially implemented features.
*   **Status**:
    *   **Completed**: Summary compiled.
    *   **Output**: Created `docs/01-summaries-and-reports/UNIMPLEMENTED_FEATURES_SUMMARY.md`.

*   **Task**: Update project documentation to reflect recent changes.
*   **Action**:
    *   Modified `docs/03-technical-architecture/ai-components/service-discovery-module.md`: Added a note that `find_capabilities` is an asynchronous method.
    *   Modified `docs/UNIFIED_DOCUMENTATION_INDEX.md`: Added an entry for `UNIMPLEMENTED_FEATURES_SUMMARY.md` under "總結與報告" (Summaries and Reports).
*   **Status**:
    *   **Completed**: Documentation updated.