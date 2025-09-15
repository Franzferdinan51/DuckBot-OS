"""
title: DuckBot Complete Command Tool
author: DuckBot Integration Team  
version: 2.0.0
description: Complete integration tool for all DuckBot features including AI, services, analytics, RAG, voice, image generation, and Discord commands
requirements: requests
"""

import requests
import json
import time
from typing import Dict, Any, Optional, List


class Tools:
    def __init__(self):
        self.duckbot_url = "http://localhost:8787"  # DuckBot WebUI
        self.token = None
        self.timeout = 60  # Longer timeout for complex operations

    def get_duckbot_token(self) -> Optional[str]:
        """Auto-detect DuckBot WebUI token"""
        if self.token:
            return self.token
            
        try:
            response = requests.get(f"{self.duckbot_url}/token", timeout=5)
            if response.status_code == 200:
                token_info = response.json()
                self.token = token_info.get("token")
                return self.token
        except Exception:
            pass
            
        return None

    def make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, 
                    params: Optional[Dict] = None, files: Optional[Dict] = None) -> Dict[str, Any]:
        """Make authenticated request to DuckBot server"""
        token = self.get_duckbot_token()
        if not token:
            return {"error": "No DuckBot token available. Please ensure DuckBot WebUI is running at http://localhost:8787"}
        
        url = f"{self.duckbot_url}{endpoint}"
        headers = {"Authorization": f"Bearer {token}"}
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, params=params, timeout=self.timeout)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, data=data, files=files, timeout=self.timeout)
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
            return {"error": f"Request timed out after {self.timeout}s. DuckBot may be processing a complex task."}
        except requests.exceptions.ConnectionError:
            return {"error": "Could not connect to DuckBot server. Ensure it's running at http://localhost:8787"}
        except Exception as e:
            return {"error": f"Request failed: {str(e)}"}

    # ===== CORE AI FUNCTIONS =====
    
    def duckbot_ai_chat(self, message: str, task_type: str = "auto", priority: str = "medium") -> str:
        """
        Chat with DuckBot AI - supports all AI task types
        
        Args:
            message: Your message/question for the AI
            task_type: auto, code, reasoning, summary, long_form, json_format, policy, arbiter
            priority: low, medium, high
        """
        if not message.strip():
            return "Error: Please provide a message for DuckBot AI"
        
        data = {
            "message": message,
            "kind": task_type,
            "risk": priority
        }
        
        result = self.make_request("POST", "/chat", data=data)
        
        if "error" in result:
            return f"[FAIL] Error: {result['error']}"
        
        if result.get("success"):
            response = result.get("response", "No response")
            model = result.get("model", "unknown")
            confidence = result.get("confidence", 0)
            cached = result.get("cached", False)
            
            cache_info = " (cached)" if cached else ""
            return f"[AI] **DuckBot AI Response:**\n\n{response}\n\n[CHART] **Details:** Model: {model} | Confidence: {confidence:.2f}{cache_info}"
        
        return f"[FAIL] Failed: {result}"

    def duckbot_task_runner(self, task_type: str, prompt: str, priority: str = "medium") -> str:
        """
        Execute tasks via the DuckBot Task Runner interface
        
        Args:
            task_type: code, reasoning, summary, long_form, json_format, policy, arbiter
            prompt: The task prompt
            priority: low, medium, high
        """
        data = {
            "kind": task_type,
            "risk": priority,
            "prompt": prompt,
            "override": ""
        }
        
        result = self.make_request("POST", "/api/task", data=data)
        
        if result.get("success"):
            task_result = result.get("result", {})
            response = task_result.get("text", "No response")
            model = task_result.get("model_used", "unknown")
            
            return f"⚡ **Task Runner Result:**\n\n{response}\n\n[CHART] **Model:** {model}"
        else:
            return f"[FAIL] Task failed: {result.get('error', 'Unknown error')}"

    def duckbot_queue_task(self, task_type: str, prompt: str, priority: str = "low") -> str:
        """
        Queue a task for background processing
        
        Args:
            task_type: Type of task to queue
            prompt: Task prompt
            priority: Task priority
        """
        data = {
            "kind": task_type,
            "risk": priority,
            "prompt": prompt
        }
        
        result = self.make_request("POST", "/queue", data=data)
        
        if "queued" in result:
            return f"[OK] Task queued successfully. Queue position: {result['queued']}"
        else:
            return f"[FAIL] Failed to queue task: {result.get('error', 'Unknown error')}"

    # ===== SYSTEM MANAGEMENT =====
    
    def duckbot_system_status(self) -> str:
        """Get comprehensive DuckBot system status"""
        ai_status = self.make_request("GET", "/api/system-status")
        services_status = self.make_request("GET", "/api/services")
        servers_status = self.make_request("GET", "/servers/status")
        
        report = "[LAUNCH] **DuckBot System Status**\n\n"
        
        # AI Router Status
        if ai_status.get("ok"):
            ai_info = ai_status.get("status", {})
            report += "[EMOJI] **AI Router:**\n"
            report += f"• Current Model: {ai_info.get('current_lm_model', 'Unknown')}\n"
            report += f"• Cache Size: {ai_info.get('cache_size', 0)} items\n"
            report += f"• Chat Tokens: {ai_info.get('chat_bucket_tokens', 0)}/{ai_info.get('chat_bucket_limit', 30)}\n"
            report += f"• Background Tokens: {ai_info.get('background_bucket_tokens', 0)}/{ai_info.get('background_bucket_limit', 30)}\n\n"
        
        # Services Status
        if services_status.get("ok"):
            services = services_status.get("services", [])
            report += "[SETTINGS] **Services:**\n"
            for service in services:
                name = service.get("name", "Unknown")
                status = service.get("status", "unknown")
                port = service.get("port", "N/A")
                
                status_emoji = "[OK]" if status == "running" else "[FAIL]"
                report += f"{status_emoji} {name} (:{port}) - {status.title()}\n"
            report += "\n"
        
        # Servers Status (ecosystem services)
        if servers_status.get("ok"):
            servers = servers_status.get("services", {})
            if servers:
                report += "[EMOJI][EMOJI] **Ecosystem Services:**\n"
                for name, info in servers.items():
                    status = info.get("status", "unknown")
                    port = info.get("port", "N/A")
                    status_emoji = "[OK]" if status == "running" else "[FAIL]"
                    report += f"{status_emoji} {name} (:{port}) - {status.title()}\n"
        
        return report

    def duckbot_manage_service(self, service_name: str, action: str) -> str:
        """
        Manage DuckBot services (start/stop/restart)
        
        Args:
            service_name: comfyui, n8n, jupyter, lm_studio, webui, open_notebook
            action: start, stop, restart
        """
        if action not in ["start", "stop", "restart"]:
            return "[FAIL] Invalid action. Use: start, stop, or restart"
        
        # Try both service management endpoints
        endpoint1 = f"/api/services/{service_name}/{action}"
        endpoint2 = f"/servers/{action}"
        
        # First try the services endpoint
        result = self.make_request("POST", endpoint1)
        
        if not result.get("success") and action != "restart":
            # Try the servers endpoint for start/stop
            data = {"service_name": service_name}
            result = self.make_request("POST", endpoint2, data=data)
        
        if result.get("success") or result.get("ok"):
            message = result.get("result", result.get("message", f"Service {action} completed"))
            return f"[OK] {service_name}: {message}"
        else:
            error = result.get("error", "Unknown error")
            return f"[FAIL] Failed to {action} {service_name}: {error}"

    def duckbot_ecosystem_control(self, action: str) -> str:
        """
        Control entire DuckBot ecosystem
        
        Args:
            action: start, stop
        """
        if action not in ["start", "stop"]:
            return "[FAIL] Invalid action. Use: start or stop"
        
        result = self.make_request("POST", f"/ecosystem/{action}")
        
        if result.get("ok"):
            results = result.get("results", {})
            report = f"[EMOJI] **Ecosystem {action.title()} Results:**\n\n"
            
            for service, status in results.items():
                status_emoji = "[OK]" if "success" in str(status).lower() else "[FAIL]"
                report += f"{status_emoji} {service}: {status}\n"
            
            return report
        else:
            return f"[FAIL] Failed to {action} ecosystem: {result.get('error', 'Unknown error')}"

    def duckbot_detect_services(self) -> str:
        """Detect available services and get startup recommendations"""
        result = self.make_request("GET", "/services/detect")
        
        if result.get("ok"):
            services = result.get("services", {})
            recommendations = result.get("recommendations", [])
            
            report = "[EMOJI] **Service Detection:**\n\n"
            
            for service_name, service_info in services.items():
                status = service_info.get("status", "unknown")
                port = service_info.get("port", "N/A")
                status_emoji = "[OK]" if status in ["running_healthy", "running_unhealthy"] else "[FAIL]"
                report += f"{status_emoji} {service_name} (:{port}) - {status.replace('_', ' ').title()}\n"
            
            if recommendations:
                report += "\n[EMOJI] **Recommendations:**\n"
                for rec in recommendations[:5]:  # Show first 5
                    report += f"• {rec}\n"
            
            return report
        else:
            return f"[FAIL] Service detection failed: {result.get('error', 'Unknown error')}"

    # ===== AI MODEL MANAGEMENT =====
    
    def duckbot_list_models(self) -> str:
        """Get list of available AI models from LM Studio"""
        result = self.make_request("GET", "/models/available")
        
        if not result.get("ok"):
            return f"[FAIL] Could not get models: {result.get('error', 'LM Studio may not be running')}"
        
        models = result.get("models", [])
        lm_studio_url = result.get("lm_studio_url", "Unknown")
        
        if not models:
            return f"[EMOJI] **No models available**\n\nLM Studio URL: {lm_studio_url}\nMake sure LM Studio is running with at least one model loaded."
        
        response = f"[AI] **Available AI Models ({len(models)} found)**\n\n"
        response += f"**LM Studio URL:** {lm_studio_url}\n\n"
        
        for i, model in enumerate(models[:15], 1):  # Show first 15 models
            model_id = model.get("id", "Unknown")
            size = model.get("size", "Unknown size")
            response += f"{i}. **{model_id}** ({size})\n"
        
        if len(models) > 15:
            response += f"\n... and {len(models) - 15} more models available"
        
        return response

    def duckbot_set_model(self, model_id: str) -> str:
        """
        Set preferred AI model for DuckBot
        
        Args:
            model_id: Model ID from the available models list
        """
        data = {"model_id": model_id}
        result = self.make_request("POST", "/models/set", data=data)
        
        if result.get("ok"):
            return f"[OK] Successfully set model to: {result.get('model_set', model_id)}"
        else:
            return f"[FAIL] Failed to set model: {result.get('error', 'Unknown error')}"

    def duckbot_refresh_models(self) -> str:
        """Refresh AI model detection from LM Studio"""
        result = self.make_request("POST", "/models/refresh")
        
        if result.get("ok") or result.get("success"):
            current_model = result.get("current_model", result.get("message", "Models refreshed"))
            return f"[EMOJI] Model cache refreshed. Current model: {current_model}"
        else:
            return f"[FAIL] Failed to refresh models: {result.get('error', 'Unknown error')}"

    # ===== COST TRACKING & ANALYTICS =====
    
    def duckbot_cost_summary(self, days: int = 7) -> str:
        """
        Get detailed cost and usage analytics
        
        Args:
            days: Number of days to analyze (1-365)
        """
        result = self.make_request("GET", "/api/cost_summary", params={"days": days})
        
        if not result.get("success"):
            return f"[FAIL] Could not retrieve cost data: {result.get('error', 'Analytics unavailable')}"
        
        data = result.get("data", {})
        
        summary = f"[EMOJI] **Cost Summary ({days} days)**\n\n"
        summary += f"[EMOJI] **Total Cost:** ${data.get('total_cost', 0):.4f}\n"
        summary += f"[EMOJI] **Total Tokens:** {data.get('total_tokens', 0):,}\n"
        summary += f"[CHART] **Total Requests:** {data.get('total_requests', 0):,}\n\n"
        
        # By model breakdown
        by_model = data.get("by_model", {})
        if by_model:
            summary += "[AI] **Usage by Model:**\n"
            for model, cost in sorted(by_model.items(), key=lambda x: x[1], reverse=True):
                summary += f"• {model}: ${cost:.4f}\n"
            summary += "\n"
        
        # By provider breakdown
        by_provider = data.get("by_provider", {})
        if by_provider:
            summary += "[EMOJI] **Usage by Provider:**\n"
            for provider, cost in sorted(by_provider.items(), key=lambda x: x[1], reverse=True):
                summary += f"• {provider}: ${cost:.4f}\n"
            summary += "\n"
        
        # Predictions
        predictions = data.get("predictions", {})
        if predictions:
            summary += "[EMOJI] **Predictions:**\n"
            monthly = predictions.get("monthly_cost", 0)
            daily = predictions.get("daily_average", 0)
            summary += f"• Daily Average: ${daily:.4f}\n"
            summary += f"• Monthly Projection: ${monthly:.2f}\n"
        
        return summary

    # ===== RAG (KNOWLEDGE BASE) MANAGEMENT =====
    
    def duckbot_rag_status(self) -> str:
        """Get RAG knowledge base status"""
        result = self.make_request("GET", "/rag/status")
        
        if result.get("ok"):
            stats = result.get("stats", {})
            
            report = "[DOCS] **RAG Knowledge Base Status:**\n\n"
            
            if isinstance(stats, dict):
                for key, value in stats.items():
                    report += f"• {key.replace('_', ' ').title()}: {value}\n"
            else:
                report += f"• Status: {stats}\n"
            
            return report
        else:
            return f"[FAIL] Could not get RAG status: {result.get('error', 'RAG system unavailable')}"

    def duckbot_rag_search(self, query: str, top_k: int = 5) -> str:
        """
        Search the RAG knowledge base
        
        Args:
            query: Search query
            top_k: Number of results to return (1-20)
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
            return f"[EMOJI] **No results found** for: '{query}'"
        
        response = f"[EMOJI] **RAG Search Results:** '{query}'\n\n"
        response += f"**[DOC] Context:**\n{context[:800]}{'...' if len(context) > 800 else ''}\n\n"
        
        if chunks:
            response += f"**[DIR] Sources ({len(chunks)} chunks):**\n"
            for i, chunk in enumerate(chunks[:5], 1):  # Show first 5 sources
                source = chunk.get("metadata", {}).get("source", "Unknown source")
                response += f"{i}. {source}\n"
        
        return response

    def duckbot_rag_ingest(self, paths: str = "") -> str:
        """
        Ingest documents into RAG knowledge base
        
        Args:
            paths: Semicolon-separated paths to ingest (empty for auto-ingest)
        """
        data = {}
        if paths.strip():
            data["path"] = paths
        
        result = self.make_request("POST", "/rag/ingest", data=data)
        
        if result.get("ok"):
            ingest_result = result.get("result", "Ingestion completed")
            return f"[DOCS] **RAG Ingestion Result:**\n\n{ingest_result}"
        else:
            return f"[FAIL] RAG ingestion failed: {result.get('error', 'Unknown error')}"

    def duckbot_rag_clear(self) -> str:
        """Clear the RAG knowledge base"""
        result = self.make_request("POST", "/rag/clear")
        
        if result.get("ok"):
            return "[OK] RAG knowledge base cleared successfully"
        else:
            return f"[FAIL] Failed to clear RAG: {result.get('error', 'Unknown error')}"

    # ===== CACHE & PERFORMANCE MANAGEMENT =====
    
    def duckbot_cache_clear(self) -> str:
        """Clear AI response cache"""
        result = self.make_request("POST", "/cache/clear")
        
        if result.get("ok"):
            return "[OK] AI cache cleared successfully"
        else:
            return "[FAIL] Failed to clear cache"

    def duckbot_reset_breakers(self) -> str:
        """Reset AI circuit breakers"""
        result = self.make_request("POST", "/breakers/reset")
        
        if result.get("ok"):
            return "[OK] Circuit breakers reset successfully"
        else:
            return "[FAIL] Failed to reset breakers"

    # ===== QWEN CODE ANALYSIS =====
    
    def duckbot_qwen_status(self) -> str:
        """Get Qwen code analysis system status"""
        result = self.make_request("GET", "/qwen/status")
        
        if result.get("ok"):
            available = result.get("qwen_available", False)
            enabled = result.get("integration_enabled", False)
            temp_dir = result.get("temp_dir", "Unknown")
            
            status_emoji = "[OK]" if available else "[FAIL]"
            
            return f"[EMOJI] **Qwen Code Analysis Status:**\n\n{status_emoji} Available: {available}\n[OK] Integration: {enabled}\n[DIR] Temp Dir: {temp_dir}"
        else:
            return f"[FAIL] Qwen status error: {result.get('error', 'Unknown error')}"

    def duckbot_qwen_analyze(self, code_prompt: str) -> str:
        """
        Analyze code using Qwen enhanced system
        
        Args:
            code_prompt: Code or code-related prompt to analyze
        """
        if not code_prompt.strip():
            return "[FAIL] Please provide code or a code-related prompt to analyze"
        
        data = {"code_prompt": code_prompt}
        result = self.make_request("POST", "/qwen/analyze", data=data)
        
        if result.get("ok"):
            analysis = result.get("analysis", "No analysis available")
            enhanced = result.get("qwen_enhanced", False)
            
            enhancement_info = " (Qwen Enhanced)" if enhanced else ""
            return f"[EMOJI] **Code Analysis{enhancement_info}:**\n\n{analysis}"
        else:
            return f"[FAIL] Code analysis failed: {result.get('error', 'Qwen system unavailable')}"

    # ===== ACTION LOGS & MONITORING =====
    
    def duckbot_action_logs(self, hours: int = 24, action_type: str = "", component: str = "", limit: int = 50) -> str:
        """
        Get DuckBot action and reasoning logs
        
        Args:
            hours: Hours of logs to retrieve (1-168)
            action_type: Filter by action type
            component: Filter by component
            limit: Maximum logs to return (1-100)
        """
        params = {
            "hours": min(hours, 168),
            "limit": min(limit, 100)
        }
        if action_type:
            params["action_type"] = action_type
        if component:
            params["component"] = component
        
        result = self.make_request("GET", "/api/action-logs", params=params)
        
        if not result.get("ok"):
            return f"[FAIL] Could not get action logs: {result.get('error', 'Logging system unavailable')}"
        
        logs = result.get("logs", [])
        count = result.get("count", 0)
        
        if not logs:
            return f"[LIST] **No action logs found** (last {hours} hours)"
        
        report = f"[LIST] **Action Logs** (last {hours} hours, {count} entries):\n\n"
        
        for i, log in enumerate(logs[:10], 1):  # Show first 10 logs
            timestamp = log.get("timestamp", "Unknown time")
            action = log.get("action_type", "Unknown action")
            comp = log.get("component", "Unknown component")
            details = log.get("details", {})
            
            report += f"{i}. **{timestamp}** - {action} ({comp})\n"
            if isinstance(details, dict) and details:
                for key, value in list(details.items())[:2]:  # Show first 2 details
                    report += f"   • {key}: {str(value)[:100]}\n"
            report += "\n"
        
        if len(logs) > 10:
            report += f"... and {len(logs) - 10} more entries"
        
        return report

    def duckbot_action_summary(self, hours: int = 24) -> str:
        """
        Get action logs summary statistics
        
        Args:
            hours: Hours to summarize (1-168)
        """
        params = {"hours": min(hours, 168)}
        result = self.make_request("GET", "/api/action-logs/summary", params=params)
        
        if not result.get("ok"):
            return f"[FAIL] Could not get action summary: {result.get('error', 'Logging unavailable')}"
        
        summary_data = result.get("summary", {})
        
        if not summary_data:
            return f"[CHART] **No action summary data** (last {hours} hours)"
        
        report = f"[CHART] **Action Summary** (last {hours} hours):\n\n"
        
        for category, value in summary_data.items():
            if isinstance(value, dict):
                report += f"**{category.replace('_', ' ').title()}:**\n"
                for sub_key, sub_value in value.items():
                    report += f"  • {sub_key}: {sub_value}\n"
                report += "\n"
            else:
                report += f"• {category.replace('_', ' ').title()}: {value}\n"
        
        return report

    # ===== MAIN COMMAND INTERFACE =====
    
    def duckbot_command(
        self,
        command: str,
        message: str = "",
        service_name: str = "",
        action: str = "",
        task_type: str = "auto",
        priority: str = "medium",
        days: int = 7,
        query: str = "",
        top_k: int = 5,
        model_id: str = "",
        hours: int = 24,
        paths: str = "",
        code_prompt: str = ""
    ) -> str:
        """
        Universal DuckBot command interface - Execute any DuckBot operation
        
        AVAILABLE COMMANDS:
        
        [AI] AI & CHAT:
        - ai_chat: Chat with DuckBot AI
        - task_runner: Execute specific AI tasks
        - queue_task: Queue background tasks
        
        [TARGET] SYSTEM MANAGEMENT:
        - system_status: Full system status
        - manage_service: Control services (start/stop/restart)
        - ecosystem_start: Start entire ecosystem
        - ecosystem_stop: Stop entire ecosystem
        - detect_services: Detect available services
        
        [EMOJI] AI MODELS:
        - list_models: Show available AI models
        - set_model: Set preferred AI model
        - refresh_models: Refresh model detection
        
        [EMOJI] ANALYTICS:
        - cost_summary: Usage and cost analytics
        - action_logs: View system logs
        - action_summary: Log statistics
        
        [DOCS] KNOWLEDGE BASE (RAG):
        - rag_search: Search knowledge base
        - rag_status: RAG system status
        - rag_ingest: Add documents to knowledge base
        - rag_clear: Clear knowledge base
        
        [TOOLS] SYSTEM MAINTENANCE:
        - cache_clear: Clear AI cache
        - reset_breakers: Reset circuit breakers
        - qwen_status: Code analysis status
        - qwen_analyze: Analyze code with Qwen
        
        Args:
            command: Command to execute (see list above)
            message: Message for AI chat/tasks
            service_name: Service name (comfyui, n8n, jupyter, lm_studio, webui)
            action: Action for services (start, stop, restart)
            task_type: AI task type (auto, code, reasoning, summary, long_form, json_format)
            priority: Priority (low, medium, high)
            days: Days for analytics (1-365)
            query: Search query for RAG
            top_k: Number of results (1-20)
            model_id: AI model identifier
            hours: Hours for logs (1-168)
            paths: Paths for RAG ingestion
            code_prompt: Code for analysis
        """
        
        # Normalize command
        cmd = command.lower().strip()
        
        try:
            # AI & Chat commands
            if cmd in ["ai_chat", "chat", "ask"]:
                return self.duckbot_ai_chat(message, task_type, priority)
            
            elif cmd in ["task_runner", "task", "run_task"]:
                return self.duckbot_task_runner(task_type, message or code_prompt, priority)
            
            elif cmd in ["queue_task", "queue"]:
                return self.duckbot_queue_task(task_type, message or code_prompt, priority)
            
            # System Management
            elif cmd in ["system_status", "status"]:
                return self.duckbot_system_status()
            
            elif cmd in ["manage_service", "service"]:
                return self.duckbot_manage_service(service_name, action)
            
            elif cmd in ["ecosystem_start", "start_ecosystem"]:
                return self.duckbot_ecosystem_control("start")
            
            elif cmd in ["ecosystem_stop", "stop_ecosystem"]:
                return self.duckbot_ecosystem_control("stop")
            
            elif cmd in ["detect_services", "detect"]:
                return self.duckbot_detect_services()
            
            # AI Model Management
            elif cmd in ["list_models", "models"]:
                return self.duckbot_list_models()
            
            elif cmd in ["set_model", "switch_model"]:
                return self.duckbot_set_model(model_id)
            
            elif cmd in ["refresh_models", "refresh"]:
                return self.duckbot_refresh_models()
            
            # Analytics & Costs
            elif cmd in ["cost_summary", "cost", "usage"]:
                return self.duckbot_cost_summary(days)
            
            elif cmd in ["action_logs", "logs"]:
                return self.duckbot_action_logs(hours, task_type, service_name, min(top_k * 10, 100))
            
            elif cmd in ["action_summary", "log_summary"]:
                return self.duckbot_action_summary(hours)
            
            # RAG Knowledge Base
            elif cmd in ["rag_search", "search_kb", "search"]:
                return self.duckbot_rag_search(query or message, top_k)
            
            elif cmd in ["rag_status", "kb_status"]:
                return self.duckbot_rag_status()
            
            elif cmd in ["rag_ingest", "ingest", "add_docs"]:
                return self.duckbot_rag_ingest(paths)
            
            elif cmd in ["rag_clear", "clear_kb"]:
                return self.duckbot_rag_clear()
            
            # System Maintenance
            elif cmd in ["cache_clear", "clear_cache"]:
                return self.duckbot_cache_clear()
            
            elif cmd in ["reset_breakers", "reset"]:
                return self.duckbot_reset_breakers()
            
            elif cmd in ["qwen_status", "code_status"]:
                return self.duckbot_qwen_status()
            
            elif cmd in ["qwen_analyze", "analyze_code", "code_analyze"]:
                return self.duckbot_qwen_analyze(code_prompt or message)
            
            # Help/Unknown command
            else:
                available = [
                    "ai_chat", "task_runner", "queue_task", "system_status", "manage_service", 
                    "ecosystem_start", "ecosystem_stop", "detect_services", "list_models", 
                    "set_model", "refresh_models", "cost_summary", "action_logs", "action_summary",
                    "rag_search", "rag_status", "rag_ingest", "rag_clear", "cache_clear", 
                    "reset_breakers", "qwen_status", "qwen_analyze"
                ]
                
                return f"[FAIL] **Unknown command:** '{command}'\n\n[TOOLS] **Available commands:**\n" + "\n".join([f"• {cmd}" for cmd in available[:15]]) + f"\n\n... and {len(available) - 15} more commands"
        
        except Exception as e:
            return f"[FAIL] **Tool error:** {str(e)}\n\nTry checking if DuckBot server is running at http://localhost:8787"