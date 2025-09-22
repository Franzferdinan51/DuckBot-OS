"""
Unified Service Manager for DuckBot Enhanced v4.2
Manages ComfyUI, TRELLIS, and VibeVoice integrations with unified API and health monitoring
"""

import asyncio
import json
import logging
import os
import time
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from pathlib import Path

from .comfyui_integration import ComfyUIManager, initialize_comfyui
from .trellis_integration import TRELLISManager, initialize_trellis
from .vibevoice_client import VibeVoiceClient
from ..core.cost_management import CostTracker
from ..core.hardware_detector import HardwareDetector

logger = logging.getLogger(__name__)

class UnifiedServiceManager:
    """Unified manager for ComfyUI, TRELLIS, and VibeVoice services"""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize Unified Service Manager

        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path or self._get_default_config_path()
        self.config = self._load_config()

        # Initialize managers
        self.comfyui_manager = ComfyUIManager(
            comfyui_path=self.config.get("comfyui", {}).get("path"),
            api_base_url=self.config.get("comfyui", {}).get("api_url", "http://localhost:8188")
        )

        self.trellis_manager = TRELLISManager(
            trellis_path=self.config.get("trellis", {}).get("path"),
            api_base_url=self.config.get("trellis", {}).get("api_url", "http://localhost:8288")
        )

        self.vibevoice_manager = VibeVoiceClient(
            api_url=self.config.get("vibevoice", {}).get("api_url", "http://localhost:8000")
        )

        # Cost tracking
        self.cost_tracker = CostTracker()

        # Hardware monitoring
        self.hardware_detector = HardwareDetector()

        # Service status tracking
        self.service_status = {
            "comfyui": {"initialized": False, "healthy": False, "last_check": None},
            "trellis": {"initialized": False, "healthy": False, "last_check": None},
            "vibevoice": {"initialized": False, "healthy": False, "last_check": None}
        }

        # Performance metrics
        self.performance_metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_response_time": 0,
            "uptime_start": datetime.now(),
            "service_usage": {
                "comfyui": 0,
                "trellis": 0,
                "vibevoice": 0
            }
        }

        # Background tasks
        self.health_check_task = None
        self.metrics_cleanup_task = None

    def _get_default_config_path(self) -> str:
        """Get default configuration file path"""
        return os.path.join(os.path.dirname(__file__), "..", "..", "config", "unified_services_config.json")

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            else:
                # Create default configuration
                default_config = self._get_default_config()
                os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
                with open(self.config_path, 'w') as f:
                    json.dump(default_config, f, indent=2)
                return default_config
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "comfyui": {
                "path": None,
                "api_url": "http://localhost:8188",
                "enabled": True,
                "auto_start": True,
                "gpu_memory_limit": 0.8,
                "max_concurrent_workflows": 3
            },
            "trellis": {
                "path": None,
                "api_url": "http://localhost:8288",
                "enabled": True,
                "auto_start": True,
                "max_concurrent_generations": 2
            },
            "vibevoice": {
                "api_url": "http://localhost:8000",
                "enabled": True,
                "auto_start": True,
                "batch_processing": True
            },
            "unified": {
                "health_check_interval": 30,
                "metrics_retention_days": 7,
                "auto_restart_services": True,
                "resource_monitoring": True,
                "cross_service_integration": True
            }
        }

    async def initialize_all(self) -> Dict[str, bool]:
        """Initialize all services"""
        results = {}

        # Initialize ComfyUI
        if self.config.get("comfyui", {}).get("enabled", True):
            try:
                result = await self.comfyui_manager.initialize()
                results["comfyui"] = result
                self.service_status["comfyui"]["initialized"] = result
                logger.info(f"ComfyUI initialization: {'Success' if result else 'Failed'}")
            except Exception as e:
                logger.error(f"ComfyUI initialization error: {e}")
                results["comfyui"] = False
        else:
            results["comfyui"] = False
            logger.info("ComfyUI disabled in configuration")

        # Initialize TRELLIS
        if self.config.get("trellis", {}).get("enabled", True):
            try:
                result = await self.trellis_manager.initialize()
                results["trellis"] = result
                self.service_status["trellis"]["initialized"] = result
                logger.info(f"TRELLIS initialization: {'Success' if result else 'Failed'}")
            except Exception as e:
                logger.error(f"TRELLIS initialization error: {e}")
                results["trellis"] = False
        else:
            results["trellis"] = False
            logger.info("TRELLIS disabled in configuration")

        # Initialize VibeVoice
        if self.config.get("vibevoice", {}).get("enabled", True):
            try:
                result = await self.vibevoice_manager.initialize()
                results["vibevoice"] = result
                self.service_status["vibevoice"]["initialized"] = result
                logger.info(f"VibeVoice initialization: {'Success' if result else 'Failed'}")
            except Exception as e:
                logger.error(f"VibeVoice initialization error: {e}")
                results["vibevoice"] = False
        else:
            results["vibevoice"] = False
            logger.info("VibeVoice disabled in configuration")

        # Start background tasks
        await self._start_background_tasks()

        # Log initialization summary
        successful = sum(1 for result in results.values() if result)
        logger.info(f"Service initialization complete: {successful}/{len(results)} services successful")

        return results

    async def _start_background_tasks(self):
        """Start background monitoring tasks"""
        # Health check task
        self.health_check_task = asyncio.create_task(self._health_check_loop())

        # Metrics cleanup task
        self.metrics_cleanup_task = asyncio.create_task(self._metrics_cleanup_loop())

    async def _health_check_loop(self):
        """Periodic health check loop"""
        interval = self.config.get("unified", {}).get("health_check_interval", 30)

        while True:
            try:
                await self._perform_health_checks()
                await asyncio.sleep(interval)
            except Exception as e:
                logger.error(f"Health check loop error: {e}")
                await asyncio.sleep(interval)

    async def _perform_health_checks(self):
        """Perform health checks on all services"""
        # Check ComfyUI
        if self.service_status["comfyui"]["initialized"]:
            try:
                is_healthy = await self.comfyui_manager._check_server_status()
                self.service_status["comfyui"]["healthy"] = is_healthy
                self.service_status["comfyui"]["last_check"] = datetime.now()

                if not is_healthy and self.config.get("unified", {}).get("auto_restart_services", True):
                    logger.warning("ComfyUI service unhealthy, attempting restart")
                    await self.comfyui_manager._start_server()
            except Exception as e:
                logger.error(f"ComfyUI health check error: {e}")
                self.service_status["comfyui"]["healthy"] = False

        # Check TRELLIS
        if self.service_status["trellis"]["initialized"]:
            try:
                is_healthy = await self.trellis_manager._check_server_status()
                self.service_status["trellis"]["healthy"] = is_healthy
                self.service_status["trellis"]["last_check"] = datetime.now()

                if not is_healthy and self.config.get("unified", {}).get("auto_restart_services", True):
                    logger.warning("TRELLIS service unhealthy, attempting restart")
                    await self.trellis_manager._start_server()
            except Exception as e:
                logger.error(f"TRELLIS health check error: {e}")
                self.service_status["trellis"]["healthy"] = False

        # Check VibeVoice
        if self.service_status["vibevoice"]["initialized"]:
            try:
                health_info = await self.vibevoice_manager.get_service_health()
                is_healthy = health_info.get("service_available", False)
                self.service_status["vibevoice"]["healthy"] = is_healthy
                self.service_status["vibevoice"]["last_check"] = datetime.now()
            except Exception as e:
                logger.error(f"VibeVoice health check error: {e}")
                self.service_status["vibevoice"]["healthy"] = False

    async def _metrics_cleanup_loop(self):
        """Clean up old metrics periodically"""
        retention_days = self.config.get("unified", {}).get("metrics_retention_days", 7)

        while True:
            try:
                # Clean up old metrics (implementation depends on storage backend)
                await asyncio.sleep(86400)  # Daily cleanup
            except Exception as e:
                logger.error(f"Metrics cleanup error: {e}")
                await asyncio.sleep(86400)

    # ComfyUI Service Methods
    async def execute_comfyui_workflow(self,
                                     workflow_type: str,
                                     parameters: Dict[str, Any],
                                     output_dir: Optional[str] = None) -> Dict[str, Any]:
        """Execute ComfyUI workflow with unified tracking"""
        if not self.service_status["comfyui"]["initialized"]:
            return {"success": False, "error": "ComfyUI service not initialized"}

        start_time = time.time()
        self.performance_metrics["total_requests"] += 1
        self.performance_metrics["service_usage"]["comfyui"] += 1

        try:
            result = await self.comfyui_manager.execute_workflow(workflow_type, parameters, output_dir)

            execution_time = time.time() - start_time
            self._update_performance_metrics(execution_time, result.get("success", False))

            return result

        except Exception as e:
            logger.error(f"ComfyUI workflow execution error: {e}")
            self._update_performance_metrics(time.time() - start_time, False)
            return {"success": False, "error": str(e)}

    # TRELLIS Service Methods
    async def generate_3d_asset(self,
                              asset_type: str,
                              parameters: Dict[str, Any],
                              output_format: str = "gaussians",
                              output_dir: Optional[str] = None) -> Dict[str, Any]:
        """Generate 3D asset using TRELLIS with unified tracking"""
        if not self.service_status["trellis"]["initialized"]:
            return {"success": False, "error": "TRELLIS service not initialized"}

        start_time = time.time()
        self.performance_metrics["total_requests"] += 1
        self.performance_metrics["service_usage"]["trellis"] += 1

        try:
            result = await self.trellis_manager.generate_3d_asset(asset_type, parameters, output_format, output_dir)

            execution_time = time.time() - start_time
            self._update_performance_metrics(execution_time, result.get("success", False))

            return result

        except Exception as e:
            logger.error(f"TRELLIS 3D generation error: {e}")
            self._update_performance_metrics(time.time() - start_time, False)
            return {"success": False, "error": str(e)}

    async def create_trellis_workflow(self,
                                    structure_type: str,
                                    tasks: List[Dict[str, Any]],
                                    dependencies: Optional[List[tuple]] = None) -> Dict[str, Any]:
        """Create TRELLIS workflow structure"""
        if not self.service_status["trellis"]["initialized"]:
            return {"success": False, "error": "TRELLIS service not initialized"}

        try:
            return await self.trellis_manager.create_workflow_structure(structure_type, tasks, dependencies)
        except Exception as e:
            logger.error(f"TRELLIS workflow creation error: {e}")
            return {"success": False, "error": str(e)}

    # VibeVoice Service Methods
    async def generate_voice_content(self,
                                  content: str,
                                  speakers: Optional[List[str]] = None,
                                  style: str = "conversational") -> Dict[str, Any]:
        """Generate voice content using VibeVoice with unified tracking"""
        if not self.service_status["vibevoice"]["initialized"]:
            return {"success": False, "error": "VibeVoice service not initialized"}

        start_time = time.time()
        self.performance_metrics["total_requests"] += 1
        self.performance_metrics["service_usage"]["vibevoice"] += 1

        try:
            audio_path = await self.vibevoice_manager.generate_voice_content(content, speakers, style)

            execution_time = time.time() - start_time
            success = audio_path is not None
            self._update_performance_metrics(execution_time, success)

            return {
                "success": success,
                "audio_path": audio_path,
                "execution_time": execution_time
            }

        except Exception as e:
            logger.error(f"VibeVoice generation error: {e}")
            self._update_performance_metrics(time.time() - start_time, False)
            return {"success": False, "error": str(e)}

    async def generate_voice_conversation(self,
                                        script: List[Dict[str, str]],
                                        style: str = "conversational",
                                        output_dir: Optional[str] = None) -> Dict[str, Any]:
        """Generate multi-speaker conversation"""
        if not self.service_status["vibevoice"]["initialized"]:
            return {"success": False, "error": "VibeVoice service not initialized"}

        try:
            audio_path = await self.vibevoice_manager.generate_conversation(script, style, output_dir)
            return {
                "success": audio_path is not None,
                "audio_path": audio_path
            }
        except Exception as e:
            logger.error(f"Voice conversation generation error: {e}")
            return {"success": False, "error": str(e)}

    # Cross-Service Integration Methods
    async def create_multimodal_workflow(self,
                                      description: str,
                                      requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Create cross-service workflow combining multiple services"""
        try:
            workflow_plan = await self._plan_multimodal_workflow(description, requirements)
            execution_results = await self._execute_multimodal_workflow(workflow_plan)

            return {
                "success": True,
                "workflow_plan": workflow_plan,
                "results": execution_results,
                "execution_summary": self._summarize_workflow_results(execution_results)
            }

        except Exception as e:
            logger.error(f"Multimodal workflow error: {e}")
            return {"success": False, "error": str(e)}

    async def _plan_multimodal_workflow(self, description: str, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Plan a multimodal workflow based on description and requirements"""
        # Analyze requirements to determine which services to use
        services_needed = []

        if "image" in description.lower() or "visual" in description.lower():
            services_needed.append("comfyui")

        if "3d" in description.lower() or "model" in description.lower():
            services_needed.append("trellis")

        if "audio" in description.lower() or "voice" in description.lower() or "sound" in description.lower():
            services_needed.append("vibevoice")

        # Create workflow plan
        workflow_plan = {
            "description": description,
            "requirements": requirements,
            "services": services_needed,
            "steps": []
        }

        # Generate workflow steps
        if "comfyui" in services_needed:
            workflow_plan["steps"].append({
                "service": "comfyui",
                "action": "generate_image",
                "parameters": {
                    "workflow_type": "text_to_image",
                    "prompt": description,
                    "negative_prompt": "blurry, low quality"
                }
            })

        if "trellis" in services_needed:
            workflow_plan["steps"].append({
                "service": "trellis",
                "action": "generate_3d",
                "parameters": {
                    "asset_type": "text_to_3d",
                    "text_prompt": description,
                    "output_format": "gaussians"
                }
            })

        if "vibevoice" in services_needed:
            workflow_plan["steps"].append({
                "service": "vibevoice",
                "action": "generate_narration",
                "parameters": {
                    "content": f"Here is {description}",
                    "speakers": ["en-alice"],
                    "style": "narrative"
                }
            })

        return workflow_plan

    async def _execute_multimodal_workflow(self, workflow_plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute multimodal workflow steps"""
        results = []

        for step in workflow_plan["steps"]:
            try:
                if step["service"] == "comfyui":
                    result = await self.execute_comfyui_workflow(
                        step["parameters"]["workflow_type"],
                        step["parameters"]
                    )
                elif step["service"] == "trellis":
                    result = await self.generate_3d_asset(
                        step["parameters"]["asset_type"],
                        step["parameters"],
                        step["parameters"]["output_format"]
                    )
                elif step["service"] == "vibevoice":
                    result = await self.generate_voice_content(
                        step["parameters"]["content"],
                        step["parameters"]["speakers"],
                        step["parameters"]["style"]
                    )
                else:
                    result = {"success": False, "error": f"Unknown service: {step['service']}"}

                results.append({
                    "step": step,
                    "result": result
                })

            except Exception as e:
                logger.error(f"Error executing workflow step: {e}")
                results.append({
                    "step": step,
                    "result": {"success": False, "error": str(e)}
                })

        return results

    def _summarize_workflow_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Summarize workflow execution results"""
        total_steps = len(results)
        successful_steps = sum(1 for r in results if r["result"].get("success", False))
        failed_steps = total_steps - successful_steps

        return {
            "total_steps": total_steps,
            "successful_steps": successful_steps,
            "failed_steps": failed_steps,
            "success_rate": successful_steps / total_steps if total_steps > 0 else 0,
            "services_used": list(set(r["step"]["service"] for r in results))
        }

    def _update_performance_metrics(self, execution_time: float, success: bool):
        """Update performance metrics"""
        self.performance_metrics["average_response_time"] = (
            (self.performance_metrics["average_response_time"] * (self.performance_metrics["total_requests"] - 1) + execution_time) /
            self.performance_metrics["total_requests"]
        )

        if success:
            self.performance_metrics["successful_requests"] += 1
        else:
            self.performance_metrics["failed_requests"] += 1

    # Status and Monitoring Methods
    async def get_unified_status(self) -> Dict[str, Any]:
        """Get unified status of all services"""
        return {
            "services": {
                "comfyui": {
                    **self.service_status["comfyui"],
                    "available_workflows": await self.comfyui_manager.get_available_workflows() if self.service_status["comfyui"]["initialized"] else []
                },
                "trellis": {
                    **self.service_status["trellis"],
                    "available_asset_types": await self.trellis_manager.get_available_asset_types() if self.service_status["trellis"]["initialized"] else [],
                    "workflow_structures": await self.trellis_manager.get_workflow_structures() if self.service_status["trellis"]["initialized"] else []
                },
                "vibevoice": {
                    **self.service_status["vibevoice"],
                    "available_voices": self.vibevoice_manager.get_available_voices() if self.service_status["vibevoice"]["initialized"] else [],
                    "health": await self.vibevoice_manager.get_service_health() if self.service_status["vibevoice"]["initialized"] else None
                }
            },
            "performance": self.performance_metrics,
            "hardware": self.hardware_detector.get_system_info(),
            "configuration": {
                k: {k2: v2 for k2, v2 in v.items() if k2 not in ["path"]}  # Exclude sensitive paths
                for k, v in self.config.items()
            }
        }

    async def get_service_health(self, service_name: str) -> Dict[str, Any]:
        """Get detailed health information for a specific service"""
        if service_name == "comfyui":
            return {
                "status": self.service_status["comfyui"],
                "stats": self.comfyui_manager.workflow_stats,
                "system_stats": await self.comfyui_manager.get_system_stats()
            }
        elif service_name == "trellis":
            return {
                "status": self.service_status["trellis"],
                "stats": self.trellis_manager.generation_stats,
                "asset_library": await self.trellis_manager.get_asset_library()
            }
        elif service_name == "vibevoice":
            return {
                "status": self.service_status["vibevoice"],
                "health": await self.vibevoice_manager.get_service_health()
            }
        else:
            return {"error": f"Unknown service: {service_name}"}

    async def restart_service(self, service_name: str) -> bool:
        """Restart a specific service"""
        try:
            if service_name == "comfyui":
                await self.comfyui_manager.stop_server()
                await self.comfyui_manager._start_server()
                return True
            elif service_name == "trellis":
                await self.trellis_manager.stop_server()
                await self.trellis_manager._start_server()
                return True
            elif service_name == "vibevoice":
                # VibeVoice doesn't have a server to restart, but we can reinitialize
                return await self.vibevoice_manager.initialize()
            else:
                return False
        except Exception as e:
            logger.error(f"Error restarting service {service_name}: {e}")
            return False

    async def update_configuration(self, new_config: Dict[str, Any]) -> bool:
        """Update configuration and apply changes"""
        try:
            # Validate configuration
            if not self._validate_configuration(new_config):
                return False

            # Update configuration
            self.config.update(new_config)

            # Save to file
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)

            # Apply configuration changes (restart services if needed)
            await self._apply_configuration_changes()

            return True

        except Exception as e:
            logger.error(f"Error updating configuration: {e}")
            return False

    def _validate_configuration(self, config: Dict[str, Any]) -> bool:
        """Validate configuration structure"""
        required_keys = ["comfyui", "trellis", "vibevoice", "unified"]

        for key in required_keys:
            if key not in config:
                logger.error(f"Missing required configuration key: {key}")
                return False

        return True

    async def _apply_configuration_changes(self):
        """Apply configuration changes"""
        # Restart services if their configuration changed
        # This is a simplified implementation
        pass

    async def _apply_configuration_changes(self):
        """Apply configuration changes"""
        # Implementation for applying configuration changes
        pass

    async def cleanup(self):
        """Clean up resources"""
        # Stop background tasks
        if self.health_check_task:
            self.health_check_task.cancel()

        if self.metrics_cleanup_task:
            self.metrics_cleanup_task.cancel()

        # Stop services
        await self.comfyui_manager.cleanup()
        await self.trellis_manager.cleanup()
        await self.vibevoice_manager.cleanup()

        logger.info("Unified service manager cleanup completed")

# Global instance (initialized lazily)
unified_service_manager = None

async def initialize_unified_services(config_path: Optional[str] = None) -> Dict[str, bool]:
    """Initialize unified services"""
    global unified_service_manager
    if unified_service_manager is None:
        unified_service_manager = UnifiedServiceManager(config_path)
    elif config_path:
        unified_service_manager = UnifiedServiceManager(config_path)
    return await unified_service_manager.initialize_all()

async def get_unified_status() -> Dict[str, Any]:
    """Get unified status of all services"""
    if unified_service_manager is None:
        raise RuntimeError("Unified services not initialized. Call initialize_unified_services() first.")
    return await unified_service_manager.get_unified_status()

def get_unified_service_manager() -> UnifiedServiceManager:
    """Get the global unified service manager instance"""
    if unified_service_manager is None:
        raise RuntimeError("Unified services not initialized. Call initialize_unified_services() first.")
    return unified_service_manager