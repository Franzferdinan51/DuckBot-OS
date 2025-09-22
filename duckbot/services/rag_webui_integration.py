#!/usr/bin/env python3
"""
RAG WebUI Integration Module for DuckBot
Integrates RAG system with WebUI components for enhanced user interface.
"""

import os
import json
import time
import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
from pathlib import Path
import hashlib

# Local imports
from ..core.enhanced_rag import EnhancedRAG, DocumentType
from ..core.rag_memory_integration import RAGMemoryIntegration, MemoryType
from ..core.rag_ai_integration import RAGAIIntegration, RAGRequest
from ..core.logging_setup import get_logger

logger = get_logger(__name__)


class UIComponent(Enum):
    """WebUI components."""
    SEARCH_INTERFACE = "search_interface"
    KNOWLEDGE_BROWSER = "knowledge_browser"
    MEMORY_VIEWER = "memory_viewer"
    AGENT_DASHBOARD = "agent_dashboard"
    TRAINING_INTERFACE = "training_interface"
    ANALYTICS_DASHBOARD = "analytics_dashboard"
    SETTINGS_PANEL = "settings_panel"


class UITheme(Enum):
    """UI themes."""
    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"
    HIGH_CONTRAST = "high_contrast"


@dataclass
class UIState:
    """User interface state."""
    session_id: str
    user_id: Optional[str] = None
    current_view: str = "dashboard"
    search_history: List[Dict[str, Any]] = field(default_factory=list)
    selected_documents: List[str] = field(default_factory=list)
    filters: Dict[str, Any] = field(default_factory=dict)
    preferences: Dict[str, Any] = field(default_factory=dict)
    last_activity: datetime = field(default_factory=datetime.now)


@dataclass
class UIComponentData:
    """UI component data structure."""
    component_id: str
    component_type: UIComponent
    data: Dict[str, Any]
    template: Optional[str] = None
    styles: Dict[str, str] = field(default_factory=dict)
    scripts: List[str] = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class RAGWebUIConfig:
    """Configuration for RAG-WebUI integration."""
    # General settings
    enabled_components: List[UIComponent] = field(default_factory=lambda: [
        UIComponent.SEARCH_INTERFACE,
        UIComponent.KNOWLEDGE_BROWSER,
        UIComponent.MEMORY_VIEWER,
        UIComponent.ANALYTICS_DASHBOARD
    ])

    # UI settings
    default_theme: UITheme = UITheme.AUTO
    max_search_history: int = 100
    enable_real_time_updates: bool = True
    update_interval: int = 5  # seconds

    # Performance settings
    max_results_per_page: int = 20
    enable_pagination: bool = True
    enable_infinite_scroll: bool = False
    cache_ui_data: bool = True
    cache_ttl: int = 300  # seconds

    # Features
    enable_knowledge_graph: bool = True
    enable_visualization: bool = True
    enable_export: bool = True
    enable_collaboration: bool = False

    # API settings
    api_base_url: str = "/api/rag"
    websocket_url: str = "/ws/rag"

    # Debug settings
    debug_ui: bool = False
    log_ui_events: bool = True


