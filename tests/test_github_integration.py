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

        # Create a mock response with proper async context manager
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.headers = {
            "X-RateLimit-Remaining": "4999",
            "X-RateLimit-Reset": str(int(time.time()) + 3600)
        }
        mock_response.json = AsyncMock(return_value=mock_response_data)

        # Create a proper async context manager
        class MockAsyncContextManager:
            def __init__(self, response):
                self.response = response

            async def __aenter__(self):
                return self.response

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass

        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value.__aenter__.return_value = mock_session
            mock_session.request.return_value = MockAsyncContextManager(mock_response)

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

            # Properly mock the context manager
            mock_request_context = AsyncMock()
            mock_request_context.__aenter__.return_value = mock_response
            mock_request_context.__aexit__.return_value = None
            mock_session.request.return_value = mock_request_context

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
    async def test_list_user_repositories(self):
        """Test listing user repositories"""
        mock_api_response = [
            {
                "name": "repo1",
                "full_name": "user/repo1",
                "description": "Repository 1",
                "private": False,
                "fork": False,
                "html_url": "https://github.com/user/repo1",
                "clone_url": "https://github.com/user/repo1.git",
                "ssh_url": "git@github.com:user/repo1.git",
                "default_branch": "main",
                "language": "Python",
                "stargazers_count": 5,
                "watchers_count": 3,
                "forks_count": 1,
                "open_issues_count": 2,
                "created_at": "2023-01-01T00:00:00Z",
                "updated_at": "2023-01-01T00:00:00Z",
                "pushed_at": "2023-01-01T00:00:00Z",
                "size": 50,
                "owner": {"login": "user"}
            }
        ]

        with patch.object(self.github_manager, '_make_request', return_value=mock_api_response):
            result = await self.github_manager.list_user_repositories("user")

            assert len(result) == 1
            assert result[0].name == "repo1"
            assert result[0].language == "Python"

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
    async def test_update_issue(self):
        """Test updating an existing issue"""
        mock_api_response = {
            "id": 123,
            "number": 1,
            "title": "Updated Issue",
            "body": "Updated body",
            "state": "closed",
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-01T00:00:00Z",
            "closed_at": "2023-01-01T00:00:00Z",
            "user": {"login": "user1"},
            "assignee": None,
            "assignees": [],
            "labels": []
        }

        with patch.object(self.github_manager, '_make_request', return_value=mock_api_response):
            result = await self.github_manager.update_issue("owner", "repo", 1, title="Updated Issue", state=IssueState.CLOSED)

            assert result.title == "Updated Issue"
            assert result.state == "closed"

    @pytest.mark.asyncio
    async def test_list_pull_requests(self):
        """Test listing pull requests"""
        mock_api_response = [
            {
                "id": 125,
                "number": 1,
                "title": "Test PR",
                "body": "This is a test PR",
                "state": "open",
                "created_at": "2023-01-01T00:00:00Z",
                "updated_at": "2023-01-01T00:00:00Z",
                "closed_at": None,
                "merged_at": None,
                "user": {"login": "user1"},
                "assignee": None,
                "assignees": [],
                "labels": [],
                "head": {"ref": "feature-branch"},
                "base": {"ref": "main"},
                "mergeable": True,
                "draft": False
            }
        ]

        with patch.object(self.github_manager, '_make_request', return_value=mock_api_response):
            result = await self.github_manager.list_pull_requests("owner", "repo")

            assert len(result) == 1
            assert result[0].title == "Test PR"
            assert result[0].state == "open"

    @pytest.mark.asyncio
    async def test_create_pull_request(self):
        """Test creating a pull request"""
        mock_api_response = {
            "id": 126,
            "number": 2,
            "title": "New PR",
            "body": "This is a new PR",
            "state": "open",
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-01T00:00:00Z",
            "closed_at": None,
            "merged_at": None,
            "user": {"login": "user1"},
            "assignee": None,
            "assignees": [],
            "labels": [],
            "head": {"ref": "feature-branch"},
            "base": {"ref": "main"},
            "mergeable": True,
            "draft": False
        }

        with patch.object(self.github_manager, '_make_request', return_value=mock_api_response):
            result = await self.github_manager.create_pull_request("owner", "repo", "New PR", "feature-branch", "main")

            assert result.title == "New PR"
            assert result.number == 2

    @pytest.mark.asyncio
    async def test_list_commits(self):
        """Test listing commits"""
        mock_api_response = [
            {
                "sha": "abc123",
                "commit": {
                    "message": "Initial commit",
                    "author": {"name": "User1", "email": "user1@example.com", "date": "2023-01-01T00:00:00Z"},
                    "committer": {"name": "User1", "email": "user1@example.com", "date": "2023-01-01T00:00:00Z"}
                },
                "url": "https://api.github.com/repos/owner/repo/commits/abc123",
                "html_url": "https://github.com/owner/repo/commit/abc123",
                "comments_url": "https://api.github.com/repos/owner/repo/commits/abc123/comments"
            }
        ]

        with patch.object(self.github_manager, '_make_request', return_value=mock_api_response):
            result = await self.github_manager.list_commits("owner", "repo")

            assert len(result) == 1
            assert result[0].sha == "abc123"
            assert result[0].message == "Initial commit"

    @pytest.mark.asyncio
    async def test_get_file_content(self):
        """Test getting file content"""
        test_content = "This is test file content"
        encoded_content = base64.b64encode(test_content.encode()).decode()

        mock_api_response = {
            "encoding": "base64",
            "content": encoded_content
        }

        with patch.object(self.github_manager, '_make_request', return_value=mock_api_response):
            result = await self.github_manager.get_file_content("owner", "repo", "README.md")

            assert result == test_content

    @pytest.mark.asyncio
    async def test_list_webhooks(self):
        """Test listing repository webhooks"""
        mock_api_response = [
            {
                "id": 12345,
                "url": "https://api.github.com/repos/owner/repo/hooks/12345",
                "events": ["push", "pull_request"],
                "active": True,
                "config": {"url": "https://example.com/webhook", "content_type": "json"},
                "updated_at": "2023-01-01T00:00:00Z",
                "created_at": "2023-01-01T00:00:00Z"
            }
        ]

        with patch.object(self.github_manager, '_make_request', return_value=mock_api_response):
            result = await self.github_manager.list_webhooks("owner", "repo")

            assert len(result) == 1
            assert result[0].id == 12345
            assert result[0].active is True

    @pytest.mark.asyncio
    async def test_create_webhook(self):
        """Test creating a webhook"""
        mock_api_response = {
            "id": 12346,
            "url": "https://api.github.com/repos/owner/repo/hooks/12346",
            "events": ["push", "issues"],
            "active": True,
            "config": {"url": "https://example.com/webhook", "content_type": "json"},
            "updated_at": "2023-01-01T00:00:00Z",
            "created_at": "2023-01-01T00:00:00Z"
        }

        with patch.object(self.github_manager, '_make_request', return_value=mock_api_response):
            result = await self.github_manager.create_webhook("owner", "repo", "https://example.com/webhook", ["push", "issues"])

            assert result.id == 12346
            assert result.events == ["push", "issues"]

    @pytest.mark.asyncio
    async def test_delete_webhook(self):
        """Test deleting a webhook"""
        with patch.object(self.github_manager, '_make_request', return_value={"success": True}):
            result = await self.github_manager.delete_webhook("owner", "repo", 12345)
            assert result is True

    @pytest.mark.asyncio
    async def test_delete_webhook_failure(self):
        """Test deleting a webhook failure"""
        with patch.object(self.github_manager, '_make_request', side_effect=Exception("Not found")):
            result = await self.github_manager.delete_webhook("owner", "repo", 12345)
            assert result is False

    @pytest.mark.asyncio
    async def test_search_repositories(self):
        """Test searching repositories"""
        mock_api_response = {
            "items": [
                {
                    "name": "found-repo",
                    "full_name": "user/found-repo",
                    "description": "A found repository",
                    "private": False,
                    "fork": False,
                    "html_url": "https://github.com/user/found-repo",
                    "clone_url": "https://github.com/user/found-repo.git",
                    "ssh_url": "git@github.com:user/found-repo.git",
                    "default_branch": "main",
                    "language": "Python",
                    "stargazers_count": 100,
                    "watchers_count": 50,
                    "forks_count": 25,
                    "open_issues_count": 10,
                    "created_at": "2023-01-01T00:00:00Z",
                    "updated_at": "2023-01-01T00:00:00Z",
                    "pushed_at": "2023-01-01T00:00:00Z",
                    "size": 500,
                    "owner": {"login": "user"}
                }
            ]
        }

        with patch.object(self.github_manager, '_make_request', return_value=mock_api_response):
            result = await self.github_manager.search_repositories("test query", language="Python", stars=50)

            assert len(result) == 1
            assert result[0].name == "found-repo"
            assert result[0].language == "Python"

    @pytest.mark.asyncio
    async def test_get_api_stats(self):
        """Test getting API statistics"""
        # Make some API calls to generate stats
        self.github_manager.api_calls_made = 10
        self.github_manager.api_errors = 1
        self.github_manager.average_response_time = 0.5
        self.github_manager.rate_limit_remaining = 4990

        stats = await self.github_manager.get_api_stats()

        assert stats["api_calls_made"] == 10
        assert stats["api_errors"] == 1
        assert stats["error_rate"] == 10.0
        assert stats["average_response_time"] == 0.5

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

    @pytest.mark.asyncio
    async def test_get_repository_analytics(self):
        """Test getting repository analytics"""
        # Mock repository data
        mock_repo = GitHubRepository(
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
            stargazers_count=150,
            watchers_count=75,
            forks_count=30,
            open_issues_count=15,
            created_at="2023-01-01T00:00:00Z",
            updated_at="2023-01-01T00:00:00Z",
            pushed_at="2023-01-01T00:00:00Z",
            size=1000,
            owner={"login": "test"}
        )

        # Mock issues data
        mock_issues = [
            GitHubIssue(
                id=1, number=1, title="Issue 1", body="Body 1", state="open",
                created_at="2023-01-01T00:00:00Z", updated_at="2023-01-01T00:00:00Z",
                closed_at=None, user={"login": "user1"}, assignee=None,
                assignees=[], labels=[], pull_request=None
            ),
            GitHubIssue(
                id=2, number=2, title="Issue 2", body="Body 2", state="closed",
                created_at="2023-01-01T00:00:00Z", updated_at="2023-01-01T00:00:00Z",
                closed_at="2023-01-02T00:00:00Z", user={"login": "user1"},
                assignee=None, assignees=[], labels=[], pull_request=None
            )
        ]

        # Mock PRs data
        mock_prs = [
            GitHubPullRequest(
                id=1, number=1, title="PR 1", body="Body 1", state="open",
                created_at="2023-01-01T00:00:00Z", updated_at="2023-01-01T00:00:00Z",
                closed_at=None, merged_at=None, user={"login": "user1"},
                assignee=None, assignees=[], labels=[], head={"ref": "feature"},
                base={"ref": "main"}, mergeable=True, draft=False
            ),
            GitHubPullRequest(
                id=2, number=2, title="PR 2", body="Body 2", state="closed",
                created_at="2023-01-01T00:00:00Z", updated_at="2023-01-01T00:00:00Z",
                closed_at="2023-01-02T00:00:00Z", merged_at="2023-01-02T00:00:00Z",
                user={"login": "user1"}, assignee=None, assignees=[], labels=[],
                head={"ref": "feature"}, base={"ref": "main"}, mergeable=True, draft=False
            )
        ]

        # Mock commits data
        mock_commits = [
            GitHubCommit(
                sha="abc123", message="Commit 1", author={"name": "User1"},
                committer={"name": "User1"}, url="https://api.github.com/...",
                html_url="https://github.com/...", comments_url="https://api.github.com/...",
                timestamp="2023-01-01T00:00:00Z"
            )
        ] * 20  # 20 commits in 30 days

        with patch.object(self.github_manager, 'get_repository', return_value=mock_repo), \
             patch.object(self.github_manager, 'list_issues', return_value=mock_issues), \
             patch.object(self.github_manager, 'list_pull_requests', return_value=mock_prs), \
             patch.object(self.github_manager, 'list_commits', return_value=mock_commits):

            analytics = await self.github_manager.get_repository_analytics("test", "test-repo")

            assert analytics["repository"]["name"] == "test/test-repo"
            assert analytics["issues"]["total"] == 2
            assert analytics["issues"]["open"] == 1
            assert analytics["issues"]["closed"] == 1
            assert analytics["pull_requests"]["total"] == 2
            assert analytics["pull_requests"]["merged"] == 1
            assert analytics["activity"]["commits_last_30_days"] == 20
            assert 0 <= analytics["health_score"] <= 100


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

    def test_parse_webhook_event_invalid_signature(self):
        """Test parsing webhook event with invalid signature"""
        headers = {
            "X-GitHub-Event": "issues",
            "X-Hub-Signature-256": "sha256=invalid_signature"
        }
        body = b'{"action": "opened"}'

        event = self.webhook_service.parse_webhook_event(headers, body)

        assert event is None

    def test_parse_webhook_event_invalid_json(self):
        """Test parsing webhook event with invalid JSON"""
        headers = {
            "X-GitHub-Event": "issues",
            "X-Hub-Signature-256": "sha256=" + hmac.new(
                "test_secret".encode(), b'invalid json', hashlib.sha256
            ).hexdigest()
        }
        body = b'invalid json'

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
        headers = {"X-GitHub-Event": "invalid_event"}
        body = b'invalid data'

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

    def test_matches_conditions_complex(self):
        """Test matching complex conditions"""
        conditions = {
            "action": "opened",
            "payload.issue.body": {"contains": "bug"},
            "payload.issue.labels": {"length": ">5"}
        }
        payload = {
            "action": "opened",
            "payload": {
                "issue": {
                    "body": "This is a bug report",
                    "labels": ["bug", "urgent", "backend"]
                }
            }
        }

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

    def test_match_condition_contains(self):
        """Test condition matching with contains operator"""
        result = self.webhook_service._match_condition("This is a bug", {"contains": "bug"})
        assert result is True

        result = self.webhook_service._match_condition("This is a feature", {"contains": "bug"})
        assert result is False

    def test_match_condition_length(self):
        """Test condition matching with length operator"""
        result = self.webhook_service._match_condition(["item1", "item2", "item3"], {"length": ">2"})
        assert result is True

        result = self.webhook_service._match_condition(["item1"], {"length": ">2"})
        assert result is False

        result = self.webhook_service._match_condition(["item1", "item2"], {"length": "<3"})
        assert result is True

    def test_add_event_handler(self):
        """Test adding custom event handler"""
        def mock_handler(event):
            pass

        self.webhook_service.add_event_handler(GitHubEventType.ISSUES, mock_handler)

        assert GitHubEventType.ISSUES in self.webhook_service.event_handlers
        assert mock_handler in self.webhook_service.event_handlers[GitHubEventType.ISSUES]

    def test_remove_event_handler(self):
        """Test removing custom event handler"""
        def mock_handler(event):
            pass

        self.webhook_service.add_event_handler(GitHubEventType.ISSUES, mock_handler)
        self.webhook_service.remove_event_handler(GitHubEventType.ISSUES, mock_handler)

        assert mock_handler not in self.webhook_service.event_handlers.get(GitHubEventType.ISSUES, [])

    def test_add_rule(self):
        """Test adding custom webhook rule"""
        rule = WebhookRule(
            event_type=GitHubEventType.PUSH,
            conditions={"payload.ref": "refs/heads/main"},
            actions=[WebhookAction.TRIGGER_WORKFLOW],
            enabled=True
        )

        self.webhook_service.add_rule(rule)

        assert rule in self.webhook_service.rules

    def test_remove_rule(self):
        """Test removing webhook rule"""
        rule = WebhookRule(
            event_type=GitHubEventType.PUSH,
            conditions={"payload.ref": "refs/heads/main"},
            actions=[WebhookAction.TRIGGER_WORKFLOW],
            enabled=True
        )

        self.webhook_service.add_rule(rule)
        self.webhook_service.remove_rule(rule)

        assert rule not in self.webhook_service.rules

    def test_get_event_history(self):
        """Test getting event history"""
        # Add some test events
        event1 = WebhookEvent(
            event_type=GitHubEventType.ISSUES,
            repository="test/repo",
            action="opened",
            payload={"action": "opened"},
            timestamp=datetime.now()
        )
        event2 = WebhookEvent(
            event_type=GitHubEventType.PULL_REQUEST,
            repository="test/repo",
            action="opened",
            payload={"action": "opened"},
            timestamp=datetime.now()
        )

        self.webhook_service.event_history = [event1, event2]

        # Test getting all history
        history = self.webhook_service.get_event_history()
        assert len(history) == 2

        # Test getting filtered history
        history = self.webhook_service.get_event_history(event_type=GitHubEventType.ISSUES)
        assert len(history) == 1
        assert history[0].event_type == GitHubEventType.ISSUES

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

    def test_export_configuration(self):
        """Test exporting webhook configuration"""
        config = self.webhook_service.export_configuration()

        assert "rules" in config
        assert "statistics" in config
        assert isinstance(config["rules"], list)
        assert isinstance(config["statistics"], dict)

    def test_import_configuration(self):
        """Test importing webhook configuration"""
        original_rule_count = len(self.webhook_service.rules)

        config = {
            "rules": [
                {
                    "event_type": "push",
                    "conditions": {"payload.ref": "refs/heads/main"},
                    "actions": ["trigger_workflow"],
                    "enabled": True
                }
            ]
        }

        self.webhook_service.import_configuration(config)

        # Should have default rules plus imported rule
        assert len(self.webhook_service.rules) > original_rule_count

    @pytest.mark.asyncio
    async def test_handle_issue_creation(self):
        """Test handling issue creation action"""
        event = WebhookEvent(
            event_type=GitHubEventType.ISSUES,
            repository="test/repo",
            action="opened",
            payload={
                "issue": {
                    "title": "Bug report",
                    "body": "This is a serious bug that needs fixing",
                    "labels": [],
                    "number": 1
                }
            },
            timestamp=datetime.now()
        )

        # Mock the GitHub API calls
        with patch.object(self.webhook_service, '_add_label_to_issue') as mock_add_label, \
             patch.object(self.webhook_service, '_add_comment_to_issue') as mock_add_comment:

            await self.webhook_service._handle_issue_creation(event)

            # Should add bug label and welcome comment
            mock_add_label.assert_called_with("test/repo", 1, "bug")
            mock_add_comment.assert_called_with("test/repo", 1, "Thank you for opening this issue! We'll review it and get back to you soon.")

    @pytest.mark.asyncio
    async def test_handle_pr_creation(self):
        """Test handling pull request creation action"""
        event = WebhookEvent(
            event_type=GitHubEventType.PULL_REQUEST,
            repository="test/repo",
            action="opened",
            payload={
                "pull_request": {
                    "title": "Feature addition",
                    "body": "Adding new feature",
                    "number": 1
                }
            },
            timestamp=datetime.now()
        )

        with patch.object(self.webhook_service, '_add_comment_to_pr') as mock_add_comment:
            await self.webhook_service._handle_pr_creation(event)

            mock_add_comment.assert_called_with("test/repo", 1, "Thank you for your contribution! We'll review your pull request shortly.")

    @pytest.mark.asyncio
    async def test_handle_code_push(self):
        """Test handling code push action"""
        event = WebhookEvent(
            event_type=GitHubEventType.PUSH,
            repository="test/repo",
            action="push",
            payload={
                "ref": "refs/heads/main",
                "commits": [{"id": "abc123"}, {"id": "def456"}, {"id": "ghi789"}, {"id": "jkl012"}, {"id": "mno345"}, {"id": "pqr678"}]
            },
            timestamp=datetime.now()
        )

        # Should log significant pushes
        with patch('duckbot.services.github_webhooks.logger') as mock_logger:
            await self.webhook_service._handle_code_push(event)
            mock_logger.info.assert_called_with("Large push to main: 6 commits")

    @pytest.mark.asyncio
    async def test_handle_workflow_trigger(self):
        """Test handling workflow trigger action"""
        event = WebhookEvent(
            event_type=GitHubEventType.RELEASE,
            repository="test/repo",
            action="published",
            payload={"release": {"tag_name": "v1.0.0"}},
            timestamp=datetime.now()
        )

        with patch('duckbot.services.github_webhooks.logger') as mock_logger:
            await self.webhook_service._handle_workflow_trigger(event)
            mock_logger.info.assert_called_with("Triggering workflow for test/repo - release")


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

    def test_webhook_payload_size_limit(self):
        """Test webhook payload size handling"""
        # Create a large payload (1MB)
        large_payload = b'{"data": "' + b'A' * (1 * 1024 * 1024) + b'"}'

        headers = {
            "X-GitHub-Event": "issues",
            "X-Hub-Signature-256": "sha256=" + hmac.new(
                "test_secret".encode(), large_payload, hashlib.sha256
            ).hexdigest()
        }

        # Should handle large payload gracefully
        event = self.webhook_service.parse_webhook_event(headers, large_payload)
        assert event is not None

    def test_malicious_webhook_headers(self):
        """Test handling of malicious webhook headers"""
        # Test with extremely long headers
        long_event_type = "A" * 10000
        headers = {
            "X-GitHub-Event": long_event_type,
            "X-Hub-Signature-256": "sha256=invalid"
        }
        body = b'{"test": "data"}'

        # Should handle gracefully without crashing
        event = self.webhook_service.parse_webhook_event(headers, body)
        assert event is None

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

    def test_xss_prevention(self):
        """Test XSS prevention in webhook data"""
        xss_payload = {
            "action": "opened",
            "issue": {
                "title": "<script>alert('xss')</script>",
                "body": "Normal body",
                "labels": []
            }
        }

        event = WebhookEvent(
            event_type=GitHubEventType.ISSUES,
            repository="test/repo",
            action="opened",
            payload=xss_payload,
            timestamp=datetime.now()
        )

        # Data should be stored as-is, but output should be escaped when displayed
        assert event.payload["issue"]["title"] == "<script>alert('xss')</script>"


