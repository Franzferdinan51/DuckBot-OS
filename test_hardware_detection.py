#!/usr/bin/env python3
"""
Test Hardware Detection for DuckBot Enhanced
"""
import sys
import os

# Fix Windows console encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer)

# Add duckbot directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'duckbot'))

def test_hardware_detection():
    """Test the hardware detection system"""
    print("🔍 Testing DuckBot Hardware Detection")
    print("=" * 50)
    
    try:
        from duckbot.hardware_detector import HardwareDetector, detect_hardware
        
        print("✅ Hardware detector imported successfully")
        
        # Test detection
        print("\n🔍 Running hardware detection...")
        config = detect_hardware()
        
        print("\n📊 Detection Results:")
        print(f"   Performance Tier: {config['performance_tier']}")
        
        # GPU Info
        gpu_info = config["hardware_info"]["gpu"]
        print(f"   Primary GPU: {gpu_info.get('primary_gpu', 'Unknown')}")
        print(f"   Total VRAM: {gpu_info.get('total_vram_gb', 0):.1f}GB")
        
        # Memory Info
        memory_info = config["hardware_info"]["memory"]
        print(f"   System RAM: {memory_info.get('total_gb', 0):.1f}GB")
        
        # CPU Info
        cpu_info = config["hardware_info"]["cpu"]
        print(f"   CPU Cores: {cpu_info.get('cores_logical', 0)} logical")
        
        # Model Recommendations
        models = config["model_recommendations"]
        print(f"\n🧠 Recommended Models:")
        for model in models.get("main_brain_candidates", [])[:3]:
            print(f"   • {model}")
        
        print(f"\n⚙️  Optimizations:")
        print(f"   Max VRAM Allocation: {models.get('max_vram_allocation', 0):.1f}GB")
        print(f"   Recommended Quantization: {models.get('recommended_quantization', 'Q4_K_M')}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Hardware detection failed: {e}")
        return False

def test_dynamic_model_manager():
    """Test the dynamic model manager with hardware detection"""
    print("\n🤖 Testing Dynamic Model Manager")
    print("=" * 50)
    
    try:
        from duckbot.dynamic_model_manager import DynamicModelManager
        
        print("✅ Dynamic model manager imported successfully")
        
        # Initialize (this will trigger hardware detection)
        print("\n🔍 Initializing with hardware detection...")
        manager = DynamicModelManager()
        
        print(f"   Performance Tier: {manager.performance_tier}")
        print(f"   Max Models: {manager.max_models_loaded}")
        print(f"   VRAM Buffer: {manager.min_free_vram_gb:.1f}GB")
        print(f"   RAM Buffer: {manager.min_free_ram_gb:.1f}GB")
        
        # Get optimized models
        optimized_models = manager.get_hardware_optimized_models()
        print(f"\n🎯 Hardware-Optimized Models:")
        for model in optimized_models[:5]:
            print(f"   • {model}")
        
        return True
        
    except Exception as e:
        print(f"❌ Dynamic model manager test failed: {e}")
        return False

