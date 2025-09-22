#!/usr/bin/env python3
"""
DuckBot Electron Launcher Validation Script
Tests all components and dependencies for the START_ELECTRON_LAUNCHER.bat
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def test_nodejs():
    """Test Node.js installation"""
    print("Testing Node.js installation...")
    try:
        result = subprocess.run(['node', '--version'],
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"[OK] Node.js {result.stdout.strip()}")
            return True
        else:
            print(f"[ERROR] Node.js not working: {result.stderr}")
            return False
    except Exception as e:
        print(f"[ERROR] Node.js test failed: {e}")
        return False

def test_react_webui():
    """Test React WebUI directory and files"""
    print("\nTesting React WebUI structure...")
    react_dir = Path("duckbot/react-webui")

    if not react_dir.exists():
        print(f"[ERROR] React WebUI directory not found: {react_dir}")
        return False

    required_files = [
        "package.json",
        "electron-main.js"
    ]

    # Check for either index.js or index.tsx
    index_js = react_dir / "src/index.js"
    index_tsx = react_dir / "src/index.tsx"
    if index_js.exists():
        print("[OK] src/index.js")
    elif index_tsx.exists():
        print("[OK] src/index.tsx")
    else:
        print("[ERROR] Missing src/index.js or src/index.tsx")
        return False

    for file in required_files:
        file_path = react_dir / file
        if file_path.exists():
            print(f"[OK] {file}")
        else:
            print(f"[ERROR] Missing {file}")
            return False

    # Check node_modules
    node_modules = react_dir / "node_modules"
    if node_modules.exists():
        print("[OK] node_modules exists")
    else:
        print("[WARN] node_modules missing - will install on first run")

    return True

def test_websocket_dependencies():
    """Test WebSocket dependencies"""
    print("\nTesting WebSocket dependencies...")
    try:
        import websockets
        print("[OK] websockets module installed")
        return True
    except ImportError:
        print("[WARN] websockets module missing - will install on first run")
        return False

def test_duckbot_scripts():
    """Test DuckBot WebSocket and MCP scripts"""
    print("\nTesting DuckBot scripts...")

    scripts = [
        "simple_websocket_server.py",
        "start_mcp_server.py"
    ]

    for script in scripts:
        if os.path.exists(script):
            print(f"[OK] {script}")
        else:
            print(f"[ERROR] Missing {script}")
            return False

    return True

def test_config_files():
    """Test configuration files"""
    print("\nTesting configuration files...")

    config_files = [
        "config/startup_config.json",
        "config/ai_config.json",
        "config/ecosystem_config.yaml"
    ]

    for config in config_files:
        if os.path.exists(config):
            print(f"[OK] {config}")
        else:
            print(f"[WARN] Missing {config} - optional")

    return True

def test_launcher_syntax():
    """Test launcher batch file syntax"""
    print("\nTesting launcher syntax...")
    launcher = "START_ELECTRON_LAUNCHER.bat"

    if not os.path.exists(launcher):
        print(f"[ERROR] Launcher not found: {launcher}")
        return False

    # Basic syntax check by reading the file
    try:
        with open(launcher, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check for common syntax issues
        if '@echo off' in content:
            print("[OK] Batch file structure valid")
        else:
            print("[ERROR] Invalid batch file structure")
            return False

        # Check for key components
        key_components = [
            'node --version',
            'duckbot\\react-webui',
            'npm run electron:start',
            'simple_websocket_server.py'
        ]

        for component in key_components:
            if component in content:
                print(f"[OK] Found: {component}")
            else:
                print(f"[ERROR] Missing: {component}")
                return False

        return True

    except Exception as e:
        print(f"[ERROR] Could not read launcher: {e}")
        return False

def main():
    """Main validation function"""
    print("=" * 60)
    print("DUCKBOT ELECTRON LAUNCHER VALIDATION")
    print("=" * 60)

    # Change to script directory
    os.chdir(Path(__file__).parent)

    tests = [
        ("Node.js", test_nodejs),
        ("React WebUI", test_react_webui),
        ("WebSocket Dependencies", test_websocket_dependencies),
        ("DuckBot Scripts", test_duckbot_scripts),
        ("Configuration Files", test_config_files),
        ("Launcher Syntax", test_launcher_syntax)
    ]

    results = []
    for name, test_func in tests:
        print(f"\n{'='*20} {name} {'='*20}")
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"[ERROR] Test failed with exception: {e}")
            results.append((name, False))

    # Summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)

    passed = 0
    total = len(results)

    for name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{name:.<30} {status}")
        if result:
            passed += 1

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("[SUCCESS] All validation tests passed!")
        print("The START_ELECTRON_LAUNCHER.bat should work correctly.")
        return True
    else:
        print("[WARNING] Some tests failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)