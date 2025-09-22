# duckbot/analytics/core/session_manager.py
import asyncio
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
import json

@dataclass
class SessionInfo:
    """Session information"""
    session_id: str
    user_id: Optional[str]
    start_time: str
    last_activity: str
    ip_address: Optional[str]
    user_agent: Optional[str]
    referrer: Optional[str]
    page_count: int
    event_count: int
    features_used: List[str]
    ai_interactions: int
    duration_seconds: float = 0.0
    is_active: bool = True

class SessionManager:
    """Manages user sessions for analytics"""

    def __init__(self, logger, analytics_db):
        self.logger = logger
        self.analytics_db = analytics_db
        self.sessions: Dict[str, SessionInfo] = {}
        self.user_sessions: Dict[str, List[str]] = {}
        self.session_timeout = 30 * 60  # 30 minutes
        self.cleanup_task = None

    async def initialize(self):
        """Initialize session manager"""
        self.logger.info("Initializing session manager")
        # Load existing sessions from database
        await self._load_sessions()

    async def start(self):
        """Start session manager background tasks"""
        self.cleanup_task = asyncio.create_task(self._cleanup_sessions_loop())

    async def stop(self):
        """Stop session manager"""
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass

    async def get_or_create_session(self, user_id: Optional[str] = None,
                                  ip_address: Optional[str] = None,
                                  user_agent: Optional[str] = None,
                                  referrer: Optional[str] = None) -> str:
        """Get existing session or create new one"""
        try:
            # Check if user has active session
            if user_id:
                active_sessions = self.user_sessions.get(user_id, [])
                for session_id in active_sessions:
                    session = self.sessions.get(session_id)
                    if session and session.is_active:
                        # Update last activity
                        session.last_activity = datetime.now(timezone.utc).isoformat()
                        await self._save_session(session)
                        return session_id

            # Create new session
            session_id = str(uuid.uuid4())
            now = datetime.now(timezone.utc)

            session = SessionInfo(
                session_id=session_id,
                user_id=user_id,
                start_time=now.isoformat(),
                last_activity=now.isoformat(),
                ip_address=ip_address,
                user_agent=user_agent,
                referrer=referrer,
                page_count=0,
                event_count=0,
                features_used=[],
                ai_interactions=0,
                is_active=True
            )

            # Store session
            self.sessions[session_id] = session

            # Add to user sessions mapping
            if user_id:
                if user_id not in self.user_sessions:
                    self.user_sessions[user_id] = []
                self.user_sessions[user_id].append(session_id)

            # Save to database
            await self._save_session(session)

            self.logger.debug(f"Created new session: {session_id}")
            return session_id

        except Exception as e:
            self.logger.error(f"Failed to get or create session: {e}")
            return str(uuid.uuid4())  # Fallback session ID

    async def update_session_activity(self, session_id: str, activity_data: Dict[str, Any]):
        """Update session activity data"""
        try:
            session = self.sessions.get(session_id)
            if not session:
                return False

            # Update last activity
            session.last_activity = datetime.now(timezone.utc).isoformat()

            # Update counters
            if "page_count" in activity_data:
                session.page_count += activity_data["page_count"]

            if "event_count" in activity_data:
                session.event_count += activity_data["event_count"]

            if "features_used" in activity_data:
                for feature in activity_data["features_used"]:
                    if feature not in session.features_used:
                        session.features_used.append(feature)

            if "ai_interactions" in activity_data:
                session.ai_interactions += activity_data["ai_interactions"]

            # Update duration
            start_time = datetime.fromisoformat(session.start_time.replace('Z', '+00:00'))
            last_activity = datetime.fromisoformat(session.last_activity.replace('Z', '+00:00'))
            session.duration_seconds = (last_activity - start_time).total_seconds()

            # Save updated session
            await self._save_session(session)

            return True

        except Exception as e:
            self.logger.error(f"Failed to update session activity: {e}")
            return False

    async def end_session(self, session_id: str):
        """End a session"""
        try:
            session = self.sessions.get(session_id)
            if not session:
                return False

            session.is_active = False
            session.last_activity = datetime.now(timezone.utc).isoformat()

            # Calculate final duration
            start_time = datetime.fromisoformat(session.start_time.replace('Z', '+00:00'))
            end_time = datetime.fromisoformat(session.last_activity.replace('Z', '+00:00'))
            session.duration_seconds = (end_time - start_time).total_seconds()

            # Save to database
            await self._save_session(session)

            # Remove from active sessions
            if session_id in self.sessions:
                del self.sessions[session_id]

            # Remove from user sessions mapping
            if session.user_id and session.user_id in self.user_sessions:
                user_sessions = self.user_sessions[session.user_id]
                if session_id in user_sessions:
                    user_sessions.remove(session_id)

            self.logger.debug(f"Ended session: {session_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to end session: {e}")
            return False

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session information"""
        session = self.sessions.get(session_id)
        if session:
            return asdict(session)

        # Try to get from database
        session_data = await self.analytics_db.get_session(session_id)
        return session_data

    async def get_user_sessions(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get sessions for a user"""
        sessions = []
        session_ids = self.user_sessions.get(user_id, [])

        for session_id in session_ids[-limit:]:
            session = self.sessions.get(session_id)
            if session:
                sessions.append(asdict(session))

        return sessions

    async def get_active_sessions(self) -> List[Dict[str, Any]]:
        """Get all active sessions"""
        active_sessions = []
        now = datetime.now(timezone.utc)

        for session in self.sessions.values():
            if session.is_active:
                # Check if session has expired
                last_activity = datetime.fromisoformat(session.last_activity.replace('Z', '+00:00'))
                if (now - last_activity).total_seconds() < self.session_timeout:
                    active_sessions.append(asdict(session))

        return active_sessions

    async def get_session_stats(self) -> Dict[str, Any]:
        """Get session statistics"""
        try:
            now = datetime.now(timezone.utc)
            total_sessions = len(self.sessions)
            active_sessions = 0
            total_users = len(self.user_sessions)

            for session in self.sessions.values():
                if session.is_active:
                    last_activity = datetime.fromisoformat(session.last_activity.replace('Z', '+00:00'))
                    if (now - last_activity).total_seconds() < self.session_timeout:
                        active_sessions += 1

            # Calculate average session duration
            durations = []
            for session in self.sessions.values():
                if session.duration_seconds > 0:
                    durations.append(session.duration_seconds)

            avg_duration = sum(durations) / len(durations) if durations else 0

            # Get most used features
            all_features = []
            for session in self.sessions.values():
                all_features.extend(session.features_used)

            feature_counts = {}
            for feature in all_features:
                feature_counts[feature] = feature_counts.get(feature, 0) + 1

            top_features = sorted(feature_counts.items(), key=lambda x: x[1], reverse=True)[:10]

            return {
                "total_sessions": total_sessions,
                "active_sessions": active_sessions,
                "unique_users": total_users,
                "average_session_duration": avg_duration,
                "session_timeout_seconds": self.session_timeout,
                "top_features": [{"feature": f, "count": c} for f, c in top_features],
                "total_ai_interactions": sum(s.ai_interactions for s in self.sessions.values()),
                "total_events": sum(s.event_count for s in self.sessions.values()),
                "total_page_views": sum(s.page_count for s in self.sessions.values())
            }

        except Exception as e:
            self.logger.error(f"Failed to get session stats: {e}")
            return {"error": str(e)}

    async def _cleanup_sessions_loop(self):
        """Background loop for cleaning up expired sessions"""
        while True:
            try:
                await asyncio.sleep(300)  # Check every 5 minutes
                await self._cleanup_expired_sessions()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in session cleanup loop: {e}")

    async def _cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        try:
            now = datetime.now(timezone.utc)
            expired_sessions = []

            for session_id, session in self.sessions.items():
                if session.is_active:
                    last_activity = datetime.fromisoformat(session.last_activity.replace('Z', '+00:00'))
                    if (now - last_activity).total_seconds() > self.session_timeout:
                        expired_sessions.append(session_id)

            # End expired sessions
            for session_id in expired_sessions:
                await self.end_session(session_id)

            if expired_sessions:
                self.logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")

        except Exception as e:
            self.logger.error(f"Failed to cleanup expired sessions: {e}")

    async def _save_session(self, session: SessionInfo):
        """Save session to database"""
        try:
            await self.analytics_db.save_session(asdict(session))
        except Exception as e:
            self.logger.error(f"Failed to save session to database: {e}")

    async def _load_sessions(self):
        """Load sessions from database"""
        try:
            # This would load recent sessions from database
            # For now, we'll start with empty sessions
            pass
        except Exception as e:
            self.logger.error(f"Failed to load sessions from database: {e}")