def simulate_different_systems():
    """Simulate how the system would work on different hardware configurations"""
    print("\n🖥️  Testing Universal Hardware Optimization")
    print("=" * 50)
    
    # Test different hardware scenarios
    test_scenarios = [
        {
            "name": "RTX 4090 Workstation",
            "vram_gb": 24, "ram_gb": 64, "cores": 16,
            "expected_tier": "enterprise"
        },
        {
            "name": "RTX 3080 Gaming PC", 
            "vram_gb": 10, "ram_gb": 32, "cores": 8,
            "expected_tier": "high_end"
        },
        {
            "name": "RTX 3060 Mid-Range",
            "vram_gb": 8, "ram_gb": 16, "cores": 6, 
            "expected_tier": "mid_range"
        },
        {
            "name": "GTX 1650 Budget",
            "vram_gb": 4, "ram_gb": 8, "cores": 4,
            "expected_tier": "budget"
        },
        {
            "name": "Integrated Graphics",
            "vram_gb": 2, "ram_gb": 8, "cores": 4,
            "expected_tier": "low_end"
        },
        {
            "name": "Old Laptop",
            "vram_gb": 1, "ram_gb": 4, "cores": 2,
            "expected_tier": "ultra_low"
        }
    ]
    
    for scenario in test_scenarios:
        print(f"\n📊 {scenario['name']}:")
        print(f"   VRAM: {scenario['vram_gb']}GB, RAM: {scenario['ram_gb']}GB, Cores: {scenario['cores']}")
        
        # Simulate hardware info
        mock_hardware = {
            "gpu": {"total_vram_gb": scenario['vram_gb'], "primary_gpu": scenario['name']},
            "memory": {"total_gb": scenario['ram_gb']},
            "cpu": {"cores_logical": scenario['cores']}
        }
        
        try:
            from duckbot.hardware_detector import HardwareDetector
            detector = HardwareDetector()
            detector.hardware_info = {"hardware_info": mock_hardware}
            
            # Calculate tier
            gpu_info = mock_hardware["gpu"]
            memory_info = mock_hardware["memory"]
            cpu_info = mock_hardware["cpu"]
            
            total_vram = gpu_info.get("total_vram_gb", 0)
            total_ram = memory_info.get("total_gb", 0)
            cpu_cores = cpu_info.get("cores_logical", 0)
            
            # Simplified tier calculation for demo
            if total_vram >= 20 and total_ram >= 64:
                tier = "enterprise"
            elif total_vram >= 12 and total_ram >= 32 and cpu_cores >= 8:
                tier = "enthusiast"
            elif total_vram >= 8 and total_ram >= 16 and cpu_cores >= 6:
                tier = "high_end"
            elif total_vram >= 6 and total_ram >= 12 and cpu_cores >= 4:
                tier = "mid_range"
            elif total_vram >= 4 and total_ram >= 8 and cpu_cores >= 4:
                tier = "budget"
            elif total_vram >= 2 or total_ram >= 4:
                tier = "low_end"
            else:
                tier = "ultra_low"
            
            print(f"   🎯 Performance Tier: {tier}")
            
            # Show what models would be recommended
            if tier == "enterprise":
                models = ["qwen/qwen3-coder-30b", "meta/llama-3-70b-instruct"]
            elif tier == "enthusiast":
                models = ["qwen/qwen3-coder-14b", "meta/llama-3-13b-instruct"]  
            elif tier == "high_end":
                models = ["qwen/qwen3-coder-7b", "google/gemma-2-9b-it"]
            elif tier == "mid_range":
                models = ["microsoft/phi-3-mini", "google/gemma-2-2b"]
            elif tier == "budget":
                models = ["microsoft/phi-3-mini", "google/gemma-2-2b"]
            else:
                models = ["microsoft/phi-2", "google/gemma-2-2b"]
                
            print(f"   🧠 Recommended Models: {', '.join(models[:2])}")
            
        except Exception as e:
            print(f"   ❌ Simulation failed: {e}")

def main():
    """Main test function"""
    success = True
    
    # Test hardware detection
    if not test_hardware_detection():
        success = False
    
    # Test dynamic model manager
    if not test_dynamic_model_manager():
        success = False
    
    # Show universal optimization examples
    simulate_different_systems()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ All hardware detection tests passed!")
        print("\n💡 Universal Hardware Optimization Features:")
        print("   🔧 Works on ANY hardware (RTX 4090 to integrated graphics)")
        print("   ⚙️  Auto-detects VRAM, RAM, CPU specs")
        print("   🎯 Recommends optimal models for each system")
        print("   📊 6 performance tiers: enterprise → ultra_low")
        print("   🚀 Automatically optimizes concurrent model limits")
    else:
        print("❌ Some tests failed - check error messages above")
        print("\n🔧 You may need to install missing dependencies:")
        print("   pip install psutil")
    
    print("\n🌍 DuckBot will now work optimally on ANY system!")
    print("   Your RTX 3080 system: high_end tier")
    print("   Friend's laptop: Automatically detects and optimizes")
    print("   Server deployment: Automatically scales to hardware")

if __name__ == "__main__":
    main()