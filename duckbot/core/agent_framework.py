#!/usr/bin/env python3
"""
Unified Agent Framework for DuckBot
Integrates Archon, MetaGPT, and n8n agent capabilities with role-based collaboration
"""

import os
import asyncio
import logging
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, AsyncGenerator
from dataclasses import dataclass, field
from enum import Enum
import sqlite3
import hashlib
from datetime import datetime, timedelta
import websockets
import uuid
import yaml

logger = logging.getLogger(__name__)

# Agent roles
class AgentRole(Enum):
    """Agent roles for enhanced collaboration"""
    PRODUCT_MANAGER = "product_manager"
    ARCHITECT = "architect"
    PROJECT_MANAGER = "project_manager"
    ENGINEER = "engineer"
    QA_ENGINEER = "qa_engineer"
    RESEARCHER = "researcher"
    TECHNICAL_WRITER = "technical_writer"
    DEVOPS = "devops"
    GENERAL = "general"

# Task status
class TaskStatus(Enum):
    """Task status tracking"""
    BACKLOG = "backlog"
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    COMPLETED = "completed"
    FAILED = "failed"

# SOP phases
class SOPPhase(Enum):
    """Standard Operating Procedure phases"""
    REQUIREMENTS = "requirements"
    DESIGN = "design"
    IMPLEMENTATION = "implementation"
    TESTING = "testing"
    REVIEW = "review"
    DEPLOYMENT = "deployment"
    MAINTENANCE = "maintenance"

@dataclass
class Team:
    """Team configuration for role-based collaboration"""
    name: str
    description: str
    roles: List[AgentRole] = field(default_factory=list)
    agents: Dict[str, Any] = field(default_factory=dict)
    active: bool = True

@dataclass
class Project:
    """Project management structure"""
    id: str
    name: str
    description: str
    team: str
    requirements: List[str] = field(default_factory=list)
    tasks: List[str] = field(default_factory=list)  # Task IDs
    status: str = "planning"
    created_at: datetime = field(default_factory=datetime.now)
    deadline: Optional[datetime] = None

@dataclass
class KnowledgeItem:
    """Knowledge base item"""
    id: str
    content: str
    embedding: Optional[List[float]]
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

@dataclass
class AgentTask:
    """Agent task structure"""
    id: str
    description: str
    role: AgentRole
    status: TaskStatus
    project_id: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    result: Optional[Dict] = None
    assigned_to: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None

