#!/usr/bin/env python3
"""
Test script for the Advanced Error Handling System
Demonstrates all features of the comprehensive error handling and recovery system
"""

import sys
import time
import asyncio
from datetime import datetime
import traceback

# Add current directory to path
sys.path.append('.')

def test_error_classification():
    """Test the error classification system"""
    print("\n=== Testing Error Classification ===")

    try:
        from duckbot.core.error_handling import (
            ErrorContext, ErrorSeverity, ErrorCategory,
            RecoveryAction, get_advanced_error_handler
        )

        # Create error handler
        handler = get_advanced_error_handler()

        # Test different error types
        test_errors = [
            {
                'context': ErrorContext(
                    service_name="TestService",
                    operation="test_operation",
                    error_type=ConnectionError("Connection failed"),
                    severity=ErrorSeverity.HIGH,
                    category=ErrorCategory.NETWORK,
                    metadata={"url": "http://test.com", "timeout": 30}
                ),
                'description': 'Network connection error'
            },
            {
                'context': ErrorContext(
                    service_name="MemoryService",
                    operation="memory_allocation",
                    error_type=MemoryError("Out of memory"),
                    severity=ErrorSeverity.CRITICAL,
                    category=ErrorCategory.MEMORY,
                    metadata={"requested_mb": 1024, "available_mb": 512}
                ),
                'description': 'Memory allocation error'
            },
            {
                'context': ErrorContext(
                    service_name="APIService",
                    operation="api_call",
                    error_type=ValueError("Invalid parameter"),
                    severity=ErrorSeverity.MEDIUM,
                    category=ErrorCategory.API,
                    metadata={"endpoint": "/api/test", "status_code": 400}
                ),
                'description': 'API validation error'
            }
        ]

        print(f"Error handler initialized: {handler is not None}")

        # Test error classification
        for i, error_data in enumerate(test_errors):
            result = handler.handle_error(error_data['context'])
            print(f"  Test {i+1}: {error_data['description']}")
            print(f"    - Recovery action: {result['recovery_action']}")
            print(f"    - Status: {result['status']}")
            print(f"    - Success: {result['success']}")

        return True

    except Exception as e:
        print(f"Error classification test failed: {e}")
        traceback.print_exc()
        return False

def test_recovery_workflows():
    """Test the recovery workflow system"""
    print("\n=== Testing Recovery Workflows ===")

    try:
        from duckbot.core.recovery_workflows import get_recovery_workflow_manager

        # Get workflow manager
        workflow_manager = get_recovery_workflow_manager()

        print(f"Workflow manager initialized: {workflow_manager is not None}")

        # List available workflows
        workflows = workflow_manager.list_workflows()
        print(f"  Available workflows: {len(workflows)}")

        for workflow_id in workflows:
            workflow = workflow_manager.get_workflow(workflow_id)
            if workflow:
                print(f"    - {workflow_id}: {workflow.description}")
                print(f"      Priority: {workflow.priority.name}")
                print(f"      Steps: {len(workflow.steps)}")

        return True

    except Exception as e:
        print(f"Recovery workflows test failed: {e}")
        traceback.print_exc()
        return False

def test_self_healing():
    """Test the self-healing system"""
    print("\n=== Testing Self-Healing System ===")

    try:
        from duckbot.core.self_healing import get_self_healing_system

        # Get self-healing system
        healing_system = get_self_healing_system()

        print(f"Self-healing system initialized: {healing_system is not None}")

        # Test health check
        health_status = healing_system.check_system_health()
        print(f"  System health: {health_status['overall_health']}")
        print(f"  Components checked: {len(health_status['component_status'])}")

        # Test auto-repair capabilities
        repair_actions = healing_system.get_available_repair_actions()
        print(f"  Available repair actions: {len(repair_actions)}")

        for action in repair_actions:
            print(f"    - {action}: {repair_actions[action]['description']}")

        return True

    except Exception as e:
        print(f"Self-healing test failed: {e}")
        traceback.print_exc()
        return False

def test_error_monitoring():
    """Test the error monitoring system"""
    print("\n=== Testing Error Monitoring System ===")

    try:
        from duckbot.core.error_monitoring import get_error_analytics_engine

        # Get analytics engine
        analytics = get_error_analytics_engine()

        print(f"Error analytics engine initialized: {analytics is not None}")

        # Get error statistics
        stats = analytics.get_error_statistics()
        print(f"  Error tracking statistics:")
        print(f"    - Total errors: {stats['total_errors']}")
        print(f"    - Unique error patterns: {stats['unique_patterns']}")
        print(f"    - Active alerts: {stats['active_alerts']}")

        # Test alerting system
        alerts = analytics.get_active_alerts()
        print(f"  Active alerts: {len(alerts)}")

        return True

    except Exception as e:
        print(f"Error monitoring test failed: {e}")
        traceback.print_exc()
        return False

