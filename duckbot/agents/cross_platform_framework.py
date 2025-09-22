"""
Cross-Platform Agent Deployment Framework for DuckBot v4.2

Based on Google AP2 patterns for multi-platform agent deployment and coordination.
Implements Python scenarios for backend agents, Web scenarios for browser agents,
and consistent type systems across platforms.

Architecture:
- CrossPlatformAgentFramework: Main deployment coordinator
- PythonAgentFramework: Backend agent deployment
- WebAgentFramework: Browser-based agent deployment
- DesktopAgentFramework: Native desktop agent deployment
- MobileAgentFramework: Mobile agent deployment (Android/iOS)
"""

import asyncio
import json
import logging
import os
import platform
import subprocess
import sys
import time
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Type, Union
import uuid
import inspect
from concurrent.futures import ThreadPoolExecutor, as_completed

# DuckBot imports
from duckbot.core.logging_setup import setup_logging
from duckbot.core.agent_framework import UnifiedAgentFramework, AgentTask
from duckbot.agents.enhanced_coordinator import EnhancedAgentCoordinator, BaseEnhancedAgent
from duckbot.core.utilities import (
    get_system_info,
    ensure_directory_exists,
    run_command_async,
    safe_execute
)

logger = setup_logging(__name__)


class AgentPlatform(Enum):
    """Supported deployment platforms for agents."""
    PYTHON = "python"
    WEB = "web"
    DESKTOP = "desktop"
    MOBILE = "mobile"
    DOCKER = "docker"
    WSL = "wsl"


class AgentState(Enum):
    """Agent deployment states."""
    PENDING = "pending"
    DEPLOYING = "deploying"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"
    TERMINATED = "terminated"


class DeploymentStatus(Enum):
    """Deployment operation status."""
    SUCCESS = "success"
    FAILED = "failed"
    IN_PROGRESS = "in_progress"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


@dataclass
class PlatformConfig:
    """Platform-specific configuration."""
    platform: AgentPlatform
    runtime_path: str
    environment_vars: Dict[str, str] = field(default_factory=dict)
    resource_limits: Dict[str, Any] = field(default_factory=dict)
    network_config: Dict[str, Any] = field(default_factory=dict)
    storage_config: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'platform': self.platform.value,
            'runtime_path': self.runtime_path,
            'environment_vars': self.environment_vars,
            'resource_limits': self.resource_limits,
            'network_config': self.network_config,
            'storage_config': self.storage_config
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PlatformConfig':
        """Create from dictionary."""
        return cls(
            platform=AgentPlatform(data['platform']),
            runtime_path=data['runtime_path'],
            environment_vars=data.get('environment_vars', {}),
            resource_limits=data.get('resource_limits', {}),
            network_config=data.get('network_config', {}),
            storage_config=data.get('storage_config', {})
        )


@dataclass
class AgentDeployment:
    """Agent deployment record."""
    deployment_id: str
    agent_id: str
    agent_class: str
    platform: AgentPlatform
    platform_config: PlatformConfig
    state: AgentState = AgentState.PENDING
    status_message: str = ""
    deployment_time: Optional[datetime] = None
    last_heartbeat: Optional[datetime] = None
    resource_usage: Dict[str, Any] = field(default_factory=dict)
    network_endpoints: Dict[str, str] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)

    def update_heartbeat(self) -> None:
        """Update agent heartbeat timestamp."""
        self.last_heartbeat = datetime.utcnow()

    def is_alive(self, timeout: int = 300) -> bool:
        """Check if agent is still alive based on heartbeat."""
        if not self.last_heartbeat:
            return False
        return (datetime.utcnow() - self.last_heartbeat).total_seconds() < timeout

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'deployment_id': self.deployment_id,
            'agent_id': self.agent_id,
            'agent_class': self.agent_class,
            'platform': self.platform.value,
            'platform_config': self.platform_config.to_dict(),
            'state': self.state.value,
            'status_message': self.status_message,
            'deployment_time': self.deployment_time.isoformat() if self.deployment_time else None,
            'last_heartbeat': self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            'resource_usage': self.resource_usage,
            'network_endpoints': self.network_endpoints,
            'dependencies': self.dependencies
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentDeployment':
        """Create from dictionary."""
        deployment = cls(
            deployment_id=data['deployment_id'],
            agent_id=data['agent_id'],
            agent_class=data['agent_class'],
            platform=AgentPlatform(data['platform']),
            platform_config=PlatformConfig.from_dict(data['platform_config']),
            state=AgentState(data.get('state', 'pending')),
            status_message=data.get('status_message', ''),
            resource_usage=data.get('resource_usage', {}),
            network_endpoints=data.get('network_endpoints', {}),
            dependencies=data.get('dependencies', [])
        )

        if data.get('deployment_time'):
            deployment.deployment_time = datetime.fromisoformat(data['deployment_time'])
        if data.get('last_heartbeat'):
            deployment.last_heartbeat = datetime.fromisoformat(data['last_heartbeat'])

        return deployment


