#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate Electron configuration from centralized configuration system
"""

import os
import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def generate_electron_config():
    """Generate Electron configuration from centralized system"""
    try:
        from config.config_bridge import get_config_bridge

        print("Generating Electron configuration from centralized system...")

        # Initialize configuration bridge
        bridge = get_config_bridge()

        # Export configuration for Electron
        config_data = bridge.export_for_electron()

        # Save to file
        config_path = project_root / "config" / "electron_config.json"
        config_path.parent.mkdir(exist_ok=True)

        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)

        print(f"Electron configuration saved to: {config_path}")

        # Print summary
        electron_config = config_data['electron_config']
        startup_modes = electron_config['startup_modes']
        system_info = config_data['system_info']

        print(f"\nConfiguration Summary:")
        print(f"   System: {system_info['name']} v{system_info['version']}")
        print(f"   Environment: {system_info['environment']}")
        print(f"   Debug Mode: {electron_config['debug_mode']}")
        print(f"   MCP Port: {electron_config['mcp_port']}")
        print(f"   WebUI Port: {electron_config['webui_port']}")
        print(f"   AI Router Port: {electron_config['ai_router_port']}")
        print(f"   Startup Modes: {len(startup_modes)}")

        enabled_modes = [mode for mode, config in startup_modes.items() if config.get('enabled', True)]
        print(f"   Enabled Modes: {len(enabled_modes)}")

        if enabled_modes:
            print(f"\nAvailable Startup Modes:")
            for mode_id, mode_config in startup_modes.items():
                if mode_config.get('enabled', True):
                    icon = mode_config.get('icon', '•')
                    print(f"   * {icon} {mode_config['name']}")
                    print(f"     Ports: {mode_config.get('ports', [])}")

        api_keys = config_data['api_keys_status']
        configured_keys = sum(api_keys.values())
        print(f"\nAPI Keys: {configured_keys}/{len(api_keys)} configured")

        return True

    except Exception as e:
        print(f"Error generating Electron configuration: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_fallback_config():
    """Create a fallback configuration if the main system fails"""
    print("Creating fallback configuration...")

    fallback_config = {
        "electron_config": {
            "debug_mode": False,
            "log_level": "INFO",
            "mcp_host": "127.0.0.1",
            "mcp_port": 8789,
            "webui_port": 8787,
            "ai_router_port": 8790,
            "enable_ai_assistant": True,
            "enable_notifications": True,
            "enable_auto_reconnect": True,
            "enable_auto_start_mcp": True,
            "theme": "dark",
            "font_size": 14,
            "chat_position": "right",
            "show_system_info": True,
            "compact_mode": False,
            "max_concurrent_services": 5,
            "service_timeout": 30,
            "health_check_interval": 30,
            "startup_modes": {
                "ultimate": {
                    "name": "Ultimate Complete Mode",
                    "description": "Complete AI integration with all features",
                    "icon": "🚀",
                    "category": "complete",
                    "requires": ["gemini", "openrouter"],
                    "command": "python start_ecosystem.py",
                    "ports": [8787, 8788, 8789],
                    "enabled": True
                },
                "enhanced-webui": {
                    "name": "Enhanced WebUI",
                    "description": "Modern web interface with AI features",
                    "icon": "🌐",
                    "category": "web",
                    "requires": ["openrouter"],
                    "command": "python duckbot/enhanced_webui.py --port 8787",
                    "ports": [8787],
                    "enabled": True
                },
                "monitoring": {
                    "name": "System Monitoring",
                    "description": "Real-time system metrics and performance",
                    "icon": "📊",
                    "category": "monitoring",
                    "requires": [],
                    "command": "python ai_ecosystem_manager.py --port 8789",
                    "ports": [8789],
                    "enabled": True
                },
                "local-only": {
                    "name": "Local-Only Privacy Mode",
                    "description": "Complete offline operation with LM Studio",
                    "icon": "🔒",
                    "category": "privacy",
                    "requires": [],
                    "command": "python start_local_ecosystem.py",
                    "ports": [8787],
                    "enabled": True
                },
                "bytebot": {
                    "name": "ByteBot Desktop Automation",
                    "description": "Complete computer control with AI",
                    "icon": "🤖",
                    "category": "automation",
                    "requires": ["gemini"],
                    "command": "python -c \"from duckbot.bytebot_integration import ByteBotIntegration; import asyncio; asyncio.run(ByteBotIntegration().start_interactive_mode())\"",
                    "ports": [],
                    "enabled": True
                }
            }
        },
        "api_keys_status": {
            "gemini": False,
            "openrouter": False,
            "zai": False,
            "zai_coding_plan": False
        },
        "services_status": {},
        "feature_flags": {
            "webui_enabled": True,
            "monitoring_enabled": True,
            "ai_routing_enabled": True,
            "local_ai_enabled": True,
            "cloud_ai_enabled": True,
            "desktop_automation_enabled": True,
            "voice_enabled": True,
            "local_only_mode": False,
            "debug_mode": False
        },
        "system_info": {
            "name": "DuckBot Enhanced",
            "version": "4.2",
            "build_date": "2025-09-16",
            "environment": "development",
            "debug_mode": False,
            "log_level": "INFO",
            "min_ram_gb": 4,
            "recommended_ram_gb": 8,
            "gpu_enabled": True,
            "max_concurrent_services": 10
        },
        "config_path": "config/duckbot_config.yaml"
    }

    # Save fallback configuration
    config_path = project_root / "config" / "electron_config.json"
    config_path.parent.mkdir(exist_ok=True)

    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(fallback_config, f, indent=2, ensure_ascii=False)

    print(f"✅ Fallback configuration saved to: {config_path}")
    return True

def test_configuration():
    """Test the generated configuration"""
    config_path = project_root / "config" / "electron_config.json"

    if not config_path.exists():
        print("❌ Configuration file not found")
        return False

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)

        # Basic validation
        required_keys = ['electron_config', 'api_keys_status', 'system_info']
        for key in required_keys:
            if key not in config_data:
                print(f"❌ Missing required key: {key}")
                return False

        electron_config = config_data['electron_config']
        startup_modes = electron_config.get('startup_modes', {})

        print(f"✅ Configuration file is valid")
        print(f"   Contains {len(startup_modes)} startup modes")
        print(f"   System: {config_data['system_info']['name']} v{config_data['system_info']['version']}")

        return True

    except Exception as e:
        print(f"❌ Error testing configuration: {e}")
        return False

def main():
    """Main function"""
    print("DuckBot Electron Configuration Generator")
    print("=" * 50)

    # Try to generate configuration from centralized system
    success = generate_electron_config()

    if not success:
        print("⚠️  Centralized configuration failed, creating fallback...")
        success = create_fallback_config()

    if success:
        # Test the configuration
        test_success = test_configuration()
        if test_success:
            print("\n✅ Configuration generation completed successfully!")
            print("\n📝 Next Steps:")
            print("   1. Replace electron-launcher/main.js with main_configured.js")
            print("   2. Test the Electron launcher")
            print("   3. Verify startup modes are working")
        else:
            print("\n❌ Configuration test failed")
    else:
        print("\n❌ Failed to generate configuration")

if __name__ == "__main__":
    main()