#!/usr/bin/env python3
"""
Enhanced Knowledge Distillation Trainer
Integrates all distillation components with the existing training infrastructure
"""

import os
import sys
import json
import time
import logging
import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Union, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader
import transformers
from transformers import (
    AutoModelForCausalLM, AutoTokenizer, AutoModelForSequenceClassification,
    Trainer, TrainingArguments, PreTrainedModel, PreTrainedTokenizer
)

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import our distillation modules
from knowledge_distillation import KnowledgeDistiller, DistillationConfig, DistillationMethod
from temperature_scaling import TemperatureScaler, TemperatureConfig, TemperatureMethod
from distillation_loss_functions import (
    BaseDistillationLoss, DistillationLossType, ComposedDistillationLoss,
    LossWeights, DistillationOptimizer, OptimizationStrategy
)
from teacher_student_models import (
    TeacherStudentManager, TeacherStudentConfig, ModelType, ArchitectureStrategy
)
from model_compression import (
    ModelCompressor, CompressionConfig, CompressionType, PruningType, QuantizationType
)
from distillation_evaluation import (
    DistillationEvaluator, EvaluationConfig, EvaluationMetric, TaskType
)

# Import existing training infrastructure
try:
    from model_trainer import GGUFTrainingConfig, TrainingMethod
    from advanced_trainer import AdvancedTrainer
    EXISTING_INFRASTRUCTURE_AVAILABLE = True
except ImportError:
    EXISTING_INFRASTRUCTURE_AVAILABLE = False
    # Fallback implementations
    class GGUFTrainingConfig:
        pass
    class TrainingMethod:
        DISTILLATION = "distillation"


@dataclass
class EnhancedDistillationConfig:
    """Enhanced configuration for knowledge distillation"""
    # Teacher-Student Configuration
    teacher_model_path: str
    student_model_path: Optional[str] = None
    model_type: ModelType = ModelType.GPT2
    architecture_strategy: ArchitectureStrategy = ArchitectureStrategy.SCALING
    scaling_factor: float = 0.5

    # Distillation Configuration
    distillation_method: DistillationMethod = DistillationMethod.STANDARD
    loss_type: DistillationLossType = DistillationLossType.KL_DIVERGENCE
    temperature: float = 2.0
    alpha: float = 0.5
    beta: float = 0.3

    # Temperature Scaling Configuration
    temperature_method: TemperatureMethod = TemperatureMethod.FIXED
    adaptive_temperature: bool = False
    temperature_schedule: str = "constant"

    # Loss Weights
    loss_weights: LossWeights = None

    # Training Configuration
    epochs: int = 5
    learning_rate: float = 5e-5
    batch_size: int = 8
    max_seq_length: int = 512
    gradient_accumulation_steps: int = 4

    # Optimization Configuration
    optimization_strategy: OptimizationStrategy = OptimizationStrategy.ADAMW
    weight_decay: float = 0.01
    max_grad_norm: float = 1.0
    warmup_steps: int = 100

    # Model Compression
    enable_compression: bool = False
    compression_type: CompressionType = CompressionType.PRUNING
    compression_ratio: float = 0.5
    quantization_type: QuantizationType = QuantizationType.DYNAMIC

    # Evaluation Configuration
    evaluation_metrics: List[EvaluationMetric] = None
    evaluation_interval: int = 500

    # Output Configuration
    output_dir: str
    save_steps: int = 500
    logging_steps: int = 50

    # Multi-Teacher Configuration
    multi_teacher: bool = False
    teacher_model_paths: List[str] = None
    teacher_weights: List[float] = None

    def __post_init__(self):
        """Post-initialization setup"""
        if self.loss_weights is None:
            self.loss_weights = LossWeights()

        if self.evaluation_metrics is None:
            self.evaluation_metrics = [
                EvaluationMetric.ACCURACY,
                EvaluationMetric.DISTILLATION_QUALITY,
                EvaluationMetric.EFFICIENCY
            ]

        if self.multi_teacher and self.teacher_model_paths is None:
            self.teacher_model_paths = [self.teacher_model_path]

        # Create output directory
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)


