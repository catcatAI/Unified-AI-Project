const { app, BrowserWindow, ipcMain } = require("electron");
const path = require("path");
const { spawn } = require("child_process");
const fs = require("fs");
const Store = require("electron-store");
const CHANNELS = require("./src/ipc-channels");
const ErrorHandler = require("./src/error-handler");

// 端口管理配置
const PORT_CONFIG = {
  FRONTEND_DASHBOARD: 3000,
  DESKTOP_APP: 3001,
  BACKEND_API: 8000  // 改回端口为8000
};

const errorHandler = new ErrorHandler();

const store = new Store();

let pythonExecutable = "python";
let backendApiUrl = `http://localhost:${PORT_CONFIG.BACKEND_API}`; // 使用统一的端口配置

function loadDesktopAppConfig() {
  const configPath = path.join(__dirname, "..", "desktop-app-config.json");
  try {
    if (fs.existsSync(configPath)) {
      const configFileContent = fs.readFileSync(configPath, "utf8");
      const config = JSON.parse(configFileContent);
      if (config.backend_api_url) {
        backendApiUrl = config.backend_api_url;
        console.log(`Main Process: Loaded backend API URL: ${backendApiUrl}`);
        // errorHandler.log('info', `Loaded backend API URL: ${backendApiUrl}`);
      } else {
        console.log("Main Process: Config file found, but backend_api_url not set. Using default.");
        // errorHandler.log('warn', "Config file found, but backend_api_url not set. Using default.");
      }
    } else {
      console.log("Main Process: desktop-app-config.json not found. Using default backend API URL.");
      // errorHandler.log('warn', "desktop-app-config.json not found. Using default backend API URL.");
    }
  } catch (error) {
    console.error("Main Process: Error loading desktop app config:", error);
    // errorHandler.log('error', `Error loading desktop app config: ${error.message}`, error);
  }
}

function loadPythonPath() {
  const envPath = path.join(__dirname, "..", "..", "..", ".env");
  try {
    if (fs.existsSync(envPath)) {
      const envFileContent = fs.readFileSync(envPath, "utf8");
      const match = envFileContent.match(/^PYTHON_EXECUTABLE=(.*)$/m);
      if (match && match[1]) {
        pythonExecutable = match[1].trim();
        console.log(
          `Main Process: Found Python executable path: ${pythonExecutable}`,
        );
        // errorHandler.log('info', `Found Python executable path: ${pythonExecutable}`);
      } else {
        console.log(
          "Main Process: .env file found, but PYTHON_EXECUTABLE not set. Using default 'python'.",
        );
        // errorHandler.log('warn', ".env file found, but PYTHON_EXECUTABLE not set. Using default 'python'.");
      }
    } else {
      console.log("Main Process: .env file not found. Using default 'python'.");
      // errorHandler.log('warn', ".env file not found. Using default 'python'.");
    }
  } catch (error) {
    console.error("Main Process: Error loading Python path:", error);
    // errorHandler.log('error', `Error loading Python path: ${error.message}`, error);
  }
}

function createWindow() {
  const initialState = store.get();
  const mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
      additionalArguments: [JSON.stringify(initialState)],
    },
  });

  mainWindow.loadFile(path.join(__dirname, "index.html"));
  mainWindow.webContents.openDevTools();
}

