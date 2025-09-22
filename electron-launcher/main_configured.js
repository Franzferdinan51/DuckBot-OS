const { app, BrowserWindow, ipcMain, Menu, dialog, shell, globalShortcut } = require('electron');
const path = require('path');
const fs = require('fs');
const Store = require('electron-store');
const si = require('systeminformation');
const axios = require('axios');
const { exec, spawn } = require('child_process');
const os = require('os');
const WebSocket = require('ws');
const chokidar = require('chokidar');
const kill = require('tree-kill');

// Global variables
let mainWindow;
let duckbotProcess = null;
let mcpConnection = null;
let chatWs = null;
let processes = new Map();
let systemMonitors = new Map();
let logWatchers = new Map();

// Connection management variables
let mcpRetryCount = 0;
let chatRetryCount = 0;
let lastMcpAttempt = 0;
let lastChatAttempt = 0;
let connectionNotified = false;
let mcpConnected = false;
let chatConnected = false;
const RETRY_DELAY = 10000; // 10 seconds between retries
const MAX_RETRIES = 3;

// Configuration system integration
let electronConfig = null;
let configBridgeInitialized = false;
let startupModes = {};

// Initialize electron store for settings
const store = new Store({
    defaults: {
        apiKeys: {
            gemini: '',
            openrouter: '',
            zai: '',
            zaiCodingPlan: ''
        },
        preferences: {
            autoStart: false,
            startMinimized: false,
            enableNotifications: true,
            enableAIAssistant: true,
            defaultInterface: 'electron',
            autoReconnect: true,
            autoStartMCP: true,
            logLevel: 'info'
        },
        ui: {
            theme: 'dark',
            fontSize: 14,
            chatPosition: 'right',
            showSystemInfo: true,
            compactMode: false
        },
        connections: {
            mcpHost: '127.0.0.1',
            mcpPort: 8789,
            webuiPort: 8787,
            aiRouterPort: 8790,
            retryAttempts: 3,
            timeout: 30000
        },
        windowState: {
            width: 1400,
            height: 900,
            x: undefined,
            y: undefined
        }
    }
});

// Initialize configuration from centralized system
async function initializeConfiguration() {
    try {
        const configPath = path.join(__dirname, '..', 'config', 'electron_config.json');

        // Try to load existing electron config first
        if (fs.existsSync(configPath)) {
            const configData = fs.readFileSync(configPath, 'utf8');
            const config = JSON.parse(configData);
            electronConfig = config.electron_config || {};
            startupModes = electronConfig.startup_modes || {};

            // Update store settings with config values
            if (electronConfig.debug_mode !== undefined) {
                store.set('preferences.logLevel', electronConfig.debug_mode ? 'debug' : 'info');
            }
            if (electronConfig.mcp_host !== undefined) {
                store.set('connections.mcpHost', electronConfig.mcp_host);
            }
            if (electronConfig.mcp_port !== undefined) {
                store.set('connections.mcpPort', electronConfig.mcp_port);
            }
            if (electronConfig.webui_port !== undefined) {
                store.set('connections.webuiPort', electronConfig.webui_port);
            }
            if (electronConfig.ai_router_port !== undefined) {
                store.set('connections.aiRouterPort', electronConfig.ai_router_port);
            }

            console.log('Loaded existing Electron configuration');
        } else {
            // Generate configuration from centralized system
            await generateElectronConfiguration();
        }

        configBridgeInitialized = true;
        console.log('Configuration system initialized successfully');

    } catch (error) {
        console.error('Failed to initialize configuration system:', error);
        // Use fallback configuration
        startupModes = getFallbackStartupModes();
        configBridgeInitialized = true;
    }
}

// Generate Electron configuration from centralized system
async function generateElectronConfiguration() {
    try {
        const pythonProcess = spawn('python', ['-c', `
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config.config_bridge import get_config_bridge
bridge = get_config_bridge()
config = bridge.export_for_electron()
import json
print(json.dumps(config))
`], {
            cwd: path.join(__dirname, '..'),
            encoding: 'utf8'
        });

        let configData = '';
        pythonProcess.stdout.on('data', (data) => {
            configData += data.toString();
        });

        pythonProcess.stderr.on('data', (data) => {
            console.error('Config generation error:', data.toString());
        });

        return new Promise((resolve, reject) => {
            pythonProcess.on('close', (code) => {
                if (code === 0 && configData) {
                    try {
                        const config = JSON.parse(configData);
                        electronConfig = config.electron_config || {};
                        startupModes = electronConfig.startup_modes || {};

                        // Update store settings with config values
                        if (electronConfig.debug_mode !== undefined) {
                            store.set('preferences.logLevel', electronConfig.debug_mode ? 'debug' : 'info');
                        }
                        if (electronConfig.mcp_host !== undefined) {
                            store.set('connections.mcpHost', electronConfig.mcp_host);
                        }
                        if (electronConfig.mcp_port !== undefined) {
                            store.set('connections.mcpPort', electronConfig.mcp_port);
                        }
                        if (electronConfig.webui_port !== undefined) {
                            store.set('connections.webuiPort', electronConfig.webui_port);
                        }
                        if (electronConfig.ai_router_port !== undefined) {
                            store.set('connections.aiRouterPort', electronConfig.ai_router_port);
                        }

                        // Save generated configuration
                        const configPath = path.join(__dirname, '..', 'config', 'electron_config.json');
                        fs.writeFileSync(configPath, JSON.stringify(config, null, 2));

                        console.log('Generated Electron configuration from centralized system');
                        resolve();
                    } catch (parseError) {
                        console.error('Failed to parse configuration:', parseError);
                        reject(parseError);
                    }
                } else {
                    console.error('Configuration generation failed with code:', code);
                    reject(new Error('Configuration generation failed'));
                }
            });

            pythonProcess.on('error', reject);
        });
    } catch (error) {
        console.error('Failed to generate Electron configuration:', error);
        throw error;
    }
}

