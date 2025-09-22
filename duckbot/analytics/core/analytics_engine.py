# duckbot/analytics/core/analytics_engine.py
import asyncio
import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import json

@dataclass
class AnalyticsConfig:
    """Configuration for the analytics engine"""
    enabled: bool = True
    sampling_rate: float = 1.0  # 1.0 = 100% of events
    batch_size: int = 100
    flush_interval: float = 30.0  # seconds
    storage_retention_days: int = 365
    enable_predictive: bool = True
    enable_realtime: bool = True

class AnalyticsEngine:
    """Main analytics engine that orchestrates all analytics components"""

    def __init__(self, logger):
        self.logger = logger
        self.config = AnalyticsConfig()
        self.is_initialized = False
        self.is_running = False

        # Core components
        self.event_tracker = None
        self.session_manager = None
        self.metrics_collector = None
        self.analytics_db = None

        # Analytics engines
        self.user_behavior_analyzer = None
        self.performance_analyzer = None
        self.business_intelligence_engine = None
        self.predictive_analytics_engine = None

        # Background tasks
        self._flush_task = None
        self._analytics_task = None

        # Performance tracking
        self.start_time = time.time()
        self.events_processed = 0
        self.events_dropped = 0

    def initialize(self) -> bool:
        """Initialize all analytics components"""
        try:
            self.logger.info("Initializing DuckBot Analytics Engine v1.0.0")

            # Initialize storage first
            from .storage.analytics_db import AnalyticsDatabase
            self.analytics_db = AnalyticsDatabase(self.logger)
            self.analytics_db.initialize()

            # Initialize core components
            from .event_tracker import EventTracker
            self.event_tracker = EventTracker(self.logger, self.config)

            from .session_manager import SessionManager
            self.session_manager = SessionManager(self.logger, self.analytics_db)

            from .metrics_collector import MetricsCollector
            self.metrics_collector = MetricsCollector(self.logger, self.config)

            # Initialize analytics engines
            from ..analytics.user_behavior import UserBehaviorAnalyzer
            self.user_behavior_analyzer = UserBehaviorAnalyzer(
                self.logger, self.analytics_db, self.config
            )

            from ..analytics.performance import PerformanceAnalyzer
            self.performance_analyzer = PerformanceAnalyzer(
                self.logger, self.analytics_db, self.config
            )

            from ..analytics.business_intelligence import BusinessIntelligenceEngine
            self.business_intelligence_engine = BusinessIntelligenceEngine(
                self.logger, self.analytics_db, self.config
            )

            from ..analytics.predictive import PredictiveAnalyticsEngine
            self.predictive_analytics_engine = PredictiveAnalyticsEngine(
                self.logger, self.analytics_db, self.config
            )

            self.is_initialized = True
            self.logger.info("Analytics engine initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize analytics engine: {e}")
            return False

    async def start(self):
        """Start the analytics engine"""
        if not self.is_initialized:
            self.logger.error("Analytics engine not initialized")
            return False

        if self.is_running:
            self.logger.warning("Analytics engine already running")
            return True

        try:
            self.logger.info("Starting analytics engine")
            self.is_running = True

            # Start background tasks
            self._flush_task = asyncio.create_task(self._flush_events_loop())
            self._analytics_task = asyncio.create_task(self._analytics_processing_loop())

            # Start all analytics engines
            await self.user_behavior_analyzer.start()
            await self.performance_analyzer.start()
            await self.business_intelligence_engine.start()

            if self.config.enable_predictive:
                await self.predictive_analytics_engine.start()

            self.logger.info("Analytics engine started successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to start analytics engine: {e}")
            await self.stop()
            return False

    async def stop(self):
        """Stop the analytics engine"""
        self.logger.info("Stopping analytics engine")
        self.is_running = False

        # Cancel background tasks
        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass

        if self._analytics_task:
            self._analytics_task.cancel()
            try:
                await self._analytics_task
            except asyncio.CancelledError:
                pass

        # Stop all analytics engines
        if self.user_behavior_analyzer:
            await self.user_behavior_analyzer.stop()

        if self.performance_analyzer:
            await self.performance_analyzer.stop()

        if self.business_intelligence_engine:
            await self.business_intelligence_engine.stop()

        if self.predictive_analytics_engine:
            await self.predictive_analytics_engine.stop()

        # Flush remaining events
        await self._flush_events()

        self.logger.info("Analytics engine stopped")

    async def track_event(self, event_type: str, event_data: Dict[str, Any],
                        user_id: Optional[str] = None, session_id: Optional[str] = None):
        """Track an analytics event"""
        if not self.is_running or not self.config.enabled:
            return

        # Apply sampling
        if self.config.sampling_rate < 1.0:
            import random
            if random.random() > self.config.sampling_rate:
                self.events_dropped += 1
                return

        try:
            # Get or create session
            if session_id is None:
                session_id = await self.session_manager.get_or_create_session(user_id)

            # Create event object
            event = {
                "event_type": event_type,
                "event_data": event_data,
                "user_id": user_id,
                "session_id": session_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "metadata": {
                    "version": "1.0.0",
                    "source": "duckbot_analytics"
                }
            }

            # Add to event tracker
            await self.event_tracker.track_event(event)
            self.events_processed += 1

            # Track metrics
            await self.metrics_collector.increment_counter(
                "analytics_events_total",
                {"event_type": event_type}
            )

        except Exception as e:
            self.logger.error(f"Failed to track event {event_type}: {e}")
            self.events_dropped += 1

    async def get_analytics_summary(self) -> Dict[str, Any]:
        """Get a comprehensive analytics summary"""
        if not self.is_running:
            return {"error": "Analytics engine not running"}

        try:
            uptime = time.time() - self.start_time

            summary = {
                "engine_status": {
                    "is_running": self.is_running,
                    "uptime_seconds": int(uptime),
                    "events_processed": self.events_processed,
                    "events_dropped": self.events_dropped,
                    "processing_rate": self.events_processed / uptime if uptime > 0 else 0,
                    "sampling_rate": self.config.sampling_rate
                },
                "user_behavior": await self.user_behavior_analyzer.get_summary(),
                "performance": await self.performance_analyzer.get_summary(),
                "business_intelligence": await self.business_intelligence_engine.get_summary()
            }

            if self.config.enable_predictive:
                summary["predictive_analytics"] = await self.predictive_analytics_engine.get_summary()

            return summary

        except Exception as e:
            self.logger.error(f"Failed to get analytics summary: {e}")
            return {"error": str(e)}

    async def _flush_events_loop(self):
        """Background loop for flushing events"""
        while self.is_running:
            try:
                await asyncio.sleep(self.config.flush_interval)
                await self._flush_events()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in flush events loop: {e}")

    async def _analytics_processing_loop(self):
        """Background loop for processing analytics"""
        while self.is_running:
            try:
                await asyncio.sleep(60.0)  # Process analytics every minute

                # Run analytics processing
                await self.user_behavior_analyzer.process_analytics()
                await self.performance_analyzer.process_analytics()
                await self.business_intelligence_engine.process_analytics()

                if self.config.enable_predictive:
                    await self.predictive_analytics_engine.process_analytics()

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in analytics processing loop: {e}")

    async def _flush_events(self):
        """Flush pending events to storage"""
        try:
            events = await self.event_tracker.get_pending_events()
            if events:
                await self.analytics_db.store_events(events)
                await self.event_tracker.clear_processed_events()
                self.logger.debug(f"Flushed {len(events)} events to storage")
        except Exception as e:
            self.logger.error(f"Failed to flush events: {e}")