#!/usr/bin/env python3
"""
DuckBot User Behavior Analytics
Advanced user behavior tracking, pattern recognition, and engagement analysis
"""

import asyncio
import json
import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
import pandas as pd
from collections import defaultdict, Counter
from pathlib import Path
import uuid

from analytics_engine import AnalyticsEngine, AnalyticsEvent, AnalyticsEventType

logger = logging.getLogger(__name__)

class UserSegment(Enum):
    """User segmentation types"""
    POWER_USER = "power_user"
    CASUAL_USER = "casual_user"
    NEW_USER = "new_user"
    CHURNED_USER = "churned_user"
    PREMIUM_USER = "premium_user"
    DEVELOPER_USER = "developer_user"

class BehaviorPattern(Enum):
    """Types of behavior patterns"""
    DAILY_PATTERN = "daily_pattern"
    WEEKLY_PATTERN = "weekly_pattern"
    FEATURE_ADOPTION = "feature_adoption"
    USAGE_SPIKE = "usage_spike"
    DECLINING_ENGAGEMENT = "declining_engagement"
    POWER_USAGE = "power_usage"
    EXPLORATORY = "exploratory"

@dataclass
class UserProfile:
    """Comprehensive user profile"""
    user_id: str
    first_seen: datetime
    last_seen: datetime
    total_sessions: int
    total_requests: int
    total_cost: float
    favorite_features: List[str]
    usage_patterns: Dict[str, Any]
    engagement_score: float
    segment: UserSegment
    retention_score: float
    lifetime_value: float
    preferences: Dict[str, Any] = field(default_factory=dict)

@dataclass
class BehaviorInsight:
    """Behavior analysis insight"""
    insight_id: str
    user_id: str
    insight_type: BehaviorPattern
    confidence_score: float
    description: str
    recommendations: List[str]
    discovered_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class EngagementMetrics:
    """User engagement metrics"""
    daily_active_users: int
    weekly_active_users: int
    monthly_active_users: int
    average_session_duration: float
    average_requests_per_session: float
    user_retention_rate: float
    feature_adoption_rate: float
    satisfaction_score: float

