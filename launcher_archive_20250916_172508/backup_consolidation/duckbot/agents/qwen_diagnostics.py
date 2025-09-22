#!/usr/bin/env python3
"""
Qwen-Code Integration for DuckBot Diagnostics
Uses qwen-code CLI tool for system analysis and diagnostics only
"""

import subprocess
import json
import os
import tempfile
from typing import Dict, List, Optional, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class QwenDiagnostics:
    """
    Wrapper for qwen-code CLI tool for diagnostics, analysis, and server management
    IMPORTANT: Analysis-focused with controlled server operations - no code modification
    """
    
    def __init__(self):
        self.qwen_available = self._check_qwen_installation()
        self.temp_dir = Path(tempfile.gettempdir()) / "duckbot_diagnostics"
        self.temp_dir.mkdir(exist_ok=True)
        self.system_prompt = self._get_duckbot_system_prompt()
        
    def _get_duckbot_system_prompt(self) -> str:
        """Default system prompt for DuckBot operations - keeps qwen-code focused"""
        return """You are assisting the DuckBot AI-managed crypto ecosystem. Your role is STRICTLY LIMITED to:

ALLOWED OPERATIONS:
- Analyze code structure and dependencies
- Diagnose error logs and system issues
- Provide performance analysis and recommendations
- Start/manage development servers when requested
- Monitor server health and analyze server logs
- Give project setup recommendations

PROHIBITED OPERATIONS:
- DO NOT modify, edit, or fix any code files
- DO NOT install or uninstall packages without explicit permission
- DO NOT make configuration changes
- DO NOT execute arbitrary commands
- DO NOT access external APIs or services without permission

CONTEXT: You are part of a sophisticated crypto trading ecosystem with AI routing, WebUI management, and automated service orchestration. Focus on diagnostics and analysis only.

IMPORTANT: Always ask for confirmation before performing any system operations beyond basic analysis."""
        
    def _check_qwen_installation(self) -> bool:
        """Check if qwen-code is installed and accessible"""
        try:
            result = subprocess.run(['qwen', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            return False
    
    def install_qwen_code(self) -> bool:
        """Install qwen-code via npm if Node.js is available"""
        try:
            # Check if npm is available
            subprocess.run(['npm', '--version'], capture_output=True, timeout=10)
            
            print("Installing qwen-code via npm...")
            result = subprocess.run(['npm', 'install', '-g', '@qwen-code/qwen-code@latest'],
                                  capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                self.qwen_available = True
                return True
            else:
                logger.error(f"Failed to install qwen-code: {result.stderr}")
                return False
                
        except (subprocess.TimeoutExpired, FileNotFoundError):
            logger.error("npm not available - cannot install qwen-code")
            return False
    
    def _run_qwen_command(self, cmd: List[str], timeout: int = 30) -> Optional[str]:
        """Run qwen command with system prompt and safety checks"""
        if not self.qwen_available:
            return None
            
        try:
            # Add system prompt to environment
            env = os.environ.copy()
            env['QWEN_SYSTEM_PROMPT'] = self.system_prompt
            
            result = subprocess.run(cmd, capture_output=True, text=True, 
                                  timeout=timeout, env=env)
            
            if result.returncode == 0:
                return result.stdout
            else:
                logger.error(f"Qwen command failed: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            logger.error(f"Qwen command timed out: {' '.join(cmd)}")
            return None
        except Exception as e:
            logger.error(f"Qwen command error: {e}")
            return None

    def analyze_codebase_structure(self, project_path: str) -> Optional[str]:
        """Analyze project structure and dependencies"""
        cmd = ['qwen', 'analyze', '--structure', project_path]
        return self._run_qwen_command(cmd)
    
    def analyze_code_prompt(self, prompt: str) -> Optional[str]:
        """Use Qwen Code tools to analyze a coding prompt or code snippet"""
        if not self.qwen_available:
            return None
            
        try:
            # Create a temporary file with the prompt/code for analysis
            temp_file = self.temp_dir / "code_analysis.txt"
            temp_file.write_text(prompt, encoding='utf-8')
            
            # Use qwen-code to analyze the prompt - try different commands
            analysis_commands = [
                ['qwen', 'analyze', str(temp_file)],
                ['qwen', 'code', '--analyze', str(temp_file)],
                ['qwen', '--file', str(temp_file), '--task', 'analyze']
            ]
            
            for cmd in analysis_commands:
                try:
                    result = self._run_qwen_command(cmd, timeout=30)
                    if result and result.strip():
                        return result.strip()
                except Exception:
                    continue
                    
            # Fallback: Direct qwen command with the prompt as argument
            if len(prompt) < 1000:  # Only for shorter prompts
                cmd = ['qwen', '--prompt', f"Analyze this code: {prompt}"]
                result = self._run_qwen_command(cmd, timeout=20)
                if result:
                    return result.strip()
                    
        except Exception as e:
            logger.warning(f"Qwen Code analysis failed: {e}")
            
        return None
    
    def diagnose_error_logs(self, log_content: str) -> Optional[str]:
        """Analyze error logs for patterns and potential causes"""
        if not self.qwen_available:
            return None
            
        try:
            # Create temporary file with log content
            log_file = self.temp_dir / "error_analysis.log"
            log_file.write_text(log_content)
            
            cmd = ['qwen', 'diagnose', '--logs', str(log_file)]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return result.stdout
            else:
                # If diagnose command doesn't exist, try general analysis
                cmd = ['qwen', 'explain', str(log_file)]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                return result.stdout if result.returncode == 0 else None
                
        except subprocess.TimeoutExpired:
            logger.error("Qwen log diagnosis timed out")
            return None
        finally:
            # Clean up temp file
            if log_file.exists():
                log_file.unlink()
    
    def analyze_performance_bottlenecks(self, code_content: str, file_extension: str = "py") -> Optional[str]:
        """Analyze code for performance issues (read-only analysis)"""
        if not self.qwen_available:
            return None
            
        try:
            # Create temporary file with code content
            code_file = self.temp_dir / f"analysis.{file_extension}"
            code_file.write_text(code_content)
            
            cmd = ['qwen', 'analyze', '--performance', str(code_file)]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return result.stdout
            else:
                # Fallback to general code explanation
                cmd = ['qwen', 'explain', str(code_file)]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                return result.stdout if result.returncode == 0 else None
                
        except subprocess.TimeoutExpired:
            logger.error("Qwen performance analysis timed out")
            return None
        finally:
            # Clean up temp file
            if code_file.exists():
                code_file.unlink()
    
    def get_system_recommendations(self, system_info: Dict[str, Any]) -> Optional[str]:
        """Get system optimization recommendations based on current state"""
        if not self.qwen_available:
            return None
            
        try:
            # Create temporary file with system info
            info_file = self.temp_dir / "system_info.json"
            info_file.write_text(json.dumps(system_info, indent=2))
            
            # Use qwen to analyze system configuration
            cmd = ['qwen', 'analyze', str(info_file)]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return result.stdout
            else:
                return None
                
        except subprocess.TimeoutExpired:
            logger.error("Qwen system analysis timed out")
            return None
        finally:
            # Clean up temp file
            if info_file.exists():
                info_file.unlink()
    
    def is_available(self) -> bool:
        """Check if qwen-code is available for use"""
        return self.qwen_available
    
    def check_existing_servers(self, port: int = None) -> Dict[str, Any]:
        """Check for existing servers on common development ports"""
        import psutil
        import socket
        
        common_ports = [3000, 5000, 8000, 8080, 3001, 5173, 4200] if port is None else [port]
        running_servers = []
        
        for p in common_ports:
            try:
                # Check if port is in use
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    result = sock.connect_ex(('localhost', p))
                    if result == 0:  # Port is open
                        # Find process using the port
                        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                            try:
                                connections = proc.connections()
                                for conn in connections:
                                    if conn.laddr.port == p:
                                        running_servers.append({
                                            'port': p,
                                            'pid': proc.info['pid'],
                                            'name': proc.info['name'],
                                            'cmdline': ' '.join(proc.info['cmdline'][:3])  # First 3 args
                                        })
                                        break
                            except (psutil.NoSuchProcess, psutil.AccessDenied):
                                continue
            except Exception:
                continue
                
        return {'running_servers': running_servers}
    
    def stop_server_by_pid(self, pid: int) -> bool:
        """Stop a server process by PID"""
        try:
            import psutil
            process = psutil.Process(pid)
            process.terminate()
            # Wait up to 5 seconds for graceful shutdown
            try:
                process.wait(timeout=5)
            except psutil.TimeoutExpired:
                # Force kill if it doesn't stop gracefully
                process.kill()
                process.wait()
            logger.info(f"Successfully stopped server with PID: {pid}")
            return True
        except Exception as e:
            logger.error(f"Failed to stop server PID {pid}: {e}")
            return False
    
    def start_development_server(self, project_path: str, server_type: str = "auto", port: int = None, 
                                force_restart: bool = False) -> Dict[str, Any]:
        """Start a development server using qwen-code's server capabilities"""
        if not self.qwen_available:
            return {"error": "qwen-code not available"}
            
        # Check for existing servers
        existing = self.check_existing_servers(port)
        
        if existing['running_servers'] and not force_restart:
            return {
                "status": "existing_server_found",
                "existing_servers": existing['running_servers'],
                "message": "Server already running. Use force_restart=True to replace it.",
                "actions": ["connect_to_existing", "stop_and_restart"]
            }
        
        # Stop existing servers if force_restart is True
        if force_restart and existing['running_servers']:
            for server in existing['running_servers']:
                self.stop_server_by_pid(server['pid'])
                
        try:
            cmd = ['qwen', 'serve', project_path]
            if server_type != "auto":
                cmd.extend(['--type', server_type])
            if port:
                cmd.extend(['--port', str(port)])
            
            # Start server in background
            process = subprocess.Popen(cmd, cwd=project_path)
            logger.info(f"Started development server with PID: {process.pid}")
            
            return {
                "status": "started",
                "pid": process.pid,
                "process": process,
                "project_path": project_path,
                "server_type": server_type
            }
            
        except Exception as e:
            logger.error(f"Failed to start development server: {e}")
            return {"error": str(e)}
    
    def check_server_health(self, url: str, timeout: int = 10) -> Dict[str, Any]:
        """Check if a server is running and responsive"""
        try:
            import requests
            response = requests.get(url, timeout=timeout)
            return {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds()
            }
        except Exception as e:
            return {
                "status": "unreachable",
                "error": str(e),
                "response_time": None
            }
    
    def analyze_server_logs(self, log_path: str) -> Optional[str]:
        """Analyze server logs for issues and patterns"""
        if not self.qwen_available:
            return None
            
        try:
            cmd = ['qwen', 'analyze', '--logs', '--server', log_path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return result.stdout
            else:
                # Fallback to general log analysis
                return self.diagnose_error_logs(Path(log_path).read_text())
                
        except subprocess.TimeoutExpired:
            logger.error("Qwen server log analysis timed out")
            return None
        except Exception as e:
            logger.error(f"Server log analysis failed: {e}")
            return None
    
    def get_project_recommendations(self, project_path: str) -> Optional[str]:
        """Get recommendations for project setup and configuration"""
        if not self.qwen_available:
            return None
            
        try:
            cmd = ['qwen', 'recommend', project_path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return result.stdout
            else:
                # Fallback to structure analysis
                return self.analyze_codebase_structure(project_path)
                
        except subprocess.TimeoutExpired:
            logger.error("Qwen project recommendations timed out")
            return None
        except Exception as e:
            logger.error(f"Project recommendations failed: {e}")
            return None
    
    def get_diagnostic_summary(self) -> Dict[str, Any]:
        """Get summary of diagnostic capabilities"""
        return {
            "qwen_available": self.qwen_available,
            "capabilities": [
                "codebase_structure_analysis",
                "error_log_diagnosis", 
                "performance_bottleneck_detection",
                "system_recommendations",
                "development_server_startup",
                "server_health_monitoring",
                "server_log_analysis",
                "project_recommendations"
            ] if self.qwen_available else [],
            "mode": "analysis_and_server_management",
            "auto_fix_disabled": True,
            "server_management_enabled": True
        }