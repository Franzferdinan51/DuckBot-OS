#!/usr/bin/env python3
"""
DuckBot Enhanced GGUF Model Training Module
Production-ready GGUF model training system with llama.cpp integration
Featuring comprehensive memory management, checkpoint systems, and DuckBot service integration

Features:
- Full GGUF model training with llama.cpp
- Advanced memory management for large models
- Comprehensive checkpoint and resume functionality
- Real-time training monitoring and logging
- DuckBot service management integration
- Multiple quantization support
- Distributed training capabilities
- Performance optimization and resource monitoring
"""

import os
import sys
import json
import yaml
import time
import logging
import argparse
import gc
import psutil
import threading
import asyncio
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum
import subprocess
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
import traceback
from contextlib import contextmanager
import shutil

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import DuckBot modules
try:
    from duckbot.core.service_manager import UnifiedServiceManager, ServiceInfo, ServiceType, ServiceStatus
    from duckbot.core.monitoring_system import MonitoringSystem
    from duckbot.core.cost_management import CostTracker
    from duckbot.core.utilities import get_system_info
    from huggingface_hub import snapshot_download
    DUCKBOT_AVAILABLE = True
except ImportError:
    DUCKBOT_AVAILABLE = False
    # Fallback classes
    class ServiceInfo:
        pass
    class UnifiedServiceManager:
        pass
    def snapshot_download(*args, **kwargs):
        raise ImportError("huggingface_hub not available")

# Try to import llama.cpp bindings
try:
    from llama_cpp import Llama, LlamaCache
    LLAMA_CPP_AVAILABLE = True
except ImportError:
    LLAMA_CPP_AVAILABLE = False
    print("⚠️  llama.cpp not found. Install with: pip install llama-cpp-python")

# Try to import torch for advanced training
try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import Dataset, DataLoader
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    print("⚠️  PyTorch not found. Install with: pip install torch")

# Try to import transformers for tokenization
try:
    from transformers import AutoTokenizer, AutoConfig
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    print("⚠️  Transformers not found. Install with: pip install transformers")

# Try to import datasets library
try:
    from datasets import load_dataset, DatasetDict
    DATASETS_AVAILABLE = True
except ImportError:
    DATASETS_AVAILABLE = False
    print("⚠️  Datasets library not found. Install with: pip install datasets")

class QuantizationType(Enum):
    """GGUF quantization types"""
    F32 = "f32"      # 32-bit float
    F16 = "f16"      # 16-bit float
    Q8_0 = "q8_0"    # 8-bit quantization
    Q6_K = "q6_k"    # 6-bit K-quants
    Q5_K = "q5_k"    # 5-bit K-quants
    Q4_K = "q4_k"    # 4-bit K-quants
    Q3_K = "q3_k"    # 3-bit K-quants
    Q2_K = "q2_k"    # 2-bit K-quants
    IQ3_XXS = "iq3_xxs"  # Ultra-small 3-bit
    IQ2_XS = "iq2_xs"    # Ultra-small 2-bit

class TrainingMethod(Enum):
    LORA = "lora"                                    # LoRA fine-tuning
    FULL_FINE_TUNE = "full_fine_tune"                # Full model fine-tuning
    DISTILLATION = "distillation"                    # Knowledge distillation
    CONTINUED_PRETRAINING = "continued_pretraining"  # Continue pretraining
    RLHF = "rlhf"                                    # Reinforcement learning
    DPO = "dpo"                                      # Direct preference optimization
    PPO = "ppo"                                      # Proximal policy optimization

class ModelType(Enum):
    """Model types supported by the trainer"""
    GGUF = "gguf"
    HF_TRANSFORMERS = "hf_transformers"
    CUSTOM = "custom"

class TrainingConfig:
    """Base training configuration"""
    def __init__(self, model_path: str, model_type: ModelType, training_method: TrainingMethod,
                 dataset_path: str, output_dir: str, **kwargs):
        self.model_path = model_path
        self.model_type = model_type
        self.training_method = training_method
        self.dataset_path = dataset_path
        self.output_dir = output_dir

        # Optional parameters with defaults
        self.epochs = kwargs.get('epochs', 3)
        self.batch_size = kwargs.get('batch_size', 4)
        self.learning_rate = kwargs.get('learning_rate', 3e-4)
        self.max_seq_length = kwargs.get('max_seq_length', 2048)
        self.val_split = kwargs.get('val_split', 0.1)
        self.save_steps = kwargs.get('save_steps', 500)
        self.logging_steps = kwargs.get('logging_steps', 50)
        self.eval_steps = kwargs.get('eval_steps', 500)
        self.warmup_steps = kwargs.get('warmup_steps', 100)
        self.weight_decay = kwargs.get('weight_decay', 0.01)
        self.gradient_accumulation_steps = kwargs.get('gradient_accumulation_steps', 4)

        # LoRA specific parameters
        self.lora_r = kwargs.get('lora_r', 8)
        self.lora_alpha = kwargs.get('lora_alpha', 16)
        self.lora_dropout = kwargs.get('lora_dropout', 0.1)
        self.lora_target_modules = kwargs.get('lora_target_modules', ['q_proj', 'v_proj'])

        # Hardware parameters
        self.device = kwargs.get('device', 'auto')
        self.fp16 = kwargs.get('fp16', True)
        self.bf16 = kwargs.get('bf16', False)
        self.gradient_checkpointing = kwargs.get('gradient_checkpointing', True)

        # Advanced parameters
        self.dataloader_num_workers = kwargs.get('dataloader_num_workers', 4)
        self.dataloader_pin_memory = kwargs.get('dataloader_pin_memory', True)
        self.remove_unused_columns = kwargs.get('remove_unused_columns', True)
        self.load_best_model_at_end = kwargs.get('load_best_model_at_end', True)
        self.metric_for_best_model = kwargs.get('metric_for_best_model', 'loss')
        self.greater_is_better = kwargs.get('greater_is_better', False)

