#!/usr/bin/env python3
"""
AI Cache and Rate Limiting Manager
Prevents API overwhelming with intelligent caching and throttling
"""

import os
import json
import time
import hashlib
import sqlite3
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from pathlib import Path
import logging
import threading
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class ConnectionPool:
    """Thread-safe SQLite connection pool to prevent connection leaks"""
    def __init__(self, db_path: Path, max_connections: int = 10):
        self.db_path = db_path
        self.max_connections = max_connections
        self.pool = []
        self.lock = threading.Lock()
        self.active_connections = 0
    
    @contextmanager
    def get_connection(self):
        """Get a database connection from pool or create new one"""
        conn = None
        try:
            with self.lock:
                if self.pool:
                    conn = self.pool.pop()
                else:
                    conn = sqlite3.connect(str(self.db_path))
                    conn.execute('PRAGMA journal_mode=WAL')  # Better concurrency
                    conn.execute('PRAGMA synchronous=NORMAL')  # Performance
                    conn.execute('PRAGMA cache_size=10000')  # Memory cache
                self.active_connections += 1
            
            yield conn
            
        finally:
            if conn:
                with self.lock:
                    self.active_connections -= 1
                    if len(self.pool) < self.max_connections:
                        self.pool.append(conn)
                    else:
                        conn.close()
    
    def close_all(self):
        """Close all connections in pool"""
        with self.lock:
            while self.pool:
                conn = self.pool.pop()
                conn.close()

@dataclass
class CacheEntry:
    key: str
    content: str
    timestamp: datetime
    ttl_seconds: int
    hit_count: int = 0
    token_usage: int = 0

@dataclass
class RateLimitConfig:
    requests_per_minute: int = 20
    requests_per_hour: int = 500
    requests_per_day: int = 2000
    tokens_per_minute: int = 50000
    tokens_per_hour: int = 1000000
    cooldown_on_limit: int = 300  # 5 minutes

