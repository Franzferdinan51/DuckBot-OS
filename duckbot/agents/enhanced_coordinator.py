"""
Enhanced Agent Coordination Framework
AP2-inspired advanced agent coordination patterns for DuckBot v4.2

Features:
- Advanced agent discovery and registration
- Dynamic capability matching
- Intelligent task routing and distribution
- Agent collaboration and knowledge sharing
- Performance monitoring and optimization
- Cross-agent communication protocols
- Fault tolerance and recovery

Author: Enhanced Agent Framework Module
Version: 1.0.0
"""

import asyncio
import json
import time
import logging
from typing import Dict, List, Optional, Any, Set, Callable, AsyncGenerator
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime, timedelta
from pathlib import Path
import uuid
import hashlib
import weakref
from concurrent.futures import ThreadPoolExecutor
import queue
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class AgentCapability(Enum):
    """Enhanced agent capabilities based on AP2 patterns"""
    # Core capabilities
    TASK_EXECUTION = "task_execution"
    KNOWLEDGE_RETRIEVAL = "knowledge_retrieval"
    DECISION_MAKING = "decision_making"
    LEARNING = "learning"

    # Specialized capabilities
    CODE_GENERATION = "code_generation"
    DATA_ANALYSIS = "data_analysis"
    COMMUNICATION = "communication"
    COORDINATION = "coordination"
    MONITORING = "monitoring"
    OPTIMIZATION = "optimization"

    # Advanced capabilities
    PREDICTION = "prediction"
    PLANNING = "planning"
    NEGOTIATION = "negotiation"
    COLLABORATION = "collaboration"
    ADAPTATION = "adaptation"

class AgentStatus(Enum):
    """Agent status states"""
    OFFLINE = "offline"
    STARTING = "starting"
    ONLINE = "online"
    BUSY = "busy"
    MAINTENANCE = "maintenance"
    ERROR = "error"
    TERMINATING = "terminating"

