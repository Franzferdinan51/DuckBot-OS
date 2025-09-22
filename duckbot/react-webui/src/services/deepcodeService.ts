import axios from 'axios';
import { useState, useEffect, useCallback } from 'react';

// DeepCode API interfaces
export interface DeepCodeJob {
  id: string;
  type: 'paper2code' | 'text2web' | 'text2backend';
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;
  input: any;
  output?: any;
  error?: string;
  created_at: string;
  updated_at: string;
}

export interface Paper2CodeInput {
  document_url?: string;
  document_text?: string;
  code_style: 'modern' | 'classic' | 'minimal';
  language: 'python' | 'javascript' | 'typescript' | 'java' | 'cpp';
  include_comments: boolean;
  include_tests: boolean;
}

export interface Text2WebInput {
  description: string;
  framework: 'react' | 'vue' | 'angular' | 'svelte';
  styling: 'css' | 'tailwind' | 'styled-components' | 'bootstrap';
  features: string[];
  pages: string[];
}

export interface Text2BackendInput {
  description: string;
  architecture: 'monolithic' | 'microservices' | 'serverless';
  language: 'python' | 'javascript' | 'java' | 'go' | 'rust';
  database: 'postgresql' | 'mysql' | 'mongodb' | 'redis' | 'sqlite';
  auth_type: 'jwt' | 'oauth' | 'session' | 'none';
  apis: string[];
}

export interface DeepCodeConfig {
  server_url: string;
  api_key?: string;
  model: string;
  max_tokens: number;
  temperature: number;
  output_directory: string;
  auto_save: boolean;
  git_integration: boolean;
}

export interface DeepCodeStatus {
  server_available: boolean;
  active_jobs: number;
  completed_jobs: number;
  failed_jobs: number;
  queue_size: number;
  system_resources: {
    cpu_usage: number;
    memory_usage: number;
    disk_usage: number;
  };
}

export class DeepCodeService {
  private baseUrl: string;
  private apiKey?: string;
  private config: DeepCodeConfig;
  private connectionStatus: string = 'disconnected';

  constructor(config: Partial<DeepCodeConfig> = {}) {
    this.config = {
      server_url: config.server_url || 'http://localhost:8000',
      api_key: config.api_key,
      model: config.model || 'qwen2.5-coder-32b',
      max_tokens: config.max_tokens || 4000,
      temperature: config.temperature || 0.7,
      output_directory: config.output_directory || './deepcode_output',
      auto_save: config.auto_save ?? true,
      git_integration: config.git_integration ?? false,
    };
    this.baseUrl = this.config.server_url.replace(/\/$/, '');
    this.apiKey = this.config.api_key;
  }

  private async request(endpoint: string, options: any = {}): Promise<any> {
    const url = `${this.baseUrl}/api/v1${endpoint}`;
    const headers: any = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (this.apiKey) {
      headers['Authorization'] = `Bearer ${this.apiKey}`;
    }

    try {
      const response = await axios({
        url,
        ...options,
        headers,
        timeout: options.timeout || 30000,
      });

      return response.data;
    } catch (error: any) {
      console.error(`DeepCode API request failed: ${endpoint}`, error);

      if (error.response) {
        throw new Error(`DeepCode API error: ${error.response.data?.error || error.response.statusText}`);
      } else if (error.code === 'ECONNREFUSED') {
        throw new Error('Cannot connect to DeepCode server. Please ensure it is running.');
      } else {
        throw new Error(`Network error: ${error.message}`);
      }
    }
  }

  // System status
  async getStatus(): Promise<DeepCodeStatus> {
    try {
      const response = await this.request('/status', { method: 'GET' });
      return response;
    } catch (error) {
      return {
        server_available: false,
        active_jobs: 0,
        completed_jobs: 0,
        failed_jobs: 0,
        queue_size: 0,
        system_resources: {
          cpu_usage: 0,
          memory_usage: 0,
          disk_usage: 0,
        },
      };
    }
  }

  // Paper2Code operations
  async createPaper2CodeJob(input: Paper2CodeInput): Promise<DeepCodeJob> {
    const response = await this.request('/paper2code', {
      method: 'POST',
      data: input,
    });
    return response.job;
  }

