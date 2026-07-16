<!--
  =============================================================================
  ANGELA-MATRIX: L3 [β] [B] [L4]
  FILE_HASH: Initial
  FILE_PATH: docs/usage/SCENARIOS.md
  FILE_TYPE: documentation
  PURPOSE: Usage scenarios — direct start, train-first, configure-first
  VERSION: 1.0.0
  STATUS: active
  LANGUAGE: en
  AUDIENCE: users, developers
  LAST_MODIFIED: 2026-07-07
  =============================================================================
-->

# Usage Scenarios

## Scenario A: Direct Start (Quickest Path)

For users who want to see the system running immediately.

```powershell
# 1. Install (see QUICK_START.md for details)
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e "apps/backend"          # Quickest path: lightweight tier (see QUICK_START.md for [standard]/[dev])
npx pnpm install --no-frozen-lockfile

# 2. Start
python scripts/run_angela.py
```

**What you get**:
- ED3N+GARDEN inference (no external LLM required)
- Emotion system active
- Memory/vector store operational
- Chat API at `http://localhost:8000`

**Limitations without LLM**:
- Offline: deterministic engines (math/physics/chemistry) work = 9.5/10 real capability; neural-net net contribution ≈35% (DET-CARRY differential, ED3N 35.3% / GARDEN 35.6% — NOT the SNN-only score; multi-dimensional scores in INTELLIGENCE_ASSESSMENT.md §1 & §4.1.1). With LLM ≈6.0/10.
- No advanced reasoning or code generation
- Responses shorter and more template-driven

---

## Scenario B: Train First, Then Start

For users who want the best possible local inference quality.

### B1. Quick Training (5-10 min)

```powershell
# Train ED3N text encoder + GARDEN SNN
python scripts/train_pipeline.py --quick

# Verify trained weights
python scripts/verify_training.py
```

This trains:
- **ED3N**: Reflex + SNN + Decode cycle (~500 steps)
- **GARDEN**: Hebbian learning convergence (~200 steps)
- **JointTrainer**: Cross-modal alignment

### B2. Full Training (30-60 min)

```powershell
# Phase 0: Visual/Audio encoder projections
python scripts/train_visual_decoder.py --texture-steps 500

# Phase 1-2: Contrastive + reconstruction learning
python scripts/train_multimodal_real.py

# Phase 3-5: Full pipeline (8 phases)
python scripts/train_pipeline.py --all-phases
```

### B3. Verify Training Results

```powershell
# Check weights exist
python -c "import numpy as np; data=np.load('data/multimodal/weights/p29_trained.npz'); print(list(data.keys()))"

# Expected output: 7 ED3N + 8 JointTrainer = 15 weight arrays
# ['visual_projection', 'audio_projection', 'cross_modal_projection', ...]
```

### B4. Expected Quality Improvement

| Metric | Untrained | Quick Train | Full Train |
|--------|-----------|-------------|------------|
| ED3N Text Acc | 0.60 | ~0.80 | ~0.91 |
| GARDEN SNN | 0.50 | ~0.65 | ~0.70 |
| SSIM | 0.85 | 0.90 | 0.95+ |

> **Note**: ED3N accuracy (0.91) is training-set accuracy. Real-world performance may be lower due to distribution shift. See [PHASE_REVIEW6.md](../06-project-management/plans/PHASE_REVIEW6.md) for methodology.

### B5. Evaluation After Training

```powershell
# Run evaluation benchmark
python scripts/run_angela.py --health-check

# Run comprehensive tests
pytest tests/ai/ed3n/ tests/ai/garden/ -v
```

---

## Scenario C: Configure First, Then Start

### C1. LLM Provider Configuration

The system supports 9 LLM backends. Set at least one in `.env`:

```ini
# --- OpenAI (best quality) ---
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o

# --- Anthropic ---
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-sonnet-4-20260514

# --- Ollama (local, free) ---
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3

# --- Other backends ---
# GOOGLE_API_KEY=...
# AZURE_OPENAI_KEY=...
# DEEPSEEK_API_KEY=...
# GROK_API_KEY=...
# XAI_API_KEY=...
# CUSTOM_LLM_ENDPOINT=...
```

Backend priority order (configurable via `LLM_PRIORITY_ORDER` env var):
1. OpenAI → Anthropic → Ollama → Google → Azure → DeepSeek → Grok → xAI → Custom

