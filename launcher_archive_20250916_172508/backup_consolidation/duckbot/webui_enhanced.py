#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DuckBot Enhanced WebUI - Old Style with Modern Enhancements
Based on the original Gradio WebUI but with all new features integrated
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

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from duckbot.ai_router_gpt import route_task_async
from multi_agent_activator import get_multi_agent_system
from duckbot.integrations.mcp_server import mcp

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

class DuckBotWebUI:
    """Enhanced WebUI with original styling and modern features"""

    def __init__(self):
        self.multi_agent_system = None
        self.chat_history = []
        self.system_status = {
            "ai_router": "offline",
            "multi_agent": "offline",
            "mcp_server": "offline",
            "webui": "online"
        }

    async def initialize_systems(self):
        """Initialize all backend systems"""
        try:
            # Initialize Multi-Agent System
            self.multi_agent_system = await get_multi_agent_system()
            self.system_status["multi_agent"] = "online"
            logger.info("Multi-Agent System initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Multi-Agent System: {e}")

        try:
            # Test AI Router
            result = await route_task_async("test", "general", "low")
            if result and "response" in result:
                self.system_status["ai_router"] = "online"
            logger.info("AI Router tested")
        except Exception as e:
            logger.error(f"Failed to initialize AI Router: {e}")

        try:
            # Test MCP Server
            if hasattr(mcp, 'tools'):
                self.system_status["mcp_server"] = "online"
            logger.info("MCP Server tested")
        except Exception as e:
            logger.error(f"Failed to initialize MCP Server: {e}")

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

def create_chat_interface(webui: DuckBotWebUI):
    """Create the main chat interface"""

    with gr.Blocks(theme=gr.themes.Soft()) as chat_interface:
        gr.Markdown("""
        # 🤖 DuckBot Chat Interface
        ### AI-powered assistant with multi-agent capabilities
        """)

        with gr.Row():
            with gr.Column(scale=3):
                chatbot = gr.Chatbot(height=500, label="Chat History")
                msg = gr.Textbox(label="Message", placeholder="Type your message here...")

            with gr.Column(scale=1):
                with gr.Group():
                    gr.Markdown("### Settings")
                    multi_agent = gr.Checkbox(
                        label="Use Multi-Agent System",
                        value=True,
                        info="Enable collaborative AI agents"
                    )
                    agent_type = gr.Dropdown(
                        choices=["general", "market_analysis", "workflow_optimization",
                                "discord_moderation", "mining_management"],
                        value="general",
                        label="Agent Type"
                    )
                    status_display = gr.JSON(
                        value=webui.system_status,
                        label="System Status"
                    )

        with gr.Row():
            submit = gr.Button("Send", variant="primary")
            clear = gr.Button("Clear Chat")

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

        submit.click(
            respond,
            inputs=[msg, chatbot, multi_agent, agent_type],
            outputs=[msg, chatbot, status_display]
        )

        msg.submit(
            respond,
            inputs=[msg, chatbot, multi_agent, agent_type],
            outputs=[msg, chatbot, status_display]
        )

        clear.click(lambda: [], outputs=[chatbot])

    return chat_interface

def create_system_monitor(webui: DuckBotWebUI):
    """Create system monitoring interface"""

    with gr.Blocks(theme=gr.themes.Soft()) as monitor:
        gr.Markdown("""
        # 📊 System Monitor
        ### Real-time system status and performance
        """)

        with gr.Row():
            with gr.Column():
                gr.JSON(value=webui.system_status, label="System Status")

            with gr.Column():
                gr.Markdown("""
                ### Service Information
                - **AI Router**: Intelligent model selection across providers
                - **Multi-Agent System**: Collaborative AI agents
                - **MCP Server**: External tool integration (50+ tools)
                - **WebUI**: User interface and chat system
                """)

        refresh_btn = gr.Button("Refresh Status")

        def refresh_status():
            return webui.system_status

        refresh_btn.click(refresh_status, outputs=[gr.JSON()])

    return monitor

