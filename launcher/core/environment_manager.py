#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Environment management module for the modular launcher
"""

import os
import sys
import subprocess
import shutil
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
import sys
from pathlib import Path

# Add launcher directory to Python path for imports
launcher_dir = Path(__file__).parent.parent
sys.path.insert(0, str(launcher_dir))

from models.service_config import EnvironmentConfig

class EnvironmentManager:
    """Manages environment setup and validation"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.project_root = Path(__file__).parent.parent.parent
        self.config = EnvironmentConfig()
        self.environment_status = {}

    def validate_environment(self) -> bool:
        """Validate the runtime environment"""
        self.logger.info("Validating environment...")

        checks = [
            self._check_python,
            self._check_node,
            self._check_dependencies,
            self._check_paths,
            self._check_environment_files
        ]

        all_passed = True
        for check in checks:
            try:
                result = check()
                self.environment_status[result["name"]] = result
                if not result.get("success", False):
                    all_passed = False
                    self.logger.warning(f"Environment check failed: {result.get('message', 'Unknown error')}")
            except Exception as e:
                self.logger.error(f"Environment check error: {e}")
                all_passed = False

        if all_passed:
            self.logger.info("Environment validation passed")
        else:
            self.logger.error("Environment validation failed")

        return all_passed

    def _check_python(self) -> Dict[str, Any]:
        """Check Python installation and version"""
        result = {"name": "python", "success": False, "message": ""}

        if not self.config.python_required:
            result["success"] = True
            result["message"] = "Python not required"
            return result

        try:
            # Try python command
            python_cmd = self._find_python_command()
            if not python_cmd:
                result["message"] = "Python command not found"
                return result

            # Get version
            version_output = subprocess.run(
                [python_cmd, "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if version_output.returncode != 0:
                result["message"] = f"Python version check failed: {version_output.stderr}"
                return result

            version_str = version_output.stdout.strip()
            result["version"] = version_str
            result["command"] = python_cmd

            # Parse version
            version_parts = version_str.replace("Python ", "").split(".")
            if len(version_parts) >= 2:
                major, minor = int(version_parts[0]), int(version_parts[1])
                required_parts = self.config.python_version_min.split(".")
                required_major, required_minor = int(required_parts[0]), int(required_parts[1])

                if major > required_major or (major == required_major and minor >= required_minor):
                    result["success"] = True
                    result["message"] = f"Python {version_str} meets requirement ({self.config.python_version_min}+)"
                else:
                    result["message"] = f"Python {version_str} below required version {self.config.python_version_min}"
            else:
                result["message"] = f"Could not parse Python version: {version_str}"

        except Exception as e:
            result["message"] = f"Python check error: {e}"

        return result

    def _check_node(self) -> Dict[str, Any]:
        """Check Node.js installation if required"""
        result = {"name": "node", "success": False, "message": ""}

        if not self.config.node_required:
            result["success"] = True
            result["message"] = "Node.js not required"
            return result

        try:
            # Check node command
            node_path = shutil.which("node")
            if not node_path:
                result["message"] = "Node.js not found in PATH"
                return result

            # Get version
            version_output = subprocess.run(
                ["node", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if version_output.returncode != 0:
                result["message"] = f"Node.js version check failed: {version_output.stderr}"
                return result

            version_str = version_output.stdout.strip().replace("v", "")
            result["version"] = version_str

            # Parse version
            version_parts = version_str.split(".")
            if len(version_parts) >= 2:
                major, minor = int(version_parts[0]), int(version_parts[1])
                required_parts = self.config.node_version_min.split(".")
                required_major, required_minor = int(required_parts[0]), int(required_parts[1])

                if major > required_major or (major == required_major and minor >= required_minor):
                    result["success"] = True
                    result["message"] = f"Node.js {version_str} meets requirement ({self.config.node_version_min}+)"
                else:
                    result["message"] = f"Node.js {version_str} below required version {self.config.node_version_min}"
            else:
                result["message"] = f"Could not parse Node.js version: {version_str}"

        except Exception as e:
            result["message"] = f"Node.js check error: {e}"

        return result

    def _check_dependencies(self) -> Dict[str, Any]:
        """Check required Python packages"""
        result = {"name": "dependencies", "success": True, "message": "", "packages": {}}

        if not self.config.required_packages:
            result["message"] = "No required packages specified"
            return result

        missing_packages = []
        available_packages = []

        for package in self.config.required_packages:
            try:
                __import__(package)
                available_packages.append(package)
                result["packages"][package] = {"status": "available", "version": "unknown"}
            except ImportError:
                missing_packages.append(package)
                result["packages"][package] = {"status": "missing", "version": "unknown"}

        if missing_packages:
            result["success"] = False
            result["message"] = f"Missing packages: {', '.join(missing_packages)}"
        else:
            result["message"] = f"All required packages available: {', '.join(available_packages)}"

        return result

    def _check_paths(self) -> Dict[str, Any]:
        """Check required paths and directories"""
        result = {"name": "paths", "success": True, "message": "", "paths": {}}

        required_dirs = [
            self.project_root / "duckbot",
            self.project_root / "config",
            self.project_root / "core_ai",
            self.project_root / "logs"
        ]

        missing_dirs = []
        available_dirs = []

        for directory in required_dirs:
            if directory.exists():
                available_dirs.append(str(directory))
                result["paths"][str(directory)] = {"status": "available"}
            else:
                missing_dirs.append(str(directory))
                result["paths"][str(directory)] = {"status": "missing"}

        if missing_dirs:
            result["success"] = False
            result["message"] = f"Missing directories: {', '.join(missing_dirs)}"
        else:
            result["message"] = f"All required directories available: {', '.join(available_dirs)}"

        return result

    def _check_environment_files(self) -> Dict[str, Any]:
        """Check environment configuration files"""
        result = {"name": "environment_files", "success": True, "message": "", "files": {}}

        env_files = self.config.env_files or [".env", "config/.env"]

        missing_files = []
        available_files = []

        for env_file in env_files:
            env_path = self.project_root / env_file
            if env_path.exists():
                available_files.append(env_file)
                result["files"][env_file] = {"status": "available"}
            else:
                missing_files.append(env_file)
                result["files"][env_file] = {"status": "missing"}

        # Environment files are optional, so don't fail if missing
        if missing_files:
            result["message"] = f"Some environment files missing: {', '.join(missing_files)}"
        else:
            result["message"] = f"All environment files available: {', '.join(available_files)}"

        return result

    def _find_python_command(self) -> Optional[str]:
        """Find the best Python command to use"""
        commands_to_try = ["python", "python3", "py", "py -3"]

        for cmd in commands_to_try:
            try:
                result = subprocess.run(
                    cmd.split() + ["--version"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    return cmd
            except (subprocess.TimeoutExpired, FileNotFoundError):
                continue

        return None

    def setup_environment(self) -> bool:
        """Setup the environment with required configurations"""
        self.logger.info("Setting up environment...")

        try:
            # Set environment variables
            os.environ["PYTHONUTF8"] = "1"
            os.environ["PYTHONIOENCODING"] = "utf-8"

            # Add project paths
            project_str = str(self.project_root)
            if project_str not in sys.path:
                sys.path.insert(0, project_str)

            # Add charm tools if available
            charm_path = self.project_root / "tools" / "charm" / "bin" / "win64"
            if charm_path.exists():
                current_path = os.environ.get("PATH", "")
                if str(charm_path) not in current_path:
                    os.environ["PATH"] = f"{charm_path};{current_path}"
                    self.logger.info(f"Added charm tools to PATH: {charm_path}")

            # Load environment files
            self._load_environment_files()

            self.logger.info("Environment setup completed")
            return True

        except Exception as e:
            self.logger.error(f"Environment setup failed: {e}")
            return False

    def _load_environment_files(self):
        """Load environment variables from files"""
        env_files = self.config.env_files or [".env", "config/.env"]

        for env_file in env_files:
            env_path = self.project_root / env_file
            if env_path.exists():
                self.logger.info(f"Loading environment from: {env_path}")
                try:
                    with open(env_path, 'r', encoding='utf-8') as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith('#') and '=' in line:
                                key, value = line.split('=', 1)
                                os.environ[key.strip()] = value.strip()
                except Exception as e:
                    self.logger.warning(f"Failed to load environment file {env_path}: {e}")

    def get_environment_status(self) -> Dict[str, Any]:
        """Get current environment status"""
        return {
            "status": "ready" if all(
                check.get("success", False)
                for check in self.environment_status.values()
            ) else "issues_found",
            "checks": self.environment_status,
            "python_command": self._find_python_command(),
            "working_directory": str(self.project_root)
        }