# Unified AI Project Monorepo

This repository contains the unified AI project, structured as a monorepo to manage various interconnected applications and services.

## Project Structure

This monorepo is organized into the following packages:

- **`packages/backend`**: The core Python backend services, including AI models, APIs, and integrations.
- **`packages/frontend-dashboard`**: The main web-based AI dashboard, built with Next.js and React.
- **`packages/desktop-app`**: The Electron-based desktop application.
- **`packages/cli`**: Command-line interface tools for interacting with the backend services.

## Getting Started

To set up and run the entire monorepo, follow these steps:

1.  **Install pnpm**: If you don't have pnpm installed, you can install it globally:
    ```bash
    npm install -g pnpm
    ```

2.  **Install Dependencies**: From the root of this repository, install all dependencies for all packages:
    ```bash
    pnpm install
    ```

3.  **Start Development Servers**: To start both the backend and frontend development servers concurrently:
    ```bash
    pnpm dev
    ```
    The backend API will typically run on `http://localhost:8000`, and the frontend dashboard on `http://localhost:3000`.

## Running Tests

To run all tests across the monorepo:

```bash
pnpm test
```

To run tests with coverage reports:

```bash
pnpm test:coverage
```

## Documentation

For detailed documentation on project architecture, development guidelines, and more, please refer to the [docs/README.md](docs/README.md) directory.

## Individual Package Readmes

For more specific information about each package, refer to their respective README files:

- [Backend README](apps/backend/README.md)
- [Frontend Dashboard README](apps/frontend-dashboard/README.md)
- [Desktop App README](apps/desktop-app/README.md)
- [CLI README](packages/cli/README.md)
