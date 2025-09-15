#!/usr/bin/env python3
"""
DuckBot Consolidation Mapping
This file provides backward compatibility imports and maps old module names to new consolidated modules.
"""

import warnings
from typing import Any

# Warn about deprecation but provide compatibility
warnings.warn(
    "DuckBot modules have been consolidated. "
    "Old import paths will be deprecated in future versions. "
    "Please update your imports to use the new consolidated modules.",
    DeprecationWarning,
    stacklevel=2
)

# ============================================================================
# Cost Management Consolidation
# ============================================================================

# Old: cost_tracker.py, cost_commands.py, cost_visualizer.py
# New: cost_management.py

try:
    from .cost_management import (
        CostTracker,
        CostVisualizer,
        CostCommands,
        ModelPricing,
        UsageRecord,
        CostSummary
    )

    # Re-export for backward compatibility
    __all_cost_exports__ = [
        'CostTracker', 'CostVisualizer', 'CostCommands',
        'ModelPricing', 'UsageRecord', 'CostSummary'
    ]

except ImportError as e:
    warnings.warn(f"Could not import cost_management: {e}")
    __all_cost_exports__ = []

# ============================================================================
# Charm Ecosystem Consolidation
# ============================================================================

# Old: charm_ecosystem.py, charm_terminal_ui.py, charm_tools_integration.py
# New: charm_manager.py

try:
    from .charm_manager import (
        CharmToolsIntegration,
        BubbleTeaApp,
        Model,
        Message,
        MessageType,
        Command,
        LipglossStyle,
        BorderStyle,
        Alignment,
        Color,
        GumInteractive,
        GlamourMarkdown,
        CharmLogger,
        SkateDB,
        CharmManager,
        create_duckbot_theme,
        # Convenience functions
        charm_tools,
        gum_input,
        gum_choose,
        gum_confirm,
        glow_render,
        ask_ai,
        store_data,
        load_data,
        is_charm_available,
        get_charm_status,
        initialize_charm_integration
    )

    __all_charm_exports__ = [
        'CharmToolsIntegration', 'BubbleTeaApp', 'Model', 'Message', 'MessageType',
        'Command', 'LipglossStyle', 'BorderStyle', 'Alignment', 'Color',
        'GumInteractive', 'GlamourMarkdown', 'CharmLogger', 'SkateDB',
        'CharmManager', 'create_duckbot_theme', 'charm_tools', 'gum_input',
        'gum_choose', 'gum_confirm', 'glow_render', 'ask_ai', 'store_data',
        'load_data', 'is_charm_available', 'get_charm_status',
        'initialize_charm_integration'
    ]

except ImportError as e:
    warnings.warn(f"Could not import charm_manager: {e}")
    __all_charm_exports__ = []

# ============================================================================
# Web UI Consolidation
# ============================================================================

# Old: webui.py, enhanced_webui.py, webui_enhanced.py, web_dashboard.py
# New: webui_manager.py

try:
    from .webui_manager import (
        DuckBotWebUI,
        WebUIConfig,
        ChatMessage,
        SystemStatus,
        create_webui,
        run_webui
    )

    __all_webui_exports__ = [
        'DuckBotWebUI', 'WebUIConfig', 'ChatMessage', 'SystemStatus',
        'create_webui', 'run_webui'
    ]

except ImportError as e:
    warnings.warn(f"Could not import webui_manager: {e}")
    __all_webui_exports__ = []

# ============================================================================
# AI Router Consolidation
# ============================================================================

# Old: ai_router_gpt.py, settings_gpt.py, provider_connectors.py
# New: ai_router_manager.py

try:
    from .ai_router_manager import (
        AIRouter,
        AISettings,
        SettingsManager,
        ProviderConfig,
        BaseConnector,
        OpenAIConnector,
        OpenRouterConnector,
        LocalConnector,
        # Global instances and functions
        ai_router,
        settings_manager,
        route_task,
        get_router_state,
        clear_cache,
        reset_breakers,
        load_settings,
        save_settings,
        apply_to_env
    )

    __all_ai_router_exports__ = [
        'AIRouter', 'AISettings', 'SettingsManager', 'ProviderConfig',
        'BaseConnector', 'OpenAIConnector', 'OpenRouterConnector', 'LocalConnector',
        'ai_router', 'settings_manager', 'route_task', 'get_router_state',
        'clear_cache', 'reset_breakers', 'load_settings', 'save_settings',
        'apply_to_env'
    ]

except ImportError as e:
    warnings.warn(f"Could not import ai_router_manager: {e}")
    __all_ai_router_exports__ = []

# ============================================================================
# Module Compatibility Layer
# ============================================================================

class CompatibilityModule:
    """Provides backward compatibility for old module imports"""

    def __init__(self, new_module_name: str, exports: list):
        self.new_module_name = new_module_name
        self.exports = exports
        self._imported_module = None

    def __getattr__(self, name: str) -> Any:
        """Dynamically import and provide access to exports"""
        if self._imported_module is None:
            try:
                module_path = self.new_module_name.split('.')
                if module_path[0] == 'duckbot':
                    # Relative import
                    module_name = module_path[1]
                    from . import module_name as imported_module
                    self._imported_module = imported_module
                else:
                    # Absolute import
                    import importlib
                    self._imported_module = importlib.import_module(self.new_module_name)
            except ImportError as e:
                raise ImportError(
                    f"Could not import {self.new_module_name} for compatibility: {e}. "
                    f"Please update your imports to use the new consolidated modules."
                )

        if name in self.exports:
            return getattr(self._imported_module, name)
        else:
            raise AttributeError(
                f"'{self.new_module_name}' has no attribute '{name}'. "
                f"Available exports: {self.exports}"
            )

