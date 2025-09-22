"""
AI-Driven System Management Module

Provides autonomous system management capabilities including:
- Predictive maintenance and health monitoring
- Dynamic resource optimization
- Automated error recovery
- Performance tuning and optimization
- Service lifecycle management
- Autonomous decision execution

Author: Claude for DuckBot Enhanced v4.2
"""

import asyncio
import logging
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import sqlite3
import threading
from pathlib import Path

from .ai_system_controller import AISystemController, AICommand, AICommandType
from .ai_decision_maker import AIDecisionMaker, DecisionCategory, DecisionContext, AIDecision
from .ai_knowledge_base import AIKnowledgeBase, KnowledgeEntry, KnowledgeQuery, KnowledgeCategory
from .monitoring_system import DuckBotMonitoring, MetricsCollector, AlertSeverity

logger = logging.getLogger(__name__)

class ManagementAction(Enum):
    """Types of autonomous management actions"""
    HEALTH_CHECK = "health_check"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    ERROR_RECOVERY = "error_recovery"
    RESOURCE_ADJUSTMENT = "resource_adjustment"
    SERVICE_RESTART = "service_restart"
    CACHE_CLEANUP = "cache_cleanup"
    LOG_ROTATION = "log_rotation"
    MEMORY_OPTIMIZATION = "memory_optimization"
    SECURITY_HARDENING = "security_hardening"
    PREDICTIVE_MAINTENANCE = "predictive_maintenance"

@dataclass
class ManagementPolicy:
    """Defines autonomous management policies"""
    name: str
    action_type: ManagementAction
    trigger_conditions: Dict[str, Any]
    action_parameters: Dict[str, Any]
    cooldown_period: int = 300  # seconds
    max_attempts: int = 3
    enabled: bool = True
    priority: int = 5  # 1-10, higher = higher priority

@dataclass
class ManagementTask:
    """Represents an autonomous management task"""
    id: str
    policy: ManagementPolicy
    trigger_time: datetime
    execution_time: Optional[datetime] = None
    status: str = "pending"  # pending, executing, completed, failed
    result: Optional[Dict[str, Any]] = None
    attempts: int = 0
    confidence_score: float = 0.0

@dataclass
class SystemHealthSnapshot:
    """Snapshot of system health state"""
    timestamp: datetime
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_activity: float
    active_services: int
    error_count: int
    warning_count: int
    performance_score: float
    health_score: float
    active_agents: int
    active_commands: int

