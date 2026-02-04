const { app, BrowserWindow, ipcMain, screen, globalShortcut, systemPreferences, nativeTheme, Menu, Tray } = require('electron');
const path = require('path');
const fs = require('fs');

// Import Live2D Cubism Web SDK (will be loaded via CDN or local)
const LIVE2D_VERSION = '5.0.0';

let mainWindow;
let settingsWindow;
let isDevMode = false;
let modelPath = null;
let currentWallpaper = null;
let tray = null;

// App lifecycle
app.whenReady().then(() => {
  isDevMode = process.argv.includes('--dev');
  
  createMainWindow();
  
  // Create system tray
  createTray();
  
  // Register global shortcuts
  registerGlobalShortcuts();
  
  // Initialize system integrations
  initializeSystemIntegrations();
  
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
        createMainWindow();
    }
  });
});

app.on('window-all-closed', () => {
  // Don't quit on macOS, just hide to tray
  if (process.platform === 'darwin') {
    if (mainWindow) {
      mainWindow.hide();
    }
  } else {
    // On Windows/Linux, hide to tray instead of quitting
    if (mainWindow) {
      mainWindow.hide();
      // Don't quit, just hide to tray
      return;
    }
    app.quit();
  }
});

app.on('before-quit', (e) => {
  // Clean up before quit
  if (tray) {
    tray.destroy();
    tray = null;
  }
  cleanupResources();
});

/**
 * Create the main desktop pet window
 */
function createMainWindow() {
  const { width, height } = screen.getPrimaryDisplay().workAreaSize;
  
  mainWindow = new BrowserWindow({
    width: 400,
    height: 600,
    x: width - 450,
    y: height - 650,
    transparent: true,
    frame: false,
    resizable: false,
    alwaysOnTop: false,
    skipTaskbar: true,
    acceptFirstMouse: true,
    titleBarStyle: 'hiddenInset',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
      webSecurity: true
    }
  });
  
  // Set click-through regions initially
  mainWindow.setIgnoreMouseEvents(true);
  
  // Load the app
  mainWindow.loadFile('index.html');
  
  // Open DevTools in development mode
  if (isDevMode) {
    mainWindow.webContents.openDevTools();
  }
  
  // Handle window position saving
  mainWindow.on('moved', () => {
    const bounds = mainWindow.getBounds();
    saveWindowPosition(bounds);
  });
  
  // Handle mouse events for click-through
  mainWindow.on('ready-to-show', () => {
    mainWindow.webContents.send('window-ready', {
      bounds: mainWindow.getBounds()
    });
  });
}

/**
 * Create system tray with context menu
 */
function createTray() {
  // Create tray icon (using base64 for simplicity)
  const iconPath = getTrayIconPath();
  tray = new Tray(iconPath);
  
  // Create context menu
  const contextMenu = Menu.buildFromTemplate([
    {
      label: 'Show Angela',
      click: () => {
        if (mainWindow) {
          mainWindow.show();
          mainWindow.focus();
        }
      }
    },
    {
      label: 'Hide Angela',
      click: () => {
        if (mainWindow) {
          mainWindow.hide();
        }
      }
    },
    { type: 'separator' },
    {
      label: 'Settings',
      click: () => {
        createSettingsWindow();
      }
    },
    {
      label: 'Reload Model',
      click: () => {
        if (mainWindow) {
          mainWindow.webContents.send('reload-model');
        }
      }
    },
    {
      label: 'Auto-startup',
      type: 'checkbox',
      checked: getAutoStartupStatus(),
      click: () => {
        const currentStatus = getAutoStartupStatus();
        setAutoStartup(!currentStatus);
        // Update menu item
        createTray();
      }
    },
    { type: 'separator' },
    {
      label: 'Toggle Always on Top',
      click: () => {
        if (mainWindow) {
          const current = mainWindow.isAlwaysOnTop();
          mainWindow.setAlwaysOnTop(!current);
          mainWindow.webContents.send('always-on-top-changed', { alwaysOnTop: !current });
        }
      }
    },
    {
      label: 'Toggle Frame',
      click: () => {
        if (mainWindow) {
          const current = mainWindow.isFrameless();
          mainWindow.setFrameable(!current);
        }
      }
    },
    { type: 'separator' },
    {
      label: 'About',
      click: () => {
        app.showAboutPanel();
      }
    },
    {
      label: 'Check for Updates',
      click: () => {
        console.log('Checking for updates...');
      }
    },
    { type: 'separator' },
    {
      label: 'Restart',
      click: () => {
        app.relaunch();
        app.exit();
      }
    },
    {
      label: 'Quit',
      click: () => {
        app.quit();
      }
    }
  ]);
  
  tray.setContextMenu(contextMenu);
  tray.setToolTip('Angela AI - Your Virtual Companion');
  
  // Double click to show window
  tray.on('double-click', () => {
    if (mainWindow) {
      if (mainWindow.isVisible()) {
        mainWindow.hide();
      } else {
        mainWindow.show();
        mainWindow.focus();
      }
    }
  });
  
  console.log('System tray created');
}

