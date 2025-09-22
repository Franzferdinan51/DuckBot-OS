#!/usr/bin/env python3
"""
DuckBot Monitoring System Integration
Seamlessly integrates monitoring capabilities with existing DuckBot components
"""

import asyncio
import functools
import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional, Callable, Union
from contextlib import contextmanager
import threading
import json

# Local imports
from duckbot.core.monitoring_system import get_monitoring, AgentMetric, AlertLevel
from duckbot.core.action_reasoning_logger import action_logger
from duckbot.services.server_manager import server_manager
# from duckbot.ai_router_gpt import get_router_state

logger = logging.getLogger(__name__)

class MonitoringIntegration:
    """Main integration class for monitoring system"""

    def __init__(self):
        self.monitoring = get_monitoring()
        self.session_id = None
        self.current_user = None
        self._integration_enabled = True

    def enable_integration(self):
        """Enable monitoring integration"""
        self._integration_enabled = True
        logger.info("Monitoring integration enabled")

    def disable_integration(self):
        """Disable monitoring integration"""
        self._integration_enabled = False
        logger.info("Monitoring integration disabled")

    def set_user_context(self, user_id: str = None, session_id: str = None):
        """Set user context for activity tracking"""
        self.current_user = user_id
        self.session_id = session_id or self.monitoring.user_activity_tracker.start_session(user_id)
        logger.debug(f"User context set: user_id={user_id}, session_id={self.session_id}")

    def record_agent_interaction(self, agent_id: str, agent_type: str,
                               response_time_ms: float, success: bool,
                               model_used: str = "", tokens_used: int = 0,
                               error_message: str = "", **kwargs):
        """Record agent interaction with monitoring system"""
        if not self._integration_enabled:
            return

        try:
            self.monitoring.record_agent_interaction(
                agent_id=agent_id,
                agent_type=agent_type,
                response_time_ms=response_time_ms,
                success=success,
                model_used=model_used,
                tokens_used=tokens_used,
                error_message=error_message
            )

            # Also record as user activity if session exists
            if self.session_id:
                self.monitoring.record_user_activity(
                    session_id=self.session_id,
                    activity_type="agent_interaction",
                    feature_used=agent_type,
                    response_time_ms=response_time_ms,
                    satisfaction_score=5 if success else 1
                )

        except Exception as e:
            logger.error(f"Error recording agent interaction: {e}")

    def record_user_activity(self, activity_type: str, feature_used: str = None,
                           response_time_ms: float = None, satisfaction_score: int = None,
                           **kwargs):
        """Record user activity"""
        if not self._integration_enabled:
            return

        try:
            if not self.session_id:
                self.session_id = self.monitoring.user_activity_tracker.start_session(self.current_user)

            self.monitoring.record_user_activity(
                session_id=self.session_id,
                activity_type=activity_type,
                feature_used=feature_used,
                response_time_ms=response_time_ms,
                satisfaction_score=satisfaction_score
            )

        except Exception as e:
            logger.error(f"Error recording user activity: {e}")

    def record_api_call(self, endpoint: str, method: str, response_time_ms: float,
                       status_code: int, success: bool = None, **kwargs):
        """Record API call metrics"""
        if not self._integration_enabled:
            return

        try:
            success = success if success is not None else (200 <= status_code < 400)

            # Record as agent interaction for API endpoints
            self.record_agent_interaction(
                agent_id=f"api_{endpoint.replace('/', '_')}",
                agent_type="api_endpoint",
                response_time_ms=response_time_ms,
                success=success,
                error_message=f"HTTP {status_code}" if not success else "",
                **kwargs
            )

            # Record as user activity
            self.record_user_activity(
                activity_type="api_call",
                feature_used=endpoint,
                response_time_ms=response_time_ms
            )

        except Exception as e:
            logger.error(f"Error recording API call: {e}")

    def record_service_event(self, service_name: str, event_type: str,
                           success: bool = True, response_time_ms: float = None,
                           error_message: str = "", **kwargs):
        """Record service-related events"""
        if not self._integration_enabled:
            return

        try:
            # Record as agent interaction
            self.record_agent_interaction(
                agent_id=f"service_{service_name}",
                agent_type=f"service_{event_type}",
                response_time_ms=response_time_ms or 0,
                success=success,
                error_message=error_message,
                **kwargs
            )

            # Also record as user activity if it's user-initiated
            if event_type in ["start", "stop", "restart"]:
                self.record_user_activity(
                    activity_type=f"service_{event_type}",
                    feature_used=service_name
                )

        except Exception as e:
            logger.error(f"Error recording service event: {e}")

    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        if not self._integration_enabled:
            return {"error": "Monitoring integration disabled"}

        try:
            return self.monitoring.get_system_status()
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return {"error": str(e)}

    def check_service_health(self, service_name: str) -> Dict[str, Any]:
        """Check health of a specific service"""
        if not self._integration_enabled:
            return {"error": "Monitoring integration disabled"}

        try:
            service_status = server_manager.get_service_status(service_name)
            return {
                "service_name": service_name,
                "status": service_status.status.value,
                "display_name": service_status.display_name,
                "port": service_status.port,
                "url": service_status.url,
                "pid": service_status.pid,
                "last_checked": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error checking service health: {e}")
            return {"error": str(e)}

    def trigger_alert(self, level: AlertLevel, title: str, message: str,
                     source: str = "monitoring_integration", **kwargs):
        """Trigger a custom alert"""
        if not self._integration_enabled:
            return

        try:
            # Create alert metrics
            metrics = {"alert_level": level.value, "alert_title": title, **kwargs}

            # Use alert manager to check and trigger alert
            self.monitoring.alert_manager.check_alerts(metrics)

            logger.warning(f"Alert triggered: {title} - {message}")

        except Exception as e:
            logger.error(f"Error triggering alert: {e}")

# Global integration instance
_integration_instance = None

def get_monitoring_integration() -> MonitoringIntegration:
    """Get the global monitoring integration instance"""
    global _integration_instance
    if _integration_instance is None:
        _integration_instance = MonitoringIntegration()
    return _integration_instance

# Decorators for easy integration

def monitor_agent(agent_id: str = None, agent_type: str = "decorated_function"):
    """Decorator to monitor agent function calls"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            integration = get_monitoring_integration()
            if not integration._integration_enabled:
                return func(*args, **kwargs)

            start_time = time.time()
            success = True
            error_message = ""
            result = None

            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                error_message = str(e)
                raise
            finally:
                response_time_ms = (time.time() - start_time) * 1000
                integration.record_agent_interaction(
                    agent_id=agent_id or func.__name__,
                    agent_type=agent_type,
                    response_time_ms=response_time_ms,
                    success=success,
                    error_message=error_message
                )

        return wrapper
    return decorator

def monitor_api(endpoint: str = None):
    """Decorator to monitor API function calls"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            integration = get_monitoring_integration()
            if not integration._integration_enabled:
                return func(*args, **kwargs)

            start_time = time.time()
            success = True
            status_code = 200
            result = None

            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                status_code = 500
                raise
            finally:
                response_time_ms = (time.time() - start_time) * 1000
                integration.record_api_call(
                    endpoint=endpoint or func.__name__,
                    method="GET",  # Could be enhanced to detect actual method
                    response_time_ms=response_time_ms,
                    status_code=status_code,
                    success=success
                )

        return wrapper
    return decorator

def monitor_service(service_name: str, event_type: str = "service_call"):
    """Decorator to monitor service function calls"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            integration = get_monitoring_integration()
            if not integration._integration_enabled:
                return func(*args, **kwargs)

            start_time = time.time()
            success = True
            error_message = ""
            result = None

            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                error_message = str(e)
                raise
            finally:
                response_time_ms = (time.time() - start_time) * 1000
                integration.record_service_event(
                    service_name=service_name,
                    event_type=event_type,
                    success=success,
                    response_time_ms=response_time_ms,
                    error_message=error_message
                )

        return wrapper
    return decorator

def monitor_user_activity(activity_type: str, feature_used: str = None):
    """Decorator to monitor user activity"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            integration = get_monitoring_integration()
            if not integration._integration_enabled:
                return func(*args, **kwargs)

            start_time = time.time()
            result = None

            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                integration.record_user_activity(
                    activity_type=activity_type,
                    feature_used=feature_used,
                    satisfaction_score=1
                )
                raise
            finally:
                response_time_ms = (time.time() - start_time) * 1000
                integration.record_user_activity(
                    activity_type=activity_type,
                    feature_used=feature_used,
                    response_time_ms=response_time_ms,
                    satisfaction_score=5
                )

        return wrapper
    return decorator

# Context managers for activity tracking

@contextmanager
def monitor_agent_context(agent_id: str, agent_type: str, **kwargs):
    """Context manager for monitoring agent operations"""
    integration = get_monitoring_integration()
    if not integration._integration_enabled:
        yield
        return

    start_time = time.time()
    success = True
    error_message = ""

    try:
        yield
    except Exception as e:
        success = False
        error_message = str(e)
        raise
    finally:
        response_time_ms = (time.time() - start_time) * 1000
        integration.record_agent_interaction(
            agent_id=agent_id,
            agent_type=agent_type,
            response_time_ms=response_time_ms,
            success=success,
            error_message=error_message,
            **kwargs
        )

@contextmanager
def monitor_user_activity_context(activity_type: str, feature_used: str = None, **kwargs):
    """Context manager for monitoring user activity"""
    integration = get_monitoring_integration()
    if not integration._integration_enabled:
        yield
        return

    start_time = time.time()
    satisfaction_score = 5

    try:
        yield
    except Exception as e:
        satisfaction_score = 1
        raise
    finally:
        response_time_ms = (time.time() - start_time) * 1000
        integration.record_user_activity(
            activity_type=activity_type,
            feature_used=feature_used,
            response_time_ms=response_time_ms,
            satisfaction_score=satisfaction_score,
            **kwargs
        )

# Enhanced server manager integration

class MonitoredServerManager:
    """Enhanced server manager with monitoring integration"""

    def __init__(self):
        self.integration = get_monitoring_integration()

    def start_service(self, service_name: str):
        """Start service with monitoring"""
        start_time = time.time()
        success = False
        error_message = ""

        try:
            success, message = server_manager.start_service(service_name)
            if not success:
                error_message = message

            self.integration.record_service_event(
                service_name=service_name,
                event_type="start",
                success=success,
                response_time_ms=(time.time() - start_time) * 1000,
                error_message=error_message
            )

            return success, message

        except Exception as e:
            success = False
            error_message = str(e)
            self.integration.record_service_event(
                service_name=service_name,
                event_type="start",
                success=success,
                response_time_ms=(time.time() - start_time) * 1000,
                error_message=error_message
            )
            raise

    def stop_service(self, service_name: str):
        """Stop service with monitoring"""
        start_time = time.time()
        success = False
        error_message = ""

        try:
            success, message = server_manager.stop_service(service_name)
            if not success:
                error_message = message

            self.integration.record_service_event(
                service_name=service_name,
                event_type="stop",
                success=success,
                response_time_ms=(time.time() - start_time) * 1000,
                error_message=error_message
            )

            return success, message

        except Exception as e:
            success = False
            error_message = str(e)
            self.integration.record_service_event(
                service_name=service_name,
                event_type="stop",
                success=success,
                response_time_ms=(time.time() - start_time) * 1000,
                error_message=error_message
            )
            raise

    def restart_service(self, service_name: str):
        """Restart service with monitoring"""
        start_time = time.time()
        success = False
        error_message = ""

        try:
            success, message = server_manager.restart_service(service_name)
            if not success:
                error_message = message

            self.integration.record_service_event(
                service_name=service_name,
                event_type="restart",
                success=success,
                response_time_ms=(time.time() - start_time) * 1000,
                error_message=error_message
            )

            return success, message

        except Exception as e:
            success = False
            error_message = str(e)
            self.integration.record_service_event(
                service_name=service_name,
                event_type="restart",
                success=success,
                response_time_ms=(time.time() - start_time) * 1000,
                error_message=error_message
            )
            raise

# Global monitored server manager instance
monitored_server_manager = MonitoredServerManager()

# Integration helper functions

def setup_monitoring_integration(user_id: str = None):
    """Setup monitoring integration for the current session"""
    integration = get_monitoring_integration()
    integration.set_user_context(user_id=user_id)
    integration.enable_integration()
    return integration

def record_chat_interaction(user_id: str, agent_id: str, response_time_ms: float,
                           success: bool, model_used: str = "", tokens_used: int = 0):
    """Record chat interaction with monitoring"""
    integration = get_monitoring_integration()
    integration.set_user_context(user_id=user_id)
    integration.record_agent_interaction(
        agent_id=agent_id,
        agent_type="chat",
        response_time_ms=response_time_ms,
        success=success,
        model_used=model_used,
        tokens_used=tokens_used
    )

def record_webui_activity(user_id: str, activity_type: str, feature_used: str = None,
                         response_time_ms: float = None, satisfaction_score: int = None):
    """Record WebUI activity with monitoring"""
    integration = get_monitoring_integration()
    integration.set_user_context(user_id=user_id)
    integration.record_user_activity(
        activity_type=activity_type,
        feature_used=feature_used,
        response_time_ms=response_time_ms,
        satisfaction_score=satisfaction_score
    )

def record_discord_activity(user_id: str, activity_type: str, feature_used: str = None,
                           response_time_ms: float = None):
    """Record Discord bot activity with monitoring"""
    integration = get_monitoring_integration()
    integration.set_user_context(user_id=user_id)
    integration.record_user_activity(
        activity_type=f"discord_{activity_type}",
        feature_used=feature_used,
        response_time_ms=response_time_ms,
        satisfaction_score=5  # Assume satisfaction unless error occurs
    )

# FastAPI integration helper

def add_monitoring_middleware(app):
    """Add monitoring middleware to FastAPI application"""
    from fastapi import Request
    from fastapi.responses import JSONResponse

    @app.middleware("http")
    async def monitoring_middleware(request: Request, call_next):
        integration = get_monitoring_integration()
        if not integration._integration_enabled:
            return await call_next(request)

        start_time = time.time()
        success = True
        status_code = 200

        try:
            response = await call_next(request)
            status_code = response.status_code
            success = 200 <= status_code < 400
            return response
        except Exception as e:
            success = False
            status_code = 500
            raise
        finally:
            response_time_ms = (time.time() - start_time) * 1000
            integration.record_api_call(
                endpoint=request.url.path,
                method=request.method,
                response_time_ms=response_time_ms,
                status_code=status_code,
                success=success
            )

    return app

# Example usage and testing

def example_usage():
    """Example of how to use the monitoring integration"""
    print("=== DuckBot Monitoring Integration Example ===")

    # Setup integration
    integration = setup_monitoring_integration(user_id="example_user")

    # Record some activities
    integration.record_agent_interaction(
        agent_id="test_agent",
        agent_type="chat",
        response_time_ms=150.5,
        success=True,
        model_used="gpt-4",
        tokens_used=100
    )

    integration.record_user_activity(
        activity_type="webui_login",
        feature_used="authentication",
        response_time_ms=45.2,
        satisfaction_score=5
    )

    # Check system status
    status = integration.get_system_status()
    print(f"System status: {status.get('system_metrics', {}).get('cpu_percent', 0)}% CPU")

    # Test service management
    success, message = monitored_server_manager.start_service("webui")
    print(f"Service start result: {success}, {message}")

    print("Integration example completed!")

if __name__ == "__main__":
    example_usage()