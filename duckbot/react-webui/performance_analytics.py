#!/usr/bin/env python3
"""
Performance Analytics and Trend Prediction System

Provides sophisticated performance analytics, trend prediction,
and automated optimization recommendations for DuckBot services.
"""

import asyncio
import json
import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from statistics import mean, median, stdev
import numpy as np
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('performance_analytics.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetric:
    """Performance metric data structure"""
    timestamp: datetime
    service_name: str
    metric_type: str  # response_time, cpu_usage, memory_usage, etc.
    value: float
    unit: str

@dataclass
class TrendAnalysis:
    """Trend analysis result"""
    metric_type: str
    service_name: str
    trend_direction: str  # increasing, decreasing, stable
    trend_strength: float  # 0.0 to 1.0
    prediction: Dict[str, Any]
    confidence: float  # 0.0 to 1.0
    time_range: str

@dataclass
class PerformanceAlert:
    """Performance-based alert"""
    alert_type: str
    severity: str
    service_name: str
    message: str
    details: Dict[str, Any]
    recommendation: str
    timestamp: datetime
    confidence: float

class PerformanceAnalytics:
    """Performance analytics and trend prediction system"""

    def __init__(self, db_path: str = "performance_metrics.db"):
        self.db_path = db_path
        self.metrics_buffer: List[PerformanceMetric] = []
        self.trends_cache: Dict[str, TrendAnalysis] = {}
        self.alert_rules = self._load_alert_rules()
        self.prediction_models = self._initialize_prediction_models()

        # Initialize database
        self._init_database()

        logger.info("Performance Analytics system initialized")

    def _init_database(self):
        """Initialize the performance metrics database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    service_name TEXT NOT NULL,
                    metric_type TEXT NOT NULL,
                    value REAL NOT NULL,
                    unit TEXT
                )
            """)
            # Create indexes separately
            conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON performance_metrics(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_service_metric ON performance_metrics(service_name, metric_type)")

            conn.execute("""
                CREATE TABLE IF NOT EXISTS trend_predictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_type TEXT NOT NULL,
                    service_name TEXT NOT NULL,
                    prediction_time DATETIME NOT NULL,
                    predicted_value REAL NOT NULL,
                    confidence REAL NOT NULL,
                    time_range TEXT NOT NULL,
                    actual_value REAL,
                    prediction_error REAL
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_trend_metric_service ON trend_predictions(metric_type, service_name)")

            conn.execute("""
                CREATE TABLE IF NOT EXISTS performance_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alert_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    service_name TEXT NOT NULL,
                    message TEXT NOT NULL,
                    details TEXT,
                    recommendation TEXT,
                    timestamp DATETIME NOT NULL,
                    confidence REAL,
                    resolved BOOLEAN DEFAULT FALSE,
                    resolved_at DATETIME
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_alert_service_severity ON performance_alerts(service_name, severity)")

            conn.commit()

    def _load_alert_rules(self) -> Dict[str, Dict[str, Any]]:
        """Load performance alert rules"""
        return {
            "response_time": {
                "warning_threshold": 5000,  # 5 seconds
                "critical_threshold": 10000,  # 10 seconds
                "trend_threshold": 0.3,  # 30% increase
                "window_size": "1h"
            },
            "memory_usage": {
                "warning_threshold": 80,  # 80%
                "critical_threshold": 95,  # 95%
                "trend_threshold": 0.2,  # 20% increase
                "window_size": "1h"
            },
            "cpu_usage": {
                "warning_threshold": 70,  # 70%
                "critical_threshold": 90,  # 90%
                "trend_threshold": 0.3,  # 30% increase
                "window_size": "1h"
            },
            "error_rate": {
                "warning_threshold": 0.05,  # 5%
                "critical_threshold": 0.1,  # 10%
                "trend_threshold": 0.5,  # 50% increase
                "window_size": "1h"
            },
            "availability": {
                "warning_threshold": 95,  # 95%
                "critical_threshold": 90,  # 90%
                "trend_threshold": -0.1,  # 10% decrease
                "window_size": "24h"
            }
        }

    def _initialize_prediction_models(self) -> Dict[str, Any]:
        """Initialize simple prediction models"""
        return {
            "linear_regression": self._linear_regression_model,
            "moving_average": self._moving_average_model,
            "exponential_smoothing": self._exponential_smoothing_model
        }

    def _linear_regression_model(self, values: List[float]) -> Dict[str, Any]:
        """Simple linear regression model"""
        if len(values) < 2:
            return {"error": "Insufficient data"}

        x = list(range(len(values)))
        y = values

        # Calculate slope and intercept
        n = len(values)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(xi * yi for xi, yi in zip(x, y))
        sum_x2 = sum(xi * xi for xi in x)

        denominator = n * sum_x2 - sum_x * sum_x
        if denominator == 0:
            return {"error": "Cannot calculate slope"}

        slope = (n * sum_xy - sum_x * sum_y) / denominator
        intercept = (sum_y - slope * sum_x) / n

        # Predict next value
        next_value = intercept + slope * len(values)

        return {
            "slope": slope,
            "intercept": intercept,
            "next_prediction": next_value
        }

    def _moving_average_model(self, values: List[float], window: int = 5) -> Dict[str, Any]:
        """Moving average model"""
        if len(values) < window:
            return {"error": f"Need at least {window} data points"}

        recent_values = values[-window:]
        average = sum(recent_values) / len(recent_values)

        return {
            "window": window,
            "average": average,
            "next_prediction": average
        }

    def _exponential_smoothing_model(self, values: List[float], alpha: float = 0.3) -> Dict[str, Any]:
        """Exponential smoothing model"""
        if len(values) < 2:
            return {"error": "Insufficient data"}

        # Simple exponential smoothing
        smoothed_values = [values[0]]
        for i in range(1, len(values)):
            smoothed_value = alpha * values[i] + (1 - alpha) * smoothed_values[i-1]
            smoothed_values.append(smoothed_value)

        next_prediction = alpha * values[-1] + (1 - alpha) * smoothed_values[-1]

        return {
            "alpha": alpha,
            "smoothed_values": smoothed_values,
            "next_prediction": next_prediction
        }

    async def collect_metrics(self, service_name: str, metrics_data: Dict[str, Any]):
        """Collect performance metrics from a service"""
        timestamp = datetime.now()

        # Extract and normalize metrics
        metric_types = {
            "response_time": ("response_time", "ms"),
            "memory_usage": ("memory_usage", "%"),
            "cpu_usage": ("cpu_usage", "%"),
            "error_rate": ("error_rate", "%"),
            "uptime": ("uptime", "seconds"),
            "request_count": ("request_count", "count"),
            "active_connections": ("active_connections", "count")
        }

        for metric_key, (metric_type, unit) in metric_types.items():
            if metric_key in metrics_data:
                try:
                    value = float(metrics_data[metric_key])
                    metric = PerformanceMetric(
                        timestamp=timestamp,
                        service_name=service_name,
                        metric_type=metric_type,
                        value=value,
                        unit=unit
                    )

                    self.metrics_buffer.append(metric)

                    # Process buffer if full
                    if len(self.metrics_buffer) >= 100:
                        await self._process_metrics_buffer()

                except (ValueError, TypeError) as e:
                    logger.warning(f"Invalid metric value for {metric_key}: {e}")

    async def _process_metrics_buffer(self):
        """Process buffered metrics and store in database"""
        if not self.metrics_buffer:
            return

        try:
            with sqlite3.connect(self.db_path) as conn:
                for metric in self.metrics_buffer:
                    conn.execute("""
                        INSERT INTO performance_metrics
                        (timestamp, service_name, metric_type, value, unit)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        metric.timestamp.isoformat(),
                        metric.service_name,
                        metric.metric_type,
                        metric.value,
                        metric.unit
                    ))

                conn.commit()

            logger.info(f"Processed {len(self.metrics_buffer)} metrics")
            self.metrics_buffer.clear()

            # Analyze trends after processing
            await self._analyze_all_trends()

        except Exception as e:
            logger.error(f"Error processing metrics buffer: {e}")

    async def _analyze_all_trends(self):
        """Analyze trends for all services and metrics"""
        try:
            # Get unique service-metric combinations
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT DISTINCT service_name, metric_type
                    FROM performance_metrics
                """)

                for service_name, metric_type in cursor.fetchall():
                    await self._analyze_metric_trend(service_name, metric_type)

        except Exception as e:
            logger.error(f"Error analyzing trends: {e}")

    async def _analyze_metric_trend(self, service_name: str, metric_type: str):
        """Analyze trend for a specific service metric"""
        try:
            # Get recent metrics
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT timestamp, value
                    FROM performance_metrics
                    WHERE service_name = ? AND metric_type = ?
                    ORDER BY timestamp DESC
                    LIMIT 100
                """, (service_name, metric_type))

                data = cursor.fetchall()

            if len(data) < 10:
                return  # Not enough data for trend analysis

            # Prepare data for analysis
            timestamps = [datetime.fromisoformat(row[0]) for row in data]
            values = [row[1] for row in data]

            # Calculate trend direction and strength
            trend_direction, trend_strength = self._calculate_trend(values)

            # Generate predictions
            predictions = await self._generate_predictions(
                service_name, metric_type, values, timestamps
            )

            # Calculate confidence
            confidence = self._calculate_prediction_confidence(values, predictions)

            # Create trend analysis
            trend_analysis = TrendAnalysis(
                metric_type=metric_type,
                service_name=service_name,
                trend_direction=trend_direction,
                trend_strength=trend_strength,
                prediction=predictions,
                confidence=confidence,
                time_range="24h"
            )

            # Cache trend analysis
            cache_key = f"{service_name}_{metric_type}"
            self.trends_cache[cache_key] = trend_analysis

            # Check for alerts
            await self._check_performance_alerts(trend_analysis, values[-1])

        except Exception as e:
            logger.error(f"Error analyzing trend for {service_name}/{metric_type}: {e}")

    def _calculate_trend(self, values: List[float]) -> Tuple[str, float]:
        """Calculate trend direction and strength"""
        if len(values) < 2:
            return "stable", 0.0

        # Simple linear regression
        x = list(range(len(values)))
        y = values

        # Calculate slope
        x_mean = mean(x)
        y_mean = mean(y)

        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(len(x)))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(len(x)))

        if denominator == 0:
            return "stable", 0.0

        slope = numerator / denominator

        # Calculate correlation coefficient for strength
        correlation = numerator / (stdev(x) * stdev(y) * len(x)) if stdev(x) > 0 and stdev(y) > 0 else 0

        # Determine direction and strength
        if abs(slope) < 0.01:
            direction = "stable"
            strength = 0.0
        elif slope > 0:
            direction = "increasing"
            strength = min(abs(correlation), 1.0)
        else:
            direction = "decreasing"
            strength = min(abs(correlation), 1.0)

        return direction, strength

    async def _generate_predictions(self, service_name: str, metric_type: str,
                                  values: List[float], timestamps: List[datetime]) -> Dict[str, Any]:
        """Generate predictions using multiple models"""
        predictions = {}

        # Simple linear regression prediction
        if len(values) >= 2:
            x = list(range(len(values)))
            y = values

            # Fit linear model
            x_mean = mean(x)
            y_mean = mean(y)

            numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(len(x)))
            denominator = sum((x[i] - x_mean) ** 2 for i in range(len(x)))

            if denominator != 0:
                slope = numerator / denominator
                intercept = y_mean - slope * x_mean

                # Predict next 5 values
                future_predictions = []
                for i in range(1, 6):
                    pred_value = intercept + slope * (len(values) + i - 1)
                    future_predictions.append(max(0, pred_value))  # Ensure non-negative

                predictions["linear_regression"] = {
                    "values": future_predictions,
                    "time_horizon": "5 steps"
                }

        # Moving average prediction
        if len(values) >= 5:
            window_size = min(5, len(values))
            recent_avg = mean(values[-window_size:])
            predictions["moving_average"] = {
                "values": [recent_avg] * 5,
                "time_horizon": "5 steps"
            }

        return predictions

    def _calculate_prediction_confidence(self, values: List[float],
                                       predictions: Dict[str, Any]) -> float:
        """Calculate confidence in predictions"""
        if not predictions or len(values) < 10:
            return 0.5  # Default confidence

        # Calculate volatility as inverse of confidence
        volatility = stdev(values) if len(values) > 1 else 0

        # Normalize volatility to confidence score
        if volatility == 0:
            return 1.0

        # Lower volatility = higher confidence
        confidence = max(0.1, min(1.0, 1.0 / (1.0 + volatility * 0.1)))

        return confidence

    async def _check_performance_alerts(self, trend_analysis: TrendAnalysis, current_value: float):
        """Check for performance-based alerts"""
        alert_rule = self.alert_rules.get(trend_analysis.metric_type)
        if not alert_rule:
            return

        alerts = []

        # Check threshold-based alerts
        if trend_analysis.metric_type in ["response_time", "memory_usage", "cpu_usage", "error_rate"]:
            if current_value >= alert_rule["critical_threshold"]:
                alerts.append(PerformanceAlert(
                    alert_type="threshold_critical",
                    severity="critical",
                    service_name=trend_analysis.service_name,
                    message=f"Critical {trend_analysis.metric_type}: {current_value:.2f}",
                    details={"current_value": current_value, "threshold": alert_rule["critical_threshold"]},
                    recommendation=f"Investigate {trend_analysis.service_name} performance immediately",
                    timestamp=datetime.now(),
                    confidence=0.95
                ))
            elif current_value >= alert_rule["warning_threshold"]:
                alerts.append(PerformanceAlert(
                    alert_type="threshold_warning",
                    severity="warning",
                    service_name=trend_analysis.service_name,
                    message=f"Warning {trend_analysis.metric_type}: {current_value:.2f}",
                    details={"current_value": current_value, "threshold": alert_rule["warning_threshold"]},
                    recommendation=f"Monitor {trend_analysis.service_name} performance closely",
                    timestamp=datetime.now(),
                    confidence=0.8
                ))

        # Check trend-based alerts
        if trend_analysis.trend_strength > alert_rule["trend_threshold"]:
            if trend_analysis.trend_direction == "increasing":
                alerts.append(PerformanceAlert(
                    alert_type="trend_warning",
                    severity="warning",
                    service_name=trend_analysis.service_name,
                    message=f"Degrading trend detected in {trend_analysis.metric_type}",
                    details={
                        "trend_direction": trend_analysis.trend_direction,
                        "trend_strength": trend_analysis.trend_strength,
                        "predictions": trend_analysis.prediction
                    },
                    recommendation=f"Analyze {trend_analysis.service_name} for performance issues",
                    timestamp=datetime.now(),
                    confidence=trend_analysis.trend_strength
                ))

        # Store alerts
        for alert in alerts:
            await self._store_alert(alert)

    async def _store_alert(self, alert: PerformanceAlert):
        """Store performance alert in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO performance_alerts
                    (alert_type, severity, service_name, message, details, recommendation, timestamp, confidence)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    alert.alert_type,
                    alert.severity,
                    alert.service_name,
                    alert.message,
                    json.dumps(alert.details),
                    alert.recommendation,
                    alert.timestamp.isoformat(),
                    alert.confidence
                ))
                conn.commit()

            logger.info(f"Performance alert stored: {alert.alert_type} for {alert.service_name}")

        except Exception as e:
            logger.error(f"Error storing alert: {e}")

    async def get_performance_summary(self, service_name: Optional[str] = None,
                                    time_range: str = "24h") -> Dict[str, Any]:
        """Get performance summary for services"""
        try:
            # Calculate time range
            if time_range == "1h":
                start_time = datetime.now() - timedelta(hours=1)
            elif time_range == "24h":
                start_time = datetime.now() - timedelta(days=1)
            elif time_range == "7d":
                start_time = datetime.now() - timedelta(days=7)
            else:
                start_time = datetime.now() - timedelta(days=1)

            with sqlite3.connect(self.db_path) as conn:
                # Get service list
                if service_name:
                    service_filter = f"WHERE service_name = '{service_name}'"
                else:
                    service_filter = ""

                cursor = conn.execute(f"""
                    SELECT service_name, metric_type, AVG(value) as avg_value,
                           MIN(value) as min_value, MAX(value) as max_value,
                           COUNT(*) as count
                    FROM performance_metrics
                    WHERE timestamp >= ? {service_filter}
                    GROUP BY service_name, metric_type
                    ORDER BY service_name, metric_type
                """, (start_time.isoformat(),))

                summary_data = {}
                for row in cursor.fetchall():
                    svc_name, metric_type, avg_val, min_val, max_val, count = row

                    if svc_name not in summary_data:
                        summary_data[svc_name] = {
                            "metrics": {},
                            "alerts": [],
                            "trends": {}
                        }

                    summary_data[svc_name]["metrics"][metric_type] = {
                        "average": avg_val,
                        "minimum": min_val,
                        "maximum": max_val,
                        "sample_count": count
                    }

                # Get alerts
                cursor = conn.execute("""
                    SELECT alert_type, severity, message, recommendation, timestamp, confidence
                    FROM performance_alerts
                    WHERE timestamp >= ? AND resolved = FALSE
                    ORDER BY timestamp DESC
                    LIMIT 50
                """, (start_time.isoformat(),))

                alerts = []
                for row in cursor.fetchall():
                    alerts.append({
                        "type": row[0],
                        "severity": row[1],
                        "message": row[2],
                        "recommendation": row[3],
                        "timestamp": row[4],
                        "confidence": row[5]
                    })

                # Get trends
                for cache_key, trend in self.trends_cache.items():
                    if service_name is None or trend.service_name == service_name:
                        if trend.service_name not in summary_data:
                            summary_data[trend.service_name] = {
                                "metrics": {},
                                "alerts": [],
                                "trends": {}
                            }

                        summary_data[trend.service_name]["trends"][trend.metric_type] = {
                            "direction": trend.trend_direction,
                            "strength": trend.trend_strength,
                            "confidence": trend.confidence,
                            "predictions": trend.prediction
                        }

                return {
                    "time_range": time_range,
                    "start_time": start_time.isoformat(),
                    "end_time": datetime.now().isoformat(),
                    "services": summary_data,
                    "total_alerts": len(alerts),
                    "alert_summary": self._summarize_alerts(alerts)
                }

        except Exception as e:
            logger.error(f"Error getting performance summary: {e}")
            return {"error": str(e)}

    def _summarize_alerts(self, alerts: List[Dict[str, Any]]) -> Dict[str, int]:
        """Summarize alerts by severity"""
        summary = {"critical": 0, "warning": 0, "info": 0}
        for alert in alerts:
            severity = alert.get("severity", "info")
            if severity in summary:
                summary[severity] += 1
        return summary

    async def get_performance_predictions(self, service_name: str,
                                       metric_types: List[str] = None) -> Dict[str, Any]:
        """Get performance predictions for a service"""
        try:
            if metric_types is None:
                metric_types = ["response_time", "memory_usage", "cpu_usage", "error_rate"]

            predictions = {}

            for metric_type in metric_types:
                cache_key = f"{service_name}_{metric_type}"
                trend = self.trends_cache.get(cache_key)

                if trend:
                    predictions[metric_type] = {
                        "current_trend": {
                            "direction": trend.trend_direction,
                            "strength": trend.trend_strength,
                            "confidence": trend.confidence
                        },
                        "predictions": trend.prediction,
                        "recommendation": self._generate_recommendation(trend)
                    }
                else:
                    predictions[metric_type] = {
                        "current_trend": None,
                        "predictions": {},
                        "recommendation": "Insufficient data for prediction"
                    }

            return {
                "service_name": service_name,
                "timestamp": datetime.now().isoformat(),
                "predictions": predictions,
                "model_accuracy": await self._calculate_model_accuracy(service_name)
            }

        except Exception as e:
            logger.error(f"Error getting performance predictions: {e}")
            return {"error": str(e)}

    def _generate_recommendation(self, trend_analysis: TrendAnalysis) -> str:
        """Generate recommendation based on trend analysis"""
        if trend_analysis.trend_direction == "increasing":
            if trend_analysis.metric_type == "response_time":
                return "Consider optimizing service performance or scaling resources"
            elif trend_analysis.metric_type in ["memory_usage", "cpu_usage"]:
                return "Monitor resource usage and consider scaling or optimization"
            elif trend_analysis.metric_type == "error_rate":
                return "Investigate error patterns and implement fixes"
        elif trend_analysis.trend_direction == "decreasing":
            if trend_analysis.metric_type in ["response_time", "memory_usage", "cpu_usage"]:
                return "Performance improving, continue monitoring"
        else:
            return "Performance stable, continue normal monitoring"

    async def _calculate_model_accuracy(self, service_name: str) -> Dict[str, float]:
        """Calculate prediction model accuracy"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT predicted_value, actual_value, prediction_error
                    FROM trend_predictions
                    WHERE service_name = ? AND actual_value IS NOT NULL
                    ORDER BY prediction_time DESC
                    LIMIT 100
                """, (service_name,))

                errors = []
                for row in cursor.fetchall():
                    if row[2] is not None:  # prediction_error
                        errors.append(abs(row[2]))

                if not errors:
                    return {"mean_error": 0.0, "accuracy": 0.0}

                mean_error = mean(errors)
                # Simple accuracy calculation (inverse of normalized error)
                accuracy = max(0.0, min(1.0, 1.0 - (mean_error / 100)))

                return {
                    "mean_error": mean_error,
                    "accuracy": accuracy,
                    "sample_size": len(errors)
                }

        except Exception as e:
            logger.error(f"Error calculating model accuracy: {e}")
            return {"mean_error": 0.0, "accuracy": 0.0}

    async def optimize_performance(self, service_name: str) -> Dict[str, Any]:
        """Generate performance optimization recommendations"""
        try:
            # Get current performance data
            summary = await self.get_performance_summary(service_name)
            predictions = await self.get_performance_predictions(service_name)

            recommendations = []

            # Analyze metrics for optimization opportunities
            if service_name in summary["services"]:
                metrics = summary["services"][service_name]["metrics"]

                # Memory optimization
                if "memory_usage" in metrics:
                    memory_usage = metrics["memory_usage"]["average"]
                    if memory_usage > 80:
                        recommendations.append({
                            "type": "memory_optimization",
                            "priority": "high",
                            "description": "High memory usage detected",
                            "actions": [
                                "Review memory allocation patterns",
                                "Implement memory pooling if applicable",
                                "Consider garbage collection optimization",
                                "Monitor for memory leaks"
                            ]
                        })

                # CPU optimization
                if "cpu_usage" in metrics:
                    cpu_usage = metrics["cpu_usage"]["average"]
                    if cpu_usage > 70:
                        recommendations.append({
                            "type": "cpu_optimization",
                            "priority": "high",
                            "description": "High CPU usage detected",
                            "actions": [
                                "Profile CPU-intensive operations",
                                "Implement caching strategies",
                                "Consider async processing",
                                "Optimize algorithms and data structures"
                            ]
                        })

                # Response time optimization
                if "response_time" in metrics:
                    response_time = metrics["response_time"]["average"]
                    if response_time > 5000:  # 5 seconds
                        recommendations.append({
                            "type": "response_time_optimization",
                            "priority": "high",
                            "description": "High response time detected",
                            "actions": [
                                "Implement request caching",
                                "Optimize database queries",
                                "Consider connection pooling",
                                "Implement load balancing"
                            ]
                        })

            # Add trend-based recommendations
            if "predictions" in predictions:
                for metric_type, prediction_data in predictions["predictions"].items():
                    if prediction_data["current_trend"]:
                        trend = prediction_data["current_trend"]
                        if trend["direction"] == "increasing" and trend["strength"] > 0.7:
                            recommendations.append({
                                "type": "trend_based",
                                "priority": "medium",
                                "description": f"Degrading trend in {metric_type}",
                                "actions": [
                                    "Monitor trend closely",
                                    "Investigate root causes",
                                    "Consider preventive measures",
                                    "Set up additional monitoring"
                                ]
                            })

            return {
                "service_name": service_name,
                "timestamp": datetime.now().isoformat(),
                "current_performance": summary.get("services", {}).get(service_name, {}),
                "recommendations": recommendations,
                "optimization_priority": self._calculate_optimization_priority(recommendations)
            }

        except Exception as e:
            logger.error(f"Error generating optimization recommendations: {e}")
            return {"error": str(e)}

    def _calculate_optimization_priority(self, recommendations: List[Dict[str, Any]]) -> str:
        """Calculate overall optimization priority"""
        if not recommendations:
            return "low"

        high_priority_count = sum(1 for r in recommendations if r.get("priority") == "high")

        if high_priority_count >= 2:
            return "critical"
        elif high_priority_count >= 1:
            return "high"
        else:
            return "medium"

    async def export_performance_report(self, service_name: Optional[str] = None,
                                      format: str = "json") -> str:
        """Export performance report"""
        try:
            summary = await self.get_performance_summary(service_name, "7d")

            if format == "json":
                return json.dumps(summary, indent=2, default=str)
            elif format == "csv":
                # Generate CSV format
                csv_lines = ["Service,Metric Type,Average,Minimum,Maximum,Sample Count"]

                for svc_name, svc_data in summary["services"].items():
                    for metric_type, metric_data in svc_data["metrics"].items():
                        csv_lines.append(f'{svc_name},{metric_type},{metric_data["average"]:.2f},'
                                       f'{metric_data["minimum"]:.2f},{metric_data["maximum"]:.2f},'
                                       f'{metric_data["sample_count"]}')

                return "\n".join(csv_lines)
            else:
                raise ValueError(f"Unsupported format: {format}")

        except Exception as e:
            logger.error(f"Error exporting performance report: {e}")
            return f"Error: {str(e)}"

    async def cleanup_old_data(self, days_to_keep: int = 30):
        """Clean up old performance data"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)

            with sqlite3.connect(self.db_path) as conn:
                # Clean old metrics
                cursor = conn.execute("""
                    DELETE FROM performance_metrics
                    WHERE timestamp < ?
                """, (cutoff_date.isoformat(),))

                metrics_deleted = cursor.rowcount

                # Clean old resolved alerts
                cursor = conn.execute("""
                    DELETE FROM performance_alerts
                    WHERE timestamp < ? AND resolved = TRUE
                """, (cutoff_date.isoformat(),))

                alerts_deleted = cursor.rowcount

                # Clean old predictions
                cursor = conn.execute("""
                    DELETE FROM trend_predictions
                    WHERE prediction_time < ?
                """, (cutoff_date.isoformat(),))

                predictions_deleted = cursor.rowcount

                conn.commit()

                logger.info(f"Cleaned up old data: {metrics_deleted} metrics, "
                           f"{alerts_deleted} alerts, {predictions_deleted} predictions")

                return {
                    "metrics_deleted": metrics_deleted,
                    "alerts_deleted": alerts_deleted,
                    "predictions_deleted": predictions_deleted
                }

        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
            return {"error": str(e)}

# Global instance
_performance_analytics = None

def get_performance_analytics() -> PerformanceAnalytics:
    """Get global performance analytics instance"""
    global _performance_analytics
    if _performance_analytics is None:
        _performance_analytics = PerformanceAnalytics()
    return _performance_analytics

async def main():
    """Main function for testing"""
    analytics = get_performance_analytics()

    # Test data collection
    test_metrics = {
        "response_time": 150.5,
        "memory_usage": 45.2,
        "cpu_usage": 35.8,
        "error_rate": 0.01
    }

    await analytics.collect_metrics("test_service", test_metrics)

    # Get performance summary
    summary = await analytics.get_performance_summary()
    print("Performance Summary:", json.dumps(summary, indent=2, default=str))

    # Get predictions
    predictions = await analytics.get_performance_predictions("test_service")
    print("Predictions:", json.dumps(predictions, indent=2, default=str))

if __name__ == "__main__":
    asyncio.run(main())