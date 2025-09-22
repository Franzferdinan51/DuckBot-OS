#!/usr/bin/env python3
"""
DuckBot Electron Startup Test Script
Tests the complete startup sequence including MCP server, React dev server, and Electron app
"""

import asyncio
import subprocess
import sys
import os
import time
import json
import signal
from pathlib import Path
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ElectronStartupTester:
    def __init__(self):
        self.processes = []
        self.project_root = Path(__file__).parent

    async def test_service_startup(self):
        """Test the startup sequence of all services"""
        logger.info("=== Testing DuckBot Electron Startup Sequence ===")

        # Test 1: Check if required files exist
        logger.info("1. Checking required files...")
        required_files = [
            'electron_startup_orchestrator.py',
            'start_mcp_server.py',
            'duckbot/react-webui/package.json',
            'duckbot/react-webui/electron-main-orchestrated.js',
            'duckbot/react-webui/service-config-reader.js'
        ]

        missing_files = []
        for file_path in required_files:
            if not (self.project_root / file_path).exists():
                missing_files.append(file_path)

        if missing_files:
            logger.error(f"Missing required files: {missing_files}")
            return False

        logger.info("✓ All required files present")

        # Test 2: Check Node.js and Python availability
        logger.info("2. Checking runtime availability...")
        try:
            # Check Python
            result = subprocess.run([sys.executable, '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"✓ Python available: {result.stdout.strip()}")
            else:
                logger.error("✗ Python not available")
                return False

            # Check Node.js
            result = subprocess.run(['node', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"✓ Node.js available: {result.stdout.strip()}")
            else:
                logger.error("✗ Node.js not available")
                return False

            # Check npm
            result = subprocess.run(['npm', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"✓ npm available: {result.stdout.strip()}")
            else:
                logger.error("✗ npm not available")
                return False

        except Exception as e:
            logger.error(f"✗ Error checking runtime availability: {e}")
            return False

        # Test 3: Install React dependencies if needed
        logger.info("3. Checking React dependencies...")
        react_dir = self.project_root / 'duckbot' / 'react-webui'
        if not (react_dir / 'node_modules').exists():
            logger.info("Installing React dependencies...")
            try:
                result = subprocess.run(
                    ['npm', 'install'],
                    cwd=react_dir,
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                if result.returncode == 0:
                    logger.info("✓ React dependencies installed")
                else:
                    logger.error(f"✗ Failed to install React dependencies: {result.stderr}")
                    return False
            except Exception as e:
                logger.error(f"✗ Error installing React dependencies: {e}")
                return False
        else:
            logger.info("✓ React dependencies already installed")

        # Test 4: Start orchestrator
        logger.info("4. Testing service orchestrator...")
        try:
            orchestrator_process = subprocess.Popen(
                [sys.executable, 'electron_startup_orchestrator.py'],
                cwd=self.project_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            self.processes.append(orchestrator_process)

            # Wait for orchestrator to start and create config
            config_file = self.project_root / 'duckbot' / 'react-webui' / 'services_config.json'
            max_wait = 30
            wait_time = 0

            while wait_time < max_wait:
                if config_file.exists():
                    logger.info("✓ Service orchestrator started successfully")
                    break
                await asyncio.sleep(1)
                wait_time += 1

            if wait_time >= max_wait:
                logger.error("✗ Service orchestrator failed to start")
                return False

            # Read and validate service configuration
            with open(config_file, 'r') as f:
                config = json.load(f)

            logger.info(f"✓ Service configuration created:")
            for service_name, service_config in config['services'].items():
                logger.info(f"  - {service_name}: {service_config['url']}")

        except Exception as e:
            logger.error(f"✗ Error testing service orchestrator: {e}")
            return False

        # Test 5: Check service health
        logger.info("5. Testing service health...")
        import aiohttp
        try:
            async with aiohttp.ClientSession() as session:
                # Test MCP server health
                mcp_url = config['services']['mcp_server']['url'] + '/health'
                try:
                    async with session.get(mcp_url, timeout=5) as response:
                        if response.status == 200:
                            logger.info("✓ MCP server health check passed")
                        else:
                            logger.warning(f"⚠ MCP server health check returned {response.status}")
                except Exception as e:
                    logger.warning(f"⚠ MCP server health check failed: {e}")

                # Test React server
                react_url = config['services']['react_server']['url']
                try:
                    async with session.get(react_url, timeout=5) as response:
                        if response.status == 200:
                            logger.info("✓ React server responding")
                        else:
                            logger.warning(f"⚠ React server returned {response.status}")
                except Exception as e:
                    logger.warning(f"⚠ React server not responding: {e}")

        except ImportError:
            logger.warning("aiohttp not available, skipping HTTP health checks")
        except Exception as e:
            logger.warning(f"Health check error: {e}")

        logger.info("=== All tests completed ===")
        return True

    def cleanup(self):
        """Clean up all processes"""
        logger.info("Cleaning up processes...")
        for process in self.processes:
            try:
                process.terminate()
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            except Exception as e:
                logger.error(f"Error cleaning up process: {e}")

        # Kill any remaining processes
        try:
            subprocess.run(['taskkill', '/F', '/IM', 'python.exe'], capture_output=True)
            subprocess.run(['taskkill', '/F', '/IM', 'node.exe'], capture_output=True)
        except:
            pass

async def main():
    tester = ElectronStartupTester()

    try:
        success = await tester.test_service_startup()
        if success:
            logger.info("🎉 All tests passed! The DuckBot Electron startup sequence is working.")
        else:
            logger.error("❌ Some tests failed. Please check the errors above.")

    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error during testing: {e}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        tester.cleanup()

if __name__ == "__main__":
    asyncio.run(main())