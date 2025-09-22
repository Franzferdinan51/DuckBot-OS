#!/usr/bin/env python3
"""
Teacher-Student Model Combinations for Knowledge Distillation
Supports various model architectures, automatic architecture matching, and model generation
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from transformers import (
    AutoModelForCausalLM, AutoTokenizer, AutoModelForSequenceClassification,
    PreTrainedModel, PreTrainedTokenizer, GPT2Config, GPT2LMHeadModel,
    BertConfig, BertForSequenceClassification, DistilBertConfig, DistilBertForSequenceClassification
)
import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Union, Callable
from dataclasses import dataclass
from enum import Enum
import logging
import json
from pathlib import Path
import copy
import math
from abc import ABC, abstractmethod


class ModelType(Enum):
    """Supported model types"""
    GPT2 = "gpt2"
    BERT = "bert"
    DISTILBERT = "distilbert"
    ROBERTA = "roberta"
    T5 = "t5"
    LLAMA = "llama"
    CUSTOM = "custom"


class ArchitectureStrategy(Enum):
    """Student architecture creation strategies"""
    MANUAL = "manual"                    # Manually specified student architecture
    SCALING = "scaling"                  # Scale down teacher architecture
    PRUNING = "pruning"                  # Prune teacher architecture
    LOW_RANK = "low_rank"                # Low-rank factorization
    BLOCK_REDUCTION = "block_reduction"   # Reduce number of blocks/layers
    WIDTH_REDUCTION = "width_reduction"   # Reduce hidden dimension
    ATTENTION_REDUCTION = "attention_reduction"  # Reduce attention heads


@dataclass
class TeacherStudentConfig:
    """Configuration for teacher-student model pairs"""
    teacher_model_path: str
    student_model_path: Optional[str] = None  # None for automatic generation
    model_type: ModelType = ModelType.GPT2
    architecture_strategy: ArchitectureStrategy = ArchitectureStrategy.SCALING
    scaling_factor: float = 0.5  # Factor for scaling down architecture
    num_layers_teacher: Optional[int] = None
    num_layers_student: Optional[int] = None
    hidden_size_teacher: Optional[int] = None
    hidden_size_student: Optional[int] = None
    num_attention_heads_teacher: Optional[int] = None
    num_attention_heads_student: Optional[int] = None
    intermediate_size_teacher: Optional[int] = None
    intermediate_size_student: Optional[int] = None


class ModelArchitectureAnalyzer:
    """Analyzes model architecture and extracts key parameters"""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def analyze_model(self, model: PreTrainedModel) -> Dict[str, Any]:
        """Analyze model architecture and extract key parameters"""
        analysis = {
            "model_type": model.config.model_type,
            "num_layers": 0,
            "hidden_size": 0,
            "num_attention_heads": 0,
            "intermediate_size": 0,
            "vocab_size": 0,
            "max_position_embeddings": 0,
            "total_parameters": 0,
            "trainable_parameters": 0,
            "architecture_details": {}
        }

        # Extract basic information from config
        config = model.config

        analysis["vocab_size"] = getattr(config, "vocab_size", 0)
        analysis["max_position_embeddings"] = getattr(config, "max_position_embeddings", 0)

        # Extract model-specific parameters
        if hasattr(config, "n_layer"):
            analysis["num_layers"] = config.n_layer
        elif hasattr(config, "num_hidden_layers"):
            analysis["num_layers"] = config.num_hidden_layers

        if hasattr(config, "n_embd"):
            analysis["hidden_size"] = config.n_embd
        elif hasattr(config, "hidden_size"):
            analysis["hidden_size"] = config.hidden_size

        if hasattr(config, "n_head"):
            analysis["num_attention_heads"] = config.n_head
        elif hasattr(config, "num_attention_heads"):
            analysis["num_attention_heads"] = config.num_attention_heads

        if hasattr(config, "n_inner"):
            analysis["intermediate_size"] = config.n_inner
        elif hasattr(config, "intermediate_size"):
            analysis["intermediate_size"] = config.intermediate_size

        # Count parameters
        analysis["total_parameters"] = sum(p.numel() for p in model.parameters())
        analysis["trainable_parameters"] = sum(p.numel() for p in model.parameters() if p.requires_grad)

        # Analyze detailed architecture
        analysis["architecture_details"] = self._analyze_architecture_details(model)

        return analysis

    def _analyze_architecture_details(self, model: PreTrainedModel) -> Dict[str, Any]:
        """Analyze detailed architecture information"""
        details = {
            "layer_types": {},
            "parameter_distribution": {},
            "activation_functions": set()
        }

        for name, module in model.named_modules():
            # Count layer types
            layer_type = type(module).__name__
            details["layer_types"][layer_type] = details["layer_types"].get(layer_type, 0) + 1

            # Count parameters by type
            for param_name, param in module.named_parameters():
                if param.requires_grad:
                    param_type = f"{layer_type}.{param_name}"
                    details["parameter_distribution"][param_type] = details["parameter_distribution"].get(param_type, 0) + param.numel()

            # Detect activation functions
            if hasattr(module, 'activation'):
                details["activation_functions"].add(type(module.activation).__name__)

        return details

    def compare_architectures(self, teacher_analysis: Dict[str, Any],
                            student_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Compare teacher and student architectures"""
        comparison = {
            "size_ratio": student_analysis["total_parameters"] / teacher_analysis["total_parameters"],
            "layer_ratio": student_analysis["num_layers"] / teacher_analysis["num_layers"],
            "hidden_size_ratio": student_analysis["hidden_size"] / teacher_analysis["hidden_size"],
            "attention_heads_ratio": student_analysis["num_attention_heads"] / teacher_analysis["num_attention_heads"],
            "compression_efficiency": 0.0
        }

        # Calculate compression efficiency
        teacher_params = teacher_analysis["total_parameters"]
        student_params = student_analysis["total_parameters"]
        if student_params < teacher_params:
            comparison["compression_efficiency"] = 1.0 - (student_params / teacher_params)

        return comparison


