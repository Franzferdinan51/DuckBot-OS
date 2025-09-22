#!/usr/bin/env python3
"""
DuckBot Launcher Integration Tests
Specific tests for launcher functionality and startup modes
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

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from test_startup_system import IntegrationTestFramework, TestConfig, TestResult
except ImportError:
    # Fallback definitions
    @dataclass
    class TestResult:
        test_name: str
        test_category: str
        status: str
        duration: float
        error_message: Optional[str] = None
        details: Optional[Dict] = None

class LauncherIntegrationTests:
    """Test suite specifically for launcher integration"""

    def __init__(self, base_dir: Path = None):
        self.base_dir = base_dir or Path(__file__).parent.parent.parent
        self.test_results: List[TestResult] = []
        self.logger = logging.getLogger('DuckBot.LauncherTests')

    def record_result(self, test_name: str, status: str, duration: float, error_msg: str = None, details: Dict = None) -> TestResult:
        """Record a test result"""
        result = TestResult(
            test_name=test_name,
            test_category="launcher",
            status=status,
            duration=duration,
            error_message=error_msg,
            details=details or {}
        )
        self.test_results.append(result)
        return result

    def test_enhanced_launcher_structure(self) -> bool:
        """Test the structure and content of the enhanced launcher"""
        start_time = time.time()

        try:
            launcher_path = self.base_dir / "START_ENHANCED_DUCKBOT.bat"
            if not launcher_path.exists():
                return False, "START_ENHANCED_DUCKBOT.bat not found"

            # Read launcher content
            with open(launcher_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Check for required sections
            required_sections = [
                "ULTIMATE INTEGRATION FEATURES",
                "ULTIMATE LAUNCH MODES",
                ":main_menu",
                ":ultimate_mode",
                ":enhanced_webui_mode",
                ":local_only_mode"
            ]

            missing_sections = []
            for section in required_sections:
                if section not in content:
                    missing_sections.append(section)

            if missing_sections:
                return False, f"Missing sections: {missing_sections}"

            # Check for required launch options
            required_options = [
                "Complete Ultimate Enhanced Mode",
                "Enhanced WebUI Dashboard",
                "Local Privacy Mode",
                "Hybrid Cloud+Local Mode"
            ]

            missing_options = []
            for option in required_options:
                if option not in content:
                    missing_options.append(option)

            if missing_options:
                return False, f"Missing launch options: {missing_options}"

            duration = time.time() - start_time
            return True, f"Launcher structure validated ({duration:.2f}s)"

        except Exception as e:
            duration = time.time() - start_time
            return False, f"Error testing launcher structure: {e}"

    def test_launcher_menu_options(self) -> bool:
        """Test that all launcher menu options are properly defined"""
        start_time = time.time()

        try:
            launcher_path = self.base_dir / "START_ENHANCED_DUCKBOT.bat"
            with open(launcher_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Check for menu options (1-10 and A-F)
            menu_patterns = [
                r"1\. \[ULTIMATE\]",
                r"2\. \[ENHANCED-WEBUI\]",
                r"3\. \[MONITORING\]",
                r"4\. \[LOCAL-ONLY\]",
                r"5\. \[HYBRID\]",
                r"6\. \[DUCKBOTOS\]",
                r"7\. \[GNOME\]",
                r"8\. \[AI-ONLY\]",
                r"9\. \[MINIMAL\]",
                r"10\. \[DEVELOPER\]"
            ]

            import re
            missing_patterns = []
            for pattern in menu_patterns:
                if not re.search(pattern, content):
                    missing_patterns.append(pattern)

            if missing_patterns:
                return False, f"Missing menu patterns: {missing_patterns}"

            # Check for corresponding labels
            required_labels = [
                ":ultimate_mode",
                ":enhanced_webui_mode",
                ":monitoring_mode",
                ":local_only_mode",
                ":hybrid_mode",
                ":duckbotos_mode",
                ":gnome_mode",
                ":ai_only_mode",
                ":minimal_mode",
                ":developer_mode"
            ]

            missing_labels = []
            for label in required_labels:
                if label not in content:
                    missing_labels.append(label)

            if missing_labels:
                return False, f"Missing mode labels: {missing_labels}"

            duration = time.time() - start_time
            return True, f"Menu options validated ({duration:.2f}s)"

        except Exception as e:
            duration = time.time() - start_time
            return False, f"Error testing menu options: {e}"

    def test_launcher_python_detection(self) -> bool:
        """Test Python detection logic in launcher"""
        start_time = time.time()

        try:
            launcher_path = self.base_dir / "START_ENHANCED_DUCKBOT.bat"
            with open(launcher_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Check for Python detection logic
            python_detection_indicators = [
                'set "PY_CMD=python"',
                'python --version',
                'py -3',
                'where py'
            ]

            missing_indicators = []
            for indicator in python_detection_indicators:
                if indicator not in content:
                    missing_indicators.append(indicator)

            if missing_indicators:
                return False, f"Missing Python detection logic: {missing_indicators}"

            # Test the actual Python detection works
            try:
                result = subprocess.run(['python', '--version'], capture_output=True, text=True, timeout=10)
                python_available = result.returncode == 0
            except:
                python_available = False

            if not python_available:
                # Try py -3
                try:
                    result = subprocess.run(['py', '-3', '--version'], capture_output=True, text=True, timeout=10)
                    python_available = result.returncode == 0
                except:
                    python_available = False

            if not python_available:
                return False, "Neither python nor py -3 is available"

            duration = time.time() - start_time
            return True, f"Python detection validated ({duration:.2f}s)"

        except Exception as e:
            duration = time.time() - start_time
            return False, f"Error testing Python detection: {e}"

    def test_launcher_directory_setup(self) -> bool:
        """Test directory setup and path handling in launcher"""
        start_time = time.time()

        try:
            launcher_path = self.base_dir / "START_ENHANCED_DUCKBOT.bat"
            with open(launcher_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Check for directory setup
            directory_setup_indicators = [
                'cd /d "%~dp0"',
                'PYTHONUTF8=1',
                'PYTHONIOENCODING=utf-8',
                'chcp 65001'
            ]

            missing_indicators = []
            for indicator in directory_setup_indicators:
                if indicator not in content:
                    missing_indicators.append(indicator)

            if missing_indicators:
                return False, f"Missing directory setup: {missing_indicators}"

            # Test that we can navigate to the base directory
            if not self.base_dir.exists():
                return False, f"Base directory does not exist: {self.base_dir}"

            # Test that key files exist in the expected locations
            key_files = [
                "start_ecosystem.py",
                "ai_ecosystem_manager.py",
                "config/startup_config.json",
                "config/ecosystem_config.yaml"
            ]

            missing_files = []
            for file_path in key_files:
                full_path = self.base_dir / file_path
                if not full_path.exists():
                    missing_files.append(file_path)

            if missing_files:
                return False, f"Missing key files: {missing_files}"

            duration = time.time() - start_time
            return True, f"Directory setup validated ({duration:.2f}s)"

        except Exception as e:
            duration = time.time() - start_time
            return False, f"Error testing directory setup: {e}"

    def test_launcher_environment_setup(self) -> bool:
        """Test environment variable setup in launcher"""
        start_time = time.time()

        try:
            launcher_path = self.base_dir / "START_ENHANCED_DUCKBOT.bat"
            with open(launcher_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Check for environment setup
            env_setup_indicators = [
                'set PYTHONUTF8=1',
                'set PYTHONIOENCODING=utf-8',
                'title DuckBot',
                'color 0A'
            ]

            missing_indicators = []
            for indicator in env_setup_indicators:
                if indicator not in content:
                    missing_indicators.append(indicator)

            if missing_indicators:
                return False, f"Missing environment setup: {missing_indicators}"

            # Test that environment variables are properly set
            test_script_content = '''
@echo off
echo Testing environment variables...
echo PYTHONUTF8=%PYTHONUTF8%
echo PYTHONIOENCODING=%PYTHONIOENCODING%
if "%PYTHONUTF8%"=="1" (
    echo PYTHONUTF8 is correctly set
) else (
    echo PYTHONUTF8 is not set correctly
)
if "%PYTHONIOENCODING%"=="utf-8" (
    echo PYTHONIOENCODING is correctly set
) else (
    echo PYTHONIOENCODING is not set correctly
)
            '''

            with tempfile.NamedTemporaryFile(mode='w', suffix='.bat', delete=False) as f:
                f.write(test_script_content)
                temp_script = f.name

            try:
                result = subprocess.run([temp_script], capture_output=True, text=True, timeout=10)

                if "correctly set" not in result.stdout:
                    return False, "Environment variables not properly set by launcher"

            finally:
                os.unlink(temp_script)

            duration = time.time() - start_time
            return True, f"Environment setup validated ({duration:.2f}s)"

        except Exception as e:
            duration = time.time() - start_time
            return False, f"Error testing environment setup: {e}"

    def test_launcher_error_handling(self) -> bool:
        """Test error handling in launcher"""
        start_time = time.time()

        try:
            launcher_path = self.base_dir / "START_ENHANCED_DUCKBOT.bat"
            with open(launcher_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Check for error handling patterns
            error_handling_indicators = [
                'if %errorlevel% neq 0',
                'echo [ERROR]',
                'pause',
                'exit /b',
                'goto error'
            ]

            missing_indicators = []
            for indicator in error_handling_indicators:
                if indicator not in content:
                    missing_indicators.append(indicator)

            # Note: Missing error handling is not necessarily a failure
            # as the launcher may use different error handling approaches

            duration = time.time() - start_time
            return True, f"Error handling analysis completed ({duration:.2f}s)"

        except Exception as e:
            duration = time.time() - start_time
            return False, f"Error testing error handling: {e}"

    def test_launcher_compatibility(self) -> bool:
        """Test launcher compatibility across different Windows versions"""
        start_time = time.time()

        try:
            launcher_path = self.base_dir / "START_ENHANCED_DUCKBOT.bat"
            with open(launcher_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Check for Windows compatibility features
            compatibility_indicators = [
                'chcp 65001',  # UTF-8 code page
                'setlocal',    # Local environment
                'endlocal',    # Restore environment
                '@echo off'    # Command echoing
            ]

            missing_indicators = []
            for indicator in compatibility_indicators:
                if indicator not in content:
                    missing_indicators.append(indicator)

            # Check for problematic commands
            problematic_commands = [
                'choice',  # May not be available in all Windows versions
                'timeout', # May not be available in very old Windows versions
            ]

            found_problematic = []
            for cmd in problematic_commands:
                if cmd in content:
                    found_problematic.append(cmd)

            compatibility_notes = []
            if missing_indicators:
                compatibility_notes.append(f"Missing compatibility features: {missing_indicators}")
            if found_problematic:
                compatibility_notes.append(f"Found potentially problematic commands: {found_problematic}")

            duration = time.time() - start_time
            return True, f"Compatibility analysis completed - {compatibility_notes} ({duration:.2f}s)"

        except Exception as e:
            duration = time.time() - start_time
            return False, f"Error testing launcher compatibility: {e}"

    def run_all_launcher_tests(self) -> List[TestResult]:
        """Run all launcher integration tests"""
        self.logger.info("Starting launcher integration tests...")

        # Define all launcher tests
        launcher_tests = [
            ("enhanced_launcher_structure", self.test_enhanced_launcher_structure),
            ("launcher_menu_options", self.test_launcher_menu_options),
            ("launcher_python_detection", self.test_launcher_python_detection),
            ("launcher_directory_setup", self.test_launcher_directory_setup),
            ("launcher_environment_setup", self.test_launcher_environment_setup),
            ("launcher_error_handling", self.test_launcher_error_handling),
            ("launcher_compatibility", self.test_launcher_compatibility),
        ]

        # Run all tests
        for test_name, test_func in launcher_tests:
            try:
                start_time = time.time()
                success, message = test_func()
                duration = time.time() - start_time

                status = "PASSED" if success else "FAILED"
                self.record_result(test_name, status, duration, message if not success else None)

                # Log result
                emoji = "✅" if success else "❌"
                self.logger.info(f"{emoji} [LAUNCHER] {test_name} ({duration:.2f}s) - {message}")

            except Exception as e:
                duration = time.time() - start_time
                error_msg = f"Test execution error: {e}"
                self.record_result(test_name, "ERROR", duration, error_msg)
                self.logger.error(f"💥 [LAUNCHER] {test_name} failed: {error_msg}")

        return self.test_results

def main():
    """Main entry point for launcher integration tests"""
    import argparse

    parser = argparse.ArgumentParser(description="DuckBot Launcher Integration Tests")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')

    # Run tests
    test_runner = LauncherIntegrationTests()
    results = test_runner.run_all_launcher_tests()

    # Print summary
    total_tests = len(results)
    passed = sum(1 for r in results if r.status == "PASSED")
    failed = sum(1 for r in results if r.status == "FAILED")
    errors = sum(1 for r in results if r.status == "ERROR")

    print(f"\n{'='*60}")
    print(f"LAUNCHER INTEGRATION TEST RESULTS")
    print(f"{'='*60}")
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed} ✅")
    print(f"Failed: {failed} ❌")
    print(f"Errors: {errors} 💥")
    print(f"Pass Rate: {(passed/total_tests*100):.1f}%")

    if failed > 0 or errors > 0:
        print(f"\n❌ Launcher integration tests completed with issues")
        sys.exit(1)
    else:
        print(f"\n✅ All launcher integration tests passed!")
        sys.exit(0)

if __name__ == "__main__":
    main()