#!/usr/bin/env python3
"""
DuckBot AutoTrain-Advanced Integration Module
Seamless integration with Hugging Face AutoTrain-Advanced for no-code ML training
Provides unified interface for model training with AutoTrain's powerful capabilities

Features:
- No-code ML training with AutoTrain-Advanced
- Support for LLM fine-tuning, text classification, and more
- Local and Hugging Face Spaces deployment
- Real-time job monitoring and logging
- Integrated with DuckBot service management
- Configuration management and templates
- Results processing and model deployment
"""

import os
import sys
import json
import yaml
import time
import logging
import asyncio
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum
import requests
from datetime import datetime, timedelta
import tempfile
import shutil

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import DuckBot modules
try:
    from duckbot.core.service_manager import UnifiedServiceManager, ServiceInfo, ServiceType, ServiceStatus
    from duckbot.core.monitoring_system import MonitoringSystem
    from duckbot.core.cost_management import CostTracker
except ImportError as e:
    logging.warning(f"DuckBot modules not available: {e}")
    UnifiedServiceManager = None
    MonitoringSystem = None
    CostTracker = None

# Try to import AutoTrain-Advanced
try:
    import autotrain
    AUTOTRAIN_AVAILABLE = True
except ImportError:
    AUTOTRAIN_AVAILABLE = False
    logging.warning("AutoTrain-Advanced not available. Install with: pip install autotrain-advanced")

class AutoTrainProjectType(Enum):
    """Supported AutoTrain project types"""
    LLM_FINE_TUNING = "llm_finetuning"
    TEXT_CLASSIFICATION = "text_classification"
    TOKEN_CLASSIFICATION = "token_classification"
    TEXT_GENERATION = "text_generation"
    SEQ2SEQ = "seq2seq"
    IMAGE_CLASSIFICATION = "image_classification"
    OBJECT_DETECTION = "object_detection"
    SENTIMENT_ANALYSIS = "sentiment_analysis"

class AutoTrainDeploymentTarget(Enum):
    """Deployment targets for AutoTrain projects"""
    LOCAL = "local"
    HUGGINGFACE_SPACES = "spaces"
    BOTH = "both"

@dataclass
class AutoTrainConfig:
    """Configuration for AutoTrain projects"""
    project_name: str
    project_type: AutoTrainProjectType
    data_path: str
    model_name: str
    deployment_target: AutoTrainDeploymentTarget = AutoTrainDeploymentTarget.LOCAL

    # Training parameters
    learning_rate: float = 2e-5
    num_epochs: int = 3
    batch_size: int = 8
    max_length: int = 512
    warmup_ratio: float = 0.1

    # Hardware configuration
    use_gpu: bool = True
    mixed_precision: bool = True
    gradient_accumulation: int = 1

    # Advanced options
    use_peft: bool = True
    quantization: bool = False
    gradient_checkpointing: bool = True

    # Hugging Face integration
    hf_token: Optional[str] = None
    hf_repo_id: Optional[str] = None
    push_to_hub: bool = False

    # Logging and monitoring
    log_level: str = "INFO"
    save_steps: int = 500
    eval_steps: int = 100

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        config_dict = asdict(self)
        config_dict['project_type'] = self.project_type.value
        config_dict['deployment_target'] = self.deployment_target.value
        return config_dict

@dataclass
class AutoTrainJob:
    """Represents an AutoTrain training job"""
    job_id: str
    project_name: str
    status: str
    config: AutoTrainConfig
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    output_path: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    logs: List[str] = field(default_factory=list)
    error_message: Optional[str] = None

