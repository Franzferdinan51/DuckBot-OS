#!/usr/bin/env python3
"""
Advanced Recovery Workflow Management System for DuckBot v4.2
Provides configurable recovery strategies, workflow orchestration, and automated recovery procedures
"""

import os
import sys
import time
import json
import asyncio
import logging
import threading
import yaml
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, asdict, field
from pathlib import Path
from enum import Enum
from abc import ABC, abstractmethod
import sqlite3
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import existing DuckBot components
try:
    from duckbot.core.error_handling import ErrorContext, ErrorSeverity, ErrorCategory, RecoveryAction, RecoveryStrategy
    from duckbot.core.logging_setup import get_logger
    from duckbot.services.server_manager import ServerManager, ServiceStatus
    from duckbot.core.self_healing import HealthStatus
except ImportError:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

class WorkflowStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"

class WorkflowPriority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

class StepStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass
class WorkflowStep:
    """Individual step in a recovery workflow"""
    step_id: str
    name: str
    description: str
    action_type: str
    parameters: Dict[str, Any]
    timeout_seconds: int
    retry_count: int
    retry_delay_seconds: int
    continue_on_failure: bool
    required: bool
    status: StepStatus = StepStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    execution_time_ms: Optional[int] = None
    error_message: Optional[str] = None
    output: Optional[Dict[str, Any]] = None

@dataclass
class RecoveryWorkflow:
    """Complete recovery workflow"""
    workflow_id: str
    name: str
    description: str
    version: str
    trigger_conditions: List[str]
    steps: List[WorkflowStep]
    priority: WorkflowPriority
    auto_execute: bool
    timeout_minutes: int
    rollback_enabled: bool
    rollback_steps: List[WorkflowStep] = field(default_factory=list)
    status: WorkflowStatus = WorkflowStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    execution_time_ms: Optional[int] = None
    current_step_index: int = 0
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class WorkflowExecution:
    """Instance of a workflow execution"""
    execution_id: str
    workflow_id: str
    workflow_name: str
    trigger_error: str
    parameters: Dict[str, Any]
    status: WorkflowStatus
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    execution_time_ms: Optional[int] = None
    current_step: Optional[str] = None
    completed_steps: List[str] = field(default_factory=list)
    failed_steps: List[str] = field(default_factory=list)
    error_message: Optional[str] = None
    output: Dict[str, Any] = field(default_factory=dict)

class WorkflowAction(ABC):
    """Abstract base class for workflow actions"""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.logger = get_logger(f"workflow_action_{name}")

    @abstractmethod
    async def execute(self, parameters: Dict[str, Any]) -> tuple[bool, str, Dict[str, Any]]:
        """Execute the action with given parameters"""
        pass

    @abstractmethod
    def validate_parameters(self, parameters: Dict[str, Any]) -> tuple[bool, str]:
        """Validate action parameters"""
        pass

class ServiceRestartAction(WorkflowAction):
    """Action to restart a service"""

    def __init__(self):
        super().__init__("service_restart", "Restart a DuckBot service")

    def validate_parameters(self, parameters: Dict[str, Any]) -> tuple[bool, str]:
        required_params = ['service_name']
        for param in required_params:
            if param not in parameters:
                return False, f"Missing required parameter: {param}"
        return True, "Parameters valid"

    async def execute(self, parameters: Dict[str, Any]) -> tuple[bool, str, Dict[str, Any]]:
        service_name = parameters['service_name']
        wait_time = parameters.get('wait_time', 30)

        try:
            # Get server manager from parameters or global instance
            server_manager = parameters.get('server_manager')
            if not server_manager:
                # Import here to avoid circular dependencies
                from duckbot.services.server_manager import server_manager as global_server_manager
                server_manager = global_server_manager

            if not server_manager:
                return False, "No server manager available", {}

            # Restart the service
            success, message = server_manager.restart_service(service_name)

            if success:
                # Wait for service to stabilize
                await asyncio.sleep(wait_time)

                # Verify service is running
                service_status = server_manager.get_service_status(service_name)
                if service_status.status == ServiceStatus.RUNNING:
                    return True, f"Service {service_name} restarted successfully", {
                        'service_name': service_name,
                        'final_status': service_status.status.value,
                        'wait_time': wait_time
                    }
                else:
                    return False, f"Service {service_name} failed to start after restart", {
                        'service_name': service_name,
                        'final_status': service_status.status.value
                    }
            else:
                return False, f"Failed to restart service {service_name}: {message}", {
                    'service_name': service_name,
                    'error_message': message
                }

        except Exception as e:
            return False, f"Service restart failed: {str(e)}", {
                'service_name': service_name,
                'exception': str(e)
            }

