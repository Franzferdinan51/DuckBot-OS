#!/usr/bin/env python3
"""
Unified Training Orchestrator for DuckBot
Integrates LoRA, full fine-tuning, and parameter-efficient training methods
"""

import os
import sys
import json
import torch
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import time
import argparse
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import training modules
try:
    from advanced_lora_trainer import LoRATrainer, AdvancedLoRAConfig, LoRAConfig, LoRAMode, MemoryStrategy
    from full_finetune_trainer import MemoryEfficientTrainer, FullFineTuneConfig, MemoryConfig, PrecisionMode
    from parameter_efficient_training import ParameterEfficientModelWrapper, PEFTConfig, PEFTMethod
    from gradient_checkpointing_system import MemoryAwareTrainer, GradientCheckpointingConfig, CheckpointingStrategy
    from training_config_templates import TrainingTemplateManager, ModelSize, HardwareProfile, TrainingObjective
    from model_trainer import ModelTrainer, GGUFTrainingConfig, QuantizationType
    HAS_TRAINING_MODULES = True
except ImportError as e:
    logging.error(f"Training modules not available: {e}")
    HAS_TRAINING_MODULES = False

class TrainingMethod(Enum):
    """Available training methods"""
    LORA = "lora"
    FULL_FINETUNE = "full_finetune"
    QLORA = "qlora"
    DORA = "dora"
    ADAPTER = "adapter"
    IA3 = "ia3"
    HYBRID = "hybrid"
    GRADIENT_CHECKPOINTING = "gradient_checkpointing"

class OrchestratorMode(Enum):
    """Orchestrator operation modes"""
    AUTO = "auto"                      # Automatic optimization
    MANUAL = "manual"                  # Manual configuration
    TEMPLATE = "template"               # Use predefined template
    ANALYSIS = "analysis"               # Analysis only

@dataclass
class TrainingJob:
    """Training job configuration"""
    job_id: str
    model_path: str
    dataset_path: str
    output_dir: str
    method: TrainingMethod
    config: Dict[str, Any]
    priority: int = 1
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    status: str = "pending"
    progress: float = 0.0
    metrics: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SystemResources:
    """System resource information"""
    gpu_memory_gb: List[float] = field(default_factory=list)
    cpu_memory_gb: float = 0.0
    gpu_count: int = 0
    cuda_available: bool = False
    gpu_names: List[str] = field(default_factory=list)

