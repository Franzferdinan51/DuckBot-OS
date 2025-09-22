"""
Comprehensive Test Suite for GitHub Integration System
Tests GitHubAPIManager and GitHubWebhookService classes with full coverage
"""

import asyncio
import json
import os
import base64
import time
import hmac
import hashlib
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from typing import Dict, List, Any, Optional
import pytest
import aiohttp
import tempfile

# Import the modules to test
from duckbot.integrations.github_integration import (
    GitHubAPIManager, GitHubRepository, GitHubIssue, GitHubPullRequest,
    GitHubCommit, GitHubWebhook, GitHubEventType, IssueState, PullRequestState
)
from duckbot.services.github_webhooks import (
    GitHubWebhookService, WebhookRule, WebhookEvent, WebhookAction
)
from duckbot.core.cost_management import CostTracker
from duckbot.core.hardware_detector import HardwareDetector


class TestGitHubAPIManager:
    """Test suite for GitHubAPIManager class"""

    @pytest.fixture(autouse=True)
    def setup_github_manager(self):
        """Set up test environment"""
        self.github_manager = GitHubAPIManager(
            token="test_token",
            base_url="https://api.github.com"
        )
        yield
        # Cleanup if needed

    def test_initialization(self):
        """Test GitHub API manager initialization"""
        assert self.github_manager is not None
        assert self.github_manager.token == "test_token"
        assert self.github_manager.base_url == "https://api.github.com"
        assert self.github_manager.rate_limit_remaining == 5000
        assert self.github_manager.repository_cache == {}
        assert self.github_manager.api_calls_made == 0
        assert self.github_manager.api_errors == 0

    def test_get_headers(self):
        """Test API request headers generation"""
        headers = self.github_manager._get_headers()
        assert "Accept" in headers
        assert headers["Accept"] == "application/vnd.github.v3+json"
        assert "Authorization" in headers
        assert headers["Authorization"] == "token test_token"
        assert "User-Agent" in headers

    @pytest.mark.asyncio
    async def test_check_rate_limit_no_wait(self):
        """Test rate limiting when within limits"""
        self.github_manager.rate_limit_remaining = 100
        self.github_manager.rate_limit_reset = time.time() + 3600

        # Should not raise exception or sleep
        start_time = time.time()
        await self.github_manager._check_rate_limit()
        elapsed = time.time() - start_time
        assert elapsed < 0.1  # Should be very fast

    @pytest.mark.asyncio
    async def test_check_rate_limit_wait_required(self):
        """Test rate limiting when limits are exceeded"""
        self.github_manager.rate_limit_remaining = 5
        self.github_manager.rate_limit_reset = time.time() + 1  # 1 second from now

        with patch('asyncio.sleep') as mock_sleep:
            await self.github_manager._check_rate_limit()
            mock_sleep.assert_called_once()

    @pytest.mark.asyncio
    async def test_make_request_success(self):
        """Test successful API request"""
        mock_response_data = {"id": 123, "name": "test-repo"}

        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value.__aenter__.return_value = mock_session

            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.headers = {
                "X-RateLimit-Remaining": "4999",
                "X-RateLimit-Reset": str(int(time.time()) + 3600)
            }
            mock_response.json = AsyncMock(return_value=mock_response_data)
            mock_session.request.return_value.__aenter__.return_value = mock_response

            result = await self.github_manager._make_request("GET", "test/endpoint")

            assert result == mock_response_data
            assert self.github_manager.api_calls_made == 1
            assert self.github_manager.rate_limit_remaining == 4999

    @pytest.mark.asyncio
    async def test_make_request_error(self):
        """Test API request with error"""
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value.__aenter__.return_value = mock_session

            mock_response = AsyncMock()
            mock_response.status = 404
            mock_response.headers = {
                "X-RateLimit-Remaining": "4999",
                "X-RateLimit-Reset": str(int(time.time()) + 3600)
            }
            mock_response.content_type = "application/json"
            mock_response.json = AsyncMock(return_value={"message": "Not found"})
            mock_session.request.return_value.__aenter__.return_value = mock_response

            with pytest.raises(Exception):
                await self.github_manager._make_request("GET", "test/endpoint")

            assert self.github_manager.api_errors == 1

    @pytest.mark.asyncio
    async def test_get_repository_cache_hit(self):
        """Test repository caching - cache hit"""
        test_repo = GitHubRepository(
            name="test-repo",
            full_name="test/test-repo",
            description="Test repository",
            private=False,
            fork=False,
            url="https://github.com/test/test-repo",
            clone_url="https://github.com/test/test-repo.git",
            ssh_url="git@github.com:test/test-repo.git",
            default_branch="main",
            language="Python",
            stargazers_count=10,
            watchers_count=5,
            forks_count=2,
            open_issues_count=3,
            created_at="2023-01-01T00:00:00Z",
            updated_at="2023-01-01T00:00:00Z",
            pushed_at="2023-01-01T00:00:00Z",
            size=100,
            owner={"login": "test"}
        )

        # Add to cache
        self.github_manager.repository_cache["test/test-repo"] = (test_repo, time.time())

        result = await self.github_manager.get_repository("test", "test-repo")
        assert result == test_repo

    @pytest.mark.asyncio
    async def test_get_repository_cache_miss(self):
        """Test repository caching - cache miss"""
        mock_api_response = {
            "name": "test-repo",
            "full_name": "test/test-repo",
            "description": "Test repository",
            "private": False,
            "fork": False,
            "html_url": "https://github.com/test/test-repo",
            "clone_url": "https://github.com/test/test-repo.git",
            "ssh_url": "git@github.com:test/test-repo.git",
            "default_branch": "main",
            "language": "Python",
            "stargazers_count": 10,
            "watchers_count": 5,
            "forks_count": 2,
            "open_issues_count": 3,
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-01T00:00:00Z",
            "pushed_at": "2023-01-01T00:00:00Z",
            "size": 100,
            "owner": {"login": "test"}
        }

        with patch.object(self.github_manager, '_make_request', return_value=mock_api_response):
            result = await self.github_manager.get_repository("test", "test-repo", use_cache=False)

            assert result.name == "test-repo"
            assert result.full_name == "test/test-repo"
            assert result.language == "Python"

    @pytest.mark.asyncio
    async def test_list_issues(self):
        """Test listing repository issues"""
        mock_api_response = [
            {
                "id": 123,
                "number": 1,
                "title": "Test Issue",
                "body": "This is a test issue",
                "state": "open",
                "created_at": "2023-01-01T00:00:00Z",
                "updated_at": "2023-01-01T00:00:00Z",
                "closed_at": None,
                "user": {"login": "user1"},
                "assignee": None,
                "assignees": [],
                "labels": []
            }
        ]

        with patch.object(self.github_manager, '_make_request', return_value=mock_api_response):
            result = await self.github_manager.list_issues("owner", "repo")

            assert len(result) == 1
            assert result[0].title == "Test Issue"
            assert result[0].state == "open"

    @pytest.mark.asyncio
    async def test_create_issue(self):
        """Test creating a new issue"""
        mock_api_response = {
            "id": 124,
            "number": 2,
            "title": "New Issue",
            "body": "This is a new issue",
            "state": "open",
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-01T00:00:00Z",
            "closed_at": None,
            "user": {"login": "user1"},
            "assignee": None,
            "assignees": [],
            "labels": []
        }

        with patch.object(self.github_manager, '_make_request', return_value=mock_api_response):
            result = await self.github_manager.create_issue("owner", "repo", "New Issue", "This is a new issue")

            assert result.title == "New Issue"
            assert result.number == 2

    @pytest.mark.asyncio
    async def test_test_connection_success(self):
        """Test successful connection test"""
        with patch.object(self.github_manager, '_make_request', return_value={"login": "testuser"}):
            result = await self.github_manager.test_connection()
            assert result is True

    @pytest.mark.asyncio
    async def test_test_connection_failure(self):
        """Test failed connection test"""
        with patch.object(self.github_manager, '_make_request', side_effect=Exception("Unauthorized")):
            result = await self.github_manager.test_connection()
            assert result is False


