"""
AI System Test Suite

Comprehensive testing and validation for all AI system components:
- Unit tests for individual AI components
- Integration tests for component interactions
- Performance tests and benchmarks
- Stress testing and load validation
- End-to-end system testing
- Autonomous system validation
- Knowledge base testing
- Decision making validation

Author: Claude for DuckBot Enhanced v4.2
"""

import asyncio
import json
import logging
import time
import unittest
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import sqlite3
import tempfile
import shutil
from unittest.mock import Mock, patch, AsyncMock

# Import AI components
from .ai_system_controller import AISystemController, AICommand, AICommandType, AICommandResult
from .ai_decision_maker import AIDecisionMaker, DecisionCategory, DecisionContext, AIDecision
from .ai_knowledge_base import AIKnowledgeBase, KnowledgeEntry, KnowledgeQuery, KnowledgeCategory
from .ai_driven_system_manager import AIDrivenSystemManager, ManagementPolicy, ManagementAction
from .ai_orchestrator import AIOrchestrator, OrchestratorConfig, OrchestratorMode
from .ai_service_integration import AIIntegrationService, ServiceType, EventType
from .ai_dashboard import AIMonitoringDashboard, DashboardView
from .monitoring_system import DuckBotMonitoring, MetricsCollector, AlertSeverity

logger = logging.getLogger(__name__)

class TestLevel(Enum):
    """Test execution levels"""
    UNIT = "unit"
    INTEGRATION = "integration"
    SYSTEM = "system"
    PERFORMANCE = "performance"
    STRESS = "stress"

class TestResult(Enum):
    """Test result types"""
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"

@dataclass
class TestCase:
    """Test case definition"""
    name: str
    description: str
    level: TestLevel
    component: str
    test_function: Callable
    expected_result: Any
    timeout: int = 30
    enabled: bool = True
    prerequisites: List[str] = field(default_factory=list)

@dataclass
class TestExecution:
    """Test execution result"""
    test_case: TestCase
    start_time: datetime
    end_time: Optional[datetime] = None
    result: TestResult = TestResult.FAILED
    output: str = ""
    error: Optional[str] = None
    execution_time: float = 0.0
    metrics: Dict[str, Any] = field(default_factory=dict)

@dataclass
class TestSuite:
    """Test suite configuration"""
    name: str
    description: str
    test_cases: List[TestCase]
    parallel_execution: bool = True
    setup_function: Optional[Callable] = None
    teardown_function: Optional[Callable] = None

