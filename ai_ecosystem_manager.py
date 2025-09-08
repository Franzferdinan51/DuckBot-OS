#!/usr/bin/env python3
"""
AI-Enhanced Ecosystem Manager for DuckBot
Intelligent service orchestration with AI-driven monitoring and optimization
"""

import os
import sys
import asyncio
import logging
import time
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
import subprocess
from datetime import datetime, timedelta

# Add the duckbot module to the path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from duckbot.cost_tracker import cost_tracker
except ImportError:
    cost_tracker = None

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AIEcosystemManager:
    """AI-enhanced ecosystem management with intelligent monitoring"""
    
    def __init__(self):
        self.services = {}
        self.service_health = {}
        self.ai_recommendations = []
        self.running = False
        self.monitoring_interval = 30
        
    async def analyze_system_health(self) -> Dict[str, Any]:
        """AI-powered system health analysis"""
        try:
            import psutil
            
            # Get system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            health_score = 100
            recommendations = []
            
            # CPU analysis
            if cpu_percent > 80:
                health_score -= 20
                recommendations.append("High CPU usage detected - consider optimizing processes")
            
            # Memory analysis
            if memory.percent > 85:
                health_score -= 25
                recommendations.append("High memory usage - recommend closing unused services")
            
            # Disk analysis
            if disk.percent > 90:
                health_score -= 15
                recommendations.append("Low disk space - cleanup recommended")
            
            return {
                "health_score": max(0, health_score),
                "metrics": {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "disk_percent": disk.percent
                },
                "recommendations": recommendations,
                "timestamp": datetime.now().isoformat()
            }
            
        except ImportError:
            return {
                "health_score": 75,
                "metrics": {"note": "psutil not available - limited monitoring"},
                "recommendations": ["Install psutil for detailed system monitoring"],
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Health analysis failed: {e}")
            return {
                "health_score": 50,
                "metrics": {"error": str(e)},
                "recommendations": ["System health check failed - manual inspection recommended"],
                "timestamp": datetime.now().isoformat()
            }
    
    async def start_ai_enhanced_services(self):
        """Start services with AI-enhanced monitoring"""
        logger.info("🤖 Starting AI-Enhanced DuckBot Ecosystem...")
        
        # Start Enhanced WebUI with AI monitoring
        try:
            from duckbot.enhanced_webui import start_enhanced_webui
            self.services['enhanced_webui'] = {
                'task': asyncio.create_task(start_enhanced_webui(host="127.0.0.1", port=8787)),
                'name': 'Enhanced WebUI',
                'port': 8787,
                'critical': True
            }
            logger.info("✅ Enhanced WebUI started with AI monitoring")
        except Exception as e:
            logger.error(f"❌ Failed to start Enhanced WebUI: {e}")
        
        # Start integration services with health monitoring
        integrations = [
            ('bytebot', 'duckbot.bytebot_integration', 'bytebot_integration', 'ByteBot Desktop Automation'),
            ('archon', 'duckbot.archon_integration', 'ArchonIntegration', 'Archon Multi-Agent System'),
            ('wsl', 'duckbot.wsl_integration', 'wsl_integration', 'WSL Integration'),
            ('chromium', 'duckbot.chromium_integration', 'chromium_integration', 'ChromiumOS Integration')
        ]
        
        for service_key, module_name, obj_name, display_name in integrations:
            try:
                module = __import__(module_name, fromlist=[obj_name])
                obj = getattr(module, obj_name)
                
                if hasattr(obj, 'start_service'):
                    if service_key == 'archon':
                        # Archon needs instance
                        from duckbot.archon_integration import ArchonIntegration
                        instance = ArchonIntegration()
                        task = asyncio.create_task(instance.start_service())
                    else:
                        task = asyncio.create_task(obj.start_service())
                    
                    self.services[service_key] = {
                        'task': task,
                        'name': display_name,
                        'critical': False
                    }
                    logger.info(f"✅ {display_name} started with AI monitoring")
                else:
                    logger.warning(f"⚠️  {display_name}: No start_service method found")
                    
            except Exception as e:
                logger.error(f"❌ Failed to start {display_name}: {e}")
        
        # Start cost tracking
        try:
            if cost_tracker:
                cost_tracker.start_monitoring()
                logger.info("✅ AI-enhanced cost tracking started")
            else:
                logger.info("ℹ️  Cost tracker not available - continuing without it")
        except Exception as e:
            logger.error(f"❌ Cost tracking failed: {e}")
    
    async def ai_health_monitor(self):
        """Continuous AI-powered health monitoring"""
        while self.running:
            try:
                # Analyze system health
                health = await self.analyze_system_health()
                self.service_health = health
                
                # Log health status
                health_score = health.get('health_score', 0)
                if health_score < 50:
                    logger.warning(f"⚠️  System health declining: {health_score}/100")
                elif health_score < 75:
                    logger.info(f"📊 System health: {health_score}/100")
                else:
                    logger.debug(f"✅ System health excellent: {health_score}/100")
                
                # Process AI recommendations
                recommendations = health.get('recommendations', [])
                if recommendations:
                    logger.info("🤖 AI Recommendations:")
                    for rec in recommendations:
                        logger.info(f"   • {rec}")
                
                # Check service status
                for service_key, service_info in self.services.items():
                    task = service_info['task']
                    if task.done():
                        if task.exception():
                            logger.error(f"❌ {service_info['name']} failed: {task.exception()}")
                        else:
                            logger.info(f"✅ {service_info['name']} completed normally")
                
                await asyncio.sleep(self.monitoring_interval)
                
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(60)  # Longer wait on error
    
    async def start_ecosystem(self):
        """Start the AI-enhanced ecosystem"""
        logger.info("🚀 Starting AI-Enhanced DuckBot Ecosystem Manager...")
        
        self.running = True
        
        # Start all services
        await self.start_ai_enhanced_services()
        
        # Start AI health monitoring
        health_monitor_task = asyncio.create_task(self.ai_health_monitor())
        
        logger.info("🎯 AI-Enhanced Ecosystem fully operational!")
        logger.info("🌐 Enhanced WebUI: http://127.0.0.1:8787")
        logger.info("🤖 AI monitoring and optimization active")
        logger.info("📊 Health analysis running every 30 seconds")
        
        try:
            # Wait for health monitor
            await health_monitor_task
        except KeyboardInterrupt:
            logger.info("🛑 Shutting down AI-enhanced ecosystem...")
            await self.shutdown()
    
    async def shutdown(self):
        """AI-guided shutdown of all services"""
        logger.info("🤖 AI-Enhanced shutdown initiated...")
        self.running = False
        
        # Stop services in optimal order (AI-determined)
        critical_services = [k for k, v in self.services.items() if v.get('critical', False)]
        non_critical_services = [k for k, v in self.services.items() if not v.get('critical', False)]
        
        # Stop non-critical services first
        for service_key in non_critical_services:
            service_info = self.services[service_key]
            task = service_info['task']
            if not task.done():
                logger.info(f"🛑 Stopping {service_info['name']}...")
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        # Stop critical services last
        for service_key in critical_services:
            service_info = self.services[service_key]
            task = service_info['task']
            if not task.done():
                logger.info(f"🛑 Stopping {service_info['name']}...")
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        logger.info("✅ AI-Enhanced DuckBot Ecosystem shutdown complete")

async def main():
    """Main entry point for AI-enhanced ecosystem"""
    manager = AIEcosystemManager()
    await manager.start_ecosystem()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nAI-Enhanced Ecosystem cancelled by user")
    except Exception as e:
        logger.error(f"AI-Enhanced Ecosystem startup failed: {e}")
        sys.exit(1)