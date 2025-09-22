#!/usr/bin/env python3
"""
MCP Server Diagnostic Script
Tests MCP server startup and provides detailed diagnostic information
"""

import asyncio
import sys
import os
import subprocess
import json
from pathlib import Path

def test_python_environment():
    """Test Python environment and dependencies"""
    print("=== Python Environment Test ===")

    # Test Python version
    print(f"Python version: {sys.version}")

    # Test critical imports
    imports_to_test = [
        'asyncio',
        'json',
        'pathlib',
        'argparse',
        'logging',
        'sys',
        'os'
    ]

    failed_imports = []
    for module in imports_to_test:
        try:
            __import__(module)
            print(f"✓ {module}")
        except ImportError as e:
            print(f"✗ {module}: {e}")
            failed_imports.append(module)

    if failed_imports:
        print(f"Failed imports: {failed_imports}")
        return False

    return True

def test_duckbot_imports():
    """Test DuckBot-specific imports"""
    print("\n=== DuckBot Import Test ===")

    # Add project root to path
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))

    imports_to_test = [
        'duckbot.integrations.mcp_server',
        'duckbot.core.health_monitor'
    ]

    failed_imports = []
    for module in imports_to_test:
        try:
            __import__(module)
            print(f"✓ {module}")
        except ImportError as e:
            print(f"✗ {module}: {e}")
            failed_imports.append(module)

    if failed_imports:
        print(f"Failed DuckBot imports: {failed_imports}")
        return False

    return True

def test_mcp_server_startup():
    """Test MCP server startup with different configurations"""
    print("\n=== MCP Server Startup Test ===")

    # Test 1: Dry run with help
    try:
        result = subprocess.run([
            sys.executable, 'start_mcp_server.py', '--help'
        ], capture_output=True, text=True, timeout=10)

        if result.returncode == 0:
            print("✓ MCP server help command works")
        else:
            print(f"✗ MCP server help failed: {result.stderr}")
    except subprocess.TimeoutExpired:
        print("✗ MCP server help command timed out")
    except Exception as e:
        print(f"✗ MCP server help command error: {e}")

    # Test 2: Actual startup attempt
    try:
        print("Testing MCP server startup...")
        result = subprocess.run([
            sys.executable, 'start_mcp_server.py',
            '--host', '127.0.0.1',
            '--port', '8791'
        ], capture_output=True, text=True, timeout=15)

        print(f"Return code: {result.returncode}")
        print(f"Stdout: {result.stdout}")
        print(f"Stderr: {result.stderr}")

        if result.returncode == 0:
            print("✓ MCP server started successfully")
        else:
            print(f"✗ MCP server failed with code {result.returncode}")

    except subprocess.TimeoutExpired:
        print("✗ MCP server startup timed out")
    except Exception as e:
        print(f"✗ MCP server startup error: {e}")

def test_directory_structure():
    """Test required directory structure"""
    print("\n=== Directory Structure Test ===")

    required_dirs = [
        'logs',
        'duckbot',
        'duckbot/integrations',
        'duckbot/core'
    ]

    missing_dirs = []
    for dir_name in required_dirs:
        dir_path = Path(dir_name)
        if dir_path.exists():
            print(f"✓ {dir_name}")
        else:
            print(f"✗ {dir_name} - missing")
            missing_dirs.append(dir_name)

    if missing_dirs:
        print(f"Missing directories: {missing_dirs}")
        return False

    return True

def test_file_permissions():
    """Test file permissions for key files"""
    print("\n=== File Permissions Test ===")

    key_files = [
        'start_mcp_server.py',
        'duckbot/integrations/mcp_server.py',
        'duckbot/core/health_monitor.py'
    ]

    permission_issues = []
    for file_name in key_files:
        file_path = Path(file_name)
        if file_path.exists():
            if os.access(file_path, os.R_OK):
                print(f"✓ {file_name} - readable")
            else:
                print(f"✗ {file_name} - not readable")
                permission_issues.append(file_name)
        else:
            print(f"✗ {file_name} - missing")
            permission_issues.append(file_name)

    if permission_issues:
        print(f"Permission issues: {permission_issues}")
        return False

    return True

def main():
    """Main diagnostic function"""
    print("DuckBot MCP Server Diagnostic")
    print("=" * 50)

    # Change to project directory
    project_root = Path(__file__).parent
    os.chdir(project_root)

    # Run all tests
    tests = [
        test_python_environment,
        test_directory_structure,
        test_file_permissions,
        test_duckbot_imports,
        test_mcp_server_startup
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"Test {test.__name__} failed: {e}")
            results.append(False)

    # Summary
    print("\n" + "=" * 50)
    print("Diagnostic Summary")
    print("=" * 50)

    passed = sum(results)
    total = len(results)

    print(f"Tests passed: {passed}/{total}")

    if passed == total:
        print("✓ All tests passed - MCP server should work")
        return 0
    else:
        print("✗ Some tests failed - MCP server may not work")
        return 1

if __name__ == "__main__":
    sys.exit(main())