"""
Web Agent Framework for DuckBot v4.2

Specialized framework for deploying and managing web-based agents in browser environments.
Based on AP2 patterns for web scenarios with consistent type systems and APIs.

Features:
- Browser-based agent deployment
- WebAssembly (WASM) agent support
- Progressive Web App (PWA) agents
- WebSocket-based real-time communication
- Cross-browser compatibility
- Web agent coordination and synchronization
"""

import asyncio
import json
import logging
import os
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union
import base64
import hashlib
import mimetypes

# DuckBot imports
from duckbot.core.logging_setup import setup_logging
from duckbot.core.utilities import safe_execute, ensure_directory_exists
from duckbot.agents.cross_platform_framework import (
    BasePlatformDeployer, AgentDeployment, DeploymentStatus, AgentPlatform,
    PlatformConfig
)

logger = setup_logging(__name__)


class WebAgentType(Enum):
    """Web agent deployment types."""
    WASM = "wasm"  # WebAssembly-based agent
    JAVASCRIPT = "javascript"  # JavaScript-based agent
    PWA = "pwa"  # Progressive Web App agent
    WEB_WORKER = "web_worker"  # Web Worker-based agent
    SERVICE_WORKER = "service_worker"  # Service Worker-based agent


class BrowserType(Enum):
    """Supported browser types."""
    CHROME = "chrome"
    FIREFOX = "firefox"
    SAFARI = "safari"
    EDGE = "edge"
    OPERA = "opera"


class WebAgentCapability(Enum):
    """Web agent capabilities."""
    DOM_MANIPULATION = "dom_manipulation"
    STORAGE_ACCESS = "storage_access"
    NETWORK_REQUESTS = "network_requests"
    WEBSOCKETS = "websockets"
    WEBGL = "webgl"
    MEDIA_ACCESS = "media_access"
    GEOLOCATION = "geolocation"
    NOTIFICATIONS = "notifications"
    OFFLINE_CAPABILITY = "offline_capability"


@dataclass
class WebAgentConfig:
    """Web agent configuration."""
    agent_type: WebAgentType
    entry_point: str  # Main JavaScript/WASM file
    dependencies: List[str] = field(default_factory=list)
    capabilities: List[WebAgentCapability] = field(default_factory=list)
    browser_compatibility: List[BrowserType] = field(default_factory=list)
    resource_limits: Dict[str, Any] = field(default_factory=dict)
    security_config: Dict[str, Any] = field(default_factory=dict)
    offline_config: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'agent_type': self.agent_type.value,
            'entry_point': self.entry_point,
            'dependencies': self.dependencies,
            'capabilities': [cap.value for cap in self.capabilities],
            'browser_compatibility': [browser.value for browser in self.browser_compatibility],
            'resource_limits': self.resource_limits,
            'security_config': self.security_config,
            'offline_config': self.offline_config
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WebAgentConfig':
        """Create from dictionary."""
        return cls(
            agent_type=WebAgentType(data['agent_type']),
            entry_point=data['entry_point'],
            dependencies=data.get('dependencies', []),
            capabilities=[WebAgentCapability(cap) for cap in data.get('capabilities', [])],
            browser_compatibility=[BrowserType(browser) for browser in data.get('browser_compatibility', [])],
            resource_limits=data.get('resource_limits', {}),
            security_config=data.get('security_config', {}),
            offline_config=data.get('offline_config', {})
        )


