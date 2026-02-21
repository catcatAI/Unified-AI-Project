# Technical Specification: Repository-wide Audit and Task Enumeration (Unified-AI-Project)

## 1) Technical Context

- **Monorepo layout**
  - Apps: [./apps/backend](./apps/backend), [./apps/desktop-app](./apps/desktop-app), [./apps/mobile-app](./apps/mobile-app), [./apps/web-live2d-viewer](./apps/web-live2d-viewer)
  - Packages: [./packages/cli](./packages/cli)
  - Tests: [./tests](./tests), legacy: [./tests_backup](./tests_backup)
  - Workspace: [./pnpm-workspace.yaml](./pnpm-workspace.yaml)
- **Languages & runtimes**
  - Python 3.8+ (per [./pyproject.toml](./pyproject.toml))
  - Node.js (root engines >=16) vs Electron app docs requiring 18+ → alignment needed
- **Package managers & scripts**
  - JS/TS: pnpm monorepo via [./package.json](./package.json) scripts: `dev`, `test`, `lint`, `format`, `check`, `build`
  - Python: tools configured in root [./pyproject.toml](./pyproject.toml); backend also has [./apps/backend/pyproject.toml](./apps/backend/pyproject.toml) and `requirements*.txt`
- **Frameworks & key libs**
  - Backend: FastAPI + Uvicorn (per [./apps/backend/README.md](./apps/backend/README.md)); verify any Flask remnants in backend `pyproject.toml`
  - Desktop: Electron with native audio modules under [./apps/desktop-app/native_modules](./apps/desktop-app/native_modules)
  - Mobile: React Native under [./apps/mobile-app](./apps/mobile-app)
  - Web/Live2D: [./apps/web-live2d-viewer](./apps/web-live2d-viewer) with embedded libs under [./apps/web-live2d-viewer/libs/live2dframework](./apps/web-live2d-viewer/libs/live2dframework)
- **Quality gates (from agents.md)**
  - JS/TS: `pnpm lint`, `pnpm format`, `pnpm test`
  - Python: `flake8 apps/backend/src tests/`, `black apps/backend/src tests/`, `isort apps/backend/src tests/`, `mypy apps/backend/src`, `pytest tests/`

## 2) Existing Architecture Signals (from PRD validation targets)

- Multiple Python dependency definitions (root and backend) create drift
- Backend entry is FastAPI (`uvicorn src.services.main_api_server:app`), but metadata mentions Flask
- Electron app requires Node 18+ while root engines is 16+
- Tests exist across many domains; some backup/legacy suites exist
- Pre-commit configs exist both at root and backend

## 3) Implementation Approach

The goal is to produce a complete, prioritized issue/task inventory and make foundational harmonization changes to enable reliable builds and tests across the repo.

1) Repository audit automation
- Implement repeatable checks using existing commands and lightweight scripts:
  - Run JS/TS gates: `pnpm lint`, `pnpm format --check` (or dry-run), `pnpm test`
  - Run Python gates: `black --check`, `isort --check-only`, `flake8`, `mypy`, `pytest`
  - Capture outputs to [./test_results](./test_results) JSON/MD where appropriate
- Cross-validate workspace installs: `pnpm install` at root and targeted filters for apps

2) Python dependency unification
- Choose single source of truth:
  - Preferred: consolidate on [./apps/backend/pyproject.toml](./apps/backend/pyproject.toml) managed by Poetry/PEP 621, with `requirements.txt` generated for CI/runtime when necessary; or
  - Alternative: maintain canonical `requirements.txt` + `requirements-dev.txt` and slim `pyproject.toml` (tools only)
- Remove or deprecate conflicting files after migration; document generation path inside repo scripts (no external docs)

3) Backend framework standardization
- Confirm FastAPI as the official framework; purge Flask metadata from [./apps/backend/pyproject.toml](./apps/backend/pyproject.toml)
- Verify app entrypoints under [./apps/backend/src/services](./apps/backend/src/services) and align scripts in [./apps/backend/package.json](./apps/backend/package.json)
- Ensure pydantic models and routers are organized under `src/{api,models,services}` (non-breaking structural tidy as needed)

4) Node version alignment and Electron build path
- Set monorepo-wide Node version policy to LTS ≥18 in [./package.json](./package.json) `engines` and CI
- Ensure Electron app install/build steps work via pnpm workspace (`--filter electron_app` if needed)
- Validate native module build scripts for Win/macOS/Linux; centralize env flags in scripts under [./scripts](./scripts)