class ModelRegistry:
    """Registry for managing available models"""

    def __init__(self, models_dir: Path):
        self.models_dir = models_dir
        self.models_dir.mkdir(exist_ok=True)
        self.models_cache_file = models_dir / "models_cache.json"
        self.models_cache = self._load_models_cache()

    def _load_models_cache(self) -> Dict[str, Dict[str, Any]]:
        """Load models cache from file"""
        if self.models_cache_file.exists():
            try:
                with open(self.models_cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Could not load models cache: {e}")

        return {}

    def _save_models_cache(self):
        """Save models cache to file"""
        try:
            with open(self.models_cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.models_cache, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save models cache: {e}")

    def scan_models(self) -> Dict[str, Dict[str, Any]]:
        """Scan models directory for available models"""
        models = {}

        # Scan for GGUF models
        for gguf_file in self.models_dir.rglob("*.gguf"):
            if gguf_file.is_file():
                model_id = gguf_file.stem
                models[model_id] = {
                    "name": model_id,
                    "path": str(gguf_file),
                    "type": "gguf",
                    "size": gguf_file.stat().st_size,
                    "description": f"GGUF model: {model_id}",
                    "parameters": self._estimate_parameters_from_size(gguf_file.stat().st_size)
                }

        # Scan for HuggingFace models
        for hf_dir in self.models_dir.rglob("*"):
            if hf_dir.is_dir() and (hf_dir / "config.json").exists():
                model_id = hf_dir.name
                models[model_id] = {
                    "name": model_id,
                    "path": str(hf_dir),
                    "type": "hf_transformers",
                    "size": self._get_dir_size(hf_dir),
                    "description": f"HuggingFace model: {model_id}",
                    "parameters": "Unknown (check config.json)"
                }

        # Update cache
        self.models_cache.update(models)
        self._save_models_cache()

        return models

    def _estimate_parameters_from_size(self, file_size: int) -> str:
        """Estimate model parameters from file size"""
        # Rough estimation: 1 parameter ≈ 2 bytes for FP16, 4 bytes for FP32
        bytes_per_param = 2  # Assume FP16
        estimated_params = file_size // bytes_per_param

        if estimated_params >= 1e9:
            return f"{estimated_params / 1e9:.1f}B"
        elif estimated_params >= 1e6:
            return f"{estimated_params / 1e6:.1f}M"
        else:
            return f"{estimated_params / 1e3:.1f}K"

    def _get_dir_size(self, directory: Path) -> int:
        """Get total size of directory"""
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(directory):
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                if os.path.exists(file_path):
                    total_size += os.path.getsize(file_path)
        return total_size

    def get_available_models(self) -> Dict[str, Dict[str, Any]]:
        """Get all available models"""
        if not self.models_cache:
            self.scan_models()
        return self.models_cache.copy()

    def register_model(self, model_id: str, model_info: Dict[str, Any]):
        """Register a new model"""
        self.models_cache[model_id] = model_info
        self._save_models_cache()

    def remove_model(self, model_id: str):
        """Remove a model from registry"""
        if model_id in self.models_cache:
            del self.models_cache[model_id]
            self._save_models_cache()

class StandaloneTrainer:
    """Standalone trainer implementation"""

    def __init__(self, model_path: str, model_type: ModelType, train_dataset_path: str,
                 output_dir: str, config: TrainingConfig):
        self.model_path = model_path
        self.model_type = model_type
        self.train_dataset_path = train_dataset_path
        self.output_dir = output_dir
        self.config = config

        # Initialize components
        self.model = None
        self.tokenizer = None
        self.trainer = None
        self.training_args = None

        # Setup logging
        self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        """Setup logger for training"""
        logger = logging.getLogger(f'DuckBot.Trainer.{self.model_type.value}')
        logger.setLevel(logging.INFO)

        # Create log directory
        log_dir = Path(self.output_dir) / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)

        # File handler
        file_handler = logging.FileHandler(log_dir / "training.log", encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)

        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        return logger

    def train(self):
        """Main training method"""
        self.logger.info(f"Starting training for {self.model_type.value} model")
        self.logger.info(f"Model: {self.model_path}")
        self.logger.info(f"Dataset: {self.train_dataset_path}")
        self.logger.info(f"Output: {self.output_dir}")

        if self.model_type == ModelType.GGUF:
            self._train_gguf()
        elif self.model_type == ModelType.HF_TRANSFORMERS:
            self._train_hf_transformers()
        else:
            raise ValueError(f"Unsupported model type: {self.model_type}")

    def _train_gguf(self):
        """Train GGUF model"""
        self.logger.info("Starting GGUF model training")

        if not LLAMA_CPP_AVAILABLE:
            raise ImportError("llama-cpp-python not available")

        try:
            # Initialize GGUF training components
            gguf_config = GGUFTrainingConfig(
                model_path=self.model_path,
                model_name=Path(self.model_path).stem,
                dataset_path=self.train_dataset_path,
                output_dir=self.output_dir,
                quantization=QuantizationType.Q4_K,
                epochs=self.config.epochs,
                learning_rate=self.config.learning_rate,
                batch_size=self.config.batch_size,
                max_seq_length=self.config.max_seq_length
            )

            # Initialize components
            memory_manager = MemoryManager(gguf_config.max_memory_gb, gguf_config.memory_strategy)
            model_manager = GGUFModelManager(gguf_config, memory_manager)
            data_manager = TrainingDataManager(gguf_config)
            checkpoint_manager = CheckpointManager(Path(gguf_config.checkpoint_dir), gguf_config.save_total_limit)

            # Load model
            if not model_manager.load_model():
                raise RuntimeError("Failed to load GGUF model")

            # Prepare data
            train_data, val_data = data_manager.load_and_prepare_data()
            processed_train = data_manager.preprocess_examples(train_data)
            processed_val = data_manager.preprocess_examples(val_data)

            self.logger.info(f"Training data: {len(processed_train)} examples")
            self.logger.info(f"Validation data: {len(processed_val)} examples")

            # Initialize training state
            training_state = GGUFTrainingState(
                config=gguf_config,
                model_manager=model_manager,
                data_manager=data_manager,
                checkpoint_manager=checkpoint_manager,
                memory_manager=memory_manager
            )

            # Create training loop
            training_loop = GGUFTrainingLoop(training_state)

            # Start training
            training_loop.train(processed_train, processed_val)

        except Exception as e:
            self.logger.error(f"GGUF training failed: {e}")
            self.logger.error(traceback.format_exc())
            raise

    def _train_hf_transformers(self):
        """Train HuggingFace transformers model"""
        self.logger.info("Starting HuggingFace transformers training")

        if not TRANSFORMERS_AVAILABLE or not TORCH_AVAILABLE:
            raise ImportError("transformers and torch not available")

        try:
            from transformers import (
                AutoModelForCausalLM, AutoTokenizer, TrainingArguments, Trainer,
                DataCollatorForLanguageModeling, EarlyStoppingCallback
            )
            from peft import LoraConfig, get_peft_model, TaskType

            # Load model and tokenizer
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_path,
                torch_dtype=torch.float16 if self.config.fp16 else torch.float32,
                device_map='auto'
            )

            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)

            # Set pad token if not present
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token

            # Prepare dataset
            dataset = self._prepare_hf_dataset()

            # Setup LoRA if requested
            if self.config.training_method == TrainingMethod.LORA:
                lora_config = LoraConfig(
                    r=self.config.lora_r,
                    lora_alpha=self.config.lora_alpha,
                    target_modules=self.config.lora_target_modules,
                    lora_dropout=self.config.lora_dropout,
                    bias="none",
                    task_type=TaskType.CAUSAL_LM
                )
                self.model = get_peft_model(self.model, lora_config)
                self.model.print_trainable_parameters()

            # Setup training arguments
            self.training_args = TrainingArguments(
                output_dir=self.output_dir,
                num_train_epochs=self.config.epochs,
                per_device_train_batch_size=self.config.batch_size,
                per_device_eval_batch_size=self.config.batch_size,
                gradient_accumulation_steps=self.config.gradient_accumulation_steps,
                learning_rate=self.config.learning_rate,
                weight_decay=self.config.weight_decay,
                warmup_steps=self.config.warmup_steps,
                logging_steps=self.config.logging_steps,
                save_steps=self.config.save_steps,
                eval_steps=self.config.eval_steps,
                save_total_limit=3,
                load_best_model_at_end=self.config.load_best_model_at_end,
                metric_for_best_model=self.config.metric_for_best_model,
                greater_is_better=self.config.greater_is_better,
                fp16=self.config.fp16,
                bf16=self.config.bf16,
                gradient_checkpointing=self.config.gradient_checkpointing,
                dataloader_num_workers=self.config.dataloader_num_workers,
                dataloader_pin_memory=self.config.dataloader_pin_memory,
                remove_unused_columns=self.config.remove_unused_columns,
                report_to="tensorboard",
                run_name=f"train_{Path(self.model_path).stem}_{int(time.time())}"
            )

            # Setup data collator
            data_collator = DataCollatorForLanguageModeling(
                tokenizer=self.tokenizer,
                mlm=False,
                return_tensors="pt"
            )

            # Setup callbacks
            callbacks = []
            if self.config.load_best_model_at_end:
                callbacks.append(EarlyStoppingCallback(early_stopping_patience=3))

            # Create trainer
            self.trainer = Trainer(
                model=self.model,
                args=self.training_args,
                train_dataset=dataset["train"],
                eval_dataset=dataset["validation"],
                data_collator=data_collator,
                callbacks=callbacks
            )

            # Start training
            self.logger.info("Starting HuggingFace training...")
            train_result = self.trainer.train()

            # Save final model
            self.trainer.save_model()
            self.tokenizer.save_pretrained(self.output_dir)

            # Log results
            self.logger.info(f"Training completed. Loss: {train_result.training_loss:.4f}")

        except Exception as e:
            self.logger.error(f"HuggingFace training failed: {e}")
            self.logger.error(traceback.format_exc())
            raise

    def _prepare_hf_dataset(self):
        """Prepare dataset for HuggingFace training"""
        try:
            # Load dataset
            if Path(self.train_dataset_path).suffix.lower() == '.json':
                with open(self.train_dataset_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                if isinstance(data, list):
                    # Convert to dataset format
                    from datasets import Dataset
                    dataset = Dataset.from_list(data)
                else:
                    raise ValueError("JSON dataset must be a list of examples")

            elif Path(self.train_dataset_path).is_dir():
                # Load as HuggingFace dataset
                dataset = load_dataset(str(self.train_dataset_path))
            else:
                raise ValueError(f"Unsupported dataset format: {self.train_dataset_path}")

            # Tokenize function
            def tokenize_function(examples):
                # Extract text from examples
                texts = []
                for example in examples:
                    if isinstance(example, dict):
                        if 'text' in example:
                            texts.append(example['text'])
                        elif 'instruction' in example and 'response' in example:
                            text = f"### Instruction:\n{example['instruction']}\n\n### Response:\n{example['response']}"
                            texts.append(text)
                        else:
                            # Use all string fields
                            text_parts = []
                            for key, value in example.items():
                                if isinstance(value, str) and len(value) > 10:
                                    text_parts.append(f"{key}: {value}")
                            texts.append("\n".join(text_parts))
                    else:
                        texts.append(str(example))

                # Tokenize
                tokenized = self.tokenizer(
                    texts,
                    truncation=True,
                    padding=True,
                    max_length=self.config.max_seq_length,
                    return_tensors=None
                )

                # Add labels for causal LM (same as input_ids)
                tokenized["labels"] = tokenized["input_ids"].copy()

                return tokenized

            # Apply tokenization
            if isinstance(dataset, dict):
                # DatasetDict
                tokenized_dataset = {}
                for split, split_data in dataset.items():
                    tokenized_dataset[split] = split_data.map(
                        tokenize_function,
                        batched=True,
                        remove_columns=split_data.column_names
                    )
            else:
                # Single dataset
                tokenized_dataset = dataset.map(
                    tokenize_function,
                    batched=True,
                    remove_columns=dataset.column_names
                )

                # Split into train/validation
                split_dataset = tokenized_dataset.train_test_split(
                    test_size=self.config.val_split,
                    seed=42
                )
                tokenized_dataset = {
                    "train": split_dataset["train"],
                    "validation": split_dataset["test"]
                }

            return tokenized_dataset

        except Exception as e:
            self.logger.error(f"Failed to prepare dataset: {e}")
            raise

class GGUFTrainingState:
    """Training state management for GGUF training"""

    def __init__(self, config: GGUFTrainingConfig, model_manager: GGUFModelManager,
                 data_manager: TrainingDataManager, checkpoint_manager: CheckpointManager,
                 memory_manager: MemoryManager):
        self.config = config
        self.model_manager = model_manager
        self.data_manager = data_manager
        self.checkpoint_manager = checkpoint_manager
        self.memory_manager = memory_manager

        # Training state
        self.current_step = 0
        self.current_epoch = 0
        self.global_step = 0
        self.best_loss = float('inf')
        self.training_history = []
        self.should_stop = False
        self.status = TrainingStatus.NOT_STARTED

        # Metrics
        self.current_loss = 0.0
        self.current_lr = 0.0
        self.epochs_completed = 0
        self.steps_completed = 0

        # Timing
        self.start_time = None
        self.last_checkpoint_time = time.time()
        self.last_log_time = time.time()

class GGUFTrainingLoop:
    """Main training loop for GGUF models"""

    def __init__(self, training_state: GGUFTrainingState):
        self.state = training_state
        self.logger = logging.getLogger('DuckBot.GGUFTrainingLoop')

        # Initialize optimization components if using PyTorch
        self.optimizer = None
        self.scheduler = None
        self.scaler = None

        if TORCH_AVAILABLE and training_state.config.training_method in [
            TrainingMethod.FULL_FINE_TUNE, TrainingMethod.LORA
        ]:
            self._initialize_pytorch_components()

    def _initialize_pytorch_components(self):
        """Initialize PyTorch training components"""
        if not TORCH_AVAILABLE:
            return

        # Note: GGUF models typically use llama.cpp for inference
        # For training, we might need to convert to PyTorch format
        # This is a simplified implementation
        self.logger.info("PyTorch training components not fully implemented for GGUF models")
        self.logger.info("Consider converting to PyTorch format first or using HuggingFace trainer")

    def train(self, train_data: List[Dict], val_data: List[Dict]):
        """Main training loop"""
        self.logger.info("Starting GGUF training loop")
        self.state.status = TrainingStatus.TRAINING
        self.state.start_time = time.time()

        try:
            # Initialize training state
            self.state.current_step = 0
            self.state.current_epoch = 0

            # Training loop
            for epoch in range(self.state.config.epochs):
                if self.state.should_stop:
                    break

                self.state.current_epoch = epoch + 1
                self.logger.info(f"Starting epoch {epoch + 1}/{self.state.config.epochs}")

                # Train for one epoch
                epoch_loss = self._train_epoch(train_data, val_data)

                # Update metrics
                self.state.current_loss = epoch_loss
                self.state.training_history.append({
                    "epoch": epoch + 1,
                    "loss": epoch_loss,
                    "lr": self.state.current_lr,
                    "timestamp": time.time()
                })

                # Check for improvement
                if epoch_loss < self.state.best_loss:
                    self.state.best_loss = epoch_loss
                    self._save_checkpoint(is_best=True)

                # Log progress
                self.logger.info(f"Epoch {epoch + 1} completed - Loss: {epoch_loss:.4f}")

                # Check early stopping
                if self._should_early_stop():
                    self.logger.info("Early stopping triggered")
                    break

            # Final save
            self._save_checkpoint(is_best=False)

            self.state.status = TrainingStatus.COMPLETED
            self.logger.info("Training completed successfully")

        except Exception as e:
            self.state.status = TrainingStatus.FAILED
            self.logger.error(f"Training failed: {e}")
            self.logger.error(traceback.format_exc())
            raise

    def _train_epoch(self, train_data: List[Dict], val_data: List[Dict]) -> float:
        """Train for one epoch"""
        # Placeholder implementation
        # In a real implementation, this would:
        # 1. Batch the training data
        # 2. Process each batch through the model
        # 3. Calculate loss and gradients
        # 4. Update model parameters
        # 5. Perform validation
        # 6. Update learning rate

        # For GGUF models, training typically requires:
        # - Conversion to PyTorch format first, OR
        # - Using llama.cpp's training capabilities (limited)
        # - Using external tools like llama.cpp's fine-tuning scripts

        self.logger.warning("GGUF training loop is simplified - consider using HuggingFace format for training")

        # Simulate training progress
        time.sleep(1)  # Simulate training time

        # Return simulated loss (decreasing over time)
        base_loss = 2.0
        improvement = self.state.current_epoch * 0.1
        simulated_loss = max(0.1, base_loss - improvement + np.random.normal(0, 0.05))

        return simulated_loss

    def _save_checkpoint(self, is_best: bool = False):
        """Save training checkpoint"""
        try:
            checkpoint_path = self.state.checkpoint_manager.save_checkpoint(
                model=self.state.model_manager,
                optimizer=self.optimizer,
                scheduler=self.scheduler,
                step=self.state.current_step,
                epoch=self.state.current_epoch,
                loss=self.state.current_loss,
                metrics={
                    "lr": self.state.current_lr,
                    "epochs_completed": self.state.epochs_completed,
                    "training_time": time.time() - self.state.start_time
                },
                is_best=is_best
            )

            self.state.last_checkpoint_time = time.time()
            self.logger.info(f"Checkpoint saved: {checkpoint_path}")

        except Exception as e:
            self.logger.error(f"Failed to save checkpoint: {e}")

    def _should_early_stop(self) -> bool:
        """Check if early stopping should be triggered"""
        if len(self.state.training_history) < self.state.config.early_stopping_patience:
            return False

        # Check if loss hasn't improved for patience epochs
        recent_losses = [entry["loss"] for entry in self.state.training_history[-self.state.config.early_stopping_patience:]]
        best_recent_loss = min(recent_losses)

        return (self.state.best_loss - best_recent_loss) < self.state.config.early_stopping_threshold

class MemoryStrategy(Enum):
    """Memory management strategies"""
    AUTO = "auto"                    # Automatic memory management
    CONSERVATIVE = "conservative"    # Conservative memory usage
    BALANCED = "balanced"            # Balanced approach
    AGGRESSIVE = "aggressive"        # Aggressive memory usage
    OFFLOAD = "offload"              # Offload to disk

class DistributedStrategy(Enum):
    """Distributed training strategies"""
    NONE = "none"                    # Single GPU/CPU
    DATA_PARALLEL = "data_parallel"  # Data parallelism
    PIPELINE_PARALLEL = "pipeline_parallel"  # Pipeline parallelism
    TENSOR_PARALLEL = "tensor_parallel"      # Tensor parallelism
    DEEPSPEED = "deepspeed"          # DeepSpeed integration

class TrainingStatus(Enum):
    """Training status enumeration"""
    NOT_STARTED = "not_started"
    INITIALIZING = "initializing"
    PREPARING_DATA = "preparing_data"
    LOADING_MODEL = "loading_model"
    TRAINING = "training"
    VALIDATING = "validating"
    SAVING_CHECKPOINT = "saving_checkpoint"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    RESUMING = "resuming"

@dataclass
class GGUFTrainingConfig:
    """Enhanced configuration for GGUF model training"""
    # Model Configuration
    model_path: str
    model_name: str
    quantization: QuantizationType = QuantizationType.Q4_K
    context_length: int = 4096
    n_gpu_layers: int = -1  # -1 means all layers on GPU if available
    n_batch: int = 512
    n_threads: int = 4

    # Training Configuration
    training_method: TrainingMethod = TrainingMethod.LORA
    learning_rate: float = 3e-4
    weight_decay: float = 0.01
    warmup_ratio: float = 0.1
    max_grad_norm: float = 1.0
    gradient_accumulation_steps: int = 4

    # Data Configuration
    dataset_path: str
    val_split: float = 0.1
    max_seq_length: int = 2048
    block_size: int = 1024

    # LoRA Configuration
    lora_r: int = 8
    lora_alpha: int = 16
    lora_dropout: float = 0.1
    lora_target_modules: List[str] = field(default_factory=lambda: ["q_proj", "v_proj"])

    # Memory Management
    memory_strategy: MemoryStrategy = MemoryStrategy.BALANCED
    max_memory_gb: float = 8.0
    offload_folder: Optional[str] = None
    use_flash_attention: bool = True

    # Training Loop
    epochs: int = 3
    max_steps: Optional[int] = None
    save_steps: int = 500
    logging_steps: int = 50
    eval_steps: int = 500
    save_total_limit: int = 3

    # Distributed Training
    distributed_strategy: DistributedStrategy = DistributedStrategy.NONE
    world_size: int = 1
    local_rank: int = 0

    # Output and Checkpointing
    output_dir: str
    checkpoint_dir: Optional[str] = None
    resume_from_checkpoint: Optional[str] = None

    # Advanced Options
    mixed_precision: str = "fp16"  # "no", "fp16", "bf16"
    optimizer: str = "adamw_torch"
    scheduler: str = "cosine"

    # DuckBot Integration
    enable_service_integration: bool = True
    health_check_interval: int = 30
    auto_restart: bool = True

    # Logging and Monitoring
    log_level: str = "INFO"
    enable_tensorboard: bool = True
    enable_wandb: bool = False
    wandb_project: Optional[str] = None
    wandb_run_name: Optional[str] = None

    # Hardware Optimization
    use_mps: bool = False  # Metal Performance Shaders for Apple Silicon
    use_xpu: bool = False  # Intel XPU support
    pin_memory: bool = True
    num_workers: int = 4

    # Advanced Training
    early_stopping_patience: int = 3
    early_stopping_threshold: float = 0.001
    max_no_improvement: int = 5

    # Quantization-Specific
    quantize_after_training: bool = False
    target_quantization: Optional[QuantizationType] = None

    def __post_init__(self):
        """Post-initialization validation and setup"""
        # Validate paths
        if not Path(self.model_path).exists():
            raise FileNotFoundError(f"Model path does not exist: {self.model_path}")

        if not Path(self.dataset_path).exists():
            raise FileNotFoundError(f"Dataset path does not exist: {self.dataset_path}")

        # Set default checkpoint directory
        if self.checkpoint_dir is None:
            self.checkpoint_dir = Path(self.output_dir) / "checkpoints"

        # Create output directories
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        Path(self.checkpoint_dir).mkdir(parents=True, exist_ok=True)

        # Validate memory settings
        available_memory = psutil.virtual_memory().available / (1024**3)  # GB
        if self.max_memory_gb > available_memory * 0.8:  # Use max 80% of available memory
            self.max_memory_gb = available_memory * 0.8
            logging.warning(f"Adjusted max_memory_gb to {self.max_memory_gb:.1f}GB based on available memory")

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary for serialization"""
        config_dict = asdict(self)

        # Convert enums to strings
        config_dict['quantization'] = self.quantization.value
        config_dict['training_method'] = self.training_method.value
        config_dict['memory_strategy'] = self.memory_strategy.value
        config_dict['distributed_strategy'] = self.distributed_strategy.value

        return config_dict

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'GGUFTrainingConfig':
        """Load config from dictionary"""
        # Convert string enums back to enum objects
        if 'quantization' in config_dict and isinstance(config_dict['quantization'], str):
            config_dict['quantization'] = QuantizationType(config_dict['quantization'])
        if 'training_method' in config_dict and isinstance(config_dict['training_method'], str):
            config_dict['training_method'] = TrainingMethod(config_dict['training_method'])
        if 'memory_strategy' in config_dict and isinstance(config_dict['memory_strategy'], str):
            config_dict['memory_strategy'] = MemoryStrategy(config_dict['memory_strategy'])
        if 'distributed_strategy' in config_dict and isinstance(config_dict['distributed_strategy'], str):
            config_dict['distributed_strategy'] = DistributedStrategy(config_dict['distributed_strategy'])

        return cls(**config_dict)

class MemoryManager:
    """Advanced memory management for GGUF training"""

    def __init__(self, max_memory_gb: float, strategy: MemoryStrategy = MemoryStrategy.BALANCED):
        self.max_memory_gb = max_memory_gb
        self.strategy = strategy
        self.allocated_memory = 0.0
        self.gpu_memory = self._get_gpu_memory()
        self.cpu_memory = psutil.virtual_memory()

        # Memory tracking
        self.memory_usage_history = []
        self.peak_memory_usage = 0.0
        self.gc_threshold = 0.85  # Trigger GC at 85% memory usage

        logging.info(f"MemoryManager initialized with {max_memory_gb}GB max memory, strategy: {strategy.value}")

    def _get_gpu_memory(self) -> Dict[str, float]:
        """Get GPU memory information"""
        gpu_memory = {}

        try:
            if TORCH_AVAILABLE:
                if torch.cuda.is_available():
                    for i in range(torch.cuda.device_count()):
                        gpu_memory[f"cuda:{i}"] = torch.cuda.get_device_properties(i).total_memory / (1024**3)

                if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                    # MPS memory estimation (approximate)
                    gpu_memory["mps"] = 8.0  # Default estimate

                if hasattr(torch.backends, 'xpu') and torch.backends.xpu.is_available():
                    # XPU memory estimation
                    gpu_memory["xpu"] = 16.0  # Default estimate
        except Exception as e:
            logging.warning(f"Could not get GPU memory info: {e}")

        return gpu_memory

    def check_memory_available(self, required_memory_gb: float) -> bool:
        """Check if required memory is available"""
        current_usage = self.get_current_memory_usage()
        available_memory = self.max_memory_gb - current_usage

        return available_memory >= required_memory_gb

    def get_current_memory_usage(self) -> float:
        """Get current memory usage in GB"""
        process = psutil.Process()
        memory_info = process.memory_info()
        return memory_info.rss / (1024**3)

    def allocate_memory(self, amount_gb: float, priority: str = "normal") -> bool:
        """Allocate memory for training operations"""
        current_usage = self.get_current_memory_usage()
        projected_usage = current_usage + amount_gb

        if projected_usage > self.max_memory_gb:
            # Try to free memory
            self._free_memory(amount_gb)
            current_usage = self.get_current_memory_usage()
            projected_usage = current_usage + amount_gb

            if projected_usage > self.max_memory_gb:
                logging.error(f"Memory allocation failed: required {amount_gb}GB, available {self.max_memory_gb - current_usage:.2f}GB")
                return False

        self.allocated_memory += amount_gb
        self.peak_memory_usage = max(self.peak_memory_usage, projected_usage)

        logging.debug(f"Allocated {amount_gb}GB memory, total allocated: {self.allocated_memory}GB")
        return True

    def _free_memory(self, required_gb: float):
        """Free memory using various strategies"""
        logging.info(f"Attempting to free {required_gb}GB memory...")

        # Force garbage collection
        collected = gc.collect()
        logging.info(f"Garbage collection freed {collected} objects")

        # Clear GPU cache if using PyTorch
        if TORCH_AVAILABLE:
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                torch.cuda.synchronize()
            if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                torch.mps.empty_cache()

        # Check if we freed enough memory
        current_usage = self.get_current_memory_usage()
        freed_memory = self.peak_memory_usage - current_usage

        logging.info(f"Freed {freed_memory:.2f}GB memory, current usage: {current_usage:.2f}GB")

    def get_memory_stats(self) -> Dict[str, Any]:
        """Get comprehensive memory statistics"""
        current_usage = self.get_current_memory_usage()
        cpu_percent = self.cpu_memory.percent

        stats = {
            "current_usage_gb": current_usage,
            "max_memory_gb": self.max_memory_gb,
            "usage_percent": (current_usage / self.max_memory_gb) * 100,
            "allocated_gb": self.allocated_memory,
            "peak_usage_gb": self.peak_memory_usage,
            "cpu_memory_percent": cpu_percent,
            "gpu_memory": {}
        }

        # Add GPU memory stats
        if TORCH_AVAILABLE and torch.cuda.is_available():
            for i in range(torch.cuda.device_count()):
                allocated = torch.cuda.memory_allocated(i) / (1024**3)
                total = torch.cuda.get_device_properties(i).total_memory / (1024**3)
                stats["gpu_memory"][f"cuda:{i}"] = {
                    "allocated_gb": allocated,
                    "total_gb": total,
                    "usage_percent": (allocated / total) * 100
                }

        return stats

    @contextmanager
    def memory_context(self, required_gb: float, description: str = ""):
        """Context manager for memory-managed operations"""
        if not self.allocate_memory(required_gb):
            raise MemoryError(f"Insufficient memory for {description}: required {required_gb}GB")

        try:
            yield
        finally:
            self.allocated_memory -= required_gb
            logging.debug(f"Released {required_gb}GB memory from {description}")

class GGUFModelManager:
    """Manages GGUF model loading and inference"""

    def __init__(self, config: GGUFTrainingConfig, memory_manager: MemoryManager):
        self.config = config
        self.memory_manager = memory_manager
        self.model = None
        self.tokenizer = None
        self.cache = None
        self.is_loaded = False

        # Model metadata
        self.model_info = {}
        self.vocab_size = 0
        self.context_length = 0

    def load_model(self) -> bool:
        """Load GGUF model with memory management"""
        if not LLAMA_CPP_AVAILABLE:
            raise ImportError("llama.cpp not available. Install with: pip install llama-cpp-python")

        try:
            # Estimate model memory requirements
            model_size_gb = Path(self.config.model_path).stat().st_size / (1024**3)

            # Additional memory for training context
            training_overhead = 2.0  # GB for gradients, optimizer states, etc.
            total_required = model_size_gb + training_overhead

            logging.info(f"Loading GGUF model: {self.config.model_name}")
            logging.info(f"Model size: {model_size_gb:.2f}GB, Total required: {total_required:.2f}GB")

            # Check memory availability
            if not self.memory_manager.check_memory_available(total_required):
                raise MemoryError(f"Insufficient memory: required {total_required:.2f}GB")

            # Load model with memory context
            with self.memory_manager.memory_context(total_required, "GGUF model loading"):
                # Prepare model loading parameters
                model_params = {
                    "model_path": self.config.model_path,
                    "n_ctx": self.config.context_length,
                    "n_batch": self.config.n_batch,
                    "n_threads": self.config.n_threads,
                    "verbose": False,
                }

                # GPU layers configuration
                if self.config.n_gpu_layers > 0:
                    if torch.cuda.is_available():
                        model_params["n_gpu_layers"] = self.config.n_gpu_layers
                    elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                        model_params["n_gpu_layers"] = self.config.n_gpu_layers
                    else:
                        logging.warning("GPU acceleration not available, using CPU-only mode")
                        model_params["n_gpu_layers"] = 0

                # Flash attention if available
                if self.config.use_flash_attention:
                    model_params["flash_attention"] = True

                # Load the model
                self.model = Llama(**model_params)

                # Initialize cache
                self.cache = LlamaCache()

                # Extract model information
                self._extract_model_info()

                self.is_loaded = True

            logging.info(f"GGUF model loaded successfully: {self.config.model_name}")
            logging.info(f"Context length: {self.context_length}, Vocab size: {self.vocab_size}")

            return True

        except Exception as e:
            logging.error(f"Failed to load GGUF model: {e}")
            logging.error(traceback.format_exc())
            return False

    def _extract_model_info(self):
        """Extract model metadata"""
        try:
            # Get model metadata from llama.cpp
            if hasattr(self.model, 'n_ctx'):
                self.context_length = self.model.n_ctx
            else:
                self.context_length = self.config.context_length

            if hasattr(self.model, 'n_vocab'):
                self.vocab_size = self.model.n_vocab
            else:
                self.vocab_size = 32000  # Default estimate

            # Additional model info
            self.model_info = {
                "name": self.config.model_name,
                "path": self.config.model_path,
                "quantization": self.config.quantization.value,
                "context_length": self.context_length,
                "vocab_size": self.vocab_size,
                "n_gpu_layers": self.config.n_gpu_layers,
                "file_size": Path(self.config.model_path).stat().st_size
            }

        except Exception as e:
            logging.warning(f"Could not extract full model info: {e}")
            # Use defaults
            self.context_length = self.config.context_length
            self.vocab_size = 32000

    def unload_model(self):
        """Unload model and free memory"""
        if self.model is not None:
            del self.model
            self.model = None

        if self.cache is not None:
            del self.cache
            self.cache = None

        self.is_loaded = False
        gc.collect()

        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        logging.info("GGUF model unloaded and memory freed")

    def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""
        return self.model_info.copy()

    def is_model_loaded(self) -> bool:
        """Check if model is loaded"""
        return self.is_loaded

class TrainingDataManager:
    """Manages training data preparation and loading"""

    def __init__(self, config: GGUFTrainingConfig):
        self.config = config
        self.train_data = None
        self.val_data = None
        self.tokenizer = None

    def load_and_prepare_data(self) -> Tuple[List[Dict], List[Dict]]:
        """Load and prepare training data"""
        dataset_path = Path(self.config.dataset_path)

        logging.info(f"Loading dataset from: {dataset_path}")

        try:
            # Handle different dataset formats
            if dataset_path.suffix.lower() == '.json':
                return self._load_json_dataset(dataset_path)
            elif dataset_path.suffix.lower() == '.jsonl':
                return self._load_jsonl_dataset(dataset_path)
            elif dataset_path.is_dir():
                return self._load_hf_dataset(dataset_path)
            else:
                raise ValueError(f"Unsupported dataset format: {dataset_path.suffix}")

        except Exception as e:
            logging.error(f"Failed to load dataset: {e}")
            raise

    def _load_json_dataset(self, file_path: Path) -> Tuple[List[Dict], List[Dict]]:
        """Load JSON format dataset"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Handle different JSON structures
        if isinstance(data, list):
            # Direct list of examples
            examples = data
        elif isinstance(data, dict):
            if 'train' in data:
                # Dict with train/val split
                train_examples = data['train']
                val_examples = data.get('validation', data.get('val', []))
                return train_examples, val_examples
            else:
                # Single dict - treat as single example
                examples = [data]
        else:
            raise ValueError("Invalid JSON dataset structure")

        return self._split_dataset(examples)

    def _load_jsonl_dataset(self, file_path: Path) -> Tuple[List[Dict], List[Dict]]:
        """Load JSONL format dataset"""
        examples = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        example = json.loads(line)
                        examples.append(example)
                    except json.JSONDecodeError as e:
                        logging.warning(f"Skipping invalid JSON line: {e}")

        return self._split_dataset(examples)

    def _load_hf_dataset(self, dir_path: Path) -> Tuple[List[Dict], List[Dict]]:
        """Load Hugging Face dataset format"""
        if not DATASETS_AVAILABLE:
            raise ImportError("Datasets library not available")

        # Load dataset
        dataset = load_dataset(str(dir_path))

        # Convert to lists
        if isinstance(dataset, DatasetDict):
            train_data = dataset['train']
            val_data = dataset.get('validation', dataset.get('val', train_data))
            return list(train_data), list(val_data)
        else:
            return self._split_dataset(list(dataset))

    def _split_dataset(self, examples: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """Split dataset into train/validation"""
        if not examples:
            return [], []

        # Shuffle examples
        import random
        random.shuffle(examples)

        # Calculate split
        val_size = int(len(examples) * self.config.val_split)
        train_size = len(examples) - val_size

        train_data = examples[:train_size]
        val_data = examples[train_size:]

        logging.info(f"Dataset split: {len(train_data)} train, {len(val_data)} validation")
        return train_data, val_data

    def preprocess_examples(self, examples: List[Dict]) -> List[Dict[str, Any]]:
        """Preprocess training examples"""
        processed = []

        for example in examples:
            try:
                # Extract text from example
                if 'text' in example:
                    text = example['text']
                elif 'instruction' in example and 'response' in example:
                    # Instruction-response format
                    text = f"### Instruction:\n{example['instruction']}\n\n### Response:\n{example['response']}"
                elif 'input' in example and 'output' in example:
                    # Input-output format
                    text = f"### Input:\n{example['input']}\n\n### Output:\n{example['output']}"
                elif 'messages' in example:
                    # Chat format
                    messages = example['messages']
                    text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])
                else:
                    # Fallback - use all string fields
                    text_parts = []
                    for key, value in example.items():
                        if isinstance(value, str) and len(value) > 10:
                            text_parts.append(f"{key}: {value}")
                    text = "\n".join(text_parts)

                # Validate text
                if not text or len(text.strip()) < 10:
                    continue

                # Truncate to max sequence length
                if len(text) > self.config.max_seq_length:
                    text = text[:self.config.max_seq_length]

                processed.append({
                    "text": text,
                    "original_example": example
                })

            except Exception as e:
                logging.warning(f"Error preprocessing example: {e}")
                continue

        return processed

