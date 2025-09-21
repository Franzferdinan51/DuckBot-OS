import { app, BrowserWindow, Menu, Tray, nativeImage } from 'electron'
import path from 'path'

export function createTray(mainWindow: BrowserWindow): Tray {
  const iconPath = path.join(__dirname, '../../assets/icon.png')
  const icon = nativeImage.createFromPath(iconPath)

  const tray = new Tray(icon)

  const contextMenu = Menu.buildFromTemplate([
    {
      label: 'Show DuckBot Desktop',
      click: () => {
        if (mainWindow) {
          mainWindow.show()
          mainWindow.focus()
        }
      }
    },
    {
      label: 'Hide DuckBot Desktop',
      click: () => {
        if (mainWindow) {
          mainWindow.hide()
        }
      }
    },
    { type: 'separator' },
    {
      label: 'Services',
      submenu: [
        { label: 'Start All Services', role: 'startAll' },
        { label: 'Stop All Services', role: 'stopAll' },
        { label: 'Restart All Services', role: 'restartAll' }
      ]
    },
    {
      label: 'Quick Actions',
      submenu: [
        { label: 'Open WebUI', click: () => { mainWindow?.webContents.send('open-webui') } },
        { label: 'Start Chat', click: () => { mainWindow?.webContents.send('start-chat') } },
        { label: 'Run Automation', click: () => { mainWindow?.webContents.send('run-automation') } }
      ]
    },
    { type: 'separator' },
    {
      label: 'Settings',
      click: () => {
        if (mainWindow) {
          mainWindow.show()
          mainWindow.webContents.send('navigate', '/settings')
        }
      }
    },
    {
      label: 'Check for Updates',
      click: () => {
        mainWindow?.webContents.send('check-updates')
      }
    },
    { type: 'separator' },
    {
      label: 'Quit',
      click: () => {
        app.quit()
      }
    }
  ])

  tray.setToolTip('DuckBot Desktop - AI Ecosystem Manager')
  tray.setContextMenu(contextMenu)

  // Show window on tray icon double-click
  tray.on('double-click', () => {
    if (mainWindow) {
      if (mainWindow.isVisible()) {
        mainWindow.hide()
      } else {
        mainWindow.show()
        mainWindow.focus()
      }
    }
  })

  return tray
}