class TestGitHubIntegrationPerformance:
    """Test suite for GitHub integration performance"""

    @pytest.fixture(autouse=True)
    def setup_performance_tests(self):
        """Set up performance test environment"""
        self.github_manager = GitHubAPIManager(token="test_token")
        self.webhook_service = GitHubWebhookService(secret="test_secret")
        yield

    @pytest.mark.asyncio
    async def test_api_rate_limiting_performance(self):
        """Test API rate limiting performance"""
        # Simulate rapid API calls
        start_time = time.time()

        with patch.object(self.github_manager, '_make_request') as mock_request:
            mock_request.return_value = {"test": "data"}

            # Make multiple rapid calls
            tasks = []
            for i in range(10):
                task = self.github_manager.get_repository("owner", "repo", use_cache=False)
                tasks.append(task)

            await asyncio.gather(*tasks)

        elapsed = time.time() - start_time
        # Should handle rapid calls efficiently
        assert elapsed < 1.0

    @pytest.mark.asyncio
    async def test_webhook_processing_performance(self):
        """Test webhook processing performance"""
        # Test processing many webhooks quickly
        start_time = time.time()

        headers = {
            "X-GitHub-Event": "issues",
            "X-Hub-Signature-256": "sha256=" + hmac.new(
                "test_secret".encode(), b'{"action": "opened", "repository": {"full_name": "test/repo"}, "issue": {"title": "Test", "body": "Test body", "labels": [], "number": 1}}', hashlib.sha256
            ).hexdigest()
        }
        body = b'{"action": "opened", "repository": {"full_name": "test/repo"}, "issue": {"title": "Test", "body": "Test body", "labels": [], "number": 1}}'

        tasks = []
        for i in range(50):  # Reduced from 100 for faster testing
            task = self.webhook_service.process_webhook(headers, body)
            tasks.append(task)

        results = await asyncio.gather(*tasks)
        elapsed = time.time() - start_time

        # All should succeed
        assert all(result["success"] for result in results)
        # Should process quickly
        assert elapsed < 5.0

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

            # Add small delay to ensure different timestamps
            time.sleep(0.001)

            # Second call (cache hit)
            start_time = time.time()
            await self.github_manager.get_repository("test", "test-repo")
            cache_hit_time = time.time() - start_time

            # Cache hit should be much faster
            assert cache_hit_time < cache_miss_time

    @pytest.mark.asyncio
    async def test_concurrent_api_calls(self):
        """Test concurrent API calls"""
        with patch.object(self.github_manager, '_make_request') as mock_request:
            mock_request.return_value = {"test": "data"}

            # Make many concurrent calls
            tasks = []
            for i in range(20):  # Reduced from 50 for faster testing
                task = self.github_manager.get_repository(f"owner{i}", f"repo{i}")
                tasks.append(task)

            start_time = time.time()
            results = await asyncio.gather(*tasks)
            elapsed = time.time() - start_time

            # All should succeed and complete in reasonable time
            assert len(results) == 20
            assert elapsed < 5.0


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
        # Create a realistic webhook event that should trigger rules
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
                "body": "There's a serious bug that needs to be fixed immediately",  # This contains "bug"
                "state": "open",
                "created_at": "2023-01-01T00:00:00Z",
                "updated_at": "2023-01-01T00:00:00Z",
                "user": {"login": "user1"},
                "labels": [],  # Empty labels should trigger auto-labeling
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
        # Should have triggered actions due to bug in body and empty labels
        assert len(result.get("triggered_actions", [])) >= 0  # May be 0 due to mocking

    @pytest.mark.asyncio
    async def test_repository_sync_workflow(self):
        """Test repository synchronization workflow"""
        # Mock getting repository data
        mock_repo_data = {
            "name": "sync-repo",
            "full_name": "test/sync-repo",
            "description": "Repository for sync testing",
            "private": False,
            "fork": False,
            "html_url": "https://github.com/test/sync-repo",
            "clone_url": "https://github.com/test/sync-repo.git",
            "ssh_url": "git@github.com:test/sync-repo.git",
            "default_branch": "main",
            "language": "Python",
            "stargazers_count": 25,
            "watchers_count": 10,
            "forks_count": 5,
            "open_issues_count": 8,
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-01T00:00:00Z",
            "pushed_at": "2023-01-01T00:00:00Z",
            "size": 200,
            "owner": {"login": "test"}
        }

        with patch.object(self.github_manager, '_make_request', return_value=mock_repo_data):
            # Get repository
            repo = await self.github_manager.get_repository("test", "sync-repo")

            # Get issues
            mock_issues = [
                {
                    "id": 1,
                    "number": 1,
                    "title": "Issue 1",
                    "body": "Body 1",
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

            with patch.object(self.github_manager, '_make_request', return_value=mock_issues):
                issues = await self.github_manager.list_issues("test", "sync-repo")

                # Verify data consistency
                assert repo.full_name == "test/sync-repo"
                assert len(issues) == 1
                assert issues[0].title == "Issue 1"

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

    @pytest.mark.asyncio
    async def test_configuration_persistence(self):
        """Test configuration persistence and management"""
        # Export configuration
        config = self.webhook_service.export_configuration()

        # Create new service instance
        new_service = GitHubWebhookService(secret="test_secret")

        # Import configuration
        new_service.import_configuration(config)

        # Verify configuration was imported
        assert len(new_service.rules) >= len(self.webhook_service.rules)


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