// Fallback startup modes if configuration system fails
function getFallbackStartupModes() {
    return {
        'ultimate': {
            name: 'Ultimate Complete Mode',
            description: 'Complete AI integration with all features',
            icon: '🚀',
            category: 'complete',
            requires: ['gemini', 'openrouter'],
            command: 'python start_ecosystem.py',
            ports: [8787, 8788, 8789],
            enabled: true
        },
        'enhanced-webui': {
            name: 'Enhanced WebUI',
            description: 'Modern web interface with AI features',
            icon: '🌐',
            category: 'web',
            requires: ['openrouter'],
            command: 'python duckbot/enhanced_webui.py --port 8787',
            ports: [8787],
            enabled: true
        },
        'monitoring': {
            name: 'System Monitoring',
            description: 'Real-time system metrics and performance',
            icon: '📊',
            category: 'monitoring',
            requires: [],
            command: 'python ai_ecosystem_manager.py --port 8789',
            ports: [8789],
            enabled: true
        },
        'local-only': {
            name: 'Local-Only Privacy Mode',
            description: 'Complete offline operation with LM Studio',
            icon: '🔒',
            category: 'privacy',
            requires: [],
            command: 'python start_local_ecosystem.py',
            ports: [8787],
            enabled: true
        },
        'bytebot': {
            name: 'ByteBot Desktop Automation',
            description: 'Complete computer control with AI',
            icon: '🤖',
            category: 'automation',
            requires: ['gemini'],
            command: 'python -c "from duckbot.bytebot_integration import ByteBotIntegration; import asyncio; asyncio.run(ByteBotIntegration().start_interactive_mode())"',
            ports: [],
            enabled: true
        },
        'discord-bot': {
            name: 'Discord Bot with VibeVoice',
            description: 'Discord integration with voice capabilities',
            icon: '🎮',
            category: 'communication',
            requires: [],
            command: 'python duckbot/discord_bot.py',
            ports: [],
            enabled: true
        }
    };
}

// Get enabled startup modes
function getEnabledStartupModes() {
    const enabled = {};
    for (const [modeId, modeConfig] of Object.entries(startupModes)) {
        if (modeConfig.enabled !== false) {
            enabled[modeId] = modeConfig;
        }
    }
    return enabled;
}

// Create main window
function createWindow() {
    const { width, height, x, y } = store.get('windowState');

    mainWindow = new BrowserWindow({
        width: width,
        height: height,
        x: x,
        y: y,
        minWidth: 1200,
        minHeight: 800,
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false,
            enableRemoteModule: true
        },
        icon: path.join(__dirname, 'assets', 'icon.png'),
        show: false,
        titleBarStyle: 'default',
        backgroundColor: '#1a1a1a'
    });

    // Load the main HTML file
    mainWindow.loadFile('index.html');

    // Expose ipcRenderer to renderer process
    mainWindow.webContents.on('dom-ready', () => {
        mainWindow.webContents.executeJavaScript(`
            const { ipcRenderer } = require('electron');
            window.ipcRenderer = ipcRenderer;
        `);
    });

    // Show window when ready
    mainWindow.once('ready-to-show', () => {
        mainWindow.show();

        // Initialize configuration system
        initializeConfiguration().then(() => {
            console.log('Configuration system ready');
            // Notify renderer that configuration is loaded
            mainWindow.webContents.send('configuration-loaded', {
                startupModes: getEnabledStartupModes(),
                electronConfig: electronConfig,
                systemInfo: getSystemInfoSync()
            });
        }).catch(error => {
            console.error('Configuration system initialization failed:', error);
        });

        // Initialize connections
        initializeConnections();

        // Start system monitoring
        startSystemMonitoring();

        console.log('DuckBot Electron Launcher ready');
    });

    // Save window state on close
    mainWindow.on('close', () => {
        const bounds = mainWindow.getBounds();
        store.set('windowState', {
            width: bounds.width,
            height: bounds.height,
            x: bounds.x,
            y: bounds.y
        });

        // Clean up processes
        cleanupProcesses();
    });

    mainWindow.on('closed', () => {
        mainWindow = null;
    });

    // Create application menu
    createMenu();

    // Register global shortcuts
    registerGlobalShortcuts();
}

// Initialize connections
function initializeConnections() {
    const preferences = store.get('preferences');

    if (preferences.enableAIAssistant) {
        connectToDuckBotMCP();
        connectToChatServer();
    }
}

