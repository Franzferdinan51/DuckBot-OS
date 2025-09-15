"""
title: DuckBot Complete Control
author: DuckBot Integration Team
version: 3.0.0
license: MIT
description: Complete DuckBot ecosystem control - AI, services, cost tracking, RAG, VibeVoice TTS, Qwen analysis, and system management
requirements: requests
"""

import requests
import json
import subprocess
import os
from typing import Optional


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

    def make_request(self, method: str, endpoint: str, data=None, params=None):
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
                response = requests.post(url, headers=headers, data=data, timeout=self.timeout)
            
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
        """Execute Windows batch commands"""
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=120, cwd=os.path.dirname(os.path.abspath(__file__)))
            if result.returncode == 0:
                return f"[OK] Success:\n{result.stdout}"
            else:
                return f"[FAIL] Failed (code {result.returncode}):\n{result.stderr}"
        except subprocess.TimeoutExpired:
            return "[FAIL] Command timed out after 2 minutes"
        except Exception as e:
            return f"[FAIL] Error: {str(e)}"

    def duckbot_start_ecosystem(self, mode: str = "unified") -> str:
        """
        Start DuckBot ecosystem in different modes.
        
        :param mode: unified, webui_only, ai_headless, local_only, headless_local, vibevoice, openwebui, quick
        :return: Startup result
        """
        mode_commands = {
            "unified": "START_ENHANCED_DUCKBOT.bat",
            "webui_only": "python -m duckbot.webui",
            "ai_headless": "python start_ai_ecosystem.py",
            "local_only": "START_LOCAL_ONLY.bat",
            "headless_local": "START_HEADLESS_LOCAL.bat",
            "vibevoice": "python start_ai_ecosystem.py",
            "openwebui": "START_OPEN_WEBUI.bat",
            "quick": "python start_ai_ecosystem.py"
        }
        
        if mode not in mode_commands:
            return f"[FAIL] Invalid mode. Available: {', '.join(mode_commands.keys())}"
        
        return f"[LAUNCH] **Starting DuckBot {mode} mode:**\n\n{self.run_batch_command(mode_commands[mode])}"

    def duckbot_emergency_kill(self) -> str:
        """Emergency kill all DuckBot processes"""
        return "[STOP] **Emergency Kill:**\n\n" + self.run_batch_command("EMERGENCY_KILL.bat")

    def duckbot_ai_chat(self, message: str, task_type: str = "auto", priority: str = "medium") -> str:
        """
        Chat with DuckBot AI.
        
        :param message: Your message for the AI
        :param task_type: auto, code, reasoning, summary, long_form, json_format, policy, arbiter
        :param priority: low, medium, high
        :return: AI response
        """
        if not message.strip():
            return "[FAIL] Please provide a message"
        
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
        """Get comprehensive system status"""
        ai_status = self.make_request("GET", "/api/system-status")
        services_status = self.make_request("GET", "/api/services")
        
        report = "[LAUNCH] **DuckBot System Status**\n\n"
        
        if ai_status.get("ok"):
            ai = ai_status.get("status", {})
            report += "[EMOJI] **AI System:**\n"
            report += f"• Model: {ai.get('current_lm_model', 'Unknown')}\n"
            report += f"• Cache: {ai.get('cache_size', 0)} items\n"
            report += f"• Chat Tokens: {ai.get('chat_bucket_tokens', 0)}/{ai.get('chat_bucket_limit', 30)}\n\n"
        
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

    def duckbot_manage_service(self, service_name: str, action: str) -> str:
        """
        Manage DuckBot services.
        
        :param service_name: comfyui, n8n, jupyter, lm_studio, webui, open_notebook, discord_bot
        :param action: start, stop, restart
        :return: Service management result
        """
        if action not in ["start", "stop", "restart"]:
            return "[FAIL] Invalid action. Use: start, stop, restart"
        
        result = self.make_request("POST", f"/api/services/{service_name}/{action}")
        
        if not result.get("success"):
            data = {"service_name": service_name}
            result = self.make_request("POST", f"/servers/{action}", data=data)
        
        if result.get("success") or result.get("ok"):
            message = result.get("result", result.get("message", f"Service {action} completed"))
            return f"[OK] {service_name}: {message}"
        else:
            error = result.get("error", "Unknown error")
            return f"[FAIL] Failed to {action} {service_name}: {error}"

    def duckbot_cost_summary(self, days: int = 7) -> str:
        """
        Get cost and usage analytics.
        
        :param days: Number of days to analyze
        :return: Cost summary
        """
        result = self.make_request("GET", "/api/cost_summary", params={"days": days})
        
        if not result.get("success"):
            return f"[FAIL] Cost data unavailable: {result.get('error', 'Analytics offline')}"
        
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

    def duckbot_rag_search(self, query: str, top_k: int = 5) -> str:
        """
        Search RAG knowledge base.
        
        :param query: Search query
        :param top_k: Number of results
        :return: Search results
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
        """Get available AI models"""
        result = self.make_request("GET", "/models/available")
        
        if not result.get("ok"):
            return f"[FAIL] Models unavailable: {result.get('error', 'LM Studio offline')}"
        
        models = result.get("models", [])
        if not models:
            return "[EMOJI] No models loaded in LM Studio"
        
        response = f"[AI] **Available Models ({len(models)})**\n\n"
        
        for i, model in enumerate(models[:15], 1):
            model_id = model.get("id", "Unknown")
            size = model.get("size", "Unknown")
            response += f"{i}. {model_id} ({size})\n"
        
        if len(models) > 15:
            response += f"\n... and {len(models) - 15} more"
        
        return response

    def duckbot_qwen_analyze(self, code: str) -> str:
        """
        Analyze code with Qwen system.
        
        :param code: Code to analyze
        :return: Analysis results
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

    def duckbot_vibevoice_setup(self) -> str:
        """Setup VibeVoice TTS system"""
        return "[EMOJI] **Setting up VibeVoice TTS:**\n\n" + self.run_batch_command("python setup_vibevoice.py")

    def duckbot_vibevoice_status(self) -> str:
        """Check VibeVoice status"""
        try:
            response = requests.get("http://localhost:8000/voices", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return f"[OK] **VibeVoice Server:**\n\n• Status: Running\n• Voices: {len(data.get('voices', []))}\n• URL: http://localhost:8000"
            else:
                return f"[WARN] VibeVoice server status: {response.status_code}"
        except Exception as e:
            return f"[FAIL] **VibeVoice Server:** Offline\n• Error: {str(e)}\n• Start with: duckbot_vibevoice_setup()"

    def duckbot_fix_dependencies(self) -> str:
        """Fix Python dependencies"""
        return "[TOOLS] **Fixing dependencies:**\n\n" + self.run_batch_command("QUICK_FIX_DEPENDENCIES.bat")

    def duckbot_comprehensive_test(self) -> str:
        """Run comprehensive system tests"""
        return "[EMOJI] **Running system tests:**\n\n" + self.run_batch_command("python test_every_feature.py")

    def duckbot_cache_clear(self) -> str:
        """Clear AI cache"""
        result = self.make_request("POST", "/cache/clear")
        
        if result.get("ok"):
            return "[OK] AI cache cleared successfully"
        else:
            return "[FAIL] Failed to clear cache"

    def duckbot_quick_command(self, command: str) -> str:
        """
        Execute quick DuckBot commands.
        
        :param command: Command to execute (emergency_kill, system_status, cache_clear, fix_deps, test_system, vibevoice_setup, vibevoice_status)
        :return: Command result
        """
        cmd = command.lower().strip()
        
        if cmd == "emergency_kill":
            return self.duckbot_emergency_kill()
        elif cmd == "system_status":
            return self.duckbot_system_status()
        elif cmd == "cache_clear":
            return self.duckbot_cache_clear()
        elif cmd == "fix_deps":
            return self.duckbot_fix_dependencies()
        elif cmd == "test_system":
            return self.duckbot_comprehensive_test()
        elif cmd == "vibevoice_setup":
            return self.duckbot_vibevoice_setup()
        elif cmd == "vibevoice_status":
            return self.duckbot_vibevoice_status()
        elif cmd == "list_models":
            return self.duckbot_list_models()
        else:
            available = ["emergency_kill", "system_status", "cache_clear", "fix_deps", "test_system", "vibevoice_setup", "vibevoice_status", "list_models"]
            return f"[FAIL] Unknown command: {command}\n\nAvailable: {', '.join(available)}"