/**
 * Get tray icon path based on platform
 */
function getTrayIconPath() {
  const iconName = process.platform === 'win32' ? 'icon.ico' : 
                   process.platform === 'darwin' ? 'icon.icns' : 'icon.png';
  
  // Try to find icon in assets directory
  const iconPath = path.join(__dirname, 'assets', iconName);
  
  if (fs.existsSync(iconPath)) {
    return iconPath;
  }
  
  // Fallback to app icon
  if (process.platform === 'win32') {
    return path.join(__dirname, '..', '..', 'resources', 'icon.ico');
  } else if (process.platform === 'darwin') {
    return path.join(__dirname, '..', '..', 'resources', 'icon.icns');
  } else {
    return path.join(__dirname, '..', '..', 'resources', 'icon.png');
  }
}

/**
 * Create settings window
 */
function createSettingsWindow() {
  if (settingsWindow) {
    settingsWindow.focus();
    return;
  }
  
  settingsWindow = new BrowserWindow({
    width: 800,
    height: 600,
    parent: mainWindow,
    modal: true,
    frame: true,
    resizable: true,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false
    }
  });
  
  settingsWindow.loadFile('settings.html');
  
  settingsWindow.on('closed', () => {
    settingsWindow = null;
  });
}

/**
 * Register global keyboard shortcuts
 */
function registerGlobalShortcuts() {
  // Toggle visibility
  globalShortcut.register('CommandOrControl+Shift+A', () => {
    if (mainWindow) {
      mainWindow.isVisible() ? mainWindow.hide() : mainWindow.show();
    }
  });
  
  // Open settings
  globalShortcut.register('CommandOrControl+Shift+S', () => {
    createSettingsWindow();
  });
  
  // Exit app
  globalShortcut.register('CommandOrControl+Shift+Q', () => {
    app.quit();
  });
}

/**
 * Initialize system-level integrations
 */
function initializeSystemIntegrations() {
  // Request necessary permissions
  if (process.platform === 'darwin') {
    // macOS permissions
    systemPreferences.askForMediaAccess('camera');
    systemPreferences.askForMediaAccess('microphone');
  }
  
  // Detect screen size changes
  screen.on('display-metrics-changed', () => {
    const { width, height } = screen.getPrimaryDisplay().workAreaSize;
    mainWindow.webContents.send('screen-changed', { width, height });
  });
  
  // Detect system theme changes
  nativeTheme.on('updated', () => {
    mainWindow.webContents.send('theme-changed', {
      shouldUseDarkColors: nativeTheme.shouldUseDarkColors
    });
  });
}

/**
 * Auto-startup management
 */
function setAutoStartup(enable) {
  if (process.platform === 'win32') {
    // Windows: use registry or task scheduler
    // Electron's app.setLoginItemSettings() handles this
    app.setLoginItemSettings({
      openAtLogin: enable,
      openAsHidden: enable
    });
  } else if (process.platform === 'darwin') {
    // macOS: use login item
    app.setLoginItemSettings({
      openAtLogin: enable,
      openAsHidden: enable
    });
  } else if (process.platform === 'linux') {
    // Linux: create autostart .desktop file
    const autostartDir = path.join(app.getPath('home'), '.config', 'autostart');
    const autostartFile = path.join(autostartDir, 'angela-ai.desktop');
    
    if (enable) {
      // Create autostart .desktop file
      const desktopEntry = `[Desktop Entry]
Type=Application
Name=Angela AI
Exec="${process.execPath}"
Icon="${path.join(__dirname, 'assets', 'icon.png')}"
X-GNOME-Autostart-enabled=true
`;
      
      try {
        if (!fs.existsSync(autostartDir)) {
          fs.mkdirSync(autostartDir, { recursive: true });
        }
        fs.writeFileSync(autostartFile, desktopEntry);
      } catch (e) {
        console.error('Failed to create autostart file:', e);
      }
    } else {
      // Remove autostart file
      try {
        if (fs.existsSync(autostartFile)) {
          fs.unlinkSync(autostartFile);
        }
      } catch (e) {
        console.error('Failed to remove autostart file:', e);
      }
    }
  }
}

