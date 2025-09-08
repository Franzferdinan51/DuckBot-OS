#!/usr/bin/env python3
"""
Test script to verify DuckBot OS interface is working properly
"""
import os
import sys

def test_duckbot_os_file():
    print("🦆 Testing DuckBot OS Interface")
    print("=" * 50)
    
    # Check if the DuckBot OS file exists
    possible_paths = [
        "DuckBotOS-Complete.html",
        os.path.join(os.getcwd(), "DuckBotOS-Complete.html"),
        os.path.join(os.path.dirname(__file__), "DuckBotOS-Complete.html")
    ]
    
    print(f"Current working directory: {os.getcwd()}")
    print(f"Script directory: {os.path.dirname(__file__)}")
    print()
    
    found_path = None
    for i, path in enumerate(possible_paths, 1):
        exists = os.path.exists(path)
        print(f"{i}. Checking: {path}")
        print(f"   Exists: {'✅ YES' if exists else '❌ NO'}")
        if exists:
            size = os.path.getsize(path)
            print(f"   Size: {size:,} bytes")
            found_path = path
        print()
    
    if found_path:
        print(f"✅ DuckBot OS file found at: {found_path}")
        
        # Test reading the file
        try:
            with open(found_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            print(f"✅ File readable: {len(content):,} characters")
            
            # Check for key components
            checks = [
                ("Desktop Icons Grid", "icons-grid" in content),
                ("3D Avatar Canvas", "duckbot-3d-canvas" in content),
                ("AI Chat Interface", "command-form" in content),
                ("Window Management", "windows-container" in content),
                ("App Definitions", "apps: [" in content),
                ("API Integration", "apiCall" in content),
                ("Three.js Integration", 'three' in content.lower()),
                ("Task Runner", 'task-runner' in content),
                ("Service Management", 'services' in content),
                ("Cost Dashboard", 'cost-dashboard' in content),
            ]
            
            print("\n🔍 Component Check:")
            for name, check in checks:
                status = "✅" if check else "❌"
                print(f"   {status} {name}")
            
            all_good = all(check for _, check in checks)
            print(f"\n{'✅ All components present!' if all_good else '⚠️ Some components missing'}")
            
        except Exception as e:
            print(f"❌ Error reading file: {e}")
            return False
    else:
        print("❌ DuckBot OS file not found!")
        return False
    
    return found_path is not None

def test_webui_routing():
    print("\n🔧 Testing WebUI Routing")
    print("=" * 50)
    
    webui_path = os.path.join("duckbot", "webui.py")
    if not os.path.exists(webui_path):
        print(f"❌ WebUI file not found: {webui_path}")
        return False
    
    try:
        with open(webui_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for the new routing code
        checks = [
            ("Home Route Modified", '@app.get("/", response_class=HTMLResponse)' in content),
            ("DuckBot OS Loading", 'DuckBotOS-Complete.html' in content),
            ("Classic Route Added", '@app.get("/classic"' in content),
            ("Path Detection", 'possible_paths' in content),
            ("Error Handling", 'DUCKBOT OS ERROR' in content),
        ]
        
        print("🔍 WebUI Route Check:")
        for name, check in checks:
            status = "✅" if check else "❌"
            print(f"   {status} {name}")
            
        all_good = all(check for _, check in checks)
        print(f"\n{'✅ WebUI routing updated correctly!' if all_good else '⚠️ WebUI routing needs fixing'}")
        return all_good
        
    except Exception as e:
        print(f"❌ Error reading WebUI file: {e}")
        return False

if __name__ == "__main__":
    print("🦆 DuckBot OS Integration Test")
    print("=" * 60)
    
    file_test = test_duckbot_os_file()
    route_test = test_webui_routing()
    
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    
    if file_test and route_test:
        print("✅ DuckBot OS should work correctly!")
        print("   Try accessing: http://localhost:8787")
        print("   Classic WebUI: http://localhost:8787/classic")
    else:
        print("❌ Issues detected - DuckBot OS may not work properly")
        if not file_test:
            print("   - DuckBot OS file missing or corrupted")
        if not route_test:
            print("   - WebUI routing not properly configured")
    
    print("\n💡 If you're still seeing the old WebUI:")
    print("   1. Restart the DuckBot server completely")
    print("   2. Clear your browser cache") 
    print("   3. Check the console output for error messages")
    print("   4. Use Ctrl+F5 to force refresh the page")