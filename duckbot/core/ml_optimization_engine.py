#!/usr/bin/env python3
"""
ML-Powered System Optimization for DuckBot v4.2
Advanced machine learning models for predictive performance optimization,
adaptive system management, and continuous learning
"""

import os
import sys
import json
import time
import pickle
import asyncio
import logging
import threading
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict, deque
import sqlite3
from pathlib import Path

# ML Framework Imports
try:
    from sklearn.ensemble import RandomForestRegressor, IsolationForest
    from sklearn.linear_model import LinearRegression, Ridge
    from sklearn.preprocessing import StandardScaler, MinMaxScaler
    from sklearn.model_selection import train_test_split, cross_val_score
    from sklearn.metrics import mean_squared_error, r2_score, classification_report
    from sklearn.cluster import KMeans, DBSCAN
    from sklearn.decomposition import PCA
    from sklearn.feature_selection import SelectKBest, f_regression
    import joblib
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("[WARNING] scikit-learn not available - ML optimization disabled")

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import Dataset, DataLoader
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    print("[WARNING] PyTorch not available - Deep learning models disabled")

# Local imports
try:
    from .hardware_detector import HardwareDetector
    from .dynamic_model_manager import DynamicModelManager
    from .logging_setup import setup_logger
    from .core.rate_limit import RateLimiter
except ImportError:
    HardwareDetector = None
    DynamicModelManager = None
    print("[WARNING] Core DuckBot modules not available")

logger = setup_logger(__name__)

class OptimizationMode(Enum):
    """ML optimization modes"""
    PREDICTIVE = "predictive"        # Predict bottlenecks before they occur
    ADAPTIVE = "adaptive"           # Adapt system parameters in real-time
    CONTINUOUS = "continuous"       # Continuous learning and improvement
    REACTIVE = "reactive"           # React to current conditions

class MetricType(Enum):
    """Types of performance metrics"""
    SYSTEM = "system"              # CPU, RAM, GPU, Disk
    LATENCY = "latency"            # Response times
    THROUGHPUT = "throughput"      # Requests per second
    ERROR = "error"                # Error rates
    CUSTOM = "custom"              # Custom application metrics

