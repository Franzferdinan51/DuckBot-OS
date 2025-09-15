#!/usr/bin/env python3
"""
Test duckbot subdirectory modules
"""

import os
import sys

def test_duckbot_modules():
    """Test which duckbot modules can be imported"""

    duckbot_modules = [
        'duckbot.ai_router_gpt',
        'duckbot.charm_terminal_ui',
        'duckbot.enhanced_webui',
        'duckbot.webui_enhanced',
        'duckbot.webui_modern'
    ]

    working_modules = []
    failed_modules = []

    for module in duckbot_modules:
        try:
            __import__(module)
            working_modules.append(module)
            print(f"[OK] {module}")
        except Exception as e:
            failed_modules.append((module, str(e)))
            print(f"[FAIL] {module}: {e}")

    print(f"\nWorking duckbot modules: {len(working_modules)}")
    print(f"Failed duckbot modules: {len(failed_modules)}")

    return working_modules, failed_modules

if __name__ == "__main__":
    test_duckbot_modules()