#!/usr/bin/env python3
"""
Advanced LoRA and Fine-Tuning Trainer
Implements state-of-the-art parameter-efficient training methods
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

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    import transformers
    from transformers import (
        AutoTokenizer, AutoModelForCausalLM, TrainingArguments, Trainer,
        DataCollatorForLanguageModeling, BitsAndBytesConfig, TrainerCallback
    )
    from transformers.trainer_utils import get_last_checkpoint
    from datasets import Dataset, DatasetDict, load_dataset
    from peft import LoraConfig, PeftModel, get_peft_model, TaskType, prepare_model_for_kbit_training
    import bitsandbytes as bnb
    from accelerate import Accelerator
    from torch.utils.data import DataLoader
    from torch.optim import AdamW, SGD, Adam, lr_scheduler
    import wandb
    HAS_DEPS = True
except ImportError as e:
    logging.warning(f"Required dependencies not installed: {e}")
    HAS_DEPS = False

class OptimizerType(Enum):
    ADAMW = "adamw"
    ADAM = "adam"
    SGD = "sgd"
    LION = "lion"
    ADAM_8BIT = "adam_8bit"
    SGD_8BIT = "sgd_8bit"

class SchedulerType(Enum):
    LINEAR = "linear"
    COSINE = "cosine"
    COSINE_WITH_RESTARTS = "cosine_with_restarts"
    POLYNOMIAL = "polynomial"
    CONSTANT = "constant"
    CONSTANT_WITH_WARMUP = "constant_with_warmup"

class QuantizationType(Enum):
    NONE = "none"
    FP4 = "fp4"
    NF4 = "nf4"
    INT8 = "int8"
    FP8 = "fp8"

class TrainingMode(Enum):
    LORA = "lora"
    FULL_FINE_TUNE = "full_fine_tune"
    QLORA = "qlora"
    DORA = "dora"
    ADALORA = "adalora"

@dataclass
class LoRAConfig:
    """LoRA configuration parameters"""
    r: int = 8  # Rank
    lora_alpha: int = 16  # Alpha parameter for LoRA scaling
    lora_dropout: float = 0.1  # Dropout probability for LoRA layers
    target_modules: Optional[List[str]] = None  # Target modules for LoRA
    bias: str = "none"  # Bias type: "none", "all", "lora_only"
    task_type: str = "CAUSAL_LM"  # Task type
    use_rslora: bool = False  # Use Rank-Stabilized LoRA
    use_dora: bool = False  # Use DoRA (Weight-Decomposed LoRA)
    modules_to_save: Optional[List[str]] = None  # Additional modules to save
    init_lora_weights: bool = True  # Initialize LoRA weights

@dataclass
class TrainingHyperparameters:
    """Training hyperparameters"""
    learning_rate: float = 3e-4
    weight_decay: float = 0.01
    num_train_epochs: int = 3
    per_device_train_batch_size: int = 4
    per_device_eval_batch_size: int = 4
    gradient_accumulation_steps: int = 4
    warmup_steps: int = 100
    logging_steps: int = 50
    save_steps: int = 500
    eval_steps: int = 500
    save_total_limit: int = 3
    load_best_model_at_end: bool = True
    metric_for_best_model: str = "eval_loss"
    greater_is_better: bool = False
    dataloader_drop_last: bool = True
    dataloader_num_workers: int = 0
    max_grad_norm: float = 1.0
    group_by_length: bool = False
    remove_unused_columns: bool = True

@dataclass
class OptimizationConfig:
    """Optimization and memory configuration"""
    optimizer_type: OptimizerType = OptimizerType.ADAMW
    scheduler_type: SchedulerType = SchedulerType.COSINE
    quantization_type: QuantizationType = QuantizationType.NONE
    gradient_checkpointing: bool = True
    use_8bit_optimizer: bool = False
    use_memory_efficient_attention: bool = True
    use_flash_attention: bool = True
    fp16: bool = True
    bf16: bool = False
    tf32: bool = False
    ddp_find_unused_parameters: bool = False
    deepspeed_config: Optional[str] = None

@dataclass
class AdvancedTrainingConfig:
    """Complete training configuration"""
    # Model and data
    model_name_or_path: str
    dataset_path: str
    output_dir: str

    # Training mode
    training_mode: TrainingMode = TrainingMode.LORA

    # Sub-configurations
    lora_config: LoRAConfig = field(default_factory=LoRAConfig)
    training_params: TrainingHyperparameters = field(default_factory=TrainingHyperparameters)
    optimization: OptimizationConfig = field(default_factory=OptimizationConfig)

    # Dataset configuration
    dataset_text_field: str = "text"
    max_seq_length: int = 2048
    packing: bool = False

    # Evaluation
    do_eval: bool = True
    evaluation_strategy: str = "steps"

    # Hugging Face Hub
    push_to_hub: bool = False
    hub_model_id: Optional[str] = None
    hub_token: Optional[str] = None

    # Logging
    report_to: str = "none"
    run_name: Optional[str] = None

    # Resume training
    resume_from_checkpoint: Optional[str] = None

class MemoryOptimizer:
    """Memory optimization utilities for training"""

    @staticmethod
    def setup_memory_efficient_training(model, config: OptimizationConfig):
        """Setup memory-efficient training"""
        if config.gradient_checkpointing:
            model.gradient_checkpointing_enable()
            model.config.use_cache = False

        # Setup quantization
        if config.quantization_type == QuantizationType.NF4:
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.bfloat16,
                bnb_4bit_use_double_quant=True,
            )
            return bnb_config
        elif config.quantization_type == QuantizationType.FP4:
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="fp4",
                bnb_4bit_compute_dtype=torch.float16,
            )
            return bnb_config
        elif config.quantization_type == QuantizationType.INT8:
            bnb_config = BitsAndBytesConfig(load_in_8bit=True)
            return bnb_config

        return None

    @staticmethod
    def get_target_modules(model, target_modules_str: str) -> List[str]:
        """Get target modules for LoRA based on model architecture"""
        if target_modules_str == "all-linear":
            # Find all linear layers
            target_modules = []
            for name, module in model.named_modules():
                if isinstance(module, torch.nn.Linear):
                    target_modules.append(name)
            return target_modules
        elif target_modules_str == "attention":
            # Attention layers only
            target_modules = []
            for name, module in model.named_modules():
                if any(keyword in name.lower() for keyword in ['q_proj', 'k_proj', 'v_proj', 'o_proj', 'query', 'key', 'value', 'out']):
                    target_modules.append(name)
            return target_modules
        elif target_modules_str == "mlp":
            # MLP layers only
            target_modules = []
            for name, module in model.named_modules():
                if any(keyword in name.lower() for keyword in ['gate_proj', 'up_proj', 'down_proj', 'mlp', 'fc']):
                    target_modules.append(name)
            return target_modules
        else:
            # Custom list
            return [module.strip() for module in target_modules_str.split(",")]

class OptimizerFactory:
    """Factory for creating optimizers with various configurations"""

    @staticmethod
    def create_optimizer(model, config: OptimizationConfig, lr: float):
        """Create optimizer based on configuration"""
        # Group parameters for differential learning rates
        no_decay = ["bias", "LayerNorm.weight", "layer_norm.weight"]
        optimizer_grouped_parameters = [
            {
                "params": [p for n, p in model.named_parameters() if not any(nd in n for nd in no_decay)],
                "weight_decay": 0.01 if not config.use_8bit_optimizer else 0.0,
            },
            {
                "params": [p for n, p in model.named_parameters() if any(nd in n for nd in no_decay)],
                "weight_decay": 0.0,
            },
        ]

        if config.optimizer_type == OptimizerType.ADAMW:
            if config.use_8bit_optimizer:
                return bnb.optim.AdamW8bit(optimizer_grouped_parameters, lr=lr)
            else:
                return AdamW(optimizer_grouped_parameters, lr=lr)
        elif config.optimizer_type == OptimizerType.ADAM:
            return Adam(optimizer_grouped_parameters, lr=lr)
        elif config.optimizer_type == OptimizerType.SGD:
            if config.use_8bit_optimizer:
                return bnb.optim.SGD8bit(optimizer_grouped_parameters, lr=lr)
            else:
                return SGD(optimizer_grouped_parameters, lr=lr)
        elif config.optimizer_type == OptimizerType.LION:
            try:
                from lion_pytorch import Lion
                return Lion(optimizer_grouped_parameters, lr=lr, weight_decay=0.01)
            except ImportError:
                logging.warning("Lion optimizer not available, using AdamW instead")
                return AdamW(optimizer_grouped_parameters, lr=lr)
        else:
            raise ValueError(f"Unknown optimizer type: {config.optimizer_type}")

class SchedulerFactory:
    """Factory for creating learning rate schedulers"""

    @staticmethod
    def create_scheduler(optimizer, config: OptimizationConfig, num_training_steps: int, num_warmup_steps: int):
        """Create learning rate scheduler"""
        if config.scheduler_type == SchedulerType.LINEAR:
            return lr_scheduler.LinearLR(
                optimizer,
                start_factor=0.1,
                end_factor=1.0,
                total_iters=num_warmup_steps
            )
        elif config.scheduler_type == SchedulerType.COSINE:
            return lr_scheduler.CosineAnnealingLR(
                optimizer,
                T_max=num_training_steps - num_warmup_steps
            )
        elif config.scheduler_type == SchedulerType.COSINE_WITH_RESTARTS:
            return lr_scheduler.CosineAnnealingWarmRestarts(
                optimizer,
                T_0=1000,  # Restart every 1000 steps
                T_mult=2   # Double restart period each time
            )
        elif config.scheduler_type == SchedulerType.POLYNOMIAL:
            return lr_scheduler.PolynomialLR(
                optimizer,
                total_iters=num_training_steps - num_warmup_steps,
                power=0.9
            )
        elif config.scheduler_type == SchedulerType.CONSTANT:
            return lr_scheduler.ConstantLR(optimizer, factor=1.0)
        elif config.scheduler_type == SchedulerType.CONSTANT_WITH_WARMUP:
            return lr_scheduler.ConstantLR(
                optimizer,
                factor=0.1,
                total_iters=num_warmup_steps
            )
        else:
            raise ValueError(f"Unknown scheduler type: {config.scheduler_type}")

class DatasetProcessor:
    """Dataset processing utilities"""

    def __init__(self, tokenizer, max_seq_length: int):
        self.tokenizer = tokenizer
        self.max_seq_length = max_seq_length

    def preprocess_function(self, examples):
        """Preprocess dataset examples"""
        # Handle different dataset formats
        if "text" in examples:
            texts = examples["text"]
        elif "instruction" in examples and "response" in examples:
            # Format as instruction-response pairs
            texts = []
            for instruction, response in zip(examples["instruction"], examples["response"]):
                texts.append(f"Instruction: {instruction}\n\nResponse: {response}")
        elif "prompt" in examples and "completion" in examples:
            # Format as prompt-completion pairs
            texts = []
            for prompt, completion in zip(examples["prompt"], examples["completion"]):
                texts.append(f"Question: {prompt}\n\nAnswer: {completion}")
        else:
            raise ValueError("Unsupported dataset format")

        # Tokenize
        tokenized = self.tokenizer(
            texts,
            truncation=True,
            padding=False,
            max_length=self.max_seq_length,
            return_tensors=None
        )

        return tokenized

    def create_dataset(self, dataset_path: str) -> Dataset:
        """Create and preprocess dataset"""
        # Load dataset
        if dataset_path.endswith('.json') or dataset_path.endswith('.jsonl'):
            dataset = load_dataset('json', data_files=dataset_path)['train']
        elif Path(dataset_path).is_dir():
            # Assume it's a Hugging Face dataset directory
            dataset = load_dataset(dataset_path)['train']
        else:
            # Try to load as Hugging Face dataset ID
            dataset = load_dataset(dataset_path)['train']

        # Apply preprocessing
        processed_dataset = dataset.map(
            self.preprocess_function,
            batched=True,
            remove_columns=dataset.column_names,
            desc="Tokenizing dataset"
        )

        return processed_dataset

class CustomCallback(TrainerCallback):
    """Custom callback for advanced training monitoring"""

    def __init__(self, config: AdvancedTrainingConfig):
        self.config = config
        self.step_count = 0
        self.start_time = time.time()
        self.loss_history = []
        self.lr_history = []

    def on_train_begin(self, args, state, control, **kwargs):
        logging.info("Training started")
        if wandb.run is not None:
            wandb.config.update({
                "model": self.config.model_name_or_path,
                "training_mode": self.config.training_mode.value,
                "learning_rate": self.config.training_params.learning_rate,
                "batch_size": self.config.training_params.per_device_train_batch_size,
                "max_seq_length": self.config.max_seq_length,
            })

    def on_train_end(self, args, state, control, **kwargs):
        training_time = time.time() - self.start_time
        logging.info(f"Training completed in {training_time:.2f} seconds")
        if wandb.run is not None:
            wandb.log({"training_time": training_time})

    def on_step_end(self, args, state, control, **kwargs):
        self.step_count += 1
        if self.step_count % self.config.training_params.logging_steps == 0:
            if hasattr(state, 'log_history') and state.log_history:
                latest_log = state.log_history[-1]
                if 'loss' in latest_log:
                    self.loss_history.append(latest_log['loss'])
                    if wandb.run is not None:
                        wandb.log({
                            "step": self.step_count,
                            "train_loss": latest_log['loss'],
                            "train_loss_smoothed": np.mean(self.loss_history[-10:])
                        })

    def on_evaluate(self, args, state, control, metrics=None, **kwargs):
        if metrics and wandb.run is not None:
            wandb.log({
                "step": state.global_step,
                "eval_loss": metrics.get("eval_loss", 0),
                "eval_perplexity": math.exp(metrics.get("eval_loss", 0)),
                "epoch": state.epoch
            })

class AdvancedTrainer:
    """Advanced trainer with LoRA and fine-tuning capabilities"""

    def __init__(self, config: AdvancedTrainingConfig):
        self.config = config
        self.model = None
        self.tokenizer = None
        self.trainer = None
        self.setup_logging()

        if not HAS_DEPS:
            raise ImportError("Required dependencies not installed. Please install transformers, peft, bitsandbytes, etc.")

    def setup_logging(self):
        """Setup logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def setup_model_and_tokenizer(self):
        """Setup model and tokenizer"""
        self.logger.info(f"Loading model: {self.config.model_name_or_path}")

        # Setup quantization
        bnb_config = MemoryOptimizer.setup_memory_efficient_training(
            self.model if self.model else None,
            self.config.optimization
        )

        # Load model
        model_kwargs = {
            "device_map": "auto",
            "trust_remote_code": True,
        }

        if bnb_config:
            model_kwargs["quantization_config"] = bnb_config

        self.model = AutoModelForCausalLM.from_pretrained(
            self.config.model_name_or_path,
            **model_kwargs
        )

        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.config.model_name_or_path,
            trust_remote_code=True
        )

        # Set padding token if not present
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        self.logger.info(f"Model loaded: {self.model.__class__.__name__}")

    def setup_lora(self):
        """Setup LoRA adapters"""
        if self.config.training_mode in [TrainingMode.LORA, TrainingMode.QLORA, TrainingMode.DORA]:

            # Get target modules
            if self.config.lora_config.target_modules is None:
                self.config.lora_config.target_modules = MemoryOptimizer.get_target_modules(
                    self.model, "all-linear"
                )

            # Create LoRA config
            lora_config = LoraConfig(
                r=self.config.lora_config.r,
                lora_alpha=self.config.lora_config.lora_alpha,
                lora_dropout=self.config.lora_config.lora_dropout,
                target_modules=self.config.lora_config.target_modules,
                bias=self.config.lora_config.bias,
                task_type=TaskType.CAUSAL_LM,
                use_rslora=self.config.lora_config.use_rslora,
                use_dora=self.config.lora_config.use_dora,
                init_lora_weights=self.config.lora_config.init_lora_weights,
            )

            # Prepare model for k-bit training if using quantization
            if self.config.training_mode == TrainingMode.QLORA:
                self.model = prepare_model_for_kbit_training(self.model)

            # Apply LoRA
            self.model = get_peft_model(self.model, lora_config)

            # Enable trainable parameters
            self.model.print_trainable_parameters()

            self.logger.info(f"LoRA setup completed with r={lora_config.r}")

    def setup_training(self):
        """Setup training arguments and trainer"""
        # Create training arguments
        training_args = TrainingArguments(
            output_dir=self.config.output_dir,
            num_train_epochs=self.config.training_params.num_train_epochs,
            per_device_train_batch_size=self.config.training_params.per_device_train_batch_size,
            per_device_eval_batch_size=self.config.training_params.per_device_eval_batch_size,
            gradient_accumulation_steps=self.config.training_params.gradient_accumulation_steps,
            warmup_steps=self.config.training_params.warmup_steps,
            logging_steps=self.config.training_params.logging_steps,
            save_steps=self.config.training_params.save_steps,
            eval_steps=self.config.training_params.eval_steps,
            save_total_limit=self.config.training_params.save_total_limit,
            learning_rate=self.config.training_params.learning_rate,
            weight_decay=self.config.training_params.weight_decay,
            fp16=self.config.optimization.fp16,
            bf16=self.config.optimization.bf16,
            tf32=self.config.optimization.tf32,
            max_grad_norm=self.config.training_params.max_grad_norm,
            gradient_checkpointing=self.config.optimization.gradient_checkpointing,
            dataloader_drop_last=self.config.training_params.dataloader_drop_last,
            dataloader_num_workers=self.config.training_params.dataloader_num_workers,
            group_by_length=self.config.training_params.group_by_length,
            remove_unused_columns=self.config.training_params.remove_unused_columns,
            load_best_model_at_end=self.config.training_params.load_best_model_at_end,
            metric_for_best_model=self.config.training_params.metric_for_best_model,
            greater_is_better=self.config.training_params.greater_is_better,
            do_eval=self.config.do_eval,
            evaluation_strategy=self.config.evaluation_strategy,
            push_to_hub=self.config.push_to_hub,
            hub_model_id=self.config.hub_model_id,
            hub_token=self.config.hub_token,
            report_to=self.config.report_to,
            run_name=self.config.run_name,
            ddp_find_unused_parameters=self.config.optimization.ddp_find_unused_parameters,
            deepspeed=self.config.optimization.deepspeed_config,
        )

        # Setup callbacks
        callbacks = [CustomCallback(self.config)]

        # Create trainer
        self.trainer = Trainer(
            model=self.model,
            args=training_args,
            callbacks=callbacks,
        )

        self.logger.info("Training setup completed")

    def prepare_dataset(self):
        """Prepare dataset for training"""
        dataset_processor = DatasetProcessor(self.tokenizer, self.config.max_seq_length)

        # Load and process dataset
        dataset = dataset_processor.create_dataset(self.config.dataset_path)

        # Create train/eval split if needed
        if "train" not in dataset.column_names and "validation" not in dataset.column_names:
            # Split dataset
            split_dataset = dataset.train_test_split(test_size=0.1)
            dataset_dict = DatasetDict({
                'train': split_dataset['train'],
                'validation': split_dataset['test']
            })
        else:
            dataset_dict = DatasetDict({'train': dataset})

        self.trainer.train_dataset = dataset_dict['train']
        if self.config.do_eval and 'validation' in dataset_dict:
            self.trainer.eval_dataset = dataset_dict['validation']

        self.logger.info(f"Dataset prepared: {len(dataset_dict['train'])} training samples")
        if 'validation' in dataset_dict:
            self.logger.info(f"Validation dataset: {len(dataset_dict['validation'])} samples")

    def train(self):
        """Start training"""
        self.logger.info("Starting training process")

        # Setup components
        self.setup_model_and_tokenizer()
        self.setup_lora()
        self.setup_training()
        self.prepare_dataset()

        # Initialize wandb if needed
        if self.config.report_to == "wandb" and self.config.run_name:
            wandb.init(project="model-training", name=self.config.run_name)

        # Start training
        result = self.trainer.train(resume_from_checkpoint=self.config.resume_from_checkpoint)

        # Save final model
        self.trainer.save_model()

        # Save training results
        with open(Path(self.config.output_dir) / "training_results.json", "w") as f:
            json.dump({
                "training_mode": self.config.training_mode.value,
                "final_loss": result.training_loss if hasattr(result, 'training_loss') else None,
                "model_path": self.config.model_name_or_path,
                "output_dir": self.config.output_dir,
                "config": self.config.__dict__,
            }, f, indent=2)

        self.logger.info("Training completed successfully")
        return result

    def save_adapter(self, adapter_name: str = "default"):
        """Save LoRA adapter"""
        if self.config.training_mode in [TrainingMode.LORA, TrainingMode.QLORA, TrainingMode.DORA]:
            adapter_path = Path(self.config.output_dir) / f"adapter_{adapter_name}"
            self.model.save_pretrained(adapter_path)
            self.tokenizer.save_pretrained(adapter_path)
            self.logger.info(f"Adapter saved to {adapter_path}")

    def merge_and_save(self):
        """Merge LoRA weights and save full model"""
        if self.config.training_mode in [TrainingMode.LORA, TrainingMode.QLORA, TrainingMode.DORA]:
            # Merge adapter weights
            merged_model = self.model.merge_and_unload()

            # Save merged model
            merged_model.save_pretrained(
                Path(self.config.output_dir) / "merged_model",
                safe_serialization=True
            )
            self.tokenizer.save_pretrained(
                Path(self.config.output_dir) / "merged_model"
            )
            self.logger.info("Merged model saved")

    def evaluate(self, eval_dataset: Optional[Dataset] = None):
        """Evaluate model"""
        if eval_dataset is None and hasattr(self.trainer, 'eval_dataset'):
            eval_dataset = self.trainer.eval_dataset

        if eval_dataset is not None:
            results = self.trainer.evaluate(eval_dataset)
            self.logger.info(f"Evaluation results: {results}")
            return results
        else:
            self.logger.warning("No evaluation dataset available")
            return {}