@dataclass
class WebAgentSession:
    """Web agent session information."""
    session_id: str
    deployment_id: str
    browser_info: Dict[str, Any]
    user_agent: str
    connection_info: Dict[str, Any]
    created_at: datetime
    last_activity: datetime
    state: str = "active"
    capabilities: List[WebAgentCapability] = field(default_factory=list)
    resources_used: Dict[str, Any] = field(default_factory=dict)

    def update_activity(self) -> None:
        """Update last activity timestamp."""
        self.last_activity = datetime.utcnow()

    def is_active(self, timeout: int = 300) -> bool:
        """Check if session is still active."""
        if self.state != "active":
            return False
        return (datetime.utcnow() - self.last_activity).total_seconds() < timeout

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'session_id': self.session_id,
            'deployment_id': self.deployment_id,
            'browser_info': self.browser_info,
            'user_agent': self.user_agent,
            'connection_info': self.connection_info,
            'created_at': self.created_at.isoformat(),
            'last_activity': self.last_activity.isoformat(),
            'state': self.state,
            'capabilities': [cap.value for cap in self.capabilities],
            'resources_used': self.resources_used
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WebAgentSession':
        """Create from dictionary."""
        session = cls(
            session_id=data['session_id'],
            deployment_id=data['deployment_id'],
            browser_info=data['browser_info'],
            user_agent=data['user_agent'],
            connection_info=data['connection_info'],
            created_at=datetime.fromisoformat(data['created_at']),
            last_activity=datetime.fromisoformat(data['last_activity']),
            state=data.get('state', 'active'),
            capabilities=[WebAgentCapability(cap) for cap in data.get('capabilities', [])],
            resources_used=data.get('resources_used', {})
        )
        return session


