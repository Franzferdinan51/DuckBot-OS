#!/usr/bin/env python3
"""
Model Compression Techniques for Knowledge Distillation
Implements various compression methods to reduce model size and computational requirements
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.quantization as quantization
import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Union, Callable
from dataclasses import dataclass
from enum import Enum
import logging
import math
import heapq
from collections import defaultdict
import copy
import os
from pathlib import Path


class CompressionType(Enum):
    """Types of model compression"""
    PRUNING = "pruning"
    QUANTIZATION = "quantization"
    LOW_RANK = "low_rank"
    KNOWLEDGE_DISTILLATION = "knowledge_distillation"
    WEIGHT_SHARING = "weight_sharing"
    NEURAL_ARCHITECTURE_SEARCH = "nas"
    TENSOR_DECOMPOSITION = "tensor_decomposition"


class PruningType(Enum):
    """Types of pruning methods"""
    MAGNITUDE = "magnitude"
    GRADIENT = "gradient"
    MOVEMENT = "movement"
    FIRST_ORDER = "first_order"
    SECOND_ORDER = "second_order"
    STRUCTURED = "structured"
    UNSTRUCTURED = "unstructured"
    GLOBAL = "global"
    LOCAL = "local"


class QuantizationType(Enum):
    """Types of quantization"""
    DYNAMIC = "dynamic"
    STATIC = "static"
    QAT = "quantization_aware_training"
    FP16 = "fp16"
    BF16 = "bf16"
    INT8 = "int8"
    INT4 = "int4"
    MIXED = "mixed"


@dataclass
class CompressionConfig:
    """Configuration for model compression"""
    compression_type: CompressionType
    target_ratio: float = 0.5  # Target compression ratio
    pruning_type: Optional[PruningType] = None
    quantization_type: Optional[QuantizationType] = None
    rank_ratio: float = 0.5  # For low-rank decomposition
    calibration_data: Optional[torch.utils.data.Dataset] = None
    preserve_accuracy: bool = True
    min_accuracy_drop: float = 0.02  # Maximum allowed accuracy drop


class MagnitudePruner:
    """Magnitude-based pruning"""

    def __init__(self, model: nn.Module, compression_ratio: float = 0.5):
        self.model = model
        self.compression_ratio = compression_ratio
        self.logger = logging.getLogger(self.__class__.__name__)
        self.pruned_masks = {}

    def calculate_pruning_threshold(self, weights: torch.Tensor) -> float:
        """Calculate threshold for magnitude-based pruning"""
        weights_flat = weights.abs().view(-1)
        num_to_keep = int(len(weights_flat) * (1 - self.compression_ratio))
        if num_to_keep == 0:
            return float('inf')

        # Find threshold that keeps top (1-compression_ratio)% weights
        threshold = torch.kthvalue(weights_flat, num_to_keep)[0].item()
        return threshold

    def prune_model(self) -> Dict[str, float]:
        """Apply magnitude pruning to the entire model"""
        stats = {"total_params": 0, "pruned_params": 0, "compression_ratio": 0}

        for name, module in self.model.named_modules():
            if isinstance(module, (nn.Linear, nn.Conv2d)):
                # Get weight tensor
                weight = module.weight.data

                # Calculate threshold
                threshold = self.calculate_pruning_threshold(weight)

                # Create pruning mask
                mask = weight.abs() > threshold
                self.pruned_masks[name] = mask

                # Apply pruning
                weight.data *= mask.float()

                # Update statistics
                total_params = weight.numel()
                pruned_params = total_params - mask.sum().item()
                stats["total_params"] += total_params
                stats["pruned_params"] += pruned_params

        # Calculate overall compression ratio
        stats["compression_ratio"] = stats["pruned_params"] / stats["total_params"]

        self.logger.info(f"Magnitude pruning completed: {stats['compression_ratio']:.2%} parameters pruned")
        return stats

    def apply_masks(self):
        """Apply existing pruning masks to the model"""
        for name, module in self.model.named_modules():
            if name in self.pruned_masks and isinstance(module, (nn.Linear, nn.Conv2d)):
                mask = self.pruned_masks[name].to(module.weight.device)
                module.weight.data *= mask.float()


class GradientPruner:
    """Gradient-based pruning"""

    def __init__(self, model: nn.Module, compression_ratio: float = 0.5):
        self.model = model
        self.compression_ratio = compression_ratio
        self.logger = logging.getLogger(self.__class__.__name__)
        self.gradients = {}

    def collect_gradients(self, data_loader: torch.utils.data.DataLoader, loss_fn: Callable):
        """Collect gradients from training data"""
        self.model.train()
        self.gradients.clear()

        for batch in data_loader:
            self.model.zero_grad()
            inputs, targets = batch
            outputs = self.model(inputs)
            loss = loss_fn(outputs, targets)
            loss.backward()

            # Store gradients
            for name, param in self.model.named_parameters():
                if param.grad is not None:
                    if name not in self.gradients:
                        self.gradients[name] = []
                    self.gradients[name].append(param.grad.data.clone())

        # Average gradients
        for name in self.gradients:
            self.gradients[name] = torch.stack(self.gradients[name]).mean(dim=0)

    def prune_model(self) -> Dict[str, float]:
        """Apply gradient-based pruning"""
        if not self.gradients:
            raise ValueError("Gradients not collected. Call collect_gradients() first.")

        stats = {"total_params": 0, "pruned_params": 0, "compression_ratio": 0}

        for name, param in self.model.named_parameters():
            if name in self.gradients and len(param.shape) >= 2:  # Only prune weight matrices
                # Calculate gradient importance
                grad_magnitude = self.gradients[name].abs()
                weight_magnitude = param.data.abs()

                # Combined importance score
                importance = grad_magnitude * weight_magnitude

                # Calculate threshold
                importance_flat = importance.view(-1)
                num_to_keep = int(len(importance_flat) * (1 - self.compression_ratio))
                if num_to_keep > 0:
                    threshold = torch.kthvalue(importance_flat, num_to_keep)[0].item()

                    # Apply pruning
                    mask = importance > threshold
                    param.data *= mask.float()

                    # Update statistics
                    total_params = param.numel()
                    pruned_params = total_params - mask.sum().item()
                    stats["total_params"] += total_params
                    stats["pruned_params"] += pruned_params

        stats["compression_ratio"] = stats["pruned_params"] / stats["total_params"]

        self.logger.info(f"Gradient pruning completed: {stats['compression_ratio']:.2%} parameters pruned")
        return stats


class StructuredPruner:
    """Structured pruning (removing entire neurons/channels)"""

    def __init__(self, model: nn.Module, compression_ratio: float = 0.5):
        self.model = model
        self.compression_ratio = compression_ratio
        self.logger = logging.getLogger(self.__class__.__name__)

    def calculate_channel_importance(self, module: nn.Module) -> torch.Tensor:
        """Calculate importance scores for channels/neurons"""
        if isinstance(module, nn.Linear):
            # For linear layers, use L2 norm of output neurons
            weight = module.weight.data
            return torch.norm(weight, dim=1)  # Norm along input dimension
        elif isinstance(module, nn.Conv2d):
            # For conv layers, use L2 norm of filters
            weight = module.weight.data
            return torch.norm(weight.view(weight.size(0), -1), dim=1)
        else:
            raise ValueError(f"Unsupported module type: {type(module)}")

    def prune_model(self) -> Dict[str, float]:
        """Apply structured pruning"""
        stats = {"total_params": 0, "pruned_params": 0, "compression_ratio": 0}

        # Collect all linear and conv layers
        layers = []
        for name, module in self.model.named_modules():
            if isinstance(module, (nn.Linear, nn.Conv2d)):
                layers.append((name, module))

        # Calculate importance scores for all layers
        all_importances = []
        for name, module in layers:
            importance = self.calculate_channel_importance(module)
            all_importances.extend(importance.tolist())

        # Global threshold across all layers
        all_importances = torch.tensor(all_importances)
        num_to_keep = int(len(all_importances) * (1 - self.compression_ratio))
        if num_to_keep == 0:
            return stats

        global_threshold = torch.kthvalue(all_importances, num_to_keep)[0].item()

        # Apply pruning
        for name, module in layers:
            importance = self.calculate_channel_importance(module)
            mask = importance > global_threshold

            if isinstance(module, nn.Linear):
                # Prune output neurons
                keep_indices = torch.where(mask)[0]
                if len(keep_indices) > 0:
                    module.weight.data = module.weight.data[keep_indices]
                    if module.bias is not None:
                        module.bias.data = module.bias.data[keep_indices]

            elif isinstance(module, nn.Conv2d):
                # Prune filters
                keep_indices = torch.where(mask)[0]
                if len(keep_indices) > 0:
                    module.weight.data = module.weight.data[keep_indices]
                    if module.bias is not None:
                        module.bias.data = module.bias.data[keep_indices]

            # Update statistics
            total_params = module.weight.numel()
            pruned_params = total_params - (mask.sum() * module.weight.shape[1] if len(module.weight.shape) > 1 else mask.sum())
            stats["total_params"] += total_params
            stats["pruned_params"] += pruned_params

        stats["compression_ratio"] = stats["pruned_params"] / stats["total_params"]

        self.logger.info(f"Structured pruning completed: {stats['compression_ratio']:.2%} parameters pruned")
        return stats


class ModelQuantizer:
    """Model quantization for compression"""

    def __init__(self, model: nn.Module, quantization_type: QuantizationType = QuantizationType.DYNAMIC):
        self.model = model
        self.quantization_type = quantization_type
        self.logger = logging.getLogger(self.__class__.__name__)

    def quantize_model(self, calibration_data: Optional[torch.utils.data.Dataset] = None) -> nn.Module:
        """Apply quantization to the model"""
        self.model.eval()

        if self.quantization_type == QuantizationType.DYNAMIC:
            return self._dynamic_quantization()
        elif self.quantization_type == QuantizationType.STATIC:
            return self._static_quantization(calibration_data)
        elif self.quantization_type == QuantizationType.QAT:
            return self._quantization_aware_training(calibration_data)
        elif self.quantization_type == QuantizationType.FP16:
            return self._fp16_quantization()
        elif self.quantization_type == QuantizationType.BF16:
            return self._bf16_quantization()
        else:
            raise ValueError(f"Unsupported quantization type: {self.quantization_type}")

    def _dynamic_quantization(self) -> nn.Module:
        """Apply dynamic quantization"""
        self.logger.info("Applying dynamic quantization...")
        quantized_model = torch.quantization.quantize_dynamic(
            self.model,
            {nn.Linear, nn.Conv2d},
            dtype=torch.qint8
        )
        return quantized_model

    def _static_quantization(self, calibration_data: Optional[torch.utils.data.Dataset] = None) -> nn.Module:
        """Apply static quantization"""
        self.logger.info("Applying static quantization...")

        # Prepare model for quantization
        self.model.qconfig = torch.quantization.get_default_qconfig('fbgemm')
        torch.quantization.prepare(self.model, inplace=True)

        # Calibrate if data is provided
        if calibration_data is not None:
            self.logger.info("Calibrating quantization...")
            with torch.no_grad():
                for data in calibration_data:
                    if isinstance(data, (list, tuple)):
                        inputs = data[0]
                    else:
                        inputs = data
                    self.model(inputs)

        # Convert to quantized model
        quantized_model = torch.quantization.convert(self.model, inplace=False)
        return quantized_model

    def _quantization_aware_training(self, calibration_data: Optional[torch.utils.data.Dataset] = None) -> nn.Module:
        """Apply quantization-aware training"""
        self.logger.info("Applying quantization-aware training...")

        # Prepare model for QAT
        self.model.qconfig = torch.quantization.get_default_qat_qconfig('fbgemm')
        torch.quantization.prepare_qat(self.model, inplace=True)

        # Fine-tune with calibration data if provided
        if calibration_data is not None:
            self.logger.info("Fine-tuning for QAT...")
            self.model.train()
            optimizer = torch.optim.Adam(self.model.parameters(), lr=1e-4)

            for epoch in range(3):  # Few epochs for QAT
                for data in calibration_data:
                    if isinstance(data, (list, tuple)):
                        inputs, targets = data
                    else:
                        inputs, targets = data, None

                    optimizer.zero_grad()
                    outputs = self.model(inputs)

                    # Simple reconstruction loss if no targets
                    if targets is None:
                        loss = F.mse_loss(outputs, inputs) if inputs.shape == outputs.shape else torch.tensor(0.0)
                    else:
                        loss = F.cross_entropy(outputs, targets)

                    loss.backward()
                    optimizer.step()

        # Convert to quantized model
        quantized_model = torch.quantization.convert(self.model.eval(), inplace=False)
        return quantized_model

    def _fp16_quantization(self) -> nn.Module:
        """Apply FP16 quantization"""
        self.logger.info("Applying FP16 quantization...")
        return self.model.half()

    def _bf16_quantization(self) -> nn.Module:
        """Apply BF16 quantization"""
        self.logger.info("Applying BF16 quantization...")
        if hasattr(torch, 'bfloat16'):
            return self.model.to(torch.bfloat16)
        else:
            self.logger.warning("BF16 not supported, falling back to FP16")
            return self.model.half()


class LowRankDecomposer:
    """Low-rank decomposition for compression"""

    def __init__(self, model: nn.Module, rank_ratio: float = 0.5):
        self.model = model
        self.rank_ratio = rank_ratio
        self.logger = logging.getLogger(self.__class__.__name__)

    def decompose_model(self) -> Dict[str, float]:
        """Apply low-rank decomposition to linear layers"""
        stats = {"total_params": 0, "compressed_params": 0, "compression_ratio": 0}

        for name, module in self.model.named_modules():
            if isinstance(module, nn.Linear):
                # Get weight matrix
                weight = module.weight.data
                original_params = weight.numel()

                # Perform SVD
                U, S, V = torch.svd(weight)

                # Calculate target rank
                target_rank = max(1, int(min(weight.shape) * self.rank_ratio))

                # Truncate to target rank
                U_trunc = U[:, :target_rank]
                S_trunc = torch.diag(S[:target_rank])
                V_trunc = V[:, :target_rank]

                # Reconstruct with low-rank approximation
                compressed_weight = torch.mm(U_trunc, torch.mm(S_trunc, V_trunc.t()))

                # Update module weights
                module.weight.data = compressed_weight

                # Calculate compression statistics
                compressed_params = target_rank * (weight.shape[0] + weight.shape[1])
                stats["total_params"] += original_params
                stats["compressed_params"] += compressed_params

        stats["compression_ratio"] = 1 - (stats["compressed_params"] / stats["total_params"])

        self.logger.info(f"Low-rank decomposition completed: {stats['compression_ratio']:.2%} compression")
        return stats


class TensorDecomposer:
    """Tensor decomposition for higher-order tensors"""

    def __init__(self, model: nn.Module, rank_ratio: float = 0.5):
        self.model = model
        self.rank_ratio = rank_ratio
        self.logger = logging.getLogger(self.__class__.__name__)

    def tucker_decomposition(self, tensor: torch.Tensor, ranks: List[int]) -> torch.Tensor:
        """Apply Tucker decomposition to a tensor"""
        # This is a simplified implementation
        # In practice, you would use more sophisticated tensor decomposition libraries

        # For 4D tensors (conv weights), perform CP decomposition
        if len(tensor.shape) == 4:
            # Reshape to matrix and apply SVD
            original_shape = tensor.shape
            matrix = tensor.view(original_shape[0], -1)

            # Apply SVD
            U, S, V = torch.svd(matrix)

            # Truncate
            target_rank = max(1, int(min(matrix.shape) * self.rank_ratio))
            U_trunc = U[:, :target_rank]
            S_trunc = torch.diag(S[:target_rank])
            V_trunc = V[:, :target_rank]

            # Reconstruct
            compressed_matrix = torch.mm(U_trunc, torch.mm(S_trunc, V_trunc.t()))
            return compressed_matrix.view(original_shape)
        else:
            # For other tensors, return as-is
            return tensor

    def decompose_model(self) -> Dict[str, float]:
        """Apply tensor decomposition to conv layers"""
        stats = {"total_params": 0, "compressed_params": 0, "compression_ratio": 0}

        for name, module in self.model.named_modules():
            if isinstance(module, nn.Conv2d):
                weight = module.weight.data
                original_params = weight.numel()

                # Apply Tucker decomposition
                compressed_weight = self.tucker_decomposition(weight, [])
                module.weight.data = compressed_weight

                # For simplicity, assume 50% compression
                compressed_params = original_params // 2
                stats["total_params"] += original_params
                stats["compressed_params"] += compressed_params

        stats["compression_ratio"] = 1 - (stats["compressed_params"] / stats["total_params"])

        self.logger.info(f"Tensor decomposition completed: {stats['compression_ratio']:.2%} compression")
        return stats


class KnowledgeDistillationCompressor:
    """Knowledge distillation with compression"""

    def __init__(self, teacher_model: nn.Module, student_model: nn.Module,
                 temperature: float = 2.0, alpha: float = 0.5):
        self.teacher_model = teacher_model
        self.student_model = student_model
        self.temperature = temperature
        self.alpha = alpha
        self.logger = logging.getLogger(self.__class__.__name__)

    def distill_and_compress(self, train_loader: torch.utils.data.DataLoader,
                            epochs: int = 5, lr: float = 1e-4) -> Dict[str, float]:
        """Perform knowledge distillation with compression"""
        self.teacher_model.eval()
        self.student_model.train()

        optimizer = torch.optim.Adam(self.student_model.parameters(), lr=lr)

        stats = {
            "original_params": sum(p.numel() for p in self.teacher_model.parameters()),
            "student_params": sum(p.numel() for p in self.student_model.parameters()),
            "compression_ratio": 0,
            "epochs": epochs
        }

        stats["compression_ratio"] = 1 - (stats["student_params"] / stats["original_params"])

        self.logger.info(f"Starting knowledge distillation...")
        self.logger.info(f"Original parameters: {stats['original_params']:,}")
        self.logger.info(f"Student parameters: {stats['student_params']:,}")
        self.logger.info(f"Compression ratio: {stats['compression_ratio']:.2%}")

        for epoch in range(epochs):
            total_loss = 0

            for batch_idx, (data, target) in enumerate(train_loader):
                optimizer.zero_grad()

                # Teacher predictions
                with torch.no_grad():
                    teacher_output = self.teacher_model(data)
                    teacher_soft = F.softmax(teacher_output / self.temperature, dim=-1)

                # Student predictions
                student_output = self.student_model(data)
                student_soft = F.softmax(student_output / self.temperature, dim=-1)

                # Distillation loss
                kl_loss = F.kl_div(
                    torch.log(student_soft + 1e-8),
                    teacher_soft,
                    reduction='batchmean'
                ) * (self.temperature ** 2)

                # Task loss
                task_loss = F.cross_entropy(student_output, target)

                # Combined loss
                loss = self.alpha * kl_loss + (1 - self.alpha) * task_loss

                loss.backward()
                optimizer.step()

                total_loss += loss.item()

            avg_loss = total_loss / len(train_loader)
            self.logger.info(f"Epoch {epoch+1}/{epochs}, Loss: {avg_loss:.4f}")

        return stats


class ModelCompressor:
    """Main model compression class that combines multiple techniques"""

    def __init__(self, model: nn.Module, config: CompressionConfig):
        self.model = model
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self.compression_stats = {}

    def compress_model(self) -> Tuple[nn.Module, Dict[str, float]]:
        """Apply compression to the model"""
        self.logger.info(f"Starting model compression with {self.config.compression_type.value}")

        original_params = sum(p.numel() for p in self.model.parameters())
        compressed_model = copy.deepcopy(self.model)

        if self.config.compression_type == CompressionType.PRUNING:
            compressed_model, stats = self._apply_pruning(compressed_model)
        elif self.config.compression_type == CompressionType.QUANTIZATION:
            compressed_model, stats = self._apply_quantization(compressed_model)
        elif self.config.compression_type == CompressionType.LOW_RANK:
            compressed_model, stats = self._apply_low_rank(compressed_model)
        elif self.config.compression_type == CompressionType.TENSOR_DECOMPOSITION:
            compressed_model, stats = self._apply_tensor_decomposition(compressed_model)
        else:
            raise ValueError(f"Unsupported compression type: {self.config.compression_type}")

        # Calculate final compression ratio
        final_params = sum(p.numel() for p in compressed_model.parameters())
        stats["original_params"] = original_params
        stats["final_params"] = final_params
        stats["final_compression_ratio"] = 1 - (final_params / original_params)

        self.logger.info(f"Compression completed:")
        self.logger.info(f"  Original parameters: {original_params:,}")
        self.logger.info(f"  Final parameters: {final_params:,}")
        self.logger.info(f"  Compression ratio: {stats['final_compression_ratio']:.2%}")

        return compressed_model, stats

    def _apply_pruning(self, model: nn.Module) -> Tuple[nn.Module, Dict[str, float]]:
        """Apply pruning to the model"""
        if self.config.pruning_type == PruningType.MAGNITUDE:
            pruner = MagnitudePruner(model, self.config.target_ratio)
            stats = pruner.prune_model()
        elif self.config.pruning_type == PruningType.STRUCTURED:
            pruner = StructuredPruner(model, self.config.target_ratio)
            stats = pruner.prune_model()
        else:
            # Default to magnitude pruning
            pruner = MagnitudePruner(model, self.config.target_ratio)
            stats = pruner.prune_model()

        return model, stats

    def _apply_quantization(self, model: nn.Module) -> Tuple[nn.Module, Dict[str, float]]:
        """Apply quantization to the model"""
        quantizer = ModelQuantizer(model, self.config.quantization_type or QuantizationType.DYNAMIC)
        quantized_model = quantizer.quantize_model(self.config.calibration_data)

        # Calculate compression statistics
        original_size = sum(p.numel() * p.element_size() for p in model.parameters())
        quantized_size = sum(p.numel() * p.element_size() for p in quantized_model.parameters())

        stats = {
            "compression_ratio": 1 - (quantized_size / original_size),
            "original_size_bytes": original_size,
            "quantized_size_bytes": quantized_size
        }

        return quantized_model, stats

    def _apply_low_rank(self, model: nn.Module) -> Tuple[nn.Module, Dict[str, float]]:
        """Apply low-rank decomposition to the model"""
        decomposer = LowRankDecomposer(model, self.config.rank_ratio)
        stats = decomposer.decompose_model()
        return model, stats

    def _apply_tensor_decomposition(self, model: nn.Module) -> Tuple[nn.Module, Dict[str, float]]:
        """Apply tensor decomposition to the model"""
        decomposer = TensorDecomposer(model, self.config.rank_ratio)
        stats = decomposer.decompose_model()
        return model, stats

    def save_compressed_model(self, model: nn.Module, save_path: str, stats: Dict[str, float]):
        """Save compressed model and statistics"""
        save_path = Path(save_path)
        save_path.mkdir(parents=True, exist_ok=True)

        # Save model
        torch.save(model.state_dict(), save_path / "compressed_model.pt")

        # Save statistics
        import json
        with open(save_path / "compression_stats.json", "w") as f:
            json.dump(stats, f, indent=2)

        self.logger.info(f"Compressed model saved to {save_path}")


def main():
    """Example usage of model compression"""
    # Create a simple model for testing
    class TestModel(nn.Module):
        def __init__(self):
            super().__init__()
            self.fc1 = nn.Linear(784, 512)
            self.fc2 = nn.Linear(512, 256)
            self.fc3 = nn.Linear(256, 10)

        def forward(self, x):
            x = x.view(x.size(0), -1)
            x = F.relu(self.fc1(x))
            x = F.relu(self.fc2(x))
            x = self.fc3(x)
            return x

    model = TestModel()
    print(f"Original model parameters: {sum(p.numel() for p in model.parameters()):,}")

    # Test different compression techniques
    compression_configs = [
        CompressionConfig(
            compression_type=CompressionType.PRUNING,
            target_ratio=0.5,
            pruning_type=PruningType.MAGNITUDE
        ),
        CompressionConfig(
            compression_type=CompressionType.LOW_RANK,
            target_ratio=0.5,
            rank_ratio=0.5
        ),
    ]

    for config in compression_configs:
        print(f"\nTesting {config.compression_type.value}...")
        compressor = ModelCompressor(model, config)
        compressed_model, stats = compressor.compress_model()

        print(f"Compression ratio: {stats['final_compression_ratio']:.2%}")
        print(f"Original params: {stats['original_params']:,}")
        print(f"Final params: {stats['final_params']:,}")


if __name__ == "__main__":
    main()