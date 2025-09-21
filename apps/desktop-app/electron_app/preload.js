const { contextBridge, ipcRenderer } = require("electron");

// Add debugging information
console.log("Preload script loading...");

try {
  // 在Electron preload环境中，__dirname是可用的，但需要确保正确使用
  // 使用path.join来构建路径更安全
  const path = require("path");
  
  // 使用相对路径而不是__dirname来避免问题
  const CHANNELS = require("./src/ipc-channels.js");
  console.log("ipc-channels.js loaded successfully");

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

  // Expose CHANNELS to the renderer process
  contextBridge.exposeInMainWorld('ipcChannels', CHANNELS);
  
  // 不再尝试在preload中加载DOMPurify，因为已经在HTML中通过CDN加载
  console.log("Preload script loaded successfully");
} catch (error) {
  console.error("Error in preload script:", error);
}