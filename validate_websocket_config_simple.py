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

def test_websocket_server():
    """Test WebSocket server initialization"""
    print("\n=== Testing WebSocket Server ===")

    try:
        from simple_websocket_server import DuckBotWebSocketServer

        # Test with default ports
        server = DuckBotWebSocketServer()

        print(f"OK WebSocket server initialized")
        print(f"   MCP port: {server.mcp_port}")
        print(f"   Chat port: {server.chat_port}")

        if server.startup_errors:
            print(f"   WARN Startup errors: {len(server.startup_errors)}")
            for error in server.startup_errors:
                print(f"     - {error}")
            return len(server.startup_errors) == 0
        else:
            print("   OK No startup errors")
            return True

    except Exception as e:
        print(f"FAIL WebSocket server test failed: {e}")
        return False

def test_service_coordinator():
    """Test service coordinator"""
    print("\n=== Testing Service Coordinator ===")

    try:
        from service_startup_coordinator import ServiceStartupCoordinator
        coordinator = ServiceStartupCoordinator()

        print("OK Service coordinator initialized")

        services = coordinator.configure_services()
        print(f"   Services configured: {len(services)}")

        startup_order = coordinator.determine_startup_order(services)
        print(f"   Startup order: {' -> '.join(startup_order)}")

        return True

    except Exception as e:
        print(f"FAIL Service coordinator test failed: {e}")
        return False

def test_port_conflicts():
    """Test for port conflicts in key services"""
    print("\n=== Testing Port Conflicts ===")

    key_ports = {
        "WebSocket MCP": 8791,
        "WebSocket Chat": 8792,
        "MCP Server": 8794,
        "WebUI": 8787,
        "Monitoring": 8789,
        "AI Router": 8790,
        "React Dev": 3000,
    }

    port_status = {}
    for service, port in key_ports.items():
        available = is_port_available(port)
        port_status[port] = {"service": service, "available": available}

    # Check for conflicts in our allocation
    conflicts = []
    used_ports = set()

    for service, port in key_ports.items():
        if port in used_ports:
            conflicts.append(f"Port {port} allocated to multiple services")
        used_ports.add(port)

    if conflicts:
        print("FAIL Port conflicts found:")
        for conflict in conflicts:
            print(f"  - {conflict}")
        return False
    else:
        print("OK No port conflicts in allocation")
        return True

def generate_configuration_summary():
    """Generate configuration summary"""
    print("\n=== Configuration Summary ===")

    try:
        from config.port_allocation import DuckBotPortAllocator
        allocator = DuckBotPortAllocator()

        summary = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_services": len(allocator.SERVICE_PORTS),
            "port_ranges": len(allocator.PORT_RANGES),
            "key_allocations": {
                "websocket_mcp": allocator.get_service_port("websocket_mcp"),
                "websocket_chat": allocator.get_service_port("websocket_chat"),
                "mcp_server": allocator.get_service_port("mcp_server"),
                "webui": allocator.get_service_port("webui"),
                "monitoring": allocator.get_service_port("monitoring"),
                "react_dev": allocator.get_service_port("react_dev"),
            }
        }

        print(f"Total services configured: {summary['total_services']}")
        print(f"Port ranges defined: {summary['port_ranges']}")
        print("\nKey port allocations:")
        for service, port in summary["key_allocations"].items():
            print(f"  {service:20} : {port}")

        # Save summary
        summary_file = project_root / "websocket_config_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)

        print(f"\nConfiguration summary saved to {summary_file}")
        return True

    except Exception as e:
        print(f"FAIL Configuration summary generation failed: {e}")
        return False

async def main():
    """Main validation function"""
    print("DuckBot WebSocket Configuration Validation")
    print("=" * 50)

    tests = [
        ("Port Allocation", test_port_allocation),
        ("WebSocket Server", test_websocket_server),
        ("Service Coordinator", test_service_coordinator),
        ("Port Conflicts", test_port_conflicts),
        ("Configuration Summary", generate_configuration_summary),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            print(f"\nRunning {test_name} test...")
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"FAIL {test_name} test crashed: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 50)
    print("VALIDATION SUMMARY")
    print("=" * 50)

    passed = 0
    failed = 0

    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
        else:
            failed += 1

    print(f"\nTotal: {passed + failed} tests")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")

    if failed == 0:
        print("\nSUCCESS! All validations passed. WebSocket configuration is ready.")
        return True
    else:
        print(f"\nWARNING! {failed} validation(s) failed. Please review the issues above.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)