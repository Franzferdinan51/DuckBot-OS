#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DuckBot Unified WebUI - Consolidated Interface
Combines the best features from enhanced_webui.py, webui_enhanced.py, webui_modern.py, and newelle_integration.py
Single entry point for all WebUI functionality with multiple interface modes
"""

import gradio as gr
import asyncio
import json
import logging
import argparse
from datetime import datetime
from typing import Dict, List, Optional, Any
import uvicorn
from fastapi import FastAPI, Request, WebSocket, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import sys
import os
import base64
from io import BytesIO

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import consolidated functionality
try:
    from duckbot.ai_router_gpt import route_task_async
    from multi_agent_activator import get_multi_agent_system
    from duckbot.integrations.mcp_server import mcp
    from duckbot.integrations.ui_tars_integration import UITarsIntegration
    from duckbot.integrations.bytebot_integration import ByteBotIntegration
    from duckbot.integrations.memento_integration import MementoIntegration
except ImportError as e:
    logging.warning(f"Some integrations not available: {e}")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Theme definitions for multiple interface modes
THEME_MAP = {
    "Default": gr.themes.Default(),
    "Soft": gr.themes.Soft(),
    "Monochrome": gr.themes.Monochrome(),
    "Glass": gr.themes.Glass(),
    "Origin": gr.themes.Origin(),
    "Citrus": gr.themes.Citrus(),
    "Ocean": gr.themes.Ocean(),
    "Base": gr.themes.Base()
}

INTERFACE_MODES = {
    "classic": "Classic Enhanced - Original style with modern features",
    "modern": "Modern UI - UI-TARS inspired design",
    "minimal": "Minimal - Clean and simple interface",
    "terminal": "Terminal - Command-line focused interface"
}

class DuckBotUnifiedWebUI:
    """Unified WebUI supporting multiple interface modes and all integrations"""

    def __init__(self, interface_mode="classic"):
        self.interface_mode = interface_mode
        self.multi_agent_system = None
        self.chat_history = []
        self.integrations = {}
        self.app = FastAPI(title="DuckBot Unified WebUI", version="4.2")

        # Initialize integrations
        self._initialize_integrations()

        # Setup FastAPI app
        self._setup_fastapi()

        # Create Gradio interface based on mode
        self.interface = self._create_interface()

    def _initialize_integrations(self):
        """Initialize all available integrations"""
        try:
            # UI-TARS Integration
            self.integrations['ui_tars'] = UITarsIntegration()
            asyncio.create_task(self.integrations['ui_tars'].initialize())

            # ByteBot Integration
            self.integrations['bytebot'] = ByteBotIntegration()
            asyncio.create_task(self.integrations['bytebot'].initialize())

            # Memento Integration
            self.integrations['memento'] = MementoIntegration()

            logger.info(f"Initialized {len(self.integrations)} integrations")
        except Exception as e:
            logger.error(f"Failed to initialize integrations: {e}")

    def _setup_fastapi(self):
        """Setup FastAPI application with middleware"""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        @self.app.get("/")
        async def read_root():
            return {"message": "DuckBot Unified WebUI", "mode": self.interface_mode}

        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await websocket.accept()
            try:
                while True:
                    data = await websocket.receive_text()
                    response = await self._process_websocket_message(data)
                    await websocket.send_text(response)
            except WebSocketDisconnect:
                logger.info("WebSocket disconnected")

    def _create_interface(self):
        """Create Gradio interface based on selected mode"""

        if self.interface_mode == "modern":
            return self._create_modern_interface()
        elif self.interface_mode == "minimal":
            return self._create_minimal_interface()
        elif self.interface_mode == "terminal":
            return self._create_terminal_interface()
        else:
            return self._create_classic_interface()

    def _create_classic_interface(self):
        """Create classic enhanced interface (original style)"""
        with gr.Blocks(
            theme=THEME_MAP["Soft"],
            title="DuckBot Unified WebUI - Classic Mode",
            css="""
            .main-header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                border-radius: 10px;
                margin-bottom: 20px;
            }
            """
        ) as interface:

            # Header
            gr.HTML("""
            <div class="main-header">
                <h1>🦆 DuckBot Unified WebUI - Classic Mode</h1>
                <p>Original style with all modern enhancements and integrations</p>
            </div>
            """)

            with gr.Tabs():
                # Chat Tab
                with gr.TabItem("💬 Chat Assistant"):
                    with gr.Row():
                        with gr.Column(scale=3):
                            chatbot = gr.Chatbot(height=500, label="Chat History")
                            msg = gr.Textbox(label="Message", placeholder="Ask DuckBot anything...")
                            with gr.Row():
                                submit_btn = gr.Button("Send", variant="primary")
                                clear_btn = gr.Button("Clear")
                        with gr.Column(scale=1):
                            use_multi_agent = gr.Checkbox(label="Use Multi-Agent", value=True)
                            agent_type = gr.Dropdown(
                                choices=["general", "reasoning", "coding", "analysis"],
                                value="general",
                                label="Agent Type"
                            )

                    # Status info
                    status_info = gr.HTML(value="<div id='status'>Ready</div>")

                    # Chat response function
                    async def respond(message, chat_history, use_multi_agent, agent_type):
                        if not message.strip():
                            return "", chat_history

                        try:
                            # Route through AI system
                            result = await route_task_async(
                                message,
                                task_type=agent_type,
                                complexity="medium"
                            )

                            response = result.get("response", "I'm not sure how to respond to that.")

                            # Add to chat history
                            chat_history.append((message, response))

                            # Update status
                            status_html = f"""
                            <div id='status'>
                                <strong>Status:</strong> Active<br>
                                <strong>Agent:</strong> {agent_type}<br>
                                <strong>Multi-Agent:</strong> {'Yes' if use_multi_agent else 'No'}<br>
                                <strong>Response Time:</strong> {result.get('execution_time', 0):.2f}s
                            </div>
                            """

                            return "", chat_history, status_html

                        except Exception as e:
                            error_msg = f"Error: {str(e)}"
                            chat_history.append((message, error_msg))
                            return "", chat_history, "<div id='status'>Error occurred</div>"

                    submit_btn.click(
                        respond,
                        [msg, chatbot, use_multi_agent, agent_type],
                        [msg, chatbot, status_info]
                    )
                    clear_btn.click(lambda: ([], ""), [], [chatbot, msg])

                # System Monitoring Tab
                with gr.TabItem("📊 System Monitor"):
                    gr.HTML("<h3>System Status and Monitoring</h3>")
                    system_status = gr.HTML(value=self._get_system_status())
                    refresh_btn = gr.Button("Refresh Status")
                    refresh_btn.click(lambda: gr.HTML(value=self._get_system_status()), [], [system_status])

                # Integrations Tab
                with gr.TabItem("🔗 Integrations"):
                    gr.HTML("<h3>Available Integrations</h3>")
                    with gr.Accordion("UI-TARS Desktop Automation", open=True):
                        gr.HTML(self._get_integration_status('ui_tars'))
                    with gr.Accordion("ByteBot Desktop Assistant", open=True):
                        gr.HTML(self._get_integration_status('bytebot'))
                    with gr.Accordion("Memento Memory System", open=True):
                        gr.HTML(self._get_integration_status('memento'))
                    with gr.Accordion("MCP Server Tools", open=True):
                        gr.HTML(self._get_mcp_tools_list())

                # Settings Tab
                with gr.TabItem("⚙️ Settings"):
                    gr.HTML("<h3>WebUI Configuration</h3>")
                    with gr.Row():
                        theme_choice = gr.Dropdown(
                            choices=list(THEME_MAP.keys()),
                            value="Soft",
                            label="Theme"
                        )
                        interface_mode_choice = gr.Dropdown(
                            choices=list(INTERFACE_MODES.keys()),
                            value="classic",
                            label="Interface Mode"
                        )

                    apply_settings_btn = gr.Button("Apply Settings")
                    settings_output = gr.HTML()

                    def apply_settings(theme, mode):
                        return f"<div>Settings applied: Theme={theme}, Mode={mode}<br>Restart required for mode change.</div>"

                    apply_settings_btn.click(
                        apply_settings,
                        [theme_choice, interface_mode_choice],
                        [settings_output]
                    )

        return interface

    def _create_modern_interface(self):
        """Create modern UI-TARS inspired interface"""
        with gr.Blocks(
            theme=THEME_MAP["Glass"],
            title="DuckBot Unified WebUI - Modern Mode",
            css="""
            .modern-header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                border-radius: 15px;
                margin-bottom: 30px;
                text-align: center;
            }
            .feature-card {
                background: rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 10px;
                padding: 20px;
                margin: 10px;
            }
            """
        ) as interface:

            # Modern header
            gr.HTML("""
            <div class="modern-header">
                <h1>🦆 DuckBot Unified WebUI - Modern Mode</h1>
                <p>UI-TARS inspired design with advanced automation features</p>
            </div>
            """)

            with gr.Tabs():
                # Main Dashboard Tab
                with gr.TabItem("🎯 Dashboard"):
                    with gr.Row():
                        with gr.Column():
                            # Quick Actions
                            gr.HTML("<h3>Quick Actions</h3>")
                            with gr.Row():
                                screenshot_btn = gr.Button("📸 Take Screenshot", variant="primary")
                                automate_btn = gr.Button("🤖 Start Automation", variant="primary")
                                analyze_btn = gr.Button("🔍 Analyze Screen", variant="primary")

                            # Results Area
                            results_area = gr.HTML(value="<div id='results'>Ready for commands</div>")

                        with gr.Column():
                            # Chat Interface
                            gr.HTML("<h3>AI Assistant</h3>")
                            chatbot = gr.Chatbot(height=400, label="AI Assistant")
                            msg = gr.Textbox(label="Command", placeholder="Describe what you want to automate...")
                            send_cmd_btn = gr.Button("Execute", variant="primary")

                # Advanced Automation Tab
                with gr.TabItem("🔧 Advanced Automation"):
                    with gr.Row():
                        with gr.Column():
                            gr.HTML("<h3>UI-TARS Controls</h3>")
                            automation_script = gr.Textbox(
                                label="Automation Script",
                                placeholder="Describe the automation sequence...",
                                lines=5
                            )
                            with gr.Row():
                                run_script_btn = gr.Button("▶️ Run Script", variant="primary")
                                save_script_btn = gr.Button("💾 Save Script")

                        with gr.Column():
                            gr.HTML("<h3>Screen Analysis</h3>")
                            screenshot_display = gr.Image(label="Current Screen", type="filepath")
                            analysis_results = gr.HTML(value="<div>No screenshot taken</div>")

                # Multi-Agent Coordination Tab
                with gr.TabItem("👥 Multi-Agent System"):
                    gr.HTML("<h3>Agent Coordination Center</h3>")
                    with gr.Row():
                        with gr.Column():
                            agent_status = gr.HTML(value=self._get_agent_status())
                            refresh_agents_btn = gr.Button("Refresh Agents")

                        with gr.Column():
                            task_input = gr.Textbox(
                                label="Assign Task to Agents",
                                placeholder="Describe the complex task...",
                                lines=3
                            )
                            assign_task_btn = gr.Button("Assign Task", variant="primary")
                            task_results = gr.HTML()

        return interface

    def _create_minimal_interface(self):
        """Create minimal clean interface"""
        with gr.Blocks(
            theme=THEME_MAP["Monochrome"],
            title="DuckBot Unified WebUI - Minimal Mode"
        ) as interface:

            gr.HTML("<h1>🦆 DuckBot</h1>")

            with gr.Row():
                with gr.Column():
                    chatbot = gr.Chatbot(height=600)
                    msg = gr.Textbox(placeholder="Type your message...")
                    send_btn = gr.Button("Send", variant="primary")

            # Simple response function
            async def simple_respond(message, chat_history):
                if message.strip():
                    try:
                        result = await route_task_async(message, "general", "low")
                        response = result.get("response", "I understand.")
                        chat_history.append((message, response))
                    except:
                        chat_history.append((message, "I'm having trouble responding right now."))
                return "", chat_history

            send_btn.click(simple_respond, [msg, chatbot], [msg, chatbot])

        return interface

    def _create_terminal_interface(self):
        """Create terminal-focused interface"""
        with gr.Blocks(
            theme=THEME_MAP["Base"],
            title="DuckBot Unified WebUI - Terminal Mode"
        ) as interface:

            gr.HTML("<h1>🖥️ DuckBot Terminal Interface</h1>")

            with gr.Row():
                with gr.Column():
                    terminal_output = gr.Textbox(
                        label="Terminal Output",
                        value="DuckBot Terminal Ready\n> ",
                        lines=20,
                        interactive=False
                    )
                    command_input = gr.Textbox(
                        label="Enter Command",
                        placeholder="Type commands or ask questions..."
                    )
                    execute_btn = gr.Button("Execute", variant="primary")

            # Terminal command processor
            async def execute_command(command, terminal):
                if not command.strip():
                    return terminal, ""

                # Add command to terminal
                terminal += f"\n> {command}\n"

                try:
                    # Try to execute as system command first, then as AI task
                    if command.startswith("!"):
                        # System command
                        result = await self._execute_system_command(command[1:])
                    else:
                        # AI task
                        result = await route_task_async(command, "general", "low")
                        result = result.get("response", "Command processed.")

                    terminal += f"{result}\n"
                except Exception as e:
                    terminal += f"Error: {str(e)}\n"

                return terminal, ""

            execute_btn.click(
                execute_command,
                [command_input, terminal_output],
                [terminal_output, command_input]
            )

        return interface

    def _get_system_status(self):
        """Get current system status HTML"""
        return f"""
        <div style='padding: 15px; background: #f8f9fa; border-radius: 8px;'>
            <h3>System Status</h3>
            <p><strong>Interface Mode:</strong> {self.interface_mode}</p>
            <p><strong>Active Integrations:</strong> {len([i for i in self.integrations.values() if hasattr(i, 'available') and i.available])}</p>
            <p><strong>Total Integrations:</strong> {len(self.integrations)}</p>
            <p><strong>Server Status:</strong> Running</p>
            <p><strong>Last Update:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        """

    def _get_integration_status(self, integration_name):
        """Get status HTML for specific integration"""
        integration = self.integrations.get(integration_name)
        if integration and hasattr(integration, 'available') and integration.available:
            status = "✅ Active"
            color = "green"
        else:
            status = "❌ Inactive"
            color = "red"

        return f"""
        <div style='padding: 10px; border-left: 4px solid {color}; background: #f8f9fa;'>
            <strong>{integration_name.upper()}:</strong> {status}
        </div>
        """

    def _get_mcp_tools_list(self):
        """Get list of available MCP tools"""
        try:
            if hasattr(mcp, 'list_tools'):
                tools = mcp.list_tools()
                tools_html = "<ul>"
                for tool in tools[:10]:  # Show first 10 tools
                    tools_html += f"<li>{tool.get('name', 'Unknown')}</li>"
                tools_html += "</ul>"
                return tools_html
        except:
            pass

        return "<p>MCP tools not available</p>"

    def _get_agent_status(self):
        """Get multi-agent system status"""
        try:
            if self.multi_agent_system:
                return f"""
                <div style='padding: 15px; background: #e8f5e8; border-radius: 8px;'>
                    <h3>Multi-Agent System Active</h3>
                    <p>Agents are ready for task coordination</p>
                    <p>Available agent types: general, reasoning, coding, analysis</p>
                </div>
                """
        except:
            pass

        return """
        <div style='padding: 15px; background: #fff3cd; border-radius: 8px;'>
            <h3>Multi-Agent System</h3>
            <p>Agent system not initialized</p>
        </div>
        """

    async def _execute_system_command(self, command):
        """Execute a system command"""
        import subprocess
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.stdout or result.stderr or "Command executed"
        except subprocess.TimeoutExpired:
            return "Command timed out"
        except Exception as e:
            return f"Error: {str(e)}"

    async def _process_websocket_message(self, data):
        """Process incoming WebSocket messages"""
        try:
            message_data = json.loads(data)
            message_type = message_data.get('type', 'chat')
            content = message_data.get('content', '')

            if message_type == 'chat':
                result = await route_task_async(content, 'general', 'medium')
                response = result.get('response', 'No response')

                return json.dumps({
                    'type': 'response',
                    'content': response,
                    'timestamp': datetime.now().isoformat()
                })
            elif message_type == 'status':
                status = {
                    'type': 'status',
                    'integrations': len(self.integrations),
                    'mode': self.interface_mode,
                    'timestamp': datetime.now().isoformat()
                }
                return json.dumps(status)
            else:
                return json.dumps({'type': 'error', 'message': 'Unknown message type'})

        except Exception as e:
            return json.dumps({'type': 'error', 'message': str(e)})

    def mount_gradio(self):
        """Mount Gradio interface to FastAPI app"""
        return gr.mount_gradio_app(self.app, self.interface, path="/")

    async def startup(self):
        """Startup the WebUI server"""
        logger.info(f"Starting DuckBot Unified WebUI in {self.interface_mode} mode")

        # Initialize all integrations
        for name, integration in self.integrations.items():
            if hasattr(integration, 'initialize'):
                try:
                    await integration.initialize()
                    logger.info(f"Initialized {name} integration")
                except Exception as e:
                    logger.error(f"Failed to initialize {name}: {e}")

    async def shutdown(self):
        """Shutdown the WebUI server"""
        logger.info("Shutting down DuckBot Unified WebUI")

        # Cleanup integrations
        for name, integration in self.integrations.items():
            if hasattr(integration, 'cleanup'):
                try:
                    await integration.cleanup()
                    logger.info(f"Cleaned up {name} integration")
                except Exception as e:
                    logger.error(f"Failed to cleanup {name}: {e}")

# Global instance for module-level access
unified_webui_instance = None

def get_unified_webui(interface_mode="classic"):
    """Get or create the unified webui instance"""
    global unified_webui_instance
    if unified_webui_instance is None:
        unified_webui_instance = DuckBotUnifiedWebUI(interface_mode)
    return unified_webui_instance

# Main execution
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DuckBot Unified WebUI")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8787, help="Port to bind to")
    parser.add_argument("--mode", choices=list(INTERFACE_MODES.keys()),
                       default="classic", help="Interface mode")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")

    args = parser.parse_args()

    # Create and start the unified webui
    webui = DuckBotUnifiedWebUI(interface_mode=args.mode)

    # Mount Gradio interface
    app = webui.mount_gradio()

    # Run the server
    print(f"Starting DuckBot Unified WebUI on {args.host}:{args.port}")
    print(f"Interface mode: {args.mode}")
    print(f"Available modes: {list(INTERFACE_MODES.keys())}")

    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info"
    )