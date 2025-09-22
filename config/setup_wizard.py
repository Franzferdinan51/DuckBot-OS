#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DuckBot API Key Setup Wizard
Interactive wizard for configuring API keys for DuckBot v4.2
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
import inquirer
from inquirer.themes import GreenPassion
import yaml

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from api_key_manager import APIKeyManager, get_api_key_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DuckBotSetupWizard:
    """Interactive setup wizard for DuckBot API keys"""

    def __init__(self):
        self.api_manager = get_api_key_manager()
        self.config_dir = Path(__file__).parent
        self.setup_log = self.config_dir / "setup_wizard.log"

    def clear_screen(self):
        """Clear the terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')

    def print_header(self):
        """Print the wizard header"""
        self.clear_screen()
        print("=" * 70)
        print("🦆 DuckBot v4.2 API Key Setup Wizard")
        print("=" * 70)
        print("This wizard will help you configure API keys for DuckBot services.")
        print("All keys are stored locally in your .env file.")
        print("=" * 70)
        print()

    def print_configuration_summary(self):
        """Print current configuration summary"""
        summary = self.api_manager.get_configuration_summary()

        print("\n📊 Current Configuration Summary:")
        print("-" * 50)
        print(f"Total API Keys: {summary['total_keys']}")
        print(f"Required Keys: {summary['required_keys']}")
        print(f"Configured Keys: {summary['configured_keys']}")
        print(f"Valid Keys: {summary['valid_keys']}")
        print()

        print("🔑 Key Status:")
        for key_name, key_info in summary['keys'].items():
            status_icon = "✅" if key_info['valid'] else "⚠️" if key_info['configured'] else "❌"
            required_icon = "🔒" if key_info['required'] else "🔓"
            print(f"  {status_icon} {required_icon} {key_info['name']}")
            if key_info['configured']:
                print(f"      Status: {key_info['status']}")
                print(f"      Value: {key_info['masked_value']}")
            else:
                print(f"      Status: Not configured")

    def get_key_setup_instructions(self, key_name: str) -> str:
        """Get setup instructions for a specific key"""
        return self.api_manager.get_setup_instructions(key_name)

    def setup_api_key(self, key_name: str) -> bool:
        """Interactive setup for a specific API key"""
        if key_name not in self.api_manager.api_configs:
            print(f"❌ Unknown API key: {key_name}")
            return False

        config = self.api_manager.api_configs[key_name]

        while True:
            self.clear_screen()
            print(f"🔑 Setting up: {config.name}")
            print("=" * 50)
            print(f"Environment Variable: {config.env_var}")
            print(f"Required: {'Yes' if config.required else 'No'}")
            print()

            print("📋 Setup Instructions:")
            print("-" * 30)
            instructions = self.get_key_setup_instructions(key_name)
            print(instructions)
            print()

            # Ask if user wants to enter the key now
            if not inquirer.confirm(
                "Do you want to enter the API key now?",
                default=True
            ):
                return False

            # Get the API key
            questions = [
                inquirer.Password(
                    'api_key',
                    message=f"Enter your {config.name}:"
                )
            ]

            answers = inquirer.prompt(questions)
            api_key = answers['api_key'].strip()

            if not api_key:
                print("❌ No API key entered.")
                if not inquirer.confirm("Try again?", default=True):
                    return False
                continue

            # Validate the key
            print("\n🔍 Validating API key...")
            validation = self.api_manager.validate_api_key(key_name)

            # Try to set the key first
            if self.api_manager.set_api_key(key_name, api_key):
                print(f"✅ {config.name} has been set.")
                print(f"   Value: {self.api_manager.mask_api_key(api_key, key_name)}")

                if validation.status.value == 'valid':
                    print("✅ API key validation successful!")
                    if validation.response_time:
                        print(f"   Response time: {validation.response_time:.2f}s")
                    return True
                else:
                    print(f"⚠️  API key saved but validation failed: {validation.error_message}")
                    if inquirer.confirm("Continue anyway?", default=True):
                        return True
                    else:
                        # Remove the key if validation failed and user wants to retry
                        self.api_manager.set_api_key(key_name, "")
                        return False
            else:
                print("❌ Failed to set API key. Please check the format and try again.")
                if not inquirer.confirm("Try again?", default=True):
                    return False

    def setup_required_keys(self) -> bool:
        """Setup all required API keys"""
        required_keys = [name for name, config in self.api_manager.api_configs.items() if config.required]

        if not required_keys:
            print("✅ No required API keys to configure.")
            return True

        print(f"\n🔒 Required API Keys ({len(required_keys)}):")
        for key_name in required_keys:
            config = self.api_manager.api_configs[key_name]
            print(f"  • {config.name}")

        if not inquirer.confirm("\nProceed with setting up required keys?", default=True):
            return False

        success_count = 0
        for key_name in required_keys:
            print(f"\n--- Setting up {key_name} ---")
            if self.setup_api_key(key_name):
                success_count += 1

        print(f"\n✅ Successfully configured {success_count}/{len(required_keys)} required keys.")
        return success_count == len(required_keys)

    def setup_optional_keys(self):
        """Setup optional API keys"""
        optional_keys = [name for name, config in self.api_manager.api_configs.items() if not config.required]

        if not optional_keys:
            return

        print(f"\n🔓 Optional API Keys ({len(optional_keys)}):")
        for key_name in optional_keys:
            config = self.api_manager.api_configs[key_name]
            print(f"  • {config.name}")

        if not inquirer.confirm("\nDo you want to configure any optional keys?", default=False):
            return

        while True:
            print("\nSelect an optional key to configure:")
            choices = [
                (self.api_manager.api_configs[key].name, key)
                for key in optional_keys
            ]
            choices.append(("← Back to main menu", "back"))

            question = [
                inquirer.List(
                    'key_choice',
                    message="Select key to configure:",
                    choices=choices
                )
            ]

            answers = inquirer.prompt(question)
            choice = answers['key_choice']

            if choice == "back":
                break

            self.setup_api_key(choice)

    def validate_configuration(self) -> bool:
        """Validate the current configuration"""
        print("\n🔍 Validating Configuration...")
        print("-" * 40)

        validations = self.api_manager.validate_all_keys()
        all_valid = True

        for key_name, validation in validations.items():
            config = self.api_manager.api_configs[key_name]
            status_icon = "✅" if validation.status.value == 'valid' else "❌"
            required_mark = "🔒" if config.required else "🔓"

            print(f"{status_icon} {required_mark} {config.name}")
            print(f"   Status: {validation.status.value}")

            if validation.status.value != 'valid':
                all_valid = False
                if validation.error_message:
                    print(f"   Error: {validation.error_message}")
            else:
                if validation.response_time:
                    print(f"   Response time: {validation.response_time:.2f}s")

            print()

        if all_valid:
            print("✅ All configured API keys are valid!")
            return True
        else:
            print("❌ Some API keys have issues.")
            return False

    def test_duckbot_connectivity(self) -> bool:
        """Test DuckBot connectivity with current configuration"""
        print("\n🧪 Testing DuckBot Connectivity...")
        print("-" * 40)

        # Test OpenRouter connectivity
        openrouter_key = self.api_manager.get_api_key("openrouter")
        if openrouter_key:
            try:
                import requests
                response = requests.get(
                    "https://openrouter.ai/api/v1/models",
                    headers={"Authorization": f"Bearer {openrouter_key}"},
                    timeout=10
                )
                if response.status_code == 200:
                    print("✅ OpenRouter connectivity: SUCCESS")
                    models = response.json().get('data', [])
                    print(f"   Available models: {len(models)}")
                else:
                    print(f"❌ OpenRouter connectivity: FAILED ({response.status_code})")
                    return False
            except Exception as e:
                print(f"❌ OpenRouter connectivity: ERROR ({str(e)})")
                return False
        else:
            print("⚠️  OpenRouter key not configured")

        # Test Discord connectivity if token exists
        discord_token = self.api_manager.get_api_key("discord")
        if discord_token:
            try:
                import requests
                response = requests.get(
                    "https://discord.com/api/v10/users/@me",
                    headers={"Authorization": f"Bot {discord_token}"},
                    timeout=10
                )
                if response.status_code == 200:
                    print("✅ Discord connectivity: SUCCESS")
                    bot_info = response.json()
                    print(f"   Bot username: {bot_info.get('username', 'Unknown')}")
                else:
                    print(f"❌ Discord connectivity: FAILED ({response.status_code})")
                    return False
            except Exception as e:
                print(f"❌ Discord connectivity: ERROR ({str(e)})")
                return False
        else:
            print("⚠️  Discord token not configured")

        return True

    def save_configuration_report(self):
        """Save a configuration report"""
        summary = self.api_manager.get_configuration_summary()
        report_file = self.config_dir / "configuration_report.json"

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        print(f"📄 Configuration report saved to: {report_file}")

    def run(self):
        """Run the setup wizard"""
        try:
            self.print_header()
            self.print_configuration_summary()

            while True:
                print("\n🎯 Setup Options:")
                print("1. 🔒 Setup Required API Keys")
                print("2. 🔓 Setup Optional API Keys")
                print("3. 🔍 Validate Current Configuration")
                print("4. 🧪 Test Connectivity")
                print("5. 📊 View Configuration Summary")
                print("6. 💾 Save Configuration Report")
                print("7. 🚀 Exit Setup Wizard")

                choice = input("\nSelect an option (1-7): ").strip()

                if choice == "1":
                    self.setup_required_keys()
                elif choice == "2":
                    self.setup_optional_keys()
                elif choice == "3":
                    self.validate_configuration()
                elif choice == "4":
                    self.test_duckbot_connectivity()
                elif choice == "5":
                    self.print_configuration_summary()
                elif choice == "6":
                    self.save_configuration_report()
                elif choice == "7":
                    print("\n👋 Setup wizard complete!")
                    print("Your DuckBot v4.2 configuration has been saved.")
                    break
                else:
                    print("❌ Invalid choice. Please try again.")

                if choice != "7":
                    input("\nPress Enter to continue...")

        except KeyboardInterrupt:
            print("\n\n👋 Setup wizard interrupted by user.")
        except Exception as e:
            logger.error(f"Setup wizard error: {e}")
            print(f"\n❌ An error occurred: {e}")
            print("Please check the logs for more information.")

def main():
    """Main entry point"""
    # Check if required dependencies are available
    try:
        import inquirer
    except ImportError:
        print("❌ Missing required dependency: inquirer")
        print("Please install it with: pip install inquirer")
        return 1

    # Run the wizard
    wizard = DuckBotSetupWizard()
    wizard.run()

    return 0

if __name__ == "__main__":
    sys.exit(main())