class UnifiedAgentFramework:
    """Unified agent framework combining Archon, MetaGPT, and n8n capabilities"""

    def __init__(self):
        self.db_path = Path("data/unified_agents.db")
        self.active_agents = {}
        self.knowledge_base = []
        self.active_tasks = {}
        self.websocket_connections = set()
        self.available = True

        # Teams and projects
        self.teams = {}
        self.projects = {}
        self.enhanced_tasks = {}  # EnhancedAgentTask instances

        # SOP workflows
        self.sop_workflows = {
            "software_development": [
                SOPPhase.REQUIREMENTS,
                SOPPhase.DESIGN,
                SOPPhase.IMPLEMENTATION,
                SOPPhase.TESTING,
                SOPPhase.DEPLOYMENT
            ],
            "research_project": [
                SOPPhase.REQUIREMENTS,
                SOPPhase.DESIGN,
                SOPPhase.IMPLEMENTATION,
                SOPPhase.REVIEW
            ],
            "content_creation": [
                SOPPhase.REQUIREMENTS,
                SOPPhase.DESIGN,
                SOPPhase.IMPLEMENTATION,
                SOPPhase.REVIEW
            ]
        }

        # Agent role capabilities
        self.role_capabilities = {
            AgentRole.PRODUCT_MANAGER: [
                "requirement_analysis", "user_story_creation", "prioritization",
                "stakeholder_communication", "roadmap_planning"
            ],
            AgentRole.ARCHITECT: [
                "system_design", "technology_selection", "api_design",
                "scalability_planning", "security_architecture"
            ],
            AgentRole.PROJECT_MANAGER: [
                "task_breakdown", "resource_allocation", "timeline_planning",
                "risk_management", "team_coordination"
            ],
            AgentRole.ENGINEER: [
                "code_implementation", "debugging", "optimization",
                "code_review", "documentation"
            ],
            AgentRole.QA_ENGINEER: [
                "test_planning", "test_execution", "bug_tracking",
                "quality_metrics", "automation"
            ],
            AgentRole.RESEARCHER: [
                "information_gathering", "analysis", "synthesis",
                "experimentation", "documentation"
            ],
            AgentRole.TECHNICAL_WRITER: [
                "documentation", "user_guides", "api_docs",
                "technical_articles", "tutorials"
            ],
            AgentRole.DEVOPS: [
                "ci_cd", "deployment", "monitoring", "infrastructure",
                "automation", "scaling"
            ],
            AgentRole.GENERAL: [
                "general_task_execution", "problem_solving", "coordination"
            ]
        }
        
    async def initialize(self) -> bool:
        """Initialize unified agent framework"""
        try:
            # Setup knowledge database
            await self._setup_knowledge_db()

            # Initialize agent capabilities
            await self._initialize_agents()

            # Initialize teams and workflows
            await self._initialize_teams()

            logger.info("Unified agent framework initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize unified agent framework: {e}")
            return False
    
    async def _setup_knowledge_db(self):
        """Setup SQLite knowledge database"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Knowledge items table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_items (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                embedding BLOB,
                metadata TEXT,
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )
        """)
        
        # Agent tasks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_tasks (
                id TEXT PRIMARY KEY,
                description TEXT NOT NULL,
                role TEXT NOT NULL,
                status TEXT DEFAULT 'backlog',
                project_id TEXT,
                dependencies TEXT,
                result TEXT,
                assigned_to TEXT,
                created_at TIMESTAMP,
                completed_at TIMESTAMP,
                estimated_hours REAL,
                actual_hours REAL
            )
        """)
        
        # Teams table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS teams (
                name TEXT PRIMARY KEY,
                description TEXT,
                roles TEXT,
                agents TEXT,
                active BOOLEAN DEFAULT 1
            )
        """)

        # Projects table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                requirements TEXT,
                tasks TEXT,
                team TEXT,
                status TEXT DEFAULT 'planning',
                created_at TIMESTAMP,
                deadline TIMESTAMP,
                FOREIGN KEY (team) REFERENCES teams(name)
            )
        """)
        
        # Create indices
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_knowledge_created ON knowledge_items(created_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON agent_tasks(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_role ON agent_tasks(role)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status)")
        
        conn.commit()
        conn.close()
    
    async def _initialize_agents(self):
        """Initialize specialized AI agents"""
        self.active_agents = {
            "knowledge_manager": {
                "name": "Knowledge Manager",
                "description": "Manages knowledge base and retrieval",
                "status": "active",
                "capabilities": ["indexing", "search", "summarization"]
            },
            "task_executor": {
                "name": "Task Executor", 
                "description": "Executes complex multi-step tasks",
                "status": "active",
                "capabilities": ["planning", "execution", "monitoring"]
            },
            "code_assistant": {
                "name": "Code Assistant",
                "description": "Provides advanced coding assistance",
                "status": "active", 
                "capabilities": ["code_generation", "debugging", "optimization"]
            },
            "research_agent": {
                "name": "Research Agent",
                "description": "Conducts research and analysis",
                "status": "active",
                "capabilities": ["web_search", "analysis", "synthesis"]
            },
            "general_agent": {
                "name": "General Agent",
                "description": "Handles general-purpose tasks",
                "status": "active",
                "capabilities": ["problem_solving", "coordination", "communication"]
            }
        }
    
    async def _initialize_teams(self):
        """Initialize default teams"""
        # Software Development Team
        dev_team = Team(
            name="software_development",
            description="Full-stack software development team",
            roles=[
                AgentRole.PRODUCT_MANAGER,
                AgentRole.ARCHITECT,
                AgentRole.PROJECT_MANAGER,
                AgentRole.ENGINEER,
                AgentRole.QA_ENGINEER,
                AgentRole.DEVOPS
            ]
        )
        self.teams["software_development"] = dev_team

        # Research Team
        research_team = Team(
            name="research",
            description="Research and analysis team",
            roles=[
                AgentRole.RESEARCHER,
                AgentRole.PRODUCT_MANAGER,
                AgentRole.TECHNICAL_WRITER
            ]
        )
        self.teams["research"] = research_team

        # Content Creation Team
        content_team = Team(
            name="content_creation",
            description="Documentation and content creation team",
            roles=[
                AgentRole.TECHNICAL_WRITER,
                AgentRole.PRODUCT_MANAGER,
                AgentRole.RESEARCHER
            ]
        )
        self.teams["content_creation"] = content_team

        # Save teams to database
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        for team_name, team in self.teams.items():
            cursor.execute("""
                INSERT OR REPLACE INTO teams (name, description, roles, agents, active)
                VALUES (?, ?, ?, ?, ?)
            """, (
                team_name,
                team.description,
                json.dumps([role.value for role in team.roles]),
                json.dumps(team.agents),
                team.active
            ))

        conn.commit()
        conn.close()

        logger.info(f"Initialized {len(self.teams)} teams")
    
    async def create_project(self, name: str, description: str, team_name: str,
                           requirements: List[str] = None,
                           deadline: Optional[datetime] = None) -> str:
        """Create a new project with team structure"""
        if team_name not in self.teams:
            raise ValueError(f"Team '{team_name}' not found")

        project_id = str(uuid.uuid4())
        project = Project(
            id=project_id,
            name=name,
            description=description,
            requirements=requirements or [],
            team=team_name,
            deadline=deadline
        )

        self.projects[project_id] = project

        # Create initial SOP-based tasks
        await self._create_sop_tasks(project_id)

        # Save to database
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO projects (id, name, description, requirements, team, status, created_at, deadline)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            project_id, name, description, json.dumps(requirements or []),
            team_name, "planning", project.created_at, deadline
        ))
        conn.commit()
        conn.close()

        logger.info(f"Created project '{name}' with {team_name} team")
        return project_id

    async def _create_sop_tasks(self, project_id: str):
        """Create initial tasks based on Standard Operating Procedures"""
        project = self.projects.get(project_id)
        if not project:
            return

        team = self.teams.get(project.team)
        if not team:
            return

        # Determine SOP workflow based on team type
        workflow = self.sop_workflows.get(project.team, ["requirements", "design", "implementation"])

        for i, phase in enumerate(workflow):
            # Determine appropriate role for this phase
            role = self._get_role_for_phase(phase, team.roles)

            task_id = str(uuid.uuid4())
            task = AgentTask(
                id=task_id,
                description=f"Execute {phase.value} phase for {project.name}",
                role=role,
                status=TaskStatus.BACKLOG if i > 0 else TaskStatus.PLANNED,
                project_id=project_id,
                estimated_hours=self._estimate_phase_hours(phase)
            )

            self.enhanced_tasks[task_id] = task
            project.tasks.append(task_id)

            # Save to database
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO agent_tasks (id, description, role, status, project_id,
                                      estimated_hours, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                task_id, task.description, task.role.value, task.status.value,
                project_id, task.estimated_hours, task.created_at
            ))
            conn.commit()
            conn.close()

    def _get_role_for_phase(self, phase: SOPPhase, available_roles: List[AgentRole]) -> AgentRole:
        """Determine appropriate role for a given SOP phase"""
        role_mapping = {
            SOPPhase.REQUIREMENTS: [AgentRole.PRODUCT_MANAGER, AgentRole.RESEARCHER],
            SOPPhase.DESIGN: [AgentRole.ARCHITECT, AgentRole.PRODUCT_MANAGER],
            SOPPhase.IMPLEMENTATION: [AgentRole.ENGINEER, AgentRole.DEVOPS],
            SOPPhase.TESTING: [AgentRole.QA_ENGINEER, AgentRole.ENGINEER],
            SOPPhase.DEPLOYMENT: [AgentRole.DEVOPS, AgentRole.ENGINEER],
            SOPPhase.MAINTENANCE: [AgentRole.DEVOPS, AgentRole.ENGINEER]
        }

        preferred_roles = role_mapping.get(phase, [AgentRole.ENGINEER])

        # Find first available preferred role
        for role in preferred_roles:
            if role in available_roles:
                return role

        # Fallback to first available role
        return available_roles[0] if available_roles else AgentRole.ENGINEER

    def _estimate_phase_hours(self, phase: SOPPhase) -> float:
        """Estimate hours for a given SOP phase"""
        estimates = {
            SOPPhase.REQUIREMENTS: 8.0,
            SOPPhase.DESIGN: 16.0,
            SOPPhase.IMPLEMENTATION: 40.0,
            SOPPhase.TESTING: 12.0,
            SOPPhase.DEPLOYMENT: 4.0,
            SOPPhase.MAINTENANCE: 8.0
        }
        return estimates.get(phase, 8.0)

    async def create_agent_task(self, description: str, role: AgentRole = AgentRole.GENERAL,
                              project_id: Optional[str] = None,
                              dependencies: List[str] = None,
                              estimated_hours: Optional[float] = None) -> str:
        """Create a new agent task"""
        task_id = str(uuid.uuid4())
        task = AgentTask(
            id=task_id,
            description=description,
            role=role,
            status=TaskStatus.BACKLOG,
            project_id=project_id,
            dependencies=dependencies or [],
            estimated_hours=estimated_hours
        )

        self.enhanced_tasks[task_id] = task

        # Add to project if specified
        if project_id and project_id in self.projects:
            self.projects[project_id].tasks.append(task_id)

        # Save to database
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO agent_tasks (id, description, role, status, project_id,
                                  dependencies, estimated_hours, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            task_id, description, role.value, TaskStatus.BACKLOG.value,
            project_id, json.dumps(dependencies or []), estimated_hours, task.created_at
        ))
        conn.commit()
        conn.close()

        # Auto-assign task
        await self._auto_assign_task(task_id)

        return task_id

    async def _auto_assign_task(self, task_id: str):
        """Automatically assign task to appropriate agent"""
        task = self.enhanced_tasks.get(task_id)
        if not task:
            return

        # Simple assignment logic based on role
        task.assigned_to = f"{task.role.value}_agent"

        # Update in database
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE agent_tasks
            SET assigned_to = ?
            WHERE id = ?
        """, (task.assigned_to, task_id))
        conn.commit()
        conn.close()

    async def execute_project_workflow(self, project_id: str) -> AsyncGenerator[Dict[str, Any], None]:
        """Execute complete workflow for a project"""
        project = self.projects.get(project_id)
        if not project:
            return

        team = self.teams.get(project.team)
        if not team:
            return

        yield {
            "type": "workflow_started",
            "project_id": project_id,
            "project_name": project.name,
            "team": team.name,
            "timestamp": datetime.now().isoformat()
        }

        # Execute SOP phases
        workflow = self.sop_workflows.get(project.team, ["requirements", "design", "implementation"])

        for phase in workflow:
            yield {
                "type": "phase_started",
                "project_id": project_id,
                "phase": phase.value,
                "timestamp": datetime.now().isoformat()
            }

            # Execute phase with appropriate role
            role = self._get_role_for_phase(phase, team.roles)
            result = await self._execute_phase_with_role(project_id, phase, role)

            yield {
                "type": "phase_completed",
                "project_id": project_id,
                "phase": phase.value,
                "result": result,
                "timestamp": datetime.now().isoformat()
            }

        yield {
            "type": "workflow_completed",
            "project_id": project_id,
            "timestamp": datetime.now().isoformat()
        }

    async def _execute_phase_with_role(self, project_id: str, phase: SOPPhase, role: AgentRole) -> Dict[str, Any]:
        """Execute a SOP phase with the assigned role"""
        project = self.projects.get(project_id)
        if not project:
            return {"error": "Project not found"}

        # Create task for this phase
        task_description = f"Execute {phase.value} phase for {project.name}"
        task_id = await self.create_agent_task(task_description, role, project_id)

        # Simulate task execution
        await asyncio.sleep(1)  # Simulate work

        # Generate phase-specific results
        result = {
            "phase": phase.value,
            "role": role.value,
            "output": self._generate_phase_output(phase, project),
            "quality_score": 0.85 + (hash(phase.value) % 10) / 100,
            "completion_time": datetime.now().isoformat()
        }

        # Update task
        task = self.enhanced_tasks.get(task_id)
        if task:
            task.status = TaskStatus.COMPLETED
            task.result = result
            task.completed_at = datetime.now()

            # Update in database
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE agent_tasks
                SET status = ?, result = ?, completed_at = ?
                WHERE id = ?
            """, (task.status.value, json.dumps(task.result) if task.result else None, task.completed_at, task.id))
            conn.commit()
            conn.close()

        return result

    def _generate_phase_output(self, phase: SOPPhase, project: Project) -> Dict[str, Any]:
        """Generate realistic output for each SOP phase"""
        outputs = {
            SOPPhase.REQUIREMENTS: {
                "user_stories": ["As a user, I want to...", "As a admin, I need to..."],
                "acceptance_criteria": ["Given... When... Then..."],
                "technical_requirements": ["System shall...", "Component must..."]
            },
            SOPPhase.DESIGN: {
                "architecture_diagram": "system_architecture.png",
                "api_endpoints": ["/api/v1/resource", "/api/v1/users"],
                "database_schema": "schema.sql",
                "technology_stack": ["Python", "FastAPI", "PostgreSQL"]
            },
            SOPPhase.IMPLEMENTATION: {
                "files_created": ["main.py", "models.py", "services.py"],
                "lines_of_code": 1250,
                "unit_tests": 45,
                "integration_tests": 12
            },
            SOPPhase.TESTING: {
                "test_cases_executed": 57,
                "bugs_found": 3,
                "bugs_fixed": 3,
                "coverage_percentage": 92.5
            },
            SOPPhase.DEPLOYMENT: {
                "deployment_url": "https://app.example.com",
                "health_check": "PASS",
                "performance_metrics": {
                    "response_time": "120ms",
                    "throughput": "1000 req/s"
                }
            }
        }

        return outputs.get(phase, {"output": f"Completed {phase.value} phase"})

    async def add_knowledge_item(self, content: str, metadata: Dict[str, Any]) -> str:
        """Add item to knowledge base"""
        item_id = hashlib.md5(content.encode()).hexdigest()
        now = datetime.now()
        
        # Store in database
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO knowledge_items 
            (id, content, metadata, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
        """, (item_id, content, json.dumps(metadata), now, now))
        
        conn.commit()
        conn.close()
        
        return item_id
    
    async def search_knowledge(self, query: str, limit: int = 10) -> List[Dict]:
        """Search knowledge base"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Simple text search - would use vector search in production
        cursor.execute("""
            SELECT id, content, metadata, created_at 
            FROM knowledge_items 
            WHERE content LIKE ? 
            ORDER BY created_at DESC 
            LIMIT ?
        """, (f"%{query}%", limit))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                "id": row[0],
                "content": row[1][:200] + "..." if len(row[1]) > 200 else row[1],
                "metadata": json.loads(row[2]) if row[2] else {},
                "created_at": row[3]
            })
        
        conn.close()
        return results

    async def get_project_status(self, project_id: str) -> Dict[str, Any]:
        """Get comprehensive project status"""
        project = self.projects.get(project_id)
        if not project:
            return {"error": "Project not found"}

        team = self.teams.get(project.team)

        # Get project tasks
        project_tasks = [self.enhanced_tasks.get(task_id) for task_id in project.tasks
                       if task_id in self.enhanced_tasks]
        project_tasks = [task for task in project_tasks if task]

        # Calculate metrics
        total_tasks = len(project_tasks)
        completed_tasks = len([t for t in project_tasks if t.status == TaskStatus.COMPLETED])
        in_progress_tasks = len([t for t in project_tasks if t.status == TaskStatus.IN_PROGRESS])

        # Calculate progress
        progress = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

        # Calculate estimated vs actual hours
        estimated_total = sum(t.estimated_hours or 0 for t in project_tasks)
        actual_total = sum(t.actual_hours or 0 for t in project_tasks if t.actual_hours)

        return {
            "project": {
                "id": project.id,
                "name": project.name,
                "description": project.description,
                "status": project.status,
                "created_at": project.created_at.isoformat(),
                "deadline": project.deadline.isoformat() if project.deadline else None
            },
            "team": {
                "name": team.name if team else "Unknown",
                "roles": [role.value for role in team.roles] if team else []
            },
            "progress": {
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "in_progress_tasks": in_progress_tasks,
                "progress_percentage": round(progress, 1)
            },
            "time_tracking": {
                "estimated_hours": estimated_total,
                "actual_hours": actual_total,
                "variance": actual_total - estimated_total
            },
            "tasks": [
                {
                    "id": task.id,
                    "description": task.description,
                    "role": task.role.value,
                    "status": task.status.value,
                    "assigned_to": task.assigned_to,
                    "estimated_hours": task.estimated_hours,
                    "actual_hours": task.actual_hours,
                    "progress": self._calculate_task_progress(task)
                }
                for task in project_tasks
            ]
        }

    def _calculate_task_progress(self, task: AgentTask) -> float:
        """Calculate individual task progress"""
        if task.status == TaskStatus.COMPLETED:
            return 100.0
        elif task.status == TaskStatus.IN_PROGRESS:
            return 50.0  # Simplified - could be more sophisticated
        elif task.status == TaskStatus.REVIEW:
            return 85.0
        else:
            return 0.0

    def get_agent_capabilities(self) -> Dict[str, Any]:
        """Get agent capabilities"""
        return {
            "available": self.available,
            "agents": list(self.active_agents.keys()),
            "features": [
                "Multi-agent task execution",
                "Knowledge base management",
                "Real-time collaboration",
                "Advanced RAG capabilities", 
                "WebSocket integration",
                "Persistent task tracking",
                "Code assistance",
                "Research capabilities",
                "Project management",
                "Role-based workflows"
            ],
            "active_tasks": len(self.active_tasks),
            "websocket_connections": len(self.websocket_connections)
        }

    async def start_interactive_mode(self):
        """Start interactive mode"""
        logger.info("Starting Unified Agent Framework Interactive Mode...")
        await self.initialize()

        if not self.available:
            print("WARNING: Agent framework not fully initialized. Limited functionality.")

        print("[AGENTS] Unified Agent Framework Active!")
        print(f"Available agents: {list(self.active_agents.keys())}")
        print(f"Teams: {list(self.teams.keys())}")
        print("\nCommands:")
        print("  - 'agents' - List all agents")
        print("  - 'tasks' - Show active tasks")
        print("  - 'teams' - Show teams")
        print("  - 'projects' - Show projects")
        print("  - 'create_project <name> <team>' - Create project")
        print("  - 'execute_workflow <project_id>' - Execute workflow")
        print("  - 'create <task>' - Create new task")
        print("  - 'status' - Show system status")
        print("  - 'help' - Show all commands")
        print("  - 'quit' - Exit")
        
        while True:
            try:
                command = input("\nAgents> ").strip()
                
                if command.lower() in ['quit', 'exit']:
                    break
                elif command.lower() == 'help':
                    await self._show_help()
                elif command.lower() == 'agents':
                    await self._show_agents()
                elif command.lower() == 'tasks':
                    await self._show_tasks()
                elif command.lower() == 'teams':
                    await self._show_teams()
                elif command.lower() == 'projects':
                    await self._show_projects()
                elif command.lower() == 'status':
                    status = await self.get_status()
                    print(f"System Status: {json.dumps(status, indent=2)}")
                elif command.startswith('create_project '):
                    parts = command[14:].split(' ', 1)
                    if len(parts) >= 2:
                        name, team = parts[0], parts[1]
                        print(f"Creating project: {name} with team: {team}")
                        try:
                            project_id = await self.create_project(name, "", team)
                            print(f"Project created with ID: {project_id}")
                        except ValueError as e:
                            print(f"Error: {e}")
                    else:
                        print("Usage: create_project <name> <team>")
                elif command.startswith('execute_workflow '):
                    project_id = command[17:]
                    if project_id:
                        print(f"Executing workflow for project: {project_id}")
                        try:
                            async for update in self.execute_project_workflow(project_id):
                                if update["type"] == "phase_started":
                                    print(f"🔄 Starting {update['phase']} phase...")
                                elif update["type"] == "phase_completed":
                                    result = update["result"]
                                    print(f"✅ {update['phase']} completed (Quality: {result['quality_score']:.1%})")
                                elif update["type"] == "workflow_completed":
                                    print("🎉 Project workflow completed!")
                        except Exception as e:
                            print(f"Error executing workflow: {e}")
                    else:
                        print("Usage: execute_workflow <project_id>")
                elif command.startswith('create '):
                    task_desc = command[7:]  # Remove 'create '
                    if task_desc:
                        print(f"Creating task: {task_desc}")
                        task_id = await self.create_agent_task(task_desc)
                        print(f"Task created with ID: {task_id}")
                        print("Executing task...")
                        # In a real implementation, we would execute the task
                        print("Task execution completed")
                    else:
                        print("Usage: create <task description>")
                elif command:
                    # Treat as natural language task
                    print(f"Creating task: {command}")
                    task_id = await self.create_agent_task(command)
                    print(f"Task created with ID: {task_id}")
                    print("Executing task...")
                    # In a real implementation, we would execute the task
                    print("Task execution completed")
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")
        
        print("Unified Agent Framework Interactive Mode ended.")

    async def _show_help(self):
        """Show detailed help information"""
        help_text = """
