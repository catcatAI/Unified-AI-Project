# Fragmenta Orchestrator

## Overview

The `FragmentaOrchestrator` (`src/fragmenta/fragmenta_orchestrator.py`) is a key component within the Unified-AI-Project designed to **process complex tasks by intelligently retrieving and synthesizing information from multiple candidate memories**. It acts as a higher-level reasoning engine that leverages the AI's stored experiences to construct comprehensive responses or solutions.

This module is crucial for enabling the AI to handle queries that require more than a simple lookup or a single tool invocation, allowing it to draw connections and derive insights from its vast memory base.

## Key Responsibilities and Features

1.  **Complex Task Processing (`process_complex_task`)**:
    *   Receives a `task_description` (which may include `query_params`) and `input_data`.
    *   Formulates queries to the `HAMMemoryManager` to retrieve multiple relevant memories.
    *   Synthesizes information from these retrieved memories to generate a comprehensive result.

2.  **Memory Retrieval and Summarization**: 
    *   Utilizes the `HAMMemoryManager`'s `query_core_memory` method to fetch a list of candidate memories that are potentially relevant to the complex task.
    *   Performs a basic summarization of the `rehydrated_gist` from each retrieved memory, extracting key information.

## How it Works

The `FragmentaOrchestrator` acts as an intelligent aggregator. When presented with a complex task, it doesn't attempt to solve it directly. Instead, it queries the AI's `HAMMemoryManager` for all relevant pieces of information (memories). Once these candidate memories are retrieved, it processes them (currently by simple summarization) and combines the insights to form a coherent response or a step towards solving the complex task. This approach allows for a flexible and scalable way to handle intricate problems by breaking them down into memory retrieval and synthesis operations.

## Integration with Other Modules

-   **`HAMMemoryManager`**: The core dependency, providing the underlying memory storage and retrieval capabilities. The `FragmentaOrchestrator` relies heavily on HAM's ability to efficiently query and return relevant experiences.
-   **`ProjectCoordinator`**: Could potentially delegate complex, multi-faceted subtasks to the `FragmentaOrchestrator` when a deep synthesis of past memories is required.
-   **`LearningManager`**: Insights gained from the `FragmentaOrchestrator`'s processing could be fed back into the `LearningManager` to refine future memory storage and retrieval strategies.

## Code Location

`src/fragmenta/fragmenta_orchestrator.py`
