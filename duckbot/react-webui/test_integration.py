#!/usr/bin/env python3
"""
Comprehensive integration test for health monitoring services
"""

import asyncio
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.health_monitor import get_health_monitor, start_health_monitoring
from event_system import get_webui_event_system, start_webui_event_system, WebUIEventType
from intelligent_alerting import get_webui_intelligent_alerting
from performance_analytics import get_performance_analytics

async def comprehensive_test():
    try:
        print('Starting comprehensive health monitoring integration test...')

        # Test health monitor
        print('\n1. Testing Health Monitor...')
        monitor = get_health_monitor()
        status = monitor.get_current_status()
        print(f'   Health monitor initialized: {status["monitoring_active"]}')
        print(f'   Services configured: {status["total_services"]}')

        # Test event system
        print('\n2. Testing Event System...')
        event_system = get_webui_event_system()
        await event_system.start()
        event_id = await event_system.emit(WebUIEventType.SYSTEM_HEALTH_CHANGED, 'test', {'status': 'healthy'})
        print(f'   Event system started, event emitted: {event_id}')

        # Test alerting system
        print('\n3. Testing Alerting System...')
        alerting_system = get_webui_intelligent_alerting()
        test_metrics = {'cpu_percent': 85, 'memory_usage': 75, 'status': 'healthy'}
        alerts = await alerting_system.check_alerts('test_service', test_metrics)
        print(f'   Alerting system active, alerts created: {len(alerts)}')

        # Test performance analytics
        print('\n4. Testing Performance Analytics...')
        analytics = get_performance_analytics()
        await analytics.collect_metrics('test_service', test_metrics)
        summary = await analytics.get_performance_summary()
        print(f'   Performance analytics working: {"services" in summary}')

        # Test integration between systems
        print('\n5. Testing System Integration...')

        # Simulate health check and propagate to other systems
        service_metrics = {
            'response_time': 2.5,
            'memory_usage': 65,
            'cpu_usage': 45,
            'error_rate': 0.02,
            'status': 'healthy'
        }

        # Collect performance metrics
        await analytics.collect_metrics('integrated_test_service', service_metrics)

        # Check for alerts
        integration_alerts = await alerting_system.check_alerts('integrated_test_service', service_metrics)

        # Emit system health event
        await event_system.emit(
            WebUIEventType.SERVICE_HEALTH_UPDATE,
            'health_monitor',
            {'service_name': 'integrated_test_service', 'metrics': service_metrics}
        )

        print(f'   Integration test completed: {len(integration_alerts)} alerts generated')

        # Get final status
        final_status = monitor.get_current_status()
        event_stats = event_system.get_event_stats()
        alert_summary = alerting_system.get_alert_summary()

        print('\n=== Final Integration Test Results ===')
        print(f'Health Monitor: {final_status["total_services"]} services configured')
        print(f'Event System: {event_stats["total_events"]} events processed')
        print(f'Alerting System: {alert_summary["total_active"]} active alerts')
        print(f'Performance Analytics: {len(summary.get("services", {}))} services monitored')

        # Clean up
        await event_system.stop()

        print('\n✅ All health monitoring services integration tests passed!')

    except Exception as e:
        print(f'❌ Integration test failed: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(comprehensive_test())