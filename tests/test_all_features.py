#!/usr/bin/env python3
"""
Test all SETUP_AND_START.bat features programmatically
"""
import sys
import time
import subprocess
import requests
from pathlib import Path
import json

# Setup Unicode encoding
import os
os.environ['PYTHONIOENCODING'] = 'utf-8'

def test_section(name):
    print(f"\n{'='*50}")
    print(f"TESTING: {name}")
    print(f"{'='*50}")

def test_imports():
    """Test all critical imports like the batch file does"""
    test_section("CRITICAL IMPORTS")
    
    tests = [
        ("Service Detector", "from duckbot.service_detector import ServiceDetector; print('[PASS] Service detector works')"),
        ("AI Ecosystem", "import start_ai_ecosystem; print('[PASS] AI ecosystem import works')"),
        ("WebUI", "from duckbot.webui import app; print('[PASS] WebUI import works')"),
        ("Server Manager", "from duckbot.server_manager import server_manager; print('[PASS] Server manager works')"),
        ("AI Router", "from duckbot.ai_router_gpt import route_task; print('[PASS] AI router works')"),
        ("Qwen Integration", "from duckbot.qwen_agent_integration import is_qwen_agent_available; print(f'[INFO] Qwen-Agent available: {is_qwen_agent_available()}')"),
    ]
    
    results = {}
    for name, test_code in tests:
        try:
            result = subprocess.run([sys.executable, '-c', test_code], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print(f"✅ {name}: {result.stdout.strip()}")
                results[name] = True
            else:
                print(f"❌ {name}: {result.stderr.strip()}")
                results[name] = False
        except Exception as e:
            print(f"❌ {name}: {str(e)}")
            results[name] = False
    
    return results

def test_service_detection():
    """Test service detection system"""
    test_section("SERVICE DETECTION")
    
    try:
        from duckbot.service_detector import ServiceDetector
        detector = ServiceDetector()
        recommendations = detector.get_startup_recommendations()
        
        print('[SCAN] Service detection results:')
        for service_name, rec in recommendations.items():
            if not rec['can_start']:
                print(f'  ✅ {service_name}: {rec["reason"]}')
            else:
                print(f'  ⭕ {service_name}: Available to start')
        return True
    except Exception as e:
        print(f"❌ Service detection failed: {e}")
        return False

def test_server_management():
    """Test server management system"""
    test_section("SERVER MANAGEMENT")
    
    try:
        from duckbot.server_manager import server_manager
        
        # Test status
        print("[STATUS] Getting all service status...")
        status = server_manager.get_all_service_status()
        for name, info in status.items():
            port_info = f":{info.port}" if info.port else ""
            print(f"  • {info.display_name}{port_info} - {info.status.value}")
        
        # Test server management tools (if available)
        from duckbot.qwen_agent_integration import get_qwen_agent_capabilities
        caps = get_qwen_agent_capabilities()
        print(f"[QWEN-AGENT] Server management tools: {caps['tools']}")
        
        return True
    except Exception as e:
        print(f"❌ Server management failed: {e}")
        return False

def test_ai_routing():
    """Test AI routing and model selection"""
    test_section("AI ROUTING & MODEL SELECTION")
    
    try:
        from duckbot.ai_router_gpt import get_lm_studio_model, TIERS, _select_best_available_model
        
        # Test LM Studio detection
        print("[LM-STUDIO] Testing model detection...")
        detected_model = get_lm_studio_model()
        print(f"[LM-STUDIO] Detected model: {detected_model}")
        
        # Test tier configuration
        print(f"[TIERS] Available AI tiers: {list(TIERS.keys())}")
        free_models = [t['model'] for t in TIERS.values() if 'free' in t.get('model', '')]
        print(f"[FREE-MODELS] Free models: {free_models[:3]}")
        
        # Test dynamic model selection
        available_models = ['qwen/qwen3-coder-30b', 'bartowski/nvidia-llama-3.3-nemotron', 'google/gemma-3-12b']
        tasks = [
            {'kind': 'reasoning', 'prompt': 'Complex analysis'},
            {'kind': 'code', 'prompt': 'Write a function'},
            {'kind': 'status', 'prompt': 'Quick check'},
        ]
        
        for task in tasks:
            selected = _select_best_available_model(available_models, task)
            print(f"[SELECTION] {task['kind']} task → {selected}")
        
        return True
    except Exception as e:
        print(f"❌ AI routing failed: {e}")
        return False

def test_webui_startup():
    """Test WebUI startup and basic functionality"""
    test_section("WEBUI FUNCTIONALITY")
    
    try:
        import threading
        import time
        from duckbot.webui import app, WEBUI_TOKEN
        import uvicorn
        
        # Start WebUI in background thread
        def start_webui():
            uvicorn.run(app, host='127.0.0.1', port=8790, log_level='error')
        
        print("[WEBUI] Starting WebUI server...")
        webui_thread = threading.Thread(target=start_webui, daemon=True)
        webui_thread.start()
        time.sleep(4)  # Give server time to start
        
        # Test endpoints
        headers = {'Authorization': f'Bearer {WEBUI_TOKEN}'}
        base_url = 'http://127.0.0.1:8790'
        
        tests = [
            ('Health Check', '/healthz', 'GET', None),
            ('Server Status', '/servers/status', 'GET', headers),
            ('Model Detection', '/models/available', 'GET', headers),
        ]
        
        results = {}
        for test_name, endpoint, method, test_headers in tests:
            try:
                if method == 'GET':
                    response = requests.get(f"{base_url}{endpoint}", headers=test_headers, timeout=5)
                else:
                    response = requests.post(f"{base_url}{endpoint}", headers=test_headers, timeout=5)
                
                print(f"  ✅ {test_name}: {response.status_code}")
                results[test_name] = response.status_code < 400
            except Exception as e:
                print(f"  ❌ {test_name}: {str(e)}")
                results[test_name] = False
        
        print(f"[WEBUI-TOKEN] Access token: {WEBUI_TOKEN[:16]}...")
        return all(results.values())
        
    except Exception as e:
        print(f"❌ WebUI test failed: {e}")
        return False

def test_external_dependencies():
    """Test external dependencies like n8n"""
    test_section("EXTERNAL DEPENDENCIES")
    
    dependencies = [
        ("Node.js", ["node", "--version"]),
        ("npm", ["npm", "--version"]),
        ("n8n", ["n8n", "--version"]),
        ("Python", [sys.executable, "--version"]),
    ]
    
    results = {}
    for name, command in dependencies:
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                version = result.stdout.strip()
                print(f"  ✅ {name}: {version}")
                results[name] = True
            else:
                print(f"  ❌ {name}: Not found or error")
                results[name] = False
        except Exception as e:
            print(f"  ❌ {name}: {str(e)}")
            results[name] = False
    
    return results

def main():
    """Run all tests"""
    try:
        print("🧪 DuckBot Complete Feature Testing Suite")
        print(f"📁 Working Directory: {Path.cwd()}")
    except UnicodeEncodeError:
        print("[TESTS] DuckBot Complete Feature Testing Suite")
        print(f"[DIR] Working Directory: {Path.cwd()}")
    
    test_results = {
        'imports': test_imports(),
        'service_detection': test_service_detection(),
        'server_management': test_server_management(),
        'ai_routing': test_ai_routing(),
        'webui': test_webui_startup(),
        'dependencies': test_external_dependencies(),
    }
    
    # Summary
    test_section("TEST SUMMARY")
    total_tests = len(test_results)
    passed_tests = sum(1 for result in test_results.values() if result)
    
    try:
        print(f"📊 Test Results: {passed_tests}/{total_tests} categories passed")
        print("\n📋 Detailed Results:")
    except UnicodeEncodeError:
        print(f"[RESULTS] Test Results: {passed_tests}/{total_tests} categories passed")
        print("\n[DETAILS] Detailed Results:")
    
    for category, result in test_results.items():
        if isinstance(result, dict):
            sub_passed = sum(1 for r in result.values() if r)
            sub_total = len(result)
            try:
                status = "✅" if sub_passed == sub_total else "⚠️" if sub_passed > 0 else "❌"
            except UnicodeEncodeError:
                status = "[PASS]" if sub_passed == sub_total else "[PARTIAL]" if sub_passed > 0 else "[FAIL]"
            print(f"  {status} {category.title()}: {sub_passed}/{sub_total}")
        else:
            try:
                status = "✅" if result else "❌"
            except UnicodeEncodeError:
                status = "[PASS]" if result else "[FAIL]"
            print(f"  {status} {category.title()}")
    
    # Overall status
    try:
        if passed_tests == total_tests:
            print("\n🎉 ALL TESTS PASSED - DuckBot is ready for production!")
            return 0
        elif passed_tests >= total_tests * 0.8:
            print(f"\n⚠️  MOSTLY WORKING - {passed_tests}/{total_tests} categories passed")
            return 1
        else:
            print(f"\n❌ NEEDS ATTENTION - Only {passed_tests}/{total_tests} categories passed")
            return 2
    except UnicodeEncodeError:
        if passed_tests == total_tests:
            print(f"\n[SUCCESS] ALL TESTS PASSED - DuckBot is ready for production!")
            return 0
        elif passed_tests >= total_tests * 0.8:
            print(f"\n[PARTIAL] MOSTLY WORKING - {passed_tests}/{total_tests} categories passed")
            return 1
        else:
            print(f"\n[ATTENTION] NEEDS ATTENTION - Only {passed_tests}/{total_tests} categories passed")
            return 2

if __name__ == "__main__":
    sys.exit(main())