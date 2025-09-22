#!/usr/bin/env python3
"""
Advanced LoRA (Low-Rank Adaptation) Training System
Implements state-of-the-art LoRA training with memory optimization and GGUF integration
"""

import os
import sys
import json
import torch
import logging
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union, Set
from dataclasses import dataclass, field
from enum import Enum
import time
import gc
from collections import defaultdict
import math
import psutil
from abc import ABC, abstractmethod

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from transformers import (
        AutoTokenizer, AutoModelForCausalLM, TrainingArguments, Trainer,
        DataCollatorForLanguageModeling, BitsAndBytesConfig,
        PreTrainedModel, PreTrainedTokenizer, get_linear_schedule_with_warmup
    )
    from peft import (
        LoraConfig, PeftModel, get_peft_model, TaskType,
        prepare_model_for_kbit_training, LoftQConfig
    )
    from datasets import Dataset, DatasetDict, load_dataset
    from torch.optim import AdamW, SGD, Adam, RMSprop
    from torch.optim.lr_scheduler import _LRScheduler
    from torch.utils.data import DataLoader, Dataset as TorchDataset
    import torch.nn as nn
    import torch.nn.functional as F
    from torch.cuda.amp import GradScaler, autocast
    from accelerate import Accelerator
    from accelerate.utils import DistributedDataParallelKwargs, find_executable_batch_size
    import wandb
    from trl import SFTTrainer, SFTConfig
    HAS_DEPS = True
except ImportError as e:
    logging.warning(f"Required dependencies not installed: {e}")
    HAS_DEPS = False

class LoRAMode(Enum):
    """LoRA training modes"""
    STANDARD = "standard"              # Standard LoRA
    QLoRA = "qlora"                    # Quantized LoRA
    LoftQ = "loftq"                    # LoftQ initialization
    DORA = "dora"                      # DoRA (Weight-Decomposed LoRA)
    VERA = "vera"                      # VeRA (Vector-based Random Adaptation)

class MemoryStrategy(Enum):
    """Memory optimization strategies"""
    AUTO = "auto"                      # Automatic optimization
    CONSERVATIVE = "conservative"      # Conservative memory usage
    BALANCED = "balanced"              # Balanced approach
    AGGRESSIVE = "aggressive"          # Aggressive memory usage
    ULTRA_EFFICIENT = "ultra_efficient" # Maximum memory savings

class OptimizerType(Enum):
    """Optimizer types"""
    ADAMW = "adamw"
    ADAM = "adam"
    SGD = "sgd"
    RMSprop = "rmsprop"
    ADAM_8BIT = "adam_8bit"
    LION = "lion"

class SchedulerType(Enum):
    """Learning rate scheduler types"""
    COSINE = "cosine"
    LINEAR = "linear"
    CONSTANT = "constant"
    COSINE_WITH_RESTARTS = "cosine_with_restarts"
    POLYNOMIAL = "polynomial"

@dataclass
class LoRAConfig:
    """LoRA configuration parameters"""
    # LoRA hyperparameters
    r: int = 8                        # Rank of LoRA matrices
    lora_alpha: int = 16               # LoRA scaling parameter
    lora_dropout: float = 0.1           # Dropout probability for LoRA layers
    target_modules: Optional[List[str]] = None  # Target modules for LoRA adaptation
    fan_in_fan_out: bool = False       # Set this to True if the layer to replace stores weight like (fan_in, fan_out)
    bias: str = "none"                # Bias type for LoRA. Can be 'none', 'all' or 'lora_only'

    # Advanced LoRA options
    modules_to_save: Optional[List[str]] = None  # List of modules to save
    init_lora_weights: bool = True     # Whether to initialize LoRA weights
    use_rslora: bool = False          # Whether to use Rank-Stabilized LoRA
    use_dora: bool = False            # Whether to use DoRA (Weight-Decomposed LoRA)

