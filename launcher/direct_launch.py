#!/usr/bin/env python3
"""
Direct launcher for DuckBot WebUI with AI Management
Bypasses batch file complexity and launches directly
"""

import os
import sys
import subprocess
import time
import threading
import webbrowser

def main():
    print("=" * 70)
    try:
        print("[DUCKBOT] DuckBot Direct Launcher - WebUI + AI Management")
    except UnicodeEncodeError:
        print("[DUCKBOT] DuckBot Direct Launcher - WebUI + AI Management")
    print("=" * 70)
    
    # Change to DuckBot directory
    os.chdir(r"C:\Users\Duck1\Desktop\DuckBotComplete")
    try:
        print(f"[FILES] Working directory: {os.getcwd()}")
    except UnicodeEncodeError:
        print(f"[DIR] Working directory: {os.getcwd()}")
    
    # Set up environment
    env = os.environ.copy()
    env["PYTHONPATH"] = os.getcwd()
    
    try:
        print("[BRAIN] Starting AI Ecosystem Manager in background...")
    except UnicodeEncodeError:
        print("[AI] Starting AI Ecosystem Manager in background...")
    
    # Start AI ecosystem in background
    ai_process = subprocess.Popen([
        sys.executable, "start_ai_ecosystem.py"
    ], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    # Give AI manager time to start
    time.sleep(3)
    
    try:
        print("[CLOUD] Starting WebUI Server...")
    except UnicodeEncodeError:
        print("[WEBUI] Starting WebUI Server...")
    
    # Start WebUI
    webui_process = subprocess.Popen([
        sys.executable, "-m", "duckbot.webui"
    ], env=env)
    
    # Wait a bit and check if processes are running
    time.sleep(5)
    
    if ai_process.poll() is None:
        try:
            print("[OK] AI Ecosystem Manager: Running")
        except UnicodeEncodeError:
            print("[OK] AI Ecosystem Manager: Running")
    else:
        try:
            print("[ERROR] AI Ecosystem Manager: Failed to start")
        except UnicodeEncodeError:
            print("[ERROR] AI Ecosystem Manager: Failed to start")
        stdout, stderr = ai_process.communicate()
        if stderr:
            print(f"   Error: {stderr[:500]}")
    
    if webui_process.poll() is None:
        try:
            print("[OK] WebUI Server: Running")
            print("[CLOUD] WebUI should be accessible at: http://localhost:8787")
            print("[EMOJI] Check console output above for access token")
        except UnicodeEncodeError:
            print("[OK] WebUI Server: Running")
            print("[URL] WebUI should be accessible at: http://localhost:8787")
            print("[TOKEN] Check console output above for access token")
    else:
        try:
            print("[ERROR] WebUI Server: Failed to start")
        except UnicodeEncodeError:
            print("[ERROR] WebUI Server: Failed to start")
    
    print("\n" + "=" * 70)
    try:
        print("[START] DuckBot is starting up!")
        print("[EMOJI] Browser should open automatically with WebUI")
        print("⏹[EMOJI]  Press Ctrl+C to stop both services")
    except UnicodeEncodeError:
        print("[STARTUP] DuckBot is starting up!")
        print("[BROWSER] Browser should open automatically with WebUI")
        print("[STOP] Press Ctrl+C to stop both services")
    print("=" * 70)
    
    try:
        # Keep running until interrupted
        while True:
            time.sleep(10)
            
            # Check if processes are still alive
            if ai_process.poll() is not None and webui_process.poll() is not None:
                print("[WARNING]  Both services have stopped")
                break
                
    except KeyboardInterrupt:
        print("\n[STOP] Shutting down DuckBot...")
        
        # Terminate processes
        if ai_process.poll() is None:
            ai_process.terminate()
            try:
                ai_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                ai_process.kill()
                
        if webui_process.poll() is None:
            webui_process.terminate()
            try:
                webui_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                webui_process.kill()
        
        print("[OK] DuckBot shutdown complete")

if __name__ == "__main__":
    main()