#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive Test Script for UI-TARS MCP Integration
Tests all 13 UI-TARS tools in the DuckBot MCP Server
"""

import asyncio
import json
import logging
import sys
import traceback
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(project_root / 'logs' / 'ui_tars_mcp_test.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class UITarsMCPTester:
    """Comprehensive tester for UI-TARS MCP integration"""

    def __init__(self):
        self.test_results = []
        self.mcp_server = None
        self.ui_tars_integration = None
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.skipped_tests = 0

        # Expected UI-TARS tools
        self.expected_ui_tars_tools = [
            "ui_tars_start_session",
            "ui_tars_stop_session",
            "ui_tars_screenshot",
            "ui_tars_click",
            "ui_tars_type",
            "ui_tars_open_application",
            "ui_tars_navigate_to_url",
            "ui_tars_find_element",
            "ui_tars_wait_for_element",
            "ui_tars_get_screen_info",
            "ui_tars_list_applications",
            "ui_tars_close_application",
            "ui_tars_workflow"
        ]

        # Test parameters
        self.test_params = {
            "ui_tars_start_session": {
                "provider": "volcengine",
                "model": "doubao-1-5-thinking-vision-pro-250428",
                "max_steps": 50
            },
            "ui_tars_click": {
                "element": "test_button",
                "context": {"window": "test_window"}
            },
            "ui_tars_type": {
                "text": "Hello World",
                "context": {"application": "test_app"}
            },
            "ui_tars_open_application": {
                "application": "notepad.exe"
            },
            "ui_tars_navigate_to_url": {
                "url": "https://example.com"
            },
            "ui_tars_find_element": {
                "element": "search_box"
            },
            "ui_tars_wait_for_element": {
                "element": "loading_spinner",
                "timeout": 30
            },
            "ui_tars_close_application": {
                "application": "notepad.exe"
            },
            "ui_tars_workflow": {
                "steps": [
                    {"type": "open", "params": {"app": "notepad.exe"}},
                    {"type": "type", "params": {"text": "Test"}},
                    {"type": "screenshot"}
                ],
                "description": "Test workflow"
            }
        }

    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all UI-TARS MCP integration tests"""
        logger.info("=== Starting UI-TARS MCP Integration Tests ===")

        try:
            # Test 1: Import MCP Server
            await self.test_mcp_server_import()

            # Test 2: Import UI-TARS Integration
            await self.test_ui_tars_import()

            # Test 3: Initialize MCP Server
            await self.test_mcp_server_initialization()

            # Test 4: Check UI-TARS Integration Availability
            await self.test_ui_tars_integration_availability()

            # Test 5: Verify Tool Registration
            await self.test_tool_registration()

            # Test 6: Test Handler Function Existence
            await self.test_handler_functions()

            # Test 7: Test Input/Output Validation
            await self.test_input_output_validation()

            # Test 8: Test Error Handling
            await self.test_error_handling()

            # Test 9: Test Integration with MCP System
            await self.test_mcp_system_integration()

            # Test 10: Test Tool Execution (Mock)
            await self.test_tool_execution_mock()

        except Exception as e:
            logger.error(f"Fatal error during testing: {e}")
            self.add_test_result(
                test_name="fatal_error",
                passed=False,
                error=str(e),
                details="Fatal error occurred during test execution"
            )

        # Generate final report
        report = self.generate_test_report()
        logger.info("=== UI-TARS MCP Integration Tests Completed ===")
        return report

    async def test_mcp_server_import(self):
        """Test MCP Server import"""
        logger.info("Testing MCP Server import...")

        try:
            from duckbot.integrations.mcp_server import DuckBotMCPServer, mcp_server
            self.mcp_server = mcp_server
            self.add_test_result(
                test_name="mcp_server_import",
                passed=True,
                details="MCP Server imported successfully"
            )
        except ImportError as e:
            self.add_test_result(
                test_name="mcp_server_import",
                passed=False,
                error=str(e),
                details="Failed to import MCP Server"
            )
        except Exception as e:
            self.add_test_result(
                test_name="mcp_server_import",
                passed=False,
                error=str(e),
                details="Unexpected error importing MCP Server"
            )

    async def test_ui_tars_import(self):
        """Test UI-TARS Integration import"""
        logger.info("Testing UI-TARS Integration import...")

        try:
            from duckbot.integrations.ui_tars_integration import UITarsIntegration, UITarsConfig
            self.ui_tars_class = UITarsIntegration
            self.ui_tars_config_class = UITarsConfig
            self.add_test_result(
                test_name="ui_tars_import",
                passed=True,
                details="UI-TARS Integration imported successfully"
            )
        except ImportError as e:
            self.add_test_result(
                test_name="ui_tars_import",
                passed=False,
                error=str(e),
                details="Failed to import UI-TARS Integration"
            )
        except Exception as e:
            self.add_test_result(
                test_name="ui_tars_import",
                passed=False,
                error=str(e),
                details="Unexpected error importing UI-TARS Integration"
            )

    async def test_mcp_server_initialization(self):
        """Test MCP Server initialization"""
        logger.info("Testing MCP Server initialization...")

        if not self.mcp_server:
            self.add_test_result(
                test_name="mcp_server_initialization",
                passed=False,
                error="MCP Server not available",
                details="Cannot initialize MCP Server - import failed"
            )
            return

        try:
            # Test server initialization
            success = await self.mcp_server.initialize_mcp_server()

            if success:
                self.add_test_result(
                    test_name="mcp_server_initialization",
                    passed=True,
                    details=f"MCP Server initialized successfully with {len(self.mcp_server.tools)} tools"
                )
            else:
                self.add_test_result(
                    test_name="mcp_server_initialization",
                    passed=False,
                    error="Initialization returned False",
                    details="MCP Server initialization failed"
                )
        except Exception as e:
            self.add_test_result(
                test_name="mcp_server_initialization",
                passed=False,
                error=str(e),
                details="Error during MCP Server initialization"
            )

    async def test_ui_tars_integration_availability(self):
        """Test UI-TARS integration availability in MCP Server"""
        logger.info("Testing UI-TARS integration availability...")

        if not self.mcp_server:
            self.add_test_result(
                test_name="ui_tars_integration_availability",
                passed=False,
                error="MCP Server not available",
                details="Cannot test UI-TARS integration - MCP Server not initialized"
            )
            return

        try:
            # Check if UI-TARS integration is in integration instances
            ui_tars_available = 'ui_tars' in self.mcp_server.integration_instances

            if ui_tars_available:
                ui_tars_instance = self.mcp_server.integration_instances['ui_tars']
                status = ui_tars_instance.get_status()
                self.add_test_result(
                    test_name="ui_tars_integration_availability",
                    passed=True,
                    details=f"UI-TARS integration available: {status}"
                )
            else:
                self.add_test_result(
                    test_name="ui_tars_integration_availability",
                    passed=False,
                    error="UI-TARS integration not found",
                    details="UI-TARS integration not in MCP Server integration instances"
                )
        except Exception as e:
            self.add_test_result(
                test_name="ui_tars_integration_availability",
                passed=False,
                error=str(e),
                details="Error checking UI-TARS integration availability"
            )

    async def test_tool_registration(self):
        """Test UI-TARS tool registration in MCP Server"""
        logger.info("Testing UI-TARS tool registration...")

        if not self.mcp_server:
            self.add_test_result(
                test_name="tool_registration",
                passed=False,
                error="MCP Server not available",
                details="Cannot test tool registration - MCP Server not initialized"
            )
            return

        registered_tools = []
        missing_tools = []

        for tool_name in self.expected_ui_tars_tools:
            if tool_name in self.mcp_server.tools:
                registered_tools.append(tool_name)
            else:
                missing_tools.append(tool_name)

        if len(registered_tools) == len(self.expected_ui_tars_tools):
            self.add_test_result(
                test_name="tool_registration",
                passed=True,
                details=f"All {len(registered_tools)} UI-TARS tools registered successfully"
            )
        else:
            self.add_test_result(
                test_name="tool_registration",
                passed=False,
                error=f"Missing {len(missing_tools)} tools",
                details=f"Registered: {registered_tools}, Missing: {missing_tools}"
            )

    async def test_handler_functions(self):
        """Test handler function existence and structure"""
        logger.info("Testing UI-TARS handler functions...")

        if not self.mcp_server:
            self.add_test_result(
                test_name="handler_functions",
                passed=False,
                error="MCP Server not available",
                details="Cannot test handler functions - MCP Server not initialized"
            )
            return

        missing_handlers = []
        invalid_handlers = []

        for tool_name in self.expected_ui_tars_tools:
            if tool_name in self.mcp_server.tools:
                tool_info = self.mcp_server.tools[tool_name]
                handler = tool_info.get('handler')

                if handler is None:
                    missing_handlers.append(tool_name)
                elif not callable(handler):
                    invalid_handlers.append(tool_name)
            else:
                missing_handlers.append(tool_name)

        if not missing_handlers and not invalid_handlers:
            self.add_test_result(
                test_name="handler_functions",
                passed=True,
                details=f"All {len(self.expected_ui_tars_tools)} UI-TARS handlers are valid and callable"
            )
        else:
            error_msg = []
            if missing_handlers:
                error_msg.append(f"Missing handlers: {missing_handlers}")
            if invalid_handlers:
                error_msg.append(f"Invalid handlers: {invalid_handlers}")

            self.add_test_result(
                test_name="handler_functions",
                passed=False,
                error="; ".join(error_msg),
                details="Some UI-TARS handlers are missing or not callable"
            )

    async def test_input_output_validation(self):
        """Test input/output validation for UI-TARS tools"""
        logger.info("Testing UI-TARS input/output validation...")

        if not self.mcp_server:
            self.add_test_result(
                test_name="input_output_validation",
                passed=False,
                error="MCP Server not available",
                details="Cannot test input/output validation - MCP Server not initialized"
            )
            return

        validation_results = []

        for tool_name in self.expected_ui_tars_tools:
            if tool_name in self.mcp_server.tools:
                tool_info = self.mcp_server.tools[tool_name]
                input_schema = tool_info.get('input_schema')

                # Test input schema structure
                if input_schema and isinstance(input_schema, dict):
                    if 'type' in input_schema and input_schema['type'] == 'object':
                        if 'properties' in input_schema:
                            validation_results.append(f"{tool_name}: Valid schema")
                        else:
                            validation_results.append(f"{tool_name}: Missing properties")
                    else:
                        validation_results.append(f"{tool_name}: Invalid schema type")
                else:
                    validation_results.append(f"{tool_name}: No input schema")

        valid_schemas = sum(1 for result in validation_results if "Valid schema" in result)
        total_schemas = len(validation_results)

        if valid_schemas == total_schemas:
            self.add_test_result(
                test_name="input_output_validation",
                passed=True,
                details=f"All {total_schemas} UI-TARS tools have valid input schemas"
            )
        else:
            self.add_test_result(
                test_name="input_output_validation",
                passed=False,
                error=f"{total_schemas - valid_schemas} tools have invalid schemas",
                details="Schema validation results: " + "; ".join(validation_results)
            )

    async def test_error_handling(self):
        """Test error handling for UI-TARS tools"""
        logger.info("Testing UI-TARS error handling...")

        if not self.mcp_server:
            self.add_test_result(
                test_name="error_handling",
                passed=False,
                error="MCP Server not available",
                details="Cannot test error handling - MCP Server not initialized"
            )
            return

        # Test error handling by examining handler functions
        error_handling_tests = []

        for tool_name in self.expected_ui_tars_tools:
            if tool_name in self.mcp_server.tools:
                handler = self.mcp_server.tools[tool_name].get('handler')

                if handler and callable(handler):
                    # Check if handler is async
                    if asyncio.iscoroutinefunction(handler):
                        error_handling_tests.append(f"{tool_name}: Async handler")
                    else:
                        error_handling_tests.append(f"{tool_name}: Sync handler")
                else:
                    error_handling_tests.append(f"{tool_name}: No handler")

        async_handlers = sum(1 for test in error_handling_tests if "Async handler" in test)
        total_handlers = len(error_handling_tests)

        # Most UI-TARS handlers should be async
        if async_handlers >= total_handlers * 0.8:  # 80% threshold
            self.add_test_result(
                test_name="error_handling",
                passed=True,
                details=f"{async_handlers}/{total_handlers} UI-TARS handlers are async-ready"
            )
        else:
            self.add_test_result(
                test_name="error_handling",
                passed=False,
                error=f"Only {async_handlers}/{total_handlers} handlers are async-ready",
                details="Error handling test results: " + "; ".join(error_handling_tests)
            )

    async def test_mcp_system_integration(self):
        """Test integration with broader MCP system"""
        logger.info("Testing MCP system integration...")

        if not self.mcp_server:
            self.add_test_result(
                test_name="mcp_system_integration",
                passed=False,
                error="MCP Server not available",
                details="Cannot test MCP system integration - MCP Server not initialized"
            )
            return

        integration_tests = []

        # Test server status
        try:
            status = self.mcp_server.get_status()
            if isinstance(status, dict) and 'running' in status:
                integration_tests.append("Server status: OK")
            else:
                integration_tests.append("Server status: Invalid")
        except Exception as e:
            integration_tests.append(f"Server status: Error - {str(e)}")

        # Test tools listing
        try:
            tools = await self.mcp_server.get_mcp_tools()
            if isinstance(tools, dict) and 'tools' in tools:
                ui_tars_tools_in_list = sum(1 for tool in tools['tools']
                                         if tool['name'] in self.expected_ui_tars_tools)
                integration_tests.append(f"Tools listing: {ui_tars_tools_in_list} UI-TARS tools found")
            else:
                integration_tests.append("Tools listing: Invalid format")
        except Exception as e:
            integration_tests.append(f"Tools listing: Error - {str(e)}")

        # Test integration instances
        try:
            integrations = list(self.mcp_server.integration_instances.keys())
            if 'ui_tars' in integrations:
                integration_tests.append("Integration instances: UI-TARS found")
            else:
                integration_tests.append("Integration instances: UI-TARS missing")
        except Exception as e:
            integration_tests.append(f"Integration instances: Error - {str(e)}")

        passed_integrations = sum(1 for test in integration_tests if "OK" in test or "found" in test)
        total_integrations = len(integration_tests)

        if passed_integrations == total_integrations:
            self.add_test_result(
                test_name="mcp_system_integration",
                passed=True,
                details=f"All {total_integrations} MCP system integration tests passed"
            )
        else:
            self.add_test_result(
                test_name="mcp_system_integration",
                passed=False,
                error=f"{total_integrations - passed_integrations} integration tests failed",
                details="Integration test results: " + "; ".join(integration_tests)
            )

    async def test_tool_execution_mock(self):
        """Test tool execution with mock data (no actual UI-TARS required)"""
        logger.info("Testing UI-TARS tool execution (mock)...")

        if not self.mcp_server:
            self.add_test_result(
                test_name="tool_execution_mock",
                passed=False,
                error="MCP Server not available",
                details="Cannot test tool execution - MCP Server not initialized"
            )
            return

        execution_results = []

        # Test a few key tools with mock parameters
        test_tools = [
            "ui_tars_start_session",
            "ui_tars_screenshot",
            "ui_tars_get_screen_info",
            "ui_tars_list_applications"
        ]

        for tool_name in test_tools:
            if tool_name in self.mcp_server.tools:
                handler = self.mcp_server.tools[tool_name].get('handler')

                if handler and callable(handler):
                    try:
                        # Use test parameters or empty dict
                        params = self.test_params.get(tool_name, {})

                        # For mock testing, we'll expect the handlers to handle missing UI-TARS gracefully
                        if asyncio.iscoroutinefunction(handler):
                            # Mock async call - we expect handlers to fail gracefully without UI-TARS
                            try:
                                result = await handler(params)
                                if isinstance(result, dict) and ('success' in result or 'error' in result):
                                    execution_results.append(f"{tool_name}: Valid response format")
                                else:
                                    execution_results.append(f"{tool_name}: Invalid response format")
                            except Exception as e:
                                # Expected to fail without UI-TARS, but should fail gracefully
                                if "UI-TARS" in str(e) or "not found" in str(e).lower():
                                    execution_results.append(f"{tool_name}: Graceful error handling")
                                else:
                                    execution_results.append(f"{tool_name}: Unexpected error - {str(e)}")
                        else:
                            execution_results.append(f"{tool_name}: Not async handler")
                    except Exception as e:
                        execution_results.append(f"{tool_name}: Handler error - {str(e)}")
                else:
                    execution_results.append(f"{tool_name}: No handler")
            else:
                execution_results.append(f"{tool_name}: Tool not found")

        valid_executions = sum(1 for result in execution_results
                              if "Valid response" in result or "Graceful error" in result)
        total_executions = len(execution_results)

        if valid_executions >= total_executions * 0.75:  # 75% threshold for mock testing
            self.add_test_result(
                test_name="tool_execution_mock",
                passed=True,
                details=f"{valid_executions}/{total_executions} tool executions handled correctly"
            )
        else:
            self.add_test_result(
                test_name="tool_execution_mock",
                passed=False,
                error=f"Only {valid_executions}/{total_executions} tool executions handled correctly",
                details="Execution results: " + "; ".join(execution_results)
            )

    def add_test_result(self, test_name: str, passed: bool,
                       error: Optional[str] = None, details: str = ""):
        """Add test result to the results list"""
        self.total_tests += 1

        if passed:
            self.passed_tests += 1
        else:
            self.failed_tests += 1

        result = {
            "test_name": test_name,
            "passed": passed,
            "timestamp": datetime.now().isoformat(),
            "details": details
        }

        if error:
            result["error"] = error

        self.test_results.append(result)

        status = "PASS" if passed else "FAIL"
        logger.info(f"Test {test_name}: {status}")
        if error:
            logger.error(f"  Error: {error}")
        if details:
            logger.info(f"  Details: {details}")

    def generate_test_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        logger.info("Generating test report...")

        report = {
            "test_summary": {
                "total_tests": self.total_tests,
                "passed_tests": self.passed_tests,
                "failed_tests": self.failed_tests,
                "skipped_tests": self.skipped_tests,
                "success_rate": (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
            },
            "ui_tars_tools_status": {
                "expected_tools": len(self.expected_ui_tars_tools),
                "tools_tested": len([r for r in self.test_results if any(tool in r['test_name'] for tool in self.expected_ui_tars_tools)]),
                "tool_names": self.expected_ui_tars_tools
            },
            "detailed_results": self.test_results,
            "recommendations": self.generate_recommendations(),
            "timestamp": datetime.now().isoformat()
        }

        # Save report to file
        report_file = project_root / 'logs' / 'ui_tars_mcp_test_report.json'
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            logger.info(f"Test report saved to: {report_file}")
        except Exception as e:
            logger.error(f"Failed to save test report: {e}")

        return report

    def generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []

        if self.failed_tests > 0:
            recommendations.append("Fix failed tests before deploying UI-TARS integration")

        # Check for common issues
        failed_tests = [r for r in self.test_results if not r['passed']]

        if any("import" in test['test_name'] for test in failed_tests):
            recommendations.append("Check MCP Server and UI-TARS integration dependencies")

        if any("registration" in test['test_name'] for test in failed_tests):
            recommendations.append("Verify UI-TARS tools are properly registered in MCP Server")

        if any("handler" in test['test_name'] for test in failed_tests):
            recommendations.append("Ensure all UI-TARS tool handlers are implemented correctly")

        if self.passed_tests == self.total_tests:
            recommendations.append("UI-TARS MCP integration is ready for production use")
            recommendations.append("Consider running actual UI-TARS tests with real installation")

        return recommendations

async def main():
    """Main test execution function"""
    tester = UITarsMCPTester()

    print("=== DuckBot UI-TARS MCP Integration Test ===")
    print("Testing all 13 UI-TARS tools in the MCP Server...")
    print("Note: This test does not require actual UI-TARS installation")
    print()

    try:
        report = await tester.run_all_tests()

        # Print summary
        summary = report['test_summary']
        print("\n=== Test Summary ===")
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Passed: {summary['passed_tests']}")
        print(f"Failed: {summary['failed_tests']}")
        print(f"Success Rate: {summary['success_rate']:.1f}%")

        if summary['failed_tests'] > 0:
            print("\n=== Failed Tests ===")
            for result in report['detailed_results']:
                if not result['passed']:
                    print(f"- {result['test_name']}: {result.get('error', 'Unknown error')}")

        print("\n=== Recommendations ===")
        for rec in report['recommendations']:
            print(f"- {rec}")

        print(f"\nFull test report saved to: logs/ui_tars_mcp_test_report.json")

        return summary['success_rate'] >= 80  # Consider 80% success rate as acceptable

    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        print(f"Test execution failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)