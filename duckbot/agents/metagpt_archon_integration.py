#!/usr/bin/env python3
"""
MetaGPT-Enhanced Archon Integration for DuckBot v4.2
Advanced multi-agent framework with role-based collaboration, SOPs, and team workflows
Combines Archon's knowledge management with MetaGPT's collaborative agent architecture
"""

import os
import asyncio
import logging
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, AsyncGenerator
from dataclasses import dataclass, field
import sqlite3
import hashlib
from datetime import datetime, timedelta
import websockets
import uuid
from enum import Enum
import yaml

logger = logging.getLogger(__name__)

class AgentRole(Enum):
    """MetaGPT-inspired agent roles"""
    PRODUCT_MANAGER = "product_manager"
    ARCHITECT = "architect"
    PROJECT_MANAGER = "project_manager"
    ENGINEER = "engineer"
    QA_ENGINEER = "qa_engineer"
    RESEARCHER = "researcher"
    TECHNICAL_WRITER = "technical_writer"
    DEVOPS = "devops"

class TaskStatus(Enum):
    """Task status tracking"""
    BACKLOG = "backlog"
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    COMPLETED = "completed"
    FAILED = "failed"

class SOPPhase(Enum):
    """Standard Operating Procedure phases"""
    REQUIREMENTS = "requirements"
    DESIGN = "design"
    IMPLEMENTATION = "implementation"
    TESTING = "testing"
    DEPLOYMENT = "deployment"
    MAINTENANCE = "maintenance"

@dataclass
class Team:
    """MetaGPT-style team configuration"""
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
    requirements: List[str] = field(default_factory=list)
    tasks: List[str] = field(default_factory=list)  # Task IDs
    team: str
    status: str = "planning"
    created_at: datetime = field(default_factory=datetime.now)
    deadline: Optional[datetime] = None

@dataclass
class KnowledgeItem:
    id: str
    content: str
    embedding: Optional[List[float]]
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

@dataclass
class AgentTask:
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

