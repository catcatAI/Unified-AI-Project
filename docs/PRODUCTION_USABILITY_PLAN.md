<!--
  =============================================================================
  ANGELA-MATRIX: L3 [β] [B] [L4]
  FILE_PATH: docs/PRODUCTION_USABILITY_PLAN.md
  FILE_TYPE: planning + audit
  PURPOSE: Production usability — current state vs target, gaps, implementation plan
  VERSION: 1.0.0
  STATUS: active
  LANGUAGE: en
    LAST_MODIFIED: 2026-09-16
  AUDIENCE: developers, product
  =============================================================================
-->

# Production Usability Plan

> **Goal**: Define exactly what "production-grade usability" means for Angela
> AI, audit every surface against it, and provide a phased implementation plan.

---

## Table of Contents

1. [Philosophy](#1-philosophy)
2. [Surfaces Audit — Current vs Target](#2-surfaces-audit)
3. [Information Model](#3-information-model)
4. [Gap Matrix](#4-gap-matrix)
5. [Phased Implementation Plan](#5-implementation-plan)
6. [Success Criteria](#6-success-criteria)

---

## 1. Philosophy

Production-grade usability for Angela AI means three things:

1. **Discoverability** — Users know what exists without reading docs
2. **Actionability** — Every problem comes with a fix
3. **Visibility** — System state is always observable, never hidden

The user should never have to grep source code to figure out what's happening.

---

## 2. Surfaces Audit

### 2.1 CLI REPL

| Dimension          | Current                               | Target                                      | Gap        |
| ------------------ | ------------------------------------- | ------------------------------------------- | ---------- |
| **Help**           | Categorized, emoji-titled             | + clickable examples, color                 | 🟡 minor   |
| **Boot banner**    | Shows LLM/Memory/State status         | + version, config file paths, uptime        | 🟡 minor   |
| **/state**         | Bar indicators per axis               | + color gradient (green→red for thresholds) | 🟡 minor   |
| **/model**         | Table with health + active            | + model name, context window, latency       | 🟡 minor   |
| **/route**         | Backend detail table                  | + last error, retry count                   | 🟢 done    |
| **/config**        | Deployment mode + backends + warnings | + file paths, edit hints                    | 🟢 done    |
| **/ctx**           | 4 subcommands                         | + /ctx history (recent decisions)           | 🟡 minor   |
| **/memory**        | Search + show results                 | + category filter, importance sort          | 🟡 minor   |
| **Error guidance** | 💡 hints on boot                      | + hints in /model, /route, /config          | 🟢 done    |
| **ANSI color**     | None (plain text)                     | Colored bars, bold headers, dim hints       | 🔴 missing |

**Overall CLI status**: ~80% production-ready. Main gap is ANSI color output.

### 2.2 Web Dashboard (Next.js @ localhost:3000)

| Component             | Current                          | Target                                                     | Gap        |
| --------------------- | -------------------------------- | ---------------------------------------------------------- | ---------- |
| **ChatPanel**         | WebSocket chat, message list     | + typing indicator, message timestamps, markdown rendering | 🟡 minor   |
| **SystemMonitor**     | CPU, Memory, Uptime, Connections | + LLM backend status, 8D state bars, disk, network         | 🔴 major   |
| **MemoryViewer**      | Search, category filter, list    | + importance visualization, recency graph                  | 🟡 minor   |
| **PetPanel**          | State fetch + pet actions        | + emotion visualization, state history graph               | 🟢 done    |
| **EconomyPanel**      | Exists but backend deleted       | Should be removed or reconnected                           | 🔴 broken  |
| **LearningDashboard** | Exists but backend deleted       | Should be removed or reconnected                           | 🔴 broken  |
| **ConfigPanel**       | ❌ Does not exist                | Deployment mode, backends, edit                            | 🔴 missing |
| **ModelSelector**     | ❌ Does not exist                | Switch active backend, health indicators                   | 🔴 missing |
| **ContextViewer**     | ❌ Does not exist                | 8D state matrix, intent registry                           | 🔴 missing |
| **HealthIndicator**   | ❌ Does not exist                | Green/yellow/red system health badge                       | 🔴 missing |
| **HelpPanel**         | ❌ Does not exist                | Links to docs, command reference                           | 🔴 missing |
| **Onboarding**        | ❌ Does not exist                | First-run wizard when API key missing                      | 🔴 missing |
| **Navigation**        | No nav                           | Tab bar or sidebar with all panels                         | 🔴 missing |
| **Error states**      | Silent failures                  | Error boundary + retry buttons                             | 🔴 missing |

**Overall Web status**: ~30% production-ready. Most panels are missing or
broken.

### 2.3 Desktop App (Electron)

| Element                  | Current                         | Target                                        | Gap        |
| ------------------------ | ------------------------------- | --------------------------------------------- | ---------- |
| **Live2D character**     | Renders, touch interaction      | ✅ Production-ready                           | 🟢 done    |
| **Chat input**           | Basic text input                | + voice toggle, send button feedback          | 🟡 minor   |
| **Toolbar**              | ⚙️ 📷 🎤 >_                     | + health badge (green/yellow/red)             | 🔴 missing |
| **Status panel**         | Backend, CPU, Memory, Disk      | + LLM backend name, deployment mode           | 🟡 minor   |
| **Settings: General**    | Window, Behavior                | ✅ Production-ready                           | 🟢 done    |
| **Settings: Appearance** | Model, Scale, Render, Wallpaper | ✅ Production-ready                           | 🟢 done    |
| **Settings: Audio**      | TTS, Volume                     | ✅ Production-ready                           | 🟢 done    |
| **Settings: Haptics**    | Enable/disable                  | ✅ Production-ready                           | 🟢 done    |
| **Settings: Network**    | Backend URL, Cluster            | ✅ Production-ready                           | 🟢 done    |
| **Settings: Advanced**   | Frame rate, Quality, Debug      | ✅ Production-ready                           | 🟢 done    |
| **Settings: LLM**        | ❌ Does not exist               | Deployment mode, model select, backend health | 🔴 missing |
| **Settings: Context**    | ❌ Does not exist               | 8D state, memory count, intent count          | 🔴 missing |
| **Settings: Help**       | ❌ Does not exist               | Links to docs, about page                     | 🔴 missing |
| **First-run**            | ❌ Does not exist               | Setup wizard on first launch                  | 🔴 missing |

**Overall Desktop status**: ~65% production-ready. Missing LLM settings panel +
help.

### 2.4 API Endpoints

| Endpoint                       | Current                         | Target                            | Gap        |
| ------------------------------ | ------------------------------- | --------------------------------- | ---------- |
| `GET /health`                  | ✅ `{status, service, version}` | ✅                                | 🟢 done    |
| `GET /api/v1/ops/status`       | ✅ CPU, Memory, Disk            | + LLM status, config mode, uptime | 🟡 minor   |
| `GET /api/v1/ops/health`       | ✅ stressed/not                 | ✅                                | 🟢 done    |
| `GET /api/v1/ops/metrics`      | ✅ Prometheus-style             | ✅                                | 🟢 done    |
| `GET /api/v1/desktop/state`    | ✅ Live2D state                 | ✅                                | 🟢 done    |
| `POST /api/v1/chat/unified`    | ✅ Chat                         | ✅                                | 🟢 done    |
| `GET /api/v1/system/discovery` | ❌ Does not exist               | All-in-one system info            | 🔴 missing |
| `GET /api/v1/config/summary`   | ❌ Does not exist               | Config overview                   | 🔴 missing |
| `GET /api/v1/llm/status`       | ❌ Does not exist               | Backend status + health           | 🔴 missing |
| `GET /api/v1/context/summary`  | ❌ Does not exist               | State + memory + intents          | 🔴 missing |
| `POST /api/v1/llm/switch`      | ❌ Does not exist               | Switch active backend             | 🔴 missing |

**Overall API status**: ~45% production-ready. Missing discovery and management
endpoints.

---

## 3. Information Model

### What users need to know (and when)

| Moment               | What to show                                  | Where                                        |
| -------------------- | --------------------------------------------- | -------------------------------------------- |
| **First launch**     | What's configured, what's missing, how to fix | CLI banner + Desktop wizard + Web onboarding |
| **Running normally** | Health status, active backend, uptime         | Toolbar badge + status bar                   |
| **Something breaks** | What broke + how to fix it                    | Error message + 💡 hint                      |
| **Changing config**  | Current value → new value confirmation        | Settings panel + REPL output                 |
| **Choosing model**   | All options + health + recommendation         | /model list + ModelSelector panel            |
| **Inspecting state** | 8D matrix + memory + context                  | /state + ContextViewer panel                 |
| **Debugging**        | Logs, metrics, recent decisions               | /eval + SystemMonitor + Swagger              |

### Information hierarchy

```
Level 0 — "Is it working?"
  → Green/yellow/red badge (everywhere)
  → Boot banner (CLI), status bar (Desktop), health badge (Web)

Level 1 — "What's happening right now?"
  → Active backend, deployment mode, uptime
  → /config summary, /route, status panel

Level 2 — "Why is it doing that?"
  → 8D state matrix, intent classification, routing decisions
  → /state, /ctx, /intent

Level 3 — "How do I change it?"
  → Config files, settings panels, model switching
  → /config, /model switch, Settings GUI

Level 4 — "Deep debugging"
  → Logs, metrics, raw data
  → /eval, /api/v1/ops/metrics, Swagger UI
```

---

## 4. Gap Matrix

### Priority 1 — Critical (Blocks production use)

| #    | Gap                                                        | Surface | Effort | Impact                            |
| ---- | ---------------------------------------------------------- | ------- | ------ | --------------------------------- |
| P1-1 | **Web: ConfigPanel** — deployment mode, backends, edit     | Web     | Medium | Users can't configure without CLI |
| P1-2 | **Web: ModelSelector** — switch backend, health            | Web     | Medium | Can't change model from UI        |
| P1-3 | **Web: HealthIndicator** — green/yellow/red badge          | Web     | Small  | No at-a-glance status             |
| P1-4 | **Web: Navigation** — tab bar or sidebar                   | Web     | Medium | Can't discover panels             |
| P1-5 | **Desktop: LLM Settings panel** — mode, model, health      | Desktop | Medium | Can't configure LLM from GUI      |
| P1-6 | **API: /system/discovery** — all-in-one info               | API     | Small  | Web/Desktop need data source      |
| P1-7 | **Web: Remove/reconnect EconomyPanel + LearningDashboard** | Web     | Small  | Dead panels confuse users         |

### Priority 2 — Important (Significantly improves UX)

| #    | Gap                                                        | Surface | Effort | Impact                         |
| ---- | ---------------------------------------------------------- | ------- | ------ | ------------------------------ |
| P2-1 | **Web: ContextViewer** — 8D state + intents + memory stats | Web     | Medium | Can't inspect state from UI    |
| P2-2 | **Desktop: Help panel** — links to docs, about             | Desktop | Small  | Users can't find documentation |
| P2-3 | **CLI: ANSI color** — colored bars, bold headers           | CLI     | Small  | Better readability             |
| P2-4 | **Web: Error boundary** — error states + retry             | Web     | Medium | Silent failures                |
| P2-5 | **Desktop: Toolbar health badge**                          | Desktop | Small  | No at-a-glance status          |
| P2-6 | **First-run wizard** — detect missing config, guide setup  | All     | Large  | New users lost                 |
| P2-7 | **API: /llm/status** + **/llm/switch**                     | API     | Small  | Programmatic management        |

### Priority 3 — Nice-to-have

| #    | Gap                                              | Surface | Effort | Impact                |
| ---- | ------------------------------------------------ | ------- | ------ | --------------------- |
| P3-1 | **Web: Chat markdown rendering**                 | Web     | Medium | Better readability    |
| P3-2 | **Web: Onboarding wizard**                       | Web     | Medium | Self-service setup    |
| P3-3 | **CLI: /ctx history** — recent routing decisions | CLI     | Small  | Debugging aid         |
| P3-4 | **Desktop: Context state widget** in main window | Desktop | Medium | At-a-glance state     |
| P3-5 | **Config hot-reload** without restart            | Backend | Large  | Better dev experience |

---

## 5. Implementation Plan

### Phase 1 — API Foundation (1 day)

**Goal**: Create the data endpoints that Web and Desktop consume.

| Task                                     | Files                                | Notes                                                                                                      |
| ---------------------------------------- | ------------------------------------ | ---------------------------------------------------------------------------------------------------------- |
| `GET /api/v1/system/discovery`           | `api/routes/system_routes.py` (new)  | Returns: deployment mode, backends (name/type/enabled/health), intents count, memory status, state summary |
| `GET /api/v1/llm/status`                 | `api/routes/llm_routes.py` (new)     | Returns: backends list with health, active, llm_mode, stats                                                |
| `POST /api/v1/llm/switch`                | `api/routes/llm_routes.py`           | Body: `{backend: "ollama-llama3"}` → switches active                                                       |
| `GET /api/v1/context/summary`            | `api/routes/context_routes.py` (new) | Returns: state matrix, memory count, intent count, recent decisions                                        |
| Register routers in `main_api_server.py` | `services/main_api_server.py`        | Add `app.include_router(...)`                                                                              |

### Phase 2 — Web Dashboard Core (2-3 days)

**Goal**: Replace dead panels with working Config/Model/Context panels.

| Task                                         | Files                                                   | Notes                                                                   |
| -------------------------------------------- | ------------------------------------------------------- | ----------------------------------------------------------------------- |
| Add tab navigation                           | `apps/web-dashboard/src/App.tsx`                        | Tab bar: Chat, System, Config, Context, Memory                          |
| **ConfigPanel** component                    | `apps/web-dashboard/src/components/ConfigPanel.tsx`     | Show deployment mode, backend list (enabled/disabled), edit mode toggle |
| **ModelSelector** component                  | `apps/web-dashboard/src/components/ModelSelector.tsx`   | Backend table with health, active marker, switch button                 |
| **HealthIndicator** component                | `apps/web-dashboard/src/components/HealthIndicator.tsx` | Green/yellow/red badge from `/ops/health`                               |
| **ContextViewer** component                  | `apps/web-dashboard/src/components/ContextViewer.tsx`   | 8D state bars, intent list, memory stats                                |
| Remove broken EconomyPanel/LearningDashboard | `apps/web-dashboard/src/App.tsx`                        | Delete dead imports                                                     |
| **HelpPanel** component                      | `apps/web-dashboard/src/components/HelpPanel.tsx`       | Links to USABILITY_GUIDE, Swagger docs                                  |

### Phase 3 — Desktop LLM Settings (1-2 days)

**Goal**: Add LLM configuration to Desktop settings window.

| Task                        | Files                                         | Notes                                                                     |
| --------------------------- | --------------------------------------------- | ------------------------------------------------------------------------- |
| Add "LLM & AI" nav item     | `apps/desktop-app/electron_app/settings.html` | New sidebar section                                                       |
| **LLM Settings section**    | `apps/desktop-app/electron_app/settings.html` | Deployment mode dropdown, backend list, model selector, health indicators |
| **Context state section**   | `apps/desktop-app/electron_app/settings.html` | 8D state display, memory count, intent count                              |
| **Help section**            | `apps/desktop-app/electron_app/settings.html` | Links to docs, version info, about                                        |
| IPC handlers for LLM config | `apps/desktop-app/electron_app/main.js`       | `settings-get-llm`, `settings-set-llm`, `llm-status`                      |
| Backend health polling      | `apps/desktop-app/electron_app/main.js`       | Periodic `/api/v1/llm/status` fetch                                       |

### Phase 4 — Polish & Onboarding (1-2 days)

**Goal**: Fill remaining gaps.

| Task                         | Files                                             | Notes                                                                         |
| ---------------------------- | ------------------------------------------------- | ----------------------------------------------------------------------------- |
| ANSI color in REPL           | `apps/backend/src/cli/repl.py`                    | ✅ Done — `\033[1m` bold, `\033[32m` green, `\033[33m` yellow, `\033[31m` red |
| Desktop toolbar health badge | `apps/desktop-app/electron_app/index.html`        | ✅ Done — 🟢/🟡/🔴 via /ops/status polling                                    |
| First-run detection          | `apps/backend/src/core/system/bootstrap/`         | ⬜ Needs bootstrap module (other agent scope)                                 |
| Web error boundary           | `apps/web-dashboard/src/`                         | ⬜ Low priority                                                               |
| Chat markdown rendering      | `apps/web-dashboard/src/components/ChatPanel.tsx` | ✅ Done — regex bold/code/links                                               |
| Delete orphaned panels       | `apps/web-dashboard/src/components/`              | ✅ Done — EconomyPanel + LearningDashboard deleted                            |
| Desktop status panel LLM     | `apps/desktop-app/electron_app/index.html`        | ✅ Done — /llm/status polling                                                 |

---

## 6. Success Criteria

A surface is "production-ready" when:

### CLI REPL

- [x] Boot banner shows health at a glance
- [x] Every error comes with a fix hint
- [x] /model shows all backends with health
- [x] /config shows deployment mode prominently
- [x] /ctx has subcommands
- [x] ANSI color output (bar green/yellow/red, bold headers, yellow hints)
- [x] /help is categorized

### Web Dashboard

- [x] Green/yellow/red health badge visible at all times (HealthIndicator)
- [x] Can view and switch LLM backends (ModelSelector)
- [x] Can view deployment mode and config summary (ConfigPanel)
- [x] Can view 8D state matrix (ContextViewer)
- [x] Can search and view memories (MemoryViewer — pre-existing)
- [x] No dead/broken panels — EconomyPanel & LearningDashboard deleted
- [ ] Error states shown, not silent — no error boundary yet (low priority)
- [x] Navigation to all panels (tab bar in index.tsx)
- [x] Chat markdown rendering (bold, code, links via regex)

### Desktop App

- [x] Live2D character works
- [x] Settings: General/Appearance/Audio/Haptics/Network/Advanced
- [x] Settings: LLM & AI (mode, model, health, switching, generation defaults)
- [x] Settings: Help (docs links, about, keyboard shortcuts)
- [x] Toolbar health badge (🟢/🟡/🔴) — index.html + JS polling
- [ ] First-run setup wizard — needs backend bootstrap integration
- [x] Status panel shows LLM backend name — JS polling /api/v1/llm/status

### API

- [x] /health, /ops/status, /ops/health
- [x] /system/discovery (all-in-one)
- [x] /llm/status (backend details)
- [x] /llm/switch (programmatic switching)
- [x] /context/summary (state + memory + intents)

---

_Last Updated: 2026-09-16 | See also: [USABILITY_GUIDE.md](USABILITY_GUIDE.md)_
