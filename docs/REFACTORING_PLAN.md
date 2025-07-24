# Refactoring and Cleanup Plan

This document outlines a plan for refactoring and cleaning up the Unified AI Project codebase. The proposed changes are based on a review of the source code, tests, documentation, and configuration files.

## 1. Source Code (`/src`)

### 1.1. `ProjectCoordinator` (`src/core_ai/dialogue/project_coordinator.py`)

-   **Issue**: Hardcoded prompts for task decomposition and result integration.
-   **Proposed Change**: Move the prompts to a configuration file (e.g., `configs/prompts.yaml`) to make them more maintainable and customizable.

-   **Issue**: Lack of robust error handling in `_substitute_dependencies`.
-   **Proposed Change**: Add a `try...except` block to handle potential `TypeError` exceptions when calling `json.dumps` on non-serializable objects.

-   **Issue**: Fragile `asyncio.sleep(5)` after launching an agent.
-   **Proposed Change**: Implement a more robust handshake mechanism. The `AgentManager` could return a future that is completed when the agent has successfully advertised its capabilities. The `ProjectCoordinator` would then `await` this future before sending a task request.

### 1.2. `HSPConnector` (`src/hsp/connector.py`)

-   **Issue**: Duplicate docstrings in the `HSPConnector` class.
-   **Proposed Change**: Remove the redundant single-line docstring.

-   **Issue**: The `on_message` method is too long and complex.
-   **Proposed Change**: Refactor the `on_message` method into smaller, more focused methods (e.g., `_decode_message`, `_handle_ack`, `_dispatch_payload`).

### 1.3. `ServiceDiscoveryModule` (`src/core_ai/service_discovery/service_discovery_module.py`)

-   **Issue**: Stale capabilities are not removed from the `known_capabilities` dictionary.
-   **Proposed Change**: Implement a periodic cleanup task that removes stale capabilities. This could be a background task that runs every few minutes.

### 1.4. `AgentManager` (`src/core_ai/agent_manager.py`)

-   **Issue**: No way to pass arguments to agent scripts.
-   **Proposed Change**: Modify the `launch_agent` method to accept a list of arguments that can be passed to the agent script.

-   **Issue**: No health check mechanism for agents.
-   **Proposed Change**: Implement a simple health check mechanism. The `BaseAgent` could expose an `is_healthy` method that can be called by the `AgentManager`.

## 2. Tests (`/tests`)

-   **Issue**: No dedicated unit tests for `ProjectCoordinator`.
-   **Proposed Change**: Create a new test file `tests/core_ai/dialogue/test_project_coordinator.py` with comprehensive unit tests for the `ProjectCoordinator`'s logic.

-   **Issue**: Limited integration test scenarios.
-   **Proposed Change**: Add more integration tests to `tests/integration/test_agent_collaboration.py` to cover edge cases and failure modes, such as failing subtasks and agent launch failures.

-   **Issue**: Lack of "real" integration tests.
-   **Proposed Change**: Create a new integration test file that uses a live (or mock) MQTT broker and actual agent processes to test the full end-to-end workflow. This would provide a higher level of confidence in the system's correctness.

## 3. Documentation (`/docs`)

-   **Issue**: The `PROJECT_OVERVIEW.md` file does not mention the "Trinity" model for backup and recovery.
-   **Proposed Change**: Add a section to `PROJECT_OVERVIEW.md` that explains the "Trinity" model, based on the information in `docs/technical_design/architecture/HAM_design_spec.md`.

-   **Issue**: "Conceptual" features are scattered across different documents.
-   **Proposed Change**: Create a new `ROADMAP.md` file in the `docs` directory to collect all the "conceptual" and "future" features into a single, consolidated view of the project's future direction.

## 4. Configuration

-   **Issue**: Redundancy in dependency management between `pyproject.toml` and `dependency_config.yaml`.
-   **Proposed Change**: Consolidate the dependency groups into `dependency_config.yaml` and either remove the `[project.optional-dependencies]` from `pyproject.toml` or generate it from `dependency_config.yaml`. The latter would be the preferred approach to maintain compatibility with standard Python tooling.