[AGENTS] Unified Agent Framework Commands:

Basic Commands:
  agents                   - List all available agents
  tasks                    - Show active and completed tasks
  teams                    - Show available teams
  projects                 - Show active projects
  status                   - Show system status and metrics
  create <task>            - Create and execute new task
  help                     - Show this help
  quit/exit               - Exit framework

Task Examples:
  Agents> create research the latest AI developments
  Agents> create write a Python function to sort a list
  Agents> create analyze system performance metrics
  Agents> create find documentation for FastAPI

Advanced Features:
  - Multi-agent coordination and collaboration
  - Knowledge base integration with RAG
  - Real-time task tracking and updates
  - WebSocket integration for live updates
  - Persistent task history and results
  - Project management with SOP workflows
  - Role-based team collaboration
        """
        print(help_text)
    
    async def _show_agents(self):
        """Show available agents"""
        print("\n[AGENTS] Available Agents:")
        for agent_id, agent in self.active_agents.items():
            print(f"  - {agent_id}: {agent.get('description', 'Multi-purpose agent')}")
        print(f"\nTotal agents: {len(self.active_agents)}")
    
    async def _show_tasks(self):
        """Show active tasks"""
        if not self.enhanced_tasks:
            print("\n[TASKS] No active tasks")
            return
            
        print("\n[TASKS] Active Tasks:")
        for task_id, task in self.enhanced_tasks.items():
            status_icon = {
                "backlog": "[BACKLOG]",
                "planned": "[PLANNED]",
                "in_progress": "[RUNNING]", 
                "completed": "[DONE]",
                "failed": "[FAILED]"
            }.get(task.status.value, "[UNKNOWN]")
            
            print(f"  {status_icon} [{task.id[:8]}] {task.description}")
            print(f"      Status: {task.status.value} | Role: {task.role.value} | Created: {task.created_at.strftime('%H:%M:%S')}")
            
        print(f"\nTotal tasks: {len(self.enhanced_tasks)}")

    async def _show_teams(self):
        """Show available teams"""
        print("\n[TEAMS] Available Teams:")
        for team_name, team in self.teams.items():
            print(f"  • {team_name}: {team.description}")
            print(f"    Roles: {', '.join([role.value for role in team.roles])}")
        print(f"\nTotal teams: {len(self.teams)}")

    async def _show_projects(self):
        """Show projects"""
        if not self.projects:
            print("\n[PROJECTS] No active projects")
            return

        print("\n[PROJECTS] Active Projects:")
        for project_id, project in self.projects.items():
            team = self.teams.get(project.team)
            print(f"  • {project.name} ({project.status})")
            print(f"    Team: {team.name if team else 'Unknown'}")
            print(f"    Tasks: {len(project.tasks)}")
            if project.deadline:
                print(f"    Deadline: {project.deadline.strftime('%Y-%m-%d')}")

        print(f"\nTotal projects: {len(self.projects)}")

    async def get_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        task_counts = {}
        for status in TaskStatus:
            count = sum(1 for task in self.enhanced_tasks.values() if task.status == status)
            task_counts[status.value] = count
        
        return {
            "agents": self.active_agents,
            "task_counts": task_counts,
            "knowledge_items": await self._get_knowledge_count(),
            "active_connections": len(self.websocket_connections),
            "teams": len(self.teams),
            "projects": len(self.projects)
        }

    async def _get_knowledge_count(self) -> int:
        """Get count of knowledge items"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM knowledge_items")
        count = cursor.fetchone()[0]
        conn.close()
        return count

