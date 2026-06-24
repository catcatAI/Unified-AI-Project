# Angela AI Architecture

> **Source of Truth**: This document is the authoritative reference for Angela AI system architecture.
> **Last Updated**: 2026-06-15
> **Derived from**: `docs/FULL_ARCHITECTURE_ANALYSIS.md`
> **完整感知・認知・執行架構**: [ANGELA_FULL_ARCHITECTURE.md](architecture/ANGELA_FULL_ARCHITECTURE.md)

---

## 1. System Overview — 6-Layer Architecture

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                         ANGELA AI — Full System Architecture                  │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  LAYER 6 — EXECUTION / PRESENTATION                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  Desktop App  │  │  Mobile App  │  │  CLI / REPL  │  │  Pixel Angela│     │
│  │  (Electron)   │  │ (ReactNative)│  │  (Python)    │  │  (PyQt6)     │     │
│  │  Live2D + WS  │  │  QR + AES    │  │  HSP + HTTP  │  │  Voxel + WS  │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
│         └─────────────────┼──────────────────┼─────────────────┘             │
│                    HTTP / WebSocket                                            │
│                                                                              │
│  LAYER 5 — API / TRANSPORT                                                   │
│  FastAPI (uvicorn) — main_api_server.py                                      │
│  Middleware: CORSMiddleware → SignedCommunicationMiddleware                   │
│  Routes: /api/v1/* (health, status, chat, session, actions)                  │
│  WebSocket: /ws/* (state sync, heartbeat, messaging, handshake required)       │
│  Session: TTLSessionManager (1h TTL, LRU, max 1000)                          │
│                                                                              │
│  LAYER 4 — APPLICATION SERVICES                                              │
│  ChatService | LLMService (Multi-LLM) | Vision/Audio/Tactile Services        │
│  EconomyManager | Wiring (DI) | AngelaTypes | MathVerifier | BrainBridge     │
│                                                                              │
│  LAYER 3 — CORE INFRASTRUCTURE                                               │
│  HAM Memory Manager (ChromaDB) | Digital Life Integrator | HSP Protocol      │
│  State Matrix 8D (αβγδ εθζη) | ConfigLoader (YAML 3-tier)                   │
│  Security A/B/C Keys | Neuroplasticity | Endocrine System | Metamorphosis     │
│                                                                              │
│  LAYER 2 — AI ENGINE                                                         │
│  10+ Agents (CreativeWriting, CodeUnderstanding, DataAnalysis, etc.)         │
│  Alignment | Learning (Experience Replay) | Reasoning (Causal-Lightweight)   │
│  RAG Manager | Personality Manager | Response Generator                      │
│  Formula Engine (HSM, CDM, LifeIntensity, ActiveCognition, NonParadox)       │
│                                                                              │
│  LAYER 1 — THEORETICAL FOUNDATION                                            │
│  HSM Formula (spacetime mapping) | CDM Dividend (cognitive dividend)         │
│  Life Intensity | Active Cognition | Non-Paradox Existence                    │
│  Precision Management | Maturity L0-L11 | Angela DNA (voxel skeleton)        │
│                                                                              │
│  CROSS-CUTTING — INTEGRATIONS                                                │
│  Atlassian (Confluence+Jira) | Google Drive (File Ops) | MCP Protocol        │
│  Firebase (Cloud) | OS Bridge | Rovo Dev Agent                               │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Module Dependency Graph

```
┌──────────┐     HTTP/WS     ┌──────────────────┐
│  Desktop  │◄──────────────►│  main_api_server  │
│  /Mobile  │                │  (FastAPI)        │
│  /CLI     │                │  ~314 lines       │
└──────────┘                 └─────────┬──────────┘
                                       │
                          ┌────────────┼────────────┐
                          ▼            ▼            ▼
                   ┌──────────┐ ┌──────────┐ ┌──────────┐
                   │api/router│ │services/ │ │wiring.py │
                   │ (v1/*)   │ │ (chat,   │ │ (DI)     │
                   └────┬─────┘ │  llm,   │ └──────────┘
                        │       │  vision) │
                        │       └────┬─────┘
                        ▼            ▼
                   ┌─────────────────────────┐
                   │       core/              │
                   │  (infrastructure + domain)│
                   │                         │
                   │ life │ bio │ engine │ hsp         │
                   │ config     │ security    │
                   │ state      │ hardware    │
                   │ (8D matrix)│ (GPU/ACC)   │
                   └───────────┬─────────────┘
                               ▼
                   ┌─────────────────────────┐
                   │        ai/               │
                   │  (AGI/ASI engine)        │
                   │  memory (HAM) | agents   │
                   │  learning | lis (immune) │
                   │  response | context      │
                   └─────────────────────────┘
```

---

## 3. Data Flow — Chat Request Lifecycle

```
User Input → Desktop App (Electron)
  → POST /api/v1/chat/unified (JSON)
  → FastAPI Router (CORS → SignedCommunicationMiddleware)
  → AngelaChatService
      ├→ StateMatrix8D.update() (αβγδ εθζη)
      ├→ IntentRegistry (Math | Code | General → LLM)
      ├→ ThetaRouter (meta-cognitive routing)
      ├→ HAMMemoryManager.store()
      ├→ LIS (ErrIntrospector) — detect bias
      ├→ AngelaLLMService
      │     ├→ pack 8D state → _construct_angela_prompt()
      │     ├→ LLM call (Ollama/GPT/Gemini)
      │     └→ unpack response
      ├→ ResponseComposer (merge LLM + formula + state)
      ├→ NeuroplasticityBridge (reinforce memory)
      └→ MetabolicHeartbeat.tick() (30s cycle)
  → WebSocket Push → Desktop App Renderer
      ├→ Live2DManager.updateExpression(emotion)
      ├→ StateMatrixDisplay (αβγδ visualization)
      └→ ChatPanel.showResponse(text)
```

> **ModuleManager**: The `ModuleManager` (in `core/system/module_manager/`) orchestrates lifecycle management
> for all discoverable service modules. It handles dynamic registration, dependency wiring, and graceful
> shutdown of modules such as ChatService, LLMService, BioIntegrator, and the Plugin Pipeline system.

---

## 4. Directory Structure

```
unified-ai-project/
├── apps/
│   ├── backend/           Python FastAPI — primary backend
│   │   └── src/
│   │       ├── api/           Route handlers (v1/endpoints/*)
│   │       ├── services/      Business logic (chat, LLM, vision, audio, tactile)
│   │       ├── core/          Infrastructure (life, bio, engine, config, security, state)
│   │       ├── ai/            AGI/ASI engine (memory, agents, learning, LIS)
│   │       ├── economy/       Economy system
│   │       ├── integrations/  External integrations (Google Drive, Atlassian)
│   │       └── system/        System-level utilities
│   ├── desktop-app/       Electron client with Live2D
│   ├── mobile-app/        React Native bridge
│   ├── pixel-angela/      PyQt anatomical experiment frontend
│   ├── web-live2d-viewer/ Live2D web preview
│   ├── gemini-os-bridge/  OS automation microservice
│   └── training/          Model training directory
├── packages/
│   ├── cli/               Python CLI tools
│   └── biology-core/      Python voxel DNA core
├── configs/               Runtime configuration (angela_config, MCP, credentials)
├── docs/                  Documentation
├── scripts/               Utility scripts
├── tests/                 Test suite (26 subdirectories)
├── reports/               Analysis reports
└── Root configs: package.json, pyproject.toml, docker-compose.yml, VERSION
```

---

## 5. Key Technologies & Patterns

| Component | Technology | Pattern |
|-----------|-----------|---------|
| API Framework | FastAPI (uvicorn) | Route-level Depends DI |
| Middleware | CORS → SignedCommunication | Chain of Responsibility |
| LLM Integration | Ollama / GPT / Gemini | Strategy pattern via LLMService |
| Memory | ChromaDB (HAM) | Layered memory hierarchy |
| State Matrix | 8D (αβγδ εθζη) | Observer → WebSocket push |
| Security | Key A/B/C encryption | AES + signed middleware |
| Configuration | YAML 3-tier (system/standard/MOD) | ConfigLoader |
| Messaging | WebSocket + HSP/MQTT | Pub/Sub |
| Desktop Renderer | Live2D Cubism SDK 5 R5 | WebGL2 |
| Package Manager | pnpm (workspace) | Monorepo |

---

## 6. GVV Image Generation Pipeline (New)

### Overview

The GVV (Geometric Vocabulary Vector) pipeline generates images from text using a multi-stage approach:

```
Text → CLIP (512-dim) → Concept Space (PCA, 87% accuracy) → 
ConceptMapper → GeometricVocabulary → InstanceOptimizer → Render
```

### Components

| Component | Location | Responsibility |
|-----------|----------|---------------|
| **ConceptMapper** | `ai/multimodal/primitives/concept_mapper.py` | Maps CLIP embeddings to shared concept space |
| **ConceptSpaceMapper** | `ai/multimodal/primitives/concept_space.py` | PCA-based projection with class centers |
| **GeometricVocabulary** | `ai/multimodal/primitives/geometric_vocabulary.py` | Stores primitive geometric patterns |
| **InstanceOptimizer** | `ai/multimodal/primitives/instance_optimizer.py` | Text-driven primitive optimization |
| **LearnableDecomposer** | `ai/multimodal/primitives/learnable_decomposer.py` | Neural image→primitive decomposition |
| **ThreeLayerVisual** | `ai/multimodal/three_layer_visual.py` | PCA encoder + nonlinear decoder (128-dim) |
| **Primitive Renderer** | `ai/multimodal/primitives/primitive_renderer.py` | PIL-based rendering of primitives |

### API Endpoints

| Method | Path | Function |
|--------|------|----------|
| POST | `/api/v1/image/generate` | Text-to-image generation |
| POST | `/api/v1/image/recognize` | Image recognition via concept space |
| POST | `/api/v1/image/reconstruct` | Image reconstruction via ThreeLayerVisual |
| POST | `/api/v1/image/interpolate` | Class interpolation |
| GET | `/api/v1/image/status` | Pipeline health check |

> **Deprecated endpoints** (kept for backward-compat): `/generate-image`, `/recognize-image`, `/reconstruct-image`, `/interpolate-classes`, `/generate-image/status`

### Key Metrics

- **Concept space accuracy**: 87% (PCA) vs 72% (neural net)
- **Source files**: 14 Python files in `ai/multimodal/primitives/`
- **Tests**: ~62 tests (38 Phase 1 + ~24 GVV)

---

## 7. 8D State Matrix (αβγδ εθζη)

| Dimension | Name | Description | Range |
|-----------|------|-------------|-------|
| α | Physiological | Energy, comfort, arousal, rest, vitality, tension | 0.0–1.0 |
| β | Cognitive | Curiosity, focus, confusion, learning, clarity, creativity | 0.0–1.0 |
| γ | Physical | Position, velocity, collision, gravity, friction | 0.0–1.0 |
| δ | Spiritual | Emotion, affect, personality, wisdom, empathy | 0.0–1.0 |
| ε | Environmental | Complexity, social density, information flow, time pressure | 0.0–1.0 |
| θ | Meta-cognitive | Novelty, mismatch doubt, creation urge, correction drive | 0.0–1.0 |
| ζ | Connectivity | Cross-module coupling, sync state, redundancy, mesh aggregation | 0.0–1.0 |
| η | Execution | Active modules, success rate, structural drift, resource efficiency | 0.0–1.0 |

---

## 7. Naming Conventions

| Language | Convention | Enforcement |
|----------|-----------|-------------|
| Python | snake_case, PascalCase classes, UPPER_SNAKE constants | Black + isort + mypy |
| JavaScript | camelCase, PascalCase classes, UPPER_SNAKE constants | ESLint + Prettier |
| API Routes | /api/v1/{resource}/{action} | FastAPI router prefixes |

## 8. Error Handling

- **Python**: Use `AngelaError` hierarchy; log with `logger.exception()` for unexpected errors
- **JavaScript**: try/catch with `throw new Error()`
- **API**: HTTPException with appropriate status codes (4xx for client, 5xx for server)

## 9. Version Governance

- Version is defined in 16+ locations (see `docs/IDEAL_ARCHITECTURE.md` §12.1)
- CI validates all version locations are in sync
- Only PATCH bumps allowed without human approval
- CHANGELOG must match real git tags (unreleased = `Internal/Unreleased`)

---

## 10. Relevant Documents

| Document | Purpose |
|----------|---------|
| `AGENTS.md` | Development guide, build/test/lint commands |
| `ANGELA_MATRIX_ANNOTATION_GUIDE.md` | Matrix annotation standards (L1-L6, αβγδ εθζη, A/B/C, L0-L11) |
| `MASTER_CONSOLIDATED_PLAN.md` | Consolidated master plan (S/A/B/C/D graded) |
| `COMPREHENSIVE_AUDIT_2026-06-25.md` | Latest comprehensive audit report |
| `IDEAL_ARCHITECTURE.md` | Target architecture blueprint |
| `REPAIR_ROADMAP.md` | Phased repair plan to reach ideal state |
| `CHANGELOG.md` | Release history |
