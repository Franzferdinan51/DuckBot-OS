#!/usr/bin/env python3
"""
ML-based AI Model Optimization for DuckBot v4.2
Uses machine learning to optimize model selection, loading, and caching strategies
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
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, mean_squared_error, silhouette_score
import joblib
import hashlib
import psutil
from collections import defaultdict, deque
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

@dataclass
class ModelPerformanceMetrics:
    """Performance metrics for AI models"""
    model_id: str
    response_time_ms: float
    accuracy_score: float
    success_rate: float
    cost_per_request: float
    tokens_per_second: float
    memory_usage_gb: float
    vram_usage_gb: float
    last_used: datetime
    usage_count: int

@dataclass
class ModelSelectionScore:
    """Score for model selection decision"""
    model_id: str
    overall_score: float
    performance_score: float
    cost_score: float
    resource_score: float
    task_fit_score: float
    confidence: float

@dataclass
class CacheOptimization:
    """Cache optimization recommendations"""
    cache_size_mb: int
    eviction_policy: str
    hit_rate_target: float
    models_to_cache: List[str]
    models_to_evict: List[str]
    preload_recommendations: List[str]

class AIModelOptimizer:
    """ML-based AI model optimization system"""

    def __init__(self, db_path: str = None, model_dir: str = None):
        self.db_path = db_path or str(Path(__file__).parent / "model_optimization.db")
        self.model_dir = model_dir or str(Path(__file__).parent / "ml_models")

        # Ensure directories exist
        Path(self.model_dir).mkdir(parents=True, exist_ok=True)

        # Initialize ML models
        self.model_selector = None
        self.performance_predictor = None
        self.cost_optimizer = None
        self.resource_clusterer = None
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()

        # Model performance tracking
        self.model_metrics = defaultdict(dict)
        self.usage_patterns = defaultdict(lambda: deque(maxlen=100))
        self.cache_manager = None

        # Feature engineering
        self.feature_columns = [
            'task_complexity', 'task_type_encoded', 'prompt_length_tokens',
            'expected_response_length', 'time_of_day', 'day_of_week',
            'current_ram_usage', 'current_vram_usage', 'current_cpu_usage',
            'concurrent_requests', 'model_size_gb', 'model_specialization_score',
            'provider_reliability_score', 'cost_per_1k_tokens', 'avg_response_time',
            'recent_success_rate', 'memory_efficiency_score', 'user_preference_score'
        ]

        # Performance tracking
        self.optimization_stats = {
            'total_optimizations': 0,
            'improved_selections': 0,
            'cost_savings_usd': 0.0,
            'response_time_improvement_ms': 0.0,
            'cache_hit_rate': 0.0,
            'last_model_update': None
        }

        # Threading
        self.lock = threading.RLock()
        self._init_database()
        self._load_models()

        # Start optimization loop
        self.optimization_active = True
        self.optimization_thread = threading.Thread(target=self._continuous_optimization, daemon=True)
        self.optimization_thread.start()

    def _init_database(self):
        """Initialize database for model optimization"""
        with sqlite3.connect(self.db_path) as conn:
            # Model performance tracking
            conn.execute('''
                CREATE TABLE IF NOT EXISTS model_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    model_id TEXT NOT NULL,
                    task_type TEXT NOT NULL,
                    response_time_ms REAL NOT NULL,
                    success BOOLEAN NOT NULL,
                    input_tokens INTEGER NOT NULL,
                    output_tokens INTEGER NOT NULL,
                    cost_usd REAL NOT NULL,
                    memory_usage_gb REAL NOT NULL,
                    vram_usage_gb REAL NOT NULL,
                    cpu_usage_percent REAL NOT NULL,
                    user_satisfaction_score REAL,
                    error_message TEXT
                )
            ''')

            # Model characteristics
            conn.execute('''
                CREATE TABLE IF NOT EXISTS model_characteristics (
                    model_id TEXT PRIMARY KEY,
                    provider TEXT NOT NULL,
                    size_gb REAL NOT NULL,
                    capabilities TEXT NOT NULL,
                    specialties TEXT NOT NULL,
                    cost_per_1k_input REAL NOT NULL,
                    cost_per_1k_output REAL NOT NULL,
                    avg_response_time_ms REAL NOT NULL,
                    reliability_score REAL NOT NULL,
                    max_context_length INTEGER NOT NULL,
                    last_updated DATETIME NOT NULL
                )
            ''')

            # Cache optimization
            conn.execute('''
                CREATE TABLE IF NOT EXISTS cache_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    model_id TEXT NOT NULL,
                    cache_hit BOOLEAN NOT NULL,
                    access_time_ms REAL NOT NULL,
                    memory_saved_gb REAL NOT NULL,
                    eviction_candidate BOOLEAN DEFAULT FALSE
                )
            ''')

            # Optimization decisions
            conn.execute('''
                CREATE TABLE IF NOT EXISTS optimization_decisions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    decision_type TEXT NOT NULL,
                    model_id TEXT NOT NULL,
                    old_value TEXT,
                    new_value TEXT,
                    improvement_score REAL,
                    confidence_score REAL,
                    implemented BOOLEAN DEFAULT FALSE
                )
            ''')

            # Create indexes
            conn.execute('CREATE INDEX IF NOT EXISTS idx_performance_timestamp ON model_performance(timestamp)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_performance_model ON model_performance(model_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_cache_timestamp ON cache_performance(timestamp)')

    def _load_models(self):
        """Load trained ML models or initialize new ones"""
        try:
            # Try to load existing models
            selector_path = Path(self.model_dir) / "model_selector.joblib"
            predictor_path = Path(self.model_dir) / "performance_predictor.joblib"
            cost_path = Path(self.model_dir) / "cost_optimizer.joblib"
            cluster_path = Path(self.model_dir) / "resource_clusterer.joblib"
            scaler_path = Path(self.model_dir) / "scaler.joblib"
            encoder_path = Path(self.model_dir) / "label_encoder.joblib"

            if selector_path.exists():
                self.model_selector = joblib.load(selector_path)
                self.performance_predictor = joblib.load(predictor_path)
                self.cost_optimizer = joblib.load(cost_path)
                self.resource_clusterer = joblib.load(cluster_path)
                self.scaler = joblib.load(scaler_path)
                self.label_encoder = joblib.load(encoder_path)
                logger.info("Loaded existing ML optimization models")
            else:
                self._initialize_models()
                logger.info("Initialized new ML optimization models")
        except Exception as e:
            logger.error(f"Error loading optimization models: {e}")
            self._initialize_models()

    def _initialize_models(self):
        """Initialize new ML models"""
        self.model_selector = RandomForestClassifier(
            n_estimators=100,
            max_depth=15,
            random_state=42,
            n_jobs=-1
        )
        self.performance_predictor = GradientBoostingRegressor(
            n_estimators=100,
            max_depth=8,
            random_state=42
        )
        self.cost_optimizer = GradientBoostingRegressor(
            n_estimators=50,
            max_depth=6,
            random_state=42
        )
        self.resource_clusterer = KMeans(
            n_clusters=5,
            random_state=42,
            n_init=10
        )

    def record_model_performance(self, model_id: str, task_type: str,
                              response_time_ms: float, success: bool,
                              input_tokens: int, output_tokens: int,
                              cost_usd: float, memory_usage_gb: float,
                              vram_usage_gb: float, cpu_usage_percent: float,
                              user_satisfaction_score: float = None,
                              error_message: str = None):
        """Record model performance for training and optimization"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO model_performance
                (timestamp, model_id, task_type, response_time_ms, success,
                 input_tokens, output_tokens, cost_usd, memory_usage_gb,
                 vram_usage_gb, cpu_usage_percent, user_satisfaction_score, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now(), model_id, task_type, response_time_ms, success,
                input_tokens, output_tokens, cost_usd, memory_usage_gb,
                vram_usage_gb, cpu_usage_percent, user_satisfaction_score, error_message
            ))

        # Update in-memory metrics
        self._update_model_metrics(model_id, {
            'response_time_ms': response_time_ms,
            'success': success,
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'cost_usd': cost_usd,
            'memory_usage_gb': memory_usage_gb,
            'vram_usage_gb': vram_usage_gb,
            'cpu_usage_percent': cpu_usage_percent,
            'timestamp': datetime.now()
        })

    def _update_model_metrics(self, model_id: str, performance_data: Dict[str, Any]):
        """Update in-memory model metrics"""
        if model_id not in self.model_metrics:
            self.model_metrics[model_id] = {
                'total_requests': 0,
                'successful_requests': 0,
                'total_response_time': 0.0,
                'total_cost': 0.0,
                'total_tokens': 0,
                'max_memory_usage': 0.0,
                'max_vram_usage': 0.0,
                'last_used': None
            }

        metrics = self.model_metrics[model_id]
        metrics['total_requests'] += 1
        metrics['total_response_time'] += performance_data['response_time_ms']
        metrics['total_cost'] += performance_data['cost_usd']
        metrics['total_tokens'] += performance_data['input_tokens'] + performance_data['output_tokens']
        metrics['max_memory_usage'] = max(metrics['max_memory_usage'], performance_data['memory_usage_gb'])
        metrics['max_vram_usage'] = max(metrics['max_vram_usage'], performance_data['vram_usage_gb'])
        metrics['last_used'] = performance_data['timestamp']

        if performance_data['success']:
            metrics['successful_requests'] += 1

    def get_performance_data(self, hours: int = 168) -> pd.DataFrame:
        """Get performance data for training ML models"""
        start_time = datetime.now() - timedelta(hours=hours)

        with sqlite3.connect(self.db_path) as conn:
            df = pd.read_sql_query('''
                SELECT mp.*, mc.size_gb, mc.avg_response_time_ms,
                       mc.reliability_score, mc.cost_per_1k_input, mc.cost_per_1k_output
                FROM model_performance mp
                LEFT JOIN model_characteristics mc ON mp.model_id = mc.model_id
                WHERE mp.timestamp >= ?
                ORDER BY mp.timestamp
            ''', conn, params=(start_time,))

        if df.empty:
            return df

        # Feature engineering
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['hour_of_day'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        df['total_tokens'] = df['input_tokens'] + df['output_tokens']
        df['tokens_per_second'] = df['total_tokens'] / (df['response_time_ms'] / 1000.0)
        df['cost_efficiency'] = df['total_tokens'] / df['cost_usd']
        df['memory_efficiency'] = df['total_tokens'] / df['memory_usage_gb']
        df['success_rate'] = df['success'].astype(int)

        return df

    def train_optimization_models(self, retrain: bool = False):
        """Train ML optimization models"""
        with self.lock:
            df = self.get_performance_data(hours=336)  # 14 days

            if len(df) < 50:  # Need minimum data
                logger.warning("Insufficient data for training optimization models")
                return False

            # Prepare features for model selection
            X_selection = self._prepare_selection_features(df)
            y_selection = df['model_id']

            # Prepare features for performance prediction
            X_performance = self._prepare_performance_features(df)
            y_performance = df['response_time_ms']

            # Prepare features for cost optimization
            X_cost = self._prepare_cost_features(df)
            y_cost = df['cost_usd']

            # Train models
            if len(X_selection) > 10:
                X_sel_scaled = self.scaler.fit_transform(X_selection)
                self.model_selector.fit(X_sel_scaled, y_selection)

                X_perf_scaled = self.scaler.transform(X_performance)
                self.performance_predictor.fit(X_perf_scaled, y_performance)

                X_cost_scaled = self.scaler.transform(X_cost)
                self.cost_optimizer.fit(X_cost_scaled, y_cost)

                # Resource clustering
                resource_features = df[['memory_usage_gb', 'vram_usage_gb', 'cpu_usage_percent', 'response_time_ms']]
                self.resource_clusterer.fit(resource_features)

                # Save models
                self._save_models()

                # Update training stats
                self.optimization_stats['last_model_update'] = datetime.now()

                logger.info("Optimization models trained successfully")
                return True

            return False

    def _prepare_selection_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare features for model selection"""
        features = pd.DataFrame()

        # Task features
        features['prompt_length_tokens'] = df['input_tokens']
        features['expected_response_length'] = df['output_tokens']
        features['task_type_encoded'] = self.label_encoder.fit_transform(df['task_type'])

        # Time features
        features['time_of_day'] = df['hour_of_day']
        features['day_of_week'] = df['day_of_week']

        # Resource features
        features['current_ram_usage'] = df['memory_usage_gb']
        features['current_vram_usage'] = df['vram_usage_gb']
        features['current_cpu_usage'] = df['cpu_usage_percent']

        # Model features (simplified)
        features['model_size_gb'] = df['size_gb'].fillna(0)
        features['cost_per_1k_tokens'] = (df['cost_per_1k_input'] + df['cost_per_1k_output']).fillna(0.001)
        features['avg_response_time'] = df['avg_response_time_ms'].fillna(1000)

        # Performance features
        features['recent_success_rate'] = df['success_rate'].rolling(window=10, min_periods=1).mean()
        features['task_complexity'] = df['input_tokens'] * df['output_tokens'] / 1000000.0

        return features.fillna(0)

    def _prepare_performance_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare features for performance prediction"""
        features = self._prepare_selection_features(df.copy())

        # Additional performance-specific features
        features['concurrent_requests'] = df.groupby('timestamp').cumcount()
        features['model_specialization_score'] = self._calculate_specialization_score(df)

        return features.fillna(0)

    def _prepare_cost_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare features for cost optimization"""
        features = self._prepare_selection_features(df.copy())

        # Cost-specific features
        features['provider_reliability_score'] = df['reliability_score'].fillna(0.5)
        features['memory_efficiency_score'] = df['memory_efficiency'].fillna(0)
        features['user_preference_score'] = df.get('user_satisfaction_score', 0.5).fillna(0.5)

        return features.fillna(0)

    def _calculate_specialization_score(self, df: pd.DataFrame) -> pd.Series:
        """Calculate model specialization score for task types"""
        # This would integrate with model capability mapping
        # For now, return a placeholder
        return pd.Series(0.5, index=df.index)

    def _save_models(self):
        """Save trained models to disk"""
        try:
            joblib.dump(self.model_selector, Path(self.model_dir) / "model_selector.joblib")
            joblib.dump(self.performance_predictor, Path(self.model_dir) / "performance_predictor.joblib")
            joblib.dump(self.cost_optimizer, Path(self.model_dir) / "cost_optimizer.joblib")
            joblib.dump(self.resource_clusterer, Path(self.model_dir) / "resource_clusterer.joblib")
            joblib.dump(self.scaler, Path(self.model_dir) / "scaler.joblib")
            joblib.dump(self.label_encoder, Path(self.model_dir) / "label_encoder.joblib")
        except Exception as e:
            logger.error(f"Error saving optimization models: {e}")

    def select_optimal_model(self, task_type: str, prompt_tokens: int,
                           expected_response_tokens: int, context: Dict[str, Any] = None) -> ModelSelectionScore:
        """Select optimal model using ML-based scoring"""
        if not self.model_selector:
            # Fallback to simple scoring
            return self._fallback_model_selection(task_type, prompt_tokens, expected_response_tokens)

        # Prepare features
        features = self._prepare_selection_features_for_prediction(
            task_type, prompt_tokens, expected_response_tokens, context
        )

        if features.empty:
            return self._fallback_model_selection(task_type, prompt_tokens, expected_response_tokens)

        # Get model probabilities
        features_scaled = self.scaler.transform([features])
        try:
            model_probs = self.model_selector.predict_proba(features_scaled)[0]
            model_classes = self.model_selector.classes_

            # Calculate comprehensive scores
            scores = []
            for i, model_id in enumerate(model_classes):
                score = self._calculate_comprehensive_score(
                    model_id, model_probs[i], task_type, context
                )
                scores.append(score)

            # Select best model
            best_score = max(scores, key=lambda x: x.overall_score)
            return best_score

        except Exception as e:
            logger.error(f"Error in model selection: {e}")
            return self._fallback_model_selection(task_type, prompt_tokens, expected_response_tokens)

    def _prepare_selection_features_for_prediction(self, task_type: str, prompt_tokens: int,
                                                 expected_response_tokens: int, context: Dict[str, Any]) -> pd.DataFrame:
        """Prepare features for real-time model selection"""
        try:
            # Encode task type
            task_type_encoded = self.label_encoder.transform([task_type])[0]
        except ValueError:
            # Unknown task type, use default
            task_type_encoded = 0

        current_time = datetime.now()
        current_ram = psutil.virtual_memory().used / (1024**3)
        current_vram = self._get_current_vram_usage()
        current_cpu = psutil.cpu_percent()

        features = pd.DataFrame([{
            'prompt_length_tokens': prompt_tokens,
            'expected_response_length': expected_response_tokens,
            'task_type_encoded': task_type_encoded,
            'time_of_day': current_time.hour,
            'day_of_week': current_time.weekday(),
            'current_ram_usage': current_ram,
            'current_vram_usage': current_vram,
            'current_cpu_usage': current_cpu,
            'model_size_gb': 0,  # Will be filled during scoring
            'cost_per_1k_tokens': 0.001,  # Default
            'avg_response_time': 1000,  # Default 1 second
            'recent_success_rate': 0.9,  # Default
            'task_complexity': prompt_tokens * expected_response_tokens / 1000000.0
        }])

        return features

    def _get_current_vram_usage(self) -> float:
        """Get current VRAM usage"""
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            if gpus:
                return sum(gpu.memoryUsed for gpu in gpus) / 1024.0
        except ImportError:
            pass
        return 0.0

    def _calculate_comprehensive_score(self, model_id: str, probability: float,
                                    task_type: str, context: Dict[str, Any]) -> ModelSelectionScore:
        """Calculate comprehensive model selection score"""
        # Get model characteristics
        model_metrics = self.model_metrics.get(model_id, {})
        total_requests = model_metrics.get('total_requests', 0)

        if total_requests == 0:
            # New model, use default scores
            return ModelSelectionScore(
                model_id=model_id,
                overall_score=probability * 0.5,
                performance_score=0.5,
                cost_score=0.5,
                resource_score=0.5,
                task_fit_score=probability,
                confidence=0.3
            )

        # Calculate individual scores
        performance_score = self._calculate_performance_score(model_id, task_type)
        cost_score = self._calculate_cost_score(model_id)
        resource_score = self._calculate_resource_score(model_id)
        task_fit_score = self._calculate_task_fit_score(model_id, task_type)

        # Weighted overall score
        overall_score = (
            performance_score * 0.3 +
            cost_score * 0.25 +
            resource_score * 0.2 +
            task_fit_score * 0.25
        )

        confidence = min(1.0, total_requests / 100.0)  # More data = higher confidence

        return ModelSelectionScore(
            model_id=model_id,
            overall_score=overall_score,
            performance_score=performance_score,
            cost_score=cost_score,
            resource_score=resource_score,
            task_fit_score=task_fit_score,
            confidence=confidence
        )

    def _calculate_performance_score(self, model_id: str, task_type: str) -> float:
        """Calculate performance score for a model"""
        metrics = self.model_metrics.get(model_id, {})
        total_requests = metrics.get('total_requests', 0)

        if total_requests == 0:
            return 0.5

        # Response time score (lower is better)
        avg_response_time = metrics['total_response_time'] / total_requests
        response_time_score = max(0, 1 - (avg_response_time / 10000.0))  # Normalize to 10s max

        # Success rate score
        success_rate = metrics['successful_requests'] / total_requests

        # Combine scores
        return (response_time_score * 0.4 + success_rate * 0.6)

    def _calculate_cost_score(self, model_id: str) -> float:
        """Calculate cost efficiency score"""
        metrics = self.model_metrics.get(model_id, {})
        total_requests = metrics.get('total_requests', 0)

        if total_requests == 0:
            return 0.5

        avg_cost = metrics['total_cost'] / total_requests
        avg_tokens = metrics['total_tokens'] / total_requests

        if avg_tokens == 0:
            return 0.0

        cost_per_token = avg_cost / avg_tokens
        # Score based on cost efficiency (lower cost per token = higher score)
        return max(0, 1 - (cost_per_token / 0.01))  # Normalize to $0.01 per token

    def _calculate_resource_score(self, model_id: str) -> float:
        """Calculate resource efficiency score"""
        metrics = self.model_metrics.get(model_id, {})
        total_requests = metrics.get('total_requests', 0)

        if total_requests == 0:
            return 0.5

        max_memory = metrics['max_memory_usage']
        max_vram = metrics['max_vram_usage']

        # Score based on resource efficiency (lower usage = higher score)
        memory_score = max(0, 1 - (max_memory / 32.0))  # Normalize to 32GB
        vram_score = max(0, 1 - (max_vram / 16.0))  # Normalize to 16GB

        return (memory_score * 0.6 + vram_score * 0.4)

    def _calculate_task_fit_score(self, model_id: str, task_type: str) -> float:
        """Calculate task fit score based on historical performance"""
        # This would analyze how well the model performs on specific task types
        # For now, use a simplified approach
        return 0.7  # Placeholder

    def _fallback_model_selection(self, task_type: str, prompt_tokens: int,
                                expected_response_tokens: int) -> ModelSelectionScore:
        """Fallback model selection when ML models aren't available"""
        # Simple heuristic-based selection
        if prompt_tokens + expected_response_tokens < 2000:
            model_id = "microsoft/phi-3-mini"  # Small model for short tasks
        elif prompt_tokens + expected_response_tokens < 8000:
            model_id = "qwen/qwen3-coder:free"  # Medium model
        else:
            model_id = "google/gemma-2-9b-it"  # Large model for complex tasks

        return ModelSelectionScore(
            model_id=model_id,
            overall_score=0.6,
            performance_score=0.6,
            cost_score=0.6,
            resource_score=0.6,
            task_fit_score=0.6,
            confidence=0.3
        )

    def optimize_cache_strategy(self, available_memory_gb: float) -> CacheOptimization:
        """Optimize model caching strategy"""
        # Get cache performance data
        with sqlite3.connect(self.db_path) as conn:
            cache_df = pd.read_sql_query('''
                SELECT model_id, cache_hit, access_time_ms, memory_saved_gb
                FROM cache_performance
                WHERE timestamp >= datetime('now', '-7 days')
            ''', conn)

        if cache_df.empty:
            return CacheOptimization(
                cache_size_mb=1024,
                eviction_policy="lru",
                hit_rate_target=0.8,
                models_to_cache=[],
                models_to_evict=[],
                preload_recommendations=[]
            )

        # Analyze cache patterns
        hit_rates = cache_df.groupby('model_id')['cache_hit'].mean()
        access_times = cache_df.groupby('model_id')['access_time_ms'].mean()
        memory_savings = cache_df.groupby('model_id')['memory_saved_gb'].sum()

        # Identify models to cache
        high_value_models = hit_rates[hit_rates > 0.7].index.tolist()
        fast_access_models = access_times[access_times < 100].index.tolist()

        models_to_cache = list(set(high_value_models + fast_access_models))

        # Identify models to evict
        low_value_models = hit_rates[hit_rates < 0.3].index.tolist()
        slow_models = access_times[access_times > 1000].index.tolist()

        models_to_evict = list(set(low_value_models + slow_models))

        # Calculate optimal cache size
        total_model_sizes = sum(self.model_metrics.get(model, {}).get('max_memory_usage', 1.0)
                              for model in models_to_cache)
        cache_size_gb = min(total_model_sizes * 1.2, available_memory_gb * 0.3)  # 30% of available memory

        # Generate preload recommendations
        preload_recommendations = []
        if models_to_cache:
            # Recommend preloading frequently accessed models
            most_accessed = hit_rates.nlargest(3).index.tolist()
            preload_recommendations = [model for model in most_accessed if model in models_to_cache]

        return CacheOptimization(
            cache_size_mb=int(cache_size_gb * 1024),
            eviction_policy="lru",  # Least Recently Used
            hit_rate_target=0.8,
            models_to_cache=models_to_cache,
            models_to_evict=models_to_evict,
            preload_recommendations=preload_recommendations
        )

    def predict_model_performance(self, model_id: str, task_type: str,
                                prompt_tokens: int, expected_response_tokens: int) -> Dict[str, float]:
        """Predict model performance for a specific task"""
        if not self.performance_predictor:
            return {
                "predicted_response_time_ms": 1000.0,
                "predicted_success_rate": 0.8,
                "predicted_cost_usd": 0.01,
                "confidence": 0.3
            }

        # Prepare features
        features = self._prepare_selection_features_for_prediction(
            task_type, prompt_tokens, expected_response_tokens, {}
        )

        if features.empty:
            return {
                "predicted_response_time_ms": 1000.0,
                "predicted_success_rate": 0.8,
                "predicted_cost_usd": 0.01,
                "confidence": 0.3
            }

        try:
            features_scaled = self.scaler.transform(features)
            predicted_response_time = self.performance_predictor.predict(features_scaled)[0]

            # Estimate other metrics based on historical data
            model_metrics = self.model_metrics.get(model_id, {})
            total_requests = model_metrics.get('total_requests', 0)

            if total_requests > 0:
                success_rate = model_metrics['successful_requests'] / total_requests
                avg_cost_per_request = model_metrics['total_cost'] / total_requests
            else:
                success_rate = 0.8
                avg_cost_per_request = 0.01

            confidence = min(1.0, total_requests / 50.0)

            return {
                "predicted_response_time_ms": max(100, predicted_response_time),
                "predicted_success_rate": success_rate,
                "predicted_cost_usd": avg_cost_per_request,
                "confidence": confidence
            }

        except Exception as e:
            logger.error(f"Error predicting model performance: {e}")
            return {
                "predicted_response_time_ms": 1000.0,
                "predicted_success_rate": 0.8,
                "predicted_cost_usd": 0.01,
                "confidence": 0.3
            }

    def get_optimization_recommendations(self) -> List[Dict[str, Any]]:
        """Get optimization recommendations based on analysis"""
        recommendations = []

        # Model loading recommendations
        underperforming_models = []
        overperforming_models = []

        for model_id, metrics in self.model_metrics.items():
            total_requests = metrics.get('total_requests', 0)
            if total_requests < 10:
                continue

            success_rate = metrics['successful_requests'] / total_requests
            avg_response_time = metrics['total_response_time'] / total_requests
            avg_cost = metrics['total_cost'] / total_requests

            if success_rate < 0.7 or avg_response_time > 5000:
                underperforming_models.append(model_id)
            elif success_rate > 0.95 and avg_response_time < 1000 and avg_cost < 0.005:
                overperforming_models.append(model_id)

        if underperforming_models:
            recommendations.append({
                "type": "model_replacement",
                "priority": "high",
                "description": f"Consider replacing underperforming models: {', '.join(underperforming_models[:3])}",
                "models": underperforming_models
            })

        if overperforming_models:
            recommendations.append({
                "type": "model_prioritization",
                "priority": "medium",
                "description": f"Prioritize usage of high-performing models: {', '.join(overperforming_models[:3])}",
                "models": overperforming_models
            })

        # Cost optimization recommendations
        expensive_models = []
        for model_id, metrics in self.model_metrics.items():
            total_requests = metrics.get('total_requests', 0)
            if total_requests < 10:
                continue

            avg_cost = metrics['total_cost'] / total_requests
            if avg_cost > 0.02:  # More than 2 cents per request
                expensive_models.append(model_id)

        if expensive_models:
            recommendations.append({
                "type": "cost_optimization",
                "priority": "medium",
                "description": f"Consider alternatives for expensive models: {', '.join(expensive_models[:3])}",
                "models": expensive_models
            })

        return recommendations

    def _continuous_optimization(self):
        """Continuous optimization loop"""
        while self.optimization_active:
            try:
                # Retrain models periodically
                if (self.optimization_stats['last_model_update'] is None or
                    (datetime.now() - self.optimization_stats['last_model_update']).hours >= 6):
                    self.train_optimization_models(retrain=True)

                # Generate and apply recommendations
                recommendations = self.get_optimization_recommendations()
                if recommendations:
                    for rec in recommendations:
                        self._record_optimization_decision(
                            rec['type'], rec.get('models', ['unknown']), None, None,
                            0.8, 0.7, False
                        )

                # Sleep for optimization interval
                time.sleep(1800)  # 30 minutes

            except Exception as e:
                logger.error(f"Error in continuous optimization: {e}")
                time.sleep(300)  # Wait before retrying

    def _record_optimization_decision(self, decision_type: str, model_ids: List[str],
                                   old_value: str, new_value: str,
                                   improvement_score: float, confidence_score: float,
                                   implemented: bool):
        """Record optimization decision"""
        with sqlite3.connect(self.db_path) as conn:
            for model_id in model_ids:
                conn.execute('''
                    INSERT INTO optimization_decisions
                    (timestamp, decision_type, model_id, old_value, new_value,
                     improvement_score, confidence_score, implemented)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    datetime.now(), decision_type, model_id, old_value, new_value,
                    improvement_score, confidence_score, implemented
                ))

    def shutdown(self):
        """Shutdown the model optimizer"""
        self.optimization_active = False
        if self.optimization_thread.is_alive():
            self.optimization_thread.join(timeout=5)

    def get_status(self) -> Dict[str, Any]:
        """Get current status of the AI model optimizer"""
        return {
            "models_trained": all([self.model_selector, self.performance_predictor]),
            "optimization_stats": self.optimization_stats,
            "tracked_models": len(self.model_metrics),
            "monitoring_active": self.optimization_active,
            "model_dir": self.model_dir,
            "database_path": self.db_path,
            "recommendations_count": len(self.get_optimization_recommendations())
        }

# Convenience functions
def get_ai_model_optimizer() -> AIModelOptimizer:
    """Get a singleton instance of the AI model optimizer"""
    if not hasattr(get_ai_model_optimizer, '_instance'):
        get_ai_model_optimizer._instance = AIModelOptimizer()
    return get_ai_model_optimizer._instance

def select_best_model(task_type: str, prompt_tokens: int, expected_response_tokens: int) -> str:
    """Select the best model for a task"""
    optimizer = get_ai_model_optimizer()
    selection = optimizer.select_optimal_model(task_type, prompt_tokens, expected_response_tokens)
    return selection.model_id

def optimize_model_cache(available_memory_gb: float) -> CacheOptimization:
    """Optimize model caching strategy"""
    optimizer = get_ai_model_optimizer()
    return optimizer.optimize_cache_strategy(available_memory_gb)