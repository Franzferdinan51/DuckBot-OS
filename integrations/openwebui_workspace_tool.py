"""
title: DuckBot Workspace Tool
author: open-webui
author_url: https://github.com/open-webui
funding_url: https://github.com/sponsors/tjbck
version: 2.0.0
license: MIT
description: Complete DuckBot integration for OpenWebUI workspace - execute AI tasks, manage services, analytics, RAG, and system control
requirements: requests
"""

import requests
import json
from typing import Optional


class Tools:
    def __init__(self):
        self.duckbot_url = "http://localhost:8787"
        self.token = None

    def get_duckbot_token(self) -> Optional[str]:
        """Auto-detect DuckBot WebUI token"""
        if self.token:
            return self.token
            
        try:
            response = requests.get(f"{self.duckbot_url}/token", timeout=5)
            if response.status_code == 200:
                self.token = response.json().get("token")
                return self.token
        except:
            return None

    def make_request(self, method: str, endpoint: str, data=None, params=None):
        """Make authenticated request to DuckBot"""
        token = self.get_duckbot_token()
        if not token:
            return {"error": "DuckBot server not available at http://localhost:8787"}
        
        url = f"{self.duckbot_url}{endpoint}"
        headers = {"Authorization": f"Bearer {token}"}
        
        try:
            if method == "GET":
                response = requests.get(url, headers=headers, params=params, timeout=30)
            else:
                response = requests.post(url, headers=headers, data=data, timeout=30)
            
            if response.status_code == 200:
                try:
                    return response.json()
                except:
                    return {"success": True, "response": response.text}
            else:
                return {"error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            return {"error": str(e)}

    def duckbot_ai_chat(
        self, 
        message: str, 
        task_type: str = "auto", 
        priority: str = "medium"
    ) -> str:
        """
        Chat with DuckBot AI system.
        
        :param message: Your message or question for DuckBot AI
        :param task_type: Type of AI task - auto, code, reasoning, summary, long_form, json_format, policy, arbiter
        :param priority: Priority level - low, medium, high
        :return: AI response from DuckBot
        """
        if not message.strip():
            return "Error: Please provide a message for DuckBot AI"
        
        data = {"message": message, "kind": task_type, "risk": priority}
        result = self.make_request("POST", "/chat", data=data)
        
        if "error" in result:
            return f"[FAIL] Error: {result['error']}"
        
        if result.get("success"):
            response = result.get("response", "No response")
            model = result.get("model", "unknown")
            confidence = result.get("confidence", 0)
            cached = " (cached)" if result.get("cached") else ""
            
            return f"[AI] **DuckBot AI:**\n\n{response}\n\n[CHART] Model: {model} | Confidence: {confidence:.2f}{cached}"
        
        return f"[FAIL] Failed: {result}"

    def duckbot_system_status(self) -> str:
        """
        Get comprehensive DuckBot system status.
        
        :return: Complete system status report
        """
        ai_status = self.make_request("GET", "/api/system-status")
        services_status = self.make_request("GET", "/api/services")
        
        report = "[LAUNCH] **DuckBot System Status**\n\n"
        
        # AI Status
        if ai_status.get("ok"):
            ai = ai_status.get("status", {})
            report += "[EMOJI] **AI System:**\n"
            report += f"• Model: {ai.get('current_lm_model', 'Unknown')}\n"
            report += f"• Cache: {ai.get('cache_size', 0)} items\n"
            report += f"• Chat Tokens: {ai.get('chat_bucket_tokens', 0)}/{ai.get('chat_bucket_limit', 30)}\n\n"
        
        # Services Status
        if services_status.get("ok"):
            services = services_status.get("services", [])
            report += "[SETTINGS] **Services:**\n"
            for svc in services:
                name = svc.get("name", "Unknown")
                status = svc.get("status", "unknown")
                port = svc.get("port", "N/A")
                emoji = "[OK]" if status == "running" else "[FAIL]"
                report += f"{emoji} {name} (:{port}) - {status.title()}\n"
        
        return report

    def duckbot_manage_service(
        self, 
        service_name: str, 
        action: str
    ) -> str:
        """
        Manage DuckBot services.
        
        :param service_name: Service name - comfyui, n8n, jupyter, lm_studio, webui, open_notebook
        :param action: Action to perform - start, stop, restart
        :return: Result of service management operation
        """
        if action not in ["start", "stop", "restart"]:
            return "[FAIL] Invalid action. Use: start, stop, restart"
        
        result = self.make_request("POST", f"/api/services/{service_name}/{action}")
        
        if result.get("success"):
            message = result.get("result", f"Service {action} completed")
            return f"[OK] {service_name}: {message}"
        else:
            error = result.get("error", "Unknown error")
            return f"[FAIL] Failed to {action} {service_name}: {error}"

    def duckbot_cost_summary(self, days: int = 7) -> str:
        """
        Get DuckBot usage and cost analytics.
        
        :param days: Number of days to analyze (1-365)
        :return: Detailed cost and usage summary
        """
        result = self.make_request("GET", "/api/cost_summary", params={"days": days})
        
        if not result.get("success"):
            return f"[FAIL] Cost data unavailable: {result.get('error', 'Analytics system offline')}"
        
        data = result.get("data", {})
        
        summary = f"[EMOJI] **Cost Summary ({days} days)**\n\n"
        summary += f"[EMOJI] Total Cost: ${data.get('total_cost', 0):.4f}\n"
        summary += f"[EMOJI] Total Tokens: {data.get('total_tokens', 0):,}\n"
        summary += f"[CHART] Total Requests: {data.get('total_requests', 0):,}\n\n"
        
        # Model breakdown
        by_model = data.get("by_model", {})
        if by_model:
            summary += "[AI] **By Model:**\n"
            for model, cost in sorted(by_model.items(), key=lambda x: x[1], reverse=True)[:5]:
                summary += f"• {model}: ${cost:.4f}\n"
            summary += "\n"
        
        # Predictions
        predictions = data.get("predictions", {})
        if predictions:
            summary += "[EMOJI] **Projections:**\n"
            summary += f"• Daily Avg: ${predictions.get('daily_average', 0):.4f}\n"
            summary += f"• Monthly: ${predictions.get('monthly_cost', 0):.2f}\n"
        
        return summary

    def duckbot_rag_search(
        self, 
        query: str, 
        top_k: int = 5
    ) -> str:
        """
        Search DuckBot's RAG knowledge base.
        
        :param query: Search query for the knowledge base
        :param top_k: Number of results to return (1-20)
        :return: Search results from RAG system
        """
        if not query.strip():
            return "[FAIL] Please provide a search query"
        
        data = {"q": query, "top_k": min(top_k, 20)}
        result = self.make_request("POST", "/rag/search", data=data)
        
        if not result.get("ok"):
            return f"[FAIL] RAG search failed: {result.get('error', 'Knowledge base unavailable')}"
        
        context = result.get("context", "")
        chunks = result.get("chunks", [])
        
        if not context:
            return f"[EMOJI] No results found for: '{query}'"
        
        response = f"[EMOJI] **Search Results:** '{query}'\n\n"
        response += f"**Context:**\n{context[:600]}{'...' if len(context) > 600 else ''}\n\n"
        
        if chunks:
            response += f"**Sources ({len(chunks)} found):**\n"
            for i, chunk in enumerate(chunks[:3], 1):
                source = chunk.get("metadata", {}).get("source", "Unknown")
                response += f"{i}. {source}\n"
        
        return response

    def duckbot_list_models(self) -> str:
        """
        Get available AI models from LM Studio.
        
        :return: List of available AI models
        """
        result = self.make_request("GET", "/models/available")
        
        if not result.get("ok"):
            return f"[FAIL] Models unavailable: {result.get('error', 'LM Studio offline')}"
        
        models = result.get("models", [])
        if not models:
            return "[EMOJI] No models loaded in LM Studio"
        
        response = f"[AI] **Available Models ({len(models)})**\n\n"
        
        for i, model in enumerate(models[:10], 1):
            model_id = model.get("id", "Unknown")
            size = model.get("size", "Unknown")
            response += f"{i}. {model_id} ({size})\n"
        
        if len(models) > 10:
            response += f"\n... and {len(models) - 10} more"
        
        return response

    def duckbot_ecosystem_start(self) -> str:
        """
        Start the complete DuckBot ecosystem.
        
        :return: Results of ecosystem startup
        """
        result = self.make_request("POST", "/ecosystem/start")
        
        if result.get("ok"):
            results = result.get("results", {})
            report = "[EMOJI] **Ecosystem Start Results:**\n\n"
            
            for service, status in results.items():
                emoji = "[OK]" if "success" in str(status).lower() else "[FAIL]"
                report += f"{emoji} {service}: {status}\n"
            
            return report
        else:
            return f"[FAIL] Ecosystem start failed: {result.get('error', 'Unknown error')}"

    def duckbot_ecosystem_stop(self) -> str:
        """
        Stop the complete DuckBot ecosystem.
        
        :return: Results of ecosystem shutdown
        """
        result = self.make_request("POST", "/ecosystem/stop")
        
        if result.get("ok"):
            results = result.get("results", {})
            report = "[STOP] **Ecosystem Stop Results:**\n\n"
            
            for service, status in results.items():
                emoji = "[OK]" if "success" in str(status).lower() else "[FAIL]"
                report += f"{emoji} {service}: {status}\n"
            
            return report
        else:
            return f"[FAIL] Ecosystem stop failed: {result.get('error', 'Unknown error')}"

    def duckbot_cache_clear(self) -> str:
        """
        Clear DuckBot's AI response cache.
        
        :return: Cache clear result
        """
        result = self.make_request("POST", "/cache/clear")
        
        if result.get("ok"):
            return "[OK] AI cache cleared successfully"
        else:
            return "[FAIL] Failed to clear cache"

    def duckbot_qwen_analyze(self, code: str) -> str:
        """
        Analyze code using DuckBot's Qwen enhanced system.
        
        :param code: Code or code-related prompt to analyze
        :return: Code analysis results
        """
        if not code.strip():
            return "[FAIL] Please provide code to analyze"
        
        data = {"code_prompt": code}
        result = self.make_request("POST", "/qwen/analyze", data=data)
        
        if result.get("ok"):
            analysis = result.get("analysis", "No analysis available")
            enhanced = " (Qwen Enhanced)" if result.get("qwen_enhanced") else ""
            return f"[EMOJI] **Code Analysis{enhanced}:**\n\n{analysis}"
        else:
            return f"[FAIL] Analysis failed: {result.get('error', 'Qwen unavailable')}"

    def duckbot_action_logs(self, hours: int = 24) -> str:
        """
        Get DuckBot action and reasoning logs.
        
        :param hours: Hours of logs to retrieve (1-168)
        :return: Recent action logs
        """
        params = {"hours": min(hours, 168), "limit": 20}
        result = self.make_request("GET", "/api/action-logs", params=params)
        
        if not result.get("ok"):
            return f"[FAIL] Logs unavailable: {result.get('error', 'Logging offline')}"
        
        logs = result.get("logs", [])
        if not logs:
            return f"[LIST] No logs found (last {hours} hours)"
        
        report = f"[LIST] **Action Logs** (last {hours} hours, {len(logs)} entries):\n\n"
        
        for i, log in enumerate(logs[:10], 1):
            timestamp = log.get("timestamp", "Unknown")
            action = log.get("action_type", "Unknown")
            component = log.get("component", "Unknown")
            
            report += f"{i}. **{timestamp}** - {action} ({component})\n"
        
        if len(logs) > 10:
            report += f"\n... and {len(logs) - 10} more entries"
        
        return report