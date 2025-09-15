#!/usr/bin/env python3
"""
DuckBot AI Terminal - Enhanced terminal with complete Charm integration
"""

import asyncio
import sys
import os
import subprocess
from pathlib import Path

# Add DuckBot path
sys.path.append('/usr/share/duckbot-de')

from duckbot.charm_tools_integration import (
    gum_input, gum_choose, gum_confirm, glow_render,
    ask_ai, store_data, load_data, get_charm_status
)
from duckbot.integration_manager import integration_manager

class DuckBotTerminal:
    """AI-enhanced terminal with Charm ecosystem integration"""
    
    def __init__(self):
        self.running = True
        self.history = []
        self.ai_mode = False
        
    async def initialize(self):
        """Initialize AI and Charm integrations"""
        print("[EMOJI] Initializing DuckBot AI Terminal...")
        
        # Initialize integration manager
        await integration_manager.initialize_all()
        
        # Check Charm tools status
        charm_status = get_charm_status()
        if charm_status['total_tools'] > 0:
            print(f"[OK] Charm ecosystem ready: {charm_status['total_tools']} tools available")
        else:
            print("[WARN]  Charm tools not available, running in basic mode")
        
        print("[LAUNCH] DuckBot Terminal ready! Type 'help' for AI commands")
        
    async def run(self):
        """Main terminal loop"""
        await self.initialize()
        
        while self.running:
            try:
                # Get user input with beautiful prompt
                command = await gum_input(
                    prompt="[EMOJI] DuckBot Terminal [EMOJI] ",
                    placeholder="Enter command or 'ai: your question'"
                )
                
                if not command:
                    continue
                    
                # Add to history
                self.history.append(command)
                
                # Process command
                await self._process_command(command)
                
            except KeyboardInterrupt:
                confirm_exit = await gum_confirm("Really exit DuckBot Terminal?")
                if confirm_exit:
                    self.running = False
            except Exception as e:
                print(f"[FAIL] Error: {e}")
    
    async def _process_command(self, command: str):
        """Process terminal commands"""
        command = command.strip()
        
        if command.startswith('ai:'):
            # AI command processing
            await self._handle_ai_command(command[3:].strip())
        elif command in ['exit', 'quit', 'q']:
            self.running = False
        elif command == 'help':
            await self._show_help()
        elif command == 'status':
            await self._show_status()
        elif command.startswith('workspace'):
            await self._handle_workspace_command(command)
        elif command.startswith('memory'):
            await self._handle_memory_command(command)
        elif command.startswith('charm'):
            await self._handle_charm_command(command)
        else:
            # Regular shell command
            await self._execute_shell_command(command)
    
    async def _handle_ai_command(self, query: str):
        """Handle AI queries"""
        print(f"[AI] Processing AI query: {query}")
        
        try:
            # Use DuckBot AI integration
            result = await integration_manager.execute_enhanced_task(
                query, {"context": "terminal_session", "history": self.history[-5:]}
            )
            
            if result.get("success"):
                response = result["result"]
                if isinstance(response, dict):
                    response = response.get("message", str(response))
                
                # Display response with beautiful formatting
                await glow_render(markdown_content=f"## AI Response\n\n{response}")
            else:
                print("[FAIL] AI query failed")
                
        except Exception as e:
            print(f"[FAIL] AI Error: {e}")
    
    async def _show_help(self):
        """Show help with beautiful formatting"""
        help_text = """
# [EMOJI] DuckBot AI Terminal Help

## AI Commands
- `ai: your question` - Ask the AI anything
- `workspace create <type>` - Create AI-optimized workspace
- `memory search <query>` - Search AI memory
- `charm status` - Show Charm tools status

## Charm Integration
- `gum-demo` - Interactive Gum component demo
- `glow <file.md>` - Render markdown with Glow
- `freeze <file>` - Create code screenshot
- `vhs-demo` - Create terminal recording

## System Commands
- `status` - Show system and AI status
- `help` - Show this help
- `exit` - Exit terminal

## Regular Commands
All standard shell commands work normally with AI enhancements.
        """
        
        await glow_render(markdown_content=help_text)
    
    async def _show_status(self):
        """Show comprehensive system status"""
        status_md = "# [EMOJI] DuckBot Terminal Status\n\n"
        
        # Integration status
        integration_status = await integration_manager.get_integration_status()
        status_md += "## Integration Status\n\n"
        
        for name, status in integration_status.items():
            icon = "[OK]" if status["initialized"] else "[FAIL]"
            status_md += f"- {icon} **{name.title()}**: {'Ready' if status['initialized'] else 'Not Available'}\n"
        
        # Charm tools status
        charm_status = get_charm_status()
        status_md += f"\n## Charm Ecosystem\n\n"
        status_md += f"- **Available Tools**: {charm_status['total_tools']}\n"
        status_md += f"- **Tools**: {', '.join(charm_status['available_tools'])}\n"
        
        # Memory status
        if integration_manager.is_integration_available("memento"):
            memento_stats = await integration_manager.get_memento_stats()
            if memento_stats.get("available"):
                status_md += f"\n## Memory System\n\n"
                status_md += f"- **Status**: Active\n"
                status_md += f"- **Cases Stored**: {memento_stats.get('total_cases', 'Unknown')}\n"
        
        await glow_render(markdown_content=status_md)
    
    async def _handle_workspace_command(self, command: str):
        """Handle workspace management commands"""
        parts = command.split()
        
        if len(parts) >= 3 and parts[1] == "create":
            workspace_type = parts[2]
            
            # Use integration manager to create workspace
            if integration_manager.is_integration_available("bytebot"):
                result = await integration_manager.execute_integrated_task(
                    "desktop", f"Create {workspace_type} workspace", 
                    {"workspace_type": workspace_type}
                )
                
                if result.get("success"):
                    print(f"[OK] Created {workspace_type} workspace")
                else:
                    print(f"[FAIL] Failed to create workspace: {result.get('result', {}).get('message', 'Unknown error')}")
            else:
                print("[FAIL] Desktop automation not available")
        else:
            print("Usage: workspace create <type>")
            print("Types: development, research, creative, communication")
    
    async def _handle_memory_command(self, command: str):
        """Handle memory system commands"""
        parts = command.split(maxsplit=2)
        
        if len(parts) >= 3 and parts[1] == "search":
            query = parts[2]
            
            if integration_manager.is_integration_available("memento"):
                result = await integration_manager.execute_integrated_task(
                    "memory", f"Search memory for: {query}"
                )
                
                if result.get("success"):
                    memories = result.get("result", {})
                    if memories:
                        md_content = f"# Memory Search Results\n\nQuery: **{query}**\n\n"
                        for memory in memories.get("results", []):
                            md_content += f"- {memory}\n"
                        await glow_render(markdown_content=md_content)
                    else:
                        print("No memories found for that query")
                else:
                    print("[FAIL] Memory search failed")
            else:
                print("[FAIL] Memory system not available")
        else:
            print("Usage: memory search <query>")
    
    async def _handle_charm_command(self, command: str):
        """Handle Charm-specific commands"""
        parts = command.split()
        
        if len(parts) >= 2:
            if parts[1] == "status":
                status = get_charm_status()
                md_content = f"""
# Charm Ecosystem Status

## Available Tools ({status['total_tools']})
{chr(10).join([f'- **{tool}**' for tool in status['available_tools']])}

## Configuration
- **Go Bin Path**: {status['config']['go_bin_path']}
- **Timeout**: {status['config']['timeout']}s
                """
                await glow_render(markdown_content=md_content)
                
            elif parts[1] == "demo":
                await self._run_charm_demo()
        else:
            print("Usage: charm <status|demo>")
    
    async def _run_charm_demo(self):
        """Run interactive Charm tools demo"""
        print("[ART] Charm Tools Interactive Demo")
        
        tools = await gum_choose([
            "Gum Input Demo",
            "Gum Choose Demo", 
            "Gum Confirm Demo",
            "Glow Markdown Demo",
            "All Demos"
        ], "Select a demo:")
        
        if not tools:
            return
        
        if tools == "Gum Input Demo" or tools == "All Demos":
            name = await gum_input(
                prompt="What's your name? ",
                placeholder="Enter your name"
            )
            if name:
                print(f"Hello, {name}! [EMOJI]")
        
        if tools == "Gum Choose Demo" or tools == "All Demos":
            color = await gum_choose([
                "Red", "Green", "Blue", "Yellow", "Purple"
            ], "Choose your favorite color:")
            
            if color:
                print(f"Great choice! {color} is awesome! [ART]")
        
        if tools == "Gum Confirm Demo" or tools == "All Demos":
            likes_ai = await gum_confirm("Do you like AI assistants?")
            if likes_ai:
                print("Fantastic! DuckBot is here to help! [AI]")
            else:
                print("That's okay, maybe DuckBot can change your mind! [EMOJI]")
        
        if tools == "Glow Markdown Demo" or tools == "All Demos":
            demo_md = """
# Welcome to Charm Glow! [EMOJI]

This is a **beautiful** markdown rendering demo.

## Features
- Beautiful typography
- Syntax highlighting
- Code blocks
- Lists and tables

```python
def hello_world():
    print("Hello from DuckBot! [EMOJI]")
```

> The future of terminal interfaces is here!
            """
            await glow_render(markdown_content=demo_md)
    
    async def _execute_shell_command(self, command: str):
        """Execute regular shell commands with AI enhancement"""
        try:
            # Run the command
            process = subprocess.run(
                command, shell=True, capture_output=True, text=True
            )
            
            # Display output
            if process.stdout:
                print(process.stdout)
            
            if process.stderr:
                print(f"[FAIL] Error: {process.stderr}")
            
            # If command failed, offer AI assistance
            if process.returncode != 0:
                help_wanted = await gum_confirm(
                    f"Command failed (exit code {process.returncode}). "
                    "Want AI help to fix it?"
                )
                
                if help_wanted:
                    await self._handle_ai_command(
                        f"The command '{command}' failed with exit code {process.returncode} "
                        f"and error: {process.stderr}. How can I fix this?"
                    )
                    
        except Exception as e:
            print(f"[FAIL] Command execution error: {e}")

async def main():
    """Main entry point"""
    terminal = DuckBotTerminal()
    await terminal.run()

if __name__ == "__main__":
    asyncio.run(main())