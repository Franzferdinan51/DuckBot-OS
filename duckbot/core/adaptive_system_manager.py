#!/usr/bin/env python3
"""
Adaptive System Manager for DuckBot v4.2
Self-learning system configuration optimization using reinforcement learning
and adaptive control algorithms
"""

import os
import json
import time
import asyncio
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
from enum import Enum
import threading
import sqlite3

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.distributions import Categorical
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    print("[WARNING] PyTorch not available - Reinforcement learning disabled")

try:
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score, classification_report
    import joblib
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("[WARNING] scikit-learn not available - Traditional ML disabled")

# Local imports
from .ml_optimization_engine import MLOptimizationEngine, SystemState
from .predictive_optimization import PredictiveOptimizer, PredictionTarget

logger = logging.getLogger(__name__)

class ActionType(Enum):
    """Types of adaptive actions"""
    SCALE_RESOURCES = "scale_resources"
    ADJUST_MODEL_CONFIG = "adjust_model_config"
    OPTIMIZE_CACHING = "optimize_caching"
    LOAD_BALANCE = "load_balance"
    THROTTLE_REQUESTS = "throttle_requests"
    PRIORITY_SCHEDULING = "priority_scheduling"
    MEMORY_MANAGEMENT = "memory_management"
    GPU_OPTIMIZATION = "gpu_optimization"
    NETWORK_OPTIMIZATION = "network_optimization"

class SystemParameter(Enum):
    """System parameters that can be adapted"""
    MAX_CONCURRENT_MODELS = "max_concurrent_models"
    MODEL_CACHE_SIZE = "model_cache_size"
    REQUEST_TIMEOUT = "request_timeout"
    BATCH_SIZE = "batch_size"
    MEMORY_LIMIT_MB = "memory_limit_mb"
    GPU_MEMORY_LIMIT_MB = "gpu_memory_limit_mb"
    CPU_THRESHOLD = "cpu_threshold"
    LATENCY_THRESHOLD = "latency_threshold"
    CACHE_TTL_SECONDS = "cache_ttl_seconds"
    QUEUE_SIZE_LIMIT = "queue_size_limit"
    THREAD_POOL_SIZE = "thread_pool_size"

@dataclass
class AdaptiveAction:
    """Represents an adaptive system action"""
    action_type: ActionType
    parameter: SystemParameter
    value: Any
    confidence: float
    expected_improvement: float
    execution_cost: float
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class SystemStateSnapshot:
    """Complete system state for adaptation"""
    timestamp: datetime
    system_metrics: Dict[str, float]
    current_parameters: Dict[SystemParameter, Any]
    performance_metrics: Dict[str, float]
    user_satisfaction_score: float
    resource_efficiency: float
    cost_efficiency: float

@dataclass
class AdaptationResult:
    """Result of an adaptation action"""
    action: AdaptiveAction
    before_metrics: Dict[str, float]
    after_metrics: Dict[str, float]
    improvement_score: float
    actual_cost: float
    success: bool
    timestamp: datetime = field(default_factory=datetime.now)

class PolicyNetwork(nn.Module):
    """Neural network for reinforcement learning policy"""
    def __init__(self, state_size: int, action_size: int, hidden_sizes: List[int] = None):
        super().__init__()

        if hidden_sizes is None:
            hidden_sizes = [256, 128, 64]

        layers = []
        prev_size = state_size

        for hidden_size in hidden_sizes:
            layers.extend([
                nn.Linear(prev_size, hidden_size),
                nn.ReLU(),
                nn.Dropout(0.2)
            ])
            prev_size = hidden_size

        layers.append(nn.Linear(prev_size, action_size))

        self.network = nn.Sequential(*layers)

    def forward(self, x):
        return self.network(x)

class ValueNetwork(nn.Module):
    """Neural network for value function approximation"""
    def __init__(self, state_size: int, hidden_sizes: List[int] = None):
        super().__init__()

        if hidden_sizes is None:
            hidden_sizes = [128, 64]

        layers = []
        prev_size = state_size

        for hidden_size in hidden_sizes:
            layers.extend([
                nn.Linear(prev_size, hidden_size),
                nn.ReLU(),
                nn.Dropout(0.2)
            ])
            prev_size = hidden_size

        layers.append(nn.Linear(prev_size, 1))

        self.network = nn.Sequential(*layers)

    def forward(self, x):
        return self.network(x)