// Connect to DuckBot MCP
function connectToDuckBotMCP() {
    const now = Date.now();

    // Rate limit connection attempts
    if (now - lastMcpAttempt < RETRY_DELAY) {
        console.log(`MCP connection rate limited. Next attempt in ${Math.ceil((RETRY_DELAY - (now - lastMcpAttempt)) / 1000)}s`);
        return;
    }

    lastMcpAttempt = now;
    const connections = store.get('connections');

    // Try different connection endpoints for Tailscale
    const connectionEndpoints = [
        `ws://${connections.mcpHost}:${connections.mcpPort}`,  // Default localhost
        `ws://100.100.100.100:${connections.mcpPort}`,           // Tailscale MagicDNS
        `ws://localhost:${connections.mcpPort}`,                  // Alternative localhost
    ];

    let currentEndpointIndex = 0;

    function tryNextEndpoint() {
        if (currentEndpointIndex >= connectionEndpoints.length) {
            console.log('All MCP connection endpoints failed');
            mcpRetryCount++;

            // Check if we should auto-start minimal services
            const preferences = store.get('preferences');
            if (preferences.autoStartMCP && mcpRetryCount === 1 && !connectionNotified) {
                console.log('Auto-starting minimal DuckBot services...');
                mainWindow.webContents.send('mcp-status', {
                    connected: false,
                    error: '🚀 Auto-starting DuckBot services for better connectivity...',
                    autoStarting: true
                });

                // Start minimal services
                setTimeout(async () => {
                    try {
                        const result = await startMinimalServices();
                        if (result.started) {
                            console.log('Minimal services started successfully');
                            // Reset and retry connection
                            mcpRetryCount = 0;
                            currentEndpointIndex = 0;
                            setTimeout(() => tryNextEndpoint(), 2000);
                        }
                    } catch (error) {
                        console.error('Failed to auto-start minimal services:', error);
                    }
                }, 1000);
            }

            // Show user guidance after first failure
            if (!connectionNotified && !(preferences.autoStartMCP && mcpRetryCount === 1)) {
                mainWindow.webContents.send('mcp-status', {
                    connected: false,
                    error: 'Unable to connect to DuckBot MCP. Please ensure DuckBot is running first.\n\n💡 Try running START_ENHANCED_DUCKBOT.bat and choose Ultimate mode to start DuckBot.',
                    showGuidance: true
                });
                connectionNotified = true;
            }

            // Exponential backoff for retries
            if (mcpRetryCount < MAX_RETRIES) {
                const backoffTime = Math.min(RETRY_DELAY * Math.pow(2, mcpRetryCount), 60000);
                console.log(`Scheduling MCP retry ${mcpRetryCount + 1}/${MAX_RETRIES} in ${backoffTime}ms`);
                setTimeout(() => {
                    currentEndpointIndex = 0;
                    tryNextEndpoint();
                }, backoffTime);
            } else {
                console.log('MCP connection max retries reached, stopping automatic reconnection');
                mainWindow.webContents.send('mcp-status', {
                    connected: false,
                    error: 'DuckBot connection unavailable. You can still use startup modes, but AI features will be limited.',
                    maxRetries: true
                });
            }
            return;
        }

        const endpoint = connectionEndpoints[currentEndpointIndex];
        console.log(`Trying MCP connection to: ${endpoint}`);

        try {
            mcpConnection = new WebSocket(endpoint);

            mcpConnection.onopen = () => {
                console.log(`Connected to DuckBot MCP at: ${endpoint}`);
                mcpConnected = true;
                mainWindow.webContents.send('mcp-status', {
                    connected: true,
                    endpoint: endpoint,
                    message: '✅ Connected to DuckBot MCP server'
                });
                mcpRetryCount = 0; // Reset retry count on successful connection
                connectionNotified = false;
            };

            mcpConnection.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    mainWindow.webContents.send('mcp-message', data);
                } catch (error) {
                    console.error('Error parsing MCP message:', error);
                }
            };

            mcpConnection.onerror = (error) => {
                console.error(`MCP connection error for ${endpoint}:`, error.message);
                currentEndpointIndex++;
                tryNextEndpoint();
            };

            mcpConnection.onclose = () => {
                console.log(`MCP connection closed for: ${endpoint}`);
                mainWindow.webContents.send('mcp-status', {
                    connected: false,
                    message: '🔌 MCP connection closed'
                });

                // Auto-reconnect if enabled, but controlled by retry logic
                const preferences = store.get('preferences');
                if (preferences.autoReconnect && mcpRetryCount < MAX_RETRIES) {
                    // Let the retry logic handle reconnection
                    setTimeout(() => {
                        currentEndpointIndex = 0;
                        tryNextEndpoint();
                    }, RETRY_DELAY * Math.pow(2, mcpRetryCount));
                }
            };

        } catch (error) {
            console.error(`Failed to create MCP connection to ${endpoint}:`, error);
            currentEndpointIndex++;
            tryNextEndpoint();
        }
    }

    tryNextEndpoint();
}

