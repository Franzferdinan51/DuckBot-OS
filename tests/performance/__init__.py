"""
Performance Tests for DuckBot v4.2

This package contains performance and load testing utilities:
- Benchmark tests for critical functions
- Load testing with concurrent users
- Memory and CPU profiling
- Response time analysis
- Scalability testing
- Performance regression detection
"""

import pytest
import asyncio
import time
import psutil
import tracemalloc
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from pathlib import Path
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Performance test configuration
PERFORMANCE_CONFIG = {
    "benchmark_min_rounds": 10,
    "benchmark_max_time": 30.0,
    "load_test_duration": 60,  # seconds
    "concurrent_users": 50,
    "max_response_time": 2.0,  # seconds
    "memory_threshold_mb": 512,
    "cpu_threshold_percent": 80,
    "error_rate_threshold": 0.05  # 5%
}

@dataclass
class PerformanceMetrics:
    """Performance metrics data class"""
    operation: str
    execution_time: float
    memory_usage_mb: float
    cpu_usage_percent: float
    success: bool
    error_message: Optional[str] = None
    timestamp: float = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()

class PerformanceBenchmark:
    """Performance benchmarking utilities"""

    def __init__(self):
        self.results: List[PerformanceMetrics] = []
        self.baseline: Dict[str, float] = {}

    def set_baseline(self, operation: str, baseline_time: float):
        """Set baseline performance for an operation"""
        self.baseline[operation] = baseline_time

    def benchmark_function(self, func, *args, **kwargs) -> PerformanceMetrics:
        """Benchmark a single function execution"""
        # Start memory tracking
        tracemalloc.start()
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        start_cpu = psutil.Process().cpu_percent()

        # Execute function
        result = None
        success = True
        error_message = None

        try:
            if asyncio.iscoroutinefunction(func):
                # For async functions, run in event loop
                loop = asyncio.get_event_loop()
                result = loop.run_until_complete(func(*args, **kwargs))
            else:
                result = func(*args, **kwargs)
        except Exception as e:
            success = False
            error_message = str(e)

        # Calculate metrics
        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        end_cpu = psutil.Process().cpu_percent()

        execution_time = end_time - start_time
        memory_usage = end_memory - start_memory
        cpu_usage = end_cpu - start_cpu

        # Stop memory tracking
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        metrics = PerformanceMetrics(
            operation=func.__name__,
            execution_time=execution_time,
            memory_usage_mb=memory_usage,
            cpu_usage_percent=cpu_usage,
            success=success,
            error_message=error_message
        )

        self.results.append(metrics)
        return metrics

    def benchmark_multiple_runs(self, func, runs: int = 10, *args, **kwargs) -> Dict[str, Any]:
        """Benchmark function multiple times and return statistics"""
        metrics_list = []

        for i in range(runs):
            metrics = self.benchmark_function(func, *args, **kwargs)
            metrics_list.append(metrics)

        # Calculate statistics
        execution_times = [m.execution_time for m in metrics_list if m.success]
        memory_usages = [m.memory_usage_mb for m in metrics_list if m.success]

        stats = {
            "operation": func.__name__,
            "total_runs": runs,
            "successful_runs": len(execution_times),
            "failed_runs": runs - len(execution_times),
            "avg_execution_time": sum(execution_times) / len(execution_times) if execution_times else 0,
            "min_execution_time": min(execution_times) if execution_times else 0,
            "max_execution_time": max(execution_times) if execution_times else 0,
            "avg_memory_usage": sum(memory_usages) / len(memory_usages) if memory_usages else 0,
            "success_rate": len(execution_times) / runs,
            "baseline_comparison": None
        }

        # Compare with baseline if available
        if func.__name__ in self.baseline:
            baseline_time = self.baseline[func.__name__]
            improvement = ((baseline_time - stats["avg_execution_time"]) / baseline_time) * 100
            stats["baseline_comparison"] = {
                "baseline_time": baseline_time,
                "improvement_percent": improvement,
                "status": "improved" if improvement > 0 else "degraded" if improvement < -5 else "stable"
            }

        return stats

    def get_summary(self) -> Dict[str, Any]:
        """Get performance summary"""
        if not self.results:
            return {"total_operations": 0}

        # Group by operation
        operations = {}
        for metric in self.results:
            op_name = metric.operation
            if op_name not in operations:
                operations[op_name] = []
            operations[op_name].append(metric)

        summary = {
            "total_operations": len(self.results),
            "operations": {},
            "threshold_violations": []
        }

        # Calculate statistics for each operation
        for op_name, metrics in operations.items():
            successful_metrics = [m for m in metrics if m.success]
            if successful_metrics:
                execution_times = [m.execution_time for m in successful_metrics]
                memory_usages = [m.memory_usage_mb for m in successful_metrics]

                summary["operations"][op_name] = {
                    "count": len(metrics),
                    "success_count": len(successful_metrics),
                    "success_rate": len(successful_metrics) / len(metrics),
                    "avg_execution_time": sum(execution_times) / len(execution_times),
                    "max_execution_time": max(execution_times),
                    "avg_memory_usage": sum(memory_usages) / len(memory_usages) if memory_usages else 0,
                    "max_memory_usage": max(memory_usages) if memory_usages else 0
                }

                # Check thresholds
                if summary["operations"][op_name]["avg_execution_time"] > PERFORMANCE_CONFIG["max_response_time"]:
                    summary["threshold_violations"].append({
                        "operation": op_name,
                        "type": "response_time",
                        "value": summary["operations"][op_name]["avg_execution_time"],
                        "threshold": PERFORMANCE_CONFIG["max_response_time"]
                    })

                if summary["operations"][op_name]["avg_memory_usage"] > PERFORMANCE_CONFIG["memory_threshold_mb"]:
                    summary["threshold_violations"].append({
                        "operation": op_name,
                        "type": "memory_usage",
                        "value": summary["operations"][op_name]["avg_memory_usage"],
                        "threshold": PERFORMANCE_CONFIG["memory_threshold_mb"]
                    })

        return summary

