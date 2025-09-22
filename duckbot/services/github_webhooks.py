"""
GitHub Webhook Service for DuckBot Enhanced v4.2
Handles GitHub webhook events and provides automated responses and workflows
"""

import asyncio
import hashlib
import hmac
import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum

from ..integrations.github_integration import GitHubEventType, GitHubIssue, GitHubPullRequest, GitHubCommit
from ..core.cost_management import CostTracker

logger = logging.getLogger(__name__)

class WebhookAction(Enum):
    """Actions to take on webhook events"""
    CREATE_ISSUE = "create_issue"
    UPDATE_ISSUE = "update_issue"
    CREATE_PR = "create_pr"
    MERGE_PR = "merge_pr"
    PUSH_CODE = "push_code"
    CREATE_RELEASE = "create_release"
    ADD_LABEL = "add_label"
    ADD_COMMENT = "add_comment"
    TRIGGER_WORKFLOW = "trigger_workflow"

@dataclass
class WebhookRule:
    """Webhook processing rule"""
    event_type: GitHubEventType
    conditions: Dict[str, Any]
    actions: List[WebhookAction]
    enabled: bool = True

@dataclass
class WebhookEvent:
    """Processed webhook event"""
    event_type: GitHubEventType
    repository: str
    action: str
    payload: Dict[str, Any]
    timestamp: datetime
    signature: Optional[str] = None

