/* DuckBot AI Desktop Extension - Main Extension File */

const { GObject, St, Clutter, Gio, GLib } = imports.gi;
const ByteArray = imports.byteArray;
const Main = imports.ui.main;
const PanelMenu = imports.ui.panelMenu;
const PopupMenu = imports.ui.popupMenu;
const ExtensionUtils = imports.misc.extensionUtils;

const Me = ExtensionUtils.getCurrentExtension();

let duckbotPanel = null;
let aiService = null;
let voiceControl = null;
let memoryManager = null;

// AI Panel Button in Top Bar
var DuckBotPanel = GObject.registerClass(
class DuckBotPanel extends PanelMenu.Button {
    _init() {
        super._init(0.0, 'DuckBot AI Assistant', false);
        
        // Create DuckBot icon
        this._icon = new St.Icon({
            icon_name: 'face-smile-symbolic',
            style_class: 'system-status-icon duckbot-icon',
        });
        
        this.add_child(this._icon);
        
        // AI Status indicator
        this._statusLabel = new St.Label({
            text: 'AI Ready',
            style_class: 'duckbot-status',
            y_align: Clutter.ActorAlign.CENTER,
        });
        this.add_child(this._statusLabel);
        
        this._buildMenu();
        this._initializeAI();
    }
    
    _buildMenu() {
        // Voice Control Section
        let voiceSection = new PopupMenu.PopupMenuSection();
        this.menu.addMenuItem(voiceSection);
        
        this._voiceToggle = new PopupMenu.PopupSwitchMenuItem('Voice Control', false);
        this._voiceToggle.connect('toggled', this._onVoiceToggled.bind(this));
        voiceSection.addMenuItem(this._voiceToggle);
        
        // AI Commands Section
        this.menu.addMenuItem(new PopupMenu.PopupSeparatorMenuItem());
        
        let aiSection = new PopupMenu.PopupMenuSection();
        this.menu.addMenuItem(aiSection);
        
        let organizeWindows = new PopupMenu.PopupMenuItem('Organize Windows');
        organizeWindows.connect('activate', () => this._executeAICommand('organize-windows'));
        aiSection.addMenuItem(organizeWindows);
        
        let smartSearch = new PopupMenu.PopupMenuItem('Smart Search');
        smartSearch.connect('activate', () => this._executeAICommand('smart-search'));
        aiSection.addMenuItem(smartSearch);
        
        let contextAnalysis = new PopupMenu.PopupMenuItem('Analyze Current Context');
        contextAnalysis.connect('activate', () => this._executeAICommand('analyze-context'));
        aiSection.addMenuItem(contextAnalysis);
        
        let systemStatus = new PopupMenu.PopupMenuItem('📊 System Status');
        systemStatus.connect('activate', () => this._showSystemStatus());
        aiSection.addMenuItem(systemStatus);
        
        let agentCoordinator = new PopupMenu.PopupMenuItem('🤖 Agent Coordinator');
        agentCoordinator.connect('activate', () => this._openAgentCoordinator());
        aiSection.addMenuItem(agentCoordinator);
        
        // Memory & Learning Section
        this.menu.addMenuItem(new PopupMenu.PopupSeparatorMenuItem());

        let memorySection = new PopupMenu.PopupMenuSection();
        this.menu.addMenuItem(memorySection);
        
        let memoryBrowser = new PopupMenu.PopupMenuItem('Browse Memory');
        memoryBrowser.connect('activate', () => this._openMemoryBrowser());
        memorySection.addMenuItem(memoryBrowser);
        
        let learnPattern = new PopupMenu.PopupMenuItem('Learn Current Workflow');
        learnPattern.connect('activate', () => this._learnWorkflow());
        memorySection.addMenuItem(learnPattern);
        
        // Settings
        this.menu.addMenuItem(new PopupMenu.PopupSeparatorMenuItem());

        let settings = new PopupMenu.PopupMenuItem('DuckBot Settings');
        settings.connect('activate', () => this._openSettings());
        this.menu.addMenuItem(settings);

        // Integration Shortcuts
        this.menu.addMenuItem(new PopupMenu.PopupSeparatorMenuItem());

        let openDashboard = new PopupMenu.PopupMenuItem('Open AI Dashboard');
        openDashboard.connect('activate', () => this._openURL(this._getWebUIURL() || 'http://localhost:8787'));
        this.menu.addMenuItem(openDashboard);

        let openMonitor = new PopupMenu.PopupMenuItem('Open System Monitor');
        openMonitor.connect('activate', () => this._openURL('http://localhost:8789'));
        this.menu.addMenuItem(openMonitor);

        let openViewer = new PopupMenu.PopupMenuItem('Open Desktop Viewer (noVNC)');
        openViewer.connect('activate', () => this._openURL('http://localhost:6080/vnc.html?autoconnect=1&password=duckbot'));
        this.menu.addMenuItem(openViewer);

        // Audio Helpers
        this.menu.addMenuItem(new PopupMenu.PopupSeparatorMenuItem());
        let audioSetup = new PopupMenu.PopupMenuItem('Configure Audio');
        audioSetup.connect('activate', () => this._runCmd("~/.local/bin/duckbot-audio setup"));
        this.menu.addMenuItem(audioSetup);
        let audioTest = new PopupMenu.PopupMenuItem('Test Audio');
        audioTest.connect('activate', () => this._runCmd("~/.local/bin/duckbot-audio test"));
        this.menu.addMenuItem(audioTest);

        // Windows Integration
        this.menu.addMenuItem(new PopupMenu.PopupSeparatorMenuItem());
        let winNotepad = new PopupMenu.PopupMenuItem('Open Windows Notepad');
        winNotepad.connect('activate', () => this._runCmd("~/.local/bin/duckbot-windows \"Start-Process notepad.exe\""));
        this.menu.addMenuItem(winNotepad);
        let winExplorer = new PopupMenu.PopupMenuItem('Open Windows Explorer');
        winExplorer.connect('activate', () => this._runCmd("~/.local/bin/duckbot-windows \"Start-Process explorer.exe\""));
        this.menu.addMenuItem(winExplorer);

        // Linux Sudo Management
        this.menu.addMenuItem(new PopupMenu.PopupSeparatorMenuItem());
        let setSudo = new PopupMenu.PopupMenuItem('Set Linux Sudo Password');
        setSudo.connect('activate', () => this._runCmd("bash -lc \"(zenity --password --title='DuckBot Sudo' | ~/.local/bin/duckbot-sudo-store -)\""));
        this.menu.addMenuItem(setSudo);
        let testSudo = new PopupMenu.PopupMenuItem('Run Sudo Test (apt update)');
        testSudo.connect('activate', () => this._runCmd("~/.local/bin/duckbot-sudo-run 'apt update -y'"));
        this.menu.addMenuItem(testSudo);

        // GPU Check
        this.menu.addMenuItem(new PopupMenu.PopupSeparatorMenuItem());
        let gpuCheck = new PopupMenu.PopupMenuItem('Verify GPU (WSL)');
        gpuCheck.connect('activate', () => this._gpuCheck());
        this.menu.addMenuItem(gpuCheck);
    }
    
    async _initializeAI() {
        try {
            // Initialize AI services
            this._updateStatus('Initializing AI...', 'orange');
            
            // Connect to DuckBot AI service
            await this._connectToAIService();
            
            // Initialize voice control
            await this._initializeVoice();
            
            // Initialize memory manager
            await this._initializeMemory();
            
            // Set up desktop monitoring
            this._setupDesktopMonitoring();
            
            this._updateStatus('AI Ready', 'green');
            
        } catch (error) {
            log(`DuckBot AI initialization failed: ${error}`);
            this._updateStatus('AI Error', 'red');
        }
    }
    
    async _connectToAIService() {
        // Connect to DuckBot core AI service via D-Bus or local socket
        // This would connect to the main DuckBot Python services
        
        // Placeholder for actual AI service connection
        return new Promise((resolve) => {
            GLib.timeout_add(GLib.PRIORITY_DEFAULT, 1000, () => {
                log('DuckBot AI service connected');
                resolve();
                return GLib.SOURCE_REMOVE;
            });
        });
    }
    
    async _initializeVoice() {
        // Initialize voice control system
        // Would integrate with speech recognition
        log('Voice control initialized');
    }
    
    async _initializeMemory() {
        // Connect to Memento memory system
        log('Memory manager initialized');
    }
    
    _setupDesktopMonitoring() {
        // Monitor desktop events for AI analysis
        // Window focus changes, app launches, file operations, etc.
        
        // Monitor window changes
        global.display.connect('window-created', this._onWindowCreated.bind(this));
        global.display.connect('window-focus-changed', this._onWindowFocusChanged.bind(this));
        
        // Monitor workspace changes  
        global.workspace_manager.connect('active-workspace-changed', 
                                       this._onWorkspaceChanged.bind(this));
    }
    
    _onWindowCreated(display, window) {
        // AI analyzes new window for context
        let appName = window.get_wm_class();
        log(`AI analyzing new window: ${appName}`);
        
        // Send to AI for context learning
        this._sendToAI('window-created', { app: appName, time: Date.now() });
    }
    
    _onWindowFocusChanged(display) {
        let focusedWindow = display.get_focus_window();
        if (focusedWindow) {
            let appName = focusedWindow.get_wm_class();
            log(`AI tracking focus change: ${appName}`);
            
            // Update AI context
            this._sendToAI('focus-changed', { app: appName, time: Date.now() });
        }
    }
    
    _onWorkspaceChanged(manager, from, to) {
        log(`AI tracking workspace change: ${from} -> ${to}`);
        this._sendToAI('workspace-changed', { from: from, to: to, time: Date.now() });
    }
    
    _onVoiceToggled(item, state) {
        if (state) {
            this._enableVoiceControl();
            this._updateStatus('Listening...', 'blue');
        } else {
            this._disableVoiceControl();
            this._updateStatus('AI Ready', 'green');
        }
    }
    
    _enableVoiceControl() {
        log('Voice control enabled');
        // Start listening for voice commands
        // Would integrate with speech recognition service
    }
    
    _disableVoiceControl() {
        log('Voice control disabled');
        // Stop listening
    }
    
    async _executeAICommand(command) {
        this._updateStatus('Processing...', 'blue');
        
        try {
            switch (command) {
                case 'organize-windows':
                    await this._organizeWindows();
                    break;
                case 'smart-search':
                    this._openSmartSearch();
                    break;
                case 'analyze-context':
                    await this._analyzeCurrentContext();
                    break;
            }
            
            this._updateStatus('AI Ready', 'green');
        } catch (error) {
            log(`AI command failed: ${error}`);
            this._updateStatus('AI Error', 'red');
        }
    }
    
    async _organizeWindows() {
        // AI-powered window organization
        let windows = global.get_window_actors();
        
        // Analyze current workspace and arrange windows intelligently
        log(`Organizing ${windows.length} windows with AI`);
        
        // This would call the AI service to determine optimal layout
        await this._sendToAI('organize-windows', { 
            workspace: global.workspace_manager.get_active_workspace_index(),
            windows: windows.length 
        });
        
        // Apply AI-suggested window arrangement
        this._applyIntelligentLayout(windows);
    }
    
    _applyIntelligentLayout(windows) {
        // Apply AI-suggested window layout
        // This would implement smart tiling, grouping related windows, etc.
        
        let workArea = Main.layoutManager.getWorkAreaForMonitor(0);
        let numWindows = windows.length;
        
        if (numWindows === 2) {
            // Side-by-side for 2 windows
            windows[0].get_meta_window().move_resize_frame(false,
                workArea.x, workArea.y, workArea.width / 2, workArea.height);
            windows[1].get_meta_window().move_resize_frame(false,
                workArea.x + workArea.width / 2, workArea.y, workArea.width / 2, workArea.height);
        } else if (numWindows === 3) {
            // Smart 3-window layout
            // Main window on left, two smaller on right
            windows[0].get_meta_window().move_resize_frame(false,
                workArea.x, workArea.y, workArea.width * 0.6, workArea.height);
            windows[1].get_meta_window().move_resize_frame(false,
                workArea.x + workArea.width * 0.6, workArea.y, workArea.width * 0.4, workArea.height / 2);
            windows[2].get_meta_window().move_resize_frame(false,
                workArea.x + workArea.width * 0.6, workArea.y + workArea.height / 2, workArea.width * 0.4, workArea.height / 2);
        }
        
        log('Applied intelligent window layout');
    }
    
    _openSmartSearch() {
        // Open AI-enhanced search interface
        log('Opening smart search');
        
        // This would launch a custom search interface with AI capabilities
        GLib.spawn_command_line_async('duckbot-search --ai-enhanced');
    }
    
    async _analyzeCurrentContext() {
        // AI analyzes current desktop context
        let context = {
            focusedApp: global.display.get_focus_window()?.get_wm_class(),
            workspace: global.workspace_manager.get_active_workspace_index(),
            time: Date.now(),
            windowCount: global.get_window_actors().length
        };
        
        log('Analyzing current context with AI');
        await this._sendToAI('analyze-context', context);
        
        // Show context analysis results
        Main.notify('DuckBot AI', 'Context analysis complete. Check memory for insights.');
    }
    
    _openMemoryBrowser() {
        // Open Memento memory browser
        log('Opening memory browser');
        GLib.spawn_command_line_async('duckbot-memory-browser');
    }
    
    _learnWorkflow() {
        // Learn current workflow pattern
        log('Learning current workflow');
        Main.notify('DuckBot AI', 'Learning your current workflow. Continue working normally.');
        
        // Start learning mode
        this._sendToAI('start-learning', { timestamp: Date.now() });
    }
    
    _openSettings() {
        // Open DuckBot settings through GNOME control center
        GLib.spawn_command_line_async('gnome-control-center');
    }

    _getWebUIURL() {
        // Prefer environment variable exported in ~/.duckbot_env and inherited by session
        try {
            let env = GLib.getenv('DUCKBOT_WEBUI_URL');
            if (env && env.length > 0) return env;
        } catch (e) {}
        return null;
    }

    _openURL(url) {
        try {
            let cmd = `bash -lc "xdg-open '${url}'"`;
            GLib.spawn_command_line_async(cmd);
        } catch (e) {
            Main.notify('DuckBot', `Failed to open URL: ${url}`);
        }
    }

    _runCmd(cmd) {
        try {
            let full = `bash -lc "${cmd}"`;
            GLib.spawn_command_line_async(full);
        } catch (e) {
            Main.notify('DuckBot', 'Command failed to start');
        }
    }

    _gpuCheck() {
        try {
            let [ok, outb] = GLib.spawn_command_line_sync("bash -lc 'if [ -e /dev/dxg ]; then echo WSL_GPU_DEVICE=present; else echo WSL_GPU_DEVICE=absent; fi; nvidia-smi 2>/dev/null || echo NVIDIA_SMI=not_found'");
            let text = outb ? ByteArray.toString(outb) : '';
            Main.notify('DuckBot GPU', text.trim());
        } catch (e) {
            Main.notify('DuckBot GPU', 'GPU check failed');
        }
    }
    
    _showSystemStatus() {
        // Show comprehensive system status in desktop notification
        log('Showing DuckBot system status');
        
        // Get status from all DuckBot components
        this._getSystemStatus().then(status => {
            let statusText = `🧠 AI: ${status.ai_status}\n📊 Agents: ${status.active_agents}\n💾 Memory: ${status.memory_usage}\n🔧 Services: ${status.integrations}`;
            Main.notify('DuckBot System Status', statusText);
        }).catch(error => {
            Main.notify('DuckBot System Status', 'Unable to retrieve status - check services');
        });
    }
    
    _openAgentCoordinator() {
        // Open agent coordination interface through terminal
        log('Opening DuckBot Agent Coordinator');
        
        // Launch the agent coordinator terminal interface
        GLib.spawn_command_line_async('gnome-terminal -- duckbot-terminal --mode=agent-coordinator');
    }
    
    async _getSystemStatus() {
        // Query DuckBot Enhanced WebUI via duckbot-cli
        try {
            let [ok, outb, errb, exit] = GLib.spawn_command_line_sync("bash -lc '~/.local/bin/duckbot-cli status'");
            let text = outb ? ByteArray.toString(outb) : '';
            let status = {};
            try { status = JSON.parse(text); } catch (e) { status = {}; }

            // Optionally fetch agents
            let agentsCount = 0;
            try {
                let [ok2, outb2] = GLib.spawn_command_line_sync("bash -lc '~/.local/bin/duckbot-cli agents'");
                let txt2 = outb2 ? ByteArray.toString(outb2) : '';
                let data2 = JSON.parse(txt2);
                if (data2 && data2.agents && data2.agents.length !== undefined) agentsCount = data2.agents.length;
            } catch (e) {
                // ignore
            }

            return {
                ai_status: 'Active',
                active_agents: agentsCount.toString(),
                memory_usage: (status.memory_usage !== undefined ? status.memory_usage + '%' : 'Unknown'),
                integrations: Array.isArray(status.active_services) ? status.active_services.join(', ') : 'Unknown'
            };
        } catch (error) {
            return {
                ai_status: 'Check services',
                active_agents: 'Unknown',
                memory_usage: 'Unknown',
                integrations: 'Check status'
            };
        }
    }
    
    async _sendToAI(action, data) {
        // Send data to DuckBot Enhanced WebUI via CLI bridge
        try {
            const payloadRaw = JSON.stringify(data || {});
            // Escape single quotes for safe bash single-quoted string
            const payloadEsc = payloadRaw.replace(/'/g, "'\"'\"'");
            const cmd = `bash -lc "~/.local/bin/duckbot-cli send '${action}' '${payloadEsc}'"`;
            GLib.spawn_command_line_async(cmd);
            log(`DuckBot CLI sent: ${action}`);
        } catch (e) {
            log(`DuckBot CLI send failed: ${e}`);
        }
        return { success: true };
    }
    
    _updateStatus(text, color) {
        this._statusLabel.set_text(text);
        
        // Update icon color based on status
        switch (color) {
            case 'green':
                this._icon.set_icon_name('face-smile-symbolic');
                break;
            case 'blue':
                this._icon.set_icon_name('face-cool-symbolic');
                break;
            case 'orange':
                this._icon.set_icon_name('face-uncertain-symbolic');
                break;
            case 'red':
                this._icon.set_icon_name('face-sad-symbolic');
                break;
        }
    }
    
    destroy() {
        // Cleanup
        super.destroy();
    }
});

