#!/usr/bin/env python3
"""
DuckBot Enhanced v4.2 Setup Verification Script
Verifies all components are properly installed
"""

import sys
import subprocess
from pathlib import Path

def check_python():
    """Check Python version"""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"✓ Python {version.major}.{version.minor}.{version.micro} - OK")
        return True
    else:
        print(f"✗ Python {version.major}.{version.minor}.{version.micro} - Need 3.8+")
        return False

def check_go():
    """Check Go installation"""
    try:
        result = subprocess.run(['go', 'version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ {result.stdout.strip()} - OK")
            return True
    except FileNotFoundError:
        pass
    print("✗ Go not found - Required for Charm tools")
    return False

def check_charm_tools():
    """Check Charm tools installation"""
    tools = ['gum', 'glow', 'mods', 'skate', 'crush', 'charm', 'freeze', 'vhs']
    available = []
    
    go_bin = Path.home() / 'go' / 'bin'
    
    for tool in tools:
        tool_path = go_bin / f"{tool}.exe"  # Windows
        if not tool_path.exists():
            tool_path = go_bin / tool  # Linux/Mac
        
        if tool_path.exists():
            available.append(tool)
            print(f"✓ {tool} - Available")
        else:
            print(f"✗ {tool} - Missing")
    
    print(f"\nCharm Tools: {len(available)}/{len(tools)} available")
    return len(available) == len(tools)

def check_duckbot_integration():
    """Check DuckBot Charm integration"""
    try:
        sys.path.append('.')
        from duckbot.charm_tools_integration import get_charm_status
        status = get_charm_status()
        print(f"✓ DuckBot Charm Integration: {status['total_tools']} tools integrated")
        return status['total_tools'] > 0
    except ImportError:
        print("✗ DuckBot Charm Integration - Import failed")
        return False
    except Exception as e:
        print(f"✗ DuckBot Charm Integration - Error: {e}")
        return False

def main():
    print("DuckBot Enhanced v4.2 - Setup Verification")
    print("=" * 50)
    
    checks = [
        check_python(),
        check_go(),
        check_charm_tools(),
        check_duckbot_integration()
    ]
    
    passed = sum(checks)
    total = len(checks)
    
    print("\n" + "=" * 50)
    print(f"Setup Status: {passed}/{total} checks passed")
    
    if passed == total:
        print("🎉 All systems ready! Run START_ENHANCED_DUCKBOT.bat to begin.")
    else:
        print("⚠ Some components need attention. Check the output above.")
        print("📖 See README.md for complete setup instructions.")

if __name__ == "__main__":
    main()
