"""
Advanced Task Management System
AP2-inspired task management with prefetching, caching, and intelligent optimization

Features:
- Intelligent task prefetching and prediction
- Advanced result caching with TTL
- Task dependency management
- Dynamic priority adjustment
- Task batching and optimization
- Performance analytics
- Shared state management
- Collaborative task execution

Author: Advanced Task Management Module
Version: 1.0.0
"""

import asyncio
import json
import time
import logging
from typing import Dict, List, Optional, Any, Set, Callable, AsyncGenerator, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime, timedelta
from pathlib import Path
import uuid
import hashlib
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict, deque
import queue
import heapq
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class TaskType(Enum):
    """Types of tasks with different execution patterns"""
    COMPUTATIONAL = "computational"
    IO_BOUND = "io_bound"
    NETWORK = "network"
    AI_INFERENCE = "ai_inference"
    DATA_PROCESSING = "data_processing"
    COLLABORATIVE = "collaborative"
    BATCH = "batch"
    REAL_TIME = "real_time"

class TaskStatus(Enum):
    """Enhanced task status states"""
    PENDING = "pending"
    PREFETCHED = "prefetched"
    QUEUED = "queued"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"
    RETRYING = "retrying"

class CacheStrategy(Enum):
    """Task result caching strategies"""
    NONE = "none"
    SIMPLE = "simple"
    LRU = "lru"
    LFU = "lfu"
    ADAPTIVE = "adaptive"
    DISTRIBUTED = "distributed"

class OptimizationStrategy(Enum):
    """Task optimization strategies"""
    NONE = "none"
    LOAD_BALANCING = "load_balancing"
    PIPELINING = "pipelining"
    BATCHING = "batching"
    PARALLELIZATION = "parallelization"
    ADAPTIVE = "adaptive"

@dataclass
class TaskDependency:
    """Task dependency specification"""
    task_id: str
    dependency_type: str  # "hard", "soft", "conditional"
    condition: Optional[Callable[[Any], bool]] = None
    timeout: Optional[timedelta] = None
    on_failure: str = "abort"  # "abort", "skip", "retry"

@dataclass
class TaskMetrics:
    """Detailed task performance metrics"""
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    assigned_at: Optional[datetime] = None

    # Timing metrics
    queue_time: Optional[timedelta] = None
    execution_time: Optional[timedelta] = None
    total_time: Optional[timedelta] = None

    # Resource usage
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    io_operations: int = 0
    network_calls: int = 0

    # Performance metrics
    success: bool = False
    error_message: Optional[str] = None
    retry_count: int = 0
    timeout_occurred: bool = False

    # Quality metrics
    result_quality: float = 0.0
    user_satisfaction: Optional[float] = None

    def calculate_efficiency(self) -> float:
        """Calculate overall task efficiency"""
        if not self.execution_time:
            return 0.0

        # Combine multiple factors
        time_efficiency = 1.0 / max(1.0, self.execution_time.total_seconds())
        resource_efficiency = 1.0 / max(1.0, self.cpu_usage + self.memory_usage)
        quality_score = self.result_quality

        # Weighted combination
        return (time_efficiency * 0.3 + resource_efficiency * 0.3 + quality_score * 0.4)

