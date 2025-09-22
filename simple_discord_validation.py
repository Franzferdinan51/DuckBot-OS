#!/usr/bin/env python3
"""
Simple Discord Commands Validation
Validates command availability without unicode characters
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def validate_discord_commands():
    """Validate Discord commands availability"""
    results = {
        "validation_time": datetime.now().isoformat(),
        "commands_status": {},
        "integrations": {},
        "issues": [],
        "recommendations": []
    }

    try:
        # Test basic imports
        try:
            from duckbot.ui.discord_bot import DiscordBot, VIBEVOICE_AVAILABLE, COST_TRACKING_AVAILABLE, LIVEKIT_AVAILABLE, MINING_COMMANDS_AVAILABLE, ENTERTAINMENT_AVAILABLE
            results["integrations"]["discord_bot"] = "AVAILABLE"
        except Exception as e:
            results["integrations"]["discord_bot"] = f"ERROR: {str(e)}"
            results["issues"].append("Discord bot core module failed to import")

        # Test VibeVoice commands
        if VIBEVOICE_AVAILABLE:
            try:
                from duckbot.agents.vibevoice_commands import VibeVoiceCommands
                vibevoice_commands = [
                    "vibevoice_command",
                    "voice_presets_command",
                    "voice_status_command",
                    "voice_help_command"
                ]

                for cmd in vibevoice_commands:
                    if hasattr(VibeVoiceCommands, cmd):
                        results["commands_status"][f"vibevoice_{cmd}"] = "AVAILABLE"
                    else:
                        results["commands_status"][f"vibevoice_{cmd}"] = "MISSING"
                        results["issues"].append(f"VibeVoice command {cmd} is missing")

                results["integrations"]["vibevoice"] = "AVAILABLE"
            except Exception as e:
                results["integrations"]["vibevoice"] = f"ERROR: {str(e)}"
                results["issues"].append("VibeVoice commands module failed to import")
        else:
            results["integrations"]["vibevoice"] = "UNAVAILABLE"
            results["issues"].append("VibeVoice integration is not available")

        # Test entertainment commands
        if ENTERTAINMENT_AVAILABLE:
            try:
                from duckbot.discord_commands.entertainment import EntertainmentCommands
                entertainment_commands = [
                    "joke_command", "meme_command", "quote_command", "fact_command",
                    "trivia_command", "eightball_command", "rps_command", "hangman_command",
                    "userinfo_command", "serverinfo_command", "avatar_command",
                    "ping_command", "uptime_command", "invite_command", "tell_joke_command"
                ]

                for cmd in entertainment_commands:
                    if hasattr(EntertainmentCommands, cmd):
                        results["commands_status"][f"entertainment_{cmd}"] = "AVAILABLE"
                    else:
                        results["commands_status"][f"entertainment_{cmd}"] = "MISSING"
                        results["issues"].append(f"Entertainment command {cmd} is missing")

                results["integrations"]["entertainment"] = "AVAILABLE"
            except Exception as e:
                results["integrations"]["entertainment"] = f"ERROR: {str(e)}"
                results["issues"].append("Entertainment commands module failed to import")
        else:
            results["integrations"]["entertainment"] = "UNAVAILABLE"
            results["issues"].append("Entertainment commands are not available")

        # Test cost commands
        if COST_TRACKING_AVAILABLE:
            try:
                from duckbot.core.cost_management import CostCommands
                cost_commands = ["cost_summary", "cost_chart", "cost_predict"]

                for cmd in cost_commands:
                    if hasattr(CostCommands, cmd):
                        results["commands_status"][f"cost_{cmd}"] = "AVAILABLE"
                    else:
                        results["commands_status"][f"cost_{cmd}"] = "MISSING"
                        results["issues"].append(f"Cost command {cmd} is missing")

                results["integrations"]["cost_tracking"] = "AVAILABLE"
            except Exception as e:
                results["integrations"]["cost_tracking"] = f"ERROR: {str(e)}"
                results["issues"].append("Cost tracking module failed to import")
        else:
            results["integrations"]["cost_tracking"] = "UNAVAILABLE"
            results["issues"].append("Cost tracking is not available")

        # Test mining commands
        if MINING_COMMANDS_AVAILABLE:
            try:
                from duckbot.agents.mining_commands import MiningCommands
                mining_commands = [
                    "mining_status", "mining_start", "mining_stop",
                    "mining_optimize", "mining_switch", "mining_profitability", "mining_help"
                ]

                for cmd in mining_commands:
                    if hasattr(MiningCommands, cmd):
                        results["commands_status"][f"mining_{cmd}"] = "AVAILABLE"
                    else:
                        results["commands_status"][f"mining_{cmd}"] = "MISSING"
                        results["issues"].append(f"Mining command {cmd} is missing")

                results["integrations"]["mining"] = "AVAILABLE"
            except Exception as e:
                results["integrations"]["mining"] = f"ERROR: {str(e)}"
                results["issues"].append("Mining commands module failed to import")
        else:
            results["integrations"]["mining"] = "UNAVAILABLE"
            results["issues"].append("Mining commands are not available")

        # Test LiveKit commands
        if LIVEKIT_AVAILABLE:
            try:
                from duckbot.integrations.livekit_integration import LiveKitCommands
                livekit_commands = ["setup_commands", "create_voice_room_command", "list_voice_rooms_command"]

                for cmd in livekit_commands:
                    if hasattr(LiveKitCommands, cmd):
                        results["commands_status"][f"livekit_{cmd}"] = "AVAILABLE"
                    else:
                        results["commands_status"][f"livekit_{cmd}"] = "MISSING"
                        results["issues"].append(f"LiveKit command {cmd} is missing")

                results["integrations"]["livekit"] = "AVAILABLE"
            except Exception as e:
                results["integrations"]["livekit"] = f"ERROR: {str(e)}"
                results["issues"].append("LiveKit commands module failed to import")
        else:
            results["integrations"]["livekit"] = "UNAVAILABLE"
            results["issues"].append("LiveKit integration is not available")

        # Check configuration
        config_path = Path(__file__).parent / "config" / "discord_config.json"
        if config_path.exists():
            results["configuration"] = "AVAILABLE"
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                results["config_features"] = list(config.get("features", {}).keys())
            except Exception as e:
                results["configuration"] = f"ERROR: {str(e)}"
                results["issues"].append("Discord configuration file is corrupted")
        else:
            results["configuration"] = "MISSING"
            results["issues"].append("Discord configuration file is missing")

        # Check environment variables
        discord_token = os.getenv('DISCORD_BOT_TOKEN')
        if discord_token:
            results["discord_token"] = "SET"
        else:
            results["discord_token"] = "NOT_SET"
            results["issues"].append("Discord bot token is not set in environment")

        # Generate recommendations
        if results["issues"]:
            results["recommendations"].append("Fix all identified issues before deploying the bot")

        if results["integrations"].get("vibevoice") != "AVAILABLE":
            results["recommendations"].append("Install and configure VibeVoice TTS integration")

        if results["integrations"].get("mining") != "AVAILABLE":
            results["recommendations"].append("Install mining management components")

        if results["discord_token"] != "SET":
            results["recommendations"].append("Set DISCORD_BOT_TOKEN environment variable")

        results["recommendations"].extend([
            "Test all commands in a development server first",
            "Set up proper logging and monitoring",
            "Regular testing after updates"
        ])

        # Calculate statistics
        total_commands = len(results["commands_status"])
        available_commands = sum(1 for status in results["commands_status"].values() if status == "AVAILABLE")

        results["statistics"] = {
            "total_commands_checked": total_commands,
            "available_commands": available_commands,
            "availability_percentage": (available_commands / total_commands * 100) if total_commands > 0 else 0
        }

    except Exception as e:
        results["validation_error"] = f"Critical validation failure: {str(e)}"
        results["issues"].append("Validation process failed completely")

    return results

def main():
    """Main validation function"""
    print("DuckBot Discord Commands Validation")
    print("=" * 50)

    results = validate_discord_commands()

    # Print results
    print(f"\nValidation completed at: {results['validation_time']}")
    print(f"Commands checked: {results['statistics']['total_commands_checked']}")
    print(f"Available commands: {results['statistics']['available_commands']}")
    print(f"Availability rate: {results['statistics']['availability_percentage']:.1f}%")

    print(f"\nIntegration Status:")
    for integration, status in results["integrations"].items():
        print(f"  {integration}: {status}")

    if results["issues"]:
        print(f"\nIssues Found ({len(results['issues'])}):")
        for i, issue in enumerate(results["issues"], 1):
            print(f"  {i}. {issue}")
    else:
        print("\nNo issues found!")

    print(f"\nRecommendations:")
    for i, rec in enumerate(results["recommendations"], 1):
        print(f"  {i}. {rec}")

    # Save results
    with open("discord_validation_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nDetailed results saved to: discord_validation_results.json")

    return results

if __name__ == "__main__":
    main()