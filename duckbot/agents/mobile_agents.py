"""
Mobile Agent Framework for DuckBot v4.2

Specialized framework for deploying and managing mobile agents on Android and iOS platforms.
Based on AP2 patterns for mobile agent scenarios with consistent type systems.

Features:
- Android agent deployment with ADB integration
- iOS agent deployment with Xcode integration
- Mobile-specific optimization patterns
- Cross-platform mobile agent coordination
- Device resource management
- Mobile security frameworks
"""

import asyncio
import json
import logging
import os
import platform
import subprocess
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

# DuckBot imports
from duckbot.core.logging_setup import setup_logging
from duckbot.core.utilities import safe_execute, run_command_async
from duckbot.agents.cross_platform_framework import (
    BasePlatformDeployer, AgentDeployment, DeploymentStatus, AgentPlatform,
    PlatformConfig
)

logger = setup_logging(__name__)


class MobileOS(Enum):
    """Supported mobile operating systems."""
    ANDROID = "android"
    IOS = "ios"


class MobileDeviceType(Enum):
    """Mobile device types."""
    PHONE = "phone"
    TABLET = "tablet"
    WEARABLE = "wearable"


class MobileAgentType(Enum):
    """Mobile agent types."""
    NATIVE = "native"  # Native mobile app
    HYBRID = "hybrid"  # Hybrid web-native app
    WEB = "web"  # Web-based mobile agent


@dataclass
class MobileDevice:
    """Mobile device information."""
    device_id: str
    device_name: str
    os_type: MobileOS
    os_version: str
    device_type: MobileDeviceType
    screen_resolution: str
    memory_mb: int
    storage_gb: float
    cpu_cores: int
    is_connected: bool = False
    last_seen: Optional[datetime] = None
    capabilities: List[str] = field(default_factory=list)

    def update_connection_status(self, connected: bool) -> None:
        """Update device connection status."""
        self.is_connected = connected
        self.last_seen = datetime.utcnow() if connected else None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'device_id': self.device_id,
            'device_name': self.device_name,
            'os_type': self.os_type.value,
            'os_version': self.os_version,
            'device_type': self.device_type.value,
            'screen_resolution': self.screen_resolution,
            'memory_mb': self.memory_mb,
            'storage_gb': self.storage_gb,
            'cpu_cores': self.cpu_cores,
            'is_connected': self.is_connected,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
            'capabilities': self.capabilities
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MobileDevice':
        """Create from dictionary."""
        device = cls(
            device_id=data['device_id'],
            device_name=data['device_name'],
            os_type=MobileOS(data['os_type']),
            os_version=data['os_version'],
            device_type=MobileDeviceType(data['device_type']),
            screen_resolution=data['screen_resolution'],
            memory_mb=data['memory_mb'],
            storage_gb=data['storage_gb'],
            cpu_cores=data['cpu_cores'],
            is_connected=data.get('is_connected', False),
            capabilities=data.get('capabilities', [])
        )

        if data.get('last_seen'):
            device.last_seen = datetime.fromisoformat(data['last_seen'])

        return device


@dataclass
class MobileAgentConfig:
    """Mobile agent configuration."""
    agent_type: MobileAgentType
    package_name: str
    version: str
    min_os_version: str
    target_os_version: str
    permissions: List[str] = field(default_factory=list)
    features: List[str] = field(default_factory=list)
    resource_requirements: Dict[str, Any] = field(default_factory=dict)
    deployment_config: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'agent_type': self.agent_type.value,
            'package_name': self.package_name,
            'version': self.version,
            'min_os_version': self.min_os_version,
            'target_os_version': self.target_os_version,
            'permissions': self.permissions,
            'features': self.features,
            'resource_requirements': self.resource_requirements,
            'deployment_config': self.deployment_config
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MobileAgentConfig':
        """Create from dictionary."""
        return cls(
            agent_type=MobileAgentType(data['agent_type']),
            package_name=data['package_name'],
            version=data['version'],
            min_os_version=data['min_os_version'],
            target_os_version=data['target_os_version'],
            permissions=data.get('permissions', []),
            features=data.get('features', []),
            resource_requirements=data.get('resource_requirements', {}),
            deployment_config=data.get('deployment_config', {})
        )


