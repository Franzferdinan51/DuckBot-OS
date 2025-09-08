#!/usr/bin/env python3
"""
[AI] Qwen-Agent Integration for DuckBot
Advanced agent capabilities with tool use and workflow management
"""

import os
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
import json
import asyncio
from dotenv import load_dotenv

# Load environment variables for OpenRouter configuration
load_dotenv()

try:
    from qwen_agent.agents import Assistant
    from qwen_agent.tools import BaseTool
    from qwen_agent import ConfigurableAgent
    QWEN_AGENT_AVAILABLE = True
except ImportError:
    QWEN_AGENT_AVAILABLE = False
    # Create dummy BaseTool for compatibility
    class BaseTool:
        def __init__(self):
            self.description = ""
            self.name = ""
            self.parameters = {}
        
        def call(self, params, **kwargs):
            return {"success": False, "error": "Qwen-Agent not available"}

from duckbot.server_manager import server_manager

logger = logging.getLogger(__name__)

class ServerManagementTool(BaseTool):
    """Advanced server management tool using Qwen-Agent framework"""
    
    description = "Manage DuckBot ecosystem services with advanced AI capabilities"
    name = "server_management"
    
    def __init__(self):
        super().__init__()
        self.parameters = {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["start", "stop", "restart", "status", "start_ecosystem", "stop_ecosystem"],
                    "description": "Action to perform on services"
                },
                "service": {
                    "type": "string",
                    "enum": ["lm_studio", "comfyui", "webui", "n8n", "open_notebook", "jupyter", "discord_bot", "all"],
                    "description": "Service to manage (optional for ecosystem operations)"
                },
                "details": {
                    "type": "boolean",
                    "default": False,
                    "description": "Return detailed status information"
                }
            },
            "required": ["action"]
        }
    
    def call(self, params: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Execute server management operations"""
        try:
            action = params.get("action")
            service = params.get("service")
            details = params.get("details", False)
            
            if action == "status":
                if service and service != "all":
                    result = server_manager.get_service_status(service)
                    return {
                        "success": True,
                        "service": service,
                        "status": result.status.value,
                        "port": result.port,
                        "display_name": result.display_name,
                        "pid": result.pid
                    }
                else:
                    status = server_manager.get_all_service_status()
                    return {
                        "success": True,
                        "services": {name: {
                            "status": info.status.value,
                            "port": info.port,
                            "display_name": info.display_name,
                            "pid": info.pid
                        } for name, info in status.items()}
                    }
            
            elif action == "start":
                if service == "all" or not service:
                    success, results = server_manager.start_ecosystem()
                    return {"success": success, "results": results, "action": "start_ecosystem"}
                else:
                    success, message = server_manager.start_service(service)
                    return {"success": success, "message": message, "service": service, "action": "start"}
            
            elif action == "stop":
                if service == "all" or not service:
                    success, results = server_manager.stop_ecosystem()
                    return {"success": success, "results": results, "action": "stop_ecosystem"}
                else:
                    success, message = server_manager.stop_service(service)
                    return {"success": success, "message": message, "service": service, "action": "stop"}
            
            elif action == "restart":
                if service and service != "all":
                    success, message = server_manager.restart_service(service)
                    return {"success": success, "message": message, "service": service, "action": "restart"}
                else:
                    return {"success": False, "error": "Restart requires a specific service name"}
            
            elif action == "start_ecosystem":
                success, results = server_manager.start_ecosystem()
                return {"success": success, "results": results, "action": "start_ecosystem"}
            
            elif action == "stop_ecosystem":
                success, results = server_manager.stop_ecosystem()
                return {"success": success, "results": results, "action": "stop_ecosystem"}
            
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
                
        except Exception as e:
            logger.error(f"Server management tool error: {e}")
            return {"success": False, "error": str(e)}

class SystemDiagnosticsTool(BaseTool):
    """System health and diagnostics tool"""
    
    description = "Perform system diagnostics and health checks"
    name = "system_diagnostics"
    
    def __init__(self):
        super().__init__()
        self.parameters = {
            "type": "object",
            "properties": {
                "check_type": {
                    "type": "string",
                    "enum": ["health", "performance", "resources", "logs", "dependencies"],
                    "description": "Type of diagnostic check to perform"
                },
                "detailed": {
                    "type": "boolean",
                    "default": False,
                    "description": "Return detailed diagnostic information"
                }
            },
            "required": ["check_type"]
        }
    
    def call(self, params: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Execute system diagnostics"""
        try:
            import psutil
            
            check_type = params.get("check_type")
            detailed = params.get("detailed", False)
            
            if check_type == "resources":
                return {
                    "success": True,
                    "cpu_percent": psutil.cpu_percent(interval=1),
                    "memory_percent": psutil.virtual_memory().percent,
                    "disk_usage": psutil.disk_usage('/').percent if os.name != 'nt' else psutil.disk_usage('C:').percent,
                    "network_io": dict(psutil.net_io_counters()._asdict()) if detailed else None
                }
            
            elif check_type == "performance":
                return {
                    "success": True,
                    "boot_time": psutil.boot_time(),
                    "cpu_count": psutil.cpu_count(),
                    "memory_total": psutil.virtual_memory().total,
                    "process_count": len(psutil.pids())
                }
            
            elif check_type == "health":
                # Check critical services
                status = server_manager.get_all_service_status()
                healthy_services = sum(1 for info in status.values() if info.status.value == "running")
                
                return {
                    "success": True,
                    "services_running": healthy_services,
                    "total_services": len(status),
                    "system_healthy": healthy_services >= len(status) * 0.5,  # 50% threshold
                    "services": {name: info.status.value for name, info in status.items()} if detailed else None
                }
            
            elif check_type == "dependencies":
                # Check Python dependencies
                try:
                    import fastapi, uvicorn, requests
                    deps_ok = True
                except ImportError:
                    deps_ok = False
                
                return {
                    "success": True,
                    "python_dependencies": deps_ok,
                    "qwen_agent_available": QWEN_AGENT_AVAILABLE,
                    "python_version": f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}"
                }
            
            else:
                return {"success": False, "error": f"Unknown check type: {check_type}"}
                
        except Exception as e:
            logger.error(f"System diagnostics error: {e}")
            return {"success": False, "error": str(e)}

