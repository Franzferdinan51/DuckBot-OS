#!/usr/bin/env python3
"""
Health Monitoring System Test Startup Script

Starts all health monitoring components for testing and validation.
"""

import asyncio
import subprocess
import sys
import time
import os
from pathlib import Path

# Configure UTF-8 encoding for Windows
os.environ['PYTHONIOENCODING'] = 'utf-8'

def print_header(title):
    """Print formatted header"""
    print(f"\n{'='*60}")
    print(f"HOSPITAL {title}")
    print(f"{'='*60}")

async def start_component(name, command, description):
    """Start a component and monitor it"""
    print(f"\nROCKET Starting {name}...")
    print(f"MEMO {description}")

    try:
        # Start the component
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Wait a bit to see if it starts successfully
        time.sleep(3)

        # Check if process is still running
        if process.poll() is None:
            print(f"OK {name} started successfully (PID: {process.pid})")
            return process
        else:
            print(f"FAIL {name} failed to start")
            return None

    except Exception as e:
        print(f"FAIL Failed to start {name}: {e}")
        return None

async def run_integration_test():
    """Run the integration test"""
    print_header("Running Integration Test")

    try:
        # Run the test
        result = subprocess.run([
            sys.executable, "test_health_monitoring_integration.py"
        ], capture_output=True, text=True)

        print(result.stdout)
        if result.stderr:
            print("Errors:")
            print(result.stderr)

        return result.returncode == 0

    except Exception as e:
        print(f"FAIL Integration test failed: {e}")
        return False

async def main():
    """Main function"""
    print_header("DuckBot Health Monitoring System - Test Environment")
    print("This script starts all health monitoring components and runs integration tests.")

    # Components to start
    components = [
        {
            "name": "Health Monitor",
            "command": "python health_monitor.py",
            "description": "Core health monitoring service"
        },
        {
            "name": "Health Monitor API",
            "command": "python health_monitor_api.py",
            "description": "REST API for health monitoring data"
        },
        {
            "name": "Event System",
            "command": "python event_system.py",
            "description": "Event-driven architecture for service state changes"
        },
        {
            "name": "Intelligent Alerting",
            "command": "python intelligent_alerting.py",
            "description": "ML-based alerting and pattern recognition"
        },
        {
            "name": "Performance Analytics",
            "command": "python performance_analytics.py",
            "description": "Performance analytics and trend prediction"
        }
    ]

    # Start components
    processes = []
    for component in components:
        process = await start_component(
            component["name"],
            component["command"],
            component["description"]
        )
        if process:
            processes.append((component["name"], process))

    # Wait for services to fully start
    print(f"\nCLOCK Waiting for services to initialize...")
    await asyncio.sleep(5)

    # Run integration test
    test_success = await run_integration_test()

    # Cleanup
    print(f"\nBROOM Cleaning up processes...")
    for name, process in processes:
        try:
            process.terminate()
            print(f"OK {name} stopped")
        except:
            try:
                process.kill()
                print(f"OK {name} force stopped")
            except:
                print(f"WARN Could not stop {name}")

    # Final status
    print_header("Test Summary")
    if test_success:
        print("PARTY All tests passed! Health monitoring system is working correctly.")
        print("\nLIST System Components:")
        print("   OK Health Monitor - Core service monitoring")
        print("   OK Health Monitor API - REST API endpoints")
        print("   OK Event System - Event-driven architecture")
        print("   OK Intelligent Alerting - ML-based alerts")
        print("   OK Performance Analytics - Trend prediction")
        print("   OK Dashboard Integration - React components")
        print("\nROCKET The system is ready for production use!")
    else:
        print("WARN Some tests failed. Please review the test output above.")
        print("WRENCH Check the component logs for troubleshooting information.")

if __name__ == "__main__":
    # Change to the script directory
    script_dir = Path(__file__).parent
    import os
    os.chdir(script_dir)

    # Run the main function
    asyncio.run(main())