class LoadTester:
    """Load testing utilities"""

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.results = []

    async def run_load_test(self, concurrent_users: int, duration: int, requests_per_second: int) -> Dict[str, Any]:
        """Run load test with specified parameters"""
        print(f"[LOAD TEST] Starting: {concurrent_users} concurrent users, {duration}s duration, {requests_per_second} req/s")

        start_time = time.time()
        tasks = []

        # Create user simulation tasks
        for user_id in range(concurrent_users):
            task = self._simulate_user(user_id, duration, requests_per_second // concurrent_users)
            tasks.append(task)

        # Run all users concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        end_time = time.time()

        # Process results
        successful_results = [r for r in results if isinstance(r, dict) and r.get("success")]
        failed_results = [r for r in results if isinstance(r, dict) and not r.get("success")]

        total_duration = end_time - start_time
        total_requests = len(successful_results) + len(failed_results)

        summary = {
            "test_duration": total_duration,
            "concurrent_users": concurrent_users,
            "target_requests_per_second": requests_per_second,
            "actual_requests_per_second": total_requests / total_duration if total_duration > 0 else 0,
            "total_requests": total_requests,
            "successful_requests": len(successful_results),
            "failed_requests": len(failed_results),
            "success_rate": len(successful_results) / total_requests if total_requests > 0 else 0,
            "error_rate": len(failed_results) / total_requests if total_requests > 0 else 0,
            "average_response_time": sum(r["response_time"] for r in successful_results) / len(successful_results) if successful_results else 0,
            "min_response_time": min(r["response_time"] for r in successful_results) if successful_results else 0,
            "max_response_time": max(r["response_time"] for r in successful_results) if successful_results else 0,
            "response_time_percentiles": self._calculate_percentiles([r["response_time"] for r in successful_results]),
            "throughput": total_requests / total_duration if total_duration > 0 else 0
        }

        self.results.append(summary)
        return summary

    async def _simulate_user(self, user_id: int, duration: int, requests_per_second: float):
        """Simulate a single user making requests"""
        end_time = time.time() + duration
        request_interval = 1.0 / requests_per_second if requests_per_second > 0 else 1.0
        user_results = []

        while time.time() < end_time:
            start_time = time.time()

            # Make request
            result = await self._make_request(user_id)
            user_results.append(result)

            # Calculate sleep time to maintain request rate
            request_duration = time.time() - start_time
            sleep_time = max(0, request_interval - request_duration)

            await asyncio.sleep(sleep_time)

        return user_results

    async def _make_request(self, user_id: int) -> Dict[str, Any]:
        """Make a single request"""
        start_time = time.time()

        try:
            # Import httpx here to avoid import issues in non-test environments
            import httpx

            async with httpx.AsyncClient(timeout=PERFORMANCE_CONFIG["max_response_time"]) as client:
                response = await client.get(f"{self.base_url}/health")

            return {
                "user_id": user_id,
                "success": response.status_code == 200,
                "status_code": response.status_code,
                "response_time": time.time() - start_time,
                "timestamp": time.time()
            }
        except Exception as e:
            return {
                "user_id": user_id,
                "success": False,
                "error": str(e),
                "response_time": time.time() - start_time,
                "timestamp": time.time()
            }

    def _calculate_percentiles(self, values: List[float]) -> Dict[str, float]:
        """Calculate percentiles for response times"""
        if not values:
            return {}

        sorted_values = sorted(values)
        n = len(sorted_values)

        return {
            "p50": sorted_values[int(n * 0.5)],
            "p90": sorted_values[int(n * 0.9)],
            "p95": sorted_values[int(n * 0.95)],
            "p99": sorted_values[int(n * 0.99)]
        }

    def get_load_test_summary(self) -> Dict[str, Any]:
        """Get summary of all load tests"""
        if not self.results:
            return {"total_tests": 0}

        return {
            "total_tests": len(self.results),
            "tests": self.results,
            "aggregate": self._calculate_aggregate_metrics()
        }

    def _calculate_aggregate_metrics(self) -> Dict[str, Any]:
        """Calculate aggregate metrics across all load tests"""
        if not self.results:
            return {}

        all_response_times = []
        total_requests = 0
        total_successful = 0

        for test in self.results:
            all_response_times.extend([r["response_time"] for r in test.get("user_results", []) if r.get("success")])
            total_requests += test["total_requests"]
            total_successful += test["successful_requests"]

        return {
            "overall_success_rate": total_successful / total_requests if total_requests > 0 else 0,
            "overall_avg_response_time": sum(all_response_times) / len(all_response_times) if all_response_times else 0,
            "overall_throughput": sum(test["throughput"] for test in self.results) / len(self.results)
        }

class MemoryProfiler:
    """Memory profiling utilities"""

    def __init__(self):
        self.snapshots = []

    def take_snapshot(self, name: str):
        """Take memory snapshot"""
        import tracemalloc
        import gc

        gc.collect()  # Force garbage collection
        snapshot = tracemalloc.take_snapshot()
        self.snapshots.append({"name": name, "snapshot": snapshot, "timestamp": time.time()})

    def compare_snapshots(self, snapshot1_name: str, snapshot2_name: str) -> Dict[str, Any]:
        """Compare two memory snapshots"""
        snapshot1 = next((s for s in self.snapshots if s["name"] == snapshot1_name), None)
        snapshot2 = next((s for s in self.snapshots if s["name"] == snapshot2_name), None)

        if not snapshot1 or not snapshot2:
            raise ValueError("One or both snapshots not found")

        top_stats = snapshot2["snapshot"].compare_to(snapshot1["snapshot"], 'lineno')

        return {
            "snapshot1_name": snapshot1_name,
            "snapshot2_name": snapshot2_name,
            "timestamp1": snapshot1["timestamp"],
            "timestamp2": snapshot2["timestamp"],
            "time_diff": snapshot2["timestamp"] - snapshot1["timestamp"],
            "top_differences": [
                {
                    "file": stat.traceback.format()[-1] if stat.traceback else "unknown",
                    "line": stat.traceback.format()[-2] if stat.traceback else "unknown",
                    "size_diff": stat.size_diff,
                    "count_diff": stat.count_diff
                }
                for stat in top_stats[:10]  # Top 10 differences
            ]
        }

    def get_memory_usage_trend(self) -> Dict[str, Any]:
        """Get memory usage trend over time"""
        if len(self.snapshots) < 2:
            return {"error": "Need at least 2 snapshots for trend analysis"}

        trends = []
        for i in range(1, len(self.snapshots)):
            prev = self.snapshots[i-1]
            curr = self.snapshots[i]

            trends.append({
                "from_name": prev["name"],
                "to_name": curr["name"],
                "time_diff": curr["timestamp"] - prev["timestamp"],
                "memory_diff": self._calculate_total_memory(curr["snapshot"]) - self._calculate_total_memory(prev["snapshot"])
            })

        return {
            "snapshots_count": len(self.snapshots),
            "trends": trends,
            "total_memory_growth": sum(t["memory_diff"] for t in trends)
        }

    def _calculate_total_memory(self, snapshot) -> int:
        """Calculate total memory usage from snapshot"""
        return sum(stat.size for stat in snapshot.statistics('lineno'))

# Performance test fixtures
@pytest.fixture(scope="session")
def performance_benchmark():
    """Provide performance benchmark utility"""
    return PerformanceBenchmark()

@pytest.fixture(scope="session")
def load_tester():
    """Provide load tester utility"""
    return LoadTester("http://localhost:8787")

@pytest.fixture(scope="session")
def memory_profiler():
    """Provide memory profiler utility"""
    return MemoryProfiler()

# Export utilities
__all__ = [
    "PerformanceBenchmark",
    "LoadTester",
    "MemoryProfiler",
    "PerformanceMetrics",
    "PERFORMANCE_CONFIG"
]