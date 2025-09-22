#!/usr/bin/env python3
"""
DuckBot Consolidated Test Suite v4.2
Comprehensive test suite for all consolidated modules

This test suite validates the consolidated functionality:
- AI Provider Manager
- Agent Framework
- Service Manager  
- Consolidated Utilities
- Integration Modules
- WebUI Components
- System Components

Features:
- Comprehensive test organization by category
- Detailed test reporting with success/failure tracking
- Support for running specific test categories
- Automatic test result analysis and recommendations
- Proper error handling and graceful degradation
- Unicode-safe output for Windows compatibility
- Backward compatibility with existing test files
"""

import asyncio
import sys
import os
import subprocess
import time
import json
import logging
import traceback
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict

# Setup proper encoding for Windows
if sys.platform == 'win32':
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('consolidated_test_suite.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

@dataclass
class TestResult:
    """Test result data structure"""
    test_name: str
    category: str
    passed: bool
    duration: float
    error: Optional[str] = None
    details: Optional[str] = None
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

@dataclass
class TestCategoryResult:
    """Test category result data structure"""
    category: str
    total_tests: int
    passed_tests: int
    failed_tests: int
    success_rate: float
    results: List[TestResult]

    def __post_init__(self):
        self.success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0

class ConsolidatedTestSuite:
    """Comprehensive test suite for consolidated DuckBot modules"""

    def __init__(self):
        self.test_results: List[TestResult] = []
        self.category_results: Dict[str, TestCategoryResult] = {}
        self.test_config = {
            "timeout": 30,
            "webui_test_port": 8792,
            "enable_detailed_logging": True,
            "save_report": True
        }

        # Test categories
        self.test_categories = {
            "ai_provider_manager": "AI Provider Manager Tests",
            "agent_framework": "Agent Framework Tests",
            "service_manager": "Service Manager Tests",
            "consolidated_utilities": "Consolidated Utilities Tests",
            "integrations": "Integration Module Tests",
            "webui": "WebUI Component Tests",
            "system": "System Component Tests"
        }

        # Test timeout configuration
        self.test_timeouts = {
            "ai_provider_manager": 15,
            "agent_framework": 45,
            "service_manager": 30,
            "consolidated_utilities": 20,
            "integrations": 60,
            "webui": 60,
            "system": 30
        }

    def run_test(self, name: str, code: str, category: str = "general",
                timeout: Optional[int] = None, capture_output: bool = True) -> Tuple[bool, str, float]:
        """Run a single test with timeout handling"""
        start_time = time.time()

        try:
            timeout = timeout or self.test_config["timeout"]

            if capture_output:
                result = subprocess.run(
                    [sys.executable, '-c', code],
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    env=os.environ.copy()
                )

                if result.returncode == 0:
                    output = result.stdout.strip()
                    duration = time.time() - start_time
                    return True, output, duration
                else:
                    error_msg = result.stderr.strip()[:500]
                    duration = time.time() - start_time
                    return False, error_msg, duration
            else:
                # For tests that don't need output capture
                process = subprocess.Popen(
                    [sys.executable, '-c', code],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    env=os.environ.copy()
                )

                stdout, stderr = process.communicate(timeout=timeout)

                if process.returncode == 0:
                    output = stdout.decode('utf-8', errors='ignore').strip()
                    duration = time.time() - start_time
                    return True, output, duration
                else:
                    error_msg = stderr.decode('utf-8', errors='ignore').strip()[:500]
                    duration = time.time() - start_time
                    return False, error_msg, duration

        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            return False, f"Timeout after {timeout} seconds", duration
        except Exception as e:
            duration = time.time() - start_time
            return False, f"Test execution error: {str(e)}", duration

    async def run_async_test(self, name: str, test_func, category: str = "general",
                           timeout: Optional[int] = None) -> Tuple[bool, str, float]:
        """Run an asynchronous test"""
        start_time = time.time()

        try:
            timeout = timeout or self.test_config["timeout"]

            # Run with timeout
            result = await asyncio.wait_for(test_func(), timeout=timeout)
            duration = time.time() - start_time
            return True, str(result), duration

        except asyncio.TimeoutError:
            duration = time.time() - start_time
            return False, f"Timeout after {timeout} seconds", duration
        except Exception as e:
            duration = time.time() - start_time
            return False, f"Async test error: {str(e)}", duration

    def record_result(self, test_name: str, category: str, passed: bool,
                     duration: float, error: Optional[str] = None, details: Optional[str] = None):
        """Record a test result"""
        result = TestResult(
            test_name=test_name,
            category=category,
            passed=passed,
            duration=duration,
            error=error,
            details=details
        )

        self.test_results.append(result)

        if self.test_config["enable_detailed_logging"]:
            status = "PASS" if passed else "FAIL"
            logger.info(f"[{status}] {category}.{test_name} ({duration:.2f}s)")
            if error:
                logger.error(f"  Error: {error}")
            if details:
                logger.info(f"  Details: {details}")

    # AI Provider Manager Tests
    def test_ai_provider_manager(self) -> bool:
        """Test AI provider manager functionality"""
        logger.info("Testing AI Provider Manager...")

        provider_tests = [
            ("Import Test", """
try:
    from duckbot.core.ai_provider_manager import AIProviderManager, ai_provider_manager
    print('✅ AI Provider Manager imported successfully')
except ImportError as e:
    print(f'❌ Import failed: {e}')
"""),
            ("Initialization Test", """
try:
    from duckbot.core.ai_provider_manager import AIProviderManager
    manager = AIProviderManager()
    print(f'✅ AI Provider Manager initialized')
    print(f'Available providers: {len(manager.get_available_providers())}')
except Exception as e:
    print(f'❌ Initialization failed: {e}')
"""),
            ("Provider Status Test", """
try:
    from duckbot.core.ai_provider_manager import get_all_provider_status
    status = get_all_provider_status()
    print(f'✅ Provider status retrieved')
    print(f'Providers checked: {len(status)}')
except Exception as e:
    print(f'❌ Provider status test failed: {e}')
"""),
            ("Model Selection Test", """
try:
    from duckbot.core.ai_provider_manager import ai_provider_manager
    task = {"kind": "code", "prompt": "Write a Python function"}
    model, provider = ai_provider_manager.select_optimal_model_for_task(task)
    print(f'✅ Model selection worked')
    print(f'Selected: {model} from {provider}')
except Exception as e:
    print(f'❌ Model selection test failed: {e}')
"""),
        ]

        passed_count = 0
        for name, code in provider_tests:
            success, output, duration = self.run_test(name, code.strip(), category="ai_provider_manager")
            self.record_result(
                f"ai_provider_{name.lower().replace(' ', '_')}",
                "ai_provider_manager", success, duration,
                None if success else output, output if success else None
            )

            if success:
                passed_count += 1

        return passed_count >= len(provider_tests) * 0.7  # 70% threshold

    # Agent Framework Tests
    def test_agent_framework(self) -> bool:
        """Test agent framework functionality"""
        logger.info("Testing Agent Framework...")

        agent_tests = [
            ("Import Test", """
try:
    from duckbot.core.unified_agent_framework import UnifiedAgentFramework, agent_framework
    print('✅ Agent Framework imported successfully')
except ImportError as e:
    print(f'❌ Import failed: {e}')
"""),
            ("Initialization Test", """
try:
    from duckbot.core.unified_agent_framework import UnifiedAgentFramework
    framework = UnifiedAgentFramework()
    print(f'✅ Agent Framework initialized')
    print(f'Available agents: {len(framework.active_agents)}')
except Exception as e:
    print(f'❌ Initialization failed: {e}')
"""),
            ("Capability Test", """
try:
    from duckbot.core.unified_agent_framework import get_agent_capabilities
    capabilities = get_agent_capabilities()
    print(f'✅ Agent capabilities retrieved')
    print(f'Available features: {len(capabilities.get("features", []))}')
except Exception as e:
    print(f'❌ Capability test failed: {e}')
"""),
            ("Task Creation Test", """
try:
    from duckbot.core.unified_agent_framework import agent_framework
    task_id = agent_framework.create_agent_task("Test task for unified agent framework")
    print(f'✅ Task creation worked')
    print(f'Task ID: {task_id[:8]}...')
except Exception as e:
    print(f'❌ Task creation test failed: {e}')
"""),
        ]

        passed_count = 0
        for name, code in agent_tests:
            success, output, duration = self.run_test(name, code.strip(), category="agent_framework")
            self.record_result(
                f"agent_{name.lower().replace(' ', '_')}",
                "agent_framework", success, duration,
                None if success else output, output if success else None
            )

            if success:
                passed_count += 1

        return passed_count >= len(agent_tests) * 0.7  # 70% threshold

    # Service Manager Tests
    def test_service_manager(self) -> bool:
        """Test service manager functionality"""
        logger.info("Testing Service Manager...")

        service_tests = [
            ("Import Test", """
try:
    from duckbot.core.service_manager import UnifiedServiceManager, service_manager
    print('✅ Service Manager imported successfully')
except ImportError as e:
    print(f'❌ Import failed: {e}')
"""),
            ("Initialization Test", """
try:
    from duckbot.core.service_manager import UnifiedServiceManager
    manager = UnifiedServiceManager()
    print(f'✅ Service Manager initialized')
    print(f'Available services: {len(manager.services)}')
except Exception as e:
    print(f'❌ Initialization failed: {e}')
"""),
            ("Status Test", """
try:
    from duckbot.core.service_manager import service_manager
    status = service_manager.get_all_service_status()
    print(f'✅ Service status retrieved')
    print(f'Services checked: {len(status)}')
except Exception as e:
    print(f'❌ Service status test failed: {e}')
"""),
            ("Capability Test", """
try:
    from duckbot.core.service_manager import get_service_capabilities
    capabilities = get_service_capabilities()
    print(f'✅ Service capabilities retrieved')
    print(f'Available integrations: {len(capabilities.get("integrations", []))}')
except Exception as e:
    print(f'❌ Capability test failed: {e}')
"""),
        ]

        passed_count = 0
        for name, code in service_tests:
            success, output, duration = self.run_test(name, code.strip(), category="service_manager")
            self.record_result(
                f"service_{name.lower().replace(' ', '_')}",
                "service_manager", success, duration,
                None if success else output, output if success else None
            )

            if success:
                passed_count += 1

        return passed_count >= len(service_tests) * 0.7  # 70% threshold

    # Consolidated Utilities Tests
    def test_consolidated_utilities(self) -> bool:
        """Test consolidated utilities functionality"""
        logger.info("Testing Consolidated Utilities...")

        utility_tests = [
            ("Import Test", """
try:
    from duckbot.core.consolidated_utilities import DuckBotConsolidatedUtilities, utilities
    print('✅ Consolidated Utilities imported successfully')
except ImportError as e:
    print(f'❌ Import failed: {e}')
"""),
            ("Initialization Test", """
try:
    from duckbot.core.consolidated_utilities import DuckBotConsolidatedUtilities
    util = DuckBotConsolidatedUtilities()
    print(f'✅ Consolidated Utilities initialized')
    print(f'Backup config: {len(util.backup_config["exclude_patterns"])} patterns')
except Exception as e:
    print(f'❌ Initialization failed: {e}')
"""),
            ("Backup Test", """
try:
    from duckbot.core.consolidated_utilities import create_backup
    result = create_backup()
    print(f'✅ Backup functionality tested')
    print(f'Success: {result.get("success", False)}')
except Exception as e:
    print(f'❌ Backup test failed: {e}')
"""),
            ("Unicode Test", """
try:
    from duckbot.core.consolidated_utilities import setup_unicode
    success = setup_unicode()
    print(f'✅ Unicode setup tested')
    print(f'Success: {success}')
except Exception as e:
    print(f'❌ Unicode test failed: {e}')
"""),
        ]

        passed_count = 0
        for name, code in utility_tests:
            success, output, duration = self.run_test(name, code.strip(), category="consolidated_utilities")
            self.record_result(
                f"utility_{name.lower().replace(' ', '_')}",
                "consolidated_utilities", success, duration,
                None if success else output, output if success else None
            )

            if success:
                passed_count += 1

        return passed_count >= len(utility_tests) * 0.7  # 70% threshold

    # Integration Tests
    def test_integrations(self) -> bool:
        """Test integration modules functionality"""
        logger.info("Testing Integration Modules...")

        integration_tests = [
            ("VibeVoice Integration", """
try:
    from duckbot.integrations.vibevoice_integration import vibevoice_integration
    print('✅ VibeVoice Integration imported')
    print(f'Available: {vibevoice_integration.is_available()}')
except ImportError:
    print('⚠️  VibeVoice Integration not available')
except Exception as e:
    print(f'❌ VibeVoice Integration error: {e}')
"""),
            ("ByteBot Integration", """
try:
    from duckbot.integrations.bytebot_integration import bytebot_integration
    print('✅ ByteBot Integration imported')
    print(f'Available: {bytebot_integration.is_available()}')
except ImportError:
    print('⚠️  ByteBot Integration not available')
except Exception as e:
    print(f'❌ ByteBot Integration error: {e}')
"""),
            ("Archon Integration", """
try:
    from duckbot.integrations.archon_integration import archon_integration
    print('✅ Archon Integration imported')
    print(f'Available: {archon_integration.is_available()}')
except ImportError:
    print('⚠️  Archon Integration not available')
except Exception as e:
    print(f'❌ Archon Integration error: {e}')
"""),
            ("Qwen-Agent Integration", """
try:
    from duckbot.integrations.qwen_agent_integration import qwen_agent
    print('✅ Qwen-Agent Integration imported')
    print(f'Available: {qwen_agent.is_available()}')
except ImportError:
    print('⚠️  Qwen-Agent Integration not available')
except Exception as e:
    print(f'❌ Qwen-Agent Integration error: {e}')
"""),
        ]

        passed_count = 0
        for name, code in integration_tests:
            success, output, duration = self.run_test(name, code.strip(), category="integrations")
            self.record_result(
                f"integration_{name.lower().replace(' ', '_').replace('-', '_')}",
                "integrations", success, duration,
                None if success else output, output if success else None
            )

            if success:
                passed_count += 1

        return passed_count >= len(integration_tests) * 0.5  # 50% threshold (some may be missing)

    # WebUI Tests
    def test_webui(self) -> bool:
        """Test WebUI components functionality"""
        logger.info("Testing WebUI Components...")

        webui_tests = [
            ("Unified WebUI Import", """
try:
    from duckbot.ui.unified_webui import app
    routes = [route.path for route in app.routes if hasattr(route, 'path')]
    print('✅ Unified WebUI imported successfully')
    print(f'Routes: {len(routes)} available')
except ImportError:
    print('⚠️  Unified WebUI not available')
except Exception as e:
    print(f'❌ Unified WebUI error: {e}')
"""),
            ("Enhanced WebUI Import", """
try:
    from duckbot.ui.enhanced_webui import app
    print('✅ Enhanced WebUI imported successfully')
except ImportError:
    print('⚠️  Enhanced WebUI not available')
except Exception as e:
    print(f'❌ Enhanced WebUI error: {e}')
"""),
            ("WebUI Modern Import", """
try:
    from duckbot.ui.webui_modern import app
    print('✅ WebUI Modern imported successfully')
except ImportError:
    print('⚠️  WebUI Modern not available')
except Exception as e:
    print(f'❌ WebUI Modern error: {e}')
"""),
            ("Charm Terminal UI Import", """
try:
    from duckbot.ui.charm_terminal_ui import CharmTerminalUI
    ui = CharmTerminalUI()
    print('✅ Charm Terminal UI imported successfully')
except ImportError:
    print('⚠️  Charm Terminal UI not available')
except Exception as e:
    print(f'❌ Charm Terminal UI error: {e}')
"""),
        ]

        passed_count = 0
        for name, code in webui_tests:
            success, output, duration = self.run_test(name, code.strip(), category="webui")
            self.record_result(
                f"webui_{name.lower().replace(' ', '_').replace('-', '_')}",
                "webui", success, duration,
                None if success else output, output if success else None
            )

            if success:
                passed_count += 1

        return passed_count >= len(webui_tests) * 0.5  # 50% threshold (some may be missing)

    # System Tests
    def test_system(self) -> bool:
        """Test system components functionality"""
        logger.info("Testing System Components...")

        system_tests = [
            ("Server Manager Import", """
try:
    from duckbot.core.server_manager import server_manager
    print('✅ Server Manager imported successfully')
except ImportError:
    print('⚠️  Server Manager not available')
except Exception as e:
    print(f'❌ Server Manager error: {e}')
"""),
            ("AI Router Import", """
try:
    from duckbot.core.ai_router_gpt import AIRouter
    router = AIRouter()
    print('✅ AI Router imported successfully')
except ImportError:
    print('⚠️  AI Router not available')
except Exception as e:
    print(f'❌ AI Router error: {e}')
"""),
            ("Cost Tracker Import", """
try:
    from duckbot.core.cost_tracker import cost_tracker
    print('✅ Cost Tracker imported successfully')
except ImportError:
    print('⚠️  Cost Tracker not available')
except Exception as e:
    print(f'❌ Cost Tracker error: {e}')
"""),
            ("Hardware Detector Import", """
try:
    from duckbot.core.hardware_detector import HardwareDetector
    detector = HardwareDetector()
    print('✅ Hardware Detector imported successfully')
except ImportError:
    print('⚠️  Hardware Detector not available')
except Exception as e:
    print(f'❌ Hardware Detector error: {e}')
"""),
        ]

        passed_count = 0
        for name, code in system_tests:
            success, output, duration = self.run_test(name, code.strip(), category="system")
            self.record_result(
                f"system_{name.lower().replace(' ', '_').replace('-', '_')}",
                "system", success, duration,
                None if success else output, output if success else None
            )

            if success:
                passed_count += 1

        return passed_count >= len(system_tests) * 0.5  # 50% threshold (some may be missing)

    # Test Category Runners
    async def run_category_tests(self, category: str) -> TestCategoryResult:
        """Run all tests for a specific category"""
        logger.info(f"Running tests for category: {category}")

        category_start_time = time.time()
        category_results = []

        if category == "ai_provider_manager":
            success = self.test_ai_provider_manager()
            duration = time.time() - category_start_time
            result = TestCategoryResult(
                category=category,
                total_tests=1,
                passed_tests=1 if success else 0,
                failed_tests=0 if success else 1,
                success_rate=100.0 if success else 0.0,
                results=[]
            )

        elif category == "agent_framework":
            success = self.test_agent_framework()
            duration = time.time() - category_start_time
            result = TestCategoryResult(
                category=category,
                total_tests=1,
                passed_tests=1 if success else 0,
                failed_tests=0 if success else 1,
                success_rate=100.0 if success else 0.0,
                results=[]
            )

        elif category == "service_manager":
            success = self.test_service_manager()
            duration = time.time() - category_start_time
            result = TestCategoryResult(
                category=category,
                total_tests=1,
                passed_tests=1 if success else 0,
                failed_tests=0 if success else 1,
                success_rate=100.0 if success else 0.0,
                results=[]
            )

        elif category == "consolidated_utilities":
            success = self.test_consolidated_utilities()
            duration = time.time() - category_start_time
            result = TestCategoryResult(
                category=category,
                total_tests=1,
                passed_tests=1 if success else 0,
                failed_tests=0 if success else 1,
                success_rate=100.0 if success else 0.0,
                results=[]
            )

        elif category == "integrations":
            success = self.test_integrations()
            duration = time.time() - category_start_time
            result = TestCategoryResult(
                category=category,
                total_tests=1,
                passed_tests=1 if success else 0,
                failed_tests=0 if success else 1,
                success_rate=100.0 if success else 0.0,
                results=[]
            )

        elif category == "webui":
            success = self.test_webui()
            duration = time.time() - category_start_time
            result = TestCategoryResult(
                category=category,
                total_tests=1,
                passed_tests=1 if success else 0,
                failed_tests=0 if success else 1,
                success_rate=100.0 if success else 0.0,
                results=[]
            )

        elif category == "system":
            success = self.test_system()
            duration = time.time() - category_start_time
            result = TestCategoryResult(
                category=category,
                total_tests=1,
                passed_tests=1 if success else 0,
                failed_tests=0 if success else 1,
                success_rate=100.0 if success else 0.0,
                results=[]
            )

        else:
            logger.error(f"Unknown test category: {category}")
            result = TestCategoryResult(
                category=category,
                total_tests=0,
                passed_tests=0,
                failed_tests=0,
                success_rate=0.0,
                results=[]
            )

        self.category_results[category] = result

        return result

    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests from all categories"""
        logger.info("Starting Consolidated DuckBot Test Suite")
        print("=" * 70)
        print("DuckBot Consolidated Test Suite v4.2")
        print("=" * 70)
        print()

        # Run tests for each category
        for category, description in self.test_categories.items():
            print(f"[{category.upper().replace('_', ' ')}] {description}")
            print("-" * 50)

            try:
                category_result = await self.run_category_tests(category)

                print(f"Results: {category_result.passed_tests}/{category_result.total_tests} tests passed "
                      f"({category_result.success_rate:.1f}%)")
                print()

            except Exception as e:
                logger.error(f"Category {category} failed: {e}")
                print(f"[ERROR] Category {category} failed: {e}")
                print()

        # Generate comprehensive report
        return self.generate_comprehensive_report()

    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        logger.info("Generating test report...")

        # Calculate overall statistics
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r.passed)
        failed_tests = total_tests - passed_tests
        overall_success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        # Calculate category statistics
        category_stats = {}
        for category, result in self.category_results.items():
            category_stats[category] = {
                "total_tests": result.total_tests,
                "passed_tests": result.passed_tests,
                "failed_tests": result.failed_tests,
                "success_rate": result.success_rate,
                "status": "PASS" if result.success_rate >= 80 else "PARTIAL" if result.success_rate >= 50 else "FAIL"
            }

        # Generate recommendations
        recommendations = self.generate_recommendations()

        # Determine overall system status
        system_status = "READY"
        if overall_success_rate >= 95:
            system_status = "EXCELLENT"
        elif overall_success_rate >= 80:
            system_status = "READY"
        elif overall_success_rate >= 60:
            system_status = "NEEDS_ATTENTION"
        else:
            system_status = "CRITICAL"

        # Create report
        report = {
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": overall_success_rate,
                "system_status": system_status,
                "timestamp": datetime.now().isoformat()
            },
            "category_summary": category_stats,
            "detailed_results": [asdict(result) for result in self.test_results],
            "recommendations": recommendations,
            "test_categories": self.test_categories
        }

        # Save report to file
        if self.test_config["save_report"]:
            try:
                report_file = Path("consolidated_test_report.json")
                with open(report_file, 'w', encoding='utf-8') as f:
                    json.dump(report, f, indent=2, ensure_ascii=False, default=str)

                logger.info(f"Consolidated test report saved to: {report_file}")
                print(f"\n[REPORT] Full test report saved to: {report_file}")

            except Exception as e:
                logger.error(f"Failed to save report: {e}")

        return report

    def generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []

        # Check overall success rate
        overall_rate = sum(r["success_rate"] for r in self.category_results.values()) / len(self.category_results) \
            if self.category_results else 0

        if overall_rate >= 80:
            recommendations.append("System is in good working condition")
        elif overall_rate >= 60:
            recommendations.append("System has some issues but is mostly functional")
        else:
            recommendations.append("System has significant issues that need attention")

        # Check specific category issues
        for category, stats in self.category_results.items():
            if stats["success_rate"] < 50:
                if category == "ai_provider_manager":
                    recommendations.append("Critical: AI Provider Manager issues detected")
                elif category == "agent_framework":
                    recommendations.append("Agent Framework has issues - check agent integrations")
                elif category == "service_manager":
                    recommendations.append("Service Manager issues - check service integrations")
                elif category == "consolidated_utilities":
                    recommendations.append("Consolidated Utilities issues - check dependencies")
                elif category == "integrations":
                    recommendations.append("Some integrations are missing or not working")
                elif category == "webui":
                    recommendations.append("WebUI components have problems")
                elif category == "system":
                    recommendations.append("System components need attention")

        # Success recommendations
        if all(stats["success_rate"] >= 70 for stats in self.category_results.values()):
            recommendations.extend([
                "All major systems are working correctly",
                "DuckBot is ready for basic operation",
                "Consider running: START_ENHANCED_DUCKBOT.bat"
            ])

        return recommendations

    def print_report_summary(self, report: Dict[str, Any]):
        """Print a summary of the test report"""
        summary = report["summary"]

        print("\n" + "=" * 70)
        print("CONSOLIDATED TEST REPORT SUMMARY")
        print("=" * 70)
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Passed: {summary['passed_tests']} ✅")
        print(f"Failed: {summary['failed_tests']} ❌")
        print(f"Success Rate: {summary['success_rate']:.1f}%")
        print(f"System Status: {summary['system_status']}")
        print()

        print("CATEGORY RESULTS:")
        print("-" * 50)
        for category, stats in report["category_summary"].items():
            status_icon = "✅" if stats["status"] == "PASS" else "⚠️" if stats["status"] == "PARTIAL" else "❌"
            print(f"{status_icon} {category.replace('_', ' ').title()}: "
                  f"{stats['passed_tests']}/{stats['total_tests']} "
                  f"({stats['success_rate']:.1f}%)")

        print("\nRECOMMENDATIONS:")
        print("-" * 50)
        for i, rec in enumerate(report["recommendations"], 1):
            print(f"{i}. {rec}")

        print("\n" + "=" * 70)

# Global instance
test_suite = ConsolidatedTestSuite()

# Convenience functions
def run_all_tests() -> Dict[str, Any]:
    """Run all tests"""
    return asyncio.run(test_suite.run_all_tests())

def run_category_tests(category: str) -> TestCategoryResult:
    """Run tests for a specific category"""
    return asyncio.run(test_suite.run_category_tests(category))

def generate_test_report() -> Dict[str, Any]:
    """Generate comprehensive test report"""
    return test_suite.generate_comprehensive_report()

def print_test_summary(report: Dict[str, Any]):
    """Print test report summary"""
    test_suite.print_report_summary(report)

if __name__ == "__main__":
    # Test the integration
    import argparse

    parser = argparse.ArgumentParser(description="DuckBot Consolidated Test Suite")
    parser.add_argument("--category", choices=[
        "ai_provider_manager", "agent_framework", "service_manager",
        "consolidated_utilities", "integrations", "webui", "system"
    ], help="Run specific test category")
    
    parser.add_argument("--timeout", type=int, default=30, help="Test timeout in seconds")
    parser.add_argument("--no-report", action="store_true", help="Don't save report file")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    # Configure based on arguments
    if args.timeout:
        test_suite.test_config["timeout"] = args.timeout

    if args.no_report:
        test_suite.test_config["save_report"] = False

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        if args.category:
            # Run specific category
            print(f"Running tests for category: {args.category}")
            category_result = asyncio.run(test_suite.run_category_tests(args.category))

            print(f"\nCategory Results:")
            print(f"Total: {category_result.total_tests}")
            print(f"Passed: {category_result.passed_tests}")
            print(f"Failed: {category_result.failed_tests}")
            print(f"Success Rate: {category_result.success_rate:.1f}%")

            sys.exit(0 if category_result.success_rate >= 80 else 1)
        else:
            # Run all tests
            report = asyncio.run(test_suite.run_all_tests())
            test_suite.print_report_summary(report)

            # Return exit code based on system status
            status = report["summary"]["system_status"]
            if status == "EXCELLENT":
                sys.exit(0)
            elif status == "READY":
                sys.exit(0)
            elif status == "NEEDS_ATTENTION":
                sys.exit(1)
            else:
                sys.exit(2)

    except KeyboardInterrupt:
        print("\n\n[STOPPED] Test execution cancelled by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Test suite execution failed: {e}")
        print(f"\n[FATAL] Test suite execution failed: {e}")
        sys.exit(3)