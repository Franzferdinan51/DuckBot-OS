/**
 * DeepCode UI - Frontend JavaScript for DeepCode WebUI
 * Handles all interactive features, WebSocket connections, and API calls
 */

class DeepCodeUI {
    constructor() {
        this.ws = null;
        this.connected = false;
        this.currentTab = 'overview';
        this.agents = [];
        this.mcpServers = [];
        this.projects = [];
        this.tasks = [];

        this.init();
    }

    init() {
        this.initEventListeners();
        this.initWebSocket();
        this.initCharts();
        this.loadInitialData();
        this.initTheme();
    }

    initEventListeners() {
        // Tab switching
        document.querySelectorAll('.tab-button').forEach(button => {
            button.addEventListener('click', (e) => {
                this.switchTab(e.target.dataset.tab);
            });
        });

        // Theme toggle
        document.getElementById('themeToggle').addEventListener('click', () => {
            this.toggleTheme();
        });

        // Modal close
        document.getElementById('modal-overlay').addEventListener('click', (e) => {
            if (e.target.id === 'modal-overlay') {
                this.closeModal();
            }
        });

        // File upload drag and drop
        this.initFileUpload();

        // Form submissions
        this.initFormHandlers();

        // Keyboard shortcuts
        this.initKeyboardShortcuts();
    }

    initWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/deepcode`;

        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
            this.connected = true;
            this.updateStatus('online');
            this.showToast('Connected to DeepCode', 'success');
        };

        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleWebSocketMessage(data);
        };

        this.ws.onclose = () => {
            this.connected = false;
            this.updateStatus('offline');
            this.showToast('Disconnected from DeepCode', 'warning');
            // Attempt to reconnect
            setTimeout(() => this.initWebSocket(), 5000);
        };

        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.showToast('WebSocket connection error', 'error');
        };
    }

    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'agent_update':
                this.updateAgent(data.agent);
                break;
            case 'mcp_server_update':
                this.updateMCPServer(data.server);
                break;
            case 'task_update':
                this.updateTask(data.task);
                break;
            case 'project_update':
                this.updateProject(data.project);
                break;
            case 'system_status':
                this.updateSystemStatus(data.status);
                break;
            case 'activity':
                this.addActivity(data.activity);
                break;
            default:
                console.log('Unknown message type:', data.type);
        }
    }

    initCharts() {
        // Agent Performance Chart
        const agentCtx = document.getElementById('agent-performance-chart');
        if (agentCtx) {
            this.agentChart = new Chart(agentCtx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Tasks Completed',
                        data: [],
                        borderColor: 'rgb(124, 58, 237)',
                        backgroundColor: 'rgba(124, 58, 237, 0.1)',
                        tension: 0.1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: true
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        }

        // MCP Connections Chart
        const mcpCtx = document.getElementById('mcp-connections-chart');
        if (mcpCtx) {
            this.mcpChart = new Chart(mcpCtx, {
                type: 'doughnut',
                data: {
                    labels: ['Connected', 'Disconnected', 'Connecting'],
                    datasets: [{
                        data: [0, 0, 0],
                        backgroundColor: [
                            'rgb(16, 185, 129)',
                            'rgb(239, 68, 68)',
                            'rgb(245, 158, 11)'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom'
                        }
                    }
                }
            });
        }
    }

    async loadInitialData() {
        try {
            const [agents, mcpServers, projects, tasks] = await Promise.all([
                this.fetchAPI('/api/deepcode/agents'),
                this.fetchAPI('/api/deepcode/mcp-servers'),
                this.fetchAPI('/api/deepcode/projects'),
                this.fetchAPI('/api/deepcode/tasks')
            ]);

            this.agents = agents;
            this.mcpServers = mcpServers;
            this.projects = projects;
            this.tasks = tasks;

            this.updateUI();
        } catch (error) {
            console.error('Failed to load initial data:', error);
            this.showToast('Failed to load initial data', 'error');
        }
    }

    updateUI() {
        this.updateAgentsList();
        this.updateMCPServersList();
        this.updateProjectsList();
        this.updateStats();
        this.updateCharts();
    }

    updateAgentsList() {
        const container = document.getElementById('agents-list');
        if (!container) return;

        container.innerHTML = this.agents.map(agent => `
            <div class="agent-card">
                <div class="agent-header">
                    <span class="agent-name">${agent.name}</span>
                    <span class="agent-status ${agent.status}"></span>
                </div>
                <div class="agent-description">${agent.description}</div>
                <div class="agent-stats">
                    <span>Tasks: ${agent.tasks_completed}</span>
                    <span>Success: ${agent.success_rate}%</span>
                </div>
            </div>
        `).join('');
    }

    updateMCPServersList() {
        const container = document.getElementById('mcp-servers-list');
        if (!container) return;

        container.innerHTML = this.mcpServers.map(server => `
            <div class="mcp-server-card">
                <div class="mcp-server-name">${server.name}</div>
                <div class="mcp-server-type">${server.type}</div>
                <div class="mcp-server-status">
                    <span class="agent-status ${server.status}"></span>
                    <span>${server.status}</span>
                </div>
                <div class="mcp-server-connection">
                    <span>Port: ${server.port}</span>
                    <button class="btn-sm" onclick="deepcodeUI.toggleMCPServer('${server.id}')">
                        ${server.status === 'connected' ? 'Disconnect' : 'Connect'}
                    </button>
                </div>
            </div>
        `).join('');
    }

    updateProjectsList() {
        const container = document.getElementById('web-projects');
        if (!container) return;

        container.innerHTML = this.projects.filter(p => p.type === 'web').map(project => `
            <div class="project-card">
                <div class="project-header">
                    <span class="project-name">${project.name}</span>
                    <span class="project-type">${project.framework}</span>
                </div>
                <div class="project-description">${project.description}</div>
                <div class="project-stats">
                    <span>Created: ${new Date(project.created_at).toLocaleDateString()}</span>
                    <span>Status: ${project.status}</span>
                </div>
            </div>
        `).join('');
    }

    updateStats() {
        document.getElementById('active-agents').textContent = this.agents.filter(a => a.status === 'online').length;
        document.getElementById('mcp-servers').textContent = this.mcpServers.filter(s => s.status === 'connected').length;
        document.getElementById('tasks-completed').textContent = this.tasks.filter(t => t.status === 'completed').length;

        const successRate = this.tasks.length > 0 ?
            Math.round((this.tasks.filter(t => t.status === 'completed').length / this.tasks.length) * 100) : 0;
        document.getElementById('success-rate').textContent = `${successRate}%`;
    }

    updateCharts() {
        // Update agent performance chart
        if (this.agentChart) {
            const labels = this.agents.map(a => a.name);
            const data = this.agents.map(a => a.tasks_completed);

            this.agentChart.data.labels = labels;
            this.agentChart.data.datasets[0].data = data;
            this.agentChart.update();
        }

        // Update MCP connections chart
        if (this.mcpChart) {
            const connected = this.mcpServers.filter(s => s.status === 'connected').length;
            const disconnected = this.mcpServers.filter(s => s.status === 'disconnected').length;
            const connecting = this.mcpServers.filter(s => s.status === 'connecting').length;

            this.mcpChart.data.datasets[0].data = [connected, disconnected, connecting];
            this.mcpChart.update();
        }
    }

    switchTab(tabName) {
        // Update tab buttons
        document.querySelectorAll('.tab-button').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

        // Update tab content
        document.querySelectorAll('.tab-pane').forEach(pane => {
            pane.classList.remove('active');
        });
        document.getElementById(tabName).classList.add('active');

        this.currentTab = tabName;

        // Load tab-specific data
        this.loadTabData(tabName);
    }

    async loadTabData(tabName) {
        try {
            switch (tabName) {
                case 'paper2code':
                    await this.loadPaper2CodeData();
                    break;
                case 'text2web':
                    await this.loadText2WebData();
                    break;
                case 'text2backend':
                    await this.loadText2BackendData();
                    break;
                case 'agents':
                    await this.loadAgentsData();
                    break;
                case 'mcp':
                    await this.loadMCPData();
                    break;
            }
        } catch (error) {
            console.error(`Failed to load ${tabName} data:`, error);
        }
    }

    async loadPaper2CodeData() {
        const papers = await this.fetchAPI('/api/deepcode/papers');
        const container = document.getElementById('paper-list');

        if (container) {
            container.innerHTML = papers.map(paper => `
                <div class="paper-item">
                    <div class="paper-info">
                        <div class="paper-title">${paper.title}</div>
                        <div class="paper-meta">
                            Uploaded: ${new Date(paper.uploaded_at).toLocaleDateString()}
                        </div>
                    </div>
                    <div class="paper-actions">
                        <button class="btn-sm primary" onclick="deepcodeUI.analyzePaper('${paper.id}')">
                            Analyze
                        </button>
                        <button class="btn-sm secondary" onclick="deepcodeUI.generateCodeFromPaper('${paper.id}')">
                            Generate Code
                        </button>
                    </div>
                </div>
            `).join('');
        }
    }

    async generateWebApp() {
        const description = document.getElementById('web-description').value;
        const framework = document.getElementById('web-framework').value;
        const styling = document.getElementById('web-styling').value;

        if (!description.trim()) {
            this.showToast('Please provide a project description', 'warning');
            return;
        }

        try {
            this.showLoading('Generating web application...');

            const response = await this.fetchAPI('/api/deepcode/generate-web', {
                method: 'POST',
                body: JSON.stringify({
                    description,
                    framework,
                    styling
                })
            });

            this.showToast('Web application generated successfully!', 'success');
            this.loadTabData('text2web');
        } catch (error) {
            console.error('Failed to generate web app:', error);
            this.showToast('Failed to generate web application', 'error');
        } finally {
            this.hideLoading();
        }
    }

    async generateBackend() {
        const description = document.getElementById('backend-description').value;
        const framework = document.getElementById('backend-framework').value;
        const database = document.getElementById('backend-database').value;

        if (!description.trim()) {
            this.showToast('Please provide a backend description', 'warning');
            return;
        }

        try {
            this.showLoading('Generating backend...');

            const response = await this.fetchAPI('/api/deepcode/generate-backend', {
                method: 'POST',
                body: JSON.stringify({
                    description,
                    framework,
                    database
                })
            });

            this.showToast('Backend generated successfully!', 'success');
            this.loadTabData('text2backend');
        } catch (error) {
            console.error('Failed to generate backend:', error);
            this.showToast('Failed to generate backend', 'error');
        } finally {
            this.hideLoading();
        }
    }

    initFileUpload() {
        const uploadZone = document.getElementById('paper-upload-zone');
        const fileInput = document.getElementById('paper-input');

        if (!uploadZone) return;

        uploadZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadZone.classList.add('drag-over');
        });

        uploadZone.addEventListener('dragleave', () => {
            uploadZone.classList.remove('drag-over');
        });

        uploadZone.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadZone.classList.remove('drag-over');
            this.handleFileUpload(e.dataTransfer.files);
        });

        fileInput.addEventListener('change', (e) => {
            this.handleFileUpload(e.target.files);
        });
    }

    async handleFileUpload(files) {
        if (files.length === 0) return;

        const file = files[0];
        const formData = new FormData();
        formData.append('file', file);

        try {
            this.showLoading('Uploading paper...');

            const response = await this.fetchAPI('/api/deepcode/upload-paper', {
                method: 'POST',
                body: formData,
                headers: {} // Let browser set Content-Type for FormData
            });

            this.showToast('Paper uploaded successfully!', 'success');
            this.loadTabData('paper2code');
        } catch (error) {
            console.error('Failed to upload paper:', error);
            this.showToast('Failed to upload paper', 'error');
        } finally {
            this.hideLoading();
        }
    }

    initFormHandlers() {
        // Add form submission handlers here
    }

    initKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey || e.metaKey) {
                switch (e.key) {
                    case 'n':
                        e.preventDefault();
                        this.showNewTaskModal();
                        break;
                    case 'o':
                        e.preventDefault();
                        document.getElementById('paper-input').click();
                        break;
                }
            }
        });
    }

    initTheme() {
        const savedTheme = localStorage.getItem('theme') || 'light';
        document.documentElement.setAttribute('data-theme', savedTheme);
        this.updateThemeToggle(savedTheme);
    }

    toggleTheme() {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';

        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        this.updateThemeToggle(newTheme);
    }

    updateThemeToggle(theme) {
        const toggle = document.getElementById('themeToggle');
        toggle.textContent = theme === 'light' ? '🌙' : '☀️';
    }

    updateStatus(status) {
        const indicator = document.getElementById('deepcode-status');
        if (indicator) {
            indicator.className = `status-indicator ${status}`;
        }
    }

    showNewTaskModal() {
        this.showModal('New Task', this.getNewTaskForm());
    }

    showPaperUploadModal() {
        this.showModal('Upload Paper', this.getPaperUploadForm());
    }

    showProjectModal() {
        this.showModal('New Project', this.getProjectForm());
    }

    showAgentsModal() {
        this.showModal('Manage Agents', this.getAgentsForm());
    }

    showModal(title, content) {
        document.getElementById('modal-title').textContent = title;
        document.getElementById('modal-body').innerHTML = content;
        document.getElementById('modal-overlay').classList.add('active');
    }

    closeModal() {
        document.getElementById('modal-overlay').classList.remove('active');
    }

    showToast(message, type = 'info') {
        const container = document.getElementById('toast-container');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;

        toast.innerHTML = `
            <div class="toast-title">${type.charAt(0).toUpperCase() + type.slice(1)}</div>
            <div class="toast-message">${message}</div>
        `;

        container.appendChild(toast);

        setTimeout(() => {
            toast.remove();
        }, 5000);
    }

    showLoading(message = 'Loading...') {
        this.showToast(message, 'info');
    }

    hideLoading() {
        // Remove loading toasts
        const loadingToasts = document.querySelectorAll('.toast.info');
        loadingToasts.forEach(toast => {
            if (toast.textContent.includes('Loading') || toast.textContent.includes('Generating')) {
                toast.remove();
            }
        });
    }

    addActivity(activity) {
        const feed = document.getElementById('activity-feed');
        if (!feed) return;

        const activityItem = document.createElement('div');
        activityItem.className = 'activity-item';
        activityItem.innerHTML = `
            <div class="activity-time">${new Date().toLocaleTimeString()}</div>
            <div class="activity-content">${activity.message}</div>
        `;

        feed.insertBefore(activityItem, feed.firstChild);

        // Keep only last 50 activities
        while (feed.children.length > 50) {
            feed.removeChild(feed.lastChild);
        }
    }

    updateSystemStatus(status) {
        // Update system status indicators
        this.updateStatus(status.overall);
        this.updateStats();
    }

    updateAgent(agent) {
        const index = this.agents.findIndex(a => a.id === agent.id);
        if (index !== -1) {
            this.agents[index] = agent;
        } else {
            this.agents.push(agent);
        }
        this.updateAgentsList();
        this.updateStats();
        this.updateCharts();
    }

    updateMCPServer(server) {
        const index = this.mcpServers.findIndex(s => s.id === server.id);
        if (index !== -1) {
            this.mcpServers[index] = server;
        } else {
            this.mcpServers.push(server);
        }
        this.updateMCPServersList();
        this.updateStats();
        this.updateCharts();
    }

    updateTask(task) {
        const index = this.tasks.findIndex(t => t.id === task.id);
        if (index !== -1) {
            this.tasks[index] = task;
        } else {
            this.tasks.push(task);
        }
        this.updateStats();
        this.addActivity({
            message: `Task "${task.title}" ${task.status}`,
            timestamp: new Date()
        });
    }

    updateProject(project) {
        const index = this.projects.findIndex(p => p.id === project.id);
        if (index !== -1) {
            this.projects[index] = project;
        } else {
            this.projects.push(project);
        }
        this.updateProjectsList();
    }

    async fetchAPI(url, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
            }
        };

        const finalOptions = {
            ...defaultOptions,
            ...options,
            headers: {
                ...defaultOptions.headers,
                ...options.headers
            }
        };

        const response = await fetch(url, finalOptions);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    }

    // Form template methods
    getNewTaskForm() {
        return `
            <form id="new-task-form">
                <div class="form-group">
                    <label>Task Type</label>
                    <select name="task_type">
                        <option value="paper2code">Paper2Code</option>
                        <option value="text2web">Text2Web</option>
                        <option value="text2backend">Text2Backend</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Description</label>
                    <textarea name="description" rows="4" required></textarea>
                </div>
                <div class="form-group">
                    <label>Priority</label>
                    <select name="priority">
                        <option value="low">Low</option>
                        <option value="medium">Medium</option>
                        <option value="high">High</option>
                    </select>
                </div>
                <div class="form-actions">
                    <button type="submit" class="btn primary">Create Task</button>
                    <button type="button" class="btn secondary" onclick="deepcodeUI.closeModal()">Cancel</button>
                </div>
            </form>
        `;
    }

    getPaperUploadForm() {
        return `
            <div class="upload-zone" onclick="document.getElementById('modal-paper-input').click()">
                <div class="upload-content">
                    <div class="upload-icon">📄</div>
                    <h3>Upload Research Paper</h3>
                    <p>Click to select file or drag and drop</p>
                    <input type="file" id="modal-paper-input" accept=".pdf,.doc,.docx,.txt" style="display: none;">
                </div>
            </div>
        `;
    }

    getProjectForm() {
        return `
            <form id="new-project-form">
                <div class="form-group">
                    <label>Project Type</label>
                    <select name="project_type">
                        <option value="web">Web Application</option>
                        <option value="backend">Backend Service</option>
                        <option value="fullstack">Full Stack</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Project Name</label>
                    <input type="text" name="name" required>
                </div>
                <div class="form-group">
                    <label>Description</label>
                    <textarea name="description" rows="4" required></textarea>
                </div>
                <div class="form-actions">
                    <button type="submit" class="btn primary">Create Project</button>
                    <button type="button" class="btn secondary" onclick="deepcodeUI.closeModal()">Cancel</button>
                </div>
            </form>
        `;
    }

    getAgentsForm() {
        return `
            <form id="new-agent-form">
                <div class="form-group">
                    <label>Agent Type</label>
                    <select name="agent_type">
                        <option value="paper_analyzer">Paper Analyzer</option>
                        <option value="code_generator">Code Generator</option>
                        <option value="quality_assurance">Quality Assurance</option>
                        <option value="project_manager">Project Manager</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Agent Name</label>
                    <input type="text" name="name" required>
                </div>
                <div class="form-group">
                    <label>Capabilities</label>
                    <textarea name="capabilities" rows="3" placeholder="Describe agent capabilities..."></textarea>
                </div>
                <div class="form-actions">
                    <button type="submit" class="btn primary">Create Agent</button>
                    <button type="button" class="btn secondary" onclick="deepcodeUI.closeModal()">Cancel</button>
                </div>
            </form>
        `;
    }
}

// Initialize DeepCode UI when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.deepcodeUI = new DeepCodeUI();
});

// Export for use in other scripts
window.DeepCodeUI = DeepCodeUI;