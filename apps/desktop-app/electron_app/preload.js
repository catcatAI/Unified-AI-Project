/**
 * Angela AI Desktop App - Preload Script
 * 
 * Provides secure IPC communication between main and renderer processes
 */

const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electronAPI', {
  // Window management
  window: {
    minimize: () => ipcRenderer.invoke('window-minimize'),
    maximize: () => ipcRenderer.invoke('window-maximize'),
    close: () => ipcRenderer.invoke('window-close'),
    setSize: (width, height) => ipcRenderer.invoke('window-set-size', { width, height }),
    setPosition: (x, y) => ipcRenderer.invoke('window-set-position', { x, y }),
    setAlwaysOnTop: (flag) => ipcRenderer.invoke('window-set-always-on-top', flag),
    setIgnoreMouseEvents: (ignore, options) => ipcRenderer.invoke('window-set-ignore-mouse-events', ignore, options),
    setClickThroughRegions: (regions) => ipcRenderer.invoke('set-click-through-regions', regions)
  },
  
  // Live2D model management
  live2d: {
    loadModel: (modelPath) => ipcRenderer.invoke('live2d-load-model', modelPath),
    getModels: () => ipcRenderer.invoke('live2d-get-models')
  },
  
  // Wallpaper management
  wallpaper: {
    set: (imagePath) => ipcRenderer.invoke('wallpaper-set', imagePath),
    get: () => ipcRenderer.invoke('wallpaper-get')
  },
  
  // Screen information
  screen: {
    getDisplays: () => ipcRenderer.invoke('screen-get-displays'),
    getPrimaryDisplay: () => ipcRenderer.invoke('screen-get-primary-display')
  },
  
  // System theme
  theme: {
    getCurrent: () => ipcRenderer.invoke('theme-get-current'),
    setSource: (source) => ipcRenderer.send('theme-set-source', source)
  },
  
  // Settings window
  settings: {
    open: () => ipcRenderer.send('settings-open'),
    close: () => ipcRenderer.send('settings-close')
  },
  
  // Audio system
  audio: {
    getDevices: () => ipcRenderer.invoke('audio-get-devices')
  },
  
  // Haptic system
  haptic: {
    getDevices: () => ipcRenderer.invoke('haptic-get-devices')
  },
  
  // File operations
  file: {
    saveDialog: (options) => ipcRenderer.invoke('file-save-dialog', options),
    openDialog: (options) => ipcRenderer.invoke('file-open-dialog', options)
  },
  
  // WebSocket communication with backend
  websocket: {
    connect: (url) => ipcRenderer.send('websocket-connect', { url }),
    disconnect: () => ipcRenderer.send('websocket-disconnect'),
    send: (message) => ipcRenderer.send('websocket-send', message)
  },
  
  // Event listeners (receive messages from main process)
  on: (channel, callback) => {
    const validChannels = [
      'window-ready',
      'screen-changed',
      'theme-changed',
      'click-through-regions-updated',
      'websocket-connected',
      'websocket-message'
    ];
    
    if (validChannels.includes(channel)) {
      ipcRenderer.on(channel, (event, ...args) => callback(...args));
    }
  },
  
  off: (channel, callback) => {
    ipcRenderer.removeListener(channel, callback);
  }
});

// Console.log for debugging in renderer process
console.log('ElectronAPI preload loaded successfully');
