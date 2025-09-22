#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI System Test Runner

Comprehensive test execution script for the DuckBot AI system.
Provides command-line interface for running different test suites.

Usage:
    python run_ai_system_tests.py                    # Run all tests
    python run_ai_system_tests.py --suite unit       # Run unit tests only
    python run_ai_system_tests.py --suite integration # Run integration tests only
    python run_ai_system_tests.py --suite performance # Run performance tests only
    python run_ai_system_tests.py --suite stress     # Run stress tests only
    python run_ai_system_tests.py --component ai_controller  # Test specific component
    python run_ai_system_tests.py --report           # Generate test report
    python run_ai_system_tests.py --cleanup          # Clean up test data
"""

import asyncio
import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add the duckbot module to the path
sys.path.append(str(Path(__file__).parent.parent))

from duckbot.core.ai_system_test_suite import AISystemTestSuite, TestLevel
from duckbot.core.ai_orchestrator import AIOrchestrator
from duckbot.core.ai_system_controller import AISystemController
from duckbot.core.ai_decision_maker import AIDecisionMaker
from duckbot.core.ai_knowledge_base import AIKnowledgeBase
from duckbot.core.ai_driven_system_manager import AIDrivenSystemManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ai_test_results.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class TestRunner:
    """Test runner for AI system tests"""

    def __init__(self):
        self.test_suite = AISystemTestSuite()
        self.results = {}

    async def run_tests(self, args):
        """Run tests based on command line arguments"""
        try:
            if args.suite:
                await self._run_specific_suite(args.suite)
            elif args.component:
                await self._run_component_tests(args.component)
            elif args.report:
                await self._generate_report()
            elif args.cleanup:
                self._cleanup_data()
            else:
                await self._run_all_tests()

            return 0

        except Exception as e:
            logger.error(f"Test execution failed: {e}")
            return 1

    async def _run_all_tests(self):
        """Run all test suites"""
        logger.info("🚀 Starting comprehensive AI system test suite")
        print("=" * 80)
        print("🧪 DUCKBOT AI SYSTEM - COMPREHENSIVE TEST SUITE")
        print("=" * 80)

        results = await self.test_suite.run_all_tests()

        # Display results
        self._display_results(results)

        # Save results
        self._save_results(results)

        logger.info(f"✅ Test suite completed with {results['overall_summary']['success_rate']:.2%} success rate")

    async def _run_specific_suite(self, suite_name):
        """Run a specific test suite"""
        logger.info(f"🚀 Running test suite: {suite_name}")
        print("=" * 80)
        print(f"🧪 DUCKBOT AI SYSTEM - {suite_name.upper()} TESTS")
        print("=" * 80)

        # Map suite names to actual suite names
        suite_mapping = {
            "unit": ["ai_system_controller", "ai_decision_maker", "ai_knowledge_base", "ai_system_manager", "ai_orchestrator"],
            "integration": ["integration"],
            "performance": ["performance"],
            "stress": ["stress"],
            "component": ["ai_system_controller", "ai_decision_maker", "ai_knowledge_base", "ai_system_manager", "ai_orchestrator"]
        }

        if suite_name not in suite_mapping:
            logger.error(f"Unknown test suite: {suite_name}")
            return 1

        suite_names = suite_mapping[suite_name]
        all_results = {}

        for suite_name in suite_names:
            try:
                results = await self.test_suite.run_test_suite(suite_name)
                all_results[suite_name] = results
                self._display_suite_results(results)
            except Exception as e:
                logger.error(f"Error running suite {suite_name}: {e}")
                all_results[suite_name] = {"error": str(e)}

        self.results = all_results

    async def _run_component_tests(self, component_name):
        """Run tests for a specific component"""
        logger.info(f"🚀 Running tests for component: {component_name}")
        print("=" * 80)
        print(f"🧪 DUCKBOT AI SYSTEM - {component_name.upper()} TESTS")
        print("=" * 80)

        # Map component names to test suites
        component_mapping = {
            "ai_controller": "ai_system_controller",
            "decision_maker": "ai_decision_maker",
            "knowledge_base": "ai_knowledge_base",
            "system_manager": "ai_system_manager",
            "orchestrator": "ai_orchestrator"
        }

        if component_name not in component_mapping:
            logger.error(f"Unknown component: {component_name}")
            return 1

        suite_name = component_mapping[component_name]
        results = await self.test_suite.run_test_suite(suite_name)
        self.results = {suite_name: results}

        self._display_suite_results(results)

    async def _generate_report(self):
        """Generate comprehensive test report"""
        logger.info("📊 Generating test report")
        print("=" * 80)
        print("📋 DUCKBOT AI SYSTEM - TEST REPORT")
        print("=" * 80)

        report = await self.test_suite.generate_test_report()

        # Display report summary
        summary = report["test_summary"]
        print(f"\n📈 Test Summary:")
        print(f"   Total Tests: {summary['total_tests']}")
        print(f"   Passed: {summary['passed_tests']} ✅")
        print(f"   Failed: {summary['failed_tests']} ❌")
        print(f"   Skipped: {summary['skipped_tests']} ⏭️")
        print(f"   Errors: {summary['error_tests']} 🔥")
        print(f"   Success Rate: {summary['success_rate']:.2%}")
        print(f"   Execution Time: {summary['total_execution_time']:.2f}s")

        # Display component performance
        print(f"\n🔧 Component Performance:")
        for component, perf in report["component_performance"].items():
            status_icon = "✅" if perf["success_rate"] >= 0.9 else "⚠️" if perf["success_rate"] >= 0.7 else "❌"
            print(f"   {component}: {perf['passed_tests']}/{perf['total_tests']} ({perf['success_rate']:.2%}) {status_icon}")

        # Display recommendations
        if report["recommendations"]:
            print(f"\n💡 Recommendations:")
            for i, rec in enumerate(report["recommendations"], 1):
                print(f"   {i}. {rec}")

        # Save report
        report_file = f"ai_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"\n📄 Detailed report saved to: {report_file}")

    def _cleanup_data(self):
        """Clean up test data"""
        logger.info("🧹 Cleaning up test data")
        self.test_suite.cleanup_test_data()
        print("✅ Test data cleaned up")

    def _display_results(self, results):
        """Display comprehensive test results"""
        summary = results["overall_summary"]

        print(f"\n🎯 Overall Results:")
        print(f"   Total Tests: {summary['total_tests']}")
        print(f"   Passed: {summary['passed_tests']} ✅")
        print(f"   Failed: {summary['failed_tests']} ❌")
        print(f"   Skipped: {summary['skipped_tests']} ⏭️")
        print(f"   Errors: {summary['error_tests']} 🔥")
        print(f"   Success Rate: {summary['success_rate']:.2%}")
        print(f"   Execution Time: {summary['total_execution_time']:.2f}s")

        print(f"\n📊 Suite Results:")
        for suite_name, suite_result in results["suite_results"].items():
            if "error" not in suite_result:
                suite_summary = suite_result["summary"]
                status_icon = "✅" if suite_summary["success_rate"] >= 0.9 else "⚠️" if suite_summary["success_rate"] >= 0.7 else "❌"
                print(f"   {suite_name}: {suite_summary['passed_tests']}/{suite_summary['total_tests']} ({suite_summary['success_rate']:.2%}) {status_icon}")

        # Display component breakdown
        if summary["component_results"]:
            print(f"\n🔧 Component Breakdown:")
            for component, comp_result in summary["component_results"].items():
                status_icon = "✅" if comp_result["success_rate"] >= 0.9 else "⚠️" if comp_result["success_rate"] >= 0.7 else "❌"
                print(f"   {component}: {comp_result['passed_tests']}/{comp_result['total_tests']} ({comp_result['success_rate']:.2%}) {status_icon}")

        # Overall assessment
        if summary["success_rate"] >= 0.95:
            print(f"\n🎉 Excellent! System is performing at optimal level")
        elif summary["success_rate"] >= 0.85:
            print(f"\n👍 Good! System is functioning well")
        elif summary["success_rate"] >= 0.70:
            print(f"\n⚠️  Acceptable! Some issues need attention")
        else:
            print(f"\n🚨 Critical! System needs immediate attention")

    def _display_suite_results(self, results):
        """Display results for a single test suite"""
        summary = results["summary"]

        print(f"\n📋 Suite Results:")
        print(f"   Total Tests: {summary['total_tests']}")
        print(f"   Passed: {summary['passed_tests']} ✅")
        print(f"   Failed: {summary['failed_tests']} ❌")
        print(f"   Skipped: {summary['skipped_tests']} ⏭️")
        print(f"   Errors: {summary['error_tests']} 🔥")
        print(f"   Success Rate: {summary['success_rate']:.2%}")
        print(f"   Execution Time: {summary['execution_time']:.2f}s")

        # Display failed tests
        if summary["failed_tests"] > 0 or summary["error_tests"] > 0:
            print(f"\n❌ Failed/Error Tests:")
            for test_result in results["test_results"]:
                if test_result["result"] in ["failed", "error"]:
                    print(f"   - {test_result['test_name']}: {test_result['result']}")
                    if test_result.get("error"):
                        print(f"     Error: {test_result['error']}")

    def _save_results(self, results):
        """Save test results to file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"ai_test_results_{timestamp}.json"

        with open(filename, 'w') as f:
            json.dump(results, f, indent=2, default=str)

        logger.info(f"📄 Test results saved to: {filename}")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="DuckBot AI System Test Suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        "--suite",
        choices=["unit", "integration", "performance", "stress", "component"],
        help="Run specific test suite"
    )

    parser.add_argument(
        "--component",
        choices=["ai_controller", "decision_maker", "knowledge_base", "system_manager", "orchestrator"],
        help="Run tests for specific component"
    )

    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate comprehensive test report"
    )

    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Clean up test data"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Run tests
    runner = TestRunner()

    try:
        return asyncio.run(runner.run_tests(args))
    except KeyboardInterrupt:
        logger.info("🛑 Test execution interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())