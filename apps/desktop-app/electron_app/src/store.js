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

// --- Actions ---

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

function setHspServices(state, services) {
    return { ...state, hsp: { ...state.hsp, services: services } };
}

function setHspTaskStatus(state, { correlationId, statusData }) {
    return {
        ...state,
        hsp: {
            ...state.hsp,
            taskStatus: {
                ...state.hsp.taskStatus,
                [correlationId]: statusData,
            },
        },
    };
}

function addHspActivePoll(state, { correlationId, intervalId }) {
    return {
        ...state,
        hsp: {
            ...state.hsp,
            activePolls: {
                ...state.hsp.activePolls,
                [correlationId]: intervalId,
            },
        },
    };
}

function removeHspActivePoll(state, correlationId) {
    const newActivePolls = { ...state.hsp.activePolls };
    delete newActivePolls[correlationId];
    return {
        ...state,
        hsp: {
            ...state.hsp,
            activePolls: newActivePolls,
        },
    };
}

function setLoading(state, isLoading) {
    return { ...state, ui: { ...state.ui, loading: isLoading } };
}

function setErrorMessage(state, errorMessage) {
    return { ...state, ui: { ...state.ui, errorMessage: errorMessage } };
}

// --- Update Function ---

let currentState = store;

function updateState(action, payload) {
  const newState = action(currentState, payload);
  currentState = newState;
  render(); // This will be defined in render.js
}
