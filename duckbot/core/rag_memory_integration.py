#!/usr/bin/env python3
"""
RAG Memory Integration Module for DuckBot
Integrates RAG system with memory and learning systems for enhanced knowledge retention.
"""

import os
import json
import time
import asyncio
import logging
import pickle
from typing import Dict, List, Optional, Any, Tuple, Union, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
from pathlib import Path
import hashlib

# Local imports
from .enhanced_rag import EnhancedRAG, Document, DocumentType, SearchResult
from .logging_setup import get_logger
from .utilities import safe_read_file, ensure_directory

logger = get_logger(__name__)


class MemoryType(Enum):
    """Types of memory storage."""
    EPISODIC = "episodic"      # Personal experiences and events
    SEMANTIC = "semantic"      # General knowledge and facts
    PROCEDURAL = "procedural"  # Skills and procedures
    WORKING = "working"        # Short-term memory
    LONG_TERM = "long_term"    # Persistent memory


class MemoryConsolidation(Enum):
    """Memory consolidation strategies."""
    FREQUENCY_BASED = "frequency_based"      # Consolidate frequently accessed memories
    RELEVANCE_BASED = "relevance_based"      # Consolidate based on relevance
    TEMPORAL_BASED = "temporal_based"        # Consolidate based on recency
    ASSOCIATION_BASED = "association_based"  # Consolidate based on associations
    HYBRID = "hybrid"                        # Combined approach


class MemoryRetrievalStrategy(Enum):
    """Memory retrieval strategies."""
    RECALL = "recall"              # Direct memory recall
    RECOGNITION = "recognition"    # Pattern recognition
    ASSOCIATIVE = "associative"    # Association-based retrieval
    CONTEXTUAL = "contextual"      # Context-aware retrieval
    SPREADING_ACTIVATION = "spreading_activation"  # Neural network-style activation


@dataclass
class Memory:
    """Memory representation."""
    id: str
    content: str
    memory_type: MemoryType
    source: str
    timestamp: datetime
    importance: float = 0.0
    access_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.now)
    associations: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[Any] = None
    consolidated: bool = False


@dataclass
class MemoryCluster:
    """Cluster of related memories."""
    id: str
    centroid_memory_id: str
    memory_ids: Set[str]
    topic: str
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MemoryConfig:
    """Configuration for RAG-memory integration."""
    # Memory settings
    max_working_memory_size: int = 100
    max_long_term_memory_size: int = 10000
    memory_consolidation_interval: int = 3600  # 1 hour
    memory_decay_rate: float = 0.01  # Per hour

    # Retrieval settings
    retrieval_strategy: MemoryRetrievalStrategy = MemoryRetrievalStrategy.CONTEXTUAL
    consolidation_strategy: MemoryConsolidation = MemoryConsolidation.HYBRID
    max_retrieval_results: int = 10
    relevance_threshold: float = 0.3

    # Learning settings
    enable_learning: bool = True
    enable_adaptive_retrieval: bool = True
    enable_memory_clustering: bool = True
    enable_forgetting: bool = True

    # Performance settings
    cache_size: int = 1000
    batch_processing_size: int = 50
    max_consolidation_threads: int = 4

    # Storage settings
    database_path: str = "data/memory.db"
    memory_index_path: str = "data/memory_index.faiss"
    clusters_path: str = "data/memory_clusters.json"

    # Debug settings
    debug_memory: bool = False
    log_memory_operations: bool = True


