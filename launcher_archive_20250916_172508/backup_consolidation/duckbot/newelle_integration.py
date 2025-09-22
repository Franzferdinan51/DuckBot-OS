#!/usr/bin/env python3
"""
Newelle-Inspired WSL Integration for DuckBot
Advanced terminal command execution, system control, and WSL environment management
Based on Newelle project features and capabilities
"""

import os
import sys
import json
import asyncio
import logging
import subprocess
import tempfile
import time
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from datetime import datetime
import base64
import requests
from pathlib import Path

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger(__name__)

@dataclass
class NewelleCommand:
    """Represents a terminal command execution"""
    command: str
    working_directory: str
    environment: Dict[str, str]
    output: str
    error: str
    exit_code: int
    execution_time: float
    timestamp: datetime

@dataclass
class NewelleSession:
    """Represents a WSL session"""
    session_id: str
    distribution: str
    working_directory: str
    environment: Dict[str, str]
    active: bool
    created_at: datetime
    last_activity: datetime

class NewelleIntegration:
    """Newelle-inspired WSL integration for DuckBot"""

    def __init__(self, wsl_distribution: str = "Ubuntu"):
        self.wsl_distribution = wsl_distribution
        self.active_sessions = {}
        self.command_history = []
        self.session_history = []
        self.voice_enabled = False
        self.mini_window_mode = False
        self.long_term_memory = {}

        # Initialize extensions
        self.extensions = {
            "file_manager": self._file_manager_extension,
            "web_search": self._web_search_extension,
            "document_chat": self._document_chat_extension,
            "system_info": self._system_info_extension,
            "terminal": self._terminal_extension,
            "process_manager": self._process_manager_extension
        }

    async def initialize(self) -> bool:
        """Initialize Newelle integration"""
        try:
            logger.info("Initializing Newelle-inspired WSL integration...")

            # Check WSL availability
            if not await self._check_wsl_availability():
                logger.warning("WSL not available, some features will be limited")
                return False

            # Initialize active sessions
            await self._initialize_sessions()

            # Load long-term memory
            await self._load_memory()

            logger.info("Newelle integration initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize Newelle integration: {e}")
            return False

    async def _check_wsl_availability(self) -> bool:
        """Check if WSL is available"""
        try:
            result = subprocess.run(
                ["wsl", "--list", "--verbose"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    async def _initialize_sessions(self):
        """Initialize WSL sessions"""
        try:
            result = subprocess.run(
                ["wsl", "--list", "--verbose"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                for line in result.stdout.strip().split('\n')[1:]:  # Skip header
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 2:
                            distro = parts[0]
                            session_id = f"newelle_{distro}_{int(time.time())}"

                            session = NewelleSession(
                                session_id=session_id,
                                distribution=distro,
                                working_directory="/home/user",
                                environment={"TERM": "xterm-256color", "LANG": "en_US.UTF-8"},
                                active=True,
                                created_at=datetime.now(),
                                last_activity=datetime.now()
                            )

                            self.active_sessions[session_id] = session
                            logger.info(f"Initialized WSL session: {distro}")
        except Exception as e:
            logger.error(f"Failed to initialize WSL sessions: {e}")

    async def execute_wsl_command(self, command: str, session_id: Optional[str] = None,
                                 working_directory: Optional[str] = None,
                                 environment: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Execute a command in WSL environment"""
        start_time = time.time()

        try:
            # Use active session or create new one
            if not session_id or session_id not in self.active_sessions:
                session_id = await self._create_session()

            session = self.active_sessions[session_id]

            # Build WSL command
            wsl_cmd = ["wsl", "-d", session.distribution]

            if working_directory:
                wsl_cmd.extend(["--cd", working_directory])
            elif session.working_directory:
                wsl_cmd.extend(["--cd", session.working_directory])

            # Set environment variables
            env = session.environment.copy()
            if environment:
                env.update(environment)

            # Add command execution
            wsl_cmd.extend(["--", "bash", "-c", command])

            # Execute command
            result = subprocess.run(
                wsl_cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                env=env
            )

            # Record command
            command_record = NewelleCommand(
                command=command,
                working_directory=working_directory or session.working_directory,
                environment=env,
                output=result.stdout,
                error=result.stderr,
                exit_code=result.returncode,
                execution_time=time.time() - start_time,
                timestamp=datetime.now()
            )

            self.command_history.append(command_record)

            # Update session activity
            session.last_activity = datetime.now()

            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr,
                "exit_code": result.returncode,
                "execution_time": command_record.execution_time,
                "session_id": session_id,
                "working_directory": working_directory or session.working_directory,
                "command": command
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Command execution timed out (5 minutes)",
                "exit_code": -1,
                "execution_time": time.time() - start_time
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "exit_code": -1,
                "execution_time": time.time() - start_time
            }

    async def _create_session(self) -> str:
        """Create a new WSL session"""
        session_id = f"newelle_{self.wsl_distribution}_{int(time.time())}"

        session = NewelleSession(
            session_id=session_id,
            distribution=self.wsl_distribution,
            working_directory="/home/user",
            environment={"TERM": "xterm-256color", "LANG": "en_US.UTF-8"},
            active=True,
            created_at=datetime.now(),
            last_activity=datetime.now()
        )

        self.active_sessions[session_id] = session
        self.session_history.append(session)

        logger.info(f"Created new WSL session: {session_id}")
        return session_id

    async def get_system_info(self) -> Dict[str, Any]:
        """Get comprehensive system information"""
        try:
            info = {}

            # WSL system info
            wsl_info = await self.execute_wsl_command("uname -a")
            if wsl_info["success"]:
                info["wsl_system"] = wsl_info["output"].strip()

            # Disk usage
            disk_info = await self.execute_wsl_command("df -h")
            if disk_info["success"]:
                info["disk_usage"] = disk_info["output"]

            # Memory usage
            memory_info = await self.execute_wsl_command("free -h")
            if memory_info["success"]:
                info["memory_usage"] = memory_info["output"]

            # Process list
            process_info = await self.execute_wsl_command("ps aux --sort=-%cpu | head -20")
            if process_info["success"]:
                info["top_processes"] = process_info["output"]

            # Network info
            network_info = await self.execute_wsl_command("ip addr show")
            if network_info["success"]:
                info["network_interfaces"] = network_info["output"]

            return {
                "success": True,
                "system_info": info,
                "active_sessions": len(self.active_sessions),
                "command_history_size": len(self.command_history)
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def manage_files(self, action: str, path: str, content: Optional[str] = None) -> Dict[str, Any]:
        """File management operations"""
        try:
            if action == "read":
                result = await self.execute_wsl_command(f"cat '{path}'")
                if result["success"]:
                    result["file_content"] = result["output"]
                    result["file_size"] = len(result["output"])
                return result

            elif action == "write":
                if content is None:
                    return {"success": False, "error": "Content required for write operation"}

                # Create temporary file with content
                with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
                    f.write(content)
                    temp_file = f.name

                try:
                    # Copy to WSL
                    copy_result = await self.execute_wsl_command(f"cp '{temp_file}' '{path}'")
                    return copy_result
                finally:
                    os.unlink(temp_file)

            elif action == "list":
                result = await self.execute_wsl_command(f"ls -la '{path}'")
                if result["success"]:
                    result["directory_contents"] = result["output"]
                return result

            elif action == "delete":
                return await self.execute_wsl_command(f"rm -rf '{path}'")

            elif action == "mkdir":
                return await self.execute_wsl_command(f"mkdir -p '{path}'")

            else:
                return {"success": False, "error": f"Unknown file action: {action}"}

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def search_web(self, query: str, num_results: int = 5) -> Dict[str, Any]:
        """Web search functionality"""
        try:
            # Use curl to search via a search engine API
            search_cmd = f'curl -s "https://api.duckduckgo.com/?q={query}&format=json&pretty=1"'

            result = await self.execute_wsl_command(search_cmd)

            if result["success"]:
                try:
                    search_data = json.loads(result["output"])
                    return {
                        "success": True,
                        "query": query,
                        "results": search_data.get("Results", [])[:num_results],
                        "related_topics": search_data.get("RelatedTopics", [])
                    }
                except json.JSONDecodeError:
                    return {
                        "success": False,
                        "error": "Failed to parse search results"
                    }
            else:
                return result

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def process_text_document(self, file_path: str, query: Optional[str] = None) -> Dict[str, Any]:
        """Process and chat with text documents"""
        try:
            # Read document
            read_result = await self.manage_files("read", file_path)

            if not read_result["success"]:
                return read_result

            content = read_result["file_content"]

            if query:
                # Simple text-based search (in real implementation, would use more sophisticated NLP)
                lines = content.split('\n')
                matching_lines = []

                for i, line in enumerate(lines, 1):
                    if query.lower() in line.lower():
                        matching_lines.append(f"Line {i}: {line}")

                return {
                    "success": True,
                    "query": query,
                    "matching_lines": matching_lines[:10],  # Limit to first 10 matches
                    "total_matches": len(matching_lines),
                    "file_path": file_path
                }
            else:
                # Document summary
                word_count = len(content.split())
                line_count = len(content.split('\n'))
                char_count = len(content)

                return {
                    "success": True,
                    "file_path": file_path,
                    "word_count": word_count,
                    "line_count": line_count,
                    "char_count": char_count,
                    "preview": content[:500] + "..." if len(content) > 500 else content
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def manage_processes(self, action: str, process_id: Optional[str] = None) -> Dict[str, Any]:
        """Process management functionality"""
        try:
            if action == "list":
                result = await self.execute_wsl_command("ps aux")
                if result["success"]:
                    lines = result["output"].split('\n')
                    processes = []

                    for line in lines[1:]:  # Skip header
                        parts = line.split()
                        if len(parts) >= 11:
                            processes.append({
                                "pid": parts[1],
                                "user": parts[0],
                                "cpu": parts[2],
                                "memory": parts[3],
                                "command": " ".join(parts[10:])
                            })

                    return {
                        "success": True,
                        "processes": processes,
                        "total_count": len(processes)
                    }
                return result

            elif action == "kill" and process_id:
                return await self.execute_wsl_command(f"kill -9 {process_id}")

            elif action == "search":
                result = await self.execute_wsl_command("ps aux")
                if result["success"]:
                    return {
                        "success": True,
                        "process_list": result["output"]
                    }
                return result

            else:
                return {"success": False, "error": "Invalid process action"}

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def get_session_status(self) -> Dict[str, Any]:
        """Get current session status"""
        try:
            return {
                "success": True,
                "active_sessions": {
                    session_id: {
                        "distribution": session.distribution,
                        "working_directory": session.working_directory,
                        "created_at": session.created_at.isoformat(),
                        "last_activity": session.last_activity.isoformat(),
                        "active": session.active
                    }
                    for session_id, session in self.active_sessions.items()
                },
                "command_history_size": len(self.command_history),
                "extensions_available": list(self.extensions.keys()),
                "voice_enabled": self.voice_enabled,
                "mini_window_mode": self.mini_window_mode
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def execute_extension(self, extension_name: str, action: str, **kwargs) -> Dict[str, Any]:
        """Execute an extension function"""
        try:
            if extension_name not in self.extensions:
                return {"success": False, "error": f"Extension {extension_name} not found"}

            extension_func = self.extensions[extension_name]
            return await extension_func(action, **kwargs)

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    # Extension implementations
    async def _file_manager_extension(self, action: str, **kwargs) -> Dict[str, Any]:
        """File manager extension"""
        if action == "list":
            path = kwargs.get("path", ".")
            return await self.manage_files("list", path)
        elif action == "read":
            path = kwargs.get("path")
            return await self.manage_files("read", path)
        elif action == "write":
            path = kwargs.get("path")
            content = kwargs.get("content")
            return await self.manage_files("write", path, content)
        else:
            return {"success": False, "error": f"Unknown file action: {action}"}

    async def _web_search_extension(self, action: str, **kwargs) -> Dict[str, Any]:
        """Web search extension"""
        if action == "search":
            query = kwargs.get("query", "")
            return await self.search_web(query)
        else:
            return {"success": False, "error": f"Unknown web search action: {action}"}

    async def _document_chat_extension(self, action: str, **kwargs) -> Dict[str, Any]:
        """Document chat extension"""
        if action == "process":
            file_path = kwargs.get("file_path")
            query = kwargs.get("query")
            return await self.process_text_document(file_path, query)
        else:
            return {"success": False, "error": f"Unknown document action: {action}"}

    async def _system_info_extension(self, action: str, **kwargs) -> Dict[str, Any]:
        """System info extension"""
        if action == "get":
            return await self.get_system_info()
        else:
            return {"success": False, "error": f"Unknown system info action: {action}"}

    async def _terminal_extension(self, action: str, **kwargs) -> Dict[str, Any]:
        """Terminal extension"""
        if action == "execute":
            command = kwargs.get("command")
            return await self.execute_wsl_command(command)
        else:
            return {"success": False, "error": f"Unknown terminal action: {action}"}

    async def _process_manager_extension(self, action: str, **kwargs) -> Dict[str, Any]:
        """Process manager extension"""
        if action == "list":
            return await self.manage_processes("list")
        elif action == "kill":
            process_id = kwargs.get("process_id")
            return await self.manage_processes("kill", process_id)
        else:
            return {"success": False, "error": f"Unknown process action: {action}"}

    async def _load_memory(self):
        """Load long-term memory"""
        try:
            memory_file = Path("data/newelle_memory.json")
            if memory_file.exists():
                with open(memory_file, 'r') as f:
                    self.long_term_memory = json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load memory: {e}")
            self.long_term_memory = {}

    async def _save_memory(self):
        """Save long-term memory"""
        try:
            memory_file = Path("data/newelle_memory.json")
            memory_file.parent.mkdir(exist_ok=True)
            with open(memory_file, 'w') as f:
                json.dump(self.long_term_memory, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save memory: {e}")

    def get_capabilities(self) -> Dict[str, Any]:
        """Get Newelle integration capabilities"""
        return {
            "available": True,
            "wsl_distribution": self.wsl_distribution,
            "active_sessions": len(self.active_sessions),
            "extensions": list(self.extensions.keys()),
            "features": [
                "WSL command execution",
                "File management",
                "Web search",
                "Document processing",
                "System monitoring",
                "Process management",
                "Multi-session support",
                "Command history",
                "Long-term memory",
                "Extension system"
            ],
            "mini_window_mode": self.mini_window_mode,
            "voice_enabled": self.voice_enabled
        }

    async def start_service(self):
        """Start Newelle as a background service"""
        logger.info("Starting Newelle-inspired WSL integration service...")
        await self.initialize()

        print("[NEWELLE] Newelle WSL Integration Service Active!")
        print(f"WSL Distribution: {self.wsl_distribution}")
        print(f"Active Sessions: {len(self.active_sessions)}")
        print(f"Extensions: {', '.join(self.extensions.keys())}")

        # Run service loop
        while True:
            try:
                await asyncio.sleep(30)  # Service heartbeat
                logger.debug("Newelle service running...")

                # Clean up inactive sessions
                current_time = datetime.now()
                inactive_sessions = [
                    session_id for session_id, session in self.active_sessions.items()
                    if (current_time - session.last_activity).total_seconds() > 3600  # 1 hour
                ]

                for session_id in inactive_sessions:
                    del self.active_sessions[session_id]
                    logger.info(f"Cleaned up inactive session: {session_id}")

            except KeyboardInterrupt:
                logger.info("Newelle service stopped")
                break
            except Exception as e:
                logger.error(f"Newelle service error: {e}")
                await asyncio.sleep(10)

    async def start_interactive_mode(self):
        """Start Newelle in interactive mode"""
        logger.info("Starting Newelle Interactive Mode...")
        await self.initialize()

        print("[NEWELLE] Newelle WSL Integration - Interactive Mode")
        print(f"WSL Distribution: {self.wsl_distribution}")
        print(f"Active Sessions: {len(self.active_sessions)}")
        print("\nCommands:")
        print("  - 'exec <command>' - Execute WSL command")
        print("  - 'files <action> <path>' - File operations (read/write/list/delete)")
        print("  - 'search <query>' - Web search")
        print("  - 'doc <path> [query]' - Process document")
        print("  - 'system' - Show system information")
        print("  - 'processes' - List processes")
        print("  - 'status' - Show session status")
        print("  - 'help' - Show all commands")
        print("  - 'quit' - Exit Newelle")

        while True:
            try:
                command = input("\nNewelle> ").strip()

                if command.lower() in ['quit', 'exit']:
                    break
                elif command.lower() == 'help':
                    await self._show_help()
                elif command.lower() == 'status':
                    status = await self.get_session_status()
                    print(f"Status: {json.dumps(status, indent=2)}")
                elif command.lower() == 'system':
                    sys_info = await self.get_system_info()
                    print(f"System Info: {json.dumps(sys_info, indent=2)}")
                elif command.lower() == 'processes':
                    processes = await self.manage_processes("list")
                    print(f"Processes: {json.dumps(processes, indent=2)}")
                elif command.startswith('exec '):
                    cmd = command[5:]  # Remove 'exec '
                    if cmd:
                        print(f"Executing: {cmd}")
                        result = await self.execute_wsl_command(cmd)
                        print(f"Result: {json.dumps(result, indent=2)}")
                    else:
                        print("Usage: exec <command>")
                elif command.startswith('files '):
                    parts = command[6:].split(' ', 1)  # Remove 'files '
                    if len(parts) >= 2:
                        action, path = parts[0], parts[1]
                        result = await self.manage_files(action, path)
                        print(f"File operation: {json.dumps(result, indent=2)}")
                    else:
                        print("Usage: files <action> <path>")
                elif command.startswith('search '):
                    query = command[7:]  # Remove 'search '
                    if query:
                        result = await self.search_web(query)
                        print(f"Search results: {json.dumps(result, indent=2)}")
                    else:
                        print("Usage: search <query>")
                elif command.startswith('doc '):
                    parts = command[4:].split(' ', 1)  # Remove 'doc '
                    if len(parts) >= 1:
                        path = parts[0]
                        query = parts[1] if len(parts) > 1 else None
                        result = await self.process_text_document(path, query)
                        print(f"Document processing: {json.dumps(result, indent=2)}")
                    else:
                        print("Usage: doc <path> [query]")
                elif command:
                    print(f"Unknown command: {command}")
                    print("Type 'help' for available commands")

            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")

        print("Newelle Interactive Mode ended.")

    async def _show_help(self):
        """Show detailed help information"""
        help_text = """
[NEWELLE] Newelle WSL Integration Commands:

Basic Commands:
  exec <command>           - Execute WSL command
  files <action> <path>    - File operations (read/write/list/delete/mkdir)
  search <query>           - Web search using DuckDuckGo
  doc <path> [query]       - Process text document and optionally search
  system                  - Show comprehensive system information
  processes               - List running processes
  status                  - Show session status and statistics
  help                    - Show this help
  quit/exit               - Exit Newelle

File Operations:
  files read <path>        - Read file content
  files write <path>       - Write content to file
  files list <path>        - List directory contents
  files delete <path>      - Delete file/directory
  files mkdir <path>       - Create directory

Extension Features:
  - File Manager: Advanced file operations
  - Web Search: DuckDuckGo integration
  - Document Chat: Process and search documents
  - System Info: Comprehensive system monitoring
  - Terminal: Command execution
  - Process Manager: Process control

Example Usage:
  Newelle> exec ls -la
  Newelle> files read /etc/os-release
  Newelle> search latest AI developments
  Newelle> doc /var/log/syslog error
  Newelle> system
  Newelle> processes

Advanced Features:
  - Multi-session WSL support
  - Long-term memory system
  - Command history tracking
  - Extension architecture
  - Process management
  - Web integration
        """
        print(help_text)

# Global instance
newelle_integration = NewelleIntegration()

async def initialize_newelle(wsl_distribution: str = "Ubuntu") -> bool:
    """Initialize Newelle integration"""
    global newelle_integration
    newelle_integration = NewelleIntegration(wsl_distribution)
    return await newelle_integration.initialize()

async def execute_newelle_command(command: str, session_id: Optional[str] = None) -> Dict[str, Any]:
    """Execute Newelle command interface"""
    return await newelle_integration.execute_wsl_command(command, session_id)

async def get_newelle_system_info() -> Dict[str, Any]:
    """Get Newelle system information"""
    return await newelle_integration.get_system_info()

def is_newelle_available() -> bool:
    """Check if Newelle is available"""
    return newelle_integration.wsl_distribution is not None

def get_newelle_capabilities() -> Dict[str, Any]:
    """Get Newelle capabilities"""
    return newelle_integration.get_capabilities()