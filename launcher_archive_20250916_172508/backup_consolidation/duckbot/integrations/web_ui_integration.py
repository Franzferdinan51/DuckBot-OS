#!/usr/bin/env python3
"""
Web-UI Integration for DuckBot
Integrates browser-use/web-ui for enhanced web interface capabilities
"""

import os
import json
import logging
import asyncio
import subprocess
import requests
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

try:
    # Web-UI integration (placeholder for actual implementation)
    WEB_UI_AVAILABLE = True
except ImportError:
    WEB_UI_AVAILABLE = False
    logger.warning("Web-UI integration not available")

@dataclass
class WebUIConfig:
    """Configuration for Web-UI integration"""
    host: str = "127.0.0.1"
    port: int = 7860  # Default Gradio port
    base_url: str = "http://127.0.0.1:7860"
    api_key: Optional[str] = None
    timeout: int = 30
    ssl_verify: bool = True

class WebUIIntegration:
    """DuckBot integration for browser-use/web-ui"""

    def __init__(self, config: Optional[WebUIConfig] = None):
        self.config = config or WebUIConfig()
        self.available = WEB_UI_AVAILABLE
        self.session = None
        
        if self.available:
            self._initialize_session()
        else:
            logger.warning("Web-UI integration not available")

    def _initialize_session(self):
        """Initialize HTTP session for Web-UI"""
        try:
            self.session = requests.Session()
            if self.config.api_key:
                self.session.headers.update({
                    "Authorization": f"Bearer {self.config.api_key}",
                    "X-API-Key": self.config.api_key
                })
            self.session.verify = self.config.ssl_verify
            logger.info("Web-UI integration session initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Web-UI session: {e}")
            self.available = False

    async def start_webui(self) -> Dict[str, Any]:
        """Start Web-UI server"""
        if not self.available:
            return {"success": False, "error": "Web-UI not available"}
            
        try:
            # Check if already running
            if await self._is_webui_running():
                return {"success": True, "message": "Web-UI already running", "url": self.config.base_url}
            
            # Start Web-UI process
            cmd = [
                "python",
                "-m",
                "webui",
                "--host", self.config.host,
                "--port", str(self.config.port)
            ]
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=Path(__file__).parent / "web-ui"
            )
            
            # Wait for startup
            await asyncio.sleep(5)
            
            if await self._is_webui_running():
                return {
                    "success": True,
                    "message": "Web-UI started successfully",
                    "url": self.config.base_url,
                    "pid": process.pid
                }
            else:
                return {
                    "success": False,
                    "error": "Web-UI failed to start",
                    "details": "Process may have exited"
                }
                
        except Exception as e:
            logger.error(f"Failed to start Web-UI: {e}")
            return {"success": False, "error": str(e)}

    async def stop_webui(self) -> Dict[str, Any]:
        """Stop Web-UI server"""
        if not self.available:
            return {"success": False, "error": "Web-UI not available"}
            
        try:
            # Check if running
            if not await self._is_webui_running():
                return {"success": True, "message": "Web-UI not running"}
            
            # Try graceful shutdown via API
            try:
                response = self.session.post(
                    f"{self.config.base_url}/api/shutdown",
                    timeout=self.config.timeout
                )
                if response.status_code == 200:
                    return {"success": True, "message": "Web-UI shut down successfully"}
            except:
                pass
            
            # If API shutdown fails, try killing process
            try:
                # This would require finding the process by port
                import psutil
                for proc in psutil.process_iter(['pid', 'name', 'connections']):
                    try:
                        for conn in proc.connections():
                            if conn.laddr.port == self.config.port:
                                proc.terminate()
                                proc.wait(timeout=10)
                                return {"success": True, "message": "Web-UI process terminated"}
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
                        continue
            except ImportError:
                pass
                
            return {"success": False, "error": "Failed to stop Web-UI"}
            
        except Exception as e:
            logger.error(f"Failed to stop Web-UI: {e}")
            return {"success": False, "error": str(e)}

    async def _is_webui_running(self) -> bool:
        """Check if Web-UI is running"""
        try:
            response = self.session.get(
                f"{self.config.base_url}/health",
                timeout=5
            )
            return response.status_code == 200
        except:
            return False

    async def get_webui_status(self) -> Dict[str, Any]:
        """Get Web-UI status"""
        if not self.available:
            return {"success": False, "error": "Web-UI not available"}
            
        try:
            running = await self._is_webui_running()
            
            status = {
                "success": True,
                "running": running,
                "url": self.config.base_url,
                "host": self.config.host,
                "port": self.config.port
            }
            
            if running:
                try:
                    response = self.session.get(
                        f"{self.config.base_url}/api/status",
                        timeout=self.config.timeout
                    )
                    if response.status_code == 200:
                        status.update(response.json())
                except:
                    pass
                    
            return status
            
        except Exception as e:
            logger.error(f"Failed to get Web-UI status: {e}")
            return {"success": False, "error": str(e)}

    async def execute_webui_task(self, task: str, parameters: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute task via Web-UI"""
        if not self.available:
            return {"success": False, "error": "Web-UI not available"}
            
        try:
            if not await self._is_webui_running():
                start_result = await self.start_webui()
                if not start_result["success"]:
                    return start_result
                    
            # Execute task via Web-UI API
            payload = {
                "task": task,
                "parameters": parameters or {}
            }
            
            response = self.session.post(
                f"{self.config.base_url}/api/task",
                json=payload,
                timeout=self.config.timeout
            )
            
            if response.status_code == 200:
                return {"success": True, "result": response.json()}
            else:
                return {
                    "success": False,
                    "error": f"Web-UI API error: {response.status_code}",
                    "details": response.text
                }
                
        except Exception as e:
            logger.error(f"Failed to execute Web-UI task: {e}")
            return {"success": False, "error": str(e)}

    async def get_webui_interface(self) -> Dict[str, Any]:
        """Get Web-UI interface information"""
        if not self.available:
            return {"success": False, "error": "Web-UI not available"}
            
        try:
            if not await self._is_webui_running():
                return {"success": False, "error": "Web-UI not running"}
                
            response = self.session.get(
                f"{self.config.base_url}/api/interface",
                timeout=self.config.timeout
            )
            
            if response.status_code == 200:
                return {"success": True, "interface": response.json()}
            else:
                return {
                    "success": False,
                    "error": f"Web-UI interface error: {response.status_code}",
                    "details": response.text
                }
                
        except Exception as e:
            logger.error(f"Failed to get Web-UI interface: {e}")
            return {"success": False, "error": str(e)}

    def get_status(self) -> Dict[str, Any]:
        """Get integration status"""
        return {
            "available": self.available,
            "configured": self.config is not None,
            "webui_running": asyncio.run(self._is_webui_running()) if self.available else False,
            "host": self.config.host if self.config else None,
            "port": self.config.port if self.config else None,
            "base_url": self.config.base_url if self.config else None
        }

# Global instance
webui_integration = WebUIIntegration()

async def initialize_webui() -> bool:
    """Initialize Web-UI integration"""
    global webui_integration
    webui_integration = WebUIIntegration()
    return webui_integration.available

async def start_webui() -> Dict[str, Any]:
    """Start Web-UI"""
    return await webui_integration.start_webui()

async def stop_webui() -> Dict[str, Any]:
    """Stop Web-UI"""
    return await webui_integration.stop_webui()

async def get_webui_status() -> Dict[str, Any]:
    """Get Web-UI status"""
    return await webui_integration.get_webui_status()

async def execute_webui_task(task: str, parameters: Optional[Dict] = None) -> Dict[str, Any]:
    """Execute task via Web-UI"""
    return await webui_integration.execute_webui_task(task, parameters)

async def get_webui_interface() -> Dict[str, Any]:
    """Get Web-UI interface"""
    return await webui_integration.get_webui_interface()

def get_webui_integration_status() -> Dict[str, Any]:
    """Get Web-UI integration status"""
    return webui_integration.get_status()

def is_webui_available() -> bool:
    """Check if Web-UI is available"""
    return webui_integration.available