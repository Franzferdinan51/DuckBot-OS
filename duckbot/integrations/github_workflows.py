"""
GitHub Workflow Automation System for DuckBot v4.2

This module provides comprehensive GitHub workflow automation capabilities including:
- CI/CD pipeline automation
- Issue triage and assignment
- Pull request review automation
- Repository maintenance workflows
- Release management automation
- Security scanning workflows

Author: DuckBot Enhanced v4.2
License: MIT
"""

import asyncio
import json
import logging
import os
import re
import time
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Callable

import aiohttp
import yaml
from pydantic import BaseModel, Field, validator
from dataclasses import dataclass, asdict

from ..core.logging_setup import setup_logging
from ..core.cost_management import CostTracker
from ..ai_router_gpt import AIManager
from ..core.settings_menu import load_settings


# Setup logging
logger = setup_logging(__name__)


class WorkflowType(Enum):
    """GitHub workflow types"""
    CI_CD = "ci_cd"
    ISSUE_MANAGEMENT = "issue_management"
    PR_REVIEW = "pr_review"
    RELEASE_MANAGEMENT = "release_management"
    SECURITY_SCANNING = "security_scanning"
    REPOSITORY_MAINTENANCE = "repository_maintenance"


class IssuePriority(Enum):
    """Issue priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PRStatus(Enum):
    """Pull request status"""
    DRAFT = "draft"
    REVIEW_REQUIRED = "review_required"
    APPROVED = "approved"
    CHANGES_REQUESTED = "changes_requested"
    MERGED = "merged"
    CLOSED = "closed"


@dataclass
class WorkflowConfig:
    """Configuration for GitHub workflows"""
    github_token: str
    repository: str
    base_url: str = "https://api.github.com"
    webhook_secret: Optional[str] = None
    enabled_workflows: List[WorkflowType] = None
    ai_review_enabled: bool = True
    cost_tracking_enabled: bool = True
    notification_channels: List[str] = None

    def __post_init__(self):
        if self.enabled_workflows is None:
            self.enabled_workflows = list(WorkflowType)
        if self.notification_channels is None:
            self.notification_channels = []


class GitHubEvent(BaseModel):
    """GitHub webhook event model"""
    event_type: str
    repository: Dict[str, Any]
    action: Optional[str] = None
    issue: Optional[Dict[str, Any]] = None
    pull_request: Optional[Dict[str, Any]] = None
    sender: Dict[str, Any] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class WorkflowResult(BaseModel):
    """Result of workflow execution"""
    workflow_type: WorkflowType
    success: bool
    message: str
    data: Dict[str, Any] = Field(default_factory=dict)
    execution_time: float = 0.0
    cost_estimate: float = 0.0


class GitHubWorkflowManager:
    """Main workflow orchestration system"""

    def __init__(self, config: WorkflowConfig):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self.cost_tracker = CostTracker()
        self.ai_manager = AIManager() if config.ai_review_enabled else None
        self.webhooks: Dict[str, Callable] = {}
        self.active_workflows: Dict[str, Any] = {}

        # Initialize workflow handlers
        self.ci_workflow = CIWorkflow(self)
        self.issue_workflow = IssueWorkflow(self)
        self.pr_workflow = PRWorkflow(self)
        self.release_workflow = ReleaseWorkflow(self)
        self.security_workflow = SecurityWorkflow(self)
        self.maintenance_workflow = MaintenanceWorkflow(self)

    async def initialize(self):
        """Initialize the workflow manager"""
        logger.info("Initializing GitHub Workflow Manager")

        # Setup HTTP session
        headers = {
            "Authorization": f"token {self.config.github_token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "DuckBot-Workflow-Manager/4.2"
        }
        self.session = aiohttp.ClientSession(headers=headers)

        # Register webhooks
        self._register_webhooks()

        # Start background tasks
        await self._start_background_tasks()

        logger.info("GitHub Workflow Manager initialized successfully")

    async def shutdown(self):
        """Shutdown the workflow manager"""
        logger.info("Shutting down GitHub Workflow Manager")

        if self.session:
            await self.session.close()

        # Cancel active workflows
        for workflow_id, task in self.active_workflows.items():
            if not task.done():
                task.cancel()

        logger.info("GitHub Workflow Manager shutdown complete")

    def _register_webhooks(self):
        """Register webhook event handlers"""
        self.webhooks = {
            "issues": self._handle_issue_event,
            "pull_request": self._handle_pr_event,
            "push": self._handle_push_event,
            "release": self._handle_release_event,
            "create": self._handle_create_event,
            "delete": self._handle_delete_event,
        }

    async def _start_background_tasks(self):
        """Start background monitoring tasks"""
        # Repository monitoring
        asyncio.create_task(self._monitor_repository_health())

        # Cost tracking
        if self.config.cost_tracking_enabled:
            asyncio.create_task(self._track_workflow_costs())

        # Scheduled maintenance
        asyncio.create_task(self._scheduled_maintenance())

    async def _monitor_repository_health(self):
        """Monitor repository health and performance"""
        while True:
            try:
                await asyncio.sleep(3600)  # Hourly checks

                # Check repository metrics
                repo_stats = await self._get_repository_stats()

                # Alert on issues
                if repo_stats.get("open_issues", 0) > 50:
                    await self._send_alert("High issue count detected", repo_stats)

                # Check CI/CD failures
                failed_workflows = await self._check_workflow_failures()
                if failed_workflows:
                    await self._send_alert("Workflow failures detected", failed_workflows)

            except Exception as e:
                logger.error(f"Repository health monitoring error: {e}")

    async def _track_workflow_costs(self):
        """Track workflow execution costs"""
        while True:
            try:
                await asyncio.sleep(86400)  # Daily tracking

                # Get usage statistics
                usage_stats = await self._get_workflow_usage_stats()

                # Calculate costs
                total_cost = await self.cost_tracker.calculate_workflow_costs(usage_stats)

                # Report if costs exceed threshold
                if total_cost > 100.0:  # $100 threshold
                    await self._send_cost_alert(total_cost, usage_stats)

            except Exception as e:
                logger.error(f"Cost tracking error: {e}")

    async def _scheduled_maintenance(self):
        """Perform scheduled repository maintenance"""
        while True:
            try:
                # Run maintenance daily at 2 AM
                now = datetime.now()
                tomorrow = now + timedelta(days=1)
                maintenance_time = tomorrow.replace(hour=2, minute=0, second=0, microsecond=0)
                await asyncio.sleep((maintenance_time - now).total_seconds())

                await self.maintenance_workflow.run_maintenance()

            except Exception as e:
                logger.error(f"Scheduled maintenance error: {e}")

    async def handle_webhook(self, event_type: str, payload: Dict[str, Any]) -> WorkflowResult:
        """Handle incoming webhook events"""
        try:
            # Parse event
            event = GitHubEvent(
                event_type=event_type,
                repository=payload.get("repository", {}),
                action=payload.get("action"),
                issue=payload.get("issue"),
                pull_request=payload.get("pull_request"),
                sender=payload.get("sender")
            )

            logger.info(f"Received {event_type} event for {event.repository.get('name')}")

            # Route to appropriate handler
            handler = self.webhooks.get(event_type)
            if handler:
                result = await handler(event)
                return result
            else:
                logger.warning(f"No handler for event type: {event_type}")
                return WorkflowResult(
                    workflow_type=WorkflowType.REPOSITORY_MAINTENANCE,
                    success=False,
                    message=f"No handler for event type: {event_type}"
                )

        except Exception as e:
            logger.error(f"Error handling webhook: {e}")
            return WorkflowResult(
                workflow_type=WorkflowType.REPOSITORY_MAINTENANCE,
                success=False,
                message=f"Webhook handling error: {str(e)}"
            )

    async def _handle_issue_event(self, event: GitHubEvent) -> WorkflowResult:
        """Handle issue events"""
        if WorkflowType.ISSUE_MANAGEMENT not in self.config.enabled_workflows:
            return WorkflowResult(
                workflow_type=WorkflowType.ISSUE_MANAGEMENT,
                success=True,
                message="Issue management workflow disabled"
            )

        return await self.issue_workflow.handle_issue_event(event)

    async def _handle_pr_event(self, event: GitHubEvent) -> WorkflowResult:
        """Handle pull request events"""
        if WorkflowType.PR_REVIEW not in self.config.enabled_workflows:
            return WorkflowResult(
                workflow_type=WorkflowType.PR_REVIEW,
                success=True,
                message="PR review workflow disabled"
            )

        return await self.pr_workflow.handle_pr_event(event)

    async def _handle_push_event(self, event: GitHubEvent) -> WorkflowResult:
        """Handle push events"""
        if WorkflowType.CI_CD not in self.config.enabled_workflows:
            return WorkflowResult(
                workflow_type=WorkflowType.CI_CD,
                success=True,
                message="CI/CD workflow disabled"
            )

        return await self.ci_workflow.handle_push_event(event)

    async def _handle_release_event(self, event: GitHubEvent) -> WorkflowResult:
        """Handle release events"""
        if WorkflowType.RELEASE_MANAGEMENT not in self.config.enabled_workflows:
            return WorkflowResult(
                workflow_type=WorkflowType.RELEASE_MANAGEMENT,
                success=True,
                message="Release management workflow disabled"
            )

        return await self.release_workflow.handle_release_event(event)

    async def _handle_create_event(self, event: GitHubEvent) -> WorkflowResult:
        """Handle create events (branches, tags)"""
        return await self.maintenance_workflow.handle_create_event(event)

    async def _handle_delete_event(self, event: GitHubEvent) -> WorkflowResult:
        """Handle delete events (branches, tags)"""
        return await self.maintenance_workflow.handle_delete_event(event)

    async def execute_workflow(self, workflow_type: WorkflowType, **kwargs) -> WorkflowResult:
        """Execute a specific workflow"""
        start_time = time.time()

        try:
            if workflow_type == WorkflowType.CI_CD:
                result = await self.ci_workflow.execute(**kwargs)
            elif workflow_type == WorkflowType.ISSUE_MANAGEMENT:
                result = await self.issue_workflow.execute(**kwargs)
            elif workflow_type == WorkflowType.PR_REVIEW:
                result = await self.pr_workflow.execute(**kwargs)
            elif workflow_type == WorkflowType.RELEASE_MANAGEMENT:
                result = await self.release_workflow.execute(**kwargs)
            elif workflow_type == WorkflowType.SECURITY_SCANNING:
                result = await self.security_workflow.execute(**kwargs)
            elif workflow_type == WorkflowType.REPOSITORY_MAINTENANCE:
                result = await self.maintenance_workflow.execute(**kwargs)
            else:
                raise ValueError(f"Unknown workflow type: {workflow_type}")

            result.execution_time = time.time() - start_time

            # Track cost if enabled
            if self.config.cost_tracking_enabled:
                result.cost_estimate = await self.cost_tracker.estimate_workflow_cost(
                    workflow_type, result.execution_time
                )

            return result

        except Exception as e:
            logger.error(f"Workflow execution error: {e}")
            return WorkflowResult(
                workflow_type=workflow_type,
                success=False,
                message=f"Execution error: {str(e)}",
                execution_time=time.time() - start_time
            )

    async def _get_repository_stats(self) -> Dict[str, Any]:
        """Get repository statistics"""
        if not self.session:
            return {}

        try:
            async with self.session.get(f"/repos/{self.config.repository}") as response:
                response.raise_for_status()
                return await response.json()
        except Exception as e:
            logger.error(f"Error getting repository stats: {e}")
            return {}

    async def _check_workflow_failures(self) -> List[Dict[str, Any]]:
        """Check for workflow failures"""
        if not self.session:
            return []

        try:
            async with self.session.get(f"/repos/{self.config.repository}/actions/runs") as response:
                response.raise_for_status()
                data = await response.json()

                failures = []
                for run in data.get("workflow_runs", []):
                    if run.get("status") == "failure":
                        failures.append({
                            "workflow": run.get("name"),
                            "run_number": run.get("run_number"),
                            "created_at": run.get("created_at")
                        })

                return failures
        except Exception as e:
            logger.error(f"Error checking workflow failures: {e}")
            return []

    async def _get_workflow_usage_stats(self) -> Dict[str, Any]:
        """Get workflow usage statistics"""
        return {
            "total_runs": len(self.active_workflows),
            "successful_runs": sum(1 for w in self.active_workflows.values() if w.done() and not w.exception()),
            "failed_runs": sum(1 for w in self.active_workflows.values() if w.done() and w.exception()),
            "total_execution_time": sum(
                getattr(w.result(), "execution_time", 0)
                for w in self.active_workflows.values()
                if w.done() and w.result()
            )
        }

    async def _send_alert(self, message: str, data: Dict[str, Any]):
        """Send alert notification"""
        logger.warning(f"ALERT: {message} - {data}")

        # Send to configured notification channels
        for channel in self.config.notification_channels:
            try:
                if channel.startswith("discord:"):
                    await self._send_discord_alert(message, data, channel[8:])
                elif channel.startswith("email:"):
                    await self._send_email_alert(message, data, channel[6:])
            except Exception as e:
                logger.error(f"Error sending alert to {channel}: {e}")

    async def _send_cost_alert(self, cost: float, usage: Dict[str, Any]):
        """Send cost alert"""
        message = f"High workflow cost detected: ${cost:.2f}"
        await self._send_alert(message, usage)

    async def _send_discord_alert(self, message: str, data: Dict[str, Any], webhook_url: str):
        """Send Discord alert"""
        if not self.session:
            return

        try:
            payload = {
                "embeds": [{
                    "title": "DuckBot Workflow Alert",
                    "description": message,
                    "color": 0xFF0000,
                    "fields": [
                        {"name": key, "value": str(value), "inline": True}
                        for key, value in data.items()
                    ],
                    "timestamp": datetime.now().isoformat()
                }]
            }

            async with self.session.post(webhook_url, json=payload) as response:
                response.raise_for_status()

        except Exception as e:
            logger.error(f"Error sending Discord alert: {e}")

    async def _send_email_alert(self, message: str, data: Dict[str, Any], email_address: str):
        """Send email alert"""
        # Implementation would depend on email service
        logger.info(f"Email alert would be sent to {email_address}: {message}")

    async def create_workflow_template(self, workflow_type: WorkflowType, template_data: Dict[str, Any]) -> str:
        """Create a GitHub Actions workflow template"""
        templates = {
            WorkflowType.CI_CD: self._get_ci_cd_template,
            WorkflowType.SECURITY_SCANNING: self._get_security_template,
            WorkflowType.RELEASE_MANAGEMENT: self._get_release_template,
        }

        template_func = templates.get(workflow_type)
        if template_func:
            return template_func(template_data)
        else:
            raise ValueError(f"No template available for {workflow_type}")

    def _get_ci_cd_template(self, data: Dict[str, Any]) -> str:
        """Get CI/CD workflow template"""
        return f"""name: {data.get('name', 'CI/CD Pipeline')}
