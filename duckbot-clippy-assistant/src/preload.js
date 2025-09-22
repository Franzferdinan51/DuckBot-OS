const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electronAPI', {
  minimizeToTray: () => ipcRenderer.invoke('minimize-to-tray'),
  toggleAlwaysOnTop: (alwaysOnTop) => ipcRenderer.invoke('toggle-always-on-top', alwaysOnTop),
  getDuckBotStatus: () => ipcRenderer.invoke('get-duckbot-status'),
  startDuckBot: () => ipcRenderer.invoke('start-duckbot'),
  stopDuckBot: () => ipcRenderer.invoke('stop-duckbot'),
  setWindowPosition: (x, y) => ipcRenderer.invoke('set-window-position', x, y),
  getWindowPosition: () => ipcRenderer.invoke('get-window-position'),
  setWindowBounds: (bounds) => ipcRenderer.invoke('set-window-bounds', bounds),
  getWindowBounds: () => ipcRenderer.invoke('get-window-bounds'),

  // Listen for events from main process
  onOpenSettings: (callback) => ipcRenderer.on('open-settings', callback),
  onShowAbout: (callback) => ipcRenderer.on('show-about', callback),

  // Remove listeners
  removeListener: (channel, callback) => ipcRenderer.removeListener(channel, callback),
  removeAllListeners: (channel) => ipcRenderer.removeAllListeners(channel)
});