class EnhancedDistillationTrainer:
    """Enhanced knowledge distillation trainer with integrated components"""

    def __init__(self, config: EnhancedDistillationConfig):
        self.config = config
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.logger = self._setup_logger()

        # Initialize components
        self.teacher_student_manager = TeacherStudentManager()
        self.temperature_scaler = TemperatureScaler(
            TemperatureConfig(
                method=config.temperature_method,
                initial_temperature=config.temperature,
                temperature_schedule=config.temperature_schedule
            )
        )
        self.distillation_loss = self._create_distillation_loss()
        self.model_compressor = None
        self.distillation_evaluator = None

        # Model storage
        self.teacher_model = None
        self.student_model = None
        self.teacher_tokenizer = None
        self.student_tokenizer = None

        # Training state
        self.training_history = []
        self.evaluation_results = {}
        self.best_score = float('-inf')

        self.logger.info("EnhancedDistillationTrainer initialized")

    def _setup_logger(self) -> logging.Logger:
        """Setup comprehensive logging"""
        logger = logging.getLogger('DuckBot.EnhancedDistillationTrainer')
        logger.setLevel(logging.INFO)

        # Create logs directory
        log_dir = Path(self.config.output_dir) / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)

        # File handler
        file_handler = logging.FileHandler(log_dir / "distillation_training.log", encoding='utf-8')
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

    def _create_distillation_loss(self) -> BaseDistillationLoss:
        """Create distillation loss function based on configuration"""
        if self.config.loss_type == DistillationLossType.KL_DIVERGENCE:
            from distillation_loss_functions import KLDivergenceLoss
            return KLDivergenceLoss(self.config.temperature, self.config.alpha)
        elif self.config.loss_type == DistillationLossType.JS_DIVERGENCE:
            from distillation_loss_functions import JSDivergenceLoss
            return JSDivergenceLoss(self.config.temperature, self.config.alpha)
        elif self.config.loss_type == DistillationLossType.ATTENTION_TRANSFER:
            from distillation_loss_functions import AttentionTransferLoss
            return AttentionTransferLoss(self.config.temperature, self.config.alpha)
        elif self.config.loss_type == DistillationLossType.FEATURE_MATCHING:
            from distillation_loss_functions import FeatureMatchingLoss
            return FeatureMatchingLoss(self.config.temperature, self.config.alpha)
        elif self.config.loss_type == DistillationLossType.RELATIONSHIP:
            from distillation_loss_functions import RelationshipDistillationLoss
            return RelationshipDistillationLoss(self.config.temperature, self.config.alpha)
        elif self.config.loss_type == DistillationLossType.VARIATIONAL:
            from distillation_loss_functions import VariationalDistillationLoss
            return VariationalDistillationLoss(self.config.temperature, self.config.alpha)
        else:
            # Use composed loss with multiple components
            return ComposedDistillationLoss(
                temperature=self.config.temperature,
                alpha=self.config.alpha,
                loss_weights=self.config.loss_weights
            )

    def load_models(self):
        """Load teacher and student models"""
        self.logger.info("Loading teacher and student models...")

        # Load teacher model
        try:
            self.teacher_model = self.teacher_student_manager.load_teacher_model(
                self.config.teacher_model_path, self.config.model_type
            )
            self.teacher_tokenizer = AutoTokenizer.from_pretrained(self.config.teacher_model_path)
            if self.teacher_tokenizer.pad_token is None:
                self.teacher_tokenizer.pad_token = self.teacher_tokenizer.eos_token

            self.logger.info(f"Teacher model loaded: {self.config.teacher_model_path}")
        except Exception as e:
            self.logger.error(f"Failed to load teacher model: {e}")
            raise

        # Create student model
        teacher_student_config = TeacherStudentConfig(
            teacher_model_path=self.config.teacher_model_path,
            student_model_path=self.config.student_model_path,
            model_type=self.config.model_type,
            architecture_strategy=self.config.architecture_strategy,
            scaling_factor=self.config.scaling_factor
        )

        try:
            self.student_model = self.teacher_student_manager.create_student_model(teacher_student_config)
            self.student_tokenizer = AutoTokenizer.from_pretrained(self.config.teacher_model_path)
            if self.student_tokenizer.pad_token is None:
                self.student_tokenizer.pad_token = self.student_tokenizer.eos_token

            self.logger.info("Student model created successfully")
        except Exception as e:
            self.logger.error(f"Failed to create student model: {e}")
            raise

        # Move models to device
        self.teacher_model.to(self.device)
        self.student_model.to(self.device)

        # Initialize model compressor if enabled
        if self.config.enable_compression:
            compression_config = CompressionConfig(
                compression_type=self.config.compression_type,
                target_ratio=self.config.compression_ratio,
                quantization_type=self.config.quantization_type
            )
            self.model_compressor = ModelCompressor(self.student_model, compression_config)

        # Initialize evaluator
        eval_config = EvaluationConfig(
            metrics=self.config.evaluation_metrics,
            task_type=TaskType.CLASSIFICATION,
            compute_efficiency=True,
            compute_calibration=True
        )
        self.distillation_evaluator = DistillationEvaluator(eval_config)

    def prepare_data(self, dataset_path: str) -> Tuple[DataLoader, DataLoader]:
        """Prepare training and validation data"""
        self.logger.info(f"Preparing dataset from: {dataset_path}")

        try:
            # Load dataset based on file format
            dataset_path = Path(dataset_path)

            if dataset_path.suffix == '.json':
                with open(dataset_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            elif dataset_path.suffix == '.jsonl':
                data = []
                with open(dataset_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        data.append(json.loads(line.strip()))
            else:
                raise ValueError(f"Unsupported dataset format: {dataset_path.suffix}")

            # Process data for training
            processed_data = []
            for example in data:
                if isinstance(example, dict):
                    if 'text' in example:
                        text = example['text']
                    elif 'instruction' in example and 'response' in example:
                        text = f"### Instruction:\n{example['instruction']}\n\n### Response:\n{example['response']}"
                    else:
                        continue

                    if len(text) > 50:  # Filter short examples
                        processed_data.append(text)

            self.logger.info(f"Processed {len(processed_data)} training examples")

            # Create tokenized dataset
            def tokenize_function(texts):
                return self.student_tokenizer(
                    texts,
                    truncation=True,
                    padding=True,
                    max_length=self.config.max_seq_length,
                    return_tensors="pt"
                )

            # Split data
            split_idx = int(len(processed_data) * 0.9)
            train_texts = processed_data[:split_idx]
            val_texts = processed_data[split_idx:]

            # Tokenize
            train_encodings = tokenize_function(train_texts)
            val_encodings = tokenize_function(val_texts)

            # Create datasets
            class TextDataset(torch.utils.data.Dataset):
                def __init__(self, encodings):
                    self.encodings = encodings

                def __getitem__(self, idx):
                    return {
                        'input_ids': self.encodings['input_ids'][idx],
                        'attention_mask': self.encodings['attention_mask'][idx],
                        'labels': self.encodings['input_ids'][idx].clone()
                    }

                def __len__(self):
                    return len(self.encodings['input_ids'])

            train_dataset = TextDataset(train_encodings)
            val_dataset = TextDataset(val_encodings)

            # Create data loaders
            train_loader = DataLoader(
                train_dataset,
                batch_size=self.config.batch_size,
                shuffle=True,
                num_workers=2
            )

            val_loader = DataLoader(
                val_dataset,
                batch_size=self.config.batch_size,
                shuffle=False,
                num_workers=2
            )

            self.logger.info(f"Created data loaders: {len(train_loader)} train batches, {len(val_loader)} val batches")
            return train_loader, val_loader

        except Exception as e:
            self.logger.error(f"Failed to prepare data: {e}")
            raise

    def train_epoch(self, train_loader: DataLoader, optimizer: torch.optim.Optimizer,
                   scheduler: torch.optim.lr_scheduler._LRScheduler, epoch: int) -> Dict[str, float]:
        """Train for one epoch"""
        self.student_model.train()
        self.teacher_model.eval()

        total_loss = 0.0
        total_distillation_loss = 0.0
        total_task_loss = 0.0
        num_batches = 0

        for batch_idx, batch in enumerate(train_loader):
            # Move batch to device
            batch = {k: v.to(self.device) for k, v in batch.items()}

            # Zero gradients
            optimizer.zero_grad()

            # Get teacher outputs
            with torch.no_grad():
                teacher_outputs = self.teacher_model(
                    input_ids=batch['input_ids'],
                    attention_mask=batch['attention_mask'],
                    output_attentions=True,
                    output_hidden_states=True
                )

            # Get student outputs
            student_outputs = self.student_model(
                input_ids=batch['input_ids'],
                attention_mask=batch['attention_mask'],
                output_attentions=True,
                output_hidden_states=True
            )

            # Compute distillation loss
            distillation_loss = self.distillation_loss.compute_loss(
                self._format_outputs(teacher_outputs),
                self._format_outputs(student_outputs),
                labels=batch.get('labels')
            )

            # Compute task loss (language modeling)
            task_loss = self._compute_task_loss(student_outputs, batch)

            # Combine losses
            total_batch_loss = self.config.alpha * distillation_loss + (1 - self.config.alpha) * task_loss

            # Backward pass
            total_batch_loss.backward()

            # Gradient clipping
            torch.nn.utils.clip_grad_norm_(self.student_model.parameters(), self.config.max_grad_norm)

            # Update parameters
            optimizer.step()
            scheduler.step()

            # Update statistics
            total_loss += total_batch_loss.item()
            total_distillation_loss += distillation_loss.item()
            total_task_loss += task_loss.item()
            num_batches += 1

            # Logging
            if batch_idx % self.config.logging_steps == 0:
                avg_loss = total_loss / num_batches
                self.logger.info(
                    f"Epoch {epoch+1}/{self.config.epochs}, "
                    f"Batch {batch_idx}/{len(train_loader)}, "
                    f"Loss: {avg_loss:.4f}, "
                    f"Distill: {total_distillation_loss/num_batches:.4f}, "
                    f"Task: {total_task_loss/num_batches:.4f}"
                )

        return {
            "total_loss": total_loss / num_batches,
            "distillation_loss": total_distillation_loss / num_batches,
            "task_loss": total_task_loss / num_batches,
            "learning_rate": optimizer.param_groups[0]['lr']
        }

    def _format_outputs(self, outputs) -> Dict[str, torch.Tensor]:
        """Format model outputs for distillation loss computation"""
        formatted = {
            'logits': outputs.logits
        }

        if hasattr(outputs, 'attentions') and outputs.attentions:
            formatted['attentions'] = outputs.attentions

        if hasattr(outputs, 'hidden_states') and outputs.hidden_states:
            formatted['hidden_states'] = outputs.hidden_states

        return formatted

    def _compute_task_loss(self, outputs, batch) -> torch.Tensor:
        """Compute task-specific loss (language modeling)"""
        logits = outputs.logits
        labels = batch['labels']

        # Shift labels for causal language modeling
        shift_logits = logits[..., :-1, :].contiguous()
        shift_labels = labels[..., 1:].contiguous()

        # Compute cross-entropy loss
        loss = F.cross_entropy(
            shift_logits.view(-1, shift_logits.size(-1)),
            shift_labels.view(-1),
            ignore_index=-100
        )

        return loss

    def evaluate_model(self, val_loader: DataLoader) -> Dict[str, float]:
        """Evaluate model performance"""
        self.student_model.eval()
        self.teacher_model.eval()

        total_loss = 0.0
        num_batches = 0

        with torch.no_grad():
            for batch in val_loader:
                batch = {k: v.to(self.device) for k, v in batch.items()}

                # Student outputs
                student_outputs = self.student_model(
                    input_ids=batch['input_ids'],
                    attention_mask=batch['attention_mask']
                )

                # Compute loss
                task_loss = self._compute_task_loss(student_outputs, batch)
                total_loss += task_loss.item()
                num_batches += 1

        avg_loss = total_loss / num_batches
        perplexity = torch.exp(torch.tensor(avg_loss)).item()

        return {
            "eval_loss": avg_loss,
            "eval_perplexity": perplexity
        }

    def compress_model(self) -> Dict[str, Any]:
        """Apply model compression if enabled"""
        if not self.config.enable_compression or self.model_compressor is None:
            return {"compression_applied": False}

        self.logger.info("Applying model compression...")

        try:
            compressed_model, compression_stats = self.model_compressor.compress_model()
            self.student_model = compressed_model

            self.logger.info(f"Compression completed: {compression_stats}")
            return compression_stats
        except Exception as e:
            self.logger.error(f"Compression failed: {e}")
            return {"compression_applied": False, "error": str(e)}

    def save_checkpoint(self, epoch: int, optimizer: torch.optim.Optimizer,
                       scheduler: torch.optim.lr_scheduler._LRScheduler,
                       metrics: Dict[str, float]):
        """Save training checkpoint"""
        checkpoint_dir = Path(self.config.output_dir) / f"checkpoint-epoch-{epoch+1}"
        checkpoint_dir.mkdir(parents=True, exist_ok=True)

        # Save models
        self.student_model.save_pretrained(checkpoint_dir / "student_model")
        if self.teacher_tokenizer:
            self.teacher_tokenizer.save_pretrained(checkpoint_dir / "tokenizer")

        # Save optimizer and scheduler states
        torch.save(optimizer.state_dict(), checkpoint_dir / "optimizer.pt")
        torch.save(scheduler.state_dict(), checkpoint_dir / "scheduler.pt")

        # Save training state
        training_state = {
            "epoch": epoch,
            "config": asdict(self.config),
            "metrics": metrics,
            "training_history": self.training_history,
            "evaluation_results": self.evaluation_results
        }

        with open(checkpoint_dir / "training_state.json", "w") as f:
            json.dump(training_state, f, indent=2, default=str)

        self.logger.info(f"Checkpoint saved to {checkpoint_dir}")

    def train(self, train_dataset_path: str, val_dataset_path: str = None):
        """Main training loop"""
        self.logger.info("Starting enhanced knowledge distillation training...")

        # Load models
        self.load_models()

        # Prepare data
        train_loader, val_loader = self.prepare_data(train_dataset_path)
        if val_dataset_path:
            _, val_loader = self.prepare_data(val_dataset_path)

        # Setup optimizer
        optimizer = torch.optim.AdamW(
            self.student_model.parameters(),
            lr=self.config.learning_rate,
            weight_decay=self.config.weight_decay
        )

        # Setup learning rate scheduler
        total_steps = len(train_loader) * self.config.epochs
        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
            optimizer,
            T_max=total_steps - self.config.warmup_steps
        )

        # Training loop
        self.logger.info(f"Starting training for {self.config.epochs} epochs...")

        for epoch in range(self.config.epochs):
            self.logger.info(f"Starting epoch {epoch+1}/{self.config.epochs}")

            # Train epoch
            epoch_metrics = self.train_epoch(train_loader, optimizer, scheduler, epoch)
            self.training_history.append(epoch_metrics)

            # Evaluate
            if val_loader:
                eval_metrics = self.evaluate_model(val_loader)
                self.logger.info(f"Epoch {epoch+1} evaluation: {eval_metrics}")

                # Update best score
                current_score = eval_metrics.get("eval_perplexity", float('inf'))
                if current_score < self.best_score:
                    self.best_score = current_score
                    self.save_checkpoint(epoch, optimizer, scheduler, {**epoch_metrics, **eval_metrics})

            # Save checkpoint
            if (epoch + 1) % self.config.save_steps == 0:
                self.save_checkpoint(epoch, optimizer, scheduler, epoch_metrics)

        # Apply compression if enabled
        compression_stats = self.compress_model()

        # Final evaluation
        if val_loader:
            final_eval = self.evaluate_model(val_loader)
            self.logger.info(f"Final evaluation: {final_eval}")

        # Save final model
        final_output_dir = Path(self.config.output_dir) / "final_model"
        self.student_model.save_pretrained(final_output_dir)
        if self.teacher_tokenizer:
            self.teacher_tokenizer.save_pretrained(final_output_dir)

        # Save training results
        results = {
            "training_history": self.training_history,
            "evaluation_results": self.evaluation_results,
            "compression_stats": compression_stats,
            "best_score": self.best_score,
            "final_evaluation": final_eval if val_loader else None
        }

        with open(Path(self.config.output_dir) / "training_results.json", "w") as f:
            json.dump(results, f, indent=2, default=str)

        self.logger.info("Training completed successfully!")
        return results

    def generate_training_report(self) -> str:
        """Generate comprehensive training report"""
        if not self.training_history:
            return "No training history available"

        report = f"""
Enhanced Knowledge Distillation Training Report
================================================

Configuration:
- Teacher Model: {self.config.teacher_model_path}
- Student Model: {self.config.student_model_path or 'Generated from teacher'}
- Architecture Strategy: {self.config.architecture_strategy.value}
- Scaling Factor: {self.config.scaling_factor}
- Distillation Method: {self.config.distillation_method.value}
- Loss Type: {self.config.loss_type.value}
- Temperature: {self.config.temperature}
- Alpha: {self.config.alpha}
- Epochs: {self.config.epochs}
- Learning Rate: {self.config.learning_rate}
- Batch Size: {self.config.batch_size}

Training Results:
- Total Epochs: {len(self.training_history)}
- Best Score: {self.best_score:.4f}
- Final Loss: {self.training_history[-1]['total_loss']:.4f}

Compression Results:
- Compression Applied: {self.config.enable_compression}
- Compression Type: {self.config.compression_type.value if self.config.enable_compression else 'N/A'}

Training History:
"""

        for i, epoch_data in enumerate(self.training_history):
            report += f"Epoch {i+1}: Loss={epoch_data['total_loss']:.4f}, " \
                     f"Distill={epoch_data['distillation_loss']:.4f}, " \
                     f"Task={epoch_data['task_loss']:.4f}, " \
                     f"LR={epoch_data['learning_rate']:.2e}\n"

        return report


def main():
    """Example usage of enhanced distillation trainer"""
    # Example configuration
    config = EnhancedDistillationConfig(
        teacher_model_path="gpt2",  # Using small GPT-2 for example
        model_type=ModelType.GPT2,
        architecture_strategy=ArchitectureStrategy.SCALING,
        scaling_factor=0.5,
        distillation_method=DistillationMethod.STANDARD,
        loss_type=DistillationLossType.KL_DIVERGENCE,
        temperature=2.0,
        alpha=0.5,
        epochs=3,
        learning_rate=5e-5,
        batch_size=4,
        output_dir="./distilled_models",
        enable_compression=True,
        compression_type=CompressionType.PRUNING,
        compression_ratio=0.3
    )

    # Create trainer
    trainer = EnhancedDistillationTrainer(config)

    print("Enhanced Knowledge Distillation Trainer initialized successfully")
    print(f"Configuration: {config}")

    # Note: In practice, you would need to provide actual dataset paths
    # results = trainer.train("path/to/train_dataset.json", "path/to/val_dataset.json")


if __name__ == "__main__":
    main()