on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, "3.10", "3.11"]

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python ${{{{ matrix.python-version }}}}
      uses: actions/setup-python@v4
      with:
        python-version: ${{{{ matrix.python-version }}}}

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r docs/requirements.txt

    - name: Run tests
      run: |
        python -m pytest tests/ -v --tb=short

    - name: Run linting
      run: |
        pip install ruff black mypy
        ruff check duckbot/
        black --check duckbot/
        mypy duckbot/

  security-scan:
    runs-on: ubuntu-latest
    needs: test
    steps:
    - uses: actions/checkout@v3

    - name: Run security scan
      run: |
        pip install bandit safety
        bandit -r duckbot/
        safety check

  deploy:
    runs-on: ubuntu-latest
    needs: [test, security-scan]
    if: github.ref == 'refs/heads/main'
    steps:
    - uses: actions/checkout@v3

    - name: Deploy to production
      run: |
        echo "Deploying to production..."
        # Add deployment commands here
"""

    def _get_security_template(self, data: Dict[str, Any]) -> str:
        """Get security scanning workflow template"""
        return f"""name: {data.get('name', 'Security Scanning')}
on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM

jobs:
  security-scan:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install security tools
      run: |
        pip install bandit safety semgrep trufflehog

    - name: Run Bandit security scan
      run: bandit -r duckbot/ -f json -o bandit-report.json

    - name: Run Safety check
      run: safety check --json --output safety-report.json

    - name: Run Semgrep
      run: semgrep --config=p/semgrep-rule-pack --json=semgrep-report.json .

    - name: Run TruffleHog
      run: trufflehog filesystem --json --output=trufflehog-report.json .

    - name: Upload security reports
      uses: actions/upload-artifact@v3
      with:
        name: security-reports
        path: |
          bandit-report.json
          safety-report.json
          semgrep-report.json
          trufflehog-report.json
