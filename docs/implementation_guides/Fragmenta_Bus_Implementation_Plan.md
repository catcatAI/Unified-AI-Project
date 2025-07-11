# Fragmenta Multi-Bus System & Tech Block Architecture: Implementation Plan

**Version:** 0.1
**Date:** July 11, 2024
**Authors:** Jules (AI Agent)

## 1. Objective

This document outlines the implementation plan for transitioning the Fragmenta system to a **Multi-Bus System & Tech Block Architecture**. The primary goal is to create a highly modular, dynamic, and efficient core architecture that enhances flexibility, scalability, code reusability, and the overall evolvability of the Unified-AI-Project. This new architecture will replace or significantly refactor the existing `FragmentaOrchestrator` and how modules are managed and interact.

## 2. Core Components & Definitions

### 2.1. Tech Blocks

*   **Definition:** The most granular, standardized, and reusable processing units within Fragmenta. Each Tech Block encapsulates a specific, well-defined AI capability or technical function. They are designed to be stateless or have their state managed externally by the bus system or a context module.
*   **Interface (`TechBlockInterface`):**
    *   `execute(input_data: TechBlockInput, context: Optional[Dict]) -> TechBlockOutput`: Executes the block's function.
    *   `get_manifest() -> TechBlockManifest`: Returns metadata about the block.
*   **`TechBlockInput` / `TechBlockOutput`:** Standardized `TypedDict` structures for data exchange.
*   **`TechBlockManifest` (`TypedDict`):**
    *   `id: str` (unique identifier, e.g., "llm.inference.gpt4o")
    *   `name: str` (human-readable name)
    *   `version: str`
    *   `description: str`
    *   `input_schema: Dict` (JSON schema for input_data)
    *   `output_schema: Dict` (JSON schema for output_data)
    *   `dependencies: List[str]` (e.g., other Tech Block IDs, external service IDs)
    *   `resource_requirements: Dict` (e.g., CPU, RAM, GPU, specific hardware flags)
*   **Examples:**
    *   `LLMInferenceBlock(model_id: str)`
    *   `TextSummarizationBlock(method: str)`
    *   `DataValidationBlock(schema: Dict)`
    *   `FileIOBlock(operation: str)`
    *   `HSPFactPublishBlock`
    *   `ToolExecutionBlock(tool_name: str)`

### 2.2. Tech Block Library

*   **Definition:** A central registry or repository for all available Tech Blocks.
*   **Functionality:**
    *   Registers new Tech Blocks (and their manifests).
    *   Retrieves Tech Blocks by ID.
    *   Manages versions and potentially dependencies between Tech Blocks.
    *   Could be implemented as a Python module with dynamic loading or a more sophisticated discovery service.

### 2.3. Bus Layers

#### 2.3.1. Technical Bus

*   **Responsibilities:**
    *   Manages the lifecycle of individual Tech Blocks (instantiation, execution, teardown).
    *   Handles low-level data flow and dependencies *between Tech Blocks within a single, coherent processing sequence defined by a ModuleBlueprint*.
    *   Optimizes resource allocation for Tech Blocks (e.g., GPU assignment, memory limits based on `resource_requirements`).
    *   Implements caching strategies for Tech Block outputs where appropriate.
*   **Key Operations:**
    *   `execute_tech_block_sequence(sequence_definition: List[Dict], initial_input: Any) -> Any`: Executes a predefined sequence of Tech Blocks.

#### 2.3.2. Module Bus

*   **Responsibilities:**
    *   Assembles "Modules" from Tech Blocks based on `ModuleBlueprint` definitions. A Module represents a higher-level, cohesive AI functionality (e.g., "SummarizeAndTranslateDocument", "UserQueryUnderstanding").
    *   Manages the lifecycle of these assembled Modules (instantiation, caching, versioning).
    *   Routes tasks (requests) to the appropriate assembled Module.
    *   Handles inter-Module communication if direct interaction is needed (though often Semantic Bus will mediate).
    *   Optionally, applies UID Persona signatures or context to Modules.
