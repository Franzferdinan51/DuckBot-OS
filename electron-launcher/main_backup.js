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

// DuckBot startup modes configuration - Using new modular launcher system
const startupModes = {
    // Core launch modes from modular launcher
    'ultimate': {
        name: '🚀 Ultimate Complete Mode',
        description: 'Complete enhanced mode with all integrations using new modular launcher',
        icon: '🚀',
        category: 'complete',
        requires: ['gemini', 'openrouter'],
        command: 'python launcher_main.py ultimate',
        ports: [8787, 8788, 8789, 8790, 8000, 7799, 7788],
        modular: true
    },
    'enhanced-webui': {
        name: '🌐 Enhanced WebUI Mode',
        description: 'Modern web interface with real-time updates',
        icon: '🌐',
        category: 'web',
        requires: ['openrouter'],
        command: 'python launcher_main.py enhanced_webui',
        ports: [8787, 8788, 8789],
        modular: true
    },
    'monitoring': {
        name: '📊 System Monitoring Mode',
        description: 'Real-time system metrics and performance tracking',
        icon: '📊',
        category: 'monitoring',
        requires: [],
        command: 'python launcher_main.py monitoring',
        ports: [8788, 8789],
        modular: true
    },
    'local-only': {
        name: '🔒 Local Privacy Mode',
        description: 'Complete offline operation with LM Studio',
        icon: '🔒',
        category: 'privacy',
        requires: [],
        command: 'python launcher_main.py local_only',
        ports: [8787, 8788, 8789],
        modular: true
    },
    'hybrid': {
        name: '☁️ Hybrid Cloud+Local Mode',
        description: 'Intelligent local/cloud AI routing',
        icon: '☁️',
        category: 'hybrid',
        requires: ['gemini', 'openrouter'],
        command: 'python launcher_main.py hybrid',
        ports: [8787, 8788, 8789],
        modular: true
    },
    'duckbot-os': {
        name: '🖥️ DuckBotOS Mode',
        description: 'AI web operating system',
        icon: '🖥️',
        category: 'os',
        requires: ['gemini', 'openrouter'],
        command: 'python launcher_main.py duckbot_os',
        ports: [8080, 8788, 8789],
        modular: true
    },
    'minimal': {
        name: '⚡ Minimal Resource Mode',
        description: 'Essential services only for low-resource systems',
        icon: '⚡',
        category: 'minimal',
        requires: [],
        command: 'python launcher_main.py minimal',
        ports: [8787, 8789],
        modular: true
    },
    'developer': {
        name: '🔧 Developer Debug Mode',
        description: 'Full debugging and development tools',
        icon: '🔧',
        category: 'development',
        requires: ['gemini', 'openrouter'],
        command: 'python launcher_main.py developer',
        ports: [8787, 8788, 8789],
        modular: true
    },

    // Individual service modes for granular control
    'enhanced-webui-only': {
        name: 'Enhanced WebUI Only',
        description: 'Modern web interface standalone',
        icon: '🌐',
        category: 'web',
        requires: ['openrouter'],
        command: 'python launcher_main.py service enhanced_webui',
        ports: [8787],
        modular: true
    },
    'system-monitoring-only': {
        name: 'System Monitoring Only',
        description: 'Real-time monitoring standalone',
        icon: '📊',
        category: 'monitoring',
        requires: [],
        command: 'python launcher_main.py service system_monitoring',
        ports: [8789],
        modular: true
    },
    'bytebot': {
        name: 'ByteBot Desktop Automation',
        description: 'Complete computer control with AI',
        icon: '🤖',
        category: 'automation',
        requires: ['gemini'],
        command: 'python launcher_main.py service bytebot',
        ports: [],
        modular: true
    },
    'ui-tars': {
        name: 'UI-TARS GUI Automation',
        description: 'Advanced visual element detection',
        icon: '👁️',
        category: 'automation',
        requires: ['gemini'],
        command: 'python launcher_main.py service ui_tars',
        ports: [7799],
        modular: true
    },
    'browser-automation': {
        name: 'Browser Automation',
        description: 'AI-powered web automation',
        icon: '🌍',
        category: 'automation',
        requires: ['gemini'],
        command: 'python launcher_main.py service browser_automation',
        ports: [7788],
        modular: true
    },
    'archon': {
        name: 'Archon Multi-Agent System',
        description: 'Advanced orchestration and knowledge management',
        icon: '🧠',
        category: 'ai',
        requires: ['openrouter'],
        command: 'python launcher_main.py service archon',
        ports: [],
        modular: true
    },
    'ai-ecosystem': {
        name: 'AI Ecosystem Manager',
        description: 'AI-powered ecosystem management',
        icon: '🧠',
        category: 'ai',
        requires: ['gemini', 'openrouter'],
        command: 'python launcher_main.py service ai_ecosystem',
        ports: [],
        modular: true
    },
    'local-ecosystem': {
        name: 'Local Ecosystem',
        description: 'Local-only AI ecosystem',
        icon: '🔒',
        category: 'ai',
        requires: [],
        command: 'python launcher_main.py service local_ecosystem',
        ports: [],
        modular: true
    },
    'mcp-server': {
        name: 'MCP Server',
        description: 'Model Context Protocol server',
        icon: '🔌',
        category: 'protocols',
        requires: [],
        command: 'python launcher_main.py service mcp_server',
        ports: [8000],
        modular: true
    },
    'discord-bot': {
        name: 'Discord Bot with VibeVoice',
        description: 'Discord integration with voice capabilities',
        icon: '🎮',
        category: 'communication',
        requires: [],
        command: 'python launcher_main.py service discord_bot',
        ports: [],
        modular: true
    },
    'vibevoice': {
        name: 'Microsoft VibeVoice TTS',
        description: 'Text-to-speech with Microsoft VibeVoice',
        icon: '🎤',
        category: 'voice',
        requires: [],
        command: 'python launcher_main.py service vibevoice',
        ports: [],
        modular: true
    },
    'charm-terminal': {
        name: 'Charm Terminal Interface',
        description: 'Beautiful interactive command-line',
        icon: '💻',
        category: 'terminal',
        requires: [],
        command: 'python launcher_main.py service charm_terminal',
        ports: [],
        modular: true
    },

    // Legacy modes for backward compatibility
    'classic': {
        name: 'Classic Mode',
        description: 'Original DuckBot experience',
        icon: '📜',
        category: 'classic',
        requires: [],
        command: 'python -m duckbot.webui',
        ports: [8787],
        modular: false
    },
    'ai-router': {
        name: 'AI Router System',
        description: 'Intelligent AI model selection',
        icon: '🔀',
        category: 'ai',
        requires: ['gemini', 'openrouter'],
        command: 'python duckbot/ai_router_gpt.py',
        ports: [8789],
        modular: false
    },
    'webui-stack': {
        name: 'WebUI Stack',
        description: 'Complete web interface suite',
        icon: '🌐',
        category: 'web',
        requires: ['openrouter'],
        command: 'python duckbot/webui_manager.py',
        ports: [8788],
        modular: false
    },
    'ai-monitor': {
        name: 'AI Monitor',
        description: 'AI-powered system monitoring',
        icon: '📊',
        category: 'monitoring',
        requires: ['gemini'],
        command: 'python duckbot/monitoring_dashboard.py',
        ports: [8789],
        modular: false
    },
    'mining-mgr': {
        name: 'Mining Manager',
        description: 'Cryptocurrency mining management',
        icon: '⛏️',
        category: 'mining',
        requires: [],
        command: 'python duckbot/mining_manager.py',
        ports: [],
        modular: false
    },
    'livekit': {
        name: 'LiveKit Real-Time Communication',
        description: 'Real-time audio/video communication',
        icon: '🎥',
        category: 'communication',
        requires: [],
        command: 'python duckbot/livekit_integration.py',
        ports: [],
        modular: false
    },
    'n8n-agent': {
        name: 'N8N Workflow Automation',
        description: 'Advanced workflow automation',
        icon: '⚙️',
        category: 'automation',
        requires: ['zai'],
        command: 'python duckbot/n8n_agent_integration.py',
        ports: [],
        modular: false
    },
    'learning': {
        name: 'AI Learning System',
        description: 'Adaptive AI learning and memory',
        icon: '📚',
        category: 'ai',
        requires: ['gemini'],
        command: 'python duckbot/learning_system.py',
        ports: [],
        modular: false
    }
};

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

        // Initialize startup AI agent
        console.log('Initializing DuckBot Startup AI Agent...');
        loadStartupAIConfig();

        // Initialize connections
        initializeConnections();

        // Start system monitoring
        startSystemMonitoring();

        console.log('DuckBot Startup AI Agent ready');
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

        // Launch process
        let command, args;

        if (mode.modular) {
            // Use modular launcher
            if (mode.command.includes('service')) {
                // Individual service mode
                const serviceName = mode.command.split(' ')[2];
                command = 'python';
                args = ['launcher_main.py', 'service', serviceName];
            } else {
                // Launch mode
                const modeName = mode.command.split(' ')[1];
                command = 'python';
                args = ['launcher_main.py', modeName];
            }
        } else {
            // Legacy mode
            command = 'python';
            args = ['-c', mode.command];
        }

        const process = spawn(command, args, {
            cwd: process.cwd(),
            env: env,
            stdio: ['pipe', 'pipe', 'pipe']
        });

        // Store process info
        processes.set(modeId, {
            process,
            startTime: Date.now(),
            mode: mode,
            options: options,
            modular: mode.modular
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
            // Removed sessionId to prevent cloning issues
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

// Process startup AI requests
async function processStartupAIRequest(userMessage, context = {}) {
    if (!startupAIConfig) {
        loadStartupAIConfig();
    }

    // Build context-aware prompt
    const systemContext = {
        current_system_state: {
            running_processes: Array.from(processes.entries()).map(([id, info]) => ({
                modeId: id,
                modeName: startupModes[id]?.name || 'Unknown',
                pid: info.process.pid,
                startTime: info.startTime,
                status: 'running'
            })),
            system_resources: await getSystemInfo(),
            api_keys_configured: {
                gemini: !!store.get('apiKeys.gemini'),
                openrouter: !!store.get('apiKeys.openrouter'),
                zai: !!store.get('apiKeys.zai'),
                zai_coding_plan: !!store.get('apiKeys.zaiCodingPlan')
            },
            connection_status: {
                mcp: mcpConnection?.readyState === WebSocket.OPEN,
                chat: chatWs?.readyState === WebSocket.OPEN
            },
            active_features: {
                monitoring: store.get('preferences.enableAIAssistant', false),
                notifications: store.get('preferences.enableNotifications', true),
                auto_reconnect: store.get('preferences.autoReconnect', true)
            }
        },
        user_context: context,
        available_modes: startupModes,
        capabilities: startupAIConfig?.capabilities || []
    };

    // Create enhanced prompt with context
    const enhancedPrompt = `${startupAIConfig.system_prompt}\n\n## Current System Context\n${JSON.stringify(systemContext, null, 2)}\n\n## User Request\n${userMessage}\n\n## Instructions\nRespond as the Startup AI Agent with:\n1. Clear assessment of current system state\n2. Intelligent recommendations for startup operations\n3. Specific actionable steps\n4. System performance considerations\n5. Error prevention and optimization suggestions`;

    // Try to get AI response from DuckBot first, fallback to local processing
    if (chatWs && chatWs.readyState === WebSocket.OPEN) {
        try {
            const response = await sendStartupAIRequestToDuckBot(enhancedPrompt);
            return response;
        } catch (error) {
            console.warn('DuckBot AI response failed, using local processing:', error);
        }
    }

    // Fallback to local AI processing
    return await localStartupAIProcessing(userMessage, systemContext);
}

// Send startup AI request to DuckBot
async function sendStartupAIRequestToDuckBot(enhancedPrompt) {
    return new Promise((resolve, reject) => {
        const requestId = `startup_ai_${Date.now()}`;

        const message = {
            type: 'startup_ai_request',
            id: requestId,
            prompt: enhancedPrompt,
            context: 'startup_management',
            timestamp: Date.now()
        };

        chatWs.send(JSON.stringify(message));

        // Set up response handler
        const responseHandler = (data) => {
            try {
                const response = JSON.parse(data);
                if (response.id === requestId && response.type === 'startup_ai_response') {
                    chatWs.removeListener('message', responseHandler);
                    resolve(response.content);
                }
            } catch (error) {
                console.error('Error processing startup AI response:', error);
            }
        };

        chatWs.on('message', responseHandler);

        // Timeout fallback
        setTimeout(() => {
            chatWs.removeListener('message', responseHandler);
            reject(new Error('Startup AI request timeout'));
        }, 30000); // 30 second timeout
    });
}

// Local startup AI processing (fallback)
async function localStartupAIProcessing(userMessage, systemContext) {
    // Simple rule-based AI for startup operations
    const lowerMessage = userMessage.toLowerCase();

    // Analyze user intent
    if (lowerMessage.includes('start') || lowerMessage.includes('launch')) {
        return await handleStartupRequest(lowerMessage, systemContext);
    } else if (lowerMessage.includes('stop') || lowerMessage.includes('kill')) {
        return await handleStopRequest(lowerMessage, systemContext);
    } else if (lowerMessage.includes('status') || lowerMessage.includes('running')) {
        return await handleStatusRequest(systemContext);
    } else if (lowerMessage.includes('recommend') || lowerMessage.includes('best')) {
        return await handleRecommendationRequest(systemContext);
    } else if (lowerMessage.includes('problem') || lowerMessage.includes('error') || lowerMessage.includes('issue')) {
        return await handleTroubleshootingRequest(systemContext);
    } else {
        return await handleGeneralRequest(userMessage, systemContext);
    }
}

// Handle startup requests
async function handleStartupRequest(message, context) {
    const runningProcesses = context.current_system_state.running_processes;
    const systemResources = context.current_system_state.system_resources;

    // Determine which mode to start
    let targetMode = null;
    let reasoning = '';

    if (message.includes('ultimate') || message.includes('complete')) {
        targetMode = '1';
        reasoning = 'Starting Ultimate Complete Mode for full system capabilities';
    } else if (message.includes('bytebot')) {
        targetMode = '15';
        reasoning = 'Starting ByteBot for desktop automation';
    } else if (message.includes('ui-tars')) {
        targetMode = '16';
        reasoning = 'Starting UI-TARS for GUI automation';
    } else if (message.includes('archon')) {
        targetMode = '17';
        reasoning = 'Starting Archon multi-agent system';
    } else if (message.includes('webui')) {
        targetMode = '20';
        reasoning = 'Starting WebUI stack for web interface';
    } else {
        // Default recommendation based on system resources
        if (systemResources.mem.total > 8000000000) { // 8GB+
            targetMode = '1';
            reasoning = 'Recommended Ultimate Complete Mode based on your system resources';
        } else {
            targetMode = '15';
            reasoning = 'Recommended ByteBot for optimal performance on your system';
        }
    }

    if (targetMode) {
        try {
            await launchMode(targetMode);
            return `🚀 ${reasoning}\n\n✅ Successfully started ${startupModes[targetMode].name}\n📊 System Status: ${runningProcesses.length + 1} processes running\n💡 Next steps: Monitor the process status and check logs for any issues`;
        } catch (error) {
            return `❌ Failed to start ${startupModes[targetMode].name}\n\n🔍 Error: ${error.message}\n💡 Suggestion: Check port availability and API key configuration`;
        }
    }

    return '🤔 I\'m not sure which mode you want to start. Please specify a mode (e.g., "start bytebot", "start ultimate", "start webui")';
}

// Handle stop requests
async function handleStopRequest(message, context) {
    const runningProcesses = context.current_system_state.running_processes;

    if (runningProcesses.length === 0) {
        return 'ℹ️ No processes are currently running';
    }

    // Find process to stop
    let processToStop = null;

    if (message.includes('all')) {
        // Stop all processes
        for (const [modeId] of runningProcesses) {
            try {
                await stopMode(modeId);
            } catch (error) {
                console.error(`Error stopping ${modeId}:`, error);
            }
        }
        return `🛑 Stopped all ${runningProcesses.length} running processes`;
    }

    // Stop specific process
    for (const [modeId, processInfo] of runningProcesses) {
        if (message.includes(processInfo.modeName.toLowerCase()) ||
            message.includes(modeId) ||
            (message.includes('bytebot') && modeId === '15') ||
            (message.includes('ui-tars') && modeId === '16') ||
            (message.includes('archon') && modeId === '17')) {
            processToStop = modeId;
            break;
        }
    }

    if (processToStop) {
        try {
            await stopMode(processToStop);
            return `🛑 Successfully stopped ${startupModes[processToStop].name}`;
        } catch (error) {
            return `❌ Failed to stop ${startupModes[processToStop].name}: ${error.message}`;
        }
    }

    return `🤔 I can\'t find a matching process to stop. Running processes: ${runningProcesses.map(p => p.modeName).join(', ')}`;
}

// Handle status requests
async function handleStatusRequest(context) {
    const runningProcesses = context.current_system_state.running_processes;
    const systemResources = context.current_system_state.system_resources;

    if (runningProcesses.length === 0) {
        return '📊 **System Status: Idle**\n\n💤 No DuckBot processes are currently running\n💡 Ready to start any mode when you\'re ready';
    }

    let status = `📊 **System Status: Active**\n\n🏃 **Running Processes (${runningProcesses.length}):**\n`;

    for (const processInfo of runningProcesses) {
        const uptime = Date.now() - processInfo.startTime;
        const uptimeMinutes = Math.floor(uptime / 60000);
        status += `• ${processInfo.modeName} (PID: ${processInfo.pid}) - Running for ${uptimeMinutes}m\n`;
    }

    status += `\n💾 **System Resources:**\n`;
    status += `• Memory: ${Math.round(systemResources.mem.used / 1024 / 1024 / 1024)}GB / ${Math.round(systemResources.mem.total / 1024 / 1024 / 1024)}GB (${Math.round(systemResources.mem.percent)}%)\n`;
    status += `• CPU: ${systemResources.currentLoad?.currentLoad || 'N/A'}% load\n`;

    return status;
}

// Handle recommendation requests
async function handleRecommendationRequest(context) {
    const systemResources = context.current_system_state.system_resources;
    const apiKeys = context.current_system_state.api_keys_configured;

    let recommendations = [];

    // Memory-based recommendations
    if (systemResources.mem.total > 16000000000) { // 16GB+
        recommendations.push('💡 **Ultimate Complete Mode** - Your system has excellent memory capacity');
    } else if (systemResources.mem.total > 8000000000) { // 8GB+
        recommendations.push('💡 **Ultimate AI Mode** - Good balance of features for your system');
    } else {
        recommendations.push('💡 **Individual Component Modes** - Start specific services as needed');
    }

    // API key-based recommendations
    if (apiKeys.gemini && apiKeys.openrouter) {
        recommendations.push('🔑 **Full AI Stack** - You have all API keys configured for maximum AI capabilities');
    } else if (apiKeys.gemini) {
        recommendations.push('🔑 **Gemini-Powered Features** - Try ByteBot or UI-TARS for automation');
    } else {
        recommendations.push('⚠️ **Configure API Keys** - Add Gemini and OpenRouter keys for AI features');
    }

    // Process-based recommendations
    const runningProcesses = context.current_system_state.running_processes;
    if (runningProcesses.length === 0) {
        recommendations.push('🚀 **Ready to Start** - Choose any startup mode to begin');
    } else if (runningProcesses.length < 3) {
        recommendations.push('🔧 **Additional Services** - Consider starting complementary services');
    } else {
        recommendations.push('⚡ **System Active** - Monitor current processes for optimization');
    }

    return `🎯 **AI Recommendations for Your System:**\n\n${recommendations.join('\n')}\n\n💬 **Ask me** to start any recommended mode or explain specific features!`;
}

// Handle troubleshooting requests
async function handleTroubleshootingRequest(context) {
    const runningProcesses = context.current_system_state.running_processes;
    const connectionStatus = context.current_system_state.connection_status;

    let troubleshooting = '🔧 **System Troubleshooting:**\n\n';

    // Connection issues
    if (!connectionStatus.mcp && !connectionStatus.chat) {
        troubleshooting += '❌ **No DuckBot Connection** - Start DuckBot main system first\n';
        troubleshooting += '💡 Run: START_ENHANCED_DUCKBOT.bat and choose Ultimate mode\n\n';
    } else if (!connectionStatus.mcp) {
        troubleshooting += '⚠️ **MCP Connection Issue** - System control limited\n\n';
    } else if (!connectionStatus.chat) {
        troubleshooting += '⚠️ **Chat Connection Issue** - AI assistant unavailable\n\n';
    }

    // Resource issues
    const systemResources = context.current_system_state.system_resources;
    if (systemResources.mem.percent > 85) {
        troubleshooting += '⚠️ **High Memory Usage** - Consider stopping unnecessary processes\n\n';
    }

    // Process issues
    if (runningProcesses.length === 0) {
        troubleshooting += '💤 **No Active Processes** - This is normal if you\'re just getting started\n\n';
    } else {
        troubleshooting += '✅ **Processes Running** - System appears to be operational\n\n';
    }

    troubleshooting += '💡 **Common Solutions:**\n';
    troubleshooting += '• Restart the launcher if connections are unstable\n';
    troubleshooting += '• Check port availability (8788-8790)\n';
    troubleshooting += '• Verify API keys are configured\n';
    troubleshooting += '• Review log files for detailed errors\n';

    return troubleshooting;
}

// Handle general requests
async function handleGeneralRequest(message, context) {
    const runningProcesses = context.current_system_state.running_processes;

    return `🤖 **DuckBot Startup AI Assistant**\n\nI'm here to help you manage DuckBot startup operations! Here's what I can do:\n\n🚀 **Start Modes:** "start bytebot", "start ultimate", "start webui"\n🛑 **Stop Processes:** "stop all", "stop bytebot"\n📊 **Check Status:** "what's running", "system status"\n🎯 **Get Recommendations:** "what should I run", "recommend mode"\n🔧 **Troubleshoot:** "help with issues", "fix problems"\n\n**Current Status:** ${runningProcesses.length} processes running\n\n💬 Ask me anything about DuckBot startup operations!`;
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
            mode: info.mode,
            modular: info.modular || false
        };
    });

    return status;
}

