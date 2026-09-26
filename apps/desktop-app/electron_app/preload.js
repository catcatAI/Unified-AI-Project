/**
 * Angela AI Desktop App - Preload Script
 *
 * Provides secure IPC communication between main and renderer processes
 */

const log = require('electron-log')
const { contextBridge, ipcRenderer } = require('electron')

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electronAPI', {
  // Window management
  window: {
    minimize: () => ipcRenderer.invoke('window-minimize'),
    maximize: () => ipcRenderer.invoke('window-maximize'),
    restore: () => ipcRenderer.invoke('window-restore'),
    close: () => ipcRenderer.invoke('window-close'),
    setSize: (width, height) => ipcRenderer.invoke('window-set-size', { width, height }),
    setSizeAndCenter: (width, height) =>
      ipcRenderer.invoke('window-set-size-and-center', { width, height }),
    getPosition: () => ipcRenderer.invoke('window-get-position'),
    setPosition: (x, y) => ipcRenderer.invoke('window-set-position', { x, y }),
    getBounds: () => ipcRenderer.invoke('window-get-bounds'),
    setAlwaysOnTop: (flag) => ipcRenderer.invoke('window-set-always-on-top', flag),
    setIgnoreMouseEvents: (ignore, options) =>
      ipcRenderer.invoke('window-set-ignore-mouse-events', ignore, options),
    setClickThroughRegions: (regions) => ipcRenderer.invoke('set-click-through-regions', regions),
    setBounds: (bounds) => ipcRenderer.send('window-set-bounds', bounds),
    // Window opacity. Requires a transparent window, which main.js creates.
    setOpacity: (opacity) => ipcRenderer.invoke('window-set-opacity', opacity),
    getOpacity: () => ipcRenderer.invoke('window-get-opacity'),
  },

  // Live2D model management
  live2d: {
    loadModel: (modelPath) => ipcRenderer.invoke('live2d-load-model', modelPath),
    getModels: () => ipcRenderer.invoke('live2d-get-models'),
  },

  // Wallpaper management
  wallpaper: {
    set: (imagePath) => ipcRenderer.invoke('wallpaper-set', imagePath),
    get: () => ipcRenderer.invoke('wallpaper-get'),
    getMode: () => ipcRenderer.invoke('wallpaper-get-mode'),
    setMode: (mode) => ipcRenderer.invoke('wallpaper-set-mode', mode),
    injectObject: (objectData) => ipcRenderer.invoke('wallpaper-inject-object', objectData),
  },

  // Performance management
  performance: {
    getMode: () => ipcRenderer.invoke('performance-get-mode'),
    setMode: (mode) => ipcRenderer.invoke('performance-set-mode', mode),
  },

  // Module management
  modules: {
    setState: (module, enabled) => ipcRenderer.invoke('module-set-state', { module, enabled }),
  },

  // Backend settings
  backend: {
    getIP: () => ipcRenderer.invoke('backend-get-ip'),
    setIP: (ip) => ipcRenderer.invoke('backend-set-ip', ip),
  },

  // Screen information
  screen: {
    getDisplays: () => ipcRenderer.invoke('screen-get-displays'),
    getPrimaryDisplay: () => ipcRenderer.invoke('screen-get-primary-display'),
  },

  // System theme
  theme: {
    getCurrent: () => ipcRenderer.invoke('theme-get-current'),
    setSource: (source) => ipcRenderer.send('theme-set-source', source),
  },

  // Settings management
  settings: {
    open: () => ipcRenderer.send('settings-open'),
    close: () => ipcRenderer.send('settings-close'),
    getAll: () => ipcRenderer.invoke('settings-get-all'),
    setAll: (settings) => ipcRenderer.invoke('settings-set-all', settings),
    reset: () => ipcRenderer.invoke('settings-reset'),
  },

  // Auto-start (login item)
  // WHY this bridge exists: main.js has implemented setAutoStartup() and
  // getAutoStartupStatus() for win32/darwin/linux and exposed them as the
  // `autostart-set` / `autostart-get` handlers, but preload.js exposed no way to
  // reach them — so the "Start Angela at login" checkbox in settings.html saved a
  // value that nothing ever applied. The handler count in main.js was the only
  // evidence the feature existed.
  autostart: {
    get: () => ipcRenderer.invoke('autostart-get'),
    set: (enable) => ipcRenderer.invoke('autostart-set', enable),
  },

  // System (loopback) audio capture. Reports unsupported_platform on Linux
  // rather than handing back a silent stream.
  systemAudio: {
    start: () => ipcRenderer.invoke('system-audio-start'),
  },

  // Debug logging level, applied to electron-log in the main process.
  debug: {
    setLogLevel: (level) => ipcRenderer.invoke('debug-set-log-level', level),
    getLogLevel: () => ipcRenderer.invoke('debug-get-log-level'),
  },

  // Audio system
  audio: {
    getDevices: () => ipcRenderer.invoke('audio-get-devices'),
  },

  // Haptic system
  haptic: {
    getDevices: () => ipcRenderer.invoke('haptic-get-devices'),
  },

  // File operations
  file: {
    saveDialog: (options) => ipcRenderer.invoke('file-save-dialog', options),
    openDialog: (options) => ipcRenderer.invoke('file-open-dialog', options),
  },

  // Security management
  security: {
    init: (keyC) => ipcRenderer.invoke('security:init', keyC),
    isInitialized: () => ipcRenderer.invoke('security:is-initialized'),
    sync: () => ipcRenderer.invoke('security:sync'),
    encrypt: (data) => ipcRenderer.invoke('security:encrypt', data),
    decrypt: (encryptedData) => ipcRenderer.invoke('security:decrypt', encryptedData),
  },

  // Plugin management (C3)
  plugins: {
    list: () => ipcRenderer.invoke('plugins-list'),
    load: (name, code) => ipcRenderer.invoke('plugins-load', { name, code }),
    save: (name, code) => ipcRenderer.invoke('plugins-save', { name, code }),
    del: (name) => ipcRenderer.invoke('plugins-delete', name),
  },

  // WebSocket communication with backend
  websocket: {
    connect: (url, sessionInfo) => ipcRenderer.send('websocket-connect', { url, sessionInfo }),
    disconnect: () => ipcRenderer.send('websocket-disconnect'),
    send: (message) => ipcRenderer.send('websocket-send', message),
    getStatus: () => ipcRenderer.invoke('websocket-get-status'),
  },

  // Event listeners (receive messages from main process)
  on: (channel, callback) => {
    const validChannels = [
      'window-ready',
      'screen-changed',
      'theme-changed',
      'click-through-regions-updated',
      'websocket-connected',
      'websocket-message',
      'websocket-disconnected',
      'websocket-error',
      'websocket-send-result',
      'backend-ip-changed',
      'render-mode',
      'performance-mode-changed',
      'performance-auto-adjust',
      'wallpaper-mode-changed',
      'wallpaper-inject-object',
      'module-toggle',
      'plugins-changed',
      'reload-model',
      'always-on-top-changed',
    ]

    if (validChannels.includes(channel)) {
      ipcRenderer.on(channel, (event, ...args) => callback(...args))
    }
  },

  off: (channel, callback) => {
    ipcRenderer.removeListener(channel, callback)
  },
})

// Expose logging to renderer process
contextBridge.exposeInMainWorld('electronLog', {
  info: (...args) => log.info(...args),
  warn: (...args) => log.warn(...args),
  error: (...args) => log.error(...args),
  debug: (...args) => log.debug(...args),
})

log.info('ElectronAPI preload loaded successfully')