def create_tools_interface(webui: DuckBotWebUI):
    """Create MCP tools interface"""

    with gr.Blocks(theme=gr.themes.Soft()) as tools:
        gr.Markdown("""
        # 🛠️ MCP Tools
        ### Model Context Protocol tools for system control
        """)

        with gr.Row():
            with gr.Column():
                tool_list = gr.Textbox(
                    value="Available MCP Tools:\n" + "\n".join([
                        f"• {tool_name}: {tool.get('description', 'No description')}"
                        for tool_name, tool in getattr(mcp, 'tools', {}).items()
                    ][:10]),
                    label="Available Tools",
                    lines=10,
                    interactive=False
                )

            with gr.Column():
                gr.Markdown("""
                ### Tool Categories
                - **System Control**: Process management, file operations
                - **Network Operations**: HTTP requests, API calls
                - **Development Tools**: Code analysis, testing
                - **Database Operations**: Query, update, manage data
                - **AI Integration**: Model management, processing
                """)

    return tools

def create_ui(theme_name="Ocean"):
    """Create the main UI interface"""

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

    # Custom CSS for enhanced styling
    css = """
    .gradio-container {
        width: 85vw !important;
        max-width: 85% !important;
        margin-left: auto !important;
        margin-right: auto !important;
        padding-top: 20px !important;
    }

    .header-text {
        text-align: center;
        margin-bottom: 30px;
    }

    .status-online {
        color: #28a745;
        font-weight: bold;
    }

    .status-offline {
        color: #dc3545;
        font-weight: bold;
    }

    .agent-info {
        background: #f8f9fa;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
    }
    """

    # Initialize WebUI
    webui = DuckBotWebUI()

    with gr.Blocks(
        title="DuckBot Enhanced WebUI",
        theme=theme_map[theme_name],
        css=css,
        js=js_func,
    ) as demo:

        with gr.Row():
            gr.Markdown(
                """
                # 🦆 DuckBot v4.2 Enhanced WebUI
                ### Complete AI-powered ecosystem with multi-agent support
                **Features**: AI Router • Multi-Agent System • MCP Server • Real-time Chat
                """,
                elem_classes=["header-text"],
            )

        with gr.Tabs() as tabs:
            with gr.TabItem("💬 Chat"):
                create_chat_interface(webui)

            with gr.TabItem("📊 System Monitor"):
                create_system_monitor(webui)

            with gr.TabItem("🛠️ MCP Tools"):
                create_tools_interface(webui)

            with gr.TabItem("⚙️ Settings"):
                with gr.Group():
                    gr.Markdown("### System Settings")

                    with gr.Row():
                        theme_selector = gr.Dropdown(
                            choices=list(theme_map.keys()),
                            value=theme_name,
                            label="Theme"
                        )

                        refresh_interval = gr.Slider(
                            minimum=5,
                            maximum=60,
                            value=15,
                            step=5,
                            label="Status Refresh (seconds)"
                        )

                    gr.Markdown("### Connection Settings")
                    gr.Textbox(
                        value="http://localhost:8787",
                        label="WebUI URL",
                        interactive=False
                    )
                    gr.Textbox(
                        value="http://localhost:8789",
                        label="AI Manager URL",
                        interactive=False
                    )

        # Initialize systems in background
        demo.load(lambda: asyncio.create_task(webui.initialize_systems()))

    return demo

# FastAPI app for additional endpoints
app = FastAPI(title="DuckBot Enhanced WebUI API")

@app.get("/")
async def get_main_ui():
    """Redirect to the main Gradio interface"""
    return HTMLResponse("""
    <html>
        <head>
            <title>DuckBot Enhanced WebUI</title>
            <meta http-equiv="refresh" content="0; url=/gradio">
        </head>
        <body>
            <h1>Redirecting to DuckBot WebUI...</h1>
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
        "webui": "online",
        "total_agents": 4,
        "mcp_tools": len(getattr(mcp, 'tools', {}))
    }

def main():
    """Main function to run the Enhanced WebUI"""
    parser = argparse.ArgumentParser(description="DuckBot Enhanced WebUI")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8787, help="Port to bind to")
    parser.add_argument("--theme", default="Ocean", choices=theme_map.keys(), help="Theme to use")
    parser.add_argument("--share", action="store_true", help="Create a public shareable link")

    args = parser.parse_args()

    logger.info(f"Starting DuckBot Enhanced WebUI on {args.host}:{args.port}")
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