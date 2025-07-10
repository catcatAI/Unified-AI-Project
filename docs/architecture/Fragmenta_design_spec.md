# Fragmenta Meta-Orchestration System - Design Specification v0.1

## 1. Introduction

Fragmenta is envisioned as a meta-learning and task orchestration system for MikoAI. Its primary role is to enable MikoAI to handle complex tasks, manage large data inputs/outputs, and coordinate various specialized AI modules and tools. Fragmenta aims to provide a layer of advanced reasoning and strategy selection, breaking down complex problems into manageable sub-tasks and synthesizing results.

This document outlines the initial conceptual design (v0.1) for Fragmenta, focusing on its core responsibilities, interactions, and particularly its approach to handling large data volumes.

## 2. Core Responsibilities

Fragmenta will be responsible for:

1.  **Task Reception & Analysis:** Receiving complex task descriptions or user goals. Analyzing these to understand requirements, constraints, and expected outcomes.
2.  **Strategy Selection:** Based on the task analysis (including input data type and size), selecting an appropriate processing strategy. This might involve choosing specific models, tools, or data handling techniques (e.g., chunking).
3.  **Data Pre-processing (especially for large data):**
    *   **Input Analysis:** Detecting the type (text, file path, raw binary, structured data) and size of input data.
    *   **Chunking:** If data is large (e.g., long text, large files), splitting it into smaller, manageable chunks suitable for processing by underlying models or tools (e.g., respecting LLM context window limits).
    *   **Metadata Generation:** Creating metadata for chunks (e.g., sequence ID, source, relationship to other chunks).
4.  **Sub-task Orchestration & Dispatch:**
    *   Dispatching chunks or sub-tasks to appropriate specialized modules:
        *   `HAMMemoryManager` for memory recall or storage of intermediate results.
        *   `ToolDispatcher` for functional tools (math, logic, translation, etc.).
        *   `LLMInterface` for generative tasks, summarization, analysis of chunks.
        *   Future models (Code Model, Daily Language Model).
        *   Other `core_ai` components.
    *   **HSP Capabilities (New):** Dispatching sub-tasks to external AIs via HSP if a suitable capability is discovered using the `ServiceDiscoveryModule`.
    *   Managing dependencies and execution flow between sub-tasks:
        *   **State Management Core:** Uses `EnhancedComplexTaskState` to track overall task progress and `EnhancedStrategyPlan` to define the execution flow.
        *   **Plan Structure:** An `EnhancedStrategyPlan` consists of a list of stages. Each stage is either a single `ProcessingStep` (executed sequentially relative to other stages) or a `List[ProcessingStep]` (a group of steps intended for parallel execution within that stage).
        *   **Step Definitions:** `ProcessingStep` is a union of `HSPStepDetails` and `LocalStepDetails`, each capturing specific parameters, detailed status (e.g., `pending_dispatch`, `dispatched`, `awaiting_result`, `completed`, `failed_response`, `timeout_error`, `retrying` for HSP; `pending`, `in_progress`, `completed`, `failed` for local), results, and error information.
        *   **Dependency Management & I/O Mapping:**
            *   `input_sources`: Each step can define multiple input sources (e.g., `[{"step_id": "s1", "output_key": "summary"}, {"step_id": "s2"}]`) to aggregate data from prior completed steps.
            *   `input_mapping`: Rules (e.g., `{"prompt": "Data: {s1.summary} and {s2.full_result}. Original: {$original_input}"}`) define how aggregated inputs and original task data are mapped to the current step's parameters.
            *   This is handled by `_prepare_step_input` (gathers inputs, checks dependencies) and `_execute_or_dispatch_step` (applies mappings using f-string-like templating).
        *   **HSP Task Lifecycle:** For HSP steps, the system manages the full lifecycle, including dispatch, configurable retries with backoff on failure (dispatch error, peer error, timeout), and timeout detection.
    *   **Parallel Processing (Foundational):** The plan structure allows defining parallel groups of steps within a stage. The orchestrator (`_advance_complex_task`) dispatches all ready steps in such a group and waits for all ofthem to reach a terminal state (basic join mechanism) before proceeding to the next stage. Dynamic identification of parallelizable steps is future work.
