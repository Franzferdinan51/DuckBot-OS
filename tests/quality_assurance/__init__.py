"""
Quality Assurance Tools for DuckBot v4.2

This package provides comprehensive quality assurance tools:
- Code quality analysis and linting
- Security vulnerability scanning
- Performance profiling and optimization
- Documentation coverage testing
- Compliance validation testing
- Code smell detection
- Technical debt analysis
"""

import ast
import subprocess
import json
import sys
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import re

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

@dataclass
class QualityIssue:
    """Quality issue data class"""
    type: str  # 'security', 'performance', 'style', 'documentation', 'complexity'
    severity: str  # 'critical', 'high', 'medium', 'low'
    file_path: str
    line_number: int
    message: str
    rule_id: str
    suggestion: Optional[str] = None

class CodeQualityAnalyzer:
    """Comprehensive code quality analysis"""

    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.issues: List[QualityIssue] = []
        self.metrics: Dict[str, Any] = {}

    def analyze_codebase(self) -> Dict[str, Any]:
        """Perform comprehensive codebase analysis"""
        print("🔍 Starting comprehensive code quality analysis...")

        # Static code analysis
        self._run_static_analysis()

        # Security scanning
        self._run_security_scan()

        # Performance analysis
        self._run_performance_analysis()

        # Documentation analysis
        self._run_documentation_analysis()

        # Code complexity analysis
        self._run_complexity_analysis()

        # Generate quality metrics
        self._calculate_quality_metrics()

        return self._generate_report()

    def _run_static_analysis(self):
        """Run static code analysis tools"""
        print("  📝 Running static code analysis...")

        # Run flake8 for style checking
        try:
            result = subprocess.run(
                ["flake8", "duckbot/", "tests/", "--max-line-length=100", "--exclude=__pycache__"],
                capture_output=True, text=True, cwd=self.project_root
            )

            if result.stdout:
                self._parse_flake8_output(result.stdout)

        except FileNotFoundError:
            print("  ⚠️  flake8 not found, skipping style checking")

        # Run black for formatting check
        try:
            result = subprocess.run(
                ["black", "--check", "duckbot/", "tests/"],
                capture_output=True, text=True, cwd=self.project_root
            )

            if result.returncode != 0:
                self.issues.append(QualityIssue(
                    type="style",
                    severity="medium",
                    file_path="multiple",
                    line_number=0,
                    message="Code formatting issues found. Run 'black duckbot/ tests/' to fix.",
                    rule_id="BLACK001"
                ))

        except FileNotFoundError:
            print("  ⚠️  black not found, skipping formatting check")

        # Run mypy for type checking
        try:
            result = subprocess.run(
                ["mypy", "duckbot/", "--ignore-missing-imports"],
                capture_output=True, text=True, cwd=self.project_root
            )

            if result.stdout:
                self._parse_mypy_output(result.stdout)

        except FileNotFoundError:
            print("  ⚠️  mypy not found, skipping type checking")

    def _run_security_scan(self):
        """Run security vulnerability scanning"""
        print("  🔒 Running security scan...")

        # Run bandit for security issues
        try:
            result = subprocess.run(
                ["bandit", "-r", "duckbot/", "-f", "json"],
                capture_output=True, text=True, cwd=self.project_root
            )

            if result.stdout:
                try:
                    bandit_results = json.loads(result.stdout)
                    self._parse_bandit_results(bandit_results)
                except json.JSONDecodeError:
                    print("  ⚠️  Could not parse bandit JSON output")

        except FileNotFoundError:
            print("  ⚠️  bandit not found, skipping security scan")

        # Run safety for dependency vulnerabilities
        try:
            result = subprocess.run(
                ["safety", "check", "--json"],
                capture_output=True, text=True, cwd=self.project_root
            )

            if result.stdout:
                try:
                    safety_results = json.loads(result.stdout)
                    self._parse_safety_results(safety_results)
                except json.JSONDecodeError:
                    print("  ⚠️  Could not parse safety JSON output")

        except FileNotFoundError:
            print("  ⚠️  safety not found, skipping dependency scan")

    def _run_performance_analysis(self):
        """Run performance analysis"""
        print("  ⚡ Running performance analysis...")

        # Analyze Python files for performance issues
        python_files = list(self.project_root.glob("duckbot/**/*.py"))
        python_files.extend(list(self.project_root.glob("tests/**/*.py")))

        for file_path in python_files:
            if file_path.is_file():
                self._analyze_file_performance(file_path)

    def _run_documentation_analysis(self):
        """Run documentation coverage analysis"""
        print("  📚 Running documentation analysis...")

        # Check docstring coverage
        python_files = list(self.project_root.glob("duckbot/**/*.py"))
        documented_functions = 0
        total_functions = 0

        for file_path in python_files:
            if file_path.is_file():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        tree = ast.parse(content)

                        for node in ast.walk(tree):
                            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                                total_functions += 1
                                if ast.get_docstring(node):
                                    documented_functions += 1

                except Exception as e:
                    print(f"  ⚠️  Error analyzing {file_path}: {e}")

        if total_functions > 0:
            docstring_coverage = (documented_functions / total_functions) * 100
            self.metrics["docstring_coverage"] = docstring_coverage

            if docstring_coverage < 70:
                self.issues.append(QualityIssue(
                    type="documentation",
                    severity="medium",
                    file_path="codebase",
                    line_number=0,
                    message=f"Low docstring coverage: {docstring_coverage:.1f}% ({documented_functions}/{total_functions} functions)",
                    rule_id="DOC001"
                ))

    def _run_complexity_analysis(self):
        """Run code complexity analysis"""
        print("  🧩 Running complexity analysis...")

        python_files = list(self.project_root.glob("duckbot/**/*.py"))

        for file_path in python_files:
            if file_path.is_file():
                self._analyze_file_complexity(file_path)

    def _analyze_file_performance(self, file_path: Path):
        """Analyze performance issues in a single file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')

            for i, line in enumerate(lines, 1):
                # Check for performance anti-patterns
                issues = self._check_performance_antipatterns(line, file_path, i)
                self.issues.extend(issues)

        except Exception as e:
            print(f"  ⚠️  Error analyzing performance in {file_path}: {e}")

    def _check_performance_antipatterns(self, line: str, file_path: Path, line_number: int) -> List[QualityIssue]:
        """Check for performance anti-patterns in a line of code"""
        issues = []

        # Check for string concatenation in loops
        if re.search(r'\+\s*\w.*\+.*\bfor\b', line):
            issues.append(QualityIssue(
                type="performance",
                severity="medium",
                file_path=str(file_path),
                line_number=line_number,
                message="String concatenation in loop detected. Consider using list join or f-strings.",
                rule_id="PERF001"
            ))

        # Check for global variable usage
        if re.search(r'^\s*global\s+', line):
            issues.append(QualityIssue(
                type="performance",
                severity="low",
                file_path=str(file_path),
                line_number=line_number,
                message="Global variable usage detected. Consider using class attributes or dependency injection.",
                rule_id="PERF002"
            ))

        # Check for inefficient list operations
        if re.search(r'\.append\(\)', line) and 'for' in line:
            issues.append(QualityIssue(
                type="performance",
                severity="low",
                file_path=str(file_path),
                line_number=line_number,
                message="List append in loop detected. Consider list comprehensions for better performance.",
                rule_id="PERF003"
            ))

        return issues

    def _analyze_file_complexity(self, file_path: Path):
        """Analyze code complexity in a single file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    complexity = self._calculate_cyclomatic_complexity(node)
                    if complexity > 10:
                        self.issues.append(QualityIssue(
                            type="complexity",
                            severity="high" if complexity > 20 else "medium",
                            file_path=str(file_path),
                            line_number=node.lineno,
                            message=f"Function '{node.name}' has high cyclomatic complexity: {complexity}",
                            rule_id="CX001"
                        ))

        except Exception as e:
            print(f"  ⚠️  Error analyzing complexity in {file_path}: {e}")

    def _calculate_cyclomatic_complexity(self, node: ast.AST) -> int:
        """Calculate cyclomatic complexity for a function"""
        complexity = 1  # Base complexity

        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, (ast.And, ast.Or)):
                complexity += 1

        return complexity

    def _parse_flake8_output(self, output: str):
        """Parse flake8 output and create issues"""
        for line in output.split('\n'):
            if line.strip():
                # Parse flake8 output: filename:line:column: code message
                match = re.match(r'([^:]+):(\d+):(\d+):\s+(\w+)\s+(.*)', line)
                if match:
                    file_path, line_num, col_num, code, message = match.groups()
                    severity = "low" if code.startswith('W') else "medium"

                    self.issues.append(QualityIssue(
                        type="style",
                        severity=severity,
                        file_path=file_path,
                        line_number=int(line_num),
                        message=message,
                        rule_id=code
                    ))

    def _parse_mypy_output(self, output: str):
        """Parse mypy output and create issues"""
        for line in output.split('\n'):
            if line.strip() and 'error:' in line.lower():
                # Parse mypy output: filename:line: error: message
                match = re.match(r'([^:]+):(\d+):\s+error:\s+(.*)', line)
                if match:
                    file_path, line_num, message = match.groups()
                    self.issues.append(QualityIssue(
                        type="style",
                        severity="medium",
                        file_path=file_path,
                        line_number=int(line_num),
                        message=message,
                        rule_id="MYPY001"
                    ))

    def _parse_bandit_results(self, results: Dict[str, Any]):
        """Parse bandit security results"""
        for issue in results.get('results', []):
            severity_map = {
                'HIGH': 'critical',
                'MEDIUM': 'high',
                'LOW': 'medium'
            }

            self.issues.append(QualityIssue(
                type="security",
                severity=severity_map.get(issue.get('severity', 'LOW'), 'medium'),
                file_path=issue.get('filename', 'unknown'),
                line_number=issue.get('line_number', 0),
                message=issue.get('issue_text', 'Unknown security issue'),
                rule_id=issue.get('test_id', 'BANDIT001'),
                suggestion=issue.get('issue_cwe', {}).get('link')
            ))

    def _parse_safety_results(self, results: Dict[str, Any]):
        """Parse safety dependency results"""
        for vuln in results:
            self.issues.append(QualityIssue(
                type="security",
                severity="high" if vuln.get('advisory', '').lower() == 'critical' else 'medium',
                file_path="dependencies",
                line_number=0,
                message=f"Vulnerable dependency: {vuln.get('package', 'unknown')} {vuln.get('installed_version', 'unknown')}",
                rule_id="SAFETY001",
                suggestion=vuln.get('advisory')
            ))

    def _calculate_quality_metrics(self):
        """Calculate overall quality metrics"""
        total_issues = len(self.issues)
        critical_issues = len([i for i in self.issues if i.severity == 'critical'])
        high_issues = len([i for i in self.issues if i.severity == 'high'])

        # Count lines of code
        total_lines = 0
        python_files = list(self.project_root.glob("duckbot/**/*.py"))
        for file_path in python_files:
            if file_path.is_file():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        total_lines += len(f.readlines())
                except Exception:
                    pass

        self.metrics.update({
            "total_issues": total_issues,
            "critical_issues": critical_issues,
            "high_issues": high_issues,
            "issues_per_1000_lines": (total_issues / max(total_lines, 1)) * 1000,
            "critical_issue_ratio": critical_issues / max(total_issues, 1),
            "total_lines_of_code": total_lines,
            "technical_debt_score": self._calculate_technical_debt_score()
        })

    def _calculate_technical_debt_score(self) -> float:
        """Calculate technical debt score (0-100, higher is worse)"""
        weights = {
            'critical': 10,
            'high': 5,
            'medium': 2,
            'low': 1
        }

        weighted_score = sum(
            weights.get(issue.severity, 1) for issue in self.issues
        )

        # Normalize to 0-100 scale
        max_possible_score = len(self.issues) * 10
        return min(100, (weighted_score / max(max_possible_score, 1)) * 100)

    def _generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive quality report"""
        # Group issues by type and severity
        issues_by_type = {}
        issues_by_severity = {}

        for issue in self.issues:
            # Group by type
            if issue.type not in issues_by_type:
                issues_by_type[issue.type] = []
            issues_by_type[issue.type].append(issue)

            # Group by severity
            if issue.severity not in issues_by_severity:
                issues_by_severity[issue.severity] = []
            issues_by_severity[issue.severity].append(issue)

        # Calculate quality score
        quality_score = max(0, 100 - self.metrics.get("technical_debt_score", 0))

        return {
            "analysis_timestamp": datetime.now().isoformat(),
            "quality_score": quality_score,
            "grade": self._get_quality_grade(quality_score),
            "summary": {
                "total_issues": self.metrics.get("total_issues", 0),
                "critical_issues": self.metrics.get("critical_issues", 0),
                "high_issues": self.metrics.get("high_issues", 0),
                "lines_of_code": self.metrics.get("total_lines_of_code", 0),
                "docstring_coverage": self.metrics.get("docstring_coverage", 0)
            },
            "issues_by_type": {k: len(v) for k, v in issues_by_type.items()},
            "issues_by_severity": {k: len(v) for k, v in issues_by_severity.items()},
            "top_issues": self._get_top_issues(issues_by_type),
            "recommendations": self._generate_recommendations(),
            "metrics": self.metrics
        }

    def _get_quality_grade(self, score: float) -> str:
        """Get quality grade based on score"""
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"

    def _get_top_issues(self, issues_by_type: Dict[str, List[QualityIssue]]) -> List[Dict[str, Any]]:
        """Get top issues by type"""
        top_issues = []

        for issue_type, issues in issues_by_type.items():
            if issues:
                # Get most severe issue of this type
                severity_priority = {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}
                most_severe = max(issues, key=lambda x: severity_priority.get(x.severity, 0))

                top_issues.append({
                    "type": issue_type,
                    "severity": most_severe.severity,
                    "message": most_severe.message,
                    "file": most_severe.file_path,
                    "count": len(issues)
                })

        return top_issues

    def _generate_recommendations(self) -> List[Dict[str, Any]]:
        """Generate improvement recommendations"""
        recommendations = []

        # Check issue density
        issues_per_kloc = self.metrics.get("issues_per_1000_lines", 0)
        if issues_per_kloc > 50:
            recommendations.append({
                "priority": "high",
                "category": "general",
                "message": f"High issue density ({issues_per_kloc:.1f} issues per KLOC). Consider comprehensive code review.",
                "estimated_effort": "high"
            })

        # Check critical issues
        critical_count = self.metrics.get("critical_issues", 0)
        if critical_count > 0:
            recommendations.append({
                "priority": "critical",
                "category": "security",
                "message": f"{critical_count} critical security issues found. Address immediately.",
                "estimated_effort": "medium"
            })

        # Check documentation
        doc_coverage = self.metrics.get("docstring_coverage", 0)
        if doc_coverage < 50:
            recommendations.append({
                "priority": "medium",
                "category": "documentation",
                "message": f"Low documentation coverage ({doc_coverage:.1f}%). Add docstrings to public functions.",
                "estimated_effort": "low"
            })

        # Check technical debt
        tech_debt_score = self.metrics.get("technical_debt_score", 0)
        if tech_debt_score > 30:
            recommendations.append({
                "priority": "medium",
                "category": "refactoring",
                "message": f"High technical debt score ({tech_debt_score:.1f}/100). Plan refactoring sprints.",
                "estimated_effort": "high"
            })

        return recommendations

# Export utilities
__all__ = [
    "CodeQualityAnalyzer",
    "QualityIssue"
]