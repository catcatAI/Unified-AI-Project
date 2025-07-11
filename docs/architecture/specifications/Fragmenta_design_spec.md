# Fragmenta Meta-Orchestration System - Design Specification v0.2

> [!IMPORTANT]
> **Implementation Status (as of July 10, 2024):**
> The Fragmenta Orchestrator (`src/fragmenta/fragmenta_orchestrator.py`) has undergone significant refactoring and enhancement compared to the initial v0.1 conceptual design.
> Key implemented features in the current version (approximating v0.2 functionality) include:
> *   **Advanced State Management:** Utilizes `EnhancedComplexTaskState` and `EnhancedStrategyPlan` TypedDicts for robust tracking of complex, multi-step tasks.
> *   **Stage-Based Execution Model:** Plans are defined as a sequence of "stages," where each stage can contain one or more "processing steps."
> *   **Sequential and Foundational Parallel Execution:** Stages are executed sequentially. Steps within a single stage (if defined as a list) are dispatched for parallel execution, with a basic join mechanism before proceeding to the next stage.
> *   **HSP Task Lifecycle Management:** Full lifecycle support for HSP sub-tasks, including dispatch, result handling, configurable timeouts, and automated retries with exponential backoff.
> *   **Input/Output Mapping:** Steps can define `input_sources` to aggregate results from prior steps and `input_mapping` to construct parameters using basic f-string-like templating.
> *   **Core Orchestration Logic:** The `_advance_complex_task` method acts as the central state machine.
>
> However, many advanced features originally envisioned for Fragmenta (and some still listed in this document as future goals) remain conceptual or are pending full implementation. These include, but are not limited to:
> *   Sophisticated dynamic strategy generation and selection (beyond current simple rule-based determination).
> *   Advanced data pre-processing techniques (e.g., true semantic chunking).
> *   Complex graph-like dependency management between steps (beyond current stage-based model).
> *   Advanced result synthesis and post-processing methods.
> *   Comprehensive self-evaluation and meta-learning capabilities.
> *   Full hardware awareness and adaptive behavior.
>
> This document aims to reflect the current design direction and implemented foundations, while also retaining some of the original broader vision for context. Readers should refer to the source code and `docs/project/STATUS_SUMMARY.md` for the most up-to-date details on specific feature implementations.

## 1. Introduction

Fragmenta is envisioned as a meta-learning and task orchestration system for MikoAI. Its primary role is to enable MikoAI to handle complex tasks, manage large data inputs/outputs, and coordinate various specialized AI modules and tools. Fragmenta aims to provide a layer of advanced reasoning and strategy selection, breaking down complex problems into manageable sub-tasks and synthesizing results.

This document outlines the conceptual design (v0.2, reflecting recent enhancements) for Fragmenta, focusing on its core responsibilities, interactions, and particularly its approach to handling large data volumes and distributed task execution.

## 2. Core Responsibilities

Fragmenta will be responsible for:

1.  **Task Reception & Analysis:** Receiving complex task descriptions or user goals. Analyzing these to understand requirements, constraints, and expected outcomes.
2.  **Strategy Selection:** Based on the task analysis (including input data type and size), selecting an appropriate processing strategy. This might involve choosing specific models, tools, or data handling techniques (e.g., chunking).
3.  **Data Pre-processing (especially for large data):**
    *   **Input Analysis:** Detecting the type (text, file path, raw binary, structured data) and size of input data.
    *   **Chunking:** If data is large (e.g., long text, large files), splitting it into smaller, manageable chunks. This is typically defined as part of a `LocalStepDetails` of type `local_chunk_process`.
    *   **Metadata Generation:** Implicitly handled by storing chunk processing results or their IDs.