// Get modular launcher status
async function getModularLauncherStatus() {
    try {
        const { exec } = require('child_process');
        const util = require('util');
        const execAsync = util.promisify(exec);

        // Check if modular launcher is available
        const result = await execAsync('python launcher_main.py --help', { timeout: 5000 });

        return {
            available: true,
            version: '1.0.0',
            capabilities: [
                'service_management',
                'launch_modes',
                'port_management',
                'health_monitoring',
                'configuration_management'
            ]
        };
    } catch (error) {
        return {
            available: false,
            error: error.message,
            capabilities: []
        };
    }
}

// Get available services from modular launcher
async function getAvailableServices() {
    try {
        const { exec } = require('child_process');
        const util = require('util');
        const execAsync = util.promisify(exec);

        const result = await execAsync('python launcher_main.py --list-services', { timeout: 10000 });

        if (result.stdout) {
            try {
                return JSON.parse(result.stdout);
            } catch (parseError) {
                console.warn('Failed to parse services JSON:', parseError);
                return [];
            }
        }
        return [];
    } catch (error) {
        console.error('Failed to get available services:', error);
        return [];
    }
}

// Get service status from modular launcher
async function getServiceStatus(serviceName) {
    try {
        const { exec } = require('child_process');
        const util = require('util');
        const execAsync = util.promisify(exec);

        const result = await execAsync(`python launcher_main.py --service-status ${serviceName}`, { timeout: 5000 });

        if (result.stdout) {
            try {
                return JSON.parse(result.stdout);
            } catch (parseError) {
                console.warn('Failed to parse service status JSON:', parseError);
                return null;
            }
        }
        return null;
    } catch (error) {
        console.error(`Failed to get service status for ${serviceName}:`, error);
        return null;
    }
}

