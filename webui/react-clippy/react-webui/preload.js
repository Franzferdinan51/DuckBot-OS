const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electron', {
  getAppInfo: () => ipcRenderer.invoke('get-app-info'),
  startDuckBotProcess: (options) => ipcRenderer.invoke('start-duckbot-process', options),
  stopDuckBotProcess: () => ipcRenderer.invoke('stop-duckbot-process'),
  onDuckBotLog: (callback) => ipcRenderer.on('duckbot-log', callback)
});