"""
OpenWebUI Tool for DuckBot Command Execution
============================================

This tool allows OpenWebUI to communicate with your DuckBot server,
enabling you to execute commands, manage services, and interact with
the AI ecosystem directly from OpenWebUI.

Usage in OpenWebUI:
1. Import this as a custom tool
2. Configure DuckBot server URL and token
3. Use the tool to execute various DuckBot commands

Author: DuckBot Integration Team
Version: 1.0
"""

import requests
import json
import time
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field


class DuckBotTool:
    """
    OpenWebUI Tool for DuckBot Integration
    
    This tool provides a bridge between OpenWebUI and your DuckBot server,
    allowing you to execute AI tasks, manage services, and control the ecosystem.
    """
    
    def __init__(self):
        self.name = "duckbot_command"
        self.description = "Execute commands on your DuckBot server including AI tasks, service management, and system control"
        
        # Default configuration - update these for your setup
        self.base_url = "http://localhost:8787"  # Default DuckBot WebUI port
        self.token = None  # Will be set via configuration or auto-detected
        self.timeout = 30  # Request timeout in seconds
        
    def get_token(self) -> Optional[str]:
        """Get or detect DuckBot WebUI token"""
        if self.token:
            return self.token
            
        try:
            # Try to get token from unprotected endpoint
            response = requests.get(f"{self.base_url}/token", timeout=5)
            if response.status_code == 200:
                token_info = response.json()
                self.token = token_info.get("token")
                return self.token
        except Exception as e:
            print(f"Could not auto-detect token: {e}")
            
        return None
    
    def make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make authenticated request to DuckBot server"""
        token = self.get_token()
        if not token:
            return {"error": "No DuckBot token available. Please ensure DuckBot WebUI is running."}
        
        url = f"{self.base_url}{endpoint}"
        headers = {"Authorization": f"Bearer {token}"}
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, params=params, timeout=self.timeout)
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


# Global tool instance
duckbot_tool = DuckBotTool()


def execute_ai_task(prompt: str, task_type: str = "auto", priority: str = "medium") -> str:
    """
    Execute an AI task on DuckBot server
    
    Args:
        prompt: The task or question for the AI
        task_type: Type of task (auto, code, reasoning, summary, etc.)
        priority: Task priority (low, medium, high)
    
    Returns:
        AI response or error message
    """
    data = {
        "message": prompt,
        "kind": task_type,
        "risk": priority
    }
    
    result = duckbot_tool.make_request("POST", "/chat", data=data)
    
    if "error" in result:
        return f"❌ Error: {result['error']}"
    
    if result.get("success"):
        response = result.get("response", "No response")
        model = result.get("model", "unknown")
        confidence = result.get("confidence", 0)
        cached = result.get("cached", False)
        
        cache_info = " (cached)" if cached else ""
        return f"🤖 {response}\n\n📊 Model: {model} | Confidence: {confidence:.2f}{cache_info}"
    
    return f"❌ Failed to execute AI task: {result}"


def get_system_status() -> str:
    """
    Get DuckBot system status including services and AI state
    
    Returns:
        Formatted system status report
    """
    # Get AI router status
    ai_status = duckbot_tool.make_request("GET", "/api/system-status")
    
    # Get services status  
    services_status = duckbot_tool.make_request("GET", "/api/services")
    
    status_report = "🚀 **DuckBot System Status**\n\n"
    
    # AI Router Status
    if ai_status.get("ok"):
        ai_info = ai_status.get("status", {})
        status_report += "🧠 **AI Router:**\n"
        status_report += f"• Current Model: {ai_info.get('current_lm_model', 'Unknown')}\n"
        status_report += f"• Cache Size: {ai_info.get('cache_size', 0)} items\n"
        status_report += f"• Chat Tokens: {ai_info.get('chat_bucket_tokens', 0)}/{ai_info.get('chat_bucket_limit', 30)}\n"
        status_report += f"• Background Tokens: {ai_info.get('background_bucket_tokens', 0)}/{ai_info.get('background_bucket_limit', 30)}\n\n"
    
    # Services Status
    if services_status.get("ok"):
        services = services_status.get("services", [])
        status_report += "⚙️ **Services:**\n"
        for service in services:
            name = service.get("name", "Unknown")
            status = service.get("status", "unknown")
            port = service.get("port", "N/A")
            
            status_emoji = "✅" if status == "running" else "❌" 
            status_report += f"{status_emoji} {name} (:{port}) - {status}\n"
        status_report += "\n"
    
    return status_report


def manage_service(service_name: str, action: str) -> str:
    """
    Manage DuckBot services (start, stop, restart)
    
    Args:
        service_name: Name of the service (comfyui, n8n, jupyter, etc.)
        action: Action to perform (start, stop, restart)
    
    Returns:
        Result of the service management action
    """
    if action not in ["start", "stop", "restart"]:
        return "❌ Invalid action. Use: start, stop, or restart"
    
    endpoint = f"/api/services/{service_name}/{action}"
    result = duckbot_tool.make_request("POST", endpoint)
    
    if result.get("success"):
        message = result.get("result", f"Service {action} completed")
        return f"✅ {service_name}: {message}"
    else:
        error = result.get("error", "Unknown error")
        return f"❌ Failed to {action} {service_name}: {error}"


def get_cost_summary(days: int = 7) -> str:
    """
    Get cost and usage summary for the specified number of days
    
    Args:
        days: Number of days to include in summary (default: 7)
    
    Returns:
        Formatted cost summary
    """
    result = duckbot_tool.make_request("GET", f"/api/cost_summary?days={days}")
    
    if not result.get("success"):
        return f"❌ Could not retrieve cost data: {result.get('error', 'Unknown error')}"
    
    data = result.get("data", {})
    
    summary = f"💰 **Cost Summary ({days} days)**\n\n"
    summary += f"• Total Cost: ${data.get('total_cost', 0):.4f}\n"
    summary += f"• Total Tokens: {data.get('total_tokens', 0):,}\n"
    summary += f"• Total Requests: {data.get('total_requests', 0):,}\n\n"
    
    # By model breakdown
    by_model = data.get("by_model", {})
    if by_model:
        summary += "**By Model:**\n"
        for model, cost in by_model.items():
            summary += f"• {model}: ${cost:.4f}\n"
        summary += "\n"
    
    # Predictions
    predictions = data.get("predictions", {})
    if predictions:
        summary += "**Predictions:**\n"
        monthly = predictions.get("monthly_cost", 0)
        daily = predictions.get("daily_average", 0)
        summary += f"• Daily Average: ${daily:.4f}\n"
        summary += f"• Monthly Projection: ${monthly:.2f}\n"
    
    return summary


def execute_rag_search(query: str, top_k: int = 4) -> str:
    """
    Search DuckBot's RAG (Retrieval Augmented Generation) index
    
    Args:
        query: Search query
        top_k: Number of results to return
    
    Returns:
        Search results from RAG system
    """
    data = {"q": query, "top_k": top_k}
    result = duckbot_tool.make_request("POST", "/rag/search", data=data)
    
    if not result.get("ok"):
        return f"❌ RAG search failed: {result.get('error', 'Unknown error')}"
    
    context = result.get("context", "")
    chunks = result.get("chunks", [])
    
    if not context:
        return "🔍 No relevant information found in RAG index."
    
    response = f"🔍 **RAG Search Results for: '{query}'**\n\n"
    response += f"**Context:** {context[:500]}{'...' if len(context) > 500 else ''}\n\n"
    
    if chunks:
        response += f"**Sources ({len(chunks)} chunks found):**\n"
        for i, chunk in enumerate(chunks[:3], 1):  # Show first 3 chunks
            source = chunk.get("metadata", {}).get("source", "Unknown")
            response += f"{i}. {source}\n"
    
    return response


def get_available_models() -> str:
    """
    Get list of available AI models from LM Studio
    
    Returns:
        List of available models
    """
    result = duckbot_tool.make_request("GET", "/models/available")
    
    if not result.get("ok"):
        return f"❌ Could not get models: {result.get('error', 'Unknown error')}"
    
    models = result.get("models", [])
    lm_studio_url = result.get("lm_studio_url", "Unknown")
    
    if not models:
        return f"📭 No models available from LM Studio ({lm_studio_url})\nMake sure LM Studio is running with at least one model loaded."
    
    response = f"🤖 **Available Models ({len(models)} found)**\n\n"
    response += f"**LM Studio URL:** {lm_studio_url}\n\n"
    
    for i, model in enumerate(models[:10], 1):  # Show first 10 models
        model_id = model.get("id", "Unknown")
        size = model.get("size", "Unknown size")
        response += f"{i}. {model_id} ({size})\n"
    
    if len(models) > 10:
        response += f"\n... and {len(models) - 10} more models"
    
    return response


# OpenWebUI Tool Function
def duckbot_command(
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
    Execute commands on your DuckBot server
    
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
    
    Returns:
        Command execution result
    """
    
    try:
        if command == "ai_task":
            if not prompt:
                return "❌ Please provide a prompt for the AI task"
            return execute_ai_task(prompt, task_type, priority)
        
        elif command == "system_status":
            return get_system_status()
        
        elif command == "manage_service":
            if not service_name or not action:
                return "❌ Please provide service_name and action for service management"
            return manage_service(service_name, action)
        
        elif command == "cost_summary":
            return get_cost_summary(days)
        
        elif command == "rag_search":
            if not query:
                return "❌ Please provide a query for RAG search"
            return execute_rag_search(query, top_k)
        
        elif command == "list_models":
            return get_available_models()
        
        else:
            available_commands = [
                "ai_task", "system_status", "manage_service", 
                "cost_summary", "rag_search", "list_models"
            ]
            return f"❌ Unknown command: {command}\n\nAvailable commands: {', '.join(available_commands)}"
    
    except Exception as e:
        return f"❌ Tool error: {str(e)}"


