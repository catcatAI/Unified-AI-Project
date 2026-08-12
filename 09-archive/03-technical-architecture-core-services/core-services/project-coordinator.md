# ProjectCoordinator: High-Level Task Decomposition and Execution

## Overview

This document provides an overview of the `ProjectCoordinator` module (`src/core_ai/dialogue/project_coordinator.py`). This is a high-level coordinator responsible for decomposing complex user requests into a series of subtasks, executing them in a logical order, and integrating the results into a final, coherent response.

## Purpose

The `ProjectCoordinator` enables the AI to handle multi-step, complex projects that require the coordination of multiple tools, services, or specialized agents. It acts as an autonomous project manager, creating a plan, dispatching tasks to the appropriate resources, and synthesizing the final result for the user.

## Key Responsibilities and Features

*   **Project Decomposition (`_decompose_user_intent_into_subtasks`)**: Utilizes a Large Language Model (LLM) to analyze a complex user query and break it down into a structured plan. This plan is represented as a list of dictionaries, where each dictionary defines a subtask with its required capability and parameters.
*   **Task Graph Execution (`_execute_task_graph`)**:
    *   Constructs a directed acyclic graph (DAG) of the subtasks using the `networkx` library. This graph represents the dependencies between tasks (e.g., the output of one task is required as the input for another).
    *   Executes the tasks in a valid topological order, ensuring that all dependencies are met before a task is run.
    *   Dynamically substitutes the outputs of completed tasks into the parameters of subsequent tasks.
*   **Subtask Dispatch (`_dispatch_single_subtask`)**:
    *   For each subtask, it uses the `ServiceDiscoveryModule` to find a suitable capability (a service or agent) that can fulfill the task's requirements.
    *   If a required agent is not currently running, it attempts to launch it on demand using the `AgentManager`.
    *   It sends the task request to the selected capability via the `HSPConnector`.
*   **Result Integration (`_integrate_subtask_results`)**: After all subtasks have been successfully executed, it uses the LLM to synthesize the individual results into a single, comprehensive final response that directly addresses the user's original, high-level query.
*   **HSP Result Handling (`handle_task_result`)**: Asynchronously receives and handles incoming HSP task results. It stores the results and uses `asyncio.Event` to notify the appropriate waiting task that its result is ready.
*   **Learning from Projects**: After a project is completed, it has the capability to pass the entire case (including the user's query, the decomposed plan, the individual results, and the final response) to the `LearningManager`. This allows the AI to learn from its project management experiences and improve its future planning and execution capabilities.

## How it Works

When the `DialogueManager` identifies a project-level query, it delegates the request to the `ProjectCoordinator`. The coordinator's first step is to use an LLM to create a detailed plan, which takes the form of a task graph. It then begins to execute this plan, dispatching each subtask to the most appropriate service or agent via the Heterogeneous Service Protocol (HSP). It waits for the results of each subtask, respecting the dependencies defined in the graph. Once all results have been collected, it uses another LLM prompt to generate a final, integrated response for the user.

## Integration with Other Modules

The `ProjectCoordinator` is a highly integrated module that works in concert with many other core components:

*   **`DialogueManager`**: The entry point for all project-level requests.
*   **`MultiLLMService`**: Used for both decomposing the initial query into a plan and for integrating the final results into a coherent response.
*   **`ServiceDiscoveryModule`**: Essential for finding available capabilities to execute the subtasks.
*   **`HSPConnector`**: The communication backbone for sending task requests to other services and agents.
*   **`AgentManager`**: Used to launch specialized agents on demand when a required capability is not immediately available.
*   **`HAMMemoryManager`**: For storing and retrieving information related to the project.
*   **`LearningManager`**: To enable the AI to learn from its project management experiences.
*   **`PersonalityManager`**: To tailor the final response to align with the AI's current personality.
*   **`networkx`**: A key external library used for creating and managing the task dependency graph.

## Code Location

`src/core_ai/dialogue/project_coordinator.py`