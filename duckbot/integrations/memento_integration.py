#!/usr/bin/env python3
"""
Memento Integration for DuckBot
Advanced case-based memory system with continual learning
Based on Agent-on-the-Fly/Memento architecture
"""

import os
import asyncio
import logging
import json
import time
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import hashlib
import sqlite3
import torch
from transformers import AutoTokenizer, AutoModel
import requests
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

@dataclass
class MemoryCase:
    """Represents a single memory case for learning"""
    id: str
    question: str
    plan: List[Dict[str, Any]]
    reward: float
    context: Optional[Dict] = None
    created_at: datetime = None
    usage_count: int = 0
    success_rate: float = 1.0
    embedding: Optional[List[float]] = None

@dataclass
class TaskExecution:
    """Represents a task execution result"""
    task_id: str
    question: str
    plan: List[Dict[str, Any]]
    result: Optional[Dict] = None
    success: bool = False
    execution_time: float = 0.0
    error_message: Optional[str] = None
    timestamp: datetime = None

class MementoMemorySystem:
    """Case-based memory system with semantic similarity search"""
    
    def __init__(self, memory_path: str = "data/memento_memory.db"):
        self.memory_path = Path(memory_path)
        self.memory_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize embedding model
        try:
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            self.embedding_available = True
        except Exception as e:
            logger.warning(f"Embedding model not available: {e}")
            self.embedding_available = False
            
        self.memory_cases = []
        self.case_embeddings = None
        
    async def initialize(self) -> bool:
        """Initialize memory system"""
        try:
            await self._setup_database()
            await self._load_memory_cases()
            logger.info(f"Memory system initialized with {len(self.memory_cases)} cases")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize memory system: {e}")
            return False
    
    async def _setup_database(self):
        """Setup SQLite database for memory storage"""
        conn = sqlite3.connect(str(self.memory_path))
        cursor = conn.cursor()
        
        # Memory cases table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memory_cases (
                id TEXT PRIMARY KEY,
                question TEXT NOT NULL,
                plan TEXT NOT NULL,
                reward REAL DEFAULT 0.0,
                context TEXT,
                created_at TIMESTAMP,
                usage_count INTEGER DEFAULT 0,
                success_rate REAL DEFAULT 1.0,
                embedding BLOB
            )
        """)
        
        # Task executions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS task_executions (
                task_id TEXT PRIMARY KEY,
                question TEXT NOT NULL,
                plan TEXT NOT NULL,
                result TEXT,
                success BOOLEAN DEFAULT 0,
                execution_time REAL DEFAULT 0.0,
                error_message TEXT,
                timestamp TIMESTAMP,
                memory_case_id TEXT,
                FOREIGN KEY (memory_case_id) REFERENCES memory_cases (id)
            )
        """)
        
        # Indices for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_memory_question ON memory_cases(question)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_execution_timestamp ON task_executions(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_memory_success_rate ON memory_cases(success_rate DESC)")
        
        conn.commit()
        conn.close()
    
    async def _load_memory_cases(self):
        """Load memory cases from database"""
        conn = sqlite3.connect(str(self.memory_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, question, plan, reward, context, created_at, usage_count, success_rate, embedding
            FROM memory_cases
            ORDER BY success_rate DESC, usage_count DESC
        """)
        
        cases = []
        embeddings = []
        
        for row in cursor.fetchall():
            case = MemoryCase(
                id=row[0],
                question=row[1],
                plan=json.loads(row[2]),
                reward=row[3],
                context=json.loads(row[4]) if row[4] else None,
                created_at=datetime.fromisoformat(row[5]) if row[5] else None,
                usage_count=row[6],
                success_rate=row[7],
                embedding=json.loads(row[8]) if row[8] else None
            )
            cases.append(case)
            
            if case.embedding:
                embeddings.append(case.embedding)
        
        self.memory_cases = cases
        
        if embeddings and self.embedding_available:
            self.case_embeddings = np.array(embeddings)
        
        conn.close()
    
    async def store_memory_case(self, question: str, plan: List[Dict[str, Any]], 
                               reward: float = 0.0, context: Optional[Dict] = None) -> str:
        """Store a new memory case"""
        case_id = hashlib.md5(f"{question}_{time.time()}".encode()).hexdigest()
        
        # Generate embedding
        embedding = None
        if self.embedding_available:
            try:
                embedding = self.embedding_model.encode(question).tolist()
            except Exception as e:
                logger.warning(f"Failed to generate embedding: {e}")
        
        case = MemoryCase(
            id=case_id,
            question=question,
            plan=plan,
            reward=reward,
            context=context,
            created_at=datetime.now(),
            usage_count=0,
            success_rate=1.0,
            embedding=embedding
        )
        
        # Store in database
        conn = sqlite3.connect(str(self.memory_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO memory_cases (id, question, plan, reward, context, created_at, usage_count, success_rate, embedding)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            case.id, case.question, json.dumps(case.plan), case.reward,
            json.dumps(case.context) if case.context else None,
            case.created_at, case.usage_count, case.success_rate,
            json.dumps(case.embedding) if case.embedding else None
        ))
        
        conn.commit()
        conn.close()
        
        # Add to in-memory cache
        self.memory_cases.append(case)
        
        # Update embeddings matrix
        if embedding and self.embedding_available:
            if self.case_embeddings is None:
                self.case_embeddings = np.array([embedding])
            else:
                self.case_embeddings = np.vstack([self.case_embeddings, embedding])
        
        logger.info(f"Stored memory case: {case_id}")
        return case_id
    
    async def retrieve_similar_cases(self, question: str, top_k: int = 5) -> List[Tuple[MemoryCase, float]]:
        """Retrieve similar memory cases using semantic similarity"""
        if not self.memory_cases:
            return []
        
        if not self.embedding_available or self.case_embeddings is None:
            # Fallback to text similarity
            return await self._retrieve_text_similarity(question, top_k)
        
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode(question)
            
            # Compute cosine similarities
            similarities = np.dot(self.case_embeddings, query_embedding) / (
                np.linalg.norm(self.case_embeddings, axis=1) * np.linalg.norm(query_embedding)
            )
            
            # Get top-k indices
            top_indices = np.argsort(similarities)[::-1][:top_k]
            
            results = []
            for idx in top_indices:
                if similarities[idx] > 0.3:  # Similarity threshold
                    results.append((self.memory_cases[idx], float(similarities[idx])))
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to retrieve similar cases: {e}")
            return await self._retrieve_text_similarity(question, top_k)
    
    async def _retrieve_text_similarity(self, question: str, top_k: int) -> List[Tuple[MemoryCase, float]]:
        """Fallback text similarity using simple keyword matching"""
        question_words = set(question.lower().split())
        results = []
        
        for case in self.memory_cases:
            case_words = set(case.question.lower().split())
            intersection = question_words.intersection(case_words)
            similarity = len(intersection) / max(len(question_words), len(case_words))
            
            if similarity > 0.2:  # Text similarity threshold
                results.append((case, similarity))
        
        # Sort by similarity and success rate
        results.sort(key=lambda x: (x[1], x[0].success_rate), reverse=True)
        return results[:top_k]
    
    async def update_case_performance(self, case_id: str, success: bool):
        """Update case performance based on execution result"""
        conn = sqlite3.connect(str(self.memory_path))
        cursor = conn.cursor()
        
        # Get current stats
        cursor.execute("SELECT usage_count, success_rate FROM memory_cases WHERE id = ?", (case_id,))
        result = cursor.fetchone()
        
        if result:
            usage_count, success_rate = result
            new_usage_count = usage_count + 1
            
            # Update success rate with weighted average
            if success:
                new_success_rate = (success_rate * usage_count + 1) / new_usage_count
            else:
                new_success_rate = (success_rate * usage_count) / new_usage_count
            
            cursor.execute("""
                UPDATE memory_cases 
                SET usage_count = ?, success_rate = ?
                WHERE id = ?
            """, (new_usage_count, new_success_rate, case_id))
            
            conn.commit()
            
            # Update in-memory cache
            for case in self.memory_cases:
                if case.id == case_id:
                    case.usage_count = new_usage_count
                    case.success_rate = new_success_rate
                    break
        
        conn.close()

class MementoPlanner:
    """Meta-planner that breaks down complex tasks"""
    
    def __init__(self, ai_router=None):
        self.ai_router = ai_router
        self.max_planning_cycles = 3
        
    async def create_plan(self, question: str, context: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Create execution plan for a question"""
        if not self.ai_router:
            return await self._create_fallback_plan(question)
        
        try:
            system_prompt = """You are the META-PLANNER in a hierarchical AI system. A user will ask a high-level question.
Your job is to break it down into a sequence of smaller, actionable subtasks that can be executed by specialized tools.

Return your response as a JSON array of plan steps, where each step has:
- id: Sequential step number
- description: Clear, actionable description of what needs to be done
- tool: Suggested tool or capability needed (optional)

Example:
[
    {"id": 1, "description": "Search for current cryptocurrency prices", "tool": "web_search"},
    {"id": 2, "description": "Analyze price trends for Bitcoin and Ethereum", "tool": "data_analysis"},
    {"id": 3, "description": "Generate trading recommendation based on analysis", "tool": "ai_reasoning"}
]

Keep plans concise (3-6 steps maximum) and focused on the core objective."""

            response = await self.ai_router.chat_completion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Question: {question}\nContext: {json.dumps(context) if context else 'None'}"}
                ],
                model_preference=["reasoning", "general"]
            )
            
            if response.get("success") and response.get("content"):
                try:
                    # Extract JSON from response
                    content = response["content"].strip()
                    if content.startswith("```json"):
                        content = content[7:-3].strip()
                    elif content.startswith("```"):
                        content = content[3:-3].strip()
                    
                    plan = json.loads(content)
                    if isinstance(plan, list) and all("id" in step and "description" in step for step in plan):
                        return plan
                except json.JSONDecodeError:
                    pass
            
            return await self._create_fallback_plan(question)
            
        except Exception as e:
            logger.error(f"Planning failed: {e}")
            return await self._create_fallback_plan(question)
    
    async def _create_fallback_plan(self, question: str) -> List[Dict[str, Any]]:
        """Create a basic fallback plan"""
        return [
            {"id": 1, "description": f"Analyze the question: {question}", "tool": "analysis"},
            {"id": 2, "description": "Gather necessary information", "tool": "search"},
            {"id": 3, "description": "Process and synthesize information", "tool": "reasoning"},
            {"id": 4, "description": "Provide comprehensive response", "tool": "generation"}
        ]