class AdaptiveSystemManager:
    """Adaptive system management using reinforcement learning"""

    def __init__(self, ml_engine: MLOptimizationEngine = None,
                 predictor: PredictiveOptimizer = None):
        self.ml_engine = ml_engine
        self.predictor = predictor

        # Current system parameters
        self.current_parameters = self._initialize_default_parameters()

        # Action history and results
        self.action_history = deque(maxlen=10000)
        self.adaptation_results = deque(maxlen=5000)

        # Learning components
        self.policy_network = None
        self.value_network = None
        self.action_classifier = None
        self.state_scaler = None

        # Initialize ML components
        self._initialize_ml_components()

        # Reinforcement learning parameters
        self.learning_rate = 0.001
        self.gamma = 0.95  # Discount factor
        self.epsilon = 0.1  # Exploration rate
        self.epsilon_decay = 0.995
        self.min_epsilon = 0.01

        # Performance tracking
        self.performance_baseline = {}
        self.adaptation_stats = {
            'actions_taken': 0,
            'successful_adaptations': 0,
            'total_improvement': 0.0,
            'average_improvement': 0.0,
            'last_adaptation': None
        }

        # Background adaptation
        self.running = False
        self.adaptation_thread = None

        # Database for persistent storage
        self.db_path = os.path.join(os.getcwd(), 'adaptive_management.db')
        self._init_database()

    def _initialize_default_parameters(self) -> Dict[SystemParameter, Any]:
        """Initialize default system parameters"""
        return {
            SystemParameter.MAX_CONCURRENT_MODELS: 3,
            SystemParameter.MODEL_CACHE_SIZE: 5,
            SystemParameter.REQUEST_TIMEOUT: 30,
            SystemParameter.BATCH_SIZE: 8,
            SystemParameter.MEMORY_LIMIT_MB: 8192,
            SystemParameter.GPU_MEMORY_LIMIT_MB: 4096,
            SystemParameter.CPU_THRESHOLD: 80,
            SystemParameter.LATENCY_THRESHOLD: 1000,
            SystemParameter.CACHE_TTL_SECONDS: 3600,
            SystemParameter.QUEUE_SIZE_LIMIT: 100,
            SystemParameter.THREAD_POOL_SIZE: 8
        }

    def _init_database(self):
        """Initialize database for adaptation history"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS adaptation_actions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    action_type TEXT NOT NULL,
                    parameter TEXT NOT NULL,
                    value TEXT NOT NULL,
                    confidence REAL,
                    expected_improvement REAL,
                    execution_cost REAL,
                    success BOOLEAN,
                    actual_improvement REAL
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_parameters (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    parameter_name TEXT NOT NULL,
                    parameter_value TEXT NOT NULL,
                    performance_score REAL
                )
            ''')

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Database initialization failed: {e}")

    def _initialize_ml_components(self):
        """Initialize machine learning components"""
        if TORCH_AVAILABLE:
            # Initialize neural networks for reinforcement learning
            state_size = self._get_state_size()
            action_size = len(ActionType) * len(SystemParameter)

            self.policy_network = PolicyNetwork(state_size, action_size)
            self.value_network = ValueNetwork(state_size)

            self.policy_optimizer = optim.Adam(self.policy_network.parameters(), lr=self.learning_rate)
            self.value_optimizer = optim.Adam(self.value_network.parameters(), lr=self.learning_rate)

            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            self.policy_network.to(self.device)
            self.value_network.to(self.device)

        if SKLEARN_AVAILABLE:
            # Initialize action classifier
            self.action_classifier = RandomForestClassifier(n_estimators=100, random_state=42)
            self.state_scaler = StandardScaler()

    def _get_state_size(self) -> int:
        """Get the size of the state representation"""
        # System metrics: CPU, memory, GPU, disk, network, latency, throughput, error_rate
        system_metrics_size = 8

        # Current parameters
        parameters_size = len(SystemParameter)

        # Performance trends
        trends_size = 6  # CPU, memory, latency trends over different time periods

        # Time features
        time_features = 3  # hour, day_of_week, is_weekend

        return system_metrics_size + parameters_size + trends_size + time_features

    def create_state_representation(self, system_state: SystemState) -> np.ndarray:
        """Create state representation for learning algorithms"""
        try:
            # System metrics
            system_metrics = [
                system_state.cpu_percent,
                system_state.memory_percent,
                system_state.gpu_utilization,
                system_state.gpu_memory_percent,
                system_state.disk_usage_percent,
                system_state.avg_latency,
                system_state.request_rate,
                system_state.error_rate
            ]

            # Current parameters (normalized)
            parameters = self._normalize_parameters(self.current_parameters)

            # Performance trends (would be calculated from history)
            trends = self._calculate_performance_trends()

            # Time features
            time_features = [
                system_state.timestamp.hour / 24.0,  # Normalized hour
                system_state.timestamp.weekday() / 7.0,  # Normalized day
                1.0 if system_state.timestamp.weekday() >= 5 else 0.0  # Weekend flag
            ]

            # Combine all features
            state_vector = system_metrics + parameters + trends + time_features

            return np.array(state_vector, dtype=np.float32)

        except Exception as e:
            logger.error(f"State representation creation failed: {e}")
            return np.zeros(self._get_state_size(), dtype=np.float32)

    def _normalize_parameters(self, parameters: Dict[SystemParameter, Any]) -> List[float]:
        """Normalize parameter values for state representation"""
        normalization_ranges = {
            SystemParameter.MAX_CONCURRENT_MODELS: (1, 10),
            SystemParameter.MODEL_CACHE_SIZE: (1, 20),
            SystemParameter.REQUEST_TIMEOUT: (5, 300),
            SystemParameter.BATCH_SIZE: (1, 64),
            SystemParameter.MEMORY_LIMIT_MB: (1024, 32768),
            SystemParameter.GPU_MEMORY_LIMIT_MB: (512, 16384),
            SystemParameter.CPU_THRESHOLD: (50, 95),
            SystemParameter.LATENCY_THRESHOLD: (100, 5000),
            SystemParameter.CACHE_TTL_SECONDS: (60, 86400),
            SystemParameter.QUEUE_SIZE_LIMIT: (10, 1000),
            SystemParameter.THREAD_POOL_SIZE: (2, 32)
        }

        normalized = []

        for param in SystemParameter:
            if param in parameters:
                value = parameters[param]
                min_val, max_val = normalization_ranges.get(param, (0, 1))

                if max_val > min_val:
                    normalized_value = (value - min_val) / (max_val - min_val)
                else:
                    normalized_value = 0.5

                normalized.append(normalized_value)
            else:
                normalized.append(0.5)  # Default normalized value

        return normalized

    def _calculate_performance_trends(self) -> List[float]:
        """Calculate performance trends from historical data"""
        # This would be implemented using historical performance data
        # For now, return placeholder values
        return [0.0] * 6  # 6 trend features

    def select_adaptive_action(self, state: np.ndarray, current_metrics: Dict[str, float]) -> AdaptiveAction:
        """Select adaptive action using reinforcement learning"""
        try:
            if TORCH_AVAILABLE and self.policy_network:
                # Use policy network for action selection
                return self._select_action_rl(state, current_metrics)
            elif SKLEARN_AVAILABLE:
                # Use traditional ML for action selection
                return self._select_action_ml(state, current_metrics)
            else:
                # Use rule-based action selection
                return self._select_action_rule_based(current_metrics)

        except Exception as e:
            logger.error(f"Action selection failed: {e}")
            return self._select_action_rule_based(current_metrics)

    def _select_action_rl(self, state: np.ndarray, current_metrics: Dict[str, float]) -> AdaptiveAction:
        """Select action using reinforcement learning policy network"""
        try:
            state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)

            # Epsilon-greedy exploration
            if np.random.random() < self.epsilon:
                # Random exploration
                action_type = np.random.choice(list(ActionType))
                parameter = np.random.choice(list(SystemParameter))
                value = self._generate_random_parameter_value(parameter)
            else:
                # Policy-based selection
                with torch.no_grad():
                    action_logits = self.policy_network(state_tensor)
                    action_probs = torch.softmax(action_logits, dim=-1)

                    # Select action
                    action_index = Categorical(action_probs).sample().item()
                    action_type, parameter = self._index_to_action_parameter(action_index)
                    value = self._calculate_optimal_parameter_value(parameter, current_metrics)

            # Calculate confidence and expected improvement
            confidence = self._calculate_action_confidence(action_type, parameter, current_metrics)
            expected_improvement = self._estimate_improvement(action_type, parameter, value, current_metrics)
            execution_cost = self._estimate_execution_cost(action_type)

            return AdaptiveAction(
                action_type=action_type,
                parameter=parameter,
                value=value,
                confidence=confidence,
                expected_improvement=expected_improvement,
                execution_cost=execution_cost
            )

        except Exception as e:
            logger.error(f"RL action selection failed: {e}")
            return self._select_action_rule_based(current_metrics)

    def _select_action_ml(self, state: np.ndarray, current_metrics: Dict[str, float]) -> AdaptiveAction:
        """Select action using traditional machine learning"""
        try:
            # This would use the action classifier to predict the best action
            # For now, use rule-based approach
            return self._select_action_rule_based(current_metrics)

        except Exception as e:
            logger.error(f"ML action selection failed: {e}")
            return self._select_action_rule_based(current_metrics)

    def _select_action_rule_based(self, current_metrics: Dict[str, float]) -> AdaptiveAction:
        """Select action using rule-based approach"""
        cpu_usage = current_metrics.get('cpu_percent', 0)
        memory_usage = current_metrics.get('memory_percent', 0)
        latency = current_metrics.get('avg_latency', 0)

        # High CPU usage
        if cpu_usage > 80:
            return AdaptiveAction(
                action_type=ActionType.THROTTLE_REQUESTS,
                parameter=SystemParameter.BATCH_SIZE,
                value=max(1, self.current_parameters[SystemParameter.BATCH_SIZE] // 2),
                confidence=0.8,
                expected_improvement=15.0,
                execution_cost=1.0
            )

        # High memory usage
        elif memory_usage > 85:
            return AdaptiveAction(
                action_type=ActionType.MEMORY_MANAGEMENT,
                parameter=SystemParameter.MAX_CONCURRENT_MODELS,
                value=max(1, self.current_parameters[SystemParameter.MAX_CONCURRENT_MODELS] - 1),
                confidence=0.9,
                expected_improvement=20.0,
                execution_cost=2.0
            )

        # High latency
        elif latency > 1000:
            return AdaptiveAction(
                action_type=ActionType.OPTIMIZE_CACHING,
                parameter=SystemParameter.CACHE_TTL_SECONDS,
                value=min(86400, self.current_parameters[SystemParameter.CACHE_TTL_SECONDS] * 2),
                confidence=0.7,
                expected_improvement=25.0,
                execution_cost=3.0
            )

        # Default optimization
        else:
            return AdaptiveAction(
                action_type=ActionType.LOAD_BALANCE,
                parameter=SystemParameter.THREAD_POOL_SIZE,
                value=min(32, self.current_parameters[SystemParameter.THREAD_POOL_SIZE] + 1),
                confidence=0.6,
                expected_improvement=10.0,
                execution_cost=1.5
            )

    def _index_to_action_parameter(self, index: int) -> Tuple[ActionType, SystemParameter]:
        """Convert action index to action type and parameter"""
        action_types = list(ActionType)
        parameters = list(SystemParameter)

        action_index = index // len(parameters)
        param_index = index % len(parameters)

        return action_types[action_index], parameters[param_index]

    def _generate_random_parameter_value(self, parameter: SystemParameter) -> Any:
        """Generate random value for parameter"""
        current_value = self.current_parameters.get(parameter, 1)

        if isinstance(current_value, int):
            variation = np.random.randint(-2, 3)
            return max(1, current_value + variation)
        else:
            variation = np.random.uniform(-0.2, 0.2)
            return max(0.1, current_value * (1 + variation))

    def _calculate_optimal_parameter_value(self, parameter: SystemParameter, current_metrics: Dict[str, float]) -> Any:
        """Calculate optimal parameter value based on current metrics"""
        current_value = self.current_parameters.get(parameter, 1)
        cpu_usage = current_metrics.get('cpu_percent', 0)
        memory_usage = current_metrics.get('memory_percent', 0)

        if parameter == SystemParameter.BATCH_SIZE:
            if cpu_usage > 80:
                return max(1, current_value // 2)
            elif cpu_usage < 50:
                return min(64, current_value * 2)
            else:
                return current_value

        elif parameter == SystemParameter.MAX_CONCURRENT_MODELS:
            if memory_usage > 85:
                return max(1, current_value - 1)
            elif memory_usage < 60 and cpu_usage < 70:
                return min(10, current_value + 1)
            else:
                return current_value

        elif parameter == SystemParameter.CACHE_TTL_SECONDS:
            if current_metrics.get('avg_latency', 0) > 1000:
                return min(86400, current_value * 2)
            else:
                return current_value

        return current_value

    def _calculate_action_confidence(self, action_type: ActionType, parameter: SystemParameter,
                                   current_metrics: Dict[str, float]) -> float:
        """Calculate confidence score for action selection"""
        # Simple heuristic-based confidence calculation
        base_confidence = 0.5

        if action_type == ActionType.MEMORY_MANAGEMENT and parameter == SystemParameter.MAX_CONCURRENT_MODELS:
            memory_usage = current_metrics.get('memory_percent', 0)
            if memory_usage > 90:
                base_confidence = 0.9
            elif memory_usage > 80:
                base_confidence = 0.8

        elif action_type == ActionType.THROTTLE_REQUESTS and parameter == SystemParameter.BATCH_SIZE:
            cpu_usage = current_metrics.get('cpu_percent', 0)
            if cpu_usage > 90:
                base_confidence = 0.9
            elif cpu_usage > 80:
                base_confidence = 0.8

        # Add some randomness to simulate uncertainty
        confidence = base_confidence + np.random.uniform(-0.1, 0.1)
        return max(0.1, min(1.0, confidence))

    def _estimate_improvement(self, action_type: ActionType, parameter: SystemParameter,
                            value: Any, current_metrics: Dict[str, float]) -> float:
        """Estimate expected improvement from action"""
        # Simple improvement estimation
        if action_type == ActionType.MEMORY_MANAGEMENT:
            memory_usage = current_metrics.get('memory_percent', 0)
            if memory_usage > 85:
                return 20.0

        elif action_type == ActionType.THROTTLE_REQUESTS:
            cpu_usage = current_metrics.get('cpu_percent', 0)
            if cpu_usage > 80:
                return 15.0

        elif action_type == ActionType.OPTIMIZE_CACHING:
            latency = current_metrics.get('avg_latency', 0)
            if latency > 1000:
                return 25.0

        return 10.0  # Default improvement estimate

    def _estimate_execution_cost(self, action_type: ActionType) -> float:
        """Estimate execution cost of action"""
        cost_mapping = {
            ActionType.SCALE_RESOURCES: 5.0,
            ActionType.ADJUST_MODEL_CONFIG: 3.0,
            ActionType.OPTIMIZE_CACHING: 2.0,
            ActionType.LOAD_BALANCE: 1.5,
            ActionType.THROTTLE_REQUESTS: 1.0,
            ActionType.PRIORITY_SCHEDULING: 2.0,
            ActionType.MEMORY_MANAGEMENT: 2.0,
            ActionType.GPU_OPTIMIZATION: 3.0,
            ActionType.NETWORK_OPTIMIZATION: 2.5
        }

        return cost_mapping.get(action_type, 1.0)

    def execute_adaptive_action(self, action: AdaptiveAction, before_metrics: Dict[str, float]) -> AdaptationResult:
        """Execute adaptive action and return result"""
        try:
            logger.info(f"Executing adaptive action: {action.action_type.value} on {action.parameter.value}")

            # Store before metrics
            before_metrics_copy = before_metrics.copy()

            # Execute the action
            success = self._apply_action(action)

            # Wait for system to stabilize
            time.sleep(5)

            # Collect after metrics
            after_metrics = self._collect_current_metrics()

            # Calculate improvement
            improvement_score = self._calculate_improvement_score(before_metrics_copy, after_metrics)

            # Update parameters
            if success:
                self.current_parameters[action.parameter] = action.value

            # Create result
            result = AdaptationResult(
                action=action,
                before_metrics=before_metrics_copy,
                after_metrics=after_metrics,
                improvement_score=improvement_score,
                actual_cost=action.execution_cost,
                success=success
            )

            # Store result
            self.adaptation_results.append(result)
            self._store_adaptation_result(result)

            # Update statistics
            self.adaptation_stats['actions_taken'] += 1
            if success:
                self.adaptation_stats['successful_adaptations'] += 1
                self.adaptation_stats['total_improvement'] += improvement_score

            self.adaptation_stats['average_improvement'] = (
                self.adaptation_stats['total_improvement'] / self.adaptation_stats['actions_taken']
                if self.adaptation_stats['actions_taken'] > 0 else 0.0
            )

            self.adaptation_stats['last_adaptation'] = datetime.now()

            # Update reinforcement learning
            if success and TORCH_AVAILABLE:
                self._update_rl_models(action, result)

            # Decay epsilon
            if self.epsilon > self.min_epsilon:
                self.epsilon *= self.epsilon_decay

            return result

        except Exception as e:
            logger.error(f"Adaptive action execution failed: {e}")

            # Create failed result
            return AdaptationResult(
                action=action,
                before_metrics=before_metrics,
                after_metrics=before_metrics.copy(),
                improvement_score=0.0,
                actual_cost=action.execution_cost,
                success=False
            )

    def _apply_action(self, action: AdaptiveAction) -> bool:
        """Apply the adaptive action to the system"""
        try:
            # This is a simplified implementation
            # In a real system, this would interface with actual system components

            if action.action_type == ActionType.MEMORY_MANAGEMENT:
                if action.parameter == SystemParameter.MAX_CONCURRENT_MODELS:
                    logger.info(f"Setting max concurrent models to: {action.value}")
                    return True

            elif action.action_type == ActionType.THROTTLE_REQUESTS:
                if action.parameter == SystemParameter.BATCH_SIZE:
                    logger.info(f"Setting batch size to: {action.value}")
                    return True

            elif action.action_type == ActionType.OPTIMIZE_CACHING:
                if action.parameter == SystemParameter.CACHE_TTL_SECONDS:
                    logger.info(f"Setting cache TTL to: {action.value} seconds")
                    return True

            elif action.action_type == ActionType.LOAD_BALANCE:
                if action.parameter == SystemParameter.THREAD_POOL_SIZE:
                    logger.info(f"Setting thread pool size to: {action.value}")
                    return True

            return True

        except Exception as e:
            logger.error(f"Failed to apply action: {e}")
            return False

    def _collect_current_metrics(self) -> Dict[str, float]:
        """Collect current system metrics"""
        try:
            import psutil

            return {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'avg_latency': 0,  # Would be collected from actual system
                'request_rate': 0,  # Would be collected from actual system
                'error_rate': 0,    # Would be collected from actual system
                'throughput': 0,    # Would be collected from actual system
                'gpu_utilization': 0,  # Would be collected if GPU available
                'disk_usage': psutil.disk_usage('/').percent
            }

        except Exception as e:
            logger.error(f"Failed to collect metrics: {e}")
            return {}

    def _calculate_improvement_score(self, before_metrics: Dict[str, float],
                                    after_metrics: Dict[str, float]) -> float:
        """Calculate improvement score from adaptation"""
        try:
            improvements = []

            # CPU improvement
            if 'cpu_percent' in before_metrics and 'cpu_percent' in after_metrics:
                cpu_improvement = before_metrics['cpu_percent'] - after_metrics['cpu_percent']
                improvements.append(cpu_improvement)

            # Memory improvement
            if 'memory_percent' in before_metrics and 'memory_percent' in after_metrics:
                memory_improvement = before_metrics['memory_percent'] - after_metrics['memory_percent']
                improvements.append(memory_improvement)

            # Latency improvement
            if 'avg_latency' in before_metrics and 'avg_latency' in after_metrics:
                latency_improvement = before_metrics['avg_latency'] - after_metrics['avg_latency']
                improvements.append(latency_improvement / 100)  # Scale down latency

            # Throughput improvement
            if 'throughput' in before_metrics and 'throughput' in after_metrics:
                throughput_improvement = after_metrics['throughput'] - before_metrics['throughput']
                improvements.append(throughput_improvement)

            # Calculate weighted average
            if improvements:
                return np.mean(improvements)
            else:
                return 0.0

        except Exception as e:
            logger.error(f"Improvement calculation failed: {e}")
            return 0.0

    def _store_adaptation_result(self, result: AdaptationResult):
        """Store adaptation result in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO adaptation_actions (
                    timestamp, action_type, parameter, value, confidence,
                    expected_improvement, execution_cost, success, actual_improvement
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                result.timestamp.isoformat(),
                result.action.action_type.value,
                result.action.parameter.value,
                str(result.action.value),
                result.action.confidence,
                result.action.expected_improvement,
                result.actual_cost,
                result.success,
                result.improvement_score
            ))

            # Store current parameters
            for param, value in self.current_parameters.items():
                cursor.execute('''
                    INSERT INTO system_parameters (timestamp, parameter_name, parameter_value, performance_score)
                    VALUES (?, ?, ?, ?)
                ''', (
                    datetime.now().isoformat(),
                    param.value,
                    str(value),
                    result.improvement_score
                ))

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Failed to store adaptation result: {e}")

    def _update_rl_models(self, action: AdaptiveAction, result: AdaptationResult):
        """Update reinforcement learning models with adaptation result"""
        try:
            # This would implement reinforcement learning updates
            # For now, it's a placeholder
            pass

        except Exception as e:
            logger.error(f"RL model update failed: {e}")

    def adaptive_control_loop(self, system_state: SystemState):
        """Main adaptive control loop"""
        try:
            # Create state representation
            state = self.create_state_representation(system_state)

            # Collect current metrics
            current_metrics = {
                'cpu_percent': system_state.cpu_percent,
                'memory_percent': system_state.memory_percent,
                'avg_latency': system_state.avg_latency,
                'request_rate': system_state.request_rate,
                'error_rate': system_state.error_rate,
                'throughput': system_state.request_rate
            }

            # Select adaptive action
            action = self.select_adaptive_action(state, current_metrics)

            # Execute action if confidence is high enough
            if action.confidence > 0.6:  # Confidence threshold
                result = self.execute_adaptive_action(action, current_metrics)

                if result.success:
                    logger.info(f"Adaptive action successful: {action.action_type.value} "
                               f"improvement: {result.improvement_score:.2f}")
                else:
                    logger.warning(f"Adaptive action failed: {action.action_type.value}")
            else:
                logger.debug(f"Action confidence too low: {action.confidence:.3f}")

        except Exception as e:
            logger.error(f"Adaptive control loop failed: {e}")

    def start_adaptive_management(self):
        """Start adaptive management background process"""
        if self.running:
            return

        self.running = True
        self.adaptation_thread = threading.Thread(target=self._adaptive_management_loop, daemon=True)
        self.adaptation_thread.start()

        logger.info("Adaptive system management started")

    def stop_adaptive_management(self):
        """Stop adaptive management"""
        self.running = False
        if self.adaptation_thread:
            self.adaptation_thread.join(timeout=5)

        logger.info("Adaptive system management stopped")

    def _adaptive_management_loop(self):
        """Background loop for adaptive management"""
        while self.running:
            try:
                # Get current system state (would come from actual system monitoring)
                system_state = self._get_current_system_state()

                if system_state:
                    # Run adaptive control
                    self.adaptive_control_loop(system_state)

                # Sleep for next iteration
                time.sleep(60)  # Check every minute

            except Exception as e:
                logger.error(f"Adaptive management loop error: {e}")
                time.sleep(30)  # Wait before retrying

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

            return SystemState(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                gpu_utilization=0.0,  # Would be populated if GPU available
                gpu_memory_percent=0.0,
                disk_usage_percent=disk.percent,
                network_io=network_io,
                active_models=[],  # Would be populated from model manager
                request_rate=0.0,   # Would be populated from request tracker
                error_rate=0.0,     # Would be populated from error tracker
                avg_latency=0.0     # Would be populated from latency tracker
            )

        except Exception as e:
            logger.error(f"Failed to get system state: {e}")
            return None

    def get_adaptation_status(self) -> Dict[str, Any]:
        """Get current adaptation status"""
        return {
            'running': self.running,
            'current_parameters': {
                param.value: value for param, value in self.current_parameters.items()
            },
            'adaptation_statistics': self.adaptation_stats,
            'epsilon': self.epsilon if TORCH_AVAILABLE else None,
            'ml_components_available': {
                'reinforcement_learning': TORCH_AVAILABLE,
                'traditional_ml': SKLEARN_AVAILABLE
            },
            'recent_actions': [
                {
                    'action_type': result.action.action_type.value,
                    'parameter': result.action.parameter.value,
                    'success': result.success,
                    'improvement': result.improvement_score,
                    'timestamp': result.timestamp.isoformat()
                }
                for result in list(self.adaptation_results)[-5:]
            ]
        }

    def export_adaptation_data(self, filepath: str) -> bool:
        """Export adaptation history for analysis"""
        try:
            data = {
                'current_parameters': {
                    param.value: value for param, value in self.current_parameters.items()
                },
                'adaptation_results': [
                    {
                        'timestamp': result.timestamp.isoformat(),
                        'action_type': result.action.action_type.value,
                        'parameter': result.action.parameter.value,
                        'value': result.action.value,
                        'confidence': result.action.confidence,
                        'expected_improvement': result.action.expected_improvement,
                        'actual_improvement': result.improvement_score,
                        'success': result.success,
                        'execution_cost': result.actual_cost
                    }
                    for result in self.adaptation_results
                ],
                'adaptation_statistics': self.adaptation_stats,
                'export_timestamp': datetime.now().isoformat()
            }

            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)

            logger.info(f"Adaptation data exported to: {filepath}")
            return True

        except Exception as e:
            logger.error(f"Failed to export adaptation data: {e}")
            return False