5.  **Result Synthesis & Post-processing:**
    *   **Merging:** Combining results from all completed steps (local and/or HSP) into a coherent final output. This is handled by the `_merge_results` method using data from `EnhancedComplexTaskState.step_results`, which now aggregates results from a potentially multi-stage plan that may include parallel stages.
    *   **Formatting:** Ensuring the final output is in the desired format for the user or calling system (handled by the merging strategy or the final step of the plan).
6.  **Self-Evaluation & Learning (Future - Phase 4 Hooks):**
    *   (No change - Still Future) Receiving feedback on task outcomes.
    *   (No change - Still Future) Logging task performance and potentially requesting model/tool upgrades or fine-tuning via hooks.
    *   (No change - Still Future) Adapting strategies based on past performance (meta-learning aspect).
7.  **Cross-Domain Orchestration (Tripartite Model):** (No change - Still Conceptual) Explicitly manage and mediate interactions between MikoAI's internal state/reasoning, the local computer environment (files, system info, hardware), and external network resources (APIs, web data).
8.  **Multimodal Data Handling (Conceptual):** (No change - Still Conceptual) Design to eventually support and orchestrate tasks involving different data modalities (text, image, audio, structured data), including routing to appropriate specialized tools and fusing results. Initial implementations may be text-focused.

## 3. Key Data Structures for Orchestration (New Section)

The enhanced `FragmentaOrchestrator` relies on the following key `TypedDict` structures (defined in `fragmenta_orchestrator.py`) to manage complex tasks:

*   **`HSPStepDetails`**: Defines an HSP task step, including `capability_id`, `target_ai_id`, `request_parameters`, `input_sources`, `input_mapping`, and detailed status fields like `status`, `correlation_id`, `dispatch_timestamp`, `result`, `error_info`, `max_retries`, `retries_left`, `retry_delay_seconds`, `last_retry_timestamp`.
*   **`LocalStepDetails`**: Defines a local task step (tool, LLM, or chunk processing), including `tool_or_model_name`, `parameters`, `input_sources`, `input_mapping`, `status`, `result`, and `error_info`.
*   **`ProcessingStep`**: A `Union` of `HSPStepDetails` and `LocalStepDetails`.
*   **`EnhancedStrategyPlan`**:
    *   `plan_id`: Unique ID for the plan.
    *   `name`: Descriptive name for the strategy.
    *   `steps`: `List[Union[ProcessingStep, List[ProcessingStep]]]`. This is the core of the plan, representing a sequence of stages. Each stage is either a single `ProcessingStep` (for sequential execution relative to other stages) or a `List[ProcessingStep]` (a group of steps to be executed in parallel within that stage).
*   **`EnhancedComplexTaskState`**:
    *   `complex_task_id`: Unique ID for the overall complex task.
    *   `original_task_description`: The initial request.
    *   `original_input_data`: The initial input.
    *   `strategy_plan`: The `EnhancedStrategyPlan` being executed.
    *   `step_results`: A dictionary mapping `step_id` to its result.
    *   `overall_status`: Tracks the high-level status of the complex task (e.g., "new", "planning", "executing", "waiting_for_hsp", "completed", "failed_execution").
    *   `current_executing_step_ids`: List of step IDs currently dispatched (especially relevant for parallel HSP tasks).
    *   `next_step_to_evaluate_index`: Pointer to the current stage/step being evaluated in the plan's `steps` list.

## 3. Key Interactions (Renumbered to 3.1)

Fragmenta will interact with:

