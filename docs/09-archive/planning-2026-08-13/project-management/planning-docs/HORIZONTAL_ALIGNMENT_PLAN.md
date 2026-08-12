# Horizontal Alignment Plan (Consolidated)

Version: v1.0
Date: 2025-08-06
Owners: PM / Tech Leads

## 1. Goal
Unify experience and practices across sub-projects (backend, frontend-dashboard, desktop-app, cli) by leveraging strengths and eliminating duplication.

## 2. Key Areas of Focus
- Code style & conventions (shared linting)
- Dependency management (centralized, consistent versions)
- Build & test processes (unified scripts)
- Shared components & libraries (extract into packages/ui)
- Architectural patterns (converge on successful patterns)

## 3. Roadmap (Merged)
### Phase 1: Foundational Improvements (Done)
- Centralize dependency management via pnpm workspaces ✅
- Unify code style & linting (shared ESLint) ✅

### Phase 2: Codebase Integration (Done)
- Integrate "Quest Features" into frontend-dashboard ✅
- Extract shared UI components into packages/ui ✅

### Phase 3: Build & Test Processes (Done)
- Unified build & test scripts at repo root ✅

### Phase 4: Next Steps
- Improve test coverage for frontend projects (High)
- Refactor backend dependency management (Poetry/Pipenv) (Medium)
- Continue extracting shared components into packages/ui (Low)
- Better integrate Quest Features with consistent layout/styling (Low)

## 4. Action Plan
1) Audit each sub-project (current state, per key area)
2) Identify alignment opportunities and quick wins
3) Prioritize and execute the roadmap tasks
4) Track progress in STATUS_AND_ACTIONS.md (rolling)

## 5. References
- HORIZONTAL_ALIGNMENT_TASK.md (superseded)
- HORIZONTAL_ALIGNMENT_ROADMAP.md (superseded)
