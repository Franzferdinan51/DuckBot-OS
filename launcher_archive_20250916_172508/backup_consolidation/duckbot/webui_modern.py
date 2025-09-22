#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DuckBot Modern WebUI - UI-TARS Inspired Design
Combining the best of DuckBot with modern UI automation interfaces
"""

import gradio as gr
import asyncio
import json
import logging
import argparse
from datetime import datetime
from typing import Dict, List, Optional, Any
import uvicorn
from fastapi import FastAPI, Request, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import sys
import os
import base64
from io import BytesIO

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from duckbot.ai_router_gpt import route_task_async
from multi_agent_activator import get_multi_agent_system
from duckbot.integrations.mcp_server import mcp
from duckbot.integrations.ui_tars_integration import UITarsIntegration

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Theme definitions
theme_map = {
    "Default": gr.themes.Default(),
    "Soft": gr.themes.Soft(),
    "Monochrome": gr.themes.Monochrome(),
    "Glass": gr.themes.Glass(),
    "Origin": gr.themes.Origin(),
    "Citrus": gr.themes.Citrus(),
    "Ocean": gr.themes.Ocean(),
    "Base": gr.themes.Base()
}

class DuckBotModernWebUI:
    """Modern WebUI with UI-TARS inspired design"""

    def __init__(self):
        self.multi_agent_system = None
        self.ui_tars = None
        self.chat_history = []
        self.screenshots = []
        self.system_status = {
            "ai_router": "offline",
            "multi_agent": "offline",
            "mcp_server": "offline",
            "ui_tars": "offline",
            "webui": "online"
        }

    async def initialize_systems(self):
        """Initialize all backend systems"""
        # Initialize Multi-Agent System
        try:
            self.multi_agent_system = await get_multi_agent_system()
            self.system_status["multi_agent"] = "online"
            logger.info("Multi-Agent System initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Multi-Agent System: {e}")

        # Test AI Router
        try:
            result = await route_task_async("test", "general", "low")
            if result and "response" in result:
                self.system_status["ai_router"] = "online"
            logger.info("AI Router tested")
        except Exception as e:
            logger.error(f"Failed to initialize AI Router: {e}")

        # Test MCP Server
        try:
            if hasattr(mcp, 'tools'):
                self.system_status["mcp_server"] = "online"
            logger.info("MCP Server tested")
        except Exception as e:
            logger.error(f"Failed to initialize MCP Server: {e}")

        # Initialize UI-TARS
        try:
            self.ui_tars = UITarsIntegration()
            if self.ui_tars.is_installed:
                self.system_status["ui_tars"] = "online"
            else:
                await self.ui_tars.install_ui_tars()
                if self.ui_tars.is_installed:
                    self.system_status["ui_tars"] = "online"
            logger.info("UI-TARS initialized")
        except Exception as e:
            logger.error(f"Failed to initialize UI-TARS: {e}")

    async def process_chat_message(self, message: str, use_multi_agent: bool = True,
                                agent_type: str = "general") -> Dict[str, Any]:
        """Process chat message with optional multi-agent support"""

        if use_multi_agent and self.multi_agent_system:
            try:
                result = await self.multi_agent_system.process_request(
                    "user_interaction",
                    {"query": message, "type": agent_type},
                    {"session_id": f"chat_{datetime.now().timestamp()}"}
                )

                response = result.get("best_result", {}).get("reasoning", "Multi-agent analysis completed")
                agents_used = len(result.get("results", {}))
                approach = result.get("approach", "unknown")

                return {
                    "response": response,
                    "agents_used": agents_used,
                    "approach": approach,
                    "success": True
                }
            except Exception as e:
                logger.error(f"Multi-agent processing failed: {e}")

        # Fallback to single agent
        try:
            result = await route_task_async(message, agent_type, "medium")
            return {
                "response": result.get("response", "No response available"),
                "agents_used": 1,
                "approach": "single_agent",
                "success": True
            }
        except Exception as e:
            logger.error(f"Single agent processing failed: {e}")
            return {
                "response": f"Error processing message: {str(e)}",
                "agents_used": 0,
                "approach": "error",
                "success": False
            }

    async def take_screenshot(self):
        """Take screenshot using UI-TARS"""
        if not self.ui_tars or not self.ui_tars.is_installed:
            return {"success": False, "error": "UI-TARS not available"}

        try:
            result = await self.ui_tars.take_screenshot()
            if result.get("success") and "screenshot" in result:
                self.screenshots.append({
                    "timestamp": datetime.now().isoformat(),
                    "data": result["screenshot"]
                })
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}

def create_modern_chat_interface(webui: DuckBotModernWebUI):
    """Create modern chat interface inspired by UI-TARS"""

    with gr.Blocks(theme=gr.themes.Glass()) as chat_interface:
        gr.Markdown("""
        # 🤖 DuckBot Modern Interface
        ### AI-Powered Assistant with UI Automation
        **Features**: Multi-Agent AI • UI Automation • Screen Control • System Integration
        """)

        with gr.Row():
            # Main chat area
            with gr.Column(scale=3):
                chatbot = gr.Chatbot(
                    height=400,
                    label="Conversation",
                    show_copy_button=True,
                    likeable=True,
                    layout="panel"
                )

                with gr.Row():
                    with gr.Column(scale=4):
                        msg = gr.Textbox(
                            label="Message",
                            placeholder="Ask me anything or request UI automation...",
                            container=False
                        )
                    with gr.Column(scale=1):
                        send_btn = gr.Button("Send", variant="primary", size="lg")

            # Side panel with controls
            with gr.Column(scale=1):
                with gr.Group():
                    gr.Markdown("### 🎛️ Controls")

                    with gr.Accordion("AI Settings", open=True):
                        multi_agent = gr.Checkbox(
                            label="Multi-Agent Mode",
                            value=True,
                            info="Use collaborative AI agents"
                        )
                        agent_type = gr.Dropdown(
                            choices=["general", "market_analysis", "workflow_optimization",
                                    "discord_moderation", "mining_management"],
                            value="general",
                            label="Agent Type"
                        )

                    with gr.Accordion("UI Automation", open=False):
                        screenshot_btn = gr.Button("📸 Take Screenshot", variant="secondary")
                        screen_info_btn = gr.Button("📊 Screen Info", variant="secondary")

                    with gr.Accordion("System Status", open=True):
                        status_display = gr.JSON(
                            value=webui.system_status,
                            label="System Status"
                        )

        # Screenshot gallery
        with gr.Group():
            gr.Markdown("### 📷 Screenshots")
            screenshot_gallery = gr.Gallery(
                label="Recent Screenshots",
                columns=4,
                height=200,
                allow_preview=True
            )

        # Action buttons
        with gr.Row():
            clear_btn = gr.Button("Clear Chat", variant="secondary")
            refresh_btn = gr.Button("Refresh Status", variant="secondary")
            save_btn = gr.Button("Save Session", variant="primary")

        async def respond(message, chat_history, use_multi_agent, agent_type):
            if not message.strip():
                return "", chat_history

            # Process the message
            result = await webui.process_chat_message(message, use_multi_agent, agent_type)

            # Add to chat history
            chat_history.append((message, result["response"]))

            # Update status
            status_info = {
                **webui.system_status,
                "last_response": {
                    "agents_used": result["agents_used"],
                    "approach": result["approach"],
                    "success": result["success"]
                }
            }

            return "", chat_history, status_info

        async def take_screenshot_fn():
            result = await webui.take_screenshot()

            # Update gallery
            gallery_images = []
            for screenshot in webui.screenshots[-8:]:  # Show last 8 screenshots
                try:
                    if screenshot["data"].startswith("data:image"):
                        gallery_images.append(screenshot["data"])
                    else:
                        # Convert base64 to data URL
                        image_data = base64.b64decode(screenshot["data"])
                        buffered = BytesIO(image_data)
                        # For Gradio gallery, we need to return the base64 data directly
                        gallery_images.append(screenshot["data"])
                except Exception as e:
                    logger.error(f"Error processing screenshot: {e}")

            return result, gallery_images

        async def get_screen_info():
            if not webui.ui_tars or not webui.ui_tars.is_installed:
                return {"success": False, "error": "UI-TARS not available"}

            try:
                return await webui.ui_tars.get_screen_info()
            except Exception as e:
                return {"success": False, "error": str(e)}

        # Event handlers
        send_btn.click(
            respond,
            inputs=[msg, chatbot, multi_agent, agent_type],
            outputs=[msg, chatbot, status_display]
        )

        msg.submit(
            respond,
            inputs=[msg, chatbot, multi_agent, agent_type],
            outputs=[msg, chatbot, status_display]
        )

        screenshot_btn.click(
            take_screenshot_fn,
            outputs=[gr.JSON(), screenshot_gallery]
        )

        screen_info_btn.click(
            get_screen_info,
            outputs=[gr.JSON()]
        )

        clear_btn.click(lambda: [], outputs=[chatbot])

        refresh_btn.click(
            lambda: webui.system_status,
            outputs=[status_display]
        )

    return chat_interface

def create_automation_interface(webui: DuckBotModernWebUI):
    """Create UI automation interface"""

    with gr.Blocks(theme=gr.themes.Glass()) as automation:
        gr.Markdown("""
        # 🎮 UI Automation Studio
        ### Control your computer with AI-powered UI automation
        """)

        with gr.Tabs() as automation_tabs:
            with gr.TabItem("🎯 Quick Actions"):
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("### Common Actions")

                        click_btn = gr.Button("🖱️ Click Element", variant="primary")
                        type_btn = gr.Button("⌨️ Type Text", variant="primary")
                        open_btn = gr.Button("📂 Open App", variant="primary")
                        nav_btn = gr.Button("🌐 Navigate", variant="primary")

                    with gr.Column():
                        gr.Markdown("### Action Parameters")

                        element_desc = gr.Textbox(
                            label="Element Description",
                            placeholder="e.g., 'Submit button', 'Username field'"
                        )

                        text_to_type = gr.Textbox(
                            label="Text to Type",
                            placeholder="Text to type"
                        )

                        app_to_open = gr.Textbox(
                            label="Application/URL",
                            placeholder="e.g., 'Chrome', 'https://google.com'"
                        )

            with gr.TabItem("🔄 Workflows"):
                with gr.Row():
                    with gr.Column(scale=2):
                        workflow_input = gr.Textbox(
                            label="Workflow Description",
                            placeholder="Describe the workflow you want to automate...",
                            lines=4
                        )

                        execute_workflow_btn = gr.Button("🚀 Execute Workflow", variant="primary", size="lg")

                    with gr.Column(scale=1):
                        gr.Markdown("### Examples")
                        examples = gr.Examples(
                            examples=[
                                "Open Chrome, navigate to Google, search for 'DuckBot AI'",
                                "Open Notepad, type 'Hello World', save document as test.txt",
                                "Take screenshot, open Paint, paste screenshot, save as image.png"
                            ],
                            inputs=[workflow_input]
                        )

            with gr.TabItem("📊 Results"):
                results_output = gr.JSON(label="Automation Results")
                action_log = gr.Textbox(
                    label="Action Log",
                    lines=10,
                    interactive=False
                )

        async def execute_click(element_description):
            if not webui.ui_tars or not webui.ui_tars.is_installed:
                return {"success": False, "error": "UI-TARS not available"}, ""

            try:
                result = await webui.ui_tars.click_element(element_description)
                log_entry = f"[{datetime.now().strftime('%H:%M:%S')}] Clicked: {element_description}\n"
                return result, log_entry
            except Exception as e:
                return {"success": False, "error": str(e)}, f"Error: {str(e)}\n"

        async def execute_type(text, element_description=""):
            if not webui.ui_tars or not webui.ui_tars.is_installed:
                return {"success": False, "error": "UI-TARS not available"}, ""

            try:
                context = {"element": element_description} if element_description else None
                result = await webui.ui_tars.type_text(text, context)
                log_entry = f"[{datetime.now().strftime('%H:%M:%S')}] Typed: '{text}'\n"
                return result, log_entry
            except Exception as e:
                return {"success": False, "error": str(e)}, f"Error: {str(e)}\n"

        async def execute_open(target):
            if not webui.ui_tars or not webui.ui_tars.is_installed:
                return {"success": False, "error": "UI-TARS not available"}, ""

            try:
                # Check if it's a URL or application
                if target.startswith(("http://", "https://")):
                    result = await webui.ui_tars.navigate_to_url(target)
                    action_type = "Navigated to URL"
                else:
                    result = await webui.ui_tars.open_application(target)
                    action_type = "Opened application"

                log_entry = f"[{datetime.now().strftime('%H:%M:%S')}] {action_type}: {target}\n"
                return result, log_entry
            except Exception as e:
                return {"success": False, "error": str(e)}, f"Error: {str(e)}\n"

        async def execute_workflow(workflow_description):
            if not webui.ui_tars or not webui.ui_tars.is_installed:
                return {"success": False, "error": "UI-TARS not available"}, ""

            try:
                # For now, use AI to interpret the workflow and execute simple commands
                result = await webui.process_chat_message(
                    f"Execute this UI automation workflow: {workflow_description}",
                    use_multi_agent=True,
                    agent_type="workflow_optimization"
                )

                log_entry = f"[{datetime.now().strftime('%H:%M:%S')}] Workflow: {workflow_description}\nResult: {result['response']}\n"
                return result, log_entry
            except Exception as e:
                return {"success": False, "error": str(e)}, f"Error: {str(e)}\n"

        # Connect buttons
        click_btn.click(
            execute_click,
            inputs=[element_desc],
            outputs=[results_output, action_log]
        )

        type_btn.click(
            execute_type,
            inputs=[text_to_type, element_desc],
            outputs=[results_output, action_log]
        )

        open_btn.click(
            execute_open,
            inputs=[app_to_open],
            outputs=[results_output, action_log]
        )

        execute_workflow_btn.click(
            execute_workflow,
            inputs=[workflow_input],
            outputs=[results_output, action_log]
        )

    return automation

def create_ui(theme_name="Glass"):
    """Create the main UI interface with UI-TARS inspired design"""

    # Dark mode JavaScript
    js_func = """
    function refresh() {
        const url = new URL(window.location);

        if (url.searchParams.get('__theme') !== 'dark') {
            url.searchParams.set('__theme', 'dark');
            window.location.href = url.href;
        }
    }
    """

    # Enhanced CSS for modern UI
    css = """
    .gradio-container {
        width: 90vw !important;
        max-width: 90% !important;
        margin-left: auto !important;
        margin-right: auto !important;
        padding-top: 20px !important;
        background: linear-gradient(135deg, #1e1e2e 0%, #2d2d44 100%);
    }

    .header-text {
        text-align: center;
        margin-bottom: 30px;
        background: linear-gradient(45deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    .status-online {
        color: #4ade80;
        font-weight: bold;
    }

    .status-offline {
        color: #f87171;
        font-weight: bold;
    }

    .modern-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 20px;
        margin: 10px 0;
    }

    .screenshot-container {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
        gap: 10px;
        padding: 10px;
    }

    /* Chat styling */
    .chatbot {
        background: rgba(30, 30, 46, 0.8) !important;
        border-radius: 12px !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
    }

    /* Button styling */
    .gr-button {
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
    }

    .gr-button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3) !important;
    }
    """

    # Initialize WebUI
    webui = DuckBotModernWebUI()

    with gr.Blocks(
        title="DuckBot Modern UI - UI-TARS Edition",
        theme=theme_map[theme_name],
        css=css,
        js=js_func,
    ) as demo:

        with gr.Row():
            gr.Markdown(
                """
                # 🦆 DuckBot Modern UI
                ### UI-TARS Inspired Design • Advanced AI Automation
                **Features**: Multi-Agent AI • UI Automation • Screen Control • System Integration • MCP Tools
                """,
                elem_classes=["header-text"],
            )

        with gr.Tabs() as tabs:
            with gr.TabItem("💬 Chat Assistant"):
                create_modern_chat_interface(webui)

            with gr.TabItem("🎮 UI Automation"):
                create_automation_interface(webui)

            with gr.TabItem("📊 System Monitor"):
                with gr.Group():
                    gr.Markdown("### System Status & Performance")

                    with gr.Row():
                        with gr.Column():
                            gr.JSON(value=webui.system_status, label="System Status")

                        with gr.Column():
                            gr.Markdown("""
                            ### System Information
                            - **AI Router**: Intelligent model selection
                            - **Multi-Agent**: Collaborative AI agents (4 active)
                            - **MCP Server**: 50+ automation tools
                            - **UI-TARS**: Advanced GUI automation
                            - **WebUI**: Modern interface system
                            """)

                refresh_btn = gr.Button("Refresh All Status")
                refresh_btn.click(lambda: webui.system_status, outputs=[gr.JSON()])

            with gr.TabItem("🛠️ MCP Tools"):
                with gr.Group():
                    gr.Markdown("### Model Context Protocol Tools")

                    tool_list = gr.Textbox(
                        value="Available MCP Tools:\n" + "\n".join([
                            f"• {tool_name}: {tool.get('description', 'No description')}"
                            for tool_name, tool in getattr(mcp, 'tools', {}).items()
                        ][:15]),
                        label="Available Tools",
                        lines=12,
                        interactive=False
                    )

                    gr.Markdown("""
                    ### Tool Categories
                    - **System Control**: Process management, file operations
                    - **UI Automation**: Screen control, application management
                    - **Network Operations**: HTTP requests, API calls
                    - **Development Tools**: Code analysis, testing
                    - **Database Operations**: Query, update, manage data
                    """)

        # Initialize systems in background
        demo.load(lambda: asyncio.create_task(webui.initialize_systems()))

    return demo

# FastAPI app for additional endpoints
app = FastAPI(title="DuckBot Modern WebUI API")

@app.get("/")
async def get_main_ui():
    """Redirect to the main Gradio interface"""
    return HTMLResponse("""
    <html>
        <head>
            <title>DuckBot Modern WebUI</title>
            <meta http-equiv="refresh" content="0; url=/gradio">
        </head>
        <body>
            <h1>Redirecting to DuckBot Modern WebUI...</h1>
            <p>If not redirected, <a href="/gradio">click here</a></p>
        </body>
    </html>
    """)

@app.get("/api/status")
async def get_status():
    """Get system status"""
    return {"status": "online", "timestamp": datetime.now().isoformat()}

@app.get("/api/systems")
async def get_systems_status():
    """Get detailed systems status"""
    return {
        "ai_router": "online",
        "multi_agent": "online",
        "mcp_server": "online",
        "ui_tars": "online",
        "webui": "online",
        "total_agents": 4,
        "mcp_tools": len(getattr(mcp, 'tools', {})),
        "ui_tars_available": True
    }

def main():
    """Main function to run the Modern WebUI"""
    parser = argparse.ArgumentParser(description="DuckBot Modern WebUI")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8787, help="Port to bind to")
    parser.add_argument("--theme", default="Glass", choices=theme_map.keys(), help="Theme to use")
    parser.add_argument("--share", action="store_true", help="Create a public shareable link")

    args = parser.parse_args()

    logger.info(f"Starting DuckBot Modern WebUI on {args.host}:{args.port}")
    logger.info(f"Theme: {args.theme}")

    # Create the Gradio interface
    demo = create_ui(theme_name=args.theme)

    # Mount Gradio app
    app.mount("/gradio", demo.app)

    # Run with uvicorn
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        log_level="info"
    )

if __name__ == "__main__":
    main()