class UserBehaviorAnalyzer:
    """Advanced user behavior analytics engine"""

    def __init__(self, analytics_engine: AnalyticsEngine):
        self.analytics_engine = analytics_engine
        self.db_path = analytics_engine.db.db_path
        self.user_profiles: Dict[str, UserProfile] = {}
        self.behavior_patterns: Dict[str, List[BehaviorInsight]] = defaultdict(list)
        self._initialize_analyzer()

    def _initialize_analyzer(self):
        """Initialize the behavior analyzer"""
        # Load existing user profiles
        self._load_user_profiles()
        # Start periodic analysis
        asyncio.create_task(self._periodic_analysis())

    def _load_user_profiles(self):
        """Load existing user profiles from database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    SELECT user_id, first_seen, last_seen, total_sessions,
                           total_requests, total_cost, favorite_features,
                           usage_patterns, engagement_score, segment,
                           retention_score, lifetime_value, preferences
                    FROM user_profiles
                ''')

                for row in cursor.fetchall():
                    user_id = row[0]
                    self.user_profiles[user_id] = UserProfile(
                        user_id=user_id,
                        first_seen=datetime.fromisoformat(row[1]),
                        last_seen=datetime.fromisoformat(row[2]),
                        total_sessions=row[3],
                        total_requests=row[4],
                        total_cost=row[5],
                        favorite_features=json.loads(row[6]) if row[6] else [],
                        usage_patterns=json.loads(row[7]) if row[7] else {},
                        engagement_score=row[8],
                        segment=UserSegment(row[9]) if row[9] else UserSegment.CASUAL_USER,
                        retention_score=row[10],
                        lifetime_value=row[11],
                        preferences=json.loads(row[12]) if row[12] else {}
                    )
        except Exception as e:
            logger.error(f"Error loading user profiles: {e}")

    async def _periodic_analysis(self):
        """Run periodic behavior analysis"""
        while True:
            try:
                await asyncio.sleep(3600)  # Run every hour
                await self._analyze_all_users()
                await self._update_engagement_metrics()
                await self._detect_behavior_patterns()
            except Exception as e:
                logger.error(f"Error in periodic analysis: {e}")

    async def track_user_action(self, user_id: str, action_type: str,
                               feature_name: str = None, metrics: Dict[str, Any] = None,
                               session_id: str = None):
        """Track a user action for behavior analysis"""
        event = AnalyticsEvent(
            event_id=str(uuid.uuid4()),
            event_type=AnalyticsEventType.INTERACTION_EVENT,
            timestamp=datetime.now(),
            user_id=user_id,
            session_id=session_id,
            feature_name=feature_name,
            metrics=metrics or {},
            metadata={'action_type': action_type}
        )

        await self.analytics_engine.track_event(event)

        # Update user profile
        await self._update_user_profile(user_id, event)

    async def _update_user_profile(self, user_id: str, event: AnalyticsEvent):
        """Update user profile based on new event"""
        try:
            if user_id not in self.user_profiles:
                # Create new user profile
                self.user_profiles[user_id] = UserProfile(
                    user_id=user_id,
                    first_seen=event.timestamp,
                    last_seen=event.timestamp,
                    total_sessions=0,
                    total_requests=0,
                    total_cost=0.0,
                    favorite_features=[],
                    usage_patterns={},
                    engagement_score=0.0,
                    segment=UserSegment.NEW_USER,
                    retention_score=0.0,
                    lifetime_value=0.0
                )

            profile = self.user_profiles[user_id]
            profile.last_seen = event.timestamp

            if event.event_type == AnalyticsEventType.FEATURE_USAGE:
                profile.total_requests += 1
                if event.feature_name and event.feature_name not in profile.favorite_features:
                    profile.favorite_features.append(event.feature_name)

                if 'cost' in event.metrics:
                    profile.total_cost += event.metrics['cost']

            # Calculate engagement score
            profile.engagement_score = self._calculate_engagement_score(profile)

            # Update user segment
            profile.segment = self._determine_user_segment(profile)

            # Save profile
            self._save_user_profile(profile)

        except Exception as e:
            logger.error(f"Error updating user profile for {user_id}: {e}")

    def _calculate_engagement_score(self, profile: UserProfile) -> float:
        """Calculate user engagement score (0-100)"""
        now = datetime.now()
        days_since_last_activity = (now - profile.last_seen).days

        # Base score on recency, frequency, and diversity
        recency_score = max(0, 100 - days_since_last_activity * 10)
        frequency_score = min(100, profile.total_requests * 2)
        diversity_score = min(100, len(profile.favorite_features) * 20)
        session_score = min(100, profile.total_sessions * 5)

        # Weighted average
        engagement_score = (
            recency_score * 0.3 +
            frequency_score * 0.3 +
            diversity_score * 0.2 +
            session_score * 0.2
        )

        return min(100, max(0, engagement_score))

    def _determine_user_segment(self, profile: UserProfile) -> UserSegment:
        """Determine user segment based on behavior"""
        now = datetime.now()
        days_since_first = (now - profile.first_seen).days
        days_since_last = (now - profile.last_seen).days

        # Check for churned users
        if days_since_last > 30:
            return UserSegment.CHURNED_USER

        # New users
        if days_since_first < 7:
            return UserSegment.NEW_USER

        # Power users
        if (profile.total_requests > 100 and
            len(profile.favorite_features) > 5 and
            profile.engagement_score > 80):
            return UserSegment.POWER_USER

        # Developer users (based on feature usage)
        dev_features = ['api_usage', 'code_generation', 'development_tools']
        if any(feat in profile.favorite_features for feat in dev_features):
            return UserSegment.DEVELOPER_USER

        # Premium users (high cost users)
        if profile.total_cost > 50:
            return UserSegment.PREMIUM_USER

        # Default to casual user
        return UserSegment.CASUAL_USER

    def _save_user_profile(self, profile: UserProfile):
        """Save user profile to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Create user_profiles table if it doesn't exist
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS user_profiles (
                        user_id TEXT PRIMARY KEY,
                        first_seen DATETIME NOT NULL,
                        last_seen DATETIME NOT NULL,
                        total_sessions INTEGER DEFAULT 0,
                        total_requests INTEGER DEFAULT 0,
                        total_cost REAL DEFAULT 0.0,
                        favorite_features TEXT,
                        usage_patterns TEXT,
                        engagement_score REAL DEFAULT 0.0,
                        segment TEXT,
                        retention_score REAL DEFAULT 0.0,
                        lifetime_value REAL DEFAULT 0.0,
                        preferences TEXT,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                conn.execute('''
                    INSERT OR REPLACE INTO user_profiles
                    (user_id, first_seen, last_seen, total_sessions, total_requests,
                     total_cost, favorite_features, usage_patterns, engagement_score,
                     segment, retention_score, lifetime_value, preferences)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    profile.user_id,
                    profile.first_seen.isoformat(),
                    profile.last_seen.isoformat(),
                    profile.total_sessions,
                    profile.total_requests,
                    profile.total_cost,
                    json.dumps(profile.favorite_features),
                    json.dumps(profile.usage_patterns),
                    profile.engagement_score,
                    profile.segment.value,
                    profile.retention_score,
                    profile.lifetime_value,
                    json.dumps(profile.preferences)
                ))
        except Exception as e:
            logger.error(f"Error saving user profile: {e}")

    async def _analyze_all_users(self):
        """Analyze all users for behavior patterns"""
        try:
            for user_id, profile in self.user_profiles.items():
                await self._analyze_individual_user(user_id, profile)
        except Exception as e:
            logger.error(f"Error analyzing all users: {e}")

    async def _analyze_individual_user(self, user_id: str, profile: UserProfile):
        """Analyze individual user behavior"""
        try:
            # Analyze usage patterns
            patterns = await self._detect_usage_patterns(user_id)
            profile.usage_patterns.update(patterns)

            # Calculate retention score
            profile.retention_score = self._calculate_retention_score(profile)

            # Calculate lifetime value
            profile.lifetime_value = self._calculate_lifetime_value(profile)

            # Update profile
            self._save_user_profile(profile)

        except Exception as e:
            logger.error(f"Error analyzing user {user_id}: {e}")

    async def _detect_usage_patterns(self, user_id: str) -> Dict[str, Any]:
        """Detect usage patterns for a user"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Get hourly usage pattern
                cursor = conn.execute('''
                    SELECT strftime('%H', timestamp) as hour, COUNT(*) as count
                    FROM analytics_events
                    WHERE user_id = ? AND timestamp >= datetime('now', '-30 days')
                    GROUP BY hour
                    ORDER BY hour
                ''', (user_id,))

                hourly_pattern = {row[0]: row[1] for row in cursor.fetchall()}

                # Get daily usage pattern
                cursor = conn.execute('''
                    SELECT strftime('%w', timestamp) as day, COUNT(*) as count
                    FROM analytics_events
                    WHERE user_id = ? AND timestamp >= datetime('now', '-30 days')
                    GROUP BY day
                    ORDER BY day
                ''', (user_id,))

                daily_pattern = {row[0]: row[1] for row in cursor.fetchall()}

                # Get feature adoption timeline
                cursor = conn.execute('''
                    SELECT feature_name, MIN(timestamp) as first_used
                    FROM analytics_events
                    WHERE user_id = ? AND feature_name IS NOT NULL
                    GROUP BY feature_name
                    ORDER BY first_used
                ''', (user_id,))

                feature_adoption = [
                    {'feature': row[0], 'first_used': row[1]}
                    for row in cursor.fetchall()
                ]

                return {
                    'hourly_pattern': hourly_pattern,
                    'daily_pattern': daily_pattern,
                    'feature_adoption': feature_adoption,
                    'analysis_timestamp': datetime.now().isoformat()
                }

        except Exception as e:
            logger.error(f"Error detecting usage patterns for {user_id}: {e}")
            return {}

    def _calculate_retention_score(self, profile: UserProfile) -> float:
        """Calculate user retention score"""
        now = datetime.now()
        days_active = (profile.last_seen - profile.first_seen).days

        if days_active == 0:
            return 0.0

        # Calculate stickiness (sessions per day)
        sessions_per_day = profile.total_sessions / max(days_active, 1)

        # Calculate recency
        days_since_last = (now - profile.last_seen).days
        recency_score = max(0, 100 - days_since_last * 5)

        # Calculate consistency
        consistency_score = min(100, sessions_per_day * 20)

        # Weighted average
        retention_score = (recency_score * 0.6 + consistency_score * 0.4)

        return min(100, max(0, retention_score))

    def _calculate_lifetime_value(self, profile: UserProfile) -> float:
        """Calculate user lifetime value"""
        if profile.total_cost == 0:
            return 0.0

        # Simple LTV calculation based on current spending and engagement
        engagement_multiplier = profile.engagement_score / 100
        retention_multiplier = profile.retention_score / 100

        # Project future value based on current patterns
        projected_annual_value = profile.total_cost * 12  # Monthly to annual
        ltv = projected_annual_value * engagement_multiplier * retention_multiplier

        return ltv

    async def _update_engagement_metrics(self):
        """Update overall engagement metrics"""
        try:
            metrics = self._calculate_engagement_metrics()

            # Store metrics
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS engagement_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        daily_active_users INTEGER,
                        weekly_active_users INTEGER,
                        monthly_active_users INTEGER,
                        average_session_duration REAL,
                        average_requests_per_session REAL,
                        user_retention_rate REAL,
                        feature_adoption_rate REAL,
                        satisfaction_score REAL
                    )
                ''')

                conn.execute('''
                    INSERT INTO engagement_metrics
                    (daily_active_users, weekly_active_users, monthly_active_users,
                     average_session_duration, average_requests_per_session,
                     user_retention_rate, feature_adoption_rate, satisfaction_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    metrics.daily_active_users,
                    metrics.weekly_active_users,
                    metrics.monthly_active_users,
                    metrics.average_session_duration,
                    metrics.average_requests_per_session,
                    metrics.user_retention_rate,
                    metrics.feature_adoption_rate,
                    metrics.satisfaction_score
                ))

        except Exception as e:
            logger.error(f"Error updating engagement metrics: {e}")

    def _calculate_engagement_metrics(self) -> EngagementMetrics:
        """Calculate comprehensive engagement metrics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Daily active users (last 24 hours)
                cursor = conn.execute('''
                    SELECT COUNT(DISTINCT user_id)
                    FROM analytics_events
                    WHERE timestamp >= datetime('now', '-1 day')
                ''')
                daily_active = cursor.fetchone()[0] or 0

                # Weekly active users (last 7 days)
                cursor = conn.execute('''
                    SELECT COUNT(DISTINCT user_id)
                    FROM analytics_events
                    WHERE timestamp >= datetime('now', '-7 days')
                ''')
                weekly_active = cursor.fetchone()[0] or 0

                # Monthly active users (last 30 days)
                cursor = conn.execute('''
                    SELECT COUNT(DISTINCT user_id)
                    FROM analytics_events
                    WHERE timestamp >= datetime('now', '-30 days')
                ''')
                monthly_active = cursor.fetchone()[0] or 0

                # Average session duration
                cursor = conn.execute('''
                    SELECT AVG(session_duration)
                    FROM user_sessions
                    WHERE session_duration IS NOT NULL
                    AND start_time >= datetime('now', '-30 days')
                ''')
                avg_duration = cursor.fetchone()[0] or 0.0

                # Average requests per session
                cursor = conn.execute('''
                    SELECT AVG(total_requests)
                    FROM user_sessions
                    WHERE start_time >= datetime('now', '-30 days')
                ''')
                avg_requests = cursor.fetchone()[0] or 0.0

                # User retention rate (simplified)
                cursor = conn.execute('''
                    SELECT COUNT(DISTINCT user_id)
                    FROM analytics_events
                    WHERE timestamp >= datetime('now', '-30 days')
                    AND user_id IN (
                        SELECT DISTINCT user_id
                        FROM analytics_events
                        WHERE timestamp BETWEEN datetime('now', '-60 days') AND datetime('now', '-30 days')
                    )
                ''')
                retained_users = cursor.fetchone()[0] or 0

                cursor = conn.execute('''
                    SELECT COUNT(DISTINCT user_id)
                    FROM analytics_events
                    WHERE timestamp BETWEEN datetime('now', '-60 days') AND datetime('now', '-30 days')
                ''')
                total_users = cursor.fetchone()[0] or 1

                retention_rate = (retained_users / total_users * 100) if total_users > 0 else 0.0

                # Feature adoption rate
                cursor = conn.execute('''
                    SELECT COUNT(DISTINCT feature_name)
                    FROM analytics_events
                    WHERE feature_name IS NOT NULL
                    AND timestamp >= datetime('now', '-30 days')
                ''')
                adopted_features = cursor.fetchone()[0] or 0

                cursor = conn.execute('''
                    SELECT COUNT(DISTINCT feature_name)
                    FROM analytics_events
                    WHERE feature_name IS NOT NULL
                ''')
                total_features = cursor.fetchone()[0] or 1

                adoption_rate = (adopted_features / total_features * 100) if total_features > 0 else 0.0

                # Satisfaction score (based on engagement scores)
                cursor = conn.execute('''
                    SELECT AVG(engagement_score)
                    FROM user_profiles
                ''')
                satisfaction = cursor.fetchone()[0] or 0.0

                return EngagementMetrics(
                    daily_active_users=daily_active,
                    weekly_active_users=weekly_active,
                    monthly_active_users=monthly_active,
                    average_session_duration=avg_duration,
                    average_requests_per_session=avg_requests,
                    user_retention_rate=retention_rate,
                    feature_adoption_rate=adoption_rate,
                    satisfaction_score=satisfaction
                )

        except Exception as e:
            logger.error(f"Error calculating engagement metrics: {e}")
            return EngagementMetrics(0, 0, 0, 0.0, 0.0, 0.0, 0.0, 0.0)

    async def _detect_behavior_patterns(self):
        """Detect behavior patterns across all users"""
        try:
            for user_id, profile in self.user_profiles.items():
                patterns = await self._analyze_user_patterns(user_id, profile)
                self.behavior_patterns[user_id] = patterns

                # Store patterns in database
                self._store_behavior_patterns(user_id, patterns)

        except Exception as e:
            logger.error(f"Error detecting behavior patterns: {e}")

    async def _analyze_user_patterns(self, user_id: str, profile: UserProfile) -> List[BehaviorInsight]:
        """Analyze behavior patterns for a specific user"""
        patterns = []

        try:
            # Detect daily pattern
            if self._has_consistent_daily_usage(user_id):
                patterns.append(BehaviorInsight(
                    insight_id=str(uuid.uuid4()),
                    user_id=user_id,
                    insight_type=BehaviorPattern.DAILY_PATTERN,
                    confidence_score=0.8,
                    description="User shows consistent daily usage patterns",
                    recommendations=["Schedule regular updates", "Offer daily features"],
                    discovered_at=datetime.now()
                ))

            # Detect power usage
            if profile.total_requests > 50 and profile.engagement_score > 70:
                patterns.append(BehaviorInsight(
                    insight_id=str(uuid.uuid4()),
                    user_id=user_id,
                    insight_type=BehaviorPattern.POWER_USAGE,
                    confidence_score=0.9,
                    description="User is a power user with high engagement",
                    recommendations=["Offer advanced features", "Provide premium support"],
                    discovered_at=datetime.now()
                ))

            # Detect exploratory behavior
            if len(profile.favorite_features) > 10:
                patterns.append(BehaviorInsight(
                    insight_id=str(uuid.uuid4()),
                    user_id=user_id,
                    insight_type=BehaviorPattern.EXPLORATORY,
                    confidence_score=0.7,
                    description="User explores many different features",
                    recommendations=["Show feature recommendations", "Provide tutorials"],
                    discovered_at=datetime.now()
                ))

            # Detect declining engagement
            if self._has_declining_engagement(user_id):
                patterns.append(BehaviorInsight(
                    insight_id=str(uuid.uuid4()),
                    user_id=user_id,
                    insight_type=BehaviorPattern.DECLINING_ENGAGEMENT,
                    confidence_score=0.6,
                    description="User engagement is declining",
                    recommendations=["Send re-engagement campaigns", "Offer personalized content"],
                    discovered_at=datetime.now()
                ))

        except Exception as e:
            logger.error(f"Error analyzing patterns for user {user_id}: {e}")

        return patterns

    def _has_consistent_daily_usage(self, user_id: str) -> bool:
        """Check if user has consistent daily usage"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    SELECT COUNT(DISTINCT DATE(timestamp)) as active_days
                    FROM analytics_events
                    WHERE user_id = ? AND timestamp >= datetime('now', '-7 days')
                ''', (user_id,))

                active_days = cursor.fetchone()[0] or 0
                return active_days >= 5  # Active at least 5 out of 7 days

        except Exception as e:
            logger.error(f"Error checking daily usage for {user_id}: {e}")
            return False

    def _has_declining_engagement(self, user_id: str) -> bool:
        """Check if user engagement is declining"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Compare recent usage with previous period
                cursor = conn.execute('''
                    SELECT COUNT(*) as recent_count
                    FROM analytics_events
                    WHERE user_id = ? AND timestamp >= datetime('now', '-7 days')
                ''', (user_id,))

                recent_count = cursor.fetchone()[0] or 0

                cursor = conn.execute('''
                    SELECT COUNT(*) as previous_count
                    FROM analytics_events
                    WHERE user_id = ? AND timestamp BETWEEN datetime('now', '-14 days') AND datetime('now', '-7 days')
                ''', (user_id,))

                previous_count = cursor.fetchone()[0] or 0

                if previous_count == 0:
                    return False

                decline_rate = (previous_count - recent_count) / previous_count
                return decline_rate > 0.3  # 30% decline

        except Exception as e:
            logger.error(f"Error checking engagement decline for {user_id}: {e}")
            return False

    def _store_behavior_patterns(self, user_id: str, patterns: List[BehaviorInsight]):
        """Store behavior patterns in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                for pattern in patterns:
                    conn.execute('''
                        INSERT OR REPLACE INTO user_behavior_patterns
                        (user_id, pattern_type, pattern_data, confidence_score, last_observed)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (
                        user_id,
                        pattern.insight_type.value,
                        json.dumps({
                            'description': pattern.description,
                            'recommendations': pattern.recommendations,
                            'metadata': pattern.metadata
                        }),
                        pattern.confidence_score,
                        pattern.discovered_at
                    ))

        except Exception as e:
            logger.error(f"Error storing behavior patterns for {user_id}: {e}")

    # Public API Methods
    def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """Get user profile"""
        return self.user_profiles.get(user_id)

    def get_user_insights(self, user_id: str) -> List[BehaviorInsight]:
        """Get behavior insights for a user"""
        return self.behavior_patterns.get(user_id, [])

    def get_segment_distribution(self) -> Dict[UserSegment, int]:
        """Get distribution of users across segments"""
        distribution = defaultdict(int)
        for profile in self.user_profiles.values():
            distribution[profile.segment] += 1
        return dict(distribution)

    def get_top_engaged_users(self, limit: int = 10) -> List[Tuple[str, float]]:
        """Get top engaged users by engagement score"""
        users = [(user_id, profile.engagement_score)
                for user_id, profile in self.user_profiles.items()]
        return sorted(users, key=lambda x: x[1], reverse=True)[:limit]

    def get_feature_popularity_by_segment(self, segment: UserSegment) -> Dict[str, int]:
        """Get feature popularity within a user segment"""
        feature_counts = defaultdict(int)

        for profile in self.user_profiles.values():
            if profile.segment == segment:
                for feature in profile.favorite_features:
                    feature_counts[feature] += 1

        return dict(feature_counts)

    def get_user_journey_map(self, user_id: str) -> Dict[str, Any]:
        """Get user journey map showing feature adoption timeline"""
        if user_id not in self.user_profiles:
            return {}

        profile = self.user_profiles[user_id]
        return {
            'user_id': user_id,
            'segment': profile.segment.value,
            'first_seen': profile.first_seen.isoformat(),
            'feature_adoption': profile.usage_patterns.get('feature_adoption', []),
            'engagement_trend': self._calculate_engagement_trend(user_id),
            'milestones': self._identify_user_milestones(profile)
        }

    def _calculate_engagement_trend(self, user_id: str) -> List[Dict[str, Any]]:
        """Calculate engagement trend over time"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    SELECT DATE(timestamp) as date, COUNT(*) as activity_count
                    FROM analytics_events
                    WHERE user_id = ? AND timestamp >= datetime('now', '-30 days')
                    GROUP BY DATE(timestamp)
                    ORDER BY date
                ''', (user_id,))

                return [{'date': row[0], 'activity_count': row[1]}
                        for row in cursor.fetchall()]

        except Exception as e:
            logger.error(f"Error calculating engagement trend for {user_id}: {e}")
            return []

    def _identify_user_milestones(self, profile: UserProfile) -> List[Dict[str, Any]]:
        """Identify key milestones in user journey"""
        milestones = []

        # First session milestone
        milestones.append({
            'type': 'first_session',
            'date': profile.first_seen.isoformat(),
            'description': 'User joined DuckBot'
        })

        # Power user milestone
        if profile.total_requests >= 100:
            milestones.append({
                'type': 'power_user',
                'date': profile.last_seen.isoformat(),
                'description': 'Achieved power user status'
            })

        # Feature adoption milestones
        if len(profile.favorite_features) >= 10:
            milestones.append({
                'type': 'feature_explorer',
                'date': profile.last_seen.isoformat(),
                'description': 'Explored 10+ features'
            })

        return milestones