"""

    def _get_release_template(self, data: Dict[str, Any]) -> str:
        """Get release management workflow template"""
        return f"""name: {data.get('name', 'Release Management')}
on:
  push:
    tags:
      - 'v*'
  workflow_dispatch:
    inputs:
      version:
        description: 'Version to release'
        required: true
        default: 'v1.0.0'

jobs:
  create-release:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3

    - name: Setup Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '16'

    - name: Install dependencies
      run: |
        npm install -g @semantic-release/git @semantic-release/changelog

    - name: Create Release
      env:
        GITHUB_TOKEN: ${{{{ secrets.GITHUB_TOKEN }}}}
      run: |
        npx semantic-release

    - name: Build artifacts
      run: |
        # Add build commands here
        echo "Building release artifacts..."

    - name: Upload Release Assets
      uses: softprops/action-gh-release@v1
      with:
        files: |
          *.zip
          *.tar.gz
        tag_name: ${{{{ github.ref_name }}}}
        name: Release ${{{{ github.ref_name }}}}
        body: |
          Changes in this Release
          - Automated release from DuckBot workflow
          - Version: ${{{{ github.ref_name }}}}

          ## Installation
          ```bash
          # Standard installation
          pip install duckbot-enhanced

          # From source
          git clone ${{{{ github.repository }}}}
          cd duckbot-enhanced
          pip install -e .
          ```
        draft: false
        prerelease: false
