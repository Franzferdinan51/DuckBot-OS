#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DuckBot v4.2 AI and WebSocket Performance Analyzer
Detailed analysis of AI model performance, WebSocket communication, and real-time features
"""

import os
import sys
import time
import json
import asyncio
import requests
import threading
import subprocess
import psutil
import socket
import websockets
import concurrent.futures
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, asdict
from contextlib import contextmanager, asynccontextmanager
import statistics
import gc
import tracemalloc

# Configure logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ai_websocket_performance.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class AIModelMetrics:
    """AI model performance metrics"""
    model_name: str
    load_time: float
    inference_times: List[float]
    memory_usage_mb: float
    cpu_usage_percent: float
    throughput_requests_per_sec: float
    error_rate: float
    token_generation_speed: float

@dataclass
class WebSocketMetrics:
    """WebSocket performance metrics"""
    endpoint: str
    connection_time: float
    message_latency: List[float]
    throughput_messages_per_sec: float
    connection_stability: float
    error_count: int
    bandwidth_mbps: float

@dataclass
class RealTimeMetrics:
    """Real-time communication metrics"""
    service_name: str
    response_time_p50: float
    response_time_p95: float
    response_time_p99: float
    availability_percent: float
    concurrent_users_supported: int
    message_loss_rate: float

class AIWebSocketPerformanceAnalyzer:
    """Analyzer for AI model and WebSocket performance in DuckBot"""

    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.results_dir = self.base_dir / "ai_websocket_analysis"
        self.results_dir.mkdir(exist_ok=True)

        # AI model endpoints
        self.ai_endpoints = {
            'lm_studio': {
                'url': 'http://localhost:1234/v1',
                'models_endpoint': '/models',
                'chat_endpoint': '/chat/completions',
                'expected_load_time': 5.0,
                'expected_inference_time': 2.0
            },
            'openai': {
                'url': 'https://api.openai.com/v1',
                'models_endpoint': '/models',
                'chat_endpoint': '/chat/completions',
                'expected_load_time': 1.0,
                'expected_inference_time': 5.0
            },
            'anthropic': {
                'url': 'https://api.anthropic.com/v1',
                'models_endpoint': '/models',
                'chat_endpoint': '/messages',
                'expected_load_time': 1.0,
                'expected_inference_time': 3.0
            }
        }

        # WebSocket endpoints
        self.websocket_endpoints = {
            'comfyui': 'ws://localhost:8188/ws',
            'n8n': 'ws://localhost:5678/ws',
            'custom': 'ws://localhost:8788/ws'
        }

        # Performance tracking
        self.ai_metrics: Dict[str, AIModelMetrics] = {}
        self.websocket_metrics: Dict[str, WebSocketMetrics] = {}
        self.realtime_metrics: Dict[str, RealTimeMetrics] = {}

        # Test configurations
        self.test_messages = [
            "Hello, how are you?",
            "What is the capital of France?",
            "Explain quantum computing in simple terms.",
            "Write a Python function to calculate factorial.",
            "What are the benefits of meditation?"
        ]

        # Initialize monitoring
        self.setup_monitoring()

    def setup_monitoring(self):
        """Setup performance monitoring infrastructure"""
        logger.info("Initializing AI and WebSocket performance monitoring...")

        # Start memory tracing
        tracemalloc.start()

        # Setup results storage
        self.setup_results_database()

        logger.info("AI and WebSocket performance monitoring initialized")

    def setup_results_database(self):
        """Setup database for storing performance results"""
        self.db_path = self.results_dir / "ai_websocket_results.db"

        import sqlite3
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS ai_model_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    model_name TEXT,
                    load_time REAL,
                    inference_time REAL,
                    memory_usage_mb REAL,
                    cpu_usage_percent REAL,
                    success BOOLEAN
                )
            ''')

            conn.execute('''
                CREATE TABLE IF NOT EXISTS websocket_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    endpoint TEXT,
                    connection_time REAL,
                    message_latency REAL,
                    throughput REAL,
                    error_count INTEGER
                )
            ''')

            conn.execute('''
                CREATE TABLE IF NOT EXISTS realtime_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    service_name TEXT,
                    response_time REAL,
                    availability REAL,
                    concurrent_users INTEGER
                )
            ''')

            conn.commit()

    @contextmanager
    def measure_time(self, operation_name: str):
        """Context manager for measuring operation time"""
        start_time = time.perf_counter()
        yield start_time
        end_time = time.perf_counter()
        execution_time = end_time - start_time
        logger.debug(f"{operation_name} took {execution_time:.4f} seconds")
        return execution_time

    def measure_memory_usage(self, process_id: int = 0) -> float:
        """Measure memory usage of a process or current process"""
        try:
            if process_id > 0:
                process = psutil.Process(process_id)
                return process.memory_info().rss / 1024 / 1024  # MB
            else:
                # Current process
                process = psutil.Process()
                return process.memory_info().rss / 1024 / 1024  # MB
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return 0.0

    def benchmark_ai_model(self, model_provider: str) -> AIModelMetrics:
        """Benchmark AI model loading and inference performance"""
        logger.info(f"Benchmarking {model_provider} AI model...")

        if model_provider not in self.ai_endpoints:
            logger.error(f"Unknown AI provider: {model_provider}")
            return AIModelMetrics(
                model_name=model_provider,
                load_time=0.0,
                inference_times=[],
                memory_usage_mb=0.0,
                cpu_usage_percent=0.0,
                throughput_requests_per_sec=0.0,
                error_rate=100.0,
                token_generation_speed=0.0
            )

        endpoint_config = self.ai_endpoints[model_provider]
        base_url = endpoint_config['url']

        # Test model loading (list available models)
        with self.measure_time(f"{model_provider}_model_loading") as load_start:
            try:
                response = requests.get(
                    f"{base_url}{endpoint_config['models_endpoint']}",
                    timeout=30
                )
                load_time = time.perf_counter() - load_start

                if response.status_code != 200:
                    logger.error(f"Failed to load {model_provider} models: {response.status_code}")
                    return AIModelMetrics(
                        model_name=model_provider,
                        load_time=load_time,
                        inference_times=[],
                        memory_usage_mb=0.0,
                        cpu_usage_percent=0.0,
                        throughput_requests_per_sec=0.0,
                        error_rate=100.0,
                        token_generation_speed=0.0
                    )

                logger.info(f"Successfully loaded {model_provider} models in {load_time:.2f}s")

            except Exception as e:
                logger.error(f"Error loading {model_provider} models: {e}")
                load_time = time.perf_counter() - load_start
                return AIModelMetrics(
                    model_name=model_provider,
                    load_time=load_time,
                    inference_times=[],
                    memory_usage_mb=0.0,
                    cpu_usage_percent=0.0,
                    throughput_requests_per_sec=0.0,
                    error_rate=100.0,
                    token_generation_speed=0.0
                )

        # Test inference performance
        inference_times = []
        error_count = 0
        total_tokens = 0

        for i, message in enumerate(self.test_messages[:3]):  # Test first 3 messages
            try:
                with self.measure_time(f"{model_provider}_inference_{i}") as inference_start:
                    if model_provider == 'lm_studio':
                        response = requests.post(
                            f"{base_url}{endpoint_config['chat_endpoint']}",
                            json={
                                'model': 'local-model',
                                'messages': [{'role': 'user', 'content': message}],
                                'max_tokens': 50,
                                'temperature': 0.7
                            },
                            timeout=30
                        )
                    elif model_provider == 'openai':
                        # Note: Requires API key
                        response = requests.post(
                            f"{base_url}{endpoint_config['chat_endpoint']}",
                            json={
                                'model': 'gpt-3.5-turbo',
                                'messages': [{'role': 'user', 'content': message}],
                                'max_tokens': 50,
                                'temperature': 0.7
                            },
                            timeout=30
                        )
                    else:
                        # Anthropic
                        response = requests.post(
                            f"{base_url}{endpoint_config['chat_endpoint']}",
                            json={
                                'model': 'claude-3-sonnet-20240229',
                                'max_tokens': 50,
                                'messages': [{'role': 'user', 'content': message}]
                            },
                            timeout=30
                        )

                    inference_time = time.perf_counter() - inference_start

                    if response.status_code == 200:
                        inference_times.append(inference_time)
                        # Estimate token count (rough approximation)
                        if 'choices' in response.json():
                            content = response.json()['choices'][0]['message']['content']
                            total_tokens += len(content.split())
                    else:
                        error_count += 1
                        logger.warning(f"Inference failed for {model_provider}: {response.status_code}")

            except Exception as e:
                error_count += 1
                logger.error(f"Error during {model_provider} inference: {e}")

        # Calculate metrics
        if inference_times:
            avg_inference_time = statistics.mean(inference_times)
            throughput = len(inference_times) / sum(inference_times) if sum(inference_times) > 0 else 0
            error_rate = (error_count / len(self.test_messages[:3])) * 100
            token_speed = total_tokens / sum(inference_times) if sum(inference_times) > 0 else 0
        else:
            avg_inference_time = 0.0
            throughput = 0.0
            error_rate = 100.0
            token_speed = 0.0

        # Measure resource usage
        memory_usage = self.measure_memory_usage()
        cpu_usage = psutil.cpu_percent(interval=1)

        return AIModelMetrics(
            model_name=model_provider,
            load_time=load_time,
            inference_times=inference_times,
            memory_usage_mb=memory_usage,
            cpu_usage_percent=cpu_usage,
            throughput_requests_per_sec=throughput,
            error_rate=error_rate,
            token_generation_speed=token_speed
        )

    async def test_websocket_connection(self, endpoint: str) -> WebSocketMetrics:
        """Test WebSocket connection performance"""
        logger.info(f"Testing WebSocket connection to {endpoint}...")

        connection_times = []
        message_latencies = []
        error_count = 0
        messages_sent = 0

        try:
            # Test connection establishment
            for _ in range(3):  # Try 3 connections
                try:
                    start_time = time.perf_counter()
                    async with websockets.connect(endpoint, timeout=10) as websocket:
                        connection_time = time.perf_counter() - start_time
                        connection_times.append(connection_time)

                        # Test message round-trip time
                        for i in range(5):  # Send 5 test messages
                            test_message = f"Test message {i}"
                            send_start = time.perf_counter()
                            await websocket.send(test_message)
                            response = await asyncio.wait_for(websocket.recv(), timeout=5)
                            receive_time = time.perf_counter() - send_start
                            message_latencies.append(receive_time)
                            messages_sent += 1

                except Exception as e:
                    error_count += 1
                    logger.warning(f"WebSocket connection failed: {e}")

        except Exception as e:
            logger.error(f"WebSocket test failed for {endpoint}: {e}")
            error_count += 1

        # Calculate metrics
        if connection_times:
            avg_connection_time = statistics.mean(connection_times)
        else:
            avg_connection_time = 0.0

        if message_latencies:
            avg_latency = statistics.mean(message_latencies)
            throughput = messages_sent / sum(message_latencies) if sum(message_latencies) > 0 else 0
            bandwidth = (messages_sent * 1024) / sum(message_latencies) / (1024 * 1024)  # Mbps (rough estimate)
        else:
            avg_latency = 0.0
            throughput = 0.0
            bandwidth = 0.0

        # Calculate connection stability
        stability = len(connection_times) / 3  # Success rate out of 3 attempts

        return WebSocketMetrics(
            endpoint=endpoint,
            connection_time=avg_connection_time,
            message_latency=message_latencies,
            throughput_messages_per_sec=throughput,
            connection_stability=stability,
            error_count=error_count,
            bandwidth_mbps=bandwidth
        )

    def test_real_time_performance(self, service_name: str, endpoint: str) -> RealTimeMetrics:
        """Test real-time performance for various services"""
        logger.info(f"Testing real-time performance for {service_name}...")

        response_times = []
        availability_tests = 100  # Number of availability tests
        successful_requests = 0

        # Test response times
        for i in range(20):  # 20 test requests
            try:
                start_time = time.perf_counter()
                response = requests.get(endpoint, timeout=10)
                response_time = time.perf_counter() - start_time

                if response.status_code == 200:
                    response_times.append(response_time)
                    successful_requests += 1
                else:
                    logger.warning(f"HTTP error for {service_name}: {response.status_code}")

            except Exception as e:
                logger.debug(f"Request failed for {service_name}: {e}")

        # Test availability
        for i in range(availability_tests):
            try:
                response = requests.get(endpoint, timeout=5)
                if response.status_code == 200:
                    successful_requests += 1
            except:
                pass

        # Calculate percentiles
        if response_times:
            sorted_times = sorted(response_times)
            p50 = sorted_times[len(sorted_times) // 2]
            p95 = sorted_times[int(len(sorted_times) * 0.95)] if len(sorted_times) > 20 else sorted_times[-1]
            p99 = sorted_times[int(len(sorted_times) * 0.99)] if len(sorted_times) > 100 else sorted_times[-1]
        else:
            p50 = p95 = p99 = 0.0

        # Calculate availability
        availability = (successful_requests / (20 + availability_tests)) * 100

        # Estimate concurrent users (rough estimate based on response time)
        if p50 > 0:
            concurrent_users = int(1000 / p50)  # Rough estimate
        else:
            concurrent_users = 0

        # Message loss rate (for WebSocket services)
        message_loss_rate = 0.0  # Would need actual WebSocket testing

        return RealTimeMetrics(
            service_name=service_name,
            response_time_p50=p50,
            response_time_p95=p95,
            response_time_p99=p99,
            availability_percent=availability,
            concurrent_users_supported=concurrent_users,
            message_loss_rate=message_loss_rate
        )

    def benchmark_concurrent_ai_requests(self, model_provider: str) -> Dict[str, Any]:
        """Benchmark concurrent AI request handling"""
        logger.info(f"Benchmarking concurrent requests for {model_provider}...")

        if model_provider not in self.ai_endpoints:
            return {}

        endpoint_config = self.ai_endpoints[model_provider]
        base_url = endpoint_config['url']

        async def make_request(session, request_id: int):
            """Make a single AI request"""
            try:
                start_time = time.perf_counter()
                async with session.post(
                    f"{base_url}{endpoint_config['chat_endpoint']}",
                    json={
                        'model': 'local-model' if model_provider == 'lm_studio' else 'gpt-3.5-turbo',
                        'messages': [{'role': 'user', 'content': f'Concurrent test message {request_id}'}],
                        'max_tokens': 30,
                        'temperature': 0.7
                    },
                    timeout=30
                ) as response:
                    response_time = time.perf_counter() - start_time
                    return {
                        'request_id': request_id,
                        'response_time': response_time,
                        'success': response.status == 200
                    }
            except Exception as e:
                return {
                    'request_id': request_id,
                    'response_time': 0.0,
                    'success': False,
                    'error': str(e)
                }

        async def run_concurrent_test(num_concurrent: int):
            """Run concurrent request test"""
            import aiohttp

            async with aiohttp.ClientSession() as session:
                tasks = [make_request(session, i) for i in range(num_concurrent)]
                results = await asyncio.gather(*tasks, return_exceptions=True)

            successful_requests = [r for r in results if isinstance(r, dict) and r.get('success', False)]
            failed_requests = [r for r in results if isinstance(r, dict) and not r.get('success', False)]

            return {
                'total_requests': num_concurrent,
                'successful_requests': len(successful_requests),
                'failed_requests': len(failed_requests),
                'success_rate': len(successful_requests) / num_concurrent * 100,
                'avg_response_time': statistics.mean([r['response_time'] for r in successful_requests]) if successful_requests else 0,
                'max_response_time': max([r['response_time'] for r in successful_requests]) if successful_requests else 0,
                'min_response_time': min([r['response_time'] for r in successful_requests]) if successful_requests else 0
            }

        # Test different concurrency levels
        concurrency_levels = [1, 5, 10, 20, 50]
        concurrent_results = {}

        for level in concurrency_levels:
            try:
                logger.info(f"Testing {level} concurrent requests...")
                result = asyncio.run(run_concurrent_test(level))
                concurrent_results[level] = result
            except Exception as e:
                logger.error(f"Concurrent test failed for level {level}: {e}")
                concurrent_results[level] = {
                    'total_requests': level,
                    'successful_requests': 0,
                    'failed_requests': level,
                    'success_rate': 0,
                    'error': str(e)
                }

        return concurrent_results

    def analyze_memory_efficiency(self) -> Dict[str, Any]:
        """Analyze memory efficiency and garbage collection"""
        logger.info("Analyzing memory efficiency...")

        # Force garbage collection
        gc.collect()

        # Take memory snapshot
        snapshot1 = tracemalloc.take_snapshot()

        # Create some memory pressure
        large_objects = []
        for i in range(100):
            large_objects.append(list(range(10000)))

        # Force garbage collection again
        gc.collect()

        # Take second snapshot
        snapshot2 = tracemalloc.take_snapshot()

        # Clean up
        del large_objects
        gc.collect()

        # Take final snapshot
        snapshot3 = tracemalloc.take_snapshot()

        # Compare snapshots
        top_stats = snapshot2.compare_to(snapshot1, 'lineno')
        cleanup_stats = snapshot3.compare_to(snapshot2, 'lineno')

        return {
            'memory_pressure_top_consumers': [
                {
                    'file': str(stat.traceback.format()[-1]) if stat.traceback else 'unknown',
                    'size_diff': stat.size_diff,
                    'count_diff': stat.count_diff
                }
                for stat in top_stats[:5]
            ],
            'cleanup_efficiency': [
                {
                    'file': str(stat.traceback.format()[-1]) if stat.traceback else 'unknown',
                    'size_diff': stat.size_diff,
                    'count_diff': stat.count_diff
                }
                for stat in cleanup_stats[:5] if stat.size_diff < 0
            ],
            'total_allocated_before': sum(stat.size for stat in snapshot1.statistics('lineno')),
            'total_allocated_pressure': sum(stat.size for stat in snapshot2.statistics('lineno')),
            'total_allocated_after': sum(stat.size for stat in snapshot3.statistics('lineno')),
            'garbage_collection_efficiency': len([stat for stat in cleanup_stats if stat.size_diff < 0]) / len(cleanup_stats) if cleanup_stats else 0
        }

    def run_comprehensive_analysis(self) -> Dict[str, Any]:
        """Run comprehensive AI and WebSocket performance analysis"""
        logger.info("Starting comprehensive AI and WebSocket performance analysis...")

        analysis_results = {
            'timestamp': datetime.now().isoformat(),
            'system_info': {},
            'ai_model_performance': {},
            'websocket_performance': {},
            'realtime_performance': {},
            'concurrent_performance': {},
            'memory_efficiency': {},
            'bottlenecks': [],
            'optimization_recommendations': []
        }

        # Capture system info
        analysis_results['system_info'] = {
            'platform': sys.platform,
            'python_version': sys.version,
            'cpu_count': psutil.cpu_count(),
            'memory_total_gb': psutil.virtual_memory().total / (1024**3),
            'network_connections': len(psutil.net_connections())
        }

        # Benchmark AI models
        logger.info("Benchmarking AI models...")
        ai_providers = ['lm_studio']  # Start with local model

        for provider in ai_providers:
            try:
                metrics = self.benchmark_ai_model(provider)
                analysis_results['ai_model_performance'][provider] = asdict(metrics)
            except Exception as e:
                logger.error(f"Error benchmarking {provider}: {e}")

        # Test WebSocket connections
        logger.info("Testing WebSocket connections...")
        for endpoint_name, endpoint_url in self.websocket_endpoints.items():
            try:
                # Test WebSocket if available
                metrics = asyncio.run(self.test_websocket_connection(endpoint_url))
                analysis_results['websocket_performance'][endpoint_name] = asdict(metrics)
            except Exception as e:
                logger.warning(f"WebSocket test failed for {endpoint_name}: {e}")

        # Test real-time performance
        logger.info("Testing real-time performance...")
        realtime_services = {
            'comfyui': 'http://localhost:8188',
            'n8n': 'http://localhost:5678/healthz',
            'open_notebook': 'http://localhost:8502/health'
        }

        for service_name, endpoint in realtime_services.items():
            try:
                metrics = self.test_real_time_performance(service_name, endpoint)
                analysis_results['realtime_performance'][service_name] = asdict(metrics)
            except Exception as e:
                logger.warning(f"Real-time test failed for {service_name}: {e}")

        # Benchmark concurrent performance
        logger.info("Benchmarking concurrent performance...")
        for provider in ai_providers:
            try:
                concurrent_results = self.benchmark_concurrent_ai_requests(provider)
                analysis_results['concurrent_performance'][provider] = concurrent_results
            except Exception as e:
                logger.warning(f"Concurrent test failed for {provider}: {e}")

        # Analyze memory efficiency
        logger.info("Analyzing memory efficiency...")
        analysis_results['memory_efficiency'] = self.analyze_memory_efficiency()

        # Identify bottlenecks
        analysis_results['bottlenecks'] = self.identify_ai_websocket_bottlenecks(analysis_results)

        # Generate recommendations
        analysis_results['optimization_recommendations'] = self.generate_ai_websocket_recommendations(analysis_results)

        logger.info("Comprehensive AI and WebSocket analysis completed")
        return analysis_results

    def identify_ai_websocket_bottlenecks(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify AI and WebSocket performance bottlenecks"""
        bottlenecks = []

        # AI model bottlenecks
        ai_performance = results.get('ai_model_performance', {})
        for model_name, metrics in ai_performance.items():
            if isinstance(metrics, dict):
                load_time = metrics.get('load_time', 0)
                inference_times = metrics.get('inference_times', [])
                error_rate = metrics.get('error_rate', 0)

                if load_time > 10.0:  # > 10 seconds to load
                    bottlenecks.append({
                        'type': 'ai_model_load_time',
                        'model': model_name,
                        'severity': 'high',
                        'description': f'{model_name} model takes {load_time:.2f}s to load',
                        'impact': 'startup_performance'
                    })

                if inference_times and statistics.mean(inference_times) > 5.0:  # > 5 seconds average inference
                    bottlenecks.append({
                        'type': 'ai_inference_time',
                        'model': model_name,
                        'severity': 'high',
                        'description': f'{model_name} inference is slow: {statistics.mean(inference_times):.2f}s average',
                        'impact': 'user_experience'
                    })

                if error_rate > 10.0:  # > 10% error rate
                    bottlenecks.append({
                        'type': 'ai_reliability',
                        'model': model_name,
                        'severity': 'high',
                        'description': f'{model_name} has high error rate: {error_rate:.1f}%',
                        'impact': 'service_reliability'
                    })

        # WebSocket bottlenecks
        websocket_perf = results.get('websocket_performance', {})
        for endpoint, metrics in websocket_perf.items():
            if isinstance(metrics, dict):
                connection_time = metrics.get('connection_time', 0)
                message_latencies = metrics.get('message_latency', [])
                stability = metrics.get('connection_stability', 0)

                if connection_time > 2.0:  # > 2 seconds to connect
                    bottlenecks.append({
                        'type': 'websocket_connection_time',
                        'endpoint': endpoint,
                        'severity': 'medium',
                        'description': f'WebSocket connection to {endpoint} is slow: {connection_time:.2f}s',
                        'impact': 'real_time_performance'
                    })

                if message_latencies and statistics.mean(message_latencies) > 1.0:  # > 1 second message latency
                    bottlenecks.append({
                        'type': 'websocket_message_latency',
                        'endpoint': endpoint,
                        'severity': 'high',
                        'description': f'WebSocket message latency for {endpoint} is high: {statistics.mean(message_latencies):.3f}s',
                        'impact': 'real_time_responsiveness'
                    })

                if stability < 0.8:  # < 80% connection success rate
                    bottlenecks.append({
                        'type': 'websocket_reliability',
                        'endpoint': endpoint,
                        'severity': 'high',
                        'description': f'WebSocket connection to {endpoint} is unreliable: {stability*100:.1f}% success rate',
                        'impact': 'service_availability'
                    })

        # Real-time performance bottlenecks
        realtime_perf = results.get('realtime_performance', {})
        for service_name, metrics in realtime_perf.items():
            if isinstance(metrics, dict):
                p95_response = metrics.get('response_time_p95', 0)
                availability = metrics.get('availability_percent', 0)

                if p95_response > 2.0:  # > 2 seconds 95th percentile
                    bottlenecks.append({
                        'type': 'realtime_response_time',
                        'service': service_name,
                        'severity': 'medium',
                        'description': f'{service_name} has high P95 response time: {p95_response:.3f}s',
                        'impact': 'user_experience'
                    })

                if availability < 95.0:  # < 95% availability
                    bottlenecks.append({
                        'type': 'realtime_availability',
                        'service': service_name,
                        'severity': 'high',
                        'description': f'{service_name} has low availability: {availability:.1f}%',
                        'impact': 'service_reliability'
                    })

        # Memory efficiency bottlenecks
        memory_eff = results.get('memory_efficiency', {})
        gc_efficiency = memory_eff.get('garbage_collection_efficiency', 0)

        if gc_efficiency < 0.5:  # < 50% garbage collection efficiency
            bottlenecks.append({
                'type': 'memory_efficiency',
                'severity': 'medium',
                'description': f'Poor garbage collection efficiency: {gc_efficiency*100:.1f}%',
                'impact': 'long_term_performance'
            })

        return bottlenecks

    def generate_ai_websocket_recommendations(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate optimization recommendations for AI and WebSocket performance"""
        recommendations = []

        # AI model optimizations
        ai_performance = results.get('ai_model_performance', {})
        for model_name, metrics in ai_performance.items():
            if isinstance(metrics, dict):
                load_time = metrics.get('load_time', 0)
                inference_times = metrics.get('inference_times', [])

                if load_time > 5.0:
                    recommendations.append({
                        'category': 'ai_optimization',
                        'priority': 'high',
                        'title': f'Optimize {model_name} model loading',
                        'description': f'{model_name} model takes {load_time:.2f}s to load, affecting startup performance.',
                        'actions': [
                            f'Implement model pre-loading for {model_name}',
                            f'Use model quantization to reduce {model_name} size',
                            f'Add model caching to avoid repeated loading',
                            f'Consider using smaller variants of {model_name} for faster startup'
                        ]
                    })

                if inference_times and statistics.mean(inference_times) > 2.0:
                    recommendations.append({
                        'category': 'ai_optimization',
                        'priority': 'high',
                        'title': f'Improve {model_name} inference speed',
                        'description': f'{model_name} inference is averaging {statistics.mean(inference_times):.2f}s.',
                        'actions': [
                            f'Implement request batching for {model_name}',
                            f'Use model optimization techniques (quantization, pruning)',
                            f'Add response caching for common queries',
                            f'Consider using GPU acceleration for {model_name}'
                        ]
                    })

        # WebSocket optimizations
        websocket_perf = results.get('websocket_performance', {})
        for endpoint, metrics in websocket_perf.items():
            if isinstance(metrics, dict):
                connection_time = metrics.get('connection_time', 0)
                message_latencies = metrics.get('message_latency', [])

                if connection_time > 1.0:
                    recommendations.append({
                        'category': 'websocket_optimization',
                        'priority': 'medium',
                        'title': f'Optimize WebSocket connection to {endpoint}',
                        'description': f'WebSocket connection time is {connection_time:.3f}s.',
                        'actions': [
                            'Implement WebSocket connection pooling',
                            'Use connection keep-alive mechanisms',
                            'Optimize WebSocket handshake process',
                            'Consider using WebSockets with fallback to HTTP long polling'
                        ]
                    })

                if message_latencies and statistics.mean(message_latencies) > 0.5:
                    recommendations.append({
                        'category': 'websocket_optimization',
                        'priority': 'high',
                        'title': f'Reduce WebSocket message latency for {endpoint}',
                        'description': f'WebSocket message latency is {statistics.mean(message_latencies):.3f}s.',
                        'actions': [
                            'Implement message compression',
                            'Use binary protocols instead of text',
                            'Optimize message serialization/deserialization',
                            'Consider using message batching for high-frequency updates'
                        ]
                    })

        # Concurrent performance optimizations
        concurrent_perf = results.get('concurrent_performance', {})
        for model_name, concurrency_results in concurrent_perf.items():
            if isinstance(concurrency_results, dict):
                # Check if performance degrades at high concurrency
                high_concurrency_results = concurrency_results.get(50, {})
                low_concurrency_results = concurrency_results.get(1, {})

                if (high_concurrency_results.get('success_rate', 0) < 90 or
                    high_concurrency_results.get('avg_response_time', 0) > low_concurrency_results.get('avg_response_time', 0) * 2):

                    recommendations.append({
                        'category': 'concurrent_optimization',
                        'priority': 'high',
                        'title': f'Improve {model_name} concurrent performance',
                        'description': f'{model_name} performance degrades under high concurrency.',
                        'actions': [
                            f'Implement request queuing for {model_name}',
                            f'Add rate limiting and load balancing',
                            f'Use async/await patterns for concurrent requests',
                            f'Consider implementing request timeouts and retries'
                        ]
                    })

        # Memory efficiency optimizations
        memory_eff = results.get('memory_efficiency', {})
        gc_efficiency = memory_eff.get('garbage_collection_efficiency', 0)

        if gc_efficiency < 0.7:
            recommendations.append({
                'category': 'memory_optimization',
                'priority': 'medium',
                'title': 'Improve memory management',
                'description': f'Garbage collection efficiency is {gc_efficiency*100:.1f}%.',
                'actions': [
                    'Implement object pooling for frequently created objects',
                    'Use context managers for proper resource cleanup',
                    'Add memory usage monitoring and alerts',
                            'Consider using weak references for large objects'
                        ]
                    })

        return recommendations

    def save_results(self, results: Dict[str, Any], filename: str = None) -> str:
        """Save analysis results to file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ai_websocket_analysis_{timestamp}.json"

        filepath = self.results_dir / filename

        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2, default=str)

        logger.info(f"AI and WebSocket analysis results saved to {filepath}")
        return str(filepath)

    def generate_report(self, results: Dict[str, Any]) -> str:
        """Generate human-readable AI and WebSocket performance report"""
        report = []
        report.append("=" * 80)
        report.append("DUCKBOT v4.2 AI AND WEBSOCKET PERFORMANCE ANALYSIS REPORT")
        report.append("=" * 80)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")

        # System Information
        sys_info = results.get('system_info', {})
        report.append("SYSTEM INFORMATION")
        report.append("-" * 40)
        report.append(f"Platform: {sys_info.get('platform', 'Unknown')}")
        report.append(f"CPU Cores: {sys_info.get('cpu_count', 'Unknown')}")
        report.append(f"Total Memory: {sys_info.get('memory_total_gb', 0):.1f} GB")
        report.append(f"Network Connections: {sys_info.get('network_connections', 0)}")
        report.append("")

        # AI Model Performance
        report.append("AI MODEL PERFORMANCE")
        report.append("-" * 40)
        ai_performance = results.get('ai_model_performance', {})

        for model_name, metrics in ai_performance.items():
            if isinstance(metrics, dict):
                load_time = metrics.get('load_time', 0)
                inference_times = metrics.get('inference_times', [])
                error_rate = metrics.get('error_rate', 0)
                throughput = metrics.get('throughput_requests_per_sec', 0)

                report.append(f"{model_name}:")
                report.append(f"  Load Time: {load_time:.3f}s")
                if inference_times:
                    report.append(f"  Avg Inference Time: {statistics.mean(inference_times):.3f}s")
                    report.append(f"  Inference P95: {statistics.quantiles(inference_times, n=20)[18] if len(inference_times) >= 20 else max(inference_times):.3f}s")
                report.append(f"  Error Rate: {error_rate:.1f}%")
                report.append(f"  Throughput: {throughput:.2f} req/s")
                report.append("")

        # WebSocket Performance
        report.append("WEBSOCKET PERFORMANCE")
        report.append("-" * 40)
        websocket_perf = results.get('websocket_performance', {})

        for endpoint, metrics in websocket_perf.items():
            if isinstance(metrics, dict):
                connection_time = metrics.get('connection_time', 0)
                message_latencies = metrics.get('message_latency', [])
                stability = metrics.get('connection_stability', 0)

                report.append(f"{endpoint}:")
                report.append(f"  Connection Time: {connection_time:.3f}s")
                if message_latencies:
                    report.append(f"  Avg Message Latency: {statistics.mean(message_latencies):.3f}s")
                report.append(f"  Connection Stability: {stability*100:.1f}%")
                report.append("")

        # Real-time Performance
        report.append("REAL-TIME PERFORMANCE")
        report.append("-" * 40)
        realtime_perf = results.get('realtime_performance', {})

        for service_name, metrics in realtime_perf.items():
            if isinstance(metrics, dict):
                p50 = metrics.get('response_time_p50', 0)
                p95 = metrics.get('response_time_p95', 0)
                availability = metrics.get('availability_percent', 0)

                report.append(f"{service_name}:")
                report.append(f"  P50 Response Time: {p50:.3f}s")
                report.append(f"  P95 Response Time: {p95:.3f}s")
                report.append(f"  Availability: {availability:.1f}%")
                report.append("")

        # Bottlenecks
        bottlenecks = results.get('bottlenecks', [])
        if bottlenecks:
            report.append("IDENTIFIED BOTTLENECKS")
            report.append("-" * 40)
            for bottleneck in bottlenecks:
                severity_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(bottleneck.get('severity', 'low'), "⚪")
                report.append(f"{severity_emoji} {bottleneck.get('type', 'Unknown').upper()}: {bottleneck.get('description', 'No description')}")
            report.append("")

        # Recommendations
        recommendations = results.get('optimization_recommendations', [])
        if recommendations:
            report.append("OPTIMIZATION RECOMMENDATIONS")
            report.append("-" * 40)
            for rec in recommendations:
                priority_emoji = {"high": "🔥", "medium": "⚡", "low": "💡"}.get(rec.get('priority', 'low'), "📝")
                report.append(f"{priority_emoji} {rec.get('title', 'No title')} ({rec.get('priority', 'low')} priority)")
                report.append(f"   {rec.get('description', 'No description')}")
                report.append("")

        # Performance Summary
        report.append("PERFORMANCE SUMMARY")
        report.append("-" * 40)

        # Calculate overall AI performance score
        ai_scores = []
        for model_name, metrics in ai_performance.items():
            if isinstance(metrics, dict):
                load_time = metrics.get('load_time', 0)
                inference_times = metrics.get('inference_times', [])
                error_rate = metrics.get('error_rate', 0)

                # Simple scoring (lower is better)
                load_score = min(100, (load_time / 10.0) * 100)
                inference_score = min(100, (statistics.mean(inference_times) / 5.0) * 100) if inference_times else 100
                error_score = error_rate

                overall_score = (load_score + inference_score + error_score) / 3
                ai_scores.append(overall_score)

        if ai_scores:
            avg_ai_score = statistics.mean(ai_scores)
            report.append(f"Average AI Performance Score: {100 - avg_ai_score:.1f}/100")
        else:
            report.append("No AI models tested")

        # Calculate WebSocket performance score
        websocket_scores = []
        for endpoint, metrics in websocket_perf.items():
            if isinstance(metrics, dict):
                connection_time = metrics.get('connection_time', 0)
                stability = metrics.get('connection_stability', 0)

                connection_score = min(100, (connection_time / 2.0) * 100)
                stability_score = (1 - stability) * 100

                overall_score = (connection_score + stability_score) / 2
                websocket_scores.append(overall_score)

        if websocket_scores:
            avg_websocket_score = statistics.mean(websocket_scores)
            report.append(f"Average WebSocket Performance Score: {100 - avg_websocket_score:.1f}/100")
        else:
            report.append("No WebSocket endpoints tested")

        report.append("")
        report.append("=" * 80)

        return "\n".join(report)

def main():
    """Main execution function"""
    analyzer = AIWebSocketPerformanceAnalyzer()

    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description="DuckBot AI and WebSocket Performance Analyzer")
    parser.add_argument("--output", help="Output filename for results")
    parser.add_argument("--report", action="store_true", help="Generate human-readable report")
    args = parser.parse_args()

    try:
        # Run comprehensive analysis
        logger.info("Starting comprehensive AI and WebSocket performance analysis...")
        results = analyzer.run_comprehensive_analysis()

        # Save results
        results_file = analyzer.save_results(results, args.output)

        # Generate report if requested
        if args.report:
            report = analyzer.generate_report(results)
            report_file = str(results_file).replace('.json', '_report.txt')
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report)
            logger.info(f"AI and WebSocket analysis report generated: {report_file}")
            print("\n" + report)

        logger.info("AI and WebSocket performance analysis completed successfully")

    except KeyboardInterrupt:
        logger.info("AI and WebSocket performance analysis interrupted by user")
    except Exception as e:
        logger.error(f"AI and WebSocket performance analysis failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()