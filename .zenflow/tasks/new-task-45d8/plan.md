# Full SDD workflow

## Configuration
- **Artifacts Path**: {@artifacts_path} → `.zenflow/tasks/{task_id}`

---

## Workflow Steps

### [x] Step: Requirements
<!-- chat-id: 383f2fd5-780e-4b1f-820c-dbf114a05ca3 -->

Create a Product Requirements Document (PRD) based on the feature description.

1. Review existing codebase to understand current architecture and patterns
2. Analyze the feature definition and identify unclear aspects
3. Ask the user for clarifications on aspects that significantly impact scope or user experience
4. Make reasonable decisions for minor details based on context and conventions
5. If user can't clarify, make a decision, state the assumption, and continue

Save the PRD to `{@artifacts_path}/requirements.md`.

### [x] Step: Technical Specification
<!-- chat-id: 6d47c389-590e-46a5-aff9-178c7d223369 -->

Create a technical specification based on the PRD in `{@artifacts_path}/requirements.md`.

1. Review existing codebase architecture and identify reusable components
2. Define the implementation approach

Save to `{@artifacts_path}/spec.md` with:
- Technical context (language, dependencies)
- Implementation approach referencing existing code patterns
- Source code structure changes
- Data model / API / interface changes
- Delivery phases (incremental, testable milestones)
- Verification approach using project lint/test commands

### [x] Step: Planning
<!-- chat-id: b8b33987-6663-4033-acfd-c8d46ba44cec -->

Create a detailed implementation plan based on `{@artifacts_path}/spec.md`.

1. Break down the work into concrete tasks
2. Each task should reference relevant contracts and include verification steps
3. Replace the Implementation step below with the planned tasks

Rule of thumb for step size: each step should represent a coherent unit of work (e.g., implement a component, add an API endpoint). Avoid steps that are too granular (single function) or too broad (entire feature).

Important: unit tests must be part of each implementation task, not separate tasks. Each task should implement the code and its tests together, if relevant.

If the feature is trivial and doesn't warrant full specification, update this workflow to remove unnecessary steps and explain the reasoning to the user.

Save to `{@artifacts_path}/plan.md`.

---

## Implementation Tasks

### [x] Step: Create Fix Automation Tools
<!-- chat-id: 19cdb42e-5c11-41c9-9a2e-754d600b59f6 -->

Create three automation scripts for systematic issue fixing.

**Files to create**:
- `scripts/fixes/fix_test_syntax.py` - Automated test syntax fixer
- `scripts/tools/import_profiler.py` - Import performance profiler  
- `scripts/tools/generate_secure_keys.py` - Security key generator

**Implementation**:
- `fix_test_syntax.py`: Fix patterns `try,` → `try:`, `::` → `:`, `==` → `=`, `coding, utf-8` → `coding: utf-8`
- `import_profiler.py`: Measure module import times, identify blocking operations
- `generate_secure_keys.py`: Generate A/B/C keys using `cryptography.fernet`, validate ≥32 chars

**Verification**:
```bash
# Test fix_test_syntax.py on sample files
python scripts/fixes/fix_test_syntax.py --dry-run --sample 5

# Test import profiler
python scripts/tools/import_profiler.py apps/backend/src/services/main_api_server.py

# Test key generator
python scripts/tools/generate_secure_keys.py --test
```

**Success Criteria**:
- All 3 scripts created and tested
- `fix_test_syntax.py` successfully fixes sample test files
- `import_profiler.py` reports module load times
- `generate_secure_keys.py` generates valid 32+ char keys

---

### [x] Step: Verify Development Environment
<!-- chat-id: c6a9b9e8-93fc-4db8-86fe-605fb818a237 -->

Verify all dependencies are installed and environment is ready.

**Checks**:
- Python 3.12.10 installed (requires 3.9+)
- Node.js 22.16.0 installed (requires 16+)
- pnpm 10.18.2 installed (requires 8+)
- Backend dependencies installed
- Frontend dependencies installed
- Git repository clean

**Commands**:
```bash
# Verify versions
python --version  # Should be 3.12.10
node --version    # Should be 22.16.0
pnpm --version    # Should be 10.18.2

# Install dependencies
pip install -r apps/backend/requirements.txt
cd apps/desktop-app/electron_app && pnpm install

# Check git status
git status
```

**Success Criteria**:
- All version requirements met
- All dependencies installed without errors
- Git working directory clean

---

### [x] Step: Fix Test Suite Syntax Errors (P1-1)
<!-- chat-id: d44fe75c-0c89-4eeb-a203-d4c67a575dc0 -->

Fix 238 test files with syntax errors using automated script.

