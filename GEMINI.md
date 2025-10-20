# Project Context for Gemini CLI

## Unified AI Project Overview
This is a monorepo containing a hybrid AI ecosystem. Its primary function is to power an internal AI system ("Angela" in "Angela's World" game) and integrate with external AI agents and development tools.

**Key components:**
- `apps/desktop-app`: Electron-based game client.
- `apps/backend`: Core Python backend (AI models, APIs, game logic).
- `apps/frontend-dashboard`: Next.js/React web dashboard for AI/game management.
- `packages/cli`: CLI tools for backend interaction.
- `packages/ui`: Shared UI components.

## Development Conventions

### General
- Monorepo managed with `pnpm` workspaces.
- Documentation is in `docs/` with `UNIFIED_DOCUMENTATION_INDEX.md` as the main index.
- Emphasis on modularity and external tool integration.

### Code Style
- **Python**: PEP 8, 4-space indentation.
- **JavaScript/TypeScript**: Standard community practices, 2-space indentation (ESLint, Prettier).
- **Imports**: Grouped (standard, third-party, local), then alphabetically sorted.
- **Typing**: Use type hints (Python), full TypeScript leveraging.
- **Naming**: `snake_case` (Python variables/functions), `PascalCase` (Python classes). `camelCase` (JS/TS variables/functions), `PascalCase` (JS/TS classes).
- **Error Handling**: Explicit and graceful. Avoid broad `except`. Use `try-catch` for JS/TS async.

### Build/Lint/Test Commands

- **Monorepo Root (`D:/Projects/Unified-AI-Project/`):**
  - `pnpm install`: Install all dependencies.
  - `pnpm dev`: Start backend and frontend dev servers.
  - `pnpm test`: Run all tests.
  - `pnpm test:coverage`: Run all tests with coverage.

- **Specific Project Example (`apps/backend`):**
  - `pip install -r requirements.txt && uvicorn src.services.main_api_server:app --reload`: Start backend dev.
  - `pip install -r requirements-dev.txt && pytest`: Run backend tests.
  - `pytest <path_to_test_file>::<test_function_name>`: Run a single Python test.

- **Specific Project Example (`apps/frontend-dashboard`):**
  - `npm run dev`: Start frontend dev server.
  - `npm run lint`: Run frontend linting.
  - `npm run test`: Run frontend tests.
