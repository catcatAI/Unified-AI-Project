# Unified AI Project Monorepo

This repository contains the Unified AI Project, a hybrid AI ecosystem structured as a monorepo. It is designed not only to power its own internal AI systems (such as the game character, Angela) but also to integrate with and orchestrate various external AI agents and development tools (e.g., Rovo Dev Agent, Gemini).

## Project Structure

This monorepo is organized into applications and packages, centered around a unique AI-driven simulation game, "Angela's World".

### Applications (`apps/`)
- **`apps/desktop-app`**: The game client for "Angela's World", built with Electron.
- **`apps/backend`**: The core Python backend that powers the game's central AI character, Angela. It includes all AI models, APIs, and game logic.
- **`apps/frontend-dashboard`**: A web-based dashboard for developers to manage, monitor, and debug the AI and game systems.

### Packages (`packages/`)
- **`packages/cli`**: Command-line interface tools for interacting with the backend services.
- **`packages/ui`**: Shared UI components and design system for the frontend applications.

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

### Export OpenAPI spec
```bash
python Unified-AI-Project/scripts/export_openapi.py
# output: Unified-AI-Project/docs/api/openapi.json
```


To run all tests across the monorepo:

```bash
pnpm test
```

To run tests with coverage reports:

```bash
pnpm test:coverage
```

## Recent Updates

- Hot reload, hot migration (blue/green), and draining support added to backend API.
  - Docs: [docs/05-development/hot-reload-and-drain.md](docs/05-development/hot-reload-and-drain.md)
  - Endpoints: see [docs/API_ENDPOINTS.md](docs/API_ENDPOINTS.md) under "Hot Reload and Drain".
- AudioService demo mode and sentiment-analysis stub implemented.
  - In demo mode, `speech_to_text_with_sentiment_analysis` returns a mock payload with `sentiment: "positive"`.
  - When demo mode is disabled, the same method raises `NotImplementedError` (until real integration is configured).

## Audio Service Demo Mode

AudioService supports a demo mode for quick end-to-end testing without external STT/Sentiment services.

Enable demo mode by adding the following to the backend config YAML:

```yaml
# apps/backend/configs/config.yaml
use_simulated_resources: true
```

Behavior in demo mode:
- `speech_to_text(audio_bytes)`: returns a mock transcription string.
- `speech_to_text_with_sentiment_analysis(audio_bytes)`: returns a JSON object like:
  ```json
  { "text": "This is a mock transcription.", "sentiment": "positive", "confidence": 0.9, "language": "en-US" }
  ```
- Disabling demo mode (or omitting the flag) causes `speech_to_text_with_sentiment_analysis` to raise `NotImplementedError`.

## Documentation

For detailed documentation on project architecture, development guidelines, and more, please refer to the [docs/README.md](docs/README.md) directory.

## Individual Package Readmes

For more specific information about each package, refer to their respective README files:

- [Backend README](apps/backend/README.md)
- [Frontend Dashboard README](apps/frontend-dashboard/README.md)
- [Desktop App README](apps/desktop-app/README.md)
- [CLI README](packages/cli/README.md)
