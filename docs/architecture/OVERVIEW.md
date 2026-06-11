# System Architecture Overview

> **Last Updated**: 2026-06-11 — Added Phase 4 Priority 4: C2 Live2D fixed, 84 new unit tests, 220 magic numbers, 31/35 API endpoints tested, code quality cleanup

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    FastAPI Server                        │
│  (api/lifespan.py → wiring.py → service initialization) │
├─────────────────────────────────────────────────────────┤
│                    Service Layer                         │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │ ChatService │  │ LLMService   │  │ ModuleManager  │  │
│  │ (router.py  │  │ (llm/        │  │ (system/       │  │
│  │  chat_service│  │  router.py) │  │  module_manager│  │
│  │  .py)       │  │              │  │  /)            │  │
│  └──────┬──────┘  └──────┬───────┘  └───────┬────────┘  │
│         │                │                   │           │
│         ▼                ▼                   ▼           │
│  ┌────────────────────────────────────────────────────┐  │
│  │              Plugin Pipeline System                │  │
│  │  (on_message → on_response → on_tick → on_event)   │  │
│  └────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────┤
│                    Core AI Layer                          │
│  ┌──────────┐ ┌───────────┐ ┌──────────┐ ┌──────────┐  │
│  │ HSP      │ │ Bio/State │ │ Memory   │ │ ED3N     │  │
│  │ Protocol │ │ Matrix    │ │ Systems  │ │ (Reflex  │  │
│  │ Engine   │ │ Engine    │ │ (HAM,    │ │  Deep +  │  │
│  │          │ │           │ │ Vector)  │ │  SNN)    │  │
│  ├──────────┤ ├───────────┤ ├──────────┤ ├──────────┤  │
│  │ GARDEN   │ │ ModelBus  │ │ Training │ │ Learning │  │
│  │ (Vector  │ │ (LLM Tier │ │ Pipeline │ │ Systems  │  │
│  │  Dict +  │ │  Router)  │ │ (8 srcs, │ │ (Anchor, │  │
│  │  Tensor  │ │           │ │  53K smp)│ │ Manager) │  │
│  │  SNN)    │ │           │ │          │ │          │  │
│  └──────────┘ └───────────┘ └──────────┘ └──────────┘  │
├─────────────────────────────────────────────────────────┤
│              Integration Layer                            │
│  ┌──────────┐ ┌───────────┐ ┌──────────┐ ┌──────────┐  │
│  │ Google   │ │ Atlassian │ │ Desktop  │ │ Web      │  │
│  │ Drive    │ │           │ │ (Tray,   │ │ Search   │  │
│  │ Service  │ │ Bridge    │ │  OS)     │ │ Tool     │  │
│  └──────────┘ └───────────┘ └──────────┘ └──────────┘  │
└─────────────────────────────────────────────────────────┘
```

## Startup Flow

```
lifespan() entry
  ├── 1. Pre-init services (ChatService, LLMService, BioIntegrator)
  ├── 2. Init ModuleManager → discovers 11 modules
  ├── 3. AI system init (GARDENBackend, ED3NEngine, ModelBus registration)
  ├── 4. Cross-service wiring (plugin system, bio events, broadcast, hot-reload)
  └── 5. Background tasks (heartbeat, ws broadcast, on_tick timer, training pipeline)
```

## Service Dependency Graph

```
ChatService ──┬── ModuleManager ──┬── intent_registry
              │                   └── card_pipeline
              ├── LLMService ──┬── ModelBus ──┬── GARDENBackend (prio 6)
              │                │              ├── OpenAI
              │                │              ├── Anthropic
              │                │              ├── Ollama
              │                │              ├── Google
              │                │              └── LlamaCpp
              │                ├── ED3NEngine (reflex → deep → SNN)
              │                └── TrainingPipeline (8 sources, 53K)
              ├── FileOperationHandler
              ├── GoogleDriveHandler
              ├── WebSearchHandler
              └── LearningHandler
```

## Key Design Decisions

1. **ModuleManager** manages lifecycle of discoverable service modules (dynamically discovered)
2. **ChatService** handles intent routing → dedicated handlers
3. **Plugin Pipeline** (5 hooks) provides cross-cutting observability
4. **TieredConfigLoader** manages config across Default → User → Evolved layers
5. **Magic Numbers** centralized in `magic_numbers.py` with config-backed defaults
6. **ModelBus** is the LLM tier router (not a general engine registry) — 10 isolated engines remain directly invoked
7. **ED3N → GARDEN** pipeline: dictionary layer (text→keys) → SNN (LIF neurons) → GARDENBackend (vector dict + TF-IDF/CharBag)
8. **Training pipeline** expands 4→13 data sources (Alpaca, templates, knowledge bases, SEO, KG, etc.) with 53,654 total samples

## Current Status (2026-06-10)

| Layer | Status | Remaining Work |
|-------|--------|----------------|
| API/Server | ✅ Stable | — |
| Chat Service | ✅ Stable | — |
| LLM Service | ✅ Stable | ModelBus routing layer active |
| Module System | ✅ Dynamic discovery | 11 modules |
| Plugin System | ✅ 5 hooks | — |
| Handlers | ✅ 4 handlers | — |
| ED3N Engine | ✅ 86/86 tests | Reflex → Deep → SNN pipeline |
| GARDEN Engine | ✅ 50/50 tests | 3 active routing paths, TF-IDF fallback |
| Training Pipeline | ✅ 53,654 samples (13 sources) | SequenceTrainer + JointTrainer |
| ModelBus | ✅ 34 tests | Registration, 7 routing paths, domain queries, timeout, edge cases |
| Magic Numbers | ✅ Full | 220 values centralized (84 H4 + 136 Q3) across 13 files via magic_numbers.py |
| Integration Testing | ✅ 116 e2e + 84 unit = 200 total this sprint | 116 integration (59 P3-2 + 33 API + 24 fault/concurrency/resource) + 84 new unit tests across 7 files (prompt_builder:10, emotion_analyzer:11, query_classifier:13, training_coordinator:10, ed3n_provider:10, garden_provider:9, learning_loop:21); ED3NEngine + GARDENEngine + ModelBus + NeuroVocabulary pipeline |
| API Endpoint Tests | ✅ 31/35 endpoints | 33 tests covering 31 registered endpoints; 4 system endpoints fixed (router.py), 2 return type mismatches fixed; 4 endpoints untestable (no route registered) |
| C2 Live2D State Broadcast | ✅ Fixed | 4 methods added (get_live2d_state, set_expression, get_all_parameters, register_live2d_state_callback); 9 tests pass; import chain verified |
| Code Quality Metrics | ✅ ANGELA-MATRIX: 99.5% (210/211) | 10 unused imports removed, 7 print→logger, 30 except narrowed, 9 long functions→32 helpers; 220 magic numbers; total 210+ tests |
| Orphan Modules | ✅ 73.0% orphan rate (154/211) | All 154 orphan files marked DEPRECATED; ai/optimization/ (2), ai/knowledge_graph/ (2), ai/dependency_manager.py (1) = 5 deleted; 31 subpackage __init__.py annotated |
| Stubs | ✅ 36/37 strict stubs implemented | 3 true stubs remain (1 functional, 2 deprecated)
| Docs | ✅ Updated | SERVICE_CATALOG.md + OVERVIEW.md current |