// Connect to chat server
function connectToChatServer() {
    const now = Date.now();

    // Rate limit connection attempts
    if (now - lastChatAttempt < RETRY_DELAY) {
        console.log(`Chat connection rate limited. Next attempt in ${Math.ceil((RETRY_DELAY - (now - lastChatAttempt)) / 1000)}s`);
        return;
    }

    lastChatAttempt = now;

    // Try different connection endpoints for Tailscale
    const chatEndpoints = [
        'ws://localhost:8790',           // Default localhost
        'ws://100.100.100.100:8790',    // Tailscale MagicDNS
        'ws://127.0.0.1:8790',          // Alternative localhost
    ];

    let currentChatEndpointIndex = 0;

    function tryNextChatEndpoint() {
        if (currentChatEndpointIndex >= chatEndpoints.length) {
            console.log('All chat connection endpoints failed');
            chatRetryCount++;

            // Show user guidance for chat connection
            if (!connectionNotified) {
                mainWindow.webContents.send('chat-status', {
                    connected: false,
                    error: 'Unable to connect to DuckBot Chat. Please ensure DuckBot is running first.\n\n💡 Run START_ENHANCED_DUCKBOT.bat and choose Ultimate mode to enable AI chat features.',
                    showGuidance: true
                });
            }

            // Exponential backoff for retries
            if (chatRetryCount < MAX_RETRIES) {
                const backoffTime = Math.min(RETRY_DELAY * Math.pow(2, chatRetryCount), 60000);
                console.log(`Scheduling chat retry ${chatRetryCount + 1}/${MAX_RETRIES} in ${backoffTime}ms`);
                setTimeout(() => {
                    currentChatEndpointIndex = 0;
                    tryNextChatEndpoint();
                }, backoffTime);
            } else {
                console.log('Chat connection max retries reached, stopping automatic reconnection');
                mainWindow.webContents.send('chat-status', {
                    connected: false,
                    error: 'DuckBot chat unavailable. You can still use startup modes and the local Startup AI assistant.',
                    maxRetries: true
                });
            }
            return;
        }

        const endpoint = chatEndpoints[currentChatEndpointIndex];
        console.log(`Trying chat connection to: ${endpoint}`);

        try {
            chatWs = new WebSocket(endpoint);

            chatWs.onopen = () => {
                console.log(`Connected to DuckBot Chat Server at: ${endpoint}`);
                chatConnected = true;
                mainWindow.webContents.send('chat-status', {
                    connected: true,
                    endpoint: endpoint,
                    message: '✅ Connected to DuckBot Chat Server'
                });
                chatRetryCount = 0; // Reset retry count on successful connection
            };

            chatWs.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    mainWindow.webContents.send('chat-message', data);
                } catch (error) {
                    console.error('Error parsing chat message:', error);
                }
            };

            chatWs.onerror = (error) => {
                console.error(`Chat connection error for ${endpoint}:`, error.message);
                currentChatEndpointIndex++;
                tryNextChatEndpoint();
            };

            chatWs.onclose = () => {
                console.log(`Chat connection closed for: ${endpoint}`);
                chatConnected = false;
                mainWindow.webContents.send('chat-status', {
                    connected: false,
                    message: '🔌 Chat connection closed'
                });

                // Auto-reconnect if enabled, but with rate limiting
                const preferences = store.get('preferences');
                if (preferences.autoReconnect && chatRetryCount < MAX_RETRIES) {
                    setTimeout(() => {
                        currentChatEndpointIndex = 0;
                        tryNextChatEndpoint();
                    }, RETRY_DELAY * Math.pow(2, chatRetryCount));
                }
            };

        } catch (error) {
            console.error(`Failed to create chat connection to ${endpoint}:`, error);
            currentChatEndpointIndex++;
            tryNextChatEndpoint();
        }
    }

    tryNextChatEndpoint();
}

// Start system monitoring
function startSystemMonitoring() {
    // Monitor system resources
    setInterval(async () => {
        try {
            const [cpu, mem, disk, network] = await Promise.all([
                si.currentLoad(),
                si.mem(),
                si.fsSize(),
                si.networkStats()
            ]);

            const systemInfo = {
                cpu: cpu.currentLoad,
                memory: (mem.used / mem.total) * 100,
                disk: disk[0] ? (disk[0].used / disk[0].size) * 100 : 0,
                network: network[0] ? network[0].rx_bytes + network[0].tx_bytes : 0,
                timestamp: Date.now()
            };

            mainWindow.webContents.send('system-stats', systemInfo);
        } catch (error) {
            console.error('Error getting system stats:', error);
        }
    }, 2000);

    // Monitor log files
    startLogMonitoring();
}

// Start log file monitoring
function startLogMonitoring() {
    const logsDir = path.join(process.cwd(), 'logs');

    if (!fs.existsSync(logsDir)) {
        fs.mkdirSync(logsDir, { recursive: true });
    }

    const watcher = chokidar.watch(path.join(logsDir, '*.log'), {
        ignored: /^\./,
        persistent: true
    });

    watcher.on('change', (filePath) => {
        const logName = path.basename(filePath, '.log');

        fs.readFile(filePath, 'utf8', (err, data) => {
            if (err) return;

            const lines = data.split('\n').filter(line => line.trim());
            const lastLine = lines[lines.length - 1];

            if (lastLine) {
                mainWindow.webContents.send('log-update', {
                    logName: logName,
                    line: lastLine,
                    timestamp: Date.now()
                });
            }
        });
    });
}

