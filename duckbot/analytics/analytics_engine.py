#!/usr/bin/env python3
"""
DuckBot Advanced Analytics System
Comprehensive analytics engine for user behavior, performance, and business intelligence
"""

import asyncio
import json
import logging
import sqlite3
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum
import numpy as np
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AnalyticsEventType(Enum):
    """Types of analytics events"""
    USER_SESSION_START = "user_session_start"
    USER_SESSION_END = "user_session_end"
    FEATURE_USAGE = "feature_usage"
    API_REQUEST = "api_request"
    ERROR_OCCURRED = "error_occurred"
    PERFORMANCE_METRIC = "performance_metric"
    COST_EVENT = "cost_event"
    MODEL_USAGE = "model_usage"
    SYSTEM_EVENT = "system_event"
    INTERACTION_EVENT = "interaction_event"

@dataclass
class AnalyticsEvent:
    """Analytics event data structure"""
    event_id: str
    event_type: AnalyticsEventType
    timestamp: datetime
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    feature_name: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            'event_id': self.event_id,
            'event_type': self.event_type.value,
            'timestamp': self.timestamp.isoformat(),
            'user_id': self.user_id,
            'session_id': self.session_id,
            'feature_name': self.feature_name,
            'metrics': json.dumps(self.metrics),
            'metadata': json.dumps(self.metadata)
        }

@dataclass
class UserSession:
    """User session tracking"""
    session_id: str
    user_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    features_used: List[str] = field(default_factory=list)
    total_requests: int = 0
    total_cost: float = 0.0
    session_duration: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def end_session(self):
        """End the session and calculate duration"""
        self.end_time = datetime.now()
        self.session_duration = (self.end_time - self.start_time).total_seconds()

@dataclass
class FeatureUsage:
    """Feature usage analytics"""
    feature_name: str
    usage_count: int
    unique_users: int
    total_cost: float
    average_cost_per_use: float
    success_rate: float
    average_response_time: float
    last_used: datetime
    user_satisfaction: float = 0.0
    popularity_score: float = 0.0

@dataclass
class PerformanceMetrics:
    """System performance metrics"""
    timestamp: datetime
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_io: Dict[str, float]
    api_response_times: Dict[str, float]
    error_rates: Dict[str, float]
    throughput: float
    system_load: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp.isoformat(),
            'cpu_usage': self.cpu_usage,
            'memory_usage': self.memory_usage,
            'disk_usage': self.disk_usage,
            'network_io': json.dumps(self.network_io),
            'api_response_times': json.dumps(self.api_response_times),
            'error_rates': json.dumps(self.error_rates),
            'throughput': self.throughput,
            'system_load': self.system_load
        }

