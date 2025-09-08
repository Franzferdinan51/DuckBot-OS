"""
title: DuckBot Control
author: open-webui
author_url: https://github.com/open-webui
funding_url: https://github.com/sponsors/tjbck
version: 0.1.0
license: MIT
description: Control your DuckBot ecosystem - chat with AI, manage services, get analytics
required_open_webui_version: 0.3.0
requirements: requests
"""

import requests
from typing import Optional


class Tools:
    def __init__(self):
        self.duckbot_url = "http://localhost:8787"
        self.token = None

    def get_duckbot_token(self) -> Optional[str]:
        """Get DuckBot authentication token"""
        if self.token:
            return self.token
            
        try:
            response = requests.get(f"{self.duckbot_url}/token", timeout=5)
            if response.status_code == 200:
                self.token = response.json().get("token")
                return self.token
        except:
            return None

    def duckbot_ai_chat(self, message: str, task_type: str = "auto") -> str:
        """
        Chat with DuckBot AI system.
        
        :param message: Your message or question for DuckBot AI
        :param task_type: Type of AI task - auto, code, reasoning, summary, long_form
        :return: AI response from DuckBot
        """
        
        if not message.strip():
            return "❌ Please provide a message for DuckBot AI"
        
        try:
            token = self.get_duckbot_token()
            if not token:
                return "❌ DuckBot server not available at http://localhost:8787. Make sure DuckBot is running."
            
            headers = {"Authorization": f"Bearer {token}"}
            data = {"message": message, "kind": task_type, "risk": "medium"}
            
            response = requests.post(f"{self.duckbot_url}/chat", headers=headers, data=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    ai_response = result.get("response", "No response")
                    model = result.get("model", "unknown")
                    confidence = result.get("confidence", 0)
                    
                    return f"🤖 **DuckBot AI Response:**\n\n{ai_response}\n\n📊 **Details:** Model: {model} | Confidence: {confidence:.2f}"
                else:
                    return f"❌ **AI Error:** {result.get('response', 'Unknown error')}"
            else:
                return f"❌ **HTTP Error:** {response.status_code} - {response.text}"
                
        except requests.exceptions.ConnectionError:
            return "❌ **Connection Error:** Cannot connect to DuckBot server. Is it running at localhost:8787?"
        except requests.exceptions.Timeout:
            return "❌ **Timeout Error:** Request timed out. DuckBot may be busy processing."
        except Exception as e:
            return f"❌ **Unexpected Error:** {str(e)}"

    def duckbot_system_status(self) -> str:
        """
        Get DuckBot system status and service information.
        
        :return: Complete system status report
        """
        
        try:
            token = self.get_duckbot_token()
            if not token:
                return "❌ **DuckBot Offline:** Server not available at http://localhost:8787"
            
            headers = {"Authorization": f"Bearer {token}"}
            
            # Get system status
            ai_response = requests.get(f"{self.duckbot_url}/api/system-status", headers=headers, timeout=10)
            services_response = requests.get(f"{self.duckbot_url}/api/services", headers=headers, timeout=10)
            
            report = "🚀 **DuckBot System Status**\n\n"
            
            # AI System Status
            if ai_response.status_code == 200:
                ai_data = ai_response.json()
                if ai_data.get("ok"):
                    status = ai_data.get("status", {})
                    report += "🧠 **AI System:**\n"
                    report += f"• **Model:** {status.get('current_lm_model', 'Unknown')}\n"
                    report += f"• **Cache:** {status.get('cache_size', 0)} items\n"
                    report += f"• **Chat Tokens:** {status.get('chat_bucket_tokens', 0)}/{status.get('chat_bucket_limit', 30)}\n"
                    report += f"• **Background Tokens:** {status.get('background_bucket_tokens', 0)}/{status.get('background_bucket_limit', 30)}\n\n"
            
            # Services Status
            if services_response.status_code == 200:
                services_data = services_response.json()
                if services_data.get("ok"):
                    services = services_data.get("services", [])
                    report += "⚙️ **Services Status:**\n"
                    for svc in services:
                        name = svc.get("name", "Unknown")
                        status = svc.get("status", "unknown")
                        port = svc.get("port", "N/A")
                        emoji = "✅" if status == "running" else "❌"
                        report += f"{emoji} **{name}** (Port {port}) - {status.title()}\n"
                    
                    # Count running services
                    running_count = sum(1 for svc in services if svc.get("status") == "running")
                    total_count = len(services)
                    report += f"\n📊 **Summary:** {running_count}/{total_count} services running"
                else:
                    report += "⚠️ **Services:** Status unavailable\n"
            else:
                report += "⚠️ **Services:** Cannot retrieve service status\n"
            
            return report
            
        except Exception as e:
            return f"❌ **Error getting system status:** {str(e)}"

    def duckbot_start_service(self, service_name: str) -> str:
        """
        Start a specific DuckBot service.
        
        :param service_name: Service to start (comfyui, n8n, jupyter, lm_studio, webui, open_notebook)
        :return: Service start operation result
        """
        
        if not service_name.strip():
            available_services = ["comfyui", "n8n", "jupyter", "lm_studio", "webui", "open_notebook"]
            return f"❌ **Missing Service Name**\n\nAvailable services: {', '.join(available_services)}"
        
        try:
            token = self.get_duckbot_token()
            if not token:
                return "❌ **DuckBot Offline:** Cannot connect to server"
            
            headers = {"Authorization": f"Bearer {token}"}
            
            response = requests.post(f"{self.duckbot_url}/api/services/{service_name}/start", headers=headers, timeout=45)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    message = result.get("result", "Started successfully")
                    return f"✅ **Service Started**\n\n**{service_name.title()}:** {message}"
                else:
                    error = result.get("error", "Unknown error occurred")
                    return f"❌ **Failed to Start {service_name.title()}**\n\n**Error:** {error}"
            else:
                return f"❌ **HTTP Error {response.status_code}**\n\nFailed to start {service_name}"
                
        except requests.exceptions.Timeout:
            return f"⏱️ **Timeout Starting {service_name.title()}**\n\nService may be starting in background. Check status in a moment."
        except Exception as e:
            return f"❌ **Error starting {service_name}:** {str(e)}"

    def duckbot_stop_service(self, service_name: str) -> str:
        """
        Stop a specific DuckBot service.
        
        :param service_name: Service to stop (comfyui, n8n, jupyter, lm_studio, webui, open_notebook)
        :return: Service stop operation result
        """
        
        if not service_name.strip():
            return "❌ **Missing Service Name:** Please specify which service to stop"
        
        try:
            token = self.get_duckbot_token()
            if not token:
                return "❌ **DuckBot Offline:** Cannot connect to server"
            
            headers = {"Authorization": f"Bearer {token}"}
            
            response = requests.post(f"{self.duckbot_url}/api/services/{service_name}/stop", headers=headers, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    message = result.get("result", "Stopped successfully")
                    return f"🛑 **Service Stopped**\n\n**{service_name.title()}:** {message}"
                else:
                    error = result.get("error", "Unknown error occurred")
                    return f"❌ **Failed to Stop {service_name.title()}**\n\n**Error:** {error}"
            else:
                return f"❌ **HTTP Error {response.status_code}**\n\nFailed to stop {service_name}"
                
        except Exception as e:
            return f"❌ **Error stopping {service_name}:** {str(e)}"

    def duckbot_cost_summary(self, days: int = 7) -> str:
        """
        Get DuckBot cost and usage analytics.
        
        :param days: Number of days to analyze (1-365)
        :return: Detailed cost and usage summary
        """
        
        if days < 1 or days > 365:
            return "❌ **Invalid Days:** Please specify 1-365 days"
        
        try:
            token = self.get_duckbot_token()
            if not token:
                return "❌ **DuckBot Offline:** Cannot retrieve cost data"
            
            headers = {"Authorization": f"Bearer {token}"}
            
            response = requests.get(f"{self.duckbot_url}/api/cost_summary?days={days}", headers=headers, timeout=15)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    data = result.get("data", {})
                    
                    summary = f"💰 **Cost Summary ({days} days)**\n\n"
                    
                    # Main metrics
                    total_cost = data.get('total_cost', 0)
                    total_tokens = data.get('total_tokens', 0)
                    total_requests = data.get('total_requests', 0)
                    
                    summary += f"💵 **Total Cost:** ${total_cost:.4f}\n"
                    summary += f"🔢 **Total Tokens:** {total_tokens:,}\n"
                    summary += f"📊 **Total Requests:** {total_requests:,}\n\n"
                    
                    # Cost per request
                    if total_requests > 0:
                        cost_per_request = total_cost / total_requests
                        summary += f"💸 **Avg Cost/Request:** ${cost_per_request:.6f}\n\n"
                    
                    # Model breakdown
                    by_model = data.get("by_model", {})
                    if by_model:
                        summary += "🤖 **Usage by Model:**\n"
                        for model, cost in sorted(by_model.items(), key=lambda x: x[1], reverse=True)[:5]:
                            percentage = (cost / total_cost * 100) if total_cost > 0 else 0
                            summary += f"• **{model}:** ${cost:.4f} ({percentage:.1f}%)\n"
                        summary += "\n"
                    
                    # Predictions
                    predictions = data.get("predictions", {})
                    if predictions:
                        summary += "📈 **Projections:**\n"
                        daily_avg = predictions.get('daily_average', 0)
                        monthly_proj = predictions.get('monthly_cost', 0)
                        summary += f"• **Daily Average:** ${daily_avg:.4f}\n"
                        summary += f"• **Monthly Projection:** ${monthly_proj:.2f}\n"
                    
                    return summary
                else:
                    return f"❌ **Cost Data Error:** {result.get('error', 'Analytics system unavailable')}"
            else:
                return f"❌ **HTTP Error {response.status_code}:** Cannot retrieve cost data"
                
        except Exception as e:
            return f"❌ **Error getting cost summary:** {str(e)}"

    def duckbot_rag_search(self, query: str, top_k: int = 5) -> str:
        """
        Search DuckBot's RAG knowledge base.
        
        :param query: Search query for the knowledge base
        :param top_k: Number of results to return (1-20)
        :return: Search results from the knowledge base
        """
        
        if not query.strip():
            return "❌ **Missing Query:** Please provide a search query for the knowledge base"
        
        # Limit top_k to reasonable range
        top_k = max(1, min(top_k, 20))
        
        try:
            token = self.get_duckbot_token()
            if not token:
                return "❌ **DuckBot Offline:** Cannot access knowledge base"
            
            headers = {"Authorization": f"Bearer {token}"}
            data = {"q": query, "top_k": top_k}
            
            response = requests.post(f"{self.duckbot_url}/rag/search", headers=headers, data=data, timeout=20)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("ok"):
                    context = result.get("context", "")
                    chunks = result.get("chunks", [])
                    
                    if not context:
                        return f"🔍 **No Results Found**\n\nNo relevant information found for query: '{query}'\n\nTry different keywords or check if documents are indexed."
                    
                    search_result = f"🔍 **Knowledge Base Search Results**\n\n"
                    search_result += f"**Query:** {query}\n"
                    search_result += f"**Results Found:** {len(chunks)}\n\n"
                    
                    # Context (truncated for readability)
                    context_preview = context[:800] if len(context) > 800 else context
                    search_result += f"**📄 Relevant Content:**\n{context_preview}"
                    if len(context) > 800:
                        search_result += "\n\n*(Content truncated for display)*"
                    
                    # Sources
                    if chunks:
                        search_result += f"\n\n**📚 Sources ({len(chunks)} documents):**\n"
                        for i, chunk in enumerate(chunks[:5], 1):  # Show top 5 sources
                            source = chunk.get("metadata", {}).get("source", "Unknown source")
                            search_result += f"{i}. {source}\n"
                        
                        if len(chunks) > 5:
                            search_result += f"... and {len(chunks) - 5} more sources"
                    
                    return search_result
                else:
                    error_msg = result.get("error", "Knowledge base search failed")
                    return f"❌ **RAG Search Failed:** {error_msg}"
            else:
                return f"❌ **HTTP Error {response.status_code}:** Cannot access knowledge base"
                
        except Exception as e:
            return f"❌ **Error searching knowledge base:** {str(e)}"

    def duckbot_list_models(self) -> str:
        """
        Get available AI models from LM Studio.
        
        :return: List of available AI models and their details
        """
        
        try:
            token = self.get_duckbot_token()
            if not token:
                return "❌ **DuckBot Offline:** Cannot retrieve model information"
            
            headers = {"Authorization": f"Bearer {token}"}
            
            response = requests.get(f"{self.duckbot_url}/models/available", headers=headers, timeout=15)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("ok"):
                    models = result.get("models", [])
                    lm_studio_url = result.get("lm_studio_url", "http://localhost:1234")
                    
                    if not models:
                        return f"📭 **No Models Available**\n\n**LM Studio Status:** {lm_studio_url}\n\n**Solution:**\n1. Start LM Studio\n2. Load at least one chat model\n3. Enable the local server\n4. Refresh this command"
                    
                    model_list = f"🤖 **Available AI Models**\n\n"
                    model_list += f"**LM Studio Server:** {lm_studio_url}\n"
                    model_list += f"**Models Loaded:** {len(models)}\n\n"
                    
                    # Show models with details
                    for i, model in enumerate(models[:12], 1):  # Show up to 12 models
                        model_id = model.get("id", "Unknown")
                        size_info = model.get("size", "Unknown size")
                        
                        # Try to extract useful info from model ID
                        model_name = model_id.split("/")[-1] if "/" in model_id else model_id
                        model_list += f"**{i}. {model_name}**\n"
                        model_list += f"   • ID: {model_id}\n"
                        model_list += f"   • Size: {size_info}\n\n"
                    
                    if len(models) > 12:
                        model_list += f"... and **{len(models) - 12}** more models available\n\n"
                    
                    model_list += "💡 **Tip:** Use `duckbot_ai_chat()` to interact with the active model"
                    
                    return model_list
                else:
                    error_msg = result.get("error", "LM Studio connection failed")
                    return f"❌ **Models Unavailable:** {error_msg}\n\n**Check:**\n• LM Studio is running\n• Local server is enabled\n• At least one model is loaded"
            else:
                return f"❌ **HTTP Error {response.status_code}:** Cannot retrieve model information"
                
        except Exception as e:
            return f"❌ **Error getting models:** {str(e)}"