// Launch startup mode
async function launchMode(modeId, options = {}) {
    try {
        const mode = startupModes[modeId];
        if (!mode) {
            throw new Error(`Unknown mode: ${modeId}`);
        }

        // Check requirements
        const requirements = await checkModeRequirements(mode);
        if (!requirements.met) {
            throw new Error(`Missing requirements: ${requirements.missing.join(', ')}`);
        }

        // Check port availability
        const portCheck = await checkPortsAvailable(mode.ports);
        if (!portCheck.available) {
            throw new Error(`Ports in use: ${portCheck.inUse.join(', ')}`);
        }

        // Notify UI
        mainWindow.webContents.send('mode-status', {
            modeId,
            status: 'starting',
            message: `Starting ${mode.name}...`
        });

        // Prepare environment
        const env = { ...process.env };
        const apiKeys = store.get('apiKeys');

        if (apiKeys.gemini) env.GEMINI_API_KEY = apiKeys.gemini;
        if (apiKeys.openrouter) env.OPENROUTER_API_KEY = apiKeys.openrouter;
        if (apiKeys.zai) env.ZAI_API_KEY = apiKeys.zai;
        if (apiKeys.zaiCodingPlan) env.ZAI_CODING_PLAN = apiKeys.zaiCodingPlan;

        // Use modular launcher if available, otherwise use direct command
        let command = mode.command;
        if (mode.modular && fs.existsSync('launcher_main.py')) {
            command = `python launcher_main.py ${modeId}`;
        }

        // Launch process
        const process = spawn('python', ['-c', command], {
            cwd: process.cwd(),
            env: env,
            stdio: ['pipe', 'pipe', 'pipe']
        });

        // Store process info
        processes.set(modeId, {
            process,
            startTime: Date.now(),
            mode: mode,
            options: options
        });

        // Handle process output
        process.stdout.on('data', (data) => {
            const output = data.toString();
            mainWindow.webContents.send('process-output', {
                modeId,
                type: 'stdout',
                data: output
            });
        });

        process.stderr.on('data', (data) => {
            const output = data.toString();
            mainWindow.webContents.send('process-output', {
                modeId,
                type: 'stderr',
                data: output
            });
        });

        process.on('close', (code) => {
            mainWindow.webContents.send('mode-status', {
                modeId,
                status: code === 0 ? 'completed' : 'failed',
                message: `${mode.name} ${code === 0 ? 'completed' : 'failed'} with code ${code}`,
                exitCode: code
            });
            processes.delete(modeId);
        });

        process.on('error', (error) => {
            mainWindow.webContents.send('mode-status', {
                modeId,
                status: 'error',
                message: `Failed to start ${mode.name}: ${error.message}`,
                error: error.message
            });
            processes.delete(modeId);
        });

        console.log(`Started ${mode.name} (PID: ${process.pid})`);

    } catch (error) {
        mainWindow.webContents.send('mode-status', {
            modeId,
            status: 'error',
            message: error.message
        });
    }
}

// Check mode requirements
async function checkModeRequirements(mode) {
    const apiKeys = store.get('apiKeys');
    const missing = [];

    for (const requirement of mode.requires || []) {
        switch (requirement) {
            case 'gemini':
                if (!apiKeys.gemini) missing.push('Gemini API Key');
                break;
            case 'openrouter':
                if (!apiKeys.openrouter) missing.push('OpenRouter API Key');
                break;
            case 'zai':
                if (!apiKeys.zai) missing.push('Z.ai API Key');
                break;
        }
    }

    return {
        met: missing.length === 0,
        missing: missing
    };
}

// Check port availability
async function checkPortsAvailable(ports) {
    const inUse = [];

    for (const port of ports) {
        try {
            const net = require('net');
            const server = net.createServer();

            await new Promise((resolve, reject) => {
                server.listen(port, () => {
                    server.close(() => resolve());
                }).on('error', reject);
            });
        } catch (error) {
            inUse.push(port);
        }
    }

    return {
        available: inUse.length === 0,
        inUse: inUse
    };
}

// Stop running mode
function stopMode(modeId) {
    const processInfo = processes.get(modeId);
    if (!processInfo) {
        throw new Error(`Mode ${modeId} is not running`);
    }

    try {
        kill(processInfo.process.pid, 'SIGTERM', (err) => {
            if (err) {
                console.error(`Error killing process ${modeId}:`, err);
            } else {
                console.log(`Stopped ${modeId} (PID: ${processInfo.process.pid})`);
            }
        });

        processes.delete(modeId);
        mainWindow.webContents.send('mode-status', {
            modeId,
            status: 'stopped',
            message: `${startupModes[modeId].name} stopped`
        });
    } catch (error) {
        console.error(`Error stopping mode ${modeId}:`, error);
    }
}

// Send chat message to DuckBot
function sendChatMessage(message) {
    if (!chatWs || chatWs.readyState !== WebSocket.OPEN) {
        console.warn('Chat connection not available, message not sent');
        return false;
    }

    try {
        const chatMessage = {
            type: 'message',
            content: message,
            timestamp: Date.now()
        };

        chatWs.send(JSON.stringify(chatMessage));
        return true;
    } catch (error) {
        console.error('Error sending chat message:', error);
        return false;
    }
}

// Send MCP command to DuckBot
function sendMCPCommand(command, params = {}) {
    if (!mcpConnection || mcpConnection.readyState !== WebSocket.OPEN) {
        throw new Error('MCP connection not available');
    }

    const mcpMessage = {
        type: 'command',
        command: command,
        params: params,
        timestamp: Date.now()
    };

    mcpConnection.send(JSON.stringify(mcpMessage));
}

// Startup AI Agent Configuration and Functions
let startupAIConfig = null;

// Load startup AI configuration
function loadStartupAIConfig() {
    try {
        const configPath = path.join(__dirname, '..', 'config', 'startup_ai_config.json');
        if (fs.existsSync(configPath)) {
            const configData = fs.readFileSync(configPath, 'utf8');
            startupAIConfig = JSON.parse(configData);
            console.log('Startup AI configuration loaded successfully');
        } else {
            console.warn('Startup AI configuration not found, using defaults');
            startupAIConfig = {
                name: "DuckBot Startup AI Agent",
                system_prompt: "You are the DuckBot Startup AI Agent, responsible for managing startup operations and providing intelligent assistance."
            };
        }
    } catch (error) {
        console.error('Error loading startup AI configuration:', error);
        startupAIConfig = {
            name: "DuckBot Startup AI Agent",
            system_prompt: "You are the DuckBot Startup AI Agent, responsible for managing startup operations."
        };
    }
}

