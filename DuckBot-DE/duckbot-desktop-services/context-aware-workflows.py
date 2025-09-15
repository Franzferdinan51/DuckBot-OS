#!/usr/bin/env python3
"""
DuckBot Desktop Environment - Context-Aware Workflows
Intelligent workflow detection, automation, and prediction system
"""

import asyncio
import json
import sqlite3
import logging
import time
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import dbus
import dbus.service
import dbus.mainloop.glib
from gi.repository import GLib

# Add DuckBot path for complete integration
sys.path.append('/usr/share/duckbot-de')
sys.path.append('/home/user/Desktop/DuckBot-v3.1.0-VibeVoice-Ready-20250829_191017 (1)')

try:
    from duckbot.ai_router_gpt import DuckBotAI
    from duckbot.dynamic_model_manager import DynamicModelManager
    from duckbot.integration_manager import integration_manager
    from duckbot.charm_tools_integration import CharmToolsIntegration
    DUCKBOT_AVAILABLE = True
except ImportError:
    DUCKBOT_AVAILABLE = False
    print("[WARN]  DuckBot core not available, running in standalone mode")

@dataclass
class WorkflowEvent:
    """Represents a single workflow event"""
    timestamp: float
    event_type: str  # app_open, app_close, file_access, command_exec, etc.
    app_name: str
    details: Dict[str, Any]
    context: Dict[str, Any]
    user_id: str = "default"

@dataclass
class WorkflowPattern:
    """Represents a detected workflow pattern"""
    pattern_id: str
    name: str
    events: List[WorkflowEvent]
    frequency: int
    confidence: float
    last_seen: float
    automation_potential: float
    description: str

@dataclass
class WorkflowContext:
    """Current context for workflow analysis"""
    active_apps: List[str]
    focused_app: str
    time_of_day: str
    day_of_week: str
    recent_files: List[str]
    recent_commands: List[str]
    system_state: Dict[str, Any]
    user_activity_level: str

