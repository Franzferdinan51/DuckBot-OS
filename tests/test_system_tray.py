#!/usr/bin/env python3
"""
Test script for the enhanced SystemTray component functionality.
This script validates the system metrics API and component behavior.
"""

import asyncio
import aiohttp
import json
import time
import logging
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SystemTrayTester:
    """Test suite for SystemTray component functionality"""

    def __init__(self, base_url: str = "http://localhost:8787"):
        self.base_url = base_url
        self.session = None
        self.test_results = []

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def add_test_result(self, test_name: str, success: bool, details: str = ""):
        """Add a test result"""
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": time.time()
        })

        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status} {test_name}: {details}")

    async def test_system_metrics_endpoint(self):
        """Test the /api/system-metrics endpoint"""
        try:
            async with self.session.get(f"{self.base_url}/api/system-metrics") as response:
                if response.status == 200:
                    data = await response.json()

                    if data.get("success"):
                        metrics = data.get("data", {})

                        # Validate required fields
                        required_fields = ["cpu", "memory", "disk", "network", "system", "timestamp"]
                        missing_fields = [field for field in required_fields if field not in metrics]

                        if missing_fields:
                            self.add_test_result(
                                "System Metrics API - Required Fields",
                                False,
                                f"Missing fields: {missing_fields}"
                            )
                            return

                        # Validate CPU data
                        cpu_data = metrics["cpu"]
                        if not all(key in cpu_data for key in ["percent", "count", "freq"]):
                            self.add_test_result(
                                "System Metrics API - CPU Data",
                                False,
                                "Missing required CPU fields"
                            )
                            return

                        # Validate memory data
                        memory_data = metrics["memory"]
                        if not all(key in memory_data for key in ["percent", "total", "available", "used"]):
                            self.add_test_result(
                                "System Metrics API - Memory Data",
                                False,
                                "Missing required memory fields"
                            )
                            return

                        # Validate disk data
                        disk_data = metrics["disk"]
                        if not all(key in disk_data for key in ["percent", "total", "used", "free"]):
                            self.add_test_result(
                                "System Metrics API - Disk Data",
                                False,
                                "Missing required disk fields"
                            )
                            return

                        # Validate network data
                        network_data = metrics["network"]
                        if not all(key in network_data for key in ["bytes_sent", "bytes_recv", "connections"]):
                            self.add_test_result(
                                "System Metrics API - Network Data",
                                False,
                                "Missing required network fields"
                            )
                            return

                        # Validate system data
                        system_data = metrics["system"]
                        if not all(key in system_data for key in ["hostname", "platform", "uptime"]):
                            self.add_test_result(
                                "System Metrics API - System Data",
                                False,
                                "Missing required system fields"
                            )
                            return

                        # Check data ranges
                        if not (0 <= cpu_data["percent"] <= 100):
                            self.add_test_result(
                                "System Metrics API - CPU Range",
                                False,
                                f"CPU percent out of range: {cpu_data['percent']}"
                            )
                            return

                        if not (0 <= memory_data["percent"] <= 100):
                            self.add_test_result(
                                "System Metrics API - Memory Range",
                                False,
                                f"Memory percent out of range: {memory_data['percent']}"
                            )
                            return

                        if not (0 <= disk_data["percent"] <= 100):
                            self.add_test_result(
                                "System Metrics API - Disk Range",
                                False,
                                f"Disk percent out of range: {disk_data['percent']}"
                            )
                            return

                        # Test battery data (optional)
                        if "battery" in metrics and metrics["battery"]:
                            battery_data = metrics["battery"]
                            if not all(key in battery_data for key in ["percent", "plugged"]):
                                self.add_test_result(
                                    "System Metrics API - Battery Data",
                                    False,
                                    "Missing required battery fields"
                                )
                                return

                            if not (0 <= battery_data["percent"] <= 100):
                                self.add_test_result(
                                    "System Metrics API - Battery Range",
                                    False,
                                    f"Battery percent out of range: {battery_data['percent']}"
                                )
                                return

                        self.add_test_result(
                            "System Metrics API",
                            True,
                            f"Successfully retrieved metrics with {len(metrics)} categories"
                        )

                        # Log sample data for verification
                        logger.info(f"Sample CPU Usage: {cpu_data['percent']:.1f}%")
                        logger.info(f"Sample Memory Usage: {memory_data['percent']:.1f}%")
                        logger.info(f"Sample Disk Usage: {disk_data['percent']:.1f}%")
                        logger.info(f"Sample Network Connections: {network_data['connections']}")
                        if metrics.get("battery"):
                            logger.info(f"Sample Battery: {metrics['battery']['percent']:.1f}%")

                    else:
                        self.add_test_result(
                            "System Metrics API - Success Flag",
                            False,
                            f"API returned success=False: {data.get('error', 'Unknown error')}"
                        )
                else:
                    self.add_test_result(
                        "System Metrics API - HTTP Status",
                        False,
                        f"HTTP {response.status}: {await response.text()}"
                    )

        except Exception as e:
            self.add_test_result(
                "System Metrics API - Connection",
                False,
                f"Connection error: {str(e)}"
            )

    async def test_api_response_time(self):
        """Test API response time"""
        try:
            start_time = time.time()
            async with self.session.get(f"{self.base_url}/api/system-metrics") as response:
                end_time = time.time()
                response_time = (end_time - start_time) * 1000  # Convert to ms

                if response.status == 200:
                    if response_time < 1000:  # Less than 1 second
                        self.add_test_result(
                            "API Response Time",
                            True,
                            f"Response time: {response_time:.1f}ms"
                        )
                    else:
                        self.add_test_result(
                            "API Response Time",
                            False,
                            f"Slow response time: {response_time:.1f}ms"
                        )
                else:
                    self.add_test_result(
                        "API Response Time",
                        False,
                        f"HTTP {response.status}"
                    )

        except Exception as e:
            self.add_test_result(
                "API Response Time",
                False,
                f"Connection error: {str(e)}"
            )

    async def test_multiple_requests(self):
        """Test multiple concurrent requests"""
        try:
            # Make 5 concurrent requests
            tasks = []
            for i in range(5):
                task = self.session.get(f"{self.base_url}/api/system-metrics")
                tasks.append(task)

            start_time = time.time()
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = time.time()

            successful_responses = 0
            for i, response in enumerate(responses):
                if isinstance(response, Exception):
                    logger.warning(f"Request {i+1} failed: {str(response)}")
                else:
                    if response.status == 200:
                        successful_responses += 1
                    else:
                        logger.warning(f"Request {i+1} returned HTTP {response.status}")

            total_time = (end_time - start_time) * 1000

            if successful_responses == 5:
                self.add_test_result(
                    "Multiple Concurrent Requests",
                    True,
                    f"All 5 requests successful in {total_time:.1f}ms"
                )
            else:
                self.add_test_result(
                    "Multiple Concurrent Requests",
                    False,
                    f"Only {successful_responses}/5 requests successful"
                )

        except Exception as e:
            self.add_test_result(
                "Multiple Concurrent Requests",
                False,
                f"Error: {str(e)}"
            )

    async def test_data_consistency(self):
        """Test data consistency across multiple requests"""
        try:
            # Make 3 requests and check consistency
            metrics_data = []
            for i in range(3):
                async with self.session.get(f"{self.base_url}/api/system-metrics") as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("success"):
                            metrics_data.append(data.get("data"))

            if len(metrics_data) < 3:
                self.add_test_result(
                    "Data Consistency",
                    False,
                    f"Only {len(metrics_data)}/3 requests succeeded"
                )
                return

            # Check timestamp consistency (should be increasing)
            timestamps = [data["timestamp"] for data in metrics_data]
            timestamp_times = [time.strptime(ts, "%Y-%m-%dT%H:%M:%S.%f") for ts in timestamps]

            is_increasing = all(timestamp_times[i] <= timestamp_times[i+1]
                              for i in range(len(timestamp_times)-1))

            if is_increasing:
                self.add_test_result(
                    "Data Consistency - Timestamps",
                    True,
                    "Timestamps are consistently increasing"
                )
            else:
                self.add_test_result(
                    "Data Consistency - Timestamps",
                    False,
                    "Timestamps are not consistently increasing"
                )

            # Check data structure consistency
            first_keys = set(metrics_data[0].keys())
            for i, data in enumerate(metrics_data[1:], 1):
                current_keys = set(data.keys())
                if first_keys != current_keys:
                    self.add_test_result(
                        "Data Consistency - Structure",
                        False,
                        f"Request {i+1} has different structure"
                    )
                    return

            self.add_test_result(
                "Data Consistency - Structure",
                True,
                "All requests have consistent data structure"
            )

        except Exception as e:
            self.add_test_result(
                "Data Consistency",
                False,
                f"Error: {str(e)}"
            )

    async def run_all_tests(self):
        """Run all tests"""
        logger.info("🧪 Starting SystemTray Component Tests")
        logger.info("=" * 50)

        # Test system metrics endpoint
        await self.test_system_metrics_endpoint()

        # Test response time
        await self.test_api_response_time()

        # Test multiple requests
        await self.test_multiple_requests()

        # Test data consistency
        await self.test_data_consistency()

        # Print summary
        logger.info("=" * 50)
        logger.info("🏁 Test Summary")
        logger.info("=" * 50)

        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)

        logger.info(f"Passed: {passed}/{total}")

        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            logger.info(f"{status} {result['test']}")
            if not result["success"] and result["details"]:
                logger.info(f"   → {result['details']}")

        if passed == total:
            logger.info("🎉 All tests passed! SystemTray component is working correctly.")
        else:
            logger.warning(f"⚠️  {total - passed} test(s) failed. Review the results above.")

        return passed == total

async def main():
    """Main test function"""
    async with SystemTrayTester() as tester:
        success = await tester.run_all_tests()
        return success

if __name__ == "__main__":
    # Run the tests
    success = asyncio.run(main())
    exit(0 if success else 1)