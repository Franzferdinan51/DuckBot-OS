#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DuckBot v4.2 Performance Profiler
Comprehensive system performance analysis and optimization recommendations
"""

import os
import sys
import time
import json
import threading
import subprocess
import psutil
import sqlite3
import requests
import asyncio
import concurrent.futures
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from contextlib import contextmanager
import tracemalloc
import gc
import socket
import urllib3
from urllib.parse import urlparse
import statistics

# Performance monitoring imports
try:
    import memory_profiler
    MEMORY_PROFILER_AVAILABLE = True
except ImportError:
    MEMORY_PROFILER_AVAILABLE = False

try:
    import pyperf
    PYPERF_AVAILABLE = True
except ImportError:
    PYPERF_AVAILABLE = False

try:
    import matplotlib.pyplot as plt
    import numpy as np
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

# Configure logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('performance_profile.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """Container for performance metrics"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    disk_usage_percent: float
    network_sent_mb: float
    network_recv_mb: float
    process_count: int
    thread_count: int
    load_average: Optional[float] = None

@dataclass
class ServiceMetrics:
    """Service-specific performance metrics"""
    service_name: str
    startup_time: float
    memory_mb: float
    cpu_percent: float
    response_time: float
    health_check_time: float
    status: str
    error_count: int
    restart_count: int

@dataclass
class DatabaseMetrics:
    """Database performance metrics"""
    query_times: List[float]
    connection_time: float
    table_scan_times: Dict[str, float]
    index_usage: Dict[str, float]
    cache_hit_ratio: float

@dataclass
class NetworkMetrics:
    """Network performance metrics"""
    request_times: Dict[str, List[float]]
    bandwidth_mbps: float
    latency_ms: float
    connection_pool_size: int
    timeout_count: int
    error_rate: float