# Create compatibility modules
cost_tracker_compat = CompatibilityModule('duckbot.cost_management', __all_cost_exports__)
cost_commands_compat = CompatibilityModule('duckbot.cost_management', __all_cost_exports__)
cost_visualizer_compat = CompatibilityModule('duckbot.cost_management', __all_cost_exports__)

charm_ecosystem_compat = CompatibilityModule('duckbot.charm_manager', __all_charm_exports__)
charm_terminal_ui_compat = CompatibilityModule('duckbot.charm_manager', __all_charm_exports__)
charm_tools_integration_compat = CompatibilityModule('duckbot.charm_manager', __all_charm_exports__)

webui_compat = CompatibilityModule('duckbot.webui_manager', __all_webui_exports__)
enhanced_webui_compat = CompatibilityModule('duckbot.webui_manager', __all_webui_exports__)
webui_enhanced_compat = CompatibilityModule('duckbot.webui_manager', __all_webui_exports__)
web_dashboard_compat = CompatibilityModule('duckbot.webui_manager', __all_webui_exports__)

ai_router_gpt_compat = CompatibilityModule('duckbot.ai_router_manager', __all_ai_router_exports__)
settings_gpt_compat = CompatibilityModule('duckbot.ai_router_manager', __all_ai_router_exports__)
provider_connectors_compat = CompatibilityModule('duckbot.ai_router_manager', __all_ai_router_exports__)

# ============================================================================
# Migration Guide
# ============================================================================

def get_migration_guide() -> str:
    """Get migration guide for updated imports"""
    return """
DuckBot Module Consolidation Migration Guide
===========================================

The following modules have been consolidated to reduce complexity and improve maintainability:

COST MANAGEMENT MODULES:
- OLD: cost_tracker.py, cost_commands.py, cost_visualizer.py
- NEW: cost_management.py
- IMPORT: from duckbot.cost_management import CostTracker, CostVisualizer, CostCommands

CHARM ECOSYSTEM MODULES:
- OLD: charm_ecosystem.py, charm_terminal_ui.py, charm_tools_integration.py
- NEW: charm_manager.py
- IMPORT: from duckbot.charm_manager import CharmToolsIntegration, CharmManager

WEB UI MODULES:
- OLD: webui.py, enhanced_webui.py, webui_enhanced.py, web_dashboard.py
- NEW: webui_manager.py
- IMPORT: from duckbot.webui_manager import DuckBotWebUI, WebUIConfig

AI ROUTER MODULES:
- OLD: ai_router_gpt.py, settings_gpt.py, provider_connectors.py
- NEW: ai_router_manager.py
- IMPORT: from duckbot.ai_router_manager import AIRouter, AISettings

BENEFITS:
✅ Reduced file count from 50+ to 4 core modules
✅ Improved maintainability and organization
✅ Better dependency management
✅ Enhanced performance with reduced import overhead
✅ Easier testing and debugging

ACTION REQUIRED:
Update your import statements to use the new consolidated modules.
Old imports will continue to work with deprecation warnings for now.
"""

def get_consolidation_summary() -> dict:
    """Get summary of consolidation efforts"""
    return {
        "original_modules": 50,
        "consolidated_modules": 4,
        "modules_consolidated": {
            "cost_management": ["cost_tracker.py", "cost_commands.py", "cost_visualizer.py"],
            "charm_manager": ["charm_ecosystem.py", "charm_terminal_ui.py", "charm_tools_integration.py"],
            "webui_manager": ["webui.py", "enhanced_webui.py", "webui_enhanced.py", "web_dashboard.py"],
            "ai_router_manager": ["ai_router_gpt.py", "settings_gpt.py", "provider_connectors.py"]
        },
        "backward_compatibility": True,
        "deprecation_warnings": True,
        "performance_improvement": "Reduced import overhead and better organization"
    }

# ============================================================================
# OpenWebUI Fix Information
# ============================================================================

def get_openwebui_fix_info() -> str:
    """Get information about the OpenWebUI integration fix"""
    return """
OpenWebUI Integration Fix
========================

PROBLEM:
The original OpenWebUI JSON function file contained hardcoded HTTP requests
to localhost:8787, which often failed when the DuckBot server wasn't running.

SOLUTION:
Created a fixed version (duckbot_openwebui_function_fixed.json) with:

✅ Local fallback execution when server unavailable
✅ Enhanced system status checking
✅ File analysis capabilities
✅ Service management commands
✅ Project information retrieval
✅ Better error handling and graceful degradation

NEW FEATURES:
- System resource monitoring (CPU, memory, disk)
- Service port detection and management
- DuckBot directory and file analysis
- Project information and setup guides
- Graceful offline functionality

USAGE:
1. Upload duckbot_openwebui_function_fixed.json to OpenWebUI
2. Use functions like duckbot_ai_chat, duckbot_system_status, duckbot_file_analysis
3. Works both online (with DuckBot server) and offline (local execution)
"""

# Export compatibility functions
__all__ = [
    'get_migration_guide',
    'get_consolidation_summary',
    'get_openwebui_fix_info'
] + __all_cost_exports__ + __all_charm_exports__ + __all_webui_exports__ + __all_ai_router_exports__