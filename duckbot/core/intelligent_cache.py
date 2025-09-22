#!/usr/bin/env python3
"""
DuckBot Intelligent Caching System
Multi-level caching with AI response similarity matching, cost-aware policies, and performance optimization
"""

import os
import json
import time
import asyncio
import hashlib
import logging
import pickle
import threading
from abc import ABC, abstractmethod
from collections import OrderedDict, defaultdict, deque
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union, Set, Callable
import sqlite3
import numpy as np

# Optional dependencies
try:
    import aiofiles
    AIOFILES_AVAILABLE = True
except ImportError:
    AIOFILES_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

# Local imports
from .logging_setup import get_logger
from .utilities import ensure_directory, safe_write_file, safe_read_file
from .hardware_detector import get_hardware_info

logger = get_logger(__name__)


class CacheLevel(Enum):
    """Cache hierarchy levels"""
    L1_MEMORY = "l1_memory"      # Fastest, smallest, in-memory
    L2_DISK = "l2_disk"          # Medium, disk-based
    L3_DATABASE = "l3_database"  # Largest, persistent
    L4_CLOUD = "l4_cloud"        # Optional, distributed


class CacheEvictionPolicy(Enum):
    """Cache eviction strategies"""
    LRU = "lru"                    # Least Recently Used
    LFU = "lfu"                    # Least Frequently Used
    FIFO = "fifo"                  # First In First Out
    ARC = "arc"                    # Adaptive Replacement Cache
    COST_AWARE = "cost_aware"      # Cost-based eviction
    SIZE_AWARE = "size_aware"      # Size-based eviction


@dataclass
class CacheEntry:
    """Universal cache entry structure"""
    key: str
    value: Any
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    ttl_seconds: Optional[int] = None
    cost_to_generate: float = 0.0
    size_bytes: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[np.ndarray] = None

    def is_expired(self) -> bool:
        """Check if entry has expired"""
        if self.ttl_seconds is None:
            return False
        return (datetime.now() - self.created_at).total_seconds() > self.ttl_seconds

    def update_access(self):
        """Update access information"""
        self.last_accessed = datetime.now()
        self.access_count += 1


@dataclass
class CacheConfig:
    """Cache configuration"""
    # Cache sizes
    l1_memory_size_mb: int = 256
    l2_disk_size_mb: int = 1024
    l3_database_size_mb: int = 5120

    # Eviction policies
    l1_eviction_policy: CacheEvictionPolicy = CacheEvictionPolicy.LRU
    l2_eviction_policy: CacheEvictionPolicy = CacheEvictionPolicy.LFU
    l3_eviction_policy: CacheEvictionPolicy = CacheEvictionPolicy.COST_AWARE

    # Performance settings
    enable_similarity_matching: bool = True
    similarity_threshold: float = 0.85
    max_embedding_cache_size: int = 10000
    compression_enabled: bool = True
    compression_level: int = 6

    # TTL settings
    default_ttl_seconds: int = 3600  # 1 hour
    ai_response_ttl_seconds: int = 86400  # 24 hours
    rag_result_ttl_seconds: int = 7200  # 2 hours
    embedding_ttl_seconds: int = 604800  # 1 week

    # Cost optimization
    enable_cost_aware_eviction: bool = True
    minimum_cost_saving_threshold: float = 0.01  # $0.01
    api_call_deduplication_window_seconds: int = 30

    # Background tasks
    enable_background_cleanup: bool = True
    cleanup_interval_seconds: int = 300  # 5 minutes
    enable_cache_warming: bool = True
    warming_interval_seconds: int = 600  # 10 minutes

    # Storage paths
    cache_dir: str = "data/cache"
    database_path: str = "data/cache/cache.db"

    # Logging and monitoring
    enable_analytics: bool = True
    analytics_interval_seconds: int = 60