*   **DialogueManager / Main Application Logic:** Receives tasks from and returns final results to the primary interaction handler.
*   **HAMMemoryManager (`ham_memory_manager.py`):**
    *   To retrieve relevant past experiences or knowledge chunks.
    *   To store intermediate results of chunked processing, along with their metadata and relationships.
    *   To store the final synthesized result of a complex task.
*   **ToolDispatcher (`tool_dispatcher.py`):**
    *   To execute specific functional tools on data chunks or as part of a task plan.
*   **LLMInterface (`llm_interface.py`):**
    *   To perform operations like summarization, analysis, or generation on data chunks or for planning steps.
*   **Other Core AI Modules (Emotion, Personality, Crisis):**
    *   To inform strategy selection or to provide context for sub-tasks (e.g., tailoring chunk processing based on overall emotional context).
*   **Specialized Models (Future):**
    *   Code Model, Daily Language Model, Contextual LSTM Model.
*   **ServiceDiscoveryModule (`service_discovery_module.py` - New Interaction):**
    *   To query for available HSP capabilities from peer AIs that might fulfill a sub-task.
*   **HSPConnector (`hsp_connector.py` - New Interaction):**
    *   To send `HSPTaskRequestPayload` messages to peer AIs.
    *   To receive `HSPTaskResultPayload` messages (via registered callbacks).

## 4. Core Data Handling for Large Inputs/Outputs (v0.1 Conceptual Design)

This is a critical function of Fragmenta.

### 4.1. Input Analysis & Chunking

*   **Trigger:** When `process_complex_task` receives input data exceeding a configurable threshold (e.g., text length, file size).
*   **Type Detection:** Basic type detection (text, path to local file, potentially URL).
*   **Chunking Strategies (Placeholders - to be refined):**
    *   **Text:**
        *   Fixed-size chunks (e.g., N characters or N tokens, respecting sentence boundaries where possible).
        *   Semantic chunking (future, possibly using an LLM or NLP techniques to find logical breakpoints).
        *   Overlap between chunks might be necessary for some processing tasks to maintain context.
    *   **Files:**
        *   Strategy depends on file type.
        *   Text-based files (e.g., `.txt`, `.md`, `.py`): Apply text chunking.
        *   Binary files: May require specialized chunking or processing based on format (e.g., process parts of a large dataset, or not suitable for chunking by Fragmenta directly, requiring a specialized tool).
*   **Metadata:** Each chunk should be associated with metadata (e.g., `original_source_id`, `chunk_sequence_id`, `total_chunks`, `chunk_type`).

### 4.2. Distributed and Parallel Processing

*   Fragmenta now processes an `EnhancedStrategyPlan` which is a list of "stages". Each stage can be a single `ProcessingStep` (executed sequentially relative to the previous stage) or a `List[ProcessingStep]` (a group of steps executed in parallel).
*   **Parallel Execution:** For stages defined as a list of steps, the orchestrator attempts to dispatch all steps in that group whose dependencies (inputs from previous stages) are met. It then waits for all steps in this parallel group to reach a terminal state before proceeding to the next stage in the plan. HSP calls within such a group are inherently asynchronous.
*   **Sequential Execution:** Stages that are single `ProcessingStep` items are executed one after the other, once the preceding stage is fully complete.
*   **Dependencies & I/O:** Each step can define `input_sources` (listing source step IDs and optional output keys) and an `input_mapping` to construct its required parameters from the results of completed antecedent steps.
*   **Example Flow for Large Text Summarization (revised for potential plan structure):**
    1.  Fragmenta receives large text.
    2.  Analyzes size, determines chunking strategy.
    3.  Chunks text into `C1, C2, ..., Cn`.
    4.  For each chunk `Ci`: Dispatch to `LLMInterface` for summarization -> `Summary_Ci`.
    5.  Store `Summary_Ci` (perhaps in HAM with metadata).
    6.  Collect all `Summary_Ci`.
    7.  Dispatch collected summaries to `LLMInterface` for a final meta-summary.

### 4.3. Result Merging & Synthesis

