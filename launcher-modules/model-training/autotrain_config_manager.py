#!/usr/bin/env python3
"""
DuckBot AutoTrain Configuration Manager
Provides comprehensive configuration management for AutoTrain-Advanced projects
Includes templates, validation, and user-friendly configuration interface

Features:
- Pre-built configuration templates for common ML tasks
- Interactive configuration wizard
- Configuration validation and optimization
- YAML/JSON configuration file management
- Integration with DuckBot's existing configuration system
"""

import os
import json
import yaml
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict, field
from enum import Enum
import jsonschema

from autotrain_integration import AutoTrainConfig, AutoTrainProjectType, AutoTrainDeploymentTarget

class ConfigFormat(Enum):
    """Supported configuration file formats"""
    YAML = "yaml"
    JSON = "json"

@dataclass
class AutoTrainTemplate:
    """Pre-built configuration template"""
    name: str
    description: str
    project_type: AutoTrainProjectType
    base_config: Dict[str, Any]
    suitable_for: List[str] = field(default_factory=list)
    difficulty: str = "beginner"  # beginner, intermediate, advanced
    estimated_time: str = "1-2 hours"
    hardware_requirements: List[str] = field(default_factory=list)

class AutoTrainConfigManager:
    """Configuration manager for AutoTrain projects"""

    def __init__(self, config_dir: Optional[str] = None):
        self.config_dir = Path(config_dir) if config_dir else Path.cwd() / "autotrain_configs"
        self.config_dir.mkdir(exist_ok=True)

        self.logger = logging.getLogger(__name__)

        # Initialize templates
        self.templates = self._load_templates()

        # Configuration schema for validation
        self.config_schema = self._load_config_schema()

    def _load_templates(self) -> Dict[str, AutoTrainTemplate]:
        """Load pre-built configuration templates"""
        templates = {}

        # LLM Fine-tuning Templates
        templates["chatbot_finetuning"] = AutoTrainTemplate(
            name="Chatbot Fine-tuning",
            description="Fine-tune a language model for conversational AI",
            project_type=AutoTrainProjectType.LLM_FINE_TUNING,
            base_config={
                "model_name": "microsoft/DialoGPT-medium",
                "learning_rate": 2e-5,
                "num_epochs": 3,
                "batch_size": 8,
                "max_length": 512,
                "warmup_ratio": 0.1,
                "use_gpu": True,
                "mixed_precision": True,
                "use_peft": True,
                "quantization": False,
                "gradient_checkpointing": True
            },
            suitable_for=["Customer service bots", "Personal assistants", "FAQ systems"],
            difficulty="intermediate",
            estimated_time="2-4 hours",
            hardware_requirements=["GPU recommended", "8GB+ RAM"]
        )

        templates["code_generation"] = AutoTrainTemplate(
            name="Code Generation",
            description="Fine-tune a model for code generation and completion",
            project_type=AutoTrainProjectType.LLM_FINE_TUNING,
            base_config={
                "model_name": "Salesforce/codegen-350M-mono",
                "learning_rate": 1e-4,
                "num_epochs": 5,
                "batch_size": 4,
                "max_length": 1024,
                "warmup_ratio": 0.1,
                "use_gpu": True,
                "mixed_precision": True,
                "use_peft": True,
                "quantization": False,
                "gradient_checkpointing": True
            },
            suitable_for=["Code completion", "Automated programming", "Documentation generation"],
            difficulty="advanced",
            estimated_time="4-8 hours",
            hardware_requirements=["GPU required", "16GB+ RAM"]
        )

        # Text Classification Templates
        templates["sentiment_analysis"] = AutoTrainTemplate(
            name="Sentiment Analysis",
            description="Train a model for sentiment classification",
            project_type=AutoTrainProjectType.TEXT_CLASSIFICATION,
            base_config={
                "model_name": "distilbert-base-uncased",
                "learning_rate": 2e-5,
                "num_epochs": 5,
                "batch_size": 16,
                "max_length": 256,
                "warmup_ratio": 0.1,
                "use_gpu": True,
                "mixed_precision": False,
                "use_peft": False,
                "quantization": False,
                "gradient_checkpointing": False
            },
            suitable_for=["Review analysis", "Social media monitoring", "Customer feedback"],
            difficulty="beginner",
            estimated_time="30 minutes - 1 hour",
            hardware_requirements=["CPU okay", "4GB+ RAM"]
        )

        templates["spam_detection"] = AutoTrainTemplate(
            name="Spam Detection",
            description="Train a spam detection classifier",
            project_type=AutoTrainProjectType.TEXT_CLASSIFICATION,
            base_config={
                "model_name": "bert-base-uncased",
                "learning_rate": 2e-5,
                "num_epochs": 3,
                "batch_size": 32,
                "max_length": 128,
                "warmup_ratio": 0.1,
                "use_gpu": True,
                "mixed_precision": False,
                "use_peft": False,
                "quantization": False,
                "gradient_checkpointing": False
            },
            suitable_for=["Email filtering", "Comment moderation", "Content screening"],
            difficulty="beginner",
            estimated_time="1-2 hours",
            hardware_requirements=["CPU okay", "4GB+ RAM"]
        )

        # Text Generation Templates
        templates["story_generation"] = AutoTrainTemplate(
            name="Story Generation",
            description="Train a model for creative story generation",
            project_type=AutoTrainProjectType.TEXT_GENERATION,
            base_config={
                "model_name": "gpt2-medium",
                "learning_rate": 5e-5,
                "num_epochs": 3,
                "batch_size": 4,
                "max_length": 1024,
                "warmup_ratio": 0.1,
                "use_gpu": True,
                "mixed_precision": True,
                "use_peft": True,
                "quantization": False,
                "gradient_checkpointing": True
            },
            suitable_for=["Creative writing", "Content generation", "Story completion"],
            difficulty="intermediate",
            estimated_time="3-6 hours",
            hardware_requirements=["GPU recommended", "8GB+ RAM"]
        )

        return templates

    def _load_config_schema(self) -> Dict[str, Any]:
        """Load JSON schema for configuration validation"""
        return {
            "type": "object",
            "properties": {
                "project_name": {
                    "type": "string",
                    "minLength": 1,
                    "pattern": "^[a-zA-Z0-9_-]+$"
                },
                "project_type": {
                    "type": "string",
                    "enum": [pt.value for pt in AutoTrainProjectType]
                },
                "data_path": {
                    "type": "string",
                    "minLength": 1
                },
                "model_name": {
                    "type": "string",
                    "minLength": 1
                },
                "learning_rate": {
                    "type": "number",
                    "minimum": 1e-8,
                    "maximum": 1.0
                },
                "num_epochs": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 100
                },
                "batch_size": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 1024
                },
                "max_length": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 8192
                }
            },
            "required": ["project_name", "project_type", "data_path", "model_name"]
        }

    def list_templates(self) -> List[AutoTrainTemplate]:
        """List all available templates"""
        return list(self.templates.values())

    def get_template(self, template_name: str) -> Optional[AutoTrainTemplate]:
        """Get a specific template"""
        return self.templates.get(template_name)

    def create_config_from_template(self, template_name: str, project_name: str,
                                   data_path: str, **overrides) -> AutoTrainConfig:
        """Create configuration from template"""
        template = self.get_template(template_name)
        if not template:
            raise ValueError(f"Template '{template_name}' not found")

        # Create base config from template
        config_dict = template.base_config.copy()
        config_dict.update({
            "project_name": project_name,
            "project_type": template.project_type,
            "data_path": data_path
        })

        # Apply overrides
        config_dict.update(overrides)

        # Create AutoTrainConfig object
        return self._dict_to_config(config_dict)

    def _dict_to_config(self, config_dict: Dict[str, Any]) -> AutoTrainConfig:
        """Convert dictionary to AutoTrainConfig object"""
        # Handle enum conversion
        if isinstance(config_dict.get("project_type"), str):
            config_dict["project_type"] = AutoTrainProjectType(config_dict["project_type"])
        if isinstance(config_dict.get("deployment_target"), str):
            config_dict["deployment_target"] = AutoTrainDeploymentTarget(config_dict["deployment_target"])

        return AutoTrainConfig(**config_dict)

    def save_config(self, config: AutoTrainConfig, filename: str, format: ConfigFormat = ConfigFormat.YAML) -> str:
        """Save configuration to file"""
        config_path = self.config_dir / f"{filename}.{format.value}"

        config_dict = config.to_dict()

        if format == ConfigFormat.YAML:
            with open(config_path, 'w') as f:
                yaml.dump(config_dict, f, default_flow_style=False)
        else:  # JSON
            with open(config_path, 'w') as f:
                json.dump(config_dict, f, indent=2)

        self.logger.info(f"Configuration saved to {config_path}")
        return str(config_path)

    def load_config(self, filename: str) -> AutoTrainConfig:
        """Load configuration from file"""
        # Try YAML first, then JSON
        yaml_path = self.config_dir / f"{filename}.yaml"
        json_path = self.config_dir / f"{filename}.json"

        if yaml_path.exists():
            with open(yaml_path, 'r') as f:
                config_dict = yaml.safe_load(f)
        elif json_path.exists():
            with open(json_path, 'r') as f:
                config_dict = json.load(f)
        else:
            raise FileNotFoundError(f"Configuration file '{filename}' not found")

        return self._dict_to_config(config_dict)

    def list_configs(self) -> List[str]:
        """List all saved configurations"""
        configs = []
        for file_path in self.config_dir.glob("*.yaml"):
            configs.append(file_path.stem)
        for file_path in self.config_dir.glob("*.json"):
            if file_path.stem not in configs:  # Avoid duplicates
                configs.append(file_path.stem)
        return sorted(configs)

    def delete_config(self, filename: str) -> bool:
        """Delete a configuration file"""
        yaml_path = self.config_dir / f"{filename}.yaml"
        json_path = self.config_dir / f"{filename}.json"

        deleted = False
        if yaml_path.exists():
            yaml_path.unlink()
            deleted = True
        if json_path.exists():
            json_path.unlink()
            deleted = True

        if deleted:
            self.logger.info(f"Configuration '{filename}' deleted")

        return deleted

    def validate_config(self, config: AutoTrainConfig) -> Dict[str, Any]:
        """Validate configuration and return validation results"""
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "recommendations": []
        }

        # Schema validation
        try:
            jsonschema.validate(config.to_dict(), self.config_schema)
        except jsonschema.ValidationError as e:
            validation_result["valid"] = False
            validation_result["errors"].append(f"Schema validation error: {e.message}")

        # Data path validation
        if not os.path.exists(config.data_path):
            validation_result["warnings"].append(f"Data path does not exist: {config.data_path}")

        # Hardware validation
        if config.use_gpu and not self._is_gpu_available():
            validation_result["warnings"].append("GPU requested but not available")

        # Memory estimation
        memory_warning = self._estimate_memory_requirements(config)
        if memory_warning:
            validation_result["warnings"].append(memory_warning)

        # Project-specific validation
        project_validation = self._validate_project_specific(config)
        validation_result["errors"].extend(project_validation["errors"])
        validation_result["warnings"].extend(project_validation["warnings"])
        validation_result["recommendations"].extend(project_validation["recommendations"])

        return validation_result

    def _is_gpu_available(self) -> bool:
        """Check if GPU is available"""
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False

    def _estimate_memory_requirements(self, config: AutoTrainConfig) -> Optional[str]:
        """Estimate memory requirements and return warning if needed"""
        try:
            import psutil
            available_memory = psutil.virtual_memory().available / (1024**3)  # GB

            # Rough estimation based on model size and batch size
            model_size_factor = {
                "small": 2,    # ~2GB
                "medium": 4,   # ~4GB
                "large": 8,    # ~8GB
                "xlarge": 16   # ~16GB
            }

            # Estimate model size from name
            if "small" in config.model_name.lower():
                estimated_memory = model_size_factor["small"] * config.batch_size
            elif "medium" in config.model_name.lower():
                estimated_memory = model_size_factor["medium"] * config.batch_size
            elif "large" in config.model_name.lower():
                estimated_memory = model_size_factor["large"] * config.batch_size
            else:
                estimated_memory = model_size_factor["medium"] * config.batch_size

            if estimated_memory > available_memory * 0.8:  # 80% threshold
                return f"Estimated memory usage ({estimated_memory:.1f}GB) exceeds available memory ({available_memory:.1f}GB)"

        except ImportError:
            pass

        return None

    def _validate_project_specific(self, config: AutoTrainConfig) -> Dict[str, List[str]]:
        """Project-specific validation"""
        result = {"errors": [], "warnings": [], "recommendations": []}

        if config.project_type == AutoTrainProjectType.LLM_FINE_TUNING:
            if config.max_length > 2048:
                result["warnings"].append("Large max_length may cause memory issues for LLM fine-tuning")

            if config.learning_rate > 1e-4:
                result["warnings"].append("High learning rate may cause instability in LLM fine-tuning")

            result["recommendations"].append("Consider using PEFT for LLM fine-tuning to reduce memory usage")

        elif config.project_type == AutoTrainProjectType.TEXT_CLASSIFICATION:
            if config.batch_size > 64:
                result["warnings"].append("Large batch size may not be necessary for text classification")

            result["recommendations"].append("Consider using a smaller model like DistilBERT for text classification")

        elif config.project_type == AutoTrainProjectType.IMAGE_CLASSIFICATION:
            if not config.use_gpu:
                result["errors"].append("GPU is recommended for image classification")

        return result

    def optimize_config(self, config: AutoTrainConfig, hardware_profile: str = "auto") -> AutoTrainConfig:
        """Optimize configuration for specific hardware profile"""
        import copy
        optimized_config = copy.deepcopy(config)

        if hardware_profile == "auto":
            hardware_profile = self._detect_hardware_profile()

        profiles = {
            "low_end": {
                "batch_size": min(config.batch_size, 4),
                "use_gpu": False,
                "mixed_precision": False,
                "gradient_checkpointing": True,
                "use_peft": True
            },
            "medium": {
                "batch_size": min(config.batch_size, 8),
                "use_gpu": True,
                "mixed_precision": True,
                "gradient_checkpointing": True,
                "use_peft": True
            },
            "high_end": {
                "batch_size": min(config.batch_size, 32),
                "use_gpu": True,
                "mixed_precision": True,
                "gradient_checkpointing": False,
                "use_peft": False
            }
        }

        if hardware_profile in profiles:
            profile = profiles[hardware_profile]
            for key, value in profile.items():
                setattr(optimized_config, key, value)

        return optimized_config

    def _detect_hardware_profile(self) -> str:
        """Detect hardware profile"""
        try:
            import psutil
            import torch

            cpu_count = psutil.cpu_count()
            memory_gb = psutil.virtual_memory().total / (1024**3)
            gpu_available = torch.cuda.is_available()

            if memory_gb < 8 or not gpu_available:
                return "low_end"
            elif memory_gb < 16 or cpu_count < 8:
                return "medium"
            else:
                return "high_end"

        except ImportError:
            return "medium"

    def create_wizard_config(self) -> AutoTrainConfig:
        """Interactive configuration wizard"""
        print("=== AutoTrain Configuration Wizard ===\n")

        # Project name
        project_name = input("Enter project name (alphanumeric, underscores, hyphens): ").strip()
        while not project_name or not all(c.isalnum() or c in '_-' for c in project_name):
            print("Invalid project name. Use only letters, numbers, underscores, and hyphens.")
            project_name = input("Enter project name: ").strip()

        # Project type
        print("\nAvailable project types:")
        for i, pt in enumerate(AutoTrainProjectType, 1):
            print(f"{i}. {pt.value.replace('_', ' ').title()}")

        while True:
            try:
                choice = int(input("\nSelect project type (number): ")) - 1
                if 0 <= choice < len(AutoTrainProjectType):
                    project_type = list(AutoTrainProjectType)[choice]
                    break
                else:
                    print("Invalid choice. Please try again.")
            except ValueError:
                print("Please enter a valid number.")

        # Template selection
        templates = [t for t in self.templates.values() if t.project_type == project_type]
        if templates:
            print("\nAvailable templates:")
            for i, template in enumerate(templates, 1):
                print(f"{i}. {template.name} - {template.description}")

            print(f"{len(templates) + 1}. Custom configuration")

            while True:
                try:
                    choice = int(input("\nSelect template (number): ")) - 1
                    if 0 <= choice < len(templates):
                        template = templates[choice]
                        config = self.create_config_from_template(
                            template.name, project_name, "placeholder_data"
                        )
                        break
                    elif choice == len(templates):
                        config = AutoTrainConfig(
                            project_name=project_name,
                            project_type=project_type,
                            data_path="placeholder_data",
                            model_name="placeholder_model"
                        )
                        break
                    else:
                        print("Invalid choice. Please try again.")
                except ValueError:
                    print("Please enter a valid number.")
        else:
            config = AutoTrainConfig(
                project_name=project_name,
                project_type=project_type,
                data_path="placeholder_data",
                model_name="placeholder_model"
            )

        # Data path
        data_path = input("\nEnter path to training data: ").strip()
        while not data_path or not os.path.exists(data_path):
            if data_path and not os.path.exists(data_path):
                print(f"Path does not exist: {data_path}")
            data_path = input("Enter path to training data: ").strip()
        config.data_path = data_path

        # Model name
        config.model_name = input("Enter model name (e.g., bert-base-uncased): ").strip()

        # Additional parameters
        print("\nOptional parameters (press Enter to use defaults):")

        lr_input = input(f"Learning rate (default: {config.learning_rate}): ").strip()
        if lr_input:
            try:
                config.learning_rate = float(lr_input)
            except ValueError:
                print("Invalid learning rate, using default.")

        epochs_input = input(f"Number of epochs (default: {config.num_epochs}): ").strip()
        if epochs_input:
            try:
                config.num_epochs = int(epochs_input)
            except ValueError:
                print("Invalid number of epochs, using default.")

        batch_input = input(f"Batch size (default: {config.batch_size}): ").strip()
        if batch_input:
            try:
                config.batch_size = int(batch_input)
            except ValueError:
                print("Invalid batch size, using default.")

        # Hardware options
        gpu_input = input("Use GPU? (y/N, default: Y): ").strip().lower()
        config.use_gpu = gpu_input in ['y', 'yes', 'true', '1'] if gpu_input else True

        # Validation
        validation = self.validate_config(config)
        if validation["errors"]:
            print("\nConfiguration has errors:")
            for error in validation["errors"]:
                print(f"  - {error}")
            return None

        if validation["warnings"]:
            print("\nConfiguration warnings:")
            for warning in validation["warnings"]:
                print(f"  - {warning}")

        # Save configuration
        save_input = input("\nSave configuration? (Y/n, default: Y): ").strip().lower()
        if save_input in ['y', 'yes', 'true', '1'] or not save_input:
            filename = input("Enter configuration filename (without extension): ").strip()
            if filename:
                self.save_config(config, filename)
                print(f"Configuration saved as '{filename}'")

        return config

    def export_config_summary(self, config: AutoTrainConfig) -> str:
        """Export configuration summary in readable format"""
        summary = f"""
AutoTrain Configuration Summary
==============================

Project: {config.project_name}
Type: {config.project_type.value.replace('_', ' ').title()}
Model: {config.model_name}
Data Path: {config.data_path}

Training Parameters:
- Learning Rate: {config.learning_rate}
- Epochs: {config.num_epochs}
- Batch Size: {config.batch_size}
- Max Length: {config.max_length}
- Warmup Ratio: {config.warmup_ratio}

Hardware Settings:
- Use GPU: {config.use_gpu}
- Mixed Precision: {config.mixed_precision}
- Gradient Accumulation: {config.gradient_accumulation}

Advanced Options:
- Use PEFT: {config.use_peft}
- Quantization: {config.quantization}
- Gradient Checkpointing: {config.gradient_checkpointing}

Deployment: {config.deployment_target.value}
"""
        return summary.strip()

if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)

    config_manager = AutoTrainConfigManager()

    # List available templates
    print("Available templates:")
    for template in config_manager.list_templates():
        print(f"  - {template.name}: {template.description}")

    # Create configuration using wizard
    config = config_manager.create_wizard_config()
    if config:
        print("\nConfiguration created successfully!")
        print(config_manager.export_config_summary(config))