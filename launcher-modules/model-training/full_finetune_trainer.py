#!/usr/bin/env python3
"""
Full Fine-Tuning Trainer with Advanced Memory Optimization
Implements comprehensive full fine-tuning with memory-efficient techniques,
gradient checkpointing, and advanced optimization strategies
"""

import os
import sys
import json
import torch
import logging
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import time
import gc
from collections import defaultdict
import math
import psutil
import pynvml

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    import transformers
    from transformers import (
        AutoTokenizer, AutoModelForCausalLM, TrainingArguments, Trainer,
        DataCollatorForLanguageModeling, BitsAndBytesConfig, TrainerCallback,
        PreTrainedModel, PreTrainedTokenizer, get_linear_schedule_with_warmup
    )
    from transformers.trainer_utils import get_last_checkpoint
    from datasets import Dataset, DatasetDict, load_dataset
    from torch.optim import AdamW, SGD, Adam, RMSprop, Lion
    from torch.optim.lr_scheduler import _LRScheduler, OneCycleLR, CosineAnnealingWarmRestarts
    from torch.utils.data import DataLoader, Dataset as TorchDataset
    import torch.nn as nn
    import torch.nn.functional as F
    from torch.cuda.amp import GradScaler, autocast
    from accelerate import Accelerator
    from accelerate.utils import DistributedDataParallelKwargs, find_executable_batch_size
    from deepspeed import DeepSpeedEngine, DeepSpeedConfig
    import wandb
    HAS_DEPS = True
except ImportError as e:
    logging.warning(f"Required dependencies not installed: {e}")
    HAS_DEPS = False

class MemoryMode(Enum):
    """Memory optimization modes"""
    STANDARD = "standard"
    GRADIENT_CHECKPOINTING = "gradient_checkpointing"
    CPU_OFFLOADING = "cpu_offloading"
    ACTIVATION_CHECKPOINTING = "activation_checkpointing"
    HYBRID = "hybrid"

class PrecisionMode(Enum):
    """Precision modes for training"""
    FP32 = "fp32"
    FP16 = "fp16"
    BF16 = "bf16"
    MIXED = "mixed"

class OffloadingStrategy(Enum):
    """Offloading strategies for memory optimization"""
    NONE = "none"
    CPU = "cpu"
    DISK = "disk"
    HYBRID = "hybrid"

@dataclass
class MemoryConfig:
    """Memory optimization configuration"""
    mode: MemoryMode = MemoryMode.HYBRID
    precision: PrecisionMode = PrecisionMode.FP16
    offloading: OffloadingStrategy = OffloadingStrategy.HYBRID
    max_memory_per_gpu: Optional[float] = None  # GB
    max_cpu_memory: Optional[float] = None  # GB
    disk_offload_path: Optional[str] = None
    enable_gradient_accumulation: bool = True
    enable_activation_checkpointing: bool = True
    enable_mixed_precision: bool = True
    enable_cpu_offload: bool = True
    enable_disk_offload: bool = False
    enable_memory_efficient_attention: bool = True
    enable_flash_attention: bool = True
    enable_torch_compile: bool = True

@dataclass
class DistributedConfig:
    """Distributed training configuration"""
    backend: str = "nccl"
    find_unused_parameters: bool = False
    gradient_as_bucket_view: bool = True
    static_graph: bool = False
    num_nodes: int = 1
    num_gpus_per_node: int = 1

@dataclass
class FullFineTuneConfig:
    """Complete full fine-tuning configuration"""
    # Model and data
    model_name_or_path: str
    dataset_path: str
    output_dir: str

    # Memory optimization
    memory_config: MemoryConfig = field(default_factory=MemoryConfig)
    distributed_config: DistributedConfig = field(default_factory=DistributedConfig)

    # Training parameters
    learning_rate: float = 2e-5
    weight_decay: float = 0.01
    num_train_epochs: int = 3
    per_device_train_batch_size: int = 1
    per_device_eval_batch_size: int = 1
    gradient_accumulation_steps: int = 32
    warmup_steps: int = 1000
    logging_steps: int = 50
    save_steps: int = 1000
    eval_steps: int = 1000
    save_total_limit: int = 3
    max_grad_norm: float = 1.0

    # Dataset
    max_seq_length: int = 2048
    mlm_probability: float = 0.15  # For masked language modeling
    preprocessing_num_workers: int = 4

    # Evaluation
    do_eval: bool = True
    evaluation_strategy: str = "steps"
    metric_for_best_model: str = "eval_loss"
    greater_is_better: bool = False

    # Optimization
    optimizer: str = "adamw"
    scheduler: str = "cosine"
    beta1: float = 0.9
    beta2: float = 0.999
    eps: float = 1e-8

    # Mixed precision
    fp16: bool = True
    fp16_opt_level: str = "O1"
    bf16: bool = False
    tf32: bool = False

    # Logging and saving
    logging_dir: Optional[str] = None
    report_to: str = "none"
    run_name: Optional[str] = None