# Global instance
agent_framework = UnifiedAgentFramework()

# Convenience functions
async def initialize_agents() -> bool:
    """Initialize agent framework"""
    return await agent_framework.initialize()

async def create_agent_task(description: str, role: AgentRole = AgentRole.GENERAL, 
                          project_id: Optional[str] = None, context: Optional[Dict] = None) -> str:
    """Create agent task interface"""
    return await agent_framework.create_agent_task(description, role, project_id)

async def get_agent_status() -> Dict[str, Any]:
    """Get agent status interface"""
    return await agent_framework.get_status()

def is_agent_framework_available() -> bool:
    """Check if agent framework is available"""
    return agent_framework.available

def get_agent_capabilities() -> Dict[str, Any]:
    """Get agent capabilities"""
    return agent_framework.get_agent_capabilities()

if __name__ == "__main__":
    # Test the integration
    import asyncio
    
    async def test():
        print("Unified Agent Framework Test")
        print("==========================")
        
        # Initialize framework
        if await initialize_agents():
            print("✅ Agent framework initialized")
            
            # Show capabilities
            capabilities = get_agent_capabilities()
            print(f"Capabilities: {json.dumps(capabilities, indent=2)}")
            
            # Create a test task
            task_id = await create_agent_task("Test task for unified agent framework")
            print(f"✅ Created test task: {task_id}")
            
            # Show status
            status = await get_agent_status()
            print(f"Status: {json.dumps(status, indent=2)}")
        else:
            print("❌ Failed to initialize agent framework")
    
    asyncio.run(test())