#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DuckBot UI-TARS Integration
ByteDance UI-TARS-desktop integration for advanced GUI automation
https://github.com/bytedance/UI-TARS-desktop
"""

import os
import sys
import json
import asyncio
import logging
import subprocess
import tempfile
import base64
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import requests
import time
from pathlib import Path

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger(__name__)

class UIModelProvider(Enum):
    """Supported UI model providers"""
    VOLCENGINE = "volcengine"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL = "local"

@dataclass
class UITarsConfig:
    """Configuration for UI-TARS integration"""
    provider: UIModelProvider = UIModelProvider.VOLCENGINE
    model: str = "doubao-1-5-thinking-vision-pro-250428"
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    max_steps: int = 50
    confidence_threshold: float = 0.8
    enable_vision: bool = True
    save_screenshots: bool = True
    screenshot_dir: str = "logs/ui_tars_screenshots"

class UITarsIntegration:
    """UI-TARS Desktop Automation Integration"""

    def __init__(self, config: Optional[UITarsConfig] = None):
        self.config = config or UITarsConfig()
        self.is_installed = False
        self.agent_process = None
        self.session_active = False
        self.current_task = None
        self.screenshot_count = 0

        # Create screenshot directory
        os.makedirs(self.config.screenshot_dir, exist_ok=True)

        # Check if UI-TARS is installed
        self._check_installation()

    def _check_installation(self):
        """Check if UI-TARS CLI is installed"""
        try:
            result = subprocess.run(
                ["agent-tars", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                self.is_installed = True
                logger.info(f"UI-TARS CLI found: {result.stdout.strip()}")
            else:
                logger.warning("UI-TARS CLI not found or not working properly")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            logger.warning("UI-TARS CLI not installed")
            self.is_installed = False

    async def install_ui_tars(self):
        """Install UI-TARS CLI if not present"""
        if self.is_installed:
            return True

        logger.info("Installing UI-TARS CLI...")
        try:
            result = subprocess.run(
                ["npm", "install", "@agent-tars/cli@latest", "-g"],
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )

            if result.returncode == 0:
                self.is_installed = True
                logger.info("UI-TARS CLI installed successfully")
                return True
            else:
                logger.error(f"Failed to install UI-TARS: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Error installing UI-TARS: {e}")
            return False

    async def start_session(self):
        """Start UI-TARS agent session"""
        if not self.is_installed:
            success = await self.install_ui_tars()
            if not success:
                raise RuntimeError("Failed to install UI-TARS")

        if self.session_active:
            logger.warning("Session already active")
            return True

        try:
            # Build command arguments
            cmd = ["agent-tars"]

            # Add provider and model
            cmd.extend(["--provider", self.config.provider.value])
            cmd.extend(["--model", self.config.model])

            # Add API key if provided
            if self.config.api_key:
                cmd.extend(["--apiKey", self.config.api_key])

            # Add configuration options
            cmd.extend(["--maxSteps", str(self.config.max_steps)])
            cmd.extend(["--confidence", str(self.config.confidence_threshold)])

            if self.config.enable_vision:
                cmd.append("--enableVision")

            # Start the agent process
            self.agent_process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            self.session_active = True
            logger.info("UI-TARS session started successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to start UI-TARS session: {e}")
            return False

    async def stop_session(self):
        """Stop UI-TARS agent session"""
        if not self.session_active:
            return True

        try:
            if self.agent_process:
                self.agent_process.terminate()
                await self.agent_process.wait()
                self.agent_process = None

            self.session_active = False
            logger.info("UI-TARS session stopped")
            return True

        except Exception as e:
            logger.error(f"Error stopping UI-TARS session: {e}")
            return False

    async def execute_command(self, command: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute a UI automation command"""
        if not self.session_active:
            success = await self.start_session()
            if not success:
                return {"success": False, "error": "Failed to start UI-TARS session"}

        try:
            # Prepare command with context
            full_command = self._prepare_command(command, context)

            # Send command to agent
            if self.agent_process and self.agent_process.stdin:
                self.agent_process.stdin.write(f"{full_command}\n".encode())
                await self.agent_process.stdin.drain()

            # Read response
            response = await self._read_response()

            # Save screenshot if enabled
            if self.config.save_screenshots and "screenshot" in response:
                await self._save_screenshot(response["screenshot"])

            return response

        except Exception as e:
            logger.error(f"Error executing command: {e}")
            return {"success": False, "error": str(e)}

    def _prepare_command(self, command: str, context: Optional[Dict] = None) -> str:
        """Prepare command with context"""
        if not context:
            return command

        # Add context information to the command
        context_info = []
        if "window" in context:
            context_info.append(f"Window: {context['window']}")
        if "application" in context:
            context_info.append(f"Application: {context['application']}")
        if "current_screen" in context:
            context_info.append(f"Current screen: {context['current_screen']}")

        if context_info:
            return f"{command} (Context: {' | '.join(context_info)})"

        return command

    async def _read_response(self) -> Dict[str, Any]:
        """Read response from UI-TARS agent"""
        if not self.agent_process or not self.agent_process.stdout:
            return {"success": False, "error": "No agent process running"}

        try:
            # Read response line by line
            response_lines = []
            while True:
                line = await self.agent_process.stdout.readline()
                if not line:
                    break

                line_text = line.decode().strip()
                if line_text:
                    response_lines.append(line_text)

                    # Check for end of response marker
                    if line_text.startswith("RESULT:") or line_text.startswith("ERROR:"):
                        break

            # Parse response
            response_text = "\n".join(response_lines)
            return self._parse_response(response_text)

        except Exception as e:
            logger.error(f"Error reading response: {e}")
            return {"success": False, "error": str(e)}

    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """Parse UI-TARS agent response"""
        try:
            # Try to parse as JSON first
            if response_text.startswith("{"):
                return json.loads(response_text)

            # Parse text-based response
            response = {"success": True, "raw_response": response_text}

            # Extract key information
            for line in response_text.split("\n"):
                if line.startswith("RESULT:"):
                    response["result"] = line[7:].strip()
                elif line.startswith("ERROR:"):
                    response["success"] = False
                    response["error"] = line[6:].strip()
                elif line.startswith("SCREENSHOT:"):
                    # Extract base64 screenshot data
                    screenshot_data = line[11:].strip()
                    response["screenshot"] = screenshot_data
                elif line.startswith("ACTION:"):
                    response["action"] = line[7:].strip()
                elif line.startswith("CONFIDENCE:"):
                    try:
                        response["confidence"] = float(line[11:].strip())
                    except ValueError:
                        pass

            return response

        except Exception as e:
            logger.error(f"Error parsing response: {e}")
            return {"success": False, "error": str(e), "raw_response": response_text}

    async def _save_screenshot(self, screenshot_data: str):
        """Save screenshot to file"""
        try:
            self.screenshot_count += 1
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"ui_tars_{timestamp}_{self.screenshot_count}.png"
            filepath = os.path.join(self.config.screenshot_dir, filename)

            # Decode base64 and save
            if screenshot_data.startswith("data:image"):
                # Remove data URL prefix
                screenshot_data = screenshot_data.split(",")[1]

            image_data = base64.b64decode(screenshot_data)
            with open(filepath, "wb") as f:
                f.write(image_data)

            logger.info(f"Screenshot saved: {filepath}")

        except Exception as e:
            logger.error(f"Error saving screenshot: {e}")

    async def take_screenshot(self) -> Dict[str, Any]:
        """Take a screenshot of current screen"""
        return await self.execute_command("take screenshot")

    async def click_element(self, element_description: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Click on a UI element"""
        command = f"click on {element_description}"
        return await self.execute_command(command, context)

    async def type_text(self, text: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Type text using keyboard"""
        command = f"type '{text}'"
        return await self.execute_command(command, context)

    async def open_application(self, app_name: str) -> Dict[str, Any]:
        """Open an application"""
        command = f"open {app_name}"
        context = {"application": app_name}
        return await self.execute_command(command, context)

    async def navigate_to_url(self, url: str) -> Dict[str, Any]:
        """Navigate to a URL in browser"""
        command = f"open browser and navigate to {url}"
        context = {"application": "browser", "url": url}
        return await self.execute_command(command, context)

    async def find_element(self, element_description: str) -> Dict[str, Any]:
        """Find a UI element on screen"""
        command = f"find {element_description}"
        return await self.execute_command(command)

    async def wait_for_element(self, element_description: str, timeout: int = 30) -> Dict[str, Any]:
        """Wait for an element to appear"""
        command = f"wait for {element_description} (timeout: {timeout}s)"
        return await self.execute_command(command)

    async def perform_workflow(self, workflow_steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Perform a multi-step workflow"""
        results = []

        for step in workflow_steps:
            step_type = step.get("type")
            step_params = step.get("params", {})
            context = step.get("context")

            if step_type == "click":
                result = await self.click_element(step_params.get("element"), context)
            elif step_type == "type":
                result = await self.type_text(step_params.get("text"), context)
            elif step_type == "open":
                result = await self.open_application(step_params.get("app"))
            elif step_type == "navigate":
                result = await self.navigate_to_url(step_params.get("url"))
            elif step_type == "wait":
                result = await self.wait_for_element(
                    step_params.get("element"),
                    step_params.get("timeout", 30)
                )
            elif step_type == "screenshot":
                result = await self.take_screenshot()
            else:
                result = {"success": False, "error": f"Unknown step type: {step_type}"}

            results.append({
                "step": step,
                "result": result
            })

            # Stop if a step fails
            if not result.get("success", False):
                break

        return {
            "success": all(r.get("success", False) for r in results),
            "results": results,
            "total_steps": len(workflow_steps),
            "completed_steps": len([r for r in results if r.get("success", False)])
        }

    async def get_screen_info(self) -> Dict[str, Any]:
        """Get current screen information"""
        return await self.execute_command("get screen information")

    async def list_running_applications(self) -> Dict[str, Any]:
        """List currently running applications"""
        return await self.execute_command("list running applications")

    async def close_application(self, app_name: str) -> Dict[str, Any]:
        """Close an application"""
        command = f"close {app_name}"
        context = {"application": app_name}
        return await self.execute_command(command, context)

    def get_status(self) -> Dict[str, Any]:
        """Get current integration status"""
        return {
            "installed": self.is_installed,
            "session_active": self.session_active,
            "config": {
                "provider": self.config.provider.value,
                "model": self.config.model,
                "max_steps": self.config.max_steps,
                "confidence_threshold": self.config.confidence_threshold,
                "enable_vision": self.config.enable_vision
            },
            "screenshot_count": self.screenshot_count,
            "screenshot_dir": self.config.screenshot_dir
        }

# MCP Server Integration Functions
async def ui_tars_execute_command(command: str, context: Optional[Dict] = None) -> Dict[str, Any]:
    """Execute UI-TARS command (MCP integration)"""
    integration = UITarsIntegration()
    return await integration.execute_command(command, context)

async def ui_tars_start_session() -> Dict[str, Any]:
    """Start UI-TARS session (MCP integration)"""
    integration = UITarsIntegration()
    success = await integration.start_session()
    return {"success": success, "status": integration.get_status()}

async def ui_tars_stop_session() -> Dict[str, Any]:
    """Stop UI-TARS session (MCP integration)"""
    integration = UITarsIntegration()
    success = await integration.stop_session()
    return {"success": success, "status": integration.get_status()}

async def ui_tars_take_screenshot() -> Dict[str, Any]:
    """Take screenshot (MCP integration)"""
    integration = UITarsIntegration()
    return await integration.take_screenshot()

async def ui_tars_click_element(element: str, context: Optional[Dict] = None) -> Dict[str, Any]:
    """Click element (MCP integration)"""
    integration = UITarsIntegration()
    return await integration.click_element(element, context)

async def ui_tars_type_text(text: str, context: Optional[Dict] = None) -> Dict[str, Any]:
    """Type text (MCP integration)"""
    integration = UITarsIntegration()
    return await integration.type_text(text, context)

# Main function for testing
async def main():
    """Main function for testing UI-TARS integration"""
    integration = UITarsIntegration()

    print("=== DuckBot UI-TARS Integration Test ===")
    print(f"UI-TARS Installed: {integration.is_installed}")

    if not integration.is_installed:
        print("Installing UI-TARS...")
        success = await integration.install_ui_tars()
        if not success:
            print("Failed to install UI-TARS")
            return

    print("Starting UI-TARS session...")
    success = await integration.start_session()
    if not success:
        print("Failed to start session")
        return

    try:
        # Test basic commands
        print("Taking screenshot...")
        result = await integration.take_screenshot()
        print(f"Screenshot result: {result}")

        print("Getting screen info...")
        result = await integration.get_screen_info()
        print(f"Screen info: {result}")

        print("Listing running applications...")
        result = await integration.list_running_applications()
        print(f"Running applications: {result}")

    finally:
        print("Stopping UI-TARS session...")
        await integration.stop_session()

if __name__ == "__main__":
    asyncio.run(main())