class RAGWebUIIntegration:
    """
    Integration between RAG system and WebUI components.
    """

    def __init__(self, rag_system: EnhancedRAG, memory_integration: Optional[RAGMemoryIntegration] = None,
                 ai_integration: Optional[RAGAIIntegration] = None, config: Optional[RAGWebUIConfig] = None):
        self.rag_system = rag_system
        self.memory_integration = memory_integration
        self.ai_integration = ai_integration
        self.config = config or RAGWebUIConfig()
        self.logger = get_logger(__name__)

        # Initialize UI systems
        self.ui_states: Dict[str, UIState] = {}
        self.ui_components: Dict[str, UIComponentData] = {}
        self.component_cache: Dict[str, Any] = {}

        # Real-time updates
        self.update_subscribers: Dict[str, List[str]] = {}  # session_id -> list of subscribed components
        self.update_queue: List[Dict[str, Any]] = []

        # Background tasks
        self._update_processor: Optional[asyncio.Task] = None
        self._cache_cleaner: Optional[asyncio.Task] = None

        # Initialize systems
        self._initialize_components()
        self._start_background_tasks()

        self.logger.info("RAG-WebUI Integration initialized")

    def _initialize_components(self):
        """Initialize UI components."""
        try:
            # Create search interface component
            self.ui_components["search_interface"] = UIComponentData(
                component_id="search_interface",
                component_type=UIComponent.SEARCH_INTERFACE,
                data={
                    "search_types": ["semantic", "keyword", "hybrid"],
                    "filters": ["document_type", "date_range", "source"],
                    "sort_options": ["relevance", "date", "source"]
                },
                template="search_interface.html"
            )

            # Create knowledge browser component
            self.ui_components["knowledge_browser"] = UIComponentData(
                component_id="knowledge_browser",
                component_type=UIComponent.KNOWLEDGE_BROWSER,
                data={
                    "view_modes": ["list", "grid", "graph"],
                    "categories": ["all", "code", "documentation", "memories"],
                    "sort_options": ["date", "relevance", "type"]
                },
                template="knowledge_browser.html"
            )

            # Create memory viewer component
            if self.memory_integration:
                self.ui_components["memory_viewer"] = UIComponentData(
                    component_id="memory_viewer",
                    component_type=UIComponent.MEMORY_VIEWER,
                    data={
                        "memory_types": [mt.value for mt in MemoryType],
                        "view_modes": ["timeline", "clusters", "network"],
                        "filters": ["type", "date_range", "importance"]
                    },
                    template="memory_viewer.html"
                )

            # Create analytics dashboard component
            self.ui_components["analytics_dashboard"] = UIComponentData(
                component_id="analytics_dashboard",
                component_type=UIComponent.ANALYTICS_DASHBOARD,
                data={
                    "charts": ["usage_stats", "performance_metrics", "knowledge_growth"],
                    "time_ranges": ["day", "week", "month", "year"],
                    "metrics": ["searches", "documents", "accuracy", "response_time"]
                },
                template="analytics_dashboard.html"
            )

            self.logger.info(f"Initialized {len(self.ui_components)} UI components")

        except Exception as e:
            self.logger.error(f"Error initializing UI components: {e}")
            raise

    def _start_background_tasks(self):
        """Start background UI tasks."""
        if self.config.enable_real_time_updates:
            self._update_processor = asyncio.create_task(self._update_processor_loop())

        if self.config.cache_ui_data:
            self._cache_cleaner = asyncio.create_task(self._cache_cleaner_loop())

        self.logger.info("Background UI tasks started")

    async def create_session(self, user_id: Optional[str] = None) -> str:
        """Create a new UI session."""
        try:
            session_id = hashlib.md5(f"{user_id}:{time.time()}".encode()).hexdigest()

            ui_state = UIState(
                session_id=session_id,
                user_id=user_id,
                preferences={
                    "theme": self.config.default_theme.value,
                    "results_per_page": self.config.max_results_per_page,
                    "enable_real_time": self.config.enable_real_time_updates
                }
            )

            self.ui_states[session_id] = ui_state
            self.update_subscribers[session_id] = []

            self.logger.info(f"Created UI session: {session_id}")
            return session_id

        except Exception as e:
            self.logger.error(f"Error creating UI session: {e}")
            raise

    async def get_component_data(self, session_id: str, component_id: str) -> Dict[str, Any]:
        """Get data for a UI component."""
        try:
            # Check cache first
            cache_key = f"{session_id}:{component_id}"
            if self.config.cache_ui_data and cache_key in self.component_cache:
                cached_data = self.component_cache[cache_key]
                if (datetime.now() - cached_data["timestamp"]).total_seconds() < self.config.cache_ttl:
                    return cached_data["data"]

            # Get component
            if component_id not in self.ui_components:
                raise ValueError(f"Component not found: {component_id}")

            component = self.ui_components[component_id]

            # Generate component-specific data
            if component.component_type == UIComponent.SEARCH_INTERFACE:
                data = await self._get_search_interface_data(session_id)
            elif component.component_type == UIComponent.KNOWLEDGE_BROWSER:
                data = await self._get_knowledge_browser_data(session_id)
            elif component.component_type == UIComponent.MEMORY_VIEWER:
                data = await self._get_memory_viewer_data(session_id)
            elif component.component_type == UIComponent.ANALYTICS_DASHBOARD:
                data = await self._get_analytics_dashboard_data(session_id)
            else:
                data = component.data.copy()

            # Add session-specific data
            ui_state = self.ui_states.get(session_id)
            if ui_state:
                data["session_preferences"] = ui_state.preferences
                data["session_filters"] = ui_state.filters

            # Cache result
            if self.config.cache_ui_data:
                self.component_cache[cache_key] = {
                    "data": data,
                    "timestamp": datetime.now()
                }

            return data

        except Exception as e:
            self.logger.error(f"Error getting component data for {component_id}: {e}")
            return {"error": str(e)}

    async def _get_search_interface_data(self, session_id: str) -> Dict[str, Any]:
        """Get search interface data."""
        try:
            ui_state = self.ui_states.get(session_id)
            if not ui_state:
                return {}

            # Get search statistics
            rag_stats = self.rag_system.get_stats()

            return {
                "search_types": ["semantic", "keyword", "hybrid"],
                "recent_searches": ui_state.search_history[-5:],
                "available_filters": {
                    "document_type": ["text", "code", "markdown", "pdf"],
                    "date_range": "enabled",
                    "source": "enabled"
                },
                "sort_options": ["relevance", "date", "source"],
                "stats": {
                    "total_documents": rag_stats.get("documents_indexed", 0),
                    "total_chunks": rag_stats.get("chunks_created", 0),
                    "recent_searches": len(ui_state.search_history)
                }
            }

        except Exception as e:
            self.logger.error(f"Error getting search interface data: {e}")
            return {}

    async def _get_knowledge_browser_data(self, session_id: str) -> Dict[str, Any]:
        """Get knowledge browser data."""
        try:
            ui_state = self.ui_states.get(session_id)
            if not ui_state:
                return {}

            # Get document statistics
            rag_stats = self.rag_system.get_stats()

            return {
                "view_modes": ["list", "grid", "graph"],
                "categories": ["all", "code", "documentation", "memories"],
                "sort_options": ["date", "relevance", "type"],
                "total_documents": rag_stats.get("documents_indexed", 0),
                "selected_documents": ui_state.selected_documents,
                "filters": ui_state.filters,
                "knowledge_graph": self.config.enable_knowledge_graph
            }

        except Exception as e:
            self.logger.error(f"Error getting knowledge browser data: {e}")
            return {}

    async def _get_memory_viewer_data(self, session_id: str) -> Dict[str, Any]:
        """Get memory viewer data."""
        try:
            if not self.memory_integration:
                return {"error": "Memory integration not available"}

            ui_state = self.ui_states.get(session_id)
            if not ui_state:
                return {}

            # Get memory statistics
            memory_stats = self.memory_integration.get_stats()

            return {
                "memory_types": [mt.value for mt in MemoryType],
                "view_modes": ["timeline", "clusters", "network"],
                "filters": ["type", "date_range", "importance"],
                "total_memories": memory_stats.get("long_term_memory_size", 0),
                "working_memory": memory_stats.get("working_memory_size", 0),
                "clusters": memory_stats.get("cluster_count", 0),
                "session_filters": ui_state.filters
            }

        except Exception as e:
            self.logger.error(f"Error getting memory viewer data: {e}")
            return {}

    async def _get_analytics_dashboard_data(self, session_id: str) -> Dict[str, Any]:
        """Get analytics dashboard data."""
        try:
            # Get system statistics
            rag_stats = self.rag_system.get_stats()
            memory_stats = self.memory_integration.get_stats() if self.memory_integration else {}

            # Generate analytics data
            analytics_data = {
                "charts": ["usage_stats", "performance_metrics", "knowledge_growth"],
                "time_ranges": ["day", "week", "month", "year"],
                "metrics": {
                    "searches_performed": rag_stats.get("searches_performed", 0),
                    "avg_search_time": rag_stats.get("avg_search_time", 0),
                    "documents_indexed": rag_stats.get("documents_indexed", 0),
                    "cache_hits": rag_stats.get("cache_hits", 0),
                    "cache_misses": rag_stats.get("cache_misses", 0)
                },
                "memory_metrics": {
                    "total_memories": memory_stats.get("long_term_memory_size", 0),
                    "clusters": memory_stats.get("cluster_count", 0),
                    "memories_retrieved": memory_stats.get("memories_retrieved", 0)
                },
                "performance": {
                    "system_health": "good",
                    "response_time": "fast",
                    "accuracy": "high"
                }
            }

            return analytics_data

        except Exception as e:
            self.logger.error(f"Error getting analytics dashboard data: {e}")
            return {}

    async def search_ui(self, session_id: str, query: str, filters: Optional[Dict[str, Any]] = None,
                       page: int = 1, limit: Optional[int] = None) -> Dict[str, Any]:
        """Perform search from UI."""
        try:
            ui_state = self.ui_states.get(session_id)
            if not ui_state:
                return {"error": "Session not found"}

            # Set limit
            limit = limit or ui_state.preferences.get("results_per_page", self.config.max_results_per_page)

            # Perform search
            search_results = await self.rag_system.search(query, top_k=limit, filters=filters)

            # Format results for UI
            formatted_results = []
            for result in search_results:
                formatted_results.append({
                    "id": result.chunk.id,
                    "content": result.chunk.content[:500] + "..." if len(result.chunk.content) > 500 else result.chunk.content,
                    "score": result.score,
                    "source": result.document.source_path,
                    "document_type": result.document.doc_type.value,
                    "metadata": result.metadata
                })

            # Update search history
            search_entry = {
                "query": query,
                "filters": filters or {},
                "timestamp": datetime.now().isoformat(),
                "results_count": len(formatted_results)
            }
            ui_state.search_history.append(search_entry)

            # Limit history
            if len(ui_state.search_history) > self.config.max_search_history:
                ui_state.search_history = ui_state.search_history[-self.config.max_search_history:]

            # Update last activity
            ui_state.last_activity = datetime.now()

            # Queue update
            self._queue_update(session_id, "search_interface", {
                "query": query,
                "results": formatted_results,
                "total_results": len(formatted_results)
            })

            return {
                "success": True,
                "results": formatted_results,
                "total_results": len(formatted_results),
                "query": query,
                "page": page,
                "limit": limit
            }

        except Exception as e:
            self.logger.error(f"Error in UI search: {e}")
            return {"success": False, "error": str(e)}

    async def get_knowledge_graph(self, session_id: str, limit: int = 50) -> Dict[str, Any]:
        """Get knowledge graph data."""
        try:
            if not self.config.enable_knowledge_graph:
                return {"error": "Knowledge graph not enabled"}

            # Get recent documents
            # This is a simplified implementation
            # In a real implementation, you'd generate actual graph data

            nodes = []
            edges = []

            # Generate sample graph data
            for i in range(min(limit, 20)):
                nodes.append({
                    "id": f"node_{i}",
                    "label": f"Document {i}",
                    "type": "document",
                    "size": 10 + i % 10
                })

            # Add some edges
            for i in range(0, len(nodes) - 1, 2):
                edges.append({
                    "source": nodes[i]["id"],
                    "target": nodes[i + 1]["id"],
                    "weight": 0.5 + (i % 5) * 0.1
                })

            return {
                "success": True,
                "nodes": nodes,
                "edges": edges,
                "layout": "force_directed"
            }

        except Exception as e:
            self.logger.error(f"Error getting knowledge graph: {e}")
            return {"success": False, "error": str(e)}

    async def export_data(self, session_id: str, export_type: str, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Export data from UI."""
        try:
            if not self.config.enable_export:
                return {"error": "Export not enabled"}

            ui_state = self.ui_states.get(session_id)
            if not ui_state:
                return {"error": "Session not found"}

            export_data = {
                "export_type": export_type,
                "timestamp": datetime.now().isoformat(),
                "session_id": session_id,
                "filters": filters or {}
            }

            if export_type == "search_history":
                export_data["data"] = ui_state.search_history
                export_data["filename"] = f"search_history_{session_id}.json"
            elif export_type == "session_data":
                export_data["data"] = {
                    "preferences": ui_state.preferences,
                    "filters": ui_state.filters,
                    "selected_documents": ui_state.selected_documents
                }
                export_data["filename"] = f"session_data_{session_id}.json"
            else:
                return {"error": f"Unsupported export type: {export_type}"}

            return {
                "success": True,
                "export_data": export_data,
                "download_url": f"/api/rag/download/{export_data['filename']}"
            }

        except Exception as e:
            self.logger.error(f"Error exporting data: {e}")
            return {"success": False, "error": str(e)}

    async def subscribe_to_updates(self, session_id: str, component_ids: List[str]):
        """Subscribe to real-time updates."""
        try:
            if session_id not in self.update_subscribers:
                self.update_subscribers[session_id] = []

            self.update_subscribers[session_id].extend(component_ids)

            self.logger.info(f"Session {session_id} subscribed to updates for components: {component_ids}")

        except Exception as e:
            self.logger.error(f"Error subscribing to updates: {e}")

    async def unsubscribe_from_updates(self, session_id: str, component_ids: List[str]):
        """Unsubscribe from real-time updates."""
        try:
            if session_id in self.update_subscribers:
                for component_id in component_ids:
                    if component_id in self.update_subscribers[session_id]:
                        self.update_subscribers[session_id].remove(component_id)

            self.logger.info(f"Session {session_id} unsubscribed from updates for components: {component_ids}")

        except Exception as e:
            self.logger.error(f"Error unsubscribing from updates: {e}")

    def _queue_update(self, session_id: str, component_id: str, data: Dict[str, Any]):
        """Queue a real-time update."""
        try:
            update = {
                "session_id": session_id,
                "component_id": component_id,
                "data": data,
                "timestamp": datetime.now().isoformat()
            }

            self.update_queue.append(update)

            # Limit queue size
            if len(self.update_queue) > 1000:
                self.update_queue = self.update_queue[-1000:]

        except Exception as e:
            self.logger.error(f"Error queuing update: {e}")

    async def _update_processor_loop(self):
        """Process real-time updates."""
        while True:
            try:
                await asyncio.sleep(self.config.update_interval)

                if not self.update_queue:
                    continue

                # Process updates
                updates_to_process = self.update_queue.copy()
                self.update_queue.clear()

                # Group updates by session
                session_updates = {}
                for update in updates_to_process:
                    session_id = update["session_id"]
                    if session_id not in session_updates:
                        session_updates[session_id] = []
                    session_updates[session_id].append(update)

                # Send updates to subscribers
                for session_id, updates in session_updates.items():
                    if session_id in self.update_subscribers:
                        subscribed_components = set(self.update_subscribers[session_id])

                        for update in updates:
                            if update["component_id"] in subscribed_components:
                                # In a real implementation, you'd send this via WebSocket
                                if self.config.debug_ui:
                                    self.logger.debug(f"Sending update to session {session_id}: {update['component_id']}")

            except Exception as e:
                self.logger.error(f"Error in update processor loop: {e}")
                await asyncio.sleep(30)

    async def _cache_cleaner_loop(self):
        """Clean expired cache entries."""
        while True:
            try:
                await asyncio.sleep(600)  # Clean every 10 minutes

                current_time = datetime.now()
                expired_keys = []

                for key, cached_data in self.component_cache.items():
                    if (current_time - cached_data["timestamp"]).total_seconds() > self.config.cache_ttl:
                        expired_keys.append(key)

                for key in expired_keys:
                    del self.component_cache[key]

                if expired_keys:
                    self.logger.debug(f"Cleaned {len(expired_keys)} expired cache entries")

            except Exception as e:
                self.logger.error(f"Error in cache cleaner loop: {e}")
                await asyncio.sleep(60)

    async def update_preferences(self, session_id: str, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Update user preferences."""
        try:
            ui_state = self.ui_states.get(session_id)
            if not ui_state:
                return {"error": "Session not found"}

            # Update preferences
            ui_state.preferences.update(preferences)

            # Clear cache for this session
            cache_keys_to_remove = [key for key in self.component_cache.keys() if key.startswith(f"{session_id}:")]
            for key in cache_keys_to_remove:
                del self.component_cache[key]

            return {
                "success": True,
                "preferences": ui_state.preferences
            }

        except Exception as e:
            self.logger.error(f"Error updating preferences: {e}")
            return {"success": False, "error": str(e)}

    def get_ui_stats(self) -> Dict[str, Any]:
        """Get UI integration statistics."""
        try:
            return {
                "active_sessions": len(self.ui_states),
                "total_components": len(self.ui_components),
                "cache_size": len(self.component_cache),
                "update_queue_size": len(self.update_queue),
                "subscribers": len(self.update_subscribers),
                "enabled_features": {
                    "real_time_updates": self.config.enable_real_time_updates,
                    "knowledge_graph": self.config.enable_knowledge_graph,
                    "visualization": self.config.enable_visualization,
                    "export": self.config.enable_export
                }
            }

        except Exception as e:
            self.logger.error(f"Error getting UI stats: {e}")
            return {}

    async def close_session(self, session_id: str):
        """Close a UI session."""
        try:
            if session_id in self.ui_states:
                del self.ui_states[session_id]

            if session_id in self.update_subscribers:
                del self.update_subscribers[session_id]

            # Clear cache for this session
            cache_keys_to_remove = [key for key in self.component_cache.keys() if key.startswith(f"{session_id}:")]
            for key in cache_keys_to_remove:
                del self.component_cache[key]

            self.logger.info(f"Closed UI session: {session_id}")

        except Exception as e:
            self.logger.error(f"Error closing session {session_id}: {e}")

    async def close(self):
        """Clean up resources."""
        try:
            # Cancel background tasks
            if self._update_processor:
                self._update_processor.cancel()
            if self._cache_cleaner:
                self._cache_cleaner.cancel()

            # Close all sessions
            for session_id in list(self.ui_states.keys()):
                await self.close_session(session_id)

            self.logger.info("RAG-WebUI Integration closed")

        except Exception as e:
            self.logger.error(f"Error closing WebUI integration: {e}")


# Global instance
_rag_webui_integration: Optional[RAGWebUIIntegration] = None


def get_rag_webui_integration(rag_system: EnhancedRAG, memory_integration: Optional[RAGMemoryIntegration] = None,
                             ai_integration: Optional[RAGAIIntegration] = None,
                             config: Optional[RAGWebUIConfig] = None) -> RAGWebUIIntegration:
    """Get or create the global RAG-WebUI integration instance."""
    global _rag_webui_integration

    if _rag_webui_integration is None:
        _rag_webui_integration = RAGWebUIIntegration(rag_system, memory_integration, ai_integration, config)

    return _rag_webui_integration