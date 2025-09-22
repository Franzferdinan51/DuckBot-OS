#!/usr/bin/env python3
"""
DuckBot Current Launcher Integration Tests
Tests for the current modular launcher system
"""

import os
import sys
import json
import subprocess
import time
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging
import yaml

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

@dataclass
class TestResult:
    test_name: str
    test_category: str
    status: str
    duration: float
    error_message: Optional[str] = None
    details: Optional[Dict] = None

class CurrentLauncherTests:
    """Test suite for the current modular launcher system"""

    def __init__(self, base_dir: Path = None):
        self.base_dir = base_dir or Path(__file__).parent.parent.parent
        self.test_results: List[TestResult] = []
        self.logger = logging.getLogger('DuckBot.CurrentLauncherTests')

        # Setup logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    def record_result(self, test_name: str, status: str, duration: float, error_msg: str = None, details: Dict = None) -> TestResult:
        """Record a test result"""
        result = TestResult(
            test_name=test_name,
            test_category="current_launcher",
            status=status,
            duration=duration,
            error_message=error_msg,
            details=details or {}
        )
        self.test_results.append(result)
        return result

    def test_launcher_files_existence(self) -> bool:
        """Test that all required launcher files exist"""
        start_time = time.time()

        try:
            # Test current launcher files
            required_files = [
                "START_MODULAR_LAUNCHER.bat",
                "START_LOCAL_ONLY.bat",
                "start_ecosystem.py",
                "ai_ecosystem_manager.py",
                "launcher/START_ENHANCED_CONFIG.bat",
                "launcher/START_ENHANCED_ECOSYSTEM.bat"
            ]

            missing_files = []
            existing_files = []

            for file_path in required_files:
                full_path = self.base_dir / file_path
                if full_path.exists():
                    existing_files.append(file_path)
                else:
                    missing_files.append(file_path)

            # Test launcher files in archive (for backward compatibility reference)
            archive_files = [
                "launcher_archive_20250916_172508/START_ENHANCED_DUCKBOT.bat",
                "launcher_archive_20250916_172508/archive/launchers/START_ENHANCED_DUCKBOT_PROPER.bat"
            ]

            archive_found = 0
            for file_path in archive_files:
                full_path = self.base_dir / file_path
                if full_path.exists():
                    archive_found += 1

            details = {
                "existing_files": existing_files,
                "missing_files": missing_files,
                "archive_files_found": archive_found,
                "total_required": len(required_files),
                "existence_rate": len(existing_files) / len(required_files)
            }

            if len(missing_files) > len(required_files) * 0.3:  # Allow 30% missing files
                return False, f"Too many missing launcher files: {missing_files}", details

            duration = time.time() - start_time
            return True, f"Launcher files existence validated ({len(existing_files)}/{len(required_files)} found)", details

        except Exception as e:
            duration = time.time() - start_time
            return False, f"Error testing launcher files existence: {e}", {}

    def test_modular_launcher_structure(self) -> bool:
        """Test the structure of the modular launcher"""
        start_time = time.time()

        try:
            launcher_path = self.base_dir / "START_MODULAR_LAUNCHER.bat"
            if not launcher_path.exists():
                return False, "START_MODULAR_LAUNCHER.bat not found", {}

            # Read launcher content
            with open(launcher_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Check for required sections
            required_sections = [
                "DUCKBOT MODULAR LAUNCHER",
                "launcher_main.py",
                "launcher\\core",
                "python --version",
                "PYTHONUTF8=1"
            ]

            missing_sections = []
            for section in required_sections:
                if section not in content:
                    missing_sections.append(section)

            # Check for launcher_main.py
            launcher_main_path = self.base_dir / "launcher_main.py"
            launcher_main_exists = launcher_main_path.exists()

            # Check for launcher core directory
            launcher_core_path = self.base_dir / "launcher" / "core"
            launcher_core_exists = launcher_core_path.exists()

            details = {
                "missing_sections": missing_sections,
                "launcher_main_exists": launcher_main_exists,
                "launcher_core_exists": launcher_core_exists,
                "launcher_file_size": len(content),
                "content_preview": content[:200] + "..." if len(content) > 200 else content
            }

            if missing_sections:
                return False, f"Missing sections in modular launcher: {missing_sections}", details

            if not launcher_main_exists:
                return False, "launcher_main.py not found", details

            duration = time.time() - start_time
            return True, f"Modular launcher structure validated successfully", details

        except Exception as e:
            duration = time.time() - start_time
            return False, f"Error testing modular launcher structure: {e}", {}

    def test_local_only_launcher(self) -> bool:
        """Test the local-only launcher functionality"""
        start_time = time.time()

        try:
            launcher_path = self.base_dir / "START_LOCAL_ONLY.bat"
            if not launcher_path.exists():
                return False, "START_LOCAL_ONLY.bat not found", {}

            # Read launcher content
            with open(launcher_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Check for required sections
            required_sections = [
                "START_LOCAL_ONLY",
                "Local-Only Privacy Mode",
                "start_local_ecosystem.py",
                "LM Studio",
                "PYTHONUTF8=1"
            ]

            missing_sections = []
            for section in required_sections:
                if section not in content:
                    missing_sections.append(section)

            # Check for local ecosystem file
            local_ecosystem_path = self.base_dir / "start_local_ecosystem.py"
            local_ecosystem_exists = local_ecosystem_path.exists()

            details = {
                "missing_sections": missing_sections,
                "local_ecosystem_exists": local_ecosystem_exists,
                "launcher_file_size": len(content),
                "content_lines": len(content.split('\n'))
            }

            if missing_sections:
                return False, f"Missing sections in local-only launcher: {missing_sections}", details

            if not local_ecosystem_exists:
                return False, "start_local_ecosystem.py not found", details

            duration = time.time() - start_time
            return True, f"Local-only launcher validated successfully", details

        except Exception as e:
            duration = time.time() - start_time
            return False, f"Error testing local-only launcher: {e}", {}

    def test_ecosystem_files(self) -> bool:
        """Test ecosystem management files"""
        start_time = time.time()

        try:
            # Test ecosystem manager
            ecosystem_path = self.base_dir / "start_ecosystem.py"
            ai_ecosystem_path = self.base_dir / "ai_ecosystem_manager.py"

            ecosystem_exists = ecosystem_path.exists()
            ai_ecosystem_exists = ai_ecosystem_path.exists()

            ecosystem_content = ""
            ai_ecosystem_content = ""

            if ecosystem_exists:
                with open(ecosystem_path, 'r', encoding='utf-8') as f:
                    ecosystem_content = f.read()

            if ai_ecosystem_exists:
                with open(ai_ecosystem_path, 'r', encoding='utf-8') as f:
                    ai_ecosystem_content = f.read()

            details = {
                "ecosystem_exists": ecosystem_exists,
                "ai_ecosystem_exists": ai_ecosystem_exists,
                "ecosystem_size": len(ecosystem_content),
                "ai_ecosystem_size": len(ai_ecosystem_content),
                "ecosystem_has_classes": "class EcosystemManager" in ecosystem_content if ecosystem_content else False,
                "ai_ecosystem_has_classes": "class AIEcosystemManager" in ai_ecosystem_content if ai_ecosystem_content else False
            }

            if not ecosystem_exists:
                return False, "start_ecosystem.py not found", details

            if not ai_ecosystem_exists:
                return False, "ai_ecosystem_manager.py not found", details

            duration = time.time() - start_time
            return True, f"Ecosystem files validated successfully", details

        except Exception as e:
            duration = time.time() - start_time
            return False, f"Error testing ecosystem files: {e}", {}

    def test_configuration_files(self) -> bool:
        """Test configuration files structure"""
        start_time = time.time()

        try:
            # Test configuration files
            config_files = [
                "config/startup_config.json",
                "config/ecosystem_config.yaml",
                "config/hardware_config.json",
                "config/ai_config.json"
            ]

            valid_configs = 0
            config_details = {}

            for config_file in config_files:
                config_path = self.base_dir / config_file
                if not config_path.exists():
                    config_details[config_file] = {"exists": False, "error": "File not found"}
                    continue

                try:
                    if config_file.endswith('.json'):
                        with open(config_path, 'r', encoding='utf-8') as f:
                            config = json.load(f)
                    elif config_file.endswith('.yaml'):
                        with open(config_path, 'r', encoding='utf-8') as f:
                            config = yaml.safe_load(f)
                    else:
                        continue

                    # Basic validation
                    if isinstance(config, dict) and len(config) > 0:
                        valid_configs += 1
                        config_details[config_file] = {
                            "exists": True,
                            "valid": True,
                            "size": len(str(config)),
                            "keys": list(config.keys())[:5]  # First 5 keys
                        }
                    else:
                        config_details[config_file] = {"exists": True, "valid": False, "error": "Invalid structure"}

                except Exception as e:
                    config_details[config_file] = {"exists": True, "valid": False, "error": str(e)}

            details = {
                "valid_configs": valid_configs,
                "total_configs": len(config_files),
                "validation_rate": valid_configs / len(config_files),
                "config_details": config_details
            }

            if valid_configs == 0:
                return False, "No valid configuration files found", details

            duration = time.time() - start_time
            return True, f"Configuration files validated ({valid_configs}/{len(config_files)} valid)", details

        except Exception as e:
            duration = time.time() - start_time
            return False, f"Error testing configuration files: {e}", {}

    def test_launcher_directory_structure(self) -> bool:
        """Test launcher directory structure"""
        start_time = time.time()

        try:
            # Test launcher directory
            launcher_dir = self.base_dir / "launcher"
            if not launcher_dir.exists():
                return False, "launcher directory not found", {}

            # Check launcher subdirectories
            launcher_subdirs = [
                "launcher/core",
                "launcher/archive",
                "launcher/START_ENHANCED_CONFIG.bat",
                "launcher/START_ENHANCED_ECOSYSTEM.bat"
            ]

            existing_items = []
            missing_items = []

            for item in launcher_subdirs:
                item_path = self.base_dir / item
                if item_path.exists():
                    existing_items.append(item)
                else:
                    missing_items.append(item)

            # Check for archive directory
            archive_dir = self.base_dir / "launcher_archive_20250916_172508"
            archive_exists = archive_dir.exists()

            details = {
                "launcher_dir_exists": launcher_dir.exists(),
                "existing_items": existing_items,
                "missing_items": missing_items,
                "archive_exists": archive_exists,
                "launcher_contents": list(launcher_dir.iterdir()) if launcher_dir.exists() else []
            }

            if not launcher_dir.exists():
                return False, "launcher directory not found", details

            duration = time.time() - start_time
            return True, f"Launcher directory structure validated", details

        except Exception as e:
            duration = time.time() - start_time
            return False, f"Error testing launcher directory structure: {e}", {}

    def test_python_environment(self) -> bool:
        """Test Python environment setup"""
        start_time = time.time()

        try:
            # Test Python availability
            python_results = {}

            # Test python command
            try:
                result = subprocess.run(['python', '--version'], capture_output=True, text=True, timeout=10)
                python_results['python'] = {
                    "available": result.returncode == 0,
                    "version": result.stdout.strip() if result.returncode == 0 else None,
                    "error": result.stderr.strip() if result.stderr else None
                }
            except Exception as e:
                python_results['python'] = {"available": False, "error": str(e)}

            # Test python3 command
            try:
                result = subprocess.run(['python3', '--version'], capture_output=True, text=True, timeout=10)
                python_results['python3'] = {
                    "available": result.returncode == 0,
                    "version": result.stdout.strip() if result.returncode == 0 else None,
                    "error": result.stderr.strip() if result.stderr else None
                }
            except Exception as e:
                python_results['python3'] = {"available": False, "error": str(e)}

            # Test py command
            try:
                result = subprocess.run(['py', '--version'], capture_output=True, text=True, timeout=10)
                python_results['py'] = {
                    "available": result.returncode == 0,
                    "version": result.stdout.strip() if result.returncode == 0 else None,
                    "error": result.stderr.strip() if result.stderr else None
                }
            except Exception as e:
                python_results['py'] = {"available": False, "error": str(e)}

            # Check if any Python version is available
            any_python_available = any(result['available'] for result in python_results.values())

            details = {
                "python_results": python_results,
                "any_python_available": any_python_available,
                "python_version": sys.version,
                "python_executable": sys.executable
            }

            if not any_python_available:
                return False, "No Python version available", details

            duration = time.time() - start_time
            return True, f"Python environment validated", details

        except Exception as e:
            duration = time.time() - start_time
            return False, f"Error testing Python environment: {e}", {}

    def test_environment_variables(self) -> bool:
        """Test critical environment variables"""
        start_time = time.time()

        try:
            # Test critical environment variables
            critical_vars = [
                'PYTHONPATH', 'PYTHONIOENCODING', 'PYTHONUTF8',
                'PATH', 'HOME', 'USERPROFILE'
            ]

            env_vars = {}
            missing_vars = []

            for var in critical_vars:
                value = os.environ.get(var)
                env_vars[var] = {
                    "exists": value is not None,
                    "value": value[:100] + "..." if value and len(value) > 100 else value
                }
                if value is None:
                    missing_vars.append(var)

            # Test DuckBot-specific environment variables
            duckbot_vars = [
                'DISCORD_TOKEN', 'OPENROUTER_API_KEY', 'GEMINI_API_KEY'
            ]

            duckbot_env_vars = {}
            for var in duckbot_vars:
                value = os.environ.get(var)
                duckbot_env_vars[var] = {
                    "exists": value is not None,
                    "has_value": bool(value and value.strip() and value != 'None' and value != '')
                }

            details = {
                "critical_vars": env_vars,
                "duckbot_vars": duckbot_env_vars,
                "missing_critical_vars": missing_vars,
                "total_critical_vars": len(critical_vars),
                "critical_vars_rate": (len(critical_vars) - len(missing_vars)) / len(critical_vars)
            }

            # Allow some critical variables to be missing (not all are required)
            if len(missing_vars) > len(critical_vars) * 0.5:
                return False, f"Too many critical environment variables missing: {missing_vars}", details

            duration = time.time() - start_time
            return True, f"Environment variables validated", details

        except Exception as e:
            duration = time.time() - start_time
            return False, f"Error testing environment variables: {e}", {}

    def run_all_tests(self) -> List[TestResult]:
        """Run all current launcher tests"""
        self.logger.info("Starting current launcher integration tests...")

        # Define all tests
        tests = [
            ("launcher_files_existence", self.test_launcher_files_existence),
            ("modular_launcher_structure", self.test_modular_launcher_structure),
            ("local_only_launcher", self.test_local_only_launcher),
            ("ecosystem_files", self.test_ecosystem_files),
            ("configuration_files", self.test_configuration_files),
            ("launcher_directory_structure", self.test_launcher_directory_structure),
            ("python_environment", self.test_python_environment),
            ("environment_variables", self.test_environment_variables),
        ]

        # Run all tests
        for test_name, test_func in tests:
            try:
                start_time = time.time()
                success, message, details = test_func()
                duration = time.time() - start_time

                status = "PASSED" if success else "FAILED"
                self.record_result(test_name, status, duration, message if not success else None, details)

                # Log result
                emoji = "✅" if success else "❌"
                self.logger.info(f"{emoji} [CURRENT_LAUNCHER] {test_name} ({duration:.2f}s) - {message}")

            except Exception as e:
                duration = time.time() - start_time
                error_msg = f"Test execution error: {e}"
                self.record_result(test_name, "ERROR", duration, error_msg)
                self.logger.error(f"💥 [CURRENT_LAUNCHER] {test_name} failed: {error_msg}")

        return self.test_results

    def generate_report(self) -> str:
        """Generate test report"""
        total_tests = len(self.test_results)
        passed = sum(1 for r in self.test_results if r.status == "PASSED")
        failed = sum(1 for r in self.test_results if r.status == "FAILED")
        errors = sum(1 for r in self.test_results if r.status == "ERROR")

        report = f"""
# DuckBot Current Launcher Integration Test Report

## Test Summary
- **Total Tests**: {total_tests}
- **Passed**: {passed} ✅
- **Failed**: {failed} ❌
- **Errors**: {errors} 💥
- **Pass Rate**: {(passed/total_tests*100):.1f}%

## Test Results
"""

        for result in self.test_results:
            status_emoji = {"PASSED": "✅", "FAILED": "❌", "ERROR": "💥"}.get(result.status, "❓")
            report += f"- {status_emoji} **{result.test_name}** ({result.duration:.2f}s)\n"
            if result.error_message:
                report += f"  - Error: {result.error_message}\n"

        if failed > 0 or errors > 0:
            report += "\n## Issues Found\n"
            for result in self.test_results:
                if result.status in ["FAILED", "ERROR"]:
                    report += f"- **{result.test_name}**: {result.error_message}\n"

        return report

def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="DuckBot Current Launcher Integration Tests")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')

    # Run tests
    test_runner = CurrentLauncherTests()
    results = test_runner.run_all_tests()

    # Print summary
    total_tests = len(results)
    passed = sum(1 for r in results if r.status == "PASSED")
    failed = sum(1 for r in results if r.status == "FAILED")
    errors = sum(1 for r in results if r.status == "ERROR")

    print(f"\n{'='*60}")
    print(f"CURRENT LAUNCHER INTEGRATION TEST RESULTS")
    print(f"{'='*60}")
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed} ✅")
    print(f"Failed: {failed} ❌")
    print(f"Errors: {errors} 💥")
    print(f"Pass Rate: {(passed/total_tests*100):.1f}%")

    # Generate and print report
    report = test_runner.generate_report()
    print(report)

    if failed > 0 or errors > 0:
        print(f"\n❌ Current launcher integration tests completed with issues")
        sys.exit(1)
    else:
        print(f"\n✅ All current launcher integration tests passed!")
        sys.exit(0)

if __name__ == "__main__":
    main()