#!/usr/bin/env python3
"""
[EMOJI]️ DuckBot Server Management System
Comprehensive server and service management for the DuckBot ecosystem
"""

import subprocess
import psutil
import time
import json
import os
import signal
import shlex
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging
import threading
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

# Import action and reasoning logger
try:
    from .action_reasoning_logger import action_logger
    ACTION_LOGGING_AVAILABLE = True
except ImportError:
    ACTION_LOGGING_AVAILABLE = False

class ServiceStatus(Enum):
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"
    UNKNOWN = "unknown"

@dataclass
class ServiceInfo:
    name: str
    display_name: str
    port: int
    pid: Optional[int] = None
    status: ServiceStatus = ServiceStatus.STOPPED
    url: Optional[str] = None
    command: Optional[str] = None
    working_dir: Optional[str] = None
    log_file: Optional[str] = None
    auto_restart: bool = False
    dependencies: List[str] = None

class ServerManager:
    """Comprehensive server and service management"""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.services = self._initialize_services()
        self.running_processes = {}
        self.monitor_thread = None
        self.monitoring = False
        
    def _get_n8n_command(self) -> str:
        """Get the correct n8n command for Windows PATH issues"""
        # Try different possible n8n locations on Windows
        possible_paths = [
            "n8n",  # If in PATH
            os.path.expanduser(r"~\AppData\Roaming\npm\n8n.cmd"),
            r"C:\Program Files\nodejs\n8n.cmd",
            r"C:\Users\%USERNAME%\AppData\Roaming\npm\n8n.cmd"
        ]
        
        for cmd in possible_paths:
            try:
                # Test if command works
                result = subprocess.run([cmd, "--version"], 
                                      capture_output=True, text=True, timeout=5, shell=True)
                if result.returncode == 0:
                    return f"{cmd}"
            except:
                continue
        
        # Default fallback
        return "n8n"
        
    def _initialize_services(self) -> Dict[str, ServiceInfo]:
        """Initialize all DuckBot ecosystem services"""
        return {
            "lm_studio": ServiceInfo(
                name="lm_studio",
                display_name="LM Studio Server",
                port=1234,
                url="http://localhost:1234",
                command="",  # LM Studio managed separately
                auto_restart=False
            ),
            "comfyui": ServiceInfo(
                name="comfyui",
                display_name="ComfyUI Image Generation",
                port=8188,
                url="http://localhost:8188",
                command=f"python start_comfyui.py",
                working_dir=str(self.base_dir),
                log_file="comfyui.log",
                auto_restart=True
            ),
            "webui": ServiceInfo(
                name="webui",
                display_name="DuckBot Professional WebUI",
                port=8787,
                url="http://localhost:8787",
                command=f"python -m duckbot.webui",
                working_dir=str(self.base_dir),
                log_file="webui.log",
                auto_restart=True
            ),
            "n8n": ServiceInfo(
                name="n8n",
                display_name="n8n Workflow Automation",
                port=5678,
                url="http://localhost:5678",
                command=self._get_n8n_command(),
                log_file="n8n.log",
                auto_restart=True
            ),
            "open_notebook": ServiceInfo(
                name="open_notebook",
                display_name="Open Notebook AI Interface",
                port=8502,
                url="http://localhost:8502",
                command=f"python {self.base_dir}/open-notebook/app_home.py",
                working_dir=str(self.base_dir / "open-notebook"),
                log_file="open_notebook.log",
                auto_restart=True
            ),
            "jupyter": ServiceInfo(
                name="jupyter",
                display_name="Jupyter Notebook Server",
                port=8889,
                url="http://localhost:8889",
                command="jupyter notebook --port=8889 --no-browser --allow-root",
                working_dir=str(self.base_dir / "notebooks"),
                log_file="jupyter.log",
                auto_restart=True
            ),
            "discord_bot": ServiceInfo(
                name="discord_bot",
                display_name="DuckBot Discord Bot",
                port=None,  # No web port
                command=f"python {self.base_dir}/ai_ecosystem_manager.py",
                working_dir=str(self.base_dir),
                log_file="discord_bot.log",
                auto_restart=True
            )
        }
    
    def get_service_status(self, service_name: str) -> ServiceInfo:
        """Get current status of a service"""
        if service_name not in self.services:
            return ServiceInfo(service_name, "Unknown Service", 0, status=ServiceStatus.UNKNOWN)
            
        service = self.services[service_name]
        
        # Check if process is running
        if service.port:
            service.status = ServiceStatus.RUNNING if self._is_port_open(service.port) else ServiceStatus.STOPPED
        elif service.pid:
            service.status = ServiceStatus.RUNNING if self._is_process_running(service.pid) else ServiceStatus.STOPPED
        else:
            service.status = ServiceStatus.UNKNOWN
            
        return service
    
    def start_service(self, service_name: str) -> Tuple[bool, str]:
        """Start a specific service"""
        start_time = time.time()
        
        if service_name not in self.services:
            result = (False, f"Unknown service: {service_name}")
            if ACTION_LOGGING_AVAILABLE:
                action_logger.log_server_management_action(
                    server_name=service_name,
                    action="start",
                    reasoning=f"Attempted to start unknown service: {service_name}",
                    outcome="Failed - Unknown service",
                    execution_time_ms=int((time.time() - start_time) * 1000)
                )
            return result
            
        service = self.services[service_name]
        
        # Check if already running
        if self.get_service_status(service_name).status == ServiceStatus.RUNNING:
            result = (True, f"{service.display_name} is already running")
            if ACTION_LOGGING_AVAILABLE:
                action_logger.log_server_management_action(
                    server_name=service_name,
                    action="start",
                    reasoning=f"Service {service.display_name} was already running on port {service.port}",
                    outcome="Success - Already running",
                    execution_time_ms=int((time.time() - start_time) * 1000)
                )
            return result
        
        try:
            # Log the start attempt
            if ACTION_LOGGING_AVAILABLE:
                action_logger.log_server_management_action(
                    server_name=service_name,
                    action="start",
                    reasoning=f"Starting {service.display_name} on port {service.port} as requested by AI or user",
                    outcome="Starting...",
                    execution_time_ms=int((time.time() - start_time) * 1000)
                )
            
            # Special handling for LM Studio
            if service_name == "lm_studio":
                return self._start_lm_studio()
            
            # Start the service
            service.status = ServiceStatus.STARTING
            
            env = os.environ.copy()
            if service.working_dir:
                os.makedirs(service.working_dir, exist_ok=True)
                
            # Create log file directory
            if service.log_file:
                log_path = Path(service.working_dir or self.base_dir) / service.log_file
                log_path.parent.mkdir(exist_ok=True)
                
                # Start process with logging
                with open(log_path, "a", encoding="utf-8") as log_f:
                    use_shell = (os.name == 'nt') and (
                        service_name == 'n8n' or
                        (service.command or '').lower().endswith('.cmd') or
                        (service.command or '').lower().endswith('.bat')
                    )
                    args = service.command if use_shell else shlex.split(service.command or '', posix=(os.name != 'nt'))
                    process = subprocess.Popen(
                        args,
                        cwd=service.working_dir,
                        env=env,
                        stdout=log_f,
                        stderr=subprocess.STDOUT,
                        shell=use_shell,
                        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
                    )
            else:
                use_shell = (os.name == 'nt') and (
                    service_name == 'n8n' or
                    (service.command or '').lower().endswith('.cmd') or
                    (service.command or '').lower().endswith('.bat')
                )
                args = service.command if use_shell else shlex.split(service.command or '', posix=(os.name != 'nt'))
                process = subprocess.Popen(
                    args,
                    cwd=service.working_dir,
                    env=env,
                    shell=use_shell,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
                )
            
            service.pid = process.pid
            self.running_processes[service_name] = process
            
            # Wait for startup; n8n can take longer to listen
            max_wait = 20 if service_name == 'n8n' else 4
            waited = 0
            while waited < max_wait:
                time.sleep(1)
                waited += 1
                if service.port and self._is_port_open(service.port):
                    break

            # Verify it started
            if service.port and self._is_port_open(service.port):
                service.status = ServiceStatus.RUNNING
                result = (True, f"{service.display_name} started successfully on port {service.port}")
                
                if ACTION_LOGGING_AVAILABLE:
                    action_logger.log_server_management_action(
                        server_name=service_name,
                        action="start",
                        reasoning=f"Successfully started {service.display_name} and verified it's listening on port {service.port}",
                        outcome=f"Success - Running on port {service.port}",
                        execution_time_ms=int((time.time() - start_time) * 1000)
                    )
                return result
                
            elif not service.port and self._is_process_running(service.pid):
                service.status = ServiceStatus.RUNNING
                result = (True, f"{service.display_name} started successfully (PID: {service.pid})")
                
                if ACTION_LOGGING_AVAILABLE:
                    action_logger.log_server_management_action(
                        server_name=service_name,
                        action="start",
                        reasoning=f"Successfully started {service.display_name} with PID {service.pid}",
                        outcome=f"Success - Running with PID {service.pid}",
                        execution_time_ms=int((time.time() - start_time) * 1000)
                    )
                return result
            else:
                service.status = ServiceStatus.ERROR
                result = (False, f"{service.display_name} failed to start properly")
                
                if ACTION_LOGGING_AVAILABLE:
                    action_logger.log_server_management_action(
                        server_name=service_name,
                        action="start",
                        reasoning=f"Process started but service is not responding on expected port {service.port}",
                        outcome="Failed - Not responding",
                        execution_time_ms=int((time.time() - start_time) * 1000)
                    )
                return result
                
        except Exception as e:
            service.status = ServiceStatus.ERROR
            result = (False, f"Failed to start {service.display_name}: {str(e)}")
            
            if ACTION_LOGGING_AVAILABLE:
                action_logger.log_server_management_action(
                    server_name=service_name,
                    action="start",
                    reasoning=f"Exception occurred while starting service: {str(e)}",
                    outcome=f"Failed - Exception: {type(e).__name__}",
                    execution_time_ms=int((time.time() - start_time) * 1000)
                )
            return result
    
    def stop_service(self, service_name: str) -> Tuple[bool, str]:
        """Stop a specific service"""
        if service_name not in self.services:
            return False, f"Unknown service: {service_name}"
            
        service = self.services[service_name]
        
        try:
            service.status = ServiceStatus.STOPPING
            
            # Special handling for LM Studio
            if service_name == "lm_studio":
                return self._stop_lm_studio()
            
            # Stop the process
            if service_name in self.running_processes:
                process = self.running_processes[service_name]
                
                if os.name == 'nt':  # Windows
                    process.terminate()
                else:  # Unix-like
                    process.send_signal(signal.SIGTERM)
                
                # Wait for graceful shutdown
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    
                del self.running_processes[service_name]
            
            # Also kill by port if needed
            if service.port:
                self._kill_process_on_port(service.port)
            
            service.status = ServiceStatus.STOPPED
            service.pid = None
            
            return True, f"{service.display_name} stopped successfully"
            
        except Exception as e:
            service.status = ServiceStatus.ERROR
            return False, f"Failed to stop {service.display_name}: {str(e)}"
    
    def restart_service(self, service_name: str) -> Tuple[bool, str]:
        """Restart a specific service"""
        stop_success, stop_msg = self.stop_service(service_name)
        if not stop_success:
            return False, f"Failed to stop for restart: {stop_msg}"
            
        time.sleep(2)  # Brief pause
        
        start_success, start_msg = self.start_service(service_name)
        return start_success, f"Restart: {start_msg}"
    
    def get_all_service_status(self) -> Dict[str, ServiceInfo]:
        """Get status of all services"""
        status = {}
        for service_name in self.services:
            status[service_name] = self.get_service_status(service_name)
        return status
    
    def start_ecosystem(self) -> Tuple[bool, List[str]]:
        """Start the complete DuckBot ecosystem in proper order"""
        results = []
        
        # Start in dependency order
        startup_order = [
            "lm_studio",     # AI models first
            "comfyui",       # Image generation
            "n8n",           # Automation 
            "open_notebook", # Notebooks
            "jupyter",       # Jupyter
            "webui",         # Dashboard (depends on services above)
            "discord_bot"    # Bot last (uses all services)
        ]
        
        for service_name in startup_order:
            if service_name in self.services:
                success, msg = self.start_service(service_name)
                results.append(f"{service_name}: {msg}")
                if not success:
                    logger.warning(f"Failed to start {service_name}: {msg}")
                    
        overall_success = all("successfully" in result or "already running" in result for result in results)
        return overall_success, results
    
    def stop_ecosystem(self) -> Tuple[bool, List[str]]:
        """Stop the complete DuckBot ecosystem"""
        results = []
        
        # Stop in reverse order
        shutdown_order = [
            "discord_bot", "webui", "jupyter", "open_notebook", 
            "n8n", "comfyui", "lm_studio"
        ]
        
        for service_name in shutdown_order:
            if service_name in self.services:
                success, msg = self.stop_service(service_name)
                results.append(f"{service_name}: {msg}")
                
        overall_success = all("successfully" in result for result in results)
        return overall_success, results
    
    def _is_port_open(self, port: int) -> bool:
        """Check if a port is open/in use"""
        try:
            for conn in psutil.net_connections():
                if conn.laddr.port == port and conn.status == psutil.CONN_LISTEN:
                    return True
            return False
        except (psutil.AccessDenied, AttributeError):
            # Fallback method
            import socket
            try:
                sock = socket.create_connection(("localhost", port), timeout=1)
                sock.close()
                return True
            except (socket.error, ConnectionRefusedError):
                return False
    
    def _find_lm_studio_executable(self) -> Optional[str]:
        """Intelligently find LM Studio installation across different systems"""
        import glob
        from pathlib import Path
        
        # Common installation paths for different platforms
        search_paths = []
        
        if os.name == 'nt':  # Windows
            search_paths = [
                # Program Files locations
                "C:/Program Files/LM Studio/LM Studio.exe",
                "C:/Program Files (x86)/LM Studio/LM Studio.exe",
                # AppData locations (user-specific installs)
                os.path.expanduser("~/AppData/Local/LM Studio/LM Studio.exe"),
                os.path.expanduser("~/AppData/Roaming/LM Studio/LM Studio.exe"),
                # Portable installations
                "./LM Studio/LM Studio.exe",
                "../LM Studio/LM Studio.exe",
            ]
            # Also search all user directories
            try:
                for user_dir in glob.glob("C:/Users/*/AppData/Local/LM Studio/LM Studio.exe"):
                    search_paths.append(user_dir)
                for user_dir in glob.glob("C:/Users/*/AppData/Roaming/LM Studio/LM Studio.exe"):
                    search_paths.append(user_dir)
            except:
                pass
        
        elif os.name == 'posix':  # macOS/Linux
            if 'darwin' in os.uname().sysname.lower():  # macOS
                search_paths = [
                    "/Applications/LM Studio.app/Contents/MacOS/LM Studio",
                    os.path.expanduser("~/Applications/LM Studio.app/Contents/MacOS/LM Studio"),
                    "/usr/local/bin/lm-studio",
                    "/opt/lm-studio/lm-studio"
                ]
            else:  # Linux
                search_paths = [
                    "/usr/local/bin/lm-studio",
                    "/usr/bin/lm-studio",
                    "/opt/lm-studio/lm-studio",
                    os.path.expanduser("~/.local/bin/lm-studio"),
                    os.path.expanduser("~/Applications/lm-studio"),
                    "./lm-studio"
                ]
        
        # Check each path
        for path in search_paths:
            if os.path.isfile(path) and os.access(path, os.X_OK):
                logger.info(f"[OK] Found LM Studio at: {path}")
                return path
        
        # Try PATH-based search
        try:
            import shutil
            for cmd in ['lm-studio', 'lmstudio', 'LM Studio', 'LM_Studio']:
                path = shutil.which(cmd)
                if path:
                    logger.info(f"[OK] Found LM Studio in PATH: {path}")
                    return path
        except:
            pass
            
        logger.warning("[ERROR] Could not locate LM Studio installation")
        return None
    
    def _is_process_running(self, pid: int) -> bool:
        """Check if a process is running by PID"""
        try:
            return psutil.pid_exists(pid)
        except:
            return False
    
    def _kill_process_on_port(self, port: int):
        """Kill process listening on specific port"""
        try:
            for proc in psutil.process_iter(['pid', 'connections']):
                try:
                    for conn in proc.info['connections'] or []:
                        if conn.laddr.port == port:
                            psutil.Process(proc.info['pid']).terminate()
                except (psutil.AccessDenied, psutil.NoSuchProcess):
                    continue
        except Exception as e:
            logger.warning(f"Could not kill process on port {port}: {e}")
    
    def _start_lm_studio(self) -> Tuple[bool, str]:
        """Special handling for LM Studio startup"""
        try:
            # Check if LM Studio is already running
            if self._is_port_open(1234):
                return True, "LM Studio is already running"
            
            # Try to find and start LM Studio (cross-platform)
            lm_studio_path = self._find_lm_studio_executable()
            if lm_studio_path:
                try:
                    if os.name == 'nt':  # Windows
                        subprocess.Popen([lm_studio_path], shell=True)
                    else:  # macOS/Linux
                        subprocess.Popen([lm_studio_path])
                    
                    time.sleep(5)  # Give it time to start
                    if self._is_port_open(1234):
                        return True, f"LM Studio started successfully from {lm_studio_path}"
                except Exception as e:
                    pass
                        
            return False, "Could not find or start LM Studio - please start manually or check installation"
                
        except Exception as e:
            return False, f"LM Studio startup error: {str(e)}"
    
    def _stop_lm_studio(self) -> Tuple[bool, str]:
        """Special handling for LM Studio shutdown"""
        try:
            # LM Studio should be closed manually by user
            # We can only check if it's stopped
            if not self._is_port_open(1234):
                return True, "LM Studio is stopped"
            else:
                return False, "LM Studio is still running - please close manually"
        except Exception as e:
            return False, f"LM Studio stop check error: {str(e)}"
    
    def start_monitoring(self):
        """Start background service monitoring"""
        if self.monitoring:
            return
            
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop background service monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
    
    def _monitoring_loop(self):
        """Background monitoring loop for auto-restart"""
        while self.monitoring:
            try:
                for service_name, service in self.services.items():
                    if service.auto_restart:
                        status = self.get_service_status(service_name)
                        if status.status == ServiceStatus.STOPPED:
                            logger.info(f"Auto-restarting {service.display_name}")
                            self.start_service(service_name)
                            
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                time.sleep(10)

# Global server manager instance
server_manager = ServerManager()