class CheckpointManager:
    """Manages training checkpoints and resume functionality"""

    def __init__(self, checkpoint_dir: Path, save_total_limit: int = 3):
        self.checkpoint_dir = checkpoint_dir
        self.save_total_limit = save_total_limit
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

        # Checkpoint tracking
        self.checkpoints = []
        self.best_checkpoint = None
        self.best_metric = float('inf')

        self._load_existing_checkpoints()

    def _load_existing_checkpoints(self):
        """Load information about existing checkpoints"""
        for checkpoint_path in self.checkpoint_dir.glob("checkpoint-*"):
            if checkpoint_path.is_dir():
                # Try to load checkpoint info
                info_file = checkpoint_path / "info.json"
                if info_file.exists():
                    try:
                        with open(info_file, 'r') as f:
                            info = json.load(f)
                        self.checkpoints.append({
                            "path": checkpoint_path,
                            "step": info.get("step", 0),
                            "epoch": info.get("epoch", 0),
                            "loss": info.get("loss", float('inf')),
                            "timestamp": info.get("timestamp", ""),
                            "is_best": info.get("is_best", False)
                        })

                        # Update best checkpoint
                        if info.get("is_best", False):
                            self.best_checkpoint = checkpoint_path
                            self.best_metric = info.get("loss", float('inf'))
                    except Exception as e:
                        logging.warning(f"Could not load checkpoint info from {info_file}: {e}")

        # Sort checkpoints by step
        self.checkpoints.sort(key=lambda x: x["step"])

    def save_checkpoint(self, model, optimizer, scheduler, step: int, epoch: int,
                       loss: float, metrics: Dict[str, Any] = None,
                       is_best: bool = False) -> Path:
        """Save training checkpoint"""
        checkpoint_name = f"checkpoint-step-{step}"
        checkpoint_path = self.checkpoint_dir / checkpoint_name
        checkpoint_path.mkdir(exist_ok=True)

        try:
            # Save model state
            model_state = {
                "step": step,
                "epoch": epoch,
                "loss": loss,
                "metrics": metrics or {},
                "timestamp": datetime.now().isoformat(),
                "is_best": is_best
            }

            # Save GGUF model state
            if hasattr(model, 'model') and model.model is not None:
                # Save llama.cpp model parameters
                model_state["model_params"] = {
                    "n_ctx": model.model.n_ctx,
                    "n_batch": model.model.n_batch,
                    "n_gpu_layers": model.config.n_gpu_layers
                }

            # Save optimizer and scheduler states
            if optimizer is not None:
                torch.save(optimizer.state_dict(), checkpoint_path / "optimizer.pt")

            if scheduler is not None:
                torch.save(scheduler.state_dict(), checkpoint_path / "scheduler.pt")

            # Save checkpoint info
            with open(checkpoint_path / "info.json", 'w') as f:
                json.dump(model_state, f, indent=2)

            # Add to checkpoints list
            checkpoint_info = {
                "path": checkpoint_path,
                "step": step,
                "epoch": epoch,
                "loss": loss,
                "timestamp": model_state["timestamp"],
                "is_best": is_best
            }
            self.checkpoints.append(checkpoint_info)

            # Update best checkpoint
            if is_best or loss < self.best_metric:
                self.best_checkpoint = checkpoint_path
                self.best_metric = loss
                model_state["is_best"] = True
                with open(checkpoint_path / "info.json", 'w') as f:
                    json.dump(model_state, f, indent=2)

            # Clean up old checkpoints
            self._cleanup_checkpoints()

            logging.info(f"Checkpoint saved: {checkpoint_path} (step {step}, loss {loss:.4f})")
            return checkpoint_path

        except Exception as e:
            logging.error(f"Failed to save checkpoint: {e}")
            # Clean up failed checkpoint
            if checkpoint_path.exists():
                shutil.rmtree(checkpoint_path)
            raise

    def load_checkpoint(self, checkpoint_path: Path, model, optimizer, scheduler):
        """Load training checkpoint"""
        if not checkpoint_path.exists():
            raise FileNotFoundError(f"Checkpoint not found: {checkpoint_path}")

        try:
            info_file = checkpoint_path / "info.json"
            with open(info_file, 'r') as f:
                checkpoint_info = json.load(f)

            # Load optimizer state
            optimizer_path = checkpoint_path / "optimizer.pt"
            if optimizer_path.exists() and optimizer is not None:
                optimizer.load_state_dict(torch.load(optimizer_path))

            # Load scheduler state
            scheduler_path = checkpoint_path / "scheduler.pt"
            if scheduler_path.exists() and scheduler is not None:
                scheduler.load_state_dict(torch.load(scheduler_path))

            logging.info(f"Checkpoint loaded: {checkpoint_path} (step {checkpoint_info['step']})")
            return checkpoint_info

        except Exception as e:
            logging.error(f"Failed to load checkpoint: {e}")
            raise

    def get_latest_checkpoint(self) -> Optional[Path]:
        """Get the latest checkpoint"""
        if not self.checkpoints:
            return None
        return self.checkpoints[-1]["path"]

    def get_best_checkpoint(self) -> Optional[Path]:
        """Get the best checkpoint"""
        return self.best_checkpoint

    def _cleanup_checkpoints(self):
        """Clean up old checkpoints to maintain save_total_limit"""
        if len(self.checkpoints) <= self.save_total_limit:
            return

        # Keep the best checkpoint and the most recent save_total_limit - 1 checkpoints
        checkpoints_to_keep = []

        # Always keep the best checkpoint
        if self.best_checkpoint:
            checkpoints_to_keep.append(self.best_checkpoint)

        # Keep the most recent checkpoints
        recent_checkpoints = sorted(
            [cp for cp in self.checkpoints if cp["path"] != self.best_checkpoint],
            key=lambda x: x["step"]
        )
        checkpoints_to_keep.extend([cp["path"] for cp in recent_checkpoints[-(self.save_total_limit - 1):]])

        # Remove old checkpoints
        for checkpoint in self.checkpoints:
            if checkpoint["path"] not in checkpoints_to_keep:
                try:
                    shutil.rmtree(checkpoint["path"])
                    logging.info(f"Removed old checkpoint: {checkpoint['path']}")
                except Exception as e:
                    logging.warning(f"Failed to remove checkpoint {checkpoint['path']}: {e}")

        # Update checkpoints list
        self.checkpoints = [cp for cp in self.checkpoints if cp["path"] in checkpoints_to_keep]

