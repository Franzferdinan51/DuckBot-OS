#!/usr/bin/env python3
"""
DuckBot Phase 2: Advanced Intelligent Window Manager
Predictive window management with machine learning and context awareness
"""

import asyncio
import json
import logging
import time
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib, Gio
import subprocess
import sqlite3
from collections import defaultdict, deque
import pickle

# DuckBot imports
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from duckbot.integration_manager import integration_manager
from duckbot.charm_tools_integration import gum_input, gum_choose, glow_render

logger = logging.getLogger(__name__)

@dataclass
class WindowEvent:
    """Window event data structure"""
    timestamp: float
    event_type: str  # 'created', 'focused', 'moved', 'resized', 'closed'
    window_id: str
    app_name: str
    window_title: str
    position: Tuple[int, int]
    size: Tuple[int, int]
    workspace: int
    context: Dict[str, Any]

@dataclass
class WindowPattern:
    """Learned window pattern"""
    pattern_id: str
    context_fingerprint: str
    layout_config: Dict[str, Any]
    confidence: float
    usage_count: int
    success_rate: float
    last_used: datetime

@dataclass
class UserWorkflow:
    """User workflow pattern"""
    workflow_id: str
    trigger_context: Dict[str, Any]
    application_sequence: List[str]
    layout_preferences: Dict[str, Any]
    frequency: float
    effectiveness_score: float