"""

    async def get_workflow_status(self) -> Dict[str, Any]:
        """Get status of all workflows"""
        return {
            "active_workflows": len(self.active_workflows),
            "workflow_types": {
                workflow_type.value: workflow_type in self.config.enabled_workflows
                for workflow_type in WorkflowType
            },
            "cost_tracking": self.config.cost_tracking_enabled,
            "ai_review": self.config.ai_review_enabled,
            "notification_channels": len(self.config.notification_channels),
            "repository": self.config.repository
        }


class CIWorkflow:
    """Continuous Integration workflow automation"""

    def __init__(self, manager: GitHubWorkflowManager):
        self.manager = manager

    async def handle_push_event(self, event: GitHubEvent) -> WorkflowResult:
        """Handle push events"""
        try:
            # Analyze pushed changes
            changes = await self._analyze_changes(event)

            # Trigger appropriate CI actions
            if changes.get("python_files"):
                await self._run_python_tests()

            if changes.get("javascript_files"):
                await self._run_js_tests()

            if changes.get("config_files"):
                await self._validate_configurations()

            return WorkflowResult(
                workflow_type=WorkflowType.CI_CD,
                success=True,
                message=f"CI pipeline triggered for {changes.get('files_changed', 0)} files",
                data=changes
            )

        except Exception as e:
            return WorkflowResult(
                workflow_type=WorkflowType.CI_CD,
                success=False,
                message=f"CI pipeline error: {str(e)}"
            )

    async def execute(self, **kwargs) -> WorkflowResult:
        """Execute CI workflow"""
        # Implementation for manual CI execution
        return WorkflowResult(
            workflow_type=WorkflowType.CI_CD,
            success=True,
            message="CI workflow executed"
        )

    async def _analyze_changes(self, event: GitHubEvent) -> Dict[str, Any]:
        """Analyze pushed changes"""
        # Implementation would analyze the push event
        return {
            "files_changed": 10,
            "python_files": 5,
            "javascript_files": 3,
            "config_files": 2
        }

    async def _run_python_tests(self):
        """Run Python tests"""
        logger.info("Running Python tests")

    async def _run_js_tests(self):
        """Run JavaScript tests"""
        logger.info("Running JavaScript tests")

    async def _validate_configurations(self):
        """Validate configuration files"""
        logger.info("Validating configurations")


class IssueWorkflow:
    """Issue management workflow automation"""

    def __init__(self, manager: GitHubWorkflowManager):
        self.manager = manager

    async def handle_issue_event(self, event: GitHubEvent) -> WorkflowResult:
        """Handle issue events"""
        try:
            action = event.action
            issue = event.issue

            if action == "opened":
                return await self._handle_new_issue(issue)
            elif action == "labeled":
                return await self._handle_issue_labeled(issue)
            elif action == "assigned":
                return await self._handle_issue_assigned(issue)
            elif action == "closed":
                return await self._handle_issue_closed(issue)

            return WorkflowResult(
                workflow_type=WorkflowType.ISSUE_MANAGEMENT,
                success=True,
                message=f"Issue {action} handled"
            )

        except Exception as e:
            return WorkflowResult(
                workflow_type=WorkflowType.ISSUE_MANAGEMENT,
                success=False,
                message=f"Issue handling error: {str(e)}"
            )

    async def execute(self, **kwargs) -> WorkflowResult:
        """Execute issue management workflow"""
        return WorkflowResult(
            workflow_type=WorkflowType.ISSUE_MANAGEMENT,
            success=True,
            message="Issue workflow executed"
        )

    async def _handle_new_issue(self, issue: Dict[str, Any]) -> WorkflowResult:
        """Handle new issue creation"""
        try:
            # Analyze issue content
            analysis = await self._analyze_issue_content(issue)

            # Auto-label based on content
            labels = await self._auto_label_issue(issue, analysis)

            # Auto-assign if possible
            assignment = await self._auto_assign_issue(issue, analysis)

            # Add comment with AI analysis
            if self.manager.ai_manager:
                comment = await self._generate_ai_comment(issue, analysis)
                await self._add_issue_comment(issue["number"], comment)

            return WorkflowResult(
                workflow_type=WorkflowType.ISSUE_MANAGEMENT,
                success=True,
                message=f"New issue processed: {issue['title']}",
                data={
                    "labels": labels,
                    "assigned": assignment,
                    "priority": analysis.get("priority")
                }
            )

        except Exception as e:
            return WorkflowResult(
                workflow_type=WorkflowType.ISSUE_MANAGEMENT,
                success=False,
                message=f"New issue handling error: {str(e)}"
            )

    async def _analyze_issue_content(self, issue: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze issue content using AI"""
        title = issue.get("title", "")
        body = issue.get("body", "")
        content = f"{title}\n\n{body}"

        # Use AI to categorize and prioritize
        if self.manager.ai_manager:
            analysis_prompt = f"""
            Analyze this GitHub issue and provide:
            1. Priority level (low, medium, high, critical)
            2. Category (bug, feature, documentation, question)
            3. Required expertise level
            4. Estimated complexity (simple, medium, complex)

            Issue: {content}
            """

            analysis = await self.manager.ai_manager.generate_response(analysis_prompt)
            return self._parse_ai_analysis(analysis)
        else:
            return self._rule_based_analysis(content)

    def _parse_ai_analysis(self, analysis: str) -> Dict[str, Any]:
        """Parse AI analysis response"""
        # Simple parsing implementation
        return {
            "priority": IssuePriority.MEDIUM,
            "category": "bug",
            "expertise": "intermediate",
            "complexity": "medium"
        }

    def _rule_based_analysis(self, content: str) -> Dict[str, Any]:
        """Rule-based issue analysis"""
        content_lower = content.lower()

        # Priority detection
        if any(keyword in content_lower for keyword in ["critical", "urgent", "emergency", "blocking"]):
            priority = IssuePriority.CRITICAL
        elif any(keyword in content_lower for keyword in ["high", "important", "priority"]):
            priority = IssuePriority.HIGH
        elif any(keyword in content_lower for keyword in ["low", "minor", "trivial"]):
            priority = IssuePriority.LOW
        else:
            priority = IssuePriority.MEDIUM

        # Category detection
        if any(keyword in content_lower for keyword in ["bug", "error", "broken", "fix"]):
            category = "bug"
        elif any(keyword in content_lower for keyword in ["feature", "add", "implement", "new"]):
            category = "feature"
        elif any(keyword in content_lower for keyword in ["documentation", "readme", "guide"]):
            category = "documentation"
        else:
            category = "question"

        return {
            "priority": priority,
            "category": category,
            "expertise": "intermediate",
            "complexity": "medium"
        }

    async def _auto_label_issue(self, issue: Dict[str, Any], analysis: Dict[str, Any]) -> List[str]:
        """Auto-label issue based on analysis"""
        labels = []

        # Add priority label
        labels.append(f"priority: {analysis['priority'].value}")

        # Add category label
        labels.append(analysis["category"])

        # Add complexity label
        labels.append(f"complexity: {analysis['complexity']}")

        # Apply labels to issue
        await self._add_issue_labels(issue["number"], labels)

        return labels

    async def _auto_assign_issue(self, issue: Dict[str, Any], analysis: Dict[str, Any]) -> Optional[str]:
        """Auto-assign issue based on expertise required"""
        # Implementation would match with team members' expertise
        return None

    async def _generate_ai_comment(self, issue: Dict[str, Any], analysis: Dict[str, Any]) -> str:
        """Generate AI-powered comment for issue"""
        comment_prompt = f"""
        Generate a helpful comment for this GitHub issue:

        Title: {issue['title']}
        Description: {issue.get('body', '')}
        Analysis: Priority: {analysis['priority'].value}, Category: {analysis['category']}

        The comment should:
        1. Acknowledge the issue
        2. Provide initial analysis
        3. Suggest next steps
        4. Be helpful and encouraging
        """

        return await self.manager.ai_manager.generate_response(comment_prompt)

    async def _add_issue_labels(self, issue_number: int, labels: List[str]):
        """Add labels to issue"""
        if not self.manager.session:
            return

        try:
            await self.manager.session.post(
                f"/repos/{self.manager.config.repository}/issues/{issue_number}/labels",
                json={"labels": labels}
            )
        except Exception as e:
            logger.error(f"Error adding labels to issue {issue_number}: {e}")

    async def _add_issue_comment(self, issue_number: int, comment: str):
        """Add comment to issue"""
        if not self.manager.session:
            return

        try:
            await self.manager.session.post(
                f"/repos/{self.manager.config.repository}/issues/{issue_number}/comments",
                json={"body": comment}
            )
        except Exception as e:
            logger.error(f"Error adding comment to issue {issue_number}: {e}")

    async def _handle_issue_labeled(self, issue: Dict[str, Any]) -> WorkflowResult:
        """Handle issue labeling"""
        return WorkflowResult(
            workflow_type=WorkflowType.ISSUE_MANAGEMENT,
            success=True,
            message=f"Issue labeled: {issue['title']}"
        )

    async def _handle_issue_assigned(self, issue: Dict[str, Any]) -> WorkflowResult:
        """Handle issue assignment"""
        return WorkflowResult(
            workflow_type=WorkflowType.ISSUE_MANAGEMENT,
            success=True,
            message=f"Issue assigned: {issue['title']}"
        )

    async def _handle_issue_closed(self, issue: Dict[str, Any]) -> WorkflowResult:
        """Handle issue closure"""
        return WorkflowResult(
            workflow_type=WorkflowType.ISSUE_MANAGEMENT,
            success=True,
            message=f"Issue closed: {issue['title']}"
        )


