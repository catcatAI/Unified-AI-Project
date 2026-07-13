<!--
  =============================================================================
  ANGELA-MATRIX: L3 [β] [B] [L4]
  FILE_HASH: Initial
  FILE_PATH: docs/usage/QUICK_START.md
  FILE_TYPE: documentation
  PURPOSE: Quick start guide — direct path from clone to running
  VERSION: 1.0.0
  STATUS: active
  LANGUAGE: en
  LAST_MODIFIED: 2026-07-07
  AUDIENCE: users, developers
  =============================================================================
-->

# Quick Start Guide

> **Goal**: Get the Angela AI system running in under 10 minutes.

## Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | 3.10+ | Tested with 3.10–3.14 |
| Node.js | 16+ | Required for frontends |
| pnpm | latest | JS workspace manager (`npx pnpm` works) |
| Ollama | latest | Local LLM backend (optional but recommended) |

## Step 1: Clone & Setup

```powershell
git clone https://github.com/catcatAI/Unified-AI-Project.git
cd Unified-AI-Project

# Python virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1

# Install backend dependencies (path-based editable install, run from repo root)
pip install -e "apps/backend[standard,testing]"

# Install JS dependencies
npx pnpm install --no-frozen-lockfile
npx pnpm approve-builds --all
```

## Step 2: Configure

Copy the environment template and edit as needed:

```powershell
copy .env.example .env
```

Minimal `.env` for direct start:

```ini
# LLM backend (at least one required)
OLLAMA_HOST=http://localhost:11434
OPENAI_API_KEY=

# System
LOG_LEVEL=INFO
```

**No LLM?** The system falls back to ED3N+GARDEN built-in inference models. Capabilities are limited (see [SCENARIOS.md](SCENARIOS.md#without-an-llm)).

## Step 3: Start

```powershell
# Option A: Unified launcher (recommended)
python scripts/run_angela.py

# Option B: Backend only
python scripts/run_angela.py --api-only

# Option C: Health check first
python scripts/run_angela.py --health-check
```

The backend starts at `http://localhost:8000`. API docs are at `http://localhost:8000/docs`.

## What Works Out of the Box

| Feature | Status | What to Expect |
|---------|--------|----------------|
| **Chat API** | ✅ | `POST /api/v1/chat` — basic dialog with emotion-aware responses |
| **Emotion System** | ✅ | Personality adapts to conversation context |
| **Memory** | ✅ | HAM + VectorStore, persists across sessions |
| **Image Understanding** | ✅ | `POST /api/v1/chat` with image attachment (vision_service) |
| **TTL Model** | ✅ | Three-layer visual decoder, already trained |
| **Training Pipeline** | ✅ | `python scripts/train_pipeline.py` (see SCENARIOS.md) |
| **Live2D Desktop** | ✅ | `npx pnpm dev:desktop` (separate terminal) |
| **Web Viewer** | ✅ | `npx pnpm dev:web` |

## What Requires an LLM

If you skip Ollama setup, these fall back to ED3N/GARDEN (reduced quality):

- Complex conversation reasoning
- Code generation
- Multi-turn planning
- Knowledge-based Q&A

## Troubleshooting

### "Module not found" errors
```powershell
pip install -e "apps/backend[standard,testing]" --force-reinstall
```

### Port 8000 already in use
```powershell
# Check what's using it
netstat -ano | findstr :8000
# Kill the process, or change port in .env:
API_PORT=8001
```

### Live2D desktop doesn't open
Run the web viewer instead:
```powershell
npx pnpm dev:web
```
Then open `http://localhost:5173` in your browser.

### Ghostscript/GPL Ghostscript warnings
These are harmless and can be ignored. They come from the PDF/image processing pipeline.

### Memory usage grows over time (leak prevention)
If you notice the system consuming more memory during long sessions, the system now automatically caps internal history buffers. All unbounded arrays have been fixed (Round 3 audit). Expected behavior:
- **Chat sessions**: TTL cache purges every 60s, max 1000 sessions
- **Vector store**: capped at 10,000 entries (FIFO eviction)
- **Emotion history**: capped at 1,000 states
- **All JS listener arrays**: deduplicated with `off()` cleanup on destroy
- **Live2D manager**: `_stopAnimation` → `stop()` (was throwing TypeError, leaking rAF/timers forever)

### "No module named 'ai.*' "
Ensure you're running from the project root (`Unified-AI-Project/`), not from inside `apps/backend/`.

## Next Steps

- [Usage Scenarios](SCENARIOS.md) — train-first, configure-first, custom LLM
- [Scripts Reference](../scripts/ACTIVE_SCRIPTS.md) — full command catalog
- [Architecture Overview](../architecture/ANGELA_FULL_ARCHITECTURE.md) — system design
