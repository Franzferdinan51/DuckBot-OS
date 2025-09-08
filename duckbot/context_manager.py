"""
DuckBot Context Management System
Manages context, memory, and learning data for intelligent agents
"""

import json
import time
import sqlite3
import asyncio
import logging
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import hashlib
import pickle
import threading
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

@dataclass
class ContextSnapshot:
    """Snapshot of context at a specific point in time"""
    context_id: str
    timestamp: float
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    tags: List[str]
    
    def __post_init__(self):
        if not self.context_id:
            self.context_id = self._generate_context_id()
    
    def _generate_context_id(self) -> str:
        """Generate unique context ID"""
        content = f"{self.timestamp}{json.dumps(self.data, sort_keys=True)}"
        return hashlib.md5(content.encode()).hexdigest()[:12]

@dataclass
class LearningPattern:
    """Represents a learned pattern from context analysis"""
    pattern_id: str
    pattern_type: str
    conditions: Dict[str, Any]
    outcomes: Dict[str, Any]
    confidence: float
    usage_count: int
    last_used: float
    success_rate: float
    
    def __post_init__(self):
        if not self.pattern_id:
            self.pattern_id = self._generate_pattern_id()
    
    def _generate_pattern_id(self) -> str:
        """Generate unique pattern ID"""
        content = f"{self.pattern_type}{json.dumps(self.conditions, sort_keys=True)}"
        return hashlib.md5(content.encode()).hexdigest()[:10]

