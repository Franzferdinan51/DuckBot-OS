#!/usr/bin/env python3
"""
Event-Driven Architecture for Service State Changes
Comprehensive event system for real-time monitoring, notifications, and automated responses
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Set, Union
from dataclasses import dataclass, asdict, field
from enum import Enum
from collections import defaultdict, deque
import uuid
import weakref

logger = logging.getLogger(__name__)

class EventType(Enum):
    # Service events
    SERVICE_STARTED = "service_started"
    SERVICE_STOPPED = "service_stopped"
    SERVICE_CRASHED = "service_crashed"
    SERVICE_RESTARTED = "service_restarted"
    SERVICE_HEALTH_CHANGED = "service_health_changed"
    SERVICE_DEGRADED = "service_degraded"
    SERVICE_RECOVERED = "service_recovered"

    # Health events
    HEALTH_CHECK_FAILED = "health_check_failed"
    HEALTH_CHECK_PASSED = "health_check_passed"
    RESPONSE_TIME_SLOW = "response_time_slow"
    MEMORY_HIGH = "memory_high"
    CPU_HIGH = "cpu_high"

    # System events
    SYSTEM_RESOURCE_LOW = "system_resource_low"
    SYSTEM_METRICS_ALERT = "system_metrics_alert"
    SYSTEM_PATTERN_DETECTED = "system_pattern_detected"

    # Alert events
    ALERT_TRIGGERED = "alert_triggered"
    ALERT_ACKNOWLEDGED = "alert_acknowledged"
    ALERT_RESOLVED = "alert_resolved"
    ALERT_ESCALATED = "alert_escalated"

    # Configuration events
    CONFIG_CHANGED = "config_changed"
    CONFIG_RELOADED = "config_reloaded"

    # Monitoring events
    MONITORING_STARTED = "monitoring_started"
    MONITORING_STOPPED = "monitoring_stopped"
    MONITORING_RESTARTED = "monitoring_restarted"

class EventPriority(Enum):
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3

@dataclass
class Event:
    id: str
    type: EventType
    priority: EventPriority
    timestamp: datetime
    source: str
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    correlation_id: Optional[str] = None
    causal_chain: List[str] = field(default_factory=list)

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

@dataclass
class EventSubscription:
    id: str
    event_type: EventType
    handler: Callable
    filter_func: Optional[Callable[[Event], bool]] = None
    priority: int = 0
    max_concurrent: int = 1
    timeout: Optional[float] = None
    retry_count: int = 0
    active: bool = True
    created_at: datetime = field(default_factory=datetime.now)

class EventSystem:
    """Comprehensive event-driven architecture for service monitoring"""

    def __init__(self):
        self.subscriptions: Dict[EventType, List[EventSubscription]] = defaultdict(list)
        self.event_history: deque = deque(maxlen=10000)
        self.active_correlations: Dict[str, List[Event]] = defaultdict(list)
        self.dead_letter_queue: deque = deque(maxlen=1000)
        self.metrics = {
            'events_processed': 0,
            'events_failed': 0,
            'subscribers_active': 0,
            'average_processing_time': 0.0,
            'dead_letter_count': 0
        }

        # Event processors
        self.processors: Dict[str, Callable] = {}

        # Background tasks
        self._background_tasks: Set[asyncio.Task] = set()
        self._running = False

        # Event bus for cross-process communication
        self._event_bus = asyncio.Queue(maxsize=10000)

        # Initialize default processors
        self._initialize_processors()

    def _initialize_processors(self):
        """Initialize default event processors"""
        self.processors = {
            'correlation': self._process_correlations,
            'aggregation': self._process_aggregations,
            'escalation': self._process_escalations,
            'persistence': self._process_persistence,
            'metrics': self._process_metrics
        }

    async def start(self):
        """Start the event system"""
        if self._running:
            return

        self._running = True
        logger.info("Starting event system")

        # Start background processors
        tasks = [
            asyncio.create_task(self._event_processor()),
            asyncio.create_task(self._correlation_processor()),
            asyncio.create_task(self _dead_letter_processor()),
            asyncio.create_task(self._metrics_collector())
        ]

        self._background_tasks.update(tasks)

    async def stop(self):
        """Stop the event system"""
        if not self._running:
            return

        self._running = False
        logger.info("Stopping event system")

        # Cancel background tasks
        for task in self._background_tasks:
            task.cancel()

        # Wait for tasks to complete
        if self._background_tasks:
            await asyncio.gather(*self._background_tasks, return_exceptions=True)

        self._background_tasks.clear()

    def subscribe(self,
                 event_type: EventType,
                 handler: Callable,
                 filter_func: Optional[Callable[[Event], bool]] = None,
                 priority: int = 0,
                 max_concurrent: int = 1,
                 timeout: Optional[float] = None,
                 retry_count: int = 0) -> str:
        """Subscribe to events"""
        subscription_id = str(uuid.uuid4())
        subscription = EventSubscription(
            id=subscription_id,
            event_type=event_type,
            handler=handler,
            filter_func=filter_func,
            priority=priority,
            max_concurrent=max_concurrent,
            timeout=timeout,
            retry_count=retry_count
        )

        # Add subscription in priority order
        subscriptions = self.subscriptions[event_type]
        subscriptions.append(subscription)
        subscriptions.sort(key=lambda x: x.priority, reverse=True)

        logger.debug(f"Added subscription {subscription_id} for {event_type.value}")
        return subscription_id

    def unsubscribe(self, subscription_id: str) -> bool:
        """Unsubscribe from events"""
        for event_type, subscriptions in self.subscriptions.items():
            for i, subscription in enumerate(subscriptions):
                if subscription.id == subscription_id:
                    subscription.active = False
                    subscriptions.pop(i)
                    logger.debug(f"Removed subscription {subscription_id}")
                    return True
        return False

    async def emit(self,
                  event_type: EventType,
                  source: str,
                  data: Dict[str, Any] = None,
                  priority: EventPriority = EventPriority.NORMAL,
                  correlation_id: Optional[str] = None,
                  metadata: Dict[str, Any] = None) -> str:
        """Emit an event"""
        event = Event(
            id=str(uuid.uuid4()),
            type=event_type,
            priority=priority,
            timestamp=datetime.now(),
            source=source,
            data=data or {},
            metadata=metadata or {},
            correlation_id=correlation_id
        )

        # Add to event bus for processing
        try:
            await self._event_bus.put(event)
            logger.debug(f"Emitted event {event.id}: {event_type.value}")
            return event.id
        except asyncio.QueueFull:
            logger.error(f"Event bus full, dropping event {event.id}")
            return ""

    async def emit_with_correlation(self,
                                   event_type: EventType,
                                   source: str,
                                   data: Dict[str, Any] = None,
                                   priority: EventPriority = EventPriority.NORMAL,
                                   causal_events: List[str] = None) -> str:
        """Emit an event with correlation tracking"""
        correlation_id = causal_events[0] if causal_events else str(uuid.uuid4())

        event = Event(
            id=str(uuid.uuid4()),
            type=event_type,
            priority=priority,
            timestamp=datetime.now(),
            source=source,
            data=data or {},
            correlation_id=correlation_id,
            causal_chain=causal_events or []
        )

        try:
            await self._event_bus.put(event)
            logger.debug(f"Emitted correlated event {event.id}: {event_type.value}")
            return event.id
        except asyncio.QueueFull:
            logger.error(f"Event bus full, dropping event {event.id}")
            return ""

    async def _event_processor(self):
        """Process events from the event bus"""
        while self._running:
            try:
                event = await asyncio.wait_for(self._event_bus.get(), timeout=1.0)

                # Add to history
                self.event_history.append(event)

                # Process through all processors
                await self._process_event_through_processors(event)

                # Deliver to subscribers
                await self._deliver_to_subscribers(event)

                # Update metrics
                self.metrics['events_processed'] += 1

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error processing event: {e}")
                self.metrics['events_failed'] += 1

    async def _process_event_through_processors(self, event: Event):
        """Process event through all registered processors"""
        for processor_name, processor in self.processors.items():
            try:
                if asyncio.iscoroutinefunction(processor):
                    await processor(event)
                else:
                    processor(event)
            except Exception as e:
                logger.error(f"Error in processor {processor_name}: {e}")

    async def _deliver_to_subscribers(self, event: Event):
        """Deliver event to all relevant subscribers"""
        subscriptions = self.subscriptions.get(event.type, [])

        # Filter inactive subscriptions
        active_subscriptions = [s for s in subscriptions if s.active]

        if not active_subscriptions:
            return

        # Create tasks for concurrent delivery
        tasks = []
        for subscription in active_subscriptions:
            # Apply filter if present
            if subscription.filter_func and not subscription.filter_func(event):
                continue

            task = asyncio.create_task(
                self._deliver_to_subscriber(subscription, event)
            )
            tasks.append(task)

        # Wait for all deliveries with timeout
        if tasks:
            try:
                await asyncio.wait_for(
                    asyncio.gather(*tasks, return_exceptions=True),
                    timeout=30.0
                )
            except asyncio.TimeoutError:
                logger.warning(f"Timeout delivering event {event.id} to subscribers")

    async def _deliver_to_subscriber(self, subscription: EventSubscription, event: Event):
        """Deliver event to a specific subscriber"""
        start_time = time.time()

        try:
            # Apply timeout if specified
            if subscription.timeout:
                await asyncio.wait_for(
                    self._execute_handler(subscription, event),
                    timeout=subscription.timeout
                )
            else:
                await self._execute_handler(subscription, event)

            # Update metrics
            processing_time = time.time() - start_time
            self._update_processing_time(processing_time)

        except asyncio.TimeoutError:
            logger.warning(f"Timeout in subscription {subscription.id} for event {event.id}")
            await self._handle_failed_delivery(subscription, event, "timeout")
        except Exception as e:
            logger.error(f"Error delivering to subscription {subscription.id}: {e}")
            await self._handle_failed_delivery(subscription, event, str(e))

    async def _execute_handler(self, subscription: EventSubscription, event: Event):
        """Execute event handler with retry logic"""
        attempts = 0
        last_error = None

        while attempts <= subscription.retry_count:
            try:
                if asyncio.iscoroutinefunction(subscription.handler):
                    await subscription.handler(event)
                else:
                    subscription.handler(event)
                return
            except Exception as e:
                last_error = e
                attempts += 1
                if attempts <= subscription.retry_count:
                    await asyncio.sleep(2 ** attempts)  # Exponential backoff
                else:
                    raise

        raise last_error

    async def _handle_failed_delivery(self, subscription: EventSubscription, event: Event, error: str):
        """Handle failed event delivery"""
        # Add to dead letter queue
        self.dead_letter_queue.append({
            'event': event,
            'subscription_id': subscription.id,
            'error': error,
            'timestamp': datetime.now()
        })

        self.metrics['dead_letter_count'] += 1

        # Log the failure
        logger.error(f"Failed to deliver event {event.id} to subscription {subscription.id}: {error}")

    def _update_processing_time(self, processing_time: float):
        """Update average processing time metric"""
        current_avg = self.metrics['average_processing_time']
        count = self.metrics['events_processed']
        self.metrics['average_processing_time'] = (current_avg * (count - 1) + processing_time) / count

    async def _correlation_processor(self):
        """Process event correlations"""
        while self._running:
            try:
                await asyncio.sleep(60)  # Process every minute

                # Analyze recent events for correlations
                recent_events = list(self.event_history)[-1000:]
                await self._analyze_correlations(recent_events)

            except Exception as e:
                logger.error(f"Error in correlation processor: {e}")

    async def _analyze_correlations(self, events: List[Event]):
        """Analyze events for temporal correlations"""
        # Group events by time windows
        time_windows = defaultdict(list)
        window_size = timedelta(minutes=5)

        for event in events:
            window_key = event.timestamp.replace(second=0, microsecond=0)
            time_windows[window_key].append(event)

        # Find correlated events
        for window_time, window_events in time_windows.items():
            if len(window_events) > 1:
                # Look for patterns like: service crashes -> restarts -> health changes
                service_events = defaultdict(list)
                for event in window_events:
                    if hasattr(event.data, 'get') and event.data.get('service_name'):
                        service_name = event.data['service_name']
                        service_events[service_name].append(event)

                # Analyze per-service event sequences
                for service_name, service_event_sequence in service_events.items():
                    if len(service_event_sequence) > 1:
                        await self._process_event_sequence(service_name, service_event_sequence)

    async def _process_event_sequence(self, service_name: str, events: List[Event]):
        """Process a sequence of events for a service"""
        # Sort by timestamp
        events.sort(key=lambda x: x.timestamp)

        # Look for specific patterns
        event_types = [event.type for event in events]

        # Pattern: CRASHED -> RESTARTED -> HEALTH_CHANGED
        if (EventType.SERVICE_CRASHED in event_types and
            EventType.SERVICE_RESTARTED in event_types and
            EventType.SERVICE_HEALTH_CHANGED in event_types):

            # Emit a correlated event
            await self.emit(
                EventType.SYSTEM_PATTERN_DETECTED,
                "event_system",
                {
                    'pattern': 'crash_restart_cycle',
                    'service_name': service_name,
                    'event_count': len(events),
                    'duration_minutes': (events[-1].timestamp - events[0].timestamp).total_seconds() / 60
                },
                priority=EventPriority.HIGH
            )

    async def _dead_letter_processor(self):
        """Process dead letter queue"""
        while self._running:
            try:
                await asyncio.sleep(300)  # Process every 5 minutes

                if not self.dead_letter_queue:
                    continue

                # Try to redeliver or log failed events
                logger.info(f"Processing {len(self.dead_letter_queue)} dead letter events")

                # Log and clear dead letters (in production, you might retry)
                while self.dead_letter_queue:
                    dead_letter = self.dead_letter_queue.popleft()
                    logger.warning(f"Dead letter event: {dead_letter['event'].id} - {dead_letter['error']}")

            except Exception as e:
                logger.error(f"Error in dead letter processor: {e}")

    async def _metrics_collector(self):
        """Collect and report metrics"""
        while self._running:
            try:
                await asyncio.sleep(60)  # Collect every minute

                # Update subscriber count
                active_count = sum(len(subs) for subs in self.subscriptions.values())
                self.metrics['subscribers_active'] = active_count

                # Log metrics
                logger.debug(f"Event system metrics: {self.metrics}")

            except Exception as e:
                logger.error(f"Error in metrics collector: {e}")

    # Processor implementations
    def _process_correlations(self, event: Event):
        """Process event correlations"""
        if event.correlation_id:
            self.active_correlations[event.correlation_id].append(event)

            # Clean up old correlations
            cutoff_time = datetime.now() - timedelta(hours=1)
            self.active_correlations = {
                k: v for k, v in self.active_correlations.items()
                if any(e.timestamp > cutoff_time for e in v)
            }

    def _process_aggregations(self, event: Event):
        """Process event aggregations"""
        # This would aggregate similar events for reporting
        pass

    def _process_escalations(self, event: Event):
        """Process event escalations"""
        # Escalate critical events
        if (event.priority == EventPriority.CRITICAL and
            event.type in [EventType.SERVICE_CRASHED, EventType.SYSTEM_RESOURCE_LOW]):

            # Check if this is a repeated critical event
            recent_critical = [
                e for e in self.event_history[-100:]
                if (e.priority == EventPriority.CRITICAL and
                    e.source == event.source and
                    e.type == event.type and
                    (datetime.now() - e.timestamp).total_seconds() < 300)  # 5 minutes
            ]

            if len(recent_critical) > 2:
                # Emit escalation event
                asyncio.create_task(self.emit(
                    EventType.ALERT_ESCALATED,
                    "event_system",
                    {
                        'original_event_id': event.id,
                        'occurrence_count': len(recent_critical),
                        'escalation_reason': 'repeated_critical_events'
                    },
                    priority=EventPriority.CRITICAL
                ))

    def _process_persistence(self, event: Event):
        """Process event persistence"""
        # This would persist events to a database
        # For now, we'll just keep them in memory (event_history)
        pass

    def _process_metrics(self, event: Event):
        """Process metrics from events"""
        # Extract and store metrics from events
        if hasattr(event.data, 'get'):
            metrics = event.data.get('metrics', {})
            if metrics:
                # This would update various metric stores
                pass

    # Query methods
    def get_event_history(self,
                         event_type: Optional[EventType] = None,
                         source: Optional[str] = None,
                         hours: int = 24,
                         limit: int = 100) -> List[Event]:
        """Get event history with optional filtering"""
        cutoff_time = datetime.now() - timedelta(hours=hours)

        events = [e for e in self.event_history if e.timestamp > cutoff_time]

        if event_type:
            events = [e for e in events if e.type == event_type]
        if source:
            events = [e for e in events if e.source == source]

        return events[-limit:]

    def get_active_subscriptions(self) -> List[EventSubscription]:
        """Get all active subscriptions"""
        all_subscriptions = []
        for subscriptions in self.subscriptions.values():
            all_subscriptions.extend(subscriptions)
        return [s for s in all_subscriptions if s.active]

    def get_metrics(self) -> Dict[str, Any]:
        """Get event system metrics"""
        return {
            **self.metrics,
            'active_subscriptions': len(self.get_active_subscriptions()),
            'event_types_monitored': len(self.subscriptions),
            'dead_letter_queue_size': len(self.dead_letter_queue),
            'active_correlations': len(self.active_correlations),
            'timestamp': datetime.now().isoformat()
        }

    def get_correlation_chains(self, correlation_id: str) -> List[Event]:
        """Get all events in a correlation chain"""
        return self.active_correlations.get(correlation_id, [])

# Global event system instance
_event_system: Optional[EventSystem] = None

def get_event_system() -> EventSystem:
    """Get the global event system instance"""
    global _event_system
    if _event_system is None:
        _event_system = EventSystem()
    return _event_system

async def start_event_system():
    """Start the global event system"""
    system = get_event_system()
    await system.start()
    return system

async def stop_event_system():
    """Stop the global event system"""
    system = get_event_system()
    await system.stop()

# Convenience functions
async def emit_event(event_type: EventType, source: str, data: Dict[str, Any] = None, **kwargs) -> str:
    """Convenience function to emit events"""
    system = get_event_system()
    return await system.emit(event_type, source, data, **kwargs)

def subscribe_to_event(event_type: EventType, handler: Callable, **kwargs) -> str:
    """Convenience function to subscribe to events"""
    system = get_event_system()
    return system.subscribe(event_type, handler, **kwargs)