class RAGMemoryIntegration:
    """
    Integration between RAG system and memory/learning systems.
    """

    def __init__(self, rag_system: EnhancedRAG, config: Optional[MemoryConfig] = None):
        self.rag_system = rag_system
        self.config = config or MemoryConfig()
        self.logger = get_logger(__name__)

        # Initialize storage
        self._initialize_storage()

        # Initialize memory systems
        self.working_memory: Dict[str, Memory] = {}
        self.long_term_memory: Dict[str, Memory] = {}
        self.memory_clusters: Dict[str, MemoryCluster] = {}

        # Performance tracking
        self._stats = {
            "memories_created": 0,
            "memories_retrieved": 0,
            "memories_consolidated": 0,
            "clusters_created": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "avg_retrieval_time": 0.0
        }

        # Background tasks
        self._consolidation_task: Optional[asyncio.Task] = None
        self._clustering_task: Optional[asyncio.Task] = None

        # Start background tasks
        self._start_background_tasks()

        self.logger.info("RAG-Memory Integration initialized")

    def _initialize_storage(self):
        """Initialize database and storage directories."""
        import sqlite3

        # Create directories
        for path in [os.path.dirname(self.config.database_path), os.path.dirname(self.config.memory_index_path)]:
            ensure_directory(path)

        # Initialize database
        conn = sqlite3.connect(self.config.database_path)
        cursor = conn.cursor()

        # Create tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                memory_type TEXT NOT NULL,
                source TEXT NOT NULL,
                timestamp REAL NOT NULL,
                importance REAL NOT NULL,
                access_count INTEGER NOT NULL,
                last_accessed REAL NOT NULL,
                associations TEXT,
                metadata TEXT,
                consolidated INTEGER NOT NULL,
                embedding BLOB
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memory_clusters (
                id TEXT PRIMARY KEY,
                centroid_memory_id TEXT NOT NULL,
                memory_ids TEXT NOT NULL,
                topic TEXT NOT NULL,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL,
                metadata TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memory_access_log (
                memory_id TEXT NOT NULL,
                access_time REAL NOT NULL,
                access_type TEXT NOT NULL,
                context TEXT
            )
        ''')

        conn.commit()
        conn.close()

        self.logger.info(f"Memory storage initialized at {self.config.database_path}")

    def _start_background_tasks(self):
        """Start background memory management tasks."""
        if self.config.enable_learning:
            self._consolidation_task = asyncio.create_task(self._memory_consolidation_loop())
            self.logger.info("Memory consolidation task started")

        if self.config.enable_memory_clustering:
            self._clustering_task = asyncio.create_task(self._memory_clustering_loop())
            self.logger.info("Memory clustering task started")

    async def store_memory(self, content: str, memory_type: MemoryType, source: str,
                          importance: float = 0.5, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Store a memory in the system.

        Args:
            content: Memory content
            memory_type: Type of memory
            source: Source of the memory
            importance: Importance score (0.0 to 1.0)
            metadata: Additional metadata

        Returns:
            Memory ID
        """
        try:
            # Generate memory ID
            memory_id = hashlib.md5(f"{content}:{source}:{time.time()}".encode()).hexdigest()

            # Create memory object
            memory = Memory(
                id=memory_id,
                content=content,
                memory_type=memory_type,
                source=source,
                timestamp=datetime.now(),
                importance=importance,
                metadata=metadata or {}
            )

            # Generate embedding
            memory.embedding = await self.rag_system._generate_embedding(content)

            # Store in appropriate memory system
            if memory_type == MemoryType.WORKING:
                self.working_memory[memory_id] = memory
                # Limit working memory size
                if len(self.working_memory) > self.config.max_working_memory_size:
                    await self._evict_working_memory()
            else:
                self.long_term_memory[memory_id] = memory
                # Limit long-term memory size
                if len(self.long_term_memory) > self.config.max_long_term_memory_size:
                    await self._evict_long_term_memory()

            # Store in database
            await self._store_memory_in_db(memory)

            # Update statistics
            self._stats["memories_created"] += 1

            # Add to RAG system as document
            await self.rag_system.add_text(
                content,
                doc_type=DocumentType.TEXT,
                metadata={
                    "memory_id": memory_id,
                    "memory_type": memory_type.value,
                    "source": source,
                    "importance": importance
                }
            )

            if self.config.debug_memory:
                self.logger.debug(f"Memory stored: {memory_id} ({memory_type.value})")

            return memory_id

        except Exception as e:
            self.logger.error(f"Error storing memory: {e}")
            raise

    async def retrieve_memories(self, query: str, memory_types: Optional[List[MemoryType]] = None,
                              limit: int = 10, context: Optional[Dict[str, Any]] = None) -> List[Memory]:
        """
        Retrieve memories based on query.

        Args:
            query: Search query
            memory_types: Types of memories to search
            limit: Maximum number of results
            context: Additional context for retrieval

        Returns:
            List of retrieved memories
        """
        try:
            start_time = time.time()

            # Search in RAG system
            search_results = await self.rag_system.search(query, top_k=limit)

            # Extract memory IDs from search results
            memory_ids = []
            for result in search_results:
                memory_id = result.chunk.metadata.get("memory_id")
                if memory_id:
                    memory_ids.append(memory_id)

            # Get memories from storage
            memories = []
            for memory_id in memory_ids:
                memory = self._get_memory_by_id(memory_id)
                if memory and (not memory_types or memory.memory_type in memory_types):
                    memories.append(memory)

            # Sort by relevance and importance
            memories.sort(key=lambda m: (m.importance, m.access_count), reverse=True)

            # Apply retrieval strategy
            if self.config.retrieval_strategy == MemoryRetrievalStrategy.CONTEXTUAL:
                memories = await self._contextual_retrieval(memories, context)
            elif self.config.retrieval_strategy == MemoryRetrievalStrategy.ASSOCIATIVE:
                memories = await self._associative_retrieval(memories, query)
            elif self.config.retrieval_strategy == MemoryRetrievalStrategy.SPREADING_ACTIVATION:
                memories = await self._spreading_activation_retrieval(memories, query)

            # Limit results
            memories = memories[:limit]

            # Update access statistics
            for memory in memories:
                memory.access_count += 1
                memory.last_accessed = datetime.now()
                await self._log_memory_access(memory.id, "retrieval", query)

            # Update statistics
            self._stats["memories_retrieved"] += len(memories)
            retrieval_time = time.time() - start_time
            self._stats["avg_retrieval_time"] = (
                (self._stats["avg_retrieval_time"] * (self._stats["memories_retrieved"] - 1) + retrieval_time) /
                self._stats["memories_retrieved"]
            )

            if self.config.debug_memory:
                self.logger.debug(f"Retrieved {len(memories)} memories in {retrieval_time:.3f}s")

            return memories

        except Exception as e:
            self.logger.error(f"Error retrieving memories: {e}")
            return []

    async def create_memory_associations(self, memory_id: str, associated_ids: List[str]):
        """Create associations between memories."""
        try:
            memory = self._get_memory_by_id(memory_id)
            if not memory:
                raise ValueError(f"Memory not found: {memory_id}")

            for associated_id in associated_ids:
                associated_memory = self._get_memory_by_id(associated_id)
                if associated_memory:
                    memory.associations.add(associated_id)
                    associated_memory.associations.add(memory_id)

                    await self._update_memory_in_db(memory)
                    await self._update_memory_in_db(associated_memory)

            if self.config.debug_memory:
                self.logger.debug(f"Created {len(associated_ids)} associations for memory {memory_id}")

        except Exception as e:
            self.logger.error(f"Error creating memory associations: {e}")
            raise

    async def reinforce_memory(self, memory_id: str, reinforcement_factor: float = 0.1):
        """Reinforce a memory by increasing its importance."""
        try:
            memory = self._get_memory_by_id(memory_id)
            if not memory:
                raise ValueError(f"Memory not found: {memory_id}")

            # Increase importance
            memory.importance = min(1.0, memory.importance + reinforcement_factor)

            # Update in database
            await self._update_memory_in_db(memory)

            if self.config.debug_memory:
                self.logger.debug(f"Reinforced memory {memory_id} (importance: {memory.importance:.3f})")

        except Exception as e:
            self.logger.error(f"Error reinforcing memory: {e}")
            raise

    async def decay_memories(self):
        """Apply decay to memories to simulate forgetting."""
        try:
            if not self.config.enable_forgetting:
                return

            current_time = datetime.now()
            decay_factor = self.config.memory_decay_rate

            for memory in list(self.long_term_memory.values()):
                # Calculate time since last access
                time_since_access = (current_time - memory.last_accessed).total_seconds() / 3600  # hours

                # Apply decay
                decay_amount = decay_factor * time_since_access
                memory.importance = max(0.0, memory.importance - decay_amount)

                # Remove if importance is too low
                if memory.importance < 0.1:
                    await self._delete_memory(memory.id)

            if self.config.debug_memory:
                self.logger.debug("Applied memory decay")

        except Exception as e:
            self.logger.error(f"Error decaying memories: {e}")

    async def get_memory_clusters(self, topic: Optional[str] = None) -> List[MemoryCluster]:
        """Get memory clusters, optionally filtered by topic."""
        try:
            if topic:
                return [cluster for cluster in self.memory_clusters.values() if topic.lower() in cluster.topic.lower()]
            else:
                return list(self.memory_clusters.values())

        except Exception as e:
            self.logger.error(f"Error getting memory clusters: {e}")
            return []

    async def _memory_consolidation_loop(self):
        """Background task for memory consolidation."""
        while True:
            try:
                await asyncio.sleep(self.config.memory_consolidation_interval)
                await self._consolidate_memories()

            except Exception as e:
                self.logger.error(f"Error in memory consolidation loop: {e}")
                await asyncio.sleep(60)  # Wait before retrying

    async def _memory_clustering_loop(self):
        """Background task for memory clustering."""
        while True:
            try:
                await asyncio.sleep(self.config.memory_consolidation_interval * 2)  # Less frequent
                await self._cluster_memories()

            except Exception as e:
                self.logger.error(f"Error in memory clustering loop: {e}")
                await asyncio.sleep(120)  # Wait before retrying

    async def _consolidate_memories(self):
        """Consolidate memories based on configured strategy."""
        try:
            if self.config.consolidation_strategy == MemoryConsolidation.FREQUENCY_BASED:
                await self._frequency_based_consolidation()
            elif self.config.consolidation_strategy == MemoryConsolidation.RELEVANCE_BASED:
                await self._relevance_based_consolidation()
            elif self.config.consolidation_strategy == MemoryConsolidation.TEMPORAL_BASED:
                await self._temporal_based_consolidation()
            elif self.config.consolidation_strategy == MemoryConsolidation.ASSOCIATION_BASED:
                await self._association_based_consolidation()
            elif self.config.consolidation_strategy == MemoryConsolidation.HYBRID:
                await self._hybrid_consolidation()

            self._stats["memories_consolidated"] += 1

        except Exception as e:
            self.logger.error(f"Error consolidating memories: {e}")

    async def _frequency_based_consolidation(self):
        """Consolidate frequently accessed memories."""
        try:
            # Get frequently accessed memories
            frequent_memories = [
                memory for memory in self.long_term_memory.values()
                if memory.access_count > 5 and not memory.consolidated
            ]

            # Consolidate top memories
            for memory in sorted(frequent_memories, key=lambda m: m.access_count, reverse=True)[:10]:
                await self._consolidate_memory(memory)

        except Exception as e:
            self.logger.error(f"Error in frequency-based consolidation: {e}")

    async def _relevance_based_consolidation(self):
        """Consolidate high-importance memories."""
        try:
            # Get high-importance memories
            important_memories = [
                memory for memory in self.long_term_memory.values()
                if memory.importance > 0.7 and not memory.consolidated
            ]

            # Consolidate top memories
            for memory in sorted(important_memories, key=lambda m: m.importance, reverse=True)[:10]:
                await self._consolidate_memory(memory)

        except Exception as e:
            self.logger.error(f"Error in relevance-based consolidation: {e}")

    async def _temporal_based_consolidation(self):
        """Consolidate recent memories."""
        try:
            # Get recent memories
            recent_threshold = datetime.now() - timedelta(hours=24)
            recent_memories = [
                memory for memory in self.long_term_memory.values()
                if memory.timestamp > recent_threshold and not memory.consolidated
            ]

            # Consolidate recent memories
            for memory in recent_memories[:20]:
                await self._consolidate_memory(memory)

        except Exception as e:
            self.logger.error(f"Error in temporal-based consolidation: {e}")

    async def _association_based_consolidation(self):
        """Consolidate memories with strong associations."""
        try:
            # Get memories with many associations
            associated_memories = [
                memory for memory in self.long_term_memory.values()
                if len(memory.associations) > 3 and not memory.consolidated
            ]

            # Consolidate highly associated memories
            for memory in sorted(associated_memories, key=lambda m: len(m.associations), reverse=True)[:10]:
                await self._consolidate_memory(memory)

        except Exception as e:
            self.logger.error(f"Error in association-based consolidation: {e}")

    async def _hybrid_consolidation(self):
        """Consolidate memories using hybrid approach."""
        try:
            # Calculate consolidation scores
            memories_to_consolidate = []
            current_time = datetime.now()

            for memory in self.long_term_memory.values():
                if memory.consolidated:
                    continue

                # Calculate score based on multiple factors
                frequency_score = min(memory.access_count / 10, 1.0)
                importance_score = memory.importance
                recency_score = max(0, 1 - (current_time - memory.timestamp).total_seconds() / (24 * 3600))
                association_score = min(len(memory.associations) / 5, 1.0)

                # Weighted combination
                consolidation_score = (
                    frequency_score * 0.3 +
                    importance_score * 0.3 +
                    recency_score * 0.2 +
                    association_score * 0.2
                )

                if consolidation_score > 0.6:
                    memories_to_consolidate.append((memory, consolidation_score))

            # Consolidate top memories
            memories_to_consolidate.sort(key=lambda x: x[1], reverse=True)
            for memory, score in memories_to_consolidate[:15]:
                await self._consolidate_memory(memory)

        except Exception as e:
            self.logger.error(f"Error in hybrid consolidation: {e}")

    async def _consolidate_memory(self, memory: Memory):
        """Consolidate a single memory."""
        try:
            # Increase importance
            memory.importance = min(1.0, memory.importance * 1.1)

            # Mark as consolidated
            memory.consolidated = True

            # Update in database
            await self._update_memory_in_db(memory)

            if self.config.debug_memory:
                self.logger.debug(f"Consolidated memory {memory.id}")

        except Exception as e:
            self.logger.error(f"Error consolidating memory {memory.id}: {e}")

    async def _cluster_memories(self):
        """Cluster related memories together."""
        try:
            # Get unclustered memories
            unclustered_memories = [
                memory for memory in self.long_term_memory.values()
                if not any(memory.id in cluster.memory_ids for cluster in self.memory_clusters.values())
            ]

            if len(unclustered_memories) < 3:
                return

            # Simple clustering based on similarity
            clusters = []
            used_memory_ids = set()

            for i, memory in enumerate(unclustered_memories):
                if memory.id in used_memory_ids:
                    continue

                # Find similar memories
                similar_memories = [memory]
                for other_memory in unclustered_memories[i+1:]:
                    if other_memory.id in used_memory_ids:
                        continue

                    # Calculate similarity
                    similarity = await self._calculate_memory_similarity(memory, other_memory)
                    if similarity > 0.7:
                        similar_memories.append(other_memory)

                # Create cluster if we have enough memories
                if len(similar_memories) >= 3:
                    cluster_id = hashlib.md5(f"cluster_{time.time()}_{i}".encode()).hexdigest()
                    memory_ids = {m.id for m in similar_memories}

                    # Determine topic
                    topic = await self._determine_cluster_topic(similar_memories)

                    cluster = MemoryCluster(
                        id=cluster_id,
                        centroid_memory_id=similar_memories[0].id,
                        memory_ids=memory_ids,
                        topic=topic
                    )

                    clusters.append(cluster)
                    used_memory_ids.update(memory_ids)

            # Store clusters
            for cluster in clusters:
                self.memory_clusters[cluster.id] = cluster
                await self._store_cluster_in_db(cluster)

            self._stats["clusters_created"] += len(clusters)

            if self.config.debug_memory:
                self.logger.debug(f"Created {len(clusters)} memory clusters")

        except Exception as e:
            self.logger.error(f"Error clustering memories: {e}")

    async def _calculate_memory_similarity(self, memory1: Memory, memory2: Memory) -> float:
        """Calculate similarity between two memories."""
        try:
            if memory1.embedding is not None and memory2.embedding is not None:
                return self.rag_system._calculate_similarity(memory1.embedding, memory2.embedding)
            else:
                # Simple text similarity
                return self._calculate_text_similarity(memory1.content, memory2.content)

        except Exception as e:
            self.logger.error(f"Error calculating memory similarity: {e}")
            return 0.0

    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple text similarity."""
        try:
            # Simple word overlap similarity
            words1 = set(text1.lower().split())
            words2 = set(text2.lower().split())

            if not words1 or not words2:
                return 0.0

            intersection = words1.intersection(words2)
            union = words1.union(words2)

            return len(intersection) / len(union)

        except Exception as e:
            self.logger.error(f"Error calculating text similarity: {e}")
            return 0.0

    async def _determine_cluster_topic(self, memories: List[Memory]) -> str:
        """Determine topic for a memory cluster."""
        try:
            # Simple topic extraction - find common words
            all_words = []
            for memory in memories:
                words = memory.content.lower().split()
                all_words.extend(words)

            # Count word frequencies
            word_counts = {}
            for word in all_words:
                if len(word) > 3:  # Ignore short words
                    word_counts[word] = word_counts.get(word, 0) + 1

            # Get most common word
            if word_counts:
                most_common_word = max(word_counts.items(), key=lambda x: x[1])[0]
                return most_common_word
            else:
                return "general"

        except Exception as e:
            self.logger.error(f"Error determining cluster topic: {e}")
            return "unknown"

    async def _contextual_retrieval(self, memories: List[Memory], context: Optional[Dict[str, Any]]) -> List[Memory]:
        """Apply contextual retrieval strategy."""
        try:
            if not context:
                return memories

            # Filter memories based on context
            filtered_memories = []

            for memory in memories:
                relevance_score = await self._calculate_context_relevance(memory, context)
                if relevance_score > self.config.relevance_threshold:
                    memory.metadata["context_relevance"] = relevance_score
                    filtered_memories.append(memory)

            # Sort by context relevance
            filtered_memories.sort(key=lambda m: m.metadata.get("context_relevance", 0.0), reverse=True)

            return filtered_memories

        except Exception as e:
            self.logger.error(f"Error in contextual retrieval: {e}")
            return memories

    async def _associative_retrieval(self, memories: List[Memory], query: str) -> List[Memory]:
        """Apply associative retrieval strategy."""
        try:
            # Start with initial memories
            result_memories = set(memories)

            # Follow associations
            for memory in memories:
                for associated_id in memory.associations:
                    associated_memory = self._get_memory_by_id(associated_id)
                    if associated_memory and associated_memory not in result_memories:
                        result_memories.add(associated_memory)

            return list(result_memories)

        except Exception as e:
            self.logger.error(f"Error in associative retrieval: {e}")
            return memories

    async def _spreading_activation_retrieval(self, memories: List[Memory], query: str) -> List[Memory]:
        """Apply spreading activation retrieval strategy."""
        try:
            # This is a simplified version of spreading activation
            # In a full implementation, you'd have a neural network-like structure

            activated_memories = set(memories)
            activation_levels = {memory.id: 1.0 for memory in memories}

            # Spread activation through associations
            for _ in range(3):  # 3 levels of spreading
                new_activations = {}
                for memory_id, activation in activation_levels.items():
                    if activation > 0.3:  # Threshold for spreading
                        memory = self._get_memory_by_id(memory_id)
                        if memory:
                            for associated_id in memory.associations:
                                if associated_id not in activation_levels:
                                    associated_memory = self._get_memory_by_id(associated_id)
                                    if associated_memory:
                                        new_activations[associated_id] = activation * 0.7
                                        activated_memories.add(associated_memory)

                activation_levels.update(new_activations)

            # Convert back to list and sort by activation
            result_memories = []
            for memory_id in activated_memories:
                memory = self._get_memory_by_id(memory_id)
                if memory:
                    memory.metadata["activation_level"] = activation_levels.get(memory_id, 0.0)
                    result_memories.append(memory)

            result_memories.sort(key=lambda m: m.metadata.get("activation_level", 0.0), reverse=True)

            return result_memories

        except Exception as e:
            self.logger.error(f"Error in spreading activation retrieval: {e}")
            return memories

    async def _calculate_context_relevance(self, memory: Memory, context: Dict[str, Any]) -> float:
        """Calculate relevance of memory to context."""
        try:
            # Simple relevance calculation
            relevance = 0.0

            # Check if memory type matches context
            if "memory_type" in context:
                if memory.memory_type.value == context["memory_type"]:
                    relevance += 0.3

            # Check if source matches context
            if "source" in context:
                if context["source"] in memory.source:
                    relevance += 0.3

            # Check temporal relevance
            if "time_period" in context:
                memory_time = memory.timestamp
                context_time = context["time_period"]
                time_diff = abs((memory_time - context_time).total_seconds())
                if time_diff < 3600:  # Within 1 hour
                    relevance += 0.4

            return min(relevance, 1.0)

        except Exception as e:
            self.logger.error(f"Error calculating context relevance: {e}")
            return 0.0

    def _get_memory_by_id(self, memory_id: str) -> Optional[Memory]:
        """Get memory by ID from storage."""
        # Check working memory first
        if memory_id in self.working_memory:
            return self.working_memory[memory_id]

        # Check long-term memory
        if memory_id in self.long_term_memory:
            return self.long_term_memory[memory_id]

        return None

    async def _evict_working_memory(self):
        """Evict old memories from working memory."""
        try:
            # Sort by last access time
            sorted_memories = sorted(
                self.working_memory.values(),
                key=lambda m: m.last_accessed
            )

            # Remove oldest memories
            memories_to_remove = sorted_memories[:len(self.working_memory) - self.config.max_working_memory_size]

            for memory in memories_to_remove:
                # Move to long-term memory if important enough
                if memory.importance > 0.5:
                    self.long_term_memory[memory.id] = memory
                del self.working_memory[memory.id]

        except Exception as e:
            self.logger.error(f"Error evicting working memory: {e}")

    async def _evict_long_term_memory(self):
        """Evict low-importance memories from long-term memory."""
        try:
            # Sort by importance
            sorted_memories = sorted(
                self.long_term_memory.values(),
                key=lambda m: m.importance
            )

            # Remove least important memories
            memories_to_remove = sorted_memories[:len(self.long_term_memory) - self.config.max_long_term_memory_size]

            for memory in memories_to_remove:
                await self._delete_memory(memory.id)

        except Exception as e:
            self.logger.error(f"Error evicting long-term memory: {e}")

    async def _delete_memory(self, memory_id: str):
        """Delete a memory from the system."""
        try:
            # Remove from memory systems
            if memory_id in self.working_memory:
                del self.working_memory[memory_id]

            if memory_id in self.long_term_memory:
                del self.long_term_memory[memory_id]

            # Remove from clusters
            for cluster in self.memory_clusters.values():
                if memory_id in cluster.memory_ids:
                    cluster.memory_ids.remove(memory_id)
                    if not cluster.memory_ids:
                        del self.memory_clusters[cluster.id]

            # Remove from database
            await self._delete_memory_from_db(memory_id)

        except Exception as e:
            self.logger.error(f"Error deleting memory {memory_id}: {e}")

    async def _store_memory_in_db(self, memory: Memory):
        """Store memory in database."""
        try:
            import sqlite3

            conn = sqlite3.connect(self.config.database_path)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR REPLACE INTO memories
                (id, content, memory_type, source, timestamp, importance, access_count, last_accessed, associations, metadata, consolidated, embedding)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                memory.id,
                memory.content,
                memory.memory_type.value,
                memory.source,
                memory.timestamp.timestamp(),
                memory.importance,
                memory.access_count,
                memory.last_accessed.timestamp(),
                json.dumps(list(memory.associations)),
                json.dumps(memory.metadata),
                int(memory.consolidated),
                pickle.dumps(memory.embedding) if memory.embedding else None
            ))

            conn.commit()
            conn.close()

        except Exception as e:
            self.logger.error(f"Error storing memory in database: {e}")

    async def _update_memory_in_db(self, memory: Memory):
        """Update memory in database."""
        try:
            import sqlite3

            conn = sqlite3.connect(self.config.database_path)
            cursor = conn.cursor()

            cursor.execute('''
                UPDATE memories SET
                content = ?, memory_type = ?, source = ?, timestamp = ?, importance = ?,
                access_count = ?, last_accessed = ?, associations = ?, metadata = ?,
                consolidated = ?, embedding = ?
                WHERE id = ?
            ''', (
                memory.content,
                memory.memory_type.value,
                memory.source,
                memory.timestamp.timestamp(),
                memory.importance,
                memory.access_count,
                memory.last_accessed.timestamp(),
                json.dumps(list(memory.associations)),
                json.dumps(memory.metadata),
                int(memory.consolidated),
                pickle.dumps(memory.embedding) if memory.embedding else None,
                memory.id
            ))

            conn.commit()
            conn.close()

        except Exception as e:
            self.logger.error(f"Error updating memory in database: {e}")

    async def _delete_memory_from_db(self, memory_id: str):
        """Delete memory from database."""
        try:
            import sqlite3

            conn = sqlite3.connect(self.config.database_path)
            cursor = conn.cursor()

            cursor.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
            cursor.execute("DELETE FROM memory_access_log WHERE memory_id = ?", (memory_id,))

            conn.commit()
            conn.close()

        except Exception as e:
            self.logger.error(f"Error deleting memory from database: {e}")

    async def _store_cluster_in_db(self, cluster: MemoryCluster):
        """Store cluster in database."""
        try:
            import sqlite3

            conn = sqlite3.connect(self.config.database_path)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR REPLACE INTO memory_clusters
                (id, centroid_memory_id, memory_ids, topic, created_at, updated_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                cluster.id,
                cluster.centroid_memory_id,
                json.dumps(list(cluster.memory_ids)),
                cluster.topic,
                cluster.created_at.timestamp(),
                cluster.updated_at.timestamp(),
                json.dumps(cluster.metadata)
            ))

            conn.commit()
            conn.close()

        except Exception as e:
            self.logger.error(f"Error storing cluster in database: {e}")

    async def _log_memory_access(self, memory_id: str, access_type: str, context: str):
        """Log memory access for analytics."""
        try:
            import sqlite3

            conn = sqlite3.connect(self.config.database_path)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO memory_access_log (memory_id, access_time, access_type, context)
                VALUES (?, ?, ?, ?)
            ''', (
                memory_id,
                time.time(),
                access_type,
                context
            ))

            conn.commit()
            conn.close()

        except Exception as e:
            self.logger.error(f"Error logging memory access: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get memory system statistics."""
        return {
            **self._stats,
            "working_memory_size": len(self.working_memory),
            "long_term_memory_size": len(self.long_term_memory),
            "cluster_count": len(self.memory_clusters),
            "config": {
                "max_working_memory_size": self.config.max_working_memory_size,
                "max_long_term_memory_size": self.config.max_long_term_memory_size,
                "retrieval_strategy": self.config.retrieval_strategy.value,
                "consolidation_strategy": self.config.consolidation_strategy.value,
                "enable_learning": self.config.enable_learning,
                "enable_memory_clustering": self.config.enable_memory_clustering
            }
        }

    async def export_memories(self, file_path: str, memory_types: Optional[List[MemoryType]] = None):
        """Export memories to file."""
        try:
            memories_to_export = []

            # Collect memories
            if not memory_types or MemoryType.WORKING in memory_types:
                memories_to_export.extend(self.working_memory.values())

            if not memory_types or MemoryType.LONG_TERM in memory_types:
                memories_to_export.extend(self.long_term_memory.values())

            # Convert to serializable format
            export_data = {
                "export_timestamp": datetime.now().isoformat(),
                "memories": [
                    {
                        "id": m.id,
                        "content": m.content,
                        "memory_type": m.memory_type.value,
                        "source": m.source,
                        "timestamp": m.timestamp.isoformat(),
                        "importance": m.importance,
                        "access_count": m.access_count,
                        "last_accessed": m.last_accessed.isoformat(),
                        "associations": list(m.associations),
                        "metadata": m.metadata,
                        "consolidated": m.consolidated
                    }
                    for m in memories_to_export
                ],
                "clusters": [
                    {
                        "id": c.id,
                        "centroid_memory_id": c.centroid_memory_id,
                        "memory_ids": list(c.memory_ids),
                        "topic": c.topic,
                        "created_at": c.created_at.isoformat(),
                        "updated_at": c.updated_at.isoformat(),
                        "metadata": c.metadata
                    }
                    for c in self.memory_clusters.values()
                ]
            }

            # Save to file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Exported {len(memories_to_export)} memories to {file_path}")

        except Exception as e:
            self.logger.error(f"Error exporting memories: {e}")
            raise

    async def import_memories(self, file_path: str):
        """Import memories from file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)

            # Import memories
            imported_count = 0
            for memory_data in import_data.get("memories", []):
                memory = Memory(
                    id=memory_data["id"],
                    content=memory_data["content"],
                    memory_type=MemoryType(memory_data["memory_type"]),
                    source=memory_data["source"],
                    timestamp=datetime.fromisoformat(memory_data["timestamp"]),
                    importance=memory_data["importance"],
                    access_count=memory_data["access_count"],
                    last_accessed=datetime.fromisoformat(memory_data["last_accessed"]),
                    associations=set(memory_data["associations"]),
                    metadata=memory_data["metadata"],
                    consolidated=memory_data["consolidated"]
                )

                # Store memory
                if memory.memory_type == MemoryType.WORKING:
                    self.working_memory[memory.id] = memory
                else:
                    self.long_term_memory[memory.id] = memory

                # Store in database
                await self._store_memory_in_db(memory)

                imported_count += 1

            # Import clusters
            for cluster_data in import_data.get("clusters", []):
                cluster = MemoryCluster(
                    id=cluster_data["id"],
                    centroid_memory_id=cluster_data["centroid_memory_id"],
                    memory_ids=set(cluster_data["memory_ids"]),
                    topic=cluster_data["topic"],
                    created_at=datetime.fromisoformat(cluster_data["created_at"]),
                    updated_at=datetime.fromisoformat(cluster_data["updated_at"]),
                    metadata=cluster_data["metadata"]
                )

                self.memory_clusters[cluster.id] = cluster
                await self._store_cluster_in_db(cluster)

            self.logger.info(f"Imported {imported_count} memories from {file_path}")

        except Exception as e:
            self.logger.error(f"Error importing memories: {e}")
            raise

    async def close(self):
        """Clean up resources."""
        try:
            # Cancel background tasks
            if self._consolidation_task:
                self._consolidation_task.cancel()
            if self._clustering_task:
                self._clustering_task.cancel()

            # Export current state
            await self.export_memories("data/memory_backup.json")

            self.logger.info("RAG-Memory Integration closed")

        except Exception as e:
            self.logger.error(f"Error closing memory integration: {e}")


# Global instance
_rag_memory_integration: Optional[RAGMemoryIntegration] = None


def get_rag_memory_integration(rag_system: EnhancedRAG, config: Optional[MemoryConfig] = None) -> RAGMemoryIntegration:
    """Get or create the global RAG-Memory integration instance."""
    global _rag_memory_integration

    if _rag_memory_integration is None:
        _rag_memory_integration = RAGMemoryIntegration(rag_system, config)

    return _rag_memory_integration