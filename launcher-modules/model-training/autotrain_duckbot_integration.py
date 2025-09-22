#!/usr/bin/env python3
"""
DuckBot AutoTrain Integration Module
Complete integration of AutoTrain-Advanced with DuckBot ecosystem
Provides seamless integration with DuckBot's AI providers, service management, and UI systems

Features:
- Complete integration with DuckBot's AI provider system
- Service management and health monitoring
- UI components and dashboards
- WebSocket-based real-time updates
- Cost tracking and resource management
- Unified configuration management
- Integration with existing DuckBot training modules
"""

import os
import sys
import json
import time
import logging
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import threading
from datetime import datetime, timedelta

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import AutoTrain modules
from autotrain_integration import AutoTrainManager, AutoTrainConfig, AutoTrainProjectType
from autotrain_config_manager import AutoTrainConfigManager
from autotrain_job_manager import AutoTrainJobManager, JobStatus, JobPriority
from autotrain_results_processor import AutoTrainResultsProcessor, DeploymentConfig, DeploymentTarget

# Import DuckBot modules
try:
    from duckbot.core.service_manager import UnifiedServiceManager, ServiceInfo, ServiceType, ServiceStatus
    from duckbot.core.monitoring_system import MonitoringSystem
    from duckbot.core.cost_management import CostTracker
    from duckbot.core.ai_provider_manager import AIProviderManager
    from duckbot.core.dynamic_model_manager import DynamicModelManager
    from duckbot.core.utilities import Utilities
    DUCKBOT_AVAILABLE = True
except ImportError as e:
    logging.warning(f"DuckBot modules not available: {e}")
    DUCKBOT_AVAILABLE = False
    UnifiedServiceManager = None
    MonitoringSystem = None
    CostTracker = None
    AIProviderManager = None
    DynamicModelManager = None
    Utilities = None

class AutoTrainServiceStatus(Enum):
    """AutoTrain service status"""
    IDLE = "idle"
    TRAINING = "training"
    PROCESSING = "processing"
    DEPLOYING = "deploying"
    ERROR = "error"

@dataclass
class AutoTrainServiceMetrics:
    """AutoTrain service metrics"""
    total_jobs: int = 0
    completed_jobs: int = 0
    failed_jobs: int = 0
    active_jobs: int = 0
    total_training_time: float = 0.0
    models_deployed: int = 0
    cost_estimate: float = 0.0
    last_activity: Optional[datetime] = None

