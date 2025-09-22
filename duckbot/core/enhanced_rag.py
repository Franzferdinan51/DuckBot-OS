#!/usr/bin/env python3
"""
Enhanced RAG Engine for DuckBot
Advanced Retrieval-Augmented Generation system with multi-vector embeddings,
advanced chunking strategies, hybrid search, and multi-modal support.
"""

import os
import re
import json
import time
import asyncio
import logging
import hashlib
import threading
import pickle
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any, Set
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor
from enum import Enum
import numpy as np
from datetime import datetime, timedelta

# Import optional dependencies
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import sentence_transformers
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

try:
    import fitz  # PyMuPDF
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

try:
    from PIL import Image
    import torch
    import torchvision.transforms as T
    from torchvision.models import resnet50, ResNet50_Weights
    IMAGE_AVAILABLE = True
except ImportError:
    IMAGE_AVAILABLE = False

# Local imports
from .logging_setup import get_logger
from .utilities import safe_read_file, ensure_directory
from .hardware_detector import get_hardware_info

# Import enhanced RAG caching
try:
    from .enhanced_rag_caching import get_rag_cache_manager
    RAG_CACHE_AVAILABLE = True
except ImportError:
    RAG_CACHE_AVAILABLE = False

logger = get_logger(__name__)


class ChunkingStrategy(Enum):
    """Document chunking strategies."""
    RECURSIVE = "recursive"
    SEMANTIC = "semantic"
    FIXED_SIZE = "fixed_size"
    DOCUMENT_AWARE = "document_aware"
    HIERARCHICAL = "hierarchical"


class EmbeddingProvider(Enum):
    """Embedding model providers."""
    OPENAI = "openai"
    LOCAL_SENTENCE_TRANSFORMERS = "local_sentence_transformers"
    LOCAL_QWEN = "local_qwen"
    LM_STUDIO = "lm_studio"
    DUMMY = "dummy"


class DocumentType(Enum):
    """Supported document types."""
    TEXT = "text"
    MARKDOWN = "markdown"
    CODE = "code"
    PDF = "pdf"
    IMAGE = "image"
    JSON = "json"
    HTML = "html"


@dataclass
class Document:
    """Document metadata and content."""
    id: str
    content: str
    doc_type: DocumentType
    source_path: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    chunks: List['Chunk'] = field(default_factory=list)


@dataclass
class Chunk:
    """Text chunk with embedding and metadata."""
    id: str
    document_id: str
    content: str
    chunk_index: int
    embedding: Optional[np.ndarray] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class SearchResult:
    """Search result with relevance score."""
    chunk: Chunk
    document: Document
    score: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RAGConfig:
    """RAG system configuration."""
    # Chunking settings
    chunk_size: int = 800
    chunk_overlap: int = 120
    chunking_strategy: ChunkingStrategy = ChunkingStrategy.RECURSIVE

    # Embedding settings
    embedding_provider: EmbeddingProvider = EmbeddingProvider.LOCAL_SENTENCE_TRANSFORMERS
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dimension: int = 384

    # Search settings
    top_k: int = 4
    similarity_threshold: float = 0.3
    use_hybrid_search: bool = True
    use_semantic_search: bool = True
    use_keyword_search: bool = True

    # Performance settings
    batch_size: int = 32
    max_workers: int = 4
    cache_embeddings: bool = True
    enable_real_time_indexing: bool = True

    # Storage settings
    database_path: str = "data/rag_enhanced.db"
    index_path: str = "data/rag_index.faiss"
    cache_dir: str = "data/rag_cache"

    # Advanced features
    enable_cross_document_reasoning: bool = True
    enable_multi_modal: bool = True
    enable_context_aware: bool = True

    # API settings
    openai_api_key: Optional[str] = None
    openai_base_url: str = "https://api.openai.com/v1"
    lm_studio_url: str = "http://localhost:1234"


