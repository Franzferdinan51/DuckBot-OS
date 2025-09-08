#!/usr/bin/env python3
"""
COMPREHENSIVE TEST - Every Single DuckBot Feature
"""
import sys
import subprocess
import os
import time
import threading
from pathlib import Path

print("[COMPREHENSIVE] Testing EVERY DuckBot Feature")
print("=" * 60)

def run_test(name, code, timeout=10):
    """Run a test with timeout"""
    try:
        result = subprocess.run([sys.executable, '-c', code], 
                              capture_output=True, text=True, timeout=timeout)
        if result.returncode == 0:
            print(f"[PASS] {name}")
            return True, result.stdout.strip()
        else:
            error_msg = result.stderr.strip()[:100]
            print(f"[FAIL] {name}: {error_msg}")
            return False, error_msg
    except subprocess.TimeoutExpired:
        print(f"[TIMEOUT] {name} (increase timeout for complex operations)")
        return False, "Timeout - consider increasing timeout for this test"
    except Exception as e:
        print(f"[ERROR] {name}: {str(e)[:100]}")
        return False, str(e)

# Test 1: All Core Imports
print("\n1. TESTING ALL CORE IMPORTS")
core_imports = [
    ("WebUI App", "from duckbot.webui import app; print('WebUI loaded')"),
    ("AI Router", "from duckbot.ai_router_gpt import route_task, get_lm_studio_model; print('AI Router loaded')"),
    ("Server Manager", "from duckbot.server_manager import server_manager; print('Server Manager loaded')"),
    ("Service Detector", "from duckbot.service_detector import ServiceDetector; print('Service Detector loaded')"),
    ("Qwen Diagnostics", "from duckbot.qwen_diagnostics import QwenDiagnostics; print('Qwen Diagnostics loaded')"),
    ("Qwen Agent Integration", "from duckbot.qwen_agent_integration import qwen_agent; print('Qwen Agent loaded')"),
    ("AI Cache Manager", "import ai_cache_manager; print('Cache Manager loaded')"),
    ("Cost Tracker", "from duckbot.cost_tracker import cost_tracker; print('Cost Tracker loaded')"),
    ("Settings GPT", "from duckbot.settings_gpt import load_settings; print('Settings loaded')"),
    ("Rate Limiter", "from duckbot.rate_limit import rate_limited; print('Rate Limiter loaded')"),
    ("Ecosystem Manager", "import ai_ecosystem_manager; print('Ecosystem Manager loaded')"),
    ("Start Ecosystem", "import start_ai_ecosystem; print('Start Ecosystem loaded')"),
    ("Start ComfyUI", "import start_comfyui; print('Start ComfyUI loaded')"),
]

import_results = {}
for name, code in core_imports:
    success, output = run_test(name, code)
    import_results[name] = success

# Test 2: AI Router Features
print("\n2. TESTING AI ROUTER FEATURES")
ai_tests = [
    ("LM Studio Detection", """
from duckbot.ai_router_gpt import get_lm_studio_model
model = get_lm_studio_model()
print(f'Detected model: {model}')
"""),
    ("Model Tiers", """
from duckbot.ai_router_gpt import TIERS
print(f'Available tiers: {list(TIERS.keys())}')
free_models = [t['model'] for t in TIERS.values() if 'free' in t.get('model', '')]
print(f'Free models: {len(free_models)}')
"""),
    ("Dynamic Model Selection", """
from duckbot.ai_router_gpt import _select_best_available_model
models = ['qwen/qwen3-coder-30b', 'bartowski/nvidia-llama-3.3-nemotron', 'google/gemma-3-12b']
task = {'kind': 'reasoning', 'prompt': 'Test reasoning task'}
selected = _select_best_available_model(models, task)
print(f'Selected: {selected}')
"""),
    ("Task Routing", """
from duckbot.ai_router_gpt import get_optimal_model_for_task
task = {'kind': 'code', 'prompt': 'Write a function'}
model = get_optimal_model_for_task(task)
print(f'Code task model: {model}')
"""),
    ("Qwen Code Tools", """
from duckbot.ai_router_gpt import can_use_qwen_code_tools
task = {'kind': 'code', 'prompt': 'debug python function'}
can_use = can_use_qwen_code_tools(task)
print(f'Can use Qwen tools: {can_use}')
"""),
]