@dataclass
class AdvancedTask:
    """Advanced task with comprehensive metadata"""
    id: str
    title: str
    description: str
    task_type: TaskType

    # Basic task data
    input_data: Dict[str, Any] = field(default_factory=dict)
    expected_output: Optional[Dict[str, Any]] = None

    # Scheduling and priority
    priority: int = 1  # 1-10, higher is more important
    deadline: Optional[datetime] = None
    estimated_duration: Optional[timedelta] = None
    max_duration: Optional[timedelta] = None

    # Execution context
    status: TaskStatus = TaskStatus.PENDING
    assigned_to: Optional[str] = None
    assigned_at: Optional[datetime] = None
    progress: float = 0.0  # 0.0 to 1.0

    # Dependencies
    dependencies: List[TaskDependency] = field(default_factory=list)
    dependent_tasks: List[str] = field(default_factory=list)

    # Execution settings
    max_retries: int = 3
    timeout: Optional[timedelta] = None
    retry_delay: timedelta = timedelta(seconds=1)
    backoff_factor: float = 2.0

    # Caching settings
    cache_strategy: CacheStrategy = CacheStrategy.SIMPLE
    cache_key: Optional[str] = None
    cache_ttl: Optional[timedelta] = timedelta(hours=1)
    is_cacheable: bool = True

    # Optimization settings
    optimization_strategy: OptimizationStrategy = OptimizationStrategy.ADAPTIVE
    batch_id: Optional[str] = None
    pipeline_stage: Optional[int] = None

    # Collaboration settings
    collaboration_enabled: bool = False
    collaborators: List[str] = field(default_factory=list)
    shared_context: Dict[str, Any] = field(default_factory=dict)

    # Metadata and tracking
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    # Results and metrics
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metrics: Optional[TaskMetrics] = None

    def __post_init__(self):
        """Initialize task components"""
        # Generate cache key if cacheable
        if self.is_cacheable and not self.cache_key:
            self._generate_cache_key()

        # Initialize metrics
        if not self.metrics:
            self.metrics = TaskMetrics(created_at=self.created_at)

    def _generate_cache_key(self):
        """Generate cache key for task"""
        cache_data = {
            "task_type": self.task_type.value,
            "title": self.title,
            "description": self.description,
            "input_data": self.input_data,
            "parameters": self.metadata.get("parameters", {})
        }
        normalized_data = json.dumps(cache_data, sort_keys=True)
        self.cache_key = hashlib.sha256(normalized_data.encode()).hexdigest()

    def can_start(self, completed_tasks: Set[str]) -> bool:
        """Check if task can start based on dependencies"""
        if not self.dependencies:
            return True

        for dep in self.dependencies:
            if dep.dependency_type == "hard":
                if dep.task_id not in completed_tasks:
                    return False
            elif dep.dependency_type == "conditional":
                if dep.condition and not dep.condition(self.input_data):
                    return False
            elif dep.dependency_type == "soft":
                # Soft dependencies don't block execution
                pass

        return True

    def is_overdue(self) -> bool:
        """Check if task is overdue"""
        if not self.deadline:
            return False
        return datetime.now() > self.deadline

    def get_priority_score(self) -> float:
        """Calculate dynamic priority score"""
        base_priority = self.priority

        # Age factor (older tasks get higher priority)
        age_hours = (datetime.now() - self.created_at).total_seconds() / 3600
        age_factor = min(age_hours / 24, 2.0)  # Max 2x boost for 24+ hours old

        # Deadline urgency
        deadline_factor = 0.0
        if self.deadline:
            hours_until_deadline = (self.deadline - datetime.now()).total_seconds() / 3600
            if hours_until_deadline < 1:
                deadline_factor = 3.0
            elif hours_until_deadline < 6:
                deadline_factor = 2.0
            elif hours_until_deadline < 24:
                deadline_factor = 1.0

        # Retry penalty
        retry_penalty = self.metrics.retry_count * 0.1 if self.metrics else 0

        return base_priority + age_factor + deadline_factor - retry_penalty