class CacheBackend(ABC):
    """Abstract base class for cache backends"""

    def __init__(self, config: CacheConfig):
        self.config = config
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'size_bytes': 0,
            'entry_count': 0
        }

    @abstractmethod
    async def get(self, key: str) -> Optional[CacheEntry]:
        """Get cache entry by key"""
        pass

    @abstractmethod
    async def set(self, key: str, entry: CacheEntry) -> bool:
        """Set cache entry"""
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete cache entry"""
        pass

    @abstractmethod
    async def clear(self) -> bool:
        """Clear all cache entries"""
        pass

    @abstractmethod
    async def cleanup_expired(self) -> int:
        """Remove expired entries, return count removed"""
        pass

    @abstractmethod
    async def get_stats(self) -> Dict[str, Any]:
        """Get backend statistics"""
        pass


class MemoryCacheBackend(CacheBackend):
    """L1 in-memory cache backend"""

    def __init__(self, config: CacheConfig):
        super().__init__(config)
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.max_size_bytes = config.l1_memory_size_mb * 1024 * 1024
        self.lock = threading.RLock()

    async def get(self, key: str) -> Optional[CacheEntry]:
        with self.lock:
            if key in self.cache:
                entry = self.cache[key]
                if entry.is_expired():
                    await self.delete(key)
                    return None

                entry.update_access()
                # Move to end for LRU
                self.cache.move_to_end(key)
                self.stats['hits'] += 1
                return entry

            self.stats['misses'] += 1
            return None

    async def set(self, key: str, entry: CacheEntry) -> bool:
        with self.lock:
            # Check if we need to evict
            while (self.stats['size_bytes'] + entry.size_bytes > self.max_size_bytes and
                   len(self.cache) > 0):
                await self._evict()

            self.cache[key] = entry
            self.stats['size_bytes'] += entry.size_bytes
            self.stats['entry_count'] = len(self.cache)
            return True

    async def delete(self, key: str) -> bool:
        with self.lock:
            if key in self.cache:
                entry = self.cache.pop(key)
                self.stats['size_bytes'] -= entry.size_bytes
                self.stats['entry_count'] = len(self.cache)
                return True
            return False

    async def clear(self) -> bool:
        with self.lock:
            self.cache.clear()
            self.stats['size_bytes'] = 0
            self.stats['entry_count'] = 0
            return True

    async def cleanup_expired(self) -> int:
        with self.lock:
            expired_keys = []
            for key, entry in self.cache.items():
                if entry.is_expired():
                    expired_keys.append(key)

            for key in expired_keys:
                await self.delete(key)

            return len(expired_keys)

    async def _evict(self):
        """Evict entries based on policy"""
        if not self.cache:
            return

        if self.config.l1_eviction_policy == CacheEvictionPolicy.LRU:
            # Remove oldest entry
            key, entry = self.cache.popitem(last=False)
            self.stats['size_bytes'] -= entry.size_bytes
            self.stats['evictions'] += 1

        elif self.config.l1_eviction_policy == CacheEvictionPolicy.LFU:
            # Find least frequently used
            lfu_key = min(self.cache.keys(),
                         key=lambda k: self.cache[k].access_count)
            entry = self.cache.pop(lfu_key)
            self.stats['size_bytes'] -= entry.size_bytes
            self.stats['evictions'] += 1

    async def get_stats(self) -> Dict[str, Any]:
        with self.lock:
            return {
                **self.stats,
                'max_size_bytes': self.max_size_bytes,
                'usage_percent': (self.stats['size_bytes'] / self.max_size_bytes * 100) if self.max_size_bytes > 0 else 0,
                'hit_rate': self.stats['hits'] / (self.stats['hits'] + self.stats['misses']) if (self.stats['hits'] + self.stats['misses']) > 0 else 0
            }


class DiskCacheBackend(CacheBackend):
    """L2 disk-based cache backend"""

    def __init__(self, config: CacheConfig):
        super().__init__(config)
        self.cache_dir = Path(config.cache_dir) / "l2_disk"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_size_bytes = config.l2_disk_size_mb * 1024 * 1020
        self.index_file = self.cache_dir / "index.json"
        self.index: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.RLock()
        self._load_index()

    def _load_index(self):
        """Load cache index from disk"""
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r') as f:
                    self.index = json.load(f)
            except Exception as e:
                logger.error(f"Error loading cache index: {e}")
                self.index = {}

    def _save_index(self):
        """Save cache index to disk"""
        try:
            with open(self.index_file, 'w') as f:
                json.dump(self.index, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving cache index: {e}")

    def _get_entry_path(self, key: str) -> Path:
        """Get file path for cache entry"""
        return self.cache_dir / f"{hashlib.md5(key.encode()).hexdigest()}.cache"

    async def get(self, key: str) -> Optional[CacheEntry]:
        with self.lock:
            if key not in self.index:
                self.stats['misses'] += 1
                return None

            entry_data = self.index[key]
            created_at = datetime.fromisoformat(entry_data['created_at'])

            # Check TTL
            ttl = entry_data.get('ttl_seconds')
            if ttl and (datetime.now() - created_at).total_seconds() > ttl:
                await self.delete(key)
                return None

            # Load from disk
            entry_path = self._get_entry_path(key)
            if not entry_path.exists():
                del self.index[key]
                self._save_index()
                self.stats['misses'] += 1
                return None

            try:
                with open(entry_path, 'rb') as f:
                    data = pickle.load(f)
                    entry = CacheEntry(**data)
                    entry.update_access()
                    self.stats['hits'] += 1
                    return entry
            except Exception as e:
                logger.error(f"Error loading cache entry: {e}")
                await self.delete(key)
                self.stats['misses'] += 1
                return None

    async def set(self, key: str, entry: CacheEntry) -> bool:
        with self.lock:
            entry_path = self._get_entry_path(key)

            try:
                # Save to disk
                with open(entry_path, 'wb') as f:
                    pickle.dump(asdict(entry), f)

                # Update index
                self.index[key] = {
                    'created_at': entry.created_at.isoformat(),
                    'last_accessed': entry.last_accessed.isoformat(),
                    'access_count': entry.access_count,
                    'ttl_seconds': entry.ttl_seconds,
                    'cost_to_generate': entry.cost_to_generate,
                    'size_bytes': entry.size_bytes,
                    'metadata': entry.metadata
                }
                self._save_index()

                self.stats['size_bytes'] += entry.size_bytes
                self.stats['entry_count'] = len(self.index)

                # Check if we need to cleanup
                if self.stats['size_bytes'] > self.max_size_bytes:
                    await self._cleanup_space()

                return True
            except Exception as e:
                logger.error(f"Error saving cache entry: {e}")
                return False

    async def delete(self, key: str) -> bool:
        with self.lock:
            if key not in self.index:
                return False

            entry_path = self._get_entry_path(key)
            if entry_path.exists():
                try:
                    entry_path.unlink()
                except Exception as e:
                    logger.error(f"Error deleting cache file: {e}")

            entry_data = self.index.pop(key)
            self.stats['size_bytes'] -= entry_data.get('size_bytes', 0)
            self.stats['entry_count'] = len(self.index)
            self._save_index()
            return True

    async def clear(self) -> bool:
        with self.lock:
            # Delete all cache files
            for file_path in self.cache_dir.glob("*.cache"):
                try:
                    file_path.unlink()
                except Exception as e:
                    logger.error(f"Error deleting cache file: {e}")

            # Clear index
            self.index.clear()
            self._save_index()
            self.stats['size_bytes'] = 0
            self.stats['entry_count'] = 0
            return True

    async def cleanup_expired(self) -> int:
        with self.lock:
            expired_keys = []
            current_time = datetime.now()

            for key, entry_data in self.index.items():
                created_at = datetime.fromisoformat(entry_data['created_at'])
                ttl = entry_data.get('ttl_seconds')

                if ttl and (current_time - created_at).total_seconds() > ttl:
                    expired_keys.append(key)

            for key in expired_keys:
                await self.delete(key)

            return len(expired_keys)

    async def _cleanup_space(self):
        """Clean up space when exceeding limits"""
        if self.config.l2_eviction_policy == CacheEvictionPolicy.LFU:
            # Sort by access count and remove least accessed
            sorted_keys = sorted(self.index.keys(),
                               key=lambda k: self.index[k].get('access_count', 0))

            while (self.stats['size_bytes'] > self.max_size_bytes and
                   sorted_keys):
                key = sorted_keys.pop(0)
                await self.delete(key)
                self.stats['evictions'] += 1

    async def get_stats(self) -> Dict[str, Any]:
        with self.lock:
            return {
                **self.stats,
                'max_size_bytes': self.max_size_bytes,
                'usage_percent': (self.stats['size_bytes'] / self.max_size_bytes * 100) if self.max_size_bytes > 0 else 0,
                'hit_rate': self.stats['hits'] / (self.stats['hits'] + self.stats['misses']) if (self.stats['hits'] + self.stats['misses']) > 0 else 0
            }


class DatabaseCacheBackend(CacheBackend):
    """L3 SQLite-based cache backend"""

    def __init__(self, config: CacheConfig):
        super().__init__(config)
        self.db_path = Path(config.database_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.max_size_bytes = config.l3_database_size_mb * 1024 * 1024
        self._init_database()
        self.lock = threading.RLock()

    def _init_database(self):
        """Initialize database tables"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS cache_entries (
                    key TEXT PRIMARY KEY,
                    value BLOB,
                    created_at DATETIME NOT NULL,
                    last_accessed DATETIME NOT NULL,
                    access_count INTEGER DEFAULT 0,
                    ttl_seconds INTEGER,
                    cost_to_generate REAL DEFAULT 0.0,
                    size_bytes INTEGER DEFAULT 0,
                    metadata TEXT
                )
            ''')

            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_created_at
                ON cache_entries(created_at)
            ''')

            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_last_accessed
                ON cache_entries(last_accessed)
            ''')

            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_access_count
                ON cache_entries(access_count)
            ''')

    async def get(self, key: str) -> Optional[CacheEntry]:
        with self.lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute('''
                        SELECT value, created_at, last_accessed, access_count,
                               ttl_seconds, cost_to_generate, size_bytes, metadata
                        FROM cache_entries WHERE key = ?
                    ''', (key,))

                    row = cursor.fetchone()
                    if not row:
                        self.stats['misses'] += 1
                        return None

                    # Check TTL
                    if row[4]:  # ttl_seconds
                        created_at = datetime.fromisoformat(row[1])
                        if (datetime.now() - created_at).total_seconds() > row[4]:
                            await self.delete(key)
                            return None

                    # Update access info
                    conn.execute('''
                        UPDATE cache_entries
                        SET last_accessed = ?, access_count = access_count + 1
                        WHERE key = ?
                    ''', (datetime.now().isoformat(), key))

                    # Deserialize entry
                    value_data = pickle.loads(row[0])
                    entry = CacheEntry(
                        key=key,
                        value=value_data['value'],
                        created_at=datetime.fromisoformat(row[1]),
                        last_accessed=datetime.fromisoformat(row[2]),
                        access_count=row[3],
                        ttl_seconds=row[4],
                        cost_to_generate=row[5],
                        size_bytes=row[6],
                        metadata=json.loads(row[7]) if row[7] else {}
                    )

                    self.stats['hits'] += 1
                    return entry

            except Exception as e:
                logger.error(f"Error getting cache entry: {e}")
                self.stats['misses'] += 1
                return None

    async def set(self, key: str, entry: CacheEntry) -> bool:
        with self.lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute('''
                        INSERT OR REPLACE INTO cache_entries
                        (key, value, created_at, last_accessed, access_count,
                         ttl_seconds, cost_to_generate, size_bytes, metadata)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        key,
                        pickle.dumps({'value': entry.value}),
                        entry.created_at.isoformat(),
                        entry.last_accessed.isoformat(),
                        entry.access_count,
                        entry.ttl_seconds,
                        entry.cost_to_generate,
                        entry.size_bytes,
                        json.dumps(entry.metadata)
                    ))

                    self.stats['size_bytes'] += entry.size_bytes
                    self.stats['entry_count'] = len(self.index) if hasattr(self, 'index') else 1

                    # Check if cleanup needed
                    if self.stats['size_bytes'] > self.max_size_bytes:
                        await self._cleanup_space()

                    return True

            except Exception as e:
                logger.error(f"Error setting cache entry: {e}")
                return False

    async def delete(self, key: str) -> bool:
        with self.lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute('''
                        DELETE FROM cache_entries WHERE key = ?
                    ''', (key,))

                    if cursor.rowcount > 0:
                        self.stats['entry_count'] = max(0, self.stats['entry_count'] - 1)
                        return True
                    return False

            except Exception as e:
                logger.error(f"Error deleting cache entry: {e}")
                return False

    async def clear(self) -> bool:
        with self.lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute('DELETE FROM cache_entries')
                    self.stats['size_bytes'] = 0
                    self.stats['entry_count'] = 0
                    return True
            except Exception as e:
                logger.error(f"Error clearing cache: {e}")
                return False

    async def cleanup_expired(self) -> int:
        with self.lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute('''
                        DELETE FROM cache_entries
                        WHERE ttl_seconds IS NOT NULL
                        AND datetime(created_at) < datetime('now', '-' || ttl_seconds || ' seconds')
                    ''')

                    count = cursor.rowcount
                    self.stats['entry_count'] = max(0, self.stats['entry_count'] - count)
                    return count

            except Exception as e:
                logger.error(f"Error cleaning up expired entries: {e}")
                return 0

    async def _cleanup_space(self):
        """Clean up space when exceeding limits"""
        if self.config.l3_eviction_policy == CacheEvictionPolicy.COST_AWARE:
            # Remove least cost-effective entries
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    SELECT key, cost_to_generate, access_count
                    FROM cache_entries
                    ORDER BY (cost_to_generate / (access_count + 1)) ASC
                ''')

                rows = cursor.fetchall()
                current_size = self.stats['size_bytes']

                for row in rows:
                    if current_size <= self.max_size_bytes:
                        break

                    await self.delete(row[0])
                    current_size -= row[1] if row[1] else 0
                    self.stats['evictions'] += 1

    async def get_stats(self) -> Dict[str, Any]:
        with self.lock:
            return {
                **self.stats,
                'max_size_bytes': self.max_size_bytes,
                'usage_percent': (self.stats['size_bytes'] / self.max_size_bytes * 100) if self.max_size_bytes > 0 else 0,
                'hit_rate': self.stats['hits'] / (self.stats['hits'] + self.stats['misses']) if (self.stats['hits'] + self.stats['misses']) > 0 else 0
            }


