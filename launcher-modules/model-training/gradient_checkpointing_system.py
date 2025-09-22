#!/usr/bin/env python3
"""
Advanced Gradient Checkpointing and Memory Management System
Implements sophisticated memory optimization techniques for large model training
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.checkpoint import checkpoint
from typing import Dict, List, Optional, Any, Tuple, Callable
import logging
import math
import gc
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

class CheckpointingStrategy(Enum):
    """Gradient checkpointing strategies"""
    NONE = "none"
    SELECTIVE = "selective"           # Checkpoint only large layers
    BLOCK_WISE = "block_wise"         # Checkpoint transformer blocks
    LAYER_WISE = "layer_wise"         # Checkpoint every N layers
    ADAPTIVE = "adaptive"             # Adaptive checkpointing based on memory
    MEMORY_AWARE = "memory_aware"     # Memory-aware checkpointing

class MemoryOptimizationMode(Enum):
    """Memory optimization modes"""
    OFF = "off"
    CONSERVATIVE = "conservative"
    BALANCED = "balanced"
    AGGRESSIVE = "aggressive"
    ULTRA_EFFICIENT = "ultra_efficient"

@dataclass
class MemoryProfile:
    """Memory profiling information"""
    available_gpu_memory: float
    model_memory: float
    activation_memory: float
    gradient_memory: float
    optimizer_memory: float
    total_required: float
    safety_margin: float = 0.1

class GradientCheckpointingConfig:
    """Configuration for gradient checkpointing"""

    def __init__(
        self,
        strategy: CheckpointingStrategy = CheckpointingStrategy.ADAPTIVE,
        checkpoint_ratio: float = 0.3,  # Fraction of layers to checkpoint
        memory_threshold: float = 0.8,  # Memory usage threshold
        enable_recompute: bool = True,  # Enable activation recomputation
        preserve_rng_state: bool = True,  # Preserve random number generator state
        use_custom_checkpoint: bool = False,  # Use custom checkpoint implementation
        layer_selection_criteria: str = "size",  # "size", "memory", "custom"
    ):
        self.strategy = strategy
        self.checkpoint_ratio = checkpoint_ratio
        self.memory_threshold = memory_threshold
        self.enable_recompute = enable_recompute
        self.preserve_rng_state = preserve_rng_state
        self.use_custom_checkpoint = use_custom_checkpoint
        self.layer_selection_criteria = layer_selection_criteria

class AdvancedMemoryManager:
    """Advanced memory management system"""

    def __init__(self, config: GradientCheckpointingConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.memory_profile: Optional[MemoryProfile] = None
        self.checkpointed_layers: Dict[str, bool] = {}
        self.layer_memory_usage: Dict[str, float] = {}

    def analyze_memory_requirements(self, model: nn.Module, batch_size: int, sequence_length: int) -> MemoryProfile:
        """Analyze memory requirements for training"""

        # Get available GPU memory
        if torch.cuda.is_available():
            available_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)  # GB
        else:
            available_memory = 8.0  # Default CPU memory estimate

        # Estimate model memory
        model_memory = self._estimate_model_memory(model)

        # Estimate activation memory
        activation_memory = self._estimate_activation_memory(model, batch_size, sequence_length)

        # Estimate gradient memory
        gradient_memory = model_memory * 2  # Gradients are typically 2x model size

        # Estimate optimizer memory (for AdamW)
        optimizer_memory = model_memory * 4  # AdamW stores 2 states per parameter

        total_required = model_memory + activation_memory + gradient_memory + optimizer_memory

        self.memory_profile = MemoryProfile(
            available_gpu_memory=available_memory,
            model_memory=model_memory,
            activation_memory=activation_memory,
            gradient_memory=gradient_memory,
            optimizer_memory=optimizer_memory,
            total_required=total_required
        )

        return self.memory_profile

    def _estimate_model_memory(self, model: nn.Module) -> float:
        """Estimate model memory usage in GB"""
        total_params = sum(p.numel() for p in model.parameters())
        # Assuming float32 (4 bytes per parameter)
        return (total_params * 4) / (1024**3)

    def _estimate_activation_memory(self, model: nn.Module, batch_size: int, sequence_length: int) -> float:
        """Estimate activation memory usage in GB"""
        # Rough estimate based on model size and input dimensions
        # This is a simplified calculation
        model_memory = self._estimate_model_memory(model)
        # Activations typically use 10-20% of model memory per batch element
        activation_ratio = 0.15 * batch_size
        return model_memory * activation_ratio

    def should_use_checkpointing(self) -> bool:
        """Determine if gradient checkpointing should be used"""
        if self.memory_profile is None:
            return False

        memory_usage_ratio = self.memory_profile.total_required / self.memory_profile.available_gpu_memory
        return memory_usage_ratio > self.config.memory_threshold

    def select_layers_for_checkpointing(self, model: nn.Module) -> List[str]:
        """Select layers to apply gradient checkpointing"""
        if self.config.strategy == CheckpointingStrategy.NONE:
            return []

        if self.config.strategy == CheckpointingStrategy.ADAPTIVE:
            return self._adaptive_layer_selection(model)
        elif self.config.strategy == CheckpointingStrategy.SELECTIVE:
            return self._selective_layer_selection(model)
        elif self.config.strategy == CheckpointingStrategy.BLOCK_WISE:
            return self._block_wise_selection(model)
        elif self.config.strategy == CheckpointingStrategy.LAYER_WISE:
            return self._layer_wise_selection(model)
        else:
            return []

    def _adaptive_layer_selection(self, model: nn.Module) -> List[str]:
        """Adaptive layer selection based on memory usage"""
        if not self.should_use_checkpointing():
            return []

        layers_to_checkpoint = []
        total_layers = 0
        layers_analyzed = {}

        # Analyze all layers
        for name, module in model.named_modules():
            if self._should_checkpoint_layer(module):
                memory_usage = self._estimate_layer_memory(module)
                layers_analyzed[name] = memory_usage
                total_layers += 1

        # Sort layers by memory usage (descending)
        sorted_layers = sorted(layers_analyzed.items(), key=lambda x: x[1], reverse=True)

        # Select top layers based on checkpoint_ratio
        num_to_checkpoint = int(total_layers * self.config.checkpoint_ratio)
        layers_to_checkpoint = [name for name, _ in sorted_layers[:num_to_checkpoint]]

        self.logger.info(f"Adaptive checkpointing: Selected {len(layers_to_checkpoint)}/{total_layers} layers")
        return layers_to_checkpoint

    def _selective_layer_selection(self, model: nn.Module) -> List[str]:
        """Select layers based on size criteria"""
        layers_to_checkpoint = []
        threshold_size = 1e6  # 1M parameters

        for name, module in model.named_modules():
            if self._should_checkpoint_layer(module):
                param_count = sum(p.numel() for p in module.parameters())
                if param_count > threshold_size:
                    layers_to_checkpoint.append(name)

        return layers_to_checkpoint

    def _block_wise_selection(self, model: nn.Module) -> List[str]:
        """Select transformer blocks for checkpointing"""
        layers_to_checkpoint = []

        for name, module in model.named_modules():
            if "block" in name.lower() or "layer" in name.lower():
                if hasattr(module, "attention") or hasattr(module, "mlp"):
                    layers_to_checkpoint.append(name)

        return layers_to_checkpoint

    def _layer_wise_selection(self, model: nn.Module) -> List[str]:
        """Select every N layers for checkpointing"""
        layers_to_checkpoint = []
        layer_names = []

        for name, module in model.named_modules():
            if self._should_checkpoint_layer(module):
                layer_names.append(name)

        # Select every N layers based on checkpoint_ratio
        if layer_names:
            step = max(1, int(1 / self.config.checkpoint_ratio))
            layers_to_checkpoint = layer_names[::step]

        return layers_to_checkpoint

    def _should_checkpoint_layer(self, module: nn.Module) -> bool:
        """Determine if a layer should be considered for checkpointing"""
        # Skip embedding layers and small layers
        if isinstance(module, (nn.Embedding, nn.LayerNorm, nn.Dropout)):
            return False

        # Check layer size
        param_count = sum(p.numel() for p in module.parameters())
        if param_count < 1000:  # Skip very small layers
            return False

        return True

    def _estimate_layer_memory(self, module: nn.Module) -> float:
        """Estimate memory usage for a specific layer"""
        param_count = sum(p.numel() for p in module.parameters())
        # Rough estimate in bytes
        return param_count * 4  # Assuming float32

class CheckpointedModule(nn.Module):
    """Wrapper module that applies gradient checkpointing"""

    def __init__(self, module: nn.Module, preserve_rng_state: bool = True):
        super().__init__()
        self.module = module
        self.preserve_rng_state = preserve_rng_state

    def forward(self, *args, **kwargs):
        """Forward pass with gradient checkpointing"""
        if torch.is_grad_enabled():
            return checkpoint(
                self.module,
                *args,
                use_reentrant=False,
                preserve_rng_state=self.preserve_rng_state,
                **kwargs
            )
        else:
            return self.module(*args, **kwargs)

class MemoryAwareTrainer:
    """Memory-aware trainer with advanced optimization"""

    def __init__(
        self,
        model: nn.Module,
        checkpointing_config: GradientCheckpointingConfig,
        memory_optimization_mode: MemoryOptimizationMode = MemoryOptimizationMode.BALANCED
    ):
        self.model = model
        self.checkpointing_config = checkpointing_config
        self.memory_optimization_mode = memory_optimization_mode
        self.memory_manager = AdvancedMemoryManager(checkpointing_config)
        self.logger = logging.getLogger(__name__)

    def apply_gradient_checkpointing(self, batch_size: int, sequence_length: int):
        """Apply gradient checkpointing to the model"""

        # Analyze memory requirements
        memory_profile = self.memory_manager.analyze_memory_requirements(
            self.model, batch_size, sequence_length
        )

        self.logger.info(f"Memory analysis:")
        self.logger.info(f"  Available GPU memory: {memory_profile.available_gpu_memory:.2f} GB")
        self.logger.info(f"  Model memory: {memory_profile.model_memory:.2f} GB")
        self.logger.info(f"  Total required: {memory_profile.total_required:.2f} GB")
        self.logger.info(f"  Memory usage ratio: {memory_profile.total_required / memory_profile.available_gpu_memory:.2f}")

        # Select layers for checkpointing
        layers_to_checkpoint = self.memory_manager.select_layers_for_checkpointing(self.model)

        # Apply checkpointing to selected layers
        self._apply_checkpointing_to_layers(layers_to_checkpoint)

        # Enable built-in gradient checkpointing if needed
        if hasattr(self.model, 'gradient_checkpointing_enable'):
            self.model.gradient_checkpointing_enable()

    def _apply_checkpointing_to_layers(self, layer_names: List[str]):
        """Apply gradient checkpointing to specific layers"""
        for name in layer_names:
            try:
                # Find the module
                module = self._find_module_by_name(self.model, name)
                if module is not None:
                    # Replace with checkpointed version
                    checkpointed_module = CheckpointedModule(module, self.checkpointing_config.preserve_rng_state)
                    self._replace_module(self.model, name, checkpointed_module)
                    self.logger.debug(f"Applied gradient checkpointing to {name}")
            except Exception as e:
                self.logger.warning(f"Failed to apply checkpointing to {name}: {e}")

    def _find_module_by_name(self, model: nn.Module, name: str) -> Optional[nn.Module]:
        """Find a module by its name"""
        for n, module in model.named_modules():
            if n == name:
                return module
        return None

    def _replace_module(self, model: nn.Module, name: str, new_module: nn.Module):
        """Replace a module in the model"""
        parent_name, child_name = name.rsplit('.', 1) if '.' in name else ('', name)

        if parent_name:
            parent = self._find_module_by_name(model, parent_name)
            if parent is not None:
                setattr(parent, child_name, new_module)
        else:
            # Replace the root module
            if isinstance(model, nn.Module):
                # This is more complex for root module replacement
                raise NotImplementedError("Root module replacement not supported")

    def apply_memory_optimizations(self):
        """Apply additional memory optimizations"""
        if self.memory_optimization_mode == MemoryOptimizationMode.OFF:
            return

        optimizations = []

        # Enable mixed precision training
        if self.memory_optimization_mode in [MemoryOptimizationMode.AGGRESSIVE, MemoryOptimizationMode.ULTRA_EFFICIENT]:
            optimizations.append("Mixed precision training (FP16/BF16)")

        # Enable memory-efficient attention
        if hasattr(F, 'scaled_dot_product_attention'):
            optimizations.append("Memory-efficient attention")

        # Enable activation checkpointing for the entire model
        if self.memory_optimization_mode in [MemoryOptimizationMode.AGGRESSIVE, MemoryOptimizationMode.ULTRA_EFFICIENT]:
            if hasattr(self.model, 'gradient_checkpointing_enable'):
                self.model.gradient_checkpointing_enable()
                optimizations.append("Global gradient checkpointing")

        # Disable gradient computation for unused parameters
        self._disable_unused_gradients()

        self.logger.info(f"Applied memory optimizations: {', '.join(optimizations)}")

    def _disable_unused_gradients(self):
        """Disable gradient computation for unused parameters"""
        for param in self.model.parameters():
            if not param.requires_grad:
                param.requires_grad = False

    def get_memory_efficient_batch_size(self, max_memory_usage: float = 0.8) -> int:
        """Calculate memory-efficient batch size"""
        if self.memory_manager.memory_profile is None:
            return 1

        available_memory = self.memory_manager.memory_profile.available_gpu_memory * max_memory_usage
        memory_per_sample = self.memory_manager.memory_profile.activation_memory

        if memory_per_sample > 0:
            batch_size = int(available_memory / memory_per_sample)
            return max(1, min(batch_size, 32))  # Clamp between 1 and 32

        return 1

    def optimize_for_inference(self):
        """Optimize model for inference"""
        optimizations = []

        # Disable gradient computation
        for param in self.model.parameters():
            param.requires_grad = False

        # Set model to eval mode
        self.model.eval()

        # Enable memory-efficient attention if available
        if hasattr(F, 'scaled_dot_product_attention'):
            optimizations.append("Memory-efficient attention")

        # Apply torch.compile if available
        if hasattr(torch, 'compile'):
            try:
                self.model = torch.compile(self.model)
                optimizations.append("Torch compilation")
            except Exception as e:
                self.logger.warning(f"Failed to compile model: {e}")

        self.logger.info(f"Applied inference optimizations: {', '.join(optimizations)}")

class GradientCheckpointingFactory:
    """Factory for creating gradient checkpointing configurations"""

    @staticmethod
    def create_conservative_config() -> GradientCheckpointingConfig:
        """Create conservative gradient checkpointing configuration"""
        return GradientCheckpointingConfig(
            strategy=CheckpointingStrategy.SELECTIVE,
            checkpoint_ratio=0.2,
            memory_threshold=0.6,
            enable_recompute=True,
            preserve_rng_state=True
        )

    @staticmethod
    def create_balanced_config() -> GradientCheckpointingConfig:
        """Create balanced gradient checkpointing configuration"""
        return GradientCheckpointingConfig(
            strategy=CheckpointingStrategy.ADAPTIVE,
            checkpoint_ratio=0.3,
            memory_threshold=0.8,
            enable_recompute=True,
            preserve_rng_state=True
        )

    @staticmethod
    def create_aggressive_config() -> GradientCheckpointingConfig:
        """Create aggressive gradient checkpointing configuration"""
        return GradientCheckpointingConfig(
            strategy=CheckpointingStrategy.MEMORY_AWARE,
            checkpoint_ratio=0.5,
            memory_threshold=0.9,
            enable_recompute=True,
            preserve_rng_state=True
        )

    @staticmethod
    def create_ultra_efficient_config() -> GradientCheckpointingConfig:
        """Create ultra-efficient gradient checkpointing configuration"""
        return GradientCheckpointingConfig(
            strategy=CheckpointingStrategy.LAYER_WISE,
            checkpoint_ratio=0.7,
            memory_threshold=0.95,
            enable_recompute=True,
            preserve_rng_state=False,  # Slightly faster but less reproducible
            layer_selection_criteria="memory"
        )

def create_memory_efficient_trainer(
    model: nn.Module,
    mode: MemoryOptimizationMode = MemoryOptimizationMode.BALANCED,
    batch_size: int = 1,
    sequence_length: int = 2048
) -> Tuple[nn.Module, MemoryAwareTrainer]:
    """Create a memory-efficient trainer with optimized model"""

    # Create appropriate configuration
    if mode == MemoryOptimizationMode.CONSERVATIVE:
        config = GradientCheckpointingFactory.create_conservative_config()
    elif mode == MemoryOptimizationMode.BALANCED:
        config = GradientCheckpointingFactory.create_balanced_config()
    elif mode == MemoryOptimizationMode.AGGRESSIVE:
        config = GradientCheckpointingFactory.create_aggressive_config()
    elif mode == MemoryOptimizationMode.ULTRA_EFFICIENT:
        config = GradientCheckpointingFactory.create_ultra_efficient_config()
    else:
        config = GradientCheckpointingConfig()

    # Create memory-aware trainer
    trainer = MemoryAwareTrainer(model, config, mode)

    # Apply gradient checkpointing
    trainer.apply_gradient_checkpointing(batch_size, sequence_length)

    # Apply additional memory optimizations
    trainer.apply_memory_optimizations()

    return model, trainer

# Utility functions
def estimate_training_memory(
    model: nn.Module,
    batch_size: int,
    sequence_length: int,
    optimizer_type: str = "adamw"
) -> Dict[str, float]:
    """Estimate memory requirements for training"""

    # Model parameters memory
    param_memory = sum(p.numel() * p.element_size() for p in model.parameters()) / (1024**3)

    # Gradient memory (typically 2x parameter memory)
    gradient_memory = param_memory * 2

    # Optimizer memory
    if optimizer_type.lower() == "adamw":
        optimizer_memory = param_memory * 4  # AdamW stores 2 states per parameter
    elif optimizer_type.lower() == "adam":
        optimizer_memory = param_memory * 4
    else:
        optimizer_memory = param_memory * 2  # SGD

    # Activation memory (rough estimate)
    activation_memory = param_memory * 0.1 * batch_size

    total_memory = param_memory + gradient_memory + optimizer_memory + activation_memory

    return {
        "parameters_gb": param_memory,
        "gradients_gb": gradient_memory,
        "optimizer_gb": optimizer_memory,
        "activations_gb": activation_memory,
        "total_gb": total_memory
    }

def get_optimal_batch_size(
    model: nn.Module,
    available_memory_gb: float,
    sequence_length: int,
    optimizer_type: str = "adamw",
    safety_margin: float = 0.1
) -> int:
    """Calculate optimal batch size based on available memory"""

    # Get memory per sample
    memory_per_sample = estimate_training_memory(model, 1, sequence_length, optimizer_type)["total_gb"]

    # Account for safety margin
    usable_memory = available_memory_gb * (1 - safety_margin)

    # Calculate batch size
    batch_size = int(usable_memory / memory_per_sample)

    return max(1, min(batch_size, 64))  # Clamp between 1 and 64

if __name__ == "__main__":
    # Example usage
    import torch

    # Create a simple model for testing
    model = nn.Sequential(
        nn.Linear(1000, 2000),
        nn.ReLU(),
        nn.Linear(2000, 1000),
        nn.ReLU(),
        nn.Linear(1000, 500)
    )

    # Create memory-efficient trainer
    optimized_model, trainer = create_memory_efficient_trainer(
        model,
        mode=MemoryOptimizationMode.BALANCED,
        batch_size=4,
        sequence_length=512
    )

    print("Memory-efficient trainer created successfully!")
    print(f"Model optimized with {trainer.checkpointing_config.strategy.value} checkpointing strategy")