5) Live2D libs management
- Establish version pinning and update policy for [./apps/web-live2d-viewer/libs/live2dframework](./apps/web-live2d-viewer/libs/live2dframework)
- If vendored, add periodic sync script; if externalized, define package source and lock strategy

6) Mobile app minimal viable path
- Verify `pnpm install` and RN bootstrap scripts
- Define narrow smoke test (build start, minimal screen, API ping to backend)

7) Tests, coverage, and gating
- Enforce coverage threshold at backend scope initially; wire `pytest --cov=apps/backend/src`
- Unify markers (`unit`, `integration`, `slow`) and stabilize flaky tests
- Move or remove [./tests_backup](./tests_backup) after triage; document disposition within repo scripts or CODEOWNERS where relevant

8) Secrets and configuration
- Add or verify `.env.example` for each app; ensure secrets are not committed
- Define CI secret usage per app; ensure config files reference env with safe defaults

9) CI and pre-commit
- Unify to a single root pre-commit config, invoking Python and JS format/lint hooks
- Ensure CI runs all gates across workspaces and backend

## 4) Source Code Structure Changes

- Backend (incremental, non-breaking):
  - Normalize modules under [./apps/backend/src](./apps/backend/src):
    - `src/api` (FastAPI routers), `src/models` (pydantic), `src/services` (business logic), `src/core` (shared utils)
  - Confirm application entry `src/services/main_api_server.py:app`; update references and scripts accordingly
- Dependencies:
  - Migrate to single canonical dependency definition; remove stale `requirements*.txt` or redundant `pyproject.toml` entries (pick one model)
- Tests:
  - Move validated tests from [./tests_backup](./tests_backup) into [./tests](./tests) or delete if obsolete
- Scripts:
  - Align start/build/test scripts across apps to use pnpm filters and shared env configuration in [./scripts](./scripts)

## 5) Data Model / API / Interface Changes

- No functional API changes required; focus is consolidation and correctness
- Formalize API surface by ensuring routers are grouped by version (e.g., `/api/v1/...`) and pydantic schemas live under `src/models`
- Define a lightweight OpenAPI verification step via FastAPI’s built-in docs to ensure no regressions

## 6) Delivery Phases (Incremental, Testable Milestones)

- Phase 1: Baseline validation and drift discovery
  - Run all quality gates; capture reports; open issues with severity and ownership
- Phase 2: Python dependency unification
  - Choose model; migrate; green on `mypy/flake8/pytest`; remove deprecated files
- Phase 3: Backend framework standardization
  - Fix `pyproject.toml` metadata; normalize entrypoints, routers, and models; regenerate OpenAPI
- Phase 4: Node policy and Electron path
  - Set engines≥18; fix workspace install/build; validate native module builds for target OS
- Phase 5: Tests and coverage gating
  - Establish coverage threshold; stabilize flaky tests; triage and migrate `tests_backup`
- Phase 6: Live2D and Mobile minimal paths
  - Define version/update policy for Live2D libs; validate RN minimal run and backend ping
- Phase 7: Secrets and CI unification
  - Add `.env.example`; wire CI secrets; unify pre-commit and CI workflows

## 7) Verification Approach

- Local commands
  - JS/TS: `pnpm lint`, `pnpm format`, `pnpm test`
  - Python: `flake8 apps/backend/src tests/`, `black apps/backend/src tests/`, `isort apps/backend/src tests/`, `mypy apps/backend/src`, `pytest tests/ --cov=apps/backend/src --cov-report=term-missing`
- Runtime checks
  - Backend: `pnpm --filter backend dev` or `python -m uvicorn src.services.main_api_server:app --reload`
  - Desktop: `cd apps/desktop-app/electron_app && pnpm install && pnpm start`
  - Mobile: RN bootstrap/build minimal run (scripted via pnpm if available)
- CI enforcement
  - Engines and matrix aligned to Node 18+ and Python 3.8+
  - Pre-commit runs on all changed files and periodic full runs

## 8) Assumptions and Open Decisions

- FastAPI is the canonical backend framework; Flask remnants are legacy and will be removed
- Single source of truth for Python deps will be selected in Planning (default: backend `pyproject.toml`)
- Node.js policy to be standardized at ≥18 LTS across the repo unless a package has stricter needs
