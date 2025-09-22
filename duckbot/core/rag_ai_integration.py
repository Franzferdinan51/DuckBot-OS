#!/usr/bin/env python3
"""
RAG AI Integration Module for DuckBot
Integrates RAG system with AI providers for enhanced response generation.
"""

import os
import json
import time
import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

# Local imports
from .enhanced_rag import EnhancedRAG, RAGConfig, SearchResult, DocumentType
from .ai_provider_manager import AIProviderManager
from .logging_setup import get_logger
from .utilities import safe_read_file

logger = get_logger(__name__)


class RAGStrategy(Enum):
    """RAG integration strategies."""
    PRE_SEARCH = "pre_search"           # Search before AI generation
    POST_SEARCH = "post_search"         # Search after AI generation
    HYBRID = "hybrid"                   # Combined approach
    QUERY_REWRITE = "query_rewrite"     # Rewrite queries for better search
    MULTI_TURN = "multi_turn"           # Multi-turn conversation context
    CONTEXT_AWARE = "context_aware"     # Context-aware retrieval


class RAGTrigger(Enum):
    """When to trigger RAG search."""
    ALWAYS = "always"                   # Always use RAG
    CONFIDENCE_BASED = "confidence_based"  # Use when AI confidence is low
    KEYWORD_BASED = "keyword_based"      # Use based on keywords
    LENGTH_BASED = "length_based"        # Use for complex/long queries
    USER_REQUESTED = "user_requested"    # Use when user explicitly requests


@dataclass
class RAGAIConfig:
    """Configuration for RAG-AI integration."""
    # General settings
    enabled: bool = True
    strategy: RAGStrategy = RAGStrategy.HYBRID
    trigger: RAGTrigger = RAGTrigger.CONFIDENCE_BASED

    # Confidence thresholds
    min_confidence_threshold: float = 0.7
    max_confidence_threshold: float = 0.9

    # Query processing
    max_context_length: int = 4000
    max_search_results: int = 5
    include_metadata: bool = True
    include_sources: bool = True

    # Context construction
    context_template: str = """
[RETRIEVED CONTEXT]
{context}

[END RETRIEVED CONTEXT]

Original Query: {query}

Please use the retrieved context to provide a comprehensive and accurate response.
If the context is not relevant to the query, you may disregard it.
"""

    # Advanced features
    enable_query_rewrite: bool = True
    enable_multi_turn: bool = True
    enable_context_aware: bool = True
    enable_cross_reference: bool = True

    # Performance settings
    cache_rag_results: bool = True
    cache_ttl: int = 300  # 5 minutes
    max_concurrent_searches: int = 3

    # Debug settings
    debug_mode: bool = False
    log_search_results: bool = True