**Pre-task**:
- Create git commit: "Pre-test-syntax-fixes checkpoint"
- Create backup: `tests_backup/`

**Execution**:
```bash
# Run automated fixes
python scripts/fixes/fix_test_syntax.py tests/

# Verify each file compiles
find tests/ -name "*.py" -exec python -m py_compile {} \;

# Verify test discovery works
pytest --collect-only --timeout=30
```

**Manual Review**:
- Review 24 files (10% sample) for correctness
- Document any edge cases requiring manual fixes
- Generate before/after fix report

**Verification**:
```bash
# Verify syntax
flake8 tests/ --count --select=E9,F63,F7,F82 --show-source --statistics

# Verify collection
pytest --collect-only
```

**Success Criteria**:
- ✅ 238/238 test files have valid Python syntax
- ✅ `pytest --collect-only` completes in <30 seconds
- ✅ 0 critical syntax errors in flake8 scan
- ✅ Git commit: "Fix test suite syntax errors (P1-1)"

---

### [x] Step: Profile Backend Import Performance (P1-2 Analysis)
<!-- chat-id: f78008d3-e527-4149-8753-ee8567255820 -->

Identify blocking operations in backend module initialization.

**Execution**:
```bash
# Profile current import times
python scripts/tools/import_profiler.py apps/backend/src/services/main_api_server.py

# Test current import behavior
time python -c "from apps.backend.src.services.main_api_server import app"
```

**Analysis**:
- Document slowest modules
- Identify blocking I/O operations (DB connections, model loading, file I/O)
- Create refactoring plan for top 5 slowest modules

**Deliverable**:
- Import profiling report (JSON/Markdown)
- List of modules requiring lazy loading

**Success Criteria**:
- Profiling report generated
- Blocking operations identified
- Refactoring targets documented

---

### [x] Step: Refactor Backend to Lazy Loading (P1-2 Implementation)
<!-- chat-id: e1b40178-78cc-4684-9037-e75191e90f57 -->

Refactor module initialization to eliminate blocking imports.

**Target Files** (based on profiling):
- `apps/backend/src/services/main_api_server.py`
- `apps/backend/src/core/__init__.py`
- `apps/backend/src/ai/__init__.py`
- Other modules identified in profiling

**Pattern**:
```python
# Before
model = load_large_model()  # Blocking at import time

# After  
_model = None
def get_model():
    global _model
    if _model is None:
        _model = load_large_model()
    return _model
```

**Changes**:
- Move module-level initialization to factory functions
- Apply lazy loading for AI models, DB connections, service discovery
- Remove synchronous I/O from module scope

**Verification**:
```bash
# Test import speed
time python -c "from apps.backend.src.services.main_api_server import app; print('Import successful')"
# Target: <2 seconds

# Test collection speed
time pytest --collect-only
# Target: <30 seconds

# Test backend startup
cd apps/backend && timeout 10s python -m uvicorn src.services.main_api_server:app --host 127.0.0.1 --port 8000
curl http://127.0.0.1:8000/health
```

**Success Criteria**:
- ✅ Backend import completes in <2 seconds
- ✅ `pytest --collect-only` completes in <30 seconds
- ✅ Backend starts within 10 seconds
- ✅ Health check responds successfully
- ✅ Git commit: "Fix backend import timeout issues (P1-2)"

---

### [x] Step: Fix Core AI System Errors (P1-3)
<!-- chat-id: 617f491f-c9f2-43c8-82b8-9e61342cd4f5 -->

Fix partially functional AI subsystems identified in completion report.

**Specific Fixes Required**:
1. `apps/backend/src/services/api_models.py:69` - Fix syntax/logic error
2. `apps/backend/src/services/hot_reload_service.py:11` - Fix import issue
3. `apps/backend/src/tools/tool_dispatcher.py:37` - Fix dispatcher logic

**Indentation Fixes** (~20 files):
```bash
# Format affected service files
black apps/backend/src/services/config.py
black apps/backend/src/services/ai_virtual_input_service.py
black apps/backend/src/services/audio_service.py
black apps/backend/src/services/resource_awareness_service.py
black apps/backend/src/services/vision_service.py
# ... and ~15 more files
```

**Verification**:
```bash
# Verify imports work
python -c "from apps.backend.src.services.angela_llm_service import *"
python -c "from apps.backend.src.services.audio_service import *"
python -c "from apps.backend.src.services.vision_service import *"

# Run formatting check
black apps/backend/src/services/ --check

# Run linting
flake8 apps/backend/src/services/ --count

# Run AI unit tests (if available)
pytest tests/ai/ -v
```