class AnalyticsDatabase:
    """Database manager for analytics data"""

    def __init__(self, db_path: str = None):
        self.db_path = db_path or str(Path(__file__).parent / "analytics.db")
        self.lock = threading.Lock()
        self._init_database()

    def _init_database(self):
        """Initialize analytics database tables"""
        with sqlite3.connect(self.db_path) as conn:
            # Events table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS analytics_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT UNIQUE,
                    event_type TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    user_id TEXT,
                    session_id TEXT,
                    feature_name TEXT,
                    metrics TEXT,
                    metadata TEXT
                )
            ''')

            # User sessions table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS user_sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    start_time DATETIME NOT NULL,
                    end_time DATETIME,
                    features_used TEXT,
                    total_requests INTEGER DEFAULT 0,
                    total_cost REAL DEFAULT 0.0,
                    session_duration REAL,
                    metadata TEXT
                )
            ''')

            # Feature usage table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS feature_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    feature_name TEXT NOT NULL,
                    usage_count INTEGER DEFAULT 0,
                    unique_users INTEGER DEFAULT 0,
                    total_cost REAL DEFAULT 0.0,
                    average_cost_per_use REAL DEFAULT 0.0,
                    success_rate REAL DEFAULT 0.0,
                    average_response_time REAL DEFAULT 0.0,
                    last_used DATETIME,
                    user_satisfaction REAL DEFAULT 0.0,
                    popularity_score REAL DEFAULT 0.0,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(feature_name)
                )
            ''')

            # Performance metrics table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    cpu_usage REAL,
                    memory_usage REAL,
                    disk_usage REAL,
                    network_io TEXT,
                    api_response_times TEXT,
                    error_rates TEXT,
                    throughput REAL,
                    system_load REAL
                )
            ''')

            # User behavior patterns table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS user_behavior_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    pattern_type TEXT NOT NULL,
                    pattern_data TEXT,
                    confidence_score REAL,
                    last_observed DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Predictive insights table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS predictive_insights (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    insight_type TEXT NOT NULL,
                    prediction_data TEXT,
                    confidence_score REAL,
                    time_horizon TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE
                )
            ''')

            # Business intelligence table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS business_intelligence (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_name TEXT NOT NULL,
                    metric_value REAL,
                    metric_type TEXT,
                    time_period TEXT,
                    trend_data TEXT,
                    insights TEXT,
                    recommendations TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Create indexes for better performance
            indexes = [
                'CREATE INDEX IF NOT EXISTS idx_events_timestamp ON analytics_events(timestamp)',
                'CREATE INDEX IF NOT EXISTS idx_events_type ON analytics_events(event_type)',
                'CREATE INDEX IF NOT EXISTS idx_events_user ON analytics_events(user_id)',
                'CREATE INDEX IF NOT EXISTS idx_sessions_user ON user_sessions(user_id)',
                'CREATE INDEX IF NOT EXISTS idx_performance_timestamp ON performance_metrics(timestamp)',
                'CREATE INDEX IF NOT EXISTS idx_feature_name ON feature_usage(feature_name)'
            ]

            for index_sql in indexes:
                conn.execute(index_sql)

class AdvancedAnalyticsEngine:
    """Main analytics engine for DuckBot"""

    def __init__(self, db_path: str = None):
        self.db = AnalyticsDatabase(db_path)
        self.active_sessions: Dict[str, UserSession] = {}
        self.event_queue = asyncio.Queue()
        self.is_running = False
        self.executor = ThreadPoolExecutor(max_workers=4)
        self._start_event_processor()

    def _start_event_processor(self):
        """Start the event processing loop"""
        def process_events():
            while True:
                try:
                    event = asyncio.run(self.event_queue.get())
                    self._process_event(event)
                except Exception as e:
                    logger.error(f"Error processing analytics event: {e}")

        threading.Thread(target=process_events, daemon=True).start()

    async def track_event(self, event: AnalyticsEvent):
        """Track an analytics event"""
        await self.event_queue.put(event)

    def _process_event(self, event: AnalyticsEvent):
        """Process a single analytics event"""
        try:
            # Store event in database
            self._store_event(event)

            # Update session if applicable
            if event.session_id and event.session_id in self.active_sessions:
                self._update_session_from_event(event)

            # Update feature usage
            if event.feature_name:
                self._update_feature_usage(event)

            # Process specific event types
            if event.event_type == AnalyticsEventType.USER_SESSION_START:
                self._handle_session_start(event)
            elif event.event_type == AnalyticsEventType.USER_SESSION_END:
                self._handle_session_end(event)
            elif event.event_type == AnalyticsEventType.PERFORMANCE_METRIC:
                self._handle_performance_metric(event)

        except Exception as e:
            logger.error(f"Error processing event {event.event_id}: {e}")

    def _store_event(self, event: AnalyticsEvent):
        """Store event in database"""
        with sqlite3.connect(self.db.db_path) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO analytics_events
                (event_id, event_type, timestamp, user_id, session_id, feature_name, metrics, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                event.event_id,
                event.event_type.value,
                event.timestamp,
                event.user_id,
                event.session_id,
                event.feature_name,
                json.dumps(event.metrics),
                json.dumps(event.metadata)
            ))

    def _update_session_from_event(self, event: AnalyticsEvent):
        """Update session data from event"""
        session = self.active_sessions[event.session_id]

        if event.feature_name and event.feature_name not in session.features_used:
            session.features_used.append(event.feature_name)

        session.total_requests += 1

        if 'cost' in event.metrics:
            session.total_cost += event.metrics['cost']

    def _update_feature_usage(self, event: AnalyticsEvent):
        """Update feature usage statistics"""
        with sqlite3.connect(self.db.db_path) as conn:
            # Check if feature exists
            cursor = conn.execute('''
                SELECT usage_count, total_cost, unique_users
                FROM feature_usage WHERE feature_name = ?
            ''', (event.feature_name,))

            result = cursor.fetchone()

            if result:
                usage_count, total_cost, unique_users = result
                new_usage_count = usage_count + 1
                new_total_cost = total_cost + event.metrics.get('cost', 0.0)

                # Check if this is a new user for this feature
                if event.user_id:
                    cursor = conn.execute('''
                        SELECT COUNT(DISTINCT user_id)
                        FROM analytics_events
                        WHERE feature_name = ? AND user_id = ?
                    ''', (event.feature_name, event.user_id))
                    user_count = cursor.fetchone()[0]
                    if user_count == 1:  # First time this user used this feature
                        new_unique_users = unique_users + 1
                    else:
                        new_unique_users = unique_users
                else:
                    new_unique_users = unique_users

                avg_cost = new_total_cost / new_usage_count if new_usage_count > 0 else 0.0

                conn.execute('''
                    UPDATE feature_usage
                    SET usage_count = ?, total_cost = ?, unique_users = ?,
                        average_cost_per_use = ?, last_used = ?
                    WHERE feature_name = ?
                ''', (new_usage_count, new_total_cost, new_unique_users,
                      avg_cost, datetime.now(), event.feature_name))
            else:
                # Create new feature usage record
                conn.execute('''
                    INSERT INTO feature_usage
                    (feature_name, usage_count, unique_users, total_cost,
                     average_cost_per_use, last_used)
                    VALUES (?, 1, 1, ?, ?, ?)
                ''', (event.feature_name, event.metrics.get('cost', 0.0),
                      event.metrics.get('cost', 0.0), datetime.now()))

    def _handle_session_start(self, event: AnalyticsEvent):
        """Handle user session start"""
        session = UserSession(
            session_id=event.session_id,
            user_id=event.user_id,
            start_time=event.timestamp,
            metadata=event.metadata
        )
        self.active_sessions[event.session_id] = session

        # Store session in database
        with sqlite3.connect(self.db.db_path) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO user_sessions
                (session_id, user_id, start_time, metadata)
                VALUES (?, ?, ?, ?)
            ''', (event.session_id, event.user_id, event.timestamp,
                  json.dumps(event.metadata)))

    def _handle_session_end(self, event: AnalyticsEvent):
        """Handle user session end"""
        if event.session_id in self.active_sessions:
            session = self.active_sessions[event.session_id]
            session.end_session()

            # Update session in database
            with sqlite3.connect(self.db.db_path) as conn:
                conn.execute('''
                    UPDATE user_sessions
                    SET end_time = ?, session_duration = ?, features_used = ?,
                        total_requests = ?, total_cost = ?
                    WHERE session_id = ?
                ''', (session.end_time, session.session_duration,
                      json.dumps(session.features_used),
                      session.total_requests, session.total_cost,
                      event.session_id))

            # Remove from active sessions
            del self.active_sessions[event.session_id]

    def _handle_performance_metric(self, event: AnalyticsEvent):
        """Handle performance metrics"""
        metrics = event.metrics

        perf_metrics = PerformanceMetrics(
            timestamp=event.timestamp,
            cpu_usage=metrics.get('cpu_usage', 0.0),
            memory_usage=metrics.get('memory_usage', 0.0),
            disk_usage=metrics.get('disk_usage', 0.0),
            network_io=metrics.get('network_io', {}),
            api_response_times=metrics.get('api_response_times', {}),
            error_rates=metrics.get('error_rates', {}),
            throughput=metrics.get('throughput', 0.0),
            system_load=metrics.get('system_load', 0.0)
        )

        # Store performance metrics
        with sqlite3.connect(self.db.db_path) as conn:
            conn.execute('''
                INSERT INTO performance_metrics
                (timestamp, cpu_usage, memory_usage, disk_usage, network_io,
                 api_response_times, error_rates, throughput, system_load)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                perf_metrics.timestamp,
                perf_metrics.cpu_usage,
                perf_metrics.memory_usage,
                perf_metrics.disk_usage,
                json.dumps(perf_metrics.network_io),
                json.dumps(perf_metrics.api_response_times),
                json.dumps(perf_metrics.error_rates),
                perf_metrics.throughput,
                perf_metrics.system_load
            ))

    # Analytics Query Methods
    def get_user_behavior_analytics(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get comprehensive user behavior analytics"""
        start_date = datetime.now() - timedelta(days=days)

        with sqlite3.connect(self.db.db_path) as conn:
            # Session analytics
            cursor = conn.execute('''
                SELECT COUNT(*) as session_count,
                       AVG(session_duration) as avg_duration,
                       SUM(total_cost) as total_cost,
                       AVG(total_requests) as avg_requests_per_session
                FROM user_sessions
                WHERE user_id = ? AND start_time >= ?
            ''', (user_id, start_date))

            session_data = cursor.fetchone()

            # Feature usage patterns
            cursor = conn.execute('''
                SELECT feature_name, COUNT(*) as usage_count
                FROM analytics_events
                WHERE user_id = ? AND timestamp >= ? AND feature_name IS NOT NULL
                GROUP BY feature_name
                ORDER BY usage_count DESC
                LIMIT 10
            ''', (user_id, start_date))

            feature_usage = cursor.fetchall()

            # Time-based usage patterns
            cursor = conn.execute('''
                SELECT strftime('%H', timestamp) as hour, COUNT(*) as count
                FROM analytics_events
                WHERE user_id = ? AND timestamp >= ?
                GROUP BY hour
                ORDER BY hour
            ''', (user_id, start_date))

            hourly_usage = cursor.fetchall()

            return {
                'user_id': user_id,
                'period_days': days,
                'session_analytics': {
                    'total_sessions': session_data[0] or 0,
                    'average_session_duration': session_data[1] or 0.0,
                    'total_cost': session_data[2] or 0.0,
                    'average_requests_per_session': session_data[3] or 0.0
                },
                'top_features': [{'feature': row[0], 'usage_count': row[1]}
                               for row in feature_usage],
                'hourly_usage_pattern': [{'hour': row[0], 'count': row[1]}
                                        for row in hourly_usage]
            }

    def get_feature_popularity(self, days: int = 30) -> List[FeatureUsage]:
        """Get feature popularity analytics"""
        start_date = datetime.now() - timedelta(days=days)

        with sqlite3.connect(self.db.db_path) as conn:
            cursor = conn.execute('''
                SELECT feature_name, usage_count, unique_users, total_cost,
                       average_cost_per_use, success_rate, average_response_time,
                       last_used, user_satisfaction, popularity_score
                FROM feature_usage
                WHERE last_used >= ?
                ORDER BY usage_count DESC
            ''', (start_date,))

            features = []
            for row in cursor.fetchall():
                features.append(FeatureUsage(*row))

            return features

    def get_performance_trends(self, days: int = 7) -> Dict[str, Any]:
        """Get performance trend analytics"""
        start_date = datetime.now() - timedelta(days=days)

        with sqlite3.connect(self.db.db_path) as conn:
            cursor = conn.execute('''
                SELECT AVG(cpu_usage) as avg_cpu,
                       AVG(memory_usage) as avg_memory,
                       AVG(disk_usage) as avg_disk,
                       AVG(throughput) as avg_throughput,
                       AVG(system_load) as avg_load
                FROM performance_metrics
                WHERE timestamp >= ?
            ''', (start_date,))

            averages = cursor.fetchone()

            # Hourly trends
            cursor = conn.execute('''
                SELECT strftime('%Y-%m-%d %H', timestamp) as hour_bucket,
                       AVG(cpu_usage) as avg_cpu,
                       AVG(memory_usage) as avg_memory,
                       AVG(throughput) as avg_throughput
                FROM performance_metrics
                WHERE timestamp >= ?
                GROUP BY hour_bucket
                ORDER BY hour_bucket
            ''', (start_date))

            hourly_trends = cursor.fetchall()

            return {
                'period_days': days,
                'overall_averages': {
                    'cpu_usage': averages[0] or 0.0,
                    'memory_usage': averages[1] or 0.0,
                    'disk_usage': averages[2] or 0.0,
                    'throughput': averages[3] or 0.0,
                    'system_load': averages[4] or 0.0
                },
                'hourly_trends': [
                    {
                        'hour': row[0],
                        'cpu_usage': row[1],
                        'memory_usage': row[2],
                        'throughput': row[3]
                    } for row in hourly_trends
                ]
            }

    def generate_business_intelligence(self, days: int = 30) -> Dict[str, Any]:
        """Generate business intelligence insights"""
        start_date = datetime.now() - timedelta(days=days)

        with sqlite3.connect(self.db.db_path) as conn:
            # Cost analysis
            cursor = conn.execute('''
                SELECT SUM(total_cost) as total_cost,
                       COUNT(DISTINCT user_id) as active_users,
                       COUNT(*) as total_events
                FROM analytics_events
                WHERE timestamp >= ?
            ''', (start_date,))

            cost_data = cursor.fetchone()

            # Feature efficiency
            cursor = conn.execute('''
                SELECT feature_name, usage_count, total_cost,
                       (usage_count * 1.0 / NULLIF(total_cost, 0)) as efficiency
                FROM feature_usage
                WHERE last_used >= ?
                ORDER BY efficiency DESC
                LIMIT 10
            ''', (start_date))

            feature_efficiency = cursor.fetchall()

            # User engagement trends
            cursor = conn.execute('''
                SELECT DATE(start_time) as date,
                       COUNT(DISTINCT user_id) as daily_active_users,
                       COUNT(*) as daily_sessions,
                       AVG(session_duration) as avg_session_duration
                FROM user_sessions
                WHERE start_time >= ?
                GROUP BY date
                ORDER BY date
            ''', (start_date,))

            engagement_trends = cursor.fetchall()

            return {
                'period_days': days,
                'cost_analysis': {
                    'total_cost': cost_data[0] or 0.0,
                    'active_users': cost_data[1] or 0,
                    'total_events': cost_data[2] or 0,
                    'cost_per_user': (cost_data[0] or 0.0) / max(cost_data[1] or 1, 1),
                    'cost_per_event': (cost_data[0] or 0.0) / max(cost_data[2] or 1, 1)
                },
                'feature_efficiency': [
                    {
                        'feature': row[0],
                        'usage_count': row[1],
                        'total_cost': row[2],
                        'efficiency_score': row[3]
                    } for row in feature_efficiency
                ],
                'engagement_trends': [
                    {
                        'date': row[0],
                        'daily_active_users': row[1],
                        'daily_sessions': row[2],
                        'avg_session_duration': row[3]
                    } for row in engagement_trends
                ]
            }

    def cleanup_old_data(self, retention_days: int = 90):
        """Clean up old analytics data"""
        cutoff_date = datetime.now() - timedelta(days=retention_days)

        with sqlite3.connect(self.db.db_path) as conn:
            tables = ['analytics_events', 'performance_metrics']
            for table in tables:
                conn.execute(f'DELETE FROM {table} WHERE timestamp < ?', (cutoff_date,))

            # Keep feature usage data but update last_used
            conn.execute('''
                UPDATE feature_usage
                SET usage_count = 0, unique_users = 0, total_cost = 0.0,
                    average_cost_per_use = 0.0
                WHERE last_used < ?
            ''', (cutoff_date,))

        logger.info(f"Cleaned up analytics data older than {retention_days} days")

# Global analytics engine instance
analytics_engine = AdvancedAnalyticsEngine()