@dataclass
class RAGRequest:
    """RAG request structure."""
    query: str
    conversation_history: List[Dict[str, str]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    timestamp: float = field(default_factory=time.time)


@dataclass
class RAGResponse:
    """RAG response structure."""
    query: str
    context: str
    search_results: List[SearchResult]
    metadata: Dict[str, Any] = field(default_factory=dict)
    processing_time: float = 0.0
    success: bool = True
    error: Optional[str] = None


class RAGAIIntegration:
    """
    Integration between RAG system and AI providers.
    """

    def __init__(self, rag_system: EnhancedRAG, ai_manager: AIProviderManager,
                 config: Optional[RAGAIConfig] = None):
        self.rag_system = rag_system
        self.ai_manager = ai_manager
        self.config = config or RAGAIConfig()
        self.logger = get_logger(__name__)

        # Initialize caches
        self._rag_cache: Dict[str, RAGResponse] = {}
        self._query_history: List[Dict[str, Any]] = []

        # Performance tracking
        self._stats = {
            "total_requests": 0,
            "rag_triggered": 0,
            "cache_hits": 0,
            "avg_processing_time": 0.0,
            "success_rate": 0.0
        }

        self.logger.info("RAG-AI Integration initialized")

    async def process_request(self, request: RAGRequest) -> RAGResponse:
        """
        Process a RAG request.

        Args:
            request: RAG request object

        Returns:
            RAG response object
        """
        try:
            start_time = time.time()
            self._stats["total_requests"] += 1

            # Check if RAG should be triggered
            should_trigger = await self._should_trigger_rag(request)
            if not should_trigger:
                return RAGResponse(
                    query=request.query,
                    context="",
                    search_results=[],
                    metadata={"triggered": False, "reason": "trigger_condition_not_met"},
                    processing_time=time.time() - start_time
                )

            # Check cache
            cache_key = self._get_cache_key(request)
            if self.config.cache_rag_results and cache_key in self._rag_cache:
                cached_response = self._rag_cache[cache_key]
                if time.time() - cached_response.timestamp < self.config.cache_ttl:
                    self._stats["cache_hits"] += 1
                    cached_response.metadata["from_cache"] = True
                    return cached_response

            # Process based on strategy
            if self.config.strategy == RAGStrategy.PRE_SEARCH:
                response = await self._pre_search_strategy(request)
            elif self.config.strategy == RAGStrategy.POST_SEARCH:
                response = await self._post_search_strategy(request)
            elif self.config.strategy == RAGStrategy.HYBRID:
                response = await self._hybrid_strategy(request)
            elif self.config.strategy == RAGStrategy.QUERY_REWRITE:
                response = await self._query_rewrite_strategy(request)
            elif self.config.strategy == RAGStrategy.MULTI_TURN:
                response = await self._multi_turn_strategy(request)
            elif self.config.strategy == RAGStrategy.CONTEXT_AWARE:
                response = await self._context_aware_strategy(request)
            else:
                response = await self._pre_search_strategy(request)

            # Update processing time
            response.processing_time = time.time() - start_time

            # Cache response
            if self.config.cache_rag_results and response.success:
                self._rag_cache[cache_key] = response

            # Update statistics
            self._stats["rag_triggered"] += 1
            if response.success:
                self._stats["success_rate"] = (
                    (self._stats["success_rate"] * (self._stats["rag_triggered"] - 1) + 1.0) /
                    self._stats["rag_triggered"]
                )
            else:
                self._stats["success_rate"] = (
                    (self._stats["success_rate"] * (self._stats["rag_triggered"] - 1) + 0.0) /
                    self._stats["rag_triggered"]
                )

            self._stats["avg_processing_time"] = (
                (self._stats["avg_processing_time"] * (self._stats["rag_triggered"] - 1) + response.processing_time) /
                self._stats["rag_triggered"]
            )

            # Log query history
            self._log_query_history(request, response)

            if self.config.debug_mode:
                self.logger.debug(f"RAG processing completed in {response.processing_time:.3f}s")

            return response

        except Exception as e:
            self.logger.error(f"Error processing RAG request: {e}")
            return RAGResponse(
                query=request.query,
                context="",
                search_results=[],
                processing_time=time.time() - start_time,
                success=False,
                error=str(e)
            )

    async def _should_trigger_rag(self, request: RAGRequest) -> bool:
        """Determine if RAG should be triggered for this request."""
        if not self.config.enabled:
            return False

        trigger_type = self.config.trigger

        if trigger_type == RAGTrigger.ALWAYS:
            return True

        elif trigger_type == RAGTrigger.CONFIDENCE_BASED:
            # Check if query complexity suggests RAG is needed
            complexity_score = await self._calculate_query_complexity(request.query)
            return complexity_score < self.config.min_confidence_threshold

        elif trigger_type == RAGTrigger.KEYWORD_BASED:
            # Check for RAG-triggering keywords
            rag_keywords = ["search", "find", "look up", "retrieve", "information", "data", "document", "file"]
            query_lower = request.query.lower()
            return any(keyword in query_lower for keyword in rag_keywords)

        elif trigger_type == RAGTrigger.LENGTH_BASED:
            # Use RAG for longer queries
            return len(request.query.split()) > 10

        elif trigger_type == RAGTrigger.USER_REQUESTED:
            # Check if user explicitly requested RAG
            explicit_keywords = ["use rag", "search documents", "look in files", "check knowledge"]
            query_lower = request.query.lower()
            return any(keyword in query_lower for keyword in explicit_keywords)

        return False

    async def _pre_search_strategy(self, request: RAGRequest) -> RAGResponse:
        """Pre-search strategy: search before AI generation."""
        try:
            # Perform search
            search_results = await self.rag_system.search(
                request.query,
                top_k=self.config.max_search_results
            )

            # Build context
            context = await self._build_context(search_results, request.query)

            return RAGResponse(
                query=request.query,
                context=context,
                search_results=search_results,
                metadata={
                    "strategy": "pre_search",
                    "search_results_count": len(search_results),
                    "context_length": len(context)
                }
            )

        except Exception as e:
            self.logger.error(f"Error in pre-search strategy: {e}")
            return RAGResponse(
                query=request.query,
                context="",
                search_results=[],
                success=False,
                error=str(e)
            )

    async def _post_search_strategy(self, request: RAGRequest) -> RAGResponse:
        """Post-search strategy: search after AI generation."""
        try:
            # First, get AI response without RAG
            ai_response = await self.ai_manager.generate_response(
                request.query,
                conversation_history=request.conversation_history
            )

            # Analyze AI response to determine if search is needed
            if await self._needs_search(ai_response):
                # Perform search
                search_results = await self.rag_system.search(
                    request.query,
                    top_k=self.config.max_search_results
                )

                # Build context
                context = await self._build_context(search_results, request.query)

                # Regenerate response with context
                final_response = await self.ai_manager.generate_response(
                    self.config.context_template.format(
                        context=context,
                        query=request.query
                    ),
                    conversation_history=request.conversation_history
                )

                return RAGResponse(
                    query=request.query,
                    context=context,
                    search_results=search_results,
                    metadata={
                        "strategy": "post_search",
                        "initial_response": ai_response,
                        "final_response": final_response,
                        "search_results_count": len(search_results)
                    }
                )
            else:
                return RAGResponse(
                    query=request.query,
                    context="",
                    search_results=[],
                    metadata={
                        "strategy": "post_search",
                        "search_triggered": False,
                        "initial_response": ai_response
                    }
                )

        except Exception as e:
            self.logger.error(f"Error in post-search strategy: {e}")
            return RAGResponse(
                query=request.query,
                context="",
                search_results=[],
                success=False,
                error=str(e)
            )

    async def _hybrid_strategy(self, request: RAGRequest) -> RAGResponse:
        """Hybrid strategy: combine pre and post search."""
        try:
            # Pre-search
            search_results = await self.rag_system.search(
                request.query,
                top_k=self.config.max_search_results
            )

            context = await self._build_context(search_results, request.query)

            # Generate response with context
            response = await self.ai_manager.generate_response(
                self.config.context_template.format(
                    context=context,
                    query=request.query
                ),
                conversation_history=request.conversation_history
            )

            # Post-search verification
            if await self._needs_verification(response):
                # Additional search for verification
                verification_results = await self.rag_system.search(
                    f"verify: {request.query}",
                    top_k=3
                )

                if verification_results:
                    verification_context = await self._build_context(verification_results, request.query)

                    # Generate final response with verification
                    final_response = await self.ai_manager.generate_response(
                        f"Original response: {response}\n\nVerification context: {verification_context}\n\nPlease verify and improve your response based on the verification context.",
                        conversation_history=request.conversation_history
                    )

                    return RAGResponse(
                        query=request.query,
                        context=context + "\n\n[VERIFICATION CONTEXT]\n" + verification_context,
                        search_results=search_results + verification_results,
                        metadata={
                            "strategy": "hybrid",
                            "initial_response": response,
                            "final_response": final_response,
                            "search_results_count": len(search_results + verification_results)
                        }
                    )

            return RAGResponse(
                query=request.query,
                context=context,
                search_results=search_results,
                metadata={
                    "strategy": "hybrid",
                    "response": response,
                    "search_results_count": len(search_results)
                }
            )

        except Exception as e:
            self.logger.error(f"Error in hybrid strategy: {e}")
            return RAGResponse(
                query=request.query,
                context="",
                search_results=[],
                success=False,
                error=str(e)
            )

    async def _query_rewrite_strategy(self, request: RAGRequest) -> RAGResponse:
        """Query rewrite strategy: rewrite queries for better search."""
        try:
            if not self.config.enable_query_rewrite:
                return await self._pre_search_strategy(request)

            # Rewrite query for better search
            rewritten_query = await self._rewrite_query(request.query)

            # Search with original and rewritten queries
            original_results = await self.rag_system.search(
                request.query,
                top_k=self.config.max_search_results // 2
            )

            rewritten_results = await self.rag_system.search(
                rewritten_query,
                top_k=self.config.max_search_results // 2
            )

            # Combine results
            all_results = original_results + rewritten_results
            all_results = self._deduplicate_results(all_results)

            # Build context
            context = await self._build_context(all_results, request.query)

            return RAGResponse(
                query=request.query,
                context=context,
                search_results=all_results,
                metadata={
                    "strategy": "query_rewrite",
                    "rewritten_query": rewritten_query,
                    "search_results_count": len(all_results)
                }
            )

        except Exception as e:
            self.logger.error(f"Error in query rewrite strategy: {e}")
            return RAGResponse(
                query=request.query,
                context="",
                search_results=[],
                success=False,
                error=str(e)
            )

    async def _multi_turn_strategy(self, request: RAGRequest) -> RAGResponse:
        """Multi-turn strategy: consider conversation history."""
        try:
            if not self.config.enable_multi_turn or not request.conversation_history:
                return await self._pre_search_strategy(request)

            # Extract key entities from conversation history
            context_entities = await self._extract_context_entities(request.conversation_history)

            # Expand query with context
            expanded_query = await self._expand_query_with_context(request.query, context_entities)

            # Search with expanded query
            search_results = await self.rag_system.search(
                expanded_query,
                top_k=self.config.max_search_results
            )

            # Build context
            context = await self._build_context(search_results, request.query)

            return RAGResponse(
                query=request.query,
                context=context,
                search_results=search_results,
                metadata={
                    "strategy": "multi_turn",
                    "expanded_query": expanded_query,
                    "context_entities": context_entities,
                    "search_results_count": len(search_results)
                }
            )

        except Exception as e:
            self.logger.error(f"Error in multi-turn strategy: {e}")
            return RAGResponse(
                query=request.query,
                context="",
                search_results=[],
                success=False,
                error=str(e)
            )

    async def _context_aware_strategy(self, request: RAGRequest) -> RAGResponse:
        """Context-aware strategy: use context to improve retrieval."""
        try:
            if not self.config.enable_context_aware:
                return await self._pre_search_strategy(request)

            # Analyze query to understand context
            query_context = await self._analyze_query_context(request.query, request.conversation_history)

            # Perform context-aware search
            search_results = await self.rag_system.search(
                request.query,
                top_k=self.config.max_search_results,
                filters=query_context.get("filters", {})
            )

            # Build context
            context = await self._build_context(search_results, request.query)

            return RAGResponse(
                query=request.query,
                context=context,
                search_results=search_results,
                metadata={
                    "strategy": "context_aware",
                    "query_context": query_context,
                    "search_results_count": len(search_results)
                }
            )

        except Exception as e:
            self.logger.error(f"Error in context-aware strategy: {e}")
            return RAGResponse(
                query=request.query,
                context="",
                search_results=[],
                success=False,
                error=str(e)
            )

    async def _build_context(self, search_results: List[SearchResult], query: str) -> str:
        """Build context string from search results."""
        if not search_results:
            return ""

        context_parts = []
        total_length = 0

        for result in search_results:
            # Format result
            source_name = Path(result.document.source_path).name
            result_text = f"[Source: {source_name} | Score: {result.score:.3f}]\n{result.chunk.content.strip()}"

            if total_length + len(result_text) > self.config.max_context_length:
                break

            context_parts.append(result_text)
            total_length += len(result_text)

        return "\n\n".join(context_parts)

    async def _calculate_query_complexity(self, query: str) -> float:
        """Calculate query complexity score."""
        try:
            # Simple complexity calculation based on:
            # - Query length
            # - Number of questions
            # - Technical terms
            # - Ambiguity

            complexity_factors = []

            # Length factor (longer queries are more complex)
            length_score = min(len(query.split()) / 20, 1.0)
            complexity_factors.append(length_score)

            # Question factor
            question_count = query.count('?')
            question_score = min(question_count / 3, 1.0)
            complexity_factors.append(question_score)

            # Technical terms factor
            technical_terms = ["function", "method", "class", "algorithm", "data", "code", "api", "database"]
            technical_count = sum(1 for term in technical_terms if term.lower() in query.lower())
            technical_score = min(technical_count / 3, 1.0)
            complexity_factors.append(technical_score)

            # Ambiguity factor
            ambiguous_words = ["maybe", "perhaps", "could", "might", "possibly", "something"]
            ambiguous_count = sum(1 for word in ambiguous_words if word.lower() in query.lower())
            ambiguity_score = min(ambiguous_count / 2, 1.0)
            complexity_factors.append(ambiguity_score)

            # Calculate overall complexity (inverse of confidence)
            overall_complexity = sum(complexity_factors) / len(complexity_factors)
            return 1.0 - overall_complexity

        except Exception as e:
            self.logger.error(f"Error calculating query complexity: {e}")
            return 0.5

    async def _needs_search(self, response: str) -> bool:
        """Determine if search is needed based on AI response."""
        try:
            # Check response for uncertainty indicators
            uncertainty_indicators = [
                "i don't know", "not sure", "unclear", "i'm not certain",
                "cannot provide", "unable to answer", "i don't have information"
            ]

            response_lower = response.lower()
            return any(indicator in response_lower for indicator in uncertainty_indicators)

        except Exception as e:
            self.logger.error(f"Error checking if search is needed: {e}")
            return False

    async def _needs_verification(self, response: str) -> bool:
        """Determine if response needs verification."""
        try:
            # Check response for statements that need verification
            verification_triggers = [
                "according to", "it is said that", "studies show", "research indicates",
                "it is believed", "some people say", "it has been reported"
            ]

            response_lower = response.lower()
            return any(trigger in response_lower for trigger in verification_triggers)

        except Exception as e:
            self.logger.error(f"Error checking if verification is needed: {e}")
            return False

    async def _rewrite_query(self, query: str) -> str:
        """Rewrite query for better search results."""
        try:
            # Simple query rewriting strategies
            rewritten = query

            # Add context terms
            context_terms = ["explain", "describe", "how to", "what is", "guide", "tutorial"]
            for term in context_terms:
                if term not in query.lower():
                    rewritten = f"{term} {rewritten}"
                    break

            return rewritten

        except Exception as e:
            self.logger.error(f"Error rewriting query: {e}")
            return query

    async def _extract_context_entities(self, conversation_history: List[Dict[str, str]]) -> List[str]:
        """Extract entities from conversation history."""
        try:
            entities = []

            for message in conversation_history:
                content = message.get("content", "")
                # Simple entity extraction (could be enhanced with NLP)
                words = content.split()
                # Filter for potential entities (nouns, proper nouns)
                for word in words:
                    if len(word) > 3 and word.isalpha() and word[0].isupper():
                        entities.append(word)

            return list(set(entities))  # Remove duplicates

        except Exception as e:
            self.logger.error(f"Error extracting context entities: {e}")
            return []

    async def _expand_query_with_context(self, query: str, entities: List[str]) -> str:
        """Expand query with context entities."""
        try:
            if not entities:
                return query

            # Add relevant entities to query
            expanded_query = query
            for entity in entities[:3]:  # Limit to top 3 entities
                if entity.lower() not in query.lower():
                    expanded_query = f"{expanded_query} {entity}"

            return expanded_query

        except Exception as e:
            self.logger.error(f"Error expanding query with context: {e}")
            return query

    async def _analyze_query_context(self, query: str, conversation_history: List[Dict[str, str]]) -> Dict[str, Any]:
        """Analyze query to understand context."""
        try:
            context = {}

            # Determine query type
            if any(word in query.lower() for word in ["how", "what", "why", "when", "where"]):
                context["query_type"] = "question"
            elif any(word in query.lower() for word in ["code", "function", "method", "class"]):
                context["query_type"] = "technical"
            elif any(word in query.lower() for word in ["help", "assist", "support"]):
                context["query_type"] = "help"
            else:
                context["query_type"] = "general"

            # Extract potential filters
            if "python" in query.lower():
                context["filters"] = {"doc_type": "code"}
            elif "documentation" in query.lower():
                context["filters"] = {"doc_type": "markdown"}

            return context

        except Exception as e:
            self.logger.error(f"Error analyzing query context: {e}")
            return {}

    def _deduplicate_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """Remove duplicate search results."""
        seen_ids = set()
        unique_results = []

        for result in results:
            if result.chunk.id not in seen_ids:
                seen_ids.add(result.chunk.id)
                unique_results.append(result)

        return unique_results

    def _get_cache_key(self, request: RAGRequest) -> str:
        """Generate cache key for request."""
        import hashlib
        cache_data = {
            "query": request.query,
            "strategy": self.config.strategy.value,
            "timestamp": request.timestamp
        }
        return hashlib.md5(json.dumps(cache_data, sort_keys=True).encode()).hexdigest()

    def _log_query_history(self, request: RAGRequest, response: RAGResponse):
        """Log query history for analytics."""
        try:
            history_entry = {
                "timestamp": time.time(),
                "query": request.query,
                "strategy": self.config.strategy.value,
                "success": response.success,
                "processing_time": response.processing_time,
                "search_results_count": len(response.search_results),
                "context_length": len(response.context)
            }

            self._query_history.append(history_entry)

            # Keep only recent history (last 1000 entries)
            if len(self._query_history) > 1000:
                self._query_history = self._query_history[-1000:]

        except Exception as e:
            self.logger.error(f"Error logging query history: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get RAG-AI integration statistics."""
        return {
            **self._stats,
            "config": {
                "enabled": self.config.enabled,
                "strategy": self.config.strategy.value,
                "trigger": self.config.trigger.value,
                "max_context_length": self.config.max_context_length,
                "max_search_results": self.config.max_search_results
            },
            "cache_size": len(self._rag_cache),
            "query_history_size": len(self._query_history)
        }

    def clear_cache(self):
        """Clear RAG cache."""
        self._rag_cache.clear()
        self.logger.info("RAG cache cleared")

    def get_query_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent query history."""
        return self._query_history[-limit:]


# Global instance
_rag_ai_integration: Optional[RAGAIIntegration] = None


def get_rag_ai_integration(rag_system: EnhancedRAG, ai_manager: AIProviderManager,
                          config: Optional[RAGAIConfig] = None) -> RAGAIIntegration:
    """Get or create the global RAG-AI integration instance."""
    global _rag_ai_integration

    if _rag_ai_integration is None:
        _rag_ai_integration = RAGAIIntegration(rag_system, ai_manager, config)

    return _rag_ai_integration