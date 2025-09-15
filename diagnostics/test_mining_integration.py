#!/usr/bin/env python3
"""
Test script for DuckBot Mining Manager
Verifies that all mining features are working correctly
"""

import asyncio
import sys
import os
from pathlib import Path

# Fix Windows console Unicode handling
if os.name == 'nt':
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Add the duckbot module to the path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from duckbot.integrations.mining_manager import MiningManager, MiningSoftware
    MINING_AVAILABLE = True
    print("[OK] Mining manager available")
except ImportError as e:
    MINING_AVAILABLE = False
    print(f"[FAIL] Mining manager not available: {e}")

async def test_mining_integration():
    """Test mining integration functionality"""
    if not MINING_AVAILABLE:
        print("[WARN] Skipping mining tests - not available")
        return False

    try:
        # Initialize mining manager
        mining_manager = MiningManager()
        print("[OK] Mining manager initialized")

        # Test getting status
        status = await mining_manager.get_mining_status()
        print(f"[OK] Mining status retrieved: {status}")

        # Test getting profitability data
        profitability = await mining_manager.get_profitability_data()
        print(f"[OK] Profitability data retrieved: {bool(profitability)}")

        # Test getting capabilities/status
        capabilities = await mining_manager.get_mining_status()
        print(f"[OK] Mining capabilities/status: {capabilities}")

        return True

    except Exception as e:
        print(f"[FAIL] Mining integration test failed: {e}")
        return False

async def main():
    """Main test function"""
    print("=" * 60)
    print("DuckBot Mining Integration Test")
    print("=" * 60)

    success = await test_mining_integration()

    print("\n" + "=" * 60)
    if success:
        print("[OK] All mining integration tests passed!")
    else:
        print("[FAIL] Some mining integration tests failed")
    print("=" * 60)

    return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)