class AICacheManager:
    """Intelligent caching and rate limiting for AI API calls"""
    
    def __init__(self, cache_dir: Path = None):
        self.cache_dir = cache_dir or Path(__file__).parent / "ai_cache"
        self.cache_dir.mkdir(exist_ok=True)
        
        self.cache_db = self.cache_dir / "ai_cache.db"
        self.rate_limit_db = self.cache_dir / "rate_limits.db"
        
        # FIXED: Initialize connection pools to prevent connection leaks
        self.cache_pool = ConnectionPool(self.cache_db)
        self.rate_limit_pool = ConnectionPool(self.rate_limit_db)
        
        # Rate limiting configuration
        self.rate_limits = RateLimitConfig()
        
        # In-memory cache for frequently accessed items
        self.memory_cache: Dict[str, CacheEntry] = {}
        self.max_memory_cache = 100
        
        # Initialize databases
        self.init_cache_db()
        self.init_rate_limit_db()
        
        logger.info("[DB] AI Cache Manager initialized with connection pooling")

    def init_cache_db(self):
        """Initialize cache database"""
        with self.cache_pool.get_connection() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS cache_entries (
                    key TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    ttl_seconds INTEGER NOT NULL,
                    hit_count INTEGER DEFAULT 0,
                    token_usage INTEGER DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_timestamp ON cache_entries(timestamp)
            ''')
            
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_ttl ON cache_entries(timestamp, ttl_seconds)
            ''')
            
            conn.commit()

    def init_rate_limit_db(self):
        """Initialize rate limiting database"""
        with self.rate_limit_pool.get_connection() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS api_calls (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    provider TEXT NOT NULL,
                    model TEXT NOT NULL,
                    tokens_used INTEGER DEFAULT 0,
                    response_time_ms INTEGER DEFAULT 0,
                    success BOOLEAN DEFAULT TRUE
                )
            ''')
            
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_timestamp_provider ON api_calls(timestamp, provider)
            ''')
            
            conn.commit()

    def generate_cache_key(self, messages: List[Dict], config: Dict) -> str:
        """Generate consistent cache key for API requests"""
        # Create a stable representation
        cache_data = {
            'messages': messages,
            'model': config.get('model', ''),
            'temperature': config.get('temperature', 0.7),
            'max_tokens': config.get('max_tokens', 2000)
        }
        
        # Generate hash
        cache_string = json.dumps(cache_data, sort_keys=True)
        return hashlib.sha256(cache_string.encode()).hexdigest()

    def get_from_cache(self, cache_key: str) -> Optional[str]:
        """Get cached response if valid"""
        
        # Check memory cache first
        if cache_key in self.memory_cache:
            entry = self.memory_cache[cache_key]
            if self.is_cache_valid(entry):
                entry.hit_count += 1
                logger.debug(f"[TARGET] Memory cache hit: {cache_key[:12]}...")
                return entry.content
            else:
                # Remove expired entry
                del self.memory_cache[cache_key]
        
        # Check database cache
        try:
            with self.cache_pool.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT content, timestamp, ttl_seconds, hit_count, token_usage FROM cache_entries WHERE key = ?",
                    (cache_key,)
                )
                row = cursor.fetchone()
                
                if row:
                    content, timestamp_str, ttl_seconds, hit_count, token_usage = row
                    timestamp = datetime.fromisoformat(timestamp_str)
                    
                    entry = CacheEntry(
                        key=cache_key,
                        content=content,
                        timestamp=timestamp,
                        ttl_seconds=ttl_seconds,
                        hit_count=hit_count,
                        token_usage=token_usage
                    )
                    
                    if self.is_cache_valid(entry):
                        # Update hit count
                        entry.hit_count += 1
                        conn.execute(
                            "UPDATE cache_entries SET hit_count = ? WHERE key = ?",
                            (entry.hit_count, cache_key)
                        )
                        conn.commit()
                        
                        # Add to memory cache
                        self.add_to_memory_cache(entry)
                        
                        logger.debug(f"[SAVE] Database cache hit: {cache_key[:12]}...")
                        return content
                    else:
                        # Remove expired entry
                        conn.execute("DELETE FROM cache_entries WHERE key = ?", (cache_key,))
                        conn.commit()
                        logger.debug(f"[DELETE] Removed expired cache entry: {cache_key[:12]}...")
        
        except Exception as e:
            logger.error(f"Error reading from cache: {e}")
        
        return None

    def store_in_cache(self, cache_key: str, content: str, ttl_seconds: int = 3600, token_usage: int = 0):
        """Store response in cache"""
        entry = CacheEntry(
            key=cache_key,
            content=content,
            timestamp=datetime.now(),
            ttl_seconds=ttl_seconds,
            token_usage=token_usage
        )
        
        try:
            # Store in database
            with self.cache_pool.get_connection() as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO cache_entries 
                    (key, content, timestamp, ttl_seconds, hit_count, token_usage)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    cache_key,
                    content,
                    entry.timestamp.isoformat(),
                    ttl_seconds,
                    0,
                    token_usage
                ))
                conn.commit()
            
            # Add to memory cache
            self.add_to_memory_cache(entry)
            
            logger.debug(f"[SAVE] Cached response: {cache_key[:12]}... (TTL: {ttl_seconds}s)")
            
        except Exception as e:
            logger.error(f"Error storing in cache: {e}")

    def add_to_memory_cache(self, entry: CacheEntry):
        """Add entry to memory cache with size management"""
        # Remove oldest entries if cache is full
        if len(self.memory_cache) >= self.max_memory_cache:
            # Remove least recently used (by timestamp)
            oldest_key = min(
                self.memory_cache.keys(),
                key=lambda k: self.memory_cache[k].timestamp
            )
            del self.memory_cache[oldest_key]
        
        self.memory_cache[entry.key] = entry

    def is_cache_valid(self, entry: CacheEntry) -> bool:
        """Check if cache entry is still valid"""
        expiry_time = entry.timestamp + timedelta(seconds=entry.ttl_seconds)
        return datetime.now() < expiry_time

    def check_rate_limits(self, provider: str) -> tuple[bool, str]:
        """Check if we can make an API call without hitting rate limits"""
        now = datetime.now()
        
        try:
            with sqlite3.connect(self.rate_limit_db) as conn:
                # Check requests per minute
                minute_ago = now - timedelta(minutes=1)
                cursor = conn.execute(
                    "SELECT COUNT(*) FROM api_calls WHERE provider = ? AND timestamp > ?",
                    (provider, minute_ago.isoformat())
                )
                requests_last_minute = cursor.fetchone()[0]
                
                if requests_last_minute >= self.rate_limits.requests_per_minute:
                    wait_time = 60 - (now - minute_ago).seconds
                    return False, f"Rate limit: {requests_last_minute}/{self.rate_limits.requests_per_minute} per minute. Wait {wait_time}s"
                
                # Check requests per hour
                hour_ago = now - timedelta(hours=1)
                cursor = conn.execute(
                    "SELECT COUNT(*) FROM api_calls WHERE provider = ? AND timestamp > ?",
                    (provider, hour_ago.isoformat())
                )
                requests_last_hour = cursor.fetchone()[0]
                
                if requests_last_hour >= self.rate_limits.requests_per_hour:
                    return False, f"Rate limit: {requests_last_hour}/{self.rate_limits.requests_per_hour} per hour"
                
                # Check requests per day
                day_ago = now - timedelta(days=1)
                cursor = conn.execute(
                    "SELECT COUNT(*) FROM api_calls WHERE provider = ? AND timestamp > ?",
                    (provider, day_ago.isoformat())
                )
                requests_last_day = cursor.fetchone()[0]
                
                if requests_last_day >= self.rate_limits.requests_per_day:
                    return False, f"Rate limit: {requests_last_day}/{self.rate_limits.requests_per_day} per day"
                
                # Check tokens per minute (if tracking)
                cursor = conn.execute(
                    "SELECT SUM(tokens_used) FROM api_calls WHERE provider = ? AND timestamp > ?",
                    (provider, minute_ago.isoformat())
                )
                tokens_result = cursor.fetchone()[0]
                tokens_last_minute = tokens_result or 0
                
                if tokens_last_minute >= self.rate_limits.tokens_per_minute:
                    return False, f"Token rate limit: {tokens_last_minute}/{self.rate_limits.tokens_per_minute} per minute"
        
        except Exception as e:
            logger.error(f"Error checking rate limits: {e}")
            # FIXED: Fail closed for security - deny request on rate limit check failure
            return False, f"Rate limit check failed: {e}"
        
        return True, "OK"

    def record_api_call(self, provider: str, model: str, tokens_used: int = 0, response_time_ms: int = 0, success: bool = True):
        """Record an API call for rate limiting tracking"""
        try:
            with sqlite3.connect(self.rate_limit_db) as conn:
                conn.execute('''
                    INSERT INTO api_calls (timestamp, provider, model, tokens_used, response_time_ms, success)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    datetime.now().isoformat(),
                    provider,
                    model,
                    tokens_used,
                    response_time_ms,
                    success
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"Error recording API call: {e}")

    def cleanup_old_entries(self, days_old: int = 7):
        """Clean up old cache entries and API call records"""
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        try:
            # Clean cache
            with sqlite3.connect(self.cache_db) as conn:
                cursor = conn.execute(
                    "DELETE FROM cache_entries WHERE timestamp < ?",
                    (cutoff_date.isoformat(),)
                )
                cache_deleted = cursor.rowcount
                conn.commit()
            
            # Clean API call records
            with sqlite3.connect(self.rate_limit_db) as conn:
                cursor = conn.execute(
                    "DELETE FROM api_calls WHERE timestamp < ?",
                    (cutoff_date.isoformat(),)
                )
                api_deleted = cursor.rowcount
                conn.commit()
            
            logger.info(f"[EMOJI] Cleanup completed: {cache_deleted} cache entries, {api_deleted} API records removed")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        stats = {
            'memory_cache_size': len(self.memory_cache),
            'memory_cache_max': self.max_memory_cache
        }
        
        try:
            with sqlite3.connect(self.cache_db) as conn:
                # Total entries
                cursor = conn.execute("SELECT COUNT(*) FROM cache_entries")
                stats['total_cache_entries'] = cursor.fetchone()[0]
                
                # Cache hits
                cursor = conn.execute("SELECT SUM(hit_count) FROM cache_entries")
                result = cursor.fetchone()[0]
                stats['total_cache_hits'] = result or 0
                
                # Most popular entries
                cursor = conn.execute(
                    "SELECT key, hit_count FROM cache_entries ORDER BY hit_count DESC LIMIT 5"
                )
                stats['top_cached_keys'] = [
                    {'key': row[0][:12] + '...', 'hits': row[1]}
                    for row in cursor.fetchall()
                ]
            
            with sqlite3.connect(self.rate_limit_db) as conn:
                # API call stats for last 24 hours
                day_ago = (datetime.now() - timedelta(days=1)).isoformat()
                
                cursor = conn.execute(
                    "SELECT provider, COUNT(*), AVG(response_time_ms), SUM(tokens_used) FROM api_calls WHERE timestamp > ? GROUP BY provider",
                    (day_ago,)
                )
                stats['api_usage_24h'] = [
                    {
                        'provider': row[0],
                        'calls': row[1],
                        'avg_response_ms': round(row[2] or 0, 1),
                        'total_tokens': row[3] or 0
                    }
                    for row in cursor.fetchall()
                ]
        
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            stats['error'] = str(e)
        
        return stats

    def estimate_tokens(self, text: str) -> int:
        """Rough estimate of token count (4 chars ≈ 1 token)"""
        return max(1, len(text) // 4)

    def get_smart_ttl(self, request_type: str, confidence: float = 0.5) -> int:
        """Get smart TTL based on request type and confidence"""
        base_ttls = {
            'system_status': 60,      # Status checks cache for 1 minute
            'decision_making': 300,   # Decisions cache for 5 minutes
            'error_analysis': 600,    # Error analysis cache for 10 minutes
            'general_chat': 1800,     # Chat responses cache for 30 minutes
            'reports': 3600,          # Reports cache for 1 hour
            'configuration': 7200     # Config help cache for 2 hours
        }
        
        base_ttl = base_ttls.get(request_type, 1800)
        
        # Lower confidence = shorter cache time
        confidence_multiplier = max(0.1, confidence)
        
        return int(base_ttl * confidence_multiplier)

    def should_use_cache(self, request_type: str) -> bool:
        """Determine if request type should use caching"""
        no_cache_types = [
            'real_time_monitoring',
            'immediate_action',
            'critical_alert'
        ]
        
        return request_type not in no_cache_types

# Context manager for cache operations
class CachedAPICall:
    """Context manager for cached API calls with rate limiting"""
    
    def __init__(self, cache_manager: AICacheManager, provider: str, model: str, 
                 request_type: str = 'general', use_cache: bool = True):
        self.cache_manager = cache_manager
        self.provider = provider
        self.model = model
        self.request_type = request_type
        self.use_cache = use_cache and cache_manager.should_use_cache(request_type)
        self.start_time = None
        self.cache_key = None
        
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            response_time_ms = int((time.time() - self.start_time) * 1000)
            success = exc_type is None
            
            # Record the API call for rate limiting
            self.cache_manager.record_api_call(
                provider=self.provider,
                model=self.model,
                response_time_ms=response_time_ms,
                success=success
            )
    
    def get_cached_or_call(self, messages: List[Dict], config: Dict, api_call_func):
        """Get from cache or make API call"""
        
        # Generate cache key
        if self.use_cache:
            self.cache_key = self.cache_manager.generate_cache_key(messages, config)
            
            # Try cache first
            cached_response = self.cache_manager.get_from_cache(self.cache_key)
            if cached_response:
                return cached_response, True  # True = from cache
        
        # Check rate limits
        can_call, limit_msg = self.cache_manager.check_rate_limits(self.provider)
        if not can_call:
            logger.warning(f"[STATUS] Rate limit hit: {limit_msg}")
            raise Exception(f"Rate limit exceeded: {limit_msg}")
        
        # Make API call
        response = api_call_func()
        
        # Cache the response
        if self.use_cache and response and self.cache_key:
            # Estimate tokens for tracking
            tokens_used = self.cache_manager.estimate_tokens(str(messages) + response)
            
            # Get smart TTL based on request type
            ttl = self.cache_manager.get_smart_ttl(self.request_type)
            
            self.cache_manager.store_in_cache(
                cache_key=self.cache_key,
                content=response,
                ttl_seconds=ttl,
                token_usage=tokens_used
            )
        
        return response, False  # False = from API