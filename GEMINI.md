# Project Analysis: Unified AI Project

This document provides an overview of the `Unified-AI-Project` codebase, intended to serve as instructional context for future interactions with the Gemini CLI.

## Project Overview

The `Unified-AI-Project` is a sophisticated monorepo designed as a **hybrid AI ecosystem**. Its primary purpose is to power an internal AI system, notably the AI character "Angela" within a simulation game called "Angela's World". Beyond this, a key architectural design is its ability to **integrate with and orchestrate various external AI agents and development tools** (e.g., Rovo Dev Agent, Gemini). This allows the project to leverage specialized external capabilities while maintaining a modular and extensible core.

The project is structured into:
*   **Applications (`apps/`)**:
    *   `desktop-app`: The Electron-based game client for "Angela's World".
    *   `backend`: The core Python backend, responsible for AI models, APIs, and game logic, driving Angela.
    *   `frontend-dashboard`: A Next.js/React web dashboard for developers to manage, monitor, and debug the AI and game systems.
*   **Packages (`packages/`)**:
    *   `cli`: Command-line interface tools for backend interaction.
    *   `ui`: Shared UI components for frontend applications.

## Building and Running

The project utilizes `pnpm` for monorepo management.

**1. Install pnpm (if not already installed):**
```bash
npm install -g pnpm
```

**2. Install Dependencies:**
From the root of the repository (`D:\Projects\Unified-AI-Project`), run:
```bash
pnpm install
```

**3. Start Development Servers:**
To concurrently start the backend and frontend development servers:
```bash
pnpm dev
```
(The backend API typically runs on `http://localhost:8000`, and the frontend dashboard on `http://localhost:3000`.)

## Testing

To run all tests across the monorepo:
```bash
pnpm test
```

To run tests with coverage reports:
```bash
pnpm test:coverage
```

## Development Conventions

*   **Monorepo Structure**: The project is organized as a monorepo using `pnpm` workspaces.
*   **Documentation**: Comprehensive documentation is maintained in the `docs/` directory, with a central `UNIFIED_DOCUMENTATION_INDEX.md` for navigation.
*   **External Tool Integration**: The project is designed to integrate with external AI development tools, and this integration is managed through specific modules within `apps/backend/src/integrations`.
*   **Testing Practices**: The project includes dedicated `tests/` directories within each application and package, indicating a focus on unit and integration testing. Python tests likely use `pytest` (inferred from `conftest.py` in `apps/backend/tests`).