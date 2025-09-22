#!/usr/bin/env python3
"""
RAG DeepCode Integration Module for DuckBot
Integrates RAG system with DeepCode operations for enhanced code analysis and generation.
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
from datetime import datetime
import hashlib
import re

# Local imports
from ..core.enhanced_rag import EnhancedRAG, DocumentType
from ..core.logging_setup import get_logger

logger = get_logger(__name__)


class CodeAnalysisType(Enum):
    """Types of code analysis operations."""
    CODE_REVIEW = "code_review"
    BUG_DETECTION = "bug_detection"
    PERFORMANCE_ANALYSIS = "performance_analysis"
    SECURITY_ANALYSIS = "security_analysis"
    REFACTORING_SUGGESTIONS = "refactoring_suggestions"
    DOCUMENTATION_GENERATION = "documentation_generation"
    CODE_COMPLETION = "code_completion"
    CODE_EXPLANATION = "code_explanation"


class CodeLanguage(Enum):
    """Programming languages."""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    JAVA = "java"
    CPP = "cpp"
    CSHARP = "csharp"
    GO = "go"
    RUST = "rust"
    TYPESCRIPT = "typescript"
    HTML = "html"
    CSS = "css"
    SQL = "sql"
    BASH = "bash"
    POWERSHELL = "powershell"


@dataclass
class CodeContext:
    """Code context information."""
    file_path: str
    language: CodeLanguage
    code: str
    dependencies: List[str] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    functions: List[str] = field(default_factory=list)
    classes: List[str] = field(default_factory=list)
    variables: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CodeAnalysisResult:
    """Result of code analysis."""
    analysis_type: CodeAnalysisType
    language: CodeLanguage
    file_path: str
    findings: List[Dict[str, Any]]
    suggestions: List[Dict[str, Any]]
    score: float
    confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    processing_time: float = 0.0


@dataclass
class RAGDeepCodeConfig:
    """Configuration for RAG-DeepCode integration."""
    # Analysis settings
    enabled_analyses: List[CodeAnalysisType] = field(default_factory=lambda: [
        CodeAnalysisType.CODE_REVIEW,
        CodeAnalysisType.BUG_DETECTION,
        CodeAnalysisType.PERFORMANCE_ANALYSIS
    ])

    # Language support
    supported_languages: List[CodeLanguage] = field(default_factory=lambda: [
        CodeLanguage.PYTHON,
        CodeLanguage.JAVASCRIPT,
        CodeLanguage.JAVA,
        CodeLanguage.CPP,
        CodeLanguage.GO
    ])

    # Performance settings
    max_file_size: int = 100000  # 100KB
    max_analysis_time: int = 300  # 5 minutes
    enable_parallel_analysis: bool = True
    max_concurrent_analyses: int = 5

    # Knowledge base settings
    enable_code_knowledge: bool = True
    code_patterns_file: str = "data/code_patterns.json"
    best_practices_file: str = "data/best_practices.json"
    security_patterns_file: str = "data/security_patterns.json"

    # Learning settings
    enable_learning: bool = True
    learn_from_feedback: bool = True
    feedback_file: str = "data/code_feedback.json"

    # Debug settings
    debug_analysis: bool = False
    log_analysis_details: bool = True


class RAGDeepCodeIntegration:
    """
    Integration between RAG system and DeepCode operations.
    """

    def __init__(self, rag_system: EnhancedRAG, config: Optional[RAGDeepCodeConfig] = None):
        self.rag_system = rag_system
        self.config = config or RAGDeepCodeConfig()
        self.logger = get_logger(__name__)

        # Initialize code knowledge base
        self.code_patterns: Dict[str, Any] = {}
        self.best_practices: Dict[str, Any] = {}
        self.security_patterns: Dict[str, Any] = {}
        self.feedback_data: List[Dict[str, Any]] = []

        # Analysis cache
        self.analysis_cache: Dict[str, CodeAnalysisResult] = {}

        # Background tasks
        self._learning_task: Optional[asyncio.Task] = None

        # Initialize systems
        self._initialize_knowledge_base()
        self._start_background_tasks()

        self.logger.info("RAG-DeepCode Integration initialized")

    def _initialize_knowledge_base(self):
        """Initialize code knowledge base."""
        try:
            # Load code patterns
            if Path(self.config.code_patterns_file).exists():
                with open(self.config.code_patterns_file, 'r') as f:
                    self.code_patterns = json.load(f)
                self.logger.info(f"Loaded {len(self.code_patterns)} code patterns")

            # Load best practices
            if Path(self.config.best_practices_file).exists():
                with open(self.config.best_practices_file, 'r') as f:
                    self.best_practices = json.load(f)
                self.logger.info(f"Loaded {len(self.best_practices)} best practices")

            # Load security patterns
            if Path(self.config.security_patterns_file).exists():
                with open(self.config.security_patterns_file, 'r') as f:
                    self.security_patterns = json.load(f)
                self.logger.info(f"Loaded {len(self.security_patterns)} security patterns")

            # Load feedback data
            if Path(self.config.feedback_file).exists():
                with open(self.config.feedback_file, 'r') as f:
                    self.feedback_data = json.load(f)
                self.logger.info(f"Loaded {len(self.feedback_data)} feedback entries")

        except Exception as e:
            self.logger.error(f"Error initializing knowledge base: {e}")

    def _start_background_tasks(self):
        """Start background learning tasks."""
        if self.config.enable_learning:
            self._learning_task = asyncio.create_task(self._learning_loop())
            self.logger.info("DeepCode learning task started")

    async def _learning_loop(self):
        """Background task for continuous learning."""
        while True:
            try:
                await asyncio.sleep(3600)  # Learn every hour
                await self._learn_from_feedback()

            except Exception as e:
                self.logger.error(f"Error in DeepCode learning loop: {e}")
                await asyncio.sleep(60)  # Wait before retrying

    async def analyze_code(self, file_path: str, analysis_types: Optional[List[CodeAnalysisType]] = None,
                         context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Analyze code using RAG-enhanced DeepCode operations.

        Args:
            file_path: Path to code file
            analysis_types: Types of analysis to perform
            context: Additional context for analysis

        Returns:
            Analysis results
        """
        try:
            start_time = time.time()

            # Validate file
            file_path = Path(file_path)
            if not file_path.exists():
                return {"success": False, "error": f"File not found: {file_path}"}

            if file_path.stat().st_size > self.config.max_file_size:
                return {"success": False, "error": f"File too large: {file_path}"}

            # Read and parse code
            code_content = await self._read_code_file(file_path)
            code_context = await self._parse_code_context(file_path, code_content)

            # Determine analysis types
            if analysis_types is None:
                analysis_types = self.config.enabled_analyses

            # Filter supported analyses
            analysis_types = [at for at in analysis_types if at in self.config.enabled_analyses]

            # Perform analyses
            analysis_tasks = []
            for analysis_type in analysis_types:
                if self.config.enable_parallel_analysis:
                    task = self._perform_analysis(analysis_type, code_context, context)
                    analysis_tasks.append(task)
                else:
                    result = await self._perform_analysis(analysis_type, code_context, context)
                    analysis_tasks.append(result)

            # Wait for all analyses to complete
            if self.config.enable_parallel_analysis:
                results = await asyncio.gather(*analysis_tasks, return_exceptions=True)
            else:
                results = analysis_tasks

            # Process results
            successful_results = []
            failed_results = []

            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    failed_results.append({
                        "analysis_type": analysis_types[i].value,
                        "error": str(result)
                    })
                else:
                    successful_results.append(result)

            # Calculate overall score
            overall_score = sum(r.score for r in successful_results) / len(successful_results) if successful_results else 0

            # Store analysis result
            cache_key = self._get_analysis_cache_key(file_path, analysis_types)
            self.analysis_cache[cache_key] = CodeAnalysisResult(
                analysis_type=CodeAnalysisType.MULTI_ANALYSIS,  # Placeholder
                language=code_context.language,
                file_path=str(file_path),
                findings=[f for r in successful_results for f in r.findings],
                suggestions=[s for r in successful_results for s in r.suggestions],
                score=overall_score,
                confidence=sum(r.confidence for r in successful_results) / len(successful_results) if successful_results else 0,
                processing_time=time.time() - start_time
            )

            # Add code to RAG system
            await self._add_code_to_rag(file_path, code_content, code_context)

            return {
                "success": True,
                "file_path": str(file_path),
                "language": code_context.language.value,
                "analyses": {
                    "successful": len(successful_results),
                    "failed": len(failed_results),
                    "results": [
                        {
                            "type": r.analysis_type.value,
                            "score": r.score,
                            "confidence": r.confidence,
                            "findings_count": len(r.findings),
                            "suggestions_count": len(r.suggestions)
                        }
                        for r in successful_results
                    ],
                    "failed_details": failed_results
                },
                "overall_score": overall_score,
                "processing_time": time.time() - start_time
            }

        except Exception as e:
            self.logger.error(f"Error analyzing code {file_path}: {e}")
            return {"success": False, "error": str(e)}

    async def _perform_analysis(self, analysis_type: CodeAnalysisType, code_context: CodeContext,
                              context: Optional[Dict[str, Any]] = None) -> CodeAnalysisResult:
        """Perform a specific type of code analysis."""
        try:
            start_time = time.time()

            if analysis_type == CodeAnalysisType.CODE_REVIEW:
                result = await self._code_review_analysis(code_context, context)
            elif analysis_type == CodeAnalysisType.BUG_DETECTION:
                result = await self._bug_detection_analysis(code_context, context)
            elif analysis_type == CodeAnalysisType.PERFORMANCE_ANALYSIS:
                result = await self._performance_analysis(code_context, context)
            elif analysis_type == CodeAnalysisType.SECURITY_ANALYSIS:
                result = await self._security_analysis(code_context, context)
            elif analysis_type == CodeAnalysisType.REFACTORING_SUGGESTIONS:
                result = await self._refactoring_analysis(code_context, context)
            elif analysis_type == CodeAnalysisType.DOCUMENTATION_GENERATION:
                result = await self._documentation_analysis(code_context, context)
            elif analysis_type == CodeAnalysisType.CODE_COMPLETION:
                result = await self._code_completion_analysis(code_context, context)
            elif analysis_type == CodeAnalysisType.CODE_EXPLANATION:
                result = await self._code_explanation_analysis(code_context, context)
            else:
                raise ValueError(f"Unsupported analysis type: {analysis_type}")

            result.processing_time = time.time() - start_time
            return result

        except Exception as e:
            self.logger.error(f"Error in {analysis_type.value} analysis: {e}")
            raise

    async def _code_review_analysis(self, code_context: CodeContext, context: Optional[Dict[str, Any]] = None) -> CodeAnalysisResult:
        """Perform code review analysis."""
        try:
            findings = []
            suggestions = []

            # Search for code review patterns
            query = f"code review best practices {code_context.language.value}"
            search_results = await self.rag_system.search(query, top_k=3)

            # Analyze code structure
            lines = code_context.code.split('\n')
            line_count = len(lines)

            # Check for common issues
            if line_count > 500:
                findings.append({
                    "type": "structure",
                    "severity": "medium",
                    "message": "File is quite large, consider splitting into smaller modules",
                    "line": 0
                })

            # Check function lengths
            function_pattern = self._get_function_pattern(code_context.language)
            functions = re.finditer(function_pattern, code_context.code)
            for match in functions:
                func_start = match.start()
                func_end = match.end()
                func_lines = code_context.code[func_start:func_end].count('\n')

                if func_lines > 50:
                    findings.append({
                        "type": "function_length",
                        "severity": "medium",
                        "message": f"Function is {func_lines} lines long, consider breaking it down",
                        "line": code_context.code[:func_start].count('\n') + 1
                    })

            # Generate suggestions based on search results
            for result in search_results:
                suggestions.append({
                    "type": "best_practice",
                    "suggestion": f"Consider: {result.chunk.content[:200]}...",
                    "source": result.document.source_path,
                    "confidence": result.score
                })

            # Calculate score
            score = max(0, 1.0 - len([f for f in findings if f["severity"] == "high"]) * 0.3 -
                       len([f for f in findings if f["severity"] == "medium"]) * 0.1)

            return CodeAnalysisResult(
                analysis_type=CodeAnalysisType.CODE_REVIEW,
                language=code_context.language,
                file_path=code_context.file_path,
                findings=findings,
                suggestions=suggestions,
                score=score,
                confidence=0.8
            )

        except Exception as e:
            self.logger.error(f"Error in code review analysis: {e}")
            raise

    async def _bug_detection_analysis(self, code_context: CodeContext, context: Optional[Dict[str, Any]] = None) -> CodeAnalysisResult:
        """Perform bug detection analysis."""
        try:
            findings = []
            suggestions = []

            # Search for common bug patterns
            query = f"common bugs {code_context.language.value} programming"
            search_results = await self.rag_system.search(query, top_k=3)

            # Language-specific bug detection
            if code_context.language == CodeLanguage.PYTHON:
                findings.extend(self._detect_python_bugs(code_context))
            elif code_context.language == CodeLanguage.JAVASCRIPT:
                findings.extend(self._detect_javascript_bugs(code_context))

            # Generate suggestions based on findings
            for finding in findings:
                suggestions.append({
                    "type": "bug_fix",
                    "suggestion": f"Fix: {finding['message']}",
                    "line": finding.get("line", 0),
                    "confidence": 0.9
                })

            # Calculate score
            score = max(0, 1.0 - len([f for f in findings if f["severity"] == "high"]) * 0.4 -
                       len([f for f in findings if f["severity"] == "medium"]) * 0.2)

            return CodeAnalysisResult(
                analysis_type=CodeAnalysisType.BUG_DETECTION,
                language=code_context.language,
                file_path=code_context.file_path,
                findings=findings,
                suggestions=suggestions,
                score=score,
                confidence=0.7
            )

        except Exception as e:
            self.logger.error(f"Error in bug detection analysis: {e}")
            raise

    async def _performance_analysis(self, code_context: CodeContext, context: Optional[Dict[str, Any]] = None) -> CodeAnalysisResult:
        """Perform performance analysis."""
        try:
            findings = []
            suggestions = []

            # Search for performance patterns
            query = f"performance optimization {code_context.language.value}"
            search_results = await self.rag_system.search(query, top_k=3)

            # Analyze code for performance issues
            if code_context.language == CodeLanguage.PYTHON:
                findings.extend(self._detect_python_performance_issues(code_context))

            # Generate suggestions
            for result in search_results:
                suggestions.append({
                    "type": "performance",
                    "suggestion": f"Optimization tip: {result.chunk.content[:200]}...",
                    "source": result.document.source_path,
                    "confidence": result.score
                })

            # Calculate score
            score = max(0, 1.0 - len(findings) * 0.2)

            return CodeAnalysisResult(
                analysis_type=CodeAnalysisType.PERFORMANCE_ANALYSIS,
                language=code_context.language,
                file_path=code_context.file_path,
                findings=findings,
                suggestions=suggestions,
                score=score,
                confidence=0.6
            )

        except Exception as e:
            self.logger.error(f"Error in performance analysis: {e}")
            raise

    async def _security_analysis(self, code_context: CodeContext, context: Optional[Dict[str, Any]] = None) -> CodeAnalysisResult:
        """Perform security analysis."""
        try:
            findings = []
            suggestions = []

            # Search for security patterns
            query = f"security vulnerabilities {code_context.language.value}"
            search_results = await self.rag_system.search(query, top_k=3)

            # Analyze code for security issues
            security_findings = self._detect_security_issues(code_context)
            findings.extend(security_findings)

            # Generate security suggestions
            for result in search_results:
                suggestions.append({
                    "type": "security",
                    "suggestion": f"Security recommendation: {result.chunk.content[:200]}...",
                    "source": result.document.source_path,
                    "confidence": result.score
                })

            # Calculate score (security is critical)
            score = max(0, 1.0 - len([f for f in findings if f["severity"] == "high"]) * 0.5)

            return CodeAnalysisResult(
                analysis_type=CodeAnalysisType.SECURITY_ANALYSIS,
                language=code_context.language,
                file_path=code_context.file_path,
                findings=findings,
                suggestions=suggestions,
                score=score,
                confidence=0.8
            )

        except Exception as e:
            self.logger.error(f"Error in security analysis: {e}")
            raise

    async def _refactoring_analysis(self, code_context: CodeContext, context: Optional[Dict[str, Any]] = None) -> CodeAnalysisResult:
        """Perform refactoring analysis."""
        try:
            findings = []
            suggestions = []

            # Search for refactoring patterns
            query = f"code refactoring patterns {code_context.language.value}"
            search_results = await self.rag_system.search(query, top_k=3)

            # Analyze code for refactoring opportunities
            refactoring_opportunities = self._detect_refactoring_opportunities(code_context)
            findings.extend(refactoring_opportunities)

            # Generate refactoring suggestions
            for result in search_results:
                suggestions.append({
                    "type": "refactoring",
                    "suggestion": f"Refactoring idea: {result.chunk.content[:200]}...",
                    "source": result.document.source_path,
                    "confidence": result.score
                })

            # Calculate score
            score = max(0, 1.0 - len(findings) * 0.1)

            return CodeAnalysisResult(
                analysis_type=CodeAnalysisType.REFACTORING_SUGGESTIONS,
                language=code_context.language,
                file_path=code_context.file_path,
                findings=findings,
                suggestions=suggestions,
                score=score,
                confidence=0.7
            )

        except Exception as e:
            self.logger.error(f"Error in refactoring analysis: {e}")
            raise

    async def _documentation_analysis(self, code_context: CodeContext, context: Optional[Dict[str, Any]] = None) -> CodeAnalysisResult:
        """Perform documentation analysis."""
        try:
            findings = []
            suggestions = []

            # Analyze documentation coverage
            doc_coverage = self._analyze_documentation_coverage(code_context)

            if doc_coverage["functions_without_docs"] > 0:
                findings.append({
                    "type": "documentation",
                    "severity": "low",
                    "message": f"{doc_coverage['functions_without_docs']} functions lack documentation",
                    "suggestion": "Add docstrings to functions"
                })

            if doc_coverage["classes_without_docs"] > 0:
                findings.append({
                    "type": "documentation",
                    "severity": "low",
                    "message": f"{doc_coverage['classes_without_docs']} classes lack documentation",
                    "suggestion": "Add docstrings to classes"
                })

            # Generate documentation suggestions
            suggestions.append({
                "type": "documentation",
                "suggestion": "Consider adding type hints for better code documentation",
                "confidence": 0.8
            })

            # Calculate score
            total_functions = doc_coverage["total_functions"]
            total_classes = doc_coverage["total_classes"]
            documented_functions = doc_coverage["functions_with_docs"]
            documented_classes = doc_coverage["classes_with_docs"]

            if total_functions + total_classes > 0:
                coverage = (documented_functions + documented_classes) / (total_functions + total_classes)
                score = coverage
            else:
                score = 0.5

            return CodeAnalysisResult(
                analysis_type=CodeAnalysisType.DOCUMENTATION_GENERATION,
                language=code_context.language,
                file_path=code_context.file_path,
                findings=findings,
                suggestions=suggestions,
                score=score,
                confidence=0.9
            )

        except Exception as e:
            self.logger.error(f"Error in documentation analysis: {e}")
            raise

    async def _code_completion_analysis(self, code_context: CodeContext, context: Optional[Dict[str, Any]] = None) -> CodeAnalysisResult:
        """Perform code completion analysis."""
        try:
            suggestions = []

            # Search for code completion patterns
            query = f"code completion patterns {code_context.language.value}"
            search_results = await self.rag_system.search(query, top_k=2)

            # Analyze code context for completion suggestions
            completion_suggestions = self._generate_completion_suggestions(code_context, context)
            suggestions.extend(completion_suggestions)

            # Add search-based suggestions
            for result in search_results:
                suggestions.append({
                    "type": "completion",
                    "suggestion": f"Pattern: {result.chunk.content[:150]}...",
                    "source": result.document.source_path,
                    "confidence": result.score
                })

            return CodeAnalysisResult(
                analysis_type=CodeAnalysisType.CODE_COMPLETION,
                language=code_context.language,
                file_path=code_context.file_path,
                findings=[],  # No findings for completion
                suggestions=suggestions,
                score=0.8,  # Always positive for completion
                confidence=0.7
            )

        except Exception as e:
            self.logger.error(f"Error in code completion analysis: {e}")
            raise

    async def _code_explanation_analysis(self, code_context: CodeContext, context: Optional[Dict[str, Any]] = None) -> CodeAnalysisResult:
        """Perform code explanation analysis."""
        try:
            explanations = []

            # Search for similar code explanations
            query = f"explain {code_context.language.value} code patterns"
            search_results = await self.rag_system.search(query, top_k=3)

            # Generate code explanations
            for function_name in code_context.functions[:3]:  # Explain first 3 functions
                explanation = await self._explain_function(function_name, code_context, search_results)
                if explanation:
                    explanations.append(explanation)

            # Format as suggestions
            suggestions = [
                {
                    "type": "explanation",
                    "suggestion": explanation,
                    "confidence": 0.8
                }
                for explanation in explanations
            ]

            return CodeAnalysisResult(
                analysis_type=CodeAnalysisType.CODE_EXPLANATION,
                language=code_context.language,
                file_path=code_context.file_path,
                findings=[],  # No findings for explanation
                suggestions=suggestions,
                score=0.9,  # Always positive for explanation
                confidence=0.8
            )

        except Exception as e:
            self.logger.error(f"Error in code explanation analysis: {e}")
            raise

    def _detect_python_bugs(self, code_context: CodeContext) -> List[Dict[str, Any]]:
        """Detect common Python bugs."""
        findings = []

        # Check for division by zero
        if " / 0" in code_context.code or " /0" in code_context.code:
            findings.append({
                "type": "bug",
                "severity": "high",
                "message": "Potential division by zero",
                "line": code_context.code.find(" / 0") if " / 0" in code_context.code else code_context.code.find(" /0")
            })

        # Check for mutable default arguments
        if "=[]" in code_context.code and "def " in code_context.code:
            # Simple check for mutable defaults
            findings.append({
                "type": "bug",
                "severity": "medium",
                "message": "Mutable default argument detected, use None instead",
                "line": code_context.code.find("=[]")
            })

        return findings

    def _detect_javascript_bugs(self, code_context: CodeContext) -> List[Dict[str, Any]]:
        """Detect common JavaScript bugs."""
        findings = []

        # Check for async/await without try/catch
        if "await " in code_context.code and "try " not in code_context.code:
            findings.append({
                "type": "bug",
                "severity": "medium",
                "message": "Await without try/catch may cause unhandled rejections",
                "line": code_context.code.find("await ")
            })

        return findings

    def _detect_python_performance_issues(self, code_context: CodeContext) -> List[Dict[str, Any]]:
        """Detect Python performance issues."""
        findings = []

        # Check for string concatenation in loops
        lines = code_context.code.split('\n')
        for i, line in enumerate(lines):
            if "for " in line and (" += " in line or " + " in line):
                findings.append({
                    "type": "performance",
                    "severity": "medium",
                    "message": "String concatenation in loop, consider using list and join",
                    "line": i + 1
                })

        return findings

    def _detect_security_issues(self, code_context: CodeContext) -> List[Dict[str, Any]]:
        """Detect security issues."""
        findings = []

        # Check for hardcoded secrets
        secret_patterns = [
            r'password\s*=\s*["\'][^"\']+["\']',
            r'api_key\s*=\s*["\'][^"\']+["\']',
            r'secret\s*=\s*["\'][^"\']+["\']'
        ]

        for pattern in secret_patterns:
            matches = re.finditer(pattern, code_context.code)
            for match in matches:
                findings.append({
                    "type": "security",
                    "severity": "high",
                    "message": "Hardcoded secret detected",
                    "line": code_context.code[:match.start()].count('\n') + 1
                })

        return findings

    def _detect_refactoring_opportunities(self, code_context: CodeContext) -> List[Dict[str, Any]]:
        """Detect refactoring opportunities."""
        findings = []

        # Check for duplicate code
        lines = code_context.code.split('\n')
        line_counts = {}
        for line in lines:
            if line.strip() and len(line.strip()) > 10:  # Ignore short lines
                line_counts[line] = line_counts.get(line, 0) + 1

        for line, count in line_counts.items():
            if count > 2:
                findings.append({
                    "type": "refactoring",
                    "severity": "low",
                    "message": f"Duplicate code detected ({count} occurrences)",
                    "suggestion": "Extract to function"
                })

        return findings

    def _analyze_documentation_coverage(self, code_context: CodeContext) -> Dict[str, int]:
        """Analyze documentation coverage."""
        lines = code_context.code.split('\n')

        total_functions = len(code_context.functions)
        functions_with_docs = 0

        total_classes = len(code_context.classes)
        classes_with_docs = 0

        # Check for docstrings
        for i, line in enumerate(lines):
            if '"""' in line or "'''" in line:
                # Found docstring, check if it's after function/class definition
                if i > 0:
                    prev_line = lines[i-1]
                    if 'def ' in prev_line:
                        functions_with_docs += 1
                    elif 'class ' in prev_line:
                        classes_with_docs += 1

        return {
            "total_functions": total_functions,
            "functions_with_docs": functions_with_docs,
            "functions_without_docs": total_functions - functions_with_docs,
            "total_classes": total_classes,
            "classes_with_docs": classes_with_docs,
            "classes_without_docs": total_classes - classes_with_docs
        }

    def _generate_completion_suggestions(self, code_context: CodeContext, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Generate code completion suggestions."""
        suggestions = []

        # Analyze last few lines to determine context
        lines = code_context.code.split('\n')
        last_lines = lines[-3:] if len(lines) >= 3 else lines

        # Simple completion suggestions based on context
        for line in last_lines:
            if 'import ' in line:
                suggestions.append({
                    "type": "completion",
                    "suggestion": "Consider adding commonly used imports",
                    "confidence": 0.6
                })
            elif 'def ' in line and ':' not in line:
                suggestions.append({
                    "type": "completion",
                    "suggestion": "Add function signature and docstring",
                    "confidence": 0.8
                })

        return suggestions

    async def _explain_function(self, function_name: str, code_context: CodeContext,
                              search_results: List[Any]) -> Optional[str]:
        """Explain a function."""
        try:
            # Find function in code
            function_pattern = rf'def {function_name}\s*\([^)]*\):'
            match = re.search(function_pattern, code_context.code)

            if not match:
                return None

            # Extract function content
            start_pos = match.start()
            end_pos = self._find_function_end(code_context.code, start_pos)

            if end_pos == -1:
                return None

            function_code = code_context.code[start_pos:end_pos]

            # Generate explanation
            explanation = f"Function `{function_name}`:\n"
            explanation += f"- Purpose: Extract parameters and logic from function signature\n"
            explanation += f"- Length: {function_code.count('\n')} lines\n"

            # Add insights from search results
            if search_results:
                explanation += "- Similar patterns found in codebase\n"

            return explanation

        except Exception as e:
            self.logger.error(f"Error explaining function {function_name}: {e}")
            return None

    def _find_function_end(self, code: str, start_pos: int) -> int:
        """Find the end of a function."""
        lines = code[start_pos:].split('\n')
        current_indent = len(lines[0]) - len(lines[0].lstrip())

        for i, line in enumerate(lines[1:], 1):
            if line.strip() and len(line) - len(line.lstrip()) <= current_indent:
                return start_pos + sum(len(lines[j]) + 1 for j in range(i))

        return len(code)

    def _get_function_pattern(self, language: CodeLanguage) -> str:
        """Get function pattern for language."""
        patterns = {
            CodeLanguage.PYTHON: r'def\s+\w+\s*\([^)]*\):',
            CodeLanguage.JAVASCRIPT: r'function\s+\w+\s*\([^)]*\)|\w+\s*=\s*function\s*\([^)]*\)|\w+\s*\([^)]*\)\s*=>',
            CodeLanguage.JAVA: r'(public|private|protected)?\s*(static)?\s*\w+\s+\w+\s*\([^)]*\)\s*\{',
            CodeLanguage.CPP: r'\w+\s+\w+\s*\([^)]*\)\s*\{',
            CodeLanguage.GO: r'func\s+\w+\s*\([^)]*\)\s*\{'
        }

        return patterns.get(language, r'\w+\s*\([^)]*\)')

    async def _read_code_file(self, file_path: Path) -> str:
        """Read code file content."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            self.logger.error(f"Error reading code file {file_path}: {e}")
            raise

    async def _parse_code_context(self, file_path: Path, code_content: str) -> CodeContext:
        """Parse code context information."""
        try:
            # Determine language from file extension
            extension = file_path.suffix.lower()
            language_map = {
                '.py': CodeLanguage.PYTHON,
                '.js': CodeLanguage.JAVASCRIPT,
                '.ts': CodeLanguage.TYPESCRIPT,
                '.java': CodeLanguage.JAVA,
                '.cpp': CodeLanguage.CPP,
                '.c': CodeLanguage.CPP,
                '.go': CodeLanguage.GO,
                '.html': CodeLanguage.HTML,
                '.css': CodeLanguage.CSS,
                '.sql': CodeLanguage.SQL,
                '.sh': CodeLanguage.BASH,
                '.ps1': CodeLanguage.POWERSHELL
            }

            language = language_map.get(extension, CodeLanguage.PYTHON)

            # Extract basic code structure
            imports = []
            functions = []
            classes = []

            lines = code_content.split('\n')
            for line in lines:
                # Extract imports
                if language == CodeLanguage.PYTHON and line.strip().startswith('import '):
                    imports.append(line.strip())
                elif language == CodeLanguage.JAVASCRIPT and line.strip().startswith('import '):
                    imports.append(line.strip())

                # Extract functions
                if language == CodeLanguage.PYTHON and line.strip().startswith('def '):
                    functions.append(line.strip()[4:].split('(')[0].strip())
                elif language == CodeLanguage.JAVASCRIPT and 'function ' in line:
                    functions.append(line.strip().split('function ')[1].split('(')[0].strip())

                # Extract classes
                if language == CodeLanguage.PYTHON and line.strip().startswith('class '):
                    classes.append(line.strip()[6:].split('(')[0].strip().split(':')[0].strip())

            return CodeContext(
                file_path=str(file_path),
                language=language,
                code=code_content,
                imports=imports,
                functions=functions,
                classes=classes
            )

        except Exception as e:
            self.logger.error(f"Error parsing code context: {e}")
            raise

    async def _add_code_to_rag(self, file_path: Path, code_content: str, code_context: CodeContext):
        """Add code to RAG system."""
        try:
            # Add as code document
            await self.rag_system.add_text(
                code_content,
                doc_type=DocumentType.CODE,
                metadata={
                    "file_path": str(file_path),
                    "language": code_context.language.value,
                    "functions": code_context.functions,
                    "classes": code_context.classes,
                    "imports": code_context.imports
                }
            )

        except Exception as e:
            self.logger.error(f"Error adding code to RAG: {e}")

    def _get_analysis_cache_key(self, file_path: Path, analysis_types: List[CodeAnalysisType]) -> str:
        """Get cache key for analysis."""
        file_mtime = Path(file_path).stat().st_mtime
        types_str = "_".join(sorted(at.value for at in analysis_types))
        return f"{file_path}_{file_mtime}_{types_str}"

    async def _learn_from_feedback(self):
        """Learn from feedback data."""
        try:
            if not self.feedback_data:
                return

            # Analyze feedback patterns
            feedback_patterns = {}
            for feedback in self.feedback_data:
                analysis_type = feedback.get("analysis_type")
                if analysis_type:
                    if analysis_type not in feedback_patterns:
                        feedback_patterns[analysis_type] = []
                    feedback_patterns[analysis_type].append(feedback)

            # Update analysis patterns based on feedback
            for analysis_type, patterns in feedback_patterns.items():
                # This is a simplified learning process
                # In a real implementation, you'd use machine learning
                avg_score = sum(p.get("score", 0) for p in patterns) / len(patterns)

                if avg_score < 0.5:
                    self.logger.warning(f"Low satisfaction score for {analysis_type}: {avg_score:.2f}")

        except Exception as e:
            self.logger.error(f"Error learning from feedback: {e}")

    async def add_feedback(self, analysis_type: str, file_path: str, score: float, feedback: str):
        """Add feedback for analysis."""
        try:
            feedback_entry = {
                "analysis_type": analysis_type,
                "file_path": file_path,
                "score": score,
                "feedback": feedback,
                "timestamp": datetime.now().isoformat()
            }

            self.feedback_data.append(feedback_entry)

            # Save feedback
            with open(self.config.feedback_file, 'w') as f:
                json.dump(self.feedback_data, f, indent=2)

            self.logger.info(f"Added feedback for {analysis_type} on {file_path}")

        except Exception as e:
            self.logger.error(f"Error adding feedback: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get DeepCode integration statistics."""
        try:
            return {
                "analyses_performed": len(self.analysis_cache),
                "feedback_entries": len(self.feedback_data),
                "supported_languages": [lang.value for lang in self.config.supported_languages],
                "enabled_analyses": [analysis.value for analysis in self.config.enabled_analyses],
                "knowledge_base": {
                    "code_patterns": len(self.code_patterns),
                    "best_practices": len(self.best_practices),
                    "security_patterns": len(self.security_patterns)
                },
                "config": {
                    "max_file_size": self.config.max_file_size,
                    "enable_parallel_analysis": self.config.enable_parallel_analysis,
                    "enable_learning": self.config.enable_learning
                }
            }

        except Exception as e:
            self.logger.error(f"Error getting DeepCode stats: {e}")
            return {}

    async def close(self):
        """Clean up resources."""
        try:
            # Cancel background tasks
            if self._learning_task:
                self._learning_task.cancel()

            # Save feedback data
            with open(self.config.feedback_file, 'w') as f:
                json.dump(self.feedback_data, f, indent=2)

            self.logger.info("RAG-DeepCode Integration closed")

        except Exception as e:
            self.logger.error(f"Error closing DeepCode integration: {e}")


# Global instance
_rag_deepcode_integration: Optional[RAGDeepCodeIntegration] = None


def get_rag_deepcode_integration(rag_system: EnhancedRAG,
                                config: Optional[RAGDeepCodeConfig] = None) -> RAGDeepCodeIntegration:
    """Get or create the global RAG-DeepCode integration instance."""
    global _rag_deepcode_integration

    if _rag_deepcode_integration is None:
        _rag_deepcode_integration = RAGDeepCodeIntegration(rag_system, config)

    return _rag_deepcode_integration