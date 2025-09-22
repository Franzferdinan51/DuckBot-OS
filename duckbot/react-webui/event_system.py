#!/usr/bin/env python3
"""
Event System for React WebUI
Provides simplified event handling for web dashboard components
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import uuid

logger = logging.getLogger(__name__)

class WebUIEventType(Enum):
    """Event types for web dashboard"""
    # Service events
    SERVICE_STATUS_CHANGED = "service_status_changed"
    SERVICE_HEALTH_UPDATE = "service_health_update"
    SERVICE_METRICS_UPDATE = "service_metrics_update"

    # Alert events
    ALERT_TRIGGERED = "alert_triggered"
    ALERT_RESOLVED = "alert_resolved"
    ALERT_ACKNOWLEDGED = "alert_acknowledged"

    # System events
    SYSTEM_METRICS_UPDATE = "system_metrics_update"
    SYSTEM_HEALTH_CHANGED = "system_health_changed"

    # UI events
    DASHBOARD_UPDATED = "dashboard_updated"
    REFRESH_REQUESTED = "refresh_requested"
    CONFIG_CHANGED = "config_changed"

@dataclass
class WebUIEvent:
    """Event data structure for web UI"""
    id: str
    type: WebUIEventType
    timestamp: datetime
    source: str
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

class WebUIEventSystem:
    """Simplified event system for React WebUI"""

    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.event_history: deque = deque(maxlen=max_history)
        self.subscribers: Dict[WebUIEventType, List[Callable]] = defaultdict(list)
        self.running = False

    async def start(self):
        """Start the event system"""
        if self.running:
            return
        self.running = True
        logger.info("WebUI Event System started")

    async def stop(self):
        """Stop the event system"""
        if not self.running:
            return
        self.running = False
        logger.info("WebUI Event System stopped")

    def subscribe(self, event_type: WebUIEventType, callback: Callable) -> str:
        """Subscribe to events"""
        subscription_id = str(uuid.uuid4())
        self.subscribers[event_type].append({
            'id': subscription_id,
            'callback': callback
        })
        logger.debug(f"Subscribed to {event_type.value} with ID {subscription_id}")
        return subscription_id

    def unsubscribe(self, subscription_id: str) -> bool:
        """Unsubscribe from events"""
        for event_type, subscribers in self.subscribers.items():
            for i, subscriber in enumerate(subscribers):
                if subscriber['id'] == subscription_id:
                    subscribers.pop(i)
                    logger.debug(f"Unsubscribed {subscription_id} from {event_type.value}")
                    return True
        return False

    async def emit(self, event_type: WebUIEventType, source: str,
                   data: Dict[str, Any] = None, metadata: Dict[str, Any] = None) -> str:
        """Emit an event"""
        if not self.running:
            logger.warning("Event system not running, event not emitted")
            return ""

        event = WebUIEvent(
            id=str(uuid.uuid4()),
            type=event_type,
            timestamp=datetime.now(),
            source=source,
            data=data or {},
            metadata=metadata or {}
        )

        # Add to history
        self.event_history.append(event)

        # Notify subscribers
        await self._notify_subscribers(event)

        logger.debug(f"Emitted event {event.id}: {event_type.value}")
        return event.id

    async def _notify_subscribers(self, event: WebUIEvent):
        """Notify all subscribers of an event"""
        subscribers = self.subscribers.get(event.type, [])

        for subscriber in subscribers:
            try:
                callback = subscriber['callback']
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                logger.error(f"Error notifying subscriber {subscriber['id']}: {e}")

    def get_recent_events(self, event_type: Optional[WebUIEventType] = None,
                          limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent events, optionally filtered by type"""
        events = list(self.event_history)

        if event_type:
            events = [e for e in events if e.type == event_type]

        events = events[-limit:]

        return [
            {
                'id': event.id,
                'type': event.type.value,
                'timestamp': event.timestamp.isoformat(),
                'source': event.source,
                'data': event.data,
                'metadata': event.metadata
            }
            for event in events
        ]

    def get_event_stats(self) -> Dict[str, Any]:
        """Get event statistics"""
        stats = {
            'total_events': len(self.event_history),
            'event_types': {},
            'subscribers': {},
            'running': self.running
        }

        # Count by event type
        for event in self.event_history:
            event_type = event.type.value
            stats['event_types'][event_type] = stats['event_types'].get(event_type, 0) + 1

        # Count subscribers by type
        for event_type, subscribers in self.subscribers.items():
            stats['subscribers'][event_type.value] = len(subscribers)

        return stats

# Global instance
_webui_event_system: Optional[WebUIEventSystem] = None

def get_webui_event_system() -> WebUIEventSystem:
    """Get the global WebUI event system instance"""
    global _webui_event_system
    if _webui_event_system is None:
        _webui_event_system = WebUIEventSystem()
    return _webui_event_system

async def start_webui_event_system():
    """Start the global WebUI event system"""
    system = get_webui_event_system()
    await system.start()
    return system

async def stop_webui_event_system():
    """Stop the global WebUI event system"""
    system = get_webui_event_system()
    await system.stop()

# Convenience functions
async def emit_webui_event(event_type: WebUIEventType, source: str,
                         data: Dict[str, Any] = None, **kwargs) -> str:
    """Convenience function to emit WebUI events"""
    system = get_webui_event_system()
    return await system.emit(event_type, source, data, **kwargs)

def subscribe_to_webui_event(event_type: WebUIEventType, callback: Callable) -> str:
    """Convenience function to subscribe to WebUI events"""
    system = get_webui_event_system()
    return system.subscribe(event_type, callback)