class IntelligentWindowManager(dbus.service.Object):
    """Phase 2: Advanced AI-powered window management with prediction"""
    
    def __init__(self):
        # Initialize D-Bus service
        DBusGMainLoop(set_as_default=True)
        self.bus = dbus.SessionBus()
        bus_name = dbus.service.BusName('org.duckbot.IntelligentWindowManager', self.bus)
        super().__init__(bus_name, '/org/duckbot/IntelligentWindowManager')
        
        # Intelligence components
        self.pattern_engine = WindowPatternEngine()
        self.prediction_system = WindowPredictionSystem()
        self.learning_engine = WindowLearningEngine()
        self.context_analyzer = ContextAnalyzer()
        
        # Event tracking
        self.window_events = deque(maxlen=10000)  # Rolling window of events
        self.active_patterns = {}
        self.user_workflows = {}
        
        # Performance monitoring
        self.prediction_accuracy = 0.75
        self.layout_satisfaction = 0.8
        
        logger.info("Intelligent Window Manager Phase 2 initialized")
    
    async def initialize(self):
        """Initialize advanced AI systems"""
        try:
            # Initialize integration manager
            await integration_manager.initialize_all()
            
            # Initialize intelligence components
            await self.pattern_engine.initialize()
            await self.prediction_system.initialize()
            await self.learning_engine.initialize()
            await self.context_analyzer.initialize()
            
            # Load existing patterns and workflows
            await self._load_learned_patterns()
            await self._load_user_workflows()
            
            # Start advanced monitoring
            self._start_intelligent_monitoring()
            
            logger.info("Intelligent Window Manager Phase 2 ready")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Intelligent Window Manager: {e}")
            return False
    
    @dbus.service.method('org.duckbot.IntelligentWindowManager', in_signature='', out_signature='b')
    def PredictAndOrganize(self):
        """D-Bus method: Predict optimal layout and organize"""
        try:
            asyncio.create_task(self._predict_and_organize())
            return True
        except Exception as e:
            logger.error(f"PredictAndOrganize failed: {e}")
            return False
    
    @dbus.service.method('org.duckbot.IntelligentWindowManager', in_signature='s', out_signature='s')
    def PredictNextApplication(self, current_context):
        """D-Bus method: Predict next application user will launch"""
        try:
            context = json.loads(current_context)
            prediction = asyncio.create_task(self._predict_next_application(context))
            return json.dumps(prediction)
        except Exception as e:
            logger.error(f"PredictNextApplication failed: {e}")
            return json.dumps({"error": str(e)})
    
    @dbus.service.method('org.duckbot.IntelligentWindowManager', in_signature='', out_signature='s')
    def GetIntelligenceMetrics(self):
        """D-Bus method: Get AI intelligence metrics"""
        try:
            metrics = {
                "prediction_accuracy": self.prediction_accuracy,
                "layout_satisfaction": self.layout_satisfaction,
                "patterns_learned": len(self.active_patterns),
                "workflows_identified": len(self.user_workflows),
                "events_processed": len(self.window_events)
            }
            return json.dumps(metrics)
        except Exception as e:
            logger.error(f"GetIntelligenceMetrics failed: {e}")
            return json.dumps({"error": str(e)})
    
    async def _predict_and_organize(self):
        """Advanced predictive window organization"""
        logger.info("Starting intelligent predictive organization")
        
        # Get current context
        current_context = await self.context_analyzer.analyze_current_context()
        
        # Get current windows
        windows = await self._get_current_windows()
        if not windows:
            return
        
        # Predict optimal layout based on patterns
        predicted_layout = await self.prediction_system.predict_optimal_layout(
            current_context, windows
        )
        
        # Learn from user's current arrangement before changing
        await self.learning_engine.observe_current_arrangement(windows, current_context)
        
        # Apply predicted layout
        success = await self._apply_intelligent_layout(predicted_layout, windows)
        
        # Monitor user satisfaction and adjust
        asyncio.create_task(self._monitor_layout_satisfaction(predicted_layout))
        
        logger.info(f"Intelligent organization complete, success: {success}")
    
    async def _predict_next_application(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Predict next application user is likely to launch"""
        
        # Analyze current context
        context_features = await self.context_analyzer.extract_features(context)
        
        # Find similar historical contexts
        similar_contexts = await self.pattern_engine.find_similar_contexts(context_features)
        
        # Predict next applications
        app_predictions = await self.prediction_system.predict_applications(
            context_features, similar_contexts
        )
        
        return {
            "predictions": app_predictions[:5],  # Top 5 predictions
            "confidence": max([pred["confidence"] for pred in app_predictions], default=0),
            "context_matches": len(similar_contexts)
        }
    
    async def _apply_intelligent_layout(self, layout: Dict[str, Any], windows: List[Dict]) -> bool:
        """Apply AI-predicted layout with smooth animations"""
        try:
            layout_type = layout.get("type", "intelligent_adaptive")
            confidence = layout.get("confidence", 0.5)
            
            # Only apply if confidence is high enough
            if confidence < 0.6:
                logger.info(f"Layout confidence too low ({confidence}), using fallback")
                return await self._apply_fallback_layout(windows)
            
            if layout_type == "contextual_development":
                return await self._apply_contextual_development_layout(windows, layout)
            elif layout_type == "predictive_research":
                return await self._apply_predictive_research_layout(windows, layout)
            elif layout_type == "adaptive_creative":
                return await self._apply_adaptive_creative_layout(windows, layout)
            elif layout_type == "intelligent_communication":
                return await self._apply_intelligent_communication_layout(windows, layout)
            else:
                return await self._apply_adaptive_grid_layout(windows, layout)
                
        except Exception as e:
            logger.error(f"Failed to apply intelligent layout: {e}")
            return False
    
    async def _apply_contextual_development_layout(self, windows: List[Dict], layout: Dict) -> bool:
        """Apply development layout with context awareness"""
        
        # Identify window roles based on content analysis
        code_windows = []
        terminal_windows = []
        browser_windows = []
        other_windows = []
        
        for window in windows:
            app_role = await self._classify_window_role(window)
            if app_role == "code_editor":
                code_windows.append(window)
            elif app_role == "terminal":
                terminal_windows.append(window)
            elif app_role == "browser":
                browser_windows.append(window)
            else:
                other_windows.append(window)
        
        # Apply intelligent development layout
        screen_width = 1920  # TODO: Get actual screen resolution
        screen_height = 1080
        
        if code_windows and terminal_windows:
            # Main editor gets 60% of screen width
            main_editor = code_windows[0]
            await self._animate_window_to_position(
                main_editor, 0, 0, int(screen_width * 0.6), screen_height
            )
            
            # Terminal gets top-right 40%
            main_terminal = terminal_windows[0]
            await self._animate_window_to_position(
                main_terminal, int(screen_width * 0.6), 0, 
                int(screen_width * 0.4), int(screen_height * 0.5)
            )
            
            # Browser gets bottom-right if available
            if browser_windows:
                browser = browser_windows[0]
                await self._animate_window_to_position(
                    browser, int(screen_width * 0.6), int(screen_height * 0.5),
                    int(screen_width * 0.4), int(screen_height * 0.5)
                )
        
        # Learn from this layout application
        await self.learning_engine.record_layout_application(
            "contextual_development", windows, layout
        )
        
        return True
    
    async def _apply_predictive_research_layout(self, windows: List[Dict], layout: Dict) -> bool:
        """Apply research layout with predictive positioning"""
        
        # Create dynamic grid based on window count and content
        num_windows = len(windows)
        
        if num_windows <= 2:
            # Side-by-side for focused research
            for i, window in enumerate(windows):
                x_pos = i * (1920 // 2)
                await self._animate_window_to_position(
                    window, x_pos, 0, 1920 // 2, 1080
                )
        elif num_windows <= 4:
            # Intelligent 2x2 grid with size optimization
            positions = [
                (0, 0, 960, 540),
                (960, 0, 960, 540),
                (0, 540, 960, 540),
                (960, 540, 960, 540)
            ]
            
            # Prioritize important windows (browsers, documents) for larger spaces
            prioritized_windows = await self._prioritize_windows_for_research(windows)
            
            for i, window in enumerate(prioritized_windows[:4]):
                x, y, w, h = positions[i]
                await self._animate_window_to_position(window, x, y, w, h)
        else:
            # Dynamic grid for many windows
            cols = min(3, max(2, int(np.sqrt(num_windows))))
            rows = (num_windows + cols - 1) // cols
            
            cell_width = 1920 // cols
            cell_height = 1080 // rows
            
            for i, window in enumerate(windows):
                row = i // cols
                col = i % cols
                x = col * cell_width
                y = row * cell_height
                await self._animate_window_to_position(
                    window, x, y, cell_width, cell_height
                )
        
        return True
    
    async def _apply_adaptive_creative_layout(self, windows: List[Dict], layout: Dict) -> bool:
        """Apply creative workflow layout with adaptive sizing"""
        
        # Identify creative applications
        primary_creative = []
        reference_windows = []
        tool_windows = []
        
        for window in windows:
            app_type = await self._classify_creative_application(window)
            if app_type == "primary_creative":
                primary_creative.append(window)
            elif app_type == "reference":
                reference_windows.append(window)
            else:
                tool_windows.append(window)
        
        # Primary creative app gets main focus
        if primary_creative:
            main_app = primary_creative[0]
            await self._animate_window_to_position(
                main_app, 0, 0, 1280, 1080  # 2/3 of screen
            )
            
            # Reference materials get side panel
            if reference_windows:
                ref_height = 1080 // len(reference_windows)
                for i, ref_window in enumerate(reference_windows):
                    y_pos = i * ref_height
                    await self._animate_window_to_position(
                        ref_window, 1280, y_pos, 640, ref_height
                    )
            
            # Tool windows get small floating positions
            for i, tool_window in enumerate(tool_windows[:2]):
                x_pos = 1280 + (i * 100)
                y_pos = 900 + (i * 50)
                await self._animate_window_to_position(
                    tool_window, x_pos, y_pos, 400, 180
                )
        
        return True
    
    async def _animate_window_to_position(self, window: Dict, x: int, y: int, w: int, h: int):
        """Animate window to position with smooth transitions"""
        
        window_id = window["id"]
        
        # Get current position
        current_x, current_y = window["x"], window["y"]
        current_w, current_h = window["width"], window["height"]
        
        # Calculate animation steps
        steps = 20
        duration = 0.3  # 300ms total animation
        
        for step in range(steps + 1):
            progress = step / steps
            # Easing function for smooth animation
            eased_progress = self._ease_in_out_cubic(progress)
            
            # Interpolate position and size
            new_x = int(current_x + (x - current_x) * eased_progress)
            new_y = int(current_y + (y - current_y) * eased_progress)
            new_w = int(current_w + (w - current_w) * eased_progress)
            new_h = int(current_h + (h - current_h) * eased_progress)
            
            # Apply position
            subprocess.run([
                "wmctrl", "-i", "-r", window_id, "-e", 
                f"0,{new_x},{new_y},{new_w},{new_h}"
            ], capture_output=True)
            
            if step < steps:
                await asyncio.sleep(duration / steps)
    
    def _ease_in_out_cubic(self, t: float) -> float:
        """Cubic easing function for smooth animations"""
        if t < 0.5:
            return 4 * t * t * t
        else:
            return 1 - pow(-2 * t + 2, 3) / 2
    
    async def _classify_window_role(self, window: Dict) -> str:
        """Classify window role for intelligent layout"""
        
        app_name = window.get("title", "").lower()
        
        # Code editors
        if any(editor in app_name for editor in [
            "code", "vscode", "vim", "emacs", "sublime", "atom", "idea"
        ]):
            return "code_editor"
        
        # Terminals
        if any(term in app_name for term in [
            "terminal", "konsole", "xterm", "gnome-terminal", "bash", "zsh"
        ]):
            return "terminal"
        
        # Browsers
        if any(browser in app_name for browser in [
            "firefox", "chrome", "chromium", "safari", "edge"
        ]):
            return "browser"
        
        # Documentation
        if any(doc in app_name for doc in [
            "documentation", "manual", "readme", "wiki"
        ]):
            return "documentation"
        
        return "other"
    
    async def _classify_creative_application(self, window: Dict) -> str:
        """Classify creative application for specialized layout"""
        
        app_name = window.get("title", "").lower()
        
        # Primary creative applications
        if any(app in app_name for app in [
            "photoshop", "gimp", "krita", "inkscape", "illustrator", 
            "blender", "maya", "cinema4d", "figma"
        ]):
            return "primary_creative"
        
        # Reference materials
        if any(ref in app_name for ref in [
            "pinterest", "artstation", "behance", "dribbble", "reference"
        ]):
            return "reference"
        
        # Tool windows
        if any(tool in app_name for tool in [
            "color", "palette", "brush", "layer", "property", "inspector"
        ]):
            return "tool"
        
        return "other"
    
    async def _prioritize_windows_for_research(self, windows: List[Dict]) -> List[Dict]:
        """Prioritize windows for research layout"""
        
        priority_scores = []
        
        for window in windows:
            score = 0
            title = window.get("title", "").lower()
            
            # Browsers get high priority
            if any(browser in title for browser in ["firefox", "chrome", "browser"]):
                score += 10
            
            # PDF viewers and documents
            if any(doc in title for doc in ["pdf", "document", "paper", "article"]):
                score += 8
            
            # Note-taking apps
            if any(note in title for note in ["notes", "notion", "obsidian", "roam"]):
                score += 7
            
            # Text editors with research content
            if any(editor in title for editor in ["editor", "text", "write"]):
                score += 5
            
            priority_scores.append((score, window))
        
        # Sort by priority score
        priority_scores.sort(key=lambda x: x[0], reverse=True)
        
        return [window for score, window in priority_scores]
    
    async def _monitor_layout_satisfaction(self, applied_layout: Dict):
        """Monitor user satisfaction with applied layout"""
        
        # Wait for user to interact with the layout
        await asyncio.sleep(10)
        
        # Check for immediate corrections (user manually moving windows)
        corrections = await self._detect_user_corrections()
        
        # Calculate satisfaction score
        satisfaction_score = 1.0 - (len(corrections) * 0.2)
        satisfaction_score = max(0.0, min(1.0, satisfaction_score))
        
        # Update learning engine
        await self.learning_engine.record_layout_satisfaction(
            applied_layout, satisfaction_score, corrections
        )
        
        # Update global satisfaction metric
        self.layout_satisfaction = (self.layout_satisfaction * 0.9 + satisfaction_score * 0.1)
        
        logger.info(f"Layout satisfaction: {satisfaction_score:.2f}")
    
    async def _detect_user_corrections(self) -> List[Dict]:
        """Detect if user manually corrected window positions"""
        
        corrections = []
        
        # Monitor window events for manual moves/resizes
        recent_events = [event for event in self.window_events 
                        if time.time() - event.timestamp < 30]
        
        manual_events = [event for event in recent_events 
                        if event.event_type in ['moved', 'resized']]
        
        for event in manual_events:
            corrections.append({
                "window_id": event.window_id,
                "correction_type": event.event_type,
                "timestamp": event.timestamp
            })
        
        return corrections
    
    def _start_intelligent_monitoring(self):
        """Start advanced window event monitoring"""
        
        def monitor_and_learn():
            """Continuous monitoring and learning"""
            
            # This would integrate with X11/Wayland events
            # For now, simulate with periodic checks
            
            return True  # Continue monitoring
        
        # Check every 2 seconds for learning opportunities
        GLib.timeout_add_seconds(2, monitor_and_learn)
    
    async def _load_learned_patterns(self):
        """Load previously learned patterns"""
        try:
            # Load from database or file
            # This is a placeholder for actual implementation
            self.active_patterns = {}
            logger.info("Loaded learned window patterns")
        except Exception as e:
            logger.error(f"Failed to load patterns: {e}")
    
    async def _load_user_workflows(self):
        """Load identified user workflows"""
        try:
            # Load from database or file
            # This is a placeholder for actual implementation
            self.user_workflows = {}
            logger.info("Loaded user workflows")
        except Exception as e:
            logger.error(f"Failed to load workflows: {e}")

class WindowPatternEngine:
    """Engine for detecting and managing window patterns"""
    
    def __init__(self):
        self.patterns_db = {}
        
    async def initialize(self):
        logger.info("Window Pattern Engine initialized")
        
    async def find_similar_contexts(self, features: Dict) -> List[Dict]:
        """Find similar historical contexts"""
        # Implement pattern matching algorithm
        return []

class WindowPredictionSystem:
    """System for predicting optimal window layouts"""
    
    def __init__(self):
        self.prediction_model = None
        
    async def initialize(self):
        logger.info("Window Prediction System initialized")
        
    async def predict_optimal_layout(self, context: Dict, windows: List) -> Dict:
        """Predict optimal layout configuration"""
        
        # Analyze context and windows to predict best layout
        num_windows = len(windows)
        
        if num_windows <= 2:
            return {
                "type": "side_by_side",
                "confidence": 0.85
            }
        elif num_windows <= 4:
            return {
                "type": "intelligent_grid",
                "confidence": 0.75
            }
        else:
            return {
                "type": "adaptive_grid", 
                "confidence": 0.65
            }
    
    async def predict_applications(self, features: Dict, contexts: List) -> List[Dict]:
        """Predict next applications to launch"""
        
        # Mock predictions - would use ML model in real implementation
        return [
            {"app": "firefox", "confidence": 0.8},
            {"app": "code", "confidence": 0.7},
            {"app": "terminal", "confidence": 0.6}
        ]

class WindowLearningEngine:
    """Engine for learning from user behavior"""
    
    def __init__(self):
        self.learning_data = []
        
    async def initialize(self):
        logger.info("Window Learning Engine initialized")
        
    async def observe_current_arrangement(self, windows: List, context: Dict):
        """Learn from current window arrangement"""
        pass
        
    async def record_layout_application(self, layout_type: str, windows: List, layout: Dict):
        """Record layout application for learning"""
        pass
        
    async def record_layout_satisfaction(self, layout: Dict, score: float, corrections: List):
        """Record user satisfaction with layout"""
        pass

class ContextAnalyzer:
    """Analyzer for understanding current context"""
    
    def __init__(self):
        pass
        
    async def initialize(self):
        logger.info("Context Analyzer initialized")
        
    async def analyze_current_context(self) -> Dict:
        """Analyze current desktop context"""
        
        return {
            "time_of_day": datetime.now().hour,
            "day_of_week": datetime.now().weekday(),
            "active_apps": [],
            "recent_activity": [],
            "workspace": 0
        }
        
    async def extract_features(self, context: Dict) -> Dict:
        """Extract features from context for ML"""
        
        return {
            "temporal_features": [context.get("time_of_day", 0)],
            "app_features": [],
            "activity_features": []
        }

async def main():
    """Main service entry point"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create and initialize the Intelligent Window Manager
    window_manager = IntelligentWindowManager()
    await window_manager.initialize()
    
    # Start the main loop
    loop = GLib.MainLoop()
    
    try:
        logger.info("DuckBot Intelligent Window Manager Phase 2 running")
        loop.run()
    except KeyboardInterrupt:
        logger.info("Service stopped by user")
    except Exception as e:
        logger.error(f"Service error: {e}")

if __name__ == "__main__":
    asyncio.run(main())