class MemoryMonitor:
    """Memory monitoring utilities"""

    def __init__(self):
        self.has_gpu = torch.cuda.is_available()
        if self.has_gpu:
            pynvml.nvmlInit()
            self.gpu_count = pynvml.nvmlDeviceGetCount()
            self.gpu_handles = [pynvml.nvmlDeviceGetHandleByIndex(i) for i in range(self.gpu_count)]

    def get_memory_info(self) -> Dict[str, Any]:
        """Get current memory usage"""
        memory_info = {}

        # CPU memory
        memory_info["cpu"] = {
            "total": psutil.virtual_memory().total / (1024**3),  # GB
            "used": psutil.virtual_memory().used / (1024**3),
            "available": psutil.virtual_memory().available / (1024**3),
            "percent": psutil.virtual_memory().percent
        }

        # GPU memory
        if self.has_gpu:
            gpu_memory = []
            for i, handle in enumerate(self.gpu_handles):
                info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                gpu_memory.append({
                    "gpu_id": i,
                    "total": info.total / (1024**3),
                    "used": info.used / (1024**3),
                    "free": info.free / (1024**3)
                })
            memory_info["gpu"] = gpu_memory

        return memory_info

    def get_optimal_batch_size(self, model, max_memory_usage: float = 0.8) -> int:
        """Calculate optimal batch size based on available memory"""
        if not self.has_gpu:
            return 1

        memory_info = self.get_memory_info()
        if not memory_info["gpu"]:
            return 1

        # Estimate model memory usage (rough approximation)
        model_size = sum(p.numel() * p.element_size() for p in model.parameters()) / (1024**3)

        # Calculate available memory
        available_memory = memory_info["gpu"][0]["total"] * max_memory_usage

        # Account for model, activations, and gradients
        activation_memory_per_sample = 4 * (model_size / 1e9)  # Rough estimate
        gradient_memory = model_size * 2  # Gradients and optimizer states

        # Calculate maximum batch size
        memory_for_batch = available_memory - model_size - gradient_memory
        max_batch_size = int(memory_for_batch / activation_memory_per_sample)

        return max(1, min(max_batch_size, 32))  # Clamp between 1 and 32

class CustomDataset(TorchDataset):
    """Custom dataset with memory-efficient loading"""

    def __init__(self, data, tokenizer, max_length: int = 2048):
        self.data = data
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        item = self.data[idx]

        # Format text based on dataset structure
        if isinstance(item, dict):
            if "text" in item:
                text = item["text"]
            elif "instruction" in item and "response" in item:
                text = f"Instruction: {item['instruction']}\n\nResponse: {item['response']}"
            elif "prompt" in item and "completion" in item:
                text = f"Question: {item['prompt']}\n\nAnswer: {item['completion']}"
            else:
                text = str(item)
        else:
            text = str(item)

        # Tokenize
        encoded = self.tokenizer(
            text,
            truncation=True,
            padding="max_length",
            max_length=self.max_length,
            return_tensors="pt"
        )

        return {
            "input_ids": encoded["input_ids"].squeeze(),
            "attention_mask": encoded["attention_mask"].squeeze(),
            "labels": encoded["input_ids"].squeeze()
        }

