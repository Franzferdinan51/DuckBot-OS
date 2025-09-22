#!/usr/bin/env python3
"""
Setup script for external MCP servers
Installs and configures external MCP servers for DuckBot
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Any

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ExternalMCPSetup:
    """Setup external MCP servers"""

    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.config_path = self.base_dir / "config" / "enhanced_mcp_config.json"
        self.mcp_servers_dir = self.base_dir / "mcp-servers"
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load enhanced MCP configuration"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Config file not found: {self.config_path}")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file: {e}")
            return {}

    async def setup_all_servers(self) -> bool:
        """Setup all external MCP servers"""
        logger.info("Setting up external MCP servers...")

        # Create MCP servers directory
        self.mcp_servers_dir.mkdir(exist_ok=True)

        external_servers = self.config.get("external_mcp_servers", {})

        results = {}
        for server_name, server_config in external_servers.items():
            if server_config.get("enabled", False):
                logger.info(f"Setting up {server_name}...")
                results[server_name] = await self._setup_server(server_name, server_config)

        # Print setup results
        logger.info("\n=== Setup Results ===")
        for server_name, success in results.items():
            status = "✅ Success" if success else "❌ Failed"
            logger.info(f"{server_name}: {status}")

        return all(results.values())

    async def _setup_server(self, server_name: str, server_config: Dict[str, Any]) -> bool:
        """Setup a specific external MCP server"""
        category = server_config.get("category", "general")

        try:
            if category == "browser_automation":
                return await self._setup_playwright(server_name, server_config)
            elif category == "system_control":
                return await self._setup_mcpcontrol(server_name, server_config)
            elif category == "filesystem":
                return await self._setup_filesystem_servers(server_name, server_config)
            elif category == "web_search":
                return await self._setup_web_search_servers(server_name, server_config)
            elif category == "development":
                return await self._setup_development_servers(server_name, server_config)
            elif category == "agent_orchestration":
                return await self._setup_agent_orchestration_servers(server_name, server_config)
            else:
                logger.warning(f"Unknown category for {server_name}: {category}")
                return False

        except Exception as e:
            logger.error(f"Error setting up {server_name}: {e}")
            return False

    async def _setup_playwright(self, server_name: str, server_config: Dict[str, Any]) -> bool:
        """Setup Playwright MCP server"""
        logger.info("Setting up Playwright MCP server...")

        try:
            # Check if Node.js is installed
            result = subprocess.run(["node", "--version"], capture_output=True, text=True)
            if result.returncode != 0:
                logger.error("Node.js is not installed. Please install Node.js 18+ first.")
                return False

            # Install Playwright MCP
            logger.info("Installing Playwright MCP...")
            result = subprocess.run(
                ["npm", "install", "-g", "@playwright/mcp@latest"],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                logger.info("Playwright MCP installed successfully")
                return True
            else:
                logger.error(f"Failed to install Playwright MCP: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"Error setting up Playwright: {e}")
            return False

    async def _setup_mcpcontrol(self, server_name: str, server_config: Dict[str, Any]) -> bool:
        """Setup MCPControl server"""
        logger.info("Setting up MCPControl...")

        try:
            # Check if Node.js is installed
            result = subprocess.run(["node", "--version"], capture_output=True, text=True)
            if result.returncode != 0:
                logger.error("Node.js is not installed. Please install Node.js 18+ first.")
                return False

            # Install MCPControl
            logger.info("Installing MCPControl...")
            result = subprocess.run(
                ["npm", "install", "-g", "mcp-control"],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                logger.info("MCPControl installed successfully")
                return True
            else:
                logger.error(f"Failed to install MCPControl: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"Error setting up MCPControl: {e}")
            return False

    async def _setup_filesystem_servers(self, server_name: str, server_config: Dict[str, Any]) -> bool:
        """Setup filesystem MCP servers"""
        logger.info("Setting up filesystem MCP servers...")

        try:
            # Setup standard filesystem server
            if server_name == "filesystem":
                result = subprocess.run(
                    ["npm", "install", "-g", "@modelcontextprotocol/server-filesystem"],
                    capture_output=True,
                    text=True
                )

                if result.returncode != 0:
                    logger.error(f"Failed to install filesystem server: {result.stderr}")
                    return False

                logger.info("Filesystem MCP server installed successfully")
                return True

            # Setup WSL filesystem server
            elif server_name == "wsl_filesystem":
                # Clone and setup WSL filesystem server
                wsl_server_dir = self.mcp_servers_dir / "wsl-filesystem"
                if not wsl_server_dir.exists():
                    subprocess.run([
                        "git", "clone",
                        "https://github.com/webconsulting/mcp-server-wsl-filesystem.git",
                        str(wsl_server_dir)
                    ])

                # Install dependencies
                subprocess.run(["npm", "install"], cwd=wsl_server_dir)
                subprocess.run(["npm", "run", "build"], cwd=wsl_server_dir)

                logger.info("WSL filesystem MCP server setup complete")
                return True

            return False

        except Exception as e:
            logger.error(f"Error setting up filesystem servers: {e}")
            return False

    async def _setup_web_search_servers(self, server_name: str, server_config: Dict[str, Any]) -> bool:
        """Setup web search MCP servers"""
        logger.info("Setting up web search MCP servers...")

        try:
            # Setup Exa search server
            if server_name == "exa_search":
                result = subprocess.run(
                    ["npm", "install", "-g", "@exa/mcp-server"],
                    capture_output=True,
                    text=True
                )

                if result.returncode == 0:
                    logger.info("Exa search MCP server installed successfully")
                    logger.info("Note: Set EXA_API_KEY environment variable for usage")
                    return True
                else:
                    logger.error(f"Failed to install Exa search server: {result.stderr}")
                    return False

            return False

        except Exception as e:
            logger.error(f"Error setting up web search servers: {e}")
            return False

    async def _setup_development_servers(self, server_name: str, server_config: Dict[str, Any]) -> bool:
        """Setup development MCP servers"""
        logger.info("Setting up development MCP servers...")

        try:
            if server_name == "claude_code_tools":
                # Clone and setup Claude Code Tools
                claude_tools_dir = self.mcp_servers_dir / "claude-code-tools"
                if not claude_tools_dir.exists():
                    subprocess.run([
                        "git", "clone",
                        "https://github.com/berch-t/claude-code-tools.git",
                        str(claude_tools_dir)
                    ])

                # Install dependencies
                subprocess.run(["npm", "install"], cwd=claude_tools_dir)
                subprocess.run(["npm", "run", "build"], cwd=claude_tools_dir)

                logger.info("Claude Code Tools MCP server setup complete")
                return True

            return False

        except Exception as e:
            logger.error(f"Error setting up development servers: {e}")
            return False

    async def _setup_agent_orchestration_servers(self, server_name: str, server_config: Dict[str, Any]) -> bool:
        """Setup agent orchestration MCP servers"""
        logger.info("Setting up agent orchestration MCP servers...")

        try:
            if server_name == "mcp_inception":
                # Clone and setup MCP Inception
                inception_dir = self.mcp_servers_dir / "mcp-inception"
                if not inception_dir.exists():
                    subprocess.run([
                        "git", "clone",
                        "https://github.com/tanevanwifferen/mcp-inception.git",
                        str(inception_dir)
                    ])

                # Install dependencies
                subprocess.run(["npm", "install"], cwd=inception_dir)
                subprocess.run(["npm", "run", "build"], cwd=inception_dir)

                # Install mcp-client-cli
                result = subprocess.run(
                    ["npm", "install", "-g", "mcp-client-cli"],
                    capture_output=True,
                    text=True
                )

                if result.returncode == 0:
                    logger.info("MCP Inception setup complete")
                    return True
                else:
                    logger.error(f"Failed to install mcp-client-cli: {result.stderr}")
                    return False

            return False

        except Exception as e:
            logger.error(f"Error setting up agent orchestration servers: {e}")
            return False

    def check_prerequisites(self) -> bool:
        """Check system prerequisites"""
        logger.info("Checking prerequisites...")

        # Check Node.js
        try:
            result = subprocess.run(["node", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                node_version = result.stdout.strip()
                logger.info(f"Node.js version: {node_version}")
            else:
                logger.error("Node.js is not installed. Please install Node.js 18+ first.")
                return False
        except FileNotFoundError:
            logger.error("Node.js is not found. Please install Node.js 18+ first.")
            return False

        # Check npm
        try:
            result = subprocess.run(["npm", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                npm_version = result.stdout.strip()
                logger.info(f"npm version: {npm_version}")
            else:
                logger.error("npm is not available.")
                return False
        except FileNotFoundError:
            logger.error("npm is not found.")
            return False

        # Check Git
        try:
            result = subprocess.run(["git", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                git_version = result.stdout.strip()
                logger.info(f"Git version: {git_version}")
            else:
                logger.error("Git is not available.")
                return False
        except FileNotFoundError:
            logger.error("Git is not found.")
            return False

        # Check Python
        try:
            result = subprocess.run([sys.executable, "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                python_version = result.stdout.strip()
                logger.info(f"Python version: {python_version}")
            else:
                logger.error("Python is not available.")
                return False
        except FileNotFoundError:
            logger.error("Python is not found.")
            return False

        logger.info("All prerequisites are satisfied")
        return True

    def create_environment_variables(self):
        """Create example environment variables"""
        env_example = """# Environment Variables for External MCP Servers
# Copy this file to .env and fill in your API keys

# Exa Search API Key (get from https://exa.ai/api)
EXA_API_KEY=your_exa_api_key_here

# Optional: Add other API keys as needed
# OPENAI_API_KEY=your_openai_api_key_here
# ANTHROPIC_API_KEY=your_anthropic_api_key_here
"""

        env_file = self.base_dir / ".env.example"
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(env_example)

        logger.info(f"Environment variables template created at: {env_file}")

async def main():
    """Main setup function"""
    setup = ExternalMCPSetup()

    # Check prerequisites
    if not setup.check_prerequisites():
        logger.error("Prerequisites not met. Please install required software first.")
        return 1

    # Create environment variables template
    setup.create_environment_variables()

    # Setup all servers
    success = await setup.setup_all_servers()

    if success:
        logger.info("✅ All external MCP servers setup successfully!")
        logger.info("\nNext steps:")
        logger.info("1. Copy .env.example to .env and add your API keys")
        logger.info("2. Run: python duckbot/integrations/enhanced_mcp_manager.py")
        logger.info("3. Configure your Claude Desktop to use the MCP servers")
        return 0
    else:
        logger.error("❌ Some servers failed to setup. Check the logs above.")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))