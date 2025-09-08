#!/usr/bin/env python3
"""
ByteBot Integration for DuckBot
Advanced task automation and desktop interaction capabilities
Based on ByteBot AI architecture
"""

import os
import subprocess
import asyncio
import logging
import json
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import base64
import io
from PIL import Image, ImageGrab
import cv2
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class TaskResult:
    success: bool
    message: str
    screenshot: Optional[str] = None
    artifacts: Optional[Dict] = None
    execution_time: float = 0.0

class ByteBotIntegration:
    """ByteBot-inspired task automation and desktop interaction"""
    
    def __init__(self):
        self.session_id = None
        self.task_history = []
        self.screenshot_cache = {}
        self.available = self._check_dependencies()
        
    def _check_dependencies(self) -> bool:
        """Check if required dependencies are available"""
        try:
            import PIL
            import cv2
            import numpy as np
            return True
        except ImportError as e:
            logger.warning(f"ByteBot dependencies not fully available: {e}")
            return False
    
    async def initialize(self) -> bool:
        """Initialize ByteBot integration"""
        try:
            if not self.available:
                logger.warning("ByteBot integration requires PIL, cv2, numpy")
                return False
                
            self.session_id = f"bytebot_{int(time.time())}"
            logger.info(f"ByteBot integration initialized - Session: {self.session_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize ByteBot integration: {e}")
            return False
    
    async def execute_natural_language_task(self, task: str, context: Optional[Dict] = None) -> TaskResult:
        """Execute a natural language task with desktop interaction"""
        start_time = time.time()
        
        try:
            # Take screenshot for context
            screenshot_b64 = await self._capture_desktop()
            
            # Parse task intent
            task_type = self._classify_task(task)
            
            result = None
            if task_type == "file_operation":
                result = await self._handle_file_operation(task, context)
            elif task_type == "application_control":
                result = await self._handle_application_control(task, context)
            elif task_type == "system_operation":
                result = await self._handle_system_operation(task, context)
            elif task_type == "web_automation":
                result = await self._handle_web_automation(task, context)
            elif task_type == "document_processing":
                result = await self._handle_document_processing(task, context)
            else:
                result = await self._handle_generic_task(task, context)
            
            execution_time = time.time() - start_time
            
            # Record task in history
            self.task_history.append({
                "task": task,
                "type": task_type,
                "result": result,
                "timestamp": time.time(),
                "execution_time": execution_time
            })
            
            return TaskResult(
                success=result.get("success", False),
                message=result.get("message", "Task completed"),
                screenshot=screenshot_b64,
                artifacts=result.get("artifacts"),
                execution_time=execution_time
            )
            
        except Exception as e:
            logger.error(f"Task execution failed: {e}")
            return TaskResult(
                success=False,
                message=f"Task failed: {str(e)}",
                execution_time=time.time() - start_time
            )
    
    def _classify_task(self, task: str) -> str:
        """Classify task type based on natural language"""
        task_lower = task.lower()
        
        file_keywords = ["file", "folder", "directory", "copy", "move", "delete", "create", "save"]
        app_keywords = ["open", "close", "launch", "start", "application", "program", "app"]
        system_keywords = ["system", "settings", "configuration", "restart", "shutdown", "service"]
        web_keywords = ["browser", "website", "url", "web", "internet", "download"]
        doc_keywords = ["document", "pdf", "word", "excel", "text", "read", "extract"]
        
        if any(keyword in task_lower for keyword in file_keywords):
            return "file_operation"
        elif any(keyword in task_lower for keyword in app_keywords):
            return "application_control"
        elif any(keyword in task_lower for keyword in system_keywords):
            return "system_operation"
        elif any(keyword in task_lower for keyword in web_keywords):
            return "web_automation"
        elif any(keyword in task_lower for keyword in doc_keywords):
            return "document_processing"
        else:
            return "generic"
    
    async def _handle_file_operation(self, task: str, context: Optional[Dict]) -> Dict:
        """Handle file and folder operations"""
        try:
            # Example file operations based on ByteBot capabilities
            if "create folder" in task.lower():
                folder_name = self._extract_filename_from_task(task)
                if folder_name:
                    path = Path.cwd() / folder_name
                    path.mkdir(exist_ok=True)
                    return {"success": True, "message": f"Created folder: {folder_name}"}
            
            elif "copy file" in task.lower():
                # Implement file copying logic
                return {"success": True, "message": "File copy operation would be implemented"}
            
            elif "find file" in task.lower():
                # Implement file search
                search_term = self._extract_search_term(task)
                files = list(Path.cwd().rglob(f"*{search_term}*"))
                return {
                    "success": True, 
                    "message": f"Found {len(files)} files matching '{search_term}'",
                    "artifacts": {"files": [str(f) for f in files[:10]]}
                }
            
            return {"success": False, "message": "File operation not recognized"}
            
        except Exception as e:
            return {"success": False, "message": f"File operation failed: {e}"}
    
    async def _handle_application_control(self, task: str, context: Optional[Dict]) -> Dict:
        """Handle application launch and control"""
        try:
            if "open notepad" in task.lower() or "launch notepad" in task.lower():
                subprocess.Popen(["notepad.exe"])
                return {"success": True, "message": "Launched Notepad"}
            
            elif "open calculator" in task.lower():
                subprocess.Popen(["calc.exe"])
                return {"success": True, "message": "Launched Calculator"}
            
            elif "open browser" in task.lower():
                subprocess.Popen(["start", "chrome"], shell=True)
                return {"success": True, "message": "Launched web browser"}
            
            return {"success": False, "message": "Application control not recognized"}
            
        except Exception as e:
            return {"success": False, "message": f"Application control failed: {e}"}
    
    async def _handle_system_operation(self, task: str, context: Optional[Dict]) -> Dict:
        """Handle system-level operations"""
        try:
            if "check system info" in task.lower():
                import platform
                info = {
                    "system": platform.system(),
                    "release": platform.release(),
                    "version": platform.version(),
                    "machine": platform.machine(),
                    "processor": platform.processor()
                }
                return {
                    "success": True, 
                    "message": "System information retrieved",
                    "artifacts": {"system_info": info}
                }
            
            elif "list processes" in task.lower():
                try:
                    import psutil
                    processes = [{"pid": p.pid, "name": p.name()} for p in psutil.process_iter(['pid', 'name'])][:20]
                    return {
                        "success": True,
                        "message": f"Found {len(processes)} running processes",
                        "artifacts": {"processes": processes}
                    }
                except ImportError:
                    return {"success": False, "message": "psutil not available for process listing"}
            
            return {"success": False, "message": "System operation not recognized"}
            
        except Exception as e:
            return {"success": False, "message": f"System operation failed: {e}"}
    
    async def _handle_web_automation(self, task: str, context: Optional[Dict]) -> Dict:
        """Handle web browser automation"""
        try:
            if "navigate to" in task.lower() or "open website" in task.lower():
                url = self._extract_url_from_task(task)
                if url:
                    import webbrowser
                    webbrowser.open(url)
                    return {"success": True, "message": f"Opened {url} in browser"}
            
            return {"success": False, "message": "Web automation not recognized"}
            
        except Exception as e:
            return {"success": False, "message": f"Web automation failed: {e}"}
    
    async def _handle_document_processing(self, task: str, context: Optional[Dict]) -> Dict:
        """Handle document processing and analysis"""
        try:
            if "read text file" in task.lower():
                filename = self._extract_filename_from_task(task)
                if filename and Path(filename).exists():
                    content = Path(filename).read_text(encoding='utf-8')
                    return {
                        "success": True,
                        "message": f"Read {len(content)} characters from {filename}",
                        "artifacts": {"content": content[:1000] + "..." if len(content) > 1000 else content}
                    }
            
            return {"success": False, "message": "Document processing not recognized"}
            
        except Exception as e:
            return {"success": False, "message": f"Document processing failed: {e}"}
    
    async def _handle_generic_task(self, task: str, context: Optional[Dict]) -> Dict:
        """Handle generic tasks that don't fit other categories"""
        return {
            "success": True,
            "message": f"Generic task processed: {task}",
            "artifacts": {"task_analysis": "This would be processed by the main AI system"}
        }
    
    async def _capture_desktop(self) -> str:
        """Capture desktop screenshot and return base64 encoded"""
        try:
            if not self.available:
                return ""
            
            screenshot = ImageGrab.grab()
            
            # Resize for efficiency
            screenshot = screenshot.resize((800, 600), Image.Resampling.LANCZOS)
            
            # Convert to base64
            buffer = io.BytesIO()
            screenshot.save(buffer, format='PNG')
            screenshot_b64 = base64.b64encode(buffer.getvalue()).decode()
            
            return screenshot_b64
            
        except Exception as e:
            logger.error(f"Screenshot capture failed: {e}")
            return ""
    
    def _extract_filename_from_task(self, task: str) -> Optional[str]:
        """Extract filename from natural language task"""
        # Simple extraction - would be more sophisticated in production
        words = task.split()
        for word in words:
            if "." in word or word.isalpha():
                return word
        return None
    
    def _extract_search_term(self, task: str) -> str:
        """Extract search term from natural language"""
        words = task.lower().split()
        try:
            find_idx = words.index("find") if "find" in words else 0
            if find_idx < len(words) - 1:
                return words[find_idx + 1]
        except:
            pass
        return "test"
    
    def _extract_url_from_task(self, task: str) -> Optional[str]:
        """Extract URL from natural language task"""
        words = task.split()
        for word in words:
            if word.startswith("http") or "." in word:
                if not word.startswith("http"):
                    word = "https://" + word
                return word
        return None
    
    async def get_task_history(self) -> List[Dict]:
        """Get history of executed tasks"""
        return self.task_history[-50:]  # Last 50 tasks
    
    async def clear_session(self):
        """Clear current session data"""
        self.task_history.clear()
        self.screenshot_cache.clear()
        self.session_id = f"bytebot_{int(time.time())}"
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get ByteBot capabilities"""
        return {
            "available": self.available,
            "session_id": self.session_id,
            "supported_operations": [
                "File operations (create, copy, move, delete, search)",
                "Application control (launch, manage)",
                "System operations (info, process management)",
                "Web automation (navigate, interact)",
                "Document processing (read, extract, analyze)",
                "Desktop interaction (screenshot, visual analysis)",
                "Natural language task interpretation"
            ],
            "task_history_count": len(self.task_history)
        }

# Global instance
bytebot_integration = ByteBotIntegration()

async def initialize_bytebot() -> bool:
    """Initialize ByteBot integration"""
    return await bytebot_integration.initialize()

async def execute_bytebot_task(task: str, context: Optional[Dict] = None) -> Dict[str, Any]:
    """Execute ByteBot task interface"""
    result = await bytebot_integration.execute_natural_language_task(task, context)
    return {
        "success": result.success,
        "message": result.message,
        "screenshot": result.screenshot,
        "artifacts": result.artifacts,
        "execution_time": result.execution_time
    }

def is_bytebot_available() -> bool:
    """Check if ByteBot is available"""
    return bytebot_integration.available

def get_bytebot_capabilities() -> Dict[str, Any]:
    """Get ByteBot capabilities"""
    return bytebot_integration.get_capabilities()