class BaseMobileDeployer(ABC):
    """Abstract base class for mobile platform deployers."""

    def __init__(self, os_type: MobileOS, config: PlatformConfig):
        self.os_type = os_type
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{os_type.value}")
        self.connected_devices: Dict[str, MobileDevice] = {}
        self.deployed_agents: Dict[str, AgentDeployment] = {}

    @abstractmethod
    async def discover_devices(self) -> List[MobileDevice]:
        """Discover connected mobile devices."""
        pass

    @abstractmethod
    async def deploy_agent(self, deployment: AgentDeployment, device_id: str) -> DeploymentStatus:
        """Deploy agent to mobile device."""
        pass

    @abstractmethod
    async def uninstall_agent(self, deployment_id: str, device_id: str) -> DeploymentStatus:
        """Uninstall agent from mobile device."""
        pass

    @abstractmethod
    async def check_agent_health(self, deployment_id: str, device_id: str) -> bool:
        """Check if mobile agent is healthy."""
        pass

    @abstractmethod
    async def get_device_metrics(self, device_id: str) -> Dict[str, Any]:
        """Get device performance metrics."""
        pass

    async def refresh_device_list(self) -> None:
        """Refresh list of connected devices."""
        try:
            devices = await self.discover_devices()

            # Update device connection status
            current_device_ids = {d.device_id for d in devices}
            for device_id, device in list(self.connected_devices.items()):
                if device_id not in current_device_ids:
                    device.update_connection_status(False)

            # Add or update devices
            for device in devices:
                if device.device_id in self.connected_devices:
                    self.connected_devices[device.device_id].update_connection_status(True)
                else:
                    self.connected_devices[device.device_id] = device
                    device.update_connection_status(True)

            self.logger.info(f"Discovered {len(devices)} {self.os_type.value} devices")

        except Exception as e:
            self.logger.error(f"Error refreshing device list: {e}")

    def get_connected_devices(self) -> List[MobileDevice]:
        """Get list of connected devices."""
        return [device for device in self.connected_devices.values() if device.is_connected]

    def get_device(self, device_id: str) -> Optional[MobileDevice]:
        """Get device by ID."""
        return self.connected_devices.get(device_id)