class AutoTrainManager:
    """Main AutoTrain-Advanced integration manager for DuckBot"""

    def __init__(self, workspace_path: Optional[str] = None):
        self.workspace_path = workspace_path or Path(project_root) / "autotrain_workspace"
        self.workspace_path.mkdir(exist_ok=True)

        self.jobs: Dict[str, AutoTrainJob] = {}
        self.active_jobs: Dict[str, subprocess.Popen] = {}
        self.service_manager = UnifiedServiceManager() if UnifiedServiceManager else None
        self.monitoring_system = MonitoringSystem() if MonitoringSystem else None

        # Setup logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

        # Initialize AutoTrain
        if AUTOTRAIN_AVAILABLE:
            self.autotrain = autotrain
        else:
            self.autotrain = None

    def create_project_config(self, config: AutoTrainConfig) -> str:
        """Create AutoTrain project configuration file"""
        config_dir = self.workspace_path / config.project_name
        config_dir.mkdir(exist_ok=True)

        config_file = config_dir / "autotrain_config.yaml"

        # Create AutoTrain-compatible configuration
        autotrain_config = {
            "task": config.project_type.value,
            "base_model": config.model_name,
            "data_path": str(config.data_path),
            "project_name": config.project_name,

            # Training parameters
            "learning_rate": config.learning_rate,
            "num_epochs": config.num_epochs,
            "batch_size": config.batch_size,
            "max_length": config.max_length,
            "warmup_ratio": config.warmup_ratio,

            # Hardware configuration
            "device": "cuda" if config.use_gpu else "cpu",
            "fp16": config.mixed_precision,
            "gradient_accumulation_steps": config.gradient_accumulation,

            # Advanced options
            "use_peft": config.use_peft,
            "quantization": config.quantization,
            "gradient_checkpointing": config.gradient_checkpointing,

            # Logging
            "logging_steps": config.save_steps,
            "evaluation_strategy": "steps",
            "eval_steps": config.eval_steps,
            "save_strategy": "steps",
            "load_best_model_at_end": True,

            # Output
            "output_dir": str(config_dir / "output"),
        }

        # Add Hugging Face integration if enabled
        if config.push_to_hub and config.hf_repo_id:
            autotrain_config.update({
                "push_to_hub": True,
                "hub_model_id": config.hf_repo_id,
            })

        with open(config_file, 'w') as f:
            yaml.dump(autotrain_config, f, default_flow_style=False)

        return str(config_file)

    def submit_training_job(self, config: AutoTrainConfig) -> str:
        """Submit a new training job to AutoTrain"""
        if not AUTOTRAIN_AVAILABLE:
            raise RuntimeError("AutoTrain-Advanced not available. Install with: pip install autotrain-advanced")

        # Generate unique job ID
        job_id = f"{config.project_name}_{int(time.time())}"

        # Create configuration file
        config_file = self.create_project_config(config)

        # Create job record
        job = AutoTrainJob(
            job_id=job_id,
            project_name=config.project_name,
            status="submitted",
            config=config,
            created_at=datetime.now()
        )

        self.jobs[job_id] = job

        # Log job submission
        self.logger.info(f"Submitted AutoTrain job {job_id} for project {config.project_name}")

        # Start training in background
        asyncio.create_task(self._run_training_job(job_id, config_file))

        return job_id

    async def _run_training_job(self, job_id: str, config_file: str):
        """Run training job in background"""
        job = self.jobs.get(job_id)
        if not job:
            return

        try:
            job.status = "running"
            job.started_at = datetime.now()

            # Prepare command
            cmd = [
                "autotrain", "train",
                "--config", config_file,
                "--log-level", job.config.log_level
            ]

            # Set up environment variables
            env = os.environ.copy()
            if job.config.hf_token:
                env["HF_TOKEN"] = job.config.hf_token

            # Start subprocess
            process = subprocess.Popen(
                cmd,
                cwd=str(self.workspace_path),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )

            self.active_jobs[job_id] = process

            # Monitor process and capture output
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    job.logs.append(output.strip())
                    self.logger.info(f"[{job_id}] {output.strip()}")

                    # Parse metrics from output
                    self._parse_metrics_from_log(job, output.strip())

            # Process completion
            return_code = process.poll()
            if return_code == 0:
                job.status = "completed"
                job.completed_at = datetime.now()
                job.output_path = str(self.workspace_path / job.config.project_name / "output")
                self.logger.info(f"AutoTrain job {job_id} completed successfully")
            else:
                job.status = "failed"
                job.completed_at = datetime.now()
                job.error_message = f"Process failed with return code {return_code}"
                self.logger.error(f"AutoTrain job {job_id} failed with return code {return_code}")

        except Exception as e:
            job.status = "failed"
            job.completed_at = datetime.now()
            job.error_message = str(e)
            self.logger.error(f"AutoTrain job {job_id} failed with error: {e}")
        finally:
            if job_id in self.active_jobs:
                del self.active_jobs[job_id]

    def _parse_metrics_from_log(self, job: AutoTrainJob, log_line: str):
        """Parse training metrics from log output"""
        # Parse common metrics from AutoTrain output
        if "loss:" in log_line:
            try:
                parts = log_line.split()
                for i, part in enumerate(parts):
                    if part == "loss:" and i + 1 < len(parts):
                        job.metrics["loss"] = float(parts[i + 1])
                    elif part == "lr:" and i + 1 < len(parts):
                        job.metrics["learning_rate"] = float(parts[i + 1])
                    elif part == "epoch:" and i + 1 < len(parts):
                        job.metrics["epoch"] = float(parts[i + 1])
            except (ValueError, IndexError):
                pass

    def get_job_status(self, job_id: str) -> Optional[AutoTrainJob]:
        """Get status of a training job"""
        return self.jobs.get(job_id)

    def list_jobs(self, project_name: Optional[str] = None) -> List[AutoTrainJob]:
        """List all training jobs, optionally filtered by project"""
        jobs = list(self.jobs.values())
        if project_name:
            jobs = [job for job in jobs if job.project_name == project_name]
        return sorted(jobs, key=lambda x: x.created_at, reverse=True)

    def cancel_job(self, job_id: str) -> bool:
        """Cancel a running training job"""
        if job_id in self.active_jobs:
            process = self.active_jobs[job_id]
            process.terminate()
            try:
                process.wait(timeout=30)
            except subprocess.TimeoutExpired:
                process.kill()

            job = self.jobs.get(job_id)
            if job:
                job.status = "cancelled"
                job.completed_at = datetime.now()

            return True
        return False

    def get_job_logs(self, job_id: str) -> List[str]:
        """Get logs for a training job"""
        job = self.jobs.get(job_id)
        return job.logs if job else []

    def download_model(self, job_id: str, output_path: str) -> bool:
        """Download trained model from completed job"""
        job = self.jobs.get(job_id)
        if not job or job.status != "completed":
            return False

        try:
            source_path = job.output_path
            if source_path and os.path.exists(source_path):
                shutil.copytree(source_path, output_path)
                return True
        except Exception as e:
            self.logger.error(f"Failed to download model for job {job_id}: {e}")

        return False

    def create_project_template(self, project_type: AutoTrainProjectType) -> Dict[str, Any]:
        """Create a template configuration for a project type"""
        templates = {
            AutoTrainProjectType.LLM_FINE_TUNING: {
                "model_name": "microsoft/DialoGPT-medium",
                "learning_rate": 2e-5,
                "num_epochs": 3,
                "batch_size": 8,
                "use_peft": True,
                "quantization": False
            },
            AutoTrainProjectType.TEXT_CLASSIFICATION: {
                "model_name": "distilbert-base-uncased",
                "learning_rate": 2e-5,
                "num_epochs": 5,
                "batch_size": 16,
                "use_peft": False,
                "quantization": False
            },
            AutoTrainProjectType.SENTIMENT_ANALYSIS: {
                "model_name": "cardiffnlp/twitter-roberta-base-sentiment-latest",
                "learning_rate": 1e-5,
                "num_epochs": 3,
                "batch_size": 32,
                "use_peft": False,
                "quantization": False
            }
        }

        return templates.get(project_type, templates[AutoTrainProjectType.LLM_FINE_TUNING])

    def validate_config(self, config: AutoTrainConfig) -> List[str]:
        """Validate AutoTrain configuration"""
        errors = []

        # Check if data path exists
        if not os.path.exists(config.data_path):
            errors.append(f"Data path does not exist: {config.data_path}")

        # Check Hugging Face integration
        if config.push_to_hub and not config.hf_token:
            errors.append("HF token is required for push_to_hub")

        if config.push_to_hub and not config.hf_repo_id:
            errors.append("HF repo_id is required for push_to_hub")

        # Validate project-specific parameters
        if config.project_type == AutoTrainProjectType.LLM_FINE_TUNING:
            if config.max_length > 2048:
                errors.append("max_length too large for LLM fine-tuning (max 2048)")

        return errors

    def get_system_resources(self) -> Dict[str, Any]:
        """Get system resource information"""
        try:
            import psutil
            return {
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_usage": psutil.disk_usage(str(self.workspace_path)).percent,
                "gpu_available": self._is_gpu_available()
            }
        except ImportError:
            return {"error": "psutil not available"}

    def _is_gpu_available(self) -> bool:
        """Check if GPU is available"""
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False

    def cleanup_old_jobs(self, days_old: int = 7):
        """Clean up old job data"""
        cutoff_date = datetime.now() - timedelta(days=days_old)

        for job_id, job in list(self.jobs.items()):
            if job.created_at < cutoff_date and job.status in ["completed", "failed", "cancelled"]:
                # Remove job data
                project_path = self.workspace_path / job.config.project_name
                if project_path.exists():
                    shutil.rmtree(project_path)

                # Remove from active jobs
                del self.jobs[job_id]

                self.logger.info(f"Cleaned up old job {job_id}")

