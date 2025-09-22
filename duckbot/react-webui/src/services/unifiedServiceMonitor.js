class UnifiedServiceMonitor {
  constructor() {
    this.services = new Map();
    this.workflows = new Map();
    this.metrics = new Map();
    this.alerts = [];
    this.insights = [];
    this.subscribers = new Set();
    this.optimizationEngine = null;

    this.initializeServices();
    this.startMonitoring();
    this.initializeOptimizationEngine();
  }

  initializeServices() {
    // Initialize all DuckBot services with their configurations
    const serviceConfigs = {
      duckbot: {
        name: 'DuckBot Core',
        port: 8787,
        healthEndpoint: '/health',
        category: 'system',
        critical: true,
        dependencies: [],
        version: '4.2.0'
      },
      comfyui: {
        name: 'ComfyUI',
        port: 8188,
        healthEndpoint: '/health',
        category: 'media',
        critical: false,
        dependencies: ['duckbot'],
        version: 'latest'
      },
      trellis: {
        name: 'TRELLIS 3D',
        port: 8189,
        healthEndpoint: '/health',
        category: 'media',
        critical: false,
        dependencies: ['duckbot'],
        version: '1.0.0'
      },
      vibevoice: {
        name: 'VibeVoice',
        port: 8190,
        healthEndpoint: '/health',
        category: 'ai',
        critical: false,
        dependencies: ['duckbot'],
        version: '2.1.0'
      },
      monitoring: {
        name: 'System Monitor',
        port: 8789,
        healthEndpoint: '/health',
        category: 'monitoring',
        critical: true,
        dependencies: ['duckbot'],
        version: '1.0.0'
      },
      bytebot: {
        name: 'ByteBot Automation',
        port: 8790,
        healthEndpoint: '/health',
        category: 'automation',
        critical: false,
        dependencies: ['duckbot'],
        version: '1.5.0'
      },
      lmstudio: {
        name: 'LM Studio',
        port: 1234,
        healthEndpoint: '/health',
        category: 'ai',
        critical: false,
        dependencies: [],
        version: '0.2.17'
      },
      webui: {
        name: 'WebUI',
        port: 3000,
        healthEndpoint: '/health',
        category: 'system',
        critical: false,
        dependencies: [],
        version: '1.0.0'
      }
    };

    Object.entries(serviceConfigs).forEach(([key, config]) => {
      this.services.set(key, {
        ...config,
        status: 'unknown',
        lastCheck: null,
        uptime: 0,
        responseTime: 0,
        errorCount: 0,
        healthScore: 100,
        metrics: {
          cpu: 0,
          memory: 0,
          requests: 0,
          errors: 0
        }
      });
    });
  }

  startMonitoring() {
    // Check service health every 5 seconds
    setInterval(() => this.checkAllServices(), 5000);

    // Collect metrics every 2 seconds
    setInterval(() => this.collectMetrics(), 2000);

    // Analyze performance every 30 seconds
    setInterval(() => this.analyzePerformance(), 30000);

    // Run optimization every 5 minutes
    setInterval(() => this.runOptimization(), 300000);
  }

  async checkAllServices() {
    const checks = Array.from(this.services.entries()).map(([key, service]) =>
      this.checkServiceHealth(key)
    );

    await Promise.allSettled(checks);
    this.notifySubscribers('services-updated', Array.from(this.services.values()));
  }

  async checkServiceHealth(serviceKey) {
    const service = this.services.get(serviceKey);
    if (!service) return;

    const startTime = Date.now();

    try {
      const response = await fetch(`http://localhost:${service.port}${service.healthEndpoint}`, {
        method: 'GET',
        timeout: 5000
      });

      const responseTime = Date.now() - startTime;

      if (response.ok) {
        const health = await response.json();

        this.services.set(serviceKey, {
          ...service,
          status: 'running',
          lastCheck: new Date(),
          responseTime,
          uptime: service.uptime + 5,
          errorCount: 0,
          healthScore: this.calculateHealthScore(responseTime, health),
          metrics: {
            ...service.metrics,
            ...health.metrics
          }
        });

        // Check for performance degradation
        if (responseTime > 2000) {
          this.addAlert('performance', `${service.name} response time degraded (${responseTime}ms)`, 'medium');
        }
      } else {
        throw new Error(`HTTP ${response.status}`);
      }
    } catch (error) {
      this.services.set(serviceKey, {
        ...service,
        status: 'error',
        lastCheck: new Date(),
        responseTime: 0,
        errorCount: service.errorCount + 1,
        healthScore: Math.max(0, service.healthScore - 10)
      });

      this.addAlert('service', `${service.name} is unavailable: ${error.message}`, 'high');

      // Attempt auto-recovery for critical services
      if (service.critical && service.errorCount >= 3) {
        await this.attemptRecovery(serviceKey);
      }
    }
  }

  calculateHealthScore(responseTime, health) {
    let score = 100;

    // Response time impact
    if (responseTime > 5000) score -= 30;
    else if (responseTime > 2000) score -= 15;
    else if (responseTime > 1000) score -= 5;

    // Resource usage impact
    if (health.metrics?.cpu > 90) score -= 20;
    else if (health.metrics?.cpu > 70) score -= 10;

    if (health.metrics?.memory > 90) score -= 20;
    else if (health.metrics?.memory > 70) score -= 10;

    // Error rate impact
    const errorRate = health.metrics?.errors / Math.max(1, health.metrics?.requests);
    if (errorRate > 0.1) score -= 30;
    else if (errorRate > 0.05) score -= 15;

    return Math.max(0, score);
  }

  async collectMetrics() {
    try {
      // Collect system-wide metrics
      const systemResponse = await fetch('http://localhost:8787/api/system/metrics');
      if (systemResponse.ok) {
        const systemMetrics = await systemResponse.json();
        this.metrics.set('system', {
          ...systemMetrics,
          timestamp: Date.now()
        });
      }

      // Collect service-specific metrics
      for (const [key, service] of this.services) {
        if (service.status === 'running') {
          try {
            const metricsResponse = await fetch(`http://localhost:${service.port}/metrics`);
            if (metricsResponse.ok) {
              const serviceMetrics = await metricsResponse.json();
              this.metrics.set(key, {
                ...serviceMetrics,
                timestamp: Date.now()
              });
            }
          } catch (error) {
            // Metrics collection failed, but service is still running
          }
        }
      }

      this.notifySubscribers('metrics-updated', Object.fromEntries(this.metrics));
    } catch (error) {
      console.error('Failed to collect metrics:', error);
    }
  }

  analyzePerformance() {
    const analysis = {
      bottlenecks: [],
      recommendations: [],
      alerts: [],
      optimization: {}
    };

    // Analyze system performance
    const systemMetrics = this.metrics.get('system');
    if (systemMetrics) {
      if (systemMetrics.cpu > 80) {
        analysis.bottlenecks.push('High CPU usage');
        analysis.recommendations.push('Consider scaling CPU-intensive services');
      }

      if (systemMetrics.memory > 80) {
        analysis.bottlenecks.push('High memory usage');
        analysis.recommendations.push('Memory optimization recommended');
      }

      if (systemMetrics.disk > 90) {
        analysis.alerts.push({
          type: 'disk',
          message: 'Disk space running low',
          severity: 'high'
        });
      }
    }

    // Analyze service performance
    for (const [key, service] of this.services) {
      if (service.healthScore < 70) {
        analysis.bottlenecks.push(`${service.name} health degraded (${service.healthScore}%)`);
      }

      if (service.responseTime > 3000) {
        analysis.recommendations.push(`Optimize ${service.name} response time`);
      }
    }

    // Generate optimization suggestions
    analysis.optimization = this.generateOptimizationSuggestions(analysis);

    this.insights = analysis;
    this.notifySubscribers('insights-updated', analysis);
  }

  generateOptimizationSuggestions(analysis) {
    const suggestions = {
      resourceAllocation: {},
      serviceScaling: {},
      configuration: {}
    };

    // Resource allocation suggestions
    const systemMetrics = this.metrics.get('system');
    if (systemMetrics) {
      if (systemMetrics.cpu > 70) {
        suggestions.resourceAllocation.cpu = 'Reduce CPU-intensive tasks or scale horizontally';
      }

      if (systemMetrics.memory > 70) {
        suggestions.resourceAllocation.memory = 'Implement memory caching or cleanup';
      }
    }

    // Service scaling suggestions
    const highLoadServices = Array.from(this.services.values())
      .filter(s => s.metrics?.requests > 1000)
      .map(s => s.name);

    if (highLoadServices.length > 0) {
      suggestions.serviceScaling = {
        scaleUp: highLoadServices,
        reason: 'High request volume detected'
      };
    }

    // Configuration suggestions
    if (analysis.bottlenecks.includes('High response time')) {
      suggestions.configuration = {
        timeouts: 'Increase timeout values for slow services',
        retries: 'Implement retry logic for failed requests'
      };
    }

    return suggestions;
  }

  async runOptimization() {
    const suggestions = this.insights.optimization;

    try {
      // Apply resource allocation optimizations
      if (suggestions.resourceAllocation) {
        await this.optimizeResources(suggestions.resourceAllocation);
      }

      // Apply service scaling
      if (suggestions.serviceScaling) {
        await this.scaleServices(suggestions.serviceScaling);
      }

      // Apply configuration changes
      if (suggestions.configuration) {
        await this.updateConfiguration(suggestions.configuration);
      }

      this.addAlert('optimization', 'System optimization completed successfully', 'low');
    } catch (error) {
      this.addAlert('optimization', `Optimization failed: ${error.message}`, 'high');
    }
  }

  async optimizeResources(suggestions) {
    // Implement resource optimization logic
    const config = {
      cpu: suggestions.cpu,
      memory: suggestions.memory,
      priorityServices: this.getCriticalServices()
    };

    await fetch('http://localhost:8787/api/system/optimize-resources', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config)
    });
  }

  async scaleServices(suggestions) {
    // Implement service scaling logic
    for (const serviceName of suggestions.scaleUp) {
      const serviceKey = Array.from(this.services.entries())
        .find(([key, service]) => service.name === serviceName)?.[0];

      if (serviceKey) {
        await this.scaleService(serviceKey, 'up');
      }
    }
  }

  async scaleService(serviceKey, direction) {
    const service = this.services.get(serviceKey);
    if (!service) return;

    try {
      await fetch(`http://localhost:${service.port}/scale`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ direction })
      });
    } catch (error) {
      console.error(`Failed to scale ${service.name}:`, error);
    }
  }

  async updateConfiguration(suggestions) {
    // Apply configuration changes
    const config = {
      timeouts: suggestions.timeouts,
      retries: suggestions.retries,
      optimization: true
    };

    await fetch('http://localhost:8787/api/config/update', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config)
    });
  }

  async attemptRecovery(serviceKey) {
    const service = this.services.get(serviceKey);
    if (!service) return;

    this.addAlert('recovery', `Attempting auto-recovery for ${service.name}`, 'medium');

    try {
      // Attempt service restart
      await fetch(`http://localhost:${service.port}/restart`, {
        method: 'POST'
      });

      // Wait and check status
      await new Promise(resolve => setTimeout(resolve, 5000));
      await this.checkServiceHealth(serviceKey);

      const updatedService = this.services.get(serviceKey);
      if (updatedService.status === 'running') {
        this.addAlert('recovery', `${service.name} recovered successfully`, 'low');
      } else {
        this.addAlert('recovery', `${service.name} recovery failed`, 'high');
      }
    } catch (error) {
      this.addAlert('recovery', `${service.name} recovery failed: ${error.message}`, 'high');
    }
  }

  addAlert(type, message, severity = 'medium') {
    const alert = {
      id: Date.now() + Math.random(),
      type,
      message,
      severity,
      timestamp: new Date(),
      acknowledged: false
    };

    this.alerts.push(alert);

    // Keep only last 100 alerts
    if (this.alerts.length > 100) {
      this.alerts = this.alerts.slice(-100);
    }

    this.notifySubscribers('alert-added', alert);
  }

  getCriticalServices() {
    return Array.from(this.services.values())
      .filter(service => service.critical)
      .map(service => service.name);
  }

  getServiceStatus() {
    return Array.from(this.services.values());
  }

  getMetrics() {
    return Object.fromEntries(this.metrics);
  }

  getAlerts() {
    return this.alerts;
  }

  getInsights() {
    return this.insights;
  }

  subscribe(callback) {
    this.subscribers.add(callback);
    return () => this.subscribers.delete(callback);
  }

  notifySubscribers(type, data) {
    this.subscribers.forEach(callback => {
      try {
        callback(type, data);
      } catch (error) {
        console.error('Subscriber callback error:', error);
      }
    });
  }

  // Workflow Management Methods
  async startWorkflow(workflowId, config = {}) {
    const workflow = {
      id: workflowId,
      status: 'running',
      startTime: Date.now(),
      config,
      steps: [],
      progress: 0,
      logs: []
    };

    this.workflows.set(workflowId, workflow);

    try {
      await this.executeWorkflow(workflowId);
    } catch (error) {
      workflow.status = 'failed';
      workflow.error = error.message;
      this.workflows.set(workflowId, workflow);
    }

    return workflow;
  }

  async executeWorkflow(workflowId) {
    const workflow = this.workflows.get(workflowId);
    if (!workflow) return;

    // Execute workflow steps based on workflow type
    switch (workflowId) {
      case 'text-to-multimedia':
        await this.executeTextToMultimediaWorkflow(workflow);
        break;
      case 'storytelling-pipeline':
        await this.executeStorytellingWorkflow(workflow);
        break;
      case 'educational-content':
        await this.executeEducationalWorkflow(workflow);
        break;
      case 'batch-processing':
        await this.executeBatchProcessingWorkflow(workflow);
        break;
      default:
        throw new Error(`Unknown workflow type: ${workflowId}`);
    }
  }

  async executeTextToMultimediaWorkflow(workflow) {
    const steps = [
      { name: 'Text Analysis', service: 'duckbot' },
      { name: 'Image Generation', service: 'comfyui' },
      { name: '3D Model Creation', service: 'trellis' },
      { name: 'Voice Synthesis', service: 'vibevoice' }
    ];

    for (let i = 0; i < steps.length; i++) {
      const step = steps[i];
      workflow.steps.push(step);
      workflow.progress = ((i + 1) / steps.length) * 100;
      this.workflows.set(workflow.id, workflow);

      // Simulate step execution
      await new Promise(resolve => setTimeout(resolve, 2000));
    }

    workflow.status = 'completed';
    this.workflows.set(workflow.id, workflow);
  }

  async executeStorytellingWorkflow(workflow) {
    // Similar implementation for storytelling workflow
    const steps = [
      { name: 'Script Generation', service: 'duckbot' },
      { name: 'Scene Creation', service: 'comfyui' },
      { name: 'Character Design', service: 'trellis' },
      { name: 'Audio Production', service: 'vibevoice' }
    ];

    for (let i = 0; i < steps.length; i++) {
      const step = steps[i];
      workflow.steps.push(step);
      workflow.progress = ((i + 1) / steps.length) * 100;
      this.workflows.set(workflow.id, workflow);

      await new Promise(resolve => setTimeout(resolve, 2000));
    }

    workflow.status = 'completed';
    this.workflows.set(workflow.id, workflow);
  }

  async executeEducationalWorkflow(workflow) {
    // Implementation for educational content workflow
    const steps = [
      { name: 'Topic Analysis', service: 'duckbot' },
      { name: 'Content Structure', service: 'duckbot' },
      { name: 'Visual Aids', service: 'comfyui' },
      { name: 'Interactive Elements', service: 'trellis' }
    ];

    for (let i = 0; i < steps.length; i++) {
      const step = steps[i];
      workflow.steps.push(step);
      workflow.progress = ((i + 1) / steps.length) * 100;
      this.workflows.set(workflow.id, workflow);

      await new Promise(resolve => setTimeout(resolve, 2000));
    }

    workflow.status = 'completed';
    this.workflows.set(workflow.id, workflow);
  }

  async executeBatchProcessingWorkflow(workflow) {
    // Implementation for batch processing workflow
    const steps = [
      { name: 'Queue Setup', service: 'duckbot' },
      { name: 'Parallel Processing', service: 'monitoring' },
      { name: 'Quality Check', service: 'duckbot' },
      { name: 'Output Organization', service: 'monitoring' }
    ];

    for (let i = 0; i < steps.length; i++) {
      const step = steps[i];
      workflow.steps.push(step);
      workflow.progress = ((i + 1) / steps.length) * 100;
      this.workflows.set(workflow.id, workflow);

      await new Promise(resolve => setTimeout(resolve, 2000));
    }

    workflow.status = 'completed';
    this.workflows.set(workflow.id, workflow);
  }

  getWorkflows() {
    return Array.from(this.workflows.values());
  }

  getWorkflow(workflowId) {
    return this.workflows.get(workflowId);
  }

  stopWorkflow(workflowId) {
    const workflow = this.workflows.get(workflowId);
    if (workflow) {
      workflow.status = 'stopped';
      this.workflows.set(workflowId, workflow);
    }
  }
}

// Export singleton instance
const unifiedServiceMonitor = new UnifiedServiceMonitor();
export default unifiedServiceMonitor;