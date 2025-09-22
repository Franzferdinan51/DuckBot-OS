import axios from 'axios';
import { io, Socket } from 'socket.io-client';
import type {
  GitHubRepository,
  GitHubIssue,
  GitHubPullRequest,
  GitHubCommit,
  GitHubWebhook,
  RepositoryAnalytics
} from '../components/GitHubRepositoryManager';

export class GitHubService {
  private baseUrl: string;
  private token: string | null;
  private socket: Socket | null;
  private listeners: Map<string, Set<Function>> = new Map();

  constructor(baseUrl: string = 'http://localhost:8787', token: string | null = null) {
    this.baseUrl = baseUrl.replace(/\/$/, '');
    this.token = token;
  }

  // WebSocket connection setup
  connectWebSocket(): void {
    if (this.socket?.connected) return;

    this.socket = io(`${this.baseUrl}`, {
      auth: this.token ? { token: this.token } : undefined,
      transports: ['websocket', 'polling']
    });

    this.socket.on('connect', () => {
      console.log('GitHub WebSocket connected');
      this.emit('connected', { connected: true });
    });

    this.socket.on('disconnect', () => {
      console.log('GitHub WebSocket disconnected');
      this.emit('disconnected', { connected: false });
    });

    this.socket.on('github-event', (data) => {
      this.emit('github-event', data);
      // Emit specific event types
      if (data.type) {
        this.emit(`github-${data.type}`, data);
      }
    });

    this.socket.on('error', (error) => {
      console.error('GitHub WebSocket error:', error);
      this.emit('error', error);
    });
  }

  disconnectWebSocket(): void {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
  }

