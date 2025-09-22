import axios from 'axios';

class TRELLISService {
  constructor() {
    this.baseURL = process.env.REACT_APP_TRELLIS_URL || 'http://localhost:8000';
    this.apiKey = process.env.REACT_APP_TRELLIS_API_KEY || '';
    this.client = axios.create({
      baseURL: this.baseURL,
      headers: {
        'Content-Type': 'application/json',
        ...(this.apiKey && { 'Authorization': `Bearer ${this.apiKey}` })
      },
      timeout: 300000 // 5 minute timeout for 3D generation
    });
  }

  // Service status and health checks
  async testConnection() {
    try {
      const response = await this.client.get('/health');
      return response.data;
    } catch (error) {
      console.error('TRELLIS connection test failed:', error);
      throw error;
    }
  }

  async getStatus() {
    try {
      const response = await this.client.get('/status');
      return response.data;
    } catch (error) {
      console.error('Failed to get TRELLIS status:', error);
      return {
        isRunning: false,
        error: error.message
      };
    }
  }

  async getSystemInfo() {
    try {
      const response = await this.client.get('/system/info');
      return response.data;
    } catch (error) {
      console.error('Failed to get TRELLIS system info:', error);
      return null;
    }
  }

  // 3D Asset Generation
  async generateTextTo3D(prompt, options = {}) {
    try {
      const payload = {
        prompt,
        ...options
      };

      const response = await this.client.post('/generate/text-to-3d', payload);
      return response.data;
    } catch (error) {
      console.error('Text-to-3D generation failed:', error);
      throw error;
    }
  }

