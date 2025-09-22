# duckbot/analytics/core/event_tracker.py
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from collections import defaultdict
import json

@dataclass
class AnalyticsEvent:
    """Represents an analytics event"""
    event_type: str
    event_data: Dict[str, Any]
    user_id: Optional[str]
    session_id: str
    timestamp: str
    metadata: Dict[str, Any]

class EventTracker:
    """Tracks and manages analytics events"""

    def __init__(self, logger, config):
        self.logger = logger
        self.config = config
        self.event_queue = asyncio.Queue(maxsize=10000)
        self.processed_events = []
        self.event_counts = defaultdict(int)
        self.user_activity = defaultdict(list)
        self.session_activity = defaultdict(list)

    async def track_event(self, event: Dict[str, Any]):
        """Track an analytics event"""
        try:
            # Create analytics event object
            analytics_event = AnalyticsEvent(
                event_type=event["event_type"],
                event_data=event["event_data"],
                user_id=event.get("user_id"),
                session_id=event["session_id"],
                timestamp=event["timestamp"],
                metadata=event.get("metadata", {})
            )

            # Add to queue
            try:
                self.event_queue.put_nowait(analytics_event)
            except asyncio.QueueFull:
                self.logger.warning("Event queue full, dropping event")
                return False

            # Update counters
            self.event_counts[analytics_event.event_type] += 1

            # Track user activity
            if analytics_event.user_id:
                self.user_activity[analytics_event.user_id].append(analytics_event)

            # Track session activity
            self.session_activity[analytics_event.session_id].append(analytics_event)

            return True

        except Exception as e:
            self.logger.error(f"Failed to track event: {e}")
            return False

    async def get_pending_events(self) -> List[AnalyticsEvent]:
        """Get pending events for processing"""
        events = []
        try:
            # Get up to batch_size events
            for _ in range(min(self.config.batch_size, self.event_queue.qsize())):
                try:
                    event = self.event_queue.get_nowait()
                    events.append(event)
                except asyncio.QueueEmpty:
                    break
        except Exception as e:
            self.logger.error(f"Failed to get pending events: {e}")

        return events

    async def clear_processed_events(self):
        """Clear processed events from memory"""
        # Keep only recent events in memory (last 1000 per user/session)
        for user_id in self.user_activity:
            if len(self.user_activity[user_id]) > 1000:
                self.user_activity[user_id] = self.user_activity[user_id][-1000:]

        for session_id in self.session_activity:
            if len(self.session_activity[session_id]) > 1000:
                self.session_activity[session_id] = self.session_activity[session_id][-1000:]

    def get_event_counts(self) -> Dict[str, int]:
        """Get event type counts"""
        return dict(self.event_counts)

    def get_user_activity(self, user_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent activity for a user"""
        events = self.user_activity.get(user_id, [])
        return [self._event_to_dict(event) for event in events[-limit:]]

    def get_session_activity(self, session_id: str) -> List[Dict[str, Any]]:
        """Get activity for a session"""
        events = self.session_activity.get(session_id, [])
        return [self._event_to_dict(event) for event in events]

    def get_recent_events(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent events across all users/sessions"""
        all_events = []
        for session_events in self.session_activity.values():
            all_events.extend(session_events)

        # Sort by timestamp and limit
        all_events.sort(key=lambda x: x.timestamp, reverse=True)
        return [self._event_to_dict(event) for event in all_events[:limit]]

    def _event_to_dict(self, event: AnalyticsEvent) -> Dict[str, Any]:
        """Convert event to dictionary for serialization"""
        return {
            "event_type": event.event_type,
            "event_data": event.event_data,
            "user_id": event.user_id,
            "session_id": event.session_id,
            "timestamp": event.timestamp,
            "metadata": event.metadata
        }

    async def track_page_view(self, user_id: Optional[str], session_id: str,
                            page_name: str, page_data: Dict[str, Any] = None):
        """Track a page view event"""
        event_data = {
            "page_name": page_name,
            "page_data": page_data or {},
            "user_agent": None,  # Will be filled by webui
            "ip_address": None,   # Will be filled by webui
            "referrer": None
        }

        await self.track_event({
            "event_type": "page_view",
            "event_data": event_data,
            "user_id": user_id,
            "session_id": session_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": {}
        })

    async def track_user_action(self, user_id: Optional[str], session_id: str,
                               action_type: str, action_data: Dict[str, Any]):
        """Track a user action event"""
        event_data = {
            "action_type": action_type,
            "action_data": action_data,
            "timestamp_ms": int(datetime.now(timezone.utc).timestamp() * 1000)
        }

        await self.track_event({
            "event_type": "user_action",
            "event_data": event_data,
            "user_id": user_id,
            "session_id": session_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": {}
        })

    async def track_error(self, user_id: Optional[str], session_id: str,
                         error_type: str, error_message: str, error_data: Dict[str, Any] = None):
        """Track an error event"""
        event_data = {
            "error_type": error_type,
            "error_message": error_message,
            "error_data": error_data or {},
            "stack_trace": None  # Will be filled by exception handler
        }

        await self.track_event({
            "event_type": "error",
            "event_data": event_data,
            "user_id": user_id,
            "session_id": session_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": {}
        })

    async def track_performance_metric(self, user_id: Optional[str], session_id: str,
                                     metric_name: str, metric_value: float,
                                     metric_data: Dict[str, Any] = None):
        """Track a performance metric"""
        event_data = {
            "metric_name": metric_name,
            "metric_value": metric_value,
            "metric_data": metric_data or {},
            "unit": "ms"  # Default unit
        }

        await self.track_event({
            "event_type": "performance_metric",
            "event_data": event_data,
            "user_id": user_id,
            "session_id": session_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": {}
        })

    async def track_ai_interaction(self, user_id: Optional[str], session_id: str,
                                 ai_provider: str, model_name: str,
                                 interaction_type: str, interaction_data: Dict[str, Any]):
        """Track AI interaction events"""
        event_data = {
            "ai_provider": ai_provider,
            "model_name": model_name,
            "interaction_type": interaction_type,  # "chat", "generate", "analyze", etc.
            "interaction_data": interaction_data,
            "timestamp_ms": int(datetime.now(timezone.utc).timestamp() * 1000)
        }

        await self.track_event({
            "event_type": "ai_interaction",
            "event_data": event_data,
            "user_id": user_id,
            "session_id": session_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": {}
        })

    async def track_feature_usage(self, user_id: Optional[str], session_id: str,
                                 feature_name: str, usage_data: Dict[str, Any]):
        """Track feature usage events"""
        event_data = {
            "feature_name": feature_name,
            "usage_data": usage_data,
            "timestamp_ms": int(datetime.now(timezone.utc).timestamp() * 1000)
        }

        await self.track_event({
            "event_type": "feature_usage",
            "event_data": event_data,
            "user_id": user_id,
            "session_id": session_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": {}
        })

    def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        return {
            "queue_size": self.event_queue.qsize(),
            "max_queue_size": self.event_queue.maxsize,
            "queue_utilization": self.event_queue.qsize() / self.event_queue.maxsize,
            "total_events_tracked": sum(self.event_counts.values()),
            "unique_event_types": len(self.event_counts),
            "active_users": len(self.user_activity),
            "active_sessions": len(self.session_activity)
        }