#!/usr/bin/env python3
"""
RAG Commands Module for DuckBot Agents
Provides RAG-enhanced commands for agent operations.
"""

import os
import json
import time
import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple, Union
from pathlib import Path
from datetime import datetime

# Local imports
from ..core.enhanced_rag import EnhancedRAG, DocumentType, RAGConfig
from ..core.rag_memory_integration import RAGMemoryIntegration, MemoryType
from ..core.rag_agent_integration import RAGAgentIntegration, AgentTaskType
from ..core.logging_setup import get_logger

logger = get_logger(__name__)


class RAGCommands:
    """
    RAG-enhanced commands for agents.
    """

    def __init__(self, rag_system: EnhancedRAG, memory_integration: Optional[RAGMemoryIntegration] = None,
                 agent_integration: Optional[RAGAgentIntegration] = None):
        self.rag_system = rag_system
        self.memory_integration = memory_integration
        self.agent_integration = agent_integration
        self.logger = get_logger(__name__)

        # Command history
        self.command_history: List[Dict[str, Any]] = []

        self.logger.info("RAG Commands initialized")

    async def search_knowledge(self, query: str, filters: Optional[Dict[str, Any]] = None,
                             limit: int = 5, include_sources: bool = True) -> Dict[str, Any]:
        """
        Search for knowledge using RAG system.

        Args:
            query: Search query
            filters: Search filters
            limit: Maximum number of results
            include_sources: Whether to include source information

        Returns:
            Search results
        """
        try:
            start_time = time.time()

            # Perform search
            search_results = await self.rag_system.search(query, top_k=limit, filters=filters)

            # Format results
            formatted_results = []
            for result in search_results:
                result_data = {
                    "content": result.chunk.content,
                    "score": result.score,
                    "chunk_id": result.chunk.id,
                    "document_id": result.document.id,
                    "metadata": result.metadata
                }

                if include_sources:
                    result_data["source"] = result.document.source_path
                    result_data["document_type"] = result.document.doc_type.value

                formatted_results.append(result_data)

            # Log command
            self._log_command("search_knowledge", {
                "query": query,
                "filters": filters,
                "limit": limit,
                "results_count": len(formatted_results),
                "processing_time": time.time() - start_time
            })

            return {
                "success": True,
                "results": formatted_results,
                "query": query,
                "total_results": len(formatted_results),
                "processing_time": time.time() - start_time
            }

        except Exception as e:
            self.logger.error(f"Error searching knowledge: {e}")
            return {
                "success": False,
                "error": str(e),
                "query": query
            }

    async def add_knowledge(self, content: str, source: str = "manual",
                         knowledge_type: str = "general", metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Add knowledge to the RAG system.

        Args:
            content: Knowledge content
            source: Source of the knowledge
            knowledge_type: Type of knowledge
            metadata: Additional metadata

        Returns:
            Operation result
        """
        try:
            start_time = time.time()

            # Add to RAG system
            doc_id = await self.rag_system.add_text(
                content,
                doc_type=DocumentType.TEXT,
                metadata={
                    "source": source,
                    "knowledge_type": knowledge_type,
                    **(metadata or {})
                }
            )

            # Add to memory system if available
            if self.memory_integration:
                memory_id = await self.memory_integration.store_memory(
                    content,
                    MemoryType.SEMANTIC,
                    source,
                    importance=0.8,
                    metadata={"knowledge_type": knowledge_type, **(metadata or {})}
                )

            # Log command
            self._log_command("add_knowledge", {
                "content_length": len(content),
                "source": source,
                "knowledge_type": knowledge_type,
                "doc_id": doc_id,
                "memory_id": memory_id if self.memory_integration else None,
                "processing_time": time.time() - start_time
            })

            return {
                "success": True,
                "doc_id": doc_id,
                "memory_id": memory_id if self.memory_integration else None,
                "content_length": len(content),
                "processing_time": time.time() - start_time
            }

        except Exception as e:
            self.logger.error(f"Error adding knowledge: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def learn_from_interaction(self, query: str, response: str, feedback: Optional[str] = None,
                                  context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Learn from an interaction.

        Args:
            query: User query
            response: System response
            feedback: User feedback (optional)
            context: Interaction context (optional)

        Returns:
            Learning result
        """
        try:
            start_time = time.time()

            # Create learning content
            learning_content = f"Query: {query}\nResponse: {response}"
            if feedback:
                learning_content += f"\nFeedback: {feedback}"

            # Store as memory if available
            memory_id = None
            if self.memory_integration:
                memory_id = await self.memory_integration.store_memory(
                    learning_content,
                    MemoryType.EPISODIC,
                    "interaction_learning",
                    importance=0.9 if feedback and "helpful" in feedback.lower() else 0.7,
                    metadata={
                        "query": query,
                        "response": response,
                        "feedback": feedback,
                        "context": context or {},
                        "timestamp": datetime.now().isoformat()
                    }
                )

            # Submit learning task to agents if available
            task_id = None
            if self.agent_integration and feedback:
                task_id = await self.agent_integration.submit_task(
                    AgentTaskType.FEEDBACK_GENERATION,
                    {
                        "query": query,
                        "response": response,
                        "feedback": feedback,
                        "context": context or {}
                    },
                    priority=1
                )

            # Log command
            self._log_command("learn_from_interaction", {
                "query_length": len(query),
                "response_length": len(response),
                "has_feedback": feedback is not None,
                "memory_id": memory_id,
                "task_id": task_id,
                "processing_time": time.time() - start_time
            })

            return {
                "success": True,
                "memory_id": memory_id,
                "task_id": task_id,
                "learned_from": "interaction",
                "processing_time": time.time() - start_time
            }

        except Exception as e:
            self.logger.error(f"Error learning from interaction: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def retrieve_memories(self, query: str, memory_types: Optional[List[str]] = None,
                              limit: int = 10, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Retrieve memories related to a query.

        Args:
            query: Search query
            memory_types: Types of memories to retrieve
            limit: Maximum number of memories
            context: Search context

        Returns:
            Retrieved memories
        """
        try:
            start_time = time.time()

            if not self.memory_integration:
                return {
                    "success": False,
                    "error": "Memory integration not available"
                }

            # Convert memory types
            mem_types = None
            if memory_types:
                mem_types = [MemoryType(t) for t in memory_types if t in [mt.value for mt in MemoryType]]

            # Retrieve memories
            memories = await self.memory_integration.retrieve_memories(
                query,
                memory_types=mem_types,
                limit=limit,
                context=context
            )

            # Format memories
            formatted_memories = []
            for memory in memories:
                formatted_memories.append({
                    "id": memory.id,
                    "content": memory.content,
                    "type": memory.memory_type.value,
                    "source": memory.source,
                    "importance": memory.importance,
                    "access_count": memory.access_count,
                    "created_at": memory.timestamp.isoformat(),
                    "last_accessed": memory.last_accessed.isoformat()
                })

            # Log command
            self._log_command("retrieve_memories", {
                "query": query,
                "memory_types": memory_types,
                "limit": limit,
                "retrieved_count": len(formatted_memories),
                "processing_time": time.time() - start_time
            })

            return {
                "success": True,
                "memories": formatted_memories,
                "total_retrieved": len(formatted_memories),
                "processing_time": time.time() - start_time
            }

        except Exception as e:
            self.logger.error(f"Error retrieving memories: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def build_context(self, query: str, max_length: int = 2000,
                          include_memories: bool = True, include_sources: bool = True) -> Dict[str, Any]:
        """
        Build context for AI responses.

        Args:
            query: Query to build context for
            max_length: Maximum context length
            include_memories: Whether to include memories
            include_sources: Whether to include sources

        Returns:
            Built context
        """
        try:
            start_time = time.time()

            context_parts = []
            current_length = 0

            # Add RAG search results
            rag_context, rag_metadata = await self.rag_system.build_context(query, max_length=max_length)

            if rag_context:
                context_parts.append(("rag_context", rag_context))
                current_length += len(rag_context)

            # Add memories if requested and available
            if include_memories and self.memory_integration:
                memories = await self.memory_integration.retrieve_memories(query, limit=3)
                if memories:
                    memory_content = "\n\n".join([f"Memory: {m.content}" for m in memories])
                    if current_length + len(memory_content) <= max_length:
                        context_parts.append(("memories", memory_content))
                        current_length += len(memory_content)

            # Combine all context parts
            final_context = "\n\n".join([part[1] for part in context_parts])

            # Build metadata
            metadata = {
                "query": query,
                "max_length": max_length,
                "actual_length": len(final_context),
                "rag_metadata": rag_metadata,
                "context_parts": [part[0] for part in context_parts],
                "include_memories": include_memories,
                "include_sources": include_sources
            }

            # Log command
            self._log_command("build_context", {
                "query": query,
                "max_length": max_length,
                "include_memories": include_memories,
                "actual_length": len(final_context),
                "parts_count": len(context_parts),
                "processing_time": time.time() - start_time
            })

            return {
                "success": True,
                "context": final_context,
                "metadata": metadata,
                "processing_time": time.time() - start_time
            }

        except Exception as e:
            self.logger.error(f"Error building context: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def analyze_knowledge_gaps(self, domain: str, query: str) -> Dict[str, Any]:
        """
        Analyze knowledge gaps in a specific domain.

        Args:
            domain: Domain to analyze
            query: Query representing the knowledge need

        Returns:
            Knowledge gap analysis
        """
        try:
            start_time = time.time()

            # Search for existing knowledge
            search_results = await self.rag_system.search(query, top_k=5)

            # Analyze results
            if search_results:
                # Have some knowledge
                coverage_score = len(search_results) / 5.0  # Normalize to 0-1
                confidence_score = sum(r.score for r in search_results) / len(search_results)

                knowledge_status = "partial" if coverage_score < 0.7 else "adequate"
            else:
                coverage_score = 0.0
                confidence_score = 0.0
                knowledge_status = "missing"

            # Generate recommendations
            recommendations = []
            if knowledge_status == "missing":
                recommendations.append(f"No knowledge found for {domain}. Consider adding relevant documentation.")
            elif knowledge_status == "partial":
                recommendations.append(f"Limited knowledge for {domain}. Consider expanding coverage.")
                recommendations.append("Current sources may need updating or supplementation.")

            # Log command
            self._log_command("analyze_knowledge_gaps", {
                "domain": domain,
                "query": query,
                "coverage_score": coverage_score,
                "confidence_score": confidence_score,
                "knowledge_status": knowledge_status,
                "processing_time": time.time() - start_time
            })

            return {
                "success": True,
                "domain": domain,
                "knowledge_status": knowledge_status,
                "coverage_score": coverage_score,
                "confidence_score": confidence_score,
                "recommendations": recommendations,
                "processing_time": time.time() - start_time
            }

        except Exception as e:
            self.logger.error(f"Error analyzing knowledge gaps: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def optimize_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Optimize a query for better search results.

        Args:
            query: Original query
            context: Query context

        Returns:
            Optimized query
        """
        try:
            start_time = time.time()

            # Basic query optimization
            optimized_query = query.strip()

            # Add context terms if available
            if context:
                domain = context.get("domain", "")
                if domain and domain.lower() not in optimized_query.lower():
                    optimized_query = f"{optimized_query} {domain}"

            # Expand with related terms
            expansions = []
            if "code" in optimized_query.lower():
                expansions.extend(["programming", "development", "implementation"])
            if "error" in optimized_query.lower():
                expansions.extend(["issue", "problem", "bug", "debugging"])
            if "how to" in optimized_query.lower():
                expansions.extend(["guide", "tutorial", "steps", "process"])

            # Add expansions
            for expansion in expansions[:2]:  # Limit to 2 expansions
                if expansion.lower() not in optimized_query.lower():
                    optimized_query = f"{optimized_query} {expansion}"

            # Test optimization
            original_results = await self.rag_system.search(query, top_k=3)
            optimized_results = await self.rag_system.search(optimized_query, top_k=3)

            # Compare results
            original_avg_score = sum(r.score for r in original_results) / len(original_results) if original_results else 0
            optimized_avg_score = sum(r.score for r in optimized_results) / len(optimized_results) if optimized_results else 0

            improvement = optimized_avg_score - original_avg_score

            # Log command
            self._log_command("optimize_query", {
                "original_query": query,
                "optimized_query": optimized_query,
                "original_score": original_avg_score,
                "optimized_score": optimized_avg_score,
                "improvement": improvement,
                "processing_time": time.time() - start_time
            })

            return {
                "success": True,
                "original_query": query,
                "optimized_query": optimized_query,
                "original_score": original_avg_score,
                "optimized_score": optimized_avg_score,
                "improvement": improvement,
                "processing_time": time.time() - start_time
            }

        except Exception as e:
            self.logger.error(f"Error optimizing query: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def cross_reference_knowledge(self, query: str, limit: int = 5) -> Dict[str, Any]:
        """
        Cross-reference knowledge across different sources.

        Args:
            query: Query to cross-reference
            limit: Maximum results per source type

        Returns:
            Cross-reference results
        """
        try:
            start_time = time.time()

            # Search with different filters
            filters_list = [
                {},  # No filter
                {"doc_type": "code"},  # Code only
                {"doc_type": "markdown"},  # Documentation only
                {"doc_type": "text"}  # General text only
            ]

            cross_reference_results = {}

            for filter_config in filters_list:
                filter_name = "all" if not filter_config else filter_config["doc_type"]
                results = await self.rag_system.search(query, top_k=limit, filters=filter_config)

                cross_reference_results[filter_name] = [
                    {
                        "content": result.chunk.content,
                        "score": result.score,
                        "source": result.document.source_path
                    }
                    for result in results
                ]

            # Find common themes
            all_contents = []
            for results in cross_reference_results.values():
                all_contents.extend([r["content"] for r in results])

            common_themes = self._extract_common_themes(all_contents)

            # Log command
            self._log_command("cross_reference_knowledge", {
                "query": query,
                "limit": limit,
                "source_types": list(cross_reference_results.keys()),
                "total_results": sum(len(results) for results in cross_reference_results.values()),
                "common_themes_count": len(common_themes),
                "processing_time": time.time() - start_time
            })

            return {
                "success": True,
                "query": query,
                "cross_references": cross_reference_results,
                "common_themes": common_themes,
                "processing_time": time.time() - start_time
            }

        except Exception as e:
            self.logger.error(f"Error cross-referencing knowledge: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _extract_common_themes(self, contents: List[str]) -> List[str]:
        """Extract common themes from content."""
        try:
            # Simple theme extraction
            all_words = []
            for content in contents:
                words = content.lower().split()
                all_words.extend(words)

            # Count word frequencies
            word_counts = {}
            for word in all_words:
                if len(word) > 4:  # Ignore short words
                    word_counts[word] = word_counts.get(word, 0) + 1

            # Get most common words
            common_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)[:10]

            return [word for word, count in common_words]

        except Exception as e:
            self.logger.error(f"Error extracting common themes: {e}")
            return []

    async def get_rag_stats(self) -> Dict[str, Any]:
        """
        Get RAG system statistics.

        Returns:
            RAG statistics
        """
        try:
            # Get basic RAG stats
            rag_stats = self.rag_system.get_stats()

            # Get memory stats if available
            memory_stats = {}
            if self.memory_integration:
                memory_stats = self.memory_integration.get_stats()

            # Get agent stats if available
            agent_stats = {}
            if self.agent_integration:
                agent_stats = self.agent_integration.get_agent_stats()

            # Get command stats
            command_stats = {
                "total_commands": len(self.command_history),
                "command_types": {},
                "avg_processing_time": 0.0
            }

            if self.command_history:
                # Count command types
                for cmd in self.command_history:
                    cmd_type = cmd.get("command", "unknown")
                    command_stats["command_types"][cmd_type] = command_stats["command_types"].get(cmd_type, 0) + 1

                # Calculate average processing time
                total_time = sum(cmd.get("processing_time", 0) for cmd in self.command_history)
                command_stats["avg_processing_time"] = total_time / len(self.command_history)

            return {
                "success": True,
                "rag_stats": rag_stats,
                "memory_stats": memory_stats,
                "agent_stats": agent_stats,
                "command_stats": command_stats,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error getting RAG stats: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _log_command(self, command: str, details: Dict[str, Any]):
        """Log command execution."""
        try:
            log_entry = {
                "command": command,
                "timestamp": datetime.now().isoformat(),
                **details
            }

            self.command_history.append(log_entry)

            # Keep only recent commands (last 1000)
            if len(self.command_history) > 1000:
                self.command_history = self.command_history[-1000:]

        except Exception as e:
            self.logger.error(f"Error logging command: {e}")

    def get_command_history(self, limit: int = 50, command_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get command history."""
        try:
            history = self.command_history

            # Filter by command type if specified
            if command_type:
                history = [cmd for cmd in history if cmd.get("command") == command_type]

            # Limit results
            return history[-limit:]

        except Exception as e:
            self.logger.error(f"Error getting command history: {e}")
            return []

    async def export_knowledge(self, file_path: str, include_memories: bool = True) -> Dict[str, Any]:
        """Export knowledge to file."""
        try:
            start_time = time.time()

            export_data = {
                "export_timestamp": datetime.now().isoformat(),
                "rag_stats": self.rag_system.get_stats()
            }

            # Export memories if available
            if include_memories and self.memory_integration:
                memory_file = file_path.replace(".json", "_memories.json")
                await self.memory_integration.export_memories(memory_file)
                export_data["memories_exported"] = True
                export_data["memories_file"] = memory_file

            # Save export data
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

            # Log command
            self._log_command("export_knowledge", {
                "file_path": file_path,
                "include_memories": include_memories,
                "processing_time": time.time() - start_time
            })

            return {
                "success": True,
                "file_path": file_path,
                "include_memories": include_memories,
                "processing_time": time.time() - start_time
            }

        except Exception as e:
            self.logger.error(f"Error exporting knowledge: {e}")
            return {
                "success": False,
                "error": str(e)
            }


# Global instance
_rag_commands: Optional[RAGCommands] = None


def get_rag_commands(rag_system: EnhancedRAG, memory_integration: Optional[RAGMemoryIntegration] = None,
                    agent_integration: Optional[RAGAgentIntegration] = None) -> RAGCommands:
    """Get or create the global RAG commands instance."""
    global _rag_commands

    if _rag_commands is None:
        _rag_commands = RAGCommands(rag_system, memory_integration, agent_integration)

    return _rag_commands