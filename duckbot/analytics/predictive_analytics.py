#!/usr/bin/env python3
"""
DuckBot Predictive Analytics System
Advanced machine learning-based predictions, forecasting, and anomaly detection
"""

import asyncio
import json
import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
import pandas as pd
from pathlib import Path
import uuid
from collections import defaultdict, deque
import statistics

from sklearn.ensemble import IsolationForest
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error
import joblib

from analytics_engine import AnalyticsEngine, AnalyticsEvent, AnalyticsEventType

logger = logging.getLogger(__name__)

class PredictionType(Enum):
    """Types of predictions"""
    USAGE_FORECAST = "usage_forecast"
    COST_FORECAST = "cost_forecast"
    PERFORMANCE_PREDICTION = "performance_prediction"
    USER_BEHAVIOR_PREDICTION = "user_behavior_prediction"
    ANOMALY_DETECTION = "anomaly_detection"
    RESOURCE_PREDICTION = "resource_prediction"
    TREND_PREDICTION = "trend_prediction"

class ModelType(Enum):
    """Types of ML models"""
    LINEAR_REGRESSION = "linear_regression"
    ISOLATION_FOREST = "isolation_forest"
    MOVING_AVERAGE = "moving_average"
    EXPONENTIAL_SMOOTHING = "exponential_smoothing"
    SEASONAL_DECOMPOSITION = "seasonal_decomposition"
    ENSEMBLE = "ensemble"

class ConfidenceLevel(Enum):
    """Confidence levels for predictions"""
    VERY_LOW = 0.2
    LOW = 0.4
    MEDIUM = 0.6
    HIGH = 0.8
    VERY_HIGH = 0.95

@dataclass
class PredictionModel:
    """ML prediction model configuration"""
    model_id: str
    model_type: ModelType
    target_metric: str
    features: List[str]
    hyperparameters: Dict[str, Any]
    accuracy_score: float
    last_trained: datetime
    is_active: bool = True

@dataclass
class PredictionResult:
    """Prediction result with confidence intervals"""
    prediction_id: str
    prediction_type: PredictionType
    model_id: str
    predicted_value: float
    confidence_interval: Tuple[float, float]
    confidence_level: float
    prediction_horizon: str
    actual_value: Optional[float] = None
    accuracy_score: Optional[float] = None
    created_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AnomalyAlert:
    """Anomaly detection alert"""
    alert_id: str
    metric_name: str
    anomaly_value: float
    expected_range: Tuple[float, float]
    severity_score: float  # 0-100
    detection_method: str
    timestamp: datetime
    is_resolved: bool = False
    root_cause_analysis: Optional[str] = None
    recommendations: List[str] = field(default_factory=list)

@dataclass
class TrendAnalysis:
    """Trend analysis results"""
    trend_id: str
    metric_name: str
    trend_direction: str  # "increasing", "decreasing", "stable"
    trend_strength: float  # 0-1
    trend_significance: float  # p-value equivalent
    seasonal_pattern: Optional[Dict[str, Any]] = None
    change_points: List[datetime] = field(default_factory=list)
    forecast_period: str = "30d"
    created_at: datetime