def create_default_configs():
    """Create default training configurations for common scenarios"""

    # Conversational AI
    conversational_config = AdvancedTrainingConfig(
        model_name_or_path="meta-llama/Llama-2-7b-chat-hf",
        dataset_path="datasets/conversations.json",
        output_dir="outputs/conversational_model",
        training_mode=TrainingMode.LORA,
        lora_config=LoRAConfig(r=16, lora_alpha=32, target_modules=["q_proj", "k_proj", "v_proj", "o_proj"]),
        training_params=TrainingHyperparameters(
            learning_rate=2e-4,
            num_train_epochs=3,
            per_device_train_batch_size=4,
            max_seq_length=2048
        ),
        optimization=OptimizationConfig(
            optimizer_type=OptimizerType.ADAMW,
            scheduler_type=SchedulerType.COSINE,
            gradient_checkpointing=True
        )
    )

    # Code generation
    code_config = AdvancedTrainingConfig(
        model_name_or_path="codellama/CodeLlama-7b-hf",
        dataset_path="datasets/code_dataset.json",
        output_dir="outputs/code_model",
        training_mode=TrainingMode.LORA,
        lora_config=LoRAConfig(r=32, lora_alpha=64, target_modules=["q_proj", "k_proj", "v_proj", "o_proj"]),
        training_params=TrainingHyperparameters(
            learning_rate=1e-4,
            num_train_epochs=5,
            per_device_train_batch_size=2,
            max_seq_length=4096
        ),
        optimization=OptimizationConfig(
            optimizer_type=OptimizerType.ADAMW,
            scheduler_type=SchedulerType.LINEAR,
            gradient_checkpointing=True
        )
    )

    # Instruction following
    instruction_config = AdvancedTrainingConfig(
        model_name_or_path="mistralai/Mistral-7B-v0.1",
        dataset_path="datasets/instructions.json",
        output_dir="outputs/instruction_model",
        training_mode=TrainingMode.QLORA,
        lora_config=LoRAConfig(r=64, lora_alpha=16, target_modules=["q_proj", "k_proj", "v_proj", "o_proj"]),
        training_params=TrainingHyperparameters(
            learning_rate=2e-4,
            num_train_epochs=3,
            per_device_train_batch_size=8,
            max_seq_length=1024
        ),
        optimization=OptimizationConfig(
            optimizer_type=OptimizerType.ADAM_8BIT,
            scheduler_type=SchedulerType.COSINE,
            quantization_type=QuantizationType.NF4,
            gradient_checkpointing=True
        )
    )

    return {
        "conversational": conversational_config,
        "code": code_config,
        "instruction": instruction_config
    }

