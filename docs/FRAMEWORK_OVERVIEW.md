<!--
  =============================================================================
  VERSION: 7.5.0-dev
  STATUS: active
  LANGUAGE: en/zh-tw
  LAST_MODIFIED: 2026-06-25
  =============================================================================
-->

# Angela AI Framework Overview

> **Framework positioning**: A modular, extensible framework for building digital life systems with hybrid AI (LLM + SNN + biological simulation).
> **Codebase**: 612 Python files (~96K lines) in `apps/backend/src/` + 50 JS files across 3 apps + 4,785 tests.
> **Intelligence**: Upper bound 6.0/10 (with LLM API), **lower bound <0.5/10** (native engines alone — ED3N/GARDEN produce random/low-quality output without training). See [INTELLIGENCE_ASSESSMENT.md](06-project-management/INTELLIGENCE_ASSESSMENT.md) for detailed scoring.
> **Architecture completeness**: ~85-90% (framework structure exists, but ML model weights are 5% trained).
> **Version**: 7.5.0-dev | **License**: MIT

[English](#english) | [繁體中文](#繁體中文-版本)

---

## English

### 1. What Is Angela AI?

Angela AI is not a single application — it is a **framework** for building AI-powered digital life systems. It provides:

- **A pipelined chat architecture** — WebSocket → emotion → crisis → alignment → execution gate → **agent routing** → LLM → causal learning → response — every stage is a replaceable component
- **7 LLM backends** — Anthropic, Google, OpenAI, Ollama, llama.cpp, ED3N (SNN), GARDEN (lightweight) — pluggable via strategy pattern
- **2 local inference engines** — ED3N (460K dictionary, SNN reflex) and GARDEN (VectorDictionary + TensorSNN) — zero-cost fallback without external APIs. ⚠️ **Caution**: Both engines have random/uninitialized weights. **Math is NOT computed by these engines** — the `math` intent is short-circuited to **MathVerifier** (single source of truth); ED3N/GARDEN route it through their dictionary layer (`route_math`) and MathRippleEngine is now only a ripple/state-propagation layer. Math accuracy measured at **100% (5/5)** via `scripts/benchmark_ed3n_garden.py` after PEMDAS fix. All other domains (knowledge, creative, reasoning) remain at 0% — native engines are concept-mapping only. VisualDecoder/AudioWaveformDecoder/SequenceGenerator output = noise. Architecture exists; training is ~5% complete.
- **A 6-dimensional state matrix** (αβγδεθ) — shared context for cognitive, emotional, and environmental state
- **Biological simulation** — 8 modules modeling energy, metabolism, endocrine, neuroplasticity, etc.
- **11 specialized agents** — Creative, Code, Data, Search, Vision, Audio, etc. — registered via `AgentAdapter`
- **A module manager** — `ModuleManager` (M0-M5, 6 files, 100 tests) for lifecycle management
- **Multi-modal pipeline** — Vision (CLIP 512-dim), Audio (edge-tts), Image generation (GVV + ThreeLayerVisual)
- **Internationalization** — `I18nManager` + `PromptManager` with en-US/zh-CN locale files
- **Full deployment stack** — Docker, docker-compose (Redis, PostgreSQL, Prometheus, Grafana, Nginx), GitHub Actions CI/CD

#### Framework vs Application

| Aspect | As Framework | As Application |
|--------|-------------|----------------|
| **Primary user** | Developers building AI systems | End users chatting with Angela |
| **Core value** | Pluggable architecture, pipeline stages, extension points | Chat, image generation, Live2D interaction |
| **Documentation** | This doc + SERVICE_CATALOG + AGENTS.md | README.md + QUICK_START.md |
| **Extension** | Add providers, agents, pipeline stages | Configure LLM, enable/disable features |

### 2. Core Architecture

#### 2.1 Six-Layer Model

```
LAYER 6 — EXECUTION / PRESENTATION
  Desktop (Electron+Live2D) | Web Dashboard (Next.js) | CLI | Pixel Angela (PyQt6)

LAYER 5 — API / TRANSPORT
  FastAPI (uvicorn) — Routes: /api/v1/* — WebSocket: /ws/*
  Middleware: CORS → SignedCommunication — Session: TTLSessionManager (1h TTL, 1000 max)

LAYER 4 — APPLICATION SERVICES
  ChatService | LLMService | VisionService | AudioService | MultimodalService
  EconomyManager | MathVerifier | BrainBridge

LAYER 3 — CORE INFRASTRUCTURE
  HAM Memory (ChromaDB) | StateMatrix 6D (αβγδεθ) | ConfigLoader (YAML 3-tier)
  ModuleManager (M0-M5) | Security A/B/C Keys | Biological Integrator

LAYER 2 — AI ENGINE
  ED3N (460K dict + SNN) | GARDEN (VectorDictionary + TensorSNN)
  GVV Pipeline | ThreeLayerVisual | Agents (×11) | Alignment | Reasoning
  QueryClassifier (16 types) | ModelBus | RAG Manager

LAYER 1 — THEORETICAL FOUNDATION
  HSM Formula | CDM Dividend | Life Intensity | Active Cognition
  Non-Paradox Existence | Precision Management | Maturity L0-L11

CROSS-CUTTING
  ModuleManager | i18n System | OpenTelemetry | Prometheus Metrics | API Versioning
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for the full 6-layer diagram and [ANGELA_FULL_ARCHITECTURE.md](architecture/ANGELA_FULL_ARCHITECTURE.md) (1330 lines) for detailed component descriptions.

#### 2.2 Chat Pipeline

```
User Input → WebSocket → POST /api/v1/chat/unified
  → EmotionAnalyzer (6-category keywords)
  → CrisisGate (auto-reset 300s, configurable)
  → BiologicalStimulus (energy/metabolism)
  → AlignmentGate (Level5ASI at crisis ≥ 2)
  → ExecutionGate (actionable intents: file/search/code/execute/task)
  → AgentRouting (creative/knowledge/opinion/vision/audio agents)
  → LLM call (7 backends, strategy pattern)
  → CausalReasoning (fire-and-forget, FIFO 500/1000)
  → ResponseComposer (merge LLM + formula + state)
  → WebSocket push → Desktop Renderer
```

All 8 stages wired and tested. Each stage can be replaced or extended independently.

#### 2.3 Key Design Decisions

| Decision | Rationale | Implementation |
|----------|-----------|----------------|
| **ED3N decoupling** | External dictionaries avoid expensive retraining | 460K entries across 3 languages; SNN reflex layers for fast path |
| **Three-layer speed** | LLM → ED3N → GARDEN fallback chain | `LLMRouter` selects provider by confidence + cost |
| **6D state matrix** | Shared context without tight coupling | `StateMatrix4D` (1244 lines), observer pattern → WebSocket push |
| **AgentAdapter pattern** | Uniform `execute()` interface for all agents | 11 agents wrapped, registered in `agent_manager.py` |
| **ModuleManager** | Dynamic lifecycle management for services | M0-M5 (6 files, 100 tests), module scanning + dependency wiring |
| **i18n as infrastructure** | Language-awareness built into prompt system | `PromptManager` + `I18nManager` (45 tests), not ad-hoc |

### 3. Component Catalog

#### 3.1 AI Engines

| Component | Path | Lines | Status | Description |
|-----------|------|-------|--------|-------------|
| ED3N Engine | `ai/ed3n/` | ~3K | 🟢 Active | Dictionary-decoupled SNN, reflex layers, cross-modal |
| GARDEN Engine | `ai/garden/` | ~2K | 🟢 Active | Lightweight VectorDictionary + TensorSNNCore |
| GVV Pipeline | `ai/multimodal/primitives/` | 14 files | 🟢 Active | Geometric vocabulary image generation, MSE 0.0042 |
| ThreeLayerVisual | `ai/multimodal/` | — | 🟡 Partial | PCA encoder (87%), decoder weights random |
| QueryClassifier | `ai/core/query_classifier.py` | — | 🟢 Active | 16 QueryTypes, confidence-based routing |
| ModelBus | `ai/core/model_bus.py` | — | 🟢 Active | Handler registration + handler-first routing |
| LLMRouter | `services/llm/router.py` | — | 🟢 Active | 7 providers, strategy pattern, provider selection |

#### 3.2 LLM Providers

| Provider | Path | Strategy | Status |
|----------|------|----------|--------|
| Anthropic | `services/llm/providers/anthropic.py` | API call | 🟢 Active |
| Google (Gemini) | `services/llm/providers/google.py` | API call | 🟢 Active |
| OpenAI | `services/llm/providers/openai.py` | API call | 🟢 Active |
| Ollama | `services/llm/providers/ollama.py` | Local API | 🟢 Active |
| llama.cpp | `services/llm/providers/llamacpp.py` | Local binary | 🟢 Active |
| ED3N | `services/llm/providers/ed3n.py` | SNN inference | 🟢 Active |
| GARDEN | `services/llm/providers/garden.py` | Vector + SNN | 🟢 Active |

#### 3.3 Memory Systems

| Component | Path | Lines | Status | Description |
|-----------|------|-------|--------|-------------|
| HAM Memory | `ai/memory/ham_memory/` | ~2K | 🟢 Active | ChromaDB + template matching, 157 templates |
| VectorStore | `ai/memory/vector_store/` | 25 files | 🟢 Active | Dual-backend (chromadb / numpy+JSON) |
| ED3N Dictionaries | `ai/ed3n/` | 460K entries | 🟢 Active | CC-CEDICT (zh↔en), JMdict (ja↔en), WordNet (en) |
| SessionManager | `core/sessions/` | — | 🟢 Active | 56 tests, 1h TTL, LRU 1000 |
| CausalReasoning | `ai/reasoning/` | — | 🟢 Active | Fire-and-forget, FIFO 500/1000 |

#### 3.4 Biological Simulation

| Module | Description | Status |
|--------|-------------|--------|
| EnergySystem | Energy consumption, recharge | 🟢 Active |
| MetabolismSystem | Metabolic rate, waste processing | 🟢 Active |
| EndocrineSystem | Hormone regulation, mood influence | 🟢 Active |
| NeuroplasticitySystem | Memory reinforcement, learning | 🟢 Active |
| CircadianRhythm | Day/night cycle, sleep needs | 🟢 Active |
| HomeostaticSystem | Balance regulation, stress response | 🟢 Active |
| ImmuneSystem | Virtual immune response | 🟢 Active |
| BiologicalIntegrator | Coordinates all subsystems | 🟢 Active |

#### 3.5 Agents (11 Registered)

| Agent | Purpose | Status |
|-------|---------|--------|
| CreativeAgent | Creative writing, story generation | 🟢 Registered |
| CodeAgent | Code generation and review | 🟢 Registered |
| DataAgent | Data analysis and visualization | 🟢 Registered |
| SearchAgent | Web and knowledge search | 🟢 Registered |
| VisionAgent | Image analysis | 🟢 Registered |
| AudioAgent | Audio processing | 🟢 Registered |
| TaskAgent | Task management | 🟢 Registered |
| LearningAgent | Continuous learning | 🟢 Registered |
| MathAgent | Mathematical reasoning | 🟢 Registered |
| MemoryAgent | Memory operations | 🟢 Registered |
| PersonalityAgent | Personality modeling | 🟢 Registered |

**Note**: All agents are registered via `AgentAdapter` but **not auto-routed** by the chat pipeline — agent invocation requires explicit `ModelBus` routing.

#### 3.6 Frontend Applications

| App | Stack | Files | Status |
|-----|-------|-------|--------|
| Desktop App | Electron + Live2D Cubism 5 | 7 unique + 33 shared JS | 🟢 Active |
| Web Dashboard | Next.js | — | 🟢 Active |
| Web Live2D Viewer | Web + Live2D | 10 unique JS | 🟢 Active |
| Pixel Angela | PyQt6 + numpy | — | 🟢 Active |

#### 3.7 Infrastructure

| Component | Tech | Status |
|-----------|------|--------|
| ModuleManager | Python, 6 files, 100 tests | 🟢 Active |
| i18n System | I18nManager + PromptManager, 45 tests | 🟢 Active |
| OpenTelemetry | Tracing middleware | 🟢 Active |
| Prometheus Metrics | /metrics endpoint | 🟢 Active |
| Docker | Multi-stage Dockerfile + docker-compose | 🟢 Active |
| CI/CD | GitHub Actions (staging + production) | 🟢 Active |
| API Versioning | `/api/v1/*` middleware | 🟢 Active |

### 4. How to Use the Framework

#### 4.1 Development Workflow

```bash
# Setup — pick a tier: "" (quick), [standard] (full features), [dev] (contributor)
python -m venv .venv
pip install -e "apps/backend[dev]"
npx pnpm install --no-frozen-lockfile

# Run
python scripts/run_angela.py           # Full stack
python scripts/run_angela.py --api-only # Backend only

# Test
pytest tests/                           # 4,261 tests
pytest tests/path/to/test_file.py -v    # Single file

# Lint & Type-check
flake8 apps/backend/src tests/
mypy apps/backend/src
```

#### 4.2 Configuration

Configuration uses a 3-tier YAML system:

```yaml
# configs/angela_config.yaml
server:
  host: 0.0.0.0
  port: 8000
llm:
  default_provider: ollama
  providers:
    ollama:
      model: llama3
      url: http://localhost:11434
```

See `apps/backend/configs/` for example configs and `core/config_loader.py` for the loader implementation.

#### 4.3 Adding an LLM Provider

1. Create a class implementing the `LLMBackend` protocol in `services/llm/providers/`
2. Register it in `services/llm/providers/__init__.py`
3. Add configuration in `angela_config.yaml`
4. Test: write a test calling `LLMRouter` with your new provider

The protocol requires `generate(prompt: str, **kwargs) -> str`. See any existing provider (e.g., `ollama.py`) as a template.

#### 4.4 Adding a New Agent

1. Create a class extending `BaseAgent` (or implementing `AgentAdapter`'s `execute()` interface)
2. Register it in `core/agents/agent_manager.py`
3. Add a `QueryType` in `QueryClassifier` (optional, for auto-routing)
4. Write tests — every agent should have at least one test

#### 4.5 Extending the Pipeline

Each stage in the chat pipeline (`chat_routes.py`) is a function or callable class. To add a new stage:

1. Create your stage function (signature: `async def stage(context: dict) -> dict`)
2. Insert it in the pipeline chain in `chat_routes.py`
3. Add configuration keys if needed
4. Write integration test

### 5. Intelligence Assessment

| Capability | Upper (with LLM) | Lower (native only) | Implementation & Caveat |
|:-----------|:-----:|:-----:|:---------------|
| Text understanding | 7/10 | 0.5/10 | 460K dictionary exists but ED3N concept mapping is 1990s NLP. Real understanding comes from LLM API. |
| Image understanding | 7/10 | 0.5/10 | numpy color histogram + Sobel edges (1990s CV). CLIP wrapper needs torch. |
| Speech understanding | 5/10 | 0/10 | Whisper feature encoder exists (numpy fallback). Native audio encoder = basic MFCC stats. |
| Text generation | 7/10 | 0.5/10 | 7 LLM backends provide real generation. ED3N/GARDEN decoders = dictionary key lookup + random weights. |
| Image generation | 6/10 | 0/10 | GVV pipeline architecture exists. **All weights random → output = gray canvas or noise.** ThreeLayerVisual MSE=0.009 (blurry 32×32 = 1995 quality). |
| Speech generation | 4/10 | 0/10 | edge-tts calls external API. Native AudioWaveformDecoder = wavetable noise (random weights). |
| Memory | 7/10 | 7/10 | VectorStore + HAM = genuinely useful. Works regardless of LLM. |
| Reasoning | 4/10 | 0.5/10 | CausalReasoningEngine = Pearson correlation only. PlanningEngine = template matching. MathRippleEngine = ripple/state-propagation layer (numeric result delegated to MathVerifier, the single math source of truth). |
| Autonomy | 3/10 | 0.5/10 | AutonomousLifeCycle wired but unstable without LLM guidance. |
| Meta-cognition | 5/10 | 4/10 | MetaController confidence tracking works. NeuroAutoSelector heuristic-based. |
| **Composite** | **6.0/10** | **<0.5/10** | Framework architecture ~85-90% complete. **ML training is ~5% complete.** Native engine output = low-quality/uninitialized. All real intelligence comes from LLM API wrappers. |

**Key insight**: This is an **architectural framework** with production-quality structure and academic-prototype ML content. The 190+ AI classes form a complete skeleton; the muscle (trained weights) is missing. The LLM API wrappers provide the only production-quality intelligence today.

### 5.5 Learning Capabilities Assessment

Angela AI has **4 levels of learning**, each building on the previous. This is unusually deep compared to standard AI agent frameworks (see §6.1 for comparison).

#### 5.5.1 Scoring Methodology

The percentages are **qualitative assessments** based on:
- **Mechanism coverage**: How many of the ideal mechanisms for each level exist
- **Testing verification**: Whether mechanisms actually work (verified via code inspection + passing tests)
- **Feature completeness**: How close each mechanism is to its ideal implementation
- **Integration**: How well mechanisms compose with each other

#### 5.5.2 Level 1 — Learn New Vocabulary and Use It → **80%**

| Mechanism | Status | Description |
|-----------|:------:|-------------|
| `ContinuousLearningPipeline._detect_and_grow()` | ✅ | Auto-discovers new tokens from user text every N interactions (configurable via `growth_interval`) |
| `DictionaryLayer.learn_from_conversation()` | ✅ | Processes utterances, detects candidates, grows dictionary entries with confidence scoring |
| `GARDENEngine.learn_from_interaction()` | ✅ | Grows vector dictionary with novel tokens, handles CJK and English |
| Encoding/decoding learned terms | ✅ | New terms appear in future responses via dictionary encode→decode pipeline |
| Multi-language support | ✅ | CJK character detection + English word boundary; separate confidence heuristics per language |
| **E2E verified** | ✅ | Tested: "量子計算機" → dictionary grows from 47→48 entries, correctly encoded as `['l1','l2']`, decoded back to original text |

**Missing (20%)**: Cross-modal concept learning (text↔image↔audio) not wired; no automatic low-confidence entry pruning during learning growth.

#### 5.5.3 Level 2 — Learn Vocabulary and Take Action → **70%**

| Mechanism | Status | Description |
|-----------|:------:|-------------|
| `ED3NTrainer` / `JointTrainer` | ✅ | Adjusts dictionary entry confidences + network connection weights between input/output keys |
| `DictionaryClassifier.learn()` | ✅ | Learns `text→query_type→action_type` mappings |
| `GARDENEngine` Hebbian SNN update | ✅ | `hebbian_update()` strengthens SNN weight connections between co-occurring concepts |
| `CausalReasoningEngine.learn()` | ✅ | Learns causal relationships from observations (Pearson correlation basis) |
| Reflex pattern learning | ✅ | `learn_reflex()` adds pattern→response pairs; `ED3NLearningIntegration` handles external sync |
| `GARDENEngine.learn_batch()` | ✅ | Batch variant: collects all tokens first, rebuilds index once, runs all Hebbian updates |

**Missing (30%)**: `ED3NLearningIntegration` → `LearningManager`/`ReplayBuffer`/`MemoryLearning` connections broken (Phase 9-12 cleanup removed the `ai.learning` package). These components gracefully return `None` instead of crashing.

#### 5.5.4 Level 3 — Strongest Learning Without Code Changes → **70% (target ≥60%)**

| Mechanism | Status | Description |
|-----------|:------:|-------------|
| All Level 1+2 mechanisms | ✅ | Fully configurable via `magic_numbers.py` — buffer sizes, intervals, learning rates, thresholds |
| `ContinuousLearningPipeline` auto-train | ✅ | Auto-triggers training every `train_interval` (default 50) when buffer ≥ `min_examples_for_train` (default 20) |
| `TrainingCoordinator` | ✅ | Tracks per-domain training: ED3N (reflex,math,logic), GARDEN (knowledge,command,general), Cloud LLM (creative,opinion). Deduplication via SHA-256 hash. |
| State persistence (`save()`/`load()`) | ✅ | Full engine state persists across restarts (dictionary + SNN weights + CL state) |
| Config-driven tuning | ✅ | All parameters via `magic_numbers.py` — no source code changes needed to tune learning behavior |
| Multi-model coordination | ✅ | `ModelBus.get_training_assignment()` + `DOMAIN_OWNERSHIP` table routes training to the correct engine |

**Missing (30%)**: No meta-learning (learning how to learn); no curriculum learning; no self-supervised exploration loop; no automatic evaluation of learned concepts.

#### 5.5.5 Level 4 — Requires Code Changes

| Feature | What Would Be Needed |
|---------|---------------------|
| New network architectures | Code changes to `CoreNetwork`, `SNNCore`, or `TensorSNNCore` |
| Reinforcement learning | New training loop, reward function, policy network |
| Few-shot / meta-learning | MAML-style outer loop, task distribution sampling |
| Integration with external ML | HuggingFace, PyTorch Lightning, or ONNX runtime connectors |
| Self-supervised learning | Pretext task generator, contrastive loss implementation |

#### 5.5.6 Unique Differentiator

Unlike other AI agent frameworks (see §6.1), Angela has **actual weight-based learning**, not just context management:

| Aspect | Angela AI | Other Frameworks (AutoGPT, MemGPT, LangChain) |
|--------|-----------|-----------------------------------------------|
| **Learning type** | 🧠 Synaptic weight updates + dictionary growth | 📋 Context management + RAG retrieval |
| **Vocabulary growth** | ✅ New entries added to dictionary on-the-fly | ❌ No new vocabulary; relies on LLM's static knowledge |
| **Weight changes** | ✅ Hebbian + gradient-like adjustments persist | ❌ Model weights never change (static LLM) |
| **Knowledge internalization** | ✅ New concepts become part of the network's internal representations | ❌ Knowledge is external (retrieved from DB, injected into context window) |
| **Persistence** | ✅ Learned knowledge survives restarts via save/load | ✅ Facts survive (in DB), but no "learning" happens |
| **Offline operation** | ✅ All learning mechanisms run locally, no API needed | ❌ RAG + LLM require external services |

**Bottom line**: Most AI "agents" today are expert context managers — they don't learn, they retrieve. Angela AI has genuine (if basic) on-the-fly learning through dictionary growth and weight updates. This puts it in a different category: **continual learning agent** rather than RAG-based chatbot.

### 6. Competitive Analysis — Strengths & Weaknesses

#### 6.1 Differentiating Strengths

| Strength | What It Means | vs LangChain | vs AutoGPT | vs Character.ai |
|:---------|:--------------|:-------------|:-----------|:----------------|
| **ED3N decoupled dictionaries** | Add knowledge without retraining (460K entries, 3 languages) | RAG requires vector DB + chunking | No equivalent | No equivalent |
| **Three-layer fallback (architecture)** | LLM → ED3N SNN → GARDEN numpy. ⚠️ ED3N/GARDEN output is low-quality without training — fallback degrades to garbage, not graceful degradation. | Single LLM path, no fallback | Single LLM path | Cloud-only |
| **Live2D desktop body** | Real-time emotion expression on a desktop avatar | No body | No body | Web chat only, no desktop app |
| **Biological simulation** | 8 modules: energy, metabolism, endocrine, circadian | No bio sim | No bio sim | Limited personality, no body |
| **Pure CPU inference (GARDEN)** | numpy backend, no GPU required | Most models require GPU | OpenAI API only | Cloud-only |
| **Language-aware i18n** | PromptManager + I18nManager built in, 45 tests | Ad-hoc localization | English only | English + JP limited |
| **6D state matrix** | Shared αβγδεθ context across all components | No shared state | No shared state | Proprietary |

#### 6.2 Weaknesses (Honest)

| Weakness | Impact | Root Cause |
|:---------|:-------|:-----------|
| **ML content < framework** | User experience far below architecture promise | Decoder random weights, unwired Whisper, untrained SNN |
| **Complexity/function ratio** | 612 files but less functionality than expected | Tries to be too many things at once |
| **Unclear user positioning** | Fails to attract any single audience clearly | Is it a developer framework? User product? Research platform? |
| **No standard benchmarks** | MMLU, HumanEval, etc. all missing | Focus on infra tests (4,261) over quality tests |
| **Agents registered but not called** | 11 agents exist but pipeline never invokes them | Architectural decision pending |
| **Auto-routing missing** | QueryClassifier + ModelBus exist but are bypassed by direct LLM calls | Pipeline shortcuts reduce effectiveness |

#### 6.3 What Actually Attracts Users

| Selling Point | Target Audience | Why It's Unique |
|:--------------|:----------------|:----------------|
| **Offline-first AI** | Privacy-conscious users, unstable networks | ChatGPT/Claude cannot run offline |
| **Live2D desktop pet** | Users seeking "companionship" | Character.ai has no desktop body |
| **Extensible framework** | AI developers, hobbyists | LangChain has no bio simulation, Live2D |
| **Bilingual i18n** | Chinese + English developers | Most frameworks are English-first |
| **GPU-free SNN** | Low-resource environments, edge computing | TensorFlow/PyTorch require GPU for speed |

**The strongest single pitch**: *"An AI that gets tired, gets hungry, lives on your desktop with a Live2D body, and runs completely offline."* — No existing project delivers all four simultaneously. **⚠️ But offline experience is currently unusable: ML model quality <0.5/10, weights random, output = noise/gray. The architecture exists; the training doesn't.**

### 7. Known Gaps

These features have infrastructure but need implementation work:

| Gap | Component | Blocker |
|-----|-----------|---------|
| YOLO object detection | Not started | Full implementation needed |
| Whisper in chat pipeline | faster-whisper 1.2.1 int8 offline STT active via AudioService._stt_faster_whisper() | ✅ **DONE** |
| Agent auto-routing | Wired into chat pipeline (Step 8) | ✅ Done (commit pending) |
| VisualDecoder training | Decoder weights random | Training loop needed |
| `/multimodal/stream` WebSocket | Dedicated handler + route registered | ✅ Done (commit pending) |
| Auto-repair pathway | `run_angela.py` auto-install on missing deps (--auto-repair flag) | ✅ Done |
| P4 refactoring | 28 long files, no load/E2E tests | Never started |

### 8. Documentation Map

| Document | Purpose |
|----------|---------|
| [README.md](../README.md) | Project overview, bilingual, quick facts |
| [ARCHITECTURE.md](ARCHITECTURE.md) | **6-layer architecture overview** (281 lines) |
| [ANGELA_FULL_ARCHITECTURE.md](architecture/ANGELA_FULL_ARCHITECTURE.md) | **Full component deep dive** (1330 lines, Chinese) |
| [IDEAL_ARCHITECTURE.md](IDEAL_ARCHITECTURE.md) | **Target architecture blueprint** (1115 lines) |
| [QUICK_START.md](QUICK_START.md) | **Getting started guide** (commands verified) |
| [COMPREHENSIVE_AUDIT_2026-06-25.md](COMPREHENSIVE_AUDIT_2026-06-25.md) | **Latest full project audit** |
| [COMPREHENSIVE_REPAIR_ROADMAP.md](COMPREHENSIVE_REPAIR_ROADMAP.md) | **Repair roadmap** (Phase A-F, all complete) |
| [MASTER_TASK_MAP.md](06-project-management/MASTER_TASK_MAP.md) | **Full provenance** for 144 claims across 23 docs |
| [SERVICE_CATALOG.md](development/SERVICE_CATALOG.md) | **Service directory** with import status |
| [GLOSSARY.md](00-overview/GLOSSARY.md) | **Terminology reference** |
| [AGENTS.md](../AGENTS.md) | **Developer/agent guidelines** (build, test, lint) |
| [CHANGELOG.md](../CHANGELOG.md) | **Version history** |

---

## 繁體中文版本

### 1. 什麼是 Angela AI Framework？

Angela AI 不是單一應用程式——它是一個**數位生命系統框架**，提供：

- **模組化聊天管線** — WebSocket → 情緒 → 危機 → 對齊 → LLM → 因果學習 → 回應，每階段都可替換
- **7 個 LLM 後端** — Anthropic、Google、OpenAI、Ollama、llama.cpp、ED3N（SNN）、GARDEN（輕量）
- **2 個本地推理引擎** — ED3N（46 萬詞典、SNN 反射）和 GARDEN（向量字典 + TensorSNN）
- **6 維狀態矩陣**（αβγδεθ）— 認知、情緒、環境狀態共享上下文
- **生物模擬** — 8 個模組（能量、代謝、內分泌、神經可塑性等）
- **11 個專業代理** — 創意、程式碼、資料、搜尋、視覺、聽覺等
- **模組管理器** — `ModuleManager`（M0-M5、6 檔案、100 測試）
- **多模態管線** — 視覺（CLIP 512-dim）、語音（edge-tts）、圖像生成（GVV + ThreeLayerVisual）
- **國際化** — `I18nManager` + `PromptManager`（en-US/zh-CN）
- **完整部署棧** — Docker、docker-compose（Redis、PostgreSQL、Prometheus、Grafana、Nginx）

### 2. 架構概覽

```
使用者輸入 → WebSocket → 情緒分析 → 危機閘門 → 生物刺激 → 對齊閘門 → LLM → 因果學習 → 回應
                                                                                ↓
                                                                          WebSocket推送 → 桌面渲染
```

六層架構：執行層（桌面/Web/CLI/像素）→ API/傳輸層（FastAPI）→ 應用服務層 → 核心基礎設施層 → AI引擎層（ED3N/GARDEN/GVV）→ 理論基礎層。

### 3. 核心元件一覽

| 類別 | 關鍵元件 | 狀態 |
|------|---------|:----:|
| **AI 引擎** | ED3N（46 萬詞典）、GARDEN（向量+SNN）、GVV 管線 | 🟢 |
| **LLM 後端** | Anthropic、Google、OpenAI、Ollama、llama.cpp、ED3N、GARDEN | 🟢 |
| **記憶** | HAM（ChromaDB）、VectorStore（雙後端）、SessionManager | 🟢 |
| **代理** | 11 個代理（創意、程式碼、資料、搜尋等） | 🟢 已註冊 |
| **生物模擬** | 8 個模組（能量、代謝、內分泌、神經等） | 🟢 |
| **前端** | Desktop（Electron+Live2D）、Web Dashboard、Pixel Angela | 🟢 |
| **基礎設施** | ModuleManager、i18n、Docker、CI/CD、OpenTelemetry | 🟢 |

### 4. 如何使用

**開發流程**：
```bash
python -m venv .venv; pip install -e "apps/backend[dev]"   # 貢獻者層級；快速體驗用 "apps/backend"、完整功能用 "apps/backend[standard]"
python scripts/run_angela.py          # 啟動全部
pytest tests/                         # 運行測試
```

**加入新 LLM 後端**：
1. 在 `services/llm/providers/` 建立類別，實作 `LLMBackend` 協定
2. 在 `__init__.py` 註冊
3. 在 `angela_config.yaml` 加入配置

**加入新代理**：
1. 建立類別實作 `AgentAdapter.execute()` 介面
2. 在 `agent_manager.py` 註冊
3. 撰寫測試

### 5. 智能評分

> **⚠️ 分數類型說明**: 以下分數為「框架分數」（已實現的框架能做什麼，含靜態數據）。訓練後的實際分數見 `INTELLIGENCE_ASSESSMENT.md`。

| 能力 | 有 LLM | 純本地 (框架) | 純本地 (訓練後) | 實現與備註 |
|:-----|:------:|:------------:|:--------------:|:---------|
| 文字理解 | 7/10 | 0.5/10 | **3.0/10** | ED3N 46 萬詞典存在但僅為概念映射（1990 年代 NLP）。真正理解來自 LLM API。訓練後 acc=0.914 (訓練集)。 |
| 圖像理解 | 7/10 | 0.5/10 | **5.0/10** | numpy 色彩直方圖 + Sobel 邊緣（1990 年代 CV）。CLIP 需要 torch。訓練後 CLIP 語意已接通。 |
| 語音理解 | 5/10 | 0/10 | **5.0/10** | Whisper encoder 存在但 numpy 降級為基本 MFCC 統計。訓練後 Whisper STT 已接通。 |
| 文字生成 | 7/10 | 0.5/10 | **0.5/10** | 7 個 LLM 後端提供真實生成。ED3N/GARDEN decoder = 字典映射 + 隨機權重。訓練後仍為字典拼接。 |
| 圖像生成 | 6/10 | 0/10 | **5.0/10** | GVV 管線架構完整。**所有權重隨機 → 輸出為灰色畫布或雜訊。** ThreeLayerVisual MSE=0.009（32×32 模糊 = 1995 品質）。訓練後有結構但仍然模糊。 |
| 語音輸出 | 4/10 | 0/10 | **4.0/10** | edge-tts 呼叫外部 API。原生 AudioWaveformDecoder = 波表雜訊（隨機權重）。訓練後 309x loss reduction，有結構但非語音品質。 |
| 記憶 | 7/10 | 7/10 | **7/10** | VectorStore + HAM 真正有用，不依賴 LLM。 |
| 推理 | 4/10 | 0.5/10 | **0.5/10** | CausalReasoningEngine 僅 Pearson 相關。PlanningEngine 模板匹配。MathRippleEngine 為真正原創認知模型。訓練後基準測試 0/5。 |
| 自主性 | 3/10 | 0.5/10 | **3.0/10** | AutonomousLifeCycle 已接線但無 LLM 不穩定。訓練後框架完整但效果不明顯。 |
| 後設認知 | 5/10 | 4/10 | **4/10** | MetaController 信心追蹤有效。NeuroAutoSelector 啟發式。 |
| **綜合** | **6.0/10** | **<0.5/10** | **3.0/10** | 框架架構 ~85-90% 完整。**ML 訓練 ~5%。** 原生引擎輸出為低品質/未初始化。所有真實智慧來自 LLM API。訓練後基準測試 38%。 |

### 5.5 學習能力評估

Angela AI 有 **4 個學習層級**，每個建立在前者之上。這比標準 AI 框架深得多（詳見 §6.1 對比）。

#### 5.5.1 評分方式

百分比是**定性評估**，基於：
- **機制覆蓋率**：每層級的理想機制有多少存在
- **測試驗證**：機制是否實際運作（代碼審查 + 測試結果）
- **功能完整度**：每個機制離理想實現多近
- **整合度**：機制之間如何協作

#### 5.5.2 Level 1 — 學習新詞彙並使用 → **80%**

| 機制 | 狀態 | 說明 |
|------|:----:|:-----|
| `ContinuousLearningPipeline._detect_and_grow()` | ✅ | 每次互動後自動發現新 token 並增長字典 |
| `DictionaryLayer.learn_from_conversation()` | ✅ | 從對話中檢測新概念，用信心分數增長字典條目 |
| `GARDENEngine.learn_from_interaction()` | ✅ | 增長向量字典，同時支援中英文 |
| 編碼/解碼已學習詞彙 | ✅ | 新詞彙在未來回應中可被自動編碼和解碼 |
| 多語言支援 | ✅ | CJK 字符檢測 + 英文詞邊界；不同語言有不同信心啟發式 |
| **端到端驗證** | ✅ | 測試通過：「量子計算機」→ 字典從 47→48 條，正確編碼為 `['l1','l2']`，解碼回原文 |

**缺失 (20%)**：跨模態概念學習（文字↔圖像↔音訊）未接線；學習增長期間無自動低信心條目清理。

#### 5.5.3 Level 2 — 學習詞彙並行動 → **70%**

| 機制 | 狀態 | 說明 |
|------|:----:|:-----|
| `ED3NTrainer` / `JointTrainer` | ✅ | 調整字典條目信心 + input/output 鍵之間的網路連接權重 |
| `DictionaryClassifier.learn()` | ✅ | 學習 `文字→查詢類型→動作類型` 映射 |
| `GARDENEngine` Hebbian SNN 更新 | ✅ | `hebbian_update()` 強化共現概念間的 SNN 權重連接 |
| `CausalReasoningEngine.learn()` | ✅ | 從觀測中學習因果關係（Pearson 相關基礎） |
| 反射模式學習 | ✅ | `learn_reflex()` 新增 pattern→response；`ED3NLearningIntegration` 處理外部同步 |
| `GARDENEngine.learn_batch()` | ✅ | 批次版本：先收集所有 token，一次性重建索引，再執行所有 Hebbian 更新 |

**缺失 (30%)**：`ED3NLearningIntegration` → `LearningManager`/`ReplayBuffer`/`MemoryLearning` 連接已斷開（Phase 9-12 清理）。這些元件優雅回傳 `None`。

#### 5.5.4 Level 3 — 不改代碼的最強學習 → **70% (目標 ≥60%)**

| 機制 | 狀態 | 說明 |
|------|:----:|:-----|
| 所有 Level 1+2 機制 | ✅ | 可透過 `magic_numbers.py` 配置 — buffer 大小、間隔、學習率、閾值 |
| `ContinuousLearningPipeline` 自動訓練 | ✅ | 每 `train_interval`（預設 50）當 buffer ≥ `min_examples_for_train`（預設 20）時自動觸發訓練 |
| `TrainingCoordinator` | ✅ | 追蹤跨領域訓練：ED3N（反射、數學、邏輯）、GARDEN（知識、指令、一般）、Cloud LLM（創意、意見）。SHA-256 去重。 |
| 狀態持久化 (`save()`/`load()`) | ✅ | 完整引擎狀態跨重啟持久化（字典 + SNN 權重 + CL 狀態） |
| 配置驅動調參 | ✅ | 所有參數透過 `magic_numbers.py` — 不需源碼修改即可調整學習行為 |
| 多模型協調 | ✅ | `ModelBus.get_training_assignment()` + `DOMAIN_OWNERSHIP` 表將訓練路由到正確引擎 |

**缺失 (30%)**：無後設學習（學習如何學習）；無課程學習；無自我監督探索迴圈；無自動評估計畫。

#### 5.5.5 Level 4 — 需改代碼

| 功能 | 所需工作 |
|------|---------|
| 新網路架構 | `CoreNetwork`、`SNNCore` 或 `TensorSNNCore` 代碼修改 |
| 強化學習 | 新訓練迴圈、獎勵函數、策略網路 |
| 少樣本 / 後設學習 | MAML 式外迴圈、任務分佈取樣 |
| 外部 ML 整合 | HuggingFace、PyTorch Lightning 或 ONNX runtime 連接器 |
| 自我監督學習 | Pretext 任務生成器、對比損失實現 |

#### 5.5.6 獨特差異化優勢

與其他 AI 框架不同（見 §6.1），Angela 有**真正的權重學習**，而不只是上下文管理：

| 面向 | Angela AI | 其他框架 (AutoGPT, MemGPT, LangChain) |
|------|-----------|----------------------------------------|
| **學習類型** | 🧠 突觸權重更新 + 字典增長 | 📋 上下文管理 + RAG 檢索 |
| **詞彙增長** | ✅ 即時新增詞典條目 | ❌ 無新詞彙；依賴 LLM 靜態知識 |
| **權重改變** | ✅ Hebbian + 梯度式調整持久化 | ❌ 模型權重永不改變（靜態 LLM） |
| **知識內化** | ✅ 新概念成為網路內部表示的一部分 | ❌ 知識在外部（從 DB 檢索，注入上下文窗口） |
| **持久化** | ✅ 學習的知識透過 save/load 跨重啟存活 | ✅ 事實存活（在 DB），但沒有「學習」發生 |
| **離線運作** | ✅ 所有學習機制在本地執行，不需 API | ❌ RAG + LLM 需要外部服務 |

**結論**：多數 AI「代理」是專家級上下文管理器——它們不學習，只檢索。Angela AI 透過字典增長和權重更新實現真正的即時學習。這將它放在不同類別：**持續學習代理**，而非基於 RAG 的聊天機器人。

### 6. 競爭分析 — 優點與缺點

#### 6.1 差異化優勢

| 優勢 | 說明 | vs LangChain | vs AutoGPT | vs Character.ai |
|:-----|:-----|:-------------|:-----------|:----------------|
| **ED3N 字典解耦** | 加入知識不需要重新訓練（46 萬條、3 語種） | RAG 需向量資料庫 | 無對應 | 無對應 |
| **三層降級（架構）** | LLM → ED3N SNN → GARDEN numpy。⚠️ ED3N/GARDEN 輸出品質低（未訓練），降級後變垃圾而非平順降級。 | 單一 LLM 無降級 | 單一 LLM | 僅雲端 |
| **Live2D 桌面身體** | 即時情緒表情的桌面角色 | 沒有身體 | 沒有身體 | Web 聊天無桌面端 |
| **生物模擬 8 模組** | 能量、代謝、內分泌、晝夜節律 | 無生物模擬 | 無生物模擬 | 有限個性無身體 |
| **純 CPU 推理** | GARDEN numpy 後端，不需 GPU | 多數需 GPU | OpenAI API | 僅雲端 |
| **語言感知 i18n** | PromptManager + I18nManager，45 測試 | 臨時在地化 | 僅英文 | 英文+日文有限 |
| **6D 狀態矩陣** | 所有元件共享 αβγδεθ 上下文 | 無共享狀態 | 無共享狀態 | 封閉 |

#### 6.2 弱點（誠實）

| 弱點 | 影響 | 根本原因 |
|:-----|:-----|:---------|
| **ML 內容跟不上框架** | 使用者體驗遠低於架構承諾 | Decoder 隨機權重、Whisper 未接線、SNN 未訓練 |
| **複雜度/功能比過高** | 612 檔案但功能比預期少 | 試圖同時做太多事 |
| **用戶定位不明** | 無法明確吸引任何單一群體 | 開發者框架？產品？研究平台？ |
| **無標準基準測試** | 缺乏 MMLU、HumanEval 等 | 專注基礎設施測試而非品質測試 |
| **代理已註冊但未呼叫** | 11 代理存在但管線不呼叫 | 架構決策未定 |
| **自動路由缺失** | QueryClassifier + ModelBus 被繞過 | 管線捷徑降低效能 |

#### 6.3 真正吸引用戶的賣點

| 賣點 | 目標族群 | 為何獨特 |
|:-----|:---------|:---------|
| **離線優先 AI** | 注重隱私、網路不穩的用戶 | ChatGPT/Claude 無法離線 |
| **Live2D 桌面寵物** | 尋求陪伴感的用戶 | Character.ai 沒有桌面身體 |
| **可擴展框架** | AI 開發者、Hobbyist | LangChain 無生物模擬/Live2D |
| **中英雙語 i18n** | 中英文開發者 | 多數框架以英文優先 |
| **免 GPU SNN** | 低資源環境、邊緣計算 | TensorFlow/PyTorch 需要 GPU |

**最強單一賣點**：*「一個會累、會餓、活在桌面上、有 Live2D 身體、可以完全離線運作的 AI」* — 沒有專案同時做到這四點。**⚠️ 目前離線體驗極差**：ML 模型品質 <0.5/10，權重隨機，輸出為雜訊/灰色畫布。離線架構存在但實際運作需要大量訓練。

### 7. 已知差距

| 功能 | 狀態 | 說明 |
|------|:----:|:-----|
| YOLO 物件偵測 | ❌ | 未開始 |
| Whisper 接線 | ❌ | 已安裝未接入管線 |
| 代理自動路由 | ✅ | 已接入聊天管線（第 8 步） |
| VisualDecoder 訓練 | ❌ | 權重隨機 |
| WebSocket 路由 | ✅ | 專用 handler + 路由已註冊 |
| 自動修復 | ❌ | `run_angela.py` 缺少自動安裝 |

### 8. 文件地圖

| 文件 | 說明 |
|------|------|
| [README.md](../README.md) | 專案總覽（中英雙語） |
| [ARCHITECTURE.md](ARCHITECTURE.md) | 6 層架構總覽 |
| [完整架構圖](architecture/ANGELA_FULL_ARCHITECTURE.md) | 完整元件深度說明（1330 行） |
| [QUICK_START.md](QUICK_START.md) | 快速啟動指南 |
| [最新審計報告](COMPREHENSIVE_AUDIT_2026-06-25.md) | 全專案審計 |
| [MASTER_TASK_MAP.md](06-project-management/MASTER_TASK_MAP.md) | 144 項 claim 完整溯源 |

---

**Version**: 7.5.0-dev | **Code**: 612 Python files, ~96K lines | **Tests**: 4,785 / 4,261 (41 skipped) | **Intelligence**: 6.0/0.5 (with LLM / native only) | **Architecture**: ~85-90% | **Training**: ~5%