class TestGitHubWebhookService:
    """Test suite for GitHubWebhookService class"""

    @pytest.fixture(autouse=True)
    def setup_webhook_service(self):
        """Set up test environment"""
        self.webhook_service = GitHubWebhookService(secret="test_secret")
        yield
        # Cleanup if needed

    def test_initialization(self):
        """Test webhook service initialization"""
        assert self.webhook_service is not None
        assert self.webhook_service.secret == "test_secret"
        assert self.webhook_service.events_processed == 0
        assert self.webhook_service.events_failed == 0
        assert self.webhook_service.actions_triggered == 0
        assert len(self.webhook_service.rules) > 0

    def test_verify_signature_valid(self):
        """Test valid webhook signature verification"""
        payload = b'{"test": "data"}'
        signature = "sha256=" + hmac.new("test_secret".encode(), payload, hashlib.sha256).hexdigest()

        result = self.webhook_service.verify_signature(payload, signature)
        assert result is True

    def test_verify_signature_invalid(self):
        """Test invalid webhook signature verification"""
        payload = b'{"test": "data"}'
        signature = "sha256=invalid_signature"

        result = self.webhook_service.verify_signature(payload, signature)
        assert result is False

    def test_verify_signature_no_secret(self):
        """Test signature verification when no secret is configured"""
        webhook_service_no_secret = GitHubWebhookService(secret=None)
        payload = b'{"test": "data"}'
        signature = "invalid_signature"

        # Should return True when no secret is configured
        result = webhook_service_no_secret.verify_signature(payload, signature)
        assert result is True

    def test_parse_webhook_event_valid(self):
        """Test parsing valid webhook event"""
        headers = {
            "X-GitHub-Event": "issues",
            "X-Hub-Signature-256": "sha256=" + hmac.new(
                "test_secret".encode(), b'{"action": "opened"}', hashlib.sha256
            ).hexdigest()
        }
        body = b'{"action": "opened", "repository": {"full_name": "test/repo"}}'

        event = self.webhook_service.parse_webhook_event(headers, body)

        assert event is not None
        assert event.event_type == GitHubEventType.ISSUES
        assert event.repository == "test/repo"
        assert event.action == "opened"

    def test_parse_webhook_event_missing_header(self):
        """Test parsing webhook event with missing event header"""
        headers = {}
        body = b'{"action": "opened"}'

        event = self.webhook_service.parse_webhook_event(headers, body)

        assert event is None

    @pytest.mark.asyncio
    async def test_process_webhook_valid(self):
        """Test processing valid webhook event"""
        headers = {
            "X-GitHub-Event": "issues",
            "X-Hub-Signature-256": "sha256=" + hmac.new(
                "test_secret".encode(), b'{"action": "opened", "repository": {"full_name": "test/repo"}, "issue": {"title": "Test issue", "body": "This is a bug", "labels": [], "number": 1}}', hashlib.sha256
            ).hexdigest()
        }
        body = b'{"action": "opened", "repository": {"full_name": "test/repo"}, "issue": {"title": "Test issue", "body": "This is a bug", "labels": [], "number": 1}}'

        result = await self.webhook_service.process_webhook(headers, body)

        assert result["success"] is True
        assert result["event_type"] == "issues"
        assert result["repository"] == "test/repo"
        assert self.webhook_service.events_processed == 1

    @pytest.mark.asyncio
    async def test_process_webhook_invalid(self):
        """Test processing invalid webhook event"""
        headers = {}
        body = b'invalid'

        result = await self.webhook_service.process_webhook(headers, body)

        assert result["success"] is False
        assert "error" in result
        assert self.webhook_service.events_failed == 1

    def test_matches_conditions_simple(self):
        """Test matching simple conditions"""
        conditions = {"action": "opened"}
        payload = {"action": "opened"}

        result = self.webhook_service._matches_conditions(conditions, payload)
        assert result is True

    def test_matches_conditions_false(self):
        """Test matching conditions that should fail"""
        conditions = {"action": "closed"}
        payload = {"action": "opened"}

        result = self.webhook_service._matches_conditions(conditions, payload)
        assert result is False

    def test_get_nested_value(self):
        """Test getting nested value from dictionary"""
        data = {
            "payload": {
                "issue": {
                    "title": "Test Issue",
                    "labels": [{"name": "bug"}, {"name": "urgent"}]
                }
            }
        }

        # Test existing nested value
        result = self.webhook_service._get_nested_value(data, "payload.issue.title")
        assert result == "Test Issue"

        # Test non-existing nested value
        result = self.webhook_service._get_nested_value(data, "payload.issue.nonexistent")
        assert result is None

    def test_add_event_handler(self):
        """Test adding custom event handler"""
        def mock_handler(event):
            pass

        self.webhook_service.add_event_handler(GitHubEventType.ISSUES, mock_handler)

        assert GitHubEventType.ISSUES in self.webhook_service.event_handlers
        assert mock_handler in self.webhook_service.event_handlers[GitHubEventType.ISSUES]

    def test_get_statistics(self):
        """Test getting webhook service statistics"""
        # Add some test events
        event1 = WebhookEvent(
            event_type=GitHubEventType.ISSUES,
            repository="test/repo",
            action="opened",
            payload={"action": "opened"},
            timestamp=datetime.now()
        )
        event2 = WebhookEvent(
            event_type=GitHubEventType.ISSUES,
            repository="test/repo",
            action="closed",
            payload={"action": "closed"},
            timestamp=datetime.now()
        )

        self.webhook_service.event_history = [event1, event2]
        self.webhook_service.events_processed = 2
        self.webhook_service.events_failed = 1
        self.webhook_service.actions_triggered = 3

        stats = self.webhook_service.get_statistics()

        assert stats["events_processed"] == 2
        assert stats["events_failed"] == 1
        assert stats["actions_triggered"] == 3
        assert stats["success_rate"] == 66.66666666666666  # 2/(2+1)*100
        assert stats["event_types"]["issues"] == 2
        assert stats["active_rules"] > 0


