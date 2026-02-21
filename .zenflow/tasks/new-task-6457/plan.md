# Full SDD workflow

## Configuration
- **Artifacts Path**: {@artifacts_path} → `.zenflow/tasks/{task_id}`

---

## Agent Instructions

If you are blocked and need user clarification, mark the current step with `[!]` in plan.md before stopping.

---

## Workflow Steps

### [x] Step: Requirements
<!-- chat-id: ff9ffce2-b3de-402a-8260-f5cd793fd254 -->

Create a Product Requirements Document (PRD) based on the feature description.

1. Review existing codebase to understand current architecture and patterns
2. Analyze the feature definition and identify unclear aspects
3. Ask the user for clarifications on aspects that significantly impact scope or user experience
4. Make reasonable decisions for minor details based on context and conventions
5. If user can't clarify, make a decision, state the assumption, and continue

Save the PRD to `{@artifacts_path}/requirements.md`.

### [x] Step: Technical Specification
<!-- chat-id: 65f34d28-1b6a-44b4-b061-1674d93d860d -->

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
<!-- chat-id: feeb4e4a-fd06-4402-9740-f9e4e5dc2df5 -->

Create a detailed implementation plan based on `{@artifacts_path}/spec.md`.

1. Break down the work into concrete tasks
2. Each task should reference relevant contracts and include verification steps
3. Replace the Implementation step below with the planned tasks

Rule of thumb for step size: each step should represent a coherent unit of work (e.g., implement a component, add an API endpoint). Avoid steps that are too granular (single function) or too broad (entire feature).

Important: unit tests must be part of each implementation task, not separate tasks. Each task should implement the code and its tests together, if relevant.

If the feature is trivial and doesn't warrant full specification, update this workflow to remove unnecessary steps and explain the reasoning to the user.

Save to `{@artifacts_path}/plan.md`.

### [ ] Step: Phase 1 - Baseline validation and drift discovery
<!-- chat-id: d4849820-93f9-4ac3-8455-0594ff370299 -->
- Ensure `.gitignore` covers generated artifacts (node_modules/, dist/, build/, .cache/, *.log)
- Install workspaces and verify installs
  - JS/TS: `pnpm install`
  - Python: create venv and install per [./pyproject.toml](./pyproject.toml) or [./apps/backend/pyproject.toml](./apps/backend/pyproject.toml)
- Run baseline quality gates and capture reports to [./test_results](./test_results)
  - JS/TS: `pnpm lint`, `pnpm format --check`, `pnpm test`
  - Python: `black --check apps/backend/src tests/`, `isort --check-only apps/backend/src tests/`, `flake8 apps/backend/src tests/`, `mypy apps/backend/src`, `pytest tests/`
- Generate summary MD/JSON under [./test_results](./test_results)
- Add/update minimal smoke tests where missing
- Verification
  - All commands complete; reports written under [./test_results](./test_results)

### [ ] Step: Phase 2 - Python dependency unification
<!-- chat-id: d1f8f1f3-d203-4082-a17d-a4ec7548a993 -->
- Select single source of truth for Python deps (default: [./apps/backend/pyproject.toml](./apps/backend/pyproject.toml))
- Migrate/remove redundant `requirements*.txt` or duplicate `pyproject.toml` entries according to chosen model
- Update repo scripts to generate `requirements.txt` if needed for CI/runtime
- Align pre-commit hooks and tooling configs to the chosen model
- Update/add unit tests if refactors impact import paths or startup
- Verification
  - `black`, `isort`, `flake8`, `mypy`, and `pytest` all pass; no duplicate/conflicting dependency files remain

### [ ] Step: Phase 3 - Backend framework standardization (FastAPI)
<!-- chat-id: 65fa47e9-aaa2-4d99-ae88-d1871073379d -->
- Purge Flask metadata/links from [./apps/backend/pyproject.toml](./apps/backend/pyproject.toml)
- Confirm application entrypoint `src/services/main_api_server.py:app`
- Normalize structure under [./apps/backend/src](./apps/backend/src): `api/` (routers), `models/` (pydantic), `services/`, `core/`
- Align [./apps/backend/package.json](./apps/backend/package.json) scripts (e.g., `dev:api`) with the canonical entrypoint
- Add/update unit tests for routers/models; validate OpenAPI generation
- Verification
  - `python -m uvicorn src.services.main_api_server:app --reload` boots
  - FastAPI docs accessible; `pytest` suite green

### [ ] Step: Phase 4 - Node version alignment and Electron build path
<!-- chat-id: 2bb60174-c206-47fd-8ebd-01583ce844c1 -->
- Set monorepo Node engines to ≥18 in [./package.json](./package.json) and CI matrix
- Ensure Electron app installs/builds via pnpm workspace (e.g., `pnpm --filter electron_app install/build`)
- Centralize native module build flags in [./scripts](./scripts); validate Windows/macOS/Linux where applicable
- Add/update smoke tests for Electron startup and core APIs (where feasible)
- Verification
  - `pnpm install` succeeds across workspaces under Node 18+
  - Electron dev starts without runtime errors; native modules compile for target OS

### [ ] Step: Phase 5 - Tests and coverage gating
- Enforce backend coverage threshold via `pytest --cov=apps/backend/src --cov-report=term-missing`
- Stabilize or mark flaky tests; unify markers (`unit`, `integration`, `slow`)
- Triage [./tests_backup](./tests_backup): migrate valid tests to [./tests](./tests) or remove obsolete ones
- Add/adjust tests to reach threshold; ensure deterministic test ordering
- Verification
  - Coverage ≥ target (initially backend scope); all tests pass locally and in CI

### [ ] Step: Phase 6 - Live2D libs management and Mobile minimal path
- Decide strategy for [./apps/web-live2d-viewer/libs/live2dframework](./apps/web-live2d-viewer/libs/live2dframework): vendored with periodic sync or externalized package with lock
- Pin versions; add/update sync or install script under [./scripts](./scripts)
- Mobile: verify RN bootstrap and create minimal smoke path (app boots, screen renders, backend ping succeeds)
- Add/update unit/integration tests where feasible (e.g., utility modules, API client stubs)
- Verification
  - Live2D viewer builds successfully; RN minimal run works and hits backend ping endpoint

### [ ] Step: Phase 7 - Secrets and CI/pre-commit unification
- Add/verify `.env.example` for each app; confirm secrets are ignored from VCS
- Unify to a single root pre-commit config invoking Python and JS format/lint hooks
- Ensure CI runs all gates (Node 18+, Python 3.8+) and enforces engines/tooling
- Verification
  - Pre-commit passes on staged/all files; CI green with full matrix