class ContextDatabase:
    """SQLite database for storing context and learning data"""
    
    def __init__(self, db_path: str = "context_memory.db"):
        self.db_path = db_path
        self.lock = threading.Lock()
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize SQLite database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Context snapshots table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS context_snapshots (
                    context_id TEXT PRIMARY KEY,
                    timestamp REAL,
                    data TEXT,
                    metadata TEXT,
                    tags TEXT,
                    created_at REAL
                )
            ''')
            
            # Learning patterns table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS learning_patterns (
                    pattern_id TEXT PRIMARY KEY,
                    pattern_type TEXT,
                    conditions TEXT,
                    outcomes TEXT,
                    confidence REAL,
                    usage_count INTEGER,
                    last_used REAL,
                    success_rate REAL,
                    created_at REAL
                )
            ''')
            
            # Agent memories table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS agent_memories (
                    memory_id TEXT PRIMARY KEY,
                    agent_type TEXT,
                    memory_key TEXT,
                    memory_data TEXT,
                    importance REAL,
                    created_at REAL,
                    last_accessed REAL,
                    access_count INTEGER
                )
            ''')
            
            # Context relationships table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS context_relationships (
                    relationship_id TEXT PRIMARY KEY,
                    source_context TEXT,
                    target_context TEXT,
                    relationship_type TEXT,
                    strength REAL,
                    created_at REAL
                )
            ''')
            
            # Create indexes for better performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_context_timestamp ON context_snapshots(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_pattern_type ON learning_patterns(pattern_type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_agent_memory ON agent_memories(agent_type, memory_key)')
            
            conn.commit()
    
    def store_context_snapshot(self, snapshot: ContextSnapshot):
        """Store context snapshot in database"""
        with self.lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT OR REPLACE INTO context_snapshots 
                        (context_id, timestamp, data, metadata, tags, created_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        snapshot.context_id,
                        snapshot.timestamp,
                        json.dumps(snapshot.data),
                        json.dumps(snapshot.metadata),
                        json.dumps(snapshot.tags),
                        time.time()
                    ))
                    conn.commit()
            except Exception as e:
                logger.error(f"Error storing context snapshot: {e}")
    
    def get_context_snapshots(self, limit: int = 100, tags: Optional[List[str]] = None) -> List[ContextSnapshot]:
        """Retrieve context snapshots from database"""
        with self.lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    if tags:
                        # Filter by tags (this is simplified - could be more sophisticated)
                        placeholders = ','.join('?' * len(tags))
                        cursor.execute(f'''
                            SELECT context_id, timestamp, data, metadata, tags
                            FROM context_snapshots 
                            WHERE tags LIKE '%' || ? || '%'
                            ORDER BY timestamp DESC LIMIT ?
                        ''', (json.dumps(tags[0]), limit))
                    else:
                        cursor.execute('''
                            SELECT context_id, timestamp, data, metadata, tags
                            FROM context_snapshots 
                            ORDER BY timestamp DESC LIMIT ?
                        ''', (limit,))
                    
                    snapshots = []
                    for row in cursor.fetchall():
                        snapshots.append(ContextSnapshot(
                            context_id=row[0],
                            timestamp=row[1],
                            data=json.loads(row[2]),
                            metadata=json.loads(row[3]),
                            tags=json.loads(row[4])
                        ))
                    
                    return snapshots
            except Exception as e:
                logger.error(f"Error retrieving context snapshots: {e}")
                return []
    
    def store_learning_pattern(self, pattern: LearningPattern):
        """Store learning pattern in database"""
        with self.lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT OR REPLACE INTO learning_patterns
                        (pattern_id, pattern_type, conditions, outcomes, confidence, 
                         usage_count, last_used, success_rate, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        pattern.pattern_id,
                        pattern.pattern_type,
                        json.dumps(pattern.conditions),
                        json.dumps(pattern.outcomes),
                        pattern.confidence,
                        pattern.usage_count,
                        pattern.last_used,
                        pattern.success_rate,
                        time.time()
                    ))
                    conn.commit()
            except Exception as e:
                logger.error(f"Error storing learning pattern: {e}")
    
    def get_learning_patterns(self, pattern_type: Optional[str] = None, min_confidence: float = 0.0) -> List[LearningPattern]:
        """Retrieve learning patterns from database"""
        with self.lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    if pattern_type:
                        cursor.execute('''
                            SELECT pattern_id, pattern_type, conditions, outcomes, 
                                   confidence, usage_count, last_used, success_rate
                            FROM learning_patterns 
                            WHERE pattern_type = ? AND confidence >= ?
                            ORDER BY confidence DESC, usage_count DESC
                        ''', (pattern_type, min_confidence))
                    else:
                        cursor.execute('''
                            SELECT pattern_id, pattern_type, conditions, outcomes, 
                                   confidence, usage_count, last_used, success_rate
                            FROM learning_patterns 
                            WHERE confidence >= ?
                            ORDER BY confidence DESC, usage_count DESC
                        ''', (min_confidence,))
                    
                    patterns = []
                    for row in cursor.fetchall():
                        patterns.append(LearningPattern(
                            pattern_id=row[0],
                            pattern_type=row[1],
                            conditions=json.loads(row[2]),
                            outcomes=json.loads(row[3]),
                            confidence=row[4],
                            usage_count=row[5],
                            last_used=row[6],
                            success_rate=row[7]
                        ))
                    
                    return patterns
            except Exception as e:
                logger.error(f"Error retrieving learning patterns: {e}")
                return []
    
    def cleanup_old_data(self, max_age_days: int = 30):
        """Clean up old context data to prevent database bloat"""
        cutoff_time = time.time() - (max_age_days * 24 * 3600)
        
        with self.lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    # Remove old context snapshots
                    cursor.execute('DELETE FROM context_snapshots WHERE created_at < ?', (cutoff_time,))
                    
                    # Remove unused learning patterns
                    cursor.execute('''
                        DELETE FROM learning_patterns 
                        WHERE last_used < ? AND usage_count < 5
                    ''', (cutoff_time,))
                    
                    # Remove old agent memories with low importance
                    cursor.execute('''
                        DELETE FROM agent_memories 
                        WHERE last_accessed < ? AND importance < 0.3
                    ''', (cutoff_time,))
                    
                    conn.commit()
                    logger.info("Cleaned up old context data")
            except Exception as e:
                logger.error(f"Error cleaning up old data: {e}")