// Get system info synchronously (for fallback)
function getSystemInfoSync() {
    return {
        name: electronConfig?.system_info?.name || 'DuckBot Enhanced',
        version: electronConfig?.system_info?.version || '4.2',
        environment: electronConfig?.system_info?.environment || 'development',
        debug_mode: electronConfig?.debug_mode || false,
        log_level: electronConfig?.log_level || 'INFO'
    };
}

// Get system information
async function getSystemInfo() {
    try {
        const [cpu, mem, osInfo, graphics, disk, network] = await Promise.all([
            si.cpu(),
            si.mem(),
            si.osInfo(),
            si.graphics(),
            si.diskLayout(),
            si.networkInterfaces()
        ]);

        return {
            cpu: {
                manufacturer: cpu.manufacturer,
                brand: cpu.brand,
                cores: cpu.cores,
                physicalCores: cpu.physicalCores,
                speed: cpu.speed
            },
            memory: {
                total: Math.round(mem.total / 1024 / 1024 / 1024),
                free: Math.round(mem.free / 1024 / 1024 / 1024),
                used: Math.round(mem.used / 1024 / 1024 / 1024)
            },
            os: {
                platform: osInfo.platform,
                distro: osInfo.distro,
                release: osInfo.release,
                arch: osInfo.arch,
                hostname: osInfo.hostname
            },
            graphics: graphics.controllers.map(gpu => ({
                model: gpu.model,
                vendor: gpu.vendor,
                vram: gpu.vram
            })),
            storage: disk.map(disk => ({
                device: disk.device,
                type: disk.type,
                size: Math.round(disk.size / 1024 / 1024 / 1024)
            })),
            network: network.map(net => ({
                iface: net.iface,
                ip4: net.ip4,
                mac: net.mac,
                speed: net.speed
            }))
        };
    } catch (error) {
        console.error('Error getting system info:', error);
        return null;
    }
}

// Get process status
function getProcessStatus() {
    const status = {};

    processes.forEach((info, modeId) => {
        status[modeId] = {
            running: true,
            pid: info.process.pid,
            startTime: info.startTime,
            uptime: Date.now() - info.startTime,
            mode: info.mode
        };
    });

    return status;
}

// Cleanup processes
function cleanupProcesses() {
    processes.forEach((info, modeId) => {
        try {
            kill(info.process.pid, 'SIGTERM');
        } catch (error) {
            console.error(`Error cleaning up process ${modeId}:`, error);
        }
    });
    processes.clear();
}

// Create application menu
function createMenu() {
    const template = [
        {
            label: 'File',
            submenu: [
                {
                    label: 'Launch Traditional Script',
                    click: () => launchTraditionalScript()
                },
                {
                    type: 'separator'
                },
                {
                    label: 'Settings',
                    click: () => mainWindow.webContents.send('show-settings')
                },
                {
                    label: 'Exit',
                    role: 'quit'
                }
            ]
        },
        {
            label: 'Launch',
            submenu: Object.keys(getEnabledStartupModes()).map(modeId => ({
                label: `${startupModes[modeId].icon} ${startupModes[modeId].name}`,
                click: () => launchMode(modeId)
            }))
        },
        {
            label: 'AI Assistant',
            submenu: [
                {
                    label: 'Chat with DuckBot',
                    click: () => mainWindow.webContents.send('focus-chat')
                },
                {
                    label: 'System Diagnostics',
                    click: () => runDiagnostics()
                },
                {
                    label: 'AI Recommendations',
                    click: () => getAIRecommendations()
                }
            ]
        },
        {
            label: 'Tools',
            submenu: [
                {
                    label: 'System Monitor',
                    click: () => mainWindow.webContents.send('show-monitor')
                },
                {
                    label: 'Log Viewer',
                    click: () => openLogsFolder()
                },
                {
                    label: 'Process Manager',
                    click: () => mainWindow.webContents.send('show-process-manager')
                },
                {
                    label: 'Configuration Manager',
                    click: () => mainWindow.webContents.send('show-config-manager')
                }
            ]
        },
        {
            label: 'Help',
            submenu: [
                {
                    label: 'Documentation',
                    click: () => shell.openExternal('https://docs.duckbot.ai')
                },
                {
                    label: 'Check for Updates',
                    click: () => checkForUpdates()
                },
                {
                    label: 'About',
                    click: () => showAboutDialog()
                }
            ]
        }
    ];

    const menu = Menu.buildFromTemplate(template);
    Menu.setApplicationMenu(menu);
}

// Register global shortcuts
function registerGlobalShortcuts() {
    // Quick launch shortcut
    globalShortcut.register('CommandOrControl+Shift+D', () => {
        if (mainWindow) {
            if (mainWindow.isVisible()) {
                mainWindow.hide();
            } else {
                mainWindow.show();
                mainWindow.focus();
            }
        }
    });

    // Chat shortcut
    globalShortcut.register('CommandOrControl+Shift+C', () => {
        if (mainWindow) {
            mainWindow.webContents.send('focus-chat');
            mainWindow.show();
            mainWindow.focus();
        }
    });
}

// Launch traditional startup script
function launchTraditionalScript() {
    const scriptPath = path.join(process.cwd(), 'START_ENHANCED_DUCKBOT.bat');

    if (fs.existsSync(scriptPath)) {
        exec(`start cmd /c "${scriptPath}"`, (error, stdout, stderr) => {
            if (error) {
                console.error(`Error launching script: ${error}`);
                return;
            }
        });
    } else {
        dialog.showMessageBox(mainWindow, {
            type: 'error',
            title: 'Script Not Found',
            message: 'START_ENHANCED_DUCKBOT.bat not found in the current directory.',
            buttons: ['OK']
        });
    }
}

