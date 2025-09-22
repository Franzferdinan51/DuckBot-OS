#!/usr/bin/env python3
"""
DuckBot Comprehensive Integration Test Runner
Runs all integration tests and generates a comprehensive report
"""

import os
import sys
import subprocess
import time
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

class ComprehensiveTestRunner:
    """Runs all integration tests and generates comprehensive reports"""

    def __init__(self, base_dir: Path = None):
        self.base_dir = base_dir or Path(__file__).parent
        self.test_results = []
        self.start_time = time.time()

    def run_test(self, test_file: str, test_name: str) -> Dict[str, Any]:
        """Run a specific test and return results"""
        try:
            print(f"\n{'='*60}")
            print(f"Running {test_name}...")
            print(f"{'='*60}")

            # Run the test
            result = subprocess.run([
                sys.executable, test_file, "--verbose"
            ], capture_output=True, text=True, timeout=300, cwd=self.base_dir)

            # Parse results
            test_result = {
                "test_name": test_name,
                "test_file": test_file,
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "timestamp": datetime.now().isoformat(),
                "duration": time.time() - self.start_time
            }

            # Print output
            print(result.stdout)
            if result.stderr:
                print(f"STDERR:\n{result.stderr}")

            return test_result

        except subprocess.TimeoutExpired:
            return {
                "test_name": test_name,
                "test_file": test_file,
                "return_code": -1,
                "error": "Test timed out",
                "timestamp": datetime.now().isoformat(),
                "duration": time.time() - self.start_time
            }
        except Exception as e:
            return {
                "test_name": test_name,
                "test_file": test_file,
                "return_code": -1,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "duration": time.time() - self.start_time
            }

    def parse_test_results(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Parse test results from output"""
        parsed = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "errors": 0,
            "pass_rate": 0.0,
            "issues": []
        }

        # Parse stdout for test results
        stdout = result.get("stdout", "")

        # Look for test summary patterns
        import re

        # Try to extract test counts
        total_match = re.search(r"Total Tests:\s*(\d+)", stdout)
        passed_match = re.search(r"Passed:\s*(\d+)", stdout)
        failed_match = re.search(r"Failed:\s*(\d+)", stdout)
        errors_match = re.search(r"Errors:\s*(\d+)", stdout)

        if total_match:
            parsed["total_tests"] = int(total_match.group(1))
        if passed_match:
            parsed["passed"] = int(passed_match.group(1))
        if failed_match:
            parsed["failed"] = int(failed_match.group(1))
        if errors_match:
            parsed["errors"] = int(errors_match.group(1))

        # Calculate pass rate
        if parsed["total_tests"] > 0:
            parsed["pass_rate"] = (parsed["passed"] / parsed["total_tests"]) * 100

        # Extract issues
        issue_lines = []
        for line in stdout.split('\n'):
            if '❌' in line or '💥' in line or 'Error:' in line or 'Missing:' in line or 'Failed:' in line:
                issue_lines.append(line.strip())

        parsed["issues"] = issue_lines

        return parsed

    def generate_comprehensive_report(self, results: List[Dict[str, Any]]) -> str:
        """Generate a comprehensive test report"""
        total_duration = time.time() - self.start_time

        # Aggregate results
        total_tests = sum(r.get("total_tests", 0) for r in results)
        total_passed = sum(r.get("passed", 0) for r in results)
        total_failed = sum(r.get("failed", 0) for r in results)
        total_errors = sum(r.get("errors", 0) for r in results)

        overall_pass_rate = (total_passed / total_tests) * 100 if total_tests > 0 else 0

        report = f"""
# DuckBot Startup System Comprehensive Integration Test Report

## Executive Summary
- **Test Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Total Duration**: {total_duration:.2f} seconds
- **Overall Pass Rate**: {overall_pass_rate:.1f}%
- **Overall Status**: {'✅ PASSED' if total_failed == 0 and total_errors == 0 else '❌ FAILED'}

## Test Results Summary
- **Total Tests**: {total_tests}
- **Passed**: {total_passed} ✅
- **Failed**: {total_failed} ❌
- **Errors**: {total_errors} 💥

## Individual Test Suites
"""

        for result in results:
            test_name = result.get("test_name", "Unknown")
            return_code = result.get("return_code", -1)
            duration = result.get("duration", 0)
            parsed = self.parse_test_results(result)

            status_emoji = "✅" if return_code == 0 else "❌"
            report += f"""
### {status_emoji} {test_name}
- **Duration**: {duration:.2f}s
- **Return Code**: {return_code}
- **Tests**: {parsed['passed']}/{parsed['total_tests']} passed ({parsed['pass_rate']:.1f}%)
"""

            if parsed['issues']:
                report += "- **Issues Found**:\n"
                for issue in parsed['issues'][:5]:  # Show first 5 issues
                    report += f"  - {issue}\n"

        report += f"""
## System Information
- **Python Version**: {sys.version.split()[0]}
- **Platform**: {sys.platform}
- **Working Directory**: {self.base_dir}
- **Test Runner**: {sys.executable}

## Critical Issues and Recommendations
"""

        # Collect all issues
        all_issues = []
        for result in results:
            parsed = self.parse_test_results(result)
            all_issues.extend(parsed['issues'])

        # Generate recommendations
        if total_failed > 0 or total_errors > 0:
            report += "### Issues Found\n"
            for issue in all_issues[:10]:  # Show first 10 issues
                report += f"- {issue}\n"

            report += "\n### Recommendations\n"

            # Specific recommendations based on common issues
            issue_text = " ".join(all_issues).lower()

            if "not found" in issue_text:
                report += "1. **Missing Files**: Ensure all required launcher and configuration files are present\n"

            if "python" in issue_text and "not found" in issue_text:
                report += "2. **Python Environment**: Verify Python installation and PATH configuration\n"

            if "configuration" in issue_text:
                report += "3. **Configuration Files**: Validate all JSON and YAML configuration files\n"

            if "permission" in issue_text or "access" in issue_text:
                report += "4. **File Permissions**: Check file permissions and accessibility\n"

            report += "5. **Dependencies**: Install all required Python dependencies\n"
            report += "6. **Environment Variables**: Verify all required environment variables are set\n"

        else:
            report += "✅ No critical issues found. All systems are functioning correctly.\n"

        report += f"""
## Next Steps
1. **Address Failed Tests**: Fix any failing tests identified above
2. **Performance Optimization**: Consider optimizing slow-performing components
3. **Documentation**: Update documentation with any system changes
4. **Regular Testing**: Run these integration tests regularly to catch regressions

## Test Artifacts
All test logs and detailed reports are available in the `test_logs/` directory.
"""

        return report

    def run_all_tests(self) -> str:
        """Run all integration tests"""
        print("🚀 Starting DuckBot Comprehensive Integration Tests")
        print(f"Working Directory: {self.base_dir}")
        print(f"Python: {sys.executable}")
        print(f"Platform: {sys.platform}")

        # Define tests to run
        test_suites = [
            ("tests/integration/test_current_launcher.py", "Current Launcher Integration"),
            ("tests/integration/test_configuration_integration.py", "Configuration System Integration"),
        ]

        results = []

        for test_file, test_name in test_suites:
            test_path = self.base_dir / test_file
            if test_path.exists():
                result = self.run_test(str(test_path), test_name)
                results.append(result)
            else:
                print(f"❌ Test file not found: {test_path}")
                results.append({
                    "test_name": test_name,
                    "test_file": test_file,
                    "return_code": -1,
                    "error": "Test file not found",
                    "timestamp": datetime.now().isoformat(),
                    "duration": 0
                })

        # Generate comprehensive report
        report = self.generate_comprehensive_report(results)

        # Save report
        report_path = self.base_dir / "test_reports" / f"comprehensive_integration_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        report_path.parent.mkdir(exist_ok=True)

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)

        # Also save JSON data
        json_path = report_path.with_suffix('.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "test_results": results,
                "parsed_results": [self.parse_test_results(r) for r in results]
            }, f, indent=2, default=str)

        # Print summary
        print(f"\n{'='*80}")
        print(f"COMPREHENSIVE INTEGRATION TEST RESULTS")
        print(f"{'='*80}")
        print(f"Report saved to: {report_path}")
        print(f"JSON data saved to: {json_path}")

        # Calculate overall stats
        total_tests = sum(self.parse_test_results(r).get("total_tests", 0) for r in results)
        total_passed = sum(self.parse_test_results(r).get("passed", 0) for r in results)
        total_failed = sum(self.parse_test_results(r).get("failed", 0) for r in results)
        total_errors = sum(self.parse_test_results(r).get("errors", 0) for r in results)

        print(f"Total Tests: {total_tests}")
        print(f"Passed: {total_passed} ✅")
        print(f"Failed: {total_failed} ❌")
        print(f"Errors: {total_errors} 💥")

        if total_failed > 0 or total_errors > 0:
            print(f"\n❌ Integration tests completed with issues")
            print(f"   Check the report for details: {report_path}")
            return report
        else:
            print(f"\n✅ All integration tests passed!")
            return report

def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="DuckBot Comprehensive Integration Test Runner")
    parser.add_argument("--report-only", action="store_true", help="Only generate report without running tests")

    args = parser.parse_args()

    runner = ComprehensiveTestRunner()

    if args.report_only:
        print("Report-only mode not implemented yet")
        sys.exit(1)
    else:
        report = runner.run_all_tests()

if __name__ == "__main__":
    main()