class AndroidDeployer(BaseMobileDeployer):
    """Android-specific agent deployer using ADB."""

    def __init__(self, config: PlatformConfig):
        super().__init__(MobileOS.ANDROID, config)
        self.adb_path = config.environment_vars.get('ADB_PATH', 'adb')
        self.sdk_path = config.environment_vars.get('ANDROID_SDK_PATH', '')
        self._device_monitors: Dict[str, asyncio.Task] = {}

    async def discover_devices(self) -> List[MobileDevice]:
        """Discover connected Android devices using ADB."""
        devices = []

        try:
            # Get list of connected devices
            result = await run_command_async([self.adb_path, 'devices'])
            lines = result.strip().split('\n')[1:]  # Skip header line

            for line in lines:
                if '\t' in line:
                    device_id, status = line.split('\t')
                    if status == 'device':
                        device = await self._get_android_device_info(device_id)
                        devices.append(device)

        except Exception as e:
            self.logger.error(f"Error discovering Android devices: {e}")

        return devices

    async def deploy_agent(self, deployment: AgentDeployment, device_id: str) -> DeploymentStatus:
        """Deploy Android agent using ADB."""
        try:
            device = self.get_device(device_id)
            if not device:
                return DeploymentStatus.FAILED

            deployment.state = AgentState.DEPLOYING
            deployment.deployment_time = datetime.utcnow()

            # Check if agent is compatible with device
            if not await self._check_agent_compatibility(deployment, device):
                deployment.state = AgentState.ERROR
                deployment.status_message = "Agent not compatible with device"
                return DeploymentStatus.FAILED

            # Build Android APK (simplified - would require actual build process)
            apk_path = await self._build_android_agent(deployment)

            # Install APK on device
            install_result = await run_command_async([
                self.adb_path, '-s', device_id, 'install', '-r', apk_path
            ])

            if 'Success' not in install_result:
                deployment.state = AgentState.ERROR
                deployment.status_message = f"Installation failed: {install_result}"
                return DeploymentStatus.FAILED

            # Grant permissions
            mobile_config = MobileAgentConfig.from_dict(
                deployment.platform_config.deployment_config.get('mobile_config', {})
            )

            for permission in mobile_config.permissions:
                await run_command_async([
                    self.adb_path, '-s', device_id, 'shell', 'pm', 'grant',
                    mobile_config.package_name, permission
                ])

            # Start agent
            await run_command_async([
                self.adb_path, '-s', device_id, 'shell', 'am', 'start',
                '-n', f"{mobile_config.package_name}/.MainActivity"
            ])

            deployment.state = AgentState.RUNNING
            deployment.status_message = "Android agent deployed successfully"
            deployment.network_endpoints['device'] = device_id

            # Start device monitoring
            self._device_monitors[deployment.deployment_id] = asyncio.create_task(
                self._monitor_android_agent(deployment.deployment_id, device_id)
            )

            self.logger.info(f"Deployed Android agent {deployment.agent_id} to device {device_id}")
            return DeploymentStatus.SUCCESS

        except Exception as e:
            deployment.state = AgentState.ERROR
            deployment.status_message = f"Android deployment failed: {str(e)}"
            self.logger.error(f"Failed to deploy Android agent: {e}")
            return DeploymentStatus.FAILED

    async def uninstall_agent(self, deployment_id: str, device_id: str) -> DeploymentStatus:
        """Uninstall Android agent."""
        try:
            deployment = self.deployed_agents.get(deployment_id)
            if not deployment:
                return DeploymentStatus.FAILED

            mobile_config = MobileAgentConfig.from_dict(
                deployment.platform_config.deployment_config.get('mobile_config', {})
            )

            # Uninstall app
            result = await run_command_async([
                self.adb_path, '-s', device_id, 'uninstall', mobile_config.package_name
            ])

            if 'Success' not in result:
                return DeploymentStatus.FAILED

            # Stop monitoring
            if deployment_id in self._device_monitors:
                self._device_monitors[deployment_id].cancel()
                del self._device_monitors[deployment_id]

            if deployment_id in self.deployed_agents:
                del self.deployed_agents[deployment_id]

            self.logger.info(f"Uninstalled Android agent from device {device_id}")
            return DeploymentStatus.SUCCESS

        except Exception as e:
            self.logger.error(f"Failed to uninstall Android agent: {e}")
            return DeploymentStatus.FAILED

    async def check_agent_health(self, deployment_id: str, device_id: str) -> bool:
        """Check if Android agent is healthy."""
        try:
            deployment = self.deployed_agents.get(deployment_id)
            if not deployment:
                return False

            mobile_config = MobileAgentConfig.from_dict(
                deployment.platform_config.deployment_config.get('mobile_config', {})
            )

            # Check if app is running
            result = await run_command_async([
                self.adb_path, '-s', device_id, 'shell', 'pgrep', '-f', mobile_config.package_name
            ])

            return bool(result.strip())

        except Exception as e:
            self.logger.error(f"Error checking Android agent health: {e}")
            return False

    async def get_device_metrics(self, device_id: str) -> Dict[str, Any]:
        """Get Android device metrics."""
        try:
            metrics = {}

            # CPU usage
            cpu_result = await run_command_async([
                self.adb_path, '-s', device_id, 'shell', 'cat', '/proc/loadavg'
            ])
            metrics['cpu_load'] = cpu_result.strip().split()[0] if cpu_result.strip() else '0'

            # Memory usage
            mem_result = await run_command_async([
                self.adb_path, '-s', device_id, 'shell', 'cat', '/proc/meminfo'
            ])
            if mem_result.strip():
                for line in mem_result.strip().split('\n'):
                    if 'MemTotal:' in line:
                        metrics['memory_total_kb'] = line.split()[1]
                    elif 'MemAvailable:' in line:
                        metrics['memory_available_kb'] = line.split()[1]

            # Battery level
            battery_result = await run_command_async([
                self.adb_path, '-s', device_id, 'shell', 'dumpsys', 'battery'
            ])
            if battery_result.strip():
                for line in battery_result.strip().split('\n'):
                    if 'level:' in line:
                        metrics['battery_level'] = line.split(':')[1].strip()
                    elif 'status:' in line:
                        metrics['battery_status'] = line.split(':')[1].strip()

            # Storage info
            storage_result = await run_command_async([
                self.adb_path, '-s', device_id, 'shell', 'df', '/data'
            ])
            if storage_result.strip():
                lines = storage_result.strip().split('\n')
                if len(lines) > 1:
                    parts = lines[1].split()
                    metrics['storage_total_kb'] = parts[1]
                    metrics['storage_available_kb'] = parts[3]

            return metrics

        except Exception as e:
            self.logger.error(f"Error getting Android device metrics: {e}")
            return {}

    async def _get_android_device_info(self, device_id: str) -> MobileDevice:
        """Get detailed Android device information."""
        try:
            # Get device model
            model_result = await run_command_async([
                self.adb_path, '-s', device_id, 'shell', 'getprop', 'ro.product.model'
            ])
            device_name = model_result.strip() or f"Android Device {device_id[:8]}"

            # Get Android version
            version_result = await run_command_async([
                self.adb_path, '-s', device_id, 'shell', 'getprop', 'ro.build.version.release'
            ])
            os_version = version_result.strip() or "Unknown"

            # Get screen resolution
            display_result = await run_command_async([
                self.adb_path, '-s', device_id, 'shell', 'wm', 'size'
            ])
            if 'Physical size:' in display_result:
                screen_resolution = display_result.split('Physical size:')[1].strip()
            else:
                screen_resolution = "Unknown"

            # Get memory info
            mem_result = await run_command_async([
                self.adb_path, '-s', device_id, 'shell', 'cat', '/proc/meminfo'
            ])
            memory_mb = 0
            if mem_result.strip():
                for line in mem_result.strip().split('\n'):
                    if 'MemTotal:' in line:
                        memory_kb = int(line.split()[1])
                        memory_mb = memory_kb // 1024
                        break

            # Determine device type based on screen size
            device_type = MobileDeviceType.PHONE
            if 'tablet' in device_name.lower() or 'pad' in device_name.lower():
                device_type = MobileDeviceType.TABLET

            return MobileDevice(
                device_id=device_id,
                device_name=device_name,
                os_type=MobileOS.ANDROID,
                os_version=os_version,
                device_type=device_type,
                screen_resolution=screen_resolution,
                memory_mb=memory_mb,
                storage_gb=8.0,  # Default, would need actual calculation
                cpu_cores=4,  # Default, would need actual detection
                capabilities=['android', 'adb', 'mobile']
            )

        except Exception as e:
            self.logger.error(f"Error getting Android device info for {device_id}: {e}")
            return MobileDevice(
                device_id=device_id,
                device_name=f"Unknown Android Device",
                os_type=MobileOS.ANDROID,
                os_version="Unknown",
                device_type=MobileDeviceType.PHONE,
                screen_resolution="Unknown",
                memory_mb=0,
                storage_gb=0,
                cpu_cores=0,
                capabilities=['android', 'adb']
            )

    async def _check_agent_compatibility(self, deployment: AgentDeployment, device: MobileDevice) -> bool:
        """Check if agent is compatible with device."""
        try:
            mobile_config = MobileAgentConfig.from_dict(
                deployment.platform_config.deployment_config.get('mobile_config', {})
            )

            # Check OS version compatibility
            if device.os_version < mobile_config.min_os_version:
                self.logger.warning(f"Device OS version {device.os_version} < required {mobile_config.min_os_version}")
                return False

            # Check device capabilities
            required_capabilities = set(mobile_config.features)
            device_capabilities = set(device.capabilities)

            if not required_capabilities.issubset(device_capabilities):
                missing = required_capabilities - device_capabilities
                self.logger.warning(f"Device missing capabilities: {missing}")
                return False

            return True

        except Exception as e:
            self.logger.error(f"Error checking agent compatibility: {e}")
            return False

    async def _build_android_agent(self, deployment: AgentDeployment) -> str:
        """Build Android agent APK (simplified implementation)."""
        # In a real implementation, this would:
        # 1. Generate Android project structure
        # 2. Copy agent code and dependencies
        # 3. Build using Gradle
        # 4. Sign the APK

        # For now, return a dummy path
        return f"/tmp/{deployment.deployment_id}.apk"

    async def _monitor_android_agent(self, deployment_id: str, device_id: str) -> None:
        """Monitor Android agent health."""
        while deployment_id in self.deployed_agents:
            try:
                healthy = await self.check_agent_health(deployment_id, device_id)

                deployment = self.deployed_agents.get(deployment_id)
                if deployment:
                    if healthy:
                        deployment.update_heartbeat()
                    else:
                        deployment.state = AgentState.ERROR
                        deployment.status_message = "Agent became unresponsive"
                        break

                await asyncio.sleep(30)

            except Exception as e:
                self.logger.error(f"Error monitoring Android agent {deployment_id}: {e}")
                await asyncio.sleep(30)