class BasePlatformDeployer(ABC):
    """Abstract base class for platform-specific deployers."""

    def __init__(self, platform: AgentPlatform, config: PlatformConfig):
        self.platform = platform
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{platform.value}")
        self._running_deployments: Dict[str, AgentDeployment] = {}

    @abstractmethod
    async def deploy_agent(self, deployment: AgentDeployment) -> DeploymentStatus:
        """Deploy agent to platform."""
        pass

    @abstractmethod
    async def stop_agent(self, deployment_id: str) -> DeploymentStatus:
        """Stop deployed agent."""
        pass

    @abstractmethod
    async def check_agent_health(self, deployment_id: str) -> bool:
        """Check if agent is healthy."""
        pass

    @abstractmethod
    async def get_agent_metrics(self, deployment_id: str) -> Dict[str, Any]:
        """Get agent performance metrics."""
        pass

    async def register_deployment(self, deployment: AgentDeployment) -> None:
        """Register deployment with deployer."""
        self._running_deployments[deployment.deployment_id] = deployment
        self.logger.info(f"Registered deployment {deployment.deployment_id} for agent {deployment.agent_id}")

    async def unregister_deployment(self, deployment_id: str) -> None:
        """Unregister deployment from deployer."""
        if deployment_id in self._running_deployments:
            del self._running_deployments[deployment_id]
            self.logger.info(f"Unregistered deployment {deployment_id}")

    def get_deployment(self, deployment_id: str) -> Optional[AgentDeployment]:
        """Get deployment by ID."""
        return self._running_deployments.get(deployment_id)

    def list_deployments(self) -> List[AgentDeployment]:
        """List all running deployments."""
        return list(self._running_deployments.values())


