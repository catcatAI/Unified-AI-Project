# Fragmenta System

## Overview

The Fragmenta system, primarily embodied by the `FragmentaOrchestrator` class (`fragmenta_orchestrator.py`), serves as a meta-orchestration layer within the Unified-AI-Project. Its core purpose is to manage and execute complex tasks that may require breaking down into smaller sub-tasks, coordinating multiple AI modules or tools, handling large data inputs/outputs, and potentially interacting with external AI capabilities via the Heterogeneous Synchronization Protocol (HSP).

Refer to `docs/architecture/Fragmenta_design_spec.md` for the broader conceptual vision and long-term goals for Fragmenta. This README focuses on the current implementation status.

## `FragmentaOrchestrator`

### Key Responsibilities (Current Implementation Focus)

1.  **Complex Task Processing (`process_complex_task`):**
    *   Receives a `task_description` (dict) and `input_data`.
    *   Manages a stateful context (`ComplexTaskState`) for each complex task, allowing for asynchronous operations.
2.  **Input Analysis (`_analyze_input`):**
    *   Performs basic analysis of input data to determine type and size, which informs strategy selection.
3.  **Strategy Determination (`_determine_processing_strategy`):**
    *   Selects a processing strategy based on the task description and input characteristics. Current strategies include:
        *   **HSP Dispatch:** If `task_description` specifies a `dispatch_to_hsp_capability_id`, Fragmenta will attempt to find this capability using the `ServiceDiscoveryModule` and dispatch the task to a peer AI via `HSPConnector`.
        *   **Local Tool Call:** If `task_description` requests a specific local tool.
        *   **Local Text Chunking & LLM Processing:** For large text inputs, chunks the data and processes chunks (e.g., summarization via `LLMInterface`).
        *   **Direct Local LLM Processing:** For smaller text inputs or other general tasks.
4.  **Local Data Handling:**
    *   **Chunking (`_chunk_data`):** Splits large text data into smaller, manageable chunks with overlap.
    *   **Local Dispatch (`_dispatch_chunk_to_processing`):** Sends data chunks or entire inputs to local processors (LLMs via `LLMInterface` or tools via `ToolDispatcher`). Stores intermediate results in `HAMMemoryManager`.
5.  **HSP Sub-Task Orchestration:**
    *   **Capability Discovery:** Interacts with the `ServiceDiscoveryModule` to find suitable HSP capabilities advertised by other AIs.
    *   **Dispatch (`_dispatch_hsp_sub_task`):** Constructs `HSPTaskRequestPayload` and uses `HSPConnector` to send sub-tasks to peer AIs. Tracks pending HSP tasks using correlation IDs.
    *   **Result Handling (`_handle_hsp_sub_task_result`):** Processes `HSPTaskResultPayload` messages received via `HSPConnector` callbacks. Updates the state of the parent complex task based on the outcome of the HSP sub-task.
6.  **Result Merging (`_merge_results`):**
    *   Combines results from processed local chunks (retrieved from HAM) or HSP sub-tasks into a final output. Supports basic merging strategies like string joining or returning single structured results.

### Dependencies

The `FragmentaOrchestrator` is designed to be initialized with instances of several core services:
*   `HAMMemoryManager`
*   `ToolDispatcher`
*   `LLMInterface`
*   `ServiceDiscoveryModule` (for HSP capability discovery)
*   `HSPConnector` (for HSP communication)
*   `PersonalityManager`, `EmotionSystem`, `CrisisSystem` (for contextual information, though less utilized in current core logic)
*   Configuration dictionary

### State Management

*   `_complex_task_context`: Stores the state (`ComplexTaskState`) of each ongoing complex task, keyed by a unique `complex_task_id`. This allows `process_complex_task` to be somewhat re-entrant and manage tasks that involve waiting for asynchronous HSP responses.
*   `_pending_hsp_sub_tasks`: Tracks HSP sub-tasks that have been dispatched but for which a result is still pending, keyed by their `correlation_id`.

### How It Works (Simplified Flow with HSP)

1.  `process_complex_task` is called with a task. A `ComplexTaskState` is created.
2.  `_determine_processing_strategy` is invoked. If an HSP strategy is chosen:
    *   `ServiceDiscoveryModule` is queried for the target capability.
    *   If found, `_dispatch_hsp_sub_task` sends an HSP task request. The `ComplexTaskState` status becomes `awaiting_hsp_result`, and a "pending" response is returned by `process_complex_task`.
3.  When the peer AI responds, `HSPConnector` routes the `HSPTaskResultPayload` to `_handle_hsp_sub_task_result`.
4.  `_handle_hsp_sub_task_result` updates the `ComplexTaskState` with the result and sets its status (e.g., to `hsp_result_received`).
5.  The system (or a subsequent call to `process_complex_task` for the same `complex_task_id`) then proceeds, potentially to the `_merge_results` step if all necessary data is available.
6.  `_merge_results` assembles the final output.
7.  `process_complex_task` returns the final "completed" status and result.

Local processing paths (tools, chunking, LLM) follow a more direct synchronous flow within `process_complex_task`, also utilizing `_dispatch_chunk_to_processing` and `_merge_results`.

### Current Status & Future Development

*   The current implementation provides foundational capabilities for local task processing (chunking, tool/LLM dispatch) and initial integration for dispatching tasks via HSP and handling their results.
*   The state management for complex, multi-step tasks involving a mix of local and asynchronous HSP operations is still evolving and could be made more robust.
*   Many advanced features from `Fragmenta_design_spec.md` (e.g., sophisticated strategy selection, dynamic adaptation, true parallel processing of sub-tasks, advanced result synthesis, self-evaluation) are future work.

This module is a key component for enabling more advanced, multi-faceted problem-solving by the AI.
