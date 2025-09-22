// ComfyUI API Integration
class ComfyUIAPI {
  constructor() {
    this.baseURL = '/api/comfyui';
  }

  // Server Management
  async startServer() {
    const response = await fetch(`${this.baseURL}/start`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      }
    });
    return response.json();
  }

  async stopServer() {
    const response = await fetch(`${this.baseURL}/stop`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      }
    });
    return response.json();
  }

  async restartServer() {
    const response = await fetch(`${this.baseURL}/restart`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      }
    });
    return response.json();
  }

  // Workflow Management
  async getWorkflows() {
    const response = await fetch(`${this.baseURL}/workflows`);
    return response.json();
  }

  async executeWorkflow(workflowType, parameters, options = {}) {
    const response = await fetch(`${this.baseURL}/execute`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        workflowType,
        parameters,
        ...options
      })
    });
    return response.json();
  }

  async getWorkflowStatus(workflowId) {
    const response = await fetch(`${this.baseURL}/workflow/${workflowId}/status`);
    return response.json();
  }

  async cancelWorkflow(workflowId) {
    const response = await fetch(`${this.baseURL}/workflow/${workflowId}/cancel`, {
      method: 'POST'
    });
    return response.json();
  }

  // System Information
  async getStats() {
    const response = await fetch(`${this.baseURL}/stats`);
    return response.json();
  }

  async getQueue() {
    const response = await fetch(`${this.baseURL}/queue`);
    return response.json();
  }

  // File Management
  async uploadFile(file, type = 'input') {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('type', type);

    const response = await fetch(`${this.baseURL}/upload`, {
      method: 'POST',
      body: formData
    });
    return response.json();
  }

  async downloadFile(filename, type = 'output') {
    const response = await fetch(`${this.baseURL}/files/${type}/${filename}`);
    return response.blob();
  }

  async listFiles(type = 'output') {
    const response = await fetch(`${this.baseURL}/files/${type}`);
    return response.json();
  }

  async deleteFile(filename, type = 'output') {
    const response = await fetch(`${this.baseURL}/files/${type}/${filename}`, {
      method: 'DELETE'
    });
    return response.json();
  }

  // Configuration
  async getConfig() {
    const response = await fetch(`${this.baseURL}/config`);
    return response.json();
  }

  async updateConfig(config) {
    const response = await fetch(`${this.baseURL}/config`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(config)
    });
    return response.json();
  }
}

export default new ComfyUIAPI();