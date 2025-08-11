# CRUSH.md - Codebase Guidelines for AI Agents

## Build/Lint/Test Commands:

### Monorepo Level:
- **Start Development Servers:** `pnpm dev`
- **Run All Tests:** `pnpm test`
- **Run All Tests with Coverage:** `pnpm test:coverage`
- **Build All Projects:** `pnpm build`

### Application/Package Specific:

#### `desktop-app` (Electron/React):
- **Start Application:** `electron .` (from `apps/desktop-app` directory)
- **Test:** `pnpm exec jest`
- **Test Coverage:** `jest --coverage`

#### `frontend-dashboard` (Next.js/React):
- **Development Mode:** `nodemon --exec "npx tsx server.ts" --watch server.ts --watch src --ext ts,tsx,js,jsx`
- **Build:** `next build`
- **Start:** `set NODE_ENV=production && tsx server.ts`
- **Lint:** `next lint`
- **Test:** `pnpm exec jest`
- **Test Coverage:** `jest --coverage`

#### `backend` (Python/FastAPI):
- **Development Mode:** `pip install -r requirements.txt && uvicorn src.services.main_api_server:app --reload`
- **Test:** `pip install -r requirements-dev.txt && pytest`
- **Test Coverage:** `pytest --cov=src --cov-report=html --cov-report=term-missing`
- **Run Single Test (Python):** `pytest <path_to_test_file>::<test_function_name>` (e.g., `pytest tests/test_my_module.py::test_my_function`)
  - Note: Tests are typically located in the `tests/` directory as per `pytest.ini`.

#### `cli` (Python):
- **Start:** `python cli/unified_cli.py`
- **Test:** `echo 'CLI tests skipped - requires backend dependencies'`

#### `ui` (React/TypeScript):
- **Lint:** `eslint . --ext .ts,.tsx`
- **Test:** `jest`

## Code Style Guidelines:

### Imports:
- Group imports logically: standard library, third-party, then local modules.
- Sort imports alphabetically within each group.

### Formatting:
- Use auto-formatters (e.g., Black for Python, Prettier/ESLint for JavaScript/TypeScript, gofmt for Go) to maintain consistent formatting.
- Python: Indent with 4 spaces.
- JavaScript/TypeScript: Indent with 2 spaces (consistent with `frontend-dashboard` and `ui`'s ESLint usage).

### Types:
- Use type hints/annotations where appropriate for clarity and maintainability (Python).
- Fully leverage TypeScript's type system for JavaScript/TypeScript projects.

### Naming Conventions:
- Python: `snake_case` for variables and functions, `PascalCase` for classes.
- JavaScript/TypeScript: `camelCase` for variables and functions, `PascalCase` for classes.

### Error Handling:
- Handle errors explicitly and gracefully. Avoid broad `except` clauses (Python).
- Use `try-catch` blocks and appropriate error handling for asynchronous operations (JavaScript/TypeScript).
- Provide meaningful error messages.

### Comments:
- Add comments to explain *why* complex logic is implemented, not *what* it does (unless the "what" is not obvious from the code).

## Repository-Specific Rules:
- No Cursor or Copilot rules found in this repository.

# DO NOT DELETE OR MODIFY THIS FILE. THIS FILE IS USED BY AI AGENTS.
