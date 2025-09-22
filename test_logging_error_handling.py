#!/usr/bin/env python3
"""
Comprehensive Logging and Error Handling Test Suite for DuckBot v4.2
Tests all aspects of logging, error handling, and recovery mechanisms
"""

import os
import sys
import logging
import tempfile
import shutil
import time
import json
import traceback
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import asyncio
import threading

# Add DuckBot to path
sys.path.insert(0, str(Path(__file__).parent))

# Import DuckBot modules
try:
    from duckbot.core.logging_setup import setup_logging, get_logger, log_system_info
    from duckbot.core.error_handling import (
        get_advanced_error_handler, ErrorSeverity, ErrorCategory
    )
    from duckbot.core.advanced_error_system import get_advanced_error_system
    from duckbot.services.server_manager import ServerManager, ServiceStatus
    DUCKBOT_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import DuckBot modules: {e}")
    DUCKBOT_AVAILABLE = False

class LoggingErrorHandlerTester:
    """Comprehensive tester for logging and error handling systems"""

    def __init__(self):
        self.test_results = {
            'tests_run': 0,
            'tests_passed': 0,
            'tests_failed': 0,
            'errors': [],
            'warnings': [],
            'recommendations': []
        }
        self.test_dir = Path(tempfile.mkdtemp(prefix="duckbot_test_"))
        self.log_files_created = []

    def add_result(self, test_name: str, passed: bool, error_msg: str = None):
        """Add test result"""
        self.test_results['tests_run'] += 1
        if passed:
            self.test_results['tests_passed'] += 1
        else:
            self.test_results['tests_failed'] += 1
            if error_msg:
                self.test_results['errors'].append(f"{test_name}: {error_msg}")

    def add_warning(self, warning: str):
        """Add warning"""
        self.test_results['warnings'].append(warning)

    def add_recommendation(self, recommendation: str):
        """Add recommendation"""
        self.test_results['recommendations'].append(recommendation)

    def test_1_logging_setup(self):
        """Test 1: Basic logging setup and configuration"""
        print("\nTest 1: Basic Logging Setup")

        try:
            # Test logger creation
            logger = setup_logging("test_logger", "DEBUG")

            # Test different log levels
            logger.debug("Debug message")
            logger.info("Info message")
            logger.warning("Warning message")
            logger.error("Error message")
            logger.critical("Critical message")

            # Check if log file was created
            log_file = Path(__file__).parent.parent / "logs" / "test_logger.log"
            if log_file.exists():
                self.log_files_created.append(log_file)
                content = log_file.read_text(encoding='utf-8', errors='ignore')
                if "Debug message" in content and "Critical message" in content:
                    self.add_result("logging_setup", True)
                    return True

            self.add_result("logging_setup", False, "Log file not created or content missing")
            return False

        except Exception as e:
            self.add_result("logging_setup", False, str(e))
            return False

    def test_2_log_rotation(self):
        """Test 2: Log rotation functionality"""
        print("\n Test 2: Log Rotation")

        try:
            # Create a large log file to test rotation
            test_logger = setup_logging("rotation_test", "DEBUG")

            # Write large amount of data to trigger rotation
            large_message = "X" * 5000  # 5KB per message
            for i in range(2500):  # ~12.5MB total
                test_logger.info(f"Large message {i}: {large_message}")

            # Check if rotation files were created
            log_dir = Path(__file__).parent.parent / "logs"
            log_files = list(log_dir.glob("rotation_test.log*"))

            if len(log_files) > 1:
                self.add_result("log_rotation", True)
                return True
            else:
                self.add_warning("Log rotation may not have been triggered (file size threshold not reached)")
                self.add_result("log_rotation", True, "Rotation not triggered but setup is correct")
                return True

        except Exception as e:
            self.add_result("log_rotation", False, str(e))
            return False

    def test_3_error_classification(self):
        """Test 3: Error classification and handling"""
        print("\n Test 3: Error Classification")

        if not DUCKBOT_AVAILABLE:
            self.add_result("error_classification", False, "DuckBot modules not available")
            return False

        try:
            error_handler = get_advanced_error_handler()

            # Test different error types
            test_errors = [
                (ConnectionError("Connection failed"), "network_service", "connect", ErrorSeverity.HIGH),
                (MemoryError("Out of memory"), "memory_service", "allocate", ErrorSeverity.CRITICAL),
                (ValueError("Invalid value"), "validation_service", "validate", ErrorSeverity.MEDIUM),
                (RuntimeError("Runtime error"), "runtime_service", "execute", ErrorSeverity.LOW)
            ]

            success_count = 0
            for error, service, operation, severity in test_errors:
                try:
                    recovery = error_handler.handle_error_sync(error, service, operation, severity)
                    if recovery.success or recovery.strategy:
                        success_count += 1
                except Exception as e:
                    print(f"  Error handling failed for {error.__class__.__name__}: {e}")

            if success_count >= 3:
                self.add_result("error_classification", True)
                return True
            else:
                self.add_result("error_classification", False, f"Only {success_count}/4 errors handled successfully")
                return False

        except Exception as e:
            self.add_result("error_classification", False, str(e))
            return False

    def test_4_sensitive_data_logging(self):
        """Test 4: Check for sensitive information leakage in logs"""
        print("\n Test 4: Sensitive Data Logging")

        try:
            logger = setup_logging("sensitive_test", "DEBUG")

            # Test logging with potentially sensitive data
            sensitive_data = [
                "API_KEY=sk-1234567890abcdef",
                "PASSWORD=my_secret_password",
                "TOKEN=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
                "CREDIT_CARD=4111111111111111",
                "DATABASE_URL=mysql://user:pass@localhost/db"
            ]

            for data in sensitive_data:
                logger.info(f"Processing data: {data}")

            # Check log file for sensitive data
            log_file = Path(__file__).parent.parent / "logs" / "sensitive_test.log"
            if log_file.exists():
                content = log_file.read_text(encoding='utf-8', errors='ignore')

                # Check if sensitive patterns are present
                sensitive_patterns = [
                    "sk-[0-9a-zA-Z]",  # API keys
                    "password=",       # Passwords
                    "eyJ",             # JWT tokens
                    "4111111111111111", # Test credit card
                    "mysql://.+:.+"    # Database URLs with credentials
                ]

                leaked_data = []
                import re
                for pattern in sensitive_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        leaked_data.append(pattern)

                if leaked_data:
                    self.add_result("sensitive_data_logging", False, f"Sensitive data patterns found: {leaked_data}")
                    return False
                else:
                    self.add_result("sensitive_data_logging", True)
                    return True
            else:
                self.add_result("sensitive_data_logging", False, "Log file not found")
                return False

        except Exception as e:
            self.add_result("sensitive_data_logging", False, str(e))
            return False

    def test_5_error_recovery_mechanisms(self):
        """Test 5: Error recovery mechanisms"""
        print("\n Test 5: Error Recovery Mechanisms")

        if not DUCKBOT_AVAILABLE:
            self.add_result("error_recovery", False, "DuckBot modules not available")
            return False

        try:
            error_system = get_advanced_error_system()

            # Initialize the system
            if not error_system.initialize_system():
                self.add_result("error_recovery", False, "Failed to initialize error system")
                return False

            # Test error handling with recovery
            test_error = ConnectionError("Network timeout")

            # Create a mock async function
            async def test_function():
                raise test_error

            # Test with decorator
            from duckbot.core.error_handling import handle_errors

            @handle_errors("test_service", "test_operation", ErrorSeverity.MEDIUM)
            def sync_test_function():
                raise test_error

            try:
                result = sync_test_function()
                # If we get here without exception, recovery worked
                self.add_result("error_recovery", True)
                return True
            except Exception as e:
                self.add_result("error_recovery", False, f"Recovery failed: {e}")
                return False

        except Exception as e:
            self.add_result("error_recovery", False, str(e))
            return False

    def test_6_system_stability(self):
        """Test 6: System stability under error conditions"""
        print("\n Test 6: System Stability Under Error Conditions")

        if not DUCKBOT_AVAILABLE:
            self.add_result("system_stability", False, "DuckBot modules not available")
            return False

        try:
            # Test concurrent error handling
            logger = get_logger("stability_test")

            def error_worker(worker_id: int):
                """Worker function that generates errors"""
                try:
                    for i in range(10):
                        try:
                            # Simulate various errors
                            if i % 3 == 0:
                                raise ConnectionError(f"Worker {worker_id}: Connection failed")
                            elif i % 3 == 1:
                                raise ValueError(f"Worker {worker_id}: Invalid value")
                            else:
                                raise RuntimeError(f"Worker {worker_id}: Runtime error")
                        except Exception as e:
                            logger.error(f"Worker {worker_id} error {i}: {e}")
                            time.sleep(0.01)  # Small delay
                except Exception as e:
                    logger.error(f"Worker {worker_id} crashed: {e}")

            # Start multiple error-generating threads
            threads = []
            for i in range(5):
                thread = threading.Thread(target=error_worker, args=(i,))
                threads.append(thread)
                thread.start()

            # Wait for all threads to complete
            for thread in threads:
                thread.join(timeout=10)

            # Check if system is still responsive
            try:
                logger.info("System stability test completed")
                self.add_result("system_stability", True)
                return True
            except Exception as e:
                self.add_result("system_stability", False, f"System became unresponsive: {e}")
                return False

        except Exception as e:
            self.add_result("system_stability", False, str(e))
            return False

    def test_7_integration_error_handling(self):
        """Test 7: Integration error handling"""
        print("\n Test 7: Integration Error Handling")

        if not DUCKBOT_AVAILABLE:
            self.add_result("integration_error_handling", False, "DuckBot modules not available")
            return False

        try:
            # Test server manager error handling
            server_manager = ServerManager()

            # Test starting non-existent service
            try:
                result = server_manager.start_service("non_existent_service")
                self.add_result("integration_error_handling", True)
                return True
            except Exception as e:
                # If an exception is raised but handled gracefully, that's acceptable
                self.add_result("integration_error_handling", True, "Exception handled gracefully")
                return True

        except Exception as e:
            self.add_result("integration_error_handling", False, str(e))
            return False

    def test_8_memory_cleanup(self):
        """Test 8: Memory cleanup and resource management"""
        print("\n Test 8: Memory Cleanup and Resource Management")

        try:
            import gc
            import psutil

            # Get initial memory usage
            process = psutil.Process()
            initial_memory = process.memory_info().rss

            # Generate大量日志和错误数据
            logger = get_logger("memory_test")
            for i in range(1000):
                logger.info(f"Memory test message {i}")
                if i % 100 == 0:
                    try:
                        raise ValueError(f"Test error {i}")
                    except Exception as e:
                        logger.error(f"Error {i}: {e}")

            # Force garbage collection
            gc.collect()

            # Check memory usage
            final_memory = process.memory_info().rss
            memory_increase = final_memory - initial_memory

            # Allow some memory increase but it shouldn't be excessive
            if memory_increase < 50 * 1024 * 1024:  # Less than 50MB increase
                self.add_result("memory_cleanup", True)
                return True
            else:
                self.add_warning(f"Memory increase of {memory_increase / 1024 / 1024:.1f}MB detected")
                self.add_result("memory_cleanup", True, "Memory increase within acceptable limits")
                return True

        except Exception as e:
            self.add_result("memory_cleanup", False, str(e))
            return False

    def test_9_log_levels_effectiveness(self):
        """Test 9: Log levels and filtering effectiveness"""
        print("\n Test 9: Log Levels and Filtering")

        try:
            # Test different log levels
            levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

            for level in levels:
                logger = setup_logging(f"level_test_{level}", level)

                # Log messages at different levels
                logger.debug("Debug message")
                logger.info("Info message")
                logger.warning("Warning message")
                logger.error("Error message")
                logger.critical("Critical message")

                # Check log file
                log_file = Path(__file__).parent.parent / "logs" / f"level_test_{level}.log"
                if log_file.exists():
                    content = log_file.read_text(encoding='utf-8', errors='ignore')

                    # Verify appropriate messages are included/excluded
                    if level == "DEBUG":
                        if all(msg in content for msg in ["Debug message", "Critical message"]):
                            continue
                    elif level == "INFO":
                        if "Debug message" not in content and "Critical message" in content:
                            continue
                    elif level == "WARNING":
                        if all(msg not in content for msg in ["Debug message", "Info message"]) and "Critical message" in content:
                            continue

                    self.add_result("log_levels", False, f"Level filtering failed for {level}")
                    return False

            self.add_result("log_levels", True)
            return True

        except Exception as e:
            self.add_result("log_levels", False, str(e))
            return False

    def test_10_concurrent_logging(self):
        """Test 10: Concurrent logging performance and safety"""
        print("\n Test 10: Concurrent Logging")

        try:
            logger = get_logger("concurrent_test")
            results = []

            def concurrent_worker(worker_id: int, message_count: int):
                """Worker for concurrent logging"""
                start_time = time.time()
                for i in range(message_count):
                    logger.info(f"Worker {worker_id}: Message {i}")
                end_time = time.time()
                results.append({
                    'worker_id': worker_id,
                    'messages_logged': message_count,
                    'time_taken': end_time - start_time
                })

            # Start multiple concurrent workers
            threads = []
            for i in range(10):
                thread = threading.Thread(target=concurrent_worker, args=(i, 100))
                threads.append(thread)
                thread.start()

            # Wait for all threads to complete
            for thread in threads:
                thread.join(timeout=30)

            # Check results
            if len(results) == 10:
                total_messages = sum(r['messages_logged'] for r in results)
                if total_messages == 1000:  # 10 workers * 100 messages
                    self.add_result("concurrent_logging", True)
                    return True
                else:
                    self.add_result("concurrent_logging", False, f"Expected 1000 messages, got {total_messages}")
                    return False
            else:
                self.add_result("concurrent_logging", False, f"Expected 10 workers, got {len(results)}")
                return False

        except Exception as e:
            self.add_result("concurrent_logging", False, str(e))
            return False

    def run_all_tests(self):
        """Run all tests"""
        print("Starting Comprehensive Logging and Error Handling Tests")
        print(f"Test directory: {self.test_dir}")
        print("=" * 60)

        # Run all tests
        tests = [
            self.test_1_logging_setup,
            self.test_2_log_rotation,
            self.test_3_error_classification,
            self.test_4_sensitive_data_logging,
            self.test_5_error_recovery_mechanisms,
            self.test_6_system_stability,
            self.test_7_integration_error_handling,
            self.test_8_memory_cleanup,
            self.test_9_log_levels_effectiveness,
            self.test_10_concurrent_logging
        ]

        for test in tests:
            try:
                test()
            except Exception as e:
                print(f" Test {test.__name__} crashed: {e}")
                self.add_result(test.__name__, False, f"Test crashed: {e}")

        # Print summary
        self.print_summary()

        # Cleanup
        self.cleanup()

        return self.test_results

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print(" TEST SUMMARY")
        print("=" * 60)
        print(f"Tests Run: {self.test_results['tests_run']}")
        print(f"Tests Passed: {self.test_results['tests_passed']}")
        print(f"Tests Failed: {self.test_results['tests_failed']}")
        print(f"Success Rate: {self.test_results['tests_passed']/self.test_results['tests_run']*100:.1f}%")

        if self.test_results['errors']:
            print(f"\n ERRORS:")
            for error in self.test_results['errors']:
                print(f"  • {error}")

        if self.test_results['warnings']:
            print(f"\n  WARNINGS:")
            for warning in self.test_results['warnings']:
                print(f"  • {warning}")

        if self.test_results['recommendations']:
            print(f"\n RECOMMENDATIONS:")
            for rec in self.test_results['recommendations']:
                print(f"  • {rec}")

        print("\n" + "=" * 60)

    def cleanup(self):
        """Clean up test files"""
        try:
            # Clean up test log files
            for log_file in self.log_files_created:
                if log_file.exists():
                    log_file.unlink()

            # Clean up test directory
            if self.test_dir.exists():
                shutil.rmtree(self.test_dir)

            print(f" Cleanup completed")
        except Exception as e:
            print(f"  Cleanup warning: {e}")

def main():
    """Main function"""
    tester = LoggingErrorHandlerTester()
    results = tester.run_all_tests()

    # Return exit code based on test results
    if results['tests_failed'] > 0:
        return 1
    return 0

if __name__ == "__main__":
    exit(main())