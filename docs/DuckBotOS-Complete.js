
        import * as THREE from 'three';
        import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
        import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

        // --- STATE MANAGEMENT ---
        let state = {
            isLoaded: false,
            agentStatus: 'idle',
            currentModel: 'gemini/gemini-1.5-flash-latest',
            conversation: [],
            lmStudioUrl: 'http://localhost:1234/v1',
            openRouterKey: '',
            geminiApiKey: '',
            apiProvider: 'gemini',
            currentCost: 0.00,
            queueSize: 0,
            voiceEnabled: false,
            files: [
                { name: 'README.md', type: 'markdown', content: '# Welcome to DuckBot OS\nYour complete AI management console.' },
                { name: 'config.json', type: 'json', content: '{"version": "3.1.0", "features": ["ai", "voice", "image"]}' },
                { name: 'main.py', type: 'python', content: '#!/usr/bin/env python3\nprint("DuckBot OS - The future of AI management")' },
            ],
            services: {
                comfyui: { name: 'ComfyUI', status: 'stopped', port: 8188, description: 'AI Image Generation' },
                lm_studio: { name: 'LM Studio', status: 'stopped', port: 1234, description: 'Local AI Models' },
                n8n: { name: 'n8n Workflows', status: 'stopped', port: 5678, description: 'Automation Platform' },
                jupyter: { name: 'Jupyter Lab', status: 'stopped', port: 8889, description: 'Data Science Notebooks' },
                webui: { name: 'DuckBot WebUI', status: 'running', port: 8787, description: 'Main Dashboard' }
            },
            apps: [
                 { id: 1, name: 'AI Chat', icon: '🤖', open: false, type: 'chat', zIndex: 10, position: {x: 100, y: 100}, size: {w: 700, h: 500} },
                 { id: 2, name: 'Task Runner', icon: '⚡', open: false, type: 'task-runner', zIndex: 10, position: {x: 150, y: 150}, size: {w: 600, h: 450} },
                 { id: 3, name: 'Files', icon: '📁', open: false, type: 'files', zIndex: 10, position: {x: 200, y: 200}, size: {w: 500, h: 450} },
                 { id: 4, name: 'Settings', icon: '⚙️', open: false, type: 'settings', zIndex: 10, position: {x: 250, y: 250}, size: {w: 550, h: 500} },
                 { id: 5, name: 'Code Editor', icon: '⌨️', open: false, type: 'code', zIndex: 10, currentFile: null, position: {x: 300, y: 300}, size: {w: 700, h: 500} },
                 { id: 6, name: 'Image Genie', icon: '✨', open: false, type: 'image-gen', zIndex: 10, position: {x: 350, y: 350}, size: {w: 400, h: 450}, lastImage: null, isGenerating: false },
                 { id: 7, name: 'Voice Studio', icon: '🎤', open: false, type: 'voice-gen', zIndex: 10, position: {x: 400, y: 400}, size: {w: 500, h: 400} },
                 { id: 8, name: 'Cost Dashboard', icon: '💰', open: false, type: 'cost-dashboard', zIndex: 10, position: {x: 450, y: 450}, size: {w: 600, h: 500} },
                 { id: 9, name: 'Services', icon: '🔧', open: false, type: 'services', zIndex: 10, position: {x: 500, y: 100}, size: {w: 650, h: 550} },
                 { id: 10, name: 'Models', icon: '🧠', open: false, type: 'models', zIndex: 10, position: {x: 550, y: 150}, size: {w: 550, h: 450} },
                 { id: 11, name: 'Queue', icon: '📋', open: false, type: 'queue', zIndex: 10, position: {x: 600, y: 200}, size: {w: 500, h: 400} },
                 { id: 12, name: 'RAG Manager', icon: '📚', open: false, type: 'rag', zIndex: 10, position: {x: 650, y: 250}, size: {w: 550, h: 500} },
                 { id: 13, name: 'Action Logs', icon: '📊', open: false, type: 'logs', zIndex: 10, position: {x: 700, y: 300}, size: {w: 650, h: 450} },
                 { id: 14, name: 'Qwen-Agent', icon: '🧠', open: false, type: 'qwen-agent', zIndex: 10, position: {x: 100, y: 400}, size: {w: 650, h: 500} },
                 { id: 15, name: 'Claude Code', icon: '🔷', open: false, type: 'claude-code', zIndex: 10, position: {x: 150, y: 450}, size: {w: 700, h: 550} },
                 { id: 16, name: 'AI Router', icon: '🔀', open: false, type: 'ai-router', zIndex: 10, position: {x: 200, y: 500}, size: {w: 750, h: 600} },
                 { id: 17, name: 'Dynamic Models', icon: '⚡', open: false, type: 'dynamic-models', zIndex: 10, position: {x: 250, y: 550}, size: {w: 600, h: 500} },
                 { id: 18, name: 'Local Parity', icon: '🏠', open: false, type: 'local-parity', zIndex: 10, position: {x: 300, y: 600}, size: {w: 650, h: 450} },
                 { id: 19, name: 'System Health', icon: '💚', open: false, type: 'system-health', zIndex: 10, position: {x: 350, y: 650}, size: {w: 700, h: 500} },
                 { id: 20, name: 'Performance', icon: '📈', open: false, type: 'performance', zIndex: 10, position: {x: 400, y: 700}, size: {w: 800, h: 550} },
                 { id: 21, name: 'Task Manager', icon: '📝', open: false, type: 'task-manager', zIndex: 10, position: {x: 450, y: 100}, size: {w: 800, h: 600} },
                 { id: 22, name: 'Knowledge Base', icon: '📚', open: false, type: 'knowledge-base', zIndex: 10, position: {x: 500, y: 150}, size: {w: 700, h: 550} },
            ],
            duckBot: {
                visible: true,
                isSpeaking: false,
                position: { x: 0, y: 0 },
                scene: null, camera: null, renderer: null, controls: null, mixer: null, clock: new THREE.Clock(),
                idleAction: null, talkAction: null
            },
            abortController: new AbortController(),
            apiToken: new URLSearchParams(window.location.search).get('token') || '',
            apiBase: window.location.origin,
            agentPaused: false
        };

        // --- UTILITY FUNCTIONS ---
        const $ = (selector) => document.querySelector(selector);
        const $$ = (selector) => document.querySelectorAll(selector);
        
        async function apiCall(endpoint, options = {}) {
            const url = `${state.apiBase}${endpoint}`;
            const headers = { 'Content-Type': 'application/json', ...options.headers };
            if (state.apiToken) {
                headers.Authorization = `Bearer ${state.apiToken}`;
            }
            
            const response = await fetch(url, {
                ...options,
                headers,
                signal: state.abortController.signal
            });
            
            if (!response.ok) {
                throw new Error(`API call failed: ${response.statusText}`);
            }
            
            return response.json();
        }
        
        // --- DOM SELECTORS ---
        const loadingScreen = $("#loading-screen");
        const desktopContainer = $("#desktop-container");
        const canvasBg = $("#canvas-bg");
        const iconsGrid = $("#icons-grid");
        const windowsContainer = $("#windows-container");
        const conversationLog = $("#conversation-log");
        const commandForm = $("#command-form");
        const commandInput = $("#command-input");
        const sendBtn = $("#send-btn");
        const stopBtn = $("#stop-btn");
        const pauseBtn = $("#pause-btn");
        const taskTypeSelect = $("#task-type-select");
        const riskLevelSelect = $("#risk-level-select");
        const voiceToggle = $("#voice-toggle");
        const duckbotClippyContainer = $("#duckbot-clippy-container");
        const duckbot3DCanvas = $("#duckbot-3d-canvas");
        const duckbotSpeechBubble = $("#duckbot-speech-bubble");
        const duckbotMessage = $("#duckbot-message");
        const hideDuckbotBtn = $("#hide-duckbot-btn");
        const showDuckbotBtn = $("#show-duckbot-btn");
        const timeDisplay = $("#time-display");
        const currentModelStatus = $("#current-model-status");
        const agentStatusIndicator = $("#agent-status-indicator");
        const costIndicator = $("#cost-indicator");
        const queueIndicator = $("#queue-indicator");

        // --- MAIN INITIALIZATION ---
        async function init() {
            setTimeout(async () => {
                loadingScreen.style.display = 'none';
                desktopContainer.style.display = 'block';
                state.isLoaded = true;
                
                showDuckBotMessage(`Welcome to DuckBot OS! Your complete AI management console is ready. Try asking me anything!`);
                state.conversation.push({ type: 'agent', content: "I'm your AI assistant with full system integration. Ask me anything or explore the apps!" });
                
                await loadSystemStatus();
                renderIcons();
                render();
            }, 2500);

            animateCanvasBackground();
            initDuckBot3D();
            
            setInterval(() => {
                timeDisplay.textContent = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            }, 1000);
            
            setInterval(updateSystemStatus, 5000); // Update status every 5 seconds
            setupEventListeners();
        }
        
        async function loadSystemStatus() {
            try {
                const [costData, queueData, servicesData, settingsData] = await Promise.all([
                    apiCall('/api/cost_summary').catch(() => ({ total: 0 })),
                    apiCall('/api/queue/status').catch(() => ({ queue_size: 0 })),
                    apiCall('/api/services').catch(() => ({ services: [] })),
                    apiCall('/api/settings').catch(() => ({}))
                ]);
                
                state.currentCost = costData.total || 0;
                state.queueSize = queueData.queue_size || 0;
                
                // Load settings into state
                if (settingsData) {
                    state.apiProvider = settingsData.apiProvider || 'gemini';
                    state.geminiApiKey = settingsData.geminiApiKey || '';
                    state.openRouterKey = settingsData.openRouterKey || '';
                    state.lmStudioUrl = settingsData.lmStudioUrl || 'http://localhost:1234';
                }
                
                if (servicesData.services) {
                    servicesData.services.forEach(service => {
                        const key = service.service_key || service.name.toLowerCase().replace(/\s+/g, '_');
                        if (state.services[key]) {
                            state.services[key].status = service.status;
                        }
                    });
                }
            } catch (error) {
                console.warn('Failed to load system status:', error);
            }
        }
        
        async function updateSystemStatus() {
            await loadSystemStatus();
            render();
        }

        // --- RENDER FUNCTIONS ---
        function renderIcons() {
            iconsGrid.innerHTML = ''; // Clear existing icons
            state.apps.forEach(app => {
                const iconEl = document.createElement('div');
                iconEl.className = 'flex flex-col items-center cursor-pointer group transform hover:scale-105 transition-all duration-200';
                iconEl.dataset.appid = app.id;
                iconEl.innerHTML = `
                    <div class="w-20 h-20 bg-slate-800/60 backdrop-blur-sm rounded-2xl flex items-center justify-center text-4xl mb-3 group-hover:bg-yellow-500/20 transition-all duration-200 shadow-lg group-hover:shadow-yellow-500/20 border border-slate-600/50">
                        ${app.icon}
                    </div>
                    <span class="text-sm text-slate-300 group-hover:text-white transition-colors font-medium">${app.name}</span>
                `;
                iconEl.addEventListener('click', () => {
                    app.open = true;
                    app.zIndex = Math.max(...state.apps.map(a => a.zIndex), 10) + 1;
                    showDuckBotMessage(`Opening ${app.name}`);
                    render();
                });
                iconsGrid.appendChild(iconEl);
            });
        }

        function render() {
            // Render windows
            state.apps.forEach(app => {
                const existingWindow = document.querySelector(`.window[data-appid="${app.id}"]`);
                if (app.open) {
                    if (!existingWindow) {
                        const windowEl = createWindowElement(app);
                        windowsContainer.appendChild(windowEl);
                    } else {
                        // Update existing window properties if needed
                        existingWindow.style.left = `${app.position.x}px`;
                        existingWindow.style.top = `${app.position.y}px`;
                        existingWindow.style.width = `${app.size.w}px`;
                        existingWindow.style.height = `${app.size.h}px`;
                        existingWindow.style.zIndex = app.zIndex;
                        // Update content if necessary (can be optimized further)
                        const contentEl = existingWindow.querySelector('.window-content');
                        contentEl.innerHTML = ''; // Clear previous content
                        contentEl.appendChild(renderWindowContent(app));
                    }
                } else {
                    if (existingWindow) {
                        existingWindow.remove();
                    }
                }
            });

            // Conversation
            conversationLog.innerHTML = state.conversation.map(msg => {
                 const colors = {
                    user: 'bg-blue-500/20 border-l-4 border-blue-500',
                    agent: 'bg-slate-700/50 border-l-4 border-cyan-500',
                    system: 'bg-slate-600/30 border-l-4 border-slate-500 text-xs italic',
                    thought: 'bg-purple-500/20 border-l-4 border-purple-500 text-xs italic'
                };
                return `<div class="p-2 rounded-lg text-sm ${colors[msg.type]}"><div class="whitespace-pre-wrap">${msg.content.replace(/</g, "&lt;").replace(/>/g, "&gt;")}</div></div>`;
            }).join('');
            conversationLog.scrollTop = conversationLog.scrollHeight;
            
            // Top Bar Updates
            currentModelStatus.textContent = state.currentModel.split('/').pop();
            agentStatusIndicator.textContent = state.agentStatus === 'thinking' ? 'Thinking...' : 'Ready';
            agentStatusIndicator.className = state.agentStatus === 'thinking' ? 'text-yellow-400 animate-pulse' : 'text-green-400';
            costIndicator.textContent = state.currentCost.toFixed(3);
            queueIndicator.textContent = state.queueSize;
            
            // Buttons
            sendBtn.style.display = state.agentStatus === 'thinking' ? 'none' : 'flex';
            stopBtn.style.display = state.agentStatus === 'thinking' ? 'flex' : 'none';
            commandInput.disabled = state.agentStatus === 'thinking';
        }

        function createWindowElement(app) {
            const windowEl = document.createElement('div');
            windowEl.className = 'window absolute bg-slate-800/80 backdrop-blur-xl border border-slate-600 rounded-xl flex flex-col shadow-2xl';
            windowEl.style.left = `${app.position.x}px`;
            windowEl.style.top = `${app.position.y}px`;
            windowEl.style.width = `${app.size.w}px`;
            windowEl.style.height = `${app.size.h}px`;
            windowEl.style.zIndex = app.zIndex;
            windowEl.dataset.appid = app.id;

            const headerEl = document.createElement('div');
            headerEl.className = 'window-header flex items-center justify-between p-2 border-b border-slate-700';
            headerEl.innerHTML = `
                <div class="flex items-center space-x-2 text-sm font-bold">
                    <span>${app.icon}</span>
                    <span>${app.name}</span>
                </div>
            `;

            const closeBtn = document.createElement('button');
            closeBtn.className = 'close-window-btn text-slate-400 hover:text-white hover:bg-red-600 w-6 h-6 rounded-md flex items-center justify-center transition-colors';
            closeBtn.innerHTML = '✕';
            closeBtn.addEventListener('click', () => {
                app.open = false;
                showDuckBotMessage(`${app.name} closed`);
                render();
            });

            headerEl.appendChild(closeBtn);

            const contentEl = document.createElement('div');
            contentEl.className = 'window-content flex-1 p-4 overflow-auto scrollbar-hide';
            contentEl.appendChild(renderWindowContent(app));

            windowEl.appendChild(headerEl);
            windowEl.appendChild(contentEl);

            return windowEl;
        }
        
        function renderWindowContent(app) {
            const container = document.createElement('div');
            switch (app.type) {
                case 'chat':
                    container.innerHTML = `<div class="h-full flex flex-col">
                                <div class="flex-1 bg-slate-900/50 rounded p-3 mb-4 overflow-y-auto">
                                    <div class="space-y-3">
                                        ${state.conversation.map(msg => {
                                            const colors = {
                                                user: 'bg-blue-500/20 border-l-4 border-blue-500',
                                                agent: 'bg-slate-700/50 border-l-4 border-cyan-500',
                                                thought: 'bg-purple-500/20 border-l-4 border-purple-500 text-xs italic'
                                            };
                                            return `<div class="p-2 rounded-lg text-sm ${colors[msg.type] || colors.agent}">
                                                       ${msg.content.replace(/</g, "&lt;").replace(/>/g, "&gt;")}
                                                   </div>`;
                                        }).join('')}
                                    </div>
                                </div>
                                <div class="flex space-x-2">
                                    <input type="text" id="chat-input-${app.id}" placeholder="Chat here..." class="flex-1 bg-slate-700/50 border border-slate-600 rounded px-3 py-2 text-sm">
                                    <button class="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded text-sm">Send</button>
                                </div>
                            </div>`;
                    const button = container.querySelector('button');
                    button.addEventListener('click', () => sendChatMessage(app.id));
                    return container;
                
                case 'task-runner':
                    container.innerHTML = `<div class="space-y-4">
                                <h4 class="font-bold text-lg text-yellow-400">AI Task Runner</h4>
                                <div class="grid grid-cols-2 gap-4">
                                    <div>
                                        <label class="block text-sm font-bold mb-1">Task Type</label>
                                        <select id="task-type-${app.id}" class="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2">
                                            <option value="code">Code Generation</option>
                                            <option value="reasoning">Reasoning</option>
                                            <option value="status">Status Check</option>
                                            <option value="summary">Summary</option>
                                        </select>
                                    </div>
                                    <div>
                                        <label class="block text-sm font-bold mb-1">Risk Level</label>
                                        <select id="risk-${app.id}" class="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2">
                                            <option value="low">Low</option>
                                            <option value="medium">Medium</option>
                                            <option value="high">High</option>
                                        </select>
                                    </div>
                                </div>
                                <div>
                                    <label class="block text-sm font-bold mb-1">Task Prompt</label>
                                    <textarea id="task-prompt-${app.id}" class="w-full bg-slate-700/50 border border-slate-600 rounded p-3 h-32" placeholder="Describe your AI task..."></textarea>
                                </div>
                                <button class="w-full bg-green-600 hover:bg-green-700 p-3 rounded font-bold">Execute Task</button>
                                <div id="task-result-${app.id}" class="bg-slate-900/50 rounded p-3 min-h-24 text-sm"></div>
                            </div>`;
                    const taskButton = container.querySelector('button');
                    taskButton.addEventListener('click', () => runAITask(app.id));
                    return container;

                case 'services':
                    const servicesContainer = document.createElement('div');
                    servicesContainer.className = 'space-y-4';
                    servicesContainer.innerHTML = `<h4 class="font-bold text-lg text-yellow-400 mb-4">Service Management</h4>`;
                    const servicesList = document.createElement('div');
                    servicesList.className = 'space-y-3';
                    Object.entries(state.services).forEach(([key, service]) => {
                        const serviceEl = document.createElement('div');
                        serviceEl.className = 'bg-slate-900/50 rounded-lg p-3 flex items-center justify-between';
                        serviceEl.innerHTML = `
                            <div class="flex items-center space-x-3">
                                <span class="status-indicator status-${service.status}"></span>
                                <div>
                                    <div class="font-bold">${service.name}</div>
                                    <div class="text-xs text-slate-400">${service.description} - Port ${service.port}</div>
                                </div>
                            </div>
                            <div class="flex space-x-2">
                                <button data-action="start" class="bg-green-600 hover:bg-green-700 px-3 py-1 rounded text-xs" ${service.status === 'running' ? 'disabled' : ''}>Start</button>
                                <button data-action="stop" class="bg-red-600 hover:bg-red-700 px-3 py-1 rounded text-xs" ${service.status === 'stopped' ? 'disabled' : ''}>Stop</button>
                                <button data-action="restart" class="bg-yellow-600 hover:bg-yellow-700 px-3 py-1 rounded text-xs">Restart</button>
                            </div>
                        `;
                        serviceEl.querySelector('[data-action="start"]').addEventListener('click', () => controlService(key, 'start'));
                        serviceEl.querySelector('[data-action="stop"]').addEventListener('click', () => controlService(key, 'stop'));
                        serviceEl.querySelector('[data-action="restart"]').addEventListener('click', () => controlService(key, 'restart'));
                        servicesList.appendChild(serviceEl);
                    });
                    servicesContainer.appendChild(servicesList);
                    const ecosystemControls = document.createElement('div');
                    ecosystemControls.className = 'border-t border-slate-700 pt-4';
                    ecosystemControls.innerHTML = `
                        <button data-action="start" class="w-full bg-green-600 hover:bg-green-700 p-2 rounded font-bold mb-2">Start All Services</button>
                        <button data-action="stop" class="w-full bg-red-600 hover:bg-red-700 p-2 rounded font-bold">Stop All Services</button>
                    `;
                    ecosystemControls.querySelector('[data-action="start"]').addEventListener('click', () => controlEcosystem('start'));
                    ecosystemControls.querySelector('[data-action="stop"]').addEventListener('click', () => controlEcosystem('stop'));
                    servicesContainer.appendChild(ecosystemControls);
                    return servicesContainer;

                case 'task-manager':
                    return renderTaskManager(app);

                case 'knowledge-base':
                    return renderKnowledgeBase(app);

                default: 
                    container.innerHTML = `<p class="text-slate-400">This feature is still being developed. Check back soon!</p>`;
                    return container;
            }
        }

        function renderTaskManager(app) {
            const container = document.createElement('div');
            container.className = 'h-full flex flex-col';
            container.innerHTML = `
                <h4 class="font-bold text-lg text-yellow-400 mb-4">Task Manager</h4>
                <div class="flex-1 grid grid-cols-3 gap-4">
                    <div class="col-span-1 bg-slate-900/50 rounded p-3">
                        <h5 class="font-bold mb-2">Projects</h5>
                        <ul id="project-list-${app.id}" class="space-y-2"></ul>
                        <div class="mt-4">
                            <input type="text" id="new-project-name-${app.id}" placeholder="New project name..." class="w-full bg-slate-700/50 border border-slate-600 rounded px-3 py-2 text-sm">
                            <button id="add-project-btn-${app.id}" class="w-full mt-2 bg-blue-600 hover:bg-blue-700 p-2 rounded text-sm">Add Project</button>
                        </div>
                    </div>
                    <div class="col-span-2 bg-slate-900/50 rounded p-3">
                        <h5 class="font-bold mb-2">Tasks</h5>
                        <ul id="task-list-${app.id}" class="space-y-2"></ul>
                        <div class="mt-4">
                            <input type="text" id="new-task-title-${app.id}" placeholder="New task title..." class="w-full bg-slate-700/50 border border-slate-600 rounded px-3 py-2 text-sm">
                            <button id="add-task-btn-${app.id}" class="w-full mt-2 bg-green-600 hover:bg-green-700 p-2 rounded text-sm">Add Task</button>
                        </div>
                    </div>
                </div>
            `;

            const addProjectBtn = container.querySelector(`#add-project-btn-${app.id}`);
            addProjectBtn.addEventListener('click', async () => {
                const projectNameInput = container.querySelector(`#new-project-name-${app.id}`);
                const projectName = projectNameInput.value.trim();
                if (projectName) {
                    await apiCall('/api/projects', { method: 'POST', body: JSON.stringify({ name: projectName }) });
                    projectNameInput.value = '';
                    renderTaskManager(app);
                }
            });

            const addTaskBtn = container.querySelector(`#add-task-btn-${app.id}`);
            addTaskBtn.addEventListener('click', async () => {
                const taskTitleInput = container.querySelector(`#new-task-title-${app.id}`);
                const taskTitle = taskTitleInput.value.trim();
                const selectedProject = container.querySelector('.project-item.selected');
                if (taskTitle && selectedProject) {
                    const projectId = selectedProject.dataset.projectId;
                    await apiCall('/api/tasks', { method: 'POST', body: JSON.stringify({ project_id: parseInt(projectId), title: taskTitle }) });
                    taskTitleInput.value = '';
                    renderTaskManager(app);
                }
            });

            const projectList = container.querySelector(`#project-list-${app.id}`);
            apiCall('/api/projects').then(projects => {
                projectList.innerHTML = '';
                projects.forEach(project => {
                    const projectEl = document.createElement('li');
                    projectEl.className = 'project-item p-2 rounded cursor-pointer hover:bg-slate-700';
                    projectEl.textContent = project.name;
                    projectEl.dataset.projectId = project.id;
                    projectEl.addEventListener('click', () => {
                        const selected = projectList.querySelector('.selected');
                        if (selected) selected.classList.remove('selected');
                        projectEl.classList.add('selected');
                        renderTasks(app, project.id);
                    });
                    projectList.appendChild(projectEl);
                });
            });

            return container;
        }

        async function renderTasks(app, projectId) {
            const taskList = document.querySelector(`#task-list-${app.id}`);
            const tasks = await apiCall(`/api/projects/${projectId}/tasks`);
            taskList.innerHTML = '';
            tasks.forEach(task => {
                const taskEl = document.createElement('li');
                taskEl.className = 'task-item flex items-center justify-between p-2 rounded';
                taskEl.innerHTML = `
                    <span>${task.title}</span>
                    <select class="task-status-select bg-slate-700 border border-slate-600 rounded px-2 py-1 text-xs">
                        <option value="todo" ${task.status === 'todo' ? 'selected' : ''}>To Do</option>
                        <option value="inprogress" ${task.status === 'inprogress' ? 'selected' : ''}>In Progress</option>
                        <option value="done" ${task.status === 'done' ? 'selected' : ''}>Done</option>
                    </select>
                `;
                const statusSelect = taskEl.querySelector('.task-status-select');
                statusSelect.addEventListener('change', async (e) => {
                    await apiCall(`/api/tasks/${task.id}`, { method: 'PUT', body: JSON.stringify({ status: e.target.value }) });
                });
                taskList.appendChild(taskEl);
            });
        }

        function renderKnowledgeBase(app) {
            const container = document.createElement('div');
            container.className = 'h-full flex flex-col';
            container.innerHTML = `
                <h4 class="font-bold text-lg text-yellow-400 mb-4">Knowledge Base</h4>
                <div class="flex-1 grid grid-cols-2 gap-4">
                    <div class="col-span-1 bg-slate-900/50 rounded p-3">
                        <h5 class="font-bold mb-2">Files</h5>
                        <ul id="file-list-${app.id}" class="space-y-2"></ul>
                        <div class="mt-4">
                            <input type="file" id="file-upload-${app.id}" class="w-full">
                            <button id="upload-btn-${app.id}" class="w-full mt-2 bg-blue-600 hover:bg-blue-700 p-2 rounded text-sm">Upload File</button>
                        </div>
                    </div>
                    <div class="col-span-1 bg-slate-900/50 rounded p-3">
                        <h5 class="font-bold mb-2">Websites</h5>
                        <div class="mt-4">
                            <input type="text" id="website-url-${app.id}" placeholder="https://example.com" class="w-full bg-slate-700/50 border border-slate-600 rounded px-3 py-2 text-sm">
                            <button id="crawl-btn-${app.id}" class="w-full mt-2 bg-green-600 hover:bg-green-700 p-2 rounded text-sm">Crawl Website</button>
                        </div>
                    </div>
                </div>
            `;

            const uploadBtn = container.querySelector(`#upload-btn-${app.id}`);
            uploadBtn.addEventListener('click', async () => {
                const fileInput = container.querySelector(`#file-upload-${app.id}`);
                const file = fileInput.files[0];
                if (file) {
                    const formData = new FormData();
                    formData.append('file', file);
                    await fetch('/api/files/upload', { method: 'POST', body: formData });
                    fileInput.value = '';
                    renderKnowledgeBase(app);
                }
            });

            const crawlBtn = container.querySelector(`#crawl-btn-${app.id}`);
            crawlBtn.addEventListener('click', async () => {
                const urlInput = container.querySelector(`#website-url-${app.id}`);
                const url = urlInput.value.trim();
                if (url) {
                    await apiCall('/api/rag/crawl', { method: 'POST', body: JSON.stringify({ url: url }) });
                    urlInput.value = '';
                }
            });

            const fileList = container.querySelector(`#file-list-${app.id}`);
            apiCall('/api/files').then(files => {
                fileList.innerHTML = '';
                files.forEach(file => {
                    const fileEl = document.createElement('li');
                    fileEl.className = 'p-2 rounded';
                    fileEl.textContent = file.name;
                    fileList.appendChild(fileEl);
                });
            });

            return container;
        }
        
        // --- WINDOW FUNCTIONS ---
        window.sendChatMessage = async function(appId) {
            const input = $("#chat-input-" + appId);
            if (!input.value.trim()) return;
            
            const message = input.value.trim();
            input.value = '';
            
            state.conversation.push({ type: 'user', content: message });
            state.agentStatus = 'thinking';
            render();
            
            try {
                const response = await apiCall('/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                    body: new URLSearchParams({ message, kind: '*', risk: 'low' })
                });
                
                state.conversation.push({
                    type: 'agent', 
                    content: response.response || 'No response received' 
                });
            } catch (error) {
                state.conversation.push({
                    type: 'system', 
                    content: `Error: ${error.message}` 
                });
            }
            
            state.agentStatus = 'idle';
            render();
        };
        
        window.runAITask = async function(appId) {
            const taskType = $(`#task-type-${appId}`).value;
            const risk = $(`#risk-${appId}`).value;
            const prompt = $(`#task-prompt-${appId}`).value;
            const resultDiv = $(`#task-result-${appId}`);
            
            if (!prompt.trim()) return;
            
            resultDiv.innerHTML = '<div class="text-slate-400">Processing task...</div>';
            
            try {
                const response = await apiCall('/api/task', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                    body: new URLSearchParams({
                        task_type: taskType, 
                        prompt, 
                        priority: risk,
                        bucket_type: 'background'
                    })
                });
                
                resultDiv.innerHTML = `<div class="text-green-400">Task completed successfully</div>
                                      <div class="mt-2 text-slate-300">${response.result?.text || 'Task executed'}</div>`;
            } catch (error) {
                resultDiv.innerHTML = `<div class="text-red-400">Task failed: ${error.message}</div>`;
            }
        };
        
        window.controlService = async function(serviceName, action) {
            try {
                await apiCall(`/api/services/${serviceName}/${action}`, { method: 'POST' });
                showDuckBotMessage(`Service ${serviceName} ${action} initiated`);
                await updateSystemStatus();
            } catch (error) {
                showDuckBotMessage(`Failed to ${action} ${serviceName}: ${error.message}`);
            }
        };
        
        window.controlEcosystem = async function(action) {
            try {
                await apiCall(`/ecosystem/${action}`, { method: 'POST' });
                showDuckBotMessage(`Ecosystem ${action} initiated`);
                await updateSystemStatus();
            } catch (error) {
                showDuckBotMessage(`Failed to ${action} ecosystem: ${error.message}`);
            }
        };
        
        window.generateImage = async function(appId) {
            const app = state.apps.find(a => a.id === appId);
            const prompt = $("#image-prompt-input-${app.id}").value;
            
            if (!prompt.trim()) return;
            
            app.isGenerating = true;
            render();
            
            try {
                const response = await apiCall('/api/generate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                    body: new URLSearchParams({
                        prompt, 
                        model: 'auto',
                        type: 'image'
                    })
                });
                
                app.lastImage = response.image_url;
                showDuckBotMessage('Image generation completed!');
            } catch (error) {
                showDuckBotMessage(`Image generation failed: ${error.message}`);
            }
            
            app.isGenerating = false;
            render();
        };
        
        window.generateVoice = async function(appId) {
            const text = $(`#voice-text-${app.id}`).value;
            const voice = $(`#voice-select-${app.id}`).value;
            const preset = $(`#voice-preset-${app.id}`).value;
            const resultDiv = $(`#voice-result-${app.id}`);
            
            if (!text.trim()) return;
            
            resultDiv.innerHTML = '<div class="text-slate-400">Generating voice...</div>';
            
            try {
                const response = await apiCall('/api/voice/generate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                    body: new URLSearchParams({ text, voice, preset })
                });
                
                if (response.success) {
                    resultDiv.innerHTML = `<audio controls class="w-full">
                                          <source src="${response.audio_url}" type="audio/mpeg">
                                          Your browser does not support the audio element.
                                          </audio>`;
                } else {
                    resultDiv.innerHTML = '<div class="text-red-400">Voice generation failed</div>';
                }
            } catch (error) {
                resultDiv.innerHTML = `<div class="text-red-400">Error: ${error.message}</div>`;
            }
        };
        
        window.saveSettings = async function(appId) {
            const provider = $(`#api-provider-select-${appId}`).value;
            const geminiKey = $(`#gemini-key-input-${appId}`).value;
            const openRouterKey = $(`#openrouter-key-input-${appId}`).value;
            const lmStudioUrl = $(`#lmstudio-url-input-${appId}`).value;
            
            try {
                // Save to backend
                const settingsData = {
                    apiProvider: provider,
                    geminiApiKey: geminiKey,
                    openRouterKey: openRouterKey,
                    lmStudioUrl: lmStudioUrl
                };
                
                const response = await apiCall('/api/settings', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(settingsData)
                });
                
                if (response.success) {
                    // Update local state
                    state.apiProvider = provider;
                    state.geminiApiKey = geminiKey;
                    state.openRouterKey = openRouterKey;
                    state.lmStudioUrl = lmStudioUrl;
                    
                    showDuckBotMessage("Settings saved successfully!");
                    render(); // Re-render to update any displays
                } else {
                    showDuckBotMessage(`Failed to save settings: ${response.error || 'Unknown error'}`);
                }
            } catch (error) {
                console.error('Settings save error:', error);
                showDuckBotMessage(`Error saving settings: ${error.message}`);
            }
        };
        
        // --- FILE MANAGEMENT FUNCTIONS ---
        window.viewFile = function(fileName) {
            const file = state.files.find(f => f.name === fileName);
            if (!file) return;
            
            // Open code editor with this file
            const codeApp = state.apps.find(app => app.type === 'code');
            if (codeApp) {
                codeApp.currentFile = file;
                codeApp.open = true;
                codeApp.zIndex = Math.max(...state.apps.map(a => a.zIndex)) + 1;
                showDuckBotMessage(`Opening ${fileName} in code editor`);
                render();
            }
        };
        
        window.selectFile = function(appId) {
            const fileName = $(`#file-select-${appId}`).value;
            const file = state.files.find(f => f.name === fileName);
            const app = state.apps.find(a => a.id === appId);
            
            if (file && app) {
                app.currentFile = file;
                render(); // Re-render to update editor content
            }
        };
        
        window.saveFile = async function(appId) {
            const editor = $(`#code-editor-${appId}`);
            const app = state.apps.find(a => a.id === appId);
            
            if (!editor || !app || !app.currentFile) return;
            
            try {
                const content = editor.value;
                
                // Save to backend
                const response = await apiCall('/api/files/save', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        filename: app.currentFile.name,
                        content: content
                    })
                });
                
                if (response.success) {
                    // Update local file
                    app.currentFile.content = content;
                    const fileIndex = state.files.findIndex(f => f.name === app.currentFile.name);
                    if (fileIndex !== -1) {
                        state.files[fileIndex].content = content;
                    }
                    showDuckBotMessage(`File ${app.currentFile.name} saved successfully!`);
                } else {
                    showDuckBotMessage(`Failed to save ${app.currentFile.name}: ${response.error || 'Unknown error'}`);
                }
            } catch (error) {
                console.error('File save error:', error);
                showDuckBotMessage(`Error saving file: ${error.message}`);
            }
        };
        
        // --- MODEL MANAGEMENT FUNCTIONS ---
        window.refreshModels = async function() {
            try {
                showDuckBotMessage("Refreshing model list...");
                
                const response = await apiCall('/api/models/refresh', {
                    method: 'POST'
                });
                
                if (response.success) {
                    showDuckBotMessage("Model list refreshed successfully!");
                    await updateSystemStatus(); // Refresh the UI
                } else {
                    showDuckBotMessage(`Failed to refresh models: ${response.error || 'Unknown error'}`);
                }
            } catch (error) {
                console.error('Model refresh error:', error);
                showDuckBotMessage(`Error refreshing models: ${error.message}`);
            }
        };
        
        // --- QUEUE MANAGEMENT FUNCTIONS ---
        window.clearQueue = async function() {
            try {
                const response = await apiCall('/api/queue/clear', {
                    method: 'POST'
                });
                
                if (response.success) {
                    state.queueSize = 0;
                    showDuckBotMessage("Queue cleared successfully!");
                    render();
                } else {
                    showDuckBotMessage(`Failed to clear queue: ${response.error || 'Unknown error'}`);
                }
            } catch (error) {
                console.error('Queue clear error:', error);
                showDuckBotMessage(`Error clearing queue: ${error.message}`);
            }
        };
        
        // --- RAG MANAGEMENT FUNCTIONS ---
        window.ragAction = async function(appId, action) {
            try {
                let message, endpoint;
                
                switch(action) {
                    case 'auto-ingest':
                        message = "Starting auto-ingestion of documents...";
                        endpoint = '/api/rag/auto-ingest';
                        break;
                    case 'clear':
                        message = "Clearing RAG index...";
                        endpoint = '/api/rag/clear';
                        break;
                    default:
                        return;
                }
                
                showDuckBotMessage(message);
                
                const response = await apiCall(endpoint, {
                    method: 'POST'
                });
                
                if (response.success) {
                    showDuckBotMessage(`RAG ${action} completed successfully!`);
                } else {
                    showDuckBotMessage(`RAG ${action} failed: ${response.error || 'Unknown error'}`);
                }
            } catch (error) {
                console.error(`RAG ${action} error:`, error);
                showDuckBotMessage(`Error with RAG ${action}: ${error.message}`);
            }
        };
        
        window.ragSearch = async function(appId) {
            const query = $("#rag-search-${app.id}").value;
            const resultsDiv = $("#rag-results-${app.id}");
            
            if (!query.trim()) return;
            
            try {
                resultsDiv.innerHTML = '<div class="text-slate-400">Searching...</div>';
                
                const response = await apiCall('/api/rag/search', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ query: query })
                });
                
                if (response.success && response.results) {
                    const resultsHtml = response.results.map(result => 
                        `<div class="border-b border-slate-600 pb-2 mb-2">
                            <div class="font-bold">${result.title || 'Document'}</div>
                            <div class="text-slate-300">${result.content?.substring(0, 200) || ''}...</div>
                            <div class="text-xs text-slate-500">Score: ${result.score?.toFixed(2) || 'N/A'}</div>
                        </div>`
                    ).join('');
                    
                    resultsDiv.innerHTML = resultsHtml || '<div class="text-slate-400">No results found</div>';
                } else {
                    resultsDiv.innerHTML = '<div class="text-red-400">Search failed</div>';
                }
            } catch (error) {
                console.error('RAG search error:', error);
                resultsDiv.innerHTML = `<div class="text-red-400">Search error: ${error.message}</div>`;
            }
        };
        
        // --- LOGS FUNCTIONS ---
        window.refreshLogs = async function(appId) {
            const container = $("#logs-container-${app.id}");
            const filter = $("#log-filter-${app.id}").value;
            
            try {
                container.innerHTML = '<div class="text-slate-400">Loading logs...</div>';
                
                const response = await apiCall(`/api/action-logs?filter=${filter}`);
                
                if (response.success && response.logs) {
                    const logsHtml = response.logs.map(log => 
                        `<div class="border-b border-slate-600 pb-1 mb-1">
                            <span class="text-xs text-slate-500">${log.timestamp || 'Unknown time'}</span>
                            <span class="text-blue-400 ml-2">[${log.type || 'INFO'}]</span>
                            <span class="ml-2">${log.message || 'No message'}</span>
                        </div>`
                    ).join('');
                    
                    container.innerHTML = logsHtml || '<div class="text-slate-400">No logs found</div>';
                } else {
                    container.innerHTML = '<div class="text-red-400">Failed to load logs</div>';
                }
            } catch (error) {
                console.error('Logs refresh error:', error);
                container.innerHTML = `<div class="text-red-400">Error loading logs: ${error.message}</div>`;
            }
        };
        
        // --- AUTO-LOADING FUNCTIONS ---
        async function loadRAGStats(appId) {
            const statsDiv = $("#rag-stats-${app.id}");
            if (!statsDiv) return;
            
            try {
                statsDiv.innerHTML = '<div class="text-slate-400">Loading...</div>';
                
                const response = await apiCall('/api/rag/stats');
                
                if (response.success) {
                    const stats = response.stats || {};
                    statsDiv.innerHTML = `
                        <div>Documents: ${stats.documents || 0}</div>
                        <div>Chunks: ${stats.chunks || 0}</div>
                        <div>Index size: ${stats.size || '0MB'}</div>
                        <div>Last updated: ${stats.lastUpdated || 'Never'}</div>
                    `;
                } else {
                    statsDiv.innerHTML = '<div class="text-red-400">Failed to load stats</div>';
                }
            } catch (error) {
                statsDiv.innerHTML = '<div class="text-red-400">Error loading stats</div>';
            }
        }
        
        async function loadQueueItems(appId) {
            const itemsDiv = $("#queue-items-${app.id}");
            if (!itemsDiv) return;
            
            try {
                const response = await apiCall('/api/queue/items');
                
                if (response.success && response.items && response.items.length > 0) {
                    const itemsHtml = response.items.map(item => `
                        <div class="bg-slate-800 rounded p-2 mb-2">
                            <div class="font-bold text-sm">${item.type || 'Task'}</div>
                            <div class="text-xs text-slate-400">${item.status || 'pending'} - ${item.created || 'unknown time'}</div>
                        </div>
                    `).join('');
                    itemsDiv.innerHTML = itemsHtml;
                } else {
                    itemsDiv.innerHTML = '<div class="text-slate-400 text-sm">No items in queue</div>';
                }
            } catch (error) {
                itemsDiv.innerHTML = '<div class="text-red-400 text-sm">Error loading queue</div>';
            }
        }
        
        async function loadModelInfo(appId) {
            const localModelsDiv = $("#local-models-${app.id}");
            if (!localModelsDiv) return;
            
            try {
                localModelsDiv.innerHTML = '<div class="text-slate-400">Loading local models...</div>';
                
                const response = await apiCall('/api/models/local');
                
                if (response.success && response.models) {
                    if (response.models.length > 0) {
                        const modelsHtml = response.models.map(model => `
                            <div class="text-sm">• ${model.name || model.id || 'Unknown Model'}</div>
                        `).join('');
                        localModelsDiv.innerHTML = modelsHtml;
                    } else {
                        localModelsDiv.innerHTML = '<div class="text-slate-400">No local models found</div>';
                    }
                } else {
                    localModelsDiv.innerHTML = '<div class="text-yellow-400">LM Studio not running</div>';
                }
            } catch (error) {
                localModelsDiv.innerHTML = '<div class="text-red-400">Error loading models</div>';
            }
        }
        
        // --- AI INTEGRATION FUNCTIONS ---
        
        // Qwen-Agent Functions
        window.executeQwenTask = async function(appId, taskType) {
            const taskInput = $("#qwen-task-input-${app.id}");
            const resultsDiv = $("#qwen-results-${app.id}");
            
            if (!taskInput.value.trim()) return;
            
            resultsDiv.innerHTML = '<div class="text-slate-400">Processing with Qwen-Agent...</div>';
            
            try {
                const response = await apiCall('/api/qwen/execute', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        task: taskInput.value.trim(),
                        task_type: taskType,
                        context: { app_id: appId }
                    })
                });
                
                if (response.success) {
                    resultsDiv.innerHTML = `
                        <div class="text-green-400 mb-2">✓ Task completed successfully</div>
                        <div class="bg-slate-800/50 rounded p-3 text-sm">
                            <div class="text-slate-300">${response.response || 'Task executed'}</div>
                            ${response.tools_used ? `<div class="text-xs text-slate-400 mt-2">Tools used: ${response.tools_used.join(', ')}</div>` : ''}
                        </div>
                    `;
                } else {
                    resultsDiv.innerHTML = `<div class="text-red-400">Task failed: ${response.error || 'Unknown error'}</div>`;
                }
                taskInput.value = '';
            } catch (error) {
                resultsDiv.innerHTML = `<div class="text-red-400">Error: ${error.message}</div>`;
            }
        };
        
        window.refreshQwenStatus = async function(appId) {
            const statusDiv = $("#qwen-status-${app.id}");
            
            try {
                statusDiv.innerHTML = '<div class="text-slate-400">Checking status...</div>';
                
                const response = await apiCall('/api/qwen/status');
                
                if (response.success) {
                    const caps = response.capabilities || {};
                    statusDiv.innerHTML = `
                        <div class="text-sm">
                            <div class="text-green-400">✓ Qwen-Agent Available: ${caps.available ? 'Yes' : 'No'}</div>
                            <div class="text-slate-300">Model: ${caps.model || 'Unknown'}</div>
                            <div class="text-slate-300">Tools: ${caps.tools ? caps.tools.join(', ') : 'None'}</div>
                        </div>
                    `;
                } else {
                    statusDiv.innerHTML = '<div class="text-red-400">Failed to check status</div>';
                }
            } catch (error) {
                statusDiv.innerHTML = `<div class="text-red-400">Error: ${error.message}</div>`;
            }
        };
        
        // Claude Code Functions
        window.executeClaudeTask = async function(appId, taskType) {
            const taskInput = $("#claude-task-input-${app.id}");
            const resultsDiv = $("#claude-results-${app.id}");
            
            if (!taskInput.value.trim()) return;
            
            resultsDiv.innerHTML = '<div class="text-slate-400">Processing with Claude Code...</div>';
            
            try {
                const response = await apiCall('/api/claude/execute', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        task: taskInput.value.trim(),
                        task_type: taskType,
                        context: { app_id: appId }
                    })
                });
                
                if (response.success) {
                    resultsDiv.innerHTML = `
                        <div class="text-green-400 mb-2">✓ Claude Code task completed</div>
                        <div class="bg-slate-800/50 rounded p-3 text-sm">
                            <div class="text-slate-300">${response.response || 'Task executed'}</div>
                            ${response.model ? `<div class="text-xs text-slate-400 mt-2">Model: ${response.model}</div>` : ''}
                            ${response.usage ? `<div class="text-xs text-slate-400">Tokens: ${JSON.stringify(response.usage)}</div>` : ''}
                        </div>
                    `;
                } else {
                    resultsDiv.innerHTML = `<div class="text-red-400">Task failed: ${response.error || 'Unknown error'}</div>`;
                }
                taskInput.value = '';
            } catch (error) {
                resultsDiv.innerHTML = `<div class="text-red-400">Error: ${error.message}</div>`;
            }
        };
        
        window.refreshClaudeStatus = async function(appId) {
            const statusDiv = $("#claude-status-${app.id}");
            
            try {
                statusDiv.innerHTML = '<div class="text-slate-400">Checking status...</div>';
                
                const response = await apiCall('/api/claude/status');
                
                if (response.success) {
                    const status = response.status || {};
                    statusDiv.innerHTML = `
                        <div class="text-sm">
                            <div class="text-green-400">✓ Claude Router: ${status.router_available ? 'Available' : 'Not Available'}</div>
                            <div class="text-slate-300">Native Claude: ${status.claude_code_available ? 'Available' : 'Not Available'}</div>
                            <div class="text-slate-300">Server Running: ${status.openrouter_server_running ? 'Yes' : 'No'}</div>
                            <div class="text-slate-300">Port: ${status.openrouter_port || 'N/A'}</div>
                        </div>
                    `;
                } else {
                    statusDiv.innerHTML = '<div class="text-red-400">Failed to check status</div>';
                }
            } catch (error) {
                statusDiv.innerHTML = `<div class="text-red-400">Error: ${error.message}</div>`;
            }
        };
        
        // AI Router Functions
        window.switchModel = async function(appId, modelType) {
            const statusDiv = $("#router-status-${app.id}");
            
            try {
                statusDiv.innerHTML = '<div class="text-slate-400">Switching model...</div>';
                
                const response = await apiCall('/api/ai-router/switch-model', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ model: modelType })
                });
                
                if (response.success) {
                    statusDiv.innerHTML = `<div class="text-green-400">✓ Switched to ${modelType}</div>`;
                    await refreshRouterStatus(appId);
                } else {
                    statusDiv.innerHTML = `<div class="text-red-400">Failed to switch: ${response.error || 'Unknown error'}</div>`;
                }
            } catch (error) {
                statusDiv.innerHTML = `<div class="text-red-400">Error: ${error.message}</div>`;
            }
        };
        
        window.testFallback = async function(appId) {
            const resultsDiv = $("#router-results-${app.id}");
            
            try {
                resultsDiv.innerHTML = '<div class="text-slate-400">Testing fallback chain...</div>';
                
                const response = await apiCall('/api/ai-router/test-fallback', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ test_message: "Hello, test message for fallback" })
                });
                
                if (response.success) {
                    resultsDiv.innerHTML = `
                        <div class="text-green-400 mb-2">✓ Fallback test completed</div>
                        <div class="bg-slate-800/50 rounded p-3 text-sm">
                            <div class="text-slate-300">Provider: ${response.provider || 'Unknown'}</div>
                            <div class="text-slate-300">Model: ${response.model || 'Unknown'}</div>
                            <div class="text-slate-300">Response: ${response.response?.substring(0, 100) || 'No response'}...</div>
                        </div>
                    `;
                } else {
                    resultsDiv.innerHTML = `<div class="text-red-400">Test failed: ${response.error || 'Unknown error'}</div>`;
                }
            } catch (error) {
                resultsDiv.innerHTML = `<div class="text-red-400">Error: ${error.message}</div>`;
            }
        };
        
        window.refreshRouterStatus = async function(appId) {
            const statusDiv = $("#router-status-${app.id}");
            
            try {
                const response = await apiCall('/api/ai-router/status');
                
                if (response.success) {
                    const status = response.status || {};
                    statusDiv.innerHTML = `
                        <div class="text-sm">
                            <div class="text-green-400">✓ Current Provider: ${status.current_provider || 'Unknown'}</div>
                            <div class="text-slate-300">Available Models: ${status.available_models || 0}</div>
                            <div class="text-slate-300">Cache Hits: ${status.cache_hits || 0}</div>
                            <div class="text-slate-300">Rate Limit: ${status.rate_limit_status || 'OK'}</div>
                        </div>
                    `;
                } else {
                    statusDiv.innerHTML = '<div class="text-red-400">Failed to get status</div>';
                }
            } catch (error) {
                statusDiv.innerHTML = `<div class="text-red-400">Error: ${error.message}</div>`;
            }
        };
        
        // Dynamic Models Functions
        window.loadSpecialistModel = async function(appId, modelType) {
            const statusDiv = $("#dynamic-status-${app.id}");
            
            try {
                statusDiv.innerHTML = '<div class="text-slate-400">Loading specialist model...</div>';
                
                const response = await apiCall('/api/dynamic-models/load-specialist', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ model_type: modelType })
                });
                
                if (response.success) {
                    statusDiv.innerHTML = `<div class="text-green-400">✓ Loaded ${modelType} specialist</div>`;
                    await refreshDynamicStatus(appId);
                } else {
                    statusDiv.innerHTML = `<div class="text-red-400">Failed to load: ${response.error || 'Unknown error'}</div>`;
                }
            } catch (error) {
                statusDiv.innerHTML = `<div class="text-red-400">Error: ${error.message}</div>`;
            }
        };
        
        window.cleanupModels = async function(appId) {
            const statusDiv = $("#dynamic-status-${app.id}");
            
            try {
                statusDiv.innerHTML = '<div class="text-slate-400">Cleaning up unused models...</div>';
                
                const response = await apiCall('/api/dynamic-models/cleanup', {
                    method: 'POST'
                });
                
                if (response.success) {
                    statusDiv.innerHTML = `<div class="text-green-400">✓ Cleanup completed</div>`;
                    await refreshDynamicStatus(appId);
                } else {
                    statusDiv.innerHTML = `<div class="text-red-400">Cleanup failed: ${response.error || 'Unknown error'}</div>`;
                }
            } catch (error) {
                statusDiv.innerHTML = `<div class="text-red-400">Error: ${error.message}</div>`;
            }
        };
        
        window.refreshDynamicStatus = async function(appId) {
            const statusDiv = $("#dynamic-status-${app.id}");
            const modelsDiv = $("#dynamic-models-${app.id}");
            
            try {
                const response = await apiCall('/api/dynamic-models/status');
                
                if (response.success) {
                    const status = response.status || {};
                    const models = status.loaded_models || [];
                    
                    const modelsHtml = models.length > 0 ? 
                        models.map(model => 
                            `<div class="text-sm text-slate-300">• ${model.name} (${model.type}) - ${model.memory_usage || 'N/A'}</div>`
                        ).join('') :
                        '<div class="text-slate-400">No specialist models loaded</div>';
                    
                    modelsDiv.innerHTML = modelsHtml;
                } else {
                    modelsDiv.innerHTML = '<div class="text-red-400">Failed to get status</div>';
                }
            } catch (error) {
                modelsDiv.innerHTML = `<div class="text-red-400">Error: ${error.message}</div>`;
            }
        };
        
        // Local Parity Functions
        window.testLocalParity = async function(appId, feature) {
            const resultsDiv = $("#parity-results-${app.id}");
            
            try {
                resultsDiv.innerHTML = '<div class="text-slate-400">Testing local parity...</div>';
                
                const response = await apiCall('/api/local-parity/test', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ feature: feature })
                });
                
                if (response.success) {
                    resultsDiv.innerHTML = `
                        <div class="text-green-400 mb-2">✓ ${feature} parity test passed</div>
                        <div class="bg-slate-800/50 rounded p-3 text-sm">
                            <div class="text-slate-300">Local: ${response.local_result ? 'Working' : 'Failed'}</div>
                            <div class="text-slate-300">Cloud: ${response.cloud_result ? 'Working' : 'Failed'}</div>
                            <div class="text-slate-300">Parity: ${response.parity ? 'Achieved' : 'Missing'}</div>
                        </div>
                    `;
                } else {
                    resultsDiv.innerHTML = `<div class="text-red-400">Test failed: ${response.error || 'Unknown error'}</div>`;
                }
            } catch (error) {
                resultsDiv.innerHTML = `<div class="text-red-400">Error: ${error.message}</div>`;
            }
        };
        
        window.refreshParityStatus = async function(appId) {
            const statusDiv = $("#parity-status-${app.id}");
            
            try {
                const response = await apiCall('/api/local-parity/status');
                
                if (response.success) {
                    const status = response.status || {};
                    statusDiv.innerHTML = `
                        <div class="text-sm">
                            <div class="text-green-400">✓ Local Mode: ${status.local_mode ? 'Enabled' : 'Disabled'}</div>
                            <div class="text-slate-300">Features Supported: ${status.supported_features || 0}</div>
                            <div class="text-slate-300">Parity Score: ${status.parity_score || '0%'}</div>
                            <div class="text-slate-300">Local Provider: ${status.local_provider || 'None'}</div>
                        </div>
                    `;
                } else {
                    statusDiv.innerHTML = '<div class="text-red-400">Failed to get status</div>';
                }
            } catch (error) {
                statusDiv.innerHTML = `<div class="text-red-400">Error: ${error.message}</div>`;
            }
        };
        
        // System Health Functions
        window.runHealthCheck = async function(appId, checkType) {
            const resultsDiv = $("#health-results-${app.id}");
            
            try {
                resultsDiv.innerHTML = '<div class="text-slate-400">Running health check...</div>';
                
                const response = await apiCall('/api/system-health/check', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ check_type: checkType })
                });
                
                if (response.success) {
                    const checks = response.checks || {};
                    const checksHtml = Object.entries(checks).map(([key, value]) => 
                        `<div class="text-sm">
                            <span class="${value.status === 'pass' ? 'text-green-400' : 'text-red-400'}">
                                ${value.status === 'pass' ? '✓' : '✗'} ${key}
                            </span>
                            <span class="text-slate-300 ml-2">${value.message || ''}</span>
                        </div>`
                    ).join('');
                    
                    resultsDiv.innerHTML = `
                        <div class="text-green-400 mb-2">Health Check: ${checkType}</div>
                        <div class="bg-slate-800/50 rounded p-3">
                            ${checksHtml || '<div class="text-slate-400">No checks performed</div>'}
                        </div>
                    `;
                } else {
                    resultsDiv.innerHTML = `<div class="text-red-400">Check failed: ${response.error || 'Unknown error'}</div>`;
                }
            } catch (error) {
                resultsDiv.innerHTML = `<div class="text-red-400">Error: ${error.message}</div>`;
            }
        };
        
        window.refreshHealthStatus = async function(appId) {
            const statusDiv = $("#health-status-${app.id}");
            
            try {
                const response = await apiCall('/api/system-health/status');
                
                if (response.success) {
                    const status = response.status || {};
                    statusDiv.innerHTML = `
                        <div class="text-sm">
                            <div class="text-green-400">✓ Overall Health: ${status.overall_health || 'Unknown'}</div>
                            <div class="text-slate-300">Services: ${status.services_healthy || 0}/${status.total_services || 0}</div>
                            <div class="text-slate-300">CPU: ${status.cpu_usage || '0%'}</div>
                            <div class="text-slate-300">Memory: ${status.memory_usage || '0%'}</div>
                        </div>
                    `;
                } else {
                    statusDiv.innerHTML = '<div class="text-red-400">Failed to get status</div>';
                }
            } catch (error) {
                statusDiv.innerHTML = `<div class="text-red-400">Error: ${error.message}</div>`;
            }
        };
        
        // Performance Functions
        window.runBenchmark = async function(appId, benchmarkType) {
            const resultsDiv = $("#performance-results-${app.id}");
            
            try {
                resultsDiv.innerHTML = '<div class="text-slate-400">Running benchmark...</div>';
                
                const response = await apiCall('/api/performance/benchmark', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ benchmark_type: benchmarkType })
                });
                
                if (response.success) {
                    const results = response.results || {};
                    resultsDiv.innerHTML = `
                        <div class="text-green-400 mb-2">✓ ${benchmarkType} benchmark completed</div>
                        <div class="bg-slate-800/50 rounded p-3 text-sm">
                            <div class="text-slate-300">Duration: ${results.duration || 'N/A'}ms</div>
                            <div class="text-slate-300">Score: ${results.score || 'N/A'}</div>
                            <div class="text-slate-300">Details: ${results.details || 'No details'}</div>
                        </div>
                    `;
                } else {
                    resultsDiv.innerHTML = `<div class="text-red-400">Benchmark failed: ${response.error || 'Unknown error'}</div>`;
                }
            } catch (error) {
                resultsDiv.innerHTML = `<div class="text-red-400">Error: ${error.message}</div>`;
            }
        };
        
        window.exportMetrics = async function(appId) {
            const resultsDiv = $("#performance-results-${app.id}");
            
            try {
                resultsDiv.innerHTML = '<div class="text-slate-400">Exporting metrics...</div>';
                
                const response = await apiCall('/api/performance/export', {
                    method: 'POST'
                });
                
                if (response.success) {
                    resultsDiv.innerHTML = `<div class="text-green-400">✓ Metrics exported successfully</div>`;
                    
                    // Trigger download if URL provided
                    if (response.download_url) {
                        const link = document.createElement('a');
                        link.href = response.download_url;
                        link.download = 'duckbot_metrics.json';
                        link.click();
                    }
                } else {
                    resultsDiv.innerHTML = `<div class="text-red-400">Export failed: ${response.error || 'Unknown error'}</div>`;
                }
            } catch (error) {
                resultsDiv.innerHTML = `<div class="text-red-400">Error: ${error.message}</div>`;
            }
        };
        
        // --- DUCK BOT 3D ---
        function initDuckBot3D() {
            const container = duckbot3DCanvas;
            state.duckBot.clock = new THREE.Clock();
            state.duckBot.scene = new THREE.Scene();
            state.duckBot.camera = new THREE.PerspectiveCamera(50, container.clientWidth / container.clientHeight, 0.1, 100);
            state.duckBot.camera.position.set(0, 1.2, 3);
            state.duckBot.renderer = new THREE.WebGLRenderer({ canvas: container, antialias: true, alpha: true });
            state.duckBot.renderer.setSize(container.clientWidth, container.clientHeight);
            state.duckBot.renderer.setPixelRatio(window.devicePixelRatio);
            
            const ambientLight = new THREE.AmbientLight(0xffffff, 2);
            state.duckBot.scene.add(ambientLight);
            const directionalLight = new THREE.DirectionalLight(0xffffff, 3);
            directionalLight.position.set(5, 5, 5);
            state.duckBot.scene.add(directionalLight);
            
            new GLTFLoader().load('https://threejs.org/examples/models/gltf/RobotExpressive/RobotExpressive.glb', (gltf) => {
                const model = gltf.scene;
                state.duckBot.scene.add(model);
                const box = new THREE.Box3().setFromObject(model);
                const center = box.getCenter(new THREE.Vector3());
                model.position.sub(center);
                
                state.duckBot.mixer = new THREE.AnimationMixer(model);
                const idleClip = THREE.AnimationClip.findByName(gltf.animations, 'Idle');
                const talkClip = THREE.AnimationClip.findByName(gltf.animations, 'Wave');
                if (idleClip) {
                    state.duckBot.idleAction = state.duckBot.mixer.clipAction(idleClip);
                    state.duckBot.idleAction.play();
                }
                if (talkClip) {
                    state.duckBot.talkAction = state.duckBot.mixer.clipAction(talkClip);
                }
            });

            function animate() {
                requestAnimationFrame(animate);
                const delta = state.duckBot.clock.getDelta();
                if (state.duckBot.mixer) state.duckBot.mixer.update(delta);
                state.duckBot.renderer.render(state.duckBot.scene, state.duckBot.camera);
            }
            animate();
        }
        
        function setDuckBotSpeaking(isSpeaking) {
            if (!state.duckBot.idleAction || !state.duckBot.talkAction) return;
            if (isSpeaking) {
                state.duckBot.idleAction.fadeOut(0.5);
                state.duckBot.talkAction.reset().fadeIn(0.5).play();
            } else {
                state.duckBot.talkAction.fadeOut(0.5);
                state.duckBot.idleAction.reset().fadeIn(0.5).play();
            }
        }
        
        function showDuckBotMessage(message, timeout = 6000) {
            duckbotMessage.textContent = message;
            duckbotSpeechBubble.style.display = 'block';
            setDuckBotSpeaking(true);
            
            if (state.voiceEnabled && window.speechSynthesis) {
                const utterance = new SpeechSynthesisUtterance(message);
                utterance.rate = 0.9;
                utterance.pitch = 1.1;
                window.speechSynthesis.speak(utterance);
            }
            
            setTimeout(() => {
                duckbotSpeechBubble.style.display = 'none';
                setDuckBotSpeaking(false);
            }, timeout);
        }
        
        // --- AI & COMMANDS ---
        async function handleCommand(e) {
            e.preventDefault();
            const input = commandInput.value.trim();
            if (!input || state.agentStatus === 'thinking') return;

            state.conversation.push({ type: 'user', content: input });
            commandInput.value = '';
            state.agentStatus = 'thinking';
            state.abortController = new AbortController();
            render();
            
            const eventSource = new EventSource(`/v1/chat/completions?message=${encodeURIComponent(input)}&model=duckbot-auto&stream=true`);

            eventSource.onmessage = function(event) {
                const data = JSON.parse(event.data);
                if (data.choices && data.choices[0].delta.content) {
                    state.conversation.push({ type: 'agent', content: data.choices[0].delta.content });
                    render();
                }
            };

            eventSource.addEventListener('thought', function(event) {
                const data = JSON.parse(event.data);
                state.conversation.push({ type: 'thought', content: data.thought });
                render();
            });

            eventSource.onerror = function(err) {
                console.error("EventSource failed:", err);
                eventSource.close();
                state.agentStatus = 'idle';
                render();
            };

            eventSource.addEventListener('end', function(event) {
                eventSource.close();
                state.agentStatus = 'idle';
                render();
            });
        }
        
        // --- EVENT LISTENERS ---
        function setupEventListeners() {
            commandForm.addEventListener('submit', handleCommand);
            
            stopBtn.addEventListener('click', () => {
                state.abortController.abort();
                state.agentStatus = 'idle';
                showDuckBotMessage("Request stopped");
                render();
            });

            pauseBtn.addEventListener('click', async () => {
                state.agentPaused = !state.agentPaused;
                if (state.agentPaused) {
                    await apiCall('/api/agent/pause', { method: 'POST' });
                    pauseBtn.textContent = 'Resume';
                } else {
                    await apiCall('/api/agent/resume', { method: 'POST' });
                    pauseBtn.textContent = 'Pause';
                }
            });
            
            voiceToggle.addEventListener('click', () => {
                state.voiceEnabled = !state.voiceEnabled;
                voiceToggle.textContent = state.voiceEnabled ? '🔊 Voice' : '🔇 Voice';
                voiceToggle.classList.toggle('bg-green-600', state.voiceEnabled);
                showDuckBotMessage(state.voiceEnabled ? 'Voice enabled' : 'Voice disabled');
            });

            // Icons
            iconsGrid.addEventListener('click', (e) => {
                const appIcon = e.target.closest('[data-appid]');
                if (appIcon) {
                    const appId = parseInt(appIcon.dataset.appid);
                    const app = state.apps.find(a => a.id === appId);
                    if(app) {
                         app.open = true;
                         app.zIndex = Math.max(...state.apps.map(a => a.zIndex), 10) + 1;
                         showDuckBotMessage(`Opening ${app.name}`);
                         
                         // Auto-load content for certain apps
                         setTimeout(() => {
                             if (app.type === 'logs') {
                                 refreshLogs(app.id);
                             } else if (app.type === 'rag') {
                                 loadRAGStats(app.id);
                             } else if (app.type === 'queue') {
                                 loadQueueItems(app.id);
                             } else if (app.type === 'models') {
                                 loadModelInfo(app.id);
                             }
                         }, 100);
                         
                         render();
                    }
                }
            });

            // Window dragging and management
            let isDraggingWindow = false;
            let draggedWindow = null;
            let dragOffset = { x: 0, y: 0 };
            
            windowsContainer.addEventListener('mousedown', (e) => {
                const windowEl = e.target.closest('.window');
                if (windowEl) {
                    const appId = parseInt(windowEl.dataset.appid);
                    const app = state.apps.find(a => a.id === appId);
                    if (app) {
                        // Bring window to front
                        app.zIndex = Math.max(...state.apps.map(a => a.zIndex), 10) + 1;
                        
                        // Check if clicking on window header for dragging
                        if (e.target.closest('.window-header')) {
                            isDraggingWindow = true;
                            draggedWindow = app;
                            
                            const rect = windowEl.getBoundingClientRect();
                            dragOffset.x = e.clientX - rect.left;
                            dragOffset.y = e.clientY - rect.top;
                            
                            windowEl.classList.add('dragging');
                            e.preventDefault(); // Prevent text selection
                        }
                        
                        render();
                    }
                }
            });
            
            document.addEventListener('mousemove', (e) => {
                if (isDraggingWindow && draggedWindow) {
                    const newX = Math.max(0, Math.min(window.innerWidth - 200, e.clientX - dragOffset.x));
                    const newY = Math.max(0, Math.min(window.innerHeight - 100, e.clientY - dragOffset.y));
                    
                    draggedWindow.position.x = newX;
                    draggedWindow.position.y = newY;
                    
                    // Update window position immediately without full re-render for performance
                    const windowEl = document.querySelector(`[data-appid="${draggedWindow.id}"]`);
                    if (windowEl) {
                        windowEl.style.left = newX + 'px';
                        windowEl.style.top = newY + 'px';
                    }
                }
            });
            
            document.addEventListener('mouseup', () => {
                if (isDraggingWindow) {
                    isDraggingWindow = false;
                    if (draggedWindow) {
                        // Remove dragging class
                        const windowEl = document.querySelector(`[data-appid="${draggedWindow.id}"]`);
                        if (windowEl) windowEl.classList.remove('dragging');
                        draggedWindow = null;
                    }
                }
            });

            windowsContainer.addEventListener('click', (e) => {
                if (e.target.classList.contains('close-window-btn')) {
                    const appId = parseInt(e.target.dataset.appid);
                    const app = state.apps.find(a => a.id === appId);
                    if (app) {
                        app.open = false;
                        showDuckBotMessage(`${app.name} closed`);
                    }
                    render();
                }
            });

             // DuckBot Dragging
            let isDraggingDuck = false, dragOffsetX, dragOffsetY;
            duckbotClippyContainer.addEventListener('mousedown', (e) => {
                isDraggingDuck = true;
                const rect = duckbotClippyContainer.getBoundingClientRect();
                dragOffsetX = e.clientX - rect.left;
                dragOffsetY = e.clientY - rect.top;
                duckbotClippyContainer.style.transition = 'none';
            });
            document.addEventListener('mousemove', (e) => {
                if (isDraggingDuck) {
                   const x = e.clientX - dragOffsetX;
                   const y = e.clientY - dragOffsetY;
                   duckbotClippyContainer.style.left = `${x}px`;
                   duckbotClippyContainer.style.top = `${y}px`;
                }
            });
            document.addEventListener('mouseup', () => { isDraggingDuck = false; });
            hideDuckbotBtn.addEventListener('click', () => { 
                state.duckBot.visible = false; 
                duckbotClippyContainer.style.display = 'none'; 
                showDuckbotBtn.style.display = 'flex'; 
            });
            showDuckbotBtn.addEventListener('click', () => { 
                state.duckBot.visible = true; 
                duckbotClippyContainer.style.display = 'block'; 
                showDuckbotBtn.style.display = 'none'; 
                showDuckBotMessage("I'm back!"); 
            });

            // --- CANVAS BACKGROUND ---
            function animateCanvasBackground() {
                const ctx = canvasBg.getContext('2d');
                let width = canvasBg.width = window.innerWidth;
                let height = canvasBg.height = window.innerHeight;
                let stars = [];
                let numStars = 200;

                for(let i = 0; i < numStars; i++) {
                    stars.push({
                        x: Math.random() * width,
                        y: Math.random() * height,
                        radius: Math.random() * 1.5,
                        vx: Math.floor(Math.random() * 50) - 25,
                        vy: Math.floor(Math.random() * 50) - 25
                    });
                }

                function draw() {
                    ctx.clearRect(0, 0, width, height);
                    ctx.globalCompositeOperation = "lighter";
                    
                    for(let i = 0; i < stars.length; i++) {
                        let s = stars[i];
                        ctx.fillStyle = "#fff";
                        ctx.beginPath();
                        ctx.arc(s.x, s.y, s.radius, 0, 2 * Math.PI);
                        ctx.fill();
                    }
                }

                function update() {
                    for(let i = 0; i < stars.length; i++) {
                        let s = stars[i];
                        s.x += s.vx / 60;
                        s.y += s.vy / 60;
                        
                        if(s.x < 0 || s.x > width) s.vx = -s.vx;
                        if(s.y < 0 || s.y > height) s.vy = -s.vy;
                    }
                }

                function tick() {
                    draw();
                    update();
                    requestAnimationFrame(tick);
                }

                tick();
            }
        }

        // --- STARTUP ---
        document.addEventListener('DOMContentLoaded', init);
