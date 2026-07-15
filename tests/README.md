# Test System

## Overview

This directory contains the Unified AI Project test suite. Tests are organized by domain.
**4,387 tests collected** (tests/; authoritative count per AGENTS.md, last verified after §X #208 — DI path validation + route fix).

Historical executed run (pre-cleanup, ~2026-07-14): 4,544 passed, 185 failed, 39 errors, 85 skipped, 2 xfailed. The failures below explain the 185/39.

## Directory Structure

```
tests/
├── ai/               # AI engine tests (ED3N, GARDEN, meta, lifecycle, multimodal)
├── api/              # API route tests
├── benchmarks/       # Performance benchmarks
├── cli/              # CLI tool tests
├── core/             # Core system tests (state matrix, formulas, etc.)
├── desktop/          # Desktop interaction tests
├── desktop-app/      # Electron desktop app tests
├── fragmenta/        # Fragmenta module tests
├── integration/      # Integration tests
├── logs/             # Test log output
├── mcp/              # MCP connector tests
├── models/           # Model tests
├── modules_fragmenta/# Fragmenta submodule tests
├── performance/      # Performance tests
├── pet/              # Pet system tests
├── security/         # Security tests
├── services/         # Service layer tests
├── shared/           # Shared module tests
├── test_data/        # Test fixtures and data
├── test_output_data/ # Test output artifacts
├── test_results/     # Test result files
├── tools/            # Tool tests
├── training/         # Training pipeline tests
├── unit/             # Unit tests
└── utils/            # Utility tests
```

## Running Tests

```bash
# All tests
pytest tests/

# All tests with timeout (recommended for CI)
pytest tests/ --timeout=30 --timeout_method=thread -q

# Single file
pytest tests/path/to/test_file.py --timeout=10 -v

# Single test function
pytest tests/path/to/test_file.py::test_function_name -v

# Quick collect-only (verify test count)
pytest tests/ --collect-only -q 2>&1 | tail -5

# With coverage
pytest tests/ --cov=apps/backend/src --cov-report=html

# Fast (skip slow markers)
pytest tests/ -m "not slow"
```

## Manual / Terminal Testing

All 3 frontends (web-live2d-viewer, Electron, Electron MVP) feature a **floating terminal overlay** (toggle with Ctrl+`) that:

- Pipes user input via WebSocket or HTTP POST to `/api/v1/chat/unified`
- Displays full JSON responses (emotion, route, hit_source, source)
- Monospace output with colorized JSON

### Quick Verification

```bash
# Verify backend is running
curl http://localhost:8000/health

# Test chat endpoint
curl -X POST http://localhost:8000/api/v1/chat/unified \
  -H "Content-Type: application/json" \
  -d '{"message": "hello", "session_id": "test-001"}'
```

### Manual Test Patterns

1. Start backend: `python run_angela.py` or `pnpm dev:backend`
2. Open any frontend in browser/Electron
3. Press Ctrl+` to open terminal
4. Type a message and press Enter — observe `route` and `hit_source` fields
5. Test patterns:

| Input | Expected Route | What to Verify |
|-------|---------------|----------------|
| "你好" / "hello" | `llm` | Natural response with emotion |
| "2+2=?" | `dual_rail` | Correct math answer |
| "幫我建立一個筆記" | `gate_confirm` | Confirmation dialog before execution |
| "我今天很難過" | `llm` | Empathetic response with emotion context |
| "/help" | `system` | REPL command help text |

### Test Coverage by Intelligence Layer

- **L1 (Hardcoded/ED3N Reflex)**: Basic greetings, math, simple Q&A
- **L2 (Local Trained Models)**: ED3N classification, GARDEN knowledge, pattern matching
- **L3 (LLM)**: Complex dialogue, creative responses, emotional support

## Security & Autonomy Testing

Key aspects to verify during testing:

- **File operations** are restricted to `_ALLOWED_ROOTS` (Desktop/Documents/Downloads/Projects)
- **Autonomous decisions** are logged through `BehaviorExecutor` with success/failure tracking
- **Execution gate** requires confirmation for destructive operations
- **Safe eval** uses AST whitelist — no arbitrary code execution

## Current Test State

| Domain | Test Count |
|--------|-----------|
| AI core | ~400 |
| GARDEN | ~125 |
| Multimodal | ~211 |
| Security | ~100+ |
| Services | ~200+ |
| Integration | ~150+ |
| Training | ~100+ |
| Other | ~3,000+ |
| **Total** | **4,387** |

## Known Test Failure Categories (2026-07-14 Audit)

The remaining failures were audited and split into **environment/asset gaps** (not code bugs — fix by installing/downloading/training or documenting) and **real bugs** (API drift in tests that must be realigned with the current API). Do **not** guess-fix API/class names — understand the current API first.

### 1. Not-installed dependencies (RESOLVED)
- `python-multipart` was missing from all dependency files → FastAPI `Form` routes failed at boot. Now declared in `apps/backend/pyproject.toml` BASE (`python-multipart>=0.0.20`, commit `9415928c`).
- `semver`, `google-api-python-client`/`google-auth*` (the `google` extra), `starlette` are already correctly declared/installed.

### 2. Not-downloaded datasets
- Lexical dictionaries **are present**: `data/dictionaries/{cedict,jmdict,wordnet}.json`. (The raw-source download URLs in `scripts/download_datasets.py` currently 404 — external source moved — but the processed JSONs are committed.)
- `CIFAR-10` / `ESC-50` are **not downloaded**, yet the heavy multimodal training suite passes (309 passed / 20 failed in the audit), so they are **not** required by any current failure.

### 3. Not-trained assets (GENERATED, absent in this checkout)
- `data/multimodal/weights/p29_trained.npz` is a **training output** (produced by `MultimodalTrainingPipeline.save_weights` / decoder `save_*`); it is not downloaded. A few decoder/encoder tests fail with `p29_trained.npz not found` / `load_default_audio_decoder_weights returned False`.
- ⚠️ Key-format gap to reconcile before regeneration: `save_weights` writes `vision_W`/`audio_W`, but `load_default_visual_decoder_weights` expects `visual_decoder_W`/`texture_*`. Regenerate via the decoder's own `save_visual_decoder_weights` after training.

### 4. Environment / performance (import timeouts, flaky)
- `torch` and `chromadb` are installed but import slowly under pytest's import-timeout guards → `torch unavailable (import timed out)`, `chromadb not available (import check failed)`. Not missing — just slow.
- `There is no current event loop in thread 'MainThread'` — Python 3.12+ removed implicit `asyncio.get_event_loop()`; tests must use `asyncio.run()`. (One instance fixed: `test_audio_service.py`.)
- Windows temp-file `PermissionError` (file lock during cleanup) — flaky, environment-specific.

### 5. Real bugs — API drift in tests (realign with current API; do NOT guess)
These tests reference removed/renamed APIs. Each needs the current API understood before fixing:
- `AngelaConfig` lost attributes: `_angela_dir`, `_interpret_axis`, `build_anchor_context`, `get_complexity_thresholds`, `get_intent_keywords`, `get_learned*`, `get_llm_config`, `get_routing_policy`, `get_tickle_config`, `reload_if_changed`, `watch`.
- Constructor signatures changed: `BaseAgent(name=)`, `AgentCollaborationManager(name=)`, `Hormone(decay_rate=)`, `WorkflowConfig(auto_deploy=)`.
- Renamed/removed: `AngelaChatService` → `ChatService` (and `_detect_drive_intent` removed); `main_api_server._build_help_text`/`_handle_model_command`/`_handle_repl_command`/`_handle_tickle_command`; `AttentionController.decide_focus`; `AudioService._generate_demo_speech_audio`; `GrayZoneVariableType.IDENTITY`; `HSMFormulaSystem._simulate_discovery`; `neuro_auto_selector.ResourceAwarenessService`.
- Misc: `_IncludedRouter.path`, `KeyError: 'profile_id'`, `fixture 'images' not found`, `test_bootstrap` `KeyError: 'max_fps'` (BootstrapManager state), `test_path_config` expects `apps/backend/tests/{data,training,models,checkpoints,configs}` (stale — actual `path_config` uses `apps/data`).

### 6. Fixed this session
- `apps/backend/src/core/__init__.py`: lazy `__getattr__` returned a sentinel for `pytest_plugins`, which pytest probed on every imported module → `pytest.UsageError` broke collection of `test_bootstrap`/`test_config_mutator`/`test_state_decoupling`. Now raises `AttributeError` for dunders + `pytest_plugins`.
- `apps/backend/tests/unit/test_audio_service.py`: `asyncio.get_event_loop().run_until_complete` → `asyncio.run` (Python 3.14).

## CI / Pre-Commit

Before committing, run:

```bash
black apps/backend/src tests/
flake8 apps/backend/src tests/
pytest tests/ --timeout=30 --timeout_method=thread -q
```

Test counts are tracked in: AGENTS.md, CHANGELOG.md, MASTER_TASK_MAP.md, IMPROVEMENT_ROADMAP.md, CAUSAL_CHAIN_COMPLETENESS.md
