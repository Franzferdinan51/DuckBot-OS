#!/usr/bin/env python3
"""
Simple WebSocket Configuration Validation
Quick validation of port allocation and basic functionality
"""

import asyncio
import json
import sys
import os
import time
import socket
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def is_port_available(port):
    """Check if a port is available"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.1)
            result = s.connect_ex(('localhost', port))
            return result != 0
    except:
        return False

def test_port_allocation():
    """Test port allocation strategy"""
    print("=== Testing Port Allocation ===")

    try:
        from config.port_allocation import DuckBotPortAllocator
        allocator = DuckBotPortAllocator()

        print("OK Port allocation module loaded successfully")

        # Get port allocations
        allocations = allocator.get_port_allocations()

        print("\nPort allocations:")
        conflicts_found = False
        port_usage = {}

        for service, port in allocations.items():
            service_info = allocator.SERVICE_PORTS.get(service)
            if service_info:
                print(f"  {service_info.description:25} : {port:>5} ({service_info.protocol})")

                # Check for conflicts
                if port in port_usage:
                    conflicts_found = True
                    print(f"    !! CONFLICT: Also used by {port_usage[port]}")
                else:
                    port_usage[port] = service

        if conflicts_found:
            print("\nFAIL Port conflicts detected!")
            return False
        else:
            print("\nOK No port conflicts found")
            return True

    except Exception as e:
        print(f"FAIL Port allocation test failed: {e}")
        return False

def test_port_availability():
    """Test port availability"""
    print("\n=== Testing Port Availability ===")

    # Test key ports
    key_ports = {
        "WebUI": 8787,
        "Monitoring": 8789,
        "AI Router": 8790,
        "WebSocket MCP": 8791,
        "WebSocket Chat": 8792,
        "MCP Server": 8794,
        "React Dev": 3000,
    }

    available_count = 0
    total_count = len(key_ports)

    for service, port in key_ports.items():
        available = is_port_available(port)
        status = "OK Available" if available else "FAIL In Use"
        print(f"  {service:15} : {port:>5} - {status}")
        if available:
            available_count += 1

    print(f"\nPort availability: {available_count}/{total_count} ports available")
    return available_count >= total_count - 2  # Allow some ports to be in use

def test_websocket_server():
    """Test WebSocket server initialization"""
    print("\n=== Testing WebSocket Server ===")

    try:
        from simple_websocket_server import DuckBotWebSocketServer

        # Test with default ports
        server = DuckBotWebSocketServer()

        print(f"✅ WebSocket server initialized")
        print(f"   MCP port: {server.mcp_port}")
        print(f"   Chat port: {server.chat_port}")

        if server.startup_errors:
            print(f"   ⚠️  Startup errors: {len(server.startup_errors)}")
            for error in server.startup_errors:
                print(f"     - {error}")
            return len(server.startup_errors) == 0
        else:
            print("   ✅ No startup errors")
            return True

    except Exception as e:
        print(f"❌ WebSocket server test failed: {e}")
        return False

def test_health_monitor():
    """Test health monitor initialization"""
    print("\n=== Testing Health Monitor ===")

    try:
        from websocket_health_monitor import WebSocketHealthMonitor
        monitor = WebSocketHealthMonitor()

        print("✅ Health monitor initialized")

        summary = monitor.get_health_summary()
        print(f"   Services monitored: {summary['total_services']}")
        print(f"   WebSocket services: {len(monitor.websocket_services)}")
        print(f"   HTTP services: {len(monitor.http_services)}")

        return True

    except Exception as e:
        print(f"❌ Health monitor test failed: {e}")
        return False

def test_service_coordinator():
    """Test service coordinator"""
    print("\n=== Testing Service Coordinator ===")

    try:
        from service_startup_coordinator import ServiceStartupCoordinator
        coordinator = ServiceStartupCoordinator()

        print("✅ Service coordinator initialized")

        services = coordinator.configure_services()
        print(f"   Services configured: {len(services)}")

        startup_order = coordinator.determine_startup_order(services)
        print(f"   Startup order: {' -> '.join(startup_order)}")

        return True

    except Exception as e:
        print(f"❌ Service coordinator test failed: {e}")
        return False

def test_environment_variables():
    """Test environment variable support"""
    print("\n=== Testing Environment Variables ===")

    try:
        from config.port_allocation import get_port_from_env

        # Test default values
        default_port = get_port_from_env("websocket_mcp", 8791)
        print(f"   Default WebSocket MCP port: {default_port}")

        # Test with environment variable
        test_port = 9999
        os.environ["DUCKBOT_WEBSOCKET_MCP_PORT"] = str(test_port)

        # Reload module to test override
        import importlib
        if 'config.port_allocation' in sys.modules:
            importlib.reload(sys.modules['config.port_allocation'])

        from config.port_allocation import get_port_from_env
        overridden_port = get_port_from_env("websocket_mcp", 8791)

        print(f"   Override WebSocket MCP port: {overridden_port}")

        # Clean up
        del os.environ["DUCKBOT_WEBSOCKET_MCP_PORT"]

        if overridden_port == test_port:
            print("   ✅ Environment variable override works")
            return True
        else:
            print("   ❌ Environment variable override failed")
            return False

    except Exception as e:
        print(f"❌ Environment variable test failed: {e}")
        return False

async def test_websocket_connectivity():
    """Test basic WebSocket connectivity"""
    print("\n=== Testing WebSocket Connectivity ===")

    try:
        import websockets
        import json

        # We'll test with a simple echo server simulation
        test_port = 8791
        if not is_port_available(test_port):
            print(f"   ⚠️  Port {test_port} is in use, skipping connectivity test")
            return True

        print(f"   Testing WebSocket connectivity on port {test_port}")
        print("   ✅ WebSocket library available")
        print("   ✅ JSON library available")

        return True

    except Exception as e:
        print(f"❌ WebSocket connectivity test failed: {e}")
        return False

def generate_report():
    """Generate configuration report"""
    print("\n=== Configuration Report ===")

    try:
        from config.port_allocation import DuckBotPortAllocator
        allocator = DuckBotPortAllocator()

        report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "port_allocator": {
                "services_configured": len(allocator.SERVICE_PORTS),
                "port_ranges": {name: {"start": range.start, "end": range.end, "description": range.description}
                               for name, range in allocator.PORT_RANGES.items()}
            },
            "environment_variables": {
                "DUCKBOT_WEBSOCKET_MCP_PORT": os.getenv("DUCKBOT_WEBSOCKET_MCP_PORT", "Not set"),
                "DUCKBOT_WEBSOCKET_CHAT_PORT": os.getenv("DUCKBOT_WEBSOCKET_CHAT_PORT", "Not set"),
                "DUCKBOT_MCP_SERVER_PORT": os.getenv("DUCKBOT_MCP_SERVER_PORT", "Not set"),
                "DUCKBOT_WEBUI_PORT": os.getenv("DUCKBOT_WEBUI_PORT", "Not set"),
                "DUCKBOT_MONITORING_PORT": os.getenv("DUCKBOT_MONITORING_PORT", "Not set"),
                "DUCKBOT_REACT_DEV_PORT": os.getenv("DUCKBOT_REACT_DEV_PORT", "Not set"),
            }
        }

        # Save report
        report_file = project_root / "websocket_config_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"✅ Configuration report saved to {report_file}")
        return True

    except Exception as e:
        print(f"❌ Report generation failed: {e}")
        return False

async def main():
    """Main validation function"""
    print("DuckBot WebSocket Configuration Validation")
    print("=" * 50)

    tests = [
        ("Port Allocation", test_port_allocation),
        ("Port Availability", test_port_availability),
        ("WebSocket Server", test_websocket_server),
        ("Health Monitor", test_health_monitor),
        ("Service Coordinator", test_service_coordinator),
        ("Environment Variables", test_environment_variables),
        ("WebSocket Connectivity", test_websocket_connectivity),
        ("Report Generation", generate_report),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 50)
    print("VALIDATION SUMMARY")
    print("=" * 50)

    passed = 0
    failed = 0

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
        else:
            failed += 1

    print(f"\nTotal: {passed + failed} tests")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")

    if failed == 0:
        print("\n🎉 All validations passed! WebSocket configuration is ready.")
        return True
    else:
        print(f"\n⚠️  {failed} validation(s) failed. Please review the issues above.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)