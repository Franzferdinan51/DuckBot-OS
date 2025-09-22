#!/usr/bin/env python3
"""
DuckBot Health Analytics Dashboard
Real-time health monitoring, analytics, and visualization interface
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import sqlite3

# Local imports
from duckbot.core.health_predictive_maintenance import (
    HealthDatabase, MonitoringDatabase, HealthStatus,
    HealthMaintenanceManager, health_maintenance_manager
)

logger = logging.getLogger(__name__)

class AnalyticsTimeframe(Enum):
    REALTIME = "realtime"
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"

class AlertSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class HealthMetric:
    """Health metric with trend analysis"""
    name: str
    current_value: float
    trend: float  # positive = increasing, negative = decreasing
    unit: str
    threshold_warning: Optional[float] = None
    threshold_critical: Optional[float] = None
    status: HealthStatus = HealthStatus.HEALTHY
    last_updated: datetime = None

@dataclass
class ComponentHealth:
    """Component health summary"""
    name: str
    status: HealthStatus
    score: float
    response_time: float
    issues_count: int
    last_check: datetime
    metrics: Dict[str, Any]

@dataclass
class SystemHealthSummary:
    """Complete system health summary"""
    overall_score: float
    overall_status: HealthStatus
    total_components: int
    healthy_components: int
    degraded_components: int
    unhealthy_components: int
    critical_issues: int
    last_updated: datetime
    component_health: List[ComponentHealth]
    system_metrics: List[HealthMetric]
    active_alerts: List[Dict]
    pending_maintenance: List[Dict]

@dataclass
class AnalyticsReport:
    """Analytics report with insights and recommendations"""
    timeframe: AnalyticsTimeframe
    generated_at: datetime
    health_score_trend: List[float]
    component_performance: Dict[str, float]
    resource_usage_summary: Dict[str, Dict[str, float]]
    prediction_summary: List[Dict]
    maintenance_summary: Dict[str, int]
    recommendations: List[str]
    key_insights: List[str]

class HealthAnalyticsEngine:
    """Analytics engine for health data processing and insights"""

    def __init__(self, health_db: HealthDatabase, monitoring_db: MonitoringDatabase):
        self.health_db = health_db
        self.monitoring_db = monitoring_db
        self.cache_timeout = 300  # 5 minutes
        self.cached_data = {}

    async def generate_health_summary(self) -> SystemHealthSummary:
        """Generate complete system health summary"""
        try:
            # Get recent health check results
            recent_health = self._get_recent_health_results()

            # Get current system metrics
            system_metrics = await self._get_current_system_metrics()

            # Get active alerts
            active_alerts = self.monitoring_db.get_active_alerts()

            # Get pending maintenance
            pending_maintenance = self.health_db.get_pending_maintenance_actions()

            # Calculate overall metrics
            overall_score = self._calculate_overall_score(recent_health)
            overall_status = self._determine_overall_status(overall_score, recent_health)

            # Component health breakdown
            component_health = self._generate_component_health(recent_health)

            # Count components by status
            total_components = len(component_health)
            healthy_components = sum(1 for c in component_health if c.status == HealthStatus.HEALTHY)
            degraded_components = sum(1 for c in component_health if c.status == HealthStatus.DEGRADED)
            unhealthy_components = sum(1 for c in component_health if c.status == HealthStatus.UNHEALTHY)
            critical_issues = sum(1 for c in component_health if c.status == HealthStatus.UNHEALTHY and c.score < 0.3)

            summary = SystemHealthSummary(
                overall_score=overall_score,
                overall_status=overall_status,
                total_components=total_components,
                healthy_components=healthy_components,
                degraded_components=degraded_components,
                unhealthy_components=unhealthy_components,
                critical_issues=critical_issues,
                last_updated=datetime.now(),
                component_health=component_health,
                system_metrics=system_metrics,
                active_alerts=active_alerts,
                pending_maintenance=pending_maintenance
            )

            # Cache the result
            self.cached_data['health_summary'] = {
                'data': summary,
                'timestamp': datetime.now()
            }

            return summary

        except Exception as e:
            logger.error(f"Error generating health summary: {e}")
            raise

    async def generate_analytics_report(self, timeframe: AnalyticsTimeframe) -> AnalyticsReport:
        """Generate detailed analytics report for specified timeframe"""
        try:
            generated_at = datetime.now()

            # Get time range
            start_time, end_time = self._get_time_range(timeframe)

            # Health score trend
            health_score_trend = self._get_health_score_trend(start_time, end_time)

            # Component performance
            component_performance = self._get_component_performance(start_time, end_time)

            # Resource usage summary
            resource_usage_summary = self._get_resource_usage_summary(start_time, end_time)

            # Prediction summary
            prediction_summary = self.health_db.get_recent_predictions(
                hours=self._timeframe_to_hours(timeframe)
            )

            # Maintenance summary
            maintenance_summary = self._get_maintenance_summary(start_time, end_time)

            # Generate recommendations
            recommendations = self._generate_recommendations(
                health_score_trend, component_performance, resource_usage_summary
            )

            # Generate key insights
            key_insights = self._generate_key_insights(
                health_score_trend, component_performance, resource_usage_summary
            )

            return AnalyticsReport(
                timeframe=timeframe,
                generated_at=generated_at,
                health_score_trend=health_score_trend,
                component_performance=component_performance,
                resource_usage_summary=resource_usage_summary,
                prediction_summary=prediction_summary,
                maintenance_summary=maintenance_summary,
                recommendations=recommendations,
                key_insights=key_insights
            )

        except Exception as e:
            logger.error(f"Error generating analytics report: {e}")
            raise

    async def get_real_time_metrics(self) -> List[HealthMetric]:
        """Get real-time system metrics with trend analysis"""
        try:
            metrics = []

            # CPU metrics
            cpu_metric = await self._get_cpu_metric_with_trend()
            metrics.append(cpu_metric)

            # Memory metrics
            memory_metric = await self._get_memory_metric_with_trend()
            metrics.append(memory_metric)

            # Disk metrics
            disk_metric = await self._get_disk_metric_with_trend()
            metrics.append(disk_metric)

            # Network metrics
            network_metric = await self._get_network_metric_with_trend()
            metrics.append(network_metric)

            # AI response time metrics
            ai_metric = await self._get_ai_response_metric_with_trend()
            metrics.append(ai_metric)

            return metrics

        except Exception as e:
            logger.error(f"Error getting real-time metrics: {e}")
            return []

    async def get_health_trends(self, timeframe: AnalyticsTimeframe) -> Dict[str, List[float]]:
        """Get health trends for all components over specified timeframe"""
        try:
            start_time, end_time = self._get_time_range(timeframe)
            trends = {}

            # Get trends for each component
            components = ['Database', 'AI Models', 'System Resources', 'Network Connectivity',
                         'Disk Space', 'Memory Usage', 'CPU Performance']

            for component in components:
                trend_data = self._get_component_health_trend(component, start_time, end_time)
                trends[component] = trend_data

            return trends

        except Exception as e:
            logger.error(f"Error getting health trends: {e}")
            return {}

    async def get_prediction_insights(self) -> Dict[str, Any]:
        """Get prediction insights and risk assessment"""
        try:
            predictions = self.health_db.get_recent_predictions(hours=24)

            insights = {
                'total_predictions': len(predictions),
                'high_risk_predictions': len([p for p in predictions if p.get('probability', 0) > 0.8]),
                'component_risk_scores': {},
                'risk_categories': {
                    'resource_exhaustion': 0,
                    'performance_degradation': 0,
                    'component_failure': 0,
                    'maintenance_needed': 0
                },
                'urgent_actions': [],
                'prevention_recommendations': []
            }

            # Analyze predictions by component
            for prediction in predictions:
                component = prediction.get('component', 'Unknown')
                probability = prediction.get('probability', 0)
                prediction_type = prediction.get('prediction_type', 'Unknown')

                # Component risk score
                if component not in insights['component_risk_scores']:
                    insights['component_risk_scores'][component] = 0
                insights['component_risk_scores'][component] = max(
                    insights['component_risk_scores'][component], probability
                )

                # Risk categories
                if prediction_type in insights['risk_categories']:
                    insights['risk_categories'][prediction_type] += 1

                # Urgent actions (high probability predictions)
                if probability > 0.8:
                    insights['urgent_actions'].append({
                        'component': component,
                        'type': prediction_type,
                        'probability': probability,
                        'timeframe': prediction.get('timeframe', 'unknown'),
                        'actions': json.loads(prediction.get('recommended_actions', '[]'))
                    })

            # Generate prevention recommendations
            insights['prevention_recommendations'] = self._generate_prevention_recommendations(insights)

            return insights

        except Exception as e:
            logger.error(f"Error getting prediction insights: {e}")
            return {}

    async def get_maintenance_dashboard(self) -> Dict[str, Any]:
        """Get maintenance dashboard data"""
        try:
            pending_maintenance = self.health_db.get_pending_maintenance_actions()

            dashboard = {
                'pending_actions': len(pending_maintenance),
                'actions_by_priority': {
                    'critical': 0,
                    'high': 0,
                    'medium': 0,
                    'low': 0
                },
                'actions_by_type': {},
                'estimated_total_duration': 0,
                'scheduled_actions': [],
                'recent_completions': [],
                'automation_status': health_maintenance_manager.automation_system.automation_active
            }

            # Analyze pending actions
            for action in pending_maintenance:
                priority = action.get('priority', 'low')
                action_type = action.get('maintenance_type', 'unknown')
                duration = action.get('estimated_duration_minutes', 0)

                dashboard['actions_by_priority'][priority] += 1
                dashboard['estimated_total_duration'] += duration

                if action_type not in dashboard['actions_by_type']:
                    dashboard['actions_by_type'][action_type] = 0
                dashboard['actions_by_type'][action_type] += 1

                if action.get('scheduled_for'):
                    dashboard['scheduled_actions'].append(action)

            return dashboard

        except Exception as e:
            logger.error(f"Error getting maintenance dashboard: {e}")
            return {}

    def _get_recent_health_results(self) -> List[Dict]:
        """Get recent health check results from database"""
        try:
            with sqlite3.connect(self.health_db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM health_check_results
                    ORDER BY last_check DESC
                    LIMIT 100
                ''')
                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting recent health results: {e}")
            return []

    async def _get_current_system_metrics(self) -> List[HealthMetric]:
        """Get current system metrics with trend analysis"""
        return await self.get_real_time_metrics()

    def _calculate_overall_score(self, health_results: List[Dict]) -> float:
        """Calculate overall health score"""
        if not health_results:
            return 0.0

        # Weight critical components more heavily
        weights = {
            'Database': 0.2,
            'AI Models': 0.2,
            'System Resources': 0.15,
            'Network Connectivity': 0.1,
            'WebUI': 0.1,
            'LM Studio': 0.1,
            'Disk Space': 0.05,
            'Memory Usage': 0.05,
            'CPU Performance': 0.05
        }

        weighted_score = 0.0
        total_weight = 0.0

        for result in health_results:
            component = result.get('component_name', '')
            score = result.get('score', 0.0)
            weight = weights.get(component, 0.05)

            weighted_score += score * weight
            total_weight += weight

        return weighted_score / total_weight if total_weight > 0 else 0.0

    def _determine_overall_status(self, score: float, health_results: List[Dict]) -> HealthStatus:
        """Determine overall system health status"""
        if score >= 0.8:
            return HealthStatus.HEALTHY
        elif score >= 0.6:
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.UNHEALTHY

    def _generate_component_health(self, health_results: List[Dict]) -> List[ComponentHealth]:
        """Generate component health summaries"""
        component_health = []

        for result in health_results:
            component = ComponentHealth(
                name=result.get('component_name', ''),
                status=HealthStatus(result.get('status', 'unknown')),
                score=result.get('score', 0.0),
                response_time=result.get('response_time_ms', 0.0),
                issues_count=len(json.loads(result.get('issues', '[]'))),
                last_check=datetime.fromisoformat(result.get('last_check', datetime.now().isoformat())),
                metrics=json.loads(result.get('metrics', '{}'))
            )
            component_health.append(component)

        return component_health

    async def _get_cpu_metric_with_trend(self) -> HealthMetric:
        """Get CPU metric with trend analysis"""
        try:
            # Get current CPU usage
            import psutil
            current_cpu = psutil.cpu_percent(interval=1)

            # Get trend from historical data
            trend = self._get_metric_trend('cpu_percent', hours=1)

            return HealthMetric(
                name="CPU Usage",
                current_value=current_cpu,
                trend=trend,
                unit="%",
                threshold_warning=80.0,
                threshold_critical=90.0,
                status=self._metric_status(current_cpu, 80.0, 90.0),
                last_updated=datetime.now()
            )
        except Exception as e:
            logger.error(f"Error getting CPU metric: {e}")
            return HealthMetric("CPU Usage", 0.0, 0.0, "%")

    async def _get_memory_metric_with_trend(self) -> HealthMetric:
        """Get memory metric with trend analysis"""
        try:
            import psutil
            memory = psutil.virtual_memory()
            current_memory = memory.percent

            trend = self._get_metric_trend('memory_percent', hours=1)

            return HealthMetric(
                name="Memory Usage",
                current_value=current_memory,
                trend=trend,
                unit="%",
                threshold_warning=80.0,
                threshold_critical=90.0,
                status=self._metric_status(current_memory, 80.0, 90.0),
                last_updated=datetime.now()
            )
        except Exception as e:
            logger.error(f"Error getting memory metric: {e}")
            return HealthMetric("Memory Usage", 0.0, 0.0, "%")

    async def _get_disk_metric_with_trend(self) -> HealthMetric:
        """Get disk metric with trend analysis"""
        try:
            import psutil
            disk = psutil.disk_usage('/')
            current_disk = (disk.used / disk.total) * 100

            trend = self._get_metric_trend('disk_percent', hours=1)

            return HealthMetric(
                name="Disk Usage",
                current_value=current_disk,
                trend=trend,
                unit="%",
                threshold_warning=85.0,
                threshold_critical=95.0,
                status=self._metric_status(current_disk, 85.0, 95.0),
                last_updated=datetime.now()
            )
        except Exception as e:
            logger.error(f"Error getting disk metric: {e}")
            return HealthMetric("Disk Usage", 0.0, 0.0, "%")

    async def _get_network_metric_with_trend(self) -> HealthMetric:
        """Get network metric with trend analysis"""
        try:
            # Get current network I/O
            import psutil
            net_io = psutil.net_io_counters()

            # Calculate network usage as percentage of available bandwidth
            # This is a simplified metric - in practice would use actual bandwidth
            network_usage = 50.0  # Placeholder

            trend = self._get_metric_trend('network_bytes_sent_per_sec', hours=1)

            return HealthMetric(
                name="Network Usage",
                current_value=network_usage,
                trend=trend,
                unit="%",
                threshold_warning=80.0,
                threshold_critical=90.0,
                status=self._metric_status(network_usage, 80.0, 90.0),
                last_updated=datetime.now()
            )
        except Exception as e:
            logger.error(f"Error getting network metric: {e}")
            return HealthMetric("Network Usage", 0.0, 0.0, "%")

    async def _get_ai_response_metric_with_trend(self) -> HealthMetric:
        """Get AI response time metric with trend analysis"""
        try:
            # Get recent AI response times
            ai_metrics = self.monitoring_db.get_system_metrics(
                name="ai_response_time_ms",
                start_time=datetime.now() - timedelta(hours=1),
                limit=100
            )

            if ai_metrics:
                current_response = sum(m['value'] for m in ai_metrics) / len(ai_metrics)
            else:
                current_response = 1000.0  # Default

            trend = self._get_metric_trend('ai_response_time_ms', hours=1)

            return HealthMetric(
                name="AI Response Time",
                current_value=current_response,
                trend=trend,
                unit="ms",
                threshold_warning=3000.0,
                threshold_critical=5000.0,
                status=self._metric_status(current_response, 3000.0, 5000.0, invert=True),
                last_updated=datetime.now()
            )
        except Exception as e:
            logger.error(f"Error getting AI response metric: {e}")
            return HealthMetric("AI Response Time", 0.0, 0.0, "ms")

    def _get_metric_trend(self, metric_name: str, hours: int) -> float:
        """Calculate trend for a specific metric"""
        try:
            start_time = datetime.now() - timedelta(hours=hours)
            metrics = self.monitoring_db.get_system_metrics(
                name=metric_name,
                start_time=start_time,
                limit=100
            )

            if len(metrics) < 2:
                return 0.0

            values = [m['value'] for m in metrics]
            return self._calculate_trend_slope(values)

        except Exception as e:
            logger.error(f"Error calculating metric trend: {e}")
            return 0.0

    def _calculate_trend_slope(self, values: List[float]) -> float:
        """Calculate trend slope using simple linear regression"""
        if len(values) < 2:
            return 0.0

        x = list(range(len(values)))
        y = values

        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(xi * yi for xi, yi in zip(x, y))
        sum_x2 = sum(xi * xi for xi in x)

        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        return slope

    def _metric_status(self, value: float, warning: float, critical: float, invert: bool = False) -> HealthStatus:
        """Determine metric status based on thresholds"""
        if invert:
            if value <= warning:
                return HealthStatus.HEALTHY
            elif value <= critical:
                return HealthStatus.DEGRADED
            else:
                return HealthStatus.UNHEALTHY
        else:
            if value <= warning:
                return HealthStatus.HEALTHY
            elif value <= critical:
                return HealthStatus.DEGRADED
            else:
                return HealthStatus.UNHEALTHY

    def _get_time_range(self, timeframe: AnalyticsTimeframe) -> tuple:
        """Get start and end time for timeframe"""
        end_time = datetime.now()

        if timeframe == AnalyticsTimeframe.HOUR:
            start_time = end_time - timedelta(hours=1)
        elif timeframe == AnalyticsTimeframe.DAY:
            start_time = end_time - timedelta(days=1)
        elif timeframe == AnalyticsTimeframe.WEEK:
            start_time = end_time - timedelta(weeks=1)
        elif timeframe == AnalyticsTimeframe.MONTH:
            start_time = end_time - timedelta(days=30)
        elif timeframe == AnalyticsTimeframe.YEAR:
            start_time = end_time - timedelta(days=365)
        else:  # REALTIME
            start_time = end_time - timedelta(minutes=5)

        return start_time, end_time

    def _timeframe_to_hours(self, timeframe: AnalyticsTimeframe) -> int:
        """Convert timeframe to hours"""
        timeframe_hours = {
            AnalyticsTimeframe.HOUR: 1,
            AnalyticsTimeframe.DAY: 24,
            AnalyticsTimeframe.WEEK: 168,
            AnalyticsTimeframe.MONTH: 720,
            AnalyticsTimeframe.YEAR: 8760,
            AnalyticsTimeframe.REALTIME: 0
        }
        return timeframe_hours.get(timeframe, 24)

    def _get_health_score_trend(self, start_time: datetime, end_time: datetime) -> List[float]:
        """Get health score trend over time"""
        try:
            with sqlite3.connect(self.health_db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT component_name, score, last_check
                    FROM health_check_results
                    WHERE last_check BETWEEN ? AND ?
                    ORDER BY last_check
                ''', (start_time.isoformat(), end_time.isoformat()))

                results = cursor.fetchall()

                # Group by time periods and calculate average scores
                time_buckets = {}
                for result in results:
                    timestamp = datetime.fromisoformat(result[2])
                    time_key = timestamp.strftime('%Y-%m-%d %H:00:00')

                    if time_key not in time_buckets:
                        time_buckets[time_key] = []
                    time_buckets[time_key].append(result[1])

                # Calculate average scores for each time bucket
                trend_data = []
                for time_key in sorted(time_buckets.keys()):
                    avg_score = sum(time_buckets[time_key]) / len(time_buckets[time_key])
                    trend_data.append(avg_score)

                return trend_data

        except Exception as e:
            logger.error(f"Error getting health score trend: {e}")
            return []

    def _get_component_performance(self, start_time: datetime, end_time: datetime) -> Dict[str, float]:
        """Get component performance metrics"""
        try:
            with sqlite3.connect(self.health_db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT component_name, AVG(score), AVG(response_time_ms)
                    FROM health_check_results
                    WHERE last_check BETWEEN ? AND ?
                    GROUP BY component_name
                ''', (start_time.isoformat(), end_time.isoformat()))

                results = cursor.fetchall()

                performance = {}
                for component_name, avg_score, avg_response_time in results:
                    # Calculate performance score (balance of score and response time)
                    response_score = max(0, 1.0 - (avg_response_time / 10000))  # Normalize response time
                    performance_score = (avg_score * 0.7 + response_score * 0.3)
                    performance[component_name] = performance_score

                return performance

        except Exception as e:
            logger.error(f"Error getting component performance: {e}")
            return {}

    def _get_resource_usage_summary(self, start_time: datetime, end_time: datetime) -> Dict[str, Dict[str, float]]:
        """Get resource usage summary statistics"""
        try:
            metrics = ['cpu_percent', 'memory_percent', 'disk_percent']
            summary = {}

            for metric in metrics:
                data = self.monitoring_db.get_system_metrics(
                    name=metric,
                    start_time=start_time,
                    end_time=end_time
                )

                if data:
                    values = [m['value'] for m in data]
                    summary[metric] = {
                        'min': min(values),
                        'max': max(values),
                        'avg': sum(values) / len(values),
                        'current': values[0] if values else 0.0
                    }
                else:
                    summary[metric] = {'min': 0, 'max': 0, 'avg': 0, 'current': 0}

            return summary

        except Exception as e:
            logger.error(f"Error getting resource usage summary: {e}")
            return {}

    def _get_maintenance_summary(self, start_time: datetime, end_time: datetime) -> Dict[str, int]:
        """Get maintenance summary statistics"""
        try:
            with sqlite3.connect(self.health_db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT maintenance_type, COUNT(*)
                    FROM maintenance_actions
                    WHERE created_at BETWEEN ? AND ?
                    GROUP BY maintenance_type
                ''', (start_time.isoformat(), end_time.isoformat()))

                results = cursor.fetchall()

                summary = dict(results)
                return summary

        except Exception as e:
            logger.error(f"Error getting maintenance summary: {e}")
            return {}

    def _get_component_health_trend(self, component: str, start_time: datetime, end_time: datetime) -> List[float]:
        """Get health trend for a specific component"""
        try:
            with sqlite3.connect(self.health_db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT score, last_check
                    FROM health_check_results
                    WHERE component_name = ? AND last_check BETWEEN ? AND ?
                    ORDER BY last_check
                ''', (component, start_time.isoformat(), end_time.isoformat()))

                results = cursor.fetchall()
                return [result[0] for result in results]

        except Exception as e:
            logger.error(f"Error getting component health trend for {component}: {e}")
            return []

    def _generate_recommendations(self, health_trend: List[float], component_perf: Dict[str, float], resource_summary: Dict[str, Dict[str, float]]) -> List[str]:
        """Generate actionable recommendations based on analytics"""
        recommendations = []

        # Health trend recommendations
        if health_trend and len(health_trend) > 5:
            recent_trend = health_trend[-5:]
            if all(score < 0.8 for score in recent_trend):
                recommendations.append("System health consistently below 80%. Consider comprehensive maintenance.")
            elif health_trend[-1] < health_trend[0] * 0.9:  # 10% decline
                recommendations.append("Health score declining. Investigate recent changes and system load.")

        # Component performance recommendations
        for component, score in component_perf.items():
            if score < 0.7:
                recommendations.append(f"{component} performance degraded ({score:.1%}). Schedule optimization.")

        # Resource usage recommendations
        for resource, stats in resource_summary.items():
            if stats['avg'] > 80:
                recommendations.append(f"High average {resource.replace('_', ' ')} ({stats['avg']:.1f}%). Monitor closely.")
            elif stats['max'] > 95:
                recommendations.append(f"Peak {resource.replace('_', ' ')} exceeded 95%. Consider capacity planning.")

        return recommendations

    def _generate_key_insights(self, health_trend: List[float], component_perf: Dict[str, float], resource_summary: Dict[str, Dict[str, float]]) -> List[str]:
        """Generate key insights from analytics data"""
        insights = []

        # Health trend insights
        if health_trend and len(health_trend) > 1:
            trend_direction = "improving" if health_trend[-1] > health_trend[0] else "declining"
            trend_change = abs(health_trend[-1] - health_trend[0])
            insights.append(f"System health {trend_direction} by {trend_change:.1%} over the period.")

        # Best/worst performing components
        if component_perf:
            best_component = max(component_perf, key=component_perf.get)
            worst_component = min(component_perf, key=component_perf.get)
            insights.append(f"Best performing: {best_component} ({component_perf[best_component]:.1%})")
            insights.append(f"Needs attention: {worst_component} ({component_perf[worst_component]:.1%})")

        # Resource pressure insights
        high_resources = [r for r, stats in resource_summary.items() if stats['avg'] > 70]
        if high_resources:
            insights.append(f"High resource pressure on: {', '.join(high_resources)}")

        return insights

    def _generate_prevention_recommendations(self, insights: Dict[str, Any]) -> List[str]:
        """Generate prevention recommendations based on prediction insights"""
        recommendations = []

        # Resource exhaustion prevention
        if insights['risk_categories']['resource_exhaustion'] > 0:
            recommendations.append("Implement resource monitoring alerts and auto-scaling")

        # Performance degradation prevention
        if insights['risk_categories']['performance_degradation'] > 0:
            recommendations.append("Schedule regular performance optimizations and capacity reviews")

        # Component failure prevention
        if insights['risk_categories']['component_failure'] > 0:
            recommendations.append("Implement component health monitoring and redundancy")

        # Proactive maintenance
        if insights['total_predictions'] > 5:
            recommendations.append("Establish preventive maintenance schedule based on predictions")

        return recommendations

class HealthDashboardAPI:
    """REST API for health dashboard data"""

    def __init__(self, analytics_engine: HealthAnalyticsEngine):
        self.analytics_engine = analytics_engine

    async def get_health_summary(self) -> Dict[str, Any]:
        """Get current health summary"""
        summary = await self.analytics_engine.generate_health_summary()
        return asdict(summary)

    async def get_real_time_metrics(self) -> List[Dict[str, Any]]:
        """Get real-time metrics"""
        metrics = await self.analytics_engine.get_real_time_metrics()
        return [asdict(metric) for metric in metrics]

    async def get_health_trends(self, timeframe: str = "day") -> Dict[str, Any]:
        """Get health trends for specified timeframe"""
        try:
            tf = AnalyticsTimeframe(timeframe)
            trends = await self.analytics_engine.get_health_trends(tf)
            return {"timeframe": timeframe, "trends": trends}
        except ValueError:
            return {"error": f"Invalid timeframe: {timeframe}"}

    async def get_analytics_report(self, timeframe: str = "day") -> Dict[str, Any]:
        """Get analytics report for specified timeframe"""
        try:
            tf = AnalyticsTimeframe(timeframe)
            report = await self.analytics_engine.generate_analytics_report(tf)
            report_dict = asdict(report)
            report_dict['timeframe'] = timeframe
            return report_dict
        except ValueError:
            return {"error": f"Invalid timeframe: {timeframe}"}

    async def get_prediction_insights(self) -> Dict[str, Any]:
        """Get prediction insights"""
        return await self.analytics_engine.get_prediction_insights()

    async def get_maintenance_dashboard(self) -> Dict[str, Any]:
        """Get maintenance dashboard data"""
        return await self.analytics_engine.get_maintenance_dashboard()

    async def trigger_health_check(self) -> Dict[str, Any]:
        """Trigger immediate health check"""
        try:
            results = await health_maintenance_manager.run_immediate_health_check()
            return {
                "status": "success",
                "timestamp": datetime.now().isoformat(),
                "components_checked": len(results),
                "overall_score": health_maintenance_manager.health_checker.get_overall_health_score(results)
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def get_system_status(self) -> Dict[str, Any]:
        """Get complete system status"""
        return health_maintenance_manager.get_system_status()

# Global instances for easy access
health_analytics_engine = HealthAnalyticsEngine(
    HealthDatabase(), MonitoringDatabase()
)
health_dashboard_api = HealthDashboardAPI(health_analytics_engine)

# FastAPI integration functions
def add_health_dashboard_routes(app):
    """Add health dashboard routes to FastAPI app"""
    from fastapi import APIRouter, HTTPException

    router = APIRouter(prefix="/api/health", tags=["health"])

    @router.get("/summary")
    async def get_health_summary():
        return await health_dashboard_api.get_health_summary()

    @router.get("/metrics")
    async def get_real_time_metrics():
        return await health_dashboard_api.get_real_time_metrics()

    @router.get("/trends/{timeframe}")
    async def get_health_trends(timeframe: str = "day"):
        return await health_dashboard_api.get_health_trends(timeframe)

    @router.get("/analytics/{timeframe}")
    async def get_analytics_report(timeframe: str = "day"):
        return await health_dashboard_api.get_analytics_report(timeframe)

    @router.get("/predictions")
    async def get_prediction_insights():
        return await health_dashboard_api.get_prediction_insights()

    @router.get("/maintenance")
    async def get_maintenance_dashboard():
        return await health_dashboard_api.get_maintenance_dashboard()

    @router.post("/check")
    async def trigger_health_check():
        return await health_dashboard_api.trigger_health_check()

    @router.get("/status")
    async def get_system_status():
        return await health_dashboard_api.get_system_status()

    app.include_router(router)