class PythonAgentDeployer(BasePlatformDeployer):
    """Deployer for Python-based agents."""

    def __init__(self, config: PlatformConfig):
        super().__init__(AgentPlatform.PYTHON, config)
        self.process_manager: Dict[str, subprocess.Popen] = {}
        self.executor = ThreadPoolExecutor(max_workers=10)

    async def deploy_agent(self, deployment: AgentDeployment) -> DeploymentStatus:
        """Deploy Python agent as subprocess."""
        try:
            deployment.state = AgentState.DEPLOYING
            deployment.deployment_time = datetime.utcnow()

            # Prepare Python environment
            python_path = self.config.runtime_path or sys.executable
            env = os.environ.copy()
            env.update(self.config.environment_vars)

            # Create agent deployment script
            script_content = self._create_deployment_script(deployment)
            script_path = f"/tmp/agent_{deployment.deployment_id}.py"

            with open(script_path, 'w') as f:
                f.write(script_content)

            # Start agent process
            process = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                lambda: subprocess.Popen(
                    [python_path, script_path],
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
            )

            self.process_manager[deployment.deployment_id] = process
            deployment.state = AgentState.RUNNING
            deployment.status_message = "Agent deployed successfully"
            deployment.network_endpoints['stdin'] = f"pipe://{deployment.deployment_id}"

            await self.register_deployment(deployment)

            # Start monitoring thread
            asyncio.create_task(self._monitor_process(deployment.deployment_id))

            self.logger.info(f"Deployed Python agent {deployment.agent_id} with PID {process.pid}")
            return DeploymentStatus.SUCCESS

        except Exception as e:
            deployment.state = AgentState.ERROR
            deployment.status_message = f"Deployment failed: {str(e)}"
            self.logger.error(f"Failed to deploy Python agent {deployment.agent_id}: {e}")
            return DeploymentStatus.FAILED

    async def stop_agent(self, deployment_id: str) -> DeploymentStatus:
        """Stop Python agent process."""
        try:
            if deployment_id in self.process_manager:
                process = self.process_manager[deployment_id]
                process.terminate()

                # Wait for graceful shutdown
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()

                del self.process_manager[deployment_id]

                if deployment_id in self._running_deployments:
                    deployment = self._running_deployments[deployment_id]
                    deployment.state = AgentState.STOPPED
                    deployment.status_message = "Agent stopped successfully"

                await self.unregister_deployment(deployment_id)
                self.logger.info(f"Stopped Python agent deployment {deployment_id}")
                return DeploymentStatus.SUCCESS

            return DeploymentStatus.FAILED

        except Exception as e:
            self.logger.error(f"Failed to stop Python agent {deployment_id}: {e}")
            return DeploymentStatus.FAILED

    async def check_agent_health(self, deployment_id: str) -> bool:
        """Check if Python agent process is healthy."""
        if deployment_id in self.process_manager:
            process = self.process_manager[deployment_id]
            return process.poll() is None
        return False

    async def get_agent_metrics(self, deployment_id: str) -> Dict[str, Any]:
        """Get Python agent metrics."""
        if deployment_id not in self.process_manager:
            return {}

        process = self.process_manager[deployment_id]
        deployment = self.get_deployment(deployment_id)

        return {
            'pid': process.pid,
            'returncode': process.returncode,
            'state': deployment.state.value if deployment else 'unknown',
            'uptime': (datetime.utcnow() - deployment.deployment_time).total_seconds() if deployment and deployment.deployment_time else 0,
            'platform': 'python',
            'memory_usage': 'N/A'  # Would require psutil for actual memory usage
        }

    def _create_deployment_script(self, deployment: AgentDeployment) -> str:
        """Create Python script for agent deployment."""
        return f'''
import asyncio
import sys
import json
import time
from datetime import datetime

# DuckBot imports
sys.path.insert(0, "{os.getcwd()}")
from duckbot.agents.intelligent_agents import {deployment.agent_class}

async def run_agent():
    """Run the deployed agent."""
    try:
        # Initialize agent
        agent_class = getattr(__import__('duckbot.agents.intelligent_agents'), '{deployment.agent_class}')
        agent = agent_class()

        # Start agent
        await agent.start_interactive_mode()

    except Exception as e:
        print(f"Agent error: {{e}}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    print(f"Starting agent {{'{deployment.agent_id}'}} at {{datetime.utcnow()}}")
    asyncio.run(run_agent())
'''

    async def _monitor_process(self, deployment_id: str) -> None:
        """Monitor agent process and update state."""
        while deployment_id in self.process_manager:
            process = self.process_manager[deployment_id]

            if process.poll() is not None:
                # Process terminated
                deployment = self.get_deployment(deployment_id)
                if deployment:
                    deployment.state = AgentState.STOPPED
                    deployment.status_message = f"Process terminated with code {process.returncode}"

                await self.unregister_deployment(deployment_id)
                del self.process_manager[deployment_id]
                break

            # Update heartbeat
            deployment = self.get_deployment(deployment_id)
            if deployment:
                deployment.update_heartbeat()

            await asyncio.sleep(5)


