#!/usr/bin/env python3
"""
DuckBot Integration Test Runner
Simple runner for integration tests
"""

import os
import sys
import subprocess
import time
from pathlib import Path
from datetime import datetime

def run_test(test_path: str, test_name: str):
    """Run a single test"""
    print(f"\n{'='*60}")
    print(f"Running {test_name}...")
    print(f"{'='*60}")

    try:
        result = subprocess.run([
            sys.executable, test_path, "--verbose"
        ], capture_output=True, text=True, timeout=300, cwd=Path.cwd())

        print(result.stdout)
        if result.stderr:
            print(f"STDERR:\n{result.stderr}")

        return result.returncode == 0

    except subprocess.TimeoutExpired:
        print("Test timed out")
        return False
    except Exception as e:
        print(f"Test failed with error: {e}")
        return False

def main():
    """Main entry point"""
    print("DuckBot Integration Test Runner")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python: {sys.version.split()[0]}")
    print(f"Platform: {sys.platform}")

    # Tests to run
    tests = [
        ("tests/integration/test_current_launcher.py", "Current Launcher"),
        ("tests/integration/test_configuration_integration.py", "Configuration System"),
    ]

    passed = 0
    failed = 0

    for test_path, test_name in tests:
        if Path(test_path).exists():
            if run_test(test_path, test_name):
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                failed += 1
                print(f"❌ {test_name} FAILED")
        else:
            failed += 1
            print(f"❌ {test_name} - Test file not found")

    # Summary
    print(f"\n{'='*60}")
    print("INTEGRATION TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Total Tests: {passed + failed}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success Rate: {(passed/(passed+failed)*100):.1f}%")

    if failed > 0:
        print("\n❌ Some tests failed. Please review the output above.")
        return 1
    else:
        print("\n✅ All tests passed!")
        return 0

if __name__ == "__main__":
    sys.exit(main())