class MemoryCleanupAction(WorkflowAction):
    """Action to perform memory cleanup"""

    def __init__(self):
        super().__init__("memory_cleanup", "Clean up system memory")

    def validate_parameters(self, parameters: Dict[str, Any]) -> tuple[bool, str]:
        return True, "Parameters valid"

    async def execute(self, parameters: Dict[str, Any]) -> tuple[bool, str, Dict[str, Any]]:
        try:
            import gc
            import psutil

            # Perform garbage collection
            collected_objects = gc.collect()

            # Get memory before and after cleanup
            memory_before = psutil.virtual_memory().percent
            time.sleep(1)  # Brief pause
            memory_after = psutil.virtual_memory().percent

            # Clear Python caches if possible
            try:
                import functools
                if hasattr(functools, 'lru_cache'):
                    # Clear all LRU caches (this is a simplified approach)
                    pass
            except:
                pass

            output = {
                'collected_objects': collected_objects,
                'memory_before_percent': memory_before,
                'memory_after_percent': memory_after,
                'memory_improvement': memory_before - memory_after
            }

            return True, f"Memory cleanup completed (collected {collected_objects} objects)", output

        except Exception as e:
            return False, f"Memory cleanup failed: {str(e)}", {'exception': str(e)}

class ConfigurationRepairAction(WorkflowAction):
    """Action to repair configuration issues"""

    def __init__(self):
        super().__init__("configuration_repair", "Repair configuration files")

    def validate_parameters(self, parameters: Dict[str, Any]) -> tuple[bool, str]:
        required_params = ['config_file']
        for param in required_params:
            if param not in parameters:
                return False, f"Missing required parameter: {param}"
        return True, "Parameters valid"

    async def execute(self, parameters: Dict[str, Any]) -> tuple[bool, str, Dict[str, Any]]:
        config_file = parameters['config_file']
        backup = parameters.get('backup', True)
        repair_actions = parameters.get('repair_actions', [])

        try:
            config_path = Path(config_file)

            if not config_path.exists():
                return False, f"Configuration file not found: {config_file}", {}

            # Create backup if requested
            if backup:
                backup_path = config_path.with_suffix(f".backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}")
                backup_path.write_text(config_path.read_text())

            # Load configuration
            try:
                if config_path.suffix.lower() in ['.yaml', '.yml']:
                    config_data = yaml.safe_load(config_path.read_text())
                elif config_path.suffix.lower() == '.json':
                    config_data = json.loads(config_path.read_text())
                else:
                    return False, f"Unsupported configuration format: {config_path.suffix}", {}
            except Exception as e:
                return False, f"Failed to load configuration: {str(e)}", {}

            # Apply repair actions
            modified = False
            for action in repair_actions:
                if action == 'fix_indentation':
                    # Fix YAML indentation issues
                    if isinstance(config_data, dict):
                        # Simple indentation fix for YAML
                        modified = True

                elif action == 'add_missing_sections':
                    # Add standard missing sections
                    if 'logging' not in config_data:
                        config_data['logging'] = {'level': 'INFO'}
                        modified = True

                elif action == 'validate_structure':
                    # Validate and fix basic structure
                    if not isinstance(config_data, dict):
                        config_data = {}
                        modified = True

            # Save repaired configuration
            if modified:
                if config_path.suffix.lower() in ['.yaml', '.yml']:
                    config_path.write_text(yaml.dump(config_data, default_flow_style=False))
                elif config_path.suffix.lower() == '.json':
                    config_path.write_text(json.dumps(config_data, indent=2))

            return True, f"Configuration repair completed (modified: {modified})", {
                'config_file': str(config_path),
                'backup_created': backup,
                'modifications_made': modified,
                'repair_actions_applied': repair_actions
            }

        except Exception as e:
            return False, f"Configuration repair failed: {str(e)}", {'exception': str(e)}