class UnifiedTrainingOrchestrator:
    """Unified training orchestrator for DuckBot"""

    def __init__(self, mode: OrchestratorMode = OrchestratorMode.AUTO):
        self.mode = mode
        self.logger = self._setup_logger()
        self.template_manager = TrainingTemplateManager() if HAS_TRAINING_MODULES else None
        self.training_jobs: Dict[str, TrainingJob] = {}
        self.active_trainers: Dict[str, Any] = {}
        self.system_resources = self._analyze_system_resources()

        if not HAS_TRAINING_MODULES:
            self.logger.error("Training modules not available. Please install required dependencies.")

    def _setup_logger(self) -> logging.Logger:
        """Setup logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)

    def _analyze_system_resources(self) -> SystemResources:
        """Analyze available system resources"""
        resources = SystemResources()

        # GPU resources
        if torch.cuda.is_available():
            resources.cuda_available = True
            resources.gpu_count = torch.cuda.device_count()
            resources.gpu_memory_gb = []
            resources.gpu_names = []

            for i in range(resources.gpu_count):
                props = torch.cuda.get_device_properties(i)
                resources.gpu_memory_gb.append(props.total_memory / (1024**3))  # GB
                resources.gpu_names.append(props.name)

        # CPU memory
        import psutil
        memory = psutil.virtual_memory()
        resources.cpu_memory_gb = memory.total / (1024**3)  # GB

        self.logger.info(f"System resources: {resources.gpu_count} GPUs, {resources.cpu_memory_gb:.1f}GB RAM")
        for i, gpu_memory in enumerate(resources.gpu_memory_gb):
            self.logger.info(f"  GPU {i}: {gpu_memory:.1f}GB ({resources.gpu_names[i]})")

        return resources

    def create_training_job(
        self,
        model_path: str,
        dataset_path: str,
        output_dir: str,
        method: TrainingMethod,
        config: Optional[Dict[str, Any]] = None,
        template_name: Optional[str] = None
    ) -> str:
        """Create a new training job"""
        job_id = f"training_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # If template specified, use template configuration
        if template_name and self.template_manager:
            template = self.template_manager.get_template(template_name)
            if template:
                config = template.get("config", {})
                self.logger.info(f"Using template '{template_name}' for job {job_id}")
            else:
                self.logger.warning(f"Template '{template_name}' not found, using provided config")

        # Validate configuration
        config = config or {}
        validated_config = self._validate_config(method, config)

        # Create job
        job = TrainingJob(
            job_id=job_id,
            model_path=model_path,
            dataset_path=dataset_path,
            output_dir=output_dir,
            method=method,
            config=validated_config
        )

        self.training_jobs[job_id] = job
        self.logger.info(f"Created training job {job_id} with method {method.value}")

        return job_id

    def _validate_config(self, method: TrainingMethod, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and complete configuration"""
        validated_config = config.copy()

        # Ensure required fields are present
        required_fields = {
            TrainingMethod.LORA: ["learning_rate", "num_train_epochs", "per_device_train_batch_size"],
            TrainingMethod.FULL_FINETUNE: ["learning_rate", "num_train_epochs", "per_device_train_batch_size"],
            TrainingMethod.QLORA: ["learning_rate", "num_train_epochs", "per_device_train_batch_size"],
            TrainingMethod.DORA: ["learning_rate", "num_train_epochs", "per_device_train_batch_size"],
        }

        # Set defaults based on method
        if method in [TrainingMethod.LORA, TrainingMethod.QLORA, TrainingMethod.DORA]:
            defaults = {
                "learning_rate": 2e-4,
                "num_train_epochs": 3,
                "per_device_train_batch_size": 4,
                "gradient_accumulation_steps": 4,
                "lora_r": 16,
                "lora_alpha": 32,
                "lora_dropout": 0.1,
                "memory_strategy": "balanced",
                "gradient_checkpointing": True
            }
        elif method == TrainingMethod.FULL_FINETUNE:
            defaults = {
                "learning_rate": 2e-5,
                "num_train_epochs": 3,
                "per_device_train_batch_size": 2,
                "gradient_accumulation_steps": 8,
                "memory_mode": "gradient_checkpointing",
                "precision": "fp16"
            }
        else:
            defaults = {}

        # Apply defaults
        for key, value in defaults.items():
            if key not in validated_config:
                validated_config[key] = value

        # Validate paths
        if not Path(config.get("model_path", "")).exists():
            raise ValueError(f"Model path not found: {config.get('model_path', '')}")

        if not Path(config.get("dataset_path", "")).exists():
            raise ValueError(f"Dataset path not found: {config.get('dataset_path', '')}")

        return validated_config

    def start_training_job(self, job_id: str) -> bool:
        """Start a training job"""
        if job_id not in self.training_jobs:
            self.logger.error(f"Training job {job_id} not found")
            return False

        job = self.training_jobs[job_id]
        if job.status != "pending":
            self.logger.warning(f"Job {job_id} is not in pending state (current: {job.status})")
            return False

        # Check system resources
        if not self._check_resources(job):
            self.logger.error(f"Insufficient resources for job {job_id}")
            return False

        # Start training
        try:
            self.logger.info(f"Starting training job {job_id}")
            job.status = "running"

            if job.method in [TrainingMethod.LORA, TrainingMethod.QLORA, TrainingMethod.DORA]:
                trainer = self._start_lora_training(job)
            elif job.method == TrainingMethod.FULL_FINETUNE:
                trainer = self._start_full_finetune_training(job)
            else:
                raise ValueError(f"Training method {job.method} not implemented")

            self.active_trainers[job_id] = trainer
            return True

        except Exception as e:
            self.logger.error(f"Failed to start training job {job_id}: {e}")
            job.status = "failed"
            return False

    def _check_resources(self, job: TrainingJob) -> bool:
        """Check if system has sufficient resources for the job"""
        # Simple resource check
        if not self.system_resources.cuda_available:
            self.logger.warning("CUDA not available, training will be slow")
            return True  # Allow CPU training

        # Check GPU memory requirements
        required_memory = job.config.get("min_vram_gb", 8.0)
        available_memory = max(self.system_resources.gpu_memory_gb) if self.system_resources.gpu_memory_gb else 0

        if available_memory < required_memory:
            self.logger.error(f"Insufficient GPU memory: required {required_memory}GB, available {available_memory}GB")
            return False

        return True

    def _start_lora_training(self, job: TrainingJob):
        """Start LoRA training"""
        config_dict = job.config

        # Create LoRA config
        lora_config = LoRAConfig(
            r=config_dict.get("lora_r", 16),
            lora_alpha=config_dict.get("lora_alpha", 32),
            lora_dropout=config_dict.get("lora_dropout", 0.1),
            target_modules=config_dict.get("target_modules", ["q_proj", "v_proj", "k_proj", "o_proj"])
        )

        # Create training config
        training_config = AdvancedLoRAConfig(
            model_name_or_path=job.model_path,
            dataset_path=job.dataset_path,
            output_dir=job.output_dir,
            lora_config=lora_config,
            lora_mode=self._get_lora_mode(job.method),
            learning_rate=config_dict.get("learning_rate", 2e-4),
            num_train_epochs=config_dict.get("num_train_epochs", 3),
            per_device_train_batch_size=config_dict.get("per_device_train_batch_size", 4),
            gradient_accumulation_steps=config_dict.get("gradient_accumulation_steps", 4),
            memory_strategy=MemoryStrategy(config_dict.get("memory_strategy", "balanced")),
            gradient_checkpointing=config_dict.get("gradient_checkpointing", True),
        )

        # Create and start trainer
        trainer = LoRATrainer(training_config)
        return trainer

    def _get_lora_mode(self, method: TrainingMethod) -> LoRAMode:
        """Convert training method to LoRA mode"""
        mode_mapping = {
            TrainingMethod.LORA: LoRAMode.STANDARD,
            TrainingMethod.QLORA: LoRAMode.QLoRA,
            TrainingMethod.DORA: LoRAMode.DORA,
        }
        return mode_mapping.get(method, LoRAMode.STANDARD)

    def _start_full_finetune_training(self, job: TrainingJob):
        """Start full fine-tuning training"""
        config_dict = job.config

        # Create memory config
        memory_config = MemoryConfig(
            mode=MemoryMode(config_dict.get("memory_mode", "gradient_checkpointing")),
            precision=PrecisionMode(config_dict.get("precision", "fp16")),
            enable_gradient_accumulation=True,
            enable_activation_checkpointing=True,
            enable_mixed_precision=True
        )

        # Create training config
        training_config = FullFineTuneConfig(
            model_name_or_path=job.model_path,
            dataset_path=job.dataset_path,
            output_dir=job.output_dir,
            memory_config=memory_config,
            learning_rate=config_dict.get("learning_rate", 2e-5),
            num_train_epochs=config_dict.get("num_train_epochs", 3),
            per_device_train_batch_size=config_dict.get("per_device_train_batch_size", 2),
            gradient_accumulation_steps=config_dict.get("gradient_accumulation_steps", 8),
            max_seq_length=config_dict.get("max_seq_length", 2048),
            fp16=config_dict.get("precision") == "fp16",
            bf16=config_dict.get("precision") == "bf16"
        )

        # Create and start trainer
        trainer = MemoryEfficientTrainer(training_config)
        return trainer

    def stop_training_job(self, job_id: str) -> bool:
        """Stop a training job"""
        if job_id not in self.training_jobs:
            self.logger.error(f"Training job {job_id} not found")
            return False

        job = self.training_jobs[job_id]
        if job.status != "running":
            self.logger.warning(f"Job {job_id} is not running (current: {job.status})")
            return False

        # Stop trainer
        if job_id in self.active_trainers:
            trainer = self.active_trainers[job_id]
            if hasattr(trainer, 'stop'):
                trainer.stop()
            del self.active_trainers[job_id]

        job.status = "stopped"
        self.logger.info(f"Stopped training job {job_id}")
        return True

    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a training job"""
        if job_id not in self.training_jobs:
            return None

        job = self.training_jobs[job_id]
        return {
            "job_id": job_id,
            "status": job.status,
            "progress": job.progress,
            "metrics": job.metrics,
            "created_at": job.created_at,
            "method": job.method.value,
            "model_path": job.model_path,
            "output_dir": job.output_dir
        }

    def list_jobs(self) -> List[Dict[str, Any]]:
        """List all training jobs"""
        return [self.get_job_status(job_id) for job_id in self.training_jobs.keys()]

    def recommend_configuration(
        self,
        model_path: str,
        hardware_profile: HardwareProfile,
        training_objective: TrainingObjective
    ) -> Dict[str, Any]:
        """Recommend training configuration based on model and hardware"""
        if not self.template_manager:
            return {"error": "Template manager not available"}

        # Estimate model size based on path
        model_size = self._estimate_model_size(model_path)

        # Get template recommendation
        template_name = self.template_manager.recommend_template(
            model_size, hardware_profile, training_objective
        )

        template = self.template_manager.get_template(template_name)
        if not template:
            return {"error": f"No suitable template found for {model_size.value} + {hardware_profile.value}"}

        return {
            "recommended_template": template_name,
            "template_description": template.get("description", ""),
            "configuration": template.get("config", {}),
            "requirements": template.get("requirements", {}),
            "estimated_training_time": self._estimate_training_time(model_size, hardware_profile)
        }

    def _estimate_model_size(self, model_path: str) -> ModelSize:
        """Estimate model size from path or file size"""
        model_path_lower = model_path.lower()

        if "7b" in model_path_lower:
            return ModelSize.MEDIUM
        elif "13b" in model_path_lower:
            return ModelSize.LARGE
        elif "30b" in model_path_lower:
            return ModelSize.XLARGE
        elif "70b" in model_path_lower:
            return ModelSize.XXLARGE
        elif any(size in model_path_lower for size in ["2b", "3b", "1b"]):
            return ModelSize.SMALL
        else:
            # Default to medium size
            return ModelSize.MEDIUM

    def _estimate_training_time(self, model_size: ModelSize, hardware_profile: HardwareProfile) -> str:
        """Estimate training time based on model size and hardware"""
        base_times = {
            ModelSize.SMALL: 2,      # hours
            ModelSize.MEDIUM: 8,     # hours
            ModelSize.LARGE: 24,     # hours
            ModelSize.XLARGE: 72,    # hours
            ModelSize.XXLARGE: 168,  # hours
        }

        hardware_multipliers = {
            HardwareProfile.LOW_END: 2.0,
            HardwareProfile.MID_RANGE: 1.0,
            HardwareProfile.HIGH_END: 0.5,
            HardwareProfile.MULTI_GPU: 0.25,
            HardwareProfile.CPU_ONLY: 4.0,
        }

        base_time = base_times.get(model_size, 8)
        multiplier = hardware_multipliers.get(hardware_profile, 1.0)

        estimated_hours = base_time * multiplier

        if estimated_hours < 1:
            return f"{int(estimated_hours * 60)} minutes"
        elif estimated_hours < 24:
            return f"{int(estimated_hours)} hours"
        else:
            days = int(estimated_hours // 24)
            hours = int(estimated_hours % 24)
            return f"{days} days, {hours} hours"

    def get_system_info(self) -> Dict[str, Any]:
        """Get system information"""
        return {
            "gpu_count": self.system_resources.gpu_count,
            "gpu_memory_gb": self.system_resources.gpu_memory_gb,
            "gpu_names": self.system_resources.gpu_names,
            "cpu_memory_gb": self.system_resources.cpu_memory_gb,
            "cuda_available": self.system_resources.cuda_available,
            "active_jobs": len(self.active_trainers),
            "pending_jobs": len([j for j in self.training_jobs.values() if j.status == "pending"]),
            "completed_jobs": len([j for j in self.training_jobs.values() if j.status == "completed"])
        }

    def save_job_config(self, job_id: str, output_path: str):
        """Save job configuration to file"""
        if job_id not in self.training_jobs:
            raise ValueError(f"Job {job_id} not found")

        job = self.training_jobs[job_id]
        job_config = {
            "job_id": job_id,
            "model_path": job.model_path,
            "dataset_path": job.dataset_path,
            "output_dir": job.output_dir,
            "method": job.method.value,
            "config": job.config,
            "created_at": job.created_at,
            "system_info": self.get_system_info()
        }

        with open(output_path, 'w') as f:
            json.dump(job_config, f, indent=2, default=str)

        self.logger.info(f"Job configuration saved to {output_path}")

    def load_job_config(self, config_path: str) -> str:
        """Load job configuration from file and create job"""
        with open(config_path, 'r') as f:
            job_config = json.load(f)

        job_id = self.create_training_job(
            model_path=job_config["model_path"],
            dataset_path=job_config["dataset_path"],
            output_dir=job_config["output_dir"],
            method=TrainingMethod(job_config["method"]),
            config=job_config["config"]
        )

        self.logger.info(f"Loaded job configuration from {config_path}")
        return job_id

    def cleanup_completed_jobs(self, max_age_hours: int = 24):
        """Clean up completed jobs older than specified age"""
        current_time = datetime.now()
        cutoff_time = current_time.timestamp() - (max_age_hours * 3600)

        jobs_to_remove = []
        for job_id, job in self.training_jobs.items():
            if job.status in ["completed", "failed", "stopped"]:
                job_time = datetime.fromisoformat(job.created_at)
                if job_time.timestamp() < cutoff_time:
                    jobs_to_remove.append(job_id)

        for job_id in jobs_to_remove:
            del self.training_jobs[job_id]
            self.logger.info(f"Cleaned up job {job_id}")

def main():
    """Main entry point for the unified training orchestrator"""
    parser = argparse.ArgumentParser(description="DuckBot Unified Training Orchestrator")
    parser.add_argument("--mode", choices=["auto", "manual", "template", "analysis"], default="auto", help="Operation mode")
    parser.add_argument("--model", type=str, help="Model path")
    parser.add_argument("--dataset", type=str, help="Dataset path")
    parser.add_argument("--output", type=str, help="Output directory")
    parser.add_argument("--method", choices=["lora", "qlora", "dora", "full_finetune", "adapter"], help="Training method")
    parser.add_argument("--template", type=str, help="Use predefined template")
    parser.add_argument("--config", type=str, help="Configuration file path")
    parser.add_argument("--hardware", choices=["low_end", "mid_range", "high_end", "multi_gpu", "cpu_only"], help="Hardware profile")
    parser.add_argument("--objective", choices=["instruction_tuning", "domain_adaptation", "continued_pretraining", "chat_finetuning", "code_finetuning"], help="Training objective")
    parser.add_argument("--recommend", action="store_true", help="Get configuration recommendation")
    parser.add_argument("--save-config", type=str, help="Save configuration to file")
    parser.add_argument("--list-templates", action="store_true", help="List available templates")
    parser.add_argument("--system-info", action="store_true", help="Show system information")
    parser.add_argument("--interactive", action="store_true", help="Start interactive mode")

    args = parser.parse_args()

    # Initialize orchestrator
    orchestrator = UnifiedTrainingOrchestrator(OrchestratorMode(args.mode))

    if args.system_info:
        info = orchestrator.get_system_info()
        print("System Information:")
        print(f"  GPU Count: {info['gpu_count']}")
        print(f"  GPU Memory: {info['gpu_memory_gb']} GB per GPU")
        print(f"  CPU Memory: {info['cpu_memory_gb']:.1f} GB")
        print(f"  CUDA Available: {info['cuda_available']}")
        print(f"  Active Jobs: {info['active_jobs']}")
        return

    if args.list_templates and orchestrator.template_manager:
        print("Available Templates:")
        for template_name in orchestrator.template_manager.list_templates():
            template = orchestrator.template_manager.get_template(template_name)
            print(f"  - {template_name}: {template.get('description', 'No description')}")
        return

    if args.recommend:
        if not all([args.model, args.hardware, args.objective]):
            print("Error: --model, --hardware, and --objective are required for recommendation")
            return

        recommendation = orchestrator.recommend_configuration(
            args.model,
            HardwareProfile(args.hardware),
            TrainingObjective(args.objective)
        )

        print("Configuration Recommendation:")
        print(f"  Template: {recommendation.get('recommended_template', 'Unknown')}")
        print(f"  Description: {recommendation.get('template_description', 'No description')}")
        print(f"  Estimated Training Time: {recommendation.get('estimated_training_time', 'Unknown')}")
        return

    if args.interactive:
        print("Interactive Mode - Type 'help' for available commands")
        interactive_orchestrator(orchestrator)
        return

    # Create training job
    if not all([args.model, args.dataset, args.output, args.method]):
        print("Error: --model, --dataset, --output, and --method are required")
        parser.print_help()
        return

    try:
        job_id = orchestrator.create_training_job(
            model_path=args.model,
            dataset_path=args.dataset,
            output_dir=args.output,
            method=TrainingMethod(args.method),
            template_name=args.template
        )

        if args.config:
            # Load custom configuration
            with open(args.config, 'r') as f:
                custom_config = json.load(f)
            orchestrator.training_jobs[job_id].config.update(custom_config)

        if args.save_config:
            orchestrator.save_job_config(job_id, args.save_config)

        # Start training
        if orchestrator.start_training_job(job_id):
            print(f"Training job {job_id} started successfully")
        else:
            print(f"Failed to start training job {job_id}")

    except Exception as e:
        print(f"Error: {e}")
        return

def interactive_orchestrator(orchestrator: UnifiedTrainingOrchestrator):
    """Interactive mode for the orchestrator"""
    import cmd

    class InteractiveOrchestrator(cmd.Cmd):
        prompt = "orchestrator> "

        def __init__(self, orchestrator_ref):
            super().__init__()
            self.orchestrator = orchestrator_ref

        def do_create(self, arg):
            """Create a new training job: create <model> <dataset> <output> <method>"""
            args = arg.split()
            if len(args) < 4:
                print("Usage: create <model> <dataset> <output> <method>")
                return

            try:
                job_id = self.orchestrator.create_training_job(
                    model_path=args[0],
                    dataset_path=args[1],
                    output_dir=args[2],
                    method=TrainingMethod(args[3])
                )
                print(f"Created job {job_id}")
            except Exception as e:
                print(f"Error: {e}")

        def do_start(self, arg):
            """Start a training job: start <job_id>"""
            if not arg:
                print("Usage: start <job_id>")
                return

            if self.orchestrator.start_training_job(arg):
                print(f"Started job {arg}")
            else:
                print(f"Failed to start job {arg}")

        def do_stop(self, arg):
            """Stop a training job: stop <job_id>"""
            if not arg:
                print("Usage: stop <job_id>")
                return

            if self.orchestrator.stop_training_job(arg):
                print(f"Stopped job {arg}")
            else:
                print(f"Failed to stop job {arg}")

        def do_status(self, arg):
            """Check job status: status [job_id]"""
            if arg:
                status = self.orchestrator.get_job_status(arg)
                if status:
                    print(f"Job {arg}: {status}")
                else:
                    print(f"Job {arg} not found")
            else:
                jobs = self.orchestrator.list_jobs()
                for job in jobs:
                    print(f"{job['job_id']}: {job['status']} ({job['method']})")

        def do_list(self, arg):
            """List all training jobs"""
            jobs = self.orchestrator.list_jobs()
            for job in jobs:
                print(f"{job['job_id']}: {job['status']} ({job['method']})")

        def do_system(self, arg):
            """Show system information"""
            info = self.orchestrator.get_system_info()
            print("System Information:")
            for key, value in info.items():
                print(f"  {key}: {value}")

        def do_templates(self, arg):
            """List available templates"""
            if self.orchestrator.template_manager:
                templates = self.orchestrator.template_manager.list_templates()
                for template in templates:
                    print(f"  - {template}")
            else:
                print("Template manager not available")

        def do_recommend(self, arg):
            """Get configuration recommendation: recommend <model> <hardware> <objective>"""
            args = arg.split()
            if len(args) < 3:
                print("Usage: recommend <model> <hardware> <objective>")
                return

            try:
                recommendation = self.orchestrator.recommend_configuration(
                    args[0], HardwareProfile(args[1]), TrainingObjective(args[2])
                )
                print("Recommendation:")
                for key, value in recommendation.items():
                    print(f"  {key}: {value}")
            except Exception as e:
                print(f"Error: {e}")

        def do_exit(self, arg):
            """Exit interactive mode"""
            return True

        def do_quit(self, arg):
            """Exit interactive mode"""
            return True

        def do_help(self, arg):
            """Show help"""
            print("Available commands:")
            print("  create <model> <dataset> <output> <method> - Create training job")
            print("  start <job_id> - Start training job")
            print("  stop <job_id> - Stop training job")
            print("  status [job_id] - Check job status")
            print("  list - List all jobs")
            print("  system - Show system information")
            print("  templates - List available templates")
            print("  recommend <model> <hardware> <objective> - Get recommendation")
            print("  exit/quit - Exit interactive mode")

    InteractiveOrchestrator(orchestrator).cmdloop()

if __name__ == "__main__":
    main()