class PerformanceProfiler:
    """Comprehensive performance profiler for DuckBot v4.2"""

    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.results_dir = self.base_dir / "performance_results"
        self.results_dir.mkdir(exist_ok=True)

        # Performance tracking
        self.system_metrics: List[PerformanceMetrics] = []
        self.service_metrics: Dict[str, ServiceMetrics] = {}
        self.database_metrics = DatabaseMetrics([], 0.0, {}, {}, 0.0)
        self.network_metrics = NetworkMetrics({}, 0.0, 0.0, 0, 0, 0.0)

        # Profiling state
        self.profiling_active = False
        self.start_time = None
        self.profile_duration = 300  # 5 minutes default

        # Service detection
        self.known_services = {
            'comfyui': {'port': 8188, 'health_endpoint': 'http://localhost:8188'},
            'n8n': {'port': 5678, 'health_endpoint': 'http://localhost:5678/healthz'},
            'open_notebook': {'port': 8502, 'health_endpoint': 'http://localhost:8502/health'},
            'jupyter': {'port': 8889, 'health_endpoint': 'http://localhost:8889'},
            'open-webui': {'port': 8080, 'health_endpoint': 'http://localhost:8080'},
            'duckbot': {'port': 0, 'health_endpoint': ''}
        }

        # Initialize monitoring
        self.setup_monitoring()

    def setup_monitoring(self):
        """Setup performance monitoring infrastructure"""
        logger.info("Initializing performance monitoring...")

        # Start memory tracing
        tracemalloc.start()

        # Initialize network monitoring
        self.network_stats = psutil.net_io_counters()
        self.network_start_time = time.time()

        # Setup database for storing results
        self.setup_results_database()

        logger.info("Performance monitoring initialized")

    def setup_results_database(self):
        """Setup database for storing performance results"""
        self.db_path = self.results_dir / "performance_results.db"

        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS system_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    cpu_percent REAL,
                    memory_percent REAL,
                    memory_used_mb REAL,
                    disk_usage_percent REAL,
                    network_sent_mb REAL,
                    network_recv_mb REAL,
                    process_count INTEGER,
                    thread_count INTEGER
                )
            ''')

            conn.execute('''
                CREATE TABLE IF NOT EXISTS service_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    service_name TEXT,
                    startup_time REAL,
                    memory_mb REAL,
                    cpu_percent REAL,
                    response_time REAL,
                    health_check_time REAL,
                    status TEXT,
                    error_count INTEGER,
                    restart_count INTEGER
                )
            ''')

            conn.execute('''
                CREATE TABLE IF NOT EXISTS database_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    query_type TEXT,
                    execution_time REAL,
                    success BOOLEAN
                )
            ''')

            conn.execute('''
                CREATE TABLE IF NOT EXISTS network_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    endpoint TEXT,
                    response_time REAL,
                    status_code INTEGER,
                    bandwidth_mbps REAL
                )
            ''')

            conn.commit()

    @contextmanager
    def measure_time(self, operation_name: str):
        """Context manager for measuring operation time"""
        start_time = time.perf_counter()
        yield
        end_time = time.perf_counter()
        execution_time = end_time - start_time
        logger.debug(f"{operation_name} took {execution_time:.4f} seconds")
        return execution_time

    def measure_system_metrics(self) -> PerformanceMetrics:
        """Measure current system performance metrics"""
        with self.measure_time("System metrics collection"):
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)

            # Memory metrics
            memory = psutil.virtual_memory()
            memory_used_mb = memory.used / 1024 / 1024

            # Disk metrics
            disk = psutil.disk_usage('/')

            # Network metrics
            net_io = psutil.net_io_counters()
            network_sent_mb = net_io.bytes_sent / 1024 / 1024
            network_recv_mb = net_io.bytes_recv / 1024 / 1024

            # Process metrics
            process_count = len(psutil.pids())
            current_process = psutil.Process()
            thread_count = current_process.num_threads()

            # Load average (Unix-like systems)
            load_average = None
            if hasattr(psutil, 'getloadavg'):
                load_average = psutil.getloadavg()[0]

            return PerformanceMetrics(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_used_mb=memory_used_mb,
                disk_usage_percent=disk.percent,
                network_sent_mb=network_sent_mb,
                network_recv_mb=network_recv_mb,
                process_count=process_count,
                thread_count=thread_count,
                load_average=load_average
            )

    def measure_service_performance(self, service_name: str) -> Optional[ServiceMetrics]:
        """Measure performance of a specific service"""
        if service_name not in self.known_services:
            logger.warning(f"Unknown service: {service_name}")
            return None

        service_info = self.known_services[service_name]

        try:
            # Check if service is running
            if service_info['port'] > 0:
                health_start = time.perf_counter()
                response = requests.get(service_info['health_endpoint'], timeout=5)
                health_check_time = time.perf_counter() - health_start
                status = "healthy" if response.status_code < 500 else "unhealthy"
            else:
                health_check_time = 0.0
                status = "unknown"

            # Find service process
            service_pid = self.find_service_pid(service_name, service_info['port'])
            if service_pid:
                process = psutil.Process(service_pid)
                memory_mb = process.memory_info().rss / 1024 / 1024
                cpu_percent = process.cpu_percent()
            else:
                memory_mb = 0.0
                cpu_percent = 0.0

            return ServiceMetrics(
                service_name=service_name,
                startup_time=0.0,  # Would need to track actual startup
                memory_mb=memory_mb,
                cpu_percent=cpu_percent,
                response_time=health_check_time,
                health_check_time=health_check_time,
                status=status,
                error_count=0,
                restart_count=0
            )

        except Exception as e:
            logger.error(f"Error measuring {service_name} performance: {e}")
            return None

    def find_service_pid(self, service_name: str, port: int) -> Optional[int]:
        """Find PID of a service by port or process name"""
        try:
            # Method 1: Check by port
            if port > 0:
                for conn in psutil.net_connections():
                    if hasattr(conn, 'laddr') and conn.laddr and conn.laddr.port == port:
                        return conn.pid

            # Method 2: Check by process name
            service_names = {
                'comfyui': ['main.py', 'ComfyUI'],
                'n8n': ['n8n'],
                'open_notebook': ['streamlit', 'python'],
                'jupyter': ['jupyter'],
                'open-webui': ['open-webui'],
                'duckbot': ['DuckBot', 'python']
            }

            if service_name in service_names:
                for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                    try:
                        cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                        for name in service_names[service_name]:
                            if name in proc.info['name'] or name in cmdline:
                                return proc.info['pid']
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue

            return None
        except Exception as e:
            logger.error(f"Error finding service PID: {e}")
            return None

    def measure_database_performance(self) -> DatabaseMetrics:
        """Measure database performance metrics"""
        ecosystem_db = self.base_dir / "core_ai" / "ecosystem_state.db"

        query_times = []
        table_scan_times = {}
        index_usage = {}

        if ecosystem_db.exists():
            try:
                with sqlite3.connect(ecosystem_db) as conn:
                    # Measure various query types
                    queries = [
                        ("SELECT COUNT(*) FROM service_history", "count_query"),
                        ("SELECT * FROM service_history LIMIT 10", "select_query"),
                        ("SELECT service_name, COUNT(*) FROM service_history GROUP BY service_name", "group_query")
                    ]

                    for query, query_type in queries:
                        start_time = time.perf_counter()
                        conn.execute(query)
                        execution_time = time.perf_counter() - start_time
                        query_times.append(execution_time)

                    # Analyze table performance
                    cursor = conn.cursor()
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = [row[0] for row in cursor.fetchall()]

                    for table in tables:
                        start_time = time.perf_counter()
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        table_scan_times[table] = time.perf_counter() - start_time

                    # Get database stats
                    cursor.execute("PRAGMA cache_size")
                    cache_size = cursor.fetchone()[0]

            except Exception as e:
                logger.error(f"Error measuring database performance: {e}")

        return DatabaseMetrics(
            query_times=query_times,
            connection_time=0.0,  # Would need connection pooling
            table_scan_times=table_scan_times,
            index_usage=index_usage,
            cache_hit_ratio=0.0  # Would need more complex analysis
        )

    def measure_network_performance(self) -> NetworkMetrics:
        """Measure network performance metrics"""
        request_times = {}
        bandwidth_mbps = 0.0
        latency_ms = 0.0

        # Test network endpoints
        endpoints = {
            'comfyui': 'http://localhost:8188',
            'n8n': 'http://localhost:5678/healthz',
            'open_notebook': 'http://localhost:8502/health',
            'open-webui': 'http://localhost:8080'
        }

        for service_name, endpoint in endpoints.items():
            try:
                start_time = time.perf_counter()
                response = requests.get(endpoint, timeout=10)
                response_time = time.perf_counter() - start_time

                if service_name not in request_times:
                    request_times[service_name] = []
                request_times[service_name].append(response_time * 1000)  # Convert to ms

            except Exception as e:
                logger.debug(f"Network test failed for {service_name}: {e}")

        # Calculate bandwidth
        try:
            current_net = psutil.net_io_counters()
            time_elapsed = time.time() - self.network_start_time
            if time_elapsed > 0:
                bytes_sent = current_net.bytes_sent - self.network_stats.bytes_sent
                bytes_recv = current_net.bytes_recv - self.network_stats.bytes_recv
                bandwidth_mbps = ((bytes_sent + bytes_recv) / time_elapsed) / (1024 * 1024)
        except Exception as e:
            logger.error(f"Error calculating bandwidth: {e}")

        # Test general network latency
        try:
            latency_start = time.perf_counter()
            socket.create_connection(("8.8.8.8", 53), timeout=5)
            latency_ms = (time.perf_counter() - latency_start) * 1000
        except Exception:
            latency_ms = 0.0

        return NetworkMetrics(
            request_times=request_times,
            bandwidth_mbps=bandwidth_mbps,
            latency_ms=latency_ms,
            connection_pool_size=0,
            timeout_count=0,
            error_rate=0.0
        )

    def detect_memory_leaks(self) -> Dict[str, Any]:
        """Detect potential memory leaks using tracemalloc"""
        if not tracemalloc.is_tracing():
            tracemalloc.start()

        snapshot1 = tracemalloc.take_snapshot()

        # Force garbage collection
        gc.collect()
        time.sleep(1)  # Wait for potential memory cleanup

        snapshot2 = tracemalloc.take_snapshot()

        # Compare snapshots
        top_stats = snapshot2.compare_to(snapshot1, 'lineno')

        leak_indicators = []
        for stat in top_stats[:10]:  # Top 10 memory consumers
            if stat.size_diff > 0:  # Growing memory usage
                leak_indicators.append({
                    'file': str(stat.traceback.format()[-1]) if stat.traceback else 'unknown',
                    'size_diff': stat.size_diff,
                    'count_diff': stat.count_diff
                })

        return {
            'leak_indicators': leak_indicators,
            'total_allocated': sum(stat.size for stat in snapshot2.statistics('lineno')),
            'leak_score': len(leak_indicators) / 10.0  # Simple scoring
        }

    def measure_concurrent_performance(self) -> Dict[str, Any]:
        """Measure concurrent operation performance"""
        results = {
            'thread_performance': [],
            'async_performance': [],
            'contention_issues': []
        }

        # Test thread performance
        def thread_task(task_id: int) -> float:
            start_time = time.perf_counter()
            time.sleep(0.1)  # Simulate work
            # Access shared resource to test contention
            with threading.Lock():
                shared_data = list(range(1000))  # Simulate shared resource access
            return time.perf_counter() - start_time

        # Run concurrent threads
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(thread_task, i) for i in range(20)]
            thread_times = [future.result() for future in concurrent.futures.as_completed(futures)]

        results['thread_performance'] = {
            'avg_time': statistics.mean(thread_times),
            'max_time': max(thread_times),
            'min_time': min(thread_times),
            'std_dev': statistics.stdev(thread_times) if len(thread_times) > 1 else 0
        }

        # Test async performance
        async def async_task(task_id: int) -> float:
            start_time = time.perf_counter()
            await asyncio.sleep(0.1)  # Simulate async work
            return time.perf_counter() - start_time

        async def run_async_tasks():
            tasks = [async_task(i) for i in range(20)]
            return await asyncio.gather(*tasks)

        try:
            loop = asyncio.get_event_loop()
            async_times = loop.run_until_complete(run_async_tasks())
            results['async_performance'] = {
                'avg_time': statistics.mean(async_times),
                'max_time': max(async_times),
                'min_time': min(async_times),
                'std_dev': statistics.stdev(async_times) if len(async_times) > 1 else 0
            }
        except Exception as e:
            logger.error(f"Error in async performance test: {e}")

        return results

    def benchmark_ai_performance(self) -> Dict[str, Any]:
        """Benchmark AI model loading and inference performance"""
        results = {
            'model_load_times': {},
            'inference_times': {},
            'memory_usage': {}
        }

        # Test LM Studio connection if available
        try:
            start_time = time.perf_counter()
            response = requests.get('http://localhost:1234/v1/models', timeout=5)
            model_load_time = time.perf_counter() - start_time

            if response.status_code == 200:
                results['model_load_times']['lm_studio'] = model_load_time

                # Test inference time
                inference_start = time.perf_counter()
                response = requests.post(
                    'http://localhost:1234/v1/chat/completions',
                    json={
                        'model': 'local-model',
                        'messages': [{'role': 'user', 'content': 'Hello'}],
                        'max_tokens': 10
                    },
                    timeout=30
                )
                inference_time = time.perf_counter() - inference_start

                if response.status_code == 200:
                    results['inference_times']['lm_studio'] = inference_time
        except Exception as e:
            logger.debug(f"LM Studio not available: {e}")

        return results

    def measure_websocket_performance(self) -> Dict[str, Any]:
        """Measure WebSocket and real-time communication performance"""
        results = {
            'connection_times': [],
            'message_latency': [],
            'throughput': 0.0,
            'connection_stability': 0.0
        }

        # Test WebSocket connections (basic HTTP fallback for now)
        websocket_endpoints = {
            'comfyui': 'ws://localhost:8188/ws',
            'n8n': 'ws://localhost:5678/ws'
        }

        for service_name, ws_url in websocket_endpoints.items():
            try:
                # For now, test HTTP endpoint as WebSocket fallback
                http_url = ws_url.replace('ws://', 'http://').replace('/ws', '')
                start_time = time.perf_counter()
                response = requests.get(http_url, timeout=5)
                connection_time = time.perf_counter() - start_time

                results['connection_times'].append({
                    'service': service_name,
                    'time': connection_time
                })

            except Exception as e:
                logger.debug(f"WebSocket test failed for {service_name}: {e}")

        return results

    def measure_ui_performance(self) -> Dict[str, Any]:
        """Measure UI rendering and responsiveness performance"""
        results = {
            'webui_load_times': {},
            'rendering_performance': {},
            'interactive_latency': {}
        }

        # Test WebUI loading times
        webui_endpoints = {
            'open-webui': 'http://localhost:8080',
            'n8n': 'http://localhost:5678',
            'open_notebook': 'http://localhost:8502'
        }

        for service_name, url in webui_endpoints.items():
            try:
                start_time = time.perf_counter()
                response = requests.get(url, timeout=10)
                load_time = time.perf_counter() - start_time

                results['webui_load_times'][service_name] = {
                    'load_time': load_time,
                    'status_code': response.status_code,
                    'content_size': len(response.content)
                }

            except Exception as e:
                logger.debug(f"UI performance test failed for {service_name}: {e}")

        return results

    def run_comprehensive_profile(self, duration: int = 300) -> Dict[str, Any]:
        """Run comprehensive performance profile"""
        logger.info(f"Starting comprehensive performance profile for {duration} seconds...")

        self.profiling_active = True
        self.start_time = time.time()

        profile_results = {
            'system_metrics': [],
            'service_metrics': {},
            'database_metrics': {},
            'network_metrics': {},
            'memory_analysis': {},
            'concurrent_performance': {},
            'ai_benchmarks': {},
            'websocket_performance': {},
            'ui_performance': {},
            'bottlenecks': [],
            'recommendations': []
        }

        # Run continuous monitoring
        def monitoring_loop():
            while self.profiling_active and (time.time() - self.start_time) < duration:
                try:
                    # System metrics
                    system_metrics = self.measure_system_metrics()
                    profile_results['system_metrics'].append(asdict(system_metrics))

                    # Service metrics
                    for service_name in self.known_services:
                        service_metrics = self.measure_service_performance(service_name)
                        if service_metrics:
                            if service_name not in profile_results['service_metrics']:
                                profile_results['service_metrics'][service_name] = []
                            profile_results['service_metrics'][service_name].append(asdict(service_metrics))

                    time.sleep(5)  # Collect metrics every 5 seconds

                except Exception as e:
                    logger.error(f"Error in monitoring loop: {e}")
                    time.sleep(5)

        # Start monitoring thread
        monitor_thread = threading.Thread(target=monitoring_loop)
        monitor_thread.start()

        # Run one-time tests
        try:
            logger.info("Running database performance tests...")
            profile_results['database_metrics'] = asdict(self.measure_database_performance())

            logger.info("Running network performance tests...")
            profile_results['network_metrics'] = asdict(self.measure_network_performance())

            logger.info("Running memory leak detection...")
            profile_results['memory_analysis'] = self.detect_memory_leaks()

            logger.info("Running concurrent performance tests...")
            profile_results['concurrent_performance'] = self.measure_concurrent_performance()

            logger.info("Running AI performance benchmarks...")
            profile_results['ai_benchmarks'] = self.benchmark_ai_performance()

            logger.info("Running WebSocket performance tests...")
            profile_results['websocket_performance'] = self.measure_websocket_performance()

            logger.info("Running UI performance tests...")
            profile_results['ui_performance'] = self.measure_ui_performance()

        except Exception as e:
            logger.error(f"Error in performance tests: {e}")

        # Wait for monitoring to complete
        monitor_thread.join()

        # Analyze results and generate recommendations
        profile_results['bottlenecks'] = self.identify_bottlenecks(profile_results)
        profile_results['recommendations'] = self.generate_recommendations(profile_results)

        logger.info("Performance profiling completed")
        return profile_results

    def identify_bottlenecks(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify performance bottlenecks from profiling results"""
        bottlenecks = []

        # System bottlenecks
        if results['system_metrics']:
            cpu_values = [m['cpu_percent'] for m in results['system_metrics']]
            memory_values = [m['memory_percent'] for m in results['system_metrics']]

            if cpu_values and statistics.mean(cpu_values) > 80:
                bottlenecks.append({
                    'type': 'cpu',
                    'severity': 'high' if statistics.mean(cpu_values) > 90 else 'medium',
                    'description': f'High CPU usage: {statistics.mean(cpu_values):.1f}% average',
                    'impact': 'system_responsiveness'
                })

            if memory_values and statistics.mean(memory_values) > 85:
                bottlenecks.append({
                    'type': 'memory',
                    'severity': 'high' if statistics.mean(memory_values) > 95 else 'medium',
                    'description': f'High memory usage: {statistics.mean(memory_values):.1f}% average',
                    'impact': 'system_stability'
                })

        # Network bottlenecks
        if results['network_metrics']:
            network_data = results['network_metrics']
            if network_data.get('latency_ms', 0) > 100:
                bottlenecks.append({
                    'type': 'network',
                    'severity': 'medium',
                    'description': f'High network latency: {network_data["latency_ms"]:.1f}ms',
                    'impact': 'service_responsiveness'
                })

        # Memory leaks
        if results['memory_analysis'].get('leak_score', 0) > 0.3:
            bottlenecks.append({
                'type': 'memory_leak',
                'severity': 'high',
                'description': 'Potential memory leaks detected',
                'impact': 'long_term_stability'
            })

        # Service bottlenecks
        for service_name, metrics_list in results['service_metrics'].items():
            if metrics_list:
                response_times = [m['response_time'] for m in metrics_list if m['response_time'] > 0]
                if response_times and statistics.mean(response_times) > 2.0:
                    bottlenecks.append({
                        'type': 'service',
                        'service': service_name,
                        'severity': 'medium',
                        'description': f'{service_name} has slow response times: {statistics.mean(response_times):.2f}s average',
                        'impact': 'user_experience'
                    })

        return bottlenecks

    def generate_recommendations(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate optimization recommendations based on profiling results"""
        recommendations = []

        # CPU optimization
        if results['system_metrics']:
            cpu_values = [m['cpu_percent'] for m in results['system_metrics']]
            if cpu_values and statistics.mean(cpu_values) > 70:
                recommendations.append({
                    'category': 'cpu_optimization',
                    'priority': 'high',
                    'title': 'Reduce CPU Usage',
                    'description': 'High CPU usage detected. Consider implementing CPU optimization strategies.',
                    'actions': [
                        'Implement request caching for frequently accessed data',
                        'Use async/await patterns for I/O operations',
                        'Optimize database queries with proper indexing',
                        'Consider load balancing for high-traffic services'
                    ]
                })

        # Memory optimization
        if results['memory_analysis'].get('leak_score', 0) > 0.1:
            recommendations.append({
                'category': 'memory_optimization',
                'priority': 'high',
                'title': 'Fix Memory Leaks',
                'description': 'Memory leaks detected that could lead to system instability.',
                'actions': [
                    'Implement proper resource cleanup using context managers',
                    'Add memory profiling to identify leak sources',
                    'Use object pooling for frequently created objects',
                    'Implement periodic garbage collection'
                ]
            })

        # Network optimization
        if results['network_metrics']:
            network_data = results['network_metrics']
            if network_data.get('latency_ms', 0) > 50:
                recommendations.append({
                    'category': 'network_optimization',
                    'priority': 'medium',
                    'title': 'Reduce Network Latency',
                    'description': 'High network latency affecting service responsiveness.',
                    'actions': [
                        'Implement request compression',
                        'Use connection pooling for HTTP requests',
                        'Add CDN for static assets',
                        'Optimize API response sizes'
                    ]
                })

        # Database optimization
        if results['database_metrics']:
            db_data = results['database_metrics']
            if db_data.get('query_times', []):
                avg_query_time = statistics.mean(db_data['query_times'])
                if avg_query_time > 0.1:
                    recommendations.append({
                        'category': 'database_optimization',
                        'priority': 'medium',
                        'title': 'Optimize Database Performance',
                        'description': 'Slow database queries detected.',
                        'actions': [
                            'Add proper database indexes',
                            'Implement query result caching',
                            'Use connection pooling',
                            'Optimize complex queries with proper joins'
                        ]
                    })

        # Service-specific optimizations
        for service_name, metrics_list in results['service_metrics'].items():
            if metrics_list:
                memory_values = [m['memory_mb'] for m in metrics_list if m['memory_mb'] > 0]
                if memory_values and statistics.mean(memory_values) > 1000:  # > 1GB
                    recommendations.append({
                        'category': 'service_optimization',
                        'priority': 'medium',
                        'title': f'Optimize {service_name} Memory Usage',
                        'description': f'{service_name} is using excessive memory: {statistics.mean(memory_values):.1f}MB average',
                        'actions': [
                            f'Implement memory pooling for {service_name}',
                            f'Add memory usage monitoring for {service_name}',
                            f'Consider container resource limits for {service_name}'
                        ]
                    })

        return recommendations

    def save_results(self, results: Dict[str, Any], filename: str = None):
        """Save profiling results to file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"performance_profile_{timestamp}.json"

        filepath = self.results_dir / filename

        # Convert datetime objects to strings for JSON serialization
        def datetime_converter(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2, default=datetime_converter)

        logger.info(f"Performance results saved to {filepath}")
        return filepath

    def generate_report(self, results: Dict[str, Any]) -> str:
        """Generate human-readable performance report"""
        report = []
        report.append("=" * 80)
        report.append("DUCKBOT v4.2 PERFORMANCE PROFILE REPORT")
        report.append("=" * 80)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")

        # Executive Summary
        report.append("EXECUTIVE SUMMARY")
        report.append("-" * 40)
        report.append(f"Bottlenecks Identified: {len(results['bottlenecks'])}")
        report.append(f"Recommendations Generated: {len(results['recommendations'])}")
        report.append("")

        # System Overview
        if results['system_metrics']:
            cpu_values = [m['cpu_percent'] for m in results['system_metrics']]
            memory_values = [m['memory_percent'] for m in results['system_metrics']]

            report.append("SYSTEM PERFORMANCE")
            report.append("-" * 40)
            report.append(f"Average CPU Usage: {statistics.mean(cpu_values):.1f}%")
            report.append(f"Average Memory Usage: {statistics.mean(memory_values):.1f}%")
            report.append(f"Peak CPU Usage: {max(cpu_values):.1f}%")
            report.append(f"Peak Memory Usage: {max(memory_values):.1f}%")
            report.append("")

        # Bottlenecks
        if results['bottlenecks']:
            report.append("IDENTIFIED BOTTLENECKS")
            report.append("-" * 40)
            for bottleneck in results['bottlenecks']:
                severity_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(bottleneck['severity'], "⚪")
                report.append(f"{severity_emoji} {bottleneck['type'].upper()}: {bottleneck['description']}")
            report.append("")

        # Recommendations
        if results['recommendations']:
            report.append("OPTIMIZATION RECOMMENDATIONS")
            report.append("-" * 40)
            for rec in results['recommendations']:
                priority_emoji = {"high": "🔥", "medium": "⚡", "low": "💡"}.get(rec['priority'], "📝")
                report.append(f"{priority_emoji} {rec['title']} ({rec['priority']} priority)")
                report.append(f"   {rec['description']}")
                report.append("")

        # Service Performance
        if results['service_metrics']:
            report.append("SERVICE PERFORMANCE")
            report.append("-" * 40)
            for service_name, metrics_list in results['service_metrics'].items():
                if metrics_list:
                    response_times = [m['response_time'] for m in metrics_list if m['response_time'] > 0]
                    memory_values = [m['memory_mb'] for m in metrics_list if m['memory_mb'] > 0]

                    if response_times:
                        report.append(f"{service_name}:")
                        report.append(f"  Avg Response Time: {statistics.mean(response_times):.3f}s")
                        report.append(f"  Avg Memory Usage: {statistics.mean(memory_values):.1f}MB")
            report.append("")

        report.append("=" * 80)
        return "\n".join(report)

def main():
    """Main execution function"""
    profiler = PerformanceProfiler()

    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description="DuckBot Performance Profiler")
    parser.add_argument("--duration", type=int, default=300, help="Profile duration in seconds")
    parser.add_argument("--output", help="Output filename for results")
    parser.add_argument("--report", action="store_true", help="Generate human-readable report")
    args = parser.parse_args()

    try:
        # Run comprehensive profile
        logger.info(f"Starting performance profiling for {args.duration} seconds...")
        results = profiler.run_comprehensive_profile(duration=args.duration)

        # Save results
        results_file = profiler.save_results(results, args.output)

        # Generate report if requested
        if args.report:
            report = profiler.generate_report(results)
            report_file = str(results_file).replace('.json', '_report.txt')
            with open(report_file, 'w') as f:
                f.write(report)
            logger.info(f"Performance report generated: {report_file}")
            print("\n" + report)

        logger.info("Performance profiling completed successfully")

    except KeyboardInterrupt:
        logger.info("Performance profiling interrupted by user")
    except Exception as e:
        logger.error(f"Performance profiling failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()