def main():
    """Main function for testing the adaptive system manager"""
    print("[EMOJI] DuckBot Adaptive System Manager")
    print("=" * 50)

    # Initialize adaptive manager
    manager = AdaptiveSystemManager()

    # Display status
    status = manager.get_adaptation_status()
    print(f"\n[STATUS] Adaptive Manager Status:")
    print(f"  Running: {status['running']}")
    print(f"  RL Available: {status['ml_components_available']['reinforcement_learning']}")
    print(f"  ML Available: {status['ml_components_available']['traditional_ml']}")

    # Test adaptive actions
    print(f"\n[TEST] Testing adaptive action selection...")

    # Create sample system state
    import psutil
    system_state = SystemState(
        timestamp=datetime.now(),
        cpu_percent=psutil.cpu_percent(interval=1),
        memory_percent=psutil.virtual_memory().percent,
        gpu_utilization=0.0,
        gpu_memory_percent=0.0,
        disk_usage_percent=psutil.disk_usage('/').percent,
        network_io={'bytes_sent': 0, 'bytes_recv': 0},
        active_models=[],
        request_rate=0.0,
        error_rate=0.0,
        avg_latency=0.0
    )

    # Create state representation
    state = manager.create_state_representation(system_state)
    current_metrics = {
        'cpu_percent': system_state.cpu_percent,
        'memory_percent': system_state.memory_percent,
        'avg_latency': system_state.avg_latency,
        'request_rate': system_state.request_rate,
        'error_rate': system_state.error_rate,
        'throughput': system_state.request_rate
    }

    # Test action selection
    action = manager.select_adaptive_action(state, current_metrics)

    print(f"[ACTION] Selected action: {action.action_type.value}")
    print(f"  Parameter: {action.parameter.value}")
    print(f"  Value: {action.value}")
    print(f"  Confidence: {action.confidence:.3f}")
    print(f"  Expected improvement: {action.expected_improvement:.2f}")

    # Test action execution
    print(f"\n[EXECUTE] Testing action execution...")

    result = manager.execute_adaptive_action(action, current_metrics)

    print(f"[RESULT] Action execution: {'Success' if result.success else 'Failed'}")
    print(f"  Improvement score: {result.improvement_score:.2f}")
    print(f"  Actual cost: {result.actual_cost:.2f}")

    # Start adaptive management
    print(f"\n[START] Starting adaptive management...")
    manager.start_adaptive_management()

    # Run for demonstration
    try:
        print(f"[EMOJI] Adaptive management running (Press Ctrl+C to stop)")
        while True:
            time.sleep(30)

            # Periodic status update
            if np.random.random() < 0.2:  # 20% chance every 30 seconds
                status = manager.get_adaptation_status()
                stats = status['adaptation_statistics']
                print(f"[STATUS] Actions: {stats['actions_taken']}, "
                      f"Success rate: {stats['successful_adaptations']}/{stats['actions_taken']}")

    except KeyboardInterrupt:
        print(f"\n[EMOJI] Stopping adaptive management...")
        manager.stop_adaptive_management()
        print(f"[EMOJI] Done!")

if __name__ == "__main__":
    main()