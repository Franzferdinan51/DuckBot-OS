#!/usr/bin/env python3
"""
Integration Manager for DuckBot
Manages all system integrations including Memento, ByteBot, Archon, WSL, ChromiumOS
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class IntegrationManager:
    """Manages all DuckBot integrations and orchestrates inter-service communication"""
    
    def __init__(self):
        self.integrations = {}
        self.initialization_status = {}
        self.ai_router = None
        self.available_integrations = []
        
        # Import integrations dynamically
        self._load_integrations()
        
    def _load_integrations(self):
        """Dynamically load all available integrations"""
        integrations_to_load = [
            ("bytebot", "duckbot.bytebot_integration", "bytebot_integration"),
            ("archon", "duckbot.archon_integration", "archon_integration"),
            ("wsl", "duckbot.wsl_integration", "wsl_integration"),
            ("chromium", "duckbot.chromium_integration", "chromium_integration"),
            ("memento", "duckbot.memento_integration", "memento_integration"),
            ("charm_tools", "duckbot.charm_tools_integration", "charm_tools"),
            ("spec_kit", "duckbot.spec_kit_integration", "spec_kit"),
        ]
        
        for name, module_path, instance_name in integrations_to_load:
            try:
                module = __import__(module_path, fromlist=[instance_name])
                integration = getattr(module, instance_name)
                self.integrations[name] = integration
                self.available_integrations.append(name)
                logger.info(f"Loaded integration: {name}")
            except ImportError as e:
                logger.warning(f"Failed to load {name} integration: {e}")
            except AttributeError as e:
                logger.warning(f"Integration {name} missing instance {instance_name}: {e}")
    
    async def initialize_all(self, ai_router=None) -> Dict[str, bool]:
        """Initialize all integrations"""
        self.ai_router = ai_router
        results = {}
        
        # Initialize core integrations first
        core_integrations = ["bytebot", "archon", "wsl", "chromium"]
        
        for integration_name in core_integrations:
            if integration_name in self.integrations:
                try:
                    integration = self.integrations[integration_name]
                    if hasattr(integration, 'initialize'):
                        result = await integration.initialize()
                        results[integration_name] = result
                        self.initialization_status[integration_name] = {
                            "initialized": result,
                            "timestamp": datetime.now(),
                            "error": None
                        }
                    else:
                        results[integration_name] = True  # No initialization needed
                        self.initialization_status[integration_name] = {
                            "initialized": True,
                            "timestamp": datetime.now(),
                            "error": None
                        }
                except Exception as e:
                    logger.error(f"Failed to initialize {integration_name}: {e}")
                    results[integration_name] = False
                    self.initialization_status[integration_name] = {
                        "initialized": False,
                        "timestamp": datetime.now(),
                        "error": str(e)
                    }
        
        # Initialize Memento last (it needs other integrations)
        if "memento" in self.integrations:
            try:
                # Import and initialize with dependencies
                from duckbot.memento_integration import initialize_memento
                result = await initialize_memento(ai_router, self)
                results["memento"] = result
                self.initialization_status["memento"] = {
                    "initialized": result,
                    "timestamp": datetime.now(),
                    "error": None
                }
                logger.info("Memento integration initialized with case-based memory")
            except Exception as e:
                logger.error(f"Failed to initialize Memento: {e}")
                results["memento"] = False
                self.initialization_status["memento"] = {
                    "initialized": False,
                    "timestamp": datetime.now(),
                    "error": str(e)
                }
        
        # Initialize Charm tools integration
        if "charm_tools" in self.integrations:
            try:
                from duckbot.charm_tools_integration import initialize_charm_integration
                result = await initialize_charm_integration()
                results["charm_tools"] = result
                self.initialization_status["charm_tools"] = {
                    "initialized": result,
                    "timestamp": datetime.now(),
                    "error": None
                }
                if result:
                    logger.info("Charm tools ecosystem successfully integrated")
                else:
                    logger.warning("Charm tools integration partially successful")
            except Exception as e:
                logger.error(f"Failed to initialize Charm tools: {e}")
                results["charm_tools"] = False
                self.initialization_status["charm_tools"] = {
                    "initialized": False,
                    "timestamp": datetime.now(),
                    "error": str(e)
                }
        
        # Initialize Spec-Kit integration
        if "spec_kit" in self.integrations:
            try:
                from duckbot.spec_kit_integration import initialize_spec_kit_integration
                result = await initialize_spec_kit_integration()
                results["spec_kit"] = result
                self.initialization_status["spec_kit"] = {
                    "initialized": result,
                    "timestamp": datetime.now(),
                    "error": None
                }
                if result:
                    logger.info("GitHub Spec-Kit successfully integrated for spec-driven development")
                else:
                    logger.warning("Spec-Kit integration failed")
            except Exception as e:
                logger.error(f"Failed to initialize Spec-Kit: {e}")
                results["spec_kit"] = False
                self.initialization_status["spec_kit"] = {
                    "initialized": False,
                    "timestamp": datetime.now(),
                    "error": str(e)
                }
        
        successful_integrations = sum(1 for r in results.values() if r)
        logger.info(f"Integration initialization complete: {successful_integrations}/{len(results)} successful")
        
        return results
    
    async def execute_integrated_task(self, task_type: str, description: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute a task using the appropriate integration"""
        start_time = time.time()
        
        # Route to appropriate integration based on task type
        if task_type == "memory" and "memento" in self.integrations:
            # Use Memento for memory-enhanced tasks
            try:
                from duckbot.memento_integration import execute_memento_task
                result = await execute_memento_task(description, context)
                return {
                    "success": True,
                    "integration_used": "memento",
                    "result": result,
                    "execution_time": time.time() - start_time
                }
            except Exception as e:
                logger.error(f"Memento task execution failed: {e}")
                # Fallback to other integrations
        
        if task_type == "desktop" and "bytebot" in self.integrations:
            # Use ByteBot for desktop automation
            try:
                integration = self.integrations["bytebot"]
                result = await integration.execute_natural_language_task(description, context)
                return {
                    "success": result.success,
                    "integration_used": "bytebot",
                    "result": {
                        "message": result.message,
                        "artifacts": result.artifacts,
                        "screenshot": result.screenshot
                    },
                    "execution_time": result.execution_time
                }
            except Exception as e:
                logger.error(f"ByteBot task execution failed: {e}")
        
        if task_type == "agents" and "archon" in self.integrations:
            # Use Archon for multi-agent tasks
            try:
                from duckbot.archon_integration import create_archon_task
                task_id = await create_archon_task(description, "task_executor", context)
                return {
                    "success": True,
                    "integration_used": "archon",
                    "result": {"task_id": task_id, "status": "created"},
                    "execution_time": time.time() - start_time
                }
            except Exception as e:
                logger.error(f"Archon task execution failed: {e}")
        
        if task_type == "linux" and "wsl" in self.integrations:
            # Use WSL for Linux commands
            try:
                from duckbot.wsl_integration import execute_wsl_command
                result = await execute_wsl_command(description)
                return {
                    "success": result.get("success", False),
                    "integration_used": "wsl",
                    "result": result,
                    "execution_time": time.time() - start_time
                }
            except Exception as e:
                logger.error(f"WSL task execution failed: {e}")
        
        if task_type == "ai_chat" and "charm_tools" in self.integrations:
            # Use Charm tools for AI-powered tasks
            try:
                from duckbot.charm_tools_integration import ask_ai
                result = await ask_ai(description, context.get("context") if context else None)
                return {
                    "success": result is not None,
                    "integration_used": "charm_tools",
                    "result": {"response": result},
                    "execution_time": time.time() - start_time
                }
            except Exception as e:
                logger.error(f"Charm tools AI task execution failed: {e}")
        
        if task_type == "ui_interaction" and "charm_tools" in self.integrations:
            # Use Charm tools for interactive UI tasks
            try:
                from duckbot.charm_tools_integration import gum_input, gum_choose, gum_confirm
                
                if "input" in description.lower():
                    result = await gum_input(placeholder=description)
                elif "choose" in description.lower() or "select" in description.lower():
                    options = context.get("options", ["Yes", "No", "Cancel"]) if context else ["Yes", "No", "Cancel"]
                    result = await gum_choose(options, description)
                elif "confirm" in description.lower():
                    result = await gum_confirm(description)
                else:
                    result = await gum_input(placeholder=description)
                
                return {
                    "success": result is not None,
                    "integration_used": "charm_tools",
                    "result": {"user_input": result},
                    "execution_time": time.time() - start_time
                }
            except Exception as e:
                logger.error(f"Charm tools UI task execution failed: {e}")
        
        # Generic execution
        return {
            "success": False,
            "integration_used": "none",
            "result": {"message": f"No suitable integration found for task type: {task_type}"},
            "execution_time": time.time() - start_time
        }
    
    async def get_integration_status(self) -> Dict[str, Any]:
        """Get status of all integrations"""
        status = {}
        
        for name, integration in self.integrations.items():
            try:
                init_status = self.initialization_status.get(name, {})
                
                if hasattr(integration, 'get_capabilities'):
                    capabilities = integration.get_capabilities()
                elif hasattr(integration, 'available'):
                    capabilities = {"available": integration.available}
                else:
                    capabilities = {"available": True}
                
                status[name] = {
                    "initialized": init_status.get("initialized", False),
                    "initialization_time": init_status.get("timestamp", "Unknown"),
                    "initialization_error": init_status.get("error"),
                    "capabilities": capabilities
                }
            except Exception as e:
                status[name] = {
                    "initialized": False,
                    "initialization_time": "Unknown",
                    "initialization_error": str(e),
                    "capabilities": {"available": False}
                }
        
        return status
    
    async def get_memento_stats(self) -> Dict[str, Any]:
        """Get Memento memory statistics"""
        if "memento" not in self.integrations:
            return {"available": False, "message": "Memento not loaded"}
        
        try:
            from duckbot.memento_integration import get_memento_memory_stats
            return await get_memento_memory_stats()
        except Exception as e:
            return {"available": False, "error": str(e)}
    
    def get_available_integrations(self) -> List[str]:
        """Get list of available integrations"""
        return self.available_integrations
    
    def is_integration_available(self, name: str) -> bool:
        """Check if a specific integration is available"""
        return name in self.integrations and self.initialization_status.get(name, {}).get("initialized", False)
    
    async def enhanced_task_execution(self, description: str, context: Optional[Dict] = None, use_memory: bool = True) -> Dict[str, Any]:
        """Enhanced task execution with automatic integration selection and memory"""
        start_time = time.time()
        
        # If Memento is available and use_memory is True, use it for intelligent task execution
        if use_memory and self.is_integration_available("memento"):
            try:
                logger.info(f"Executing task with memory enhancement: {description}")
                from duckbot.memento_integration import execute_memento_task
                result = await execute_memento_task(description, context)
                
                return {
                    "success": result.get("success", False),
                    "method": "memento_enhanced",
                    "result": result,
                    "execution_time": time.time() - start_time,
                    "memory_used": True,
                    "similar_cases_found": result.get("similar_cases_used", 0)
                }
            except Exception as e:
                logger.error(f"Memento-enhanced execution failed: {e}")
                # Continue with fallback execution
        
        # Fallback: Determine task type and route appropriately
        description_lower = description.lower()
        
        task_type = "generic"
        if any(keyword in description_lower for keyword in ["desktop", "click", "type", "screenshot", "automate"]):
            task_type = "desktop"
        elif any(keyword in description_lower for keyword in ["agent", "task", "research", "analyze"]):
            task_type = "agents"
        elif any(keyword in description_lower for keyword in ["linux", "bash", "shell", "command"]):
            task_type = "linux"
        
        result = await self.execute_integrated_task(task_type, description, context)
        result["method"] = "integration_routed"
        result["memory_used"] = False
        
        return result
    
    # Properties for easy access to integrations
    @property
    def bytebot_integration(self):
        """Get ByteBot integration"""
        return self.integrations.get("bytebot")
    
    @property
    def archon_integration(self):
        """Get Archon integration"""
        return self.integrations.get("archon")
    
    @property
    def wsl_integration(self):
        """Get WSL integration"""
        return self.integrations.get("wsl")
    
    @property
    def chromium_integration(self):
        """Get ChromiumOS integration"""
        return self.integrations.get("chromium")
    
    @property
    def memento_integration(self):
        """Get Memento integration"""
        return self.integrations.get("memento")
    
    @property
    def charm_tools(self):
        """Get Charm tools integration"""
        return self.integrations.get("charm_tools")

# Global instance
integration_manager = IntegrationManager()

async def initialize_integration_manager(ai_router=None) -> Dict[str, bool]:
    """Initialize the integration manager"""
    return await integration_manager.initialize_all(ai_router)

async def execute_enhanced_task(description: str, context: Optional[Dict] = None, use_memory: bool = True) -> Dict[str, Any]:
    """Execute task with enhanced integration and memory support"""
    return await integration_manager.enhanced_task_execution(description, context, use_memory)

def get_integration_manager() -> IntegrationManager:
    """Get the global integration manager instance"""
    return integration_manager