class TaskPriority(Enum):
    """Task priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4
    EMERGENCY = 5

class CollaborationMode(Enum):
    """Agent collaboration modes"""
    INDEPENDENT = "independent"
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    HIERARCHICAL = "hierarchical"
    CONSENSUS = "consensus"

@dataclass
class AgentCapabilitySpec:
    """Detailed capability specification"""
    capability: AgentCapability
    proficiency: float  # 0.0 to 1.0
    experience: int  # Number of tasks handled
    last_used: Optional[datetime] = None
    success_rate: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AgentMetrics:
    """Agent performance metrics"""
    tasks_completed: int = 0
    tasks_failed: int = 0
    avg_response_time: float = 0.0
    avg_success_rate: float = 0.0
    uptime_percentage: float = 100.0
    resource_usage: Dict[str, float] = field(default_factory=dict)
    last_activity: Optional[datetime] = None

    @property
    def total_tasks(self) -> int:
        return self.tasks_completed + self.tasks_failed

    @property
    def success_rate(self) -> float:
        if self.total_tasks == 0:
            return 0.0
        return self.tasks_completed / self.total_tasks

@dataclass
class EnhancedAgentTask:
    """Enhanced task structure with AP2-inspired features"""
    id: str
    title: str
    description: str
    required_capabilities: List[AgentCapability]
    priority: TaskPriority = TaskPriority.NORMAL
    collaboration_mode: CollaborationMode = CollaborationMode.INDEPENDENT

    # Task metadata
    created_at: datetime = field(default_factory=datetime.now)
    deadline: Optional[datetime] = None
    estimated_duration: Optional[timedelta] = None
    actual_duration: Optional[timedelta] = None

    # Execution state
    status: str = "pending"
    assigned_agents: List[str] = field(default_factory=list)
    progress: float = 0.0
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    # Dependencies and relationships
    dependencies: List[str] = field(default_factory=list)
    subtasks: List[str] = field(default_factory=list)
    parent_task: Optional[str] = None

    # Context and data
    context: Dict[str, Any] = field(default_factory=dict)
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)

    # Collaboration and sharing
    shared_state: Dict[str, Any] = field(default_factory=dict)
    collaboration_history: List[Dict[str, Any]] = field(default_factory=list)

    # Caching and optimization
    cache_key: Optional[str] = None
    is_cacheable: bool = True
    cache_ttl: Optional[timedelta] = None

@dataclass
class AgentManifest:
    """Agent manifest for discovery and registration"""
    agent_id: str
    name: str
    version: str
    description: str
    capabilities: List[AgentCapabilitySpec]
    status: AgentStatus = AgentStatus.OFFLINE
    endpoint: Optional[str] = None
    max_concurrent_tasks: int = 5
    supported_protocols: List[str] = field(default_factory=list)

    # Performance and health
    metrics: AgentMetrics = field(default_factory=AgentMetrics)
    health_check_interval: int = 30  # seconds
    last_health_check: Optional[datetime] = None

    # Resource requirements
    cpu_requirement: Optional[float] = None
    memory_requirement: Optional[float] = None
    gpu_requirement: Optional[float] = None

    # Availability and scheduling
    available_schedule: Dict[str, str] = field(default_factory=dict)  # day -> time ranges
    timezone: str = "UTC"

    # Security and authorization
    required_permissions: List[str] = field(default_factory=list)
    security_clearance: int = 0

    # Metadata
    tags: List[str] = field(default_factory=list)
    contact_info: Optional[Dict[str, str]] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

class BaseEnhancedAgent(ABC):
    """Base class for enhanced agents with AP2-inspired capabilities"""

    def __init__(self, manifest: AgentManifest):
        self.manifest = manifest
        self.task_queue = asyncio.Queue()
        self.active_tasks: Dict[str, EnhancedAgentTask] = {}
        self.is_running = False
        self.executor = ThreadPoolExecutor(max_workers=manifest.max_concurrent_tasks)

        # Knowledge and learning
        self.knowledge_base: Dict[str, Any] = {}
        self.learning_history: List[Dict[str, Any]] = []
        self.collaboration_peers: Set[str] = set()

        # Performance tracking
        self.task_start_times: Dict[str, datetime] = {}
        self.performance_history: List[Dict[str, Any]] = []

    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the agent"""
        pass

    @abstractmethod
    async def execute_task(self, task: EnhancedAgentTask) -> Dict[str, Any]:
        """Execute a specific task"""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Perform health check"""
        pass

    async def start(self):
        """Start the agent"""
        self.is_running = True
        self.manifest.status = AgentStatus.STARTING

        if await self.initialize():
            self.manifest.status = AgentStatus.ONLINE
            logger.info(f"Agent {self.manifest.name} started successfully")

            # Start task processing loop
            asyncio.create_task(self._task_processing_loop())

            # Start health check loop
            asyncio.create_task(self._health_check_loop())
        else:
            self.manifest.status = AgentStatus.ERROR
            logger.error(f"Failed to start agent {self.manifest.name}")

    async def stop(self):
        """Stop the agent"""
        self.manifest.status = AgentStatus.TERMINATING
        self.is_running = False

        # Cancel all active tasks
        for task in self.active_tasks.values():
            task.status = "cancelled"

        # Shutdown executor
        self.executor.shutdown(wait=True)

        self.manifest.status = AgentStatus.OFFLINE
        logger.info(f"Agent {self.manifest.name} stopped")

    async def _task_processing_loop(self):
        """Main task processing loop"""
        while self.is_running:
            try:
                task = await asyncio.wait_for(self.task_queue.get(), timeout=1.0)

                # Update agent status
                if len(self.active_tasks) >= self.manifest.max_concurrent_tasks:
                    self.manifest.status = AgentStatus.BUSY
                else:
                    self.manifest.status = AgentStatus.ONLINE

                # Execute task
                asyncio.create_task(self._execute_task_safely(task))

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error in task processing loop: {e}")

    async def _execute_task_safely(self, task: EnhancedAgentTask):
        """Execute task with error handling and metrics"""
        task_id = task.id
        self.active_tasks[task_id] = task
        self.task_start_times[task_id] = datetime.now()

        try:
            # Update task status
            task.status = "in_progress"
            task.assigned_agents.append(self.manifest.agent_id)

            # Execute the task
            result = await self.execute_task(task)

            # Update task and metrics
            task.status = "completed"
            task.result = result
            task.progress = 100.0
            task.actual_duration = datetime.now() - self.task_start_times[task_id]

            # Update agent metrics
            self.manifest.metrics.tasks_completed += 1
            self._update_performance_metrics(task, success=True)

            logger.info(f"Task {task_id} completed successfully by {self.manifest.name}")

        except Exception as e:
            # Handle task failure
            task.status = "failed"
            task.error = str(e)

            # Update agent metrics
            self.manifest.metrics.tasks_failed += 1
            self._update_performance_metrics(task, success=False)

            logger.error(f"Task {task_id} failed in {self.manifest.name}: {e}")

        finally:
            # Cleanup
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]
            if task_id in self.task_start_times:
                del self.task_start_times[task_id]

            # Update agent status
            if len(self.active_tasks) < self.manifest.max_concurrent_tasks:
                self.manifest.status = AgentStatus.ONLINE

    async def _health_check_loop(self):
        """Periodic health check loop"""
        while self.is_running:
            try:
                await asyncio.sleep(self.manifest.health_check_interval)

                is_healthy = await self.health_check()
                self.manifest.last_health_check = datetime.now()

                if not is_healthy:
                    logger.warning(f"Health check failed for agent {self.manifest.name}")
                    # Implement recovery logic here

            except Exception as e:
                logger.error(f"Error in health check loop: {e}")

    def _update_performance_metrics(self, task: EnhancedAgentTask, success: bool):
        """Update agent performance metrics"""
        if task.id in self.task_start_times:
            duration = (datetime.now() - self.task_start_times[task.id]).total_seconds()

            # Update average response time
            total_tasks = self.manifest.metrics.total_tasks
            current_avg = self.manifest.metrics.avg_response_time
            self.manifest.metrics.avg_response_time = (
                (current_avg * (total_tasks - 1) + duration) / total_tasks
            )

        # Update success rate
        self.manifest.metrics.avg_success_rate = self.manifest.metrics.success_rate

        # Update last activity
        self.manifest.metrics.last_activity = datetime.now()

        # Record performance history
        self.performance_history.append({
            "timestamp": datetime.now(),
            "task_id": task.id,
            "success": success,
            "duration": task.actual_duration.total_seconds() if task.actual_duration else 0,
            "capabilities_used": [cap.value for cap in task.required_capabilities]
        })

        # Limit history size
        if len(self.performance_history) > 1000:
            self.performance_history = self.performance_history[-500:]

    async def add_knowledge(self, key: str, value: Any, metadata: Dict[str, Any] = None):
        """Add knowledge to agent's knowledge base"""
        self.knowledge_base[key] = {
            "value": value,
            "metadata": metadata or {},
            "created_at": datetime.now(),
            "access_count": 0
        }

    async def get_knowledge(self, key: str) -> Optional[Any]:
        """Retrieve knowledge from agent's knowledge base"""
        if key in self.knowledge_base:
            knowledge = self.knowledge_base[key]
            knowledge["access_count"] += 1
            return knowledge["value"]
        return None

    def can_handle_task(self, task: EnhancedAgentTask) -> float:
        """Calculate capability match score for task"""
        if not task.required_capabilities:
            return 0.5  # Neutral score for no specific requirements

        total_score = 0.0
        matched_capabilities = 0

        for req_capability in task.required_capabilities:
            for agent_cap in self.manifest.capabilities:
                if agent_cap.capability == req_capability:
                    # Score based on proficiency and success rate
                    score = agent_cap.proficiency * agent_cap.success_rate
                    total_score += score
                    matched_capabilities += 1
                    break

        if matched_capabilities == 0:
            return 0.0  # Cannot handle task

        return total_score / matched_capabilities

