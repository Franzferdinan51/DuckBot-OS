#!/usr/bin/env python3
"""
Parameter-Efficient Training Methods with Advanced Optimizer Support
Implements various parameter-efficient fine-tuning (PEFT) methods and advanced optimizers
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.optim import Optimizer, AdamW, Adam, SGD, RMSprop
from typing import Dict, List, Optional, Any, Tuple, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging
import math
import numpy as np
from abc import ABC, abstractmethod

# Try to import additional optimizers
try:
    from bitsandbytes.optim import AdamW8bit, Adam8bit, Lion8bit
    HAS_8BIT_OPTIMIZERS = True
except ImportError:
    HAS_8BIT_OPTIMIZERS = False

try:
    from torch_optimizer import Lion, RAdam, Lookahead, AdaBound, AdaBoundW
    HAS_TORCH_OPTIMIZER = True
except ImportError:
    HAS_TORCH_OPTIMIZER = False

try:
    from adafactor import Adafactor
    HAS_ADAFACTOR = True
except ImportError:
    HAS_ADAFACTOR = False

class PEFTMethod(Enum):
    """Parameter-Efficient Fine-Tuning methods"""
    LORA = "lora"                    # Low-Rank Adaptation
    ADAPTER = "adapter"              # Adapter layers
    PREFIX_TUNING = "prefix_tuning"   # Prefix tuning
    PROMPT_TUNING = "prompt_tuning"   # Prompt tuning
    IA3 = "ia3"                      # (IA)³ Infused Adapter by Inhibiting and Amplifying
    DORA = "dora"                    # Weight-Decomposed LoRA
    VERA = "vera"                    # Vector-based Random Adaptation
    COMPAC = "compac"                # Compact adapters

class OptimizerType(Enum):
    """Advanced optimizer types"""
    ADAMW = "adamw"
    ADAM = "adam"
    SGD = "sgd"
    RMSprop = "rmsprop"
    ADAM_8BIT = "adam_8bit"
    LION = "lion"
    LION_8BIT = "lion_8bit"
    RADAM = "radam"
    LOOKAHEAD = "lookahead"
    ADABOUND = "adabound"
    ADAFACTOR = "adafactor"

class LearningRateSchedule(Enum):
    """Learning rate scheduling strategies"""
    COSINE = "cosine"
    LINEAR = "linear"
    EXPONENTIAL = "exponential"
    COSINE_WITH_RESTARTS = "cosine_with_restarts"
    WARMUP_COSINE = "warmup_cosine"
    CYCLICAL = "cyclical"
    ONE_CYCLE = "one_cycle"
    POLYNOMIAL = "polynomial"

@dataclass
class PEFTConfig:
    """Base configuration for PEFT methods"""
    method: PEFTMethod
    target_modules: Optional[List[str]] = None
    trainable_params_ratio: float = 0.1  # Target ratio of trainable parameters
    enable_gradient_checkpointing: bool = True

@dataclass
class LoRAConfig(PEFTConfig):
    """LoRA configuration"""
    r: int = 8                        # Rank of LoRA matrices
    lora_alpha: int = 16               # LoRA scaling parameter
    lora_dropout: float = 0.1          # Dropout probability
    bias: str = "none"                 # Bias type ("none", "all", "lora_only")
    use_rslora: bool = False          # Use Rank-Stabilized LoRA
    use_dora: bool = False            # Use Weight-Decomposed LoRA

@dataclass
class AdapterConfig(PEFTConfig):
    """Adapter configuration"""
    adapter_dim: int = 64              # Adapter hidden dimension
    adapter_dropout: float = 0.1       # Dropout probability
    adapter_act_fn: str = "gelu"       # Activation function
    use_parallel_adapter: bool = False # Use parallel adapter
    use_compact_adapter: bool = False  # Use compact adapter

@dataclass
class PrefixTuningConfig(PEFTConfig):
    """Prefix tuning configuration"""
    num_virtual_tokens: int = 20       # Number of virtual tokens
    prefix_projection: bool = True     # Use prefix projection
    prefix_dim: int = 512              # Prefix projection dimension

@dataclass
class OptimizerConfig:
    """Advanced optimizer configuration"""
    optimizer_type: OptimizerType
    lr: float = 1e-3
    weight_decay: float = 0.01
    betas: Tuple[float, float] = (0.9, 0.999)
    eps: float = 1e-8
    momentum: float = 0.9
    amsgrad: bool = False
    foreach: bool = True

    # 8-bit optimizer settings
    quantization_bits: int = 8
    percentile_clipping: float = 100.0
    block_wise: bool = True

    # Advanced optimizer settings
    lookahead_k: int = 5              # Lookahead steps
    lookahead_alpha: float = 0.5      # Lookahead alpha
    decay_rate: float = 0.999         # AdaBound decay rate
    final_lr: float = 0.1             # AdaBound final learning rate

@dataclass
class SchedulerConfig:
    """Learning rate scheduler configuration"""
    scheduler_type: LearningRateSchedule
    total_steps: int
    warmup_steps: int = 0
    warmup_ratio: float = 0.1
    min_lr_ratio: float = 0.1
    cycle_length: int = 1000
    cycle_multiplier: float = 2.0
    gamma: float = 0.9
    power: float = 1.0

class ParameterEfficientLayer(nn.Module):
    """Base class for parameter-efficient layers"""

    def __init__(self, original_module: nn.Module, config: PEFTConfig):
        super().__init__()
        self.original_module = original_module
        self.config = config
        self.trainable_params = 0
        self.total_params = 0

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        raise NotImplementedError

    def get_trainable_params(self) -> int:
        return self.trainable_params

    def get_total_params(self) -> int:
        return self.total_params

class LoRALayer(ParameterEfficientLayer):
    """LoRA adaptation layer"""

    def __init__(self, original_module: nn.Module, config: LoRAConfig):
        super().__init__(original_module, config)
        self.r = config.r
        self.lora_alpha = config.lora_alpha
        self.lora_dropout = config.lora_dropout
        self.scaling = self.lora_alpha / self.r

        # Determine if this is a linear layer
        if isinstance(original_module, nn.Linear):
            self.in_features = original_module.in_features
            self.out_features = original_module.out_features

            # LoRA matrices
            self.lora_A = nn.Parameter(torch.randn(self.r, self.in_features))
            self.lora_B = nn.Parameter(torch.randn(self.out_features, self.r))

            # Dropout
            self.lora_dropout_layer = nn.Dropout(config.lora_dropout)

            # Freeze original parameters
            for param in original_module.parameters():
                param.requires_grad = False

            # Count parameters
            self.trainable_params = self.lora_A.numel() + self.lora_B.numel()
            self.total_params = sum(p.numel() for p in original_module.parameters()) + self.trainable_params

        else:
            raise ValueError(f"LoRA not supported for {type(original_module)}")

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # Original module output
        original_output = self.original_module(x)

        # LoRA adaptation
        lora_output = self.lora_dropout_layer(x)
        lora_output = lora_output @ self.lora_A.T
        lora_output = lora_output @ self.lora_B.T
        lora_output = lora_output * self.scaling

        return original_output + lora_output

class AdapterLayer(ParameterEfficientLayer):
    """Adapter layer"""

    def __init__(self, original_module: nn.Module, config: AdapterConfig):
        super().__init__(original_module, config)
        self.adapter_dim = config.adapter_dim
        self.adapter_dropout = config.adapter_dropout
        self.adapter_act_fn = config.adapter_act_fn

        if isinstance(original_module, nn.Linear):
            self.in_features = original_module.in_features
            self.out_features = original_module.out_features

            # Adapter layers
            self.adapter_down = nn.Linear(self.out_features, self.adapter_dim)
            self.adapter_up = nn.Linear(self.adapter_dim, self.out_features)
            self.adapter_dropout_layer = nn.Dropout(config.adapter_dropout)
            self.adapter_act = self._get_activation_fn(config.adapter_act_fn)

            # Initialize adapter weights
            nn.init.zeros_(self.adapter_down.weight)
            nn.init.zeros_(self.adapter_down.bias)
            nn.init.zeros_(self.adapter_up.weight)
            nn.init.zeros_(self.adapter_up.bias)

            # Freeze original parameters
            for param in original_module.parameters():
                param.requires_grad = False

            # Count parameters
            self.trainable_params = (
                self.adapter_down.weight.numel() + self.adapter_down.bias.numel() +
                self.adapter_up.weight.numel() + self.adapter_up.bias.numel()
            )
            self.total_params = sum(p.numel() for p in original_module.parameters()) + self.trainable_params

        else:
            raise ValueError(f"Adapter not supported for {type(original_module)}")

    def _get_activation_fn(self, act_fn: str) -> nn.Module:
        """Get activation function"""
        if act_fn == "gelu":
            return nn.GELU()
        elif act_fn == "relu":
            return nn.ReLU()
        elif act_fn == "tanh":
            return nn.Tanh()
        elif act_fn == "sigmoid":
            return nn.Sigmoid()
        else:
            return nn.Identity()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # Original module output
        original_output = self.original_module(x)

        # Adapter adaptation
        adapter_output = self.adapter_dropout_layer(original_output)
        adapter_output = self.adapter_down(adapter_output)
        adapter_output = self.adapter_act(adapter_output)
        adapter_output = self.adapter_up(adapter_output)

        return original_output + adapter_output

class IA3Layer(ParameterEfficientLayer):
    """(IA)³ layer - Infused Adapter by Inhibiting and Amplifying"""

    def __init__(self, original_module: nn.Module, config: PEFTConfig):
        super().__init__(original_module, config)

        if isinstance(original_module, nn.Linear):
            self.in_features = original_module.in_features
            self.out_features = original_module.out_features

            # IA³ vectors
            self.ia3_l = nn.Parameter(torch.ones(1, self.in_features))
            self.ia3_r = nn.Parameter(torch.ones(self.out_features, 1))

            # Freeze original parameters
            for param in original_module.parameters():
                param.requires_grad = False

            # Count parameters
            self.trainable_params = self.ia3_l.numel() + self.ia3_r.numel()
            self.total_params = sum(p.numel() for p in original_module.parameters()) + self.trainable_params

        else:
            raise ValueError(f"IA³ not supported for {type(original_module)}")

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # Apply IA³ scaling
        x_scaled = x * self.ia3_l

        # Original module
        original_output = self.original_module(x_scaled)

        # Apply output scaling
        return original_output * self.ia3_r

class AdvancedOptimizerFactory:
    """Factory for creating advanced optimizers"""

    @staticmethod
    def create_optimizer(
        model: nn.Module,
        config: OptimizerConfig,
        separate_weight_decay: bool = True
    ) -> Optimizer:
        """Create optimizer based on configuration"""

        if separate_weight_decay:
            # Separate parameters with and without weight decay
            no_decay = ["bias", "LayerNorm.weight", "layer_norm.weight", "norm.weight"]
            optimizer_grouped_parameters = [
                {
                    "params": [p for n, p in model.named_parameters() if not any(nd in n for nd in no_decay)],
                    "weight_decay": config.weight_decay,
                },
                {
                    "params": [p for n, p in model.named_parameters() if any(nd in n for nd in no_decay)],
                    "weight_decay": 0.0,
                },
            ]
        else:
            optimizer_grouped_parameters = model.parameters()

        # Create optimizer based on type
        if config.optimizer_type == OptimizerType.ADAMW:
            return AdamW(
                optimizer_grouped_parameters,
                lr=config.lr,
                betas=config.betas,
                eps=config.eps,
                weight_decay=config.weight_decay,
                amsgrad=config.amsgrad,
                foreach=config.foreach,
            )

        elif config.optimizer_type == OptimizerType.ADAM:
            return Adam(
                optimizer_grouped_parameters,
                lr=config.lr,
                betas=config.betas,
                eps=config.eps,
                weight_decay=config.weight_decay,
                amsgrad=config.amsgrad,
                foreach=config.foreach,
            )

        elif config.optimizer_type == OptimizerType.SGD:
            return SGD(
                optimizer_grouped_parameters,
                lr=config.lr,
                momentum=config.momentum,
                weight_decay=config.weight_decay,
            )

        elif config.optimizer_type == OptimizerType.RMSprop:
            return RMSprop(
                optimizer_grouped_parameters,
                lr=config.lr,
                alpha=config.gamma,
                weight_decay=config.weight_decay,
                momentum=config.momentum,
                eps=config.eps,
            )

        elif config.optimizer_type == OptimizerType.ADAM_8BIT and HAS_8BIT_OPTIMIZERS:
            return AdamW8bit(
                optimizer_grouped_parameters,
                lr=config.lr,
                betas=config.betas,
                eps=config.eps,
                weight_decay=config.weight_decay,
                percentile_clipping=config.percentile_clipping,
                block_wise=config.block_wise,
            )

        elif config.optimizer_type == OptimizerType.LION and HAS_TORCH_OPTIMIZER:
            return Lion(
                optimizer_grouped_parameters,
                lr=config.lr,
                weight_decay=config.weight_decay,
                betas=config.betas,
            )

        elif config.optimizer_type == OptimizerType.LION_8BIT and HAS_8BIT_OPTIMIZERS:
            return Lion8bit(
                optimizer_grouped_parameters,
                lr=config.lr,
                betas=config.betas,
                weight_decay=config.weight_decay,
            )

        elif config.optimizer_type == OptimizerType.RADAM and HAS_TORCH_OPTIMIZER:
            return RAdam(
                optimizer_grouped_parameters,
                lr=config.lr,
                betas=config.betas,
                weight_decay=config.weight_decay,
                eps=config.eps,
            )

        elif config.optimizer_type == OptimizerType.LOOKAHEAD and HAS_TORCH_OPTIMIZER:
            base_optimizer = AdamW(
                optimizer_grouped_parameters,
                lr=config.lr,
                betas=config.betas,
                eps=config.eps,
                weight_decay=config.weight_decay,
            )
            return Lookahead(base_optimizer, k=config.lookahead_k, alpha=config.lookahead_alpha)

        elif config.optimizer_type == OptimizerType.ADABOUND and HAS_TORCH_OPTIMIZER:
            return AdaBound(
                optimizer_grouped_parameters,
                lr=config.lr,
                betas=config.betas,
                final_lr=config.final_lr,
                gamma=config.decay_rate,
                weight_decay=config.weight_decay,
            )

        elif config.optimizer_type == OptimizerType.ADAFACTOR and HAS_ADAFACTOR:
            return Adafactor(
                optimizer_grouped_parameters,
                lr=config.lr,
                eps=(config.eps, config.eps * 1e-30),
                clip_threshold=config.percentile_clipping,
                decay_rate=config.decay_rate,
                beta1=None if config.betas[0] == 0.0 else config.betas[0],
                weight_decay=config.weight_decay,
                scale_parameter=False,
                relative_step=False,
                warmup_init=False,
            )

        else:
            raise ValueError(f"Unsupported optimizer type: {config.optimizer_type}")

class LearningRateSchedulerFactory:
    """Factory for creating learning rate schedulers"""

    @staticmethod
    def create_scheduler(
        optimizer: Optimizer,
        config: SchedulerConfig,
        total_steps: int
    ) -> torch.optim.lr_scheduler._LRScheduler:
        """Create learning rate scheduler based on configuration"""

        # Adjust total steps if needed
        if config.total_steps > 0:
            total_steps = config.total_steps

        # Calculate warmup steps
        warmup_steps = config.warmup_steps
        if warmup_steps == 0 and config.warmup_ratio > 0:
            warmup_steps = int(total_steps * config.warmup_ratio)

        if config.scheduler_type == LearningRateSchedule.COSINE:
            return torch.optim.lr_scheduler.CosineAnnealingLR(
                optimizer,
                T_max=total_steps - warmup_steps,
                eta_min=optimizer.param_groups[0]['lr'] * config.min_lr_ratio
            )

        elif config.scheduler_type == LearningRateSchedule.LINEAR:
            return torch.optim.lr_scheduler.LinearLR(
                optimizer,
                start_factor=0.1,
                end_factor=1.0,
                total_iters=warmup_steps if warmup_steps > 0 else total_steps
            )

        elif config.scheduler_type == LearningRateSchedule.EXPONENTIAL:
            return torch.optim.lr_scheduler.ExponentialLR(
                optimizer,
                gamma=config.gamma
            )

        elif config.scheduler_type == LearningRateSchedule.COSINE_WITH_RESTARTS:
            return torch.optim.lr_scheduler.CosineAnnealingWarmRestarts(
                optimizer,
                T_0=config.cycle_length,
                T_mult=config.cycle_multiplier,
                eta_min=optimizer.param_groups[0]['lr'] * config.min_lr_ratio
            )

        elif config.scheduler_type == LearningRateSchedule.WARMUP_COSINE:
            if warmup_steps > 0:
                return torch.optim.lr_scheduler.SequentialLR(
                    optimizer,
                    schedulers=[
                        torch.optim.lr_scheduler.LinearLR(
                            optimizer,
                            start_factor=0.1,
                            end_factor=1.0,
                            total_iters=warmup_steps
                        ),
                        torch.optim.lr_scheduler.CosineAnnealingLR(
                            optimizer,
                            T_max=total_steps - warmup_steps,
                            eta_min=optimizer.param_groups[0]['lr'] * config.min_lr_ratio
                        )
                    ],
                    milestones=[warmup_steps]
                )
            else:
                return torch.optim.lr_scheduler.CosineAnnealingLR(
                    optimizer,
                    T_max=total_steps,
                    eta_min=optimizer.param_groups[0]['lr'] * config.min_lr_ratio
                )

        elif config.scheduler_type == LearningRateSchedule.CYCLICAL:
            return torch.optim.lr_scheduler.CyclicLR(
                optimizer,
                base_lr=optimizer.param_groups[0]['lr'] * config.min_lr_ratio,
                max_lr=optimizer.param_groups[0]['lr'],
                step_size_up=config.cycle_length // 2,
                mode='triangular2',
                gamma=config.gamma
            )

        elif config.scheduler_type == LearningRateSchedule.ONE_CYCLE:
            return torch.optim.lr_scheduler.OneCycleLR(
                optimizer,
                max_lr=optimizer.param_groups[0]['lr'],
                total_steps=total_steps,
                pct_start=warmup_steps / total_steps if warmup_steps > 0 else 0.3,
                anneal_strategy='cos',
                div_factor=25.0,
                final_div_factor=10000.0
            )

        elif config.scheduler_type == LearningRateSchedule.POLYNOMIAL:
            return torch.optim.lr_scheduler.PolynomialLR(
                optimizer,
                total_iter=total_steps,
                power=config.power
            )

        else:
            return torch.optim.lr_scheduler.ConstantLR(optimizer, factor=1.0)

class ParameterEfficientModelWrapper:
    """Wrapper for applying PEFT methods to models"""

    def __init__(self, model: nn.Module, config: PEFTConfig):
        self.model = model
        self.config = config
        self.peft_layers: Dict[str, ParameterEfficientLayer] = {}
        self.logger = logging.getLogger(__name__)

        # Apply PEFT method
        self._apply_peft_method()

    def _apply_peft_method(self):
        """Apply the configured PEFT method"""
        if self.config.method == PEFTMethod.LORA:
            self._apply_lora()
        elif self.config.method == PEFTMethod.ADAPTER:
            self._apply_adapter()
        elif self.config.method == PEFTMethod.IA3:
            self._apply_ia3()
        else:
            raise ValueError(f"PEFT method {self.config.method} not implemented")

    def _apply_lora(self):
        """Apply LoRA to the model"""
        if not isinstance(self.config, LoRAConfig):
            self.config = LoRAConfig(**self.config.__dict__)

        target_modules = self.config.target_modules or self._get_default_target_modules()

        for name, module in self.model.named_modules():
            if any(target in name for target in target_modules):
                if isinstance(module, nn.Linear):
                    # Replace with LoRA layer
                    lora_layer = LoRALayer(module, self.config)
                    self._replace_module(name, lora_layer)
                    self.peft_layers[name] = lora_layer

        self._log_peft_stats()

    def _apply_adapter(self):
        """Apply adapter layers to the model"""
        if not isinstance(self.config, AdapterConfig):
            self.config = AdapterConfig(**self.config.__dict__)

        target_modules = self.config.target_modules or self._get_default_target_modules()

        for name, module in self.model.named_modules():
            if any(target in name for target in target_modules):
                if isinstance(module, nn.Linear):
                    # Replace with adapter layer
                    adapter_layer = AdapterLayer(module, self.config)
                    self._replace_module(name, adapter_layer)
                    self.peft_layers[name] = adapter_layer

        self._log_peft_stats()

    def _apply_ia3(self):
        """Apply IA³ to the model"""
        target_modules = self.config.target_modules or self._get_default_target_modules()

        for name, module in self.model.named_modules():
            if any(target in name for target in target_modules):
                if isinstance(module, nn.Linear):
                    # Replace with IA³ layer
                    ia3_layer = IA3Layer(module, self.config)
                    self._replace_module(name, ia3_layer)
                    self.peft_layers[name] = ia3_layer

        self._log_peft_stats()

    def _get_default_target_modules(self) -> List[str]:
        """Get default target modules for transformer models"""
        return ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]

    def _replace_module(self, name: str, new_module: nn.Module):
        """Replace a module in the model"""
        parent_name, child_name = name.rsplit('.', 1) if '.' in name else ('', name)

        if parent_name:
            parent = self._find_module_by_name(self.model, parent_name)
            if parent is not None:
                setattr(parent, child_name, new_module)
        else:
            # This is complex for root module - skip for now
            pass

    def _find_module_by_name(self, model: nn.Module, name: str) -> Optional[nn.Module]:
        """Find a module by its name"""
        for n, module in model.named_modules():
            if n == name:
                return module
        return None

    def _log_peft_stats(self):
        """Log PEFT statistics"""
        total_params = sum(p.numel() for p in self.model.parameters())
        trainable_params = sum(p.numel() for p in self.model.parameters() if p.requires_grad)
        trainable_ratio = trainable_params / total_params

        self.logger.info(f"Applied {self.config.method.value} to model")
        self.logger.info(f"  Total parameters: {total_params:,}")
        self.logger.info(f"  Trainable parameters: {trainable_params:,}")
        self.logger.info(f"  Trainable ratio: {trainable_ratio:.2%}")

    def get_trainable_parameters(self) -> List[torch.Tensor]:
        """Get trainable parameters"""
        return [p for p in self.model.parameters() if p.requires_grad]

    def get_parameter_efficiency_stats(self) -> Dict[str, Any]:
        """Get parameter efficiency statistics"""
        total_params = sum(p.numel() for p in self.model.parameters())
        trainable_params = sum(p.numel() for p in self.model.parameters() if p.requires_grad)

        return {
            "total_parameters": total_params,
            "trainable_parameters": trainable_params,
            "trainable_ratio": trainable_params / total_params,
            "efficiency_ratio": 1 - (trainable_params / total_params),
            "peft_method": self.config.method.value,
            "num_peft_layers": len(self.peft_layers)
        }

# Configuration presets
def create_peft_presets():
    """Create predefined PEFT configurations"""
    presets = {}

    # Ultra-efficient LoRA
    presets["ultra_efficient_lora"] = LoRAConfig(
        method=PEFTMethod.LORA,
        r=4,
        lora_alpha=8,
        lora_dropout=0.1,
        trainable_params_ratio=0.01,
        target_modules=["q_proj", "v_proj"]
    )

    # Balanced LoRA
    presets["balanced_lora"] = LoRAConfig(
        method=PEFTMethod.LORA,
        r=16,
        lora_alpha=32,
        lora_dropout=0.05,
        trainable_params_ratio=0.05,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"]
    )

    # High-performance LoRA
    presets["high_performance_lora"] = LoRAConfig(
        method=PEFTMethod.LORA,
        r=32,
        lora_alpha=64,
        lora_dropout=0.0,
        trainable_params_ratio=0.1,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
    )

    # IA3 for efficient adaptation
    presets["ia3_efficient"] = PEFTConfig(
        method=PEFTMethod.IA3,
        trainable_params_ratio=0.001,
        target_modules=["q_proj", "v_proj", "k_proj"]
    )

    return presets

def create_optimizer_presets():
    """Create predefined optimizer configurations"""
    presets = {}

    # AdamW balanced
    presets["adamw_balanced"] = OptimizerConfig(
        optimizer_type=OptimizerType.ADAMW,
        lr=2e-4,
        weight_decay=0.01,
        betas=(0.9, 0.999),
        eps=1e-8
    )

    # 8-bit AdamW for memory efficiency
    presets["adamw_8bit"] = OptimizerConfig(
        optimizer_type=OptimizerType.ADAM_8BIT,
        lr=2e-4,
        weight_decay=0.01,
        betas=(0.9, 0.999),
        eps=1e-8,
        quantization_bits=8
    )

    # Lion optimizer for better performance
    presets["lion"] = OptimizerConfig(
        optimizer_type=OptimizerType.LION,
        lr=1e-4,
        weight_decay=0.01,
        betas=(0.9, 0.99)
    )

    # Lookahead AdamW for stability
    presets["lookahead_adamw"] = OptimizerConfig(
        optimizer_type=OptimizerType.LOOKAHEAD,
        lr=2e-4,
        weight_decay=0.01,
        betas=(0.9, 0.999),
        lookahead_k=5,
        lookahead_alpha=0.5
    )

    return presets

def create_scheduler_presets():
    """Create predefined scheduler configurations"""
    presets = {}

    # Cosine annealing
    presets["cosine"] = SchedulerConfig(
        scheduler_type=LearningRateSchedule.COSINE,
        total_steps=10000,
        warmup_ratio=0.1,
        min_lr_ratio=0.1
    )

    # One-cycle learning rate
    presets["one_cycle"] = SchedulerConfig(
        scheduler_type=LearningRateSchedule.ONE_CYCLE,
        total_steps=10000,
        warmup_ratio=0.3,
        min_lr_ratio=0.01
    )

    # Cosine with restarts
    presets["cosine_restarts"] = SchedulerConfig(
        scheduler_type=LearningRateSchedule.COSINE_WITH_RESTARTS,
        total_steps=10000,
        cycle_length=1000,
        cycle_multiplier=2.0,
        min_lr_ratio=0.1
    )

    return presets

if __name__ == "__main__":
    # Example usage
    import torch

    # Create a simple model
    model = nn.Sequential(
        nn.Linear(1000, 2000),
        nn.ReLU(),
        nn.Linear(2000, 1000),
        nn.ReLU(),
        nn.Linear(1000, 500)
    )

    # Apply LoRA
    lora_config = LoRAConfig(
        method=PEFTMethod.LORA,
        r=8,
        lora_alpha=16,
        lora_dropout=0.1,
        target_modules=["1", "4"]  # Linear layers
    )

    peft_model = ParameterEfficientModelWrapper(model, lora_config)

    # Get stats
    stats = peft_model.get_parameter_efficiency_stats()
    print(f"PEFT Model Stats: {stats}")

    # Create optimizer
    optimizer_config = OptimizerConfig(
        optimizer_type=OptimizerType.ADAMW,
        lr=1e-3,
        weight_decay=0.01
    )

    optimizer = AdvancedOptimizerFactory.create_optimizer(peft_model.model, optimizer_config)

    print(f"Created optimizer: {type(optimizer).__name__}")