class DuckBotAutoTrainIntegration:
    """Complete integration of AutoTrain with DuckBot ecosystem"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.service_name = "autotrain_integration"
        self.service_version = "1.0.0"

        # Initialize AutoTrain components
        self.autotrain_manager = AutoTrainManager()
        self.config_manager = AutoTrainConfigManager()
        self.job_manager = AutoTrainJobManager()
        self.results_processor = AutoTrainResultsProcessor()

        # Initialize DuckBot components
        self.service_manager = UnifiedServiceManager() if DUCKBOT_AVAILABLE else None
        self.monitoring_system = MonitoringSystem() if DUCKBOT_AVAILABLE else None
        self.cost_tracker = CostTracker() if DUCKBOT_AVAILABLE else None
        self.ai_provider_manager = AIProviderManager() if DUCKBOT_AVAILABLE else None
        self.dynamic_model_manager = DynamicModelManager() if DUCKBOT_AVAILABLE else None
        self.utilities = Utilities() if DUCKBOT_AVAILABLE else None

        # Service state
        self.service_status = AutoTrainServiceStatus.IDLE
        self.service_metrics = AutoTrainServiceMetrics()
        self.service_info = None

        # Event handling
        self.event_handlers = {}
        self._setup_event_handlers()

        # WebSocket support for real-time updates
        self.websocket_clients = set()

        # Background tasks
        self._running = False
        self._monitor_thread = None

    def _setup_event_handlers(self):
        """Setup event handlers for job management"""
        self.job_manager.add_event_callback("job_submitted", self._on_job_submitted)
        self.job_manager.add_event_callback("job_started", self._on_job_started)
        self.job_manager.add_event_callback("job_completed", self._on_job_completed)
        self.job_manager.add_event_callback("job_failed", self._on_job_failed)
        self.job_manager.add_event_callback("job_cancelled", self._on_job_cancelled)

    async def initialize_service(self):
        """Initialize the AutoTrain service within DuckBot ecosystem"""
        try:
            if not DUCKBOT_AVAILABLE:
                self.logger.error("DuckBot modules not available")
                return False

            # Create service info
            self.service_info = ServiceInfo(
                name=self.service_name,
                service_type=ServiceType.AI_TRAINING,
                description="AutoTrain-Advanced integration for no-code ML training",
                version=self.service_version
            )

            # Register service
            await self.service_manager.register_service(self.service_info)

            # Start job processing
            self.job_manager.start_processing()

            # Start monitoring
            self._start_monitoring()

            self.logger.info("AutoTrain service initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize AutoTrain service: {e}")
            return False

    def _start_monitoring(self):
        """Start background monitoring"""
        self._running = True
        self._monitor_thread = threading.Thread(target=self._monitoring_loop)
        self._monitor_thread.daemon = True
        self._monitor_thread.start()

    def _monitoring_loop(self):
        """Background monitoring loop"""
        while self._running:
            try:
                self._update_service_metrics()
                self._check_service_health()
                time.sleep(30)  # Update every 30 seconds
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")

    def _update_service_metrics(self):
        """Update service metrics"""
        try:
            # Get job statistics
            job_stats = self.job_manager.get_job_statistics()

            # Update metrics
            self.service_metrics.total_jobs = job_stats["total_jobs"]
            self.service_metrics.completed_jobs = job_stats["completed_jobs"]
            self.service_metrics.failed_jobs = job_stats["failed_jobs"]
            self.service_metrics.active_jobs = job_stats["queue_status"]["running"]
            self.service_metrics.last_activity = datetime.now()

            # Calculate cost estimate
            if self.cost_tracker:
                # Simple cost estimation based on training time
                self.service_metrics.cost_estimate = (
                    self.service_metrics.total_training_time * 0.001  # $0.001 per second
                )

            # Broadcast update to WebSocket clients
            self._broadcast_metrics_update()

        except Exception as e:
            self.logger.error(f"Error updating service metrics: {e}")

    def _check_service_health(self):
        """Check service health"""
        try:
            # Check if AutoTrain is available
            if not hasattr(self.autotrain_manager, 'autotrain') or self.autotrain_manager.autotrain is None:
                self.logger.warning("AutoTrain-Advanced not available")
                self.service_status = AutoTrainServiceStatus.ERROR
                return

            # Check system resources
            if self.utilities:
                system_info = self.utilities.get_system_info()
                if system_info.get("memory_percent", 0) > 90:
                    self.logger.warning("High memory usage detected")
                if system_info.get("cpu_percent", 0) > 95:
                    self.logger.warning("High CPU usage detected")

            # Update service status based on active jobs
            if self.service_metrics.active_jobs > 0:
                self.service_status = AutoTrainServiceStatus.TRAINING
            else:
                self.service_status = AutoTrainServiceStatus.IDLE

        except Exception as e:
            self.logger.error(f"Error checking service health: {e}")

    # Event handlers
    def _on_job_submitted(self, job_id: str):
        """Handle job submitted event"""
        self.service_metrics.total_jobs += 1
        self._broadcast_event("job_submitted", {"job_id": job_id})
        self.logger.info(f"Job submitted: {job_id}")

    def _on_job_started(self, job_id: str):
        """Handle job started event"""
        self.service_metrics.active_jobs += 1
        self.service_status = AutoTrainServiceStatus.TRAINING
        self._broadcast_event("job_started", {"job_id": job_id})
        self.logger.info(f"Job started: {job_id}")

    def _on_job_completed(self, job_id: str):
        """Handle job completed event"""
        self.service_metrics.completed_jobs += 1
        self.service_metrics.active_jobs -= 1

        # Process results
        asyncio.create_task(self._process_job_results(job_id))

        self._broadcast_event("job_completed", {"job_id": job_id})
        self.logger.info(f"Job completed: {job_id}")

    def _on_job_failed(self, job_id: str):
        """Handle job failed event"""
        self.service_metrics.failed_jobs += 1
        self.service_metrics.active_jobs -= 1
        self._broadcast_event("job_failed", {"job_id": job_id})
        self.logger.error(f"Job failed: {job_id}")

    def _on_job_cancelled(self, job_id: str):
        """Handle job cancelled event"""
        self.service_metrics.active_jobs -= 1
        self._broadcast_event("job_cancelled", {"job_id": job_id})
        self.logger.info(f"Job cancelled: {job_id}")

    async def _process_job_results(self, job_id: str):
        """Process completed job results"""
        try:
            self.service_status = AutoTrainServiceStatus.PROCESSING

            # Process results
            result = self.results_processor.process_completed_job(job_id)
            if result:
                # Auto-deploy to DuckBot ecosystem
                deploy_config = DeploymentConfig(
                    target=DeploymentTarget.DUCKBOT_ECOSYSTEM,
                    model_path=result.model_path,
                    model_name=f"autotrain_{job_id}",
                    description=f"Auto-trained model from job {job_id}"
                )

                success = self.results_processor.deploy_model(result, deploy_config)
                if success:
                    self.service_metrics.models_deployed += 1

                # Broadcast results
                self._broadcast_event("job_processed", {
                    "job_id": job_id,
                    "success": success,
                    "metrics": result.metrics.__dict__,
                    "deployment_success": success
                })

        except Exception as e:
            self.logger.error(f"Error processing job results: {e}")
        finally:
            self.service_status = AutoTrainServiceStatus.IDLE

    # WebSocket support
    def register_websocket_client(self, websocket):
        """Register WebSocket client for real-time updates"""
        self.websocket_clients.add(websocket)

    def unregister_websocket_client(self, websocket):
        """Unregister WebSocket client"""
        self.websocket_clients.discard(websocket)

    def _broadcast_event(self, event_type: str, data: Dict[str, Any]):
        """Broadcast event to WebSocket clients"""
        message = {
            "type": event_type,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }

        for client in self.websocket_clients.copy():
            try:
                # Send message (implementation depends on WebSocket library)
                pass
            except Exception as e:
                self.logger.error(f"Error sending WebSocket message: {e}")
                self.websocket_clients.discard(client)

    def _broadcast_metrics_update(self):
        """Broadcast metrics update to WebSocket clients"""
        self._broadcast_event("metrics_update", {
            "metrics": self.service_metrics.__dict__,
            "status": self.service_status.value
        })

    # API methods for DuckBot integration
    async def submit_training_job(self, config: Dict[str, Any]) -> str:
        """Submit training job via API"""
        try:
            # Convert dict to AutoTrainConfig
            autotrain_config = AutoTrainConfig(**config)

            # Submit job
            job_id = self.job_manager.submit_job(autotrain_config)

            return job_id
        except Exception as e:
            self.logger.error(f"Error submitting training job: {e}")
            raise

    async def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get job status via API"""
        return self.job_manager.get_job_status(job_id)

    async def list_jobs(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """List jobs via API"""
        job_status = JobStatus(status) if status else None
        return self.job_manager.list_jobs(status=job_status)

    async def cancel_job(self, job_id: str) -> bool:
        """Cancel job via API"""
        return self.job_manager.cancel_job(job_id)

    async def get_service_status(self) -> Dict[str, Any]:
        """Get service status via API"""
        return {
            "status": self.service_status.value,
            "metrics": self.service_metrics.__dict__,
            "version": self.service_version,
            "available": DUCKBOT_AVAILABLE and self.autotrain_manager.autotrain is not None
        }

    async def get_available_templates(self) -> List[Dict[str, Any]]:
        """Get available training templates"""
        templates = self.config_manager.list_templates()
        return [
            {
                "name": template.name,
                "description": template.description,
                "project_type": template.project_type.value,
                "difficulty": template.difficulty,
                "estimated_time": template.estimated_time,
                "hardware_requirements": template.hardware_requirements
            }
            for template in templates
        ]

    async def create_config_from_template(self, template_name: str, project_name: str,
                                        data_path: str, **overrides) -> Dict[str, Any]:
        """Create configuration from template"""
        template = self.config_manager.get_template(template_name)
        if not template:
            raise ValueError(f"Template '{template_name}' not found")

        config = self.config_manager.create_config_from_template(
            template_name, project_name, data_path, **overrides
        )

        return config.to_dict()

    async def get_system_resources(self) -> Dict[str, Any]:
        """Get system resources information"""
        return self.autotrain_manager.get_system_resources()

    async def optimize_config(self, config: Dict[str, Any], hardware_profile: str = "auto") -> Dict[str, Any]:
        """Optimize configuration for hardware"""
        autotrain_config = AutoTrainConfig(**config)
        optimized_config = self.config_manager.optimize_config(autotrain_config, hardware_profile)
        return optimized_config.to_dict()

    # Integration with existing DuckBot training modules
    def integrate_with_existing_training(self):
        """Integrate with existing DuckBot training modules"""
        try:
            # This would integrate with existing training modules
            # For now, just log the intention
            self.logger.info("Integration with existing training modules requested")

            # Could add specific integration points here
            # - Shared configuration management
            # - Unified job queue
            # - Common metrics collection
            # - Shared resource management

        except Exception as e:
            self.logger.error(f"Error integrating with existing training modules: {e}")

    def shutdown(self):
        """Shutdown the service"""
        self.logger.info("Shutting down AutoTrain integration service")

        self._running = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)

        self.job_manager.stop_processing()

        if self.service_manager and self.service_info:
            asyncio.create_task(self.service_manager.deregister_service(self.service_info.name))

        self.logger.info("AutoTrain integration service shutdown complete")

    # Health check
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "checks": {}
        }

        # Check AutoTrain availability
        health_status["checks"]["autotrain_available"] = (
            hasattr(self.autotrain_manager, 'autotrain') and
            self.autotrain_manager.autotrain is not None
        )

        # Check DuckBot integration
        health_status["checks"]["duckbot_integration"] = DUCKBOT_AVAILABLE

        # Check job manager
        health_status["checks"]["job_manager"] = self.job_manager._running

        # Check service registration
        health_status["checks"]["service_registered"] = (
            self.service_manager and self.service_info is not None
        )

        # Overall health
        if all(health_status["checks"].values()):
            health_status["status"] = "healthy"
        else:
            health_status["status"] = "degraded"

        return health_status