class EnhancedAgentCoordinator:
    """Advanced agent coordinator with AP2-inspired patterns"""

    def __init__(self):
        self.agents: Dict[str, BaseEnhancedAgent] = {}
        self.agent_manifests: Dict[str, AgentManifest] = {}
        self.tasks: Dict[str, EnhancedAgentTask] = {}
        self.task_queue = asyncio.PriorityQueue()

        # Coordination state
        self.is_running = False
        self.coordination_stats = {
            "tasks_created": 0,
            "tasks_assigned": 0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "avg_assignment_time": 0.0,
            "load_balance_efficiency": 0.0
        }

        # Collaboration management
        self.collaboration_groups: Dict[str, List[str]] = {}
        self.shared_state: Dict[str, Any] = {}

        # Performance optimization
        self.capability_cache: Dict[str, List[str]] = {}  # capability -> agent_ids
        self.performance_history: List[Dict[str, Any]] = []

        # Background services
        self.task_prefetcher = TaskPrefetcher(self)
        self.cache_manager = CacheManager(self)
        self.collaboration_manager = CollaborationManager(self)

    async def initialize(self) -> bool:
        """Initialize the coordinator"""
        try:
            self.is_running = True

            # Start background services
            await self.task_prefetcher.start()
            await self.cache_manager.start()
            await self.collaboration_manager.start()

            # Start coordination loops
            asyncio.create_task(self._task_assignment_loop())
            asyncio.create_task(self._load_balancing_loop())
            asyncio.create_task(self._performance_monitoring_loop())
            asyncio.create_task(self._collaboration_coordination_loop())

            logger.info("Enhanced Agent Coordinator initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize coordinator: {e}")
            return False

    async def register_agent(self, agent: BaseEnhancedAgent) -> bool:
        """Register an agent with the coordinator"""
        try:
            manifest = agent.manifest

            # Check if agent already registered
            if manifest.agent_id in self.agents:
                logger.warning(f"Agent {manifest.agent_id} already registered")
                return False

            # Register agent
            self.agents[manifest.agent_id] = agent
            self.agent_manifests[manifest.agent_id] = manifest

            # Update capability cache
            for cap_spec in manifest.capabilities:
                capability = cap_spec.capability.value
                if capability not in self.capability_cache:
                    self.capability_cache[capability] = []
                self.capability_cache[capability].append(manifest.agent_id)

            # Start the agent
            await agent.start()

            logger.info(f"Agent {manifest.name} registered successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to register agent {agent.manifest.name}: {e}")
            return False

    async def unregister_agent(self, agent_id: str) -> bool:
        """Unregister an agent from the coordinator"""
        try:
            if agent_id not in self.agents:
                logger.warning(f"Agent {agent_id} not found for unregistration")
                return False

            agent = self.agents[agent_id]
            manifest = self.agent_manifests[agent_id]

            # Stop the agent
            await agent.stop()

            # Remove from capability cache
            for cap_spec in manifest.capabilities:
                capability = cap_spec.capability.value
                if capability in self.capability_cache:
                    self.capability_cache[capability].remove(agent_id)
                    if not self.capability_cache[capability]:
                        del self.capability_cache[capability]

            # Remove from agents and manifests
            del self.agents[agent_id]
            del self.agent_manifests[agent_id]

            # Handle active tasks
            for task in self.tasks.values():
                if agent_id in task.assigned_agents:
                    task.assigned_agents.remove(agent_id)
                    if task.status == "in_progress":
                        task.status = "pending"
                        # Reassign task
                        await self._assign_task(task)

            logger.info(f"Agent {manifest.name} unregistered successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to unregister agent {agent_id}: {e}")
            return False

    async def create_task(self, title: str, description: str,
                         required_capabilities: List[AgentCapability],
                         **kwargs) -> str:
        """Create a new task"""
        task_id = str(uuid.uuid4())

        task = EnhancedAgentTask(
            id=task_id,
            title=title,
            description=description,
            required_capabilities=required_capabilities,
            **kwargs
        )

        # Generate cache key if task is cacheable
        if task.is_cacheable:
            cache_data = {
                "title": title,
                "description": description,
                "capabilities": [cap.value for cap in required_capabilities],
                "input_data": task.input_data
            }
            task.cache_key = hashlib.md5(json.dumps(cache_data, sort_keys=True).encode()).hexdigest()

        self.tasks[task_id] = task

        # Add to task queue with priority
        await self.task_queue.put((task.priority.value, task_id))

        # Update stats
        self.coordination_stats["tasks_created"] += 1

        logger.info(f"Task {task_id} created: {title}")
        return task_id

    async def _task_assignment_loop(self):
        """Main task assignment loop"""
        while self.is_running:
            try:
                # Get task from queue
                priority, task_id = await asyncio.wait_for(self.task_queue.get(), timeout=1.0)
                task = self.tasks.get(task_id)

                if not task or task.status != "pending":
                    continue

                # Check cache first
                if task.is_cacheable and task.cache_key:
                    cached_result = await self.cache_manager.get_cached_result(task.cache_key)
                    if cached_result:
                        task.result = cached_result
                        task.status = "completed"
                        task.progress = 100.0
                        self.coordination_stats["tasks_completed"] += 1
                        logger.info(f"Task {task_id} completed from cache")
                        continue

                # Assign task to appropriate agents
                await self._assign_task(task)

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error in task assignment loop: {e}")

    async def _assign_task(self, task: EnhancedAgentTask):
        """Assign task to best-suited agents"""
        start_time = datetime.now()

        # Find best agents for task
        candidate_agents = self._find_candidate_agents(task)

        if not candidate_agents:
            logger.warning(f"No suitable agents found for task {task.id}")
            task.status = "failed"
            task.error = "No suitable agents available"
            return

        # Select agents based on collaboration mode
        if task.collaboration_mode == CollaborationMode.INDEPENDENT:
            # Assign to single best agent
            best_agent_id = candidate_agents[0]
            await self._assign_to_agent(task, best_agent_id)
        else:
            # Assign to multiple agents for collaboration
            for agent_id in candidate_agents[:3]:  # Limit to 3 agents for collaboration
                await self._assign_to_agent(task, agent_id)

        # Update assignment time metric
        assignment_time = (datetime.now() - start_time).total_seconds()
        total_assignments = self.coordination_stats["tasks_assigned"]
        current_avg = self.coordination_stats["avg_assignment_time"]
        self.coordination_stats["avg_assignment_time"] = (
            (current_avg * total_assignments + assignment_time) / (total_assignments + 1)
        )
        self.coordination_stats["tasks_assigned"] += 1

    def _find_candidate_agents(self, task: EnhancedAgentTask) -> List[str]:
        """Find best candidate agents for task"""
        candidate_scores = {}

        for agent_id, manifest in self.agent_manifests.items():
            if manifest.status not in [AgentStatus.ONLINE, AgentStatus.BUSY]:
                continue

            agent = self.agents[agent_id]
            capability_score = agent.can_handle_task(task)

            if capability_score > 0:
                # Consider current load
                load_factor = len(agent.active_tasks) / manifest.max_concurrent_tasks
                load_score = 1.0 - load_factor

                # Consider performance metrics
                performance_score = manifest.metrics.avg_success_rate

                # Consider availability
                availability_score = 1.0 if manifest.status == AgentStatus.ONLINE else 0.5

                # Calculate total score
                total_score = (capability_score * 0.4 +
                             load_score * 0.3 +
                             performance_score * 0.2 +
                             availability_score * 0.1)

                candidate_scores[agent_id] = total_score

        # Sort by score and return agent IDs
        sorted_candidates = sorted(candidate_scores.items(), key=lambda x: x[1], reverse=True)
        return [agent_id for agent_id, score in sorted_candidates]

    async def _assign_to_agent(self, task: EnhancedAgentTask, agent_id: str):
        """Assign task to specific agent"""
        agent = self.agents[agent_id]
        await agent.task_queue.put(task)

    async def _load_balancing_loop(self):
        """Monitor and balance load across agents"""
        while self.is_running:
            try:
                await asyncio.sleep(10)  # Check every 10 seconds

                # Calculate load balance efficiency
                total_capacity = sum(m.max_concurrent_tasks for m in self.agent_manifests.values())
                active_tasks = sum(len(a.active_tasks) for a in self.agents.values())

                if total_capacity > 0:
                    load_percentage = active_tasks / total_capacity
                    self.coordination_stats["load_balance_efficiency"] = 1.0 - abs(0.7 - load_percentage)

                # Detect and handle overload situations
                for agent_id, agent in self.agents.items():
                    manifest = self.agent_manifests[agent_id]

                    # Check if agent is overloaded
                    if len(agent.active_tasks) > manifest.max_concurrent_tasks * 0.8:
                        logger.warning(f"Agent {manifest.name} is approaching capacity limit")

                        # Implement load balancing strategies here
                        await self._balance_agent_load(agent_id)

            except Exception as e:
                logger.error(f"Error in load balancing loop: {e}")

    async def _balance_agent_load(self, overloaded_agent_id: str):
        """Balance load for overloaded agent"""
        overloaded_agent = self.agents[overloaded_agent_id]

        # Find tasks that can be reassigned
        reassigned_tasks = []
        for task in list(overloaded_agent.active_tasks.values()):
            if len(task.assigned_agents) > 1:  # Collaborative task
                continue

            # Find alternative agents
            candidates = self._find_candidate_agents(task)
            candidates = [aid for aid in candidates if aid != overloaded_agent_id]

            if candidates:
                # Reassign task
                await self._assign_to_agent(task, candidates[0])
                reassigned_tasks.append(task.id)

        if reassigned_tasks:
            logger.info(f"Reassigned {len(reassigned_tasks)} tasks from overloaded agent {overloaded_agent_id}")

    async def _performance_monitoring_loop(self):
        """Monitor agent and system performance"""
        while self.is_running:
            try:
                await asyncio.sleep(30)  # Monitor every 30 seconds

                # Collect performance metrics
                performance_snapshot = {
                    "timestamp": datetime.now(),
                    "agents": len(self.agents),
                    "active_tasks": sum(len(a.active_tasks) for a in self.agents.values()),
                    "pending_tasks": len([t for t in self.tasks.values() if t.status == "pending"]),
                    "completed_tasks": len([t for t in self.tasks.values() if t.status == "completed"]),
                    "failed_tasks": len([t for t in self.tasks.values() if t.status == "failed"]),
                    "coordination_stats": self.coordination_stats.copy(),
                    "agent_performance": {}
                }

                # Collect individual agent performance
                for agent_id, manifest in self.agent_manifests.items():
                    performance_snapshot["agent_performance"][agent_id] = {
                        "status": manifest.status.value,
                        "active_tasks": len(self.agents[agent_id].active_tasks),
                        "total_tasks": manifest.metrics.total_tasks,
                        "success_rate": manifest.metrics.success_rate,
                        "avg_response_time": manifest.metrics.avg_response_time
                    }

                self.performance_history.append(performance_snapshot)

                # Limit history size
                if len(self.performance_history) > 1000:
                    self.performance_history = self.performance_history[-500:]

                # Log performance summary
                logger.info(f"Performance snapshot: {performance_snapshot['active_tasks']} active tasks, "
                           f"{performance_snapshot['completed_tasks']} completed, "
                           f"{performance_snapshot['failed_tasks']} failed")

            except Exception as e:
                logger.error(f"Error in performance monitoring loop: {e}")

    async def _collaboration_coordination_loop(self):
        """Coordinate collaboration between agents"""
        while self.is_running:
            try:
                await asyncio.sleep(15)  # Check every 15 seconds

                # Process collaborative tasks
                collaborative_tasks = [t for t in self.tasks.values()
                                     if len(t.assigned_agents) > 1 and t.status == "in_progress"]

                for task in collaborative_tasks:
                    await self._coordinate_collaboration(task)

            except Exception as e:
                logger.error(f"Error in collaboration coordination loop: {e}")

    async def _coordinate_collaboration(self, task: EnhancedAgentTask):
        """Coordinate collaboration for a task"""
        assigned_agents = task.assigned_agents

        # Get agent states
        agent_states = {}
        for agent_id in assigned_agents:
            if agent_id in self.agents:
                agent = self.agents[agent_id]
                agent_states[agent_id] = {
                    "active_tasks": len(agent.active_tasks),
                    "capabilities": [cap.capability.value for cap in agent.manifest.capabilities],
                    "performance": agent.manifest.metrics.success_rate
                }

        # Implement collaboration logic based on mode
        if task.collaboration_mode == CollaborationMode.CONSENSUS:
            await self._coordinate_consensus(task, agent_states)
        elif task.collaboration_mode == CollaborationMode.PARALLEL:
            await self._coordinate_parallel(task, agent_states)
        elif task.collaboration_mode == CollaborationMode.SEQUENTIAL:
            await self._coordinate_sequential(task, agent_states)

    async def _coordinate_consensus(self, task: EnhancedAgentTask, agent_states: Dict[str, Any]):
        """Coordinate consensus-based collaboration"""
        # Implement consensus decision making
        pass

    async def _coordinate_parallel(self, task: EnhancedAgentTask, agent_states: Dict[str, Any]):
        """Coordinate parallel execution"""
        # Implement parallel execution coordination
        pass

    async def _coordinate_sequential(self, task: EnhancedAgentTask, agent_states: Dict[str, Any]):
        """Coordinate sequential execution"""
        # Implement sequential execution coordination
        pass

    async def get_status(self) -> Dict[str, Any]:
        """Get coordinator status and metrics"""
        return {
            "is_running": self.is_running,
            "registered_agents": len(self.agents),
            "active_tasks": sum(len(a.active_tasks) for a in self.agents.values()),
            "total_tasks": len(self.tasks),
            "coordination_stats": self.coordination_stats,
            "agent_statuses": {
                agent_id: manifest.status.value
                for agent_id, manifest in self.agent_manifests.items()
            },
            "capability_coverage": {
                capability: len(agents)
                for capability, agents in self.capability_cache.items()
            }
        }

    async def shutdown(self):
        """Shutdown the coordinator"""
        self.is_running = False

        # Stop all agents
        for agent in self.agents.values():
            await agent.stop()

        # Stop background services
        await self.task_prefetcher.stop()
        await self.cache_manager.stop()
        await self.collaboration_manager.stop()

        logger.info("Enhanced Agent Coordinator shutdown complete")

