const { app, BrowserWindow, ipcMain, Tray, Menu, screen, contextBridge } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let mainWindow;
let tray;
let isMinimizedToTray = false;

// Keep a global reference to prevent garbage collection
let duckbotProcess = null;

function createWindow() {
  // Get screen dimensions
  const { width: screenWidth, height: screenHeight } = screen.getPrimaryDisplay().workAreaSize;
  
  // Create the browser window - Clippy-like size and positioning
  mainWindow = new BrowserWindow({
    width: 450,
    height: 650,
    x: screenWidth - 470, // Position on the right side of screen
    y: screenHeight - 670, // Position at bottom right
    frame: false, // Frameless for Clippy-like appearance
    alwaysOnTop: true, // Always stay on top like Clippy
    transparent: true, // Transparent background
    resizable: true,
    minimizable: true,
    maximizable: false,
    skipTaskbar: false, // Show in taskbar initially
    icon: path.join(__dirname, '../assets/duckbot-icon.png'),
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      enableRemoteModule: false,
      preload: path.join(__dirname, 'preload.js')
    }
  });

  // Load the React dev server in development or built files in production
  if (process.env.NODE_ENV === 'development') {
    mainWindow.loadURL('http://localhost:3000');
    // mainWindow.webContents.openDevTools();
  } else {
    mainWindow.loadFile(path.join(__dirname, '../build/index.html'));
  }

  // Handle window closed
  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  // Handle minimize - minimize to tray instead of taskbar for Clippy-like behavior
  mainWindow.on('minimize', (event) => {
    if (process.platform === 'win32') {
      event.preventDefault();
      mainWindow.hide();
      isMinimizedToTray = true;
      
      // Update tray tooltip
      if (tray) {
        tray.setToolTip('DuckBot Clippy - Click to restore');
      }
    }
  });

  // Handle window focus changes
  mainWindow.on('blur', () => {
    // Optional: Auto-minimize when losing focus (true Clippy behavior)
    // Uncomment the next line if you want this behavior
    // mainWindow.minimize();
  });
}

function createTray() {
  // Create system tray icon with fallback
  const trayIconPath = path.join(__dirname, '../assets/duckbot-tray.png');
  try {
    tray = new Tray(trayIconPath);
  } catch (error) {
    console.warn('Failed to load tray icon, using fallback:', error.message);
    // Use built-in icon or create a simple fallback
    try {
      const { nativeImage } = require('electron');
      const fallbackIcon = nativeImage.createEmpty();
      tray = new Tray(fallbackIcon);
    } catch (fallbackError) {
      console.error('Failed to create fallback tray icon:', fallbackError);
      return; // Skip tray creation if all attempts fail
    }
  }
  
  const contextMenu = Menu.buildFromTemplate([
    {
      label: 'Show DuckBot Clippy',
      click: () => {
        showWindow();
      }
    },
    {
      label: 'Hide DuckBot Clippy', 
      click: () => {
        if (mainWindow) {
          mainWindow.hide();
          isMinimizedToTray = true;
        }
      }
    },
    { type: 'separator' },
    {
      label: 'Always on Top',
      type: 'checkbox',
      checked: true,
      click: (menuItem) => {
        if (mainWindow) {
          mainWindow.setAlwaysOnTop(menuItem.checked);
        }
      }
    },
    {
      label: 'Settings',
      click: () => {
        // Send message to renderer to open settings
        if (mainWindow) {
          mainWindow.webContents.send('open-settings');
        }
      }
    },
    { type: 'separator' },
    {
      label: 'Start DuckBot WebUI',
      click: () => {
        startDuckBotWebUI();
      }
    },
    {
      label: 'Stop DuckBot WebUI',
      click: () => {
        stopDuckBotWebUI();
      }
    },
    { type: 'separator' },
    {
      label: 'About',
      click: () => {
        if (mainWindow) {
          mainWindow.webContents.send('show-about');
        }
      }
    },
    {
      label: 'Quit DuckBot Clippy',
      click: () => {
        app.quit();
      }
    }
  ]);

  tray.setToolTip('DuckBot Clippy - 3D AI Desktop Companion');
  tray.setContextMenu(contextMenu);
  
  // Handle tray click - restore window
  tray.on('click', () => {
    showWindow();
  });
  
  tray.on('double-click', () => {
    showWindow();
  });
}

