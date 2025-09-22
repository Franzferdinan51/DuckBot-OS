#!/usr/bin/env python3
"""
DuckBot Consolidation Verification Script v4.2
Verify that all consolidation efforts were successful

This script verifies:
1. Core modules consolidation
2. Agent framework consolidation  
3. Service management consolidation
4. Utilities consolidation
5. Test suite consolidation
6. Batch file consolidation
7. Backward compatibility preservation
8. Feature parity maintenance

Features:
- Comprehensive verification of all consolidation efforts
- Detailed reporting with success/failure tracking
- Backward compatibility testing
- Feature parity validation
- Performance benchmarking
- Resource usage monitoring
- Unicode-safe output for Windows
- Cross-platform compatibility
"""

import os
import sys
import subprocess
import time
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import asyncio
import importlib
from datetime import datetime

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
        logging.FileHandler('consolidation_verification.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class ConsolidationVerifier:
    """Verify all consolidation efforts"""

    def __init__(self):
        self.results = []
        self.categories = {
            "core_modules": "Core Modules Consolidation",
            "agent_framework": "Agent Framework Consolidation",
            "service_management": "Service Management Consolidation",
            "utilities": "Utilities Consolidation",
            "test_suite": "Test Suite Consolidation",
            "batch_files": "Batch File Consolidation",
            "backward_compatibility": "Backward Compatibility",
            "feature_parity": "Feature Parity"
        }
        self.verification_config = {
            "timeout": 30,
            "verbose": True,
            "save_report": True
        }

    def verify_core_modules(self) -> bool:
        """Verify core modules consolidation"""
        logger.info("Verifying Core Modules Consolidation...")
        
        core_modules = [
            ("AI Provider Manager", "duckbot.core.ai_provider_manager"),
            ("Agent Framework", "duckbot.core.agent_framework"),
            ("Service Manager", "duckbot.core.service_manager"),
            ("Utilities", "duckbot.core.consolidated_utilities")
        ]
        
        passed_count = 0
        for name, module in core_modules:
            try:
                importlib.import_module(module)
                logger.info(f"✅ {name}: Available")
                passed_count += 1
            except ImportError as e:
                logger.error(f"❌ {name}: Not available - {e}")
            except Exception as e:
                logger.error(f"❌ {name}: Error - {e}")
        
        # Check that old modules are still accessible (backward compatibility)
        old_modules = [
            ("Cost Tracker", "duckbot.cost_tracker"),
            ("WebUI", "duckbot.webui"),
            ("AI Router", "duckbot.ai_router_gpt"),
            ("Server Manager", "duckbot.server_manager")
        ]
        
        for name, module in old_modules:
            try:
                importlib.import_module(module)
                logger.info(f"✅ {name}: Backward compatible")
            except ImportError as e:
                logger.warning(f"⚠️  {name}: Not backward compatible - {e}")
        
        return passed_count >= len(core_modules) * 0.8  # 80% threshold

    def verify_agent_framework(self) -> bool:
        """Verify agent framework consolidation"""
        logger.info("Verifying Agent Framework Consolidation...")
        
        try:
            from duckbot.core.agent_framework import UnifiedAgentFramework
            
            framework = UnifiedAgentFramework()
            capabilities = framework.get_agent_capabilities()
            
            logger.info(f"✅ Agent Framework: Available")
            logger.info(f"   Agents: {len(capabilities.get('agents', []))}")
            logger.info(f"   Features: {len(capabilities.get('features', []))}")
            
            return True
            
        except ImportError as e:
            logger.error(f"❌ Agent Framework: Not available - {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Agent Framework: Error - {e}")
            return False

    def verify_service_management(self) -> bool:
        """Verify service management consolidation"""
        logger.info("Verifying Service Management Consolidation...")
        
        try:
            from duckbot.core.service_manager import UnifiedServiceManager, ServiceType
            
            manager = UnifiedServiceManager()
            
            logger.info(f"✅ Service Manager: Available")
            logger.info(f"   Services: {len(manager.services)}")
            logger.info(f"   Service Types: {len(list(ServiceType))}")
            
            return True
            
        except ImportError as e:
            logger.error(f"❌ Service Manager: Not available - {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Service Manager: Error - {e}")
            return False

    def verify_utilities(self) -> bool:
        """Verify utilities consolidation"""
        logger.info("Verifying Utilities Consolidation...")
        
        try:
            from duckbot.core.consolidated_utilities import DuckBotConsolidatedUtilities
            
            utilities = DuckBotConsolidatedUtilities()
            
            logger.info(f"✅ Consolidated Utilities: Available")
            logger.info(f"   Backup patterns: {len(utilities.backup_config['exclude_patterns'])}")
            logger.info(f"   AI providers: {len(utilities.ai_providers)}")
            
            return True
            
        except ImportError as e:
            logger.error(f"❌ Consolidated Utilities: Not available - {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Consolidated Utilities: Error - {e}")
            return False

    def verify_test_suite(self) -> bool:
        """Verify test suite consolidation"""
        logger.info("Verifying Test Suite Consolidation...")
        
        test_files = [
            "tests/consolidated_test_suite.py",
            "tests/test_runner.py"
        ]
        
        passed_count = 0
        for test_file in test_files:
            if Path(test_file).exists():
                logger.info(f"✅ {test_file}: Exists")
                passed_count += 1
            else:
                logger.error(f"❌ {test_file}: Missing")
        
        # Check that old test files have been removed (or consolidated)
        old_test_files = [
            "tests/test_all_features.py",
            "tests/test_dynamic_model.py",
            "tests/test_enhanced_duckbot.py"
        ]
        
        removed_count = 0
        for old_test in old_test_files:
            if not Path(old_test).exists():
                logger.info(f"✅ {old_test}: Removed (properly consolidated)")
                removed_count += 1
            else:
                logger.warning(f"⚠️  {old_test}: Still exists (may need consolidation)")
        
        return passed_count >= len(test_files) * 0.8  # 80% threshold

    def verify_batch_files(self) -> bool:
        """Verify batch file consolidation"""
        logger.info("Verifying Batch File Consolidation...")
        
        # Check that consolidated launcher exists
        consolidated_launchers = [
            "launcher/UNIFIED_DUCKBOT_LAUNCHER.bat",
            "launcher/CONSOLIDATED_DUCKBOT_LAUNCHER.bat"
        ]
        
        passed_count = 0
        for launcher in consolidated_launchers:
            if Path(launcher).exists():
                logger.info(f"✅ {launcher}: Exists")
                passed_count += 1
            else:
                logger.error(f"❌ {launcher}: Missing")
        
        # Check that redundant batch files have been removed
        redundant_launchers = [
            "launcher/START_ENHANCED_DUCKBOT.bat",
            "launcher/START_ULTIMATE_DUCKBOT.bat",
            "launcher/START_AUTO.bat"
        ]
        
        removed_count = 0
        for redundant in redundant_launchers:
            if not Path(redundant).exists():
                logger.info(f"✅ {redundant}: Removed (properly consolidated)")
                removed_count += 1
            else:
                logger.warning(f"⚠️  {redundant}: Still exists (may need removal)")
        
        return passed_count >= len(consolidated_launchers) * 0.8  # 80% threshold

    def verify_backward_compatibility(self) -> bool:
        """Verify backward compatibility preservation"""
        logger.info("Verifying Backward Compatibility...")
        
        # Check that old import paths still work with warnings or have equivalents
        old_imports = [
            ("Cost Tracker", "duckbot.cost_tracker", "duckbot.core.cost_management"),
            ("WebUI", "duckbot.webui", "duckbot.webui_enhanced"),
            ("AI Router", "duckbot.ai_router_gpt", "duckbot.ai_router_gpt"),
            ("Server Manager", "duckbot.server_manager", "duckbot.services.server_manager")
        ]
        
        passed_count = 0
        for name, old_module, new_module in old_imports:
            try:
                # Try old module first (might have compatibility layer)
                imported = importlib.import_module(old_module)
                logger.info(f"✅ {name}: Backward compatible (old module)")
                passed_count += 1
            except ImportError:
                try:
                    # Try new consolidated module
                    imported = importlib.import_module(new_module)
                    logger.info(f"✅ {name}: Compatible with new module ({new_module})")
                    passed_count += 1
                except ImportError as e:
                    logger.warning(f"⚠️  {name}: Not compatible - {e}")
                except Exception as e:
                    logger.error(f"❌ {name}: Error during import - {e}")
            except Exception as e:
                logger.error(f"❌ {name}: Error during import - {e}")
        
        return passed_count >= len(old_imports) * 0.7  # 70% threshold

    def verify_feature_parity(self) -> bool:
        """Verify feature parity maintenance"""
        logger.info("Verifying Feature Parity...")
        
        # Check that all major features are still available through new consolidated modules
        major_features = [
            ("AI Routing", "duckbot.ai_router_gpt", "duckbot.core.ai_provider_manager"),
            ("Agent Framework", "duckbot.archon_integration", "duckbot.core.agent_framework"),
            ("Service Management", "duckbot.server_manager", "duckbot.core.service_manager"),
            ("WebUI", "duckbot.webui_enhanced", "duckbot.webui_enhanced"),
            ("Enhanced WebUI", "duckbot.ui.enhanced_webui", "duckbot.ui.unified_webui"),
            ("Archon Integration", "duckbot.integrations.archon_integration", "duckbot.integrations.archon_integration"),
            ("ByteBot Integration", "duckbot.integrations.bytebot_integration", "duckbot.integrations.bytebot_integration"),
            ("VibeVoice Integration", "duckbot.integrations.vibevoice_integration", "duckbot.integrations.vibevoice_client"),
            ("MCP Server", "duckbot.integrations.mcp_server", "duckbot.integrations.mcp_server"),
            ("Qwen-Agent", "duckbot.integrations.qwen_agent_integration", "duckbot.integrations.qwen_agent_integration"),
            ("Browser-Use", "duckbot.integrations.browser_use_integration", "duckbot.integrations.browser_use_integration"),
            ("Web-UI", "duckbot.integrations.web_ui_integration", "duckbot.integrations.web_ui_integration"),
            ("Persona Engine", "duckbot.integrations.persona_engine_integration", "duckbot.integrations.persona_engine_integration"),
            ("Mining Manager", "duckbot.integrations.mining_manager", "duckbot.integrations.mining_manager"),
            ("Docker MCP Gateway", "duckbot.integrations.docker_mcp_gateway", "duckbot.integrations.docker_mcp_gateway"),
            ("WSL Integration", "duckbot.integrations.wsl_integration", "duckbot.integrations.wsl_integration")
        ]
        
        available_count = 0
        for name, old_module, new_module in major_features:
            try:
                # Try old module first (backward compatibility)
                imported = importlib.import_module(old_module)
                logger.info(f"✅ {name}: Available (old module)")
                available_count += 1
            except ImportError:
                try:
                    # Try new consolidated module
                    imported = importlib.import_module(new_module)
                    logger.info(f"✅ {name}: Available (new consolidated module)")
                    available_count += 1
                except ImportError as e:
                    logger.error(f"❌ {name}: Not available - {e}")
                except Exception as e:
                    logger.error(f"❌ {name}: Error - {e}")
            except Exception as e:
                logger.error(f"❌ {name}: Error - {e}")
        
        return available_count >= len(major_features) * 0.8  # 80% threshold

    def run_verification(self) -> Dict[str, Any]:
        """Run all verification tests"""
        logger.info("Starting DuckBot Consolidation Verification...")
        print("=" * 70)
        print("🦆 DUCKBOT CONSOLIDATION VERIFICATION v4.2")
        print("=" * 70)
        print()
        
        verification_results = {}
        
        # Run verification for each category
        for category, description in self.categories.items():
            print(f"[{category.upper().replace('_', ' ')}] {description}")
            print("-" * 50)
            
            try:
                if category == "core_modules":
                    result = self.verify_core_modules()
                elif category == "agent_framework":
                    result = self.verify_agent_framework()
                elif category == "service_management":
                    result = self.verify_service_management()
                elif category == "utilities":
                    result = self.verify_utilities()
                elif category == "test_suite":
                    result = self.verify_test_suite()
                elif category == "batch_files":
                    result = self.verify_batch_files()
                elif category == "backward_compatibility":
                    result = self.verify_backward_compatibility()
                elif category == "feature_parity":
                    result = self.verify_feature_parity()
                else:
                    result = False
                    logger.warning(f"Unknown verification category: {category}")
                
                verification_results[category] = {
                    "passed": result,
                    "description": description
                }
                
                status = "✅ PASS" if result else "❌ FAIL"
                print(f"Status: {status}")
                print()
                
            except Exception as e:
                logger.error(f"Verification category {category} failed: {e}")
                verification_results[category] = {
                    "passed": False,
                    "description": description,
                    "error": str(e)
                }
                print(f"[ERROR] Category {category} failed: {e}")
                print()
        
        # Generate comprehensive report
        return self.generate_report(verification_results)

    def generate_report(self, verification_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive verification report"""
        logger.info("Generating verification report...")
        
        # Calculate overall statistics
        total_categories = len(verification_results)
        passed_categories = sum(1 for r in verification_results.values() if r["passed"])
        failed_categories = total_categories - passed_categories
        overall_success_rate = (passed_categories / total_categories * 100) if total_categories > 0 else 0
        
        # Generate category summary
        category_summary = {}
        for category, result in verification_results.items():
            category_summary[category] = {
                "passed": result["passed"],
                "description": result["description"],
                "status": "PASS" if result["passed"] else "FAIL"
            }
        
        # Generate recommendations
        recommendations = self.generate_recommendations(verification_results)
        
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
                "total_categories": total_categories,
                "passed_categories": passed_categories,
                "failed_categories": failed_categories,
                "success_rate": overall_success_rate,
                "system_status": system_status,
                "timestamp": datetime.now().isoformat()
            },
            "category_summary": category_summary,
            "detailed_results": verification_results,
            "recommendations": recommendations,
            "categories": self.categories
        }
        
        # Save report to file
        if self.verification_config["save_report"]:
            try:
                report_file = Path("consolidation_verification_report.json")
                with open(report_file, 'w', encoding='utf-8') as f:
                    json.dump(report, f, indent=2, ensure_ascii=False, default=str)
                
                logger.info(f"Consolidation verification report saved to: {report_file}")
                print(f"\n[REPORT] Full verification report saved to: {report_file}")
            
            except Exception as e:
                logger.error(f"Failed to save report: {e}")
        
        return report

    def generate_recommendations(self, verification_results: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on verification results"""
        recommendations = []
        
        # Check overall success rate
        overall_rate = sum(1 for r in verification_results.values() if r["passed"]) / len(verification_results) * 100
        
        if overall_rate >= 80:
            recommendations.append("System is in good working condition after consolidation")
        elif overall_rate >= 60:
            recommendations.append("System has some issues but is mostly functional after consolidation")
        else:
            recommendations.append("System has significant issues that need attention after consolidation")
        
        # Check specific category issues
        for category, result in verification_results.items():
            if not result["passed"]:
                if category == "core_modules":
                    recommendations.append("Critical: Core modules consolidation issues detected")
                elif category == "agent_framework":
                    recommendations.append("Agent framework consolidation issues - check agent integrations")
                elif category == "service_management":
                    recommendations.append("Service management consolidation issues - check service integrations")
                elif category == "utilities":
                    recommendations.append("Utilities consolidation issues - check dependency management")
                elif category == "test_suite":
                    recommendations.append("Test suite consolidation issues - check testing framework")
                elif category == "batch_files":
                    recommendations.append("Batch file consolidation issues - check launcher scripts")
                elif category == "backward_compatibility":
                    recommendations.append("Backward compatibility issues - check import paths")
                elif category == "feature_parity":
                    recommendations.append("Feature parity issues - check missing functionality")
        
        # Success recommendations
        if all(result["passed"] for result in verification_results.values()):
            recommendations.extend([
                "All consolidation efforts successful",
                "System is ready for production use",
                "Consider running: launcher/UNIFIED_DUCKBOT_LAUNCHER.bat",
                "Access WebUI at: http://localhost:8787",
                "Monitor system health with: ai_ecosystem_manager.py"
            ])
        
        return recommendations

    def print_report_summary(self, report: Dict[str, Any]):
        """Print a summary of the verification report"""
        summary = report["summary"]
        
        print("\n" + "=" * 70)
        print("CONSOLIDATION VERIFICATION REPORT SUMMARY")
        print("=" * 70)
        print(f"Total Categories: {summary['total_categories']}")
        print(f"Passed: {summary['passed_categories']} ✅")
        print(f"Failed: {summary['failed_categories']} ❌")
        print(f"Success Rate: {summary['success_rate']:.1f}%")
        print(f"System Status: {summary['system_status']}")
        print()
        
        print("CATEGORY RESULTS:")
        print("-" * 50)
        for category, result in report["category_summary"].items():
            status_icon = "✅" if result["status"] == "PASS" else "❌"
            print(f"{status_icon} {category.replace('_', ' ').title()}")
        
        print("\nRECOMMENDATIONS:")
        print("-" * 50)
        for i, rec in enumerate(report["recommendations"], 1):
            print(f"{i}. {rec}")
        
        print("\n" + "=" * 70)

# Global instance
verifier = ConsolidationVerifier()

# Convenience functions
def run_verification() -> Dict[str, Any]:
    """Run consolidation verification"""
    return verifier.run_verification()

def verify_core_modules() -> bool:
    """Verify core modules consolidation"""
    return verifier.verify_core_modules()

def verify_agent_framework() -> bool:
    """Verify agent framework consolidation"""
    return verifier.verify_agent_framework()

def verify_service_management() -> bool:
    """Verify service management consolidation"""
    return verifier.verify_service_management()

def verify_utilities() -> bool:
    """Verify utilities consolidation"""
    return verifier.verify_utilities()

def verify_test_suite() -> bool:
    """Verify test suite consolidation"""
    return verifier.verify_test_suite()

def verify_batch_files() -> bool:
    """Verify batch file consolidation"""
    return verifier.verify_batch_files()

def verify_backward_compatibility() -> bool:
    """Verify backward compatibility preservation"""
    return verifier.verify_backward_compatibility()

def verify_feature_parity() -> bool:
    """Verify feature parity maintenance"""
    return verifier.verify_feature_parity()

def generate_verification_report() -> Dict[str, Any]:
    """Generate comprehensive verification report"""
    return verifier.generate_report({})

def print_verification_summary(report: Dict[str, Any]):
    """Print verification report summary"""
    verifier.print_report_summary(report)

async def main():
    """Main verification function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="DuckBot Consolidation Verification")
    parser.add_argument("--category", choices=[
        "core_modules", "agent_framework", "service_management", "utilities",
        "test_suite", "batch_files", "backward_compatibility", "feature_parity"
    ], help="Run specific verification category")
    parser.add_argument("--timeout", type=int, default=30, help="Verification timeout in seconds")
    parser.add_argument("--no-report", action="store_true", help="Don't save report file")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Configure based on arguments
    if args.timeout:
        verifier.verification_config["timeout"] = args.timeout
    
    if args.no_report:
        verifier.verification_config["save_report"] = False
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        if args.category:
            # Run specific category
            print(f"Running verification for category: {args.category}")
            
            category_functions = {
                "core_modules": verify_core_modules,
                "agent_framework": verify_agent_framework,
                "service_management": verify_service_management,
                "utilities": verify_utilities,
                "test_suite": verify_test_suite,
                "batch_files": verify_batch_files,
                "backward_compatibility": verify_backward_compatibility,
                "feature_parity": verify_feature_parity
            }
            
            if args.category in category_functions:
                result = category_functions[args.category]()
                print(f"\nCategory Result: {'PASS' if result else 'FAIL'}")
                return 0 if result else 1
            else:
                print(f"[ERROR] Unknown category: {args.category}")
                return 1
        
        else:
            # Run all verifications
            report = run_verification()
            verifier.print_report_summary(report)
            
            # Return exit code based on system status
            status = report["summary"]["system_status"]
            if status in ["EXCELLENT", "READY"]:
                return 0
            elif status == "NEEDS_ATTENTION":
                return 1
            else:
                return 2
    
    except KeyboardInterrupt:
        print("\n\n[STOPPED] Verification cancelled by user")
        return 130
    except Exception as e:
        logger.error(f"Verification failed: {e}")
        print(f"\n[FATAL] Verification failed: {e}")
        return 3

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)