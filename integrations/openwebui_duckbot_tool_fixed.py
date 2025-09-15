"""
title: DuckBot Command Tool
author: DuckBot Integration Team
version: 1.0.0
description: Execute commands on your DuckBot server including AI tasks, service management, and system monitoring
requirements: requests
"""

import requests
import json
import time
from typing import Dict, Any, Optional


class Tools:
    def __init__(self):
        self.base_url = "http://localhost:8787"  # Default DuckBot WebUI port
        self.token = None
        self.timeout = 30

    def get_duckbot_token(self) -> Optional[str]:
        """Get or detect DuckBot WebUI token"""
        if self.token:
            return self.token
            
        try:
            response = requests.get(f"{self.base_url}/token", timeout=5)
            if response.status_code == 200:
                token_info = response.json()
                self.token = token_info.get("token")
                return self.token
        except Exception:
            pass
            
        return None

    def make_duckbot_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make authenticated request to DuckBot server"""
        token = self.get_duckbot_token()
        if not token:
            return {"error": "No DuckBot token available. Please ensure DuckBot WebUI is running."}
        
        url = f"{self.base_url}{endpoint}"
        headers = {"Authorization": f"Bearer {token}"}
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, timeout=self.timeout)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, data=data, timeout=self.timeout)
            else:
                return {"error": f"Unsupported HTTP method: {method}"}
            
            if response.status_code == 200:
                try:
                    return response.json()
                except json.JSONDecodeError:
                    return {"success": True, "response": response.text}
            else:
                return {"error": f"HTTP {response.status_code}: {response.text}"}
                
        except requests.exceptions.Timeout:
            return {"error": "Request timed out. DuckBot server may be busy."}
        except requests.exceptions.ConnectionError:
            return {"error": "Could not connect to DuckBot server. Is it running?"}
        except Exception as e:
            return {"error": f"Request failed: {str(e)}"}

    def duckbot_command(
        self,
        command: str,
        prompt: str = "",
        service_name: str = "",
        action: str = "",
        task_type: str = "auto",
        priority: str = "medium",
        days: int = 7,
        query: str = "",
        top_k: int = 4
    ) -> str:
        """
        Execute commands on your DuckBot server.
        
        Available commands:
        - ai_task: Execute AI task with prompt
        - system_status: Get system and services status  
        - manage_service: Control services (start/stop/restart)
        - cost_summary: Get usage and cost summary
        - rag_search: Search RAG knowledge base
        - list_models: Get available AI models
        
        Args:
            command: Command to execute
            prompt: Text for AI tasks
            service_name: Service name for management (comfyui, n8n, jupyter, etc.)
            action: Action for service management (start, stop, restart)
            task_type: AI task type (auto, code, reasoning, summary, etc.)
            priority: Task priority (low, medium, high)
            days: Days for cost summary
            query: Search query for RAG
            top_k: Number of RAG results
        """
        
        try:
            if command == "ai_task":
                return self._execute_ai_task(prompt, task_type, priority)
            elif command == "system_status":
                return self._get_system_status()
            elif command == "manage_service":
                return self._manage_service(service_name, action)
            elif command == "cost_summary":
                return self._get_cost_summary(days)
            elif command == "rag_search":
                return self._execute_rag_search(query, top_k)
            elif command == "list_models":
                return self._get_available_models()
            else:
                available = ["ai_task", "system_status", "manage_service", "cost_summary", "rag_search", "list_models"]
                return f"Unknown command: {command}. Available: {', '.join(available)}"
        
        except Exception as e:
            return f"Tool error: {str(e)}"

    def _execute_ai_task(self, prompt: str, task_type: str, priority: str) -> str:
        """Execute an AI task on DuckBot server"""
        if not prompt:
            return "Please provide a prompt for the AI task"
        
        data = {"message": prompt, "kind": task_type, "risk": priority}
        result = self.make_duckbot_request("POST", "/chat", data=data)
        
        if "error" in result:
            return f"Error: {result['error']}"
        
        if result.get("success"):
            response = result.get("response", "No response")
            model = result.get("model", "unknown")
            confidence = result.get("confidence", 0)
            cached = result.get("cached", False)
            
            cache_info = " (cached)" if cached else ""
            return f"AI Response: {response}\n\nModel: {model} | Confidence: {confidence:.2f}{cache_info}"
        
        return f"Failed to execute AI task: {result}"

    def _get_system_status(self) -> str:
        """Get DuckBot system status"""
        ai_status = self.make_duckbot_request("GET", "/api/system-status")
        services_status = self.make_duckbot_request("GET", "/api/services")
        
        status_report = "DuckBot System Status:\n\n"
        
        # AI Router Status
        if ai_status.get("ok"):
            ai_info = ai_status.get("status", {})
            status_report += "AI Router:\n"
            status_report += f"- Current Model: {ai_info.get('current_lm_model', 'Unknown')}\n"
            status_report += f"- Cache Size: {ai_info.get('cache_size', 0)} items\n"
            status_report += f"- Chat Tokens: {ai_info.get('chat_bucket_tokens', 0)}/{ai_info.get('chat_bucket_limit', 30)}\n"
            status_report += f"- Background Tokens: {ai_info.get('background_bucket_tokens', 0)}/{ai_info.get('background_bucket_limit', 30)}\n\n"
        
        # Services Status
        if services_status.get("ok"):
            services = services_status.get("services", [])
            status_report += "Services:\n"
            for service in services:
                name = service.get("name", "Unknown")
                status = service.get("status", "unknown")
                port = service.get("port", "N/A")
                
                status_emoji = "[EMOJI]" if status == "running" else "[EMOJI]" 
                status_report += f"{status_emoji} {name} (:{port}) - {status}\n"
        
        return status_report

    def _manage_service(self, service_name: str, action: str) -> str:
        """Manage DuckBot services"""
        if not service_name or not action:
            return "Please provide service_name and action for service management"
        
        if action not in ["start", "stop", "restart"]:
            return "Invalid action. Use: start, stop, or restart"
        
        endpoint = f"/api/services/{service_name}/{action}"
        result = self.make_duckbot_request("POST", endpoint)
        
        if result.get("success"):
            message = result.get("result", f"Service {action} completed")
            return f"Success: {service_name} - {message}"
        else:
            error = result.get("error", "Unknown error")
            return f"Failed to {action} {service_name}: {error}"

    def _get_cost_summary(self, days: int) -> str:
        """Get cost and usage summary"""
        result = self.make_duckbot_request("GET", f"/api/cost_summary?days={days}")
        
        if not result.get("success"):
            return f"Could not retrieve cost data: {result.get('error', 'Unknown error')}"
        
        data = result.get("data", {})
        
        summary = f"Cost Summary ({days} days):\n\n"
        summary += f"- Total Cost: ${data.get('total_cost', 0):.4f}\n"
        summary += f"- Total Tokens: {data.get('total_tokens', 0):,}\n"
        summary += f"- Total Requests: {data.get('total_requests', 0):,}\n\n"
        
        # By model breakdown
        by_model = data.get("by_model", {})
        if by_model:
            summary += "By Model:\n"
            for model, cost in by_model.items():
                summary += f"- {model}: ${cost:.4f}\n"
            summary += "\n"
        
        # Predictions
        predictions = data.get("predictions", {})
        if predictions:
            summary += "Predictions:\n"
            monthly = predictions.get("monthly_cost", 0)
            daily = predictions.get("daily_average", 0)
            summary += f"- Daily Average: ${daily:.4f}\n"
            summary += f"- Monthly Projection: ${monthly:.2f}\n"
        
        return summary

    def _execute_rag_search(self, query: str, top_k: int) -> str:
        """Search DuckBot's RAG system"""
        if not query:
            return "Please provide a query for RAG search"
        
        data = {"q": query, "top_k": top_k}
        result = self.make_duckbot_request("POST", "/rag/search", data=data)
        
        if not result.get("ok"):
            return f"RAG search failed: {result.get('error', 'Unknown error')}"
        
        context = result.get("context", "")
        chunks = result.get("chunks", [])
        
        if not context:
            return "No relevant information found in RAG index."
        
        response = f"RAG Search Results for: '{query}'\n\n"
        response += f"Context: {context[:500]}{'...' if len(context) > 500 else ''}\n\n"
        
        if chunks:
            response += f"Sources ({len(chunks)} chunks found):\n"
            for i, chunk in enumerate(chunks[:3], 1):
                source = chunk.get("metadata", {}).get("source", "Unknown")
                response += f"{i}. {source}\n"
        
        return response

    def _get_available_models(self) -> str:
        """Get list of available AI models"""
        result = self.make_duckbot_request("GET", "/models/available")
        
        if not result.get("ok"):
            return f"Could not get models: {result.get('error', 'Unknown error')}"
        
        models = result.get("models", [])
        lm_studio_url = result.get("lm_studio_url", "Unknown")
        
        if not models:
            return f"No models available from LM Studio ({lm_studio_url})\nMake sure LM Studio is running with at least one model loaded."
        
        response = f"Available Models ({len(models)} found):\n\n"
        response += f"LM Studio URL: {lm_studio_url}\n\n"
        
        for i, model in enumerate(models[:10], 1):
            model_id = model.get("id", "Unknown")
            size = model.get("size", "Unknown size")
            response += f"{i}. {model_id} ({size})\n"
        
        if len(models) > 10:
            response += f"\n... and {len(models) - 10} more models"
        
        return response