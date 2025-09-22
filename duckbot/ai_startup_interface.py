#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DuckBot AI-Powered Startup Interface
Advanced terminal-based startup system with AI integration and API management
"""

import os
import sys
import json
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime

# Try to import Charm tools
try:
    from duckbot.ui.charm_manager import CharmManager
    CHARM_AVAILABLE = True
except ImportError:
    CHARM_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class APIKeys:
    """API key configuration"""
    gemini_api_key: Optional[str] = None
    openrouter_api_key: Optional[str] = None
    zai_api_key: Optional[str] = None
    zai_coding_plan: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'APIKeys':
        return cls(**data)

@dataclass
class StartupMode:
    """Startup mode configuration"""
    id: str
    name: str
    description: str
    category: str
    requires_api: List[str] = None
    ai_powered: bool = True
    port: Optional[int] = None

    def __post_init__(self):
        if self.requires_api is None:
            self.requires_api = []

class AIStartupInterface:
    """AI-Powered Startup Interface with Charm integration"""

    def __init__(self):
        self.charm_manager = None
        self.api_keys = APIKeys()
        self.startup_modes = self._initialize_startup_modes()
        self.config_file = Path("config/startup_config.json")
        self._load_config()

        if CHARM_AVAILABLE:
            try:
                self.charm_manager = CharmManager()
            except Exception as e:
                logger.error(f"Error initializing Charm manager: {e}")

    def _initialize_startup_modes(self) -> List[StartupMode]:
        """Initialize all available startup modes"""
        return [
            # AI-Enhanced Modes
            StartupMode(
                id="ai_enhanced",
                name="AI-Enhanced WebUI Dashboard",
                description="Complete AI-powered dashboard with all features",
                category="AI Enhanced",
                requires_api=["openrouter"],
                port=8788
            ),
            StartupMode(
                id="local_only",
                name="Local-Only Privacy Mode",
                description="Complete privacy with local AI models",
                category="AI Enhanced",
                ai_powered=True
            ),
            StartupMode(
                id="ultimate_complete",
                name="Ultimate Complete AI System",
                description="Full AI ecosystem with all integrations",
                category="AI Enhanced",
                requires_api=["openrouter", "gemini"],
                ai_powered=True
            ),

            # Individual Component Modes
            StartupMode(
                id="bytebot",
                name="ByteBot Desktop Automation",
                description="AI-powered desktop control and automation",
                category="Individual Components",
                requires_api=["gemini"],
                ai_powered=True
            ),
            StartupMode(
                id="ui_tars",
                name="UI-TARS GUI Automation",
                description="Visual AI for GUI automation and control",
                category="Individual Components",
                requires_api=["gemini"],
                ai_powered=True
            ),
            StartupMode(
                id="archon",
                name="Archon Multi-Agent System",
                description="Coordinated AI agents for complex tasks",
                category="Individual Components",
                requires_api=["openrouter"],
                ai_powered=True
            ),
            StartupMode(
                id="livekit",
                name="LiveKit Real-Time Communication",
                description="WebRTC-based communication platform",
                category="Individual Components",
                ai_powered=True
            ),
            StartupMode(
                id="n8n_agent",
                name="N8N Workflow Automation",
                description="AI-powered business process automation",
                category="Individual Components",
                requires_api=["zai"],
                ai_powered=True
            ),
            StartupMode(
                id="learning_system",
                name="AI Learning System",
                description="Adaptive AI with continuous learning",
                category="Individual Components",
                requires_api=["gemini"],
                ai_powered=True
            ),
            StartupMode(
                id="mcp_server",
                name="MCP Server",
                description="Model Context Protocol for AI integration",
                category="Individual Components",
                ai_powered=True
            ),

            # Interface Modes
            StartupMode(
                id="charm_terminal",
                name="Charm Terminal Interface",
                description="Beautiful terminal-based AI interface",
                category="Interfaces",
                ai_powered=True
            ),
            StartupMode(
                id="webui_stack",
                name="Complete WebUI Stack",
                description="All web interfaces in one launch",
                category="Interfaces",
                port=8788
            ),
            StartupMode(
                id="ai_monitor",
                name="AI System Monitor",
                description="Real-time AI monitoring and optimization",
                category="Interfaces",
                port=8789
            ),

            # Development Modes
            StartupMode(
                id="development",
                name="Development Environment",
                description="Full development setup with tools",
                category="Development",
                ai_powered=True
            ),
        ]

    def _load_config(self):
        """Load configuration from file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.api_keys = APIKeys.from_dict(config.get('api_keys', {}))
            except Exception as e:
                logger.error(f"Error loading config: {e}")

    def _save_config(self):
        """Save configuration to file"""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump({'api_keys': self.api_keys.to_dict()}, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving config: {e}")

    def check_api_requirements(self, mode: StartupMode) -> Dict[str, bool]:
        """Check if required API keys are available"""
        requirements = {}
        for api in mode.requires_api:
            if api == "gemini":
                requirements["gemini"] = bool(self.api_keys.gemini_api_key)
            elif api == "openrouter":
                requirements["openrouter"] = bool(self.api_keys.openrouter_api_key)
            elif api == "zai":
                requirements["zai"] = bool(self.api_keys.zai_api_key)
        return requirements

    def setup_api_keys(self):
        """Interactive API key setup"""
        print("\n" + "="*60)
        print("🔑 API KEY SETUP")
        print("="*60)

        # Gemini API Key
        if not self.api_keys.gemini_api_key:
            print("\n🤖 Gemini API Key (for AI-powered features):")
            gemini_key = input("Enter Gemini API Key (or press Enter to skip): ").strip()
            if gemini_key:
                self.api_keys.gemini_api_key = gemini_key
                print("✅ Gemini API Key saved")

        # OpenRouter API Key
        if not self.api_keys.openrouter_api_key:
            print("\n🌐 OpenRouter API Key (for cloud AI models):")
            openrouter_key = input("Enter OpenRouter API Key (or press Enter to skip): ").strip()
            if openrouter_key:
                self.api_keys.openrouter_api_key = openrouter_key
                print("✅ OpenRouter API Key saved")

        # Z.ai API Key
        if not self.api_keys.zai_api_key:
            print("\n⚡ Z.ai API Key (for coding assistance):")
            zai_key = input("Enter Z.ai API Key (or press Enter to skip): ").strip()
            if zai_key:
                self.api_keys.zai_api_key = zai_key
                print("✅ Z.ai API Key saved")

        # Z.ai Coding Plan
        if not self.api_keys.zai_coding_plan:
            print("\n💻 Z.ai Coding Plan (optional):")
            coding_plan = input("Enter Z.ai Coding Plan ID (or press Enter to skip): ").strip()
            if coding_plan:
                self.api_keys.zai_coding_plan = coding_plan
                print("✅ Z.ai Coding Plan saved")

        self._save_config()
        print("\n🎉 API configuration saved!")

    def display_modes_by_category(self):
        """Display startup modes organized by category"""
        categories = {}
        for mode in self.startup_modes:
            if mode.category not in categories:
                categories[mode.category] = []
            categories[mode.category].append(mode)

        print("\n" + "="*80)
        print("🚀 DUCKBOT AI-POWERED STARTUP INTERFACE")
        print("="*80)

        for i, (category, modes) in enumerate(categories.items(), 1):
            print(f"\n📂 {category.upper()}")
            print("-" * 40)

            for j, mode in enumerate(modes, 1):
                # Check API requirements
                requirements = self.check_api_requirements(mode)
                missing_apis = [api for api, available in requirements.items() if not available]

                # Status indicator
                if missing_apis:
                    status = "🔒"
                    status_text = f"(Missing: {', '.join(missing_apis)})"
                elif mode.ai_powered:
                    status = "🤖"
                    status_text = "(AI-Powered)"
                else:
                    status = "⚡"
                    status_text = "(Ready)"

                # Port info
                port_info = f" - Port {mode.port}" if mode.port else ""

                print(f"  {status} {mode.id.replace('_', ' ').title()}{port_info}")
                print(f"     {mode.description}")
                if status_text:
                    print(f"     {status_text}")
                print()

    def get_mode_by_id(self, mode_id: str) -> Optional[StartupMode]:
        """Get startup mode by ID"""
        for mode in self.startup_modes:
            if mode.id == mode_id:
                return mode
        return None

    def launch_mode(self, mode_id: str):
        """Launch a specific startup mode"""
        mode = self.get_mode_by_id(mode_id)
        if not mode:
            print(f"❌ Unknown mode: {mode_id}")
            return

        # Check API requirements
        requirements = self.check_api_requirements(mode)
        missing_apis = [api for api, available in requirements.items() if not available]

        if missing_apis:
            print(f"❌ Missing required API keys: {', '.join(missing_apis)}")
            print("Please setup API keys first (option 'setup')")
            return

        print(f"\n🚀 Launching {mode.name}...")
        print(f"📝 {mode.description}")

        # Create environment with API keys
        env = os.environ.copy()
        if self.api_keys.gemini_api_key:
            env["GEMINI_API_KEY"] = self.api_keys.gemini_api_key
        if self.api_keys.openrouter_api_key:
            env["OPENROUTER_API_KEY"] = self.api_keys.openrouter_api_key
        if self.api_keys.zai_api_key:
            env["ZAI_API_KEY"] = self.api_keys.zai_api_key
        if self.api_keys.zai_coding_plan:
            env["ZAI_CODING_PLAN"] = self.api_keys.zai_coding_plan

        # Launch the mode
        try:
            # For now, use the existing batch script with mode selection
            # This will be enhanced with direct Python launching
            import subprocess
            subprocess.run(["launcher\\CONSOLIDATED_DUCKBOT_LAUNCHER.bat"], env=env, shell=True)
        except Exception as e:
            print(f"❌ Error launching mode: {e}")

    def show_ai_recommendations(self):
        """Show AI-powered startup recommendations"""
        print("\n🤖 AI-POWERED RECOMMENDATIONS")
        print("="*40)

        # Analyze available API keys
        available_apis = []
        if self.api_keys.gemini_api_key:
            available_apis.append("Gemini")
        if self.api_keys.openrouter_api_key:
            available_apis.append("OpenRouter")
        if self.api_keys.zai_api_key:
            available_apis.append("Z.ai")

        if not available_apis:
            print("🔒 No API keys configured")
            print("💡 Recommendation: Setup API keys for AI-powered features")
            return

        print(f"✅ Available APIs: {', '.join(available_apis)}")

        # Recommendations based on available APIs
        recommendations = []

        if "gemini" in available_apis and "openrouter" in available_apis:
            recommendations.append(("🌟 Ultimate Complete AI System", "ultimate_complete"))

        if "gemini" in available_apis:
            recommendations.append(("🤖 ByteBot Desktop Automation", "bytebot"))
            recommendations.append(("🎯 UI-TARS GUI Automation", "ui_tars"))

        if "openrouter" in available_apis:
            recommendations.append(("🧠 Archon Multi-Agent System", "archon"))

        if "zai" in available_apis:
            recommendations.append(("⚡ N8N Workflow Automation", "n8n_agent"))

        if recommendations:
            print("\n🎯 Recommended modes:")
            for name, mode_id in recommendations:
                print(f"  • {name} (ID: {mode_id})")
        else:
            print("💡 Consider setting up more API keys for additional features")

    def show_system_status(self):
        """Show system status and information"""
        print("\n📊 SYSTEM STATUS")
        print("="*40)

        # API Keys Status
        print("🔑 API Keys:")
        print(f"  Gemini: {'✅' if self.api_keys.gemini_api_key else '❌'}")
        print(f"  OpenRouter: {'✅' if self.api_keys.openrouter_api_key else '❌'}")
        print(f"  Z.ai: {'✅' if self.api_keys.zai_api_key else '❌'}")

        # System Info
        print("\n💻 System:")
        print(f"  Python: {sys.version.split()[0]}")
        print(f"  Charm Tools: {'✅' if CHARM_AVAILABLE else '❌'}")

        # Configuration
        print(f"\n⚙️  Config: {self.config_file}")
        print(f"  Modes Available: {len(self.startup_modes)}")

    async def start_interactive_mode(self):
        """Start interactive mode"""
        print("🤖 DuckBot AI-Powered Startup Interface")
        print("Type 'help' for commands or 'quit' to exit")

        while True:
            try:
                command = input("\n🚀 duckbot-start> ").strip().lower()

                if command in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                elif command == 'help':
                    self.show_help()
                elif command == 'setup':
                    self.setup_api_keys()
                elif command == 'list':
                    self.display_modes_by_category()
                elif command == 'recommend':
                    self.show_ai_recommendations()
                elif command == 'status':
                    self.show_system_status()
                elif command.startswith('launch '):
                    mode_id = command[7:].strip()
                    self.launch_mode(mode_id)
                elif command in ['clear', 'cls']:
                    os.system('cls' if os.name == 'nt' else 'clear')
                else:
                    print(f"❌ Unknown command: {command}")
                    print("Type 'help' for available commands")

            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")

    def show_help(self):
        """Show help information"""
        print("\n📚 AVAILABLE COMMANDS")
        print("="*40)
        print("help          - Show this help message")
        print("setup         - Setup API keys")
        print("list          - List all startup modes")
        print("recommend     - Show AI recommendations")
        print("status        - Show system status")
        print("launch <id>   - Launch specific mode")
        print("clear/cls     - Clear screen")
        print("quit/exit/q   - Exit")

async def main():
    """Main entry point"""
    interface = AIStartupInterface()
    await interface.start_interactive_mode()

if __name__ == "__main__":
    asyncio.run(main())