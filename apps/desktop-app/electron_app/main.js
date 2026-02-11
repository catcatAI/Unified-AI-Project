const { app, BrowserWindow, ipcMain, screen, globalShortcut, systemPreferences, nativeTheme, Menu, Tray, nativeImage, protocol } = require('electron');
const path = require('path');
const fs = require('fs');
const securityManager = require('./js/security-manager');

// Global error handler for EPIPE (prevents crashes when writing to closed pipes)
process.on('uncaughtException', (err) => {
  if (err.code === 'EPIPE' || err.code === 'ECONNRESET') {
    console.warn('[Main] Ignored pipe error (renderer closed):', err.code);
  } else {
    console.error('[Main] Uncaught Exception:', err);
  }
});

// Import Live2D Cubism Web SDK (will be loaded via CDN or local)
const LIVE2D_VERSION = '5.0.0';

// 单实例锁 - 防止启动多个实例
const gotTheLock = app.requestSingleInstanceLock();

if (!gotTheLock) {
  console.log('[Main] Another instance is already running. Quitting...');
  app.quit();
  process.exit(0);
}

let mainWindow;
let settingsWindow;
let isDevMode = false;
let modelPath = null;
let currentWallpaper = null;
let currentWallpaperMode = '2D';
let currentPerformanceMode = 'standard';
let backendIP = '127.0.0.1';
let moduleStates = {
  vision: true,
  audio: true,
  tactile: true,
  action: true
};
let tray = null;

// FIX: Helper function to safely send to mainWindow
function sendToMainWindow(channel, data) {
  if (mainWindow && !mainWindow.isDestroyed() && mainWindow.webContents) {
    try {
      mainWindow.webContents.send(channel, data);
      return true;
    } catch (e) {
      console.warn(`[Main] Failed to send ${channel}:`, e.message);
      return false;
    }
  }
  return false;
}

// FIX: Helper function to safely call mainWindow methods
function safeMainWindowCall(callback) {
  if (mainWindow && !mainWindow.isDestroyed()) {
    try {
      callback(mainWindow);
      return true;
    } catch (e) {
      console.warn('[Main] Failed to call method on mainWindow:', e.message);
      return false;
    }
  }
  return false;
}

// 当第二个实例尝试启动时，将焦点转移到现有窗口
app.on('second-instance', (event, commandLine, workingDirectory) => {
  console.log('[Main] Second instance detected, focusing existing window');
  
  // FIX: Check if mainWindow exists and is valid before accessing
  if (mainWindow && !mainWindow.isDestroyed()) {
    if (mainWindow.isMinimized()) mainWindow.restore();
    mainWindow.focus();
  }
});

