"""
DuckBot React WebUI Package
Health monitoring and analytics components for the Electron-based dashboard
"""

__version__ = "4.2.0"
__author__ = "DuckBot Team"

# Import main components for easier access
from .health_monitor_api import router as health_monitor_router
from .performance_analytics import get_performance_analytics, PerformanceAnalytics

__all__ = [
    "health_monitor_router",
    "get_performance_analytics",
    "PerformanceAnalytics"
]