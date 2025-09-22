#!/usr/bin/env python3
"""
Unified Services Startup Script for DuckBot Enhanced v4.2
Starts ComfyUI, TRELLIS, and VibeVoice integrations with unified management
"""

import asyncio
import logging
import os
import sys
import signal
import time
from typing import Dict, Any, Optional
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import unified services
from duckbot.integrations.unified_service_manager import initialize_unified_services, get_unified_status
from duckbot.integrations.unified_webui_integration import integrate_with_webui
from duckbot.enhanced_webui import app
from duckbot.core.logging_setup import setup_logging

# Configure logging
logger = logging.getLogger(__name__)

class UnifiedServicesLauncher:
    """Launcher for unified services"""

    def __init__(self):
        self.config_path = os.path.join(project_root, "config", "unified_services_config.json")
        self.shutdown_event = asyncio.Event()
        self.startup_complete = False

    async def startup(self):
        """Start all unified services"""
        try:
            print("🚀 Starting DuckBot Unified Services...")
            print("=" * 60)

            # Initialize logging
            setup_logging()
            logger.info("Initializing unified services...")

            # Initialize unified services
            print("📦 Initializing service managers...")
            initialization_results = await initialize_unified_services(self.config_path)

            # Report initialization results
            print("\n📊 Service Initialization Results:")
            for service, success in initialization_results.items():
                status = "✅ Online" if success else "❌ Offline"
                print(f"   {service.upper()}: {status}")

            # Integrate with WebUI
            print("\n🌐 Integrating with WebUI...")
            integrate_with_webui(app)

            # Get unified status
            print("\n🔍 Checking service health...")
            status = await get_unified_status()
            self._print_status_summary(status)

            self.startup_complete = True
            print("\n🎉 Unified services startup complete!")

            # Print access information
            self._print_access_info()

        except Exception as e:
            logger.error(f"Startup failed: {e}")
            print(f"\n❌ Startup failed: {e}")
            self.startup_complete = False

    def _print_status_summary(self, status: Dict[str, Any]):
        """Print service status summary"""
        services = status.get("services", {})

        print("\n📈 Service Status Summary:")
        for service_name, service_info in services.items():
            status_icon = "🟢" if service_info.get("healthy") else "🔴"
            initialized = "✅" if service_info.get("initialized") else "❌"
            print(f"   {status_icon} {service_name.upper()}: {initialized} | "
                  f"Healthy: {service_info.get('healthy', False)}")

        # Performance metrics
        perf = status.get("performance", {})
        if perf.get("total_requests", 0) > 0:
            success_rate = (perf.get("successful_requests", 0) / perf.get("total_requests", 1)) * 100
            print(f"\n📊 Performance: {success_rate:.1f}% success rate | "
                  f"Avg response: {perf.get('average_response_time', 0):.1f}s")

    def _print_access_info(self):
        """Print access information"""
        print("\n" + "=" * 60)
        print("🌐 ACCESS INFORMATION")
        print("=" * 60)
        print("📱 WebUI Dashboard: http://localhost:8787")
        print("🔗 Unified Services API: http://localhost:8787/api/unified")
        print("📊 Unified Dashboard: http://localhost:8787/api/unified/dashboard")
        print("\n🛠️  Service Endpoints:")
        print("   • ComfyUI: http://localhost:8188")
        print("   • TRELLIS: http://localhost:8288")
        print("   • VibeVoice: http://localhost:8000")
        print("\n📚 API Documentation:")
        print("   • FastAPI Docs: http://localhost:8787/docs")
        print("   • ReDoc: http://localhost:8787/redoc")
        print("\n💡 Usage Examples:")
        print("   • Generate images: POST /api/unified/comfyui/execute")
        print("   • Create 3D assets: POST /api/unified/trellis/generate")
        print("   • Generate speech: POST /api/unified/vibevoice/generate")
        print("   • Multimodal workflows: POST /api/unified/multimodal-workflow")
        print("=" * 60)

    async def run_foreground(self):
        """Run services in foreground mode"""
        if not self.startup_complete:
            logger.error("Cannot run services - startup incomplete")
            return

        try:
            print("\n🏃 Running services in foreground mode...")
            print("Press Ctrl+C to shutdown gracefully")

            # Setup signal handlers
            def signal_handler(signum, frame):
                print(f"\n🛑 Received signal {signum}, shutting down...")
                self.shutdown_event.set()

            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)

            # Main loop
            while not self.shutdown_event.is_set():
                try:
                    # Periodic status check
                    await asyncio.sleep(30)
                    if self.shutdown_event.is_set():
                        break

                    # Get and log status
                    status = await get_unified_status()
                    # Could add periodic status logging here

                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Error in main loop: {e}")
                    await asyncio.sleep(5)

        except KeyboardInterrupt:
            print("\n🛑 Keyboard interrupt received")
        finally:
            await self.shutdown()

    async def run_background(self):
        """Run services in background mode"""
        if not self.startup_complete:
            logger.error("Cannot run services - startup incomplete")
            return

        try:
            print("\n🌙 Running services in background mode...")
            print("Use the WebUI dashboard to monitor and control services")

            # Start WebUI in background
            import uvicorn
            config = uvicorn.Config(
                app=app,
                host="127.0.0.1",
                port=8787,
                log_level="info",
                access_log=False
            )
            server = uvicorn.Server(config)

            # Run server until shutdown
            await server.serve()

        except Exception as e:
            logger.error(f"Error running background services: {e}")
        finally:
            await self.shutdown()

    async def shutdown(self):
        """Graceful shutdown"""
        print("\n🔄 Shutting down unified services...")

        try:
            # Shutdown unified service manager
            from duckbot.integrations.unified_service_manager import unified_service_manager
            await unified_service_manager.cleanup()

            print("✅ Services shut down successfully")

        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
            print(f"❌ Shutdown error: {e}")

        print("👋 DuckBot Unified Services stopped")


async def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="DuckBot Unified Services Launcher")
    parser.add_argument(
        "--mode",
        choices=["foreground", "background"],
        default="background",
        help="Run mode: foreground (console) or background (WebUI)"
    )
    parser.add_argument(
        "--config",
        help="Path to configuration file"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8787,
        help="WebUI port (default: 8787)"
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="WebUI host (default: 127.0.0.1)"
    )

    args = parser.parse_args()

    # Create launcher
    launcher = UnifiedServicesLauncher()
    if args.config:
        launcher.config_path = args.config

    # Update app host/port
    app.state.host = args.host
    app.state.port = args.port

    # Startup sequence
    await launcher.startup()

    if not launcher.startup_complete:
        print("❌ Failed to start services")
        return 1

    # Run in specified mode
    try:
        if args.mode == "foreground":
            await launcher.run_foreground()
        else:
            await launcher.run_background()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        return 1

    return 0


def entry_point():
    """Entry point for script execution"""
    try:
        return asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Interrupted by user")
        return 0
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        return 1


if __name__ == "__main__":
    exit_code = entry_point()
    sys.exit(exit_code)