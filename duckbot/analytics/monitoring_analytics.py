#!/usr/bin/env python3
"""
DuckBot Monitoring Analytics System
Advanced analytics, data export, and reporting capabilities
"""

import asyncio
import json
import logging
import os
import sqlite3
import csv
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import statistics
from dataclasses import dataclass, asdict
from enum import Enum
import threading
import time

# Local imports
from duckbot.core.monitoring_system import (
    get_monitoring, MonitoringDatabase, AlertLevel, HealthStatus
)

logger = logging.getLogger(__name__)

class ReportFormat(Enum):
    JSON = "json"
    CSV = "csv"
    EXCEL = "excel"
    PDF = "pdf"
    HTML = "html"

class AnalyticsPeriod(Enum):
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"

@dataclass
class AnalyticsData:
    """Container for analytics data"""
    period: AnalyticsPeriod
    start_time: datetime
    end_time: datetime
    total_records: int
    summary: Dict[str, Any]
    trends: Dict[str, List[float]]
    anomalies: List[Dict[str, Any]]
    recommendations: List[str]

class PerformanceAnalyzer:
    """Analyzes system and agent performance metrics"""

    def __init__(self, database: MonitoringDatabase):
        self.database = database

    def analyze_system_performance(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Analyze system performance over time period"""
        try:
            # Get system metrics for the period
            metrics = self.database.get_system_metrics(
                start_time=start_time,
                end_time=end_time,
                limit=10000
            )

            if not metrics:
                return {"error": "No metrics found for the specified period"}

            # Group by metric name
            metric_groups = {}
            for metric in metrics:
                name = metric["name"]
                if name not in metric_groups:
                    metric_groups[name] = []
                metric_groups[name].append(metric)

            analysis = {}
            for name, values in metric_groups.items():
                numeric_values = [v["value"] for v in values if isinstance(v["value"], (int, float))]

                if numeric_values:
                    analysis[name] = {
                        "min": min(numeric_values),
                        "max": max(numeric_values),
                        "avg": statistics.mean(numeric_values),
                        "median": statistics.median(numeric_values),
                        "std_dev": statistics.stdev(numeric_values) if len(numeric_values) > 1 else 0,
                        "percentile_95": np.percentile(numeric_values, 95) if numeric_values else 0,
                        "percentile_99": np.percentile(numeric_values, 99) if numeric_values else 0,
                        "trend": self._calculate_trend(numeric_values),
                        "data_points": len(numeric_values)
                    }

            return {
                "period": {
                    "start": start_time.isoformat(),
                    "end": end_time.isoformat(),
                    "duration_hours": (end_time - start_time).total_seconds() / 3600
                },
                "metrics_analysis": analysis,
                "summary": self._generate_performance_summary(analysis),
                "anomalies": self._detect_anomalies(analysis)
            }

        except Exception as e:
            logger.error(f"Error analyzing system performance: {e}")
            return {"error": str(e)}

    def analyze_agent_performance(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Analyze agent performance over time period"""
        try:
            # Get agent metrics from database
            with sqlite3.connect(self.database.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT agent_id, agent_type, response_time_ms, success,
                           model_used, tokens_used, timestamp
                    FROM agent_metrics
                    WHERE timestamp BETWEEN ? AND ?
                    ORDER BY timestamp
                ''', (start_time.isoformat(), end_time.isoformat()))

                columns = [desc[0] for desc in cursor.description]
                metrics = [dict(zip(columns, row)) for row in cursor.fetchall()]

            if not metrics:
                return {"error": "No agent metrics found for the specified period"}

            # Group by agent
            agent_groups = {}
            for metric in metrics:
                agent_id = metric["agent_id"]
                if agent_id not in agent_groups:
                    agent_groups[agent_id] = []
                agent_groups[agent_id].append(metric)

            analysis = {}
            for agent_id, values in agent_groups.items():
                response_times = [v["response_time_ms"] for v in values if v["response_time_ms"]]
                success_rate = sum(1 for v in values if v["success"]) / len(values) if values else 0

                analysis[agent_id] = {
                    "agent_type": values[0]["agent_type"] if values else "unknown",
                    "total_requests": len(values),
                    "successful_requests": sum(1 for v in values if v["success"]),
                    "failed_requests": sum(1 for v in values if not v["success"]),
                    "success_rate": success_rate,
                    "avg_response_time": statistics.mean(response_times) if response_times else 0,
                    "min_response_time": min(response_times) if response_times else 0,
                    "max_response_time": max(response_times) if response_times else 0,
                    "total_tokens": sum(v["tokens_used"] for v in values if v["tokens_used"]),
                    "models_used": list(set(v["model_used"] for v in values if v["model_used"])),
                    "error_patterns": self._analyze_error_patterns(values)
                }

            return {
                "period": {
                    "start": start_time.isoformat(),
                    "end": end_time.isoformat(),
                    "duration_hours": (end_time - start_time).total_seconds() / 3600
                },
                "agents_analysis": analysis,
                "summary": self._generate_agent_summary(analysis)
            }

        except Exception as e:
            logger.error(f"Error analyzing agent performance: {e}")
            return {"error": str(e)}

    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction"""
        if len(values) < 2:
            return "stable"

        # Simple linear regression for trend
        x = list(range(len(values)))
        y = values

        try:
            slope = np.polyfit(x, y, 1)[0]
            if slope > 0.1:
                return "increasing"
            elif slope < -0.1:
                return "decreasing"
            else:
                return "stable"
        except:
            return "unknown"

    def _generate_performance_summary(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate performance summary"""
        summary = {
            "overall_status": "healthy",
            "critical_issues": [],
            "warnings": [],
            "recommendations": []
        }

        # Check CPU usage
        if "cpu_percent" in analysis:
            cpu_avg = analysis["cpu_percent"]["avg"]
            if cpu_avg > 90:
                summary["critical_issues"].append(f"High CPU usage: {cpu_avg:.1f}% average")
                summary["overall_status"] = "critical"
            elif cpu_avg > 75:
                summary["warnings"].append(f"Elevated CPU usage: {cpu_avg:.1f}% average")
                summary["overall_status"] = "warning"

        # Check memory usage
        if "memory_percent" in analysis:
            memory_avg = analysis["memory_percent"]["avg"]
            if memory_avg > 85:
                summary["critical_issues"].append(f"High memory usage: {memory_avg:.1f}% average")
                if summary["overall_status"] != "critical":
                    summary["overall_status"] = "critical"
            elif memory_avg > 70:
                summary["warnings"].append(f"Elevated memory usage: {memory_avg:.1f}% average")
                if summary["overall_status"] == "healthy":
                    summary["overall_status"] = "warning"

        # Generate recommendations
        if summary["overall_status"] == "critical":
            summary["recommendations"].append("Immediate investigation required for critical resource usage")
        elif summary["overall_status"] == "warning":
            summary["recommendations"].append("Monitor resource usage and consider optimization")

        return summary

    def _generate_agent_summary(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate agent performance summary"""
        total_requests = sum(agent["total_requests"] for agent in analysis.values())
        total_successful = sum(agent["successful_requests"] for agent in analysis.values())
        overall_success_rate = total_successful / total_requests if total_requests > 0 else 0

        avg_response_time = statistics.mean([
            agent["avg_response_time"] for agent in analysis.values()
            if agent["avg_response_time"] > 0
        ]) if analysis else 0

        return {
            "total_agents": len(analysis),
            "total_requests": total_requests,
            "total_successful": total_successful,
            "overall_success_rate": overall_success_rate,
            "average_response_time": avg_response_time,
            "best_performing_agent": max(
                analysis.items(),
                key=lambda x: x[1]["success_rate"],
                default=("none", {"success_rate": 0})
            )[0],
            "slowest_agent": max(
                analysis.items(),
                key=lambda x: x[1]["avg_response_time"],
                default=("none", {"avg_response_time": 0})
            )[0]
        }

    def _detect_anomalies(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect anomalies in performance data"""
        anomalies = []

        for metric_name, data in analysis.items():
            if data["std_dev"] > 0:
                # Check for values beyond 3 standard deviations
                threshold = data["avg"] + (3 * data["std_dev"])
                if data["max"] > threshold:
                    anomalies.append({
                        "metric": metric_name,
                        "type": "high_outlier",
                        "value": data["max"],
                        "threshold": threshold,
                        "severity": "warning"
                    })

        return anomalies

    def _analyze_error_patterns(self, values: List[Dict]) -> Dict[str, Any]:
        """Analyze error patterns in agent responses"""
        failed_requests = [v for v in values if not v["success"]]

        if not failed_requests:
            return {"total_failures": 0, "error_types": {}, "error_timeline": []}

        error_types = {}
        for request in failed_requests:
            error_msg = request.get("error_message", "unknown")
            error_types[error_msg] = error_types.get(error_msg, 0) + 1

        return {
            "total_failures": len(failed_requests),
            "error_types": error_types,
            "failure_rate": len(failed_requests) / len(values)
        }

class DataExporter:
    """Exports monitoring data in various formats"""

    def __init__(self, database: MonitoringDatabase):
        self.database = database
        self.export_dir = Path("exports")
        self.export_dir.mkdir(exist_ok=True)

    def export_system_metrics(self, start_time: datetime, end_time: datetime,
                             format: ReportFormat = ReportFormat.CSV) -> str:
        """Export system metrics data"""
        try:
            metrics = self.database.get_system_metrics(
                start_time=start_time,
                end_time=end_time,
                limit=50000
            )

            if not metrics:
                raise ValueError("No metrics data found for the specified period")

            filename = self._generate_filename("system_metrics", format)
            filepath = self.export_dir / filename

            if format == ReportFormat.CSV:
                self._export_csv(metrics, filepath)
            elif format == ReportFormat.JSON:
                self._export_json(metrics, filepath)
            elif format == ReportFormat.EXCEL:
                self._export_excel(metrics, filepath)
            elif format == ReportFormat.HTML:
                self._export_html(metrics, filepath, "System Metrics Export")

            logger.info(f"System metrics exported to: {filepath}")
            return str(filepath)

        except Exception as e:
            logger.error(f"Error exporting system metrics: {e}")
            raise

    def export_agent_metrics(self, start_time: datetime, end_time: datetime,
                            format: ReportFormat = ReportFormat.CSV) -> str:
        """Export agent metrics data"""
        try:
            with sqlite3.connect(self.database.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM agent_metrics
                    WHERE timestamp BETWEEN ? AND ?
                    ORDER BY timestamp
                ''', (start_time.isoformat(), end_time.isoformat()))

                columns = [desc[0] for desc in cursor.description]
                metrics = [dict(zip(columns, row)) for row in cursor.fetchall()]

            if not metrics:
                raise ValueError("No agent metrics data found for the specified period")

            filename = self._generate_filename("agent_metrics", format)
            filepath = self.export_dir / filename

            if format == ReportFormat.CSV:
                self._export_csv(metrics, filepath)
            elif format == ReportFormat.JSON:
                self._export_json(metrics, filepath)
            elif format == ReportFormat.EXCEL:
                self._export_excel(metrics, filepath)
            elif format == ReportFormat.HTML:
                self._export_html(metrics, filepath, "Agent Metrics Export")

            logger.info(f"Agent metrics exported to: {filepath}")
            return str(filepath)

        except Exception as e:
            logger.error(f"Error exporting agent metrics: {e}")
            raise

    def export_alerts(self, start_time: datetime, end_time: datetime,
                     format: ReportFormat = ReportFormat.CSV) -> str:
        """Export alerts data"""
        try:
            with sqlite3.connect(self.database.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM alerts
                    WHERE timestamp BETWEEN ? AND ?
                    ORDER BY timestamp
                ''', (start_time.isoformat(), end_time.isoformat()))

                columns = [desc[0] for desc in cursor.description]
                alerts = [dict(zip(columns, row)) for row in cursor.fetchall()]

            if not alerts:
                raise ValueError("No alerts data found for the specified period")

            filename = self._generate_filename("alerts", format)
            filepath = self.export_dir / filename

            if format == ReportFormat.CSV:
                self._export_csv(alerts, filepath)
            elif format == ReportFormat.JSON:
                self._export_json(alerts, filepath)
            elif format == ReportFormat.EXCEL:
                self._export_excel(alerts, filepath)
            elif format == ReportFormat.HTML:
                self._export_html(alerts, filepath, "Alerts Export")

            logger.info(f"Alerts exported to: {filepath}")
            return str(filepath)

        except Exception as e:
            logger.error(f"Error exporting alerts: {e}")
            raise

    def _generate_filename(self, data_type: str, format: ReportFormat) -> str:
        """Generate filename for export"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        extensions = {
            ReportFormat.CSV: "csv",
            ReportFormat.JSON: "json",
            ReportFormat.EXCEL: "xlsx",
            ReportFormat.HTML: "html"
        }
        return f"{data_type}_export_{timestamp}.{extensions[format]}"

    def _export_csv(self, data: List[Dict], filepath: Path):
        """Export data to CSV format"""
        if not data:
            return

        df = pd.DataFrame(data)
        df.to_csv(filepath, index=False)

    def _export_json(self, data: List[Dict], filepath: Path):
        """Export data to JSON format"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)

    def _export_excel(self, data: List[Dict], filepath: Path):
        """Export data to Excel format"""
        if not data:
            return

        df = pd.DataFrame(data)
        df.to_excel(filepath, index=False)

    def _export_html(self, data: List[Dict], filepath: Path, title: str):
        """Export data to HTML format"""
        if not data:
            return

        df = pd.DataFrame(data)
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{title}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .timestamp {{ font-size: 0.8em; color: #666; }}
            </style>
        </head>
        <body>
            <h1>{title}</h1>
            <p class="timestamp">Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            {df.to_html(index=False, escape=False)}
        </body>
        </html>
        """

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)

class ReportGenerator:
    """Generates comprehensive monitoring reports"""

    def __init__(self, database: MonitoringDatabase):
        self.database = database
        self.analyzer = PerformanceAnalyzer(database)
        self.exporter = DataExporter(database)

    def generate_comprehensive_report(self, start_time: datetime, end_time: datetime) -> str:
        """Generate comprehensive monitoring report"""
        try:
            # Analyze system performance
            system_analysis = self.analyzer.analyze_system_performance(start_time, end_time)

            # Analyze agent performance
            agent_analysis = self.analyzer.analyze_agent_performance(start_time, end_time)

            # Get service health summary
            service_health = self._get_service_health_summary(start_time, end_time)

            # Get alerts summary
            alerts_summary = self._get_alerts_summary(start_time, end_time)

            # Generate report
            report = {
                "metadata": {
                    "title": "DuckBot Monitoring Report",
                    "period": {
                        "start": start_time.isoformat(),
                        "end": end_time.isoformat(),
                        "duration_days": (end_time - start_time).days
                    },
                    "generated_at": datetime.now().isoformat(),
                    "version": "1.0.0"
                },
                "executive_summary": self._generate_executive_summary(
                    system_analysis, agent_analysis, service_health, alerts_summary
                ),
                "system_performance": system_analysis,
                "agent_performance": agent_analysis,
                "service_health": service_health,
                "alerts_summary": alerts_summary,
                "recommendations": self._generate_recommendations(
                    system_analysis, agent_analysis, service_health, alerts_summary
                )
            }

            # Save report
            report_dir = Path("reports")
            report_dir.mkdir(exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_filename = f"duckbot_monitoring_report_{timestamp}.json"
            report_filepath = report_dir / report_filename

            with open(report_filepath, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, default=str)

            # Also generate HTML version
            html_report = self._generate_html_report(report)
            html_filename = f"duckbot_monitoring_report_{timestamp}.html"
            html_filepath = report_dir / html_filename

            with open(html_filepath, 'w', encoding='utf-8') as f:
                f.write(html_report)

            logger.info(f"Comprehensive report generated: {report_filepath}")
            return str(report_filepath)

        except Exception as e:
            logger.error(f"Error generating comprehensive report: {e}")
            raise

    def _get_service_health_summary(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Get service health summary"""
        try:
            with sqlite3.connect(self.database.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT service_name, status, COUNT(*) as count,
                           AVG(response_time_ms) as avg_response_time
                    FROM service_health
                    WHERE last_check BETWEEN ? AND ?
                    GROUP BY service_name, status
                ''', (start_time.isoformat(), end_time.isoformat()))

                results = cursor.fetchall()

            summary = {}
            for row in results:
                service_name, status, count, avg_response_time = row
                if service_name not in summary:
                    summary[service_name] = {
                        "total_checks": 0,
                        "healthy_checks": 0,
                        "degraded_checks": 0,
                        "unhealthy_checks": 0,
                        "avg_response_time": 0
                    }

                summary[service_name]["total_checks"] += count
                if status == "healthy":
                    summary[service_name]["healthy_checks"] += count
                elif status == "degraded":
                    summary[service_name]["degraded_checks"] += count
                elif status == "unhealthy":
                    summary[service_name]["unhealthy_checks"] += count

                if avg_response_time:
                    summary[service_name]["avg_response_time"] = avg_response_time

            return summary

        except Exception as e:
            logger.error(f"Error getting service health summary: {e}")
            return {}

    def _get_alerts_summary(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Get alerts summary"""
        try:
            with sqlite3.connect(self.database.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT level, COUNT(*) as count
                    FROM alerts
                    WHERE timestamp BETWEEN ? AND ?
                    GROUP BY level
                ''', (start_time.isoformat(), end_time.isoformat()))

                results = cursor.fetchall()

            summary = {
                "total_alerts": 0,
                "by_level": {},
                "active_alerts": 0
            }

            for level, count in results:
                summary["by_level"][level] = count
                summary["total_alerts"] += count

            # Get active alerts count
            active_alerts = self.database.get_active_alerts()
            summary["active_alerts"] = len(active_alerts)

            return summary

        except Exception as e:
            logger.error(f"Error getting alerts summary: {e}")
            return {}

    def _generate_executive_summary(self, system_analysis: Dict, agent_analysis: Dict,
                                  service_health: Dict, alerts_summary: Dict) -> Dict[str, Any]:
        """Generate executive summary"""
        return {
            "overall_health": "healthy",
            "key_metrics": {
                "avg_cpu_usage": system_analysis.get("metrics_analysis", {}).get("cpu_percent", {}).get("avg", 0),
                "avg_memory_usage": system_analysis.get("metrics_analysis", {}).get("memory_percent", {}).get("avg", 0),
                "agent_success_rate": agent_analysis.get("summary", {}).get("overall_success_rate", 0),
                "total_alerts": alerts_summary.get("total_alerts", 0)
            },
            "top_issues": [],
            "highlights": []
        }

    def _generate_recommendations(self, system_analysis: Dict, agent_analysis: Dict,
                                 service_health: Dict, alerts_summary: Dict) -> List[str]:
        """Generate recommendations based on analysis"""
        recommendations = []

        # System recommendations
        if "metrics_analysis" in system_analysis:
            cpu_avg = system_analysis["metrics_analysis"].get("cpu_percent", {}).get("avg", 0)
            memory_avg = system_analysis["metrics_analysis"].get("memory_percent", {}).get("avg", 0)

            if cpu_avg > 80:
                recommendations.append("Consider optimizing CPU usage or scaling resources")
            if memory_avg > 75:
                recommendations.append("Monitor memory usage and consider memory optimization")

        # Agent recommendations
        if "agents_analysis" in agent_analysis:
            success_rate = agent_analysis.get("summary", {}).get("overall_success_rate", 0)
            if success_rate < 0.95:
                recommendations.append("Investigate agent failure patterns and improve error handling")

        # Service recommendations
        unhealthy_services = [
            service for service, health in service_health.items()
            if health["unhealthy_checks"] > 0
        ]
        if unhealthy_services:
            recommendations.append(f"Review and fix unhealthy services: {', '.join(unhealthy_services)}")

        return recommendations

    def _generate_html_report(self, report: Dict) -> str:
        """Generate HTML version of the report"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{report['metadata']['title']}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }}
                .header {{ background: #f4f4f4; padding: 20px; border-radius: 5px; }}
                .section {{ margin: 20px 0; }}
                .metric {{ background: #fff; padding: 15px; margin: 10px 0; border: 1px solid #ddd; border-radius: 5px; }}
                .recommendation {{ background: #e8f4f8; padding: 15px; margin: 10px 0; border-left: 4px solid #17a2b8; }}
                .alert {{ background: #f8d7da; padding: 15px; margin: 10px 0; border-left: 4px solid #dc3545; }}
                table {{ border-collapse: collapse; width: 100%; margin: 10px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{report['metadata']['title']}</h1>
                <p>Period: {report['metadata']['period']['start']} to {report['metadata']['period']['end']}</p>
                <p>Generated: {report['metadata']['generated_at']}</p>
            </div>

            <div class="section">
                <h2>Executive Summary</h2>
                <div class="metric">
                    <h3>Overall Health: {report['executive_summary']['overall_health'].upper()}</h3>
                    <p>Average CPU Usage: {report['executive_summary']['key_metrics']['avg_cpu_usage']:.1f}%</p>
                    <p>Average Memory Usage: {report['executive_summary']['key_metrics']['avg_memory_usage']:.1f}%</p>
                    <p>Agent Success Rate: {report['executive_summary']['key_metrics']['agent_success_rate']:.1%}</p>
                    <p>Total Alerts: {report['executive_summary']['key_metrics']['total_alerts']}</p>
                </div>
            </div>

            <div class="section">
                <h2>Recommendations</h2>
                {self._format_recommendations_html(report['recommendations'])}
            </div>

            <div class="section">
                <h2>System Performance</h2>
                {self._format_system_analysis_html(report['system_performance'])}
            </div>

            <div class="section">
                <h2>Agent Performance</h2>
                {self._format_agent_analysis_html(report['agent_performance'])}
            </div>

            <div class="section">
                <h2>Service Health</h2>
                {self._format_service_health_html(report['service_health'])}
            </div>

            <div class="section">
                <h2>Alerts Summary</h2>
                {self._format_alerts_summary_html(report['alerts_summary'])}
            </div>
        </body>
        </html>
        """

    def _format_recommendations_html(self, recommendations: List[str]) -> str:
        """Format recommendations as HTML"""
        if not recommendations:
            return "<p>No specific recommendations at this time.</p>"

        html = ""
        for rec in recommendations:
            html += f'<div class="recommendation">{rec}</div>'
        return html

    def _format_system_analysis_html(self, analysis: Dict) -> str:
        """Format system analysis as HTML"""
        if "metrics_analysis" not in analysis:
            return "<p>No system performance data available.</p>"

        html = '<table><tr><th>Metric</th><th>Average</th><th>Min</th><th>Max</th><th>Trend</th></tr>'

        for metric_name, data in analysis["metrics_analysis"].items():
            html += f"""
                <tr>
                    <td>{metric_name.replace('_', ' ').title()}</td>
                    <td>{data['avg']:.2f}</td>
                    <td>{data['min']:.2f}</td>
                    <td>{data['max']:.2f}</td>
                    <td>{data['trend']}</td>
                </tr>
            """

        html += "</table>"
        return html

    def _format_agent_analysis_html(self, analysis: Dict) -> str:
        """Format agent analysis as HTML"""
        if "agents_analysis" not in analysis:
            return "<p>No agent performance data available.</p>"

        summary = analysis.get("summary", {})
        html = f"""
            <div class="metric">
                <h3>Agent Summary</h3>
                <p>Total Agents: {summary.get('total_agents', 0)}</p>
                <p>Total Requests: {summary.get('total_requests', 0)}</p>
                <p>Overall Success Rate: {summary.get('overall_success_rate', 0):.1%}</p>
                <p>Average Response Time: {summary.get('average_response_time', 0):.1f}ms</p>
            </div>
        """

        return html

    def _format_service_health_html(self, service_health: Dict) -> str:
        """Format service health as HTML"""
        if not service_health:
            return "<p>No service health data available.</p>"

        html = '<table><tr><th>Service</th><th>Total Checks</th><th>Healthy</th><th>Unhealthy</th><th>Avg Response Time</th></tr>'

        for service_name, health in service_health.items():
            html += f"""
                <tr>
                    <td>{service_name}</td>
                    <td>{health['total_checks']}</td>
                    <td>{health['healthy_checks']}</td>
                    <td>{health['unhealthy_checks']}</td>
                    <td>{health['avg_response_time']:.1f}ms</td>
                </tr>
            """

        html += "</table>"
        return html

    def _format_alerts_summary_html(self, alerts_summary: Dict) -> str:
        """Format alerts summary as HTML"""
        if not alerts_summary:
            return "<p>No alerts data available.</p>"

        html = f"""
            <div class="metric">
                <h3>Alerts Summary</h3>
                <p>Total Alerts: {alerts_summary.get('total_alerts', 0)}</p>
                <p>Active Alerts: {alerts_summary.get('active_alerts', 0)}</p>
            </div>
        """

        if alerts_summary.get('by_level'):
            html += '<h4>Alerts by Level:</h4><ul>'
            for level, count in alerts_summary['by_level'].items():
                html += f'<li>{level.title()}: {count}</li>'
            html += '</ul>'

        return html

class MonitoringAnalytics:
    """Main analytics orchestrator"""

    def __init__(self, database: MonitoringDatabase = None):
        self.database = database or get_monitoring().database
        self.analyzer = PerformanceAnalyzer(self.database)
        self.exporter = DataExporter(self.database)
        self.report_generator = ReportGenerator(self.database)

    def get_system_performance_report(self, period: AnalyticsPeriod = AnalyticsPeriod.DAY) -> Dict[str, Any]:
        """Get system performance report for specified period"""
        end_time = datetime.now()
        start_time = self._get_start_time(period, end_time)

        return self.analyzer.analyze_system_performance(start_time, end_time)

    def get_agent_performance_report(self, period: AnalyticsPeriod = AnalyticsPeriod.DAY) -> Dict[str, Any]:
        """Get agent performance report for specified period"""
        end_time = datetime.now()
        start_time = self._get_start_time(period, end_time)

        return self.analyzer.analyze_agent_performance(start_time, end_time)

    def export_data(self, data_type: str, period: AnalyticsPeriod = AnalyticsPeriod.DAY,
                   format: ReportFormat = ReportFormat.CSV) -> str:
        """Export data for specified period"""
        end_time = datetime.now()
        start_time = self._get_start_time(period, end_time)

        if data_type == "system_metrics":
            return self.exporter.export_system_metrics(start_time, end_time, format)
        elif data_type == "agent_metrics":
            return self.exporter.export_agent_metrics(start_time, end_time, format)
        elif data_type == "alerts":
            return self.exporter.export_alerts(start_time, end_time, format)
        else:
            raise ValueError(f"Unknown data type: {data_type}")

    def generate_report(self, period: AnalyticsPeriod = AnalyticsPeriod.DAY) -> str:
        """Generate comprehensive report for specified period"""
        end_time = datetime.now()
        start_time = self._get_start_time(period, end_time)

        return self.report_generator.generate_comprehensive_report(start_time, end_time)

    def _get_start_time(self, period: AnalyticsPeriod, end_time: datetime) -> datetime:
        """Get start time for specified period"""
        if period == AnalyticsPeriod.HOUR:
            return end_time - timedelta(hours=1)
        elif period == AnalyticsPeriod.DAY:
            return end_time - timedelta(days=1)
        elif period == AnalyticsPeriod.WEEK:
            return end_time - timedelta(weeks=1)
        elif period == AnalyticsPeriod.MONTH:
            return end_time - timedelta(days=30)
        elif period == AnalyticsPeriod.YEAR:
            return end_time - timedelta(days=365)
        else:
            raise ValueError(f"Unknown period: {period}")

# Global analytics instance
_analytics_instance = None

def get_analytics() -> MonitoringAnalytics:
    """Get the global analytics instance"""
    global _analytics_instance
    if _analytics_instance is None:
        _analytics_instance = MonitoringAnalytics()
    return _analytics_instance

if __name__ == "__main__":
    # Test the analytics system
    print("Testing DuckBot Monitoring Analytics System")

    analytics = get_analytics()

    try:
        # Test system performance analysis
        print("\n1. Testing system performance analysis...")
        system_report = analytics.get_system_performance_report(AnalyticsPeriod.HOUR)
        print(f"System report generated with {len(system_report.get('metrics_analysis', {}))} metrics")

        # Test data export
        print("\n2. Testing data export...")
        export_path = analytics.export_data("system_metrics", AnalyticsPeriod.HOUR, ReportFormat.CSV)
        print(f"Data exported to: {export_path}")

        # Test report generation
        print("\n3. Testing report generation...")
        report_path = analytics.generate_report(AnalyticsPeriod.HOUR)
        print(f"Report generated: {report_path}")

        print("\nAnalytics system test completed successfully!")

    except Exception as e:
        print(f"Error testing analytics system: {e}")
        import traceback
        traceback.print_exc()