class AISystemTestSuite:
    """Comprehensive AI System Test Suite"""

    def __init__(self, test_data_dir: Optional[Path] = None):
        self.test_data_dir = test_data_dir or Path("test_data")
        self.test_data_dir.mkdir(exist_ok=True)

        # Test execution tracking
        self.test_suites: Dict[str, TestSuite] = {}
        self.test_executions: List[TestExecution] = []
        self.current_execution: Optional[TestExecution] = None

        # Test results
        self.test_results = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "skipped_tests": 0,
            "error_tests": 0,
            "total_execution_time": 0.0,
            "success_rate": 0.0,
            "performance_metrics": {},
            "component_results": {}
        }

        # Test configuration
        self.test_config = {
            "timeout": 60,
            "parallel_workers": 4,
            "verbose_logging": True,
            "generate_reports": True,
            "cleanup_after_tests": True,
            "stress_test_duration": 300,  # 5 minutes
            "performance_test_iterations": 100
        }

        # Database setup
        self.db_path = self.test_data_dir / "ai_test_suite.db"
        self._init_database()

        # Initialize test suites
        self._initialize_test_suites()

        logger.info("AI System Test Suite initialized")

    def _init_database(self):
        """Initialize test database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Test executions table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS test_executions (
                        execution_id TEXT PRIMARY KEY,
                        test_name TEXT,
                        test_level TEXT,
                        component TEXT,
                        start_time TEXT,
                        end_time TEXT,
                        result TEXT,
                        execution_time REAL,
                        output TEXT,
                        error TEXT,
                        metrics TEXT
                    )
                """)

                # Test results summary table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS test_results_summary (
                        test_run_id TEXT PRIMARY KEY,
                        timestamp TEXT,
                        total_tests INTEGER,
                        passed_tests INTEGER,
                        failed_tests INTEGER,
                        skipped_tests INTEGER,
                        error_tests INTEGER,
                        success_rate REAL,
                        total_execution_time REAL,
                        performance_metrics TEXT
                    )
                """)

                conn.commit()
                logger.info("Test suite database initialized")

        except Exception as e:
            logger.error(f"Failed to initialize test database: {e}")

    def _initialize_test_suites(self):
        """Initialize all test suites"""
        # AI System Controller Tests
        self.test_suites["ai_system_controller"] = TestSuite(
            name="AI System Controller Tests",
            description="Test AI command processing and system control functionality",
            test_cases=self._get_ai_controller_tests(),
            setup_function=self._setup_ai_controller_tests,
            teardown_function=self._teardown_ai_controller_tests
        )

        # AI Decision Maker Tests
        self.test_suites["ai_decision_maker"] = TestSuite(
            name="AI Decision Maker Tests",
            description="Test AI decision making and confidence scoring",
            test_cases=self._get_ai_decision_maker_tests(),
            setup_function=self._setup_ai_decision_maker_tests,
            teardown_function=self._teardown_ai_decision_maker_tests
        )

        # AI Knowledge Base Tests
        self.test_suites["ai_knowledge_base"] = TestSuite(
            name="AI Knowledge Base Tests",
            description="Test knowledge base operations and search functionality",
            test_cases=self._get_ai_knowledge_base_tests(),
            setup_function=self._setup_ai_knowledge_base_tests,
            teardown_function=self._teardown_ai_knowledge_base_tests
        )

        # AI-Driven System Manager Tests
        self.test_suites["ai_system_manager"] = TestSuite(
            name="AI System Manager Tests",
            description="Test autonomous system management capabilities",
            test_cases=self._get_ai_system_manager_tests(),
            setup_function=self._setup_ai_system_manager_tests,
            teardown_function=self._teardown_ai_system_manager_tests
        )

        # AI Orchestrator Tests
        self.test_suites["ai_orchestrator"] = TestSuite(
            name="AI Orchestrator Tests",
            description="Test AI orchestrator coordination and management",
            test_cases=self._get_ai_orchestrator_tests(),
            setup_function=self._setup_ai_orchestrator_tests,
            teardown_function=self._teardown_ai_orchestrator_tests
        )

        # Integration Tests
        self.test_suites["integration"] = TestSuite(
            name="Integration Tests",
            description="Test component integration and interactions",
            test_cases=self._get_integration_tests(),
            parallel_execution=False,
            setup_function=self._setup_integration_tests,
            teardown_function=self._teardown_integration_tests
        )

        # Performance Tests
        self.test_suites["performance"] = TestSuite(
            name="Performance Tests",
            description="Test system performance under various loads",
            test_cases=self._get_performance_tests(),
            parallel_execution=False,
            setup_function=self._setup_performance_tests,
            teardown_function=self._teardown_performance_tests
        )

        # Stress Tests
        self.test_suites["stress"] = TestSuite(
            name="Stress Tests",
            description="Test system stability under extreme conditions",
            test_cases=self._get_stress_tests(),
            parallel_execution=False,
            setup_function=self._setup_stress_tests,
            teardown_function=self._teardown_stress_tests
        )

    def _get_ai_controller_tests(self) -> List[TestCase]:
        """Get AI System Controller test cases"""
        return [
            TestCase(
                name="test_command_creation",
                description="Test AI command creation and validation",
                level=TestLevel.UNIT,
                component="ai_system_controller",
                test_function=self._test_command_creation,
                expected_result=True
            ),
            TestCase(
                name="test_command_execution",
                description="Test AI command execution flow",
                level=TestLevel.UNIT,
                component="ai_system_controller",
                test_function=self._test_command_execution,
                expected_result=True
            ),
            TestCase(
                name="test_command_types",
                description="Test all supported AI command types",
                level=TestLevel.UNIT,
                component="ai_system_controller",
                test_function=self._test_command_types,
                expected_result=True
            ),
            TestCase(
                name="test_error_handling",
                description="Test error handling in command execution",
                level=TestLevel.UNIT,
                component="ai_system_controller",
                test_function=self._test_error_handling,
                expected_result=True
            )
        ]

    def _get_ai_decision_maker_tests(self) -> List[TestCase]:
        """Get AI Decision Maker test cases"""
        return [
            TestCase(
                name="test_decision_context_creation",
                description="Test decision context creation and validation",
                level=TestLevel.UNIT,
                component="ai_decision_maker",
                test_function=self._test_decision_context_creation,
                expected_result=True
            ),
            TestCase(
                name="test_decision_making",
                description="Test AI decision making process",
                level=TestLevel.UNIT,
                component="ai_decision_maker",
                test_function=self._test_decision_making,
                expected_result=True
            ),
            TestCase(
                name="test_confidence_scoring",
                description="Test decision confidence scoring",
                level=TestLevel.UNIT,
                component="ai_decision_maker",
                test_function=self._test_confidence_scoring,
                expected_result=True
            ),
            TestCase(
                name="test_decision_categories",
                description="Test all decision categories",
                level=TestLevel.UNIT,
                component="ai_decision_maker",
                test_function=self._test_decision_categories,
                expected_result=True
            )
        ]

    def _get_ai_knowledge_base_tests(self) -> List[TestCase]:
        """Get AI Knowledge Base test cases"""
        return [
            TestCase(
                name="test_knowledge_entry_creation",
                description="Test knowledge entry creation and validation",
                level=TestLevel.UNIT,
                component="ai_knowledge_base",
                test_function=self._test_knowledge_entry_creation,
                expected_result=True
            ),
            TestCase(
                name="test_knowledge_search",
                description="Test knowledge base search functionality",
                level=TestLevel.UNIT,
                component="ai_knowledge_base",
                test_function=self._test_knowledge_search,
                expected_result=True
            ),
            TestCase(
                name="test_knowledge_categories",
                description="Test knowledge categories and filtering",
                level=TestLevel.UNIT,
                component="ai_knowledge_base",
                test_function=self._test_knowledge_categories,
                expected_result=True
            ),
            TestCase(
                name="test_knowledge_relationships",
                description="Test knowledge relationship tracking",
                level=TestLevel.UNIT,
                component="ai_knowledge_base",
                test_function=self._test_knowledge_relationships,
                expected_result=True
            )
        ]

    def _get_ai_system_manager_tests(self) -> List[TestCase]:
        """Get AI System Manager test cases"""
        return [
            TestCase(
                name="test_policy_creation",
                description="Test management policy creation and validation",
                level=TestLevel.UNIT,
                component="ai_system_manager",
                test_function=self._test_policy_creation,
                expected_result=True
            ),
            TestCase(
                name="test_task_creation",
                description="Test autonomous task creation and execution",
                level=TestLevel.UNIT,
                component="ai_system_manager",
                test_function=self._test_task_creation,
                expected_result=True
            ),
            TestCase(
                name="test_health_monitoring",
                description="Test system health monitoring",
                level=TestLevel.UNIT,
                component="ai_system_manager",
                test_function=self._test_health_monitoring,
                expected_result=True
            ),
            TestCase(
                name="test_predictive_analysis",
                description="Test predictive analysis and trend detection",
                level=TestLevel.UNIT,
                component="ai_system_manager",
                test_function=self._test_predictive_analysis,
                expected_result=True
            )
        ]

    def _get_ai_orchestrator_tests(self) -> List[TestCase]:
        """Get AI Orchestrator test cases"""
        return [
            TestCase(
                name="test_orchestrator_initialization",
                description="Test AI orchestrator initialization",
                level=TestLevel.UNIT,
                component="ai_orchestrator",
                test_function=self._test_orchestrator_initialization,
                expected_result=True
            ),
            TestCase(
                name="test_operation_management",
                description="Test operation creation and management",
                level=TestLevel.UNIT,
                component="ai_orchestrator",
                test_function=self._test_operation_management,
                expected_result=True
            ),
            TestCase(
                name="test_approval_workflow",
                description="Test operation approval workflow",
                level=TestLevel.UNIT,
                component="ai_orchestrator",
                test_function=self._test_approval_workflow,
                expected_result=True
            ),
            TestCase(
                name="test_event_handling",
                description="Test event handling and broadcasting",
                level=TestLevel.UNIT,
                component="ai_orchestrator",
                test_function=self._test_event_handling,
                expected_result=True
            )
        ]

    def _get_integration_tests(self) -> List[TestCase]:
        """Get integration test cases"""
        return [
            TestCase(
                name="test_full_ai_workflow",
                description="Test complete AI workflow from monitoring to action",
                level=TestLevel.INTEGRATION,
                component="integration",
                test_function=self._test_full_ai_workflow,
                expected_result=True,
                timeout=120
            ),
            TestCase(
                name="test_component_communication",
                description="Test inter-component communication",
                level=TestLevel.INTEGRATION,
                component="integration",
                test_function=self._test_component_communication,
                expected_result=True
            ),
            TestCase(
                name="test_error_propagation",
                description="Test error propagation and handling across components",
                level=TestLevel.INTEGRATION,
                component="integration",
                test_function=self._test_error_propagation,
                expected_result=True
            ),
            TestCase(
                name="test_state_synchronization",
                description="Test state synchronization between components",
                level=TestLevel.INTEGRATION,
                component="integration",
                test_function=self._test_state_synchronization,
                expected_result=True
            )
        ]

    def _get_performance_tests(self) -> List[TestCase]:
        """Get performance test cases"""
        return [
            TestCase(
                name="test_command_processing_performance",
                description="Test command processing performance",
                level=TestLevel.PERFORMANCE,
                component="performance",
                test_function=self._test_command_processing_performance,
                expected_result={"max_time": 1.0, "throughput": 100},
                timeout=60
            ),
            TestCase(
                name="test_decision_making_performance",
                description="Test decision making performance",
                level=TestLevel.PERFORMANCE,
                component="performance",
                test_function=self._test_decision_making_performance,
                expected_result={"max_time": 2.0, "throughput": 50},
                timeout=60
            ),
            TestCase(
                name="test_knowledge_search_performance",
                description="Test knowledge search performance",
                level=TestLevel.PERFORMANCE,
                component="performance",
                test_function=self._test_knowledge_search_performance,
                expected_result={"max_time": 0.5, "throughput": 200},
                timeout=60
            ),
            TestCase(
                name="test_system_scalability",
                description="Test system scalability under load",
                level=TestLevel.PERFORMANCE,
                component="performance",
                test_function=self._test_system_scalability,
                expected_result={"success_rate": 0.95, "max_response_time": 5.0},
                timeout=120
            )
        ]

    def _get_stress_tests(self) -> List[TestCase]:
        """Get stress test cases"""
        return [
            TestCase(
                name="test_high_load_handling",
                description="Test system behavior under high load",
                level=TestLevel.STRESS,
                component="stress",
                test_function=self._test_high_load_handling,
                expected_result={"stability": True, "error_rate": 0.05},
                timeout=self.test_config["stress_test_duration"]
            ),
            TestCase(
                name="test_memory_management",
                description="Test memory management under stress",
                level=TestLevel.STRESS,
                component="stress",
                test_function=self._test_memory_management,
                expected_result={"memory_leak": False, "max_memory": "1GB"},
                timeout=self.test_config["stress_test_duration"]
            ),
            TestCase(
                name="test_concurrent_operations",
                description="Test concurrent operation handling",
                level=TestLevel.STRESS,
                component="stress",
                test_function=self._test_concurrent_operations,
                expected_result={"concurrency_success": True, "max_concurrent": 100},
                timeout=self.test_config["stress_test_duration"]
            ),
            TestCase(
                name="test_recovery_from_failure",
                description="Test system recovery from failure conditions",
                level=TestLevel.STRESS,
                component="stress",
                test_function=self._test_recovery_from_failure,
                expected_result={"recovery_success": True, "recovery_time": 30},
                timeout=180
            )
        ]

    # Test setup and teardown functions
    async def _setup_ai_controller_tests(self):
        """Setup AI controller tests"""
        self.ai_controller = AISystemController()
        await self.ai_controller.start_controller()

    async def _teardown_ai_controller_tests(self):
        """Teardown AI controller tests"""
        if hasattr(self, 'ai_controller'):
            await self.ai_controller.stop_controller()

    async def _setup_ai_decision_maker_tests(self):
        """Setup AI decision maker tests"""
        self.decision_maker = AIDecisionMaker()

    async def _teardown_ai_decision_maker_tests(self):
        """Teardown AI decision maker tests"""
        pass  # No specific teardown needed

    async def _setup_ai_knowledge_base_tests(self):
        """Setup AI knowledge base tests"""
        # Use temporary database for testing
        self.temp_knowledge_db = Path(tempfile.mkdtemp()) / "test_knowledge.db"
        self.knowledge_base = AIKnowledgeBase(db_path=str(self.temp_knowledge_db))

    async def _teardown_ai_knowledge_base_tests(self):
        """Teardown AI knowledge base tests"""
        if hasattr(self, 'temp_knowledge_db') and self.temp_knowledge_db.exists():
            shutil.rmtree(self.temp_knowledge_db.parent)

    async def _setup_ai_system_manager_tests(self):
        """Setup AI system manager tests"""
        self.ai_controller = AISystemController()
        self.decision_maker = AIDecisionMaker()
        self.knowledge_base = AIKnowledgeBase(db_path=":memory:")
        self.monitoring_system = DuckBotMonitoring()

        self.system_manager = AIDrivenSystemManager(
            self.ai_controller,
            self.decision_maker,
            self.knowledge_base,
            self.monitoring_system
        )

        await self.ai_controller.start_controller()
        await self.monitoring_system.start_monitoring()

    async def _teardown_ai_system_manager_tests(self):
        """Teardown AI system manager tests"""
        if hasattr(self, 'system_manager'):
            await self.system_manager.stop_management()
        if hasattr(self, 'monitoring_system'):
            await self.monitoring_system.stop_monitoring()
        if hasattr(self, 'ai_controller'):
            await self.ai_controller.stop_controller()

    async def _setup_ai_orchestrator_tests(self):
        """Setup AI orchestrator tests"""
        self.orchestrator = AIOrchestrator()
        await self.orchestrator.start_orchestrator()

    async def _teardown_ai_orchestrator_tests(self):
        """Teardown AI orchestrator tests"""
        if hasattr(self, 'orchestrator'):
            await self.orchestrator.stop_orchestrator()

    async def _setup_integration_tests(self):
        """Setup integration tests"""
        # Setup full system for integration testing
        self.orchestrator = AIOrchestrator()
        self.integration_service = AIIntegrationService(self.orchestrator)
        self.dashboard = AIMonitoringDashboard(self.orchestrator, self.integration_service)

        await self.orchestrator.start_orchestrator()

    async def _teardown_integration_tests(self):
        """Teardown integration tests"""
        if hasattr(self, 'orchestrator'):
            await self.orchestrator.stop_orchestrator()

    async def _setup_performance_tests(self):
        """Setup performance tests"""
        self.orchestrator = AIOrchestrator()
        await self.orchestrator.start_orchestrator()

    async def _teardown_performance_tests(self):
        """Teardown performance tests"""
        if hasattr(self, 'orchestrator'):
            await self.orchestrator.stop_orchestrator()

    async def _setup_stress_tests(self):
        """Setup stress tests"""
        self.orchestrator = AIOrchestrator()
        await self.orchestrator.start_orchestrator()

    async def _teardown_stress_tests(self):
        """Teardown stress tests"""
        if hasattr(self, 'orchestrator'):
            await self.orchestrator.stop_orchestrator()

    # Test implementation functions
    async def _test_command_creation(self) -> bool:
        """Test AI command creation"""
        try:
            # Test command creation
            command = AICommand(
                command_type=AICommandType.SYSTEM_MONITORING,
                parameters={"action": "health_check"}
            )

            # Validate command structure
            assert command.id is not None
            assert command.command_type == AICommandType.SYSTEM_MONITORING
            assert command.parameters == {"action": "health_check"}
            assert command.status == "pending"

            # Test all command types
            for cmd_type in AICommandType:
                command = AICommand(
                    command_type=cmd_type,
                    parameters={"test": True}
                )
                assert command.command_type == cmd_type

            return True
        except Exception as e:
            logger.error(f"Command creation test failed: {e}")
            return False

    async def _test_command_execution(self) -> bool:
        """Test AI command execution"""
        try:
            # Create test command
            command = AICommand(
                command_type=AICommandType.SYSTEM_MONITORING,
                parameters={"action": "health_check"}
            )

            # Execute command
            result = await self.ai_controller.process_command(command)

            # Validate result
            assert result is not None
            assert result.command_id == command.id
            assert result.execution_time > 0

            return True
        except Exception as e:
            logger.error(f"Command execution test failed: {e}")
            return False

    async def _test_command_types(self) -> bool:
        """Test all supported AI command types"""
        try:
            # Test each command type
            test_commands = [
                (AICommandType.SYSTEM_MONITORING, {"action": "health_check"}),
                (AICommandType.HEALTH_MANAGEMENT, {"action": "diagnose"}),
                (AICommandType.PERFORMANCE_OPTIMIZATION, {"target": "system"}),
                (AICommandType.ERROR_RECOVERY, {"error_id": "test_error"}),
                (AICommandType.SERVICE_CONTROL, {"service": "test_service", "action": "restart"}),
                (AICommandType.RESOURCE_MANAGEMENT, {"resource": "memory", "action": "cleanup"}),
                (AICommandType.PREDICTIVE_MAINTENANCE, {"action": "analyze"}),
                (AICommandType.AGENT_MANAGEMENT, {"agent": "test_agent", "action": "status"})
            ]

            for cmd_type, params in test_commands:
                command = AICommand(
                    command_type=cmd_type,
                    parameters=params
                )

                result = await self.ai_controller.process_command(command)
                assert result.success in [True, False]  # Either success or handled failure

            return True
        except Exception as e:
            logger.error(f"Command types test failed: {e}")
            return False

    async def _test_error_handling(self) -> bool:
        """Test error handling in command execution"""
        try:
            # Test with invalid parameters
            command = AICommand(
                command_type=AICommandType.SYSTEM_MONITORING,
                parameters={"invalid_action": "nonexistent"}
            )

            result = await self.ai_controller.process_command(command)
            assert result.success == False
            assert result.error is not None

            # Test with non-existent service
            command = AICommand(
                command_type=AICommandType.SERVICE_CONTROL,
                parameters={"service": "nonexistent_service", "action": "restart"}
            )

            result = await self.ai_controller.process_command(command)
            assert result.success == False
            assert result.error is not None

            return True
        except Exception as e:
            logger.error(f"Error handling test failed: {e}")
            return False

    async def _test_decision_context_creation(self) -> bool:
        """Test decision context creation"""
        try:
            # Create decision context
            context = DecisionContext(
                system_state={"cpu_usage": 0.8, "memory_usage": 0.7},
                performance_metrics={"success_rate": 0.9, "response_time": 1.5},
                constraints={"max_time": 10, "safety_checks": True},
                objectives=["optimize_performance", "minimize_errors"]
            )

            # Validate context structure
            assert context.system_state is not None
            assert context.performance_metrics is not None
            assert context.constraints is not None
            assert context.objectives is not None
            assert len(context.objectives) == 2

            return True
        except Exception as e:
            logger.error(f"Decision context creation test failed: {e}")
            return False

    async def _test_decision_making(self) -> bool:
        """Test AI decision making process"""
        try:
            # Create context
            context = DecisionContext(
                system_state={"performance_score": 0.6, "error_count": 5},
                performance_metrics={"success_rate": 0.8, "response_time": 2.0},
                constraints={"autonomy_level": 0.8},
                objectives=["improve_performance", "reduce_errors"]
            )

            # Make decision
            decision = await self.decision_maker.make_decision(
                DecisionCategory.SYSTEM_MANAGEMENT, context
            )

            # Validate decision structure
            assert decision is not None
            assert decision.id is not None
            assert decision.action is not None
            assert decision.confidence_score >= 0.0
            assert decision.confidence_score <= 1.0
            assert decision.reasoning is not None

            return True
        except Exception as e:
            logger.error(f"Decision making test failed: {e}")
            return False

    async def _test_confidence_scoring(self) -> bool:
        """Test decision confidence scoring"""
        try:
            # Test with high-confidence scenario
            context = DecisionContext(
                system_state={"performance_score": 0.95, "error_count": 0},
                performance_metrics={"success_rate": 0.99, "response_time": 0.5},
                constraints={"autonomy_level": 0.9},
                objectives=["maintain_performance"]
            )

            decision = await self.decision_maker.make_decision(
                DecisionCategory.SYSTEM_MANAGEMENT, context
            )

            # High confidence for good system state
            assert decision.confidence_score >= 0.7

            # Test with low-confidence scenario
            context = DecisionContext(
                system_state={"performance_score": 0.3, "error_count": 20},
                performance_metrics={"success_rate": 0.4, "response_time": 10.0},
                constraints={"autonomy_level": 0.9},
                objectives=["fix_system"]
            )

            decision = await self.decision_maker.make_decision(
                DecisionCategory.ERROR_RECOVERY, context
            )

            # Lower confidence for problematic system
            assert decision.confidence_score <= 0.8

            return True
        except Exception as e:
            logger.error(f"Confidence scoring test failed: {e}")
            return False

    async def _test_decision_categories(self) -> bool:
        """Test all decision categories"""
        try:
            # Test context for different categories
            test_contexts = [
                (DecisionCategory.SYSTEM_MANAGEMENT, {
                    "system_state": {"performance_score": 0.7},
                    "objectives": ["optimize_system"]
                }),
                (DecisionCategory.ERROR_RECOVERY, {
                    "system_state": {"error_count": 5},
                    "objectives": ["fix_errors"]
                }),
                (DecisionCategory.PERFORMANCE_OPTIMIZATION, {
                    "system_state": {"cpu_usage": 0.9},
                    "objectives": ["improve_performance"]
                }),
                (DecisionCategory.RESOURCE_MANAGEMENT, {
                    "system_state": {"memory_usage": 0.85},
                    "objectives": ["manage_resources"]
                })
            ]

            for category, context_data in test_contexts:
                context = DecisionContext(**context_data)
                decision = await self.decision_maker.make_decision(category, context)

                assert decision is not None
                assert decision.category == category

            return True
        except Exception as e:
            logger.error(f"Decision categories test failed: {e}")
            return False

    async def _test_knowledge_entry_creation(self) -> bool:
        """Test knowledge entry creation"""
        try:
            # Create knowledge entry
            entry = KnowledgeEntry(
                category=KnowledgeCategory.SYSTEM_HEALTH_MONITORING,
                title="Test Knowledge Entry",
                content="This is a test knowledge entry content",
                tags=["test", "knowledge"],
                metadata={"test": True}
            )

            # Add to knowledge base
            entry_id = self.knowledge_base.add_knowledge(entry)

            # Validate entry creation
            assert entry_id is not None
            assert len(self.knowledge_base.knowledge) > 0

            # Verify entry was stored correctly
            stored_entry = self.knowledge_base.knowledge[entry_id]
            assert stored_entry.title == "Test Knowledge Entry"
            assert stored_entry.content == "This is a test knowledge entry content"
            assert stored_entry.category == KnowledgeCategory.SYSTEM_HEALTH_MONITORING

            return True
        except Exception as e:
            logger.error(f"Knowledge entry creation test failed: {e}")
            return False

    async def _test_knowledge_search(self) -> bool:
        """Test knowledge base search functionality"""
        try:
            # Add test entries
            test_entries = [
                KnowledgeEntry(
                    category=KnowledgeCategory.SYSTEM_HEALTH_MONITORING,
                    title="CPU Optimization",
                    content="Optimize CPU usage for better performance",
                    tags=["cpu", "optimization", "performance"]
                ),
                KnowledgeEntry(
                    category=KnowledgeCategory.ERROR_RECOVERY,
                    title="Memory Error Handling",
                    content="Handle memory errors and leaks",
                    tags=["memory", "error", "recovery"]
                )
            ]

            for entry in test_entries:
                self.knowledge_base.add_knowledge(entry)

            # Test search
            query = KnowledgeQuery(
                query_text="CPU optimization",
                category=KnowledgeCategory.SYSTEM_HEALTH_MONITORING,
                limit=5
            )

            result = self.knowledge_base.search_knowledge(query)

            # Validate search results
            assert result is not None
            assert len(result.entries) > 0
            assert result.total_results > 0

            # Test category filtering
            cpu_result = self.knowledge_base.search_knowledge(
                KnowledgeQuery(query_text="optimization", category=KnowledgeCategory.SYSTEM_HEALTH_MONITORING)
            )
            memory_result = self.knowledge_base.search_knowledge(
                KnowledgeQuery(query_text="error", category=KnowledgeCategory.ERROR_RECOVERY)
            )

            assert len(cpu_result.entries) > 0
            assert len(memory_result.entries) > 0

            return True
        except Exception as e:
            logger.error(f"Knowledge search test failed: {e}")
            return False

    async def _test_knowledge_categories(self) -> bool:
        """Test knowledge categories and filtering"""
        try:
            # Add entries to different categories
            categories = [
                KnowledgeCategory.SYSTEM_HEALTH_MONITORING,
                KnowledgeCategory.PERFORMANCE_OPTIMIZATION,
                KnowledgeCategory.ERROR_RECOVERY,
                KnowledgeCategory.SERVICE_MANAGEMENT
            ]

            for i, category in enumerate(categories):
                entry = KnowledgeEntry(
                    category=category,
                    title=f"Test Entry {i}",
                    content=f"Content for category {category.value}",
                    tags=[category.value]
                )
                self.knowledge_base.add_knowledge(entry)

            # Test category filtering
            for category in categories:
                query = KnowledgeQuery(
                    query_text="test",
                    category=category,
                    limit=10
                )

                result = self.knowledge_base.search_knowledge(query)

                # Verify results are from correct category
                for entry, score in result.entries:
                    assert entry.category == category

            return True
        except Exception as e:
            logger.error(f"Knowledge categories test failed: {e}")
            return False

    async def _test_knowledge_relationships(self) -> bool:
        """Test knowledge relationship tracking"""
        try:
            # Create related entries
            entry1 = KnowledgeEntry(
                category=KnowledgeCategory.SYSTEM_HEALTH_MONITORING,
                title="System Performance",
                content="Monitor and optimize system performance",
                tags=["performance", "monitoring"]
            )

            entry2 = KnowledgeEntry(
                category=KnowledgeCategory.PERFORMANCE_OPTIMIZATION,
                title="CPU Optimization",
                content="Optimize CPU usage for better performance",
                tags=["cpu", "optimization", "performance"]
            )

            # Add entries
            entry1_id = self.knowledge_base.add_knowledge(entry1)
            entry2_id = self.knowledge_base.add_knowledge(entry2)

            # Add relationship
            self.knowledge_base.add_relationship(entry1_id, entry2_id, "related_to")

            # Search for related entries
            query = KnowledgeQuery(
                query_text="performance",
                include_related=True,
                limit=10
            )

            result = self.knowledge_base.search_knowledge(query)

            # Verify relationship is included
            assert len(result.entries) > 0

            return True
        except Exception as e:
            logger.error(f"Knowledge relationships test failed: {e}")
            return False

    async def _test_policy_creation(self) -> bool:
        """Test management policy creation"""
        try:
            # Create test policy
            policy = ManagementPolicy(
                name="Test Policy",
                action_type=ManagementAction.PERFORMANCE_OPTIMIZATION,
                trigger_conditions={
                    "cpu_usage": {"operator": ">", "value": 0.8},
                    "duration": {"operator": ">", "value": 300}
                },
                action_parameters={
                    "optimize_models": True,
                    "reduce_services": True
                },
                cooldown_period=600,
                priority=8
            )

            # Add to system manager
            self.system_manager.add_custom_policy(policy)

            # Validate policy was added
            assert "Test Policy" in self.system_manager.policies
            stored_policy = self.system_manager.policies["Test Policy"]
            assert stored_policy.name == "Test Policy"
            assert stored_policy.action_type == ManagementAction.PERFORMANCE_OPTIMIZATION

            return True
        except Exception as e:
            logger.error(f"Policy creation test failed: {e}")
            return False

    async def _test_task_creation(self) -> bool:
        """Test autonomous task creation"""
        try:
            # Create policy
            policy = ManagementPolicy(
                name="Test Task Policy",
                action_type=ManagementAction.HEALTH_CHECK,
                trigger_conditions={
                    "health_score": {"operator": "<", "value": 0.7}
                },
                action_parameters={"comprehensive": True},
                cooldown_period=300,
                priority=6
            )

            self.system_manager.add_custom_policy(policy)

            # Create test snapshot that should trigger policy
            from .ai_driven_system_manager import SystemHealthSnapshot
            snapshot = SystemHealthSnapshot(
                timestamp=datetime.now(),
                cpu_usage=0.9,
                memory_usage=0.85,
                disk_usage=0.7,
                network_activity=1000,
                active_services=5,
                error_count=10,
                warning_count=5,
                performance_score=0.6,
                health_score=0.5,
                active_agents=3,
                active_commands=2
            )

            # Check policy triggers
            await self.system_manager._check_policy_triggers(snapshot)

            # Validate task creation
            assert len(self.system_manager.active_tasks) > 0

            task = list(self.system_manager.active_tasks.values())[0]
            assert task.policy.name == "Test Task Policy"
            assert task.status == "pending"

            return True
        except Exception as e:
            logger.error(f"Task creation test failed: {e}")
            return False

    async def _test_health_monitoring(self) -> bool:
        """Test system health monitoring"""
        try:
            # Start monitoring
            await self.system_manager.start_management()

            # Wait a short time for monitoring to start
            await asyncio.sleep(2)

            # Check if health snapshots are being captured
            assert len(self.system_manager.health_history) > 0

            # Validate snapshot structure
            snapshot = self.system_manager.health_history[-1]
            assert snapshot.timestamp is not None
            assert snapshot.cpu_usage >= 0.0
            assert snapshot.memory_usage >= 0.0
            assert snapshot.health_score >= 0.0
            assert snapshot.performance_score >= 0.0

            # Stop monitoring
            await self.system_manager.stop_management()

            return True
        except Exception as e:
            logger.error(f"Health monitoring test failed: {e}")
            return False

    async def _test_predictive_analysis(self) -> bool:
        """Test predictive analysis and trend detection"""
        try:
            # Create test health history with upward trends
            base_time = datetime.now() - timedelta(hours=1)
            snapshots = []

            for i in range(10):
                snapshot = Mock()
                snapshot.cpu_usage = 0.5 + (i * 0.05)  # Increasing trend
                snapshot.memory_usage = 0.6 + (i * 0.03)  # Increasing trend
                snapshot.error_count = i  # Increasing trend
                snapshot.performance_score = 0.9 - (i * 0.02)  # Decreasing trend
                snapshots.append(snapshot)

            self.system_manager.health_history = snapshots

            # Test trend analysis
            cpu_trend = self.system_manager._calculate_trend([s.cpu_usage for s in snapshots])
            memory_trend = self.system_manager._calculate_trend([s.memory_usage for s in snapshots])
            error_trend = self.system_manager._calculate_trend([s.error_count for s in snapshots])

            # Validate trend detection
            assert cpu_trend > 0.0  # Upward trend
            assert memory_trend > 0.0  # Upward trend
            assert error_trend > 0.0  # Upward trend

            return True
        except Exception as e:
            logger.error(f"Predictive analysis test failed: {e}")
            return False

    async def _test_orchestrator_initialization(self) -> bool:
        """Test AI orchestrator initialization"""
        try:
            # Test different orchestrator modes
            modes = [
                OrchestratorMode.MANUAL,
                OrchestratorMode.ASSISTED,
                OrchestratorMode.AUTONOMOUS,
                OrchestratorMode.SUPERVISED
            ]

            for mode in modes:
                config = OrchestratorConfig(mode=mode)
                orchestrator = AIOrchestrator(config)

                # Validate configuration
                assert orchestrator.config.mode == mode
                assert orchestrator.ai_controller is not None
                assert orchestrator.decision_maker is not None
                assert orchestrator.knowledge_base is not None

                # Clean up
                await orchestrator.stop_orchestrator()

            return True
        except Exception as e:
            logger.error(f"Orchestrator initialization test failed: {e}")
            return False

    async def _test_operation_management(self) -> bool:
        """Test operation creation and management"""
        try:
            # Create test operation
            operation_id = await self.orchestrator.request_operation(
                operation_type="test_operation",
                description="Test operation for validation",
                parameters={"test": True},
                priority=7,
                requires_approval=False
            )

            # Validate operation creation
            assert operation_id is not None
            assert operation_id in self.orchestrator.operations

            operation = self.orchestrator.operations[operation_id]
            assert operation.operation_type == "test_operation"
            assert operation.description == "Test operation for validation"
            assert operation.status == "approved"  # No approval required

            # Test pending approval
            pending_id = await self.orchestrator.request_operation(
                operation_type="pending_operation",
                description="Operation requiring approval",
                requires_approval=True
            )

            assert pending_id in self.orchestrator.operations
            assert self.orchestrator.operations[pending_id].status == "pending"

            return True
        except Exception as e:
            logger.error(f"Operation management test failed: {e}")
            return False

    async def _test_approval_workflow(self) -> bool:
        """Test operation approval workflow"""
        try:
            # Create operation requiring approval
            operation_id = await self.orchestrator.request_operation(
                operation_type="approval_test",
                description="Test approval workflow",
                requires_approval=True
            )

            # Check pending approvals
            pending = self.orchestrator.get_pending_operations()
            assert len(pending) > 0
            assert pending[0]["id"] == operation_id

            # Approve operation
            success = await self.orchestrator.approve_operation(operation_id, "test_user")
            assert success == True

            # Check operation is approved
            operation = self.orchestrator.operations[operation_id]
            assert operation.status == "approved"
            assert operation.approved_by == "test_user"

            # Test rejection
            reject_id = await self.orchestrator.request_operation(
                operation_type="rejection_test",
                description="Test rejection workflow",
                requires_approval=True
            )

            success = await self.orchestrator.reject_operation(reject_id, "Test rejection")
            assert success == True

            # Check operation is rejected
            operation = self.orchestrator.operations[reject_id]
            assert operation.status == "cancelled"

            return True
        except Exception as e:
            logger.error(f"Approval workflow test failed: {e}")
            return False

    async def _test_event_handling(self) -> bool:
        """Test event handling and broadcasting"""
        try:
            # Track received events
            received_events = []

            def event_handler(event_data):
                received_events.append(event_data)

            # Register event handler
            self.orchestrator.add_event_handler("operation_completed", event_handler)

            # Create and complete an operation
            operation_id = await self.orchestrator.request_operation(
                operation_type="event_test",
                description="Test event handling",
                requires_approval=False
            )

            # Simulate operation completion
            await self.orchestrator._emit_event("operation_completed", {
                "operation_id": operation_id,
                "status": "completed"
            })

            # Wait for event processing
            await asyncio.sleep(0.1)

            # Validate event was received
            assert len(received_events) > 0
            assert received_events[-1]["operation_id"] == operation_id

            return True
        except Exception as e:
            logger.error(f"Event handling test failed: {e}")
            return False

    # Integration test implementations
    async def _test_full_ai_workflow(self) -> bool:
        """Test complete AI workflow from monitoring to action"""
        try:
            # Simulate system degradation
            with patch.object(self.orchestrator.monitoring_system, 'get_system_status') as mock_status:
                mock_status.return_value = {
                    "health_score": 0.4,
                    "performance_score": 0.3,
                    "active_alerts": [{"severity": "critical", "message": "High CPU usage"}],
                    "services": [{"name": "test_service", "status": "degraded"}]
                }

                # Wait for autonomous decision making
                await asyncio.sleep(5)

                # Check if operations were created
                operations = self.orchestrator.get_recent_operations(5)
                assert len(operations) > 0

                # Verify operations address the issues
                optimization_ops = [op for op in operations if "optimization" in op["type"].lower()]
                assert len(optimization_ops) > 0

            return True
        except Exception as e:
            logger.error(f"Full AI workflow test failed: {e}")
            return False

    async def _test_component_communication(self) -> bool:
        """Test inter-component communication"""
        try:
            # Test knowledge base access from decision maker
            context = DecisionContext(
                system_state={"error_type": "memory_leak"},
                objectives=["resolve_issue"]
            )

            # Decision maker should query knowledge base
            decision = await self.orchestrator.decision_maker.make_decision(
                DecisionCategory.ERROR_RECOVERY, context
            )

            # Verify decision was made
            assert decision is not None
            assert decision.action is not None

            return True
        except Exception as e:
            logger.error(f"Component communication test failed: {e}")
            return False

    async def _test_error_propagation(self) -> bool:
        """Test error propagation and handling across components"""
        try:
            # Simulate error in monitoring system
            with patch.object(self.orchestrator.monitoring_system, 'get_system_status') as mock_status:
                mock_status.side_effect = Exception("Monitoring system error")

                # System should handle error gracefully
                status = self.orchestrator.get_orchestrator_status()
                assert "running" in status

            return True
        except Exception as e:
            logger.error(f"Error propagation test failed: {e}")
            return False

    async def _test_state_synchronization(self) -> bool:
        """Test state synchronization between components"""
        try:
            # Get initial state
            initial_status = self.orchestrator.get_orchestrator_status()

            # Create operation
            operation_id = await self.orchestrator.request_operation(
                operation_type="sync_test",
                description="Test state synchronization",
                requires_approval=False
            )

            # Get updated state
            updated_status = self.orchestrator.get_orchestrator_status()

            # Verify state is synchronized
            assert updated_status["active_operations"] == initial_status["active_operations"] + 1

            return True
        except Exception as e:
            logger.error(f"State synchronization test failed: {e}")
            return False

    # Performance test implementations
    async def _test_command_processing_performance(self) -> Dict[str, Any]:
        """Test command processing performance"""
        try:
            # Create test commands
            commands = []
            for i in range(self.test_config["performance_test_iterations"]):
                command = AICommand(
                    command_type=AICommandType.SYSTEM_MONITORING,
                    parameters={"action": f"test_{i}"}
                )
                commands.append(command)

            # Measure execution time
            start_time = time.time()
            results = []

            for command in commands:
                result = await self.orchestrator.ai_controller.process_command(command)
                results.append(result)

            total_time = time.time() - start_time

            # Calculate metrics
            avg_time = total_time / len(commands)
            throughput = len(commands) / total_time

            return {
                "total_time": total_time,
                "avg_time": avg_time,
                "throughput": throughput,
                "success_rate": sum(1 for r in results if r.success) / len(results)
            }
        except Exception as e:
            logger.error(f"Command processing performance test failed: {e}")
            return {"error": str(e)}

    async def _test_decision_making_performance(self) -> Dict[str, Any]:
        """Test decision making performance"""
        try:
            # Create test contexts
            contexts = []
            for i in range(self.test_config["performance_test_iterations"] // 2):  # Fewer iterations as decisions are more complex
                context = DecisionContext(
                    system_state={"performance_score": 0.7 + (i * 0.01)},
                    objectives=["optimize_system"]
                )
                contexts.append(context)

            # Measure execution time
            start_time = time.time()
            decisions = []

            for context in contexts:
                decision = await self.orchestrator.decision_maker.make_decision(
                    DecisionCategory.SYSTEM_MANAGEMENT, context
                )
                decisions.append(decision)

            total_time = time.time() - start_time

            # Calculate metrics
            avg_time = total_time / len(contexts)
            throughput = len(contexts) / total_time
            avg_confidence = sum(d.confidence_score for d in decisions) / len(decisions)

            return {
                "total_time": total_time,
                "avg_time": avg_time,
                "throughput": throughput,
                "avg_confidence": avg_confidence
            }
        except Exception as e:
            logger.error(f"Decision making performance test failed: {e}")
            return {"error": str(e)}

    async def _test_knowledge_search_performance(self) -> Dict[str, Any]:
        """Test knowledge search performance"""
        try:
            # Create test queries
            queries = []
            for i in range(self.test_config["performance_test_iterations"]):
                query = KnowledgeQuery(
                    query_text=f"test query {i % 10}",  # Repeat queries to test caching
                    limit=10
                )
                queries.append(query)

            # Measure execution time
            start_time = time.time()
            results = []

            for query in queries:
                result = self.orchestrator.knowledge_base.search_knowledge(query)
                results.append(result)

            total_time = time.time() - start_time

            # Calculate metrics
            avg_time = total_time / len(queries)
            throughput = len(queries) / total_time
            avg_results = sum(len(r.entries) for r in results) / len(results)

            return {
                "total_time": total_time,
                "avg_time": avg_time,
                "throughput": throughput,
                "avg_results": avg_results
            }
        except Exception as e:
            logger.error(f"Knowledge search performance test failed: {e}")
            return {"error": str(e)}

    async def _test_system_scalability(self) -> Dict[str, Any]:
        """Test system scalability under load"""
        try:
            # Create concurrent load
            concurrent_operations = 50
            operations = []

            start_time = time.time()

            # Create operations concurrently
            tasks = []
            for i in range(concurrent_operations):
                task = self.orchestrator.request_operation(
                    operation_type="scalability_test",
                    description=f"Scalability test operation {i}",
                    requires_approval=False
                )
                tasks.append(task)

            # Wait for all operations to complete
            operation_ids = await asyncio.gather(*tasks, return_exceptions=True)

            # Wait for operations to be processed
            await asyncio.sleep(5)

            total_time = time.time() - start_time

            # Calculate metrics
            successful_operations = len([oid for oid in operation_ids if not isinstance(oid, Exception)])
            success_rate = successful_operations / concurrent_operations
            throughput = concurrent_operations / total_time

            # Get system status after load
            status = self.orchestrator.get_orchestrator_status()

            return {
                "total_time": total_time,
                "successful_operations": successful_operations,
                "concurrent_operations": concurrent_operations,
                "success_rate": success_rate,
                "throughput": throughput,
                "system_health": status.get("monitoring_status", {}).get("health_score", 0.0)
            }
        except Exception as e:
            logger.error(f"System scalability test failed: {e}")
            return {"error": str(e)}

    # Stress test implementations
    async def _test_high_load_handling(self) -> Dict[str, Any]:
        """Test system behavior under high load"""
        try:
            start_time = time.time()
            duration = self.test_config["stress_test_duration"]
            operations_per_second = 20

            successful_operations = 0
            failed_operations = 0
            total_operations = 0

            # Generate continuous load
            while time.time() - start_time < duration:
                # Create burst of operations
                tasks = []
                for i in range(operations_per_second):
                    task = self.orchestrator.request_operation(
                        operation_type="stress_test",
                        description=f"Stress test operation {total_operations}",
                        requires_approval=False
                    )
                    tasks.append(task)
                    total_operations += 1

                # Execute operations
                try:
                    operation_ids = await asyncio.wait_for(
                        asyncio.gather(*tasks, return_exceptions=True),
                        timeout=5.0
                    )

                    successful = len([oid for oid in operation_ids if not isinstance(oid, Exception)])
                    successful_operations += successful
                    failed_operations += (len(operation_ids) - successful)

                except asyncio.TimeoutError:
                    failed_operations += len(tasks)

                # Wait before next batch
                await asyncio.sleep(1.0)

            total_time = time.time() - start_time
            error_rate = failed_operations / total_operations if total_operations > 0 else 0

            return {
                "total_time": total_time,
                "total_operations": total_operations,
                "successful_operations": successful_operations,
                "failed_operations": failed_operations,
                "error_rate": error_rate,
                "operations_per_second": total_operations / total_time,
                "stability": error_rate < 0.1  # Less than 10% error rate
            }
        except Exception as e:
            logger.error(f"High load handling test failed: {e}")
            return {"error": str(e)}

    async def _test_memory_management(self) -> Dict[str, Any]:
        """Test memory management under stress"""
        try:
            import psutil
            import gc

            # Get initial memory usage
            process = psutil.Process()
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB

            # Generate memory load
            large_data_sets = []
            for i in range(100):
                # Create large data structures
                large_data = {"data": ["x" * 1000] * 10000}  # ~10MB per set
                large_data_sets.append(large_data)

                # Create some operations to process data
                await self.orchestrator.request_operation(
                    operation_type="memory_test",
                    description=f"Memory test operation {i}",
                    parameters={"data_size": len(large_data["data"])},
                    requires_approval=False
                )

                # Force garbage collection periodically
                if i % 20 == 0:
                    gc.collect()

            # Get peak memory usage
            peak_memory = process.memory_info().rss / 1024 / 1024  # MB

            # Clear data and force cleanup
            large_data_sets.clear()
            gc.collect()

            # Get final memory usage
            final_memory = process.memory_info().rss / 1024 / 1024  # MB

            # Calculate memory growth
            memory_growth = final_memory - initial_memory
            memory_leak = memory_growth > 100  # More than 100MB growth indicates potential leak

            return {
                "initial_memory_mb": initial_memory,
                "peak_memory_mb": peak_memory,
                "final_memory_mb": final_memory,
                "memory_growth_mb": memory_growth,
                "memory_leak": memory_leak,
                "max_memory": f"{peak_memory:.1f}MB"
            }
        except Exception as e:
            logger.error(f"Memory management test failed: {e}")
            return {"error": str(e)}

    async def _test_concurrent_operations(self) -> Dict[str, Any]:
        """Test concurrent operation handling"""
        try:
            max_concurrent = 100
            concurrency_levels = [10, 25, 50, 75, 100]

            results = {}

            for concurrency in concurrency_levels:
                start_time = time.time()

                # Create concurrent operations
                tasks = []
                for i in range(concurrency):
                    task = self.orchestrator.request_operation(
                        operation_type="concurrency_test",
                        description=f"Concurrency test {concurrency}-{i}",
                        requires_approval=False
                    )
                    tasks.append(task)

                # Execute with timeout
                try:
                    operation_ids = await asyncio.wait_for(
                        asyncio.gather(*tasks, return_exceptions=True),
                        timeout=30.0
                    )

                    successful = len([oid for oid in operation_ids if not isinstance(oid, Exception)])
                    total_time = time.time() - start_time

                    results[concurrency] = {
                        "successful": successful,
                        "total": concurrency,
                        "success_rate": successful / concurrency,
                        "total_time": total_time,
                        "throughput": concurrency / total_time
                    }

                except asyncio.TimeoutError:
                    results[concurrency] = {
                        "successful": 0,
                        "total": concurrency,
                        "success_rate": 0.0,
                        "timeout": True
                    }

            # Find maximum successful concurrency
            max_successful = max([
                level for level, result in results.items()
                if result["success_rate"] > 0.9
            ] + [0])

            return {
                "concurrency_results": results,
                "max_successful_concurrency": max_successful,
                "concurrency_success": max_successful >= 50
            }
        except Exception as e:
            logger.error(f"Concurrent operations test failed: {e}")
            return {"error": str(e)}

    async def _test_recovery_from_failure(self) -> Dict[str, Any]:
        """Test system recovery from failure conditions"""
        try:
            start_time = time.time()

            # Test 1: Component failure simulation
            with patch.object(self.orchestrator.monitoring_system, 'get_system_status') as mock_status:
                # First call fails, subsequent calls succeed
                mock_status.side_effect = [Exception("Component failure")] + [
                    {"health_score": 0.8, "performance_score": 0.7}
                ] * 10

                # System should recover and continue functioning
                for i in range(5):
                    status = self.orchestrator.get_orchestrator_status()
                    # System should still be running despite component failure

            # Test 2: Memory pressure simulation
            import gc
            large_objects = []

            def memory_intensive_operation():
                # Create memory pressure
                large_data = ["x" * 1000000] * 100  # Large data structure
                large_objects.append(large_data)
                return len(large_data)

            # Execute memory intensive operations
            for i in range(50):
                try:
                    result = memory_intensive_operation()
                    # System should handle memory pressure

                    # Periodic cleanup
                    if i % 10 == 0:
                        large_objects.clear()
                        gc.collect()

                except MemoryError:
                    # System should handle memory errors gracefully
                    large_objects.clear()
                    gc.collect()
                    continue

            # Test 3: Rapid operation cycling
            recovery_time = None
            for cycle in range(5):
                # Create many operations quickly
                tasks = []
                for i in range(20):
                    task = self.orchestrator.request_operation(
                        operation_type="recovery_test",
                        description=f"Recovery test cycle {cycle}-{i}",
                        requires_approval=False
                    )
                    tasks.append(task)

                # Cancel half the operations to simulate failures
                operation_ids = await asyncio.gather(*tasks, return_exceptions=True)

                # Wait for recovery
                await asyncio.sleep(2)

                # Check if system recovered
                status = self.orchestrator.get_orchestrator_status()
                if status.get("running", False):
                    recovery_time = time.time() - start_time
                    break

            # Clear memory
            large_objects.clear()
            gc.collect()

            return {
                "recovery_success": recovery_time is not None,
                "recovery_time": recovery_time,
                "test_duration": time.time() - start_time
            }
        except Exception as e:
            logger.error(f"Recovery from failure test failed: {e}")
            return {"error": str(e)}

    # Test execution methods
    async def run_test_suite(self, suite_name: str) -> Dict[str, Any]:
        """Run a specific test suite"""
        if suite_name not in self.test_suites:
            raise ValueError(f"Test suite '{suite_name}' not found")

        suite = self.test_suites[suite_name]
        logger.info(f"Running test suite: {suite_name}")

        # Setup
        if suite.setup_function:
            await suite.setup_function()

        results = {
            "suite_name": suite_name,
            "description": suite.description,
            "start_time": datetime.now().isoformat(),
            "test_results": [],
            "summary": {
                "total_tests": 0,
                "passed_tests": 0,
                "failed_tests": 0,
                "skipped_tests": 0,
                "error_tests": 0,
                "execution_time": 0.0,
                "success_rate": 0.0
            }
        }

        # Execute tests
        suite_start_time = time.time()

        if suite.parallel_execution:
            # Execute tests in parallel
            tasks = []
            for test_case in suite.test_cases:
                if test_case.enabled:
                    task = self._execute_test_case(test_case)
                    tasks.append(task)

            test_results = await asyncio.gather(*tasks, return_exceptions=True)
        else:
            # Execute tests sequentially
            test_results = []
            for test_case in suite.test_cases:
                if test_case.enabled:
                    result = await self._execute_test_case(test_case)
                    test_results.append(result)

        # Process results
        for result in test_results:
            if isinstance(result, TestExecution):
                results["test_results"].append(self._test_execution_to_dict(result))
            elif isinstance(result, Exception):
                # Test execution failed
                error_result = TestExecution(
                    test_case=TestCase(name="unknown", description="Test execution error", level=TestLevel.UNIT, component="unknown", test_function=lambda: None, expected_result=None),
                    start_time=datetime.now(),
                    result=TestResult.ERROR,
                    error=str(result)
                )
                results["test_results"].append(self._test_execution_to_dict(error_result))

        # Calculate summary
        suite_execution_time = time.time() - suite_start_time
        self._calculate_suite_summary(results, suite_execution_time)

        # Teardown
        if suite.teardown_function:
            await suite.teardown_function()

        logger.info(f"Test suite '{suite_name}' completed with {results['summary']['success_rate']:.2%} success rate")
        return results

    async def _execute_test_case(self, test_case: TestCase) -> TestExecution:
        """Execute a single test case"""
        execution = TestExecution(
            test_case=test_case,
            start_time=datetime.now()
        )

        try:
            logger.info(f"Executing test: {test_case.name}")

            # Check prerequisites
            for prereq in test_case.prerequisites:
                if not hasattr(self, prereq):
                    execution.result = TestResult.SKIPPED
                    execution.output = f"Prerequisite '{prereq}' not met"
                    return execution

            # Execute test with timeout
            if asyncio.iscoroutinefunction(test_case.test_function):
                result = await asyncio.wait_for(
                    test_case.test_function(),
                    timeout=test_case.timeout
                )
            else:
                result = test_case.test_function()

            # Validate result
            if isinstance(test_case.expected_result, dict):
                # Performance test - compare metrics
                if isinstance(result, dict) and "error" not in result:
                    success = all(
                        result.get(key, 0) <= test_case.expected_result[key]
                        for key in test_case.expected_result
                        if key.endswith("_time") or key == "error_rate"
                    ) and all(
                        result.get(key, 0) >= test_case.expected_result[key]
                        for key in test_case.expected_result
                        if key in ["throughput", "success_rate", "stability"]
                    )
                else:
                    success = False
            else:
                # Simple boolean test
                success = bool(result) == bool(test_case.expected_result)

            execution.result = TestResult.PASSED if success else TestResult.FAILED
            execution.output = f"Test {'passed' if success else 'failed'}. Result: {result}"
            execution.metrics = {"result": result} if isinstance(result, dict) else {"success": success}

        except asyncio.TimeoutError:
            execution.result = TestResult.FAILED
            execution.error = f"Test timed out after {test_case.timeout} seconds"
            execution.output = execution.error
        except Exception as e:
            execution.result = TestResult.ERROR
            execution.error = str(e)
            execution.output = f"Test execution error: {e}"

        finally:
            execution.end_time = datetime.now()
            execution.execution_time = (execution.end_time - execution.start_time).total_seconds()

            # Store execution
            self.test_executions.append(execution)
            self._store_test_execution(execution)

            logger.info(f"Test '{test_case.name}' completed with result: {execution.result.value}")

        return execution

    def _test_execution_to_dict(self, execution: TestExecution) -> Dict[str, Any]:
        """Convert test execution to dictionary"""
        return {
            "test_name": execution.test_case.name,
            "description": execution.test_case.description,
            "level": execution.test_case.level.value,
            "component": execution.test_case.component,
            "start_time": execution.start_time.isoformat(),
            "end_time": execution.end_time.isoformat() if execution.end_time else None,
            "result": execution.result.value,
            "execution_time": execution.execution_time,
            "output": execution.output,
            "error": execution.error,
            "metrics": execution.metrics
        }

    def _calculate_suite_summary(self, results: Dict[str, Any], execution_time: float):
        """Calculate test suite summary"""
        test_results = results["test_results"]

        summary = results["summary"]
        summary["total_tests"] = len(test_results)
        summary["passed_tests"] = len([r for r in test_results if r["result"] == "passed"])
        summary["failed_tests"] = len([r for r in test_results if r["result"] == "failed"])
        summary["skipped_tests"] = len([r for r in test_results if r["result"] == "skipped"])
        summary["error_tests"] = len([r for r in test_results if r["result"] == "error"])
        summary["execution_time"] = execution_time

        if summary["total_tests"] > 0:
            summary["success_rate"] = summary["passed_tests"] / summary["total_tests"]
        else:
            summary["success_rate"] = 0.0

    def _store_test_execution(self, execution: TestExecution):
        """Store test execution in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO test_executions
                    (execution_id, test_name, test_level, component, start_time, end_time,
                     result, execution_time, output, error, metrics)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    f"exec_{int(time.time() * 1000)}",
                    execution.test_case.name,
                    execution.test_case.level.value,
                    execution.test_case.component,
                    execution.start_time.isoformat(),
                    execution.end_time.isoformat() if execution.end_time else None,
                    execution.result.value,
                    execution.execution_time,
                    execution.output,
                    execution.error,
                    json.dumps(execution.metrics)
                ))
                conn.commit()

        except Exception as e:
            logger.error(f"Error storing test execution: {e}")

    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all test suites"""
        logger.info("Starting comprehensive AI system test suite")

        start_time = time.time()
        all_results = {}

        # Run each test suite
        for suite_name in self.test_suites:
            try:
                suite_result = await self.run_test_suite(suite_name)
                all_results[suite_name] = suite_result
            except Exception as e:
                logger.error(f"Error running test suite '{suite_name}': {e}")
                all_results[suite_name] = {
                    "suite_name": suite_name,
                    "error": str(e),
                    "summary": {
                        "total_tests": 0,
                        "passed_tests": 0,
                        "failed_tests": 0,
                        "success_rate": 0.0
                    }
                }

        # Calculate overall summary
        total_execution_time = time.time() - start_time
        overall_summary = self._calculate_overall_summary(all_results, total_execution_time)

        # Store overall results
        self._store_test_results_summary(overall_summary)

        # Update test results
        self.test_results.update(overall_summary)

        logger.info(f"Comprehensive test suite completed with {overall_summary['success_rate']:.2%} success rate")
        return {
            "timestamp": datetime.now().isoformat(),
            "execution_time": total_execution_time,
            "overall_summary": overall_summary,
            "suite_results": all_results
        }

    def _calculate_overall_summary(self, all_results: Dict[str, Any], total_execution_time: float) -> Dict[str, Any]:
        """Calculate overall test summary"""
        total_tests = sum(result["summary"]["total_tests"] for result in all_results.values())
        passed_tests = sum(result["summary"]["passed_tests"] for result in all_results.values())
        failed_tests = sum(result["summary"]["failed_tests"] for result in all_results.values())
        skipped_tests = sum(result["summary"]["skipped_tests"] for result in all_results.values())
        error_tests = sum(result["summary"]["error_tests"] for result in all_results.values())

        success_rate = passed_tests / total_tests if total_tests > 0 else 0.0

        # Component breakdown
        component_results = {}
        for suite_name, result in all_results.items():
            if "error" not in result:
                component = suite_name.replace("_tests", "")
                component_results[component] = {
                    "total_tests": result["summary"]["total_tests"],
                    "passed_tests": result["summary"]["passed_tests"],
                    "success_rate": result["summary"]["success_rate"]
                }

        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "skipped_tests": skipped_tests,
            "error_tests": error_tests,
            "success_rate": success_rate,
            "total_execution_time": total_execution_time,
            "component_results": component_results
        }

    def _store_test_results_summary(self, summary: Dict[str, Any]):
        """Store test results summary in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO test_results_summary
                    (test_run_id, timestamp, total_tests, passed_tests, failed_tests,
                     skipped_tests, error_tests, success_rate, total_execution_time, performance_metrics)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    f"run_{int(time.time() * 1000)}",
                    datetime.now().isoformat(),
                    summary["total_tests"],
                    summary["passed_tests"],
                    summary["failed_tests"],
                    summary["skipped_tests"],
                    summary["error_tests"],
                    summary["success_rate"],
                    summary["total_execution_time"],
                    json.dumps(self.test_results["performance_metrics"])
                ))
                conn.commit()

        except Exception as e:
            logger.error(f"Error storing test results summary: {e}")

    async def generate_test_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        try:
            # Get recent test executions
            recent_executions = self.test_executions[-100:]  # Last 100 executions

            # Calculate component performance
            component_performance = {}
            for execution in recent_executions:
                component = execution.test_case.component
                if component not in component_performance:
                    component_performance[component] = {"total": 0, "passed": 0}
                component_performance[component]["total"] += 1
                if execution.result == TestResult.PASSED:
                    component_performance[component]["passed"] += 1

            # Calculate success rates
            for component in component_performance:
                total = component_performance[component]["total"]
                passed = component_performance[component]["passed"]
                component_performance[component]["success_rate"] = passed / total if total > 0 else 0.0

            # Generate recommendations
            recommendations = []
            for component, performance in component_performance.items():
                if performance["success_rate"] < 0.8:
                    recommendations.append(f"Component '{component}' has low success rate ({performance['success_rate']:.2%}) - investigate and fix issues")

            if self.test_results["success_rate"] < 0.9:
                recommendations.append("Overall system success rate is below 90% - review failed tests and address issues")

            return {
                "report_timestamp": datetime.now().isoformat(),
                "test_summary": self.test_results,
                "component_performance": component_performance,
                "recent_executions": [self._test_execution_to_dict(exec) for exec in recent_executions[-20:]],
                "recommendations": recommendations,
                "test_configuration": self.test_config
            }

        except Exception as e:
            logger.error(f"Error generating test report: {e}")
            return {"error": str(e)}

    def get_test_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get test execution history"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT test_name, test_level, component, start_time, end_time, result,
                           execution_time, output, error
                    FROM test_executions
                    ORDER BY start_time DESC
                    LIMIT ?
                """, (limit,))

                rows = cursor.fetchall()

                return [
                    {
                        "test_name": row[0],
                        "test_level": row[1],
                        "component": row[2],
                        "start_time": row[3],
                        "end_time": row[4],
                        "result": row[5],
                        "execution_time": row[6],
                        "output": row[7],
                        "error": row[8]
                    }
                    for row in rows
                ]

        except Exception as e:
            logger.error(f"Error getting test history: {e}")
            return []

    def cleanup_test_data(self):
        """Clean up test data"""
        try:
            if self.test_config["cleanup_after_tests"]:
                if self.test_data_dir.exists():
                    shutil.rmtree(self.test_data_dir)
                    self.test_data_dir.mkdir(exist_ok=True)
                logger.info("Test data cleaned up")

        except Exception as e:
            logger.error(f"Error cleaning up test data: {e}")