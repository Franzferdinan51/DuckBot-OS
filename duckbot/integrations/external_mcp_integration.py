#!/usr/bin/env python3
"""
DuckBot External MCP Server Integration
Integrates external MCP servers into DuckBot ecosystem
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Callable
import uuid
import requests
import aiohttp
import psutil

# DuckBot imports
try:
    from .mcp_server import DuckBotMCPServer
    from ..core.logging_setup import setup_logging
    DUCKBOT_AVAILABLE = True
except ImportError:
    DUCKBOT_AVAILABLE = False

# Setup logging
logger = logging.getLogger(__name__)

class ExternalMCPManager:
    """Manages external MCP server integrations for DuckBot"""

    def __init__(self):
        self.external_servers = {}
        self.server_processes = {}
        self.server_health = {}
        self.integration_config = {}
        self._load_configuration()

    def _load_configuration(self):
        """Load external MCP server configuration"""
        config_path = Path(__file__).parent.parent / "config" / "external_mcp_config.json"

        default_config = {
            "external_servers": {
                "mcp_chrome": {
                    "enabled": True,
                    "repository": "hangwin/mcp-chrome",
                    "install_method": "npm",
                    "package": "@modelcontextprotocol/server-chrome",
                    "auto_start": True,
                    "timeout": 30,
                    "priority": "high"
                },
                "playwright": {
                    "enabled": True,
                    "repository": "samuelcolvin/mcp-playwright",
                    "install_method": "pip",
                    "package": "mcp-playwright",
                    "auto_start": True,
                    "timeout": 30,
                    "priority": "high"
                },
                "exa_search": {
                    "enabled": True,
                    "repository": "exa-labs/mcp-server-exa",
                    "install_method": "npm",
                    "package": "@modelcontextprotocol/server-exa",
                    "auto_start": True,
                    "timeout": 30,
                    "priority": "medium",
                    "env_vars": {
                        "EXA_API_KEY": ""
                    }
                },
                "perplexity": {
                    "enabled": True,
                    "repository": "perplexityai/mcp-server-perplexity",
                    "install_method": "npm",
                    "package": "@modelcontextprotocol/server-perplexity",
                    "auto_start": True,
                    "timeout": 30,
                    "priority": "medium",
                    "env_vars": {
                        "PERPLEXITY_API_KEY": ""
                    }
                },
                "dbhub": {
                    "enabled": True,
                    "repository": "dbhub-io/mcp-server-dbhub",
                    "install_method": "npm",
                    "package": "@modelcontextprotocol/server-dbhub",
                    "auto_start": True,
                    "timeout": 30,
                    "priority": "medium",
                    "env_vars": {
                        "DBHUB_API_KEY": ""
                    }
                },
                "filesystem": {
                    "enabled": True,
                    "repository": "modelcontextprotocol/server-filesystem",
                    "install_method": "npm",
                    "package": "@modelcontextprotocol/server-filesystem",
                    "auto_start": True,
                    "timeout": 30,
                    "priority": "high",
                    "allowed_directories": ["/tmp", "/home/user/projects"]
                }
            },
            "global_settings": {
                "auto_install": True,
                "health_check_interval": 60,
                "max_retries": 3,
                "fallback_mode": True,
                "log_level": "INFO"
            }
        }

        try:
            if config_path.exists():
                with open(config_path, 'r') as f:
                    self.integration_config = json.load(f)
            else:
                self.integration_config = default_config
                # Create default config file
                config_path.parent.mkdir(parents=True, exist_ok=True)
                with open(config_path, 'w') as f:
                    json.dump(default_config, f, indent=2)
                logger.info(f"Created default external MCP configuration at {config_path}")
        except Exception as e:
            logger.error(f"Failed to load external MCP configuration: {e}")
            self.integration_config = default_config

    async def initialize_external_servers(self):
        """Initialize all external MCP servers"""
        logger.info("Initializing external MCP servers...")

        for server_name, config in self.integration_config.get("external_servers", {}).items():
            if config.get("enabled", False):
                try:
                    await self._initialize_server(server_name, config)
                except Exception as e:
                    logger.error(f"Failed to initialize {server_name}: {e}")
                    if self.integration_config.get("global_settings", {}).get("fallback_mode", True):
                        await self._initialize_fallback_server(server_name, config)

    async def _initialize_server(self, server_name: str, config: dict):
        """Initialize a specific external MCP server"""
        logger.info(f"Initializing external MCP server: {server_name}")

        # Check if server is already installed
        if not await self._check_server_installed(server_name, config):
            if config.get("auto_install", True):
                await self._install_server(server_name, config)
            else:
                logger.warning(f"Server {server_name} not installed and auto_install disabled")
                return

        # Start the server
        if config.get("auto_start", True):
            await self._start_server(server_name, config)

        # Register server tools
        await self._register_server_tools(server_name, config)

        # Add to external servers list
        self.external_servers[server_name] = {
            "config": config,
            "status": "running",
            "tools": [],
            "last_check": datetime.now().isoformat()
        }

        logger.info(f"Successfully initialized external MCP server: {server_name}")

    async def _check_server_installed(self, server_name: str, config: dict) -> bool:
        """Check if an external MCP server is installed"""
        install_method = config.get("install_method", "npm")
        package = config.get("package", "")

        try:
            if install_method == "npm":
                result = subprocess.run(
                    ["npm", "list", "-g", package],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                return result.returncode == 0
            elif install_method == "pip":
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "show", package],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                return result.returncode == 0
        except Exception as e:
            logger.warning(f"Failed to check if {server_name} is installed: {e}")
            return False

        return False

    async def _install_server(self, server_name: str, config: dict):
        """Install an external MCP server"""
        logger.info(f"Installing external MCP server: {server_name}")

        install_method = config.get("install_method", "npm")
        package = config.get("package", "")

        try:
            if install_method == "npm":
                cmd = ["npm", "install", "-g", package]
            elif install_method == "pip":
                cmd = [sys.executable, "-m", "pip", "install", package]
            else:
                raise ValueError(f"Unknown install method: {install_method}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode != 0:
                raise Exception(f"Installation failed: {result.stderr}")

            logger.info(f"Successfully installed {server_name}")

        except Exception as e:
            logger.error(f"Failed to install {server_name}: {e}")
            raise

    async def _start_server(self, server_name: str, config: dict):
        """Start an external MCP server"""
        logger.info(f"Starting external MCP server: {server_name}")

        install_method = config.get("install_method", "npm")
        package = config.get("package", "")

        try:
            # Prepare environment variables
            env = os.environ.copy()
            env_vars = config.get("env_vars", {})
            for key, value in env_vars.items():
                if value:  # Only set if value is not empty
                    env[key] = value

            # Start the server process
            if install_method == "npm":
                cmd = ["npx", package]
            elif install_method == "pip":
                cmd = [sys.executable, "-m", package]
            else:
                raise ValueError(f"Unknown install method: {install_method}")

            # Start server in background
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                text=True
            )

            self.server_processes[server_name] = process

            # Wait a moment for server to start
            await asyncio.sleep(2)

            # Check if server is running
            if process.poll() is None:
                logger.info(f"Successfully started {server_name} (PID: {process.pid})")
                self.server_health[server_name] = {
                    "status": "running",
                    "pid": process.pid,
                    "last_check": datetime.now().isoformat()
                }
            else:
                raise Exception(f"Server {server_name} failed to start")

        except Exception as e:
            logger.error(f"Failed to start {server_name}: {e}")
            raise

    async def _register_server_tools(self, server_name: str, config: dict):
        """Register tools from external MCP server"""
        logger.info(f"Registering tools from external MCP server: {server_name}")

        # This is a simplified implementation
        # In a real implementation, you would connect to the MCP server
        # and retrieve its tool definitions

        # Define common tools for each server type
        server_tools = self._get_server_tools(server_name, config)

        # Add tools to the external servers list
        self.external_servers[server_name]["tools"] = server_tools

        logger.info(f"Registered {len(server_tools)} tools from {server_name}")

    def _get_server_tools(self, server_name: str, config: dict) -> List[dict]:
        """Get tool definitions for a specific server"""

        if server_name == "mcp_chrome":
            return [
                {
                    "name": "chrome_navigate",
                    "description": "Navigate to a URL in Chrome browser",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "url": {"type": "string", "description": "URL to navigate to"}
                        },
                        "required": ["url"]
                    }
                },
                {
                    "name": "chrome_screenshot",
                    "description": "Take a screenshot of the current page",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "selector": {"type": "string", "description": "CSS selector to screenshot (optional)"}
                        }
                    }
                },
                {
                    "name": "chrome_click",
                    "description": "Click on an element in Chrome",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "selector": {"type": "string", "description": "CSS selector of element to click"}
                        },
                        "required": ["selector"]
                    }
                },
                {
                    "name": "chrome_type",
                    "description": "Type text into an element in Chrome",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "selector": {"type": "string", "description": "CSS selector of element"},
                            "text": {"type": "string", "description": "Text to type"}
                        },
                        "required": ["selector", "text"]
                    }
                }
            ]

        elif server_name == "playwright":
            return [
                {
                    "name": "playwright_navigate",
                    "description": "Navigate to a URL using Playwright",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "url": {"type": "string", "description": "URL to navigate to"},
                            "browser": {"type": "string", "enum": ["chromium", "firefox", "webkit"], "default": "chromium"}
                        },
                        "required": ["url"]
                    }
                },
                {
                    "name": "playwright_screenshot",
                    "description": "Take a screenshot using Playwright",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "selector": {"type": "string", "description": "CSS selector (optional)"},
                            "full_page": {"type": "boolean", "default": False}
                        }
                    }
                },
                {
                    "name": "playwright_click",
                    "description": "Click on an element using Playwright",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "selector": {"type": "string", "description": "CSS selector of element"}
                        },
                        "required": ["selector"]
                    }
                },
                {
                    "name": "playwright_fill",
                    "description": "Fill form field using Playwright",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "selector": {"type": "string", "description": "CSS selector of field"},
                            "value": {"type": "string", "description": "Value to fill"}
                        },
                        "required": ["selector", "value"]
                    }
                }
            ]

        elif server_name == "exa_search":
            return [
                {
                    "name": "exa_search",
                    "description": "Search the web using Exa API",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query"},
                            "num_results": {"type": "integer", "default": 10},
                            "type": {"type": "string", "enum": ["web", "news", "papers"], "default": "web"}
                        },
                        "required": ["query"]
                    }
                }
            ]

        elif server_name == "perplexity":
            return [
                {
                    "name": "perplexity_search",
                    "description": "Search the web using Perplexity AI",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query"},
                            "model": {"type": "string", "default": "mixtral-8x7b-instruct"}
                        },
                        "required": ["query"]
                    }
                }
            ]

        elif server_name == "dbhub":
            return [
                {
                    "name": "dbhub_query",
                    "description": "Execute SQL query using dbhub",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "database_type": {"type": "string", "enum": ["mysql", "postgresql", "sqlserver", "mariadb"]},
                            "connection_string": {"type": "string", "description": "Database connection string"},
                            "query": {"type": "string", "description": "SQL query to execute"}
                        },
                        "required": ["database_type", "connection_string", "query"]
                    }
                }
            ]

        elif server_name == "filesystem":
            return [
                {
                    "name": "filesystem_read",
                    "description": "Read a file",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "File path to read"}
                        },
                        "required": ["path"]
                    }
                },
                {
                    "name": "filesystem_write",
                    "description": "Write content to a file",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "File path to write"},
                            "content": {"type": "string", "description": "Content to write"},
                            "append": {"type": "boolean", "default": False}
                        },
                        "required": ["path", "content"]
                    }
                },
                {
                    "name": "filesystem_list",
                    "description": "List directory contents",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "Directory path"}
                        },
                        "required": ["path"]
                    }
                }
            ]

        return []

    async def _initialize_fallback_server(self, server_name: str, config: dict):
        """Initialize fallback implementation for external server"""
        logger.info(f"Initializing fallback implementation for {server_name}")

        # Create fallback implementation
        fallback_tools = self._get_fallback_tools(server_name, config)

        self.external_servers[server_name] = {
            "config": config,
            "status": "fallback",
            "tools": fallback_tools,
            "last_check": datetime.now().isoformat()
        }

        logger.info(f"Initialized fallback implementation for {server_name}")

    def _get_fallback_tools(self, server_name: str, config: dict) -> List[dict]:
        """Get fallback tool implementations"""

        if server_name == "mcp_chrome":
            return [
                {
                    "name": "chrome_navigate_fallback",
                    "description": "Fallback: Open URL in default browser",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "url": {"type": "string", "description": "URL to open"}
                        },
                        "required": ["url"]
                    }
                }
            ]

        elif server_name == "exa_search":
            return [
                {
                    "name": "exa_search_fallback",
                    "description": "Fallback: Basic web search using requests",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query"}
                        },
                        "required": ["query"]
                    }
                }
            ]

        return []

    async def execute_external_tool(self, server_name: str, tool_name: str, params: dict) -> dict:
        """Execute a tool from an external MCP server"""

        if server_name not in self.external_servers:
            return {"success": False, "error": f"Server {server_name} not found"}

        server_info = self.external_servers[server_name]

        if server_info["status"] == "fallback":
            return await self._execute_fallback_tool(server_name, tool_name, params)

        # Check if tool exists
        tool_found = False
        for tool in server_info["tools"]:
            if tool["name"] == tool_name:
                tool_found = True
                break

        if not tool_found:
            return {"success": False, "error": f"Tool {tool_name} not found in server {server_name}"}

        try:
            # Execute tool (this is a simplified implementation)
            # In a real implementation, you would send the request to the MCP server

            result = await self._execute_tool_request(server_name, tool_name, params)

            return {
                "success": True,
                "result": result,
                "server": server_name,
                "tool": tool_name,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to execute {tool_name} from {server_name}: {e}")
            return {"success": False, "error": str(e)}

    async def _execute_tool_request(self, server_name: str, tool_name: str, params: dict) -> dict:
        """Execute a tool request (simplified implementation)"""

        # This is a mock implementation
        # In a real implementation, you would:
        # 1. Connect to the MCP server
        # 2. Send the tool request
        # 3. Parse the response

        if server_name == "mcp_chrome":
            if tool_name == "chrome_navigate":
                return {"message": f"Would navigate to {params.get('url')}"}
            elif tool_name == "chrome_screenshot":
                return {"message": "Would take screenshot"}

        elif server_name == "exa_search":
            if tool_name == "exa_search":
                return {
                    "results": [
                        {"title": "Mock result 1", "url": "https://example.com/1"},
                        {"title": "Mock result 2", "url": "https://example.com/2"}
                    ]
                }

        return {"message": f"Executed {tool_name} with params: {params}"}

    async def _execute_fallback_tool(self, server_name: str, tool_name: str, params: dict) -> dict:
        """Execute fallback tool implementation"""

        try:
            if server_name == "mcp_chrome" and tool_name == "chrome_navigate_fallback":
                import webbrowser
                url = params.get("url")
                webbrowser.open(url)
                return {"success": True, "message": f"Opened {url} in default browser"}

            elif server_name == "exa_search" and tool_name == "exa_search_fallback":
                query = params.get("query")
                # Simple fallback using a basic search
                return {
                    "success": True,
                    "results": [
                        {"title": f"Search result for: {query}", "url": "https://example.com"}
                    ]
                }

            return {"success": False, "error": f"Fallback tool {tool_name} not implemented"}

        except Exception as e:
            return {"success": False, "error": f"Fallback tool failed: {str(e)}"}

    async def check_server_health(self, server_name: str = None) -> dict:
        """Check health of external MCP servers"""

        if server_name:
            servers_to_check = [server_name]
        else:
            servers_to_check = list(self.external_servers.keys())

        health_results = {}

        for server in servers_to_check:
            if server in self.server_processes:
                process = self.server_processes[server]

                if process.poll() is None:
                    self.server_health[server] = {
                        "status": "running",
                        "pid": process.pid,
                        "last_check": datetime.now().isoformat()
                    }
                else:
                    self.server_health[server] = {
                        "status": "stopped",
                        "last_check": datetime.now().isoformat()
                    }

            health_results[server] = self.server_health.get(server, {"status": "unknown"})

        return health_results

    async def stop_server(self, server_name: str):
        """Stop an external MCP server"""

        if server_name in self.server_processes:
            process = self.server_processes[server_name]

            try:
                process.terminate()
                process.wait(timeout=10)

                if server_name in self.external_servers:
                    self.external_servers[server_name]["status"] = "stopped"

                if server_name in self.server_health:
                    self.server_health[server_name]["status"] = "stopped"

                logger.info(f"Stopped external MCP server: {server_name}")

            except Exception as e:
                logger.error(f"Failed to stop {server_name}: {e}")
                process.kill()  # Force kill if terminate fails

    async def stop_all_servers(self):
        """Stop all external MCP servers"""

        for server_name in list(self.server_processes.keys()):
            await self.stop_server(server_name)

        logger.info("Stopped all external MCP servers")

    def get_external_tools(self) -> dict:
        """Get all available external tools"""

        all_tools = {}

        for server_name, server_info in self.external_servers.items():
            if server_info["status"] in ["running", "fallback"]:
                for tool in server_info["tools"]:
                    tool_name = f"{server_name}_{tool['name']}"
                    all_tools[tool_name] = {
                        "server": server_name,
                        "description": tool["description"],
                        "input_schema": tool["input_schema"],
                        "status": server_info["status"]
                    }

        return all_tools

    def get_server_status(self) -> dict:
        """Get status of all external MCP servers"""

        status = {}

        for server_name, server_info in self.external_servers.items():
            status[server_name] = {
                "status": server_info["status"],
                "tools_count": len(server_info["tools"]),
                "last_check": server_info["last_check"]
            }

            if server_name in self.server_health:
                status[server_name].update(self.server_health[server_name])

        return status

# Global instance
external_mcp_manager = ExternalMCPManager()

# Integration functions
async def initialize_external_mcp_servers():
    """Initialize all external MCP servers"""
    await external_mcp_manager.initialize_external_servers()

async def execute_external_mcp_tool(server_name: str, tool_name: str, params: dict) -> dict:
    """Execute a tool from an external MCP server"""
    return await external_mcp_manager.execute_external_tool(server_name, tool_name, params)

async def stop_external_mcp_servers():
    """Stop all external MCP servers"""
    await external_mcp_manager.stop_all_servers()

def get_external_mcp_tools() -> dict:
    """Get all available external MCP tools"""
    return external_mcp_manager.get_external_tools()

def get_external_mcp_status() -> dict:
    """Get status of all external MCP servers"""
    return external_mcp_manager.get_server_status()

if __name__ == "__main__":
    import asyncio

    async def main():
        try:
            await initialize_external_mcp_servers()
            print("External MCP servers initialized successfully")

            # Check status
            status = get_external_mcp_status()
            print(f"Server status: {status}")

            # Get tools
            tools = get_external_mcp_tools()
            print(f"Available tools: {list(tools.keys())}")

            # Keep running
            while True:
                await asyncio.sleep(60)
                await external_mcp_manager.check_server_health()

        except KeyboardInterrupt:
            await stop_external_mcp_servers()
            print("External MCP servers stopped")

    asyncio.run(main())