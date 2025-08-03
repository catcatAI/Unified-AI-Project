# History and Session Management Proposal

This document proposes a system for saving and restoring user sessions and conversation history in the Electron application.

## 1. The Problem

The application currently does not persist any data between sessions. When the user closes the application, all conversation history and settings are lost.

## 2. The Proposal: `electron-store`

I propose using the `electron-store` library to persist the application state to the user's local machine. `electron-store` is a simple and robust library for storing and retrieving data in Electron applications.

### 2.1. Installation

First, we will need to install `electron-store`:

```bash
npm install electron-store
```

### 2.2. Saving the State

We will create a new `store` instance and use it to save the application state whenever it changes.

```javascript
// main.js
const Store = require('electron-store');
const store = new Store();

// ...

ipcMain.handle('save-state', (event, state) => {
  store.set(state);
});
```

### 2.3. Loading the State

When the application starts, we will load the saved state from the store.

```javascript
// main.js
const Store = require('electron-store');
const store = new Store();

// ...

function createWindow() {
  const initialState = store.get();
  const mainWindow = new BrowserWindow({
    // ...
    webPreferences: {
      // ...
      preload: path.join(__dirname, 'preload.js'),
      additionalArguments: [JSON.stringify(initialState)],
    },
  });
  // ...
}
```

### 2.4. Updating the Renderer

We will update the renderer process to get the initial state from the main process and to send the updated state to the main process whenever it changes.

```javascript
// preload.js
contextBridge.exposeInMainWorld('initialState', JSON.parse(process.argv.find(arg => arg.startsWith('{'))));

// renderer.js
let currentState = window.initialState || store;

function updateState(action, payload) {
  const newState = action(currentState, payload);
  currentState = newState;
  render();
  window.electronAPI.invoke('save-state', currentState);
}
```

## 3. Benefits of this Approach

*   **Data Persistence**: The application state will be saved between sessions.
*   **Simple API**: `electron-store` has a simple and easy-to-use API.
*   **Robust**: `electron-store` is a popular and well-tested library.

## 4. Implementation Plan

1.  Install the `electron-store` library.
2.  Refactor `main.js` to use `electron-store` to save and load the application state.
3.  Refactor `preload.js` to expose the initial state to the renderer process.
4.  Refactor `renderer.js` to use the initial state and to send the updated state to the main process.