*   **Key Operations:**
    *   `assemble_module(blueprint_id: str, context: Optional[Dict]) -> AssembledModuleInstanceID`: Creates an instance of a module.
    *   `invoke_module(module_instance_id: ModuleInstanceID, task_data: Any) -> Any`: Executes a task on an assembled module.
    *   `get_module_interface(module_id: str) -> Dict`: Describes what a module can do.

#### 2.3.3. Semantic Bus

*   **Responsibilities:**
    *   The highest-level orchestration layer, interacting directly with the `DialogueManager` or other top-level system components.
    *   Interprets user intent or system goals into semantic tasks.
    *   Selects and deploys appropriate Modules (via the Module Bus) or sequences of Modules to fulfill these tasks.
    *   Manages the overall narrative flow, context, and UID persona state for an interaction.
    *   Synthesizes final outputs for the user.
*   **Key Operations:**
    *   `process_semantic_request(request: SemanticTaskRequest, user_context: UserContext) -> SemanticTaskResponse`: The main entry point for handling user interactions or system-driven tasks.

## 3. Proposed New Modules/Classes (in `src/fragmenta_bus/`)

*   `common/`:
    *   `tech_block_interface.py`: Defines `TechBlock` (ABC), `TechBlockInput`, `TechBlockOutput`, `TechBlockManifest`.
    *   `bus_message_types.py`: Defines `BusMessage`, `SemanticTaskRequest`, `SemanticTaskResponse`, `ModuleBlueprint`, `AssembledModuleInstanceID`, `UserContext`, etc.
*   `tech_blocks/`:
    *   `library.py`: `TechBlockLibrary` class.
    *   `standard_blocks/`: Directory for concrete Tech Block implementations (e.g., `llm_blocks.py`, `io_blocks.py`).
*   `technical_bus/`:
    *   `controller.py`: `TechnicalBusController` class.
    *   `resource_manager.py`: `TechBlockResourceManager`.
    *   `caching.py`: `TechBlockCache`.
*   `module_bus/`:
    *   `controller.py`: `ModuleBusController` class.
    *   `assembler.py`: `ModuleAssembler` (uses `ModuleBlueprint`s).
    *   `module_instance.py`: `AssembledModuleInstance` class.
*   `semantic_bus/`:
    *   `controller.py`: `SemanticBusController` class.
    *   `intent_parser.py`: `IntentParser` (to translate requests to module calls).
    *   `narrative_manager.py`: `NarrativeContextManager`.

## 4. Data Structures (Examples using `TypedDict`)

```python
from typing import TypedDict, List, Dict, Any, Optional, Literal

class TechBlockInput(TypedDict):
    data: Any
    config: Optional[Dict]

class TechBlockOutput(TypedDict):
    result: Any
    status: Literal["success", "error"]
    error_message: Optional[str]
    metadata: Optional[Dict]

class TechBlockManifest(TypedDict):
    id: str
    name: str
    version: str
    description: str
    input_schema: Dict # JSON Schema
    output_schema: Dict # JSON Schema
    dependencies: List[str]
    resource_requirements: Dict

class ModuleBlueprintStep(TypedDict):
    block_id: str
    config_override: Optional[Dict]
    input_source_step_ids: Optional[List[str]] # For piping output from previous steps
    input_mapping: Optional[Dict[str, str]] # Maps aggregated inputs to current block's input fields

class ModuleBlueprint(TypedDict):
    id: str
    name: str
    version: str
    description: str
    steps: List[ModuleBlueprintStep] # Sequence of Tech Blocks to execute
    input_schema: Dict
    output_schema: Dict

class SemanticTaskRequest(TypedDict):
    task_id: str
    intent: str
    data: Any
    user_id: str
    session_id: str
    priority: Optional[int]
```

## 5. API Definitions (Conceptual Methods)

*   **`TechBlockLibrary`:**
    *   `register_block(block_class: type[TechBlock])`
    *   `get_block_instance(block_id: str) -> TechBlock`
*   **`TechnicalBusController`:**
    *   `execute_block(block_id: str, input_data: TechBlockInput, context: Optional[Dict]) -> TechBlockOutput`
    *   `run_block_sequence(blueprint_steps: List[ModuleBlueprintStep], initial_payload: Any, context: Optional[Dict]) -> TechBlockOutput`
