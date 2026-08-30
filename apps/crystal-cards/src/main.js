const { app, BrowserWindow, ipcMain, Menu } = require('electron');
const path = require('path');
const { AIPlayerServer } = require('./ai-player-server');

let mainWindow;
const aiServer = new AIPlayerServer();

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 800,
    minWidth: 960,
    minHeight: 600,
    title: 'Crystal Cards',
    backgroundColor: '#0a0a1a',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
    icon: path.join(__dirname, '..', 'assets', 'icons', 'icon.png'),
    autoHideMenuBar: true,
  });

  mainWindow.loadFile(path.join(__dirname, 'index.html'));

  Menu.setApplicationMenu(null);

  // Connect AI player server to game window
  aiServer.setGameWindow(mainWindow);

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

app.whenReady().then(() => {
  createWindow();

  // Start AI player server
  aiServer.start();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  aiServer.stop();
  if (process.platform !== 'darwin') app.quit();
});

// IPC handlers
ipcMain.handle('get-settings', async () => {
  return {
    volume: 0.7,
    language: 'zh-TW',
    quality: 'high',
    showTutorial: true,
  };
});

ipcMain.handle('save-settings', async (_event, settings) => {
  console.log('Settings saved:', settings);
  return true;
});

ipcMain.handle('get-data-path', async () => {
  return path.join(__dirname, '..', 'game-data');
});
