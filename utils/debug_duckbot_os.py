#!/usr/bin/env python3
"""
Debug script to test DuckBot OS loading
"""
import os

def debug_duckbot_os():
    print("DuckBot OS Debug")
    print("=" * 50)
    
    current_dir = os.getcwd()
    print(f"Current directory: {current_dir}")
    print()
    
    # Test the same paths the WebUI uses
    possible_paths = [
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "DuckBotOS-Complete.html"),
        os.path.join(os.getcwd(), "DuckBotOS-Complete.html"),
        "DuckBotOS-Complete.html"
    ]
    
    print("Checking DuckBot OS file locations:")
    for i, path in enumerate(possible_paths, 1):
        exists = os.path.exists(path)
        print(f"{i}. {path}")
        print(f"   Exists: {'YES' if exists else 'NO'}")
        if exists:
            try:
                size = os.path.getsize(path)
                print(f"   Size: {size:,} bytes")
                
                # Test reading first 100 chars
                with open(path, 'r', encoding='utf-8') as f:
                    first_chars = f.read(100)
                print(f"   Readable: YES (starts with: {repr(first_chars[:50])}...)")
                
                # Test for key content
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                has_desktop = "desktop" in content.lower()
                has_apps = "apps: [" in content
                has_avatar = "duckbot-3d" in content
                
                print(f"   Has desktop: {'YES' if has_desktop else 'NO'}")
                print(f"   Has apps: {'YES' if has_apps else 'NO'}")
                print(f"   Has avatar: {'YES' if has_avatar else 'NO'}")
                
            except Exception as e:
                print(f"   Error reading: {e}")
        print()
    
    # Check what files ARE in the current directory
    print("Files in current directory:")
    try:
        files = [f for f in os.listdir('.') if f.endswith('.html')]
        for file in files:
            print(f"  - {file}")
        if not files:
            print("  (No .html files found)")
    except Exception as e:
        print(f"  Error listing files: {e}")

if __name__ == "__main__":
    debug_duckbot_os()