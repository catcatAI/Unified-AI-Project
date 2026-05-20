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
| Total Python files in `apps/backend/src/` | **503** |
| Total directories (including empty) | **156** |
| Empty directories | **12** |
| Total config files (YAML/JSON) | **13** |
| Total JS/TS modules (desktop-app) | **63** |
| Test files shipped in `src/` | **8** |
| `_demo.py` files in production | **4** |
| `_fixed.py` duplicate files | **2** (1 active, 1 dead) |
| Unused `_v2` files | **1** |
| Dead config sections (no code consumer) | **~18** |
| Broken CLI entry points | **2** |

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
| Encryption | `EncryptedCommunicationMiddleware` (Key B) |
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
- **Which one is "production"?** `main_api_server.py` has version `6.0.4` and is the target of `start_server*.py`. But `main.py` has encryption middleware that `main_api_server.py` lacks.

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

| Section | Key(s) | YAML Line | Problem |
|---------|--------|-----------|---------|
| `state_to_llm` | `alpha_energy.*`, `beta_curiosity.*`, etc. | 414-430 | Natural language labels exist but `config_loader.py:_build_axis_context` uses hardcoded logic. **PARTIALLY FIXED** — `state_to_llm` now read first, falls back to coord_rules. |
| `response_schema` | `version`, `fields` | 434-436 | Never read by any code |
| `persistence` | `state_matrix.checkpoint_interval`, `persist_to` | 440-447 | `state_persistence.py` hardcodes `auto_save_interval=300` |
| `predefined_templates` | All 5 templates | 490-510 | `template_library.py` hardcodes different content |
| `empathy` | `thresholds.*`, `emotion_keywords` | 954-963 | Never read |
| `state_tracking` | `coordinate_recalculation`, `anchor_update_threshold`, `history_window` | 967-970 | Never read |
| `theta` | `novelty_estimation.*`, `self_correction.*` | 974-980 | Hardcoded in `theta_router.py` |
| `eta` | `module_trigger_curve.*`, `execution_tracking.*` | 984-991 | Hardcoded in `eta_axis.py` |
| `routing.route_registry` | Full route list | 54-70 | All routes registered via FastAPI decorators |
| `learning.decay` | `enabled`, `days_to_decay`, etc. | 395-410 | Never read |
| `learning.write_strategy` | `mode`, `debounce_ms`, etc. | 395-410 | Never read |
| `learning.template_quality` | `enabled`, `match_tracking_window`, etc. | 395-410 | Never read |
| `llm.backend_priority` | `["ollama", "google", ...]` | 1003-1008 | Backend order from `multi_llm_config.json` iteration |
| `llm.memory.*` | All 5 keys | ~1025-1040 | Hardcoded in `precompute_service.py` |
| `middleware.encrypted_communication` | `enabled` | 24 | Never read |
| `middleware.auth` | `enabled` | 27 | Never read |
| `chat_flow.default_flow` | `"angela_chat_service"` | 13 | Hardcoded string in `main_api_server.py:647` |
| `chat_flow.http_timeout` | `30.0` | 14 | Never read |
| `chat_flow.truncation_message` | `"..."` | 17 | Never read |
| `chat_flow.response_schema_version` | `"2.0"` | 18 | Never read |
| `document_builder.max_segments` | `10` | 947 | Hardcoded as `8` in `document_builder.py:77` |
| `document_builder.learning_threshold` | `success_count`, `keyword_match_count` | 949-950 | Never read |
| `services.web_search.num_results` | `5` | 304 | Hardcoded as `3` in `chat_service.py:924` |
| `template_matching.score_weights` | `state_similarity: 0.0`, etc. | 480-486 | **FIXED** — code now reads from config; mismatched weights were 0.40/0.20 vs YAML 0.0/0.0 |
| `llm.emotion` | `negation_words`, `intensifier_words` | ~1025 | **FIXED** — code now reads from config, falls back to built-in list |

**Total dead/partial config subsections: ~25, of which 3 were FIXED during audit.**

---

## 5. Dead Code & Orphan Files

### 5.1 Orphaned Source Files

