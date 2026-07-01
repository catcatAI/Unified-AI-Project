<!--
  =============================================================================
  FILE_HASH: 46E0CB0D
  FILE_PATH: agents.md
  FILE_TYPE: documentation
  PURPOSE: Agent 开发指南 - 包含构建、测试、代码规范等命令说明
  VERSION: 7.5.0-dev
  STATUS: active
  LANGUAGE: en
  LAST_MODIFIED: 2026-06-28
  AUDIENCE: developers, agents
  =============================================================================
-->

# Agent Guidelines for Angela AI

## ASI Engineering Standards (Mandatory)

1. **Surgical Precision**: Repairs and updates must be strictly limited to the target code. Do not modify unrelated logic, formatting, or comments.
2. **Incremental Only**: Avoid `write_file` for established core files. Use `replace` for surgical edits.
3. **Zero Pruning**: Never use placeholders like "rest of code" or "omitted". Full context must be maintained in documentation updates.
4. **No Placeholders**: `pass` or `random` logic is forbidden in completed tasks.
5. **Matrix Alignment**: All new code must be annotated according to the Angela Matrix (L1-L6, αβγδ, A/B/C, L0-L11).

## Angela Matrix Annotation

Refer to `@ANGELA_MATRIX_ANNOTATION_GUIDE.md` for detailed rules.

### Python Annotation Template
```python
# =============================================================================
# ANGELA-MATRIX: [L1-L6] [αβγδ] [A/B/C] [L0-L11]
# =============================================================================
```

### JavaScript Annotation Template
```javascript
/**
 * =============================================================================
 * ANGELA-MATRIX: [L1-L6] [αβγδ] [A/B/C] [L0-L11]
 * =============================================================================
 */
```

## Build/Lint/Test Commands

### Python (Backend)

```bash
# Run all tests (multiple test directories)
pytest tests/ apps/backend/tests/

# Run single test file
pytest tests/path/to/test_file.py
pytest apps/backend/tests/path/to/test_file.py

# Run single test function
pytest tests/path/to/test_file.py::test_function_name

# Run single test class
pytest tests/path/to/test_file.py::TestClassName

# Run with coverage
pytest --cov=apps/backend/src --cov-report=html

# Linting & Formatting
flake8 apps/backend/src tests/           # Lint check
black apps/backend/src tests/            # Format code
isort apps/backend/src tests/            # Sort imports
mypy apps/backend/src                    # Type check

# Run all checks (pre-commit)
pre-commit run --all-files
```

> ✅ **NOTE (Updated 2026-06-29)**: Extended session now **158+ commits** (Jun 25–29). Includes §X #34-#54: save_visual_decoder_weights, TemporalState↔CausalReasoningEngine bridge, U5 security, all stub eliminations (R1-R3, §X #27), T1-T5 training DONE, 5 real stub modules (§X #49), ripple/node+influence/space stubs (§X #50), magic number migration (§X #51), test_final.py fix (§X #52), 4 Level5ASI STUB→real modules (§X #53), formula coefficient migration (§X #54). **All stubs eliminated** (0 stubs). **5,085 tests collected** (full testpaths), 4,578 (tests/), 0 errors.
> 