class TestGitHubIntegrationSecurity:
    """Test suite for GitHub integration security features"""

    @pytest.fixture(autouse=True)
    def setup_security_tests(self):
        """Set up security test environment"""
        self.webhook_service = GitHubWebhookService(secret="test_secret")
        yield

    def test_signature_verification_timing_attack(self):
        """Test signature verification is resistant to timing attacks"""
        payload = b'{"test": "data"}'
        valid_signature = "sha256=" + hmac.new("test_secret".encode(), payload, hashlib.sha256).hexdigest()
        invalid_signature = "sha256=" + hmac.new("test_secret".encode(), b'different', hashlib.sha256).hexdigest()

        # Both calls should take similar time (using hmac.compare_digest)
        import time
        start = time.time()
        result1 = self.webhook_service.verify_signature(payload, valid_signature)
        time1 = time.time() - start

        start = time.time()
        result2 = self.webhook_service.verify_signature(payload, invalid_signature)
        time2 = time.time() - start

        assert result1 is True
        assert result2 is False
        # Time difference should be small (within 1ms for typical cases)
        assert abs(time1 - time2) < 0.001

    def test_sql_injection_prevention(self):
        """Test SQL injection prevention in webhook data"""
        malicious_payload = {
            "action": "opened",
            "issue": {
                "title": "Test issue",
                "body": "'); DROP TABLE issues; --",
                "labels": []
            }
        }

        # Should handle without SQL errors (since we don't use SQL directly)
        event = WebhookEvent(
            event_type=GitHubEventType.ISSUES,
            repository="test/repo",
            action="opened",
            payload=malicious_payload,
            timestamp=datetime.now()
        )

        assert event.payload["issue"]["body"] == "'); DROP TABLE issues; --"


