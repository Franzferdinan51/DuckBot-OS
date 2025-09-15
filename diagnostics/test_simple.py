#!/usr/bin/env python3
"""
Simple DuckBot feature test (Unicode-safe)
"""
import sys
import subprocess

def test_imports():
    """Test critical imports"""
    print("\n[TESTING] Critical imports...")
    
    tests = [
        ("Service Detector", "from duckbot.service_detector import ServiceDetector; print('[PASS] Service detector')"),
        ("WebUI", "from duckbot.webui import app; print('[PASS] WebUI')"),
        ("Server Manager", "from duckbot.server_manager import server_manager; print('[PASS] Server manager')"),
        ("AI Router", "from duckbot.ai_router_gpt import route_task; print('[PASS] AI router')"),
    ]
    
    passed = 0
    for name, test_code in tests:
        try:
            result = subprocess.run([sys.executable, '-c', test_code], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print(f"[PASS] {name}")
                passed += 1
            else:
                print(f"[FAIL] {name}: {result.stderr.strip()[:100]}")
        except Exception as e:
            print(f"[FAIL] {name}: {str(e)[:100]}")
    
    print(f"[IMPORTS] {passed}/{len(tests)} passed")
    return passed == len(tests)

def test_server_status():
    """Test server management"""
    print("\n[TESTING] Server management...")
    
    try:
        from duckbot.server_manager import server_manager
        status = server_manager.get_all_service_status()
        
        running = 0
        for name, info in status.items():
            state = info.status.value
            port = f":{info.port}" if info.port else ""
            print(f"[STATUS] {name}{port} - {state}")
            if state == "running":
                running += 1
        
        print(f"[SERVERS] {running}/{len(status)} services running")
        return True
    except Exception as e:
        print(f"[FAIL] Server management: {str(e)[:100]}")
        return False

def test_ai_routing():
    """Test AI model routing"""
    print("\n[TESTING] AI routing...")
    
    try:
        from duckbot.ai_router_gpt import get_lm_studio_model, TIERS
        
        # Test model detection
        model = get_lm_studio_model()
        print(f"[MODEL] LM Studio: {model}")
        
        # Test tiers
        free_models = [t['model'] for t in TIERS.values() if 'free' in t.get('model', '')]
        print(f"[TIERS] {len(TIERS)} tiers, {len(free_models)} free models")
        
        return True
    except Exception as e:
        print(f"[FAIL] AI routing: {str(e)[:100]}")
        return False

def test_dependencies():
    """Test external dependencies"""
    print("\n[TESTING] Dependencies...")
    
    deps = [
        ("Node.js", ["node", "--version"]),
        ("n8n", ["n8n", "--version"]),
    ]
    
    passed = 0
    for name, command in deps:
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                version = result.stdout.strip()
                print(f"[PASS] {name}: {version}")
                passed += 1
            else:
                print(f"[FAIL] {name}: Not found")
        except Exception as e:
            print(f"[FAIL] {name}: {str(e)[:50]}")
    
    print(f"[DEPS] {passed}/{len(deps)} dependencies available")
    return passed >= 1  # At least one should work

def main():
    print("[START] DuckBot Complete Feature Testing")
    print(f"[DIR] Working Directory: {sys.path[0]}")
    
    results = {
        'imports': test_imports(),
        'servers': test_server_status(),
        'ai_routing': test_ai_routing(),
        'dependencies': test_dependencies(),
    }
    
    passed = sum(results.values())
    total = len(results)
    
    print(f"\n[SUMMARY] {passed}/{total} test categories passed")
    
    for category, result in results.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"  {status} {category.title()}")
    
    if passed == total:
        print("\n[SUCCESS] All tests passed - System ready!")
        return 0
    else:
        print(f"\n[PARTIAL] {passed}/{total} categories working")
        return 1

if __name__ == "__main__":
    sys.exit(main())