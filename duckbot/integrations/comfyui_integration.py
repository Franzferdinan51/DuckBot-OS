"""
ComfyUI Integration for DuckBot Enhanced v4.2
Provides comprehensive workflow management and GPU-accelerated AI processing
"""

import asyncio
import json
import os
import subprocess
import time
import aiohttp
import logging
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import uuid

from ..core.cost_management import CostTracker
from ..core.hardware_detector import HardwareDetector

logger = logging.getLogger(__name__)

class ComfyUIManager:
    """Manages ComfyUI server, workflows, and API communication"""

    def __init__(self,
                 comfyui_path: Optional[str] = None,
                 api_base_url: str = "http://localhost:8188",
                 cost_tracker: Optional[CostTracker] = None):
        """
        Initialize ComfyUI Manager

        Args:
            comfyui_path: Path to ComfyUI installation
            api_base_url: ComfyUI API base URL
            cost_tracker: Optional cost tracking instance
        """
        self.comfyui_path = comfyui_path or self._find_comfyui_path()
        self.api_base_url = api_base_url.rstrip('/')
        self.cost_tracker = cost_tracker
        self.hardware_detector = HardwareDetector()

        # Server management
        self.server_process = None
        self.server_port = 8188
        self.is_server_running = False

        # Workflow management
        self.workflow_templates = {}
        self.active_workflows = {}
        self.workflow_results = {}

        # Resource management
        self.gpu_memory_limit = 0.8  # 80% GPU memory usage limit
        self.max_concurrent_workflows = 3

        # Performance tracking
        self.workflow_stats = {
            "total_workflows": 0,
            "successful_workflows": 0,
            "failed_workflows": 0,
            "average_execution_time": 0,
            "gpu_usage_peak": 0
        }

    def _find_comfyui_path(self) -> Optional[str]:
        """Find ComfyUI installation path"""
        possible_paths = [
            "C:/ComfyUI",
            "C:/Program Files/ComfyUI",
            "D:/ComfyUI",
            os.path.expanduser("~/ComfyUI"),
            "./ComfyUI"
        ]

        for path in possible_paths:
            if os.path.exists(path) and os.path.exists(os.path.join(path, "main.py")):
                logger.info(f"Found ComfyUI at: {path}")
                return path

        logger.warning("ComfyUI installation not found. Please install ComfyUI.")
        return None

    async def initialize(self) -> bool:
        """Initialize ComfyUI integration"""
        if not self.comfyui_path:
            logger.error("ComfyUI path not found")
            return False

        try:
            # Check if ComfyUI is properly installed
            if not await self._validate_comfyui_installation():
                return False

            # Load workflow templates
            await self._load_workflow_templates()

            # Start server if not running
            if not await self._check_server_status():
                await self._start_server()

            logger.info("ComfyUI integration initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize ComfyUI: {e}")
            return False

    async def _validate_comfyui_installation(self) -> bool:
        """Validate ComfyUI installation"""
        required_files = ["main.py", "nodes.py", "folder_paths.py"]

        for file in required_files:
            file_path = os.path.join(self.comfyui_path, file)
            if not os.path.exists(file_path):
                logger.error(f"Missing required ComfyUI file: {file}")
                return False

        # Check for required dependencies
        try:
            import torch
            import torchvision
            import torchaudio
            logger.info("PyTorch dependencies available")
            return True
        except ImportError as e:
            logger.error(f"Missing PyTorch dependencies: {e}")
            return False

    async def _load_workflow_templates(self):
        """Load workflow templates from configuration"""
        self.workflow_templates = {
            "text_to_image": {
                "template": self._get_text_to_image_workflow(),
                "description": "Generate images from text prompts",
                "category": "generation"
            },
            "image_to_image": {
                "template": self._get_image_to_image_workflow(),
                "description": "Transform images using text prompts",
                "category": "processing"
            },
            "upscaling": {
                "template": self._get_upscaling_workflow(),
                "description": "Upscale images with AI enhancement",
                "category": "enhancement"
            },
            "inpainting": {
                "template": self._get_inpainting_workflow(),
                "description": "Edit and repair image regions",
                "category": "editing"
            },
            "controlnet": {
                "template": self._get_controlnet_workflow(),
                "description": "Generate images with pose/depth control",
                "category": "controlled_generation"
            }
        }

        logger.info(f"Loaded {len(self.workflow_templates)} workflow templates")

    def _get_text_to_image_workflow(self) -> Dict:
        """Get text-to-image workflow template"""
        return {
            "1": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {
                    "ckpt_name": "v1-5-pruned.ckpt"
                }
            },
            "2": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "text": "{prompt}",
                    "clip": ["1", 1]
                }
            },
            "3": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "text": "{negative_prompt}",
                    "clip": ["1", 1]
                }
            },
            "4": {
                "class_type": "EmptyLatentImage",
                "inputs": {
                    "width": 512,
                    "height": 512,
                    "batch_size": 1
                }
            },
            "5": {
                "class_type": "KSampler",
                "inputs": {
                    "seed": "{seed}",
                    "steps": 20,
                    "cfg": 7,
                    "sampler_name": "euler",
                    "scheduler": "normal",
                    "denoise": 1,
                    "model": ["1", 0],
                    "positive": ["2", 0],
                    "negative": ["3", 0],
                    "latent_image": ["4", 0]
                }
            },
            "6": {
                "class_type": "VAEDecode",
                "inputs": {
                    "samples": ["5", 0],
                    "vae": ["1", 2]
                }
            },
            "7": {
                "class_type": "SaveImage",
                "inputs": {
                    "filename_prefix": "ComfyUI",
                    "images": ["6", 0]
                }
            }
        }

    def _get_image_to_image_workflow(self) -> Dict:
        """Get image-to-image workflow template"""
        return {
            "1": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {
                    "ckpt_name": "v1-5-pruned.ckpt"
                }
            },
            "2": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "text": "{prompt}",
                    "clip": ["1", 1]
                }
            },
            "3": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "text": "{negative_prompt}",
                    "clip": ["1", 1]
                }
            },
            "4": {
                "class_type": "LoadImage",
                "inputs": {
                    "image": "{input_image}"
                }
            },
            "5": {
                "class_type": "VAEEncode",
                "inputs": {
                    "pixels": ["4", 0],
                    "vae": ["1", 2]
                }
            },
            "6": {
                "class_type": "KSampler",
                "inputs": {
                    "seed": "{seed}",
                    "steps": 20,
                    "cfg": 7,
                    "sampler_name": "euler",
                    "scheduler": "normal",
                    "denoise": 0.75,
                    "model": ["1", 0],
                    "positive": ["2", 0],
                    "negative": ["3", 0],
                    "latent_image": ["5", 0]
                }
            },
            "7": {
                "class_type": "VAEDecode",
                "inputs": {
                    "samples": ["6", 0],
                    "vae": ["1", 2]
                }
            },
            "8": {
                "class_type": "SaveImage",
                "inputs": {
                    "filename_prefix": "img2img",
                    "images": ["7", 0]
                }
            }
        }

    def _get_upscaling_workflow(self) -> Dict:
        """Get upscaling workflow template"""
        return {
            "1": {
                "class_type": "LoadImage",
                "inputs": {
                    "image": "{input_image}"
                }
            },
            "2": {
                "class_type": "UpscaleModelLoader",
                "inputs": {
                    "model_name": "4x-UltraSharp"
                }
            },
            "3": {
                "class_type": "ImageUpscaleWithModel",
                "inputs": {
                    "upscale_model": ["2", 0],
                    "image": ["1", 0]
                }
            },
            "4": {
                "class_type": "SaveImage",
                "inputs": {
                    "filename_prefix": "upscaled",
                    "images": ["3", 0]
                }
            }
        }

    def _get_inpainting_workflow(self) -> Dict:
        """Get inpainting workflow template"""
        return {
            "1": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {
                    "ckpt_name": "v1-5-pruned.ckpt"
                }
            },
            "2": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "text": "{prompt}",
                    "clip": ["1", 1]
                }
            },
            "3": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "text": "{negative_prompt}",
                    "clip": ["1", 1]
                }
            },
            "4": {
                "class_type": "LoadImage",
                "inputs": {
                    "image": "{input_image}"
                }
            },
            "5": {
                "class_type": "LoadImage",
                "inputs": {
                    "image": "{mask_image}"
                }
            },
            "6": {
                "class_type": "VAEEncode",
                "inputs": {
                    "pixels": ["4", 0],
                    "vae": ["1", 2]
                }
            },
            "7": {
                "class_type": "VAEEncode",
                "inputs": {
                    "pixels": ["5", 0],
                    "vae": ["1", 2]
                }
            },
            "8": {
                "class_type": "KSampler",
                "inputs": {
                    "seed": "{seed}",
                    "steps": 20,
                    "cfg": 7,
                    "sampler_name": "euler",
                    "scheduler": "normal",
                    "denoise": 1,
                    "model": ["1", 0],
                    "positive": ["2", 0],
                    "negative": ["3", 0],
                    "latent_image": ["6", 0]
                }
            },
            "9": {
                "class_type": "VAEDecode",
                "inputs": {
                    "samples": ["8", 0],
                    "vae": ["1", 2]
                }
            },
            "10": {
                "class_type": "SaveImage",
                "inputs": {
                    "filename_prefix": "inpainted",
                    "images": ["9", 0]
                }
            }
        }

    def _get_controlnet_workflow(self) -> Dict:
        """Get ControlNet workflow template"""
        return {
            "1": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {
                    "ckpt_name": "v1-5-pruned.ckpt"
                }
            },
            "2": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "text": "{prompt}",
                    "clip": ["1", 1]
                }
            },
            "3": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "text": "{negative_prompt}",
                    "clip": ["1", 1]
                }
            },
            "4": {
                "class_type": "ControlNetLoader",
                "inputs": {
                    "control_net_name": "control_canny"
                }
            },
            "5": {
                "class_type": "LoadImage",
                "inputs": {
                    "image": "{control_image}"
                }
            },
            "6": {
                "class_type": "ControlNetApply",
                "inputs": {
                    "strength": 1,
                    "conditioning": ["2", 0],
                    "control_net": ["4", 0],
                    "image": ["5", 0]
                }
            },
            "7": {
                "class_type": "EmptyLatentImage",
                "inputs": {
                    "width": 512,
                    "height": 512,
                    "batch_size": 1
                }
            },
            "8": {
                "class_type": "KSampler",
                "inputs": {
                    "seed": "{seed}",
                    "steps": 20,
                    "cfg": 7,
                    "sampler_name": "euler",
                    "scheduler": "normal",
                    "denoise": 1,
                    "model": ["1", 0],
                    "positive": ["6", 0],
                    "negative": ["3", 0],
                    "latent_image": ["7", 0]
                }
            },
            "9": {
                "class_type": "VAEDecode",
                "inputs": {
                    "samples": ["8", 0],
                    "vae": ["1", 2]
                }
            },
            "10": {
                "class_type": "SaveImage",
                "inputs": {
                    "filename_prefix": "controlnet",
                    "images": ["9", 0]
                }
            }
        }

    async def _check_server_status(self) -> bool:
        """Check if ComfyUI server is running"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_base_url}/system_stats", timeout=5) as response:
                    if response.status == 200:
                        self.is_server_running = True
                        return True
        except Exception:
            pass

        self.is_server_running = False
        return False

    async def _start_server(self):
        """Start ComfyUI server"""
        if self.is_server_running:
            return

        try:
            # Prepare server command
            cmd = [
                "python", "main.py",
                "--port", str(self.server_port),
                "--listen", "127.0.0.1",
                "--enable-cors-header"
            ]

            # Start server process
            self.server_process = subprocess.Popen(
                cmd,
                cwd=self.comfyui_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )

            # Wait for server to start
            await asyncio.sleep(10)

            # Verify server is running
            if await self._check_server_status():
                logger.info(f"ComfyUI server started on port {self.server_port}")
                self.is_server_running = True
            else:
                logger.error("Failed to start ComfyUI server")
                if self.server_process:
                    self.server_process.terminate()

        except Exception as e:
            logger.error(f"Error starting ComfyUI server: {e}")

    async def execute_workflow(self,
                             workflow_type: str,
                             parameters: Dict[str, Any],
                             output_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute a ComfyUI workflow

        Args:
            workflow_type: Type of workflow to execute
            parameters: Workflow parameters
            output_dir: Optional output directory

        Returns:
            Execution result with file paths and metadata
        """
        if not self.is_server_running:
            return {"success": False, "error": "ComfyUI server not running"}

        workflow_id = str(uuid.uuid4())
        start_time = time.time()

        try:
            # Get workflow template
            template = self.workflow_templates.get(workflow_type)
            if not template:
                return {"success": False, "error": f"Unknown workflow type: {workflow_type}"}

            # Prepare workflow with parameters
            workflow = await self._prepare_workflow(template, parameters)

            # Check resources
            if not await self._check_resources():
                return {"success": False, "error": "Insufficient resources available"}

            # Execute workflow
            result = await self._execute_workflow_api(workflow, workflow_id, output_dir)

            # Track execution
            execution_time = time.time() - start_time
            await self._track_workflow_execution(workflow_type, execution_time, result["success"])

            return result

        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            await self._track_workflow_execution(workflow_type, time.time() - start_time, False)
            return {"success": False, "error": str(e)}

    async def _prepare_workflow(self, template: Dict, parameters: Dict[str, Any]) -> Dict:
        """Prepare workflow with parameters"""
        workflow = json.loads(json.dumps(template))  # Deep copy

        # Replace parameter placeholders
        for node_id, node_data in workflow.items():
            for input_name, input_value in node_data.get("inputs", {}).items():
                if isinstance(input_value, str) and input_value.startswith("{"):
                    param_name = input_value.strip("{}")
                    if param_name in parameters:
                        workflow[node_id]["inputs"][input_name] = parameters[param_name]

        return workflow

    async def _check_resources(self) -> bool:
        """Check if sufficient resources are available"""
        # Check GPU memory if available
        gpu_info = self.hardware_detector.get_gpu_info()
        if gpu_info and "memory" in gpu_info:
            total_memory = gpu_info["memory"].get("total", 0)
            used_memory = gpu_info["memory"].get("used", 0)

            if total_memory > 0:
                usage_percent = used_memory / total_memory
                if usage_percent > self.gpu_memory_limit:
                    logger.warning(f"GPU memory usage too high: {usage_percent:.2%}")
                    return False

        # Check concurrent workflows
        active_count = len([w for w in self.active_workflows.values() if w["status"] == "running"])
        if active_count >= self.max_concurrent_workflows:
            logger.warning(f"Maximum concurrent workflows reached: {active_count}")
            return False

        return True

    async def _execute_workflow_api(self, workflow: Dict, workflow_id: str, output_dir: Optional[str]) -> Dict[str, Any]:
        """Execute workflow via ComfyUI API"""
        try:
            async with aiohttp.ClientSession() as session:
                # Submit workflow
                submit_data = {
                    "prompt": workflow,
                    "client_id": workflow_id
                }

                async with session.post(f"{self.api_base_url}/prompt", json=submit_data) as response:
                    if response.status != 200:
                        return {"success": False, "error": f"API error: {response.status}"}

                    result = await response.json()
                    prompt_id = result.get("prompt_id")

                    if not prompt_id:
                        return {"success": False, "error": "No prompt ID returned"}

                # Monitor execution
                execution_result = await self._monitor_workflow_execution(prompt_id, workflow_id, output_dir)
                return execution_result

        except Exception as e:
            logger.error(f"Workflow API execution failed: {e}")
            return {"success": False, "error": str(e)}

    async def _monitor_workflow_execution(self, prompt_id: str, workflow_id: str, output_dir: Optional[str], max_wait: int = 300) -> Dict[str, Any]:
        """Monitor workflow execution and collect results"""
        start_time = time.time()

        # Track active workflow
        self.active_workflows[workflow_id] = {
            "prompt_id": prompt_id,
            "status": "running",
            "start_time": start_time,
            "progress": 0
        }

        try:
            async with aiohttp.ClientSession() as session:
                while time.time() - start_time < max_wait:
                    # Check status
                    async with session.get(f"{self.api_base_url}/prompt/{prompt_id}") as response:
                        if response.status == 200:
                            status_data = await response.json()

                            if status_data.get("status") == "completed":
                                # Get execution results
                                return await self._collect_results(prompt_id, workflow_id, output_dir, session)
                            elif status_data.get("status") == "error":
                                error_msg = status_data.get("error", "Unknown error")
                                logger.error(f"Workflow execution error: {error_msg}")
                                return {"success": False, "error": error_msg}

                    await asyncio.sleep(2)

                # Timeout
                logger.error(f"Workflow execution timed out: {workflow_id}")
                return {"success": False, "error": "Execution timeout"}

        except Exception as e:
            logger.error(f"Error monitoring workflow: {e}")
            return {"success": False, "error": str(e)}

        finally:
            # Clean up active workflow tracking
            if workflow_id in self.active_workflows:
                del self.active_workflows[workflow_id]

    async def _collect_results(self, prompt_id: str, workflow_id: str, output_dir: Optional[str], session: aiohttp.ClientSession) -> Dict[str, Any]:
        """Collect workflow execution results"""
        try:
            # Get history
            async with session.get(f"{self.api_base_url}/history/{prompt_id}") as response:
                if response.status == 200:
                    history = await response.json()

                    # Extract output files
                    output_files = await self._extract_output_files(history, output_dir)

                    # Store results
                    result = {
                        "success": True,
                        "workflow_id": workflow_id,
                        "prompt_id": prompt_id,
                        "output_files": output_files,
                        "execution_time": time.time() - self.active_workflows[workflow_id]["start_time"]
                    }

                    self.workflow_results[workflow_id] = result
                    return result

            return {"success": False, "error": "Failed to collect results"}

        except Exception as e:
            logger.error(f"Error collecting results: {e}")
            return {"success": False, "error": str(e)}

    async def _extract_output_files(self, history: Dict, output_dir: Optional[str]) -> List[str]:
        """Extract output file paths from workflow history"""
        output_files = []

        try:
            # Parse history to find SaveImage nodes
            for prompt_data in history.values():
                outputs = prompt_data.get("outputs", {})

                for node_id, node_output in outputs.items():
                    if "images" in node_output:
                        for image_info in node_output["images"]:
                            # Get image file path
                            image_path = os.path.join(self.comfyui_path, "output", image_info["filename"])

                            if os.path.exists(image_path):
                                if output_dir:
                                    # Copy to output directory
                                    dest_path = os.path.join(output_dir, image_info["filename"])
                                    shutil.copy2(image_path, dest_path)
                                    output_files.append(dest_path)
                                else:
                                    output_files.append(image_path)

        except Exception as e:
            logger.error(f"Error extracting output files: {e}")

        return output_files

    async def _track_workflow_execution(self, workflow_type: str, execution_time: float, success: bool):
        """Track workflow execution statistics"""
        self.workflow_stats["total_workflows"] += 1

        if success:
            self.workflow_stats["successful_workflows"] += 1
        else:
            self.workflow_stats["failed_workflows"] += 1

        # Update average execution time
        total_time = self.workflow_stats["average_execution_time"] * (self.workflow_stats["total_workflows"] - 1)
        self.workflow_stats["average_execution_time"] = (total_time + execution_time) / self.workflow_stats["total_workflows"]

        # Track costs if cost tracker available
        if self.cost_tracker:
            await self.cost_tracker.track_custom_usage("comfyui", {
                "workflow_type": workflow_type,
                "execution_time": execution_time,
                "success": success,
                "timestamp": datetime.now().isoformat()
            })

    async def get_available_workflows(self) -> List[Dict[str, Any]]:
        """Get list of available workflow templates"""
        return [
            {
                "name": name,
                "description": template["description"],
                "category": template["category"]
            }
            for name, template in self.workflow_templates.items()
        ]

    async def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific workflow"""
        return self.active_workflows.get(workflow_id)

    async def get_system_stats(self) -> Dict[str, Any]:
        """Get ComfyUI system statistics"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_base_url}/system_stats") as response:
                    if response.status == 200:
                        return await response.json()
        except Exception as e:
            logger.error(f"Error getting system stats: {e}")

        return {}

    async def stop_server(self):
        """Stop ComfyUI server"""
        if self.server_process:
            try:
                self.server_process.terminate()
                await asyncio.sleep(5)

                if self.server_process.poll() is None:
                    self.server_process.kill()

                self.is_server_running = False
                logger.info("ComfyUI server stopped")

            except Exception as e:
                logger.error(f"Error stopping ComfyUI server: {e}")

    async def cleanup(self):
        """Clean up resources"""
        await self.stop_server()

        # Clean up temporary files
        for workflow_id, result in self.workflow_results.items():
            for file_path in result.get("output_files", []):
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                except Exception as e:
                    logger.error(f"Error cleaning up file {file_path}: {e}")

# Global instance
comfyui_manager = ComfyUIManager()

async def initialize_comfyui() -> bool:
    """Initialize ComfyUI integration"""
    return await comfyui_manager.initialize()

async def execute_comfyui_workflow(workflow_type: str, parameters: Dict[str, Any], output_dir: Optional[str] = None) -> Dict[str, Any]:
    """Execute ComfyUI workflow"""
    return await comfyui_manager.execute_workflow(workflow_type, parameters, output_dir)

def get_comfyui_manager() -> ComfyUIManager:
    """Get the global ComfyUI manager instance"""
    return comfyui_manager