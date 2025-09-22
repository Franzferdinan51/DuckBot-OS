#!/usr/bin/env python3
"""
Test script for the Model Training Module
"""

import os
import sys
from pathlib import Path

def test_module_structure():
    """Test that the module directory structure is correct"""
    module_dir = Path(__file__).parent
    required_files = [
        "model_trainer.py",
        "ui_server.py",
        "module.py",
        "config.json",
        "requirements.txt",
        "START_MODEL_TRAINING.bat",
        "START_FROM_ELECTRON.bat",
        "enhanced_autotrain_ui.html",
        "sample_dataset.json",
        "sample_training_config.json",
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
            print(f"OK Module info: {info['name']}")
        
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

def test_ui_files():
    """Test that UI files exist and are valid"""
    module_dir = Path(__file__).parent
    ui_files = ["enhanced_autotrain_ui.html", "autotrain_ui.html", "ui.html"]
    
    print("Testing UI files...")
    
    found_ui = False
    for ui_file in ui_files:
        file_path = module_dir / ui_file
        if file_path.exists():
            # Check if file has content
            if file_path.stat().st_size > 0:
                found_ui = True
                print(f"OK Found UI file: {ui_file}")
            else:
                print(f"X UI file is empty: {ui_file}")
                return False
    
    if not found_ui:
        print("X No UI files found")
        return False
    
    return True

def test_requirements():
    """Test that requirements file exists"""
    module_dir = Path(__file__).parent
    req_file = module_dir / "requirements.txt"
    
    print("Testing requirements file...")
    
    if not req_file.exists():
        print("X Requirements file not found")
        return False
    
    if req_file.stat().st_size == 0:
        print("X Requirements file is empty")
        return False
    
    print("OK Requirements file is valid")
    return True

def main():
    """Run all tests"""
    print("DuckBot Model Training Module Test")
    print("=" * 40)
    
    tests = [
        test_module_structure,
        test_module_import,
        test_ui_files,
        test_requirements
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 40)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("All tests passed!")
        return 0
    else:
        print("Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())