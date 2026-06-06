# System Architecture Overview

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
│  │ HSP      │ │ Bio/State │ │ Memory   │ │ Learning │  │
│  │ Protocol │ │ Matrix    │ │ Systems  │ │ Systems  │  │
│  │ Engine   │ │ Engine    │ │ (HAM,    │ │ (Anchor, │  │
│  │          │ │           │ │ Vector)  │ │ Manager) │  │
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
  ├── 3. Cross-service wiring (plugin system, bio events, broadcast)
  └── 4. Background tasks (heartbeat, ws broadcast, on_tick timer)
```

## Service Dependency Graph

```
ChatService ──┬── ModuleManager ──┬── intent_registry
              │                   └── card_pipeline
              ├── LLMService ──┬── OpenAI
              │                ├── Anthropic
              │                ├── Ollama
              │                ├── Google
              │                └── LlamaCpp
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

## Current Status (2026-06-06)

| Layer | Status | Remaining Work |
|-------|--------|----------------|
| API/Server | ✅ Stable | — |
| Chat Service | ✅ Stable | — |
| LLM Service | ✅ Stable | — |
| Module System | ✅ Dynamic discovery | — |
| Plugin System | ✅ 5 hooks | — |
| Handlers | ✅ 4 handlers | — |
| Magic Numbers | 🟡 Partial | ~43 values remaining |
| Stubs | ✅ 36/37 strict stubs implemented | 3 true stubs remain (1 functional, 2 deprecated)
| Docs | 🟡 In progress | See COMPREHENSIVE_AUDIT_REPORT_V2.md, PHASE_REVIEW5.md |
