const { contextBridge, ipcRenderer } = require('electron');

// Define valid IPC channels
const ipcChannels = {
  RUN_SCRIPT: 'run-script',
  RUN_CLI_COMMAND: 'run-cli-command',
  GET_SYSTEM_INFO: 'get-system-info',
  CHECK_ENVIRONMENT: 'check-environment'
};

contextBridge.exposeInMainWorld('electronAPI', {
  runScript: (script, args) => ipcRenderer.invoke(ipcChannels.RUN_SCRIPT, { script, args }),
  runCliCommand: (command, args) => ipcRenderer.invoke(ipcChannels.RUN_CLI_COMMAND, { command, args }),
  getSystemInfo: () => ipcRenderer.invoke(ipcChannels.GET_SYSTEM_INFO),
  checkEnvironment: () => ipcRenderer.invoke(ipcChannels.CHECK_ENVIRONMENT),
  onScriptOutput: (callback) => ipcRenderer.on('script-output', callback),
  onCliOutput: (callback) => ipcRenderer.on('cli-output', callback)
});