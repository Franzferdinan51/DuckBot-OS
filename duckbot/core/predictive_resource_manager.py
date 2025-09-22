#!/usr/bin/env python3
"""
ML-based Predictive Resource Management for DuckBot v4.2
Uses machine learning to predict system resource needs and optimize allocation
"""

import numpy as np
import pandas as pd
import sqlite3
import threading
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import logging
from sklearn.ensemble import RandomForestRegressor, IsolationForest
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error
import joblib
import psutil
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

@dataclass
class ResourcePrediction:
    """Prediction for system resource usage"""
    timestamp: datetime
    predicted_ram_gb: float
    predicted_vram_gb: float
    predicted_cpu_percent: float
    confidence: float
    prediction_window_minutes: int
    anomaly_detected: bool
    anomaly_score: float

@dataclass
class ResourceAllocation:
    """Recommended resource allocation"""
    ram_allocation_gb: float
    vram_allocation_gb: float
    cpu_allocation_percent: float
    model_loading_recommendations: List[str]
    cleanup_recommendations: List[str]
    optimization_actions: List[str]

class PredictiveResourceManager:
    """ML-based predictive resource management system"""

    def __init__(self, db_path: str = None, model_dir: str = None):
        self.db_path = db_path or str(Path(__file__).parent / "resource_predictions.db")
        self.model_dir = model_dir or str(Path(__file__).parent / "ml_models")

        # Ensure directories exist
        Path(self.model_dir).mkdir(parents=True, exist_ok=True)

        # Initialize ML models
        self.ram_predictor = None
        self.vram_predictor = None
        self.cpu_predictor = None
        self.anomaly_detector = None
        self.scaler = StandardScaler()

        # Training data
        self.feature_columns = [
            'hour_of_day', 'day_of_week', 'is_weekend', 'loaded_models_count',
            'active_services_count', 'recent_requests_count', 'avg_request_size',
            'current_ram_usage', 'current_vram_usage', 'current_cpu_usage',
            'ram_trend_1h', 'vram_trend_1h', 'cpu_trend_1h',
            'ram_trend_24h', 'vram_trend_24h', 'cpu_trend_24h'
        ]

        # Performance tracking
        self.prediction_accuracy = {
            'ram_mae': 0.0,
            'vram_mae': 0.0,
            'cpu_mae': 0.0,
            'predictions_count': 0,
            'last_training': None
        }

        # Threading
        self.lock = threading.RLock()
        self._init_database()
        self._load_models()

        # Start continuous monitoring
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(target=self._continuous_monitoring, daemon=True)
        self.monitor_thread.start()

    def _init_database(self):
        """Initialize database for resource monitoring and predictions"""
        with sqlite3.connect(self.db_path) as conn:
            # Resource usage history
            conn.execute('''
                CREATE TABLE IF NOT EXISTS resource_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    ram_usage_gb REAL NOT NULL,
                    vram_usage_gb REAL NOT NULL,
                    cpu_usage_percent REAL NOT NULL,
                    loaded_models_count INTEGER NOT NULL,
                    active_services_count INTEGER NOT NULL,
                    recent_requests_count INTEGER NOT NULL,
                    avg_request_size INTEGER NOT NULL,
                    system_load_score REAL NOT NULL
                )
            ''')

            # Predictions history
            conn.execute('''
                CREATE TABLE IF NOT EXISTS resource_predictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    prediction_window_minutes INTEGER NOT NULL,
                    predicted_ram_gb REAL NOT NULL,
                    predicted_vram_gb REAL NOT NULL,
                    predicted_cpu_percent REAL NOT NULL,
                    confidence REAL NOT NULL,
                    actual_ram_gb REAL,
                    actual_vram_gb REAL,
                    actual_cpu_percent REAL,
                    prediction_error_ram REAL,
                    prediction_error_vram REAL,
                    prediction_error_cpu REAL
                )
            ''')

            # Anomaly detection history
            conn.execute('''
                CREATE TABLE IF NOT EXISTS resource_anomalies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    anomaly_type TEXT NOT NULL,
                    severity_score REAL NOT NULL,
                    description TEXT NOT NULL,
                    resolved BOOLEAN DEFAULT FALSE,
                    resolution_timestamp DATETIME
                )
            ''')

            # Create indexes
            conn.execute('CREATE INDEX IF NOT EXISTS idx_resource_usage_timestamp ON resource_usage(timestamp)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_predictions_timestamp ON resource_predictions(timestamp)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_anomalies_timestamp ON resource_anomalies(timestamp)')

    def _load_models(self):
        """Load trained ML models or initialize new ones"""
        try:
            # Try to load existing models
            ram_model_path = Path(self.model_dir) / "ram_predictor.joblib"
            vram_model_path = Path(self.model_dir) / "vram_predictor.joblib"
            cpu_model_path = Path(self.model_dir) / "cpu_predictor.joblib"
            anomaly_model_path = Path(self.model_dir) / "anomaly_detector.joblib"
            scaler_path = Path(self.model_dir) / "scaler.joblib"

            if ram_model_path.exists():
                self.ram_predictor = joblib.load(ram_model_path)
                self.vram_predictor = joblib.load(vram_model_path)
                self.cpu_predictor = joblib.load(cpu_model_path)
                self.anomaly_detector = joblib.load(anomaly_model_path)
                self.scaler = joblib.load(scaler_path)
                logger.info("Loaded existing ML models")
            else:
                # Initialize new models
                self._initialize_models()
                logger.info("Initialized new ML models")
        except Exception as e:
            logger.error(f"Error loading models: {e}")
            self._initialize_models()

    def _initialize_models(self):
        """Initialize new ML models"""
        self.ram_predictor = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
        self.vram_predictor = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
        self.cpu_predictor = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
        self.anomaly_detector = IsolationForest(
            contamination=0.1,
            random_state=42,
            n_jobs=-1
        )

    def record_resource_usage(self, ram_usage_gb: float, vram_usage_gb: float,
                             cpu_usage_percent: float, loaded_models_count: int = 0,
                             active_services_count: int = 0, recent_requests_count: int = 0,
                             avg_request_size: int = 0):
        """Record current resource usage for training and monitoring"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO resource_usage
                (timestamp, ram_usage_gb, vram_usage_gb, cpu_usage_percent,
                 loaded_models_count, active_services_count, recent_requests_count,
                 avg_request_size, system_load_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now(), ram_usage_gb, vram_usage_gb, cpu_usage_percent,
                loaded_models_count, active_services_count, recent_requests_count,
                avg_request_size, self._calculate_system_load_score(
                    ram_usage_gb, vram_usage_gb, cpu_usage_percent
                )
            ))

    def _calculate_system_load_score(self, ram_gb: float, vram_gb: float, cpu_percent: float) -> float:
        """Calculate overall system load score (0-100)"""
        # Normalize to 0-100 scale (assuming typical max values)
        ram_score = min(ram_gb / 32.0 * 100, 100)  # 32GB max
        vram_score = min(vram_gb / 16.0 * 100, 100)  # 16GB max
        cpu_score = cpu_percent

        return (ram_score * 0.4 + vram_score * 0.4 + cpu_score * 0.2)

    def get_historical_data(self, hours: int = 24) -> pd.DataFrame:
        """Get historical resource usage data for training"""
        start_time = datetime.now() - timedelta(hours=hours)

        with sqlite3.connect(self.db_path) as conn:
            df = pd.read_sql_query('''
                SELECT * FROM resource_usage
                WHERE timestamp >= ?
                ORDER BY timestamp
            ''', conn, params=(start_time,))

        if df.empty:
            return df

        # Feature engineering
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['hour_of_day'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)

        # Calculate trends
        for resource in ['ram_usage_gb', 'vram_usage_gb', 'cpu_usage_percent']:
            # 1-hour trend
            df[f'{resource}_trend_1h'] = df[resource].rolling(window=12, min_periods=1).mean()
            # 24-hour trend
            df[f'{resource}_trend_24h'] = df[resource].rolling(window=288, min_periods=1).mean()

        return df

    def train_models(self, retrain: bool = False):
        """Train ML models on historical data"""
        with self.lock:
            # Get training data
            df = self.get_historical_data(hours=168)  # 7 days of data

            if len(df) < 100:  # Need minimum data
                logger.warning("Insufficient data for training models")
                return False

            # Prepare features
            X = df[self.feature_columns].copy()
            y_ram = df['ram_usage_gb']
            y_vram = df['vram_usage_gb']
            y_cpu = df['cpu_usage_percent']

            # Split data
            X_train, X_test, y_ram_train, y_ram_test = train_test_split(
                X, y_ram, test_size=0.2, random_state=42
            )
            _, _, y_vram_train, y_vram_test = train_test_split(
                X, y_vram, test_size=0.2, random_state=42
            )
            _, _, y_cpu_train, y_cpu_test = train_test_split(
                X, y_cpu, test_size=0.2, random_state=42
            )

            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)

            # Train models
            self.ram_predictor.fit(X_train_scaled, y_ram_train)
            self.vram_predictor.fit(X_train_scaled, y_vram_train)
            self.cpu_predictor.fit(X_train_scaled, y_cpu_train)

            # Evaluate models
            ram_pred = self.ram_predictor.predict(X_test_scaled)
            vram_pred = self.vram_predictor.predict(X_test_scaled)
            cpu_pred = self.cpu_predictor.predict(X_test_scaled)

            self.prediction_accuracy.update({
                'ram_mae': mean_absolute_error(y_ram_test, ram_pred),
                'vram_mae': mean_absolute_error(y_vram_test, vram_pred),
                'cpu_mae': mean_absolute_error(y_cpu_test, cpu_pred),
                'predictions_count': len(y_ram_test),
                'last_training': datetime.now()
            })

            # Train anomaly detector
            all_features = self.scaler.transform(X)
            self.anomaly_detector.fit(all_features)

            # Save models
            self._save_models()

            logger.info(f"Models trained successfully. RAM MAE: {self.prediction_accuracy['ram_mae']:.3f}GB, "
                       f"VRAM MAE: {self.prediction_accuracy['vram_mae']:.3f}GB, "
                       f"CPU MAE: {self.prediction_accuracy['cpu_mae']:.3f}%")

            return True

    def _save_models(self):
        """Save trained models to disk"""
        try:
            joblib.dump(self.ram_predictor, Path(self.model_dir) / "ram_predictor.joblib")
            joblib.dump(self.vram_predictor, Path(self.model_dir) / "vram_predictor.joblib")
            joblib.dump(self.cpu_predictor, Path(self.model_dir) / "cpu_predictor.joblib")
            joblib.dump(self.anomaly_detector, Path(self.model_dir) / "anomaly_detector.joblib")
            joblib.dump(self.scaler, Path(self.model_dir) / "scaler.joblib")
        except Exception as e:
            logger.error(f"Error saving models: {e}")

    def predict_resource_usage(self, minutes_ahead: int = 30) -> ResourcePrediction:
        """Predict resource usage for future time window"""
        if not all([self.ram_predictor, self.vram_predictor, self.cpu_predictor]):
            return ResourcePrediction(
                timestamp=datetime.now() + timedelta(minutes=minutes_ahead),
                predicted_ram_gb=0.0,
                predicted_vram_gb=0.0,
                predicted_cpu_percent=0.0,
                confidence=0.0,
                prediction_window_minutes=minutes_ahead,
                anomaly_detected=False,
                anomaly_score=0.0
            )

        # Get current features
        current_features = self._get_current_features()

        # Make prediction
        features_scaled = self.scaler.transform([current_features])

        ram_pred = self.ram_predictor.predict(features_scaled)[0]
        vram_pred = self.vram_predictor.predict(features_scaled)[0]
        cpu_pred = self.cpu_predictor.predict(features_scaled)[0]

        # Calculate confidence based on prediction accuracy
        confidence = max(0.0, 1.0 - (self.prediction_accuracy['ram_mae'] / max(ram_pred, 1.0)))

        # Detect anomalies
        anomaly_score = self.anomaly_detector.decision_function(features_scaled)[0]
        anomaly_detected = anomaly_score < 0  # Isolation Forest: negative = anomaly

        # Record prediction
        self._record_prediction(
            minutes_ahead, ram_pred, vram_pred, cpu_pred, confidence
        )

        return ResourcePrediction(
            timestamp=datetime.now() + timedelta(minutes=minutes_ahead),
            predicted_ram_gb=max(0, ram_pred),
            predicted_vram_gb=max(0, vram_pred),
            predicted_cpu_percent=max(0, min(100, cpu_pred)),
            confidence=confidence,
            prediction_window_minutes=minutes_ahead,
            anomaly_detected=anomaly_detected,
            anomaly_score=anomaly_score
        )

    def _get_current_features(self) -> List[float]:
        """Get current feature values for prediction"""
        current_time = datetime.now()

        # Get current system state
        current_ram = psutil.virtual_memory().used / (1024**3)
        current_vram = self._get_current_vram_usage()
        current_cpu = psutil.cpu_percent(interval=1)

        # Get recent trends (simplified)
        df_recent = self.get_historical_data(hours=2)
        if len(df_recent) > 0:
            ram_trend_1h = df_recent['ram_usage_gb'].mean()
            vram_trend_1h = df_recent['vram_usage_gb'].mean()
            cpu_trend_1h = df_recent['cpu_usage_percent'].mean()
        else:
            ram_trend_1h = current_ram
            vram_trend_1h = current_vram
            cpu_trend_1h = current_cpu

        # Get 24-hour trends
        df_24h = self.get_historical_data(hours=24)
        if len(df_24h) > 0:
            ram_trend_24h = df_24h['ram_usage_gb'].mean()
            vram_trend_24h = df_24h['vram_usage_gb'].mean()
            cpu_trend_24h = df_24h['cpu_usage_percent'].mean()
        else:
            ram_trend_24h = current_ram
            vram_trend_24h = current_vram
            cpu_trend_24h = current_cpu

        return [
            current_time.hour,
            current_time.weekday(),
            1 if current_time.weekday() >= 5 else 0,  # is_weekend
            self._get_loaded_models_count(),  # loaded_models_count
            self._get_active_services_count(),  # active_services_count
            self._get_recent_requests_count(),  # recent_requests_count
            self._get_avg_request_size(),  # avg_request_size
            current_ram,
            current_vram,
            current_cpu,
            ram_trend_1h,
            vram_trend_1h,
            cpu_trend_1h,
            ram_trend_24h,
            vram_trend_24h,
            cpu_trend_24h
        ]

    def _get_current_vram_usage(self) -> float:
        """Get current VRAM usage"""
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            if gpus:
                return sum(gpu.memoryUsed for gpu in gpus) / 1024.0  # Convert MB to GB
        except ImportError:
            pass
        return 0.0

    def _get_loaded_models_count(self) -> int:
        """Get count of currently loaded AI models"""
        # This would integrate with the dynamic model manager
        try:
            # For now, return a placeholder
            return 1
        except:
            return 0

    def _get_active_services_count(self) -> int:
        """Get count of active services"""
        # This would integrate with the service manager
        try:
            # For now, return a placeholder
            return 3
        except:
            return 0

    def _get_recent_requests_count(self) -> int:
        """Get count of recent AI requests"""
        # This would integrate with request tracking
        try:
            # For now, return a placeholder
            return 10
        except:
            return 0

    def _get_avg_request_size(self) -> int:
        """Get average request size in tokens"""
        # This would integrate with request tracking
        try:
            # For now, return a placeholder
            return 1000
        except:
            return 0

    def _record_prediction(self, minutes_ahead: int, ram_pred: float, vram_pred: float,
                          cpu_pred: float, confidence: float):
        """Record prediction for later accuracy evaluation"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO resource_predictions
                (timestamp, prediction_window_minutes, predicted_ram_gb,
                 predicted_vram_gb, predicted_cpu_percent, confidence)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now(), minutes_ahead, ram_pred, vram_pred, cpu_pred, confidence
            ))

    def get_resource_allocation_recommendations(self, prediction: ResourcePrediction) -> ResourceAllocation:
        """Get resource allocation recommendations based on predictions"""
        recommendations = ResourceAllocation(
            ram_allocation_gb=prediction.predicted_ram_gb * 1.2,  # 20% buffer
            vram_allocation_gb=prediction.predicted_vram_gb * 1.2,  # 20% buffer
            cpu_allocation_percent=min(90, prediction.predicted_cpu_percent + 10),
            model_loading_recommendations=[],
            cleanup_recommendations=[],
            optimization_actions=[]
        )

        # Model loading recommendations
        if prediction.predicted_ram_gb < 8:  # Low RAM usage
            recommendations.model_loading_recommendations.append(
                "Consider loading additional specialized models"
            )
        elif prediction.predicted_ram_gb > 16:  # High RAM usage
            recommendations.cleanup_recommendations.append(
                "Unload non-essential models to free memory"
            )

        # Cleanup recommendations
        if prediction.predicted_vram_gb > 12:  # High VRAM usage
            recommendations.cleanup_recommendations.append(
                "Consider unloading large AI models"
            )

        # Optimization actions
        if prediction.anomaly_detected:
            recommendations.optimization_actions.append(
                f"Anomaly detected (score: {prediction.anomaly_score:.2f}) - investigate resource usage"
            )

        if prediction.confidence < 0.7:
            recommendations.optimization_actions.append(
                "Low prediction confidence - consider manual monitoring"
            )

        # Performance-based recommendations
        if prediction.predicted_cpu_percent > 80:
            recommendations.optimization_actions.append(
                "High CPU usage predicted - consider load balancing"
            )

        return recommendations

    def detect_anomalies(self) -> List[Dict[str, Any]]:
        """Detect current resource usage anomalies"""
        current_features = self._get_current_features()

        if not self.anomaly_detector:
            return []

        features_scaled = self.scaler.transform([current_features])
        anomaly_score = self.anomaly_detector.decision_function(features_scaled)[0]

        anomalies = []

        if anomaly_score < 0:  # Anomaly detected
            anomaly_type = self._classify_anomaly(current_features)
            severity = abs(anomaly_score)

            anomalies.append({
                "type": anomaly_type,
                "severity": severity,
                "score": anomaly_score,
                "description": f"Resource usage anomaly detected: {anomaly_type}",
                "timestamp": datetime.now()
            })

            # Record anomaly
            self._record_anomaly(anomaly_type, severity, f"Anomaly detected: {anomaly_type}")

        return anomalies

    def _classify_anomaly(self, features: List[float]) -> str:
        """Classify the type of anomaly based on features"""
        current_ram = features[7]
        current_vram = features[8]
        current_cpu = features[9]

        if current_ram > 16:
            return "High Memory Usage"
        elif current_vram > 12:
            return "High VRAM Usage"
        elif current_cpu > 90:
            return "High CPU Usage"
        elif features[5] > 50:  # High request count
            return "High Request Volume"
        else:
            return "Unusual Pattern"

    def _record_anomaly(self, anomaly_type: str, severity: float, description: str):
        """Record anomaly in database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO resource_anomalies
                (timestamp, anomaly_type, severity_score, description)
                VALUES (?, ?, ?, ?)
            ''', (datetime.now(), anomaly_type, severity, description))

    def get_capacity_planning_insights(self, days_ahead: int = 7) -> Dict[str, Any]:
        """Get capacity planning insights for future needs"""
        # Get historical patterns
        df = self.get_historical_data(hours=24 * 7)  # 7 days

        if df.empty:
            return {"error": "Insufficient data for capacity planning"}

        # Analyze trends
        insights = {
            "current_trends": {
                "ram_growth_rate": self._calculate_growth_rate(df['ram_usage_gb']),
                "vram_growth_rate": self._calculate_growth_rate(df['vram_usage_gb']),
                "cpu_growth_rate": self._calculate_growth_rate(df['cpu_usage_percent'])
            },
            "peak_usage_patterns": self._analyze_peak_patterns(df),
            "capacity_recommendations": [],
            "risk_assessment": []
        }

        # Generate recommendations
        if insights["current_trends"]["ram_growth_rate"] > 0.1:  # 10% growth
            insights["capacity_recommendations"].append(
                "RAM usage growing rapidly - consider memory upgrades"
            )
            insights["risk_assessment"].append({
                "risk": "Memory capacity",
                "level": "medium",
                "timeline": f"{days_ahead} days"
            })

        if insights["current_trends"]["vram_growth_rate"] > 0.15:  # 15% growth
            insights["capacity_recommendations"].append(
                "VRAM usage growing rapidly - consider GPU upgrades"
            )
            insights["risk_assessment"].append({
                "risk": "GPU capacity",
                "level": "high",
                "timeline": f"{days_ahead} days"
            })

        return insights

    def _calculate_growth_rate(self, series: pd.Series) -> float:
        """Calculate growth rate for a time series"""
        if len(series) < 2:
            return 0.0

        # Simple linear regression to get trend
        x = np.arange(len(series))
        y = series.values

        slope = np.polyfit(x, y, 1)[0]
        mean_val = np.mean(y)

        return slope / mean_val if mean_val != 0 else 0.0

    def _analyze_peak_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze peak usage patterns"""
        patterns = {
            "daily_peak_hour": df['hour_of_day'].iloc[df['ram_usage_gb'].idxmax()],
            "weekly_peak_day": df['day_of_week'].iloc[df['ram_usage_gb'].idxmax()],
            "peak_ram_usage": df['ram_usage_gb'].max(),
            "peak_vram_usage": df['vram_usage_gb'].max(),
            "peak_cpu_usage": df['cpu_usage_percent'].max()
        }

        return patterns

    def _continuous_monitoring(self):
        """Continuous monitoring thread"""
        while self.monitoring_active:
            try:
                # Record current resource usage
                current_ram = psutil.virtual_memory().used / (1024**3)
                current_vram = self._get_current_vram_usage()
                current_cpu = psutil.cpu_percent(interval=1)

                self.record_resource_usage(
                    current_ram, current_vram, current_cpu,
                    self._get_loaded_models_count(),
                    self._get_active_services_count(),
                    self._get_recent_requests_count(),
                    self._get_avg_request_size()
                )

                # Check for anomalies
                anomalies = self.detect_anomalies()
                if anomalies:
                    logger.warning(f"Resource anomalies detected: {anomalies}")

                # Retrain models periodically
                if (self.prediction_accuracy['last_training'] is None or
                    (datetime.now() - self.prediction_accuracy['last_training']).days >= 1):
                    self.train_models(retrain=True)

                # Sleep for monitoring interval
                time.sleep(300)  # 5 minutes

            except Exception as e:
                logger.error(f"Error in continuous monitoring: {e}")
                time.sleep(60)  # Wait before retrying

    def shutdown(self):
        """Shutdown the resource manager"""
        self.monitoring_active = False
        if self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)

    def get_status(self) -> Dict[str, Any]:
        """Get current status of the predictive resource manager"""
        return {
            "models_trained": all([self.ram_predictor, self.vram_predictor, self.cpu_predictor]),
            "prediction_accuracy": self.prediction_accuracy,
            "monitoring_active": self.monitoring_active,
            "model_dir": self.model_dir,
            "database_path": self.db_path,
            "feature_count": len(self.feature_columns),
            "data_points": len(self.get_historical_data(hours=24))
        }

# Convenience functions
def get_predictive_resource_manager() -> PredictiveResourceManager:
    """Get a singleton instance of the predictive resource manager"""
    if not hasattr(get_predictive_resource_manager, '_instance'):
        get_predictive_resource_manager._instance = PredictiveResourceManager()
    return get_predictive_resource_manager._instance

def predict_resource_needs(minutes_ahead: int = 30) -> ResourcePrediction:
    """Predict resource needs for the specified time ahead"""
    manager = get_predictive_resource_manager()
    return manager.predict_resource_usage(minutes_ahead)

def get_optimal_resource_allocation() -> ResourceAllocation:
    """Get optimal resource allocation recommendations"""
    manager = get_predictive_resource_manager()
    prediction = manager.predict_resource_usage()
    return manager.get_resource_allocation_recommendations(prediction)