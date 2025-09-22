#!/usr/bin/env python3
"""
Health Monitor API Endpoints
Provides REST API for health monitoring data and control
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
import logging

# Local imports
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.health_monitor import get_health_monitor, HealthMonitor
from core.logging_setup import setup_logging
from performance_analytics import get_performance_analytics, PerformanceAnalytics

logger = logging.getLogger(__name__)
router = APIRouter()

# Global health monitor instance
_health_monitor: Optional[HealthMonitor] = None

async def get_health_monitor_instance() -> HealthMonitor:
    """Get or create health monitor instance"""
    global _health_monitor
    if _health_monitor is None:
        _health_monitor = get_health_monitor()
        if not _health_monitor.running:
            await _health_monitor.start_monitoring()
    return _health_monitor

@router.get("/status")
async def get_system_status():
    """Get overall system health status"""
    try:
        monitor = await get_health_monitor_instance()
        status = monitor.get_current_status()
        return JSONResponse(content=status)
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/services")
async def get_service_health():
    """Get health status for all services"""
    try:
        monitor = await get_health_monitor_instance()
        services = {}

        for service_name, service_data in monitor.services.items():
            current_health = service_data.get('health_history', [])[-1] if service_data.get('health_history') else None
            if current_health:
                services[service_name] = {
                    'name': current_health.name,
                    'status': current_health.status,
                    'response_time': current_health.response_time,
                    'error': current_health.error,
                    'last_check': current_health.last_check.isoformat(),
                    'uptime': current_health.uptime,
                    'restart_count': current_health.restart_count,
                    'metrics': current_health.metrics,
                    'history': [
                        {
                            'timestamp': h.last_check.isoformat(),
                            'status': h.status,
                            'response_time': h.response_time,
                            'error': h.error
                        }
                        for h in service_data.get('health_history', [])[-50:]  # Last 50 checks
                    ]
                }

        return JSONResponse(content=services)
    except Exception as e:
        logger.error(f"Error getting service health: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/services/{service_name}")
async def get_service_detail(service_name: str):
    """Get detailed health information for a specific service"""
    try:
        monitor = await get_health_monitor_instance()

        if service_name not in monitor.services:
            raise HTTPException(status_code=404, detail=f"Service {service_name} not found")

        service_data = monitor.services[service_name]
        current_health = service_data.get('health_history', [])[-1] if service_data.get('health_history') else None

        if not current_health:
            raise HTTPException(status_code=404, detail=f"No health data available for {service_name}")

        # Get recent history
        history = monitor.get_service_history(service_name, hours=24)

        return JSONResponse(content={
            'service': service_name,
            'current_health': {
                'name': current_health.name,
                'status': current_health.status,
                'response_time': current_health.response_time,
                'error': current_health.error,
                'last_check': current_health.last_check.isoformat(),
                'uptime': current_health.uptime,
                'restart_count': current_health.restart_count,
                'metrics': current_health.metrics
            },
            'restart_history': service_data.get('restart_count', 0),
            'current_uptime': service_data.get('current_uptime', 0),
            'history': history,
            'availability_24h': calculate_availability(history),
            'avg_response_time_24h': calculate_avg_response_time(history)
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting service detail for {service_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/services/{service_name}/history")
async def get_service_history(
    service_name: str,
    hours: int = Query(24, ge=1, le=168, description="Hours of history to retrieve (1-168)")
):
    """Get health history for a specific service"""
    try:
        monitor = await get_health_monitor_instance()
        history = monitor.get_service_history(service_name, hours)

        return JSONResponse(content={
            'service': service_name,
            'hours': hours,
            'data_points': len(history),
            'history': history
        })

    except Exception as e:
        logger.error(f"Error getting service history for {service_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics")
async def get_system_metrics(
    hours: int = Query(24, ge=1, le=168, description="Hours of metrics to retrieve (1-168)")
):
    """Get system performance metrics"""
    try:
        monitor = await get_health_monitor_instance()
        metrics = monitor.get_system_metrics_history(hours)

        return JSONResponse(content={
            'hours': hours,
            'data_points': len(metrics),
            'metrics': metrics
        })

    except Exception as e:
        logger.error(f"Error getting system metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics/summary")
async def get_metrics_summary():
    """Get summary statistics for system metrics"""
    try:
        monitor = await get_health_monitor_instance()
        metrics = monitor.get_system_metrics_history(hours=1)  # Last hour

        if not metrics:
            return JSONResponse(content={
                'cpu_avg': 0,
                'cpu_max': 0,
                'memory_avg': 0,
                'memory_max': 0,
                'sample_count': 0
            })

        cpu_values = [m['cpu_percent'] for m in metrics if m['cpu_percent'] is not None]
        memory_values = [m['memory_percent'] for m in metrics if m['memory_percent'] is not None]

        return JSONResponse(content={
            'cpu_avg': sum(cpu_values) / len(cpu_values) if cpu_values else 0,
            'cpu_max': max(cpu_values) if cpu_values else 0,
            'memory_avg': sum(memory_values) / len(memory_values) if memory_values else 0,
            'memory_max': max(memory_values) if memory_values else 0,
            'sample_count': len(metrics)
        })

    except Exception as e:
        logger.error(f"Error getting metrics summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/alerts")
async def get_alerts(
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of alerts to return"),
    unresolved_only: bool = Query(False, description="Only return unresolved alerts"),
    severity: Optional[str] = Query(None, description="Filter by severity (critical, warning, info)")
):
    """Get alert history"""
    try:
        monitor = await get_health_monitor_instance()
        alerts = monitor.get_alerts(limit, unresolved_only)

        # Filter by severity if specified
        if severity:
            alerts = [alert for alert in alerts if alert['severity'] == severity]

        return JSONResponse(content={
            'total_alerts': len(alerts),
            'filters': {
                'unresolved_only': unresolved_only,
                'severity': severity
            },
            'alerts': alerts
        })

    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/alerts/{alert_id}")
async def get_alert_detail(alert_id: int):
    """Get detailed information about a specific alert"""
    try:
        monitor = await get_health_monitor_instance()

        # This would need to be implemented in the HealthMonitor class
        # For now, we'll search through all alerts
        all_alerts = monitor.get_alerts(limit=1000)
        alert = next((a for a in all_alerts if a['id'] == alert_id), None)

        if not alert:
            raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")

        return JSONResponse(content=alert)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting alert detail for {alert_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: int):
    """Acknowledge an alert"""
    try:
        monitor = await get_health_monitor_instance()

        # This would need to be implemented in the HealthMonitor class
        # For now, we'll just return success
        logger.info(f"Alert {alert_id} acknowledged")

        return JSONResponse(content={
            'success': True,
            'message': f'Alert {alert_id} acknowledged',
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error acknowledging alert {alert_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: int):
    """Mark an alert as resolved"""
    try:
        monitor = await get_health_monitor_instance()

        # This would need to be implemented in the HealthMonitor class
        # For now, we'll just return success
        logger.info(f"Alert {alert_id} resolved")

        return JSONResponse(content={
            'success': True,
            'message': f'Alert {alert_id} resolved',
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error resolving alert {alert_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics")
async def get_health_analytics(
    hours: int = Query(24, ge=1, le=168, description="Hours of data to analyze (1-168)")
):
    """Get health analytics and insights"""
    try:
        monitor = await get_health_monitor_instance()

        # Get service health data
        service_analytics = {}
        for service_name in monitor.services.keys():
            history = monitor.get_service_history(service_name, hours)
            if history:
                service_analytics[service_name] = {
                    'availability': calculate_availability(history),
                    'avg_response_time': calculate_avg_response_time(history),
                    'total_checks': len(history),
                    'unhealthy_count': len([h for h in history if h['status'] == 'unhealthy']),
                    'error_rate': len([h for h in history if h['error']]) / len(history) * 100 if history else 0
                }

        # Get system metrics analytics
        metrics_history = monitor.get_system_metrics_history(hours)
        metrics_analytics = {}

        if metrics_history:
            cpu_values = [m['cpu_percent'] for m in metrics_history if m['cpu_percent'] is not None]
            memory_values = [m['memory_percent'] for m in metrics_history if m['memory_percent'] is not None]

            metrics_analytics = {
                'cpu': {
                    'avg': sum(cpu_values) / len(cpu_values) if cpu_values else 0,
                    'max': max(cpu_values) if cpu_values else 0,
                    'min': min(cpu_values) if cpu_values else 0,
                    'trend': calculate_trend(cpu_values[-10:] if len(cpu_values) >= 10 else cpu_values)
                },
                'memory': {
                    'avg': sum(memory_values) / len(memory_values) if memory_values else 0,
                    'max': max(memory_values) if memory_values else 0,
                    'min': min(memory_values) if memory_values else 0,
                    'trend': calculate_trend(memory_values[-10:] if len(memory_values) >= 10 else memory_values)
                }
            }

        # Get alert analytics
        alerts = monitor.get_alerts(limit=1000)
        recent_alerts = [a for a in alerts if datetime.fromisoformat(a['timestamp']) > datetime.now() - timedelta(hours=hours)]

        alert_analytics = {
            'total_alerts': len(recent_alerts),
            'by_severity': {
                'critical': len([a for a in recent_alerts if a['severity'] == 'critical']),
                'warning': len([a for a in recent_alerts if a['severity'] == 'warning']),
                'info': len([a for a in recent_alerts if a['severity'] == 'info'])
            },
            'by_service': {},
            'resolved_count': len([a for a in recent_alerts if a['resolved']]),
            'unresolved_count': len([a for a in recent_alerts if not a['resolved']])
        }

        # Group alerts by service
        for alert in recent_alerts:
            service = alert['service_name'] or 'system'
            if service not in alert_analytics['by_service']:
                alert_analytics['by_service'][service] = 0
            alert_analytics['by_service'][service] += 1

        return JSONResponse(content={
            'time_range': {
                'hours': hours,
                'start': (datetime.now() - timedelta(hours=hours)).isoformat(),
                'end': datetime.now().isoformat()
            },
            'service_analytics': service_analytics,
            'metrics_analytics': metrics_analytics,
            'alert_analytics': alert_analytics,
            'overall_health': calculate_overall_health(service_analytics)
        })

    except Exception as e:
        logger.error(f"Error getting health analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/monitoring/start")
async def start_monitoring():
    """Start health monitoring"""
    try:
        monitor = await get_health_monitor_instance()
        if monitor.running:
            return JSONResponse(content={
                'success': True,
                'message': 'Monitoring already running',
                'status': 'running'
            })

        await monitor.start_monitoring()

        return JSONResponse(content={
            'success': True,
            'message': 'Health monitoring started',
            'status': 'running',
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error starting monitoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/monitoring/stop")
async def stop_monitoring():
    """Stop health monitoring"""
    try:
        monitor = await get_health_monitor_instance()
        if not monitor.running:
            return JSONResponse(content={
                'success': True,
                'message': 'Monitoring already stopped',
                'status': 'stopped'
            })

        await monitor.stop_monitoring()

        return JSONResponse(content={
            'success': True,
            'message': 'Health monitoring stopped',
            'status': 'stopped',
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error stopping monitoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/monitoring/status")
async def get_monitoring_status():
    """Get current monitoring status"""
    try:
        monitor = await get_health_monitor_instance()

        return JSONResponse(content={
            'running': monitor.running,
            'services_monitored': len(monitor.services),
            'service_configs': len(monitor.service_configs),
            'alert_rules': len(monitor.alert_rules),
            'database_path': monitor.db_path,
            'monitor_tasks': len(monitor.monitor_tasks),
            'start_time': monitor.services.get('start_time', datetime.now().isoformat())
        })

    except Exception as e:
        logger.error(f"Error getting monitoring status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/check/{service_name}")
async def manual_service_check(service_name: str):
    """Manually trigger a health check for a specific service"""
    try:
        monitor = await get_health_monitor_instance()

        if service_name not in monitor.service_configs:
            raise HTTPException(status_code=404, detail=f"Service {service_name} not configured")

        # Perform health check
        config = monitor.service_configs[service_name]
        health = await monitor._check_service_health(service_name, config)

        return JSONResponse(content={
            'success': True,
            'service': service_name,
            'health': {
                'name': health.name,
                'status': health.status,
                'response_time': health.response_time,
                'error': health.error,
                'timestamp': health.last_check.isoformat(),
                'metrics': health.metrics
            },
            'timestamp': datetime.now().isoformat()
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error performing manual check for {service_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/system/check")
async def manual_system_check():
    """Manually trigger a system metrics collection"""
    try:
        monitor = await get_health_monitor_instance()
        metrics = monitor._collect_system_metrics()

        await monitor._store_system_metrics(metrics)

        return JSONResponse(content={
            'success': True,
            'metrics': {
                'timestamp': metrics.timestamp.isoformat(),
                'cpu_percent': metrics.cpu_percent,
                'memory_percent': metrics.memory_percent,
                'memory_used': metrics.memory_used,
                'memory_total': metrics.memory_total,
                'disk_usage': metrics.disk_usage,
                'network_io': metrics.network_io,
                'process_count': metrics.process_count,
                'load_average': metrics.load_average
            },
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error performing system check: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Helper functions
def calculate_availability(history: List[Dict[str, Any]]) -> float:
    """Calculate service availability percentage"""
    if not history:
        return 0.0

    healthy_count = len([h for h in history if h['status'] == 'healthy'])
    return (healthy_count / len(history)) * 100

def calculate_avg_response_time(history: List[Dict[str, Any]]) -> float:
    """Calculate average response time"""
    if not history:
        return 0.0

    response_times = [h['response_time'] for h in history if h['response_time'] is not None]
    return sum(response_times) / len(response_times) if response_times else 0.0

def calculate_trend(values: List[float]) -> str:
    """Calculate trend direction"""
    if len(values) < 2:
        return 'stable'

    first_half = values[:len(values)//2]
    second_half = values[len(values)//2:]

    first_avg = sum(first_half) / len(first_half)
    second_avg = sum(second_half) / len(second_half)

    if second_avg > first_avg * 1.05:
        return 'increasing'
    elif second_avg < first_avg * 0.95:
        return 'decreasing'
    else:
        return 'stable'

def calculate_overall_health(service_analytics: Dict[str, Any]) -> str:
    """Calculate overall system health status"""
    if not service_analytics:
        return 'unknown'

    availabilities = [data['availability'] for data in service_analytics.values()]
    avg_availability = sum(availabilities) / len(availabilities)

    if avg_availability >= 99:
        return 'excellent'
    elif avg_availability >= 95:
        return 'good'
    elif avg_availability >= 90:
        return 'fair'
    else:
        return 'poor'

# Analytics API endpoints
@router.get("/analytics/summary")
async def get_analytics_summary():
    """Get comprehensive analytics summary"""
    try:
        analytics = get_performance_analytics()
        summary = await analytics.get_performance_summary()
        return JSONResponse(content=summary)
    except Exception as e:
        logger.error(f"Error getting analytics summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/predictions")
async def get_performance_predictions(
    service_name: str,
    metric_types: str = Query(None, description="Comma-separated list of metric types")
):
    """Get performance predictions for a service"""
    try:
        analytics = get_performance_analytics()

        metrics = metric_types.split(',') if metric_types else None
        predictions = await analytics.get_performance_predictions(service_name, metrics)
        return JSONResponse(content=predictions)
    except Exception as e:
        logger.error(f"Error getting performance predictions for {service_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/optimize/{service_name}")
async def get_optimization_recommendations(service_name: str):
    """Get optimization recommendations for a service"""
    try:
        analytics = get_performance_analytics()
        recommendations = await analytics.optimize_performance(service_name)
        return JSONResponse(content=recommendations)
    except Exception as e:
        logger.error(f"Error getting optimization recommendations for {service_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/export")
async def export_performance_report(
    service_name: str = Query(None, description="Service name (optional)"),
    format: str = Query("json", description="Export format (json, csv)")
):
    """Export performance report"""
    try:
        analytics = get_performance_analytics()
        report = await analytics.export_performance_report(service_name, format)

        if format == "json":
            return JSONResponse(content=json.loads(report))
        else:
            return JSONResponse(content={"report": report})
    except Exception as e:
        logger.error(f"Error exporting performance report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analytics/metrics/{service_name}")
async def collect_service_metrics(
    service_name: str,
    metrics_data: Dict[str, Any]
):
    """Collect performance metrics for a service"""
    try:
        analytics = get_performance_analytics()
        await analytics.collect_metrics(service_name, metrics_data)
        return JSONResponse(content={"success": True, "message": "Metrics collected"})
    except Exception as e:
        logger.error(f"Error collecting metrics for {service_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analytics/cleanup")
async def cleanup_old_data(
    days_to_keep: int = Query(30, ge=1, le=365, description="Days of data to keep (1-365)")
):
    """Clean up old performance data"""
    try:
        analytics = get_performance_analytics()
        result = await analytics.cleanup_old_data(days_to_keep)
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Error cleaning up old data: {e}")
        raise HTTPException(status_code=500, detail=str(e))