// App lifecycle
app.whenReady().then(async () => {
  isDevMode = process.argv.includes('--dev');
  
  // Enable GPU acceleration for WebGL
  app.commandLine.appendSwitch('enable-gpu-rasterization');
  app.commandLine.appendSwitch('enable-zero-copy');
  app.commandLine.appendSwitch('ignore-gpu-blacklist');
  app.commandLine.appendSwitch('enable-webgl2-compute-context');
  app.commandLine.appendSwitch('enable-webgl2');  // Enable WebGL 2.0
  app.commandLine.appendSwitch('enable-accelerated-2d-canvas');  // Accelerated 2D canvas
  app.commandLine.appendSwitch('enable-gpu-driver-bug-workarounds');  // Driver compatibility
  
  // Register file protocol for loading Live2D model files
  // Define allowed directories to prevent path traversal attacks
  const ALLOWED_DIRECTORIES = [
    require('path').join(__dirname, 'resources'),
    require('path').join(__dirname, 'resources/models'),
    require('path').join(__dirname, 'data'),
    require('path').join(__dirname, 'models'),
    require('path').join(__dirname, '..', '..', 'resources')
  ];

  protocol.registerFileProtocol('local', (request, callback) => {
    console.log('[Main] Local protocol request:', request.url);
    
    let urlPath = request.url;
    
    // First, decode the entire URL to handle Chinese characters properly
    // This must happen BEFORE we extract the path
    try {
      urlPath = decodeURIComponent(urlPath);
    } catch (e) {
      console.warn('[Main] Failed to decode URL:', urlPath);
      callback({ error: -2 }); // Failed to decode
      return;
    }
    
    console.log('[Main] Decoded URL:', urlPath);
    
    // Handle local://, local:///, local://// etc. formats (variable slashes)
    // After decoding, we need to remove the 'local:' prefix and any leading slashes
    if (urlPath.startsWith('local:')) {
      // Remove 'local:' prefix
      urlPath = urlPath.substring(6);
      
      // Remove all leading slashes (there can be 1-3 of them)
      while (urlPath.startsWith('/')) {
        urlPath = urlPath.substring(1);
      }
    }
    
    // Ensure path starts with /
    if (!urlPath.startsWith('/') && urlPath.indexOf('/') > -1) {
      urlPath = '/' + urlPath;
    }
    
    // Use path.normalize to clean the path, then path.resolve for absolute path
    const normalizedPath = require('path').normalize(urlPath);
    const filePath = require('path').resolve(normalizedPath);
    
    console.log('[Main] Local protocol resolved:', urlPath, '->', filePath);
    
    // SECURITY: Verify path is within allowed directories
    const isAllowed = ALLOWED_DIRECTORIES.some(allowedDir => {
      const relativePath = require('path').relative(allowedDir, filePath);
      // Path is allowed if it doesn't start with '..' (prevents path traversal)
      return !relativePath.startsWith('..');
    });
    
    if (!isAllowed) {
      console.error('[Main] Path traversal attempt blocked:', filePath);
      console.error('[Main] Requested path is outside allowed directories');
      callback({ error: -3 }); // Access denied
      return;
    }
    
    // Verify file exists
    if (require('fs').existsSync(filePath)) {
      callback({ path: filePath });
    } else {
      console.error('[Main] File not found:', filePath);
      
      // Try alternative path resolution for Chinese characters
      // If the path contains Chinese characters that weren't decoded properly
      if (urlPath.includes('%')) {
        console.warn('[Main] Trying alternative decode for remaining encoded characters...');
        try {
          const altPath = decodeURIComponent(urlPath);
          const altFilePath = require('path').resolve(require('path').normalize(altPath));
          console.warn('[Main] Alternative path:', altFilePath);
          
          if (require('fs').existsSync(altFilePath)) {
            callback({ path: altFilePath });
            return;
          }
        } catch (e2) {
          console.warn('[Main] Alternative decode failed:', e2);
        }
      }
      
      callback({ error: -6 }); // FILE_NOT_FOUND
    }
  });
  console.log('[Main] Local file protocol registered');
  
  // Initialize security manager (Key C sync)
  const userDataPath = app.getPath('userData');
  await securityManager.setup(userDataPath, backendIP);
  
  createMainWindow();
  
  // Create system tray
  createTray();
  
  // Register security handlers
  registerSecurityHandlers();
  
  // Register global shortcuts
  registerGlobalShortcuts();
  
  // Initialize system integrations
  initializeSystemIntegrations();
  
  // Auto-connect to backend WebSocket
  const wsUrl = `ws://${backendIP}:8000/ws`;
  console.log(`[Main] Auto-connecting to backend WebSocket: ${wsUrl}`);
  connectWebSocket(wsUrl);
  
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
        createMainWindow();
    }
  });
});