class ContextManager:
    """Central manager for context, memory, and learning"""
    
    def __init__(self, db_path: Optional[str] = None):
        self.db = ContextDatabase(db_path or "duckbot_context.db")
        self.active_contexts: Dict[str, Dict[str, Any]] = {}
        self.pattern_cache: Dict[str, List[LearningPattern]] = {}
        self.memory_cache: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.context_relationships: Dict[str, List[str]] = defaultdict(list)
        
        # Start cleanup task - disabled for sync initialization
        # asyncio.create_task(self._periodic_cleanup())
    
    async def create_context_snapshot(self, data: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None, tags: Optional[List[str]] = None) -> ContextSnapshot:
        """Create and store a context snapshot"""
        snapshot = ContextSnapshot(
            context_id="",  # Will be auto-generated
            timestamp=time.time(),
            data=data,
            metadata=metadata or {},
            tags=tags or []
        )
        
        self.db.store_context_snapshot(snapshot)
        return snapshot
    
    async def analyze_context_patterns(self, context_data: Dict[str, Any], context_type: str) -> List[LearningPattern]:
        """Analyze context data to identify patterns"""
        # Check cache first
        cache_key = f"{context_type}_{hashlib.md5(json.dumps(context_data, sort_keys=True).encode()).hexdigest()[:8]}"
        
        if cache_key in self.pattern_cache:
            return self.pattern_cache[cache_key]
        
        # Find matching patterns from database
        existing_patterns = self.db.get_learning_patterns(context_type, min_confidence=0.5)
        matching_patterns = []
        
        for pattern in existing_patterns:
            if self._pattern_matches_context(pattern.conditions, context_data):
                matching_patterns.append(pattern)
                # Update usage statistics
                pattern.usage_count += 1
                pattern.last_used = time.time()
                self.db.store_learning_pattern(pattern)
        
        # Cache results
        self.pattern_cache[cache_key] = matching_patterns
        
        return matching_patterns
    
    def _pattern_matches_context(self, conditions: Dict[str, Any], context_data: Dict[str, Any]) -> bool:
        """Check if pattern conditions match current context"""
        for key, expected_value in conditions.items():
            if key not in context_data:
                return False
            
            actual_value = context_data[key]
            
            # Handle different value types
            if isinstance(expected_value, dict) and "range" in expected_value:
                # Range matching
                range_min = expected_value["range"].get("min", float('-inf'))
                range_max = expected_value["range"].get("max", float('inf'))
                if not (range_min <= actual_value <= range_max):
                    return False
            elif isinstance(expected_value, list):
                # List membership
                if actual_value not in expected_value:
                    return False
            else:
                # Exact match
                if actual_value != expected_value:
                    return False
        
        return True
    
    async def learn_from_outcome(self, context_data: Dict[str, Any], outcome: Dict[str, Any], success: bool, context_type: str):
        """Learn from context-outcome pairs to build patterns"""
        # Extract key features from context
        key_features = self._extract_key_features(context_data)
        
        # Create or update learning pattern
        pattern = LearningPattern(
            pattern_id="",  # Will be auto-generated
            pattern_type=context_type,
            conditions=key_features,
            outcomes=outcome,
            confidence=0.5,  # Starting confidence
            usage_count=1,
            last_used=time.time(),
            success_rate=1.0 if success else 0.0
        )
        
        # Check if similar pattern exists
        existing_patterns = self.db.get_learning_patterns(context_type)
        similar_pattern = None
        
        for existing in existing_patterns:
            if self._patterns_similar(existing.conditions, key_features):
                similar_pattern = existing
                break
        
        if similar_pattern:
            # Update existing pattern
            total_attempts = similar_pattern.usage_count + 1
            success_count = (similar_pattern.success_rate * similar_pattern.usage_count) + (1 if success else 0)
            
            similar_pattern.usage_count = total_attempts
            similar_pattern.success_rate = success_count / total_attempts
            similar_pattern.confidence = min(0.95, similar_pattern.confidence + 0.05 if success else similar_pattern.confidence - 0.02)
            similar_pattern.last_used = time.time()
            
            # Update outcomes (merge with existing)
            similar_pattern.outcomes.update(outcome)
            
            self.db.store_learning_pattern(similar_pattern)
        else:
            # Store new pattern
            self.db.store_learning_pattern(pattern)
    
    def _extract_key_features(self, context_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key features from context data for pattern matching"""
        key_features = {}
        
        # Extract numeric ranges for numeric values
        for key, value in context_data.items():
            if isinstance(value, (int, float)):
                # Create range buckets for numeric values
                if value < 0.3:
                    key_features[key] = {"range": {"min": 0, "max": 0.3}}
                elif value < 0.7:
                    key_features[key] = {"range": {"min": 0.3, "max": 0.7}}
                else:
                    key_features[key] = {"range": {"min": 0.7, "max": 1.0}}
            elif isinstance(value, str):
                # Keep string values as-is
                key_features[key] = value
            elif isinstance(value, bool):
                # Keep boolean values
                key_features[key] = value
            elif isinstance(value, list) and len(value) <= 5:
                # Keep small lists
                key_features[key] = value
        
        return key_features
    
    def _patterns_similar(self, pattern1: Dict[str, Any], pattern2: Dict[str, Any]) -> bool:
        """Check if two patterns are similar enough to merge"""
        common_keys = set(pattern1.keys()) & set(pattern2.keys())
        if len(common_keys) < min(len(pattern1), len(pattern2)) * 0.7:
            return False
        
        matches = 0
        for key in common_keys:
            if pattern1[key] == pattern2[key]:
                matches += 1
        
        similarity = matches / len(common_keys)
        return similarity >= 0.8
    
    async def store_agent_memory(self, agent_type: str, memory_key: str, memory_data: Any, importance: float = 0.5):
        """Store agent-specific memory data"""
        memory_id = f"{agent_type}_{memory_key}_{int(time.time())}"
        
        with sqlite3.connect(self.db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO agent_memories 
                (memory_id, agent_type, memory_key, memory_data, importance, created_at, last_accessed, access_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                memory_id,
                agent_type,
                memory_key,
                json.dumps(memory_data) if not isinstance(memory_data, str) else memory_data,
                importance,
                time.time(),
                time.time(),
                0
            ))
            conn.commit()
        
        # Also store in cache
        cache_key = f"{agent_type}_{memory_key}"
        self.memory_cache[cache_key].append({
            "data": memory_data,
            "timestamp": time.time(),
            "importance": importance
        })
    
    async def retrieve_agent_memory(self, agent_type: str, memory_key: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieve agent-specific memory data"""
        cache_key = f"{agent_type}_{memory_key}"
        
        # Check cache first
        if cache_key in self.memory_cache and len(self.memory_cache[cache_key]) > 0:
            return list(self.memory_cache[cache_key])[-limit:]
        
        # Query database
        with sqlite3.connect(self.db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT memory_data, importance, created_at, last_accessed
                FROM agent_memories
                WHERE agent_type = ? AND memory_key = ?
                ORDER BY created_at DESC LIMIT ?
            ''', (agent_type, memory_key, limit))
            
            memories = []
            for row in cursor.fetchall():
                try:
                    data = json.loads(row[0])
                except:
                    data = row[0]
                
                memories.append({
                    "data": data,
                    "importance": row[1],
                    "created_at": row[2],
                    "last_accessed": row[3]
                })
            
            # Update cache
            self.memory_cache[cache_key].extend(memories)
            
            return memories
    
    async def find_similar_contexts(self, current_context: Dict[str, Any], limit: int = 5) -> List[ContextSnapshot]:
        """Find similar historical contexts"""
        # Get recent context snapshots
        recent_snapshots = self.db.get_context_snapshots(limit=100)
        
        # Calculate similarity scores
        similarities = []
        for snapshot in recent_snapshots:
            similarity = self._calculate_context_similarity(current_context, snapshot.data)
            if similarity > 0.6:  # Only include reasonably similar contexts
                similarities.append((similarity, snapshot))
        
        # Sort by similarity and return top matches
        similarities.sort(key=lambda x: x[0], reverse=True)
        return [snapshot for _, snapshot in similarities[:limit]]
    
    def _calculate_context_similarity(self, context1: Dict[str, Any], context2: Dict[str, Any]) -> float:
        """Calculate similarity between two contexts"""
        common_keys = set(context1.keys()) & set(context2.keys())
        if not common_keys:
            return 0.0
        
        matches = 0
        for key in common_keys:
            val1, val2 = context1[key], context2[key]
            
            if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                # Numeric similarity
                if val1 == 0 and val2 == 0:
                    matches += 1
                elif val1 != 0 or val2 != 0:
                    similarity = 1 - abs(val1 - val2) / max(abs(val1), abs(val2), 1)
                    matches += max(0, similarity)
            elif val1 == val2:
                # Exact match
                matches += 1
            elif isinstance(val1, str) and isinstance(val2, str):
                # String similarity (simplified)
                if val1.lower() in val2.lower() or val2.lower() in val1.lower():
                    matches += 0.5
        
        return matches / len(common_keys)
    
    async def get_context_insights(self, context_type: Optional[str] = None) -> Dict[str, Any]:
        """Get insights about stored contexts and patterns"""
        insights = {
            "total_contexts": 0,
            "total_patterns": 0,
            "pattern_types": {},
            "top_patterns": [],
            "memory_usage": 0
        }
        
        # Count contexts
        with sqlite3.connect(self.db.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM context_snapshots')
            insights["total_contexts"] = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM learning_patterns')
            insights["total_patterns"] = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM agent_memories')
            insights["memory_usage"] = cursor.fetchone()[0]
            
            # Pattern type breakdown
            cursor.execute('''
                SELECT pattern_type, COUNT(*) as count, AVG(confidence) as avg_confidence
                FROM learning_patterns 
                GROUP BY pattern_type
            ''')
            
            for row in cursor.fetchall():
                insights["pattern_types"][row[0]] = {
                    "count": row[1],
                    "avg_confidence": row[2]
                }
            
            # Top patterns by usage
            cursor.execute('''
                SELECT pattern_type, conditions, usage_count, confidence, success_rate
                FROM learning_patterns 
                ORDER BY usage_count DESC, confidence DESC
                LIMIT 10
            ''')
            
            for row in cursor.fetchall():
                insights["top_patterns"].append({
                    "type": row[0],
                    "conditions": json.loads(row[1]),
                    "usage_count": row[2],
                    "confidence": row[3],
                    "success_rate": row[4]
                })
        
        return insights
    
    async def _periodic_cleanup(self):
        """Periodic cleanup of old data"""
        while True:
            try:
                await asyncio.sleep(3600)  # Run every hour
                self.db.cleanup_old_data(max_age_days=30)
                
                # Clear old cache entries
                current_time = time.time()
                for cache_key, patterns in list(self.pattern_cache.items()):
                    # Remove cache entries older than 1 hour
                    if hasattr(patterns, 'timestamp') and current_time - patterns.timestamp > 3600:
                        del self.pattern_cache[cache_key]
                
                logger.info("Periodic context cleanup completed")
            except Exception as e:
                logger.error(f"Error in periodic cleanup: {e}")


# Global context manager instance
context_manager = ContextManager()

# Convenience functions for easy integration
async def create_context(data: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None, tags: Optional[List[str]] = None) -> ContextSnapshot:
    """Create context snapshot"""
    return await context_manager.create_context_snapshot(data, metadata, tags)

async def find_patterns(context_data: Dict[str, Any], context_type: str) -> List[LearningPattern]:
    """Find matching patterns for context"""
    return await context_manager.analyze_context_patterns(context_data, context_type)

async def learn_from_experience(context_data: Dict[str, Any], outcome: Dict[str, Any], success: bool, context_type: str):
    """Learn from context-outcome pair"""
    await context_manager.learn_from_outcome(context_data, outcome, success, context_type)

async def store_memory(agent_type: str, memory_key: str, memory_data: Any, importance: float = 0.5):
    """Store agent memory"""
    await context_manager.store_agent_memory(agent_type, memory_key, memory_data, importance)

async def get_memory(agent_type: str, memory_key: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Retrieve agent memory"""
    return await context_manager.retrieve_agent_memory(agent_type, memory_key, limit)

async def get_insights(context_type: Optional[str] = None) -> Dict[str, Any]:
    """Get context insights"""
    return await context_manager.get_context_insights(context_type)