class EnhancedRAG:
    """
    Enhanced RAG Engine with advanced features and intelligent caching.
    """

    def __init__(self, config: Optional[RAGConfig] = None):
        self.config = config or RAGConfig()
        self.logger = get_logger(__name__)

        # Initialize components
        self._initialize_directories()

        # Initialize enhanced caching
        self.cache_manager = None
        if RAG_CACHE_AVAILABLE:
            try:
                from .intelligent_cache import CacheConfig
                cache_config = CacheConfig(
                    rag_result_ttl_seconds=7200,  # 2 hours for RAG results
                    enable_similarity_matching=True,
                    similarity_threshold=0.85
                )
                self.cache_manager = get_rag_cache_manager(cache_config)
                self.logger.info("Enhanced RAG caching initialized")
            except Exception as e:
                self.logger.warning(f"Failed to initialize RAG caching: {e}")
        else:
            self.logger.warning("Enhanced RAG caching not available")
        self._initialize_embedding_provider()
        self._initialize_search_components()
        self._initialize_database()

        # Runtime state
        self._document_cache: Dict[str, Document] = {}
        self._embedding_cache: Dict[str, np.ndarray] = {}
        self._index_lock = threading.RLock()
        self._executor = ThreadPoolExecutor(max_workers=self.config.max_workers)

        # Performance tracking
        self._stats = {
            "documents_indexed": 0,
            "chunks_created": 0,
            "searches_performed": 0,
            "avg_search_time": 0.0,
            "cache_hits": 0,
            "cache_misses": 0
        }

        self.logger.info("Enhanced RAG Engine initialized")

    def _initialize_directories(self):
        """Initialize required directories."""
        for path in [self.config.cache_dir, os.path.dirname(self.config.database_path)]:
            ensure_directory(path)

    def _initialize_embedding_provider(self):
        """Initialize the selected embedding provider."""
        if self.config.embedding_provider == EmbeddingProvider.OPENAI:
            if not OPENAI_AVAILABLE:
                self.logger.warning("OpenAI not available, falling back to dummy embeddings")
                self.config.embedding_provider = EmbeddingProvider.DUMMY
            else:
                openai.api_key = self.config.openai_api_key or os.getenv("OPENAI_API_KEY")
                if not openai.api_key:
                    self.logger.warning("OpenAI API key not found, falling back to dummy embeddings")
                    self.config.embedding_provider = EmbeddingProvider.DUMMY

        elif self.config.embedding_provider == EmbeddingProvider.LOCAL_SENTENCE_TRANSFORMERS:
            if not SENTENCE_TRANSFORMERS_AVAILABLE:
                self.logger.warning("Sentence transformers not available, falling back to dummy embeddings")
                self.config.embedding_provider = EmbeddingProvider.DUMMY
            else:
                try:
                    self.embedding_model = sentence_transformers.SentenceTransformer(
                        self.config.embedding_model
                    )
                    self.config.embedding_dimension = self.embedding_model.get_sentence_embedding_dimension()
                    self.logger.info(f"Loaded sentence transformer model: {self.config.embedding_model}")
                except Exception as e:
                    self.logger.error(f"Failed to load sentence transformer: {e}")
                    self.config.embedding_provider = EmbeddingProvider.DUMMY

        elif self.config.embedding_provider == EmbeddingProvider.LM_STUDIO:
            # Initialize LM Studio embedding client
            self.lm_studio_client = None  # TODO: Implement LM Studio embedding client
            self.logger.info("LM Studio embedding provider configured")

        # Initialize dummy embeddings if no provider is available
        if self.config.embedding_provider == EmbeddingProvider.DUMMY:
            self.config.embedding_dimension = 384
            self.logger.info("Using dummy embeddings for RAG system")

    def _initialize_search_components(self):
        """Initialize search components."""
        if SKLEARN_AVAILABLE:
            self.tfidf_vectorizer = TfidfVectorizer(
                max_features=10000,
                stop_words='english',
                ngram_range=(1, 2)
            )
            self.tfidf_matrix = None
            self.tfidf_docs = []
        else:
            self.logger.warning("Scikit-learn not available, keyword search disabled")
            self.config.use_keyword_search = False

    def _initialize_database(self):
        """Initialize SQLite database for document storage."""
        import sqlite3

        self.db_path = self.config.database_path
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                doc_type TEXT NOT NULL,
                source_path TEXT NOT NULL,
                metadata TEXT,
                created_at REAL,
                updated_at REAL
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chunks (
                id TEXT PRIMARY KEY,
                document_id TEXT NOT NULL,
                content TEXT NOT NULL,
                chunk_index INTEGER NOT NULL,
                embedding BLOB,
                metadata TEXT,
                created_at REAL,
                FOREIGN KEY (document_id) REFERENCES documents (id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS search_cache (
                query_hash TEXT PRIMARY KEY,
                results TEXT,
                timestamp REAL
            )
        ''')

        conn.commit()
        conn.close()

        self.logger.info(f"Database initialized at {self.db_path}")

    async def add_document(self, file_path: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Add a document to the RAG system.

        Args:
            file_path: Path to the document file
            metadata: Additional metadata for the document

        Returns:
            Document ID
        """
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")

            # Determine document type
            doc_type = self._detect_document_type(file_path)

            # Extract content based on document type
            content = await self._extract_content(file_path, doc_type)

            # Create document object
            doc_id = hashlib.md5(str(file_path).encode()).hexdigest()
            document = Document(
                id=doc_id,
                content=content,
                doc_type=doc_type,
                source_path=str(file_path),
                metadata=metadata or {},
                created_at=datetime.now(),
                updated_at=datetime.now()
            )

            # Process document (chunk, embed, index)
            await self._process_document(document)

            # Update statistics
            self._stats["documents_indexed"] += 1

            self.logger.info(f"Document added: {file_path} ({doc_type.value})")
            return doc_id

        except Exception as e:
            self.logger.error(f"Error adding document {file_path}: {e}")
            raise

    async def add_text(self, text: str, doc_type: DocumentType = DocumentType.TEXT,
                      metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Add text content directly to the RAG system.

        Args:
            text: Text content to add
            doc_type: Type of document
            metadata: Additional metadata

        Returns:
            Document ID
        """
        try:
            doc_id = hashlib.md5(text.encode()).hexdigest()
            document = Document(
                id=doc_id,
                content=text,
                doc_type=doc_type,
                source_path="direct_input",
                metadata=metadata or {},
                created_at=datetime.now(),
                updated_at=datetime.now()
            )

            await self._process_document(document)
            self._stats["documents_indexed"] += 1

            self.logger.info(f"Text document added: {doc_id}")
            return doc_id

        except Exception as e:
            self.logger.error(f"Error adding text document: {e}")
            raise

    async def search(self, query: str, top_k: Optional[int] = None,
                    filters: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        """
        Search for relevant chunks based on query with enhanced caching.

        Args:
            query: Search query
            top_k: Number of results to return
            filters: Search filters (doc_type, source_path, etc.)

        Returns:
            List of search results
        """
        try:
            start_time = time.time()
            top_k = top_k or self.config.top_k

            # Use enhanced caching if available
            if self.cache_manager:
                results, metadata = await self.cache_manager.search_with_cache(
                    self, query,
                    embedding_model=self.config.embedding_provider.value,
                    chunking_strategy=self.config.chunking_strategy.value,
                    similarity_threshold=self.config.similarity_threshold,
                    top_k=top_k,
                    filters=filters
                )

                if metadata['cached']:
                    self._stats["cache_hits"] += 1
                    self.logger.debug(f"Enhanced cache hit: {metadata['cache_hit_type']}")
                    return results
            else:
                # Fallback to basic caching
                cache_key = hashlib.md5(f"{query}:{top_k}:{json.dumps(filters or {})}".encode()).hexdigest()
                cached_result = self._get_from_cache(cache_key)
                if cached_result:
                    self._stats["cache_hits"] += 1
                    return cached_result

            self._stats["cache_misses"] += 1

            # Perform search
            results = []

            if self.config.use_semantic_search:
                semantic_results = await self._semantic_search(query, top_k, filters)
                results.extend(semantic_results)

            if self.config.use_keyword_search:
                keyword_results = await self._keyword_search(query, top_k, filters)
                results.extend(keyword_results)

            # Remove duplicates and re-rank
            results = self._deduplicate_and_rank(results, top_k)

            # Cache results
            self._cache_results(cache_key, results)

            # Update statistics
            search_time = time.time() - start_time
            self._stats["searches_performed"] += 1
            self._stats["avg_search_time"] = (
                (self._stats["avg_search_time"] * (self._stats["searches_performed"] - 1) + search_time) /
                self._stats["searches_performed"]
            )

            self.logger.debug(f"Search completed in {search_time:.3f}s, found {len(results)} results")
            return results

        except Exception as e:
            self.logger.error(f"Error during search: {e}")
            return []

    async def _semantic_search(self, query: str, top_k: int,
                              filters: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        """Perform semantic search using embeddings."""
        try:
            # Generate query embedding
            query_embedding = await self._generate_embedding(query)

            # Get candidate chunks from database
            candidate_chunks = self._get_candidate_chunks(filters)

            if not candidate_chunks:
                return []

            # Calculate similarities
            similarities = []
            for chunk in candidate_chunks:
                if chunk.embedding is not None:
                    similarity = self._calculate_similarity(query_embedding, chunk.embedding)
                    if similarity >= self.config.similarity_threshold:
                        similarities.append((chunk, similarity))

            # Sort by similarity and get top_k
            similarities.sort(key=lambda x: x[1], reverse=True)
            top_results = similarities[:top_k]

            # Convert to SearchResult objects
            results = []
            for chunk, similarity in top_results:
                document = self._document_cache.get(chunk.document_id)
                if document:
                    result = SearchResult(
                        chunk=chunk,
                        document=document,
                        score=similarity,
                        metadata={"search_type": "semantic"}
                    )
                    results.append(result)

            return results

        except Exception as e:
            self.logger.error(f"Error in semantic search: {e}")
            return []

    async def _keyword_search(self, query: str, top_k: int,
                             filters: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        """Perform keyword search using TF-IDF."""
        if not SKLEARN_AVAILABLE or not self.tfidf_matrix is not None:
            return []

        try:
            # Transform query to TF-IDF
            query_tfidf = self.tfidf_vectorizer.transform([query])

            # Calculate similarities
            similarities = cosine_similarity(query_tfidf, self.tfidf_matrix)[0]

            # Get top results
            top_indices = similarities.argsort()[-top_k:][::-1]

            results = []
            for idx in top_indices:
                if similarities[idx] >= self.config.similarity_threshold:
                    chunk = self.tfidf_docs[idx]
                    document = self._document_cache.get(chunk.document_id)
                    if document:
                        result = SearchResult(
                            chunk=chunk,
                            document=document,
                            score=float(similarities[idx]),
                            metadata={"search_type": "keyword"}
                        )
                        results.append(result)

            return results

        except Exception as e:
            self.logger.error(f"Error in keyword search: {e}")
            return []

    def _deduplicate_and_rank(self, results: List[SearchResult], top_k: int) -> List[SearchResult]:
        """Remove duplicates and rank results."""
        # Remove duplicates based on chunk ID
        seen_chunks = set()
        unique_results = []

        for result in results:
            if result.chunk.id not in seen_chunks:
                seen_chunks.add(result.chunk.id)
                unique_results.append(result)

        # Combine scores for hybrid search
        if self.config.use_hybrid_search:
            combined_scores = {}
            for result in unique_results:
                chunk_id = result.chunk.id
                if chunk_id not in combined_scores:
                    combined_scores[chunk_id] = {
                        "result": result,
                        "semantic_score": 0.0,
                        "keyword_score": 0.0,
                        "score_count": 0
                    }

                search_type = result.metadata.get("search_type", "unknown")
                if search_type == "semantic":
                    combined_scores[chunk_id]["semantic_score"] = result.score
                elif search_type == "keyword":
                    combined_scores[chunk_id]["keyword_score"] = result.score

                combined_scores[chunk_id]["score_count"] += 1

            # Calculate combined scores
            final_results = []
            for chunk_id, data in combined_scores.items():
                # Weighted combination of semantic and keyword scores
                semantic_weight = 0.7
                keyword_weight = 0.3

                combined_score = (
                    data["semantic_score"] * semantic_weight +
                    data["keyword_score"] * keyword_weight
                )

                result = data["result"]
                result.score = combined_score
                result.metadata["combined_score"] = combined_score
                final_results.append(result)

            # Sort by combined score
            final_results.sort(key=lambda x: x.score, reverse=True)
            unique_results = final_results[:top_k]
        else:
            unique_results.sort(key=lambda x: x.score, reverse=True)
            unique_results = unique_results[:top_k]

        return unique_results

    async def _process_document(self, document: Document):
        """Process a document: chunk, embed, and index."""
        try:
            # Chunk the document
            chunks = await self._chunk_document(document)

            # Generate embeddings for chunks
            embedding_tasks = []
            for chunk in chunks:
                task = self._generate_embedding(chunk.content)
                embedding_tasks.append(task)

            if embedding_tasks:
                embeddings = await asyncio.gather(*embedding_tasks, return_exceptions=True)

                for chunk, embedding in zip(chunks, embeddings):
                    if isinstance(embedding, Exception):
                        self.logger.error(f"Error generating embedding for chunk {chunk.id}: {embedding}")
                    else:
                        chunk.embedding = embedding

            # Store in database
            await self._store_document(document, chunks)

            # Update TF-IDF matrix if needed
            if self.config.use_keyword_search:
                await self._update_tfidf_matrix(chunks)

            # Cache document
            self._document_cache[document.id] = document

            self._stats["chunks_created"] += len(chunks)

        except Exception as e:
            self.logger.error(f"Error processing document {document.id}: {e}")
            raise

    async def _chunk_document(self, document: Document) -> List[Chunk]:
        """Chunk document based on configured strategy."""
        try:
            if self.config.chunking_strategy == ChunkingStrategy.RECURSIVE:
                return await self._recursive_chunking(document)
            elif self.config.chunking_strategy == ChunkingStrategy.FIXED_SIZE:
                return await self._fixed_size_chunking(document)
            elif self.config.chunking_strategy == ChunkingStrategy.SEMANTIC:
                return await self._semantic_chunking(document)
            elif self.config.chunking_strategy == ChunkingStrategy.DOCUMENT_AWARE:
                return await self._document_aware_chunking(document)
            elif self.config.chunking_strategy == ChunkingStrategy.HIERARCHICAL:
                return await self._hierarchical_chunking(document)
            else:
                return await self._fixed_size_chunking(document)

        except Exception as e:
            self.logger.error(f"Error chunking document: {e}")
            return await self._fixed_size_chunking(document)

    async def _recursive_chunking(self, document: Document) -> List[Chunk]:
        """Recursive chunking with different separators."""
        content = document.content
        chunks = []

        # Define separators in order of preference
        separators = ["\n\n", "\n", ". ", ", ", " "]

        def recursive_split(text: str, separators: List[str], chunk_size: int) -> List[str]:
            if not separators or len(text) <= chunk_size:
                return [text]

            separator = separators[0]
            parts = text.split(separator)

            result = []
            current_chunk = ""

            for part in parts:
                if len(current_chunk) + len(part) + len(separator) <= chunk_size:
                    current_chunk += part + separator
                else:
                    if current_chunk:
                        result.append(current_chunk.strip())
                    current_chunk = part + separator

                    # If part itself is too long, split it further
                    if len(current_chunk) > chunk_size:
                        sub_chunks = recursive_split(current_chunk, separators[1:], chunk_size)
                        result.extend(sub_chunks[:-1])
                        current_chunk = sub_chunks[-1]

            if current_chunk:
                result.append(current_chunk.strip())

            return result

        text_chunks = recursive_split(content, separators, self.config.chunk_size)

        # Create chunk objects
        for i, chunk_content in enumerate(text_chunks):
            if chunk_content.strip():
                chunk = Chunk(
                    id=f"{document.id}_chunk_{i}",
                    document_id=document.id,
                    content=chunk_content.strip(),
                    chunk_index=i,
                    metadata={"chunking_strategy": "recursive"}
                )
                chunks.append(chunk)

        return chunks

    async def _fixed_size_chunking(self, document: Document) -> List[Chunk]:
        """Fixed-size chunking with overlap."""
        content = document.content
        chunks = []

        start = 0
        content_length = len(content)

        while start < content_length:
            end = min(start + self.config.chunk_size, content_length)
            chunk_content = content[start:end]

            # Create chunk object
            chunk = Chunk(
                id=f"{document.id}_chunk_{len(chunks)}",
                document_id=document.id,
                content=chunk_content,
                chunk_index=len(chunks),
                metadata={"chunking_strategy": "fixed_size"}
            )
            chunks.append(chunk)

            # Move to next chunk with overlap
            if end >= content_length:
                break
            start = max(start + self.config.chunk_size - self.config.chunk_overlap, start + 1)

        return chunks

    async def _semantic_chunking(self, document: Document) -> List[Chunk]:
        """Semantic chunking based on content similarity."""
        # For now, fall back to fixed-size chunking
        # TODO: Implement proper semantic chunking
        self.logger.warning("Semantic chunking not fully implemented, using fixed-size")
        return await self._fixed_size_chunking(document)

    async def _document_aware_chunking(self, document: Document) -> List[Chunk]:
        """Document-aware chunking based on document structure."""
        content = document.content
        chunks = []

        if document.doc_type == DocumentType.MARKDOWN:
            # Split by markdown headers
            sections = re.split(r'\n#+\s+', content)

            current_chunk = ""
            chunk_index = 0

            for section in sections:
                if not section.strip():
                    continue

                # If adding this section would exceed chunk size, create new chunk
                if len(current_chunk) + len(section) > self.config.chunk_size and current_chunk:
                    chunk = Chunk(
                        id=f"{document.id}_chunk_{chunk_index}",
                        document_id=document.id,
                        content=current_chunk.strip(),
                        chunk_index=chunk_index,
                        metadata={"chunking_strategy": "document_aware", "section": True}
                    )
                    chunks.append(chunk)
                    chunk_index += 1
                    current_chunk = section
                else:
                    if current_chunk:
                        current_chunk += "\n\n" + section
                    else:
                        current_chunk = section

            # Add remaining content
            if current_chunk:
                chunk = Chunk(
                    id=f"{document.id}_chunk_{chunk_index}",
                    document_id=document.id,
                    content=current_chunk.strip(),
                    chunk_index=chunk_index,
                    metadata={"chunking_strategy": "document_aware", "section": True}
                )
                chunks.append(chunk)

        elif document.doc_type == DocumentType.CODE:
            # Split by functions/classes
            functions = re.split(r'\n(def |class |async def )', content)

            current_chunk = ""
            chunk_index = 0

            for i, part in enumerate(functions):
                if i == 0:
                    current_chunk = part
                    continue

                # Add function/class signature
                function_part = functions[i-1] + part

                if len(current_chunk) + len(function_part) > self.config.chunk_size and current_chunk:
                    chunk = Chunk(
                        id=f"{document.id}_chunk_{chunk_index}",
                        document_id=document.id,
                        content=current_chunk.strip(),
                        chunk_index=chunk_index,
                        metadata={"chunking_strategy": "document_aware", "code_function": True}
                    )
                    chunks.append(chunk)
                    chunk_index += 1
                    current_chunk = function_part
                else:
                    current_chunk += function_part

            # Add remaining content
            if current_chunk:
                chunk = Chunk(
                    id=f"{document.id}_chunk_{chunk_index}",
                    document_id=document.id,
                    content=current_chunk.strip(),
                    chunk_index=chunk_index,
                    metadata={"chunking_strategy": "document_aware", "code_function": True}
                )
                chunks.append(chunk)
        else:
            # Fall back to fixed-size chunking
            return await self._fixed_size_chunking(document)

        return chunks

    async def _hierarchical_chunking(self, document: Document) -> List[Chunk]:
        """Hierarchical chunking with multiple levels."""
        # For now, fall back to fixed-size chunking
        # TODO: Implement proper hierarchical chunking
        self.logger.warning("Hierarchical chunking not fully implemented, using fixed-size")
        return await self._fixed_size_chunking(document)

    async def _generate_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for text using configured provider."""
        try:
            # Check cache first
            if self.config.cache_embeddings:
                cache_key = hashlib.md5(text.encode()).hexdigest()
                if cache_key in self._embedding_cache:
                    return self._embedding_cache[cache_key]

            # Generate embedding based on provider
            if self.config.embedding_provider == EmbeddingProvider.OPENAI:
                embedding = await self._generate_openai_embedding(text)
            elif self.config.embedding_provider == EmbeddingProvider.LOCAL_SENTENCE_TRANSFORMERS:
                embedding = await self._generate_sentence_transformer_embedding(text)
            elif self.config.embedding_provider == EmbeddingProvider.LM_STUDIO:
                embedding = await self._generate_lm_studio_embedding(text)
            else:
                # Dummy embedding
                embedding = np.random.rand(self.config.embedding_dimension).astype(np.float32)

            # Cache embedding
            if self.config.cache_embeddings:
                self._embedding_cache[cache_key] = embedding

            return embedding

        except Exception as e:
            self.logger.error(f"Error generating embedding: {e}")
            # Return dummy embedding as fallback
            return np.random.rand(self.config.embedding_dimension).astype(np.float32)

    async def _generate_openai_embedding(self, text: str) -> np.ndarray:
        """Generate embedding using OpenAI API."""
        try:
            response = await openai.Embedding.acreate(
                model="text-embedding-ada-002",
                input=text[:8000]  # Limit text length
            )

            embedding = np.array(response['data'][0]['embedding'], dtype=np.float32)
            return embedding

        except Exception as e:
            self.logger.error(f"OpenAI embedding error: {e}")
            raise

    async def _generate_sentence_transformer_embedding(self, text: str) -> np.ndarray:
        """Generate embedding using sentence transformers."""
        try:
            embedding = self.embedding_model.encode(text, convert_to_numpy=True)
            return embedding.astype(np.float32)

        except Exception as e:
            self.logger.error(f"Sentence transformer embedding error: {e}")
            raise

    async def _generate_lm_studio_embedding(self, text: str) -> np.ndarray:
        """Generate embedding using LM Studio."""
        # TODO: Implement LM Studio embedding generation
        self.logger.warning("LM Studio embedding not implemented, using dummy")
        return np.random.rand(self.config.embedding_dimension).astype(np.float32)

    def _calculate_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """Calculate cosine similarity between two embeddings."""
        try:
            if embedding1 is None or embedding2 is None:
                return 0.0

            # Normalize embeddings
            embedding1_norm = embedding1 / np.linalg.norm(embedding1)
            embedding2_norm = embedding2 / np.linalg.norm(embedding2)

            # Calculate cosine similarity
            similarity = np.dot(embedding1_norm, embedding2_norm)
            return float(similarity)

        except Exception as e:
            self.logger.error(f"Error calculating similarity: {e}")
            return 0.0

    def _detect_document_type(self, file_path: Path) -> DocumentType:
        """Detect document type based on file extension."""
        extension = file_path.suffix.lower()

        if extension in ['.md', '.markdown']:
            return DocumentType.MARKDOWN
        elif extension in ['.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', '.go', '.rs', '.php']:
            return DocumentType.CODE
        elif extension in ['.pdf']:
            return DocumentType.PDF
        elif extension in ['.json']:
            return DocumentType.JSON
        elif extension in ['.html', '.htm']:
            return DocumentType.HTML
        elif extension in ['.txt', '.log']:
            return DocumentType.TEXT
        else:
            return DocumentType.TEXT

    async def _extract_content(self, file_path: Path, doc_type: DocumentType) -> str:
        """Extract content from file based on document type."""
        try:
            if doc_type == DocumentType.PDF:
                return await self._extract_pdf_content(file_path)
            elif doc_type == DocumentType.IMAGE:
                return await self._extract_image_content(file_path)
            elif doc_type == DocumentType.JSON:
                return await self._extract_json_content(file_path)
            elif doc_type == DocumentType.HTML:
                return await self._extract_html_content(file_path)
            else:
                # Plain text extraction
                return await safe_read_file(str(file_path))

        except Exception as e:
            self.logger.error(f"Error extracting content from {file_path}: {e}")
            return ""

    async def _extract_pdf_content(self, file_path: Path) -> str:
        """Extract text content from PDF file."""
        if not PDF_AVAILABLE:
            self.logger.warning("PDF extraction not available")
            return ""

        try:
            doc = fitz.open(str(file_path))
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return text

        except Exception as e:
            self.logger.error(f"Error extracting PDF content: {e}")
            return ""

    async def _extract_image_content(self, file_path: Path) -> str:
        """Extract content from image file."""
        if not IMAGE_AVAILABLE:
            self.logger.warning("Image extraction not available")
            return ""

        try:
            # Load image
            image = Image.open(file_path)

            # Use pre-trained model for image features
            # This is a placeholder - in a real implementation, you'd use OCR or image captioning
            image_tensor = T.ToTensor()(image).unsqueeze(0)

            # Generate image description (placeholder)
            description = f"Image of size {image.size} with {image.mode} color mode"

            return description

        except Exception as e:
            self.logger.error(f"Error extracting image content: {e}")
            return ""

    async def _extract_json_content(self, file_path: Path) -> str:
        """Extract content from JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Convert to readable text
            text = json.dumps(data, indent=2, ensure_ascii=False)
            return text

        except Exception as e:
            self.logger.error(f"Error extracting JSON content: {e}")
            return ""

    async def _extract_html_content(self, file_path: Path) -> str:
        """Extract text content from HTML file."""
        try:
            from bs4 import BeautifulSoup

            with open(file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()

            soup = BeautifulSoup(html_content, 'html.parser')

            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()

            # Get text
            text = soup.get_text(separator=' ', strip=True)

            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)

            return text

        except Exception as e:
            self.logger.error(f"Error extracting HTML content: {e}")
            return ""

    async def _store_document(self, document: Document, chunks: List[Chunk]):
        """Store document and chunks in database."""
        try:
            import sqlite3

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Store document
            cursor.execute('''
                INSERT OR REPLACE INTO documents
                (id, content, doc_type, source_path, metadata, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                document.id,
                document.content,
                document.doc_type.value,
                document.source_path,
                json.dumps(document.metadata),
                document.created_at.timestamp(),
                document.updated_at.timestamp()
            ))

            # Store chunks
            for chunk in chunks:
                embedding_blob = pickle.dumps(chunk.embedding) if chunk.embedding is not None else None

                cursor.execute('''
                    INSERT OR REPLACE INTO chunks
                    (id, document_id, content, chunk_index, embedding, metadata, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    chunk.id,
                    chunk.document_id,
                    chunk.content,
                    chunk.chunk_index,
                    embedding_blob,
                    json.dumps(chunk.metadata),
                    chunk.created_at.timestamp()
                ))

            conn.commit()
            conn.close()

        except Exception as e:
            self.logger.error(f"Error storing document: {e}")
            raise

    def _get_candidate_chunks(self, filters: Optional[Dict[str, Any]] = None) -> List[Chunk]:
        """Get candidate chunks from database based on filters."""
        try:
            import sqlite3

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            query = "SELECT id, document_id, content, chunk_index, embedding, metadata, created_at FROM chunks"
            params = []

            if filters:
                conditions = []

                if "doc_type" in filters:
                    conditions.append("document_id IN (SELECT id FROM documents WHERE doc_type = ?)")
                    params.append(filters["doc_type"])

                if "source_path" in filters:
                    conditions.append("document_id IN (SELECT id FROM documents WHERE source_path LIKE ?)")
                    params.append(f"%{filters['source_path']}%")

                if conditions:
                    query += " WHERE " + " AND ".join(conditions)

            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()

            chunks = []
            for row in rows:
                chunk_id, document_id, content, chunk_index, embedding_blob, metadata_json, created_at = row

                # Deserialize embedding
                embedding = pickle.loads(embedding_blob) if embedding_blob else None

                # Deserialize metadata
                metadata = json.loads(metadata_json) if metadata_json else {}

                chunk = Chunk(
                    id=chunk_id,
                    document_id=document_id,
                    content=content,
                    chunk_index=chunk_index,
                    embedding=embedding,
                    metadata=metadata,
                    created_at=datetime.fromtimestamp(created_at)
                )
                chunks.append(chunk)

            return chunks

        except Exception as e:
            self.logger.error(f"Error getting candidate chunks: {e}")
            return []

    async def _update_tfidf_matrix(self, chunks: List[Chunk]):
        """Update TF-IDF matrix for keyword search."""
        if not SKLEARN_AVAILABLE:
            return

        try:
            # Add new chunks to TF-IDF docs
            new_texts = [chunk.content for chunk in chunks]
            self.tfidf_docs.extend(chunks)

            # Fit or update TF-IDF vectorizer
            if self.tfidf_matrix is None:
                self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(new_texts)
            else:
                new_matrix = self.tfidf_vectorizer.transform(new_texts)
                self.tfidf_matrix = np.vstack([self.tfidf_matrix, new_matrix])

        except Exception as e:
            self.logger.error(f"Error updating TF-IDF matrix: {e}")

    def _get_from_cache(self, cache_key: str) -> Optional[List[SearchResult]]:
        """Get search results from cache."""
        try:
            import sqlite3

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT results, timestamp FROM search_cache WHERE query_hash = ?
            ''', (cache_key,))

            row = cursor.fetchone()
            conn.close()

            if row:
                results_json, timestamp = row
                # Check if cache is still valid (24 hours)
                if time.time() - timestamp < 86400:
                    results_data = json.loads(results_json)
                    results = []

                    for result_data in results_data:
                        # Reconstruct SearchResult objects
                        # This is simplified - in production, you'd need proper serialization
                        pass

                    return results

        except Exception as e:
            self.logger.error(f"Error getting from cache: {e}")

        return None

    def _cache_results(self, cache_key: str, results: List[SearchResult]):
        """Cache search results."""
        try:
            import sqlite3

            # Serialize results
            results_data = []
            for result in results:
                result_data = {
                    "chunk_id": result.chunk.id,
                    "document_id": result.document.id,
                    "score": result.score,
                    "metadata": result.metadata
                }
                results_data.append(result_data)

            results_json = json.dumps(results_data)

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR REPLACE INTO search_cache (query_hash, results, timestamp)
                VALUES (?, ?, ?)
            ''', (cache_key, results_json, time.time()))

            conn.commit()
            conn.close()

        except Exception as e:
            self.logger.error(f"Error caching results: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get RAG system statistics."""
        return {
            **self._stats,
            "documents_cached": len(self._document_cache),
            "embeddings_cached": len(self._embedding_cache),
            "config": {
                "chunking_strategy": self.config.chunking_strategy.value,
                "embedding_provider": self.config.embedding_provider.value,
                "embedding_model": self.config.embedding_model,
                "embedding_dimension": self.config.embedding_dimension,
                "use_hybrid_search": self.config.use_hybrid_search,
                "use_semantic_search": self.config.use_semantic_search,
                "use_keyword_search": self.config.use_keyword_search
            }
        }

    def clear_cache(self):
        """Clear all caches."""
        self._document_cache.clear()
        self._embedding_cache.clear()
        self._stats["cache_hits"] = 0
        self._stats["cache_misses"] = 0

        try:
            import sqlite3
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM search_cache")
            conn.commit()
            conn.close()

        except Exception as e:
            self.logger.error(f"Error clearing cache: {e}")

    async def clear_index(self):
        """Clear the entire RAG index."""
        try:
            import sqlite3
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("DELETE FROM documents")
            cursor.execute("DELETE FROM chunks")
            cursor.execute("DELETE FROM search_cache")

            conn.commit()
            conn.close()

            # Clear caches
            self.clear_cache()

            # Reset TF-IDF matrix
            if SKLEARN_AVAILABLE:
                self.tfidf_matrix = None
                self.tfidf_docs = []

            # Reset statistics
            self._stats = {
                "documents_indexed": 0,
                "chunks_created": 0,
                "searches_performed": 0,
                "avg_search_time": 0.0,
                "cache_hits": 0,
                "cache_misses": 0
            }

            self.logger.info("RAG index cleared")

        except Exception as e:
            self.logger.error(f"Error clearing index: {e}")
            raise

    async def build_context(self, query: str, max_chars: int = 2000) -> Tuple[str, List[Dict]]:
        """Build context string from search results."""
        try:
            results = await self.search(query)

            if not results:
                return "", []

            context_parts = []
            metadata = []
            total_chars = 0

            for result in results:
                # Format context part
                source_name = Path(result.document.source_path).name
                context_part = f"[Source: {source_name} | Score: {result.score:.3f}]\n{result.chunk.content.strip()}"

                if total_chars + len(context_part) > max_chars:
                    break

                context_parts.append(context_part)
                total_chars += len(context_part)

                metadata.append({
                    "chunk_id": result.chunk.id,
                    "document_id": result.document.id,
                    "source": result.document.source_path,
                    "score": result.score,
                    "metadata": result.metadata
                })

            context = "\n\n".join(context_parts)
            return context, metadata

        except Exception as e:
            self.logger.error(f"Error building context: {e}")
            return "", []

    async def close(self):
        """Clean up resources."""
        try:
            self._executor.shutdown(wait=True)
            self.logger.info("Enhanced RAG Engine closed")

        except Exception as e:
            self.logger.error(f"Error closing RAG engine: {e}")


# Global instance
_rag_instance: Optional[EnhancedRAG] = None


def get_rag_instance(config: Optional[RAGConfig] = None) -> EnhancedRAG:
    """Get or create the global RAG instance."""
    global _rag_instance

    if _rag_instance is None:
        _rag_instance = EnhancedRAG(config)

    return _rag_instance


async def initialize_rag_system(config: Optional[RAGConfig] = None) -> EnhancedRAG:
    """Initialize the RAG system."""
    global _rag_instance

    if _rag_instance is None:
        _rag_instance = EnhancedRAG(config)

    return _rag_instance


async def shutdown_rag_system():
    """Shutdown the RAG system."""
    global _rag_instance

    if _rag_instance is not None:
        await _rag_instance.close()
        _rag_instance = None