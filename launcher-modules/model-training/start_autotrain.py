#!/usr/bin/env python3
"""
DuckBot AutoTrain Launcher
Main launcher for AutoTrain-Advanced integration with DuckBot
Provides command-line interface and service management

Features:
- Command-line interface for AutoTrain operations
- Service management and health monitoring
- Configuration management
- Job submission and monitoring
- Results processing and deployment
- Integration with DuckBot ecosystem
"""

import os
import sys
import json
import time
import logging
import argparse
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import AutoTrain modules
from autotrain_integration import AutoTrainConfig, AutoTrainProjectType
from autotrain_config_manager import AutoTrainConfigManager, ConfigFormat
from autotrain_job_manager import AutoTrainJobManager, JobPriority
from autotrain_results_processor import AutoTrainResultsProcessor, DeploymentConfig, DeploymentTarget
from autotrain_duckbot_integration import DuckBotAutoTrainIntegration

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(project_root / "logs" / "autotrain.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class AutoTrainCLI:
    """Command-line interface for AutoTrain operations"""

    def __init__(self):
        self.config_manager = AutoTrainConfigManager()
        self.job_manager = AutoTrainJobManager()
        self.results_processor = AutoTrainResultsProcessor()
        self.integration = DuckBotAutoTrainIntegration()

    def list_templates(self):
        """List available training templates"""
        print("Available AutoTrain Templates:")
        print("=" * 50)

        templates = self.config_manager.list_templates()
        for i, template in enumerate(templates, 1):
            print(f"{i}. {template.name}")
            print(f"   Type: {template.project_type.value.replace('_', ' ').title()}")
            print(f"   Description: {template.description}")
            print(f"   Difficulty: {template.difficulty}")
            print(f"   Estimated Time: {template.estimated_time}")
            print(f"   Hardware: {', '.join(template.hardware_requirements)}")
            print()

    def create_config_wizard(self):
        """Interactive configuration wizard"""
        print("AutoTrain Configuration Wizard")
        print("=" * 30)

        try:
            config = self.config_manager.create_wizard_config()
            if config:
                print("\nConfiguration created successfully!")
                print(self.config_manager.export_config_summary(config))
            else:
                print("Configuration creation cancelled or failed.")
        except KeyboardInterrupt:
            print("\nConfiguration wizard cancelled.")
        except Exception as e:
            print(f"Error in configuration wizard: {e}")

    def submit_job(self, config_file: str, priority: str = "normal", tags: Optional[List[str]] = None):
        """Submit a training job from configuration file"""
        try:
            # Load configuration
            config = self.config_manager.load_config(config_file)

            # Convert priority
            priority_map = {
                "low": JobPriority.LOW,
                "normal": JobPriority.NORMAL,
                "high": JobPriority.HIGH,
                "critical": JobPriority.CRITICAL
            }
            job_priority = priority_map.get(priority.lower(), JobPriority.NORMAL)

            # Submit job
            job_id = self.job_manager.submit_job(
                config,
                priority=job_priority,
                tags=tags or []
            )

            print(f"Job submitted successfully!")
            print(f"Job ID: {job_id}")
            print(f"Project: {config.project_name}")
            print(f"Type: {config.project_type.value}")
            print(f"Priority: {priority}")

            return job_id

        except Exception as e:
            print(f"Error submitting job: {e}")
            return None

    def monitor_job(self, job_id: str, follow: bool = False):
        """Monitor a specific job"""
        try:
            while True:
                status = self.job_manager.get_job_status(job_id)

                if not status:
                    print(f"Job {job_id} not found")
                    return

                print(f"Job ID: {job_id}")
                print(f"Status: {status['status']}")
                print(f"Project: {status.get('project_name', 'N/A')}")

                if status['status'] == 'running':
                    if 'metrics' in status:
                        metrics = status['metrics']
                        if 'loss' in metrics:
                            print(f"Loss: {metrics['loss']:.4f}")
                        if 'learning_rate' in metrics:
                            print(f"Learning Rate: {metrics['learning_rate']:.2e}")

                elif status['status'] in ['completed', 'failed', 'cancelled']:
                    if status['status'] == 'completed':
                        print(f"✓ Job completed successfully!")
                        if 'metrics' in status:
                            metrics = status['metrics']
                            if 'duration' in metrics:
                                duration = metrics['duration']
                                hours = int(duration // 3600)
                                minutes = int((duration % 3600) // 60)
                                seconds = int(duration % 60)
                                print(f"Duration: {hours:02d}:{minutes:02d}:{seconds:02d}")
                    elif status['status'] == 'failed':
                        print(f"✗ Job failed!")
                        if status.get('error_message'):
                            print(f"Error: {status['error_message']}")
                    else:
                        print(f"Job cancelled")

                    break

                if not follow:
                    break

                time.sleep(5)

        except KeyboardInterrupt:
            print("\nMonitoring stopped")
        except Exception as e:
            print(f"Error monitoring job: {e}")

    def list_jobs(self, status: Optional[str] = None):
        """List all jobs"""
        try:
            jobs = self.job_manager.list_jobs(status=status)

            if not jobs:
                print("No jobs found")
                return

            print(f"Jobs ({'Status: ' + status if status else 'All'}):")
            print("=" * 80)

            for job in jobs:
                print(f"Job ID: {job['job_id']}")
                print(f"Project: {job['project_name']}")
                print(f"Status: {job['status']}")
                print(f"Priority: {job['priority']}")
                print(f"Submitted: {job['submit_time']}")
                if job.get('start_time'):
                    print(f"Started: {job['start_time']}")
                if job.get('end_time'):
                    print(f"Ended: {job['end_time']}")
                print("-" * 40)

        except Exception as e:
            print(f"Error listing jobs: {e}")

    def cancel_job(self, job_id: str):
        """Cancel a job"""
        try:
            success = self.job_manager.cancel_job(job_id)
            if success:
                print(f"Job {job_id} cancelled successfully")
            else:
                print(f"Failed to cancel job {job_id}")
        except Exception as e:
            print(f"Error cancelling job: {e}")

    def process_results(self, job_id: str):
        """Process job results"""
        try:
            result = self.results_processor.process_completed_job(job_id)

            if result:
                print(f"Results processed for job {job_id}")
                print(f"Model path: {result.model_path}")
                print(f"Model size: {result.metrics.model_size:.2f} GB")

                if result.metrics.loss:
                    print(f"Final loss: {result.metrics.loss:.4f}")
                if result.metrics.accuracy:
                    print(f"Final accuracy: {result.metrics.accuracy:.4f}")

                # Auto-deploy locally
                deploy_config = DeploymentConfig(
                    target=DeploymentTarget.LOCAL,
                    model_path=result.model_path,
                    model_name=f"autotrain_{job_id}",
                    description=f"Auto-trained model from job {job_id}"
                )

                success = self.results_processor.deploy_model(result, deploy_config)
                print(f"Local deployment: {'Success' if success else 'Failed'}")

            else:
                print(f"Failed to process results for job {job_id}")

        except Exception as e:
            print(f"Error processing results: {e}")

    def show_queue_status(self):
        """Show job queue status"""
        try:
            status = self.job_manager.get_queue_status()
            print("Job Queue Status:")
            print("=" * 30)
            print(f"Queued: {status['queued']}")
            print(f"Running: {status['running']}")
            print(f"Completed: {status['completed']}")
            print(f"Max Concurrent: {status['max_concurrent']}")
            print(f"Processing: {status['processing']}")
        except Exception as e:
            print(f"Error getting queue status: {e}")

    def show_system_resources(self):
        """Show system resources"""
        try:
            if hasattr(self.job_manager.autotrain_manager, 'get_system_resources'):
                resources = self.job_manager.autotrain_manager.get_system_resources()
                print("System Resources:")
                print("=" * 30)
                for key, value in resources.items():
                    print(f"{key}: {value}")
            else:
                print("System resources information not available")
        except Exception as e:
            print(f"Error getting system resources: {e}")

    def start_service(self):
        """Start AutoTrain service"""
        try:
            print("Starting AutoTrain service...")
            success = asyncio.run(self.integration.initialize_service())

            if success:
                print("AutoTrain service started successfully")

                # Keep service running
                try:
                    while True:
                        time.sleep(10)
                        status = asyncio.run(self.integration.get_service_status())
                        print(f"\rService Status: {status['status']} | "
                              f"Active Jobs: {status['metrics']['active_jobs']} | "
                              f"Completed: {status['metrics']['completed_jobs']} | "
                              f"Failed: {status['metrics']['failed_jobs']}", end="")
                except KeyboardInterrupt:
                    print("\nStopping service...")
                    self.integration.shutdown()
            else:
                print("Failed to start AutoTrain service")

        except Exception as e:
            print(f"Error starting service: {e}")

    def health_check(self):
        """Perform health check"""
        try:
            health = asyncio.run(self.integration.health_check())
            print("AutoTrain Health Check:")
            print("=" * 30)
            print(f"Overall Status: {health['status']}")
            print(f"Timestamp: {health['timestamp']}")
            print("Checks:")
            for check_name, check_result in health['checks'].items():
                status_symbol = "✓" if check_result else "✗"
                print(f"  {status_symbol} {check_name}: {check_result}")
        except Exception as e:
            print(f"Error performing health check: {e}")

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="DuckBot AutoTrain-Advanced CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python start_autotrain.py templates                    # List available templates
  python start_autotrain.py wizard                       # Create configuration
  python start_autotrain.py submit -c config.yaml        # Submit job
  python start_autotrain.py monitor JOB_ID              # Monitor job
  python start_autotrain.py jobs                         # List all jobs
  python start_autotrain.py service                      # Start service
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Templates command
    subparsers.add_parser('templates', help='List available templates')

    # Wizard command
    subparsers.add_parser('wizard', help='Interactive configuration wizard')

    # Submit command
    submit_parser = subparsers.add_parser('submit', help='Submit training job')
    submit_parser.add_argument('-c', '--config', required=True, help='Configuration file')
    submit_parser.add_argument('-p', '--priority', choices=['low', 'normal', 'high', 'critical'],
                               default='normal', help='Job priority')
    submit_parser.add_argument('-t', '--tags', nargs='*', help='Job tags')

    # Monitor command
    monitor_parser = subparsers.add_parser('monitor', help='Monitor job')
    monitor_parser.add_argument('job_id', help='Job ID to monitor')
    monitor_parser.add_argument('-f', '--follow', action='store_true', help='Follow job progress')

    # Jobs command
    jobs_parser = subparsers.add_parser('jobs', help='List jobs')
    jobs_parser.add_argument('-s', '--status', help='Filter by status')

    # Cancel command
    cancel_parser = subparsers.add_parser('cancel', help='Cancel job')
    cancel_parser.add_argument('job_id', help='Job ID to cancel')

    # Process command
    process_parser = subparsers.add_parser('process', help='Process job results')
    process_parser.add_argument('job_id', help='Job ID to process')

    # Queue command
    subparsers.add_parser('queue', help='Show queue status')

    # Resources command
    subparsers.add_parser('resources', help='Show system resources')

    # Service command
    subparsers.add_parser('service', help='Start AutoTrain service')

    # Health command
    subparsers.add_parser('health', help='Perform health check')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    cli = AutoTrainCLI()

    # Ensure job manager is running for commands that need it
    if args.command in ['submit', 'monitor', 'jobs', 'cancel', 'process', 'queue']:
        cli.job_manager.start_processing()

    try:
        if args.command == 'templates':
            cli.list_templates()
        elif args.command == 'wizard':
            cli.create_config_wizard()
        elif args.command == 'submit':
            cli.submit_job(args.config, args.priority, args.tags)
        elif args.command == 'monitor':
            cli.monitor_job(args.job_id, args.follow)
        elif args.command == 'jobs':
            cli.list_jobs(args.status)
        elif args.command == 'cancel':
            cli.cancel_job(args.job_id)
        elif args.command == 'process':
            cli.process_results(args.job_id)
        elif args.command == 'queue':
            cli.show_queue_status()
        elif args.command == 'resources':
            cli.show_system_resources()
        elif args.command == 'service':
            cli.start_service()
        elif args.command == 'health':
            cli.health_check()
        else:
            parser.print_help()

    except KeyboardInterrupt:
        print("\nOperation cancelled")
    except Exception as e:
        print(f"Error: {e}")
        logger.error(f"CLI error: {e}")
    finally:
        # Stop job manager if it was started
        if args.command in ['submit', 'monitor', 'jobs', 'cancel', 'process', 'queue']:
            cli.job_manager.stop_processing()

if __name__ == "__main__":
    main()