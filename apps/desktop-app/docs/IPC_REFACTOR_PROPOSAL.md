# IPC Refactor Proposal

This document proposes a more structured and maintainable approach to Inter-Process Communication (IPC) in the Electron application.

## 1. The Problem

The current IPC implementation is functional, but it has some drawbacks:
-   The API call handling in `main.js` uses a single, dynamic handler with a regular expression. This is clever, but it can be hard to read and debug. It also makes it difficult to see at a glance which API endpoints are available.
-   The channel names are defined as string literals in `preload.js`. This makes them prone to typos and makes it hard to get a quick overview of all available channels.

## 2. The Proposal: A More Explicit and Structured Approach

I propose refactoring the IPC communication to be more explicit and structured.

### 2.1. Define Channels in a Shared File

Create a new file, `apps/desktop-app/electron_app/src/ipc-channels.js`, to define all the IPC channel names as constants.

```javascript
// apps/desktop-app/electron_app/src/ipc-channels.js
module.exports = {
  // Game
  GAME_START: 'game:start',

  // API
  API_START_SESSION: 'api:start-session',
  API_SEND_MESSAGE: 'api:send-message',

  // HSP
  HSP_GET_DISCOVERED_SERVICES: 'hsp:get-discovered-services',
  HSP_REQUEST_TASK: 'hsp:request-task',
  HSP_GET_TASK_STATUS: 'hsp:get-task-status',
};
```

### 2.2. Use Explicit Handlers in `main.js`

Refactor `main.js` to use explicit handlers for each IPC channel.

```javascript
// main.js
const { ipcMain } = require('electron');
const CHANNELS = require('./src/ipc-channels');

// ...

ipcMain.handle(CHANNELS.GAME_START, async () => {
  // ...
});

ipcMain.handle(CHANNELS.API_START_SESSION, async (event, data) => {
  // ...
});

ipcMain.handle(CHANNELS.API_SEND_MESSAGE, async (event, data) => {
  // ...
});

// ... and so on for the other channels
```

### 2.3. Update `preload.js` to Use the Shared Channels

Refactor `preload.js` to import the channel constants from `ipc-channels.js` and use them to whitelist the available channels.

```javascript
// preload.js
const { contextBridge, ipcRenderer } = require('electron');
const CHANNELS = require('./src/ipc-channels');

const validChannels = Object.values(CHANNELS);

contextBridge.exposeInMainWorld('electronAPI', {
  invoke: async (channel, ...args) => {
    if (validChannels.includes(channel)) {
      return await ipcRenderer.invoke(channel, ...args);
    }
    return null;
  },
});
```

### 2.4. Update `renderer.js` to Use the Shared Channels

Refactor `renderer.js` to import the channel constants from `ipc-channels.js` and use them when invoking IPC functions.

```javascript
// renderer.js
const CHANNELS = require('./src/ipc-channels');

// ...

async function startNewSession() {
  const response = await window.electronAPI.invoke(CHANNELS.API_START_SESSION, {});
  // ...
}
```

## 3. Benefits of this Approach

*   **Improved Readability**: The code will be easier to read and understand.
*   **Improved Maintainability**: It will be easier to add, remove, or modify IPC channels.
*   **Reduced Risk of Typos**: Using constants for channel names will reduce the risk of typos.
*   **Better Discoverability**: It will be easy to see all the available IPC channels by looking at the `ipc-channels.js` file.

## 4. Implementation Plan

1.  Create the `apps/desktop-app/electron_app/src/ipc-channels.js` file.
2.  Refactor `main.js` to use the new channel constants and explicit handlers.
3.  Refactor `preload.js` to use the new channel constants for whitelisting.
4.  Refactor `renderer.js` to use the new channel constants.
5.  Update `index.html` to include the new `ipc-channels.js` file.
