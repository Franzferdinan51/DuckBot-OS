#!/usr/bin/env python3
"""
Claude Code Integration for DuckBot
Integrates Claude Code Router MCP and native Claude Code capabilities
"""

import os
import subprocess
import asyncio
import logging
import requests
import json
from pathlib import Path
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

class ClaudeCodeIntegration:
    """
    Integration layer for Claude Code and Claude Code Router
    Provides unified access to Claude Code capabilities for the main brain
    """
    
    def __init__(self):
        self.router_available = False
        self.claude_code_available = False
        self.openrouter_server_process = None
        self.router_port = 8765  # Default Claude Code Router port
        self.openrouter_port = 11434  # OpenRouter proxy port
        
    async def initialize(self) -> bool:
        """Initialize Claude Code integration"""
        try:
            # Check for Claude Code Router installation
            self.router_available = await self._check_claude_code_router()
            
            # Check for native Claude Code
            self.claude_code_available = await self._check_claude_code()
            
            # Start OpenRouter server if needed
            await self._ensure_openrouter_server()
            
            logger.info(f"Claude Code integration initialized - Router: {self.router_available}, Native: {self.claude_code_available}")
            return self.router_available or self.claude_code_available
            
        except Exception as e:
            logger.error(f"Failed to initialize Claude Code integration: {e}")
            return False
    
    async def _check_claude_code_router(self) -> bool:
        """Check if Claude Code Router is installed"""
        try:
            result = subprocess.run(['ccr', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                logger.info("Claude Code Router detected")
                return True
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            pass
        
        try:
            result = subprocess.run(['npm', 'list', '-g', '@musistudio/claude-code-router'], 
                                  capture_output=True, text=True, timeout=5)
            return '@musistudio/claude-code-router' in result.stdout
        except:
            return False
    
    async def _check_claude_code(self) -> bool:
        """Check if native Claude Code is available"""
        try:
            result = subprocess.run(['claude-code', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except:
            return False
    
    async def _ensure_openrouter_server(self) -> bool:
        """Start OpenRouter proxy server for the main brain"""
        if self.openrouter_server_process and self.openrouter_server_process.poll() is None:
            return True  # Already running
        
        try:
            # Check if port is available
            if self._is_port_in_use(self.openrouter_port):
                logger.info(f"OpenRouter server already running on port {self.openrouter_port}")
                return True
            
            # Start Claude Code Router
            if self.router_available:
                cmd = ['ccr', 'code']  # Correct command based on documentation
                self.openrouter_server_process = subprocess.Popen(
                    cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                
                # Wait a moment for startup
                await asyncio.sleep(2)
                
                if self.openrouter_server_process.poll() is None:
                    logger.info(f"OpenRouter server started on port {self.openrouter_port}")
                    return True
            
        except Exception as e:
            logger.error(f"Failed to start OpenRouter server: {e}")
        
        return False
    
    def _is_port_in_use(self, port: int) -> bool:
        """Check if a port is already in use"""
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) == 0
    
    async def execute_code_task(self, task: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Execute a code-related task using Claude Code capabilities
        This integrates with the main brain system
        """
        try:
            if self.router_available:
                return await self._execute_via_router(task, context)
            elif self.claude_code_available:
                return await self._execute_via_native(task, context)
            else:
                return {
                    'success': False,
                    'error': 'No Claude Code capabilities available',
                    'suggestion': 'Install Claude Code Router: npm install -g @musistudio/claude-code-router'
                }
        except Exception as e:
            logger.error(f"Code task execution failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'task': task
            }
    
    async def _execute_via_router(self, task: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute task via Claude Code Router"""
        try:
            # Use the OpenRouter server we started
            api_url = f"http://localhost:{self.openrouter_port}/v1/chat/completions"
            
            payload = {
                "model": "anthropic/claude-3.5-sonnet",  # Default model
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a code analysis and development assistant integrated into the DuckBot AI ecosystem. Provide practical, executable solutions."
                    },
                    {
                        "role": "user", 
                        "content": task
                    }
                ],
                "max_tokens": 4000,
                "temperature": 0.1
            }
            
            if context:
                payload["messages"][0]["content"] += f"\n\nContext: {json.dumps(context, indent=2)}"
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY', '')}"
            }
            
            response = requests.post(api_url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'response': result['choices'][0]['message']['content'],
                    'model': result.get('model', 'claude-via-router'),
                    'usage': result.get('usage', {})
                }
            else:
                return {
                    'success': False,
                    'error': f"Router API error: {response.status_code}",
                    'details': response.text
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f"Router execution failed: {e}"
            }
    
    async def _execute_via_native(self, task: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute task via native Claude Code"""
        try:
            # Create a temporary file with the task
            temp_file = Path.cwd() / "temp_claude_task.txt"
            with open(temp_file, 'w') as f:
                f.write(f"Task: {task}\n")
                if context:
                    f.write(f"Context: {json.dumps(context, indent=2)}\n")
            
            # Execute with Claude Code
            result = subprocess.run([
                'claude-code', 'analyze', str(temp_file)
            ], capture_output=True, text=True, timeout=60)
            
            # Clean up
            temp_file.unlink(missing_ok=True)
            
            if result.returncode == 0:
                return {
                    'success': True,
                    'response': result.stdout,
                    'model': 'claude-native'
                }
            else:
                return {
                    'success': False,
                    'error': result.stderr or "Native Claude Code execution failed"
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f"Native execution failed: {e}"
            }
    
    def get_available_models(self) -> List[str]:
        """Get list of available models through Claude Code integration"""
        models = []
        
        if self.router_available:
            models.extend([
                'anthropic/claude-3.5-sonnet',
                'anthropic/claude-3-haiku', 
                'openrouter/auto',  # Let OpenRouter choose
                'deepseek/coder',
                'ollama/codellama'
            ])
        
        if self.claude_code_available:
            models.append('claude-native')
        
        return models
    
    async def switch_model(self, model_name: str) -> bool:
        """Switch the active model for Claude Code Router"""
        if not self.router_available:
            return False
        
        try:
            # Send model switch command to router
            api_url = f"http://localhost:{self.openrouter_port}/v1/models/{model_name}/activate"
            response = requests.post(api_url, timeout=10)
            return response.status_code == 200
        except:
            return False
    
    def is_available(self) -> bool:
        """Check if any Claude Code capability is available"""
        return self.router_available or self.claude_code_available
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive status of Claude Code integration"""
        return {
            'router_available': self.router_available,
            'claude_code_available': self.claude_code_available,
            'openrouter_server_running': (
                self.openrouter_server_process is not None and 
                self.openrouter_server_process.poll() is None
            ),
            'openrouter_port': self.openrouter_port,
            'available_models': self.get_available_models()
        }
    
    async def shutdown(self):
        """Shutdown Claude Code integration and cleanup"""
        if self.openrouter_server_process:
            try:
                self.openrouter_server_process.terminate()
                await asyncio.sleep(2)
                if self.openrouter_server_process.poll() is None:
                    self.openrouter_server_process.kill()
                logger.info("OpenRouter server stopped")
            except Exception as e:
                logger.error(f"Error stopping OpenRouter server: {e}")


# Global instance for main brain integration
claude_code_integration = ClaudeCodeIntegration()


async def initialize_claude_code() -> bool:
    """Initialize Claude Code integration for the main brain"""
    return await claude_code_integration.initialize()


async def execute_claude_code_task(task: str, context: Optional[Dict] = None) -> Dict[str, Any]:
    """Execute a task using Claude Code - main brain interface"""
    return await claude_code_integration.execute_code_task(task, context)


def is_claude_code_available() -> bool:
    """Check if Claude Code is available for the main brain"""
    return claude_code_integration.is_available()


def get_claude_code_status() -> Dict[str, Any]:
    """Get Claude Code status for diagnostics"""
    return claude_code_integration.get_status()