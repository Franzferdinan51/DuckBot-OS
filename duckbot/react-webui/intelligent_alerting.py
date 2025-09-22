#!/usr/bin/env python3
"""
Intelligent Alerting System for React WebUI
Provides alert management and notification functionality for the web dashboard
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import uuid

logger = logging.getLogger(__name__)

class AlertSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

class AlertStatus(Enum):
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"

@dataclass
class WebUIAlert:
    """Alert data structure for web UI"""
    id: str
    title: str
    message: str
    severity: AlertSeverity
    status: AlertStatus
    service_name: Optional[str] = None
    source: str = "webui"
    created_at: datetime = field(default_factory=datetime.now)
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class WebUIIntelligentAlerting:
    """Simplified intelligent alerting system for React WebUI"""

    def __init__(self, max_alerts: int = 500):
        self.max_alerts = max_alerts
        self.active_alerts: Dict[str, WebUIAlert] = {}
        self.alert_history: deque = deque(maxlen=max_alerts)
        self.alert_rules: Dict[str, Dict[str, Any]] = {}
        self.subscribers: List[Callable] = []

        # Initialize default alert rules
        self._initialize_default_rules()

    def _initialize_default_rules(self):
        """Initialize default alerting rules"""
        self.alert_rules = {
            'high_cpu_usage': {
                'condition': lambda data: data.get('cpu_percent', 0) > 80,
                'severity': AlertSeverity.WARNING,
                'title': 'High CPU Usage',
                'message_template': 'CPU usage is at {cpu_percent}%'
            },
            'critical_cpu_usage': {
                'condition': lambda data: data.get('cpu_percent', 0) > 95,
                'severity': AlertSeverity.CRITICAL,
                'title': 'Critical CPU Usage',
                'message_template': 'CPU usage is critical at {cpu_percent}%'
            },
            'high_memory_usage': {
                'condition': lambda data: data.get('memory_percent', 0) > 85,
                'severity': AlertSeverity.WARNING,
                'title': 'High Memory Usage',
                'message_template': 'Memory usage is at {memory_percent}%'
            },
            'service_unhealthy': {
                'condition': lambda data: data.get('status') == 'unhealthy',
                'severity': AlertSeverity.CRITICAL,
                'title': 'Service Unhealthy',
                'message_template': 'Service {service_name} is unhealthy'
            },
            'slow_response': {
                'condition': lambda data: data.get('response_time', 0) > 5,
                'severity': AlertSeverity.WARNING,
                'title': 'Slow Response Time',
                'message_template': 'Service {service_name} response time: {response_time}s'
            }
        }

    def add_alert_rule(self, rule_name: str, condition: Callable, severity: AlertSeverity,
                       title: str, message_template: str):
        """Add a custom alert rule"""
        self.alert_rules[rule_name] = {
            'condition': condition,
            'severity': severity,
            'title': title,
            'message_template': message_template
        }
        logger.info(f"Added alert rule: {rule_name}")

    def remove_alert_rule(self, rule_name: str):
        """Remove an alert rule"""
        if rule_name in self.alert_rules:
            del self.alert_rules[rule_name]
            logger.info(f"Removed alert rule: {rule_name}")

    def subscribe_to_alerts(self, callback: Callable):
        """Subscribe to alert notifications"""
        self.subscribers.append(callback)

    def unsubscribe_from_alerts(self, callback: Callable):
        """Unsubscribe from alert notifications"""
        if callback in self.subscribers:
            self.subscribers.remove(callback)

    async def check_alerts(self, service_name: str, metrics: Dict[str, Any]):
        """Check metrics against alert rules"""
        alerts_created = []

        for rule_name, rule in self.alert_rules.items():
            try:
                # Prepare data for condition check
                check_data = {
                    'service_name': service_name,
                    'timestamp': datetime.now(),
                    **metrics
                }

                # Check condition
                if rule['condition'](check_data):
                    # Check if similar alert already exists
                    existing_alert = self._find_similar_alert(rule_name, service_name)
                    if existing_alert and existing_alert.status == AlertStatus.ACTIVE:
                        continue  # Skip duplicate active alerts

                    # Create new alert
                    alert = WebUIAlert(
                        id=f"{rule_name}_{service_name}_{int(time.time())}",
                        title=rule['title'],
                        message=rule['message_template'].format(**check_data),
                        severity=rule['severity'],
                        status=AlertStatus.ACTIVE,
                        service_name=service_name,
                        metadata={
                            'rule_name': rule_name,
                            'metrics': metrics
                        }
                    )

                    await self._create_alert(alert)
                    alerts_created.append(alert)

            except Exception as e:
                logger.error(f"Error checking alert rule {rule_name}: {e}")

        return alerts_created

    def _find_similar_alert(self, rule_name: str, service_name: str) -> Optional[WebUIAlert]:
        """Find similar active alert"""
        for alert in self.active_alerts.values():
            if (alert.status == AlertStatus.ACTIVE and
                alert.metadata.get('rule_name') == rule_name and
                alert.service_name == service_name):
                return alert
        return None

    async def _create_alert(self, alert: WebUIAlert):
        """Create and store an alert"""
        # Store active alert
        self.active_alerts[alert.id] = alert

        # Add to history
        self.alert_history.append(alert)

        # Notify subscribers
        await self._notify_subscribers(alert)

        logger.warning(f"Alert created: {alert.severity.value} - {alert.message}")

    async def _notify_subscribers(self, alert: WebUIAlert):
        """Notify subscribers of new alert"""
        for subscriber in self.subscribers:
            try:
                if asyncio.iscoroutinefunction(subscriber):
                    await subscriber(alert)
                else:
                    subscriber(alert)
            except Exception as e:
                logger.error(f"Error notifying alert subscriber: {e}")

    async def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.status = AlertStatus.ACKNOWLEDGED
            alert.acknowledged_at = datetime.now()
            await self._notify_subscribers(alert)
            logger.info(f"Alert {alert_id} acknowledged")
            return True
        return False

    async def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.status = AlertStatus.RESOLVED
            alert.resolved_at = datetime.now()
            await self._notify_subscribers(alert)
            del self.active_alerts[alert_id]
            logger.info(f"Alert {alert_id} resolved")
            return True
        return False

    def get_active_alerts(self, severity: Optional[AlertSeverity] = None,
                         service_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get active alerts with optional filtering"""
        alerts = list(self.active_alerts.values())

        if severity:
            alerts = [alert for alert in alerts if alert.severity == severity]

        if service_name:
            alerts = [alert for alert in alerts if alert.service_name == service_name]

        return [self._alert_to_dict(alert) for alert in alerts]

    def get_alert_history(self, hours: int = 24, severity: Optional[AlertSeverity] = None,
                         service_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get alert history"""
        cutoff_time = datetime.now() - timedelta(hours=hours)

        alerts = [alert for alert in self.alert_history if alert.created_at > cutoff_time]

        if severity:
            alerts = [alert for alert in alerts if alert.severity == severity]

        if service_name:
            alerts = [alert for alert in alerts if alert.service_name == service_name]

        return [self._alert_to_dict(alert) for alert in alerts]

    def _alert_to_dict(self, alert: WebUIAlert) -> Dict[str, Any]:
        """Convert alert to dictionary"""
        return {
            'id': alert.id,
            'title': alert.title,
            'message': alert.message,
            'severity': alert.severity.value,
            'status': alert.status.value,
            'service_name': alert.service_name,
            'source': alert.source,
            'created_at': alert.created_at.isoformat(),
            'acknowledged_at': alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
            'resolved_at': alert.resolved_at.isoformat() if alert.resolved_at else None,
            'metadata': alert.metadata
        }

    def get_alert_summary(self) -> Dict[str, Any]:
        """Get alert summary statistics"""
        active_alerts = list(self.active_alerts.values())

        summary = {
            'total_active': len(active_alerts),
            'by_severity': {
                'critical': len([a for a in active_alerts if a.severity == AlertSeverity.CRITICAL]),
                'warning': len([a for a in active_alerts if a.severity == AlertSeverity.WARNING]),
                'info': len([a for a in active_alerts if a.severity == AlertSeverity.INFO])
            },
            'by_status': {
                'active': len([a for a in active_alerts if a.status == AlertStatus.ACTIVE]),
                'acknowledged': len([a for a in active_alerts if a.status == AlertStatus.ACKNOWLEDGED])
            },
            'by_service': {}
        }

        # Count by service
        for alert in active_alerts:
            service = alert.service_name or 'system'
            if service not in summary['by_service']:
                summary['by_service'][service] = 0
            summary['by_service'][service] += 1

        return summary

    def cleanup_old_alerts(self, days: int = 7):
        """Clean up old resolved alerts"""
        cutoff_time = datetime.now() - timedelta(days=days)

        # Keep only recent alerts in history
        old_size = len(self.alert_history)
        self.alert_history = deque(
            [alert for alert in self.alert_history if alert.created_at > cutoff_time],
            maxlen=self.max_alerts
        )

        cleaned_count = old_size - len(self.alert_history)
        if cleaned_count > 0:
            logger.info(f"Cleaned up {cleaned_count} old alerts")

# Global instance
_webui_intelligent_alerting: Optional[WebUIIntelligentAlerting] = None

def get_webui_intelligent_alerting() -> WebUIIntelligentAlerting:
    """Get the global WebUI intelligent alerting instance"""
    global _webui_intelligent_alerting
    if _webui_intelligent_alerting is None:
        _webui_intelligent_alerting = WebUIIntelligentAlerting()
    return _webui_intelligent_alerting

# Convenience functions
async def check_webui_alerts(service_name: str, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Convenience function to check alerts for a service"""
    system = get_webui_intelligent_alerting()
    alerts = await system.check_alerts(service_name, metrics)
    return [system._alert_to_dict(alert) for alert in alerts]

async def acknowledge_webui_alert(alert_id: str) -> bool:
    """Convenience function to acknowledge an alert"""
    system = get_webui_intelligent_alerting()
    return await system.acknowledge_alert(alert_id)

async def resolve_webui_alert(alert_id: str) -> bool:
    """Convenience function to resolve an alert"""
    system = get_webui_intelligent_alerting()
    return await system.resolve_alert(alert_id)