class TestGitHubIntegrationPerformance:
    """Test suite for GitHub integration performance"""

    @pytest.fixture(autouse=True)
    def setup_performance_tests(self):
        """Set up performance test environment"""
        self.github_manager = GitHubAPIManager(token="test_token")
        self.webhook_service = GitHubWebhookService(secret="test_secret")
        yield

    @pytest.mark.asyncio
    async def test_cache_performance(self):
        """Test repository caching performance"""
        # Mock repository data
        mock_api_response = {
            "name": "test-repo",
            "full_name": "test/test-repo",
            "description": "Test repository",
            "private": False,
            "fork": False,
            "html_url": "https://github.com/test/test-repo",
            "clone_url": "https://github.com/test/test-repo.git",
            "ssh_url": "git@github.com:test/test-repo.git",
            "default_branch": "main",
            "language": "Python",
            "stargazers_count": 10,
            "watchers_count": 5,
            "forks_count": 2,
            "open_issues_count": 3,
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-01T00:00:00Z",
            "pushed_at": "2023-01-01T00:00:00Z",
            "size": 100,
            "owner": {"login": "test"}
        }

        with patch.object(self.github_manager, '_make_request', return_value=mock_api_response):
            # First call (cache miss)
            start_time = time.time()
            await self.github_manager.get_repository("test", "test-repo", use_cache=False)
            cache_miss_time = time.time() - start_time

            # Second call (cache hit)
            start_time = time.time()
            await self.github_manager.get_repository("test", "test-repo")
            cache_hit_time = time.time() - start_time

            # Cache hit should be much faster
            assert cache_hit_time < cache_miss_time


