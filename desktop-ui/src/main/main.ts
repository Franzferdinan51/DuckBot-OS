import { app, BrowserWindow, ipcMain, Menu, dialog, shell } from 'electron'
import path from 'path'
import Store from 'electron-store'
import { DuckBotServiceManager } from './services/DuckBotServiceManager'
import { WebSocketServer } from './services/WebSocketServer'
import { createTray } from './tray/DuckBotTray'
import { createMenu } from './menu/DuckBotMenu'

// Configure electron-store
const store = new Store({
  defaults: {
    windowBounds: { width: 1400, height: 900 },
    theme: 'dark',
    autoStart: false,
    notifications: true,
    services: {
      lmStudioUrl: 'http://localhost:1234',
      webuiPort: 8787,
      monitoringPort: 8789
    }
  }
})

let mainWindow: BrowserWindow | null = null
let serviceManager: DuckBotServiceManager | null = null
let wsServer: WebSocketServer | null = null
let isQuitting = false

// Create main browser window
function createWindow(): BrowserWindow {
  const { width, height } = store.get('windowBounds') as { width: number; height: number }

  const window = new BrowserWindow({
    width,
    height,
    minWidth: 800,
    minHeight: 600,
    show: false,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js'),
      webSecurity: true,
      allowRunningInsecureContent: false,
      experimentalFeatures: false,
      sandbox: false
    },
    // icon: path.join(__dirname, '../../assets/icon.png'),
    titleBarStyle: 'default',
    backgroundColor: '#0f172a'
  })

  // Load the app
  if (process.env.NODE_ENV === 'development') {
    window.loadURL('http://localhost:3000')
    window.webContents.openDevTools()
  } else {
    window.loadFile(path.join(__dirname, 'renderer/index.html'))
  }

  // Window state management
  window.on('resize', () => {
    const { width, height } = window.getBounds()
    store.set('windowBounds', { width, height })
  })

  window.on('close', (e) => {
    if (!isQuitting && store.get('minimizeToTray') as boolean) {
      e.preventDefault()
      window.hide()
    }
  })

  return window
}

// App lifecycle handlers
app.whenReady().then(async () => {
  // Initialize service manager
  serviceManager = new DuckBotServiceManager()
  await serviceManager.initialize()

  // Initialize WebSocket server
  wsServer = new WebSocketServer(serviceManager)
  await wsServer.start()

  // Create main window
  mainWindow = createWindow()

  // Create system tray
  const tray = createTray(mainWindow)

  // Create application menu
  const menu = createMenu(mainWindow, serviceManager)
  Menu.setApplicationMenu(menu)

  // Show window when ready
  mainWindow.once('ready-to-show', () => {
    mainWindow?.show()
  })

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      mainWindow = createWindow()
    }
  })
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin' || isQuitting) {
    app.quit()
  }
})

app.on('before-quit', () => {
  isQuitting = true
  wsServer?.stop()
  serviceManager?.cleanup()
})

// IPC Handlers for service management
ipcMain.handle('get-system-status', async () => {
  return await serviceManager?.getSystemStatus() || {}
})

ipcMain.handle('start-service', async (event, serviceName: string) => {
  return await serviceManager?.startService(serviceName)
})

ipcMain.handle('stop-service', async (event, serviceName: string) => {
  return await serviceManager?.stopService(serviceName)
})

ipcMain.handle('restart-service', async (event, serviceName: string) => {
  return await serviceManager?.restartService(serviceName)
})

ipcMain.handle('get-service-logs', async (event, serviceName: string) => {
  return await serviceManager?.getServiceLogs(serviceName)
})

ipcMain.handle('get-system-metrics', async () => {
  return await serviceManager?.getSystemMetrics() || {}
})

ipcMain.handle('get-cost-data', async () => {
  return await serviceManager?.getCostData() || {}
})

ipcMain.handle('get-ai-config', async () => {
  return await serviceManager?.getAIConfig() || {}
})

ipcMain.handle('update-ai-config', async (event, config: any) => {
  return await serviceManager?.updateAIConfig(config)
})

ipcMain.handle('execute-automation', async (event, command: string, params?: any) => {
  return await serviceManager?.executeAutomation(command, params)
})

ipcMain.handle('get-conversations', async () => {
  return await serviceManager?.getConversations() || []
})

ipcMain.handle('send-message', async (event, message: string, provider?: string) => {
  return await serviceManager?.sendMessage(message, provider)
})

ipcMain.handle('get-agents', async () => {
  return await serviceManager?.getAgents() || []
})

ipcMain.handle('control-agent', async (event, agentId: string, action: string, params?: any) => {
  return await serviceManager?.controlAgent(agentId, action, params)
})

// Configuration handlers
ipcMain.handle('get-config', () => {
  return store.store
})

ipcMain.handle('update-config', async (event, key: string, value: any) => {
  store.set(key, value)
  return true
})

ipcMain.handle('reset-config', async () => {
  store.clear()
  app.relaunch()
  app.exit()
})

// File system handlers
ipcMain.handle('open-file-dialog', async (event, options: any) => {
  const result = await dialog.showOpenDialog(mainWindow!, options)
  return result
})

ipcMain.handle('save-file-dialog', async (event, options: any) => {
  const result = await dialog.showSaveDialog(mainWindow!, options)
  return result
})

ipcMain.handle('open-external', async (event, url: string) => {
  await shell.openExternal(url)
})

// Notification handler
ipcMain.handle('show-notification', (event, options: any) => {
  if (store.get('notifications') as boolean) {
    new Notification({
      title: options.title,
      body: options.body,
      // icon: path.join(__dirname, '../../assets/icon.png'),
      silent: options.silent || false
    }).show()
  }
})

// Export service manager for external access
export { serviceManager, store }