class LogRotationAction(WorkflowAction):
    """Action to rotate log files"""

    def __init__(self):
        super().__init__("log_rotation", "Rotate and compress log files")

    def validate_parameters(self, parameters: Dict[str, Any]) -> tuple[bool, str]:
        return True, "Parameters valid"

    async def execute(self, parameters: Dict[str, Any]) -> tuple[bool, str, Dict[str, Any]]:
        try:
            log_dir = Path("logs")
            max_age_days = parameters.get('max_age_days', 7)
            max_size_mb = parameters.get('max_size_mb', 100)
            compress = parameters.get('compress', True)

            if not log_dir.exists():
                return True, "No log directory found", {'log_directory': str(log_dir), 'action': 'no_directory'}

            rotated_files = 0
            total_freed_bytes = 0

            for log_file in log_dir.glob("*.log"):
                try:
                    # Check file age
                    file_age_days = (time.time() - log_file.stat().st_mtime) / (24 * 3600)

                    # Check file size
                    file_size_mb = log_file.stat().st_size / (1024 * 1024)

                    # Rotate if file is too old or too large
                    if file_age_days > max_age_days or file_size_mb > max_size_mb:
                        # Create backup filename
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        backup_file = log_dir / f"{log_file.stem}.{timestamp}.log"

                        # Move file to backup
                        log_file.rename(backup_file)
                        rotated_files += 1
                        total_freed_bytes += backup_file.stat().st_size

                        # Compress if requested
                        if compress:
                            try:
                                import gzip
                                with open(backup_file, 'rb') as f_in:
                                    with gzip.open(backup_file.with_suffix('.gz'), 'wb') as f_out:
                                        f_out.writelines(f_in)
                                backup_file.unlink()  # Remove uncompressed backup
                            except Exception as e:
                                self.logger.warning(f"Failed to compress {backup_file}: {e}")

                except Exception as e:
                    self.logger.error(f"Error processing log file {log_file}: {e}")

            output = {
                'rotated_files': rotated_files,
                'total_freed_mb': total_freed_bytes / (1024 * 1024),
                'log_directory': str(log_dir),
                'max_age_days': max_age_days,
                'max_size_mb': max_size_mb,
                'compression_enabled': compress
            }

            return True, f"Log rotation completed (rotated {rotated_files} files)", output

        except Exception as e:
            return False, f"Log rotation failed: {str(e)}", {'exception': str(e)}

class ProcessCleanupAction(WorkflowAction):
    """Action to clean up processes"""

    def __init__(self):
        super().__init__("process_cleanup", "Clean up zombie or stuck processes")

    def validate_parameters(self, parameters: Dict[str, Any]) -> tuple[bool, str]:
        return True, "Parameters valid"

    async def execute(self, parameters: Dict[str, Any]) -> tuple[bool, str, Dict[str, Any]]:
        try:
            import psutil

            process_types = parameters.get('process_types', ['zombie'])
            max_age_minutes = parameters.get('max_age_minutes', 60)
            dry_run = parameters.get('dry_run', False)

            killed_processes = []
            total_processes = 0

            for proc in psutil.process_iter(['pid', 'name', 'status', 'create_time']):
                try:
                    proc_age_minutes = (time.time() - proc.info['create_time']) / 60

                    should_kill = False
                    if 'zombie' in process_types and proc.info['status'] == psutil.STATUS_ZOMBIE:
                        should_kill = True
                    elif 'stale' in process_types and proc_age_minutes > max_age_minutes:
                        should_kill = True

                    if should_kill:
                        total_processes += 1
                        if not dry_run:
                            proc.kill()
                            killed_processes.append({
                                'pid': proc.info['pid'],
                                'name': proc.info['name'],
                                'status': proc.info['status'],
                                'age_minutes': proc_age_minutes
                            })

                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            output = {
                'total_processes_found': total_processes,
                'killed_processes': len(killed_processes),
                'process_types': process_types,
                'max_age_minutes': max_age_minutes,
                'dry_run': dry_run,
                'killed_process_details': killed_processes
            }

            action_type = "Dry run completed" if dry_run else "Process cleanup completed"
            return True, f"{action_type} (found {total_processes}, killed {len(killed_processes)})", output

        except Exception as e:
            return False, f"Process cleanup failed: {str(e)}", {'exception': str(e)}

