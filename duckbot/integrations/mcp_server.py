#!/usr/bin/env python3
"""
DuckBot MCP (Model Context Protocol) Server
Comprehensive MCP server implementation for DuckBot ecosystem integrations
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Callable
import uuid

# MCP imports
try:
    from mcp import Server, Tool, Resource
    from mcp.server import Server as MCPServer
    from mcp.client import Client as MCPClient
    from mcp.tools import ToolRegistry
    from mcp.resources import ResourceRegistry
    MCP_AVAILABLE = True
except ImportError:
    print("MCP not available - installing fallback implementation")
    MCP_AVAILABLE = False

# DuckBot imports
try:
    from ..ai_router_gpt import route_task, get_available_providers, get_ollama_model
    from .bytebot_integration import ByteBotIntegration
    from .archon_integration import ArchonIntegration
    from .memento_integration import execute_memento_task, get_memento_capabilities
    from .wsl_integration import WSLIntegration
    from .charm_ecosystem import CharmEcosystem
    from ..core.cost_management import CostTracker
    from ..services.server_manager import ServerManager
    from ..agents.learning_system import LearningSystem
    from ..services.ai_router_manager import connector_manager
    DUCKBOT_INTEGRATIONS_AVAILABLE = True
except ImportError as e:
    print(f"DuckBot integrations not fully available: {e}")
    DUCKBOT_INTEGRATIONS_AVAILABLE = False

# UI-TARS integration
try:
    from .ui_tars_integration import UITarsIntegration
    UI_TARS_INTEGRATION_AVAILABLE = True
except ImportError:
    UI_TARS_INTEGRATION_AVAILABLE = False
    print("UI-TARS integration not available")

# Docker MCP Gateway integration
try:
    from .docker_mcp_gateway import DockerMCPGateway, DockerMCPServer, docker_mcp_gateway
    DOCKER_MCP_GATEWAY_AVAILABLE = True
except ImportError:
    DOCKER_MCP_GATEWAY_AVAILABLE = False
    print("Docker MCP Gateway integration not available")

# DeepCode integration
try:
    from launcher_modules.deepcode.deepcode_integration import DuckBotDeepCodeIntegration
    from launcher_modules.deepcode.deepcode_mcp_servers import DeepCodeMCPServerManager
    DEEPCODE_AVAILABLE = True
except ImportError:
    DEEPCODE_AVAILABLE = False
    print("DeepCode integration not available")

# Enhanced RAG integration
try:
    from duckbot.core.enhanced_rag import EnhancedRAGEngine
    from duckbot.core.rag_ai_integration import RAGAIIntegration
    from duckbot.core.rag_memory_integration import RAGMemoryIntegration
    from duckbot.core.rag_agent_integration import RAGAgentIntegration
    ENHANCED_RAG_AVAILABLE = True
except ImportError:
    ENHANCED_RAG_AVAILABLE = False
    print("Enhanced RAG integration not available")

# Memento integration check
MEMENTO_INTEGRATION_AVAILABLE = DUCKBOT_INTEGRATIONS_AVAILABLE

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DuckBotMCPServer:
    """MCP Server for DuckBot ecosystem"""

    def __init__(self):
        self.server = None
        self.tools = {}
        self.resources = {}
        self.clients = {}
        self.sessions = {}
        self.integration_instances = {}
        self.running = False

        # Initialize DuckBot integrations
        self._initialize_integrations()

    def _initialize_integrations(self):
        """Initialize DuckBot integration instances"""
        try:
            # Initialize UI-TARS integration
            if UI_TARS_INTEGRATION_AVAILABLE:
                self.integration_instances['ui_tars'] = UITarsIntegration()

            # Initialize other integrations if available
            if DUCKBOT_INTEGRATIONS_AVAILABLE:
                try:
                    self.integration_instances['bytebot'] = ByteBotIntegration()
                except:
                    pass
                try:
                    self.integration_instances['archon'] = ArchonIntegration()
                except:
                    pass
                try:
                    self.integration_instances['wsl'] = WSLIntegration()
                except:
                    pass
                try:
                    self.integration_instances['charm'] = CharmEcosystem()
                except:
                    pass
                try:
                    self.integration_instances['cost_tracker'] = CostTracker()
                except:
                    pass
                try:
                    self.integration_instances['server_manager'] = ServerManager()
                except:
                    pass
                try:
                    self.integration_instances['learning'] = LearningSystem()
                except:
                    pass

            logger.info(f"DuckBot integrations initialized for MCP: {list(self.integration_instances.keys())}")
        except Exception as e:
            logger.error(f"Failed to initialize DuckBot integrations: {e}")

    async def initialize_mcp_server(self):
        """Initialize MCP server with DuckBot tools and resources"""
        if not MCP_AVAILABLE:
            logger.warning("MCP not available, using fallback implementation")
            # Always register tools even in fallback mode
            await self._register_tools()
            await self._register_resources()
            return self._initialize_fallback_server()

        try:
            # Create MCP server
            self.server = MCPServer(
                name="duckbot-mcp",
                version="1.0.0",
                description="DuckBot Ecosystem MCP Server"
            )

            # Register tools
            await self._register_tools()

            # Register resources
            await self._register_resources()

            # Set up event handlers
            self._setup_event_handlers()

            logger.info("MCP server initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize MCP server: {e}")
            # Always register tools even in fallback mode
            await self._register_tools()
            await self._register_resources()
            return self._initialize_fallback_server()

    def _initialize_fallback_server(self):
        """Initialize fallback MCP-like server"""
        logger.info("Initializing fallback MCP server")
        self.server = self._create_fallback_server()
        return True

    def _create_fallback_server(self):
        """Create fallback server implementation"""
        class FallbackServer:
            def __init__(self):
                self.tools = {}
                self.resources = {}

            async def start(self, host: str, port: int):
                logger.info(f"Fallback MCP server starting on {host}:{port}")

            async def stop(self):
                logger.info("Fallback MCP server stopped")

        return FallbackServer()

    async def _register_tools(self):
        """Register DuckBot tools with MCP server"""
        # Always register tools even if MCP is not available (fallback mode)

        # AI and Communication Tools
        await self._register_ai_tools()

        # Desktop Automation Tools
        await self._register_desktop_tools()

        # System Integration Tools
        await self._register_system_tools()

        # Multi-Agent Tools
        await self._register_agent_tools()

        # Memory and Learning Tools
        await self._register_memory_tools()

        # Terminal and CLI Tools
        await self._register_terminal_tools()

        # UI-TARS Integration Tools
        await self._register_ui_tars_tools()

        # Docker MCP Gateway Tools
        await self._register_docker_gateway_tools()

        # DeepCode Integration Tools
        await self._register_deepcode_tools()

        # Enhanced RAG Tools
        await self._register_rag_tools()

        logger.info(f"Registered {len(self.tools)} MCP tools")

    async def _register_ai_tools(self):
        """Register AI and communication tools"""
        # AI Task Routing
        self._register_tool(
            name="ai_route_task",
            description="Route AI task to appropriate provider/model",
            input_schema={
                "type": "object",
                "properties": {
                    "task": {"type": "string", "description": "Task description"},
                    "provider": {"type": "string", "description": "Preferred provider (optional)"},
                    "model": {"type": "string", "description": "Specific model (optional)"},
                    "context": {"type": "object", "description": "Additional context"}
                },
                "required": ["task"]
            },
            handler=self._handle_ai_route_task
        )

        # Provider Management
        self._register_tool(
            name="ai_list_providers",
            description="List available AI providers",
            input_schema={"type": "object", "properties": {}},
            handler=self._handle_list_providers
        )

        # Provider Switching
        self._register_tool(
            name="ai_switch_provider",
            description="Switch AI provider",
            input_schema={
                "type": "object",
                "properties": {
                    "provider": {"type": "string", "description": "Provider name"},
                    "api_key": {"type": "string", "description": "API key (optional)"}
                },
                "required": ["provider"]
            },
            handler=self._handle_switch_provider
        )

    async def _register_desktop_tools(self):
        """Register desktop automation tools"""
        if 'bytebot' not in self.integration_instances:
            return

        # Screenshot Analysis
        self._register_tool(
            name="desktop_screenshot",
            description="Take and analyze screenshot",
            input_schema={
                "type": "object",
                "properties": {
                    "analysis": {"type": "boolean", "description": "Enable AI analysis", "default": True}
                }
            },
            handler=self._handle_screenshot
        )

        # Mouse Control
        self._register_tool(
            name="desktop_mouse_click",
            description="Click mouse at coordinates",
            input_schema={
                "type": "object",
                "properties": {
                    "x": {"type": "integer", "description": "X coordinate"},
                    "y": {"type": "integer", "description": "Y coordinate"},
                    "button": {"type": "string", "enum": ["left", "right", "middle"], "default": "left"}
                },
                "required": ["x", "y"]
            },
            handler=self._handle_mouse_click
        )

        # Keyboard Input
        self._register_tool(
            name="desktop_type_text",
            description="Type text using keyboard",
            input_schema={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to type"},
                    "delay": {"type": "number", "description": "Delay between keystrokes"}
                },
                "required": ["text"]
            },
            handler=self._handle_type_text
        )

    async def _register_system_tools(self):
        """Register system integration tools"""
        # System Status
        self._register_tool(
            name="system_status",
            description="Get system status and metrics",
            input_schema={"type": "object", "properties": {}},
            handler=self._handle_system_status
        )

        # Process Management
        self._register_tool(
            name="system_list_processes",
            description="List running processes",
            input_schema={
                "type": "object",
                "properties": {
                    "filter": {"type": "string", "description": "Process name filter"}
                }
            },
            handler=self._handle_list_processes
        )

        # Service Management
        self._register_tool(
            name="system_manage_service",
            description="Start/stop system services",
            input_schema={
                "type": "object",
                "properties": {
                    "service": {"type": "string", "description": "Service name"},
                    "action": {"type": "string", "enum": ["start", "stop", "restart"], "description": "Action to perform"}
                },
                "required": ["service", "action"]
            },
            handler=self._handle_manage_service
        )

    async def _register_agent_tools(self):
        """Register multi-agent tools"""
        if 'archon' not in self.integration_instances:
            return

        # Agent Creation
        self._register_tool(
            name="agent_create",
            description="Create new AI agent",
            input_schema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Agent name"},
                    "type": {"type": "string", "description": "Agent type"},
                    "capabilities": {"type": "array", "items": {"type": "string"}, "description": "Agent capabilities"},
                    "config": {"type": "object", "description": "Agent configuration"}
                },
                "required": ["name", "type"]
            },
            handler=self._handle_create_agent
        )

        # Agent Communication
        self._register_tool(
            name="agent_communicate",
            description="Send message to agent",
            input_schema={
                "type": "object",
                "properties": {
                    "agent_id": {"type": "string", "description": "Agent ID"},
                    "message": {"type": "string", "description": "Message content"},
                    "context": {"type": "object", "description": "Message context"}
                },
                "required": ["agent_id", "message"]
            },
            handler=self._handle_agent_communicate
        )

    async def _register_memory_tools(self):
        """Register memory and learning tools"""
        # Memory Query
        self._register_tool(
            name="memory_query",
            description="Query conversation memory",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "limit": {"type": "integer", "description": "Result limit", "default": 10},
                    "context": {"type": "object", "description": "Search context"}
                },
                "required": ["query"]
            },
            handler=self._handle_memory_query
        )

        # Memory Store
        self._register_tool(
            name="memory_store",
            description="Store information in memory",
            input_schema={
                "type": "object",
                "properties": {
                    "content": {"type": "string", "description": "Content to store"},
                    "metadata": {"type": "object", "description": "Additional metadata"},
                    "tags": {"type": "array", "items": {"type": "string"}, "description": "Content tags"}
                },
                "required": ["content"]
            },
            handler=self._handle_memory_store
        )

    async def _register_terminal_tools(self):
        """Register terminal and CLI tools"""
        if 'charm' not in self.integration_instances:
            return

        # Terminal Command
        self._register_tool(
            name="terminal_execute",
            description="Execute terminal command",
            input_schema={
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Command to execute"},
                    "working_dir": {"type": "string", "description": "Working directory"},
                    "timeout": {"type": "integer", "description": "Command timeout in seconds"}
                },
                "required": ["command"]
            },
            handler=self._handle_terminal_execute
        )

        # Interactive Menu
        self._register_tool(
            name="terminal_interactive",
            description="Create interactive terminal menu",
            input_schema={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Menu title"},
                    "options": {"type": "array", "items": {"type": "string"}, "description": "Menu options"}
                },
                "required": ["title", "options"]
            },
            handler=self._handle_terminal_interactive
        )

    async def _register_docker_gateway_tools(self):
        """Register Docker MCP Gateway tools"""
        if not DOCKER_MCP_GATEWAY_AVAILABLE:
            return

        try:
            # Initialize Docker MCP Gateway if not already done
            if not hasattr(self, 'docker_gateway'):
                self.docker_gateway = docker_mcp_gateway
                await self.docker_gateway.initialize()

            # Gateway Status
            self._register_tool(
                name="docker_gateway_status",
                description="Get Docker MCP Gateway status and information",
                input_schema={"type": "object", "properties": {}},
                handler=self._handle_docker_gateway_status
            )

            # List Catalogs
            self._register_tool(
                name="docker_list_catalogs",
                description="List available MCP catalogs in Docker gateway",
                input_schema={"type": "object", "properties": {}},
                handler=self._handle_docker_list_catalogs
            )

            # List Servers
            self._register_tool(
                name="docker_list_servers",
                description="List available MCP servers in Docker gateway",
                input_schema={"type": "object", "properties": {}},
                handler=self._handle_docker_list_servers
            )

            # List Tools
            self._register_tool(
                name="docker_list_tools",
                description="List available tools from Docker MCP servers",
                input_schema={
                    "type": "object",
                    "properties": {
                        "server_name": {"type": "string", "description": "Specific server name (optional)"}
                    }
                },
                handler=self._handle_docker_list_tools
            )

            # Start Server
            self._register_tool(
                name="docker_start_server",
                description="Start a Docker MCP server",
                input_schema={
                    "type": "object",
                    "properties": {
                        "server_name": {"type": "string", "description": "Server name to start"}
                    },
                    "required": ["server_name"]
                },
                handler=self._handle_docker_start_server
            )

            # Stop Server
            self._register_tool(
                name="docker_stop_server",
                description="Stop a Docker MCP server",
                input_schema={
                    "type": "object",
                    "properties": {
                        "server_name": {"type": "string", "description": "Server name to stop"}
                    },
                    "required": ["server_name"]
                },
                handler=self._handle_docker_stop_server
            )

            # Execute Tool
            self._register_tool(
                name="docker_execute_tool",
                description="Execute a tool on a Docker MCP server",
                input_schema={
                    "type": "object",
                    "properties": {
                        "server_name": {"type": "string", "description": "Server name"},
                        "tool_name": {"type": "string", "description": "Tool name to execute"},
                        "arguments": {"type": "object", "description": "Tool arguments"}
                    },
                    "required": ["server_name", "tool_name"]
                },
                handler=self._handle_docker_execute_tool
            )

            # Add Server
            self._register_tool(
                name="docker_add_server",
                description="Add a new Docker MCP server",
                input_schema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Server name"},
                        "image": {"type": "string", "description": "Docker image"},
                        "port": {"type": "integer", "description": "Port number"},
                        "environment": {"type": "object", "description": "Environment variables"},
                        "volumes": {"type": "array", "items": {"type": "string"}, "description": "Volume mappings"},
                        "secrets": {"type": "array", "items": {"type": "string"}, "description": "Secret names"}
                    },
                    "required": ["name", "image", "port"]
                },
                handler=self._handle_docker_add_server
            )

            # Remove Server
            self._register_tool(
                name="docker_remove_server",
                description="Remove a Docker MCP server",
                input_schema={
                    "type": "object",
                    "properties": {
                        "server_name": {"type": "string", "description": "Server name to remove"}
                    },
                    "required": ["server_name"]
                },
                handler=self._handle_docker_remove_server
            )

            logger.info("Docker MCP Gateway tools registered successfully")

        except Exception as e:
            logger.error(f"Failed to register Docker MCP Gateway tools: {e}")

    async def _register_ui_tars_tools(self):
        """Register UI-TARS integration tools"""
        if not UI_TARS_INTEGRATION_AVAILABLE:
            logger.warning("UI-TARS integration not available, skipping tool registration")
            return

        try:
            # Initialize UI-TARS integration if not already done
            if 'ui_tars' not in self.integration_instances:
                self.integration_instances['ui_tars'] = UITarsIntegration()

            ui_tars = self.integration_instances['ui_tars']

            # UI-TARS Session Management
            self._register_tool(
                name="ui_tars_start_session",
                description="Start UI-TARS automation session",
                input_schema={
                    "type": "object",
                    "properties": {
                        "provider": {"type": "string", "description": "Model provider (volcengine, openai, anthropic, local)", "default": "volcengine"},
                        "model": {"type": "string", "description": "Model name", "default": "doubao-1-5-thinking-vision-pro-250428"},
                        "api_key": {"type": "string", "description": "API key (optional)"},
                        "max_steps": {"type": "integer", "description": "Maximum automation steps", "default": 50}
                    }
                },
                handler=self._handle_ui_tars_start_session
            )

            self._register_tool(
                name="ui_tars_stop_session",
                description="Stop UI-TARS automation session",
                input_schema={"type": "object", "properties": {}},
                handler=self._handle_ui_tars_stop_session
            )

            # UI-TARS Actions
            self._register_tool(
                name="ui_tars_screenshot",
                description="Take screenshot of current screen",
                input_schema={
                    "type": "object",
                    "properties": {
                        "analysis": {"type": "boolean", "description": "Enable AI analysis", "default": True}
                    }
                },
                handler=self._handle_ui_tars_screenshot
            )

            self._register_tool(
                name="ui_tars_click",
                description="Click on UI element",
                input_schema={
                    "type": "object",
                    "properties": {
                        "element": {"type": "string", "description": "Element description to click"},
                        "context": {"type": "object", "description": "Additional context (window, application, etc.)"}
                    },
                    "required": ["element"]
                },
                handler=self._handle_ui_tars_click
            )

            self._register_tool(
                name="ui_tars_type",
                description="Type text using keyboard",
                input_schema={
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "Text to type"},
                        "element": {"type": "string", "description": "Target element description (optional)"},
                        "context": {"type": "object", "description": "Additional context"}
                    },
                    "required": ["text"]
                },
                handler=self._handle_ui_tars_type
            )

            self._register_tool(
                name="ui_tars_open_application",
                description="Open application",
                input_schema={
                    "type": "object",
                    "properties": {
                        "application": {"type": "string", "description": "Application name to open"}
                    },
                    "required": ["application"]
                },
                handler=self._handle_ui_tars_open_application
            )

            self._register_tool(
                name="ui_tars_navigate_to_url",
                description="Navigate to URL in browser",
                input_schema={
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "URL to navigate to"}
                    },
                    "required": ["url"]
                },
                handler=self._handle_ui_tars_navigate_to_url
            )

            self._register_tool(
                name="ui_tars_find_element",
                description="Find UI element on screen",
                input_schema={
                    "type": "object",
                    "properties": {
                        "element": {"type": "string", "description": "Element description to find"}
                    },
                    "required": ["element"]
                },
                handler=self._handle_ui_tars_find_element
            )

            self._register_tool(
                name="ui_tars_wait_for_element",
                description="Wait for element to appear",
                input_schema={
                    "type": "object",
                    "properties": {
                        "element": {"type": "string", "description": "Element to wait for"},
                        "timeout": {"type": "integer", "description": "Timeout in seconds", "default": 30}
                    },
                    "required": ["element"]
                },
                handler=self._handle_ui_tars_wait_for_element
            )

            self._register_tool(
                name="ui_tars_get_screen_info",
                description="Get current screen information",
                input_schema={"type": "object", "properties": {}},
                handler=self._handle_ui_tars_get_screen_info
            )

            self._register_tool(
                name="ui_tars_list_applications",
                description="List running applications",
                input_schema={"type": "object", "properties": {}},
                handler=self._handle_ui_tars_list_applications
            )

            self._register_tool(
                name="ui_tars_close_application",
                description="Close application",
                input_schema={
                    "type": "object",
                    "properties": {
                        "application": {"type": "string", "description": "Application name to close"}
                    },
                    "required": ["application"]
                },
                handler=self._handle_ui_tars_close_application
            )

            self._register_tool(
                name="ui_tars_workflow",
                description="Execute multi-step workflow",
                input_schema={
                    "type": "object",
                    "properties": {
                        "steps": {"type": "array", "description": "List of workflow steps"},
                        "description": {"type": "string", "description": "Natural language workflow description"}
                    }
                },
                handler=self._handle_ui_tars_workflow
            )

            logger.info("UI-TARS integration tools registered successfully")

        except Exception as e:
            logger.error(f"Failed to register UI-TARS tools: {e}")

    async def _register_deepcode_tools(self):
        """Register DeepCode integration tools"""
        if not DEEPCODE_AVAILABLE:
            logger.warning("DeepCode integration not available, skipping tool registration")
            return

        try:
            # Initialize DeepCode integration if not already done
            if 'deepcode' not in self.integration_instances:
                try:
                    self.integration_instances['deepcode'] = DuckBotDeepCodeIntegration()
                except:
                    logger.warning("Failed to initialize DeepCode integration")
                    return

            # Paper2Code Tool
            self._register_tool(
                name="deepcode_paper2code",
                description="Convert research papers to executable code",
                input_schema={
                    "type": "object",
                    "properties": {
                        "paper_path": {"type": "string", "description": "Path to research paper (PDF)"},
                        "output_dir": {"type": "string", "description": "Output directory for generated code"},
                        "language": {"type": "string", "description": "Target programming language", "default": "python"},
                        "framework": {"type": "string", "description": "Target framework (optional)"}
                    },
                    "required": ["paper_path", "output_dir"]
                },
                handler=self._handle_deepcode_paper2code
            )

            # Text2Web Tool
            self._register_tool(
                name="deepcode_text2web",
                description="Convert text descriptions to web applications",
                input_schema={
                    "type": "object",
                    "properties": {
                        "description": {"type": "string", "description": "Text description of web application"},
                        "output_dir": {"type": "string", "description": "Output directory"},
                        "framework": {"type": "string", "enum": ["react", "vue", "angular", "html"], "default": "react"},
                        "features": {"type": "array", "items": {"type": "string"}, "description": "Required features"}
                    },
                    "required": ["description", "output_dir"]
                },
                handler=self._handle_deepcode_text2web
            )

            # Text2Backend Tool
            self._register_tool(
                name="deepcode_text2backend",
                description="Convert text descriptions to backend APIs",
                input_schema={
                    "type": "object",
                    "properties": {
                        "description": {"type": "string", "description": "Text description of backend API"},
                        "output_dir": {"type": "string", "description": "Output directory"},
                        "framework": {"type": "string", "enum": ["fastapi", "express", "django", "flask"], "default": "fastapi"},
                        "database": {"type": "string", "description": "Database type (optional)"}
                    },
                    "required": ["description", "output_dir"]
                },
                handler=self._handle_deepcode_text2backend
            )

            # DeepCode Analysis Tool
            self._register_tool(
                name="deepcode_analyze",
                description="Analyze code with DeepCode AI",
                input_schema={
                    "type": "object",
                    "properties": {
                        "code_path": {"type": "string", "description": "Path to code to analyze"},
                        "analysis_type": {"type": "string", "enum": ["quality", "security", "performance", "maintainability"], "default": "quality"},
                        "language": {"type": "string", "description": "Programming language"}
                    },
                    "required": ["code_path"]
                },
                handler=self._handle_deepcode_analyze
            )

            logger.info("DeepCode integration tools registered successfully")

        except Exception as e:
            logger.error(f"Failed to register DeepCode tools: {e}")

    async def _register_rag_tools(self):
        """Register Enhanced RAG tools"""
        if not ENHANCED_RAG_AVAILABLE:
            logger.warning("Enhanced RAG integration not available, skipping tool registration")
            return

        try:
            # Initialize Enhanced RAG components
            if 'rag_engine' not in self.integration_instances:
                try:
                    self.integration_instances['rag_engine'] = EnhancedRAGEngine()
                except:
                    logger.warning("Failed to initialize Enhanced RAG engine")
                    return

            if 'rag_ai' not in self.integration_instances:
                try:
                    self.integration_instances['rag_ai'] = RAGAIIntegration()
                except:
                    logger.warning("Failed to initialize RAG AI integration")
                    return

            if 'rag_memory' not in self.integration_instances:
                try:
                    self.integration_instances['rag_memory'] = RAGMemoryIntegration()
                except:
                    logger.warning("Failed to initialize RAG memory integration")
                    return

            if 'rag_agent' not in self.integration_instances:
                try:
                    self.integration_instances['rag_agent'] = RAGAgentIntegration()
                except:
                    logger.warning("Failed to initialize RAG agent integration")
                    return

            # RAG Document Processing
            self._register_tool(
                name="rag_process_document",
                description="Process and index document for RAG",
                input_schema={
                    "type": "object",
                    "properties": {
                        "document_path": {"type": "string", "description": "Path to document to process"},
                        "collection_name": {"type": "string", "description": "Collection name (optional)"},
                        "metadata": {"type": "object", "description": "Document metadata"}
                    },
                    "required": ["document_path"]
                },
                handler=self._handle_rag_process_document
            )

            # RAG Query
            self._register_tool(
                name="rag_query",
                description="Query RAG system for information",
                input_schema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Query text"},
                        "collection_name": {"type": "string", "description": "Collection name (optional)"},
                        "limit": {"type": "integer", "description": "Result limit", "default": 5},
                        "threshold": {"type": "number", "description": "Similarity threshold", "default": 0.7}
                    },
                    "required": ["query"]
                },
                handler=self._handle_rag_query
            )

            # RAG Create Collection
            self._register_tool(
                name="rag_create_collection",
                description="Create new RAG collection",
                input_schema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Collection name"},
                        "description": {"type": "string", "description": "Collection description"},
                        "embedding_model": {"type": "string", "description": "Embedding model (optional)"}
                    },
                    "required": ["name"]
                },
                handler=self._handle_rag_create_collection
            )

            # RAG List Collections
            self._register_tool(
                name="rag_list_collections",
                description="List RAG collections",
                input_schema={"type": "object", "properties": {}},
                handler=self._handle_rag_list_collections
            )

            # RAG Delete Collection
            self._register_tool(
                name="rag_delete_collection",
                description="Delete RAG collection",
                input_schema={
                    "type": "object",
                    "properties": {
                        "collection_name": {"type": "string", "description": "Collection name"}
                    },
                    "required": ["collection_name"]
                },
                handler=self._handle_rag_delete_collection
            )

            # RAG AI Integration
            self._register_tool(
                name="rag_ai_enhance",
                description="Enhance AI responses with RAG context",
                input_schema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Original query"},
                        "collection_name": {"type": "string", "description": "Collection name (optional)"},
                        "provider": {"type": "string", "description": "AI provider (optional)"},
                        "model": {"type": "string", "description": "AI model (optional)"}
                    },
                    "required": ["query"]
                },
                handler=self._handle_rag_ai_enhance
            )

            # RAG Memory Integration
            self._register_tool(
                name="rag_memory_store",
                description="Store conversation in RAG memory",
                input_schema={
                    "type": "object",
                    "properties": {
                        "conversation": {"type": "string", "description": "Conversation content"},
                        "metadata": {"type": "object", "description": "Conversation metadata"},
                        "collection_name": {"type": "string", "description": "Collection name (optional)"}
                    },
                    "required": ["conversation"]
                },
                handler=self._handle_rag_memory_store
            )

            # RAG Agent Integration
            self._register_tool(
                name="rag_agent_query",
                description="Query RAG system via agent",
                input_schema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Query for agent"},
                        "agent_type": {"type": "string", "description": "Agent type (optional)"},
                        "collection_name": {"type": "string", "description": "Collection name (optional)"}
                    },
                    "required": ["query"]
                },
                handler=self._handle_rag_agent_query
            )

            logger.info("Enhanced RAG tools registered successfully")

        except Exception as e:
            logger.error(f"Failed to register Enhanced RAG tools: {e}")

    # DeepCode Tool Handlers
    async def _handle_deepcode_paper2code(self, params: dict) -> dict:
        """Handle DeepCode Paper2Code"""
        try:
            if 'deepcode' not in self.integration_instances:
                return {"success": False, "error": "DeepCode integration not available"}

            deepcode = self.integration_instances['deepcode']
            result = await deepcode.paper2code(
                paper_path=params['paper_path'],
                output_dir=params['output_dir'],
                language=params.get('language', 'python'),
                framework=params.get('framework')
            )

            return {
                "success": True,
                "result": result,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"DeepCode Paper2Code failed: {e}")
            return {"success": False, "error": str(e)}

    async def _handle_deepcode_text2web(self, params: dict) -> dict:
        """Handle DeepCode Text2Web"""
        try:
            if 'deepcode' not in self.integration_instances:
                return {"success": False, "error": "DeepCode integration not available"}

            deepcode = self.integration_instances['deepcode']
            result = await deepcode.text2web(
                description=params['description'],
                output_dir=params['output_dir'],
                framework=params.get('framework', 'react'),
                features=params.get('features', [])
            )

            return {
                "success": True,
                "result": result,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"DeepCode Text2Web failed: {e}")
            return {"success": False, "error": str(e)}

    async def _handle_deepcode_text2backend(self, params: dict) -> dict:
        """Handle DeepCode Text2Backend"""
        try:
            if 'deepcode' not in self.integration_instances:
                return {"success": False, "error": "DeepCode integration not available"}

            deepcode = self.integration_instances['deepcode']
            result = await deepcode.text2backend(
                description=params['description'],
                output_dir=params['output_dir'],
                framework=params.get('framework', 'fastapi'),
                database=params.get('database')
            )

            return {
                "success": True,
                "result": result,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"DeepCode Text2Backend failed: {e}")
            return {"success": False, "error": str(e)}

    async def _handle_deepcode_analyze(self, params: dict) -> dict:
        """Handle DeepCode code analysis"""
        try:
            if 'deepcode' not in self.integration_instances:
                return {"success": False, "error": "DeepCode integration not available"}

            deepcode = self.integration_instances['deepcode']
            result = await deepcode.analyze_code(
                code_path=params['code_path'],
                analysis_type=params.get('analysis_type', 'quality'),
                language=params.get('language')
            )

            return {
                "success": True,
                "result": result,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"DeepCode analysis failed: {e}")
            return {"success": False, "error": str(e)}

    # Enhanced RAG Tool Handlers
    async def _handle_rag_process_document(self, params: dict) -> dict:
        """Handle RAG document processing"""
        try:
            if 'rag_engine' not in self.integration_instances:
                return {"success": False, "error": "RAG engine not available"}

            rag_engine = self.integration_instances['rag_engine']
            result = await rag_engine.process_document(
                document_path=params['document_path'],
                collection_name=params.get('collection_name'),
                metadata=params.get('metadata', {})
            )

            return {
                "success": True,
                "result": result,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"RAG document processing failed: {e}")
            return {"success": False, "error": str(e)}

    async def _handle_rag_query(self, params: dict) -> dict:
        """Handle RAG query"""
        try:
            if 'rag_engine' not in self.integration_instances:
                return {"success": False, "error": "RAG engine not available"}

            rag_engine = self.integration_instances['rag_engine']
            result = await rag_engine.query(
                query_text=params['query'],
                collection_name=params.get('collection_name'),
                limit=params.get('limit', 5),
                threshold=params.get('threshold', 0.7)
            )

            return {
                "success": True,
                "result": result,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"RAG query failed: {e}")
            return {"success": False, "error": str(e)}

    async def _handle_rag_create_collection(self, params: dict) -> dict:
        """Handle RAG collection creation"""
        try:
            if 'rag_engine' not in self.integration_instances:
                return {"success": False, "error": "RAG engine not available"}

            rag_engine = self.integration_instances['rag_engine']
            result = await rag_engine.create_collection(
                name=params['name'],
                description=params.get('description', ''),
                embedding_model=params.get('embedding_model')
            )

            return {
                "success": True,
                "result": result,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"RAG collection creation failed: {e}")
            return {"success": False, "error": str(e)}

    async def _handle_rag_list_collections(self, params: dict) -> dict:
        """Handle RAG collection listing"""
        try:
            if 'rag_engine' not in self.integration_instances:
                return {"success": False, "error": "RAG engine not available"}

            rag_engine = self.integration_instances['rag_engine']
            collections = await rag_engine.list_collections()

            return {
                "success": True,
                "collections": collections,
                "count": len(collections),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"RAG collection listing failed: {e}")
            return {"success": False, "error": str(e)}

    async def _handle_rag_delete_collection(self, params: dict) -> dict:
        """Handle RAG collection deletion"""
        try:
            if 'rag_engine' not in self.integration_instances:
                return {"success": False, "error": "RAG engine not available"}

            rag_engine = self.integration_instances['rag_engine']
            result = await rag_engine.delete_collection(params['collection_name'])

            return {
                "success": True,
                "result": result,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"RAG collection deletion failed: {e}")
            return {"success": False, "error": str(e)}

    async def _handle_rag_ai_enhance(self, params: dict) -> dict:
        """Handle RAG AI enhancement"""
        try:
            if 'rag_ai' not in self.integration_instances:
                return {"success": False, "error": "RAG AI integration not available"}

            rag_ai = self.integration_instances['rag_ai']
            result = await rag_ai.enhance_response(
                query=params['query'],
                collection_name=params.get('collection_name'),
                provider=params.get('provider'),
                model=params.get('model')
            )

            return {
                "success": True,
                "result": result,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"RAG AI enhancement failed: {e}")
            return {"success": False, "error": str(e)}

    async def _handle_rag_memory_store(self, params: dict) -> dict:
        """Handle RAG memory storage"""
        try:
            if 'rag_memory' not in self.integration_instances:
                return {"success": False, "error": "RAG memory integration not available"}

            rag_memory = self.integration_instances['rag_memory']
            result = await rag_memory.store_conversation(
                conversation=params['conversation'],
                metadata=params.get('metadata', {}),
                collection_name=params.get('collection_name')
            )

            return {
                "success": True,
                "result": result,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"RAG memory storage failed: {e}")
            return {"success": False, "error": str(e)}

    async def _handle_rag_agent_query(self, params: dict) -> dict:
        """Handle RAG agent query"""
        try:
            if 'rag_agent' not in self.integration_instances:
                return {"success": False, "error": "RAG agent integration not available"}

            rag_agent = self.integration_instances['rag_agent']
            result = await rag_agent.agent_query(
                query=params['query'],
                agent_type=params.get('agent_type'),
                collection_name=params.get('collection_name')
            )

            return {
                "success": True,
                "result": result,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"RAG agent query failed: {e}")
            return {"success": False, "error": str(e)}

    # UI-TARS Tool Handlers
    async def _handle_ui_tars_start_session(self, params: dict) -> dict:
        """Handle UI-TARS session start"""
        try:
            from duckbot.integrations.ui_tars_integration import UITarsIntegration

            ui_tars = UITarsIntegration()

            # Configure with provided parameters
            if params.get('provider'):
                ui_tars.config.provider = params['provider']
            if params.get('model'):
                ui_tars.config.model = params['model']
            if params.get('api_key'):
                ui_tars.config.api_key = params['api_key']
            if params.get('max_steps'):
                ui_tars.config.max_steps = params['max_steps']

            success = await ui_tars.start_session()
            return {
                "success": success,
                "status": ui_tars.get_status()
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _handle_ui_tars_stop_session(self, params: dict) -> dict:
        """Handle UI-TARS session stop"""
        try:
            from duckbot.integrations.ui_tars_integration import UITarsIntegration

            ui_tars = UITarsIntegration()
            success = await ui_tars.stop_session()
            return {
                "success": success,
                "status": ui_tars.get_status()
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _handle_ui_tars_screenshot(self, params: dict) -> dict:
        """Handle UI-TARS screenshot"""
        try:
            from duckbot.integrations.ui_tars_integration import UITarsIntegration

            ui_tars = UITarsIntegration()
            result = await ui_tars.take_screenshot()
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _handle_ui_tars_click(self, params: dict) -> dict:
        """Handle UI-TARS click"""
        try:
            from duckbot.integrations.ui_tars_integration import UITarsIntegration

            ui_tars = UITarsIntegration()
            result = await ui_tars.click_element(
                params['element'],
                params.get('context')
            )
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _handle_ui_tars_type(self, params: dict) -> dict:
        """Handle UI-TARS type"""
        try:
            from duckbot.integrations.ui_tars_integration import UITarsIntegration

            ui_tars = UITarsIntegration()
            result = await ui_tars.type_text(
                params['text'],
                params.get('context')
            )
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _handle_ui_tars_open_application(self, params: dict) -> dict:
        """Handle UI-TARS open application"""
        try:
            from duckbot.integrations.ui_tars_integration import UITarsIntegration

            ui_tars = UITarsIntegration()
            result = await ui_tars.open_application(params['application'])
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _handle_ui_tars_navigate_to_url(self, params: dict) -> dict:
        """Handle UI-TARS navigate to URL"""
        try:
            from duckbot.integrations.ui_tars_integration import UITarsIntegration

            ui_tars = UITarsIntegration()
            result = await ui_tars.navigate_to_url(params['url'])
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _handle_ui_tars_find_element(self, params: dict) -> dict:
        """Handle UI-TARS find element"""
        try:
            from duckbot.integrations.ui_tars_integration import UITarsIntegration

            ui_tars = UITarsIntegration()
            result = await ui_tars.find_element(params['element'])
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _handle_ui_tars_wait_for_element(self, params: dict) -> dict:
        """Handle UI-TARS wait for element"""
        try:
            from duckbot.integrations.ui_tars_integration import UITarsIntegration

            ui_tars = UITarsIntegration()
            result = await ui_tars.wait_for_element(
                params['element'],
                params.get('timeout', 30)
            )
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _handle_ui_tars_get_screen_info(self, params: dict) -> dict:
        """Handle UI-TARS get screen info"""
        try:
            from duckbot.integrations.ui_tars_integration import UITarsIntegration

            ui_tars = UITarsIntegration()
            result = await ui_tars.get_screen_info()
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _handle_ui_tars_list_applications(self, params: dict) -> dict:
        """Handle UI-TARS list applications"""
        try:
            from duckbot.integrations.ui_tars_integration import UITarsIntegration

            ui_tars = UITarsIntegration()
            result = await ui_tars.list_running_applications()
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _handle_ui_tars_close_application(self, params: dict) -> dict:
        """Handle UI-TARS close application"""
        try:
            from duckbot.integrations.ui_tars_integration import UITarsIntegration

            ui_tars = UITarsIntegration()
            result = await ui_tars.close_application(params['application'])
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _handle_ui_tars_workflow(self, params: dict) -> dict:
        """Handle UI-TARS workflow execution"""
        try:
            from duckbot.integrations.ui_tars_integration import UITarsIntegration

            ui_tars = UITarsIntegration()

            if 'steps' in params:
                # Execute predefined workflow
                result = await ui_tars.perform_workflow(params['steps'])
            elif 'description' in params:
                # Use AI to interpret natural language workflow
                result = await ui_tars.execute_command(params['description'])
            else:
                return {"success": False, "error": "Either steps or description required"}

            return result
        except Exception as e:
            return {"success": False, "error": str(e)}

    # Docker MCP Gateway Tool Handlers
    async def _handle_docker_gateway_status(self, arguments: dict) -> dict:
        """Handle Docker MCP Gateway status request"""
        try:
            status = await self.docker_gateway.get_gateway_status()
            return {"success": True, "status": status}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _handle_docker_list_catalogs(self, arguments: dict) -> dict:
        """Handle Docker MCP Gateway catalog listing"""
        try:
            catalogs = await self.docker_gateway.list_catalogs()
            return {"success": True, "catalogs": catalogs}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _handle_docker_list_servers(self, arguments: dict) -> dict:
        """Handle Docker MCP Gateway server listing"""
        try:
            servers = await self.docker_gateway.list_servers()
            return {"success": True, "servers": servers}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _handle_docker_list_tools(self, arguments: dict) -> dict:
        """Handle Docker MCP Gateway tool listing"""
        try:
            server_name = arguments.get("server_name")
            tools = await self.docker_gateway.list_tools(server_name)
            return {"success": True, "tools": tools}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _handle_docker_start_server(self, arguments: dict) -> dict:
        """Handle Docker MCP Gateway server start"""
        try:
            server_name = arguments["server_name"]
            result = await self.docker_gateway.start_server(server_name)
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _handle_docker_stop_server(self, arguments: dict) -> dict:
        """Handle Docker MCP Gateway server stop"""
        try:
            server_name = arguments["server_name"]
            result = await self.docker_gateway.stop_server(server_name)
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _handle_docker_execute_tool(self, arguments: dict) -> dict:
        """Handle Docker MCP Gateway tool execution"""
        try:
            server_name = arguments["server_name"]
            tool_name = arguments["tool_name"]
            tool_args = arguments.get("arguments", {})
            result = await self.docker_gateway.execute_tool(server_name, tool_name, tool_args)
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _handle_docker_add_server(self, arguments: dict) -> dict:
        """Handle Docker MCP Gateway server addition"""
        try:
            server_config = DockerMCPServer(
                name=arguments["name"],
                image=arguments["image"],
                port=arguments["port"],
                environment=arguments.get("environment", {}),
                volumes=arguments.get("volumes", []),
                secrets=arguments.get("secrets", [])
            )
            result = await self.docker_gateway.add_server(server_config)
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _handle_docker_remove_server(self, arguments: dict) -> dict:
        """Handle Docker MCP Gateway server removal"""
        try:
            server_name = arguments["server_name"]
            result = await self.docker_gateway.remove_server(server_name)
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _register_resources(self):
        """Register DuckBot resources with MCP server"""
        if not MCP_AVAILABLE:
            return

        # System Resources
        self._register_resource(
            name="system_info",
            description="System information and capabilities",
            uri="duckbot://system/info",
            mime_type="application/json",
            handler=self._get_system_info
        )

        # Agent Resources
        self._register_resource(
            name="agent_registry",
            description="Available AI agents and their capabilities",
            uri="duckbot://agents/registry",
            mime_type="application/json",
            handler=self._get_agent_registry
        )

        # Memory Resources
        self._register_resource(
            name="memory_index",
            description="Conversation memory index",
            uri="duckbot://memory/index",
            mime_type="application/json",
            handler=self._get_memory_index
        )

        logger.info(f"Registered {len(self.resources)} MCP resources")

    def _register_tool(self, name: str, description: str, input_schema: dict, handler: Callable):
        """Register a tool with the MCP server"""
        self.tools[name] = {
            "name": name,
            "description": description,
            "input_schema": input_schema,
            "handler": handler
        }

        if MCP_AVAILABLE and hasattr(self.server, 'register_tool'):
            tool = Tool(
                name=name,
                description=description,
                input_schema=input_schema
            )
            self.server.register_tool(tool, handler)

    def _register_resource(self, name: str, description: str, uri: str, mime_type: str, handler: Callable):
        """Register a resource with the MCP server"""
        self.resources[name] = {
            "name": name,
            "description": description,
            "uri": uri,
            "mime_type": mime_type,
            "handler": handler
        }

        if MCP_AVAILABLE and hasattr(self.server, 'register_resource'):
            resource = Resource(
                name=name,
                description=description,
                uri=uri,
                mime_type=mime_type
            )
            self.server.register_resource(resource, handler)

    def _setup_event_handlers(self):
        """Set up MCP server event handlers"""
        if not MCP_AVAILABLE:
            return

        # Client connection events
        if hasattr(self.server, 'on_client_connect'):
            self.server.on_client_connect(self._handle_client_connect)

        if hasattr(self.server, 'on_client_disconnect'):
            self.server.on_client_disconnect(self._handle_client_disconnect)

        # Tool execution events
        if hasattr(self.server, 'on_tool_execute'):
            self.server.on_tool_execute(self._handle_tool_execute)

        # Resource access events
        if hasattr(self.server, 'on_resource_access'):
            self.server.on_resource_access(self._handle_resource_access)

    # Tool Handlers
    async def _handle_ai_route_task(self, params: dict) -> dict:
        """Handle AI task routing"""
        try:
            task = params.get("task")
            provider = params.get("provider")
            model = params.get("model")
            context = params.get("context", {})

            result = await route_task(
                task=task,
                provider=provider,
                model=model,
                context=context
            )

            return {
                "success": True,
                "result": result,
                "provider": provider or "auto-selected",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"AI task routing failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def _handle_list_providers(self, params: dict) -> dict:
        """Handle provider listing"""
        try:
            providers = get_available_providers()
            return {
                "success": True,
                "providers": providers,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Provider listing failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def _handle_switch_provider(self, params: dict) -> dict:
        """Handle provider switching"""
        try:
            provider = params.get("provider")
            api_key = params.get("api_key")

            result = await connector_manager.switch_provider(provider, api_key)
            return {
                "success": result,
                "provider": provider,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Provider switching failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def _handle_screenshot(self, params: dict) -> dict:
        """Handle screenshot capture and analysis"""
        try:
            if 'bytebot' not in self.integration_instances:
                return {"success": False, "error": "ByteBot integration not available"}

            bytebot = self.integration_instances['bytebot']
            analysis = params.get("analysis", True)

            # Take screenshot
            screenshot_path = await bytebot.take_screenshot()

            result = {
                "success": True,
                "screenshot_path": str(screenshot_path),
                "timestamp": datetime.now().isoformat()
            }

            # Analyze screenshot if requested
            if analysis:
                analysis_result = await bytebot.analyze_screenshot(screenshot_path)
                result["analysis"] = analysis_result

            return result
        except Exception as e:
            logger.error(f"Screenshot capture failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def _handle_mouse_click(self, params: dict) -> dict:
        """Handle mouse click"""
        try:
            if 'bytebot' not in self.integration_instances:
                return {"success": False, "error": "ByteBot integration not available"}

            bytebot = self.integration_instances['bytebot']
            x = params.get("x")
            y = params.get("y")
            button = params.get("button", "left")

            await bytebot.click_at(x, y, button)

            return {
                "success": True,
                "position": {"x": x, "y": y},
                "button": button,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Mouse click failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def _handle_type_text(self, params: dict) -> dict:
        """Handle text typing"""
        try:
            if 'bytebot' not in self.integration_instances:
                return {"success": False, "error": "ByteBot integration not available"}

            bytebot = self.integration_instances['bytebot']
            text = params.get("text")
            delay = params.get("delay")

            await bytebot.type_text(text, delay)

            return {
                "success": True,
                "text": text,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Text typing failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def _handle_system_status(self, params: dict) -> dict:
        """Handle system status request"""
        try:
            import psutil

            status = {
                "cpu_usage": psutil.cpu_percent(),
                "memory_usage": psutil.virtual_memory().percent,
                "disk_usage": psutil.disk_usage('/').percent,
                "timestamp": datetime.now().isoformat()
            }

            return {
                "success": True,
                "status": status
            }
        except Exception as e:
            logger.error(f"System status failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def _handle_list_processes(self, params: dict) -> dict:
        """Handle process listing"""
        try:
            import psutil

            filter_name = params.get("filter")
            processes = []

            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    proc_info = proc.info
                    if filter_name and filter_name.lower() not in proc_info['name'].lower():
                        continue
                    processes.append(proc_info)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue

            return {
                "success": True,
                "processes": processes[:50],  # Limit results
                "count": len(processes),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Process listing failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def _handle_manage_service(self, params: dict) -> dict:
        """Handle service management"""
        try:
            if 'server_manager' not in self.integration_instances:
                return {"success": False, "error": "Server manager not available"}

            manager = self.integration_instances['server_manager']
            service = params.get("service")
            action = params.get("action")

            if action == "start":
                result = await manager.start_service(service)
            elif action == "stop":
                result = await manager.stop_service(service)
            elif action == "restart":
                result = await manager.restart_service(service)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}

            return {
                "success": result,
                "service": service,
                "action": action,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Service management failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def _handle_create_agent(self, params: dict) -> dict:
        """Handle agent creation"""
        try:
            if 'archon' not in self.integration_instances:
                return {"success": False, "error": "Archon integration not available"}

            archon = self.integration_instances['archon']
            name = params.get("name")
            agent_type = params.get("type")
            capabilities = params.get("capabilities", [])
            config = params.get("config", {})

            agent_id = await archon.create_agent(name, agent_type, capabilities, config)

            return {
                "success": True,
                "agent_id": agent_id,
                "name": name,
                "type": agent_type,
                "capabilities": capabilities,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Agent creation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def _handle_agent_communicate(self, params: dict) -> dict:
        """Handle agent communication"""
        try:
            if 'archon' not in self.integration_instances:
                return {"success": False, "error": "Archon integration not available"}

            archon = self.integration_instances['archon']
            agent_id = params.get("agent_id")
            message = params.get("message")
            context = params.get("context", {})

            response = await archon.communicate_with_agent(agent_id, message, context)

            return {
                "success": True,
                "agent_id": agent_id,
                "message": message,
                "response": response,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Agent communication failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def _handle_memory_query(self, params: dict) -> dict:
        """Handle memory query"""
        try:
            query = params.get("query")
            limit = params.get("limit", 10)
            context = params.get("context", {})

            if MEMENTO_INTEGRATION_AVAILABLE:
                results = await execute_memento_task("query", {
                    "query": query,
                    "limit": limit,
                    "context": context
                })
            else:
                # Fallback memory implementation
                results = []

            return {
                "success": True,
                "query": query,
                "results": results,
                "count": len(results),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Memory query failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def _handle_memory_store(self, params: dict) -> dict:
        """Handle memory storage"""
        try:
            content = params.get("content")
            metadata = params.get("metadata", {})
            tags = params.get("tags", [])

            if MEMENTO_INTEGRATION_AVAILABLE:
                result = await execute_memento_task("store", {
                    "content": content,
                    "metadata": metadata,
                    "tags": tags
                })
            else:
                # Fallback storage
                result = {"stored": True, "id": str(uuid.uuid4())}

            return {
                "success": True,
                "content": content,
                "storage_result": result,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Memory storage failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def _handle_terminal_execute(self, params: dict) -> dict:
        """Handle terminal command execution"""
        try:
            if 'charm' not in self.integration_instances:
                return {"success": False, "error": "Charm integration not available"}

            charm = self.integration_instances['charm']
            command = params.get("command")
            working_dir = params.get("working_dir")
            timeout = params.get("timeout")

            result = await charm.execute_command(command, working_dir, timeout)

            return {
                "success": True,
                "command": command,
                "result": result,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Terminal execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def _handle_terminal_interactive(self, params: dict) -> dict:
        """Handle interactive terminal menu"""
        try:
            if 'charm' not in self.integration_instances:
                return {"success": False, "error": "Charm integration not available"}

            charm = self.integration_instances['charm']
            title = params.get("title")
            options = params.get("options")

            result = await charm.create_interactive_menu(title, options)

            return {
                "success": True,
                "title": title,
                "selected_option": result,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Interactive menu failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    # Resource Handlers
    async def _get_system_info(self) -> dict:
        """Get system information resource"""
        try:
            import platform
            import psutil

            info = {
                "platform": platform.platform(),
                "python_version": platform.python_version(),
                "cpu_count": psutil.cpu_count(),
                "memory_total": psutil.virtual_memory().total,
                "disk_total": psutil.disk_usage('/').total,
                "duckbot_version": "3.1.0+",
                "mcp_version": "1.0.0",
                "integrations": list(self.integration_instances.keys()),
                "available_tools": list(self.tools.keys()),
                "available_resources": list(self.resources.keys())
            }

            return info
        except Exception as e:
            logger.error(f"System info failed: {e}")
            return {"error": str(e)}

    async def _get_agent_registry(self) -> dict:
        """Get agent registry resource"""
        try:
            if 'archon' not in self.integration_instances:
                return {"agents": []}

            archon = self.integration_instances['archon']
            agents = await archon.list_agents()

            return {
                "agents": agents,
                "count": len(agents),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Agent registry failed: {e}")
            return {"error": str(e)}

    async def _get_memory_index(self) -> dict:
        """Get memory index resource"""
        try:
            if MEMENTO_INTEGRATION_AVAILABLE:
                index = await get_memento_capabilities()
                return {
                    "memory_index": index,
                    "capabilities": index.get("capabilities", []),
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {"memory_index": [], "capabilities": []}
        except Exception as e:
            logger.error(f"Memory index failed: {e}")
            return {"error": str(e)}

    # Event Handlers
    async def _handle_client_connect(self, client_id: str, client_info: dict):
        """Handle client connection"""
        logger.info(f"MCP client connected: {client_id}")
        self.clients[client_id] = {
            "connected_at": datetime.now(),
            "info": client_info
        }

    async def _handle_client_disconnect(self, client_id: str):
        """Handle client disconnection"""
        logger.info(f"MCP client disconnected: {client_id}")
        if client_id in self.clients:
            del self.clients[client_id]

    async def _handle_tool_execute(self, tool_name: str, params: dict, client_id: str):
        """Handle tool execution"""
        logger.info(f"Tool executed: {tool_name} by client {client_id}")

        # Log tool usage for learning system
        if 'learning' in self.integration_instances:
            try:
                await self.integration_instances['learning'].log_tool_usage(
                    tool_name, params, client_id
                )
            except Exception as e:
                logger.warning(f"Failed to log tool usage: {e}")

    async def _handle_resource_access(self, resource_name: str, client_id: str):
        """Handle resource access"""
        logger.info(f"Resource accessed: {resource_name} by client {client_id}")

    # Server Management
    async def start(self, host: str = "127.0.0.1", port: int = 8790):
        """Start the MCP server"""
        try:
            # Initialize server if not already done
            if not self.server:
                await self.initialize_mcp_server()

            self.running = True
            logger.info(f"Starting DuckBot MCP server on {host}:{port}")

            if hasattr(self.server, 'start'):
                await self.server.start(host, port)
            else:
                # Fallback implementation
                await self._run_fallback_server(host, port)

        except Exception as e:
            logger.error(f"Failed to start MCP server: {e}")
            raise

    async def _run_fallback_server(self, host: str, port: int):
        """Run fallback server implementation"""
        import uvicorn
        from fastapi import FastAPI

        app = FastAPI(title="DuckBot MCP Fallback Server")

        @app.post("/tools/{tool_name}")
        async def execute_tool(tool_name: str, params: dict):
            if tool_name in self.tools:
                return await self.tools[tool_name]["handler"](params)
            return {"error": f"Tool {tool_name} not found"}

        @app.get("/resources/{resource_name}")
        async def get_resource(resource_name: str):
            if resource_name in self.resources:
                return await self.resources[resource_name]["handler"]()
            return {"error": f"Resource {resource_name} not found"}

        @app.get("/tools")
        async def list_tools():
            return {
                "tools": [
                    {
                        "name": tool["name"],
                        "description": tool["description"],
                        "input_schema": tool["input_schema"]
                    }
                    for tool in self.tools.values()
                ]
            }

        @app.get("/resources")
        async def list_resources():
            return {
                "resources": [
                    {
                        "name": resource["name"],
                        "description": resource["description"],
                        "uri": resource["uri"],
                        "mime_type": resource["mime_type"]
                    }
                    for resource in self.resources.values()
                ]
            }

        await uvicorn.run(app, host=host, port=port)

    async def stop(self):
        """Stop the MCP server"""
        try:
            self.running = False

            if self.server and hasattr(self.server, 'stop'):
                await self.server.stop()

            # Stop all integrations
            for integration in self.integration_instances.values():
                if hasattr(integration, 'stop'):
                    try:
                        await integration.stop()
                    except Exception as e:
                        logger.warning(f"Failed to stop integration: {e}")

            logger.info("DuckBot MCP server stopped")

        except Exception as e:
            logger.error(f"Failed to stop MCP server: {e}")

    def get_status(self) -> dict:
        """Get server status"""
        return {
            "running": self.running,
            "tools_count": len(self.tools),
            "resources_count": len(self.resources),
            "clients_count": len(self.clients),
            "integrations": list(self.integration_instances.keys()),
            "mcp_available": MCP_AVAILABLE,
            "timestamp": datetime.now().isoformat()
        }

    async def get_mcp_tools(self):
        """Get available MCP tools"""
        return {
            "tools": [
                {
                    "name": tool["name"],
                    "description": tool["description"],
                    "input_schema": tool["input_schema"]
                }
                for tool in self.tools.values()
            ]
        }

# Global server instance
mcp_server = DuckBotMCPServer()

async def start_mcp_server(host: str = "127.0.0.1", port: int = 8790):
    """Start the DuckBot MCP server"""
    await mcp_server.start(host, port)

async def stop_mcp_server():
    """Stop the DuckBot MCP server"""
    await mcp_server.stop()

async def get_mcp_tools():
    """Get available MCP tools"""
    return {
        "tools": [
            {
                "name": tool["name"],
                "description": tool["description"],
                "input_schema": tool["input_schema"]
            }
            for tool in mcp_server.tools.values()
        ]
    }

async def get_mcp_resources():
    """Get available MCP resources"""
    return {
        "resources": [
            {
                "name": resource["name"],
                "description": resource["description"],
                "uri": resource["uri"],
                "mime_type": resource["mime_type"]
            }
            for resource in mcp_server.resources.values()
        ]
    }

async def execute_mcp_tool(tool_name: str, params: dict):
    """Execute MCP tool"""
    if tool_name in mcp_server.tools:
        return await mcp_server.tools[tool_name]["handler"](params)
    else:
        return {
            "success": False,
            "error": f"Tool '{tool_name}' not found",
            "timestamp": datetime.now().isoformat()
        }

if __name__ == "__main__":
    import asyncio

    async def main():
        try:
            await start_mcp_server()
        except KeyboardInterrupt:
            await stop_mcp_server()

# Export mcp server instance for external use
mcp = mcp_server