// Launch individual service using modular launcher
async function launchService(serviceName) {
    try {
        const modeId = `service-${serviceName}`;

        // Check if already running
        if (processes.has(modeId)) {
            throw new Error(`Service ${serviceName} is already running`);
        }

        // Notify UI
        mainWindow.webContents.send('mode-status', {
            modeId,
            status: 'starting',
            message: `Starting service: ${serviceName}...`
        });

        // Prepare environment
        const env = { ...process.env };
        const apiKeys = store.get('apiKeys');

        if (apiKeys.gemini) env.GEMINI_API_KEY = apiKeys.gemini;
        if (apiKeys.openrouter) env.OPENROUTER_API_KEY = apiKeys.openrouter;
        if (apiKeys.zai) env.ZAI_API_KEY = apiKeys.zai;

        // Launch service using modular launcher
        const process = spawn('python', ['launcher_main.py', 'service', serviceName], {
            cwd: process.cwd(),
            env: env,
            stdio: ['pipe', 'pipe', 'pipe']
        });

        // Store process info
        processes.set(modeId, {
            process,
            startTime: Date.now(),
            mode: {
                name: `Service: ${serviceName}`,
                description: `Individual service: ${serviceName}`,
                icon: '🔧'
            },
            options: {},
            modular: true,
            serviceName: serviceName
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
                message: `Service ${serviceName} ${code === 0 ? 'completed' : 'failed'} with code ${code}`,
                exitCode: code
            });
            processes.delete(modeId);
        });

        process.on('error', (error) => {
            mainWindow.webContents.send('mode-status', {
                modeId,
                status: 'error',
                message: `Failed to start service ${serviceName}: ${error.message}`,
                error: error.message
            });
            processes.delete(modeId);
        });

        console.log(`Started service ${serviceName} (PID: ${process.pid})`);

    } catch (error) {
        mainWindow.webContents.send('mode-status', {
            modeId: `service-${serviceName}`,
            status: 'error',
            message: error.message
        });
    }
}

