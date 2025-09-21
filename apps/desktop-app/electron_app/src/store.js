// 修复global未定义的问题
if (typeof global === 'undefined') {
  window.global = window;
}

// 确保DOMPurify在全局作用域可用
if (window.DOMPurify) {
  global.DOMPurify = window.DOMPurify;
}

const initialState = window.initialState || {
  // Application state
  activeView: 'chat', // 'chat', 'hsp', 'game', 'settings'
  chat: {
    sessionId: null,
    messages: [], // { text: string, sender: 'user' | 'ai' | 'system' }
  },
  hsp: {
    services: [], // { id: string, name: string, ... }
    taskStatus: {}, // { [correlationId]: { status: string, ... } }
    activePolls: {}, // { [correlationId]: intervalId }
  },
  // Adding Atlassian integration state
  atlassian: {
    status: null,
    projects: [],
    spaces: [],
    agents: [],
    tasks: []
  },
  settings: {
    theme: 'dark',
    defaultModel: 'gpt-4',
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

// Adding Atlassian integration related actions
function setAtlassianStatus(state, status) {
    return { 
        ...state, 
        atlassian: { 
            ...state.atlassian, 
            status: status 
        } 
    };
}

function setJiraProjects(state, projects) {
    return { 
        ...state, 
        atlassian: { 
            ...state.atlassian, 
            projects: projects 
        } 
    };
}

function setConfluenceSpaces(state, spaces) {
    return { 
        ...state, 
        atlassian: { 
            ...state.atlassian, 
            spaces: spaces 
        } 
    };
}

function setRovoAgents(state, agents) {
    return { 
        ...state, 
        atlassian: { 
            ...state.atlassian, 
            agents: agents 
        } 
    };
}

function setRovoTasks(state, tasks) {
    return { 
        ...state, 
        atlassian: { 
            ...state.atlassian, 
            tasks: tasks 
        } 
    };
}

function setTheme(state, theme) {
    return { ...state, settings: { ...state.settings, theme: theme } };
}

function setDefaultModel(state, defaultModel) {
    return { ...state, settings: { ...state.settings, defaultModel: defaultModel } };
}

function setLoading(state, isLoading) {
    return { ...state, ui: { ...state.ui, loading: isLoading } };
}

function setErrorMessage(state, errorMessage) {
    return { ...state, ui: { ...state.ui, errorMessage: errorMessage } };
}

// --- Update Function ---

let currentState = initialState;

function updateState(action, payload) {
  const newState = action(currentState, payload);
  currentState = newState;
  render(); // This will be defined in render.js
  
  // Check if electronAPI is available before invoking
  if (window.electronAPI && typeof window.electronAPI.invoke === 'function') {
    window.electronAPI.invoke('save-state', currentState);
  } else {
    console.warn('electronAPI not available, state not saved');
  }
}

window.store = {
    getState: () => currentState,
    updateState,
    actions: {
        setActiveView,
        setSessionId,
        addChatMessage,
        setHspServices,
        setHspTaskStatus,
        addHspActivePoll,
        removeHspActivePoll,
        setAtlassianStatus,
        setJiraProjects,
        setConfluenceSpaces,
        setRovoAgents,
        setRovoTasks,
        setTheme,
        setDefaultModel,
        setLoading,
        setErrorMessage,
    },
};