// Open logs folder
function openLogsFolder() {
    const logsPath = path.join(process.cwd(), 'logs');
    if (fs.existsSync(logsPath)) {
        shell.openPath(logsPath);
    } else {
        dialog.showMessageBox(mainWindow, {
            type: 'info',
            title: 'Logs Folder',
            message: 'Logs folder not found. It will be created when you launch a mode.',
            buttons: ['OK']
        });
    }
}

// Run diagnostics
async function runDiagnostics() {
    try {
        const systemInfo = await getSystemInfo();
        const processStatus = getProcessStatus();
        const apiKeys = store.get('apiKeys');

        const diagnostics = {
            system: systemInfo,
            processes: processStatus,
            apiKeys: {
                gemini: !!apiKeys.gemini,
                openrouter: !!apiKeys.openrouter,
                zai: !!apiKeys.zai
            },
            connections: {
                mcp: mcpConnection && mcpConnection.readyState === WebSocket.OPEN,
                chat: chatWs && chatWs.readyState === WebSocket.OPEN
            },
            ports: await checkAllPorts(),
            configuration: {
                bridge_initialized: configBridgeInitialized,
                config_loaded: !!electronConfig,
                startup_modes_count: Object.keys(startupModes).length
            },
            timestamp: Date.now()
        };

        mainWindow.webContents.send('diagnostics-results', diagnostics);
    } catch (error) {
        console.error('Error running diagnostics:', error);
    }
}

// Check all ports
async function checkAllPorts() {
    const allPorts = new Set();
    Object.values(startupModes).forEach(mode => {
        if (mode.ports) {
            mode.ports.forEach(port => allPorts.add(port));
        }
    });

    const portStatus = {};
    for (const port of allPorts) {
        try {
            const net = require('net');
            const server = net.createServer();

            await new Promise((resolve, reject) => {
                server.listen(port, () => {
                    server.close(() => {
                        portStatus[port] = 'available';
                        resolve();
                    });
                }).on('error', () => {
                    portStatus[port] = 'in-use';
                    resolve();
                });
            });
        } catch (error) {
            portStatus[port] = 'error';
        }
    }

    return portStatus;
}

// Get AI recommendations
function getAIRecommendations() {
    const systemInfo = getSystemInfo();
    const processStatus = getProcessStatus();
    const apiKeys = store.get('apiKeys');

    // Send recommendation request to DuckBot
    if (mcpConnection && mcpConnection.readyState === WebSocket.OPEN) {
        sendMCPCommand('get_recommendations', {
            system_info: systemInfo,
            process_status: processStatus,
            api_keys: apiKeys
        });
    }
}

// Show about dialog
function showAboutDialog() {
    dialog.showMessageBox(mainWindow, {
        type: 'info',
        title: 'About DuckBot AI Launcher',
        message: 'DuckBot AI-Powered Launcher',
        detail: `Version ${electronConfig?.system_info?.version || '1.0.0'}\n\nA comprehensive AI-powered startup interface for DuckBot v4.2\n\nFeatures:\n• Deep DuckBot integration\n• Real-time monitoring\n• AI-powered recommendations\n• Complete startup control\n• Centralized configuration management\n\nBuilt with Electron ❤️`,
        buttons: ['OK']
    });
}

// Check for updates
function checkForUpdates() {
    // Placeholder for update checking logic
    dialog.showMessageBox(mainWindow, {
        type: 'info',
        title: 'Check for Updates',
        message: 'Update checking coming soon!',
        buttons: ['OK']
    });
}

// Start minimal services function (direct call)
async function startMinimalServices() {
    const minimalScript = path.join(__dirname, '..', 'START_MINIMAL_SERVICES.bat');

    // Check if minimal services script exists, if not create it
    if (!fs.existsSync(minimalScript)) {
        const minimalScriptContent = `@echo off
echo Starting Minimal DuckBot Services (MCP + Chat)...
cd /d "%~dp0"
start "MCP Server" python ai_ecosystem_manager.py --host 0.0.0.0 --port 8789 --mcp-only
timeout /t 3 /nobreak
start "Chat Server" python -c "
from duckbot.chat_server import ChatServer
import asyncio
server = ChatServer(host='0.0.0.0', port=8790)
asyncio.run(server.start())
"
echo Services started. MCP: localhost:8789, Chat: localhost:8790
pause
`;
        fs.writeFileSync(minimalScript, minimalScriptContent);
    }

    return new Promise((resolve) => {
        const child = spawn('cmd.exe', ['/c', minimalScript], {
            detached: true,
            stdio: 'ignore'
        });

        child.unref();

        // Give it a moment to start, then check status
        setTimeout(async () => {
            const services = await checkDuckBotServices();
            resolve({
                started: services.length > 0,
                services: services
            });
        }, 5000);
    });
}

// Check DuckBot service ports
async function checkDuckBotServices() {
    const services = [];
    const ports = [8787, 8789, 8790]; // WebUI, MCP, Chat

    for (const port of ports) {
        try {
            const response = await axios.get(`http://localhost:${port}`, { timeout: 1000 });
            services.push({
                port: port,
                name: getServiceName(port),
                status: 'running'
            });
        } catch (error) {
            // Check if port is in use but not responding
            const portStatus = await new Promise((resolve) => {
                exec(`netstat -ano | findstr :${port}`, (error, stdout) => {
                    resolve(stdout.includes('LISTENING'));
                });
            });

            if (portStatus) {
                services.push({
                    port: port,
                    name: getServiceName(port),
                    status: 'listening'
                });
            }
        }
    }

    return services;
}

