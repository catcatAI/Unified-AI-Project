# Project Coordinator Detailed Workflow

## Overview

The `ProjectCoordinator` is a core component within the `DialogueManager`, responsible for handling complex, multi-step user requests that go beyond simple, single-turn interactions. It acts as the "brain" for project management, orchestrating various AI agents and services to achieve a user's goal.

## Core Responsibilities

1.  **Task Decomposition**: Breaking down a high-level user query into a structured plan of executable subtasks.
2.  **Task Sequencing**: Organizing subtasks into a dependency graph to ensure correct execution order.
3.  **Agent/Service Orchestration**: Dispatching subtasks to the appropriate specialized agents or services via the HSP network.
4.  **Dynamic Agent Provisioning**: Automatically launching necessary agents if they are not currently available.
5.  **Result Integration**: Synthesizing the results from all subtasks into a single, coherent, and user-friendly final response.
6.  **Continuous Learning**: Recording the entire project lifecycle (from query to final response) and feeding it to the `LearningManager` for future improvement.

## Detailed Workflow

The `ProjectCoordinator` follows a sophisticated, multi-phase process to handle a project:

### Phase 1: Decompose User Intent

-   **Trigger**: The `DialogueManager` delegates a complex query (e.g., prefixed with `project:`) to the `handle_project` method.
-   **Action**: The coordinator calls the `_decompose_user_intent_into_subtasks` method.
-   **Mechanism**: It queries a Large Language Model (LLM) with the user's request and a comprehensive list of all currently available agent capabilities (provided by the `ServiceDiscoveryModule`).
-   **Output**: The LLM returns a JSON array of subtask objects. Each object defines the `capability_needed` and the specific `task_parameters` for that step.

### Phase 2: Execute Task Graph

-   **Action**: The list of subtasks is passed to the `_execute_task_graph` method.
-   **Mechanism**:
    1.  A Directed Acyclic Graph (DAG) is constructed using the `networkx` library to represent the tasks and their dependencies. Dependencies are identified by looking for placeholders like `<output_of_task_1>` in the `task_parameters`.
    2.  The graph is topologically sorted to determine the correct, non-blocking execution order.
    3.  The coordinator iterates through the sorted tasks.

### Phase 3: Dispatch and Monitor Individual Subtasks

-   **Action**: For each task in the execution order, the `_dispatch_single_subtask` method is called.
-   **Mechanism**:
    1.  **Dependency Injection**: The `_substitute_dependencies` helper function replaces any dependency placeholders in the task's parameters with the actual outputs from previously completed tasks.
    2.  **Capability Search**: It queries the `ServiceDiscoveryModule` to find an active agent with the required capability.
    3.  **Dynamic Launch**: If no agent is found, it communicates with the `AgentManager` to launch the required agent script (e.g., `data_analysis_agent.py`). It then waits for the new agent to register its capabilities.
    4.  **HSP Dispatch**: A formal task request is sent to the target agent via the `HSPConnector`.
    5.  **Asynchronous Wait**: The coordinator then enters an asynchronous wait state for the task result, using an `asyncio.Event` tied to the request's `correlation_id`. The `handle_task_result` method will set this event upon receiving the result from the HSP network.

### Phase 4: Integrate and Respond

-   **Action**: Once all tasks in the graph are completed, the `_integrate_subtask_results` method is called.
-   **Mechanism**: It sends the original user query along with the complete set of subtask results to the LLM.
-   **Output**: The LLM generates a final, comprehensive response that synthesizes all the intermediate findings.

### Phase 5: Learn from Experience

-   **Action**: The `LearningManager` is invoked to process and store the entire project case.
-   **Mechanism**: A detailed record, including the initial query, the decomposed plan, all intermediate results, and the final response, is passed to the `learn_from_project_case` method. This allows the system to learn from its successes and failures.

## Key Interactions

The `ProjectCoordinator` is a central hub that interacts with several other core services:

-   **`MultiLLMService`**: Used for both task decomposition and final result integration.
-   **`ServiceDiscoveryModule`**: To find available agents and their capabilities.
-   **`AgentManager`**: To dynamically launch agents when needed.
-   **`HSPConnector`**: To send task requests to agents and receive results.
-   **`LearningManager`**: To store and learn from completed projects.
-   **`HAMMemoryManager`**: (Indirectly via LearningManager) To persist the learned knowledge.
-   **`PersonalityManager`**: To ensure the final response is consistent with the AI's current personality.