*   Strategies depend on the task and chunk processing results:
    *   **Concatenation:** Simple joining of processed text chunks (if appropriate).
    *   **Summarization of Summaries:** As in the example above.
    *   **List Aggregation:** If each chunk produces a list of items (e.g., detected entities), merge these lists (handle duplicates).
    *   **Structured Data Aggregation:** If chunks produce structured data, merge them into a final structure.
*   The merging logic will be a key part of the strategy selected by Fragmenta.

## 5. `FragmentaOrchestrator` Class (Conceptual API - v0.1)

**Implementation Status Note (July 2024 - Further Updated):** The `FragmentaOrchestrator` has been significantly refactored. It now implements an enhanced state management system (`EnhancedComplexTaskState`, `EnhancedStrategyPlan` with `ProcessingStep` details) allowing for more complex task flows. Key improvements include:
*   **Stateful Step Execution:** The `_advance_complex_task` method processes tasks based on a plan composed of sequential stages, where each stage can be a single step or a group of steps intended for parallel execution. Basic dependency checking between steps is performed using `input_sources`.
*   **Parallelism Foundation:** The plan structure (`EnhancedStrategyPlan.steps` as `List[Union[ProcessingStep, List[ProcessingStep]]]`) now supports defining parallel groups of tasks. The orchestrator will attempt to dispatch all ready tasks in a parallel group and wait for their completion before proceeding (basic join).
*   **Improved I/O Mapping:** Steps now define `input_sources` (list of source step/output key) and `input_mapping` (to construct parameters for the current step). A basic f-string like templating for `input_mapping` has been implemented.
*   **HSP Task Integration:** Can dispatch HSP sub-tasks and receive their results asynchronously, with states updated within the new plan structure.
*   **Error Handling & Retries for HSP:** Basic error detection (dispatch errors, peer-reported failures, timeouts) and a configurable retry mechanism with backoff for HSP tasks are integrated with the new state machine.
*   **Rudimentary local processing** (chunking, LLM/tool dispatch, result merging) is maintained within this new stateful framework.

While these changes provide foundational support for parallelism and more explicit data flow, many advanced features from this design spec (e.g., sophisticated dynamic strategy selection for parallelism, complex input aggregation logic, semantic chunking, deep self-evaluation, full hardware awareness) remain conceptual or for future implementation. Refer to `docs/PROJECT_STATUS_SUMMARY.md` for current details.

File: `src/fragmenta/fragmenta_orchestrator.py`

```python
class FragmentaOrchestrator:
    def __init__(self, ham_manager, tool_dispatcher, llm_interface, personality_manager, emotion_system, crisis_system, config=None):
        # Initialize with references to other key MikoAI systems
        pass

    def process_complex_task(self, task_description: dict, input_data: any) -> any:
        """
        Main entry point for Fragmenta.
        - task_description: Structured info about the goal, constraints, desired output format.
        - input_data: Can be raw text, file path, structured data, etc.
        """
        # 1. Analyze input_data (type, size) -> _analyze_input()
        # 2. Determine processing strategy (chunking, tools, models, merging) -> _determine_processing_strategy()
        # 3. If chunking needed: _chunk_data()
        # 4. Loop/dispatch chunks for processing: _dispatch_chunk_to_processing() using HAM, Tools, LLM etc.
        # 5. Merge results: _merge_results()
        # 6. Return final synthesized output.
        return "Placeholder: Fragmenta processed complex task."

    # Internal placeholder methods
    def _analyze_input(self, input_data: any) -> dict: # Returns input_type, input_size, etc.
        return {"type": "unknown", "size": 0}

    def _determine_processing_strategy(self, task_desc: dict, input_info: dict) -> dict: # Returns strategy plan
        return {"name": "placeholder_strategy", "steps": []}

    def _chunk_data(self, data: any, strategy: dict) -> list: # Returns list of chunks
        return [data] # No chunking in placeholder

    def _dispatch_chunk_to_processing(self, chunk: any, strategy_step: dict) -> any: # Returns processed chunk
        return chunk # Identity processing

    def _merge_results(self, chunk_results: list, strategy: dict) -> any: # Returns final synthesized result
        return chunk_results[0] if chunk_results else None
```