class CustomOptimizer:
    """Custom optimizer with memory-efficient implementations"""

    def __init__(self, model, config: FullFineTuneConfig):
        self.model = model
        self.config = config

    def create_optimizer(self):
        """Create optimizer with memory-efficient configuration"""
        # Separate parameters with and without weight decay
        no_decay = ["bias", "LayerNorm.weight", "layer_norm.weight", "norm.weight"]
        optimizer_grouped_parameters = [
            {
                "params": [p for n, p in self.model.named_parameters() if not any(nd in n for nd in no_decay)],
                "weight_decay": self.config.weight_decay,
            },
            {
                "params": [p for n, p in self.model.named_parameters() if any(nd in n for nd in no_decay)],
                "weight_decay": 0.0,
            },
        ]

        if self.config.optimizer == "adamw":
            return AdamW(optimizer_grouped_parameters, lr=self.config.learning_rate)
        elif self.config.optimizer == "adam":
            return Adam(optimizer_grouped_parameters, lr=self.config.learning_rate)
        elif self.config.optimizer == "sgd":
            return SGD(optimizer_grouped_parameters, lr=self.config.learning_rate)
        else:
            raise ValueError(f"Unknown optimizer: {self.config.optimizer}")

class CustomScheduler:
    """Custom learning rate scheduler"""

    def __init__(self, optimizer, config: FullFineTuneConfig, num_training_steps: int):
        self.optimizer = optimizer
        self.config = config
        self.num_training_steps = num_training_steps

    def create_scheduler(self):
        """Create learning rate scheduler"""
        if self.config.scheduler == "cosine":
            return lr_scheduler.CosineAnnealingLR(
                self.optimizer,
                T_max=self.num_training_steps - self.config.warmup_steps
            )
        elif self.config.scheduler == "linear":
            return lr_scheduler.LinearLR(
                self.optimizer,
                start_factor=0.1,
                end_factor=1.0,
                total_iters=self.config.warmup_steps
            )
        elif self.config.scheduler == "cosine_with_restarts":
            return lr_scheduler.CosineAnnealingWarmRestarts(
                self.optimizer,
                T_0=1000,
                T_mult=2
            )
        else:
            return lr_scheduler.ConstantLR(self.optimizer, factor=1.0)