class StudentArchitectureGenerator:
    """Generates student model architectures based on teacher models"""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def create_student_model(self, teacher_model: PreTrainedModel,
                           strategy: ArchitectureStrategy,
                           config: TeacherStudentConfig) -> PreTrainedModel:
        """Create student model architecture based on teacher and strategy"""
        self.logger.info(f"Creating student model using {strategy.value} strategy")

        if strategy == ArchitectureStrategy.MANUAL:
            return self._create_manual_student(teacher_model, config)
        elif strategy == ArchitectureStrategy.SCALING:
            return self._create_scaled_student(teacher_model, config)
        elif strategy == ArchitectureStrategy.BLOCK_REDUCTION:
            return self._create_block_reduced_student(teacher_model, config)
        elif strategy == ArchitectureStrategy.WIDTH_REDUCTION:
            return self._create_width_reduced_student(teacher_model, config)
        elif strategy == ArchitectureStrategy.ATTENTION_REDUCTION:
            return self._create_attention_reduced_student(teacher_model, config)
        else:
            raise ValueError(f"Unsupported architecture strategy: {strategy}")

    def _create_manual_student(self, teacher_model: PreTrainedModel,
                              config: TeacherStudentConfig) -> PreTrainedModel:
        """Create student model with manually specified architecture"""
        if config.student_model_path:
            # Load existing student model
            return AutoModelForCausalLM.from_pretrained(config.student_model_path)
        else:
            # Create new model based on specified parameters
            return self._create_custom_student(teacher_model, config)

    def _create_scaled_student(self, teacher_model: PreTrainedModel,
                             config: TeacherStudentConfig) -> PreTrainedModel:
        """Create student model by scaling down teacher architecture"""
        teacher_config = teacher_model.config

        # Create new config with scaled parameters
        student_config = copy.deepcopy(teacher_config)

        # Scale number of layers
        if hasattr(student_config, "n_layer"):
            student_config.n_layer = max(1, int(student_config.n_layer * config.scaling_factor))
        elif hasattr(student_config, "num_hidden_layers"):
            student_config.num_hidden_layers = max(1, int(student_config.num_hidden_layers * config.scaling_factor))

        # Scale hidden size
        if hasattr(student_config, "n_embd"):
            student_config.n_embd = max(128, int(student_config.n_embd * math.sqrt(config.scaling_factor)))
        elif hasattr(student_config, "hidden_size"):
            student_config.hidden_size = max(128, int(student_config.hidden_size * math.sqrt(config.scaling_factor)))

        # Scale intermediate size
        if hasattr(student_config, "n_inner"):
            student_config.n_inner = max(512, int(student_config.n_inner * config.scaling_factor))
        elif hasattr(student_config, "intermediate_size"):
            student_config.intermediate_size = max(512, int(student_config.intermediate_size * config.scaling_factor))

        # Scale attention heads
        if hasattr(student_config, "n_head"):
            student_config.n_head = max(1, int(student_config.n_head * math.sqrt(config.scaling_factor)))
        elif hasattr(student_config, "num_attention_heads"):
            student_config.num_attention_heads = max(1, int(student_config.num_attention_heads * math.sqrt(config.scaling_factor)))

        # Create student model
        student_model = type(teacher_model)(student_config)

        # Initialize weights from teacher (with resizing)
        self._initialize_from_teacher(student_model, teacher_model)

        return student_model

    def _create_block_reduced_student(self, teacher_model: PreTrainedModel,
                                    config: TeacherStudentConfig) -> PreTrainedModel:
        """Create student model by reducing number of blocks/layers"""
        teacher_config = teacher_model.config

        student_config = copy.deepcopy(teacher_config)

        # Reduce number of layers
        target_layers = config.num_layers_student
        if target_layers is None:
            target_layers = max(1, int(getattr(teacher_config, "n_layer", getattr(teacher_config, "num_hidden_layers", 12)) * config.scaling_factor))

        if hasattr(student_config, "n_layer"):
            student_config.n_layer = target_layers
        elif hasattr(student_config, "num_hidden_layers"):
            student_config.num_hidden_layers = target_layers

        # Create student model
        student_model = type(teacher_model)(student_config)

        # Copy weights from teacher layers
        self._copy_layer_weights(student_model, teacher_model, target_layers)

        return student_model

    def _create_width_reduced_student(self, teacher_model: PreTrainedModel,
                                     config: TeacherStudentConfig) -> PreTrainedModel:
        """Create student model by reducing hidden dimension width"""
        teacher_config = teacher_model.config

        student_config = copy.deepcopy(teacher_config)

        # Reduce hidden size
        target_hidden_size = config.hidden_size_student
        if target_hidden_size is None:
            current_hidden_size = getattr(teacher_config, "n_embd", getattr(teacher_config, "hidden_size", 768))
            target_hidden_size = max(256, int(current_hidden_size * config.scaling_factor))

        if hasattr(student_config, "n_embd"):
            student_config.n_embd = target_hidden_size
        elif hasattr(student_config, "hidden_size"):
            student_config.hidden_size = target_hidden_size

        # Adjust intermediate size proportionally
        if hasattr(student_config, "n_inner"):
            student_config.n_inner = max(512, int(target_hidden_size * 4))
        elif hasattr(student_config, "intermediate_size"):
            student_config.intermediate_size = max(512, int(target_hidden_size * 4))

        # Create student model
        student_model = type(teacher_model)(student_config)

        # Initialize with projected weights
        self._initialize_with_projection(student_model, teacher_model)

        return student_model

    def _create_attention_reduced_student(self, teacher_model: PreTrainedModel,
                                        config: TeacherStudentConfig) -> PreTrainedModel:
        """Create student model by reducing number of attention heads"""
        teacher_config = teacher_model.config

        student_config = copy.deepcopy(teacher_config)

        # Reduce attention heads
        target_heads = config.num_attention_heads_student
        if target_heads is None:
            current_heads = getattr(teacher_config, "n_head", getattr(teacher_config, "num_attention_heads", 12))
            target_heads = max(1, int(current_heads * config.scaling_factor))

        if hasattr(student_config, "n_head"):
            student_config.n_head = target_heads
        elif hasattr(student_config, "num_attention_heads"):
            student_config.num_attention_heads = target_heads

        # Create student model
        student_model = type(teacher_model)(student_config)

        # Initialize weights with attention head adjustment
        self._initialize_attention_weights(student_model, teacher_model)

        return student_model

    def _create_custom_student(self, teacher_model: PreTrainedModel,
                             config: TeacherStudentConfig) -> PreTrainedModel:
        """Create custom student model with specified parameters"""
        teacher_config = teacher_model.config

        # Create custom config
        student_config = copy.deepcopy(teacher_config)

        # Apply custom parameters
        if config.num_layers_student is not None:
            if hasattr(student_config, "n_layer"):
                student_config.n_layer = config.num_layers_student
            elif hasattr(student_config, "num_hidden_layers"):
                student_config.num_hidden_layers = config.num_layers_student

        if config.hidden_size_student is not None:
            if hasattr(student_config, "n_embd"):
                student_config.n_embd = config.hidden_size_student
            elif hasattr(student_config, "hidden_size"):
                student_config.hidden_size = config.hidden_size_student

        if config.num_attention_heads_student is not None:
            if hasattr(student_config, "n_head"):
                student_config.n_head = config.num_attention_heads_student
            elif hasattr(student_config, "num_attention_heads"):
                student_config.num_attention_heads = config.num_attention_heads_student

        if config.intermediate_size_student is not None:
            if hasattr(student_config, "n_inner"):
                student_config.n_inner = config.intermediate_size_student
            elif hasattr(student_config, "intermediate_size"):
                student_config.intermediate_size = config.intermediate_size_student

        # Create student model
        student_model = type(teacher_model)(student_config)

        # Initialize weights
        self._initialize_from_teacher(student_model, teacher_model)

        return student_model

    def _initialize_from_teacher(self, student_model: PreTrainedModel, teacher_model: PreTrainedModel):
        """Initialize student model weights from teacher model"""
        student_dict = student_model.state_dict()
        teacher_dict = teacher_model.state_dict()

        # Copy matching layers
        for name in student_dict:
            if name in teacher_dict and student_dict[name].shape == teacher_dict[name].shape:
                student_dict[name].copy_(teacher_dict[name])

        student_model.load_state_dict(student_dict)

    def _copy_layer_weights(self, student_model: PreTrainedModel, teacher_model: PreTrainedModel,
                          num_student_layers: int):
        """Copy weights from teacher layers to student layers"""
        teacher_dict = teacher_model.state_dict()
        student_dict = student_model.state_dict()

        # Calculate layer mapping
        num_teacher_layers = len([k for k in teacher_dict.keys() if 'h.' in k and '.weight' in k])
        layer_mapping = self._create_layer_mapping(num_teacher_layers, num_student_layers)

        # Copy weights based on mapping
        for student_layer, teacher_layer in layer_mapping.items():
            # Copy transformer blocks
            for param_type in ['.weight', '.bias']:
                student_key = f'transformer.h.{student_layer}.{param_type}'
                teacher_key = f'transformer.h.{teacher_layer}.{param_type}'

                if student_key in student_dict and teacher_key in teacher_dict:
                    if student_dict[student_key].shape == teacher_dict[teacher_key].shape:
                        student_dict[student_key].copy_(teacher_dict[teacher_key])

        student_model.load_state_dict(student_dict)

    def _initialize_with_projection(self, student_model: PreTrainedModel, teacher_model: PreTrainedModel):
        """Initialize student model with projected weights from teacher"""
        teacher_dict = teacher_model.state_dict()
        student_dict = student_model.state_dict()

        # Project weights for different dimensions
        for name in student_dict:
            if name in teacher_dict:
                teacher_weight = teacher_dict[name]
                student_weight = student_dict[name]

                if len(teacher_weight.shape) == 2:  # Linear layers
                    # Use SVD for weight projection
                    U, S, V = torch.svd(teacher_weight)
                    target_rank = min(student_weight.shape)
                    U_reduced = U[:, :target_rank]
                    S_reduced = torch.diag(S[:target_rank])
                    V_reduced = V[:, :target_rank]

                    projected_weight = torch.mm(U_reduced, torch.mm(S_reduced, V_reduced.t()))
                    if projected_weight.shape == student_weight.shape:
                        student_dict[name].copy_(projected_weight)

        student_model.load_state_dict(student_dict)

    def _initialize_attention_weights(self, student_model: PreTrainedModel, teacher_model: PreTrainedModel):
        """Initialize attention weights for reduced number of heads"""
        teacher_dict = teacher_model.state_dict()
        student_dict = student_model.state_dict()

        for name in student_dict:
            if 'attention' in name and ('weight' in name or 'bias' in name):
                if name in teacher_dict:
                    teacher_weight = teacher_dict[name]
                    student_weight = student_dict[name]

                    # Reshape attention weights for different number of heads
                    if len(teacher_weight.shape) >= 2:
                        # Simple approach: average over extra heads or duplicate existing ones
                        if teacher_weight.shape[0] > student_weight.shape[0]:
                            # Average extra dimensions
                            teacher_weight = teacher_weight.mean(dim=0, keepdim=True)
                            if teacher_weight.shape == student_weight.shape:
                                student_dict[name].copy_(teacher_weight)
                        elif teacher_weight.shape[0] < student_weight.shape[0]:
                            # Duplicate existing dimensions
                            repeats = student_weight.shape[0] // teacher_weight.shape[0]
                            teacher_weight = teacher_weight.repeat(repeats, *([1] * (len(teacher_weight.shape) - 1)))
                            if teacher_weight.shape == student_weight.shape:
                                student_dict[name].copy_(teacher_weight)

        student_model.load_state_dict(student_dict)

    def _create_layer_mapping(self, num_teacher_layers: int, num_student_layers: int) -> Dict[int, int]:
        """Create mapping between teacher and student layers"""
        if num_student_layers >= num_teacher_layers:
            # Student has more layers, use identity mapping
            return {i: min(i, num_teacher_layers - 1) for i in range(num_student_layers)}
        else:
            # Student has fewer layers, use uniform sampling
            mapping = {}
            for i in range(num_student_layers):
                teacher_idx = int(i * (num_teacher_layers - 1) / (num_student_layers - 1)) if num_student_layers > 1 else 0
                mapping[i] = teacher_idx
            return mapping


