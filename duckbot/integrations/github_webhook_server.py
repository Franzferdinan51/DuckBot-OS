"""
GitHub Webhook Server for DuckBot Workflow Automation

This module provides a Flask-based webhook server for handling GitHub webhook events
and triggering the appropriate workflow automation tasks.

Usage:
    python -m duckbot.integrations.github_webhook_server
"""

import asyncio
import json
import logging
import os
import hmac
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional

from flask import Flask, request, jsonify
from werkzeug.serving import WSGIRequestHandler

from .github_workflows import (
    create_github_workflow_manager,
    WorkflowConfig,
    WorkflowType
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GitHubWebhookServer:
    """GitHub webhook server"""

    def __init__(self, config: WorkflowConfig):
        self.config = config
        self.app = Flask(__name__)
        self.workflow_manager = None
        self.setup_routes()

    def setup_routes(self):
        """Setup Flask routes"""

        @self.app.route("/", methods=["GET"])
        def health_check():
            """Health check endpoint"""
            return jsonify({
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "service": "DuckBot GitHub Webhook Server"
            })

        @self.app.route("/webhook/github", methods=["POST"])
        def handle_github_webhook():
            """Handle GitHub webhook events"""
            try:
                # Verify signature if secret is configured
                if self.config.webhook_secret:
                    if not self.verify_signature(request):
                        return jsonify({"error": "Invalid signature"}), 401

                # Parse event
                event_type = request.headers.get("X-GitHub-Event", "")
                delivery_id = request.headers.get("X-GitHub-Delivery", "")
                signature = request.headers.get("X-Hub-Signature-256", "")

                if not event_type:
                    return jsonify({"error": "Missing X-GitHub-Event header"}), 400

                # Get payload
                if request.is_json:
                    payload = request.get_json()
                else:
                    payload = json.loads(request.data.decode("utf-8"))

                logger.info(f"Received {event_type} event (delivery: {delivery_id})")

                # Handle webhook asynchronously
                asyncio.create_task(self.handle_webhook_async(event_type, payload))

                return jsonify({"status": "accepted"}), 202

            except Exception as e:
                logger.error(f"Error handling webhook: {e}")
                return jsonify({"error": str(e)}), 500

        @self.app.route("/webhook/test", methods=["POST"])
        def handle_test_webhook():
            """Handle test webhook events"""
            try:
                payload = request.get_json()
                logger.info(f"Test webhook received: {payload}")

                # Test event handling
                test_event = {
                    "event_type": "test",
                    "repository": {"name": "Test", "full_name": "test/test"},
                    "action": "test",
                    "payload": payload
                }

                if self.workflow_manager:
                    asyncio.create_task(self.test_workflow_manager())

                return jsonify({"status": "test accepted"}), 200

            except Exception as e:
                logger.error(f"Error handling test webhook: {e}")
                return jsonify({"error": str(e)}), 500

        @self.app.route("/status", methods=["GET"])
        def get_status():
            """Get server and workflow status"""
            status = {
                "server": {
                    "status": "running",
                    "timestamp": datetime.now().isoformat(),
                    "uptime": "N/A"
                },
                "workflow_manager": {
                    "initialized": self.workflow_manager is not None
                }
            }

            if self.workflow_manager:
                workflow_status = asyncio.run(self.workflow_manager.get_workflow_status())
                status["workflow_manager"].update(workflow_status)

            return jsonify(status)

        @self.app.route("/workflows/execute/<workflow_type>", methods=["POST"])
        async def execute_workflow(workflow_type):
            """Execute a specific workflow"""
            try:
                # Parse workflow type
                try:
                    workflow_enum = WorkflowType(workflow_type)
                except ValueError:
                    return jsonify({"error": f"Invalid workflow type: {workflow_type}"}), 400

                # Get parameters from request
                params = request.get_json() or {}

                # Execute workflow
                if not self.workflow_manager:
                    return jsonify({"error": "Workflow manager not initialized"}), 500

                result = await self.workflow_manager.execute_workflow(workflow_enum, **params)

                return jsonify({
                    "workflow_type": workflow_type,
                    "success": result.success,
                    "message": result.message,
                    "execution_time": result.execution_time,
                    "cost_estimate": result.cost_estimate,
                    "data": result.data
                })

            except Exception as e:
                logger.error(f"Error executing workflow: {e}")
                return jsonify({"error": str(e)}), 500

        @self.app.route("/workflows/templates/<workflow_type>", methods=["GET"])
        async def get_workflow_template(workflow_type):
            """Get workflow template"""
            try:
                # Parse workflow type
                try:
                    workflow_enum = WorkflowType(workflow_type)
                except ValueError:
                    return jsonify({"error": f"Invalid workflow type: {workflow_type}"}), 400

                # Get template data from query parameters
                template_data = dict(request.args)

                # Generate template
                if not self.workflow_manager:
                    return jsonify({"error": "Workflow manager not initialized"}), 500

                template = await self.workflow_manager.create_workflow_template(
                    workflow_enum, template_data
                )

                return jsonify({
                    "workflow_type": workflow_type,
                    "template": template,
                    "template_data": template_data
                })

            except Exception as e:
                logger.error(f"Error generating template: {e}")
                return jsonify({"error": str(e)}), 500

    def verify_signature(self, request) -> bool:
        """Verify GitHub webhook signature"""
        if not self.config.webhook_secret:
            return True

        # Get signature from header
        signature_header = request.headers.get("X-Hub-Signature-256", "")
        if not signature_header:
            return False

        # Extract signature
        try:
            signature = signature_header.split("sha256=")[1]
        except IndexError:
            return False

        # Calculate expected signature
        secret = self.config.webhook_secret.encode("utf-8")
        expected_signature = hmac.new(secret, request.data, hashlib.sha256).hexdigest()

        return hmac.compare_digest(signature, expected_signature)

    async def handle_webhook_async(self, event_type: str, payload: Dict[str, Any]):
        """Handle webhook event asynchronously"""
        try:
            if not self.workflow_manager:
                logger.warning("Workflow manager not initialized, skipping webhook")
                return

            result = await self.workflow_manager.handle_webhook(event_type, payload)
            logger.info(f"Webhook result: {result.success} - {result.message}")

        except Exception as e:
            logger.error(f"Error in async webhook handling: {e}")

    async def test_workflow_manager(self):
        """Test workflow manager functionality"""
        if not self.workflow_manager:
            return

        try:
            # Test CI/CD workflow
            result = await self.workflow_manager.execute_workflow(WorkflowType.CI_CD)
            logger.info(f"Test CI/CD workflow: {result.success}")

            # Test security workflow
            result = await self.workflow_manager.execute_workflow(WorkflowType.SECURITY_SCANNING)
            logger.info(f"Test security workflow: {result.success}")

        except Exception as e:
            logger.error(f"Error testing workflow manager: {e}")

    async def initialize(self):
        """Initialize the webhook server"""
        logger.info("Initializing GitHub webhook server")

        # Initialize workflow manager
        self.workflow_manager = await create_github_workflow_manager(self.config)

        logger.info("GitHub webhook server initialized")

    async def shutdown(self):
        """Shutdown the webhook server"""
        logger.info("Shutting down GitHub webhook server")

        if self.workflow_manager:
            await self.workflow_manager.shutdown()

        logger.info("GitHub webhook server shutdown complete")

    def run(self, host: str = "0.0.0.0", port: int = 8080, debug: bool = False):
        """Run the webhook server"""
        logger.info(f"Starting webhook server on {host}:{port}")

        # Initialize async components
        asyncio.run(self.initialize())

        try:
            # Run Flask app
            self.app.run(host=host, port=port, debug=debug)
        finally:
            # Cleanup
            asyncio.run(self.shutdown())


def create_server_from_config(config_path: str = "config/github_workflows_config.json") -> GitHubWebhookServer:
    """Create webhook server from configuration file"""
    # Load configuration
    if os.path.exists(config_path):
        with open(config_path) as f:
            config_data = json.load(f)
        logger.info(f"Loaded configuration from {config_path}")
    else:
        # Use environment variables
        config_data = {
            "github_token": os.getenv("GITHUB_TOKEN"),
            "repository": os.getenv("GITHUB_REPOSITORY"),
            "webhook_secret": os.getenv("WEBHOOK_SECRET"),
            "enabled_workflows": list(WorkflowType),
            "ai_review_enabled": os.getenv("AI_REVIEW_ENABLED", "false").lower() == "true",
            "cost_tracking_enabled": os.getenv("COST_TRACKING_ENABLED", "true").lower() == "true",
            "notification_channels": os.getenv("NOTIFICATION_CHANNELS", "").split(",") if os.getenv("NOTIFICATION_CHANNELS") else []
        }
        logger.info("Using environment variables for configuration")

    config = WorkflowConfig(**config_data)
    return GitHubWebhookServer(config)


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="DuckBot GitHub Webhook Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind to")
    parser.add_argument("--config", default="config/github_workflows_config.json", help="Configuration file path")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    args = parser.parse_args()

    # Create and run server
    server = create_server_from_config(args.config)
    server.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()