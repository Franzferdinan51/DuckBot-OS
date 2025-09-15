#!/usr/bin/env python3
"""
Simple test script to verify DuckBot OS interface
"""
import os

def test_files():
    print("DuckBot OS Integration Test")
    print("=" * 50)
    
    # Check if the DuckBot OS file exists
    duckbot_os_file = "DuckBotOS-Complete.html"
    
    print(f"Current directory: {os.getcwd()}")
    print(f"Checking for: {duckbot_os_file}")
    
    if os.path.exists(duckbot_os_file):
        size = os.path.getsize(duckbot_os_file)
        print(f"[EMOJI] DuckBot OS file found: {size:,} bytes")
        
        # Test reading
        try:
            with open(duckbot_os_file, 'r', encoding='utf-8') as f:
                content = f.read()
            print(f"[EMOJI] File readable: {len(content):,} characters")
            
            # Check key components
            if "icons-grid" in content:
                print("[EMOJI] Desktop icons present")
            if "duckbot-3d-canvas" in content:
                print("[EMOJI] 3D Avatar present")
            if "apps: [" in content:
                print("[EMOJI] Apps defined")
            if "services" in content:
                print("[EMOJI] Services app present")
                
            return True
        except Exception as e:
            print(f"[EMOJI] Error reading file: {e}")
            return False
    else:
        print("[EMOJI] DuckBot OS file not found!")
        return False

def test_webui():
    print("\nWebUI Configuration Test")
    print("=" * 50)
    
    webui_file = os.path.join("duckbot", "webui.py")
    if os.path.exists(webui_file):
        with open(webui_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if "DuckBotOS-Complete.html" in content:
            print("[EMOJI] WebUI updated to serve DuckBot OS")
        else:
            print("[EMOJI] WebUI not updated")
            return False
            
        if "possible_paths" in content:
            print("[EMOJI] Path detection added")
        else:
            print("[EMOJI] Path detection missing")
            return False
            
        return True
    else:
        print("[EMOJI] WebUI file not found")
        return False

if __name__ == "__main__":
    file_ok = test_files()
    webui_ok = test_webui()
    
    print("\nSUMMARY")
    print("=" * 50)
    
    if file_ok and webui_ok:
        print("[EMOJI] DuckBot OS should work!")
        print("  Access: http://localhost:8787")
        print("  Classic: http://localhost:8787/classic")
        print("\nIf still showing old UI:")
        print("  1. Restart DuckBot server")
        print("  2. Clear browser cache")
        print("  3. Use Ctrl+F5 to refresh")
    else:
        print("[EMOJI] Issues found - may not work properly")