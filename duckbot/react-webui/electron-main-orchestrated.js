const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const isDev = require('electron-is-dev');
const WebSocket = require('ws');

// Import our service configuration reader
const serviceConfig = require('./service-config-reader');

// Import error handling utilities
const { ElectronErrorHandler } = require('./electron-error-handler');

// Keep a global reference of the window object
let mainWindow;

// Initialize error handler
const errorHandler = new ElectronErrorHandler({
  logFile: path.join(__dirname, '..', 'logs', 'electron-error.log'),
  enableConsole: true,
  enableFile: true,
  autoRecovery: true,
  maxRetries: 3,
  retryDelay: 2000
});

// Add missing logDebug method if it doesn't exist
if (!errorHandler.logDebug) {
  errorHandler.logDebug = function(message, context = {}) {
    this.log('DEBUG', message, context);
  };
}

function createWindow() {
  try {
    console.log('🖥️  Creating Electron main window...');

    // Create the browser window with enhanced visibility options
    mainWindow = new BrowserWindow({
      width: 1200,
      height: 800,
      show: true, // Show window immediately
      webPreferences: {
        preload: path.join(__dirname, 'preload.js'),
        nodeIntegration: false,
        contextIsolation: true,
      },
      icon: path.join(__dirname, 'public/favicon.ico')
    });

    console.log('✅ BrowserWindow created successfully');

    // Ensure window is visible and focused
    mainWindow.show();
    mainWindow.focus();
    mainWindow.center();

    // Load the React app using service configuration
    if (isDev) {
      const reactConfig = serviceConfig.getReactServerConfig();
      const reactUrl = reactConfig.url;
      console.log(`🌐 Loading React app from: ${reactUrl}`);

      mainWindow.loadURL(reactUrl).catch((error) => {
        console.error('❌ Failed to load React dev server:', error);
        // Fallback to built version
        const fallbackPath = path.join(__dirname, 'build', 'index.html');
        if (require('fs').existsSync(fallbackPath)) {
          console.log('📁 Falling back to built version...');
          mainWindow.loadFile(fallbackPath);
        } else {
          console.error('❌ No fallback available');
        }
      });

      // Only open DevTools in development
      if (process.env.NODE_ENV !== 'test') {
        mainWindow.webContents.openDevTools();
      }
    } else {
      const buildPath = path.join(__dirname, 'build/index.html');
      console.log(`📁 Loading built app from: ${buildPath}`);
      mainWindow.loadFile(buildPath);
    }

    // Show window when content is ready
    mainWindow.once('ready-to-show', () => {
      console.log('👁️  Window ready to show, displaying window...');
      mainWindow.show();
      mainWindow.focus();

      // Center window on screen
      mainWindow.center();
      console.log('🎯 Window centered and focused');
    });

    // Handle window state
    mainWindow.on('show', () => {
      console.log('👁️  Window shown event fired');
    });

    mainWindow.on('focus', () => {
      console.log('🎯 Window focused event fired');
    });

    // Emitted when the window is closed.
    mainWindow.on('closed', function () {
      console.log('🔒 Window closed, setting mainWindow to null');
      mainWindow = null;
    });

    // Handle window crashes
    mainWindow.on('unresponsive', () => {
      errorHandler.handleError('WINDOW_UNRESPONSIVE', 'Main window became unresponsive', { window: 'main' });
    });

    mainWindow.on('responsive', () => {
      errorHandler.logInfo('Main window became responsive again');
    });

    // Handle renderer process crashes
    mainWindow.webContents.on('crashed', (event, killed) => {
      console.error(`💥 Renderer process crashed (killed: ${killed})`);
      errorHandler.handleError('RENDERER_CRASH', `Renderer process crashed (killed: ${killed})`, { killed });

      // Attempt to recover
      if (errorHandler.config.autoRecovery) {
        setTimeout(() => {
          try {
            console.log('🔄 Attempting to recover from renderer crash...');
            if (mainWindow) {
              mainWindow.destroy();
            }
            createWindow();
            errorHandler.logInfo('Recovered from renderer crash');
          } catch (error) {
            console.error('❌ Failed to recover from renderer crash:', error);
            errorHandler.handleError('RECOVERY_FAILED', 'Failed to recover from renderer crash', { error: error.message });
          }
        }, 3000);
      }
    });

    // Handle did-fail-load events
    mainWindow.webContents.on('did-fail-load', (event, errorCode, errorDesc, validatedURL) => {
      console.error(`❌ Failed to load URL: ${validatedURL}`, { errorCode, errorDesc });
      errorHandler.handleError('LOAD_FAILED', `Failed to load URL: ${validatedURL} (${errorCode}: ${errorDesc})`, {
        errorCode,
        errorDesc,
        validatedURL
      });

      // Attempt fallback to built version
      if (isDev && !validatedURL.includes('index.html')) {
        const fallbackPath = path.join(__dirname, 'build', 'index.html');
        if (require('fs').existsSync(fallbackPath)) {
          console.log('📁 Falling back to built version after load failure...');
          setTimeout(() => {
            mainWindow.loadFile(fallbackPath);
          }, 1000);
        }
      }
    });

    // Handle window creation errors
    mainWindow.on('failed-to-show', () => {
      console.error('❌ Window failed to show');
      errorHandler.handleError('WINDOW_FAILED_TO_SHOW', 'Window failed to show');
    });

    // Send service configuration to renderer
    if (serviceConfig.isConfigValid()) {
      mainWindow.webContents.on('did-finish-load', () => {
        mainWindow.webContents.send('service-config', serviceConfig.config);
      });
    }

  } catch (error) {
    errorHandler.handleError('WINDOW_CREATION_FAILED', `Failed to create main window: ${error.message}`, { error });
    throw error;
  }
}