**Success Criteria**:
- ✅ All 3 specific errors fixed
- ✅ All ~20 indentation errors fixed
- ✅ All AI service modules import successfully
- ✅ 0 indentation errors in flake8 scan
- ✅ Backend starts without AI system errors
- ✅ Git commit: "Fix core AI system issues (P1-3)"

---

### [x] Step: Setup Environment Configuration (P2-3)
<!-- chat-id: 5e868bc5-32fa-4a94-874e-a0338571abab -->

Generate secure keys and create `.env` file for development.

**Execution**:
```bash
# Generate secure A/B/C keys
python scripts/tools/generate_secure_keys.py --output .env

# Verify configuration
python -m apps.backend.src.core.config_validator

# Test backend startup with keys
cd apps/backend && python -m uvicorn src.services.main_api_server:app --host 127.0.0.1 --port 8000
```

**Validation**:
- All keys ≥32 characters
- Keys are base64-compatible
- Keys are unique (A ≠ B ≠ C)
- No placeholder values
- `.env` file in `.gitignore`

**Documentation**:
- Document key rotation procedure
- Add security best practices to docs

**Success Criteria**:
- ✅ `.env` file created with secure keys
- ✅ All keys meet security requirements
- ✅ Backend starts successfully with keys
- ✅ Configuration validation passes
- ✅ Git commit: "Add environment configuration (P2-3)" (note: .env not committed)

---

### [ ] Step: Document Technical Debt (P2-1)

Scan and categorize all technical debt markers in codebase.

**Execution**:
```bash
# Scan for debt markers (Windows CMD syntax)
findstr /S /N /I "TODO FIXME HACK BUG" apps\backend\src\*.py > technical_debt_scan.txt
```

**Analysis**:
- Categorize by severity (Critical, High, Medium, Low)
- Categorize by module (AI, Services, Core, Tools, etc.)
- Estimate effort for each item
- Create GitHub issues for high-priority items

**Deliverable**:
- Technical debt inventory (CSV/JSON)
- GitHub issues created for Critical/High items
- Documentation for debt tracking process

**Success Criteria**:
- ✅ All 43+ debt markers documented
- ✅ High-priority items have GitHub issues
- ✅ Debt tracking process documented
- ✅ Git commit: "Document technical debt markers (P2-1)"

---

### [ ] Step: Review Deprecated Code (P2-2)

Review 3 files with deprecation warnings and create update plan.

**Files**:
1. `apps/backend/src/economy/economy_manager.py`
2. `apps/backend/src/core/hsp/versioning.py`
3. `apps/backend/src/core/hsm_formula_system.py`

**For each file**:
- Identify deprecated API usage
- Check if modern alternative exists
- Assess update feasibility (dependency constraints)
- Update code if feasible, otherwise add TODO comment
- Document deprecation status

**Deliverable**:
- Deprecation review report
- Updated code (if feasible)
- Update plan for blocked items

**Success Criteria**:
- ✅ All 3 files reviewed
- ✅ Update plan documented for each file
- ✅ Feasible updates implemented
- ✅ Git commit: "Review deprecated code (P2-2)"

---

### [ ] Step: Run Full Test Suite and Generate Coverage

Execute complete test suite and measure baseline coverage.

**Execution**:
```bash
# Run full test suite with coverage
pytest tests/ -v --cov=apps/backend/src --cov-report=html --cov-report=term

# Generate coverage report
# Report will be in htmlcov/index.html
```

**Analysis**:
- Document baseline coverage percentage
- Identify untested critical modules
- Document any test failures
- Create report of test execution metrics

**Success Criteria**:
- ✅ Test suite completes without collection errors
- ✅ Coverage report generated
- ✅ Baseline coverage documented
- ✅ Test failures documented (if any)

---

### [ ] Step: Run All Lint and Type Checks

Verify code quality across entire codebase.

**Execution**:
```bash
# Python linting
flake8 apps/backend/src tests/ --count --statistics
black apps/backend/src tests/ --check
isort apps/backend/src tests/ --check-only
mypy apps/backend/src --show-error-codes --pretty

# JavaScript linting  
cd apps/desktop-app/electron_app && pnpm lint:js
```

**Documentation**:
- Document linting results (error counts, warnings)
- Document any remaining issues
- Create plan for addressing warnings

**Success Criteria**:
- ✅ Flake8 shows 0 critical syntax errors
- ✅ Black formatting check passes (or only minor issues)
- ✅ JavaScript linting passes (or only minor warnings)
- ✅ Linting results documented

---

### [ ] Step: Verify Backend Functionality

Comprehensive backend testing and verification.