@dataclass
class PerformanceMetric:
    """Single performance metric data point"""
    timestamp: datetime
    metric_type: MetricType
    name: str
    value: float
    unit: str
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SystemState:
    """Complete system state snapshot"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    gpu_utilization: float
    gpu_memory_percent: float
    disk_usage_percent: float
    network_io: Dict[str, float]
    active_models: List[str]
    request_rate: float
    error_rate: float
    avg_latency: float

@dataclass
class MLOptimizationConfig:
    """Configuration for ML optimization system"""
    enabled: bool = True
    optimization_mode: OptimizationMode = OptimizationMode.ADAPTIVE
    prediction_horizon_minutes: int = 30
    retraining_interval_hours: int = 6
    anomaly_detection_threshold: float = 0.1
    model_accuracy_target: float = 0.85
    max_memory_usage_mb: int = 2048
    enable_continuous_learning: bool = True
    enable_real_time_adaptation: bool = True
    enable_predictive_scaling: bool = True
    enable_anomaly_detection: bool = True
    enable_resource_optimization: bool = True

class NeuralPerformancePredictor(nn.Module):
    """Neural network for performance prediction"""
    def __init__(self, input_size: int, hidden_sizes: List[int] = None):
        super().__init__()
        if hidden_sizes is None:
            hidden_sizes = [128, 64, 32]

        layers = []
        prev_size = input_size

        for hidden_size in hidden_sizes:
            layers.extend([
                nn.Linear(prev_size, hidden_size),
                nn.ReLU(),
                nn.Dropout(0.2)
            ])
            prev_size = hidden_size

        layers.append(nn.Linear(prev_size, 1))  # Single output for prediction

        self.network = nn.Sequential(*layers)

    def forward(self, x):
        return self.network(x)

class PerformanceDataset(Dataset):
    """Dataset for training performance models"""
    def __init__(self, features: np.ndarray, targets: np.ndarray):
        self.features = torch.FloatTensor(features)
        self.targets = torch.FloatTensor(targets)

    def __len__(self):
        return len(self.features)

    def __getitem__(self, idx):
        return self.features[idx], self.targets[idx]

class MLOptimizationEngine:
    """Main ML optimization engine for DuckBot v4.2"""

    def __init__(self, config: MLOptimizationConfig = None):
        self.config = config or MLOptimizationConfig()

        # Initialize hardware detection
        self.hardware_detector = HardwareDetector() if HardwareDetector else None
        self.hardware_info = {}
        self.performance_tier = "unknown"

        # ML Models storage
        self.models = {
            'cpu_predictor': None,
            'memory_predictor': None,
            'latency_predictor': None,
            'anomaly_detector': None,
            'resource_optimizer': None,
            'load_balancer': None,
            'model_selector': None
        }

        # Data storage
        self.metrics_history = deque(maxlen=10000)
        self.system_states = deque(maxlen=5000)
        self.optimization_decisions = deque(maxlen=1000)

        # Performance tracking
        self.optimization_stats = {
            'predictions_made': 0,
            'optimizations_applied': 0,
            'anomalies_detected': 0,
            'accuracy_score': 0.0,
            'last_retrain': None,
            'total_savings_seconds': 0
        }

        # Database for persistent storage
        self.db_path = os.path.join(os.getcwd(), 'ml_optimization.db')
        self._init_database()

        # Background tasks
        self.running = False
        self.background_thread = None

        # Initialize ML components if available
        self._init_ml_components()

        # Start optimization engine
        if self.config.enabled:
            self.start()

    def _init_database(self):
        """Initialize SQLite database for persistent storage"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Create tables
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    metric_type TEXT NOT NULL,
                    name TEXT NOT NULL,
                    value REAL NOT NULL,
                    unit TEXT,
                    metadata TEXT
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_states (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    cpu_percent REAL,
                    memory_percent REAL,
                    gpu_utilization REAL,
                    gpu_memory_percent REAL,
                    disk_usage_percent REAL,
                    network_io TEXT,
                    active_models TEXT,
                    request_rate REAL,
                    error_rate REAL,
                    avg_latency REAL
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS predictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    model_type TEXT NOT NULL,
                    prediction TEXT NOT NULL,
                    confidence REAL,
                    actual_outcome TEXT,
                    accuracy REAL
                )
            ''')

            conn.commit()
            conn.close()
            logger.info("ML optimization database initialized")

        except Exception as e:
            logger.error(f"Database initialization failed: {e}")

    def _init_ml_components(self):
        """Initialize machine learning components"""
        if not SKLEARN_AVAILABLE:
            logger.warning("scikit-learn not available - ML optimization disabled")
            return

        # Initialize scalers
        self.feature_scaler = StandardScaler()
        self.target_scaler = StandardScaler()

        # Initialize base models
        self.models['cpu_predictor'] = RandomForestRegressor(n_estimators=100, random_state=42)
        self.models['memory_predictor'] = RandomForestRegressor(n_estimators=100, random_state=42)
        self.models['latency_predictor'] = RandomForestRegressor(n_estimators=100, random_state=42)
        self.models['anomaly_detector'] = IsolationForest(contamination=0.1, random_state=42)
        self.models['resource_optimizer'] = RandomForestRegressor(n_estimators=50, random_state=42)

        # Initialize neural networks if PyTorch available
        if TORCH_AVAILABLE:
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            logger.info(f"ML optimization using device: {self.device}")
        else:
            self.device = torch.device('cpu')

        # Load existing models if available
        self._load_models()

    def detect_hardware(self):
        """Detect system hardware and capabilities"""
        if not self.hardware_detector:
            logger.warning("Hardware detector not available")
            return

        try:
            config = self.hardware_detector.detect_all_hardware()
            self.hardware_info = config["hardware_info"]
            self.performance_tier = config["performance_tier"]

            # Update ML configuration based on hardware
            self._adjust_config_for_hardware()

            logger.info(f"Hardware detected: {self.performance_tier} tier")

        except Exception as e:
            logger.error(f"Hardware detection failed: {e}")

    def _adjust_config_for_hardware(self):
        """Adjust ML optimization configuration based on hardware"""
        gpu_info = self.hardware_info.get("gpu", {})
        memory_info = self.hardware_info.get("memory", {})

        total_vram = gpu_info.get("total_vram_gb", 0)
        total_ram = memory_info.get("total_gb", 0)

        # Adjust model complexity based on hardware
        if self.performance_tier in ["enterprise", "enthusiast"]:
            self.config.max_memory_usage_mb = 4096
            self.config.enable_continuous_learning = True
            self.config.enable_real_time_adaptation = True
        elif self.performance_tier in ["high_end", "mid_range"]:
            self.config.max_memory_usage_mb = 2048
            self.config.enable_continuous_learning = True
            self.config.enable_real_time_adaptation = True
        else:
            self.config.max_memory_usage_mb = 1024
            self.config.enable_continuous_learning = False
            self.config.enable_real_time_adaptation = False

    def collect_metrics(self, metrics: List[PerformanceMetric]):
        """Collect performance metrics for ML analysis"""
        for metric in metrics:
            self.metrics_history.append(metric)
            self._store_metric(metric)

    def collect_system_state(self, state: SystemState):
        """Collect system state snapshot"""
        self.system_states.append(state)
        self._store_system_state(state)

    def _store_metric(self, metric: PerformanceMetric):
        """Store metric in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO metrics (timestamp, metric_type, name, value, unit, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                metric.timestamp.isoformat(),
                metric.metric_type.value,
                metric.name,
                metric.value,
                metric.unit,
                json.dumps(metric.metadata)
            ))

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Failed to store metric: {e}")

    def _store_system_state(self, state: SystemState):
        """Store system state in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO system_states (
                    timestamp, cpu_percent, memory_percent, gpu_utilization,
                    gpu_memory_percent, disk_usage_percent, network_io,
                    active_models, request_rate, error_rate, avg_latency
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                state.timestamp.isoformat(),
                state.cpu_percent,
                state.memory_percent,
                state.gpu_utilization,
                state.gpu_memory_percent,
                state.disk_usage_percent,
                json.dumps(state.network_io),
                json.dumps(state.active_models),
                state.request_rate,
                state.error_rate,
                state.avg_latency
            ))

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Failed to store system state: {e}")

    def predict_performance_bottlenecks(self, horizon_minutes: int = None) -> Dict[str, Any]:
        """Predict potential performance bottlenecks"""
        if not SKLEARN_AVAILABLE:
            return {"error": "ML not available"}

        horizon = horizon_minutes or self.config.prediction_horizon_minutes

        try:
            # Prepare features from recent system states
            features = self._prepare_prediction_features()

            if len(features) < 10:
                return {"error": "Insufficient data for prediction"}

            # Make predictions
            predictions = {}

            for metric_name, model in [('cpu', self.models['cpu_predictor']),
                                       ('memory', self.models['memory_predictor']),
                                       ('latency', self.models['latency_predictor'])]:

                if model and hasattr(model, 'predict'):
                    try:
                        # Predict future values
                        future_features = self._project_features(features, horizon_minutes)
                        scaled_features = self.feature_scaler.transform(future_features)
                        prediction = model.predict(scaled_features)

                        # Inverse transform to get actual values
                        if hasattr(self, f'{metric_name}_scaler'):
                            scaler = getattr(self, f'{metric_name}_scaler')
                            prediction = scaler.inverse_transform(prediction.reshape(-1, 1)).flatten()

                        predictions[metric_name] = {
                            'current': float(features[-1][0]) if len(features) > 0 else 0,
                            'predicted': float(prediction[-1]) if len(prediction) > 0 else 0,
                            'trend': 'increasing' if prediction[-1] > features[-1][0] else 'decreasing',
                            'confidence': self._calculate_prediction_confidence(model, features)
                        }

                    except Exception as e:
                        logger.error(f"Prediction failed for {metric_name}: {e}")

            # Detect anomalies
            anomalies = self._detect_anomalies(features)

            # Generate optimization recommendations
            recommendations = self._generate_optimization_recommendations(predictions, anomalies)

            self.optimization_stats['predictions_made'] += 1

            return {
                'timestamp': datetime.now().isoformat(),
                'horizon_minutes': horizon,
                'predictions': predictions,
                'anomalies': anomalies,
                'recommendations': recommendations,
                'confidence': self._calculate_overall_confidence(predictions)
            }

        except Exception as e:
            logger.error(f"Performance prediction failed: {e}")
            return {"error": str(e)}

    def _prepare_prediction_features(self) -> np.ndarray:
        """Prepare features for ML prediction"""
        if len(self.system_states) < 10:
            return np.array([])

        # Extract features from recent system states
        features_list = []

        for state in list(self.system_states)[-100:]:  # Last 100 states
            feature_vector = [
                state.cpu_percent,
                state.memory_percent,
                state.gpu_utilization,
                state.gpu_memory_percent,
                state.disk_usage_percent,
                state.request_rate,
                state.error_rate,
                state.avg_latency,
                len(state.active_models),
                # Time-based features
                state.timestamp.hour,
                state.timestamp.weekday(),
                # Network features
                state.network_io.get('bytes_sent', 0) / 1024 / 1024,  # MB
                state.network_io.get('bytes_recv', 0) / 1024 / 1024,  # MB
            ]
            features_list.append(feature_vector)

        return np.array(features_list)

    def _project_features(self, current_features: np.ndarray, horizon_minutes: int) -> np.ndarray:
        """Project features into the future for prediction"""
        # Simple linear projection for now - could be improved with time series models
        if len(current_features) < 2:
            return current_features

        # Calculate trends
        trends = np.diff(current_features, axis=0)
        avg_trend = np.mean(trends, axis=0)

        # Project forward
        steps_ahead = max(1, horizon_minutes // 5)  # Assuming 5-minute intervals
        last_features = current_features[-1]
        projected = last_features + avg_trend * steps_ahead

        # Ensure realistic bounds
        projected = np.clip(projected, 0, 100)  # Percentages can't exceed 100%

        # Reshape for single prediction
        return projected.reshape(1, -1)

    def _detect_anomalies(self, features: np.ndarray) -> List[Dict[str, Any]]:
        """Detect anomalies in system behavior"""
        if not self.config.enable_anomaly_detection or len(features) < 10:
            return []

        try:
            anomaly_detector = self.models['anomaly_detector']
            if not anomaly_detector:
                return []

            # Fit detector if not already trained
            if not hasattr(anomaly_detector, 'estimators_'):
                anomaly_detector.fit(features)

            # Detect anomalies
            anomaly_scores = anomaly_detector.decision_function(features)
            predictions = anomaly_detector.predict(features)

            anomalies = []
            for i, (score, prediction) in enumerate(zip(anomaly_scores, predictions)):
                if prediction == -1:  # Anomaly detected
                    anomalies.append({
                        'timestamp': datetime.now() - timedelta(minutes=len(features)-i),
                        'score': float(score),
                        'severity': 'high' if score < -0.5 else 'medium',
                        'features_affected': self._identify_affected_features(features[i])
                    })

            self.optimization_stats['anomalies_detected'] += len(anomalies)

            return anomalies

        except Exception as e:
            logger.error(f"Anomaly detection failed: {e}")
            return []

    def _identify_affected_features(self, anomaly_features: np.ndarray) -> List[str]:
        """Identify which features contributed to the anomaly"""
        feature_names = [
            'cpu_percent', 'memory_percent', 'gpu_utilization', 'gpu_memory_percent',
            'disk_usage_percent', 'request_rate', 'error_rate', 'avg_latency',
            'active_models_count', 'hour', 'weekday', 'network_sent_mb', 'network_recv_mb'
        ]

        affected = []
        for i, value in enumerate(anomaly_features):
            if i < len(feature_names):
                feature_name = feature_names[i]
                if value > 90 or value < 10:  # Extreme values
                    affected.append(feature_name)

        return affected

    def _generate_optimization_recommendations(self, predictions: Dict, anomalies: List) -> List[Dict]:
        """Generate optimization recommendations based on predictions and anomalies"""
        recommendations = []

        # CPU-based recommendations
        if 'cpu' in predictions:
            cpu_pred = predictions['cpu']
            if cpu_pred['predicted'] > 80:
                recommendations.append({
                    'type': 'cpu_optimization',
                    'priority': 'high',
                    'action': 'reduce_cpu_load',
                    'description': f"CPU predicted to reach {cpu_pred['predicted']:.1f}% - consider load balancing",
                    'estimated_impact': 'reduce cpu usage by 15-25%'
                })

        # Memory-based recommendations
        if 'memory' in predictions:
            mem_pred = predictions['memory']
            if mem_pred['predicted'] > 85:
                recommendations.append({
                    'type': 'memory_optimization',
                    'priority': 'high',
                    'action': 'optimize_memory_usage',
                    'description': f"Memory predicted to reach {mem_pred['predicted']:.1f}% - consider model unloading",
                    'estimated_impact': 'free up 1-2GB memory'
                })

        # Latency-based recommendations
        if 'latency' in predictions:
            lat_pred = predictions['latency']
            if lat_pred['predicted'] > 1000:  # 1 second
                recommendations.append({
                    'type': 'latency_optimization',
                    'priority': 'medium',
                    'action': 'reduce_latency',
                    'description': f"Latency predicted to reach {lat_pred['predicted']:.0f}ms - consider caching strategies",
                    'estimated_impact': 'reduce latency by 30-50%'
                })

        # Anomaly-based recommendations
        for anomaly in anomalies:
            recommendations.append({
                'type': 'anomaly_resolution',
                'priority': anomaly['severity'],
                'action': 'investigate_anomaly',
                'description': f"Anomaly detected with score {anomaly['score']:.2f} - investigate affected features",
                'affected_features': anomaly['features_affected']
            })

        return recommendations

    def _calculate_prediction_confidence(self, model, features: np.ndarray) -> float:
        """Calculate confidence score for prediction"""
        try:
            if hasattr(model, 'predict_proba'):
                # Use model's probability estimates if available
                probas = model.predict_proba(features)
                return float(np.max(probas))
            elif hasattr(model, 'score'):
                # Use model's score as confidence
                score = model.score(features, np.zeros(len(features)))  # Dummy targets
                return max(0.0, min(1.0, float(score)))
            else:
                # Use feature variance as confidence proxy
                variance = np.var(features, axis=0)
                return float(1.0 / (1.0 + np.mean(variance)))
        except:
            return 0.5  # Default confidence

    def _calculate_overall_confidence(self, predictions: Dict) -> float:
        """Calculate overall confidence across all predictions"""
        if not predictions:
            return 0.0

        confidences = [pred.get('confidence', 0.5) for pred in predictions.values()]
        return float(np.mean(confidences))

    def apply_optimization(self, recommendation: Dict[str, Any]) -> bool:
        """Apply an optimization recommendation"""
        try:
            action = recommendation.get('action')
            priority = recommendation.get('priority', 'medium')

            logger.info(f"Applying optimization: {action} (priority: {priority})")

            # Implement optimization logic based on action type
            success = False

            if action == 'reduce_cpu_load':
                success = self._optimize_cpu_usage()
            elif action == 'optimize_memory_usage':
                success = self._optimize_memory_usage()
            elif action == 'reduce_latency':
                success = self._optimize_latency()
            elif action == 'investigate_anomaly':
                success = self._handle_anomaly(recommendation)
            else:
                logger.warning(f"Unknown optimization action: {action}")
                return False

            if success:
                self.optimization_stats['optimizations_applied'] += 1
                self.optimization_decisions.append({
                    'timestamp': datetime.now(),
                    'action': action,
                    'priority': priority,
                    'success': True
                })

            return success

        except Exception as e:
            logger.error(f"Optimization application failed: {e}")
            return False

    def _optimize_cpu_usage(self) -> bool:
        """Optimize CPU usage through various strategies"""
        # Implementation would depend on available system components
        logger.info("Optimizing CPU usage")

        # Strategies could include:
        # 1. Reduce model precision
        # 2. Implement request batching
        # 3. Load balancing between models
        # 4. Reduce concurrent operations

        return True

    def _optimize_memory_usage(self) -> bool:
        """Optimize memory usage"""
        logger.info("Optimizing memory usage")

        # Strategies could include:
        # 1. Unload unused models
        # 2. Implement memory caching
        # 3. Reduce model sizes
        # 4. Clear unused resources

        return True

    def _optimize_latency(self) -> bool:
        """Optimize response latency"""
        logger.info("Optimizing latency")

        # Strategies could include:
        # 1. Implement result caching
        # 2. Optimize model loading
        # 3. Reduce network overhead
        # 4. Implement request queuing

        return True

    def _handle_anomaly(self, recommendation: Dict) -> bool:
        """Handle detected anomaly"""
        logger.info(f"Handling anomaly: {recommendation}")

        # Strategies could include:
        # 1. System diagnostics
        # 2. Roll back recent changes
        # 3. Restart affected services
        # 4. Alert administrators

        return True

    def retrain_models(self) -> bool:
        """Retrain ML models with recent data"""
        if not SKLEARN_AVAILABLE:
            return False

        try:
            logger.info("Retraining ML models")

            # Prepare training data
            features = self._prepare_training_features()
            targets = self._prepare_training_targets()

            if len(features) < 50:
                logger.warning("Insufficient data for retraining")
                return False

            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                features, targets, test_size=0.2, random_state=42
            )

            # Retrain each model
            retrained_count = 0

            for model_name, model in self.models.items():
                if model and hasattr(model, 'fit'):
                    try:
                        # Prepare specific targets for each model
                        if model_name == 'cpu_predictor':
                            y_model = y_train[:, 0]  # CPU targets
                        elif model_name == 'memory_predictor':
                            y_model = y_train[:, 1]  # Memory targets
                        elif model_name == 'latency_predictor':
                            y_model = y_train[:, 2]  # Latency targets
                        else:
                            continue

                        # Retrain model
                        model.fit(X_train, y_model)

                        # Evaluate performance
                        if model_name in ['cpu_predictor', 'memory_predictor', 'latency_predictor']:
                            y_test_model = y_test[:, 0] if model_name == 'cpu_predictor' else \
                                           y_test[:, 1] if model_name == 'memory_predictor' else \
                                           y_test[:, 2]

                            score = model.score(X_test, y_test_model)
                            logger.info(f"Model {model_name} retrained with score: {score:.3f}")

                            if score > self.config.model_accuracy_target:
                                retrained_count += 1

                    except Exception as e:
                        logger.error(f"Failed to retrain {model_name}: {e}")

            # Save retrained models
            self._save_models()

            # Update statistics
            self.optimization_stats['last_retrain'] = datetime.now()

            logger.info(f"Retrained {retrained_count} models successfully")
            return retrained_count > 0

        except Exception as e:
            logger.error(f"Model retraining failed: {e}")
            return False

    def _prepare_training_features(self) -> np.ndarray:
        """Prepare features for model training"""
        features_list = []

        for state in self.system_states:
            feature_vector = [
                state.cpu_percent,
                state.memory_percent,
                state.gpu_utilization,
                state.gpu_memory_percent,
                state.disk_usage_percent,
                state.request_rate,
                state.error_rate,
                state.avg_latency,
                len(state.active_models),
                state.timestamp.hour,
                state.timestamp.weekday(),
                state.network_io.get('bytes_sent', 0) / 1024 / 1024,
                state.network_io.get('bytes_recv', 0) / 1024 / 1024,
            ]
            features_list.append(feature_vector)

        return np.array(features_list)

    def _prepare_training_targets(self) -> np.ndarray:
        """Prepare targets for model training"""
        targets_list = []

        for i, state in enumerate(self.system_states):
            # Use next state as target (predicting future values)
            if i < len(self.system_states) - 1:
                next_state = self.system_states[i + 1]
                target_vector = [
                    next_state.cpu_percent,
                    next_state.memory_percent,
                    next_state.avg_latency
                ]
                targets_list.append(target_vector)

        return np.array(targets_list)

    def _save_models(self):
        """Save trained models to disk"""
        try:
            model_dir = os.path.join(os.getcwd(), 'ml_models')
            os.makedirs(model_dir, exist_ok=True)

            for model_name, model in self.models.items():
                if model and SKLEARN_AVAILABLE:
                    model_path = os.path.join(model_dir, f'{model_name}.pkl')
                    joblib.dump(model, model_path)

            # Save scalers
            scaler_path = os.path.join(model_dir, 'scalers.pkl')
            joblib.dump({
                'feature_scaler': self.feature_scaler,
                'target_scaler': self.target_scaler
            }, scaler_path)

            logger.info("ML models saved successfully")

        except Exception as e:
            logger.error(f"Failed to save models: {e}")

    def _load_models(self):
        """Load trained models from disk"""
        try:
            model_dir = os.path.join(os.getcwd(), 'ml_models')

            if not os.path.exists(model_dir):
                return

            for model_name in self.models.keys():
                model_path = os.path.join(model_dir, f'{model_name}.pkl')
                if os.path.exists(model_path):
                    try:
                        self.models[model_name] = joblib.load(model_path)
                        logger.info(f"Loaded model: {model_name}")
                    except Exception as e:
                        logger.error(f"Failed to load {model_name}: {e}")

            # Load scalers
            scaler_path = os.path.join(model_dir, 'scalers.pkl')
            if os.path.exists(scaler_path):
                try:
                    scalers = joblib.load(scaler_path)
                    self.feature_scaler = scalers.get('feature_scaler', self.feature_scaler)
                    self.target_scaler = scalers.get('target_scaler', self.target_scaler)
                except Exception as e:
                    logger.error(f"Failed to load scalers: {e}")

        except Exception as e:
            logger.error(f"Failed to load models: {e}")

    def start(self):
        """Start the ML optimization engine"""
        if self.running:
            return

        self.running = True
        self.background_thread = threading.Thread(target=self._background_loop, daemon=True)
        self.background_thread.start()

        logger.info("ML optimization engine started")

    def stop(self):
        """Stop the ML optimization engine"""
        self.running = False
        if self.background_thread:
            self.background_thread.join(timeout=5)

        # Save models before stopping
        self._save_models()

        logger.info("ML optimization engine stopped")

    def _background_loop(self):
        """Background loop for continuous optimization"""
        while self.running:
            try:
                # Collect current system state
                current_state = self._get_current_system_state()
                if current_state:
                    self.collect_system_state(current_state)

                # Perform predictions
                if self.config.optimization_mode == OptimizationMode.PREDICTIVE:
                    predictions = self.predict_performance_bottlenecks()
                    if predictions and 'recommendations' in predictions:
                        for rec in predictions['recommendations']:
                            if rec.get('priority') == 'high':
                                self.apply_optimization(rec)

                # Retrain models periodically
                if self.config.enable_continuous_learning:
                    last_retrain = self.optimization_stats.get('last_retrain')
                    if (last_retrain is None or
                        datetime.now() - last_retrain > timedelta(hours=self.config.retraining_interval_hours)):
                        self.retrain_models()

                # Sleep for next iteration
                time.sleep(300)  # 5 minutes

            except Exception as e:
                logger.error(f"Background loop error: {e}")
                time.sleep(60)  # Wait before retrying

    def _get_current_system_state(self) -> Optional[SystemState]:
        """Get current system state"""
        try:
            import psutil

            # Get basic system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            # Network I/O
            network = psutil.net_io_counters()
            network_io = {
                'bytes_sent': network.bytes_sent,
                'bytes_recv': network.bytes_recv,
                'packets_sent': network.packets_sent,
                'packets_recv': network.packets_recv
            }

            # GPU metrics (if available)
            gpu_utilization = 0.0
            gpu_memory_percent = 0.0

            try:
                if self.hardware_info and self.hardware_info.get('gpu', {}).get('nvidia'):
                    result = subprocess.run(['nvidia-smi', '--query-gpu=utilization.gpu,memory.used,memory.total',
                                           '--format=csv,noheader,nounits'],
                                          capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        lines = result.stdout.strip().split('\n')
                        if lines:
                            gpu_util, mem_used, mem_total = map(float, lines[0].split(', '))
                            gpu_utilization = gpu_util
                            gpu_memory_percent = (mem_used / mem_total) * 100
            except:
                pass

            return SystemState(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                gpu_utilization=gpu_utilization,
                gpu_memory_percent=gpu_memory_percent,
                disk_usage_percent=disk.percent,
                network_io=network_io,
                active_models=[],  # Would be populated by model manager
                request_rate=0.0,   # Would be populated by request tracker
                error_rate=0.0,     # Would be populated by error tracker
                avg_latency=0.0     # Would be populated by latency tracker
            )

        except Exception as e:
            logger.error(f"Failed to get system state: {e}")
            return None

    def get_optimization_status(self) -> Dict[str, Any]:
        """Get current status of ML optimization"""
        return {
            'running': self.running,
            'performance_tier': self.performance_tier,
            'config': {
                'enabled': self.config.enabled,
                'optimization_mode': self.config.optimization_mode.value,
                'prediction_horizon_minutes': self.config.prediction_horizon_minutes,
                'anomaly_detection_enabled': self.config.enable_anomaly_detection,
                'continuous_learning_enabled': self.config.enable_continuous_learning
            },
            'statistics': self.optimization_stats,
            'data_points': {
                'metrics_collected': len(self.metrics_history),
                'system_states': len(self.system_states),
                'optimization_decisions': len(self.optimization_decisions)
            },
            'models': {
                name: {'loaded': model is not None}
                for name, model in self.models.items()
            }
        }

    def export_optimization_data(self, filepath: str) -> bool:
        """Export optimization data for analysis"""
        try:
            data = {
                'metrics_history': [
                    {
                        'timestamp': m.timestamp.isoformat(),
                        'metric_type': m.metric_type.value,
                        'name': m.name,
                        'value': m.value,
                        'unit': m.unit,
                        'metadata': m.metadata
                    } for m in self.metrics_history
                ],
                'system_states': [
                    {
                        'timestamp': s.timestamp.isoformat(),
                        'cpu_percent': s.cpu_percent,
                        'memory_percent': s.memory_percent,
                        'gpu_utilization': s.gpu_utilization,
                        'gpu_memory_percent': s.gpu_memory_percent,
                        'disk_usage_percent': s.disk_usage_percent,
                        'network_io': s.network_io,
                        'active_models': s.active_models,
                        'request_rate': s.request_rate,
                        'error_rate': s.error_rate,
                        'avg_latency': s.avg_latency
                    } for s in self.system_states
                ],
                'optimization_decisions': [
                    {
                        'timestamp': d['timestamp'].isoformat() if isinstance(d['timestamp'], datetime) else d['timestamp'],
                        'action': d['action'],
                        'priority': d['priority'],
                        'success': d['success']
                    } for d in self.optimization_decisions
                ],
                'statistics': self.optimization_stats,
                'export_timestamp': datetime.now().isoformat()
            }

            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)

            logger.info(f"Optimization data exported to: {filepath}")
            return True

        except Exception as e:
            logger.error(f"Failed to export optimization data: {e}")
            return False

def main():
    """Main function for testing the ML optimization engine"""
    print("[EMOJI] DuckBot ML Optimization Engine")
    print("=" * 50)

    # Initialize optimization engine
    config = MLOptimizationConfig(
        enabled=True,
        optimization_mode=OptimizationMode.ADAPTIVE,
        prediction_horizon_minutes=15,
        enable_continuous_learning=True
    )

    engine = MLOptimizationEngine(config)

    # Detect hardware
    engine.detect_hardware()

    # Display status
    status = engine.get_optimization_status()
    print(f"\n[STATUS] ML Optimization Status:")
    print(f"  Running: {status['running']}")
    print(f"  Performance Tier: {status['performance_tier']}")
    print(f"  Models Loaded: {sum(1 for m in status['models'].values() if m['loaded'])}")

    # Test prediction
    print(f"\n[PREDICT] Testing performance prediction...")
    prediction = engine.predict_performance_bottlenecks(horizon_minutes=10)
    if 'error' not in prediction:
        print(f"  Predictions made: {len(prediction.get('predictions', {}))}")
        print(f"  Anomalies detected: {len(prediction.get('anomalies', []))}")
        print(f"  Recommendations: {len(prediction.get('recommendations', []))}")
    else:
        print(f"  Prediction failed: {prediction['error']}")

    # Keep running for demonstration
    try:
        print(f"\n[EMOJI] ML optimization engine running (Press Ctrl+C to stop)")
        while True:
            time.sleep(60)

            # Periodic status update
            if np.random.random() < 0.1:  # 10% chance every minute
                status = engine.get_optimization_status()
                print(f"[STATUS] Predictions: {status['statistics']['predictions_made']}, "
                      f"Optimizations: {status['statistics']['optimizations_applied']}")

    except KeyboardInterrupt:
        print(f"\n[EMOJI] Stopping ML optimization engine...")
        engine.stop()
        print(f"[EMOJI] Done!")

if __name__ == "__main__":
    main()