def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Advanced LoRA and Fine-Tuning Trainer")
    parser.add_argument("--config", type=str, help="Path to configuration file")
    parser.add_argument("--model", type=str, help="Model name or path")
    parser.add_argument("--dataset", type=str, help="Dataset path")
    parser.add_argument("--output", type=str, help="Output directory")
    parser.add_argument("--mode", choices=["lora", "qlora", "full"], default="lora", help="Training mode")
    parser.add_argument("--learning-rate", type=float, default=3e-4, help="Learning rate")
    parser.add_argument("--batch-size", type=int, default=4, help="Batch size")
    parser.add_argument("--epochs", type=int, default=3, help="Number of epochs")
    parser.add_argument("--save-adapter", action="store_true", help="Save LoRA adapter")
    parser.add_argument("--merge-and-save", action="store_true", help="Merge and save full model")
    parser.add_argument("--template", choices=["conversational", "code", "instruction"], help="Use preset configuration")

    args = parser.parse_args()

    # Create trainer
    if args.template:
        configs = create_default_configs()
        config = configs[args.template]
    elif args.config:
        # Load from file
        with open(args.config, 'r') as f:
            config_data = json.load(f)
        config = AdvancedTrainingConfig(**config_data)
    else:
        # Create from command line args
        config = AdvancedTrainingConfig(
            model_name_or_path=args.model,
            dataset_path=args.dataset,
            output_dir=args.output,
            training_mode=TrainingMode(args.mode),
            training_params=TrainingHyperparameters(
                learning_rate=args.learning_rate,
                num_train_epochs=args.epochs,
                per_device_train_batch_size=args.batch_size
            )
        )

    # Train
    trainer = AdvancedTrainer(config)
    result = trainer.train()

    # Save if requested
    if args.save_adapter:
        trainer.save_adapter()

    if args.merge_and_save:
        trainer.merge_and_save()

    print("Training completed successfully!")

if __name__ == "__main__":
    main()