# Electron Main Process: Desktop Application Core

## Overview

The `main.js` (`apps/desktop-app/electron_app/main.js`) serves as the **main process script for the Electron desktop application** of the Unified-AI-Project. It is the central orchestrator responsible for the application's lifecycle, window management, inter-process communication (IPC) with the renderer process, and crucially, the **launching and management of the Python backend AI services**.

This module is the bridge that connects the user-facing desktop interface with the powerful AI functionalities residing in the Python backend, enabling a rich, integrated desktop experience for "Angela's World" and other AI interactions.

## Key Responsibilities and Features

1.  **Application Lifecycle Management**: 
    *   Utilizes Electron's `app` module to control the application's startup, shutdown, and activation events.
    *   Ensures proper initialization and graceful termination of the application.

2.  **Window Management (`createWindow`)**: 
    *   Creates and configures the main `BrowserWindow` that houses the application's user interface.
    *   Sets window dimensions, web preferences (e.g., `preload` script, `contextIsolation`), and loads the `index.html` file.
    *   Includes `openDevTools()` for development and debugging.

3.  **Backend API Communication**: 
    *   Handles HTTP requests to the Python backend API (running on `http://localhost:8000` by default).
    *   Provides `ipcMain.handle` methods (e.g., `API_START_SESSION`, `API_SEND_MESSAGE`) that allow the renderer process to make API calls to the backend.

4.  **Python Backend Process Launch (`ipcMain.handle(CHANNELS.GAME_START)`)**: 
    *   Spawns a child process to run the Python game backend (`backend/src/game/main.py`).
    *   Captures and logs `stdout` and `stderr` from the Python process for monitoring and debugging.

5.  **Configuration Loading**: 
    *   Loads the `backend_api_url` from `desktop-app-config.json` and the `PYTHON_EXECUTABLE` path from the project's `.env` file.
    *   Provides sensible default values if configuration files or variables are not found.

6.  **Inter-Process Communication (IPC) Handlers**: 
    *   Defines various `ipcMain.handle` functions to respond to requests from the renderer process.
    *   These include requests for starting game processes, making API calls (e.g., chat, session management), and querying HSP-related services (with mock data for now).

7.  **Application State Storage (`electron-store`)**: 
    *   Uses the `electron-store` library to persist application state (e.g., user preferences, last session info) across application launches.

## How it Works

When the Electron application starts, `main.js` initializes the main process. It loads configuration, sets up the main window, and defines IPC handlers. The renderer process (the web page) communicates with this main process via IPC channels to perform privileged operations like launching the Python backend or making network requests. The main process acts as a secure intermediary, ensuring that backend operations are managed and executed correctly.

## Integration with Other Modules

-   **Renderer Process (HTML, CSS, JavaScript)**: The main process provides the backend services and control mechanisms for the user interface running in the renderer process.
-   **Python Backend**: Directly launches and communicates with the Python backend AI services, making them accessible to the desktop application.
-   **`desktop-app-config.json`**: External configuration for the desktop application.
-   **`.env` file**: Used to locate the Python executable and other environment-specific settings.

## Code Location

`apps/desktop-app/electron_app/main.js`
