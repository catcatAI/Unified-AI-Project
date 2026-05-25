# Angela AI Architecture

> **Source of Truth**: This document is the authoritative reference for Angela AI system architecture.
> **Last Updated**: 2026-05-26
> **Derived from**: `docs/FULL_ARCHITECTURE_ANALYSIS.md`

---

## 1. System Overview — 6-Layer Architecture

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                         ANGELA AI — Full System Architecture                  │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  LAYER 6 — EXECUTION / PRESENTATION                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                       │
│  │  Desktop App  │  │  Mobile App  │  │  CLI / REPL  │                       │
│  │  (Electron)   │  │ (ReactNative)│  │  (Python)    │                       │
│  │  Live2D + WS  │  │  QR + AES    │  │  HSP + HTTP  │                       │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘                       │
│         └─────────────────┼──────────────────┘                               │
│                    HTTP / WebSocket                                            │
│                                                                              │
│  LAYER 5 — API / TRANSPORT                                                   │
│  FastAPI (uvicorn) — main_api_server.py                                      │
│  Middleware: CORSMiddleware → SignedCommunicationMiddleware                   │
│  Routes: /api/v1/* (health, status, chat, session, actions)                  │
│  WebSocket: /ws/* (state sync, heartbeat, messaging)                         │
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
│  Alignment | Learning (Experience Replay) | Reasoning (Causal) | LIS (Immune)│
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
│  /CLI     │                │  1668 lines       │
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
                   │ autonomous │ hsp         │
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
      ├→ IntentRouter (Math | Code | General → LLM)
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

---

## 4. Directory Structure

```
unified-ai-project/
├── apps/
│   ├── backend/           Python FastAPI — primary backend
│   │   └── src/
│   │       ├── api/           Route handlers (v1/endpoints/*)
│   │       ├── services/      Business logic (chat, LLM, vision, audio, tactile)
│   │       ├── core/          Infrastructure (config, security, state, autonomous)
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
├── tests/                 Test suite (24 subdirectories)
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

## 6. 8D State Matrix (αβγδ εθζη)

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

- Version is defined in 13 locations (see `MASTER_CONSOLIDATED_PLAN.md` S1)
- CI validates all 13 version locations are in sync
- Only PATCH bumps allowed without human approval
- CHANGELOG must match real git tags (unreleased = `Internal/Unreleased`)

---

## 10. Relevant Documents

| Document | Purpose |
|----------|---------|
| `AGENTS.md` | Development guide, build/test/lint commands |
| `ANGELA_MATRIX_ANNOTATION_GUIDE.md` | Matrix annotation standards (L1-L6, αβγδ εθζη, A/B/C, L0-L11) |
| `MASTER_CONSOLIDATED_PLAN.md` | Active task plan (27 items, S/A/B/C graded) |
| `FULL_ARCHITECTURE_ANALYSIS.md` | Comprehensive architecture audit (1201 lines) |
| `CHANGELOG.md` | Release history |