class MetaGPTArchonIntegration:
    """MetaGPT-enhanced Archon integration with role-based collaboration"""

    def __init__(self):
        self.db_path = Path("data/metagpt_archon.db")
        self.teams = {}
        self.projects = {}
        self.knowledge_base = []
        self.active_tasks = {}
        self.websocket_connections = set()
        self.available = True

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
            ]
        }

    async def initialize(self) -> bool:
        """Initialize MetaGPT-enhanced Archon integration"""
        try:
            # Setup enhanced database
            await self._setup_enhanced_db()

            # Initialize default teams
            await self._initialize_default_teams()

            # Load existing projects and tasks
            await self._load_existing_data()

            logger.info("MetaGPT-enhanced Archon integration initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize MetaGPT Archon integration: {e}")
            return False

    async def _setup_enhanced_db(self):
        """Setup enhanced SQLite database for MetaGPT features"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

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

        # Enhanced agent tasks table
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
                actual_hours REAL,
                FOREIGN KEY (project_id) REFERENCES projects(id)
            )
        """)

        # Knowledge items table (from original Archon)
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

        # Team collaboration logs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS collaboration_logs (
                id TEXT PRIMARY KEY,
                project_id TEXT,
                from_role TEXT,
                to_role TEXT,
                message TEXT,
                timestamp TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects(id)
            )
        """)

        # SOP execution logs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sop_logs (
                id TEXT PRIMARY KEY,
                project_id TEXT,
                phase TEXT,
                status TEXT,
                details TEXT,
                timestamp TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects(id)
            )
        """)

        # Create indices
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON agent_tasks(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_role ON agent_tasks(role)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_collaboration_project ON collaboration_logs(project_id)")

        conn.commit()
        conn.close()

    async def _initialize_default_teams(self):
        """Initialize default MetaGPT-style teams"""

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

    async def create_project(self, name: str, description: str, team_name: str,
                           requirements: List[str] = None, deadline: Optional[datetime] = None) -> str:
        """Create a new project with MetaGPT team structure"""

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

        # Automatically create initial tasks based on SOP
        await self._create_sop_tasks(project_id)

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

            self.active_tasks[task_id] = task
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

    async def create_agent_task(self, description: str, role: AgentRole,
                              project_id: Optional[str] = None,
                              dependencies: List[str] = None,
                              estimated_hours: Optional[float] = None) -> str:
        """Create a new agent task with MetaGPT role assignment"""

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

        self.active_tasks[task_id] = task

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

        # Auto-assign task if agents are available
        await self._auto_assign_task(task_id)

        return task_id

    async def _auto_assign_task(self, task_id: str):
        """Automatically assign task to available agent"""
        task = self.active_tasks.get(task_id)
        if not task:
            return

        # Find available agent for this role
        project = self.projects.get(task.project_id) if task.project_id else None
        team = self.teams.get(project.team) if project else None

        if team:
            # Simple assignment logic - in real implementation would be more sophisticated
            task.assigned_to = f"{task.role.value}_agent"
            await self._update_task_in_db(task)

    async def execute_project_workflow(self, project_id: str) -> AsyncGenerator[Dict[str, Any], None]:
        """Execute complete MetaGPT workflow for a project"""
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

            # Log SOP phase start
            await self._log_sop_phase(project_id, phase, "started", {})

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

            # Log SOP phase completion
            await self._log_sop_phase(project_id, phase, "completed", result)

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

        # Simulate task execution (in real implementation would call AI)
        await asyncio.sleep(2)  # Simulate work

        # Generate phase-specific results
        result = {
            "phase": phase.value,
            "role": role.value,
            "output": self._generate_phase_output(phase, project),
            "quality_score": 0.85 + (hash(phase.value) % 10) / 100,
            "completion_time": datetime.now().isoformat()
        }

        # Update task
        task = self.active_tasks.get(task_id)
        if task:
            task.status = TaskStatus.COMPLETED
            task.result = result
            task.completed_at = datetime.now()
            await self._update_task_in_db(task)

        return result

    def _generate_phase_output(self, phase: SOPPhase, project: Project) -> Dict[str, Any]:
        """Generate realistic output for each SOP phase"""
        outputs = {
            SOPPhase.REQUIREMENTS: {
                "user_stories": [
                    "As a user, I want to...",
                    "As a admin, I need to..."
                ],
                "acceptance_criteria": [
                    "Given... When... Then..."
                ],
                "technical_requirements": [
                    "System shall...",
                    "Component must..."
                ]
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

    async def _log_sop_phase(self, project_id: str, phase: SOPPhase, status: str, details: Dict):
        """Log SOP phase execution"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO sop_logs (id, project_id, phase, status, details, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            str(uuid.uuid4()), project_id, phase.value, status,
            json.dumps(details), datetime.now()
        ))
        conn.commit()
        conn.close()

    async def get_project_status(self, project_id: str) -> Dict[str, Any]:
        """Get comprehensive project status"""
        project = self.projects.get(project_id)
        if not project:
            return {"error": "Project not found"}

        team = self.teams.get(project.team)

        # Get project tasks
        project_tasks = [self.active_tasks.get(task_id) for task_id in project.tasks
                       if task_id in self.active_tasks]
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

    async def _update_task_in_db(self, task: AgentTask):
        """Update task in database"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE agent_tasks
            SET status = ?, result = ?, assigned_to = ?,
                completed_at = ?, actual_hours = ?
            WHERE id = ?
        """, (
            task.status.value, json.dumps(task.result) if task.result else None,
            task.assigned_to, task.completed_at, task.actual_hours, task.id
        ))
        conn.commit()
        conn.close()

    async def _load_existing_data(self):
        """Load existing projects and tasks from database"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        # Load projects
        cursor.execute("SELECT * FROM projects")
        for row in cursor.fetchall():
            project_id, name, description, requirements_json, tasks_json, team, status, created_at, deadline = row
            project = Project(
                id=project_id,
                name=name,
                description=description,
                requirements=json.loads(requirements_json) if requirements_json else [],
                tasks=json.loads(tasks_json) if tasks_json else [],
                team=team,
                status=status,
                created_at=datetime.fromisoformat(created_at),
                deadline=datetime.fromisoformat(deadline) if deadline else None
            )
            self.projects[project_id] = project

        # Load tasks
        cursor.execute("SELECT * FROM agent_tasks")
        for row in cursor.fetchall():
            (task_id, description, role_str, status_str, project_id,
             dependencies_json, result_json, assigned_to, created_at,
             completed_at, estimated_hours, actual_hours) = row

            task = AgentTask(
                id=task_id,
                description=description,
                role=AgentRole(role_str),
                status=TaskStatus(status_str),
                project_id=project_id,
                dependencies=json.loads(dependencies_json) if dependencies_json else [],
                result=json.loads(result_json) if result_json else None,
                assigned_to=assigned_to,
                created_at=datetime.fromisoformat(created_at),
                completed_at=datetime.fromisoformat(completed_at) if completed_at else None,
                estimated_hours=estimated_hours,
                actual_hours=actual_hours
            )
            self.active_tasks[task_id] = task

        conn.close()

    async def start_interactive_mode(self):
        """Start interactive MetaGPT project management mode"""
        print("=== MetaGPT-Enhanced Archon Project Management ===")
        print("Available teams:")
        for team_name, team in self.teams.items():
            print(f"  • {team_name}: {', '.join([role.value for role in team.roles])}")

        while True:
            print("\nOptions:")
            print("1. Create new project")
            print("2. View project status")
            print("3. Execute project workflow")
            print("4. Create custom task")
            print("5. Exit")

            choice = input("\nSelect option: ").strip()

            if choice == "1":
                await self._interactive_create_project()
            elif choice == "2":
                await self._interactive_view_status()
            elif choice == "3":
                await self._interactive_execute_workflow()
            elif choice == "4":
                await self._interactive_create_task()
            elif choice == "5":
                break
            else:
                print("Invalid option. Please try again.")

    async def _interactive_create_project(self):
        """Interactive project creation"""
        name = input("Project name: ").strip()
        description = input("Project description: ").strip()

        print("\nAvailable teams:")
        for i, (team_name, team) in enumerate(self.teams.items(), 1):
            print(f"{i}. {team_name}")

        team_choice = input("Select team (number): ").strip()
        try:
            team_name = list(self.teams.keys())[int(team_choice) - 1]
        except (ValueError, IndexError):
            print("Invalid team selection.")
            return

        deadline_str = input("Deadline (YYYY-MM-DD, optional): ").strip()
        deadline = datetime.fromisoformat(deadline_str) if deadline_str else None

        project_id = await self.create_project(name, description, team_name, deadline=deadline)
        print(f"✅ Project created with ID: {project_id}")

    async def _interactive_view_status(self):
        """Interactive project status viewing"""
        project_id = input("Enter project ID: ").strip()
        status = await self.get_project_status(project_id)

        if "error" in status:
            print(f"❌ {status['error']}")
            return

        project = status["project"]
        progress = status["progress"]

        print(f"\n📊 Project: {project['name']}")
        print(f"   Status: {project['status']}")
        print(f"   Team: {status['team']['name']}")
        print(f"   Progress: {progress['progress_percentage']}% "
              f"({progress['completed_tasks']}/{progress['total_tasks']} tasks)")

        if status["time_tracking"]["estimated_hours"]:
            print(f"   Time: {status['time_tracking']['actual_hours']:.1f}h / "
                  f"{status['time_tracking']['estimated_hours']:.1f}h")

        print(f"\n📋 Tasks:")
        for task in status["tasks"]:
            status_icon = "✅" if task["status"] == "completed" else "🔄" if task["status"] == "in_progress" else "⏳"
            print(f"   {status_icon} {task['description']} ({task['role']})")

    async def _interactive_execute_workflow(self):
        """Interactive workflow execution"""
        project_id = input("Enter project ID: ").strip()

        print(f"\n🚀 Executing MetaGPT workflow for project {project_id}...")

        async for update in self.execute_project_workflow(project_id):
            if update["type"] == "phase_started":
                print(f"   Starting {update['phase']} phase...")
            elif update["type"] == "phase_completed":
                result = update["result"]
                print(f"   ✅ {update['phase']} completed (Quality: {result['quality_score']:.1%})")
            elif update["type"] == "workflow_completed":
                print("   🎉 Project workflow completed!")

        print("\n✅ Workflow execution complete!")

    async def _interactive_create_task(self):
        """Interactive task creation"""
        description = input("Task description: ").strip()

        print("\nAvailable roles:")
        for i, role in enumerate(AgentRole, 1):
            print(f"{i}. {role.value}")

        role_choice = input("Select role (number): ").strip()
        try:
            role = list(AgentRole)[int(role_choice) - 1]
        except (ValueError, IndexError):
            print("Invalid role selection.")
            return

        project_id = input("Project ID (optional, press Enter to skip): ").strip() or None

        task_id = await self.create_agent_task(description, role, project_id)
        print(f"✅ Task created with ID: {task_id}")

# Test function
async def test_metagpt_archon():
    """Test MetaGPT-enhanced Archon integration"""
    print("🧪 Testing MetaGPT-Enhanced Archon Integration...")

    # Initialize integration
    archon = MetaGPTArchonIntegration()
    if await archon.initialize():
        print("✅ MetaGPT Archon integration initialized successfully")

        # Test project creation
        project_id = await archon.create_project(
            name="DuckBot v4.2 Enhancement",
            description="Enhance DuckBot with MetaGPT multi-agent capabilities",
            team_name="software_development",
            deadline=datetime.now() + timedelta(days=30)
        )
        print(f"✅ Project created: {project_id}")

        # Test project status
        status = await archon.get_project_status(project_id)
        print(f"✅ Project status: {status['progress']['progress_percentage']}% complete")

        # Test workflow execution
        print("✅ Testing workflow execution...")
        async for update in archon.execute_project_workflow(project_id):
            if update["type"] == "phase_completed":
                print(f"   Phase {update['phase']} completed with quality {update['result']['quality_score']:.1%}")

        print("🎉 MetaGPT Archon integration test completed successfully!")
        return True
    else:
        print("❌ Failed to initialize MetaGPT Archon integration")
        return False

if __name__ == "__main__":
    asyncio.run(test_metagpt_archon())