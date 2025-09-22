#!/usr/bin/env python3
"""
Module loader for DuckBot launcher modules
"""

import os
import sys
from pathlib import Path
import importlib.util

def discover_modules():
    """Discover all available launcher modules"""
    project_root = Path(__file__).parent.parent.parent
    modules_dir = project_root / "launcher-modules"
    
    if not modules_dir.exists():
        return []
    
    modules = []
    for module_dir in modules_dir.iterdir():
        if module_dir.is_dir():
            # Look for module.py or __init__.py
            module_file = module_dir / "module.py"
            if module_file.exists():
                modules.append({
                    "name": module_dir.name,
                    "path": str(module_dir),
                    "module_file": str(module_file)
                })
    
    return modules

def load_module(module_path):
    """Load a module dynamically"""
    module_file = Path(module_path) / "module.py"
    
    if not module_file.exists():
        raise FileNotFoundError(f"Module file not found: {module_file}")
    
    # Load the module
    spec = importlib.util.spec_from_file_location("module", module_file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    return module

def get_module_info(module_path):
    """Get information about a module"""
    try:
        module = load_module(module_path)
        if hasattr(module, 'get_module_info'):
            return module.get_module_info()
        else:
            # Fallback information
            return {
                "name": Path(module_path).name,
                "display_name": Path(module_path).name.replace("-", " ").title(),
                "description": "DuckBot launcher module",
                "version": "1.0.0",
                "enabled": True
            }
    except Exception as e:
        return {
            "name": Path(module_path).name,
            "display_name": Path(module_path).name.replace("-", " ").title(),
            "description": f"Error loading module: {e}",
            "version": "0.0.0",
            "enabled": False
        }

def get_module_service_config(module_path):
    """Get service configuration for a module"""
    try:
        module = load_module(module_path)
        if hasattr(module, 'get_service_config'):
            return module.get_service_config()
    except Exception as e:
        print(f"Error loading service config for {module_path}: {e}")
        return None

def get_module_launch_modes(module_path):
    """Get launch modes for a module"""
    try:
        module = load_module(module_path)
        if hasattr(module, 'get_launch_modes'):
            return module.get_launch_modes()
    except Exception as e:
        print(f"Error loading launch modes for {module_path}: {e}")
        return []

if __name__ == "__main__":
    # Test module discovery
    print("Discovering DuckBot launcher modules...")
    modules = discover_modules()
    
    print(f"Found {len(modules)} modules:")
    for module in modules:
        print(f"  - {module['name']}")
        info = get_module_info(module['path'])
        print(f"    Display Name: {info.get('display_name', 'N/A')}")
        print(f"    Description: {info.get('description', 'N/A')}")
        print(f"    Version: {info.get('version', 'N/A')}")
        print(f"    Enabled: {info.get('enabled', False)}")
        print()