class IOSDeployer(BaseMobileDeployer):
    """iOS-specific agent deployer using Xcode tools."""

    def __init__(self, config: PlatformConfig):
        super().__init__(MobileOS.IOS, config)
        self.xcode_path = config.environment_vars.get('XCODE_PATH', '/Applications/Xcode.app')
        self.ios_deploy_path = config.environment_vars.get('IOS_DEPLOY_PATH', 'ios-deploy')

    async def discover_devices(self) -> List[MobileDevice]:
        """Discover connected iOS devices."""
        devices = []

        try:
            # Use ios-deploy to find connected devices
            result = await run_command_async([self.ios_deploy_path, '-c'])

            if 'Found' in result:
                # Parse device information
                lines = result.strip().split('\n')
                for line in lines:
                    if 'UDID:' in line:
                        device_id = line.split('UDID:')[1].strip().split()[0]
                        device = await self._get_ios_device_info(device_id)
                        devices.append(device)

        except Exception as e:
            self.logger.error(f"Error discovering iOS devices: {e}")

        return devices

    async def deploy_agent(self, deployment: AgentDeployment, device_id: str) -> DeploymentStatus:
        """Deploy iOS agent using Xcode tools."""
        try:
            device = self.get_device(device_id)
            if not device:
                return DeploymentStatus.FAILED

            deployment.state = AgentState.DEPLOYING
            deployment.deployment_time = datetime.utcnow()

            # Check agent compatibility
            if not await self._check_agent_compatibility(deployment, device):
                deployment.state = AgentState.ERROR
                deployment.status_message = "Agent not compatible with device"
                return DeploymentStatus.FAILED

            # Build iOS app (simplified)
            app_path = await self._build_ios_agent(deployment)

            # Deploy to device using ios-deploy
            result = await run_command_async([
                self.ios_deploy_path, '-i', app_path, '-b', device_id
            ])

            if 'Install' not in result:
                deployment.state = AgentState.ERROR
                deployment.status_message = f"iOS installation failed: {result}"
                return DeploymentStatus.FAILED

            deployment.state = AgentState.RUNNING
            deployment.status_message = "iOS agent deployed successfully"
            deployment.network_endpoints['device'] = device_id

            self.logger.info(f"Deployed iOS agent {deployment.agent_id} to device {device_id}")
            return DeploymentStatus.SUCCESS

        except Exception as e:
            deployment.state = AgentState.ERROR
            deployment.status_message = f"iOS deployment failed: {str(e)}"
            self.logger.error(f"Failed to deploy iOS agent: {e}")
            return DeploymentStatus.FAILED

    async def uninstall_agent(self, deployment_id: str, device_id: str) -> DeploymentStatus:
        """Uninstall iOS agent."""
        try:
            deployment = self.deployed_agents.get(deployment_id)
            if not deployment:
                return DeploymentStatus.FAILED

            mobile_config = MobileAgentConfig.from_dict(
                deployment.platform_config.deployment_config.get('mobile_config', {})
            )

            # Uninstall app (simplified - would need proper iOS tooling)
            await run_command_async([
                self.ios_deploy_path, '-U', mobile_config.package_name, '-b', device_id
            ])

            if deployment_id in self.deployed_agents:
                del self.deployed_agents[deployment_id]

            self.logger.info(f"Uninstalled iOS agent from device {device_id}")
            return DeploymentStatus.SUCCESS

        except Exception as e:
            self.logger.error(f"Failed to uninstall iOS agent: {e}")
            return DeploymentStatus.FAILED

    async def check_agent_health(self, deployment_id: str, device_id: str) -> bool:
        """Check if iOS agent is healthy."""
        try:
            deployment = self.deployed_agents.get(deployment_id)
            if not deployment:
                return False

            # Check if app is installed (simplified)
            mobile_config = MobileAgentConfig.from_dict(
                deployment.platform_config.deployment_config.get('mobile_config', {})
            )

            result = await run_command_async([
                self.ios_deploy_path, '-l', '-b', device_id
            ])

            return mobile_config.package_name in result

        except Exception as e:
            self.logger.error(f"Error checking iOS agent health: {e}")
            return False

    async def get_device_metrics(self, device_id: str) -> Dict[str, Any]:
        """Get iOS device metrics."""
        try:
            metrics = {}

            # Battery level (would need proper iOS tooling)
            metrics['battery_level'] = 'N/A'
            metrics['battery_status'] = 'N/A'

            # Storage info
            metrics['storage_total_gb'] = 'N/A'
            metrics['storage_available_gb'] = 'N/A'

            # Memory info
            metrics['memory_total_mb'] = 'N/A'
            metrics['memory_available_mb'] = 'N/A'

            return metrics

        except Exception as e:
            self.logger.error(f"Error getting iOS device metrics: {e}")
            return {}

    async def _get_ios_device_info(self, device_id: str) -> MobileDevice:
        """Get detailed iOS device information."""
        try:
            # Get device info (simplified - would need proper iOS tooling)
            device_name = f"iOS Device {device_id[:8]}"
            os_version = "Unknown"
            screen_resolution = "Unknown"

            return MobileDevice(
                device_id=device_id,
                device_name=device_name,
                os_type=MobileOS.IOS,
                os_version=os_version,
                device_type=MobileDeviceType.PHONE,
                screen_resolution=screen_resolution,
                memory_mb=0,
                storage_gb=0,
                cpu_cores=0,
                capabilities=['ios', 'mobile']
            )

        except Exception as e:
            self.logger.error(f"Error getting iOS device info for {device_id}: {e}")
            return MobileDevice(
                device_id=device_id,
                device_name=f"Unknown iOS Device",
                os_type=MobileOS.IOS,
                os_version="Unknown",
                device_type=MobileDeviceType.PHONE,
                screen_resolution="Unknown",
                memory_mb=0,
                storage_gb=0,
                cpu_cores=0,
                capabilities=['ios']
            )

    async def _check_agent_compatibility(self, deployment: AgentDeployment, device: MobileDevice) -> bool:
        """Check if agent is compatible with iOS device."""
        try:
            mobile_config = MobileAgentConfig.from_dict(
                deployment.platform_config.deployment_config.get('mobile_config', {})
            )

            # Check OS version compatibility
            if device.os_version < mobile_config.min_os_version:
                return False

            return True

        except Exception as e:
            self.logger.error(f"Error checking iOS agent compatibility: {e}")
            return False

    async def _build_ios_agent(self, deployment: AgentDeployment) -> str:
        """Build iOS app (simplified implementation)."""
        # In a real implementation, this would:
        # 1. Generate Xcode project
        # 2. Build using xcodebuild
        # 3. Code sign the app

        return f"/tmp/{deployment.deployment_id}.app"


