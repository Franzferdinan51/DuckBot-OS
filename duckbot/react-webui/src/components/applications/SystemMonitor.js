import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, ResponsiveContainer, AreaChart, Area } from 'recharts';
import { useSystem } from '../../contexts/SystemContext';
import { useAI } from '../../contexts/AIContext';

const SystemMonitor = ({ onClose }) => {
  const { systemStatus, services, getSystemHealth, fetchSystemStatus } = useSystem();
  const { costData, ragStats } = useAI();
  
  const [performanceData, setPerformanceData] = useState([]);
  const [selectedTab, setSelectedTab] = useState('overview');
  const [autoRefresh, setAutoRefresh] = useState(true);

  useEffect(() => {
    // Initial data load
    fetchSystemStatus();
    
    // Auto-refresh
    let interval;
    if (autoRefresh) {
      interval = setInterval(() => {
        fetchSystemStatus();
        
        // Add performance data point
        setPerformanceData(prev => {
          const newData = [...prev, {
            time: new Date().toLocaleTimeString(),
            cpu: systemStatus.cpu || 0,
            memory: systemStatus.memory ? Math.round((systemStatus.memory.used / systemStatus.memory.total) * 100) : 0,
            gpu: systemStatus.gpu || 0,
            timestamp: Date.now()
          }];
          
          // Keep only last 20 data points
          return newData.slice(-20);
        });
      }, 5000);
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [autoRefresh, systemStatus.cpu, systemStatus.memory, systemStatus.gpu, fetchSystemStatus]);

  const health = getSystemHealth();

  const getHealthColor = () => {
    switch (health.overall) {
      case 'excellent': return 'text-green-400';
      case 'good': return 'text-blue-400';
      case 'poor': return 'text-yellow-400';
      case 'critical': return 'text-red-400';
      default: return 'text-gray-400';
    }
  };

  const getHealthIcon = () => {
    switch (health.overall) {
      case 'excellent': return '🟢';
      case 'good': return '🔵';
      case 'poor': return '🟡';
      case 'critical': return '🔴';
      default: return '⚪';
    }
  };

  const formatUptime = (seconds) => {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    
    if (days > 0) return `${days}d ${hours}h ${minutes}m`;
    if (hours > 0) return `${hours}h ${minutes}m`;
    return `${minutes}m`;
  };

  const formatBytes = (bytes) => {
    if (!bytes || bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const tabs = [
    { id: 'overview', label: '📊 Overview', icon: '📊' },
    { id: 'performance', label: '⚡ Performance', icon: '⚡' },
    { id: 'services', label: '🔧 Services', icon: '🔧' },
    { id: 'ai-stats', label: '🤖 AI Stats', icon: '🤖' },
    { id: 'logs', label: '📋 Recent Logs', icon: '📋' }
  ];

  return (
    <div className="system-monitor h-full flex flex-col bg-slate-900">
      {/* Header */}
      <div className="flex-shrink-0 bg-slate-800 p-4 border-b border-slate-700">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="text-2xl">📊</div>
            <div>
              <h2 className="text-lg font-semibold text-white">System Monitor</h2>
              <div className="text-xs text-slate-400 flex items-center space-x-2">
                <span>{getHealthIcon()}</span>
                <span className={getHealthColor()}>System Health: {health.overall}</span>
                <span>•</span>
                <span>Uptime: {formatUptime(systemStatus.uptime || 0)}</span>
              </div>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            <label className="flex items-center space-x-2 text-sm text-slate-300">
              <input
                type="checkbox"
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
                className="rounded"
              />
              <span>Auto-refresh</span>
            </label>
            <button
              onClick={fetchSystemStatus}
              className="btn-secondary text-sm"
            >
              🔄 Refresh
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex space-x-1 mt-4 bg-slate-700/50 rounded-lg p-1">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setSelectedTab(tab.id)}
              className={`flex-1 px-3 py-2 rounded text-sm transition-all ${
                selectedTab === tab.id
                  ? 'bg-blue-500 text-white'
                  : 'text-slate-300 hover:bg-slate-600'
              }`}
            >
              {tab.icon} {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {selectedTab === 'overview' && (
          <div className="space-y-6">
            {/* System Overview Cards */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
              <SystemCard
                title="CPU Usage"
                value={`${systemStatus.cpu || 0}%`}
                icon="🔥"
                color={systemStatus.cpu > 80 ? 'text-red-400' : systemStatus.cpu > 60 ? 'text-yellow-400' : 'text-green-400'}
              />
              <SystemCard
                title="Memory Usage"
                value={systemStatus.memory ? `${Math.round((systemStatus.memory.used / systemStatus.memory.total) * 100)}%` : '0%'}
                subtitle={systemStatus.memory ? `${formatBytes(systemStatus.memory.used)} / ${formatBytes(systemStatus.memory.total)}` : 'N/A'}
                icon="🧠"
                color={systemStatus.memory && (systemStatus.memory.used / systemStatus.memory.total) > 0.8 ? 'text-red-400' : 'text-green-400'}
              />
              <SystemCard
                title="GPU Usage"
                value={`${systemStatus.gpu || 0}%`}
                icon="🎮"
                color={systemStatus.gpu > 80 ? 'text-red-400' : 'text-green-400'}
              />
              <SystemCard
                title="Services"
                value={`${health.runningServices}/${health.totalServices}`}
                subtitle={`${health.percentage}% running`}
                icon="⚙️"
                color={health.criticalServices < health.totalCriticalServices ? 'text-red-400' : 'text-green-400'}
              />
            </div>

            {/* Health Status */}
            <div className="glass rounded-lg p-6">
              <h3 className="text-lg font-semibold text-white mb-4">System Health</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="text-center">
                  <div className={`text-4xl ${getHealthColor()}`}>{getHealthIcon()}</div>
                  <div className={`text-2xl font-bold ${getHealthColor()}`}>{health.overall}</div>
                  <div className="text-sm text-slate-400">Overall Health</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl text-blue-400">⚙️</div>
                  <div className="text-xl font-bold text-white">{health.runningServices}/{health.totalServices}</div>
                  <div className="text-sm text-slate-400">Services Running</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl text-red-400">🚨</div>
                  <div className="text-xl font-bold text-white">{health.criticalServices}/{health.totalCriticalServices}</div>
                  <div className="text-sm text-slate-400">Critical Services</div>
                </div>
              </div>
            </div>
          </div>
        )}

        {selectedTab === 'performance' && (
          <div className="space-y-6">
            <div className="glass rounded-lg p-6">
              <h3 className="text-lg font-semibold text-white mb-4">Real-time Performance</h3>
              {performanceData.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={performanceData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                    <XAxis dataKey="time" stroke="#cbd5e1" fontSize={12} />
                    <YAxis stroke="#cbd5e1" fontSize={12} />
                    <Area 
                      type="monotone" 
                      dataKey="cpu" 
                      stackId="1"
                      stroke="#ef4444" 
                      fill="rgba(239, 68, 68, 0.3)"
                      name="CPU %"
                    />
                    <Area 
                      type="monotone" 
                      dataKey="memory" 
                      stackId="2"
                      stroke="#3b82f6" 
                      fill="rgba(59, 130, 246, 0.3)"
                      name="Memory %"
                    />
                    {systemStatus.gpu > 0 && (
                      <Area 
                        type="monotone" 
                        dataKey="gpu" 
                        stackId="3"
                        stroke="#10b981" 
                        fill="rgba(16, 185, 129, 0.3)"
                        name="GPU %"
                      />
                    )}
                  </AreaChart>
                </ResponsiveContainer>
              ) : (
                <div className="text-center text-slate-400 py-16">
                  <div className="text-4xl mb-4">📊</div>
                  <p>Collecting performance data...</p>
                  <p className="text-sm mt-2">Charts will appear after a few seconds</p>
                </div>
              )}
            </div>

            {/* Resource Breakdown */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="glass rounded-lg p-4">
                <h4 className="font-semibold text-white mb-3">CPU Details</h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Current Usage:</span>
                    <span className="text-white">{systemStatus.cpu || 0}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Cores Available:</span>
                    <span className="text-white">{navigator.hardwareConcurrency || 'Unknown'}</span>
                  </div>
                  <div className="w-full bg-slate-700 rounded-full h-2">
                    <div 
                      className="bg-red-400 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${systemStatus.cpu || 0}%` }}
                    />
                  </div>
                </div>
              </div>

              <div className="glass rounded-lg p-4">
                <h4 className="font-semibold text-white mb-3">Memory Details</h4>
                {systemStatus.memory ? (
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-slate-400">Used:</span>
                      <span className="text-white">{formatBytes(systemStatus.memory.used)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Total:</span>
                      <span className="text-white">{formatBytes(systemStatus.memory.total)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Free:</span>
                      <span className="text-white">{formatBytes(systemStatus.memory.total - systemStatus.memory.used)}</span>
                    </div>
                    <div className="w-full bg-slate-700 rounded-full h-2">
                      <div 
                        className="bg-blue-400 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${(systemStatus.memory.used / systemStatus.memory.total) * 100}%` }}
                      />
                    </div>
                  </div>
                ) : (
                  <div className="text-slate-400 text-sm">Memory information not available</div>
                )}
              </div>
            </div>
          </div>
        )}

        {selectedTab === 'services' && (
          <div className="space-y-4">
            {services.map(service => (
              <ServiceCard key={service.id} service={service} />
            ))}
          </div>
        )}

        {selectedTab === 'ai-stats' && (
          <div className="space-y-6">
            {/* AI Usage Stats */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
              <SystemCard
                title="Daily Cost"
                value={`$${costData.daily || '0.00'}`}
                icon="💰"
                color="text-green-400"
              />
              <SystemCard
                title="Monthly Cost"
                value={`$${costData.monthly || '0.00'}`}
                icon="📊"
                color="text-blue-400"
              />
              <SystemCard
                title="RAG Documents"
                value={ragStats.totalDocuments || 0}
                icon="📚"
                color="text-purple-400"
              />
              <SystemCard
                title="Index Size"
                value={ragStats.indexSize || '0 MB'}
                icon="💾"
                color="text-cyan-400"
              />
            </div>

            {/* AI Provider Status */}
            <div className="glass rounded-lg p-6">
              <h3 className="text-lg font-semibold text-white mb-4">AI Provider Status</h3>
              <div className="space-y-3">
                <ProviderStatus name="DuckBot AI Router" status="running" />
                <ProviderStatus name="LM Studio" status="unknown" />
                <ProviderStatus name="OpenRouter" status="connected" />
              </div>
            </div>
          </div>
        )}

        {selectedTab === 'logs' && (
          <div className="space-y-4">
            <div className="glass rounded-lg p-6">
              <h3 className="text-lg font-semibold text-white mb-4">Recent System Events</h3>
              <div className="space-y-2 max-h-96 overflow-y-auto">
                <LogEntry 
                  time="14:23:45" 
                  level="INFO" 
                  message="System health check completed - Status: Excellent" 
                />
                <LogEntry 
                  time="14:22:30" 
                  level="INFO" 
                  message="AI model switched to duckbot-auto" 
                />
                <LogEntry 
                  time="14:20:15" 
                  level="WARN" 
                  message="High CPU usage detected (85%)" 
                />
                <LogEntry 
                  time="14:18:00" 
                  level="INFO" 
                  message="Service 'comfyui' status changed to running" 
                />
                <LogEntry 
                  time="14:15:45" 
                  level="INFO" 
                  message="RAG index updated - 15 new documents processed" 
                />
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// Helper Components
const SystemCard = ({ title, value, subtitle, icon, color = 'text-white' }) => (
  <motion.div
    whileHover={{ scale: 1.02 }}
    className="glass rounded-lg p-4"
  >
    <div className="flex items-center space-x-3">
      <div className="text-2xl">{icon}</div>
      <div>
        <div className="text-xs text-slate-400 font-medium">{title}</div>
        <div className={`text-lg font-bold ${color}`}>{value}</div>
        {subtitle && <div className="text-xs text-slate-500">{subtitle}</div>}
      </div>
    </div>
  </motion.div>
);

const ServiceCard = ({ service }) => (
  <motion.div
    whileHover={{ scale: 1.01 }}
    className="glass rounded-lg p-4"
  >
    <div className="flex items-center justify-between">
      <div className="flex items-center space-x-3">
        <div className={`w-3 h-3 rounded-full ${
          service.status === 'running' ? 'bg-green-400' :
          service.status === 'stopped' ? 'bg-red-400' : 'bg-yellow-400'
        }`} />
        <div>
          <div className="font-medium text-white">{service.name}</div>
          <div className="text-xs text-slate-400">{service.description}</div>
        </div>
      </div>
      <div className="flex items-center space-x-2">
        {service.port && (
          <span className="text-xs bg-slate-700 px-2 py-1 rounded">:{service.port}</span>
        )}
        <span className={`text-xs px-2 py-1 rounded ${
          service.status === 'running' ? 'bg-green-500/20 text-green-400' :
          service.status === 'stopped' ? 'bg-red-500/20 text-red-400' : 'bg-yellow-500/20 text-yellow-400'
        }`}>
          {service.status}
        </span>
      </div>
    </div>
  </motion.div>
);

const ProviderStatus = ({ name, status }) => (
  <div className="flex items-center justify-between p-3 bg-slate-800/50 rounded">
    <span className="text-white">{name}</span>
    <span className={`px-2 py-1 rounded text-xs ${
      status === 'running' || status === 'connected' ? 'bg-green-500/20 text-green-400' :
      status === 'stopped' ? 'bg-red-500/20 text-red-400' : 'bg-yellow-500/20 text-yellow-400'
    }`}>
      {status}
    </span>
  </div>
);

const LogEntry = ({ time, level, message }) => (
  <div className="flex items-start space-x-3 p-2 hover:bg-slate-800/50 rounded">
    <span className="text-xs text-slate-500 font-mono">{time}</span>
    <span className={`text-xs px-1.5 py-0.5 rounded font-semibold ${
      level === 'INFO' ? 'bg-blue-500/20 text-blue-400' :
      level === 'WARN' ? 'bg-yellow-500/20 text-yellow-400' :
      level === 'ERROR' ? 'bg-red-500/20 text-red-400' : 'bg-gray-500/20 text-gray-400'
    }`}>
      {level}
    </span>
    <span className="text-sm text-slate-300 flex-1">{message}</span>
  </div>
);

export default SystemMonitor;