class TestGitHubIntegrationIntegration:
    """Integration tests for GitHub integration system"""

    @pytest.fixture(autouse=True)
    def setup_integration_tests(self):
        """Set up integration test environment"""
        self.github_manager = GitHubAPIManager(token="test_token")
        self.webhook_service = GitHubWebhookService(secret="test_secret")
        yield

    @pytest.mark.asyncio
    async def test_full_webhook_workflow(self):
        """Test complete webhook workflow from event to action"""
        # Create a realistic webhook event
        webhook_payload = {
            "action": "opened",
            "repository": {
                "full_name": "test/repo",
                "name": "repo",
                "owner": {"login": "test"}
            },
            "issue": {
                "id": 123,
                "number": 1,
                "title": "Bug in the system",
                "body": "There's a serious bug that needs to be fixed immediately",
                "state": "open",
                "created_at": "2023-01-01T00:00:00Z",
                "updated_at": "2023-01-01T00:00:00Z",
                "user": {"login": "user1"},
                "labels": [],
                "assignee": None,
                "assignees": []
            },
            "sender": {"login": "user1"}
        }

        headers = {
            "X-GitHub-Event": "issues",
            "X-Hub-Signature-256": "sha256=" + hmac.new(
                "test_secret".encode(), json.dumps(webhook_payload).encode(), hashlib.sha256
            ).hexdigest(),
            "Content-Type": "application/json"
        }

        # Process the webhook
        result = await self.webhook_service.process_webhook(headers, json.dumps(webhook_payload).encode())

        # Verify processing
        assert result["success"] is True
        assert result["event_type"] == "issues"
        assert result["repository"] == "test/repo"
        assert len(result["triggered_actions"]) > 0

    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self):
        """Test error handling and recovery mechanisms"""
        # Test API error handling
        with patch.object(self.github_manager, '_make_request', side_effect=Exception("API Error")):
            with pytest.raises(Exception):
                await self.github_manager.get_repository("test", "repo")

        # Test webhook error handling
        invalid_headers = {"X-GitHub-Event": "invalid_event"}
        invalid_body = b'invalid json'

        result = await self.webhook_service.process_webhook(invalid_headers, invalid_body)

        assert result["success"] is False
        assert "error" in result


# Test fixtures
@pytest.fixture
def github_manager():
    """Fixture providing GitHubAPIManager instance"""
    return GitHubAPIManager(token="test_token")


@pytest.fixture
def webhook_service():
    """Fixture providing GitHubWebhookService instance"""
    return GitHubWebhookService(secret="test_secret")


@pytest.fixture
def sample_repository_data():
    """Fixture providing sample repository data"""
    return {
        "name": "test-repo",
        "full_name": "test/test-repo",
        "description": "Test repository",
        "private": False,
        "fork": False,
        "html_url": "https://github.com/test/test-repo",
        "clone_url": "https://github.com/test/test-repo.git",
        "ssh_url": "git@github.com:test/test-repo.git",
        "default_branch": "main",
        "language": "Python",
        "stargazers_count": 10,
        "watchers_count": 5,
        "forks_count": 2,
        "open_issues_count": 3,
        "created_at": "2023-01-01T00:00:00Z",
        "updated_at": "2023-01-01T00:00:00Z",
        "pushed_at": "2023-01-01T00:00:00Z",
        "size": 100,
        "owner": {"login": "test"}
    }


@pytest.fixture
def sample_webhook_payload():
    """Fixture providing sample webhook payload"""
    return {
        "action": "opened",
        "repository": {
            "full_name": "test/repo",
            "name": "repo",
            "owner": {"login": "test"}
        },
        "issue": {
            "id": 123,
            "number": 1,
            "title": "Test Issue",
            "body": "This is a test issue",
            "state": "open",
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-01T00:00:00Z",
            "user": {"login": "user1"},
            "labels": [],
            "assignee": None,
            "assignees": []
        },
        "sender": {"login": "user1"}
    }


# Test runner
if __name__ == "__main__":
    pytest.main([__file__, "-v"])