function getAutoStartupStatus() {
  if (process.platform === 'win32' || process.platform === 'darwin') {
    const settings = app.getLoginItemSettings();
    return settings.openAtLogin || false;
  } else if (process.platform === 'linux') {
    const autostartFile = path.join(app.getPath('home'), '.config', 'autostart', 'angela-ai.desktop');
    return fs.existsSync(autostartFile);
  }
  return false;
}

/**
 * Save/restore window position
 */
function saveWindowPosition(bounds) {
  const configPath = path.join(app.getPath('userData'), 'window-position.json');
  fs.writeFileSync(configPath, JSON.stringify(bounds));
}

function restoreWindowPosition() {
  const configPath = path.join(app.getPath('userData'), 'window-position.json');
  try {
    const data = fs.readFileSync(configPath, 'utf8');
    return JSON.parse(data);
  } catch {
    return null;
  }
}

/**
 * Cleanup resources before quit
 */
function cleanupResources() {
  globalShortcut.unregisterAll();
}

/**
 * IPC handlers for communication with renderer process
 */

// Window management
ipcMain.handle('window-minimize', () => {
  mainWindow.minimize();
});

ipcMain.handle('window-maximize', () => {
  if (mainWindow.isMaximized()) {
    mainWindow.unmaximize();
  } else {
    mainWindow.maximize();
  }
});

ipcMain.handle('window-close', () => {
  mainWindow.close();
});

ipcMain.handle('window-set-size', (event, { width, height }) => {
  mainWindow.setSize(width, height);
});

ipcMain.handle('window-set-position', (event, { x, y }) => {
  mainWindow.setPosition(x, y);
});

ipcMain.handle('window-set-always-on-top', (event, flag) => {
  mainWindow.setAlwaysOnTop(flag);
});

ipcMain.handle('window-set-ignore-mouse-events', (event, ignore, options = {}) => {
  mainWindow.setIgnoreMouseEvents(ignore, {
    forward: options.forward || true,
    translate: options.translate || false
  });
});

// Click-through regions
ipcMain.handle('set-click-through-regions', (event, regions) => {
  // Set transparent regions (where mouse events pass through)
  if (regions.length > 0) {
    mainWindow.setIgnoreMouseEvents(true, {
      forward: true,
      translate: false
    });
  } else {
    mainWindow.setIgnoreMouseEvents(false);
  }
  
  // Send regions to renderer for hit testing
  mainWindow.webContents.send('click-through-regions-updated', regions);
});