4.  **Sub-task Orchestration & Dispatch (Core of `_advance_complex_task`):**
    *   **Execution based on `EnhancedStrategyPlan`:** The orchestrator processes a plan composed of sequential "stages". Each stage can contain a single `ProcessingStep` or a list of `ProcessingStep`s intended for parallel execution.
    *   **Step Types (`ProcessingStep`):**
        *   **`LocalStepDetails`**: For tasks executed locally. This can be a call to a tool via `ToolDispatcher` (`local_tool`), direct LLM processing via `LLMInterface` (`local_llm`), or a specific chunk-processing loop (`local_chunk_process`) which itself might use tools or LLMs.
        *   **`HSPStepDetails`**: For tasks dispatched to external AIs via the Heterogeneous Synchronization Protocol (HSP).
    *   **Dependency Management (`input_sources`):** Each step can declare its input dependencies on the outputs of prior steps. The orchestrator ensures these dependencies are met before a step is executed.
    *   **Input/Output Mapping (`input_mapping`):** Allows flexible construction of a step's input parameters from various sources: outputs of prior steps, the original complex task input (`{$original_input}`), or the task description (`{$task_description}`). Uses a basic f-string-like templating mechanism.
    *   **HSP Task Lifecycle Management:** For `HSPStepDetails`, the orchestrator manages the full lifecycle:
        *   Dispatching the task request via `HSPConnector`.
        *   Tracking the task using a `correlation_id`.
        *   Handling asynchronous results via a callback mechanism (`_handle_hsp_sub_task_result`).
        *   Implementing configurable timeouts for responses.
        *   Implementing configurable retries with exponential backoff for dispatch failures, peer-reported errors, or timeouts.
    *   **Parallel Execution (Foundational):** When a stage in the `EnhancedStrategyPlan` contains a list of `ProcessingStep`s, the orchestrator attempts to dispatch all ready steps in that list concurrently (especially for non-blocking HSP tasks). It then waits for all steps in that parallel group to reach a terminal state (completed or failed with no retries left) before proceeding to the next stage (basic join mechanism).
    *   **State Tracking:** Utilizes `EnhancedComplexTaskState` to maintain the overall status of the complex task, the status of each individual step, intermediate results, and manages retry/timeout counters for HSP tasks.
