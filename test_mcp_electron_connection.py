#!/usr/bin/env python3
"""
Test script to simulate Electron launcher MCP connection attempts
and debug HTTP 426 (Upgrade Required) errors
"""

import asyncio
import json
import logging
import requests
import websockets
from typing import Dict, Any

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MCPConnectionTester:
    """Test MCP server connection methods"""

    def __init__(self, host: str = "127.0.0.1", port: int = 8790):
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"

    def test_http_connection(self) -> Dict[str, Any]:
        """Test basic HTTP connection"""
        logger.info("Testing basic HTTP connection...")
        try:
            response = requests.get(f"{self.base_url}/", timeout=5)
            return {
                "method": "GET",
                "url": f"{self.base_url}/",
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "content": response.text[:500],
                "success": response.status_code < 400
            }
        except Exception as e:
            return {"method": "GET", "error": str(e), "success": False}

    def test_http_with_upgrade_headers(self) -> Dict[str, Any]:
        """Test HTTP with WebSocket upgrade headers (simulating Electron)"""
        logger.info("Testing HTTP with WebSocket upgrade headers...")
        try:
            headers = {
                "Connection": "Upgrade",
                "Upgrade": "websocket",
                "Sec-WebSocket-Version": "13",
                "Sec-WebSocket-Key": "dGhlIHNhbXBsZSBub25jZQ=="
            }
            response = requests.get(f"{self.base_url}/", headers=headers, timeout=5)
            return {
                "method": "GET with upgrade headers",
                "url": f"{self.base_url}/",
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "content": response.text[:500],
                "success": response.status_code < 400
            }
        except Exception as e:
            return {"method": "GET with upgrade headers", "error": str(e), "success": False}

    def test_tools_endpoint(self) -> Dict[str, Any]:
        """Test MCP tools endpoint"""
        logger.info("Testing tools endpoint...")
        try:
            response = requests.get(f"{self.base_url}/tools", timeout=5)
            return {
                "method": "GET",
                "url": f"{self.base_url}/tools",
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "content_length": len(response.content),
                "success": response.status_code < 400
            }
        except Exception as e:
            return {"method": "GET tools", "error": str(e), "success": False}

    def test_tool_execution(self) -> Dict[str, Any]:
        """Test tool execution via HTTP POST"""
        logger.info("Testing tool execution...")
        try:
            response = requests.post(
                f"{self.base_url}/tools/system_status",
                json={},
                timeout=5
            )
            return {
                "method": "POST",
                "url": f"{self.base_url}/tools/system_status",
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "content": response.text[:500],
                "success": response.status_code < 400
            }
        except Exception as e:
            return {"method": "POST tool execution", "error": str(e), "success": False}

    async def test_websocket_connection(self) -> Dict[str, Any]:
        """Test direct WebSocket connection"""
        logger.info("Testing WebSocket connection...")
        try:
            uri = f"ws://{self.host}:{self.port}"
            async with websockets.connect(uri, timeout=5) as websocket:
                # Send a test message
                await websocket.send(json.dumps({"type": "test"}))
                response = await websocket.recv()
                return {
                    "method": "WebSocket",
                    "uri": uri,
                    "success": True,
                    "response": response[:500]
                }
        except Exception as e:
            return {"method": "WebSocket", "error": str(e), "success": False}

    def test_various_user_agents(self) -> Dict[str, Any]:
        """Test with different User-Agent strings"""
        logger.info("Testing with various User-Agent strings...")
        user_agents = [
            "curl/8.15.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Electron/25.0.0",
            "axios/1.6.0",
            "Node.js HTTP client"
        ]

        results = []
        for ua in user_agents:
            try:
                response = requests.get(
                    f"{self.base_url}/tools",
                    headers={"User-Agent": ua},
                    timeout=5
                )
                results.append({
                    "user_agent": ua,
                    "status_code": response.status_code,
                    "success": response.status_code < 400
                })
            except Exception as e:
                results.append({
                    "user_agent": ua,
                    "error": str(e),
                    "success": False
                })

        return {"method": "User-Agent tests", "results": results}

    def analyze_headers(self) -> Dict[str, Any]:
        """Analyze response headers for WebSocket/upgrade requirements"""
        logger.info("Analyzing response headers...")
        try:
            response = requests.get(f"{self.base_url}/", timeout=5)
            headers = dict(response.headers)

            analysis = {
                "has_connection_upgrade": False,
                "has_upgrade_header": False,
                "has_websocket_related": False,
                "content_type": headers.get("content-type", ""),
                "server": headers.get("server", ""),
                "all_headers": headers
            }

            # Check for WebSocket-related headers
            for key, value in headers.items():
                key_lower = key.lower()
                value_lower = value.lower()
                if "connection" in key_lower and "upgrade" in value_lower:
                    analysis["has_connection_upgrade"] = True
                if "upgrade" in key_lower and "websocket" in value_lower:
                    analysis["has_upgrade_header"] = True
                if "websocket" in value_lower:
                    analysis["has_websocket_related"] = True

            return analysis
        except Exception as e:
            return {"method": "Header analysis", "error": str(e)}

    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all connection tests"""
        logger.info("Starting comprehensive MCP connection tests...")

        results = {
            "http_basic": self.test_http_connection(),
            "http_with_upgrade": self.test_http_with_upgrade_headers(),
            "tools_endpoint": self.test_tools_endpoint(),
            "tool_execution": self.test_tool_execution(),
            "user_agents": self.test_various_user_agents(),
            "header_analysis": self.analyze_headers()
        }

        # WebSocket test
        try:
            results["websocket"] = await self.test_websocket_connection()
        except Exception as e:
            results["websocket"] = {"method": "WebSocket", "error": str(e), "success": False}

        return results

    def generate_recommendation(self, results: Dict[str, Any]) -> str:
        """Generate recommendations based on test results"""
        logger.info("Generating connection recommendations...")

        recommendations = []

        # Check if basic HTTP works
        if results["http_basic"].get("success", False):
            recommendations.append("Basic HTTP connection works")

            # Check if tools endpoint works
            if results["tools_endpoint"].get("success", False):
                recommendations.append("MCP tools endpoint accessible")

                # Check if tool execution works
                if results["tool_execution"].get("success", False):
                    recommendations.append("Tool execution via HTTP POST works")
                else:
                    recommendations.append("Tool execution failed - check server configuration")
            else:
                recommendations.append("MCP tools endpoint not accessible")
        else:
            recommendations.append("Basic HTTP connection failed")

        # Check WebSocket upgrade response
        upgrade_result = results["http_with_upgrade"]
        if upgrade_result.get("status_code") == 426:
            recommendations.append("Server returns HTTP 426 for WebSocket upgrade requests")
            recommendations.append("  → Server may require WebSocket for MCP protocol")
            recommendations.append("  → Check if Electron client is trying to use MCP over WebSocket")
        elif upgrade_result.get("success", False):
            recommendations.append("WebSocket upgrade headers accepted")

        # Check header analysis
        header_analysis = results["header_analysis"]
        if header_analysis.get("has_connection_upgrade") or header_analysis.get("has_upgrade_header"):
            recommendations.append("Server headers indicate WebSocket support required")

        # Check WebSocket test
        websocket_result = results.get("websocket", {})
        if websocket_result.get("success", False):
            recommendations.append("Direct WebSocket connection works")
        else:
            recommendations.append("Direct WebSocket connection failed")

        # Final recommendation
        if results["tools_endpoint"].get("success", False) and results["tool_execution"].get("success", False):
            recommendations.append("\nRECOMMENDATION:")
            recommendations.append("The MCP server is working correctly via HTTP REST API.")
            recommendations.append("The HTTP 426 error occurs when trying to upgrade to WebSocket.")
            recommendations.append("Electron client should:")
            recommendations.append("1. Use HTTP REST endpoints for MCP operations")
            recommendations.append("2. Connect to /tools endpoint for tool discovery")
            recommendations.append("3. Use POST requests to /tools/{tool_name} for execution")
            recommendations.append("4. Avoid WebSocket upgrade requests")
        else:
            recommendations.append("\nServer appears to have connectivity issues")

        return "\n".join(recommendations)

async def main():
    """Main test function"""
    tester = MCPConnectionTester()

    # Run all tests
    results = await tester.run_all_tests()

    # Print results
    print("\n" + "="*60)
    print("MCP CONNECTION TEST RESULTS")
    print("="*60)

    for test_name, result in results.items():
        print(f"\n{test_name.upper()}:")
        if isinstance(result, dict):
            for key, value in result.items():
                if key != "all_headers":  # Skip verbose headers
                    print(f"  {key}: {value}")
        else:
            print(f"  {result}")

    # Generate and print recommendations
    print("\n" + "="*60)
    print("RECOMMENDATIONS")
    print("="*60)
    recommendations = tester.generate_recommendation(results)
    print(recommendations)

if __name__ == "__main__":
    asyncio.run(main())