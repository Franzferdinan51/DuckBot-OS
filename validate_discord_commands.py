#!/usr/bin/env python3
"""
DuckBot Discord Commands Validation
Validates command availability and structure without calling Discord API
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import inspect

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import DuckBot components
try:
    from duckbot.ui.discord_bot import DiscordBot, VIBEVOICE_AVAILABLE, COST_TRACKING_AVAILABLE, LIVEKIT_AVAILABLE, MINING_COMMANDS_AVAILABLE, ENTERTAINMENT_AVAILABLE
    from duckbot.agents.vibevoice_commands import VibeVoiceCommands
    from duckbot.core.cost_management import CostCommands
    from duckbot.agents.mining_commands import MiningCommands
    from duckbot.discord_commands.entertainment import EntertainmentCommands
    from duckbot.integrations.livekit_integration import LiveKitCommands
    IMPORTS_SUCCESSFUL = True
except ImportError as e:
    print(f"❌ Import error: {e}")
    IMPORTS_SUCCESSFUL = False

logger = logging.getLogger(__name__)

class DiscordCommandsValidator:
    """Validates Discord commands availability and structure"""

    def __init__(self):
        self.validation_results = {
            "imports": {},
            "vibevoice_commands": {},
            "entertainment_commands": {},
            "cost_commands": {},
            "mining_commands": {},
            "livekit_commands": {},
            "utility_commands": {},
            "integrations": {},
            "configuration": {},
            "recommendations": []
        }
        self.validation_start_time = datetime.now()

    def validate_imports(self):
        """Validate that all required modules can be imported"""
        logger.info("Validating imports...")

        self.validation_results["imports"]["discord"] = {
            "status": "✅ AVAILABLE" if IMPORTS_SUCCESSFUL else "❌ FAILED",
            "details": "Discord.py and DuckBot modules" if IMPORTS_SUCCESSFUL else f"Import failed: {ImportError}"
        }

        # Check Discord.py
        try:
            import discord
            self.validation_results["imports"]["discord_py"] = {
                "status": "✅ AVAILABLE",
                "details": f"Discord.py version {discord.__version__}"
            }
        except ImportError:
            self.validation_results["imports"]["discord_py"] = {
                "status": "❌ UNAVAILABLE",
                "details": "Discord.py not installed"
            }

        # Check specific components
        self.validation_results["imports"]["vibevoice"] = {
            "status": "✅ AVAILABLE" if VIBEVOICE_AVAILABLE else "❌ UNAVAILABLE",
            "details": "VibeVoice commands module"
        }

        self.validation_results["imports"]["cost_tracking"] = {
            "status": "✅ AVAILABLE" if COST_TRACKING_AVAILABLE else "❌ UNAVAILABLE",
            "details": "Cost tracking module"
        }

        self.validation_results["imports"]["livekit"] = {
            "status": "✅ AVAILABLE" if LIVEKIT_AVAILABLE else "❌ UNAVAILABLE",
            "details": "LiveKit integration module"
        }

        self.validation_results["imports"]["mining"] = {
            "status": "✅ AVAILABLE" if MINING_COMMANDS_AVAILABLE else "❌ UNAVAILABLE",
            "details": "Mining commands module"
        }

        self.validation_results["imports"]["entertainment"] = {
            "status": "✅ AVAILABLE" if ENTERTAINMENT_AVAILABLE else "❌ UNAVAILABLE",
            "details": "Entertainment commands module"
        }

    def validate_vibevoice_commands(self):
        """Validate VibeVoice command structure"""
        logger.info("Validating VibeVoice commands...")

        if not VIBEVOICE_AVAILABLE:
            self.validation_results["vibevoice_commands"]["availability"] = {
                "status": "❌ UNAVAILABLE",
                "details": "VibeVoice commands module not available"
            }
            return

        try:
            # Check command methods
            vibevoice_methods = [
                ("vibevoice_command", "Generate multi-speaker voice content"),
                ("voice_presets_command", "Show available voice presets"),
                ("voice_status_command", "Check VibeVoice service status"),
                ("voice_help_command", "Show VibeVoice help guide")
            ]

            for method_name, description in vibevoice_methods:
                if hasattr(VibeVoiceCommands, method_name):
                    method = getattr(VibeVoiceCommands, method_name)
                    if callable(method):
                        self.validation_results["vibevoice_commands"][method_name] = {
                            "status": "✅ AVAILABLE",
                            "details": description
                        }
                    else:
                        self.validation_results["vibevoice_commands"][method_name] = {
                            "status": "⚠️ NOT CALLABLE",
                            "details": f"Method {method_name} exists but is not callable"
                        }
                else:
                    self.validation_results["vibevoice_commands"][method_name] = {
                        "status": "❌ MISSING",
                        "details": f"Method {method_name} not found"
                    }

        except Exception as e:
            self.validation_results["vibevoice_commands"]["validation_error"] = {
                "status": "❌ ERROR",
                "details": f"Validation failed: {str(e)}"
            }

    def validate_entertainment_commands(self):
        """Validate entertainment command structure"""
        logger.info("Validating entertainment commands...")

        if not ENTERTAINMENT_AVAILABLE:
            self.validation_results["entertainment_commands"]["availability"] = {
                "status": "❌ UNAVAILABLE",
                "details": "Entertainment commands module not available"
            }
            return

        try:
            # Check entertainment command methods
            entertainment_methods = [
                ("joke_command", "Get random joke"),
                ("meme_command", "Get random meme"),
                ("quote_command", "Get inspirational quote"),
                ("fact_command", "Get interesting fact"),
                ("trivia_command", "Start trivia quiz"),
                ("eightball_command", "Magic 8-ball"),
                ("rps_command", "Rock Paper Scissors game"),
                ("hangman_command", "Hangman game"),
                ("userinfo_command", "User information"),
                ("serverinfo_command", "Server information"),
                ("avatar_command", "User avatar"),
                ("ping_command", "Bot latency"),
                ("uptime_command", "Bot uptime"),
                ("invite_command", "Bot invite link"),
                ("tell_joke_command", "VibeVoice joke telling")
            ]

            for method_name, description in entertainment_methods:
                if hasattr(EntertainmentCommands, method_name):
                    method = getattr(EntertainmentCommands, method_name)
                    if callable(method):
                        self.validation_results["entertainment_commands"][method_name] = {
                            "status": "✅ AVAILABLE",
                            "details": description
                        }
                    else:
                        self.validation_results["entertainment_commands"][method_name] = {
                            "status": "⚠️ NOT CALLABLE",
                            "details": f"Method {method_name} exists but is not callable"
                        }
                else:
                    self.validation_results["entertainment_commands"][method_name] = {
                        "status": "❌ MISSING",
                        "details": f"Method {method_name} not found"
                    }

        except Exception as e:
            self.validation_results["entertainment_commands"]["validation_error"] = {
                "status": "❌ ERROR",
                "details": f"Validation failed: {str(e)}"
            }

    def validate_cost_commands(self):
        """Validate cost tracking command structure"""
        logger.info("Validating cost commands...")

        if not COST_TRACKING_AVAILABLE:
            self.validation_results["cost_commands"]["availability"] = {
                "status": "❌ UNAVAILABLE",
                "details": "Cost tracking module not available"
            }
            return

        try:
            # Check cost command methods
            cost_methods = [
                ("cost_summary", "Get cost usage summary"),
                ("cost_chart", "Generate cost visualization"),
                ("cost_predict", "Get cost predictions")
            ]

            for method_name, description in cost_methods:
                if hasattr(CostCommands, method_name):
                    method = getattr(CostCommands, method_name)
                    if callable(method):
                        self.validation_results["cost_commands"][method_name] = {
                            "status": "✅ AVAILABLE",
                            "details": description
                        }
                    else:
                        self.validation_results["cost_commands"][method_name] = {
                            "status": "⚠️ NOT CALLABLE",
                            "details": f"Method {method_name} exists but is not callable"
                        }
                else:
                    self.validation_results["cost_commands"][method_name] = {
                        "status": "❌ MISSING",
                        "details": f"Method {method_name} not found"
                    }

        except Exception as e:
            self.validation_results["cost_commands"]["validation_error"] = {
                "status": "❌ ERROR",
                "details": f"Validation failed: {str(e)}"
            }

    def validate_mining_commands(self):
        """Validate mining command structure"""
        logger.info("Validating mining commands...")

        if not MINING_COMMANDS_AVAILABLE:
            self.validation_results["mining_commands"]["availability"] = {
                "status": "❌ UNAVAILABLE",
                "details": "Mining commands module not available"
            }
            return

        try:
            # Check mining command methods
            mining_methods = [
                ("mining_status", "Get mining status"),
                ("mining_start", "Start mining"),
                ("mining_stop", "Stop mining"),
                ("mining_optimize", "Get mining optimization"),
                ("mining_switch", "Switch mining software"),
                ("mining_profitability", "Check mining profitability"),
                ("mining_help", "Mining help")
            ]

            for method_name, description in mining_methods:
                if hasattr(MiningCommands, method_name):
                    method = getattr(MiningCommands, method_name)
                    if callable(method):
                        self.validation_results["mining_commands"][method_name] = {
                            "status": "✅ AVAILABLE",
                            "details": description
                        }
                    else:
                        self.validation_results["mining_commands"][method_name] = {
                            "status": "⚠️ NOT CALLABLE",
                            "details": f"Method {method_name} exists but is not callable"
                        }
                else:
                    self.validation_results["mining_commands"][method_name] = {
                        "status": "❌ MISSING",
                        "details": f"Method {method_name} not found"
                    }

        except Exception as e:
            self.validation_results["mining_commands"]["validation_error"] = {
                "status": "❌ ERROR",
                "details": f"Validation failed: {str(e)}"
            }

    def validate_livekit_commands(self):
        """Validate LiveKit command structure"""
        logger.info("Validating LiveKit commands...")

        if not LIVEKIT_AVAILABLE:
            self.validation_results["livekit_commands"]["availability"] = {
                "status": "❌ UNAVAILABLE",
                "details": "LiveKit integration module not available"
            }
            return

        try:
            # Check LiveKit command methods
            livekit_methods = [
                ("setup_commands", "Setup LiveKit commands"),
                ("create_voice_room_command", "Create voice conference room"),
                ("list_voice_rooms_command", "List voice conference rooms")
            ]

            for method_name, description in livekit_methods:
                if hasattr(LiveKitCommands, method_name):
                    method = getattr(LiveKitCommands, method_name)
                    if callable(method):
                        self.validation_results["livekit_commands"][method_name] = {
                            "status": "✅ AVAILABLE",
                            "details": description
                        }
                    else:
                        self.validation_results["livekit_commands"][method_name] = {
                            "status": "⚠️ NOT CALLABLE",
                            "details": f"Method {method_name} exists but is not callable"
                        }
                else:
                    self.validation_results["livekit_commands"][method_name] = {
                        "status": "❌ MISSING",
                        "details": f"Method {method_name} not found"
                    }

        except Exception as e:
            self.validation_results["livekit_commands"]["validation_error"] = {
                "status": "❌ ERROR",
                "details": f"Validation failed: {str(e)}"
            }

    def validate_utility_commands(self):
        """Validate utility command structure"""
        logger.info("Validating utility commands...")

        try:
            # Check DiscordBot utility methods
            utility_methods = [
                ("check_permissions", "Check user permissions"),
                ("get_user_voice_channel", "Get user voice channel"),
                ("join_voice_channel", "Join voice channel"),
                ("leave_voice_channel", "Leave voice channel"),
                ("start_service", "Start bot service"),
                ("stop_service", "Stop bot service")
            ]

            for method_name, description in utility_methods:
                if hasattr(DiscordBot, method_name):
                    method = getattr(DiscordBot, method_name)
                    if callable(method):
                        self.validation_results["utility_commands"][method_name] = {
                            "status": "✅ AVAILABLE",
                            "details": description
                        }
                    else:
                        self.validation_results["utility_commands"][method_name] = {
                            "status": "⚠️ NOT CALLABLE",
                            "details": f"Method {method_name} exists but is not callable"
                        }
                else:
                    self.validation_results["utility_commands"][method_name] = {
                        "status": "❌ MISSING",
                        "details": f"Method {method_name} not found"
                    }

        except Exception as e:
            self.validation_results["utility_commands"]["validation_error"] = {
                "status": "❌ ERROR",
                "details": f"Validation failed: {str(e)}"
            }

    def validate_integrations(self):
        """Validate integration availability"""
        logger.info("Validating integrations...")

        try:
            # Check VibeVoice integration
            try:
                from duckbot.integrations.vibevoice_client import vibevoice_integration
                if vibevoice_integration and hasattr(vibevoice_integration, 'available'):
                    status = "✅ AVAILABLE" if vibevoice_integration.available else "⚠️ UNAVAILABLE"
                    self.validation_results["integrations"]["vibevoice"] = {
                        "status": status,
                        "details": "Microsoft VibeVoice TTS integration"
                    }
                else:
                    self.validation_results["integrations"]["vibevoice"] = {
                        "status": "⚠️ IMPROPERLY CONFIGURED",
                        "details": "VibeVoice integration exists but not properly configured"
                    }
            except ImportError:
                self.validation_results["integrations"]["vibevoice"] = {
                    "status": "❌ NOT INSTALLED",
                    "details": "VibeVoice integration not installed"
                }

            # Check LiveKit integration
            try:
                from duckbot.integrations.livekit_integration import LiveKitIntegration
                self.validation_results["integrations"]["livekit"] = {
                    "status": "✅ AVAILABLE",
                    "details": "LiveKit voice conference integration"
                }
            except ImportError:
                self.validation_results["integrations"]["livekit"] = {
                    "status": "❌ NOT INSTALLED",
                    "details": "LiveKit integration not installed"
                }

            # Check mining integration
            try:
                from duckbot.integrations.mining_manager import MiningManager
                self.validation_results["integrations"]["mining"] = {
                    "status": "✅ AVAILABLE",
                    "details": "Mining management integration"
                }
            except ImportError:
                self.validation_results["integrations"]["mining"] = {
                    "status": "❌ NOT INSTALLED",
                    "details": "Mining management integration not installed"
                }

            # Check cost tracking integration
            try:
                from duckbot.core.cost_management import CostTracker
                self.validation_results["integrations"]["cost_tracking"] = {
                    "status": "✅ AVAILABLE",
                    "details": "Cost tracking integration"
                }
            except ImportError:
                self.validation_results["integrations"]["cost_tracking"] = {
                    "status": "❌ NOT INSTALLED",
                    "details": "Cost tracking integration not installed"
                }

        except Exception as e:
            self.validation_results["integrations"]["validation_error"] = {
                "status": "❌ ERROR",
                "details": f"Integration validation failed: {str(e)}"
            }

    def validate_configuration(self):
        """Validate configuration files"""
        logger.info("Validating configuration...")

        try:
            # Check Discord configuration
            config_path = Path(__file__).parent / "config" / "discord_config.json"
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = json.load(f)

                self.validation_results["configuration"]["discord_config"] = {
                    "status": "✅ LOADED",
                    "details": f"Discord configuration loaded with {len(config)} sections"
                }

                # Check specific configurations
                if "rate_limits" in config:
                    self.validation_results["configuration"]["rate_limits"] = {
                        "status": "✅ CONFIGURED",
                        "details": f"Rate limits configured for {len(config['rate_limits'])} command types"
                    }

                if "features" in config:
                    features = config["features"]
                    self.validation_results["configuration"]["features"] = {
                        "status": "✅ CONFIGURED",
                        "details": f"Features configured: {', '.join(features.keys())}"
                    }

                    # Check VibeVoice configuration
                    if "vibevoice" in features:
                        vibevoice_config = features["vibevoice"]
                        if "presets" in vibevoice_config:
                            self.validation_results["configuration"]["vibevoice_presets"] = {
                                "status": "✅ CONFIGURED",
                                "details": f"{len(vibevoice_config['presets'])} voice presets configured"
                            }
            else:
                self.validation_results["configuration"]["discord_config"] = {
                    "status": "❌ MISSING",
                    "details": "Discord configuration file not found"
                }

            # Check environment variables
            discord_token = os.getenv('DISCORD_BOT_TOKEN')
            if discord_token:
                self.validation_results["configuration"]["discord_token"] = {
                    "status": "✅ SET",
                    "details": "Discord bot token is configured"
                }
            else:
                self.validation_results["configuration"]["discord_token"] = {
                    "status": "⚠️ NOT SET",
                    "details": "Discord bot token not set in environment"
                }

        except Exception as e:
            self.validation_results["configuration"]["validation_error"] = {
                "status": "❌ ERROR",
                "details": f"Configuration validation failed: {str(e)}"
            }

    def generate_recommendations(self):
        """Generate recommendations based on validation results"""
        recommendations = []

        # Check overall availability
        available_commands = 0
        total_commands = 0

        for category, commands in self.validation_results.items():
            if category in ["imports", "integrations", "configuration", "recommendations"]:
                continue

            for command_name, result in commands.items():
                if command_name in ["availability", "validation_error"]:
                    continue

                total_commands += 1
                if result["status"].startswith("✅"):
                    available_commands += 1

        # Generate recommendations based on availability
        if available_commands / total_commands < 0.8:
            recommendations.append("🔧 Multiple commands are unavailable - check installations and dependencies")

        # Check specific recommendations
        if self.validation_results.get("imports", {}).get("vibevoice", {}).get("status") == "❌ UNAVAILABLE":
            recommendations.append("🎙️ Install VibeVoice TTS integration")

        if self.validation_results.get("imports", {}).get("mining", {}).get("status") == "❌ UNAVAILABLE":
            recommendations.append("⛏️ Install mining management components")

        if self.validation_results.get("configuration", {}).get("discord_token", {}).get("status") == "⚠️ NOT SET":
            recommendations.append("🔑 Set DISCORD_BOT_TOKEN environment variable")

        if self.validation_results.get("integrations", {}).get("livekit", {}).get("status") == "❌ NOT INSTALLED":
            recommendations.append("🎤 Install LiveKit for voice conference features")

        # General recommendations
        recommendations.extend([
            "📊 Test bot in a development server before production use",
            "🛡️ Set up proper error handling and logging",
            "🔍 Monitor command usage and performance",
            "📝 Keep documentation updated with available commands",
            "🧪 Regular testing after updates"
        ])

        self.validation_results["recommendations"] = recommendations

    def generate_validation_report(self):
        """Generate comprehensive validation report"""
        logger.info("Generating validation report...")

        report = {
            "validation_summary": {
                "start_time": self.validation_start_time.isoformat(),
                "end_time": datetime.now().isoformat(),
                "duration": str(datetime.now() - self.validation_start_time),
                "total_commands_checked": 0,
                "available_commands": 0,
                "unavailable_commands": 0,
                "warning_commands": 0
            },
            "detailed_results": self.validation_results,
            "recommendations": self.validation_results.get("recommendations", [])
        }

        # Calculate statistics
        for category, commands in self.validation_results.items():
            if category in ["imports", "integrations", "configuration", "recommendations"]:
                continue

            for command_name, result in commands.items():
                if command_name in ["availability", "validation_error"]:
                    continue

                report["validation_summary"]["total_commands_checked"] += 1

                if result["status"].startswith("✅"):
                    report["validation_summary"]["available_commands"] += 1
                elif result["status"].startswith("❌"):
                    report["validation_summary"]["unavailable_commands"] += 1
                elif result["status"].startswith("⚠️"):
                    report["validation_summary"]["warning_commands"] += 1

        return report

    async def run_validation(self):
        """Run complete validation"""
        logger.info("Starting comprehensive Discord commands validation...")

        # Run all validation steps
        self.validate_imports()
        self.validate_vibevoice_commands()
        self.validate_entertainment_commands()
        self.validate_cost_commands()
        self.validate_mining_commands()
        self.validate_livekit_commands()
        self.validate_utility_commands()
        self.validate_integrations()
        self.validate_configuration()
        self.generate_recommendations()

        # Generate report
        report = self.generate_validation_report()

        return report

async def main():
    """Main validation function"""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Run validation
    validator = DiscordCommandsValidator()
    report = await validator.run_validation()

    # Print summary
    print("\n" + "="*80)
    print("DUCKBOT DISCORD COMMANDS VALIDATION REPORT")
    print("="*80)

    summary = report["validation_summary"]
    print(f"Validation Duration: {summary['duration']}")
    print(f"Total Commands Checked: {summary['total_commands_checked']}")
    print(f"✅ Available: {summary['available_commands']}")
    print(f"❌ Unavailable: {summary['unavailable_commands']}")
    print(f"⚠️ Warnings: {summary['warning_commands']}")
    print(f"Availability Rate: {(summary['available_commands']/summary['total_commands_checked']*100):.1f}%")

    print("\nCATEGORY RESULTS:")
    print("-"*80)

    categories = [
        ("imports", "Module Imports"),
        ("vibevoice_commands", "VibeVoice Commands"),
        ("entertainment_commands", "Entertainment Commands"),
        ("cost_commands", "Cost Commands"),
        ("mining_commands", "Mining Commands"),
        ("livekit_commands", "LiveKit Commands"),
        ("utility_commands", "Utility Commands"),
        ("integrations", "Integration Status"),
        ("configuration", "Configuration Status")
    ]

    for category_key, category_name in categories:
        if category_key in report["detailed_results"]:
            print(f"\n{category_name}:")
            category_results = report["detailed_results"][category_key]
            for test_name, result in category_results.items():
                print(f"  {result['status']} {test_name.replace('_', ' ').title()}")
                if result.get("details"):
                    print(f"    {result['details']}")

    print("\nRECOMMENDATIONS:")
    print("-"*80)
    for i, rec in enumerate(report["recommendations"], 1):
        print(f"{i}. {rec}")

    # Save report to file
    report_path = Path("discord_commands_validation_report.json")
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"\nFull report saved to: {report_path}")

    return report

if __name__ == "__main__":
    asyncio.run(main())