#!/usr/bin/env python3
"""
DuckBot AI Window Manager
Intelligent window management service for DuckBot Desktop Environment
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, Tuple
import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib, Gio
import subprocess

# DuckBot imports
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from duckbot.integration_manager import integration_manager
from duckbot.charm_tools_integration import gum_input, gum_choose

logger = logging.getLogger(__name__)

class AIWindowManager(dbus.service.Object):
    """AI-powered window management service"""
    
    def __init__(self):
        # Initialize D-Bus service
        DBusGMainLoop(set_as_default=True)
        self.bus = dbus.SessionBus()
        bus_name = dbus.service.BusName('org.duckbot.WindowManager', self.bus)
        super().__init__(bus_name, '/org/duckbot/WindowManager')
        
        # AI and memory integration
        self.ai_service = None
        self.memento = None
        self.learning_mode = False
        
        # Window tracking
        self.window_history = []
        self.workspace_patterns = {}
        self.user_preferences = {}
        
        # Layout intelligence
        self.layout_engine = IntelligentLayoutEngine()
        
        logger.info("DuckBot AI Window Manager started")
    
    async def initialize(self):
        """Initialize AI services and integrations"""
        try:
            # Connect to DuckBot integration manager
            await integration_manager.initialize_all()
            
            if integration_manager.is_integration_available("memento"):
                self.memento = integration_manager.memento_integration
                logger.info("Memento memory integration active")
            
            # Load user preferences from memory
            await self._load_preferences()
            
            # Start monitoring window events
            self._start_window_monitoring()
            
            logger.info("AI Window Manager initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize AI Window Manager: {e}")
            return False
    
    @dbus.service.method('org.duckbot.WindowManager', in_signature='', out_signature='b')
    def OrganizeWindows(self):
        """D-Bus method: Organize windows intelligently"""
        try:
            asyncio.create_task(self._organize_windows_ai())
            return True
        except Exception as e:
            logger.error(f"OrganizeWindows failed: {e}")
            return False
    
    @dbus.service.method('org.duckbot.WindowManager', in_signature='s', out_signature='b')
    def CreateWorkspace(self, workspace_type):
        """D-Bus method: Create specialized workspace"""
        try:
            asyncio.create_task(self._create_ai_workspace(workspace_type))
            return True
        except Exception as e:
            logger.error(f"CreateWorkspace failed: {e}")
            return False
    
    @dbus.service.method('org.duckbot.WindowManager', in_signature='s', out_signature='s')
    def AnalyzeContext(self, context_data):
        """D-Bus method: Analyze current window context"""
        try:
            result = asyncio.create_task(self._analyze_window_context(context_data))
            return json.dumps(result)
        except Exception as e:
            logger.error(f"AnalyzeContext failed: {e}")
            return json.dumps({"error": str(e)})
    
    async def _organize_windows_ai(self):
        """AI-powered window organization"""
        logger.info("Starting AI window organization")
        
        # Get current windows
        windows = await self._get_current_windows()
        if not windows:
            return
        
        # Analyze window context and relationships
        context = await self._analyze_window_relationships(windows)
        
        # Use AI to determine optimal layout
        layout_suggestion = await self._get_ai_layout_suggestion(context)
        
        # Apply the suggested layout
        await self._apply_layout(layout_suggestion, windows)
        
        # Learn from this organization for future improvements
        if self.memento:
            await self._store_organization_pattern(context, layout_suggestion)
        
        logger.info("AI window organization complete")
    
    async def _create_ai_workspace(self, workspace_type: str):
        """Create AI-optimized workspace for specific tasks"""
        logger.info(f"Creating AI workspace: {workspace_type}")
        
        workspace_templates = {
            "development": {
                "applications": ["code", "gnome-terminal", "firefox"],
                "layout": "development_optimized",
                "ai_agents": ["code-assistant", "documentation"]
            },
            "research": {
                "applications": ["firefox", "gnome-text-editor", "evince"],
                "layout": "research_grid", 
                "ai_agents": ["research-assistant", "summarizer"]
            },
            "creative": {
                "applications": ["gimp", "inkscape", "blender"],
                "layout": "creative_suite",
                "ai_agents": ["creative-assistant", "asset-manager"]
            },
            "communication": {
                "applications": ["thunderbird", "slack", "zoom"],
                "layout": "communication_hub",
                "ai_agents": ["meeting-assistant", "email-ai"]
            }
        }
        
        if workspace_type not in workspace_templates:
            # Use AI to create custom workspace
            workspace_config = await self._ai_create_custom_workspace(workspace_type)
        else:
            workspace_config = workspace_templates[workspace_type]
        
        # Create new workspace
        subprocess.run(["wmctrl", "-n", "4"])  # Ensure we have enough workspaces
        
        # Launch applications
        for app in workspace_config["applications"]:
            subprocess.Popen([app])
            await asyncio.sleep(1)  # Stagger launches
        
        # Apply specialized layout
        await asyncio.sleep(3)  # Wait for apps to fully load
        await self._apply_workspace_layout(workspace_config["layout"])
        
        # Deploy AI agents if available
        if integration_manager.is_integration_available("archon"):
            for agent in workspace_config.get("ai_agents", []):
                await self._deploy_workspace_agent(agent)
        
        logger.info(f"AI workspace '{workspace_type}' created successfully")
    
    async def _get_current_windows(self) -> List[Dict]:
        """Get information about current windows"""
        try:
            result = subprocess.run(["wmctrl", "-l", "-G"], capture_output=True, text=True)
            windows = []
            
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = line.split(None, 4)
                    if len(parts) >= 5:
                        windows.append({
                            "id": parts[0],
                            "desktop": int(parts[1]),
                            "x": int(parts[2]),
                            "y": int(parts[3]),
                            "width": int(parts[4]) if len(parts) > 4 else 0,
                            "height": int(parts[5]) if len(parts) > 5 else 0,
                            "title": parts[-1] if len(parts) > 4 else "Unknown"
                        })
            
            return windows
            
        except Exception as e:
            logger.error(f"Failed to get window list: {e}")
            return []
    
    async def _analyze_window_relationships(self, windows: List[Dict]) -> Dict:
        """Analyze relationships between windows using AI"""
        context = {
            "window_count": len(windows),
            "applications": {},
            "screen_usage": {},
            "patterns": []
        }
        
        # Group by application
        for window in windows:
            app_name = self._extract_app_name(window["title"])
            if app_name not in context["applications"]:
                context["applications"][app_name] = []
            context["applications"][app_name].append(window)
        
        # Analyze screen usage patterns
        total_screen_area = 1920 * 1080  # TODO: Get actual screen resolution
        for window in windows:
            area = window["width"] * window["height"]
            usage = area / total_screen_area if total_screen_area > 0 else 0
            context["screen_usage"][window["id"]] = usage
        
        # Use AI to identify patterns
        if self.memento:
            similar_contexts = await self._find_similar_contexts(context)
            context["similar_patterns"] = similar_contexts
        
        return context
    
    async def _get_ai_layout_suggestion(self, context: Dict) -> Dict:
        """Get AI-powered layout suggestions"""
        
        # Use integration manager to get AI suggestion
        if integration_manager.is_integration_available("memento"):
            # Use Memento to find similar layouts that worked well
            suggestion = await integration_manager.execute_enhanced_task(
                f"Suggest optimal window layout for {context['window_count']} windows with applications: {list(context['applications'].keys())}"
            )
            
            if suggestion.get("success"):
                return suggestion["result"]
        
        # Fallback to rule-based suggestions
        return self.layout_engine.suggest_layout(context)
    
    async def _apply_layout(self, layout_suggestion: Dict, windows: List[Dict]):
        """Apply the AI-suggested window layout"""
        try:
            layout_type = layout_suggestion.get("type", "auto_grid")
            
            if layout_type == "development_split":
                await self._apply_development_layout(windows)
            elif layout_type == "research_grid":
                await self._apply_research_layout(windows)
            elif layout_type == "side_by_side":
                await self._apply_side_by_side_layout(windows)
            else:
                await self._apply_auto_grid_layout(windows)
                
            logger.info(f"Applied layout: {layout_type}")
            
        except Exception as e:
            logger.error(f"Failed to apply layout: {e}")
    
    async def _apply_development_layout(self, windows: List[Dict]):
        """Apply development-optimized layout"""
        if len(windows) == 2:
            # Editor on left, terminal on right
            subprocess.run(["wmctrl", "-i", "-r", windows[0]["id"], "-e", "0,0,0,960,1080"])
            subprocess.run(["wmctrl", "-i", "-r", windows[1]["id"], "-e", "0,960,0,960,1080"])
        elif len(windows) == 3:
            # Editor on left, terminal top-right, browser bottom-right
            subprocess.run(["wmctrl", "-i", "-r", windows[0]["id"], "-e", "0,0,0,1280,1080"])
            subprocess.run(["wmctrl", "-i", "-r", windows[1]["id"], "-e", "0,1280,0,640,540"])
            subprocess.run(["wmctrl", "-i", "-r", windows[2]["id"], "-e", "0,1280,540,640,540"])
    
    async def _apply_research_layout(self, windows: List[Dict]):
        """Apply research-optimized grid layout"""
        # Create 2x2 grid for research windows
        positions = [
            "0,0,0,960,540",      # Top-left
            "0,960,0,960,540",    # Top-right  
            "0,0,540,960,540",    # Bottom-left
            "0,960,540,960,540"   # Bottom-right
        ]
        
        for i, window in enumerate(windows[:4]):
            if i < len(positions):
                subprocess.run(["wmctrl", "-i", "-r", window["id"], "-e", positions[i]])
    
    async def _apply_side_by_side_layout(self, windows: List[Dict]):
        """Apply simple side-by-side layout"""
        screen_width = 1920  # TODO: Get actual screen width
        window_width = screen_width // len(windows)
        
        for i, window in enumerate(windows):
            x_pos = i * window_width
            subprocess.run(["wmctrl", "-i", "-r", window["id"], "-e", f"0,{x_pos},0,{window_width},1080"])
    
    async def _apply_auto_grid_layout(self, windows: List[Dict]):
        """Apply automatic grid layout"""
        import math
        
        num_windows = len(windows)
        cols = math.ceil(math.sqrt(num_windows))
        rows = math.ceil(num_windows / cols)
        
        screen_width = 1920   # TODO: Get actual screen dimensions
        screen_height = 1080
        
        window_width = screen_width // cols
        window_height = screen_height // rows
        
        for i, window in enumerate(windows):
            row = i // cols
            col = i % cols
            
            x_pos = col * window_width
            y_pos = row * window_height
            
            subprocess.run(["wmctrl", "-i", "-r", window["id"], "-e", 
                          f"0,{x_pos},{y_pos},{window_width},{window_height}"])
    
    def _extract_app_name(self, window_title: str) -> str:
        """Extract application name from window title"""
        # Simple heuristics to identify applications
        if "Visual Studio Code" in window_title or "VSCode" in window_title:
            return "code"
        elif "Terminal" in window_title or "bash" in window_title:
            return "terminal"
        elif "Firefox" in window_title or "Mozilla" in window_title:
            return "browser"
        elif "Files" in window_title or "Nautilus" in window_title:
            return "files"
        else:
            return window_title.split("-")[-1].strip().lower()
    
    async def _load_preferences(self):
        """Load user window management preferences from memory"""
        if self.memento:
            try:
                prefs = await integration_manager.execute_enhanced_task(
                    "Load my window management preferences and patterns"
                )
                if prefs.get("success"):
                    self.user_preferences = prefs["result"]
                    logger.info("Loaded user window preferences from memory")
            except Exception as e:
                logger.error(f"Failed to load preferences: {e}")
    
    def _start_window_monitoring(self):
        """Start monitoring window events for learning"""
        # This would be implemented to monitor X11 or Wayland events
        # For now, we'll use a simple timer to periodically check windows
        
        def monitor_windows():
            # Periodic window monitoring for learning
            return True  # Continue monitoring
        
        GLib.timeout_add_seconds(5, monitor_windows)

class IntelligentLayoutEngine:
    """AI-powered layout suggestion engine"""
    
    def suggest_layout(self, context: Dict) -> Dict:
        """Suggest optimal layout based on context"""
        num_windows = context["window_count"]
        apps = list(context["applications"].keys())
        
        # Rule-based layout suggestions
        if num_windows == 1:
            return {"type": "maximized", "confidence": 0.9}
        
        elif num_windows == 2:
            if "code" in apps and "terminal" in apps:
                return {"type": "development_split", "confidence": 0.95}
            else:
                return {"type": "side_by_side", "confidence": 0.8}
        
        elif num_windows <= 4 and any("research" in app or "browser" in app for app in apps):
            return {"type": "research_grid", "confidence": 0.85}
        
        else:
            return {"type": "auto_grid", "confidence": 0.7}

async def main():
    """Main service entry point"""
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create and initialize the AI Window Manager
    window_manager = AIWindowManager()
    await window_manager.initialize()
    
    # Start the main loop
    loop = GLib.MainLoop()
    
    try:
        logger.info("DuckBot AI Window Manager service running")
        loop.run()
    except KeyboardInterrupt:
        logger.info("Service stopped by user")
    except Exception as e:
        logger.error(f"Service error: {e}")

if __name__ == "__main__":
    asyncio.run(main())