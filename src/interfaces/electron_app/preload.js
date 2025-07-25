// Placeholder for Electron preload script (preload.js)
const { contextBridge, ipcRenderer } = require('electron');

console.log("Electron preload.js placeholder script loaded.");

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object.
// This is a security best practice.
contextBridge.exposeInMainWorld(
  'electronAPI', // This will be window.electronAPI in the renderer
  {
    // Example: Send a message to the main process
    sendMessage: (channel, data) => {
      // Whitelist channels
      const validChannels = ['toMainProcess', 'anotherChannel'];
      if (validChannels.includes(channel)) {
        console.log(`Preload: Sending message on channel '${channel}' with data:`, data);
        ipcRenderer.send(channel, data);
      } else {
        console.warn(`Preload: Attempted to send on invalid channel '${channel}'`);
      }
    },
    // Example: Receive a message from the main process
    onMessage: (channel, func) => {
      const validChannels = ['fromMainProcess', 'updateCounter'];
      if (validChannels.includes(channel)) {
        // Deliberately strip event as it includes `sender`
        ipcRenderer.on(channel, (event, ...args) => func(...args));
        console.log(`Preload: Registered listener for channel '${channel}'`);
      } else {
        console.warn(`Preload: Attempted to listen on invalid channel '${channel}'`);
      }
    },
    // Example: Invoke a handler in the main process and get a response
    invoke: async (channel, ...args) => {
        const validChannels = [
            'handle-action',
            'hsp:get-discovered-services',
            'hsp:request-task',
            'hsp:get-task-status', // Added for polling task status
            'game:start' // Added for starting the game
        ];
        if (validChannels.includes(channel)) {
            console.log(`Preload: Invoking main process handler on channel '${channel}' with args:`, args);
            return await ipcRenderer.invoke(channel, ...args);
        }
        console.warn(`Preload: Attempted to invoke on invalid channel '${channel}'`);
        return null;
    }
    // You can add more functions here to expose specific IPC functionalities
  }
);

// Example of setting up an IPC listener in main.js for 'handle-action':
// ipcMain.handle('handle-action', async (event, someArgument) => {
//   console.log('Main process received handle-action with:', someArgument);
//   // Do something, then return a result
//   return { reply: `Processed: ${someArgument}` };
// });

// Example of sending from renderer.js:
// async function doSomething() {
//   const result = await window.electronAPI.invoke('handle-action', 'my-data');
//   console.log('Renderer received result:', result); // { reply: 'Processed: my-data' }
// }
