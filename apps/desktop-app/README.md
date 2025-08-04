# Desktop App: Angela's World Game Client

This application is the official game client for "Angela's World", the AI-driven simulation game at the heart of the Unified AI Project.

## Features

- Desktop interface for interacting with AI services
- Integrates with the Python backend via IPC
- Embedded web views for specific functionalities (e.g., code inspection, dashboard)

## Getting Started

To run the desktop application:

```bash
pnpm --filter desktop-app start
```

## Running Tests

To run tests for the desktop application:

```bash
pnpm --filter desktop-app test
```

To run tests with coverage:

```bash
pnpm --filter desktop-app test:coverage
```
