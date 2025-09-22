import { EventEmitter } from 'events';

class ComfyUIService extends EventEmitter {
  constructor() {
    super();
    this.apiBaseUrl = 'http://localhost:8188';
    this.isRunning = false;
    this.status = {
      isRunning: false,
      port: 8188,
      gpuUsage: 0,
      gpuMemory: 0,
      gpuMemoryTotal: 0,
      activeWorkflows: [],
      systemStats: {}
    };

    // Initialize status checking
    this.startStatusMonitoring();
  }

  // Server Management
  async startServer() {
    try {
      const response = await fetch('/api/comfyui/start', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();

      if (result.success) {
        this.isRunning = true;
        this.status.isRunning = true;
        this.emit('serverStarted', result);
        return result;
      } else {
        throw new Error(result.error || 'Failed to start ComfyUI server');
      }
    } catch (error) {
      console.error('Error starting ComfyUI server:', error);
      this.emit('error', { type: 'serverStart', error: error.message });
      throw error;
    }
  }

  async stopServer() {
    try {
      const response = await fetch('/api/comfyui/stop', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();

      if (result.success) {
        this.isRunning = false;
        this.status.isRunning = false;
        this.status.activeWorkflows = [];
        this.emit('serverStopped', result);
        return result;
      } else {
        throw new Error(result.error || 'Failed to stop ComfyUI server');
      }
    } catch (error) {
      console.error('Error stopping ComfyUI server:', error);
      this.emit('error', { type: 'serverStop', error: error.message });
      throw error;
    }
  }

  async restartServer() {
    try {
      await this.stopServer();
      await new Promise(resolve => setTimeout(resolve, 2000)); // Wait for server to fully stop
      return await this.startServer();
    } catch (error) {
      console.error('Error restarting ComfyUI server:', error);
      throw error;
    }
  }

  // Workflow Management
  async getAvailableWorkflows() {
    try {
      const response = await fetch('/api/comfyui/workflows');

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching workflows:', error);
      return [];
    }
  }

  async executeWorkflow(workflowType, parameters, options = {}) {
    try {
      const requestData = {
        workflowType,
        parameters,
        ...options
      };

      const response = await fetch('/api/comfyui/execute', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestData)
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();

      if (result.success) {
        this.emit('workflowStarted', result);

        // Start monitoring workflow progress
        this.monitorWorkflow(result.workflowId);

        return result;
      } else {
        throw new Error(result.error || 'Failed to execute workflow');
      }
    } catch (error) {
      console.error('Error executing workflow:', error);
      this.emit('error', { type: 'workflowExecution', error: error.message });
      throw error;
    }
  }

  async getWorkflowStatus(workflowId) {
    try {
      const response = await fetch(`/api/comfyui/workflow/${workflowId}/status`);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching workflow status:', error);
      return null;
    }
  }

  async cancelWorkflow(workflowId) {
    try {
      const response = await fetch(`/api/comfyui/workflow/${workflowId}/cancel`, {
        method: 'POST'
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();

      if (result.success) {
        this.emit('workflowCancelled', { workflowId, result });
      }

      return result;
    } catch (error) {
      console.error('Error cancelling workflow:', error);
      throw error;
    }
  }

  // System Information
  async getSystemStats() {
    try {
      const response = await fetch('/api/comfyui/stats');

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const stats = await response.json();
      this.updateSystemStats(stats);
      return stats;
    } catch (error) {
      console.error('Error fetching system stats:', error);
      return this.status.systemStats;
    }
  }

  async getQueueStatus() {
    try {
      const response = await fetch('/api/comfyui/queue');

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching queue status:', error);
      return { running: [], queued: [] };
    }
  }

  // File Management
  async uploadFile(file, type = 'input') {
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('type', type);

      const response = await fetch('/api/comfyui/upload', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error uploading file:', error);
      throw error;
    }
  }

  async downloadFile(filename, type = 'output') {
    try {
      const response = await fetch(`/api/comfyui/files/${type}/${filename}`);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Error downloading file:', error);
      throw error;
    }
  }

  async listFiles(type = 'output') {
    try {
      const response = await fetch(`/api/comfyui/files/${type}`);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error listing files:', error);
      return [];
    }
  }

  async deleteFile(filename, type = 'output') {
    try {
      const response = await fetch(`/api/comfyui/files/${type}/${filename}`, {
        method: 'DELETE'
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error deleting file:', error);
      throw error;
    }
  }

  // Configuration Management
  async getConfiguration() {
    try {
      const response = await fetch('/api/comfyui/config');

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching configuration:', error);
      return this.getDefaultConfiguration();
    }
  }

  async updateConfiguration(config) {
    try {
      const response = await fetch('/api/comfyui/config', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(config)
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();

      if (result.success) {
        this.emit('configurationUpdated', config);
      }

      return result;
    } catch (error) {
      console.error('Error updating configuration:', error);
      throw error;
    }
  }

  // WebSocket connection for real-time updates
  connectWebSocket() {
    if (this.ws) {
      this.ws.close();
    }

    try {
      this.ws = new WebSocket('ws://localhost:8188/ws');

      this.ws.onopen = () => {
        console.log('ComfyUI WebSocket connected');
        this.emit('wsConnected');
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.handleWebSocketMessage(data);
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      this.ws.onclose = () => {
        console.log('ComfyUI WebSocket disconnected');
        this.emit('wsDisconnected');

        // Attempt to reconnect after 5 seconds
        setTimeout(() => this.connectWebSocket(), 5000);
      };

      this.ws.onerror = (error) => {
        console.error('ComfyUI WebSocket error:', error);
        this.emit('wsError', error);
      };
    } catch (error) {
      console.error('Error connecting WebSocket:', error);
      this.emit('error', { type: 'websocket', error: error.message });
    }
  }

  disconnectWebSocket() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  handleWebSocketMessage(data) {
    switch (data.type) {
      case 'status':
        this.updateStatus(data.data);
        this.emit('statusUpdate', data.data);
        break;
      case 'workflow_progress':
        this.emit('workflowProgress', data.data);
        break;
      case 'workflow_completed':
        this.emit('workflowCompleted', data.data);
        break;
      case 'workflow_error':
        this.emit('workflowError', data.data);
        break;
      case 'system_stats':
        this.updateSystemStats(data.data);
        this.emit('systemStatsUpdate', data.data);
        break;
      default:
        console.log('Unknown WebSocket message type:', data.type);
    }
  }

  updateStatus(statusData) {
    this.status = { ...this.status, ...statusData };
    this.isRunning = this.status.isRunning;
  }

  updateSystemStats(stats) {
    this.status.systemStats = stats;
    this.status.gpuUsage = stats.gpu_usage || 0;
    this.status.gpuMemory = stats.gpu_memory_used || 0;
    this.status.gpuMemoryTotal = stats.gpu_memory_total || 0;
  }

  async monitorWorkflow(workflowId) {
    const checkStatus = async () => {
      try {
        const status = await this.getWorkflowStatus(workflowId);

        if (status) {
          this.emit('workflowProgress', { workflowId, ...status });

          if (status.status === 'completed') {
            this.emit('workflowCompleted', { workflowId, result: status.result });
            return;
          } else if (status.status === 'error') {
            this.emit('workflowError', { workflowId, error: status.error });
            return;
          }

          // Continue monitoring
          setTimeout(checkStatus, 1000);
        }
      } catch (error) {
        console.error('Error monitoring workflow:', error);
        this.emit('error', { type: 'workflowMonitoring', error: error.message });
      }
    };

    checkStatus();
  }

  startStatusMonitoring() {
    // Check server status every 5 seconds
    setInterval(async () => {
      if (this.isRunning) {
        try {
          await this.getSystemStats();
        } catch (error) {
          // Server might be down, update status
          this.updateStatus({ isRunning: false });
        }
      }
    }, 5000);

    // Try to connect WebSocket when running
    setInterval(() => {
      if (this.isRunning && (!this.ws || this.ws.readyState !== WebSocket.OPEN)) {
        this.connectWebSocket();
      }
    }, 10000);
  }

  getDefaultConfiguration() {
    return {
      gpuMemoryLimit: 80,
      maxConcurrentWorkflows: 3,
      autoStartServer: true,
      enableGPUMode: true,
      comfyuiPath: '',
      defaultModels: {
        checkpoint: 'v1-5-pruned.ckpt',
        vae: 'vae-ft-mse-840000-ema-pruned.ckpt',
        upscale: '4x-UltraSharp.pth'
      },
      performance: {
        lowVramMode: false,
        medVramOptimizations: true,
        fp16Mode: true,
        forceFallbackCpu: false
      }
    };
  }

  // Utility methods
  getCurrentStatus() {
    return { ...this.status };
  }

  isServerRunning() {
    return this.isRunning;
  }

  getActiveWorkflowCount() {
    return this.status.activeWorkflows.length;
  }

  getQueueLength() {
    return this.status.queueLength || 0;
  }
}

// Export singleton instance
const comfyuiService = new ComfyUIService();
export default comfyuiService;