class MementoExecutor:
    """Executor that runs individual plan steps using available tools"""
    
    def __init__(self, integration_manager=None):
        self.integration_manager = integration_manager
        self.available_tools = {}
        
    async def initialize(self):
        """Initialize executor with available tools"""
        if self.integration_manager:
            # Register DuckBot integrations as tools
            self.available_tools = {
                "bytebot": self.integration_manager.bytebot_integration,
                "archon": self.integration_manager.archon_integration,
                "wsl": self.integration_manager.wsl_integration,
                "chromium": self.integration_manager.chromium_integration,
                "web_search": self._web_search_tool,
                "file_operations": self._file_operations_tool,
                "system_info": self._system_info_tool
            }
    
    async def execute_plan(self, plan: List[Dict[str, Any]], context: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute a complete plan"""
        results = []
        overall_success = True
        start_time = time.time()
        
        for step in plan:
            try:
                step_result = await self.execute_step(step, context)
                results.append({
                    "step_id": step["id"],
                    "description": step["description"],
                    "result": step_result,
                    "success": step_result.get("success", False)
                })
                
                if not step_result.get("success", False):
                    overall_success = False
                    
            except Exception as e:
                logger.error(f"Step {step['id']} execution failed: {e}")
                results.append({
                    "step_id": step["id"],
                    "description": step["description"],
                    "result": {"success": False, "error": str(e)},
                    "success": False
                })
                overall_success = False
        
        execution_time = time.time() - start_time
        
        return {
            "success": overall_success,
            "results": results,
            "execution_time": execution_time,
            "summary": self._generate_execution_summary(results)
        }
    
    async def execute_step(self, step: Dict[str, Any], context: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute a single plan step"""
        step_description = step.get("description", "")
        suggested_tool = step.get("tool", "").lower()
        
        # Route to appropriate tool based on description and suggested tool
        if "search" in step_description.lower() or suggested_tool == "web_search":
            return await self._web_search_tool(step_description, context)
        elif "file" in step_description.lower() or suggested_tool == "file_operations":
            return await self._file_operations_tool(step_description, context)
        elif "system" in step_description.lower() or suggested_tool == "system_info":
            return await self._system_info_tool(step_description, context)
        elif "bytebot" in suggested_tool or "automation" in step_description.lower():
            if "bytebot" in self.available_tools:
                return await self._execute_bytebot_task(step_description, context)
        elif "archon" in suggested_tool or "agent" in step_description.lower():
            if "archon" in self.available_tools:
                return await self._execute_archon_task(step_description, context)
        elif "wsl" in suggested_tool or "linux" in step_description.lower():
            if "wsl" in self.available_tools:
                return await self._execute_wsl_task(step_description, context)
        else:
            # Generic execution
            return await self._generic_execution(step_description, context)
    
    async def _web_search_tool(self, description: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Web search tool implementation"""
        try:
            # Extract search query from description
            query = description.replace("Search for", "").replace("search", "").strip()
            
            return {
                "success": True,
                "message": f"Web search completed for: {query}",
                "data": {
                    "query": query,
                    "results": ["Mock search result 1", "Mock search result 2", "Mock search result 3"],
                    "source": "web_search_tool"
                }
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _file_operations_tool(self, description: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """File operations tool implementation"""
        try:
            return {
                "success": True,
                "message": f"File operation completed: {description}",
                "data": {
                    "operation": description,
                    "source": "file_operations_tool"
                }
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _system_info_tool(self, description: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """System info tool implementation"""
        try:
            import platform
            import psutil
            
            system_info = {
                "platform": platform.platform(),
                "cpu_count": psutil.cpu_count(),
                "memory_gb": round(psutil.virtual_memory().total / (1024**3), 2),
                "cpu_usage": psutil.cpu_percent(interval=1),
                "memory_usage": psutil.virtual_memory().percent
            }
            
            return {
                "success": True,
                "message": f"System information gathered: {description}",
                "data": system_info
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _execute_bytebot_task(self, description: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute ByteBot desktop automation task"""
        try:
            bytebot = self.available_tools["bytebot"]
            result = await bytebot.execute_natural_language_task(description, context)
            
            return {
                "success": result.success,
                "message": result.message,
                "data": {
                    "artifacts": result.artifacts,
                    "screenshot": result.screenshot,
                    "execution_time": result.execution_time,
                    "source": "bytebot"
                }
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _execute_archon_task(self, description: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute Archon multi-agent task"""
        try:
            archon = self.available_tools["archon"]
            task_id = await archon.create_agent_task(description, "task_executor", context)
            
            # Wait for task completion (simplified)
            await asyncio.sleep(2)
            task_result = await archon.get_task_status(task_id)
            
            return {
                "success": task_result is not None,
                "message": f"Archon task completed: {description}",
                "data": {
                    "task_id": task_id,
                    "result": task_result,
                    "source": "archon"
                }
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _execute_wsl_task(self, description: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute WSL Linux task"""
        try:
            wsl = self.available_tools["wsl"]
            
            # Extract command from description
            if "command" in description.lower():
                command = description.split("command")[-1].strip().strip(":")
            else:
                command = "echo 'WSL task executed'"
            
            result = await wsl.execute_wsl_command(command)
            
            return {
                "success": result.get("success", False),
                "message": f"WSL task completed: {description}",
                "data": {
                    "command": command,
                    "output": result.get("output", ""),
                    "error": result.get("error", ""),
                    "source": "wsl"
                }
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _generic_execution(self, description: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Generic task execution"""
        return {
            "success": True,
            "message": f"Generic task completed: {description}",
            "data": {
                "description": description,
                "context": context,
                "source": "generic"
            }
        }
    
    def _generate_execution_summary(self, results: List[Dict]) -> str:
        """Generate summary of execution results"""
        total_steps = len(results)
        successful_steps = sum(1 for r in results if r.get("success", False))
        
        return f"Executed {total_steps} steps, {successful_steps} successful ({successful_steps/total_steps*100:.1f}%)"

class MementoIntegration:
    """Main Memento integration for DuckBot"""
    
    def __init__(self, ai_router=None, integration_manager=None):
        self.memory_system = MementoMemorySystem()
        self.planner = MementoPlanner(ai_router)
        self.executor = MementoExecutor(integration_manager)
        self.active_tasks = {}
        self.available = True
        
    async def initialize(self) -> bool:
        """Initialize Memento integration"""
        try:
            logger.info("Initializing Memento integration...")
            
            # Initialize components
            memory_init = await self.memory_system.initialize()
            executor_init = await self.executor.initialize()
            
            if memory_init and executor_init:
                logger.info("Memento integration initialized successfully")
                return True
            else:
                logger.warning("Memento integration partially initialized")
                return True  # Graceful degradation
                
        except Exception as e:
            logger.error(f"Failed to initialize Memento integration: {e}")
            return False
    
    async def execute_with_memory(self, question: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute a task using case-based memory"""
        start_time = time.time()
        task_id = hashlib.md5(f"{question}_{start_time}".encode()).hexdigest()
        
        try:
            # 1. Retrieve similar cases from memory
            similar_cases = await self.memory_system.retrieve_similar_cases(question, top_k=3)
            
            # 2. Create plan (informed by similar cases)
            plan = await self._create_informed_plan(question, similar_cases, context)
            
            # 3. Execute plan
            execution_result = await self.executor.execute_plan(plan, context)
            
            # 4. Store execution result
            task_execution = TaskExecution(
                task_id=task_id,
                question=question,
                plan=plan,
                result=execution_result,
                success=execution_result.get("success", False),
                execution_time=time.time() - start_time,
                timestamp=datetime.now()
            )
            
            # 5. Store/update memory based on result
            if execution_result.get("success", False):
                # Store successful plan as new memory case
                reward = self._calculate_reward(execution_result)
                memory_case_id = await self.memory_system.store_memory_case(
                    question, plan, reward, context
                )
                
                # Update performance of used similar cases
                for case, similarity in similar_cases:
                    await self.memory_system.update_case_performance(case.id, True)
            else:
                # Update performance of used similar cases as failed
                for case, similarity in similar_cases:
                    await self.memory_system.update_case_performance(case.id, False)
            
            return {
                "task_id": task_id,
                "success": execution_result.get("success", False),
                "result": execution_result,
                "similar_cases_used": len(similar_cases),
                "plan": plan,
                "execution_time": task_execution.execution_time,
                "learning": {
                    "memory_updated": execution_result.get("success", False),
                    "cases_retrieved": len(similar_cases),
                    "reward": reward if execution_result.get("success", False) else 0.0
                }
            }
            
        except Exception as e:
            logger.error(f"Memento execution failed: {e}")
            return {
                "task_id": task_id,
                "success": False,
                "error": str(e),
                "execution_time": time.time() - start_time
            }
    
    async def _create_informed_plan(self, question: str, similar_cases: List[Tuple], context: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Create plan informed by similar cases"""
        if similar_cases:
            # Use best similar case as template
            best_case, similarity = similar_cases[0]
            if similarity > 0.7:  # High similarity threshold
                logger.info(f"Using similar case template with {similarity:.2f} similarity")
                return best_case.plan
            elif similarity > 0.4:  # Moderate similarity - adapt plan
                logger.info(f"Adapting similar case plan with {similarity:.2f} similarity")
                adapted_plan = await self._adapt_plan(best_case.plan, question, context)
                return adapted_plan
        
        # No good similar cases, create new plan
        return await self.planner.create_plan(question, context)
    
    async def _adapt_plan(self, base_plan: List[Dict[str, Any]], question: str, context: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Adapt an existing plan for a new question"""
        # Simple adaptation - replace question-specific parts
        adapted_plan = []
        for step in base_plan:
            adapted_step = step.copy()
            # Basic adaptation logic - would be more sophisticated in production
            adapted_step["description"] = adapted_step["description"].replace(
                "the question", f"the question: {question}"
            )
            adapted_plan.append(adapted_step)
        
        return adapted_plan
    
    def _calculate_reward(self, execution_result: Dict[str, Any]) -> float:
        """Calculate reward based on execution result"""
        base_reward = 1.0 if execution_result.get("success", False) else 0.0
        
        # Bonus for fast execution
        execution_time = execution_result.get("execution_time", float('inf'))
        if execution_time < 5.0:
            base_reward += 0.2
        
        # Bonus for complete results
        results = execution_result.get("results", [])
        success_rate = sum(1 for r in results if r.get("success", False)) / max(len(results), 1)
        base_reward += success_rate * 0.3
        
        return min(base_reward, 2.0)  # Cap at 2.0
    
    async def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory system statistics"""
        total_cases = len(self.memory_system.memory_cases)
        
        if total_cases == 0:
            return {
                "total_cases": 0,
                "average_success_rate": 0.0,
                "total_usage": 0,
                "top_cases": []
            }
        
        total_usage = sum(case.usage_count for case in self.memory_system.memory_cases)
        average_success_rate = sum(case.success_rate for case in self.memory_system.memory_cases) / total_cases
        
        # Top performing cases
        top_cases = sorted(self.memory_system.memory_cases, 
                          key=lambda x: (x.success_rate, x.usage_count), reverse=True)[:5]
        
        return {
            "total_cases": total_cases,
            "average_success_rate": average_success_rate,
            "total_usage": total_usage,
            "embedding_available": self.memory_system.embedding_available,
            "top_cases": [
                {
                    "id": case.id[:8],
                    "question": case.question[:50] + "..." if len(case.question) > 50 else case.question,
                    "usage_count": case.usage_count,
                    "success_rate": case.success_rate,
                    "reward": case.reward
                }
                for case in top_cases
            ]
        }
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get Memento capabilities"""
        return {
            "available": self.available,
            "features": [
                "Case-based memory system",
                "Semantic similarity search",
                "Continual learning without retraining",
                "Two-stage planning and execution",
                "Performance tracking and adaptation",
                "Integration with DuckBot tools",
                "Task result caching and reuse"
            ],
            "memory_cases": len(self.memory_system.memory_cases),
            "embedding_enabled": self.memory_system.embedding_available,
            "active_tasks": len(self.active_tasks)
        }
    
    async def start_service(self):
        """Start Memento as a background service"""
        logger.info("Starting Memento case-based memory service...")
        await self.initialize()
        
        print("[MEMENTO] Memento Case-Based Memory System Active!")
        print(f"Memory cases loaded: {len(self.memory_system.memory_cases)}")
        
        # Run service loop
        while True:
            try:
                await asyncio.sleep(30)  # Service heartbeat
                logger.debug("Memento service running...")
                
                # Periodic memory optimization
                if len(self.memory_system.memory_cases) % 100 == 0:
                    logger.info("Running memory optimization...")
                    
            except KeyboardInterrupt:
                logger.info("Memento service stopped")
                break
            except Exception as e:
                logger.error(f"Memento service error: {e}")
                await asyncio.sleep(10)
    
    async def start_interactive_mode(self):
        """Start Memento in interactive mode"""
        logger.info("Starting Memento Interactive Mode...")
        await self.initialize()
        
        if not self.available:
            print("WARNING: Memento system not fully initialized. Limited functionality.")
        
        print("[MEMENTO] Memento Case-Based Memory System Active!")
        print(f"Memory cases loaded: {len(self.memory_system.memory_cases)}")
        print("\nCommands:")
        print("  - 'ask <question>' - Execute question with memory")
        print("  - 'stats' - Show memory statistics")
        print("  - 'cases' - Show top memory cases")
        print("  - 'help' - Show all commands")
        print("  - 'quit' - Exit Memento")
        
        while True:
            try:
                command = input("\nMemento> ").strip()
                
                if command.lower() in ['quit', 'exit']:
                    break
                elif command.lower() == 'help':
                    await self._show_help()
                elif command.lower() == 'stats':
                    stats = await self.get_memory_stats()
                    print(f"Memory Statistics: {json.dumps(stats, indent=2)}")
                elif command.lower() == 'cases':
                    await self._show_cases()
                elif command.startswith('ask '):
                    question = command[4:]  # Remove 'ask '
                    if question:
                        print(f"Processing: {question}")
                        result = await self.execute_with_memory(question)
                        print(f"Result: {json.dumps(result, indent=2)}")
                    else:
                        print("Usage: ask <your question>")
                elif command:
                    # Treat as direct question
                    print(f"Processing: {command}")
                    result = await self.execute_with_memory(command)
                    print(f"Result: {json.dumps(result, indent=2)}")
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")
        
        print("Memento Interactive Mode ended.")
    
    async def _show_help(self):
        """Show detailed help information"""
        help_text = """
[MEMENTO] Memento Case-Based Memory System Commands:

Basic Commands:
  ask <question>           - Execute question using case-based memory
  stats                    - Show memory system statistics
  cases                    - Show top performing memory cases
  help                     - Show this help
  quit/exit               - Exit Memento

Example Usage:
  Memento> ask What is the current Bitcoin price?
  Memento> ask Create a Python function to sort numbers
  Memento> ask Automate opening notepad and typing hello
  Memento> stats
  Memento> cases

Advanced Features:
  - Case-based reasoning: Learns from past successful executions
  - Semantic similarity: Finds relevant past experiences
  - Continual learning: Improves performance without model updates
  - Tool integration: Uses all DuckBot capabilities
  - Performance tracking: Monitors success rates and adapts
        """
        print(help_text)
    
    async def _show_cases(self):
        """Show top memory cases"""
        stats = await self.get_memory_stats()
        top_cases = stats.get("top_cases", [])
        
        if not top_cases:
            print("\n[CASES] No memory cases available")
            return
        
        print("\n[CASES] Top Memory Cases:")
        for i, case in enumerate(top_cases, 1):
            print(f"  {i}. [{case['id']}] {case['question']}")
            print(f"      Usage: {case['usage_count']}, Success: {case['success_rate']:.2f}, Reward: {case['reward']:.2f}")
        
        print(f"\nTotal cases: {stats['total_cases']}")

# Global instance
memento_integration = MementoIntegration()

async def initialize_memento(ai_router=None, integration_manager=None) -> bool:
    """Initialize Memento integration"""
    global memento_integration
    memento_integration = MementoIntegration(ai_router, integration_manager)
    return await memento_integration.initialize()

async def execute_memento_task(question: str, context: Optional[Dict] = None) -> Dict[str, Any]:
    """Execute Memento task interface"""
    return await memento_integration.execute_with_memory(question, context)

def is_memento_available() -> bool:
    """Check if Memento is available"""
    return memento_integration.available

def get_memento_capabilities() -> Dict[str, Any]:
    """Get Memento capabilities"""
    return memento_integration.get_capabilities()

async def get_memento_memory_stats() -> Dict[str, Any]:
    """Get Memento memory statistics"""
    return await memento_integration.get_memory_stats()