class DuckBotQwenAgent:
    """Enhanced DuckBot Agent with Qwen-Agent capabilities"""
    
    def __init__(self):
        self.available = QWEN_AGENT_AVAILABLE
        self.agent = None
        self.tools = {}
        
        if self.available:
            self._initialize_agent()
        else:
            logger.warning("Qwen-Agent not available - install with: pip install qwen-agent")
    
    def _initialize_agent(self):
        """Initialize the Qwen Agent with DuckBot tools"""
        try:
            # Register custom tools
            self.tools = {
                "server_management": ServerManagementTool(),
                "system_diagnostics": SystemDiagnosticsTool()
            }
            
            # Configure the agent with OpenRouter authentication
            config = {
                "model": os.getenv("QWEN_CODE_MODEL", "qwen/qwen3-coder:free"),
                "model_server": "openrouter",  # Use OpenRouter instead of LM Studio for Qwen
                "api_key": os.getenv("OPENROUTER_API_KEY", ""),
                "base_url": os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
                "max_tokens": int(os.getenv("QWEN_CODE_MAX_TOKENS", "4000")),
                "temperature": float(os.getenv("QWEN_CODE_TEMPERATURE", "0.1")),
                "tools": list(self.tools.values()),
                "app_name": os.getenv("OPENROUTER_APP_NAME", "DuckBot-v3.0.6-Professional")
            }
            
            # Validate OpenRouter API key
            if not config["api_key"] or config["api_key"] == "your_openrouter_api_key_here":
                logger.warning("[WARNING] OpenRouter API key not configured - Qwen-Agent will have limited functionality")
                logger.warning("   Set OPENROUTER_API_KEY in .env file for full Qwen Code access")
            
            self.agent = Assistant(llm=config)
            logger.info("[OK] Qwen-Agent initialized with DuckBot tools")
            
        except Exception as e:
            logger.error(f"Failed to initialize Qwen-Agent: {e}")
            self.available = False
    
    async def execute_task(self, task: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute a task using advanced Qwen-Agent capabilities"""
        if not self.available or not self.agent:
            return {
                "success": False, 
                "error": "Qwen-Agent not available",
                "fallback": "Use basic AI routing instead"
            }
        
        try:
            # Enhanced task execution with tool use
            response = self.agent.run(messages=[{"role": "user", "content": task}])
            
            return {
                "success": True,
                "response": response,
                "tools_used": [tool.name for tool in response.get("tools_used", [])],
                "agent_type": "qwen_agent_enhanced"
            }
            
        except Exception as e:
            logger.error(f"Qwen-Agent execution error: {e}")
            return {
                "success": False,
                "error": str(e),
                "fallback": "Use basic AI routing instead"
            }
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get available capabilities"""
        return {
            "available": self.available,
            "tools": list(self.tools.keys()) if self.tools else [],
            "model": os.getenv("AI_MODEL_MAIN_BRAIN", "qwen/qwen3-coder:free"),
            "advanced_features": [
                "Advanced tool use",
                "Multi-step reasoning", 
                "Server management",
                "System diagnostics",
                "Workflow orchestration"
            ] if self.available else ["Basic AI routing only"]
        }

# Global instance
qwen_agent = DuckBotQwenAgent()

def is_qwen_agent_available() -> bool:
    """Check if Qwen-Agent is available and working"""
    return qwen_agent.available

def get_qwen_agent_capabilities() -> Dict[str, Any]:
    """Get Qwen-Agent capabilities"""
    return qwen_agent.get_capabilities()

async def execute_enhanced_task(task: str, context: Optional[Dict] = None) -> Dict[str, Any]:
    """Execute task with enhanced Qwen-Agent capabilities"""
    return await qwen_agent.execute_task(task, context)