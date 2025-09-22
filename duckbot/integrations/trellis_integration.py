"""
Microsoft TRELLIS Integration for DuckBot Enhanced v4.2
Provides 3D asset generation and structured AI workflow management
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
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime
import uuid

from ..core.cost_management import CostTracker
from ..core.hardware_detector import HardwareDetector

logger = logging.getLogger(__name__)

class TRELLISManager:
    """Manages Microsoft TRELLIS 3D asset generation and workflow organization"""

    def __init__(self,
                 trellis_path: Optional[str] = None,
                 api_base_url: str = "http://localhost:8288",
                 cost_tracker: Optional[CostTracker] = None):
        """
        Initialize TRELLIS Manager

        Args:
            trellis_path: Path to TRELLIS installation
            api_base_url: TRELLIS API base URL
            cost_tracker: Optional cost tracking instance
        """
        self.trellis_path = trellis_path or self._find_trellis_path()
        self.api_base_url = api_base_url.rstrip('/')
        self.cost_tracker = cost_tracker
        self.hardware_detector = HardwareDetector()

        # Server management
        self.server_process = None
        self.server_port = 8288
        self.is_server_running = False

        # 3D asset generation
        self.asset_templates = {}
        self.active_generations = {}
        self.asset_library = {}

        # Workflow organization
        self.workflow_structures = {}
        self.task_dependencies = {}
        self.execution_graphs = {}

        # Performance tracking
        self.generation_stats = {
            "total_assets": 0,
            "successful_assets": 0,
            "failed_assets": 0,
            "average_generation_time": 0,
            "gpu_usage_peak": 0,
            "output_formats": {
                "radiance_fields": 0,
                "gaussians": 0,
                "meshes": 0
            }
        }

    def _find_trellis_path(self) -> Optional[str]:
        """Find TRELLIS installation path"""
        possible_paths = [
            "C:/TRELLIS",
            "C:/Program Files/TRELLIS",
            "D:/TRELLIS",
            os.path.expanduser("~/TRELLIS"),
            "./TRELLIS"
        ]

        for path in possible_paths:
            if os.path.exists(path) and (
                os.path.exists(os.path.join(path, "main.py")) or
                os.path.exists(os.path.join(path, "app.py"))
            ):
                logger.info(f"Found TRELLIS at: {path}")
                return path

        logger.warning("TRELLIS installation not found. Please install TRELLIS.")
        return None

    async def initialize(self) -> bool:
        """Initialize TRELLIS integration"""
        if not self.trellis_path:
            logger.error("TRELLIS path not found")
            return False

        try:
            # Check if TRELLIS is properly installed
            if not await self._validate_trellis_installation():
                return False

            # Load asset templates
            await self._load_asset_templates()

            # Initialize workflow structures
            await self._initialize_workflow_structures()

            # Start server if not running
            if not await self._check_server_status():
                await self._start_server()

            logger.info("TRELLIS integration initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize TRELLIS: {e}")
            return False

    async def _validate_trellis_installation(self) -> bool:
        """Validate TRELLIS installation"""
        # Check for required files
        required_patterns = ["*.py", "models/*", "configs/*"]

        for pattern in required_patterns:
            if not any(Path(self.trellis_path).glob(pattern)):
                logger.warning(f"TRELLIS installation missing files matching pattern: {pattern}")
                # Continue with installation as structure might vary

        # Check for required dependencies
        try:
            import torch
            import numpy as np
            import trimesh
            logger.info("3D processing dependencies available")
            return True
        except ImportError as e:
            logger.error(f"Missing 3D processing dependencies: {e}")
            return False

    async def _load_asset_templates(self):
        """Load 3D asset generation templates"""
        self.asset_templates = {
            "text_to_3d": {
                "description": "Generate 3D assets from text descriptions",
                "input_type": "text",
                "output_formats": ["radiance_fields", "gaussians", "meshes"],
                "parameters": {
                    "text_prompt": "string",
                    "resolution": "int[256,512,1024]",
                    "quality": "string[low,medium,high]",
                    "style": "string[realistic,stylized,abstract]"
                }
            },
            "image_to_3d": {
                "description": "Generate 3D assets from 2D images",
                "input_type": "image",
                "output_formats": ["radiance_fields", "gaussians", "meshes"],
                "parameters": {
                    "input_image": "image_path",
                    "resolution": "int[256,512,1024]",
                    "quality": "string[low,medium,high]",
                    "multi_view": "boolean"
                }
            },
            "multi_view_to_3d": {
                "description": "Generate 3D assets from multiple view images",
                "input_type": "multi_image",
                "output_formats": ["radiance_fields", "gaussians", "meshes"],
                "parameters": {
                    "input_images": "image_path_list",
                    "camera_poses": "pose_list",
                    "resolution": "int[256,512,1024]",
                    "quality": "string[low,medium,high]"
                }
            },
            "mesh_refinement": {
                "description": "Refine and optimize existing 3D meshes",
                "input_type": "mesh",
                "output_formats": ["meshes"],
                "parameters": {
                    "input_mesh": "mesh_path",
                    "target_polygons": "int",
                    "smoothing": "boolean",
                    "watertight": "boolean"
                }
            },
            "style_transfer_3d": {
                "description": "Apply artistic styles to 3D assets",
                "input_type": "mesh+text",
                "output_formats": ["meshes"],
                "parameters": {
                    "input_mesh": "mesh_path",
                    "style_prompt": "string",
                    "strength": "float[0,1]"
                }
            }
        }

        logger.info(f"Loaded {len(self.asset_templates)} 3D asset templates")

    async def _initialize_workflow_structures(self):
        """Initialize TRELLIS workflow structures"""
        self.workflow_structures = {
            "sequential": {
                "description": "Linear execution of tasks",
                "structure": "chain",
                "use_cases": ["simple_generation", "basic_processing"]
            },
            "parallel": {
                "description": "Concurrent execution of independent tasks",
                "structure": "tree",
                "use_cases": ["batch_processing", "multi_asset_generation"]
            },
            "hierarchical": {
                "description": "Organized task hierarchy with dependencies",
                "structure": "dag",
                "use_cases": ["complex_workflows", "multi_stage_processing"]
            },
            "adaptive": {
                "description": "Dynamic workflow adaptation based on results",
                "structure": "dynamic_graph",
                "use_cases": ["intelligent_processing", "quality_aware_generation"]
            }
        }

    async def _check_server_status(self) -> bool:
        """Check if TRELLIS server is running"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_base_url}/health", timeout=5) as response:
                    if response.status == 200:
                        self.is_server_running = True
                        return True
        except Exception:
            pass

        self.is_server_running = False
        return False

    async def _start_server(self):
        """Start TRELLIS server"""
        if self.is_server_running:
            return

        try:
            # Prepare server command
            cmd = [
                "python", "app.py",
                "--port", str(self.server_port),
                "--host", "127.0.0.1"
            ]

            # Set environment variables
            env = os.environ.copy()
            env["PYTHONPATH"] = self.trellis_path

            # Start server process
            self.server_process = subprocess.Popen(
                cmd,
                cwd=self.trellis_path,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )

            # Wait for server to start
            await asyncio.sleep(15)

            # Verify server is running
            if await self._check_server_status():
                logger.info(f"TRELLIS server started on port {self.server_port}")
                self.is_server_running = True
            else:
                logger.error("Failed to start TRELLIS server")
                if self.server_process:
                    self.server_process.terminate()

        except Exception as e:
            logger.error(f"Error starting TRELLIS server: {e}")

    async def generate_3d_asset(self,
                              asset_type: str,
                              parameters: Dict[str, Any],
                              output_format: str = "gaussians",
                              output_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate 3D asset using TRELLIS

        Args:
            asset_type: Type of 3D asset to generate
            parameters: Generation parameters
            output_format: Output format (radiance_fields, gaussians, meshes)
            output_dir: Optional output directory

        Returns:
            Generation result with file paths and metadata
        """
        if not self.is_server_running:
            return {"success": False, "error": "TRELLIS server not running"}

        generation_id = str(uuid.uuid4())
        start_time = time.time()

        try:
            # Validate asset type
            template = self.asset_templates.get(asset_type)
            if not template:
                return {"success": False, "error": f"Unknown asset type: {asset_type}"}

            # Validate output format
            if output_format not in template["output_formats"]:
                return {"success": False, "error": f"Unsupported output format: {output_format}"}

            # Prepare generation request
            request_data = {
                "asset_type": asset_type,
                "parameters": parameters,
                "output_format": output_format,
                "generation_id": generation_id
            }

            # Check resources
            if not await self._check_generation_resources():
                return {"success": False, "error": "Insufficient resources available"}

            # Execute generation
            result = await self._execute_generation_api(request_data, output_dir)

            # Track generation
            execution_time = time.time() - start_time
            await self._track_asset_generation(asset_type, output_format, execution_time, result["success"])

            return result

        except Exception as e:
            logger.error(f"3D asset generation failed: {e}")
            await self._track_asset_generation(asset_type, output_format, time.time() - start_time, False)
            return {"success": False, "error": str(e)}

    async def _check_generation_resources(self) -> bool:
        """Check if sufficient resources are available for 3D generation"""
        # Check GPU memory
        gpu_info = self.hardware_detector.get_gpu_info()
        if gpu_info and "memory" in gpu_info:
            total_memory = gpu_info["memory"].get("total", 0)
            used_memory = gpu_info["memory"].get("used", 0)

            if total_memory > 0:
                usage_percent = used_memory / total_memory
                if usage_percent > 0.9:  # 90% limit for 3D generation
                    logger.warning(f"GPU memory usage too high for 3D generation: {usage_percent:.2%}")
                    return False

        # Check concurrent generations
        active_count = len([g for g in self.active_generations.values() if g["status"] == "generating"])
        if active_count >= 2:  # Max 2 concurrent 3D generations
            logger.warning(f"Maximum concurrent 3D generations reached: {active_count}")
            return False

        return True

    async def _execute_generation_api(self, request_data: Dict, output_dir: Optional[str]) -> Dict[str, Any]:
        """Execute 3D asset generation via TRELLIS API"""
        try:
            async with aiohttp.ClientSession() as session:
                # Submit generation request
                async with session.post(f"{self.api_base_url}/generate", json=request_data) as response:
                    if response.status != 200:
                        return {"success": False, "error": f"API error: {response.status}"}

                    result = await response.json()
                    generation_id = result.get("generation_id")

                    if not generation_id:
                        return {"success": False, "error": "No generation ID returned"}

                # Monitor generation
                generation_result = await self._monitor_generation(generation_id, output_dir)
                return generation_result

        except Exception as e:
            logger.error(f"TRELLIS API generation failed: {e}")
            return {"success": False, "error": str(e)}

    async def _monitor_generation(self, generation_id: str, output_dir: Optional[str], max_wait: int = 600) -> Dict[str, Any]:
        """Monitor 3D asset generation and collect results"""
        start_time = time.time()

        # Track active generation
        self.active_generations[generation_id] = {
            "generation_id": generation_id,
            "status": "generating",
            "start_time": start_time,
            "progress": 0
        }

        try:
            async with aiohttp.ClientSession() as session:
                while time.time() - start_time < max_wait:
                    # Check status
                    async with session.get(f"{self.api_base_url}/generation/{generation_id}") as response:
                        if response.status == 200:
                            status_data = await response.json()

                            if status_data.get("status") == "completed":
                                # Get generation results
                                return await self._collect_generation_results(generation_id, output_dir, session)
                            elif status_data.get("status") == "error":
                                error_msg = status_data.get("error", "Unknown error")
                                logger.error(f"3D generation error: {error_msg}")
                                return {"success": False, "error": error_msg}
                            elif status_data.get("status") == "processing":
                                # Update progress
                                progress = status_data.get("progress", 0)
                                self.active_generations[generation_id]["progress"] = progress

                    await asyncio.sleep(5)

                # Timeout
                logger.error(f"3D generation timed out: {generation_id}")
                return {"success": False, "error": "Generation timeout"}

        except Exception as e:
            logger.error(f"Error monitoring 3D generation: {e}")
            return {"success": False, "error": str(e)}

        finally:
            # Clean up active generation tracking
            if generation_id in self.active_generations:
                del self.active_generations[generation_id]

    async def _collect_generation_results(self, generation_id: str, output_dir: Optional[str], session: aiohttp.ClientSession) -> Dict[str, Any]:
        """Collect 3D asset generation results"""
        try:
            # Get results
            async with session.get(f"{self.api_base_url}/results/{generation_id}") as response:
                if response.status == 200:
                    results = await response.json()

                    # Process output files
                    output_files = await self._process_output_files(results, output_dir)

                    # Store in asset library
                    asset_metadata = {
                        "generation_id": generation_id,
                        "timestamp": datetime.now().isoformat(),
                        "output_files": output_files,
                        "parameters": results.get("parameters", {}),
                        "quality_metrics": results.get("quality_metrics", {})
                    }

                    self.asset_library[generation_id] = asset_metadata

                    return {
                        "success": True,
                        "generation_id": generation_id,
                        "output_files": output_files,
                        "metadata": asset_metadata,
                        "execution_time": time.time() - self.active_generations[generation_id]["start_time"]
                    }

            return {"success": False, "error": "Failed to collect generation results"}

        except Exception as e:
            logger.error(f"Error collecting generation results: {e}")
            return {"success": False, "error": str(e)}

    async def _process_output_files(self, results: Dict, output_dir: Optional[str]) -> List[str]:
        """Process and organize output files"""
        output_files = []

        try:
            for file_info in results.get("output_files", []):
                source_path = file_info.get("path")
                if source_path and os.path.exists(source_path):
                    if output_dir:
                        # Copy to output directory
                        dest_path = os.path.join(output_dir, os.path.basename(source_path))
                        shutil.copy2(source_path, dest_path)
                        output_files.append(dest_path)
                    else:
                        output_files.append(source_path)

        except Exception as e:
            logger.error(f"Error processing output files: {e}")

        return output_files

    async def create_workflow_structure(self,
                                      structure_type: str,
                                      tasks: List[Dict[str, Any]],
                                      dependencies: Optional[List[Tuple[str, str]]] = None) -> Dict[str, Any]:
        """
        Create a structured workflow using TRELLIS organization

        Args:
            structure_type: Type of workflow structure
            tasks: List of tasks to organize
            dependencies: Optional task dependencies

        Returns:
            Workflow structure information
        """
        try:
            # Validate structure type
            if structure_type not in self.workflow_structures:
                return {"success": False, "error": f"Unknown structure type: {structure_type}"}

            # Create workflow structure
            workflow_id = str(uuid.uuid4())
            workflow_structure = {
                "workflow_id": workflow_id,
                "structure_type": structure_type,
                "tasks": tasks,
                "dependencies": dependencies or [],
                "created_at": datetime.now().isoformat(),
                "status": "created"
            }

            # Build execution graph
            if structure_type == "hierarchical":
                workflow_structure["execution_graph"] = self._build_dependency_graph(tasks, dependencies)
            elif structure_type == "adaptive":
                workflow_structure["adaptive_rules"] = self._create_adaptive_rules(tasks)

            # Store workflow
            self.execution_graphs[workflow_id] = workflow_structure

            return {
                "success": True,
                "workflow_id": workflow_id,
                "structure": workflow_structure
            }

        except Exception as e:
            logger.error(f"Error creating workflow structure: {e}")
            return {"success": False, "error": str(e)}

    def _build_dependency_graph(self, tasks: List[Dict], dependencies: List[Tuple[str, str]]) -> Dict:
        """Build dependency graph for tasks"""
        graph = {
            "nodes": [],
            "edges": []
        }

        # Add nodes
        for task in tasks:
            graph["nodes"].append({
                "id": task["id"],
                "type": task.get("type", "generic"),
                "parameters": task.get("parameters", {})
            })

        # Add edges
        for source, target in dependencies:
            graph["edges"].append({
                "source": source,
                "target": target,
                "type": "dependency"
            })

        return graph

    def _create_adaptive_rules(self, tasks: List[Dict]) -> List[Dict]:
        """Create adaptive rules for dynamic workflows"""
        rules = []

        for task in tasks:
            if "adaptive_conditions" in task:
                rules.append({
                    "task_id": task["id"],
                    "conditions": task["adaptive_conditions"],
                    "actions": task.get("adaptive_actions", [])
                })

        return rules

    async def execute_workflow(self, workflow_id: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute a structured workflow"""
        try:
            workflow = self.execution_graphs.get(workflow_id)
            if not workflow:
                return {"success": False, "error": f"Workflow not found: {workflow_id}"}

            workflow["status"] = "running"
            workflow["start_time"] = time.time()

            # Execute based on structure type
            if workflow["structure_type"] == "sequential":
                result = await self._execute_sequential_workflow(workflow, context)
            elif workflow["structure_type"] == "parallel":
                result = await self._execute_parallel_workflow(workflow, context)
            elif workflow["structure_type"] == "hierarchical":
                result = await self._execute_hierarchical_workflow(workflow, context)
            elif workflow["structure_type"] == "adaptive":
                result = await self._execute_adaptive_workflow(workflow, context)
            else:
                return {"success": False, "error": f"Unsupported workflow type: {workflow['structure_type']}"}

            workflow["status"] = "completed"
            workflow["end_time"] = time.time()

            return result

        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            return {"success": False, "error": str(e)}

    async def _execute_sequential_workflow(self, workflow: Dict, context: Optional[Dict]) -> Dict[str, Any]:
        """Execute sequential workflow"""
        results = []

        for task in workflow["tasks"]:
            try:
                task_result = await self._execute_task(task, context)
                results.append(task_result)

                # Check if task failed and workflow should stop
                if not task_result.get("success", False):
                    break

            except Exception as e:
                logger.error(f"Task execution failed: {e}")
                results.append({"success": False, "error": str(e)})
                break

        return {
            "success": all(r.get("success", False) for r in results),
            "workflow_id": workflow["workflow_id"],
            "task_results": results,
            "execution_time": time.time() - workflow["start_time"]
        }

    async def _execute_parallel_workflow(self, workflow: Dict, context: Optional[Dict]) -> Dict[str, Any]:
        """Execute parallel workflow"""
        tasks = []

        for task in workflow["tasks"]:
            tasks.append(self._execute_task(task, context))

        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({"success": False, "error": str(result)})
            else:
                processed_results.append(result)

        return {
            "success": all(r.get("success", False) for r in processed_results),
            "workflow_id": workflow["workflow_id"],
            "task_results": processed_results,
            "execution_time": time.time() - workflow["start_time"]
        }

    async def _execute_hierarchical_workflow(self, workflow: Dict, context: Optional[Dict]) -> Dict[str, Any]:
        """Execute hierarchical workflow with dependencies"""
        # This is a simplified implementation
        # In a full implementation, you'd use a proper topological sort
        return await self._execute_sequential_workflow(workflow, context)

    async def _execute_adaptive_workflow(self, workflow: Dict, context: Optional[Dict]) -> Dict[str, Any]:
        """Execute adaptive workflow"""
        results = []
        execution_context = context or {}

        for task in workflow["tasks"]:
            try:
                # Check adaptive conditions
                should_execute = True
                if "adaptive_rules" in workflow:
                    for rule in workflow["adaptive_rules"]:
                        if rule["task_id"] == task["id"]:
                            should_execute = self._evaluate_conditions(rule["conditions"], execution_context)
                            break

                if should_execute:
                    task_result = await self._execute_task(task, execution_context)
                    results.append(task_result)

                    # Update execution context
                    if task_result.get("success"):
                        execution_context[task["id"]] = task_result

                else:
                    results.append({"success": True, "skipped": True, "task_id": task["id"]})

            except Exception as e:
                logger.error(f"Adaptive task execution failed: {e}")
                results.append({"success": False, "error": str(e), "task_id": task["id"]})

        return {
            "success": all(r.get("success", False) for r in results if not r.get("skipped", False)),
            "workflow_id": workflow["workflow_id"],
            "task_results": results,
            "execution_context": execution_context,
            "execution_time": time.time() - workflow["start_time"]
        }

    def _evaluate_conditions(self, conditions: List[Dict], context: Dict) -> bool:
        """Evaluate adaptive conditions"""
        for condition in conditions:
            field = condition.get("field")
            operator = condition.get("operator", "equals")
            value = condition.get("value")

            context_value = context.get(field)

            if operator == "equals":
                if context_value != value:
                    return False
            elif operator == "greater_than":
                if not context_value or context_value <= value:
                    return False
            elif operator == "less_than":
                if not context_value or context_value >= value:
                    return False

        return True

    async def _execute_task(self, task: Dict, context: Optional[Dict]) -> Dict[str, Any]:
        """Execute a single task"""
        task_type = task.get("type")
        parameters = task.get("parameters", {})

        # Route task execution based on type
        if task_type == "3d_generation":
            return await self.generate_3d_asset(
                parameters.get("asset_type"),
                parameters.get("generation_params", {}),
                parameters.get("output_format", "gaussians")
            )
        elif task_type == "comfyui_workflow":
            # This would integrate with ComfyUI
            return {"success": True, "message": "ComfyUI integration placeholder"}
        elif task_type == "voice_generation":
            # This would integrate with VibeVoice
            return {"success": True, "message": "VibeVoice integration placeholder"}
        else:
            return {"success": False, "error": f"Unknown task type: {task_type}"}

    async def _track_asset_generation(self, asset_type: str, output_format: str, execution_time: float, success: bool):
        """Track 3D asset generation statistics"""
        self.generation_stats["total_assets"] += 1

        if success:
            self.generation_stats["successful_assets"] += 1
            self.generation_stats["output_formats"][output_format] += 1
        else:
            self.generation_stats["failed_assets"] += 1

        # Update average execution time
        total_time = self.generation_stats["average_generation_time"] * (self.generation_stats["total_assets"] - 1)
        self.generation_stats["average_generation_time"] = (total_time + execution_time) / self.generation_stats["total_assets"]

        # Track costs if cost tracker available
        if self.cost_tracker:
            await self.cost_tracker.track_custom_usage("trellis", {
                "asset_type": asset_type,
                "output_format": output_format,
                "execution_time": execution_time,
                "success": success,
                "timestamp": datetime.now().isoformat()
            })

    async def get_available_asset_types(self) -> List[Dict[str, Any]]:
        """Get list of available 3D asset types"""
        return [
            {
                "name": name,
                "description": template["description"],
                "input_type": template["input_type"],
                "output_formats": template["output_formats"]
            }
            for name, template in self.asset_templates.items()
        ]

    async def get_workflow_structures(self) -> List[Dict[str, Any]]:
        """Get list of available workflow structures"""
        return [
            {
                "name": name,
                "description": structure["description"],
                "structure": structure["structure"],
                "use_cases": structure["use_cases"]
            }
            for name, structure in self.workflow_structures.items()
        ]

    async def get_generation_status(self, generation_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific 3D generation"""
        return self.active_generations.get(generation_id)

    async def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific workflow"""
        return self.execution_graphs.get(workflow_id)

    async def get_asset_library(self) -> Dict[str, Any]:
        """Get asset library information"""
        return {
            "total_assets": len(self.asset_library),
            "assets": list(self.asset_library.values()),
            "formats": {
                format_name: sum(1 for asset in self.asset_library.values()
                               if any(format_name in file for file in asset.get("output_files", [])))
                for format_name in ["radiance_fields", "gaussians", "meshes"]
            }
        }

    async def stop_server(self):
        """Stop TRELLIS server"""
        if self.server_process:
            try:
                self.server_process.terminate()
                await asyncio.sleep(5)

                if self.server_process.poll() is None:
                    self.server_process.kill()

                self.is_server_running = False
                logger.info("TRELLIS server stopped")

            except Exception as e:
                logger.error(f"Error stopping TRELLIS server: {e}")

    async def cleanup(self):
        """Clean up resources"""
        await self.stop_server()

        # Clean up temporary files
        for asset in self.asset_library.values():
            for file_path in asset.get("output_files", []):
                try:
                    if os.path.exists(file_path) and "temp" in file_path:
                        os.remove(file_path)
                except Exception as e:
                    logger.error(f"Error cleaning up file {file_path}: {e}")

# Global instance
trellis_manager = TRELLISManager()

async def initialize_trellis() -> bool:
    """Initialize TRELLIS integration"""
    return await trellis_manager.initialize()

async def generate_3d_asset(asset_type: str, parameters: Dict[str, Any], output_format: str = "gaussians", output_dir: Optional[str] = None) -> Dict[str, Any]:
    """Generate 3D asset using TRELLIS"""
    return await trellis_manager.generate_3d_asset(asset_type, parameters, output_format, output_dir)

async def create_workflow_structure(structure_type: str, tasks: List[Dict[str, Any]], dependencies: Optional[List[Tuple[str, str]]] = None) -> Dict[str, Any]:
    """Create structured workflow"""
    return await trellis_manager.create_workflow_structure(structure_type, tasks, dependencies)

def get_trellis_manager() -> TRELLISManager:
    """Get the global TRELLIS manager instance"""
    return trellis_manager