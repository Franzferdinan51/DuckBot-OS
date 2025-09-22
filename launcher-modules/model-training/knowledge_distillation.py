#!/usr/bin/env python3
"""
Knowledge Distillation Module
Implements various knowledge distillation techniques for model training
Supports teacher-student architectures, temperature scaling, and model compression
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

class DistillationMethod(Enum):
    """Knowledge distillation methods"""
    STANDARD = "standard"  # Standard KL divergence distillation
    ATTENTION = "attention"  # Attention transfer
    HINT = "hint"  # Hint-based distillation
    FEATURE = "feature"  # Feature matching
    RELATION = "relation"  # Relation-based distillation
    DATA_FREE = "data_free"  # Data-free distillation
    SELF = "self"  # Self-distillation

class CompressionTechnique(Enum):
    """Model compression techniques"""
    PRUNING = "pruning"
    QUANTIZATION = "quantization"
    LOW_RANK = "low_rank"
    KNOWLEDGE_DISTILLATION = "knowledge_distillation"

@dataclass
class DistillationConfig:
    """Configuration for knowledge distillation"""
    teacher_model_path: str
    student_model_path: str
    output_dir: str
    distillation_method: DistillationMethod = DistillationMethod.STANDARD
    temperature: float = 2.0
    alpha: float = 0.5  # Weight for distillation loss vs hard labels
    beta: float = 0.5   # Weight for auxiliary losses (attention, features, etc.)
    epochs: int = 5
    learning_rate: float = 5e-5
    batch_size: int = 8
    max_seq_length: int = 512
    save_steps: int = 500
    logging_steps: int = 50
    eval_steps: int = 500
    warmup_steps: int = 100
    weight_decay: float = 0.01
    max_grad_norm: float = 1.0
    compression_techniques: List[CompressionTechnique] = None
    compression_ratio: float = 0.5  # Target compression ratio
    use_attention_transfer: bool = False
    use_feature_matching: bool = False
    intermediate_layer_mapping: Dict[int, int] = None
    evaluation_metrics: List[str] = None

    def __post_init__(self):
        if self.compression_techniques is None:
            self.compression_techniques = [CompressionTechnique.KNOWLEDGE_DISTILLATION]
        if self.intermediate_layer_mapping is None:
            self.intermediate_layer_mapping = {}
        if self.evaluation_metrics is None:
            self.evaluation_metrics = ["accuracy", "perplexity", "bleu", "rouge"]

class KnowledgeDistiller:
    """Main knowledge distillation class"""

    def __init__(self, config: DistillationConfig):
        self.config = config
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.logger = self._setup_logger()

        # Initialize models
        self.teacher_model = None
        self.student_model = None
        self.teacher_tokenizer = None
        self.student_tokenizer = None

        # Training state
        self.training_history = []
        self.evaluation_results = {}

        self.logger.info("KnowledgeDistiller initialized")

    def _setup_logger(self) -> logging.Logger:
        """Setup logger for the distiller"""
        logger = logging.getLogger('DuckBot.KnowledgeDistiller')
        logger.setLevel(logging.INFO)

        # Create logs directory
        log_dir = Path(self.config.output_dir) / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)

        # File handler
        file_handler = logging.FileHandler(log_dir / "distillation.log", encoding='utf-8')
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

    def load_models(self):
        """Load teacher and student models"""
        self.logger.info("Loading teacher and student models...")

        # Load teacher model
        try:
            self.teacher_tokenizer = AutoTokenizer.from_pretrained(self.config.teacher_model_path)
            self.teacher_model = AutoModelForCausalLM.from_pretrained(
                self.config.teacher_model_path,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                device_map="auto"
            )
            self.teacher_model.eval()  # Set to evaluation mode
            self.logger.info(f"Teacher model loaded: {self.config.teacher_model_path}")
        except Exception as e:
            self.logger.error(f"Failed to load teacher model: {e}")
            raise

        # Load student model
        try:
            self.student_tokenizer = AutoTokenizer.from_pretrained(self.config.student_model_path)
            self.student_model = AutoModelForCausalLM.from_pretrained(
                self.config.student_model_path,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                device_map="auto"
            )
            self.logger.info(f"Student model loaded: {self.config.student_model_path}")
        except Exception as e:
            self.logger.error(f"Failed to load student model: {e}")
            raise

    def temperature_scaled_softmax(self, logits: torch.Tensor, temperature: float) -> torch.Tensor:
        """Apply temperature scaling to logits"""
        if temperature != 1.0:
            logits = logits / temperature
        return F.softmax(logits, dim=-1)

    def compute_kl_divergence_loss(
        self,
        teacher_logits: torch.Tensor,
        student_logits: torch.Tensor,
        temperature: float = 1.0
    ) -> torch.Tensor:
        """Compute KL divergence loss between teacher and student logits"""
        # Apply temperature scaling
        teacher_probs = self.temperature_scaled_softmax(teacher_logits, temperature)
        student_probs = self.temperature_scaled_softmax(student_logits, temperature)

        # Compute KL divergence
        kl_loss = F.kl_div(
            torch.log(student_probs + 1e-8),
            teacher_probs,
            reduction='batchmean'
        )

        return kl_loss * (temperature ** 2)

    def compute_attention_transfer_loss(
        self,
        teacher_attention: List[torch.Tensor],
        student_attention: List[torch.Tensor]
    ) -> torch.Tensor:
        """Compute attention transfer loss"""
        if not teacher_attention or not student_attention:
            return torch.tensor(0.0, device=self.device)

        total_loss = 0.0
        min_layers = min(len(teacher_attention), len(student_attention))

        for i in range(min_layers):
            # Get attention matrices
            teacher_att = teacher_attention[i]
            student_att = student_attention[i]

            # Normalize attention matrices
            teacher_att = F.normalize(teacher_att, p=2, dim=-1)
            student_att = F.normalize(student_att, p=2, dim=-1)

            # Compute MSE loss between attention matrices
            loss = F.mse_loss(student_att, teacher_att)
            total_loss += loss

        return total_loss / min_layers if min_layers > 0 else torch.tensor(0.0, device=self.device)

    def compute_feature_matching_loss(
        self,
        teacher_features: Dict[str, torch.Tensor],
        student_features: Dict[str, torch.Tensor]
    ) -> torch.Tensor:
        """Compute feature matching loss"""
        if not teacher_features or not student_features:
            return torch.tensor(0.0, device=self.device)

        total_loss = 0.0
        matched_layers = 0

        # Match features based on layer mapping
        for layer_name, teacher_feat in teacher_features.items():
            # Find corresponding student layer
            student_layer_name = layer_name.replace("teacher", "student")
            if student_layer_name in student_features:
                student_feat = student_features[student_layer_name]

                # Ensure same dimensions
                if teacher_feat.shape == student_feat.shape:
                    loss = F.mse_loss(student_feat, teacher_feat)
                    total_loss += loss
                    matched_layers += 1

        return total_loss / matched_layers if matched_layers > 0 else torch.tensor(0.0, device=self.device)

    def compute_distillation_loss(
        self,
        batch: Dict[str, torch.Tensor],
        return_all_losses: bool = False
    ) -> Union[torch.Tensor, Tuple[torch.Tensor, Dict[str, torch.Tensor]]]:
        """Compute total distillation loss"""
        # Get teacher outputs
        with torch.no_grad():
            teacher_outputs = self.teacher_model(**batch, output_attentions=True, output_hidden_states=True)
            teacher_logits = teacher_outputs.logits
            teacher_attention = teacher_outputs.attentions
            teacher_hidden_states = teacher_outputs.hidden_states

        # Get student outputs
        student_outputs = self.student_model(**batch, output_attentions=True, output_hidden_states=True)
        student_logits = student_outputs.logits
        student_attention = student_outputs.attentions
        student_hidden_states = student_outputs.hidden_states

        # Compute losses
        losses = {}

        # KL divergence loss
        kl_loss = self.compute_kl_divergence_loss(
            teacher_logits, student_logits, self.config.temperature
        )
        losses['kl_loss'] = kl_loss

        # Attention transfer loss
        if self.config.use_attention_transfer:
            attn_loss = self.compute_attention_transfer_loss(teacher_attention, student_attention)
            losses['attention_loss'] = attn_loss

        # Feature matching loss
        if self.config.use_feature_matching:
            # Extract features from hidden states
            teacher_features = {f'layer_{i}': state for i, state in enumerate(teacher_hidden_states)}
            student_features = {f'layer_{i}': state for i, state in enumerate(student_hidden_states)}

            feature_loss = self.compute_feature_matching_loss(teacher_features, student_features)
            losses['feature_loss'] = feature_loss

        # Hard label loss (if labels are available)
        if 'labels' in batch:
            labels = batch['labels']
            # Shift labels for causal language modeling
            shift_labels = labels[..., 1:].contiguous()
            shift_logits = student_logits[..., :-1, :].contiguous()

            # Compute cross-entropy loss
            ce_loss = F.cross_entropy(
                shift_logits.view(-1, shift_logits.size(-1)),
                shift_labels.view(-1),
                ignore_index=-100
            )
            losses['ce_loss'] = ce_loss

        # Combine losses
        total_loss = self.config.alpha * losses['kl_loss']

        if 'attention_loss' in losses:
            total_loss += self.config.beta * losses['attention_loss']

        if 'feature_loss' in losses:
            total_loss += self.config.beta * losses['feature_loss']

        if 'ce_loss' in losses:
            total_loss += (1 - self.config.alpha) * losses['ce_loss']

        if return_all_losses:
            return total_loss, losses
        else:
            return total_loss

    def create_student_architecture(self, architecture_type: str = "scaled_down"):
        """Create student architecture from teacher model"""
        if architecture_type == "scaled_down":
            return self._create_scaled_down_student()
        elif architecture_type == "pruned":
            return self._create_pruned_student()
        elif architecture_type == "low_rank":
            return self._create_low_rank_student()
        else:
            raise ValueError(f"Unknown architecture type: {architecture_type}")

    def _create_scaled_down_student(self):
        """Create a scaled-down version of the teacher model"""
        # This is a simplified example - in practice, you'd need to carefully design
        # the student architecture to maintain performance while reducing size

        # For now, we'll just use the existing student model
        # In a real implementation, you might:
        # 1. Reduce the number of layers
        # 2. Reduce hidden dimension size
        # 3. Reduce number of attention heads
        # 4. Reduce FFN dimension

        return self.student_model

    def _create_pruned_student(self):
        """Create a pruned version of the teacher model"""
        # Implement model pruning
        # This would involve magnitude-based pruning, structured pruning, etc.

        # For now, return the existing student model
        return self.student_model

    def _create_low_rank_student(self):
        """Create a low-rank approximation of the teacher model"""
        # Implement low-rank factorization
        # This would involve SVD decomposition of weight matrices

        # For now, return the existing student model
        return self.student_model

    def apply_compression(self):
        """Apply compression techniques to the student model"""
        for technique in self.config.compression_techniques:
            if technique == CompressionTechnique.PRUNING:
                self._apply_pruning()
            elif technique == CompressionTechnique.QUANTIZATION:
                self._apply_quantization()
            elif technique == CompressionTechnique.LOW_RANK:
                self._apply_low_rank_factorization()

    def _apply_pruning(self):
        """Apply model pruning"""
        # Implement magnitude-based pruning
        parameters_to_prune = []
        for name, module in self.student_model.named_modules():
            if isinstance(module, nn.Linear):
                parameters_to_prune.append((module, 'weight'))

        # Calculate pruning amount based on compression ratio
        amount = 1.0 - self.config.compression_ratio

        # Apply pruning
        for module, param_name in parameters_to_prune:
            # Get parameter values
            param = getattr(module, param_name)

            # Calculate threshold
            param_flat = param.data.abs().view(-1)
            threshold = torch.kthvalue(param_flat, int(len(param_flat) * amount))[0]

            # Apply pruning mask
            mask = param.data.abs() > threshold
            param.data *= mask.float()

        self.logger.info(f"Applied pruning with compression ratio: {self.config.compression_ratio}")

    def _apply_quantization(self):
        """Apply model quantization"""
        # Implement quantization
        # This would involve converting weights to lower precision

        # For now, just log the intent
        self.logger.info("Applied quantization (placeholder implementation)")

    def _apply_low_rank_factorization(self):
        """Apply low-rank factorization"""
        # Implement low-rank factorization using SVD
        for name, module in self.student_model.named_modules():
            if isinstance(module, nn.Linear):
                # Get weight matrix
                weight = module.weight.data

                # Perform SVD
                U, S, V = torch.svd(weight)

                # Calculate target rank based on compression ratio
                target_rank = int(min(weight.shape) * self.config.compression_ratio)

                # Reconstruct with reduced rank
                U_reduced = U[:, :target_rank]
                S_reduced = torch.diag(S[:target_rank])
                V_reduced = V[:, :target_rank]

                # Update weight
                module.weight.data = torch.mm(U_reduced, torch.mm(S_reduced, V_reduced.t()))

        self.logger.info(f"Applied low-rank factorization with compression ratio: {self.config.compression_ratio}")

    def evaluate_distilled_model(self, eval_dataset) -> Dict[str, float]:
        """Evaluate the distilled model"""
        self.logger.info("Evaluating distilled model...")

        # Set model to evaluation mode
        self.student_model.eval()

        evaluation_results = {}

        # Create data loader
        eval_dataloader = DataLoader(eval_dataset, batch_size=self.config.batch_size, shuffle=False)

        total_loss = 0.0
        total_samples = 0

        with torch.no_grad():
            for batch in eval_dataloader:
                # Move batch to device
                batch = {k: v.to(self.device) for k, v in batch.items()}

                # Get model outputs
                outputs = self.student_model(**batch)

                # Compute loss if labels are available
                if 'labels' in batch:
                    labels = batch['labels']
                    shift_labels = labels[..., 1:].contiguous()
                    shift_logits = outputs.logits[..., :-1, :].contiguous()

                    loss = F.cross_entropy(
                        shift_logits.view(-1, shift_logits.size(-1)),
                        shift_labels.view(-1),
                        ignore_index=-100
                    )

                    total_loss += loss.item() * len(labels)
                    total_samples += len(labels)

        # Calculate average loss
        avg_loss = total_loss / total_samples if total_samples > 0 else float('inf')
        perplexity = torch.exp(torch.tensor(avg_loss)).item()

        evaluation_results['eval_loss'] = avg_loss
        evaluation_results['eval_perplexity'] = perplexity

        self.logger.info(f"Evaluation results: {evaluation_results}")
        return evaluation_results

    def save_distilled_model(self, save_directory: str):
        """Save the distilled model and configuration"""
        save_path = Path(save_directory)
        save_path.mkdir(parents=True, exist_ok=True)

        # Save model
        self.student_model.save_pretrained(save_path)

        # Save tokenizer
        self.student_tokenizer.save_pretrained(save_path)

        # Save configuration
        config_dict = asdict(self.config)
        config_dict['distillation_method'] = config_dict['distillation_method'].value
        config_dict['compression_techniques'] = [tech.value for tech in config_dict['compression_techniques']]

        with open(save_path / "distillation_config.json", "w") as f:
            json.dump(config_dict, f, indent=2)

        # Save training history
        with open(save_path / "distillation_history.json", "w") as f:
            json.dump(self.training_history, f, indent=2)

        # Save evaluation results
        with open(save_path / "evaluation_results.json", "w") as f:
            json.dump(self.evaluation_results, f, indent=2)

        self.logger.info(f"Distilled model saved to {save_path}")

    def distill(self, train_dataset, eval_dataset=None):
        """Main distillation method"""
        self.logger.info("Starting knowledge distillation...")

        # Load models
        self.load_models()

        # Apply compression if requested
        if CompressionTechnique.KNOWLEDGE_DISTILLATION not in self.config.compression_techniques:
            self.apply_compression()

        # Create data loaders
        train_dataloader = DataLoader(
            train_dataset,
            batch_size=self.config.batch_size,
            shuffle=True
        )

        # Setup optimizer
        optimizer = torch.optim.AdamW(
            self.student_model.parameters(),
            lr=self.config.learning_rate,
            weight_decay=self.config.weight_decay
        )

        # Setup learning rate scheduler
        scheduler = torch.optim.lr_scheduler.LinearLR(
            optimizer,
            start_factor=0.1,
            end_factor=1.0,
            total_iters=self.config.warmup_steps
        )

        # Training loop
        self.student_model.train()

        for epoch in range(self.config.epochs):
            epoch_loss = 0.0
            num_batches = 0

            for step, batch in enumerate(train_dataloader):
                # Move batch to device
                batch = {k: v.to(self.device) for k, v in batch.items()}

                # Zero gradients
                optimizer.zero_grad()

                # Compute distillation loss
                loss = self.compute_distillation_loss(batch)

                # Backward pass
                loss.backward()

                # Gradient clipping
                torch.nn.utils.clip_grad_norm_(
                    self.student_model.parameters(),
                    self.config.max_grad_norm
                )

                # Update parameters
                optimizer.step()

                # Update learning rate
                scheduler.step()

                # Update loss
                epoch_loss += loss.item()
                num_batches += 1

                # Logging
                if step % self.config.logging_steps == 0:
                    avg_loss = epoch_loss / num_batches
                    self.logger.info(
                        f"Epoch {epoch+1}/{self.config.epochs}, "
                        f"Step {step}/{len(train_dataloader)}, "
                        f"Loss: {avg_loss:.4f}"
                    )

                # Save checkpoint
                if step % self.config.save_steps == 0:
                    checkpoint_path = Path(self.config.output_dir) / f"checkpoint-epoch-{epoch+1}-step-{step}"
                    self.save_distilled_model(checkpoint_path)

            # Calculate average epoch loss
            avg_epoch_loss = epoch_loss / num_batches if num_batches > 0 else float('inf')

            # Record training history
            epoch_history = {
                "epoch": epoch + 1,
                "loss": avg_epoch_loss,
                "learning_rate": optimizer.param_groups[0]['lr']
            }
            self.training_history.append(epoch_history)

            self.logger.info(f"Epoch {epoch+1} completed. Average loss: {avg_epoch_loss:.4f}")

            # Evaluate if evaluation dataset is provided
            if eval_dataset is not None and (epoch + 1) % self.config.eval_steps == 0:
                eval_results = self.evaluate_distilled_model(eval_dataset)
                self.evaluation_results[f"epoch_{epoch+1}"] = eval_results

        # Save final model
        self.save_distilled_model(self.config.output_dir)

        self.logger.info("Knowledge distillation completed successfully")

        return {
            "training_history": self.training_history,
            "evaluation_results": self.evaluation_results
        }

def create_distillation_config_from_dict(config_dict: Dict[str, Any]) -> DistillationConfig:
    """Create DistillationConfig from dictionary"""
    # Convert string enums to enum objects
    if 'distillation_method' in config_dict:
        config_dict['distillation_method'] = DistillationMethod(config_dict['distillation_method'])

    if 'compression_techniques' in config_dict and isinstance(config_dict['compression_techniques'], list):
        config_dict['compression_techniques'] = [
            CompressionTechnique(tech) for tech in config_dict['compression_techniques']
        ]

    return DistillationConfig(**config_dict)

def main():
    """Example usage of the knowledge distillation module"""
    # Example configuration
    config = DistillationConfig(
        teacher_model_path="microsoft/DialoGPT-medium",
        student_model_path="microsoft/DialoGPT-small",
        output_dir="./distilled_models",
        distillation_method=DistillationMethod.STANDARD,
        temperature=2.0,
        alpha=0.5,
        epochs=3,
        learning_rate=5e-5,
        batch_size=4,
        use_attention_transfer=True,
        use_feature_matching=True
    )

    # Create distiller
    distiller = KnowledgeDistiller(config)

    # Note: In practice, you would need to provide actual datasets
    # train_dataset = ...
    # eval_dataset = ...

    # Run distillation
    # results = distiller.distill(train_dataset, eval_dataset)

    print("Knowledge distillation module initialized successfully")
    print(f"Configuration: {config}")

if __name__ == "__main__":
    main()