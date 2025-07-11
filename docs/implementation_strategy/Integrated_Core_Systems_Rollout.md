# Integrated Core Systems Rollout Strategy

**Version:** 0.1
**Date:** July 11, 2024
**Authors:** Jules (AI Agent)
**Related Plans:**
*   `docs/implementation_guides/Fragmenta_Bus_Implementation_Plan.md`
*   `docs/implementation_guides/ContextCore_Implementation_Plan.md`
*   `docs/implementation_guides/Actuarion_Module_Implementation_Plan.md`
*   `docs/implementation_guides/Semantic_Tables_Implementation_Plan.md`
**Detailed Designs (Bus System):**
*   `docs/detailed_design/fragmenta_bus/tech_block_core_definitions.md`
*   `docs/detailed_design/fragmenta_bus/technical_bus_controller_and_library.md`
*   `docs/detailed_design/fragmenta_bus/module_bus_and_blueprints.md`
*   `docs/detailed_design/fragmenta_bus/semantic_bus_controller.md`

## 1. Introduction

This document outlines a high-level strategy for the integrated development and rollout of four core architectural systems proposed for the Unified-AI-Project:

1.  **Fragmenta Multi-Bus System & Tech Blocks (Bus System)**
2.  **ContextCore Module (Long-Term Memory & Context)**
3.  **Actuarion Module (Validation & Risk Assessment)**
4.  **Semantic Multiplication Tables (SMTs - Foundational Knowledge)**

The goal is to define a cohesive approach that considers their interdependencies, allows for parallel development where feasible, and enables a phased integration into the existing codebase. This strategy aims to transform the project's architecture systematically, leading to a more modular, intelligent, reliable, and evolvable AI system.

## 2. Core Systems Overview & Interdependencies

A brief recap of each system and its key relationships:

*   **Fragmenta Bus System:**
    *   **Role:** Provides a dynamic, modular execution framework using Tech Blocks, Module Blueprints, and a three-tiered bus (Technical, Module, Semantic).
    *   **Dependencies:** Relies on well-defined Tech Block interfaces.
    *   **Provides To:** A runtime environment for other systems (ContextCore, Actuarion) if they are implemented as Modules/Tech Blocks. Orchestrates calls to these systems.

*   **ContextCore Module:**
    *   **Role:** Manages long-term memory, contextual knowledge graphs, vector stores, and user profiles.
    *   **Dependencies:** Needs storage backends (local or cloud). Its ingestion pipeline might use Tech Blocks (e.g., for NLP processing) from the Bus System.
    *   **Provides To:** Rich contextual data and knowledge to the Bus System (for routing/planning), Actuarion (for validation), SMTs (as a potential storage/access layer), and general AI reasoning.

*   **Actuarion Module:**
    *   **Role:** Assesses semantic risk, logical coherence, and factual accuracy.
    *   **Dependencies:** Heavily relies on `ContextCore` for factual knowledge and policies, and `SMTs` for foundational rules/axioms. Its own assessors could be Tech Blocks executed by the Bus System.
    *   **Provides To:** Validation reports and risk scores to the Bus System (for decision making on AI outputs) and `DialogueManager`. Feedback to `LearningManager`.

*   **Semantic Multiplication Tables (SMTs):**
    *   **Role:** Store foundational, domain-specific knowledge.
    *   **Dependencies:** Need a management system (e.g., `SemanticTableManager`) which could be part of `ContextCore` or a standalone service. Parsers for SMT definition files.
    *   **Provides To:** Core axiomatic knowledge to `Actuarion` (for validation), `ContextCore` (as a type of stored knowledge), and reasoning components/Tech Blocks within the Bus System.

**Key Interdependency Summary:**

```mermaid
graph TD
    A[Fragmenta Bus System] --> B{Orchestrates/Uses};
    B --> C[ContextCore Module];
    B --> D[Actuarion Module];
    B --> E[SMT-Aware Modules/TechBlocks];

    C --> A; subgraph ContextCore Internals
        direction LR
        C_KG[Knowledge Graph]
        C_VS[Vector Store]
        C_DS[Document Store]
        F[Semantic Tables (SMTs)]
    end
    C --> D;
    F --> D;

    D --> A;

    subgraph External Systems
        G[DialogueManager]
        H[LearningManager]
    end
    A --> G;
    D --> G;
    C --> G;
    D --> H;
    C --> H;
```

*   The **Bus System** is central to execution.
*   **ContextCore** is central to knowledge storage and retrieval, including SMTs.
*   **Actuarion** consumes knowledge from ContextCore/SMTs and is invoked by the Bus/DialogueManager.

## 3. Proposed Phased Rollout Strategy

This strategy aims to build foundational layers first, allowing for incremental integration and parallel work where possible.

### Phase 0: Core Interfaces, Data Models & Initial Stubs (Preparation)