// Extension lifecycle
function init() {
    log('DuckBot AI Desktop Extension initializing');
    return new Extension();
}

class Extension {
    enable() {
        log('DuckBot AI Desktop Extension enabled');
        
        // Create AI panel
        duckbotPanel = new DuckBotPanel();
        Main.panel.addToStatusArea('duckbot-ai', duckbotPanel, 0, 'right');
        
        // Initialize AI services bridge
        this._initializeAIBridge();
        
        // Set up global key bindings
        this._setupKeybindings();
    }
    
    disable() {
        log('DuckBot AI Desktop Extension disabled');
        
        if (duckbotPanel) {
            duckbotPanel.destroy();
            duckbotPanel = null;
        }
        
        // Cleanup AI services
        this._cleanupAIBridge();
        
        // Remove keybindings
        this._removeKeybindings();
    }
    
    _initializeAIBridge() {
        // Initialize bridge to DuckBot AI services
        log('Initializing AI bridge');
    }
    
    _cleanupAIBridge() {
        // Cleanup AI service connections
        log('Cleaning up AI bridge');
    }
    
    _setupKeybindings() {
        // Set up global keyboard shortcuts
        // Super+Space for AI assistant, Super+V for voice, etc.
        log('Setting up AI keybindings');
    }
    
    _removeKeybindings() {
        // Remove keyboard shortcuts
        log('Removing AI keybindings');
    }
}
