"""
GitHub API Integration for DuckBot Enhanced v4.2
Provides comprehensive repository management, issue tracking, and automation capabilities
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import aiohttp
import base64
from pathlib import Path

from ..core.cost_management import CostTracker
from ..core.hardware_detector import HardwareDetector

logger = logging.getLogger(__name__)

class GitHubEventType(Enum):
    """GitHub event types for webhook handling"""
    PUSH = "push"
    ISSUES = "issues"
    ISSUE_COMMENT = "issue_comment"
    PULL_REQUEST = "pull_request"
    PULL_REQUEST_REVIEW = "pull_request_review"
    CREATE = "create"
    DELETE = "delete"
    RELEASE = "release"
    WATCH = "watch"
    FORK = "fork"

class IssueState(Enum):
    """GitHub issue states"""
    OPEN = "open"
    CLOSED = "closed"
    ALL = "all"

class PullRequestState(Enum):
    """GitHub pull request states"""
    OPEN = "open"
    CLOSED = "closed"
    ALL = "all"

@dataclass
class GitHubRepository:
    """GitHub repository information"""
    name: str
    full_name: str
    description: str
    private: bool
    fork: bool
    url: str
    clone_url: str
    ssh_url: str
    default_branch: str
    language: str
    stargazers_count: int
    watchers_count: int
    forks_count: int
    open_issues_count: int
    created_at: str
    updated_at: str
    pushed_at: str
    size: int
    owner: Dict[str, Any]

@dataclass
class GitHubIssue:
    """GitHub issue information"""
    id: int
    number: int
    title: str
    body: str
    state: str
    created_at: str
    updated_at: str
    closed_at: Optional[str]
    user: Dict[str, Any]
    assignee: Optional[Dict[str, Any]]
    assignees: List[Dict[str, Any]]
    labels: List[Dict[str, Any]]
    pull_request: Optional[Dict[str, Any]]

@dataclass
class GitHubPullRequest:
    """GitHub pull request information"""
    id: int
    number: int
    title: str
    body: str
    state: str
    created_at: str
    updated_at: str
    closed_at: Optional[str]
    merged_at: Optional[str]
    user: Dict[str, Any]
    assignee: Optional[Dict[str, Any]]
    assignees: List[Dict[str, Any]]
    labels: List[Dict[str, Any]]
    head: Dict[str, Any]
    base: Dict[str, Any]
    mergeable: Optional[bool]
    draft: bool

@dataclass
class GitHubCommit:
    """GitHub commit information"""
    sha: str
    message: str
    author: Dict[str, Any]
    committer: Dict[str, Any]
    url: str
    html_url: str
    comments_url: str
    timestamp: str

@dataclass
class GitHubWebhook:
    """GitHub webhook configuration"""
    id: int
    url: str
    events: List[str]
    active: bool
    config: Dict[str, Any]
    updated_at: str
    created_at: str

class GitHubAPIManager:
    """Manages GitHub API integration and automation"""

    def __init__(self,
                 token: Optional[str] = None,
                 base_url: str = "https://api.github.com",
                 cost_tracker: Optional[CostTracker] = None):
        """
        Initialize GitHub API Manager

        Args:
            token: GitHub personal access token
            base_url: GitHub API base URL
            cost_tracker: Optional cost tracking instance
        """
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.base_url = base_url.rstrip('/')
        self.cost_tracker = cost_tracker
        self.hardware_detector = HardwareDetector()

        # Rate limiting tracking
        self.rate_limit_remaining = 5000
        self.rate_limit_reset = time.time() + 3600
        self.last_request_time = 0

        # Webhook management
        self.webhook_handlers = {}
        self.webhook_secret = os.getenv("GITHUB_WEBHOOK_SECRET")

        # Repository cache
        self.repository_cache = {}
        self.cache_ttl = 300  # 5 minutes

        # Performance tracking
        self.api_calls_made = 0
        self.api_errors = 0
        self.average_response_time = 0

    def _get_headers(self) -> Dict[str, str]:
        """Get API request headers"""
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "DuckBot-Enhanced-v4.2"
        }

        if self.token:
            headers["Authorization"] = f"token {self.token}"

        return headers

    async def _check_rate_limit(self):
        """Check and respect rate limits"""
        current_time = time.time()

        if self.rate_limit_remaining <= 10 and current_time < self.rate_limit_reset:
            wait_time = self.rate_limit_reset - current_time
            logger.warning(f"Rate limit exceeded. Waiting {wait_time:.0f} seconds")
            await asyncio.sleep(wait_time)

    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make authenticated API request with rate limiting"""
        await self._check_rate_limit()

        start_time = time.time()
        self.api_calls_made += 1

        try:
            async with aiohttp.ClientSession(headers=self._get_headers()) as session:
                url = f"{self.base_url}/{endpoint.lstrip('/')}"

                async with session.request(method, url, **kwargs) as response:
                    # Update rate limit info
                    self.rate_limit_remaining = int(response.headers.get("X-RateLimit-Remaining", 5000))
                    reset_time = int(response.headers.get("X-RateLimit-Reset", time.time() + 3600))
                    self.rate_limit_reset = reset_time

                    # Update performance metrics
                    response_time = time.time() - start_time
                    self.average_response_time = (self.average_response_time * (self.api_calls_made - 1) + response_time) / self.api_calls_made

                    if response.status == 200:
                        return await response.json()
                    elif response.status == 204:
                        return {"success": True}
                    else:
                        error_data = await response.json() if response.content_type == "application/json" else await response.text()
                        logger.error(f"GitHub API error {response.status}: {error_data}")
                        self.api_errors += 1
                        raise Exception(f"GitHub API error {response.status}: {error_data}")

        except Exception as e:
            self.api_errors += 1
            logger.error(f"GitHub API request failed: {e}")
            raise

    # Repository Management
    async def get_repository(self, owner: str, repo: str, use_cache: bool = True) -> GitHubRepository:
        """Get repository information"""
        cache_key = f"{owner}/{repo}"

        if use_cache and cache_key in self.repository_cache:
            cached_data, cached_time = self.repository_cache[cache_key]
            if time.time() - cached_time < self.cache_ttl:
                return cached_data

        data = await self._make_request("GET", f"repos/{owner}/{repo}")

        repo = GitHubRepository(
            name=data["name"],
            full_name=data["full_name"],
            description=data.get("description", ""),
            private=data["private"],
            fork=data["fork"],
            url=data["html_url"],
            clone_url=data["clone_url"],
            ssh_url=data["ssh_url"],
            default_branch=data.get("default_branch", "main"),
            language=data.get("language"),
            stargazers_count=data.get("stargazers_count", 0),
            watchers_count=data.get("watchers_count", 0),
            forks_count=data.get("forks_count", 0),
            open_issues_count=data.get("open_issues_count", 0),
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            pushed_at=data["pushed_at"],
            size=data.get("size", 0),
            owner=data["owner"]
        )

        self.repository_cache[cache_key] = (repo, time.time())
        return repo

    async def list_user_repositories(self, username: str, visibility: str = "all") -> List[GitHubRepository]:
        """List user repositories"""
        params = {"visibility": visibility, "sort": "updated", "per_page": 100}
        data = await self._make_request("GET", f"users/{username}/repos", params=params)

        repositories = []
        for repo_data in data:
            repo = GitHubRepository(
                name=repo_data["name"],
                full_name=repo_data["full_name"],
                description=repo_data.get("description", ""),
                private=repo_data["private"],
                fork=repo_data["fork"],
                url=repo_data["html_url"],
                clone_url=repo_data["clone_url"],
                ssh_url=repo_data["ssh_url"],
                default_branch=repo_data.get("default_branch", "main"),
                language=repo_data.get("language"),
                stargazers_count=repo_data.get("stargazers_count", 0),
                watchers_count=repo_data.get("watchers_count", 0),
                forks_count=repo_data.get("forks_count", 0),
                open_issues_count=repo_data.get("open_issues_count", 0),
                created_at=repo_data["created_at"],
                updated_at=repo_data["updated_at"],
                pushed_at=repo_data["pushed_at"],
                size=repo_data.get("size", 0),
                owner=repo_data["owner"]
            )
            repositories.append(repo)

        return repositories

    # Issue Management
    async def list_issues(self, owner: str, repo: str, state: IssueState = IssueState.OPEN,
                         labels: Optional[List[str]] = None) -> List[GitHubIssue]:
        """List repository issues"""
        params = {"state": state.value, "per_page": 100}
        if labels:
            params["labels"] = ",".join(labels)

        data = await self._make_request("GET", f"repos/{owner}/{repo}/issues", params=params)

        issues = []
        for issue_data in data:
            # Filter out pull requests
            if "pull_request" in issue_data:
                continue

            issue = GitHubIssue(
                id=issue_data["id"],
                number=issue_data["number"],
                title=issue_data["title"],
                body=issue_data.get("body", ""),
                state=issue_data["state"],
                created_at=issue_data["created_at"],
                updated_at=issue_data["updated_at"],
                closed_at=issue_data.get("closed_at"),
                user=issue_data["user"],
                assignee=issue_data.get("assignee"),
                assignees=issue_data.get("assignees", []),
                labels=issue_data.get("labels", []),
                pull_request=issue_data.get("pull_request")
            )
            issues.append(issue)

        return issues

    async def create_issue(self, owner: str, repo: str, title: str, body: str,
                          labels: Optional[List[str]] = None, assignees: Optional[List[str]] = None) -> GitHubIssue:
        """Create a new issue"""
        payload = {
            "title": title,
            "body": body
        }

        if labels:
            payload["labels"] = labels
        if assignees:
            payload["assignees"] = assignees

        data = await self._make_request("POST", f"repos/{owner}/{repo}/issues", json=payload)

        return GitHubIssue(
            id=data["id"],
            number=data["number"],
            title=data["title"],
            body=data.get("body", ""),
            state=data["state"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            closed_at=data.get("closed_at"),
            user=data["user"],
            assignee=data.get("assignee"),
            assignees=data.get("assignees", []),
            labels=data.get("labels", []),
            pull_request=data.get("pull_request")
        )

    async def update_issue(self, owner: str, repo: str, issue_number: int,
                          title: Optional[str] = None, body: Optional[str] = None,
                          state: Optional[IssueState] = None, labels: Optional[List[str]] = None) -> GitHubIssue:
        """Update an existing issue"""
        payload = {}

        if title:
            payload["title"] = title
        if body:
            payload["body"] = body
        if state:
            payload["state"] = state.value
        if labels is not None:
            payload["labels"] = labels

        data = await self._make_request("PATCH", f"repos/{owner}/{repo}/issues/{issue_number}", json=payload)

        return GitHubIssue(
            id=data["id"],
            number=data["number"],
            title=data["title"],
            body=data.get("body", ""),
            state=data["state"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            closed_at=data.get("closed_at"),
            user=data["user"],
            assignee=data.get("assignee"),
            assignees=data.get("assignees", []),
            labels=data.get("labels", []),
            pull_request=data.get("pull_request")
        )

    # Pull Request Management
    async def list_pull_requests(self, owner: str, repo: str, state: PullRequestState = PullRequestState.OPEN) -> List[GitHubPullRequest]:
        """List repository pull requests"""
        params = {"state": state.value, "per_page": 100}

        data = await self._make_request("GET", f"repos/{owner}/{repo}/pulls", params=params)

        prs = []
        for pr_data in data:
            pr = GitHubPullRequest(
                id=pr_data["id"],
                number=pr_data["number"],
                title=pr_data["title"],
                body=pr_data.get("body", ""),
                state=pr_data["state"],
                created_at=pr_data["created_at"],
                updated_at=pr_data["updated_at"],
                closed_at=pr_data.get("closed_at"),
                merged_at=pr_data.get("merged_at"),
                user=pr_data["user"],
                assignee=pr_data.get("assignee"),
                assignees=pr_data.get("assignees", []),
                labels=pr_data.get("labels", []),
                head=pr_data["head"],
                base=pr_data["base"],
                mergeable=pr_data.get("mergeable"),
                draft=pr_data.get("draft", False)
            )
            prs.append(pr)

        return prs

    async def create_pull_request(self, owner: str, repo: str, title: str, head: str,
                               base: str, body: Optional[str] = None, draft: bool = False) -> GitHubPullRequest:
        """Create a new pull request"""
        payload = {
            "title": title,
            "head": head,
            "base": base,
            "draft": draft
        }

        if body:
            payload["body"] = body

        data = await self._make_request("POST", f"repos/{owner}/{repo}/pulls", json=payload)

        return GitHubPullRequest(
            id=data["id"],
            number=data["number"],
            title=data["title"],
            body=data.get("body", ""),
            state=data["state"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            closed_at=data.get("closed_at"),
            merged_at=data.get("merged_at"),
            user=data["user"],
            assignee=data.get("assignee"),
            assignees=data.get("assignees", []),
            labels=data.get("labels", []),
            head=data["head"],
            base=data["base"],
            mergeable=data.get("mergeable"),
            draft=data.get("draft", False)
        )

    # Commit Management
    async def list_commits(self, owner: str, repo: str, branch: Optional[str] = None,
                          since: Optional[datetime] = None, until: Optional[datetime] = None) -> List[GitHubCommit]:
        """List repository commits"""
        params = {"per_page": 100}

        if branch:
            params["sha"] = branch
        if since:
            params["since"] = since.isoformat()
        if until:
            params["until"] = until.isoformat()

        data = await self._make_request("GET", f"repos/{owner}/{repo}/commits", params=params)

        commits = []
        for commit_data in data:
            commit = GitHubCommit(
                sha=commit_data["sha"],
                message=commit_data["commit"]["message"],
                author=commit_data["commit"]["author"],
                committer=commit_data["commit"]["committer"],
                url=commit_data["url"],
                html_url=commit_data["html_url"],
                comments_url=commit_data["comments_url"],
                timestamp=commit_data["commit"]["committer"]["date"]
            )
            commits.append(commit)

        return commits

    async def get_file_content(self, owner: str, repo: str, path: str, ref: Optional[str] = None) -> str:
        """Get file content from repository"""
        params = {}
        if ref:
            params["ref"] = ref

        data = await self._make_request("GET", f"repos/{owner}/{repo}/contents/{path}", params=params)

        if data.get("encoding") == "base64":
            return base64.b64decode(data["content"]).decode("utf-8")
        else:
            return data.get("content", "")

    # Webhook Management
    async def list_webhooks(self, owner: str, repo: str) -> List[GitHubWebhook]:
        """List repository webhooks"""
        data = await self._make_request("GET", f"repos/{owner}/{repo}/hooks")

        webhooks = []
        for hook_data in data:
            webhook = GitHubWebhook(
                id=hook_data["id"],
                url=hook_data["url"],
                events=hook_data["events"],
                active=hook_data["active"],
                config=hook_data["config"],
                updated_at=hook_data["updated_at"],
                created_at=hook_data["created_at"]
            )
            webhooks.append(webhook)

        return webhooks

    async def create_webhook(self, owner: str, repo: str, webhook_url: str,
                            events: List[str], secret: Optional[str] = None) -> GitHubWebhook:
        """Create a new webhook"""
        payload = {
            "name": "web",
            "url": webhook_url,
            "events": events,
            "active": True
        }

        if secret:
            payload["secret"] = secret

        data = await self._make_request("POST", f"repos/{owner}/{repo}/hooks", json=payload)

        return GitHubWebhook(
            id=data["id"],
            url=data["url"],
            events=data["events"],
            active=data["active"],
            config=data["config"],
            updated_at=data["updated_at"],
            created_at=data["created_at"]
        )

    async def delete_webhook(self, owner: str, repo: str, webhook_id: int) -> bool:
        """Delete a webhook"""
        try:
            await self._make_request("DELETE", f"repos/{owner}/{repo}/hooks/{webhook_id}")
            return True
        except Exception:
            return False

    # Analytics and Monitoring
    async def get_repository_analytics(self, owner: str, repo: str) -> Dict[str, Any]:
        """Get repository analytics and health metrics"""
        # Get repository info
        repo = await self.get_repository(owner, repo)

        # Get issues
        issues = await self.list_issues(owner, repo, IssueState.ALL)
        open_issues = [i for i in issues if i.state == "open"]
        closed_issues = [i for i in issues if i.state == "closed"]

        # Get pull requests
        prs = await self.list_pull_requests(owner, repo, PullRequestState.ALL)
        open_prs = [pr for pr in prs if pr.state == "open"]
        closed_prs = [pr for pr in prs if pr.state == "closed"]
        merged_prs = [pr for pr in prs if pr.merged_at]

        # Get recent commits
        thirty_days_ago = datetime.now() - timedelta(days=30)
        recent_commits = await self.list_commits(owner, repo, since=thirty_days_ago)

        # Calculate metrics
        total_commits = len(recent_commits)
        avg_commits_per_day = total_commits / 30 if total_commits > 0 else 0

        # Issue resolution rate
        resolution_rate = (len(closed_issues) / len(issues)) * 100 if issues else 0

        # PR merge rate
        merge_rate = (len(merged_prs) / len(closed_prs)) * 100 if closed_prs else 0

        return {
            "repository": {
                "name": repo.full_name,
                "description": repo.description,
                "language": repo.language,
                "stars": repo.stargazers_count,
                "forks": repo.forks_count,
                "watchers": repo.watchers_count,
                "size_kb": repo.size,
                "created_at": repo.created_at,
                "last_pushed": repo.pushed_at
            },
            "issues": {
                "total": len(issues),
                "open": len(open_issues),
                "closed": len(closed_issues),
                "resolution_rate": resolution_rate
            },
            "pull_requests": {
                "total": len(prs),
                "open": len(open_prs),
                "closed": len(closed_prs),
                "merged": len(merged_prs),
                "merge_rate": merge_rate
            },
            "activity": {
                "commits_last_30_days": total_commits,
                "avg_commits_per_day": avg_commits_per_day,
                "last_updated": repo.updated_at
            },
            "health_score": self._calculate_health_score(repo, open_issues, avg_commits_per_day, resolution_rate, merge_rate)
        }

    def _calculate_health_score(self, repo: GitHubRepository, open_issues: List[GitHubIssue],
                              avg_commits_per_day: float, resolution_rate: float, merge_rate: float) -> int:
        """Calculate repository health score (0-100)"""
        score = 0

        # Activity score (40 points)
        if avg_commits_per_day > 1:
            score += 20
        elif avg_commits_per_day > 0.5:
            score += 10

        # Issue management (30 points)
        if resolution_rate > 80:
            score += 20
        elif resolution_rate > 60:
            score += 10

        if len(open_issues) < 10:
            score += 10
        elif len(open_issues) < 50:
            score += 5

        # PR management (20 points)
        if merge_rate > 80:
            score += 15
        elif merge_rate > 60:
            score += 10

        # Community engagement (10 points)
        if repo.stargazers_count > 100:
            score += 10
        elif repo.stargazers_count > 50:
            score += 5

        return min(score, 100)

    # Utility methods
    async def search_repositories(self, query: str, language: Optional[str] = None,
                                 stars: Optional[int] = None) -> List[GitHubRepository]:
        """Search for repositories"""
        params = {"q": query, "per_page": 100}

        if language:
            params["q"] += f" language:{language}"
        if stars:
            params["q"] += f" stars:>{stars}"

        data = await self._make_request("GET", "search/repositories", params=params)

        repositories = []
        for repo_data in data.get("items", []):
            repo = GitHubRepository(
                name=repo_data["name"],
                full_name=repo_data["full_name"],
                description=repo_data.get("description", ""),
                private=repo_data["private"],
                fork=repo_data["fork"],
                url=repo_data["html_url"],
                clone_url=repo_data["clone_url"],
                ssh_url=repo_data["ssh_url"],
                default_branch=repo_data.get("default_branch", "main"),
                language=repo_data.get("language"),
                stargazers_count=repo_data.get("stargazers_count", 0),
                watchers_count=repo_data.get("watchers_count", 0),
                forks_count=repo_data.get("forks_count", 0),
                open_issues_count=repo_data.get("open_issues_count", 0),
                created_at=repo_data["created_at"],
                updated_at=repo_data["updated_at"],
                pushed_at=repo_data["pushed_at"],
                size=repo_data.get("size", 0),
                owner=repo_data["owner"]
            )
            repositories.append(repo)

        return repositories

    async def get_api_stats(self) -> Dict[str, Any]:
        """Get API usage statistics"""
        return {
            "api_calls_made": self.api_calls_made,
            "api_errors": self.api_errors,
            "error_rate": (self.api_errors / self.api_calls_made * 100) if self.api_calls_made > 0 else 0,
            "average_response_time": self.average_response_time,
            "rate_limit_remaining": self.rate_limit_remaining,
            "rate_limit_reset": datetime.fromtimestamp(self.rate_limit_reset).isoformat(),
            "cached_repositories": len(self.repository_cache)
        }

    async def test_connection(self) -> bool:
        """Test GitHub API connection"""
        try:
            await self._make_request("GET", "user")
            return True
        except Exception as e:
            logger.error(f"GitHub connection test failed: {e}")
            return False

# Global instance
github_manager = GitHubAPIManager()

async def initialize_github() -> bool:
    """Initialize GitHub integration"""
    return await github_manager.test_connection()

def get_github_manager() -> GitHubAPIManager:
    """Get the global GitHub manager instance"""
    return github_manager