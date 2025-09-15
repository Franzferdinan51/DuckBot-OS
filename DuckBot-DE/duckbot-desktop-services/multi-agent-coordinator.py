#!/usr/bin/env python3
"""
DuckBot Desktop Environment - Multi-Agent Coordination System
Advanced orchestration and coordination of multiple AI agents for complex desktop tasks
"""

import asyncio
import json
import sqlite3
import logging
import time
import uuid
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict
from pathlib import Path
from enum import Enum
import dbus
import dbus.service
import dbus.mainloop.glib
from gi.repository import GLib

# Add DuckBot path for complete integration
sys.path.append('/usr/share/duckbot-de')
sys.path.append('/home/user/Desktop/DuckBot-v3.1.0-VibeVoice-Ready-20250829_191017 (1)')

try:
    from duckbot.ai_router_gpt import DuckBotAI
    from duckbot.dynamic_model_manager import DynamicModelManager
    from duckbot.integration_manager import integration_manager
    from duckbot.charm_tools_integration import CharmToolsIntegration
    DUCKBOT_AVAILABLE = True
except ImportError:
    DUCKBOT_AVAILABLE = False
    print("[WARN]  DuckBot core not available, running in standalone mode")

class AgentType(Enum):
    """Types of available AI agents"""
    RESEARCH = "research"           # Information gathering and analysis
    DEVELOPMENT = "development"     # Code writing and software development
    AUTOMATION = "automation"       # Task automation and scripting
    ANALYSIS = "analysis"          # Data analysis and insights
    COMMUNICATION = "communication" # Email, messaging, social interaction
    CREATIVE = "creative"          # Content creation, design, writing
    SYSTEM = "system"              # System administration and monitoring
    COORDINATION = "coordination"   # Meta-agent for coordinating others

