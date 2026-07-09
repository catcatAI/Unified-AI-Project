# Test System

## Overview

This directory contains the Unified AI Project test suite. Tests are organized by domain.
**4,387 tests collected** (as of 2026-07-09).

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

## CI / Pre-Commit

Before committing, run:

```bash
black apps/backend/src tests/
flake8 apps/backend/src tests/
pytest tests/ --timeout=30 --timeout_method=thread -q
```

Test counts are tracked in: AGENTS.md, CHANGELOG.md, MASTER_TASK_MAP.md, IMPROVEMENT_ROADMAP.md, CAUSAL_CHAIN_COMPLETENESS.md
