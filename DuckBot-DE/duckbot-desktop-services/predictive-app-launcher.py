#!/usr/bin/env python3
"""
DuckBot Phase 2: Predictive Application Launcher
Integrated with ALL DuckBot features for intelligent app prediction and launching
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
import os
from pathlib import Path

# DuckBot Complete Integration
import sys
sys.path.append('/usr/share/duckbot-de')
from duckbot.integration_manager import integration_manager
from duckbot.charm_tools_integration import (
    gum_input, gum_choose, gum_confirm, glow_render,
    ask_ai, store_data, load_data, get_charm_status
)
from duckbot.memento_integration import execute_memento_task, get_memento_memory_stats
from duckbot.bytebot_integration import execute_natural_language_task
from duckbot.archon_integration import create_archon_task
from duckbot.wsl_integration import execute_wsl_command
from duckbot.chromium_integration import chromium_integration
from duckbot.ai_router_gpt import AIRouter
from duckbot.cost_tracker import CostTracker

logger = logging.getLogger(__name__)

@dataclass
class AppUsageEvent:
    """Application usage event"""
    timestamp: float
    app_name: str
    launch_method: str  # 'manual', 'predicted', 'voice', 'ai_suggested'
    context: Dict[str, Any]
    duration: Optional[float] = None
    satisfaction_score: Optional[float] = None

@dataclass
class ContextPattern:
    """Context pattern for application prediction"""
    pattern_id: str
    context_features: Dict[str, Any]
    common_apps: List[str]
    app_probabilities: Dict[str, float]
    confidence: float
    success_rate: float

@dataclass
class AppPrediction:
    """Application launch prediction"""
    app_name: str
    confidence: float
    reasoning: str
    context_match: float
    historical_usage: float
    ai_recommendation: float

class PredictiveAppLauncher(dbus.service.Object):
    """Phase 2: Intelligent application prediction with full DuckBot integration"""
    
    def __init__(self):
        # Initialize D-Bus service
        DBusGMainLoop(set_as_default=True)
        self.bus = dbus.SessionBus()
        bus_name = dbus.service.BusName('org.duckbot.PredictiveAppLauncher', self.bus)
        super().__init__(bus_name, '/org/duckbot/PredictiveAppLauncher')
        
        # Complete DuckBot integration
        self.ai_router = AIRouter()
        self.cost_tracker = CostTracker()
        self.memento_available = False
        self.bytebot_available = False
        self.archon_available = False
        self.charm_available = False
        
        # Intelligence components
        self.usage_tracker = AppUsageTracker()
        self.context_analyzer = AppContextAnalyzer()
        self.prediction_engine = AppPredictionEngine()
        self.learning_system = AppLearningSystem()
        
        # Data storage
        self.usage_history = deque(maxlen=50000)
        self.context_patterns = {}
        self.app_categories = {}
        self.user_preferences = {}
        
        # Performance metrics
        self.prediction_accuracy = 0.0
        self.user_satisfaction = 0.0
        self.total_predictions = 0
        self.correct_predictions = 0
        
        logger.info("Predictive App Launcher with full DuckBot integration initialized")
    
    async def initialize(self):
        """Initialize with complete DuckBot integration"""
        try:
            # Initialize integration manager with all services
            await integration_manager.initialize_all()
            
            # Check available integrations
            self.memento_available = integration_manager.is_integration_available("memento")
            self.bytebot_available = integration_manager.is_integration_available("bytebot")
            self.archon_available = integration_manager.is_integration_available("archon")
            self.charm_available = integration_manager.is_integration_available("charm_tools")
            
            logger.info(f"Integration status - Memento: {self.memento_available}, "
                       f"ByteBot: {self.bytebot_available}, Archon: {self.archon_available}, "
                       f"Charm: {self.charm_available}")
            
            # Initialize AI router
            await self.ai_router.initialize()
            
            # Initialize intelligence components
            await self.usage_tracker.initialize()
            await self.context_analyzer.initialize()
            await self.prediction_engine.initialize(self)
            await self.learning_system.initialize(self)
            
            # Load historical data from Memento if available
            if self.memento_available:
                await self._load_memento_patterns()
            
            # Load Charm-enhanced user preferences
            if self.charm_available:
                await self._load_charm_preferences()
            
            # Initialize application categories
            await self._initialize_app_categories()
            
            # Start intelligent monitoring
            self._start_prediction_monitoring()
            
            logger.info("Predictive App Launcher fully initialized with all integrations")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Predictive App Launcher: {e}")
            return False
    
    @dbus.service.method('org.duckbot.PredictiveAppLauncher', 
                         in_signature='s', out_signature='s')
    def GetAppPredictions(self, context_json):
        """D-Bus method: Get intelligent app predictions"""
        try:
            context = json.loads(context_json)
            predictions = asyncio.create_task(self._get_intelligent_predictions(context))
            return json.dumps(predictions)
        except Exception as e:
            logger.error(f"GetAppPredictions failed: {e}")
            return json.dumps({"error": str(e)})
    
    @dbus.service.method('org.duckbot.PredictiveAppLauncher', 
                         in_signature='ss', out_signature='b')
    def LaunchAppWithContext(self, app_name, context_json):
        """D-Bus method: Launch app with full context awareness"""
        try:
            context = json.loads(context_json)
            asyncio.create_task(self._launch_app_intelligently(app_name, context))
            return True
        except Exception as e:
            logger.error(f"LaunchAppWithContext failed: {e}")
            return False
    
    @dbus.service.method('org.duckbot.PredictiveAppLauncher', 
                         in_signature='s', out_signature='s')
    def ProcessNaturalLanguageRequest(self, request):
        """D-Bus method: Process natural language app requests"""
        try:
            result = asyncio.create_task(self._process_nl_request(request))
            return json.dumps(result)
        except Exception as e:
            logger.error(f"ProcessNaturalLanguageRequest failed: {e}")
            return json.dumps({"error": str(e)})
    
    async def _get_intelligent_predictions(self, context: Dict[str, Any]) -> List[Dict]:
        """Get intelligent app predictions using all available DuckBot features"""
        
        # Analyze current context with full intelligence
        enhanced_context = await self.context_analyzer.enhance_context_with_ai(context)
        
        # Get predictions from multiple sources
        predictions = []
        
        # 1. Pattern-based predictions
        pattern_predictions = await self.prediction_engine.get_pattern_predictions(enhanced_context)
        predictions.extend(pattern_predictions)
        
        # 2. Memento memory-enhanced predictions
        if self.memento_available:
            memory_predictions = await self._get_memento_predictions(enhanced_context)
            predictions.extend(memory_predictions)
        
        # 3. AI-powered contextual predictions
        ai_predictions = await self._get_ai_contextual_predictions(enhanced_context)
        predictions.extend(ai_predictions)
        
        # 4. ByteBot desktop context predictions
        if self.bytebot_available:
            desktop_predictions = await self._get_desktop_context_predictions(enhanced_context)
            predictions.extend(desktop_predictions)
        
        # 5. Archon multi-agent analysis predictions
        if self.archon_available:
            agent_predictions = await self._get_agent_analysis_predictions(enhanced_context)
            predictions.extend(agent_predictions)
        
        # Combine and rank all predictions
        final_predictions = await self._combine_and_rank_predictions(predictions, enhanced_context)
        
        # Learn from these predictions for future improvement
        await self.learning_system.record_predictions(final_predictions, enhanced_context)
        
        return final_predictions[:10]  # Return top 10 predictions
    
    async def _get_memento_predictions(self, context: Dict) -> List[Dict]:
        """Get predictions enhanced by Memento memory"""
        try:
            # Query Memento for similar contexts
            memory_query = f"Find similar application usage contexts for: {json.dumps(context)}"
            
            result = await execute_memento_task(memory_query, {
                "task_type": "app_prediction",
                "context": context
            })
            
            if result.get("success"):
                similar_cases = result.get("similar_cases", [])
                
                predictions = []
                for case in similar_cases:
                    app_usage = case.get("solution", {}).get("app_launched")
                    if app_usage:
                        predictions.append({
                            "app_name": app_usage,
                            "confidence": case.get("similarity", 0.5),
                            "reasoning": f"Similar context from memory with {case.get('similarity', 0):.2f} similarity",
                            "source": "memento"
                        })
                
                return predictions
            
        except Exception as e:
            logger.error(f"Memento prediction error: {e}")
        
        return []
    
    async def _get_ai_contextual_predictions(self, context: Dict) -> List[Dict]:
        """Get AI-powered contextual predictions"""
        try:
            # Create intelligent query for AI
            context_description = await self._describe_context_for_ai(context)
            
            ai_query = f"""Based on this context: {context_description}
            
            What applications would be most useful right now? Consider:
            - Time of day and typical work patterns
            - Currently open applications and workflow
            - User's apparent task or goal
            - Productivity and efficiency optimization
            
            Provide 5 specific application recommendations with reasoning."""
            
            # Use AI router for intelligent response
            ai_response = await self.ai_router.route_request(ai_query, {
                "task_type": "app_prediction",
                "context": context,
                "use_memory": True
            })
            
            if ai_response.get("success"):
                # Parse AI response into structured predictions
                predictions = await self._parse_ai_predictions(ai_response["response"])
                return predictions
            
        except Exception as e:
            logger.error(f"AI contextual prediction error: {e}")
        
        return []
    
    async def _get_desktop_context_predictions(self, context: Dict) -> List[Dict]:
        """Get predictions based on desktop automation context"""
        try:
            if not self.bytebot_available:
                return []
            
            # Analyze desktop state with ByteBot
            desktop_analysis = await execute_natural_language_task(
                "Analyze current desktop state and suggest useful applications",
                {"analysis_type": "app_prediction", "context": context}
            )
            
            if desktop_analysis.get("success"):
                # Extract app suggestions from desktop analysis
                suggestions = desktop_analysis.get("result", {}).get("suggestions", [])
                
                predictions = []
                for suggestion in suggestions:
                    predictions.append({
                        "app_name": suggestion.get("app"),
                        "confidence": suggestion.get("confidence", 0.6),
                        "reasoning": suggestion.get("reason", "Desktop context analysis"),
                        "source": "bytebot"
                    })
                
                return predictions
            
        except Exception as e:
            logger.error(f"Desktop context prediction error: {e}")
        
        return []
    
    async def _get_agent_analysis_predictions(self, context: Dict) -> List[Dict]:
        """Get predictions from multi-agent analysis"""
        try:
            if not self.archon_available:
                return []
            
            # Create specialized agent for app prediction analysis
            agent_task = await create_archon_task(
                f"Analyze context and predict optimal applications: {json.dumps(context)}",
                "app_prediction_agent",
                {
                    "analysis_depth": "comprehensive",
                    "context": context,
                    "prediction_count": 5
                }
            )
            
            if agent_task:
                # Wait for agent analysis (this would be async in real implementation)
                await asyncio.sleep(1)
                
                # Mock agent predictions - real implementation would query agent results
                return [
                    {
                        "app_name": "predicted_app",
                        "confidence": 0.7,
                        "reasoning": "Multi-agent analysis recommendation", 
                        "source": "archon"
                    }
                ]
            
        except Exception as e:
            logger.error(f"Agent analysis prediction error: {e}")
        
        return []
    
    async def _combine_and_rank_predictions(self, predictions: List[Dict], context: Dict) -> List[Dict]:
        """Intelligently combine and rank all predictions"""
        
        # Group predictions by app name
        app_predictions = defaultdict(list)
        for pred in predictions:
            app_predictions[pred["app_name"]].append(pred)
        
        # Calculate combined scores for each app
        combined_predictions = []
        
        for app_name, pred_list in app_predictions.items():
            # Combine confidences with weighted average
            total_weight = 0
            weighted_confidence = 0
            
            source_weights = {
                "pattern": 0.3,
                "memento": 0.25, 
                "ai": 0.2,
                "bytebot": 0.15,
                "archon": 0.1
            }
            
            reasoning_parts = []
            
            for pred in pred_list:
                source = pred.get("source", "pattern")
                weight = source_weights.get(source, 0.1)
                confidence = pred.get("confidence", 0.5)
                
                weighted_confidence += confidence * weight
                total_weight += weight
                reasoning_parts.append(f"{source}: {pred.get('reasoning', 'N/A')}")
            
            if total_weight > 0:
                final_confidence = weighted_confidence / total_weight
            else:
                final_confidence = 0.5
            
            # Apply context-specific boosting
            boosted_confidence = await self._apply_context_boosting(
                app_name, final_confidence, context
            )
            
            combined_predictions.append({
                "app_name": app_name,
                "confidence": boosted_confidence,
                "reasoning": " | ".join(reasoning_parts),
                "prediction_sources": len(pred_list),
                "context_match": await self._calculate_context_match(app_name, context)
            })
        
        # Sort by confidence
        combined_predictions.sort(key=lambda x: x["confidence"], reverse=True)
        
        return combined_predictions
    
    async def _apply_context_boosting(self, app_name: str, confidence: float, context: Dict) -> float:
        """Apply context-specific confidence boosting"""
        
        boost = 0.0
        
        # Time-based boosting
        hour = datetime.now().hour
        if app_name in self.app_categories.get("work", []) and 9 <= hour <= 17:
            boost += 0.1
        elif app_name in self.app_categories.get("entertainment", []) and (hour >= 18 or hour <= 8):
            boost += 0.1
        
        # Recent usage boosting
        recent_apps = [event.app_name for event in list(self.usage_history)[-10:]]
        if app_name in recent_apps:
            boost += 0.05
        
        # Context keyword boosting
        context_text = json.dumps(context).lower()
        app_keywords = self.app_categories.get("keywords", {}).get(app_name, [])
        for keyword in app_keywords:
            if keyword.lower() in context_text:
                boost += 0.05
        
        return min(1.0, confidence + boost)
    
    async def _calculate_context_match(self, app_name: str, context: Dict) -> float:
        """Calculate how well app matches current context"""
        
        # This would implement sophisticated context matching
        # For now, return a mock value
        return 0.7
    
    async def _launch_app_intelligently(self, app_name: str, context: Dict):
        """Launch application with full intelligence and context awareness"""
        
        logger.info(f"Launching {app_name} intelligently with context: {context}")
        
        # Pre-launch analysis and preparation
        await self._prepare_intelligent_launch(app_name, context)
        
        # Launch the application
        launch_success = False
        launch_method = "standard"
        
        try:
            # Try ByteBot enhanced launch if available
            if self.bytebot_available:
                bytebot_result = await execute_natural_language_task(
                    f"Launch {app_name} in the optimal way for current context",
                    {"app": app_name, "context": context}
                )
                if bytebot_result.get("success"):
                    launch_success = True
                    launch_method = "bytebot_enhanced"
            
            # Fallback to standard launch
            if not launch_success:
                subprocess.Popen([app_name])
                launch_success = True
                launch_method = "standard"
            
            # Post-launch intelligence
            if launch_success:
                await self._handle_post_launch_intelligence(app_name, context, launch_method)
            
        except Exception as e:
            logger.error(f"Failed to launch {app_name}: {e}")
            await self._handle_launch_failure(app_name, context, str(e))
    
    async def _prepare_intelligent_launch(self, app_name: str, context: Dict):
        """Prepare for intelligent application launch"""
        
        # Store launch context for learning
        await store_data(f"launch_context_{app_name}_{time.time()}", {
            "app": app_name,
            "context": context,
            "timestamp": time.time()
        })
        
        # Notify Memento about launch intention
        if self.memento_available:
            await execute_memento_task(
                f"User is launching {app_name}",
                {"event_type": "app_launch", "app": app_name, "context": context}
            )
        
        # Prepare workspace if needed
        workspace_prep = context.get("workspace_preparation")
        if workspace_prep and self.bytebot_available:
            await execute_natural_language_task(
                f"Prepare workspace for {app_name}: {workspace_prep}",
                {"preparation_type": "workspace", "app": app_name}
            )
    
    async def _handle_post_launch_intelligence(self, app_name: str, context: Dict, method: str):
        """Handle post-launch intelligence and learning"""
        
        # Record successful launch
        launch_event = AppUsageEvent(
            timestamp=time.time(),
            app_name=app_name,
            launch_method=method,
            context=context
        )
        self.usage_history.append(launch_event)
        
        # Update prediction accuracy if this was a predicted launch
        if context.get("was_predicted"):
            self.correct_predictions += 1
            self.total_predictions += 1
            self.prediction_accuracy = self.correct_predictions / self.total_predictions
        
        # Learn from successful launch
        await self.learning_system.record_successful_launch(app_name, context, method)
        
        # Suggest complementary applications
        await self._suggest_complementary_apps(app_name, context)
        
        logger.info(f"Successfully launched {app_name} with method {method}")
    
    async def _suggest_complementary_apps(self, launched_app: str, context: Dict):
        """Suggest complementary applications after a launch"""
        
        # Find applications commonly used with this one
        complementary_apps = await self._find_complementary_apps(launched_app)
        
        if complementary_apps and self.charm_available:
            # Show elegant suggestion using Charm
            app_choices = [f"{app} ({reason})" for app, reason in complementary_apps.items()]
            
            if len(app_choices) > 0:
                # Show suggestion after a brief delay
                await asyncio.sleep(3)
                
                suggestion = await gum_choose(
                    app_choices + ["No, thank you"],
                    f"Since you launched {launched_app}, you might also want to open:",
                    limit=1
                )
                
                if suggestion and suggestion != "No, thank you":
                    suggested_app = suggestion.split(" (")[0]
                    await self._launch_app_intelligently(suggested_app, {
                        **context,
                        "suggested_by": launched_app,
                        "suggestion_type": "complementary"
                    })
    
    async def _find_complementary_apps(self, app_name: str) -> Dict[str, str]:
        """Find apps commonly used with the given app"""
        
        complementary = {}
        
        # Analyze usage history for patterns
        app_sessions = []
        current_session = []
        
        for event in self.usage_history:
            if event.app_name == app_name:
                if current_session:
                    app_sessions.append(current_session)
                current_session = [event]
            elif current_session:
                current_session.append(event)
        
        # Find frequently co-used applications
        co_usage = defaultdict(int)
        for session in app_sessions:
            other_apps = [e.app_name for e in session if e.app_name != app_name]
            for other_app in set(other_apps):
                co_usage[other_app] += 1
        
        # Convert to recommendations
        total_sessions = len(app_sessions)
        if total_sessions > 0:
            for other_app, count in co_usage.items():
                if count / total_sessions > 0.3:  # Used together >30% of the time
                    complementary[other_app] = f"Used together {count}/{total_sessions} times"
        
        return complementary
    
    async def _process_nl_request(self, request: str) -> Dict[str, Any]:
        """Process natural language application request"""
        
        logger.info(f"Processing NL request: {request}")
        
        try:
            # Use AI to understand the request
            ai_query = f"""Parse this application request: "{request}"
            
            Extract:
            1. What application(s) the user wants to launch
            2. Any specific configuration or context needed
            3. The user's apparent goal or task
            4. Any workflow or workspace requirements
            
            Respond in JSON format with: app_name, context, goal, requirements"""
            
            ai_response = await self.ai_router.route_request(ai_query, {
                "task_type": "nl_parsing",
                "request": request
            })
            
            if ai_response.get("success"):
                parsed_request = await self._parse_nl_response(ai_response["response"])
                
                # Launch application with parsed context
                app_name = parsed_request.get("app_name")
                if app_name:
                    enhanced_context = {
                        "nl_request": request,
                        "parsed_goal": parsed_request.get("goal"),
                        "requirements": parsed_request.get("requirements"),
                        "ai_confidence": ai_response.get("confidence", 0.5)
                    }
                    
                    await self._launch_app_intelligently(app_name, enhanced_context)
                    
                    return {
                        "success": True,
                        "app_launched": app_name,
                        "context": enhanced_context
                    }
                else:
                    # Could not identify app, provide suggestions
                    suggestions = await self._get_app_suggestions_from_nl(request)
                    return {
                        "success": False,
                        "reason": "Could not identify specific application",
                        "suggestions": suggestions
                    }
            
        except Exception as e:
            logger.error(f"NL request processing error: {e}")
            return {"success": False, "error": str(e)}
    
    async def _load_memento_patterns(self):
        """Load application patterns from Memento memory"""
        try:
            if not self.memento_available:
                return
            
            memory_stats = await get_memento_memory_stats()
            if memory_stats.get("available"):
                # Query for application usage patterns
                pattern_query = "Find patterns in application usage and launching behavior"
                result = await execute_memento_task(pattern_query)
                
                if result.get("success"):
                    patterns = result.get("patterns", [])
                    for pattern in patterns:
                        pattern_id = pattern.get("id")
                        if pattern_id:
                            self.context_patterns[pattern_id] = pattern
                    
                    logger.info(f"Loaded {len(patterns)} patterns from Memento")
            
        except Exception as e:
            logger.error(f"Failed to load Memento patterns: {e}")
    
    async def _load_charm_preferences(self):
        """Load user preferences using Charm tools"""
        try:
            if not self.charm_available:
                return
            
            # Load preferences from Skate storage
            prefs_data = await load_data("app_launcher_preferences")
            if prefs_data:
                self.user_preferences = json.loads(prefs_data)
                logger.info("Loaded user preferences from Charm storage")
            
        except Exception as e:
            logger.error(f"Failed to load Charm preferences: {e}")
    
    async def _initialize_app_categories(self):
        """Initialize application categories and metadata"""
        
        self.app_categories = {
            "work": [
                "code", "vscode", "sublime", "atom", "idea", "eclipse",
                "libreoffice", "calc", "writer", "impress",
                "slack", "teams", "zoom", "skype"
            ],
            "entertainment": [
                "firefox", "chrome", "spotify", "vlc", "steam", 
                "netflix", "youtube", "games"
            ],
            "development": [
                "terminal", "git", "docker", "kubernetes", "postman",
                "database", "mysql", "mongodb", "redis"
            ],
            "creative": [
                "gimp", "inkscape", "blender", "photoshop", "illustrator",
                "figma", "sketch", "canva"
            ],
            "keywords": {
                "firefox": ["browse", "web", "internet", "search"],
                "code": ["edit", "program", "code", "develop"],
                "terminal": ["command", "shell", "terminal", "bash"],
                "spotify": ["music", "audio", "song", "playlist"]
            }
        }
        
        logger.info("Application categories initialized")
    
    def _start_prediction_monitoring(self):
        """Start continuous prediction monitoring and learning"""
        
        def monitor_and_predict():
            """Continuous monitoring for prediction opportunities"""
            
            # This would monitor for prediction opportunities
            # For now, just return True to continue monitoring
            
            return True
        
        # Monitor every 30 seconds for prediction opportunities
        GLib.timeout_add_seconds(30, monitor_and_predict)

class AppUsageTracker:
    """Track application usage patterns"""
    
    async def initialize(self):
        logger.info("App Usage Tracker initialized")

class AppContextAnalyzer:
    """Analyze context for application predictions"""
    
    async def initialize(self):
        logger.info("App Context Analyzer initialized")
    
    async def enhance_context_with_ai(self, context: Dict) -> Dict:
        """Enhance context using AI analysis"""
        
        # Add temporal features
        now = datetime.now()
        context["enhanced"] = {
            "hour": now.hour,
            "day_of_week": now.weekday(),
            "is_weekend": now.weekday() >= 5,
            "is_work_hours": 9 <= now.hour <= 17
        }
        
        return context

class AppPredictionEngine:
    """Engine for generating application predictions"""
    
    async def initialize(self, launcher):
        self.launcher = launcher
        logger.info("App Prediction Engine initialized")
    
    async def get_pattern_predictions(self, context: Dict) -> List[Dict]:
        """Get predictions based on learned patterns"""
        
        # Mock pattern-based predictions
        return [
            {
                "app_name": "firefox",
                "confidence": 0.8,
                "reasoning": "Commonly used at this time",
                "source": "pattern"
            }
        ]

class AppLearningSystem:
    """System for learning from application usage"""
    
    async def initialize(self, launcher):
        self.launcher = launcher
        logger.info("App Learning System initialized")
    
    async def record_predictions(self, predictions: List[Dict], context: Dict):
        """Record predictions for learning"""
        pass
    
    async def record_successful_launch(self, app_name: str, context: Dict, method: str):
        """Record successful app launch"""
        pass

async def main():
    """Main service entry point"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create and initialize the Predictive App Launcher
    app_launcher = PredictiveAppLauncher()
    await app_launcher.initialize()
    
    # Start the main loop
    loop = GLib.MainLoop()
    
    try:
        logger.info("DuckBot Predictive App Launcher Phase 2 running")
        loop.run()
    except KeyboardInterrupt:
        logger.info("Service stopped by user")
    except Exception as e:
        logger.error(f"Service error: {e}")

if __name__ == "__main__":
    asyncio.run(main())