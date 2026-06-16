<!--
  =============================================================================
  FILE_HASH: 46E0CB0D
  FILE_PATH: agents.md
  FILE_TYPE: documentation
  PURPOSE: Agent 开发指南 - 包含构建、测试、代码规范等命令说明
  VERSION: 7.5.0-dev
  STATUS: active
  LANGUAGE: en
  LAST_MODIFIED: 2026-06-06
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

> ✅ **NOTE (Updated 2026-06-08)**: All alias fixes applied. Test collection now has **0 errors** (511 tests collected). Real classes exist under different names — all 5 aliases applied:
> - `ModelProvider` → `LLMBackend` (alias added in `protocols.py`)
> - `AuditoryAttentionController` → `AttentionController` (alias added in `auditory_attention.py`)
> - `ArtLearningSystem` → `ArtLearningWorkflow` (alias added in `art_learning_system.py`)
> - `DesktopPresence` → `DesktopInteraction` (alias added in `desktop_presence.py`)
> - `Live2DIntegration` → `Live2DAvatarGenerator` (alias added in `live2d_integration.py`)
> - `MemoryNeuroplasticityBridge` → `NeuroplasticitySystem` (alias added in `memory_neuroplasticity_bridge.py`)
> 
> All 5 alias exports applied (~10 lines total). No re-implementation needed.

> ✅ **NOTE (Updated 2026-06-16)**: Phase 3-6 implementation complete. New test files added:
> - `tests/ai/garden/test_phase4_integration.py` (33 tests): ChromaDB, KG, multi-step, emotion, learning
> - `tests/ai/test_phase5_integration.py` (13 tests): Continuous learning, session persistence, memory importance, learning loop
> - `tests/ai/test_phase6_e2e.py` (24 tests): E2E pipeline, performance benchmarks
> 
> **Total new tests: 70** (33 + 13 + 24)
> 
> Existing garden tests: ~92 (test_dictionary.py, test_garden_engine.py, etc.)
> **Grand total garden tests: ~125**

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
  backend/           # Python FastAPI + AI systems
    ai/core/         # 分類器、執行閘門、ModelBus
    ai/ed3n/         # ED3N 外部字典解耦神經網路
    ai/garden/       # GARDEN 輕量推理引擎
    ai/context/      # 上下文管理（部分 stub）
    ai/lifecycle/    # 記憶整合循環、主動互動
    ai/response/     # 回應組合、學習循環
    ai/learning/     # 學習管理器、經驗回放
    ai/meta/         # 元學習、自適應控制
    ai/reasoning/    # 因果推理
    ai/ops/          # 智能運維、預測維護
    ai/alignment/    # 情緒系統、本體系統
    ai/memory/       # HAM 記憶、數學漣漪引擎
    ai/agents/       # 動態代理註冊
    services/        # LLM 路由、聊天服務、處理器
    api/routes/      # FastAPI 路由
  desktop-app/       # Electron + Live2D
  mobile-app/        # React Native bridge
packages/
  cli/               # CLI tools
tests/
  ai/garden/         # GARDEN 測試 (125 tests)
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