**Tests**:
1. **Startup Test**:
   ```bash
   cd apps/backend
   python -m uvicorn src.services.main_api_server:app --host 127.0.0.1 --port 8000
   # Verify startup completes in <10 seconds
   ```

2. **Health Check**:
   ```bash
   curl http://127.0.0.1:8000/health
   # Should return 200 OK
   ```

3. **WebSocket Test**:
   - Connect to `ws://127.0.0.1:8000/ws`
   - Verify connection established
   - Send test message
   - Verify response received

4. **Log Verification**:
   - Check logs for startup errors
   - Verify no import errors
   - Verify all services initialized

**Deliverable**:
- Backend functionality test report
- Startup performance metrics
- Log analysis summary

**Success Criteria**:
- ✅ Backend starts in <10 seconds
- ✅ Health endpoint responds correctly
- ✅ WebSocket connections work
- ✅ No critical errors in logs

---

### [ ] Step: Verify Desktop App Functionality

Test desktop application launch and basic functionality.

**Tests**:
1. **Installation**:
   ```bash
   cd apps/desktop-app/electron_app
   pnpm install
   ```

2. **Launch Test**:
   ```bash
   pnpm start
   # Verify window opens
   ```

3. **Functionality Checks**:
   - Verify Live2D model loads
   - Verify backend connection established
   - Test basic interactions (click, drag)
   - Check for JavaScript errors in DevTools

4. **Integration Test**:
   - Start backend first
   - Start desktop app
   - Send message from desktop
   - Verify response via WebSocket

**Deliverable**:
- Desktop app verification report
- Integration test results
- Screenshots of successful launch

**Success Criteria**:
- ✅ Desktop app launches successfully
- ✅ Live2D model loads and animates
- ✅ Backend connection established
- ✅ Basic interactions work
- ✅ No critical JavaScript errors

---

### [ ] Step: Create Implementation Summary Report

Document all work completed, metrics achieved, and remaining issues.

**Report Sections**:
1. **Executive Summary**
   - Project familiarization completed
   - Issues identified and categorized
   - P1 issues resolved status

2. **Metrics Achieved**
   - Test files fixed: 238/238
   - Backend import time: Before/After
   - Test collection time: Before/After
   - Flake8 errors: Before/After
   - AI modules importable: %

3. **Work Completed**
   - P1-1: Test suite fixes (detailed)
   - P1-2: Backend import fixes (detailed)
   - P1-3: AI system fixes (detailed)
   - P2 issues: Configuration, debt documentation, deprecated code

4. **Known Remaining Issues**
   - P3 issues deferred
   - Any P2 issues not completed
   - Any test failures found

5. **Recommendations**
   - Future work priorities
   - Process improvements
   - Technical debt roadmap

**Deliverable**:
- Implementation summary report (Markdown)
- Metrics comparison table
- Screenshots/logs as evidence

**Success Criteria**:
- ✅ Complete implementation report created
- ✅ All metrics documented with before/after values
- ✅ Remaining issues clearly documented
- ✅ Recommendations provided

---

### [ ] Step: Final Verification and Git Commit

Perform final end-to-end verification and create completion commit.

**Final Checks**:
```bash
# 1. Test suite verification
pytest --collect-only
pytest tests/unit/ -v --maxfail=5

# 2. Backend import verification
time python -c "from apps.backend.src.services.main_api_server import app"

# 3. Backend startup verification
cd apps/backend && python -m uvicorn src.services.main_api_server:app --host 127.0.0.1 --port 8000
curl http://127.0.0.1:8000/health

# 4. Linting verification
flake8 apps/backend/src tests/ --count
black apps/backend/src tests/ --check

# 5. Desktop app verification
cd apps/desktop-app/electron_app && pnpm start
```

**Documentation Updates**:
- Update README.md if needed
- Update audit reports
- Archive outdated critical issue docs (P3-1)

**Git Workflow**:
```bash
# Review all changes
git status
git diff

# Create final commit
git add .
git commit -m "Complete project familiarization and issue resolution

- Fixed 238 test files with syntax errors (P1-1)
- Refactored backend to lazy loading, import time <2s (P1-2)
- Fixed Core AI system errors and indentation issues (P1-3)
- Generated secure environment configuration (P2-3)
- Documented technical debt markers (P2-1)
- Reviewed deprecated code (P2-2)
- Verified full system functionality
- Generated implementation summary report

All P1 issues resolved. System fully functional and test suite operational."
```

**Success Criteria**:
- ✅ All verification checks pass
- ✅ All P1 issues resolved
- ✅ Documentation updated
- ✅ Clean git commit created
- ✅ Implementation summary report completed
- ✅ Project ready for production use
