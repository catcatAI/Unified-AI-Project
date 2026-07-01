<!--
  =============================================================================
  VERSION: 7.5.0-dev
  STATUS: active
  LANGUAGE: zh-tw/en
  LAST_MODIFIED: 2026-07-01 (updated for §X #88)
  =============================================================================
-->

# Angela AI v7.5.0-dev — Cross-Platform Digital Life System

[English](#english-version) | [繁體中文](#繁體中文版)

---

## 📑 Index

<details>
<summary><b>English</b></summary>

- [English Version](#english-version)
  - [Current Status](#current-status-code-verified-as-of-2026-06-15)
  - [Quick Start](#quick-start)
  - [Scripts Reference](#scripts-reference)
  - [What Actually Works](#what-actually-works-code-verified-2026-06-15)
  - [What's Broken / Never Finished](#what-does-not-work--is-stub)
  - [Orphaned Systems](#orphaned-systems-status)
  - [Roadmap](#roadmap--future-phases)
  - [Documentation Index](#documentation-index)
</details>

<details>
<summary><b>繁體中文</b></summary>

- [繁體中文版](#繁體中文版)
  - [當前進度](#當前進度2026-06-15-代碼驗證)
  - [快速啟動](#快速啟動-1)
  - [腳本參考](#腳本參考)
  - [什麼能跑](#什麼能跑2026-06-15-驗證)
  - [什麼不能用](#什麼無法運作-1)
  - [未來路線圖](#修正後路線圖)
  - [文件索引](#架構文件)
</details>

---

<a name="english-version"></a>

## English Version

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active%20Development-yellow.svg)]()
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-blue.svg)]()

**Angela AI** is a digital life system with biological simulation and LLM integration capabilities.

**Quick facts**: 612 Python files in backend src (~96K lines). Electron + Live2D desktop companion (50 JS files across shared-js/desktop/web). Pixel art engine (PyQt6 renderer). **~5,085 tests (full) / ~4,726 tests (tests/) — 0 errors.**  
**Component versions**: backend `7.5.0-dev` · desktop `7.5.0-dev` · cli `7.5.0-dev` · biology-core `7.5.0-dev`.  
**Architecture audit score**: **~85-90%** (2026-06-25; up from ~55-60% after Phases 0-5 repairs).  
**Total project files**: ~3,500+ (620 Python in backend src · 295 JS/TS · 1,021+ docs · 500+ config · 480+ test).  
See [AGENTS.md](AGENTS.md) for developer/agent guidelines, [CHANGELOG.md](CHANGELOG.md) for version history, and [COMPREHENSIVE_AUDIT_2026-06-25.md](docs/COMPREHENSIVE_AUDIT_2026-06-25.md) for latest audit.

> **STATUS (2026-07-01)**: Latest §X #80-#88: EmotionSystem C³ 4.0 (§X #80), IntentModel C³ 3.0 (§X #81), CausalReasoningEngine C³ 4.0 (§X #82), MetaController C³ 4.0 closed-loop (§X #83), ExecutionGate C³ 5.0 feedback loop (§X #84), AutonomousLifeCycle config-driven thresholds (§X #85), test consolidation (§X #86 — 4 redundant files deleted), MD sync (§X #87), orphan-to-skip test conversion (§X #88 — 3 orphan files → 9 skip tests). Real CIFAR-10 data training (§X #79). GlobalSystemClock unified time base (§X #76-77). **~5,085 tests (full) / 4,726 tests (tests/) — 0 errors.** Architecture: ~85-90%.
> **PIPELINE**: WebSocket → emotion → crisis gate → alignment gate → execution gate → **agent routing** → LLM → causal learning → response. GVV pipeline for image generation.  
> **See**: [MASTER_TASK_MAP.md](docs/06-project-management/MASTER_TASK_MAP.md) (task provenance), [IMPROVEMENT_ROADMAP.md](docs/06-project-management/IMPROVEMENT_ROADMAP.md) (improvement roadmap), [CAUSAL_CHAIN_COMPLETENESS.md](docs/06-project-management/CAUSAL_CHAIN_COMPLETENESS.md) (causal depth).

---

### Current Status (code-verified as of 2026-07-01)

| Area | Status | Key evidence |
|------|--------|-------------|
| **Server starts** | ✅ IMPORTS OK | `main_api_server.py` imports successfully |
| **Chat pipeline** | ✅ FULLY WIRED | Complete: WebSocket → emotion → crisis → alignment → execution gate → agent routing → LLM → causal learning → response |
| **CrisisSystem** | ✅ INTEGRATED | Safety gate in `chat_routes.py:142-151`, auto-reset timeout, config loaded |
| **CausalReasoning** | ✅ INTEGRATED | Fire-and-forget learning after every response, FIFO cap (500/1000) |
| **Level5ASI** | ✅ INTEGRATED | Alignment gate triggered at crisis_level ≥ 2, lazy-initialized |
| **ModelEnsemble** | ✅ INTEGRATED | Multi-model voting via `context["use_ensemble"] = True` |
| **11 Agents** | ✅ REGISTERED | AgentAdapter wraps all agents with `execute()` interface |
| **QueryClassifier** | ✅ EXTENDED | 16 QueryTypes (FILE, SEARCH, CODE, EXECUTE, TASK, VISION, AUDIO, OPINION) |
| **ModelBus** | ✅ EXTENDED | Handler registration + handler-first routing for FILE/SEARCH/CODE/EXECUTE/TASK |
| **Autonomous Cognition** | ✅ INTEGRATED | AutonomousLifeCycle + θ Router + 5 formula metrics injected into prompts |
| **Vision Endpoints** | ✅ IMPLEMENTED | `/vision/analyze` + `/chat/with-image` endpoints |
| **Image Generation** | ✅ IMPLEMENTED | GVV + ThreeLayerVisual, 10 endpoints (5 deprecated + 5 standardized `/image/`), 14 source files, ~62 tests |
| **AgentOrchestrator** | ✅ COMPLETE | Intent classification, agent selection, task decomposition (Phase 2) |
| **PlanningEngine** | ✅ COMPLETE | Goal decomposition, dependency tracking, progress monitoring (Phase 2) |
| **ReasoningEngines** | ✅ COMPLETE | ChainOfThought, Analogical, Abductive reasoning (Phase 2) |
| **TrustManager** | ✅ COMPLETE | User trust scoring, permission control, violation tracking (Phase 3) |
| **ContentFilter** | ✅ COMPLETE | Toxicity detection, PII filtering, safety classification (Phase 3) |
| **SafetyAudit** | ✅ COMPLETE | Audit trail, compliance checks, alert system (Phase 3) |
| **Web Dashboard** | ✅ COMPLETE | Next.js: ChatPanel, PetPanel, SystemMonitor, EconomyPanel, LearningDashboard (Phase 4) |
| **Docker/CI/CD** | ✅ COMPLETE | Dockerfile, docker-compose, Prometheus, Grafana, Nginx, GitHub Actions deploy (Phase 5) |
| **OpenTelemetry** | ✅ COMPLETE | Tracing middleware (Phase 5) |
| **API Versioning** | ✅ COMPLETE | Version routing middleware (Phase 5) |
| **i18n System** | ✅ COMPLETE | I18nManager, PromptManager, 4 handlers + 4 LLM modules i18n'd, 45 tests (Phase 7) |
| **Config system** | ✅ | `config_loader.py:get_config()` returns Config |
| **Tests** | ✅ PASSING | ~5,085 tests collected (full) / ~4,726 (tests/), 0 errors, 0 collection errors |
| **JS Sharing** | ✅ COMPLETE | 33 shared files → `packages/shared-js/js/`, 0 duplicates remaining |
| **SessionManager** | ✅ COMPLETE | 56 tests covering full lifecycle (Phase 5.8) |
| **Skip Audit** | ✅ COMPLETE | Phase 5.9: 5 collection errors fixed, all skip reasons verified |
| **Architecture Audit** | ✅ CREATED | `docs/COMPREHENSIVE_AUDIT_2026-06-25.md` — ~55-60% → ~85-90% after all 6 phases |
| **Target Blueprint** | ✅ CREATED | `docs/IDEAL_ARCHITECTURE.md` — 16-section target architecture |
| **Repair Roadmap** | ✅ COMPLETE | `docs/COMPREHENSIVE_REPAIR_ROADMAP.md` — all 6 phases executed, 0 remaining tasks |
| **Master Task Map** | ✅ CREATED | `docs/06-project-management/MASTER_TASK_MAP.md` — all 23 plans cross-referenced with git/code |
| **Causal Chain Completeness** | ✅ CREATED | `docs/06-project-management/CAUSAL_CHAIN_COMPLETENESS.md` — §0 no-stub principle, real depth scores, timing audit |
| **EmotionSystem Behavioral Driving** | ✅ **DONE** | `apply_influence()` now modifies PAD state, `get_behavioral_adjustment()` maps emotion→routing_mode/response_style, wired into pipeline Step 5 → prompt builder reads it |
| **MetaController Auto-apply** | ✅ **DONE** | `auto_apply_thresholds()` now adjusts reasoning/quality/high_demand thresholds in NeuroAutoSelector._analyze_task() |
| **LifeCycle 6/6 States** | ✅ **DONE** | INITIALIZING, AWAKENING, GROWING, MATURE, RESTING, DORMANT — all 6 have distinct behaviors in _apply_state_behaviors() |
| **Heartbeat Integration Freq** | ✅ **FIXED** | Integration loop 0.1s → 2.0-10.0s dynamic based on arousal (was 50-600x mismatch, now ~2x) |
| **Level5ASI Simulated Sleep** | ✅ **FIXED** | Removed `await asyncio.sleep(1.0)` simulated processing delay |
| **IntentModel Production Wiring** | ✅ **DONE** | IntentManager wired into DigitalLifeIntegrator._life_cycle_loop(): homeostatic intents → get_intent_influence() → state matrix update (energy/focus/happiness/bond). Closed loop! |
| **Autonomy Decision Speed** | ✅ **FIXED** | AutonomousLifeCycle decision_interval 300s→60s (5x faster, §8.6 #8) |
| **create_task Exception Handlers** | ✅ **DONE** | **16 tasks in 13 files** — added 6 more protected loops: action_execution_bridge._execution_loop + 5 bio loops (ANS, EmotionalBlending, MultidimensionalTrigger, Neuroplasticity, Tactile). All background loops now have exception handling (§8.6 #7) |
| **Bridge Event-Driven Wait** | ✅ **DONE** | `_wait_for_completion` busy-poll (0.05s, 20Hz) → `asyncio.Event`. Also consolidated `emotion_tick→emotion_update`, `bridge_fast→bridge_error_backoff`. §8.6 #2: 3/4 loop pairs consolidated (§8.6 #2/#3) |
| **HardwareProfile** | ✅ **DONE** | `hardware_profile.py`: 5 hardware scenarios (desktop/laptop/power-saver/low-power/server) + 22 interval fields + auto-detection + runtime overrides. 20 tests (§8.6 #5) |
| **HardwareProfile → loop_sleep()** | ✅ **DONE** | `magic_numbers.py` now loads HardwareProfile lazily and applies multiplier to all 32+ loops. All loops now hardware-aware (§8.6 #4 BASIC) |
| **time.sleep() Audit** | ✅ **DONE** | All remaining `time.sleep()` calls verified in sync/thread contexts only. §8.6 #6 effectively complete |

See **[COMPREHENSIVE_AUDIT_2026-06-25.md](docs/COMPREHENSIVE_AUDIT_2026-06-25.md)** (latest audit), **[IDEAL_ARCHITECTURE.md](docs/IDEAL_ARCHITECTURE.md)** (target), **[COMPREHENSIVE_REPAIR_ROADMAP.md](docs/COMPREHENSIVE_REPAIR_ROADMAP.md)** (plan), **[MASTER_TASK_MAP.md](docs/06-project-management/MASTER_TASK_MAP.md)** (task provenance), **[CAUSAL_CHAIN_COMPLETENESS.md](docs/06-project-management/CAUSAL_CHAIN_COMPLETENESS.md)** (causal depth), **[IMPROVEMENT_ROADMAP.md](docs/06-project-management/IMPROVEMENT_ROADMAP.md)** (improvement roadmap).

### Intelligence Assessment (Code-Verified 2026-06-29)

Upper bound (with LLM API: OpenAI/Anthropic/Ollama) vs lower bound (ED3N+GARDEN only):

| Capability | Upper | Lower | Status |
|:-----------|:-----:|:-----:|:-------|
| **Text understanding** | 7/10 | 5/10 | ED3N 460K dictionary + GARDEN SNN, real multilingual |
| **Image understanding** | 7/10 | 5/10 | CLIP 512-dim real, VisionService PIL-based |
| **Speech understanding** | 5/10 | 3/10 | faster-whisper 1.2.1 int8 offline STT active via AudioService._stt_faster_whisper() |
| **Text generation** | 7/10 | 4/10 | 7 LLM backends, ED3N reflex+shallow fallback |
| **Image generation** | 6/10 | 6/10 | GVV + ThreeLayerVisual, MSE 0.0042, no Stable Diffusion |
| **Speech generation** | 4/10 | 2/10 | edge-tts works (reading only, no singing) |
| **Memory** | 7/10 | 7/10 | VectorStore 460K + HAM templates + ED3N dictionaries |
| **Reasoning** | 4/10 | 3/10 | Framework exists (causal, CoT, analogical), depth limited |
| **Autonomy** | 3/10 | 3/10 | AutonomousLifeCycle wired, behavior unstable |
| **Meta-cognition** | 5/10 | 4/10 | MetaController: confidence calibration + LLM thresholds |
| **Composite** | **6.0/10** | **4.5/10** | Architecture: ~85-90%. Actual capabilities: limited by ML model depth |

**Key**: Upper bound = connected to external LLM (realistic full-power scenario). Lower bound = ED3N+GARDEN only (no-cost fallback). See [PHASE_REVIEW6.md §4](docs/06-project-management/plans/PHASE_REVIEW6.md) for full methodology.

### Quick Start

```bash
# Clone
git clone https://github.com/catcatAI/Unified-AI-Project.git
cd Unified-AI-Project

# (Recommended) Setup and activate Python virtual environment (.venv)
python -m venv .venv
# On Windows PowerShell:
.venv\Scripts\Activate.ps1
# On macOS/Linux:
source .venv/bin/activate

# Install Python backend dependencies
pip install -r apps/backend/requirements.txt

# Install JS workspace dependencies using pnpm (use npx if pnpm is not installed globally)
npx pnpm install --no-frozen-lockfile
npx pnpm approve-builds --all

# Option 1: Use unified launcher (Recommended)
python scripts/run_angela.py              # Start all (backend + desktop)
python scripts/run_angela.py --api-only   # Backend only
python scripts/run_angela.py --health-check  # Health check

# Option 2: Start backend directly
python apps/backend/start_server.py

# Option 3: Start desktop app (separate terminal)
npx pnpm dev:desktop
```

**Prerequisites**: Python 3.10+, Node.js 16+, Ollama (LLM backend).

---

### Scripts Reference

| Category | Script | Description |
|----------|--------|-------------|
| **Launch** | `scripts/run_angela.py` | Primary launcher (recommended) |
| **Launch** | `scripts/start_all.bat` | Start backend + frontend concurrently |
| **Launch** | `scripts/start_backend.bat` | Start backend in dev mode |
| **Launch** | `scripts/unified-ai.bat` | Comprehensive project launcher |
| **Health** | `scripts/check_auth_status.py` | Check authentication status |
| **Health** | `scripts/check_last_memories.py` | Inspect recent HAM memory entries |
| **Health** | `scripts/check_vec_store.py` | Verify vector store integrity |
| **Health** | `scripts/check_ports.ps1` | Check port availability |
| **Health** | `scripts/debug_memory.py` | Debug memory system issues |
| **Health** | `scripts/utils/health_check.py` | Full diagnostics |
| **Health** | `scripts/utils/check_resources.py` | System resource monitor |
| **Training** | `scripts/train_ed3n.py` | ED3N training |
| **Training** | `scripts/train_pipeline.py` | Training pipeline |
| **Training** | `scripts/generate_training_data.py` | Generate training data |
| **Drive** | `scripts/trigger_sync.py` | Manually trigger Drive sync |
| **Drive** | `scripts/verify_drive_analyzer.py` | Verify Drive Analyzer |
| **Dev** | `scripts/verify_ice_loop.py` | Verify ICE loop |
| **Dev** | `scripts/verify_phase_2_loop.py` | Verify Phase 2 reward loop |
| **Setup** | `scripts/setup_project.bat` / `.sh` | Initial project setup |
| **Setup** | `scripts/utils/init_config.py` | Configuration initialization |
| **Setup** | `scripts/utils/verify_p0_systems.py` | P0 systems verification |
| **Setup** | `scripts/utils/improve_live2d_loading.py` | Live2D loading optimization |

> Full list: [scripts/ACTIVE_SCRIPTS.md](scripts/ACTIVE_SCRIPTS.md)

---

### What Actually Works (Code-Verified 2026-06-29)

**Chat Pipeline (fully wired):**
- **Complete pipeline** — WebSocket → emotion analysis → crisis gate → biological stimulus → alignment gate → execution gate → agent routing → LLM → causal learning → response ✅
- **Session history** — 30-message rolling window, ED3N retrieval pool ✅
- **Emotion analysis** — 6-category emotion keywords, emotion-aware prompt injection ✅
- **Crisis system** — Safety gate auto-reset timeout (300s), config loaded from `apps/backend/configs/crisis_system_config.json` ✅
- **Level5ASI alignment** — Triggered at crisis_level ≥ 2, lazy-initialized ✅
- **CausalReasoning** — Fire-and-forget learning after every response, FIFO cap (500 obs / 1000 rels) ✅
- **ModelEnsemble** — Multi-model voting via `context["use_ensemble"] = True` ✅
- **Autonomous cognition** — AutonomousLifeCycle + θ Router + 5 formula metrics in prompts ✅
- **Vision endpoints** — `/vision/analyze` + `/chat/with-image` with image context ✅
- **Template matching** — 157 templates, 60s cached formula summaries ✅

**AI Systems:**
- **LLM providers** — All 8 providers: Anthropic, Google, OpenAI, Ollama, llama.cpp, ED3N, GARDEN ✅
- **QueryClassifier** — 16 QueryTypes (FILE, SEARCH, CODE, EXECUTE, TASK, VISION, AUDIO, OPINION, etc.) ✅
- **ModelBus** — Handler registration + handler-first routing ✅
- **11 Specialized Agents** — Registered via AgentAdapter, wrapped with `execute()` interface ✅
- **ED3N engine** — SNN, reflex layers, cross-modal processing ✅
- **GARDEN engine** — VectorDictionary, TensorSNNCore ✅

**i18n (Internationalization) System:**
- **I18nManager** — Multi-language translation management, JSON locale file loading ✅
- **PromptManager** — LLM prompt template management, language-aware selection ✅
- **Handler i18n** — 4 handlers completed (file_operation, task_manager, system_command, code_execution) ✅
- **Prompt Builder i18n** — 60+ prompt strings replaced with `prompt()` calls ✅
- **LLM Decision Loop i18n** — 40+ prompt strings replaced ✅
- **Locale files** — en-US.json, zh-CN.json, prompts.en-US.json, prompts.zh-CN.json ✅
- **Desktop App i18n** — zh-CN bug fixed, case-insensitive locale matching ✅

**Phase 0 — Foundation Fixes:**
- **Import fixes** — execution_manager.py, UCC await-in-sync, EnvironmentSimulator, duplicate lines ✅
- **Context subsystems activated** — dialogue_context, model_context, tool_context, memory_context, integration_with_ham ✅
- **DEPRECATED markers cleaned** — 9 packages cleaned ✅

**Phase 1 — Core Activation:**
- **Context wiring** — DialogueContext + MemoryContext injected in chat pipeline ✅
- **ED3N cycling** — Max 3 cycles, confidence threshold 0.7 ✅
- **GARDEN cycling** — Max 3 cycles, response length improvement check ✅
- **UnifiedLearningOrchestrator** — Connects 6 learning subsystems ✅

**Phase 2 — Intelligence Layer:**
- **AgentOrchestrator** — Intent classification, agent selection, task decomposition ✅
- **PlanningEngine** — Goal decomposition, dependency tracking, progress monitoring ✅
- **ReasoningEngines** — ChainOfThought, Analogical, Abductive reasoning ✅

**Phase 3 — Safety & Trust:**
- **TrustManager** — User trust scoring, permission control, violation tracking ✅
- **ContentFilter** — Toxicity detection, PII filtering, safety classification ✅
- **SafetyAudit** — Audit trail, compliance checks, alert system ✅

**Phase 4 — Embodiment:**
- **Web Dashboard** — Next.js: ChatPanel, PetPanel, SystemMonitor, EconomyPanel, LearningDashboard, MemoryViewer ✅

**Phase 5 — Infrastructure:**
- **Docker** — Multi-stage Dockerfile, docker-compose with Redis, PostgreSQL, Prometheus, Grafana, Nginx ✅
- **CI/CD** — GitHub Actions with staging/production deployment ✅
- **Monitoring** — Prometheus metrics, Grafana dashboards, alert rules ✅
- **OpenTelemetry** — Distributed tracing middleware ✅
- **API Versioning** — Version routing middleware ✅

**Phase 6 — Polish & Launch:**
- **Benchmarks** — ED3N, GARDEN, Classifier baselines ✅
- **Profiling** — Unified profiler with imports/memory modes ✅
- **OpenAPI** — Static spec export script ✅
- **Documentation** — Deployment guide, User guide ✅

**Core Infrastructure:**
- **Config system** — `config_loader.py:get_config()` ✅
- **State matrix** — 6D state matrix (αβγδεθ), 1,244 lines ✅
- **HSP connector** — 51 KB, full protocol with circuit breaker ✅
- **Action execution** — 48 KB, priority queue, dependency resolution ✅
- **Biological systems** — 8 modules with real code (20-46 KB each) ✅
- **ChromaDB memory** — HAM memory with vector store ✅
- **Desktop app** — Electron + Live2D, 7 unique + 33 shared JS files, Epsilon_free model ✅
- **Pixel art engine** — PyQt6 renderer, numpy voxel body ✅
- **CLI** — Unified CLI with HTTP client ✅
- **Gemini OS bridge** — pyautogui automation ✅
- **Test suite** — 4,902 total ✅

### What Does NOT Work / Needs Work

- **YOLO object detection** — Not started ❌
- **`/multimodal/stream` WebSocket route** — Dedicated handler (`multimodal_ws_handler.py`) + route registered ✅
- **Whisper faster-whisper in ChatService** — Installed and wired: offline high-quality STT via AudioService._stt_faster_whisper() ✅
- **Agent auto-routing** — Wired into chat pipeline Step 8 (creative/knowledge/opinion/vision/audio) ✅
- **VisualDecoder training** — T1 DONE: Full pipeline (projection + texture) trainable, projection weights trained (42× CIFAR-10 loss reduction) ✅
- **P4 refactoring** — 25/31 >100L long functions refactored (3 pure-data + 3 algorithmic remain), load/stress/E2E tests, desktop tray — partial ⏳
- **Auto-repair pathway** — `run_angela.py` now has auto-install on missing deps (--auto-repair flag, or interactive prompt) ✅

### Deleted (Phase 9-12 Cleanup) — Do Not Re-implement
- **Mobile app** — Was skeleton (3 files), deleted in Phase 11 🗑️
- **TactileService** — Was stub (66 lines), no hardware support, deleted in Phase 11 🗑️
- **ImageGenerationAgent** — Was stub always returning "unavailable", deleted in Phase 9 🗑️
- **ComfyUIClient/AngelaRealPainter** — Stubs with `image_url: None`, deleted in Phase 10 🗑️
- **`services/wiring.py`** — Dead code never called, deleted in Phase 11 🗑️
- **11 dead subsystems** (learning/ops/dialogue/evaluation/execution/code_inspection/compression/lis/language_models/integration/symbolic_space) — Deleted in Phase 11b 🗑️
- **5 dead modules** (code_understanding/personality/time/translation/distributed) — Deleted in Phase 12 🗑️
- **Trust module** — Deleted in Phase 12b 🗑️
- **`ai/security/`** — Empty module, deleted in Phase 9 🗑️
- **`comic_composer.py`** — Placeholder URL, deleted in Phase 9 🗑️

### Orphaned Systems Status

| Category | Count | Action |
|----------|-------|--------|
| **Wired into pipeline** | 6 | CrisisSystem, CausalReasoning, Level5ASI, ModelEnsemble, 11 Agents, AgentManager |
| **Deleted (stubs/duplicates)** | 18 | services/ai_editor_config.py, services/ai_virtual_input_service.py, plus Phase 11 deleted subsystems |
| **Retained but unwired** | 18 | real_time_monitor, event_loop_system, execution_manager, language_models/, etc. |
| **Deleted (Phase 1 cleanup)** | 12 | modules/ directory removed (12 wrapper files) |

### Roadmap / Future Phases

| Phase | Focus | Status | Priority |
|:------|:------|:------:|:--------:|
| **Chat Pipeline** | Full wiring: emotion → crisis → alignment → LLM → causal learning | ✅ **DONE** | 🔴 CRITICAL |
| **Orphaned Systems** | Wire 6 systems, delete 16 stubs, retain 18 for future | ✅ **DONE** | 🔴 CRITICAL |
| **Bug Fixes** | 15 bugs fixed across ensemble, causal, crisis, level5, adapter | ✅ **DONE** | 🔴 CRITICAL |
| **Architecture Doc** | `ANGELA_FULL_ARCHITECTURE.md` — 1183 lines, 35KB | ✅ **DONE** | 🟡 MEDIUM |
| **Phase 0-6** | Foundation, Core, Intelligence, Safety, Embodiment, Infrastructure, Polish | ✅ **DONE** | 🔴 CRITICAL |
| **i18n Internationalization** | I18nManager, PromptManager, Handler/Prompt replacement, Locale files | ✅ **DONE** | 🟡 MEDIUM |
| **YOLO Object Detection** | New feature | ⬜ | 🔴 HIGH |
| **Auto-Repair Pathway** | run_angela.py auto-install on missing deps | ✅ **DONE** | 🔴 HIGH |
| **Agent Auto-Routing** | Chat pipeline Step 8 wires agents | ✅ **DONE** | 🔴 HIGH |
| **Frontend Multimodal** | Image/audio upload in Desktop/Web | ⬜ | 🔴 HIGH |
| **Whisper ChatService Wiring** | faster-whisper into chat pipeline | ✅ **DONE** | 🟡 MEDIUM |
| **VisualDecoder Training** | Phase 3: texture branch pixel-level training added (T1 DONE) | ✅ | 🟡 MEDIUM |
| **WebSocket Route** | `/multimodal/stream` registered | ✅ **DONE** | 🟡 MEDIUM |
| **P4 Refactoring** | 28 long files / load tests / E2E / tray | ⬜ | 🟡 MEDIUM |
| **Integrate Retained Systems** | real_time_monitor, event_loop_system, etc. | ⬜ | 🟢 LOW |

---

### Documentation Index

See dedicated docs for full diagrams:

| Document | Contents |
|----------|----------|
| [FRAMEWORK_OVERVIEW](docs/FRAMEWORK_OVERVIEW.md) | **Framework positioning, component catalog, extension guide** (bilingual) — how to use Angela AI as a framework |
| [ANGELA_FULL_ARCHITECTURE](docs/architecture/ANGELA_FULL_ARCHITECTURE.md) | **Full system architecture** — perception, cognition, emotion, execution, memory, alignment, pipeline (1183 lines) |
| [PROJECT_CHARTER](docs/00-overview/PROJECT_CHARTER.md) | Project mission, scope, principles |
| [GLOSSARY](docs/00-overview/GLOSSARY.md) | Full project terminology reference |
| [UNIFIED_DOC_INDEX](docs/09-archive/UNIFIED_DOCUMENTATION_INDEX.md) | Comprehensive doc inventory (archived) |
| [WIRING_MAP](docs/03-technical-architecture/analysis/WIRING_MAP_2026-05-21.md) | Server lifecycle, factory chains, subtle wiring, dead code registry |
| [CODE_STATISTICS](docs/03-technical-architecture/analysis/CODE_STATISTICS_2026-05-21.md) | Live vs dead vs semi-finished code by directory |
| [MODULARITY_ANALYSIS](docs/03-technical-architecture/analysis/MODULARITY_ANALYSIS_2026-05-21.md) | God modules, central hub coupling, 20+ singletons |
| [PROBLEM_ANALYSIS](docs/03-technical-architecture/analysis/PROBLEM_ANALYSIS_2026-05-21.md) | 3-perspective audit, security issues, CTO roadmap |
| [FORENSIC_AUDIT](docs/03-technical-architecture/analysis/FORENSIC_AUDIT_2026-05-22.md) | 3-perspective audit: execution paths, TCS migration, security + dead code |
| [MASTER_CONSOLIDATED_PLAN](docs/06-project-management/plans/MASTER_CONSOLIDATED_PLAN.md) | **Active task plan**: 53 items, S/A/B/C tiers, 53/53 complete |
| [CARD_INTEGRATION_PLAN](docs/06-project-management/plans/ANGELA_CARD_INTEGRATION_PLAN.md) | Card pipeline → ChatService wiring: 4 phases, 10 disconnection points |
| [MODULE_MANAGER_DESIGN](docs/03-technical-architecture/design/MODULE_MANAGER_SYSTEM.md) | ✅ **Implemented** — M0-M5 (6 files + 100 tests) + 6 modules (card_pipeline, intent_registry, vision, audio, tactile, drive) |
| [CARD_INTEGRATION_REVIEW](docs/06-project-management/plans/CARD_INTEGRATION_PLAN_REVIEW.md) | Proactive audit: 25 issues found before implementation, 8 HIGH |
| [PHASE6_NEXT_PLAN](docs/06-project-management/plans/PHASE6_NEXT_PLAN.md) | Quality finishing: Plugin deployment, Config handlers, Magic number migration, Stub cleanup |
| [MASTER_FINALIZATION_PLAN](docs/06-project-management/plans/MASTER_FINALIZATION_PLAN.md) | Final push to 0: Remaining handlers, orphaned services, NotImplementedErrors, docs, tests |
| [REMAINING_ISSUES_PLAN](docs/06-project-management/plans/REMAINING_ISSUES_PLAN.md) | Placeholder cleanup, unittest→pytest migration |
| [TEST_RESTRUCTURE_PLAN](docs/06-project-management/plans/TEST_RESTRUCTURE_PLAN.md) | Test layer architecture, conftest layering, CI integration |
| [COMPREHENSIVE_AUDIT_REPORT](docs/06-project-management/plans/COMPREHENSIVE_AUDIT_REPORT.md) | **Audit V1 (05-31)**: Plans, docs, code, tests, config, apps — original completion audit |
| [COMPREHENSIVE_AUDIT_REPORT_V2](docs/06-project-management/plans/COMPREHENSIVE_AUDIT_REPORT_V2.md) | **Audit V2 (06-06)**: H5 post-sprint full scan — 3 true stubs, 20 intentional excepts, 132 long files |
| [COMPREHENSIVE_AUDIT_V3](docs/06-project-management/plans/COMPREHENSIVE_AUDIT_V3.md) | **Audit V3 (06-07)**: ED3N/GARDEN/Model Bus/Router 深度審計，16 HIGH + 16 MEDIUM 問題，P0-P4 修復計畫 |
| [PHASE_REVIEW](docs/06-project-management/plans/PHASE_REVIEW.md) | **Phase Review 1 (06-02)**: First 3-agent parallel audit, 10-dimension assessment |
| [PHASE_REVIEW2](docs/06-project-management/plans/PHASE_REVIEW2.md) | **Phase Review 2 (06-03)**: 17-session tracking audit, ~96% composite |
| [PHASE_REVIEW3](docs/06-project-management/plans/PHASE_REVIEW3.md) | **Phase Review 3 (06-04)**: 3-agent comprehensive audit, 10-dimension assessment |
| [PHASE_REVIEW4](docs/06-project-management/plans/PHASE_REVIEW4.md) | **Phase Review 4 (06-05, v5)**: H5 stub sprint, 36/37 stubs done, 24 empty excepts fixed, ~62% |
| [PHASE_REVIEW5](docs/06-project-management/plans/PHASE_REVIEW5.md) | **Phase Review 5 (06-06, NEW)**: H5 sprint final, 0 HIGH vulns, H7 roadmap |
| [ANGELA_LLM_SNN_ARCHITECTURE_PLAN](docs/06-project-management/plans/ANGELA_LLM_SNN_ARCHITECTURE_PLAN.md) | **ED3N Architecture Plan (06-06, NEW)**: External Dictionary Decoupled Neural Network — LLM + SNN design, training pipeline, 4-phase roadmap |
| [GARDEN_MODEL_PLAN](docs/06-project-management/plans/GARDEN_MODEL_PLAN.md) | **GARDEN Scale Plan (06-06, NEW)**: Giant Associative Relation Decoupled Evolutionary Network — Lightweight 1GB model and 5-tier scaling plan |
| [ED3N_TRAINING_GUIDE](docs/06-project-management/guides/ED3N_TRAINING_GUIDE.md) | **ED3N Training Guide (06-06, NEW)**: How to train, evaluate, and deploy ED3N with real data — terminal commands, data format, troubleshooting |

---

<a name="繁體中文版"></a>

## 繁體中文版

**Angela AI** 是一個數位生命系統，具備生物模擬、LLM 整合與完整聊天管線。

**Quick facts**：612 個 Python 檔案 (backend src)、~96K 行。Electron + Live2D 桌面端、33 shared JS。  
**實際狀態**: Phase 0-7 全部完成。聊天管線完整接線、孤兒系統整合、Phase 9-12 刪除 26 個死代碼子系統、~5,920 行死代碼移除。AgentOrchestrator、PlanningEngine、ReasoningEngines、TrustManager、ContentFilter、SafetyAudit、Web Dashboard、Docker/CI/CD、OpenTelemetry 全部運作。Phase 11-12 已清理 learning/ops/dialogue/evaluation/execution 等 11 個未使用子系統。  
**管線**: WebSocket → 情緒分析 → 危機閘門 → 對齊閘門 → 執行閘門 → **代理路由** → LLM → 因果學習 → 回應。

---

### 當前進度（2026-06-25 代碼驗證）

| 領域 | 狀態 | 關鍵證據 |
|:-----|:----:|:------|
| **聊天管線** | ✅ 完整接線 | 完整管線：情緒 → 危機 → 對齊 → 執行閘門 → 代理路由 → LLM → 因果學習 |
| **CrisisSystem** | ✅ 已整合 | 安全閘門，自動重置超時 (300s) |
| **CausalReasoning** | ✅ 已整合 | 每次回應後觸發學習，FIFO 上限 (500/1000) |
| **Level5ASI** | ✅ 已整合 | 對齊閘門，crisis_level ≥ 2 時觸發 |
| **ModelEnsemble** | ✅ 已整合 | 多模型投票，`context["use_ensemble"] = True` |
| **11 個代理** | ✅ 已註冊 | AgentAdapter 包裝所有代理 |
| **QueryClassifier** | ✅ 已擴展 | 16 種 QueryTypes |
| **ModelBus** | ✅ 已擴展 | Handler 註冊 + Handler-first 路由 |
| **自主認知** | ✅ 已整合 | AutonomousLifeCycle + θ Router + 5 個公式指標 |
| **視覺端點** | ✅ 已實作 | `/vision/analyze` + `/chat/with-image` |
| **圖像生成** | ✅ 已實作 | GVV + ThreeLayerVisual，5 個端點，MSE 0.0042，[文檔](apps/backend/src/ai/multimodal/THREE_LAYER_VISUAL.md) |
| **AgentOrchestrator** | ✅ 已完成 | 意圖分類、代理選擇、任務分解（Phase 2） |
| **PlanningEngine** | ✅ 已完成 | 目標分解、依賴追蹤、進度監控（Phase 2） |
| **ReasoningEngines** | ✅ 已完成 | ChainOfThought、Analogical、Abductive 推理（Phase 2） |
| **TrustManager** | ✅ 已完成 | 信任評分、權限控制、違規追蹤（Phase 3） |
| **ContentFilter** | ✅ 已完成 | 毒性偵測、PII 過濾、安全分類（Phase 3） |
| **SafetyAudit** | ✅ 已完成 | 審計追蹤、合規檢查、警報系統（Phase 3） |
| **Web Dashboard** | ✅ 已完成 | Next.js: ChatPanel、PetPanel、SystemMonitor、EconomyPanel、LearningDashboard（Phase 4） |
| **Docker/CI/CD** | ✅ 已完成 | Dockerfile、docker-compose、Prometheus、Grafana、Nginx、GitHub Actions 部署（Phase 5） |
| **OpenTelemetry** | ✅ 已完成 | 分散式追蹤中間件（Phase 5） |
| **API Versioning** | ✅ 已完成 | 版本路由中間件（Phase 5） |
| **i18n 系統** | ✅ 已完成 | I18nManager、PromptManager、4 個 handler + 4 個 LLM 模組 i18n、45 個測試（Phase 7） |
| **測試** | ✅ 通過 | ~5,085 (全部) / ~4,726 (tests/) — 0 collection errors |
| **智能分數** | ✅ 已評分 | 6.0/10 (有 LLM) / 4.5/10 (純 ED3N+GARDEN) |
| **Master Task Map** | ✅ 已建立 | 23 份計畫全部交叉參照、144 項 claim 驗證、26 個 DO-NOT-REIMPLEMENT |
| **因果鏈完成度** | ✅ 已建立 | `docs/06-project-management/CAUSAL_CHAIN_COMPLETENESS.md` — §0 無 stub 原則、真實深度分數、時脈審計 |
| **EmotionSystem 行為驅動** | ✅ **已完成** | `apply_influence()` 現在修改 PAD 狀態，`get_behavioral_adjustment()` 映射情緒→routing_mode/response_style，已接入管線第5步 |
| **架構文檔** | ✅ 已建立 | `docs/architecture/ANGELA_FULL_ARCHITECTURE.md` |

---

### 快速啟動

```bash
# 克隆專案
git clone https://github.com/catcatAI/Unified-AI-Project.git
cd Unified-AI-Project

# (推薦) 建立並啟用 Python 虛擬環境
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS/Linux:
source .venv/bin/activate

# 安裝後端 Python 依賴
pip install -r apps/backend/requirements.txt

# 使用 pnpm 安裝工作區 JS 依賴
npx pnpm install --no-frozen-lockfile
npx pnpm approve-builds --all

# 方式一：使用統一啟動器（推薦）
python scripts/run_angela.py              # 啟動全部（後端 + 桌面）
python scripts/run_angela.py --api-only   # 只啟動後端
python scripts/run_angela.py --health-check  # 健康檢查

# 方式二：直接啟動後端
python apps/backend/start_server.py

# 方式三：手動啟動桌面端 (另開終端機)
npx pnpm dev:desktop
```

**環境需求**：Python 3.10+、Node.js 16+、Ollama（LLM 後端）

---

### 腳本參考

| 類別 | 腳本 | 說明 |
|------|------|------|
| **啟動** | `scripts/run_angela.py` | 主要啟動器（推薦） |
| **啟動** | `scripts/start_all.bat` | 同時啟動後端 + 桌面端 |
| **啟動** | `scripts/start_backend.bat` | 開發模式啟動後端 |
| **啟動** | `scripts/unified-ai.bat` | 綜合專案啟動器 |
| **健康檢查** | `scripts/check_auth_status.py` | 檢查認證狀態 |
| **健康檢查** | `scripts/check_last_memories.py` | 檢視近期 HAM 記憶 |
| **健康檢查** | `scripts/check_vec_store.py` | 驗證向量儲存完整性 |
| **健康檢查** | `scripts/check_ports.ps1` | 檢查連接埠可用性 |
| **健康檢查** | `scripts/debug_memory.py` | 除錯記憶系統 |
| **健康檢查** | `scripts/utils/health_check.py` | 完整診斷 |
| **健康檢查** | `scripts/utils/check_resources.py` | 系統資源監控 |
| **訓練** | `scripts/train_ed3n.py` | ED3N 訓練 |
| **訓練** | `scripts/train_pipeline.py` | 訓練管線 |
| **訓練** | `scripts/generate_training_data.py` | 生成訓練資料 |
| **雲端硬碟** | `scripts/trigger_sync.py` | 手動觸發 Drive 同步 |
| **雲端硬碟** | `scripts/verify_drive_analyzer.py` | 驗證 Drive Analyzer |
| **開發** | `scripts/verify_ice_loop.py` | 驗證 ICE 循環 |
| **開發** | `scripts/verify_phase_2_loop.py` | 驗證 Phase 2 獎勵循環 |
| **設定** | `scripts/setup_project.bat` / `.sh` | 初始專案設定 |
| **設定** | `scripts/utils/init_config.py` | 配置初始化 |
| **設定** | `scripts/utils/verify_p0_systems.py` | P0 系統驗證 |
| **設定** | `scripts/utils/improve_live2d_loading.py` | Live2D 載入優化 |

> 完整清單：[scripts/ACTIVE_SCRIPTS.md](scripts/ACTIVE_SCRIPTS.md)

---

### 什麼能跑（2026-06-25 驗證）

**聊天管線（完整接線）：**
- **完整管線** — WebSocket → 情緒分析 → 危機閘門 → 生物刺激 → 對齊閘門 → 執行閘門 → 代理路由 → LLM → 因果學習 → 回應 ✅
- **Session 歷史** — 30 條訊息滾動視窗，ED3N 檢索池 ✅
- **情緒分析** — 6 類情緒關鍵字，情緒感知 prompt 注入 ✅
- **危機系統** — 安全閘門自動重置超時 ✅
- **Level5ASI 對齊** — crisis_level ≥ 2 時觸發 ✅
- **因果推理** — 每次回應後學習，FIFO 上限 ✅
- **ModelEnsemble** — 多模型投票 ✅
- **自主認知** — 公式指標注入 prompt ✅
- **視覺端點** — 圖片分析 + 圖片聊天 ✅

**AI 系統：**
- **LLM 供應商** — 8 個供應商：Anthropic, Google, OpenAI, Ollama, llama.cpp, ED3N, GARDEN ✅
- **QueryClassifier** — 16 種 QueryTypes ✅
- **ModelBus** — Handler 註冊 + Handler-first 路由 ✅
- **11 個專業代理** — 透過 AgentAdapter 註冊 ✅
- **ED3N 引擎** — SNN、反射層、跨模態處理 ✅
- **GARDEN 引擎** — VectorDictionary、TensorSNNCore ✅

**國際化（i18n）系統：**
- **I18nManager** — 多語言翻譯管理，支援 JSON locale 檔案載入 ✅
- **PromptManager** — LLM 提示模板管理，語言動態選擇 ✅
- **Handler i18n** — 4 個 handler 已完成硬編字串替換（file_operation, task_manager, system_command, code_execution）✅
- **Prompt Builder i18n** — 60+ 提示字串已替換為 `prompt()` 呼叫 ✅
- **LLM Decision Loop i18n** — 40+ 提示字串已替換 ✅
- **Locale 檔案** — en-US.json, zh-CN.json, prompts.en-US.json, prompts.zh-CN.json ✅
- **Desktop App i18n** — zh-CN bug 修復，大小寫不敏感 locale 匹配 ✅

**Phase 0 — 基礎修復：**
- **Import 修復** — execution_manager.py、UCC await-in-sync、EnvironmentSimulator、重複行 ✅
- **Context 子系統啟用** — dialogue_context、model_context、tool_context、memory_context、integration_with_ham ✅
- **DEPRECATED 標記清理** — 9 個 package 清理 ✅

**Phase 1 — 核心啟動：**
- **Context 接線** — DialogueContext + MemoryContext 注入聊天管線 ✅
- **ED3N 循環** — 最多 3 次迭代，信心閾值 0.7 ✅
- **GARDEN 循環** — 最多 3 次迭代，回應長度改善檢查 ✅
- **UnifiedLearningOrchestrator** — 連接 6 個學習子系統 ✅

**Phase 2 — 智能層：**
- **AgentOrchestrator** — 意圖分類、代理選擇、任務分解 ✅
- **PlanningEngine** — 目標分解、依賴追蹤、進度監控 ✅
- **ReasoningEngines** — ChainOfThought、Analogical、Abductive 推理 ✅

**Phase 3 — 安全信任：**
- **TrustManager** — 信任評分、權限控制、違規追蹤 ✅
- **ContentFilter** — 毒性偵測、PII 過濾、安全分類 ✅
- **SafetyAudit** — 審計追蹤、合規檢查、警報系統 ✅

**Phase 4 — 具現化：**
- **Web Dashboard** — Next.js: ChatPanel、PetPanel、SystemMonitor、EconomyPanel、LearningDashboard、MemoryViewer ✅

**Phase 5 — 基礎設施：**
- **Docker** — 多階段 Dockerfile、docker-compose 含 Redis、PostgreSQL、Prometheus、Grafana、Nginx ✅
- **CI/CD** — GitHub Actions staging/production 部署 ✅
- **監控** — Prometheus 指標、Grafana 儀表板、警報規則 ✅
- **OpenTelemetry** — 分散式追蹤中間件 ✅
- **API Versioning** — 版本路由中間件 ✅

**Phase 6 — 文件與優化：**
- **基準測試** — ED3N、GARDEN、Classifier 基線 ✅
- **效能分析** — 統一分析器（imports/memory 模式）✅
- **OpenAPI** — 靜態規格匯出腳本 ✅
- **文件** — 部署指南、使用者指南 ✅

**核心基礎設施：**
- **配置系統** — `config_loader.py:get_config()` ✅
- **State Matrix** — 6D 狀態矩陣 (αβγδεθ)，1,244 行 ✅
- **HSP 連接器** — 51 KB，完整協議 ✅
- **生物系統** — 8 個模組 ✅
- **ChromaDB 記憶** — HAM 記憶 + 向量儲存 ✅
- **桌面端** — Electron + Live2D，Epsilon_free 模型 ✅
- **像素端** — PyQt6 渲染引擎 ✅
- **CLI** — 統一命令列工具 ✅

### 什麼無法運作

- **YOLO 物件檢測** — 未開始 ❌
- **Whisper 接線** — faster-whisper 已安裝並接入聊天管線 (離線高品質 STT) ✅
- **代理自動路由** — 已接入聊天管線第 8 步（創意/知識/意見/視覺/聽覺）✅
- **VisualDecoder 訓練** — T1 DONE: 投射權重已訓練 (42× CIFAR-10 損失降低)，紋理權重已可訓練 ✅
- **P4 重構** — 25/31 長函式已重構（3 純資料 + 3 演算法剩餘），負載/E2E/tray 尚未開始 ⏳
- **自動修復路徑** — `run_angela.py` 現在有自動安裝功能（--auto-repair 或互動提示）✅

### 已刪除 (Phase 9-12 清理) — 不要重新實作
- **手機端** — scaffold 已刪除（Phase 11）🗑️
- **TactileService** — stub 已刪除（Phase 11）🗑️
- **ImageGenerationAgent** — stub 已刪除（Phase 9）🗑️
- **ComfyUIClient** — stub 已刪除（Phase 10）🗑️
- **`services/wiring.py`** — 死代碼已刪除（Phase 11）🗑️
- **11 個死子系統** — 已刪除（Phase 11b）🗑️
- **5 個死模組** — 已刪除（Phase 12）🗑️

### 孤兒系統狀態

| 類別 | 數量 | 處理方式 |
|------|------|---------|
| **已接入管線** | 6 | CrisisSystem, CausalReasoning, Level5ASI, ModelEnsemble, 11 Agents, AgentManager |
| **已刪除（stub/重複）** | 16 | services/ai_editor_config.py 等 |
| **保留但未接入** | 18 | real_time_monitor, event_loop_system, execution_manager 等 |

---

### 修正後路線圖

| 階段 | 目標 | 狀態 | 優先級 |
|:------|:-----|:----:|:--------:|
| **聊天管線** | 完整接線：情緒 → 危機 → 對齊 → 執行閘門 → 代理路由 → LLM → 因果學習 | ✅ **已完成** | 🔴 CRITICAL |
| **孤兒系統** | 接入 6 系統、刪除 16 個 stub、保留 18 個 | ✅ **已完成** | 🔴 CRITICAL |
| **Bug 修復** | 15 個 bug 修復 | ✅ **已完成** | 🔴 CRITICAL |
| **架構文檔** | `ANGELA_FULL_ARCHITECTURE.md` — 1183 行 | ✅ **已完成** | 🟡 MEDIUM |
| **Phase 0-6** | Foundation, Core, Intelligence, Safety, Embodiment, Infrastructure, Polish | ✅ **已完成** | 🔴 CRITICAL |
| **i18n 國際化** | I18nManager, PromptManager, Handler/Prompt 替換, Locale 檔案 | ✅ **已完成** | 🟡 MEDIUM |
| **YOLO 物件檢測** | 新功能 | ⬜ | 🔴 HIGH |
| **自動修復路徑** | run_angela.py 缺失依賴時自動安裝 | ✅ **已完成** | 🔴 HIGH |
| **代理自動路由** | 聊天管線第 8 步接入 agent | ✅ **已完成** | 🔴 HIGH |
| **前端多模態** | Desktop/Web 圖片/音訊上傳 | ⬜ | 🔴 HIGH |
| **Whisper 接線** | faster-whisper 接入聊天管線 | ✅ **已完成** | 🟡 MEDIUM |
| **VisualDecoder 訓練** | CLP 擴展訓練 decoder | ⬜ | 🟡 MEDIUM |
| **WebSocket 路由** | `/multimodal/stream` 已註冊 | ✅ **已完成** | 🟡 MEDIUM |
| **P4 重構** | 28 長檔案 / 負載測試 / E2E / tray | ⬜ | 🟡 MEDIUM |
| **整合保留系統** | real_time_monitor, event_loop_system 等 | ⬜ | 🟢 LOW |

---

### 架構文件

| 文件 | 內容 |
|------|------|
| [框架總覽](docs/FRAMEWORK_OVERVIEW.md) | **框架定位、元件目錄、擴展指南**（中英雙語） |
| [專案憲章](docs/00-overview/PROJECT_CHARTER.md) | 專案使命、範圍、原則 |
| [詞彙表](docs/00-overview/GLOSSARY.md) | 完整名詞解釋 |
| [統一文件索引](docs/09-archive/UNIFIED_DOCUMENTATION_INDEX.md) | 所有文件導覽（已封存） |
| [完整架構圖](docs/architecture/ANGELA_FULL_ARCHITECTURE.md) | **Angela 感知・認知・執行完整架構** — 如何視、聽、觸、說、畫、移、思考、感受、自主 |
| [技術架構概覽](docs/03-technical-architecture/README.md) | HSP、HAM、NGR、8D Matrix、多模態代理、通訊層、安全性 |
| [ARCHITECTURE_MAP](docs/03-technical-architecture/analysis/ARCHITECTURE_MAP_2026-05-20.md) | 伺服器拓撲、port 衝突、路由對照 |
| [全量架構分析](docs/09-archive/FULL_ARCHITECTURE_ANALYSIS.md) | 完整架構圖譜、版本溯源、六層一致性評分 |
| [AGENTS.md](AGENTS.md) | 代理開發指南 — 構建/測試/代碼規範 |
| [CHANGELOG.md](CHANGELOG.md) | 版本歷史與變更記錄 |

### 分析與計畫文件

| 文件 | 內容 |
|------|------|
| [WIRING_MAP](docs/03-technical-architecture/analysis/WIRING_MAP_2026-05-21.md) | 接線圖、工廠鏈、死代碼 |
| [CODE_STATISTICS](docs/03-technical-architecture/analysis/CODE_STATISTICS_2026-05-21.md) | 代碼統計、活/死/半成品 |
| [MODULARITY_ANALYSIS](docs/03-technical-architecture/analysis/MODULARITY_ANALYSIS_2026-05-21.md) | God module、耦合、singleton |
| [PROBLEM_ANALYSIS](docs/03-technical-architecture/analysis/PROBLEM_ANALYSIS_2026-05-21.md) | 三重視角審計、安全問題、優先級 |
| [FORENSIC_AUDIT](docs/03-technical-architecture/analysis/FORENSIC_AUDIT_2026-05-22.md) | 三輪獨立審計：執行路徑、TCS 遷移、安全性 + 死代碼 |
| [MASTER_CONSOLIDATED_PLAN](docs/06-project-management/plans/MASTER_CONSOLIDATED_PLAN.md) | **進行中任務總計畫**：53 項、S/A/B/C 分級、53/53 完成 |
| [CARD_INTEGRATION_PLAN](docs/06-project-management/plans/ANGELA_CARD_INTEGRATION_PLAN.md) | 卡片管道 → ChatService 接線 v2：ModuleManager 驅動 |
| [MODULE_MANAGER_DESIGN](docs/03-technical-architecture/design/MODULE_MANAGER_SYSTEM.md) | ✅ **已實作** — M0-M5 (6 files + 100 tests) + 6 模組 |
| [CARD_INTEGRATION_REVIEW](docs/06-project-management/plans/CARD_INTEGRATION_PLAN_REVIEW.md) | 事前審計：執行前發現 25 問題（8 HIGH） |
| [PHASE6_NEXT_PLAN](docs/06-project-management/plans/PHASE6_NEXT_PLAN.md) | Quality finishing: Plugin 部署, Config handler, Magic number 遷移 |
| [MASTER_FINALIZATION_PLAN](docs/06-project-management/plans/MASTER_FINALIZATION_PLAN.md) | Final push to 0: 殘留 handler, 孤立服務, NotImplementedError |
| [REMAINING_ISSUES_PLAN](docs/06-project-management/plans/REMAINING_ISSUES_PLAN.md) | placeholder 清除、unittest→pytest 遷移 |
| [TEST_RESTRUCTURE_PLAN](docs/06-project-management/plans/TEST_RESTRUCTURE_PLAN.md) | 測試層級架構、conftest 分層、CI 整合 |
| [COMPREHENSIVE_AUDIT_REPORT](docs/06-project-management/plans/COMPREHENSIVE_AUDIT_REPORT.md) | **全面審計報告 V1**: 計畫、文檔、代碼、測試、配置、應用 |
| [COMPREHENSIVE_AUDIT_REPORT_V2](docs/06-project-management/plans/COMPREHENSIVE_AUDIT_REPORT_V2.md) | **全面審計報告 V2**: H5 後冲刺全面扫描 — 3 個真 stub、20 個有意義 except |
| [COMPREHENSIVE_AUDIT_V3](docs/06-project-management/plans/COMPREHENSIVE_AUDIT_V3.md) | **全面審計報告 V3**: ED3N/GARDEN/Model Bus/Router 深度審計 |
| [PHASE_REVIEW](docs/06-project-management/plans/PHASE_REVIEW.md) | **階段審查 1 (06-02)**: 首次3代理並行審計，10維度評分 |
| [PHASE_REVIEW2](docs/06-project-management/plans/PHASE_REVIEW2.md) | **階段審查 2 (06-03)**: 17會話後追蹤審計，~96% 綜合分數 |
| [PHASE_REVIEW3](docs/06-project-management/plans/PHASE_REVIEW3.md) | **階段審查 3 (06-04)**: 3代理綜合審計，10維度判定 |
| [PHASE_REVIEW4](docs/06-project-management/plans/PHASE_REVIEW4.md) | **階段審查 4 (06-05)**: H5 stub 冲刺，36/37 stubs 完成 |
| [PHASE_REVIEW5](docs/06-project-management/plans/PHASE_REVIEW5.md) | **階段審查 5 (06-06)**: H5 sprint final，2837 測試，0 HIGH 漏洞 |
| [ANGELA_LLM_SNN_ARCHITECTURE_PLAN](docs/06-project-management/plans/ANGELA_LLM_SNN_ARCHITECTURE_PLAN.md) | **ED3N 架構計畫**: 外部字典解耦神經網路 — LLM + SNN 設計、訓練管線、4 階段路線圖 |
| [GARDEN_MODEL_PLAN](docs/06-project-management/plans/GARDEN_MODEL_PLAN.md) | **GARDEN 擴展計畫**: 1GB 輕量級本地模型與五級擴展架構 |
| [ED3N_TRAINING_GUIDE](docs/06-project-management/guides/ED3N_TRAINING_GUIDE.md) | **ED3N 訓練指南**: 訓練、評估、部署 ED3N |

---

**Version**: 7.5.0-dev | **Code Stats**: 612 Python files, ~96K lines | **Tests**: ~5,085 (full) / ~4,726 (tests/) — 0 errors | **Intelligence**: 6.0/10 (upper) 4.5/10 (lower) | **Architecture**: ~85-90% | | [Architecture](docs/architecture/ANGELA_FULL_ARCHITECTURE.md) | [Task Map](docs/06-project-management/MASTER_TASK_MAP.md) | [Improvement Roadmap](docs/06-project-management/IMPROVEMENT_ROADMAP.md) | [Changelog](CHANGELOG.md)