// Get service name by port
function getServiceName(port) {
    switch (port) {
        case 8787: return 'WebUI';
        case 8789: return 'MCP Server';
        case 8790: return 'Chat Server';
        default: return `Port ${port}`;
    }
}

// IPC Handlers
ipcMain.handle('get-startup-modes', () => {
    return getEnabledStartupModes();
});

ipcMain.handle('get-system-info', async () => {
    return await getSystemInfo();
});

ipcMain.handle('get-process-status', () => {
    return getProcessStatus();
});

ipcMain.handle('get-api-keys', () => {
    return store.get('apiKeys');
});

ipcMain.handle('save-api-keys', (event, apiKeys) => {
    store.set('apiKeys', apiKeys);
    return true;
});

ipcMain.handle('get-preferences', () => {
    return store.get('preferences');
});

ipcMain.handle('save-preferences', (event, preferences) => {
    store.set('preferences', preferences);

    // Reset connection counts and retry if AI assistant was enabled
    if (preferences.enableAIAssistant) {
        mcpRetryCount = 0;
        chatRetryCount = 0;
        connectionNotified = false;
        lastMcpAttempt = 0;
        lastChatAttempt = 0;
        mcpConnected = false;
        chatConnected = false;

        // Attempt reconnection after a short delay
        setTimeout(() => {
            connectToDuckBotMCP();
            connectToChatServer();
        }, 1000);
    }

    return true;
});

// Get configuration status
ipcMain.handle('get-configuration-status', () => {
    return {
        initialized: configBridgeInitialized,
        electron_config: electronConfig,
        startup_modes_count: Object.keys(startupModes).length,
        enabled_modes_count: Object.keys(getEnabledStartupModes()).length
    };
});

// Regenerate configuration
ipcMain.handle('regenerate-configuration', async () => {
    try {
        await generateElectronConfiguration();
        return {
            success: true,
            message: 'Configuration regenerated successfully'
        };
    } catch (error) {
        return {
            success: false,
            error: error.message
        };
    }
});

// Manual retry for connections
ipcMain.handle('retry-connections', () => {
    mcpRetryCount = 0;
    chatRetryCount = 0;
    connectionNotified = false;
    lastMcpAttempt = 0;
    lastChatAttempt = 0;
    mcpConnected = false;
    chatConnected = false;

    connectToDuckBotMCP();
    connectToChatServer();

    return true;
});

ipcMain.handle('launch-mode', async (event, modeId, options = {}) => {
    await launchMode(modeId, options);
    return true;
});

ipcMain.handle('stop-mode', async (event, modeId) => {
    stopMode(modeId);
    return true;
});

ipcMain.handle('send-chat-message', async (event, message) => {
    return sendChatMessage(message);
});

ipcMain.handle('send-mcp-command', (event, command, params = {}) => {
    sendMCPCommand(command, params);
    return true;
});

ipcMain.handle('run-diagnostics', async () => {
    await runDiagnostics();
    return true;
});

ipcMain.handle('get-recommendations', () => {
    getAIRecommendations();
    return true;
});

ipcMain.handle('open-external-url', (event, url) => {
    shell.openExternal(url);
    return true;
});

ipcMain.handle('open-folder', (event, folderPath) => {
    shell.openPath(folderPath);
    return true;
});

ipcMain.handle('check-ports', async (event, ports) => {
    const result = await checkPortsAvailable(ports);
    return result;
});

ipcMain.handle('check-mode-requirements', async (event, modeId) => {
    const mode = startupModes[modeId];
    if (!mode) return { met: false, missing: ['Unknown mode'] };

    const result = await checkModeRequirements(mode);
    return result;
});

// App event handlers
app.whenReady().then(() => {
    createWindow();
    registerGlobalShortcuts(); // Register shortcuts after app is ready
});

app.on('window-all-closed', () => {
    // Unregister global shortcuts
    globalShortcut.unregisterAll();

    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
        createWindow();
    }
});

app.on('will-quit', () => {
    // Unregister global shortcuts if app is ready
    try {
        globalShortcut.unregisterAll();
    } catch (error) {
        console.log('Could not unregister global shortcuts:', error.message);
    }
});

// Handle second instance
const gotTheLock = app.requestSingleInstanceLock();

if (!gotTheLock) {
    app.quit();
} else {
    app.on('second-instance', () => {
        // Someone tried to run a second instance, we should focus our window
        if (mainWindow) {
            if (mainWindow.isMinimized()) mainWindow.restore();
            mainWindow.focus();
        }
    });
}

// Process unhandled exceptions
process.on('uncaughtException', (error) => {
    console.error('Uncaught Exception:', error);

    if (mainWindow) {
        mainWindow.webContents.send('uncaught-exception', {
            message: error.message,
            stack: error.stack
        });
    }
});

process.on('unhandledRejection', (reason, promise) => {
    console.error('Unhandled Rejection at:', promise, 'reason:', reason);

    if (mainWindow) {
        // Make the error objects serializable
        const serializableReason = reason instanceof Error ? {
            message: reason.message,
            stack: reason.stack,
            name: reason.name
        } : String(reason);

        mainWindow.webContents.send('unhandled-rejection', {
            reason: serializableReason,
            promise: String(promise)
        });
    }
});