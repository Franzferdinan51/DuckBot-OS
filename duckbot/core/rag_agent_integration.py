#!/usr/bin/env python3
"""
RAG Agent Integration Module for DuckBot
Integrates RAG system with multi-agent framework for enhanced agent coordination.
"""

import os
import json
import time
import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple, Union, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
from pathlib import Path
import hashlib

# Local imports
from .enhanced_rag import EnhancedRAG, Document, DocumentType, SearchResult
from .agent_framework import AgentFramework
from .logging_setup import get_logger
from .utilities import safe_read_file

logger = get_logger(__name__)


class AgentRole(Enum):
    """Agent roles in the RAG system."""
    RETRIEVER = "retriever"            # Specialized in information retrieval
    PROCESSOR = "processor"            # Specialized in information processing
    COORDINATOR = "coordinator"        # Coordinates agent activities
    ANALYZER = "analyzer"              # Analyzes information quality
    SYNTHESIZER = "synthesizer"        # Synthesizes information
    VALIDATOR = "validator"            # Validates information accuracy
    LEARNER = "learner"                # Learns from interactions
    SPECIALIST = "specialist"          # Domain specialist


class AgentTaskType(Enum):
    """Types of tasks agents can perform."""
    DOCUMENT_RETRIEVAL = "document_retrieval"
    CONTEXT_BUILDING = "context_building"
    QUERY_OPTIMIZATION = "query_optimization"
    RESULT_FILTERING = "result_filtering"
    QUALITY_ASSESSMENT = "quality_assessment"
    KNOWLEDGE_SYNTHESIS = "knowledge_synthesis"
    CROSS_REFERENCE = "cross_reference"
    FEEDBACK_GENERATION = "feedback_generation"


class AgentCollaborationMode(Enum):
    """Agent collaboration modes."""
    SEQUENTIAL = "sequential"          # Agents work in sequence
    PARALLEL = "parallel"             # Agents work in parallel
    HIERARCHICAL = "hierarchical"     # Hierarchical coordination
    PEER_TO_PEER = "peer_to_peer"     # Direct peer collaboration
    SWARM = "swarm"                   # Swarm intelligence approach


@dataclass
class AgentCapability:
    """Agent capability definition."""
    name: str
    description: str
    task_types: List[AgentTaskType]
    expertise_domains: List[str]
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    confidence_threshold: float = 0.7
    max_concurrent_tasks: int = 3


@dataclass
class AgentTask:
    """Task for RAG agents."""
    id: str
    task_type: AgentTaskType
    input_data: Dict[str, Any]
    assigned_agent: Optional[str] = None
    priority: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    deadline: Optional[datetime] = None
    dependencies: List[str] = field(default_factory=list)
    result: Optional[Dict[str, Any]] = None
    status: str = "pending"  # pending, assigned, in_progress, completed, failed
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentKnowledge:
    """Knowledge representation for agents."""
    id: str
    content: str
    agent_id: str
    knowledge_type: str
    confidence: float
    source: str
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)
    usage_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RAGAgentConfig:
    """Configuration for RAG-agent integration."""
    # Agent settings
    max_agents: int = 8
    collaboration_mode: AgentCollaborationMode = AgentCollaborationMode.HIERARCHICAL
    enable_specialization: bool = True
    enable_learning: bool = True

    # Task management
    max_pending_tasks: int = 100
    task_timeout: int = 300  # 5 minutes
    enable_task_prioritization: bool = True
    enable_task_dependencies: bool = True

    # Knowledge sharing
    enable_knowledge_sharing: bool = True
    knowledge_sharing_threshold: float = 0.8
    max_knowledge_entries: int = 1000

    # Performance settings
    performance_tracking: bool = True
    agent_selection_strategy: str = "performance_based"  # performance_based, load_balanced, round_robin
    max_concurrent_tasks_per_agent: int = 3

    # Coordination settings
    coordinator_agent_id: str = "rag_coordinator"
    enable_agent_communication: bool = True
    communication_protocol: str = "message_queue"  # message_queue, direct, pub_sub

    # Debug settings
    debug_agents: bool = False
    log_agent_activities: bool = True