class TaskPrefetcher:
    """Task prefetching and prediction service"""

    def __init__(self, coordinator: EnhancedAgentCoordinator):
        self.coordinator = coordinator
        self.is_running = False
        self.prediction_model = None  # Would be ML model in production

    async def start(self):
        """Start task prefetching service"""
        self.is_running = True
        asyncio.create_task(self._prefetching_loop())
        logger.info("Task Prefetcher started")

    async def stop(self):
        """Stop task prefetching service"""
        self.is_running = False
        logger.info("Task Prefetcher stopped")

    async def _prefetching_loop(self):
        """Main prefetching loop"""
        while self.is_running:
            try:
                await asyncio.sleep(5)  # Check every 5 seconds

                # Analyze task patterns and prefetch likely tasks
                await self._analyze_and_prefetch()

            except Exception as e:
                logger.error(f"Error in task prefetching loop: {e}")

    async def _analyze_and_prefetch(self):
        """Analyze patterns and prefetch tasks"""
        # Analyze task history to predict future tasks
        # This is a simplified implementation
        # In production, this would use ML models

        # Get recent tasks
        recent_tasks = [t for t in self.coordinator.tasks.values()
                       if t.created_at > datetime.now() - timedelta(hours=1)]

        if len(recent_tasks) < 3:
            return

        # Analyze patterns and create prefetch tasks
        # This is a placeholder for more sophisticated prediction
        pass

