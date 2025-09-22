#!/usr/bin/env python3
"""
Model Training Module for DuckBot Modular Launcher
"""

import os
import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Try to import DuckBot modules
try:
    # These imports might fail if we're not in the full DuckBot environment
    from launcher.models.service_config import ServiceConfig, ServiceType
    from launcher.models.launch_mode import LaunchMode
    
    DUCKBOT_AVAILABLE = True
except ImportError:
    # Create mock classes for standalone operation
    class ServiceType:
        AI_SERVICE = "ai_service"
        WEB_UI = "web_ui"
        MONITORING = "monitoring"
        AUTOMATION = "automation"
        INTEGRATION = "integration"
        UTILITY = "utility"
    
    class ServiceConfig:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
    
    class LaunchMode:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
    
    DUCKBOT_AVAILABLE = False

def get_service_config() -> ServiceConfig:
    """Get the service configuration for the model training module"""
    return ServiceConfig(
        name="model_training",
        display_name="🤖 Model Training & Fine-tuning",
        type=ServiceType.AI_SERVICE,
        description="Train and fine-tune AI models with GGUF and Hugging Face support. AutoTrain-like interface.",
        command=f"python {Path(__file__).parent / 'ui_server.py'}",
        working_dir=str(Path(__file__).parent),
        ports=[8080],
        dependencies=[],
        env_vars={},
        log_file="logs/model_training.log",
        enabled=True
    )

def get_launch_modes() -> list:
    """Get launch modes for the model training module"""
    return [
        LaunchMode(
            name="model_training",
            display_name="🤖 Model Training Studio",
            description="Complete model training and fine-tuning environment with AutoTrain-like interface",
            services=["model_training"],
            priority=7,
            icon="🤖"
        )
    ]

def get_module_info() -> dict:
    """Get information about this module"""
    return {
        "name": "model_training",
        "display_name": "Model Training & Fine-tuning",
        "description": "Train and fine-tune AI models with GGUF and Hugging Face support. Features AutoTrain-like interface.",
        "version": "1.0.0",
        "author": "DuckBot Team",
        "category": "ai",
        "enabled": True,
        "dependencies": [
            "transformers",
            "datasets", 
            "torch",
            "peft",
            "bitsandbytes",
            "huggingface_hub"
        ]
    }

if __name__ == "__main__":
    # Test the module
    print("Model Training Module for DuckBot")
    print("=" * 40)
    print(f"Service Config: {get_service_config()}")
    print(f"Launch Modes: {get_launch_modes()}")
    print(f"Module Info: {get_module_info()}")