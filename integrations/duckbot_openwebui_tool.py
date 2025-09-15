"""
title: DuckBot Control
author: DuckBot Team
version: 3.0.0
license: MIT
description: Complete DuckBot ecosystem control - AI chat, services, cost tracking, RAG search, VibeVoice TTS, Qwen analysis, and system management
requirements: requests
"""

import requests
import subprocess
import os
from typing import Optional


class Tools:
    def __init__(self):
        pass

    def duckbot_ai_chat(self, message: str, task_type: str = "auto") -> str:
        """
        Chat with DuckBot AI system.
        
        Args:
            message: Your message or question for DuckBot AI
            task_type: Type of AI task - auto, code, reasoning, summary, long_form
        
        Returns:
            AI response from DuckBot
        """
        
        try:
            # Get DuckBot token
            token_response = requests.get("http://localhost:8787/token", timeout=5)
            if token_response.status_code != 200:
                return "[FAIL] DuckBot server not available at http://localhost:8787"
            
            token = token_response.json().get("token")
            if not token:
                return "[FAIL] Could not get DuckBot authentication token"
            
            # Send chat request
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
                
        except requests.exceptions.ConnectionError:
            return "[FAIL] Cannot connect to DuckBot server. Is it running at localhost:8787?"
        except requests.exceptions.Timeout:
            return "[FAIL] Request timed out. DuckBot may be busy."
        except Exception as e:
            return f"[FAIL] Error: {str(e)}"

    def duckbot_system_status(self) -> str:
        """
        Get DuckBot system status.
        
        Returns:
            Complete system status report
        """
        
        try:
            # Get token
            token_response = requests.get("http://localhost:8787/token", timeout=5)
            if token_response.status_code != 200:
                return "[FAIL] DuckBot server not available"
            
            token = token_response.json().get("token")
            headers = {"Authorization": f"Bearer {token}"}
            
            # Get system status
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

    def duckbot_start_service(self, service_name: str) -> str:
        """
        Start a DuckBot service.
        
        Args:
            service_name: Service to start (comfyui, n8n, jupyter, lm_studio, webui)
        
        Returns:
            Service start result
        """
        
        if not service_name:
            return "[FAIL] Please specify a service name (comfyui, n8n, jupyter, lm_studio, webui)"
        
        try:
            # Get token
            token_response = requests.get("http://localhost:8787/token", timeout=5)
            if token_response.status_code != 200:
                return "[FAIL] DuckBot server not available"
            
            token = token_response.json().get("token")
            headers = {"Authorization": f"Bearer {token}"}
            
            # Start service
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

    def duckbot_stop_service(self, service_name: str) -> str:
        """
        Stop a DuckBot service.
        
        Args:
            service_name: Service to stop (comfyui, n8n, jupyter, lm_studio, webui)
        
        Returns:
            Service stop result
        """
        
        if not service_name:
            return "[FAIL] Please specify a service name"
        
        try:
            token_response = requests.get("http://localhost:8787/token", timeout=5)
            if token_response.status_code != 200:
                return "[FAIL] DuckBot server not available"
            
            token = token_response.json().get("token")
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

    def duckbot_emergency_kill(self) -> str:
        """
        Emergency kill all DuckBot processes.
        
        Returns:
            Kill operation result
        """
        
        try:
            # Try to find DuckBot directory and run emergency kill
            current_dir = os.getcwd()
            
            # Look for EMERGENCY_KILL.bat in current directory or parent directories
            kill_script = None
            search_dirs = [current_dir, os.path.dirname(current_dir), os.path.dirname(os.path.dirname(current_dir))]
            
            for directory in search_dirs:
                potential_script = os.path.join(directory, "EMERGENCY_KILL.bat")
                if os.path.exists(potential_script):
                    kill_script = potential_script
                    break
            
            if kill_script:
                result = subprocess.run([kill_script], shell=True, capture_output=True, text=True, timeout=30)
                if result.returncode == 0:
                    return f"[OK] **Emergency Kill Completed:**\n\n{result.stdout}"
                else:
                    return f"[WARN] **Emergency Kill Result:**\n\n{result.stderr}"
            else:
                # Fallback - kill python processes manually
                result = subprocess.run(["taskkill", "/F", "/IM", "python.exe"], capture_output=True, text=True)
                return f"⚡ **Manual Process Kill:**\n\n{result.stdout if result.returncode == 0 else result.stderr}"
                
        except Exception as e:
            return f"[FAIL] Error during emergency kill: {str(e)}"

    def duckbot_cost_summary(self, days: int = 7) -> str:
        """
        Get DuckBot usage and cost summary.
        
        Args:
            days: Number of days to analyze (1-365)
        
        Returns:
            Cost and usage summary
        """
        
        try:
            token_response = requests.get("http://localhost:8787/token", timeout=5)
            if token_response.status_code != 200:
                return "[FAIL] DuckBot server not available"
            
            token = token_response.json().get("token")
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

    def duckbot_rag_search(self, query: str, top_k: int = 5) -> str:
        """
        Search DuckBot's RAG knowledge base.
        
        Args:
            query: Search query for the knowledge base
            top_k: Number of results to return (1-20)
        
        Returns:
            Search results from RAG system
        """
        
        if not query.strip():
            return "[FAIL] Please provide a search query"
        
        try:
            token_response = requests.get("http://localhost:8787/token", timeout=5)
            if token_response.status_code != 200:
                return "[FAIL] DuckBot server not available"
            
            token = token_response.json().get("token")
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

    def duckbot_start_ecosystem(self, mode: str = "unified") -> str:
        """
        Start DuckBot ecosystem.
        
        Args:
            mode: Startup mode - unified, local_only, webui_only, headless
        
        Returns:
            Ecosystem startup result
        """
        
        try:
            # Try to find and run the appropriate startup script
            current_dir = os.getcwd()
            
            mode_scripts = {
                "unified": "START_ENHANCED_DUCKBOT.bat",
                "local_only": "START_LOCAL_ONLY.bat", 
                "webui_only": "python -m duckbot.webui",
                "headless": "START_HEADLESS_LOCAL.bat"
            }
            
            script = mode_scripts.get(mode, mode_scripts["unified"])
            
            if script.endswith(".bat"):
                # Look for batch file
                script_path = None
                search_dirs = [current_dir, os.path.dirname(current_dir)]
                
                for directory in search_dirs:
                    potential_path = os.path.join(directory, script)
                    if os.path.exists(potential_path):
                        script_path = potential_path
                        break
                
                if script_path:
                    # Start the batch file in background
                    subprocess.Popen([script_path], shell=True, cwd=os.path.dirname(script_path))
                    return f"[OK] **Starting DuckBot {mode} mode**\n\nEcosystem startup initiated. Check http://localhost:8787 in ~30 seconds."
                else:
                    return f"[FAIL] Could not find startup script: {script}"
            else:
                # Python command
                subprocess.Popen(script.split(), shell=True)
                return f"[OK] **Starting DuckBot {mode} mode**\n\nWebUI starting... Check http://localhost:8787"
                
        except Exception as e:
            return f"[FAIL] Error starting ecosystem: {str(e)}"

    def duckbot_list_models(self) -> str:
        """
        Get available AI models from LM Studio.
        
        Returns:
            List of available AI models
        """
        
        try:
            token_response = requests.get("http://localhost:8787/token", timeout=5)
            if token_response.status_code != 200:
                return "[FAIL] DuckBot server not available"
            
            token = token_response.json().get("token")
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

    def duckbot_qwen_analyze(self, code: str) -> str:
        """
        Analyze code using DuckBot's Qwen enhanced system.
        
        Args:
            code: Code to analyze
        
        Returns:
            Code analysis results
        """
        
        if not code.strip():
            return "[FAIL] Please provide code to analyze"
        
        try:
            token_response = requests.get("http://localhost:8787/token", timeout=5)
            if token_response.status_code != 200:
                return "[FAIL] DuckBot server not available"
            
            token = token_response.json().get("token")
            headers = {"Authorization": f"Bearer {token}"}
            data = {"code_prompt": code}
            
            response = requests.post("http://localhost:8787/qwen/analyze", headers=headers, data=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("ok"):
                    analysis = result.get("analysis", "No analysis available")
                    enhanced = " (Qwen Enhanced)" if result.get("qwen_enhanced") else ""
                    return f"[EMOJI] **Code Analysis{enhanced}:**\n\n{analysis}"
                else:
                    return f"[FAIL] Analysis failed: {result.get('error', 'Qwen unavailable')}"
            else:
                return f"[FAIL] HTTP Error {response.status_code}"
                
        except Exception as e:
            return f"[FAIL] Error analyzing code: {str(e)}"

    def duckbot_vibevoice_tts(self, text: str, voice: str = "default") -> str:
        """
        Generate speech using VibeVoice TTS system.
        
        Args:
            text: Text to convert to speech
            voice: Voice to use for TTS generation
        
        Returns:
            TTS generation result with audio URL
        """
        
        if not text.strip():
            return "[FAIL] Please provide text to convert to speech"
        
        try:
            token_response = requests.get("http://localhost:8787/token", timeout=5)
            if token_response.status_code != 200:
                return "[FAIL] DuckBot server not available"
            
            token = token_response.json().get("token")
            headers = {"Authorization": f"Bearer {token}"}
            data = {"text": text, "voice": voice}
            
            response = requests.post("http://localhost:8787/vibevoice/tts", headers=headers, data=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    audio_url = result.get("audio_url", "")
                    voice_used = result.get("voice", voice)
                    duration = result.get("duration", 0)
                    
                    return f"[EMOJI] **VibeVoice TTS Generated**\n\n**Voice:** {voice_used}\n**Duration:** {duration}s\n**Audio URL:** {audio_url}"
                else:
                    error = result.get("error", "TTS generation failed")
                    return f"[FAIL] TTS Error: {error}"
            else:
                return f"[FAIL] HTTP Error {response.status_code}"
                
        except Exception as e:
            return f"[FAIL] Error with VibeVoice TTS: {str(e)}"

    def duckbot_vibevoice_status(self) -> str:
        """
        Check VibeVoice TTS system status.
        
        Returns:
            VibeVoice system status and available voices
        """
        
        try:
            # Check VibeVoice server directly
            response = requests.get("http://localhost:8000/voices", timeout=5)
            if response.status_code == 200:
                data = response.json()
                voices = data.get('voices', [])
                
                status_report = "[OK] **VibeVoice TTS Server**\n\n"
                status_report += f"• **Status:** Running\n"
                status_report += f"• **Available Voices:** {len(voices)}\n"
                status_report += f"• **Server URL:** http://localhost:8000\n\n"
                
                if voices:
                    status_report += "[EMOJI] **Voice List:**\n"
                    for i, voice in enumerate(voices[:5], 1):
                        status_report += f"{i}. {voice}\n"
                    if len(voices) > 5:
                        status_report += f"... and {len(voices) - 5} more voices"
                
                return status_report
            else:
                return f"[WARN] VibeVoice server status: HTTP {response.status_code}"
                
        except requests.exceptions.ConnectionError:
            return "[FAIL] **VibeVoice Server:** Offline\n\n• Server not running at http://localhost:8000\n• Start VibeVoice server first"
        except Exception as e:
            return f"[FAIL] Error checking VibeVoice status: {str(e)}"

    def duckbot_comprehensive_command(self, command: str) -> str:
        """
        Execute comprehensive DuckBot commands with full ecosystem control.
        
        Args:
            command: Command to execute (status, kill, restart_all, fix_deps, test_all, cache_clear)
        
        Returns:
            Command execution result
        """
        
        cmd = command.lower().strip()
        
        if cmd == "status":
            return self.duckbot_system_status()
        elif cmd == "kill" or cmd == "emergency_kill":
            return self.duckbot_emergency_kill()
        elif cmd == "restart_all":
            kill_result = self.duckbot_emergency_kill()
            return kill_result + "\n\n" + self.duckbot_start_ecosystem("unified")
        elif cmd == "fix_deps":
            return self.run_batch_command("QUICK_FIX_DEPENDENCIES.bat")
        elif cmd == "test_all":
            return self.run_batch_command("python test_every_feature.py")
        elif cmd == "cache_clear":
            try:
                token_response = requests.get("http://localhost:8787/token", timeout=5)
                if token_response.status_code != 200:
                    return "[FAIL] DuckBot server not available"
                
                token = token_response.json().get("token")
                headers = {"Authorization": f"Bearer {token}"}
                
                response = requests.post("http://localhost:8787/cache/clear", headers=headers, timeout=10)
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("ok"):
                        return "[OK] AI cache cleared successfully"
                    else:
                        return "[FAIL] Failed to clear cache"
                else:
                    return f"[FAIL] HTTP Error {response.status_code}"
            except Exception as e:
                return f"[FAIL] Error clearing cache: {str(e)}"
        else:
            available = ["status", "kill", "restart_all", "fix_deps", "test_all", "cache_clear"]
            return f"[FAIL] Unknown command: {command}\n\nAvailable: {', '.join(available)}"

    def run_batch_command(self, command: str) -> str:
        """
        Execute Windows batch commands safely.
        
        Args:
            command: Batch command or script to execute
        
        Returns:
            Command execution result
        """
        
        try:
            current_dir = os.getcwd()
            
            # If it's a .bat file, look for it
            if command.endswith(".bat"):
                script_path = None
                search_dirs = [current_dir, os.path.dirname(current_dir)]
                
                for directory in search_dirs:
                    potential_path = os.path.join(directory, command)
                    if os.path.exists(potential_path):
                        script_path = potential_path
                        break
                
                if script_path:
                    result = subprocess.run([script_path], shell=True, capture_output=True, text=True, timeout=120, cwd=os.path.dirname(script_path))
                else:
                    return f"[FAIL] Script not found: {command}"
            else:
                # Direct command execution
                result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=120, cwd=current_dir)
            
            if result.returncode == 0:
                return f"[OK] **Success:**\n\n{result.stdout}"
            else:
                return f"[FAIL] **Failed (code {result.returncode}):**\n\n{result.stderr}"
                
        except subprocess.TimeoutExpired:
            return "[FAIL] Command timed out after 2 minutes"
        except Exception as e:
            return f"[FAIL] Error executing command: {str(e)}"