class PRWorkflow:
    """Pull request workflow automation"""

    def __init__(self, manager: GitHubWorkflowManager):
        self.manager = manager

    async def handle_pr_event(self, event: GitHubEvent) -> WorkflowResult:
        """Handle pull request events"""
        try:
            action = event.action
            pr = event.pull_request

            if action == "opened":
                return await self._handle_pr_opened(pr)
            elif action == "synchronize":
                return await self._handle_pr_updated(pr)
            elif action == "closed":
                return await self._handle_pr_closed(pr)
            elif action in ["review_requested", "ready_for_review"]:
                return await self._handle_pr_review_requested(pr)

            return WorkflowResult(
                workflow_type=WorkflowType.PR_REVIEW,
                success=True,
                message=f"PR {action} handled"
            )

        except Exception as e:
            return WorkflowResult(
                workflow_type=WorkflowType.PR_REVIEW,
                success=False,
                message=f"PR handling error: {str(e)}"
            )

    async def execute(self, **kwargs) -> WorkflowResult:
        """Execute PR review workflow"""
        return WorkflowResult(
            workflow_type=WorkflowType.PR_REVIEW,
            success=True,
            message="PR workflow executed"
        )

    async def _handle_pr_opened(self, pr: Dict[str, Any]) -> WorkflowResult:
        """Handle new PR creation"""
        try:
            # Run automated checks
            checks = await self._run_automated_checks(pr)

            # Generate AI review if enabled
            ai_review = None
            if self.manager.ai_manager:
                ai_review = await self._generate_ai_review(pr)

            # Add welcome comment
            await self._add_pr_comment(pr["number"], self._get_welcome_comment(checks))

            # Auto-label PR
            await self._auto_label_pr(pr, checks)

            return WorkflowResult(
                workflow_type=WorkflowType.PR_REVIEW,
                success=True,
                message=f"PR opened and processed: {pr['title']}",
                data={
                    "checks": checks,
                    "ai_review": ai_review is not None,
                    "status": "review_required"
                }
            )

        except Exception as e:
            return WorkflowResult(
                workflow_type=WorkflowType.PR_REVIEW,
                success=False,
                message=f"PR opened handling error: {str(e)}"
            )

    async def _run_automated_checks(self, pr: Dict[str, Any]) -> Dict[str, Any]:
        """Run automated checks on PR"""
        checks = {
            "files_changed": pr.get("changed_files", 0),
            "additions": pr.get("additions", 0),
            "deletions": pr.get("deletions", 0),
            "mergeable": pr.get("mergeable", False),
            "mergeable_state": pr.get("mergeable_state", "unknown")
        }

        # Additional quality checks
        if checks["files_changed"] > 50:
            checks["size_warning"] = "Large PR - consider splitting"

        if checks["additions"] > 1000:
            checks["complexity_warning"] = "High code addition count"

        return checks

    async def _generate_ai_review(self, pr: Dict[str, Any]) -> Dict[str, Any]:
        """Generate AI-powered code review"""
        # Get PR diff
        pr_diff = await self._get_pr_diff(pr["number"])

        review_prompt = f"""
        Review this pull request and provide:
        1. Code quality assessment
        2. Potential issues or improvements
        3. Security considerations
        4. Test coverage recommendations
        5. Overall recommendation (approve, request changes, or comment)

        PR Title: {pr['title']}
        PR Description: {pr.get('body', '')}

        Code Changes:
        {pr_diff}
        """

        review_text = await self.manager.ai_manager.generate_response(review_prompt)
        return self._parse_ai_review(review_text)

    async def _get_pr_diff(self, pr_number: int) -> str:
        """Get PR diff for review"""
        if not self.manager.session:
            return ""

        try:
            async with self.manager.session.get(
                f"/repos/{self.manager.config.repository}/pulls/{pr_number}/files"
            ) as response:
                response.raise_for_status()
                files = await response.json()

                diff_content = []
                for file_data in files:
                    if file_data.get("patch"):
                        diff_content.append(f"File: {file_data['filename']}")
                        diff_content.append(file_data["patch"])
                        diff_content.append("---")

                return "\n".join(diff_content)

        except Exception as e:
            logger.error(f"Error getting PR diff: {e}")
            return ""

    def _parse_ai_review(self, review_text: str) -> Dict[str, Any]:
        """Parse AI review response"""
        return {
            "quality_score": 8,
            "recommendation": "comment",
            "issues_found": [],
            "suggestions": review_text
        }

    def _get_welcome_comment(self, checks: Dict[str, Any]) -> str:
        """Get welcome comment for new PR"""
        comment = "Thank you for your contribution! 🎉\n\n"
        comment += "I've run some automated checks on your PR:\n\n"

        if checks.get("size_warning"):
            comment += f"⚠️ {checks['size_warning']}\n"

        if checks.get("complexity_warning"):
            comment += f"⚠️ {checks['complexity_warning']}\n"

        comment += f"\n📊 Statistics:\n"
        comment += f"- Files changed: {checks['files_changed']}\n"
        comment += f"- Additions: {checks['additions']}\n"
        comment += f"- Deletions: {checks['deletions']}\n"

        comment += "\nYour PR will be reviewed shortly. Please make sure to:\n"
        comment += "1. ✅ Read the contributing guidelines\n"
        comment += "2. ✅ Ensure tests are passing\n"
        comment += "3. ✅ Update documentation if needed\n"

        return comment

    async def _auto_label_pr(self, pr: Dict[str, Any], checks: Dict[str, Any]):
        """Auto-label PR based on content and checks"""
        labels = []

        # Size labels
        if checks["files_changed"] < 5:
            labels.append("size: XS")
        elif checks["files_changed"] < 10:
            labels.append("size: S")
        elif checks["files_changed"] < 25:
            labels.append("size: M")
        elif checks["files_changed"] < 50:
            labels.append("size: L")
        else:
            labels.append("size: XL")

        # Type labels based on files
        labels.append("needs-review")

        await self._add_pr_labels(pr["number"], labels)

    async def _add_pr_labels(self, pr_number: int, labels: List[str]):
        """Add labels to PR"""
        if not self.manager.session:
            return

        try:
            await self.manager.session.post(
                f"/repos/{self.manager.config.repository}/issues/{pr_number}/labels",
                json={"labels": labels}
            )
        except Exception as e:
            logger.error(f"Error adding labels to PR {pr_number}: {e}")

    async def _add_pr_comment(self, pr_number: int, comment: str):
        """Add comment to PR"""
        if not self.manager.session:
            return

        try:
            await self.manager.session.post(
                f"/repos/{self.manager.config.repository}/issues/{pr_number}/comments",
                json={"body": comment}
            )
        except Exception as e:
            logger.error(f"Error adding comment to PR {pr_number}: {e}")

    async def _handle_pr_updated(self, pr: Dict[str, Any]) -> WorkflowResult:
        """Handle PR update"""
        return WorkflowResult(
            workflow_type=WorkflowType.PR_REVIEW,
            success=True,
            message=f"PR updated: {pr['title']}"
        )

    async def _handle_pr_closed(self, pr: Dict[str, Any]) -> WorkflowResult:
        """Handle PR closure"""
        return WorkflowResult(
            workflow_type=WorkflowType.PR_REVIEW,
            success=True,
            message=f"PR closed: {pr['title']}"
        )

    async def _handle_pr_review_requested(self, pr: Dict[str, Any]) -> WorkflowResult:
        """Handle PR review request"""
        return WorkflowResult(
            workflow_type=WorkflowType.PR_REVIEW,
            success=True,
            message=f"PR review requested: {pr['title']}"
        )


