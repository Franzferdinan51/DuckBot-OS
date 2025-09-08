#!/usr/bin/env python3
"""
Charm-inspired Terminal UI Components for DuckBot
Beautiful, interactive terminal interfaces with multi-model AI support
Based on the Charm ecosystem (Bubbletea, Lipgloss, etc.)
"""

import os
import sys
import asyncio
import logging
import json
import time
import threading
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
import subprocess
import shlex

logger = logging.getLogger(__name__)

# Terminal color codes and styling
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    ITALIC = '\033[3m'
    UNDERLINE = '\033[4m'
    
    # Colors
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    
    # Bright colors
    BRIGHT_BLACK = '\033[90m'
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'
    
    # Background colors
    BG_BLACK = '\033[40m'
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'
    BG_MAGENTA = '\033[45m'
    BG_CYAN = '\033[46m'
    BG_WHITE = '\033[47m'

@dataclass
class UITheme:
    """Terminal UI theme configuration"""
    primary: str = Colors.BRIGHT_CYAN
    secondary: str = Colors.BRIGHT_BLUE
    accent: str = Colors.BRIGHT_GREEN
    warning: str = Colors.BRIGHT_YELLOW
    error: str = Colors.BRIGHT_RED
    muted: str = Colors.BRIGHT_BLACK
    text: str = Colors.WHITE
    background: str = Colors.RESET

@dataclass
class SessionConfig:
    """AI session configuration"""
    provider: str = "local"
    model: str = "qwen3-coder"
    temperature: float = 0.7
    max_tokens: int = 2048
    context_length: int = 8192
    tools_enabled: bool = True
    logging_enabled: bool = True
    debug_mode: bool = False

@dataclass
class ChatMessage:
    """Chat message structure"""
    role: str  # 'user', 'assistant', 'system'
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    model: Optional[str] = None
    tokens: Optional[int] = None
    cost: Optional[float] = None
    execution_time: Optional[float] = None

