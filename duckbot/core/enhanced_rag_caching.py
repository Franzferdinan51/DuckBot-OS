#!/usr/bin/env python3
"""
Enhanced RAG Caching Integration for DuckBot
Intelligent caching layer for RAG operations with similarity matching and performance optimization
"""

import asyncio
import hashlib
import json
import logging
import time
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import numpy as np

from .intelligent_cache import get_intelligent_cache, CacheConfig, CacheEntry
from .enhanced_rag import SearchResult, Document
from .logging_setup import get_logger

logger = get_logger(__name__)


@dataclass
class RAGCacheEntry:
    """Enhanced RAG cache entry with similarity metadata"""
    query: str
    results: List[SearchResult]
    embedding_model: str
    chunking_strategy: str
    similarity_threshold: float
    top_k: int
    filters: Dict[str, Any]
    created_at: datetime = field(default_factory=datetime.now)
    ttl_seconds: int = 7200  # 2 hours default
    access_count: int = 0
    cost_to_generate: float = 0.0

    def get_cache_key(self) -> str:
        """Generate cache key for this entry"""
        normalized_data = {
            "query": self.query.strip(),
            "embedding_model": self.embedding_model,
            "chunking_strategy": self.chunking_strategy,
            "similarity_threshold": self.similarity_threshold,
            "top_k": self.top_k,
            "filters": self.filters or {}
        }
        data_str = json.dumps(normalized_data, sort_keys=True)
        return f"rag_search_{hashlib.md5(data_str.encode()).hexdigest()}"

    def is_expired(self) -> bool:
        """Check if entry has expired"""
        return (datetime.now() - self.created_at).total_seconds() > self.ttl_seconds


