// Type definitions for DuckBot React WebUI

export interface DuckBotResponse {
  id: string;
  content: string;
  timestamp: string;
  model: string;
  provider: string;
  tokens?: {
    input: number;
    output: number;
    cost?: number;
  };
}

export interface ChatMessage {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: string;
  metadata?: {
    model?: string;
    provider?: string;
    tokens?: {
      input: number;
      output: number;
    };
  };
}

export interface ModelInfo {
  id: string;
  name: string;
  provider: string;
  description: string;
  maxTokens: number;
  supportsStreaming: boolean;
  supportsVision: boolean;
  supportsFunctions: boolean;
  costPerToken?: {
    input: number;
    output: number;
  };
}

export interface ProviderStatus {
  name: string;
  status: 'connected' | 'disconnected' | 'error' | 'free-mode';
  url?: string;
  models: ModelInfo[];
  lastChecked: string;
  error?: string;
}

export interface SystemHealth {
  overall: 'excellent' | 'good' | 'poor' | 'critical';
  cpu: number;
  memory: {
    used: number;
    total: number;
    percentage: number;
  };
  disk: {
    used: number;
    total: number;
    percentage: number;
  };
  network?: {
    latency: number;
    bandwidth: number;
  };
  services: {
    running: number;
    total: number;
    services: Array<{
      name: string;
      status: 'running' | 'stopped' | 'error';
      cpu?: number;
      memory?: number;
    }>;
  };
}

export interface ServiceInfo {
  id: string;
  name: string;
  status: 'running' | 'stopped' | 'error' | 'starting';
  port?: number;
  url?: string;
  description: string;
  dependencies?: string[];
  resources?: {
    cpu: number;
    memory: number;
  };
  lastUpdated: string;
  logs?: string[];
}

export interface VoiceModel {
  id: string;
  name: string;
  language: string;
  gender: 'male' | 'female' | 'neutral';
  type: 'tts' | 'cloning';
  quality: 'low' | 'medium' | 'high' | 'ultra';
  description?: string;
  size?: number;
  createdAt?: string;
}

export interface VoicePreset {
  id: string;
  name: string;
  voiceId: string;
  settings: {
    speed: number;
    pitch: number;
    volume: number;
    emotion?: string;
  };
  description?: string;
  isDefault?: boolean;
}

export interface AudioFile {
  id: string;
  filename: string;
  path: string;
  size: number;
  duration: number;
  format: string;
  sampleRate: number;
  channels: number;
  bitrate: number;
  voiceId: string;
  createdAt: string;
  metadata?: {
    text?: string;
    emotion?: string;
    language?: string;
  };
}

export interface GenerationJob {
  id: string;
  type: 'single' | 'conversation' | 'podcast';
  status: 'pending' | 'processing' | 'completed' | 'error';
  progress: number;
  text: string;
  voiceId: string;
  settings: {
    speed: number;
    pitch: number;
    emotion?: string;
    language?: string;
  };
  outputPath?: string;
  duration?: number;
  error?: string;
  createdAt: string;
  completedAt?: string;
}

// GitHub Integration Types
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

// WebSocket Event Types
export interface GitHubWebSocketEvent {
  type: 'push' | 'issues' | 'pull_request' | 'commit_comment' | 'issue_comment' | 'pull_request_review' | 'deployment' | 'deployment_status' | 'fork' | 'gollum' | 'member' | 'public' | 'release' | 'repository' | 'star' | 'status' | 'team_add' | 'watch';
  repository: GitHubRepository;
  payload: any;
  timestamp: string;
}

export interface GitHubPushEvent extends GitHubWebSocketEvent {
  type: 'push';
  payload: {
    ref: string;
    before: string;
    after: string;
    created: boolean;
    deleted: boolean;
    forced: boolean;
    base_ref: string | null;
    compare: string;
    commits: Array<{
      id: string;
      message: string;
      timestamp: string;
      url: string;
      author: {
        name: string;
        email: string;
      };
      added: string[];
      removed: string[];
      modified: string[];
    }>;
    head_commit: {
      id: string;
      message: string;
      timestamp: string;
      url: string;
      author: {
        name: string;
        email: string;
      };
    };
    repository: GitHubRepository;
    pusher: {
      name: string;
      email: string;
    };
  };
}

export interface GitHubIssuesEvent extends GitHubWebSocketEvent {
  type: 'issues';
  payload: {
    action: 'opened' | 'closed' | 'reopened' | 'edited' | 'assigned' | 'unassigned' | 'labeled' | 'unlabeled';
    issue: GitHubIssue;
    changes?: Record<string, any>;
    assignee?: { login: string; avatar_url: string } | null;
    label?: { id: number; name: string; color: string };
  };
}

export interface GitHubPullRequestEvent extends GitHubWebSocketEvent {
  type: 'pull_request';
  payload: {
    action: 'opened' | 'closed' | 'reopened' | 'edited' | 'assigned' | 'unassigned' | 'review_requested' | 'review_request_removed' | 'synchronize';
    pull_request: GitHubPullRequest;
    changes?: Record<string, any>;
    assignee?: { login: string; avatar_url: string } | null;
    requested_reviewer?: { login: string; avatar_url: string };
  };
}