  async generateImageTo3D(imageFile, options = {}) {
    try {
      const formData = new FormData();
      formData.append('image', imageFile);

      // Add options as JSON
      Object.keys(options).forEach(key => {
        formData.append(key, typeof options[key] === 'object' ? JSON.stringify(options[key]) : options[key]);
      });

      const response = await this.client.post('/generate/image-to-3d', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      return response.data;
    } catch (error) {
      console.error('Image-to-3D generation failed:', error);
      throw error;
    }
  }

  async refineMesh(meshFile, options = {}) {
    try {
      const formData = new FormData();
      formData.append('mesh', meshFile);

      Object.keys(options).forEach(key => {
        formData.append(key, typeof options[key] === 'object' ? JSON.stringify(options[key]) : options[key]);
      });

      const response = await this.client.post('/refine/mesh', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      return response.data;
    } catch (error) {
      console.error('Mesh refinement failed:', error);
      throw error;
    }
  }

  async applyStyleTransfer(meshFile, stylePrompt, options = {}) {
    try {
      const formData = new FormData();
      formData.append('mesh', meshFile);
      formData.append('style_prompt', stylePrompt);

      Object.keys(options).forEach(key => {
        formData.append(key, typeof options[key] === 'object' ? JSON.stringify(options[key]) : options[key]);
      });

      const response = await this.client.post('/style/transfer', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      return response.data;
    } catch (error) {
      console.error('Style transfer failed:', error);
      throw error;
    }
  }

  async generateSLAT(meshFile, options = {}) {
    try {
      const formData = new FormData();
      formData.append('mesh', meshFile);

      Object.keys(options).forEach(key => {
        formData.append(key, typeof options[key] === 'object' ? JSON.stringify(options[key]) : options[key]);
      });

      const response = await this.client.post('/generate/slat', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      return response.data;
    } catch (error) {
      console.error('SLAT generation failed:', error);
      throw error;
    }
  }

  // Generation Job Management
  async getJobStatus(jobId) {
    try {
      const response = await this.client.get(`/jobs/${jobId}`);
      return response.data;
    } catch (error) {
      console.error('Failed to get job status:', error);
      throw error;
    }
  }

  async cancelJob(jobId) {
    try {
      const response = await this.client.post(`/jobs/${jobId}/cancel`);
      return response.data;
    } catch (error) {
      console.error('Failed to cancel job:', error);
      throw error;
    }
  }

  async getJobQueue() {
    try {
      const response = await this.client.get('/jobs/queue');
      return response.data;
    } catch (error) {
      console.error('Failed to get job queue:', error);
      return { jobs: [], active: 0, queued: 0 };
    }
  }

  // Asset and Project Management
  async getAssets(filters = {}) {
    try {
      const params = new URLSearchParams(filters);
      const response = await this.client.get(`/assets?${params}`);
      return response.data;
    } catch (error) {
      console.error('Failed to get assets:', error);
      return { assets: [], total: 0 };
    }
  }

  async getAssetDetails(assetId) {
    try {
      const response = await this.client.get(`/assets/${assetId}`);
      return response.data;
    } catch (error) {
      console.error('Failed to get asset details:', error);
      throw error;
    }
  }

  async downloadAsset(assetId, format = 'glb') {
    try {
      const response = await this.client.get(`/assets/${assetId}/download`, {
        params: { format },
        responseType: 'blob'
      });
      return response.data;
    } catch (error) {
      console.error('Failed to download asset:', error);
      throw error;
    }
  }

  async deleteAsset(assetId) {
    try {
      const response = await this.client.delete(`/assets/${assetId}`);
      return response.data;
    } catch (error) {
      console.error('Failed to delete asset:', error);
      throw error;
    }
  }

  async getProjects(filters = {}) {
    try {
      const params = new URLSearchParams(filters);
      const response = await this.client.get(`/projects?${params}`);
      return response.data;
    } catch (error) {
      console.error('Failed to get projects:', error);
      return { projects: [], total: 0 };
    }
  }

  async createProject(projectData) {
    try {
      const response = await this.client.post('/projects', projectData);
      return response.data;
    } catch (error) {
      console.error('Failed to create project:', error);
      throw error;
    }
  }

  async getProjectDetails(projectId) {
    try {
      const response = await this.client.get(`/projects/${projectId}`);
      return response.data;
    } catch (error) {
      console.error('Failed to get project details:', error);
      throw error;
    }
  }

  async addAssetToProject(projectId, assetId) {
    try {
      const response = await this.client.post(`/projects/${projectId}/assets`, { assetId });
      return response.data;
    } catch (error) {
      console.error('Failed to add asset to project:', error);
      throw error;
    }
  }

  // Configuration and Settings
  async getConfiguration() {
    try {
      const response = await this.client.get('/config');
      return response.data;
    } catch (error) {
      console.error('Failed to get configuration:', error);
      return null;
    }
  }

  async updateConfiguration(config) {
    try {
      const response = await this.client.put('/config', config);
      return response.data;
    } catch (error) {
      console.error('Failed to update configuration:', error);
      throw error;
    }
  }

  async getPresets() {
    try {
      const response = await this.client.get('/presets');
      return response.data;
    } catch (error) {
      console.error('Failed to get presets:', error);
      return { presets: [] };
    }
  }

  // Utility methods
  async getFormats() {
    try {
      const response = await this.client.get('/formats');
      return response.data;
    } catch (error) {
      console.error('Failed to get supported formats:', error);
      return { input: [], output: [] };
    }
  }

  async validateFile(file) {
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await this.client.post('/validate/file', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      return response.data;
    } catch (error) {
      console.error('File validation failed:', error);
      throw error;
    }
  }

  // Streaming support for long-running operations
  createGenerationStream(prompt, options = {}) {
    const eventSource = new EventSource(`${this.baseURL}/generate/stream?prompt=${encodeURIComponent(prompt)}&${new URLSearchParams(options)}`);

    return {
      eventSource,
      onMessage: (callback) => {
        eventSource.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            callback(data);
          } catch (error) {
            console.error('Failed to parse SSE message:', error);
          }
        };
      },
      onError: (callback) => {
        eventSource.onerror = callback;
      },
      close: () => {
        eventSource.close();
      }
    };
  }
}

export default TRELLISService;