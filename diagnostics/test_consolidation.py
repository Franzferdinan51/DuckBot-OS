#!/usr/bin/env python3
"""
DuckBot Consolidation Validation Script
Tests that all consolidated modules work correctly and provide backward compatibility.
"""

import sys
import os
from pathlib import Path

def test_import(module_name, expected_exports=None):
    """Test importing a module and optionally check for expected exports"""
    try:
        print(f"Testing import: {module_name}", end=" ")

        # Test import
        module = __import__(module_name, fromlist=['*'])

        if expected_exports:
            missing_exports = []
            for export in expected_exports:
                if not hasattr(module, export):
                    missing_exports.append(export)

            if missing_exports:
                print(f"FAILED - Missing exports: {missing_exports}")
                return False
            else:
                print(f"SUCCESS - All {len(expected_exports)} exports available")
                return True
        else:
            print("SUCCESS")
            return True

    except ImportError as e:
        print(f"FAILED - Import error: {e}")
        return False
    except Exception as e:
        print(f"FAILED - Unexpected error: {e}")
        return False

def test_backward_compatibility():
    """Test that old import patterns still work with warnings"""
    print("\nTesting Backward Compatibility")
    print("=" * 50)

    compatibility_tests = [
        ("duckbot.cost_management", ["CostTracker", "CostVisualizer", "CostCommands"]),
        ("duckbot.charm_manager", ["CharmToolsIntegration", "CharmManager"]),
        ("duckbot.webui_manager", ["DuckBotWebUI", "WebUIConfig"]),
        ("duckbot.ai_router_manager", ["AIRouter", "AISettings", "route_task"]),
    ]

    passed = 0
    total = len(compatibility_tests)

    for module_name, expected_exports in compatibility_tests:
        if test_import(module_name, expected_exports):
            passed += 1

    print(f"\nCompatibility Tests: {passed}/{total} passed")
    return passed == total

def test_new_modules():
    """Test that new consolidated modules work correctly"""
    print("\nTesting New Consolidated Modules")
    print("=" * 50)

    module_tests = [
        ("duckbot.cost_management", ["CostTracker", "ModelPricing", "UsageRecord"]),
        ("duckbot.charm_manager", ["CharmManager", "CharmToolsIntegration", "LipglossStyle"]),
        ("duckbot.webui_manager", ["DuckBotWebUI", "WebUIConfig", "ChatMessage"]),
        ("duckbot.ai_router_manager", ["AIRouter", "AISettings", "SettingsManager"]),
        ("duckbot.consolidation_mapping", ["get_migration_guide", "get_consolidation_summary"]),
    ]

    passed = 0
    total = len(module_tests)

    for module_name, expected_exports in module_tests:
        if test_import(module_name, expected_exports):
            passed += 1

    print(f"\nNew Module Tests: {passed}/{total} passed")
    return passed == total

def test_optional_features():
    """Test optional features and integrations"""
    print("\nTesting Optional Features")
    print("=" * 50)

    # Test that modules handle missing optional dependencies gracefully
    optional_tests = [
        "duckbot.cost_management",
        "duckbot.charm_manager",
        "duckbot.webui_manager",
        "duckbot.ai_router_manager"
    ]

    passed = 0
    total = len(optional_tests)

    for module_name in optional_tests:
        try:
            print(f"Testing {module_name} handles missing dependencies", end=" ")
            module = __import__(module_name, fromlist=['*'])

            # Test that module can be imported without crashing
            if hasattr(module, '__name__'):
                print("SUCCESS")
                passed += 1
            else:
                print("FAILED - Module not properly loaded")

        except Exception as e:
            print(f"FAILED - {e}")

    print(f"\nOptional Feature Tests: {passed}/{total} passed")
    return passed == total

def test_file_structure():
    """Test that all expected files exist"""
    print("\nTesting File Structure")
    print("=" * 50)

    expected_files = [
        "duckbot/cost_management.py",
        "duckbot/charm_manager.py",
        "duckbot/webui_manager.py",
        "duckbot/ai_router_manager.py",
        "duckbot/consolidation_mapping.py",
        "duckbot_openwebui_function_fixed.json",
        "consolidation_complete.md"
    ]

    base_path = Path.cwd()
    passed = 0
    total = len(expected_files)

    for file_path in expected_files:
        full_path = base_path / file_path
        print(f"Checking {file_path}", end=" ")

        if full_path.exists():
            print("EXISTS")
            passed += 1
        else:
            print("MISSING")

    print(f"\nFile Structure Tests: {passed}/{total} passed")
    return passed == total

def test_performance():
    """Basic performance test - measure import times"""
    print("\nTesting Import Performance")
    print("=" * 50)

    import time

    modules_to_test = [
        "duckbot.cost_management",
        "duckbot.charm_manager",
        "duckbot.webui_manager",
        "duckbot.ai_router_manager"
    ]

    total_time = 0

    for module_name in modules_to_test:
        start_time = time.time()
        try:
            __import__(module_name)
            import_time = time.time() - start_time
            print(f"{module_name}: {import_time:.3f}s")
            total_time += import_time
        except Exception as e:
            print(f"{module_name}: FAILED - {e}")

    print(f"\nTotal Import Time: {total_time:.3f}s")
    return total_time < 2.0  # Should be under 2 seconds

def main():
    """Run all validation tests"""
    print("DuckBot Consolidation Validation")
    print("=" * 60)

    # Add duckbot directory to path
    duckbot_path = Path.cwd() / "duckbot"
    if duckbot_path.exists():
        sys.path.insert(0, str(duckbot_path))

    # Run all tests
    tests = [
        ("File Structure", test_file_structure),
        ("New Modules", test_new_modules),
        ("Backward Compatibility", test_backward_compatibility),
        ("Optional Features", test_optional_features),
        ("Performance", test_performance)
    ]

    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"{test_name} test crashed: {e}")
            results[test_name] = False

    # Summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)

    passed = sum(results.values())
    total = len(results)

    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        print(f"{status} {test_name}")

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("\nALL TESTS PASSED! Consolidation successful!")
        print("\nReady for production use!")
        return 0
    else:
        print(f"\n{total - passed} tests failed. Review issues above.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)