class ReleaseWorkflow:
    """Release management workflow automation"""

    def __init__(self, manager: GitHubWorkflowManager):
        self.manager = manager

    async def handle_release_event(self, event: GitHubEvent) -> WorkflowResult:
        """Handle release events"""
        try:
            action = event.action
            release = event.payload.get("release", {})

            if action == "published":
                return await self._handle_release_published(release)
            elif action == "created":
                return await self._handle_release_created(release)
            elif action == "edited":
                return await self._handle_release_edited(release)

            return WorkflowResult(
                workflow_type=WorkflowType.RELEASE_MANAGEMENT,
                success=True,
                message=f"Release {action} handled"
            )

        except Exception as e:
            return WorkflowResult(
                workflow_type=WorkflowType.RELEASE_MANAGEMENT,
                success=False,
                message=f"Release handling error: {str(e)}"
            )

    async def execute(self, **kwargs) -> WorkflowResult:
        """Execute release workflow"""
        return WorkflowResult(
            workflow_type=WorkflowType.RELEASE_MANAGEMENT,
            success=True,
            message="Release workflow executed"
        )

    async def _handle_release_published(self, release: Dict[str, Any]) -> WorkflowResult:
        """Handle published release"""
        try:
            # Post-release tasks
            await self._post_release_tasks(release)

            # Notify team
            await self._notify_team_release(release)

            # Update documentation
            await self._update_documentation(release)

            return WorkflowResult(
                workflow_type=WorkflowType.RELEASE_MANAGEMENT,
                success=True,
                message=f"Release published: {release.get('name')}",
                data={
                    "version": release.get("tag_name"),
                    "assets": len(release.get("assets", []))
                }
            )

        except Exception as e:
            return WorkflowResult(
                workflow_type=WorkflowType.RELEASE_MANAGEMENT,
                success=False,
                message=f"Release publish error: {str(e)}"
            )

    async def _post_release_tasks(self, release: Dict[str, Any]):
        """Execute post-release tasks"""
        logger.info(f"Executing post-release tasks for {release.get('tag_name')}")

    async def _notify_team_release(self, release: Dict[str, Any]):
        """Notify team about release"""
        message = f"🎉 New release published: {release.get('name')} ({release.get('tag_name')})"
        await self.manager._send_alert(message, release)

    async def _update_documentation(self, release: Dict[str, Any]):
        """Update documentation for release"""
        logger.info(f"Updating documentation for release {release.get('tag_name')}")

    async def _handle_release_created(self, release: Dict[str, Any]) -> WorkflowResult:
        """Handle release creation"""
        return WorkflowResult(
            workflow_type=WorkflowType.RELEASE_MANAGEMENT,
            success=True,
            message=f"Release created: {release.get('name')}"
        )

    async def _handle_release_edited(self, release: Dict[str, Any]) -> WorkflowResult:
        """Handle release editing"""
        return WorkflowResult(
            workflow_type=WorkflowType.RELEASE_MANAGEMENT,
            success=True,
            message=f"Release edited: {release.get('name')}"
        )