| File | Status | Reason |
|------|--------|--------|
| `ai/context/manager.py` | **DEAD** | `__init__.py` imports from `manager_fixed` instead |
| `ai/context/storage/base_fixed.py` | **DEAD** | No file imports it; `manager_fixed.py` imports from `base.py` |
| `core/autonomous/self_introspector.py` | **DEAD** | Zero import references anywhere |
| `core/autonomous/self_introspector_v2.py` | **DEAD** | Zero import references anywhere |

### 5.2 Test Files in Production Tree (`apps/backend/src/`)

These are test files that should be in `tests/`, not in the shipped `src/` package:

| File | Directory |
|------|-----------|
| `test_browser_controller.py` | `core/autonomous/` |
| `test_integration.py` | `core/tests/` |
| `test_feedback_loops.py` | `core/tests/` |
| `test_action_execution_bridge.py` | `core/tests/` |
| `test_config.py` | `src/` root |
| `test_audio.py` | `src/` root |

### 5.3 Demo Files in Production Tree

| File | Directory | Notes |
|------|-----------|-------|
| `demo_feedback_loop.py` | `core/` | Not imported by production code |
| `demo_learning_manager.py` | `core/managers/` | Has duplicate in `ai/learning/` — possible confusion |
| `demo_learning_manager.py` | `ai/learning/` | Has duplicate in `core/managers/` — possible confusion |
| `demo_context_system.py` | `ai/context/` | Not imported by production code |
| `level5_asi_demo.py` | `ai/examples/` | Not imported by production code |

### 5.4 Duplicate/Wasteful Module Pairs

| File A | File B | Notes |
|--------|--------|-------|
| `manager.py` | `manager_fixed.py` | `_fixed` is the active one; `manager.py` is dead |
| `base.py` | `base_fixed.py` | `base_fixed.py` is dead; `base.py` is active |
| `self_introspector.py` | `self_introspector_v2.py` | Neither is imported anywhere — both dead |
| `core/managers/demo_learning_manager.py` | `ai/learning/demo_learning_manager.py` | Two files with same name, different locations |
| `config_loader.py` (root) | `core/config_loader.py` | Different modules with same filename — potential import confusion |

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
| `cli_runner.py` | ~160 | **BROKEN** — pervasive syntax errors (double colons, `==` in args) |
| `cli/unified_cli.py` | ~200 | **BROKEN** — same pervasive syntax errors |
| `cli/main.py` | ~150 | **BROKEN** — syntax errors (missing commas) |
| `cli/client.py` | 109 | **CLEAN** — functional HTTP client |
| `cli/port_manager.py` | 277 | **CLEAN** — functional port utilities |
| `cli/error_handler.py` | 179 | **CLEAN** — functional error logging |
| `cli/ai_models_cli.py` | 429 | **MOSTLY CLEAN** — functional if backend deps exist |

### 9.2 Assessment

- The CLI was clearly written/refactored in multiple passes with errors introduced
- `cli_runner.py` and `unified_cli.py` have identical broken patterns suggesting copy-paste errors
- Utility modules (`client.py`, `port_manager.py`, `error_handler.py`) are clean and functional
- **Ambition vs reality**: The CLI tries to expose 6 command groups (health, chat, analyze, search, image, atlassian) across 4 entry points, but none of the entry points work due to syntax errors
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
| 0.1 | Two competing FastAPI apps | `main.py` vs `main_api_server.py` | Confused entry points, `main.py` has encryption, `main_api_server.py` doesn't |
| 0.2 | CLI entry points broken | `cli_runner.py`, `cli/unified_cli.py` | Cannot run any CLI command |
| 0.3 | No encryption on main API | `main_api_server.py` | Desktop and mobile apps send encrypted payloads but server doesn't validate |

### P1 — High

| # | Issue | Location | Impact |
|---|-------|----------|--------|
| 1.1 | Dead config: 18 sections never read | `angela_core.yaml` | Config exists but is ignored: `theta`, `eta`, `empathy`, `persistence`, etc. |
| 1.2 | Dead code: `self_introspector*` not imported | `core/autonomous/` | Two files, zero consumers |
| 1.3 | Dead code: `manager.py` not imported | `ai/context/` | `manager_fixed.py` is the active version; `manager.py` is orphaned |
| 1.4 | Dead code: `base_fixed.py` not imported | `ai/context/storage/` | Completely orphaned |
| 1.5 | Test files in production package | 8 files in `src/` | Shipped test code in production namespace |
| 1.6 | `demo_*` files in production | 4 files in `src/` | Demo code in production namespace |
| 1.7 | Hardcoded URLs & paths in config | All 13 YAML/JSON files | No env var interpolation, not portable |

