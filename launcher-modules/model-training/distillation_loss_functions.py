#!/usr/bin/env python3
"""
Advanced Distillation Loss Functions and Optimization Strategies
Implements comprehensive loss functions and optimization techniques for knowledge distillation
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Union, Callable
from dataclasses import dataclass
from enum import Enum
import logging
import math
from abc import ABC, abstractmethod


class DistillationLossType(Enum):
    """Types of distillation loss functions"""
    KL_DIVERGENCE = "kl_divergence"
    JS_DIVERGENCE = "js_divergence"
    WASSERSTEIN = "wasserstein"
    HISTOGRAM = "histogram"
    ATTENTION_TRANSFER = "attention_transfer"
    FEATURE_MATCHING = "feature_matching"
    RELATIONSHIP = "relationship"
    HINT_BASED = "hint_based"
    VARIATIONAL = "variational"
    ADVERSARIAL = "adversarial"
    CONTRASTIVE = "contrastive"
    PROBABILITY_ALIGNMENT = "probability_alignment"


class OptimizationStrategy(Enum):
    """Optimization strategies for distillation"""
    ADAMW = "adamw"
    SGD_WITH_MOMENTUM = "sgd_momentum"
    ADAGRAD = "adagrad"
    RMSPROP = "rmsprop"
    LOOKAHEAD = "lookahead"
    SAM = "sam"
    ADAPTIVE_LR = "adaptive_lr"
    GRADIENT_CLIP = "gradient_clip"
    WARMUP_COSINE = "warmup_cosine"
    ONE_CYCLE = "one_cycle"


@dataclass
class LossWeights:
    """Weights for different loss components"""
    kl_weight: float = 1.0
    attention_weight: float = 0.5
    feature_weight: float = 0.5
    relationship_weight: float = 0.3
    hint_weight: float = 0.3
    adversarial_weight: float = 0.1
    contrastive_weight: float = 0.2
    task_weight: float = 1.0
    diversity_weight: float = 0.1


class BaseDistillationLoss(ABC):
    """Abstract base class for distillation loss functions"""

    def __init__(self, temperature: float = 2.0, alpha: float = 0.5):
        self.temperature = temperature
        self.alpha = alpha
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def compute_loss(self,
                    teacher_outputs: Dict[str, torch.Tensor],
                    student_outputs: Dict[str, torch.Tensor],
                    labels: Optional[torch.Tensor] = None) -> torch.Tensor:
        """Compute the distillation loss"""
        pass

    def temperature_scale(self, logits: torch.Tensor) -> torch.Tensor:
        """Apply temperature scaling to logits"""
        return logits / self.temperature

    def soft_targets(self, logits: torch.Tensor) -> torch.Tensor:
        """Compute soft targets from logits"""
        scaled_logits = self.temperature_scale(logits)
        return F.softmax(scaled_logits, dim=-1)


class KLDivergenceLoss(BaseDistillationLoss):
    """KL Divergence loss for knowledge distillation"""

    def compute_loss(self,
                    teacher_outputs: Dict[str, torch.Tensor],
                    student_outputs: Dict[str, torch.Tensor],
                    labels: Optional[torch.Tensor] = None) -> torch.Tensor:

        teacher_logits = teacher_outputs.get('logits')
        student_logits = student_outputs.get('logits')

        if teacher_logits is None or student_logits is None:
            raise ValueError("Logits not found in outputs")

        # Compute soft targets
        teacher_soft = self.soft_targets(teacher_logits)
        student_soft = self.soft_targets(student_logits)

        # Compute KL divergence
        kl_loss = F.kl_div(
            torch.log(student_soft + 1e-8),
            teacher_soft,
            reduction='batchmean'
        )

        # Apply temperature scaling
        kl_loss = kl_loss * (self.temperature ** 2)

        # Add task loss if labels are provided
        task_loss = torch.tensor(0.0, device=teacher_logits.device)
        if labels is not None:
            task_loss = F.cross_entropy(student_logits, labels)

        # Combine losses
        total_loss = self.alpha * kl_loss + (1 - self.alpha) * task_loss

        return total_loss


class JSDivergenceLoss(BaseDistillationLoss):
    """Jensen-Shannon Divergence loss"""

    def compute_loss(self,
                    teacher_outputs: Dict[str, torch.Tensor],
                    student_outputs: Dict[str, torch.Tensor],
                    labels: Optional[torch.Tensor] = None) -> torch.Tensor:

        teacher_logits = teacher_outputs.get('logits')
        student_logits = student_outputs.get('logits')

        teacher_soft = self.soft_targets(teacher_logits)
        student_soft = self.soft_targets(student_logits)

        # Compute average distribution
        avg_soft = 0.5 * (teacher_soft + student_soft)

        # Compute JS divergence
        js_loss = 0.5 * (
            F.kl_div(torch.log(teacher_soft + 1e-8), avg_soft, reduction='batchmean') +
            F.kl_div(torch.log(student_soft + 1e-8), avg_soft, reduction='batchmean')
        )

        return js_loss


class WassersteinLoss(BaseDistillationLoss):
    """Wasserstein distance loss"""

    def compute_loss(self,
                    teacher_outputs: Dict[str, torch.Tensor],
                    student_outputs: Dict[str, torch.Tensor],
                    labels: Optional[torch.Tensor] = None) -> torch.Tensor:

        teacher_logits = teacher_outputs.get('logits')
        student_logits = student_outputs.get('logits')

        teacher_soft = self.soft_targets(teacher_logits)
        student_soft = self.soft_targets(student_logits)

        # Sort probabilities for Wasserstein distance
        teacher_sorted = torch.sort(teacher_soft, dim=-1)[0]
        student_sorted = torch.sort(student_soft, dim=-1)[0]

        # Compute Wasserstein distance
        w_loss = torch.mean(torch.abs(teacher_sorted - student_sorted))

        return w_loss


class AttentionTransferLoss(BaseDistillationLoss):
    """Attention transfer loss"""

    def compute_loss(self,
                    teacher_outputs: Dict[str, torch.Tensor],
                    student_outputs: Dict[str, torch.Tensor],
                    labels: Optional[torch.Tensor] = None) -> torch.Tensor:

        teacher_attention = teacher_outputs.get('attentions', [])
        student_attention = student_outputs.get('attentions', [])

        if not teacher_attention or not student_attention:
            return torch.tensor(0.0, device=student_outputs['logits'].device)

        total_loss = 0.0
        num_layers = min(len(teacher_attention), len(student_attention))

        for i in range(num_layers):
            teacher_att = teacher_attention[i]
            student_att = student_attention[i]

            # Normalize attention matrices
            teacher_att = F.normalize(teacher_att, p=2, dim=-1)
            student_att = F.normalize(student_att, p=2, dim=-1)

            # Compute attention transfer loss
            layer_loss = F.mse_loss(student_att, teacher_att)
            total_loss += layer_loss

        return total_loss / num_layers


class FeatureMatchingLoss(BaseDistillationLoss):
    """Feature matching loss"""

    def compute_loss(self,
                    teacher_outputs: Dict[str, torch.Tensor],
                    student_outputs: Dict[str, torch.Tensor],
                    labels: Optional[torch.Tensor] = None) -> torch.Tensor:

        teacher_hidden = teacher_outputs.get('hidden_states', [])
        student_hidden = student_outputs.get('hidden_states', [])

        if not teacher_hidden or not student_hidden:
            return torch.tensor(0.0, device=student_outputs['logits'].device)

        total_loss = 0.0
        num_layers = min(len(teacher_hidden), len(student_hidden))

        for i in range(num_layers):
            teacher_feat = teacher_hidden[i]
            student_feat = student_hidden[i]

            # Adaptive layer matching
            if teacher_feat.shape != student_feat.shape:
                # Project to same dimension if needed
                if teacher_feat.size(-1) != student_feat.size(-1):
                    proj = nn.Linear(student_feat.size(-1), teacher_feat.size(-1)).to(student_feat.device)
                    student_feat = proj(student_feat)

            # Compute feature matching loss
            layer_loss = F.mse_loss(student_feat, teacher_feat)
            total_loss += layer_loss

        return total_loss / num_layers


class RelationshipDistillationLoss(BaseDistillationLoss):
    """Relationship-based distillation loss"""

    def compute_loss(self,
                    teacher_outputs: Dict[str, torch.Tensor],
                    student_outputs: Dict[str, torch.Tensor],
                    labels: Optional[torch.Tensor] = None) -> torch.Tensor:

        teacher_logits = teacher_outputs.get('logits')
        student_logits = student_outputs.get('logits')

        batch_size = teacher_logits.size(0)

        # Compute teacher relationships
        teacher_sim = torch.cosine_similarity(teacher_logits.unsqueeze(1),
                                            teacher_logits.unsqueeze(0), dim=-1)
        student_sim = torch.cosine_similarity(student_logits.unsqueeze(1),
                                            student_logits.unsqueeze(0), dim=-1)

        # Remove diagonal elements
        mask = torch.eye(batch_size, device=teacher_logits.device).bool()
        teacher_sim = teacher_sim[~mask]
        student_sim = student_sim[~mask]

        # Compute relationship loss
        rel_loss = F.mse_loss(student_sim, teacher_sim)

        return rel_loss


class HintBasedLoss(BaseDistillationLoss):
    """Hint-based distillation loss"""

    def __init__(self, temperature: float = 2.0, alpha: float = 0.5, hint_layers: List[int] = None):
        super().__init__(temperature, alpha)
        self.hint_layers = hint_layers or [6, 12]  # Default hint layers

    def compute_loss(self,
                    teacher_outputs: Dict[str, torch.Tensor],
                    student_outputs: Dict[str, torch.Tensor],
                    labels: Optional[torch.Tensor] = None) -> torch.Tensor:

        teacher_hidden = teacher_outputs.get('hidden_states', [])
        student_hidden = student_outputs.get('hidden_states', [])

        if not teacher_hidden or not student_hidden:
            return torch.tensor(0.0, device=student_outputs['logits'].device)

        total_loss = 0.0
        num_hints = 0

        for hint_layer in self.hint_layers:
            if hint_layer < len(teacher_hidden) and hint_layer < len(student_hidden):
                teacher_hint = teacher_hidden[hint_layer]
                student_hint = student_hidden[hint_layer]

                # Apply hint transformation
                hint_loss = F.mse_loss(student_hint, teacher_hint)
                total_loss += hint_loss
                num_hints += 1

        return total_loss / num_hints if num_hints > 0 else torch.tensor(0.0, device=student_outputs['logits'].device)


class VariationalDistillationLoss(BaseDistillationLoss):
    """Variational distillation loss with uncertainty estimation"""

    def __init__(self, temperature: float = 2.0, alpha: float = 0.5,
                 kl_weight: float = 0.1, entropy_weight: float = 0.1):
        super().__init__(temperature, alpha)
        self.kl_weight = kl_weight
        self.entropy_weight = entropy_weight

    def compute_loss(self,
                    teacher_outputs: Dict[str, torch.Tensor],
                    student_outputs: Dict[str, torch.Tensor],
                    labels: Optional[torch.Tensor] = None) -> torch.Tensor:

        teacher_logits = teacher_outputs.get('logits')
        student_logits = student_outputs.get('logits')

        # Standard KL divergence
        kl_loss = KLDivergenceLoss(self.temperature, self.alpha).compute_loss(
            teacher_outputs, student_outputs, labels
        )

        # Add uncertainty regularization
        student_soft = self.soft_targets(student_logits)
        teacher_soft = self.soft_targets(teacher_logits)

        # Entropy regularization
        entropy = -torch.sum(student_soft * torch.log(student_soft + 1e-8), dim=-1)
        entropy_loss = torch.mean(entropy)

        # Variational regularization
        student_log_std = torch.log(torch.var(student_logits, dim=-1) + 1e-8)
        teacher_log_std = torch.log(torch.var(teacher_logits, dim=-1) + 1e-8)
        var_loss = F.mse_loss(student_log_std, teacher_log_std)

        total_loss = kl_loss + self.kl_weight * var_loss - self.entropy_weight * entropy_loss

        return total_loss


class AdversarialDistillationLoss(BaseDistillationLoss):
    """Adversarial distillation loss with discriminator"""

    def __init__(self, temperature: float = 2.0, alpha: float = 0.5,
                 discriminator_hidden_dim: int = 256):
        super().__init__(temperature, alpha)
        self.discriminator_hidden_dim = discriminator_hidden_dim
        self.discriminator = None
        self.discriminator_optimizer = None

    def _create_discriminator(self, input_dim: int, device: torch.device):
        """Create discriminator network"""
        self.discriminator = nn.Sequential(
            nn.Linear(input_dim, self.discriminator_hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(self.discriminator_hidden_dim, self.discriminator_hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(self.discriminator_hidden_dim, 1),
            nn.Sigmoid()
        ).to(device)

        self.discriminator_optimizer = torch.optim.Adam(
            self.discriminator.parameters(), lr=1e-4
        )

    def compute_loss(self,
                    teacher_outputs: Dict[str, torch.Tensor],
                    student_outputs: Dict[str, torch.Tensor],
                    labels: Optional[torch.Tensor] = None) -> torch.Tensor:

        teacher_logits = teacher_outputs.get('logits')
        student_logits = student_outputs.get('logits')
        device = teacher_logits.device

        # Initialize discriminator if needed
        if self.discriminator is None:
            input_dim = teacher_logits.size(-1)
            self._create_discriminator(input_dim, device)

        # Standard distillation loss
        kl_loss = KLDivergenceLoss(self.temperature, self.alpha).compute_loss(
            teacher_outputs, student_outputs, labels
        )

        # Adversarial loss
        teacher_soft = self.soft_targets(teacher_logits)
        student_soft = self.soft_targets(student_logits)

        # Discriminator predictions
        teacher_pred = self.discriminator(teacher_soft.detach())
        student_pred = self.discriminator(student_soft)

        # Adversarial training
        real_labels = torch.ones_like(teacher_pred)
        fake_labels = torch.zeros_like(student_pred)

        # Discriminator loss
        d_loss = 0.5 * (
            F.binary_cross_entropy(teacher_pred, real_labels) +
            F.binary_cross_entropy(student_pred, real_labels)  # Student tries to fool
        )

        # Student adversarial loss
        adv_loss = F.binary_cross_entropy(student_pred, fake_labels)

        # Update discriminator
        self.discriminator_optimizer.zero_grad()
        d_loss.backward()
        self.discriminator_optimizer.step()

        total_loss = kl_loss + 0.1 * adv_loss

        return total_loss


class ContrastiveDistillationLoss(BaseDistillationLoss):
    """Contrastive distillation loss"""

    def __init__(self, temperature: float = 2.0, alpha: float = 0.5,
                 contrastive_temperature: float = 0.1):
        super().__init__(temperature, alpha)
        self.contrastive_temperature = contrastive_temperature

    def compute_loss(self,
                    teacher_outputs: Dict[str, torch.Tensor],
                    student_outputs: Dict[str, torch.Tensor],
                    labels: Optional[torch.Tensor] = None) -> torch.Tensor:

        teacher_logits = teacher_outputs.get('logits')
        student_logits = student_outputs.get('logits')

        # Standard distillation loss
        kl_loss = KLDivergenceLoss(self.temperature, self.alpha).compute_loss(
            teacher_outputs, student_outputs, labels
        )

        # Contrastive loss
        teacher_soft = self.soft_targets(teacher_logits)
        student_soft = self.soft_targets(student_logits)

        batch_size = teacher_soft.size(0)

        # Compute positive and negative pairs
        positive_sim = torch.cosine_similarity(teacher_soft, student_soft, dim=-1)

        # Negative samples (other examples in batch)
        negative_sim = []
        for i in range(batch_size):
            negatives = []
            for j in range(batch_size):
                if i != j:
                    neg_sim = torch.cosine_similarity(
                        teacher_soft[i].unsqueeze(0),
                        student_soft[j].unsqueeze(0),
                        dim=-1
                    )
                    negatives.append(neg_sim)
            negative_sim.append(torch.cat(negatives))

        negative_sim = torch.stack(negative_sim)

        # Contrastive loss
        logits = torch.cat([positive_sim.unsqueeze(1), negative_sim], dim=1)
        logits = logits / self.contrastive_temperature

        # Labels: positive pair is index 0
        contrastive_labels = torch.zeros(batch_size, dtype=torch.long, device=teacher_logits.device)
        cont_loss = F.cross_entropy(logits, contrastive_labels)

        total_loss = kl_loss + 0.1 * cont_loss

        return total_loss


class ComposedDistillationLoss(BaseDistillationLoss):
    """Composed distillation loss combining multiple loss functions"""

    def __init__(self, temperature: float = 2.0, alpha: float = 0.5,
                 loss_weights: LossWeights = None,
                 loss_types: List[DistillationLossType] = None):
        super().__init__(temperature, alpha)
        self.loss_weights = loss_weights or LossWeights()
        self.loss_types = loss_types or [
            DistillationLossType.KL_DIVERGENCE,
            DistillationLossType.ATTENTION_TRANSFER,
            DistillationLossType.FEATURE_MATCHING
        ]

        # Initialize individual loss functions
        self.loss_functions = {}
        self._initialize_loss_functions()

    def _initialize_loss_functions(self):
        """Initialize individual loss functions"""
        for loss_type in self.loss_types:
            if loss_type == DistillationLossType.KL_DIVERGENCE:
                self.loss_functions[loss_type] = KLDivergenceLoss(self.temperature, self.alpha)
            elif loss_type == DistillationLossType.JS_DIVERGENCE:
                self.loss_functions[loss_type] = JSDivergenceLoss(self.temperature, self.alpha)
            elif loss_type == DistillationLossType.ATTENTION_TRANSFER:
                self.loss_functions[loss_type] = AttentionTransferLoss(self.temperature, self.alpha)
            elif loss_type == DistillationLossType.FEATURE_MATCHING:
                self.loss_functions[loss_type] = FeatureMatchingLoss(self.temperature, self.alpha)
            elif loss_type == DistillationLossType.RELATIONSHIP:
                self.loss_functions[loss_type] = RelationshipDistillationLoss(self.temperature, self.alpha)
            elif loss_type == DistillationLossType.HINT_BASED:
                self.loss_functions[loss_type] = HintBasedLoss(self.temperature, self.alpha)
            elif loss_type == DistillationLossType.VARIATIONAL:
                self.loss_functions[loss_type] = VariationalDistillationLoss(self.temperature, self.alpha)
            elif loss_type == DistillationLossType.ADVERSARIAL:
                self.loss_functions[loss_type] = AdversarialDistillationLoss(self.temperature, self.alpha)
            elif loss_type == DistillationLossType.CONTRASTIVE:
                self.loss_functions[loss_type] = ContrastiveDistillationLoss(self.temperature, self.alpha)

    def compute_loss(self,
                    teacher_outputs: Dict[str, torch.Tensor],
                    student_outputs: Dict[str, torch.Tensor],
                    labels: Optional[torch.Tensor] = None) -> torch.Tensor:

        total_loss = 0.0

        for loss_type, loss_func in self.loss_functions.items():
            try:
                loss_value = loss_func.compute_loss(teacher_outputs, student_outputs, labels)

                # Apply appropriate weight
                if loss_type == DistillationLossType.KL_DIVERGENCE:
                    weight = self.loss_weights.kl_weight
                elif loss_type == DistillationLossType.ATTENTION_TRANSFER:
                    weight = self.loss_weights.attention_weight
                elif loss_type == DistillationLossType.FEATURE_MATCHING:
                    weight = self.loss_weights.feature_weight
                elif loss_type == DistillationLossType.RELATIONSHIP:
                    weight = self.loss_weights.relationship_weight
                elif loss_type == DistillationLossType.HINT_BASED:
                    weight = self.loss_weights.hint_weight
                elif loss_type == DistillationLossType.ADVERSARIAL:
                    weight = self.loss_weights.adversarial_weight
                elif loss_type == DistillationLossType.CONTRASTIVE:
                    weight = self.loss_weights.contrastive_weight
                else:
                    weight = 1.0

                total_loss += weight * loss_value

            except Exception as e:
                self.logger.warning(f"Error computing {loss_type.value} loss: {e}")
                continue

        return total_loss


class DistillationOptimizer:
    """Advanced optimization strategies for knowledge distillation"""

    def __init__(self, model: nn.Module, strategy: OptimizationStrategy = OptimizationStrategy.ADAMW,
                 learning_rate: float = 1e-4, weight_decay: float = 0.01):
        self.model = model
        self.strategy = strategy
        self.learning_rate = learning_rate
        self.weight_decay = weight_decay
        self.logger = logging.getLogger(self.__class__.__name__)

        self.optimizer = None
        self.scheduler = None
        self._initialize_optimizer()

    def _initialize_optimizer(self):
        """Initialize optimizer based on strategy"""
        if self.strategy == OptimizationStrategy.ADAMW:
            self.optimizer = torch.optim.AdamW(
                self.model.parameters(),
                lr=self.learning_rate,
                weight_decay=self.weight_decay
            )
        elif self.strategy == OptimizationStrategy.SGD_WITH_MOMENTUM:
            self.optimizer = torch.optim.SGD(
                self.model.parameters(),
                lr=self.learning_rate,
                momentum=0.9,
                weight_decay=self.weight_decay
            )
        elif self.strategy == OptimizationStrategy.ADAGRAD:
            self.optimizer = torch.optim.Adagrad(
                self.model.parameters(),
                lr=self.learning_rate,
                weight_decay=self.weight_decay
            )
        elif self.strategy == OptimizationStrategy.RMSPROP:
            self.optimizer = torch.optim.RMSprop(
                self.model.parameters(),
                lr=self.learning_rate,
                weight_decay=self.weight_decay
            )
        else:
            # Default to AdamW
            self.optimizer = torch.optim.AdamW(
                self.model.parameters(),
                lr=self.learning_rate,
                weight_decay=self.weight_decay
            )

    def create_scheduler(self, total_steps: int, warmup_steps: int = 100):
        """Create learning rate scheduler"""
        if self.strategy == OptimizationStrategy.WARMUP_COSINE:
            self.scheduler = torch.optim.lr_scheduler.OneCycleLR(
                self.optimizer,
                max_lr=self.learning_rate,
                total_steps=total_steps,
                pct_start=warmup_steps / total_steps,
                anneal_strategy='cos'
            )
        elif self.strategy == OptimizationStrategy.ONE_CYCLE:
            self.scheduler = torch.optim.lr_scheduler.OneCycleLR(
                self.optimizer,
                max_lr=self.learning_rate,
                total_steps=total_steps,
                pct_start=warmup_steps / total_steps
            )
        else:
            # Default cosine annealing
            self.scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
                self.optimizer,
                T_max=total_steps - warmup_steps
            )

    def step(self, loss: torch.Tensor):
        """Perform optimization step"""
        self.optimizer.zero_grad()
        loss.backward()

        # Gradient clipping if enabled
        if self.strategy == OptimizationStrategy.GRADIENT_CLIP:
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)

        self.optimizer.step()

        if self.scheduler is not None:
            self.scheduler.step()

    def get_learning_rate(self) -> float:
        """Get current learning rate"""
        return self.optimizer.param_groups[0]['lr']


class AdaptiveLearningRateOptimizer:
    """Adaptive learning rate optimizer for distillation"""

    def __init__(self, model: nn.Module, initial_lr: float = 1e-4):
        self.model = model
        self.initial_lr = initial_lr
        self.optimizer = torch.optim.AdamW(model.parameters(), lr=initial_lr)
        self.logger = logging.getLogger(self.__class__.__name__)

        # Adaptive parameters
        self.best_loss = float('inf')
        self.patience = 10
        self.factor = 0.5
        self.min_lr = 1e-6
        self.wait_count = 0

    def step(self, loss: torch.Tensor, current_step: int):
        """Perform optimization step with adaptive learning rate"""
        self.optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
        self.optimizer.step()

        # Adaptive learning rate adjustment
        if loss.item() < self.best_loss:
            self.best_loss = loss.item()
            self.wait_count = 0
        else:
            self.wait_count += 1

        if self.wait_count >= self.patience:
            current_lr = self.optimizer.param_groups[0]['lr']
            if current_lr > self.min_lr:
                new_lr = max(current_lr * self.factor, self.min_lr)
                for param_group in self.optimizer.param_groups:
                    param_group['lr'] = new_lr
                self.logger.info(f"Learning rate reduced to {new_lr:.2e}")
                self.wait_count = 0


def create_distillation_loss(loss_type: DistillationLossType,
                            temperature: float = 2.0,
                            alpha: float = 0.5,
                            **kwargs) -> BaseDistillationLoss:
    """Factory function to create distillation loss functions"""
    if loss_type == DistillationLossType.KL_DIVERGENCE:
        return KLDivergenceLoss(temperature, alpha)
    elif loss_type == DistillationLossType.JS_DIVERGENCE:
        return JSDivergenceLoss(temperature, alpha)
    elif loss_type == DistillationLossType.WASSERSTEIN:
        return WassersteinLoss(temperature, alpha)
    elif loss_type == DistillationLossType.ATTENTION_TRANSFER:
        return AttentionTransferLoss(temperature, alpha)
    elif loss_type == DistillationLossType.FEATURE_MATCHING:
        return FeatureMatchingLoss(temperature, alpha)
    elif loss_type == DistillationLossType.RELATIONSHIP:
        return RelationshipDistillationLoss(temperature, alpha)
    elif loss_type == DistillationLossType.HINT_BASED:
        return HintBasedLoss(temperature, alpha, kwargs.get('hint_layers'))
    elif loss_type == DistillationLossType.VARIATIONAL:
        return VariationalDistillationLoss(temperature, alpha,
                                          kwargs.get('kl_weight', 0.1),
                                          kwargs.get('entropy_weight', 0.1))
    elif loss_type == DistillationLossType.ADVERSARIAL:
        return AdversarialDistillationLoss(temperature, alpha,
                                           kwargs.get('discriminator_hidden_dim', 256))
    elif loss_type == DistillationLossType.CONTRASTIVE:
        return ContrastiveDistillationLoss(temperature, alpha,
                                           kwargs.get('contrastive_temperature', 0.1))
    else:
        raise ValueError(f"Unknown loss type: {loss_type}")


def main():
    """Example usage of distillation loss functions"""
    # Create dummy data
    batch_size, seq_len, vocab_size = 4, 10, 1000

    teacher_logits = torch.randn(batch_size, seq_len, vocab_size)
    student_logits = torch.randn(batch_size, seq_len, vocab_size)
    labels = torch.randint(0, vocab_size, (batch_size, seq_len))

    # Create teacher and student outputs
    teacher_outputs = {
        'logits': teacher_logits,
        'attentions': [torch.randn(batch_size, 8, seq_len, seq_len) for _ in range(12)],
        'hidden_states': [torch.randn(batch_size, seq_len, 768) for _ in range(12)]
    }

    student_outputs = {
        'logits': student_logits,
        'attentions': [torch.randn(batch_size, 8, seq_len, seq_len) for _ in range(6)],
        'hidden_states': [torch.randn(batch_size, seq_len, 512) for _ in range(6)]
    }

    # Test different loss functions
    loss_types = [
        DistillationLossType.KL_DIVERGENCE,
        DistillationLossType.ATTENTION_TRANSFER,
        DistillationLossType.FEATURE_MATCHING,
        DistillationLossType.RELATIONSHIP,
        DistillationLossType.VARIATIONAL
    ]

    for loss_type in loss_types:
        loss_fn = create_distillation_loss(loss_type, temperature=2.0, alpha=0.5)
        loss = loss_fn.compute_loss(teacher_outputs, student_outputs, labels)
        print(f"{loss_type.value}: {loss.item():.4f}")

    # Test composed loss
    loss_weights = LossWeights(kl_weight=1.0, attention_weight=0.5, feature_weight=0.3)
    composed_loss = ComposedDistillationLoss(
        temperature=2.0, alpha=0.5, loss_weights=loss_weights
    )
    loss = composed_loss.compute_loss(teacher_outputs, student_outputs, labels)
    print(f"Composed loss: {loss.item():.4f}")


if __name__ == "__main__":
    main()