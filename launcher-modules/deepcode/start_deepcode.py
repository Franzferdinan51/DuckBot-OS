#!/usr/bin/env python3
"""
DuckBot DeepCode CLI Launcher
Comprehensive command-line interface for DeepCode integration with DuckBot ecosystem
Provides Paper2Code, Text2Web, Text2Backend capabilities with interactive features

Features:
- Command-line interface for all DeepCode operations
- Interactive configuration wizard
- Service management and health monitoring
- Template management and customization
- Real-time progress monitoring
- Batch processing capabilities
- Integration with DuckBot ecosystem
- WebSocket support for real-time updates
- Resource management and optimization
"""

import os
import sys
import json
import time
import logging
import argparse
import asyncio
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime, timedelta
import tempfile
import shutil

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import DeepCode modules
from deepcode_integration import (
    DuckBotDeepCodeIntegration, DeepCodeConfig, DeepCodeTaskType, DeepCodeStatus
)
from deepcode_mcp_servers import DeepCodeMCPServerManager

# Import DuckBot modules if available
try:
    from duckbot.core.service_manager import UnifiedServiceManager
    from duckbot.core.monitoring_system import MonitoringSystem
    from duckbot.core.cost_management import CostTracker
    from duckbot.core.ai_provider_manager import AIProviderManager
    from duckbot.core.utilities import Utilities
    DUCKBOT_AVAILABLE = True
