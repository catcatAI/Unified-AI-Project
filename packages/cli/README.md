# CLI Package

This package contains the command-line interface (CLI) tools for interacting with the Unified AI Project's backend services.

## Features

- Pure HTTP client (no backend imports required)
- Console script entry: `unified-ai`
- Config via flags or env (CLI_BASE_URL, CLI_TOKEN, CLI_TIMEOUT)
- Supports JSON output (`--json`) for automation
- Port management and conflict resolution
- Unified execution framework for all project tools

- Send queries to the AI
- Interact with HSP services
- Manage AI models
- Access training system and concept models
- Context management and tool tracking
- Automated defect detection and testing optimization

## Getting Started

### Install (dev)

- Option A: Run via pnpm
```bash
pnpm --filter cli start -- --help
```

- Option B: Install as console script
```bash
pip install -e .\packages\cli
unified-ai --help
```

Environment variables:
- CLI_BASE_URL (default http://localhost:8000)
- CLI_TOKEN (optional)
- CLI_TIMEOUT (default 10)

Examples:
```bash
unified-ai health --json
unified-ai chat "Hello" --session-id s1 --json
unified-ai analyze --code "def x(): pass" --language python --json
unified-ai atlassian status --json
```

To run the CLI:

```bash
pnpm --filter cli start
```

## Running Tests

To run tests for the CLI:

```bash
pnpm --filter cli test
```

To run tests with coverage:

```bash
pnpm --filter cli test:coverage
```
