import React, { useState, useEffect } from 'react';
import { Activity, Zap, Shield, Settings, Play, Square, RotateCcw, AlertTriangle, CheckCircle, Clock, Network, Server } from 'lucide-react';

const EnhancedSystemDashboard = () => {
  const [systemStatus, setSystemStatus] = useState({
    environment: { success: false, checks: {} },
    services: {},
    ports: {},
    loading: true,
    error: null
  });

  const [selectedService, setSelectedService] = useState(null);
  const [serviceConfigs, setServiceConfigs] = useState({
    enhanced_webui: {
      name: 'enhanced_webui',
      displayName: 'Enhanced WebUI',
      type: 'web_ui',
      description: 'Modern web interface with real-time updates',
      command: 'python -m duckbot.enhanced_webui --host 127.0.0.1 --port 8787',
      workingDir: '../..',
      ports: [{ number: 8787, name: 'WebUI', checkHealth: true, healthEndpoint: '/' }],
      autoRestart: true
    },
    system_monitoring: {
      name: 'system_monitoring',
      displayName: 'System Monitoring',
      type: 'monitoring',
      description: 'Real-time system metrics and performance tracking',
      command: 'python ai_ecosystem_manager.py',
      workingDir: '../..',
      ports: [{ number: 8789, name: 'System Monitoring', checkHealth: true, healthEndpoint: '/health' }],
      autoRestart: true
    },
    modern_webui: {
      name: 'modern_webui',
      displayName: 'Modern WebUI',
      type: 'web_ui',
      description: 'React-based modern interface',
      command: 'python duckbot/react-webui/server.py',
      workingDir: '../..',
      ports: [{ number: 8790, name: 'Modern WebUI', checkHealth: true, healthEndpoint: '/' }],
      autoRestart: true
    }
  });

  // Load system status on mount
  useEffect(() => {
    loadSystemStatus();
    const interval = setInterval(loadSystemStatus, 5000); // Update every 5 seconds
    return () => clearInterval(interval);
  }, []);

  const loadSystemStatus = async () => {
    try {
      if (window.electronAPI) {
        // Load environment status
        const envResult = await window.electronAPI.validateEnvironment();

        // Load port status
        const portStatus = await window.electronAPI.getPortStatus();

        // Load service status
        const serviceStatus = await window.electronAPI.getServiceStatus();

        setSystemStatus(prev => ({
          environment: envResult,
          ports: portStatus,
          services: serviceStatus,
          loading: false,
          error: null
        }));
      }
    } catch (error) {
      setSystemStatus(prev => ({
        ...prev,
        loading: false,
        error: error.message
      }));
    }
  };

  const startService = async (serviceName) => {
    try {
      const config = serviceConfigs[serviceName];
      if (config && window.electronAPI) {
        const result = await window.electronAPI.startService(config);
        if (result.success) {
          await loadSystemStatus();
        } else {
          alert(`Failed to start service: ${result.message}`);
        }
      }
    } catch (error) {
      alert(`Error starting service: ${error.message}`);
    }
  };

  const stopService = async (serviceName) => {
    try {
      if (window.electronAPI) {
        const result = await window.electronAPI.stopService(serviceName);
        if (result.success) {
          await loadSystemStatus();
        } else {
          alert(`Failed to stop service: ${result.message}`);
        }
      }
    } catch (error) {
      alert(`Error stopping service: ${error.message}`);
    }
  };

  const restartService = async (serviceName) => {
    try {
      if (window.electronAPI) {
        const result = await window.electronAPI.restartService(serviceName);
        if (result.success) {
          await loadSystemStatus();
        } else {
          alert(`Failed to restart service: ${result.message}`);
        }
      }
    } catch (error) {
      alert(`Error restarting service: ${error.message}`);
    }
  };

  const scanPorts = async () => {
    try {
      if (window.electronAPI) {
        await window.electronAPI.scanPorts();
        await loadSystemStatus();
      }
    } catch (error) {
      alert(`Error scanning ports: ${error.message}`);
    }
  };

  const resolveConflicts = async () => {
    try {
      if (window.electronAPI) {
        const result = await window.electronAPI.resolvePortConflicts();
        if (result.conflicts.length > 0) {
          alert(`Port conflicts detected:\n${result.suggestions.join('\n')}`);
        } else {
          alert('No port conflicts detected');
        }
      }
    } catch (error) {
      alert(`Error resolving conflicts: ${error.message}`);
    }
  };

  const formatUptime = (uptime) => {
    if (!uptime) return 'N/A';
    const seconds = Math.floor(uptime / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (days > 0) return `${days}d ${hours % 24}h`;
    if (hours > 0) return `${hours}h ${minutes % 60}m`;
    if (minutes > 0) return `${minutes}m ${seconds % 60}s`;
    return `${seconds}s`;
  };

  const getStatusIcon = (status, health) => {
    if (status === 'error' || (health && !health.isHealthy)) {
      return <AlertTriangle className="h-4 w-4 text-red-500" />;
    }
    if (status === 'running' && health && health.isHealthy) {
      return <CheckCircle className="h-4 w-4 text-green-500" />;
    }
    return <Clock className="h-4 w-4 text-yellow-500" />;
  };

  const getPortStatusColor = (portInfo) => {
    if (!portInfo.inUse) return 'text-gray-400';
    if (portInfo.healthStatus) return 'text-green-500';
    return 'text-red-500';
  };

  if (systemStatus.loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <Activity className="h-8 w-8 animate-spin mx-auto mb-2 text-blue-500" />
          <p className="text-gray-400">Loading system status...</p>
        </div>
      </div>
    );
  }

  if (systemStatus.error) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center text-red-500">
          <AlertTriangle className="h-8 w-8 mx-auto mb-2" />
          <p>Error: {systemStatus.error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">System Dashboard</h1>
          <p className="text-gray-400">Monitor and manage DuckBot services and system status</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={scanPorts}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg flex items-center gap-2"
          >
            <Network className="h-4 w-4" />
            Scan Ports
          </button>
          <button
            onClick={resolveConflicts}
            className="px-4 py-2 bg-orange-600 hover:bg-orange-700 text-white rounded-lg flex items-center gap-2"
          >
            <AlertTriangle className="h-4 w-4" />
            Resolve Conflicts
          </button>
        </div>
      </div>

      {/* Environment Status */}
      <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
        <h2 className="text-lg font-semibold mb-3 flex items-center gap-2">
          <Shield className="h-5 w-5 text-blue-500" />
          Environment Status
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {Object.entries(systemStatus.environment.checks || {}).map(([key, check]) => (
            <div key={key} className="bg-gray-900 rounded p-3">
              <div className="flex items-center justify-between mb-1">
                <span className="text-sm font-medium capitalize">{key.replace('_', ' ')}</span>
                {check.success ? (
                  <CheckCircle className="h-4 w-4 text-green-500" />
                ) : (
                  <AlertTriangle className="h-4 w-4 text-red-500" />
                )}
              </div>
              <p className="text-xs text-gray-400">{check.message || 'Unknown'}</p>
              {check.version && (
                <p className="text-xs text-gray-500 mt-1">Version: {check.version}</p>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Services Management */}
      <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
        <h2 className="text-lg font-semibold mb-3 flex items-center gap-2">
          <Server className="h-5 w-5 text-green-500" />
          Service Management
        </h2>
        <div className="grid gap-4">
          {Object.entries(serviceConfigs).map(([serviceName, config]) => {
            const service = systemStatus.services[serviceName];
            const isRunning = service?.running || false;
            const health = service?.health || {};

            return (
              <div key={serviceName} className="bg-gray-900 rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <div>
                    <h3 className="font-semibold text-white flex items-center gap-2">
                      {getStatusIcon(service?.status, health)}
                      {config.displayName}
                    </h3>
                    <p className="text-sm text-gray-400">{config.description}</p>
                  </div>
                  <div className="flex gap-2">
                    {!isRunning ? (
                      <button
                        onClick={() => startService(serviceName)}
                        className="px-3 py-1 bg-green-600 hover:bg-green-700 text-white rounded text-sm flex items-center gap-1"
                      >
                        <Play className="h-3 w-3" />
                        Start
                      </button>
                    ) : (
                      <>
                        <button
                          onClick={() => stopService(serviceName)}
                          className="px-3 py-1 bg-red-600 hover:bg-red-700 text-white rounded text-sm flex items-center gap-1"
                        >
                          <Square className="h-3 w-3" />
                          Stop
                        </button>
                        <button
                          onClick={() => restartService(serviceName)}
                          className="px-3 py-1 bg-yellow-600 hover:bg-yellow-700 text-white rounded text-sm flex items-center gap-1"
                        >
                          <RotateCcw className="h-3 w-3" />
                          Restart
                        </button>
                      </>
                    )}
                  </div>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <span className="text-gray-400">Status:</span>
                    <span className={`ml-2 ${isRunning ? 'text-green-500' : 'text-red-500'}`}>
                      {isRunning ? 'Running' : 'Stopped'}
                    </span>
                  </div>
                  {service?.pid && (
                    <div>
                      <span className="text-gray-400">PID:</span>
                      <span className="ml-2 text-gray-300">{service.pid}</span>
                    </div>
                  )}
                  {service?.uptime && (
                    <div>
                      <span className="text-gray-400">Uptime:</span>
                      <span className="ml-2 text-gray-300">{formatUptime(service.uptime)}</span>
                    </div>
                  )}
                  {service?.restartCount !== undefined && service.restartCount > 0 && (
                    <div>
                      <span className="text-gray-400">Restarts:</span>
                      <span className="ml-2 text-yellow-500">{service.restartCount}</span>
                    </div>
                  )}
                </div>

                {health && health.lastCheck && (
                  <div className="mt-2 text-xs text-gray-500">
                    Last health check: {new Date(health.lastCheck).toLocaleString()}
                    {health.responseTime && ` (${Math.round(health.responseTime)}ms)`}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Port Status */}
      <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
        <h2 className="text-lg font-semibold mb-3 flex items-center gap-2">
          <Network className="h-5 w-5 text-purple-500" />
          Port Status
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {Object.entries(systemStatus.ports || {}).map(([portNum, portInfo]) => (
            <div key={portNum} className="bg-gray-900 rounded p-3">
              <div className="flex items-center justify-between mb-2">
                <span className="font-semibold">Port {portNum}</span>
                <span className={`text-sm ${getPortStatusColor(portInfo)}`}>
                  {portInfo.inUse ? 'In Use' : 'Available'}
                </span>
              </div>
              <p className="text-sm text-gray-400 mb-1">{portInfo.name}</p>
              {portInfo.service && (
                <p className="text-xs text-gray-500">Service: {portInfo.service}</p>
              )}
              {portInfo.inUse && portInfo.healthStatus !== undefined && (
                <div className="flex items-center gap-1 mt-1">
                  {portInfo.healthStatus ? (
                    <CheckCircle className="h-3 w-3 text-green-500" />
                  ) : (
                    <AlertTriangle className="h-3 w-3 text-red-500" />
                  )}
                  <span className="text-xs text-gray-400">
                    {portInfo.healthStatus ? 'Healthy' : 'Unhealthy'}
                  </span>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default EnhancedSystemDashboard;