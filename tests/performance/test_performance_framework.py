#!/usr/bin/env python3
"""
Performance Testing Framework for DuckBot v4.2
Comprehensive performance testing including load testing, stress testing, and benchmarking
"""

import pytest
import asyncio
import sys
import os
import time
import json
import psutil
import threading
import multiprocessing
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict
from unittest.mock import MagicMock, AsyncMock, patch
import statistics
import tracemalloc
import cProfile
import pstats
import io
import matplotlib.pyplot as plt
import numpy as np
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

@dataclass
class PerformanceMetrics:
    """Performance metrics data structure."""
    operation: str
    execution_time: float
    memory_usage_mb: float
    cpu_usage_percent: float
    timestamp: float
    success: bool
    error_message: Optional[str] = None

@dataclass
class LoadTestResult:
    """Load test results."""
    test_name: str
    concurrent_users: int
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_response_time: float
    min_response_time: float
    max_response_time: float
    p95_response_time: float
    p99_response_time: float
    requests_per_second: float
    error_rate: float
    duration_seconds: float

@dataclass
class BenchmarkResult:
    """Benchmark results."""
    benchmark_name: str
    iterations: int
    average_time: float
    min_time: float
    max_time: float
    std_deviation: float
    total_time: float
    memory_before_mb: float
    memory_after_mb: float
    memory_increase_mb: float