// Stop individual service
async function stopService(serviceName) {
    const modeId = `service-${serviceName}`;
    const processInfo = processes.get(modeId);

    if (!processInfo) {
        throw new Error(`Service ${serviceName} is not running`);
    }

    try {
        kill(processInfo.process.pid, 'SIGTERM', (err) => {
            if (err) {
                console.error(`Error stopping service ${serviceName}:`, err);
            } else {
                console.log(`Stopped service ${serviceName} (PID: ${processInfo.process.pid})`);
            }
        });

        processes.delete(modeId);
        mainWindow.webContents.send('mode-status', {
            modeId,
            status: 'stopped',
            message: `Service ${serviceName} stopped`
        });
    } catch (error) {
        console.error(`Error stopping service ${serviceName}:`, error);
    }
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
            submenu: Object.keys(startupModes).map(modeId => ({
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
        mode.ports.forEach(port => allPorts.add(port));
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
        detail: 'Version 1.0.0\n\nA comprehensive AI-powered startup interface for DuckBot v4.2\n\nFeatures:\n• Deep DuckBot integration\n• Real-time monitoring\n• AI-powered recommendations\n• Complete startup control\n\nBuilt with Electron ❤️',
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

// IPC Handlers
ipcMain.handle('get-startup-modes', () => {
    return startupModes;
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

// Check if DuckBot processes are running
ipcMain.handle('check-duckbot-status', async () => {
    const processes = await findRunningDuckBotProcesses();
    const services = await checkDuckBotServices();

    return {
        processes: processes,
        services: services,
        isRunning: processes.length > 0 || services.length > 0,
        recommendation: getDuckBotRecommendation(processes, services)
    };
});

// Auto-start DuckBot with recommended mode
ipcMain.handle('start-duckbot-recommended', async (event, mode = 'ultimate') => {
    const startupScript = path.join(__dirname, '..', 'START_ENHANCED_DUCKBOT.bat');

    return new Promise((resolve) => {
        const child = spawn('cmd.exe', ['/c', startupScript], {
            detached: true,
            stdio: 'ignore'
        });

        child.unref();

        // Give it a moment to start, then check status
        setTimeout(async () => {
            const status = await checkDuckBotServices();
            resolve({
                started: status.length > 0,
                services: status,
                mode: mode
            });
        }, 5000);
    });
});

// Start MCP server only
ipcMain.handle('start-mcp-server', async () => {
    const mcpScript = path.join(__dirname, '..', 'START_MCP_ONLY.bat');

    // Check if MCP-only script exists, if not create it
    if (!fs.existsSync(mcpScript)) {
        const mcpScriptContent = `@echo off
echo Starting DuckBot MCP Server...
cd /d "%~dp0"
python ai_ecosystem_manager.py --host 0.0.0.0 --port 8789 --mcp-only
pause
`;
        fs.writeFileSync(mcpScript, mcpScriptContent);
    }

    return new Promise((resolve) => {
        const child = spawn('cmd.exe', ['/c', mcpScript], {
            detached: true,
            stdio: 'ignore'
        });

        child.unref();

        // Give it a moment to start, then check status
        setTimeout(async () => {
            const services = await checkDuckBotServices();
            const mcpService = services.find(s => s.port === 8789);
            resolve({
                started: !!mcpService,
                service: mcpService
            });
        }, 3000);
    });
});

// Start minimal DuckBot services (MCP + Chat)
ipcMain.handle('start-minimal-services', async () => {
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
});

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

// Find running DuckBot processes
async function findRunningDuckBotProcesses() {
    return new Promise((resolve) => {
        exec('tasklist /fi "imagename eq python.exe" /fo csv /nh', (error, stdout) => {
            if (error) {
                resolve([]);
                return;
            }

            const lines = stdout.split('\n');
            const processes = [];

            for (const line of lines) {
                if (line.includes('python') &&
                    (line.includes('duckbot') ||
                     line.includes('enhanced') ||
                     line.includes('webui') ||
                     line.includes('ai_ecosystem'))) {
                    processes.push(line.trim());
                }
            }

            resolve(processes);
        });
    });
}

// Check DuckBot service ports
async function checkDuckBotServices() {
    const services = [];
    const ports = [8788, 8789, 8790]; // WebUI, MCP, Chat

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
        case 8788: return 'WebUI';
        case 8789: return 'MCP Server';
        case 8790: return 'Chat Server';
        default: return `Port ${port}`;
    }
}

// Get DuckBot startup recommendation
function getDuckBotRecommendation(processes, services) {
    if (processes.length === 0 && services.length === 0) {
        return {
            action: 'start',
            message: 'DuckBot is not running. Start the Ultimate mode for full functionality.',
            mode: 'ultimate',
            priority: 'high'
        };
    }

    if (services.length < 3) {
        return {
            action: 'restart',
            message: 'DuckBot is partially running. Restart with Ultimate mode for all services.',
            mode: 'ultimate',
            priority: 'medium'
        };
    }

    return {
        action: 'none',
        message: 'DuckBot is running with all services.',
        mode: 'none',
        priority: 'low'
    };
}

ipcMain.handle('launch-mode', async (event, modeId, options = {}) => {
    await launchMode(modeId, options);
    return true;
});

ipcMain.handle('stop-mode', async (event, modeId) => {
    stopMode(modeId);
    return true;
});

ipcMain.handle('send-chat-message', async (event, message) => {
    // Send to both traditional chat and startup AI for comprehensive response
    const traditionalResponse = sendChatMessage(message);

    // Get startup AI response
    try {
        const startupAIResponse = await processStartupAIRequest(message);

        // Send the startup AI response back to the renderer
        event.sender.send('startup-ai-response', {
            type: 'startup_ai',
            content: startupAIResponse,
            timestamp: Date.now(),
            agent: startupAIConfig?.name || 'DuckBot Startup AI Agent'
        });

        return { traditionalSent: traditionalResponse, startupAI: true };
    } catch (error) {
        console.error('Startup AI processing error:', error);
        sendChatMessage(message); // Fallback to traditional only
        return { traditionalSent: traditionalResponse, startupAI: false };
    }
});

// Handle startup AI specific requests
ipcMain.handle('send-startup-ai-request', async (event, message, context = {}) => {
    try {
        const response = await processStartupAIRequest(message, context);
        return {
            success: true,
            response: response,
            agent: startupAIConfig?.name || 'DuckBot Startup AI Agent'
        };
    } catch (error) {
        console.error('Startup AI request error:', error);
        return {
            success: false,
            error: error.message,
            response: 'Sorry, I encountered an error processing your request. Please try again.'
        };
    }
});

// Get startup AI configuration
ipcMain.handle('get-startup-ai-config', () => {
    if (!startupAIConfig) {
        loadStartupAIConfig();
    }
    return {
        config: startupAIConfig,
        loaded: !!startupAIConfig,
        capabilities: startupAIConfig?.capabilities || []
    };
});

// Update startup AI configuration
ipcMain.handle('update-startup-ai-config', (event, updates) => {
    try {
        if (!startupAIConfig) {
            loadStartupAIConfig();
        }

        // Merge updates with existing config
        startupAIConfig = { ...startupAIConfig, ...updates };

        // Save to file
        const configPath = path.join(__dirname, '..', 'config', 'startup_ai_config.json');
        fs.writeFileSync(configPath, JSON.stringify(startupAIConfig, null, 2));

        console.log('Startup AI configuration updated successfully');
        return { success: true, config: startupAIConfig };
    } catch (error) {
        console.error('Error updating startup AI configuration:', error);
        return { success: false, error: error.message };
    }
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

// Modular launcher IPC handlers
ipcMain.handle('get-modular-launcher-status', async () => {
    return await getModularLauncherStatus();
});

ipcMain.handle('get-available-services', async () => {
    return await getAvailableServices();
});

ipcMain.handle('get-service-status', async (event, serviceName) => {
    return await getServiceStatus(serviceName);
});

ipcMain.handle('launch-service', async (event, serviceName) => {
    await launchService(serviceName);
    return true;
});

ipcMain.handle('stop-service', async (event, serviceName) => {
    await stopService(serviceName);
    return true;
});

ipcMain.handle('get-launcher-system-status', async () => {
    const modularStatus = await getModularLauncherStatus();
    const processStatus = getProcessStatus();
    const availableServices = await getAvailableServices();

    return {
        modular: modularStatus,
        processes: processStatus,
        services: availableServices,
        uptime: process.uptime(),
        timestamp: Date.now()
    };
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