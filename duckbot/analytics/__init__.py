# duckbot/analytics/__init__.py
"""
DuckBot Advanced Analytics System
A comprehensive analytics platform for user behavior analysis,
performance monitoring, business intelligence, and predictive analytics.
"""

from .core.analytics_engine import AnalyticsEngine
from .core.event_tracker import EventTracker
from .core.session_manager import SessionManager
from .core.metrics_collector import MetricsCollector
from .analytics.user_behavior import UserBehaviorAnalyzer
from .analytics.performance import PerformanceAnalyzer
from .analytics.business_intelligence import BusinessIntelligenceEngine
from .analytics.predictive import PredictiveAnalyticsEngine
from .storage.analytics_db import AnalyticsDatabase
from .api.analytics_api import AnalyticsAPI
from .ui.analytics_dashboard import AnalyticsDashboard

__version__ = "1.0.0"
__all__ = [
    "AnalyticsEngine",
    "EventTracker",
    "SessionManager",
    "MetricsCollector",
    "UserBehaviorAnalyzer",
    "PerformanceAnalyzer",
    "BusinessIntelligenceEngine",
    "PredictiveAnalyticsEngine",
    "AnalyticsDatabase",
    "AnalyticsAPI",
    "AnalyticsDashboard"
]

# Initialize global analytics engine
_analytics_engine = None

def get_analytics_engine():
    """Get the global analytics engine instance"""
    global _analytics_engine
    if _analytics_engine is None:
        from duckbot.logging_setup import get_logger
        logger = get_logger("analytics")
        _analytics_engine = AnalyticsEngine(logger)
    return _analytics_engine

def initialize_analytics():
    """Initialize the analytics system"""
    engine = get_analytics_engine()
    engine.initialize()
    return engine