import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, BarChart, Bar, Legend } from 'recharts';
import {
  GitBranch,
  GitCommit,
  GitPullRequest,
  AlertCircle, // Using AlertCircle instead of non-existent AlertCircle
  Activity,
  Settings,
  Search,
  Filter,
  RefreshCw,
  Users,
  Star,
  Eye,
  Webhook,
  Calendar,
  Clock,
  CheckCircle,
  XCircle
} from 'lucide-react';

// TypeScript interfaces for GitHub API responses
export interface GitHubRepository {
  id: number;
  name: string;
  full_name: string;
  description: string | null;
  html_url: string;
  clone_url: string;
  language: string | null;
  stargazers_count: number;
  watchers_count: number;
  forks_count: number;
  open_issues_count: number;
  default_branch: string;
  created_at: string;
  updated_at: string;
  pushed_at: string;
  size: number;
  private: boolean;
  owner: {
    login: string;
    avatar_url: string;
    type: string;
  };
}

export interface GitHubIssue {
  id: number;
  number: number;
  title: string;
  body: string | null;
  state: 'open' | 'closed';
  created_at: string;
  updated_at: string;
  closed_at: string | null;
  user: {
    login: string;
    avatar_url: string;
  };
  assignee: {
    login: string;
    avatar_url: string;
  } | null;
  labels: Array<{
    id: number;
    name: string;
    color: string;
  }>;
  pull_request?: {
    html_url: string;
  };
}

export interface GitHubPullRequest {
  id: number;
  number: number;
  title: string;
  body: string | null;
  state: 'open' | 'closed' | 'merged';
  created_at: string;
  updated_at: string;
  closed_at: string | null;
  merged_at: string | null;
  user: {
    login: string;
    avatar_url: string;
  };
  assignee: {
    login: string;
    avatar_url: string;
  } | null;
  labels: Array<{
    id: number;
    name: string;
    color: string;
  }>;
  head: {
    ref: string;
    sha: string;
  };
  base: {
    ref: string;
    sha: string;
  };
  additions: number;
  deletions: number;
  changed_files: number;
  review_comments: number;
  commits: number;
}

export interface GitHubCommit {
  sha: string;
  commit: {
    message: string;
    author: {
      name: string;
      email: string;
      date: string;
    };
    committer: {
      name: string;
      email: string;
      date: string;
    };
  };
  author: {
    login: string;
    avatar_url: string;
  } | null;
  html_url: string;
  stats: {
    additions: number;
    deletions: number;
    total: number;
  };
}

export interface GitHubWebhook {
  id: number;
  url: string;
  type: string;
  active: boolean;
  events: string[];
  created_at: string;
  updated_at: string;
  config: {
    url: string;
    content_type: string;
    secret?: string;
    insecure_ssl?: string;
  };
  last_response?: {
    code: number;
    status: string;
    message: string;
  };
}

export interface RepositoryAnalytics {
  commits_by_day: Array<{ date: string; commits: number }>;
  issues_by_state: Array<{ state: string; count: number; color: string }>;
  prs_by_state: Array<{ state: string; count: number; color: string }>;
  activity_by_week: Array<{ week: string; commits: number; issues: number; prs: number }>;
  contributors: Array<{
    login: string;
    avatar_url: string;
    commits: number;
    additions: number;
    deletions: number;
  }>;
  languages: Array<{ name: string; bytes: number; percentage: number }>;
}

interface GitHubRepositoryManagerProps {
  baseUrl?: string;
  token?: string;
  className?: string;
}