app.on('window-all-closed', () => {
  // Don't quit on macOS, just hide to tray
  if (process.platform === 'darwin') {
    if (mainWindow && !mainWindow.isDestroyed()) {
      mainWindow.hide();
    }
  } else {
    // On Windows/Linux, hide to tray instead of quitting
    if (mainWindow && !mainWindow.isDestroyed()) {
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
    x: Math.max(0, width - 450),
    y: Math.max(0, height - 650),
    transparent: false,  // Disable transparency for WebGL support
    frame: false,
    resizable: true,  // Enable resizing
    alwaysOnTop: true,
    skipTaskbar: false,
    acceptFirstMouse: true,
    titleBarStyle: 'hiddenInset',
    show: false,
    backgroundColor: '#00000000',  // Transparent background color
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false,
      webSecurity: true,
      // Enable WebGL 2.0 and hardware acceleration
      webgl: true,
      enableWebGL2: true,
      hardwareAcceleration: 'force',
      experimentalFeatures: true
    }
  });
  
  console.log('[Window] Creating window with bounds:', mainWindow.getBounds());
  
  // Set minimum size
  mainWindow.setMinimumSize(200, 300);
  
  // Enable draggable region
  mainWindow.setSkipTaskbar(false);
  
  // Load the app
  console.log('[Window] Loading index.html...');
  mainWindow.loadFile('index.html');
  
  // Log when page is loaded
  mainWindow.webContents.on('did-finish-load', () => {
    console.log('[Window] Page loaded successfully');
  });
  
  // Add right-click context menu for main window
  mainWindow.webContents.on('context-menu', (event, params) => {
    event.preventDefault();
    
    // Safety check
    if (!mainWindow || mainWindow.isDestroyed()) {
      console.warn('[ContextMenu] mainWindow is null or destroyed');
      return;
    }
    
    try {
    const contextMenu = Menu.buildFromTemplate([
      {
        label: 'Show/Hide Angela',
        click: () => {
          if (mainWindow.isVisible()) {
            mainWindow.hide();
          } else {
            mainWindow.show();
            mainWindow.focus();
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
          sendToMainWindow('reload-model');
        }
      },
      { type: 'separator' },
      {
        label: 'Toggle Always on Top',
        click: () => {
          const current = mainWindow.isAlwaysOnTop();
          mainWindow.setAlwaysOnTop(!current);
          sendToMainWindow('always-on-top-changed', { alwaysOnTop: !current });
        }
      },
      {
        label: 'Toggle Frame',
        click: () => {
          const current = mainWindow.isFrameless();
          mainWindow.setFrameable(!current);
        }
      },
      { type: 'separator' },
      {
        label: 'Performance Mode',
        submenu: [
          { label: 'Lite', type: 'radio', checked: currentPerformanceMode === 'lite', click: () => setPerformanceMode('lite') },
          { label: 'Standard', type: 'radio', checked: currentPerformanceMode === 'standard', click: () => setPerformanceMode('standard') },
          { label: 'Extended', type: 'radio', checked: currentPerformanceMode === 'extended', click: () => setPerformanceMode('extended') },
          { label: 'Ultra', type: 'radio', checked: currentPerformanceMode === 'ultra', click: () => setPerformanceMode('ultra') }
        ]
      },
      {
        label: 'Wallpaper Mode',
        submenu: [
          { label: '2D (Basic)', type: 'radio', checked: currentWallpaperMode === '2D', click: () => setWallpaperMode('2D') },
          { label: '2.5D (Parallax)', type: 'radio', checked: currentWallpaperMode === '2.5D', click: () => setWallpaperMode('2.5D') },
          { label: '3D (Full)', type: 'radio', checked: currentWallpaperMode === '3D', click: () => setWallpaperMode('3D') }
        ]
      },
      { type: 'separator' },
      {
        label: 'Modules',
        submenu: [
          { label: 'Vision System', type: 'checkbox', checked: moduleStates.vision, click: (item) => toggleModule('vision', item.checked) },
          { label: 'Audio System', type: 'checkbox', checked: moduleStates.audio, click: (item) => toggleModule('audio', item.checked) },
          { label: 'Tactile System', type: 'checkbox', checked: moduleStates.tactile, click: (item) => toggleModule('tactile', item.checked) },
          { label: 'Action Executor', type: 'checkbox', checked: moduleStates.action, click: (item) => toggleModule('action', item.checked) }
        ]
      },
      { type: 'separator' },
      {
        label: 'Auto-startup',
        type: 'checkbox',
        checked: getAutoStartupStatus(),
        click: (item) => {
          const currentStatus = getAutoStartupStatus();
          setAutoStartup(!currentStatus);
          createTray(); // Refresh tray menu
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
    
    contextMenu.popup(mainWindow);
    } catch (error) {
      console.error('[ContextMenu] Error showing context menu:', error.message);
    }
  });
  
  // Log any page load errors
  mainWindow.webContents.on('did-fail-load', (event, errorCode, errorDescription) => {
    console.error('[Window] Page load failed:', errorCode, errorDescription);
  });
  
  // Log console messages from renderer
  mainWindow.webContents.on('console-message', (event, level, message, line, sourceId) => {
    // Skip if window is destroyed to avoid EPIPE error
    if (mainWindow.isDestroyed()) return;
    console.log(`[Renderer] ${message}`);
  });
  
  // Wait for ready-to-show before showing
  mainWindow.on('ready-to-show', () => {
    console.log('[Window] Window ready to show, showing now...');
    mainWindow.show();
    mainWindow.setAlwaysOnTop(true);
    mainWindow.focus();
    console.log('[Window] Window shown with bounds:', mainWindow.getBounds());
    
    // Open DevTools for debugging
    mainWindow.webContents.openDevTools();
    
    sendToMainWindow('window-ready', {
      bounds: safeMainWindowCall(w => w.getBounds()) || mainWindow.getBounds()
    });
  });
  
  // Handle window position saving
  mainWindow.on('moved', () => {
    const bounds = mainWindow.getBounds();
    console.log('[Window] Window moved to:', bounds);
    saveWindowPosition(bounds);
  });
  
  // Open DevTools in development mode
  if (isDevMode) {
    mainWindow.webContents.openDevTools();
  }
}

/**
 * Create system tray with context menu
 */
function createTray() {
  try {
    const iconPath = getTrayIconPath();
    if (fs.existsSync(iconPath)) {
      tray = new Tray(iconPath);
    } else {
      // Fallback to an empty image if icon not found
      tray = new Tray(nativeImage.createEmpty());
      console.warn('Tray icon not found, using empty placeholder');
    }
  } catch (error) {
    console.error('Failed to create tray:', error);
    // Don't crash the whole app if tray fails
    return;
  }
  
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
      label: 'Advanced Settings',
      submenu: [
        {
          label: 'Connection',
          submenu: [
            { label: `IP: ${backendIP}`, enabled: false },
            { label: 'Set to localhost (127.0.0.1)', click: () => setBackendIP('127.0.0.1') },
            { label: 'Custom IP...', click: () => createSettingsWindow('advanced') }
          ]
        },
        { type: 'separator' },
        {
          label: 'Open Advanced Tab',
          click: () => createSettingsWindow('advanced')
        }
      ]
    },
    {
      label: 'Hardware & Performance',
      submenu: [
        {
          label: 'Performance Mode',
          submenu: [
            { label: 'Lite', type: 'radio', checked: currentPerformanceMode === 'lite', click: () => setPerformanceMode('lite') },
            { label: 'Standard', type: 'radio', checked: currentPerformanceMode === 'standard', click: () => setPerformanceMode('standard') },
            { label: 'Extended', type: 'radio', checked: currentPerformanceMode === 'extended', click: () => setPerformanceMode('extended') },
            { label: 'Ultra', type: 'radio', checked: currentPerformanceMode === 'ultra', click: () => setPerformanceMode('ultra') }
          ]
        },
        {
          label: 'Wallpaper Rendering',
          submenu: [
            { label: '2D (Basic)', type: 'radio', checked: currentWallpaperMode === '2D', click: () => setWallpaperMode('2D') },
            { label: '2.5D (Parallax)', type: 'radio', checked: currentWallpaperMode === '2.5D', click: () => setWallpaperMode('2.5D') },
            { label: '3D (Full)', type: 'radio', checked: currentWallpaperMode === '3D', click: () => setWallpaperMode('3D') }
          ]
        },
        { type: 'separator' },
        { label: 'Auto-adjust', type: 'checkbox', checked: true, click: (item) => {
          sendToMainWindow('performance-auto-adjust', item.checked);
        }}
      ]
    },
    {
      label: 'Angela Matrix',
      submenu: [
        { label: 'Vision System', type: 'checkbox', checked: moduleStates.vision, click: (item) => toggleModule('vision', item.checked) },
        { label: 'Audio System', type: 'checkbox', checked: moduleStates.audio, click: (item) => toggleModule('audio', item.checked) },
        { label: 'Tactile System', type: 'checkbox', checked: moduleStates.tactile, click: (item) => toggleModule('tactile', item.checked) },
        { label: 'Action Executor', type: 'checkbox', checked: moduleStates.action, click: (item) => toggleModule('action', item.checked) }
      ]
    },
    {
      label: 'Reload Model',
      click: () => {
        sendToMainWindow('reload-model');
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
          sendToMainWindow('always-on-top-changed', { alwaysOnTop: !current });
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
function createSettingsWindow(tab = 'general') {
  if (settingsWindow) {
    settingsWindow.focus();
    if (tab) {
      settingsWindow.webContents.send('open-tab', tab);
    }
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
  
  settingsWindow.loadFile('settings.html', { query: { tab } });
  
  settingsWindow.on('closed', () => {
    settingsWindow = null;
  });
}

/**
 * Register security related IPC handlers
 */
function registerSecurityHandlers() {
  ipcMain.handle('security:init', (event, keyC) => {
    try {
      securityManager.init(keyC);
      return { success: true };
    } catch (error) {
      return { success: false, error: error.message };
    }
  });

  ipcMain.handle('security:is-initialized', () => {
    return securityManager.isInitialized();
  });

  ipcMain.handle('security:sync', async () => {
    const result = await securityManager.syncFromBackend(backendIP);
    return { success: result };
  });

  ipcMain.handle('security:encrypt', (event, data) => {
    try {
      return { success: true, data: securityManager.encrypt(data) };
    } catch (error) {
      return { success: false, error: error.message };
    }
  });

  ipcMain.handle('security:decrypt', (event, encryptedData) => {
    try {
      return { success: true, data: securityManager.decrypt(encryptedData) };
    } catch (error) {
      return { success: false, error: error.message };
    }
  });
}

/**
 * Register global shortcuts
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
    sendToMainWindow('screen-changed', { width, height });
  });
  
  // Detect system theme changes
  nativeTheme.on('updated', () => {
    sendToMainWindow('theme-changed', {
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
 * Hardware & Performance settings helpers
 */
function setPerformanceMode(mode) {
  currentPerformanceMode = mode;
  sendToMainWindow('performance-mode-changed', mode);
  createTray(); // Refresh menu
}

function setWallpaperMode(mode) {
  currentWallpaperMode = mode;
  sendToMainWindow('wallpaper-mode-changed', mode);
  createTray(); // Refresh menu
}

function toggleModule(module, enabled) {
  moduleStates[module] = enabled;
  sendToMainWindow('module-toggle', { module, enabled });
  createTray(); // Refresh menu
}

function setBackendIP(ip) {
  backendIP = ip;
  sendToMainWindow('backend-ip-changed', ip);
  createTray(); // Refresh menu
}

/**
 * IPC handlers for communication with renderer process
 */

// Performance & Wallpaper Mode
ipcMain.handle('performance-get-mode', () => currentPerformanceMode);
ipcMain.handle('performance-set-mode', (event, mode) => {
  setPerformanceMode(mode);
  return { success: true };
});

ipcMain.handle('wallpaper-get-mode', () => currentWallpaperMode);
ipcMain.handle('wallpaper-set-mode', (event, mode) => {
  setWallpaperMode(mode);
  return { success: true };
});

ipcMain.handle('module-set-state', (event, { module, enabled }) => {
  moduleStates[module] = enabled;
  createTray(); // Refresh menu
  return { success: true };
});

ipcMain.handle('backend-get-ip', () => backendIP);
ipcMain.handle('backend-set-ip', (event, ip) => {
  backendIP = ip;
  createTray(); // Refresh menu
  return { success: true };
});

ipcMain.handle('wallpaper-inject-object', (event, objectData) => {
  if (sendToMainWindow('wallpaper-inject-object', objectData)) {
    return { success: true };
  }
  return { success: false, error: 'Main window not available' };
});

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

ipcMain.handle('window-get-position', () => {
  const [x, y] = mainWindow.getPosition();
  return { x, y };
});

ipcMain.handle('window-get-bounds', () => {
  return mainWindow.getBounds();
});

ipcMain.handle('window-set-size-and-center', (event, { width, height }) => {
  const { width: screenWidth, height: screenHeight } = screen.getPrimaryDisplay().workAreaSize;
  const x = Math.max(0, screenWidth - width - 50);
  const y = Math.max(0, screenHeight - height - 50);
  mainWindow.setBounds({ x, y, width, height });
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
  try {
    // Set transparent regions (where mouse events pass through)
    if (regions && regions.length > 0) {
      // 将穿透区域转换为skipRegions（不穿透的区域）
      // Electron的skipRegions参数指定哪些区域不忽略鼠标事件
      const skipRegions = regions.map(region => ({
        x: Math.floor(region.x),
        y: Math.floor(region.y),
        width: Math.ceil(region.width),
        height: Math.ceil(region.height)
      }));
      
      mainWindow.setIgnoreMouseEvents(true, {
        forward: true,
        translate: false,
        skipRegions: skipRegions
      });
      
      console.log('[Main] 点击穿透区域已设置:', skipRegions.length, '个区域');
    } else {
      mainWindow.setIgnoreMouseEvents(false);
      console.log('[Main] 点击穿透已禁用');
    }
    
    // Send regions to renderer for hit testing
    sendToMainWindow('click-through-regions-updated', regions);
  } catch (error) {
    console.error('[Main] 设置点击穿透区域失败:', error);
    // 失败时恢复默认行为
    mainWindow.setIgnoreMouseEvents(false);
  }
});

// Live2D model management
ipcMain.handle('live2d-load-model', async (event, modelPath) => {
  try {
    // Normalize path separators
    const normalizedModelPath = modelPath.replace(/\\/g, '/');

    // Correctly resolve models directory relative to project root
    // apps/desktop-app/electron_app -> ../../../resources/models
    const projectRoot = path.join(__dirname, '..', '..', '..');
    const modelsDir = path.join(projectRoot, 'resources', 'models');

    // Check if modelPath is already a full path or relative
    let fullPath;
    if (normalizedModelPath.startsWith('/') || normalizedModelPath.includes(':')) {
      // Already a full path
      fullPath = normalizedModelPath;
    } else if (normalizedModelPath.startsWith('resources/')) {
      // Relative path starting with resources/
      fullPath = path.join(projectRoot, normalizedModelPath);
    } else if (normalizedModelPath.includes('/')) {
      // Relative path with directory
      fullPath = path.join(modelsDir, normalizedModelPath);
    } else {
      // Just a model name, find in modelsDir
      const modelDir = path.join(modelsDir, normalizedModelPath);
      if (fs.existsSync(modelDir) && fs.statSync(modelDir).isDirectory()) {
        // It's a directory, find the model file
        const modelFiles = fs.readdirSync(modelDir).filter(f => f.endsWith('.model3.json'));
        const modelFile = modelFiles.find(f => f.includes('_t03')) || modelFiles[0];
        if (modelFile) {
          fullPath = path.join(modelDir, modelFile);
        } else {
          fullPath = modelDir;
        }
      } else {
        fullPath = path.join(modelsDir, normalizedModelPath);
      }
    }

    // If it's a directory, check for model file
    if (fs.existsSync(fullPath) && fs.statSync(fullPath).isDirectory()) {
      // Check for runtime/ subdirectory or model file
      const runtimePath = path.join(fullPath, 'runtime');
      if (fs.existsSync(runtimePath)) {
        fullPath = runtimePath;
      } else {
        // Find model3.json in this directory
        const modelFiles = fs.readdirSync(fullPath).filter(f => f.endsWith('.model3.json'));
        const modelFile = modelFiles.find(f => f.includes('_t03')) || modelFiles[0];
        if (modelFile) {
          fullPath = path.join(fullPath, modelFile);
        }
      }
    }

    if (fs.existsSync(fullPath)) {
      console.log(`[Main] Loading Live2D model from: ${fullPath}`);

      // Convert file path to file URL for renderer
      const fileUrl = `file://${fullPath}`;
      console.log(`[Main] Converting to URL: ${fileUrl}`);

      return { success: true, path: fullPath, url: fileUrl };
    }

    console.warn(`[Main] Model path not found: ${fullPath}`);
    return { success: false, error: 'Model file not found' };
  } catch (error) {
    console.error(`[Main] Error loading Live2D model: ${error.message}`);
    return { success: false, error: error.message };
  }
});

ipcMain.handle('live2d-get-models', () => {
  const modelsDir = path.join(__dirname, '..', '..', '..', 'resources', 'models');
  console.log(`[Main] Searching for models in: ${modelsDir}`);

  if (!fs.existsSync(modelsDir)) {
    console.warn(`[Main] Models directory not found: ${modelsDir}`);
    return [];
  }

  // Helper function to find model3.json recursively
  function findModelJson(dir, baseName) {
    // First check root of model dir
    const rootPath = path.join(dir, String(baseName) + '.model3.json');
    if (fs.existsSync(rootPath)) {
      return { foundPath: String(baseName) + '.model3.json', subdir: '' };
    }

    // Check runtime/ subdirectory (Epsilon style)
    const runtimePath = path.join(dir, 'runtime', String(baseName) + '.model3.json');
    if (fs.existsSync(runtimePath)) {
      return { foundPath: 'runtime/' + String(baseName) + '.model3.json', subdir: 'runtime' };
    }

    // Try any .model3.json file in root
    const entries = fs.readdirSync(dir, { withFileTypes: true });
    const modelJsonFiles = entries
      .filter(e => e.isFile() && String(e.name).endsWith('.model3.json'))
      .map(e => String(e.name));

    if (modelJsonFiles.length > 0 && modelJsonFiles[0]) {
      return { foundPath: String(modelJsonFiles[0]), subdir: '' };
    }

    // Try .model3.json in subdirectories
    const subdirs = entries.filter(e => e.isDirectory()).map(e => String(e.name));
    for (const subdirName of subdirs) {
      const subdirPath = path.join(dir, String(subdirName));
      const files = fs.readdirSync(subdirPath, { withFileTypes: true });
      const jsonFiles = files
        .filter(e => e.isFile() && String(e.name).endsWith('.model3.json'))
        .map(e => String(e.name));
      if (jsonFiles.length > 0 && jsonFiles[0]) {
        return { foundPath: path.join(String(subdirName), String(jsonFiles[0])), subdir: String(subdirName) };
      }
    }

    return null;
  }

  const models = fs.readdirSync(modelsDir, { withFileTypes: true })
    .filter(dirent => dirent.isDirectory())
    .map(dirent => {
      const modelDir = path.join(modelsDir, dirent.name);
      const result = findModelJson(modelDir, dirent.name);

      if (result) {
        const relativePath = path.join('resources', 'models', dirent.name, result.foundPath);
        console.log(`[Main] Found model: ${dirent.name}, relative path: ${relativePath}`);

        return {
          name: dirent.name,
          path: relativePath,
          fullPath: path.join(modelDir, result.foundPath)
        };
      }

      return {
        name: dirent.name,
        path: path.join('resources', 'models', dirent.name),
        fullPath: modelDir
      };
    })
    .filter(m => m.path.endsWith('.model3.json'));

  console.log(`[Main] Found ${models.length} models`);
  return models;
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
const WebSocket = require('ws');
let wsClient = null;
let wsReconnectTimer = null;
let wsReconnectAttempts = 0;
const WS_MAX_RECONNECT_ATTEMPTS = 5;
const WS_RECONNECT_DELAY = 3000;

function connectWebSocket(url) {
  if (wsClient && wsClient.readyState === WebSocket.OPEN) {
    console.log('[WebSocket] Already connected');
    return;
  }

  try {
    console.log(`[WebSocket] Connecting to ${url}...`);
    wsClient = new WebSocket(url);

    wsClient.on('open', () => {
      console.log('[WebSocket] Connected successfully');
      wsReconnectAttempts = 0;
      // Skip sending if window is destroyed
      if (!mainWindow || mainWindow.isDestroyed()) return;
      sendToMainWindow('websocket-connected', { success: true });
    });

    wsClient.on('message', (data) => {
      // Skip if window is destroyed
      if (!mainWindow || mainWindow.isDestroyed()) return;

      try {
        const message = JSON.parse(data.toString());
        console.log('[WebSocket] Received:', message);
        sendToMainWindow('websocket-message', message);
      } catch (error) {
        console.error('[WebSocket] Failed to parse message:', error);
      }
    });

    wsClient.on('error', (error) => {
      console.error('[WebSocket] Error:', error.message);
      // Skip sending if window is destroyed
      if (!mainWindow || mainWindow.isDestroyed()) return;
      sendToMainWindow('websocket-error', { error: error.message });
    });

    wsClient.on('close', (code, reason) => {
      console.log(`[WebSocket] Closed: ${code} - ${reason}`);
      wsClient = null;
      
      // Skip sending if window is destroyed
      if (!mainWindow || mainWindow.isDestroyed()) return;
      
      sendToMainWindow('websocket-disconnected', { code, reason: reason.toString() });

      // Auto-reconnect
      if (wsReconnectAttempts < WS_MAX_RECONNECT_ATTEMPTS) {
        wsReconnectAttempts++;
        console.log(`[WebSocket] Reconnecting in ${WS_RECONNECT_DELAY}ms (attempt ${wsReconnectAttempts}/${WS_MAX_RECONNECT_ATTEMPTS})...`);
        wsReconnectTimer = setTimeout(() => {
          connectWebSocket(url);
        }, WS_RECONNECT_DELAY);
      } else {
        console.error('[WebSocket] Max reconnection attempts reached');
      }
    });
  } catch (error) {
    console.error('[WebSocket] Connection failed:', error);
    sendToMainWindow('websocket-error', { error: error.message });
  }
}

function disconnectWebSocket() {
  if (wsReconnectTimer) {
    clearTimeout(wsReconnectTimer);
    wsReconnectTimer = null;
  }
  
  if (wsClient) {
    wsClient.close();
    wsClient = null;
  }
  
  wsReconnectAttempts = 0;
}

function sendWebSocketMessage(message) {
  if (!wsClient || wsClient.readyState !== WebSocket.OPEN) {
    console.error('[WebSocket] Not connected');
    return false;
  }

  try {
    wsClient.send(JSON.stringify(message));
    return true;
  } catch (error) {
    console.error('[WebSocket] Failed to send message:', error);
    return false;
  }
}

ipcMain.on('websocket-connect', (event, { url }) => {
  connectWebSocket(url);
});

ipcMain.on('websocket-disconnect', () => {
  disconnectWebSocket();
});

ipcMain.on('websocket-send', (event, message) => {
  const success = sendWebSocketMessage(message);
  event.reply('websocket-send-result', { success });
});

ipcMain.handle('websocket-get-status', () => {
  return {
    connected: wsClient && wsClient.readyState === WebSocket.OPEN,
    reconnectAttempts: wsReconnectAttempts
  };
});

// Export for testing
if (module.exports) {
  module.exports = {
    createMainWindow,
    saveWindowPosition,
    restoreWindowPosition
  };
}