# DuckBot integration functions
def create_autotrain_service() -> ServiceInfo:
    """Create AutoTrain service info for DuckBot"""
    return ServiceInfo(
        name="autotrain_manager",
        service_type=ServiceType.AI_TRAINING,
        description="AutoTrain-Advanced integration for no-code ML training",
        version="1.0.0"
    )

async def start_autotrain_service():
    """Start AutoTrain service as part of DuckBot ecosystem"""
    if not UnifiedServiceManager:
        logging.error("DuckBot service manager not available")
        return

    service_manager = UnifiedServiceManager()
    autotrain_service = create_autotrain_service()

    # Initialize AutoTrain manager
    autotrain_manager = AutoTrainManager()

    # Register service
    await service_manager.register_service(autotrain_service)

    logging.info("AutoTrain service started successfully")

if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)

    # Create AutoTrain manager
    manager = AutoTrainManager()

    # Example configuration
    config = AutoTrainConfig(
        project_name="example_llm_finetuning",
        project_type=AutoTrainProjectType.LLM_FINE_TUNING,
        data_path="./example_data",
        model_name="microsoft/DialoGPT-medium",
        learning_rate=2e-5,
        num_epochs=3,
        batch_size=8
    )

    # Submit training job
    job_id = manager.submit_training_job(config)
    print(f"Submitted job: {job_id}")

    # Monitor job status
    while True:
        job = manager.get_job_status(job_id)
        if job:
            print(f"Job status: {job.status}")
            if job.status in ["completed", "failed", "cancelled"]:
                break
        time.sleep(10)