### C2. Hardware Profile

```ini
# Automatic detection (desktop/laptop/power-saver/low-power/server)
# Override with:
HARDWARE_SCENARIO=SERVER_CLOUD
```

Effects of each profile:

| Profile | Decision Interval | Heartbeat | Neuroplasticity | Use Case |
|---------|:-----------------:|:---------:|:---------------:|----------|
| HIGH_PERFORMANCE_DESKTOP | 60s | 5-30s | 60s | Development/gaming PC |
| LAPTOP_NORMAL | 120s | 10-60s | 120s | Everyday laptop |
| LAPTOP_POWER_SAVER | 300s | 30-120s | 300s | Battery saving |
| LOW_POWER_DEVICE | 600s | 60-300s | 600s | Raspberry Pi / thin client |
| SERVER_CLOUD | 30s | 1-10s | 30s | Cloud deployment |

### C3. Emotion System

```ini
# Personality preset (alpha/beta/gamma/delta)
# alpha: energetic, curious, expressive (default)
# beta: analytical, focused, reserved
# gamma: warm, empathetic, playful
# delta: loyal, protective, consistent
PERSONALITY_PRESET=delta

# Feedback sensitivity (0.0–1.0)
EMOTION_FEEDBACK_SENSITIVITY=0.7

# Sustained negative threshold (interactions before mood shift)
EMOTION_SUSTAINED_NEGATIVE_THRESHOLD=3
```

### C4. Training Configuration

```ini
# Training hyperparameters
TRAINING_LEARNING_RATE=0.001
TRAINING_BATCH_SIZE=32
TRAINING_EPOCHS=100

# Dataset paths (default: auto-download)
TEXT_DATASET_PATH=data/datasets/text
IMAGE_DATASET_PATH=data/datasets/images

# Vector store
VECTOR_STORE_PATH=data/vector_store
VECTOR_STORE_BACKEND=auto  # chromadb or numpy+json
```

### C5. Memory & Context

```ini
# Memory limits
MAX_CONTEXT_LENGTH=4096
HAM_MAX_ENTRIES=10000
VECTOR_STORE_MAX_RESULTS=20

# Session management
SESSION_TIMEOUT_MINUTES=30
```

### C6. Logging & Debug

```ini
LOG_LEVEL=DEBUG      # DEBUG/INFO/WARNING/ERROR
LOG_FORMAT=detailed  # detailed or simple
API_LOG_BODY=true    # Log request/response bodies
```

---

## Scenario D: Without an LLM

ED3N + GARDEN only (no external API calls).

```powershell
# Start without any LLM configured
python scripts/run_angela.py
```

**Capable of**:
- Task status reporting ("what can you do?")
- Simple pattern matching responses
- Basic memory operations
- Image processing (vision service)

**Not capable of**:
- Complex reasoning
- Multi-turn planning
- Knowledge integration
- Code generation

---

## Scenario E: Docker Deployment

> Docker support is experimental. The backend can run in a container, but GPU acceleration requires additional setup.

```powershell
# Build image
docker build -t angela-ai -f apps/backend/Dockerfile .

# Run (CPU only)
docker run -p 8000:8000 -v ${PWD}/data:/app/data angela-ai

# Run (GPU with Ollama sidecar)
docker run -p 8000:8000 --gpus all -e OLLAMA_HOST=http://ollama:11434 angela-ai
```

---

## Choosing Your Scenario

| Your Goal | Recommended Path | Time |
|-----------|-----------------|------|
| "Just see it work" | **Scenario A** → Direct Start | 5 min |
| "Best local quality" | **Scenario B** → Train First (quick) | 15 min |
| "Production quality" | **Scenario B** → Train First (full) + **C1** (LLM) | 45 min |
| "Custom deployment" | **Scenario C** → Configure + **A** → Start | 10 min |
| "No internet/API keys" | **Scenario D** → No LLM | 5 min |
| "Server deployment" | **Scenario C2** → Server profile + **E** → Docker | 20 min |

## See Also

- [Quick Start](QUICK_START.md) — basic installation
- [ACTIVE_SCRIPTS.md](../scripts/ACTIVE_SCRIPTS.md) — command reference
- [MASTER_TASK_MAP.md](../06-project-management/MASTER_TASK_MAP.md) — development roadmap
