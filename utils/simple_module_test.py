#!/usr/bin/env python3
"""
Simple test to verify which modules are available
"""

import os
import sys

def test_module_imports():
    """Test which modules can be imported"""

    modules_to_test = [
        'ai_cache_manager',
        'start_ai_ecosystem',
        'start_ecosystem',
        'ai_ecosystem_manager',
        'doctor_check_imports',
        'doctor_check_services'
    ]

    working_modules = []
    failed_modules = []

    for module in modules_to_test:
        try:
            __import__(module)
            working_modules.append(module)
            print(f"[OK] {module}")
        except Exception as e:
            failed_modules.append((module, str(e)))
            print(f"[FAIL] {module}: {e}")

    print(f"\nWorking modules: {len(working_modules)}")
    print(f"Failed modules: {len(failed_modules)}")

    return working_modules, failed_modules

if __name__ == "__main__":
    test_module_imports()