class MobileAgentFramework:
    """Main mobile agent framework."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.deployers: Dict[MobileOS, BaseMobileDeployer] = {}
        self.deployments: Dict[str, AgentDeployment] = {}
        self._running = False
        self._device_discovery_task = None

        # Initialize deployers
        self._initialize_deployers()

    def _initialize_deployers(self) -> None:
        """Initialize mobile platform deployers."""
        try:
            # Android deployer
            android_config = PlatformConfig(
                AgentPlatform.MOBILE,
                "android",
                environment_vars={
                    'ADB_PATH': 'adb',
                    'ANDROID_SDK_PATH': ''
                }
            )
            self.deployers[MobileOS.ANDROID] = AndroidDeployer(android_config)

            # iOS deployer
            ios_config = PlatformConfig(
                AgentPlatform.MOBILE,
                "ios",
                environment_vars={
                    'XCODE_PATH': '/Applications/Xcode.app',
                    'IOS_DEPLOY_PATH': 'ios-deploy'
                }
            )
            self.deployers[MobileOS.IOS] = IOSDeployer(ios_config)

            self.logger.info("Initialized mobile platform deployers")

        except Exception as e:
            self.logger.error(f"Failed to initialize mobile deployers: {e}")

    async def start(self) -> None:
        """Start the mobile agent framework."""
        self._running = True

        # Start device discovery
        self._device_discovery_task = asyncio.create_task(self._device_discovery_loop())

        self.logger.info("Mobile agent framework started")

    async def stop(self) -> None:
        """Stop the mobile agent framework."""
        self._running = False

        # Stop all deployments
        for deployment_id in list(self.deployments.keys()):
            await self.stop_agent(deployment_id)

        # Stop device discovery
        if self._device_discovery_task:
            self._device_discovery_task.cancel()
            try:
                await self._device_discovery_task
            except asyncio.CancelledError:
                pass

        self.logger.info("Mobile agent framework stopped")

    async def discover_devices(self) -> Dict[str, List[MobileDevice]]:
        """Discover all connected mobile devices."""
        all_devices = {}

        for os_type, deployer in self.deployers.items():
            await deployer.refresh_device_list()
            devices = deployer.get_connected_devices()
            all_devices[os_type.value] = devices

        return all_devices

    async def deploy_mobile_agent(self,
                                 agent_class: str,
                                 os_type: MobileOS,
                                 device_id: str,
                                 mobile_config: MobileAgentConfig,
                                 platform_config: Optional[PlatformConfig] = None) -> str:
        """Deploy mobile agent to specific device."""
        try:
            deployer = self.deployers.get(os_type)
            if not deployer:
                raise ValueError(f"Unsupported mobile OS: {os_type}")

            device = deployer.get_device(device_id)
            if not device:
                raise ValueError(f"Device {device_id} not found")

            # Create deployment
            deployment_id = f"{agent_class}_{device_id}_{uuid.uuid4().hex[:8]}"
            config = platform_config or PlatformConfig(
                AgentPlatform.MOBILE,
                os_type.value,
                deployment_config={'mobile_config': mobile_config.to_dict()}
            )

            deployment = AgentDeployment(
                deployment_id=deployment_id,
                agent_id=agent_class,
                agent_class=agent_class,
                platform=AgentPlatform.MOBILE,
                platform_config=config
            )

            # Deploy agent
            status = await deployer.deploy_agent(deployment, device_id)

            if status == DeploymentStatus.SUCCESS:
                self.deployments[deployment_id] = deployment
                deployer.deployed_agents[deployment_id] = deployment
                self.logger.info(f"Deployed mobile agent {agent_class} to {os_type.value} device {device_id}")
                return deployment_id
            else:
                raise RuntimeError(f"Mobile deployment failed: {deployment.status_message}")

        except Exception as e:
            self.logger.error(f"Error deploying mobile agent: {e}")
            raise

    async def stop_agent(self, deployment_id: str) -> bool:
        """Stop mobile agent."""
        try:
            deployment = self.deployments.get(deployment_id)
            if not deployment:
                return False

            # Find the deployer and device
            for deployer in self.deployers.values():
                if deployment_id in deployer.deployed_agents:
                    device_id = deployment.network_endpoints.get('device')
                    if device_id:
                        status = await deployer.uninstall_agent(deployment_id, device_id)
                        if status == DeploymentStatus.SUCCESS:
                            del self.deployments[deployment_id]
                            return True

            return False

        except Exception as e:
            self.logger.error(f"Error stopping mobile agent {deployment_id}: {e}")
            return False

    async def get_mobile_agent_status(self, deployment_id: str) -> Optional[Dict[str, Any]]:
        """Get mobile agent status."""
        deployment = self.deployments.get(deployment_id)
        if not deployment:
            return None

        # Find the deployer
        for deployer in self.deployers.values():
            if deployment_id in deployer.deployed_agents:
                device_id = deployment.network_endpoints.get('device')
                if device_id:
                    healthy = await deployer.check_agent_health(deployment_id, device_id)
                    device_metrics = await deployer.get_device_metrics(device_id)

                    return {
                        'deployment': deployment.to_dict(),
                        'healthy': healthy,
                        'device_metrics': device_metrics,
                        'device_id': device_id,
                        'platform': deployment.platform.value
                    }

        return None

    async def _device_discovery_loop(self) -> None:
        """Continuously discover mobile devices."""
        while self._running:
            try:
                await self.discover_devices()
                await asyncio.sleep(60)  # Check every minute

            except Exception as e:
                self.logger.error(f"Error in device discovery loop: {e}")
                await asyncio.sleep(60)

    def get_framework_summary(self) -> Dict[str, Any]:
        """Get mobile framework summary."""
        summary = {
            'total_deployments': len(self.deployments),
            'platforms': {},
            'connected_devices': {}
        }

        for os_type, deployer in self.deployers.items():
            devices = deployer.get_connected_devices()
            summary['connected_devices'][os_type.value] = len(devices)
            summary['platforms'][os_type.value] = {
                'deployments': len(deployer.deployed_agents),
                'devices': len(devices)
            }

        return summary


# Global instance
_mobile_framework = None


def get_mobile_framework() -> MobileAgentFramework:
    """Get global mobile framework instance."""
    global _mobile_framework
    if _mobile_framework is None:
        _mobile_framework = MobileAgentFramework()
    return _mobile_framework


# Example usage
async def example_mobile_deployment():
    """Example of mobile agent deployment."""
    framework = get_mobile_framework()
    await framework.start()

    try:
        # Discover devices
        devices = await framework.discover_devices()
        print(f"Connected devices: {devices}")

        # Deploy to first available Android device
        if devices.get('android'):
            device = devices['android'][0]
            mobile_config = MobileAgentConfig(
                agent_type=MobileAgentType.NATIVE,
                package_name="com.duckbot.agent",
                version="1.0.0",
                min_os_version="8.0",
                target_os_version="13.0",
                permissions=["android.permission.INTERNET", "android.permission.ACCESS_NETWORK_STATE"],
                features=["mobile_ai", "communication"]
            )

            deployment_id = await framework.deploy_mobile_agent(
                'MobileAssistantAgent',
                MobileOS.ANDROID,
                device.device_id,
                mobile_config
            )

            print(f"Deployed mobile agent: {deployment_id}")

            # Check status
            status = await framework.get_mobile_agent_status(deployment_id)
            print(f"Mobile agent status: {status}")

    finally:
        await framework.stop()


if __name__ == "__main__":
    asyncio.run(example_mobile_deployment())