class PredictiveAnalyticsEngine:
    """Advanced predictive analytics engine with ML capabilities"""

    def __init__(self, analytics_engine: AnalyticsEngine):
        self.analytics_engine = analytics_engine
        self.db_path = analytics_engine.db.db_path

        self.models: Dict[str, PredictionModel] = {}
        self.predictions: Dict[str, PredictionResult] = {}
        self.anomaly_alerts: List[AnomalyAlert] = []
        self.trend_analyses: Dict[str, TrendAnalysis] = {}

        self.model_cache_dir = Path(__file__).parent / "models"
        self.model_cache_dir.mkdir(exist_ok=True)

        self.is_running = False
        self._initialize_predictive_engine()

    def _initialize_predictive_engine(self):
        """Initialize the predictive analytics engine"""
        # Create database tables
        self._create_database_tables()
        # Load existing models
        self._load_models()
        # Start prediction services
        self.start_prediction_services()

    def _create_database_tables(self):
        """Create predictive analytics database tables"""
        with sqlite3.connect(self.db_path) as conn:
            # Prediction models table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS prediction_models (
                    model_id TEXT PRIMARY KEY,
                    model_type TEXT NOT NULL,
                    target_metric TEXT NOT NULL,
                    features TEXT,
                    hyperparameters TEXT,
                    accuracy_score REAL,
                    last_trained DATETIME,
                    is_active BOOLEAN DEFAULT TRUE
                )
            ''')

            # Predictions table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS predictions (
                    prediction_id TEXT PRIMARY KEY,
                    prediction_type TEXT NOT NULL,
                    model_id TEXT,
                    predicted_value REAL,
                    confidence_interval_low REAL,
                    confidence_interval_high REAL,
                    confidence_level REAL,
                    prediction_horizon TEXT,
                    actual_value REAL,
                    accuracy_score REAL,
                    created_at DATETIME,
                    metadata TEXT,
                    FOREIGN KEY (model_id) REFERENCES prediction_models(model_id)
                )
            ''')

            # Anomaly alerts table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS anomaly_alerts (
                    alert_id TEXT PRIMARY KEY,
                    metric_name TEXT NOT NULL,
                    anomaly_value REAL,
                    expected_range_low REAL,
                    expected_range_high REAL,
                    severity_score REAL,
                    detection_method TEXT,
                    timestamp DATETIME,
                    is_resolved BOOLEAN DEFAULT FALSE,
                    root_cause_analysis TEXT,
                    recommendations TEXT
                )
            ''')

            # Trend analysis table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS trend_analyses (
                    trend_id TEXT PRIMARY KEY,
                    metric_name TEXT NOT NULL,
                    trend_direction TEXT,
                    trend_strength REAL,
                    trend_significance REAL,
                    seasonal_pattern TEXT,
                    change_points TEXT,
                    forecast_period TEXT,
                    created_at DATETIME
                )
            ''')

            # Model performance tracking table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS model_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_id TEXT,
                    prediction_id TEXT,
                    actual_value REAL,
                    predicted_value REAL,
                    error REAL,
                    absolute_error REAL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (model_id) REFERENCES prediction_models(model_id),
                    FOREIGN KEY (prediction_id) REFERENCES predictions(prediction_id)
                )
            ''')

            # Create indexes
            indexes = [
                'CREATE INDEX IF NOT EXISTS idx_models_metric ON prediction_models(target_metric)',
                'CREATE INDEX IF NOT EXISTS idx_predictions_type ON predictions(prediction_type)',
                'CREATE INDEX IF NOT EXISTS idx_predictions_created ON predictions(created_at)',
                'CREATE INDEX IF NOT EXISTS idx_anomalies_metric ON anomaly_alerts(metric_name)',
                'CREATE INDEX IF NOT EXISTS idx_anomalies_timestamp ON anomaly_alerts(timestamp)',
                'CREATE INDEX IF NOT EXISTS idx_trends_metric ON trend_analyses(metric_name)'
            ]

            for index_sql in indexes:
                conn.execute(index_sql)

    def _load_models(self):
        """Load existing prediction models"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('SELECT * FROM prediction_models WHERE is_active = TRUE')
                for row in cursor.fetchall():
                    model = PredictionModel(
                        model_id=row[0],
                        model_type=ModelType(row[1]),
                        target_metric=row[2],
                        features=json.loads(row[3]) if row[3] else [],
                        hyperparameters=json.loads(row[4]) if row[4] else {},
                        accuracy_score=row[5] or 0.0,
                        last_trained=datetime.fromisoformat(row[6]) if row[6] else datetime.now(),
                        is_active=row[7]
                    )
                    self.models[model.model_id] = model

                    # Load model file if it exists
                    model_file = self.model_cache_dir / f"{model.model_id}.joblib"
                    if model_file.exists():
                        try:
                            model_object = joblib.load(model_file)
                            # Store the actual model object
                            setattr(model, '_model_object', model_object)
                        except Exception as e:
                            logger.error(f"Error loading model file for {model.model_id}: {e}")

        except Exception as e:
            logger.error(f"Error loading prediction models: {e}")

    def start_prediction_services(self):
        """Start prediction services"""
        if not self.is_running:
            self.is_running = True
            asyncio.create_task(self._prediction_service_loop())

    async def _prediction_service_loop(self):
        """Main prediction service loop"""
        while self.is_running:
            try:
                # Generate predictions
                await self._generate_all_predictions()

                # Detect anomalies
                await self._detect_anomalies()

                # Analyze trends
                await self._analyze_trends()

                # Retrain models if needed
                await self._retrain_models()

                # Wait for next cycle
                await asyncio.sleep(3600)  # Run every hour

            except Exception as e:
                logger.error(f"Error in prediction service loop: {e}")
                await asyncio.sleep(1800)  # Wait 30 minutes on error

    async def _generate_all_predictions(self):
        """Generate predictions for all active models"""
        try:
            for model_id, model in self.models.items():
                if model.is_active:
                    await self._generate_prediction(model)

        except Exception as e:
            logger.error(f"Error generating predictions: {e}")

    async def _generate_prediction(self, model: PredictionModel):
        """Generate prediction for a specific model"""
        try:
            # Get historical data
            historical_data = await self._get_historical_data(model.target_metric, 30)

            if len(historical_data) < 5:
                logger.warning(f"Insufficient data for prediction model {model.model_id}")
                return

            # Make prediction based on model type
            if model.model_type == ModelType.LINEAR_REGRESSION:
                prediction_result = await self._linear_regression_prediction(model, historical_data)
            elif model.model_type == ModelType.MOVING_AVERAGE:
                prediction_result = await self._moving_average_prediction(model, historical_data)
            elif model.model_type == ModelType.EXPONENTIAL_SMOOTHING:
                prediction_result = await self._exponential_smoothing_prediction(model, historical_data)
            else:
                logger.warning(f"Unsupported model type: {model.model_type}")
                return

            # Store prediction
            self.predictions[prediction_result.prediction_id] = prediction_result
            self._store_prediction(prediction_result)

        except Exception as e:
            logger.error(f"Error generating prediction for model {model.model_id}: {e}")

    async def _get_historical_data(self, metric_name: str, days: int) -> List[float]:
        """Get historical data for a metric"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                if metric_name == "cost":
                    cursor = conn.execute('''
                        SELECT DATE(timestamp) as date, SUM(total_cost) as value
                        FROM cost_records
                        WHERE timestamp >= datetime('now', '-{} days')
                        GROUP BY date
                        ORDER BY date
                    '''.format(days))
                elif metric_name == "users":
                    cursor = conn.execute('''
                        SELECT DATE(timestamp) as date, COUNT(DISTINCT user_id) as value
                        FROM analytics_events
                        WHERE timestamp >= datetime('now', '-{} days')
                        GROUP BY date
                        ORDER BY date
                    '''.format(days))
                elif metric_name == "cpu_usage":
                    cursor = conn.execute('''
                        SELECT DATE(timestamp) as date, AVG(cpu_percent) as value
                        FROM system_metrics
                        WHERE timestamp >= datetime('now', '-{} days')
                        GROUP BY date
                        ORDER BY date
                    '''.format(days))
                else:
                    # Generic metric query
                    cursor = conn.execute('''
                        SELECT DATE(timestamp) as date, AVG(CAST(metrics as REAL)) as value
                        FROM analytics_events
                        WHERE timestamp >= datetime('now', '-{} days')
                        AND metrics LIKE ?
                        GROUP BY date
                        ORDER BY date
                    '''.format(days, (f'%"{metric_name}"%',)))

                results = cursor.fetchall()
                return [row[1] for row in results if row[1] is not None]

        except Exception as e:
            logger.error(f"Error getting historical data for {metric_name}: {e}")
            return []

    async def _linear_regression_prediction(self, model: PredictionModel, historical_data: List[float]) -> PredictionResult:
        """Generate prediction using linear regression"""
        try:
            if len(historical_data) < 2:
                return None

            # Prepare data
            X = np.array(range(len(historical_data))).reshape(-1, 1)
            y = np.array(historical_data)

            # Train model
            lr_model = LinearRegression()
            lr_model.fit(X, y)

            # Make prediction for next period
            next_x = np.array([[len(historical_data)]])
            predicted_value = lr_model.predict(next_x)[0]

            # Calculate confidence interval (simplified)
            residuals = y - lr_model.predict(X)
            residual_std = np.std(residuals)
            confidence_interval = (
                max(0, predicted_value - 1.96 * residual_std),
                predicted_value + 1.96 * residual_std
            )

            # Calculate accuracy score
            accuracy = max(0, 1 - (residual_std / np.mean(y))) if np.mean(y) > 0 else 0.5

            # Save model
            model_file = self.model_cache_dir / f"{model.model_id}.joblib"
            joblib.dump(lr_model, model_file)

            return PredictionResult(
                prediction_id=str(uuid.uuid4()),
                prediction_type=PredictionType.USAGE_FORECAST,
                model_id=model.model_id,
                predicted_value=predicted_value,
                confidence_interval=confidence_interval,
                confidence_level=0.95,
                prediction_horizon="1d",
                accuracy_score=accuracy,
                created_at=datetime.now(),
                metadata={"model_type": "linear_regression", "training_samples": len(historical_data)}
            )

        except Exception as e:
            logger.error(f"Error in linear regression prediction: {e}")
            return None

    async def _moving_average_prediction(self, model: PredictionModel, historical_data: List[float]) -> PredictionResult:
        """Generate prediction using moving average"""
        try:
            if len(historical_data) < 3:
                return None

            window_size = min(7, len(historical_data) // 2)
            if window_size < 2:
                window_size = 2

            # Calculate moving average
            moving_avg = []
            for i in range(window_size, len(historical_data)):
                avg = np.mean(historical_data[i-window_size:i])
                moving_avg.append(avg)

            # Predict next value
            predicted_value = np.mean(moving_avg[-3:]) if len(moving_avg) >= 3 else np.mean(moving_avg)

            # Calculate confidence interval
            if len(moving_avg) > 1:
                std_dev = np.std(moving_avg)
                confidence_interval = (
                    max(0, predicted_value - 1.96 * std_dev),
                    predicted_value + 1.96 * std_dev
                )
            else:
                confidence_interval = (predicted_value * 0.8, predicted_value * 1.2)

            # Calculate accuracy based on recent performance
            recent_actual = historical_data[-window_size:]
            recent_predicted = [predicted_value] * len(recent_actual)
            mae = mean_absolute_error(recent_actual, recent_predicted)
            accuracy = max(0, 1 - (mae / np.mean(recent_actual))) if np.mean(recent_actual) > 0 else 0.5

            return PredictionResult(
                prediction_id=str(uuid.uuid4()),
                prediction_type=PredictionType.USAGE_FORECAST,
                model_id=model.model_id,
                predicted_value=predicted_value,
                confidence_interval=confidence_interval,
                confidence_level=0.85,
                prediction_horizon="1d",
                accuracy_score=accuracy,
                created_at=datetime.now(),
                metadata={"model_type": "moving_average", "window_size": window_size}
            )

        except Exception as e:
            logger.error(f"Error in moving average prediction: {e}")
            return None

    async def _exponential_smoothing_prediction(self, model: PredictionModel, historical_data: List[float]) -> PredictionResult:
        """Generate prediction using exponential smoothing"""
        try:
            if len(historical_data) < 2:
                return None

            alpha = model.hyperparameters.get('alpha', 0.3)  # Smoothing parameter

            # Apply exponential smoothing
            smoothed_values = [historical_data[0]]
            for i in range(1, len(historical_data)):
                smoothed_value = alpha * historical_data[i] + (1 - alpha) * smoothed_values[i-1]
                smoothed_values.append(smoothed_value)

            # Predict next value
            predicted_value = smoothed_values[-1]

            # Calculate confidence interval
            residuals = [historical_data[i] - smoothed_values[i] for i in range(len(historical_data))]
            residual_std = np.std(residuals) if len(residuals) > 1 else predicted_value * 0.1

            confidence_interval = (
                max(0, predicted_value - 1.96 * residual_std),
                predicted_value + 1.96 * residual_std
            )

            # Calculate accuracy
            mae = mean_absolute_error(historical_data, smoothed_values)
            accuracy = max(0, 1 - (mae / np.mean(historical_data))) if np.mean(historical_data) > 0 else 0.5

            return PredictionResult(
                prediction_id=str(uuid.uuid4()),
                prediction_type=PredictionType.USAGE_FORECAST,
                model_id=model.model_id,
                predicted_value=predicted_value,
                confidence_interval=confidence_interval,
                confidence_level=0.90,
                prediction_horizon="1d",
                accuracy_score=accuracy,
                created_at=datetime.now(),
                metadata={"model_type": "exponential_smoothing", "alpha": alpha}
            )

        except Exception as e:
            logger.error(f"Error in exponential smoothing prediction: {e}")
            return None

    def _store_prediction(self, prediction: PredictionResult):
        """Store prediction in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO predictions
                    (prediction_id, prediction_type, model_id, predicted_value,
                     confidence_interval_low, confidence_interval_high, confidence_level,
                     prediction_horizon, actual_value, accuracy_score, created_at, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    prediction.prediction_id,
                    prediction.prediction_type.value,
                    prediction.model_id,
                    prediction.predicted_value,
                    prediction.confidence_interval[0],
                    prediction.confidence_interval[1],
                    prediction.confidence_level,
                    prediction.prediction_horizon,
                    prediction.actual_value,
                    prediction.accuracy_score,
                    prediction.created_at,
                    json.dumps(prediction.metadata)
                ))
        except Exception as e:
            logger.error(f"Error storing prediction: {e}")

    async def _detect_anomalies(self):
        """Detect anomalies in system metrics"""
        try:
            # Check various metrics for anomalies
            metrics_to_check = [
                ("cpu_usage", "system_metrics", "cpu_percent"),
                ("memory_usage", "system_metrics", "memory_percent"),
                ("daily_cost", "cost_records", "total_cost"),
                ("user_activity", "analytics_events", "user_id")
            ]

            for metric_name, table, column in metrics_to_check:
                await self._detect_metric_anomalies(metric_name, table, column)

        except Exception as e:
            logger.error(f"Error detecting anomalies: {e}")

    async def _detect_metric_anomalies(self, metric_name: str, table: str, column: str):
        """Detect anomalies for a specific metric"""
        try:
            # Get recent data
            with sqlite3.connect(self.db_path) as conn:
                if column == "total_cost":
                    cursor = conn.execute(f'''
                        SELECT DATE(timestamp) as date, SUM({column}) as value
                        FROM {table}
                        WHERE timestamp >= datetime('now', '-7 days')
                        GROUP BY date
                        ORDER BY date
                    ''')
                elif column == "user_id":
                    cursor = conn.execute(f'''
                        SELECT DATE(timestamp) as date, COUNT(DISTINCT {column}) as value
                        FROM {table}
                        WHERE timestamp >= datetime('now', '-7 days')
                        GROUP BY date
                        ORDER BY date
                    ''')
                else:
                    cursor = conn.execute(f'''
                        SELECT DATE(timestamp) as date, AVG({column}) as value
                        FROM {table}
                        WHERE timestamp >= datetime('now', '-7 days')
                        GROUP BY date
                        ORDER BY date
                    ''')

                results = cursor.fetchall()

            if len(results) < 3:
                return

            values = [row[1] for row in results if row[1] is not None]

            # Use statistical methods for anomaly detection
            mean_val = np.mean(values)
            std_val = np.std(values)

            # Check for anomalies in recent data
            latest_value = values[-1] if values else 0
            z_score = abs((latest_value - mean_val) / std_val) if std_val > 0 else 0

            if z_score > 2.5:  # Significant anomaly
                # Calculate expected range
                expected_range = (mean_val - 2 * std_val, mean_val + 2 * std_val)

                # Calculate severity score
                severity_score = min(100, (z_score - 2.5) * 20)

                alert = AnomalyAlert(
                    alert_id=str(uuid.uuid4()),
                    metric_name=metric_name,
                    anomaly_value=latest_value,
                    expected_range=expected_range,
                    severity_score=severity_score,
                    detection_method="statistical_z_score",
                    timestamp=datetime.now(),
                    recommendations=self._generate_anomaly_recommendations(metric_name, latest_value, expected_range)
                )

                self.anomaly_alerts.append(alert)
                self._store_anomaly_alert(alert)

        except Exception as e:
            logger.error(f"Error detecting anomalies for {metric_name}: {e}")

    def _generate_anomaly_recommendations(self, metric_name: str, anomaly_value: float, expected_range: Tuple[float, float]) -> List[str]:
        """Generate recommendations for anomaly resolution"""
        recommendations = []

        if metric_name == "cpu_usage":
            if anomaly_value > expected_range[1]:
                recommendations.extend([
                    "Identify CPU-intensive processes",
                    "Consider load balancing",
                    "Optimize resource allocation"
                ])
        elif metric_name == "memory_usage":
            if anomaly_value > expected_range[1]:
                recommendations.extend([
                    "Check for memory leaks",
                    "Clear cache if applicable",
                    "Monitor memory-intensive operations"
                ])
        elif metric_name == "daily_cost":
            if anomaly_value > expected_range[1]:
                recommendations.extend([
                    "Review recent cost increases",
                    "Optimize API usage",
                    "Consider cost-effective alternatives"
                ])
        elif metric_name == "user_activity":
            if anomaly_value < expected_range[0]:
                recommendations.extend([
                    "Investigate user engagement drop",
                    "Check service availability",
                    "Review recent changes"
                ])

        return recommendations if recommendations else ["Investigate the cause of this anomaly"]

    def _store_anomaly_alert(self, alert: AnomalyAlert):
        """Store anomaly alert in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO anomaly_alerts
                    (alert_id, metric_name, anomaly_value, expected_range_low,
                     expected_range_high, severity_score, detection_method, timestamp,
                     root_cause_analysis, recommendations)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    alert.alert_id,
                    alert.metric_name,
                    alert.anomaly_value,
                    alert.expected_range[0],
                    alert.expected_range[1],
                    alert.severity_score,
                    alert.detection_method,
                    alert.timestamp,
                    alert.root_cause_analysis,
                    json.dumps(alert.recommendations)
                ))
        except Exception as e:
            logger.error(f"Error storing anomaly alert: {e}")

    async def _analyze_trends(self):
        """Analyze trends in various metrics"""
        try:
            metrics_to_analyze = [
                "cost",
                "users",
                "cpu_usage",
                "memory_usage"
            ]

            for metric in metrics_to_analyze:
                await self._analyze_metric_trend(metric)

        except Exception as e:
            logger.error(f"Error analyzing trends: {e}")

    async def _analyze_metric_trend(self, metric_name: str):
        """Analyze trend for a specific metric"""
        try:
            historical_data = await self._get_historical_data(metric_name, 30)

            if len(historical_data) < 5:
                return

            # Calculate trend using linear regression
            X = np.array(range(len(historical_data))).reshape(-1, 1)
            y = np.array(historical_data)

            lr_model = LinearRegression()
            lr_model.fit(X, y)

            slope = lr_model.coef_[0]
            r_squared = lr_model.score(X, y)

            # Determine trend direction
            if abs(slope) < 0.01:
                trend_direction = "stable"
            elif slope > 0:
                trend_direction = "increasing"
            else:
                trend_direction = "decreasing"

            # Calculate trend strength (normalized)
            trend_strength = min(1.0, abs(slope) / np.mean(y) if np.mean(y) > 0 else 0)

            # Calculate trend significance
            trend_significance = r_squared

            # Detect change points (simplified)
            change_points = []
            for i in range(1, len(historical_data) - 1):
                if abs(historical_data[i] - historical_data[i-1]) > np.std(historical_data) * 2:
                    change_points.append(datetime.now() - timedelta(days=len(historical_data) - i))

            trend_analysis = TrendAnalysis(
                trend_id=str(uuid.uuid4()),
                metric_name=metric_name,
                trend_direction=trend_direction,
                trend_strength=trend_strength,
                trend_significance=trend_significance,
                change_points=change_points,
                forecast_period="30d",
                created_at=datetime.now()
            )

            self.trend_analyses[metric_name] = trend_analysis
            self._store_trend_analysis(trend_analysis)

        except Exception as e:
            logger.error(f"Error analyzing trend for {metric_name}: {e}")

    def _store_trend_analysis(self, trend: TrendAnalysis):
        """Store trend analysis in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO trend_analyses
                    (trend_id, metric_name, trend_direction, trend_strength,
                     trend_significance, change_points, forecast_period, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    trend.trend_id,
                    trend.metric_name,
                    trend.trend_direction,
                    trend.trend_strength,
                    trend.trend_significance,
                    json.dumps([cp.isoformat() for cp in trend.change_points]),
                    trend.forecast_period,
                    trend.created_at
                ))
        except Exception as e:
            logger.error(f"Error storing trend analysis: {e}")

    async def _retrain_models(self):
        """Retrain models periodically"""
        try:
            # Check if models need retraining (e.g., weekly)
            for model_id, model in self.models.items():
                days_since_training = (datetime.now() - model.last_trained).days
                if days_since_training >= 7:  # Retrain weekly
                    await self._retrain_model(model)

        except Exception as e:
            logger.error(f"Error retraining models: {e}")

    async def _retrain_model(self, model: PredictionModel):
        """Retrain a specific model"""
        try:
            # Get fresh historical data
            historical_data = await self._get_historical_data(model.target_metric, 60)  # 60 days for retraining

            if len(historical_data) < 10:
                logger.warning(f"Insufficient data for retraining model {model.model_id}")
                return

            # Retrain based on model type
            if model.model_type == ModelType.LINEAR_REGRESSION:
                new_model = await self._linear_regression_prediction(model, historical_data)
            elif model.model_type == ModelType.MOVING_AVERAGE:
                new_model = await self._moving_average_prediction(model, historical_data)
            elif model.model_type == ModelType.EXPONENTIAL_SMOOTHING:
                new_model = await self._exponential_smoothing_prediction(model, historical_data)
            else:
                return

            if new_model and new_model.accuracy_score > model.accuracy_score:
                # Update model
                model.accuracy_score = new_model.accuracy_score
                model.last_trained = datetime.now()
                self._update_model_in_db(model)

                logger.info(f"Retrained model {model.model_id} with new accuracy: {new_model.accuracy_score:.3f}")

        except Exception as e:
            logger.error(f"Error retraining model {model.model_id}: {e}")

    def _update_model_in_db(self, model: PredictionModel):
        """Update model in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    UPDATE prediction_models
                    SET accuracy_score = ?, last_trained = ?
                    WHERE model_id = ?
                ''', (model.accuracy_score, model.last_trained, model.model_id))
        except Exception as e:
            logger.error(f"Error updating model in database: {e}")

    # Public API Methods
    def create_prediction_model(self, model_type: ModelType, target_metric: str,
                              features: List[str], hyperparameters: Dict[str, Any] = None) -> str:
        """Create a new prediction model"""
        try:
            model_id = str(uuid.uuid4())
            model = PredictionModel(
                model_id=model_id,
                model_type=model_type,
                target_metric=target_metric,
                features=features,
                hyperparameters=hyperparameters or {},
                accuracy_score=0.0,
                last_trained=datetime.now()
            )

            self.models[model_id] = model

            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO prediction_models
                    (model_id, model_type, target_metric, features, hyperparameters,
                     accuracy_score, last_trained, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    model.model_id,
                    model.model_type.value,
                    model.target_metric,
                    json.dumps(model.features),
                    json.dumps(model.hyperparameters),
                    model.accuracy_score,
                    model.last_trained,
                    model.is_active
                ))

            # Generate initial prediction
            asyncio.create_task(self._generate_prediction(model))

            return model_id

        except Exception as e:
            logger.error(f"Error creating prediction model: {e}")
            return None

    def get_predictions(self, metric_name: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get predictions, optionally filtered by metric"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                if metric_name:
                    cursor = conn.execute('''
                        SELECT p.*, m.target_metric
                        FROM predictions p
                        JOIN prediction_models m ON p.model_id = m.model_id
                        WHERE m.target_metric = ?
                        ORDER BY p.created_at DESC
                        LIMIT ?
                    ''', (metric_name, limit))
                else:
                    cursor = conn.execute('''
                        SELECT p.*, m.target_metric
                        FROM predictions p
                        JOIN prediction_models m ON p.model_id = m.model_id
                        ORDER BY p.created_at DESC
                        LIMIT ?
                    ''', (limit,))

                predictions = []
                for row in cursor.fetchall():
                    predictions.append({
                        'prediction_id': row[0],
                        'prediction_type': row[1],
                        'model_id': row[2],
                        'predicted_value': row[3],
                        'confidence_interval': (row[4], row[5]),
                        'confidence_level': row[6],
                        'prediction_horizon': row[7],
                        'actual_value': row[8],
                        'accuracy_score': row[9],
                        'created_at': row[10],
                        'target_metric': row[11],
                        'metadata': json.loads(row[12]) if row[12] else {}
                    })

                return predictions

        except Exception as e:
            logger.error(f"Error getting predictions: {e}")
            return []

    def get_anomaly_alerts(self, resolved: bool = False, limit: int = 50) -> List[Dict[str, Any]]:
        """Get anomaly alerts"""
        try:
            filtered_alerts = [alert for alert in self.anomaly_alerts
                              if alert.is_resolved == resolved][:limit]

            return [
                {
                    'alert_id': alert.alert_id,
                    'metric_name': alert.metric_name,
                    'anomaly_value': alert.anomaly_value,
                    'expected_range': alert.expected_range,
                    'severity_score': alert.severity_score,
                    'detection_method': alert.detection_method,
                    'timestamp': alert.timestamp.isoformat(),
                    'is_resolved': alert.is_resolved,
                    'recommendations': alert.recommendations
                }
                for alert in filtered_alerts
            ]

        except Exception as e:
            logger.error(f"Error getting anomaly alerts: {e}")
            return []

    def get_trend_analyses(self, metric_name: str = None) -> List[Dict[str, Any]]:
        """Get trend analyses"""
        try:
            analyses = []
            for trend_id, trend in self.trend_analyses.items():
                if metric_name is None or trend.metric_name == metric_name:
                    analyses.append({
                        'trend_id': trend.trend_id,
                        'metric_name': trend.metric_name,
                        'trend_direction': trend.trend_direction,
                        'trend_strength': trend.trend_strength,
                        'trend_significance': trend.trend_significance,
                        'change_points': [cp.isoformat() for cp in trend.change_points],
                        'forecast_period': trend.forecast_period,
                        'created_at': trend.created_at.isoformat()
                    })

            return analyses

        except Exception as e:
            logger.error(f"Error getting trend analyses: {e}")
            return []

    def get_forecast(self, metric_name: str, days: int = 7) -> Dict[str, Any]:
        """Get forecast for a specific metric"""
        try:
            # Find the best model for this metric
            best_model = None
            best_accuracy = 0.0

            for model in self.models.values():
                if model.target_metric == metric_name and model.is_active:
                    if model.accuracy_score > best_accuracy:
                        best_accuracy = model.accuracy_score
                        best_model = model

            if not best_model:
                return {"error": "No model available for this metric"}

            # Generate multi-day forecast
            historical_data = await self._get_historical_data(metric_name, 30)
            forecast_values = []
            confidence_intervals = []

            for day in range(days):
                # Generate prediction for each day
                if best_model.model_type == ModelType.LINEAR_REGRESSION:
                    prediction = await self._linear_regression_prediction(best_model, historical_data + forecast_values)
                elif best_model.model_type == ModelType.MOVING_AVERAGE:
                    prediction = await self._moving_average_prediction(best_model, historical_data + forecast_values)
                elif best_model.model_type == ModelType.EXPONENTIAL_SMOOTHING:
                    prediction = await self._exponential_smoothing_prediction(best_model, historical_data + forecast_values)
                else:
                    break

                if prediction:
                    forecast_values.append(prediction.predicted_value)
                    confidence_intervals.append(prediction.confidence_interval)

            return {
                'metric_name': metric_name,
                'forecast_period': f"{days}d",
                'model_used': best_model.model_id,
                'model_accuracy': best_model.accuracy_score,
                'forecast_values': forecast_values,
                'confidence_intervals': confidence_intervals,
                'created_at': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error getting forecast for {metric_name}: {e}")
            return {"error": str(e)}

    def resolve_anomaly(self, alert_id: str):
        """Resolve an anomaly alert"""
        for alert in self.anomaly_alerts:
            if alert.alert_id == alert_id:
                alert.is_resolved = True
                break

    def get_model_performance(self, model_id: str = None) -> Dict[str, Any]:
        """Get model performance metrics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                if model_id:
                    cursor = conn.execute('''
                        SELECT AVG(absolute_error), AVG(error), COUNT(*)
                        FROM model_performance
                        WHERE model_id = ?
                    ''', (model_id,))
                else:
                    cursor = conn.execute('''
                        SELECT m.model_id, m.target_metric, AVG(mp.absolute_error), AVG(mp.error), COUNT(mp.*)
                        FROM model_performance mp
                        JOIN prediction_models m ON mp.model_id = m.model_id
                        GROUP BY m.model_id, m.target_metric
                    ''')

                results = cursor.fetchall()

                if model_id and results:
                    return {
                        'model_id': model_id,
                        'average_absolute_error': results[0][0],
                        'average_error': results[0][1],
                        'total_predictions': results[0][2]
                    }
                else:
                    return {
                        'models': [
                            {
                                'model_id': row[0],
                                'target_metric': row[1],
                                'average_absolute_error': row[2],
                                'average_error': row[3],
                                'total_predictions': row[4]
                            }
                            for row in results
                        ]
                    }

        except Exception as e:
            logger.error(f"Error getting model performance: {e}")
            return {}

    def cleanup_old_data(self, retention_days: int = 90):
        """Clean up old predictive analytics data"""
        try:
            cutoff_date = datetime.now() - timedelta(days=retention_days)

            with sqlite3.connect(self.db_path) as conn:
                tables = ['predictions', 'anomaly_alerts', 'model_performance']
                for table in tables:
                    conn.execute(f'DELETE FROM {table} WHERE timestamp < ? OR created_at < ?', (cutoff_date, cutoff_date))

            logger.info(f"Cleaned up predictive analytics data older than {retention_days} days")

        except Exception as e:
            logger.error(f"Error cleaning up predictive analytics data: {e}")

    def stop(self):
        """Stop the predictive analytics engine"""
        self.is_running = False