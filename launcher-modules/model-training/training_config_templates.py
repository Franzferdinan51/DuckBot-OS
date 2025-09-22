#!/usr/bin/env python3
"""
Training Configuration Templates for Common Scenarios
Pre-configured templates for various model training scenarios with optimized settings
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import logging

# Import configuration classes from other modules
try:
    from advanced_lora_trainer import (
        AdvancedLoRAConfig, LoRAConfig, LoRAMode, MemoryStrategy,
        OptimizerType, SchedulerType, QuantizationConfig
    )
    from full_finetune_trainer import (
        FullFineTuneConfig, MemoryConfig, PrecisionMode, OffloadingStrategy,
        DistributedConfig
    )
    from parameter_efficient_training import (
        PEFTConfig, PEFTMethod, OptimizerConfig, SchedulerConfig,
        create_peft_presets, create_optimizer_presets, create_scheduler_presets
    )
    from gradient_checkpointing_system import (
        GradientCheckpointingConfig, CheckpointingStrategy, MemoryOptimizationMode,
        GradientCheckpointingFactory
    )
    HAS_LOCAL_MODULES = True
except ImportError:
    HAS_LOCAL_MODULES = False
    # Fallback dummy classes
    class AdvancedLoRAConfig:
        pass
    class FullFineTuneConfig:
        pass

class ModelSize(Enum):
    """Model size categories"""
    SMALL = "small"          # < 1B parameters
    MEDIUM = "medium"        # 1B - 7B parameters
    LARGE = "large"          # 7B - 30B parameters
    XLARGE = "xlarge"        # 30B - 70B parameters
    XXLARGE = "xxlarge"      # > 70B parameters

class HardwareProfile(Enum):
    """Hardware capability profiles"""
    LOW_END = "low_end"           # Consumer GPU (e.g., RTX 3060, 8GB VRAM)
    MID_RANGE = "mid_range"       # Mid-range GPU (e.g., RTX 3090, 24GB VRAM)
    HIGH_END = "high_end"         # High-end GPU (e.g., A100, 40GB+ VRAM)
    MULTI_GPU = "multi_gpu"       # Multiple GPU setup
    CPU_ONLY = "cpu_only"         # CPU-only training

class TrainingObjective(Enum):
    """Training objectives"""
    INSTRUCTION_TUNING = "instruction_tuning"
    DOMAIN_ADAPTATION = "domain_adaptation"
    CONTINUED_PRETRAINING = "continued_pretraining"
    CHAT_FINETUNING = "chat_finetuning"
    CODE_FINETUNING = "code_finetuning"
    MULTILINGUAL_TUNING = "multilingual_tuning"
    TASK_SPECIFIC = "task_specific"

@dataclass
class TrainingScenario:
    """Training scenario definition"""
    name: str
    description: str
    model_size: ModelSize
    hardware_profile: HardwareProfile
    training_objective: TrainingObjective
    peft_method: PEFTMethod
    expected_memory_usage_gb: float
    estimated_training_time_hours: float
    recommended_epochs: int
    quality_expectation: str

class TrainingTemplateManager:
    """Manages training configuration templates"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.templates: Dict[str, Dict[str, Any]] = {}
        self.scenarios: Dict[str, TrainingScenario] = {}

        if HAS_LOCAL_MODULES:
            self._initialize_templates()
            self._initialize_scenarios()

    def _initialize_templates(self):
        """Initialize all training templates"""
        self.templates = {
            # LoRA Templates
            "lora_ultra_efficient": self._create_lora_ultra_efficient_template(),
            "lora_balanced": self._create_lora_balanced_template(),
            "lora_high_performance": self._create_lora_high_performance_template(),
            "lora_dora": self._create_lora_dora_template(),
            "lora_qdora": self._create_lora_qdora_template(),

            # Full Fine-tuning Templates
            "full_finetune_memory_efficient": self._create_full_finetune_memory_efficient_template(),
            "full_finetune_balanced": self._create_full_finetune_balanced_template(),
            "full_finetune_high_performance": self._create_full_finetune_high_performance_template(),
            "full_finetune_distributed": self._create_full_finetune_distributed_template(),

            # Mixed Method Templates
            "hybrid_qlora_adapter": self._create_hybrid_qlora_adapter_template(),
            "hybrid_gradient_checkpointing": self._create_hybrid_gradient_checkpointing_template(),
            "hybrid_memory_optimized": self._create_hybrid_memory_optimized_template(),

            # Specialized Templates
            "instruction_tuning_llama7b": self._create_instruction_tuning_llama7b_template(),
            "code_tuning_codellama": self._create_code_tuning_codellama_template(),
            "chat_tuning_mistral": self._create_chat_tuning_mistral_template(),
            "domain_adaptation_llama70b": self._create_domain_adaptation_llama70b_template(),
        }

    def _initialize_scenarios(self):
        """Initialize training scenarios"""
        self.scenarios = {
            "consumer_llama7b_instruction": TrainingScenario(
                name="Consumer GPU - Llama 7B Instruction Tuning",
                description="Instruction tuning on consumer hardware with limited VRAM",
                model_size=ModelSize.MEDIUM,
                hardware_profile=HardwareProfile.LOW_END,
                training_objective=TrainingObjective.INSTRUCTION_TUNING,
                peft_method=PEFTMethod.LORA,
                expected_memory_usage_gb=8.0,
                estimated_training_time_hours=12,
                recommended_epochs=3,
                quality_expectation="Good quality for general instruction following"
            ),

            "mid_range_llama70b_domain": TrainingScenario(
                name="Mid-range GPU - Llama 70B Domain Adaptation",
                description="Domain adaptation on mid-range hardware for large models",
                model_size=ModelSize.XLARGE,
                hardware_profile=HardwareProfile.MID_RANGE,
                training_objective=TrainingObjective.DOMAIN_ADAPTATION,
                peft_method=PEFTMethod.LORA,
                expected_memory_usage_gb=24.0,
                estimated_training_time_hours=48,
                recommended_epochs=2,
                quality_expectation="Excellent domain-specific adaptation"
            ),

            "high_end_mistral_chat": TrainingScenario(
                name="High-end GPU - Mistral Chat Fine-tuning",
                description="High-quality chat fine-tuning on professional hardware",
                model_size=ModelSize.MEDIUM,
                hardware_profile=HardwareProfile.HIGH_END,
                training_objective=TrainingObjective.CHAT_FINETUNING,
                peft_method=PEFTMethod.LORA,
                expected_memory_usage_gb=16.0,
                estimated_training_time_hours=6,
                recommended_epochs=3,
                quality_expectation="Professional-grade chat model"
            ),

            "multi_gpu_falcon40b": TrainingScenario(
                name="Multi-GPU - Falcon 40B Continued Pretraining",
                description="Large-scale continued pretraining on multi-GPU setup",
                model_size=ModelSize.XLARGE,
                hardware_profile=HardwareProfile.MULTI_GPU,
                training_objective=TrainingObjective.CONTINUED_PRETRAINING,
                peft_method=PEFTMethod.LORA,
                expected_memory_usage_gb=80.0,
                estimated_training_time_hours=72,
                recommended_epochs=1,
                quality_expectation="State-of-the-art continued pretraining"
            ),

            "cpu_only_phi2_task": TrainingScenario(
                name="CPU-only - Phi-2 Task Specific Training",
                description="Task-specific training on CPU hardware",
                model_size=ModelSize.SMALL,
                hardware_profile=HardwareProfile.CPU_ONLY,
                training_objective=TrainingObjective.TASK_SPECIFIC,
                peft_method=PEFTMethod.LORA,
                expected_memory_usage_gb=16.0,
                estimated_training_time_hours=24,
                recommended_epochs=5,
                quality_expectation="Good task performance with longer training"
            ),
        }

    def _create_lora_ultra_efficient_template(self) -> Dict[str, Any]:
        """Create ultra-efficient LoRA template"""
        return {
            "name": "Ultra-Efficient LoRA",
            "description": "Maximum memory efficiency for large models on limited hardware",
            "config": AdvancedLoRAConfig(
                model_name_or_path="meta-llama/Llama-2-70B-hf",
                dataset_path="datasets/instructions.json",
                output_dir="outputs/lora_ultra_efficient",
                lora_config=LoRAConfig(
                    r=4,
                    lora_alpha=8,
                    lora_dropout=0.1,
                    target_modules=["q_proj", "v_proj"]
                ),
                lora_mode=LoRAMode.QLoRA,
                quantization_config=QuantizationConfig(
                    load_in_4bit=True,
                    bnb_4bit_quant_type="nf4",
                    bnb_4bit_use_double_quant=True
                ),
                learning_rate=1e-4,
                num_train_epochs=2,
                per_device_train_batch_size=1,
                gradient_accumulation_steps=64,
                memory_strategy=MemoryStrategy.ULTRA_EFFICIENT,
                gradient_checkpointing=True,
                fp16=True,
                bf16=False
            ).__dict__,
            "requirements": {
                "min_vram_gb": 8,
                "min_system_ram_gb": 32,
                "recommended_gpu": "RTX 3060 or better",
                "training_time_estimate": "24-48 hours for 70B model"
            }
        }

    def _create_lora_balanced_template(self) -> Dict[str, Any]:
        """Create balanced LoRA template"""
        return {
            "name": "Balanced LoRA",
            "description": "Good balance between performance and memory usage",
            "config": AdvancedLoRAConfig(
                model_name_or_path="mistralai/Mistral-7B-v0.1",
                dataset_path="datasets/chat_data.json",
                output_dir="outputs/lora_balanced",
                lora_config=LoRAConfig(
                    r=16,
                    lora_alpha=32,
                    lora_dropout=0.05,
                    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"]
                ),
                lora_mode=LoRAMode.QLoRA,
                quantization_config=QuantizationConfig(
                    load_in_4bit=True,
                    bnb_4bit_quant_type="nf4"
                ),
                learning_rate=2e-4,
                num_train_epochs=3,
                per_device_train_batch_size=4,
                gradient_accumulation_steps=8,
                memory_strategy=MemoryStrategy.BALANCED,
                gradient_checkpointing=True,
                bf16=True
            ).__dict__,
            "requirements": {
                "min_vram_gb": 16,
                "min_system_ram_gb": 16,
                "recommended_gpu": "RTX 3090 or better",
                "training_time_estimate": "6-12 hours for 7B model"
            }
        }

    def _create_lora_high_performance_template(self) -> Dict[str, Any]:
        """Create high-performance LoRA template"""
        return {
            "name": "High-Performance LoRA",
            "description": "Maximum performance with less memory optimization",
            "config": AdvancedLoRAConfig(
                model_name_or_path="microsoft/DialoGPT-medium",
                dataset_path="datasets/conversations.json",
                output_dir="outputs/lora_high_performance",
                lora_config=LoRAConfig(
                    r=64,
                    lora_alpha=128,
                    lora_dropout=0.0,
                    target_modules=["c_attn", "c_proj", "mlp.c_fc", "mlp.c_proj"]
                ),
                lora_mode=LoRAMode.STANDARD,
                learning_rate=3e-4,
                num_train_epochs=5,
                per_device_train_batch_size=16,
                gradient_accumulation_steps=1,
                memory_strategy=MemoryStrategy.AGGRESSIVE,
                gradient_checkpointing=False,
                fp32=True
            ).__dict__,
            "requirements": {
                "min_vram_gb": 32,
                "min_system_ram_gb": 32,
                "recommended_gpu": "A100 or RTX 4090",
                "training_time_estimate": "2-4 hours for small model"
            }
        }

    def _create_lora_dora_template(self) -> Dict[str, Any]:
        """Create DoRA (Weight-Decomposed LoRA) template"""
        return {
            "name": "DoRA Enhanced LoRA",
            "description": "Weight-decomposed LoRA for better performance",
            "config": AdvancedLoRAConfig(
                model_name_or_path="mistralai/Mistral-7B-v0.1",
                dataset_path="datasets/specialized_data.json",
                output_dir="outputs/lora_dora",
                lora_config=LoRAConfig(
                    r=16,
                    lora_alpha=32,
                    lora_dropout=0.05,
                    use_dora=True,
                    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
                ),
                lora_mode=LoRAMode.DORA,
                learning_rate=1e-4,
                num_train_epochs=3,
                per_device_train_batch_size=4,
                gradient_accumulation_steps=8,
                memory_strategy=MemoryStrategy.BALANCED,
                gradient_checkpointing=True,
                bf16=True
            ).__dict__,
            "requirements": {
                "min_vram_gb": 16,
                "min_system_ram_gb": 16,
                "recommended_gpu": "RTX 3090 or better",
                "training_time_estimate": "8-16 hours for 7B model",
                "notes": "DoRA provides better convergence but requires more compute"
            }
        }

    def _create_lora_qdora_template(self) -> Dict[str, Any]:
        """Create QDoRA (Quantized DoRA) template"""
        return {
            "name": "QDoRA Ultra-Efficient",
            "description": "Quantized DoRA for maximum efficiency with good performance",
            "config": AdvancedLoRAConfig(
                model_name_or_path="meta-llama/Llama-2-70B-hf",
                dataset_path="datasets/ultra_efficient_data.json",
                output_dir="outputs/lora_qdora",
                lora_config=LoRAConfig(
                    r=8,
                    lora_alpha=16,
                    lora_dropout=0.1,
                    use_dora=True,
                    target_modules=["q_proj", "v_proj"]
                ),
                lora_mode=LoRAMode.QLoRA,
                quantization_config=QuantizationConfig(
                    load_in_4bit=True,
                    bnb_4bit_quant_type="nf4",
                    bnb_4bit_use_double_quant=True,
                    bnb_4bit_compute_dtype=torch.float16
                ),
                learning_rate=1e-4,
                num_train_epochs=2,
                per_device_train_batch_size=1,
                gradient_accumulation_steps=32,
                memory_strategy=MemoryStrategy.ULTRA_EFFICIENT,
                gradient_checkpointing=True,
                fp16=True
            ).__dict__,
            "requirements": {
                "min_vram_gb": 8,
                "min_system_ram_gb": 32,
                "recommended_gpu": "RTX 3060 or better",
                "training_time_estimate": "16-32 hours for 70B model",
                "notes": "Best combination of efficiency and performance for large models"
            }
        }

    def _create_full_finetune_memory_efficient_template(self) -> Dict[str, Any]:
        """Create memory-efficient full fine-tuning template"""
        return {
            "name": "Memory-Efficient Full Fine-tuning",
            "description": "Full fine-tuning with maximum memory optimization",
            "config": FullFineTuneConfig(
                model_name_or_path="meta-llama/Llama-2-7B-hf",
                dataset_path="datasets/full_finetune_data.json",
                output_dir="outputs/full_finetune_memory_efficient",
                memory_config=MemoryConfig(
                    mode=MemoryMode.HYBRID,
                    precision=PrecisionMode.FP16,
                    offloading=OffloadingStrategy.CPU,
                    max_memory_per_gpu=16.0,
                    enable_gradient_accumulation=True,
                    enable_activation_checkpointing=True,
                    enable_cpu_offload=True,
                    enable_mixed_precision=True
                ),
                learning_rate=2e-5,
                num_train_epochs=3,
                per_device_train_batch_size=1,
                gradient_accumulation_steps=16,
                max_seq_length=2048,
                fp16=True
            ).__dict__,
            "requirements": {
                "min_vram_gb": 16,
                "min_system_ram_gb": 64,
                "recommended_gpu": "RTX 3090 or better",
                "training_time_estimate": "24-48 hours for 7B model",
                "notes": "Uses CPU offloading and gradient checkpointing"
            }
        }

    def _create_full_finetune_balanced_template(self) -> Dict[str, Any]:
        """Create balanced full fine-tuning template"""
        return {
            "name": "Balanced Full Fine-tuning",
            "description": "Full fine-tuning with good balance of speed and memory",
            "config": FullFineTuneConfig(
                model_name_or_path="microsoft/DialoGPT-medium",
                dataset_path="datasets/balanced_finetune_data.json",
                output_dir="outputs/full_finetune_balanced",
                memory_config=MemoryConfig(
                    mode=MemoryMode.GRADIENT_CHECKPOINTING,
                    precision=PrecisionMode.BF16,
                    enable_gradient_accumulation=True,
                    enable_activation_checkpointing=True,
                    enable_mixed_precision=True
                ),
                learning_rate=5e-5,
                num_train_epochs=3,
                per_device_train_batch_size=4,
                gradient_accumulation_steps=4,
                max_seq_length=1024,
                bf16=True
            ).__dict__,
            "requirements": {
                "min_vram_gb": 24,
                "min_system_ram_gb": 32,
                "recommended_gpu": "RTX 4090 or A100",
                "training_time_estimate": "4-8 hours for medium model"
            }
        }

    def _create_full_finetune_high_performance_template(self) -> Dict[str, Any]:
        """Create high-performance full fine-tuning template"""
        return {
            "name": "High-Performance Full Fine-tuning",
            "description": "Maximum performance full fine-tuning with minimal optimization",
            "config": FullFineTuneConfig(
                model_name_or_path="gpt2-medium",
                dataset_path="datasets/high_performance_data.json",
                output_dir="outputs/full_finetune_high_performance",
                memory_config=MemoryConfig(
                    mode=MemoryMode.STANDARD,
                    precision=PrecisionMode.FP32,
                    enable_gradient_accumulation=False,
                    enable_activation_checkpointing=False,
                    enable_mixed_precision=False
                ),
                learning_rate=1e-4,
                num_train_epochs=5,
                per_device_train_batch_size=32,
                gradient_accumulation_steps=1,
                max_seq_length=512,
                fp32=True
            ).__dict__,
            "requirements": {
                "min_vram_gb": 32,
                "min_system_ram_gb": 32,
                "recommended_gpu": "A100 or RTX 4090",
                "training_time_estimate": "1-2 hours for small model"
            }
        }

    def _create_full_finetune_distributed_template(self) -> Dict[str, Any]:
        """Create distributed full fine-tuning template"""
        return {
            "name": "Distributed Full Fine-tuning",
            "description": "Multi-GPU distributed training for large models",
            "config": FullFineTuneConfig(
                model_name_or_path="meta-llama/Llama-2-70B-hf",
                dataset_path="datasets/distributed_data.json",
                output_dir="outputs/full_finetune_distributed",
                memory_config=MemoryConfig(
                    mode=MemoryMode.STANDARD,
                    precision=PrecisionMode.BF16,
                    enable_mixed_precision=True
                ),
                distributed_config=DistributedConfig(
                    backend="nccl",
                    num_gpus_per_node=4,
                    num_nodes=2
                ),
                learning_rate=1e-5,
                num_train_epochs=2,
                per_device_train_batch_size=2,
                gradient_accumulation_steps=8,
                max_seq_length=4096,
                bf16=True
            ).__dict__,
            "requirements": {
                "min_vram_gb_per_gpu": 40,
                "total_gpu_count": 8,
                "min_system_ram_gb": 128,
                "recommended_setup": "2x4 A100/H100 nodes",
                "training_time_estimate": "12-24 hours for 70B model on 8 GPUs"
            }
        }

    def _create_hybrid_qlora_adapter_template(self) -> Dict[str, Any]:
        """Create hybrid QLoRA + Adapter template"""
        return {
            "name": "Hybrid QLoRA + Adapter",
            "description": "Combined QLoRA and adapter methods for maximum efficiency",
            "config": {
                "primary_method": "qlora",
                "secondary_method": "adapter",
                "lora_config": LoRAConfig(
                    r=8,
                    lora_alpha=16,
                    lora_dropout=0.1,
                    target_modules=["q_proj", "v_proj"]
                ),
                "adapter_config": {
                    "adapter_dim": 64,
                    "adapter_dropout": 0.1,
                    "adapter_act_fn": "gelu"
                },
                "quantization_config": QuantizationConfig(
                    load_in_4bit=True,
                    bnb_4bit_quant_type="nf4"
                ),
                "learning_rate": 2e-4,
                "num_train_epochs": 3,
                "per_device_train_batch_size": 2,
                "gradient_accumulation_steps": 16,
                "memory_strategy": MemoryStrategy.BALANCED
            },
            "requirements": {
                "min_vram_gb": 12,
                "min_system_ram_gb": 24,
                "recommended_gpu": "RTX 3080 or better",
                "training_time_estimate": "8-16 hours for 7B model"
            }
        }

    def _create_hybrid_gradient_checkpointing_template(self) -> Dict[str, Any]:
        """Create hybrid gradient checkpointing template"""
        return {
            "name": "Hybrid Gradient Checkpointing",
            "description": "Advanced gradient checkpointing with memory optimization",
            "config": {
                "gradient_checkpointing_config": GradientCheckpointingConfig(
                    strategy=CheckpointingStrategy.MEMORY_AWARE,
                    checkpoint_ratio=0.4,
                    memory_threshold=0.85,
                    enable_recompute=True,
                    layer_selection_criteria="memory"
                ),
                "memory_optimization_mode": MemoryOptimizationMode.AGGRESSIVE,
                "model_config": FullFineTuneConfig(
                    model_name_or_path="meta-llama/Llama-2-13B-hf",
                    dataset_path="datasets/checkpointing_data.json",
                    output_dir="outputs/hybrid_checkpointing",
                    learning_rate=2e-5,
                    num_train_epochs=3,
                    per_device_train_batch_size=1,
                    gradient_accumulation_steps=32
                )
            },
            "requirements": {
                "min_vram_gb": 10,
                "min_system_ram_gb": 32,
                "recommended_gpu": "RTX 3070 or better",
                "training_time_estimate": "12-24 hours for 13B model"
            }
        }

    def _create_hybrid_memory_optimized_template(self) -> Dict[str, Any]:
        """Create hybrid memory optimization template"""
        return {
            "name": "Hybrid Memory Optimization",
            "description": "Combines all memory optimization techniques",
            "config": {
                "techniques": [
                    "gradient_checkpointing",
                    "mixed_precision",
                    "gradient_accumulation",
                    "cpu_offloading",
                    "activation_checkpointing"
                ],
                "lora_config": LoRAConfig(
                    r=4,
                    lora_alpha=8,
                    lora_dropout=0.1,
                    target_modules=["q_proj", "v_proj"]
                ),
                "quantization_config": QuantizationConfig(
                    load_in_4bit=True,
                    bnb_4bit_quant_type="nf4",
                    bnb_4bit_use_double_quant=True
                ),
                "gradient_checkpointing_config": GradientCheckpointingConfig(
                    strategy=CheckpointingStrategy.ADAPTIVE,
                    checkpoint_ratio=0.3
                ),
                "learning_rate": 1e-4,
                "num_train_epochs=2",
                "per_device_train_batch_size": 1,
                "gradient_accumulation_steps": 64,
                "memory_strategy": MemoryStrategy.ULTRA_EFFICIENT
            },
            "requirements": {
                "min_vram_gb": 6,
                "min_system_ram_gb": 32,
                "recommended_gpu": "RTX 3060 or better",
                "training_time_estimate": "20-40 hours for 70B model"
            }
        }

    def _create_instruction_tuning_llama7b_template(self) -> Dict[str, Any]:
        """Create instruction tuning template for Llama 7B"""
        return {
            "name": "Instruction Tuning - Llama 7B",
            "description": "Optimized for instruction following tasks on Llama 7B",
            "config": AdvancedLoRAConfig(
                model_name_or_path="meta-llama/Llama-2-7B-hf",
                dataset_path="datasets/instructions.json",
                output_dir="outputs/llama7b_instruction",
                lora_config=LoRAConfig(
                    r=16,
                    lora_alpha=32,
                    lora_dropout=0.05,
                    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
                ),
                lora_mode=LoRAMode.QLoRA,
                quantization_config=QuantizationConfig(
                    load_in_4bit=True,
                    bnb_4bit_quant_type="nf4"
                ),
                learning_rate=2e-4,
                num_train_epochs=3,
                per_device_train_batch_size=4,
                gradient_accumulation_steps=4,
                max_seq_length=2048,
                dataset_text_field="instruction",
                memory_strategy=MemoryStrategy.BALANCED,
                bf16=True
            ).__dict__,
            "requirements": {
                "min_vram_gb": 12,
                "min_system_ram_gb": 16,
                "recommended_gpu": "RTX 3060 or better",
                "training_time_estimate": "6-12 hours"
            }
        }

    def _create_code_tuning_codellama_template(self) -> Dict[str, Any]:
        """Create code tuning template for CodeLlama"""
        return {
            "name": "Code Tuning - CodeLlama",
            "description": "Specialized for code generation and understanding tasks",
            "config": AdvancedLoRAConfig(
                model_name_or_path="codellama/CodeLlama-7B-hf",
                dataset_path="datasets/code_data.json",
                output_dir="outputs/codellama_code",
                lora_config=LoRAConfig(
                    r=32,
                    lora_alpha=64,
                    lora_dropout=0.0,
                    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
                ),
                lora_mode=LoRAMode.STANDARD,
                learning_rate=3e-4,
                num_train_epochs=5,
                per_device_train_batch_size=8,
                gradient_accumulation_steps=2,
                max_seq_length=4096,
                dataset_text_field="code",
                memory_strategy=MemoryStrategy.AGGRESSIVE,
                fp16=False,
                bf16=True
            ).__dict__,
            "requirements": {
                "min_vram_gb": 24,
                "min_system_ram_gb": 32,
                "recommended_gpu": "RTX 4090 or A100",
                "training_time_estimate": "8-16 hours"
            }
        }

    def _create_chat_tuning_mistral_template(self) -> Dict[str, Any]:
        """Create chat tuning template for Mistral"""
        return {
            "name": "Chat Tuning - Mistral",
            "description": "Optimized for conversational AI and chat applications",
            "config": AdvancedLoRAConfig(
                model_name_or_path="mistralai/Mistral-7B-Instruct-v0.1",
                dataset_path="datasets/chat_data.json",
                output_dir="outputs/mistral_chat",
                lora_config=LoRAConfig(
                    r=16,
                    lora_alpha=32,
                    lora_dropout=0.05,
                    use_dora=True,
                    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
                ),
                lora_mode=LoRAMode.DORA,
                learning_rate=1e-4,
                num_train_epochs=3,
                per_device_train_batch_size=4,
                gradient_accumulation_steps=8,
                max_seq_length=4096,
                dataset_text_field="messages",
                memory_strategy=MemoryStrategy.BALANCED,
                bf16=True
            ).__dict__,
            "requirements": {
                "min_vram_gb": 16,
                "min_system_ram_gb": 16,
                "recommended_gpu": "RTX 3090 or better",
                "training_time_estimate": "8-16 hours"
            }
        }

    def _create_domain_adaptation_llama70b_template(self) -> Dict[str, Any]:
        """Create domain adaptation template for Llama 70B"""
        return {
            "name": "Domain Adaptation - Llama 70B",
            "description": "Large-scale domain adaptation for specialized applications",
            "config": AdvancedLoRAConfig(
                model_name_or_path="meta-llama/Llama-2-70B-hf",
                dataset_path="datasets/domain_data.json",
                output_dir="outputs/llama70b_domain",
                lora_config=LoRAConfig(
                    r=8,
                    lora_alpha=16,
                    lora_dropout=0.1,
                    target_modules=["q_proj", "v_proj"]
                ),
                lora_mode=LoRAMode.QLoRA,
                quantization_config=QuantizationConfig(
                    load_in_4bit=True,
                    bnb_4bit_quant_type="nf4",
                    bnb_4bit_use_double_quant=True,
                    bnb_4bit_compute_dtype=torch.float16
                ),
                learning_rate=1e-4,
                num_train_epochs=2,
                per_device_train_batch_size=1,
                gradient_accumulation_steps=32,
                max_seq_length=2048,
                memory_strategy=MemoryStrategy.ULTRA_EFFICIENT,
                gradient_checkpointing=True,
                fp16=True
            ).__dict__,
            "requirements": {
                "min_vram_gb": 8,
                "min_system_ram_gb": 64,
                "recommended_gpu": "RTX 3060 or better",
                "training_time_estimate": "24-48 hours"
            }
        }

    def get_template(self, template_name: str) -> Optional[Dict[str, Any]]:
        """Get a specific template by name"""
        return self.templates.get(template_name)

    def list_templates(self) -> List[str]:
        """List all available templates"""
        return list(self.templates.keys())

    def get_scenario(self, scenario_name: str) -> Optional[TrainingScenario]:
        """Get a specific scenario by name"""
        return self.scenarios.get(scenario_name)

    def list_scenarios(self) -> List[str]:
        """List all available scenarios"""
        return list(self.scenarios.keys())

    def recommend_template(
        self,
        model_size: ModelSize,
        hardware_profile: HardwareProfile,
        training_objective: TrainingObjective,
        available_vram_gb: Optional[float] = None
    ) -> str:
        """Recommend a template based on requirements"""
        recommendations = []

        for scenario_name, scenario in self.scenarios.items():
            if (scenario.model_size == model_size and
                scenario.hardware_profile == hardware_profile and
                scenario.training_objective == training_objective):

                # Check memory requirements
                if available_vram_gb is not None:
                    if scenario.expected_memory_usage_gb <= available_vram_gb:
                        recommendations.append(scenario_name)
                else:
                    recommendations.append(scenario_name)

        if recommendations:
            return recommendations[0]

        # Fallback recommendations
        if hardware_profile == HardwareProfile.LOW_END:
            return "lora_ultra_efficient"
        elif hardware_profile == HardwareProfile.MID_RANGE:
            return "lora_balanced"
        elif hardware_profile == HardwareProfile.HIGH_END:
            return "lora_high_performance"
        else:
            return "lora_balanced"

    def save_template(self, template_name: str, output_path: str):
        """Save a template to file"""
        template = self.get_template(template_name)
        if template is None:
            raise ValueError(f"Template '{template_name}' not found")

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(template, f, indent=2, default=str)

        self.logger.info(f"Template '{template_name}' saved to {output_path}")

    def load_template(self, template_path: str) -> Dict[str, Any]:
        """Load a template from file"""
        with open(template_path, 'r') as f:
            template = json.load(f)

        self.logger.info(f"Template loaded from {template_path}")
        return template

    def create_custom_template(
        self,
        name: str,
        description: str,
        base_template: str,
        customizations: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a custom template based on an existing one"""
        base = self.get_template(base_template)
        if base is None:
            raise ValueError(f"Base template '{base_template}' not found")

        # Create custom template
        custom_template = base.copy()
        custom_template["name"] = name
        custom_template["description"] = description

        # Apply customizations
        if "config" in customizations:
            custom_template["config"].update(customizations["config"])

        if "requirements" in customizations:
            custom_template["requirements"].update(customizations["requirements"])

        return custom_template

    def get_hardware_recommendations(self, hardware_profile: HardwareProfile) -> Dict[str, Any]:
        """Get hardware recommendations for a profile"""
        recommendations = {
            HardwareProfile.LOW_END: {
                "min_vram_gb": 8,
                "recommended_vram_gb": 12,
                "min_system_ram_gb": 16,
                "recommended_system_ram_gb": 32,
                "recommended_models": ["Llama-2-7B", "Mistral-7B", "Phi-2"],
                "recommended_methods": ["QLoRA", "DoRA"],
                "max_batch_size": 4,
                "max_model_size": "7B"
            },
            HardwareProfile.MID_RANGE: {
                "min_vram_gb": 16,
                "recommended_vram_gb": 24,
                "min_system_ram_gb": 32,
                "recommended_system_ram_gb": 64,
                "recommended_models": ["Llama-2-13B", "Llama-2-70B", "Mistral-7B"],
                "recommended_methods": ["QLoRA", "Standard LoRA", "DoRA"],
                "max_batch_size": 8,
                "max_model_size": "70B"
            },
            HardwareProfile.HIGH_END: {
                "min_vram_gb": 40,
                "recommended_vram_gb": 80,
                "min_system_ram_gb": 64,
                "recommended_system_ram_gb": 128,
                "recommended_models": ["Llama-2-70B", "Falcon-40B", "CodeLlama-34B"],
                "recommended_methods": ["Full Fine-tuning", "LoRA", "DoRA"],
                "max_batch_size": 32,
                "max_model_size": "70B"
            },
            HardwareProfile.MULTI_GPU: {
                "min_vram_gb_per_gpu": 16,
                "recommended_vram_gb_per_gpu": 40,
                "min_total_vram_gb": 64,
                "recommended_total_vram_gb": 160,
                "min_system_ram_gb": 128,
                "recommended_system_ram_gb": 256,
                "recommended_models": ["Llama-2-70B", "Falcon-40B", "CodeLlama-34B"],
                "recommended_methods": ["Distributed Full Fine-tuning", "QLoRA"],
                "max_batch_size": 64,
                "max_model_size": "70B"
            },
            HardwareProfile.CPU_ONLY: {
                "min_system_ram_gb": 32,
                "recommended_system_ram_gb": 64,
                "recommended_models": ["Phi-2", "GPT-2", "DistilGPT-2"],
                "recommended_methods": ["LoRA", "Full Fine-tuning"],
                "max_batch_size": 1,
                "max_model_size": "1B"
            }
        }

        return recommendations.get(hardware_profile, {})

def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Training Configuration Templates")
    parser.add_argument("--list-templates", action="store_true", help="List all available templates")
    parser.add_argument("--list-scenarios", action="store_true", help="List all available scenarios")
    parser.add_argument("--get-template", type=str, help="Get a specific template")
    parser.add_argument("--get-scenario", type=str, help="Get a specific scenario")
    parser.add_argument("--recommend", action="store_true", help="Get template recommendation")
    parser.add_argument("--model-size", choices=["small", "medium", "large", "xlarge", "xxlarge"], help="Model size")
    parser.add_argument("--hardware", choices=["low_end", "mid_range", "high_end", "multi_gpu", "cpu_only"], help="Hardware profile")
    parser.add_argument("--objective", choices=["instruction_tuning", "domain_adaptation", "continued_pretraining", "chat_finetuning", "code_finetuning"], help="Training objective")
    parser.add_argument("--save-template", type=str, help="Save template to file")
    parser.add_argument("--output-dir", type=str, default="configs/templates", help="Output directory")

    args = parser.parse_args()

    template_manager = TrainingTemplateManager()

    if args.list_templates:
        print("Available templates:")
        for template_name in template_manager.list_templates():
            template = template_manager.get_template(template_name)
            print(f"  - {template_name}: {template.get('description', 'No description')}")

    elif args.list_scenarios:
        print("Available scenarios:")
        for scenario_name in template_manager.list_scenarios():
            scenario = template_manager.get_scenario(scenario_name)
            print(f"  - {scenario_name}: {scenario.description}")

    elif args.get_template:
        template = template_manager.get_template(args.get_template)
        if template:
            print(f"Template: {template.get('name', 'Unknown')}")
            print(f"Description: {template.get('description', 'No description')}")
            print(f"Requirements: {template.get('requirements', {})}")
        else:
            print(f"Template '{args.get_template}' not found")

    elif args.get_scenario:
        scenario = template_manager.get_scenario(args.get_scenario)
        if scenario:
            print(f"Scenario: {scenario.name}")
            print(f"Description: {scenario.description}")
            print(f"Model Size: {scenario.model_size.value}")
            print(f"Hardware: {scenario.hardware_profile.value}")
            print(f"Objective: {scenario.training_objective.value}")
            print(f"Expected Memory: {scenario.expected_memory_usage_gb}GB")
            print(f"Training Time: {scenario.estimated_training_time_hours} hours")
        else:
            print(f"Scenario '{args.get_scenario}' not found")

    elif args.recommend:
        if not all([args.model_size, args.hardware, args.objective]):
            print("Error: --model-size, --hardware, and --objective are required for recommendation")
            return

        template_name = template_manager.recommend_template(
            ModelSize(args.model_size),
            HardwareProfile(args.hardware),
            TrainingObjective(args.objective)
        )

        print(f"Recommended template: {template_name}")
        template = template_manager.get_template(template_name)
        if template:
            print(f"Description: {template.get('description', 'No description')}")

    elif args.save_template and args.get_template:
        output_path = Path(args.output_dir) / f"{args.get_template}.json"
        template_manager.save_template(args.get_template, output_path)
        print(f"Template saved to {output_path}")

if __name__ == "__main__":
    main()