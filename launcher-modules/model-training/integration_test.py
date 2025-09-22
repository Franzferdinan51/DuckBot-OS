#!/usr/bin/env python3
"""
Integration test for the Model Training Module with DuckBot Launcher
"""

import os
import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_module_structure():
    """Test that the module directory structure is correct"""
    # Use absolute path from the test script location
    test_dir = Path(__file__).parent
    module_dir = test_dir
    
    required_files = [
        "model_trainer.py",
        "module.py",
        "config.json",
        "requirements.txt",
        "START_MODEL_TRAINING.bat",
        "START_FROM_ELECTRON.bat",
        "autotrain_ui.html",
        "web_ui.py",
        "api_server.py",
        "README.md"
    ]
    
    print("Testing module directory structure...")
    
    if not module_dir.exists():
        print("X Module directory not found")
        return False
    
    missing_files = []
    for file_name in required_files:
        file_path = module_dir / file_name
        if not file_path.exists():
            missing_files.append(file_name)
    
    if missing_files:
        print(f"X Missing files: {missing_files}")
        return False
    
    print("OK All required files present")
    return True

def test_module_import():
    """Test that the module can be imported"""
    try:
        module_dir = Path(__file__).parent
        sys.path.insert(0, str(module_dir))
        
        import module
        print("OK Module imported successfully")
        
        # Test module functions
        if hasattr(module, 'get_module_info'):
            info = module.get_module_info()
            print(f"OK Module info: {info}")
        
        if hasattr(module, 'get_service_config'):
            service_config = module.get_service_config()
            print(f"OK Service config: {service_config.name}")
        
        if hasattr(module, 'get_launch_modes'):
            launch_modes = module.get_launch_modes()
            print(f"OK Launch modes: {[mode.name for mode in launch_modes]}")
        
        return True
    except Exception as e:
        print(f"X Module import failed: {e}")
        return False

def test_config_bridge_integration():
    """Test that the module is integrated with the config bridge"""
    try:
        # Check if the config bridge includes the model training mode
        test_dir = Path(__file__).parent
        project_root = test_dir.parent.parent
        config_bridge_path = project_root / "config" / "config_bridge.py"
        if not config_bridge_path.exists():
            print("X Config bridge not found")
            return False
        
        with open(config_bridge_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'model_training' in content:
            print("OK Model training mode found in config bridge")
            return True
        else:
            print("X Model training mode not found in config bridge")
            return False
    except Exception as e:
        print(f"X Config bridge test failed: {e}")
        return False

def test_launcher_integration():
    """Test that the module is integrated with the launcher"""
    try:
        # Check if the launcher config manager includes the model training service
        test_dir = Path(__file__).parent
        project_root = test_dir.parent.parent
        config_manager_path = project_root / "launcher" / "core" / "config_manager.py"
        if not config_manager_path.exists():
            print("X Config manager not found")
            return False
        
        with open(config_manager_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'model_training' in content:
            print("OK Model training service found in launcher config")
            return True
        else:
            print("X Model training service not found in launcher config")
            return False
    except Exception as e:
        print(f"X Launcher integration test failed: {e}")
        return False

def test_api_server():
    """Test that the API server can be imported"""
    try:
        test_dir = Path(__file__).parent
        sys.path.insert(0, str(test_dir))
        
        import api_server
        print("OK API server imported successfully")
        return True
    except Exception as e:
        print(f"X API server import failed: {e}")
        return False

def main():
    """Run all integration tests"""
    print("DuckBot Model Training Module Integration Test")
    print("=" * 50)
    
    tests = [
        test_module_structure,
        test_module_import,
        test_config_bridge_integration,
        test_launcher_integration,
        test_api_server
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("All integration tests passed!")
        return 0
    else:
        print("Some integration tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())