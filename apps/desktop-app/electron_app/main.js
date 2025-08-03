const { app, BrowserWindow, ipcMain } = require("electron");
const path = require("path");
const { spawn } = require("child_process");
const fs = require("fs");
const Store = require("electron-store");
const CHANNELS = require("./src/ipc-channels");

const store = new Store();

let pythonExecutable = "python";
let backendApiUrl = "http://localhost:8000"; // Default value

function loadDesktopAppConfig() {
  const configPath = path.join(__dirname, "..", "desktop-app-config.json");
  try {
    if (fs.existsSync(configPath)) {
      const configFileContent = fs.readFileSync(configPath, "utf8");
      const config = JSON.parse(configFileContent);
      if (config.backend_api_url) {
        backendApiUrl = config.backend_api_url;
        console.log(`Main Process: Loaded backend API URL: ${backendApiUrl}`);
      } else {
        console.log("Main Process: Config file found, but backend_api_url not set. Using default.");
      }
    } else {
      console.log("Main Process: desktop-app-config.json not found. Using default backend API URL.");
    }
  } catch (error) {
    console.error("Main Process: Error loading desktop app config:", error);
  }
}

function loadPythonPath() {
  const envPath = path.join(__dirname, "..", "..", "..", ".env");
  if (fs.existsSync(envPath)) {
    const envFileContent = fs.readFileSync(envPath, "utf8");
    const match = envFileContent.match(/^PYTHON_EXECUTABLE=(.*)$/m);
    if (match && match[1]) {
      pythonExecutable = match[1].trim();
      console.log(
        `Main Process: Found Python executable path: ${pythonExecutable}`,
      );
    } else {
      console.log(
        "Main Process: .env file found, but PYTHON_EXECUTABLE not set. Using default 'python'.",
      );
    }
  } else {
    console.log("Main Process: .env file not found. Using default 'python'.");
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
  // mainWindow.webContents.openDevTools();
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
  console.log("Main Process: Received 'game:start' request from renderer.");
  const gameProcess = spawn(pythonExecutable, [
    path.join(__dirname, "..", "..", "..", "backend", "src", "game", "main.py"),
  ]);

  gameProcess.stdout.on("data", (data) => {
    console.log(`Game stdout: ${data}`);
  });

  gameProcess.stderr.on("data", (data) => {
    console.error(`Game stderr: ${data}`);
  });

  gameProcess.on("close", (code) => {
    console.log(`Game process exited with code ${code}`);
  });
});

async function handleApiCall(method, apiPath, data) {
    const url = `${backendApiUrl}/api/${apiPath}`;
    try {
        const response = await fetch(url, {
            method: method.toUpperCase(),
            headers: { "Content-Type": "application/json" },
            body: data ? JSON.stringify(data) : undefined,
        });
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error(`Main Process: Error in API call (${method.toUpperCase()} ${apiPath}):`, error);
        throw error;
    }
}

ipcMain.handle(CHANNELS.API_START_SESSION, async (event, data) => {
    return handleApiCall("post", "session/start", data);
});

ipcMain.handle(CHANNELS.API_SEND_MESSAGE, async (event, data) => {
    return handleApiCall("post", "session/message", data);
});

ipcMain.handle(CHANNELS.HSP_GET_DISCOVERED_SERVICES, async (event, data) => {
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
});

ipcMain.handle(CHANNELS.HSP_REQUEST_TASK, async (event, data) => {
    // This would typically call a backend service, but for now we mock it
    console.log("Main Process: Received 'hsp:request-task' request from renderer.");
    return {
        status_message: "Task request sent.",
        correlation_id: `mock-correlation-${Date.now()}`,
    };
});

ipcMain.handle(CHANNELS.HSP_GET_TASK_STATUS, async (event, correlationId) => {
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
});

ipcMain.handle('save-state', (event, state) => {
  store.set(state);
});