# Tool metadata for OpenWebUI
TOOL_METADATA = {
    "name": "duckbot_command",
    "description": "Execute commands on your DuckBot server including AI tasks, service management, and system monitoring",
    "parameters": {
        "command": {
            "type": "string", 
            "description": "Command to execute (ai_task, system_status, manage_service, cost_summary, rag_search, list_models)",
            "required": True
        },
        "prompt": {
            "type": "string",
            "description": "Text prompt for AI tasks",
            "required": False
        },
        "service_name": {
            "type": "string", 
            "description": "Service name for management (comfyui, n8n, jupyter, lm_studio, webui)",
            "required": False
        },
        "action": {
            "type": "string",
            "description": "Service action (start, stop, restart)", 
            "required": False
        },
        "task_type": {
            "type": "string",
            "description": "AI task type (auto, code, reasoning, summary, long_form, json_format)",
            "default": "auto",
            "required": False
        },
        "priority": {
            "type": "string", 
            "description": "Task priority (low, medium, high)",
            "default": "medium",
            "required": False
        },
        "days": {
            "type": "integer",
            "description": "Number of days for cost summary",
            "default": 7,
            "required": False
        },
        "query": {
            "type": "string",
            "description": "Search query for RAG system",
            "required": False
        },
        "top_k": {
            "type": "integer", 
            "description": "Number of RAG search results",
            "default": 4,
            "required": False
        }
    }
}


if __name__ == "__main__":
    # Test the tool
    print("Testing DuckBot OpenWebUI Tool...")
    print("=" * 50)
    
    # Test system status
    print("Testing system status...")
    result = duckbot_command("system_status")
    print(result)
    print("\n" + "=" * 50)
    
    # Test AI task
    print("Testing AI task...")
    result = duckbot_command("ai_task", prompt="What is the current time?", task_type="auto")
    print(result)