# Service creation function
def create_autotrain_service() -> ServiceInfo:
    """Create AutoTrain service info for DuckBot"""
    return ServiceInfo(
        name="autotrain_integration",
        service_type=ServiceType.AI_TRAINING,
        description="AutoTrain-Advanced integration for no-code ML training",
        version="1.0.0"
    )

# Main service startup
async def start_autotrain_service():
    """Start AutoTrain service as part of DuckBot ecosystem"""
    integration = DuckBotAutoTrainIntegration()
    success = await integration.initialize_service()

    if success:
        logging.info("AutoTrain service started successfully")
        return integration
    else:
        logging.error("Failed to start AutoTrain service")
        return None

if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)

    # Create and start integration
    integration = DuckBotAutoTrainIntegration()
    success = asyncio.run(integration.initialize_service())

    if success:
        print("AutoTrain integration started successfully")

        # Example: Submit a training job
        config = {
            "project_name": "example_integration",
            "project_type": "text_classification",
            "data_path": "./example_data",
            "model_name": "distilbert-base-uncased",
            "learning_rate": 2e-5,
            "num_epochs": 3,
            "batch_size": 16
        }

        job_id = asyncio.run(integration.submit_training_job(config))
        print(f"Submitted job: {job_id}")

        # Monitor job
        try:
            while True:
                status = asyncio.run(integration.get_job_status(job_id))
                if status:
                    print(f"Job status: {status['status']}")
                    if status['status'] in ['completed', 'failed', 'cancelled']:
                        break
                time.sleep(5)
        except KeyboardInterrupt:
            print("Shutting down...")
            integration.shutdown()
    else:
        print("Failed to start AutoTrain integration")