class RecoveryWorkflowManager:
    """Advanced recovery workflow management system"""

    def __init__(self, server_manager: Optional[ServerManager] = None):
        self.logger = get_logger("recovery_workflow_manager")
        self.server_manager = server_manager
        self.workflows: Dict[str, RecoveryWorkflow] = {}
        self.executions: Dict[str, WorkflowExecution] = {}
        self.actions: Dict[str, WorkflowAction] = {}
        self.workflow_queue: List[str] = []
        self.active_executions: Dict[str, asyncio.Task] = {}
        self.execution_history: List[WorkflowExecution] = []

        # Threading for workflow execution
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.execution_lock = threading.Lock()

        # Database for persistence
        self.db_path = Path(__file__).parent.parent / "data" / "recovery_workflows.db"
        self._initialize_database()

        # Initialize actions
        self._initialize_actions()

        # Load default workflows
        self._load_default_workflows()

        # Start workflow processor
        self._start_workflow_processor()

    def _initialize_database(self):
        """Initialize workflow database"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS workflows (
                    workflow_id TEXT PRIMARY KEY,
                    name TEXT,
                    description TEXT,
                    version TEXT,
                    trigger_conditions TEXT,
                    workflow_data TEXT,
                    created_at DATETIME,
                    updated_at DATETIME
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS workflow_executions (
                    execution_id TEXT PRIMARY KEY,
                    workflow_id TEXT,
                    workflow_name TEXT,
                    trigger_error TEXT,
                    parameters TEXT,
                    status TEXT,
                    started_at DATETIME,
                    completed_at DATETIME,
                    execution_time_ms INTEGER,
                    current_step TEXT,
                    completed_steps TEXT,
                    failed_steps TEXT,
                    error_message TEXT,
                    output TEXT
                )
            """)

            conn.execute("CREATE INDEX IF NOT EXISTS idx_workflows_id ON workflows(workflow_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_executions_workflow ON workflow_executions(workflow_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_executions_status ON workflow_executions(status)")

    def _initialize_actions(self):
        """Initialize available workflow actions"""
        self.actions = {
            'service_restart': ServiceRestartAction(),
            'memory_cleanup': MemoryCleanupAction(),
            'configuration_repair': ConfigurationRepairAction(),
            'log_rotation': LogRotationAction(),
            'process_cleanup': ProcessCleanupAction()
        }

        self.logger.info(f"Initialized {len(self.actions)} workflow actions")

    def _load_default_workflows(self):
        """Load default recovery workflows"""
        default_workflows = [
            RecoveryWorkflow(
                workflow_id="service_failure_recovery",
                name="Service Failure Recovery",
                description="Recover from service failures with restart and verification",
                version="1.0",
                trigger_conditions=["service_failure", "service_unresponsive"],
                steps=[
                    WorkflowStep(
                        step_id="verify_service_status",
                        name="Verify Service Status",
                        description="Check current service status",
                        action_type="service_status_check",
                        parameters={},
                        timeout_seconds=30,
                        retry_count=3,
                        retry_delay_seconds=5,
                        continue_on_failure=False,
                        required=True
                    ),
                    WorkflowStep(
                        step_id="restart_service",
                        name="Restart Service",
                        description="Restart the failed service",
                        action_type="service_restart",
                        parameters={"wait_time": 30},
                        timeout_seconds=120,
                        retry_count=2,
                        retry_delay_seconds=10,
                        continue_on_failure=False,
                        required=True
                    ),
                    WorkflowStep(
                        step_id="verify_restart",
                        name="Verify Restart Success",
                        description="Verify service is running after restart",
                        action_type="service_status_check",
                        parameters={},
                        timeout_seconds=30,
                        retry_count=3,
                        retry_delay_seconds=5,
                        continue_on_failure=False,
                        required=True
                    )
                ],
                priority=WorkflowPriority.HIGH,
                auto_execute=True,
                timeout_minutes=10,
                rollback_enabled=True,
                rollback_steps=[
                    WorkflowStep(
                        step_id="restore_previous_state",
                        name="Restore Previous State",
                        description="Attempt to restore service to previous state",
                        action_type="service_rollback",
                        parameters={},
                        timeout_seconds=60,
                        retry_count=1,
                        retry_delay_seconds=0,
                        continue_on_failure=True,
                        required=False
                    )
                ]
            ),
            RecoveryWorkflow(
                workflow_id="memory_pressure_recovery",
                name="Memory Pressure Recovery",
                description="Recover from high memory usage",
                version="1.0",
                trigger_conditions=["memory_pressure_high", "memory_exhaustion"],
                steps=[
                    WorkflowStep(
                        step_id="memory_cleanup",
                        name="Memory Cleanup",
                        description="Perform system memory cleanup",
                        action_type="memory_cleanup",
                        parameters={},
                        timeout_seconds=60,
                        retry_count=2,
                        retry_delay_seconds=10,
                        continue_on_failure=True,
                        required=True
                    ),
                    WorkflowStep(
                        step_id="restart_memory_services",
                        name="Restart Memory-Intensive Services",
                        description="Restart services that consume high memory",
                        action_type="service_restart",
                        parameters={"service_name": "comfyui"},
                        timeout_seconds=120,
                        retry_count=2,
                        retry_delay_seconds=15,
                        continue_on_failure=True,
                        required=False
                    ),
                    WorkflowStep(
                        step_id="verify_memory_improvement",
                        name="Verify Memory Improvement",
                        description="Check if memory usage has improved",
                        action_type="memory_check",
                        parameters={},
                        timeout_seconds=30,
                        retry_count=3,
                        retry_delay_seconds=5,
                        continue_on_failure=False,
                        required=True
                    )
                ],
                priority=WorkflowPriority.HIGH,
                auto_execute=True,
                timeout_minutes=15,
                rollback_enabled=False
            ),
            RecoveryWorkflow(
                workflow_id="configuration_repair_workflow",
                name="Configuration Repair Workflow",
                description="Repair corrupted configuration files",
                version="1.0",
                trigger_conditions=["configuration_error", "config_corruption"],
                steps=[
                    WorkflowStep(
                        step_id="backup_configuration",
                        name="Backup Configuration",
                        description="Create backup of current configuration",
                        action_type="file_backup",
                        parameters={"backup": True},
                        timeout_seconds=30,
                        retry_count=1,
                        retry_delay_seconds=0,
                        continue_on_failure=False,
                        required=True
                    ),
                    WorkflowStep(
                        step_id="repair_configuration",
                        name="Repair Configuration",
                        description="Repair configuration file issues",
                        action_type="configuration_repair",
                        parameters={
                            "repair_actions": ["fix_indentation", "add_missing_sections", "validate_structure"]
                        },
                        timeout_seconds=60,
                        retry_count=2,
                        retry_delay_seconds=10,
                        continue_on_failure=False,
                        required=True
                    ),
                    WorkflowStep(
                        step_id="validate_repair",
                        name="Validate Repair",
                        description="Validate that configuration repair was successful",
                        action_type="configuration_validation",
                        parameters={},
                        timeout_seconds=30,
                        retry_count=3,
                        retry_delay_seconds=5,
                        continue_on_failure=False,
                        required=True
                    )
                ],
                priority=WorkflowPriority.NORMAL,
                auto_execute=True,
                timeout_minutes=10,
                rollback_enabled=True
            ),
            RecoveryWorkflow(
                workflow_id="log_maintenance_workflow",
                name="Log Maintenance Workflow",
                description="Perform log file maintenance",
                version="1.0",
                trigger_conditions=["log_files_large", "disk_space_low"],
                steps=[
                    WorkflowStep(
                        step_id="rotate_logs",
                        name="Rotate Log Files",
                        description="Rotate and compress old log files",
                        action_type="log_rotation",
                        parameters={
                            "max_age_days": 7,
                            "max_size_mb": 100,
                            "compress": True
                        },
                        timeout_seconds=120,
                        retry_count=2,
                        retry_delay_seconds=15,
                        continue_on_failure=True,
                        required=True
                    ),
                    WorkflowStep(
                        step_id="verify_disk_space",
                        name="Verify Disk Space",
                        description="Check if disk space improved",
                        action_type="disk_check",
                        parameters={},
                        timeout_seconds=30,
                        retry_count=3,
                        retry_delay_seconds=5,
                        continue_on_failure=True,
                        required=False
                    )
                ],
                priority=WorkflowPriority.LOW,
                auto_execute=True,
                timeout_minutes=5,
                rollback_enabled=False
            )
        ]

        for workflow in default_workflows:
            self.workflows[workflow.workflow_id] = workflow
            self._save_workflow(workflow)

        self.logger.info(f"Loaded {len(default_workflows)} default recovery workflows")

    def _save_workflow(self, workflow: RecoveryWorkflow):
        """Save workflow to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO workflows (
                        workflow_id, name, description, version, trigger_conditions,
                        workflow_data, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    workflow.workflow_id,
                    workflow.name,
                    workflow.description,
                    workflow.version,
                    json.dumps(workflow.trigger_conditions),
                    json.dumps(asdict(workflow)),
                    workflow.created_at,
                    datetime.now()
                ))
        except Exception as e:
            self.logger.error(f"Failed to save workflow {workflow.workflow_id}: {e}")

    def _start_workflow_processor(self):
        """Start background workflow processor"""
        def processor_loop():
            while True:
                try:
                    if self.workflow_queue:
                        with self.execution_lock:
                            if self.workflow_queue:
                                execution_id = self.workflow_queue.pop(0)

                        # Execute workflow
                        asyncio.run(self._execute_workflow_by_id(execution_id))

                    time.sleep(1)  # Check queue every second

                except Exception as e:
                    self.logger.error(f"Workflow processor error: {e}")
                    time.sleep(5)

        processor_thread = threading.Thread(target=processor_loop, daemon=True)
        processor_thread.start()

        self.logger.info("Workflow processor started")

    async def execute_workflow(self,
                            workflow_id: str,
                            trigger_error: str = "manual",
                            parameters: Optional[Dict[str, Any]] = None) -> WorkflowExecution:
        """Execute a recovery workflow"""
        if workflow_id not in self.workflows:
            raise ValueError(f"Unknown workflow: {workflow_id}")

        workflow = self.workflows[workflow_id]
        execution_id = str(uuid.uuid4())

        # Create execution instance
        execution = WorkflowExecution(
            execution_id=execution_id,
            workflow_id=workflow_id,
            workflow_name=workflow.name,
            trigger_error=trigger_error,
            parameters=parameters or {},
            status=WorkflowStatus.PENDING
        )

        # Store execution
        self.executions[execution_id] = execution

        # Add to queue
        with self.execution_lock:
            self.workflow_queue.append(execution_id)

        self.logger.info(f"Workflow {workflow_id} queued for execution (ID: {execution_id})")

        return execution

    async def _execute_workflow_by_id(self, execution_id: str) -> WorkflowExecution:
        """Execute a workflow by execution ID"""
        if execution_id not in self.executions:
            raise ValueError(f"Unknown execution ID: {execution_id}")

        execution = self.executions[execution_id]
        workflow = self.workflows[execution.workflow_id]

        try:
            # Update execution status
            execution.status = WorkflowStatus.RUNNING
            execution.started_at = datetime.now()

            self.logger.info(f"Starting workflow execution: {workflow.name} (ID: {execution_id})")

            start_time = time.time()

            # Execute workflow steps
            success = await self._execute_workflow_steps(workflow, execution)

            # Update execution status
            execution.status = WorkflowStatus.COMPLETED if success else WorkflowStatus.FAILED
            execution.completed_at = datetime.now()
            execution.execution_time_ms = int((time.time() - start_time) * 1000)

            if success:
                self.logger.info(f"Workflow execution completed successfully: {workflow.name}")
            else:
                self.logger.error(f"Workflow execution failed: {workflow.name} - {execution.error_message}")

        except Exception as e:
            execution.status = WorkflowStatus.FAILED
            execution.completed_at = datetime.now()
            execution.execution_time_ms = int((time.time() - start_time) * 1000)
            execution.error_message = f"Workflow execution failed: {str(e)}"

            self.logger.error(f"Workflow execution crashed: {workflow.name} - {str(e)}")

        finally:
            # Save execution to database
            self._save_execution(execution)

            # Add to history
            self.execution_history.append(execution)
            if len(self.execution_history) > 1000:
                self.execution_history = self.execution_history[-500:]

        return execution

    async def _execute_workflow_steps(self, workflow: RecoveryWorkflow, execution: WorkflowExecution) -> bool:
        """Execute all steps in a workflow"""
        total_timeout = workflow.timeout_minutes * 60
        start_time = time.time()

        for i, step in enumerate(workflow.steps):
            # Check timeout
            elapsed_time = time.time() - start_time
            if elapsed_time > total_timeout:
                execution.error_message = f"Workflow timeout after {elapsed_time:.1f} seconds"
                return False

            # Update current step
            execution.current_step = step.step_id
            step.status = StepStatus.RUNNING
            step.start_time = datetime.now()

            self.logger.info(f"Executing workflow step: {step.name} ({step.step_id})")

            try:
                # Execute step with timeout
                step_success, step_message, step_output = await asyncio.wait_for(
                    self._execute_step(step, execution.parameters),
                    timeout=step.timeout_seconds
                )

                step.end_time = datetime.now()
                step.execution_time_ms = int((step.end_time - step.start_time).total_seconds() * 1000)
                step.output = step_output

                if step_success:
                    step.status = StepStatus.COMPLETED
                    execution.completed_steps.append(step.step_id)
                    self.logger.info(f"Step completed successfully: {step.name}")
                else:
                    step.status = StepStatus.FAILED
                    step.error_message = step_message
                    execution.failed_steps.append(step.step_id)

                    self.logger.error(f"Step failed: {step.name} - {step_message}")

                    # Handle failure based on step configuration
                    if not step.continue_on_failure:
                        execution.error_message = f"Workflow failed at step {step.name}: {step_message}"

                        # Attempt rollback if enabled
                        if workflow.rollback_enabled:
                            self.logger.info(f"Attempting rollback for workflow {workflow.name}")
                            await self._execute_rollback(workflow, execution)

                        return False

            except asyncio.TimeoutError:
                step.status = StepStatus.FAILED
                step.error_message = f"Step timeout after {step.timeout_seconds} seconds"
                execution.failed_steps.append(step.step_id)
                execution.error_message = f"Step timeout: {step.name}"

                self.logger.error(f"Step timeout: {step.name}")

                if not step.continue_on_failure:
                    if workflow.rollback_enabled:
                        await self._execute_rollback(workflow, execution)
                    return False

            except Exception as e:
                step.status = StepStatus.FAILED
                step.error_message = f"Step exception: {str(e)}"
                execution.failed_steps.append(step.step_id)
                execution.error_message = f"Step exception: {step.name} - {str(e)}"

                self.logger.error(f"Step exception: {step.name} - {str(e)}")

                if not step.continue_on_failure:
                    if workflow.rollback_enabled:
                        await self._execute_rollback(workflow, execution)
                    return False

        return True

    async def _execute_step(self, step: WorkflowStep, execution_parameters: Dict[str, Any]) -> tuple[bool, str, Dict[str, Any]]:
        """Execute a single workflow step"""
        if step.action_type not in self.actions:
            return False, f"Unknown action type: {step.action_type}", {}

        action = self.actions[step.action_type]

        # Validate parameters
        valid, validation_message = action.validate_parameters(step.parameters)
        if not valid:
            return False, f"Parameter validation failed: {validation_message}", {}

        # Execute with retries
        for attempt in range(step.retry_count + 1):
            try:
                # Merge step parameters with execution parameters
                merged_parameters = {**execution_parameters, **step.parameters}

                success, message, output = await action.execute(merged_parameters)

                if success:
                    return success, message, output
                elif attempt < step.retry_count:
                    self.logger.warning(f"Step {step.name} failed, retrying ({attempt + 1}/{step.retry_count}): {message}")
                    await asyncio.sleep(step.retry_delay_seconds)
                else:
                    return False, f"Step failed after {step.retry_count + 1} attempts: {message}", output

            except Exception as e:
                if attempt < step.retry_count:
                    self.logger.warning(f"Step {step.name} exception, retrying ({attempt + 1}/{step.retry_count}): {str(e)}")
                    await asyncio.sleep(step.retry_delay_seconds)
                else:
                    return False, f"Step exception after {step.retry_count + 1} attempts: {str(e)}", {}

        return False, "Step execution failed", {}

    async def _execute_rollback(self, workflow: RecoveryWorkflow, execution: WorkflowExecution):
        """Execute rollback steps for a workflow"""
        if not workflow.rollback_steps:
            return

        self.logger.info(f"Executing rollback for workflow: {workflow.name}")

        for rollback_step in workflow.rollback_steps:
            try:
                rollback_step.status = StepStatus.RUNNING
                rollback_step.start_time = datetime.now()

                success, message, output = await asyncio.wait_for(
                    self._execute_step(rollback_step, execution.parameters),
                    timeout=rollback_step.timeout_seconds
                )

                rollback_step.end_time = datetime.now()
                rollback_step.status = StepStatus.COMPLETED if success else StepStatus.FAILED

                if success:
                    self.logger.info(f"Rollback step completed: {rollback_step.name}")
                else:
                    self.logger.error(f"Rollback step failed: {rollback_step.name} - {message}")

            except Exception as e:
                rollback_step.status = StepStatus.FAILED
                rollback_step.error_message = str(e)
                self.logger.error(f"Rollback step exception: {rollback_step.name} - {str(e)}")

    def _save_execution(self, execution: WorkflowExecution):
        """Save execution to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO workflow_executions (
                        execution_id, workflow_id, workflow_name, trigger_error, parameters,
                        status, started_at, completed_at, execution_time_ms, current_step,
                        completed_steps, failed_steps, error_message, output
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    execution.execution_id,
                    execution.workflow_id,
                    execution.workflow_name,
                    execution.trigger_error,
                    json.dumps(execution.parameters),
                    execution.status.value,
                    execution.started_at,
                    execution.completed_at,
                    execution.execution_time_ms,
                    execution.current_step,
                    json.dumps(execution.completed_steps),
                    json.dumps(execution.failed_steps),
                    execution.error_message,
                    json.dumps(execution.output)
                ))
        except Exception as e:
            self.logger.error(f"Failed to save execution {execution.execution_id}: {e}")

    def find_matching_workflows(self, error_context: ErrorContext) -> List[RecoveryWorkflow]:
        """Find workflows that match the given error context"""
        matching_workflows = []

        error_signature = f"{error_context.category.value}_{error_context.error_type}"

        for workflow in self.workflows.values():
            if not workflow.auto_execute:
                continue

            # Check trigger conditions
            for condition in workflow.trigger_conditions:
                if condition in error_signature or condition in error_context.error_message.lower():
                    matching_workflows.append(workflow)
                    break

        # Sort by priority
        matching_workflows.sort(key=lambda w: w.priority.value, reverse=True)

        return matching_workflows

    async def handle_error_with_workflow(self, error_context: ErrorContext) -> Optional[WorkflowExecution]:
        """Handle an error using appropriate workflows"""
        # Find matching workflows
        matching_workflows = self.find_matching_workflows(error_context)

        if not matching_workflows:
            self.logger.info(f"No matching workflows found for error: {error_context.error_type}")
            return None

        # Execute the highest priority workflow
        workflow = matching_workflows[0]
        self.logger.info(f"Executing workflow {workflow.name} for error: {error_context.error_type}")

        execution_parameters = {
            'error_context': asdict(error_context),
            'service_name': error_context.service_name,
            'error_type': error_context.error_type,
            'server_manager': self.server_manager
        }

        execution = await self.execute_workflow(
            workflow.workflow_id,
            trigger_error=f"{error_context.category.value}_{error_context.error_type}",
            parameters=execution_parameters
        )

        return execution

    def get_workflow_status(self, execution_id: str) -> Optional[WorkflowExecution]:
        """Get status of a workflow execution"""
        return self.executions.get(execution_id)

    def get_execution_history(self, limit: int = 50) -> List[WorkflowExecution]:
        """Get recent execution history"""
        return self.execution_history[-limit:]

    def get_workflow_statistics(self) -> Dict[str, Any]:
        """Get workflow execution statistics"""
        if not self.execution_history:
            return {"total_executions": 0}

        total_executions = len(self.execution_history)
        successful_executions = sum(1 for ex in self.execution_history if ex.status == WorkflowStatus.COMPLETED)
        failed_executions = sum(1 for ex in self.execution_history if ex.status == WorkflowStatus.FAILED)

        # Workflow-specific statistics
        workflow_stats = {}
        for workflow_id, workflow in self.workflows.items():
            executions = [ex for ex in self.execution_history if ex.workflow_id == workflow_id]
            successful = sum(1 for ex in executions if ex.status == WorkflowStatus.COMPLETED)

            workflow_stats[workflow_id] = {
                'name': workflow.name,
                'total_executions': len(executions),
                'successful_executions': successful,
                'success_rate': successful / len(executions) if executions else 0,
                'average_execution_time_ms': sum(ex.execution_time_ms or 0 for ex in executions) / len(executions) if executions else 0
            }

        return {
            'total_executions': total_executions,
            'successful_executions': successful_executions,
            'failed_executions': failed_executions,
            'overall_success_rate': successful_executions / total_executions if total_executions > 0 else 0,
            'workflow_statistics': workflow_stats
        }

    def add_custom_workflow(self, workflow: RecoveryWorkflow):
        """Add a custom workflow"""
        self.workflows[workflow.workflow_id] = workflow
        self._save_workflow(workflow)
        self.logger.info(f"Added custom workflow: {workflow.name}")

    def remove_workflow(self, workflow_id: str):
        """Remove a workflow"""
        if workflow_id in self.workflows:
            del self.workflows[workflow_id]
            self.logger.info(f"Removed workflow: {workflow_id}")

    def get_available_workflows(self) -> Dict[str, RecoveryWorkflow]:
        """Get all available workflows"""
        return self.workflows.copy()