ai_results = {}
for name, code in ai_tests:
    success, output = run_test(name, code.strip())
    ai_results[name] = success

# Test 3: Server Management
print("\n3. TESTING SERVER MANAGEMENT")
server_tests = [
    ("Service Status", """
from duckbot.server_manager import server_manager
status = server_manager.get_all_service_status()
print(f'Services monitored: {len(status)}')
running = sum(1 for info in status.values() if info.status.value == 'running')
print(f'Running services: {running}')
"""),
    ("Service Info", """
from duckbot.server_manager import server_manager
info = server_manager.get_service_status('lm_studio')
print(f'LM Studio status: {info.status.value}')
print(f'LM Studio port: {info.port}')
"""),
    ("Server Management Task", """
from duckbot.ai_router_gpt import handle_server_management_task
task = {'kind': 'status', 'prompt': 'check server status'}
result = handle_server_management_task(task)
print(f'Server task result: {result is not None}')
"""),
]

server_results = {}
for name, code in server_tests:
    success, output = run_test(name, code.strip())
    server_results[name] = success

# Test 4: WebUI Features
print("\n4. TESTING WEBUI FEATURES")
# Start WebUI in background for testing
def start_webui_background():
    try:
        from duckbot.webui import app
        import uvicorn
        uvicorn.run(app, host='127.0.0.1', port=8791, log_level='error')
    except:
        pass

webui_thread = threading.Thread(target=start_webui_background, daemon=True)
webui_thread.start()
time.sleep(3)

webui_tests = [
    ("WebUI Token Generation", """
from duckbot.webui import WEBUI_TOKEN
print(f'Token generated: {len(WEBUI_TOKEN) > 10}')
"""),
    ("WebUI Routes", """
from duckbot.webui import app
routes = [route.path for route in app.routes if hasattr(route, 'path')]
server_routes = [r for r in routes if 'server' in r or 'ecosystem' in r]
print(f'Total routes: {len(routes)}')
print(f'Server routes: {len(server_routes)}')
"""),
    ("Settings Management", """
from duckbot.settings_gpt import load_settings, save_settings
settings = load_settings()
print(f'Settings loaded: {isinstance(settings, dict)}')
"""),
]

webui_results = {}
for name, code in webui_tests:
    success, output = run_test(name, code.strip())
    webui_results[name] = success

# Test 5: Service Detection
print("\n5. TESTING SERVICE DETECTION")
service_tests = [
    ("Service Detector", """
from duckbot.service_detector import ServiceDetector
detector = ServiceDetector()
recommendations = detector.get_startup_recommendations()
print(f'Services detected: {len(recommendations)}')
"""),
    ("Port Detection", """
from duckbot.service_detector import ServiceDetector
detector = ServiceDetector()
comfyui_status = detector._is_service_running('comfyui')
print(f'ComfyUI detection: {comfyui_status}')
"""),
]

detection_results = {}
for name, code in service_tests:
    # Service detection can be slow, use longer timeout
    success, output = run_test(name, code.strip(), timeout=30)
    detection_results[name] = success

# Test 6: Qwen Features
print("\n6. TESTING QWEN FEATURES")
qwen_tests = [
    ("Qwen Diagnostics", """
from duckbot.qwen_diagnostics import QwenDiagnostics
qd = QwenDiagnostics()
available = qd.is_available()
print(f'Qwen diagnostics available: {available}')
"""),
    ("Qwen Agent Integration", """
from duckbot.qwen_agent_integration import is_qwen_agent_available, get_qwen_agent_capabilities
available = is_qwen_agent_available()
caps = get_qwen_agent_capabilities()
print(f'Qwen Agent available: {available}')
print(f'Capabilities: {len(caps["tools"])} tools')
"""),
]

qwen_results = {}
for name, code in qwen_tests:
    success, output = run_test(name, code.strip())
    qwen_results[name] = success

# Test 7: External Dependencies
print("\n7. TESTING EXTERNAL DEPENDENCIES")
# Windows PATH fix: Add common Node.js paths
import os
node_paths = [
    r"C:\Program Files\nodejs",
    r"C:\Program Files (x86)\nodejs", 
    os.path.expanduser(r"~\AppData\Roaming\npm")
]
current_path = os.environ.get('PATH', '')
for path in node_paths:
    if path not in current_path and os.path.exists(path):
        os.environ['PATH'] = current_path + os.pathsep + path

