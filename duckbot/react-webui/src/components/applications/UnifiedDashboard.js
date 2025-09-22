import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { LineChart, Line, AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

// Service Status Types
const SERVICE_STATUS = {
  RUNNING: 'running',
  STOPPED: 'stopped',
  ERROR: 'error',
  STARTING: 'starting',
  MAINTENANCE: 'maintenance'
};

// Service Categories
const SERVICE_CATEGORIES = {
  AI: 'ai',
  MEDIA: 'media',
  SYSTEM: 'system',
  AUTOMATION: 'automation',
  MONITORING: 'monitoring'
};

const UnifiedDashboard = ({ onClose }) => {
  // Service states
  const [services, setServices] = useState({
    comfyui: { name: 'ComfyUI', status: SERVICE_STATUS.RUNNING, category: SERVICE_CATEGORIES.MEDIA, port: 8188, version: 'latest' },
    trellis: { name: 'TRELLIS', status: SERVICE_STATUS.RUNNING, category: SERVICE_CATEGORIES.MEDIA, port: 8189, version: '1.0.0' },
    vibevoice: { name: 'VibeVoice', status: SERVICE_STATUS.RUNNING, category: SERVICE_CATEGORIES.AI, port: 8190, version: '2.1.0' },
    duckbot: { name: 'DuckBot Core', status: SERVICE_STATUS.RUNNING, category: SERVICE_CATEGORIES.SYSTEM, port: 8787, version: '4.2.0' },
    monitoring: { name: 'Monitoring', status: SERVICE_STATUS.RUNNING, category: SERVICE_CATEGORIES.MONITORING, port: 8789, version: '1.0.0' },
    bytebot: { name: 'ByteBot', status: SERVICE_STATUS.RUNNING, category: SERVICE_CATEGORIES.AUTOMATION, port: 8790, version: '1.5.0' },
    lmstudio: { name: 'LM Studio', status: SERVICE_STATUS.RUNNING, category: SERVICE_CATEGORIES.AI, port: 1234, version: '0.2.17' },
    webui: { name: 'WebUI', status: SERVICE_STATUS.RUNNING, category: SERVICE_CATEGORIES.SYSTEM, port: 3000, version: '1.0.0' }
  });

  // System metrics
  const [systemMetrics, setSystemMetrics] = useState({
    cpu: 0,
    memory: 0,
    gpu: 0,
    disk: 0,
    network: 0,
    uptime: 0
  });

  // Workflows
  const [workflows, setWorkflows] = useState([
    {
      id: 'text-to-multimedia',
      name: 'Text to Multimedia',
      status: 'ready',
      steps: ['Text Analysis', 'Image Generation', '3D Model Creation', 'Voice Synthesis'],
      progress: 0,
      services: ['duckbot', 'comfyui', 'trellis', 'vibevoice']
    },
    {
      id: 'storytelling-pipeline',
      name: 'Storytelling Pipeline',
      status: 'ready',
      steps: ['Script Generation', 'Scene Creation', 'Character Design', 'Audio Production'],
      progress: 0,
      services: ['duckbot', 'comfyui', 'trellis', 'vibevoice']
    },
    {
      id: 'educational-content',
      name: 'Educational Content Generator',
      status: 'ready',
      steps: ['Topic Analysis', 'Content Structure', 'Visual Aids', 'Interactive Elements'],
      progress: 0,
      services: ['duckbot', 'comfyui', 'trellis']
    },
    {
      id: 'batch-processing',
      name: 'Batch Processing',
      status: 'ready',
      steps: ['Queue Setup', 'Parallel Processing', 'Quality Check', 'Output Organization'],
      progress: 0,
      services: ['duckbot', 'comfyui', 'monitoring']
    }
  ]);

  // Active workflows
  const [activeWorkflows, setActiveWorkflows] = useState([]);

  // AI Insights
  const [aiInsights, setAiInsights] = useState({
    systemOptimization: [],
    performanceAlerts: [],
    recommendations: [],
    predictiveMaintenance: []
  });

  // Configuration state
  const [config, setConfig] = useState({
    global: {
      autoOptimization: true,
      predictiveMaintenance: true,
      resourceAllocation: 'dynamic',
      securityLevel: 'high',
      backupEnabled: true
    },
    services: {},
    workflows: {
      autoRetry: true,
      parallelProcessing: true,
      qualityChecks: true
    },
    ai: {
      optimizationInterval: 300,
      confidenceThreshold: 0.8,
      learningEnabled: true
    }
  });

  // Resource allocation data for charts
  const [resourceData, setResourceData] = useState([]);
  const [servicePerformance, setServicePerformance] = useState([]);

  // Initialize dashboard
  useEffect(() => {
    initializeDashboard();
    startMonitoring();
  }, []);

  const initializeDashboard = useCallback(async () => {
    try {
      // Load service configurations
      const response = await fetch('http://localhost:8787/api/services/config');
      if (response.ok) {
        const serviceConfig = await response.json();
        setServices(prev => ({ ...prev, ...serviceConfig }));
      }

      // Load AI insights
      const insightsResponse = await fetch('http://localhost:8787/api/ai/insights');
      if (insightsResponse.ok) {
        const insights = await insightsResponse.json();
        setAiInsights(insights);
      }

    } catch (error) {
      console.error('Failed to initialize dashboard:', error);
    }
  }, []);

  const startMonitoring = useCallback(() => {
    // Update system metrics every second
    const metricsInterval = setInterval(async () => {
      try {
        const response = await fetch('http://localhost:8787/api/system/metrics');
        if (response.ok) {
          const metrics = await response.json();
          setSystemMetrics(metrics);
          updateResourceData(metrics);
        }
      } catch (error) {
        console.error('Failed to fetch metrics:', error);
      }
    }, 1000);

    // Check service health every 5 seconds
    const healthInterval = setInterval(async () => {
      await checkServiceHealth();
    }, 5000);

    // Update AI insights every 30 seconds
    const insightsInterval = setInterval(async () => {
      await updateAIInsights();
    }, 30000);

    return () => {
      clearInterval(metricsInterval);
      clearInterval(healthInterval);
      clearInterval(insightsInterval);
    };
  }, []);

  const checkServiceHealth = async () => {
    const updatedServices = { ...services };

    for (const [key, service] of Object.entries(services)) {
      try {
        const response = await fetch(`http://localhost:${service.port}/health`);
        if (response.ok) {
          updatedServices[key].status = SERVICE_STATUS.RUNNING;
          updatedServices[key].lastCheck = new Date();
        } else {
          updatedServices[key].status = SERVICE_STATUS.ERROR;
        }
      } catch (error) {
        updatedServices[key].status = SERVICE_STATUS.STOPPED;
      }
    }

    setServices(updatedServices);
    updateServicePerformance(updatedServices);
  };

  const updateAIInsights = async () => {
    try {
      const response = await fetch('http://localhost:8787/api/ai/insights');
      if (response.ok) {
        const insights = await response.json();
        setAiInsights(insights);
      }
    } catch (error) {
      console.error('Failed to update AI insights:', error);
    }
  };

  const updateResourceData = (metrics) => {
    const timestamp = new Date().toLocaleTimeString();
    const newDataPoint = {
      time: timestamp,
      cpu: metrics.cpu,
      memory: metrics.memory,
      gpu: metrics.gpu || 0,
      disk: metrics.disk || 0,
      network: metrics.network || 0
    };

    setResourceData(prev => {
      const updated = [...prev, newDataPoint];
      return updated.slice(-20); // Keep last 20 data points
    });
  };

  const updateServicePerformance = (serviceStatus) => {
    const performanceData = Object.entries(serviceStatus).map(([key, service]) => ({
      name: service.name,
      status: service.status,
      uptime: calculateUptime(service.lastCheck),
      responseTime: Math.random() * 100 + 10, // Mock response time
      requests: Math.floor(Math.random() * 1000) + 100 // Mock request count
    }));

    setServicePerformance(performanceData);
  };

  const calculateUptime = (lastCheck) => {
    if (!lastCheck) return 'Unknown';
    const uptime = Date.now() - new Date(lastCheck).getTime();
    const hours = Math.floor(uptime / (1000 * 60 * 60));
    const minutes = Math.floor((uptime % (1000 * 60 * 60)) / (1000 * 60));
    return `${hours}h ${minutes}m`;
  };

  const startWorkflow = async (workflowId) => {
    const workflow = workflows.find(w => w.id === workflowId);
    if (!workflow) return;

    const activeWorkflow = {
      ...workflow,
      startTime: new Date(),
      progress: 0,
      currentStep: 0,
      status: 'running'
    };

    setActiveWorkflows(prev => [...prev, activeWorkflow]);

    // Simulate workflow execution
    for (let i = 0; i < workflow.steps.length; i++) {
      await new Promise(resolve => setTimeout(resolve, 2000)); // 2 second delay per step

      setActiveWorkflows(prev => prev.map(w =>
        w.id === workflowId
          ? { ...w, progress: ((i + 1) / workflow.steps.length) * 100, currentStep: i }
          : w
      ));
    }

    // Mark as completed
    setActiveWorkflows(prev => prev.map(w =>
      w.id === workflowId
        ? { ...w, status: 'completed', progress: 100, currentStep: workflow.steps.length - 1 }
        : w
    ));
  };

  const stopWorkflow = (workflowId) => {
    setActiveWorkflows(prev => prev.filter(w => w.id !== workflowId));
  };

  const restartService = async (serviceKey) => {
    try {
      const service = services[serviceKey];
      const response = await fetch(`http://localhost:${service.port}/restart`, {
        method: 'POST'
      });

      if (response.ok) {
        setServices(prev => ({
          ...prev,
          [serviceKey]: { ...prev[serviceKey], status: SERVICE_STATUS.STARTING }
        }));

        // Check status after a delay
        setTimeout(() => checkServiceHealth(), 3000);
      }
    } catch (error) {
      console.error(`Failed to restart ${serviceKey}:`, error);
    }
  };

  const optimizeSystem = async () => {
    try {
      const response = await fetch('http://localhost:8787/api/system/optimize', {
        method: 'POST'
      });

      if (response.ok) {
        const optimization = await response.json();
        setConfig(prev => ({
          ...prev,
          global: { ...prev.global, ...optimization.settings }
        }));
      }
    } catch (error) {
      console.error('Failed to optimize system:', error);
    }
  };

  const updateConfig = async (section, newConfig) => {
    try {
      const response = await fetch('http://localhost:8787/api/config/update', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ section, config: newConfig })
      });

      if (response.ok) {
        setConfig(prev => ({
          ...prev,
          [section]: { ...prev[section], ...newConfig }
        }));
      }
    } catch (error) {
      console.error('Failed to update config:', error);
    }
  };

  // Chart colors
  const colors = {
    cpu: '#8884d8',
    memory: '#82ca9d',
    gpu: '#ffc658',
    disk: '#ff7300',
    network: '#00ff88'
  };

  const statusColors = {
    [SERVICE_STATUS.RUNNING]: '#10b981',
    [SERVICE_STATUS.STOPPED]: '#ef4444',
    [SERVICE_STATUS.ERROR]: '#f59e0b',
    [SERVICE_STATUS.STARTING]: '#3b82f6',
    [SERVICE_STATUS.MAINTENANCE]: '#8b5cf6'
  };

  return (
    <div className="h-full w-full bg-slate-900/95 rounded-lg flex flex-col">
      {/* Header */}
      <div className="p-6 border-b border-slate-700">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white">Unified Services Dashboard</h1>
            <p className="text-slate-400 mt-1">AI-Powered System Management and Optimization</p>
          </div>
          <div className="flex items-center space-x-4">
            <button
              onClick={optimizeSystem}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
            >
              🚀 Optimize System
            </button>
            <button
              onClick={onClose}
              className="px-4 py-2 bg-slate-600 hover:bg-slate-700 text-white rounded-lg transition-colors"
            >
              ✕
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {/* System Overview Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {Object.entries(systemMetrics).map(([key, value]) => (
            <div key={key} className="glass-strong rounded-lg p-4">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-medium text-slate-400 uppercase">{key}</h3>
                <div className={`w-3 h-3 rounded-full ${
                  value > 80 ? 'bg-red-400' : value > 60 ? 'bg-yellow-400' : 'bg-green-400'
                }`} />
              </div>
              <div className="text-2xl font-bold text-white mt-2">{value}%</div>
            </div>
          ))}
        </div>

        {/* Services Grid */}
        <div className="glass-strong rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-white">Service Status</h2>
            <div className="flex space-x-2">
              {Object.entries(SERVICE_CATEGORIES).map(([key, value]) => (
                <span key={key} className="text-xs px-2 py-1 bg-slate-700 text-slate-300 rounded">
                  {key}
                </span>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {Object.entries(services).map(([key, service]) => (
              <div key={key} className="glass-medium rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-semibold text-white">{service.name}</h3>
                  <div
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: statusColors[service.status] }}
                  />
                </div>
                <div className="text-xs text-slate-400 space-y-1">
                  <div>Port: {service.port}</div>
                  <div>Version: {service.version}</div>
                  <div className="capitalize">Status: {service.status}</div>
                </div>
                <div className="mt-3 flex space-x-2">
                  <button
                    onClick={() => restartService(key)}
                    className="text-xs px-2 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded"
                  >
                    Restart
                  </button>
                  <button
                    onClick={() => window.open(`http://localhost:${service.port}`, '_blank')}
                    className="text-xs px-2 py-1 bg-slate-600 hover:bg-slate-700 text-white rounded"
                  >
                    Open
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Resource Usage Chart */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="glass-strong rounded-lg p-6">
            <h2 className="text-xl font-bold text-white mb-4">Resource Usage</h2>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={resourceData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#475569" />
                  <XAxis dataKey="time" stroke="#94a3b8" />
                  <YAxis stroke="#94a3b8" />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569' }}
                    labelStyle={{ color: '#f1f5f9' }}
                  />
                  <Area type="monotone" dataKey="cpu" stackId="1" stroke={colors.cpu} fill={colors.cpu} fillOpacity={0.6} />
                  <Area type="monotone" dataKey="memory" stackId="1" stroke={colors.memory} fill={colors.memory} fillOpacity={0.6} />
                  <Area type="monotone" dataKey="gpu" stackId="1" stroke={colors.gpu} fill={colors.gpu} fillOpacity={0.6} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="glass-strong rounded-lg p-6">
            <h2 className="text-xl font-bold text-white mb-4">Service Performance</h2>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={servicePerformance}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#475569" />
                  <XAxis dataKey="name" stroke="#94a3b8" />
                  <YAxis stroke="#94a3b8" />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569' }}
                    labelStyle={{ color: '#f1f5f9' }}
                  />
                  <Bar dataKey="responseTime" fill={colors.cpu} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* Workflow Management */}
        <div className="glass-strong rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-white">Cross-Service Workflows</h2>
            <span className="text-sm text-slate-400">AI-Optimized Pipelines</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
            {workflows.map(workflow => (
              <div key={workflow.id} className="glass-medium rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="font-semibold text-white">{workflow.name}</h3>
                  <button
                    onClick={() => startWorkflow(workflow.id)}
                    disabled={activeWorkflows.some(w => w.id === workflow.id)}
                    className="px-3 py-1 bg-green-600 hover:bg-green-700 disabled:bg-slate-600 text-white rounded text-sm"
                  >
                    Start
                  </button>
                </div>

                <div className="space-y-2">
                  {workflow.steps.map((step, index) => {
                    const activeWorkflow = activeWorkflows.find(w => w.id === workflow.id);
                    const isActive = activeWorkflow?.currentStep === index;
                    const isCompleted = activeWorkflow ? index <= activeWorkflow.currentStep : false;

                    return (
                      <div key={index} className="flex items-center space-x-2">
                        <div className={`w-4 h-4 rounded-full flex items-center justify-center text-xs ${
                          isCompleted ? 'bg-green-500' : isActive ? 'bg-blue-500 animate-pulse' : 'bg-slate-600'
                        }`}>
                          {isCompleted ? '✓' : index + 1}
                        </div>
                        <span className={`text-sm ${isCompleted ? 'text-green-400' : isActive ? 'text-blue-400' : 'text-slate-400'}`}>
                          {step}
                        </span>
                      </div>
                    );
                  })}
                </div>

                {activeWorkflows.some(w => w.id === workflow.id) && (
                  <div className="mt-3">
                    <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
                      <span>Progress</span>
                      <span>{Math.round(activeWorkflows.find(w => w.id === workflow.id)?.progress || 0)}%</span>
                    </div>
                    <div className="w-full bg-slate-700 rounded-full h-2">
                      <div
                        className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${activeWorkflows.find(w => w.id === workflow.id)?.progress || 0}%` }}
                      />
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* AI Insights and Recommendations */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="glass-strong rounded-lg p-6">
            <h2 className="text-xl font-bold text-white mb-4">AI Insights</h2>
            <div className="space-y-3">
              {aiInsights.recommendations?.map((insight, index) => (
                <div key={index} className="flex items-start space-x-3 p-3 bg-slate-800/50 rounded-lg">
                  <div className="text-blue-400 text-sm">💡</div>
                  <div>
                    <div className="text-sm font-medium text-white">{insight.title}</div>
                    <div className="text-xs text-slate-400">{insight.description}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="glass-strong rounded-lg p-6">
            <h2 className="text-xl font-bold text-white mb-4">System Alerts</h2>
            <div className="space-y-3">
              {aiInsights.performanceAlerts?.map((alert, index) => (
                <div key={index} className="flex items-start space-x-3 p-3 bg-slate-800/50 rounded-lg">
                  <div className={`text-sm ${
                    alert.severity === 'high' ? 'text-red-400' :
                    alert.severity === 'medium' ? 'text-yellow-400' : 'text-blue-400'
                  }`}>
                    {alert.severity === 'high' ? '🚨' : alert.severity === 'medium' ? '⚠️' : 'ℹ️'}
                  </div>
                  <div>
                    <div className="text-sm font-medium text-white">{alert.title}</div>
                    <div className="text-xs text-slate-400">{alert.description}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Configuration Panel */}
        <div className="glass-strong rounded-lg p-6">
          <h2 className="text-xl font-bold text-white mb-4">Unified Configuration</h2>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div>
              <h3 className="font-semibold text-white mb-3">Global Settings</h3>
              <div className="space-y-3">
                {Object.entries(config.global).map(([key, value]) => (
                  <label key={key} className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={value}
                      onChange={(e) => updateConfig('global', { [key]: e.target.checked })}
                      className="rounded text-blue-600"
                    />
                    <span className="text-sm text-slate-300 capitalize">{key.replace(/([A-Z])/g, ' $1')}</span>
                  </label>
                ))}
              </div>
            </div>

            <div>
              <h3 className="font-semibold text-white mb-3">AI Configuration</h3>
              <div className="space-y-3">
                <div>
                  <label className="text-sm text-slate-300">Optimization Interval (s)</label>
                  <input
                    type="number"
                    value={config.ai.optimizationInterval}
                    onChange={(e) => updateConfig('ai', { optimizationInterval: parseInt(e.target.value) })}
                    className="w-full mt-1 px-2 py-1 bg-slate-700 border border-slate-600 rounded text-white text-sm"
                  />
                </div>
                <div>
                  <label className="text-sm text-slate-300">Confidence Threshold</label>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.1"
                    value={config.ai.confidenceThreshold}
                    onChange={(e) => updateConfig('ai', { confidenceThreshold: parseFloat(e.target.value) })}
                    className="w-full mt-1"
                  />
                  <div className="text-xs text-slate-400">{config.ai.confidenceThreshold}</div>
                </div>
              </div>
            </div>

            <div>
              <h3 className="font-semibold text-white mb-3">Workflow Settings</h3>
              <div className="space-y-3">
                {Object.entries(config.workflows).map(([key, value]) => (
                  <label key={key} className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={value}
                      onChange={(e) => updateConfig('workflows', { [key]: e.target.checked })}
                      className="rounded text-blue-600"
                    />
                    <span className="text-sm text-slate-300 capitalize">{key.replace(/([A-Z])/g, ' $1')}</span>
                  </label>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default UnifiedDashboard;