class RAGCacheManager:
    """Enhanced RAG cache manager with intelligent features"""

    def __init__(self, cache_config: CacheConfig = None):
        if cache_config is None:
            cache_config = CacheConfig(
                rag_result_ttl_seconds=7200,  # 2 hours for RAG results
                enable_similarity_matching=True,
                similarity_threshold=0.85,
                default_ttl_seconds=7200
            )

        self.cache = get_intelligent_cache(cache_config)
        self.config = cache_config
        self.stats = {
            'rag_hits': 0,
            'rag_misses': 0,
            'similarity_hits': 0,
            'cost_saved': 0.0,
            'average_response_time_saved': 0.0,
            'cache_entries': 0
        }

        # Pending queries for deduplication
        self.pending_queries: Dict[str, asyncio.Future] = {}
        self.query_locks: Dict[str, asyncio.Lock] = {}

        logger.info("Enhanced RAG cache manager initialized")

    async def get_cached_results(self, query: str, embedding_model: str,
                               chunking_strategy: str, similarity_threshold: float,
                               top_k: int, filters: Dict[str, Any] = None) -> Optional[List[SearchResult]]:
        """Get cached RAG search results with exact match"""
        cache_entry = RAGCacheEntry(
            query=query,
            results=[],
            embedding_model=embedding_model,
            chunking_strategy=chunking_strategy,
            similarity_threshold=similarity_threshold,
            top_k=top_k,
            filters=filters or {}
        )

        cache_key = cache_entry.get_cache_key()
        cached_result = await self.cache.get(cache_key)

        if cached_result:
            if not cached_result.is_expired():
                self.stats['rag_hits'] += 1
                self.stats['cost_saved'] += cached_result.cost_to_generate
                logger.debug(f"RAG cache hit for query: {query[:50]}...")
                return cached_result.value['results']
            else:
                # Remove expired entry
                await self.cache.delete(cache_key)

        self.stats['rag_misses'] += 1
        return None

    async def get_similar_results(self, query: str, embedding_model: str,
                                 similarity_threshold: float = 0.9) -> Optional[List[SearchResult]]:
        """Get results from semantically similar queries"""
        if not self.config.enable_similarity_matching:
            return None

        # Generate cache key for similarity search
        similarity_key = f"rag_similarity_{hashlib.md5(query.encode()).hexdigest()}"
        cached_similar = await self.cache.get(similarity_key)

        if cached_similar:
            self.stats['similarity_hits'] += 1
            self.stats['cost_saved'] += cached_similar.cost_to_generate
            logger.debug(f"RAG similarity cache hit for query: {query[:50]}...")
            return cached_similar.value['results']

        return None

    async def cache_results(self, query: str, results: List[SearchResult],
                          embedding_model: str, chunking_strategy: str,
                          similarity_threshold: float, top_k: int,
                          filters: Dict[str, Any] = None,
                          cost_to_generate: float = 0.0) -> bool:
        """Cache RAG search results"""
        try:
            # Create cache entry
            cache_entry = RAGCacheEntry(
                query=query,
                results=results,
                embedding_model=embedding_model,
                chunking_strategy=chunking_strategy,
                similarity_threshold=similarity_threshold,
                top_k=top_k,
                filters=filters or {},
                ttl_seconds=self.config.rag_result_ttl_seconds,
                cost_to_generate=cost_to_generate
            )

            # Cache exact match
            cache_key = cache_entry.get_cache_key()
            success = await self.cache.set(
                cache_key,
                {'results': [asdict(result) for result in results]},
                ttl_seconds=self.config.rag_result_ttl_seconds,
                cost_to_generate=cost_to_generate,
                category="rag_search",
                metadata={
                    'query_type': 'exact_match',
                    'embedding_model': embedding_model,
                    'chunking_strategy': chunking_strategy,
                    'result_count': len(results)
                }
            )

            # Cache for similarity matching if enabled
            if self.config.enable_similarity_matching and results:
                similarity_key = f"rag_similarity_{hashlib.md5(query.encode()).hexdigest()}"
                await self.cache.set(
                    similarity_key,
                    {'results': [asdict(result) for result in results]},
                    ttl_seconds=self.config.rag_result_ttl_seconds,
                    cost_to_generate=cost_to_generate,
                    category="rag_similarity",
                    metadata={
                        'query_type': 'similarity_match',
                        'original_query': query,
                        'embedding_model': embedding_model,
                        'result_count': len(results)
                    }
                )

            self.stats['cache_entries'] += 1
            logger.debug(f"Cached RAG results for query: {query[:50]}...")
            return success

        except Exception as e:
            logger.error(f"Error caching RAG results: {e}")
            return False

    async def search_with_cache(self, rag_system, query: str,
                               embedding_model: str = None,
                               chunking_strategy: str = None,
                               similarity_threshold: float = None,
                               top_k: int = 5,
                               filters: Dict[str, Any] = None) -> Tuple[List[SearchResult], Dict[str, Any]]:
        """
        Perform RAG search with intelligent caching
        Returns (results, metadata)
        """
        start_time = time.time()
        metadata = {
            'cached': False,
            'cache_hit_type': None,
            'response_time_ms': 0,
            'cost_saved': 0.0
        }

        # Use defaults from RAG system if not provided
        if embedding_model is None:
            embedding_model = getattr(rag_system.config, 'embedding_model', 'default')
        if chunking_strategy is None:
            chunking_strategy = getattr(rag_system.config, 'chunking_strategy', 'recursive')
        if similarity_threshold is None:
            similarity_threshold = getattr(rag_system.config, 'similarity_threshold', 0.3)

        # Try exact cache match first
        cached_results = await self.get_cached_results(
            query, embedding_model, chunking_strategy, similarity_threshold, top_k, filters
        )

        if cached_results:
            # Convert dict results back to SearchResult objects
            results = []
            for result_dict in cached_results:
                result = SearchResult(
                    chunk=Document(**result_dict['chunk']),
                    score=result_dict['score'],
                    metadata=result_dict.get('metadata', {})
                )
                results.append(result)

            metadata['cached'] = True
            metadata['cache_hit_type'] = 'exact'
            metadata['response_time_ms'] = (time.time() - start_time) * 1000
            metadata['cost_saved'] = self._estimate_rag_cost()

            return results, metadata

        # Try similarity match
        similar_results = await self.get_similar_results(query, embedding_model)
        if similar_results:
            # Convert dict results back to SearchResult objects
            results = []
            for result_dict in similar_results:
                result = SearchResult(
                    chunk=Document(**result_dict['chunk']),
                    score=result_dict['score'],
                    metadata=result_dict.get('metadata', {})
                )
                results.append(result)

            metadata['cached'] = True
            metadata['cache_hit_type'] = 'similarity'
            metadata['response_time_ms'] = (time.time() - start_time) * 1000
            metadata['cost_saved'] = self._estimate_rag_cost()

            return results, metadata

        # Perform actual search with deduplication
        query_hash = hashlib.md5(f"{query}:{embedding_model}:{chunking_strategy}".encode()).hexdigest()

        if query_hash in self.pending_queries:
            # Wait for existing query
            metadata['deduplicated'] = True
            results = await self.pending_queries[query_hash]
        else:
            # Execute new query
            future = asyncio.get_event_loop().create_future()
            self.pending_queries[query_hash] = future

            try:
                # Perform search
                actual_results = await rag_system.search(
                    query=query,
                    top_k=top_k,
                    filters=filters,
                    similarity_threshold=similarity_threshold
                )

                # Cache results
                await self.cache_results(
                    query, actual_results, embedding_model, chunking_strategy,
                    similarity_threshold, top_k, filters,
                    cost_to_generate=self._estimate_rag_cost()
                )

                results = actual_results
                future.set_result(results)

            except Exception as e:
                logger.error(f"Error in RAG search: {e}")
                future.set_exception(e)
                raise

            finally:
                # Clean up pending query
                self.pending_queries.pop(query_hash, None)

        metadata['response_time_ms'] = (time.time() - start_time) * 1000
        return results, metadata

    async def cache_embeddings(self, text: str, embedding: np.ndarray) -> bool:
        """Cache text embeddings for reuse"""
        try:
            cache_key = f"rag_embedding_{hashlib.md5(text.encode()).hexdigest()}"
            success = await self.cache.set(
                cache_key,
                embedding.tolist(),
                ttl_seconds=self.config.embedding_ttl_seconds,
                cost_to_generate=self._estimate_embedding_cost(),
                category="rag_embedding",
                metadata={
                    'text_length': len(text),
                    'embedding_dim': len(embedding)
                }
            )

            logger.debug(f"Cached embedding for text: {text[:50]}...")
            return success

        except Exception as e:
            logger.error(f"Error caching embedding: {e}")
            return False

    async def get_cached_embedding(self, text: str) -> Optional[np.ndarray]:
        """Get cached text embedding"""
        try:
            cache_key = f"rag_embedding_{hashlib.md5(text.encode()).hexdigest()}"
            cached_result = await self.cache.get(cache_key)

            if cached_result:
                logger.debug(f"Embedding cache hit for text: {text[:50]}...")
                return np.array(cached_result.value)

            return None

        except Exception as e:
            logger.error(f"Error getting cached embedding: {e}")
            return None

    async def cache_documents(self, documents: List[Document]) -> bool:
        """Cache processed documents for fast retrieval"""
        try:
            for doc in documents:
                cache_key = f"rag_document_{doc.id}"
                await self.cache.set(
                    cache_key,
                    asdict(doc),
                    ttl_seconds=self.config.embedding_ttl_seconds * 2,  # Longer TTL for documents
                    cost_to_generate=self._estimate_document_processing_cost(doc),
                    category="rag_document",
                    metadata={
                        'document_type': doc.type.value if hasattr(doc, 'type') else 'unknown',
                        'content_length': len(doc.content) if hasattr(doc, 'content') else 0
                    }
                )

            logger.debug(f"Cached {len(documents)} documents")
            return True

        except Exception as e:
            logger.error(f"Error caching documents: {e}")
            return False

    async def get_cached_document(self, doc_id: str) -> Optional[Document]:
        """Get cached document"""
        try:
            cache_key = f"rag_document_{doc_id}"
            cached_result = await self.cache.get(cache_key)

            if cached_result:
                logger.debug(f"Document cache hit for: {doc_id}")
                return Document(**cached_result.value)

            return None

        except Exception as e:
            logger.error(f"Error getting cached document: {e}")
            return None

    async def cleanup_expired_entries(self) -> int:
        """Clean up expired cache entries"""
        total_removed = 0
        for backend in self.cache.backends.values():
            removed = await backend.cleanup_expired()
            total_removed += removed

        if total_removed > 0:
            logger.info(f"RAG cache cleanup: removed {total_removed} expired entries")
            self.stats['cache_entries'] = max(0, self.stats['cache_entries'] - total_removed)

        return total_removed

    async def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive RAG cache statistics"""
        total_requests = self.stats['rag_hits'] + self.stats['rag_misses']
        hit_rate = self.stats['rag_hits'] / total_requests if total_requests > 0 else 0.0

        stats = {
            'rag_cache_stats': self.stats.copy(),
            'hit_rate': hit_rate,
            'cache_enabled': self.cache is not None,
            'similarity_matching_enabled': self.config.enable_similarity_matching,
            'config': asdict(self.config)
        }

        # Add detailed cache stats if available
        if self.cache:
            try:
                detailed_stats = await self.cache.get_stats()
                stats['detailed_cache_stats'] = detailed_stats
            except Exception as e:
                logger.warning(f"Could not get detailed cache stats: {e}")

        return stats

    def _estimate_rag_cost(self) -> float:
        """Estimate cost for RAG search operation"""
        # Simple cost estimation based on typical RAG operations
        return 0.001  # $0.001 per search (embedding + search)

    def _estimate_embedding_cost(self) -> float:
        """Estimate cost for embedding generation"""
        return 0.0005  # $0.0005 per embedding

    def _estimate_document_processing_cost(self, doc: Document) -> float:
        """Estimate cost for document processing"""
        # Base cost + per-character cost
        base_cost = 0.01
        char_cost = len(getattr(doc, 'content', '')) * 0.000001  # $0.001 per 1K characters
        return base_cost + char_cost

    async def preload_common_queries(self, common_queries: List[str], rag_system):
        """Preload cache with common queries"""
        logger.info(f"Preloading cache with {len(common_queries)} common queries")

        for query in common_queries:
            try:
                results, _ = await self.search_with_cache(
                    rag_system, query,
                    top_k=3,  # Smaller top_k for preloading
                    similarity_threshold=0.8  # Slightly lower threshold
                )

                if results:
                    logger.debug(f"Preloaded query: {query[:50]}...")

            except Exception as e:
                logger.warning(f"Failed to preload query '{query}': {e}")

        logger.info("Cache preloading completed")


# Global instance
_rag_cache_manager: Optional[RAGCacheManager] = None

def get_rag_cache_manager(config: CacheConfig = None) -> RAGCacheManager:
    """Get or create the global RAG cache manager instance"""
    global _rag_cache_manager
    if _rag_cache_manager is None:
        _rag_cache_manager = RAGCacheManager(config)
    return _rag_cache_manager

async def stop_rag_cache_manager():
    """Stop the global RAG cache manager"""
    global _rag_cache_manager
    if _rag_cache_manager is not None:
        await _rag_cache_manager.cleanup_expired_entries()
        _rag_cache_manager = None