*   **Objective:** Define and agree upon the core Python interfaces (ABCs) and data structures (`TypedDict`s/Pydantic models) for ALL FOUR systems. This creates the "contracts" between them.
*   **Activities:**
    *   Finalize detailed designs for:
        *   Bus System: `TechBlock`, `TechBlockManifest`, `TechBlockInput/Output`, `ModuleBlueprint`, `ModuleBlueprintStep`, `InputSourceMappingValue`, `SemanticTaskRequest/Response`, `UserContext`. (Largely done in existing detailed designs).
        *   ContextCore: `ContextItem`, `KnowledgeGraphTriple`, `RetrievedContextChunk`, core `ContextCoreManager` API methods.
        *   Actuarion: `ValidationInput`, `ValidationIssue`, `ValidationReport`, `ValidationPolicy`, `ValidationRule`, core `ActuarionManager` API methods.
        *   SMTs: `SemanticTable`, `SMTEntry` variations, `SMTQuery/Result`, core `SemanticTableManager` API methods.
    *   Create basic Python stub files in `src/` for the main manager/controller classes and these data models.
*   **Parallel Work:** This phase is primarily design and definition, can be done by a focused team.
*   **Impact on `src/`:** New directories and files for interfaces and data models (e.g., `src/fragmenta_bus/common/`, `src/core_ai/memory/context_core/models.py`, etc.). No functional changes yet.

### Phase 1: Foundational Execution & Basic Context

*   **Objective:** Get a minimal, operational Technical Bus and Module Bus. Implement basic ContextCore storage and retrieval.
*   **Bus System Stream:**
    *   Implement `TechBlockLibrary`.
    *   Implement `TechnicalBusController` (focus on `execute_single_block` and simple `execute_block_sequence` without complex input mapping initially).
    *   Develop 2-3 simple, concrete Tech Blocks (e.g., `EchoBlock`, `StringConcatenateBlock`).
    *   Implement `ModuleBusController` with basic blueprint loading and sequential execution of steps (using the simplified Technical Bus sequence execution). Initial `input_data_mapping` can be direct passthrough or basic field selection.
*   **ContextCore Stream:**
    *   Implement `ContextCoreManager` with basic `add_item`, `get_item`.
    *   Implement local/simple backends: `NetworkXCKG` (or just dict-based graph initially), local `FAISSVectorStore` (or even simpler list-based semantic search), `SQLiteDocumentStore`.
    *   Basic `ContextIngestionPipeline` and `ContextQueryEngine` for these simple stores.
*   **Interdependencies:** Minimal at this stage. Bus can run without ContextCore, ContextCore can be developed independently.
*   **Impact on `src/`:**
    *   Functional implementations in `src/fragmenta_bus/` and `src/core_ai/memory/context_core/`.
    *   Refactor one very simple existing tool or service to be a Tech Block and a ModuleBlueprint.

### Phase 2: Semantic Layer & Knowledge Integration

*   **Objective:** Introduce the Semantic Bus. Integrate SMTs into ContextCore. Start using basic SMTs and ContextCore in Actuarion.
*   **Bus System Stream:**
    *   Implement `SemanticBusController` with basic intent mapping (e.g., rule-based or dict-based `IntentToBlueprintMapper`).
    *   `SemanticBusController` invokes `ModuleBusController`.
    *   Refine `ModuleBusController`'s `input_data_mapping` and `runtime_config_mapping` to handle more complex data construction from multiple sources (as designed in `module_bus_and_blueprints.md`).
*   **ContextCore & SMTs Stream:**
    *   Implement `SemanticTableManager` (or integrate SMT management into `ContextCoreManager`).
    *   Implement SMT parsers (YAML/JSON).
    *   Create and load a few foundational SMTs (e.g., common fallacies, basic project facts).
    *   `ContextCoreManager.get_relevant_context()` starts to include SMT results.
*   **Actuarion Module Stream:**
    *   Implement `ActuarionManager` and basic rule-based assessors (e.g., `FallacyDetector` using an SMT, keyword-based `HarmfulContentAssessor`).
    *   Actuarion queries `ContextCore` for relevant SMTs or basic facts.
*   **Interdependencies:**
    *   Semantic Bus needs Module Bus.
    *   Actuarion needs ContextCore (with SMTs).
    *   Bus System can start invoking simple Actuarion modules for validation.
*   **Impact on `src/`:**
    *   `DialogueManager` starts making initial calls to `SemanticBusController` for a subset of tasks.
    *   New `src/core_ai/knowledge/semantic_tables/` directory (if SMTs are separate from ContextCore).
    *   Functional `src/core_ai/validation/actuarion/`.

### Phase 3: Richer Functionality & Application Logic Migration