  async uploadPaper2CodeDocument(file: File): Promise<{ document_url: string; document_id: string }> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await this.request('/paper2code/upload', {
      method: 'POST',
      data: formData,
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 60000,
    });
    return response;
  }

  // Text2Web operations
  async createText2WebJob(input: Text2WebInput): Promise<DeepCodeJob> {
    const response = await this.request('/text2web', {
      method: 'POST',
      data: input,
    });
    return response.job;
  }

  // Text2Backend operations
  async createText2BackendJob(input: Text2BackendInput): Promise<DeepCodeJob> {
    const response = await this.request('/text2backend', {
      method: 'POST',
      data: input,
    });
    return response.job;
  }

  // Job management
  async getJob(jobId: string): Promise<DeepCodeJob> {
    const response = await this.request(`/jobs/${jobId}`, { method: 'GET' });
    return response.job;
  }

  async getJobs(filters?: { type?: string; status?: string; limit?: number }): Promise<DeepCodeJob[]> {
    const params = new URLSearchParams();
    if (filters?.type) params.append('type', filters.type);
    if (filters?.status) params.append('status', filters.status);
    if (filters?.limit) params.append('limit', filters.limit.toString());

    const endpoint = `/jobs${params.toString() ? `?${params.toString()}` : ''}`;
    const response = await this.request(endpoint, { method: 'GET' });
    return response.jobs;
  }

  async cancelJob(jobId: string): Promise<void> {
    await this.request(`/jobs/${jobId}/cancel`, { method: 'POST' });
  }

  async deleteJob(jobId: string): Promise<void> {
    await this.request(`/jobs/${jobId}`, { method: 'DELETE' });
  }

  // Output management
  async getJobOutput(jobId: string): Promise<any> {
    const response = await this.request(`/jobs/${jobId}/output`, { method: 'GET' });
    return response.output;
  }

  async downloadJobOutput(jobId: string, format: 'zip' | 'tar' = 'zip'): Promise<Blob> {
    const response = await this.request(`/jobs/${jobId}/download?format=${format}`, {
      method: 'GET',
      responseType: 'blob',
    });
    return response;
  }

  // Configuration
  async updateConfig(config: Partial<DeepCodeConfig>): Promise<DeepCodeConfig> {
    this.config = { ...this.config, ...config };
    await this.request('/config', {
      method: 'PUT',
      data: this.config,
    });
    return this.config;
  }

  getConfig(): DeepCodeConfig {
    return { ...this.config };
  }

  // WebSocket connection for real-time updates
  createWebSocketConnection(): WebSocket | null {
    try {
      const wsUrl = this.baseUrl.replace('http', 'ws');
      const ws = new WebSocket(`${wsUrl}/ws`);

      ws.onopen = () => {
        console.log('DeepCode WebSocket connected');
        this.connectionStatus = 'connected';
      };

      ws.onerror = (error) => {
        console.error('DeepCode WebSocket error:', error);
        this.connectionStatus = 'error';
      };

      ws.onclose = () => {
        console.log('DeepCode WebSocket disconnected');
        this.connectionStatus = 'disconnected';
      };

      return ws;
    } catch (error) {
      console.error('Failed to create DeepCode WebSocket connection:', error);
      this.connectionStatus = 'failed';
      return null;
    }
  }

  // Test connection
  async testConnection(): Promise<boolean> {
    try {
      const status = await this.getStatus();
      return status.server_available;
    } catch (error) {
      return false;
    }
  }
}

// DeepCode React Hook for easier integration

export function useDeepCode(config?: Partial<DeepCodeConfig>) {
  const [service] = useState(() => new DeepCodeService(config));
  const [status, setStatus] = useState<DeepCodeStatus | null>(null);
  const [jobs, setJobs] = useState<DeepCodeJob[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [wsConnection, setWsConnection] = useState<WebSocket | null>(null);

  // Load initial status
  useEffect(() => {
    const loadStatus = async () => {
      try {
        const statusData = await service.getStatus();
        setStatus(statusData);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load status');
      }
    };

    loadStatus();
  }, [service]);

  // Load jobs
  const loadJobs = useCallback(async (filters?: { type?: string; status?: string; limit?: number }) => {
    setIsLoading(true);
    setError(null);

    try {
      const jobsData = await service.getJobs(filters);
      setJobs(jobsData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load jobs');
    } finally {
      setIsLoading(false);
    }
  }, [service]);

  // Create WebSocket connection
  useEffect(() => {
    const ws = service.createWebSocketConnection();
    setWsConnection(ws);

    if (ws) {
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          if (data.type === 'job_update') {
            setJobs(prev => prev.map(job =>
              job.id === data.job.id ? data.job : job
            ));
          } else if (data.type === 'status_update') {
            setStatus(data.status);
          }
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err);
        }
      };
    }

    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, [service]);

  // Paper2Code
  const createPaper2CodeJob = useCallback(async (input: Paper2CodeInput) => {
    setIsLoading(true);
    setError(null);

    try {
      const job = await service.createPaper2CodeJob(input);
      setJobs(prev => [job, ...prev]);
      return job;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create Paper2Code job');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [service]);

  // Text2Web
  const createText2WebJob = useCallback(async (input: Text2WebInput) => {
    setIsLoading(true);
    setError(null);

    try {
      const job = await service.createText2WebJob(input);
      setJobs(prev => [job, ...prev]);
      return job;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create Text2Web job');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [service]);

  // Text2Backend
  const createText2BackendJob = useCallback(async (input: Text2BackendInput) => {
    setIsLoading(true);
    setError(null);

    try {
      const job = await service.createText2BackendJob(input);
      setJobs(prev => [job, ...prev]);
      return job;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create Text2Backend job');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [service]);

  // Job management
  const cancelJob = useCallback(async (jobId: string) => {
    try {
      await service.cancelJob(jobId);
      setJobs(prev => prev.map(job =>
        job.id === jobId ? { ...job, status: 'failed' as const } : job
      ));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to cancel job');
    }
  }, [service]);

  const deleteJob = useCallback(async (jobId: string) => {
    try {
      await service.deleteJob(jobId);
      setJobs(prev => prev.filter(job => job.id !== jobId));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete job');
    }
  }, [service]);

  const getJobOutput = useCallback(async (jobId: string) => {
    try {
      return await service.getJobOutput(jobId);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to get job output');
      throw err;
    }
  }, [service]);

  return {
    service,
    status,
    jobs,
    isLoading,
    error,
    wsConnection,
    loadJobs,
    createPaper2CodeJob,
    createText2WebJob,
    createText2BackendJob,
    cancelJob,
    deleteJob,
    getJobOutput,
  };
}