except ImportError:
    DUCKBOT_AVAILABLE = False
    UnifiedServiceManager = None
    MonitoringSystem = None
    CostTracker = None
    AIProviderManager = None
    Utilities = None

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(project_root / "logs" / "deepcode_cli.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class DeepCodeCLI:
    """Command-line interface for DeepCode operations"""

    def __init__(self):
        self.deepcode = None
        self.mcp_manager = None
        self.config = None
        self.logger = logging.getLogger(__name__)

        # Initialize DuckBot components if available
        self.service_manager = UnifiedServiceManager() if DUCKBOT_AVAILABLE else None
        self.monitoring_system = MonitoringSystem() if DUCKBOT_AVAILABLE else None
        self.cost_tracker = CostTracker() if DUCKBOT_AVAILABLE else None
        self.ai_provider_manager = AIProviderManager() if DUCKBOT_AVAILABLE else None
        self.utilities = Utilities() if DUCKBOT_AVAILABLE else None

    def initialize_deepcode(self, config_path: Optional[str] = None):
        """Initialize DeepCode integration"""
        try:
            # Load configuration
            if config_path and os.path.exists(config_path):
                self.config = self._load_config(config_path)
            else:
                self.config = DeepCodeConfig()

            # Initialize DeepCode integration
            self.deepcode = DuckBotDeepCodeIntegration(self.config)

            # Initialize MCP servers
            self.mcp_manager = DeepCodeMCPServerManager()

            self.logger.info("DeepCode CLI initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize DeepCode: {e}")
            return False

    def _load_config(self, config_path: str) -> DeepCodeConfig:
        """Load DeepCode configuration from file"""
        try:
            with open(config_path, 'r') as f:
                if config_path.endswith('.json'):
                    config_data = json.load(f)
                elif config_path.endswith('.yaml') or config_path.endswith('.yml'):
                    config_data = yaml.safe_load(f)
                else:
                    raise ValueError(f"Unsupported config format: {config_path}")

            # Convert to DeepCodeConfig
            return DeepCodeConfig(**config_data)

        except Exception as e:
            self.logger.error(f"Error loading config: {e}")
            return DeepCodeConfig()

    def paper2code(self, paper_path: str, output_dir: Optional[str] = None,
                   config: Optional[str] = None, follow: bool = False):
        """Process research paper to code"""
        try:
            if not self.deepcode:
                print("DeepCode not initialized. Please run 'config' first.")
                return

            # Load task-specific config if provided
            task_config = {}
            if config and os.path.exists(config):
                with open(config, 'r') as f:
                    task_config = json.load(f)

            # Submit task
            task_id = asyncio.run(self.deepcode.paper2code(paper_path, output_dir, task_config))

            print(f"Paper2Code task submitted successfully!")
            print(f"Task ID: {task_id}")
            print(f"Paper: {paper_path}")
            print(f"Output: {output_dir or f'./deepcode_output/{task_id}'}")

            # Monitor if requested
            if follow:
                self._monitor_task(task_id)

            return task_id

        except Exception as e:
            print(f"Error submitting Paper2Code task: {e}")
            return None

    def text2web(self, description: str, output_dir: Optional[str] = None,
                 config: Optional[str] = None, follow: bool = False):
        """Generate web application from text description"""
        try:
            if not self.deepcode:
                print("DeepCode not initialized. Please run 'config' first.")
                return

            # Load task-specific config if provided
            task_config = {}
            if config and os.path.exists(config):
                with open(config, 'r') as f:
                    task_config = json.load(f)

            # Submit task
            task_id = asyncio.run(self.deepcode.text2web(description, output_dir, task_config))

            print(f"Text2Web task submitted successfully!")
            print(f"Task ID: {task_id}")
            print(f"Description: {description[:100]}...")
            print(f"Output: {output_dir or f'./deepcode_output/{task_id}'}")

            # Monitor if requested
            if follow:
                self._monitor_task(task_id)

            return task_id

        except Exception as e:
            print(f"Error submitting Text2Web task: {e}")
            return None

    def text2backend(self, description: str, output_dir: Optional[str] = None,
                     config: Optional[str] = None, follow: bool = False):
        """Generate backend system from text description"""
        try:
            if not self.deepcode:
                print("DeepCode not initialized. Please run 'config' first.")
                return

            # Load task-specific config if provided
            task_config = {}
            if config and os.path.exists(config):
                with open(config, 'r') as f:
                    task_config = json.load(f)

            # Submit task
            task_id = asyncio.run(self.deepcode.text2backend(description, output_dir, task_config))

            print(f"Text2Backend task submitted successfully!")
            print(f"Task ID: {task_id}")
            print(f"Description: {description[:100]}...")
            print(f"Output: {output_dir or f'./deepcode_output/{task_id}'}")

            # Monitor if requested
            if follow:
                self._monitor_task(task_id)

            return task_id

        except Exception as e:
            print(f"Error submitting Text2Backend task: {e}")
            return None

    def status(self, task_id: Optional[str] = None, task_type: Optional[str] = None,
               status_filter: Optional[str] = None, detailed: bool = False):
        """Check task status"""
        try:
            if not self.deepcode:
                print("DeepCode not initialized. Please run 'config' first.")
                return

            if task_id:
                # Get specific task status
                task_status = asyncio.run(self.deepcode.get_task_status(task_id))
                if task_status:
                    self._display_task_status(task_status, detailed)
                else:
                    print(f"Task {task_id} not found")
            else:
                # List tasks with optional filtering
                tasks = asyncio.run(self.deepcode.list_tasks(task_type, status_filter))

                if not tasks:
                    print("No tasks found")
                    return

                print(f"Tasks ({task_type or 'All'} - {status_filter or 'All Statuses'}):")
                print("=" * 80)

                for task in tasks:
                    self._display_task_summary(task)

        except Exception as e:
            print(f"Error getting task status: {e}")

    def _display_task_status(self, task_status: Dict[str, Any], detailed: bool = False):
        """Display detailed task status"""
        print(f"Task ID: {task_status['task_id']}")
        print(f"Type: {task_status['task_type']}")
        print(f"Status: {task_status['status']}")
        print(f"Created: {task_status['created_at']}")

        if task_status['started_at']:
            print(f"Started: {task_status['started_at']}")
        if task_status['completed_at']:
            print(f"Completed: {task_status['completed_at']}")

        if detailed:
            print(f"Progress: {task_status['progress']} steps")

            if task_status.get('logs'):
                print("Recent logs:")
                for log in task_status['logs'][-5:]:
                    print(f"  {log}")

            if task_status.get('error_message'):
                print(f"Error: {task_status['error_message']}")

            if task_status.get('result'):
                print("Result:")
                result = task_status['result']
                for key, value in result.items():
                    print(f"  {key}: {value}")

    def _display_task_summary(self, task: Dict[str, Any]):
        """Display task summary"""
        status_symbol = {
            'pending': '⏳',
            'planning': '📋',
            'executing': '⚡',
            'validating': '✅',
            'completed': '✅',
            'failed': '❌',
            'cancelled': '🚫'
        }.get(task['status'], '❓')

        print(f"{status_symbol} {task['task_id']}")
        print(f"   Type: {task['task_type']}")
        print(f"   Status: {task['status']}")
        print(f"   Created: {task['created_at']}")
        if task['completed_at']:
            print(f"   Completed: {task['completed_at']}")
        print("-" * 40)

    def config_wizard(self):
        """Interactive configuration wizard"""
        print("DeepCode Configuration Wizard")
        print("=" * 40)

        config_data = {}

        try:
            # Basic configuration
            print("\n1. Basic Configuration")
            print("-" * 20)

            output_dir = input(f"Output directory [default: ./deepcode_output]: ").strip()
            if output_dir:
                config_data['output_dir'] = output_dir

            max_concurrent = input(f"Max concurrent tasks [default: 3]: ").strip()
            if max_concurrent and max_concurrent.isdigit():
                config_data['max_concurrent_tasks'] = int(max_concurrent)

            timeout = input(f"Task timeout (seconds) [default: 3600]: ").strip()
            if timeout and timeout.isdigit():
                config_data['timeout_seconds'] = int(timeout)

            # Quality settings
            print("\n2. Quality Settings")
            print("-" * 20)

            validation = input("Enable code validation [Y/n]: ").strip().lower()
            config_data['enable_validation'] = validation != 'n'

            testing = input("Enable automated testing [Y/n]: ").strip().lower()
            config_data['enable_testing'] = testing != 'n'

            quality_threshold = input("Code quality threshold (0.0-1.0) [default: 0.8]: ").strip()
            if quality_threshold:
                try:
                    config_data['code_quality_threshold'] = float(quality_threshold)
                except ValueError:
                    print("Invalid value, using default")

            # Integration settings
            print("\n3. Integration Settings")
            print("-" * 20)

            duckbot_integration = input("Enable DuckBot integration [Y/n]: ").strip().lower()
            config_data['enable_duckbot_integration'] = duckbot_integration != 'n'

            cost_tracking = input("Enable cost tracking [Y/n]: ").strip().lower()
            config_data['enable_cost_tracking'] = cost_tracking != 'n'

            # API keys
            print("\n4. API Keys (Optional)")
            print("-" * 20)

            api_keys = {}
            brave_key = input("Brave API key (press Enter to skip): ").strip()
            if brave_key:
                api_keys['brave'] = brave_key

            if api_keys:
                config_data['api_keys'] = api_keys

            # Create configuration
            config = DeepCodeConfig(**config_data)

            # Save configuration
            config_path = project_root / "config" / "deepcode_config.json"
            config_path.parent.mkdir(exist_ok=True)

            with open(config_path, 'w') as f:
                json.dump(asdict(config), f, indent=2)

            print(f"\nConfiguration saved to: {config_path}")
            print("Configuration wizard completed successfully!")

            # Display summary
            print("\nConfiguration Summary:")
            print("-" * 20)
            print(f"Output directory: {config.output_dir}")
            print(f"Max concurrent tasks: {config.max_concurrent_tasks}")
            print(f"Code validation: {'Enabled' if config.enable_validation else 'Disabled'}")
            print(f"Automated testing: {'Enabled' if config.enable_testing else 'Disabled'}")
            print(f"DuckBot integration: {'Enabled' if config.enable_duckbot_integration else 'Disabled'}")
            print(f"Cost tracking: {'Enabled' if config.enable_cost_tracking else 'Disabled'}")

        except KeyboardInterrupt:
            print("\nConfiguration wizard cancelled.")
        except Exception as e:
            print(f"Error in configuration wizard: {e}")

    def service(self, port: int = 8790):
        """Start DeepCode service"""
        try:
            if not self.deepcode:
                print("DeepCode not initialized. Please run 'config' first.")
                return

            print("Starting DeepCode service...")

            # Initialize service
            success = asyncio.run(self.deepcode.initialize_service())
            if not success:
                print("Failed to initialize DeepCode service")
                return

            # Initialize MCP servers
            if self.mcp_manager:
                asyncio.run(self.mcp_manager.initialize_servers())

            print("DeepCode service started successfully")
            print(f"Service port: {port}")
            print("Press Ctrl+C to stop the service")

            # Keep service running
            try:
                while True:
                    status = asyncio.run(self.deepcode.get_service_status())
                    print(f"\rActive: {status['active_tasks']} | "
                          f"Queue: {status['queue_size']} | "
                          f"MCP: {len(self.mcp_manager.servers) if self.mcp_manager else 0} servers", end="")
                    time.sleep(5)
            except KeyboardInterrupt:
                print("\nStopping service...")

                # Shutdown MCP servers
                if self.mcp_manager:
                    asyncio.run(self.mcp_manager.shutdown_servers())

                # Shutdown DeepCode
                self.deepcode.shutdown()

        except Exception as e:
            print(f"Error starting service: {e}")

    def templates(self, template_type: Optional[str] = None):
        """List available templates"""
        print("DeepCode Templates")
        print("=" * 30)

        # Define available templates
        templates = {
            "paper2code": [
                {
                    "name": "ml_algorithm",
                    "description": "Machine learning algorithm implementation",
                    "complexity": "medium",
                    "estimated_time": "2-4 hours",
                    "output": "Complete Python package with tests"
                },
                {
                    "name": "data_processing",
                    "description": "Data processing pipeline",
                    "complexity": "low",
                    "estimated_time": "1-2 hours",
                    "output": "Data processing scripts and utilities"
                },
                {
                    "name": "computer_vision",
                    "description": "Computer vision model",
                    "complexity": "high",
                    "estimated_time": "4-6 hours",
                    "output": "CV model with training scripts"
                }
            ],
            "text2web": [
                {
                    "name": "dashboard",
                    "description": "Analytics dashboard",
                    "complexity": "medium",
                    "estimated_time": "2-3 hours",
                    "output": "React dashboard with charts"
                },
                {
                    "name": "crud_app",
                    "description": "CRUD web application",
                    "complexity": "medium",
                    "estimated_time": "3-4 hours",
                    "output": "Full-stack CRUD application"
                },
                {
                    "name": "portfolio",
                    "description": "Portfolio website",
                    "complexity": "low",
                    "estimated_time": "1-2 hours",
                    "output": "Responsive portfolio site"
                }
            ],
            "text2backend": [
                {
                    "name": "rest_api",
                    "description": "REST API service",
                    "complexity": "medium",
                    "estimated_time": "2-3 hours",
                    "output": "FastAPI REST service"
                },
                {
                    "name": "microservice",
                    "description": "Microservice architecture",
                    "complexity": "high",
                    "estimated_time": "4-5 hours",
                    "output": "Microservice with Docker"
                },
                {
                    "name": "data_api",
                    "description": "Data processing API",
                    "complexity": "medium",
                    "estimated_time": "2-4 hours",
                    "output": "Data processing pipeline API"
                }
            ]
        }

        if template_type and template_type in templates:
            print(f"\n{template_type.upper()} Templates:")
            print("-" * 20)

            for i, template in enumerate(templates[template_type], 1):
                print(f"{i}. {template['name']}")
                print(f"   Description: {template['description']}")
                print(f"   Complexity: {template['complexity']}")
                print(f"   Estimated Time: {template['estimated_time']}")
                print(f"   Output: {template['output']}")
                print()
        else:
            for category, category_templates in templates.items():
                print(f"\n{category.upper()} ({len(category_templates)} templates):")
                for template in category_templates:
                    print(f"  • {template['name']}: {template['description']}")

    def health(self):
        """Perform health check"""
        print("DeepCode Health Check")
        print("=" * 30)

        try:
            health_status = {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "checks": {}
            }

            # Check DeepCode integration
            if self.deepcode:
                service_status = asyncio.run(self.deepcode.get_service_status())
                health_status["checks"]["deepcode_integration"] = True
                health_status["checks"]["mcp_available"] = service_status.get("mcp_available", False)
                health_status["checks"]["active_tasks"] = service_status.get("active_tasks", 0)
                health_status["checks"]["queue_size"] = service_status.get("queue_size", 0)
            else:
                health_status["checks"]["deepcode_integration"] = False

            # Check MCP servers
            if self.mcp_manager:
                mcp_status = self.mcp_manager.get_server_status()
                health_status["checks"]["mcp_servers"] = mcp_status.get("total_servers", 0) > 0
            else:
                health_status["checks"]["mcp_servers"] = False

            # Check DuckBot integration
            health_status["checks"]["duckbot_available"] = DUCKBOT_AVAILABLE

            # Check output directory
            output_dir = Path(self.config.output_dir if self.config else "./deepcode_output")
            health_status["checks"]["output_directory"] = output_dir.exists()

            # Check configuration
            config_path = project_root / "config" / "deepcode_config.json"
            health_status["checks"]["configuration"] = config_path.exists()

            # Display results
            print(f"Overall Status: {health_status['status']}")
            print(f"Timestamp: {health_status['timestamp']}")
            print("\nChecks:")

            for check_name, check_result in health_status["checks"].items():
                status_symbol = "✓" if check_result else "✗"
                if isinstance(check_result, bool):
                    print(f"  {status_symbol} {check_name}: {'Pass' if check_result else 'Fail'}")
                else:
                    print(f"  • {check_name}: {check_result}")

            # Recommendations
            print("\nRecommendations:")
            if not health_status["checks"]["configuration"]:
                print("  • Run 'python start_deepcode.py config' to create configuration")
            if not health_status["checks"]["deepcode_integration"]:
                print("  • Check DeepCode installation and dependencies")
            if not health_status["checks"]["mcp_servers"]:
                print("  • Check MCP server dependencies")
            if not health_status["checks"]["output_directory"]:
                print("  • Create output directory or check permissions")

        except Exception as e:
            print(f"Error performing health check: {e}")

    def _monitor_task(self, task_id: str):
        """Monitor task progress"""
        try:
            print(f"Monitoring task {task_id}...")
            print("Press Ctrl+C to stop monitoring")

            while True:
                task_status = asyncio.run(self.deepcode.get_task_status(task_id))

                if not task_status:
                    print(f"Task {task_id} not found")
                    break

                status = task_status['status']
                progress = task_status.get('progress', 0)

                # Clear line and update
                print(f"\rTask {task_id}: {status} | Progress: {progress} steps", end="")

                if status in ['completed', 'failed', 'cancelled']:
                    print(f"\nTask {status}")
                    if task_status.get('error_message'):
                        print(f"Error: {task_status['error_message']}")
                    break

                time.sleep(2)

        except KeyboardInterrupt:
            print(f"\nStopped monitoring task {task_id}")
        except Exception as e:
            print(f"\nError monitoring task: {e}")

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="DuckBot DeepCode CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python start_deepcode.py config                           # Create configuration
  python start_deepcode.py paper2code paper.pdf             # Process paper to code
  python start_deepcode.py text2web "Create a dashboard"     # Generate web app
  python start_deepcode.py text2backend "User management API" # Generate backend
  python start_deepcode.py status                          # Check all tasks
  python start_deepcode.py status TASK_ID                   # Check specific task
  python start_deepcode.py templates                       # List templates
  python start_deepcode.py service                         # Start service
  python start_deepcode.py health                          # Health check
        """
    )

    parser.add_argument('--config', '-c', help='Configuration file path')

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Paper2Code command
    paper2code_parser = subparsers.add_parser('paper2code', help='Process research paper to code')
    paper2code_parser.add_argument('paper_path', help='Path to research paper')
    paper2code_parser.add_argument('-o', '--output-dir', help='Output directory')
    paper2code_parser.add_argument('-t', '--task-config', help='Task configuration file')
    paper2code_parser.add_argument('-f', '--follow', action='store_true', help='Follow task progress')

    # Text2Web command
    text2web_parser = subparsers.add_parser('text2web', help='Generate web application from text')
    text2web_parser.add_argument('description', help='Application description')
    text2web_parser.add_argument('-o', '--output-dir', help='Output directory')
    text2web_parser.add_argument('-t', '--task-config', help='Task configuration file')
    text2web_parser.add_argument('-f', '--follow', action='store_true', help='Follow task progress')

    # Text2Backend command
    text2backend_parser = subparsers.add_parser('text2backend', help='Generate backend system from text')
    text2backend_parser.add_argument('description', help='Backend description')
    text2backend_parser.add_argument('-o', '--output-dir', help='Output directory')
    text2backend_parser.add_argument('-t', '--task-config', help='Task configuration file')
    text2backend_parser.add_argument('-f', '--follow', action='store_true', help='Follow task progress')

    # Status command
    status_parser = subparsers.add_parser('status', help='Check task status')
    status_parser.add_argument('task_id', nargs='?', help='Specific task ID')
    status_parser.add_argument('--type', help='Filter by task type')
    status_parser.add_argument('--status', help='Filter by status')
    status_parser.add_argument('-d', '--detailed', action='store_true', help='Show detailed information')

    # Config command
    config_parser = subparsers.add_parser('config', help='Configuration wizard')

    # Service command
    service_parser = subparsers.add_parser('service', help='Start DeepCode service')
    service_parser.add_argument('-p', '--port', type=int, default=8790, help='Service port')

    # Templates command
    templates_parser = subparsers.add_parser('templates', help='List available templates')
    templates_parser.add_argument('--type', help='Filter by template type')

    # Health command
    subparsers.add_parser('health', help='Perform health check')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    cli = DeepCodeCLI()

    # Initialize DeepCode with config
    cli.initialize_deepcode(args.config)

    try:
        if args.command == 'paper2code':
            cli.paper2code(args.paper_path, args.output_dir, args.task_config, args.follow)
        elif args.command == 'text2web':
            cli.text2web(args.description, args.output_dir, args.task_config, args.follow)
        elif args.command == 'text2backend':
            cli.text2backend(args.description, args.output_dir, args.task_config, args.follow)
        elif args.command == 'status':
            cli.status(args.task_id, args.type, args.status, args.detailed)
        elif args.command == 'config':
            cli.config_wizard()
        elif args.command == 'service':
            cli.service(args.port)
        elif args.command == 'templates':
            cli.templates(args.type)
        elif args.command == 'health':
            cli.health()
        else:
            parser.print_help()

    except KeyboardInterrupt:
        print("\nOperation cancelled")
    except Exception as e:
        print(f"Error: {e}")
        logger.error(f"CLI error: {e}")

if __name__ == "__main__":
    main()