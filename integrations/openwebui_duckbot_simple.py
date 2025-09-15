"""
title: DuckBot Simple Command Tool
author: DuckBot Team  
version: 1.0.0
description: Simple tool to execute AI tasks and manage your DuckBot server
requirements: requests
"""

import requests
import json


class Tools:
    def __init__(self):
        self.duckbot_url = "http://localhost:8787"
        self.token = None
    
    def get_token(self):
        """Auto-detect DuckBot token"""
        try:
            response = requests.get(f"{self.duckbot_url}/token", timeout=5)
            if response.status_code == 200:
                return response.json().get("token")
        except:
            pass
        return None
    
    def duckbot_ai_task(self, prompt: str, task_type: str = "auto") -> str:
        """
        Execute an AI task on your DuckBot server.
        
        Args:
            prompt: The question or task for DuckBot AI
            task_type: Type of task (auto, code, reasoning, summary, long_form)
        
        Returns:
            AI response from DuckBot
        """
        
        if not prompt.strip():
            return "Error: Please provide a prompt for the AI task"
        
        # Get token
        token = self.get_token()
        if not token:
            return "Error: Could not connect to DuckBot server. Make sure it's running at http://localhost:8787"
        
        # Make request
        try:
            headers = {"Authorization": f"Bearer {token}"}
            data = {
                "message": prompt,
                "kind": task_type,
                "risk": "medium"
            }
            
            response = requests.post(
                f"{self.duckbot_url}/chat",
                headers=headers,
                data=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    ai_response = result.get("response", "No response")
                    model = result.get("model", "unknown")
                    confidence = result.get("confidence", 0)
                    
                    return f"DuckBot AI: {ai_response}\n\n(Model: {model}, Confidence: {confidence:.2f})"
                else:
                    return f"Error: {result.get('response', 'Unknown error')}"
            else:
                return f"Error: HTTP {response.status_code} - {response.text}"
                
        except requests.exceptions.ConnectionError:
            return "Error: Cannot connect to DuckBot server. Is it running?"
        except requests.exceptions.Timeout:
            return "Error: Request timed out. DuckBot may be busy."
        except Exception as e:
            return f"Error: {str(e)}"
    
    def duckbot_status(self) -> str:
        """
        Get DuckBot system status.
        
        Returns:
            Current system status
        """
        
        token = self.get_token()
        if not token:
            return "Error: Could not connect to DuckBot server"
        
        try:
            headers = {"Authorization": f"Bearer {token}"}
            
            # Get AI status
            ai_response = requests.get(f"{self.duckbot_url}/api/system-status", headers=headers, timeout=10)
            
            if ai_response.status_code == 200:
                ai_data = ai_response.json()
                if ai_data.get("ok"):
                    status = ai_data.get("status", {})
                    
                    report = "DuckBot Status:\n\n"
                    report += f"Current Model: {status.get('current_lm_model', 'Unknown')}\n"
                    report += f"Cache Items: {status.get('cache_size', 0)}\n"
                    report += f"Chat Tokens: {status.get('chat_bucket_tokens', 0)}/{status.get('chat_bucket_limit', 30)}\n"
                    report += f"Background Tokens: {status.get('background_bucket_tokens', 0)}/{status.get('background_bucket_limit', 30)}\n"
                    
                    return report
            
            return "DuckBot server is running but status unavailable"
            
        except Exception as e:
            return f"Error getting status: {str(e)}"
    
    def duckbot_start_service(self, service_name: str) -> str:
        """
        Start a DuckBot service.
        
        Args:
            service_name: Service to start (comfyui, n8n, jupyter, lm_studio)
        
        Returns:
            Result of starting the service
        """
        
        if not service_name:
            return "Error: Please specify a service name (comfyui, n8n, jupyter, lm_studio)"
        
        token = self.get_token()
        if not token:
            return "Error: Could not connect to DuckBot server"
        
        try:
            headers = {"Authorization": f"Bearer {token}"}
            
            response = requests.post(
                f"{self.duckbot_url}/api/services/{service_name}/start",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    return f"Successfully started {service_name}: {result.get('result', 'Started')}"
                else:
                    return f"Failed to start {service_name}: {result.get('error', 'Unknown error')}"
            else:
                return f"Error starting {service_name}: HTTP {response.status_code}"
                
        except Exception as e:
            return f"Error starting {service_name}: {str(e)}"