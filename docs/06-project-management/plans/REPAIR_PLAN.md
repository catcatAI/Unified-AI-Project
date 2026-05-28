# 综合修复计划 Unified Repair Plan

**项目版本:** 7.5.0-dev  
**创建日期:** 2026-05-28  
**状态:** Phase 0/1 Active (63% complete)  
**负责人:** Agent  
**最后更新:** 2026-05-28  

---

## 目录

1. [范围与目标 Scope & Objectives](#1-范围与目标)
2. [依赖关系 Dependency Graph](#2-依赖关系)
3. [Phase 0 — 即时安全修复 Immediate Safety](#3-phase-0--即时安全修复-immediate-safety)
4. [Phase 1 — 关键运行时修复 Critical Runtime](#4-phase-1--关键运行时修复-critical-runtime)
5. [Phase 2 — 高优先级 High Priority](#5-phase-2--高优先级-high-priority)
6. [Phase 3 — 中优先级 Medium Priority](#6-phase-3--中优先级-medium-priority)
7. [Phase 4 — 低优先级 Low Priority](#7-phase-4--低优先级-low-priority)
8. [验收标准 Acceptance Criteria](#8-验收标准)
9. [附录 Appendix](#9-附录)

---

## 1. 范围与目标

### 1.1 总工作量估计

| Phase | Effort (person-hours) | Risk Level | Dependencies |
|-------|----------------------|------------|--------------|
| Phase 0 | 4–6 | Critical | None |
| Phase 1 | 40–60 | High | Phase 0 |
| Phase 2 | 24–36 | Medium | Phase 1 |
| Phase 3 | 32–48 | Low | Phase 2 |
| Phase 4 | 16–24 | Low | Phase 3 |
| **Total** | **116–174** | — | — |

### 1.2 修复原则

1. **Surgical precision** — fix only the broken line, not surrounding code
2. **No placeholders** — every replacement must be complete, valid code
3. **No AI self-assigned MAJOR/MINOR version bumps** — PATCH only
4. **All 13 version locations must stay in sync**
5. **Every commit must explain WHY in the body**

---

## 2. 依赖关系

```
Phase 0 (Secrets/Safety)
  │
  ▼
Phase 1 (Runtime: imports, eval, mypy)
  │
  ▼
Phase 2 (Deprecated APIs, hardcoded paths, print→log)
  │
  ▼
Phase 3 (Lint, complexity, coverage, config dedup)
  │
  ▼
Phase 4 (Dead code, version strings, orphaned files)
```

- Phase 1 depends on Phase 0 because secret rotation must precede CI execution
- Phase 2 depends on Phase 1 because import fixes unlock correct `mypy`/`flake8` runs
- Phase 3 depends on Phase 2 because lint runs will be noisy until Phase 2 is done
- Phase 4 depends on Phase 3 to ensure coverage metrics are real before pruning

---

## 3. Phase 0 — 即时安全修复 Immediate Safety

**Effort:** 4–6 person-hours | **Risk:** Critical | **Dependencies:** None

### 3.1 轮换硬编码密钥 Rotate Hardcoded Secrets

| # | File | Finding | Fix |
|---|------|---------|-----|
| P0-1 | `.env` | Real `GEMINI_API_KEY` and `OLLAMA_API_KEY` on disk | Rotate both keys immediately; replace `.env` with `.env.template` using placeholder values |
| P0-2 | `credentials.json` | Real Google OAuth credentials | Remove file from repo; add to `.gitignore`; store in vault/CI secrets |
| P0-3 | `apps/backend/src/core/security/encryption.py` | Source may contain test keys | Audit and replace any hardcoded keys with env var lookups |

### 3.2 文件上传路径遍历 File Upload Path Traversal

| # | File | Lines | Finding | Fix |
|---|------|-------|---------|-----|
| P0-4 | `apps/backend/src/api/v1/endpoints/drive.py` | 382–395 | `upload_file` accepts user-supplied `file_path` parameter — opens arbitrary local files and uploads them to Google Drive. Data exfiltration vector. | Remove the `file_path` parameter; only accept uploaded file objects from the request. Validate path is within a sandboxed temp directory. Add path traversal sanitization (`os.path.realpath` + prefix check). |

### 3.3 Drive Endpoint Lockdown

| # | File | Lines | Finding | Fix |
|---|------|-------|---------|-----|
| P0-5 | `apps/backend/src/api/v1/endpoints/drive.py` | 382–395 | Same HIGH-severity issue | Add authentication guard; require `current_user` dependency; add rate-limiting |

### 3.4 权限控制激活 Activate Auth Middleware

| # | File | Finding | Fix |
|---|------|---------|-----|
| P0-6 | `apps/backend/src/api/v1/endpoints/*.py` | No auth middleware wired on routes | Wire `auth_middleware.py` as a FastAPI `dependencies=[Depends(get_current_user)]` on every router |
| P0-7 | `apps/backend/src/core/middleware/auth_middleware.py` | Exists but unused | Verify it works; add to app lifespan |

### 3.5 SECURITY.md 补充 Security Policy

| # | File | Fix |
|---|------|-----|
| P0-8 | `SECURITY.md` (create if missing) | Add coordinated disclosure process and PGP key for security reports |

---

## 4. Phase 1 — 关键运行时修复 Critical Runtime

**Effort:** 40–60 person-hours | **Risk:** High | **Dependencies:** Phase 0

### 4.1 修复 13 个测试文件中的错误导入 Fix Import Errors in 13 Test Files

Replace `core.autonomous.state_matrix_adapter` → `core.engine.state_matrix_adapter` in these files:

| # | File |
|---|------|
| P1-1 | `tests/core/test_port_routing_e2e.py` |
| P1-2 | `tests/core/test_state_matrix_integrations.py` |
| P1-3 | `tests/core/test_audit_comprehensive.py` |
| P1-4 | `tests/core/test_smoke_real.py` |
| P1-5 | `tests/core/test_phase7.py` |
| P1-6 | `tests/core/test_llm_e2e.py` |
| P1-7 | `tests/core/test_persistence.py` |
| P1-8 | `tests/core/test_self_introspector_v2.py` |
| P1-9 | `tests/core/test_axis_port_registry.py` |
| P1-10 | `tests/core/autonomous/test_state_matrix_adapter.py` |
| P1-11 | `tests/core/interfaces/test_state_persistence.py` |
| P1-12 | `tests/ai/test_code_inspector_integration.py` |

### 4.2 修复 11 个源文件中的 from src. 导入 Fix from src. Imports

Replace `from src.X.Y import Z` → `from X.Y import Z` in:

| # | File | Pattern |
|---|------|---------|
| P1-13 | `apps/backend/src/ai/alignment/decision_theory_system.py` | `from src.core...` |
| P1-14 | `apps/backend/src/ai/agents/specialized/planning_agent.py` | `from src...` |
| P1-15 | `apps/backend/src/ai/execution/execution_manager.py` | `from src...` |
| P1-16 | `apps/backend/src/ai/memory/ham_memory_manager.py` | `from src...` |
| P1-17 | `apps/backend/src/ai/memory/ham_utils.py` | `from src...` |
| P1-18 | `apps/backend/src/core/utils.py` | `from src...` |
| P1-19 | `apps/backend/src/integrations/atlassian_bridge.py` | `from src...` |
| P1-20 | `apps/backend/src/services/chat_service.py` | `from src...` |
| P1-21 | `apps/backend/src/services/llm/router.py` | `from src...` |
| P1-22 | `apps/backend/src/services/llm/__init__.py` | `from src...` |
| P1-23 | `apps/backend/src/services/security/bootstrap_manager.py` | `from bootstrap_manager import...` |

**Fix:** `sed -i 's/from src\./from /g'` across each file. Verify by running `pytest --import-mode=importlib`.

### 4.3 修复 2 个测试文件中的 core_ai / tools/ 引用 Fix core_ai / tools/ Refs

| # | File | Fix |
|---|------|-----|
| P1-24 | `tests/scripts/test_final_comprehensive.py` | Replace `core_ai` → `core.ai`; replace `tools/` → `apps/backend/src/tools/` or remove if non-existent |

### 4.4 修复 F821 未定义名称错误 Fix 173 F821 Undefined Names

Priority files with bulk undeclared symbols:

| # | File | Missing Symbols | Fix |
|---|------|----------------|-----|
| P1-25 | `apps/backend/src/services/llm/router.py` | ~20 missing refs (logger, Request, etc.) | Add `from loguru import logger`; add proper type imports |
| P1-26 | `apps/backend/src/core/utils.py` | `logger` | Add `from loguru import logger` |
| P1-27 | `apps/backend/src/ai/execution/execution_manager.py` | `logger` | Add `from loguru import logger` |
| P1-28 | `apps/backend/src/ai/memory/ham_utils.py` | `numpy`, `np` | Add `import numpy as np` |
| P1-29 | `apps/backend/src/core/security/encryption.py` | `hmac` | Add `import hmac` |
| P1-30 | `apps/backend/src/core/security/bootstrap_manager.py` | `datetime` | Add `from datetime import datetime` |
| P1-31 | `apps/backend/src/integrations/atlassian_bridge.py` | `datetime` | Add `from datetime import datetime` |
| P1-32 | `apps/backend/src/ai/alignment/decision_theory_system.py` | `datetime` | Add `from datetime import datetime` |
| P1-33 | `apps/backend/src/services/chat_service.py` | `user_name` | Add proper parameter or global declaration |

**Process:** Run `mypy apps/backend/src --ignore-missing-imports --show-error-codes 2>&1 | grep "F821"` to generate full list; fix each with surgical `edit` calls. Re-run mypy until F821 count is 0.

### 4.5 修复 SyntaxError in lightweight_code_model.py

| # | File | Line | Finding | Fix |
|---|------|------|---------|-----|
| P1-34 | `apps/backend/src/ai/intelligence/lightweight_code_model.py` | 185 | Unterminated f-string blocks all mypy execution | Replace `f"some string with missing closing brace` → properly terminated f-string with `}}` escape or correct expression |

### 4.6 修复 mypy 版本配置 Fix mypy python_version

| # | File | Finding | Fix |
|---|------|---------|-----|
| P1-35 | `pyproject.toml` or `mypy.ini` | `python_version = "3.8"` incompatible with mypy 2.0 | Change to `python_version = "3.10"` (minimum supported by project deps) |

### 4.7 替换 4 个裸 eval() 调用 Replace 4 Bare eval() Calls

| # | File | Line | Fix |
|---|------|------|-----|
| P1-36 | `apps/backend/src/ai/verification/math_verifier.py` | 302 | Replace with `safe_eval()` from `core.security.secure_eval` |
| P1-37 | `apps/backend/src/ai/utils/logic_unit.py` | 352 | Same |
| P1-38 | `apps/backend/src/core/engineering/eta_axis.py` | 217 | Same |
| P1-39 | `apps/backend/src/ai/intelligence/math_ripple_engine.py` | 709 | Same |

### 4.8 Electron 安全修复 Electron Security Fixes

| # | File | Lines | Finding | Fix |
|---|------|-------|---------|-----|
| P1-40 | `apps/desktop-app/main.js` | 1354–1371 | `executeJavaScript` bypasses `contextIsolation` | Remove `executeJavaScript` calls; use `ipcMain.handle` + `contextBridge` instead |
| P1-41 | `apps/desktop-app/main.js` | 584 | `openDevTools()` runs unconditionally | Guard with `if (!app.isPackaged)` |
| P1-42 | `apps/desktop-app/main.js` | 349 | `--remote-debugging-port=9222` always exposed | Remove in production builds; conditionally add only when `--debug` flag passed |
| P1-43 | `apps/desktop-app/index.html` | — | No Content-Security-Policy meta tag | Add `<meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'">` |

### 4.9 修复 55 个测试文件中的 sys.path 篡改 Remove sys.path Manipulation

| # | Finding | Fix |
|---|---------|-----|
| P1-44 | ~55 test files call `sys.path.insert(0, ...)` | Convert to conftest.py-based path setup; use `--rootdir` and `--import-mode=importlib` in `pyproject.toml` |

**Process:** Run `rg "sys\.path" tests/ --files-with-matches` to get full list. Add a `conftest.py` at `tests/` level with proper path setup, then remove `sys.path` lines from individual test files.

### 4.10 修复 13 个 1 行冒烟测试文件 Fix 13 Single-Line Smoke Tests

| # | Finding | Fix |
|---|---------|-----|
| P1-45 | 13 test files crammed onto 1 line, unparseable by AST | Split each into valid multi-line Python with proper `def test_*():` structure |

---

## 5. Phase 2 — 高优先级 High Priority

**Effort:** 24–36 person-hours | **Risk:** Medium | **Dependencies:** Phase 1

### 5.1 替换所有 print() 为日志 Replace 160+ print() with Logging

| # | File | Approx Count | Fix |
|---|------|-------------|-----|
| P2-1 | `apps/backend/src/core/config_validator.py` | 285–320: many print() | Replace each with `logger.info()` |
| P2-2 | `apps/backend/src/core/system_monitor.py` | Multiple | Replace with `logger.*()` |
| P2-3 | `apps/backend/src/core/performance_optimizer.py` | Multiple | Replace with `logger.*()` |
| P2-4 | `apps/backend/src/services/real_time_monitor.py` | Multiple | Replace with `logger.*()` |

**Process:** Run `rg "print\(" apps/backend/src/ --include "*.py" -n` to get full list. Add `from loguru import logger` where missing; replace each print with appropriate log level.

### 5.2 修复 F541 f-string without placeholders (78 instances)

| # | Key Files | Count | Fix |
|---|-----------|-------|-----|
| P2-5 | `life_intensity_formula.py` | 6 | Replace `f"string"` → `"string"` |
| P2-6 | `non_paradox_existence.py` | 5 | Same |
| P2-7 | `demo_feedback_loop.py` | 6 | Same |
| P2-8 | `hal.py` | 4 | Same |
| P2-9 | `live2d_avatar_generator.py` | 4 | Same |

**Process:** Run `ruff check --select=F541` to get full list; bulk-fix with `ruff check --select=F541 --fix`.

### 5.3 移除硬编码路径 Remove Hardcoded Paths

| # | Finding | Fix |
|---|---------|-----|
| P2-10 | 50+ `/home/cat/桌面/` paths across tests/scripts/, apps/desktop-app/test_desktop_app.py, scripts/ | Replace with `pathlib.Path.home() / "Desktop"` or configurable env vars |
| P2-11 | `frontend-utils.js:91` — `/home/cat/桌面/...` | Same |
| P2-12 | `angela-character-config.js:166` — hardcoded user path | Same |
| P2-13 | 68 hardcoded Linux paths in test files (`/home/cat/桌面/`, `/tmp/`) | Replace with `tmp_path` fixture or `pathlib.Path` |

### 5.4 移除 857 console.log Replace console.log with Logger

| # | File | Fix |
|---|------|-----|
| P2-14 | All `*.js` in `apps/desktop-app/` | Replace console.log with structured logger (electron-log or winston) |

**Process:** Run `rg "console\.(log|warn|error)" apps/desktop-app/ --include "*.js" -n` for full list.

### 5.5 替换弃用 API Replace Deprecated APIs

| # | API | Files | Fix |
|---|-----|-------|-----|
| P2-15 | `datetime.utcnow()` | ~20 files | Replace with `datetime.now(tz=timezone.utc)` |
| P2-16 | `asyncio.get_event_loop()` | 11 files | Replace with `asyncio.get_running_loop()` or `asyncio.new_event_loop()` |
| P2-17 | `asyncio.ensure_future()` | 1 file | Replace with `asyncio.create_task()` |
| P2-18 | `asyncio.coroutine` type hint | 1 file | Replace with `Coroutine` type from `typing` |

### 5.6 修复 Plugin Manager 中的 new Function()

| # | File | Finding | Fix |
|---|------|---------|-----|
| P2-19 | `apps/backend/src/core/plugin_manager.py` (or similar) | Uses `new Function()` — eval-like risk | Replace with sandboxed `vm` module or pre-registered plugin registry |

### 5.7 锁定 requirements.txt Pin requirements.txt Versions

| # | File | Finding | Fix |
|---|------|---------|-----|
| P2-20 | `requirements.txt` | No version pins — supply chain risk | Add `>=` minimum versions for all deps based on current lockfile |

---

## 6. Phase 3 — 中优先级 Medium Priority

**Effort:** 32–48 person-hours | **Risk:** Low | **Dependencies:** Phase 2

### 6.1 修复 101 个 C901 圈复杂度违规 Fix Cyclomatic Complexity

| # | Finding | Fix |
|---|---------|-----|
| P3-1 | 101 functions exceed C901 threshold | Refactor each into smaller functions; extract branches into helper methods |

**Process:** Run `flake8 --max-complexity=10 apps/backend/src/ --select=C901` to get full list. Tackle top-10 highest complexity first.

### 6.2 修复 115 个 E402 导入位置违规 Fix E402 Import Not at Top

| # | Finding | Fix |
|---|---------|-----|
| P3-2 | 115 imports not at top of file | Move to top unless truly conditional (lazy imports). Where lazy import is intentional (circular dep), add `# noqa: E402` |

### 6.3 修复 112 个 F841 未使用变量 Fix F841 Unused Variables

| # | Finding | Fix |
|---|---------|-----|
| P3-3 | 112 unused local variables | Remove or prefix with `_` |

**Process:** Run `ruff check --select=F841 --fix` for auto-fixable instances; manual review for pattern-breaking ones.

### 6.4 修复 28 个 # type: ignore 注释 Fix type: ignore Comments

| # | Finding | Fix |
|---|---------|-----|
| P3-4 | `# type: ignore` used instead of fixing type errors | For each, fix the underlying typing issue or add proper type stubs |

### 6.5 合并重复的 pytest 配置 Consolidate pytest Config

| # | Files | Finding | Fix |
|---|-------|---------|-----|
| P3-5 | `pyproject.toml` + `apps/backend/pytest.ini` + `configs/pytest.ini` | Three competing pytest config files | Consolidate into `pyproject.toml`; delete the other two |

### 6.6 修复 --cov-fail-under=1

| # | File | Finding | Fix |
|---|------|---------|-----|
| P3-6 | `pyproject.toml` | `--cov-fail-under=1` effectively disables coverage enforcement | Raise to `--cov-fail-under=50` (minimum viable) after Phase 1 and Phase 2 |

### 6.7 合并两个 package.json Diverging Dependencies

| # | Finding | Fix |
|---|---------|-----|
| P3-7 | Root `package.json` and `apps/desktop-app/package.json` have diverging ws versions | Align ws version; use `pnpm` workspace protocol for shared deps |

### 6.8 删除无效 Linux 构建目标 Remove Invalid Appx Target

| # | File | Finding | Fix |
|---|------|---------|-----|
| P3-8 | `apps/desktop-app/electron-builder.yml` or `package.json` | Appx (Windows Store) target in Linux build config | Remove `Appx` target; keep `snap`, `AppImage`, `deb` |

### 6.9 合并重复共享代码 Deduplicate Shared Code

| # | Duplicate Pairs | Fix |
|---|----------------|-----|
| P3-9 | `src/shared/error.py` vs `src/core/shared/error.py` | Keep one; alias with import in the other location |
| P3-10 | `src/shared/key_manager.py` vs `src/core/shared/key_manager.py` | Same |
| P3-11 | `src/shared/utils/` vs `src/core/shared/utils/` | Same |

### 6.10 添加 ESLint for desktop-app

| # | Finding | Fix |
|---|---------|-----|
| P3-12 | No ESLint configured for `apps/desktop-app/` | Add `.eslintrc.js` with `eslint:recommended` + `electron` plugin |

### 6.11 修复 Windows 不兼容 Fix Windows Incompatibilities

| # | File | Finding | Fix |
|---|------|---------|-----|
| P3-13 | `apps/backend/src/services/execution_monitor.py` | `signal.SIGALRM` doesn't exist on Windows | Add `try/except AttributeError` fallback using `threading.Timer` |
| P3-14 | `apps/backend/src/core/security/key_manager.py` | `os.chmod()` with no Windows fallback | Check `sys.platform == "win32"` or use `os.stat()` with `FILE_ATTRIBUTE_*` |
| P3-15 | `apps/backend/src/core/desktop_interaction.py` | Same | Same fix |
| P3-16 | Various files | `USERPROFILE` instead of `pathlib.Path.home()` | Replace with `Path.home()` |

### 6.12 修复缺少的 __init__.py

| # | Path | Fix |
|---|------|-----|
| P3-17 | `apps/backend/src/core/system/` | Add `__init__.py` if subpackages are imported as `from core.system.*` |

---

## 7. Phase 4 — 低优先级 Low Priority

**Effort:** 16–24 person-hours | **Risk:** Low | **Dependencies:** Phase 3

### 7.1 同步版本字符串 Sync Version Strings

| # | Finding | Fix |
|---|---------|-----|
| P4-1 | ~100+ files say `v6.x` when project is `7.5.0-dev` | Run version consistency script; update all `__version__`, `version` fields, and doc headers |

### 7.2 修复 desktop-app 版本 Mismatched desktop-app Version

| # | File | Finding | Fix |
|---|------|---------|-----|
| P4-2 | `apps/desktop-app/package.json` | `version: "4.1.0-dev"` vs main project `7.5.0-dev` | Align or document intentional decoupling |

### 7.3 移除死代码 Remove Dead Code

| # | Finding | Fix |
|---|---------|-----|
| P4-3 | `src/agents/` (5 files) — never imported | Archive or delete |
| P4-4 | `ai/agents/specialized/planning_agent.py` — zero references | Archive or delete |
| P4-5 | `archive/` (98 unreferenced Python files) | Remove from `archive/` (that's what git is for); or create a proper `legacy/` index |
| P4-6 | `core/autonomous/` standalone scripts — not in test suite | Either add tests or remove |
| P4-7 | `core/tests/` (1945 lines) — wrong directory | Move to `tests/core/` |

### 7.4 移除 144+ 注释代码块 Remove 144+ Commented-Out Code Blocks

| # | Finding | Fix |
|---|---------|-----|
| P4-8 | ~30 files with commented-out code blocks | Remove all commented-out code (use git history for reference) |

### 7.5 修复 .flake8 / pyproject.toml 配置漂移 Fix Config Drift

| # | Finding | Fix |
|---|---------|-----|
| P4-9 | Both `.flake8` and `pyproject.toml` configure flake8 | Consolidate into `pyproject.toml`; delete `.flake8` |

### 7.6 清理 225+ 未测试模块 Address 225+ Untested Modules

| # | Finding | Fix |
|---|---------|-----|
| P4-10 | 225+ source modules >50 lines with no tests | Add at least smoke/import test for each; prioritize based on call frequency |

---

## 8. 验收标准

| Phase | Gate | Command |
|-------|------|---------|
| Phase 0 | No secrets on disk | `rg -i "(api.?key|secret|password|credentials)" --include "*.{py,js,json,txt,env}" --no-ignore` — verify only `.env.template` matches |
| Phase 0 | Path traversal impossible | Review `drive.py` upload endpoint |
| Phase 1 | All 13 broken tests pass | `pytest tests/core/test_port_routing_e2e.py tests/core/test_state_matrix_integrations.py ... -x` |
| Phase 1 | `mypy apps/backend/src` passes with 0 errors | `mypy apps/backend/src` |
| Phase 1 | No F821 errors | `ruff check --select=F821 apps/backend/src/` |
| Phase 1 | No eval() in source | `rg "\beval\(" apps/backend/src/ --include "*.py"` — only matches in `secure_eval.py` |
| Phase 2 | No F541 errors | `ruff check --select=F541 apps/backend/src/` |
| Phase 2 | No deprecated API calls | `rg "utcnow|get_event_loop|ensure_future|asyncio\.coroutine" apps/backend/src/` |
| Phase 3 | C901 count < 50 | `flake8 --max-complexity=10 apps/backend/src/ --select=C901 | wc -l` |
| Phase 3 | E402 count < 20 | `ruff check --select=E402 apps/backend/src/` |
| Phase 3 | F841 count < 10 | `ruff check --select=F841 apps/backend/src/` |
| Phase 4 | All version strings match | Custom script comparing `__version__` across files |
| All | `pnpm check` passes | `pnpm check` (lint + format + test + type-check) |

---

## 9. 附录

### 9.1 使用工具建议 Tooling Recommendations

| Task | Tool |
|------|------|
| Bulk find-and-replace imports | `ruff check --fix --select=F821` or `sed` |
| Remove unused variables | `ruff check --fix --select=F841` |
| Fix f-strings | `ruff check --fix --select=F541` |
| Format code | `black apps/backend/src/` + `isort apps/backend/src/` |
| Type checking | `mypy apps/backend/src/` |
| Security audit | `bandit -r apps/backend/src/` |
| Complexity analysis | `radon cc apps/backend/src/ -s -n C` |

### 9.2 快速引用命令

```bash
# List all F821 errors
ruff check --select=F821 apps/backend/src/ 2>&1 | grep "F821"

# List all test files with sys.path manipulation
rg "sys\.path" tests/ --files-with-matches

# List all print() calls
rg -n "print\(" apps/backend/src/ --include "*.py"

# List all console.log calls
rg -n "console\.(log|warn|error)" apps/desktop-app/ --include "*.js"

# Check for deprecated APIs
rg -n "utcnow|get_event_loop|ensure_future" apps/backend/src/

# List all commented-out code blocks
rg -n "^\s*#" apps/backend/src/ --include "*.py" -c | sort -t: -k2 -rn | head -30
```
