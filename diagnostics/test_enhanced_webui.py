#!/usr/bin/env python3
"""
Test script for Enhanced DuckBot WebUI
"""

import asyncio
import uvicorn
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from duckbot.webui_enhanced import app, ACCESS_TOKEN

def main():
    print("[LAUNCH] Starting DuckBot Enhanced WebUI Test...")
    print(f"[EMOJI] Access Token: {ACCESS_TOKEN}")
    print(f"[GLOBE] Dashboard URL: http://localhost:8787/dashboard?token={ACCESS_TOKEN}")
    print(f"[CHART] Health Check: http://localhost:8787/api/health")
    print(f"[EMOJI] WebSocket: ws://localhost:8787/ws?token={ACCESS_TOKEN}")
    print()
    print("[EMOJI] Enhanced Features:")
    print("  • Real-time WebSocket monitoring")
    print("  • Modern responsive UI/UX")
    print("  • Enhanced service management")
    print("  • Advanced chat interface")
    print("  • System metrics dashboard")
    print("  • Dark/light theme support")
    print()
    print("Press Ctrl+C to stop...")
    
    # Run the enhanced WebUI
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8787,
        log_level="info",
        access_log=True
    )

if __name__ == "__main__":
    main()