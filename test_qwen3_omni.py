#!/usr/bin/env python3
"""
Quick test script for Qwen3-Omni integration
"""

import asyncio
import sys
import os
import time

# Add current directory to path
sys.path.append(os.getcwd())

from duckbot.core.qwen3_omni_integration import qwen3_omni_integration

async def test_qwen3_omni():
    """Test Qwen3-Omni integration"""
    print("=== QWEN3-OMNI INTEGRATION TEST ===")
    print()

    # Test 1: Import and status
    print("1. Testing integration import...")
    status = qwen3_omni_integration.get_status()
    print(f"   Status: {status}")
    print()

    # Test 2: Model loading
    print("2. Testing model loading...")
    if not status["available"]:
        print("   Loading model...")
        start_time = time.time()
        result = await qwen3_omni_integration.load_model()
        load_time = time.time() - start_time
        print(f"   Load result: {result}")
        print(f"   Load time: {load_time:.1f}s")

        if result:
            status = qwen3_omni_integration.get_status()
            print(f"   Updated status: {status}")
        else:
            print("   ❌ Failed to load model!")
            return
    else:
        print("   ✓ Model already loaded")
    print()

    # Test 3: Simple text generation
    print("3. Testing simple text generation...")
    try:
        start_time = time.time()
        result = await qwen3_omni_integration.generate_text("Hello! Please respond with just 'Hello, I am Qwen3-Omni!'")
        generation_time = time.time() - start_time

        print(f"   Response: {result.text}")
        print(f"   Confidence: {result.confidence:.2f}")
        print(f"   Processing time: {result.processing_time:.2f}s")
        print(f"   Usage: {result.usage}")
        print("   ✓ Text generation successful!")

    except Exception as e:
        print(f"   ❌ Text generation failed: {e}")
        import traceback
        traceback.print_exc()
    print()

    print("=== TEST COMPLETE ===")
    print("If all tests passed, the Qwen3-Omni integration is working correctly!")

if __name__ == "__main__":
    asyncio.run(test_qwen3_omni())