5.  **Result Synthesis & Post-processing:**
    *   **Intermediate Results:** Results from each step are stored in `EnhancedComplexTaskState.step_results`.
    *   **Final Result:** The current implementation primarily considers the result of the final step in the plan as the overall result of the complex task. More sophisticated merging logic (as prototyped in `_merge_results`) for combining outputs from multiple branches or steps is a future enhancement for complex strategies.
    *   **Formatting:** Ensuring the final output is in the desired format would typically be the responsibility of the final step(s) in the plan or a dedicated formatting step.
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
    *   `step_results`: A dictionary mapping `step_id` to its processed result.
    *   `overall_status`: Tracks the high-level status of the complex task (e.g., "new", "planning", "executing", "waiting_for_hsp", "merging_results", "completed", "failed_plan", "failed_execution").
    *   `current_executing_step_ids`: List of step IDs currently dispatched or in active execution (especially relevant for parallel HSP tasks).
    *   `next_stage_index`: An integer pointing to the index of the current stage in the `strategy_plan.steps` list that is being evaluated or executed.
    *   `current_step_indices_in_stage`: A list of integers, used when a stage consists of a list of parallel steps. It tracks the indices of steps within that parallel list that are currently being processed or have been dispatched. (This field was noted in code but its exact usage in the current `_advance_complex_task` loop might need further clarification based on the implementation's iteration logic for parallel stages).

## 3. Key Interactions (Renumbered to 3.1)

Fragmenta will interact with:

*   **DialogueManager / Main Application Logic:** Receives complex task requests and (eventually) receives the final synthesized results.
*   **HAMMemoryManager (`ham_memory_manager.py`):**
    *   Potentially used to retrieve relevant past experiences or knowledge chunks that might inform strategy selection (though this is advanced and not current core logic).
    *   Can be used by local steps to store or retrieve data. The orchestrator itself primarily manages results in its `EnhancedComplexTaskState.step_results`.
*   **ToolDispatcher (`tool_dispatcher.py`):**
    *   Used by `LocalStepDetails` of type `local_tool` to execute specific tools.
*   **LLMInterface (`llm_interface.py`):**
    *   Used by `LocalStepDetails` of type `local_llm` or `local_chunk_process` to perform LLM-based operations.
*   **Other Core AI Modules (Emotion, Personality, Crisis):**
    *   These modules are passed during `FragmentaOrchestrator` initialization but are not directly used in the current core task execution loop (`_advance_complex_task`). Their integration would be part of more advanced dynamic strategy selection or context-aware processing in future iterations.
*   **Specialized Models (Future):**
    *   Future plans might involve direct interaction with specialized models beyond what's covered by `ToolDispatcher` or `LLMInterface`.
*   **ServiceDiscoveryModule (`service_discovery_module.py`):**
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

## 5. Orchestrator Interaction and API (v0.2 Focus)

> [!WARNING]
> The following sub-sections describe the conceptual API from the original v0.1 specification. This API is now largely outdated due to the significant refactoring of the `FragmentaOrchestrator`'s internal logic, which is now driven by the `EnhancedStrategyPlan` and the `_advance_complex_task` state machine.
>
> The primary external interaction point remains the `process_complex_task(task_description: Dict[str, Any], input_data: Any, complex_task_id: Optional[str] = None)` method. However, its internal operation and the way strategies are determined and executed have fundamentally changed.
>
> For an accurate understanding of the current capabilities and interaction patterns, please refer to:
> *   **Section 2: Core Responsibilities** (especially sub-section 4 on Sub-task Orchestration & Dispatch).
> *   **Section 3: Key Data Structures for Orchestration**.
> *   The source code: `src/fragmenta/fragmenta_orchestrator.py`.
>
> The old conceptual methods like `_analyze_input`, `_determine_processing_strategy` (in its simple v0.1 form), `_chunk_data`, `_dispatch_chunk_to_processing`, and `_merge_results` still exist in the code but their roles are now more as helper functions or simplified fallbacks within the new state-driven execution model, rather than direct top-level API components of a simple sequential process. The `_determine_processing_strategy` in particular is very basic in the current implementation and does not reflect advanced dynamic strategy selection.

**Original v0.1 Conceptual API (Largely Outdated):**

File: `src/fragmenta/fragmenta_orchestrator.py` (Note: Link refers to the file, but the class structure below is the v0.1 concept)

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

*   **Advanced Orchestration Architectures:**
    *   **Multi-Bus System and Tech Blocks:** A significant conceptual evolution involves redesigning Fragmenta around a multi-layered bus system (Technical, Module, and Semantic buses) that dynamically assembles fundamental "Tech Blocks" into modules and personalities. This aims for greater modularity, efficiency, and emergent capabilities. For a detailed exploration of this concept, see `docs/architecture/advanced_concepts/Fragmenta_Bus_Architecture.md`.
*   **Sophisticated Strategy Generation & Selection:** The current `_determine_processing_strategy` is very basic. Future work should focus on more dynamic and intelligent strategy generation, potentially using ML models, rule-based systems, or planning algorithms, and incorporating factors like hardware context, task type, and past performance.
*   **Advanced Dependency Management:** Evolve beyond the current stage-based dependencies to support more complex, graph-like dependency structures between steps.
*   **Dynamic Strategy Adjustment:** Allow the orchestrator to modify the execution plan mid-stream based on intermediate results, failures of certain paths, or changes in the environment.
*   **Cost, Resource, and Time Estimation:** Incorporate mechanisms to estimate the cost (e.g., tokens, API calls), computational resources, and time required for different strategies or steps, enabling more informed strategy selection.
*   **Enhanced Error Handling and Recovery:**
    *   Develop more sophisticated error recovery strategies beyond the current HSP retries (e.g., dynamic fallback to alternative capabilities or local methods, prompting for user intervention).
    *   Implement standardized error handling and retry mechanisms for `LocalStepDetails` comparable to what exists for HSP steps.
    *   Improve failure propagation logic, especially within parallel execution groups.
*   **Advanced Parallel Control:**
    *   Implement mechanisms to limit the concurrency of local tasks (e.g., thread pools, async task limits).
    *   Support more complex join conditions for parallel step groups beyond simply "all completed or failed."
    *   Explore dynamic identification of parallelizable steps within a task.
*   **Integration with `ContextCore`:** Deeply integrate with the proposed `ContextCore` (see `../blueprints/ContextCore_design_proposal.md`) for richer contextual information to inform strategy selection, step parameterization, and long-term learning from task executions.
*   **Sophisticated Input/Output Parameter Mapping:** Enhance the current basic f-string templating for `input_mapping` with more powerful tools like JSONPath, a small expression language, or conditional mapping logic for complex data transformations between steps.
*   **Comprehensive Result Synthesis:** Develop more advanced methods for `_merge_results` to synthesize final outputs from multiple, potentially diverse, intermediate step results, especially for branched or parallel execution plans.
*   **Plan Validation:** Implement more robust validation of `EnhancedStrategyPlan` structures before execution to catch errors in dependencies, input/output mappings, or step definitions.
*   **Improved Local Chunk Processing:** Refine the `local_chunk_process` step type to better manage inputs/outputs for chunk-wise operations and their subsequent aggregation.

This v0.2 specification, reflecting recent enhancements, provides a more robust and flexible orchestration foundation. Future work will focus on building more advanced intelligence and capabilities upon this base.
```