class TaskPredictor:
    """Machine learning-based task prediction for prefetching"""

    def __init__(self):
        self.task_history: List[AdvancedTask] = []
        self.patterns: Dict[str, Any] = {}
        self.is_trained = False

    def add_to_history(self, task: AdvancedTask):
        """Add completed task to history for learning"""
        if task.status == TaskStatus.COMPLETED:
            self.task_history.append(task)
            self._update_patterns()

    def predict_next_tasks(self, current_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Predict likely next tasks based on patterns"""
        predictions = []

        if not self.is_trained or len(self.task_history) < 10:
            return predictions

        # Simple pattern-based prediction
        # In production, this would use sophisticated ML models

        # Time-based patterns
        current_hour = datetime.now().hour
        current_day = datetime.now().weekday()

        # Find similar historical patterns
        similar_tasks = [
            task for task in self.task_history
            if (task.created_at.hour == current_hour or
                task.created_at.weekday() == current_day)
        ]

        # Extract common task types and parameters
        task_type_counts = defaultdict(int)
        for task in similar_tasks:
            task_type_counts[task.task_type.value] += 1

        # Generate predictions for most common task types
        for task_type, count in task_type_counts.items():
            if count >= 3:  # Threshold for prediction confidence
                predictions.append({
                    "task_type": task_type,
                    "confidence": min(count / len(similar_tasks), 1.0),
                    "estimated_parameters": self._extract_typical_parameters(task_type)
                })

        return sorted(predictions, key=lambda x: x["confidence"], reverse=True)[:5]

    def _update_patterns(self):
        """Update internal pattern models"""
        if len(self.task_history) >= 10:
            self.is_trained = True
            self._analyze_patterns()

    def _analyze_patterns(self):
        """Analyze task patterns for prediction"""
        # Analyze temporal patterns
        temporal_patterns = defaultdict(list)
        for task in self.task_history:
            hour_key = task.created_at.hour
            temporal_patterns[hour_key].append(task.task_type.value)

        # Find frequent patterns
        self.patterns["temporal"] = {}
        for hour, tasks in temporal_patterns.items():
            if len(tasks) >= 3:
                task_counts = defaultdict(int)
                for task_type in tasks:
                    task_counts[task_type] += 1

                self.patterns["temporal"][hour] = {
                    task_type: count / len(tasks)
                    for task_type, count in task_counts.items()
                }

    def _extract_typical_parameters(self, task_type: str) -> Dict[str, Any]:
        """Extract typical parameters for task type"""
        similar_tasks = [
            task for task in self.task_history
            if task.task_type.value == task_type
        ]

        if not similar_tasks:
            return {}

        # Extract common metadata parameters
        all_params = []
        for task in similar_tasks:
            params = task.metadata.get("parameters", {})
            all_params.append(params)

        # Find most common parameters
        typical_params = {}
        if all_params:
            # Simple parameter extraction
            param_keys = set()
            for params in all_params:
                param_keys.update(params.keys())

            for key in param_keys:
                values = [params.get(key) for params in all_params if key in params]
                if values:
                    # Use most common value
                    typical_params[key] = max(set(values), key=values.count)

        return typical_params

class AdvancedCache:
    """Advanced caching system for task results"""

    def __init__(self, max_size: int = 1000, strategy: CacheStrategy = CacheStrategy.ADAPTIVE):
        self.max_size = max_size
        self.strategy = strategy
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.access_records: Dict[str, List[datetime]] = defaultdict(list)
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "size": 0
        }

        # Strategy-specific data
        if strategy == CacheStrategy.LRU:
            self.lru_queue = deque()
        elif strategy == CacheStrategy.LFU:
            self.access_counts = defaultdict(int)

    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get item from cache"""
        if key not in self.cache:
            self.stats["misses"] += 1
            return None

        cache_item = self.cache[key]

        # Check if expired
        if cache_item.get("expires_at", datetime.max) <= datetime.now():
            await self._evict(key)
            self.stats["misses"] += 1
            return None

        # Update access records
        self.access_records[key].append(datetime.now())
        if self.strategy == CacheStrategy.LRU:
            self._update_lru(key)
        elif self.strategy == CacheStrategy.LFU:
            self.access_counts[key] += 1

        self.stats["hits"] += 1
        return cache_item["data"]

    async def put(self, key: str, data: Dict[str, Any], ttl: Optional[timedelta] = None):
        """Put item in cache"""
        # Check capacity and evict if necessary
        if len(self.cache) >= self.max_size:
            await self._evict_lru()

        expires_at = datetime.max
        if ttl:
            expires_at = datetime.now() + ttl

        self.cache[key] = {
            "data": data,
            "created_at": datetime.now(),
            "expires_at": expires_at,
            "size": len(json.dumps(data))
        }

        self.access_records[key] = [datetime.now()]

        if self.strategy == CacheStrategy.LRU:
            self._update_lru(key)
        elif self.strategy == CacheStrategy.LFU:
            self.access_counts[key] = 1

        self.stats["size"] = len(self.cache)

    async def _evict_lru(self):
        """Evict least recently used item"""
        if self.strategy == CacheStrategy.LRU and self.lru_queue:
            key = self.lru_queue.popleft()
            await self._evict(key)
        else:
            # Find least recently accessed
            if self.access_records:
                lru_key = min(self.access_records.keys(),
                             key=lambda k: max(self.access_records[k]) if self.access_records[k] else datetime.min)
                await self._evict(lru_key)

    async def _evict(self, key: str):
        """Evict specific key from cache"""
        if key in self.cache:
            del self.cache[key]
            if key in self.access_records:
                del self.access_records[key]
            if key in self.access_counts:
                del self.access_counts[key]
            if key in self.lru_queue:
                try:
                    self.lru_queue.remove(key)
                except ValueError:
                    pass
            self.stats["evictions"] += 1
            self.stats["size"] = len(self.cache)

    def _update_lru(self, key: str):
        """Update LRU queue"""
        if key in self.lru_queue:
            self.lru_queue.remove(key)
        self.lru_queue.append(key)

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = self.stats["hits"] / total_requests if total_requests > 0 else 0

        return {
            **self.stats,
            "hit_rate": hit_rate,
            "total_requests": total_requests,
            "strategy": self.strategy.value,
            "utilization": len(self.cache) / self.max_size
        }

class TaskBatcher:
    """Task batching and optimization"""

    def __init__(self, max_batch_size: int = 10, max_wait_time: timedelta = timedelta(seconds=5)):
        self.max_batch_size = max_batch_size
        self.max_wait_time = max_wait_time
        self.pending_batches: Dict[str, List[AdvancedTask]] = defaultdict(list)
        self.batch_timers: Dict[str, asyncio.Task] = {}

    async def add_to_batch(self, task: AdvancedTask, batch_key: str) -> bool:
        """Add task to batch for processing"""
        self.pending_batches[batch_key].append(task)

        # Start timer if this is the first task in batch
        if len(self.pending_batches[batch_key]) == 1:
            self.batch_timers[batch_key] = asyncio.create_task(
                self._batch_timeout(batch_key)
            )

        # Check if batch is ready
        if len(self.pending_batches[batch_key]) >= self.max_batch_size:
            await self._process_batch(batch_key)
            return True

        return False

    async def _batch_timeout(self, batch_key: str):
        """Handle batch timeout"""
        await asyncio.sleep(self.max_wait_time.total_seconds())
        await self._process_batch(batch_key)

    async def _process_batch(self, batch_key: str):
        """Process batch of tasks"""
        if batch_key not in self.pending_batches:
            return

        batch_tasks = self.pending_batches.pop(batch_key, [])
        if batch_key in self.batch_timers:
            self.batch_timers[batch_key].cancel()
            del self.batch_timers[batch_key]

        if not batch_tasks:
            return

        # Update tasks with batch information
        batch_id = str(uuid.uuid4())
        for i, task in enumerate(batch_tasks):
            task.batch_id = batch_id
            task.metadata["batch_position"] = i
            task.metadata["batch_size"] = len(batch_tasks)

        logger.info(f"Processing batch {batch_id} with {len(batch_tasks)} tasks")
        return batch_tasks

class AdvancedTaskManager:
    """Advanced task management system with AP2-inspired features"""

    def __init__(self):
        self.tasks: Dict[str, AdvancedTask] = {}
        self.completed_tasks: Set[str] = set()
        self.pending_queue = asyncio.PriorityQueue()
        self.active_tasks: Dict[str, AdvancedTask] = {}
        self.failed_tasks: Dict[str, AdvancedTask] = {}

        # Task dependencies graph
        self.dependency_graph: Dict[str, List[str]] = defaultdict(list)
        self.reverse_dependency_graph: Dict[str, List[str]] = defaultdict(list)

        # Optimization components
        self.task_predictor = TaskPredictor()
        self.cache = AdvancedCache(strategy=CacheStrategy.ADAPTIVE)
        self.batcher = TaskBatcher()
        self.executor = ThreadPoolExecutor(max_workers=10)

        # Performance tracking
        self.performance_stats = {
            "tasks_created": 0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "avg_execution_time": 0.0,
            "cache_hit_rate": 0.0,
            "prefetch_accuracy": 0.0
        }

        # Background services
        self.prefetcher = TaskPrefetcher(self)
        self.optimizer = TaskOptimizer(self)
        self.monitor = TaskMonitor(self)

        # Configuration
        self.max_concurrent_tasks = 50
        self.enable_prefetching = True
        self.enable_caching = True
        self.enable_batching = True

        # Event handlers
        self.task_completed_handlers: List[Callable] = []
        self.task_failed_handlers: List[Callable] = []

    async def initialize(self) -> bool:
        """Initialize task manager"""
        try:
            # Start background services
            await self.prefetcher.start()
            await self.optimizer.start()
            await self.monitor.start()

            # Start processing loops
            asyncio.create_task(self._task_processing_loop())
            asyncio.create_task(self._dependency_resolution_loop())
            asyncio.create_task(self._performance_tracking_loop())

            logger.info("Advanced Task Manager initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize task manager: {e}")
            return False

    async def create_task(self, title: str, description: str, task_type: TaskType,
                         input_data: Dict[str, Any] = None, **kwargs) -> str:
        """Create a new advanced task"""
        task_id = str(uuid.uuid4())

        task = AdvancedTask(
            id=task_id,
            title=title,
            description=description,
            task_type=task_type,
            input_data=input_data or {},
            **kwargs
        )

        self.tasks[task_id] = task
        self.performance_stats["tasks_created"] += 1

        # Add to dependency graph
        for dep in task.dependencies:
            self.dependency_graph[dep.task_id].append(task_id)
            self.reverse_dependency_graph[task_id].append(dep.task_id)

        # Add to processing queue
        priority_score = task.get_priority_score()
        await self.pending_queue.put((-priority_score, task_id))  # Negative for max-heap

        logger.info(f"Created task {task_id}: {title}")
        return task_id

    async def _task_processing_loop(self):
        """Main task processing loop"""
        while True:
            try:
                # Get next task
                priority, task_id = await asyncio.wait_for(self.pending_queue.get(), timeout=1.0)
                task = self.tasks.get(task_id)

                if not task:
                    continue

                # Check if task can start
                if not task.can_start(self.completed_tasks):
                    # Re-queue for later
                    await asyncio.sleep(1)
                    await self.pending_queue.put((priority, task_id))
                    continue

                # Check cache
                if self.enable_caching and task.is_cacheable and task.cache_key:
                    cached_result = await self.cache.get(task.cache_key)
                    if cached_result:
                        await self._complete_task_from_cache(task, cached_result)
                        continue

                # Assign task for execution
                await self._assign_task(task)

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error in task processing loop: {e}")

    async def _assign_task(self, task: AdvancedTask):
        """Assign task for execution"""
        task.status = TaskStatus.ASSIGNED
        task.assigned_at = datetime.now()
        self.active_tasks[task.id] = task

        # Execute task based on type and optimization strategy
        if task.optimization_strategy == OptimizationStrategy.BATCHING and self.enable_batching:
            batch_key = f"{task.task_type.value}_{hash(str(task.input_data)) % 10}"
            batch_ready = await self.batcher.add_to_batch(task, batch_key)

            if not batch_ready:
                task.status = TaskStatus.QUEUED
        else:
            # Execute individual task
            asyncio.create_task(self._execute_task(task))

    async def _execute_task(self, task: AdvancedTask):
        """Execute individual task"""
        task.status = TaskStatus.IN_PROGRESS
        task.metrics.started_at = datetime.now()

        try:
            # Execute with timeout
            if task.timeout:
                result = await asyncio.wait_for(
                    self._run_task_execution(task),
                    timeout=task.timeout.total_seconds()
                )
            else:
                result = await self._run_task_execution(task)

            # Task completed successfully
            await self._complete_task(task, result)

        except asyncio.TimeoutError:
            await self._handle_task_timeout(task)
        except Exception as e:
            await self._handle_task_failure(task, e)

    async def _run_task_execution(self, task: AdvancedTask) -> Dict[str, Any]:
        """Run the actual task execution"""
        # This is a placeholder - in a real implementation, this would
        # delegate to appropriate task executors based on task type

        # Simulate task execution
        if task.task_type == TaskType.COMPUTATIONAL:
            result = await self._execute_computational_task(task)
        elif task.task_type == TaskType.IO_BOUND:
            result = await self._execute_io_task(task)
        elif task.task_type == TaskType.AI_INFERENCE:
            result = await self._execute_ai_task(task)
        else:
            result = await self._execute_generic_task(task)

        return result

    async def _execute_computational_task(self, task: AdvancedTask) -> Dict[str, Any]:
        """Execute computational task"""
        # Simulate computation
        await asyncio.sleep(0.1)
        return {
            "result": f"Computation completed for {task.title}",
            "computed_values": [1, 2, 3, 4, 5],
            "timestamp": datetime.now().isoformat()
        }

    async def _execute_io_task(self, task: AdvancedTask) -> Dict[str, Any]:
        """Execute I/O bound task"""
        # Simulate I/O operation
        await asyncio.sleep(0.5)
        return {
            "result": f"I/O operation completed for {task.title}",
            "data_read": 1024,
            "data_written": 512,
            "timestamp": datetime.now().isoformat()
        }

    async def _execute_ai_task(self, task: AdvancedTask) -> Dict[str, Any]:
        """Execute AI inference task"""
        # Simulate AI inference
        await asyncio.sleep(0.3)
        return {
            "result": f"AI inference completed for {task.title}",
            "confidence": 0.95,
            "predictions": ["positive", "neutral", "negative"],
            "timestamp": datetime.now().isoformat()
        }

    async def _execute_generic_task(self, task: AdvancedTask) -> Dict[str, Any]:
        """Execute generic task"""
        await asyncio.sleep(0.2)
        return {
            "result": f"Generic task completed for {task.title}",
            "status": "success",
            "timestamp": datetime.now().isoformat()
        }

    async def _complete_task(self, task: AdvancedTask, result: Dict[str, Any]):
        """Complete task successfully"""
        task.status = TaskStatus.COMPLETED
        task.result = result
        task.metrics.completed_at = datetime.now()
        task.metrics.success = True
        task.progress = 1.0

        # Calculate timing metrics
        if task.metrics.started_at:
            task.metrics.execution_time = task.metrics.completed_at - task.metrics.started_at
        if task.metrics.assigned_at:
            task.metrics.queue_time = task.metrics.started_at - task.metrics.assigned_at
        task.metrics.total_time = task.metrics.completed_at - task.metrics.created_at

        # Cache result
        if self.enable_caching and task.is_cacheable and task.cache_key:
            await self.cache.put(task.cache_key, result, task.cache_ttl)

        # Update state
        self.completed_tasks.add(task.id)
        if task.id in self.active_tasks:
            del self.active_tasks[task.id]

        # Update stats
        self.performance_stats["tasks_completed"] += 1
        self._update_performance_stats(task)

        # Add to predictor history
        self.task_predictor.add_to_history(task)

        # Notify dependencies
        await self._notify_dependent_tasks(task.id)

        # Trigger event handlers
        for handler in self.task_completed_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(task)
                else:
                    handler(task)
            except Exception as e:
                logger.error(f"Error in task completed handler: {e}")

        logger.info(f"Task {task.id} completed successfully")

    async def _complete_task_from_cache(self, task: AdvancedTask, cached_result: Dict[str, Any]):
        """Complete task from cached result"""
        task.status = TaskStatus.COMPLETED
        task.result = cached_result
        task.metrics.completed_at = datetime.now()
        task.metrics.success = True
        task.progress = 1.0

        # Update state
        self.completed_tasks.add(task.id)

        # Update stats
        self.performance_stats["tasks_completed"] += 1

        # Notify dependencies
        await self._notify_dependent_tasks(task.id)

        logger.info(f"Task {task.id} completed from cache")

    async def _handle_task_timeout(self, task: AdvancedTask):
        """Handle task timeout"""
        task.status = TaskStatus.TIMEOUT
        task.metrics.completed_at = datetime.now()
        task.metrics.timeout_occurred = True
        task.error = "Task execution timed out"

        await self._handle_task_failure(task, TimeoutError("Task timed out"))

    async def _handle_task_failure(self, task: AdvancedTask, error: Exception):
        """Handle task failure"""
        task.metrics.retry_count += 1

        if task.metrics.retry_count < task.max_retries:
            # Retry task
            task.status = TaskStatus.RETRYING
            task.error = str(error)

            # Apply backoff delay
            retry_delay = task.retry_delay * (task.backoff_factor ** (task.metrics.retry_count - 1))
            await asyncio.sleep(retry_delay.total_seconds())

            # Re-queue task
            priority_score = task.get_priority_score()
            await self.pending_queue.put((-priority_score, task.id))

            logger.info(f"Retrying task {task.id} (attempt {task.metrics.retry_count})")
        else:
            # Task failed permanently
            task.status = TaskStatus.FAILED
            task.error = str(error)
            task.metrics.completed_at = datetime.now()

            # Update state
            if task.id in self.active_tasks:
                del self.active_tasks[task.id]
            self.failed_tasks[task.id] = task

            # Update stats
            self.performance_stats["tasks_failed"] += 1

            # Trigger failure handlers
            for handler in self.task_failed_handlers:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(task)
                    else:
                        handler(task)
                except Exception as e:
                    logger.error(f"Error in task failed handler: {e}")

            logger.error(f"Task {task.id} failed permanently: {error}")

    async def _notify_dependent_tasks(self, completed_task_id: str):
        """Notify and enable dependent tasks"""
        dependent_ids = self.reverse_dependency_graph.get(completed_task_id, [])

        for dependent_id in dependent_ids:
            if dependent_id in self.tasks:
                dependent_task = self.tasks[dependent_id]
                if dependent_task.can_start(self.completed_tasks):
                    # Re-queue dependent task with updated priority
                    priority_score = dependent_task.get_priority_score()
                    await self.pending_queue.put((-priority_score, dependent_id))

    async def _dependency_resolution_loop(self):
        """Periodic dependency resolution"""
        while True:
            try:
                await asyncio.sleep(5)  # Check every 5 seconds

                # Check for tasks that can now start
                for task_id, task in self.tasks.items():
                    if (task.status == TaskStatus.PENDING and
                        task.can_start(self.completed_tasks) and
                        task_id not in self.active_tasks):

                        priority_score = task.get_priority_score()
                        await self.pending_queue.put((-priority_score, task_id))

            except Exception as e:
                logger.error(f"Error in dependency resolution loop: {e}")

    async def _performance_tracking_loop(self):
        """Track system performance"""
        while True:
            try:
                await asyncio.sleep(30)  # Update every 30 seconds

                # Calculate average execution time
                completed_tasks_list = [t for t in self.tasks.values()
                                      if t.status == TaskStatus.COMPLETED and t.metrics.execution_time]

                if completed_tasks_list:
                    avg_time = sum(t.metrics.execution_time.total_seconds()
                                  for t in completed_tasks_list) / len(completed_tasks_list)
                    self.performance_stats["avg_execution_time"] = avg_time

                # Update cache hit rate
                cache_stats = self.cache.get_stats()
                self.performance_stats["cache_hit_rate"] = cache_stats.get("hit_rate", 0.0)

                # Log performance summary
                logger.debug(f"Task Manager Performance: "
                           f"Active: {len(self.active_tasks)}, "
                           f"Completed: {len(self.completed_tasks)}, "
                           f"Failed: {len(self.failed_tasks)}, "
                           f"Avg Time: {self.performance_stats['avg_execution_time']:.2f}s")

            except Exception as e:
                logger.error(f"Error in performance tracking loop: {e}")

    def _update_performance_stats(self, task: AdvancedTask):
        """Update performance statistics"""
        if task.metrics.execution_time:
            total_completed = self.performance_stats["tasks_completed"]
            current_avg = self.performance_stats["avg_execution_time"]

            # Update moving average
            if total_completed > 1:
                new_avg = (current_avg * (total_completed - 1) +
                          task.metrics.execution_time.total_seconds()) / total_completed
                self.performance_stats["avg_execution_time"] = new_avg
            else:
                self.performance_stats["avg_execution_time"] = task.metrics.execution_time.total_seconds()

    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed task status"""
        task = self.tasks.get(task_id)
        if not task:
            return None

        return {
            "id": task.id,
            "title": task.title,
            "status": task.status.value,
            "progress": task.progress,
            "assigned_to": task.assigned_to,
            "created_at": task.created_at.isoformat(),
            "started_at": task.metrics.started_at.isoformat() if task.metrics.started_at else None,
            "completed_at": task.metrics.completed_at.isoformat() if task.metrics.completed_at else None,
            "execution_time": task.metrics.execution_time.total_seconds() if task.metrics.execution_time else None,
            "retry_count": task.metrics.retry_count,
            "error": task.error,
            "efficiency": task.metrics.calculate_efficiency()
        }

    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        return {
            "tasks": {
                "total": len(self.tasks),
                "pending": len([t for t in self.tasks.values() if t.status == TaskStatus.PENDING]),
                "queued": len([t for t in self.tasks.values() if t.status == TaskStatus.QUEUED]),
                "active": len(self.active_tasks),
                "completed": len(self.completed_tasks),
                "failed": len(self.failed_tasks)
            },
            "performance": self.performance_stats,
            "cache": self.cache.get_stats(),
            "predictor": {
                "trained": self.task_predictor.is_trained,
                "history_size": len(self.task_predictor.task_history)
            }
        }

    def add_task_completed_handler(self, handler: Callable):
        """Add handler for task completion events"""
        self.task_completed_handlers.append(handler)

    def add_task_failed_handler(self, handler: Callable):
        """Add handler for task failure events"""
        self.task_failed_handlers.append(handler)

class TaskPrefetcher:
    """Task prefetching service"""

    def __init__(self, task_manager: AdvancedTaskManager):
        self.task_manager = task_manager
        self.is_running = False
        self.prefetch_queue = asyncio.Queue()

    async def start(self):
        """Start prefetching service"""
        self.is_running = True
        asyncio.create_task(self._prefetching_loop())
        logger.info("Task Prefetcher started")

    async def stop(self):
        """Stop prefetching service"""
        self.is_running = False
        logger.info("Task Prefetcher stopped")

    async def _prefetching_loop(self):
        """Main prefetching loop"""
        while self.is_running:
            try:
                await asyncio.sleep(10)  # Check every 10 seconds

                # Get predictions
                current_context = {"time": datetime.now()}
                predictions = self.task_manager.task_predictor.predict_next_tasks(current_context)

                # Create prefetch tasks
                for prediction in predictions:
                    if prediction["confidence"] > 0.6:  # Confidence threshold
                        await self._create_prefetch_task(prediction)

            except Exception as e:
                logger.error(f"Error in prefetching loop: {e}")

    async def _create_prefetch_task(self, prediction: Dict[str, Any]):
        """Create prefetch task based on prediction"""
        task_id = await self.task_manager.create_task(
            title=f"Prefetched: {prediction['task_type']}",
            description=f"Prefetched task for {prediction['task_type']}",
            task_type=TaskType(prediction["task_type"]),
            input_data=prediction.get("estimated_parameters", {}),
            priority=1,  # Low priority for prefetch tasks
            metadata={"prefetched": True, "confidence": prediction["confidence"]}
        )

        # Mark as prefetched
        if task_id in self.task_manager.tasks:
            self.task_manager.tasks[task_id].status = TaskStatus.PREFETCHED

        logger.debug(f"Created prefetch task {task_id} with confidence {prediction['confidence']:.2f}")

class TaskOptimizer:
    """Task optimization service"""

    def __init__(self, task_manager: AdvancedTaskManager):
        self.task_manager = task_manager
        self.is_running = False

    async def start(self):
        """Start optimization service"""
        self.is_running = True
        asyncio.create_task(self._optimization_loop())
        logger.info("Task Optimizer started")

    async def stop(self):
        """Stop optimization service"""
        self.is_running = False
        logger.info("Task Optimizer stopped")

    async def _optimization_loop(self):
        """Main optimization loop"""
        while self.is_running:
            try:
                await asyncio.sleep(60)  # Optimize every minute

                # Analyze and optimize task queue
                await self._optimize_task_queue()

                # Optimize resource allocation
                await self._optimize_resources()

            except Exception as e:
                logger.error(f"Error in optimization loop: {e}")

    async def _optimize_task_queue(self):
        """Optimize task queue ordering"""
        # Re-prioritize tasks based on current conditions
        pass

    async def _optimize_resources(self):
        """Optimize resource allocation"""
        # Adjust resource allocation based on current load
        pass

class TaskMonitor:
    """Task monitoring and analytics"""

    def __init__(self, task_manager: AdvancedTaskManager):
        self.task_manager = task_manager
        self.is_running = False

    async def start(self):
        """Start monitoring service"""
        self.is_running = True
        asyncio.create_task(self._monitoring_loop())
        logger.info("Task Monitor started")

    async def stop(self):
        """Stop monitoring service"""
        self.is_running = False
        logger.info("Task Monitor stopped")

    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.is_running:
            try:
                await asyncio.sleep(30)  # Monitor every 30 seconds

                # Monitor task execution
                await self._monitor_execution()

                # Check for anomalies
                await self._detect_anomalies()

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")

    async def _monitor_execution(self):
        """Monitor task execution"""
        # Analyze execution patterns and performance
        pass

    async def _detect_anomalies(self):
        """Detect execution anomalies"""
        # Check for unusual patterns or performance issues
        pass

# Global task manager instance
advanced_task_manager = AdvancedTaskManager()

# Convenience functions
async def initialize_advanced_task_manager() -> bool:
    """Initialize advanced task manager"""
    return await advanced_task_manager.initialize()

async def create_advanced_task(title: str, description: str, task_type: TaskType,
                            input_data: Dict[str, Any] = None, **kwargs) -> str:
    """Create advanced task"""
    return await advanced_task_manager.create_task(title, description, task_type, input_data, **kwargs)

async def get_task_system_status() -> Dict[str, Any]:
    """Get task system status"""
    return await advanced_task_manager.get_system_status()

if __name__ == "__main__":
    # Test the advanced task manager
    import asyncio

    async def test():
        print("Advanced Task Manager Test")
        print("=========================")

        # Initialize task manager
        if await initialize_advanced_task_manager():
            print("✅ Advanced task manager initialized")

            # Create test tasks
            task1_id = await create_advanced_task(
                title="Data Analysis",
                description="Analyze sample dataset",
                task_type=TaskType.DATA_PROCESSING,
                input_data={"dataset": "sample.csv", "analysis_type": "statistical"}
            )
            print(f"✅ Created task 1: {task1_id}")

            task2_id = await create_advanced_task(
                title="AI Inference",
                description="Run AI model inference",
                task_type=TaskType.AI_INFERENCE,
                input_data={"model": "bert", "input_text": "Hello world"}
            )
            print(f"✅ Created task 2: {task2_id}")

            # Wait for tasks to complete
            await asyncio.sleep(2)

            # Show status
            status = await get_task_system_status()
            print(f"System Status: {json.dumps(status, indent=2, default=str)}")
        else:
            print("❌ Failed to initialize advanced task manager")

    asyncio.run(test())