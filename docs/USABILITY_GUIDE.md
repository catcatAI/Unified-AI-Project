<!--
  =============================================================================
  ANGELA-MATRIX: L3 [βγδ] [B] [L4]
  FILE_HASH: USABILITY_GUIDE_v1
  FILE_PATH: docs/USABILITY_GUIDE.md
  FILE_TYPE: documentation
  PURPOSE: Usability guide — configuration, models, context, UI discovery
  VERSION: 1.0.0
  STATUS: active
  LANGUAGE: en
    LAST_MODIFIED: 2026-09-16
  AUDIENCE: users, developers
  =============================================================================
-->

# Angela AI — Usability Guide

> **Purpose**: Show users _where_ everything lives, _what_ is available, and
> _how_ to use it — covering configuration, AI models, context, and all
> interactive surfaces.

---

## Table of Contents

1. [Where Things Are](#1-where-things-are)
2. [Configuration & Settings](#2-configuration--settings)
3. [AI Models & Backends](#3-ai-models--backends)
4. [Context System](#4-context-system)
5. [UI Surfaces](#5-ui-surfaces)
6. [Quick Reference Card](#6-quick-reference-card)

---

## 1. Where Things Are

### File Locations at a Glance

| What                   | Path                                                 | Format | Editable at Runtime?    |
| ---------------------- | ---------------------------------------------------- | ------ | ----------------------- |
| **Main config**        | `apps/backend/configs/config.yaml`                   | YAML   | No (restart needed)     |
| **LLM backends**       | `apps/backend/configs/system/llm.default.yaml`       | YAML   | No (restart)            |
| **User LLM overrides** | `apps/backend/configs/system/llm.user.yaml`          | YAML   | No (restart)            |
| **Core defaults**      | `apps/backend/configs/system/core.default.yaml`      | YAML   | No                      |
| **Bootstrap**          | `apps/backend/configs/system/bootstrap.default.yaml` | YAML   | No                      |
| **Keys**               | `apps/backend/configs/system/keys.default.yaml`      | YAML   | No                      |
| **Ed3N config**        | `apps/backend/configs/system/ed3n.default.yaml`      | YAML   | No                      |
| **Timing**             | `apps/backend/configs/system/timing.default.yaml`    | YAML   | No                      |
| **Capacity**           | `apps/backend/configs/system/capacity.default.yaml`  | YAML   | No                      |
| **Game config**        | `apps/backend/configs/system/game.default.yaml`      | YAML   | No                      |
| **Crisis system**      | `apps/backend/configs/crisis_system_config.json`     | JSON   | No                      |
| **Personality**        | `apps/backend/configs/personality_profiles/`         | YAML   | No                      |
| **Formula configs**    | `apps/backend/configs/formula_configs/`              | YAML   | No                      |
| **Performance**        | `apps/backend/configs/performance_config.yaml`       | YAML   | No                      |
| **Environment**        | `.env` (project root)                                | dotenv | No (restart)            |
| **Learned config**     | `data/angela_learned/*.yaml`                         | YAML   | **Yes** (Angela writes) |
| **Desktop settings**   | `<user_data>/settings.json`                          | JSON   | **Yes** (GUI)           |
| **Version manifest**   | `apps/backend/configs/version_manifest.json`         | JSON   | No                      |

### Config Priority (Low → High)

```
*.default.yaml  →  *.user.yaml  →  *.evolved.yaml  →  .env  →  Learned (data/angela_learned/)
```

Angela merges all layers; higher-priority layers override lower ones.

---

## 2. Configuration & Settings

### 2.1 Deployment Modes (`llm.default.yaml`)

The `deployment.mode` field controls which AI backends are allowed:

| Mode        | What's Allowed                                      | Use Case                           |
| ----------- | --------------------------------------------------- | ---------------------------------- |
| `local`     | Only local models (ED3N, GARDEN, Ollama, llama.cpp) | No internet, privacy-first         |
| `local+llm` | Local + cloud LLM (opt-in)                          | Best quality when online           |
| `llm`       | Only cloud LLM (OpenAI, Anthropic, Google)          | Maximum quality, requires API keys |
| `auto`      | All backends open; engine auto-selects              | Hands-off, best-effort             |

**Where to change**: `apps/backend/configs/system/llm.default.yaml` →
`deployment.mode`

```yaml
deployment:
  mode: local # Change to: local | local+llm | llm | auto
  selection: available # available = only healthy backends; per-vendor = register all, fallback on fail
```

### 2.2 Environment Variables (`.env`)

Create `.env` from `.env.example`:

```bash
# LLM backend (at least one needed for conversation)
OLLAMA_HOST=http://localhost:11434
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=AIza...

# System
LOG_LEVEL=INFO
SECRET_KEY=your-secret-key

# Google Drive (optional)
GOOGLE_DRIVE_CREDENTIALS=path/to/credentials.json
```

### 2.3 Three-Mode Configuration (`config.yaml`)

Angela supports **Lite / Standard / Extended** modes based on hardware:

| Mode         | RAM     | GPU            | Features                        | LLM                             |
| ------------ | ------- | -------------- | ------------------------------- | ------------------------------- |
| **Lite**     | 4 GB    | ❌             | Basic chat, no learning         | tinyllama-1.1b (Ollama)         |
| **Standard** | 8–16 GB | Optional       | Full chat, learning, memory     | gpt-3.5-turbo + Ollama fallback |
| **Extended** | 16+ GB  | ✅ Recommended | Everything + dreaming, self-mod | gemini-pro / gpt-4              |

**Where**: `apps/backend/configs/config.yaml` → `angela_modes`

### 2.4 Desktop App Settings (GUI)

The Electron desktop app has a full **Settings** window:

| Setting                  | Location in Settings         | What It Does                   |
| ------------------------ | ---------------------------- | ------------------------------ |
| **Always on Top**        | General → Window             | Pin Angela above other windows |
| **Auto-start**           | General → Window             | Launch on system boot          |
| **Window Opacity**       | General → Window             | Adjust transparency (0.1–1.0)  |
| **Idle Mode**            | General → Behavior           | Enable autonomous behaviors    |
| **Response Sensitivity** | General → Behavior           | Low / Medium / High            |
| **Active Model**         | Appearance → Model Selection | Switch Live2D character model  |
| **Model Scale**          | Appearance → Model Selection | Resize character (0.5x–2.0x)   |
| **Render Mode**          | Appearance → Rendering       | Live2D (animated) vs Static    |
| **Wallpaper Mode**       | Appearance → Wallpaper       | Overlay / Behind / None        |
| **TTS Engine**           | Audio → Text-to-Speech       | Engine selection               |
| **TTS Voice**            | Audio → Text-to-Speech       | Voice selection                |
| **Haptic Feedback**      | Haptics                      | Enable/disable vibration       |
| **Network**              | Network & Cluster            | Backend URL, cluster settings  |
| **Advanced**             | Advanced                     | Debug mode, log level, reset   |

**How to open**: ⚙️ button in toolbar, or system tray → Settings, or
`Ctrl+Shift+S`

### 2.5 REPL Configuration Commands

In the CLI REPL mode, use these commands:

```
/config, /cfg    — Show current YAML config summary (intents, thresholds, LLM providers, fallback chain)
/route, /r       — Show LLM routing status (backends, active, fallback chain, stats)
/model list      — List all available LLM backends
/model stats     — Show LLM usage statistics
/model switch X  — Switch active backend to X
/model auto      — Enable auto-routing mode
```

### 2.6 API Configuration Discovery

```bash
# System status (CPU, memory, disk)
curl http://localhost:8000/api/v1/ops/status

# Health check
curl http://localhost:8000/api/v1/ops/health

# Full system metrics
curl http://localhost:8000/api/v1/ops/metrics

# Desktop state (Live2D, actions)
curl http://localhost:8000/api/v1/desktop/state

# Action executor status
curl http://localhost:8000/api/v1/actions/status

# Image generation status
curl http://localhost:8000/api/v1/image/status

# Multimodal health
curl http://localhost:8000/api/v1/multimodal/health
```

---

## 3. AI Models & Backends

### 3.1 Available Backends

| Backend ID         | Type  | Provider  | Enabled | Notes                                                  |
| ------------------ | ----- | --------- | ------- | ------------------------------------------------------ |
| `unified-1g`       | local | unified   | ✅      | Fixed-size statistical core + deterministic math/logic |
| `llamacpp-local`   | local | llama_cpp | ❌      | Local llama.cpp server (manual start)                  |
| `ollama-llama3`    | local | ollama    | ✅      | Ollama with qwen3.5:0.8b                               |
| `openai-gpt4o`     | cloud | openai    | ❌      | Requires OPENAI_API_KEY                                |
| `anthropic-claude` | cloud | anthropic | ❌      | Requires ANTHROPIC_API_KEY                             |
| `google-gemini`    | cloud | google    | ❌      | Requires GOOGLE_API_KEY                                |

**Where to configure**: `apps/backend/configs/system/llm.default.yaml` →
`backends`

### 3.2 Model Selection Logic

When `deployment.mode = auto`, the **NeuroAutoSelector** picks the best backend:

1. **Hardware capability** → score from SystemHardwareProbe (CPU, RAM, GPU)
2. **System load** → time budget (simple/fast vs complex/thorough)
3. **Task complexity** → intent classification (factual, creative, reasoning)
4. **8D state matrix** → correction from alpha.energy, epsilon.precision,
   theta.novelty
5. **Backend selection** → ranked by priority, health, and compatibility

### 3.3 Switching Models

**REPL**:

```
/model list                     # See what's available
/model switch ollama-llama3     # Switch to Ollama
/model switch unified-1g        # Switch to unified engine
/model auto                     # Let Angela auto-select
```

**API** (programmatic):

```bash
# Check current backend
curl http://localhost:8000/api/v1/ops/status | jq '.llm_backend'

# Persist settings (Desktop Settings → llm.user.yaml; restart to take effect)
curl -X POST http://localhost:8000/api/v1/llm/config \
  -H "Content-Type: application/json" \
  -d '{"deployment.mode": "local+llm", "settings.defaults.temperature": 0.8}'
# Read back current effective values
curl http://localhost:8000/api/v1/llm/config
```

Persisted keys (whitelist; anything else → 400): `deployment.mode`,
`deployment.selection`, `settings.defaults.temperature` (0–2),
`settings.defaults.max_tokens` (1–8192), `settings.llm_mode`,
`settings.enable_memory_enhancement`, `settings.memory.max_history`,
`settings.preferred_backend` (honoured at next router init),
`web_search.enabled`.

**Config** (permanent change): Edit
`apps/backend/configs/system/llm.default.yaml`:

```yaml
backends:
  ollama-llama3:
    enabled: true # ← toggle
    model_name: 'qwen3.5:0.8b' # ← change model
  openai-gpt4o:
    enabled: true # ← enable cloud
```

### 3.4 Without an LLM

If no external LLM is configured, Angela falls back to:

- **Unified Engine** (`unified-1g`): statistical core + deterministic
  math/logic + semantic QA
- **ED3N**: dictionary-based neural network (association learning)
- **GARDEN**: lightweight reasoning engine

Capabilities without LLM: basic conversation, math (9.5/10), factual QA (10/10),
symbolic reasoning (10/10). No open-domain creative conversation.

### 3.5 Web Search (Always Available)

Regardless of `deployment.mode`, web search is always enabled:

```yaml
web_search:
  enabled: true
  provider: duckduckgo # duckduckgo | wikipedia | both
  max_results: 3
  timeout: 2.5
```

Provides grounded factual lookup as a base tool.

---

## 4. Context System

### 4.1 What Context Exists

Angela maintains multiple context layers:

| Context Type         | What It Holds                              | Where It Lives                              |
| -------------------- | ------------------------------------------ | ------------------------------------------- |
| **Tool Context**     | Available tools, categories, usage history | `ToolContextManager` (in-memory)            |
| **Model Context**    | Model capabilities, parameters, health     | `ModelContextManager` (in-memory)           |
| **Agent Context**    | Agent roles, skills, task assignments      | `AgentContextManager` (in-memory)           |
| **Dialogue Context** | Conversation history, session state        | `DialogueContextManager` (in-memory + disk) |
| **Memory Context**   | Long-term memories (ChromaDB vectors)      | `MemoryContextManager` (ChromaDB)           |
| **8D State Matrix**  | α β γ δ ε θ ζ η emotional/cognitive state  | `StateMatrix` (in-memory)                   |

### 4.2 Viewing Context

**REPL commands**:

```
/state, /s       — View 8D state matrix with visual bars
/memory, /m [q]  — View memory summary (optionally search by keyword)
/intent, /i      — View intent registry as a clean table
/route, /r       — View LLM routing detail with backend health
/config, /cfg    — View config summary with deployment mode + warnings
/ctx             — Full context overview (state + memory + models + config)
/ctx state       — State matrix only
/ctx models      — LLM backends only
/ctx memory      — Memory status only
/ctx config      — Config summary only
/model list      — All backends with health status + active marker
/model switch X  — Switch active backend
```

**API endpoints**:

```bash
# System state
curl http://localhost:8000/api/v1/ops/status

# Memory (via chat service)
curl -X POST http://localhost:8000/api/v1/chat/unified \
  -H "Content-Type: application/json" \
  -d '{"message": "show me your memories"}'

# Multimodal context
curl http://localhost:8000/api/v1/multimodal/health
curl http://localhost:8000/api/v1/multimodal/cml/stats
```

### 4.3 8D State Matrix Dimensions

Each dimension represents an aspect of Angela's internal state:

| Dimension   | Symbol | What It Tracks                                  |
| ----------- | ------ | ----------------------------------------------- |
| **Alpha**   | α      | Energy, comfort, arousal                        |
| **Beta**    | β      | Focus, curiosity, learning rate                 |
| **Gamma**   | γ      | Happiness, trust, anticipation                  |
| **Delta**   | δ      | Bond, trust, attention                          |
| **Epsilon** | ε      | Precision, confidence, accuracy                 |
| **Theta**   | θ      | Novelty, correction urge                        |
| **Zeta**    | ζ      | (Reserved)                                      |
| **Eta**     | η      | Execution count, success rate, structural drift |

Values range 0.0–1.0. View with `/state` in REPL.

### 4.4 Memory System

Angela has multi-layer memory:

| Layer  | Type                     | Retention     | Access     |
| ------ | ------------------------ | ------------- | ---------- |
| **L1** | Sensory (raw input)      | Seconds       | Automatic  |
| **L2** | Working (active context) | Minutes–Hours | Automatic  |
| **L3** | Episodic (experiences)   | Days–Weeks    | Searchable |
| **L4** | Semantic (knowledge)     | Permanent     | Searchable |
| **L5** | Procedural (skills)      | Permanent     | Automatic  |

**Viewing memories**:

```
/memory              — Show recent memories
/memory sadness      — Search for memories about "sadness"
/memory experience   — Search for experience memories
```

### 4.5 Intent System

Angela classifies user messages into intents for routing:

| Intent     | Keywords (examples)    | Handler              |
| ---------- | ---------------------- | -------------------- |
| `greeting` | hello, hi, hey, 你好   | Chat pipeline        |
| `question` | what, how, why, 什麼   | Knowledge base + LLM |
| `emotion`  | sad, happy, angry      | Emotion system       |
| `creative` | draw, write, imagine   | Creative agent       |
| `code`     | code, program, debug   | Code agent           |
| `math`     | calculate, solve, 數學 | MathVerifier         |
| `memory`   | remember, forget, 記住 | Memory system        |

**View all intents**: `/intent` in REPL

---

## 5. UI Surfaces

### 5.1 Desktop App (Electron + Live2D)

| Element              | What It Shows            | How to Interact                |
| -------------------- | ------------------------ | ------------------------------ |
| **Live2D Character** | Angela's animated avatar | Click/touch to interact        |
| **Chat Bubble**      | Conversation messages    | Type in input field            |
| **Toolbar**          | Quick actions            | ⚙️ Settings, 📷 Camera, 🎤 Mic |
| **System Tray**      | Background controls      | Right-click for menu           |
| **Settings Window**  | Full configuration       | ⚙️ or Ctrl+Shift+S             |

**Toolbar buttons**:

- ⚙️ **Settings** — Opens settings window
- 📷 **Screenshot** — Capture current view
- 🎤 **Voice** — Toggle voice input
- 🔄 **Reset** — Reset to default state

### 5.2 Web Dashboard (Next.js)

Access at `http://localhost:3000`:

| Panel                 | What It Shows                    | API Endpoint           |
| --------------------- | -------------------------------- | ---------------------- |
| **ChatPanel**         | Conversation interface           | `/api/v1/chat/unified` |
| **PetPanel**          | Virtual pet interactions         | Pet state APIs         |
| **SystemMonitor**     | CPU, memory, uptime, connections | `/api/v1/ops/metrics`  |
| **MemoryViewer**      | Search/filter memories           | `/api/memories`        |
| **EconomyPanel**      | (Backend removed in Phase 11)    | N/A                    |
| **LearningDashboard** | (Backend removed in Phase 11)    | N/A                    |

### 5.3 CLI REPL

Start with: `python scripts/run_angela.py --repl`

```
┌──────────────────────────────────────────────────────────┐
│  Angela REPL — Full Command Reference                     │
├──────────────────────────────────────────────────────────┤
│  /help, /h         — This help                           │
│  /state, /s        — 8D state matrix snapshot            │
│  /memory, /m [q]   — Memory summary (optional search)   │
│  /config, /cfg     — YAML config summary                 │
│  /intent, /i       — Intent registry overview            │
│  /route, /r        — LLM routing status                  │
│  /model [sub]      — LLM model management                │
│    list              — List available backends            │
│    stats             — Show usage statistics              │
│    switch <name>     — Switch active backend              │
│    auto              — Enable auto-routing                │
│  /tickle, /tkl     — Tickle reflex system                │
│  /drive [sub]      — Google Drive operations             │
│  /clear, /c        — Clear screen                        │
│  /history          — Recent command history              │
│  /eval <expr>      — Evaluate Python expression          │
│  exit/quit         — Stop REPL                           │
└──────────────────────────────────────────────────────────┘
```

### 5.4 REPL Boot Banner

When the REPL starts, it shows a **status banner** with:

- LLM backend status (active backend, mode, or ❌ + fix hints)
- Memory manager status
- 8D state energy bar

If something is broken, **actionable hints** (💡) tell you exactly how to fix
it:

```
── Boot Status ──────────────────────────────────────
  LLM:      ❌ No backend available
  💡 Add Ollama: install from https://ollama.ai, then 'ollama pull qwen3.5:0.8b'
  💡 Or add API key: set OPENAI_API_KEY in .env and deployment.mode: local+llm in llm.default.yaml
  Memory:   ✅ initialized
  State:    [██████████████░░░░░░] 0.70 (α.energy)
```

## 5.5 Swagger / API Docs

Access at `http://localhost:8000/docs` — auto-generated API documentation for
all endpoints.

---

## 6. Quick Reference Card

### "I want to…"

| Goal                       | How                                                                                |
| -------------------------- | ---------------------------------------------------------------------------------- |
| **Change LLM backend**     | Edit `llm.default.yaml` → `backends.X.enabled: true`, or `/model switch X` in REPL |
| **Use cloud AI**           | Set `deployment.mode: local+llm` + add API key in `.env`                           |
| **View system state**      | `/state` in REPL or `GET /api/v1/ops/status`                                       |
| **Search memories**        | `/memory <keyword>` in REPL or `POST /api/v1/chat/unified` with memory query       |
| **See what intents exist** | `/intent` in REPL                                                                  |
| **Check LLM status**       | `/route` in REPL or `GET /api/v1/ops/status`                                       |
| **Switch Live2D model**    | Settings → Appearance → Active Model (desktop app)                                 |
| **Adjust transparency**    | Settings → General → Window Opacity (desktop app)                                  |
| **Enable voice**           | Settings → Audio → TTS Engine (desktop app)                                        |
| **View API docs**          | Open `http://localhost:8000/docs` in browser                                       |
| **Run in auto mode**       | Set `deployment.mode: auto` in `llm.default.yaml`                                  |
| **Add Ollama models**      | `ollama pull <model>` then update `model_name` in `llm.default.yaml`               |
| **Reset all settings**     | Desktop: Settings → Advanced → Reset All Settings                                  |
| **Check health**           | `GET /api/v1/ops/health`                                                           |
| **See what's broken**      | `GET /api/v1/ops/status` + check logs                                              |

### "Where is…?"

| Item             | Location                                         |
| ---------------- | ------------------------------------------------ |
| LLM config       | `apps/backend/configs/system/llm.default.yaml`   |
| User overrides   | `apps/backend/configs/system/llm.user.yaml`      |
| Learned configs  | `data/angela_learned/*.yaml`                     |
| Desktop settings | `<userData>/settings.json` (platform-specific)   |
| Environment vars | `.env` (project root)                            |
| Crisis config    | `apps/backend/configs/crisis_system_config.json` |
| Personality      | `apps/backend/configs/personality_profiles/`     |
| Formulas         | `apps/backend/configs/formula_configs/`          |
| Logs             | `logs/` directory                                |
| Test storage     | `test_storage/`                                  |
| Context storage  | `context_storage/`                               |

---

_Last Updated: 2026-09-16 | See also: [USER_GUIDE.md](USER_GUIDE.md),
[QUICK_START.md](usage/QUICK_START.md)_
