# duckbot/service_detector.py
import requests
import time
import subprocess
import psutil
import os
from typing import Dict, List, Optional, Tuple
from pathlib import Path

class ServiceDetector:
    """Detect and manage running services to avoid conflicts"""
    
    def __init__(self):
        self.services = {
            'lm_studio': {
                'ports': [1234],
                'health_endpoints': ['http://localhost:1234/v1/models'],
                'name': 'LM Studio',
                'process_keywords': ['lmstudio', 'lm-studio']
            },
            'comfyui': {
                'ports': [8188],
                'health_endpoints': ['http://localhost:8188'],
                'name': 'ComfyUI',
                'process_keywords': ['comfyui', 'comfy', 'main.py'],
                'local_paths': ['ComfyUI/main.py', 'ComfyUI_windows_portable_nvidia/ComfyUI/main.py']
            },
            'jupyter': {
                'ports': [8888, 8889],
                'health_endpoints': ['http://localhost:8888', 'http://localhost:8889'],
                'name': 'Jupyter',
                'process_keywords': ['jupyter-notebook', 'jupyter']
            },
            'n8n': {
                'ports': [5678],
                'health_endpoints': ['http://localhost:5678/healthz'],
                'name': 'n8n',
                'process_keywords': ['n8n']
            },
            'webui': {
                'ports': [8787],
                'health_endpoints': ['http://localhost:8787/healthz'],
                'name': 'DuckBot WebUI',
                'process_keywords': ['duckbot.webui', 'uvicorn']
            }
        }
    
    def check_port_in_use(self, port: int) -> bool:
        """Check if a specific port is in use"""
        for conn in psutil.net_connections():
            if conn.laddr.port == port and conn.status == psutil.CONN_LISTEN:
                return True
        return False
    
    def check_service_health(self, url: str, timeout: int = 3) -> Dict:
        """Check if service responds to health check"""
        try:
            response = requests.get(url, timeout=timeout)
            return {
                'status': 'healthy' if response.status_code == 200 else 'unhealthy',
                'status_code': response.status_code,
                'response_time': response.elapsed.total_seconds(),
                'reachable': True
            }
        except requests.exceptions.ConnectionError:
            return {'status': 'port_closed', 'reachable': False}
        except requests.exceptions.Timeout:
            return {'status': 'timeout', 'reachable': False}
        except Exception as e:
            return {'status': 'error', 'error': str(e), 'reachable': False}
    
    def find_process_by_keywords(self, keywords: List[str]) -> List[Dict]:
        """Find processes matching keywords"""
        matching_processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = ' '.join(proc.info['cmdline'] or []).lower()
                name = proc.info['name'].lower()
                
                for keyword in keywords:
                    if keyword in name or keyword in cmdline:
                        matching_processes.append({
                            'pid': proc.info['pid'],
                            'name': proc.info['name'],
                            'cmdline': proc.info['cmdline']
                        })
                        break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return matching_processes
    
    def detect_service_status(self, service_name: str) -> Dict:
        """Comprehensive service detection"""
        if service_name not in self.services:
            return {'status': 'unknown', 'service': service_name}
        
        service_config = self.services[service_name]
        result = {
            'service': service_name,
            'name': service_config['name'],
            'status': 'not_running',
            'ports_in_use': [],
            'health_checks': {},
            'processes': []
        }
        
        # Check ports
        for port in service_config['ports']:
            if self.check_port_in_use(port):
                result['ports_in_use'].append(port)
        
        # Check health endpoints
        for endpoint in service_config['health_endpoints']:
            health = self.check_service_health(endpoint)
            result['health_checks'][endpoint] = health
            
            if health.get('reachable') and health.get('status') == 'healthy':
                result['status'] = 'running_healthy'
            elif health.get('reachable'):
                result['status'] = 'running_unhealthy'
        
        # Check processes
        processes = self.find_process_by_keywords(service_config['process_keywords'])
        result['processes'] = processes
        
        if processes and result['status'] == 'not_running':
            result['status'] = 'process_detected'
        
        return result
    
    def get_all_service_status(self) -> Dict[str, Dict]:
        """Get status of all known services"""
        status = {}
        for service_name in self.services.keys():
            status[service_name] = self.detect_service_status(service_name)
        return status
    
    def can_start_service(self, service_name: str) -> Tuple[bool, str]:
        """Check if we can safely start a service"""
        status = self.detect_service_status(service_name)
        
        if status['status'] == 'running_healthy':
            return False, f"{status['name']} is already running and healthy - will connect to existing instance"
        
        if status['status'] == 'running_unhealthy':
            return False, f"{status['name']} is running but unhealthy - may need restart"
        
        if status['ports_in_use']:
            ports_str = ', '.join(map(str, status['ports_in_use']))
            return False, f"Required ports ({ports_str}) are already in use by another service"
        
        if status['processes']:
            return False, f"{status['name']} process detected but not responding - may need cleanup"
        
        return True, f"Safe to start {status['name']}"
    
    def get_startup_recommendations(self) -> Dict[str, str]:
        """Get recommendations for service startup"""
        recommendations = {}
        
        for service_name in self.services.keys():
            can_start, reason = self.can_start_service(service_name)
            recommendations[service_name] = {
                'can_start': can_start,
                'reason': reason,
                'action': 'start' if can_start else 'connect_or_skip'
            }
        
        return recommendations
    
    def wait_for_service_health(self, service_name: str, timeout: int = 30, check_interval: int = 2) -> bool:
        """Wait for a service to become healthy"""
        if service_name not in self.services:
            return False
        
        start_time = time.time()
        service_config = self.services[service_name]
        
        while time.time() - start_time < timeout:
            for endpoint in service_config['health_endpoints']:
                health = self.check_service_health(endpoint)
                if health.get('status') == 'healthy':
                    return True
            
            time.sleep(check_interval)
        
        return False
    
    def find_local_comfyui(self) -> Optional[str]:
        """Find local ComfyUI installation path"""
        from pathlib import Path
        
        base_path = Path.cwd()
        possible_paths = [
            base_path / "ComfyUI" / "main.py",
            base_path / "ComfyUI_windows_portable_nvidia" / "ComfyUI" / "main.py",
            base_path / "ComfyUI_windows_portable" / "ComfyUI" / "main.py"
        ]
        
        for path in possible_paths:
            if path.exists():
                return str(path.parent)
        
        return None
    
    def start_local_comfyui(self) -> Tuple[bool, str]:
        """Start local ComfyUI installation"""
        comfyui_path = self.find_local_comfyui()
        if not comfyui_path:
            return False, "Local ComfyUI installation not found"
        
        try:
            import subprocess
            import sys
            from pathlib import Path
            
            main_py = Path(comfyui_path) / "main.py"
            if not main_py.exists():
                return False, f"main.py not found at {main_py}"
            
            # Start ComfyUI in background
            cmd = [sys.executable, str(main_py), "--listen", "127.0.0.1", "--port", "8188"]
            process = subprocess.Popen(
                cmd,
                cwd=comfyui_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
            )
            
            # Wait a moment for startup
            time.sleep(2)
            
            # Check if it started successfully
            if self.wait_for_service_health('comfyui', timeout=15):
                return True, f"ComfyUI started successfully from {comfyui_path}"
            else:
                return False, "ComfyUI started but not responding to health checks"
                
        except Exception as e:
            return False, f"Failed to start ComfyUI: {str(e)}"
    
    def print_service_report(self):
        """Print a comprehensive service status report"""
        print("[SEARCH] DuckBot Service Detection Report")
        print("=" * 50)
        
        # Check for local ComfyUI
        comfyui_path = self.find_local_comfyui()
        if comfyui_path:
            print(f"\n[EMOJI] Local ComfyUI detected at: {comfyui_path}")
        
        status = self.get_all_service_status()
        recommendations = self.get_startup_recommendations()
        
        for service_name, service_status in status.items():
            rec = recommendations[service_name]
            
            print(f"\n[EMOJI] {service_status['name']}:")
            print(f"   Status: {service_status['status']}")
            print(f"   Action: {rec['action']}")
            print(f"   Reason: {rec['reason']}")
            
            if service_name == 'comfyui' and comfyui_path:
                print(f"   Local Path: {comfyui_path}")
            
            if service_status['ports_in_use']:
                print(f"   Ports in use: {service_status['ports_in_use']}")
            
            if service_status['processes']:
                print(f"   Processes found: {len(service_status['processes'])}")
        
        print("\n" + "=" * 50)

if __name__ == "__main__":
    # Test the service detector
    detector = ServiceDetector()
    detector.print_service_report()