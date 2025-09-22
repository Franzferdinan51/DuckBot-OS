"""
AI Orchestrator - Main Integration Hub

Coordinates all AI components for comprehensive system management:
- AI System Controller (command interface)
- AI Decision Maker (intelligent decisions)
- AI Knowledge Base (system knowledge)
- AI-Driven System Manager (autonomous management)
- Monitoring System (system awareness)

Provides unified interface for AI-driven system operations.

Author: Claude for DuckBot Enhanced v4.2
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import json

from .ai_system_controller import AISystemController, AICommand, AICommandType, AICommandResult
from .ai_decision_maker import AIDecisionMaker, DecisionCategory, DecisionContext, AIDecision
from .ai_knowledge_base import AIKnowledgeBase, KnowledgeEntry, KnowledgeQuery, KnowledgeCategory
from .ai_driven_system_manager import AIDrivenSystemManager, ManagementPolicy, ManagementAction
from .monitoring_system import DuckBotMonitoring, MetricsCollector, AlertSeverity
from ..ai_router_gpt import AIRouter, ModelProvider

logger = logging.getLogger(__name__)

class OrchestratorMode(Enum):
    """Orchestrator operation modes"""
    MANUAL = "manual"           # All actions require manual approval
    ASSISTED = "assisted"       # AI suggests actions, human approves
    AUTONOMOUS = "autonomous"   # AI operates autonomously with constraints
    SUPERVISED = "supervised"   # Autonomous with human oversight

@dataclass
class OrchestratorConfig:
    """Configuration for AI Orchestrator"""
    mode: OrchestratorMode = OrchestratorMode.ASSISTED
    autonomy_level: float = 0.7  # 0.0 = manual, 1.0 = fully autonomous
    max_concurrent_operations: int = 10
    learning_enabled: bool = True
    predictive_enabled: bool = True
    auto_recovery_enabled: bool = True
    safety_checks_enabled: bool = True
    notification_level: str = "warning"  # info, warning, error, critical

@dataclass
class SystemOperation:
    """Represents a system operation managed by the orchestrator"""
    id: str
    operation_type: str
    description: str
    parameters: Dict[str, Any]
    priority: int = 5  # 1-10
    estimated_duration: int = 60  # seconds
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: str = "pending"  # pending, approved, executing, completed, failed, cancelled
    result: Optional[Dict[str, Any]] = None
    confidence_score: float = 0.0
    requires_approval: bool = True
    approved_by: Optional[str] = None

class AIOrchestrator:
    """Main AI Orchestrator for coordinated system management"""

    def __init__(self, config: Optional[OrchestratorConfig] = None):
        self.config = config or OrchestratorConfig()

        # Initialize all AI components
        self.ai_controller = AISystemController()
        self.decision_maker = AIDecisionMaker()
        self.knowledge_base = AIKnowledgeBase()
        self.monitoring_system = DuckBotMonitoring()
        self.ai_router = AIRouter()

        # Initialize AI-driven system manager
        self.system_manager = AIDrivenSystemManager(
            self.ai_controller,
            self.decision_maker,
            self.knowledge_base,
            self.monitoring_system
        )

        # Operation management
        self.operations: Dict[str, SystemOperation] = {}
        self.operation_history: List[SystemOperation] = []
        self.pending_approvals: List[SystemOperation] = []

        # Performance tracking
        self.orchestrator_stats = {
            "total_operations": 0,
            "completed_operations": 0,
            "failed_operations": 0,
            "autonomous_operations": 0,
            "average_decision_time": 0.0,
            "success_rate": 0.0,
            "knowledge_base_queries": 0,
            "preventive_actions": 0,
            "optimization_actions": 0,
            "recovery_actions": 0
        }

        # Background tasks
        self._running = False
        self._background_tasks: List[asyncio.Task] = []

        # Event handlers
        self.event_handlers: Dict[str, List[Callable]] = {}

        logger.info("AI Orchestrator initialized successfully")

    async def start_orchestrator(self):
        """Start the AI Orchestrator"""
        if self._running:
            logger.warning("AI Orchestrator is already running")
            return

        self._running = True
        logger.info(f"Starting AI Orchestrator in {self.config.mode.value} mode")

        # Start all components
        await self.monitoring_system.start_monitoring()
        await self.system_manager.start_management()

        # Start background tasks
        self._background_tasks = [
            asyncio.create_task(self._system_monitoring_loop()),
            asyncio.create_task(self._operation_processing_loop()),
            asyncio.create_task(self._decision_making_loop()),
            asyncio.create_task(self._learning_loop()),
            asyncio.create_task(self._health_check_loop())
        ]

        logger.info("AI Orchestrator started successfully")

    async def stop_orchestrator(self):
        """Stop the AI Orchestrator"""
        if not self._running:
            return

        self._running = False
        logger.info("Stopping AI Orchestrator")

        # Stop components
        await self.system_manager.stop_management()
        await self.monitoring_system.stop_monitoring()

        # Cancel background tasks
        for task in self._background_tasks:
            task.cancel()

        await asyncio.gather(*self._background_tasks, return_exceptions=True)
        self._background_tasks.clear()

        logger.info("AI Orchestrator stopped successfully")

    async def _system_monitoring_loop(self):
        """Continuous system monitoring loop"""
        while self._running:
            try:
                # Get current system state
                system_status = self.monitoring_system.get_system_status()

                # Check for alerts that need attention
                alerts = self.monitoring_system.alert_manager.get_active_alerts()

                # Process critical alerts
                critical_alerts = [
                    alert for alert in alerts
                    if alert.severity in [AlertSeverity.ERROR, AlertSeverity.CRITICAL]
                ]

                if critical_alerts:
                    await self._handle_critical_alerts(critical_alerts)

                # Emit system status event
                await self._emit_event("system_status_update", {
                    "status": system_status,
                    "alerts_count": len(alerts),
                    "critical_alerts": len(critical_alerts)
                })

                await asyncio.sleep(30)  # Check every 30 seconds

            except Exception as e:
                logger.error(f"Error in system monitoring loop: {e}")
                await asyncio.sleep(60)

    async def _handle_critical_alerts(self, alerts: List[Any]):
        """Handle critical system alerts"""
        try:
            for alert in alerts:
                # Check if we already have an operation for this alert
                existing_operation = None
                for op in self.operations.values():
                    if op.operation_type == "alert_response" and alert.id in str(op.parameters):
                        existing_operation = op
                        break

                if existing_operation:
                    continue  # Already handling this alert

                # Create operation to handle alert
                operation = SystemOperation(
                    id=f"alert_{alert.id}_{int(time.time())}",
                    operation_type="alert_response",
                    description=f"Handle {alert.severity.value} alert: {alert.message}",
                    parameters={
                        "alert_id": alert.id,
                        "alert_type": alert.alert_type,
                        "severity": alert.severity.value,
                        "message": alert.message,
                        "source": alert.source
                    },
                    priority=9 if alert.severity == AlertSeverity.CRITICAL else 7,
                    requires_approval=self.config.mode != OrchestratorMode.AUTONOMOUS
                )

                await self._create_operation(operation)

        except Exception as e:
            logger.error(f"Error handling critical alerts: {e}")

    async def _operation_processing_loop(self):
        """Process pending operations"""
        while self._running:
            try:
                # Get operations ready for processing
                ready_operations = [
                    op for op in self.operations.values()
                    if op.status == "approved" or (op.status == "pending" and not op.requires_approval)
                ]

                # Sort by priority
                ready_operations.sort(key=lambda op: op.priority, reverse=True)

                # Process operations within concurrency limit
                active_operations = [
                    op for op in self.operations.values()
                    if op.status == "executing"
                ]

                available_slots = self.config.max_concurrent_operations - len(active_operations)

                for operation in ready_operations[:available_slots]:
                    await self._execute_operation(operation)

                await asyncio.sleep(5)  # Check every 5 seconds

            except Exception as e:
                logger.error(f"Error in operation processing loop: {e}")
                await asyncio.sleep(10)

    async def _execute_operation(self, operation: SystemOperation):
        """Execute a system operation"""
        try:
            operation.status = "executing"
            operation.started_at = datetime.now()

            logger.info(f"Executing operation: {operation.id} - {operation.description}")

            # Execute based on operation type
            if operation.operation_type == "alert_response":
                result = await self._execute_alert_response(operation)
            elif operation.operation_type == "system_optimization":
                result = await self._execute_system_optimization(operation)
            elif operation.operation_type == "maintenance_task":
                result = await self._execute_maintenance_task(operation)
            elif operation.operation_type == "knowledge_update":
                result = await self._execute_knowledge_update(operation)
            else:
                result = {"error": f"Unknown operation type: {operation.operation_type}"}

            operation.result = result
            operation.completed_at = datetime.now()

            if result.get("success", False):
                operation.status = "completed"
                self.orchestrator_stats["completed_operations"] += 1
                logger.info(f"Completed operation: {operation.id}")
            else:
                operation.status = "failed"
                self.orchestrator_stats["failed_operations"] += 1
                logger.error(f"Failed operation: {operation.id} - {result.get('error', 'Unknown error')}")

            # Move to history
            self.operation_history.append(operation)
            if operation.id in self.operations:
                del self.operations[operation.id]

            # Emit operation completion event
            await self._emit_event("operation_completed", {
                "operation_id": operation.id,
                "status": operation.status,
                "result": result
            })

        except Exception as e:
            logger.error(f"Error executing operation {operation.id}: {e}")
            operation.status = "failed"
            operation.result = {"error": str(e)}
            operation.completed_at = datetime.now()

            self.orchestrator_stats["failed_operations"] += 1

            # Move to history
            self.operation_history.append(operation)
            if operation.id in self.operations:
                del self.operations[operation.id]

    async def _execute_alert_response(self, operation: SystemOperation) -> Dict[str, Any]:
        """Execute alert response operation"""
        try:
            alert_params = operation.parameters

            # Create decision context
            context = DecisionContext(
                system_state={
                    "alert": alert_params,
                    "current_system_status": self.monitoring_system.get_system_status()
                },
                performance_metrics=self._get_current_performance_metrics(),
                constraints={
                    "max_response_time": 300,  # 5 minutes
                    "safety_checks": self.config.safety_checks_enabled
                },
                objectives=["resolve_alert", "minimize_disruption", "prevent_recurrence"]
            )

            # Get AI decision
            decision = await self.decision_maker.make_decision(
                DecisionCategory.ERROR_RECOVERY, context
            )

            if decision.confidence_score < 0.5:
                return {
                    "success": False,
                    "error": "Insufficient confidence to respond to alert",
                    "confidence_score": decision.confidence_score
                }

            # Execute the recommended action
            action_result = await self._execute_ai_action(decision.action, decision.parameters)

            # Query knowledge base for similar incidents
            similar_incidents = await self._query_similar_incidents(alert_params)

            return {
                "success": action_result.get("success", False),
                "decision": {
                    "action": decision.action,
                    "reasoning": decision.reasoning,
                    "confidence": decision.confidence_score
                },
                "action_result": action_result,
                "similar_incidents": similar_incidents,
                "resolution_time": (operation.completed_at - operation.started_at).total_seconds() if operation.completed_at else None
            }

        except Exception as e:
            logger.error(f"Error executing alert response: {e}")
            return {"success": False, "error": str(e)}

    async def _execute_system_optimization(self, operation: SystemOperation) -> Dict[str, Any]:
        """Execute system optimization operation"""
        try:
            # Use AI system manager to perform optimization
            success = await self.system_manager.force_trigger_policy("High CPU Usage Optimization")

            return {
                "success": success,
                "optimization_type": "performance",
                "triggered_by": "ai_orchestrator",
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error executing system optimization: {e}")
            return {"success": False, "error": str(e)}

    async def _execute_maintenance_task(self, operation: SystemOperation) -> Dict[str, Any]:
        """Execute maintenance task operation"""
        try:
            # Use AI system manager to perform maintenance
            success = await self.system_manager.force_trigger_policy("Predictive Maintenance")

            return {
                "success": success,
                "maintenance_type": "predictive",
                "triggered_by": "ai_orchestrator",
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error executing maintenance task: {e}")
            return {"success": False, "error": str(e)}

    async def _execute_knowledge_update(self, operation: SystemOperation) -> Dict[str, Any]:
        """Execute knowledge update operation"""
        try:
            # Extract knowledge from operation parameters
            knowledge_data = operation.parameters.get("knowledge", {})

            # Create knowledge entry
            entry = KnowledgeEntry(
                category=KnowledgeCategory.SYSTEM_HEALTH_MONITORING,
                title=knowledge_data.get("title", "System Learning"),
                content=knowledge_data.get("content", ""),
                tags=knowledge_data.get("tags", []),
                metadata={
                    "source": "ai_orchestrator",
                    "operation_id": operation.id,
                    "timestamp": datetime.now().isoformat()
                }
            )

            # Add to knowledge base
            entry_id = self.knowledge_base.add_knowledge(entry)

            return {
                "success": True,
                "entry_id": entry_id,
                "knowledge_type": entry.category.value,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error executing knowledge update: {e}")
            return {"success": False, "error": str(e)}

    async def _execute_ai_action(self, action: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute AI-recommended action"""
        try:
            # Map action to appropriate command
            command_map = {
                "restart_service": AICommandType.SERVICE_CONTROL,
                "optimize_system": AICommandType.PERFORMANCE_OPTIMIZATION,
                "check_health": AICommandType.HEALTH_MANAGEMENT,
                "manage_resources": AICommandType.RESOURCE_MANAGEMENT,
                "recover_error": AICommandType.ERROR_RECOVERY
            }

            command_type = command_map.get(action)
            if not command_type:
                return {"success": False, "error": f"Unknown action: {action}"}

            # Create and execute command
            command = AICommand(
                command_type=command_type,
                parameters=parameters
            )

            result = await self.ai_controller.process_command(command)
            return {"success": result.success, "result": result.result}

        except Exception as e:
            logger.error(f"Error executing AI action: {e}")
            return {"success": False, "error": str(e)}

    async def _query_similar_incidents(self, alert_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Query knowledge base for similar incidents"""
        try:
            query = KnowledgeQuery(
                query_text=f"Alert: {alert_params.get('message', '')}",
                category=KnowledgeCategory.ERROR_RECOVERY,
                limit=5
            )

            search_result = self.knowledge_base.search_knowledge(query)
            self.orchestrator_stats["knowledge_base_queries"] += 1

            return [
                {
                    "entry_id": entry.id,
                    "title": entry.title,
                    "relevance_score": score,
                    "content_preview": entry.content[:200] + "..." if len(entry.content) > 200 else entry.content
                }
                for entry, score in search_result.entries
            ]

        except Exception as e:
            logger.error(f"Error querying similar incidents: {e}")
            return []

    async def _decision_making_loop(self):
        """Continuous decision making loop"""
        while self._running:
            try:
                # Analyze current system state
                system_status = self.monitoring_system.get_system_status()

                # Check if any decisions need to be made
                if await self._should_make_decision(system_status):
                    await self._make_system_decision(system_status)

                await asyncio.sleep(60)  # Check every minute

            except Exception as e:
                logger.error(f"Error in decision making loop: {e}")
                await asyncio.sleep(30)

    async def _should_make_decision(self, system_status: Dict[str, Any]) -> bool:
        """Determine if a decision should be made"""
        try:
            # Check performance score
            performance_score = system_status.get("performance_score", 1.0)
            if performance_score < 0.6:
                return True

            # Check error count
            error_count = len(self.monitoring_system.alert_manager.alerts.get(
                AlertSeverity.ERROR, []))
            if error_count > 3:
                return True

            # Check resource usage
            metrics = self.monitoring_system.metrics_collector.get_current_metrics()
            if metrics.get("memory_percent", 0) > 90:
                return True
            if metrics.get("cpu_percent", 0) > 85:
                return True

            return False

        except Exception as e:
            logger.error(f"Error checking if decision should be made: {e}")
            return False

    async def _make_system_decision(self, system_status: Dict[str, Any]):
        """Make a system decision"""
        try:
            # Create decision context
            context = DecisionContext(
                system_state=system_status,
                performance_metrics=self._get_current_performance_metrics(),
                constraints={
                    "autonomy_level": self.config.autonomy_level,
                    "safety_checks": self.config.safety_checks_enabled
                },
                objectives=["system_optimization", "error_prevention", "performance_improvement"]
            )

            # Get AI decision
            decision = await self.decision_maker.make_decision(
                DecisionCategory.SYSTEM_MANAGEMENT, context
            )

            if decision.confidence_score >= self.config.autonomy_level:
                # Create operation for the decision
                operation = SystemOperation(
                    id=f"decision_{int(time.time())}",
                    operation_type="system_optimization",
                    description=f"AI decision: {decision.action}",
                    parameters=decision.parameters,
                    priority=8,
                    requires_approval=self.config.mode == OrchestratorMode.SUPERVISED,
                    confidence_score=decision.confidence_score
                )

                await self._create_operation(operation)
                self.orchestrator_stats["autonomous_operations"] += 1

            else:
                logger.info(f"AI decision confidence too low: {decision.confidence_score:.2f}")

        except Exception as e:
            logger.error(f"Error making system decision: {e}")

    def _get_current_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        return {
            "success_rate": self.orchestrator_stats["success_rate"],
            "average_decision_time": self.orchestrator_stats["average_decision_time"],
            "total_operations": self.orchestrator_stats["total_operations"],
            "active_operations": len([op for op in self.operations.values() if op.status == "executing"])
        }

    async def _learning_loop(self):
        """Continuous learning and improvement loop"""
        while self._running:
            try:
                if not self.config.learning_enabled:
                    await asyncio.sleep(600)
                    continue

                # Analyze recent operations for learning
                if len(self.operation_history) >= 10:
                    await self._learn_from_operations()

                await asyncio.sleep(1800)  # Check every 30 minutes

            except Exception as e:
                logger.error(f"Error in learning loop: {e}")
                await asyncio.sleep(60)

    async def _learn_from_operations(self):
        """Learn from completed operations"""
        try:
            # Analyze recent operations
            recent_operations = self.operation_history[-20:]

            # Calculate success rate
            successful_ops = [op for op in recent_operations if op.status == "completed"]
            success_rate = len(successful_ops) / len(recent_operations) if recent_operations else 0

            self.orchestrator_stats["success_rate"] = success_rate

            # Adapt autonomy level based on success rate
            if success_rate > 0.9:
                self.config.autonomy_level = min(1.0, self.config.autonomy_level + 0.02)
            elif success_rate < 0.6:
                self.config.autonomy_level = max(0.3, self.config.autonomy_level - 0.02)

            # Learn from failures
            failed_ops = [op for op in recent_operations if op.status == "failed"]
            for op in failed_ops:
                await self._learn_from_failure(op)

            logger.info(f"Updated autonomy level to {self.config.autonomy_level:.2f} based on success rate {success_rate:.2f}")

        except Exception as e:
            logger.error(f"Error learning from operations: {e}")

    async def _learn_from_failure(self, operation: SystemOperation):
        """Learn from operation failures"""
        try:
            # Create knowledge entry from failure
            error_info = operation.result.get("error", "Unknown error") if operation.result else "Unknown error"

            knowledge_content = f"""
Failure Analysis:
Operation: {operation.description}
Type: {operation.operation_type}
Error: {error_info}
Timestamp: {operation.created_at}
Parameters: {json.dumps(operation.parameters, indent=2)}

Lessons Learned:
- This type of operation failed and may need different approach
- Consider alternative methods or additional safeguards
- Review operation parameters for future attempts

Recommendations:
- Validate system state before attempting similar operations
- Consider implementing additional error handling
- Review operation parameters and adjust approach
"""

            entry = KnowledgeEntry(
                category=KnowledgeCategory.TROUBLESHOOTING,
                title=f"Failure Analysis: {operation.operation_type}",
                content=knowledge_content,
                tags=["failure_analysis", "learning", "autonomous_system"],
                metadata={
                    "operation_id": operation.id,
                    "failure_timestamp": operation.completed_at.isoformat() if operation.completed_at else None,
                    "confidence_score": operation.confidence_score,
                    "priority": operation.priority
                }
            )

            self.knowledge_base.add_knowledge(entry)

        except Exception as e:
            logger.error(f"Error learning from failure: {e}")

    async def _health_check_loop(self):
        """Periodic health check loop"""
        while self._running:
            try:
                # Perform comprehensive health check
                health_result = await self._perform_health_check()

                # Create operation if issues found
                if not health_result.get("healthy", True):
                    operation = SystemOperation(
                        id=f"health_check_{int(time.time())}",
                        operation_type="maintenance_task",
                        description="System health maintenance",
                        parameters=health_result.get("issues", {}),
                        priority=6,
                        requires_approval=self.config.mode == OrchestratorMode.MANUAL
                    )

                    await self._create_operation(operation)

                await asyncio.sleep(3600)  # Check every hour

            except Exception as e:
                logger.error(f"Error in health check loop: {e}")
                await asyncio.sleep(300)

    async def _perform_health_check(self) -> Dict[str, Any]:
        """Perform comprehensive system health check"""
        try:
            # Get system status
            system_status = self.monitoring_system.get_system_status()

            # Get active alerts
            alerts = self.monitoring_system.alert_manager.get_active_alerts()

            # Get metrics
            metrics = self.monitoring_system.metrics_collector.get_current_metrics()

            # Check for issues
            issues = {}

            # Check resource usage
            if metrics.get("memory_percent", 0) > 85:
                issues["high_memory"] = metrics.get("memory_percent")

            if metrics.get("cpu_percent", 0) > 80:
                issues["high_cpu"] = metrics.get("cpu_percent")

            # Check for critical alerts
            critical_alerts = [alert for alert in alerts if alert.severity == AlertSeverity.CRITICAL]
            if critical_alerts:
                issues["critical_alerts"] = len(critical_alerts)

            # Check performance score
            if system_status.get("performance_score", 1.0) < 0.7:
                issues["low_performance"] = system_status.get("performance_score")

            return {
                "healthy": len(issues) == 0,
                "issues": issues,
                "system_status": system_status,
                "metrics": metrics,
                "alerts_count": len(alerts)
            }

        except Exception as e:
            logger.error(f"Error performing health check: {e}")
            return {"healthy": False, "error": str(e)}

    async def _create_operation(self, operation: SystemOperation):
        """Create and track a new operation"""
        try:
            self.operations[operation.id] = operation
            self.orchestrator_stats["total_operations"] += 1

            # Check if operation requires approval
            if operation.requires_approval:
                self.pending_approvals.append(operation)
                await self._emit_event("operation_approval_required", {
                    "operation_id": operation.id,
                    "description": operation.description,
                    "priority": operation.priority,
                    "confidence_score": operation.confidence_score
                })
            else:
                operation.status = "approved"

            logger.info(f"Created operation: {operation.id} - {operation.description}")

        except Exception as e:
            logger.error(f"Error creating operation: {e}")

    async def approve_operation(self, operation_id: str, approved_by: str = "user") -> bool:
        """Approve a pending operation"""
        try:
            if operation_id not in self.operations:
                logger.error(f"Operation not found: {operation_id}")
                return False

            operation = self.operations[operation_id]
            if operation.status != "pending":
                logger.error(f"Operation not pending approval: {operation_id}")
                return False

            operation.status = "approved"
            operation.approved_by = approved_by

            # Remove from pending approvals
            self.pending_approvals = [op for op in self.pending_approvals if op.id != operation_id]

            await self._emit_event("operation_approved", {
                "operation_id": operation_id,
                "approved_by": approved_by
            })

            logger.info(f"Approved operation: {operation_id}")
            return True

        except Exception as e:
            logger.error(f"Error approving operation: {e}")
            return False

    async def reject_operation(self, operation_id: str, reason: str = "Rejected by user") -> bool:
        """Reject a pending operation"""
        try:
            if operation_id not in self.operations:
                logger.error(f"Operation not found: {operation_id}")
                return False

            operation = self.operations[operation_id]
            if operation.status != "pending":
                logger.error(f"Operation not pending approval: {operation_id}")
                return False

            operation.status = "cancelled"
            operation.result = {"cancelled": True, "reason": reason}

            # Remove from pending approvals
            self.pending_approvals = [op for op in self.pending_approvals if op.id != operation_id]

            await self._emit_event("operation_rejected", {
                "operation_id": operation_id,
                "reason": reason
            })

            logger.info(f"Rejected operation: {operation_id} - {reason}")
            return True

        except Exception as e:
            logger.error(f"Error rejecting operation: {e}")
            return False

    async def _emit_event(self, event_type: str, event_data: Dict[str, Any]):
        """Emit an event to registered handlers"""
        try:
            if event_type in self.event_handlers:
                for handler in self.event_handlers[event_type]:
                    try:
                        if asyncio.iscoroutinefunction(handler):
                            await handler(event_data)
                        else:
                            handler(event_data)
                    except Exception as e:
                        logger.error(f"Error in event handler: {e}")

        except Exception as e:
            logger.error(f"Error emitting event: {e}")

    def add_event_handler(self, event_type: str, handler: Callable):
        """Add an event handler"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)

    def remove_event_handler(self, event_type: str, handler: Callable):
        """Remove an event handler"""
        if event_type in self.event_handlers:
            try:
                self.event_handlers[event_type].remove(handler)
            except ValueError:
                pass  # Handler not found

    async def request_operation(self, operation_type: str, description: str,
                              parameters: Dict[str, Any], priority: int = 5,
                              requires_approval: Optional[bool] = None) -> str:
        """Request a new operation"""
        try:
            operation_id = f"manual_{int(time.time())}"

            # Determine if approval is required
            if requires_approval is None:
                requires_approval = self.config.mode in [OrchestratorMode.MANUAL, OrchestratorMode.ASSISTED]

            operation = SystemOperation(
                id=operation_id,
                operation_type=operation_type,
                description=description,
                parameters=parameters,
                priority=priority,
                requires_approval=requires_approval
            )

            await self._create_operation(operation)
            return operation_id

        except Exception as e:
            logger.error(f"Error requesting operation: {e}")
            raise

    def get_orchestrator_status(self) -> Dict[str, Any]:
        """Get current orchestrator status"""
        return {
            "running": self._running,
            "mode": self.config.mode.value,
            "autonomy_level": self.config.autonomy_level,
            "stats": self.orchestrator_stats,
            "active_operations": len(self.operations),
            "pending_approvals": len(self.pending_approvals),
            "operation_history": len(self.operation_history),
            "system_manager_status": self.system_manager.get_management_status(),
            "monitoring_status": self.monitoring_system.get_system_status()
        }

    def get_pending_operations(self) -> List[Dict[str, Any]]:
        """Get pending operations requiring approval"""
        return [
            {
                "id": op.id,
                "type": op.operation_type,
                "description": op.description,
                "priority": op.priority,
                "confidence_score": op.confidence_score,
                "created_at": op.created_at.isoformat()
            }
            for op in self.pending_approvals
        ]

    def get_recent_operations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent operations"""
        recent_ops = sorted(
            self.operation_history[-limit:],
            key=lambda op: op.completed_at or op.created_at,
            reverse=True
        )

        return [
            {
                "id": op.id,
                "type": op.operation_type,
                "description": op.description,
                "status": op.status,
                "priority": op.priority,
                "confidence_score": op.confidence_score,
                "created_at": op.created_at.isoformat(),
                "started_at": op.started_at.isoformat() if op.started_at else None,
                "completed_at": op.completed_at.isoformat() if op.completed_at else None,
                "duration": (op.completed_at - op.started_at).total_seconds() if op.completed_at and op.started_at else None,
                "result": op.result
            }
            for op in recent_ops
        ]

    async def generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate comprehensive system report"""
        try:
            # Get orchestrator status
            orchestrator_status = self.get_orchestrator_status()

            # Get system manager report
            manager_report = await self.system_manager.generate_management_report()

            # Get knowledge base stats
            kb_stats = self.knowledge_base.get_usage_stats()

            # Get monitoring system status
            monitoring_status = self.monitoring_system.get_system_status()

            # Calculate overall system health
            overall_health = self._calculate_overall_health(
                orchestrator_status,
                manager_report,
                monitoring_status
            )

            return {
                "report_timestamp": datetime.now().isoformat(),
                "overall_health": overall_health,
                "orchestrator_status": orchestrator_status,
                "system_management": manager_report,
                "knowledge_base": kb_stats,
                "monitoring_system": monitoring_status,
                "recommendations": self._generate_recommendations(
                    orchestrator_status,
                    manager_report,
                    monitoring_status
                )
            }

        except Exception as e:
            logger.error(f"Error generating comprehensive report: {e}")
            return {"error": str(e)}

    def _calculate_overall_health(self, orchestrator_status: Dict[str, Any],
                                manager_report: Dict[str, Any],
                                monitoring_status: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall system health score"""
        try:
            # Extract health indicators
            orchestrator_success_rate = orchestrator_status.get("stats", {}).get("success_rate", 0.0)
            manager_success_rate = manager_report.get("management_statistics", {}).get("success_rate", 0.0)
            monitoring_health_score = monitoring_status.get("health_score", 0.0)

            # Calculate weighted average
            weights = {"orchestrator": 0.4, "manager": 0.4, "monitoring": 0.2}
            overall_score = (
                weights["orchestrator"] * orchestrator_success_rate +
                weights["manager"] * manager_success_rate +
                weights["monitoring"] * monitoring_health_score
            )

            # Determine health status
            if overall_score >= 0.9:
                status = "excellent"
            elif overall_score >= 0.7:
                status = "good"
            elif overall_score >= 0.5:
                status = "fair"
            else:
                status = "poor"

            return {
                "score": overall_score,
                "status": status,
                "components": {
                    "orchestrator": orchestrator_success_rate,
                    "system_manager": manager_success_rate,
                    "monitoring": monitoring_health_score
                }
            }

        except Exception as e:
            logger.error(f"Error calculating overall health: {e}")
            return {"score": 0.0, "status": "error"}

    def _generate_recommendations(self, orchestrator_status: Dict[str, Any],
                                manager_report: Dict[str, Any],
                                monitoring_status: Dict[str, Any]) -> List[str]:
        """Generate system recommendations"""
        recommendations = []

        try:
            # Check orchestrator performance
            orchestrator_success_rate = orchestrator_status.get("stats", {}).get("success_rate", 0.0)
            if orchestrator_success_rate < 0.7:
                recommendations.append("Consider adjusting AI decision confidence thresholds")

            # Check system manager performance
            manager_success_rate = manager_report.get("management_statistics", {}).get("success_rate", 0.0)
            if manager_success_rate < 0.7:
                recommendations.append("Review autonomous management policies and adjust parameters")

            # Check monitoring alerts
            alerts = monitoring_status.get("active_alerts", 0)
            if alerts > 5:
                recommendations.append("High number of active alerts - consider system maintenance")

            # Check resource usage
            metrics = monitoring_status.get("metrics", {})
            if metrics.get("memory_percent", 0) > 80:
                recommendations.append("High memory usage detected - consider optimization")

            if metrics.get("cpu_percent", 0) > 75:
                recommendations.append("High CPU usage detected - review running processes")

            # Check autonomy level
            autonomy_level = orchestrator_status.get("autonomy_level", 0.0)
            if autonomy_level > 0.8 and orchestrator_success_rate < 0.8:
                recommendations.append("Consider reducing autonomy level until success rate improves")

            return recommendations

        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return ["Error generating recommendations"]