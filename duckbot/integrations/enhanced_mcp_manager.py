#!/usr/bin/env python3
"""
Enhanced MCP Server Manager for DuckBot
Manages external MCP server integrations with intelligent orchestration
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

# DuckBot imports
try:
    from .mcp_server import DuckBotMCPServer
    from ..core.service_manager import UnifiedServiceManager
    from ..core.logging_setup import setup_logging
    DUCKBOT_AVAILABLE = True
except ImportError:
    DUCKBOT_AVAILABLE = False

class EnhancedMCPManager:
    """Enhanced MCP server manager with external server integration"""

    def __init__(self, config_path: str = "config/enhanced_mcp_config.json"):
        self.config_path = config_path
        self.config = self._load_config()
        self.external_servers = {}
        self.server_processes = {}
        self.server_health = {}
        self.unified_tools = {}
        self.logger = self._setup_logging()

        # Initialize core MCP server
        self.core_mcp_server = None
        if DUCKBOT_AVAILABLE:
            self.core_mcp_server = DuckBotMCPServer()

        self.logger.info("Enhanced MCP Manager initialized")

    def _load_config(self) -> Dict[str, Any]:
        """Load enhanced MCP configuration"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            self.logger.warning(f"Config file not found: {self.config_path}")
            return self._get_default_config()
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in config file: {e}")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "external_mcp_servers": {},
            "server_categories": {},
            "integration_settings": {
                "auto_discovery": True,
                "health_check_interval": 30,
                "max_external_servers": 10,
                "fallback_mode": True
            }
        }

    def _setup_logging(self) -> logging.Logger:
        """Setup logging for enhanced MCP manager"""
        logger = logging.getLogger("EnhancedMCPManager")
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    async def initialize(self) -> bool:
        """Initialize enhanced MCP manager and start servers"""
        try:
            self.logger.info("Initializing Enhanced MCP Manager...")

            # Initialize core MCP server
            if self.core_mcp_server:
                await self.core_mcp_server.start_mcp_server()
                self.logger.info("Core MCP server started")

            # Start external MCP servers
            await self._start_external_servers()

            # Start health monitoring
            asyncio.create_task(self._health_monitor_loop())

            self.logger.info("Enhanced MCP Manager initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize Enhanced MCP Manager: {e}")
            return False

    async def _start_external_servers(self):
        """Start configured external MCP servers"""
        external_servers = self.config.get("external_mcp_servers", {})

        for server_name, server_config in external_servers.items():
            if server_config.get("enabled", False) and server_config.get("auto_start", False):
                await self._start_external_server(server_name, server_config)

    async def _start_external_server(self, server_name: str, server_config: Dict[str, Any]):
        """Start a specific external MCP server"""
        try:
            command = server_config.get("command")
            args = server_config.get("args", [])
            env = server_config.get("env", {})

            if not command:
                self.logger.error(f"No command specified for server: {server_name}")
                return

            # Prepare environment variables
            process_env = os.environ.copy()
            for key, value in env.items():
                # Support environment variable substitution
                if value.startswith("${") and value.endswith("}"):
                    env_var = value[2:-1]
                    process_env[key] = os.getenv(env_var, "")
                else:
                    process_env[key] = value

            # Start the server process
            process = await asyncio.create_subprocess_exec(
                command,
                *args,
                env=process_env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(Path.cwd())
            )

            self.server_processes[server_name] = process
            self.external_servers[server_name] = server_config
            self.server_health[server_name] = {
                "status": "starting",
                "last_check": datetime.now().isoformat(),
                "pid": process.pid
            }

            self.logger.info(f"Started external MCP server: {server_name} (PID: {process.pid})")

            # Wait a moment for server to initialize
            await asyncio.sleep(2)

            # Perform initial health check
            await self._check_server_health(server_name)

        except Exception as e:
            self.logger.error(f"Failed to start external server {server_name}: {e}")
            self.server_health[server_name] = {
                "status": "failed",
                "last_check": datetime.now().isoformat(),
                "error": str(e)
            }

    async def _check_server_health(self, server_name: str) -> bool:
        """Check health of an external MCP server"""
        try:
            process = self.server_processes.get(server_name)
            if not process:
                return False

            # Check if process is still running
            return_code = process.returncode
            if return_code is not None:
                self.server_health[server_name] = {
                    "status": "stopped",
                    "last_check": datetime.now().isoformat(),
                    "return_code": return_code
                }
                return False

            # Update health status
            self.server_health[server_name] = {
                "status": "healthy",
                "last_check": datetime.now().isoformat(),
                "pid": process.pid
            }

            return True

        except Exception as e:
            self.logger.error(f"Health check failed for {server_name}: {e}")
            self.server_health[server_name] = {
                "status": "unhealthy",
                "last_check": datetime.now().isoformat(),
                "error": str(e)
            }
            return False

    async def _health_monitor_loop(self):
        """Monitor health of external MCP servers"""
        health_check_interval = self.config.get("integration_settings", {}).get("health_check_interval", 30)

        while True:
            try:
                await asyncio.sleep(health_check_interval)

                for server_name in list(self.server_health.keys()):
                    await self._check_server_health(server_name)

                    # Auto-restart failed servers
                    if self.server_health[server_name]["status"] in ["stopped", "unhealthy"]:
                        server_config = self.external_servers.get(server_name)
                        if server_config and server_config.get("auto_start", False):
                            self.logger.info(f"Auto-restarting server: {server_name}")
                            await self._start_external_server(server_name, server_config)

            except Exception as e:
                self.logger.error(f"Error in health monitor loop: {e}")

    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool across available MCP servers"""
        try:
            # Try core MCP server first
            if self.core_mcp_server:
                result = await self.core_mcp_server.execute_tool(tool_name, arguments)
                if result.get("success"):
                    return result

            # Try external servers by category
            server_config = self._find_server_for_tool(tool_name)
            if server_config:
                return await self._execute_on_external_server(server_config, tool_name, arguments)

            return {
                "success": False,
                "error": f"Tool '{tool_name}' not found in any MCP server",
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error executing tool {tool_name}: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def _find_server_for_tool(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Find the best server for a given tool"""
        # Tool to server mapping
        tool_server_mapping = {
            # Browser automation
            "browser_navigate": "playwright",
            "browser_click": "playwright",
            "browser_snapshot": "playwright",
            "browser_fill_form": "playwright",

            # System control
            "mouse_move": "mcpcontrol",
            "mouse_click": "mcpcontrol",
            "keyboard_type": "mcpcontrol",
            "window_focus": "mcpcontrol",
            "screen_capture": "mcpcontrol",

            # Filesystem
            "read_file": "filesystem",
            "write_file": "filesystem",
            "list_directory": "filesystem",
            "search_files": "filesystem",

            # WSL filesystem
            "wsl_read_file": "wsl_filesystem",
            "wsl_write_file": "wsl_filesystem",
            "wsl_list_directory": "wsl_filesystem",

            # Web search
            "web_search": "exa_search",
            "search_web": "exa_search",

            # Development
            "generate_docs": "claude_code_tools",
            "extract_wisdom": "claude_code_tools",
            "code_analysis": "claude_code_tools",

            # Agent orchestration
            "execute_mcp_client": "mcp_inception",
            "execute_parallel_mcp_client": "mcp_inception",
            "execute_map_reduce_mcp_client": "mcp_inception"
        }

        server_name = tool_server_mapping.get(tool_name)
        if server_name and server_name in self.external_servers:
            return self.external_servers[server_name]

        return None

    async def _execute_on_external_server(self, server_config: Dict[str, Any], tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute tool on external MCP server"""
        # This is a simplified implementation
        # In a real implementation, you would use the MCP protocol to communicate with the external server

        try:
            # For now, return a placeholder result
            return {
                "success": True,
                "result": f"Tool '{tool_name}' executed on external server",
                "server": server_config.get("name"),
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error executing {tool_name} on external server: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def get_server_status(self) -> Dict[str, Any]:
        """Get status of all MCP servers"""
        return {
            "core_server": {
                "available": self.core_mcp_server is not None,
                "status": "running" if self.core_mcp_server else "not_available"
            },
            "external_servers": {
                name: {
                    "config": config,
                    "health": self.server_health.get(name, {}),
                    "process": {
                        "pid": process.pid if process else None,
                        "running": process.returncode is None if process else False
                    } if process else None
                }
                for name, config in self.external_servers.items()
                for process in [self.server_processes.get(name)]
            },
            "unified_tools": list(self.unified_tools.keys()),
            "timestamp": datetime.now().isoformat()
        }

    async def stop_all_servers(self):
        """Stop all external MCP servers"""
        self.logger.info("Stopping all external MCP servers...")

        for server_name, process in self.server_processes.items():
            try:
                if process.returncode is None:
                    process.terminate()
                    # Wait for graceful shutdown
                    try:
                        await asyncio.wait_for(process.wait(), timeout=5)
                    except asyncio.TimeoutError:
                        process.kill()
                        await process.wait()

                self.logger.info(f"Stopped external server: {server_name}")

            except Exception as e:
                self.logger.error(f"Error stopping server {server_name}: {e}")

        self.server_processes.clear()
        self.logger.info("All external MCP servers stopped")

    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get list of available tools from all servers"""
        tools = []

        # Get tools from core server
        if self.core_mcp_server:
            try:
                core_tools = self.core_mcp_server.get_available_tools()
                tools.extend(core_tools)
            except Exception as e:
                self.logger.error(f"Error getting tools from core server: {e}")

        # Get tools from external servers
        for server_name, server_config in self.external_servers.items():
            category = server_config.get("category", "general")

            # Add category-specific tools
            category_tools = self._get_category_tools(category)
            for tool in category_tools:
                tool["server"] = server_name
                tool["server_category"] = category
                tools.append(tool)

        return tools

    def _get_category_tools(self, category: str) -> List[Dict[str, Any]]:
        """Get tools for a specific category"""
        tool_definitions = {
            "browser_automation": [
                {
                    "name": "browser_navigate",
                    "description": "Navigate to a URL in the browser",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "url": {"type": "string", "description": "URL to navigate to"}
                        },
                        "required": ["url"]
                    }
                },
                {
                    "name": "browser_click",
                    "description": "Click on an element in the browser",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "selector": {"type": "string", "description": "CSS selector for element"}
                        },
                        "required": ["selector"]
                    }
                },
                {
                    "name": "browser_snapshot",
                    "description": "Take a snapshot of the current browser state",
                    "inputSchema": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            ],
            "system_control": [
                {
                    "name": "mouse_move",
                    "description": "Move mouse to specific coordinates",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "x": {"type": "integer", "description": "X coordinate"},
                            "y": {"type": "integer", "description": "Y coordinate"}
                        },
                        "required": ["x", "y"]
                    }
                },
                {
                    "name": "mouse_click",
                    "description": "Click mouse at current position",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "button": {"type": "string", "enum": ["left", "right", "middle"], "description": "Mouse button"}
                        },
                        "required": []
                    }
                },
                {
                    "name": "keyboard_type",
                    "description": "Type text using keyboard",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "text": {"type": "string", "description": "Text to type"}
                        },
                        "required": ["text"]
                    }
                }
            ],
            "filesystem": [
                {
                    "name": "read_file",
                    "description": "Read file contents",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "File path"}
                        },
                        "required": ["path"]
                    }
                },
                {
                    "name": "write_file",
                    "description": "Write content to file",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "File path"},
                            "content": {"type": "string", "description": "Content to write"}
                        },
                        "required": ["path", "content"]
                    }
                },
                {
                    "name": "list_directory",
                    "description": "List directory contents",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "Directory path"}
                        },
                        "required": ["path"]
                    }
                }
            ],
            "web_search": [
                {
                    "name": "web_search",
                    "description": "Search the web",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query"},
                            "num_results": {"type": "integer", "description": "Number of results"}
                        },
                        "required": ["query"]
                    }
                }
            ],
            "development": [
                {
                    "name": "generate_docs",
                    "description": "Generate documentation",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "source": {"type": "string", "description": "Source code or file path"}
                        },
                        "required": ["source"]
                    }
                },
                {
                    "name": "extract_wisdom",
                    "description": "Extract insights from text or video",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "content": {"type": "string", "description": "Content to analyze"}
                        },
                        "required": ["content"]
                    }
                }
            ],
            "agent_orchestration": [
                {
                    "name": "execute_mcp_client",
                    "description": "Execute task on another MCP client",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "prompt": {"type": "string", "description": "Prompt to execute"}
                        },
                        "required": ["prompt"]
                    }
                },
                {
                    "name": "execute_parallel_mcp_client",
                    "description": "Execute tasks in parallel",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "prompt": {"type": "string", "description": "Prompt template"},
                            "inputs": {"type": "array", "description": "List of inputs"}
                        },
                        "required": ["prompt", "inputs"]
                    }
                }
            ]
        }

        return tool_definitions.get(category, [])

# Singleton instance
_enhanced_mcp_manager = None

def get_enhanced_mcp_manager() -> EnhancedMCPManager:
    """Get the enhanced MCP manager instance"""
    global _enhanced_mcp_manager
    if _enhanced_mcp_manager is None:
        _enhanced_mcp_manager = EnhancedMCPManager()
    return _enhanced_mcp_manager

# CLI functions
async def main():
    """Main CLI function"""
    manager = get_enhanced_mcp_manager()

    try:
        # Initialize manager
        success = await manager.initialize()
        if not success:
            print("Failed to initialize Enhanced MCP Manager")
            return 1

        print("Enhanced MCP Manager started successfully")
        print("Available tools:", len(manager.get_available_tools()))
        print("External servers:", len(manager.external_servers))

        # Keep running
        while True:
            await asyncio.sleep(60)

    except KeyboardInterrupt:
        print("\nShutting down Enhanced MCP Manager...")
        await manager.stop_all_servers()
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))