*   **`ModuleBusController`:**
    *   `load_blueprint(blueprint_id: str) -> ModuleBlueprint`
    *   `assemble_module_instance(blueprint_id: str, instance_id: Optional[str] = None) -> AssembledModuleInstanceID`
    *   `invoke_module(instance_id: AssembledModuleInstanceID, input_data: Any, context: Optional[Dict]) -> Any`
    *   `get_module_description(blueprint_id: str) -> Dict`
*   **`SemanticBusController`:**
    *   `handle_user_request(query: str, user_context: UserContext) -> str` (high-level example)
    *   `dispatch_semantic_task(task_request: SemanticTaskRequest) -> SemanticTaskResponse`

## 6. Core Logic/Algorithms

*   **Tech Block Execution:** Technical Bus instantiates/retrieves a Tech Block, validates input against its manifest, executes it, validates output, and handles caching.
*   **Module Assembly (Module Bus):**
    1.  Retrieves `ModuleBlueprint`.
    2.  For each step in the blueprint:
        *   The Module Bus requests the Technical Bus to prepare/execute the specified Tech Block.
        *   Handles data piping: output of one block becomes input for the next, potentially with transformation based on `input_mapping`.
    3.  The assembled sequence of operations defines the Module's behavior.
*   **Task Routing (Semantic Bus):**
    1.  Receives a `SemanticTaskRequest`.
    2.  Parses intent and identifies required capabilities.
    3.  Selects an appropriate `ModuleBlueprint` (or a sequence of them).
    4.  Instructs Module Bus to assemble and invoke the Module(s).
    5.  Manages context (e.g., conversation history, user profile) passed to Modules.
    6.  Processes Module output into a final user-facing response.

## 7. Integration Points & Refactoring Plan

This is a major architectural change and will require significant refactoring.

*   **`FragmentaOrchestrator` (`src/fragmenta/fragmenta_orchestrator.py`):**
    *   **Phase 1 (Coexistence):** The new Bus system will initially run alongside. The Orchestrator might delegate some sub-tasks to the Semantic Bus.
    *   **Phase 2 (Gradual Replacement):** Complex task plans in the Orchestrator will be redesigned as `ModuleBlueprint`s or sequences of Semantic Bus tasks. The Orchestrator's state management and step execution logic will be largely superseded by the Bus controllers.
    *   **End Goal:** `FragmentaOrchestrator` may be significantly simplified to be a thin client of the Semantic Bus or entirely replaced for its core orchestration duties.
*   **`DialogueManager` (`src/core_ai/dialogue/dialogue_manager.py`):**
    *   Will become a primary client of the `SemanticBusController`.
    *   Instead of directly calling various services (LLM, tools, learning), it will formulate `SemanticTaskRequest`s and send them to the Semantic Bus.
    *   Its role will shift more towards managing conversation state, user interaction nuances, and high-level dialogue strategy, relying on the Bus for capability execution.
*   **Existing Services (e.g., `LLMInterface`, `ToolDispatcher`, `HSPConnector`):**
    *   These will be wrapped as, or refactored into, one or more Tech Blocks.
    *   E.g., `LLMInterface` methods become different `LLMInferenceBlock` types. `ToolDispatcher` logic might be part of a `ToolExecutionCoordinatorBlock` or specific tool Tech Blocks.
*   **`src/modules_fragmenta/` & other specialized modules:**
    *   Existing modules will be decomposed into finer-grained Tech Blocks.
    *   Their current functionality will be redefined as `ModuleBlueprint`s that assemble these Tech Blocks.
*   **`ContextCore` (Future Module):**
    *   Would likely be implemented as a set of specialized Tech Blocks (e.g., `ContextStorageBlock`, `ContextRetrievalBlock`) and accessed via Modules assembled on the Module Bus. The Semantic Bus would manage the high-level context flow to and from ContextCore-powered Modules.
*   **`Actuarion Module` (Future Module):**
    *   Could be a Module assembled from Tech Blocks like `LogicValidationBlock`, `SemanticRiskAnalysisBlock`. It would be invoked by the Semantic Bus at appropriate points in a task.

## 8. Configuration (`configs/`)

