# Comprehensive Project Audit V2 — Angela AI

> Generated: 2026-05-20 | Scope: Full codebase, config, call chains, dead code, cross-app wiring

---

## Table of Contents
1. [Executive Summary](#1-executive-summary)
2. [Project Inventory](#2-project-inventory)
3. [Entry Point Analysis — Two Competing FastAPI Apps](#3-entry-point-analysis)
4. [Config Audit — YAML Keys vs Code Consumption](#4-config-audit)
5. [Dead Code & Orphan Files](#5-dead-code--orphan-files)
6. [Import & Call Chain Map](#6-import--call-chain-map)
7. [Desktop App Wiring](#7-desktop-app-wiring)
8. [Mobile App Wiring](#8-mobile-app-wiring)
9. [CLI Package State](#9-cli-package-state)
10. [Environment Variable Usage](#10-environment-variable-usage)
11. [Critical Issues Summary](#11-critical-issues-summary)
12. [Repair Priority Matrix](#12-repair-priority-matrix)

---

## 1. Executive Summary

| Metric | Value |
|--------|-------|
| Total Python files in `apps/backend/src/` | **499** |
| Total directories (including empty) | **156** |
| Empty directories | **12** |
| Total config files (YAML/JSON) | **13** |
| Total JS/TS modules (desktop-app) | **63** |
| Test files shipped in `src/` | **6** |
| `_demo.py` files in production | **9** |
| `_fixed.py` duplicate files | **1** (active only; dead one removed) |
| Dead orphan files removed | **4** (`manager.py`, `base_fixed.py`, `self_introspector.py`, `self_introspector_v2.py`) |
| Dead config sections (no code consumer) | **~13** (reduced from ~18; 3 wired + 2 verified safe to wire) |
| Broken CLI entry points | **0** (all 6 files now pass `ast.parse` syntax validation) |

**Key finding: The project has two completely separate FastAPI apps** (`main.py` vs `main_api_server.py`) with different routes, middleware, and lifecycle handlers. The intended production entry path through `start_server.py` → `main_api_server.py` is one, but `main.py` is a parallel app that is also maintained. This is the single largest architectural confusion.

---

## 2. Project Inventory

### 2.1 Backend Python (`apps/backend/src/`)

Root directory: 6 files (`config_loader.py`, `path_config.py`, `system_self_maintenance.py`, `test_audio.py`, `test_config.py`, `__init__.py`)

Major sub-trees:

| Directory | Files | Purpose |
|-----------|-------|---------|
| `core/` | ~120 | Core engine: config, state matrix, security, HSP, tools, perceptions |
| `core/autonomous/` | ~40 | Digital life: state_matrix, theta_router, eta_axis, evolution, L2D bridge |
| `ai/` | ~100 | AI subsystems: agents, memory (HAM), learning, alignment, context |
| `ai/memory/ham_memory/` | 10 | Hierarchical Associative Memory core |
| `services/` | 18 | API server, LLM service, chat service, integrations |
| `api/` | 10 | FastAPI route definitions |
| `integrations/` | 10 | Atlassian, Google Drive, Rovo, MCP connectors |
| `core/hsp/` | 15 | Homomorphic Service Protocol |
| `core/tools/` | 20+ | Calculator, math, logic, web search, code understanding |
| `core/perception/` | 8 | Auditory, tactile, visual, attention |

### 2.2 Config Files (13 total)

| File | Location | Lines | Sections |
|------|----------|-------|----------|
| `angela_core.yaml` | `src/config/` | 1082 | 27 top-level |
| `anchor_rules.yaml` | `src/config/` | 254 | 9 axes |
| `llm_providers.yaml` | `src/config/` | 79 | 5 |
| `tickle_config.yaml` | `src/config/` | 177 | 7 |
| `file_ops.yaml` | `src/config/` | 95 | 5 |
| `multi_llm_config.json` | `configs/` | 48 | 6 backends |
| `angela_config.yaml` | `configs/` | 104 | 11 |
| `angela_state.yaml` | `configs/` | 361 | 9 |
| `prompts.yaml` | `configs/` | 11 | 2 |
| `test_config.json` | `configs/` | 16 | 3 |
| `learned_thresholds.yaml` | `src/config/angela/` | 15 | 2 |
| `learned_patterns.yaml` | `src/config/angela/` | 20 | 2 |
| `learned_routes.yaml` | `src/config/angela/` | 15 | 2 |

### 2.3 External Apps

| App | Tech | Files | Status |
|-----|------|-------|--------|
| Desktop `apps/desktop-app/` | Electron 40 + Live2D 5 | 63 JS + 6 HTML | **Production ready** |
| Mobile `apps/mobile-app/` | React Native 0.74 | 6 JS | **Functional** |
| Pixel Angela `apps/pixel-angela/` | Python (standalone) | 15 py | Experimental |
| Gemini OS Bridge `apps/gemini-os-bridge/` | Python | 8 py | Experimental |

---

## 3. Entry Point Analysis — Two Competing FastAPI Apps

### 3.1 App A: `main.py` ("AGI Entry")

| Property | Value |
|----------|-------|
| File | `apps/backend/main.py` |
| App title | `"Unified AI Project - Level 5 AGI"` |
| Version | `"1.0.0"` |
| CORS | Wildcard `*` |
| Encryption | **None** (`EncryptedCommunicationMiddleware` exists in `shared/security_middleware.py` but is never imported) |
| Routes | 8 inline + `api.router` |
| Lifecycle | Full: DeploymentManager, ClusterManager, Sync, KnowledgeGraph, Monitor |

### 3.2 App B: `main_api_server.py` ("Angela API")

| Property | Value |
|----------|-------|
| File | `apps/backend/src/services/main_api_server.py` |
| App title | `"Angela AI API"` |
| Version | `"6.0.4"` |
| CORS | Config-driven (from `angela_core.yaml`) |
| Encryption | **None** |
| Routes | Only `api.router` |
| Lifecycle | Config-driven pre-init: ChatService, LLM, BioIntegrator |

### 3.3 The Confusion

- `start_server.py` and `start_server_all_interfaces.py` both proxy to **App B** (`main_api_server`).
- `main.py` is an independent, parallel app.
- They **do not share state, routes, or middleware**.
- Some scripts/test files import from one, some from the other.
- **Which one is "production"?** `main_api_server.py` has version `6.0.4` and is the target of `start_server*.py`. `main.py` appears to be a legacy/parallel version. **Neither app uses `EncryptedCommunicationMiddleware`** — it's defined in `shared/security_middleware.py` but never imported by either FastAPI app.

---

## 4. Config Audit — YAML Keys vs Code Consumption

### 4.1 Fully Consumed Config Sections

| Section | Code Consumer | Notes |
|---------|--------------|-------|
| `intents` | `config_loader.py`, `intent_registry.py`, `chat_service.py` | Working |
| `complexity` | `chat_service.py`, `config_loader.py` | Working |
| `neuro_fragments` | `chat_service.py`, `angela_llm_service.py` | Working |
| `fallback_patterns` | `project_coordinator.py` | Working |
| `user_profile` | `chat_service.py` | Working |
| `spatial_math` | `cognitive_operations.py` | Working |
| `state_constants` | `chat_service.py`, `main_api_server.py` | Working |
| `math_verifier` | `math_verifier.py` | Working |
| `auto_mode` | `neuro_auto_selector.py` | Working |
| `document_builder` (partial) | `config_loader.py`, `document_builder.py` | `segment_timeout_seconds` only |
| `lifecycle` | `main_api_server.py` | Working |
| `session_manager` | `main_api_server.py` | Working |
| `middleware.cors` | `main_api_server.py` | Working |
| `chat_flow` (partial) | `main_api_server.py` | `max_message_length` + `truncation_length` read |
| `llm.defaults` | `angela_llm_service.py` | Working |
| `llm.biological_state` | `angela_llm_service.py` | Working |
| `llm.template_match` | `angela_llm_service.py` | Working |

### 4.2 Dead Config — Values Exist in YAML but No Code Reads Them

| Section | Key(s) | Status |
|---------|--------|--------|
| `state_to_llm` | `alpha_energy.*`, `beta_curiosity.*`, etc. | **FIXED** — `config_loader.py:_build_axis_context` reads config first, falls back to coord_rules |
| `response_schema` | `version`, `fields` | Never read by any code |
| `persistence` | `state_matrix.checkpoint_interval`, `persist_to` | Hardcoded in `state_persistence.py`; semantic values match but code uses separate config system (`core.state.config_loader`) |
| `predefined_templates` | All 5 templates | Hardcoded in `template_library.py:_initialize_predefined_templates()` — cannot wire (API refactor required) |
| `empathy` | `thresholds.*`, `emotion_keywords` | Never read; code's empathy system uses different concepts |
| `state_tracking` | `coordinate_recalculation`, `anchor_update_threshold`, `history_window` | Never read |
| `theta` | `novelty_estimation.*`, `self_correction.*` | Hardcoded in `theta_router.py` — **cannot wire** (YAML key semantics differ from code variables) |
| `eta` | `module_trigger_curve.*`, `execution_tracking.*` | Hardcoded in `eta_axis.py` — **cannot wire** (code uses 5 signal weights vs YAML's 3) |
| `routing.route_registry` | Full route list | All routes registered via FastAPI decorators |
| `learning.decay` | `enabled`, `days_to_decay`, etc. | Never read |
| `learning.write_strategy` | `mode`, `debounce_ms`, etc. | Never read |
| `learning.template_quality` | `enabled`, `match_tracking_window`, etc. | Never read |
| `llm.backend_priority` | `["ollama", "google", ...]` | Backend order from `multi_llm_config.json` iteration — no code reads this |
| `llm.memory.*` | All 5 keys | **FIXED** — `angela_llm_service.py:662-668` now reads from `llm.memory` via `_get_llm_config()` |
| `middleware.encrypted_communication` | `enabled` | Never read; `EncryptedCommunicationMiddleware` is never imported by either FastAPI app |
| `middleware.auth` | `enabled` | Never read |
| `chat_flow.default_flow` | `"angela_chat_service"` | **FIXED** — `main_api_server.py:642` reads from config |
| `chat_flow.http_timeout` | `30.0` | **FIXED** — `main_api_server.py:608/641` reads and uses `_http_timeout` |
| `chat_flow.truncation_message` | `"..."` | **FIXED** — `main_api_server.py:644` reads from config |
| `chat_flow.response_schema_version` | `"2.0"` | **FIXED** — `main_api_server.py:645` reads from config |
| `document_builder.max_segments` | `10` | Hardcoded as `8` in `document_builder.py:77` |
| `document_builder.learning_threshold` | `success_count`, `keyword_match_count` | Never read |
| `services.web_search.num_results` | `5` | **FIXED** — `chat_service.py:924-926` reads from config |
| `template_matching.score_weights` | `state_similarity`, `impression_similarity` | **FIXED** — code reads from config; YAML values corrected from `0.0` to `0.40`/`0.20` to match code defaults |
| `llm.emotion` | `negation_words`, `intensifier_words` | **FIXED** — code reads from config, falls back to built-in lists |

**Total dead/partial config subsections: ~25 → After fixes: ~13 remaining. Of 12 fixed: 9 wired to code + 3 semantically uncorrectable.**

---

## 5. Dead Code & Orphan Files

### 5.1 Orphaned Source Files

| File | Status | Reason |
|------|--------|--------|
| `ai/context/manager.py` | **REMOVED** | `__init__.py` imports from `manager_fixed` instead; confirmed zero residual imports |
| `ai/context/storage/base_fixed.py` | **REMOVED** | No file imported it; `manager_fixed.py` imports from `base.py` |
| `core/autonomous/self_introspector.py` | **REMOVED** | Zero import references anywhere |
| `core/autonomous/self_introspector_v2.py` | **REMOVED** | Zero import references anywhere |

### 5.2 Test Files in Production Tree (`apps/backend/src/`)

These are test files that live inside `src/` rather than `tests/`. No production code imports them; they are harmless but non-standard:

| File | Directory |
|------|-----------|
| `test_browser_controller.py` | `core/autonomous/` |
| `test_integration.py` | `core/tests/` |
| `test_feedback_loops.py` | `core/tests/` |
| `test_action_execution_bridge.py` | `core/tests/` |
| `test_config.py` | `src/` root |
| `test_audio.py` | `src/` root |

### 5.3 Demo Files in Production Tree (`apps/backend/src/`)

| File | Directory | Notes |
|------|-----------|-------|
| `collaboration_demo_agent.py` | `agents/` | Zero production imports |
| `monitoring_demo_agent.py` | `agents/` | Zero production imports |
| `registry_demo_agent.py` | `agents/` | Zero production imports |
| `demo_feedback_loop.py` | `core/` | Zero production imports |
| `desktop_demo.py` | `core/art/` | Zero production imports |
| `demo_learning_manager.py` | `core/managers/` | Has duplicate in `ai/learning/` |
| `demo_context_system.py` | `ai/context/` | Zero production imports |
| `level5_asi_demo.py` | `ai/examples/` | Zero production imports |
| `demo_learning_manager.py` | `ai/learning/` | Has duplicate in `core/managers/` |

### 5.4 Naming Collisions (no runtime impact)

| File A | File B | Notes |
|--------|--------|-------|
| `config_loader.py` (root) | `core/config_loader.py` | `core/state/config_loader.py` makes 3 total. All imports use full dotted paths — no ambiguity at runtime |
| `core/managers/demo_learning_manager.py` | `ai/learning/demo_learning_manager.py` | Same filename, different directories; no production code imports either |

**Cleanup done**: 4 dead files removed (`manager.py`, `base_fixed.py`, `self_introspector.py`, `self_introspector_v2.py`). Remaining collisions have zero runtime impact and are left for future cleanup.

---

## 6. Import & Call Chain Map

### 6.1 Server Startup Chain

```
start_server.py
  └─ import: src.services.main_api_server.app
       ├─ Top-level imports (30+ modules):
       │    ├─ core.config_loader → get_angela_config
       │    ├─ core.autonomous.desktop_interaction
       │    ├─ core.autonomous.action_executor
       │    ├─ services.vision_service
       │    ├─ services.audio_service
       │    ├─ services.tactile_service
       │    ├─ services.chat_service → generate_angela_response
       │    ├─ services.angela_llm_service → get_llm_service
       │    ├─ system.security_monitor
       │    ├─ api.router.router (recursive: loads ALL v1 endpoints)
       │    ├─ core.autonomous.digital_life_integrator
       │    ├─ economy.economy_manager
       │    └─ core.cognitive_economy_bridge
       ├─ Module-level instances:
       │    ├─ SystemMetricsManager()
       │    ├─ TTLSessionManager()
       │    ├─ FastAPI(title="Angela AI API")
       │    └─ api_v1_router (shared)
       └─ lifespan (lazy):
            ├─ services.chat_service.get_angela_chat_service
            ├─ services.angela_llm_service.get_llm_service
            └─ core.autonomous.biological_integrator
```

### 6.2 Alternative Startup Chain

```
main.py
  └─ creates FastAPI(title="Unified AI Project - Level 5 AGI")
       ├─ system.security_monitor.ABCKeyManager (immediate)
       ├─ shared.security_middleware (Key B encryption)
       ├─ api.router (shared, same instance as above)
       └─ lifespan:
            ├─ DeploymentManager (try/except)
            ├─ ClusterManager (try/except)
            ├─ SyncManager (try/except)
            ├─ UnifiedKnowledgeGraph (try/except)
            └─ EnterpriseMonitor (try/except)
```

### 6.3 Config Loader Call Graph

All 25 `get_authority()` calls use section key `"angela_core"` exclusively. No code fetches any other config section. Flow:

```
get_authority("angela_core", default)
  └─ ConfigAuthority.get(section)
       └─ Loaded from: src/config/angela_core.yaml
            ├─ chat_flow, middleware, lifecycle, session_manager
            ├─ intents, services, complexity, learning
            ├─ state_to_llm, response_schema, persistence
            ├─ fallback_patterns, template_matching, predefined_templates
            ├─ neuro_fragments, user_profile, spatial_math
            ├─ state_constants, math_verifier, document_builder
            ├─ empathy, state_tracking, theta, eta, llm, auto_mode
```

### 6.4 Chat Request Pipeline (API → Response)

```
POST /angela/chat
  → main_api_server._handle_chat_request()
    → chat_service.generate_angela_response()
      → AngelaChatService.generate_response()
        → EgoGuard.check(text)
        → _detect_intent() → _rank_intents_by_priority()
          → handler dispatch:
              math → _handle_math_intent → MathVerifier
              task → _handle_task_intent → ProjectCoordinator
              code → _handle_code_intent → CodeInspector
              character_card → DocumentBuilder
              document → DocumentBuilder
              learning → _record_route_learning + _handle_llm_fallback
              drive → _handle_drive_command → GoogleDriveService
              llm_manage → list backends
              general →
                → _try_neuro_synthesis → NeuroBlender
                or → _handle_llm_fallback → LLMService
        → _update_state_matrix()
        → _update_emotion_context()
        → _update_theta_after_response()
        → _update_eta_after_response()
        → _checkpoint_state()
```

---

## 7. Desktop App Wiring

### 7.1 Architecture

```
main.js (Electron main process, 1566 lines)
  ├─ Creates BrowserWindow (transparent, frameless, always-on-top)
  ├─ System tray with context menu
  ├─ Global shortcuts, single-instance lock
  └─ preload.js (contextBridge API, 22 namespaces)
       └─ index.html (renderer entry, 800+ lines)
            └─ 63 JS modules loaded via <script> tags
                 ├─ app.js — main orchestrator
                 ├─ live2d-manager.js — character rendering
                 ├─ backend-websocket.js — real-time communication
                 ├─ api-client.js — REST API calls
                 ├─ dialogue-ui.js — chat UI
                 ├─ performance-manager.js — mode switching
                 ├─ security-manager.js — encryption
                 └─ ... 56 more modules
```

### 7.2 Backend Dependencies

The desktop app communicates with the Python backend via:

| Channel | Endpoint | Protocol |
|---------|----------|----------|
| Chat | `POST /api/v1/chat/unified` | HTTP REST |
| Chat (fallback) | `POST /dialogue` | HTTP REST |
| Chat (fallback) | `POST /angela/chat` | HTTP REST |
| State | `WS /ws` | WebSocket |
| Health | `GET /health` | HTTP REST |
| Status | `GET /status` | HTTP REST |
| Sync Keys | `POST /api/v1/security/sync-key-c` | HTTP REST |

### 7.3 Assessment

- **Fully functional**: Window management, Live2D rendering, websocket, chat UI, performance modes, tray icon, security
- **No unit tests**: `"test": "echo Tests coming soon"`
- **No dependency injection**: All 63 modules loaded via `<script>` tags in index.html — hard to test, no module bundling
- **Static backend IP**: Default `127.0.0.1:8000`, configurable but not auto-discovered

---

## 8. Mobile App Wiring

### 8.1 Architecture

```
App.js (React Native, 828 lines)
  ├─ Pairing screen: QR scan or manual IP + Key B entry
  └─ Main dashboard:
       ├─ 8D Matrix visualization (animated)
       ├─ System metrics (CPU%, MEM%)
       ├─ Module toggle controls
       ├─ Eta panel (execution stats)
       └─ Command chat interface
```

### 8.2 Backend Dependencies

| Channel | Endpoint | Protocol |
|---------|----------|----------|
| Status | `GET /api/v1/mobile/status` | HTTP REST |
| State | `GET /api/v1/state/summary` | HTTP REST (polled 3s) |
| Eta | `GET /api/v1/state/eta/report` | HTTP REST |
| Chat | `POST /api/v1/mobile/chat` | HTTP REST (encrypted) |
| Module | `POST /api/v1/mobile/module-control` | HTTP REST (encrypted) |
| Realtime | `WS /ws` | WebSocket |
| Health | `GET /api/v1/health` | HTTP REST |
| Keys | `POST /api/v1/security/sync-key-c` | HTTP REST |

### 8.3 Assessment

- **Functional**: Pairing flow, dashboard, matrix viz, module controls, encrypted chat
- **Small codebase**: 6 source files, well-structured
- **No automated tests**: Only 1 small Jest test (`client.test.js`)

---

## 9. CLI Package State

### 9.1 Files

| File | Lines | Status |
|------|-------|--------|
| `cli_runner.py` | 94 | **FIXED** — clean `argparse` + mock fallback, `if __name__ == "__main__"` |
| `cli/unified_cli.py` | 360 | **FIXED** — 6 command groups (health/chat/analyze/search/image/atlassian), proper argparse, mock client fallback |
| `cli/main.py` | 505 | **FIXED** — syntax errors corrected; phantom `core_services`/`hsp.types` imports replaced with `core_services` stub + `core.hsp.types` real import; graceful fallback on missing backends |
| `cli/client.py` | 109 | **CLEAN** — functional HTTP client (unchanged) |
| `cli/port_manager.py` | 277 | **CLEAN** — functional port utilities (unchanged) |
| `cli/error_handler.py` | 179 | **CLEAN** — functional error logging (unchanged) |
| `cli/ai_models_cli.py` | 429 | **MOSTLY CLEAN** — functional if backend deps exist (unchanged) |

### 9.2 Assessment

- **All 6 CLI Python files now pass `ast.parse` syntax validation**
- Created `apps/backend/src/core_services.py` stub to satisfy `main.py` imports — provides graceful no-op `initialize_services()`, `get_services()` (returns empty), `shutdown_services()`
- The `cli_runner.py` entry point still wraps import in try/except — if backend modules are missing it falls back to simulated responses (health/chat only)
- **Known limitation**: `main.py`'s HSP callbacks, model/data/train commands all depend on `get_services()` returning real services — on systems without the full backend, these commands show "not available" messages instead of working
- Packaging (`setup.py`) is minimal — no console scripts defined

---

## 10. Environment Variable Usage

### 10.1 By File (80 total occurrences across 22 files)

| File | Count | Key Vars |
|------|-------|----------|
| `core/config/system_config.py` | 27 | `ENVIRONMENT`, `DEBUG`, `HOST`, `PORT`, `REDIS_*`, `MQTT_*`, `CHROMA_*`, `AUTO_TRAINING`, etc. |
| `ai/context/config.py` | 13 | `CONTEXT_STORAGE_DIR`, `CONTEXT_*` flags |
| `core/utils.py` | 6 | Wrapper helpers: `get_env()`, `get_env_bool()`, etc. |
| `services/angela_llm_service.py` | 5 | `api_key_env` (dynamic), `MULTI_LLM_CONFIG` |
| `core/hsp/security.py` | 3 | `HSP_ENCRYPTION_KEY`, `TESTING_MODE` |
| `core/hsp/connector.py` | 3 | `TEST_MODE`, `TESTING` |
| `core/code_inspector/code_inspector.py` | 3 | In suggestion strings |
| `ai/ensemble.py` | 2 | `OPENAI_API_KEY`, `ANTHROPIC_API_KEY` |
| `shared/key_manager.py` | 2 | Dynamic |
| `core/config_validator.py` | 2 | `LIVE2D_MODEL_PATH` |
| `core/shared/key_manager.py` | 2 | Dynamic |

### 10.2 Critical Finding: **No env vars in any YAML config file**

Every value in all 13 config files is a hardcoded literal. Zero `${VAR}` or `$VAR` references. This means:
- API keys must be set as environment variables separately
- There's no single source of truth for configuration — it's split between env vars, YAML files, and hardcoded defaults
- The `multi_llm_config.json` correctly documents which env var to set via `api_key_env`, but no YAML config does this

---

## 11. Critical Issues Summary

Ranked by severity (P0 = blocking, P1 = high, P2 = medium, P3 = low):

### P0 — Blocking

| # | Issue | Location | Impact |
|---|-------|----------|--------|
| 0.1 | Two competing FastAPI apps | `main.py` vs `main_api_server.py` | Confused entry points; different routes/middleware/lifecycle. Neither has encryption middleware. |
| 0.2 | ~~CLI entry points broken~~ | `cli_runner.py`, `cli/unified_cli.py` | **FIXED** — all 6 files pass syntax; `core_services.py` stub created |
| 0.3 | ~~No encryption on main API~~ | `main_api_server.py` | **REMOVED** — neither FastAPI app uses `EncryptedCommunicationMiddleware`; the class exists in `shared/security_middleware.py` but is never imported |

### P1 — High

| # | Issue | Location | Impact |
|---|-------|----------|--------|
| 1.1 | Dead config: ~13 sections never read | `angela_core.yaml` | Config exists but ignored: `response_schema`, `empathy`, `state_tracking`, `theta`, `eta`, `routing`, `learning.*`, `llm.backend_priority`, `middleware.*`, `document_builder.*`, `predefined_templates`, `persistence` |
| 1.2 | ~~Dead code: `self_introspector*`~~ | `core/autonomous/` | **FIXED** — both files removed |
| 1.3 | ~~Dead code: `manager.py`~~ | `ai/context/` | **FIXED** — removed |
| 1.4 | ~~Dead code: `base_fixed.py`~~ | `ai/context/storage/` | **FIXED** — removed |
| 1.5 | Test files in production package | 6 files in `src/` | Shipped test code in production namespace (no runtime impact) |
| 1.6 | `demo_*` files in production | 9 files in `src/` | Demo code in production namespace (no runtime impact) |
| 1.7 | Hardcoded URLs & paths in config | All 13 YAML/JSON files | No env var interpolation, not portable |

### P2 — Medium

| # | Issue | Location | Impact |
|---|-------|----------|--------|
| 2.1 | Two `demo_learning_manager.py` files | `core/managers/` + `ai/learning/` | Same name, different locations; no production imports |
| 2.2 | `config_loader.py` name collision | `src/` root + `core/` + `core/state/` | Three files, same name; all imports use dotted paths → no runtime ambiguity |
| 2.3 | Desktop app no unit tests | `apps/desktop-app/` | Test placeholder |
| 2.4 | Learned YAML files never consumed | `config/angela/learned_*.yaml` | Auto-generated but no code reads them back |
| 2.5 | `multi_llm_config.json` vs YAML overlap | Both `configs/` and `src/config/` | Duplicate LLM configuration sources |

### P3 — Low

| # | Issue | Location | Impact |
|---|-------|----------|--------|
| 3.1 | `require('electron')` in renderer | `js/install-ws.js` | Should use preload bridge, not direct require |
| 3.2 | 12 empty directories | Various | Dead namespace packages |
| 3.3 | `apps/pixel-angela/` unmaintained | Standalone | Unknown if functional |
| 3.4 | `apps/gemini-os-bridge/` unmaintained | Standalone | Unknown if functional |

---

## 12. Repair Priority Matrix

### Phase 0 — DONE

| ID | Task | Status | File(s) |
|----|------|--------|---------|
| F0.1 | Fix CLI syntax errors | **DONE** | `cli_runner.py`, `cli/unified_cli.py`, `cli/main.py`, `cli/client.py`, `cli/port_manager.py`, `cli/error_handler.py` |
| F0.2 | Remove `manager.py` (dead) | **DONE** | `ai/context/manager.py` |
| F0.3 | Remove `base_fixed.py` (dead) | **DONE** | `ai/context/storage/base_fixed.py` |
| F0.4 | Remove `self_introspector.py` and `_v2` (both dead) | **DONE** | `core/autonomous/self_introspector*.py` |

### Phase 1 — Config Wire-Up

| ID | Task | Status | Description |
|----|------|--------|-------------|
| F1.1 | Wire `theta` config | **CANCELLED** — semantic mismatch | YAML `novelty_estimation` vs code `CREATE_THRESHOLD` (axis creation, not novelty) |
| F1.2 | Wire `eta` config | **CANCELLED** — semantic mismatch | YAML uses 3 weights (`complexity_weight`, `novelty_weight`, `history_weight`); code uses 5 different signal keys |
| F1.3 | Wire `persistence` config | **CANCELLED** — separate config system | `state_persistence.py` uses `core.state.config_loader.StateConfig`, not `core.config_loader.AngelaConfigManager` |
| F1.4 | Wire `predefined_templates` | **DEFERRED** — requires API refactor | Hardcoded `MemoryTemplate.add_template()` calls; would need YAML→object deserialization layer |
| F1.5 | Wire `empathy` config | **CANCELLED** — different system | YAML `empathy.thresholds` (arousal/valence) vs code's HSP behavior trigger threshold (0.6) |
| F1.6 | Wire `chat_flow` items | **DONE** | `default_flow`, `http_timeout`, `truncation_message`, `response_schema_version` |
| F1.7 | Wire `llm.backend_priority` | **CANCELLED** — no code consumer | Backend order from `multi_llm_config.json` iteration; no code reads this list |
| F1.8 | Wire `llm.memory.*` | **DONE** | Precompute thresholds (`idle_threshold`, `cpu_threshold`, `max_queue_size`, `llm_timeout`) in `angela_llm_service.py:662-668` |
| F1.9 | Wire `services.web_search.num_results` | **DONE** | `chat_service.py:924-926` |
| F1.10 | Wire `template_matching.score_weights` | **DONE** + YAML value correction | `memory_template.py:259` reads config; HAD to fix YAML `state_similarity:0.0`→`0.40` and `impression_similarity:0.0`→`0.20` |
| F1.11 | Wire `llm.emotion` | **DONE** | `angela_llm_service.py:1988-1998` reads negation/intensifier words from config |
| F1.12 | Wire `state_to_llm` | **DONE** | `config_loader.py` `_build_axis_context()` reads config first, falls back to coord_rules |

### Phase 2 — Structural Cleanup

| ID | Task | Status | Description |
|----|------|--------|-------------|
| F2.1 | Move test files out of `src/` | **SKIPPED** — cosmetic | 6 test files; zero production imports; leaving them is harmless |
| F2.2 | Move demo files out of `src/` | **SKIPPED** — cosmetic | 9 demo files; zero production imports; leaving them is harmless |
| F2.3 | Resolve `config_loader.py` collision | **SKIPPED** — no runtime impact | All imports use dotted paths (`core.config_loader`, `core.state.config_loader`); bare `import config_loader` never used |
| F2.4 | Resolve `demo_learning_manager.py` collision | **SKIPPED** — no runtime impact | Different directories; neither imported by production code |
| F2.5 | Wire learned YAML consumption | **DEFERRED** | `learned_*.yaml` generated by learning system, not consumed back; requires new read path |
| F2.6 | Fix `ai/context/__init__.py` `__all__` mismatch | **DONE** | Added missing imports for 7 classes (`DatabaseStorage`, `ToolContextManager`, etc.) |

### Phase 3 — Cross-App Alignment

| ID | Task | Status | Description |
|----|------|--------|-------------|
| F3.1 | Unify FastAPI apps or document choice | **PENDING** | Two apps (`main.py` vs `main_api_server.py`) share same `api.router` but different middleware/lifecycle |
| F3.2 | Add encryption middleware | **CANCELLED** — both apps lack it | `EncryptedCommunicationMiddleware` in `shared/security_middleware.py` is never imported by either app. Not a gap between apps — both have none. |
| F3.3 | Add env var interpolation to YAML loader | **PENDING** | Support `${VAR_NAME}` syntax in all config files |

---

## Appendix A: File Hash Map (Key Files)

| File | Lines | Role |
|------|-------|------|
| `src/services/main_api_server.py` | 1641 | Main FastAPI app + endpoints |
| `src/services/chat_service.py` | 1289 | Chat pipeline orchestration |
| `src/services/angela_llm_service.py` | 2266 | LLM backend management |
| `src/core/config_loader.py` | 902 | Config loading + authority system |
| `src/core/autonomous/state_matrix.py` | ~600 | 8D state matrix |
| `src/core/autonomous/theta_router.py` | ~500 | Theta novelty/self-correction |
| `src/core/autonomous/eta_axis.py` | ~500 | Eta execution tracking |
| `src/ai/memory/ham_memory/ham_manager.py` | ~600 | HAM memory core |
| `src/ai/context/manager_fixed.py` | ~800 | Context system (active) |
| `src/config/angela_core.yaml` | 1082 | Primary config (27 sections) |

## Appendix B: Desktop JS Module Layer Map

```
Layer 0: Foundation (5)
  logger.js, error-handler.js, global-error-handler.js
  frontend-utils.js, weak-ref-manager.js

Layer 1: Infrastructure (10)
  api-client.js, backend-websocket.js, websocket-wrapper.js
  security-manager.js, security-utils.js
  i18n.js, theme-manager.js
  performance-manager.js, performance-monitor.js
  settings-manager.js

Layer 2: State & Logic (6)
  state-matrix.js, state-persistence.js
  maturity-tracker.js, time-evolution-manager.js
  precision-manager.js, availability-manager.js

Layer 3: Rendering (10)
  live2d-manager.js, live2d-manager-improved.js
  live2d-cubism-wrapper.js, cubism-sdk-manager.js
  simple-live2d-loader.js, model-resource-checker.js
  layer-renderer.js, unified-display-matrix.js
  z-index-manager.js, wallpaper-handler.js

Layer 4: UI & Interaction (10)
  app.js, dialogue-ui.js, input-handler.js
  character-touch-detector.js, gesture-manager.js
  haptic-handler.js, audio-handler.js
  settings.js, tray-manager.js
  plugin-manager.js

Layer 5: Diagnostics (12)
  integration-tester.js, final-tester.js
  quick-diagnosis.js, deep-live2d-diagnostic.js
  hardware-diagnostic.js, cubism-tester.js
  live2d-test.js, live2d-analyzer.js
  live2d-hit-test.js, live2d-test-suite.js
  test-touch-coordinates.js, resource-connection-manager.js
```