class MultiTeacherDistillation:
    """Support for distillation from multiple teacher models"""

    def __init__(self, teacher_models: List[PreTrainedModel],
                 teacher_weights: Optional[List[float]] = None):
        self.teacher_models = teacher_models
        self.teacher_weights = teacher_weights or [1.0 / len(teacher_models)] * len(teacher_models)
        self.logger = logging.getLogger(self.__class__.__name__)

        # Validate weights
        if len(self.teacher_weights) != len(self.teacher_models):
            raise ValueError("Number of weights must match number of teacher models")

        # Normalize weights
        total_weight = sum(self.teacher_weights)
        self.teacher_weights = [w / total_weight for w in self.teacher_weights]

    def get_ensemble_logits(self, input_ids: torch.Tensor) -> torch.Tensor:
        """Get ensemble logits from all teacher models"""
        all_logits = []

        for teacher_model in self.teacher_models:
            with torch.no_grad():
                outputs = teacher_model(input_ids)
                all_logits.append(outputs.logits)

        # Weighted average of logits
        ensemble_logits = torch.zeros_like(all_logits[0])
        for logits, weight in zip(all_logits, self.teacher_weights):
            ensemble_logits += weight * logits

        return ensemble_logits

    def get_ensemble_attention(self, input_ids: torch.Tensor) -> List[torch.Tensor]:
        """Get ensemble attention patterns from all teacher models"""
        all_attentions = []

        for teacher_model in self.teacher_models:
            with torch.no_grad():
                outputs = teacher_model(input_ids, output_attentions=True)
                all_attentions.append(outputs.attentions)

        # Average attention patterns
        num_layers = len(all_attentions[0])
        ensemble_attentions = []

        for layer_idx in range(num_layers):
            layer_attentions = []
            for teacher_idx in range(len(self.teacher_models)):
                layer_attentions.append(all_attentions[teacher_idx][layer_idx])

            # Weighted average
            ensemble_layer = torch.zeros_like(layer_attentions[0])
            for attention, weight in zip(layer_attentions, self.teacher_weights):
                ensemble_layer += weight * attention

            ensemble_attentions.append(ensemble_layer)

        return ensemble_attentions


