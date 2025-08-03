const { contextBridge, ipcRenderer } = require("electron");
const CHANNELS = require("./src/ipc-channels");

const validChannels = Object.values(CHANNELS);

contextBridge.exposeInMainWorld("electronAPI", {
  invoke: async (channel, ...args) => {
    if (validChannels.includes(channel)) {
      return await ipcRenderer.invoke(channel, ...args);
    }
    console.warn(`Preload: Attempted to invoke on invalid channel '${channel}'`);
    return null;
  },
});

contextBridge.exposeInMainWorld('initialState', JSON.parse(process.argv.find(arg => arg.startsWith('{'))));
