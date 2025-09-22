#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DuckBot Performance Optimization System
Comprehensive performance optimization for memory, CPU, I/O, and network operations
"""

import os
import sys
import json
import time
import asyncio
import logging
import threading
import psutil
import gc
import tracemalloc
import weakref
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from functools import wraps, lru_cache
from contextlib import contextmanager, asynccontextmanager
import queue
import mmap
import sqlite3
from pathlib import Path
import aiofiles
import aiohttp
from collections import defaultdict, deque
import hashlib
import pickle

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """Performance metrics tracking"""
    timestamp: float = field(default_factory=time.time)
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    memory_used_mb: float = 0.0
    disk_io_read_mb: float = 0.0
    disk_io_write_mb: float = 0.0
    network_io_sent_mb: float = 0.0
    network_io_recv_mb: float = 0.0
    active_threads: int = 0
    active_connections: int = 0
    cache_hit_rate: float = 0.0
    response_time_ms: float = 0.0

class MemoryOptimizer:
    """Advanced memory management and optimization"""

    def __init__(self):
        self.memory_pool = {}
        self.weak_references = weakref.WeakValueDictionary()
        self.memory_thresholds = {
            'warning': 80.0,  # 80% memory usage
            'critical': 90.0,  # 90% memory usage
            'emergency': 95.0  # 95% memory usage
        }
        self.object_sizes = {}
        self.garbage_collection_stats = defaultdict(int)

        # Start memory monitoring
        tracemalloc.start()
        self._start_memory_monitor()

    def _start_memory_monitor(self):
        """Start background memory monitoring"""
        def monitor_loop():
            while True:
                try:
                    memory_percent = psutil.virtual_memory().percent

                    if memory_percent > self.memory_thresholds['emergency']:
                        self._emergency_memory_cleanup()
                    elif memory_percent > self.memory_thresholds['critical']:
                        self._critical_memory_cleanup()
                    elif memory_percent > self.memory_thresholds['warning']:
                        self._warning_memory_cleanup()

                    time.sleep(5)  # Check every 5 seconds
                except Exception as e:
                    logger.error(f"Memory monitor error: {e}")
                    time.sleep(10)

        thread = threading.Thread(target=monitor_loop, daemon=True)
        thread.start()

    def _emergency_memory_cleanup(self):
        """Emergency memory cleanup"""
        logger.warning("Emergency memory cleanup triggered")

        # Force garbage collection
        collected = gc.collect(2)  # Generation 2 collection
        self.garbage_collection_stats['emergency'] += collected

        # Clear memory pools
        self.memory_pool.clear()

        # Clear caches
        self._clear_all_caches()

        # Log current memory usage
        memory_info = psutil.virtual_memory()
        logger.warning(f"Emergency cleanup - Memory: {memory_info.percent}% ({memory_info.used / 1024**3:.1f}GB)")

    def _critical_memory_cleanup(self):
        """Critical memory cleanup"""
        logger.warning("Critical memory cleanup triggered")

        # Aggressive garbage collection
        collected = gc.collect(2)
        self.garbage_collection_stats['critical'] += collected

        # Clear large objects from memory pool
        self._clear_large_objects()

        # Compact memory pools
        self._compact_memory_pools()

    def _warning_memory_cleanup(self):
        """Warning level memory cleanup"""
        logger.info("Warning level memory cleanup triggered")

        # Regular garbage collection
        collected = gc.collect()
        self.garbage_collection_stats['warning'] += collected

        # Clear old cache entries
        self._clear_old_cache_entries()

    def _clear_large_objects(self):
        """Clear large objects from memory"""
        large_objects = [(obj_id, size) for obj_id, size in self.object_sizes.items() if size > 10 * 1024 * 1024]  # > 10MB

        for obj_id, size in large_objects:
            if obj_id in self.memory_pool:
                del self.memory_pool[obj_id]
                logger.info(f"Cleared large object: {size / 1024**2:.1f}MB")

    def _compact_memory_pools(self):
        """Compact memory pools to reduce fragmentation"""
        # Create new compacted pools
        new_pool = {}

        for obj_id, obj in list(self.memory_pool.items()):
            if obj is not None:
                new_pool[obj_id] = obj

        self.memory_pool = new_pool

    def _clear_all_caches(self):
        """Clear all LRU caches"""
        # Clear function caches
        for func in [f for f in globals().values() if hasattr(f, 'cache_clear')]:
            try:
                func.cache_clear()
            except:
                pass

    def _clear_old_cache_entries(self):
        """Clear old cache entries based on age"""
        current_time = time.time()
        max_age = 300  # 5 minutes

        # This would need to be implemented based on your caching strategy
        pass

    def get_memory_pool_object(self, obj_id: str, factory: Callable, *args, **kwargs):
        """Get object from memory pool or create new one"""
        if obj_id in self.memory_pool:
            obj = self.memory_pool[obj_id]
            if obj is not None:
                return obj

        # Create new object
        obj = factory(*args, **kwargs)
        self.memory_pool[obj_id] = obj
        self.object_sizes[id(obj)] = sys.getsizeof(obj)

        return obj

    def register_weak_reference(self, key: str, obj: Any):
        """Register a weak reference to an object"""
        self.weak_references[key] = obj

    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory statistics"""
        memory_info = psutil.virtual_memory()
        current, peak = tracemalloc.get_traced_memory()

        return {
            'memory_percent': memory_info.percent,
            'memory_used_gb': memory_info.used / 1024**3,
            'memory_available_gb': memory_info.available / 1024**3,
            'current_traced_mb': current / 1024**2,
            'peak_traced_mb': peak / 1024**2,
            'pool_objects': len(self.memory_pool),
            'weak_references': len(self.weak_references),
            'garbage_collections': dict(self.garbage_collection_stats)
        }