class TeacherStudentManager:
    """Main class for managing teacher-student model combinations"""

    def __init__(self):
        self.architecture_analyzer = ModelArchitectureAnalyzer()
        self.student_generator = StudentArchitectureGenerator()
        self.logger = logging.getLogger(self.__class__.__name__)

        self.teacher_model = None
        self.student_model = None
        self.teacher_analysis = None
        self.student_analysis = None

    def load_teacher_model(self, model_path: str, model_type: ModelType = ModelType.GPT2) -> PreTrainedModel:
        """Load teacher model"""
        self.logger.info(f"Loading teacher model from {model_path}")

        try:
            self.teacher_model = AutoModelForCausalLM.from_pretrained(model_path)
            self.teacher_analysis = self.architecture_analyzer.analyze_model(self.teacher_model)

            self.logger.info(f"Teacher model loaded successfully")
            self.logger.info(f"Parameters: {self.teacher_analysis['total_parameters']:,}")
            self.logger.info(f"Layers: {self.teacher_analysis['num_layers']}")
            self.logger.info(f"Hidden size: {self.teacher_analysis['hidden_size']}")

            return self.teacher_model
        except Exception as e:
            self.logger.error(f"Failed to load teacher model: {e}")
            raise

    def create_student_model(self, config: TeacherStudentConfig) -> PreTrainedModel:
        """Create student model based on teacher and configuration"""
        if self.teacher_model is None:
            raise ValueError("Teacher model must be loaded first")

        self.logger.info("Creating student model...")

        # Create student architecture
        self.student_model = self.student_generator.create_student_model(
            self.teacher_model, config.architecture_strategy, config
        )

        # Analyze student architecture
        self.student_analysis = self.architecture_analyzer.analyze_model(self.student_model)

        # Compare architectures
        comparison = self.architecture_analyzer.compare_architectures(
            self.teacher_analysis, self.student_analysis
        )

        self.logger.info("Student model created successfully")
        self.logger.info(f"Parameters: {self.student_analysis['total_parameters']:,}")
        self.logger.info(f"Compression ratio: {comparison['compression_efficiency']:.2%}")

        return self.student_model

    def save_student_model(self, save_path: str, tokenizer: Optional[PreTrainedTokenizer] = None):
        """Save student model and analysis"""
        if self.student_model is None:
            raise ValueError("Student model not created")

        save_path = Path(save_path)
        save_path.mkdir(parents=True, exist_ok=True)

        # Save model
        self.student_model.save_pretrained(save_path)

        # Save tokenizer if provided
        if tokenizer:
            tokenizer.save_pretrained(save_path)

        # Save analysis
        analysis_data = {
            "teacher_analysis": self.teacher_analysis,
            "student_analysis": self.student_analysis,
            "comparison": self.architecture_analyzer.compare_architectures(
                self.teacher_analysis, self.student_analysis
            )
        }

        with open(save_path / "model_analysis.json", "w") as f:
            json.dump(analysis_data, f, indent=2, default=str)

        self.logger.info(f"Student model saved to {save_path}")

    def get_model_summary(self) -> Dict[str, Any]:
        """Get summary of teacher and student models"""
        if self.teacher_model is None or self.student_model is None:
            raise ValueError("Both teacher and student models must be loaded")

        return {
            "teacher": self.teacher_analysis,
            "student": self.student_analysis,
            "comparison": self.architecture_analyzer.compare_architectures(
                self.teacher_analysis, self.student_analysis
            )
        }

    def validate_compatibility(self) -> bool:
        """Validate teacher-student model compatibility"""
        if self.teacher_model is None or self.student_model is None:
            return False

        # Check basic compatibility
        teacher_vocab = self.teacher_analysis.get("vocab_size", 0)
        student_vocab = self.student_analysis.get("vocab_size", 0)

        if teacher_vocab != student_vocab:
            self.logger.warning(f"Vocabulary size mismatch: teacher={teacher_vocab}, student={student_vocab}")
            return False

        # Check model type compatibility
        teacher_type = self.teacher_analysis.get("model_type", "")
        student_type = self.student_analysis.get("model_type", "")

        if teacher_type != student_type:
            self.logger.warning(f"Model type mismatch: teacher={teacher_type}, student={student_type}")
            return False

        return True


def main():
    """Example usage of teacher-student model management"""
    # Create manager
    manager = TeacherStudentManager()

    # Example configuration
    config = TeacherStudentConfig(
        teacher_model_path="gpt2",  # Using small GPT-2 for example
        model_type=ModelType.GPT2,
        architecture_strategy=ArchitectureStrategy.SCALING,
        scaling_factor=0.5
    )

    try:
        # Load teacher model
        teacher_model = manager.load_teacher_model(config.teacher_model_path, config.model_type)

        # Create student model
        student_model = manager.create_student_model(config)

        # Get summary
        summary = manager.get_model_summary()
        print("Teacher-Student Model Summary:")
        print(f"Teacher parameters: {summary['teacher']['total_parameters']:,}")
        print(f"Student parameters: {summary['student']['total_parameters']:,}")
        print(f"Compression ratio: {summary['comparison']['compression_efficiency']:.2%}")

        # Validate compatibility
        if manager.validate_compatibility():
            print("Models are compatible for distillation")
        else:
            print("Models have compatibility issues")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()