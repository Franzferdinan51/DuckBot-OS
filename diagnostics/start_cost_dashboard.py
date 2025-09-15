#!/usr/bin/env python3
"""
DuckBot Cost Dashboard Launcher
Starts the Flask cost tracking dashboard on port 8080
"""

import os
import sys
import threading
import webbrowser
from pathlib import Path

# Add duckbot to path
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

try:
    from duckbot.web_dashboard import run_dashboard
    print("[EMOJI] DuckBot Cost Dashboard Launcher")
    print("[CHART] Starting cost tracking web dashboard...")
    print("[GLOBE] Dashboard will be available at: http://localhost:8080")
    print("[EMOJI] Open this URL in your browser to view cost analytics")
    print()
    
    def open_browser():
        """Open browser after short delay"""
        import time
        time.sleep(3)
        try:
            webbrowser.open('http://localhost:8080')
            print("[GLOBE] Opened dashboard in browser")
        except:
            print("[EMOJI] Please manually open: http://localhost:8080")
    
    # Start browser opener in background
    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()
    
    # Start dashboard
    run_dashboard(host='0.0.0.0', port=8080, debug=False)
    
except ImportError as e:
    print(f"[FAIL] Error importing cost dashboard: {e}")
    print("[EMOJI] Make sure the duckbot package is properly installed")
    print("[DIR] Current directory should contain the 'duckbot' folder")
    sys.exit(1)
except KeyboardInterrupt:
    print("\n[EMOJI] Cost dashboard stopped by user")
    sys.exit(0)
except Exception as e:
    print(f"[FAIL] Error starting cost dashboard: {e}")
    sys.exit(1)