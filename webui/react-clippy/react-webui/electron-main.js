const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const isDev = require('electron-is-dev');

// Keep a global reference of the window object, if you don't, the window will
// be closed automatically when the JavaScript object is garbage collected.
let mainWindow;
let duckbotProcess;

function createWindow() {
  // Create the browser window.
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
    },
    icon: path.join(__dirname, 'public/favicon.ico')
  });

  // Load the React app
  if (isDev) {
    mainWindow.loadURL('http://localhost:3000');
    mainWindow.webContents.openDevTools();
  } else {
    mainWindow.loadFile(path.join(__dirname, 'build/index.html'));
  }

  // Emitted when the window is closed.
  mainWindow.on('closed', function () {
    // Dereference the window object, usually you would store windows
    // in an array if your app supports multi windows, this is the time
    // when you should delete the corresponding element.
    mainWindow = null;
  });
}

// Start DuckBot backend process
function startDuckBotBackend() {
  const pythonPath = process.env.PYTHON_PATH || 'python';
  
  // Use the module approach to start enhanced_webui
  duckbotProcess = spawn(pythonPath, ['-m', 'duckbot.enhanced_webui', '--host', '127.0.0.1', '--port', '8787'], {
    cwd: path.join(__dirname, '..')
  });

  duckbotProcess.stdout.on('data', (data) => {
    console.log(`DuckBot Backend: ${data}`);
    // Send log to renderer process
    if (mainWindow) {
      mainWindow.webContents.send('duckbot-log', { type: 'info', message: data.toString() });
    }
  });

  duckbotProcess.stderr.on('data', (data) => {
    console.error(`DuckBot Backend Error: ${data}`);
    // Send error to renderer process
    if (mainWindow) {
      mainWindow.webContents.send('duckbot-log', { type: 'error', message: data.toString() });
    }
  });

  duckbotProcess.on('close', (code) => {
    console.log(`DuckBot Backend process exited with code ${code}`);
    if (mainWindow) {
      mainWindow.webContents.send('duckbot-log', { type: 'info', message: `DuckBot Backend process exited with code ${code}` });
    }
  });
}

// This method will be called when Electron has finished
// initialization and is ready to create browser windows.
// Some APIs can only be used after this event occurs.
app.on('ready', () => {
  createWindow();
  startDuckBotBackend();
});

// Quit when all windows are closed.
app.on('window-all-closed', function () {
  // On macOS it is common for applications and their menu bar
  // to stay active until the user quits explicitly with Cmd + Q
  if (process.platform !== 'darwin') {
    if (duckbotProcess) {
      duckbotProcess.kill();
    }
    app.quit();
  }
});

app.on('activate', function () {
  // On macOS it's common to re-create a window in the app when the
  // dock icon is clicked and there are no other windows open.
  if (mainWindow === null) {
    createWindow();
  }
});

// IPC handlers
ipcMain.handle('get-app-info', async () => {
  return {
    version: app.getVersion(),
    name: 'DuckBot v3.1.0+',
    platform: process.platform
  };
});

ipcMain.handle('start-duckbot-process', async (event, options) => {
  // Implementation for starting different DuckBot processes
  return { success: true, message: 'Process started' };
});

ipcMain.handle('stop-duckbot-process', async () => {
  // Implementation for stopping DuckBot processes
  if (duckbotProcess) {
    duckbotProcess.kill();
    return { success: true, message: 'Process stopped' };
  }
  return { success: false, message: 'No process running' };
});