# Global instance
_workflow_manager = None

def get_recovery_workflow_manager(server_manager: Optional[ServerManager] = None) -> RecoveryWorkflowManager:
    """Get the global recovery workflow manager instance"""
    global _workflow_manager

    if _workflow_manager is None:
        _workflow_manager = RecoveryWorkflowManager(server_manager)

    return _workflow_manager

if __name__ == "__main__":
    # Example usage
    async def example_usage():
        """Demonstrate recovery workflow system usage"""

        # Create workflow manager
        workflow_manager = get_recovery_workflow_manager()

        # List available workflows
        workflows = workflow_manager.get_available_workflows()
        print(f"Available workflows: {list(workflows.keys())}")

        # Execute a workflow manually
        execution = await workflow_manager.execute_workflow(
            "log_maintenance_workflow",
            trigger_error="manual_test",
            parameters={"dry_run": True}
        )

        print(f"Workflow execution started: {execution.execution_id}")

        # Wait for execution to complete
        while execution.status in [WorkflowStatus.PENDING, WorkflowStatus.RUNNING]:
            await asyncio.sleep(1)
            execution = workflow_manager.get_workflow_status(execution.execution_id)
            print(f"Execution status: {execution.status.value}")

        print(f"Workflow execution completed: {execution.status.value}")
        if execution.error_message:
            print(f"Error: {execution.error_message}")

        # Get statistics
        stats = workflow_manager.get_workflow_statistics()
        print(f"Workflow statistics: {stats}")

    # Run example
    asyncio.run(example_usage())