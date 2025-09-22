#!/usr/bin/env python3
"""
GitHub Workflow Automation Example

This script demonstrates how to use the DuckBot GitHub workflow automation system
to automate various GitHub repository management tasks.

Usage:
    python github_workflow_example.py
"""

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Dict, Any

# Add the project root to Python path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from duckbot.integrations.github_workflows import (
    create_github_workflow_manager,
    WorkflowConfig,
    WorkflowType,
    GitHubEvent
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Main example function"""
    logger.info("Starting GitHub Workflow Automation Example")

    # Load configuration
    config = await load_configuration()

    # Create workflow manager
    manager = await create_github_workflow_manager(config)

    try:
        # Demonstrate various workflow operations
        await demonstrate_workflow_operations(manager)

        # Show workflow status
        await show_workflow_status(manager)

        # Generate workflow templates
        await generate_workflow_templates(manager)

    finally:
        # Cleanup
        await manager.shutdown()

    logger.info("GitHub Workflow Automation Example completed")


async def load_configuration() -> WorkflowConfig:
    """Load workflow configuration"""
    # Try to load from config file
    config_path = Path("config/github_workflows_config.json")
    if config_path.exists():
        with open(config_path) as f:
            config_data = json.load(f)
        logger.info("Loaded configuration from file")
    else:
        # Use environment variables with defaults
        config_data = {
            "github_token": os.getenv("GITHUB_TOKEN", "your-github-token"),
            "repository": os.getenv("GITHUB_REPOSITORY", "your-username/your-repo"),
            "base_url": "https://api.github.com",
            "webhook_secret": os.getenv("WEBHOOK_SECRET"),
            "enabled_workflows": [
                WorkflowType.CI_CD,
                WorkflowType.ISSUE_MANAGEMENT,
                WorkflowType.PR_REVIEW,
                WorkflowType.RELEASE_MANAGEMENT,
                WorkflowType.SECURITY_SCANNING,
                WorkflowType.REPOSITORY_MAINTENANCE
            ],
            "ai_review_enabled": False,  # Disabled for demo
            "cost_tracking_enabled": True,
            "notification_channels": []
        }
        logger.info("Using default configuration")

    return WorkflowConfig(**config_data)


async def demonstrate_workflow_operations(manager):
    """Demonstrate various workflow operations"""
    logger.info("=== Demonstrating Workflow Operations ===")

    # 1. Execute CI/CD workflow
    logger.info("1. Executing CI/CD workflow...")
    ci_result = await manager.execute_workflow(WorkflowType.CI_CD)
    logger.info(f"CI/CD result: {ci_result.success} - {ci_result.message}")

    # 2. Execute security scanning workflow
    logger.info("2. Executing security scanning workflow...")
    security_result = await manager.execute_workflow(WorkflowType.SECURITY_SCANNING)
    logger.info(f"Security result: {security_result.success} - {security_result.message}")

    # 3. Execute repository maintenance workflow
    logger.info("3. Executing repository maintenance workflow...")
    maintenance_result = await manager.execute_workflow(WorkflowType.REPOSITORY_MAINTENANCE)
    logger.info(f"Maintenance result: {maintenance_result.success} - {maintenance_result.message}")

    # 4. Simulate webhook events
    logger.info("4. Simulating webhook events...")
    await simulate_webhook_events(manager)


async def simulate_webhook_events(manager):
    """Simulate various webhook events"""
    # Simulate issue opened event
    issue_event = GitHubEvent(
        event_type="issues",
        repository={"name": "DuckBot", "full_name": "username/DuckBot"},
        action="opened",
        issue={
            "number": 123,
            "title": "Add new AI integration feature",
            "body": "I would like to add a new AI integration feature to DuckBot...",
            "user": {"login": "contributor"}
        }
    )

    issue_result = await manager.handle_webhook("issues", issue_event.model_dump())
    logger.info(f"Issue webhook result: {issue_result.success} - {issue_result.message}")

    # Simulate PR opened event
    pr_event = GitHubEvent(
        event_type="pull_request",
        repository={"name": "DuckBot", "full_name": "username/DuckBot"},
        action="opened",
        pull_request={
            "number": 456,
            "title": "Feature: Add AI integration",
            "body": "This PR adds the new AI integration feature...",
            "user": {"login": "contributor"},
            "changed_files": 12,
            "additions": 450,
            "deletions": 23,
            "mergeable": True,
            "mergeable_state": "clean"
        }
    )

    pr_result = await manager.handle_webhook("pull_request", pr_event.model_dump())
    logger.info(f"PR webhook result: {pr_result.success} - {pr_result.message}")

    # Simulate release published event
    release_event = GitHubEvent(
        event_type="release",
        repository={"name": "DuckBot", "full_name": "username/DuckBot"},
        action="published",
        payload={
            "release": {
                "name": "DuckBot v4.2.0",
                "tag_name": "v4.2.0",
                "body": "Release notes for v4.2.0...",
                "assets": []
            }
        }
    )

    release_result = await manager.handle_webhook("release", release_event.model_dump())
    logger.info(f"Release webhook result: {release_result.success} - {release_result.message}")


async def show_workflow_status(manager):
    """Show current workflow status"""
    logger.info("=== Workflow Status ===")
    status = await manager.get_workflow_status()

    logger.info(f"Active workflows: {status['active_workflows']}")
    logger.info(f"Cost tracking enabled: {status['cost_tracking']}")
    logger.info(f"AI review enabled: {status['ai_review']}")
    logger.info(f"Repository: {status['repository']}")
    logger.info("Enabled workflow types:")
    for workflow_type, enabled in status['workflow_types'].items():
        logger.info(f"  - {workflow_type}: {'✅' if enabled else '❌'}")


async def generate_workflow_templates(manager):
    """Generate workflow templates"""
    logger.info("=== Generating Workflow Templates ===")

    # CI/CD template
    ci_template = await manager.create_workflow_template(
        WorkflowType.CI_CD,
        {"name": "DuckBot CI/CD Pipeline"}
    )

    ci_template_path = Path("templates/ci-cd-workflow.yml")
    ci_template_path.parent.mkdir(exist_ok=True)
    with open(ci_template_path, "w") as f:
        f.write(ci_template)
    logger.info(f"CI/CD template saved to {ci_template_path}")

    # Security template
    security_template = await manager.create_workflow_template(
        WorkflowType.SECURITY_SCANNING,
        {"name": "DuckBot Security Scanning"}
    )

    security_template_path = Path("templates/security-workflow.yml")
    with open(security_template_path, "w") as f:
        f.write(security_template)
    logger.info(f"Security template saved to {security_template_path}")

    # Release template
    release_template = await manager.create_workflow_template(
        WorkflowType.RELEASE_MANAGEMENT,
        {"name": "DuckBot Release Management"}
    )

    release_template_path = Path("templates/release-workflow.yml")
    with open(release_template_path, "w") as f:
        f.write(release_template)
    logger.info(f"Release template saved to {release_template_path}")


async def advanced_workflow_demo():
    """Advanced workflow demonstration"""
    logger.info("=== Advanced Workflow Demo ===")

    # This would require actual GitHub API access
    config = WorkflowConfig(
        github_token="your-real-github-token",
        repository="your-username/your-repo",
        enabled_workflows=list(WorkflowType),
        ai_review_enabled=True,
        cost_tracking_enabled=True,
        notification_channels=["discord:your-webhook-url"]
    )

    manager = await create_github_workflow_manager(config)

    try:
        # Advanced issue management with AI
        await demonstrate_ai_issue_management(manager)

        # Advanced PR review with AI
        await demonstrate_ai_pr_review(manager)

        # Cost tracking demonstration
        await demonstrate_cost_tracking(manager)

    finally:
        await manager.shutdown()


async def demonstrate_ai_issue_management(manager):
    """Demonstrate AI-powered issue management"""
    logger.info("Demonstrating AI issue management...")

    # Create a complex issue
    complex_issue = {
        "number": 789,
        "title": "Critical security vulnerability in authentication system",
        "body": """
        I've discovered a critical security vulnerability in the authentication system.

        The issue is in the `duckbot/auth.py` file where session tokens are not properly validated.
        This could allow attackers to bypass authentication and gain unauthorized access.

        Steps to reproduce:
        1. Send a malformed session token
        2. Observe that the system accepts it
        3. Gain access to protected resources

        This is urgent and needs immediate attention.
        """,
        "user": {"login": "security-researcher"}
    }

    issue_event = GitHubEvent(
        event_type="issues",
        repository={"name": "DuckBot", "full_name": "username/DuckBot"},
        action="opened",
        issue=complex_issue
    )

    # Handle with AI analysis
    result = await manager.handle_webhook("issues", issue_event.model_dump())
    logger.info(f"AI issue management result: {result.success}")

    if result.success:
        logger.info(f"Issue analysis: {result.data}")


async def demonstrate_ai_pr_review(manager):
    """Demonstrate AI-powered PR review"""
    logger.info("Demonstrating AI PR review...")

    # Create a complex PR
    complex_pr = {
        "number": 101,
        "title": "Refactor authentication system with enhanced security",
        "body": """
        This PR refactors the authentication system to address security vulnerabilities.

        Changes:
        - Implemented proper session token validation
        - Added rate limiting for authentication attempts
        - Enhanced password hashing with bcrypt
        - Added comprehensive logging for security events

        Fixes #789
        """,
        "user": {"login": "developer"},
        "changed_files": 25,
        "additions": 1200,
        "deletions": 300,
        "mergeable": True,
        "mergeable_state": "clean"
    }

    pr_event = GitHubEvent(
        event_type="pull_request",
        repository={"name": "DuckBot", "full_name": "username/DuckBot"},
        action="opened",
        pull_request=complex_pr
    )

    # Handle with AI review
    result = await manager.handle_webhook("pull_request", pr_event.model_dump())
    logger.info(f"AI PR review result: {result.success}")

    if result.success:
        logger.info(f"PR review data: {result.data}")


async def demonstrate_cost_tracking(manager):
    """Demonstrate cost tracking capabilities"""
    logger.info("Demonstrating cost tracking...")

    # Execute multiple workflows to track costs
    workflows = [
        WorkflowType.CI_CD,
        WorkflowType.SECURITY_SCANNING,
        WorkflowType.ISSUE_MANAGEMENT,
        WorkflowType.PR_REVIEW
    ]

    total_cost = 0.0
    for workflow_type in workflows:
        result = await manager.execute_workflow(workflow_type)
        total_cost += result.cost_estimate
        logger.info(f"{workflow_type.value} cost: ${result.cost_estimate:.4f}")

    logger.info(f"Total estimated cost: ${total_cost:.4f}")


if __name__ == "__main__":
    # Run the main example
    asyncio.run(main())

    # Uncomment the following to run advanced demo (requires real GitHub token)
    # asyncio.run(advanced_workflow_demo())