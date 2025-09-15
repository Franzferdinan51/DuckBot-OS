"""
title: DuckBot Control
author: open-webui
author_url: https://github.com/open-webui
funding_url: https://github.com/sponsors/tjbck
version: 0.1.0
"""

import requests
import json


def get_duckbot_token():
    """Get DuckBot authentication token"""
    try:
        response = requests.get("http://localhost:8787/token", timeout=5)
        if response.status_code == 200:
            return response.json().get("token")
    except:
        pass
    return None


def duckbot_ai_chat(message: str, task_type: str = "auto") -> str:
    """
    Chat with DuckBot AI system.
    
    :param message: Your message or question for DuckBot AI
    :param task_type: Type of AI task - auto, code, reasoning, summary, long_form
    :return: AI response from DuckBot
    """
    
    if not message.strip():
        return "[FAIL] Please provide a message for DuckBot AI"
    
    try:
        token = get_duckbot_token()
        if not token:
            return "[FAIL] DuckBot server not available at http://localhost:8787"
        
        headers = {"Authorization": f"Bearer {token}"}
        data = {"message": message, "kind": task_type, "risk": "medium"}
        
        response = requests.post("http://localhost:8787/chat", headers=headers, data=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                ai_response = result.get("response", "No response")
                model = result.get("model", "unknown")
                confidence = result.get("confidence", 0)
                
                return f"[AI] **DuckBot AI:**\n\n{ai_response}\n\n[CHART] Model: {model} | Confidence: {confidence:.2f}"
            else:
                return f"[FAIL] AI Error: {result.get('response', 'Unknown error')}"
        else:
            return f"[FAIL] HTTP Error: {response.status_code}"
            
    except Exception as e:
        return f"[FAIL] Error: {str(e)}"


def duckbot_system_status() -> str:
    """
    Get DuckBot system status.
    
    :return: Complete system status report
    """
    
    try:
        token = get_duckbot_token()
        if not token:
            return "[FAIL] DuckBot server not available at http://localhost:8787"
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get AI status
        ai_response = requests.get("http://localhost:8787/api/system-status", headers=headers, timeout=10)
        services_response = requests.get("http://localhost:8787/api/services", headers=headers, timeout=10)
        
        report = "[LAUNCH] **DuckBot System Status**\n\n"
        
        # AI Status
        if ai_response.status_code == 200:
            ai_data = ai_response.json()
            if ai_data.get("ok"):
                status = ai_data.get("status", {})
                report += "[EMOJI] **AI System:**\n"
                report += f"• Model: {status.get('current_lm_model', 'Unknown')}\n"
                report += f"• Cache: {status.get('cache_size', 0)} items\n"
                report += f"• Chat Tokens: {status.get('chat_bucket_tokens', 0)}/{status.get('chat_bucket_limit', 30)}\n\n"
        
        # Services Status
        if services_response.status_code == 200:
            services_data = services_response.json()
            if services_data.get("ok"):
                services = services_data.get("services", [])
                report += "[SETTINGS] **Services:**\n"
                for svc in services:
                    name = svc.get("name", "Unknown")
                    status = svc.get("status", "unknown")
                    port = svc.get("port", "N/A")
                    emoji = "[OK]" if status == "running" else "[FAIL]"
                    report += f"{emoji} {name} (:{port}) - {status.title()}\n"
        
        return report
        
    except Exception as e:
        return f"[FAIL] Error getting status: {str(e)}"


def duckbot_start_service(service_name: str) -> str:
    """
    Start a DuckBot service.
    
    :param service_name: Service to start (comfyui, n8n, jupyter, lm_studio, webui)
    :return: Service start result
    """
    
    if not service_name:
        return "[FAIL] Please specify a service name (comfyui, n8n, jupyter, lm_studio, webui)"
    
    try:
        token = get_duckbot_token()
        if not token:
            return "[FAIL] DuckBot server not available"
        
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.post(f"http://localhost:8787/api/services/{service_name}/start", headers=headers, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                return f"[OK] Started {service_name}: {result.get('result', 'Success')}"
            else:
                return f"[FAIL] Failed to start {service_name}: {result.get('error', 'Unknown error')}"
        else:
            return f"[FAIL] HTTP Error {response.status_code}"
            
    except Exception as e:
        return f"[FAIL] Error starting {service_name}: {str(e)}"


def duckbot_stop_service(service_name: str) -> str:
    """
    Stop a DuckBot service.
    
    :param service_name: Service to stop (comfyui, n8n, jupyter, lm_studio, webui)
    :return: Service stop result
    """
    
    if not service_name:
        return "[FAIL] Please specify a service name"
    
    try:
        token = get_duckbot_token()
        if not token:
            return "[FAIL] DuckBot server not available"
        
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.post(f"http://localhost:8787/api/services/{service_name}/stop", headers=headers, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                return f"[OK] Stopped {service_name}: {result.get('result', 'Success')}"
            else:
                return f"[FAIL] Failed to stop {service_name}: {result.get('error', 'Unknown error')}"
        else:
            return f"[FAIL] HTTP Error {response.status_code}"
            
    except Exception as e:
        return f"[FAIL] Error stopping {service_name}: {str(e)}"


def duckbot_cost_summary(days: int = 7) -> str:
    """
    Get DuckBot usage and cost summary.
    
    :param days: Number of days to analyze (1-365)
    :return: Cost and usage summary
    """
    
    try:
        token = get_duckbot_token()
        if not token:
            return "[FAIL] DuckBot server not available"
        
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.get(f"http://localhost:8787/api/cost_summary?days={days}", headers=headers, timeout=15)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                data = result.get("data", {})
                
                summary = f"[EMOJI] **Cost Summary ({days} days)**\n\n"
                summary += f"[EMOJI] Total Cost: ${data.get('total_cost', 0):.4f}\n"
                summary += f"[EMOJI] Total Tokens: {data.get('total_tokens', 0):,}\n"
                summary += f"[CHART] Total Requests: {data.get('total_requests', 0):,}\n\n"
                
                by_model = data.get("by_model", {})
                if by_model:
                    summary += "[AI] **By Model:**\n"
                    for model, cost in sorted(by_model.items(), key=lambda x: x[1], reverse=True)[:5]:
                        summary += f"• {model}: ${cost:.4f}\n"
                    summary += "\n"
                
                predictions = data.get("predictions", {})
                if predictions:
                    summary += "[EMOJI] **Projections:**\n"
                    summary += f"• Daily Avg: ${predictions.get('daily_average', 0):.4f}\n"
                    summary += f"• Monthly: ${predictions.get('monthly_cost', 0):.2f}\n"
                
                return summary
            else:
                return f"[FAIL] Cost data error: {result.get('error', 'Unknown error')}"
        else:
            return f"[FAIL] HTTP Error {response.status_code}"
            
    except Exception as e:
        return f"[FAIL] Error getting cost summary: {str(e)}"


def duckbot_rag_search(query: str, top_k: int = 5) -> str:
    """
    Search DuckBot's RAG knowledge base.
    
    :param query: Search query for the knowledge base
    :param top_k: Number of results to return (1-20)
    :return: Search results from RAG system
    """
    
    if not query.strip():
        return "[FAIL] Please provide a search query"
    
    try:
        token = get_duckbot_token()
        if not token:
            return "[FAIL] DuckBot server not available"
        
        headers = {"Authorization": f"Bearer {token}"}
        data = {"q": query, "top_k": min(top_k, 20)}
        
        response = requests.post("http://localhost:8787/rag/search", headers=headers, data=data, timeout=15)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("ok"):
                context = result.get("context", "")
                chunks = result.get("chunks", [])
                
                if not context:
                    return f"[EMOJI] No results found for: '{query}'"
                
                search_result = f"[EMOJI] **Search Results:** '{query}'\n\n"
                search_result += f"**Context:**\n{context[:600]}{'...' if len(context) > 600 else ''}\n\n"
                
                if chunks:
                    search_result += f"**Sources ({len(chunks)} found):**\n"
                    for i, chunk in enumerate(chunks[:3], 1):
                        source = chunk.get("metadata", {}).get("source", "Unknown")
                        search_result += f"{i}. {source}\n"
                
                return search_result
            else:
                return f"[FAIL] RAG search failed: {result.get('error', 'Knowledge base unavailable')}"
        else:
            return f"[FAIL] HTTP Error {response.status_code}"
            
    except Exception as e:
        return f"[FAIL] Error searching RAG: {str(e)}"


def duckbot_list_models() -> str:
    """
    Get available AI models from LM Studio.
    
    :return: List of available AI models
    """
    
    try:
        token = get_duckbot_token()
        if not token:
            return "[FAIL] DuckBot server not available"
        
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.get("http://localhost:8787/models/available", headers=headers, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("ok"):
                models = result.get("models", [])
                
                if not models:
                    return "[EMOJI] No models loaded in LM Studio\n\nStart LM Studio and load a model first."
                
                model_list = f"[AI] **Available Models ({len(models)})**\n\n"
                
                for i, model in enumerate(models[:10], 1):
                    model_id = model.get("id", "Unknown")
                    size = model.get("size", "Unknown")
                    model_list += f"{i}. {model_id} ({size})\n"
                
                if len(models) > 10:
                    model_list += f"\n... and {len(models) - 10} more models"
                
                return model_list
            else:
                return f"[FAIL] Models unavailable: {result.get('error', 'LM Studio offline')}"
        else:
            return f"[FAIL] HTTP Error {response.status_code}"
            
    except Exception as e:
        return f"[FAIL] Error getting models: {str(e)}"