#!/usr/bin/env python3
"""
Model Status Checker for DuckBot Dynamic Model Manager
Shows current loaded models, system resources, and usage statistics
"""

import os
import json
import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

def main():
    """Show dynamic model manager status"""
    print("[BRAIN] DuckBot Dynamic Model Manager Status")
    print("=" * 50)
    
    try:
        from duckbot.dynamic_model_manager import DynamicModelManager
        
        manager = DynamicModelManager()
        status = manager.get_status()
        
        print(f"[BRAIN] Main Brain Model: {status.get('main_brain_model', 'Not set')}")
        if status.get('main_brain_model'):
            print("   [PROTECTED]  Protected - never unloaded")
        
        print(f"\n[EMOJI] Total Loaded Models: {len(status['currently_loaded'])}")
        
        task_specific = status.get('task_specific_models', [])
        if task_specific:
            print(f"[FOCUS] Task-Specific Models: {len(task_specific)}")
            for i, model in enumerate(task_specific, 1):
                print(f"   {i}. {model}")
        else:
            print("[FOCUS] Task-Specific Models: None loaded")
            
        slots = status.get('model_slots', {})
        if slots:
            print(f"\n[EMOJI] Model Slots: {slots.get('used', 0)}/{slots.get('max', 3)} used")
            
        print("\n[SAVE] System Resources:")
        resources = status['system_resources']
        print(f"   RAM Available: {resources['free_ram_gb']}GB")
        print(f"   VRAM Available: {resources['free_vram_gb']}GB") 
        print(f"   CPU Usage: {resources['cpu_percent']:.1f}%")
        
        print("\n[METRICS] Model Usage Statistics:")
        if status['usage_stats']:
            for model, count in sorted(status['usage_stats'].items(), key=lambda x: x[1], reverse=True):
                print(f"   {model}: {count} times")
        else:
            print("   (No usage statistics yet)")
            
        print("\n[FOCUS] Recent Task History:")
        if status['recent_tasks']:
            for task in status['recent_tasks']:
                task_kind = task.get('kind', 'unknown')
                model_selected = task.get('model_selected', 'unknown')
                print(f"   {task_kind} → {model_selected}")
        else:
            print("   (No recent tasks)")
            
        # Check if dynamic loading is enabled
        if os.getenv('ENABLE_DYNAMIC_LOADING') == 'true':
            print("\n[OK] Dynamic model loading is ENABLED")
        else:
            print("\n[WARNING]  Dynamic model loading is DISABLED")
            
    except ImportError:
        print("[ERROR] Dynamic Model Manager not available")
        print("   Make sure you're running this from the DuckBot directory")
    except Exception as e:
        print(f"[ERROR] Error checking status: {e}")

if __name__ == "__main__":
    main()