// Live2D model management
ipcMain.handle('live2d-load-model', async (event, modelPath) => {
  try {
    // Normalize path separators
    const normalizedModelPath = modelPath.replace(/\\/g, '/');
    const modelName = normalizedModelPath.split('/').pop();
    
    // Handle both direct model paths and model directories
    let fullPath;
    if (fs.statSync(path.join(__dirname, '..', '..', 'resources', 'models', normalizedModelPath)).isDirectory()) {
      // If it's a directory, check for runtime/ subdirectory (for miara_pro_en models)
      const runtimePath = path.join(__dirname, '..', '..', 'resources', 'models', normalizedModelPath, 'runtime');
      if (fs.existsSync(runtimePath)) {
        fullPath = runtimePath;
      } else {
        fullPath = path.join(__dirname, '..', '..', 'resources', 'models', normalizedModelPath);
      }
    } else {
      fullPath = path.join(__dirname, '..', '..', 'resources', 'models', modelPath);
    }
    
    if (fs.existsSync(fullPath)) {
      return { success: true, path: fullPath };
    }
    
    return { success: false, error: 'Model file not found' };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

ipcMain.handle('live2d-get-models', () => {
  const modelsDir = path.join(__dirname, '..', '..', 'resources', 'models');
  if (!fs.existsSync(modelsDir)) {
    return [];
  }
  
  return fs.readdirSync(modelsDir, { withFileTypes: true })
    .filter(dirent => dirent.isDirectory())
    .map(dirent => ({
      name: dirent.name,
      path: path.join(modelsDir, dirent.name)
    }));
});

ipcMain.handle('live2d-get-models', () => {
  const modelsDir = path.join(__dirname, '..', '..', '..', 'resources', 'models');
  if (!fs.existsSync(modelsDir)) {
    return [];
  }
  
  return fs.readdirSync(modelsDir, { withFileTypes: true })
    .filter(dirent => dirent.isDirectory())
    .map(dirent => ({
      name: dirent.name,
      path: path.join(modelsDir, dirent.name)
    }));
});

// Wallpaper management
ipcMain.handle('wallpaper-set', async (event, imagePath) => {
  try {
    // Don't actually change system wallpaper
    // Just store for non-destructive overlay
    currentWallpaper = imagePath;
    
    // Get current system wallpaper
    const systemWallpaper = await getSystemWallpaper();
    
    return {
      success: true,
      systemWallpaper: systemWallpaper,
      userWallpaper: imagePath
    };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

ipcMain.handle('wallpaper-get', async () => {
  try {
    const systemWallpaper = await getSystemWallpaper();
    return {
      systemWallpaper: systemWallpaper,
      userWallpaper: currentWallpaper
    };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

async function getSystemWallpaper() {
  // Platform-specific wallpaper detection
  if (process.platform === 'win32') {
    const { exec } = require('child_process');
    return new Promise((resolve) => {
      exec('reg query "HKEY_CURRENT_USER\\Control Panel\\Desktop" /v Wallpaper', (error, stdout) => {
        if (error) {
          resolve(null);
          return;
        }
        const match = stdout.match(/Wallpaper\s+REG_SZ\s+(.+)/);
        resolve(match ? match[1] : null);
      });
    });
  } else if (process.platform === 'darwin') {
    const { exec } = require('child_process');
    return new Promise((resolve) => {
      exec('defaults read com.apple.desktop Background', (error) => {
        // macOS wallpaper detection is complex, simplify for now
        resolve(null);
      });
    });
  } else {
    // Linux
    return null;
  }
}

// Screen information
ipcMain.handle('screen-get-displays', () => {
  return screen.getAllDisplays();
});

ipcMain.handle('screen-get-primary-display', () => {
  const display = screen.getPrimaryDisplay();
  return {
    id: display.id,
    bounds: display.bounds,
    workArea: display.workArea,
    scaleFactor: display.scaleFactor
  };
});

// System theme
ipcMain.handle('theme-get-current', () => {
  return {
    shouldUseDarkColors: nativeTheme.shouldUseDarkColors,
    shouldUseHighContrastColors: nativeTheme.shouldUseHighContrastColors,
    shouldUseInvertedColorScheme: nativeTheme.shouldUseInvertedColorScheme
  };
});

ipcMain.on('theme-set-source', (event, source) => {
  nativeTheme.themeSource = source;
});

// Settings window
ipcMain.on('settings-open', () => {
  createSettingsWindow();
});

ipcMain.on('settings-close', () => {
  if (settingsWindow) {
    settingsWindow.close();
  }
});

// Auto-startup management
ipcMain.handle('autostart-get', () => {
  return getAutoStartupStatus();
});

ipcMain.handle('autostart-set', (event, enable) => {
  setAutoStartup(enable);
  return { success: true, enabled: enable };
});

// Audio system (placeholder - will be expanded)
ipcMain.handle('audio-get-devices', async () => {
  // Will use node-core-audio or similar
  return {
    inputDevices: [],
    outputDevices: []
  };
});

// Haptic system (placeholder - will be expanded)
ipcMain.handle('haptic-get-devices', async () => {
  return {
    devices: []
  };
});

// File operations
ipcMain.handle('file-save-dialog', async (event, options) => {
  const result = await mainWindow.webContents.executeJavaScript(`
    new Promise((resolve) => {
      const { dialog } = require('electron').remote;
      dialog.showSaveDialog(mainWindow, ${JSON.stringify(options)}).then(resolve);
    });
  `);
  return result;
});

ipcMain.handle('file-open-dialog', async (event, options) => {
  const result = await mainWindow.webContents.executeJavaScript(`
    new Promise((resolve) => {
      const { dialog } = require('electron').remote;
      dialog.showOpenDialog(mainWindow, ${JSON.stringify(options)}).then(resolve);
    });
  `);
  return result;
});

// Backend API communication (WebSocket)
let wsClient = null;

ipcMain.on('websocket-connect', (event, { url }) => {
  // Connect to backend WebSocket
  // Will use ws or WebSocket library
  event.reply('websocket-connected', { success: true });
});

ipcMain.on('websocket-disconnect', () => {
  // Disconnect from backend WebSocket
});

ipcMain.on('websocket-send', (event, message) => {
  // Send message to backend
});

// Export for testing
if (module.exports) {
  module.exports = {
    createMainWindow,
    saveWindowPosition,
    restoreWindowPosition
  };
}
