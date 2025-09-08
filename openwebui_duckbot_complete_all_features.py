"""
title: DuckBot Complete All-Features Tool
author: open-webui
author_url: https://github.com/open-webui
funding_url: https://github.com/sponsors/tjbck
version: 3.0.0
license: MIT
description: COMPLETE DuckBot integration with ALL features - ecosystem management, AI routing, services, cost tracking, RAG, VibeVoice TTS, Discord commands, and advanced system control
requirements: requests
"""

import requests
import json
import subprocess
import os
from typing import Optional, Dict, Any


class Tools:
    def __init__(self):
        self.duckbot_url = "http://localhost:8787"
        self.token = None
        self.timeout = 60

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

    def make_request(self, method: str, endpoint: str, data=None, params=None, files=None):
        """Make authenticated request to DuckBot"""
        token = self.get_duckbot_token()
        if not token:
            return {"error": "DuckBot server not available at http://localhost:8787"}
        
        url = f"{self.duckbot_url}{endpoint}"
        headers = {"Authorization": f"Bearer {token}"}
        
        try:
            if method == "GET":
                response = requests.get(url, headers=headers, params=params, timeout=self.timeout)
            else:
                response = requests.post(url, headers=headers, data=data, files=files, timeout=self.timeout)
            
            if response.status_code == 200:
                try:
                    return response.json()
                except:
                    return {"success": True, "response": response.text}
            else:
                return {"error": f"HTTP {response.status_code}: {response.text}"}
                
        except Exception as e:
            return {"error": str(e)}

    def run_batch_command(self, command: str) -> str:
        """Execute Windows batch commands for DuckBot ecosystem control"""
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=120)
            if result.returncode == 0:
                return f"✅ Command executed successfully:\n{result.stdout}"
            else:
                return f"❌ Command failed (exit code {result.returncode}):\n{result.stderr}"
        except subprocess.TimeoutExpired:
            return "❌ Command timed out after 2 minutes"
        except Exception as e:
            return f"❌ Error executing command: {str(e)}"

    # ===== ECOSYSTEM STARTUP AND CONTROL =====

    def duckbot_start_ecosystem(self, mode: str = "unified") -> str:
        """
        Start DuckBot ecosystem with different modes.
        
        :param mode: unified, webui_only, ai_headless, local_only, headless_local, vibevoice, openwebui, quick
        :return: Startup result
        """
        mode_commands = {
            "unified": "START_ENHANCED_DUCKBOT.bat",
            "webui_only": "python -m duckbot.webui",
            "ai_headless": "python start_ai_ecosystem.py",
            "local_only": "START_LOCAL_ONLY.bat",
            "headless_local": "START_HEADLESS_LOCAL.bat", 
            "vibevoice": "start /MIN python start_ai_ecosystem.py",
            "openwebui": "START_OPEN_WEBUI.bat",
            "quick": "python start_ai_ecosystem.py && python -m duckbot.webui"
        }
        
        if mode not in mode_commands:
            available = ", ".join(mode_commands.keys())
            return f"❌ Invalid mode. Available modes: {available}"
        
        command = mode_commands[mode]
        return f"🚀 Starting DuckBot {mode} mode...\n\n{self.run_batch_command(command)}"

    def duckbot_emergency_kill(self) -> str:
        """
        Emergency kill all DuckBot processes.
        
        :return: Kill operation result
        """
        return "🛑 Emergency killing all DuckBot processes...\n\n" + self.run_batch_command("EMERGENCY_KILL.bat")

    def duckbot_quick_kill(self) -> str:
        """
        Quick kill DuckBot processes with options.
        
        :return: Kill operation result  
        """
        return "⚡ Quick kill DuckBot processes...\n\n" + self.run_batch_command("QUICK_KILL.bat")

    # ===== AI CHAT AND TASKS =====

    def duckbot_ai_chat(self, message: str, task_type: str = "auto", priority: str = "medium") -> str:
        """
        Chat with DuckBot AI system.
        
        :param message: Your message or question for DuckBot AI
        :param task_type: auto, code, reasoning, summary, long_form, json_format, policy, arbiter
        :param priority: low, medium, high
        :return: AI response from DuckBot
        """
        if not message.strip():
            return "❌ Please provide a message for DuckBot AI"
        
        data = {"message": message, "kind": task_type, "risk": priority}
        result = self.make_request("POST", "/chat", data=data)
        
        if "error" in result:
            return f"❌ Error: {result['error']}"
        
        if result.get("success"):
            response = result.get("response", "No response")
            model = result.get("model", "unknown")
            confidence = result.get("confidence", 0)
            cached = " (cached)" if result.get("cached") else ""
            
            return f"🤖 **DuckBot AI Response:**\n\n{response}\n\n📊 Model: {model} | Confidence: {confidence:.2f}{cached}"
        
        return f"❌ Failed: {result}"

    def duckbot_task_runner(self, task_type: str, prompt: str, priority: str = "medium") -> str:
        """
        Execute specific AI tasks via Task Runner interface.
        
        :param task_type: code, reasoning, summary, long_form, json_format, policy, arbiter
        :param prompt: Task prompt
        :param priority: low, medium, high
        :return: Task execution result
        """
        data = {"task_type": task_type, "prompt": prompt, "priority": priority}
        result = self.make_request("POST", "/api/task", data=data)
        
        if result.get("success"):
            return f"⚡ **Task Runner Result:**\n\n{result.get('result', {}).get('text', 'No result')}"
        else:
            return f"❌ Task failed: {result.get('error', 'Unknown error')}"

    def duckbot_queue_task(self, task_type: str, prompt: str, priority: str = "low") -> str:
        """
        Queue task for background processing.
        
        :param task_type: Type of task
        :param prompt: Task prompt
        :param priority: Task priority
        :return: Queue result
        """
        data = {"kind": task_type, "risk": priority, "prompt": prompt}
        result = self.make_request("POST", "/queue", data=data)
        
        if "queued" in result:
            return f"✅ Task queued successfully. Queue position: {result['queued']}"
        else:
            return f"❌ Failed to queue: {result.get('error', 'Unknown error')}"

    # ===== SYSTEM STATUS AND MONITORING =====

    def duckbot_system_status(self) -> str:
        """Get comprehensive system status"""
        ai_status = self.make_request("GET", "/api/system-status")
        services_status = self.make_request("GET", "/api/services")
        servers_status = self.make_request("GET", "/servers/status")
        
        report = "🚀 **DuckBot System Status**\n\n"
        
        # AI Router Status
        if ai_status.get("ok"):
            ai = ai_status.get("status", {})
            report += "🧠 **AI System:**\n"
            report += f"• Model: {ai.get('current_lm_model', 'Unknown')}\n"
            report += f"• Cache: {ai.get('cache_size', 0)} items\n"
            report += f"• Chat Tokens: {ai.get('chat_bucket_tokens', 0)}/{ai.get('chat_bucket_limit', 30)}\n"
            report += f"• Background Tokens: {ai.get('background_bucket_tokens', 0)}/{ai.get('background_bucket_limit', 30)}\n\n"
        
        # Services Status
        if services_status.get("ok"):
            services = services_status.get("services", [])
            report += "⚙️ **Services:**\n"
            for svc in services:
                name = svc.get("name", "Unknown")
                status = svc.get("status", "unknown")
                port = svc.get("port", "N/A")
                emoji = "✅" if status == "running" else "❌"
                report += f"{emoji} {name} (:{port}) - {status.title()}\n"
            report += "\n"
        
        # Ecosystem Servers
        if servers_status.get("ok"):
            servers = servers_status.get("services", {})
            if servers:
                report += "🖥️ **Ecosystem Services:**\n"
                for name, info in servers.items():
                    status = info.get("status", "unknown")
                    port = info.get("port", "N/A")
                    emoji = "✅" if status == "running" else "❌"
                    report += f"{emoji} {name} (:{port}) - {status.title()}\n"
        
        return report

    def duckbot_quick_system_check(self) -> str:
        """
        Quick system health check via batch script.
        
        :return: System health report
        """
        return "🔍 **Quick System Health Check:**\n\n" + self.run_batch_command("python -c \"import psutil, requests; print(f'CPU: {psutil.cpu_percent()}%'); print(f'RAM: {psutil.virtual_memory().percent}%'); [print(f'{name}: OK') if requests.get(url, timeout=2).status_code == 200 else print(f'{name}: DOWN') for name, url in [('WebUI', 'http://localhost:8787'), ('LM Studio', 'http://localhost:1234/v1/models')] if True]\"")

    def duckbot_comprehensive_test(self) -> str:
        """
        Run comprehensive system testing.
        
        :return: Test results
        """
        return "🧪 **Running comprehensive system tests:**\n\n" + self.run_batch_command("python test_every_feature.py")

    def duckbot_test_enhanced_system(self) -> str:
        """
        Run enhanced system tests.
        
        :return: Enhanced test results
        """
        return "🧪 **Running enhanced system tests:**\n\n" + self.run_batch_command("test_enhanced_system.bat")

    # ===== SERVICE MANAGEMENT =====

    def duckbot_manage_service(self, service_name: str, action: str) -> str:
        """
        Manage DuckBot services.
        
        :param service_name: comfyui, n8n, jupyter, lm_studio, webui, open_notebook, discord_bot
        :param action: start, stop, restart
        :return: Service management result
        """
        if action not in ["start", "stop", "restart"]:
            return "❌ Invalid action. Use: start, stop, restart"
        
        # Try WebUI API first
        result = self.make_request("POST", f"/api/services/{service_name}/{action}")
        
        if not result.get("success"):
            # Try servers API
            data = {"service_name": service_name}
            result = self.make_request("POST", f"/servers/{action}", data=data)
        
        if result.get("success") or result.get("ok"):
            message = result.get("result", result.get("message", f"Service {action} completed"))
            return f"✅ {service_name}: {message}"
        else:
            error = result.get("error", "Unknown error")
            return f"❌ Failed to {action} {service_name}: {error}"

    def duckbot_detect_services(self) -> str:
        """Detect all available services and get recommendations"""
        result = self.make_request("GET", "/services/detect")
        
        if result.get("ok"):
            services = result.get("services", {})
            recommendations = result.get("recommendations", [])
            
            report = "🔍 **Service Detection Results:**\n\n"
            
            for service_name, service_info in services.items():
                status = service_info.get("status", "unknown")
                port = service_info.get("port", "N/A")
                emoji = "✅" if status in ["running_healthy", "running_unhealthy"] else "❌"
                report += f"{emoji} {service_name} (:{port}) - {status.replace('_', ' ').title()}\n"
            
            if recommendations:
                report += "\n💡 **Recommendations:**\n"
                for rec in recommendations:
                    report += f"• {rec}\n"
            
            return report
        else:
            return f"❌ Service detection failed: {result.get('error', 'Unknown error')}"

    def duckbot_install_missing_services(self) -> str:
        """
        Install missing services and dependencies.
        
        :return: Installation result
        """
        return "📦 **Installing missing services:**\n\n" + self.run_batch_command("install_missing_services.bat")

    # ===== AI MODEL MANAGEMENT =====

    def duckbot_list_models(self) -> str:
        """Get available AI models from LM Studio"""
        result = self.make_request("GET", "/models/available")
        
        if not result.get("ok"):
            return f"❌ Models unavailable: {result.get('error', 'LM Studio offline')}"
        
        models = result.get("models", [])
        if not models:
            return "📭 No models loaded in LM Studio"
        
        response = f"🤖 **Available Models ({len(models)})**\n\n"
        
        for i, model in enumerate(models[:15], 1):
            model_id = model.get("id", "Unknown")
            size = model.get("size", "Unknown")
            response += f"{i}. {model_id} ({size})\n"
        
        if len(models) > 15:
            response += f"\n... and {len(models) - 15} more"
        
        return response

    def duckbot_set_model(self, model_id: str) -> str:
        """
        Set preferred AI model.
        
        :param model_id: Model identifier
        :return: Model setting result
        """
        data = {"model_id": model_id}
        result = self.make_request("POST", "/models/set", data=data)
        
        if result.get("ok"):
            return f"✅ Model set to: {result.get('model_set', model_id)}"
        else:
            return f"❌ Failed to set model: {result.get('error', 'Unknown error')}"

    def duckbot_refresh_models(self) -> str:
        """Refresh AI model detection"""
        result = self.make_request("POST", "/models/refresh")
        
        if result.get("ok") or result.get("success"):
            return f"🔄 Model cache refreshed: {result.get('message', 'Complete')}"
        else:
            return f"❌ Failed to refresh: {result.get('error', 'Unknown error')}"

    def duckbot_check_model_status(self) -> str:
        """
        Check dynamic model status and usage.
        
        :return: Model status report
        """
        return "📊 **Checking model status:**\n\n" + self.run_batch_command("CHECK_MODEL_STATUS.bat")

    # ===== COST TRACKING AND ANALYTICS =====

    def duckbot_cost_summary(self, days: int = 7) -> str:
        """
        Get detailed cost and usage analytics.
        
        :param days: Number of days to analyze
        :return: Cost summary
        """
        result = self.make_request("GET", "/api/cost_summary", params={"days": days})
        
        if not result.get("success"):
            return f"❌ Cost data unavailable: {result.get('error', 'Analytics offline')}"
        
        data = result.get("data", {})
        
        summary = f"💰 **Cost Summary ({days} days)**\n\n"
        summary += f"💵 Total Cost: ${data.get('total_cost', 0):.4f}\n"
        summary += f"🔢 Total Tokens: {data.get('total_tokens', 0):,}\n"
        summary += f"📊 Total Requests: {data.get('total_requests', 0):,}\n\n"
        
        # Model breakdown
        by_model = data.get("by_model", {})
        if by_model:
            summary += "🤖 **By Model:**\n"
            for model, cost in sorted(by_model.items(), key=lambda x: x[1], reverse=True)[:5]:
                summary += f"• {model}: ${cost:.4f}\n"
            summary += "\n"
        
        # Predictions
        predictions = data.get("predictions", {})
        if predictions:
            summary += "📈 **Projections:**\n"
            summary += f"• Daily Avg: ${predictions.get('daily_average', 0):.4f}\n"
            summary += f"• Monthly: ${predictions.get('monthly_cost', 0):.2f}\n"
        
        return summary

    def duckbot_start_cost_dashboard(self) -> str:
        """
        Start the professional cost tracking dashboard.
        
        :return: Dashboard startup result
        """
        return "📊 **Starting cost dashboard:**\n\n" + self.run_batch_command("python start_cost_dashboard.py")

    # ===== RAG KNOWLEDGE BASE =====

    def duckbot_rag_search(self, query: str, top_k: int = 5) -> str:
        """
        Search RAG knowledge base.
        
        :param query: Search query
        :param top_k: Number of results
        :return: Search results
        """
        if not query.strip():
            return "❌ Please provide a search query"
        
        data = {"q": query, "top_k": min(top_k, 20)}
        result = self.make_request("POST", "/rag/search", data=data)
        
        if not result.get("ok"):
            return f"❌ RAG search failed: {result.get('error', 'Knowledge base unavailable')}"
        
        context = result.get("context", "")
        chunks = result.get("chunks", [])
        
        if not context:
            return f"🔍 No results found for: '{query}'"
        
        response = f"🔍 **Search Results:** '{query}'\n\n"
        response += f"**Context:**\n{context[:600]}{'...' if len(context) > 600 else ''}\n\n"
        
        if chunks:
            response += f"**Sources ({len(chunks)} found):**\n"
            for i, chunk in enumerate(chunks[:3], 1):
                source = chunk.get("metadata", {}).get("source", "Unknown")
                response += f"{i}. {source}\n"
        
        return response

    def duckbot_rag_status(self) -> str:
        """Get RAG system status"""
        result = self.make_request("GET", "/rag/status")
        
        if result.get("ok"):
            stats = result.get("stats", {})
            report = "📚 **RAG Knowledge Base Status:**\n\n"
            
            if isinstance(stats, dict):
                for key, value in stats.items():
                    report += f"• {key.replace('_', ' ').title()}: {value}\n"
            else:
                report += f"• Status: {stats}\n"
            
            return report
        else:
            return f"❌ RAG status error: {result.get('error', 'RAG unavailable')}"

    def duckbot_rag_ingest(self, paths: str = "") -> str:
        """
        Ingest documents into RAG knowledge base.
        
        :param paths: Semicolon-separated paths (empty for auto-ingest)
        :return: Ingestion result
        """
        data = {"path": paths} if paths.strip() else {}
        result = self.make_request("POST", "/rag/ingest", data=data)
        
        if result.get("ok"):
            return f"📚 **RAG Ingestion:**\n\n{result.get('result', 'Completed')}"
        else:
            return f"❌ RAG ingestion failed: {result.get('error', 'Unknown error')}"

    def duckbot_rag_clear(self) -> str:
        """Clear RAG knowledge base"""
        result = self.make_request("POST", "/rag/clear")
        
        if result.get("ok"):
            return "✅ RAG knowledge base cleared"
        else:
            return f"❌ Failed to clear RAG: {result.get('error', 'Unknown error')}"

    # ===== VIBEVOICE TTS INTEGRATION =====

    def duckbot_vibevoice_setup(self) -> str:
        """
        Setup VibeVoice TTS system.
        
        :return: Setup result
        """
        return "🎤 **Setting up VibeVoice TTS:**\n\n" + self.run_batch_command("python setup_vibevoice.py")

    def duckbot_vibevoice_start_server(self) -> str:
        """
        Start VibeVoice TTS server.
        
        :return: Server startup result
        """
        return "🎤 **Starting VibeVoice server:**\n\n" + self.run_batch_command("cd VibeVoice-FastAPI && python main.py --host 0.0.0.0 --port 8000")

    def duckbot_vibevoice_test(self) -> str:
        """
        Test VibeVoice integration.
        
        :return: Test results
        """
        return "🧪 **Testing VibeVoice:**\n\n" + self.run_batch_command("python test_vibevoice.py")

    def duckbot_vibevoice_status(self) -> str:
        """Check VibeVoice system status"""
        try:
            response = requests.get("http://localhost:8000/voices", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return f"✅ **VibeVoice Server Status:**\n\n• Server: Running\n• Available Voices: {len(data.get('voices', []))}\n• URL: http://localhost:8000"
            else:
                return f"⚠️ VibeVoice server responded with status {response.status_code}"
        except Exception as e:
            return f"❌ **VibeVoice Server:** Not accessible\n• Error: {str(e)}\n• Solution: Start server with duckbot_vibevoice_start_server()"

    # ===== QWEN CODE ANALYSIS =====

    def duckbot_qwen_status(self) -> str:
        """Get Qwen code analysis status"""
        result = self.make_request("GET", "/qwen/status")
        
        if result.get("ok"):
            available = result.get("qwen_available", False)
            enabled = result.get("integration_enabled", False)
            
            return f"🧠 **Qwen Code Analysis:**\n\n• Available: {'✅' if available else '❌'}\n• Integration: {'✅' if enabled else '❌'}\n• Temp Dir: {result.get('temp_dir', 'Unknown')}"
        else:
            return f"❌ Qwen status error: {result.get('error', 'Qwen unavailable')}"

    def duckbot_qwen_analyze(self, code: str) -> str:
        """
        Analyze code with Qwen enhanced system.
        
        :param code: Code to analyze
        :return: Analysis results
        """
        if not code.strip():
            return "❌ Please provide code to analyze"
        
        data = {"code_prompt": code}
        result = self.make_request("POST", "/qwen/analyze", data=data)
        
        if result.get("ok"):
            analysis = result.get("analysis", "No analysis available")
            enhanced = " (Qwen Enhanced)" if result.get("qwen_enhanced") else ""
            return f"🧠 **Code Analysis{enhanced}:**\n\n{analysis}"
        else:
            return f"❌ Analysis failed: {result.get('error', 'Qwen unavailable')}"

    def duckbot_qwen_setup(self) -> str:
        """
        Setup Qwen code analysis system.
        
        :return: Setup result
        """
        return "🧠 **Setting up Qwen code analysis:**\n\n" + self.run_batch_command("QWEN_SETUP_AND_START.bat")

    # ===== ADVANCED SYSTEM OPERATIONS =====

    def duckbot_cache_clear(self) -> str:
        """Clear AI response cache"""
        result = self.make_request("POST", "/cache/clear")
        
        if result.get("ok"):
            return "✅ AI cache cleared successfully"
        else:
            return "❌ Failed to clear cache"

    def duckbot_reset_breakers(self) -> str:
        """Reset AI circuit breakers"""
        result = self.make_request("POST", "/breakers/reset")
        
        if result.get("ok"):
            return "✅ Circuit breakers reset successfully"
        else:
            return "❌ Failed to reset breakers"

    def duckbot_action_logs(self, hours: int = 24) -> str:
        """
        Get system action and reasoning logs.
        
        :param hours: Hours of logs to retrieve
        :return: Action logs
        """
        params = {"hours": min(hours, 168), "limit": 20}
        result = self.make_request("GET", "/api/action-logs", params=params)
        
        if not result.get("ok"):
            return f"❌ Logs unavailable: {result.get('error', 'Logging offline')}"
        
        logs = result.get("logs", [])
        if not logs:
            return f"📋 No logs found (last {hours} hours)"
        
        report = f"📋 **Action Logs** (last {hours} hours, {len(logs)} entries):\n\n"
        
        for i, log in enumerate(logs[:10], 1):
            timestamp = log.get("timestamp", "Unknown")
            action = log.get("action_type", "Unknown")
            component = log.get("component", "Unknown")
            
            report += f"{i}. **{timestamp}** - {action} ({component})\n"
        
        if len(logs) > 10:
            report += f"\n... and {len(logs) - 10} more entries"
        
        return report

    def duckbot_action_summary(self, hours: int = 24) -> str:
        """
        Get action logs summary statistics.
        
        :param hours: Hours to summarize
        :return: Summary statistics
        """
        params = {"hours": min(hours, 168)}
        result = self.make_request("GET", "/api/action-logs/summary", params=params)
        
        if not result.get("ok"):
            return f"❌ Summary unavailable: {result.get('error', 'Logging offline')}"
        
        summary_data = result.get("summary", {})
        if not summary_data:
            return f"📊 No summary data (last {hours} hours)"
        
        report = f"📊 **Action Summary** (last {hours} hours):\n\n"
        
        for category, value in summary_data.items():
            if isinstance(value, dict):
                report += f"**{category.replace('_', ' ').title()}:**\n"
                for sub_key, sub_value in value.items():
                    report += f"  • {sub_key}: {sub_value}\n"
                report += "\n"
            else:
                report += f"• {category.replace('_', ' ').title()}: {value}\n"
        
        return report

    # ===== DEPENDENCY AND SYSTEM MANAGEMENT =====

    def duckbot_fix_dependencies(self) -> str:
        """
        Fix Python dependencies and common issues.
        
        :return: Dependency fix results
        """
        return "🔧 **Fixing dependencies:**\n\n" + self.run_batch_command("QUICK_FIX_DEPENDENCIES.bat")

    def duckbot_doctor_mode(self, diagnostic_type: str = "quick") -> str:
        """
        Run system diagnostics and repairs.
        
        :param diagnostic_type: quick, full, deps, repair, report
        :return: Diagnostic results
        """
        diagnostic_commands = {
            "quick": "python -c \"import psutil; print('System OK' if psutil.cpu_percent() < 90 else 'High CPU')\"",
            "full": "python test_every_feature.py",
            "deps": "pip install fastapi uvicorn aiohttp requests discord.py torch",
            "repair": "python repair_system.py",
            "report": "python generate_health_report.py"
        }
        
        command = diagnostic_commands.get(diagnostic_type, diagnostic_commands["quick"])
        return f"🩺 **System Doctor ({diagnostic_type}):**\n\n{self.run_batch_command(command)}"

    def duckbot_test_local_parity(self) -> str:
        """
        Test local-cloud feature parity.
        
        :return: Parity test results
        """
        return "🧪 **Testing local-cloud parity:**\n\n" + self.run_batch_command("TEST_LOCAL_PARITY.bat")

    # ===== OPENWEBUI AND CLAUDE INTEGRATION =====

    def duckbot_start_openwebui(self) -> str:
        """
        Start Open-WebUI with DuckBot integration.
        
        :return: OpenWebUI startup result
        """
        return "🌐 **Starting Open-WebUI:**\n\n" + self.run_batch_command("START_OPEN_WEBUI.bat")

    def duckbot_start_claude_router(self) -> str:
        """
        Start OpenWebUI with Claude router integration.
        
        :return: Claude router startup result
        """
        return "🤖 **Starting Claude router:**\n\n" + self.run_batch_command("START_OPENWEBUI_CLAUDE_ROUTER.bat")

    def duckbot_start_openrouter_free(self) -> str:
        """
        Start OpenWebUI with free OpenRouter models.
        
        :return: Free OpenRouter startup result
        """
        return "💸 **Starting free OpenRouter:**\n\n" + self.run_batch_command("START_OPENWEBUI_OPENROUTER_FREE.bat")

    # ===== DISCORD BOT MANAGEMENT =====

    def duckbot_start_discord_bot(self, mode: str = "enhanced") -> str:
        """
        Start Discord bot in various modes.
        
        :param mode: enhanced, code_focused, basic
        :return: Discord bot startup result
        """
        mode_commands = {
            "enhanced": "START_ENHANCED_DUCKBOT.bat",
            "code_focused": "START_CODE_FOCUSED_BOT.bat",
            "basic": "python DuckBot-v2.3.0-Trading-Video-Enhanced.py"
        }
        
        command = mode_commands.get(mode, mode_commands["enhanced"])
        return f"🤖 **Starting Discord bot ({mode}):**\n\n{self.run_batch_command(command)}"

    # ===== UNIVERSAL COMMAND INTERFACE =====

    def duckbot_execute_command(
        self,
        command: str,
        # Parameters for different command types
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
        code: str = "",
        mode: str = "unified",
        diagnostic_type: str = "quick"
    ) -> str:
        """
        Universal DuckBot command interface - Execute ANY DuckBot operation.
        
        ECOSYSTEM CONTROL:
        - start_ecosystem: Start DuckBot ecosystem (mode: unified, webui_only, ai_headless, local_only, headless_local, vibevoice, openwebui, quick)
        - emergency_kill: Emergency kill all processes
        - quick_kill: Quick kill with options
        
        AI & CHAT:
        - ai_chat: Chat with AI (message, task_type, priority)
        - task_runner: Execute AI tasks (task_type, message, priority)
        - queue_task: Queue background tasks (task_type, message, priority)
        
        SYSTEM STATUS:
        - system_status: Complete system status
        - quick_check: Quick health check
        - comprehensive_test: Full system testing
        - test_enhanced: Enhanced system tests
        
        SERVICE MANAGEMENT:
        - manage_service: Control services (service_name, action)
        - detect_services: Detect all services
        - install_services: Install missing services
        
        AI MODELS:
        - list_models: Show available models
        - set_model: Set preferred model (model_id)
        - refresh_models: Refresh model detection
        - check_model_status: Dynamic model status
        
        COST & ANALYTICS:
        - cost_summary: Usage analytics (days)
        - start_cost_dashboard: Launch cost dashboard
        - action_logs: System logs (hours)
        - action_summary: Log statistics (hours)
        
        RAG KNOWLEDGE BASE:
        - rag_search: Search knowledge base (query, top_k)
        - rag_status: RAG system status
        - rag_ingest: Add documents (paths)
        - rag_clear: Clear knowledge base
        
        VIBEVOICE TTS:
        - vibevoice_setup: Setup TTS system
        - vibevoice_start: Start TTS server
        - vibevoice_test: Test TTS integration
        - vibevoice_status: Check TTS status
        
        QWEN CODE ANALYSIS:
        - qwen_status: Code analysis status
        - qwen_analyze: Analyze code (code)
        - qwen_setup: Setup Qwen system
        
        SYSTEM OPERATIONS:
        - cache_clear: Clear AI cache
        - reset_breakers: Reset circuit breakers
        - fix_dependencies: Fix Python deps
        - doctor_mode: System diagnostics (diagnostic_type)
        - test_local_parity: Test local-cloud parity
        
        INTEGRATIONS:
        - start_openwebui: Start Open-WebUI
        - start_claude_router: Start Claude router
        - start_openrouter_free: Start free OpenRouter
        - start_discord_bot: Start Discord bot (mode)
        """
        
        cmd = command.lower().strip()
        
        try:
            # Ecosystem Control
            if cmd == "start_ecosystem":
                return self.duckbot_start_ecosystem(mode)
            elif cmd == "emergency_kill":
                return self.duckbot_emergency_kill()
            elif cmd == "quick_kill":
                return self.duckbot_quick_kill()
            
            # AI & Chat
            elif cmd == "ai_chat":
                return self.duckbot_ai_chat(message, task_type, priority)
            elif cmd == "task_runner":
                return self.duckbot_task_runner(task_type, message or code, priority)
            elif cmd == "queue_task":
                return self.duckbot_queue_task(task_type, message or code, priority)
            
            # System Status
            elif cmd == "system_status":
                return self.duckbot_system_status()
            elif cmd == "quick_check":
                return self.duckbot_quick_system_check()
            elif cmd == "comprehensive_test":
                return self.duckbot_comprehensive_test()
            elif cmd == "test_enhanced":
                return self.duckbot_test_enhanced_system()
            
            # Service Management  
            elif cmd == "manage_service":
                return self.duckbot_manage_service(service_name, action)
            elif cmd == "detect_services":
                return self.duckbot_detect_services()
            elif cmd == "install_services":
                return self.duckbot_install_missing_services()
            
            # AI Models
            elif cmd == "list_models":
                return self.duckbot_list_models()
            elif cmd == "set_model":
                return self.duckbot_set_model(model_id)
            elif cmd == "refresh_models":
                return self.duckbot_refresh_models()
            elif cmd == "check_model_status":
                return self.duckbot_check_model_status()
            
            # Cost & Analytics
            elif cmd == "cost_summary":
                return self.duckbot_cost_summary(days)
            elif cmd == "start_cost_dashboard":
                return self.duckbot_start_cost_dashboard()
            elif cmd == "action_logs":
                return self.duckbot_action_logs(hours)
            elif cmd == "action_summary":
                return self.duckbot_action_summary(hours)
            
            # RAG Knowledge Base
            elif cmd == "rag_search":
                return self.duckbot_rag_search(query or message, top_k)
            elif cmd == "rag_status":
                return self.duckbot_rag_status()
            elif cmd == "rag_ingest":
                return self.duckbot_rag_ingest(paths)
            elif cmd == "rag_clear":
                return self.duckbot_rag_clear()
            
            # VibeVoice TTS
            elif cmd == "vibevoice_setup":
                return self.duckbot_vibevoice_setup()
            elif cmd == "vibevoice_start":
                return self.duckbot_vibevoice_start_server()
            elif cmd == "vibevoice_test":
                return self.duckbot_vibevoice_test()
            elif cmd == "vibevoice_status":
                return self.duckbot_vibevoice_status()
            
            # Qwen Code Analysis
            elif cmd == "qwen_status":
                return self.duckbot_qwen_status()
            elif cmd == "qwen_analyze":
                return self.duckbot_qwen_analyze(code or message)
            elif cmd == "qwen_setup":
                return self.duckbot_qwen_setup()
            
            # System Operations
            elif cmd == "cache_clear":
                return self.duckbot_cache_clear()
            elif cmd == "reset_breakers":
                return self.duckbot_reset_breakers()
            elif cmd == "fix_dependencies":
                return self.duckbot_fix_dependencies()
            elif cmd == "doctor_mode":
                return self.duckbot_doctor_mode(diagnostic_type)
            elif cmd == "test_local_parity":
                return self.duckbot_test_local_parity()
            
            # Integrations
            elif cmd == "start_openwebui":
                return self.duckbot_start_openwebui()
            elif cmd == "start_claude_router":
                return self.duckbot_start_claude_router()
            elif cmd == "start_openrouter_free":
                return self.duckbot_start_openrouter_free()
            elif cmd == "start_discord_bot":
                return self.duckbot_start_discord_bot(mode)
            
            else:
                available_commands = [
                    "start_ecosystem", "emergency_kill", "quick_kill", "ai_chat", "task_runner", 
                    "queue_task", "system_status", "quick_check", "comprehensive_test", "test_enhanced",
                    "manage_service", "detect_services", "install_services", "list_models", "set_model",
                    "refresh_models", "check_model_status", "cost_summary", "start_cost_dashboard",
                    "action_logs", "action_summary", "rag_search", "rag_status", "rag_ingest", 
                    "rag_clear", "vibevoice_setup", "vibevoice_start", "vibevoice_test", "vibevoice_status",
                    "qwen_status", "qwen_analyze", "qwen_setup", "cache_clear", "reset_breakers",
                    "fix_dependencies", "doctor_mode", "test_local_parity", "start_openwebui",
                    "start_claude_router", "start_openrouter_free", "start_discord_bot"
                ]
                
                return f"❌ **Unknown command:** '{command}'\n\n🔧 **Available commands:**\n" + "\n".join([f"• {cmd}" for cmd in available_commands[:20]]) + f"\n\n... and {len(available_commands) - 20} more commands"
        
        except Exception as e:
            return f"❌ **Command execution error:** {str(e)}\n\nEnsure DuckBot server is running at http://localhost:8787"