*   New directory: `configs/fragmenta_bus/`
    *   `tech_block_manifests/`: JSON or YAML files for each `TechBlockManifest`.
    *   `module_blueprints/`: JSON or YAML files for each `ModuleBlueprint`.
    *   `bus_settings.yaml`: General settings for bus operations (e.g., cache policies, default resource limits, logging levels).
*   Existing configurations (e.g., `personality_profiles/`, `formula_configs/`) will still be used, but accessed via Tech Blocks or Modules that are designed to read them.

## 9. Basic Test Cases

*   **Tech Block Tests:**
    *   Unit test individual Tech Blocks: `test_llm_inference_block_success()`, `test_file_write_block_permissions_error()`.
    *   Test manifest validation for inputs/outputs.
*   **Technical Bus Tests:**
    *   Test execution of a sequence of Tech Blocks.
    *   Test resource allocation and error handling for blocks.
*   **Module Bus Tests:**
    *   Test `ModuleAssembler` correctly assembles a Module from a blueprint.
    *   Test `ModuleBusController.invoke_module()` with valid and invalid inputs.
    *   Test Module caching.
*   **Semantic Bus Tests:**
    *   Test `IntentParser` correctly maps a user query to a task.
    *   Test end-to-end processing of a `SemanticTaskRequest` involving multiple Modules.
    *   Test context management and propagation.
*   **Integration Tests:**
    *   Test `DialogueManager` interacting with `SemanticBusController`.
    *   Test refactored legacy services operating as Tech Blocks.

## 10. Potential Challenges & Mitigation

*   **Complexity:** The three-tier bus system is inherently complex.
    *   **Mitigation:** Phased rollout. Start with implementing the Technical Bus and a few core Tech Blocks. Incrementally build Module Bus and Semantic Bus. Clear interface definitions and comprehensive documentation are crucial.
*   **Performance Overhead:** Dynamic assembly and inter-bus communication can add latency.
    *   **Mitigation:** Efficient caching strategies for Tech Blocks and assembled Modules. Optimize hot paths in bus controllers. Asynchronous processing for non-critical tasks.
*   **Interface Standardization:** Defining robust and future-proof interfaces for Tech Blocks and Modules.
    *   **Mitigation:** Iterative design with community feedback. Use schema validation (JSON Schema) for inputs/outputs. Versioning for interfaces.
*   **Debugging & Tracing:** Understanding data flow and errors across multiple dynamic components.
    *   **Mitigation:** Implement comprehensive logging with correlation IDs across buses. Develop visualization or debugging tools for tracing task execution.
*   **Refactoring Effort:** Significant effort to refactor existing code into Tech Blocks and adapt to the new architecture.
    *   **Mitigation:** Prioritize refactoring of core modules first. Provide clear guidelines and tools for wrapping existing services as Tech Blocks.

## 11. Phased Implementation (High-Level)

1.  **Phase 1: Core Bus Infrastructure & Basic Tech Blocks.**
    *   Implement `TechBlockInterface`, `TechBlockLibrary`.
    *   Develop initial `TechnicalBusController`.
    *   Create a few essential Tech Blocks (e.g., basic LLM call, simple string manipulation).
2.  **Phase 2: Module Bus & Module Assembly.**
    *   Implement `ModuleBusController` and `ModuleAssembler`.
    *   Define simple `ModuleBlueprint`s using Phase 1 Tech Blocks.
    *   Begin refactoring one or two simple existing services into this new model.
3.  **Phase 3: Semantic Bus & Initial Integration.**
    *   Implement `SemanticBusController` and basic intent parsing.
    *   Integrate `DialogueManager` to make its first calls to the Semantic Bus for a limited set of tasks.
4.  **Phase 4: Wider Refactoring & Feature Migration.**
    *   Systematically refactor more existing modules and services into the Bus/Tech Block architecture.
    *   Expand the `TechBlockLibrary` and `ModuleBlueprint` repository.
5.  **Phase 5: Optimization & Advanced Features.**
    *   Focus on performance tuning, caching, resource management, and advanced bus features (e.g., dynamic routing, advanced error recovery).

This plan provides a roadmap for a transformative architectural upgrade, aiming to make Fragmenta a truly next-generation AI system.
