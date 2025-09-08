#!/usr/bin/env python3
"""
Dynamic Model Manager for DuckBot Local-Only Mode
Intelligently loads/unloads models based on task requirements and system resources
"""

import os
import time
import json
import psutil
import requests
import subprocess
import re
import threading
from pathlib import Path

# Import hardware detector
try:
    from .hardware_detector import HardwareDetector
    HARDWARE_DETECTION_AVAILABLE = True
except ImportError:
    HARDWARE_DETECTION_AVAILABLE = False
    HardwareDetector = None
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict, deque

# Model performance and resource requirements database
@dataclass
class ModelSpec:
    id: str
    name: str
    size_gb: float
    ram_required_gb: float
    vram_required_gb: float
    capabilities: List[str]  # ["coding", "reasoning", "general", "math", "analysis"]
    performance_score: int  # 1-100
    load_time_seconds: float
    specialty_bonus: Dict[str, int]  # Task type -> bonus points

class DynamicModelManager:
    def __init__(self, lm_studio_url: str = "http://localhost:1234"):
        self.lm_studio_url = lm_studio_url
        self.currently_loaded = {}  # model_id -> load_timestamp
        self.task_history = deque(maxlen=100)  # Recent task patterns
        self.model_usage_stats = defaultdict(int)  # model_id -> usage_count
        self.lock = threading.RLock()
        
        # Hardware detection and optimization
        self.hardware_info = None
        self.performance_tier = "unknown"
        self.detect_hardware()
        
        # Main brain model - always kept loaded for system orchestration
        self.main_brain_model = None
        self.main_brain_protected = True  # Never unload the main brain
        
        # System resource monitoring (will be updated by hardware detection)
        self.min_free_ram_gb = 2.0  # Keep at least 2GB free
        self.min_free_vram_gb = 1.0  # Keep at least 1GB VRAM free
        self.max_models_loaded = 3  # Main brain + 2 task-specific models
        
        # Load model database
        self.model_database = self._initialize_model_database()
        
        # Initialize main brain on startup
        self._initialize_main_brain()
    
    def detect_hardware(self):
        """Detect hardware and optimize configuration"""
        if not HARDWARE_DETECTION_AVAILABLE:
            print("[HARDWARE] Hardware detection not available - using defaults")
            return
            
        try:
            print("[HARDWARE] Detecting system hardware...")
            detector = HardwareDetector()
            config = detector.detect_all_hardware()
            
            self.hardware_info = config["hardware_info"]
            self.performance_tier = config["performance_tier"]
            
            # Update system resource limits based on detected hardware
            gpu_info = self.hardware_info.get("gpu", {})
            memory_info = self.hardware_info.get("memory", {})
            
            total_vram = gpu_info.get("total_vram_gb", 4)
            total_ram = memory_info.get("total_gb", 8)
            
            # Universal VRAM optimization based on total available
            if total_vram >= 20:  # Enterprise/Workstation
                self.min_free_vram_gb = 4.0
                self.max_models_loaded = 4
            elif total_vram >= 12:  # Enthusiast
                self.min_free_vram_gb = 2.0
                self.max_models_loaded = 3
            elif total_vram >= 8:   # High-end
                self.min_free_vram_gb = 2.0
                self.max_models_loaded = 3
            elif total_vram >= 6:   # Mid-range
                self.min_free_vram_gb = 1.5
                self.max_models_loaded = 2
            elif total_vram >= 4:   # Budget
                self.min_free_vram_gb = 1.0
                self.max_models_loaded = 2
            elif total_vram >= 2:   # Low-end
                self.min_free_vram_gb = 0.5
                self.max_models_loaded = 1
            else:  # Ultra-low/integrated
                self.min_free_vram_gb = 0.5
                self.max_models_loaded = 1
            
            # Universal RAM optimization
            if total_ram >= 64:      # Workstation
                self.min_free_ram_gb = 8.0
            elif total_ram >= 32:   # High-end
                self.min_free_ram_gb = 4.0
            elif total_ram >= 16:   # Mid-range
                self.min_free_ram_gb = 2.0
            elif total_ram >= 8:    # Budget
                self.min_free_ram_gb = 1.0
            else:  # Low-end
                self.min_free_ram_gb = 0.5
            
            print(f"[HARDWARE] Detected: {gpu_info.get('primary_gpu', 'Unknown GPU')}")
            print(f"[HARDWARE] VRAM: {total_vram:.1f}GB, RAM: {total_ram:.1f}GB")
            print(f"[HARDWARE] Performance tier: {self.performance_tier}")
            print(f"[HARDWARE] Max models: {self.max_models_loaded}, VRAM buffer: {self.min_free_vram_gb:.1f}GB")
            
            # Save hardware config for reference
            try:
                detector.save_hardware_config()
            except Exception as e:
                print(f"[WARNING] Could not save hardware config: {e}")
                
        except Exception as e:
            print(f"[ERROR] Hardware detection failed: {e}")
            print("[HARDWARE] Using default configuration")
    
    def get_hardware_optimized_models(self) -> List[str]:
        """Get list of models optimized for detected hardware - Universal for any system"""
        if not self.hardware_info:
            return ["qwen/qwen3-coder:free", "nvidia_NVIDIA-Nemotron-Nano-9B-v2-GGUF/nvidia_NVIDIA-Nemotron-Nano-9B-v2-Q5_K_S.gguf", "microsoft/phi-3-mini"]
        
        # Use the hardware detector's recommendations if available
        try:
            detector = HardwareDetector() if HARDWARE_DETECTION_AVAILABLE else None
            if detector and self.hardware_info:
                detector.hardware_info = self.hardware_info
                detector.performance_tier = self.performance_tier
                recommendations = detector._generate_model_recommendations()
                return recommendations.get("main_brain_candidates", [])
        except Exception:
            pass
            
        # Fallback to tier-based selection
        if self.performance_tier == "enterprise":
            return [
                "qwen/qwen3-coder-30b",
                "meta/llama-3-70b-instruct",
                "qwen/qwen2.5-coder-32b"
            ]
        elif self.performance_tier == "enthusiast":
            return [
                "qwen/qwen3-coder-14b",
                "meta/llama-3-13b-instruct",
                "google/gemma-2-27b"
            ]
        elif self.performance_tier == "high_end":
            return [
                "qwen/qwen3-coder:free",     # OpenRouter free tier first
                "nvidia_NVIDIA-Nemotron-Nano-9B-v2-GGUF/nvidia_NVIDIA-Nemotron-Nano-9B-v2-Q5_K_S.gguf",  # LM Studio local
                "google/gemma-2-9b-it",
                "microsoft/phi-3-medium"
            ]
        elif self.performance_tier == "mid_range":
            return [
                "microsoft/phi-3-mini",
                "google/gemma-2-2b",
                "qwen/qwen2.5-coder-3b"
            ]
        elif self.performance_tier == "budget":
            return [
                "microsoft/phi-3-mini",
                "google/gemma-2-2b"
            ]
        else:  # low_end, ultra_low, unknown
            return [
                "microsoft/phi-2",
                "google/gemma-2-2b"
            ]
        
    def _initialize_model_database(self) -> Dict[str, ModelSpec]:
        """Initialize database of known models and their characteristics"""
        return {
            # Coding specialists
            "qwen/qwen3-coder-30b": ModelSpec(
                id="qwen/qwen3-coder-30b",
                name="Qwen3 Coder 30B",
                size_gb=16.0,
                ram_required_gb=20.0,
                vram_required_gb=16.0,
                capabilities=["coding", "analysis", "debugging"],
                performance_score=90,
                load_time_seconds=45.0,
                specialty_bonus={"code": 25, "json_format": 20, "debugging": 30}
            ),
            "qwen/qwen2.5-coder-32b": ModelSpec(
                id="qwen/qwen2.5-coder-32b", 
                name="Qwen2.5 Coder 32B",
                size_gb=17.0,
                ram_required_gb=21.0,
                vram_required_gb=17.0,
                capabilities=["coding", "analysis"],
                performance_score=85,
                load_time_seconds=50.0,
                specialty_bonus={"code": 20, "analysis": 15}
            ),
            
            # Local LM Studio models
            "nvidia_NVIDIA-Nemotron-Nano-9B-v2-GGUF/nvidia_NVIDIA-Nemotron-Nano-9B-v2-Q5_K_S.gguf": ModelSpec(
                id="nvidia_NVIDIA-Nemotron-Nano-9B-v2-GGUF/nvidia_NVIDIA-Nemotron-Nano-9B-v2-Q5_K_S.gguf",
                name="NVIDIA Nemotron Nano 9B (Q5_K_S)",
                size_gb=6.5,
                ram_required_gb=8.0,
                vram_required_gb=7.0,
                capabilities=["general", "reasoning", "coding", "analysis"],
                performance_score=75,
                load_time_seconds=15.0,
                specialty_bonus={"general": 15, "reasoning": 10, "code": 10}
            ),
            
            # Reasoning specialists
            "bartowski/nvidia-llama-3.3-nemotron": ModelSpec(
                id="bartowski/nvidia-llama-3.3-nemotron",
                name="Nemotron 70B",
                size_gb=35.0,
                ram_required_gb=42.0,
                vram_required_gb=35.0,
                capabilities=["reasoning", "analysis", "math"],
                performance_score=95,
                load_time_seconds=120.0,
                specialty_bonus={"reasoning": 30, "policy": 25, "arbiter": 30}
            ),
            "deepseek/deepseek-r1": ModelSpec(
                id="deepseek/deepseek-r1",
                name="DeepSeek R1",
                size_gb=30.0,
                ram_required_gb=36.0,
                vram_required_gb=30.0,
                capabilities=["reasoning", "math", "analysis"],
                performance_score=92,
                load_time_seconds=90.0,
                specialty_bonus={"reasoning": 35, "r1": 40}
            ),
            
            # OpenRouter free tier models
            "qwen/qwen3-coder:free": ModelSpec(
                id="qwen/qwen3-coder:free",
                name="Qwen3 Coder (Free Tier)",
                size_gb=0.0,  # Cloud model - no local resources needed
                ram_required_gb=0.0,
                vram_required_gb=0.0,
                capabilities=["coding", "general", "analysis", "reasoning"],
                performance_score=85,
                load_time_seconds=2.0,  # Fast cloud access
                specialty_bonus={"code": 30, "general": 20, "analysis": 15, "reasoning": 10}
            ),
            
            # Efficient general purpose
            "google/gemma-3-12b": ModelSpec(
                id="google/gemma-3-12b",
                name="Gemma 3 12B",
                size_gb=6.5,
                ram_required_gb=8.0,
                vram_required_gb=6.5,
                capabilities=["general", "summary"],
                performance_score=70,
                load_time_seconds=20.0,
                specialty_bonus={"status": 15, "summary": 20}
            ),
            "qwen/qwq-32b": ModelSpec(
                id="qwen/qwq-32b",
                name="QwQ 32B",
                size_gb=16.0,
                ram_required_gb=20.0,
                vram_required_gb=16.0,
                capabilities=["qa", "reasoning"],
                performance_score=80,
                load_time_seconds=40.0,
                specialty_bonus={"qa": 25, "question": 20}
            )
        }
        
    def _initialize_main_brain(self):
        """Initialize and load the main brain model for system orchestration"""
        # Get hardware-optimized candidates first, then fallbacks
        hardware_optimized = self.get_hardware_optimized_models()
        fallback_candidates = [
            "qwen/qwen3-coder:free",     # OpenRouter free tier (PREFERRED DEFAULT)
            "nvidia_NVIDIA-Nemotron-Nano-9B-v2-GGUF/nvidia_NVIDIA-Nemotron-Nano-9B-v2-Q5_K_S.gguf",  # LM Studio local fallback
            "google/gemma-2-9b-it",      # Efficient backup
            "microsoft/phi-3-medium",    # Small but capable
            "qwen/qwen3-coder-7b",       # Coding specialist (smaller)
            "google/gemma-3-12b"         # Cloud provider backup
        ]
        
        main_brain_candidates = hardware_optimized + fallback_candidates
        
        print("[BRAIN] Initializing main brain model for system orchestration...")
        
        for candidate in main_brain_candidates:
            if candidate in self.model_database:
                can_load, reason = self.can_load_model(candidate)
                if can_load:
                    if self.load_model(candidate):
                        self.main_brain_model = candidate
                        print(f"[OK] Main brain established: {candidate}")
                        print("[PROTECTED]  Main brain will remain loaded for system management")
                        break
                    else:
                        print(f"[ERROR] Failed to load main brain candidate: {candidate}")
                else:
                    print(f"[WARNING]  Cannot load {candidate} as main brain: {reason}")
        
        if not self.main_brain_model:
            print("[WARNING]  No suitable main brain model could be loaded")
            print("[LOADING] System will use whatever model is currently available")
            
    def get_main_brain_model(self) -> str:
        """Get the main brain model ID"""
        return self.main_brain_model or "No main brain loaded"
        
    def is_main_brain_model(self, model_id: str) -> bool:
        """Check if a model is the protected main brain"""
        return model_id == self.main_brain_model
        
    def get_system_resources(self) -> Tuple[float, float, float]:
        """Get current system resource availability.
        - RAM: available system memory (GB)
        - VRAM: max free VRAM across GPUs (GB), robust to multi-GPU
        - CPU: current CPU percent
        """
        # RAM
        ram = psutil.virtual_memory()
        free_ram_gb = ram.available / (1024**3)

        # VRAM (robust, multi-GPU aware)
        free_vram_gb = self._detect_free_vram_gb()

        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)

        return free_ram_gb, free_vram_gb, cpu_percent

    def _detect_free_vram_gb(self) -> float:
        """Detect max free VRAM across available NVIDIA GPUs.
        Tries GPUtil, then falls back to nvidia-smi. Returns conservative default if unavailable.
        """
        # Try GPUtil first
        try:
            import GPUtil  # type: ignore
            gpus = GPUtil.getGPUs()
            if gpus:
                # memoryFree is in MB
                free_list = [(g.id, getattr(g, 'memoryFree', 0.0) / 1024.0) for g in gpus]
                best = max(free_list, key=lambda x: x[1])[1]
                if best > 0:
                    return float(best)
        except Exception:
            pass

        # Fallback: nvidia-smi
        try:
            cmd = [
                'nvidia-smi',
                '--query-gpu=memory.total,memory.free',
                '--format=csv,noheader,nounits'
            ]
            out = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, text=True, timeout=2)
            free_vals = []
            for line in out.strip().splitlines():
                parts = [p.strip() for p in line.split(',')]
                if len(parts) >= 2 and parts[1].isdigit():
                    free_mb = float(parts[1])
                    free_vals.append(free_mb / 1024.0)
            if free_vals:
                return float(max(free_vals))
        except Exception:
            pass

        # Last resort conservative default
        return 8.0
        
    def can_load_model(self, model_id: str) -> Tuple[bool, str]:
        """Check if we can load a specific model given current resources"""
        if model_id not in self.model_database:
            return False, f"Unknown model: {model_id}"
            
        spec = self.model_database[model_id]
        free_ram, free_vram, cpu_percent = self.get_system_resources()
        
        # Check resource requirements
        if free_ram < spec.ram_required_gb + self.min_free_ram_gb:
            return False, f"Insufficient RAM: need {spec.ram_required_gb}GB, have {free_ram:.1f}GB free"
            
        if free_vram < spec.vram_required_gb + self.min_free_vram_gb:
            return False, f"Insufficient VRAM: need {spec.vram_required_gb}GB, have {free_vram:.1f}GB free"
            
        if cpu_percent > 90:
            return False, "CPU too busy"
            
        # Check concurrent model limit
        if len(self.currently_loaded) >= self.max_models_loaded:
            return False, f"Max models loaded ({self.max_models_loaded})"
            
        return True, "OK"
        
    def select_optimal_model_for_task(self, task: dict) -> str:
        """Select the best model for a task, considering resources and performance"""
        task_kind = task.get("kind", "*")
        task_risk = task.get("risk", "low")
        prompt_length = len(task.get("prompt", ""))
        
        # For general system orchestration tasks, always use main brain
        orchestration_tasks = ["server_management", "ecosystem_management", "system_status", 
                             "service_management", "policy", "arbiter"]
        if task_kind in orchestration_tasks:
            if self.main_brain_model:
                print(f"[BRAIN] Using main brain '{self.main_brain_model}' for orchestration task: {task_kind}")
                return self.main_brain_model
        
        # For specialized tasks, consider loading task-specific models
        # But if the main brain is suitable, prefer it to avoid loading/unloading
        if self.main_brain_model and self.main_brain_model in self.model_database:
            main_brain_spec = self.model_database[self.main_brain_model]
            
            # Check if main brain is suitable for this task
            main_brain_suitable = (
                task_kind in main_brain_spec.capabilities or
                task_kind in main_brain_spec.specialty_bonus or
                "general" in main_brain_spec.capabilities or
                prompt_length < 500  # Use main brain for short/simple tasks
            )
            
            if main_brain_suitable:
                print(f"[BRAIN] Main brain '{self.main_brain_model}' suitable for task: {task_kind}")
                return self.main_brain_model
        
        # Score all available models for specialized task loading
        model_scores = {}
        
        for model_id, spec in self.model_database.items():
            score = spec.performance_score
            
            # Task-specific bonuses
            if task_kind in spec.specialty_bonus:
                score += spec.specialty_bonus[task_kind]
                
            # Capability matching
            if task_kind in ["reasoning", "policy"] and "reasoning" in spec.capabilities:
                score += 20
            elif task_kind in ["code", "debugging"] and "coding" in spec.capabilities:
                score += 20
                
            # Resource efficiency bonus for light tasks
            if prompt_length < 200 and spec.size_gb < 10:
                score += 15
                
            # Penalty for heavy models on simple tasks
            if task_kind in ["status", "summary"] and spec.size_gb > 20:
                score -= 25
                
            # Usage frequency bonus (prefer recently used models if they're good)
            if model_id in self.model_usage_stats:
                score += min(self.model_usage_stats[model_id] * 2, 10)
                
            # Currently loaded bonus (avoid loading/unloading)
            if model_id in self.currently_loaded:
                score += 30
                
            model_scores[model_id] = score
            
        # Sort by score and check resource availability
        sorted_models = sorted(model_scores.items(), key=lambda x: x[1], reverse=True)
        
        for model_id, score in sorted_models:
            can_load, reason = self.can_load_model(model_id)
            if can_load:
                return model_id
                
        # If no model can be loaded, try to free up resources
        if sorted_models:
            desired_model = sorted_models[0][0]
            if self._make_room_for_model(desired_model):
                return desired_model
                
        # Fallback to smallest available model
        smallest_model = min(self.model_database.keys(), 
                           key=lambda x: self.model_database[x].size_gb)
        return smallest_model
        
    def _make_room_for_model(self, target_model_id: str) -> bool:
        """Unload models to make room for target model"""
        if target_model_id not in self.model_database:
            return False
            
        target_spec = self.model_database[target_model_id]
        
        # Find least recently used models to unload
        if not self.currently_loaded:
            return True
            
        # Sort by last used time (oldest first)
        models_by_age = sorted(self.currently_loaded.items(), key=lambda x: x[1])
        
        for model_id, load_time in models_by_age:
            if self._unload_model(model_id):
                # Check if we now have enough resources
                can_load, _ = self.can_load_model(target_model_id)
                if can_load:
                    return True
                    
        return False
        
    def load_model(self, model_id: str) -> bool:
        """Load a specific model in LM Studio"""
        with self.lock:
            # Check if already loaded
            if model_id in self.currently_loaded:
                return True
                
            # Check resources
            can_load, reason = self.can_load_model(model_id)
            if not can_load:
                print(f"[WARNING]  Cannot load {model_id}: {reason}")
                return False
                
            try:
                # LM Studio load model API call
                response = requests.post(
                    f"{self.lm_studio_url}/models/load",
                    json={"model": model_id},
                    timeout=300  # 5 minute timeout for loading
                )
                
                if response.status_code == 200:
                    self.currently_loaded[model_id] = time.time()
                    self.model_usage_stats[model_id] += 1
                    print(f"[OK] Loaded model: {model_id}")
                    return True
                else:
                    print(f"[ERROR] Failed to load {model_id}: Status {response.status_code}")
                    return False
                    
            except Exception as e:
                print(f"[ERROR] Error loading {model_id}: {e}")
                return False
                
    def _unload_model(self, model_id: str) -> bool:
        """Unload a specific model from LM Studio (protects main brain)"""
        # Never unload the main brain model
        if self.is_main_brain_model(model_id):
            print(f"[PROTECTED]  Protecting main brain model from unload: {model_id}")
            return False
            
        try:
            response = requests.post(
                f"{self.lm_studio_url}/models/unload",
                json={"model": model_id},
                timeout=60
            )
            
            if response.status_code == 200:
                if model_id in self.currently_loaded:
                    del self.currently_loaded[model_id]
                print(f"[LOADING] Unloaded task-specific model: {model_id}")
                return True
            else:
                print(f"[WARNING]  Failed to unload {model_id}: Status {response.status_code}")
                return False
                
        except Exception as e:
            print(f"[WARNING]  Error unloading {model_id}: {e}")
            return False
            
    def get_or_load_model_for_task(self, task: dict) -> str:
        """Main entry point: get the best model for a task, loading it if needed"""
        with self.lock:
            optimal_model = self.select_optimal_model_for_task(task)
            
            # Record task for pattern analysis
            self.task_history.append({
                "kind": task.get("kind", "*"),
                "model_selected": optimal_model,
                "timestamp": time.time()
            })
            
            # Load if needed
            if optimal_model not in self.currently_loaded:
                if self.load_model(optimal_model):
                    task_kind = task.get("kind", "*")
                    print(f"[FOCUS] Dynamically loaded '{optimal_model}' for task '{task_kind}'")
                else:
                    # Fallback to any currently loaded model
                    if self.currently_loaded:
                        fallback = list(self.currently_loaded.keys())[0]
                        print(f"[LOADING] Falling back to loaded model: {fallback}")
                        return fallback
                    else:
                        print("[ERROR] No models available")
                        return "No model available"
            else:
                print(f"[OK] Using loaded model '{optimal_model}' for task '{task.get('kind', '*')}'")
                
            return optimal_model
            
    def cleanup_unused_models(self, max_idle_minutes: int = 10):
        """Unload models that haven't been used recently (protects main brain)"""
        with self.lock:
            current_time = time.time()
            idle_threshold = max_idle_minutes * 60
            
            to_unload = []
            for model_id, load_time in self.currently_loaded.items():
                # Never cleanup the main brain model
                if not self.is_main_brain_model(model_id):
                    if current_time - load_time > idle_threshold:
                        to_unload.append(model_id)
                        
            if to_unload:
                print(f"[EMOJI] Cleaning up {len(to_unload)} idle task-specific model(s)")
                for model_id in to_unload:
                    self._unload_model(model_id)
            else:
                print("[EMOJI] No idle task-specific models to cleanup")
                
    def get_status(self) -> dict:
        """Get current status of model manager"""
        free_ram, free_vram, cpu_percent = self.get_system_resources()
        
        # Separate main brain from task-specific models
        task_specific_models = [m for m in self.currently_loaded.keys() 
                              if not self.is_main_brain_model(m)]
        
        return {
            "main_brain_model": self.main_brain_model,
            "currently_loaded": list(self.currently_loaded.keys()),
            "task_specific_models": task_specific_models,
            "system_resources": {
                "free_ram_gb": round(free_ram, 1),
                "free_vram_gb": round(free_vram, 1), 
                "cpu_percent": cpu_percent
            },
            "usage_stats": dict(self.model_usage_stats),
            "recent_tasks": list(self.task_history)[-5:],  # Last 5 tasks
            "model_slots": {
                "used": len(self.currently_loaded),
                "max": self.max_models_loaded,
                "main_brain_protected": self.main_brain_protected
            }
        }
