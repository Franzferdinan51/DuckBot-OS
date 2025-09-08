"""
Dynamic Hardware Detection for DuckBot Enhanced
Automatically detects and optimizes for available hardware
"""
import os
import sys
import json
import subprocess
import platform
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class HardwareDetector:
    def __init__(self):
        self.hardware_info = {}
        self.model_recommendations = {}
        self.performance_tier = "unknown"
        
    def detect_all_hardware(self) -> Dict:
        """Detect all hardware components and return comprehensive info"""
        try:
            self.hardware_info = {
                "system": self._detect_system_info(),
                "gpu": self._detect_gpu_info(),
                "cpu": self._detect_cpu_info(),
                "memory": self._detect_memory_info(),
                "storage": self._detect_storage_info()
            }
            
            # Determine performance tier
            self.performance_tier = self._calculate_performance_tier()
            
            # Generate model recommendations
            self.model_recommendations = self._generate_model_recommendations()
            
            return {
                "hardware_info": self.hardware_info,
                "performance_tier": self.performance_tier,
                "model_recommendations": self.model_recommendations,
                "detection_timestamp": self._get_timestamp()
            }
            
        except Exception as e:
            logger.error(f"Hardware detection failed: {e}")
            return self._fallback_config()
    
    def _detect_system_info(self) -> Dict:
        """Detect system information"""
        try:
            return {
                "platform": platform.system(),
                "release": platform.release(),
                "version": platform.version(),
                "machine": platform.machine(),
                "processor": platform.processor(),
                "python_version": platform.python_version(),
                "architecture": platform.architecture()[0]
            }
        except Exception as e:
            logger.error(f"System detection failed: {e}")
            return {"platform": "unknown", "error": str(e)}
    
    def _detect_gpu_info(self) -> Dict:
        """Detect GPU information with NVIDIA, AMD, and Intel support"""
        gpu_info = {
            "nvidia": [],
            "amd": [],
            "intel": [],
            "total_vram_gb": 0,
            "primary_gpu": None,
            "compute_capability": None
        }
        
        # NVIDIA Detection
        try:
            result = subprocess.run(['nvidia-smi', '--query-gpu=name,memory.total,driver_version,compute_cap', 
                                   '--format=csv,noheader,nounits'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        parts = line.split(', ')
                        if len(parts) >= 4:
                            name, memory, driver, compute_cap = parts[:4]
                            vram_gb = int(memory) / 1024
                            gpu_info["nvidia"].append({
                                "name": name.strip(),
                                "vram_mb": int(memory),
                                "vram_gb": round(vram_gb, 1),
                                "driver_version": driver.strip(),
                                "compute_capability": compute_cap.strip()
                            })
                            gpu_info["total_vram_gb"] += vram_gb
                            
                            if not gpu_info["primary_gpu"]:
                                gpu_info["primary_gpu"] = name.strip()
                                gpu_info["compute_capability"] = compute_cap.strip()
        except Exception as e:
            logger.debug(f"NVIDIA detection failed: {e}")
        
        # Windows GPU Detection (fallback)
        if not gpu_info["nvidia"] and platform.system() == "Windows":
            try:
                result = subprocess.run(['wmic', 'path', 'win32_VideoController', 'get', 'name,AdapterRAM'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')[1:]  # Skip header
                    for line in lines:
                        if line.strip():
                            parts = line.strip().split()
                            if len(parts) >= 2:
                                adapter_ram = parts[0] if parts[0].isdigit() else "0"
                                name = " ".join(parts[1:]) if len(parts) > 1 else "Unknown GPU"
                                
                                if "nvidia" in name.lower():
                                    vram_gb = int(adapter_ram) / (1024**3) if adapter_ram.isdigit() and int(adapter_ram) > 0 else 0
                                    gpu_info["nvidia"].append({
                                        "name": name,
                                        "vram_mb": int(adapter_ram) / (1024**2) if adapter_ram.isdigit() else 0,
                                        "vram_gb": round(vram_gb, 1),
                                        "driver_version": "unknown",
                                        "compute_capability": "unknown"
                                    })
                                    gpu_info["total_vram_gb"] += vram_gb
                                    if not gpu_info["primary_gpu"]:
                                        gpu_info["primary_gpu"] = name
            except Exception as e:
                logger.debug(f"Windows GPU detection failed: {e}")
        
        # AMD Detection (basic)
        try:
            if platform.system() == "Linux":
                result = subprocess.run(['rocm-smi', '--showmeminfo', 'vram'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    # Parse AMD GPU info
                    pass  # TODO: Implement AMD parsing
        except Exception:
            pass
        
        return gpu_info
    
    def _detect_cpu_info(self) -> Dict:
        """Detect CPU information"""
        try:
            import psutil
            cpu_info = {
                "model": platform.processor(),
                "cores_physical": psutil.cpu_count(logical=False),
                "cores_logical": psutil.cpu_count(logical=True),
                "max_frequency_mhz": psutil.cpu_freq().max if psutil.cpu_freq() else 0,
                "current_frequency_mhz": psutil.cpu_freq().current if psutil.cpu_freq() else 0,
                "usage_percent": psutil.cpu_percent(interval=1)
            }
            
            # Detect CPU features
            if platform.system() == "Windows":
                try:
                    result = subprocess.run(['wmic', 'cpu', 'get', 'name,maxclockspeed,numberofcores,numberoflogicalprocessors'], 
                                          capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        lines = result.stdout.strip().split('\n')[1:]
                        for line in lines:
                            if line.strip():
                                parts = line.strip().split()
                                if len(parts) >= 4:
                                    cpu_info["max_clock_speed"] = int(parts[0]) if parts[0].isdigit() else 0
                                    cpu_info["name"] = " ".join(parts[3:]) if len(parts) > 3 else "Unknown CPU"
                except Exception:
                    pass
            
            return cpu_info
            
        except ImportError:
            logger.warning("psutil not available, using basic CPU detection")
            return {
                "model": platform.processor(),
                "cores_physical": os.cpu_count(),
                "cores_logical": os.cpu_count(),
                "warning": "Limited CPU info - install psutil for detailed detection"
            }
        except Exception as e:
            logger.error(f"CPU detection failed: {e}")
            return {"error": str(e)}
    
    def _detect_memory_info(self) -> Dict:
        """Detect system memory information"""
        try:
            import psutil
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            return {
                "total_gb": round(memory.total / (1024**3), 1),
                "available_gb": round(memory.available / (1024**3), 1),
                "used_gb": round(memory.used / (1024**3), 1),
                "usage_percent": memory.percent,
                "swap_total_gb": round(swap.total / (1024**3), 1),
                "swap_used_gb": round(swap.used / (1024**3), 1),
                "swap_usage_percent": swap.percent
            }
        except ImportError:
            # Fallback for Windows without psutil
            if platform.system() == "Windows":
                try:
                    result = subprocess.run(['wmic', 'computersystem', 'get', 'TotalPhysicalMemory'], 
                                          capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        lines = result.stdout.strip().split('\n')
                        for line in lines[1:]:
                            if line.strip().isdigit():
                                total_bytes = int(line.strip())
                                total_gb = round(total_bytes / (1024**3), 1)
                                return {
                                    "total_gb": total_gb,
                                    "warning": "Limited memory info - install psutil for detailed detection"
                                }
                except Exception:
                    pass
            
            return {"error": "Could not detect memory - install psutil"}
        except Exception as e:
            logger.error(f"Memory detection failed: {e}")
            return {"error": str(e)}
    
    def _detect_storage_info(self) -> Dict:
        """Detect storage information"""
        try:
            import psutil
            storage_info = {
                "disks": [],
                "total_space_gb": 0,
                "free_space_gb": 0
            }
            
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    disk_info = {
                        "device": partition.device,
                        "mountpoint": partition.mountpoint,
                        "fstype": partition.fstype,
                        "total_gb": round(usage.total / (1024**3), 1),
                        "used_gb": round(usage.used / (1024**3), 1),
                        "free_gb": round(usage.free / (1024**3), 1),
                        "usage_percent": round((usage.used / usage.total) * 100, 1)
                    }
                    storage_info["disks"].append(disk_info)
                    storage_info["total_space_gb"] += disk_info["total_gb"]
                    storage_info["free_space_gb"] += disk_info["free_gb"]
                except (PermissionError, FileNotFoundError):
                    continue
            
            return storage_info
        except ImportError:
            return {"error": "Storage detection requires psutil"}
        except Exception as e:
            logger.error(f"Storage detection failed: {e}")
            return {"error": str(e)}
    
    def _calculate_performance_tier(self) -> str:
        """Calculate overall performance tier based on hardware - Universal for any system"""
        try:
            gpu_info = self.hardware_info.get("gpu", {})
            memory_info = self.hardware_info.get("memory", {})
            cpu_info = self.hardware_info.get("cpu", {})
            
            total_vram = gpu_info.get("total_vram_gb", 0)
            total_ram = memory_info.get("total_gb", 0)
            cpu_cores = cpu_info.get("cores_logical", 0)
            primary_gpu = gpu_info.get("primary_gpu", "").lower()
            
            # Enterprise/Workstation tier (RTX 4090, H100, A100, etc.)
            if (total_vram >= 20 and total_ram >= 64) or "h100" in primary_gpu or "a100" in primary_gpu:
                return "enterprise"
            # Enthusiast tier (RTX 4080/4070 Ti, RTX 3080 Ti/3090, etc.)
            elif (total_vram >= 12 and total_ram >= 32 and cpu_cores >= 8) or "4080" in primary_gpu or "4090" in primary_gpu or "3090" in primary_gpu:
                return "enthusiast"
            # High-end tier (RTX 4070, RTX 3080, RTX 3070, RX 7800 XT, etc.)
            elif (total_vram >= 8 and total_ram >= 16 and cpu_cores >= 6) or any(x in primary_gpu for x in ["4070", "3080", "3070", "7800", "6800"]):
                return "high_end"
            # Mid-range tier (RTX 4060, RTX 3060, RX 6600, GTX 1070, etc.)
            elif (total_vram >= 6 and total_ram >= 12 and cpu_cores >= 4) or any(x in primary_gpu for x in ["4060", "3060", "6600", "1070", "1080"]):
                return "mid_range"
            # Budget tier (GTX 1650, RX 5500, integrated graphics with decent specs)
            elif (total_vram >= 4 and total_ram >= 8 and cpu_cores >= 4) or any(x in primary_gpu for x in ["1650", "1660", "5500", "5600"]):
                return "budget"
            # Low-end tier (integrated graphics, old GPUs)
            elif total_vram >= 2 or total_ram >= 4:
                return "low_end"
            # Ultra-low tier (very old systems, minimal specs)
            else:
                return "ultra_low"
                
        except Exception as e:
            logger.error(f"Performance tier calculation failed: {e}")
            return "unknown"
    
    def _generate_model_recommendations(self) -> Dict:
        """Generate model recommendations based on detected hardware - Universal optimization"""
        try:
            gpu_info = self.hardware_info.get("gpu", {})
            memory_info = self.hardware_info.get("memory", {})
            total_vram = gpu_info.get("total_vram_gb", 0)
            total_ram = memory_info.get("total_gb", 0)
            tier = self.performance_tier
            
            recommendations = {
                "local_models_capable": [],
                "main_brain_candidates": [],
                "max_vram_allocation": 0,
                "recommended_quantization": "Q4_K_M",
                "concurrent_models": 1
            }
            
            if tier == "enterprise":
                # Workstation/Data Center GPUs (H100, A100, RTX 4090, etc.)
                recommendations.update({
                    "local_models_capable": [
                        "qwen/qwen3-coder-30b",
                        "meta/llama-3-70b-instruct",
                        "mistral/mixtral-8x22b-instruct",
                        "qwen/qwen2.5-coder-32b",
                        "deepseek/deepseek-coder-33b"
                    ],
                    "main_brain_candidates": [
                        "qwen/qwen3-coder-30b",
                        "meta/llama-3-70b-instruct",
                        "qwen/qwen2.5-coder-32b"
                    ],
                    "max_vram_allocation": max(16, total_vram - 4),
                    "recommended_quantization": "Q8_0",
                    "concurrent_models": 4
                })
            elif tier == "enthusiast":
                # High-end consumer (RTX 3090/4080/4070Ti, etc.)
                recommendations.update({
                    "local_models_capable": [
                        "qwen/qwen3-coder-14b",
                        "meta/llama-3-13b-instruct",
                        "mistral/mixtral-8x7b-instruct",
                        "qwen/qwen2.5-coder-14b",
                        "google/gemma-2-27b"
                    ],
                    "main_brain_candidates": [
                        "qwen/qwen3-coder-14b",
                        "meta/llama-3-13b-instruct",
                        "google/gemma-2-27b"
                    ],
                    "max_vram_allocation": max(10, total_vram - 2),
                    "recommended_quantization": "Q6_K",
                    "concurrent_models": 3
                })
            elif tier == "high_end":
                # Upper mid-range (RTX 3080/4070/3070, RX 7800 XT, etc.)
                recommendations.update({
                    "local_models_capable": [
                        "qwen/qwen3-coder-7b",
                        "google/gemma-2-9b-it", 
                        "microsoft/phi-3-medium",
                        "meta/llama-3-8b-instruct",
                        "qwen/qwen2.5-coder-7b"
                    ],
                    "main_brain_candidates": [
                        "qwen/qwen3-coder-7b",
                        "google/gemma-2-9b-it",
                        "microsoft/phi-3-medium"
                    ],
                    "max_vram_allocation": max(6, total_vram - 2),
                    "recommended_quantization": "Q6_K",
                    "concurrent_models": 3
                })
            elif tier == "mid_range":
                # Mid-range (RTX 3060/4060, RX 6600, etc.)
                recommendations.update({
                    "local_models_capable": [
                        "microsoft/phi-3-mini",
                        "google/gemma-2-2b",
                        "qwen/qwen2.5-coder-3b",
                        "microsoft/phi-3-small",
                        "meta/llama-3-3b"
                    ],
                    "main_brain_candidates": [
                        "microsoft/phi-3-mini",
                        "google/gemma-2-2b",
                        "qwen/qwen2.5-coder-3b"
                    ],
                    "max_vram_allocation": max(4, total_vram - 1.5),
                    "recommended_quantization": "Q5_K_M",
                    "concurrent_models": 2
                })
            elif tier == "budget":
                # Budget GPUs (GTX 1650, RX 5500, etc.)
                recommendations.update({
                    "local_models_capable": [
                        "microsoft/phi-3-mini",
                        "google/gemma-2-2b",
                        "qwen/qwen2.5-coder-1.5b",
                        "microsoft/phi-2"
                    ],
                    "main_brain_candidates": [
                        "microsoft/phi-3-mini",
                        "google/gemma-2-2b"
                    ],
                    "max_vram_allocation": max(3, total_vram - 1),
                    "recommended_quantization": "Q4_K_M",
                    "concurrent_models": 2
                })
            elif tier == "low_end":
                # Low-end/integrated graphics
                recommendations.update({
                    "local_models_capable": [
                        "microsoft/phi-3-mini",
                        "google/gemma-2-2b",
                        "qwen/qwen2.5-coder-1.5b"
                    ],
                    "main_brain_candidates": [
                        "microsoft/phi-3-mini",
                        "google/gemma-2-2b"
                    ],
                    "max_vram_allocation": max(2, total_vram - 1),
                    "recommended_quantization": "Q4_K_M",
                    "concurrent_models": 1
                })
            else:
                # Ultra-low or unknown hardware
                recommendations.update({
                    "local_models_capable": [
                        "microsoft/phi-2",
                        "google/gemma-2-2b",
                        "qwen/qwen2.5-0.5b"
                    ],
                    "main_brain_candidates": [
                        "microsoft/phi-2"
                    ],
                    "max_vram_allocation": max(1, total_vram - 0.5),
                    "recommended_quantization": "Q3_K_S",
                    "concurrent_models": 1
                })
            
            # Universal fallback model that works on almost any system
            recommendations["local_fallback_model"] = "microsoft/phi-3-mini-4k-instruct-q4.gguf"
            
            # Adjust for low RAM systems
            if total_ram < 8:
                recommendations["concurrent_models"] = 1
                recommendations["max_vram_allocation"] = min(recommendations["max_vram_allocation"], 2)
            elif total_ram < 16:
                recommendations["concurrent_models"] = min(recommendations["concurrent_models"], 2)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Model recommendation generation failed: {e}")
            return self._fallback_model_config()
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def _fallback_config(self) -> Dict:
        """Return fallback configuration if detection fails"""
        return {
            "hardware_info": {
                "system": {"platform": platform.system(), "error": "Detection failed"},
                "gpu": {"total_vram_gb": 4, "error": "Could not detect GPU"},
                "cpu": {"cores_logical": 4, "error": "Could not detect CPU"},
                "memory": {"total_gb": 8, "error": "Could not detect memory"}
            },
            "performance_tier": "budget",
            "model_recommendations": self._fallback_model_config(),
            "detection_timestamp": self._get_timestamp(),
            "warning": "Using fallback configuration - hardware detection failed"
        }
    
    def _fallback_model_config(self) -> Dict:
        """Return fallback model configuration"""
        return {
            "local_models_capable": ["microsoft/phi-3-mini"],
            "main_brain_candidates": ["microsoft/phi-3-mini"],
            "max_vram_allocation": 2,
            "recommended_quantization": "Q4_K_M",
            "local_fallback_model": "nvidia_NVIDIA-Nemotron-Nano-9B-v2-GGUF/nvidia_NVIDIA-Nemotron-Nano-9B-v2-Q5_K_S.gguf"
        }
    
    def save_hardware_config(self, filepath: str = None) -> str:
        """Save hardware configuration to file"""
        if not filepath:
            filepath = os.path.join(os.getcwd(), "hardware_config.json")
        
        config = self.detect_all_hardware()
        
        try:
            with open(filepath, 'w') as f:
                json.dump(config, f, indent=2)
            logger.info(f"Hardware configuration saved to: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Failed to save hardware config: {e}")
            return ""

def detect_hardware() -> Dict:
    """Convenience function to detect hardware"""
    detector = HardwareDetector()
    return detector.detect_all_hardware()

def main():
    """Main function for command-line usage"""
    print("🔍 DuckBot Hardware Detection")
    print("=" * 50)
    
    detector = HardwareDetector()
    config = detector.detect_all_hardware()
    
    print("\n📊 Hardware Detection Results:")
    print(json.dumps(config, indent=2))
    
    # Save to file
    config_file = detector.save_hardware_config()
    if config_file:
        print(f"\n💾 Configuration saved to: {config_file}")
    
    print("\n🎯 Performance Tier:", config["performance_tier"])
    print("🧠 Recommended Models:", ", ".join(config["model_recommendations"]["main_brain_candidates"]))

if __name__ == "__main__":
    main()