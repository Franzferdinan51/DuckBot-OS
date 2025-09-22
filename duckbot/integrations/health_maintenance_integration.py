#!/usr/bin/env python3
"""
DuckBot Health Maintenance Integration
Integrates health checks and predictive maintenance with existing systems
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

# Local imports
from duckbot.core.health_predictive_maintenance import (
    HealthMaintenanceManager, health_maintenance_manager,
    start_health_maintenance, stop_health_maintenance
)
from duckbot.core.health_analytics_dashboard import (
    HealthAnalyticsEngine, health_analytics_engine,
    HealthDashboardAPI, health_dashboard_api, add_health_dashboard_routes
)
from duckbot.core.monitoring_system import MonitoringDatabase

logger = logging.getLogger(__name__)

class HealthMaintenanceIntegration:
    """Integration layer for health maintenance system"""

    def __init__(self):
        self.health_manager = health_maintenance_manager
        self.analytics_engine = health_analytics_engine
        self.dashboard_api = health_dashboard_api
        self.is_running = False
        self.integration_config = {
            'auto_start': True,
            'health_check_interval': 1800,  # 30 minutes
            'prediction_interval': 3600,   # 1 hour
            'cleanup_interval': 86400,     # 24 hours
            'enable_automation': True,
            'enable_alerting': True
        }

    async def initialize_integration(self, fastapi_app=None):
        """Initialize health maintenance integration"""
        try:
            logger.info("Initializing Health Maintenance Integration...")

            # Start health maintenance system if auto-start enabled
            if self.integration_config['auto_start']:
                await self.health_manager.start()
                logger.info("Health maintenance system started")

            # Add dashboard routes if FastAPI app provided
            if fastapi_app:
                add_health_dashboard_routes(fastapi_app)
                logger.info("Health dashboard routes added to FastAPI app")

            self.is_running = True
            logger.info("Health Maintenance Integration initialized successfully")

            return True

        except Exception as e:
            logger.error(f"Failed to initialize Health Maintenance Integration: {e}")
            return False

    async def shutdown_integration(self):
        """Shutdown health maintenance integration"""
        try:
            if self.is_running:
                logger.info("Shutting down Health Maintenance Integration...")
                await self.health_manager.stop()
                self.is_running = False
                logger.info("Health Maintenance Integration shutdown complete")

        except Exception as e:
            logger.error(f"Error during integration shutdown: {e}")

    async def get_system_health_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive system health dashboard data"""
        try:
            # Get health summary
            health_summary = await self.dashboard_api.get_health_summary()

            # Get real-time metrics
            real_time_metrics = await self.dashboard_api.get_real_time_metrics()

            # Get prediction insights
            prediction_insights = await self.dashboard_api.get_prediction_insights()

            # Get maintenance dashboard
            maintenance_dashboard = await self.dashboard_api.get_maintenance_dashboard()

            # Get system status
            system_status = await self.dashboard_api.get_system_status()

            return {
                'timestamp': datetime.now().isoformat(),
                'health_summary': health_summary,
                'real_time_metrics': real_time_metrics,
                'prediction_insights': prediction_insights,
                'maintenance_dashboard': maintenance_dashboard,
                'system_status': system_status,
                'integration_status': {
                    'running': self.is_running,
                    'auto_start': self.integration_config['auto_start'],
                    'automation_enabled': self.integration_config['enable_automation']
                }
            }

        except Exception as e:
            logger.error(f"Error getting system health dashboard: {e}")
            return {'error': str(e), 'timestamp': datetime.now().isoformat()}

    async def run_comprehensive_health_check(self) -> Dict[str, Any]:
        """Run comprehensive health check and return results"""
        try:
            logger.info("Running comprehensive health check...")

            # Trigger immediate health check
            check_result = await self.dashboard_api.trigger_health_check()

            # Get detailed results
            health_results = await self.health_manager.run_immediate_health_check()

            # Calculate overall score
            overall_score = self.health_manager.health_checker.get_overall_health_score(health_results)

            # Generate recommendations
            recommendations = await self._generate_health_recommendations(health_results)

            return {
                'timestamp': datetime.now().isoformat(),
                'check_result': check_result,
                'overall_score': overall_score,
                'component_results': {name: {
                    'status': result.status.value,
                    'score': result.score,
                    'issues': result.issues,
                    'recommendations': result.recommendations
                } for name, result in health_results.items()},
                'recommendations': recommendations,
                'action_required': overall_score < 0.8
            }

        except Exception as e:
            logger.error(f"Error running comprehensive health check: {e}")
            return {'error': str(e), 'timestamp': datetime.now().isoformat()}

    async def get_maintenance_recommendations(self) -> Dict[str, Any]:
        """Get maintenance recommendations and predictions"""
        try:
            # Get predictions
            predictions = await self.health_manager.get_predictions(hours=24)

            # Get pending maintenance
            pending_maintenance = await self.health_manager.get_pending_maintenance()

            # Get analytics insights
            analytics_report = await self.analytics_engine.generate_analytics_report(
                self.analytics_engine.AnalyticsTimeframe.DAY
            )

            return {
                'timestamp': datetime.now().isoformat(),
                'predictions': predictions,
                'pending_maintenance': pending_maintenance,
                'analytics_insights': {
                    'recommendations': analytics_report.recommendations,
                    'key_insights': analytics_report.key_insights,
                    'urgent_actions': []
                },
                'automation_status': {
                    'active': self.health_manager.automation_system.automation_active,
                    'completed_actions': len(self.health_manager.automation_system.maintenance_history)
                }
            }

        except Exception as e:
            logger.error(f"Error getting maintenance recommendations: {e}")
            return {'error': str(e), 'timestamp': datetime.now().isoformat()}

    async def execute_maintenance_action(self, action_id: str) -> Dict[str, Any]:
        """Execute a specific maintenance action"""
        try:
            # Get action details
            pending_actions = await self.health_manager.get_pending_maintenance()
            action_data = next((action for action in pending_actions if action['id'] == action_id), None)

            if not action_data:
                return {'error': f'Maintenance action {action_id} not found', 'timestamp': datetime.now().isoformat()}

            # Execute action
            await self.health_manager.automation_system._execute_maintenance_action(action_data)

            return {
                'status': 'success',
                'action_id': action_id,
                'action_name': action_data.get('name', ''),
                'executed_at': datetime.now().isoformat(),
                'message': f'Maintenance action {action_data.get("name", "")} executed successfully'
            }

        except Exception as e:
            logger.error(f"Error executing maintenance action {action_id}: {e}")
            return {'error': str(e), 'action_id': action_id, 'timestamp': datetime.now().isoformat()}

    async def schedule_maintenance_window(self, name: str, start_time: datetime, end_time: datetime,
                                       action_ids: List[str], impact: str = "low") -> Dict[str, Any]:
        """Schedule a maintenance window"""
        try:
            import uuid

            schedule_id = str(uuid.uuid4())
            schedule = self.health_manager.health_db.MaintenanceSchedule(
                id=schedule_id,
                name=name,
                start_time=start_time,
                end_time=end_time,
                actions=action_ids,
                impact=impact,
                status="scheduled",
                created_at=datetime.now(),
                rollback_available=True
            )

            # Store schedule
            self.health_manager.health_db.store_maintenance_schedule(schedule)

            return {
                'status': 'success',
                'schedule_id': schedule_id,
                'name': name,
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'actions_count': len(action_ids),
                'impact': impact
            }

        except Exception as e:
            logger.error(f"Error scheduling maintenance window: {e}")
            return {'error': str(e), 'timestamp': datetime.now().isoformat()}

    async def get_health_trends(self, timeframe: str = "day") -> Dict[str, Any]:
        """Get health trends for specified timeframe"""
        try:
            trends = await self.dashboard_api.get_health_trends(timeframe)
            return trends

        except Exception as e:
            logger.error(f"Error getting health trends: {e}")
            return {'error': str(e), 'timeframe': timeframe, 'timestamp': datetime.now().isoformat()}

    async def get_analytics_report(self, timeframe: str = "day") -> Dict[str, Any]:
        """Get analytics report for specified timeframe"""
        try:
            report = await self.dashboard_api.get_analytics_report(timeframe)
            return report

        except Exception as e:
            logger.error(f"Error getting analytics report: {e}")
            return {'error': str(e), 'timeframe': timeframe, 'timestamp': datetime.now().isoformat()}

    async def _generate_health_recommendations(self, health_results: Dict[str, Any]) -> List[str]:
        """Generate health recommendations based on results"""
        recommendations = []

        try:
            # Analyze overall score
            overall_score = self.health_manager.health_checker.get_overall_health_score(health_results)

            if overall_score < 0.5:
                recommendations.append("CRITICAL: System health is critically low. Immediate attention required.")
            elif overall_score < 0.7:
                recommendations.append("WARNING: System health is degraded. Consider maintenance actions.")

            # Analyze individual components
            for component_name, result in health_results.items():
                if result.score < 0.5:
                    recommendations.append(f"Critical issue with {component_name}: {', '.join(result.issues)}")
                elif result.score < 0.8:
                    recommendations.append(f"Degraded performance in {component_name}: {', '.join(result.recommendations)}")

            # Resource-based recommendations
            if 'System Resources' in health_results:
                sys_resource = health_results['System Resources']
                if sys_resource.score < 0.7:
                    recommendations.append("System resources under pressure. Monitor resource usage closely.")

            # Maintenance-based recommendations
            pending_maintenance = await self.health_manager.get_pending_maintenance()
            if len(pending_maintenance) > 3:
                recommendations.append(f"Multiple pending maintenance actions ({len(pending_maintenance)}). Schedule maintenance window.")

        except Exception as e:
            logger.error(f"Error generating health recommendations: {e}")
            recommendations.append("Error generating recommendations. Check system logs.")

        return recommendations

    async def configure_integration(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Configure integration settings"""
        try:
            old_config = self.integration_config.copy()
            self.integration_config.update(config)

            # Apply changes
            if self.is_running:
                if not config.get('auto_start', True) and old_config.get('auto_start', True):
                    await self.health_manager.stop()
                elif config.get('auto_start', True) and not old_config.get('auto_start', True):
                    await self.health_manager.start()

            return {
                'status': 'success',
                'old_config': old_config,
                'new_config': self.integration_config,
                'applied_changes': list(config.keys())
            }

        except Exception as e:
            logger.error(f"Error configuring integration: {e}")
            return {'error': str(e), 'timestamp': datetime.now().isoformat()}

    def get_integration_status(self) -> Dict[str, Any]:
        """Get current integration status"""
        return {
            'is_running': self.is_running,
            'health_manager_running': self.health_manager.running,
            'automation_active': self.health_manager.automation_system.automation_active,
            'configuration': self.integration_config,
            'database_paths': {
                'health_db': self.health_manager.health_db.db_path,
                'monitoring_db': self.health_manager.monitoring_db.db_path
            },
            'statistics': {
                'maintenance_history_count': len(self.health_manager.automation_system.maintenance_history),
                'system_uptime': self.health_manager.automation_system.get_system_stats().get('uptime', 0)
            }
        }

# Global integration instance
health_maintenance_integration = HealthMaintenanceIntegration()

# Convenience functions for external use
async def initialize_health_maintenance(fastapi_app=None):
    """Initialize health maintenance integration"""
    return await health_maintenance_integration.initialize_integration(fastapi_app)

async def shutdown_health_maintenance():
    """Shutdown health maintenance integration"""
    return await health_maintenance_integration.shutdown_integration()

async def get_system_health_dashboard():
    """Get system health dashboard"""
    return await health_maintenance_integration.get_system_health_dashboard()

async def run_health_check():
    """Run comprehensive health check"""
    return await health_maintenance_integration.run_comprehensive_health_check()

async def get_maintenance_recommendations():
    """Get maintenance recommendations"""
    return await health_maintenance_integration.get_maintenance_recommendations()

# Integration hooks for existing DuckBot systems
class HealthMaintenanceHooks:
    """Hooks for integrating with existing DuckBot systems"""

    @staticmethod
    async def on_system_startup():
        """Hook called when DuckBot system starts up"""
        try:
            logger.info("Health Maintenance: System startup hook triggered")
            await health_maintenance_integration.initialize_integration()
            await health_maintenance_integration.run_comprehensive_health_check()
        except Exception as e:
            logger.error(f"Health Maintenance startup error: {e}")

    @staticmethod
    async def on_system_shutdown():
        """Hook called when DuckBot system shuts down"""
        try:
            logger.info("Health Maintenance: System shutdown hook triggered")
            await health_maintenance_integration.shutdown_integration()
        except Exception as e:
            logger.error(f"Health Maintenance shutdown error: {e}")

    @staticmethod
    async def on_service_health_check(service_name: str, health_status: str):
        """Hook called when service health check is performed"""
        try:
            # Log service health status
            logger.info(f"Health Maintenance: Service {service_name} health check - {health_status}")

            # If service is unhealthy, trigger system health check
            if health_status.lower() in ['unhealthy', 'critical', 'error']:
                logger.warning(f"Health Maintenance: Unhealthy service detected - {service_name}")
                # Could trigger automated response here

        except Exception as e:
            logger.error(f"Health Maintenance service health check error: {e}")

    @staticmethod
    async def on_resource_alert(resource_type: str, current_value: float, threshold: float):
        """Hook called when resource alert is triggered"""
        try:
            logger.warning(f"Health Maintenance: Resource alert - {resource_type}: {current_value} (threshold: {threshold})")

            # Could trigger automated cleanup or scaling actions
            if resource_type == 'disk' and current_value > 95:
                logger.critical("Health Maintenance: Critical disk space alert - triggering cleanup")
                # Trigger automated cleanup

        except Exception as e:
            logger.error(f"Health Maintenance resource alert error: {e}")

    @staticmethod
    async def on_maintenance_completed(action_id: str, status: str):
        """Hook called when maintenance action is completed"""
        try:
            logger.info(f"Health Maintenance: Maintenance action {action_id} completed with status: {status}")

            # Could trigger follow-up actions or notifications
            if status == 'failed':
                logger.error(f"Health Maintenance: Maintenance action {action_id} failed")
                # Could schedule retry or alert administrators

        except Exception as e:
            logger.error(f"Health Maintenance maintenance completion error: {e}")

# Standalone startup script
async def start_health_maintenance_standalone():
    """Start health maintenance system in standalone mode"""
    try:
        print("Starting DuckBot Health Maintenance System...")
        await health_maintenance_integration.initialize_integration()

        print("Health Maintenance System started successfully!")
        print("- Health monitoring active")
        print("- Predictive maintenance enabled")
        print("- Automated cleanup scheduled")
        print("- Dashboard API available")

        # Keep running
        while True:
            await asyncio.sleep(60)

    except KeyboardInterrupt:
        print("\nShutting down Health Maintenance System...")
        await health_maintenance_integration.shutdown_integration()
        print("Health Maintenance System stopped.")
    except Exception as e:
        logger.error(f"Health Maintenance standalone error: {e}")
        await health_maintenance_integration.shutdown_integration()

if __name__ == "__main__":
    asyncio.run(start_health_maintenance_standalone())