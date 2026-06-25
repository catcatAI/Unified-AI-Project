# Angela AI Architecture

> **Source of Truth**: This document is the authoritative reference for Angela AI system architecture.
> **Last Updated**: 2026-06-25
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
│  │  Desktop App  │  │  Web         │  │  CLI / REPL  │  │  Pixel Angela│     │
│  │  (Electron)   │  │  Dashboard   │  │  (Python)    │  │  (PyQt6)     │     │
│  │  Live2D + WS  │  │  (Next.js)   │  │  HTTP + WS   │  │  Voxel + WS  │     │
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
│  ChatService | LLMService (Multi-LLM) | Vision/Audio Services                │
│  EconomyManager | AngelaTypes | MathVerifier | BrainBridge                   │
│                                                                              │
│  LAYER 3 — CORE INFRASTRUCTURE                                               │
│  HAM Memory Manager (ChromaDB) | Digital Life Integrator                     │
│  State Matrix 8D (αβγδ εθζη) | ConfigLoader (YAML 3-tier)                   │
│  Security A/B/C Keys | Neuroplasticity | Endocrine System | Metamorphosis     │
│                                                                              │
│  LAYER 2 — AI ENGINE                                                         │
│  ED3N (External Dictionary Decoupled Neural Network) | GARDEN (Lightweight)  │
│  GVV Pipeline | ThreeLayerVisual | Agents (Creative, Code, Data, etc.)       │
│  Alignment | Reasoning (Causal-Lightweight) | RAG Manager                    │
│  Personality Manager | Response Composer | Formula Engine                     │
│  (HSM, CDM, LifeIntensity, ActiveCognition, NonParadox)                      │
│                                                                              │
│  LAYER 1 — THEORETICAL FOUNDATION                                            │
│  HSM Formula (spacetime mapping) | CDM Dividend (cognitive dividend)         │
│  Life Intensity | Active Cognition | Non-Paradox Existence                    │
│  Precision Management | Maturity L0-L11 | Angela DNA (voxel skeleton)        │
│                                                                              │
│  CROSS-CUTTING — INTEGRATIONS                                                │
│  Atlassian (Confluence+Jira) | Google Drive (File Ops) | MCP Protocol        │
│  Firebase (Cloud) | Gemini OS Bridge | Rovo Dev Agent                        │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Module Dependency Graph

```
┌──────────┐     HTTP/WS     ┌──────────────────┐
│  Desktop  │◄──────────────►│  main_api_server  │
│  /Web     │                │  (FastAPI)        │
│  /CLI     │                │  ~314 lines       │
└──────────┘                 └─────────┬──────────┘
                                       │
                          ┌────────────┼────────────┐
                          ▼            ▼
                   ┌──────────┐ ┌──────────────┐
                   │api/router│ │  services/    │
                   │ (v1/*)   │ │ (chat, llm,  │
                   └────┬─────┘ │  vision,      │
                        │       │  multimodal)  │
                        │       └──────┬────────┘
                        ▼              ▼
                   ┌─────────────────────────┐
                   │       core/              │
                   │  (infrastructure + domain)│
                   │                         │
                   │ life │ bio │ engine     │
                   │ config │ security       │
                   │ state │ hardware        │
                   │ (8D matrix) │ (GPU/ACC)  │
                   └───────────┬─────────────┘
                               ▼
                   ┌────────────────────────────────────┐
                   │        ai/ (AGI/ASI engine)         │
                   │  ED3N | GARDEN | GVV                │
                   │  ThreeLayerVisual | memory (HAM)     │
                   │  agents | response | context         │
                   │  lifecycle | reasoning               │
                   └────────────────────────────────────┘
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
│   │       ├── services/      Business logic (chat, LLM, vision, audio)
│   │       ├── core/          Infrastructure (life, bio, engine, config, security, state)
│   │       ├── ai/            AGI/ASI engine (ED3N, GARDEN, memory, agents)
│   │       │   ├── multimodal/primitives/  GVV + composition image pipeline
│   │       │   ├── ed3n/                  External Dictionary Decoupled Net
│   │       │   └── garden/                Lightweight inference engine
│   │       ├── economy/       Economy system
│   │       ├── integrations/  External integrations (Google Drive, Atlassian)
│   │       └── system/        System-level utilities
│   ├── desktop-app/       Electron client with Live2D
│   ├── pixel-angela/      PyQt anatomical experiment frontend
│   ├── web-live2d-viewer/ Live2D web preview
│   ├── web-dashboard/     Next.js Web dashboard
│   ├── gemini-os-bridge/  OS automation microservice
│   └── training/          Model training directory
├── packages/
│   ├── cli/               Python CLI tools
│   ├── biology-core/      Python voxel DNA core
│   └── shared-js/         JS shared library (33 files)
├── configs/               Runtime configuration (angela_config, MCP, credentials)
├── docs/                  Documentation (50+ MD files)
├── scripts/               Utility scripts (50+ Python scripts)
├── tests/                 Test suite (~4,776 tests)
├── models/                Trained model artifacts (concept_space, GVV)
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
| Messaging | WebSocket | Pub/Sub |
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

> **Deprecated endpoints** (kept for backward-compat with deprecation warnings): `/generate-image`, `/recognize-image`, `/reconstruct-image`, `/interpolate-classes`, `/generate-image/status` → use `/api/v1/image/*` equivalents

### Key Metrics

- **Concept space accuracy**: 87% (PCA) vs 72% (neural net)
- **Source files**: 14 Python files in `ai/multimodal/primitives/`
- **Tests**: ~62 tests (38 Phase 1 + ~24 GVV)

---

## 8. 8D State Matrix (αβγδ εθζη)

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

## 9. Naming Conventions

| Language | Convention | Enforcement |
|----------|-----------|-------------|
| Python | snake_case, PascalCase classes, UPPER_SNAKE constants | Black + isort + mypy |
| JavaScript | camelCase, PascalCase classes, UPPER_SNAKE constants | ESLint + Prettier |
| API Routes | /api/v1/{resource}/{action} | FastAPI router prefixes |

## 10. Error Handling

- **Python**: Use `AngelaError` hierarchy; log with `logger.exception()` for unexpected errors
- **JavaScript**: try/catch with `throw new Error()`
- **API**: HTTPException with appropriate status codes (4xx for client, 5xx for server)

## 11. Version Governance

- Version is defined in 16+ locations (see `docs/IDEAL_ARCHITECTURE.md` §12.1)
- CI validates all version locations are in sync
- Only PATCH bumps allowed without human approval
- CHANGELOG must match real git tags (unreleased = `Internal/Unreleased`)

---

## 12. Relevant Documents

| Document | Purpose |
|----------|---------|
| `AGENTS.md` | Development guide, build/test/lint commands |
| `ANGELA_MATRIX_ANNOTATION_GUIDE.md` | Matrix annotation standards (L1-L6, αβγδ εθζη, A/B/C, L0-L11) |
| `docs/COMPREHENSIVE_REPAIR_ROADMAP.md` | Phased repair roadmap (Phase A-F) |
| `docs/OMISSIONS_CHECKLIST.md` | Known omissions and gaps tracker |
| `docs/COMPOSITIONAL_IMAGE_GENERATION_IMPLEMENTATION_SUMMARY.md` | GVV pipeline summary |
| `docs/06-project-management/plans/PHASE_REVIEW6.md` | 62.5-round dev log |
| `docs/06-project-management/plans/PROJECT_HONEST_AUDIT.md` | Honest project audit (~6.0/10) |
| `CHANGELOG.md` | Release history |
