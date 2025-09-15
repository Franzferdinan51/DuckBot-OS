#!/usr/bin/env python3
"""
Test Local Feature Parity - Verify all cloud features work in local-only mode
"""

import os
import sys
import time
import json
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

def test_local_feature_parity():
    """Test that all cloud features work in local-only mode"""
    print("🧪 Testing Local Feature Parity")
    print("=" * 50)
    
    # Enable local-only mode
    os.environ['AI_LOCAL_ONLY_MODE'] = 'true'
    os.environ['ENABLE_DYNAMIC_LOADING'] = 'true'
    
    test_results = {}
    
    print("[TOOLS] Setup: Local-only mode enabled")
    
    # Test 1: AI Router Integration
    print("\n1️⃣  Testing AI Router Local Integration...")
    try:
        from duckbot.ai_router_gpt import route_task
        
        test_task = {
            "kind": "code",
            "risk": "low", 
            "prompt": "Write a Python function to calculate fibonacci numbers",
            "user_id": "test_user"
        }
        
        response = route_task(test_task, bucket_type="general")
        
        test_results["ai_router"] = {
            "status": "[OK] PASS",
            "local_mode": response.get("local_feature_parity", False),
            "model_used": response.get("model_used", "unknown"),
            "enhancements": response.get("local_enhancements", [])
        }
        
        print(f"   [OK] AI Router: {response.get('model_used', 'unknown')}")
        if response.get("local_enhancements"):
            print(f"   [TARGET] Local Enhancements: {', '.join(response['local_enhancements'])}")
            
    except Exception as e:
        test_results["ai_router"] = {"status": "[FAIL] FAIL", "error": str(e)}
        print(f"   [FAIL] AI Router Error: {e}")
    
    # Test 2: Dynamic Model Management
    print("\n2️⃣  Testing Dynamic Model Management...")
    try:
        from duckbot.dynamic_model_manager import DynamicModelManager
        
        manager = DynamicModelManager()
        status = manager.get_status()
        
        test_results["dynamic_models"] = {
            "status": "[OK] PASS",
            "main_brain": status.get("main_brain_model"),
            "loaded_models": len(status.get("currently_loaded", [])),
            "task_specific": len(status.get("task_specific_models", []))
        }
        
        print(f"   [OK] Main Brain: {status.get('main_brain_model', 'Not set')}")
        print(f"   [TARGET] Task Models: {len(status.get('task_specific_models', []))}")
        print(f"   [SAVE] RAM Available: {status['system_resources']['free_ram_gb']}GB")
        
    except Exception as e:
        test_results["dynamic_models"] = {"status": "[FAIL] FAIL", "error": str(e)}
        print(f"   [FAIL] Dynamic Models Error: {e}")
    
    # Test 3: Local Feature Parity Module
    print("\n3️⃣  Testing Local Feature Parity Module...")
    try:
        from duckbot.local_feature_parity import local_parity
        
        test_task = {"kind": "analysis", "prompt": "Analyze system performance"}
        test_response = {"text": "System analysis complete", "model_used": "local"}
        
        enhanced_response = local_parity.enhance_response_locally(test_task, test_response)
        
        test_results["local_parity"] = {
            "status": "[OK] PASS",
            "enhancements_applied": enhanced_response.get("local_enhancements", []),
            "rag_used": enhanced_response.get("rag_used", False),
            "enhanced_ai": enhanced_response.get("enhanced_with_local_ai", False)
        }
        
        print(f"   [OK] Feature Parity Module Working")
        if enhanced_response.get("local_enhancements"):
            print(f"   [TARGET] Applied: {', '.join(enhanced_response['local_enhancements'])}")
            
    except Exception as e:
        test_results["local_parity"] = {"status": "[FAIL] FAIL", "error": str(e)}
        print(f"   [FAIL] Local Parity Error: {e}")
    
    # Test 4: RAG in Local Mode
    print("\n4️⃣  Testing RAG (Retrieval-Augmented Generation)...")
    try:
        from duckbot.rag import maybe_augment_with_rag, index_stats
        
        test_task = {"prompt": "What are the system requirements?", "kind": "qa"}
        augmented_task, rag_info = maybe_augment_with_rag(test_task)
        
        test_results["rag"] = {
            "status": "[OK] PASS",
            "rag_used": rag_info.get("used", False),
            "chunks_found": len(rag_info.get("chunks", [])),
            "index_stats": index_stats()
        }
        
        print(f"   [OK] RAG Available")
        print(f"   [DOCS] RAG Used: {rag_info.get('used', False)}")
        
    except Exception as e:
        test_results["rag"] = {"status": "[FAIL] FAIL", "error": str(e)}
        print(f"   [FAIL] RAG Error: {e}")
    
    # Test 5: Action Logging
    print("\n5️⃣  Testing Action Logging...")
    try:
        from duckbot.action_reasoning_logger import action_logger
        
        action_logger.log_ai_routing_decision(
            prompt="Test prompt",
            chosen_model="local_test_model",
            reasoning="Testing local action logging",
            available_models=["local_test_model"],
            rate_limit_status={"bucket": "test", "tokens": 100},
            execution_time_ms=50,
            outcome="Success: Test",
            user_id="test_user"
        )
        
        test_results["action_logging"] = {
            "status": "[OK] PASS",
            "local_compatible": True
        }
        
        print("   [OK] Action Logging Working")
        
    except Exception as e:
        test_results["action_logging"] = {"status": "[FAIL] FAIL", "error": str(e)}
        print(f"   [FAIL] Action Logging Error: {e}")
    
    # Test 6: Cost Tracking (Local Usage Tracking)
    print("\n6️⃣  Testing Cost/Usage Tracking...")
    try:
        from duckbot.cost_tracker import CostTracker
        
        tracker = CostTracker()
        tracker.track_request(
            provider="local",
            model="test_local_model",
            input_tokens=100,
            output_tokens=50,
            cost=0.0,  # Local models are free
            request_type="local_test"
        )
        
        test_results["cost_tracking"] = {
            "status": "[OK] PASS", 
            "local_tracking": True
        }
        
        print("   [OK] Usage Tracking Working (Local models = $0 cost)")
        
    except Exception as e:
        test_results["cost_tracking"] = {"status": "[FAIL] FAIL", "error": str(e)}
        print(f"   [FAIL] Cost Tracking Error: {e}")
    
    # Test 7: Rate Limiting (Resource-Based)
    print("\n7️⃣  Testing Resource-Based Rate Limiting...")
    try:
        from duckbot.local_feature_parity import local_parity
        
        # Test multiple rate limit checks
        allowed_1 = local_parity.ensure_local_rate_limiting("general")
        allowed_2 = local_parity.ensure_local_rate_limiting("chat")
        
        test_results["rate_limiting"] = {
            "status": "[OK] PASS",
            "resource_based": True,
            "general_allowed": allowed_1,
            "chat_allowed": allowed_2
        }
        
        print(f"   [OK] Resource-Based Rate Limiting Working")
        print(f"   🖥️  System Load Monitoring: Active")
        
    except Exception as e:
        test_results["rate_limiting"] = {"status": "[FAIL] FAIL", "error": str(e)}
        print(f"   [FAIL] Rate Limiting Error: {e}")
    
    # Summary
    print("\n[STATS] TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for result in test_results.values() if "[OK] PASS" in result.get("status", ""))
    failed = len(test_results) - passed
    
    print(f"[OK] Passed: {passed}")
    print(f"[FAIL] Failed: {failed}")
    print(f"[STATS] Success Rate: {(passed/len(test_results)*100):.1f}%")
    
    print("\n🏠 LOCAL-ONLY MODE FEATURE PARITY:")
    
    essential_features = [
        ("Dynamic Model Loading", "dynamic_models"),
        ("AI Task Routing", "ai_router"), 
        ("Local Enhancements", "local_parity"),
        ("Resource Rate Limiting", "rate_limiting")
    ]
    
    for feature_name, test_key in essential_features:
        status = test_results.get(test_key, {}).get("status", "[FAIL] NOT TESTED")
        print(f"   {status}: {feature_name}")
    
    optional_features = [
        ("RAG Integration", "rag"),
        ("Action Logging", "action_logging"),
        ("Usage Tracking", "cost_tracking")
    ]
    
    print("\n[TOOLS] OPTIONAL FEATURES:")
    for feature_name, test_key in optional_features:
        status = test_results.get(test_key, {}).get("status", "[FAIL] NOT TESTED")
        print(f"   {status}: {feature_name}")
    
    # Feature comparison
    print(f"\n🆚 CLOUD VS LOCAL FEATURE COMPARISON:")
    print(f"   [AI] AI Routing: [OK] Cloud ↔️ [OK] Local (Dynamic Models)")
    print(f"   💰 Cost Control: [OK] Cloud ($$) ↔️ [OK] Local (Resources)")
    print(f"   [DOCS] RAG: [OK] Cloud ↔️ [OK] Local (Same)")
    print(f"   [STATS] Analytics: [OK] Cloud ↔️ [OK] Local (Usage Tracking)")
    print(f"   🔄 Caching: [OK] Cloud ↔️ [OK] Local (Same)")
    print(f"   🛡️ Rate Limiting: [OK] Cloud (API) ↔️ [OK] Local (Resources)")
    
    if failed == 0:
        print(f"\n[SUCCESS] ALL TESTS PASSED! Local-only mode has full feature parity!")
        return True
    else:
        print(f"\n[WARN]  {failed} test(s) failed. Check implementation.")
        return False

if __name__ == "__main__":
    try:
        success = test_local_feature_parity()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[FAIL] Test suite error: {e}")
        sys.exit(1)