class WebAgentDeployer(BasePlatformDeployer):
    """Deployer for web-based agents."""

    def __init__(self, config: PlatformConfig):
        super().__init__(AgentPlatform.WEB, config)
        self.web_server_port = config.network_config.get('port', 8080)
        self.web_agents: Dict[str, Dict[str, Any]] = {}

    async def deploy_agent(self, deployment: AgentDeployment) -> DeploymentStatus:
        """Deploy web agent."""
        try:
            deployment.state = AgentState.DEPLOYING
            deployment.deployment_time = datetime.utcnow()

            # Create web agent configuration
            web_config = {
                'agent_id': deployment.agent_id,
                'agent_class': deployment.agent_class,
                'platform_config': deployment.platform_config.to_dict(),
                'deployment_id': deployment.deployment_id,
                'endpoints': self._generate_web_endpoints(deployment)
            }

            self.web_agents[deployment.deployment_id] = web_config
            deployment.state = AgentState.RUNNING
            deployment.status_message = "Web agent deployed successfully"
            deployment.network_endpoints = web_config['endpoints']

            await self.register_deployment(deployment)

            self.logger.info(f"Deployed web agent {deployment.agent_id}")
            return DeploymentStatus.SUCCESS

        except Exception as e:
            deployment.state = AgentState.ERROR
            deployment.status_message = f"Web deployment failed: {str(e)}"
            self.logger.error(f"Failed to deploy web agent {deployment.agent_id}: {e}")
            return DeploymentStatus.FAILED

    async def stop_agent(self, deployment_id: str) -> DeploymentStatus:
        """Stop web agent."""
        try:
            if deployment_id in self.web_agents:
                del self.web_agents[deployment_id]

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
        return deployment_id in self.web_agents

    async def get_agent_metrics(self, deployment_id: str) -> Dict[str, Any]:
        """Get web agent metrics."""
        if deployment_id not in self.web_agents:
            return {}

        web_config = self.web_agents[deployment_id]
        deployment = self.get_deployment(deployment_id)

        return {
            'platform': 'web',
            'endpoints': web_config.get('endpoints', {}),
            'state': deployment.state.value if deployment else 'unknown',
            'uptime': (datetime.utcnow() - deployment.deployment_time).total_seconds() if deployment and deployment.deployment_time else 0,
            'request_count': web_config.get('metrics', {}).get('request_count', 0),
            'avg_response_time': web_config.get('metrics', {}).get('avg_response_time', 0)
        }

    def _generate_web_endpoints(self, deployment: AgentDeployment) -> Dict[str, str]:
        """Generate web endpoints for agent."""
        base_url = f"http://localhost:{self.web_server_port}"
        return {
            'api': f"{base_url}/api/agents/{deployment.agent_id}",
            'websocket': f"ws://localhost:{self.web_server_port}/ws/agents/{deployment.agent_id}",
            'health': f"{base_url}/health/agents/{deployment.agent_id}",
            'metrics': f"{base_url}/metrics/agents/{deployment.agent_id}"
        }


