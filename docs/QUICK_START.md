# Unified AI Project — Quick Start Guide

> **Last verified**: 2026-06-25 — commands tested against actual project structure

## Prerequisites

- Python 3.10+
- Node.js 16+
- Ollama (LLM backend, optional for local inference)

## Setup

```bash
# 1. Clone
git clone https://github.com/catcatAI/Unified-AI-Project.git
cd Unified-AI-Project

# 2. Create and activate Python virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\Activate.ps1
# macOS/Linux:
source .venv/bin/activate

# 3. Install Python backend dependencies
pip install -r apps/backend/requirements.txt

# 4. Install JS workspace dependencies
npx pnpm install --no-frozen-lockfile
npx pnpm approve-builds --all
```

## Run

```bash
# Option 1: Unified launcher (recommended)
python scripts/run_angela.py              # Start all (backend + desktop)
python scripts/run_angela.py --api-only   # Backend only
python scripts/run_angela.py --health-check  # Health check

# Option 2: Backend directly
python apps/backend/start_server.py

# Option 3: Desktop app (separate terminal)
npx pnpm dev:desktop
```

## Test

```bash
# Run all tests
pytest tests/ apps/backend/tests/

# Run with coverage
pytest --cov=apps/backend/src --cov-report=html

# Single test file
pytest tests/path/to/test_file.py -v
```

## Services (after starting)

| Service | URL |
|---------|-----|
| Backend API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| Web dashboard | http://localhost:3000 |

## Project Structure (key directories)

| Directory | Purpose |
|-----------|---------|
| `apps/backend/src/` | Python FastAPI backend (612 files, ~96K lines) |
| `apps/desktop-app/` | Electron + Live2D desktop companion |
| `apps/web-live2d-viewer/` | Web-based Live2D viewer |
| `apps/pixel-angela/` | PyQt6 pixel art engine |
| `packages/shared-js/` | Shared JS library (33 files) |
| `packages/cli/` | Python CLI tools |
| `tests/` | Test suite (~4,261 tests) |
| `docs/` | Documentation (50+ MD files) |

## Key Facts

- **612 Python files** in backend src (~96K lines)
- **~4,261 tests** across 480+ test files, 0 errors
- **Architecture health**: ~85-90% (2026-06-25 audit)
- **Repair phases**: All 6 phases (0-5 + C/D/E/F) complete
- **See**: `docs/COMPREHENSIVE_REPAIR_ROADMAP.md` for full repair status

---

*For detailed developer guidelines, see [AGENTS.md](../AGENTS.md). For version history, see [CHANGELOG.md](../CHANGELOG.md). For full audit, see [COMPREHENSIVE_AUDIT_2026-06-25.md](COMPREHENSIVE_AUDIT_2026-06-25.md).*