class TaskPriority(Enum):
    """Task priority levels"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4
    EMERGENCY = 5

class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class Agent:
    """Represents an AI agent in the system"""
    agent_id: str
    agent_type: AgentType
    name: str
    description: str
    capabilities: List[str]
    specializations: List[str]
    current_task: Optional[str] = None
    status: str = "idle"
    load_factor: float = 0.0
    success_rate: float = 1.0
    last_active: float = 0.0
    total_tasks_completed: int = 0
    average_completion_time: float = 0.0
    preferred_models: List[str] = None
    resource_requirements: Dict[str, Any] = None

@dataclass
class Task:
    """Represents a task to be executed by agents"""
    task_id: str
    title: str
    description: str
    task_type: str
    priority: TaskPriority
    status: TaskStatus
    created_at: float
    updated_at: float
    assigned_agent: Optional[str] = None
    parent_task: Optional[str] = None
    subtasks: List[str] = None
    dependencies: List[str] = None
    context: Dict[str, Any] = None
    result: Dict[str, Any] = None
    error_message: Optional[str] = None
    estimated_duration: float = 300.0  # 5 minutes default
    actual_duration: Optional[float] = None
    deadline: Optional[float] = None

@dataclass
class Collaboration:
    """Represents a collaboration between multiple agents"""
    collaboration_id: str
    title: str
    participating_agents: List[str]
    primary_agent: str
    task_id: str
    collaboration_type: str  # parallel, sequential, hierarchical
    status: str
    created_at: float
    completed_at: Optional[float] = None
    shared_context: Dict[str, Any] = None
    communication_log: List[Dict[str, Any]] = None

class MultiAgentCoordinator(dbus.service.Object):
    """
    Multi-Agent Coordination System
    
    Features:
    - Intelligent agent selection and task assignment
    - Dynamic load balancing across agents
    - Inter-agent communication and collaboration
    - Task decomposition and dependency management
    - Performance monitoring and optimization
    - Integration with all DuckBot AI systems
    - Adaptive learning from task outcomes
    - Resource-aware scheduling
    - Fault tolerance and failover
    """
    
    def __init__(self):
        # D-Bus setup
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        self.bus = dbus.SessionBus()
        super().__init__(self.bus, '/org/duckbot/MultiAgentCoordinator')
        
        # Core components
        self.logger = self._setup_logging()
        self.db_path = Path.home() / '.duckbot' / 'multiagent.db'
        self.db_path.parent.mkdir(exist_ok=True)
        
        # Agent management
        self.agents: Dict[str, Agent] = {}
        self.tasks: Dict[str, Task] = {}
        self.collaborations: Dict[str, Collaboration] = {}
        
        # Task queues by priority
        self.task_queues = {
            priority: asyncio.Queue() for priority in TaskPriority
        }
        
        # DuckBot integrations
        self.duckbot_ai = None
        self.memento_available = False
        self.charm_tools = None
        self.model_manager = None
        
        # Coordination state
        self.active_collaborations = {}
        self.agent_communications = {}
        self.performance_metrics = {}
        
        # Configuration
        self.config = {
            'max_agents_per_task': 5,
            'task_timeout': 1800,  # 30 minutes
            'collaboration_timeout': 3600,  # 1 hour
            'load_balance_threshold': 0.8,
            'failover_attempts': 3,
            'communication_timeout': 30,
            'performance_tracking_window': 24 * 3600,  # 24 hours
        }
        
        # Scheduling
        self.scheduler_running = False
        self.coordinator_agent = None
        
    def _setup_logging(self) -> logging.Logger:
        """Setup comprehensive logging"""
        logger = logging.getLogger('MultiAgentCoordinator')
        logger.setLevel(logging.INFO)
        
        # File handler
        log_file = Path.home() / '.duckbot' / 'multiagent_coordinator.log'
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # Format
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        return logger
        
    async def initialize(self):
        """Initialize all components and integrations"""
        self.logger.info("[AI] Initializing Multi-Agent Coordination System...")
        
        # Initialize database
        await self._init_database()
        
        # Initialize DuckBot integrations
        if DUCKBOT_AVAILABLE:
            await self._init_duckbot_integrations()
        
        # Initialize default agents
        await self._init_default_agents()
        
        # Load existing state
        await self._load_state()
        
        # Start scheduler
        await self._start_scheduler()
        
        # Start coordination loops
        asyncio.create_task(self._coordination_loop())
        asyncio.create_task(self._monitoring_loop())
        
        self.logger.info("[OK] Multi-Agent Coordination System initialized successfully")
        
    async def _init_database(self):
        """Initialize SQLite database for agent coordination"""
        self.db = sqlite3.connect(str(self.db_path))
        
        # Agents table
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS agents (
                agent_id TEXT PRIMARY KEY,
                agent_type TEXT,
                name TEXT,
                description TEXT,
                capabilities TEXT,
                specializations TEXT,
                current_task TEXT,
                status TEXT,
                load_factor REAL,
                success_rate REAL,
                last_active REAL,
                total_tasks_completed INTEGER,
                average_completion_time REAL,
                preferred_models TEXT,
                resource_requirements TEXT
            )
        """)
        
        # Tasks table
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                task_id TEXT PRIMARY KEY,
                title TEXT,
                description TEXT,
                task_type TEXT,
                priority INTEGER,
                status TEXT,
                created_at REAL,
                updated_at REAL,
                assigned_agent TEXT,
                parent_task TEXT,
                subtasks TEXT,
                dependencies TEXT,
                context TEXT,
                result TEXT,
                error_message TEXT,
                estimated_duration REAL,
                actual_duration REAL,
                deadline REAL
            )
        """)
        
        # Collaborations table
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS collaborations (
                collaboration_id TEXT PRIMARY KEY,
                title TEXT,
                participating_agents TEXT,
                primary_agent TEXT,
                task_id TEXT,
                collaboration_type TEXT,
                status TEXT,
                created_at REAL,
                completed_at REAL,
                shared_context TEXT,
                communication_log TEXT
            )
        """)
        
        # Performance metrics table
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS performance_metrics (
                metric_id TEXT PRIMARY KEY,
                agent_id TEXT,
                task_id TEXT,
                metric_type TEXT,
                value REAL,
                timestamp REAL,
                context TEXT
            )
        """)
        
        self.db.commit()
        
    async def _init_duckbot_integrations(self):
        """Initialize DuckBot AI ecosystem integrations"""
        try:
            # Initialize AI router
            self.duckbot_ai = DuckBotAI()
            await self.duckbot_ai.initialize()
            
            # Initialize dynamic model manager
            self.model_manager = DynamicModelManager()
            await self.model_manager.initialize()
            
            # Initialize integration manager
            await integration_manager.initialize_all()
            
            # Check Memento availability
            if integration_manager.is_integration_available("memento"):
                self.memento_available = True
                self.logger.info("[OK] Memento memory integration available")
            
            # Initialize Charm tools
            self.charm_tools = CharmToolsIntegration()
            
            self.logger.info("[OK] DuckBot integrations initialized")
            
        except Exception as e:
            self.logger.error(f"[FAIL] DuckBot integration failed: {e}")
            
    async def _init_default_agents(self):
        """Initialize default AI agents"""
        default_agents = [
            Agent(
                agent_id="research_specialist",
                agent_type=AgentType.RESEARCH,
                name="Research Specialist",
                description="Expert in information gathering, analysis, and research tasks",
                capabilities=["web_search", "data_analysis", "summarization", "fact_checking"],
                specializations=["academic_research", "market_research", "technical_documentation"],
                preferred_models=["reasoning", "general"],
                resource_requirements={"memory": "medium", "processing": "medium"}
            ),
            Agent(
                agent_id="development_expert",
                agent_type=AgentType.DEVELOPMENT,
                name="Development Expert",
                description="Specialized in software development, coding, and technical tasks",
                capabilities=["code_generation", "debugging", "testing", "architecture_design"],
                specializations=["python", "javascript", "system_programming", "web_development"],
                preferred_models=["code", "reasoning"],
                resource_requirements={"memory": "high", "processing": "high"}
            ),
            Agent(
                agent_id="automation_engineer",
                agent_type=AgentType.AUTOMATION,
                name="Automation Engineer",
                description="Expert in task automation, scripting, and workflow optimization",
                capabilities=["script_generation", "workflow_design", "system_integration", "monitoring"],
                specializations=["bash_scripting", "python_automation", "desktop_automation"],
                preferred_models=["code", "general"],
                resource_requirements={"memory": "medium", "processing": "medium"}
            ),
            Agent(
                agent_id="data_analyst",
                agent_type=AgentType.ANALYSIS,
                name="Data Analyst",
                description="Specialized in data analysis, visualization, and insights",
                capabilities=["data_processing", "statistical_analysis", "visualization", "reporting"],
                specializations=["pandas", "matplotlib", "statistical_modeling", "business_intelligence"],
                preferred_models=["reasoning", "code"],
                resource_requirements={"memory": "high", "processing": "high"}
            ),
            Agent(
                agent_id="communication_assistant",
                agent_type=AgentType.COMMUNICATION,
                name="Communication Assistant",
                description="Expert in communication, writing, and social interaction",
                capabilities=["content_writing", "email_composition", "social_media", "translation"],
                specializations=["professional_writing", "technical_writing", "customer_service"],
                preferred_models=["general", "reasoning"],
                resource_requirements={"memory": "low", "processing": "medium"}
            ),
            Agent(
                agent_id="creative_designer",
                agent_type=AgentType.CREATIVE,
                name="Creative Designer",
                description="Specialized in creative tasks, design, and content creation",
                capabilities=["content_creation", "design_thinking", "brainstorming", "visual_design"],
                specializations=["graphic_design", "ui_ux", "creative_writing", "branding"],
                preferred_models=["general", "creative"],
                resource_requirements={"memory": "medium", "processing": "medium"}
            ),
            Agent(
                agent_id="system_administrator",
                agent_type=AgentType.SYSTEM,
                name="System Administrator",
                description="Expert in system administration, monitoring, and infrastructure",
                capabilities=["system_monitoring", "performance_optimization", "security", "maintenance"],
                specializations=["linux_administration", "network_management", "security_auditing"],
                preferred_models=["code", "general"],
                resource_requirements={"memory": "medium", "processing": "low"}
            ),
            Agent(
                agent_id="coordination_master",
                agent_type=AgentType.COORDINATION,
                name="Coordination Master",
                description="Meta-agent responsible for coordinating and managing other agents",
                capabilities=["task_decomposition", "agent_selection", "load_balancing", "conflict_resolution"],
                specializations=["project_management", "resource_allocation", "strategic_planning"],
                preferred_models=["reasoning", "general"],
                resource_requirements={"memory": "high", "processing": "medium"}
            )
        ]
        
        for agent in default_agents:
            self.agents[agent.agent_id] = agent
            await self._save_agent(agent)
            
        # Set coordination master as the coordinator
        self.coordinator_agent = self.agents["coordination_master"]
        
        self.logger.info(f"[OK] Initialized {len(default_agents)} default agents")
        
    async def _load_state(self):
        """Load existing agents, tasks, and collaborations from database"""
        # Load agents
        cursor = self.db.execute("SELECT * FROM agents")
        for row in cursor.fetchall():
            agent_data = dict(zip([col[0] for col in cursor.description], row))
            
            # Deserialize complex fields
            agent_data['capabilities'] = json.loads(agent_data['capabilities']) if agent_data['capabilities'] else []
            agent_data['specializations'] = json.loads(agent_data['specializations']) if agent_data['specializations'] else []
            agent_data['preferred_models'] = json.loads(agent_data['preferred_models']) if agent_data['preferred_models'] else []
            agent_data['resource_requirements'] = json.loads(agent_data['resource_requirements']) if agent_data['resource_requirements'] else {}
            agent_data['agent_type'] = AgentType(agent_data['agent_type'])
            
            agent = Agent(**agent_data)
            self.agents[agent.agent_id] = agent
            
        # Load tasks
        cursor = self.db.execute("SELECT * FROM tasks WHERE status NOT IN ('completed', 'failed', 'cancelled')")
        for row in cursor.fetchall():
            task_data = dict(zip([col[0] for col in cursor.description], row))
            
            # Deserialize complex fields
            task_data['subtasks'] = json.loads(task_data['subtasks']) if task_data['subtasks'] else []
            task_data['dependencies'] = json.loads(task_data['dependencies']) if task_data['dependencies'] else []
            task_data['context'] = json.loads(task_data['context']) if task_data['context'] else {}
            task_data['result'] = json.loads(task_data['result']) if task_data['result'] else {}
            task_data['priority'] = TaskPriority(task_data['priority'])
            task_data['status'] = TaskStatus(task_data['status'])
            
            task = Task(**task_data)
            self.tasks[task.task_id] = task
            
        # Load active collaborations
        cursor = self.db.execute("SELECT * FROM collaborations WHERE status = 'active'")
        for row in cursor.fetchall():
            collab_data = dict(zip([col[0] for col in cursor.description], row))
            
            # Deserialize complex fields
            collab_data['participating_agents'] = json.loads(collab_data['participating_agents']) if collab_data['participating_agents'] else []
            collab_data['shared_context'] = json.loads(collab_data['shared_context']) if collab_data['shared_context'] else {}
            collab_data['communication_log'] = json.loads(collab_data['communication_log']) if collab_data['communication_log'] else []
            
            collaboration = Collaboration(**collab_data)
            self.collaborations[collaboration.collaboration_id] = collaboration
            
        self.logger.info(f"[DOCS] Loaded {len(self.agents)} agents, {len(self.tasks)} active tasks, {len(self.collaborations)} collaborations")
        
    async def _start_scheduler(self):
        """Start the task scheduler"""
        if not self.scheduler_running:
            self.scheduler_running = True
            asyncio.create_task(self._scheduler_loop())
            self.logger.info("⏰ Task scheduler started")
            
    async def _scheduler_loop(self):
        """Main scheduler loop for task assignment and execution"""
        while self.scheduler_running:
            try:
                # Process tasks by priority
                for priority in reversed(list(TaskPriority)):
                    if not self.task_queues[priority].empty():
                        task = await self.task_queues[priority].get()
                        await self._process_task_assignment(task)
                
                # Check for task timeouts
                await self._check_task_timeouts()
                
                # Rebalance loads if needed
                await self._rebalance_loads()
                
                await asyncio.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                self.logger.error(f"[FAIL] Scheduler error: {e}")
                await asyncio.sleep(10)
                
    async def _process_task_assignment(self, task: Task):
        """Process task assignment to appropriate agent"""
        try:
            # Find best agent for task
            best_agent = await self._select_best_agent(task)
            
            if best_agent:
                # Assign task to agent
                await self._assign_task_to_agent(task, best_agent)
                
                # Start task execution
                asyncio.create_task(self._execute_task(task, best_agent))
                
            else:
                # No available agents, requeue with delay
                await asyncio.sleep(30)
                await self.task_queues[task.priority].put(task)
                self.logger.warning(f"⏳ No available agents for task {task.task_id}, requeued")
                
        except Exception as e:
            self.logger.error(f"[FAIL] Task assignment error: {e}")
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            await self._save_task(task)
            
    async def _select_best_agent(self, task: Task) -> Optional[Agent]:
        """Select the best agent for a given task"""
        try:
            # Filter agents by availability and capabilities
            available_agents = []
            
            for agent in self.agents.values():
                if (agent.status == "idle" and 
                    agent.load_factor < self.config['load_balance_threshold']):
                    
                    # Check if agent has required capabilities
                    if await self._agent_can_handle_task(agent, task):
                        available_agents.append(agent)
            
            if not available_agents:
                return None
            
            # Score agents based on suitability
            scored_agents = []
            for agent in available_agents:
                score = await self._calculate_agent_score(agent, task)
                scored_agents.append((agent, score))
            
            # Sort by score and return best
            scored_agents.sort(key=lambda x: x[1], reverse=True)
            return scored_agents[0][0]
            
        except Exception as e:
            self.logger.error(f"[FAIL] Agent selection error: {e}")
            return None
            
    async def _agent_can_handle_task(self, agent: Agent, task: Task) -> bool:
        """Check if agent can handle the given task"""
        # Basic capability matching
        task_requirements = task.context.get('required_capabilities', [])
        
        if task_requirements:
            agent_capabilities = set(agent.capabilities)
            required_capabilities = set(task_requirements)
            
            # Agent must have at least 50% of required capabilities
            overlap = len(agent_capabilities & required_capabilities)
            coverage = overlap / len(required_capabilities) if required_capabilities else 1.0
            
            return coverage >= 0.5
        
        # Type-based matching
        task_type_mapping = {
            'research': [AgentType.RESEARCH, AgentType.ANALYSIS],
            'development': [AgentType.DEVELOPMENT, AgentType.AUTOMATION],
            'analysis': [AgentType.ANALYSIS, AgentType.RESEARCH],
            'automation': [AgentType.AUTOMATION, AgentType.SYSTEM],
            'communication': [AgentType.COMMUNICATION, AgentType.CREATIVE],
            'creative': [AgentType.CREATIVE, AgentType.COMMUNICATION],
            'system': [AgentType.SYSTEM, AgentType.AUTOMATION]
        }
        
        suitable_types = task_type_mapping.get(task.task_type, [])
        return agent.agent_type in suitable_types or agent.agent_type == AgentType.COORDINATION
        
    async def _calculate_agent_score(self, agent: Agent, task: Task) -> float:
        """Calculate suitability score for agent-task pairing"""
        score = 0.0
        
        # Base score from success rate
        score += agent.success_rate * 30
        
        # Load factor (lower is better)
        score += (1.0 - agent.load_factor) * 20
        
        # Capability matching
        task_capabilities = set(task.context.get('required_capabilities', []))
        agent_capabilities = set(agent.capabilities)
        
        if task_capabilities:
            overlap = len(task_capabilities & agent_capabilities)
            coverage = overlap / len(task_capabilities)
            score += coverage * 25
        
        # Specialization matching
        task_specializations = set(task.context.get('specializations', []))
        agent_specializations = set(agent.specializations)
        
        if task_specializations:
            overlap = len(task_specializations & agent_specializations)
            if overlap > 0:
                score += overlap * 15
        
        # Recent activity (prefer recently active agents)
        time_since_active = time.time() - agent.last_active
        if time_since_active < 3600:  # Within last hour
            score += 10
            
        # Performance history
        if agent.average_completion_time > 0:
            # Prefer faster agents for urgent tasks
            if task.priority in [TaskPriority.HIGH, TaskPriority.CRITICAL, TaskPriority.EMERGENCY]:
                speed_factor = min(1.0, 300 / agent.average_completion_time)  # 5 minutes baseline
                score += speed_factor * 10
        
        return score
        
    async def _assign_task_to_agent(self, task: Task, agent: Agent):
        """Assign task to agent and update status"""
        task.assigned_agent = agent.agent_id
        task.status = TaskStatus.ASSIGNED
        task.updated_at = time.time()
        
        agent.current_task = task.task_id
        agent.status = "assigned"
        agent.load_factor = min(1.0, agent.load_factor + 0.3)
        
        await self._save_task(task)
        await self._save_agent(agent)
        
        self.logger.info(f"[LIST] Assigned task '{task.title}' to agent '{agent.name}'")
        
    async def _execute_task(self, task: Task, agent: Agent):
        """Execute task using assigned agent"""
        start_time = time.time()
        
        try:
            # Update status
            task.status = TaskStatus.IN_PROGRESS
            agent.status = "working"
            agent.last_active = start_time
            
            await self._save_task(task)
            await self._save_agent(agent)
            
            self.logger.info(f"[LAUNCH] Starting task execution: {task.title}")
            
            # Check if task requires collaboration
            if await self._task_requires_collaboration(task):
                result = await self._execute_collaborative_task(task, agent)
            else:
                result = await self._execute_single_agent_task(task, agent)
            
            # Calculate duration
            end_time = time.time()
            task.actual_duration = end_time - start_time
            
            # Update agent performance
            await self._update_agent_performance(agent, task, True)
            
            # Complete task
            task.status = TaskStatus.COMPLETED
            task.result = result
            task.updated_at = end_time
            
            self.logger.info(f"[OK] Task completed: {task.title} ({task.actual_duration:.1f}s)")
            
        except Exception as e:
            # Handle task failure
            end_time = time.time()
            task.actual_duration = end_time - start_time
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            task.updated_at = end_time
            
            await self._update_agent_performance(agent, task, False)
            
            self.logger.error(f"[FAIL] Task failed: {task.title} - {e}")
            
        finally:
            # Cleanup agent state
            agent.current_task = None
            agent.status = "idle"
            agent.load_factor = max(0.0, agent.load_factor - 0.3)
            agent.total_tasks_completed += 1
            
            await self._save_task(task)
            await self._save_agent(agent)
            
            # Store in memory if available
            if self.memento_available:
                await self._store_task_completion_in_memory(task, agent)
                
    async def _task_requires_collaboration(self, task: Task) -> bool:
        """Determine if task requires multiple agents"""
        # Check task complexity indicators
        complexity_indicators = [
            len(task.description) > 500,  # Long description
            task.context.get('estimated_subtasks', 0) > 3,  # Multiple subtasks
            len(task.context.get('required_capabilities', [])) > 3,  # Multiple capabilities
            task.priority in [TaskPriority.HIGH, TaskPriority.CRITICAL],  # High priority
            'collaboration' in task.description.lower(),  # Explicit collaboration request
        ]
        
        return sum(complexity_indicators) >= 2
        
    async def _execute_single_agent_task(self, task: Task, agent: Agent) -> Dict[str, Any]:
        """Execute task with single agent"""
        if not self.duckbot_ai or not DUCKBOT_AVAILABLE:
            return {"error": "DuckBot AI not available"}
        
        try:
            # Prepare enhanced context
            enhanced_context = {
                **task.context,
                'agent_capabilities': agent.capabilities,
                'agent_specializations': agent.specializations,
                'task_id': task.task_id,
                'agent_id': agent.agent_id
            }
            
            # Select appropriate model based on agent preferences
            preferred_model = "local"
            if agent.preferred_models:
                preferred_model = agent.preferred_models[0]
            
            # Execute with DuckBot AI
            result = await self.duckbot_ai.enhanced_request(
                task.description,
                enhanced_context,
                preferred_model=preferred_model
            )
            
            if result.get("success"):
                return {
                    "success": True,
                    "result": result["result"],
                    "agent_id": agent.agent_id,
                    "execution_type": "single_agent"
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error", "Unknown error"),
                    "agent_id": agent.agent_id
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "agent_id": agent.agent_id
            }
            
    async def _execute_collaborative_task(self, task: Task, primary_agent: Agent) -> Dict[str, Any]:
        """Execute task with multiple agents in collaboration"""
        try:
            # Create collaboration
            collaboration_id = str(uuid.uuid4())
            
            # Select additional agents
            additional_agents = await self._select_collaboration_agents(task, primary_agent)
            
            all_agents = [primary_agent] + additional_agents
            collaboration = Collaboration(
                collaboration_id=collaboration_id,
                title=f"Collaboration for: {task.title}",
                participating_agents=[agent.agent_id for agent in all_agents],
                primary_agent=primary_agent.agent_id,
                task_id=task.task_id,
                collaboration_type="hierarchical",
                status="active",
                created_at=time.time(),
                shared_context={
                    "original_task": asdict(task),
                    "agent_roles": await self._assign_collaboration_roles(all_agents, task)
                },
                communication_log=[]
            )
            
            self.collaborations[collaboration_id] = collaboration
            await self._save_collaboration(collaboration)
            
            # Execute collaborative task
            result = await self._execute_hierarchical_collaboration(collaboration, task, all_agents)
            
            # Complete collaboration
            collaboration.status = "completed"
            collaboration.completed_at = time.time()
            await self._save_collaboration(collaboration)
            
            return result
            
        except Exception as e:
            self.logger.error(f"[FAIL] Collaborative task execution error: {e}")
            return {
                "success": False,
                "error": str(e),
                "execution_type": "collaborative"
            }
            
    async def _select_collaboration_agents(self, task: Task, primary_agent: Agent) -> List[Agent]:
        """Select additional agents for collaboration"""
        additional_agents = []
        
        # Determine what additional capabilities are needed
        required_capabilities = set(task.context.get('required_capabilities', []))
        primary_capabilities = set(primary_agent.capabilities)
        missing_capabilities = required_capabilities - primary_capabilities
        
        if missing_capabilities:
            # Find agents with missing capabilities
            for agent in self.agents.values():
                if (agent.agent_id != primary_agent.agent_id and
                    agent.status == "idle" and
                    agent.load_factor < self.config['load_balance_threshold'] and
                    len(additional_agents) < self.config['max_agents_per_task'] - 1):
                    
                    agent_capabilities = set(agent.capabilities)
                    if agent_capabilities & missing_capabilities:
                        additional_agents.append(agent)
                        missing_capabilities -= agent_capabilities
                        
                        if not missing_capabilities:
                            break
        
        return additional_agents
        
    async def _assign_collaboration_roles(self, agents: List[Agent], task: Task) -> Dict[str, str]:
        """Assign specific roles to agents in collaboration"""
        roles = {}
        
        # Primary agent is always the coordinator
        roles[agents[0].agent_id] = "coordinator"
        
        # Assign roles based on agent types and task requirements
        role_assignments = {
            AgentType.RESEARCH: "researcher",
            AgentType.DEVELOPMENT: "developer", 
            AgentType.AUTOMATION: "automator",
            AgentType.ANALYSIS: "analyst",
            AgentType.COMMUNICATION: "communicator",
            AgentType.CREATIVE: "creative_lead",
            AgentType.SYSTEM: "system_specialist"
        }
        
        for agent in agents[1:]:
            roles[agent.agent_id] = role_assignments.get(agent.agent_type, "specialist")
            
        return roles
        
    async def _execute_hierarchical_collaboration(self, collaboration: Collaboration, task: Task, agents: List[Agent]) -> Dict[str, Any]:
        """Execute hierarchical collaboration with primary agent coordinating"""
        try:
            primary_agent = agents[0]
            
            # Phase 1: Task decomposition by primary agent
            decomposition_context = {
                "task": asdict(task),
                "available_agents": [
                    {
                        "id": agent.agent_id,
                        "type": agent.agent_type.value,
                        "capabilities": agent.capabilities,
                        "role": collaboration.shared_context["agent_roles"][agent.agent_id]
                    } for agent in agents
                ]
            }
            
            decomposition_result = await self.duckbot_ai.enhanced_request(
                f"As the coordinating agent, decompose this task into subtasks for the available agents: {task.description}",
                decomposition_context,
                preferred_model="reasoning"
            )
            
            if not decomposition_result.get("success"):
                return {"success": False, "error": "Task decomposition failed"}
            
            # Parse subtasks
            subtasks = await self._parse_subtasks(decomposition_result["result"]["content"], agents[1:])
            
            # Phase 2: Parallel execution of subtasks
            subtask_results = await asyncio.gather(
                *[self._execute_subtask(subtask, agent) for subtask, agent in zip(subtasks, agents[1:])],
                return_exceptions=True
            )
            
            # Phase 3: Integration by primary agent
            integration_context = {
                "original_task": task.description,
                "subtask_results": [
                    {
                        "agent": agents[i+1].agent_id,
                        "result": result if not isinstance(result, Exception) else {"error": str(result)}
                    } for i, result in enumerate(subtask_results)
                ]
            }
            
            final_result = await self.duckbot_ai.enhanced_request(
                "Integrate the subtask results into a final solution for the original task",
                integration_context,
                preferred_model="reasoning"
            )
            
            # Log collaboration communication
            await self._log_collaboration_communication(collaboration, "integration", integration_context)
            
            return {
                "success": True,
                "result": final_result["result"] if final_result.get("success") else {"error": "Integration failed"},
                "collaboration_id": collaboration.collaboration_id,
                "participating_agents": [agent.agent_id for agent in agents],
                "execution_type": "hierarchical_collaboration",
                "subtask_results": subtask_results
            }
            
        except Exception as e:
            self.logger.error(f"[FAIL] Hierarchical collaboration error: {e}")
            return {
                "success": False,
                "error": str(e),
                "execution_type": "hierarchical_collaboration"
            }
            
    async def _parse_subtasks(self, decomposition_text: str, agents: List[Agent]) -> List[Dict[str, Any]]:
        """Parse AI-generated task decomposition into structured subtasks"""
        subtasks = []
        
        # Simple parsing - in practice would be more sophisticated
        lines = decomposition_text.split('\n')
        current_subtask = None
        
        for line in lines:
            line = line.strip()
            if line.startswith(('-', '*', '•', '1.', '2.', '3.', '4.', '5.')):
                if current_subtask:
                    subtasks.append(current_subtask)
                    
                current_subtask = {
                    "description": line.lstrip('-*•0123456789. '),
                    "details": ""
                }
            elif current_subtask and line:
                current_subtask["details"] += f" {line}"
                
        if current_subtask:
            subtasks.append(current_subtask)
            
        # Ensure we have subtasks for each agent
        while len(subtasks) < len(agents):
            subtasks.append({
                "description": f"Support task for {agents[len(subtasks)].name}",
                "details": "Provide assistance and support for the main task"
            })
            
        return subtasks[:len(agents)]
        
    async def _execute_subtask(self, subtask: Dict[str, Any], agent: Agent) -> Dict[str, Any]:
        """Execute a subtask with specific agent"""
        try:
            context = {
                "subtask_description": subtask["description"],
                "subtask_details": subtask["details"],
                "agent_role": agent.agent_type.value,
                "agent_capabilities": agent.capabilities
            }
            
            preferred_model = agent.preferred_models[0] if agent.preferred_models else "local"
            
            result = await self.duckbot_ai.enhanced_request(
                f"Execute this subtask: {subtask['description']}. {subtask['details']}",
                context,
                preferred_model=preferred_model
            )
            
            return result
            
        except Exception as e:
            return {"success": False, "error": str(e)}
            
    async def _log_collaboration_communication(self, collaboration: Collaboration, message_type: str, content: Dict[str, Any]):
        """Log communication within collaboration"""
        log_entry = {
            "timestamp": time.time(),
            "type": message_type,
            "content": content
        }
        
        collaboration.communication_log.append(log_entry)
        await self._save_collaboration(collaboration)
        
    async def _update_agent_performance(self, agent: Agent, task: Task, success: bool):
        """Update agent performance metrics"""
        try:
            # Update success rate
            total_tasks = agent.total_tasks_completed + 1
            if success:
                agent.success_rate = ((agent.success_rate * agent.total_tasks_completed) + 1.0) / total_tasks
            else:
                agent.success_rate = (agent.success_rate * agent.total_tasks_completed) / total_tasks
                
            # Update average completion time
            if task.actual_duration:
                if agent.average_completion_time == 0:
                    agent.average_completion_time = task.actual_duration
                else:
                    agent.average_completion_time = (
                        (agent.average_completion_time * agent.total_tasks_completed) + task.actual_duration
                    ) / total_tasks
            
            # Store performance metric
            metric_id = str(uuid.uuid4())
            self.db.execute("""
                INSERT INTO performance_metrics
                (metric_id, agent_id, task_id, metric_type, value, timestamp, context)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                metric_id,
                agent.agent_id,
                task.task_id,
                "task_completion",
                1.0 if success else 0.0,
                time.time(),
                json.dumps({"duration": task.actual_duration, "priority": task.priority.value})
            ))
            self.db.commit()
            
        except Exception as e:
            self.logger.error(f"[FAIL] Performance update error: {e}")
            
    async def _coordination_loop(self):
        """Main coordination loop for monitoring and optimization"""
        while True:
            try:
                # Monitor active collaborations
                await self._monitor_collaborations()
                
                # Optimize agent allocation
                await self._optimize_agent_allocation()
                
                # Check for stuck tasks
                await self._check_stuck_tasks()
                
                # Performance analysis
                await self._analyze_performance()
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                self.logger.error(f"[FAIL] Coordination loop error: {e}")
                await asyncio.sleep(120)
                
    async def _monitoring_loop(self):
        """Monitoring loop for system health and metrics"""
        while True:
            try:
                # Monitor system resources
                await self._monitor_system_resources()
                
                # Update agent load factors
                await self._update_agent_loads()
                
                # Check for failed agents
                await self._check_agent_health()
                
                # Cleanup old data
                await self._cleanup_old_data()
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                self.logger.error(f"[FAIL] Monitoring loop error: {e}")
                await asyncio.sleep(60)
                
    async def _store_task_completion_in_memory(self, task: Task, agent: Agent):
        """Store task completion in Memento memory"""
        try:
            memory_data = {
                'type': 'task_completion',
                'task_id': task.task_id,
                'task_title': task.title,
                'agent_id': agent.agent_id,
                'agent_name': agent.name,
                'success': task.status == TaskStatus.COMPLETED,
                'duration': task.actual_duration,
                'priority': task.priority.value,
                'timestamp': time.time()
            }
            
            result = await integration_manager.execute_integrated_task(
                "memory",
                "Store task completion",
                memory_data
            )
            
            if result.get("success"):
                self.logger.debug("[SAVE] Task completion stored in Memento")
                
        except Exception as e:
            self.logger.error(f"[FAIL] Memento storage error: {e}")
            
    # Helper methods for database operations
    async def _save_agent(self, agent: Agent):
        """Save agent to database"""
        self.db.execute("""
            INSERT OR REPLACE INTO agents
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            agent.agent_id,
            agent.agent_type.value,
            agent.name,
            agent.description,
            json.dumps(agent.capabilities),
            json.dumps(agent.specializations),
            agent.current_task,
            agent.status,
            agent.load_factor,
            agent.success_rate,
            agent.last_active,
            agent.total_tasks_completed,
            agent.average_completion_time,
            json.dumps(agent.preferred_models),
            json.dumps(agent.resource_requirements)
        ))
        self.db.commit()
        
    async def _save_task(self, task: Task):
        """Save task to database"""
        self.db.execute("""
            INSERT OR REPLACE INTO tasks
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            task.task_id,
            task.title,
            task.description,
            task.task_type,
            task.priority.value,
            task.status.value,
            task.created_at,
            task.updated_at,
            task.assigned_agent,
            task.parent_task,
            json.dumps(task.subtasks),
            json.dumps(task.dependencies),
            json.dumps(task.context),
            json.dumps(task.result),
            task.error_message,
            task.estimated_duration,
            task.actual_duration,
            task.deadline
        ))
        self.db.commit()
        
    async def _save_collaboration(self, collaboration: Collaboration):
        """Save collaboration to database"""
        self.db.execute("""
            INSERT OR REPLACE INTO collaborations
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            collaboration.collaboration_id,
            collaboration.title,
            json.dumps(collaboration.participating_agents),
            collaboration.primary_agent,
            collaboration.task_id,
            collaboration.collaboration_type,
            collaboration.status,
            collaboration.created_at,
            collaboration.completed_at,
            json.dumps(collaboration.shared_context),
            json.dumps(collaboration.communication_log)
        ))
        self.db.commit()
        
    # Placeholder methods for monitoring and optimization
    async def _check_task_timeouts(self):
        """Check for timed out tasks"""
        pass
        
    async def _rebalance_loads(self):
        """Rebalance agent loads"""
        pass
        
    async def _monitor_collaborations(self):
        """Monitor active collaborations"""
        pass
        
    async def _optimize_agent_allocation(self):
        """Optimize agent allocation"""
        pass
        
    async def _check_stuck_tasks(self):
        """Check for stuck tasks"""
        pass
        
    async def _analyze_performance(self):
        """Analyze performance metrics"""
        pass
        
    async def _monitor_system_resources(self):
        """Monitor system resources"""
        pass
        
    async def _update_agent_loads(self):
        """Update agent load factors"""
        pass
        
    async def _check_agent_health(self):
        """Check agent health status"""
        pass
        
    async def _cleanup_old_data(self):
        """Cleanup old data"""
        pass
        
    # D-Bus interface methods
    @dbus.service.method('org.duckbot.MultiAgentCoordinator', in_signature='ssssis', out_signature='s')
    def SubmitTask(self, title: str, description: str, task_type: str, priority: int, context: str) -> str:
        """Submit a new task for execution"""
        try:
            task_id = str(uuid.uuid4())
            task = Task(
                task_id=task_id,
                title=title,
                description=description,
                task_type=task_type,
                priority=TaskPriority(priority),
                status=TaskStatus.PENDING,
                created_at=time.time(),
                updated_at=time.time(),
                context=json.loads(context) if context else {}
            )
            
            self.tasks[task_id] = task
            asyncio.create_task(self._save_task(task))
            
            # Add to appropriate queue
            asyncio.create_task(self.task_queues[task.priority].put(task))
            
            return task_id
            
        except Exception as e:
            self.logger.error(f"[FAIL] Task submission error: {e}")
            return ""
            
    @dbus.service.method('org.duckbot.MultiAgentCoordinator', in_signature='s', out_signature='s')
    def GetTaskStatus(self, task_id: str) -> str:
        """Get status of a specific task"""
        try:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                return json.dumps({
                    'task_id': task_id,
                    'status': task.status.value,
                    'assigned_agent': task.assigned_agent,
                    'progress': self._calculate_task_progress(task),
                    'result': task.result
                })
            return json.dumps({'error': 'Task not found'})
        except Exception as e:
            return json.dumps({'error': str(e)})
            
    @dbus.service.method('org.duckbot.MultiAgentCoordinator', out_signature='s')
    def GetSystemStatus(self) -> str:
        """Get overall system status"""
        try:
            status = {
                'total_agents': len(self.agents),
                'active_agents': len([a for a in self.agents.values() if a.status != 'idle']),
                'pending_tasks': len([t for t in self.tasks.values() if t.status == TaskStatus.PENDING]),
                'active_tasks': len([t for t in self.tasks.values() if t.status == TaskStatus.IN_PROGRESS]),
                'active_collaborations': len([c for c in self.collaborations.values() if c.status == 'active']),
                'system_load': sum(a.load_factor for a in self.agents.values()) / len(self.agents) if self.agents else 0
            }
            return json.dumps(status)
        except Exception as e:
            return json.dumps({'error': str(e)})
            
    def _calculate_task_progress(self, task: Task) -> float:
        """Calculate task progress percentage"""
        if task.status == TaskStatus.COMPLETED:
            return 100.0
        elif task.status == TaskStatus.FAILED:
            return 0.0
        elif task.status == TaskStatus.IN_PROGRESS:
            # Estimate based on time elapsed vs estimated duration
            elapsed = time.time() - task.created_at
            return min(90.0, (elapsed / task.estimated_duration) * 100) if task.estimated_duration > 0 else 50.0
        else:
            return 0.0

async def main():
    """Main entry point"""
    print("[AI] Starting DuckBot Multi-Agent Coordination System...")
    
    try:
        # Create and initialize coordinator
        coordinator = MultiAgentCoordinator()
        await coordinator.initialize()
        
        print("[OK] Multi-Agent Coordination System started successfully")
        print("[LAUNCH] Ready to coordinate AI agents for complex tasks")
        
        # Run main loop
        loop = GLib.MainLoop()
        loop.run()
        
    except KeyboardInterrupt:
        print("\n[EMOJI] Shutting down Multi-Agent Coordinator...")
    except Exception as e:
        print(f"[FAIL] Fatal error: {e}")
        return 1
        
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))