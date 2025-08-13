# Fragmenta Orchestrator

## Overview

This document provides an overview of the `FragmentaOrchestrator` module (`src/fragmenta/fragmenta_orchestrator.py`). This module demonstrates a conceptual framework for processing complex tasks by retrieving, processing, and synthesizing multiple candidate memories from the Hierarchical Associative Memory (HAM) system.

## Purpose

The primary purpose of the `FragmentaOrchestrator` is to handle complex problems that cannot be solved by retrieving a single piece of information. Instead of looking for a single perfect answer, it is designed to gather multiple, partially-relevant memory "fragments" (hence "Fragmenta") and orchestrate their processing to build a more comprehensive solution. This represents a more advanced form of reasoning, moving from simple lookups to synthesis and multi-source information fusion.

## Key Responsibilities and Features

*   **Complex Task Processing (`process_complex_task`)**: The core method that takes a task description and input data.
*   **Multi-Candidate Memory Retrieval**: It queries the `HAMMemoryManager` with the `return_multiple_candidates=True` flag, which is a crucial feature for retrieving a list of relevant memories rather than just the single best match.
*   **Memory Fragment Processing**: It iterates through the retrieved candidate memories and applies a processing function to each one. In the current placeholder implementation, this is a simple text summarization of the memory's "gist".
*   **Result Synthesis**: It returns a structured list of the processed results, which in a more advanced implementation could be further synthesized into a final, coherent answer.

## How it Works

The `FragmentaOrchestrator` is invoked when a task is deemed too complex for a standard memory query. It uses the task description to formulate a broad query to the `HAMMemoryManager`. The HAM, in turn, returns a list of candidate memories that are potentially relevant to the task. The orchestrator then processes each of these memory fragments. The current implementation performs a simple summarization, but a more sophisticated version could involve:

*   Ranking the fragments by relevance.
*   Extracting key entities and relationships from each fragment.
*   Fusing the information to form a new, synthesized memory.
*   Identifying and resolving contradictions between fragments.

This approach allows the AI to tackle more nuanced and multifaceted problems by drawing on a wider range of its stored knowledge.

## Integration with Other Modules

*   **`HAMMemoryManager`**: This is the most critical dependency. The orchestrator's functionality is entirely dependent on the HAM's ability to perform multi-candidate queries and return rich memory objects.

## Code Location

`apps/backend/src/fragmenta/fragmenta_orchestrator.py`