// Health monitoring for MCP server
const mcpHealthMonitor = {
  mcpPort: serviceConfig.getMCPPort(),
  mcpServiceName: 'mcp_server',
  mcpProcess: null,
  isStarting: false,

  async startMCPService() {
    if (this.isStarting) {
      errorHandler.logWarning('MCP server startup already in progress');
      return false;
    }

    this.isStarting = true;

    try {
      errorHandler.logInfo('MCP server should be managed by orchestrator, checking health...');

      // Since the orchestrator manages the MCP server, we just check if it's healthy
      const health = await this.getMCPHealthStatus();
      if (health.status === 'healthy') {
        this.isStarting = false;
        return true;
      }

      errorHandler.logWarning('MCP server not healthy, orchestrator should restart it');
      this.isStarting = false;
      return false;

    } catch (error) {
      errorHandler.handleError('MCP_HEALTH_CHECK_FAILED', `MCP server health check failed: ${error.message}`, { error: error.message });
      this.isStarting = false;
      return false;
    }
  },

  async getMCPHealthStatus() {
    try {
      // Test WebSocket connection to MCP server instead of HTTP health endpoint
      return new Promise((resolve, reject) => {
        const ws = new WebSocket(`ws://127.0.0.1:${this.mcpPort}`);
        const timeout = setTimeout(() => {
          ws.close();
          reject(new Error('WebSocket connection timeout'));
        }, 5000);

        ws.on('open', () => {
          clearTimeout(timeout);
          // Send ping to test server responsiveness
          ws.send(JSON.stringify({ type: 'ping' }));

          // Wait for response
          const responseTimeout = setTimeout(() => {
            ws.close();
            reject(new Error('No response from MCP server'));
          }, 2000);

          ws.on('message', (data) => {
            clearTimeout(responseTimeout);
            try {
              const response = JSON.parse(data);
              ws.close();
              resolve({
                status: 'healthy',
                responseTime: Date.now(),
                data: response
              });
            } catch (e) {
              ws.close();
              reject(new Error('Invalid response from MCP server'));
            }
          });
        });

        ws.on('error', (error) => {
          clearTimeout(timeout);
          reject(new Error(`WebSocket connection failed: ${error.message}`));
        });
      });
    } catch (error) {
      errorHandler.logWarning(`MCP health check failed: ${error.message}`);
      return { status: 'unhealthy', error: error.message, responseTime: Date.now() };
    }
  },

  async attemptMCPRecovery() {
    errorHandler.logInfo('MCP recovery - orchestrator should handle this automatically');
    // The orchestrator will handle MCP server recovery
    return false;
  }
};

// IPC handlers for communication with renderer process
ipcMain.handle('get-service-config', () => {
  return serviceConfig.config;
});

ipcMain.handle('get-mcp-status', async () => {
  return await mcpHealthMonitor.getMCPHealthStatus();
});

ipcMain.handle('restart-mcp-server', async () => {
  // The orchestrator handles restarts, but we can trigger a config reload
  serviceConfig.reloadConfig();
  return { success: true, message: 'Configuration reloaded, orchestrator will handle restart' };
});

// Window management IPC handlers
ipcMain.handle('minimize-window', () => {
  if (mainWindow) {
    mainWindow.minimize();
    return { success: true };
  }
  return { success: false, error: 'No main window' };
});

ipcMain.handle('maximize-window', () => {
  if (mainWindow) {
    if (mainWindow.isMaximized()) {
      mainWindow.restore();
    } else {
      mainWindow.maximize();
    }
    return { success: true };
  }
  return { success: false, error: 'No main window' };
});

ipcMain.handle('close-window', () => {
  if (mainWindow) {
    mainWindow.close();
    return { success: true };
  }
  return { success: false, error: 'No main window' };
});

// App lifecycle events
app.whenReady().then(() => {
  createWindow();

  app.on('activate', function () {
    // On macOS it's common to re-create a window in the app when the
    // dock icon is clicked and there are no other windows open.
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });

  // Start health monitoring
  setInterval(async () => {
    if (mainWindow && !mainWindow.isDestroyed()) {
      try {
        const mcpStatus = await mcpHealthMonitor.getMCPHealthStatus();
        mainWindow.webContents.send('mcp-status', mcpStatus);
      } catch (error) {
        console.error('Error sending MCP status to renderer:', error);
      }
    }
  }, 10000); // Check every 10 seconds
});

app.on('window-all-closed', function () {
  // On OS X it is common for applications and their menu bar
  // to stay active until the user quits explicitly with Cmd + Q
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('before-quit', () => {
  // Cleanup before quitting
  if (mcpHealthMonitor.mcpProcess && !mcpHealthMonitor.mcpProcess.killed) {
    mcpHealthMonitor.mcpProcess.kill();
  }
});

// Error handling for uncaught exceptions
process.on('uncaughtException', (error) => {
  errorHandler.handleError('UNCAUGHT_EXCEPTION', `Uncaught exception: ${error.message}`, { error: error.stack });
  console.error('Uncaught Exception:', error);
});

process.on('unhandledRejection', (reason, promise) => {
  errorHandler.handleError('UNHANDLED_REJECTION', `Unhandled rejection at: ${promise}, reason: ${reason}`, { reason, promise });
  console.error('Unhandled Rejection at:', promise, 'reason:', reason);
});

// Export for testing
module.exports = {
  createWindow,
  mcpHealthMonitor,
  serviceConfig,
  errorHandler
};