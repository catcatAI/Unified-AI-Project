# Backend: The Heart of Angela

This application contains the core Python backend services that power Angela, the central AI character in the "Angela's World" simulation game.

## Features

- AI models and logic
- API endpoints (FastAPI)
- Integrations with external services
- Data processing and management

## Getting Started

To run the backend development server:

```bash
pnpm --filter backend dev
```

## ChromaDB Setup

This project utilizes ChromaDB for vector storage. The backend is configured to first attempt to connect to a running ChromaDB server via `HttpClient` (defaulting to `localhost:8000`). If this connection fails, it will automatically fall back to using an `EphemeralClient`, which runs an in-memory ChromaDB instance. While the `EphemeralClient` is convenient for development and testing, it does not persist data across sessions.

For persistent vector storage and optimal performance, it is recommended to run a dedicated ChromaDB server. You can start a ChromaDB server using Docker:

```bash
docker run -p 8000:8000 chromadb/chroma
```

Ensure Docker is installed and running on your system before executing this command. Once the server is running, the backend will automatically connect to it.

## Running Tests

To run tests for the backend:

```bash
pnpm --filter backend test
```

To run tests with coverage:

```bash
pnpm --filter backend test:coverage
```