@dataclass
class QuantizationConfig:
    """Quantization configuration for QLoRA"""
    load_in_4bit: bool = True
    load_in_8bit: bool = False
    bnb_4bit_quant_type: str = "nf4"   # 'nf4' or 'fp4'
    bnb_4bit_compute_dtype: torch.dtype = torch.bfloat16
    bnb_4bit_use_double_quant: bool = True
    llm_int8_threshold: float = 6.0
    llm_int8_has_fp16_weight: bool = False

@dataclass
class AdvancedLoRAConfig:
    """Complete LoRA training configuration"""
    # Model and data
    model_name_or_path: str
    dataset_path: str
    output_dir: str

    # LoRA configuration
    lora_config: LoRAConfig = field(default_factory=LoRAConfig)
    lora_mode: LoRAMode = LoRAMode.QLoRA
    quantization_config: Optional[QuantizationConfig] = None

    # Training parameters
    learning_rate: float = 2e-4
    num_train_epochs: int = 3
    per_device_train_batch_size: int = 4
    per_device_eval_batch_size: int = 4
    gradient_accumulation_steps: int = 1
    warmup_ratio: float = 0.03
    max_grad_norm: float = 1.0

    # Dataset
    max_seq_length: int = 2048
    packing: bool = False
    dataset_text_field: str = "text"

    # Optimization
    optimizer: OptimizerType = OptimizerType.ADAMW
    scheduler: SchedulerType = SchedulerType.COSINE
    weight_decay: float = 0.01
    beta1: float = 0.9
    beta2: float = 0.999
    eps: float = 1e-8

    # Memory optimization
    memory_strategy: MemoryStrategy = MemoryStrategy.BALANCED
    gradient_checkpointing: bool = True
    fp16: bool = True
    bf16: bool = False
    tf32: bool = False

    # Evaluation and logging
    evaluation_strategy: str = "no"
    eval_steps: int = 100
    save_strategy: str = "epoch"
    save_steps: int = 500
    save_total_limit: int = 3
    logging_steps: int = 10
    report_to: str = "none"

    # Distributed training
    ddp_find_unused_parameters: bool = False
    deepspeed: Optional[str] = None

    # Advanced options
    max_steps: Optional[int] = None
    lr_scheduler_type: str = "cosine"
    warmup_steps: Optional[int] = None
    group_by_length: bool = False

    def __post_init__(self):
        """Post-initialization setup"""
        # Set default quantization config for QLoRA
        if self.lora_mode == LoRAMode.QLoRA and self.quantization_config is None:
            self.quantization_config = QuantizationConfig()

        # Set default target modules if not provided
        if self.lora_config.target_modules is None:
            self.lora_config.target_modules = self._get_default_target_modules()

        # Setup memory strategy defaults
        self._setup_memory_defaults()

    def _get_default_target_modules(self) -> List[str]:
        """Get default target modules based on model architecture"""
        model_name = self.model_name_or_path.lower()

        if "llama" in model_name or "mistral" in model_name:
            return ["q_proj", "v_proj", "k_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
        elif "gpt" in model_name:
            return ["c_attn", "c_proj", "mlp.c_fc", "mlp.c_proj"]
        elif "falcon" in model_name:
            return ["query_key_value", "dense", "dense_h_to_4h", "dense_4h_to_h"]
        else:
            return ["q_proj", "v_proj", "k_proj", "o_proj"]

    def _setup_memory_defaults(self):
        """Setup memory strategy defaults"""
        if self.memory_strategy == MemoryStrategy.ULTRA_EFFICIENT:
            self.gradient_checkpointing = True
            self.per_device_train_batch_size = 1
            self.gradient_accumulation_steps = max(self.gradient_accumulation_steps, 16)
        elif self.memory_strategy == MemoryStrategy.CONSERVATIVE:
            self.gradient_checkpointing = True
            self.per_device_train_batch_size = min(self.per_device_train_batch_size, 2)

class MemoryAnalyzer:
    """Analyzes memory requirements and provides optimization recommendations"""

    def __init__(self):
        self.has_gpu = torch.cuda.is_available()
        self.gpu_memory = []
        self.cpu_memory = psutil.virtual_memory()

        if self.has_gpu:
            for i in range(torch.cuda.device_count()):
                props = torch.cuda.get_device_properties(i)
                self.gpu_memory.append({
                    "device": i,
                    "total": props.total_memory / (1024**3),  # GB
                    "name": props.name
                })

    def analyze_model_memory_requirements(self, model_name: str, config: AdvancedLoRAConfig) -> Dict[str, Any]:
        """Analyze memory requirements for model training"""
        analysis = {
            "model_name": model_name,
            "estimated_memory_gb": 0,
            "recommended_batch_size": 1,
            "recommended_gradient_accumulation": 1,
            "memory_warnings": [],
            "optimization_suggestions": []
        }

        # Estimate model size
        model_size_gb = self._estimate_model_size(model_name)
        analysis["estimated_memory_gb"] = model_size_gb

        # Calculate available memory
        if self.has_gpu and self.gpu_memory:
            available_gpu_memory = self.gpu_memory[0]["total"] * 0.8  # Use 80% of available memory

            # Estimate memory usage breakdown
            base_model_memory = model_size_gb
            lora_memory = model_size_gb * 0.01 * config.lora_config.r  # Rough estimate
            optimizer_memory = model_size_gb * 4  # AdamW optimizer states
            activation_memory = config.per_device_train_batch_size * model_size_gb * 0.1

            total_required = base_model_memory + lora_memory + optimizer_memory + activation_memory

            if total_required > available_gpu_memory:
                analysis["memory_warnings"].append(
                    f"Estimated memory requirement ({total_required:.1f}GB) exceeds available GPU memory ({available_gpu_memory:.1f}GB)"
                )

                # Suggest optimizations
                if config.memory_strategy != MemoryStrategy.ULTRA_EFFICIENT:
                    analysis["optimization_suggestions"].append("Consider using ULTRA_EFFICIENT memory strategy")

                if config.per_device_train_batch_size > 1:
                    new_batch_size = 1
                    analysis["recommended_batch_size"] = new_batch_size
                    analysis["optimization_suggestions"].append(f"Reduce batch size to {new_batch_size}")

                # Calculate required gradient accumulation
                if config.gradient_accumulation_steps < 32:
                    new_grad_accum = min(32, int(available_gpu_memory / activation_memory))
                    analysis["recommended_gradient_accumulation"] = new_grad_accum
                    analysis["optimization_suggestions"].append(f"Increase gradient accumulation to {new_grad_accum}")

        return analysis

    def _estimate_model_size(self, model_name: str) -> float:
        """Estimate model size in GB"""
        # Rough estimates based on common model sizes
        if "7b" in model_name.lower():
            return 14.0  # ~14GB for 7B model
        elif "13b" in model_name.lower():
            return 26.0  # ~26GB for 13B model
        elif "30b" in model_name.lower():
            return 60.0  # ~60GB for 30B model
        elif "70b" in model_name.lower():
            return 140.0  # ~140GB for 70B model
        else:
            return 20.0  # Default estimate

class LoRATrainer:
    """Advanced LoRA trainer with multiple optimization strategies"""

    def __init__(self, config: AdvancedLoRAConfig):
        self.config = config
        self.model = None
        self.tokenizer = None
        self.peft_config = None
        self.peft_model = None
        self.trainer = None
        self.memory_analyzer = MemoryAnalyzer()
        self.setup_logging()

        if not HAS_DEPS:
            raise ImportError("Required dependencies not installed")

    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def prepare_model(self):
        """Prepare model for LoRA training"""
        self.logger.info(f"Preparing model: {self.config.model_name_or_path}")

        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.config.model_name_or_path,
            trust_remote_code=True
        )

        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        # Load base model with appropriate configuration
        model_kwargs = self._get_model_kwargs()

        self.model = AutoModelForCausalLM.from_pretrained(
            self.config.model_name_or_path,
            **model_kwargs
        )

        # Prepare model for training
        if self.config.lora_mode == LoRAMode.QLoRA:
            self.model = prepare_model_for_kbit_training(self.model)

        # Create PEFT configuration
        self.peft_config = self._create_peft_config()

        # Apply LoRA
        self.peft_model = get_peft_model(self.model, self.peft_config)

        # Print trainable parameters info
        self._print_trainable_params()

    def _get_model_kwargs(self) -> Dict[str, Any]:
        """Get model loading kwargs based on configuration"""
        kwargs = {
            "trust_remote_code": True,
            "device_map": "auto",
        }

        # Add quantization config if using QLoRA
        if self.config.lora_mode == LoRAMode.QLoRA and self.config.quantization_config:
            kwargs["quantization_config"] = BitsAndBytesConfig(
                load_in_4bit=self.config.quantization_config.load_in_4bit,
                load_in_8bit=self.config.quantization_config.load_in_8bit,
                bnb_4bit_quant_type=self.config.quantization_config.bnb_4bit_quant_type,
                bnb_4bit_compute_dtype=self.config.quantization_config.bnb_4bit_compute_dtype,
                bnb_4bit_use_double_quant=self.config.quantization_config.bnb_4bit_use_double_quant,
            )

        # Add torch dtype
        if self.config.fp16:
            kwargs["torch_dtype"] = torch.float16
        elif self.config.bf16:
            kwargs["torch_dtype"] = torch.bfloat16

        return kwargs

    def _create_peft_config(self) -> LoraConfig:
        """Create PEFT configuration"""
        # Handle different LoRA modes
        if self.config.lora_mode == LoRAMode.DORA:
            return self._create_dora_config()
        elif self.config.lora_mode == LoRAMode.LoftQ:
            return self._create_loftq_config()
        elif self.config.lora_mode == LoRAMode.VERA:
            return self._create_vera_config()
        else:
            return self._create_standard_lora_config()

    def _create_standard_lora_config(self) -> LoraConfig:
        """Create standard LoRA configuration"""
        return LoraConfig(
            r=self.config.lora_config.r,
            lora_alpha=self.config.lora_config.lora_alpha,
            lora_dropout=self.config.lora_config.lora_dropout,
            target_modules=self.config.lora_config.target_modules,
            bias=self.config.lora_config.bias,
            task_type=TaskType.CAUSAL_LM,
            modules_to_save=self.config.lora_config.modules_to_save,
            init_lora_weights=self.config.lora_config.init_lora_weights,
            use_rslora=self.config.lora_config.use_rslora,
        )

    def _create_dora_config(self) -> LoraConfig:
        """Create DoRA (Weight-Decomposed LoRA) configuration"""
        return LoraConfig(
            r=self.config.lora_config.r,
            lora_alpha=self.config.lora_config.lora_alpha,
            lora_dropout=self.config.lora_config.lora_dropout,
            target_modules=self.config.lora_config.target_modules,
            bias=self.config.lora_config.bias,
            task_type=TaskType.CAUSAL_LM,
            use_dora=True,  # Enable DoRA
            modules_to_save=self.config.lora_config.modules_to_save,
            init_lora_weights=self.config.lora_config.init_lora_weights,
        )

    def _create_loftq_config(self) -> LoraConfig:
        """Create LoftQ configuration"""
        return LoraConfig(
            r=self.config.lora_config.r,
            lora_alpha=self.config.lora_config.lora_alpha,
            lora_dropout=self.config.lora_config.lora_dropout,
            target_modules=self.config.lora_config.target_modules,
            bias=self.config.lora_config.bias,
            task_type=TaskType.CAUSAL_LM,
            init_lora_weights="loftq",  # LoftQ initialization
            loftq_config=LoftQConfig(loftq_bits=4),  # 4-bit LoftQ
            modules_to_save=self.config.lora_config.modules_to_save,
        )

    def _create_vera_config(self) -> LoraConfig:
        """Create VeRA (Vector-based Random Adaptation) configuration"""
        return LoraConfig(
            r=self.config.lora_config.r,
            lora_alpha=self.config.lora_config.lora_alpha,
            lora_dropout=self.config.lora_config.lora_dropout,
            target_modules=self.config.lora_config.target_modules,
            bias=self.config.lora_config.bias,
            task_type=TaskType.CAUSAL_LM,
            use_rslora=True,  # Enable VeRA
            init_lora_weights=False,  # Random initialization
            modules_to_save=self.config.lora_config.modules_to_save,
        )

    def _print_trainable_params(self):
        """Print information about trainable parameters"""
        trainable_params = 0
        all_param = 0
        for _, param in self.peft_model.named_parameters():
            all_param += param.numel()
            if param.requires_grad:
                trainable_params += param.numel()

        percentage = 100 * trainable_params / all_param
        self.logger.info(f"Trainable params: {trainable_params:,} ({percentage:.2f}% of total)")
        self.logger.info(f"All params: {all_param:,}")

    def load_and_prepare_dataset(self):
        """Load and prepare dataset for training"""
        self.logger.info(f"Loading dataset from: {self.config.dataset_path}")

        # Load dataset
        if self.config.dataset_path.endswith('.json'):
            with open(self.config.dataset_path, 'r') as f:
                data = json.load(f)
            dataset = Dataset.from_list(data)
        elif self.config.dataset_path.endswith('.jsonl'):
            data = []
            with open(self.config.dataset_path, 'r') as f:
                for line in f:
                    data.append(json.loads(line))
            dataset = Dataset.from_list(data)
        else:
            # Assume it's a Hugging Face dataset
            dataset = load_dataset(self.config.dataset_path)['train']

        # Tokenize dataset
        def tokenize_function(examples):
            return self.tokenizer(
                examples[self.config.dataset_text_field],
                truncation=True,
                max_length=self.config.max_seq_length,
                padding=False,  # Will be handled by data collator
            )

        tokenized_dataset = dataset.map(
            tokenize_function,
            batched=True,
            remove_columns=dataset.column_names,
            desc="Tokenizing dataset"
        )

        return tokenized_dataset

    def create_training_arguments(self) -> TrainingArguments:
        """Create training arguments"""
        # Calculate warmup steps if not provided
        warmup_steps = self.config.warmup_steps
        if warmup_steps is None:
            warmup_steps = int(self.config.num_train_epochs * 1000 * self.config.warmup_ratio)

        return TrainingArguments(
            output_dir=self.config.output_dir,
            learning_rate=self.config.learning_rate,
            num_train_epochs=self.config.num_train_epochs,
            per_device_train_batch_size=self.config.per_device_train_batch_size,
            per_device_eval_batch_size=self.config.per_device_eval_batch_size,
            gradient_accumulation_steps=self.config.gradient_accumulation_steps,
            warmup_steps=warmup_steps,
            max_grad_norm=self.config.max_grad_norm,
            logging_steps=self.config.logging_steps,
            evaluation_strategy=self.config.evaluation_strategy,
            eval_steps=self.config.eval_steps,
            save_strategy=self.config.save_strategy,
            save_steps=self.config.save_steps,
            save_total_limit=self.config.save_total_limit,
            report_to=self.config.report_to,
            fp16=self.config.fp16,
            bf16=self.config.bf16,
            tf32=self.config.tf32,
            gradient_checkpointing=self.config.gradient_checkpointing,
            ddp_find_unused_parameters=self.config.ddp_find_unused_parameters,
            deepspeed=self.config.deepspeed,
            max_steps=self.config.max_steps,
            lr_scheduler_type=self.config.lr_scheduler_type,
            group_by_length=self.config.group_by_length,
        )

    def create_trainer(self, dataset):
        """Create trainer instance"""
        training_args = self.create_training_arguments()

        # Data collator
        data_collator = DataCollatorForLanguageModeling(
            tokenizer=self.tokenizer,
            mlm=False,
            return_tensors="pt"
        )

        # Create trainer
        self.trainer = Trainer(
            model=self.peft_model,
            args=training_args,
            train_dataset=dataset,
            eval_dataset=None,  # Will be set if evaluation is enabled
            data_collator=data_collator,
        )

        return self.trainer

    def train(self):
        """Run LoRA training"""
        self.logger.info("Starting LoRA training")

        # Analyze memory requirements
        memory_analysis = self.memory_analyzer.analyze_model_memory_requirements(
            self.config.model_name_or_path, self.config
        )
        self.logger.info(f"Memory analysis: {memory_analysis}")

        # Prepare model
        self.prepare_model()

        # Load dataset
        dataset = self.load_and_prepare_dataset()

        # Create trainer
        trainer = self.create_trainer(dataset)

        # Initialize wandb if needed
        if self.config.report_to == "wandb":
            wandb.init(project="lora-training", name=f"lora-{self.config.model_name_or_path}")

        # Start training
        trainer.train()

        # Save final model
        self.save_model()

        self.logger.info("LoRA training completed successfully")

    def save_model(self):
        """Save trained LoRA model"""
        output_path = Path(self.config.output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Save LoRA adapter
        self.peft_model.save_pretrained(output_path)

        # Save tokenizer
        self.tokenizer.save_pretrained(output_path)

        # Save configuration
        config_dict = {
            "lora_config": self.config.lora_config.__dict__,
            "training_config": self.config.__dict__,
            "model_name": self.config.model_name_or_path,
        }

        with open(output_path / "lora_config.json", 'w') as f:
            json.dump(config_dict, f, indent=2, default=str)

        self.logger.info(f"LoRA model saved to {output_path}")

    def merge_and_save(self, merge_path: str):
        """Merge LoRA adapter with base model and save"""
        if self.peft_model is None:
            raise ValueError("No trained LoRA model available")

        self.logger.info(f"Merging LoRA adapter and saving to {merge_path}")

        # Merge adapter weights
        merged_model = self.peft_model.merge_and_unload()

        # Save merged model
        merge_path = Path(merge_path)
        merge_path.mkdir(parents=True, exist_ok=True)

        merged_model.save_pretrained(merge_path)
        self.tokenizer.save_pretrained(merge_path)

        self.logger.info(f"Merged model saved to {merge_path}")

class LoRAConfigManager:
    """Manages LoRA configuration presets and templates"""

    @staticmethod
    def create_efficient_configs():
        """Create memory-efficient LoRA configurations"""
        configs = {}

        # Ultra-efficient for large models
        configs["ultra_efficient"] = AdvancedLoRAConfig(
            model_name_or_path="meta-llama/Llama-2-70B-hf",
            dataset_path="datasets/large_dataset.json",
            output_dir="outputs/lora_ultra_efficient",
            lora_config=LoRAConfig(r=8, lora_alpha=16, lora_dropout=0.1),
            lora_mode=LoRAMode.QLoRA,
            per_device_train_batch_size=1,
            gradient_accumulation_steps=32,
            learning_rate=1e-4,
            memory_strategy=MemoryStrategy.ULTRA_EFFICIENT,
            gradient_checkpointing=True,
            fp16=True,
        )

        # Balanced for medium models
        configs["balanced"] = AdvancedLoRAConfig(
            model_name_or_path="mistralai/Mistral-7B-v0.1",
            dataset_path="datasets/medium_dataset.json",
            output_dir="outputs/lora_balanced",
            lora_config=LoRAConfig(r=16, lora_alpha=32, lora_dropout=0.05),
            lora_mode=LoRAMode.QLoRA,
            per_device_train_batch_size=4,
            gradient_accumulation_steps=4,
            learning_rate=2e-4,
            memory_strategy=MemoryStrategy.BALANCED,
            gradient_checkpointing=True,
            bf16=True,
        )

        # High-performance for small models
        configs["high_performance"] = AdvancedLoRAConfig(
            model_name_or_path="gpt2-medium",
            dataset_path="datasets/small_dataset.json",
            output_dir="outputs/lora_high_performance",
            lora_config=LoRAConfig(r=32, lora_alpha=64, lora_dropout=0.0),
            lora_mode=LoRAMode.STANDARD,
            per_device_train_batch_size=8,
            gradient_accumulation_steps=1,
            learning_rate=3e-4,
            memory_strategy=MemoryStrategy.AGGRESSIVE,
            gradient_checkpointing=False,
            fp16=False,
        )

        # DoRA configuration
        configs["dora"] = AdvancedLoRAConfig(
            model_name_or_path="mistralai/Mistral-7B-v0.1",
            dataset_path="datasets/medium_dataset.json",
            output_dir="outputs/lora_dora",
            lora_config=LoRAConfig(r=16, lora_alpha=32, lora_dropout=0.05, use_dora=True),
            lora_mode=LoRAMode.DORA,
            per_device_train_batch_size=4,
            gradient_accumulation_steps=4,
            learning_rate=1e-4,
            memory_strategy=MemoryStrategy.BALANCED,
            gradient_checkpointing=True,
            bf16=True,
        )

        return configs

    @staticmethod
    def save_config_template(config_name: str, config: AdvancedLoRAConfig, save_path: str):
        """Save configuration template to file"""
        template = {
            "config_name": config_name,
            "description": f"Template for {config_name} LoRA training",
            "config": config.__dict__,
            "usage_notes": [
                "Adjust model_name_or_path, dataset_path, and output_dir as needed",
                "Fine-tune hyperparameters based on your specific use case",
                "Monitor memory usage during training"
            ]
        }

        with open(save_path, 'w') as f:
            json.dump(template, f, indent=2, default=str)

def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Advanced LoRA Training System")
    parser.add_argument("--config", type=str, help="Path to configuration file")
    parser.add_argument("--model", type=str, help="Model name or path")
    parser.add_argument("--dataset", type=str, help="Dataset path")
    parser.add_argument("--output", type=str, help="Output directory")
    parser.add_argument("--template", choices=["ultra_efficient", "balanced", "high_performance", "dora"], help="Use preset configuration")
    parser.add_argument("--lora-mode", choices=["standard", "qlora", "dora", "loftq", "vera"], default="qlora", help="LoRA training mode")
    parser.add_argument("--rank", type=int, default=8, help="LoRA rank")
    parser.add_argument("--alpha", type=int, default=16, help="LoRA alpha")
    parser.add_argument("--learning-rate", type=float, default=2e-4, help="Learning rate")
    parser.add_argument("--batch-size", type=int, default=4, help="Batch size")
    parser.add_argument("--epochs", type=int, default=3, help="Number of epochs")
    parser.add_argument("--memory-strategy", choices=["auto", "conservative", "balanced", "aggressive", "ultra_efficient"], default="balanced", help="Memory optimization strategy")
    parser.add_argument("--merge", action="store_true", help="Merge LoRA adapter after training")

    args = parser.parse_args()

    # Create configuration
    if args.template:
        configs = LoRAConfigManager.create_efficient_configs()
        config = configs[args.template]
    elif args.config:
        # Load from file
        with open(args.config, 'r') as f:
            config_data = json.load(f)
        config = AdvancedLoRAConfig(**config_data)
    else:
        # Create from command line args
        config = AdvancedLoRAConfig(
            model_name_or_path=args.model,
            dataset_path=args.dataset,
            output_dir=args.output,
            lora_mode=LoRAMode(args.lora_mode),
            lora_config=LoRAConfig(r=args.rank, lora_alpha=args.alpha),
            learning_rate=args.learning_rate,
            num_train_epochs=args.epochs,
            per_device_train_batch_size=args.batch_size,
            memory_strategy=MemoryStrategy(args.memory_strategy),
        )

    # Train
    trainer = LoRATrainer(config)
    trainer.train()

    # Merge if requested
    if args.merge:
        merge_path = f"{args.output}_merged"
        trainer.merge_and_save(merge_path)

    print("LoRA training completed successfully!")

if __name__ == "__main__":
    main()