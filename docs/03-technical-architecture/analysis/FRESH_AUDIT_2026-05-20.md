# Fresh Comprehensive Audit — Angela AI

> Generated: 2026-05-20 | Method: Three parallel agents scanning full codebase, cross-referenced against each other, then deep-verified

---

## Table of Contents
1. [Critical Server Blockers — Will Crash on Startup](#1-critical-server-blockers)
2. [Architectural Issues — Dual Apps, Confused Routes](#2-architectural-issues)
3. [Frontend-Backend Endpoint Gaps](#3-frontend-backend-endpoint-gaps)
4. [Dead Config Sections (8 Remaining)](#4-dead-config-sections)
5. [Minor & Informational Findings](#5-minor--informational-findings)
6. [Already Fixed — This Session](#6-already-fixed)
7. [Repair Priority Matrix](#7-repair-priority-matrix)

---

## 1. Critical Server Blockers — Will Crash on Startup

### 1.1 Five Duplicate Route Registrations in `main_api_server.py:848-860`

**Root cause**: `main_api_server.py` imports `api_v1_router` (which already includes `vision.router`, `audio.router`, `tactile.router` via `api/router.py`), then registers **exact same paths again** as stacked decorators on the **wrong handler**.

| Duplicate Path | File Line | Wrong Handler | Correct Handler Location |
|---|---|---|---|
| `POST /api/v1/vision/sampling` | `main_api_server.py:853` | `get_brain_dividend()` | `api/v1/endpoints/vision.py:19` → `get_vision_sampling()` |
| `POST /api/v1/vision/perceive` | `main_api_server.py:854` | `get_brain_dividend()` | `api/v1/endpoints/vision.py:40` → `vision_perceive()` |
| `POST /api/v1/audio/scan` | `main_api_server.py:855` | `get_brain_dividend()` | `api/v1/endpoints/audio.py:19` → `audio_scan()` |
| `POST /api/v1/audio/register_user` | `main_api_server.py:856` | `get_brain_dividend()` | `api/v1/endpoints/audio.py:30` → `audio_register_user()` |
| `POST /api/v1/tactile/model` | `main_api_server.py:857` | `get_brain_dividend()` | `api/v1/endpoints/tactile.py:19` → `tactile_model()` |

**Impact**: FastAPI raises `ValueError: Duplicate operation` on startup. **Server will NOT start** if these routes are hit.

**Additionally**: `POST /api/v1/tactile/touch` at line 858 routes to `get_brain_dividend()` (returns CDM dividend data) — semantically nonsensical for a tactile endpoint.

### 1.2 Two WebSocket `/ws` Handlers — Conflicting

| File | Line | Handler Detail |
|---|---|---|
| `main.py` | 373 | `@app.websocket("/ws")` — basic ConnectionManager relay |
| `main_api_server.py` | 1030 | `@app.websocket("/ws")` — full handshake, heartbeat, chat, state, tactile events |

Both bind the same path. If both apps ever run on the same port, the second registration wins. Since `start_server.py` proxies to `main_api_server.py`, only its handler is active in production.

---

## 2. Architectural Issues

### 2.1 Two Competing FastAPI Apps — Endpoint Mismatch

| App | Entry File | Title | When Used |
|---|---|---|---|
| **App A** | `apps/backend/main.py` | `"Unified AI Project - Level 5 AGI"` | Appears legacy/parallel; has 8 inline routes + `api.router` |
| **App B** | `src/services/main_api_server.py` | `"Angela AI API"` | Target of `start_server.py` and `start_server_all_interfaces.py` |

**Critical gap**: The desktop client (`api-client.js`) calls `POST /api/v1/chat/unified`, `POST /dialogue`, `POST /angela/chat` — these routes ONLY exist in **App B** (`main_api_server.py`). They are NOT available in **App A** (`main.py`). If someone starts `main.py` thinking it's the production server, the desktop app will get 404s on all chat endpoints.

### 2.2 Stacked Decorators at Lines 848-860 — Route Hijack

Five vision/audio/tactile routes are stacked on the `get_brain_dividend()` handler:

```python
@api_v1_router.post("/vision/sampling")
@api_v1_router.post("/vision/perceive")
@api_v1_router.post("/audio/scan")
@api_v1_router.post("/audio/register_user")
@api_v1_router.post("/tactile/model")
@api_v1_router.post("/tactile/touch")
@api_v1_router.post("/brain/metrics")
async def get_brain_dividend():
    ...
```

This means a `POST /vision/sampling` request returns brain dividend data, not vision sampling data. This is a **routing hijack** — the vision/audio/tactile endpoints are overridden to return economy data.

### 2.3 Config Loader Triple Collision — Verified Harmless but Confusing

Three files named `config_loader.py`:

| File | Class | Purpose | Imports |
|---|---|---|---|
| `src/config_loader.py` | None (bare functions) | Legacy/demo YAML loader | Zero imports |
| `src/core/config_loader.py` | `AngelaConfigManager` | Angela AI config (27 sections) | 15+ consumers |
| `src/core/state/config_loader.py` | `StateConfig` | State matrix config (angela_state.yaml) | 2 consumers |

All imports use dotted paths — no bare `import config_loader` exists. Zero runtime ambiguity.

### 2.4 StateConfig Bypass

`StateConfig` (in `core/state/config_loader.py`) was designed to "Replace all hardcoded values in `state_matrix.py`" (line 6 of that file). However:

- `state_matrix.py` (1721 lines) — **does NOT import or use** `StateConfig`. It hardcodes axis defaults directly.
- `state_matrix_adapter.py` (1438 lines) — **DOES** import and use `StateConfig`.
- The adapter wraps `StateMatrix4D` but the underlying matrix still has hardcoded defaults that `StateConfig` was meant to replace.

---

## 3. Frontend-Backend Endpoint Gaps

### 3.1 Desktop Client Calls That Will 404

| Endpoint Called | Desktop File | Backend Status |
|---|---|---|
| `GET /economy/balance` | `api-client.js` | Backend has `GET /economy/balance/{user_id}` (required param) → **422 or 404** |
| `POST /pet/action` | `api-client.js` | Backend has `POST /pet/action/trigger` only → **404** |
| `GET /status` | `api-client.js` | No bare `/status` at app root → **404** |
| `GET /api/v1/cluster/status` | `settings.js` | Exists in `router.py:113` but only when `main.py`'s router is included → depends on which app serves |

### 3.2 Mobile Client Calls

| Endpoint Called | Mobile File | Backend Status |
|---|---|---|
| `GET /api/v1/state/summary` | `App.js:116` | Exists in `services/api/state_matrix_api.py:104` (App B only) |
| `GET /api/v1/state/eta/report` | `App.js:117` | Exists in `services/api/state_matrix_api.py:475` (App B only) |
| `POST /api/v1/mobile/chat` | `App.js:256` | Exists in `api/v1/endpoints/mobile.py:70` |
| `POST /api/v1/mobile/module-control` | `App.js:205` | Exists in `api/v1/endpoints/mobile.py:85` |
| `GET /api/v1/mobile/status` | `App.js:170` | Exists in `api/v1/endpoints/mobile.py:27` |

**Key finding**: Mobile's state endpoints (`state/summary`, `state/eta/report`) are served by `state_matrix_api.py` which is only included in **App B** (`main_api_server.py`). If `main.py` is used, mobile gets 404 on state visualization.

### 3.3 Unused Backend Routes — Never Called by Any Frontend

| Route | Backend File | Function |
|---|---|---|
| All `GET/POST /api/v1/drive/*` | `drive.py` | Google Drive integration — no frontend uses it |
| All `GET /api/v1/trace/*` | `trace.py` | Causal tracing — unused externally |
| All `GET/POST /api/v1/ops/*` | `ops_routes.py` | AI Ops dashboard — unused externally |
| All `POST /api/v1/vision/*` | `vision.py` | Vision service — unused externally (desktop doesn't use camera) |
| All `POST /api/v1/audio/*` | `audio.py` | Audio service — unused externally |
| `POST /api/v1/pet/interaction` | `pet.py` | Desktop calls wrong path (`/pet/action` instead of `/pet/action/trigger`) |
| `POST /api/v1/chat/completions` | `router.py` | `/chat/unified` is used instead |
| `POST /api/v1/mobile/sync` | `mobile.py` | Never called by mobile app |
| `POST /api/v1/mobile/module-control` | `mobile.py` | Mobile calls route but maybe different params |
| `GET /api/v1/agents` | `router.py` | Agent listing — no consumer |
| `POST /api/v1/angela/reload` | `router.py` | LLM reload — no consumer |

---

## 4. Dead Config Sections (8 Remaining)

Of 27 top-level keys in `angela_core.yaml` (1080 lines), **8 are entirely dead** — no Python code reads them:

| Section | Lines | Type | Notes |
|---|---|---|---|
| `learning` | 395-410 | Entire block | `decay`, `write_strategy`, `template_quality` — zero `.get("learning", {})` calls |
| `response_schema` | 434-436 | Entire block | `version: "2.0"` and `fields` list — never read |
| `persistence` | 440-447 | Entire block | `checkpoint_interval`, `persist_to` — code uses separate config system |
| `predefined_templates` | 488-508 | Entire block | 5 templates with content — code hardcodes different content |
| `empathy` | 952-961 | Entire block | `thresholds` and `emotion_keywords` — code uses different emotion system |
| `state_tracking` | 965-968 | Entire block | `coordinate_recalculation`, `anchor_update_threshold` — never read |
| `theta` | 972-978 | Entire block | `novelty_estimation`, `self_correction` — would need code refactor to consume |
| `eta` | 982-989 | Entire block | `module_trigger_curve`, `execution_tracking` — key names don't match code |

Additionally, `middleware.encrypted_communication` and `middleware.auth` (lines 29-32, both `enabled: false`) are never read, but since they're disabled, this is harmless.

**Previously dead sections now fixed** (not counted above): `chat_flow.default_flow/http_timeout/truncation_message/response_schema_version`, `services.web_search.num_results`, `template_matching.score_weights`, `llm.memory.*`, `llm.emotion`, `state_to_llm`.

---

## 5. Minor & Informational Findings

### 5.1 `mobile.py` — Duplicate GET/POST `/status`

`api/v1/endpoints/mobile.py` defines:
- Line 27: `GET /api/v1/mobile/status` — returns `{status: "ok", ...}`
- Line 59: `POST /api/v1/mobile/status` — returns `{status: "ok", ...}` with slightly different format

Both return nearly identical data. One is redundant.

### 5.2 Economy Endpoint — Missing User ID

Desktop `api-client.js` calls `GET /economy/balance`, but the backend route is `GET /economy/balance/{user_id}` with a **required** path parameter. The client will get a 422 validation error.

### 5.3 Learned YAML Files — Are Actually Active

Contrary to previous audit claims, `learned_patterns.yaml`, `learned_thresholds.yaml`, and `learned_routes.yaml` **ARE consumed** by `core/config_loader.py`:
- `get_learned_intent_keywords()` reads `learned_patterns.yaml`
- `get_learned_thresholds()` reads `learned_thresholds.yaml`
- `get_best_route()` reads `learned_routes.yaml`

They are actively loaded and queried. The learning system writes to `learned_routes.yaml` via `neuro_auto_selector.py`.

### 5.4 Config File Duplication — Zero Overlap

`configs/config.yaml` (server, chromadb, modes) and `src/config/angela_core.yaml` (Angela AI config) have **zero overlapping top-level keys**. They serve different purposes.

### 5.5 Encryption Middleware — Neither App Uses It

`EncryptedCommunicationMiddleware` in `shared/security_middleware.py` is defined but **never imported** by either FastAPI app. This was incorrectly flagged as a gap in the previous audit.

### 5.6 Desktop-Only Routes in `main_api_server.py`

Routes like `/desktop/state`, `/desktop/organize`, `/desktop/cleanup` (lines 869-890) and `/vision/*`, `/audio/*`, `/tactile/*` at lines 848-858 are only defined in `main_api_server.py`. If someone extracts the router for use elsewhere, these routes are lost.

### 5.7 `state_matrix_api.py` Route Module — Not in Standard Path

The state matrix API routes live at `services/api/state_matrix_api.py` rather than `api/v1/endpoints/`. This is inconsistent — all other route modules (drive, vision, audio, pet, economy, etc.) are in `api/v1/endpoints/`.

---

## 6. Already Fixed (This Session)

| Fix | Details | Files Touched |
|---|---|---|
| CLI 6 files syntax | All pass `ast.parse` | `cli_runner.py`, `client.py`, `unified_cli.py`, `error_handler.py`, `port_manager.py`, `main.py` |
| CLI phantom imports | `core_services.py` stub created; `hsp.types` → `core.hsp.types` | `src/core_services.py` (new), `cli/main.py` |
| Dead code removal | 4 orphaned files deleted | `manager.py`, `base_fixed.py`, `self_introspector.py`, `self_introspector_v2.py` |
| `chat_flow` config wire | timeout, default_flow, truncation_message, schema_version | `main_api_server.py:605-655` |
| `web_search.num_results` | Reads from `services.web_search` | `chat_service.py:924-926` |
| `score_weights` YAML fix | Corrected `state_similarity:0.0`→`0.40`, `impression:0.0`→`0.20` | `angela_core.yaml:481-485` |
| `llm.memory.precompute_*` | Wired to `_get_llm_config("memory", {})` | `angela_llm_service.py:662-668` |
| `ai/context/__init__.py` | Fixed `__all__` vs import mismatch (7 missing imports added) | `ai/context/__init__.py` |
| Audit document updated | Reflected all fixes, corrected encryption middleware error | `COMPREHENSIVE_PROJECT_AUDIT_V2.md` |

---

## 7. Repair Priority Matrix

### P0 — Startup Blockers

| ID | Issue | Location | Fix |
|----|-------|----------|-----|
| **F0** | 5 duplicate routes (vision/audio/tactile) stacked on `get_brain_dividend()` | `main_api_server.py:848-858` | **Remove stacked decorators. These routes already exist via `api.router` → sub-routers.** The final route `/brain/metrics` is valid; the 6 routes above it are duplicates routing to the wrong handler. |

### P1 — High

| ID | Issue | Location | Fix |
|----|-------|----------|-----|
| **F1** | Desktop calls `GET /economy/balance` (no user_id) | `api-client.js` + `economy.py:20` | Either add a default user_id to the backend route, or fix the frontend to include `{user_id}` |
| **F2** | Desktop calls `POST /pet/action` but backend has `/pet/action/trigger` | `api-client.js` + `pet.py:85` | Add `POST /pet/action` alias in `pet.py` (or fix desktop) |
| **F3** | Desktop calls `GET /status` — no route exists | `api-client.js` | Add `@app.get("/status")` returning health info |
| **F4** | `main.py` (App A) missing chat/state endpoints that desktop/mobile need | `main.py` vs `main_api_server.py` | Document clearly which app to run, or merge the missing routes into `main.py` |

### P2 — Medium

| ID | Issue | Location | Fix |
|----|-------|----------|-----|
| **F5** | 8 dead config sections | `angela_core.yaml` | Either remove or annotate with `# DEAD — for future use` |
| **F6** | Mobile `GET/POST /status` duplicate | `mobile.py:27,59` | Remove one (keep GET as standard) |
| **F7** | State routes in wrong location (`services/api/` instead of `api/v1/endpoints/`) | `state_matrix_api.py` | Move to standard path for consistency |

### P3 — Low

| ID | Issue | Location | Fix |
|----|-------|----------|-----|
| **F8** | `EncryptedCommunicationMiddleware` never imported | `shared/security_middleware.py` | Either delete dead file or integrate into both apps |
| **F9** | 6 test files + 9 demo files in production tree | Various under `src/` | Move to `tests/` (cosmetic, no runtime impact) |
| **F10** | `state_matrix.py` bypasses `StateConfig` | `state_matrix.py` | Wire `StateConfig` into `state_matrix.py` (was the original design intent) |

---

## Appendix: Verification Methodology

This audit was produced by:

1. **Parallel agent scan** — 3 agents simultaneously exploring:
   - Full project structure + file counts
   - Backend import chains + config systems + state system
   - Frontend API calls vs backend route definitions
2. **Cross-reference pass** — 10 specific queries sent to a 4th agent to verify and deep-validate findings
3. **Conflict detection** — Duplicate route registration was found by cross-referencing `main_api_server.py` stacked decorators against sub-router definitions
4. **Config consumption mapping** — Every top-level key in `angela_core.yaml` was checked against `grep` results for `.get("key"` patterns

The key finding (#1 — 5 duplicate routes that crash FastAPI) was missed by all previous audits because they assumed the stacked decorators were intentional rather than copy-paste errors.
