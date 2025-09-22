#!/usr/bin/env python3
"""
RAG Service Integration Module for DuckBot
Integrates RAG system with service management for enhanced service coordination.
"""

import os
import json
import time
import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple, Union, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
from pathlib import Path
import hashlib

# Local imports
from .enhanced_rag import EnhancedRAG, Document, DocumentType, SearchResult
from .service_manager import ServiceManager
from .logging_setup import get_logger
from .utilities import safe_read_file

logger = get_logger(__name__)


class ServiceRAGRole(Enum):
    """RAG roles for services."""
    KNOWLEDGE_PROVIDER = "knowledge_provider"    # Provides knowledge to services
    CONTEXT_BUILDER = "context_builder"          # Builds context for services
    SERVICE_ORCHESTRATOR = "service_orchestrator"  # Orchestrates service coordination
    QUALITY_ASSUROR = "quality_assuror"        # Assures service quality
    PERFORMANCE_OPTIMIZER = "performance_optimizer"  # Optimizes service performance


class ServiceRAGMode(Enum):
    """RAG modes for services."""
    ACTIVE = "active"              # RAG actively involved in service operations
    PASSIVE = "passive"            # RAG provides background knowledge
    ON_DEMAND = "on_demand"        # RAG activated when requested
    BATCH = "batch"               # RAG processes in batch mode


@dataclass
class ServiceRAGConfig:
    """Configuration for RAG-service integration."""
    # General settings
    enabled: bool = True
    default_mode: ServiceRAGMode = ServiceRAGMode.ACTIVE

    # Service-specific settings
    service_roles: Dict[str, ServiceRAGRole] = field(default_factory=dict)
    service_modes: Dict[str, ServiceRAGMode] = field(default_factory=dict)

    # Performance settings
    max_concurrent_services: int = 10
    service_timeout: int = 300  # 5 minutes
    enable_service_caching: bool = True
    cache_ttl: int = 600  # 10 minutes

    # Knowledge management
    enable_knowledge_sharing: bool = True
    knowledge_sync_interval: int = 60  # 1 minute
    max_knowledge_entries_per_service: int = 1000

    # Monitoring settings
    enable_service_monitoring: bool = True
    monitoring_interval: int = 30  # 30 seconds
    performance_thresholds: Dict[str, float] = field(default_factory=lambda: {
        "response_time": 5.0,
        "success_rate": 0.9,
        "knowledge_relevance": 0.7
    })

    # Debug settings
    debug_services: bool = False
    log_service_activities: bool = True


@dataclass
class ServiceKnowledge:
    """Knowledge specific to a service."""
    id: str
    service_id: str
    content: str
    knowledge_type: str
    confidence: float
    source: str
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)
    usage_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


