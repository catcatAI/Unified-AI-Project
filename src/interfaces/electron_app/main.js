// Placeholder for Electron main process (main.js)
const { app, BrowserWindow, ipcMain, net } = require('electron'); // Added ipcMain and net
const path = require('path');
const { spawn } = require('child_process');

const API_BASE_URL = "http://localhost:8000/api/v1"; // Assuming FastAPI runs here

function createWindow () {
  // Create the browser window.
  const mainWindow = new BrowserWindow({
    width: 800,
    height: 600,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true, // Recommended for security
      nodeIntegration: false  // Recommended for security
    }
  });

  // Load the index.html of the app.
  mainWindow.loadFile(path.join(__dirname, 'index.html'));

  // Open the DevTools (optional - useful for debugging renderer process)
  // mainWindow.webContents.openDevTools();

  console.log("Electron main window created and index.html loaded.");
}

app.whenReady().then(() => {
  createWindow();

  app.on('activate', function () {
    // On macOS it's common to re-create a window in the app when the
    // dock icon is clicked and there are no other windows open.
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', function () {
  // Quit when all windows are closed, except on macOS.
  if (process.platform !== 'darwin') app.quit();
});

// --- IPC Handlers ---
ipcMain.handle('hsp:get-discovered-services', async () => {
  console.log("Main Process: Received 'hsp:get-discovered-services' request from renderer.");
  return new Promise((resolve, reject) => {
    const request = net.request({
      method: 'GET',
      protocol: 'http:',
      hostname: 'localhost',
      port: 8000, // Assuming FastAPI port
      path: '/api/v1/hsp/services',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      }
    });

    let responseBody = '';
    request.on('response', (response) => {
      console.log(`Main Process: API GET /hsp/services - STATUS: ${response.statusCode}`);
      response.on('data', (chunk) => {
        responseBody += chunk;
      });
      response.on('end', () => {
        if (response.statusCode === 200) {
          try {
            const parsedData = JSON.parse(responseBody);
            console.log("Main Process: Successfully fetched and parsed services from API.");
            resolve(parsedData);
          } catch (e) {
            console.error("Main Process: Failed to parse JSON from API response:", e);
            reject(new Error('Failed to parse API response.'));
          }
        } else {
          console.error(`Main Process: API request failed with status ${response.statusCode}. Body: ${responseBody}`);
          reject(new Error(`API request failed with status ${response.statusCode}`));
        }
      });
      response.on('error', (error) => {
        console.error('Main Process: Error in API response stream:', error);
        reject(error);
      });
    });

    request.on('error', (error) => {
      console.error('Main Process: Error making API request to /hsp/services:', error);
      reject(error);
    });

    request.end();
  });
});

ipcMain.handle('hsp:request-task', async (event, { targetCapabilityId, parameters }) => {
  console.log(`Main Process: Received 'hsp:request-task' for cap ID '${targetCapabilityId}' with params:`, parameters);
  return new Promise((resolve, reject) => {
    const postData = JSON.stringify({
      target_capability_id: targetCapabilityId,
      parameters: parameters
    });

    const request = net.request({
      method: 'POST',
      protocol: 'http:',
      hostname: 'localhost',
      port: 8000, // FastAPI port
      path: '/api/v1/hsp/tasks',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(postData),
        'Accept': 'application/json'
      }
    });

    let responseBody = '';
    request.on('response', (response) => {
      console.log(`Main Process: API POST /hsp/tasks - STATUS: ${response.statusCode}`);
      response.on('data', (chunk) => { responseBody += chunk; });
      response.on('end', () => {
        try {
          const parsedData = JSON.parse(responseBody);
          console.log("Main Process: Successfully received response from POST /hsp/tasks API:", parsedData);
          resolve(parsedData); // This is HSPTaskRequestOutput model
        } catch (e) {
          console.error("Main Process: Failed to parse JSON from POST /hsp/tasks API response:", e, "Body:", responseBody);
          reject(new Error('Failed to parse API response for task request.'));
        }
      });
      response.on('error', (error) => { reject(error); });
    });
    request.on('error', (error) => { reject(error); });
    request.write(postData);
    request.end();
  });
});

ipcMain.handle('hsp:get-task-status', async (event, correlationId) => {
  console.log(`Main Process: Received 'hsp:get-task-status' for correlation ID '${correlationId}'.`);
  return new Promise((resolve, reject) => {
    const request = net.request({
      method: 'GET',
      protocol: 'http:',
      hostname: 'localhost',
      port: 8000, // FastAPI port
      path: `/api/v1/hsp/tasks/${correlationId}`, // Use the correlationId in the path
      headers: {
        'Accept': 'application/json'
      }
    });

    let responseBody = '';
    request.on('response', (response) => {
      console.log(`Main Process: API GET /hsp/tasks/${correlationId} - STATUS: ${response.statusCode}`);
      response.on('data', (chunk) => { responseBody += chunk; });
      response.on('end', () => {
        try {
          const parsedData = JSON.parse(responseBody);
          console.log(`Main Process: Successfully received response from GET /hsp/tasks/${correlationId} API:`, parsedData);
          resolve(parsedData); // This is HSPTaskStatusOutput model
        } catch (e) {
          console.error(`Main Process: Failed to parse JSON from GET /hsp/tasks/${correlationId} API response:`, e, "Body:", responseBody);
          reject(new Error('Failed to parse API response for task status.'));
        }
      });
      response.on('error', (error) => { reject(error); });
    });
    request.on('error', (error) => { reject(error); });
    request.end();
  });
});


ipcMain.handle('game:start', async () => {
  console.log("Main Process: Received 'game:start' request from renderer.");
  const gameProcess = spawn('python', [path.join(__dirname, '..', '..', 'game', 'main.py')]);

  gameProcess.stdout.on('data', (data) => {
    console.log(`Game stdout: ${data}`);
  });

  gameProcess.stderr.on('data', (data) => {
    console.error(`Game stderr: ${data}`);
  });

  gameProcess.on('close', (code) => {
    console.log(`Game process exited with code ${code}`);
  });
});

console.log("Electron main.js placeholder script loaded. IPC handlers for HSP services and tasks set up.");
