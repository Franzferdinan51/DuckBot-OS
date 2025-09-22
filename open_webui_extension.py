"""
DuckBot Extension for Open WebUI
Provides complete DuckBot ecosystem integration with Open WebUI chat interface
"""

import json
import requests
import asyncio
import subprocess
import os
import sys
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class DuckBotWebUIExtension:
    """Complete DuckBot integration extension for Open WebUI"""

    def __init__(self):
        self.duckbot_url = "http://localhost:8787"
        self.webui_url = "http://localhost:3000"
        self.timeout = 30
        self.extension_config = {
            "name": "DuckBot Extension",
            "version": "1.0.0",
            "description": "Complete DuckBot AI ecosystem integration",
            "author": "DuckBot Team",
            "features": [
                "ai_chat",
                "system_status",
                "service_control",
                "cost_tracking",
                "rag_search",
                "model_management",
                "desktop_automation",
                "multi_agent_coordination"
            ]
        }

    def get_extension_manifest(self) -> Dict[str, Any]:
        """Get Open WebUI extension manifest"""
        return {
            **self.extension_config,
            "api_endpoints": {
                "chat": "/duckbot/chat",
                "status": "/duckbot/status",
                "services": "/duckbot/services",
                "cost": "/duckbot/cost",
                "search": "/duckbot/search",
                "models": "/duckbot/models",
                "automate": "/duckbot/automate"
            },
            "webhooks": [
                "duckbot.response",
                "duckbot.status_change",
                "duckbot.service_event"
            ]
        }

    async def chat_with_duckbot(self, message: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Send chat message to DuckBot AI system"""
        try:
            # Get authentication token from DuckBot
            token = await self._get_duckbot_token()
            if not token:
                return {
                    "success": False,
                    "error": "DuckBot server not available",
                    "response": "❌ DuckBot server is not running. Please start DuckBot first."
                }

            headers = {"Authorization": f"Bearer {token}"}
            data = {
                "message": message,
                "kind": context.get("task_type", "auto") if context else "auto",
                "risk": "medium",
                "context": context or {}
            }

            response = requests.post(
                f"{self.duckbot_url}/chat",
                headers=headers,
                json=data,
                timeout=self.timeout
            )

            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    return {
                        "success": True,
                        "response": result.get("response", "No response"),
                        "model": result.get("model", "unknown"),
                        "confidence": result.get("confidence", 0),
                        "tokens_used": result.get("tokens_used", 0),
                        "metadata": {
                            "processing_time": result.get("processing_time", 0),
                            "cache_hit": result.get("cache_hit", False)
                        }
                    }
                else:
                    return {
                        "success": False,
                        "error": result.get("response", "Unknown error"),
                        "response": f"❌ AI Error: {result.get('response', 'Unknown error')}"
                    }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}",
                    "response": f"❌ HTTP Error: {response.status_code} - {response.text}"
                }

        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "error": "Connection failed",
                "response": "❌ Cannot connect to DuckBot server. Is it running at localhost:8787?"
            }
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "error": "Request timeout",
                "response": "❌ Request timed out. DuckBot may be busy processing."
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "response": f"❌ Unexpected error: {str(e)}"
            }

    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive DuckBot system status"""
        try:
            token = await self._get_duckbot_token()
            if not token:
                return {"success": False, "error": "DuckBot offline"}

            headers = {"Authorization": f"Bearer {token}"}

            # Get AI system status
            ai_response = requests.get(
                f"{self.duckbot_url}/api/system-status",
                headers=headers,
                timeout=10
            )

            # Get services status
            services_response = requests.get(
                f"{self.duckbot_url}/api/services",
                headers=headers,
                timeout=10
            )

            status_report = {
                "success": True,
                "duckbot_online": True,
                "ai_system": {},
                "services": [],
                "webui_accessible": self._check_webui_access()
            }

            # Parse AI system status
            if ai_response.status_code == 200:
                ai_data = ai_response.json()
                if ai_data.get("ok"):
                    status = ai_data.get("status", {})
                    status_report["ai_system"] = {
                        "current_model": status.get("current_lm_model", "Unknown"),
                        "cache_size": status.get("cache_size", 0),
                        "chat_tokens": f"{status.get('chat_bucket_tokens', 0)}/{status.get('chat_bucket_limit', 30)}",
                        "background_tokens": f"{status.get('background_bucket_tokens', 0)}/{status.get('background_bucket_limit', 30)}"
                    }

            # Parse services status
            if services_response.status_code == 200:
                services_data = services_response.json()
                if services_data.get("ok"):
                    services = services_data.get("services", [])
                    status_report["services"] = [
                        {
                            "name": svc.get("name", "Unknown"),
                            "status": svc.get("status", "unknown"),
                            "port": svc.get("port", "N/A"),
                            "url": f"http://localhost:{svc.get('port', '')}" if svc.get('port') else None
                        }
                        for svc in services
                    ]

                    # Count running services
                    running_count = sum(1 for svc in services if svc.get("status") == "running")
                    status_report["services_summary"] = f"{running_count}/{len(services)} running"

            return status_report

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "duckbot_online": False,
                "services": []
            }

    async def control_service(self, action: str, service_name: str) -> Dict[str, Any]:
        """Control DuckBot services (start/stop)"""
        try:
            token = await self._get_duckbot_token()
            if not token:
                return {"success": False, "error": "DuckBot offline"}

            headers = {"Authorization": f"Bearer {token}"}

            response = requests.post(
                f"{self.duckbot_url}/api/services/{service_name}/{action}",
                headers=headers,
                timeout=45
            )

            if response.status_code == 200:
                result = response.json()
                return {
                    "success": result.get("success", False),
                    "message": result.get("result", "Operation completed"),
                    "error": result.get("error")
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}",
                    "message": f"Failed to {action} {service_name}"
                }

        except requests.exceptions.Timeout:
            return {
                "success": False,
                "error": "timeout",
                "message": f"Service {action} timed out. Check status in a moment."
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Error controlling {service_name}: {str(e)}"
            }

    async def get_cost_summary(self, days: int = 7) -> Dict[str, Any]:
        """Get cost and usage analytics"""
        try:
            token = await self._get_duckbot_token()
            if not token:
                return {"success": False, "error": "DuckBot offline"}

            headers = {"Authorization": f"Bearer {token}"}

            response = requests.get(
                f"{self.duckbot_url}/api/cost_summary?days={days}",
                headers=headers,
                timeout=15
            )

            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    data = result.get("data", {})
                    return {
                        "success": True,
                        "total_cost": data.get('total_cost', 0),
                        "total_tokens": data.get('total_tokens', 0),
                        "total_requests": data.get('total_requests', 0),
                        "by_model": data.get("by_model", {}),
                        "predictions": data.get("predictions", {})
                    }
                else:
                    return {
                        "success": False,
                        "error": result.get('error', 'Analytics unavailable')
                    }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}"
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def search_knowledge_base(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        """Search DuckBot's RAG knowledge base"""
        try:
            token = await self._get_duckbot_token()
            if not token:
                return {"success": False, "error": "DuckBot offline"}

            headers = {"Authorization": f"Bearer {token}"}
            data = {"q": query, "top_k": min(max(top_k, 1), 20)}

            response = requests.post(
                f"{self.duckbot_url}/rag/search",
                headers=headers,
                json=data,
                timeout=20
            )

            if response.status_code == 200:
                result = response.json()
                if result.get("ok"):
                    return {
                        "success": True,
                        "context": result.get("context", ""),
                        "chunks": result.get("chunks", []),
                        "sources": [chunk.get("metadata", {}).get("source", "Unknown") for chunk in result.get("chunks", [])]
                    }
                else:
                    return {
                        "success": False,
                        "error": result.get("error", "Search failed")
                    }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}"
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def get_available_models(self) -> Dict[str, Any]:
        """Get available AI models from LM Studio"""
        try:
            token = await self._get_duckbot_token()
            if not token:
                return {"success": False, "error": "DuckBot offline"}

            headers = {"Authorization": f"Bearer {token}"}

            response = requests.get(
                f"{self.duckbot_url}/models/available",
                headers=headers,
                timeout=15
            )

            if response.status_code == 200:
                result = response.json()
                if result.get("ok"):
                    return {
                        "success": True,
                        "models": result.get("models", []),
                        "lm_studio_url": result.get("lm_studio_url", "http://localhost:1234")
                    }
                else:
                    return {
                        "success": False,
                        "error": result.get("error", "LM Studio connection failed")
                    }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}"
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def automate_desktop_task(self, command: str) -> Dict[str, Any]:
        """Execute desktop automation via ByteBot"""
        try:
            # Check if ByteBot service is available
            status = await self.get_system_status()
            if not status.get("success"):
                return {"success": False, "error": "Cannot check system status"}

            bytebot_running = any(
                svc.get("name") == "ByteBot" and svc.get("status") == "running"
                for svc in status.get("services", [])
            )

            if not bytebot_running:
                return {
                    "success": False,
                    "error": "ByteBot service not running",
                    "message": "Please start ByteBot service first"
                }

            # Send automation command to DuckBot for routing to ByteBot
            result = await self.chat_with_duckbot(
                command,
                context={"task_type": "automation", "priority": "high"}
            )

            if result.get("success"):
                return {
                    "success": True,
                    "message": "Automation command sent to ByteBot",
                    "response": result.get("response", "Command processed")
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error", "Automation failed"),
                    "message": result.get("response", "Failed to process automation command")
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Automation error: {str(e)}"
            }

    async def _get_duckbot_token(self) -> Optional[str]:
        """Get DuckBot authentication token"""
        try:
            response = requests.get(f"{self.duckbot_url}/token", timeout=5)
            if response.status_code == 200:
                return response.json().get("token")
        except:
            pass
        return None

    def _check_webui_access(self) -> bool:
        """Check if Open WebUI is accessible"""
        try:
            response = requests.get(f"{self.webui_url}", timeout=3)
            return response.status_code == 200
        except:
            return False

    def generate_extension_files(self, output_dir: str = ".") -> None:
        """Generate Open WebUI extension files"""
        output_path = Path(output_dir)

        # Create extension manifest
        manifest = {
            "name": "DuckBot Integration",
            "version": "1.0.0",
            "description": "Complete DuckBot AI ecosystem integration",
            "author": "DuckBot Team",
            "license": "MIT",
            "homepage": "https://github.com/duckbot",
            "api": {
                "baseUrl": "http://localhost:8787",
                "endpoints": {
                    "chat": "/chat",
                    "status": "/api/system-status",
                    "services": "/api/services",
                    "cost": "/api/cost_summary",
                    "search": "/rag/search",
                    "models": "/models/available"
                }
            },
            "features": [
                "Real-time AI chat with multiple models",
                "System monitoring and service control",
                "Cost tracking and analytics",
                "Knowledge base search (RAG)",
                "Desktop automation via ByteBot",
                "Multi-agent coordination",
                "Model management and switching"
            ],
            "webui_integration": {
                "chat_interface": True,
                "system_monitoring": True,
                "service_controls": True,
                "cost_dashboard": True,
                "knowledge_search": True,
                "automation_panel": True
            }
        }

        # Write manifest file
        with open(output_path / "duckbot_extension.json", "w") as f:
            json.dump(manifest, f, indent=2)

        # Create JavaScript extension file
        js_extension = '''
// DuckBot Open WebUI Extension
class DuckBotExtension {
    constructor() {
        this.apiBase = "http://localhost:8787";
        this.name = "DuckBot Extension";
        this.version = "1.0.0";
    }

    async chat(message, options = {}) {
        try {
            const response = await fetch(`${this.apiBase}/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${await this.getToken()}`
                },
                body: JSON.stringify({
                    message: message,
                    kind: options.taskType || 'auto',
                    risk: 'medium',
                    context: options.context || {}
                })
            });

            const result = await response.json();
            return {
                success: result.success,
                response: result.response,
                model: result.model,
                confidence: result.confidence
            };
        } catch (error) {
            console.error('DuckBot chat error:', error);
            return {
                success: false,
                response: `Error: ${error.message}`
            };
        }
    }

    async getSystemStatus() {
        try {
            const response = await fetch(`${this.apiBase}/api/system-status`, {
                headers: { 'Authorization': `Bearer ${await this.getToken()}` }
            });
            return await response.json();
        } catch (error) {
            console.error('Status check error:', error);
            return { success: false, error: error.message };
        }
    }

    async getToken() {
        try {
            const response = await fetch(`${this.apiBase}/token`);
            const data = await response.json();
            return data.token;
        } catch (error) {
            console.error('Token error:', error);
            return null;
        }
    }

    async getServiceStatus() {
        try {
            const response = await fetch(`${this.apiBase}/api/services`, {
                headers: { 'Authorization': `Bearer ${await this.getToken()}` }
            });
            return await response.json();
        } catch (error) {
            console.error('Service status error:', error);
            return { success: false, error: error.message };
        }
    }
}

// Register extension globally
window.DuckBotExtension = DuckBotExtension;
'''

        # Write JavaScript extension
        with open(output_path / "duckbot_extension.js", "w") as f:
            f.write(js_extension)

        # Create CSS for DuckBot styling
        css_styles = '''
/* DuckBot Extension Styles */
.duckbot-panel {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 12px;
    padding: 16px;
    margin: 12px 0;
    color: white;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.duckbot-status {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 12px;
}

.duckbot-status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #4ade80;
    animation: pulse 2s infinite;
}

.duckbot-status-dot.offline {
    background: #ef4444;
    animation: none;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}

.duckbot-chat-container {
    background: white;
    border-radius: 8px;
    padding: 16px;
    margin: 12px 0;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.duckbot-model-selector {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    padding: 8px 12px;
    margin: 8px 0;
    width: 100%;
}

.duckbot-cost-display {
    background: #fef3c7;
    border: 1px solid #f59e0b;
    border-radius: 6px;
    padding: 8px 12px;
    margin: 8px 0;
    font-size: 14px;
}

.duckbot-services-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 12px;
    margin: 12px 0;
}

.duckbot-service-card {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    padding: 12px;
    text-align: center;
}

.duckbot-service-card.running {
    border-color: #4ade80;
    background: #f0fdf4;
}

.duckbot-automation-button {
    background: #8b5cf6;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    cursor: pointer;
    font-size: 14px;
    margin: 4px;
    transition: background 0.2s;
}

.duckbot-automation-button:hover {
    background: #7c3aed;
}

.duckbot-automation-button:disabled {
    background: #9ca3af;
    cursor: not-allowed;
}
'''

        # Write CSS styles
        with open(output_path / "duckbot_extension.css", "w") as f:
            f.write(css_styles)

        print(f"✅ DuckBot extension files generated in {output_path}")
        print("Files created:")
        print("  - duckbot_extension.json (manifest)")
        print("  - duckbot_extension.js (JavaScript extension)")
        print("  - duckbot_extension.css (styles)")

        # Create installation instructions
        instructions = '''
# DuckBot Open WebUI Extension Installation

## Quick Install

1. Copy the generated files to your Open WebUI extensions directory:
   ```bash
   # For Docker installations
   cp duckbot_extension.* /path/to/open-webui/extensions/

   # For local installations
   cp duckbot_extension.* ./extensions/
   ```

2. Restart Open WebUI

3. The extension will automatically:
   - Connect to DuckBot at http://localhost:8787
   - Add DuckBot AI chat capabilities
   - Enable system monitoring and service control
   - Provide cost tracking and analytics
   - Add desktop automation features

## Features

- **AI Chat**: Multi-model AI conversations via DuckBot
- **System Status**: Real-time monitoring of all DuckBot services
- **Service Control**: Start/stop DuckBot services from the web interface
- **Cost Analytics**: Track token usage and costs
- **Knowledge Search**: Search DuckBot's RAG knowledge base
- **Desktop Automation**: Control applications via natural language
- **Model Management**: Switch between different AI models

## Configuration

The extension automatically connects to:
- DuckBot API: http://localhost:8787
- Open WebUI: http://localhost:3000

Ensure DuckBot is running before using the extension features.
'''

        with open(output_path / "INSTALL.md", "w") as f:
            f.write(instructions)

# Extension instance for direct use
duckbot_extension = DuckBotWebUIExtension()

# Convenience functions for Open WebUI integration
async def duckbot_chat(message: str, **kwargs) -> Dict[str, Any]:
    """Chat with DuckBot from Open WebUI"""
    return await duckbot_extension.chat_with_duckbot(message, kwargs)

async def duckbot_status() -> Dict[str, Any]:
    """Get DuckBot system status"""
    return await duckbot_extension.get_system_status()

async def duckbot_service_control(action: str, service: str) -> Dict[str, Any]:
    """Control DuckBot services"""
    return await duckbot_extension.control_service(action, service)

async def duckbot_automate(command: str) -> Dict[str, Any]:
    """Execute desktop automation"""
    return await duckbot_extension.automate_desktop_task(command)

# Export for Open WebUI
__all__ = [
    'DuckBotWebUIExtension',
    'duckbot_chat',
    'duckbot_status',
    'duckbot_service_control',
    'duckbot_automate',
    'duckbot_extension'
]