class CacheManager:
    """Task result caching and management"""

    def __init__(self, coordinator: EnhancedAgentCoordinator):
        self.coordinator = coordinator
        self.is_running = False
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.cache_stats = {
            "hits": 0,
            "misses": 0,
            "size": 0
        }

    async def start(self):
        """Start cache management service"""
        self.is_running = True
        asyncio.create_task(self._cache_cleanup_loop())
        logger.info("Cache Manager started")

    async def stop(self):
        """Stop cache management service"""
        self.is_running = False
        logger.info("Cache Manager stopped")

    async def get_cached_result(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached result for task"""
        if cache_key in self.cache:
            cached_item = self.cache[cache_key]

            # Check if cache is expired
            if cached_item.get("expires_at", datetime.max) > datetime.now():
                self.cache_stats["hits"] += 1
                return cached_item["result"]
            else:
                # Remove expired cache entry
                del self.cache[cache_key]
                self.cache_stats["size"] -= 1

        self.cache_stats["misses"] += 1
        return None

    async def cache_result(self, cache_key: str, result: Dict[str, Any], ttl: timedelta = timedelta(hours=1)):
        """Cache task result"""
        self.cache[cache_key] = {
            "result": result,
            "created_at": datetime.now(),
            "expires_at": datetime.now() + ttl
        }
        self.cache_stats["size"] += 1

    async def _cache_cleanup_loop(self):
        """Periodic cache cleanup"""
        while self.is_running:
            try:
                await asyncio.sleep(300)  # Cleanup every 5 minutes

                # Remove expired entries
                now = datetime.now()
                expired_keys = [
                    key for key, item in self.cache.items()
                    if item.get("expires_at", datetime.max) <= now
                ]

                for key in expired_keys:
                    del self.cache[key]
                    self.cache_stats["size"] -= 1

                if expired_keys:
                    logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")

            except Exception as e:
                logger.error(f"Error in cache cleanup loop: {e}")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.cache_stats["hits"] + self.cache_stats["misses"]
        hit_rate = self.cache_stats["hits"] / total_requests if total_requests > 0 else 0

        return {
            **self.cache_stats,
            "hit_rate": hit_rate,
            "total_requests": total_requests
        }

class CollaborationManager:
    """Agent collaboration and communication management"""

    def __init__(self, coordinator: EnhancedAgentCoordinator):
        self.coordinator = coordinator
        self.is_running = False
        self.collaboration_sessions: Dict[str, Dict[str, Any]] = {}

    async def start(self):
        """Start collaboration management service"""
        self.is_running = True
        asyncio.create_task(self._collaboration_monitoring_loop())
        logger.info("Collaboration Manager started")

    async def stop(self):
        """Stop collaboration management service"""
        self.is_running = False
        logger.info("Collaboration Manager stopped")

    async def _collaboration_monitoring_loop(self):
        """Monitor active collaborations"""
        while self.is_running:
            try:
                await asyncio.sleep(10)  # Check every 10 seconds

                # Monitor active collaboration sessions
                active_sessions = len(self.collaboration_sessions)
                if active_sessions > 0:
                    logger.debug(f"Monitoring {active_sessions} active collaboration sessions")

            except Exception as e:
                logger.error(f"Error in collaboration monitoring loop: {e}")

    async def create_collaboration_session(self, task_id: str, participant_agents: List[str]) -> str:
        """Create new collaboration session"""
        session_id = str(uuid.uuid4())

        self.collaboration_sessions[session_id] = {
            "task_id": task_id,
            "participants": participant_agents,
            "created_at": datetime.now(),
            "status": "active",
            "messages": [],
            "shared_data": {}
        }

        logger.info(f"Created collaboration session {session_id} for task {task_id}")
        return session_id

    async def send_collaboration_message(self, session_id: str, sender_id: str, message: str, data: Dict[str, Any] = None):
        """Send message in collaboration session"""
        if session_id not in self.collaboration_sessions:
            return False

        session = self.collaboration_sessions[session_id]

        message_obj = {
            "sender_id": sender_id,
            "message": message,
            "data": data or {},
            "timestamp": datetime.now()
        }

        session["messages"].append(message_obj)

        # Deliver message to all participants
        for participant_id in session["participants"]:
            if participant_id != sender_id and participant_id in self.coordinator.agents:
                agent = self.coordinator.agents[participant_id]
                # In a real implementation, this would use agent communication protocols
                logger.debug(f"Delivered message from {sender_id} to {participant_id}")

        return True

# Global coordinator instance
enhanced_coordinator = EnhancedAgentCoordinator()

# Convenience functions
async def initialize_enhanced_coordinator() -> bool:
    """Initialize the enhanced coordinator"""
    return await enhanced_coordinator.initialize()

async def register_enhanced_agent(agent: BaseEnhancedAgent) -> bool:
    """Register an enhanced agent"""
    return await enhanced_coordinator.register_agent(agent)

async def create_enhanced_task(title: str, description: str,
                             required_capabilities: List[AgentCapability],
                             **kwargs) -> str:
    """Create an enhanced task"""
    return await enhanced_coordinator.create_task(title, description, required_capabilities, **kwargs)

async def get_coordinator_status() -> Dict[str, Any]:
    """Get coordinator status"""
    return await enhanced_coordinator.get_status()

if __name__ == "__main__":
    # Test the enhanced coordinator
    import asyncio

    async def test():
        print("Enhanced Agent Coordinator Test")
        print("===============================")

        # Initialize coordinator
        if await initialize_enhanced_coordinator():
            print("✅ Enhanced coordinator initialized")

            # Create test task
            task_id = await create_enhanced_task(
                title="Test Analysis Task",
                description="Analyze test data and provide insights",
                required_capabilities=[AgentCapability.DATA_ANALYSIS, AgentCapability.DECISION_MAKING]
            )
            print(f"✅ Created test task: {task_id}")

            # Show status
            status = await get_coordinator_status()
            print(f"Status: {json.dumps(status, indent=2, default=str)}")
        else:
            print("❌ Failed to initialize enhanced coordinator")

    asyncio.run(test())