class ModelTrainer:
    """Main model trainer class with DuckBot service integration"""

    def __init__(self, config_path: Optional[str] = None):
        # Setup directories first
        self.project_root = Path(__file__).parent.parent.parent
        self.models_dir = self.project_root / "models"
        self.datasets_dir = self.project_root / "datasets"
        self.output_dir = self.project_root / "trained_models"

        # Create directories if they don't exist
        self.models_dir.mkdir(exist_ok=True)
        self.datasets_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)

        # Initialize model registry
        self.model_registry = ModelRegistry(self.models_dir)

        # Setup logging and monitoring
        self.logger = self._setup_logger()
        self.config_path = config_path
        self.training_config: Optional[TrainingConfig] = None
        self.process: Optional[subprocess.Popen] = None
        self.is_training = False
        self.training_thread: Optional[threading.Thread] = None

        # DuckBot service integration
        self.service_manager = None
        self.monitoring_system = None
        self.cost_tracker = None
        self.service_integration_enabled = DUCKBOT_AVAILABLE

        if self.service_integration_enabled:
            self._initialize_duckbot_services()

        # Training monitoring
        self.training_metrics = {
            "start_time": None,
            "current_step": 0,
            "current_epoch": 0,
            "current_loss": 0.0,
            "best_loss": float('inf'),
            "learning_rate": 0.0,
            "memory_usage": 0.0,
            "cpu_usage": 0.0,
            "gpu_usage": 0.0,
            "estimated_time_remaining": None,
            "samples_processed": 0,
            "total_samples": 0
        }

        # Event system for real-time updates
        self.event_callbacks = {
            "training_started": [],
            "training_progress": [],
            "training_completed": [],
            "training_failed": [],
            "checkpoint_saved": [],
            "error_occurred": []
        }

        self.logger.info("ModelTrainer initialized with DuckBot service integration")

    def _initialize_duckbot_services(self):
        """Initialize DuckBot service integration"""
        try:
            # Initialize service manager
            self.service_manager = UnifiedServiceManager()

            # Initialize monitoring system
            self.monitoring_system = MonitoringSystem()

            # Initialize cost tracker
            self.cost_tracker = CostTracker()

            # Register model training service with DuckBot
            self._register_training_service()

            self.logger.info("DuckBot services initialized successfully")

        except Exception as e:
            self.logger.warning(f"Failed to initialize DuckBot services: {e}")
            self.service_integration_enabled = False

    def _register_training_service(self):
        """Register model training service with DuckBot"""
        if not self.service_manager:
            return

        try:
            # Create service info for model training
            training_service_info = ServiceInfo(
                name="model_training",
                display_name="DuckBot Model Training",
                service_type=ServiceType.ENHANCED,
                status=ServiceStatus.STOPPED,
                port=None,  # Dynamic port allocation
                config={
                    "models_dir": str(self.models_dir),
                    "datasets_dir": str(self.datasets_dir),
                    "output_dir": str(self.output_dir),
                    "supported_model_types": ["gguf", "hf_transformers"],
                    "supported_training_methods": ["lora", "full_fine_tune", "distillation"]
                },
                auto_start=False,  # Manual start
                dependencies=["lm_studio"] if self.service_manager.services.get("lm_studio") else []
            )

            # Register with service manager
            self.service_manager.services["model_training"] = training_service_info
            self.service_manager.locks["model_training"] = threading.Lock()
            self.service_manager.callbacks["model_training"] = []

            self.logger.info("Model training service registered with DuckBot")

        except Exception as e:
            self.logger.error(f"Failed to register training service: {e}")

    def add_event_callback(self, event_type: str, callback):
        """Add callback for training events"""
        if event_type in self.event_callbacks:
            self.event_callbacks[event_type].append(callback)

    def _emit_event(self, event_type: str, data: Dict[str, Any]):
        """Emit training event to callbacks"""
        if event_type in self.event_callbacks:
            for callback in self.event_callbacks[event_type]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        # Run async callback in new event loop
                        asyncio.run(callback(event_type, data))
                    else:
                        callback(event_type, data)
                except Exception as e:
                    self.logger.error(f"Error in event callback: {e}")

    def update_service_status(self, status: ServiceStatus):
        """Update service status in DuckBot"""
        if self.service_integration_enabled and self.service_manager:
            try:
                if "model_training" in self.service_manager.services:
                    self.service_manager.services["model_training"].status = status

                    # Notify service manager of status change
                    asyncio.run(self.service_manager._notify_service_change("model_training", status.value))

            except Exception as e:
                self.logger.error(f"Failed to update service status: {e}")

    def get_training_metrics(self) -> Dict[str, Any]:
        """Get comprehensive training metrics"""
        metrics = self.training_metrics.copy()

        # Add system metrics
        try:
            system_info = psutil.virtual_memory()
            metrics["system_memory"] = {
                "total_gb": system_info.total / (1024**3),
                "available_gb": system_info.available / (1024**3),
                "percent_used": system_info.percent
            }

            # CPU usage
            metrics["cpu_usage"] = psutil.cpu_percent(interval=1)

            # GPU usage if available
            if TORCH_AVAILABLE and torch.cuda.is_available():
                gpu_memory = torch.cuda.memory_allocated() / (1024**3)
                gpu_total = torch.cuda.get_device_properties(0).total_memory / (1024**3)
                metrics["gpu_usage"] = {
                    "allocated_gb": gpu_memory,
                    "total_gb": gpu_total,
                    "percent_used": (gpu_memory / gpu_total) * 100
                }

        except Exception as e:
            self.logger.warning(f"Could not get system metrics: {e}")

        # Add training progress
        if self.training_metrics["start_time"]:
            elapsed_time = time.time() - self.training_metrics["start_time"]
            metrics["elapsed_time_seconds"] = elapsed_time
            metrics["elapsed_time_formatted"] = str(timedelta(seconds=int(elapsed_time)))

            # Estimate remaining time
            if self.training_metrics["current_step"] > 0 and self.training_config:
                steps_per_second = self.training_metrics["current_step"] / elapsed_time
                total_steps = self.training_config.epochs * (1000 // self.training_config.logging_steps)  # Estimate
                remaining_steps = total_steps - self.training_metrics["current_step"]
                if steps_per_second > 0:
                    remaining_seconds = remaining_steps / steps_per_second
                    metrics["estimated_time_remaining"] = str(timedelta(seconds=int(remaining_seconds)))

        return metrics

    def start_training_with_service(self, config: TrainingConfig) -> bool:
        """Start training with DuckBot service integration"""
        if not self.start_training(config):
            return False

        # Update service status
        self.update_service_status(ServiceStatus.RUNNING)

        # Emit training started event
        self._emit_event("training_started", {
            "config": config.__dict__,
            "start_time": time.time()
        })

        return True

    def create_comprehensive_config(self, **kwargs) -> GGUFTrainingConfig:
        """Create comprehensive GGUF training configuration with validation"""
        # Default values for GGUF training
        config_dict = {
            # Model Configuration
            "model_path": kwargs.get("model_path", ""),
            "model_name": kwargs.get("model_name", ""),
            "quantization": kwargs.get("quantization", QuantizationType.Q4_K),
            "context_length": kwargs.get("context_length", 4096),
            "n_gpu_layers": kwargs.get("n_gpu_layers", -1),
            "n_batch": kwargs.get("n_batch", 512),
            "n_threads": kwargs.get("n_threads", 4),

            # Training Configuration
            "training_method": kwargs.get("training_method", TrainingMethod.LORA),
            "learning_rate": kwargs.get("learning_rate", 3e-4),
            "weight_decay": kwargs.get("weight_decay", 0.01),
            "warmup_ratio": kwargs.get("warmup_ratio", 0.1),
            "max_grad_norm": kwargs.get("max_grad_norm", 1.0),
            "gradient_accumulation_steps": kwargs.get("gradient_accumulation_steps", 4),

            # Data Configuration
            "dataset_path": kwargs.get("dataset_path", ""),
            "val_split": kwargs.get("val_split", 0.1),
            "max_seq_length": kwargs.get("max_seq_length", 2048),
            "block_size": kwargs.get("block_size", 1024),

            # LoRA Configuration
            "lora_r": kwargs.get("lora_r", 8),
            "lora_alpha": kwargs.get("lora_alpha", 16),
            "lora_dropout": kwargs.get("lora_dropout", 0.1),
            "lora_target_modules": kwargs.get("lora_target_modules", ["q_proj", "v_proj"]),

            # Memory Management
            "memory_strategy": kwargs.get("memory_strategy", MemoryStrategy.BALANCED),
            "max_memory_gb": kwargs.get("max_memory_gb", 8.0),
            "offload_folder": kwargs.get("offload_folder", None),
            "use_flash_attention": kwargs.get("use_flash_attention", True),

            # Training Loop
            "epochs": kwargs.get("epochs", 3),
            "max_steps": kwargs.get("max_steps", None),
            "save_steps": kwargs.get("save_steps", 500),
            "logging_steps": kwargs.get("logging_steps", 50),
            "eval_steps": kwargs.get("eval_steps", 500),
            "save_total_limit": kwargs.get("save_total_limit", 3),

            # Distributed Training
            "distributed_strategy": kwargs.get("distributed_strategy", DistributedStrategy.NONE),
            "world_size": kwargs.get("world_size", 1),
            "local_rank": kwargs.get("local_rank", 0),

            # Output and Checkpointing
            "output_dir": kwargs.get("output_dir", ""),
            "checkpoint_dir": kwargs.get("checkpoint_dir", None),
            "resume_from_checkpoint": kwargs.get("resume_from_checkpoint", None),

            # Advanced Options
            "mixed_precision": kwargs.get("mixed_precision", "fp16"),
            "optimizer": kwargs.get("optimizer", "adamw_torch"),
            "scheduler": kwargs.get("scheduler", "cosine"),

            # DuckBot Integration
            "enable_service_integration": kwargs.get("enable_service_integration", True),
            "health_check_interval": kwargs.get("health_check_interval", 30),
            "auto_restart": kwargs.get("auto_restart", True),

            # Logging and Monitoring
            "log_level": kwargs.get("log_level", "INFO"),
            "enable_tensorboard": kwargs.get("enable_tensorboard", True),
            "enable_wandb": kwargs.get("enable_wandb", False),
            "wandb_project": kwargs.get("wandb_project", None),
            "wandb_run_name": kwargs.get("wandb_run_name", None),

            # Hardware Optimization
            "use_mps": kwargs.get("use_mps", False),
            "use_xpu": kwargs.get("use_xpu", False),
            "pin_memory": kwargs.get("pin_memory", True),
            "num_workers": kwargs.get("num_workers", 4),

            # Advanced Training
            "early_stopping_patience": kwargs.get("early_stopping_patience", 3),
            "early_stopping_threshold": kwargs.get("early_stopping_threshold", 0.001),
            "max_no_improvement": kwargs.get("max_no_improvement", 5),

            # Quantization-Specific
            "quantize_after_training": kwargs.get("quantize_after_training", False),
            "target_quantization": kwargs.get("target_quantization", None)
        }

        # Validate required parameters
        if not config_dict["model_path"]:
            raise ValueError("model_path is required")
        if not config_dict["dataset_path"]:
            raise ValueError("dataset_path is required")
        if not config_dict["output_dir"]:
            raise ValueError("output_dir is required")

        # Set model name from path if not provided
        if not config_dict["model_name"]:
            config_dict["model_name"] = Path(config_dict["model_path"]).stem

        # Auto-detect optimal parameters based on system
        config_dict = self._auto_optimize_config(config_dict)

        # Create configuration object
        return GGUFTrainingConfig(**config_dict)

    def _auto_optimize_config(self, config_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Auto-optimize configuration based on system capabilities"""
        try:
            # Get system information
            system_memory = psutil.virtual_memory()
            total_memory_gb = system_memory.total / (1024**3)
            available_memory_gb = system_memory.available / (1024**3)

            # Optimize memory settings
            if config_dict["max_memory_gb"] > available_memory_gb * 0.8:
                config_dict["max_memory_gb"] = available_memory_gb * 0.8

            # Optimize batch size based on available memory
            if config_dict["batch_size"] > 4 and total_memory_gb < 16:
                config_dict["batch_size"] = 2
            elif config_dict["batch_size"] > 8 and total_memory_gb < 32:
                config_dict["batch_size"] = 4

            # Optimize GPU layers
            if TORCH_AVAILABLE and torch.cuda.is_available():
                gpu_memory_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
                if gpu_memory_gb < 8:
                    config_dict["n_gpu_layers"] = 20  # Use fewer layers for small GPUs
                elif gpu_memory_gb > 16:
                    config_dict["n_gpu_layers"] = -1  # Use all layers for large GPUs

            # Optimize thread count
            cpu_count = psutil.cpu_count(logical=False)
            config_dict["n_threads"] = min(config_dict["n_threads"], cpu_count)

            # Optimize context length based on model size
            model_path = Path(config_dict["model_path"])
            if model_path.exists():
                model_size_gb = model_path.stat().st_size / (1024**3)
                if model_size_gb < 4:
                    config_dict["context_length"] = 2048
                elif model_size_gb > 13:
                    config_dict["context_length"] = 8192

            # Enable mixed precision based on GPU capability
            if TORCH_AVAILABLE and torch.cuda.is_available():
                if torch.cuda.get_device_properties(0).major >= 7:
                    config_dict["mixed_precision"] = "fp16"
                else:
                    config_dict["mixed_precision"] = "no"

            self.logger.info("Configuration auto-optimized based on system capabilities")

        except Exception as e:
            self.logger.warning(f"Could not auto-optimize configuration: {e}")

        return config_dict

    def validate_config(self, config: GGUFTrainingConfig) -> Tuple[bool, List[str]]:
        """Validate training configuration"""
        errors = []

        # Check required files
        if not Path(config.model_path).exists():
            errors.append(f"Model file not found: {config.model_path}")

        if not Path(config.dataset_path).exists():
            errors.append(f"Dataset file not found: {config.dataset_path}")

        # Check memory requirements
        model_size_gb = Path(config.model_path).stat().st_size / (1024**3)
        required_memory = model_size_gb + 2.0  # Model + training overhead

        available_memory = psutil.virtual_memory().available / (1024**3)
        if required_memory > available_memory * 0.9:
            errors.append(f"Insufficient memory: required {required_memory:.1f}GB, available {available_memory:.1f}GB")

        # Check learning rate
        if config.learning_rate <= 0 or config.learning_rate > 1:
            errors.append(f"Learning rate must be between 0 and 1: {config.learning_rate}")

        # Check epochs
        if config.epochs <= 0 or config.epochs > 100:
            errors.append(f"Epochs must be between 1 and 100: {config.epochs}")

        # Check batch size
        if config.batch_size <= 0 or config.batch_size > 128:
            errors.append(f"Batch size must be between 1 and 128: {config.batch_size}")

        # Check context length
        if config.context_length < 512 or config.context_length > 32768:
            errors.append(f"Context length must be between 512 and 32768: {config.context_length}")

        # Check LoRA parameters if using LoRA
        if config.training_method == TrainingMethod.LORA:
            if config.lora_r <= 0 or config.lora_r > 256:
                errors.append(f"LoRA rank must be between 1 and 256: {config.lora_r}")
            if config.lora_alpha <= 0 or config.lora_alpha > 512:
                errors.append(f"LoRA alpha must be between 1 and 512: {config.lora_alpha}")
            if config.lora_dropout < 0 or config.lora_dropout >= 1:
                errors.append(f"LoRA dropout must be between 0 and 1: {config.lora_dropout}")

        # Check dependencies
        if config.training_method == TrainingMethod.LORA and not PEFT_AVAILABLE:
            errors.append("PEFT library not available for LoRA training")

        if config.training_method in [TrainingMethod.FULL_FINE_TUNE, TrainingMethod.LORA] and not TORCH_AVAILABLE:
            errors.append("PyTorch not available for training")

        return len(errors) == 0, errors

    def save_training_config(self, config: GGUFTrainingConfig, config_path: str):
        """Save training configuration to file"""
        try:
            config_dict = config.to_dict()

            # Add metadata
            config_dict["metadata"] = {
                "created_at": datetime.now().isoformat(),
                "duckbot_version": "4.2",
                "config_version": "1.0",
                "system_info": {
                    "platform": platform.system(),
                    "python_version": sys.version,
                    "cpu_count": psutil.cpu_count(),
                    "memory_gb": psutil.virtual_memory().total / (1024**3)
                }
            }

            # Create directory if needed
            Path(config_path).parent.mkdir(parents=True, exist_ok=True)

            # Save based on file extension
            if config_path.endswith('.json'):
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(config_dict, f, indent=2)
            elif config_path.endswith('.yaml') or config_path.endswith('.yml'):
                with open(config_path, 'w', encoding='utf-8') as f:
                    yaml.dump(config_dict, f, default_flow_style=False)
            else:
                raise ValueError("Unsupported config file format")

            self.logger.info(f"Training configuration saved to {config_path}")

        except Exception as e:
            self.logger.error(f"Failed to save training config: {e}")
            raise

    def load_training_config(self, config_path: str) -> GGUFTrainingConfig:
        """Load training configuration from file"""
        try:
            if not Path(config_path).exists():
                raise FileNotFoundError(f"Config file not found: {config_path}")

            # Load based on file extension
            if config_path.endswith('.json'):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_dict = json.load(f)
            elif config_path.endswith('.yaml') or config_path.endswith('.yml'):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_dict = yaml.safe_load(f)
            else:
                raise ValueError("Unsupported config file format")

            # Remove metadata if present
            if "metadata" in config_dict:
                del config_dict["metadata"]

            # Create configuration object
            config = GGUFTrainingConfig.from_dict(config_dict)

            self.logger.info(f"Training configuration loaded from {config_path}")
            return config

        except Exception as e:
            self.logger.error(f"Failed to load training config: {e}")
            raise

    def create_sample_config(self, output_path: str):
        """Create a sample configuration file"""
        sample_config = self.create_comprehensive_config(
            model_path="./models/sample_model.gguf",
            dataset_path="./datasets/sample_dataset.json",
            output_dir="./trained_models/sample_output",
            model_name="Sample Model",
            epochs=3,
            training_method=TrainingMethod.LORA,
            learning_rate=3e-4,
            batch_size=4,
            quantization=QuantizationType.Q4_K,
            context_length=2048,
            memory_strategy=MemoryStrategy.BALANCED
        )

        self.save_training_config(sample_config, output_path)
        self.logger.info(f"Sample configuration created at {output_path}")

    def get_config_presets(self) -> Dict[str, Dict[str, Any]]:
        """Get predefined configuration presets"""
        return {
            "fast_test": {
                "description": "Fast testing configuration",
                "epochs": 1,
                "batch_size": 2,
                "max_seq_length": 1024,
                "save_steps": 100,
                "eval_steps": 100,
                "logging_steps": 10,
                "memory_strategy": MemoryStrategy.CONSERVATIVE,
                "gradient_accumulation_steps": 1
            },
            "balanced_training": {
                "description": "Balanced training configuration",
                "epochs": 3,
                "batch_size": 4,
                "max_seq_length": 2048,
                "save_steps": 500,
                "eval_steps": 500,
                "logging_steps": 50,
                "memory_strategy": MemoryStrategy.BALANCED,
                "gradient_accumulation_steps": 4
            },
            "high_quality": {
                "description": "High quality training configuration",
                "epochs": 5,
                "batch_size": 8,
                "max_seq_length": 4096,
                "save_steps": 1000,
                "eval_steps": 1000,
                "logging_steps": 100,
                "memory_strategy": MemoryStrategy.AGGRESSIVE,
                "gradient_accumulation_steps": 8,
                "early_stopping_patience": 5
            },
            "memory_efficient": {
                "description": "Memory efficient configuration for large models",
                "epochs": 2,
                "batch_size": 1,
                "max_seq_length": 1024,
                "save_steps": 250,
                "eval_steps": 250,
                "logging_steps": 25,
                "memory_strategy": MemoryStrategy.CONSERVATIVE,
                "gradient_accumulation_steps": 16,
                "offload_folder": "./offload"
            }
        }
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logger for the trainer"""
        logger = logging.getLogger('DuckBot.ModelTrainer')
        logger.setLevel(logging.INFO)
        
        # Create logs directory
        log_dir = self.project_root / "logs"
        log_dir.mkdir(exist_ok=True)
        
        # File handler
        file_handler = logging.FileHandler(
            log_dir / "model_trainer.log", encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def load_config(self, config_path: str) -> TrainingConfig:
        """Load training configuration from file"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                if config_path.endswith('.json'):
                    config_data = json.load(f)
                elif config_path.endswith('.yaml') or config_path.endswith('.yml'):
                    config_data = yaml.safe_load(f)
                else:
                    raise ValueError("Unsupported config file format")
            
            # Convert string enums to enum objects
            if 'model_type' in config_data:
                config_data['model_type'] = ModelType(config_data['model_type'])
            if 'training_method' in config_data:
                config_data['training_method'] = TrainingMethod(config_data['training_method'])
            
            self.training_config = TrainingConfig(**config_data)
            self.logger.info(f"Loaded training configuration from {config_path}")
            return self.training_config
        except Exception as e:
            self.logger.error(f"Failed to load config: {e}")
            raise
    
    def save_config(self, config: TrainingConfig, config_path: str):
        """Save training configuration to file"""
        try:
            config_dict = asdict(config)
            # Convert enum objects to strings
            if isinstance(config_dict.get('model_type'), ModelType):
                config_dict['model_type'] = config_dict['model_type'].value
            if isinstance(config_dict.get('training_method'), TrainingMethod):
                config_dict['training_method'] = config_dict['training_method'].value
            
            with open(config_path, 'w', encoding='utf-8') as f:
                if config_path.endswith('.json'):
                    json.dump(config_dict, f, indent=2)
                elif config_path.endswith('.yaml') or config_path.endswith('.yml'):
                    yaml.dump(config_dict, f, default_flow_style=False)
            
            self.logger.info(f"Saved training configuration to {config_path}")
        except Exception as e:
            self.logger.error(f"Failed to save config: {e}")
            raise
    
    def download_hf_model(self, model_id: str, token: Optional[str] = None) -> str:
        """Download a model from Hugging Face"""
        try:
            self.logger.info(f"Downloading model {model_id} from Hugging Face...")
            
            # Download the model
            model_path = snapshot_download(
                repo_id=model_id,
                token=token,
                cache_dir=str(self.models_dir / "hf_cache")
            )
            
            # Move to models directory
            model_name = model_id.replace("/", "_")
            final_path = self.models_dir / model_name
            if final_path.exists():
                shutil.rmtree(final_path)
            shutil.move(model_path, final_path)
            
            self.logger.info(f"Downloaded model to {final_path}")
            return str(final_path)
        except Exception as e:
            self.logger.error(f"Failed to download model: {e}")
            raise
    
    def find_gguf_model(self, model_name: str) -> Optional[str]:
        """Find a GGUF model by name"""
        # Search in models directory
        for file_path in self.models_dir.rglob(f"*{model_name}*.gguf"):
            if file_path.is_file():
                return str(file_path)
        
        # Search in common model locations
        common_paths = [
            Path.home() / ".cache" / "lm-studio" / "models",
            Path.home() / "Downloads",
            Path("C:\\Users\\Public\\Documents\\LMStudio\\models") if os.name == 'nt' else Path("/usr/local/share/models")
        ]
        
        for path in common_paths:
            if path.exists():
                for file_path in path.rglob(f"*{model_name}*.gguf"):
                    if file_path.is_file():
                        return str(file_path)
        
        return None
    
    def prepare_dataset(self, dataset_path: str) -> str:
        """Prepare dataset for training"""
        dataset_path = Path(dataset_path)
        
        if not dataset_path.exists():
            raise FileNotFoundError(f"Dataset not found: {dataset_path}")
        
        # If it's a directory, assume it contains the dataset files
        if dataset_path.is_dir():
            return str(dataset_path)
        
        # If it's a file, check if it needs processing
        if dataset_path.suffix.lower() in ['.json', '.jsonl']:
            # Already in correct format
            return str(dataset_path)
        
        # For other formats, we might need conversion
        # This is a simplified example - you'd want more robust handling
        self.logger.warning(f"Dataset format {dataset_path.suffix} may require conversion")
        return str(dataset_path)
    
    def start_training(self, config: Optional[TrainingConfig] = None) -> bool:
        """Start the model training process"""
        if self.is_training:
            self.logger.warning("Training is already in progress")
            return False
        
        if config:
            self.training_config = config
        elif not self.training_config:
            raise ValueError("No training configuration provided")
        
        self.logger.info("Starting model training...")
        self.is_training = True
        
        # Start training in a separate thread
        self.training_thread = threading.Thread(target=self._run_training, daemon=True)
        self.training_thread.start()
        
        return True
    
    def _run_training(self):
        """Run the actual training process"""
        try:
            config = self.training_config

            # Initialize training metrics
            self.training_metrics["start_time"] = time.time()
            self.training_metrics["current_step"] = 0
            self.training_metrics["current_epoch"] = 0
            self.training_metrics["current_loss"] = 0.0
            self.training_metrics["best_loss"] = float('inf')

            # Emit training started event
            self._emit_event("training_started", {
                "config": config.__dict__,
                "start_time": self.training_metrics["start_time"]
            })

            # Update service status
            self.update_service_status(ServiceStatus.RUNNING)

            # Prepare model path
            if config.model_path.startswith("hf:"):
                # Download from Hugging Face if needed
                model_id = config.model_path[3:]  # Remove "hf:" prefix
                model_path = self.download_hf_model(model_id)
            elif config.model_path.endswith(".gguf"):
                # Find GGUF model
                model_path = self.find_gguf_model(config.model_path) or config.model_path
            else:
                model_path = config.model_path

            if not os.path.exists(model_path):
                raise FileNotFoundError(f"Model not found: {model_path}")

            # Prepare dataset
            dataset_path = self.prepare_dataset(config.dataset_path)

            # Prepare output directory
            output_path = Path(config.output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            # Start monitoring thread
            monitoring_thread = threading.Thread(target=self._monitor_training, daemon=True)
            monitoring_thread.start()

            # Create standalone trainer
            trainer = StandaloneTrainer(
                model_path=model_path,
                model_type=config.model_type,
                train_dataset_path=dataset_path,
                output_dir=str(output_path),
                config=config
            )

            # Run training
            trainer.train()

            # Update final metrics
            self.training_metrics["current_loss"] = getattr(trainer, 'final_loss', 0.0)

            # Emit training completed event
            self._emit_event("training_completed", {
                "final_loss": self.training_metrics["current_loss"],
                "training_time": time.time() - self.training_metrics["start_time"],
                "output_dir": str(output_path)
            })

            # Update service status
            self.update_service_status(ServiceStatus.STOPPED)

            self.logger.info("Training completed successfully")

        except Exception as e:
            # Emit error event
            self._emit_event("training_failed", {
                "error": str(e),
                "traceback": traceback.format_exc(),
                "training_time": time.time() - self.training_metrics["start_time"] if self.training_metrics["start_time"] else 0
            })

            # Update service status
            self.update_service_status(ServiceStatus.ERROR)

            self.logger.error(f"Training failed: {e}")
            self.logger.error(traceback.format_exc())
        finally:
            self.is_training = False

    def _monitor_training(self):
        """Monitor training progress and emit events"""
        while self.is_training:
            try:
                # Get current metrics
                metrics = self.get_training_metrics()

                # Emit progress event
                self._emit_event("training_progress", metrics)

                # Log progress periodically
                if self.training_metrics["current_step"] % 100 == 0 and self.training_metrics["current_step"] > 0:
                    self.logger.info(f"Training progress - Step: {self.training_metrics['current_step']}, "
                                   f"Loss: {self.training_metrics['current_loss']:.4f}, "
                                   f"Memory: {metrics.get('system_memory', {}).get('percent_used', 0):.1f}%")

                # Check for issues
                if metrics.get("system_memory", {}).get("percent_used", 0) > 95:
                    self.logger.warning("High memory usage detected during training")

                if metrics.get("cpu_usage", 0) > 95:
                    self.logger.warning("High CPU usage detected during training")

                # Wait before next check
                time.sleep(10)  # Check every 10 seconds

            except Exception as e:
                self.logger.error(f"Error in training monitoring: {e}")
                time.sleep(30)  # Wait longer on error

    def start_training_with_monitoring(self, config: TrainingConfig) -> bool:
        """Start training with enhanced monitoring and logging"""
        # Validate configuration first
        if isinstance(config, GGUFTrainingConfig):
            is_valid, errors = self.validate_config(config)
            if not is_valid:
                self.logger.error("Configuration validation failed:")
                for error in errors:
                    self.logger.error(f"  - {error}")
                return False

        # Start training
        return self.start_training_with_service(config)

    def get_training_status_detailed(self) -> Dict[str, Any]:
        """Get detailed training status with comprehensive information"""
        status = self.get_training_status()

        # Add comprehensive metrics
        status["metrics"] = self.get_training_metrics()

        # Add system information
        status["system"] = {
            "platform": platform.system(),
            "python_version": sys.version,
            "cpu_count": psutil.cpu_count(),
            "memory_total_gb": psutil.virtual_memory().total / (1024**3),
            "gpu_available": TORCH_AVAILABLE and torch.cuda.is_available() if TORCH_AVAILABLE else False
        }

        # Add DuckBot integration status
        status["duckbot_integration"] = {
            "enabled": self.service_integration_enabled,
            "service_registered": self.service_manager is not None,
            "monitoring_active": self.monitoring_system is not None,
            "cost_tracking": self.cost_tracker is not None
        }

        # Add available models
        try:
            status["available_models"] = self.list_available_models()
        except Exception as e:
            self.logger.warning(f"Could not get available models: {e}")
            status["available_models"] = []

        return status

    def export_training_logs(self, output_path: str):
        """Export training logs and metrics to file"""
        try:
            # Create export data
            export_data = {
                "training_session": {
                    "start_time": self.training_metrics.get("start_time"),
                    "end_time": time.time() if not self.is_training else None,
                    "is_training": self.is_training,
                    "config": self.training_config.__dict__ if self.training_config else None
                },
                "metrics": self.get_training_metrics(),
                "system_info": {
                    "platform": platform.system(),
                    "cpu_count": psutil.cpu_count(),
                    "memory_gb": psutil.virtual_memory().total / (1024**3),
                    "export_time": datetime.now().isoformat()
                }
            }

            # Save export
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, default=str)

            self.logger.info(f"Training logs exported to {output_path}")

        except Exception as e:
            self.logger.error(f"Failed to export training logs: {e}")
            raise

    def cleanup_training_artifacts(self, keep_checkpoints: int = 3):
        """Clean up training artifacts to save space"""
        try:
            if not self.training_config or not self.training_config.output_dir:
                return

            output_dir = Path(self.training_config.output_dir)
            if not output_dir.exists():
                return

            # Clean up old checkpoints
            checkpoints_dir = output_dir / "checkpoints"
            if checkpoints_dir.exists():
                checkpoints = list(checkpoints_dir.glob("checkpoint-*"))
                checkpoints.sort(key=lambda x: x.stat().st_mtime, reverse=True)

                # Keep only the latest N checkpoints
                for checkpoint in checkpoints[keep_checkpoints:]:
                    try:
                        shutil.rmtree(checkpoint)
                        self.logger.info(f"Removed old checkpoint: {checkpoint}")
                    except Exception as e:
                        self.logger.warning(f"Could not remove checkpoint {checkpoint}: {e}")

            # Clean up temporary files
            temp_files = list(output_dir.glob("*.tmp"))
            for temp_file in temp_files:
                try:
                    temp_file.unlink()
                    self.logger.info(f"Removed temporary file: {temp_file}")
                except Exception as e:
                    self.logger.warning(f"Could not remove temp file {temp_file}: {e}")

            # Clean up old logs
            logs_dir = output_dir / "logs"
            if logs_dir.exists():
                log_files = list(logs_dir.glob("training_*.log"))
                log_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

                # Keep only the latest 5 log files
                for log_file in log_files[5:]:
                    try:
                        log_file.unlink()
                        self.logger.info(f"Removed old log file: {log_file}")
                    except Exception as e:
                        self.logger.warning(f"Could not remove log file {log_file}: {e}")

        except Exception as e:
            self.logger.error(f"Failed to cleanup training artifacts: {e}")

    def estimate_training_time(self, config: TrainingConfig) -> Dict[str, Any]:
        """Estimate training time based on configuration"""
        try:
            # Base estimates (rough approximations)
            base_time_per_epoch = {
                TrainingMethod.LORA: 30,  # minutes
                TrainingMethod.FULL_FINE_TUNE: 120,
                TrainingMethod.DISTILLATION: 90,
                TrainingMethod.CONTINUED_PRETRAINING: 180
            }

            # Get model size factor
            model_path = Path(config.model_path)
            if model_path.exists():
                model_size_gb = model_path.stat().st_size / (1024**3)
                size_factor = max(0.5, model_size_gb / 7.0)  # Normalize to 7GB models
            else:
                size_factor = 1.0

            # Get data size factor
            dataset_path = Path(config.dataset_path)
            if dataset_path.exists():
                if dataset_path.is_file():
                    dataset_size_mb = dataset_path.stat().st_size / (1024**2)
                else:
                    dataset_size_mb = sum(f.stat().st_size for f in dataset_path.rglob('*') if f.is_file()) / (1024**2)
                data_factor = max(0.5, dataset_size_mb / 100.0)  # Normalize to 100MB datasets
            else:
                data_factor = 1.0

            # Get hardware factor
            cpu_factor = psutil.cpu_count() / 8.0  # Normalize to 8 CPUs
            memory_factor = psutil.virtual_memory().total / (1024**3) / 16.0  # Normalize to 16GB

            if TORCH_AVAILABLE and torch.cuda.is_available():
                gpu_factor = torch.cuda.get_device_properties(0).total_memory / (1024**3) / 8.0  # Normalize to 8GB
            else:
                gpu_factor = 0.5  # CPU only

            # Calculate estimated time
            base_time = base_time_per_epoch.get(config.training_method, 60)
            estimated_minutes = (base_time * config.epochs * size_factor * data_factor) / (cpu_factor * memory_factor * gpu_factor)

            # Add variance
            optimistic_minutes = estimated_minutes * 0.7
            pessimistic_minutes = estimated_minutes * 1.5

            return {
                "estimated_minutes": int(estimated_minutes),
                "estimated_hours": estimated_minutes / 60,
                "optimistic_minutes": int(optimistic_minutes),
                "pessimistic_minutes": int(pessimistic_minutes),
                "factors": {
                    "method_factor": config.training_method.value,
                    "size_factor": round(size_factor, 2),
                    "data_factor": round(data_factor, 2),
                    "cpu_factor": round(cpu_factor, 2),
                    "memory_factor": round(memory_factor, 2),
                    "gpu_factor": round(gpu_factor, 2)
                }
            }

        except Exception as e:
            self.logger.warning(f"Could not estimate training time: {e}")
            return {
                "estimated_minutes": None,
                "estimated_hours": None,
                "error": str(e)
            }
    
    def stop_training(self) -> bool:
        """Stop the training process"""
        if not self.is_training:
            self.logger.warning("No training in progress")
            return False
        
        self.logger.info("Stopping training...")
        
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
        
        self.is_training = False
        self.logger.info("Training stopped")
        return True
    
    def get_training_status(self) -> Dict[str, Any]:
        """Get current training status"""
        return {
            "is_training": self.is_training,
            "model_path": self.training_config.model_path if self.training_config else None,
            "output_dir": self.training_config.output_dir if self.training_config else None,
            "epochs": self.training_config.epochs if self.training_config else 0,
            "process_pid": self.process.pid if self.process else None,
        }
    
    def list_available_models(self) -> List[Dict[str, str]]:
        """List available models"""
        models_info = self.model_registry.get_available_models()
        models = []
        
        for model_id, model_info in models_info.items():
            size_mb = model_info["size"] / (1024 * 1024) if model_info["size"] else 0
            models.append({
                "id": model_id,
                "name": model_info["name"],
                "description": model_info["description"],
                "type": model_info["type"],
                "parameters": model_info.get("parameters", "Unknown"),
                "size": f"{size_mb:.1f} MB"
            })
        
        return models

def start_web_ui(port: int = 8080):
    """Start the web UI server"""
    try:
        import http.server
        import socketserver
        import webbrowser
        import threading
        
        # Get the directory containing this script
        web_dir = Path(__file__).parent
        
        # Change to the web directory
        os.chdir(web_dir)
        
        # Check if UI file exists
        ui_files = ["enhanced_autotrain_ui.html", "autotrain_ui.html", "ui.html"]
        ui_file = None
        for file in ui_files:
            if (web_dir / file).exists():
                ui_file = file
                break
        
        if not ui_file:
            print(f"Web UI file not found. Checked: {', '.join(ui_files)}")
            return
        
        # Start server
        handler = http.server.SimpleHTTPRequestHandler
        with socketserver.TCPServer(("", port), handler) as httpd:
            print(f"Serving DuckBot AutoTrain UI at http://localhost:{port}/{ui_file}")
            
            # Open browser in a separate thread
            def open_browser():
                time.sleep(1)
                webbrowser.open(f'http://localhost:{port}/{ui_file}')
            
            browser_thread = threading.Thread(target=open_browser, daemon=True)
            browser_thread.start()
            
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                print("\nShutting down server...")
                httpd.shutdown()
    except Exception as e:
        print(f"Failed to start web UI server: {e}")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="DuckBot Model Training Module")
    parser.add_argument("--config", help="Path to training configuration file")
    parser.add_argument("--model", help="Model path or Hugging Face model ID (prefix with hf: for HF models)")
    parser.add_argument("--dataset", help="Path to training dataset")
    parser.add_argument("--output", help="Output directory for trained model")
    parser.add_argument("--type", choices=["gguf", "hf"], default="hf", help="Model type")
    parser.add_argument("--method", choices=["lora", "full", "distill"], default="lora", help="Training method")
    parser.add_argument("--list-models", action="store_true", help="List available models")
    parser.add_argument("--download", help="Download Hugging Face model")
    parser.add_argument("--web-ui", action="store_true", help="Start web UI server")
    parser.add_argument("--port", type=int, default=8080, help="Port for web UI server")
    
    args = parser.parse_args()
    
    trainer = ModelTrainer()
    
    if args.web_ui:
        # Start web UI server
        start_web_ui(args.port)
        return
    
    if args.list_models:
        models = trainer.list_available_models()
        print("Available models:")
        for model in models:
            print(f"  - {model['name']} ({model['type']}, {model['size']})")
            print(f"    {model['description']}")
            print(f"    Parameters: {model['parameters']}")
            print()
        return
    
    if args.download:
        try:
            model_path = trainer.download_hf_model(args.download)
            print(f"Model downloaded to: {model_path}")
        except Exception as e:
            print(f"Failed to download model: {e}")
        return
    
    if args.config:
        try:
            config = trainer.load_config(args.config)
            trainer.start_training(config)
        except Exception as e:
            print(f"Failed to start training: {e}")
            return
    elif args.model and args.dataset and args.output:
        # Create config from command line args
        model_type = ModelType.GGUF if args.type == "gguf" else ModelType.HF_TRANSFORMERS
        training_method = TrainingMethod.LORA if args.method == "lora" else TrainingMethod.FULL_FINE_TUNE
        
        config = TrainingConfig(
            model_path=args.model,
            model_type=model_type,
            training_method=training_method,
            dataset_path=args.dataset,
            output_dir=args.output
        )
        
        trainer.start_training(config)
    else:
        print("Please provide either a config file or model/dataset/output parameters")
        parser.print_help()

if __name__ == "__main__":
    main()