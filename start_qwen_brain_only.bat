@echo off
echo Starting Qwen3-Omni Brain only...
echo.

cd /d "%~dp0"

echo Loading Qwen3-Omni model...
python -c "
import asyncio
import sys
import os
sys.path.append(os.getcwd())

from duckbot.core.qwen3_omni_integration import qwen3_omni_integration

async def start_brain():
    try:
        print('=== QWEN3-OMNI AI BRAIN ===')
        print(f'Model path: {qwen3_omni_integration.config.model_id}')
        print('')

        print('Loading model...')
        start_time = __import__('time').time()
        result = await qwen3_omni_integration.load_model()
        load_time = __import__('time').time() - start_time

        if result:
            print(f'✓ Model loaded successfully in {load_time:.1f}s!')
            status = qwen3_omni_integration.get_status()
            print(f'Device: {status[\"device\"]}')
            print(f'Available: {status[\"available\"]}')
            print('')
            print('Qwen3-Omni AI Brain is ready!')
            print('Press Ctrl+C to exit.')

            # Keep running
            count = 0
            while True:
                await asyncio.sleep(60)
                count += 1
                if count % 5 == 0:
                    print(f'[STATUS] Running for {count} minutes')
        else:
            print('❌ Failed to load model!')

    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()

try:
    asyncio.run(start_brain())
except KeyboardInterrupt:
    print('\\nQwen3-Omni AI Brain stopped.')
"