app.whenReady().then(() => {
  loadDesktopAppConfig();
  loadPythonPath();
  createWindow();

  app.on("activate", function () {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on("window-all-closed", function () {
  if (process.platform !== "darwin") app.quit();
});

// --- IPC Handlers ---

ipcMain.handle(CHANNELS.GAME_START, async () => {
  try {
    console.log("Main Process: Received 'game:start' request from renderer.");
    const gameProcess = spawn(pythonExecutable, [
      path.join(__dirname, "..", "..", "..", "backend", "src", "game", "main.py"),
    ]);

    gameProcess.stdout.on("data", (data) => {
      console.log(`Game stdout: ${data}`);
    });

    gameProcess.stderr.on("data", (data) => {
      console.error(`Game stderr: ${data}`);
      errorHandler.log('error', `Game stderr: ${data}`);
    });

    gameProcess.on("close", (code) => {
      console.log(`Game process exited with code ${code}`);
      if (code !== 0) {
        errorHandler.log('error', `Game process exited with code ${code}`);
      }
    });

    gameProcess.on("error", (error) => {
      console.error(`Game process error: ${error.message}`);
      errorHandler.log('error', `Game process error: ${error.message}`, error);
    });
  } catch (error) {
    errorHandler.log('error', `Error in GAME_START: ${error.message}`, error);
    throw error;
  }
});

async function handleApiCall(method, apiPath, data) {
    const url = `${backendApiUrl}/api/v1/${apiPath}`;
    try {
        const response = await fetch(url, {
            method: method.toUpperCase(),
            headers: { "Content-Type": "application/json" },
            body: data ? JSON.stringify(data) : undefined,
        });
        if (!response.ok) {
            const errorInfo = await response.text();
            const error = new Error(`HTTP error! status: ${response.status}, message: ${errorInfo}`);
            error.status = response.status;
            throw error;
        }
        return await response.json();
    } catch (error) {
        errorHandler.log('error', `Main Process: Error in API call (${method.toUpperCase()} ${apiPath}): ${error.message}`, error);
        throw error;
    }
}

ipcMain.handle(CHANNELS.API_START_SESSION, async (event, data) => {
    try {
        return await handleApiCall("post", "session/start", data);
    } catch (error) {
        errorHandler.log('error', `Error in API_START_SESSION: ${error.message}`, error);
        throw error;
    }
});

ipcMain.handle(CHANNELS.API_SEND_MESSAGE, async (event, data) => {
    try {
        return await handleApiCall("post", "angela/chat", data);
    } catch (error) {
        errorHandler.log('error', `Error in API_SEND_MESSAGE: ${error.message}`, error);
        throw error;
    }
});

// 添加新的API处理器
ipcMain.handle("api:code-analysis", async (event, data) => {
    try {
        return await handleApiCall("post", "code", data);
    } catch (error) {
        errorHandler.log('error', `Error in api:code-analysis: ${error.message}`, error);
        throw error;
    }
});

ipcMain.handle("api:search", async (event, data) => {
    try {
        return await handleApiCall("post", "search", data);
    } catch (error) {
        errorHandler.log('error', `Error in api:search: ${error.message}`, error);
        throw error;
    }
});

ipcMain.handle("api:image-generation", async (event, data) => {
    try {
        return await handleApiCall("post", "image", data);
    } catch (error) {
        errorHandler.log('error', `Error in api:image-generation: ${error.message}`, error);
        throw error;
    }
});

ipcMain.handle("api:health", async (event) => {
    try {
        return await handleApiCall("get", "health");
    } catch (error) {
        errorHandler.log('error', `Error in api:health: ${error.message}`, error);
        throw error;
    }
});

// Atlassian handlers
ipcMain.handle("api:atlassian-status", async () => {
    try {
        return await handleApiCall("get", "atlassian/status");
    } catch (error) {
        errorHandler.log('error', `Error in api:atlassian-status: ${error.message}`, error);
        throw error;
    }
});

ipcMain.handle("api:atlassian-health", async () => {
    try {
        return await handleApiCall("get", "atlassian/health");
    } catch (error) {
        errorHandler.log('error', `Error in api:atlassian-health: ${error.message}`, error);
        throw error;
    }
});

ipcMain.handle("api:jira-projects", async () => {
    try {
        return await handleApiCall("get", "atlassian/jira/projects");
    } catch (error) {
        errorHandler.log('error', `Error in api:jira-projects: ${error.message}`, error);
        throw error;
    }
});

ipcMain.handle("api:jira-issues", async (e, { jql, limit }) => {
    try {
        return await handleApiCall("get", `atlassian/jira/issues${jql?`?jql=${encodeURIComponent(jql)}&limit=${limit||20}`:`?limit=${limit||20}`}`);
    } catch (error) {
        errorHandler.log('error', `Error in api:jira-issues: ${error.message}`, error);
        throw error;
    }
});

ipcMain.handle("api:jira-create", async (e, data) => {
    try {
        return await handleApiCall("post", "atlassian/jira/issue", data);
    } catch (error) {
        errorHandler.log('error', `Error in api:jira-create: ${error.message}`, error);
        throw error;
    }
});

ipcMain.handle("api:confluence-spaces", async () => {
    try {
        return await handleApiCall("get", "atlassian/confluence/spaces");
    } catch (error) {
        errorHandler.log('error', `Error in api:confluence-spaces: ${error.message}`, error);
        throw error;
    }
});

ipcMain.handle("api:confluence-search", async (e, { query, limit }) => {
    try {
        return await handleApiCall("get", `atlassian/confluence/search?query=${encodeURIComponent(query)}&limit=${limit||25}`);
    } catch (error) {
        errorHandler.log('error', `Error in api:confluence-search: ${error.message}`, error);
        throw error;
    }
});

ipcMain.handle("api:confluence-create-page", async (e, data) => {
    try {
        return await handleApiCall("post", "atlassian/confluence/page", data);
    } catch (error) {
        errorHandler.log('error', `Error in api:confluence-create-page: ${error.message}`, error);
        throw error;
    }
});

ipcMain.handle("api:rovo-agents", async () => {
    try {
        return await handleApiCall("get", "atlassian/rovo/agents");
    } catch (error) {
        errorHandler.log('error', `Error in api:rovo-agents: ${error.message}`, error);
        throw error;
    }
});

ipcMain.handle("api:rovo-tasks", async () => {
    try {
        return await handleApiCall("get", "atlassian/rovo/tasks");
    } catch (error) {
        errorHandler.log('error', `Error in api:rovo-tasks: ${error.message}`, error);
        throw error;
    }
});

ipcMain.handle("api:rovo-assign-task", async (e, data) => {
    try {
        return await handleApiCall("post", "atlassian/rovo/assign", data);
    } catch (error) {
        errorHandler.log('error', `Error in api:rovo-assign-task: ${error.message}`, error);
        throw error;
    }
});

ipcMain.handle(CHANNELS.HSP_GET_DISCOVERED_SERVICES, async (event, data) => {
    try {
        // This would typically call a backend service, but for now we mock it
        console.log("Main Process: Received 'hsp:get-discovered-services' request from renderer.");
        return [
            {
                capability_id: "test-capability-1",
                name: "Test Capability 1",
                version: "1.0",
                ai_id: "test-ai-1",
                description: "This is a test capability.",
                tags: ["test", "mock"],
                availability_status: "available",
            },
        ];
    } catch (error) {
        errorHandler.log('error', `Error in HSP_GET_DISCOVERED_SERVICES: ${error.message}`, error);
        throw error;
    }
});

ipcMain.handle(CHANNELS.HSP_REQUEST_TASK, async (event, data) => {
    try {
        // This would typically call a backend service, but for now we mock it
        console.log("Main Process: Received 'hsp:request-task' request from renderer.");
        return {
            status_message: "Task request sent.",
            correlation_id: `mock-correlation-${Date.now()}`,
        };
    } catch (error) {
        errorHandler.log('error', `Error in HSP_REQUEST_TASK: ${error.message}`, error);
        throw error;
    }
});

ipcMain.handle(CHANNELS.HSP_GET_TASK_STATUS, async (event, correlationId) => {
    try {
        // This would typically call a backend service, but for now we mock it
        console.log(`Main Process: Received 'hsp:get-task-status' request for ${correlationId}.`);
        return {
            correlation_id: correlationId,
            status: "completed",
            message: "The task completed successfully.",
            result_payload: {
                result: "This is a mock result.",
            },
        };
    } catch (error) {
        errorHandler.log('error', `Error in HSP_GET_TASK_STATUS: ${error.message}`, error);
        throw error;
    }
});

ipcMain.handle('save-state', (event, state) => {
  store.set(state);
});