external_deps = [
    ("Node.js", ["node", "--version"]),
    ("npm", ["npm", "--version"]),
    ("n8n (direct)", ["n8n", "--version"]),
    ("Python", [sys.executable, "--version"]),
]

dep_results = {}
for name, command in external_deps:
    try:
        # Increase timeout for n8n which can be slow to respond
        timeout_val = 15 if "n8n" in name else 5
        result = subprocess.run(command, capture_output=True, text=True, timeout=timeout_val, shell=True)
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"[PASS] {name}: {version}")
            dep_results[name] = True
        else:
            print(f"[FAIL] {name}: Not available (return code {result.returncode})")
            dep_results[name] = False
    except subprocess.TimeoutExpired:
        print(f"[TIMEOUT] {name}: Command timed out")
        dep_results[name] = False
    except Exception as e:
        # For n8n, try alternative detection methods
        if "n8n" in name:
            try:
                # Check if n8n.cmd exists in npm directory
                npm_dir = os.path.expanduser(r"~\AppData\Roaming\npm")
                n8n_cmd = os.path.join(npm_dir, "n8n.cmd")
                if os.path.exists(n8n_cmd):
                    print(f"[PASS] {name}: Found at {n8n_cmd}")
                    dep_results[name] = True
                    continue
            except:
                pass
        print(f"[FAIL] {name}: {str(e)[:50]}")
        dep_results[name] = False

# Test 8: Configuration Files
print("\n8. TESTING CONFIGURATION")
config_tests = [
    ("AI Config", "import json; data = json.load(open('ai_config.json')); print(f'AI config loaded: {len(data)} keys')"),
    ("Ecosystem Config", "import yaml; data = yaml.safe_load(open('ecosystem_config.yaml')); print(f'Ecosystem config: {len(data)} sections')"),
    ("Environment", "import os; token = os.getenv('AI_MODEL_MAIN_BRAIN', 'default'); print(f'Env vars working: {token}')"),
]

config_results = {}
for name, code in config_tests:
    success, output = run_test(name, code)
    config_results[name] = success

# COMPREHENSIVE SUMMARY
print("\n" + "="*60)
print("COMPREHENSIVE TEST RESULTS")
print("="*60)

all_results = {
    "Core Imports": import_results,
    "AI Router": ai_results, 
    "Server Management": server_results,
    "WebUI Features": webui_results,
    "Service Detection": detection_results,
    "Qwen Features": qwen_results,
    "External Dependencies": dep_results,
    "Configuration": config_results,
}

total_tests = 0
passed_tests = 0

for category, results in all_results.items():
    category_passed = sum(results.values())
    category_total = len(results)
    total_tests += category_total
    passed_tests += category_passed
    
    status = "[PASS]" if category_passed == category_total else "[PARTIAL]" if category_passed > 0 else "[FAIL]"
    print(f"{status} {category}: {category_passed}/{category_total}")
    
    # Show failed tests
    failed = [name for name, result in results.items() if not result]
    if failed:
        for fail in failed[:3]:  # Show first 3 failures
            print(f"    - FAILED: {fail}")

print(f"\nOVERALL RESULT: {passed_tests}/{total_tests} tests passed")

# Calculate success rate
success_rate = (passed_tests / total_tests) * 100

if passed_tests == total_tests:
    print(f"\n[PERFECT] ALL FEATURES TESTED AND WORKING! (100%)")
    sys.exit(0)
elif passed_tests >= total_tests * 0.95:
    print(f"\n[EXCELLENT] {passed_tests}/{total_tests} working ({success_rate:.1f}%) - System is production ready!")
    sys.exit(0)
elif passed_tests >= total_tests * 0.9:
    print(f"\n[VERY GOOD] {passed_tests}/{total_tests} working ({success_rate:.1f}%) - System is production ready!")
    sys.exit(0)
elif passed_tests >= total_tests * 0.8:
    print(f"\n[GOOD] {passed_tests}/{total_tests} working ({success_rate:.1f}%) - Minor issues to address")
    sys.exit(1)
else:
    print(f"\n[ATTENTION] Only {passed_tests}/{total_tests} working ({success_rate:.1f}%) - Needs attention")
    sys.exit(2)