class WebAgentDeployer(BasePlatformDeployer):
    """Web agent deployer for browser environments."""

    def __init__(self, config: PlatformConfig):
        super().__init__(AgentPlatform.WEB, config)
        self.web_root = Path(config.runtime_path or "web_agents")
        self.sessions: Dict[str, WebAgentSession] = {}
        self.agent_manifests: Dict[str, Dict[str, Any]] = {}
        self.websocket_connections: Dict[str, Any] = {}  # Would be WebSocket connections
        self._session_cleanup_task = None

        # Ensure web root exists
        ensure_directory_exists(self.web_root)

    async def deploy_agent(self, deployment: AgentDeployment) -> DeploymentStatus:
        """Deploy web agent."""
        try:
            deployment.state = AgentState.DEPLOYING
            deployment.deployment_time = datetime.utcnow()

            # Parse web configuration
            web_config = WebAgentConfig.from_dict(
                deployment.platform_config.deployment_config.get('web_config', {})
            )

            # Generate web agent files
            await self._generate_web_agent_files(deployment, web_config)

            # Create agent manifest
            manifest = await self._create_agent_manifest(deployment, web_config)
            self.agent_manifests[deployment.deployment_id] = manifest

            deployment.state = AgentState.RUNNING
            deployment.status_message = "Web agent deployed successfully"
            deployment.network_endpoints.update({
                'web_root': str(self.web_root),
                'manifest': f"/agents/{deployment.deployment_id}/manifest.json",
                'websocket': f"/ws/agents/{deployment.deployment_id}"
            })

            await self.register_deployment(deployment)

            # Start session cleanup
            if not self._session_cleanup_task:
                self._session_cleanup_task = asyncio.create_task(self._session_cleanup_loop())

            self.logger.info(f"Deployed web agent {deployment.agent_id}")
            return DeploymentStatus.SUCCESS

        except Exception as e:
            deployment.state = AgentState.ERROR
            deployment.status_message = f"Web deployment failed: {str(e)}"
            self.logger.error(f"Failed to deploy web agent: {e}")
            return DeploymentStatus.FAILED

    async def stop_agent(self, deployment_id: str) -> DeploymentStatus:
        """Stop web agent."""
        try:
            if deployment_id in self.agent_manifests:
                # Remove agent files
                agent_dir = self.web_root / deployment_id
                if agent_dir.exists():
                    import shutil
                    shutil.rmtree(agent_dir)

                # Clean up sessions
                sessions_to_remove = [
                    session_id for session_id, session in self.sessions.items()
                    if session.deployment_id == deployment_id
                ]
                for session_id in sessions_to_remove:
                    del self.sessions[session_id]

                # Remove manifest
                del self.agent_manifests[deployment_id]

                deployment = self.get_deployment(deployment_id)
                if deployment:
                    deployment.state = AgentState.STOPPED
                    deployment.status_message = "Web agent stopped successfully"

                await self.unregister_deployment(deployment_id)
                self.logger.info(f"Stopped web agent {deployment_id}")
                return DeploymentStatus.SUCCESS

            return DeploymentStatus.FAILED

        except Exception as e:
            self.logger.error(f"Failed to stop web agent {deployment_id}: {e}")
            return DeploymentStatus.FAILED

    async def check_agent_health(self, deployment_id: str) -> bool:
        """Check if web agent is healthy."""
        try:
            # Check if agent has active sessions
            active_sessions = [
                session for session in self.sessions.values()
                if session.deployment_id == deployment_id and session.is_active()
            ]

            # Also check if agent files exist
            agent_dir = self.web_root / deployment_id
            files_exist = agent_dir.exists() and (agent_dir / "manifest.json").exists()

            return len(active_sessions) > 0 or files_exist

        except Exception as e:
            self.logger.error(f"Error checking web agent health: {e}")
            return False

    async def get_agent_metrics(self, deployment_id: str) -> Dict[str, Any]:
        """Get web agent metrics."""
        try:
            deployment = self.get_deployment(deployment_id)
            if not deployment:
                return {}

            # Get session metrics
            sessions = [
                session for session in self.sessions.values()
                if session.deployment_id == deployment_id
            ]

            active_sessions = [s for s in sessions if s.is_active()]
            total_sessions = len(sessions)

            # Calculate session duration
            session_durations = []
            for session in sessions:
                duration = (session.last_activity - session.created_at).total_seconds()
                session_durations.append(duration)

            avg_session_duration = sum(session_durations) / len(session_durations) if session_durations else 0

            # Resource usage
            total_memory = sum(session.resources_used.get('memory_mb', 0) for session in sessions)
            total_storage = sum(session.resources_used.get('storage_mb', 0) for session in sessions)

            return {
                'platform': 'web',
                'total_sessions': total_sessions,
                'active_sessions': len(active_sessions),
                'avg_session_duration': avg_session_duration,
                'total_memory_mb': total_memory,
                'total_storage_mb': total_storage,
                'supported_browsers': len(deployment.platform_config.deployment_config.get('web_config', {}).get('browser_compatibility', [])),
                'uptime': (datetime.utcnow() - deployment.deployment_time).total_seconds() if deployment.deployment_time else 0,
                'state': deployment.state.value
            }

        except Exception as e:
            self.logger.error(f"Error getting web agent metrics: {e}")
            return {}

    async def create_web_session(self,
                               deployment_id: str,
                               browser_info: Dict[str, Any],
                               user_agent: str,
                               connection_info: Dict[str, Any]) -> str:
        """Create new web agent session."""
        try:
            deployment = self.get_deployment(deployment_id)
            if not deployment or deployment.state != AgentState.RUNNING:
                raise ValueError(f"Agent {deployment_id} not available")

            session_id = f"session_{uuid.uuid4().hex[:12]}"
            web_config = WebAgentConfig.from_dict(
                deployment.platform_config.deployment_config.get('web_config', {})
            )

            session = WebAgentSession(
                session_id=session_id,
                deployment_id=deployment_id,
                browser_info=browser_info,
                user_agent=user_agent,
                connection_info=connection_info,
                created_at=datetime.utcnow(),
                last_activity=datetime.utcnow(),
                capabilities=web_config.capabilities
            )

            self.sessions[session_id] = session
            self.logger.info(f"Created web session {session_id} for agent {deployment_id}")
            return session_id

        except Exception as e:
            self.logger.error(f"Error creating web session: {e}")
            raise

    async def update_session_activity(self, session_id: str, activity_data: Dict[str, Any]) -> None:
        """Update session activity and resources."""
        try:
            session = self.sessions.get(session_id)
            if not session:
                return

            session.update_activity()
            session.resources_used.update(activity_data.get('resources_used', {}))

            # Update capabilities based on actual usage
            new_capabilities = activity_data.get('capabilities_used', [])
            for cap_name in new_capabilities:
                try:
                    cap = WebAgentCapability(cap_name)
                    if cap not in session.capabilities:
                        session.capabilities.append(cap)
                except ValueError:
                    pass

        except Exception as e:
            self.logger.error(f"Error updating session activity: {e}")

    async def close_session(self, session_id: str) -> None:
        """Close web session."""
        try:
            if session_id in self.sessions:
                session = self.sessions[session_id]
                session.state = "closed"
                self.logger.info(f"Closed web session {session_id}")

                # Remove after a delay
                await asyncio.sleep(60)  # Keep for 1 minute for metrics
                if session_id in self.sessions:
                    del self.sessions[session_id]

        except Exception as e:
            self.logger.error(f"Error closing web session: {e}")

    async def _generate_web_agent_files(self, deployment: AgentDeployment, web_config: WebAgentConfig) -> None:
        """Generate web agent files."""
        try:
            agent_dir = self.web_root / deployment.deployment_id
            ensure_directory_exists(agent_dir)

            # Generate entry point based on agent type
            if web_config.agent_type == WebAgentType.WASM:
                await self._generate_wasm_agent(deployment, agent_dir, web_config)
            elif web_config.agent_type == WebAgentType.JAVASCRIPT:
                await self._generate_javascript_agent(deployment, agent_dir, web_config)
            elif web_config.agent_type == WebAgentType.PWA:
                await self._generate_pwa_agent(deployment, agent_dir, web_config)
            elif web_config.agent_type == WebAgentType.WEB_WORKER:
                await self._generate_web_worker_agent(deployment, agent_dir, web_config)
            else:
                raise ValueError(f"Unsupported web agent type: {web_config.agent_type}")

            # Generate dependencies
            for dep in web_config.dependencies:
                await self._generate_dependency_file(agent_dir, dep)

            # Generate service worker if needed
            if WebAgentCapability.OFFLINE_CAPABILITY in web_config.capabilities:
                await self._generate_service_worker(deployment, agent_dir, web_config)

        except Exception as e:
            self.logger.error(f"Error generating web agent files: {e}")
            raise

    async def _generate_wasm_agent(self, deployment: AgentDeployment, agent_dir: Path, web_config: WebAgentConfig) -> None:
        """Generate WebAssembly agent files."""
        # In a real implementation, this would compile Python code to WASM
        # For now, generate placeholder files

        # WASM loader JavaScript
        wasm_loader = f'''
class {deployment.agent_class} {{
    constructor() {{
        this.initialized = false;
        this.capabilities = {json.dumps([cap.value for cap in web_config.capabilities])};
    }}

    async initialize() {{
        if (this.initialized) return;

        try {{
            // Load WASM module
            const wasmModule = await WebAssembly.compileStreaming(
                fetch('{web_config.entry_point}')
            );
            this.wasmInstance = await WebAssembly.instantiate(wasmModule);
            this.initialized = true;
        }} catch (error) {{
            console.error('Failed to initialize WASM agent:', error);
            throw error;
        }}
    }}

    async processMessage(message) {{
        if (!this.initialized) {{
            await this.initialize();
        }}

        // Process message through WASM
        const result = this.wasmInstance.exports.processMessage(
            JSON.stringify(message)
        );

        return JSON.parse(result);
    }}

    getCapabilities() {{
        return this.capabilities;
    }}
}}

// Export for use
window.{deployment.agent_class} = {deployment.agent_class};
'''

        with open(agent_dir / "agent.js", 'w') as f:
            f.write(wasm_loader)

        # Placeholder WASM file (in reality, this would be compiled)
        with open(agent_dir / web_config.entry_point, 'wb') as f:
            f.write(b'placeholder_wasm_content')

    async def _generate_javascript_agent(self, deployment: AgentDeployment, agent_dir: Path, web_config: WebAgentConfig) -> None:
        """Generate JavaScript agent files."""
        agent_code = f'''
class {deployment.agent_class} {{
    constructor(sessionId) {{
        this.sessionId = sessionId;
        this.initialized = false;
        this.capabilities = {json.dumps([cap.value for cap in web_config.capabilities])};
        this.messageHandlers = new Map();
    }}

    async initialize() {{
        if (this.initialized) return;

        try {{
            // Initialize WebSocket connection
            this.ws = new WebSocket('{deployment.network_endpoints.get('websocket', '')}');

            this.ws.onmessage = (event) => {{
                const message = JSON.parse(event.data);
                this.handleMessage(message);
            }};

            this.ws.onopen = () => {{
                this.initialized = true;
                console.log('WebSocket connected for session', this.sessionId);
            }};

            this.ws.onerror = (error) => {{
                console.error('WebSocket error:', error);
            }};

            this.ws.onclose = () => {{
                console.log('WebSocket closed for session', this.sessionId);
            }};
        }} catch (error) {{
            console.error('Failed to initialize JavaScript agent:', error);
            throw error;
        }}
    }}

    async processMessage(message) {{
        if (!this.initialized) {{
            await this.initialize();
        }}

        // Process message locally or send to backend
        if (this.canProcessLocally(message)) {{
            return await this.processLocally(message);
        }} else {{
            return await this.sendToBackend(message);
        }}
    }}

    canProcessLocally(message) {{
        // Check if message can be processed locally
        const type = message.type;
        return this.capabilities.includes(type);
    }}

    async processLocally(message) {{
        // Process message using local capabilities
        switch (message.type) {{
            case 'dom_manipulation':
                return await this.handleDomManipulation(message);
            case 'storage_access':
                return await this.handleStorageAccess(message);
            default:
                throw new Error(`Unsupported message type: ${{message.type}}`);
        }}
    }}

    async sendToBackend(message) {{
        return new Promise((resolve, reject) => {{
            const messageId = uuidv4();

            this.messageHandlers.set(messageId, {{ resolve, reject }});

            this.ws.send(JSON.stringify({{
                ...message,
                sessionId: this.sessionId,
                messageId: messageId
            }}));
        }});
    }}

    handleMessage(message) {{
        if (message.messageId && this.messageHandlers.has(message.messageId)) {{
            const handler = this.messageHandlers.get(message.messageId);
            this.messageHandlers.delete(message.messageId);

            if (message.error) {{
                handler.reject(new Error(message.error));
            }} else {{
                handler.resolve(message.result);
            }}
        }}
    }}

    getCapabilities() {{
        return this.capabilities;
    }}
}}

// UUID generation helper
function uuidv4() {{
    return ([1e7]+-1e3+-4e3+-8e3+-1e11).replace(/[018]/g, c =>
        (c ^ crypto.getRandomValues(new Uint8Array(1))[0] & 15 >> c / 4).toString(16)
    );
}}

// Export for use
window.{deployment.agent_class} = {deployment.agent_class};
'''

        with open(agent_dir / web_config.entry_point, 'w') as f:
            f.write(agent_code)

    async def _generate_pwa_agent(self, deployment: AgentDeployment, agent_dir: Path, web_config: WebAgentConfig) -> None:
        """Generate Progressive Web App agent files."""
        # Generate PWA manifest
        pwa_manifest = f'''
{{
  "name": "{deployment.agent_class}",
  "short_name": "{deployment.agent_class}",
  "description": "DuckBot Web Agent",
  "start_url": "/agents/{deployment.deployment_id}/",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#007bff",
  "icons": [
    {{
      "src": "icon-192.png",
      "sizes": "192x192",
      "type": "image/png"
    }},
    {{
      "src": "icon-512.png",
      "sizes": "512x512",
      "type": "image/png"
    }}
  ],
  "capabilities": {json.dumps([cap.value for cap in web_config.capabilities])}
}}
'''

        with open(agent_dir / "manifest.json", 'w') as f:
            f.write(pwa_manifest)

        # Generate main HTML file
        html_content = f'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{deployment.agent_class}</title>
    <link rel="manifest" href="manifest.json">
    <script src="{web_config.entry_point}"></script>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .container {{ max-width: 800px; margin: 0 auto; }}
        .status {{ padding: 10px; margin: 10px 0; border-radius: 5px; }}
        .status.success {{ background-color: #d4edda; color: #155724; }}
        .status.error {{ background-color: #f8d7da; color: #721c24; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{deployment.agent_class}</h1>
        <div id="status" class="status">Initializing...</div>
        <div id="output"></div>
    </div>

    <script>
        async function initializeAgent() {{
            try {{
                const agent = new {deployment.agent_class}('session_' + Math.random().toString(36).substr(2, 9));
                await agent.initialize();

                document.getElementById('status').textContent = 'Agent initialized successfully';
                document.getElementById('status').className = 'status success';

                console.log('Agent capabilities:', agent.getCapabilities());
            }} catch (error) {{
                document.getElementById('status').textContent = 'Error: ' + error.message;
                document.getElementById('status').className = 'status error';
                console.error('Agent initialization failed:', error);
            }}
        }}

        // Initialize when page loads
        window.addEventListener('load', initializeAgent);
    </script>
</body>
</html>
'''

        with open(agent_dir / "index.html", 'w') as f:
            f.write(html_content)

        # Generate JavaScript agent
        await self._generate_javascript_agent(deployment, agent_dir, web_config)

    async def _generate_web_worker_agent(self, deployment: AgentDeployment, agent_dir: Path, web_config: WebAgentConfig) -> None:
        """Generate Web Worker agent files."""
        # Main thread code
        main_code = f'''
class {deployment.agent_class} {{
    constructor() {{
        this.worker = null;
        this.initialized = false;
        this.messageHandlers = new Map();
    }}

    async initialize() {{
        if (this.initialized) return;

        try {{
            this.worker = new Worker('{web_config.entry_point}');

            this.worker.onmessage = (event) => {{
                const message = event.data;
                this.handleWorkerMessage(message);
            }};

            this.worker.onerror = (error) => {{
                console.error('Worker error:', error);
            }};

            // Initialize worker
            this.worker.postMessage({{ type: 'initialize' }});

            this.initialized = true;
        }} catch (error) {{
            console.error('Failed to initialize Web Worker agent:', error);
            throw error;
        }}
    }}

    async processMessage(message) {{
        if (!this.initialized) {{
            await this.initialize();
        }}

        return new Promise((resolve, reject) => {{
            const messageId = Date.now().toString();

            this.messageHandlers.set(messageId, {{ resolve, reject }});

            this.worker.postMessage({{
                ...message,
                messageId: messageId
            }});
        }});
    }}

    handleWorkerMessage(message) {{
        if (message.messageId && this.messageHandlers.has(message.messageId)) {{
            const handler = this.messageHandlers.get(message.messageId);
            this.messageHandlers.delete(message.messageId);

            if (message.error) {{
                handler.reject(new Error(message.error));
            }} else {{
                handler.resolve(message.result);
            }}
        }}
    }}

    getCapabilities() {{
        return ['dom_manipulation', 'storage_access', 'network_requests'];
    }}
}}

window.{deployment.agent_class} = {deployment.agent_class};
'''

        with open(agent_dir / "agent.js", 'w') as f:
            f.write(main_code)

        # Worker code
        worker_code = f'''
// Worker code for {deployment.agent_class}
let initialized = false;

self.onmessage = function(event) {{
    const message = event.data;

    if (message.type === 'initialize') {{
        initialize();
    }} else if (message.messageId) {{
        processMessage(message);
    }}
}};

function initialize() {{
    initialized = true;
    self.postMessage({{ type: 'initialized' }});
}}

async function processMessage(message) {{
    try {{
        let result;

        switch (message.type) {{
            case 'computation':
                result = await handleComputation(message.data);
                break;
            case 'data_processing':
                result = await handleDataProcessing(message.data);
                break;
            default:
                throw new Error(`Unsupported message type: ${{message.type}}`);
        }}

        self.postMessage({{
            messageId: message.messageId,
            result: result
        }});
    }} catch (error) {{
        self.postMessage({{
            messageId: message.messageId,
            error: error.message
        }});
    }}
}}

async function handleComputation(data) {{
    // Perform CPU-intensive computation
    // This runs in a separate thread
    return {{ computed: true, data: data }};
}}

async function handleDataProcessing(data) {{
    // Process data without blocking main thread
    return {{ processed: true, data: data }};
}}
'''

        with open(agent_dir / web_config.entry_point, 'w') as f:
            f.write(worker_code)

    async def _generate_service_worker(self, deployment: AgentDeployment, agent_dir: Path, web_config: WebAgentConfig) -> None:
        """Generate Service Worker for offline capability."""
        sw_code = f'''
const CACHE_NAME = '{deployment.deployment_id}-v1';
const urlsToCache = [
    '/agents/{deployment.deployment_id}/',
    '/agents/{deployment.deployment_id}/index.html',
    '/agents/{deployment.deployment_id}/agent.js',
    '/agents/{deployment.deployment_id}/manifest.json'
];

self.addEventListener('install', event => {{
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => cache.addAll(urlsToCache))
    );
}});

self.addEventListener('fetch', event => {{
    event.respondWith(
        caches.match(event.request)
            .then(response => {{
                return response || fetch(event.request);
            }})
    );
}});

self.addEventListener('activate', event => {{
    event.waitUntil(
        caches.keys().then(cacheNames => {{
            return Promise.all(
                cacheNames.filter(cacheName => {{
                    return cacheName.startsWith('{deployment.deployment_id}-') &&
                           cacheName !== CACHE_NAME;
                }}).map(cacheName => {{
                    return caches.delete(cacheName);
                }})
            );
        }})
    );
}});
'''

        with open(agent_dir / "sw.js", 'w') as f:
            f.write(sw_code)

    async def _generate_dependency_file(self, agent_dir: Path, dependency: str) -> None:
        """Generate dependency file."""
        # In a real implementation, this would copy actual dependency files
        # For now, create placeholder files
        dep_path = agent_dir / dependency
        ensure_directory_exists(dep_path.parent)

        if dependency.endswith('.js'):
            with open(dep_path, 'w') as f:
                f.write(f'// Dependency: {dependency}\n// Generated for DuckBot web agent\n')
        elif dependency.endswith('.css'):
            with open(dep_path, 'w') as f:
                f.write(f'/* Dependency: {dependency} */\n/* Generated for DuckBot web agent */\n')

    async def _create_agent_manifest(self, deployment: AgentDeployment, web_config: WebAgentConfig) -> Dict[str, Any]:
        """Create agent manifest."""
        manifest = {
            'deployment_id': deployment.deployment_id,
            'agent_id': deployment.agent_id,
            'agent_class': deployment.agent_class,
            'agent_type': web_config.agent_type.value,
            'entry_point': web_config.entry_point,
            'dependencies': web_config.dependencies,
            'capabilities': [cap.value for cap in web_config.capabilities],
            'browser_compatibility': [browser.value for browser in web_config.browser_compatibility],
            'resource_limits': web_config.resource_limits,
            'security_config': web_config.security_config,
            'offline_config': web_config.offline_config,
            'endpoints': deployment.network_endpoints,
            'created_at': deployment.deployment_time.isoformat(),
            'version': '1.0.0'
        }

        with open(self.web_root / deployment.deployment_id / "agent_manifest.json", 'w') as f:
            json.dump(manifest, f, indent=2)

        return manifest

    async def _session_cleanup_loop(self) -> None:
        """Clean up inactive sessions."""
        while True:
            try:
                current_time = datetime.utcnow()
                sessions_to_remove = []

                for session_id, session in self.sessions.items():
                    if not session.is_active(timeout=300):  # 5 minutes timeout
                        sessions_to_remove.append(session_id)

                for session_id in sessions_to_remove:
                    await self.close_session(session_id)

                await asyncio.sleep(60)  # Check every minute

            except Exception as e:
                self.logger.error(f"Error in session cleanup loop: {e}")
                await asyncio.sleep(60)


class WebAgentFramework:
    """Main web agent framework."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.deployer: Optional[WebAgentDeployer] = None
        self._running = False

    async def start(self) -> None:
        """Start the web agent framework."""
        config = PlatformConfig(
            AgentPlatform.WEB,
            "web_agents",
            network_config={'port': 8080}
        )
        self.deployer = WebAgentDeployer(config)
        self._running = True
        self.logger.info("Web agent framework started")

    async def stop(self) -> None:
        """Stop the web agent framework."""
        self._running = False
        self.logger.info("Web agent framework stopped")

    async def deploy_web_agent(self,
                              agent_class: str,
                              web_config: WebAgentConfig,
                              agent_id: Optional[str] = None) -> str:
        """Deploy web agent."""
        if not self.deployer:
            raise RuntimeError("Web agent framework not started")

        deployment_id = agent_id or f"{agent_class}_{uuid.uuid4().hex[:8]}"

        platform_config = PlatformConfig(
            AgentPlatform.WEB,
            "web_agents",
            deployment_config={'web_config': web_config.to_dict()}
        )

        deployment = AgentDeployment(
            deployment_id=deployment_id,
            agent_id=agent_id or agent_class,
            agent_class=agent_class,
            platform=AgentPlatform.WEB,
            platform_config=platform_config
        )

        status = await self.deployer.deploy_agent(deployment)

        if status == DeploymentStatus.SUCCESS:
            return deployment_id
        else:
            raise RuntimeError(f"Web deployment failed: {deployment.status_message}")

    async def create_web_session(self,
                               deployment_id: str,
                               browser_info: Dict[str, Any],
                               user_agent: str,
                               connection_info: Dict[str, Any]) -> str:
        """Create web session for agent."""
        if not self.deployer:
            raise RuntimeError("Web agent framework not started")

        return await self.deployer.create_web_session(
            deployment_id, browser_info, user_agent, connection_info
        )

    async def get_web_agent_status(self, deployment_id: str) -> Optional[Dict[str, Any]]:
        """Get web agent status."""
        if not self.deployer:
            return None

        deployment = self.deployer.get_deployment(deployment_id)
        if not deployment:
            return None

        metrics = await self.deployer.get_agent_metrics(deployment_id)
        health = await self.deployer.check_agent_health(deployment_id)

        return {
            'deployment': deployment.to_dict(),
            'metrics': metrics,
            'healthy': health,
            'platform': deployment.platform.value
        }

    def get_framework_summary(self) -> Dict[str, Any]:
        """Get web framework summary."""
        if not self.deployer:
            return {}

        return {
            'total_deployments': len(self.deployer._running_deployments),
            'total_sessions': len(self.deployer.sessions),
            'active_sessions': len([s for s in self.deployer.sessions.values() if s.is_active()]),
            'web_root': str(self.deployer.web_root)
        }


# Global instance
_web_framework = None


def get_web_framework() -> WebAgentFramework:
    """Get global web framework instance."""
    global _web_framework
    if _web_framework is None:
        _web_framework = WebAgentFramework()
    return _web_framework


# Example usage
async def example_web_deployment():
    """Example of web agent deployment."""
    framework = get_web_framework()
    await framework.start()

    try:
        # Deploy JavaScript web agent
        web_config = WebAgentConfig(
            agent_type=WebAgentType.JAVASCRIPT,
            entry_point="agent.js",
            dependencies=["utils.js", "styles.css"],
            capabilities=[
                WebAgentCapability.DOM_MANIPULATION,
                WebAgentCapability.STORAGE_ACCESS,
                WebAgentCapability.NETWORK_REQUESTS,
                WebAgentCapability.WEBSOCKETS
            ],
            browser_compatibility=[BrowserType.CHROME, BrowserType.FIREFOX, BrowserType.EDGE],
            resource_limits={
                'max_memory_mb': 512,
                'max_storage_mb': 100
            }
        )

        deployment_id = await framework.deploy_web_agent('WebAssistantAgent', web_config)
        print(f"Deployed web agent: {deployment_id}")

        # Create session
        browser_info = {
            'name': 'Chrome',
            'version': '120.0.0',
            'platform': 'Windows'
        }

        session_id = await framework.create_web_session(
            deployment_id,
            browser_info,
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            {'ip': '127.0.0.1', 'user_agent': 'DuckBot Test'}
        )

        print(f"Created web session: {session_id}")

        # Check status
        status = await framework.get_web_agent_status(deployment_id)
        print(f"Web agent status: {status}")

    finally:
        await framework.stop()


if __name__ == "__main__":
    asyncio.run(example_web_deployment())