*   **Objective:** Enhance all four systems with more advanced features. Migrate more application logic (e.g., from `DialogueManager`, `LearningManager`) to use the new architecture.
*   **Bus System Stream:**
    *   Implement schema validation for Tech Block I/O and Module I/O using `jsonschema`.
    *   Develop more sophisticated Tech Blocks (e.g., wrapping existing services like `LLMInterface`, `ToolDispatcher` tools).
    *   Explore advanced `ModuleBlueprint` features (e.g., simple conditional steps if feasible).
*   **ContextCore Stream:**
    *   Implement `ContextSummarizer`.
    *   Develop context maintenance routines (archiving, temporal decay).
    *   Enhance `ContextQueryEngine` with hybrid retrieval and basic reranking.
    *   `LearningManager` and `ContentAnalyzerModule` start robustly ingesting into ContextCore.
*   **Actuarion Module Stream:**
    *   Implement model-based assessors (e.g., using LLMs for nuanced risk).
    *   Develop `FactVerificationAgent` with more robust `ContextCore` querying.
    *   Implement `ValidationPolicy` management.
*   **SMTs Stream:**
    *   Expand the SMT repository with more domains.
    *   Refine SMT query mechanisms.
*   **Interdependencies:** All systems are now more deeply interconnected.
*   **Impact on `src/`:**
    *   Significant refactoring of `DialogueManager` to delegate most capability execution to the Semantic Bus.
    *   `LearningManager` logic modified to write to/read from `ContextCore`.
    *   Old services increasingly wrapped as Tech Blocks.

### Phase 4: Optimization, Scalability & Full Integration

*   **Objective:** Focus on performance, scalability, robustness, and ensuring all core AI functionalities operate through the new integrated architecture.
*   **Bus System Stream:**
    *   Implement caching for Tech Blocks and Assembled Modules.
    *   Resource management for Tech Blocks.
    *   Advanced error handling and recovery within bus controllers.
*   **ContextCore Stream:**
    *   If needed, migrate to scalable backends (Neo4j, Pinecone, Elasticsearch).
    *   Optimize query performance and indexing.
*   **Actuarion Module Stream:**
    *   Refine assessor accuracy, reduce false positives/negatives.
    *   Improve explainability of reports.
*   **SMTs Stream:**
    *   Develop tools for SMT curation and validation.
*   **Interdependencies:** Focus on optimizing the interactions between the fully featured systems.
*   **Impact on `src/`:**
    *   Most original monolithic services and orchestrators are either replaced or become thin clients of the new systems.
    *   The AI's core reasoning and operational flow are primarily managed by the Bus System, informed by ContextCore/SMTs, and validated by Actuarion.

## 4. Parallel Workstreams

Once Phase 0 (Interfaces & Stubs) is complete, several workstreams can proceed with some degree of parallelism, coordinated by the defined interfaces:

*   **Bus System Core Development:** Technical Bus, Module Bus, basic Semantic Bus.
*   **ContextCore Backend & API Development:** Independent of bus implementation initially, focusing on storage/retrieval.
*   **SMT Definition & Parser Development:** Can proceed once SMT models are defined.
*   **Actuarion Assessor Development (Rule-based):** Can start once data models for validation are set.
*   **Tech Block Creation:** Simple, standalone Tech Blocks can be developed and unit-tested early.

## 5. Refactoring Existing Code (`src/`)

This rollout implies a significant, gradual refactoring of the existing `src/` codebase.

*   **`DialogueManager`:** Will shift from direct service calls to interacting primarily with the `SemanticBusController` and `ContextCoreManager`. Its internal state management might also be simplified as more context moves to `ContextCore`.
*   **`FragmentaOrchestrator`:** Its role will be progressively taken over by the Bus System. Initially, it might delegate tasks to the Semantic Bus. Eventually, its complex plan execution logic will be replaced by `ModuleBlueprint`s.
*   **`HAMMemoryManager`:** May be complemented or gradually replaced by `ContextCore`.
*   **`LearningManager` / `ContentAnalyzerModule`:** Will become primary data producers for `ContextCore`.
*   **`LLMInterface`, `ToolDispatcher`, other services:** Will be wrapped into or re-implemented as collections of Tech Blocks.
*   **Specialized Modules (e.g., in `src/modules_fragmenta/`):** Will be decomposed into Tech Blocks and defined as `ModuleBlueprint`s.

The guiding principle for refactoring should be to introduce the new systems and incrementally migrate functionality, ensuring backward compatibility or clear transition paths where possible.

## 6. Conclusion

This integrated rollout strategy provides a roadmap for transforming the Unified-AI-Project's architecture into a more powerful, modular, and intelligent system. By phasing development and focusing on clear interfaces, we can manage complexity and build towards a cohesive ecosystem where the Bus System, ContextCore, Actuarion, and SMTs work together seamlessly. This approach prioritizes establishing strong foundations before building more complex application logic on top.
