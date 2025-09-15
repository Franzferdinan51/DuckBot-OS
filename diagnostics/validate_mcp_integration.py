#!/usr/bin/env python3
"""
Validation script for DuckBot MCP Integration
"""

import sys
import os
import asyncio
from pathlib import Path

def test_python_environment():
    """Test Python environment and dependencies"""
    print("=== Testing Python Environment ===")

    # Test Python version
    print(f"Python Version: {sys.version}")

    # Test key dependencies
    dependencies = [
        'fastapi', 'uvicorn', 'websockets', 'psutil',
        'httpx', 'aiohttp', 'asyncio'
    ]

    for dep in dependencies:
        try:
            __import__(dep)
            print(f"[OK] {dep}: Available")
        except ImportError:
            print(f"[FAIL] {dep}: Missing")

    return True

def test_duckbot_modules():
    """Test DuckBot module imports"""
    print("\n=== Testing DuckBot Modules ===")

    modules = [
        'duckbot.mcp_server',
        'duckbot.enhanced_webui',
        'duckbot.ai_router_gpt',
        'duckbot.server_manager'
    ]

    success_count = 0
    for module in modules:
        try:
            __import__(module)
            print(f"[OK] {module}: OK")
            success_count += 1
        except Exception as e:
            print(f"[FAIL] {module}: Error - {e}")

    print(f"\nModule Success Rate: {success_count}/{len(modules)} ({success_count/len(modules)*100:.1f}%)")
    return success_count == len(modules)

async def test_mcp_server():
    """Test MCP Server functionality"""
    print("\n=== Testing MCP Server ===")

    try:
        from duckbot.mcp_server import DuckBotMCPServer, MCP_AVAILABLE

        print(f"MCP Available: {MCP_AVAILABLE}")

        # Create server instance
        server = DuckBotMCPServer()
        print("[OK] MCP Server instance created")

        # Test server attributes
        print(f"[OK] Server host: {getattr(server, 'host', 'N/A')}")
        print(f"[OK] Server port: {getattr(server, 'port', 'N/A')}")

        return True
    except Exception as e:
        print(f"[FAIL] MCP Server test failed: {e}")
        return False

async def test_enhanced_webui():
    """Test Enhanced WebUI with MCP integration"""
    print("\n=== Testing Enhanced WebUI ===")

    try:
        from duckbot.enhanced_webui import EnhancedWebUI

        # Create WebUI instance
        webui = EnhancedWebUI()
        print("[OK] Enhanced WebUI instance created")

        # Test MCP integration
        print(f"[OK] MCP Available: {webui.mcp_available}")
        print(f"[OK] MCP Server Status: {webui.mcp_server_status}")
        print(f"[OK] MCP Tools Count: {len(webui.mcp_tools)}")

        # Test MCP status API
        status = await webui.get_mcp_status()
        print("[OK] MCP Status API working")
        print(f"   Status: {status.get('status', 'N/A')}")
        print(f"   Docker Status: {status.get('docker_status', 'N/A')}")

        return True
    except Exception as e:
        print(f"[FAIL] Enhanced WebUI test failed: {e}")
        return False

def test_files_exist():
    """Test required files exist"""
    print("\n=== Testing File Structure ===")

    required_files = [
        'START_ENHANCED_DUCKBOT.bat',
        'duckbot/mcp_server.py',
        'duckbot/enhanced_webui.py',
        'duckbot/ai_router_gpt.py',
        'requirements.txt',
        'MCP_README.md',
        'Dockerfile.mcp',
        'docker-compose.mcp.yml',
        'duckbot/config/mcp_config.json'
    ]

    success_count = 0
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"[OK] {file_path}: Exists")
            success_count += 1
        else:
            print(f"[FAIL] {file_path}: Missing")

    print(f"\nFile Success Rate: {success_count}/{len(required_files)} ({success_count/len(required_files)*100:.1f}%)")
    return success_count == len(required_files)

def test_launcher_syntax():
    """Test launcher batch file syntax"""
    print("\n=== Testing Launcher Syntax ===")

    launcher_file = Path('START_ENHANCED_DUCKBOT.bat')
    if not launcher_file.exists():
        print("[EMOJI] Launcher file not found")
        return False

    try:
        content = launcher_file.read_text(encoding='utf-8')

        # Check for key sections
        checks = [
            ('main_menu', ':main_menu'),
            ('mcp_options', ':mcp_options'),
            ('ultimate_mode', ':ultimate_complete_mode'),
            ('webui_mode', ':enhanced_webui_mode'),
            ('python_check', 'python --version'),
            ('mcp_integration', 'MCP (MODEL CONTEXT PROTOCOL)')
        ]

        success_count = 0
        for name, pattern in checks:
            if pattern in content:
                print(f"[OK] {name}: Found")
                success_count += 1
            else:
                print(f"[FAIL] {name}: Missing")

        print(f"\nSyntax Success Rate: {success_count}/{len(checks)} ({success_count/len(checks)*100:.1f}%)")
        return success_count == len(checks)

    except Exception as e:
        print(f"[FAIL] Launcher syntax test failed: {e}")
        return False

async def main():
    """Main validation function"""
    print("DuckBot MCP Integration Validation")
    print("=" * 50)

    tests = [
        ("Python Environment", test_python_environment),
        ("File Structure", test_files_exist),
        ("Launcher Syntax", test_launcher_syntax),
        ("DuckBot Modules", test_duckbot_modules),
        ("MCP Server", test_mcp_server),
        ("Enhanced WebUI", test_enhanced_webui),
    ]

    results = []
    for name, test_func in tests:
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"[FAIL] {name} test crashed: {e}")
            results.append((name, False))

    print("\n" + "=" * 50)
    print("VALIDATION SUMMARY")
    print("=" * 50)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status}: {name}")

    print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")

    if passed == total:
        print("\nSUCCESS: All MCP integration tests passed!")
        print("\nThe enhanced startup script should work with:")
        print("  • Option 2: Enhanced WebUI Dashboard")
        print("  • Option M: MCP Options Menu")
        print("  • Option 1: Ultimate Complete Mode")
        print("\nRun: START_ENHANCED_DUCKBOT.bat")
    else:
        print(f"\nWARNING: {total - passed} test(s) failed")
        print("Some features may not work correctly")

    return passed == total

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)