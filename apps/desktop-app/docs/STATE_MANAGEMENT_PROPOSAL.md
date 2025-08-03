# State Management Proposal

This document proposes a simple, centralized state management structure for the Electron application. This proposal avoids external libraries and uses plain JavaScript to create a predictable and maintainable state container.

## 1. The Problem

Currently, the application state is managed in an ad-hoc manner:
-   State variables like `currentSessionId` and `activePolls` are global within the renderer process.
-   The DOM is used as a primary source of truth for the UI state (e.g., which view is active, the content of input fields).

This approach can lead to bugs that are hard to track, and it makes the application logic tightly coupled to the UI.

## 2. The Proposal: A Simple State Store

I propose creating a single, centralized `store` object to hold all application state. This store will be the single source of truth for the application.

### 2.1. The Store Object

The store object will have the following structure:

```javascript
const store = {
  // Application state
  activeView: 'chat', // 'chat', 'hsp', 'game'
  chat: {
    sessionId: null,
    messages: [], // { text: string, sender: 'user' | 'ai' | 'system' }
  },
hsp: {
    services: [], // { id: string, name: string, ... }
    taskStatus: {}, // { [correlationId]: { status: string, ... } }
    activePolls: {}, // { [correlationId]: intervalId }
  },

  // UI state
  ui: {
    loading: false,
    errorMessage: null,
  },
};
```

### 2.2. State-Modifying Functions (Actions)

Instead of modifying the store directly, we will use a set of "action" functions to update the state. These functions will take the current state and a payload as arguments, and they will return a new state object. This will make state changes more predictable and easier to debug.

Example actions:

```javascript
function setActiveView(state, viewId) {
  return { ...state, activeView: viewId };
}

function setSessionId(state, sessionId) {
  return { ...state, chat: { ...state.chat, sessionId: sessionId } };
}

function addChatMessage(state, message) {
  return {
    ...state,
    chat: {
      ...state.chat,
      messages: [...state.chat.messages, message],
    },
  };
}
```

### 2.3. The `updateState` Function

A single `updateState` function will be responsible for applying the actions to the store and re-rendering the UI.

```javascript
let currentState = store;

function updateState(action, payload) {
  const newState = action(currentState, payload);
  currentState = newState;
  render(); // Re-render the UI with the new state
}
```

### 2.4. The `render` Function

The `render` function will be responsible for updating the DOM based on the current state in the store. This function will be called every time the state is updated.

```javascript
function render() {
  // Update the active view
  showView(currentState.activeView);

  // Update the chat display
  renderChatMessages(currentState.chat.messages);

  // Update the HSP services list
  renderHspServices(currentState.hsp.services);

  // ... and so on for the rest of the UI
}
```

## 3. Benefits of this Approach

*   **Centralized State**: All application state is in one place, making it easy to understand and debug.
*   **Predictable State Changes**: State is only modified through actions, which makes it easy to track how the state changes over time.
*   **Decoupled Logic and UI**: The application logic (actions) is decoupled from the UI (the `render` function). This makes the code easier to test and maintain.
*   **No New Dependencies**: This approach uses plain JavaScript and does not require any new libraries.

## 4. Implementation Plan

1.  Create a new `store.js` file to define the store object and the action functions.
2.  Refactor `renderer.js` to use the new store and actions.
3.  Create a `render.js` file to hold the `render` function and all other DOM-manipulating code.
4.  Update `index.html` to include the new JavaScript files.
