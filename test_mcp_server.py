#!/usr/bin/env python3
"""
MCP Server Test Script
Tests the MCP server functionality and available integrations
"""

import asyncio
import json
import requests
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MCPServerTester:
    def __init__(self):
        self.server_url = "http://127.0.0.1:8790"
        self.test_results = []

    def log_test(self, test_name, passed, details=""):
        """Log test results"""
        status = "PASS" if passed else "FAIL"
        self.test_results.append({
            "test": test_name,
            "status": status,
            "details": details
        })
        logger.info(f"{status}: {test_name} - {details}")

    async def test_server_connectivity(self):
        """Test if MCP server is accessible"""
        try:
            # Try to connect to the server
            response = requests.get(f"{self.server_url}/", timeout=5)
            self.log_test("Server Connectivity", True, f"Server responded with status {response.status_code}")
            return True
        except requests.exceptions.ConnectionError:
            self.log_test("Server Connectivity", False, "Connection refused - server may not be running")
            return False
        except Exception as e:
            self.log_test("Server Connectivity", False, f"Error: {e}")
            return False

    async def test_tool_registration(self):
        """Test if tools are properly registered"""
        try:
            # Import MCP server to check registered tools
            import sys
            sys.path.insert(0, str(Path(__file__).parent))

            from duckbot.integrations.mcp_server import DuckBotMCPServer

            server = DuckBotMCPServer()
            tools = server.tools
            resources = server.resources

            self.log_test("Tool Registration", True,
                          f"Registered {len(tools)} tools and {len(resources)} resources")

            # Log available tools
            for tool_name in tools:
                logger.info(f"  - Tool: {tool_name}")

            for resource_name in resources:
                logger.info(f"  - Resource: {resource_name}")

            return True
        except Exception as e:
            self.log_test("Tool Registration", False, f"Error: {e}")
            return False

    async def test_integration_availability(self):
        """Test if all integrations are available"""
        try:
            import sys
            sys.path.insert(0, str(Path(__file__).parent))

            from duckbot.integrations.mcp_server import DuckBotMCPServer

            server = DuckBotMCPServer()
            integrations = list(server.integration_instances.keys())

            expected_integrations = ['ui_tars', 'bytebot', 'archon', 'wsl', 'cost_tracker', 'server_manager']

            missing_integrations = [i for i in expected_integrations if i not in integrations]

            if missing_integrations:
                self.log_test("Integration Availability", False,
                              f"Missing integrations: {missing_integrations}")
            else:
                self.log_test("Integration Availability", True,
                              f"All expected integrations available: {integrations}")

            return len(missing_integrations) == 0
        except Exception as e:
            self.log_test("Integration Availability", False, f"Error: {e}")
            return False

    async def test_mcp_protocol(self):
        """Test MCP protocol compliance"""
        try:
            # Test MCP protocol handshake
            response = requests.post(f"{self.server_url}/mcp",
                                   json={"jsonrpc": "2.0", "method": "initialize", "id": 1},
                                   timeout=5)

            if response.status_code == 200:
                self.log_test("MCP Protocol", True, "MCP protocol handshake successful")
                return True
            else:
                self.log_test("MCP Protocol", False,
                              f"MCP protocol handshake failed with status {response.status_code}")
                return False
        except Exception as e:
            self.log_test("MCP Protocol", False, f"Error: {e}")
            return False

    async def test_error_handling(self):
        """Test error handling"""
        try:
            # Test error response
            response = requests.post(f"{self.server_url}/mcp",
                                   json={"jsonrpc": "2.0", "method": "invalid_method", "id": 1},
                                   timeout=5)

            if response.status_code == 200:
                data = response.json()
                if "error" in data:
                    self.log_test("Error Handling", True, "Proper error response received")
                    return True
                else:
                    self.log_test("Error Handling", False, "No error in response to invalid method")
                    return False
            else:
                self.log_test("Error Handling", False,
                              f"Unexpected status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Error Handling", False, f"Error: {e}")
            return False

    async def test_specific_integrations(self):
        """Test specific integration functionality"""
        try:
            import sys
            sys.path.insert(0, str(Path(__file__).parent))

            from duckbot.integrations.mcp_server import DuckBotMCPServer

            server = DuckBotMCPServer()

            # Test ByteBot integration
            if 'bytebot' in server.integration_instances:
                bytebot = server.integration_instances['bytebot']
                self.log_test("ByteBot Integration", True, "ByteBot instance created successfully")

            # Test Archon integration
            if 'archon' in server.integration_instances:
                archon = server.integration_instances['archon']
                self.log_test("Archon Integration", True, "Archon instance created successfully")

            # Test WSL integration
            if 'wsl' in server.integration_instances:
                wsl = server.integration_instances['wsl']
                self.log_test("WSL Integration", True, "WSL instance created successfully")

            # Test Cost Tracker integration
            if 'cost_tracker' in server.integration_instances:
                cost_tracker = server.integration_instances['cost_tracker']
                self.log_test("Cost Tracker Integration", True, "Cost Tracker instance created successfully")

            # Test Server Manager integration
            if 'server_manager' in server.integration_instances:
                server_manager = server.integration_instances['server_manager']
                self.log_test("Server Manager Integration", True, "Server Manager instance created successfully")

            return True
        except Exception as e:
            self.log_test("Specific Integrations", False, f"Error: {e}")
            return False

    async def run_all_tests(self):
        """Run all tests"""
        logger.info("=== MCP Server Test Suite ===")

        await self.test_server_connectivity()
        await self.test_tool_registration()
        await self.test_integration_availability()
        await self.test_mcp_protocol()
        await self.test_error_handling()
        await self.test_specific_integrations()

        # Generate test report
        self.generate_test_report()

    def generate_test_report(self):
        """Generate comprehensive test report"""
        logger.info("=== Test Report ===")

        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["status"] == "PASS"])
        failed_tests = len([r for r in self.test_results if r["status"] == "FAIL"])

        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {passed_tests}")
        logger.info(f"Failed: {failed_tests}")
        logger.info(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")

        if failed_tests > 0:
            logger.info("\nFailed Tests:")
            for result in self.test_results:
                if result["status"] == "FAIL":
                    logger.info(f"  - {result['test']}: {result['details']}")

        # Save report to file
        report_path = Path(__file__).parent / "logs" / "mcp_server_test_report.json"
        with open(report_path, 'w') as f:
            json.dump({
                "timestamp": str(asyncio.get_event_loop().time()),
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": (passed_tests/total_tests)*100,
                "results": self.test_results
            }, f, indent=2)

        logger.info(f"Test report saved to: {report_path}")

async def main():
    """Main test function"""
    tester = MCPServerTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())