### P2 — Medium

| # | Issue | Location | Impact |
|---|-------|----------|--------|
| 2.1 | Two `demo_learning_manager.py` files | `core/managers/` + `ai/learning/` | Same name, different locations — import confusion |
| 2.2 | `config_loader.py` name collision | `src/` root + `core/` + `core/state/` | Three files named `config_loader.py` |
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

### Phase 0 — Must Fix (this session)

| ID | Task | Effort | File(s) |
|----|------|--------|---------|
| F0.1 | Fix CLI syntax errors | 30min | `cli_runner.py`, `cli/unified_cli.py`, `cli/main.py` |
| F0.2 | Remove `manager.py` (dead) | 5min | `ai/context/manager.py` |
| F0.3 | Remove `base_fixed.py` (dead) | 5min | `ai/context/storage/base_fixed.py` |
| F0.4 | Remove `self_introspector.py` and `_v2` (both dead) | 5min | `core/autonomous/self_introspector*.py` |

### Phase 1 — Config Wire-Up

| ID | Task | Effort | Description |
|----|------|--------|-------------|
| F1.1 | Wire `theta` config | 20min | Read `theta.novelty_estimation.min_threshold` etc. in `theta_router.py` |
| F1.2 | Wire `eta` config | 20min | Read `eta.module_trigger_curve.*` in `eta_axis.py` |
| F1.3 | Wire `persistence` config | 15min | Read `persistence.state_matrix.checkpoint_interval` in `state_persistence.py` |
| F1.4 | Wire `predefined_templates` | 20min | Replace hardcoded templates in `template_library.py` with YAML values |
| F1.5 | Wire `empathy` config | 15min | Read `empathy.*` in emotion system |
| F1.6 | Wire remaining `chat_flow` items | 10min | `default_flow`, `http_timeout`, `truncation_message`, `response_schema_version` |
| F1.7 | Wire `llm.backend_priority` | 15min | Use for backend selection order instead of dict iteration |
| F1.8 | Wire `llm.memory.*` | 15min | Read precompute thresholds in `precompute_service.py` |
| F1.9 | Wire `services.web_search.num_results` | 5min | Read in `chat_service.py:924` |

### Phase 2 — Structural Cleanup

| ID | Task | Effort | Description |
|----|------|--------|-------------|
| F2.1 | Move test files out of `src/` | 15min | Move 8 test files to `tests/` directory |
| F2.2 | Move demo files out of `src/` | 10min | Move 4 demo files or delete |
| F2.3 | Resolve `config_loader.py` collision | 20min | Rename root `config_loader.py` to avoid confusion with `core/config_loader.py` |
| F2.4 | Resolve `demo_learning_manager.py` collision | 10min | Keep one, remove the other |
| F2.5 | Wire learned YAML consumption | 30min | Read `learned_*.yaml` back for decision-making |

### Phase 3 — Cross-App Alignment

| ID | Task | Effort | Description |
|----|------|--------|-------------|
| F3.1 | Unify FastAPI apps or document choice | 60min | Either merge `main.py` into `main_api_server.py` or kill one |
| F3.2 | Add encryption middleware to `main_api_server` | 30min | Port `EncryptedCommunicationMiddleware` from `main.py` |
| F3.3 | Add env var interpolation to YAML loader | 45min | Support `${VAR_NAME}` syntax in all config files |

---

## Appendix A: File Hash Map (Key Files)

| File | Lines | Role |
|------|-------|------|
| `src/services/main_api_server.py` | 1638 | Main FastAPI app + endpoints |
| `src/services/chat_service.py` | 1100+ | Chat pipeline orchestration |
| `src/services/angela_llm_service.py` | 2274 | LLM backend management |
| `src/core/config_loader.py` | 886 | Config loading + authority system |
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
