"""
DuckBot Learning System
Continuous improvement system for agents and system performance
"""

import json
import time
import asyncio
import logging
import threading
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
from collections import defaultdict, deque
import sqlite3
import numpy as np
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

@dataclass
class LearningEvent:
    """Individual learning event record"""
    event_id: str
    timestamp: float
    event_type: str  # "success", "failure", "feedback", "correction"
    agent_type: str
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]
    success_metric: float
    feedback: Optional[str]
    context: Dict[str, Any]
    metadata: Dict[str, Any]

@dataclass
class PerformanceMetrics:
    """Performance metrics for learning analysis"""
    total_events: int
    success_rate: float
    average_confidence: float
    improvement_rate: float
    learning_velocity: float
    pattern_recognition_score: float
    adaptation_speed: float

class LearningDatabase:
    """Database for storing learning events and metrics"""
    
    def __init__(self, db_path: str = "learning_system.db"):
        self.db_path = db_path
        self.lock = threading.Lock()
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize learning database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Learning events table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS learning_events (
                    event_id TEXT PRIMARY KEY,
                    timestamp REAL,
                    event_type TEXT,
                    agent_type TEXT,
                    input_data TEXT,
                    output_data TEXT,
                    success_metric REAL,
                    feedback TEXT,
                    context TEXT,
                    metadata TEXT
                )
            ''')
            
            # Performance metrics table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    metric_id TEXT PRIMARY KEY,
                    agent_type TEXT,
                    timestamp REAL,
                    total_events INTEGER,
                    success_rate REAL,
                    average_confidence REAL,
                    improvement_rate REAL,
                    learning_velocity REAL,
                    pattern_recognition_score REAL,
                    adaptation_speed REAL,
                    metadata TEXT
                )
            ''')
            
            # Learning patterns table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS learned_patterns (
                    pattern_id TEXT PRIMARY KEY,
                    agent_type TEXT,
                    pattern_type TEXT,
                    pattern_data TEXT,
                    confidence REAL,
                    usage_count INTEGER,
                    success_rate REAL,
                    created_at REAL,
                    last_used REAL
                )
            ''')
            
            # Create indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_timestamp ON learning_events(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_agent ON learning_events(agent_type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_metrics_agent ON performance_metrics(agent_type)')
            
            conn.commit()
    
    def store_learning_event(self, event: LearningEvent):
        """Store learning event"""
        with self.lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT OR REPLACE INTO learning_events
                        (event_id, timestamp, event_type, agent_type, input_data,
                         output_data, success_metric, feedback, context, metadata)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        event.event_id,
                        event.timestamp,
                        event.event_type,
                        event.agent_type,
                        json.dumps(event.input_data),
                        json.dumps(event.output_data),
                        event.success_metric,
                        event.feedback,
                        json.dumps(event.context),
                        json.dumps(event.metadata)
                    ))
                    conn.commit()
            except Exception as e:
                logger.error(f"Error storing learning event: {e}")
    
    def get_learning_events(self, agent_type: Optional[str] = None, 
                           event_type: Optional[str] = None,
                           limit: int = 1000) -> List[LearningEvent]:
        """Retrieve learning events"""
        with self.lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    query = "SELECT * FROM learning_events WHERE 1=1"
                    params = []
                    
                    if agent_type:
                        query += " AND agent_type = ?"
                        params.append(agent_type)
                    
                    if event_type:
                        query += " AND event_type = ?"
                        params.append(event_type)
                    
                    query += " ORDER BY timestamp DESC LIMIT ?"
                    params.append(limit)
                    
                    cursor.execute(query, params)
                    
                    events = []
                    for row in cursor.fetchall():
                        events.append(LearningEvent(
                            event_id=row[0],
                            timestamp=row[1],
                            event_type=row[2],
                            agent_type=row[3],
                            input_data=json.loads(row[4]),
                            output_data=json.loads(row[5]),
                            success_metric=row[6],
                            feedback=row[7],
                            context=json.loads(row[8]),
                            metadata=json.loads(row[9])
                        ))
                    
                    return events
            except Exception as e:
                logger.error(f"Error retrieving learning events: {e}")
                return []

class LearningAnalyzer:
    """Analyzes learning events to identify patterns and improvements"""
    
    def __init__(self):
        self.pattern_cache: Dict[str, List[Dict[str, Any]]] = {}
        self.performance_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
    
    def analyze_performance_trends(self, events: List[LearningEvent]) -> Dict[str, Any]:
        """Analyze performance trends from learning events"""
        if not events:
            return {"error": "No events to analyze"}
        
        # Group events by agent type
        agent_events = defaultdict(list)
        for event in events:
            agent_events[event.agent_type].append(event)
        
        trends = {}
        for agent_type, agent_event_list in agent_events.items():
            trends[agent_type] = self._analyze_agent_trends(agent_event_list)
        
        return trends
    
    def _analyze_agent_trends(self, events: List[LearningEvent]) -> Dict[str, Any]:
        """Analyze trends for specific agent"""
        if not events:
            return {}
        
        # Sort by timestamp
        events.sort(key=lambda x: x.timestamp)
        
        # Calculate metrics over time windows
        window_size = max(10, len(events) // 10)  # Adaptive window size
        windows = []
        
        for i in range(0, len(events), window_size):
            window_events = events[i:i+window_size]
            if len(window_events) < 3:  # Skip too small windows
                continue
            
            window_metrics = {
                "timestamp": window_events[-1].timestamp,
                "success_rate": sum(1 for e in window_events if e.success_metric > 0.7) / len(window_events),
                "avg_confidence": sum(e.success_metric for e in window_events) / len(window_events),
                "event_count": len(window_events),
                "feedback_ratio": sum(1 for e in window_events if e.feedback) / len(window_events)
            }
            windows.append(window_metrics)
        
        if len(windows) < 2:
            return {"insufficient_data": True}
        
        # Calculate improvement metrics
        first_window = windows[0]
        last_window = windows[-1]
        
        improvement_rate = (last_window["success_rate"] - first_window["success_rate"]) / len(windows)
        confidence_improvement = (last_window["avg_confidence"] - first_window["avg_confidence"]) / len(windows)
        
        # Calculate learning velocity (how quickly agent improves)
        learning_velocity = 0.0
        if len(windows) > 2:
            velocity_sum = 0
            for i in range(1, len(windows)):
                velocity_sum += windows[i]["success_rate"] - windows[i-1]["success_rate"]
            learning_velocity = velocity_sum / (len(windows) - 1)
        
        return {
            "improvement_rate": improvement_rate,
            "confidence_improvement": confidence_improvement,
            "learning_velocity": learning_velocity,
            "current_success_rate": last_window["success_rate"],
            "current_avg_confidence": last_window["avg_confidence"],
            "total_events": len(events),
            "time_span": events[-1].timestamp - events[0].timestamp,
            "windows_analyzed": len(windows)
        }
    
    def detect_learning_patterns(self, events: List[LearningEvent]) -> List[Dict[str, Any]]:
        """Detect learning patterns from events"""
        patterns = []
        
        # Pattern 1: Input-output correlation patterns
        io_patterns = self._detect_io_patterns(events)
        patterns.extend(io_patterns)
        
        # Pattern 2: Temporal patterns
        temporal_patterns = self._detect_temporal_patterns(events)
        patterns.extend(temporal_patterns)
        
        # Pattern 3: Context-dependent patterns
        context_patterns = self._detect_context_patterns(events)
        patterns.extend(context_patterns)
        
        return patterns
    
    def _detect_io_patterns(self, events: List[LearningEvent]) -> List[Dict[str, Any]]:
        """Detect input-output patterns"""
        patterns = []
        
        # Group events by similar inputs
        input_groups = defaultdict(list)
        for event in events:
            # Simple input similarity based on keys
            input_signature = tuple(sorted(event.input_data.keys()))
            input_groups[input_signature].append(event)
        
        for signature, group_events in input_groups.items():
            if len(group_events) < 5:  # Need minimum events for pattern
                continue
            
            # Analyze success patterns
            success_events = [e for e in group_events if e.success_metric > 0.7]
            if len(success_events) > len(group_events) * 0.6:  # >60% success rate
                pattern = {
                    "type": "input_output_correlation",
                    "input_signature": signature,
                    "success_rate": len(success_events) / len(group_events),
                    "confidence": min(0.95, len(success_events) / 10),  # Confidence based on sample size
                    "sample_size": len(group_events),
                    "description": f"High success pattern for inputs: {signature}"
                }
                patterns.append(pattern)
        
        return patterns
    
    def _detect_temporal_patterns(self, events: List[LearningEvent]) -> List[Dict[str, Any]]:
        """Detect temporal patterns"""
        patterns = []
        
        if len(events) < 20:  # Need sufficient events
            return patterns
        
        # Sort by timestamp
        events.sort(key=lambda x: x.timestamp)
        
        # Detect time-of-day patterns
        hour_success = defaultdict(list)
        for event in events:
            hour = datetime.fromtimestamp(event.timestamp).hour
            hour_success[hour].append(event.success_metric)
        
        # Find hours with significantly higher success rates
        overall_success = sum(e.success_metric for e in events) / len(events)
        
        for hour, metrics in hour_success.items():
            if len(metrics) < 3:  # Skip hours with few events
                continue
            
            hour_avg = sum(metrics) / len(metrics)
            if hour_avg > overall_success + 0.1:  # 10% better than average
                pattern = {
                    "type": "temporal_performance",
                    "hour": hour,
                    "success_rate": hour_avg,
                    "improvement": hour_avg - overall_success,
                    "sample_size": len(metrics),
                    "confidence": min(0.9, len(metrics) / 20),
                    "description": f"Better performance at hour {hour}"
                }
                patterns.append(pattern)
        
        return patterns
    
    def _detect_context_patterns(self, events: List[LearningEvent]) -> List[Dict[str, Any]]:
        """Detect context-dependent patterns"""
        patterns = []
        
        # Group by context features
        context_groups = defaultdict(list)
        for event in events:
            if not event.context:
                continue
            
            # Create context signature from key context features
            context_features = []
            for key, value in event.context.items():
                if isinstance(value, (str, int, float, bool)):
                    context_features.append(f"{key}:{value}")
            
            if context_features:
                signature = tuple(sorted(context_features)[:5])  # Limit to top 5 features
                context_groups[signature].append(event)
        
        for signature, group_events in context_groups.items():
            if len(group_events) < 5:
                continue
            
            success_rate = sum(1 for e in group_events if e.success_metric > 0.7) / len(group_events)
            if success_rate > 0.8:  # High success rate
                pattern = {
                    "type": "context_dependent",
                    "context_signature": signature,
                    "success_rate": success_rate,
                    "sample_size": len(group_events),
                    "confidence": min(0.9, len(group_events) / 15),
                    "description": f"High success in context: {signature[:3]}..."
                }
                patterns.append(pattern)
        
        return patterns
    
    def generate_improvement_recommendations(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate recommendations for improvement"""
        recommendations = []
        
        for agent_type, trends in analysis.items():
            if "insufficient_data" in trends:
                recommendations.append({
                    "agent_type": agent_type,
                    "priority": "low",
                    "recommendation": "Collect more data for meaningful analysis",
                    "action": "continue_monitoring"
                })
                continue
            
            # Check improvement rate
            improvement_rate = trends.get("improvement_rate", 0)
            if improvement_rate < 0:
                recommendations.append({
                    "agent_type": agent_type,
                    "priority": "high",
                    "recommendation": "Agent performance is declining",
                    "action": "investigate_regression",
                    "details": f"Improvement rate: {improvement_rate:.3f}"
                })
            elif improvement_rate < 0.01:  # Very slow learning
                recommendations.append({
                    "agent_type": agent_type,
                    "priority": "medium",
                    "recommendation": "Learning rate is very slow",
                    "action": "adjust_learning_parameters",
                    "details": f"Current rate: {improvement_rate:.4f}"
                })
            
            # Check success rate
            success_rate = trends.get("current_success_rate", 0)
            if success_rate < 0.6:
                recommendations.append({
                    "agent_type": agent_type,
                    "priority": "high",
                    "recommendation": "Low success rate needs attention",
                    "action": "retrain_or_adjust_threshold",
                    "details": f"Success rate: {success_rate:.2%}"
                })
            elif success_rate > 0.9:
                recommendations.append({
                    "agent_type": agent_type,
                    "priority": "low",
                    "recommendation": "Excellent performance, consider increasing difficulty",
                    "action": "increase_challenge_level",
                    "details": f"Success rate: {success_rate:.2%}"
                })
        
        # Sort by priority
        priority_order = {"high": 3, "medium": 2, "low": 1}
        recommendations.sort(key=lambda x: priority_order.get(x["priority"], 0), reverse=True)
        
        return recommendations

class LearningSystem:
    """Main learning system coordinator"""
    
    def __init__(self, db_path: Optional[str] = None):
        self.db = LearningDatabase(db_path or "duckbot_learning.db")
        self.analyzer = LearningAnalyzer()
        self.learning_enabled = True
        self.auto_improvement = True
        self.learning_rate = 0.05
        
        # Background learning task
        self._learning_task = None
        self._start_background_learning()
    
    def _start_background_learning(self):
        """Start background learning task"""
        if self._learning_task is None:
            self._learning_task = asyncio.create_task(self._background_learning_loop())
    
    async def _background_learning_loop(self):
        """Background learning loop"""
        while self.learning_enabled:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                
                # Perform learning analysis
                await self._perform_learning_cycle()
                
            except Exception as e:
                logger.error(f"Error in background learning: {e}")
                await asyncio.sleep(60)  # Wait before retrying
    
    async def _perform_learning_cycle(self):
        """Perform one learning cycle"""
        try:
            # Get recent events (last hour)
            cutoff_time = time.time() - 3600
            recent_events = [
                e for e in self.db.get_learning_events(limit=500)
                if e.timestamp > cutoff_time
            ]
            
            if len(recent_events) < 10:
                return  # Not enough recent data
            
            # Analyze trends
            analysis = self.analyzer.analyze_performance_trends(recent_events)
            
            # Detect patterns
            patterns = self.analyzer.detect_learning_patterns(recent_events)
            
            # Generate recommendations
            recommendations = self.analyzer.generate_improvement_recommendations(analysis)
            
            # Apply auto-improvements if enabled
            if self.auto_improvement:
                await self._apply_improvements(recommendations)
            
            # Log learning results
            logger.info(f"Learning cycle completed: {len(recent_events)} events analyzed, "
                       f"{len(patterns)} patterns found, {len(recommendations)} recommendations")
            
        except Exception as e:
            logger.error(f"Error in learning cycle: {e}")
    
    async def _apply_improvements(self, recommendations: List[Dict[str, Any]]):
        """Apply automatic improvements based on recommendations"""
        for rec in recommendations:
            if rec["priority"] == "high" and rec["action"] in ["adjust_learning_parameters"]:
                try:
                    # Example: adjust learning rate for struggling agents
                    agent_type = rec["agent_type"]
                    logger.info(f"Auto-adjusting parameters for {agent_type}")
                    
                    # This would integrate with the intelligent agents system
                    # to adjust agent parameters based on learning recommendations
                    
                except Exception as e:
                    logger.error(f"Error applying improvement: {e}")
    
    async def record_learning_event(self, event_type: str, agent_type: str, 
                                   input_data: Dict[str, Any], output_data: Dict[str, Any],
                                   success_metric: float, feedback: Optional[str] = None,
                                   context: Optional[Dict[str, Any]] = None):
        """Record a learning event"""
        
        event = LearningEvent(
            event_id=f"{agent_type}_{int(time.time() * 1000)}_{hash(str(input_data)) % 10000}",
            timestamp=time.time(),
            event_type=event_type,
            agent_type=agent_type,
            input_data=input_data,
            output_data=output_data,
            success_metric=success_metric,
            feedback=feedback,
            context=context or {},
            metadata={"learning_rate": self.learning_rate}
        )
        
        self.db.store_learning_event(event)
        
        # Update analyzer cache
        if agent_type not in self.analyzer.performance_history:
            self.analyzer.performance_history[agent_type] = deque(maxlen=1000)
        
        self.analyzer.performance_history[agent_type].append({
            "timestamp": event.timestamp,
            "success_metric": success_metric,
            "event_type": event_type
        })
    
    async def get_learning_report(self, agent_type: Optional[str] = None, 
                                 days: int = 7) -> Dict[str, Any]:
        """Get comprehensive learning report"""
        
        # Get events from specified time period
        cutoff_time = time.time() - (days * 24 * 3600)
        events = [
            e for e in self.db.get_learning_events(agent_type=agent_type, limit=5000)
            if e.timestamp > cutoff_time
        ]
        
        if not events:
            return {"error": "No learning events found"}
        
        # Perform analysis
        trends = self.analyzer.analyze_performance_trends(events)
        patterns = self.analyzer.detect_learning_patterns(events)
        recommendations = self.analyzer.generate_improvement_recommendations(trends)
        
        # Calculate overall metrics
        total_events = len(events)
        success_events = sum(1 for e in events if e.success_metric > 0.7)
        success_rate = success_events / total_events if total_events > 0 else 0
        
        avg_confidence = sum(e.success_metric for e in events) / total_events if total_events > 0 else 0
        
        # Recent vs historical comparison
        recent_events = [e for e in events if e.timestamp > time.time() - (24 * 3600)]
        recent_success = sum(1 for e in recent_events if e.success_metric > 0.7) / max(1, len(recent_events))
        
        return {
            "summary": {
                "total_events": total_events,
                "success_rate": success_rate,
                "average_confidence": avg_confidence,
                "recent_success_rate": recent_success,
                "improvement": recent_success - success_rate if len(recent_events) > 10 else None,
                "time_period_days": days
            },
            "trends": trends,
            "patterns": patterns,
            "recommendations": recommendations,
            "agent_breakdown": self._get_agent_breakdown(events),
            "learning_insights": self._generate_learning_insights(events, trends, patterns)
        }
    
    def _get_agent_breakdown(self, events: List[LearningEvent]) -> Dict[str, Any]:
        """Get breakdown of events by agent type"""
        breakdown = defaultdict(lambda: {"count": 0, "success": 0, "avg_confidence": 0})
        
        for event in events:
            breakdown[event.agent_type]["count"] += 1
            if event.success_metric > 0.7:
                breakdown[event.agent_type]["success"] += 1
            breakdown[event.agent_type]["avg_confidence"] += event.success_metric
        
        # Calculate rates
        for agent_data in breakdown.values():
            if agent_data["count"] > 0:
                agent_data["success_rate"] = agent_data["success"] / agent_data["count"]
                agent_data["avg_confidence"] /= agent_data["count"]
        
        return dict(breakdown)
    
    def _generate_learning_insights(self, events: List[LearningEvent], 
                                   trends: Dict[str, Any], 
                                   patterns: List[Dict[str, Any]]) -> List[str]:
        """Generate human-readable learning insights"""
        insights = []
        
        # Overall performance insights
        if len(events) > 100:
            avg_success = sum(1 for e in events if e.success_metric > 0.7) / len(events)
            if avg_success > 0.8:
                insights.append("🎉 System is performing excellently with high success rates")
            elif avg_success > 0.6:
                insights.append("✅ System performance is good with room for improvement")
            else:
                insights.append("⚠️ System performance needs attention - low success rates detected")
        
        # Agent-specific insights
        for agent_type, trend_data in trends.items():
            if "improvement_rate" in trend_data:
                improvement = trend_data["improvement_rate"]
                if improvement > 0.01:
                    insights.append(f"📈 {agent_type} agent is learning rapidly (improvement: {improvement:.1%})")
                elif improvement < -0.01:
                    insights.append(f"📉 {agent_type} agent performance is declining - investigate needed")
        
        # Pattern insights
        if len(patterns) > 0:
            high_conf_patterns = [p for p in patterns if p.get("confidence", 0) > 0.8]
            if high_conf_patterns:
                insights.append(f"🔍 Discovered {len(high_conf_patterns)} high-confidence learning patterns")
        
        return insights


# Global learning system instance
learning_system = LearningSystem()

# Convenience functions for easy integration
async def record_success(agent_type: str, input_data: Dict[str, Any], 
                        output_data: Dict[str, Any], confidence: float,
                        context: Optional[Dict[str, Any]] = None):
    """Record a successful operation"""
    await learning_system.record_learning_event(
        "success", agent_type, input_data, output_data, confidence, None, context
    )

async def record_failure(agent_type: str, input_data: Dict[str, Any], 
                        error: str, context: Optional[Dict[str, Any]] = None):
    """Record a failed operation"""
    await learning_system.record_learning_event(
        "failure", agent_type, input_data, {"error": error}, 0.0, error, context
    )

async def record_feedback(agent_type: str, input_data: Dict[str, Any], 
                         output_data: Dict[str, Any], feedback: str,
                         success_metric: float, context: Optional[Dict[str, Any]] = None):
    """Record feedback on an operation"""
    await learning_system.record_learning_event(
        "feedback", agent_type, input_data, output_data, success_metric, feedback, context
    )

async def get_learning_insights(agent_type: Optional[str] = None, days: int = 7) -> Dict[str, Any]:
    """Get learning insights and recommendations"""
    return await learning_system.get_learning_report(agent_type, days)