class RAGServiceIntegration:
    """
    Integration between RAG system and service management.
    """

    def __init__(self, rag_system: EnhancedRAG, service_manager: ServiceManager,
                 config: Optional[ServiceRAGConfig] = None):
        self.rag_system = rag_system
        self.service_manager = service_manager
        self.config = config or ServiceRAGConfig()
        self.logger = get_logger(__name__)

        # Initialize service systems
        self.service_knowledge: Dict[str, Dict[str, ServiceKnowledge]] = {}
        self.service_contexts: Dict[str, Dict[str, Any]] = {}
        self.service_performance: Dict[str, Dict[str, float]] = {}

        # Caching systems
        self.service_cache: Dict[str, Dict[str, Any]] = {}
        self.knowledge_cache: Dict[str, ServiceKnowledge] = {}

        # Background tasks
        self._knowledge_sync_task: Optional[asyncio.Task] = None
        self._monitoring_task: Optional[asyncio.Task] = None

        # Start background tasks
        self._start_background_tasks()

        self.logger.info("RAG-Service Integration initialized")

    def _start_background_tasks(self):
        """Start background service management tasks."""
        if self.config.enable_knowledge_sharing:
            self._knowledge_sync_task = asyncio.create_task(self._knowledge_sync_loop())

        if self.config.enable_service_monitoring:
            self._monitoring_task = asyncio.create_task(self._service_monitoring_loop())

        self.logger.info("Background service tasks started")

    async def register_service(self, service_id: str, role: ServiceRAGRole,
                             mode: ServiceRAGMode = None, initial_knowledge: List[str] = None):
        """Register a service with the RAG system."""
        try:
            if mode is None:
                mode = self.config.default_mode

            # Set service role and mode
            self.config.service_roles[service_id] = role
            self.config.service_modes[service_id] = mode

            # Initialize service knowledge base
            self.service_knowledge[service_id] = {}

            # Initialize service context
            self.service_contexts[service_id] = {
                "role": role.value,
                "mode": mode.value,
                "knowledge_count": 0,
                "last_sync": datetime.now(),
                "performance_metrics": {}
            }

            # Add initial knowledge
            if initial_knowledge:
                for knowledge_content in initial_knowledge:
                    await self._add_service_knowledge(service_id, knowledge_content, "initial")

            self.logger.info(f"Service {service_id} registered with RAG system (role: {role.value})")

        except Exception as e:
            self.logger.error(f"Error registering service {service_id}: {e}")
            raise

    async def get_service_knowledge(self, service_id: str, query: str,
                                  limit: int = 5) -> List[ServiceKnowledge]:
        """Get knowledge for a specific service."""
        try:
            # Check cache first
            cache_key = f"{service_id}:{query}:{limit}"
            if self.config.enable_service_caching and cache_key in self.knowledge_cache:
                cached_result = self.knowledge_cache[cache_key]
                if (datetime.now() - cached_result.last_accessed).total_seconds() < self.config.cache_ttl:
                    return [cached_result]

            # Get service-specific knowledge
            service_knowledge = self.service_knowledge.get(service_id, {})
            relevant_knowledge = []

            for knowledge_id, knowledge in service_knowledge.items():
                # Simple relevance check
                if query.lower() in knowledge.content.lower():
                    relevant_knowledge.append(knowledge)

            # Sort by confidence and usage
            relevant_knowledge.sort(key=lambda k: (k.confidence, k.usage_count), reverse=True)
            relevant_knowledge = relevant_knowledge[:limit]

            # Cache result
            if relevant_knowledge and self.config.enable_service_caching:
                self.knowledge_cache[cache_key] = relevant_knowledge[0]

            return relevant_knowledge

        except Exception as e:
            self.logger.error(f"Error getting service knowledge for {service_id}: {e}")
            return []

    async def add_service_knowledge(self, service_id: str, content: str,
                                 knowledge_type: str = "manual", confidence: float = 0.8) -> str:
        """Add knowledge to a service."""
        try:
            return await self._add_service_knowledge(service_id, content, knowledge_type, confidence)

        except Exception as e:
            self.logger.error(f"Error adding service knowledge for {service_id}: {e}")
            raise

    async def _add_service_knowledge(self, service_id: str, content: str,
                                  knowledge_type: str, confidence: float = 0.8) -> str:
        """Internal method to add service knowledge."""
        try:
            knowledge_id = hashlib.md5(f"{service_id}:{content}:{time.time()}".encode()).hexdigest()

            knowledge = ServiceKnowledge(
                id=knowledge_id,
                service_id=service_id,
                content=content,
                knowledge_type=knowledge_type,
                confidence=confidence,
                source=f"service_{service_id}"
            )

            # Add to service knowledge base
            if service_id not in self.service_knowledge:
                self.service_knowledge[service_id] = {}

            self.service_knowledge[service_id][knowledge_id] = knowledge

            # Update service context
            if service_id in self.service_contexts:
                self.service_contexts[service_id]["knowledge_count"] += 1
                self.service_contexts[service_id]["last_sync"] = datetime.now()

            # Add to RAG system
            await self.rag_system.add_text(
                content,
                doc_type=DocumentType.TEXT,
                metadata={
                    "service_id": service_id,
                    "knowledge_id": knowledge_id,
                    "knowledge_type": knowledge_type,
                    "confidence": confidence
                }
            )

            return knowledge_id

        except Exception as e:
            self.logger.error(f"Error adding service knowledge: {e}")
            raise

    async def build_service_context(self, service_id: str, request_data: Dict[str, Any],
                                 max_length: int = 2000) -> str:
        """Build context for a service request."""
        try:
            # Get service-specific knowledge
            query = request_data.get("query", "")
            service_knowledge = await self.get_service_knowledge(service_id, query, limit=3)

            # Build context
            context_parts = []
            total_length = 0

            # Add service role information
            role = self.config.service_roles.get(service_id, ServiceRAGRole.KNOWLEDGE_PROVIDER)
            context_parts.append(f"Service Role: {role.value}")

            # Add service knowledge
            for knowledge in service_knowledge:
                knowledge_text = f"Service Knowledge: {knowledge.content}"
                if total_length + len(knowledge_text) <= max_length:
                    context_parts.append(knowledge_text)
                    total_length += len(knowledge_text)

            # Add RAG search results if applicable
            if query and self.config.service_modes.get(service_id) != ServiceRAGMode.PASSIVE:
                search_results = await self.rag_system.search(query, top_k=2)
                for result in search_results:
                    result_text = f"Additional Context: {result.chunk.content}"
                    if total_length + len(result_text) <= max_length:
                        context_parts.append(result_text)
                        total_length += len(result_text)

            return "\n\n".join(context_parts)

        except Exception as e:
            self.logger.error(f"Error building service context for {service_id}: {e}")
            return ""

    async def monitor_service_performance(self, service_id: str, metrics: Dict[str, float]):
        """Monitor service performance and provide recommendations."""
        try:
            if service_id not in self.service_performance:
                self.service_performance[service_id] = {}

            # Update performance metrics
            for metric, value in metrics.items():
                if metric not in self.service_performance[service_id]:
                    self.service_performance[service_id][metric] = []

                self.service_performance[service_id][metric].append({
                    "value": value,
                    "timestamp": datetime.now()
                })

                # Keep only recent metrics (last 100)
                if len(self.service_performance[service_id][metric]) > 100:
                    self.service_performance[service_id][metric] = self.service_performance[service_id][metric][-100:]

            # Check thresholds and provide recommendations
            recommendations = []
            for metric, threshold in self.config.performance_thresholds.items():
                if metric in metrics and metrics[metric] < threshold:
                    recommendations.append(f"{metric} is below threshold ({metrics[metric]:.2f} < {threshold:.2f})")

            if recommendations:
                self.logger.warning(f"Service {service_id} performance issues: {', '.join(recommendations)}")

                # Add recommendations to service knowledge
                await self._add_service_knowledge(
                    service_id,
                    f"Performance Recommendations: {'; '.join(recommendations)}",
                    "performance_recommendation",
                    0.9
                )

        except Exception as e:
            self.logger.error(f"Error monitoring service performance for {service_id}: {e}")

    async def _knowledge_sync_loop(self):
        """Background task for knowledge synchronization."""
        while True:
            try:
                await asyncio.sleep(self.config.knowledge_sync_interval)
                await self._sync_service_knowledge()

            except Exception as e:
                self.logger.error(f"Error in knowledge sync loop: {e}")
                await asyncio.sleep(30)  # Wait before retrying

    async def _service_monitoring_loop(self):
        """Background task for service monitoring."""
        while True:
            try:
                await asyncio.sleep(self.config.monitoring_interval)
                await self._monitor_services()

            except Exception as e:
                self.logger.error(f"Error in service monitoring loop: {e}")
                await asyncio.sleep(30)  # Wait before retrying

    async def _sync_service_knowledge(self):
        """Synchronize knowledge between services."""
        try:
            # Share high-confidence knowledge between services
            for service_id, knowledge_base in self.service_knowledge.items():
                for knowledge_id, knowledge in knowledge_base.items():
                    if knowledge.confidence >= 0.8:  # High confidence threshold
                        # Share with other services
                        for other_service_id in self.service_knowledge.keys():
                            if other_service_id != service_id:
                                # Check if knowledge already exists
                                exists = any(
                                    k.content == knowledge.content
                                    for k in self.service_knowledge[other_service_id].values()
                                )

                                if not exists:
                                    # Create shared knowledge
                                    shared_knowledge = ServiceKnowledge(
                                        id=f"{knowledge_id}_shared_{other_service_id}",
                                        service_id=other_service_id,
                                        content=knowledge.content,
                                        knowledge_type="shared",
                                        confidence=knowledge.confidence * 0.9,  # Slightly reduced
                                        source=f"shared_from_{service_id}"
                                    )

                                    self.service_knowledge[other_service_id][shared_knowledge.id] = shared_knowledge

        except Exception as e:
            self.logger.error(f"Error syncing service knowledge: {e}")

    async def _monitor_services(self):
        """Monitor service health and performance."""
        try:
            # Monitor each service
            for service_id, context in self.service_contexts.items():
                # Get service status from service manager
                service_status = self.service_manager.get_service_status(service_id)

                if service_status:
                    # Update service context with current status
                    context["status"] = service_status.get("status", "unknown")
                    context["last_check"] = datetime.now()

                    # Check for issues
                    if service_status.get("status") == "error":
                        error_msg = service_status.get("error", "Unknown error")
                        self.logger.warning(f"Service {service_id} error: {error_msg}")

                        # Add error information to service knowledge
                        await self._add_service_knowledge(
                            service_id,
                            f"Service Error: {error_msg}",
                            "error_log",
                            0.7
                        )

        except Exception as e:
            self.logger.error(f"Error monitoring services: {e}")

    def get_service_stats(self) -> Dict[str, Any]:
        """Get service integration statistics."""
        try:
            return {
                "registered_services": len(self.service_knowledge),
                "total_knowledge_entries": sum(len(kb) for kb in self.service_knowledge.values()),
                "service_performance": self.service_performance,
                "cache_size": len(self.knowledge_cache),
                "config": {
                    "enabled": self.config.enabled,
                    "default_mode": self.config.default_mode.value,
                    "enable_knowledge_sharing": self.config.enable_knowledge_sharing,
                    "enable_service_monitoring": self.config.enable_service_monitoring
                }
            }

        except Exception as e:
            self.logger.error(f"Error getting service stats: {e}")
            return {}

    async def close(self):
        """Clean up resources."""
        try:
            # Cancel background tasks
            if self._knowledge_sync_task:
                self._knowledge_sync_task.cancel()
            if self._monitoring_task:
                self._monitoring_task.cancel()

            self.logger.info("RAG-Service Integration closed")

        except Exception as e:
            self.logger.error(f"Error closing service integration: {e}")


# Global instance
_rag_service_integration: Optional[RAGServiceIntegration] = None


def get_rag_service_integration(rag_system: EnhancedRAG, service_manager: ServiceManager,
                             config: Optional[ServiceRAGConfig] = None) -> RAGServiceIntegration:
    """Get or create the global RAG-Service integration instance."""
    global _rag_service_integration

    if _rag_service_integration is None:
        _rag_service_integration = RAGServiceIntegration(rag_system, service_manager, config)

    return _rag_service_integration