class CrossPlatformAgentFramework:
    """Main cross-platform agent deployment framework."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.deployers: Dict[AgentPlatform, BasePlatformDeployer] = {}
        self.deployments: Dict[str, AgentDeployment] = {}
        self.agent_registry: Dict[str, Type[BaseEnhancedAgent]] = {}
        self.platform_configs: Dict[AgentPlatform, PlatformConfig] = {}
        self.coordinator = EnhancedAgentCoordinator()
        self.task_queue = asyncio.Queue()
        self.health_check_interval = 30
        self._running = False
        self._health_monitor_task = None

        # Initialize deployers
        self._initialize_deployers()
        self._load_platform_configs()

    def _initialize_deployers(self) -> None:
        """Initialize platform deployers."""
        try:
            # Python deployer
            python_config = self.platform_configs.get(AgentPlatform.PYTHON,
                PlatformConfig(AgentPlatform.PYTHON, sys.executable))
            self.deployers[AgentPlatform.PYTHON] = PythonAgentDeployer(python_config)

            # Web deployer
            web_config = self.platform_configs.get(AgentPlatform.WEB,
                PlatformConfig(AgentPlatform.WEB, "localhost",
                             network_config={'port': 8080}))
            self.deployers[AgentPlatform.WEB] = WebAgentDeployer(web_config)

            self.logger.info("Initialized platform deployers")

        except Exception as e:
            self.logger.error(f"Failed to initialize deployers: {e}")

    def _load_platform_configs(self) -> None:
        """Load platform configurations."""
        # Default configurations
        self.platform_configs[AgentPlatform.PYTHON] = PlatformConfig(
            AgentPlatform.PYTHON,
            sys.executable,
            environment_vars={
                'PYTHONPATH': os.getcwd(),
                'DUCKBOT_ENV': 'production'
            },
            resource_limits={
                'max_memory': '1GB',
                'max_cpu_time': 300
            }
        )

        self.platform_configs[AgentPlatform.WEB] = PlatformConfig(
            AgentPlatform.WEB,
            "localhost",
            network_config={
                'port': 8080,
                'host': '0.0.0.0'
            },
            environment_vars={
                'FLASK_ENV': 'production'
            }
        )

        self.platform_configs[AgentPlatform.DESKTOP] = PlatformConfig(
            AgentPlatform.DESKTOP,
            os.getcwd(),
            environment_vars={
                'DISPLAY': ':0'
            }
        )

        self.platform_configs[AgentPlatform.MOBILE] = PlatformConfig(
            AgentPlatform.MOBILE,
            "mobile_runtime",
            network_config={
                'port': 9090
            }
        )

        self.platform_configs[AgentPlatform.DOCKER] = PlatformConfig(
            AgentPlatform.DOCKER,
            "docker",
            environment_vars={
                'DOCKER_HOST': 'unix:///var/run/docker.sock'
            }
        )

        self.platform_configs[AgentPlatform.WSL] = PlatformConfig(
            AgentPlatform.WSL,
            "/mnt/c/Users/Ryan/Desktop/DuckBot-Consolidated-v4.2",
            environment_vars={
                'WSL_DISTRO_NAME': 'Ubuntu'
            }
        )

    async def start(self) -> None:
        """Start the cross-platform framework."""
        self._running = True
        self._health_monitor_task = asyncio.create_task(self._health_monitor())
        self.logger.info("Cross-platform agent framework started")

    async def stop(self) -> None:
        """Stop the cross-platform framework."""
        self._running = False

        # Stop all deployments
        for deployment_id in list(self.deployments.keys()):
            await self.stop_agent(deployment_id)

        # Stop health monitor
        if self._health_monitor_task:
            self._health_monitor_task.cancel()
            try:
                await self._health_monitor_task
            except asyncio.CancelledError:
                pass

        self.logger.info("Cross-platform agent framework stopped")

    async def deploy_agent(self,
                          agent_class: str,
                          platform: AgentPlatform,
                          platform_config: Optional[PlatformConfig] = None,
                          agent_id: Optional[str] = None) -> str:
        """Deploy agent to specified platform."""
        try:
            # Generate deployment ID
            deployment_id = agent_id or f"{agent_class}_{uuid.uuid4().hex[:8]}"

            # Validate platform
            if platform not in self.deployers:
                raise ValueError(f"Unsupported platform: {platform}")

            # Use provided config or default
            config = platform_config or self.platform_configs[platform]

            # Create deployment record
            deployment = AgentDeployment(
                deployment_id=deployment_id,
                agent_id=agent_id or agent_class,
                agent_class=agent_class,
                platform=platform,
                platform_config=config
            )

            # Deploy to platform
            deployer = self.deployers[platform]
            status = await deployer.deploy_agent(deployment)

            if status == DeploymentStatus.SUCCESS:
                self.deployments[deployment_id] = deployment
                self.logger.info(f"Successfully deployed agent {agent_class} to {platform.value}")
                return deployment_id
            else:
                self.logger.error(f"Failed to deploy agent {agent_class} to {platform.value}")
                raise RuntimeError(f"Deployment failed: {deployment.status_message}")

        except Exception as e:
            self.logger.error(f"Error deploying agent {agent_class} to {platform.value}: {e}")
            raise

    async def stop_agent(self, deployment_id: str) -> bool:
        """Stop deployed agent."""
        try:
            deployment = self.deployments.get(deployment_id)
            if not deployment:
                self.logger.warning(f"Deployment {deployment_id} not found")
                return False

            deployer = self.deployers.get(deployment.platform)
            if not deployer:
                self.logger.error(f"No deployer for platform {deployment.platform}")
                return False

            status = await deployer.stop_agent(deployment_id)

            if status == DeploymentStatus.SUCCESS:
                del self.deployments[deployment_id]
                self.logger.info(f"Stopped agent deployment {deployment_id}")
                return True
            else:
                self.logger.error(f"Failed to stop agent deployment {deployment_id}")
                return False

        except Exception as e:
            self.logger.error(f"Error stopping agent {deployment_id}: {e}")
            return False

    async def coordinate_cross_platform_agents(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate agents across different platforms for a task."""
        try:
            # Create coordination task
            coordination_id = f"coord_{uuid.uuid4().hex[:8]}"

            # Analyze task requirements
            required_capabilities = self._analyze_task_requirements(task)

            # Find suitable agents across platforms
            suitable_agents = await self._find_suitable_agents(required_capabilities)

            # Deploy additional agents if needed
            for agent_spec in suitable_agents.get('needed_deployments', []):
                await self.deploy_agent(
                    agent_spec['class'],
                    agent_spec['platform'],
                    agent_spec.get('config')
                )

            # Coordinate task execution
            result = await self.coordinator.coordinate_agents(task)

            return {
                'coordination_id': coordination_id,
                'task': task,
                'result': result,
                'agents_involved': suitable_agents.get('agents', []),
                'platforms_used': list(set(d.platform.value for d in self.deployments.values())),
                'execution_time': time.time()
            }

        except Exception as e:
            self.logger.error(f"Error coordinating cross-platform agents: {e}")
            return {
                'error': str(e),
                'task': task,
                'coordination_id': coordination_id
            }

    def _analyze_task_requirements(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze task to determine required capabilities."""
        requirements = {
            'capabilities': [],
            'platforms': [],
            'resources': {},
            'complexity': 'medium'
        }

        # Analyze task type
        task_type = task.get('type', 'general')

        if task_type == 'desktop_automation':
            requirements['capabilities'].extend(['ui_automation', 'screenshot_analysis'])
            requirements['platforms'].extend([AgentPlatform.DESKTOP, AgentPlatform.PYTHON])
        elif task_type == 'web_automation':
            requirements['capabilities'].extend(['web_interaction', 'javascript'])
            requirements['platforms'].extend([AgentPlatform.WEB, AgentPlatform.PYTHON])
        elif task_type == 'data_analysis':
            requirements['capabilities'].extend(['ml_processing', 'data_manipulation'])
            requirements['platforms'].extend([AgentPlatform.PYTHON, AgentPlatform.DOCKER])
        elif task_type == 'communication':
            requirements['capabilities'].extend(['messaging', 'file_sharing'])
            requirements['platforms'].extend([AgentPlatform.WEB, AgentPlatform.MOBILE])

        # Analyze resource requirements
        if task.get('requires_gpu', False):
            requirements['resources']['gpu'] = True
        if task.get('large_dataset', False):
            requirements['resources']['memory'] = '4GB+'

        return requirements

    async def _find_suitable_agents(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Find suitable agents for task requirements."""
        suitable_agents = []
        needed_deployments = []

        # Check existing deployments
        for deployment in self.deployments.values():
            if deployment.state == AgentState.RUNNING:
                agent_capabilities = self._get_agent_capabilities(deployment.agent_class)

                # Check if agent meets requirements
                if self._agent_meets_requirements(agent_capabilities, requirements):
                    suitable_agents.append({
                        'deployment_id': deployment.deployment_id,
                        'agent_class': deployment.agent_class,
                        'platform': deployment.platform,
                        'capabilities': agent_capabilities
                    })

        # Determine if additional deployments are needed
        missing_capabilities = self._find_missing_capabilities(suitable_agents, requirements)

        if missing_capabilities:
            needed_deployments = self._plan_additional_deployments(missing_capabilities, requirements)

        return {
            'agents': suitable_agents,
            'needed_deployments': needed_deployments,
            'coverage_score': len(suitable_agents) / max(1, len(requirements['capabilities']))
        }

    def _get_agent_capabilities(self, agent_class: str) -> List[str]:
        """Get capabilities for agent class."""
        # This would be expanded with actual agent capability mapping
        capability_map = {
            'MarketAnalyzerAgent': ['market_analysis', 'data_processing', 'prediction'],
            'DiscordModeratorAgent': ['moderation', 'communication', 'content_analysis'],
            'WorkflowOptimizerAgent': ['optimization', 'automation', 'analysis'],
            'MiningManagerAgent': ['mining', 'resource_management', 'monitoring'],
            'BaseEnhancedAgent': ['general_ai', 'coordination', 'learning']
        }

        return capability_map.get(agent_class, ['general_ai'])

    def _agent_meets_requirements(self, agent_capabilities: List[str], requirements: Dict[str, Any]) -> bool:
        """Check if agent meets task requirements."""
        required_capabilities = set(requirements.get('capabilities', []))
        agent_capability_set = set(agent_capabilities)

        # Check if agent has at least some required capabilities
        intersection = required_capabilities.intersection(agent_capability_set)
        return len(intersection) > 0

    def _find_missing_capabilities(self, suitable_agents: List[Dict], requirements: Dict[str, Any]) -> List[str]:
        """Find capabilities not covered by existing agents."""
        covered_capabilities = set()

        for agent in suitable_agents:
            covered_capabilities.update(agent['capabilities'])

        required_capabilities = set(requirements.get('capabilities', []))
        return list(required_capabilities - covered_capabilities)

    def _plan_additional_deployments(self, missing_capabilities: List[str], requirements: Dict[str, Any]) -> List[Dict]:
        """Plan additional agent deployments."""
        deployments = []

        # Map capabilities to agent classes
        capability_to_agent = {
            'ui_automation': {'class': 'ByteBotAgent', 'platform': AgentPlatform.DESKTOP},
            'web_interaction': {'class': 'BrowserUseAgent', 'platform': AgentPlatform.WEB},
            'data_processing': {'class': 'DataProcessorAgent', 'platform': AgentPlatform.PYTHON},
            'ml_processing': {'class': 'MLAgent', 'platform': AgentPlatform.DOCKER},
            'messaging': {'class': 'CommunicationAgent', 'platform': AgentPlatform.WEB}
        }

        for capability in missing_capabilities:
            if capability in capability_to_agent:
                agent_spec = capability_to_agent[capability]
                deployments.append({
                    'class': agent_spec['class'],
                    'platform': agent_spec['platform'],
                    'config': self.platform_configs[agent_spec['platform']]
                })

        return deployments

    async def get_deployment_status(self, deployment_id: str) -> Optional[Dict[str, Any]]:
        """Get deployment status."""
        deployment = self.deployments.get(deployment_id)
        if not deployment:
            return None

        deployer = self.deployers.get(deployment.platform)
        if not deployer:
            return None

        metrics = await deployer.get_agent_metrics(deployment_id)
        health = await deployer.check_agent_health(deployment_id)

        return {
            'deployment': deployment.to_dict(),
            'metrics': metrics,
            'healthy': health,
            'platform': deployment.platform.value
        }

    async def list_deployments(self, platform: Optional[AgentPlatform] = None) -> List[Dict[str, Any]]:
        """List all deployments, optionally filtered by platform."""
        deployments = []

        for deployment in self.deployments.values():
            if platform is None or deployment.platform == platform:
                status = await self.get_deployment_status(deployment.deployment_id)
                if status:
                    deployments.append(status)

        return deployments

    async def _health_monitor(self) -> None:
        """Monitor health of all deployments."""
        while self._running:
            try:
                for deployment_id in list(self.deployments.keys()):
                    deployment = self.deployments.get(deployment_id)
                    if deployment:
                        deployer = self.deployers.get(deployment.platform)
                        if deployer:
                            healthy = await deployer.check_agent_health(deployment_id)

                            if not healthy and deployment.state == AgentState.RUNNING:
                                self.logger.warning(f"Agent {deployment_id} appears unhealthy")
                                deployment.state = AgentState.ERROR
                                deployment.status_message = "Agent became unhealthy"

                await asyncio.sleep(self.health_check_interval)

            except Exception as e:
                self.logger.error(f"Error in health monitor: {e}")
                await asyncio.sleep(self.health_check_interval)

    def get_platform_summary(self) -> Dict[str, Any]:
        """Get summary of platform usage."""
        summary = {
            'total_deployments': len(self.deployments),
            'platforms': {},
            'healthy_deployments': 0,
            'unhealthy_deployments': 0
        }

        for deployment in self.deployments.values():
            platform = deployment.platform.value

            if platform not in summary['platforms']:
                summary['platforms'][platform] = {
                    'count': 0,
                    'healthy': 0,
                    'unhealthy': 0
                }

            summary['platforms'][platform]['count'] += 1

            if deployment.state == AgentState.RUNNING and deployment.is_alive():
                summary['platforms'][platform]['healthy'] += 1
                summary['healthy_deployments'] += 1
            else:
                summary['platforms'][platform]['unhealthy'] += 1
                summary['unhealthy_deployments'] += 1

        return summary


# Global instance
_cross_platform_framework = None


def get_cross_platform_framework() -> CrossPlatformAgentFramework:
    """Get global cross-platform framework instance."""
    global _cross_platform_framework
    if _cross_platform_framework is None:
        _cross_platform_framework = CrossPlatformAgentFramework()
    return _cross_platform_framework


async def deploy_agent_cross_platform(
    agent_class: str,
    platform: AgentPlatform,
    platform_config: Optional[PlatformConfig] = None,
    agent_id: Optional[str] = None
) -> str:
    """Deploy agent across platforms."""
    framework = get_cross_platform_framework()
    return await framework.deploy_agent(agent_class, platform, platform_config, agent_id)


async def coordinate_cross_platform_task(task: Dict[str, Any]) -> Dict[str, Any]:
    """Coordinate agents across platforms for a task."""
    framework = get_cross_platform_framework()
    return await framework.coordinate_cross_platform_agents(task)


# Example usage and integration functions
async def example_cross_platform_deployment():
    """Example of cross-platform agent deployment."""
    framework = get_cross_platform_framework()
    await framework.start()

    try:
        # Deploy agents to different platforms
        python_deployment = await framework.deploy_agent(
            'MarketAnalyzerAgent',
            AgentPlatform.PYTHON
        )

        web_deployment = await framework.deploy_agent(
            'DiscordModeratorAgent',
            AgentPlatform.WEB
        )

        # Coordinate cross-platform task
        task = {
            'type': 'data_analysis',
            'description': 'Analyze market data and moderate discussions',
            'requires_gpu': False,
            'large_dataset': True
        }

        result = await framework.coordinate_cross_platform_agents(task)
        print(f"Cross-platform coordination result: {result}")

        # Get deployment status
        status = await framework.get_deployment_status(python_deployment)
        print(f"Python agent status: {status}")

    finally:
        await framework.stop()


if __name__ == "__main__":
    # Run example
    asyncio.run(example_cross_platform_deployment())