> ✅ **NOTE (Updated 2026-07-01)**: **§X #83**: MetaController C³ 4.0 — closed-loop calibration history → adjustment multiplier. **§X #84**: ExecutionGate C³ 5.0 — execution result feedback loop (record_result → dynamic threshold). 11 new tests (59 total). **4,712 tests collected (tests/) — 0 errors.**
> - **Phase A1-A4**: External dictionary download + convert + import pipeline
> - **New scripts**: `scripts/download_datasets.py` (CC-CEDICT/JMdict/WordNet), `scripts/import_dictionaries.py`
> - **460,281 entries** imported: 125k CC-CEDICT (zh↔en) + 217k JMdict (ja↔en) + 117k WordNet 3.0 (en)
> - **Data volume**: 132MB JSON (35.8+57.7+38.8MB) — 110MB → 242MB total growth
> - **Performance fix**: `_dirty` flag in `dictionary_layer.py` prevents redundant index rebuilds; `encode_soft` uses keyword/bigram index for candidate filtering instead of full O(n) scan — query speed improved 60-1000x
> - **DictionaryLayer**: `bulk_add_entries()` method, `max_entries` default increased to 500000
> - **Phase C (GARDEN numpy backend)**: SNN dual backend (torch or numpy) — no hard torch dependency. Cross-platform: CPU/GPU, Win/Linux/macOS. 201 GARDEN tests pass.
> - **Phase D (ED3N Engine强化)**: `ContinuousLearningPipeline` wired into `ED3NEngine` (optional), `learn_reflex()` method, save/load CL state, `__init__.py` exports.
> - **Cross-platform fixes**: `apps/backend/src/ai/ed3n/multimodal/image_encoder.py` ImportError handler, `apps/backend/src/core/managers/execution_monitor.py` SIGALRM→`_thread.interrupt_main()` on Windows, hardcoded paths fixed, `apps/backend/src/services/api/state_matrix_api.py` encoding.
> - **ED3N total**: 114 tests — all pass (5.29s, was 14.20s)
> - **Non-ML total**: 315 tests — all pass (4:13, was 5:00/8:48)
> - **Zero new external dependencies** — everything uses stdlib + existing project modules
> - **Phase 3.3 (Vector store persistence)**: Dual-backend (chromadb/numpy+JSON) `VectorMemoryStore`. Auto-detects chromadb; falls back to pure numpy + JSON for cross-platform zero-dep persistence. `VECTOR_STORE_PATH` env var controls storage dir (default `data/vector_store/`). 25 tests pass. `ham_utils.py` stubs → real implementations (cosine similarity, embedding, uuid, timestamp).
> - **HAM wiring fix**: `ham_vector_store_manager.py` now has `embed_text()` / `query_similar()` methods (were missing → semantic search was dead code). End-to-end numpy backend: embed → store → search → persist → reload verified.
> 
> ✅ **NOTE (Updated 2026-06-29)**: Extended session continues — 158+ commits (Jun 25-29). §X #49-54 all DONE:
> - **§X #49**: 5 real stub modules (precision_projection_matrix, resonance, cognitive_pipeline, attractor_field, negativity) — +70 tests
> - **§X #50**: 2 more stubs (ripple/node, influence/space) — +10 tests
> - **§X #51**: 11 magic numbers migrated to config-driven accessors
> - **§X #52**: test_final.py StateConfig API mismatch fixed
> - **§X #53**: 4 Level5ASI STUB classes → real modules (distributed_coordinator, hyperlinked_parameter_cluster, aligned_base_agent, HSPMessageEnvelope)
> - **§X #54**: ~35-40 formula coefficients migrated (P9-3: ~0 formula coefficients remain)
> - **T5 DONE**: ThreeLayerVisual automatic PCA training — 21 new tests (multimodal: 139→160)
> - **0 docstring-only stubs remain** in source code
> - **0 STUB markers** in source code
> - **5,085 tests (full)** / **4,578 tests (tests/)** — 0 collection errors
> - §0.5 banned: 2 remaining (Frontend Live2D, Frontend Dashboard)
> - Architecture: ~85-90%
>

### JavaScript/TypeScript

```bash
# Linting
pnpm lint:js                             # ESLint check
pnpm format:js                           # Prettier format

# Single file formatting
prettier --write "path/to/file.js"
```

### Full Project

```bash
pnpm lint                                # All linting
pnpm format                              # All formatting
pnpm test                                # All tests
pnpm check                               # Pre-commit checks
```

## Code Style Guidelines

### Python

- **Line length**: 100 characters
- **Formatter**: Black with isort for imports
- **Type hints**: Use for function signatures; mypy checks enabled
- **Naming**:
  - Classes: `PascalCase`
  - Functions/variables: `snake_case`
  - Constants: `UPPER_SNAKE_CASE`
  - Private: `_leading_underscore`

### Import Order

```python
# 1. Standard library
import os
from typing import List

# 2. Third-party
import numpy as np
from fastapi import FastAPI

# 3. First-party (project) — adjust path based on working directory
from apps.backend.src.core import utils
from apps.backend.src.ai.memory.ham_memory.ham_manager import HAMMemoryManager
```

### Error Handling