  // Event listener management
  on(event: string, callback: Function): void {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event)!.add(callback);
  }

  off(event: string, callback: Function): void {
    const callbacks = this.listeners.get(event);
    if (callbacks) {
      callbacks.delete(callback);
      if (callbacks.size === 0) {
        this.listeners.delete(event);
      }
    }
  }

  private emit(event: string, data: any): void {
    const callbacks = this.listeners.get(event);
    if (callbacks) {
      callbacks.forEach(callback => callback(data));
    }
  }

  // Repository operations
  async getRepositories(): Promise<GitHubRepository[]> {
    try {
      const response = await axios.get(`${this.baseUrl}/api/github/repositories`, {
        headers: this.getAuthHeaders(),
        timeout: 10000
      });
      return response.data;
    } catch (error) {
      console.error('Failed to fetch repositories:', error);
      throw this.handleError(error);
    }
  }

  async getRepository(owner: string, repo: string): Promise<GitHubRepository> {
    try {
      const response = await axios.get(`${this.baseUrl}/api/github/repositories/${owner}/${repo}`, {
        headers: this.getAuthHeaders(),
        timeout: 10000
      });
      return response.data;
    } catch (error) {
      console.error('Failed to fetch repository:', error);
      throw this.handleError(error);
    }
  }

  // Issue operations
  async getIssues(owner: string, repo: string, params?: {
    state?: 'all' | 'open' | 'closed';
    assignee?: string;
    labels?: string;
    page?: number;
    per_page?: number;
  }): Promise<GitHubIssue[]> {
    try {
      const queryParams = new URLSearchParams();
      if (params) {
        Object.entries(params).forEach(([key, value]) => {
          if (value !== undefined) {
            queryParams.append(key, value.toString());
          }
        });
      }

      const response = await axios.get(
        `${this.baseUrl}/api/github/repositories/${owner}/${repo}/issues?${queryParams}`,
        {
          headers: this.getAuthHeaders(),
          timeout: 10000
        }
      );
      return response.data;
    } catch (error) {
      console.error('Failed to fetch issues:', error);
      throw this.handleError(error);
    }
  }

  async createIssue(owner: string, repo: string, issue: {
    title: string;
    body: string;
    assignees?: string[];
    labels?: string[];
  }): Promise<GitHubIssue> {
    try {
      const response = await axios.post(
        `${this.baseUrl}/api/github/repositories/${owner}/${repo}/issues`,
        issue,
        {
          headers: this.getAuthHeaders(),
          timeout: 15000
        }
      );
      return response.data;
    } catch (error) {
      console.error('Failed to create issue:', error);
      throw this.handleError(error);
    }
  }

  async updateIssue(owner: string, repo: string, issueNumber: number, updates: {
    state?: 'open' | 'closed';
    title?: string;
    body?: string;
    assignees?: string[];
    labels?: string[];
  }): Promise<GitHubIssue> {
    try {
      const response = await axios.patch(
        `${this.baseUrl}/api/github/repositories/${owner}/${repo}/issues/${issueNumber}`,
        updates,
        {
          headers: this.getAuthHeaders(),
          timeout: 15000
        }
      );
      return response.data;
    } catch (error) {
      console.error('Failed to update issue:', error);
      throw this.handleError(error);
    }
  }

  // Pull Request operations
  async getPullRequests(owner: string, repo: string, params?: {
    state?: 'all' | 'open' | 'closed' | 'merged';
    author?: string;
    page?: number;
    per_page?: number;
  }): Promise<GitHubPullRequest[]> {
    try {
      const queryParams = new URLSearchParams();
      if (params) {
        Object.entries(params).forEach(([key, value]) => {
          if (value !== undefined) {
            queryParams.append(key, value.toString());
          }
        });
      }

      const response = await axios.get(
        `${this.baseUrl}/api/github/repositories/${owner}/${repo}/pulls?${queryParams}`,
        {
          headers: this.getAuthHeaders(),
          timeout: 10000
        }
      );
      return response.data;
    } catch (error) {
      console.error('Failed to fetch pull requests:', error);
      throw this.handleError(error);
    }
  }

  async createPullRequest(owner: string, repo: string, pr: {
    title: string;
    body: string;
    head: string;
    base: string;
  }): Promise<GitHubPullRequest> {
    try {
      const response = await axios.post(
        `${this.baseUrl}/api/github/repositories/${owner}/${repo}/pulls`,
        pr,
        {
          headers: this.getAuthHeaders(),
          timeout: 15000
        }
      );
      return response.data;
    } catch (error) {
      console.error('Failed to create pull request:', error);
      throw this.handleError(error);
    }
  }

  async mergePullRequest(owner: string, repo: string, prNumber: number, mergeMethod: 'merge' | 'squash' | 'rebase' = 'merge'): Promise<any> {
    try {
      const response = await axios.put(
        `${this.baseUrl}/api/github/repositories/${owner}/${repo}/pulls/${prNumber}/merge`,
        { merge_method: mergeMethod },
        {
          headers: this.getAuthHeaders(),
          timeout: 15000
        }
      );
      return response.data;
    } catch (error) {
      console.error('Failed to merge pull request:', error);
      throw this.handleError(error);
    }
  }

  // Commit operations
  async getCommits(owner: string, repo: string, params?: {
    sha?: string;
    path?: string;
    author?: string;
    since?: string;
    until?: string;
    page?: number;
    per_page?: number;
  }): Promise<GitHubCommit[]> {
    try {
      const queryParams = new URLSearchParams();
      if (params) {
        Object.entries(params).forEach(([key, value]) => {
          if (value !== undefined) {
            queryParams.append(key, value.toString());
          }
        });
      }

      const response = await axios.get(
        `${this.baseUrl}/api/github/repositories/${owner}/${repo}/commits?${queryParams}`,
        {
          headers: this.getAuthHeaders(),
          timeout: 10000
        }
      );
      return response.data;
    } catch (error) {
      console.error('Failed to fetch commits:', error);
      throw this.handleError(error);
    }
  }

  async getCommit(owner: string, repo: string, sha: string): Promise<GitHubCommit> {
    try {
      const response = await axios.get(
        `${this.baseUrl}/api/github/repositories/${owner}/${repo}/commits/${sha}`,
        {
          headers: this.getAuthHeaders(),
          timeout: 10000
        }
      );
      return response.data;
    } catch (error) {
      console.error('Failed to fetch commit:', error);
      throw this.handleError(error);
    }
  }

  // Webhook operations
  async getWebhooks(owner: string, repo: string): Promise<GitHubWebhook[]> {
    try {
      const response = await axios.get(
        `${this.baseUrl}/api/github/repositories/${owner}/${repo}/webhooks`,
        {
          headers: this.getAuthHeaders(),
          timeout: 10000
        }
      );
      return response.data;
    } catch (error) {
      console.error('Failed to fetch webhooks:', error);
      throw this.handleError(error);
    }
  }

  async createWebhook(owner: string, repo: string, webhook: {
    url: string;
    content_type: 'json' | 'form';
    secret?: string;
    events: string[];
    active?: boolean;
  }): Promise<GitHubWebhook> {
    try {
      const response = await axios.post(
        `${this.baseUrl}/api/github/repositories/${owner}/${repo}/webhooks`,
        webhook,
        {
          headers: this.getAuthHeaders(),
          timeout: 15000
        }
      );
      return response.data;
    } catch (error) {
      console.error('Failed to create webhook:', error);
      throw this.handleError(error);
    }
  }

  async updateWebhook(owner: string, repo: string, webhookId: number, updates: {
    url?: string;
    content_type?: 'json' | 'form';
    secret?: string;
    events?: string[];
    active?: boolean;
  }): Promise<GitHubWebhook> {
    try {
      const response = await axios.patch(
        `${this.baseUrl}/api/github/repositories/${owner}/${repo}/webhooks/${webhookId}`,
        updates,
        {
          headers: this.getAuthHeaders(),
          timeout: 15000
        }
      );
      return response.data;
    } catch (error) {
      console.error('Failed to update webhook:', error);
      throw this.handleError(error);
    }
  }

  async deleteWebhook(owner: string, repo: string, webhookId: number): Promise<void> {
    try {
      await axios.delete(
        `${this.baseUrl}/api/github/repositories/${owner}/${repo}/webhooks/${webhookId}`,
        {
          headers: this.getAuthHeaders(),
          timeout: 10000
        }
      );
    } catch (error) {
      console.error('Failed to delete webhook:', error);
      throw this.handleError(error);
    }
  }

  async pingWebhook(owner: string, repo: string, webhookId: number): Promise<void> {
    try {
      await axios.post(
        `${this.baseUrl}/api/github/repositories/${owner}/${repo}/webhooks/${webhookId}/pings`,
        {},
        {
          headers: this.getAuthHeaders(),
          timeout: 10000
        }
      );
    } catch (error) {
      console.error('Failed to ping webhook:', error);
      throw this.handleError(error);
    }
  }

  // Analytics operations
  async getRepositoryAnalytics(owner: string, repo: string): Promise<RepositoryAnalytics> {
    try {
      const response = await axios.get(
        `${this.baseUrl}/api/github/repositories/${owner}/${repo}/analytics`,
        {
          headers: this.getAuthHeaders(),
          timeout: 15000
        }
      );
      return response.data;
    } catch (error) {
      console.error('Failed to fetch repository analytics:', error);
      throw this.handleError(error);
    }
  }

  async getCommitActivity(owner: string, repo: string): Promise<Array<{ week: string; commits: number }>> {
    try {
      const response = await axios.get(
        `${this.baseUrl}/api/github/repositories/${owner}/${repo}/stats/commit_activity`,
        {
          headers: this.getAuthHeaders(),
          timeout: 10000
        }
      );
      return response.data;
    } catch (error) {
      console.error('Failed to fetch commit activity:', error);
      throw this.handleError(error);
    }
  }

  async getCodeFrequency(owner: string, repo: string): Promise<Array<{ week: string; additions: number; deletions: number }>> {
    try {
      const response = await axios.get(
        `${this.baseUrl}/api/github/repositories/${owner}/${repo}/stats/code_frequency`,
        {
          headers: this.getAuthHeaders(),
          timeout: 10000
        }
      );
      return response.data;
    } catch (error) {
      console.error('Failed to fetch code frequency:', error);
      throw this.handleError(error);
    }
  }

  async getContributors(owner: string, repo: string): Promise<Array<{
    login: string;
    avatar_url: string;
    contributions: number;
    additions: number;
    deletions: number;
  }>> {
    try {
      const response = await axios.get(
        `${this.baseUrl}/api/github/repositories/${owner}/${repo}/stats/contributors`,
        {
          headers: this.getAuthHeaders(),
          timeout: 10000
        }
      );
      return response.data;
    } catch (error) {
      console.error('Failed to fetch contributors:', error);
      throw this.handleError(error);
    }
  }

  // Utility methods
  private getAuthHeaders(): Record<string, string> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json'
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    return headers;
  }

  private handleError(error: any): Error {
    if (error.response) {
      const status = error.response.status;
      const message = error.response.data?.message || error.response.data?.error || 'Unknown error';

      switch (status) {
        case 401:
          return new Error('Authentication required. Please check your GitHub token.');
        case 403:
          return new Error('Access forbidden. You may not have permission for this action.');
        case 404:
          return new Error('Resource not found.');
        case 429:
          return new Error('Rate limit exceeded. Please try again later.');
        case 500:
          return new Error('Server error. Please try again later.');
        default:
          return new Error(`GitHub API error (${status}): ${message}`);
      }
    } else if (error.code === 'ECONNREFUSED') {
      return new Error('Cannot connect to GitHub service. Please ensure the service is running.');
    } else if (error.code === 'ECONNABORTED') {
      return new Error('Request timeout. Please try again.');
    } else {
      return new Error(`Network error: ${error.message}`);
    }
  }

  // Configuration methods
  setBaseUrl(url: string): void {
    this.baseUrl = url.replace(/\/$/, '');
    if (this.socket) {
      this.disconnectWebSocket();
      this.connectWebSocket();
    }
  }

  setToken(token: string | null): void {
    this.token = token;
    if (this.socket) {
      this.disconnectWebSocket();
      this.connectWebSocket();
    }
  }

  // Test connection
  async testConnection(): Promise<boolean> {
    try {
      await this.getRepositories();
      return true;
    } catch (error) {
      console.error('GitHub service connection test failed:', error);
      return false;
    }
  }
}

// Export singleton instance
export const githubService = new GitHubService();

// Export React hook for easy integration
export const useGitHubService = (baseUrl?: string, token?: string) => {
  const service = new GitHubService(baseUrl, token);

  // This hook can be used in React components with proper React import
  // For now, we'll return the service instance
  return service;
};