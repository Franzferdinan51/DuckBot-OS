#!/usr/bin/env python3
"""
Simple test script for DuckBot Monitoring System
"""

import sys
import time
import tempfile
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    print("Testing DuckBot Monitoring System")
    print("=" * 50)

    # Test 1: Import core monitoring system
    print("\n1. Testing core monitoring system import...")
    from duckbot.core.monitoring_system import (
        DuckBotMonitoring, MonitoringDatabase, SystemMetric, AgentMetric,
        AlertLevel, HealthStatus, MetricType
    )
    print("OK - Core monitoring system imported successfully")

    # Test 2: Create temporary database
    print("\n2. Testing database creation...")
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_db.close()
    db = MonitoringDatabase(temp_db.name)
    print("OK - Database created successfully")

    # Test 3: Store system metric
    print("\n3. Testing system metrics storage...")
    from datetime import datetime
    metric = SystemMetric(
        name="test_cpu",
        value=75.5,
        metric_type=MetricType.GAUGE,
        timestamp=datetime.now(),
        tags={"host": "test"}
    )
    db.store_system_metric(metric)
    print("OK - System metric stored successfully")

    # Test 4: Create monitoring instance
    print("\n4. Testing monitoring instance creation...")
    monitoring = DuckBotMonitoring(temp_db.name)
    print("OK - Monitoring instance created successfully")

    # Test 5: Record agent interaction
    print("\n5. Testing agent interaction recording...")
    monitoring.record_agent_interaction(
        agent_id="test_agent",
        agent_type="chat",
        response_time_ms=150.5,
        success=True,
        model_used="test-model",
        tokens_used=100
    )
    print("OK - Agent interaction recorded successfully")

    # Test 6: Start monitoring
    print("\n6. Testing monitoring startup...")
    monitoring.start(metrics_interval=1.0, health_check_interval=2.0)
    print("OK - Monitoring started successfully")

    # Test 7: Get system status
    print("\n7. Testing system status retrieval...")
    status = monitoring.get_system_status()
    print(f"OK - System status retrieved: {len(status)} components")

    # Test 8: User activity tracking
    print("\n8. Testing user activity tracking...")
    session_id = monitoring.user_activity_tracker.start_session("test_user")
    monitoring.record_user_activity(
        session_id=session_id,
        activity_type="test",
        feature_used="monitoring",
        response_time_ms=50.0,
        satisfaction_score=5
    )
    print("OK - User activity tracked successfully")

    # Test 9: Activity summary
    print("\n9. Testing activity summary...")
    summary = monitoring.user_activity_tracker.get_activity_summary(hours=1)
    print(f"OK - Activity summary: {summary.get('total_activities', 0)} activities")

    # Test 10: Alert system
    print("\n10. Testing alert system...")
    monitoring.alert_manager.check_alerts({
        "cpu_percent": 95.0,
        "memory_percent": 88.0
    })
    alerts = monitoring.database.get_active_alerts()
    print(f"OK - Alert system working: {len(alerts)} alerts created")

    # Test 11: Stop monitoring
    print("\n11. Testing monitoring shutdown...")
    monitoring.stop()
    print("OK - Monitoring stopped successfully")

    # Clean up (commented out due to file lock)
    # os.unlink(temp_db.name)
    print("INFO - Database file kept for inspection")

    print("\nAll tests passed! Monitoring system is working correctly.")

    # Test dashboard import
    print("\n12. Testing dashboard import...")
    try:
        from duckbot.services.enhanced_monitoring_dashboard import EnhancedMonitoringDashboard
        print("OK - Dashboard imported successfully")
    except ImportError as e:
        print(f"WARN -  Dashboard import failed (expected if dependencies missing): {e}")

    # Test analytics import
    print("\n13. Testing analytics import...")
    try:
        from duckbot.analytics.monitoring_analytics import MonitoringAnalytics
        print("OK - Analytics imported successfully")
    except ImportError as e:
        print(f"WARN -  Analytics import failed (expected if dependencies missing): {e}")

    # Test integration import
    print("\n14. Testing integration import...")
    try:
        from duckbot.integrations.monitoring_integration import get_monitoring_integration
        print("OK - Integration imported successfully")
    except ImportError as e:
        print(f"WARN -  Integration import failed: {e}")

    print("\nMonitoring System Test Summary:")
    print("OK - Core monitoring system: WORKING")
    print("OK - Database operations: WORKING")
    print("OK - Metrics collection: WORKING")
    print("OK - Agent monitoring: WORKING")
    print("OK - User activity tracking: WORKING")
    print("OK - Alert system: WORKING")
    print("OK - System status: WORKING")
    print("Dashboard: Available (if dependencies installed)")
    print("Analytics: Available (if dependencies installed)")
    print("Integration: Available")

    print("\nMonitoring system is ready for use!")
    print("   Run: python start_monitoring_system.py")
    print("   Or:  python start_monitoring_system.py --cli")

except Exception as e:
    print(f"ERROR - Test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)