class MemoryEfficientTrainer:
    """Memory-efficient full fine-tuning trainer"""

    def __init__(self, config: FullFineTuneConfig):
        self.config = config
        self.model = None
        self.tokenizer = None
        self.optimizer = None
        self.scheduler = None
        self.accelerator = None
        self.memory_monitor = MemoryMonitor()
        self.scaler = None
        self.setup_logging()

        if not HAS_DEPS:
            raise ImportError("Required dependencies not installed")

    def setup_logging(self):
        """Setup logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def setup_accelerator(self):
        """Setup accelerator for distributed training"""
        kwargs = DistributedDataParallelKwargs(
            find_unused_parameters=self.config.distributed_config.find_unused_parameters
        )

        self.accelerator = Accelerator(
            mixed_precision=self.config.memory_config.precision.value,
            gradient_accumulation_steps=self.config.gradient_accumulation_steps,
            cpu_offload=self.config.memory_config.cpu_offload,
            kwargs_handlers=[kwargs],
        )

    def load_model_and_tokenizer(self):
        """Load model and tokenizer with memory optimization"""
        self.logger.info(f"Loading model: {self.config.model_name_or_path}")

        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.config.model_name_or_path,
            trust_remote_code=True
        )

        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        # Load model with memory optimization
        model_kwargs = {
            "trust_remote_code": True,
            "device_map": "auto",
        }

        # Setup quantization if needed
        if self.config.memory_config.precision == PrecisionMode.FP16:
            model_kwargs["torch_dtype"] = torch.float16
        elif self.config.memory_config.precision == PrecisionMode.BF16:
            model_kwargs["torch_dtype"] = torch.bfloat16

        # Load model
        self.model = AutoModelForCausalLM.from_pretrained(
            self.config.model_name_or_path,
            **model_kwargs
        )

        # Apply memory optimizations
        self._apply_memory_optimizations()

        self.logger.info(f"Model loaded: {self.model.__class__.__name__}")

    def _apply_memory_optimizations(self):
        """Apply various memory optimization techniques"""
        if self.config.memory_config.mode == MemoryMode.GRADIENT_CHECKPOINTING:
            self.model.gradient_checkpointing_enable()

        if self.config.memory_config.enable_activation_checkpointing:
            self._setup_activation_checkpointing()

        if self.config.memory_config.enable_torch_compile:
            try:
                self.model = torch.compile(self.model)
                self.logger.info("Model compiled with torch.compile")
            except Exception as e:
                self.logger.warning(f"Failed to compile model: {e}")

    def _setup_activation_checkpointing(self):
        """Setup activation checkpointing"""
        if hasattr(self.model, "gradient_checkpointing_enable"):
            self.model.gradient_checkpointing_enable()
            self.model.config.use_cache = False

    def setup_optimizer_and_scheduler(self):
        """Setup optimizer and scheduler"""
        # Calculate number of training steps
        num_training_steps = self._estimate_training_steps()

        # Create optimizer
        custom_optimizer = CustomOptimizer(self.model, self.config)
        self.optimizer = custom_optimizer.create_optimizer()

        # Create scheduler
        custom_scheduler = CustomScheduler(self.optimizer, self.config, num_training_steps)
        self.scheduler = custom_scheduler.create_scheduler()

        # Setup gradient scaler for mixed precision
        if self.config.memory_config.precision == PrecisionMode.FP16:
            self.scaler = GradScaler()

    def _estimate_training_steps(self) -> int:
        """Estimate number of training steps"""
        # This is a rough estimate - in practice, you'd calculate based on dataset size
        return 10000  # Default estimate

    def prepare_dataloaders(self):
        """Prepare training and evaluation dataloaders"""
        # Load dataset
        if self.config.dataset_path.endswith('.json'):
            with open(self.config.dataset_path, 'r') as f:
                data = json.load(f)
        else:
            # Assume it's a Hugging Face dataset
            dataset = load_dataset(self.config.dataset_path)['train']
            data = [item for item in dataset]

        # Create custom dataset
        custom_dataset = CustomDataset(data, self.tokenizer, self.config.max_seq_length)

        # Split into train/validation
        train_size = int(0.9 * len(custom_dataset))
        train_dataset = torch.utils.data.Subset(custom_dataset, range(train_size))
        eval_dataset = torch.utils.data.Subset(custom_dataset, range(train_size, len(custom_dataset)))

        # Create dataloaders
        train_dataloader = DataLoader(
            train_dataset,
            batch_size=self.config.per_device_train_batch_size,
            shuffle=True,
            num_workers=self.config.preprocessing_num_workers,
            pin_memory=True,
        )

        eval_dataloader = DataLoader(
            eval_dataset,
            batch_size=self.config.per_device_eval_batch_size,
            shuffle=False,
            num_workers=self.config.preprocessing_num_workers,
            pin_memory=True,
        )

        # Prepare with accelerator
        self.model, self.optimizer, train_dataloader, eval_dataloader = self.accelerator.prepare(
            self.model, self.optimizer, train_dataloader, eval_dataloader
        )

        return train_dataloader, eval_dataloader

    def train_epoch(self, train_dataloader, epoch: int):
        """Train for one epoch"""
        self.model.train()
        total_loss = 0
        num_batches = 0

        for batch_idx, batch in enumerate(train_dataloader):
            with autocast(dtype=torch.float16 if self.config.memory_config.precision == PrecisionMode.FP16 else torch.bfloat16):
                outputs = self.model(**batch)
                loss = outputs.loss

            # Backward pass
            if self.scaler:
                self.scaler.scale(loss).backward()
                self.scaler.step(self.optimizer)
                self.scaler.update()
            else:
                self.accelerator.backward(loss)
                self.optimizer.step()

            # Step scheduler
            if self.scheduler:
                self.scheduler.step()

            # Zero gradients
            self.optimizer.zero_grad()

            # Update loss
            total_loss += loss.item()
            num_batches += 1

            # Log progress
            if batch_idx % self.config.logging_steps == 0:
                avg_loss = total_loss / num_batches
                lr = self.optimizer.param_groups[0]['lr']
                self.logger.info(f"Epoch {epoch}, Step {batch_idx}, Loss: {avg_loss:.4f}, LR: {lr:.2e}")

                # Log to wandb if enabled
                if self.config.report_to == "wandb" and self.accelerator.is_main_process:
                    wandb.log({
                        "train_loss": avg_loss,
                        "learning_rate": lr,
                        "epoch": epoch,
                        "step": batch_idx
                    })

        return total_loss / num_batches

    def evaluate(self, eval_dataloader):
        """Evaluate model"""
        self.model.eval()
        total_loss = 0
        num_batches = 0

        with torch.no_grad():
            for batch in eval_dataloader:
                with autocast(dtype=torch.float16 if self.config.memory_config.precision == PrecisionMode.FP16 else torch.bfloat16):
                    outputs = self.model(**batch)
                    loss = outputs.loss

                total_loss += loss.item()
                num_batches += 1

        avg_loss = total_loss / num_batches
        perplexity = math.exp(avg_loss)

        self.logger.info(f"Evaluation - Loss: {avg_loss:.4f}, Perplexity: {perplexity:.2f}")

        if self.config.report_to == "wandb" and self.accelerator.is_main_process:
            wandb.log({
                "eval_loss": avg_loss,
                "eval_perplexity": perplexity
            })

        return {"eval_loss": avg_loss, "eval_perplexity": perplexity}

    def train(self):
        """Main training loop"""
        self.logger.info("Starting full fine-tuning training")

        # Setup components
        self.setup_accelerator()
        self.load_model_and_tokenizer()
        self.setup_optimizer_and_scheduler()

        # Prepare dataloaders
        train_dataloader, eval_dataloader = self.prepare_dataloaders()

        # Initialize wandb if needed
        if self.config.report_to == "wandb" and self.accelerator.is_main_process:
            wandb.init(project="full-finetune", name=self.config.run_name)
            wandb.config.update(self.config.__dict__)

        # Training loop
        best_eval_loss = float('inf')
        for epoch in range(self.config.num_train_epochs):
            self.logger.info(f"Starting epoch {epoch + 1}/{self.config.num_train_epochs}")

            # Train epoch
            train_loss = self.train_epoch(train_dataloader, epoch)

            # Evaluate
            if self.config.do_eval:
                eval_results = self.evaluate(eval_dataloader)
                eval_loss = eval_results["eval_loss"]

                # Save best model
                if eval_loss < best_eval_loss:
                    best_eval_loss = eval_loss
                    self.save_model(f"best_model_epoch_{epoch}")

            # Save checkpoint
            if (epoch + 1) % 1 == 0:  # Save every epoch
                self.save_model(f"checkpoint_epoch_{epoch}")

        # Save final model
        self.save_model("final_model")

        self.logger.info("Training completed successfully")

    def save_model(self, save_name: str):
        """Save model checkpoint"""
        save_path = Path(self.config.output_dir) / save_name
        save_path.mkdir(parents=True, exist_ok=True)

        # Save model state
        unwrapped_model = self.accelerator.unwrap_model(self.model)
        unwrapped_model.save_pretrained(save_path)

        # Save tokenizer
        self.tokenizer.save_pretrained(save_path)

        # Save optimizer state
        torch.save(self.optimizer.state_dict(), save_path / "optimizer.pt")

        # Save scheduler state
        if self.scheduler:
            torch.save(self.scheduler.state_dict(), save_path / "scheduler.pt")

        # Save training config
        with open(save_path / "training_config.json", 'w') as f:
            json.dump(self.config.__dict__, f, indent=2, default=str)

        self.logger.info(f"Model saved to {save_path}")

    def get_memory_usage_report(self) -> str:
        """Generate memory usage report"""
        memory_info = self.memory_monitor.get_memory_info()
        report = "Memory Usage Report:\n"
        report += f"CPU: {memory_info['cpu']['used']:.2f}GB / {memory_info['cpu']['total']:.2f}GB ({memory_info['cpu']['percent']:.1f}%)\n"

        if 'gpu' in memory_info:
            for gpu in memory_info['gpu']:
                report += f"GPU {gpu['gpu_id']}: {gpu['used']:.2f}GB / {gpu['total']:.2f}GB ({gpu['used']/gpu['total']*100:.1f}%)\n"

        return report

def create_memory_efficient_configs():
    """Create memory-efficient training configurations"""

    # Ultra-memory-efficient for large models
    ultra_efficient_config = FullFineTuneConfig(
        model_name_or_path="meta-llama/Llama-2-70b-hf",
        dataset_path="datasets/large_dataset.json",
        output_dir="outputs/ultra_efficient",
        memory_config=MemoryConfig(
            mode=MemoryMode.HYBRID,
            precision=PrecisionMode.FP16,
            offloading=OffloadingStrategy.CPU,
            enable_gradient_accumulation=True,
            enable_activation_checkpointing=True,
            enable_cpu_offload=True,
            enable_mixed_precision=True
        ),
        training_params={
            "learning_rate": 1e-5,
            "num_train_epochs": 2,
            "per_device_train_batch_size": 1,
            "gradient_accumulation_steps": 64
        }
    )

    # Balanced for medium models
    balanced_config = FullFineTuneConfig(
        model_name_or_path="mistralai/Mistral-7B-v0.1",
        dataset_path="datasets/medium_dataset.json",
        output_dir="outputs/balanced",
        memory_config=MemoryConfig(
            mode=MemoryMode.GRADIENT_CHECKPOINTING,
            precision=PrecisionMode.BF16,
            offloading=OffloadingStrategy.NONE,
            enable_gradient_accumulation=True,
            enable_activation_checkpointing=True,
            enable_mixed_precision=True
        ),
        training_params={
            "learning_rate": 2e-5,
            "num_train_epochs": 3,
            "per_device_train_batch_size": 2,
            "gradient_accumulation_steps": 16
        }
    )

    # High-performance for small models
    high_performance_config = FullFineTuneConfig(
        model_name_or_path="gpt2-medium",
        dataset_path="datasets/small_dataset.json",
        output_dir="outputs/high_performance",
        memory_config=MemoryConfig(
            mode=MemoryMode.STANDARD,
            precision=PrecisionMode.FP32,
            offloading=OffloadingStrategy.NONE,
            enable_gradient_accumulation=False,
            enable_activation_checkpointing=False,
            enable_mixed_precision=False
        ),
        training_params={
            "learning_rate": 5e-5,
            "num_train_epochs": 5,
            "per_device_train_batch_size": 8,
            "gradient_accumulation_steps": 1
        }
    )

    return {
        "ultra_efficient": ultra_efficient_config,
        "balanced": balanced_config,
        "high_performance": high_performance_config
    }

def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Memory-Efficient Full Fine-Tuning Trainer")
    parser.add_argument("--config", type=str, help="Path to configuration file")
    parser.add_argument("--model", type=str, help="Model name or path")
    parser.add_argument("--dataset", type=str, help="Dataset path")
    parser.add_argument("--output", type=str, help="Output directory")
    parser.add_argument("--learning-rate", type=float, default=2e-5, help="Learning rate")
    parser.add_argument("--batch-size", type=int, default=1, help="Batch size")
    parser.add_argument("--epochs", type=int, default=3, help="Number of epochs")
    parser.add_argument("--gradient-accumulation", type=int, default=32, help="Gradient accumulation steps")
    parser.add_argument("--memory-mode", choices=["standard", "gradient_checkpointing", "cpu_offloading", "hybrid"], default="hybrid", help="Memory optimization mode")
    parser.add_argument("--precision", choices=["fp32", "fp16", "bf16"], default="fp16", help="Precision mode")
    parser.add_argument("--template", choices=["ultra_efficient", "balanced", "high_performance"], help="Use preset configuration")

    args = parser.parse_args()

    # Create trainer
    if args.template:
        configs = create_memory_efficient_configs()
        config = configs[args.template]
    elif args.config:
        # Load from file
        with open(args.config, 'r') as f:
            config_data = json.load(f)
        config = FullFineTuneConfig(**config_data)
    else:
        # Create from command line args
        config = FullFineTuneConfig(
            model_name_or_path=args.model,
            dataset_path=args.dataset,
            output_dir=args.output,
            learning_rate=args.learning_rate,
            num_train_epochs=args.epochs,
            per_device_train_batch_size=args.batch_size,
            gradient_accumulation_steps=args.gradient_accumulation,
            memory_config=MemoryConfig(
                mode=MemoryMode(args.memory_mode),
                precision=PrecisionMode(args.precision)
            )
        )

    # Train
    trainer = MemoryEfficientTrainer(config)
    trainer.train()

    # Print memory report
    print(trainer.get_memory_usage_report())

    print("Full fine-tuning completed successfully!")

if __name__ == "__main__":
    main()