class RAGAgentIntegration:
    """
    Integration between RAG system and multi-agent framework.
    """

    def __init__(self, rag_system: EnhancedRAG, agent_framework: AgentFramework,
                 config: Optional[RAGAgentConfig] = None):
        self.rag_system = rag_system
        self.agent_framework = agent_framework
        self.config = config or RAGAgentConfig()
        self.logger = get_logger(__name__)

        # Initialize agent systems
        self.agents: Dict[str, Dict[str, Any]] = {}
        self.agent_capabilities: Dict[str, AgentCapability] = {}
        self.agent_knowledge: Dict[str, AgentKnowledge] = {}

        # Task management
        self.pending_tasks: Dict[str, AgentTask] = {}
        self.active_tasks: Dict[str, AgentTask] = {}
        self.completed_tasks: Dict[str, AgentTask] = {}

        # Performance tracking
        self.agent_performance: Dict[str, Dict[str, float]] = {}
        self.task_statistics: Dict[str, Any] = {}

        # Communication system
        self.message_queue: List[Dict[str, Any]] = []
        self.agent_subscriptions: Dict[str, Set[str]] = {}

        # Background tasks
        self._task_scheduler: Optional[asyncio.Task] = None
        self._knowledge_updater: Optional[asyncio.Task] = None
        self._performance_monitor: Optional[asyncio.Task] = None

        # Initialize systems
        self._initialize_agents()
        self._start_background_tasks()

        self.logger.info("RAG-Agent Integration initialized")

    def _initialize_agents(self):
        """Initialize RAG-specialized agents."""
        try:
            # Create coordinator agent
            coordinator = self._create_agent(
                agent_id=self.config.coordinator_agent_id,
                role=AgentRole.COORDINATOR,
                capabilities=[
                    AgentCapability(
                        name="task_coordination",
                        description="Coordinates agent activities and task distribution",
                        task_types=[AgentTaskType.CONTEXT_BUILDING, AgentTaskType.QUERY_OPTIMIZATION],
                        expertise_domains=["coordination", "planning"],
                        confidence_threshold=0.9
                    )
                ]
            )

            # Create specialized agents
            specialist_agents = [
                (AgentRole.RETRIEVER, "document_retrieval", [
                    AgentTaskType.DOCUMENT_RETRIEVAL, AgentTaskType.RESULT_FILTERING
                ], ["search", "retrieval", "information"]),
                (AgentRole.PROCESSOR, "information_processing", [
                    AgentTaskType.CONTEXT_BUILDING, AgentTaskType.KNOWLEDGE_SYNTHESIS
                ], ["processing", "analysis", "synthesis"]),
                (AgentRole.ANALYZER, "quality_analysis", [
                    AgentTaskType.QUALITY_ASSESSMENT, AgentTaskType.VALIDATION
                ], ["analysis", "validation", "quality"]),
                (AgentRole.SYNTHESIZER, "knowledge_synthesis", [
                    AgentTaskType.KNOWLEDGE_SYNTHESIS, AgentTaskType.CROSS_REFERENCE
                ], ["synthesis", "integration", "reasoning"]),
                (AgentRole.LEARNER, "learning_optimization", [
                    AgentTaskType.FEEDBACK_GENERATION
                ], ["learning", "optimization", "adaptation"])
            ]

            for role, name, task_types, domains in specialist_agents:
                agent_id = f"rag_{role.value}_{hashlib.md5(name.encode()).hexdigest()[:8]}"
                self._create_agent(
                    agent_id=agent_id,
                    role=role,
                    capabilities=[
                        AgentCapability(
                            name=name,
                            description=f"Specialized in {name}",
                            task_types=task_types,
                            expertise_domains=domains,
                            confidence_threshold=0.7
                        )
                    ]
                )

            self.logger.info(f"Initialized {len(self.agents)} RAG agents")

        except Exception as e:
            self.logger.error(f"Error initializing agents: {e}")
            raise

    def _create_agent(self, agent_id: str, role: AgentRole, capabilities: List[AgentCapability]):
        """Create a RAG agent."""
        try:
            agent_data = {
                "id": agent_id,
                "role": role.value,
                "capabilities": capabilities,
                "status": "active",
                "current_tasks": [],
                "completed_tasks": 0,
                "failed_tasks": 0,
                "performance_score": 0.0,
                "knowledge_base": [],
                "created_at": datetime.now(),
                "last_activity": datetime.now()
            }

            self.agents[agent_id] = agent_data
            self.agent_capabilities[agent_id] = capabilities[0]  # Primary capability
            self.agent_performance[agent_id] = {
                "task_success_rate": 0.0,
                "avg_completion_time": 0.0,
                "quality_score": 0.0,
                "efficiency_score": 0.0
            }

            # Register with agent framework
            self.agent_framework.register_agent(agent_id, {
                "role": role.value,
                "capabilities": [cap.name for cap in capabilities],
                "rag_specialized": True
            })

            self.logger.debug(f"Created agent: {agent_id} ({role.value})")

        except Exception as e:
            self.logger.error(f"Error creating agent {agent_id}: {e}")
            raise

    def _start_background_tasks(self):
        """Start background agent management tasks."""
        self._task_scheduler = asyncio.create_task(self._task_scheduling_loop())
        self._knowledge_updater = asyncio.create_task(self._knowledge_update_loop())
        self._performance_monitor = asyncio.create_task(self._performance_monitoring_loop())

        self.logger.info("Background agent tasks started")

    async def _task_scheduling_loop(self):
        """Background task for scheduling agent tasks."""
        while True:
            try:
                await asyncio.sleep(1)  # Check every second

                # Process pending tasks
                await self._process_pending_tasks()

                # Check for task timeouts
                await self._check_task_timeouts()

                # Update agent loads
                await self._update_agent_loads()

            except Exception as e:
                self.logger.error(f"Error in task scheduling loop: {e}")
                await asyncio.sleep(5)  # Wait before retrying

    async def _knowledge_update_loop(self):
        """Background task for updating agent knowledge."""
        while True:
            try:
                await asyncio.sleep(60)  # Update every minute

                if self.config.enable_knowledge_sharing:
                    await self._share_agent_knowledge()

                if self.config.enable_learning:
                    await self._update_agent_learning()

            except Exception as e:
                self.logger.error(f"Error in knowledge update loop: {e}")
                await asyncio.sleep(30)  # Wait before retrying

    async def _performance_monitoring_loop(self):
        """Background task for monitoring agent performance."""
        while True:
            try:
                await asyncio.sleep(300)  # Monitor every 5 minutes

                if self.config.performance_tracking:
                    await self._update_agent_performance()
                    await self._optimize_agent_allocation()

            except Exception as e:
                self.logger.error(f"Error in performance monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait before retrying

    async def submit_task(self, task_type: AgentTaskType, input_data: Dict[str, Any],
                         priority: int = 0, deadline: Optional[datetime] = None,
                         dependencies: Optional[List[str]] = None) -> str:
        """
        Submit a task to the RAG agent system.

        Args:
            task_type: Type of task
            input_data: Input data for the task
            priority: Task priority (higher = more important)
            deadline: Task deadline
            dependencies: Task dependencies

        Returns:
            Task ID
        """
        try:
            task_id = hashlib.md5(f"{task_type.value}:{time.time()}:{json.dumps(input_data)}".encode()).hexdigest()

            task = AgentTask(
                id=task_id,
                task_type=task_type,
                input_data=input_data,
                priority=priority,
                deadline=deadline,
                dependencies=dependencies or []
            )

            # Check task limit
            if len(self.pending_tasks) >= self.config.max_pending_tasks:
                # Remove lowest priority task
                lowest_priority_task = min(self.pending_tasks.values(), key=lambda t: t.priority)
                del self.pending_tasks[lowest_priority_task.id]

            self.pending_tasks[task_id] = task

            if self.config.debug_agents:
                self.logger.debug(f"Task submitted: {task_id} ({task_type.value})")

            return task_id

        except Exception as e:
            self.logger.error(f"Error submitting task: {e}")
            raise

    async def get_task_result(self, task_id: str, timeout: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Get result for a task.

        Args:
            task_id: Task ID
            timeout: Timeout in seconds

        Returns:
            Task result or None if not completed
        """
        try:
            start_time = time.time()

            while True:
                # Check if task is completed
                if task_id in self.completed_tasks:
                    return self.completed_tasks[task_id].result

                # Check if task failed
                if task_id in self.completed_tasks and self.completed_tasks[task_id].status == "failed":
                    return {"error": "Task failed"}

                # Check timeout
                if timeout and (time.time() - start_time) > timeout:
                    return {"error": "Timeout"}

                await asyncio.sleep(0.1)

        except Exception as e:
            self.logger.error(f"Error getting task result: {e}")
            return None

    async def _process_pending_tasks(self):
        """Process pending tasks and assign to agents."""
        try:
            if not self.pending_tasks:
                return

            # Sort tasks by priority
            sorted_tasks = sorted(
                self.pending_tasks.values(),
                key=lambda t: t.priority,
                reverse=True
            )

            for task in sorted_tasks:
                if len(self.active_tasks) >= self.config.max_agents * self.config.max_concurrent_tasks_per_agent:
                    break

                # Check dependencies
                if task.dependencies:
                    if not all(dep_id in self.completed_tasks for dep_id in task.dependencies):
                        continue

                # Select best agent for task
                agent_id = await self._select_agent_for_task(task)
                if agent_id:
                    await self._assign_task_to_agent(task, agent_id)

        except Exception as e:
            self.logger.error(f"Error processing pending tasks: {e}")

    async def _select_agent_for_task(self, task: AgentTask) -> Optional[str]:
        """Select the best agent for a task."""
        try:
            # Get capable agents
            capable_agents = []
            for agent_id, agent_data in self.agents.items():
                # Check if agent can handle task type
                agent_capability = self.agent_capabilities.get(agent_id)
                if agent_capability and task.task_type in agent_capability.task_types:
                    # Check agent load
                    current_load = len(agent_data["current_tasks"])
                    if current_load < self.config.max_concurrent_tasks_per_agent:
                        capable_agents.append((agent_id, agent_data, agent_capability))

            if not capable_agents:
                return None

            # Select agent based on strategy
            if self.config.agent_selection_strategy == "performance_based":
                # Select based on performance score
                best_agent = max(capable_agents, key=lambda x: x[1]["performance_score"])
                return best_agent[0]
            elif self.config.agent_selection_strategy == "load_balanced":
                # Select based on current load
                best_agent = min(capable_agents, key=lambda x: len(x[1]["current_tasks"]))
                return best_agent[0]
            elif self.config.agent_selection_strategy == "round_robin":
                # Select in round-robin fashion
                return capable_agents[0][0]
            else:
                return capable_agents[0][0]

        except Exception as e:
            self.logger.error(f"Error selecting agent for task: {e}")
            return None

    async def _assign_task_to_agent(self, task: AgentTask, agent_id: str):
        """Assign a task to an agent."""
        try:
            # Update task status
            task.assigned_agent = agent_id
            task.status = "assigned"

            # Move to active tasks
            self.active_tasks[task.id] = task
            del self.pending_tasks[task.id]

            # Update agent data
            self.agents[agent_id]["current_tasks"].append(task.id)

            # Execute task
            asyncio.create_task(self._execute_agent_task(task, agent_id))

            if self.config.debug_agents:
                self.logger.debug(f"Task {task.id} assigned to agent {agent_id}")

        except Exception as e:
            self.logger.error(f"Error assigning task to agent: {e}")
            # Revert task status
            task.status = "pending"
            task.assigned_agent = None
            self.pending_tasks[task.id] = task
            if task.id in self.active_tasks:
                del self.active_tasks[task.id]

    async def _execute_agent_task(self, task: AgentTask, agent_id: str):
        """Execute a task using the assigned agent."""
        try:
            # Update task status
            task.status = "in_progress"

            # Get agent
            agent_data = self.agents[agent_id]
            agent_capability = self.agent_capabilities[agent_id]

            # Execute based on task type
            start_time = time.time()

            if task.task_type == AgentTaskType.DOCUMENT_RETRIEVAL:
                result = await self._execute_document_retrieval(task, agent_data)
            elif task.task_type == AgentTaskType.CONTEXT_BUILDING:
                result = await self._execute_context_building(task, agent_data)
            elif task.task_type == AgentTaskType.QUERY_OPTIMIZATION:
                result = await self._execute_query_optimization(task, agent_data)
            elif task.task_type == AgentTaskType.RESULT_FILTERING:
                result = await self._execute_result_filtering(task, agent_data)
            elif task.task_type == AgentTaskType.QUALITY_ASSESSMENT:
                result = await self._execute_quality_assessment(task, agent_data)
            elif task.task_type == AgentTaskType.KNOWLEDGE_SYNTHESIS:
                result = await self._execute_knowledge_synthesis(task, agent_data)
            elif task.task_type == AgentTaskType.CROSS_REFERENCE:
                result = await self._execute_cross_reference(task, agent_data)
            elif task.task_type == AgentTaskType.FEEDBACK_GENERATION:
                result = await self._execute_feedback_generation(task, agent_data)
            else:
                result = {"error": f"Unknown task type: {task.task_type}"}

            completion_time = time.time() - start_time

            # Update task
            task.result = result
            task.status = "completed" if "error" not in result else "failed"

            # Move to completed tasks
            self.completed_tasks[task.id] = task
            if task.id in self.active_tasks:
                del self.active_tasks[task.id]

            # Update agent statistics
            agent_data["current_tasks"].remove(task.id)
            if task.status == "completed":
                agent_data["completed_tasks"] += 1
            else:
                agent_data["failed_tasks"] += 1

            agent_data["last_activity"] = datetime.now()

            # Update performance metrics
            await self._update_agent_task_performance(agent_id, task, completion_time, result)

            # Log completion
            if self.config.log_agent_activities:
                self.logger.info(f"Agent {agent_id} completed task {task.id} in {completion_time:.3f}s")

        except Exception as e:
            self.logger.error(f"Error executing agent task {task.id}: {e}")
            # Mark task as failed
            task.status = "failed"
            task.result = {"error": str(e)}
            self.completed_tasks[task.id] = task
            if task.id in self.active_tasks:
                del self.active_tasks[task.id]

            # Update agent
            if agent_id in self.agents:
                self.agents[agent_id]["current_tasks"].remove(task.id)
                self.agents[agent_id]["failed_tasks"] += 1

    async def _execute_document_retrieval(self, task: AgentTask, agent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute document retrieval task."""
        try:
            query = task.input_data.get("query", "")
            filters = task.input_data.get("filters", {})
            top_k = task.input_data.get("top_k", 5)

            # Perform search
            search_results = await self.rag_system.search(query, top_k=top_k, filters=filters)

            # Add agent knowledge to results
            relevant_knowledge = await self._get_relevant_agent_knowledge(query, agent_data["id"])
            if relevant_knowledge:
                search_results.extend(relevant_knowledge)

            return {
                "search_results": [
                    {
                        "chunk_id": result.chunk.id,
                        "document_id": result.document.id,
                        "content": result.chunk.content,
                        "score": result.score,
                        "metadata": result.metadata
                    }
                    for result in search_results
                ],
                "agent_id": agent_data["id"],
                "task_type": "document_retrieval"
            }

        except Exception as e:
            return {"error": str(e)}

    async def _execute_context_building(self, task: AgentTask, agent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute context building task."""
        try:
            search_results = task.input_data.get("search_results", [])
            query = task.input_data.get("query", "")
            max_length = task.input_data.get("max_length", 2000)

            # Build context from search results
            context_parts = []
            total_length = 0

            for result in search_results:
                if total_length >= max_length:
                    break

                content = result.get("content", "")
                if total_length + len(content) <= max_length:
                    context_parts.append(content)
                    total_length += len(content)
                else:
                    remaining_space = max_length - total_length
                    context_parts.append(content[:remaining_space])
                    total_length = max_length

            context = "\n\n".join(context_parts)

            return {
                "context": context,
                "context_length": total_length,
                "agent_id": agent_data["id"],
                "task_type": "context_building"
            }

        except Exception as e:
            return {"error": str(e)}

    async def _execute_query_optimization(self, task: AgentTask, agent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute query optimization task."""
        try:
            query = task.input_data.get("query", "")
            context = task.input_data.get("context", "")

            # Simple query optimization
            optimized_query = query

            # Add context terms if available
            if context:
                context_keywords = self._extract_keywords(context)
                for keyword in context_keywords[:3]:
                    if keyword.lower() not in query.lower():
                        optimized_query = f"{optimized_query} {keyword}"

            return {
                "original_query": query,
                "optimized_query": optimized_query,
                "optimization_type": "keyword_expansion",
                "agent_id": agent_data["id"],
                "task_type": "query_optimization"
            }

        except Exception as e:
            return {"error": str(e)}

    async def _execute_result_filtering(self, task: AgentTask, agent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute result filtering task."""
        try:
            search_results = task.input_data.get("search_results", [])
            relevance_threshold = task.input_data.get("relevance_threshold", 0.3)

            # Filter results by relevance
            filtered_results = [
                result for result in search_results
                if result.get("score", 0) >= relevance_threshold
            ]

            # Sort by relevance
            filtered_results.sort(key=lambda x: x.get("score", 0), reverse=True)

            return {
                "filtered_results": filtered_results,
                "original_count": len(search_results),
                "filtered_count": len(filtered_results),
                "agent_id": agent_data["id"],
                "task_type": "result_filtering"
            }

        except Exception as e:
            return {"error": str(e)}

    async def _execute_quality_assessment(self, task: AgentTask, agent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute quality assessment task."""
        try:
            search_results = task.input_data.get("search_results", [])
            query = task.input_data.get("query", "")

            # Assess quality of each result
            quality_scores = []
            for result in search_results:
                score = await self._assess_result_quality(result, query)
                quality_scores.append(score)

            # Calculate overall quality
            overall_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0

            return {
                "quality_scores": quality_scores,
                "overall_quality": overall_quality,
                "assessment_method": "relevance_and_completeness",
                "agent_id": agent_data["id"],
                "task_type": "quality_assessment"
            }

        except Exception as e:
            return {"error": str(e)}

    async def _execute_knowledge_synthesis(self, task: AgentTask, agent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute knowledge synthesis task."""
        try:
            search_results = task.input_data.get("search_results", [])
            query = task.input_data.get("query", "")

            # Synthesize knowledge from multiple sources
            synthesized_content = await self._synthesize_knowledge(search_results, query)

            return {
                "synthesized_content": synthesized_content,
                "source_count": len(search_results),
                "synthesis_method": "content_aggregation",
                "agent_id": agent_data["id"],
                "task_type": "knowledge_synthesis"
            }

        except Exception as e:
            return {"error": str(e)}

    async def _execute_cross_reference(self, task: AgentTask, agent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute cross-reference task."""
        try:
            search_results = task.input_data.get("search_results", [])

            # Find cross-references between results
            cross_references = []
            for i, result1 in enumerate(search_results):
                for j, result2 in enumerate(search_results[i+1:], i+1):
                    similarity = await self._calculate_result_similarity(result1, result2)
                    if similarity > 0.5:
                        cross_references.append({
                            "result1_index": i,
                            "result2_index": j,
                            "similarity": similarity
                        })

            return {
                "cross_references": cross_references,
                "total_comparisons": len(search_results) * (len(search_results) - 1) // 2,
                "agent_id": agent_data["id"],
                "task_type": "cross_reference"
            }

        except Exception as e:
            return {"error": str(e)}

    async def _execute_feedback_generation(self, task: AgentTask, agent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute feedback generation task."""
        try:
            task_result = task.input_data.get("task_result", {})
            user_feedback = task.input_data.get("user_feedback", "")

            # Generate feedback for agent improvement
            feedback_analysis = await self._analyze_feedback(task_result, user_feedback)

            return {
                "feedback_analysis": feedback_analysis,
                "improvement_suggestions": feedback_analysis.get("suggestions", []),
                "agent_id": agent_data["id"],
                "task_type": "feedback_generation"
            }

        except Exception as e:
            return {"error": str(e)}

    async def _assess_result_quality(self, result: Dict[str, Any], query: str) -> float:
        """Assess the quality of a search result."""
        try:
            # Simple quality assessment based on:
            # - Relevance to query
            # - Content length
            # - Score

            relevance_score = result.get("score", 0)
            content = result.get("content", "")

            # Length score (prefer medium-length content)
            length_score = 1.0 - abs(len(content) - 500) / 1000
            length_score = max(0, min(1, length_score))

            # Query relevance
            query_words = set(query.lower().split())
            content_words = set(content.lower().split())
            query_relevance = len(query_words.intersection(content_words)) / len(query_words) if query_words else 0

            # Combined quality score
            quality_score = (relevance_score * 0.5 + length_score * 0.3 + query_relevance * 0.2)

            return quality_score

        except Exception as e:
            self.logger.error(f"Error assessing result quality: {e}")
            return 0.0

    async def _synthesize_knowledge(self, search_results: List[Dict[str, Any]], query: str) -> str:
        """Synthesize knowledge from multiple search results."""
        try:
            if not search_results:
                return ""

            # Extract key points from each result
            key_points = []
            for result in search_results:
                content = result.get("content", "")
                # Simple key point extraction (first few sentences)
                sentences = content.split('.')
                if sentences:
                    key_points.append(sentences[0].strip())

            # Combine key points
            synthesized = "Based on the retrieved information:\n\n"
            for i, point in enumerate(key_points[:5]):  # Limit to 5 points
                synthesized += f"{i+1}. {point}.\n"

            return synthesized

        except Exception as e:
            self.logger.error(f"Error synthesizing knowledge: {e}")
            return ""

    async def _calculate_result_similarity(self, result1: Dict[str, Any], result2: Dict[str, Any]) -> float:
        """Calculate similarity between two results."""
        try:
            content1 = result1.get("content", "")
            content2 = result2.get("content", "")

            # Simple text similarity
            words1 = set(content1.lower().split())
            words2 = set(content2.lower().split())

            if not words1 or not words2:
                return 0.0

            intersection = words1.intersection(words2)
            union = words1.union(words2)

            return len(intersection) / len(union)

        except Exception as e:
            self.logger.error(f"Error calculating result similarity: {e}")
            return 0.0

    async def _analyze_feedback(self, task_result: Dict[str, Any], user_feedback: str) -> Dict[str, Any]:
        """Analyze user feedback for agent improvement."""
        try:
            # Simple feedback analysis
            analysis = {
                "feedback_received": bool(user_feedback),
                "feedback_length": len(user_feedback),
                "suggestions": []
            }

            # Extract improvement suggestions
            if user_feedback:
                if "helpful" in user_feedback.lower():
                    analysis["suggestions"].append("Continue current approach")
                elif "not helpful" in user_feedback.lower():
                    analysis["suggestions"].append("Consider alternative approaches")
                elif "more information" in user_feedback.lower():
                    analysis["suggestions"].append("Provide more detailed responses")

            return analysis

        except Exception as e:
            self.logger.error(f"Error analyzing feedback: {e}")
            return {"error": str(e)}

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text."""
        try:
            # Simple keyword extraction
            words = text.lower().split()
            # Filter out common words and short words
            stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"}
            keywords = [word for word in words if len(word) > 3 and word not in stop_words]

            # Return unique keywords
            return list(set(keywords))

        except Exception as e:
            self.logger.error(f"Error extracting keywords: {e}")
            return []

    async def _get_relevant_agent_knowledge(self, query: str, agent_id: str) -> List[Dict[str, Any]]:
        """Get relevant knowledge from agent."""
        try:
            relevant_knowledge = []

            for knowledge_id, knowledge in self.agent_knowledge.items():
                if knowledge.agent_id == agent_id:
                    # Simple relevance check
                    if query.lower() in knowledge.content.lower():
                        relevant_knowledge.append({
                            "knowledge_id": knowledge_id,
                            "content": knowledge.content,
                            "confidence": knowledge.confidence,
                            "source": knowledge.source
                        })

            return relevant_knowledge

        except Exception as e:
            self.logger.error(f"Error getting relevant agent knowledge: {e}")
            return []

    async def _check_task_timeouts(self):
        """Check for task timeouts."""
        try:
            current_time = datetime.now()

            for task_id, task in list(self.active_tasks.items()):
                if task.deadline and current_time > task.deadline:
                    # Task timed out
                    task.status = "failed"
                    task.result = {"error": "Task timeout"}

                    # Move to completed tasks
                    self.completed_tasks[task_id] = task
                    del self.active_tasks[task_id]

                    # Update agent
                    if task.assigned_agent and task.assigned_agent in self.agents:
                        agent_data = self.agents[task.assigned_agent]
                        agent_data["current_tasks"].remove(task_id)
                        agent_data["failed_tasks"] += 1

                    self.logger.warning(f"Task {task_id} timed out")

        except Exception as e:
            self.logger.error(f"Error checking task timeouts: {e}")

    async def _update_agent_loads(self):
        """Update agent load information."""
        try:
            for agent_id, agent_data in self.agents.items():
                current_load = len(agent_data["current_tasks"])
                max_capacity = self.config.max_concurrent_tasks_per_agent

                # Update agent status based on load
                if current_load >= max_capacity:
                    agent_data["status"] = "overloaded"
                elif current_load >= max_capacity * 0.8:
                    agent_data["status"] = "busy"
                else:
                    agent_data["status"] = "active"

        except Exception as e:
            self.logger.error(f"Error updating agent loads: {e}")

    async def _share_agent_knowledge(self):
        """Share knowledge between agents."""
        try:
            # Get knowledge to share
            knowledge_to_share = []

            for knowledge_id, knowledge in self.agent_knowledge.items():
                if knowledge.confidence >= self.config.knowledge_sharing_threshold:
                    knowledge_to_share.append(knowledge)

            # Share with other agents
            for knowledge in knowledge_to_share:
                for agent_id in self.agents.keys():
                    if agent_id != knowledge.agent_id:
                        # Add knowledge to agent's knowledge base
                        if agent_id not in self.agent_knowledge:
                            # Create shared knowledge entry
                            shared_knowledge = AgentKnowledge(
                                id=f"{knowledge.id}_shared_{agent_id}",
                                content=knowledge.content,
                                agent_id=agent_id,
                                knowledge_type=knowledge.knowledge_type,
                                confidence=knowledge.confidence * 0.9,  # Slightly reduced confidence
                                source=f"shared_from_{knowledge.agent_id}"
                            )
                            self.agent_knowledge[shared_knowledge.id] = shared_knowledge

        except Exception as e:
            self.logger.error(f"Error sharing agent knowledge: {e}")

    async def _update_agent_learning(self):
        """Update agent learning based on experience."""
        try:
            for agent_id, agent_data in self.agents.items():
                # Calculate performance metrics
                total_tasks = agent_data["completed_tasks"] + agent_data["failed_tasks"]
                if total_tasks > 0:
                    success_rate = agent_data["completed_tasks"] / total_tasks

                    # Update performance score
                    agent_data["performance_score"] = success_rate

                    # Learn from recent tasks
                    recent_tasks = [t for t in self.completed_tasks.values() if t.assigned_agent == agent_id]
                    if recent_tasks:
                        # Analyze recent performance
                        recent_success = sum(1 for t in recent_tasks if t.status == "completed")
                        recent_success_rate = recent_success / len(recent_tasks)

                        # Adjust confidence based on recent performance
                        if agent_id in self.agent_capabilities:
                            capability = self.agent_capabilities[agent_id]
                            if recent_success_rate > 0.8:
                                capability.confidence_threshold = min(0.95, capability.confidence_threshold + 0.01)
                            elif recent_success_rate < 0.5:
                                capability.confidence_threshold = max(0.5, capability.confidence_threshold - 0.01)

        except Exception as e:
            self.logger.error(f"Error updating agent learning: {e}")

    async def _update_agent_performance(self):
        """Update agent performance metrics."""
        try:
            for agent_id, agent_data in self.agents.items():
                # Get recent tasks for this agent
                recent_tasks = [t for t in self.completed_tasks.values() if t.assigned_agent == agent_id][-50:]

                if recent_tasks:
                    # Calculate performance metrics
                    successful_tasks = [t for t in recent_tasks if t.status == "completed"]
                    task_success_rate = len(successful_tasks) / len(recent_tasks)

                    # Calculate average completion time
                    completion_times = []
                    for task in recent_tasks:
                        if task.status == "completed" and "completion_time" in task.metadata:
                            completion_times.append(task.metadata["completion_time"])

                    avg_completion_time = sum(completion_times) / len(completion_times) if completion_times else 0

                    # Update performance tracking
                    self.agent_performance[agent_id]["task_success_rate"] = task_success_rate
                    self.agent_performance[agent_id]["avg_completion_time"] = avg_completion_time

        except Exception as e:
            self.logger.error(f"Error updating agent performance: {e}")

    async def _update_agent_task_performance(self, agent_id: str, task: AgentTask, completion_time: float, result: Dict[str, Any]):
        """Update agent performance after task completion."""
        try:
            # Add completion time to task metadata
            task.metadata["completion_time"] = completion_time

            # Update agent performance
            performance = self.agent_performance.get(agent_id, {})
            if performance:
                # Update success rate
                total_tasks = performance.get("total_tasks", 0) + 1
                successful_tasks = performance.get("successful_tasks", 0) + (1 if task.status == "completed" else 0)
                performance["task_success_rate"] = successful_tasks / total_tasks

                # Update average completion time
                current_avg = performance.get("avg_completion_time", 0)
                performance["avg_completion_time"] = (current_avg * (total_tasks - 1) + completion_time) / total_tasks

                performance["total_tasks"] = total_tasks
                performance["successful_tasks"] = successful_tasks

        except Exception as e:
            self.logger.error(f"Error updating agent task performance: {e}")

    async def _optimize_agent_allocation(self):
        """Optimize agent allocation based on performance."""
        try:
            # Analyze agent performance and suggest optimizations
            for agent_id, performance in self.agent_performance.items():
                if performance.get("task_success_rate", 0) < 0.5:
                    # Low-performing agent - consider retraining or reallocation
                    self.logger.warning(f"Agent {agent_id} has low success rate: {performance['task_success_rate']:.2f}")

                if performance.get("avg_completion_time", 0) > 60:  # More than 1 minute
                    # Slow agent - consider load balancing
                    self.logger.warning(f"Agent {agent_id} has high average completion time: {performance['avg_completion_time']:.2f}s")

        except Exception as e:
            self.logger.error(f"Error optimizing agent allocation: {e}")

    def get_agent_stats(self) -> Dict[str, Any]:
        """Get agent system statistics."""
        try:
            return {
                "total_agents": len(self.agents),
                "active_agents": len([a for a in self.agents.values() if a["status"] == "active"]),
                "busy_agents": len([a for a in self.agents.values() if a["status"] == "busy"]),
                "overloaded_agents": len([a for a in self.agents.values() if a["status"] == "overloaded"]),
                "pending_tasks": len(self.pending_tasks),
                "active_tasks": len(self.active_tasks),
                "completed_tasks": len(self.completed_tasks),
                "agent_performance": self.agent_performance,
                "total_knowledge_entries": len(self.agent_knowledge),
                "config": {
                    "max_agents": self.config.max_agents,
                    "collaboration_mode": self.config.collaboration_mode.value,
                    "enable_specialization": self.config.enable_specialization,
                    "enable_learning": self.config.enable_learning
                }
            }

        except Exception as e:
            self.logger.error(f"Error getting agent stats: {e}")
            return {}

    async def close(self):
        """Clean up resources."""
        try:
            # Cancel background tasks
            if self._task_scheduler:
                self._task_scheduler.cancel()
            if self._knowledge_updater:
                self._knowledge_updater.cancel()
            if self._performance_monitor:
                self._performance_monitor.cancel()

            # Save agent states
            await self._save_agent_states()

            self.logger.info("RAG-Agent Integration closed")

        except Exception as e:
            self.logger.error(f"Error closing agent integration: {e}")

    async def _save_agent_states(self):
        """Save agent states to file."""
        try:
            states = {
                "agents": self.agents,
                "agent_performance": self.agent_performance,
                "agent_knowledge": {
                    k: {
                        "content": v.content,
                        "agent_id": v.agent_id,
                        "knowledge_type": v.knowledge_type,
                        "confidence": v.confidence,
                        "source": v.source,
                        "usage_count": v.usage_count
                    }
                    for k, v in self.agent_knowledge.items()
                },
                "timestamp": datetime.now().isoformat()
            }

            with open("data/rag_agent_states.json", "w") as f:
                json.dump(states, f, indent=2, default=str)

        except Exception as e:
            self.logger.error(f"Error saving agent states: {e}")


# Global instance
_rag_agent_integration: Optional[RAGAgentIntegration] = None


def get_rag_agent_integration(rag_system: EnhancedRAG, agent_framework: AgentFramework,
                            config: Optional[RAGAgentConfig] = None) -> RAGAgentIntegration:
    """Get or create the global RAG-Agent integration instance."""
    global _rag_agent_integration

    if _rag_agent_integration is None:
        _rag_agent_integration = RAGAgentIntegration(rag_system, agent_framework, config)

    return _rag_agent_integration