class GitHubWebhookService:
    """Handles GitHub webhook events and automated responses"""

    def __init__(self, secret: Optional[str] = None, cost_tracker: Optional[CostTracker] = None):
        """
        Initialize webhook service

        Args:
            secret: Webhook secret for signature verification
            cost_tracker: Optional cost tracking instance
        """
        self.secret = secret or os.getenv("GITHUB_WEBHOOK_SECRET")
        self.cost_tracker = cost_tracker

        # Event handlers
        self.event_handlers: Dict[GitHubEventType, List[Callable]] = {}

        # Processing rules
        self.rules: List[WebhookRule] = []

        # Event history
        self.event_history: List[WebhookEvent] = []
        self.max_history = 1000

        # Processing stats
        self.events_processed = 0
        self.events_failed = 0
        self.actions_triggered = 0

        # Initialize default rules
        self._initialize_default_rules()

    def _initialize_default_rules(self):
        """Initialize default webhook processing rules"""
        default_rules = [
            # Issue automation rules
            WebhookRule(
                event_type=GitHubEventType.ISSUES,
                conditions={"action": "opened", "payload.issue.labels": []},
                actions=[WebhookAction.ADD_LABEL],
                enabled=True
            ),
            WebhookRule(
                event_type=GitHubEventType.ISSUES,
                conditions={"action": "opened", "payload.issue.body": {"contains": "bug"}},
                actions=[WebhookAction.ADD_LABEL, WebhookAction.ADD_COMMENT],
                enabled=True
            ),
            WebhookRule(
                event_type=GitHubEventType.ISSUES,
                conditions={"action": "opened", "payload.issue.body": {"contains": "feature request"}},
                actions=[WebhookAction.ADD_LABEL],
                enabled=True
            ),

            # PR automation rules
            WebhookRule(
                event_type=GitHubEventType.PULL_REQUEST,
                conditions={"action": "opened"},
                actions=[WebhookAction.ADD_COMMENT],
                enabled=True
            ),
            WebhookRule(
                event_type=GitHubEventType.PULL_REQUEST,
                conditions={"action": "closed", "payload.pull_request.merged": True},
                actions=[WebhookAction.ADD_LABEL],
                enabled=True
            ),

            # Push automation rules
            WebhookRule(
                event_type=GitHubEventType.PUSH,
                conditions={"payload.ref": "refs/heads/main"},
                actions=[WebhookAction.TRIGGER_WORKFLOW],
                enabled=True
            ),
            WebhookRule(
                event_type=GitHubEventType.PUSH,
                conditions={"payload.commits": {"length": ">10"}},
                actions=[WebhookAction.TRIGGER_WORKFLOW],
                enabled=True
            ),

            # Release automation rules
            WebhookRule(
                event_type=GitHubEventType.RELEASE,
                conditions={"action": "published"},
                actions=[WebhookAction.TRIGGER_WORKFLOW, WebhookAction.ADD_COMMENT],
                enabled=True
            )
        ]

        self.rules.extend(default_rules)

    def verify_signature(self, payload: bytes, signature: str) -> bool:
        """Verify GitHub webhook signature"""
        if not self.secret:
            logger.warning("No webhook secret configured, skipping signature verification")
            return True

        expected_signature = f"sha256={hmac.new(self.secret.encode(), payload, hashlib.sha256).hexdigest()}"
        return hmac.compare_digest(expected_signature, signature)

    def parse_webhook_event(self, headers: Dict[str, str], body: bytes) -> Optional[WebhookEvent]:
        """Parse and validate webhook event"""
        try:
            # Get event type
            event_type = headers.get("X-GitHub-Event")
            if not event_type:
                logger.error("Missing X-GitHub-Event header")
                return None

            # Verify signature
            signature = headers.get("X-Hub-Signature-256")
            if signature and not self.verify_signature(body, signature):
                logger.error("Invalid webhook signature")
                return None

            # Parse payload
            try:
                payload = json.loads(body.decode("utf-8"))
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON payload: {e}")
                return None

            # Create event object
            event = WebhookEvent(
                event_type=GitHubEventType(event_type),
                repository=payload.get("repository", {}).get("full_name", ""),
                action=payload.get("action", ""),
                payload=payload,
                timestamp=datetime.now(),
                signature=signature
            )

            return event

        except Exception as e:
            logger.error(f"Error parsing webhook event: {e}")
            return None

    async def process_webhook(self, headers: Dict[str, str], body: bytes) -> Dict[str, Any]:
        """Process incoming webhook event"""
        # Parse event
        event = self.parse_webhook_event(headers, body)
        if not event:
            return {"success": False, "error": "Invalid webhook event"}

        # Add to history
        self.event_history.append(event)
        if len(self.event_history) > self.max_history:
            self.event_history.pop(0)

        # Process event
        try:
            result = await self._process_event(event)
            self.events_processed += 1
            return result
        except Exception as e:
            logger.error(f"Error processing webhook event: {e}")
            self.events_failed += 1
            return {"success": False, "error": str(e)}

    async def _process_event(self, event: WebhookEvent) -> Dict[str, Any]:
        """Process individual webhook event"""
        triggered_actions = []

        # Find matching rules
        for rule in self.rules:
            if not rule.enabled or rule.event_type != event.event_type:
                continue

            if self._matches_conditions(rule.conditions, event.payload):
                # Execute rule actions
                for action in rule.actions:
                    try:
                        await self._execute_action(action, event)
                        triggered_actions.append(action.value)
                        self.actions_triggered += 1
                    except Exception as e:
                        logger.error(f"Error executing action {action.value}: {e}")

        # Call custom event handlers
        if event.event_type in self.event_handlers:
            for handler in self.event_handlers[event.event_type]:
                try:
                    await handler(event)
                except Exception as e:
                    logger.error(f"Error in custom handler: {e}")

        return {
            "success": True,
            "event_type": event.event_type.value,
            "repository": event.repository,
            "triggered_actions": triggered_actions,
            "timestamp": event.timestamp.isoformat()
        }

    def _matches_conditions(self, conditions: Dict[str, Any], payload: Dict[str, Any]) -> bool:
        """Check if payload matches rule conditions"""
        for key_path, expected_value in conditions.items():
            actual_value = self._get_nested_value(payload, key_path)
            if not self._match_condition(actual_value, expected_value):
                return False
        return True

    def _get_nested_value(self, data: Dict[str, Any], key_path: str) -> Any:
        """Get nested value from dictionary using dot notation"""
        keys = key_path.split(".")
        current = data

        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None

        return current

    def _match_condition(self, actual: Any, expected: Any) -> bool:
        """Check if actual value matches expected condition"""
        if isinstance(expected, dict):
            # Handle complex conditions
            for op, value in expected.items():
                if op == "contains":
                    return actual and value in str(actual)
                elif op == "length":
                    if value.startswith(">"):
                        return actual and len(actual) > int(value[1:])
                    elif value.startswith("<"):
                        return actual and len(actual) < int(value[1:])
        else:
            # Simple equality
            return actual == expected

        return False

    async def _execute_action(self, action: WebhookAction, event: WebhookEvent):
        """Execute webhook action"""
        logger.info(f"Executing action {action.value} for event {event.event_type.value}")

        if action == WebhookAction.CREATE_ISSUE:
            await self._handle_issue_creation(event)
        elif action == WebhookAction.UPDATE_ISSUE:
            await self._handle_issue_update(event)
        elif action == WebhookAction.CREATE_PR:
            await self._handle_pr_creation(event)
        elif action == WebhookAction.MERGE_PR:
            await self._handle_pr_merge(event)
        elif action == WebhookAction.PUSH_CODE:
            await self._handle_code_push(event)
        elif action == WebhookAction.CREATE_RELEASE:
            await self._handle_release_creation(event)
        elif action == WebhookAction.ADD_LABEL:
            await self._handle_label_addition(event)
        elif action == WebhookAction.ADD_COMMENT:
            await self._handle_comment_addition(event)
        elif action == WebhookAction.TRIGGER_WORKFLOW:
            await self._handle_workflow_trigger(event)

    async def _handle_issue_creation(self, event: WebhookEvent):
        """Handle issue creation action"""
        issue_data = event.payload.get("issue", {})
        title = issue_data.get("title", "")
        body = issue_data.get("body", "")
        labels = [label.get("name", "") for label in issue_data.get("labels", [])]

        # Auto-categorize issue
        if "bug" in body.lower() or "error" in body.lower():
            await self._add_label_to_issue(event.repository, issue_data["number"], "bug")
        elif "feature" in body.lower() or "enhancement" in body.lower():
            await self._add_label_to_issue(event.repository, issue_data["number"], "enhancement")
        elif "documentation" in body.lower():
            await self._add_label_to_issue(event.repository, issue_data["number"], "documentation")

        # Add welcome comment
        await self._add_comment_to_issue(event.repository, issue_data["number"],
            "Thank you for opening this issue! We'll review it and get back to you soon.")

    async def _handle_pr_creation(self, event: WebhookEvent):
        """Handle pull request creation action"""
        pr_data = event.payload.get("pull_request", {})
        title = pr_data.get("title", "")
        body = pr_data.get("body", "")

        # Add welcome comment
        await self._add_comment_to_pr(event.repository, pr_data["number"],
            "Thank you for your contribution! We'll review your pull request shortly.")

    async def _handle_code_push(self, event: WebhookEvent):
        """Handle code push action"""
        commits = event.payload.get("commits", [])
        branch = event.payload.get("ref", "").replace("refs/heads/", "")

        # Log significant pushes
        if len(commits) > 5:
            logger.info(f"Large push to {branch}: {len(commits)} commits")

    async def _handle_workflow_trigger(self, event: WebhookEvent):
        """Handle workflow trigger action"""
        # This would integrate with CI/CD systems
        logger.info(f"Triggering workflow for {event.repository} - {event.event_type.value}")

    async def _handle_label_addition(self, event: WebhookEvent):
        """Handle label addition action"""
        # Auto-label based on content
        pass

    async def _handle_comment_addition(self, event: WebhookEvent):
        """Handle comment addition action"""
        # Add automated comments
        pass

    async def _add_label_to_issue(self, repository: str, issue_number: int, label: str):
        """Add label to issue (requires GitHub API)"""
        logger.info(f"Adding label '{label}' to issue #{issue_number} in {repository}")
        # Implementation would use GitHub API to add label

    async def _add_comment_to_issue(self, repository: str, issue_number: int, comment: str):
        """Add comment to issue (requires GitHub API)"""
        logger.info(f"Adding comment to issue #{issue_number} in {repository}")
        # Implementation would use GitHub API to add comment

    async def _add_comment_to_pr(self, repository: str, pr_number: int, comment: str):
        """Add comment to pull request (requires GitHub API)"""
        logger.info(f"Adding comment to PR #{pr_number} in {repository}")
        # Implementation would use GitHub API to add comment

    def add_event_handler(self, event_type: GitHubEventType, handler: Callable):
        """Add custom event handler"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)

    def remove_event_handler(self, event_type: GitHubEventType, handler: Callable):
        """Remove custom event handler"""
        if event_type in self.event_handlers:
            self.event_handlers[event_type].remove(handler)

    def add_rule(self, rule: WebhookRule):
        """Add custom webhook rule"""
        self.rules.append(rule)

    def remove_rule(self, rule: WebhookRule):
        """Remove webhook rule"""
        if rule in self.rules:
            self.rules.remove(rule)

    def get_event_history(self, event_type: Optional[GitHubEventType] = None,
                          limit: int = 100) -> List[WebhookEvent]:
        """Get webhook event history"""
        history = self.event_history
        if event_type:
            history = [event for event in history if event.event_type == event_type]

        return history[-limit:]

    def get_statistics(self) -> Dict[str, Any]:
        """Get webhook service statistics"""
        event_types = {}
        for event in self.event_history:
            event_type = event.event_type.value
            event_types[event_type] = event_types.get(event_type, 0) + 1

        return {
            "events_processed": self.events_processed,
            "events_failed": self.events_failed,
            "actions_triggered": self.actions_triggered,
            "success_rate": (self.events_processed / (self.events_processed + self.events_failed) * 100) if (self.events_processed + self.events_failed) > 0 else 0,
            "event_types": event_types,
            "active_rules": len([rule for rule in self.rules if rule.enabled]),
            "total_rules": len(self.rules)
        }

    def export_configuration(self) -> Dict[str, Any]:
        """Export webhook service configuration"""
        return {
            "rules": [
                {
                    "event_type": rule.event_type.value,
                    "conditions": rule.conditions,
                    "actions": [action.value for action in rule.actions],
                    "enabled": rule.enabled
                }
                for rule in self.rules
            ],
            "statistics": self.get_statistics()
        }

    def import_configuration(self, config: Dict[str, Any]):
        """Import webhook service configuration"""
        self.rules.clear()
        self._initialize_default_rules()

        for rule_config in config.get("rules", []):
            rule = WebhookRule(
                event_type=GitHubEventType(rule_config["event_type"]),
                conditions=rule_config["conditions"],
                actions=[WebhookAction(action) for action in rule_config["actions"]],
                enabled=rule_config.get("enabled", True)
            )
            self.rules.append(rule)

# Global instance
webhook_service = GitHubWebhookService()

def get_webhook_service() -> GitHubWebhookService:
    """Get the global webhook service instance"""
    return webhook_service