class PerformanceMonitor:
    """Performance monitoring utility."""

    def __init__(self):
        self.metrics_history: List[PerformanceMetrics] = []
        self.process = psutil.Process()
        self.start_memory = None
        self.start_time = None

    def start_monitoring(self):
        """Start performance monitoring."""
        self.start_time = time.time()
        self.start_memory = self.process.memory_info().rss / 1024 / 1024
        tracemalloc.start()

    def stop_monitoring(self, operation: str, success: bool = True, error_message: str = None) -> PerformanceMetrics:
        """Stop performance monitoring and record metrics."""
        end_time = time.time()
        end_memory = self.process.memory_info().rss / 1024 / 1024
        execution_time = end_time - self.start_time
        memory_usage = end_memory - self.start_memory
        cpu_usage = self.process.cpu_percent()

        # Memory tracking
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        metrics = PerformanceMetrics(
            operation=operation,
            execution_time=execution_time,
            memory_usage_mb=memory_usage,
            cpu_usage_percent=cpu_usage,
            timestamp=end_time,
            success=success,
            error_message=error_message
        )

        self.metrics_history.append(metrics)
        return metrics

    def get_system_resources(self) -> Dict[str, float]:
        """Get current system resource usage."""
        return {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage_percent": psutil.disk_usage('/').percent,
            "process_memory_mb": self.process.memory_info().rss / 1024 / 1024,
            "process_cpu_percent": self.process.cpu_percent()
        }

    def generate_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report."""
        if not self.metrics_history:
            return {"error": "No metrics recorded"}

        # Group metrics by operation
        operations = {}
        for metric in self.metrics_history:
            if metric.operation not in operations:
                operations[metric.operation] = []
            operations[metric.operation].append(metric)

        # Calculate statistics for each operation
        report = {
            "summary": {
                "total_operations": len(self.metrics_history),
                "successful_operations": sum(1 for m in self.metrics_history if m.success),
                "failed_operations": sum(1 for m in self.metrics_history if not m.success),
                "total_execution_time": sum(m.execution_time for m in self.metrics_history),
                "average_execution_time": statistics.mean(m.execution_time for m in self.metrics_history),
                "total_memory_usage_mb": sum(m.memory_usage_mb for m in self.metrics_history)
            },
            "operations": {}
        }

        for operation, metrics in operations.items():
            execution_times = [m.execution_time for m in metrics]
            memory_usages = [m.memory_usage_mb for m in metrics]
            cpu_usages = [m.cpu_usage_percent for m in metrics]

            report["operations"][operation] = {
                "count": len(metrics),
                "success_rate": sum(1 for m in metrics if m.success) / len(metrics),
                "average_execution_time": statistics.mean(execution_times),
                "min_execution_time": min(execution_times),
                "max_execution_time": max(execution_times),
                "std_execution_time": statistics.stdev(execution_times) if len(execution_times) > 1 else 0,
                "p95_execution_time": np.percentile(execution_times, 95),
                "p99_execution_time": np.percentile(execution_times, 99),
                "average_memory_usage_mb": statistics.mean(memory_usages),
                "average_cpu_usage_percent": statistics.mean(cpu_usages)
            }

        return report

class LoadTester:
    """Load testing utility."""

    def __init__(self, monitor: PerformanceMonitor):
        self.monitor = monitor

    async def run_load_test(
        self,
        test_name: str,
        target_function: Callable,
        concurrent_users: int,
        requests_per_user: int,
        ramp_up_period: float = 1.0,
        think_time: float = 0.1
    ) -> LoadTestResult:
        """Run a load test."""
        self.monitor.start_monitoring()
        start_time = time.time()
        response_times = []
        successful_requests = 0
        failed_requests = 0
        errors = []

        async def make_requests(user_id: int):
            nonlocal successful_requests, failed_requests
            user_start_time = time.time()

            # Ramp up delay
            if ramp_up_period > 0:
                ramp_delay = (ramp_up_period / concurrent_users) * user_id
                await asyncio.sleep(ramp_delay)

            for request_num in range(requests_per_user):
                request_start_time = time.time()

                try:
                    if asyncio.iscoroutinefunction(target_function):
                        await target_function(user_id, request_num)
                    else:
                        await asyncio.get_event_loop().run_in_executor(
                            None, target_function, user_id, request_num
                        )

                    request_end_time = time.time()
                    response_time = request_end_time - request_start_time
                    response_times.append(response_time)
                    successful_requests += 1

                    # Think time
                    if think_time > 0:
                        await asyncio.sleep(think_time)

                except Exception as e:
                    request_end_time = time.time()
                    response_time = request_end_time - request_start_time
                    response_times.append(response_time)
                    failed_requests += 1
                    errors.append(str(e))

        # Create concurrent users
        tasks = [make_requests(user_id) for user_id in range(concurrent_users)]
        await asyncio.gather(*tasks, return_exceptions=True)

        end_time = time.time()
        total_time = end_time - start_time

        # Calculate statistics
        if response_times:
            avg_response_time = statistics.mean(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
            p95_response_time = np.percentile(response_times, 95)
            p99_response_time = np.percentile(response_times, 99)
        else:
            avg_response_time = min_response_time = max_response_time = p95_response_time = p99_response_time = 0

        requests_per_second = (successful_requests + failed_requests) / total_time
        error_rate = failed_requests / (successful_requests + failed_requests) if (successful_requests + failed_requests) > 0 else 0

        self.monitor.stop_monitoring(f"load_test_{test_name}")

        return LoadTestResult(
            test_name=test_name,
            concurrent_users=concurrent_users,
            total_requests=successful_requests + failed_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            average_response_time=avg_response_time,
            min_response_time=min_response_time,
            max_response_time=max_response_time,
            p95_response_time=p95_response_time,
            p99_response_time=p99_response_time,
            requests_per_second=requests_per_second,
            error_rate=error_rate,
            duration_seconds=total_time
        )

class BenchmarkRunner:
    """Benchmark running utility."""

    def __init__(self, monitor: PerformanceMonitor):
        self.monitor = monitor

    async def run_benchmark(
        self,
        benchmark_name: str,
        target_function: Callable,
        iterations: int = 100,
        warmup_iterations: int = 10
    ) -> BenchmarkResult:
        """Run a benchmark."""
        # Warmup
        for _ in range(warmup_iterations):
            if asyncio.iscoroutinefunction(target_function):
                await target_function()
            else:
                target_function()

        # Benchmark
        execution_times = []
        self.monitor.start_monitoring()
        start_memory = self.monitor.process.memory_info().rss / 1024 / 1024

        start_time = time.time()
        for _ in range(iterations):
            iter_start_time = time.time()

            try:
                if asyncio.iscoroutinefunction(target_function):
                    await target_function()
                else:
                    target_function()

                iter_end_time = time.time()
                execution_times.append(iter_end_time - iter_start_time)

            except Exception as e:
                print(f"Benchmark iteration failed: {e}")
                execution_times.append(float('inf'))  # Mark as failed

        end_time = time.time()
        end_memory = self.monitor.process.memory_info().rss / 1024 / 1024
        total_time = end_time - start_time

        # Filter out failed iterations
        successful_times = [t for t in execution_times if t != float('inf')]
        failed_iterations = len(execution_times) - len(successful_times)

        if successful_times:
            avg_time = statistics.mean(successful_times)
            min_time = min(successful_times)
            max_time = max(successful_times)
            std_dev = statistics.stdev(successful_times) if len(successful_times) > 1 else 0
        else:
            avg_time = min_time = max_time = std_dev = 0

        memory_increase = end_memory - start_memory

        self.monitor.stop_monitoring(f"benchmark_{benchmark_name}")

        return BenchmarkResult(
            benchmark_name=benchmark_name,
            iterations=iterations,
            average_time=avg_time,
            min_time=min_time,
            max_time=max_time,
            std_deviation=std_dev,
            total_time=total_time,
            memory_before_mb=start_memory,
            memory_after_mb=end_memory,
            memory_increase_mb=memory_increase
        )

class StressTester:
    """Stress testing utility."""

    def __init__(self, monitor: PerformanceMonitor):
        self.monitor = monitor

    async def run_stress_test(
        self,
        test_name: str,
        target_function: Callable,
        max_concurrent_users: int,
        test_duration: float,
        user_increment: int = 10,
        increment_interval: float = 30.0
    ) -> Dict[str, Any]:
        """Run a stress test."""
        results = []
        current_users = user_increment
        start_time = time.time()

        while current_users <= max_concurrent_users and (time.time() - start_time) < test_duration:
            print(f"Testing with {current_users} concurrent users...")

            # Run load test for current user count
            load_test_result = await self.run_load_test_at_concurrency(
                target_function, current_users, test_duration=increment_interval
            )

            results.append({
                "concurrent_users": current_users,
                "result": load_test_result,
                "system_resources": self.monitor.get_system_resources()
            })

            # Check if system is under stress
            system_resources = self.monitor.get_system_resources()
            if (system_resources["cpu_percent"] > 90 or
                system_resources["memory_percent"] > 90 or
                load_test_result.error_rate > 0.1):
                print(f"System stress detected at {current_users} users")
                break

            current_users += user_increment

        return {
            "test_name": test_name,
            "max_users_tested": current_users - user_increment,
            "results": results,
            "stress_point": current_users if current_users <= max_concurrent_users else max_concurrent_users
        }

    async def run_load_test_at_concurrency(
        self,
        target_function: Callable,
        concurrent_users: int,
        test_duration: float
    ) -> LoadTestResult:
        """Run a load test at specific concurrency for a duration."""
        response_times = []
        successful_requests = 0
        failed_requests = 0
        start_time = time.time()

        async def user_task(user_id: int):
            nonlocal successful_requests, failed_requests

            while (time.time() - start_time) < test_duration:
                request_start_time = time.time()

                try:
                    if asyncio.iscoroutinefunction(target_function):
                        await target_function(user_id)
                    else:
                        await asyncio.get_event_loop().run_in_executor(
                            None, target_function, user_id
                        )

                    request_end_time = time.time()
                    response_times.append(request_end_time - request_start_time)
                    successful_requests += 1

                except Exception as e:
                    request_end_time = time.time()
                    response_times.append(request_end_time - request_start_time)
                    failed_requests += 1

                # Small delay between requests
                await asyncio.sleep(0.1)

        # Create concurrent users
        tasks = [user_task(user_id) for user_id in range(concurrent_users)]
        await asyncio.gather(*tasks, return_exceptions=True)

        end_time = time.time()
        total_time = end_time - start_time

        # Calculate statistics
        if response_times:
            avg_response_time = statistics.mean(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
            p95_response_time = np.percentile(response_times, 95)
            p99_response_time = np.percentile(response_times, 99)
        else:
            avg_response_time = min_response_time = max_response_time = p95_response_time = p99_response_time = 0

        requests_per_second = (successful_requests + failed_requests) / total_time
        error_rate = failed_requests / (successful_requests + failed_requests) if (successful_requests + failed_requests) > 0 else 0

        return LoadTestResult(
            test_name=f"stress_test_{concurrent_users}_users",
            concurrent_users=concurrent_users,
            total_requests=successful_requests + failed_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            average_response_time=avg_response_time,
            min_response_time=min_response_time,
            max_response_time=max_response_time,
            p95_response_time=p95_response_time,
            p99_response_time=p99_response_time,
            requests_per_second=requests_per_second,
            error_rate=error_rate,
            duration_seconds=total_time
        )

class TestPerformanceFramework:
    """Performance framework tests."""

    @pytest.fixture
    def performance_monitor(self):
        """Create performance monitor instance."""
        return PerformanceMonitor()

    @pytest.fixture
    def load_tester(self, performance_monitor):
        """Create load tester instance."""
        return LoadTester(performance_monitor)

    @pytest.fixture
    def benchmark_runner(self, performance_monitor):
        """Create benchmark runner instance."""
        return BenchmarkRunner(performance_monitor)

    @pytest.fixture
    def stress_tester(self, performance_monitor):
        """Create stress tester instance."""
        return StressTester(performance_monitor)

    @pytest.mark.performance
    def test_performance_monitor_initialization(self, performance_monitor):
        """Test performance monitor initialization."""
        assert performance_monitor is not None
        assert hasattr(performance_monitor, 'metrics_history')
        assert hasattr(performance_monitor, 'process')

    @pytest.mark.performance
    def test_performance_monitoring(self, performance_monitor):
        """Test performance monitoring functionality."""
        def test_function():
            time.sleep(0.1)
            return "test"

        performance_monitor.start_monitoring()
        result = test_function()
        metrics = performance_monitor.stop_monitoring("test_function")

        assert metrics.operation == "test_function"
        assert metrics.execution_time > 0.1
        assert metrics.success is True
        assert result == "test"

    @pytest.mark.performance
    def test_system_resource_monitoring(self, performance_monitor):
        """Test system resource monitoring."""
        resources = performance_monitor.get_system_resources()

        assert "cpu_percent" in resources
        assert "memory_percent" in resources
        assert "disk_usage_percent" in resources
        assert "process_memory_mb" in resources
        assert "process_cpu_percent" in resources

        assert 0 <= resources["cpu_percent"] <= 100
        assert 0 <= resources["memory_percent"] <= 100
        assert 0 <= resources["disk_usage_percent"] <= 100

    @pytest.mark.performance
    def test_performance_report_generation(self, performance_monitor):
        """Test performance report generation."""
        # Add some test metrics
        for i in range(5):
            performance_monitor.metrics_history.append(PerformanceMetrics(
                operation=f"test_operation_{i}",
                execution_time=0.1 + i * 0.01,
                memory_usage_mb=1.0 + i * 0.1,
                cpu_usage_percent=10.0 + i * 2,
                timestamp=time.time(),
                success=True
            ))

        report = performance_monitor.generate_performance_report()

        assert "summary" in report
        assert "operations" in report
        assert report["summary"]["total_operations"] == 5
        assert report["summary"]["successful_operations"] == 5
        assert "test_operation_0" in report["operations"]

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_load_testing(self, load_tester):
        """Test load testing functionality."""
        async def mock_request(user_id: int, request_num: int):
            await asyncio.sleep(0.01)  # Simulate work
            return f"Response for user {user_id}, request {request_num}"

        result = await load_tester.run_load_test(
            test_name="mock_api",
            target_function=mock_request,
            concurrent_users=5,
            requests_per_user=3,
            ramp_up_period=0.5,
            think_time=0.05
        )

        assert result.test_name == "mock_api"
        assert result.concurrent_users == 5
        assert result.total_requests == 15
        assert result.successful_requests > 0
        assert result.average_response_time > 0
        assert result.requests_per_second > 0

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_benchmarking(self, benchmark_runner):
        """Test benchmarking functionality."""
        def mock_function():
            # Simple computation
            return sum(i * i for i in range(100))

        result = await benchmark_runner.run_benchmark(
            benchmark_name="mock_computation",
            target_function=mock_function,
            iterations=50,
            warmup_iterations=5
        )

        assert result.benchmark_name == "mock_computation"
        assert result.iterations == 50
        assert result.average_time > 0
        assert result.min_time > 0
        assert result.max_time > 0
        assert result.total_time > 0
        assert result.memory_increase_mb >= 0

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_stress_testing(self, stress_tester):
        """Test stress testing functionality."""
        async def mock_task(user_id: int):
            await asyncio.sleep(0.001)  # Very short task
            return f"Task {user_id} completed"

        result = await stress_tester.run_stress_test(
            test_name="mock_stress",
            target_function=mock_task,
            max_concurrent_users=20,
            test_duration=10.0,
            user_increment=5,
            increment_interval=2.0
        )

        assert result["test_name"] == "mock_stress"
        assert "max_users_tested" in result
        assert "results" in result
        assert "stress_point" in result
        assert len(result["results"]) > 0

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_concurrent_performance_limits(self, load_tester):
        """Test performance limits under concurrent load."""
        async def cpu_intensive_task(user_id: int, request_num: int):
            # CPU intensive task
            result = 0
            for i in range(100000):
                result += i * i
            return result

        # Test with increasing concurrency
        concurrency_levels = [1, 5, 10, 20]
        results = []

        for concurrency in concurrency_levels:
            result = await load_tester.run_load_test(
                test_name=f"cpu_test_{concurrency}",
                target_function=cpu_intensive_task,
                concurrent_users=concurrency,
                requests_per_user=2,
                ramp_up_period=0.1,
                think_time=0.01
            )
            results.append(result)

        # Verify performance degrades gracefully
        for i, result in enumerate(results):
            assert result.average_response_time > 0
            assert result.error_rate < 0.1  # Less than 10% error rate

    @pytest.mark.performance
    def test_memory_usage_tracking(self, performance_monitor):
        """Test memory usage tracking."""
        def memory_intensive_function():
            # Create some memory usage
            data = [i for i in range(10000)]
            time.sleep(0.01)
            return len(data)

        initial_memory = performance_monitor.process.memory_info().rss / 1024 / 1024

        performance_monitor.start_monitoring()
        result = memory_intensive_function()
        metrics = performance_monitor.stop_monitoring("memory_test")

        final_memory = performance_monitor.process.memory_info().rss / 1024 / 1024

        assert metrics.memory_usage_mb > 0
        assert result == 10000
        assert metrics.operation == "memory_test"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_error_handling_in_performance_tests(self, load_tester):
        """Test error handling in performance tests."""
        async def failing_function(user_id: int, request_num: int):
            if request_num % 3 == 0:  # Fail every 3rd request
                raise Exception("Intentional failure")
            return "Success"

        result = await load_tester.run_load_test(
            test_name="error_test",
            target_function=failing_function,
            concurrent_users=3,
            requests_per_user=3,
            ramp_up_period=0.1,
            think_time=0.01
        )

        # Should have some failures
        assert result.failed_requests > 0
        assert result.error_rate > 0
        assert result.successful_requests > 0

    @pytest.mark.performance
    def test_profiling_integration(self, performance_monitor):
        """Test profiling integration."""
        def profiled_function():
            # Function that will show up in profile
            time.sleep(0.01)
            data = [i ** 2 for i in range(1000)]
            return sum(data)

        # Profile the function
        profiler = cProfile.Profile()
        profiler.enable()

        performance_monitor.start_monitoring()
        result = profiled_function()
        metrics = performance_monitor.stop_monitoring("profiled_test")

        profiler.disable()
        profiler_stats = pstats.Stats(profiler)
        profiler_stats.sort_stats('cumulative')

        # Verify profiling captured the function
        stats_dict = profiler_stats.stats
        function_found = any('profiled_function' in func[0] for func in stats_dict.keys())

        assert function_found
        assert result == sum(i ** 2 for i in range(1000))
        assert metrics.execution_time > 0.01

# Performance test fixtures for different scenarios
class PerformanceTestFixtures:
    """Test fixtures for common performance scenarios."""

    @staticmethod
    async def api_response_simulation(delay: float = 0.01):
        """Simulate API response."""
        await asyncio.sleep(delay)
        return {"status": "success", "data": "test_data"}

    @staticmethod
    async def database_query_simulation(rows: int = 100):
        """Simulate database query."""
        await asyncio.sleep(0.005)
        data = [{"id": i, "value": f"data_{i}"} for i in range(rows)]
        return data

    @staticmethod
    async def file_io_simulation(file_size: int = 1024):
        """Simulate file I/O operations."""
        await asyncio.sleep(0.02)
        data = b"x" * file_size
        return len(data)

    @staticmethod
    async def computation_simulation(iterations: int = 1000):
        """Simulate computational work."""
        result = 0
        for i in range(iterations):
            result += i * i
        return result

    @staticmethod
    async def memory_allocation_simulation(size_mb: int = 1):
        """Simulate memory allocation."""
        data = [0] * (size_mb * 1024 * 256)  # Allocate approximately size_mb MB
        await asyncio.sleep(0.001)
        return len(data)