```python
# Use custom AngelaError hierarchy
from apps.backend.src.core.angela_error import AngelaError, ConfigurationError

try:
    result = risky_operation()
except ConfigurationError as e:
    logger.error(f"Config error: {e}")
    raise
except Exception as e:
    logger.exception(f"Unexpected error: {e}")
    raise AngelaError(f"Operation failed: {e}") from e
```

### JavaScript

- **Line length**: 100 characters
- **Quotes**: Single quotes
- **Semicolons**: Yes (enforced by Prettier)
- **Naming**:
  - Classes: `PascalCase`
  - Functions/variables: `camelCase`
  - Constants: `UPPER_SNAKE_CASE`

### Error Handling (JS)

```javascript
try {
  const result = await riskyOperation()
} catch (error) {
  logger.error('Operation failed:', error)
  throw new Error(`Operation failed: ${error.message}`)
}
```

## Testing Guidelines

- Tests in `tests/` directory
- Naming: `test_*.py` for files, `test_*` for functions
- Coverage target: >80%
- Markers: `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.slow`

## Version Governance Rules

1. **No AI self-assigned MAJOR versions**: Any version bump to MAJOR or MINOR must be explicitly approved by a human. AI agents may increment PATCH only.
2. **CHANGELOG must match real versions**: Every CHANGELOG entry must correspond to a real git tag or source code version change. Fictional/unreleased versions must be marked `Internal/Unreleased`.
3. **All 14 version locations must stay in sync**: Before any commit that changes `package.json` version, run a consistency check across all version files. See `docs/06-project-management/plans/MASTER_CONSOLIDATED_PLAN.md` for the full file list.
4. **No bare "Fix and update" commits**: Every commit that touches a version field must explain WHY in the commit message body.

## Git Workflow

```bash
# Before commit - run checks
pnpm check

# Or manually
black apps/backend/src tests/ && flake8 apps/backend/src tests/
```

## Key Project Structure

```
apps/
  backend/           # Python FastAPI + AI systems (612 Python files, ~96K lines)
    ai/core/         # QueryClassifier, ExecutionGate, ModelBus, unicode_utils
    ai/ed3n/         # ED3N engine (reflex → SNN → decode → cycle)
    ai/garden/       # GARDEN lightweight inference engine
    ai/context/      # Context management (dialogue, memory)
    ai/lifecycle/    # Memory integration cycle, active interaction
    ai/response/     # Response composition, learning loop
    ai/meta/         # Meta-learning, adaptive control
    ai/reasoning/    # Causal reasoning
    ai/alignment/    # Emotion system, ontology system
    ai/memory/       # HAM memory, vector store
    ai/agents/       # Dynamic agent registration
    ai/multimodal/primitives/  # Compositional image gen (GVV: 14 source files, ~62 tests)
    services/        # LLM routing, chat service, handlers
    api/routes/      # FastAPI routes (v1/*)
  desktop-app/       # Electron + Live2D desktop app (7 unique JS files + 33 shared)
  web-live2d-viewer/ # Web-based Live2D model viewer (10 unique JS files + 33 shared)
  pixel-angela/      # PyQt6 pixel art rendering engine
  gemini-os-bridge/  # OS automation microservice
packages/
  shared-js/         # Shared JS package (33 JS files, platform detection)
  cli/               # CLI tools
tests/
  ai/garden/         # GARDEN 測試 (125 tests)
  ai/multimodal/primitives/  # Primitives tests (38 tests, NEW)
  ai/                # ED3N/Lifecycle/Meta 測試 (37+ tests)
```

## Technology Stack

- **Python**: 3.10+ with FastAPI, pytest, Black, isort, flake8, mypy
- **JavaScript**: ES6+ with Electron, ESLint, Prettier
- **Package Manager**: pnpm (monorepo)
- **Pre-commit**: Automated linting/formatting

## Quick Commands Reference

| Task          | Command                              |
| ------------- | ------------------------------------ |
| Dev server (backend) | `pnpm dev:backend`               |
| Dev server (desktop) | `pnpm dev:desktop`               |
| All dev servers | `pnpm dev:all`                      |
| Single test   | `pytest tests/path.py::test_func -v` |
| Format Python | `black apps/backend/src tests/`      |
| Format JS     | `prettier --write "**/*.js"`         |
| Type check    | `mypy apps/backend/src`              |
| Lint all      | `pnpm lint`                          |
| Run all tests | `pnpm test`                          |