class IntelligentCache:
    """Main intelligent caching system"""

    def __init__(self, config: CacheConfig = None):
        self.config = config or CacheConfig()

        # Initialize cache backends
        self.backends = {
            CacheLevel.L1_MEMORY: MemoryCacheBackend(self.config),
            CacheLevel.L2_DISK: DiskCacheBackend(self.config),
            CacheLevel.L3_DATABASE: DatabaseCacheBackend(self.config)
        }

        # Similarity matching
        self.embedding_model = None
        if self.config.enable_similarity_matching and SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            except Exception as e:
                logger.warning(f"Failed to load embedding model: {e}")

        # API call deduplication
        self.pending_calls: Dict[str, asyncio.Future] = {}
        self.call_locks: Dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)

        # Background tasks
        self._running = True
        self._cleanup_task = None
        self._warming_task = None
        self._analytics_task = None

        # Cache analytics
        self.analytics_data = {
            'total_hits': 0,
            'total_misses': 0,
            'total_cost_saved': 0.0,
            'average_response_time_saved': 0.0,
            'cache_effectiveness': {}
        }

        # Start background tasks
        if self.config.enable_background_cleanup:
            self._start_background_tasks()

        logger.info("Intelligent caching system initialized")

    def _start_background_tasks(self):
        """Start background maintenance tasks"""
        async def cleanup_task():
            while self._running:
                try:
                    total_removed = 0
                    for backend in self.backends.values():
                        removed = await backend.cleanup_expired()
                        total_removed += removed

                    if total_removed > 0:
                        logger.info(f"Cache cleanup: removed {total_removed} expired entries")

                    await asyncio.sleep(self.config.cleanup_interval_seconds)
                except Exception as e:
                    logger.error(f"Error in cache cleanup: {e}")
                    await asyncio.sleep(60)

        async def warming_task():
            while self._running:
                try:
                    await self._warm_cache()
                    await asyncio.sleep(self.config.warming_interval_seconds)
                except Exception as e:
                    logger.error(f"Error in cache warming: {e}")
                    await asyncio.sleep(60)

        async def analytics_task():
            while self._running:
                try:
                    await self._update_analytics()
                    await asyncio.sleep(self.config.analytics_interval_seconds)
                except Exception as e:
                    logger.error(f"Error in cache analytics: {e}")
                    await asyncio.sleep(60)

        # Create tasks
        loop = asyncio.get_event_loop()
        self._cleanup_task = loop.create_task(cleanup_task())
        self._warming_task = loop.create_task(warming_task())
        self._analytics_task = loop.create_task(analytics_task())

    async def get(self, key: str, similarity_threshold: float = None) -> Optional[CacheEntry]:
        """Get cached value with similarity matching"""
        # Try L1 cache first
        for level in [CacheLevel.L1_MEMORY, CacheLevel.L2_DISK, CacheLevel.L3_DATABASE]:
            entry = await self.backends[level].get(key)
            if entry:
                # Propagate to higher levels if needed
                if level != CacheLevel.L1_MEMORY:
                    await self.backends[CacheLevel.L1_MEMORY].set(key, entry)

                self.analytics_data['total_hits'] += 1
                return entry

        # Similarity matching for AI responses
        if (self.config.enable_similarity_matching and
            self.embedding_model and
            similarity_threshold is not None):

            similar_entry = await self._find_similar_entry(key, similarity_threshold)
            if similar_entry:
                self.analytics_data['total_hits'] += 1
                return similar_entry

        self.analytics_data['total_misses'] += 1
        return None

    async def set(self, key: str, value: Any, ttl_seconds: int = None,
                 cost_to_generate: float = 0.0, category: str = "general",
                 metadata: Dict[str, Any] = None) -> bool:
        """Set cached value"""
        try:
            # Calculate size
            size_bytes = len(pickle.dumps(value))

            # Generate embedding if similarity matching is enabled
            embedding = None
            if (self.config.enable_similarity_matching and
                self.embedding_model and
                isinstance(value, str)):
                try:
                    embedding = self.embedding_model.encode([key])[0]
                except Exception as e:
                    logger.warning(f"Failed to generate embedding: {e}")

            # Create cache entry
            entry = CacheEntry(
                key=key,
                value=value,
                ttl_seconds=ttl_seconds or self.config.default_ttl_seconds,
                cost_to_generate=cost_to_generate,
                size_bytes=size_bytes,
                metadata=metadata or {},
                embedding=embedding
            )

            # Set in all backends
            success = True
            for backend in self.backends.values():
                if not await backend.set(key, entry):
                    success = False

            if success:
                # Update analytics
                self.analytics_data['total_cost_saved'] += cost_to_generate
                if category not in self.analytics_data['cache_effectiveness']:
                    self.analytics_data['cache_effectiveness'][category] = {
                        'hits': 0, 'misses': 0, 'cost_saved': 0.0
                    }
                self.analytics_data['cache_effectiveness'][category]['cost_saved'] += cost_to_generate

            return success

        except Exception as e:
            logger.error(f"Error setting cache entry: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete cached value"""
        success = True
        for backend in self.backends.values():
            if not await backend.delete(key):
                success = False
        return success

    async def clear(self) -> bool:
        """Clear all cache"""
        success = True
        for backend in self.backends.values():
            if not await backend.clear():
                success = False
        return success

    async def cached_call(self, cache_key: str, func: Callable, *args, **kwargs) -> Any:
        """Execute function with caching and deduplication"""
        # Check cache first
        cached_result = await self.get(cache_key)
        if cached_result:
            return cached_result.value

        # Check for duplicate in-flight calls
        async with self.call_locks[cache_key]:
            if cache_key in self.pending_calls:
                return await self.pending_calls[cache_key]

            # Create future for this call
            future = asyncio.get_event_loop().create_future()
            self.pending_calls[cache_key] = future

            try:
                # Execute the function
                result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)

                # Cache the result
                await self.set(cache_key, result,
                             ttl_seconds=self.config.api_call_deduplication_window_seconds)

                # Set future result
                future.set_result(result)
                return result

            except Exception as e:
                future.set_exception(e)
                raise

            finally:
                # Clean up
                self.pending_calls.pop(cache_key, None)

    async def _find_similar_entry(self, query: str, threshold: float) -> Optional[CacheEntry]:
        """Find similar cached entry using embeddings"""
        if not self.embedding_model:
            return None

        try:
            query_embedding = self.embedding_model.encode([query])[0]

            # Search through all backends for entries with embeddings
            for level in [CacheLevel.L1_MEMORY, CacheLevel.L2_DISK, CacheLevel.L3_DATABASE]:
                # This is a simplified search - in practice, you'd want a more efficient approach
                # For now, we'll just check the L1 cache
                if level == CacheLevel.L1_MEMORY:
                    backend = self.backends[level]
                    if hasattr(backend, 'cache'):
                        for entry in backend.cache.values():
                            if entry.embedding is not None:
                                similarity = self._calculate_similarity(query_embedding, entry.embedding)
                                if similarity >= threshold:
                                    return entry

            return None

        except Exception as e:
            logger.error(f"Error finding similar entry: {e}")
            return None

    def _calculate_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """Calculate cosine similarity between embeddings"""
        try:
            return float(np.dot(embedding1, embedding2) /
                        (np.linalg.norm(embedding1) * np.linalg.norm(embedding2)))
        except Exception:
            return 0.0

    async def _warm_cache(self):
        """Warm up cache with frequently accessed data"""
        # This would typically load frequently used patterns or pre-compute common queries
        pass

    async def _update_analytics(self):
        """Update cache analytics"""
        try:
            total_requests = self.analytics_data['total_hits'] + self.analytics_data['total_misses']
            if total_requests > 0:
                hit_rate = self.analytics_data['total_hits'] / total_requests
                logger.info(f"Cache performance: {hit_rate:.2%} hit rate, "
                           f"${self.analytics_data['total_cost_saved']:.4f} saved")
        except Exception as e:
            logger.error(f"Error updating analytics: {e}")

    async def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        stats = {
            'config': asdict(self.config),
            'analytics': self.analytics_data,
            'backends': {}
        }

        for level, backend in self.backends.items():
            stats['backends'][level.value] = await backend.get_stats()

        return stats

    async def stop(self):
        """Stop the caching system"""
        self._running = False

        # Cancel background tasks
        if self._cleanup_task:
            self._cleanup_task.cancel()
        if self._warming_task:
            self._warming_task.cancel()
        if self._analytics_task:
            self._analytics_task.cancel()

        logger.info("Intelligent caching system stopped")


# Global instance
_intelligent_cache: Optional[IntelligentCache] = None

def get_intelligent_cache(config: CacheConfig = None) -> IntelligentCache:
    """Get or create the global intelligent cache instance"""
    global _intelligent_cache
    if _intelligent_cache is None:
        _intelligent_cache = IntelligentCache(config)
    return _intelligent_cache

async def stop_intelligent_cache():
    """Stop the global intelligent cache"""
    global _intelligent_cache
    if _intelligent_cache is not None:
        await _intelligent_cache.stop()
        _intelligent_cache = None