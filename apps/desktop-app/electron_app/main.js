const { app, BrowserWindow, ipcMain } = require("electron");
const path = require("path");
const { spawn } = require("child_process");
const fs = require("fs");

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
  const mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
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

ipcMain.handle("game:start", async () => {
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

ipcMain.handle(/^api:(get|post|put|delete):(.*)$/, async (event, method, path, data) => {
  const url = `${backendApiUrl}/api/${path}`;
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
    console.error(`Main Process: Error in API call (${method.toUpperCase()} ${path}):`, error);
    throw error;
  }
});