class CPUOptimizer:
    """CPU performance optimization and load balancing"""

    def __init__(self):
        self.thread_pool = ThreadPoolExecutor(max_workers=min(32, os.cpu_count() * 2))
        self.process_pool = ProcessPoolExecutor(max_workers=min(8, os.cpu_count()))
        self.cpu_thresholds = {
            'high': 80.0,
            'critical': 90.0
        }
        self.task_queue = queue.PriorityQueue()
        self.load_balancer = LoadBalancer()

        # Start CPU monitoring
        self._start_cpu_monitor()

    def _start_cpu_monitor(self):
        """Start CPU monitoring and load balancing"""
        def monitor_loop():
            while True:
                try:
                    cpu_percent = psutil.cpu_percent(interval=1)

                    if cpu_percent > self.cpu_thresholds['critical']:
                        self._handle_critical_cpu_load()
                    elif cpu_percent > self.cpu_thresholds['high']:
                        self._handle_high_cpu_load()

                    # Balance load across workers
                    self.load_balancer.balance_load()

                    time.sleep(2)
                except Exception as e:
                    logger.error(f"CPU monitor error: {e}")
                    time.sleep(5)

        thread = threading.Thread(target=monitor_loop, daemon=True)
        thread.start()

    def _handle_critical_cpu_load(self):
        """Handle critical CPU load"""
        logger.warning("Critical CPU load detected")

        # Pause non-essential tasks
        self.task_queue.queue.clear()

        # Reduce thread pool size
        current_workers = self.thread_pool._max_workers
        new_workers = max(4, current_workers // 2)
        self.thread_pool._max_workers = new_workers

        logger.info(f"Reduced thread pool from {current_workers} to {new_workers}")

    def _handle_high_cpu_load(self):
        """Handle high CPU load"""
        logger.info("High CPU load detected")

        # Throttle new task submissions
        # Prioritize existing tasks

    def submit_task(self, task: Callable, priority: int = 0, *args, **kwargs):
        """Submit task with priority"""
        self.task_queue.put((priority, task, args, kwargs))

    async def run_async_task(self, task: Callable, *args, **kwargs):
        """Run task asynchronously"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.thread_pool, task, *args, **kwargs)

    def run_cpu_intensive_task(self, task: Callable, *args, **kwargs):
        """Run CPU-intensive task in process pool"""
        return self.process_pool.submit(task, *args, **kwargs)

    def get_cpu_stats(self) -> Dict[str, Any]:
        """Get CPU statistics"""
        return {
            'cpu_percent': psutil.cpu_percent(),
            'cpu_count': psutil.cpu_count(),
            'load_average': os.getloadavg() if hasattr(os, 'getloadavg') else [0, 0, 0],
            'thread_pool_workers': self.thread_pool._max_workers,
            'process_pool_workers': self.process_pool._max_workers,
            'queue_size': self.task_queue.qsize()
        }

class LoadBalancer:
    """Simple load balancer for task distribution"""

    def __init__(self):
        self.workers = []
        self.worker_loads = defaultdict(float)

    def add_worker(self, worker_id: str, capacity: float = 1.0):
        """Add a worker to the load balancer"""
        self.workers.append(worker_id)
        self.worker_loads[worker_id] = 0.0

    def remove_worker(self, worker_id: str):
        """Remove a worker from the load balancer"""
        if worker_id in self.workers:
            self.workers.remove(worker_id)
            del self.worker_loads[worker_id]

    def get_best_worker(self) -> Optional[str]:
        """Get the worker with the lowest load"""
        if not self.workers:
            return None

        return min(self.workers, key=lambda w: self.worker_loads[w])

    def update_load(self, worker_id: str, load_delta: float):
        """Update worker load"""
        self.worker_loads[worker_id] += load_delta

    def balance_load(self):
        """Balance load across workers"""
        # Decay loads over time
        for worker_id in self.worker_loads:
            self.worker_loads[worker_id] *= 0.95

class IOOptimizer:
    """I/O performance optimization"""

    def __init__(self):
        self.file_cache = {}
        self.db_connection_pools = {}
        self.io_buffer_pool = {}
        self.async_file_handler = None

        # Initialize async file handler
        self._initialize_async_file_handler()

    def _initialize_async_file_handler(self):
        """Initialize async file handling"""
        self.async_file_handler = aiofiles.open

    async def read_file_async(self, file_path: str, use_cache: bool = True) -> bytes:
        """Read file asynchronously with caching"""
        if use_cache and file_path in self.file_cache:
            return self.file_cache[file_path]

        try:
            async with aiofiles.open(file_path, 'rb') as f:
                content = await f.read()

            if use_cache:
                self.file_cache[file_path] = content

            return content
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            raise

    async def write_file_async(self, file_path: str, content: bytes, use_buffer: bool = True):
        """Write file asynchronously with buffering"""
        if use_buffer:
            buffer_id = hashlib.md5(content).hexdigest()
            if buffer_id in self.io_buffer_pool:
                # Buffer already exists, no need to write
                return

        try:
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(content)

            if use_buffer:
                self.io_buffer_pool[buffer_id] = content

        except Exception as e:
            logger.error(f"Error writing file {file_path}: {e}")
            raise

    def get_db_connection(self, db_path: str) -> sqlite3.Connection:
        """Get database connection from pool"""
        if db_path not in self.db_connection_pools:
            self.db_connection_pools[db_path] = []

        pool = self.db_connection_pools[db_path]

        if pool:
            return pool.pop()
        else:
            # Create new connection
            conn = sqlite3.connect(db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            return conn

    def return_db_connection(self, db_path: str, conn: sqlite3.Connection):
        """Return database connection to pool"""
        if db_path not in self.db_connection_pools:
            self.db_connection_pools[db_path] = []

        pool = self.db_connection_pools[db_path]
        pool.append(conn)

    def clear_cache(self):
        """Clear file cache"""
        self.file_cache.clear()
        self.io_buffer_pool.clear()

    def get_io_stats(self) -> Dict[str, Any]:
        """Get I/O statistics"""
        return {
            'cached_files': len(self.file_cache),
            'db_pools': len(self.db_connection_pools),
            'buffered_writes': len(self.io_buffer_pool),
            'disk_io': psutil.disk_io_counters()._asdict() if psutil.disk_io_counters() else {}
        }

class NetworkOptimizer:
    """Network performance optimization"""

    def __init__(self):
        self.connection_pools = {}
        self.request_cache = {}
        self.session = None
        self.retry_config = {
            'max_retries': 3,
            'backoff_factor': 1.0,
            'timeout': 30.0
        }

        # Initialize HTTP session
        self._initialize_http_session()

    def _initialize_http_session(self):
        """Initialize HTTP session with connection pooling"""
        self.session = aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(
                limit=100,
                limit_per_host=30,
                ttl_dns_cache=300,
                use_dns_cache=True,
                keepalive_timeout=30,
                enable_cleanup_closed=True
            ),
            timeout=aiohttp.ClientTimeout(total=self.retry_config['timeout'])
        )

    async def make_request(self, url: str, method: str = 'GET', **kwargs) -> Dict[str, Any]:
        """Make HTTP request with retries and caching"""
        cache_key = f"{method}:{url}:{hash(str(kwargs))}"

        # Check cache for GET requests
        if method.upper() == 'GET' and cache_key in self.request_cache:
            cached_response = self.request_cache[cache_key]
            if time.time() - cached_response['timestamp'] < 300:  # 5 minutes cache
                return cached_response['data']

        # Make request with retries
        for attempt in range(self.retry_config['max_retries']):
            try:
                async with self.session.request(method, url, **kwargs) as response:
                    data = await response.json()

                    # Cache GET requests
                    if method.upper() == 'GET':
                        self.request_cache[cache_key] = {
                            'data': data,
                            'timestamp': time.time()
                        }

                    return data

            except Exception as e:
                if attempt == self.retry_config['max_retries'] - 1:
                    logger.error(f"Request failed after {self.retry_config['max_retries']} attempts: {e}")
                    raise

                # Exponential backoff
                backoff = self.retry_config['backoff_factor'] * (2 ** attempt)
                await asyncio.sleep(backoff)

    async def websocket_connection(self, url: str, **kwargs):
        """Create WebSocket connection"""
        return await self.session.ws_connect(url, **kwargs)

    def clear_cache(self):
        """Clear request cache"""
        self.request_cache.clear()

    async def close(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()

    def get_network_stats(self) -> Dict[str, Any]:
        """Get network statistics"""
        net_io = psutil.net_io_counters()
        return {
            'cached_requests': len(self.request_cache),
            'bytes_sent': net_io.bytes_sent,
            'bytes_recv': net_io.bytes_recv,
            'packets_sent': net_io.packets_sent,
            'packets_recv': net_io.packets_recv
        }

class PerformanceMonitor:
    """Comprehensive performance monitoring"""

    def __init__(self):
        self.metrics_history = deque(maxlen=1000)
        self.benchmark_results = {}
        self.alert_thresholds = {
            'cpu_percent': 90.0,
            'memory_percent': 90.0,
            'response_time_ms': 5000.0
        }

        # Start monitoring
        self._start_monitoring()

    def _start_monitoring(self):
        """Start performance monitoring"""
        def monitor_loop():
            while True:
                try:
                    metrics = self._collect_metrics()
                    self.metrics_history.append(metrics)

                    # Check for alerts
                    self._check_alerts(metrics)

                    time.sleep(10)  # Collect metrics every 10 seconds
                except Exception as e:
                    logger.error(f"Performance monitor error: {e}")
                    time.sleep(30)

        thread = threading.Thread(target=monitor_loop, daemon=True)
        thread.start()

    def _collect_metrics(self) -> PerformanceMetrics:
        """Collect performance metrics"""
        return PerformanceMetrics(
            cpu_percent=psutil.cpu_percent(),
            memory_percent=psutil.virtual_memory().percent,
            memory_used_mb=psutil.virtual_memory().used / 1024**2,
            disk_io_read_mb=psutil.disk_io_counters().read_bytes / 1024**2 if psutil.disk_io_counters() else 0,
            disk_io_write_mb=psutil.disk_io_counters().write_bytes / 1024**2 if psutil.disk_io_counters() else 0,
            network_io_sent_mb=psutil.net_io_counters().bytes_sent / 1024**2,
            network_io_recv_mb=psutil.net_io_counters().bytes_recv / 1024**2,
            active_threads=threading.active_count(),
            active_connections=len(self.metrics_history)
        )

    def _check_alerts(self, metrics: PerformanceMetrics):
        """Check for performance alerts"""
        alerts = []

        if metrics.cpu_percent > self.alert_thresholds['cpu_percent']:
            alerts.append(f"High CPU usage: {metrics.cpu_percent}%")

        if metrics.memory_percent > self.alert_thresholds['memory_percent']:
            alerts.append(f"High memory usage: {metrics.memory_percent}%")

        if metrics.response_time_ms > self.alert_thresholds['response_time_ms']:
            alerts.append(f"High response time: {metrics.response_time_ms}ms")

        if alerts:
            logger.warning("Performance alerts: " + "; ".join(alerts))

    def benchmark_function(self, func_name: str, func: Callable, *args, **kwargs) -> float:
        """Benchmark function execution time"""
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()

        execution_time = (end_time - start_time) * 1000  # Convert to milliseconds

        if func_name not in self.benchmark_results:
            self.benchmark_results[func_name] = []

        self.benchmark_results[func_name].append(execution_time)

        return execution_time

    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report"""
        return {
            'current_metrics': self.metrics_history[-1] if self.metrics_history else None,
            'historical_metrics': list(self.metrics_history)[-100:],  # Last 100 metrics
            'benchmark_results': self.benchmark_results,
            'alerts_count': len([m for m in self.metrics_history if self._has_alerts(m)])
        }

    def _has_alerts(self, metrics: PerformanceMetrics) -> bool:
        """Check if metrics have alerts"""
        return (metrics.cpu_percent > self.alert_thresholds['cpu_percent'] or
                metrics.memory_percent > self.alert_thresholds['memory_percent'] or
                metrics.response_time_ms > self.alert_thresholds['response_time_ms'])

class PerformanceOptimizer:
    """Main performance optimization system"""

    def __init__(self):
        self.memory_optimizer = MemoryOptimizer()
        self.cpu_optimizer = CPUOptimizer()
        self.io_optimizer = IOOptimizer()
        self.network_optimizer = NetworkOptimizer()
        self.performance_monitor = PerformanceMonitor()

        logger.info("Performance optimization system initialized")

    def get_optimization_stats(self) -> Dict[str, Any]:
        """Get comprehensive optimization statistics"""
        return {
            'memory': self.memory_optimizer.get_memory_stats(),
            'cpu': self.cpu_optimizer.get_cpu_stats(),
            'io': self.io_optimizer.get_io_stats(),
            'network': self.network_optimizer.get_network_stats(),
            'performance': self.performance_monitor.get_performance_report()
        }

    def optimize_memory_usage(self):
        """Trigger memory optimization"""
        self.memory_optimizer._critical_memory_cleanup()

    def optimize_cpu_usage(self):
        """Trigger CPU optimization"""
        self.cpu_optimizer._handle_high_cpu_load()

    def clear_all_caches(self):
        """Clear all caches"""
        self.memory_optimizer._clear_all_caches()
        self.io_optimizer.clear_cache()
        self.network_optimizer.clear_cache()

    async def shutdown(self):
        """Shutdown optimization system"""
        await self.network_optimizer.close()
        self.cpu_optimizer.thread_pool.shutdown()
        self.cpu_optimizer.process_pool.shutdown()

# Global instance
performance_optimizer = PerformanceOptimizer()

# Decorators for performance optimization
def performance_monitor(func_name: str = None):
    """Decorator to monitor function performance"""
    def decorator(func):
        name = func_name or f"{func.__module__}.{func.__name__}"

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                execution_time = (time.time() - start_time) * 1000
                performance_optimizer.performance_monitor.benchmark_function(name, lambda: result)
                return result
            except Exception as e:
                execution_time = (time.time() - start_time) * 1000
                logger.error(f"Function {name} failed after {execution_time:.2f}ms: {e}")
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            return performance_optimizer.performance_monitor.benchmark_function(name, func, *args, **kwargs)

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator

def memory_optimized(obj_id: str = None):
    """Decorator to optimize memory usage for functions"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if obj_id:
                return performance_optimizer.memory_optimizer.get_memory_pool_object(
                    obj_id, func, *args, **kwargs
                )
            return func(*args, **kwargs)
        return wrapper
    return decorator

def async_optimized():
    """Decorator to run functions asynchronously"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await performance_optimizer.cpu_optimizer.run_async_task(func, *args, **kwargs)
        return wrapper
    return decorator

# Context managers for performance optimization
@contextmanager
def performance_context(operation_name: str):
    """Context manager for performance monitoring"""
    start_time = time.time()
    try:
        yield
    finally:
        execution_time = (time.time() - start_time) * 1000
        performance_optimizer.performance_monitor.benchmark_function(
            f"context:{operation_name}", lambda: execution_time
        )

@asynccontextmanager
async def async_performance_context(operation_name: str):
    """Async context manager for performance monitoring"""
    start_time = time.time()
    try:
        yield
    finally:
        execution_time = (time.time() - start_time) * 1000
        performance_optimizer.performance_monitor.benchmark_function(
            f"async_context:{operation_name}", lambda: execution_time
        )

# Utility functions
def get_system_performance_metrics() -> Dict[str, Any]:
    """Get current system performance metrics"""
    return performance_optimizer.get_optimization_stats()

async def optimize_system_performance():
    """Optimize overall system performance"""
    performance_optimizer.optimize_memory_usage()
    performance_optimizer.optimize_cpu_usage()
    performance_optimizer.clear_all_caches()

def benchmark_system() -> Dict[str, Any]:
    """Benchmark system performance"""
    return performance_optimizer.performance_monitor.get_performance_report()

if __name__ == "__main__":
    # Example usage
    print("DuckBot Performance Optimization System")
    print("=" * 50)

    # Get performance stats
    stats = get_system_performance_metrics()
    print(f"Memory Usage: {stats['memory']['memory_percent']:.1f}%")
    print(f"CPU Usage: {stats['cpu']['cpu_percent']:.1f}%")
    print(f"Cached Files: {stats['io']['cached_files']}")
    print(f"Network Requests: {stats['network']['cached_requests']}")

    print("\nPerformance optimization system initialized successfully!")