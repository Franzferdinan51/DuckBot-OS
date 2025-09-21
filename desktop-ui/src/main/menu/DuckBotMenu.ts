import { app, BrowserWindow, Menu, dialog, shell } from 'electron'
import { DuckBotServiceManager } from '../services/DuckBotServiceManager'

export function createMenu(mainWindow: BrowserWindow, serviceManager: DuckBotServiceManager): Menu {
  const isMac = process.platform === 'darwin'

  const template = [
    // App menu (macOS)
    ...(isMac ? [{
      label: app.name,
      submenu: [
        { role: 'about', label: 'About DuckBot Desktop' },
        { type: 'separator' },
        { role: 'services' },
        { type: 'separator' },
        { role: 'hide' },
        { role: 'hideothers' },
        { role: 'unhide' },
        { type: 'separator' },
        { role: 'quit' }
      ]
    }] : []),

    // File menu
    {
      label: 'File',
      submenu: [
        {
          label: 'New Chat',
          accelerator: 'CmdOrCtrl+N',
          click: () => mainWindow.webContents.send('new-chat')
        },
        {
          label: 'New Automation',
          accelerator: 'CmdOrCtrl+Shift+A',
          click: () => mainWindow.webContents.send('new-automation')
        },
        { type: 'separator' },
        {
          label: 'Export Configuration',
          click: async () => {
            const result = await dialog.showSaveDialog(mainWindow, {
              filters: [{ name: 'JSON', extensions: ['json'] }],
              defaultPath: 'duckbot-config.json'
            })
            if (!result.canceled) {
              mainWindow.webContents.send('export-config', result.filePath)
            }
          }
        },
        {
          label: 'Import Configuration',
          click: async () => {
            const result = await dialog.showOpenDialog(mainWindow, {
              filters: [{ name: 'JSON', extensions: ['json'] }],
              properties: ['openFile']
            })
            if (!result.canceled) {
              mainWindow.webContents.send('import-config', result.filePaths[0])
            }
          }
        },
        { type: 'separator' },
        isMac ? { role: 'close' } : { role: 'quit' }
      ]
    },

    // Edit menu
    {
      label: 'Edit',
      submenu: [
        { role: 'undo', label: 'Undo' },
        { role: 'redo', label: 'Redo' },
        { type: 'separator' },
        { role: 'cut', label: 'Cut' },
        { role: 'copy', label: 'Copy' },
        { role: 'paste', label: 'Paste' },
        ...(isMac ? [
          { role: 'pasteAndMatchStyle', label: 'Paste and Match Style' },
          { role: 'delete', label: 'Delete' },
          { role: 'selectAll', label: 'Select All' },
          { type: 'separator' },
          {
            label: 'Speech',
            submenu: [
              { role: 'startspeaking', label: 'Start Speaking' },
              { role: 'stopspeaking', label: 'Stop Speaking' }
            ]
          }
        ] : [
          { role: 'delete', label: 'Delete' },
          { type: 'separator' },
          { role: 'selectAll', label: 'Select All' }
        ])
      ]
    },

    // View menu
    {
      label: 'View',
      submenu: [
        {
          label: 'Dashboard',
          accelerator: 'CmdOrCtrl+1',
          click: () => mainWindow.webContents.send('navigate', '/dashboard')
        },
        {
          label: 'Services',
          accelerator: 'CmdOrCtrl+2',
          click: () => mainWindow.webContents.send('navigate', '/services')
        },
        {
          label: 'Agents',
          accelerator: 'CmdOrCtrl+3',
          click: () => mainWindow.webContents.send('navigate', '/agents')
        },
        {
          label: 'Chat',
          accelerator: 'CmdOrCtrl+4',
          click: () => mainWindow.webContents.send('navigate', '/chat')
        },
        {
          label: 'Automation',
          accelerator: 'CmdOrCtrl+5',
          click: () => mainWindow.webContents.send('navigate', '/automation')
        },
        { type: 'separator' },
        {
          label: 'Reload',
          accelerator: 'CmdOrCtrl+R',
          click: () => mainWindow.reload()
        },
        {
          label: 'Force Reload',
          accelerator: 'CmdOrCtrl+Shift+R',
          click: () => mainWindow.webContents.reloadIgnoringCache()
        },
        {
          label: 'Toggle Developer Tools',
          accelerator: isMac ? 'Alt+Cmd+I' : 'Ctrl+Shift+I',
          click: () => mainWindow.webContents.toggleDevTools()
        },
        { type: 'separator' },
        { role: 'resetzoom', label: 'Reset Zoom' },
        { role: 'zoomin', label: 'Zoom In' },
        { role: 'zoomout', label: 'Zoom Out' },
        { type: 'separator' },
        { role: 'togglefullscreen', label: 'Toggle Full Screen' }
      ]
    },

    // Services menu
    {
      label: 'Services',
      submenu: [
        {
          label: 'Start All Services',
          accelerator: 'CmdOrCtrl+Shift+S',
          click: async () => {
            const services = await serviceManager.getSystemStatus()
            for (const [name, status] of Object.entries(services)) {
              if (status.status !== 'running') {
                await serviceManager.startService(name)
              }
            }
          }
        },
        {
          label: 'Stop All Services',
          accelerator: 'CmdOrCtrl+Shift+X',
          click: async () => {
            const services = await serviceManager.getSystemStatus()
            for (const [name, status] of Object.entries(services)) {
              if (status.status === 'running') {
                await serviceManager.stopService(name)
              }
            }
          }
        },
        {
          label: 'Restart All Services',
          accelerator: 'CmdOrCtrl+Shift+R',
          click: async () => {
            const services = await serviceManager.getSystemStatus()
            for (const [name] of Object.entries(services)) {
              await serviceManager.restartService(name)
            }
          }
        },
        { type: 'separator' },
        {
          label: 'LM Studio',
          submenu: [
            {
              label: 'Start',
              click: () => serviceManager.startService('lm_studio')
            },
            {
              label: 'Stop',
              click: () => serviceManager.stopService('lm_studio')
            },
            {
              label: 'Restart',
              click: () => serviceManager.restartService('lm_studio')
            }
          ]
        },
        {
          label: 'WebUI',
          submenu: [
            {
              label: 'Start',
              click: () => serviceManager.startService('webui')
            },
            {
              label: 'Stop',
              click: () => serviceManager.stopService('webui')
            },
            {
              label: 'Restart',
              click: () => serviceManager.restartService('webui')
            }
          ]
        },
        {
          label: 'Monitoring',
          submenu: [
            {
              label: 'Start',
              click: () => serviceManager.startService('monitoring')
            },
            {
              label: 'Stop',
              click: () => serviceManager.stopService('monitoring')
            },
            {
              label: 'Restart',
              click: () => serviceManager.restartService('monitoring')
            }
          ]
        }
      ]
    },

    // Window menu
    {
      label: 'Window',
      submenu: [
        { role: 'minimize', label: 'Minimize' },
        { role: 'zoom', label: 'Zoom' },
        ...(isMac ? [
          { type: 'separator' },
          { role: 'front', label: 'Bring All to Front' },
          { type: 'separator' },
          { role: 'window', label: 'Window' }
        ] : [
          { type: 'separator' },
          { role: 'close', label: 'Close' }
        ])
      ]
    },

    // Help menu
    {
      label: 'Help',
      submenu: [
        {
          label: 'Documentation',
          click: async () => {
            await shell.openExternal('https://docs.duckbot.ai')
          }
        },
        {
          label: 'GitHub Repository',
          click: async () => {
            await shell.openExternal('https://github.com/duckbot/duckbot-desktop')
          }
        },
        {
          label: 'Report Issue',
          click: async () => {
            await shell.openExternal('https://github.com/duckbot/duckbot-desktop/issues')
          }
        },
        { type: 'separator' },
        {
          label: 'Check for Updates',
          click: () => mainWindow.webContents.send('check-updates')
        },
        { type: 'separator' },
        { role: 'about', label: 'About DuckBot Desktop' }
      ]
    }
  ] as any

  const menu = Menu.buildFromTemplate(template)
  return menu
}