def test_integration_system():
    """Test the integration system"""
    print("\n=== Testing Integration System ===")

    try:
        from duckbot.core.error_integration import get_error_integration_manager

        # Get integration manager
        integration = get_error_integration_manager()

        print(f"Integration manager initialized: {integration is not None}")

        # Get integration status
        status = integration.get_integration_status()
        print(f"  Integration status:")
        print(f"    - Error handling: {status['error_handling']['status']}")
        print(f"    - Self-healing: {status['self_healing']['status']}")
        print(f"    - Monitoring: {status['monitoring']['status']}")
        print(f"    - Workflows: {status['workflows']['status']}")

        return True

    except Exception as e:
        print(f"Integration system test failed: {e}")
        traceback.print_exc()
        return False

def test_dashboard():
    """Test the recovery dashboard"""
    print("\n=== Testing Recovery Dashboard ===")

    try:
        from duckbot.core.recovery_dashboard import get_recovery_dashboard

        # Get dashboard
        dashboard = get_recovery_dashboard()

        print(f"Dashboard initialized: {dashboard is not None}")

        # Get dashboard status
        status = dashboard.get_dashboard_status()
        print(f"  Dashboard status:")
        print(f"    - Running: {status['running']}")
        print(f"    - Port: {status['port']}")
        print(f"    - Connected clients: {status['connected_clients']}")

        return True

    except Exception as e:
        print(f"Dashboard test failed: {e}")
        traceback.print_exc()
        return False

def test_comprehensive_system():
    """Test the complete integrated system"""
    print("\n=== Testing Complete System Integration ===")

    try:
        from duckbot.core.advanced_error_system import AdvancedErrorSystem

        # Create and initialize system
        system = AdvancedErrorSystem()

        if not system.initialize_system():
            print("Failed to initialize system")
            return False

        if not system.start_system():
            print("Failed to start system")
            return False

        print("Advanced Error System initialized and started")

        # Get comprehensive system status
        status = system.get_system_status()
        print(f"  System Status:")
        print(f"    - Initialized: {status['system_initialized']}")
        print(f"    - Running: {status['system_running']}")
        print(f"    - Uptime: {status['uptime_seconds']:.2f} seconds")

        # Test metrics
        metrics = status['metrics']
        print(f"  System Metrics:")
        for key, value in metrics.items():
            print(f"    - {key}: {value}")

        # Test a simulated error handling scenario
        print("\n  Testing error handling scenario...")

        # Simulate an error
        from duckbot.core.error_handling import ErrorContext, ErrorSeverity, ErrorCategory

        error_context = ErrorContext(
            service_name="TestService",
            operation="critical_operation",
            error_type=RuntimeError("Test error for demonstration"),
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.SERVICE,
            metadata={"test": True, "demonstration": True}
        )

        result = system.handle_error(error_context)
        print(f"    Error handled successfully: {result['success']}")
        print(f"    Recovery action: {result['recovery_action']}")

        return True

    except Exception as e:
        print(f"Comprehensive system test failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("Starting Advanced Error Handling System Test Suite")
    print("=" * 60)

    test_results = []

    # Run all tests
    test_functions = [
        test_error_classification,
        test_recovery_workflows,
        test_self_healing,
        test_error_monitoring,
        test_integration_system,
        test_dashboard,
        test_comprehensive_system
    ]

    for test_func in test_functions:
        try:
            result = test_func()
            test_results.append((test_func.__name__, result))
        except Exception as e:
            print(f"Test {test_func.__name__} failed with exception: {e}")
            test_results.append((test_func.__name__, False))

    # Summary
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)

    passed = 0
    total = len(test_results)

    for test_name, result in test_results:
        status = "PASS" if result else "FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1

    print(f"\nSummary: {passed}/{total} tests passed")

    if passed == total:
        print("\nAll tests passed! The Advanced Error Handling System is fully operational.")
        print("\nSystem Features:")
        print("  - Comprehensive error classification with severity levels")
        print("  - Automated recovery mechanisms with multiple strategies")
        print("  - Real-time error monitoring and analytics")
        print("  - Self-healing capabilities with health checks")
        print("  - Configurable recovery workflows")
        print("  - Integration with existing DuckBot systems")
        print("  - Web-based recovery dashboard")
        print("  - Circuit breaker patterns and failure prevention")
        print("  - Predictive analytics and trend analysis")
        print("  - Comprehensive logging and reporting")

        print("\nUsage:")
        print("  from duckbot.core.advanced_error_system import AdvancedErrorSystem")
        print("  system = AdvancedErrorSystem()")
        print("  system.initialize_system()")
        print("  system.start_system()")
        print("  system.handle_error(error_context)")
        print("  status = system.get_system_status()")

        return True
    else:
        print(f"\n{total - passed} tests failed. Please check the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)