class TerminalUI:
    """Charm-inspired terminal interface for DuckBot"""
    
    def __init__(self, theme: Optional[UITheme] = None):
        self.theme = theme or UITheme()
        self.width = self._get_terminal_width()
        self.height = self._get_terminal_height()
        self.session_config = SessionConfig()
        self.chat_history: List[ChatMessage] = []
        self.context_manager = None
        self.active_tools: List[str] = []
        
    def _get_terminal_width(self) -> int:
        """Get terminal width"""
        try:
            return os.get_terminal_size().columns
        except:
            return 80
            
    def _get_terminal_height(self) -> int:
        """Get terminal height"""
        try:
            return os.get_terminal_size().lines
        except:
            return 24
    
    def clear_screen(self):
        """Clear the terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def print_header(self, title: str, subtitle: Optional[str] = None):
        """Print a styled header"""
        border = "═" * (self.width - 2)
        
        print(f"{self.theme.primary}╔{border}╗{self.theme.text}")
        print(f"{self.theme.primary}║{self.theme.accent}{self.theme.bold} {title.center(self.width - 4)} {self.theme.primary}║{self.theme.text}")
        
        if subtitle:
            print(f"{self.theme.primary}║{self.theme.muted} {subtitle.center(self.width - 4)} {self.theme.primary}║{self.theme.text}")
        
        print(f"{self.theme.primary}╚{border}╝{self.theme.text}")
        print()
    
    def print_section(self, title: str, content: List[str]):
        """Print a styled section"""
        print(f"{self.theme.secondary}┌─ {self.theme.bold}{title}{self.theme.secondary} {'─' * (self.width - len(title) - 4)}┐{self.theme.text}")
        
        for line in content:
            print(f"{self.theme.secondary}│{self.theme.text} {line.ljust(self.width - 4)} {self.theme.secondary}│{self.theme.text}")
        
        print(f"{self.theme.secondary}└{'─' * (self.width - 2)}┘{self.theme.text}")
        print()
    
    def print_status_bar(self, left: str, right: str = ""):
        """Print a status bar at the bottom"""
        available_width = self.width - len(left) - len(right) - 2
        padding = " " * max(0, available_width)
        
        print(f"{self.theme.primary}{self.theme.bg_blue} {left}{padding}{right} {self.theme.text}")
    
    def print_spinner(self, message: str):
        """Print a spinner with message"""
        spinner_chars = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
        for char in spinner_chars:
            print(f"\r{self.theme.accent}{char}{self.theme.text} {message}", end="", flush=True)
            time.sleep(0.1)
    
    def print_progress_bar(self, current: int, total: int, message: str = ""):
        """Print a progress bar"""
        percentage = current / total if total > 0 else 0
        filled = int(percentage * 50)
        bar = "█" * filled + "░" * (50 - filled)
        
        print(f"\r{self.theme.accent}[{bar}]{self.theme.text} {percentage:.1%} {message}", end="", flush=True)
    
    def input_styled(self, prompt: str, color: str = None) -> str:
        """Styled input prompt"""
        color = color or self.theme.primary
        return input(f"{color}❯{self.theme.text} {prompt}")
    
    def confirm(self, question: str) -> bool:
        """Styled confirmation prompt"""
        response = self.input_styled(f"{question} {self.theme.muted}(y/N){self.theme.text}").strip().lower()
        return response in ['y', 'yes']
    
    def select_option(self, options: List[str], title: str = "Select an option:") -> int:
        """Interactive option selection"""
        print(f"{self.theme.accent}{title}{self.theme.text}")
        print()
        
        for i, option in enumerate(options):
            print(f"{self.theme.secondary}{i + 1}.{self.theme.text} {option}")
        
        print()
        while True:
            try:
                choice = int(self.input_styled("Enter choice:")) - 1
                if 0 <= choice < len(options):
                    return choice
                else:
                    print(f"{self.theme.error}Invalid choice. Please select 1-{len(options)}.{self.theme.text}")
            except ValueError:
                print(f"{self.theme.error}Please enter a valid number.{self.theme.text}")

class CharmTerminalInterface:
    """Main terminal interface for DuckBot with Charm-inspired design"""
    
    def __init__(self):
        self.ui = TerminalUI()
        self.running = False
        self.ai_router = None
        self.wsl_integration = None
        self.bytebot_integration = None
        self.session_active = False
        
    async def initialize(self):
        """Initialize the terminal interface"""
        try:
            # Import integrations
            from .ai_router_gpt import route_task
            from .wsl_integration import wsl_integration
            from .bytebot_integration import ByteBotIntegration
            
            self.ai_router = route_task
            self.wsl_integration = wsl_integration
            self.bytebot_integration = ByteBotIntegration()
            
            # Initialize WSL if available
            await wsl_integration.initialize()
            
            logger.info("Charm Terminal Interface initialized")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize terminal interface: {e}")
            return False
    
    def display_welcome(self):
        """Display welcome screen"""
        self.ui.clear_screen()
        
        logo = [
            "    ____             __   ____        __     _________",
            "   / __ \\__  _______/ /__/ __ )____  / /_   / ____/ (_)____",
            "  / / / / / / / ___/ //_/ __  / __ \\/ __/  / /   / / / ___/",
            " / /_/ / /_/ / /__/ ,< / /_/ / /_/ / /_   / /___/ / (__  )",
            "/_____/\\__,_/\\___/_/|_/_____/\\____/\\__/   \\____/_/_/____/",
        ]
        
        self.ui.print_header("DuckBot v3.1.0+ Terminal Interface", "Powered by Charm-inspired UI")
        
        for line in logo:
            print(f"{self.ui.theme.accent}{line.center(self.ui.width)}{self.ui.theme.text}")
        
        print()
        
        # System status
        status_info = []
        
        # Check WSL
        if self.wsl_integration and self.wsl_integration.wsl_available:
            distros = list(self.wsl_integration.available_distros.keys())
            status_info.append(f"{self.ui.theme.accent}✓{self.ui.theme.text} WSL Available - Distros: {', '.join(distros)}")
        else:
            status_info.append(f"{self.ui.theme.warning}⚠{self.ui.theme.text} WSL Not Available")
        
        # Check ByteBot capabilities
        if self.bytebot_integration and self.bytebot_integration.available:
            status_info.append(f"{self.ui.theme.accent}✓{self.ui.theme.text} ByteBot Desktop Integration Ready")
        else:
            status_info.append(f"{self.ui.theme.warning}⚠{self.ui.theme.text} ByteBot Integration Limited")
        
        # Check AI providers
        status_info.append(f"{self.ui.theme.accent}✓{self.ui.theme.text} AI Router Active - Multi-model Support")
        
        self.ui.print_section("System Status", status_info)
    
    def display_main_menu(self):
        """Display main menu"""
        options = [
            "🤖 Start AI Chat Session",
            "🖥️  WSL Integration Menu", 
            "🖱️  Desktop Automation (ByteBot)",
            "⚙️  Configuration & Settings",
            "📊 System Monitoring",
            "🔧 Development Tools",
            "📝 Session Management",
            "❌ Exit"
        ]
        
        choice = self.ui.select_option(options, "Main Menu:")
        return choice
    
    async def handle_ai_chat(self):
        """Handle AI chat session"""
        self.ui.clear_screen()
        self.ui.print_header("AI Chat Session", "Multi-model AI interaction")
        
        # Session configuration
        if self.ui.confirm("Configure session settings?"):
            await self.configure_ai_session()
        
        # Start chat loop
        self.session_active = True
        print(f"{self.ui.theme.accent}Chat session started. Type 'exit' to end, 'help' for commands.{self.ui.theme.text}")
        print()
        
        while self.session_active:
            try:
                user_input = self.ui.input_styled("You:")
                
                if user_input.lower() == 'exit':
                    self.session_active = False
                    break
                elif user_input.lower() == 'help':
                    self.display_chat_help()
                    continue
                elif user_input.lower() == 'clear':
                    self.ui.clear_screen()
                    continue
                elif user_input.lower().startswith('model '):
                    model_name = user_input[6:].strip()
                    await self.switch_model(model_name)
                    continue
                
                if not user_input.strip():
                    continue
                
                # Process AI request
                await self.process_ai_request(user_input)
                
            except KeyboardInterrupt:
                print(f"\n{self.ui.theme.warning}Session interrupted.{self.ui.theme.text}")
                self.session_active = False
            except Exception as e:
                print(f"{self.ui.theme.error}Error: {e}{self.ui.theme.text}")
    
    async def process_ai_request(self, user_input: str):
        """Process AI request with routing"""
        start_time = time.time()
        
        # Show spinner
        print(f"{self.ui.theme.muted}Processing...{self.ui.theme.text}", end="", flush=True)
        
        try:
            # Route the task
            result = await self.ai_router(user_input, task_kind="general")
            execution_time = time.time() - start_time
            
            # Clear spinner line
            print(f"\r{' ' * 20}\r", end="")
            
            # Display response
            print(f"{self.ui.theme.secondary}Assistant{self.ui.theme.muted} ({self.ui.session_config.model}, {execution_time:.2f}s):{self.ui.theme.text}")
            print(f"{result.get('response', 'No response')}")
            print()
            
            # Add to history
            message = ChatMessage(
                role="assistant",
                content=result.get('response', ''),
                model=result.get('model_used'),
                execution_time=execution_time
            )
            self.ui.chat_history.append(message)
            
        except Exception as e:
            print(f"\r{self.ui.theme.error}Error processing request: {e}{self.ui.theme.text}")
    
    async def configure_ai_session(self):
        """Configure AI session settings"""
        print(f"{self.ui.theme.accent}Session Configuration:{self.ui.theme.text}")
        print()
        
        # Provider selection
        providers = ["local", "cloud", "hybrid"]
        provider_choice = self.ui.select_option(providers, "Select AI provider mode:")
        self.ui.session_config.provider = providers[provider_choice]
        
        # Model selection based on provider
        if self.ui.session_config.provider == "local":
            models = ["qwen3-coder", "gemma-12b", "nemotron"]
        else:
            models = ["gpt-4o-mini", "claude-3-haiku", "qwen-plus"]
        
        model_choice = self.ui.select_option(models, "Select model:")
        self.ui.session_config.model = models[model_choice]
        
        # Advanced settings
        if self.ui.confirm("Configure advanced settings?"):
            self.ui.session_config.temperature = float(self.ui.input_styled("Temperature (0.0-1.0):") or "0.7")
            self.ui.session_config.max_tokens = int(self.ui.input_styled("Max tokens:") or "2048")
            self.ui.session_config.tools_enabled = self.ui.confirm("Enable tools?")
            self.ui.session_config.debug_mode = self.ui.confirm("Enable debug mode?")
        
        print(f"{self.ui.theme.accent}Configuration saved.{self.ui.theme.text}")
        print()
    
    async def handle_wsl_menu(self):
        """Handle WSL integration menu"""
        if not self.wsl_integration or not self.wsl_integration.wsl_available:
            print(f"{self.ui.theme.error}WSL not available on this system.{self.ui.theme.text}")
            input("Press Enter to continue...")
            return
        
        self.ui.clear_screen()
        self.ui.print_header("WSL Integration", "Windows Subsystem for Linux")
        
        options = [
            "📋 List Distributions",
            "🚀 Start/Stop Distribution", 
            "💻 Execute Command",
            "📦 Install Package",
            "🐳 Docker Management",
            "📊 System Information",
            "📁 File Operations",
            "🌐 Network Information",
            "🔙 Back to Main Menu"
        ]
        
        choice = self.ui.select_option(options, "WSL Menu:")
        
        if choice == 0:  # List distributions
            await self.show_wsl_distributions()
        elif choice == 1:  # Start/Stop distribution
            await self.manage_wsl_distribution()
        elif choice == 2:  # Execute command
            await self.execute_wsl_command()
        elif choice == 3:  # Install package
            await self.install_wsl_package()
        elif choice == 4:  # Docker management
            await self.manage_wsl_docker()
        elif choice == 5:  # System information
            await self.show_wsl_system_info()
        elif choice == 6:  # File operations
            await self.handle_wsl_files()
        elif choice == 7:  # Network information
            await self.show_wsl_network()
        # Choice 8 returns to main menu
    
    def display_chat_help(self):
        """Display chat help information"""
        help_commands = [
            "exit - End chat session",
            "clear - Clear screen",
            "help - Show this help",
            "model <name> - Switch AI model",
            "/tools - Show available tools",
            "/history - Show chat history",
            "/config - Show session config"
        ]
        
        self.ui.print_section("Chat Commands", help_commands)
    
    async def run(self):
        """Main run loop"""
        if not await self.initialize():
            print(f"{self.ui.theme.error}Failed to initialize terminal interface.{self.ui.theme.text}")
            return
        
        self.running = True
        
        while self.running:
            try:
                self.display_welcome()
                choice = self.display_main_menu()
                
                if choice == 0:  # AI Chat
                    await self.handle_ai_chat()
                elif choice == 1:  # WSL Integration
                    await self.handle_wsl_menu()
                elif choice == 2:  # ByteBot Desktop Automation
                    await self.handle_bytebot_menu()
                elif choice == 3:  # Configuration
                    await self.handle_configuration()
                elif choice == 4:  # System Monitoring
                    await self.handle_monitoring()
                elif choice == 5:  # Development Tools
                    await self.handle_dev_tools()
                elif choice == 6:  # Session Management
                    await self.handle_session_management()
                elif choice == 7:  # Exit
                    self.running = False
                    
            except KeyboardInterrupt:
                if self.ui.confirm("\nAre you sure you want to exit?"):
                    self.running = False
            except Exception as e:
                print(f"{self.ui.theme.error}Unexpected error: {e}{self.ui.theme.text}")
                input("Press Enter to continue...")
        
        print(f"{self.ui.theme.accent}Thank you for using DuckBot Terminal Interface!{self.ui.theme.text}")

# Global instance
charm_terminal = CharmTerminalInterface()

async def start_terminal_interface():
    """Start the Charm terminal interface"""
    await charm_terminal.run()

def main():
    """CLI entry point"""
    asyncio.run(start_terminal_interface())

if __name__ == "__main__":
    main()