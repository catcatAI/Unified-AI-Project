const { contextBridge, ipcRenderer } = require("electron");

// Add debugging information
console.log("Preload script loading...");

try {
  // 修复路径问题 - 使用相对路径
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

  // 安全地解析初始状态
  let initialState = {};
  try {
    const initialStateArg = process.argv.find(arg => arg.startsWith('{'));
    if (initialStateArg) {
      initialState = JSON.parse(initialStateArg);
    }
  } catch (e) {
    console.warn("Could not parse initial state:", e);
  }
  contextBridge.exposeInMainWorld('initialState', initialState);

  // Expose CHANNELS to the renderer process
  contextBridge.exposeInMainWorld('ipcChannels', CHANNELS);
  
  console.log("Preload script loaded successfully");
} catch (error) {
  console.error("Error in preload script:", error);
  // 即使加载失败也要暴露基本的API
  contextBridge.exposeInMainWorld("electronAPI", {
    invoke: async (channel, ...args) => {
      console.error(`IPC not available for channel '${channel}'`);
      return null;
    },
  });
}