function showWindow() {
  if (mainWindow) {
    if (mainWindow.isMinimized()) {
      mainWindow.restore();
    }
    mainWindow.show();
    mainWindow.focus();
    isMinimizedToTray = false;
    
    if (tray) {
      tray.setToolTip('DuckBot Clippy - 3D AI Desktop Companion');
    }
  }
}

function startDuckBotWebUI() {
  if (duckbotProcess) {
    console.log('DuckBot WebUI is already running');
    return;
  }

  try {
    // Start DuckBot WebUI in the parent directory
    const duckbotPath = path.join(__dirname, '../../');
    duckbotProcess = spawn('python', ['-m', 'duckbot.webui'], {
      cwd: duckbotPath,
      detached: false,
      stdio: 'ignore' // Run silently in background
    });

    duckbotProcess.on('error', (error) => {
      console.error('Failed to start DuckBot WebUI:', error);
      duckbotProcess = null;
    });

    duckbotProcess.on('exit', (code) => {
      console.log(`DuckBot WebUI exited with code ${code}`);
      duckbotProcess = null;
    });

    console.log('DuckBot WebUI started successfully');
  } catch (error) {
    console.error('Error starting DuckBot WebUI:', error);
  }
}

function stopDuckBotWebUI() {
  if (duckbotProcess) {
    duckbotProcess.kill();
    duckbotProcess = null;
    console.log('DuckBot WebUI stopped');
  }
}

// App event handlers
app.whenReady().then(() => {
  createWindow();
  createTray();
  
  // Auto-start DuckBot WebUI
  setTimeout(() => {
    startDuckBotWebUI();
  }, 2000);
});

app.on('window-all-closed', () => {
  // Keep running in background when all windows are closed (like Clippy)
  // Don't quit on macOS unless specifically requested
  if (process.platform !== 'darwin') {
    // Don't quit - stay in tray
    return;
  }
});

app.on('activate', () => {
  if (mainWindow === null) {
    createWindow();
  } else {
    showWindow();
  }
});

app.on('before-quit', () => {
  // Cleanup DuckBot process
  stopDuckBotWebUI();
});

// IPC handlers for renderer process communication
ipcMain.handle('minimize-to-tray', () => {
  if (mainWindow) {
    mainWindow.hide();
    isMinimizedToTray = true;
  }
});

ipcMain.handle('toggle-always-on-top', (event, alwaysOnTop) => {
  if (mainWindow) {
    mainWindow.setAlwaysOnTop(alwaysOnTop);
  }
});

ipcMain.handle('get-duckbot-status', () => {
  return {
    webui: duckbotProcess !== null,
    clippy: mainWindow !== null
  };
});

ipcMain.handle('start-duckbot', () => {
  startDuckBotWebUI();
});

ipcMain.handle('stop-duckbot', () => {
  stopDuckBotWebUI();
});

// Handle drag and drop repositioning
ipcMain.handle('set-window-position', (event, x, y) => {
  if (mainWindow) {
    mainWindow.setPosition(x, y);
  }
});

ipcMain.handle('get-window-position', () => {
  if (mainWindow) {
    return mainWindow.getPosition();
  }
  return [0, 0];
});

// Handle window bounds
ipcMain.handle('set-window-bounds', (event, bounds) => {
  if (mainWindow) {
    mainWindow.setBounds(bounds);
  }
});

ipcMain.handle('get-window-bounds', () => {
  if (mainWindow) {
    return mainWindow.getBounds();
  }
  return { x: 0, y: 0, width: 400, height: 600 };
});