## 6. Hardware Awareness and Adaptive Behavior (Conceptual)

A crucial long-term capability for Fragmenta and MikoAI is the ability to understand and adapt to the underlying hardware environment. This allows for optimized performance, resource utilization, and feature availability across diverse deployment platforms (e.g., powerful servers, desktop computers, mobile devices, embedded systems, conceptual nanomachines).

### 6.1. Hardware Capability Detection
*   **Mechanism:** The system (potentially a dedicated service or a utility within Fragmenta) would need methods to detect or infer capabilities of the current hardware:
    *   CPU (cores, speed, architecture).
    *   Available RAM.
    *   GPU (presence, type, VRAM) and other specialized AI accelerators (e.g., TPUs, NPUs).
    *   Network bandwidth and latency.
    *   Storage (available space, speed).
    *   Power status (e.g., battery vs. mains power for mobile/embedded).
*   **Granularity:** Detection might range from coarse (e.g., "server-class," "mobile-class") to fine-grained details.

### 6.2. Strategy Adaptation by Fragmenta
Fragmenta's `_determine_processing_strategy` method would be enhanced to consider these hardware capabilities:
*   **Model Selection:** Choose different sizes or types of models (e.g., a larger LLM on a server with a GPU vs. a smaller, quantized LLM on a mobile device).
*   **Parallelism & Concurrency:** Adjust the degree of parallelism for chunk processing or sub-task execution based on available CPU cores.
*   **Resource Allocation:** Limit memory usage or computational intensity for tasks on resource-constrained devices.
*   **Feature Toggling:** Enable or disable certain computationally expensive features or tools based on hardware. For example, high-resolution vision processing might only be enabled if a capable GPU is detected.
*   **Data Handling:** Adjust chunk sizes or data transfer methods based on memory and network conditions.
*   **Power Management:** On battery-powered devices, select less power-intensive strategies.

### 6.3. Runtime Profiles
*   The system might maintain different "runtime profiles" (e.g., "high_performance_server", "balanced_desktop", "low_power_mobile") that predefine sets of adaptive behaviors and model choices. Fragmenta could select a profile at startup or dynamically.

This is a complex area requiring significant research and development, likely evolving across multiple phases of MikoAI. Initial versions might rely on manually configured profiles or very basic detection.

## 7. Future Considerations (Renumbered)

*   More sophisticated strategy selection (potentially ML-based, incorporating hardware context, or allowing for more graph-like plans rather than the current list-of-stages). This includes dynamic generation of parallel execution groups.
*   Dynamic adjustment of strategies based on intermediate results or failures of alternative paths.
*   Cost/resource estimation for different strategies.
*   **Error Handling & Retries:** While basic error handling, timeouts, and retries for HSP tasks are implemented, more advanced error recovery strategies (e.g., dynamic fallback to different capabilities or local methods, user intervention prompts, more nuanced failure propagation in parallel groups) are future considerations.
*   **Parallelism:** The current plan structure supports defining parallel groups, and the orchestrator can dispatch them and wait for completion. However, more advanced parallel control (e.g., limiting concurrency of local tasks, complex join conditions beyond "all complete", dynamic identification of parallelizable steps) needs further design.
*   Integration with the "Contextual LSTM Model" or other advanced memory/context systems for richer strategy selection or chunk processing.
*   **Input Parameter Mapping:** The current f-string-like templating for `input_mapping` is basic. More sophisticated mapping logic (e.g., JSONPath, small expression language, conditional mapping) could be added for complex data transformations between steps.

This v0.1 specification, along with recent implementations, provides a stateful orchestrator with foundational support for sequential and basic parallel step execution, and improved HSP task management. Further enhancements will build upon this.
```
