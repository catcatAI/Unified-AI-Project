# Desktop App Package

This package contains the Electron-based desktop application for the Unified AI Project.

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