class ContextAwareWorkflows(dbus.service.Object):
    """
    Context-Aware Workflows System
    
    Features:
    - Intelligent workflow detection and pattern recognition
    - Predictive workflow automation
    - Context-aware task suggestions
    - Multi-modal workflow learning (apps, files, commands, time)
    - Integration with DuckBot AI ecosystem
    - Memento memory integration for persistent learning
    - Charm tools for elegant user interactions
    """
    
    def __init__(self):
        # D-Bus setup
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        self.bus = dbus.SessionBus()
        super().__init__(self.bus, '/org/duckbot/ContextWorkflows')
        
        # Core components
        self.logger = self._setup_logging()
        self.db_path = Path.home() / '.duckbot' / 'workflows.db'
        self.db_path.parent.mkdir(exist_ok=True)
        
        # Workflow analysis
        self.events = []
        self.patterns = {}
        self.current_context = None
        self.workflow_suggestions = []
        
        # DuckBot integrations
        self.duckbot_ai = None
        self.memento_available = False
        self.charm_tools = None
        self.model_manager = None
        
        # Configuration
        self.config = {
            'pattern_min_frequency': 3,
            'pattern_confidence_threshold': 0.7,
            'context_window_hours': 24,
            'automation_confidence_threshold': 0.8,
            'max_stored_events': 10000,
            'analysis_interval': 300,  # 5 minutes
        }
        
        # Analysis state
        self.last_analysis = 0
        self.active_workflows = {}
        self.pending_automations = []
        
    def _setup_logging(self) -> logging.Logger:
        """Setup comprehensive logging"""
        logger = logging.getLogger('ContextWorkflows')
        logger.setLevel(logging.INFO)
        
        # File handler
        log_file = Path.home() / '.duckbot' / 'context_workflows.log'
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # Format
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        return logger
        
    async def initialize(self):
        """Initialize all components and integrations"""
        self.logger.info("[EMOJI] Initializing Context-Aware Workflows...")
        
        # Initialize database
        await self._init_database()
        
        # Initialize DuckBot integrations
        if DUCKBOT_AVAILABLE:
            await self._init_duckbot_integrations()
        
        # Load existing patterns
        await self._load_patterns()
        
        # Start background analysis
        asyncio.create_task(self._analysis_loop())
        
        self.logger.info("[OK] Context-Aware Workflows initialized successfully")
        
    async def _init_database(self):
        """Initialize SQLite database for workflow storage"""
        self.db = sqlite3.connect(str(self.db_path))
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS workflow_events (
                id INTEGER PRIMARY KEY,
                timestamp REAL,
                event_type TEXT,
                app_name TEXT,
                details TEXT,
                context TEXT,
                user_id TEXT DEFAULT 'default'
            )
        """)
        
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS workflow_patterns (
                pattern_id TEXT PRIMARY KEY,
                name TEXT,
                events TEXT,
                frequency INTEGER,
                confidence REAL,
                last_seen REAL,
                automation_potential REAL,
                description TEXT
            )
        """)
        
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS workflow_automations (
                automation_id TEXT PRIMARY KEY,
                pattern_id TEXT,
                automation_script TEXT,
                success_rate REAL,
                last_executed REAL,
                enabled BOOLEAN DEFAULT 1
            )
        """)
        
        self.db.commit()
        
    async def _init_duckbot_integrations(self):
        """Initialize DuckBot AI ecosystem integrations"""
        try:
            # Initialize AI router
            self.duckbot_ai = DuckBotAI()
            await self.duckbot_ai.initialize()
            
            # Initialize dynamic model manager
            self.model_manager = DynamicModelManager()
            await self.model_manager.initialize()
            
            # Initialize integration manager
            await integration_manager.initialize_all()
            
            # Check Memento availability
            if integration_manager.is_integration_available("memento"):
                self.memento_available = True
                self.logger.info("[OK] Memento memory integration available")
            
            # Initialize Charm tools
            self.charm_tools = CharmToolsIntegration()
            
            self.logger.info("[OK] DuckBot integrations initialized")
            
        except Exception as e:
            self.logger.error(f"[FAIL] DuckBot integration failed: {e}")
            
    async def _load_patterns(self):
        """Load existing workflow patterns from database"""
        cursor = self.db.execute(
            "SELECT * FROM workflow_patterns ORDER BY confidence DESC"
        )
        
        for row in cursor.fetchall():
            pattern_id, name, events_json, frequency, confidence, last_seen, automation_potential, description = row
            
            # Deserialize events
            events_data = json.loads(events_json)
            events = [WorkflowEvent(**event) for event in events_data]
            
            pattern = WorkflowPattern(
                pattern_id=pattern_id,
                name=name,
                events=events,
                frequency=frequency,
                confidence=confidence,
                last_seen=last_seen,
                automation_potential=automation_potential,
                description=description
            )
            
            self.patterns[pattern_id] = pattern
            
        self.logger.info(f"[DOCS] Loaded {len(self.patterns)} workflow patterns")
        
    async def _analysis_loop(self):
        """Main analysis loop for pattern detection and context updates"""
        while True:
            try:
                current_time = time.time()
                
                # Update current context
                await self._update_current_context()
                
                # Analyze patterns every 5 minutes
                if current_time - self.last_analysis > self.config['analysis_interval']:
                    await self._analyze_patterns()
                    await self._generate_suggestions()
                    self.last_analysis = current_time
                
                # Check for automation opportunities
                await self._check_automation_opportunities()
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                self.logger.error(f"[FAIL] Analysis loop error: {e}")
                await asyncio.sleep(60)
                
    async def _update_current_context(self):
        """Update current workflow context"""
        try:
            # Get active applications
            active_apps = await self._get_active_applications()
            
            # Get focused application
            focused_app = await self._get_focused_application()
            
            # Get time context
            now = datetime.now()
            time_of_day = self._get_time_period(now.hour)
            day_of_week = now.strftime("%A")
            
            # Get recent files and commands
            recent_files = await self._get_recent_files()
            recent_commands = await self._get_recent_commands()
            
            # Get system state
            system_state = await self._get_system_state()
            
            # Determine user activity level
            activity_level = await self._determine_activity_level()
            
            self.current_context = WorkflowContext(
                active_apps=active_apps,
                focused_app=focused_app,
                time_of_day=time_of_day,
                day_of_week=day_of_week,
                recent_files=recent_files,
                recent_commands=recent_commands,
                system_state=system_state,
                user_activity_level=activity_level
            )
            
        except Exception as e:
            self.logger.error(f"[FAIL] Context update error: {e}")
            
    async def _get_active_applications(self) -> List[str]:
        """Get currently active applications"""
        try:
            import psutil
            apps = []
            for proc in psutil.process_iter(['name']):
                try:
                    if proc.info['name']:
                        apps.append(proc.info['name'])
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            return list(set(apps))  # Remove duplicates
        except Exception:
            return []
            
    async def _get_focused_application(self) -> str:
        """Get currently focused application"""
        try:
            # Use xdotool or similar to get focused window
            import subprocess
            result = subprocess.run(
                ['xdotool', 'getwindowfocus', 'getwindowname'],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return "unknown"
        
    def _get_time_period(self, hour: int) -> str:
        """Get descriptive time period"""
        if 6 <= hour < 12:
            return "morning"
        elif 12 <= hour < 17:
            return "afternoon"
        elif 17 <= hour < 21:
            return "evening"
        else:
            return "night"
            
    async def _get_recent_files(self) -> List[str]:
        """Get recently accessed files"""
        try:
            # Check recent files from various sources
            recent = []
            
            # Check recent documents
            recent_docs = Path.home() / '.recently-used.xbel'
            if recent_docs.exists():
                # Parse XBEL format for recent files
                pass
            
            return recent[:10]  # Last 10 files
        except Exception:
            return []
            
    async def _get_recent_commands(self) -> List[str]:
        """Get recently executed commands"""
        try:
            # Check bash history
            history_file = Path.home() / '.bash_history'
            if history_file.exists():
                lines = history_file.read_text().strip().split('\n')
                return lines[-20:]  # Last 20 commands
        except Exception:
            pass
        return []
        
    async def _get_system_state(self) -> Dict[str, Any]:
        """Get current system state"""
        try:
            import psutil
            return {
                'cpu_percent': psutil.cpu_percent(),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_usage': psutil.disk_usage('/').percent,
                'network_active': len(psutil.net_connections()) > 10
            }
        except Exception:
            return {}
            
    async def _determine_activity_level(self) -> str:
        """Determine current user activity level"""
        try:
            # Simple heuristic based on number of active apps and system usage
            if not self.current_context:
                return "unknown"
                
            active_count = len(self.current_context.active_apps) if hasattr(self.current_context, 'active_apps') else 0
            
            if active_count < 5:
                return "low"
            elif active_count < 15:
                return "medium"
            else:
                return "high"
        except Exception:
            return "unknown"
            
    async def _analyze_patterns(self):
        """Analyze recent events for workflow patterns"""
        try:
            self.logger.info("[EMOJI] Analyzing workflow patterns...")
            
            # Get recent events (last 24 hours)
            cutoff_time = time.time() - (self.config['context_window_hours'] * 3600)
            recent_events = await self._get_recent_events(cutoff_time)
            
            if len(recent_events) < 3:
                return
            
            # Analyze sequences
            sequences = await self._find_event_sequences(recent_events)
            
            # Update existing patterns or create new ones
            for sequence in sequences:
                await self._update_or_create_pattern(sequence)
            
            # Clean up old patterns
            await self._cleanup_old_patterns()
            
            self.logger.info(f"[OK] Pattern analysis complete. {len(self.patterns)} patterns total")
            
        except Exception as e:
            self.logger.error(f"[FAIL] Pattern analysis error: {e}")
            
    async def _get_recent_events(self, cutoff_time: float) -> List[WorkflowEvent]:
        """Get events since cutoff time"""
        cursor = self.db.execute(
            "SELECT * FROM workflow_events WHERE timestamp > ? ORDER BY timestamp",
            (cutoff_time,)
        )
        
        events = []
        for row in cursor.fetchall():
            _, timestamp, event_type, app_name, details_json, context_json, user_id = row
            
            details = json.loads(details_json) if details_json else {}
            context = json.loads(context_json) if context_json else {}
            
            event = WorkflowEvent(
                timestamp=timestamp,
                event_type=event_type,
                app_name=app_name,
                details=details,
                context=context,
                user_id=user_id
            )
            events.append(event)
            
        return events
        
    async def _find_event_sequences(self, events: List[WorkflowEvent]) -> List[List[WorkflowEvent]]:
        """Find meaningful event sequences"""
        sequences = []
        
        # Simple sliding window approach
        window_size = 5
        for i in range(len(events) - window_size + 1):
            window = events[i:i + window_size]
            
            # Check if this is a meaningful sequence
            if await self._is_meaningful_sequence(window):
                sequences.append(window)
        
        return sequences
        
    async def _is_meaningful_sequence(self, events: List[WorkflowEvent]) -> bool:
        """Determine if a sequence of events is meaningful"""
        if len(events) < 2:
            return False
            
        # Check temporal proximity (events within 1 hour)
        time_span = events[-1].timestamp - events[0].timestamp
        if time_span > 3600:  # 1 hour
            return False
            
        # Check for app diversity (not all same app)
        apps = set(event.app_name for event in events)
        if len(apps) < 2:
            return False
            
        return True
        
    async def _update_or_create_pattern(self, sequence: List[WorkflowEvent]):
        """Update existing pattern or create new one"""
        # Generate pattern signature
        signature = self._generate_pattern_signature(sequence)
        
        if signature in self.patterns:
            # Update existing pattern
            pattern = self.patterns[signature]
            pattern.frequency += 1
            pattern.last_seen = time.time()
            pattern.confidence = min(1.0, pattern.confidence + 0.1)
        else:
            # Create new pattern
            pattern = WorkflowPattern(
                pattern_id=signature,
                name=await self._generate_pattern_name(sequence),
                events=sequence,
                frequency=1,
                confidence=0.5,
                last_seen=time.time(),
                automation_potential=await self._calculate_automation_potential(sequence),
                description=await self._generate_pattern_description(sequence)
            )
            self.patterns[signature] = pattern
            
        # Save to database
        await self._save_pattern(pattern)
        
    def _generate_pattern_signature(self, sequence: List[WorkflowEvent]) -> str:
        """Generate unique signature for event sequence"""
        app_sequence = " -> ".join(event.app_name for event in sequence)
        event_sequence = " -> ".join(event.event_type for event in sequence)
        return f"{app_sequence}::{event_sequence}"
        
    async def _generate_pattern_name(self, sequence: List[WorkflowEvent]) -> str:
        """Generate human-readable name for pattern"""
        if self.duckbot_ai and DUCKBOT_AVAILABLE:
            try:
                # Use AI to generate descriptive name
                context = {
                    'sequence': [{'app': e.app_name, 'action': e.event_type} for e in sequence]
                }
                
                result = await self.duckbot_ai.enhanced_request(
                    "Generate a concise, descriptive name for this workflow pattern",
                    context,
                    preferred_model="local"
                )
                
                if result.get("success"):
                    return result["result"]["content"][:50]  # Limit length
                    
            except Exception as e:
                self.logger.debug(f"AI pattern naming failed: {e}")
        
        # Fallback to simple naming
        apps = " + ".join(set(event.app_name for event in sequence))
        return f"Workflow: {apps}"
        
    async def _calculate_automation_potential(self, sequence: List[WorkflowEvent]) -> float:
        """Calculate how suitable this pattern is for automation"""
        # Simple heuristic based on sequence characteristics
        score = 0.0
        
        # Repetitive sequences score higher
        if len(sequence) >= 3:
            score += 0.3
            
        # File operations are good for automation
        file_ops = sum(1 for e in sequence if 'file' in e.event_type.lower())
        score += min(0.4, file_ops * 0.1)
        
        # Command execution patterns
        cmd_ops = sum(1 for e in sequence if 'command' in e.event_type.lower())
        score += min(0.3, cmd_ops * 0.1)
        
        return min(1.0, score)
        
    async def _generate_pattern_description(self, sequence: List[WorkflowEvent]) -> str:
        """Generate description for pattern"""
        if self.duckbot_ai and DUCKBOT_AVAILABLE:
            try:
                context = {
                    'sequence': [
                        {
                            'app': e.app_name,
                            'action': e.event_type,
                            'time': datetime.fromtimestamp(e.timestamp).strftime("%H:%M")
                        } for e in sequence
                    ]
                }
                
                result = await self.duckbot_ai.enhanced_request(
                    "Generate a brief description of what this workflow accomplishes",
                    context,
                    preferred_model="local"
                )
                
                if result.get("success"):
                    return result["result"]["content"][:200]
                    
            except Exception as e:
                self.logger.debug(f"AI description generation failed: {e}")
        
        # Fallback description
        return f"Workflow involving {len(sequence)} steps across {len(set(e.app_name for e in sequence))} applications"
        
    async def _save_pattern(self, pattern: WorkflowPattern):
        """Save pattern to database"""
        events_json = json.dumps([asdict(event) for event in pattern.events])
        
        self.db.execute("""
            INSERT OR REPLACE INTO workflow_patterns
            (pattern_id, name, events, frequency, confidence, last_seen, automation_potential, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            pattern.pattern_id,
            pattern.name,
            events_json,
            pattern.frequency,
            pattern.confidence,
            pattern.last_seen,
            pattern.automation_potential,
            pattern.description
        ))
        self.db.commit()
        
    async def _cleanup_old_patterns(self):
        """Remove old, low-confidence patterns"""
        cutoff_time = time.time() - (30 * 24 * 3600)  # 30 days
        
        to_remove = []
        for pattern_id, pattern in self.patterns.items():
            if (pattern.last_seen < cutoff_time and 
                pattern.confidence < self.config['pattern_confidence_threshold']):
                to_remove.append(pattern_id)
        
        for pattern_id in to_remove:
            del self.patterns[pattern_id]
            self.db.execute("DELETE FROM workflow_patterns WHERE pattern_id = ?", (pattern_id,))
        
        if to_remove:
            self.db.commit()
            self.logger.info(f"[EMOJI] Cleaned up {len(to_remove)} old patterns")
            
    async def _generate_suggestions(self):
        """Generate workflow suggestions based on context and patterns"""
        if not self.current_context:
            return
            
        suggestions = []
        
        # Find patterns matching current context
        matching_patterns = await self._find_matching_patterns()
        
        for pattern in matching_patterns:
            if pattern.confidence > self.config['pattern_confidence_threshold']:
                suggestion = await self._create_suggestion(pattern)
                if suggestion:
                    suggestions.append(suggestion)
        
        # AI-powered contextual suggestions
        if self.duckbot_ai and DUCKBOT_AVAILABLE:
            ai_suggestions = await self._get_ai_suggestions()
            suggestions.extend(ai_suggestions)
        
        self.workflow_suggestions = suggestions[:5]  # Keep top 5
        
        # Store in Memento if available
        if self.memento_available:
            await self._store_suggestions_in_memory()
            
    async def _find_matching_patterns(self) -> List[WorkflowPattern]:
        """Find patterns matching current context"""
        matching = []
        
        for pattern in self.patterns.values():
            match_score = await self._calculate_pattern_match(pattern)
            if match_score > 0.5:
                matching.append(pattern)
        
        # Sort by match score and confidence
        return sorted(matching, key=lambda p: p.confidence, reverse=True)
        
    async def _calculate_pattern_match(self, pattern: WorkflowPattern) -> float:
        """Calculate how well pattern matches current context"""
        if not self.current_context:
            return 0.0
            
        score = 0.0
        
        # Check time similarity
        pattern_time = datetime.fromtimestamp(pattern.last_seen)
        current_time = datetime.now()
        
        if pattern_time.hour == current_time.hour:
            score += 0.3
        elif abs(pattern_time.hour - current_time.hour) <= 2:
            score += 0.1
            
        # Check day similarity
        if pattern_time.strftime("%A") == current_time.strftime("%A"):
            score += 0.2
            
        # Check app similarity
        pattern_apps = set(event.app_name for event in pattern.events)
        current_apps = set(self.current_context.active_apps)
        
        if pattern_apps & current_apps:  # Intersection
            overlap = len(pattern_apps & current_apps) / len(pattern_apps | current_apps)
            score += overlap * 0.5
            
        return min(1.0, score)
        
    async def _create_suggestion(self, pattern: WorkflowPattern) -> Optional[Dict[str, Any]]:
        """Create actionable suggestion from pattern"""
        try:
            return {
                'id': pattern.pattern_id,
                'title': pattern.name,
                'description': pattern.description,
                'confidence': pattern.confidence,
                'automation_potential': pattern.automation_potential,
                'actions': await self._extract_actions(pattern),
                'frequency': pattern.frequency
            }
        except Exception as e:
            self.logger.error(f"[FAIL] Suggestion creation error: {e}")
            return None
            
    async def _extract_actions(self, pattern: WorkflowPattern) -> List[Dict[str, Any]]:
        """Extract actionable steps from pattern"""
        actions = []
        
        for event in pattern.events:
            action = {
                'type': event.event_type,
                'app': event.app_name,
                'description': f"{event.event_type} in {event.app_name}"
            }
            
            # Add specific details if available
            if event.details:
                action['details'] = event.details
                
            actions.append(action)
            
        return actions
        
    async def _get_ai_suggestions(self) -> List[Dict[str, Any]]:
        """Get AI-powered workflow suggestions"""
        try:
            context_summary = {
                'current_app': self.current_context.focused_app,
                'active_apps': self.current_context.active_apps[:5],
                'time_period': self.current_context.time_of_day,
                'day': self.current_context.day_of_week,
                'activity_level': self.current_context.user_activity_level,
                'recent_patterns': [p.name for p in list(self.patterns.values())[:3]]
            }
            
            result = await self.duckbot_ai.enhanced_request(
                "Based on the current context, suggest 2-3 workflow optimizations or automations that would be helpful",
                context_summary,
                preferred_model="local"
            )
            
            if result.get("success"):
                # Parse AI response into structured suggestions
                ai_text = result["result"]["content"]
                return await self._parse_ai_suggestions(ai_text)
                
        except Exception as e:
            self.logger.error(f"[FAIL] AI suggestions error: {e}")
            
        return []
        
    async def _parse_ai_suggestions(self, ai_text: str) -> List[Dict[str, Any]]:
        """Parse AI response into structured suggestions"""
        # Simple parsing - in practice would be more sophisticated
        suggestions = []
        
        # Split by lines and look for suggestion patterns
        lines = ai_text.split('\n')
        current_suggestion = None
        
        for line in lines:
            line = line.strip()
            if line.startswith(('-', '*', '•')):
                if current_suggestion:
                    suggestions.append(current_suggestion)
                    
                current_suggestion = {
                    'id': f"ai_suggestion_{len(suggestions)}",
                    'title': line[1:].strip(),
                    'description': line[1:].strip(),
                    'confidence': 0.7,
                    'automation_potential': 0.6,
                    'actions': [],
                    'source': 'ai'
                }
            elif current_suggestion and line:
                current_suggestion['description'] += f" {line}"
                
        if current_suggestion:
            suggestions.append(current_suggestion)
            
        return suggestions[:3]  # Max 3 AI suggestions
        
    async def _store_suggestions_in_memory(self):
        """Store current suggestions in Memento memory"""
        try:
            if not self.memento_available:
                return
                
            memory_data = {
                'type': 'workflow_suggestions',
                'timestamp': time.time(),
                'context': asdict(self.current_context),
                'suggestions': self.workflow_suggestions,
                'active_patterns': len(self.patterns)
            }
            
            result = await integration_manager.execute_integrated_task(
                "memory",
                "Store workflow suggestions",
                memory_data
            )
            
            if result.get("success"):
                self.logger.debug("[SAVE] Suggestions stored in Memento")
                
        except Exception as e:
            self.logger.error(f"[FAIL] Memento storage error: {e}")
            
    async def _check_automation_opportunities(self):
        """Check for automation opportunities and execute if appropriate"""
        try:
            for pattern in self.patterns.values():
                if (pattern.automation_potential > self.config['automation_confidence_threshold'] and
                    pattern.confidence > self.config['pattern_confidence_threshold']):
                    
                    # Check if pattern is currently active
                    if await self._is_pattern_currently_active(pattern):
                        await self._suggest_automation(pattern)
                        
        except Exception as e:
            self.logger.error(f"[FAIL] Automation check error: {e}")
            
    async def _is_pattern_currently_active(self, pattern: WorkflowPattern) -> bool:
        """Check if pattern conditions are currently met"""
        if not self.current_context:
            return False
            
        # Simple heuristic: check if first app in pattern is currently focused
        if pattern.events:
            first_app = pattern.events[0].app_name
            return first_app == self.current_context.focused_app
            
        return False
        
    async def _suggest_automation(self, pattern: WorkflowPattern):
        """Suggest automation for pattern"""
        try:
            if self.charm_tools:
                # Use Charm tools for elegant suggestion UI
                message = f"[AI] Automation Available\n\nPattern: {pattern.name}\nConfidence: {pattern.confidence:.0%}\n\nWould you like to automate this workflow?"
                
                response = await self.charm_tools.gum_confirm(
                    prompt=message
                )
                
                if response:
                    await self._create_automation(pattern)
                    
        except Exception as e:
            self.logger.error(f"[FAIL] Automation suggestion error: {e}")
            
    async def _create_automation(self, pattern: WorkflowPattern):
        """Create automation script for pattern"""
        try:
            # Generate automation script
            script = await self._generate_automation_script(pattern)
            
            if script:
                # Save automation
                automation_id = f"auto_{pattern.pattern_id}_{int(time.time())}"
                
                self.db.execute("""
                    INSERT INTO workflow_automations
                    (automation_id, pattern_id, automation_script, success_rate, last_executed)
                    VALUES (?, ?, ?, ?, ?)
                """, (automation_id, pattern.pattern_id, script, 0.0, 0.0))
                self.db.commit()
                
                self.logger.info(f"[OK] Created automation for pattern: {pattern.name}")
                
                if self.charm_tools:
                    await self.charm_tools.gum_style(
                        text="[OK] Automation created successfully!",
                        foreground="green"
                    )
                    
        except Exception as e:
            self.logger.error(f"[FAIL] Automation creation error: {e}")
            
    async def _generate_automation_script(self, pattern: WorkflowPattern) -> Optional[str]:
        """Generate automation script for pattern"""
        if self.duckbot_ai and DUCKBOT_AVAILABLE:
            try:
                context = {
                    'pattern_name': pattern.name,
                    'events': [
                        {
                            'type': e.event_type,
                            'app': e.app_name,
                            'details': e.details
                        } for e in pattern.events
                    ]
                }
                
                result = await self.duckbot_ai.enhanced_request(
                    "Generate a bash script to automate this workflow pattern",
                    context,
                    preferred_model="local"
                )
                
                if result.get("success"):
                    return result["result"]["content"]
                    
            except Exception as e:
                self.logger.error(f"[FAIL] Script generation error: {e}")
        
        return None
        
    # D-Bus interface methods
    @dbus.service.method('org.duckbot.ContextWorkflows', in_signature='ssss', out_signature='b')
    def RecordEvent(self, event_type: str, app_name: str, details: str, context: str) -> bool:
        """Record a workflow event"""
        try:
            event = WorkflowEvent(
                timestamp=time.time(),
                event_type=event_type,
                app_name=app_name,
                details=json.loads(details) if details else {},
                context=json.loads(context) if context else {}
            )
            
            # Store in database
            self.db.execute("""
                INSERT INTO workflow_events
                (timestamp, event_type, app_name, details, context)
                VALUES (?, ?, ?, ?, ?)
            """, (
                event.timestamp,
                event.event_type,
                event.app_name,
                json.dumps(event.details),
                json.dumps(event.context)
            ))
            self.db.commit()
            
            self.events.append(event)
            
            # Trigger immediate analysis if significant event
            if event_type in ['app_open', 'file_access', 'command_exec']:
                asyncio.create_task(self._analyze_immediate_patterns())
            
            return True
            
        except Exception as e:
            self.logger.error(f"[FAIL] Event recording error: {e}")
            return False
            
    @dbus.service.method('org.duckbot.ContextWorkflows', out_signature='s')
    def GetCurrentSuggestions(self) -> str:
        """Get current workflow suggestions"""
        try:
            return json.dumps(self.workflow_suggestions)
        except Exception as e:
            self.logger.error(f"[FAIL] Suggestions retrieval error: {e}")
            return "[]"
            
    @dbus.service.method('org.duckbot.ContextWorkflows', out_signature='s')
    def GetPatterns(self) -> str:
        """Get all detected patterns"""
        try:
            patterns_data = []
            for pattern in self.patterns.values():
                patterns_data.append({
                    'id': pattern.pattern_id,
                    'name': pattern.name,
                    'frequency': pattern.frequency,
                    'confidence': pattern.confidence,
                    'automation_potential': pattern.automation_potential,
                    'description': pattern.description,
                    'last_seen': pattern.last_seen
                })
            return json.dumps(patterns_data)
        except Exception as e:
            self.logger.error(f"[FAIL] Patterns retrieval error: {e}")
            return "[]"
            
    @dbus.service.method('org.duckbot.ContextWorkflows', out_signature='s')
    def GetCurrentContext(self) -> str:
        """Get current workflow context"""
        try:
            if self.current_context:
                return json.dumps(asdict(self.current_context))
            return "{}"
        except Exception as e:
            self.logger.error(f"[FAIL] Context retrieval error: {e}")
            return "{}"
            
    async def _analyze_immediate_patterns(self):
        """Analyze patterns immediately after significant events"""
        try:
            # Quick pattern check for recent events
            recent_events = self.events[-10:]  # Last 10 events
            if len(recent_events) >= 3:
                sequences = await self._find_event_sequences(recent_events)
                for sequence in sequences:
                    await self._update_or_create_pattern(sequence)
                    
        except Exception as e:
            self.logger.error(f"[FAIL] Immediate analysis error: {e}")

async def main():
    """Main entry point"""
    print("[EMOJI] Starting DuckBot Context-Aware Workflows...")
    
    try:
        # Create and initialize workflows system
        workflows = ContextAwareWorkflows()
        await workflows.initialize()
        
        print("[OK] Context-Aware Workflows started successfully")
        print("[EMOJI] Monitoring workflows and learning patterns...")
        
        # Run main loop
        loop = GLib.MainLoop()
        loop.run()
        
    except KeyboardInterrupt:
        print("\n[EMOJI] Shutting down Context-Aware Workflows...")
    except Exception as e:
        print(f"[FAIL] Fatal error: {e}")
        return 1
        
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))