class AIDrivenSystemManager:
    """AI-driven autonomous system management"""

    def __init__(self, ai_controller: AISystemController,
                 decision_maker: AIDecisionMaker,
                 knowledge_base: AIKnowledgeBase,
                 monitoring_system: DuckBotMonitoring):
        self.ai_controller = ai_controller
        self.decision_maker = decision_maker
        self.knowledge_base = knowledge_base
        self.monitoring_system = monitoring_system

        # Management state
        self.policies: Dict[str, ManagementPolicy] = {}
        self.active_tasks: Dict[str, ManagementTask] = {}
        self.completed_tasks: List[ManagementTask] = []
        self.health_history: List[SystemHealthSnapshot] = []

        # Performance tracking
        self.management_stats = {
            "total_tasks_created": 0,
            "total_tasks_completed": 0,
            "total_tasks_failed": 0,
            "average_execution_time": 0.0,
            "success_rate": 0.0,
            "prevention_count": 0,
            "optimization_count": 0,
            "recovery_count": 0
        }

        # Configuration
        self.config = {
            "autonomy_level": 0.8,  # 0.0 = manual, 1.0 = fully autonomous
            "max_concurrent_tasks": 5,
            "health_check_interval": 60,  # seconds
            "performance_threshold": 0.7,
            "error_threshold": 5,  # errors per minute
            "learning_enabled": True,
            "predictive_enabled": True,
            "auto_recovery_enabled": True
        }

        # Database setup
        self.db_path = Path("duckbot_ai_management.db")
        self._init_database()

        # Background tasks
        self._running = False
        self._background_tasks: List[asyncio.Task] = []

        # Load default policies
        self._load_default_policies()

    def _init_database(self):
        """Initialize management database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Tasks table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS management_tasks (
                        id TEXT PRIMARY KEY,
                        policy_name TEXT,
                        trigger_time TEXT,
                        execution_time TEXT,
                        status TEXT,
                        result TEXT,
                        attempts INTEGER,
                        confidence_score REAL
                    )
                """)

                # Health snapshots table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS health_snapshots (
                        timestamp TEXT PRIMARY KEY,
                        cpu_usage REAL,
                        memory_usage REAL,
                        disk_usage REAL,
                        network_activity REAL,
                        active_services INTEGER,
                        error_count INTEGER,
                        warning_count INTEGER,
                        performance_score REAL,
                        health_score REAL,
                        active_agents INTEGER,
                        active_commands INTEGER
                    )
                """)

                # Management stats table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS management_stats (
                        stat_name TEXT PRIMARY KEY,
                        stat_value REAL,
                        last_updated TEXT
                    )
                """)

                conn.commit()
                logger.info("AI Management database initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize management database: {e}")

    def _load_default_policies(self):
        """Load default autonomous management policies"""
        default_policies = [
            ManagementPolicy(
                name="High CPU Usage Optimization",
                action_type=ManagementAction.PERFORMANCE_OPTIMIZATION,
                trigger_conditions={
                    "cpu_usage": {"operator": ">", "value": 0.85},
                    "duration": {"operator": ">", "value": 300}  # 5 minutes
                },
                action_parameters={
                    "optimize_models": True,
                    "reduce_services": True,
                    "cleanup_memory": True
                },
                cooldown_period=600,
                priority=8
            ),

            ManagementPolicy(
                name="Memory Leak Detection",
                action_type=ManagementAction.MEMORY_OPTIMIZATION,
                trigger_conditions={
                    "memory_usage": {"operator": ">", "value": 0.90},
                    "growth_rate": {"operator": ">", "value": 0.01}  # 1% per minute
                },
                action_parameters={
                    "garbage_collect": True,
                    "restart_services": True,
                    "clear_caches": True
                },
                cooldown_period=900,
                priority=9
            ),

            ManagementPolicy(
                name="Service Failure Recovery",
                action_type=ManagementAction.SERVICE_RESTART,
                trigger_conditions={
                    "service_status": {"operator": "=", "value": "failed"},
                    "consecutive_failures": {"operator": ">=", "value": 3}
                },
                action_parameters={
                    "graceful_restart": True,
                    "backup_state": True,
                    "notify_admin": True
                },
                cooldown_period=300,
                priority=10
            ),

            ManagementPolicy(
                name="Predictive Maintenance",
                action_type=ManagementAction.PREDICTIVE_MAINTENANCE,
                trigger_conditions={
                    "error_trend": {"operator": ">", "value": 0.2},  # 20% increase
                    "performance_degradation": {"operator": ">", "value": 0.15}
                },
                action_parameters={
                    "health_check": True,
                    "optimize_system": True,
                    "preventive_actions": True
                },
                cooldown_period=3600,
                priority=6
            ),

            ManagementPolicy(
                name="Cache Cleanup",
                action_type=ManagementAction.CACHE_CLEANUP,
                trigger_conditions={
                    "cache_size": {"operator": ">", "value": 1000000000},  # 1GB
                    "cache_hit_rate": {"operator": "<", "value": 0.5}
                },
                action_parameters={
                    "clear_expired": True,
                    "compress_remaining": True,
                    "optimize_structure": True
                },
                cooldown_period=1800,
                priority=4
            )
        ]

        for policy in default_policies:
            self.policies[policy.name] = policy

        logger.info(f"Loaded {len(default_policies)} default management policies")

    async def start_management(self):
        """Start autonomous system management"""
        if self._running:
            logger.warning("AI System Manager is already running")
            return

        self._running = True
        logger.info("Starting AI-Driven System Manager")

        # Start background tasks
        self._background_tasks = [
            asyncio.create_task(self._health_monitoring_loop()),
            asyncio.create_task(self._task_execution_loop()),
            asyncio.create_task(self._predictive_analysis_loop()),
            asyncio.create_task(self._performance_optimization_loop()),
            asyncio.create_task(self._learning_and_adaptation_loop())
        ]

        logger.info("AI System Manager started successfully")

    async def stop_management(self):
        """Stop autonomous system management"""
        if not self._running:
            return

        self._running = False
        logger.info("Stopping AI-Driven System Manager")

        # Cancel background tasks
        for task in self._background_tasks:
            task.cancel()

        # Wait for tasks to complete
        await asyncio.gather(*self._background_tasks, return_exceptions=True)
        self._background_tasks.clear()

        logger.info("AI System Manager stopped successfully")

    async def _health_monitoring_loop(self):
        """Continuous health monitoring loop"""
        while self._running:
            try:
                # Take health snapshot
                snapshot = await self._capture_health_snapshot()
                self.health_history.append(snapshot)

                # Keep only recent history (last 1000 snapshots)
                if len(self.health_history) > 1000:
                    self.health_history = self.health_history[-1000:]

                # Check for policy triggers
                await self._check_policy_triggers(snapshot)

                # Store snapshot in database
                await self._store_health_snapshot(snapshot)

                await asyncio.sleep(self.config["health_check_interval"])

            except Exception as e:
                logger.error(f"Error in health monitoring loop: {e}")
                await asyncio.sleep(30)  # Brief pause before retry

    async def _capture_health_snapshot(self) -> SystemHealthSnapshot:
        """Capture current system health snapshot"""
        try:
            # Get metrics from monitoring system
            metrics = self.monitoring_system.metrics_collector.get_current_metrics()

            # Get system status
            system_status = self.monitoring_system.get_system_status()

            # Get active services count
            active_services = len(system_status.get("active_services", []))

            # Get error and warning counts
            error_count = len(self.monitoring_system.alert_manager.alerts.get(
                AlertSeverity.ERROR, []))
            warning_count = len(self.monitoring_system.alert_manager.alerts.get(
                AlertSeverity.WARNING, []))

            # Get active agents and commands
            active_agents = len(getattr(self.ai_controller, 'active_agents', {}))
            active_commands = len(getattr(self.ai_controller, 'active_commands', {}))

            return SystemHealthSnapshot(
                timestamp=datetime.now(),
                cpu_usage=metrics.get("cpu_percent", 0.0) / 100.0,
                memory_usage=metrics.get("memory_percent", 0.0) / 100.0,
                disk_usage=metrics.get("disk_percent", 0.0) / 100.0,
                network_activity=metrics.get("network_io", {}).get("total", 0.0),
                active_services=active_services,
                error_count=error_count,
                warning_count=warning_count,
                performance_score=system_status.get("performance_score", 0.0),
                health_score=system_status.get("health_score", 0.0),
                active_agents=active_agents,
                active_commands=active_commands
            )

        except Exception as e:
            logger.error(f"Error capturing health snapshot: {e}")
            # Return default snapshot
            return SystemHealthSnapshot(
                timestamp=datetime.now(),
                cpu_usage=0.0, memory_usage=0.0, disk_usage=0.0,
                network_activity=0.0, active_services=0, error_count=0,
                warning_count=0, performance_score=0.0, health_score=0.0,
                active_agents=0, active_commands=0
            )

    async def _check_policy_triggers(self, snapshot: SystemHealthSnapshot):
        """Check if any management policies should be triggered"""
        for policy_name, policy in self.policies.items():
            if not policy.enabled:
                continue

            try:
                if await self._evaluate_policy_conditions(policy, snapshot):
                    # Check cooldown period
                    if await self._check_cooldown_period(policy_name):
                        continue

                    # Create management task
                    task = await self._create_management_task(policy, snapshot)
                    if task:
                        self.active_tasks[task.id] = task
                        self.management_stats["total_tasks_created"] += 1
                        logger.info(f"Created management task: {task.id} for policy: {policy_name}")

            except Exception as e:
                logger.error(f"Error checking policy triggers for {policy_name}: {e}")

    async def _evaluate_policy_conditions(self, policy: ManagementPolicy,
                                        snapshot: SystemHealthSnapshot) -> bool:
        """Evaluate if policy conditions are met"""
        try:
            conditions = policy.trigger_conditions

            # CPU usage condition
            if "cpu_usage" in conditions:
                condition = conditions["cpu_usage"]
                cpu_condition_met = self._evaluate_numeric_condition(
                    snapshot.cpu_usage, condition["operator"], condition["value"]
                )
                if not cpu_condition_met:
                    return False

            # Memory usage condition
            if "memory_usage" in conditions:
                condition = conditions["memory_usage"]
                memory_condition_met = self._evaluate_numeric_condition(
                    snapshot.memory_usage, condition["operator"], condition["value"]
                )
                if not memory_condition_met:
                    return False

            # Error count condition
            if "error_count" in conditions:
                condition = conditions["error_count"]
                error_condition_met = self._evaluate_numeric_condition(
                    snapshot.error_count, condition["operator"], condition["value"]
                )
                if not error_condition_met:
                    return False

            # Performance score condition
            if "performance_score" in conditions:
                condition = conditions["performance_score"]
                perf_condition_met = self._evaluate_numeric_condition(
                    snapshot.performance_score, condition["operator"], condition["value"]
                )
                if not perf_condition_met:
                    return False

            # Additional condition evaluations can be added here

            return True

        except Exception as e:
            logger.error(f"Error evaluating policy conditions: {e}")
            return False

    def _evaluate_numeric_condition(self, value: float, operator: str, threshold: float) -> bool:
        """Evaluate a numeric condition"""
        if operator == ">":
            return value > threshold
        elif operator == ">=":
            return value >= threshold
        elif operator == "<":
            return value < threshold
        elif operator == "<=":
            return value <= threshold
        elif operator == "==":
            return value == threshold
        elif operator == "!=":
            return value != threshold
        else:
            logger.warning(f"Unknown operator: {operator}")
            return False

    async def _check_cooldown_period(self, policy_name: str) -> bool:
        """Check if policy is in cooldown period"""
        try:
            # Find most recent completed task for this policy
            recent_tasks = [
                task for task in self.completed_tasks
                if task.policy.name == policy_name and task.status == "completed"
            ]

            if not recent_tasks:
                return False

            most_recent = max(recent_tasks, key=lambda t: t.execution_time or t.trigger_time)
            time_since_completion = (datetime.now() - most_recent.execution_time).total_seconds()

            policy = self.policies[policy_name]
            return time_since_completion < policy.cooldown_period

        except Exception as e:
            logger.error(f"Error checking cooldown period: {e}")
            return False

    async def _create_management_task(self, policy: ManagementPolicy,
                                    snapshot: SystemHealthSnapshot) -> Optional[ManagementTask]:
        """Create a management task for the given policy"""
        try:
            task_id = f"task_{policy.action_type.value}_{int(time.time())}"

            # Create decision context for AI analysis
            context = DecisionContext(
                system_state={
                    "health_snapshot": snapshot.__dict__,
                    "active_tasks": len(self.active_tasks),
                    "completed_tasks": len(self.completed_tasks),
                    "system_history": self.health_history[-10:] if self.health_history else []
                },
                performance_metrics={
                    "success_rate": self.management_stats["success_rate"],
                    "average_execution_time": self.management_stats["average_execution_time"],
                    "prevention_count": self.management_stats["prevention_count"]
                },
                constraints={
                    "max_concurrent_tasks": self.config["max_concurrent_tasks"],
                    "autonomy_level": self.config["autonomy_level"]
                },
                objectives=["system_optimization", "error_prevention", "performance_improvement"]
            )

            # Get AI decision
            decision = await self.decision_maker.make_decision(
                DecisionCategory.SYSTEM_MANAGEMENT, context
            )

            if decision.confidence_score < self.config["autonomy_level"]:
                logger.info(f"AI confidence too low for task creation: {decision.confidence_score:.2f}")
                return None

            task = ManagementTask(
                id=task_id,
                policy=policy,
                trigger_time=snapshot.timestamp,
                confidence_score=decision.confidence_score
            )

            return task

        except Exception as e:
            logger.error(f"Error creating management task: {e}")
            return None

    async def _task_execution_loop(self):
        """Execute pending management tasks"""
        while self._running:
            try:
                # Get tasks ready for execution
                ready_tasks = [
                    task for task in self.active_tasks.values()
                    if task.status == "pending" and len([
                        t for t in self.active_tasks.values()
                        if t.status == "executing"
                    ]) < self.config["max_concurrent_tasks"]
                ]

                # Sort by priority
                ready_tasks.sort(key=lambda t: t.policy.priority, reverse=True)

                for task in ready_tasks[:3]:  # Execute up to 3 tasks per cycle
                    await self._execute_management_task(task)

                await asyncio.sleep(10)  # Check every 10 seconds

            except Exception as e:
                logger.error(f"Error in task execution loop: {e}")
                await asyncio.sleep(30)

    async def _execute_management_task(self, task: ManagementTask):
        """Execute a management task"""
        try:
            task.status = "executing"
            task.execution_time = datetime.now()
            task.attempts += 1

            logger.info(f"Executing management task: {task.id}")

            # Execute based on action type
            result = await self._execute_action(task.policy.action_type, task.policy.action_parameters)

            task.result = result
            task.status = "completed"

            # Update stats
            self.management_stats["total_tasks_completed"] += 1
            if task.policy.action_type == ManagementAction.PERFORMANCE_OPTIMIZATION:
                self.management_stats["optimization_count"] += 1
            elif task.policy.action_type == ManagementAction.ERROR_RECOVERY:
                self.management_stats["recovery_count"] += 1
            elif task.policy.action_type == ManagementAction.PREDICTIVE_MAINTENANCE:
                self.management_stats["prevention_count"] += 1

            # Move to completed tasks
            self.completed_tasks.append(task)
            if task.id in self.active_tasks:
                del self.active_tasks[task.id]

            logger.info(f"Completed management task: {task.id}")

        except Exception as e:
            logger.error(f"Error executing management task {task.id}: {e}")
            task.status = "failed"
            task.result = {"error": str(e)}

            # Update stats
            self.management_stats["total_tasks_failed"] += 1

            # Retry if under max attempts
            if task.attempts < task.policy.max_attempts:
                task.status = "pending"
                await asyncio.sleep(60)  # Wait before retry
            else:
                # Move to completed as failed
                self.completed_tasks.append(task)
                if task.id in self.active_tasks:
                    del self.active_tasks[task.id]

    async def _execute_action(self, action_type: ManagementAction,
                            parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a specific management action"""
        try:
            if action_type == ManagementAction.PERFORMANCE_OPTIMIZATION:
                return await self._optimize_performance(parameters)
            elif action_type == ManagementAction.MEMORY_OPTIMIZATION:
                return await self._optimize_memory(parameters)
            elif action_type == ManagementAction.SERVICE_RESTART:
                return await self._restart_services(parameters)
            elif action_type == ManagementAction.PREDICTIVE_MAINTENANCE:
                return await self._perform_predictive_maintenance(parameters)
            elif action_type == ManagementAction.CACHE_CLEANUP:
                return await self._cleanup_cache(parameters)
            elif action_type == ManagementAction.HEALTH_CHECK:
                return await self._perform_health_check(parameters)
            else:
                return {"error": f"Unknown action type: {action_type}"}

        except Exception as e:
            logger.error(f"Error executing action {action_type}: {e}")
            return {"error": str(e)}

    async def _optimize_performance(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize system performance"""
        result = {"actions_taken": []}

        try:
            # Optimize models if requested
            if parameters.get("optimize_models", False):
                command = AICommand(
                    command_type=AICommandType.PERFORMANCE_OPTIMIZATION,
                    parameters={"target": "models", "action": "optimize"}
                )
                cmd_result = await self.ai_controller.process_command(command)
                result["actions_taken"].append({"action": "model_optimization", "result": cmd_result.success})

            # Reduce services if requested
            if parameters.get("reduce_services", False):
                command = AICommand(
                    command_type=AICommandType.SERVICE_CONTROL,
                    parameters={"action": "reduce_load", "services": "non_essential"}
                )
                cmd_result = await self.ai_controller.process_command(command)
                result["actions_taken"].append({"action": "service_reduction", "result": cmd_result.success})

            # Cleanup memory if requested
            if parameters.get("cleanup_memory", False):
                command = AICommand(
                    command_type=AICommandType.RESOURCE_MANAGEMENT,
                    parameters={"action": "memory_cleanup", "force": True}
                )
                cmd_result = await self.ai_controller.process_command(command)
                result["actions_taken"].append({"action": "memory_cleanup", "result": cmd_result.success})

            return result

        except Exception as e:
            logger.error(f"Error optimizing performance: {e}")
            return {"error": str(e), "actions_taken": result["actions_taken"]}

    async def _optimize_memory(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize memory usage"""
        result = {"actions_taken": []}

        try:
            # Garbage collection
            if parameters.get("garbage_collect", False):
                import gc
                collected = gc.collect()
                result["actions_taken"].append({"action": "garbage_collection", "collected_objects": collected})

            # Clear caches
            if parameters.get("clear_caches", False):
                command = AICommand(
                    command_type=AICommandType.RESOURCE_MANAGEMENT,
                    parameters={"action": "clear_all_caches"}
                )
                cmd_result = await self.ai_controller.process_command(command)
                result["actions_taken"].append({"action": "cache_clearing", "result": cmd_result.success})

            return result

        except Exception as e:
            logger.error(f"Error optimizing memory: {e}")
            return {"error": str(e), "actions_taken": result["actions_taken"]}

    async def _restart_services(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Restart failed services"""
        result = {"actions_taken": []}

        try:
            # Get failed services from monitoring system
            system_status = self.monitoring_system.get_system_status()
            failed_services = [
                service for service in system_status.get("services", [])
                if service.get("status") == "failed"
            ]

            for service in failed_services:
                service_name = service.get("name", "unknown")

                command = AICommand(
                    command_type=AICommandType.SERVICE_CONTROL,
                    parameters={
                        "action": "restart",
                        "service_name": service_name,
                        "graceful": parameters.get("graceful_restart", True)
                    }
                )

                cmd_result = await self.ai_controller.process_command(command)
                result["actions_taken"].append({
                    "action": "service_restart",
                    "service": service_name,
                    "result": cmd_result.success
                })

            return result

        except Exception as e:
            logger.error(f"Error restarting services: {e}")
            return {"error": str(e), "actions_taken": result["actions_taken"]}

    async def _perform_predictive_maintenance(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Perform predictive maintenance actions"""
        result = {"actions_taken": []}

        try:
            # Health check
            if parameters.get("health_check", False):
                command = AICommand(
                    command_type=AICommandType.SYSTEM_MONITORING,
                    parameters={"action": "comprehensive_health_check"}
                )
                cmd_result = await self.ai_controller.process_command(command)
                result["actions_taken"].append({"action": "health_check", "result": cmd_result.success})

            # System optimization
            if parameters.get("optimize_system", False):
                opt_result = await self._optimize_performance({
                    "optimize_models": True,
                    "reduce_services": True,
                    "cleanup_memory": True
                })
                result["actions_taken"].append({"action": "system_optimization", "result": opt_result})

            return result

        except Exception as e:
            logger.error(f"Error performing predictive maintenance: {e}")
            return {"error": str(e), "actions_taken": result["actions_taken"]}

    async def _cleanup_cache(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Clean up system caches"""
        result = {"actions_taken": []}

        try:
            # Clear expired cache entries
            if parameters.get("clear_expired", False):
                command = AICommand(
                    command_type=AICommandType.RESOURCE_MANAGEMENT,
                    parameters={"action": "clear_expired_cache"}
                )
                cmd_result = await self.ai_controller.process_command(command)
                result["actions_taken"].append({"action": "clear_expired", "result": cmd_result.success})

            # Compress remaining cache
            if parameters.get("compress_remaining", False):
                command = AICommand(
                    command_type=AICommandType.RESOURCE_MANAGEMENT,
                    parameters={"action": "compress_cache"}
                )
                cmd_result = await self.ai_controller.process_command(command)
                result["actions_taken"].append({"action": "compress_cache", "result": cmd_result.success})

            return result

        except Exception as e:
            logger.error(f"Error cleaning up cache: {e}")
            return {"error": str(e), "actions_taken": result["actions_taken"]}

    async def _perform_health_check(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        try:
            command = AICommand(
                command_type=AICommandType.HEALTH_MANAGEMENT,
                parameters={"action": "comprehensive_check", "detailed": True}
            )

            cmd_result = await self.ai_controller.process_command(command)
            return {"health_check_result": cmd_result.success, "details": cmd_result.result}

        except Exception as e:
            logger.error(f"Error performing health check: {e}")
            return {"error": str(e)}

    async def _predictive_analysis_loop(self):
        """Continuous predictive analysis loop"""
        while self._running:
            try:
                if not self.config["predictive_enabled"]:
                    await asyncio.sleep(300)
                    continue

                # Analyze trends in health history
                if len(self.health_history) >= 10:
                    await self._analyze_trends_and_predict()

                await asyncio.sleep(300)  # Check every 5 minutes

            except Exception as e:
                logger.error(f"Error in predictive analysis loop: {e}")
                await asyncio.sleep(60)

    async def _analyze_trends_and_predict(self):
        """Analyze system trends and predict issues"""
        try:
            recent_history = self.health_history[-20:]  # Last 20 snapshots

            # Analyze CPU trend
            cpu_values = [h.cpu_usage for h in recent_history]
            cpu_trend = self._calculate_trend(cpu_values)

            # Analyze memory trend
            memory_values = [h.memory_usage for h in recent_history]
            memory_trend = self._calculate_trend(memory_values)

            # Analyze error trend
            error_values = [h.error_count for h in recent_history]
            error_trend = self._calculate_trend(error_values)

            # Check for concerning trends
            if cpu_trend > 0.05:  # 5% increase per cycle
                logger.warning(f"CPU usage trending upward: {cpu_trend:.3f}")

            if memory_trend > 0.03:  # 3% increase per cycle
                logger.warning(f"Memory usage trending upward: {memory_trend:.3f}")

            if error_trend > 0.1:  # 10% increase per cycle
                logger.warning(f"Error count trending upward: {error_trend:.3f}")

            # Trigger preventive actions if trends are concerning
            if any([cpu_trend > 0.1, memory_trend > 0.08, error_trend > 0.2]):
                await self._trigger_preventive_actions()

        except Exception as e:
            logger.error(f"Error analyzing trends: {e}")

    def _calculate_trend(self, values: List[float]) -> float:
        """Calculate linear trend slope"""
        if len(values) < 2:
            return 0.0

        n = len(values)
        x_values = list(range(n))

        # Calculate linear regression slope
        x_mean = sum(x_values) / n
        y_mean = sum(values) / n

        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, values))
        denominator = sum((x - x_mean) ** 2 for x in x_values)

        if denominator == 0:
            return 0.0

        return numerator / denominator

    async def _trigger_preventive_actions(self):
        """Trigger preventive maintenance actions"""
        try:
            # Find predictive maintenance policy
            policy = self.policies.get("Predictive Maintenance")
            if policy and policy.enabled:
                # Create snapshot for current state
                snapshot = await self._capture_health_snapshot()

                # Create task if not in cooldown
                if not await self._check_cooldown_period(policy.name):
                    task = await self._create_management_task(policy, snapshot)
                    if task:
                        self.active_tasks[task.id] = task
                        logger.info("Created preventive maintenance task due to concerning trends")

        except Exception as e:
            logger.error(f"Error triggering preventive actions: {e}")

    async def _performance_optimization_loop(self):
        """Continuous performance optimization loop"""
        while self._running:
            try:
                # Check if optimization is needed
                if len(self.health_history) >= 5:
                    recent_snapshots = self.health_history[-5:]
                    avg_performance = sum(s.performance_score for s in recent_snapshots) / len(recent_snapshots)

                    if avg_performance < self.config["performance_threshold"]:
                        logger.info(f"Performance below threshold ({avg_performance:.2f}), triggering optimization")

                        # Find performance optimization policy
                        policy = self.policies.get("High CPU Usage Optimization")
                        if policy and policy.enabled and not await self._check_cooldown_period(policy.name):
                            snapshot = await self._capture_health_snapshot()
                            task = await self._create_management_task(policy, snapshot)
                            if task:
                                self.active_tasks[task.id] = task

                await asyncio.sleep(600)  # Check every 10 minutes

            except Exception as e:
                logger.error(f"Error in performance optimization loop: {e}")
                await asyncio.sleep(60)

    async def _learning_and_adaptation_loop(self):
        """Continuous learning and adaptation loop"""
        while self._running:
            try:
                if not self.config["learning_enabled"]:
                    await asyncio.sleep(600)
                    continue

                # Analyze completed tasks for learning
                if len(self.completed_tasks) >= 10:
                    await self._analyze_and_adapt()

                await asyncio.sleep(1800)  # Check every 30 minutes

            except Exception as e:
                logger.error(f"Error in learning loop: {e}")
                await asyncio.sleep(60)

    async def _analyze_and_adapt(self):
        """Analyze performance and adapt policies"""
        try:
            # Calculate success rate
            completed_count = len(self.completed_tasks)
            successful_count = len([t for t in self.completed_tasks if t.status == "completed"])

            if completed_count > 0:
                success_rate = successful_count / completed_count
                self.management_stats["success_rate"] = success_rate

                # Calculate average execution time
                completed_with_time = [
                    t for t in self.completed_tasks
                    if t.status == "completed" and t.execution_time and t.trigger_time
                ]

                if completed_with_time:
                    execution_times = [
                        (t.execution_time - t.trigger_time).total_seconds()
                        for t in completed_with_time
                    ]
                    avg_time = sum(execution_times) / len(execution_times)
                    self.management_stats["average_execution_time"] = avg_time

                # Adapt autonomy level based on success rate
                if success_rate > 0.9:
                    self.config["autonomy_level"] = min(1.0, self.config["autonomy_level"] + 0.05)
                elif success_rate < 0.7:
                    self.config["autonomy_level"] = max(0.3, self.config["autonomy_level"] - 0.05)

                logger.info(f"Adapted autonomy level to {self.config['autonomy_level']:.2f} based on success rate {success_rate:.2f}")

                # Store updated stats
                await self._store_management_stats()

        except Exception as e:
            logger.error(f"Error in learning and adaptation: {e}")

    async def _store_health_snapshot(self, snapshot: SystemHealthSnapshot):
        """Store health snapshot in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO health_snapshots
                    (timestamp, cpu_usage, memory_usage, disk_usage, network_activity,
                     active_services, error_count, warning_count, performance_score,
                     health_score, active_agents, active_commands)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    snapshot.timestamp.isoformat(),
                    snapshot.cpu_usage, snapshot.memory_usage, snapshot.disk_usage,
                    snapshot.network_activity, snapshot.active_services, snapshot.error_count,
                    snapshot.warning_count, snapshot.performance_score, snapshot.health_score,
                    snapshot.active_agents, snapshot.active_commands
                ))
                conn.commit()

        except Exception as e:
            logger.error(f"Error storing health snapshot: {e}")

    async def _store_management_stats(self):
        """Store management statistics in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                for stat_name, stat_value in self.management_stats.items():
                    cursor.execute("""
                        INSERT OR REPLACE INTO management_stats (stat_name, stat_value, last_updated)
                        VALUES (?, ?, ?)
                    """, (stat_name, stat_value, datetime.now().isoformat()))
                conn.commit()

        except Exception as e:
            logger.error(f"Error storing management stats: {e}")

    def get_management_status(self) -> Dict[str, Any]:
        """Get current management status"""
        return {
            "running": self._running,
            "config": self.config,
            "stats": self.management_stats,
            "active_tasks": len(self.active_tasks),
            "completed_tasks": len(self.completed_tasks),
            "policies": len(self.policies),
            "health_history_size": len(self.health_history),
            "autonomy_level": self.config["autonomy_level"]
        }

    def get_recent_tasks(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent management tasks"""
        recent_tasks = sorted(
            self.completed_tasks[-limit:],
            key=lambda t: t.execution_time or t.trigger_time,
            reverse=True
        )

        return [
            {
                "id": task.id,
                "policy": task.policy.name,
                "action_type": task.policy.action_type.value,
                "status": task.status,
                "trigger_time": task.trigger_time.isoformat(),
                "execution_time": task.execution_time.isoformat() if task.execution_time else None,
                "attempts": task.attempts,
                "confidence_score": task.confidence_score,
                "result": task.result
            }
            for task in recent_tasks
        ]

    def add_custom_policy(self, policy: ManagementPolicy) -> bool:
        """Add a custom management policy"""
        try:
            self.policies[policy.name] = policy
            logger.info(f"Added custom management policy: {policy.name}")
            return True

        except Exception as e:
            logger.error(f"Error adding custom policy: {e}")
            return False

    def remove_policy(self, policy_name: str) -> bool:
        """Remove a management policy"""
        try:
            if policy_name in self.policies:
                del self.policies[policy_name]
                logger.info(f"Removed management policy: {policy_name}")
                return True
            else:
                logger.warning(f"Policy not found: {policy_name}")
                return False

        except Exception as e:
            logger.error(f"Error removing policy: {e}")
            return False

    async def force_trigger_policy(self, policy_name: str) -> bool:
        """Force trigger a specific policy"""
        try:
            if policy_name not in self.policies:
                logger.error(f"Policy not found: {policy_name}")
                return False

            policy = self.policies[policy_name]
            snapshot = await self._capture_health_snapshot()

            task = await self._create_management_task(policy, snapshot)
            if task:
                self.active_tasks[task.id] = task
                logger.info(f"Force triggered policy: {policy_name}")
                return True
            else:
                logger.error(f"Failed to create task for policy: {policy_name}")
                return False

        except Exception as e:
            logger.error(f"Error force triggering policy: {e}")
            return False

    async def generate_management_report(self) -> Dict[str, Any]:
        """Generate comprehensive management report"""
        try:
            # Get current status
            current_snapshot = await self._capture_health_snapshot()

            # Calculate statistics
            total_tasks = self.management_stats["total_tasks_created"]
            successful_tasks = self.management_stats["total_tasks_completed"]
            failed_tasks = self.management_stats["total_tasks_failed"]

            success_rate = successful_tasks / total_tasks if total_tasks > 0 else 0.0

            # Analyze policy effectiveness
            policy_stats = {}
            for policy_name, policy in self.policies.items():
                policy_tasks = [
                    task for task in self.completed_tasks
                    if task.policy.name == policy_name
                ]

                if policy_tasks:
                    successful = len([t for t in policy_tasks if t.status == "completed"])
                    policy_stats[policy_name] = {
                        "total_executions": len(policy_tasks),
                        "successful_executions": successful,
                        "success_rate": successful / len(policy_tasks),
                        "average_confidence": sum(t.confidence_score for t in policy_tasks) / len(policy_tasks)
                    }

            # Generate recommendations
            recommendations = []
            if success_rate < 0.7:
                recommendations.append("Consider adjusting autonomy level or reviewing policy effectiveness")

            if current_snapshot.cpu_usage > 0.8:
                recommendations.append("High CPU usage detected - consider performance optimization")

            if current_snapshot.memory_usage > 0.85:
                recommendations.append("High memory usage detected - consider memory optimization")

            return {
                "report_timestamp": datetime.now().isoformat(),
                "system_status": {
                    "health_score": current_snapshot.health_score,
                    "performance_score": current_snapshot.performance_score,
                    "cpu_usage": current_snapshot.cpu_usage,
                    "memory_usage": current_snapshot.memory_usage,
                    "active_services": current_snapshot.active_services,
                    "active_agents": current_snapshot.active_agents
                },
                "management_statistics": {
                    "total_tasks": total_tasks,
                    "successful_tasks": successful_tasks,
                    "failed_tasks": failed_tasks,
                    "success_rate": success_rate,
                    "average_execution_time": self.management_stats["average_execution_time"],
                    "autonomy_level": self.config["autonomy_level"]
                },
                "policy_effectiveness": policy_stats,
                "recommendations": recommendations,
                "recent_activities": self.get_recent_tasks(5)
            }

        except Exception as e:
            logger.error(f"Error generating management report: {e}")
            return {"error": str(e)}