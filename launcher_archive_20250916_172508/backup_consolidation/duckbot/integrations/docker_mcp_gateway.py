#!/usr/bin/env python3
"""
Docker MCP Gateway Integration for DuckBot

This module provides integration with Docker's MCP Gateway for secure,
container-based MCP server management with proper isolation.
"""

import asyncio
import json
import subprocess
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class DockerMCPServer:
    """Represents a Docker MCP Server configuration"""
    name: str
    image: str
    port: int
    environment: Dict[str, str]
    volumes: List[str]
    secrets: List[str]
    enabled: bool = True

class DockerMCPGateway:
    """Docker MCP Gateway integration for DuckBot"""

    def __init__(self):
        self.gateway_config_path = Path.home() / ".docker" / "mcp"
        self.config_file = self.gateway_config_path / "config.json"
        self.catalogs_file = self.gateway_config_path / "catalogs.json"
        self.servers_file = self.gateway_config_path / "servers.json"

        # Initialize Docker MCP Gateway components
        self.catalogs = {}
        self.servers = {}
        self.tools = {}

        # Ensure config directory exists
        self.gateway_config_path.mkdir(parents=True, exist_ok=True)

        logger.info("Docker MCP Gateway integration initialized")

    async def initialize(self):
        """Initialize Docker MCP Gateway connection and configuration"""
        try:
            # Check if Docker MCP Gateway is available
            if await self._check_docker_mcp_available():
                await self._load_configuration()
                await self._discover_servers()
                await self._load_tools()
                logger.info("Docker MCP Gateway initialized successfully")
            else:
                logger.warning("Docker MCP Gateway not available - using fallback mode")
                await self._initialize_fallback_mode()
        except Exception as e:
            logger.error(f"Failed to initialize Docker MCP Gateway: {e}")
            await self._initialize_fallback_mode()

    async def _check_docker_mcp_available(self) -> bool:
        """Check if Docker MCP Gateway is available"""
        try:
            # Check if Docker is running
            result = subprocess.run(
                ["docker", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode != 0:
                return False

            # Check if Docker MCP plugin is available
            result = subprocess.run(
                ["docker", "mcp", "--help"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    async def _load_configuration(self):
        """Load Docker MCP Gateway configuration"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.catalogs = config.get('catalogs', {})
                    self.servers = config.get('servers', {})
                    logger.info(f"Loaded configuration: {len(self.servers)} servers")
            else:
                await self._create_default_configuration()
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            await self._create_default_configuration()

    async def _create_default_configuration(self):
        """Create default Docker MCP Gateway configuration"""
        default_config = {
            "catalogs": {
                "duckbot": {
                    "description": "DuckBot MCP Server Catalog",
                    "url": "http://localhost:8000/catalog",
                    "auth": None
                }
            },
            "servers": {
                "duckbot-main": {
                    "catalog": "duckbot",
                    "image": "duckbot-mcp:latest",
                    "port": 8000,
                    "environment": {
                        "DUCKBOT_MODE": "production",
                        "LOG_LEVEL": "INFO"
                    },
                    "volumes": [
                        "./logs:/app/logs",
                        "./duckbot/config:/app/config"
                    ],
                    "secrets": [],
                    "enabled": True
                }
            }
        }

        try:
            with open(self.config_file, 'w') as f:
                json.dump(default_config, f, indent=2)
            self.catalogs = default_config['catalogs']
            self.servers = default_config['servers']
            logger.info("Created default configuration")
        except Exception as e:
            logger.error(f"Failed to create default configuration: {e}")

    async def _discover_servers(self):
        """Discover available MCP servers via Docker MCP Gateway"""
        try:
            # Try to list servers using Docker MCP Gateway
            result = subprocess.run(
                ["docker", "mcp", "server", "list", "--format", "json"],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                servers_data = json.loads(result.stdout)
                for server in servers_data:
                    self.servers[server['name']] = server
                logger.info(f"Discovered {len(servers_data)} servers via Docker MCP Gateway")
        except Exception as e:
            logger.warning(f"Failed to discover servers via Docker MCP Gateway: {e}")

    async def _load_tools(self):
        """Load available tools from Docker MCP Gateway servers"""
        try:
            for server_name, server_config in self.servers.items():
                if server_config.get('enabled', True):
                    tools = await self._get_server_tools(server_name)
                    self.tools[server_name] = tools
                    logger.info(f"Loaded {len(tools)} tools from server {server_name}")
        except Exception as e:
            logger.error(f"Failed to load tools: {e}")

    async def _get_server_tools(self, server_name: str) -> List[Dict[str, Any]]:
        """Get tools from a specific server"""
        try:
            # Try to get tools via Docker MCP Gateway
            result = subprocess.run(
                ["docker", "mcp", "server", "tools", server_name, "--format", "json"],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                return json.loads(result.stdout)
            else:
                # Fallback: try direct HTTP request to server
                server_config = self.servers.get(server_name, {})
                port = server_config.get('port', 8000)

                import aiohttp
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"http://localhost:{port}/tools") as response:
                        if response.status == 200:
                            data = await response.json()
                            return data.get('tools', [])

                return []
        except Exception as e:
            logger.warning(f"Failed to get tools from server {server_name}: {e}")
            return []

    async def _initialize_fallback_mode(self):
        """Initialize fallback mode without Docker MCP Gateway"""
        logger.info("Initializing fallback mode for Docker MCP Gateway")

        # Create basic fallback configuration
        self.catalogs = {
            "duckbot-fallback": {
                "description": "DuckBot Fallback Catalog",
                "url": "http://localhost:8000/catalog",
                "auth": None
            }
        }

        self.servers = {
            "duckbot-main": {
                "catalog": "duckbot-fallback",
                "image": "duckbot-mcp:latest",
                "port": 8000,
                "environment": {},
                "volumes": [],
                "secrets": [],
                "enabled": True
            }
        }

        # Try to load tools from local DuckBot MCP server
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get("http://localhost:8000/tools") as response:
                    if response.status == 200:
                        data = await response.json()
                        self.tools["duckbot-main"] = data.get('tools', [])
        except Exception as e:
            logger.warning(f"Failed to load tools in fallback mode: {e}")
            self.tools["duckbot-main"] = []

    async def list_catalogs(self) -> Dict[str, Any]:
        """List available MCP catalogs"""
        return {
            "catalogs": self.catalogs,
            "count": len(self.catalogs)
        }

    async def list_servers(self) -> Dict[str, Any]:
        """List available MCP servers"""
        return {
            "servers": self.servers,
            "count": len(self.servers)
        }

    async def list_tools(self, server_name: Optional[str] = None) -> Dict[str, Any]:
        """List available tools from MCP servers"""
        if server_name:
            return {
                "server": server_name,
                "tools": self.tools.get(server_name, [])
            }
        else:
            return {
                "tools": self.tools,
                "total_tools": sum(len(tools) for tools in self.tools.values())
            }

    async def start_server(self, server_name: str) -> Dict[str, Any]:
        """Start a Docker MCP server"""
        try:
            if server_name not in self.servers:
                return {"success": False, "error": f"Server {server_name} not found"}

            # Try to start server using Docker MCP Gateway
            result = subprocess.run(
                ["docker", "mcp", "server", "start", server_name],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                return {"success": True, "message": f"Server {server_name} started"}
            else:
                return {
                    "success": False,
                    "error": f"Failed to start server {server_name}: {result.stderr}"
                }
        except Exception as e:
            return {"success": False, "error": f"Error starting server {server_name}: {e}"}

    async def stop_server(self, server_name: str) -> Dict[str, Any]:
        """Stop a Docker MCP server"""
        try:
            if server_name not in self.servers:
                return {"success": False, "error": f"Server {server_name} not found"}

            # Try to stop server using Docker MCP Gateway
            result = subprocess.run(
                ["docker", "mcp", "server", "stop", server_name],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                return {"success": True, "message": f"Server {server_name} stopped"}
            else:
                return {
                    "success": False,
                    "error": f"Failed to stop server {server_name}: {result.stderr}"
                }
        except Exception as e:
            return {"success": False, "error": f"Error stopping server {server_name}: {e}"}

    async def execute_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool on a Docker MCP server"""
        try:
            if server_name not in self.servers:
                return {"success": False, "error": f"Server {server_name} not found"}

            # Try to execute tool using Docker MCP Gateway
            tool_data = {
                "server": server_name,
                "tool": tool_name,
                "arguments": arguments
            }

            result = subprocess.run(
                ["docker", "mcp", "tool", "execute", "--json", json.dumps(tool_data)],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                return {"success": True, "result": json.loads(result.stdout)}
            else:
                return {
                    "success": False,
                    "error": f"Failed to execute tool {tool_name}: {result.stderr}"
                }
        except Exception as e:
            return {"success": False, "error": f"Error executing tool {tool_name}: {e}"}

    async def add_server(self, server_config: DockerMCPServer) -> Dict[str, Any]:
        """Add a new Docker MCP server"""
        try:
            # Add to configuration
            self.servers[server_config.name] = {
                "catalog": "duckbot",
                "image": server_config.image,
                "port": server_config.port,
                "environment": server_config.environment,
                "volumes": server_config.volumes,
                "secrets": server_config.secrets,
                "enabled": server_config.enabled
            }

            # Save configuration
            await self._save_configuration()

            # Try to add server using Docker MCP Gateway
            result = subprocess.run([
                "docker", "mcp", "server", "add",
                server_config.name,
                "--image", server_config.image,
                "--port", str(server_config.port),
                *(["--env"] + [f"{k}={v}" for k, v in server_config.environment.items()]),
                *(["--volume"] + server_config.volumes),
                *(["--secret"] + server_config.secrets)
            ], capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                return {"success": True, "message": f"Server {server_config.name} added"}
            else:
                logger.warning(f"Docker MCP Gateway command failed, using local config only: {result.stderr}")
                return {"success": True, "message": f"Server {server_config.name} added (local config)"}
        except Exception as e:
            return {"success": False, "error": f"Error adding server {server_config.name}: {e}"}

    async def remove_server(self, server_name: str) -> Dict[str, Any]:
        """Remove a Docker MCP server"""
        try:
            if server_name not in self.servers:
                return {"success": False, "error": f"Server {server_name} not found"}

            # Remove from configuration
            del self.servers[server_name]

            # Save configuration
            await self._save_configuration()

            # Try to remove server using Docker MCP Gateway
            result = subprocess.run(
                ["docker", "mcp", "server", "remove", server_name],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                return {"success": True, "message": f"Server {server_name} removed"}
            else:
                logger.warning(f"Docker MCP Gateway command failed, using local config only: {result.stderr}")
                return {"success": True, "message": f"Server {server_name} removed (local config)"}
        except Exception as e:
            return {"success": False, "error": f"Error removing server {server_name}: {e}"}

    async def _save_configuration(self):
        """Save current configuration to file"""
        try:
            config = {
                "catalogs": self.catalogs,
                "servers": self.servers
            }

            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)

            logger.info("Configuration saved successfully")
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")

    async def get_gateway_status(self) -> Dict[str, Any]:
        """Get Docker MCP Gateway status"""
        try:
            # Check Docker status
            docker_result = subprocess.run(
                ["docker", "info"],
                capture_output=True,
                text=True,
                timeout=10
            )
            docker_running = docker_result.returncode == 0

            # Check Docker MCP Gateway status
            gateway_result = subprocess.run(
                ["docker", "mcp", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            gateway_available = gateway_result.returncode == 0

            # Get server status
            server_status = {}
            for server_name in self.servers:
                try:
                    result = subprocess.run(
                        ["docker", "mcp", "server", "status", server_name],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    server_status[server_name] = "running" if result.returncode == 0 else "stopped"
                except:
                    server_status[server_name] = "unknown"

            return {
                "docker_running": docker_running,
                "gateway_available": gateway_available,
                "gateway_version": gateway_result.stdout.strip() if gateway_available else "Not available",
                "servers": server_status,
                "total_servers": len(self.servers),
                "total_tools": sum(len(tools) for tools in self.tools.values())
            }
        except Exception as e:
            logger.error(f"Failed to get gateway status: {e}")
            return {"error": str(e)}

# Global instance
docker_mcp_gateway = DockerMCPGateway()

async def initialize_docker_mcp_gateway():
    """Initialize Docker MCP Gateway integration"""
    await docker_mcp_gateway.initialize()
    return docker_mcp_gateway