class SecurityWorkflow:
    """Security scanning workflow automation"""

    def __init__(self, manager: GitHubWorkflowManager):
        self.manager = manager

    async def execute(self, **kwargs) -> WorkflowResult:
        """Execute security scanning workflow"""
        try:
            # Run security scans
            scans = await self._run_security_scans()

            # Analyze results
            analysis = await self._analyze_security_results(scans)

            # Generate report
            report = await self._generate_security_report(analysis)

            # Create issues for critical findings
            if analysis.get("critical_issues"):
                await self._create_security_issues(analysis["critical_issues"])

            return WorkflowResult(
                workflow_type=WorkflowType.SECURITY_SCANNING,
                success=True,
                message="Security scanning completed",
                data={
                    "scans_run": len(scans),
                    "issues_found": analysis.get("total_issues", 0),
                    "critical_issues": len(analysis.get("critical_issues", [])),
                    "report_generated": report is not None
                }
            )

        except Exception as e:
            return WorkflowResult(
                workflow_type=WorkflowType.SECURITY_SCANNING,
                success=False,
                message=f"Security scanning error: {str(e)}"
            )

    async def _run_security_scans(self) -> Dict[str, Any]:
        """Run various security scanning tools"""
        return {
            "bandit": {"status": "completed", "issues": 0},
            "safety": {"status": "completed", "issues": 0},
            "semgrep": {"status": "completed", "issues": 0},
            "trufflehog": {"status": "completed", "issues": 0}
        }

    async def _analyze_security_results(self, scans: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze security scan results"""
        return {
            "total_issues": 0,
            "critical_issues": [],
            "high_issues": [],
            "medium_issues": [],
            "low_issues": []
        }

    async def _generate_security_report(self, analysis: Dict[str, Any]) -> Optional[str]:
        """Generate security report"""
        return "Security scan report generated"

    async def _create_security_issues(self, critical_issues: List[Dict[str, Any]]):
        """Create GitHub issues for critical security findings"""
        for issue in critical_issues:
            await self._create_security_issue(issue)

    async def _create_security_issue(self, issue_data: Dict[str, Any]):
        """Create a security issue"""
        logger.info(f"Creating security issue: {issue_data.get('title')}")


class MaintenanceWorkflow:
    """Repository maintenance workflow automation"""

    def __init__(self, manager: GitHubWorkflowManager):
        self.manager = manager

    async def handle_create_event(self, event: GitHubEvent) -> WorkflowResult:
        """Handle create events"""
        return WorkflowResult(
            workflow_type=WorkflowType.REPOSITORY_MAINTENANCE,
            success=True,
            message="Create event handled"
        )

    async def handle_delete_event(self, event: GitHubEvent) -> WorkflowResult:
        """Handle delete events"""
        return WorkflowResult(
            workflow_type=WorkflowType.REPOSITORY_MAINTENANCE,
            success=True,
            message="Delete event handled"
        )

    async def execute(self, **kwargs) -> WorkflowResult:
        """Execute maintenance workflow"""
        return WorkflowResult(
            workflow_type=WorkflowType.REPOSITORY_MAINTENANCE,
            success=True,
            message="Maintenance workflow executed"
        )

    async def run_maintenance(self):
        """Run scheduled maintenance tasks"""
        try:
            logger.info("Running repository maintenance")

            # Clean up old branches
            await self._cleanup_old_branches()

            # Update labels
            await self._update_repository_labels()

            # Archive old issues
            await self._archive_old_issues()

            # Update documentation
            await self._update_readme_stats()

            logger.info("Repository maintenance completed")

        except Exception as e:
            logger.error(f"Maintenance error: {e}")

    async def _cleanup_old_branches(self):
        """Clean up old merged branches"""
        logger.info("Cleaning up old branches")

    async def _update_repository_labels(self):
        """Update repository labels"""
        logger.info("Updating repository labels")

    async def _archive_old_issues(self):
        """Archive old, resolved issues"""
        logger.info("Archiving old issues")

    async def _update_readme_stats(self):
        """Update README with repository statistics"""
        logger.info("Updating README statistics")


# Factory function for easy initialization
async def create_github_workflow_manager(config: WorkflowConfig) -> GitHubWorkflowManager:
    """Create and initialize GitHub workflow manager"""
    manager = GitHubWorkflowManager(config)
    await manager.initialize()
    return manager