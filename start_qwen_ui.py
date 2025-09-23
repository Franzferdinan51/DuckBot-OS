#!/usr/bin/env python3
"""
Qwen3-Omni UI startup script
"""

import subprocess
import sys
import os
import time

def start_ui():
    """Start the Qwen3-Omni UI"""
    try:
        print('Starting Qwen3-Omni UI...')

        # Change to UI directory
        ui_dir = os.path.join(os.getcwd(), 'qwen3-omni-ui')

        if not os.path.exists(ui_dir):
            print(f'Qwen3-Omni-UI directory not found at: {ui_dir}')
            return False

        os.chdir(ui_dir)

        # Check if node_modules exists
        if not os.path.exists('node_modules'):
            print('Installing UI dependencies...')
            result = subprocess.run(['npm', 'install'], shell=True, capture_output=True, text=True)
            if result.returncode != 0:
                print(f'Failed to install UI dependencies: {result.stderr}')
                return False

        print('Starting Qwen3-Omni-UI development server...')
        print('This will open in your default browser...')

        # Start the UI
        subprocess.run(['npm', 'run', 'dev'], shell=True)

    except KeyboardInterrupt:
        print('\n🛑 Qwen3-Omni UI stopped by user.')
    except Exception as e:
        print(f'Error starting Qwen3-Omni UI: {e}')
        return False

    return True

if __name__ == '__main__':
    start_ui()