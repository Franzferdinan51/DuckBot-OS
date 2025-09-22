#!/usr/bin/env python3
"""
DuckBot Analytics Integration
Central integration layer for all analytics components
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

from analytics_engine import AnalyticsEngine, AnalyticsEvent, AnalyticsEventType
from user_behavior_analytics import UserBehaviorAnalyzer
from performance_analytics import PerformanceAnalyzer
from business_intelligence import BusinessIntelligenceEngine
from realtime_dashboard import RealtimeAnalyticsDashboard
from predictive_analytics import PredictiveAnalyticsEngine

logger = logging.getLogger(__name__)

class AnalyticsIntegration:
    """Central analytics integration point for DuckBot"""

    def __init__(self, db_path: str = None):
        # Initialize all analytics components
        self.analytics_engine = AnalyticsEngine(db_path)
        self.user_analyzer = UserBehaviorAnalyzer(self.analytics_engine)
        self.performance_analyzer = PerformanceAnalyzer(self.analytics_engine)
        self.bi_engine = BusinessIntelligenceEngine(self.analytics_engine)
        self.predictive_engine = PredictiveAnalyticsEngine(self.analytics_engine)

        # Initialize real-time dashboard
        self.dashboard = RealtimeAnalyticsDashboard(
            self.analytics_engine,
            self.user_analyzer,
            self.performance_analyzer,
            self.bi_engine
        )

        self.is_initialized = True
        logger.info("DuckBot Analytics System initialized successfully")

    # User Behavior Tracking
    async def track_user_session_start(self, user_id: str, session_id: str, metadata: Dict[str, Any] = None):
        """Track user session start"""
        event = AnalyticsEvent(
            event_id=str(uuid.uuid4()),
            event_type=AnalyticsEventType.USER_SESSION_START,
            timestamp=datetime.now(),
            user_id=user_id,
            session_id=session_id,
            metadata=metadata or {}
        )
        await self.analytics_engine.track_event(event)

    async def track_user_session_end(self, user_id: str, session_id: str, metadata: Dict[str, Any] = None):
        """Track user session end"""
        event = AnalyticsEvent(
            event_id=str(uuid.uuid4()),
            event_type=AnalyticsEventType.USER_SESSION_END,
            timestamp=datetime.now(),
            user_id=user_id,
            session_id=session_id,
            metadata=metadata or {}
        )
        await self.analytics_engine.track_event(event)

    async def track_feature_usage(self, user_id: str, feature_name: str, metrics: Dict[str, Any] = None, session_id: str = None):
        """Track feature usage"""
        event = AnalyticsEvent(
            event_id=str(uuid.uuid4()),
            event_type=AnalyticsEventType.FEATURE_USAGE,
            timestamp=datetime.now(),
            user_id=user_id,
            session_id=session_id,
            feature_name=feature_name,
            metrics=metrics or {}
        )
        await self.analytics_engine.track_event(event)

    async def track_user_action(self, user_id: str, action_type: str, feature_name: str = None, metrics: Dict[str, Any] = None, session_id: str = None):
        """Track user action for behavior analysis"""
        await self.user_analyzer.track_user_action(user_id, action_type, feature_name, metrics, session_id)

    # Performance Tracking
    async def track_performance_metrics(self, cpu_usage: float, memory_usage: float, disk_usage: float, system_load: float, network_io: Dict[str, float] = None):
        """Track system performance metrics"""
        metrics = {
            'cpu_usage': cpu_usage,
            'memory_usage': memory_usage,
            'disk_usage': disk_usage,
            'system_load': system_load,
            'network_io': network_io or {}
        }

        event = AnalyticsEvent(
            event_id=str(uuid.uuid4()),
            event_type=AnalyticsEventType.PERFORMANCE_METRIC,
            timestamp=datetime.now(),
            metrics=metrics
        )
        await self.analytics_engine.track_event(event)

    async def track_service_metrics(self, service_name: str, response_time: float, error_rate: float = 0.0, throughput: float = 0.0, success_rate: float = 100.0, availability: float = 100.0):
        """Track service-specific performance metrics"""
        await self.performance_analyzer.track_service_metrics(
            service_name, response_time, error_rate, throughput, success_rate, availability
        )

    # Cost Tracking
    async def track_cost_event(self, provider: str, model: str, input_tokens: int, output_tokens: int, cost: float, user_id: str = None, session_id: str = None):
        """Track cost-related events"""
        event = AnalyticsEvent(
            event_id=str(uuid.uuid4()),
            event_type=AnalyticsEventType.COST_EVENT,
            timestamp=datetime.now(),
            user_id=user_id,
            session_id=session_id,
            metrics={
                'provider': provider,
                'model': model,
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'cost': cost
            }
        )
        await self.analytics_engine.track_event(event)

        # Also record in cost tracker if available
        try:
            from cost_management import CostTracker
            cost_tracker = CostTracker()
            cost_tracker.record_usage(provider, model, input_tokens, output_tokens, "api_request", user_id, session_id)
        except ImportError:
            pass

    # Analytics Query Methods
    def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive user profile"""
        profile = self.user_analyzer.get_user_profile(user_id)
        if profile:
            return {
                'user_id': profile.user_id,
                'first_seen': profile.first_seen.isoformat(),
                'last_seen': profile.last_seen.isoformat(),
                'total_sessions': profile.total_sessions,
                'total_requests': profile.total_requests,
                'total_cost': profile.total_cost,
                'favorite_features': profile.favorite_features,
                'engagement_score': profile.engagement_score,
                'segment': profile.segment.value,
                'retention_score': profile.retention_score,
                'lifetime_value': profile.lifetime_value
            }
        return None

    def get_user_insights(self, user_id: str) -> List[Dict[str, Any]]:
        """Get behavior insights for a user"""
        insights = self.user_analyzer.get_user_insights(user_id)
        return [
            {
                'insight_id': insight.insight_id,
                'insight_type': insight.insight_type.value,
                'description': insight.description,
                'confidence_score': insight.confidence_score,
                'recommendations': insight.recommendations,
                'discovered_at': insight.discovered_at.isoformat()
            }
            for insight in insights
        ]

    def get_performance_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get performance summary"""
        return self.performance_analyzer.get_performance_summary(hours)

    def get_cost_breakdown(self, days: int = 30) -> Dict[str, Any]:
        """Get detailed cost breakdown"""
        return self.bi_engine.get_cost_breakdown(days)

    def get_business_insights(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get business insights"""
        return self.bi_engine.get_business_insights(limit)

    def get_predictions(self, metric_name: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get predictions"""
        return self.predictive_engine.get_predictions(metric_name, limit)

    def get_anomaly_alerts(self, resolved: bool = False, limit: int = 50) -> List[Dict[str, Any]]:
        """Get anomaly alerts"""
        return self.predictive_engine.get_anomaly_alerts(resolved, limit)

    def get_forecast(self, metric_name: str, days: int = 7) -> Dict[str, Any]:
        """Get forecast for a specific metric"""
        return self.predictive_engine.get_forecast(metric_name, days)

    # Dashboard Methods
    def start_dashboard(self, host: str = "127.0.0.1", port: int = 8790):
        """Start the real-time analytics dashboard"""
        self.dashboard.run_dashboard(host, port)

    def stop_dashboard(self):
        """Stop the analytics dashboard"""
        self.dashboard.stop()

    # Utility Methods
    def cleanup_old_data(self, retention_days: int = 90):
        """Clean up old analytics data"""
        self.analytics_engine.cleanup_old_data(retention_days)
        self.performance_analyzer.cleanup_old_data(retention_days)
        self.bi_engine.cleanup_old_data(retention_days)
        self.predictive_engine.cleanup_old_data(retention_days)

    def get_system_status(self) -> Dict[str, Any]:
        """Get analytics system status"""
        return {
            'analytics_engine': 'running',
            'user_analyzer': 'running',
            'performance_analyzer': 'running',
            'bi_engine': 'running',
            'predictive_engine': 'running',
            'dashboard': 'running' if self.dashboard.is_running else 'stopped',
            'database_path': self.analytics_engine.db.db_path,
            'initialized_at': datetime.now().isoformat()
        }

    def create_prediction_model(self, model_type: str, target_metric: str, features: List[str], hyperparameters: Dict[str, Any] = None) -> str:
        """Create a new prediction model"""
        model_type_enum = self.predictive_engine.ModelType(model_type)
        return self.predictive_engine.create_prediction_model(model_type_enum, target_metric, features, hyperparameters)

    def resolve_anomaly(self, alert_id: str):
        """Resolve an anomaly alert"""
        self.predictive_engine.resolve_anomaly(alert_id)
        self.dashboard.resolve_alert(alert_id)

    def get_comprehensive_report(self, days: int = 30) -> Dict[str, Any]:
        """Generate comprehensive analytics report"""
        return {
            'report_period': f"{days} days",
            'generated_at': datetime.now().isoformat(),
            'user_analytics': {
                'active_users': self.user_analyzer._calculate_engagement_metrics().daily_active_users,
                'user_segments': self.user_analyzer.get_segment_distribution(),
                'top_engaged_users': self.user_analyzer.get_top_engaged_users(10)
            },
            'performance_analytics': {
                'summary': self.performance_analyzer.get_performance_summary(),
                'trends': self.performance_analyzer.get_performance_trends(),
                'active_bottlenecks': len(self.performance_analyzer.get_active_bottlenecks())
            },
            'business_intelligence': {
                'cost_breakdown': self.bi_engine.get_cost_breakdown(),
                'roi_metrics': self.bi_engine.get_roi_metrics(),
                'insights': self.bi_engine.get_business_insights(10),
                'optimization_opportunities': self.bi_engine.get_cost_optimization_opportunities()
            },
            'predictive_analytics': {
                'recent_predictions': self.predictive_engine.get_predictions(limit=20),
                'active_anomalies': self.predictive_engine.get_anomaly_alerts(resolved=False, limit=10),
                'trend_analyses': self.predictive_engine.get_trend_analyses()
            }
        }

    async def shutdown(self):
        """Shutdown analytics system gracefully"""
        logger.info("Shutting down DuckBot Analytics System...")
        self.dashboard.stop()
        self.performance_analyzer.stop_monitoring()
        self.predictive_engine.stop()
        logger.info("DuckBot Analytics System shutdown complete")

# Global analytics instance
analytics_integration = None

def get_analytics() -> AnalyticsIntegration:
    """Get the global analytics instance"""
    global analytics_integration
    if analytics_integration is None:
        analytics_integration = AnalyticsIntegration()
    return analytics_integration

def initialize_analytics(db_path: str = None) -> AnalyticsIntegration:
    """Initialize the analytics system"""
    global analytics_integration
    analytics_integration = AnalyticsIntegration(db_path)
    return analytics_integration