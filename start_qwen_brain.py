#!/usr/bin/env python3
"""
Qwen3-Omni AI Brain startup script
"""

import asyncio
import sys
import os
import time
import signal

# Add current directory to path
sys.path.append(os.getcwd())

from duckbot.core.qwen3_omni_integration import qwen3_omni_integration

async def start_qwen_brain():
    """Start the Qwen3-Omni AI Brain"""
    try:
        print('=== QWEN3-OMNI AI BRAIN STARTING ===')
        print(f'Model path: {qwen3_omni_integration.config.model_id}')
        device_attr = getattr(qwen3_omni_integration, 'device', 'auto')
        print(f'Device: {device_attr}')
        print('')

        print('Loading Qwen3-Omni model with Flash Attention 2...')
        start_time = time.time()
        result = await qwen3_omni_integration.load_model()
        load_time = time.time() - start_time

        if result:
            print(f'+ Qwen3-Omni model loaded successfully in {load_time:.1f}s!')
            status = qwen3_omni_integration.get_status()
            print(f'  - Available: {status["available"]}')
            print(f'  - Device: {status["device"]}')
            print(f'  - Flash Attention: {status["flash_attention"]}')
            print(f'  - Load Time: {status.get("load_time", "N/A")}s')
            memory_info = status.get("memory_available", {})
            if memory_info:
                print(f'  - Memory: {memory_info}')
            else:
                print('  - Memory: Not available')
        else:
            print('X Failed to load Qwen3-Omni model!')
            return

        print('')
        print('QWEN3-OMNI AI BRAIN IS READY!')
        print('Say "hey duckbot" to activate voice assistant')
        print('Model is loaded and ready for multimodal processing')
        print('')
        print('Press Ctrl+C to exit.')
        print('')

        # Keep the service running with status updates
        count = 0
        while True:
            await asyncio.sleep(60)  # Status update every minute
            count += 1
            if count % 5 == 0:  # Every 5 minutes
                print(f'  [STATUS] Qwen3-Omni AI Brain running - Uptime: {count} minutes')

    except KeyboardInterrupt:
        print('\nQwen3-Omni AI Brain stopped by user.')
    except Exception as e:
        print(f'Error starting Qwen3-Omni AI Brain: {e}')
        import traceback
        traceback.print_exc()

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print(f'\nQwen3-Omni AI Brain received signal {signum}, shutting down...')
    sys.exit(0)

if __name__ == '__main__':
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Start the brain
    asyncio.run(start_qwen_brain())