const GitHubRepositoryManager: React.FC<GitHubRepositoryManagerProps> = ({
  baseUrl = 'http://localhost:8787',
  token,
  className = ''
}) => {
  const [repositories, setRepositories] = useState<GitHubRepository[]>([]);
  const [selectedRepo, setSelectedRepo] = useState<GitHubRepository | null>(null);
  const [issues, setIssues] = useState<GitHubIssue[]>([]);
  const [pullRequests, setPullRequests] = useState<GitHubPullRequest[]>([]);
  const [commits, setCommits] = useState<GitHubCommit[]>([]);
  const [webhooks, setWebhooks] = useState<GitHubWebhook[]>([]);
  const [analytics, setAnalytics] = useState<RepositoryAnalytics | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [activeTab, setActiveTab] = useState<'repos' | 'issues' | 'prs' | 'commits' | 'webhooks' | 'analytics'>('repos');
  const [issueFilters, setIssueFilters] = useState({
    state: 'all' as 'all' | 'open' | 'closed',
    assignee: '',
    labels: ''
  });
  const [prFilters, setPrFilters] = useState({
    state: 'all' as 'all' | 'open' | 'closed' | 'merged',
    author: ''
  });

  // Fetch repositories
  const fetchRepositories = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${baseUrl}/api/github/repositories`, {
        headers: token ? { 'Authorization': `Bearer ${token}` } : {}
      });
      if (!response.ok) throw new Error('Failed to fetch repositories');
      const data = await response.json();
      setRepositories(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  // Fetch issues for selected repository
  const fetchIssues = async () => {
    if (!selectedRepo) return;
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (issueFilters.state !== 'all') params.append('state', issueFilters.state);
      if (issueFilters.assignee) params.append('assignee', issueFilters.assignee);
      if (issueFilters.labels) params.append('labels', issueFilters.labels);

      const response = await fetch(
        `${baseUrl}/api/github/repositories/${selectedRepo.full_name}/issues?${params}`,
        { headers: token ? { 'Authorization': `Bearer ${token}` } : {} }
      );
      if (!response.ok) throw new Error('Failed to fetch issues');
      const data = await response.json();
      setIssues(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  // Fetch pull requests for selected repository
  const fetchPullRequests = async () => {
    if (!selectedRepo) return;
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (prFilters.state !== 'all') params.append('state', prFilters.state);
      if (prFilters.author) params.append('author', prFilters.author);

      const response = await fetch(
        `${baseUrl}/api/github/repositories/${selectedRepo.full_name}/pulls?${params}`,
        { headers: token ? { 'Authorization': `Bearer ${token}` } : {} }
      );
      if (!response.ok) throw new Error('Failed to fetch pull requests');
      const data = await response.json();
      setPullRequests(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  // Fetch commits for selected repository
  const fetchCommits = async () => {
    if (!selectedRepo) return;
    setLoading(true);
    try {
      const response = await fetch(
        `${baseUrl}/api/github/repositories/${selectedRepo.full_name}/commits`,
        { headers: token ? { 'Authorization': `Bearer ${token}` } : {} }
      );
      if (!response.ok) throw new Error('Failed to fetch commits');
      const data = await response.json();
      setCommits(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  // Fetch webhooks for selected repository
  const fetchWebhooks = async () => {
    if (!selectedRepo) return;
    setLoading(true);
    try {
      const response = await fetch(
        `${baseUrl}/api/github/repositories/${selectedRepo.full_name}/webhooks`,
        { headers: token ? { 'Authorization': `Bearer ${token}` } : {} }
      );
      if (!response.ok) throw new Error('Failed to fetch webhooks');
      const data = await response.json();
      setWebhooks(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  // Fetch analytics for selected repository
  const fetchAnalytics = async () => {
    if (!selectedRepo) return;
    setLoading(true);
    try {
      const response = await fetch(
        `${baseUrl}/api/github/repositories/${selectedRepo.full_name}/analytics`,
        { headers: token ? { 'Authorization': `Bearer ${token}` } : {} }
      );
      if (!response.ok) throw new Error('Failed to fetch analytics');
      const data = await response.json();
      setAnalytics(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  // Initialize data
  useEffect(() => {
    fetchRepositories();
  }, []);

  // Fetch repository-specific data when repo is selected
  useEffect(() => {
    if (selectedRepo) {
      switch (activeTab) {
        case 'issues':
          fetchIssues();
          break;
        case 'prs':
          fetchPullRequests();
          break;
        case 'commits':
          fetchCommits();
          break;
        case 'webhooks':
          fetchWebhooks();
          break;
        case 'analytics':
          fetchAnalytics();
          break;
      }
    }
  }, [selectedRepo, activeTab, issueFilters, prFilters]);

  // Filter repositories based on search
  const filteredRepos = repositories.filter(repo =>
    repo.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    repo.description?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    repo.owner.login.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Handle repository selection
  const handleRepoSelect = (repo: GitHubRepository) => {
    setSelectedRepo(repo);
    setActiveTab('issues'); // Default to issues tab
  };

  // Format date for display
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // Get status icon for issues/PRs
  const getStatusIcon = (state: string) => {
    switch (state) {
      case 'open':
        return <AlertCircle className="h-4 w-4 text-green-500" />;
      case 'closed':
        return <XCircle className="h-4 w-4 text-red-500" />;
      case 'merged':
        return <CheckCircle className="h-4 w-4 text-purple-500" />;
      default:
        return <AlertCircle className="h-4 w-4 text-gray-500" />;
    }
  };

  // Tab navigation
  const tabs = [
    { id: 'repos', label: 'Repositories', icon: GitBranch },
    { id: 'issues', label: 'Issues', icon: AlertCircle },
    { id: 'prs', label: 'Pull Requests', icon: GitPullRequest },
    { id: 'commits', label: 'Commits', icon: GitCommit },
    { id: 'webhooks', label: 'Webhooks', icon: Webhook },
    { id: 'analytics', label: 'Analytics', icon: Activity }
  ] as const;

  return (
    <div className={`bg-gray-900 text-white min-h-screen ${className}`}>
      {/* Header */}
      <div className="bg-gray-800 border-b border-gray-700 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <GitBranch className="h-6 w-6 text-blue-400" />
            <h1 className="text-2xl font-bold">GitHub Repository Manager</h1>
            {selectedRepo && (
              <div className="flex items-center space-x-2">
                <span className="text-gray-400">/</span>
                <span className="text-lg font-medium text-blue-400">{selectedRepo.full_name}</span>
              </div>
            )}
          </div>
          <div className="flex items-center space-x-4">
            <button
              onClick={fetchRepositories}
              disabled={loading}
              className="p-2 hover:bg-gray-700 rounded-lg transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`h-5 w-5 ${loading ? 'animate-spin' : ''}`} />
            </button>
            <button className="p-2 hover:bg-gray-700 rounded-lg transition-colors">
              <Settings className="h-5 w-5" />
            </button>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="bg-gray-800 border-b border-gray-700">
        <div className="flex space-x-1 p-1">
          {tabs.map(tab => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors ${
                  activeTab === tab.id
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-400 hover:text-white hover:bg-gray-700'
                }`}
              >
                <Icon className="h-4 w-4" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="m-4 p-4 bg-red-900 border border-red-700 rounded-lg">
          <div className="flex items-center space-x-2">
            <AlertCircle className="h-5 w-5 text-red-400" />
            <span className="text-red-200">{error}</span>
          </div>
        </div>
      )}

      {/* Content Area */}
      <div className="p-4">
        {loading && (
          <div className="flex items-center justify-center py-8">
            <RefreshCw className="h-8 w-8 animate-spin text-blue-400" />
          </div>
        )}

        {/* Repositories Tab */}
        {activeTab === 'repos' && (
          <div className="space-y-4">
            {/* Search Bar */}
            <div className="flex items-center space-x-4 bg-gray-800 p-4 rounded-lg">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search repositories..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full bg-gray-700 text-white pl-10 pr-4 py-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <button className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors">
                <Filter className="h-4 w-4" />
              </button>
            </div>

            {/* Repository Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredRepos.map(repo => (
                <div
                  key={repo.id}
                  onClick={() => handleRepoSelect(repo)}
                  className="bg-gray-800 p-4 rounded-lg cursor-pointer hover:bg-gray-700 transition-colors border border-gray-700"
                >
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <h3 className="font-semibold text-lg">{repo.name}</h3>
                      <p className="text-gray-400 text-sm">{repo.owner.login}</p>
                    </div>
                    <img src={repo.owner.avatar_url} alt={repo.owner.login} className="h-8 w-8 rounded-full" />
                  </div>

                  {repo.description && (
                    <p className="text-gray-300 text-sm mb-3 line-clamp-2">{repo.description}</p>
                  )}

                  <div className="flex items-center justify-between text-sm">
                    <div className="flex items-center space-x-4 text-gray-400">
                      {repo.language && (
                        <span className="flex items-center space-x-1">
                          <div className="w-3 h-3 bg-blue-400 rounded-full"></div>
                          <span>{repo.language}</span>
                        </span>
                      )}
                      <span className="flex items-center space-x-1">
                        <Star className="h-3 w-3" />
                        <span>{repo.stargazers_count}</span>
                      </span>
                      <span className="flex items-center space-x-1">
                        <GitBranch className="h-3 w-3" />
                        <span>{repo.forks_count}</span>
                      </span>
                    </div>
                    <span className="text-gray-500">
                      {new Date(repo.updated_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Issues Tab */}
        {activeTab === 'issues' && selectedRepo && (
          <div className="space-y-4">
            {/* Filters */}
            <div className="bg-gray-800 p-4 rounded-lg">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <select
                  value={issueFilters.state}
                  onChange={(e) => setIssueFilters({ ...issueFilters, state: e.target.value as any })}
                  className="bg-gray-700 text-white px-3 py-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="all">All Issues</option>
                  <option value="open">Open</option>
                  <option value="closed">Closed</option>
                </select>
                <input
                  type="text"
                  placeholder="Filter by assignee..."
                  value={issueFilters.assignee}
                  onChange={(e) => setIssueFilters({ ...issueFilters, assignee: e.target.value })}
                  className="bg-gray-700 text-white px-3 py-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <input
                  type="text"
                  placeholder="Filter by labels..."
                  value={issueFilters.labels}
                  onChange={(e) => setIssueFilters({ ...issueFilters, labels: e.target.value })}
                  className="bg-gray-700 text-white px-3 py-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            {/* Issues List */}
            <div className="space-y-2">
              {issues.map(issue => (
                <div key={issue.id} className="bg-gray-800 p-4 rounded-lg border border-gray-700">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-2">
                        {getStatusIcon(issue.state)}
                        <span className="font-semibold">#{issue.number}</span>
                        <span className="text-gray-400">•</span>
                        <span className="text-blue-400">{issue.title}</span>
                      </div>

                      <p className="text-gray-300 text-sm mb-2 line-clamp-2">{issue.body}</p>

                      <div className="flex items-center space-x-4 text-sm text-gray-400">
                        <div className="flex items-center space-x-1">
                          <img src={issue.user.avatar_url} alt={issue.user.login} className="h-4 w-4 rounded-full" />
                          <span>{issue.user.login}</span>
                        </div>
                        <span>{formatDate(issue.created_at)}</span>
                        {issue.labels.length > 0 && (
                          <div className="flex items-center space-x-1">
                            {issue.labels.slice(0, 3).map(label => (
                              <span
                                key={label.id}
                                className="px-2 py-1 text-xs rounded-full"
                                style={{ backgroundColor: `#${label.color}20`, color: `#${label.color}` }}
                              >
                                {label.name}
                              </span>
                            ))}
                            {issue.labels.length > 3 && (
                              <span className="text-xs">+{issue.labels.length - 3}</span>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Pull Requests Tab */}
        {activeTab === 'prs' && selectedRepo && (
          <div className="space-y-4">
            {/* Filters */}
            <div className="bg-gray-800 p-4 rounded-lg">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <select
                  value={prFilters.state}
                  onChange={(e) => setPrFilters({ ...prFilters, state: e.target.value as any })}
                  className="bg-gray-700 text-white px-3 py-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="all">All Pull Requests</option>
                  <option value="open">Open</option>
                  <option value="closed">Closed</option>
                  <option value="merged">Merged</option>
                </select>
                <input
                  type="text"
                  placeholder="Filter by author..."
                  value={prFilters.author}
                  onChange={(e) => setPrFilters({ ...prFilters, author: e.target.value })}
                  className="bg-gray-700 text-white px-3 py-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            {/* PRs List */}
            <div className="space-y-2">
              {pullRequests.map(pr => (
                <div key={pr.id} className="bg-gray-800 p-4 rounded-lg border border-gray-700">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-2">
                        {getStatusIcon(pr.state)}
                        <span className="font-semibold">#{pr.number}</span>
                        <span className="text-gray-400">•</span>
                        <span className="text-green-400">{pr.title}</span>
                      </div>

                      <div className="flex items-center space-x-4 text-sm text-gray-400 mb-2">
                        <span className="flex items-center space-x-1">
                          <GitBranch className="h-3 w-3" />
                          <span>{pr.head.ref} → {pr.base.ref}</span>
                        </span>
                        <span className="flex items-center space-x-1">
                          <span className="text-green-400">+{pr.additions}</span>
                          <span className="text-red-400">-{pr.deletions}</span>
                          <span className="text-gray-500">({pr.changed_files} files)</span>
                        </span>
                      </div>

                      <div className="flex items-center space-x-4 text-sm text-gray-400">
                        <div className="flex items-center space-x-1">
                          <img src={pr.user.avatar_url} alt={pr.user.login} className="h-4 w-4 rounded-full" />
                          <span>{pr.user.login}</span>
                        </div>
                        <span>{formatDate(pr.created_at)}</span>
                        {pr.labels.length > 0 && (
                          <div className="flex items-center space-x-1">
                            {pr.labels.slice(0, 2).map(label => (
                              <span
                                key={label.id}
                                className="px-2 py-1 text-xs rounded-full"
                                style={{ backgroundColor: `#${label.color}20`, color: `#${label.color}` }}
                              >
                                {label.name}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Commits Tab */}
        {activeTab === 'commits' && selectedRepo && (
          <div className="space-y-2">
            {commits.map(commit => (
              <div key={commit.sha} className="bg-gray-800 p-4 rounded-lg border border-gray-700">
                <div className="flex items-start space-x-4">
                  {commit.author && (
                    <img src={commit.author.avatar_url} alt={commit.author.login} className="h-8 w-8 rounded-full" />
                  )}
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-1">
                      <span className="font-medium text-blue-400">{commit.commit.author.name}</span>
                      <span className="text-gray-400 text-sm">
                        {formatDate(commit.commit.author.date)}
                      </span>
                    </div>
                    <p className="text-gray-200 mb-2">{commit.commit.message}</p>
                    <div className="flex items-center space-x-4 text-sm text-gray-400">
                      <span className="font-mono text-xs bg-gray-700 px-2 py-1 rounded">
                        {commit.sha.substring(0, 7)}
                      </span>
                      <span className="flex items-center space-x-1">
                        <span className="text-green-400">+{commit.stats.additions}</span>
                        <span className="text-red-400">-{commit.stats.deletions}</span>
                        <span className="text-gray-500">({commit.stats.total} total)</span>
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Webhooks Tab */}
        {activeTab === 'webhooks' && selectedRepo && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold">Repository Webhooks</h3>
              <button className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors">
                Add Webhook
              </button>
            </div>

            <div className="space-y-2">
              {webhooks.map(webhook => (
                <div key={webhook.id} className="bg-gray-800 p-4 rounded-lg border border-gray-700">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-2">
                        <span className={`w-2 h-2 rounded-full ${webhook.active ? 'bg-green-400' : 'bg-red-400'}`}></span>
                        <span className="font-medium">{webhook.type}</span>
                        <span className="text-gray-400">•</span>
                        <span className="text-blue-400 text-sm">{webhook.config.url}</span>
                      </div>

                      <div className="flex items-center space-x-4 text-sm text-gray-400">
                        <span>Events: {webhook.events.join(', ')}</span>
                        <span>Content Type: {webhook.config.content_type}</span>
                        <span>Created: {formatDate(webhook.created_at)}</span>
                      </div>

                      {webhook.last_response && (
                        <div className="mt-2 p-2 bg-gray-700 rounded text-sm">
                          <span className="text-gray-400">Last response: </span>
                          <span className={webhook.last_response.code < 400 ? 'text-green-400' : 'text-red-400'}>
                            {webhook.last_response.code} - {webhook.last_response.status}
                          </span>
                        </div>
                      )}
                    </div>

                    <div className="flex items-center space-x-2">
                      <button className="p-2 hover:bg-gray-700 rounded transition-colors">
                        <Settings className="h-4 w-4" />
                      </button>
                      <button className="p-2 hover:bg-gray-700 rounded transition-colors">
                        <RefreshCw className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Analytics Tab */}
        {activeTab === 'analytics' && selectedRepo && analytics && (
          <div className="space-y-6">
            {/* Commit Activity Chart */}
            <div className="bg-gray-800 p-4 rounded-lg">
              <h3 className="text-lg font-semibold mb-4">Commit Activity</h3>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={analytics.commits_by_day}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                    <XAxis dataKey="date" stroke="#9CA3AF" />
                    <YAxis stroke="#9CA3AF" />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#1F2937', border: 'none' }}
                      itemStyle={{ color: '#ffffff' }}
                    />
                    <Line type="monotone" dataKey="commits" stroke="#3B82F6" strokeWidth={2} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Issues and PRs Distribution */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-gray-800 p-4 rounded-lg">
                <h3 className="text-lg font-semibold mb-4">Issues Distribution</h3>
                <div className="h-48">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={analytics.issues_by_state}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                        outerRadius={80}
                        fill="#8884d8"
                        dataKey="count"
                      >
                        {analytics.issues_by_state.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip
                        contentStyle={{ backgroundColor: '#1F2937', border: 'none' }}
                        itemStyle={{ color: '#ffffff' }}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              </div>

              <div className="bg-gray-800 p-4 rounded-lg">
                <h3 className="text-lg font-semibold mb-4">Pull Requests Distribution</h3>
                <div className="h-48">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={analytics.prs_by_state}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                        outerRadius={80}
                        fill="#8884d8"
                        dataKey="count"
                      >
                        {analytics.prs_by_state.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip
                        contentStyle={{ backgroundColor: '#1F2937', border: 'none' }}
                        itemStyle={{ color: '#ffffff' }}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>

            {/* Weekly Activity */}
            <div className="bg-gray-800 p-4 rounded-lg">
              <h3 className="text-lg font-semibold mb-4">Weekly Activity</h3>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={analytics.activity_by_week}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                    <XAxis dataKey="week" stroke="#9CA3AF" />
                    <YAxis stroke="#9CA3AF" />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#1F2937', border: 'none' }}
                      itemStyle={{ color: '#ffffff' }}
                    />
                    <Legend />
                    <Bar dataKey="commits" fill="#3B82F6" />
                    <Bar dataKey="issues" fill="#EF4444" />
                    <Bar dataKey="prs" fill="#10B981" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Top Contributors */}
            <div className="bg-gray-800 p-4 rounded-lg">
              <h3 className="text-lg font-semibold mb-4">Top Contributors</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {analytics.contributors.slice(0, 6).map(contributor => (
                  <div key={contributor.login} className="flex items-center space-x-3 p-3 bg-gray-700 rounded-lg">
                    <img src={contributor.avatar_url} alt={contributor.login} className="h-10 w-10 rounded-full" />
                    <div className="flex-1">
                      <div className="font-medium">{contributor.login}</div>
                      <div className="text-sm text-gray-400">
                        {contributor.commits} commits •
                        <span className="text-green-400"> +{contributor.additions}</span> •
                        <span className="text-red-400"> -{contributor.deletions}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Language Distribution */}
            <div className="bg-gray-800 p-4 rounded-lg">
              <h3 className="text-lg font-semibold mb-4">Language Distribution</h3>
              <div className="space-y-2">
                {analytics.languages.map(lang => (
                  <div key={lang.name} className="flex items-center space-x-3">
                    <div className="w-32 text-sm">{lang.name}</div>
                    <div className="flex-1 bg-gray-700 rounded-full h-6 relative overflow-hidden">
                      <div
                        className="h-full bg-blue-500 rounded-full"
                        style={{ width: `${lang.percentage}%` }}
                      ></div>
                    </div>
                    <div className="w-16 text-sm text-right text-gray-400">{lang.percentage.toFixed(1)}%</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default GitHubRepositoryManager;