#!/usr/bin/env python3
"""
Generate comprehensive test summary report from CI/CD pipeline results
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
import yaml

class TestSummaryGenerator:
    """Generate comprehensive test summary reports"""

    def __init__(self, results_dir: str = "."):
        self.results_dir = Path(results_dir)
        self.test_results = {}
        self.summary_data = {
            "generated_at": datetime.now().isoformat(),
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "skipped_tests": 0,
            "coverage": {},
            "performance": {},
            "security": {},
            "categories": {},
            "recommendations": []
        }

    def collect_results(self):
        """Collect test results from various sources"""
        print("Collecting test results...")

        # Collect unit test results
        self._collect_unit_test_results()

        # Collect integration test results
        self._collect_integration_test_results()

        # Collect performance test results
        self._collect_performance_results()

        # Collect security test results
        self._collect_security_results()

        # Collect code quality results
        self._collect_code_quality_results()

    def _collect_unit_test_results(self):
        """Collect unit test results from coverage reports"""
        coverage_files = [
            "coverage.xml",
            "coverage-reports-*/coverage.xml",
            "htmlcov/index.html"
        ]

        for pattern in coverage_files:
            for file_path in self.results_dir.glob(pattern):
                if file_path.exists():
                    try:
                        if file_path.suffix == '.xml':
                            self._parse_coverage_xml(file_path)
                        elif file_path.name == 'index.html':
                            self._parse_coverage_html(file_path.parent)
                    except Exception as e:
                        print(f"Warning: Could not parse {file_path}: {e}")

    def _collect_integration_test_results(self):
        """Collect integration test results"""
        integration_dirs = [
            "integration-test-results",
            "test-results/integration"
        ]

        for dir_name in integration_dirs:
            dir_path = self.results_dir / dir_name
            if dir_path.exists():
                self._scan_test_results_dir(dir_path, "integration")

    def _collect_performance_results(self):
        """Collect performance test results"""
        performance_files = [
            "performance-results/load-test-results_stats.csv",
            "performance-results/benchmark-results.json",
            "locust-report.html"
        ]

        for file_pattern in performance_files:
            for file_path in self.results_dir.glob(file_pattern):
                if file_path.exists():
                    try:
                        if file_path.suffix == '.json':
                            with open(file_path, 'r') as f:
                                data = json.load(f)
                                self.summary_data["performance"][file_path.stem] = data
                        elif file_path.suffix == '.csv':
                            self._parse_locust_csv(file_path)
                    except Exception as e:
                        print(f"Warning: Could not parse {file_path}: {e}")

    def _collect_security_results(self):
        """Collect security test results"""
        security_files = [
            "security-test-results/bandit-report.json",
            "security-test-results/safety-report.json",
            "security-test-results/trufflehog-results.json",
            "security-test-results/semgrep-results.json"
        ]

        for file_pattern in security_files:
            for file_path in self.results_dir.glob(file_pattern):
                if file_path.exists():
                    try:
                        with open(file_path, 'r') as f:
                            data = json.load(f)
                            tool_name = file_path.stem.replace('-report', '').replace('-results', '')
                            self.summary_data["security"][tool_name] = data
                    except Exception as e:
                        print(f"Warning: Could not parse {file_path}: {e}")

    def _collect_code_quality_results(self):
        """Collect code quality results"""
        quality_indicators = [
            "black-check.passed",
            "flake-check.passed",
            "mypy-check.passed"
        ]

        for indicator in quality_indicators:
            file_path = self.results_dir / indicator
            if file_path.exists():
                self.summary_data["code_quality"] = self.summary_data.get("code_quality", {})
                self.summary_data["code_quality"][indicator.replace(".passed", "")] = True

    def _parse_coverage_xml(self, file_path: Path):
        """Parse coverage XML report"""
        import xml.etree.ElementTree as ET

        try:
            tree = ET.parse(file_path)
            root = tree.getroot()

            coverage_data = {
                "line_rate": float(root.get('line-rate', 0)),
                "branch_rate": float(root.get('branch-rate', 0)),
                "lines_covered": int(root.get('lines-valid', 0)) - int(root.get('lines-covered', 0)),
                "lines_valid": int(root.get('lines-valid', 0)),
                "branches_covered": int(root.get('branches-covered', 0)),
                "branches_valid": int(root.get('branches-valid', 0))
            }

            coverage_percentage = coverage_data["line_rate"] * 100
            self.summary_data["coverage"] = {
                "percentage": coverage_percentage,
                "lines_covered": coverage_data["lines_covered"],
                "lines_valid": coverage_data["lines_valid"],
                "status": "good" if coverage_percentage >= 80 else "warning" if coverage_percentage >= 60 else "poor"
            }

        except Exception as e:
            print(f"Error parsing coverage XML: {e}")

    def _parse_coverage_html(self, html_dir: Path):
        """Parse coverage HTML report (fallback)"""
        # Simple parsing of HTML coverage report
        index_file = html_dir / "index.html"
        if index_file.exists():
            try:
                with open(index_file, 'r') as f:
                    content = f.read()
                    # Look for coverage percentage in HTML
                    import re
                    coverage_match = re.search(r'(\d+(?:\.\d+)?)%', content)
                    if coverage_match:
                        coverage_percentage = float(coverage_match.group(1))
                        self.summary_data["coverage"] = {
                            "percentage": coverage_percentage,
                            "status": "good" if coverage_percentage >= 80 else "warning" if coverage_percentage >= 60 else "poor"
                        }
            except Exception as e:
                print(f"Error parsing coverage HTML: {e}")

    def _parse_locust_csv(self, file_path: Path):
        """Parse Locust CSV results"""
        try:
            import pandas as pd

            df = pd.read_csv(file_path)
            if not df.empty:
                stats = {
                    "total_requests": len(df),
                    "avg_response_time": df['Request Count'].mean() if 'Request Count' in df.columns else 0,
                    "max_response_time": df['Request Count'].max() if 'Request Count' in df.columns else 0,
                    "failures": df['Failure Count'].sum() if 'Failure Count' in df.columns else 0,
                    "failure_rate": (df['Failure Count'].sum() / len(df)) * 100 if 'Failure Count' in df.columns else 0
                }
                self.summary_data["performance"]["locust"] = stats
        except ImportError:
            print("Warning: pandas not available, skipping Locust CSV parsing")
        except Exception as e:
            print(f"Error parsing Locust CSV: {e}")

    def _scan_test_results_dir(self, dir_path: Path, category: str):
        """Scan directory for test result files"""
        for file_path in dir_path.rglob("*.xml"):
            if file_path.name.startswith("test-"):
                try:
                    self._parse_junit_xml(file_path, category)
                except Exception as e:
                    print(f"Warning: Could not parse {file_path}: {e}")

    def _parse_junit_xml(self, file_path: Path, category: str):
        """Parse JUnit XML test results"""
        import xml.etree.ElementTree as ET

        try:
            tree = ET.parse(file_path)
            root = tree.getroot()

            for testsuite in root.findall('testsuite'):
                tests = int(testsuite.get('tests', 0))
                failures = int(testsuite.get('failures', 0))
                skipped = int(testsuite.get('skipped', 0))
                errors = int(testsuite.get('errors', 0))

                self.summary_data["total_tests"] += tests
                self.summary_data["failed_tests"] += failures + errors
                self.summary_data["skipped_tests"] += skipped
                self.summary_data["passed_tests"] += tests - failures - errors - skipped

                if category not in self.summary_data["categories"]:
                    self.summary_data["categories"][category] = {
                        "total": 0,
                        "passed": 0,
                        "failed": 0,
                        "skipped": 0
                    }

                self.summary_data["categories"][category]["total"] += tests
                self.summary_data["categories"][category]["passed"] += tests - failures - errors - skipped
                self.summary_data["categories"][category]["failed"] += failures + errors
                self.summary_data["categories"][category]["skipped"] += skipped

        except Exception as e:
            print(f"Error parsing JUnit XML {file_path}: {e}")

    def generate_recommendations(self):
        """Generate recommendations based on test results"""
        recommendations = []

        # Coverage recommendations
        coverage = self.summary_data.get("coverage", {})
        if coverage.get("percentage", 0) < 80:
            recommendations.append({
                "type": "coverage",
                "priority": "high",
                "message": f"Test coverage is {coverage['percentage']:.1f}%. Add more tests to reach 80% coverage."
            })

        # Security recommendations
        security = self.summary_data.get("security", {})
        if "bandit" in security:
            bandit_issues = len(security["bandit"].get("results", []))
            if bandit_issues > 0:
                recommendations.append({
                    "type": "security",
                    "priority": "high",
                    "message": f"Bandit found {bandit_issues} security issues. Review and fix security vulnerabilities."
                })

        # Performance recommendations
        performance = self.summary_data.get("performance", {})
        if "locust" in performance:
            locust_stats = performance["locust"]
            if locust_stats.get("failure_rate", 0) > 5:
                recommendations.append({
                    "type": "performance",
                    "priority": "medium",
                    "message": f"High failure rate ({locust_stats['failure_rate']:.1f}%) in load testing. Investigate performance bottlenecks."
                })

        # Test failure recommendations
        if self.summary_data["failed_tests"] > 0:
            recommendations.append({
                "type": "test_quality",
                "priority": "high",
                "message": f"{self.summary_data['failed_tests']} tests failed. Review and fix failing tests before merging."
            })

        self.summary_data["recommendations"] = recommendations

    def generate_markdown_report(self) -> str:
        """Generate Markdown test summary report"""
        report = []

        # Header
        report.append("# DuckBot v4.2 Test Summary Report")
        report.append(f"**Generated:** {self.summary_data['generated_at']}")
        report.append("")

        # Test Overview
        report.append("## 📊 Test Overview")
        report.append("| Metric | Value |")
        report.append("|--------|-------|")
        report.append(f"| Total Tests | {self.summary_data['total_tests']} |")
        report.append(f"| ✅ Passed | {self.summary_data['passed_tests']} |")
        report.append(f"| ❌ Failed | {self.summary_data['failed_tests']} |")
        report.append(f"| ⏭️ Skipped | {self.summary_data['skipped_tests']} |")

        success_rate = (self.summary_data['passed_tests'] / max(self.summary_data['total_tests'], 1)) * 100
        report.append(f"| Success Rate | {success_rate:.1f}% |")
        report.append("")

        # Coverage
        coverage = self.summary_data.get("coverage", {})
        if coverage:
            report.append("## 📈 Code Coverage")
            coverage_status = "🟢" if coverage["status"] == "good" else "🟡" if coverage["status"] == "warning" else "🔴"
            report.append(f"{coverage_status} **Coverage:** {coverage['percentage']:.1f}%")
            report.append(f"- Lines covered: {coverage['lines_covered']}/{coverage['lines_valid']}")
            report.append("")

        # Category Breakdown
        if self.summary_data["categories"]:
            report.append("## 🏷️ Test Categories")
            report.append("| Category | Total | Passed | Failed | Success Rate |")
            report.append("|----------|-------|--------|--------|--------------|")

            for category, stats in self.summary_data["categories"].items():
                category_rate = (stats["passed"] / max(stats["total"], 1)) * 100
                report.append(f"| {category.title()} | {stats['total']} | {stats['passed']} | {stats['failed']} | {category_rate:.1f}% |")
            report.append("")

        # Security Results
        security = self.summary_data.get("security", {})
        if security:
            report.append("## 🔒 Security Scan Results")
            for tool, results in security.items():
                if tool == "bandit" and "results" in results:
                    issues = len(results["results"])
                    status = "🟢" if issues == 0 else "🟡" if issues < 5 else "🔴"
                    report.append(f"{status} **Bandit:** {issues} issues found")
                elif tool == "safety":
                    vulnerabilities = len(results.get("vulnerabilities", []))
                    status = "🟢" if vulnerabilities == 0 else "🔴"
                    report.append(f"{status} **Safety:** {vulnerabilities} vulnerabilities found")
            report.append("")

        # Performance Results
        performance = self.summary_data.get("performance", {})
        if performance:
            report.append("## ⚡ Performance Results")
            if "locust" in performance:
                stats = performance["locust"]
                report.append(f"**Load Testing Results:**")
                report.append(f"- Total requests: {stats['total_requests']}")
                report.append(f"- Failure rate: {stats['failure_rate']:.1f}%")
                report.append("")

        # Recommendations
        if self.summary_data["recommendations"]:
            report.append("## 💡 Recommendations")
            for rec in self.summary_data["recommendations"]:
                priority_icon = "🔴" if rec["priority"] == "high" else "🟡" if rec["priority"] == "medium" else "🟢"
                report.append(f"{priority_icon} **{rec['type'].title()}**: {rec['message']}")
            report.append("")

        # Overall Status
        overall_status = "🟢 All Tests Passed" if self.summary_data["failed_tests"] == 0 else "🔴 Tests Failed"
        report.append(f"## 🎯 Overall Status: {overall_status}")
        report.append("")

        return "\n".join(report)

    def generate_html_report(self) -> str:
        """Generate HTML test summary report"""
        markdown_content = self.generate_markdown_report()

        # Convert Markdown to HTML (simple version)
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DuckBot v4.2 Test Summary</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            border-bottom: 3px solid #007acc;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #555;
            margin-top: 30px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        th {{
            background-color: #f8f9fa;
            font-weight: 600;
        }}
        .success {{
            color: #28a745;
            font-weight: bold;
        }}
        .failure {{
            color: #dc3545;
            font-weight: bold;
        }}
        .warning {{
            color: #ffc107;
            font-weight: bold;
        }}
        .status-good {{
            background-color: #d4edda;
        }}
        .status-warning {{
            background-color: #fff3cd;
        }}
        .status-bad {{
            background-color: #f8d7da;
        }}
        pre {{
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 4px;
            overflow-x: auto;
        }}
    </style>
</head>
<body>
    <div class="container">
        {markdown_content.replace('```', '<pre>').replace('`', '<code>')}
    </div>
</body>
</html>
        """

        return html_content

    def save_reports(self):
        """Save reports to files"""
        # Generate reports
        markdown_report = self.generate_markdown_report()
        html_report = self.generate_html_report()

        # Save Markdown report
        with open("test-summary.md", "w") as f:
            f.write(markdown_report)

        # Save HTML report
        with open("test-summary.html", "w") as f:
            f.write(html_report)

        # Save JSON data
        with open("test-summary.json", "w") as f:
            json.dump(self.summary_data, f, indent=2)

        print("✅ Test summary reports generated:")
        print("   - test-summary.md")
        print("   - test-summary.html")
        print("   - test-summary.json")

def main():
    """Main function"""
    print("🧪 DuckBot v4.2 Test Summary Generator")
    print("=" * 50)

    generator = TestSummaryGenerator()
    generator.collect_results()
    generator.generate_recommendations()
    generator.save_reports()

    # Print summary to console
    print("\n📊 Test Summary:")
    print(f"   Total Tests: {generator.summary_data['total_tests']}")
    print(f"   Passed: {generator.summary_data['passed_tests']}")
    print(f"   Failed: {generator.summary_data['failed_tests']}")
    print(f"   Coverage: {generator.summary_data.get('coverage', {}).get('percentage', 0):.1f}%")

    if generator.summary_data['recommendations']:
        print(f"\n💡 {len(generator.summary_data['recommendations'])} recommendations generated")

if __name__ == "__main__":
    main()