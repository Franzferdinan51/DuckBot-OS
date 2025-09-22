import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Wifi, Battery, Volume2, Settings, Clock, Power,
  Cpu, HardDrive, Activity, WifiOff, Thermometer, Zap,
  Monitor, Server, Network, MemoryStick, AlertCircle
} from 'lucide-react';
import { SystemTrayProps } from './types';

interface SystemMetrics {
  cpu: {
    percent: number;
    count: number;
    freq: { current: number };
    temp?: number;
    load_avg?: number[];
  };
  memory: {
    percent: number;
    total: number;
    available: number;
    used: number;
    swap: {
      percent: number;
      total: number;
      used: number;
    };
  };
  disk: {
    percent: number;
    total: number;
    used: number;
    free: number;
    io: {
      read_bytes: number;
      write_bytes: number;
    };
  };
  network: {
    bytes_sent: number;
    bytes_recv: number;
    packets_sent: number;
    packets_recv: number;
    connections: number;
    interfaces: Array<{
      name: string;
      ip: string;
      is_wifi: boolean;
    }>;
  };
  battery?: {
    percent: number;
    plugged: boolean;
    time_left?: number;
  };
  system: {
    hostname: string;
    platform: string;
    platform_version: string;
    process_count: number;
    boot_time: string;
    uptime: number;
  };
  timestamp: string;
}

const SystemTray: React.FC<SystemTrayProps> = ({ onSettingsClick, onPowerClick }) => {
  const [currentTime, setCurrentTime] = useState('');
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Update time
  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setCurrentTime(now.toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      }));
    };

    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  // Fetch system metrics
  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const response = await fetch('/api/system-metrics');
        const data = await response.json();

        if (data.success) {
          setMetrics(data.data);
          setError(null);
        } else {
          setError(data.error || 'Failed to fetch metrics');
        }
      } catch (err) {
        setError('Network error');
      } finally {
        setLoading(false);
      }
    };

    fetchMetrics();
    const interval = setInterval(fetchMetrics, 2000); // Update every 2 seconds
    return () => clearInterval(interval);
  }, []);

  // Utility functions for formatting
  const formatBytes = (bytes: number): string => {
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    if (bytes === 0) return '0 B';
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${sizes[i]}`;
  };

  const formatUptime = (seconds: number): string => {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);

    if (days > 0) return `${days}d ${hours}h`;
    if (hours > 0) return `${hours}h ${minutes}m`;
    return `${minutes}m`;
  };

  const getColorForPercent = (percent: number): string => {
    if (percent < 50) return 'text-green-400';
    if (percent < 80) return 'text-yellow-400';
    return 'text-red-400';
  };

  const getProgressColor = (percent: number): string => {
    if (percent < 50) return 'bg-green-500';
    if (percent < 80) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  // Tooltip component
  const Tooltip: React.FC<{
    children: React.ReactNode;
    content: React.ReactNode;
    position?: 'top' | 'bottom';
  }> = ({ children, content, position = 'bottom' }) => (
    <div className="relative group">
      {children}
      <div className={`absolute ${position === 'bottom' ? 'bottom-full mb-2' : 'top-full mt-2'} left-1/2 transform -translate-x-1/2 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50`}>
        <div className="bg-gray-900 text-white text-xs rounded-md shadow-lg border border-gray-700 px-3 py-2 min-w-max">
          {content}
        </div>
      </div>
    </div>
  );

  // Mini progress bar component
  const MiniProgress: React.FC<{ value: number; width?: number }> = ({ value, width = 40 }) => (
    <div className="relative">
      <div className={`h-1.5 bg-gray-600 rounded-full overflow-hidden`} style={{ width }}>
        <motion.div
          className={`h-full ${getProgressColor(value)} rounded-full`}
          initial={{ width: 0 }}
          animate={{ width: `${value}%` }}
          transition={{ duration: 0.5 }}
        />
      </div>
    </div>
  );

  if (loading) {
    return (
      <div className="flex items-center space-x-2 px-4">
        <div className="animate-spin w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full"></div>
        <span className="text-gray-400 text-sm">Loading...</span>
      </div>
    );
  }

  if (error || !metrics) {
    return (
      <div className="flex items-center space-x-2 px-4">
        <AlertCircle className="w-4 h-4 text-red-400" />
        <span className="text-gray-400 text-sm">System metrics unavailable</span>
      </div>
    );
  }

  return (
    <div className="flex items-center space-x-2 px-2 bg-gray-900/80 backdrop-blur-sm border-t border-gray-700">
      {/* CPU Usage */}
      <Tooltip content={
        <div className="space-y-1">
          <div className="font-semibold">CPU Usage</div>
          <div>Cores: {metrics.cpu.count}</div>
          <div>Frequency: {metrics.cpu.freq.current.toFixed(0)} MHz</div>
          {metrics.cpu.temp && <div>Temperature: {metrics.cpu.temp.toFixed(1)}°C</div>}
          {metrics.cpu.load_avg && (
            <div>Load: {metrics.cpu.load_avg.slice(0, 3).map(l => l.toFixed(2)).join(', ')}</div>
          )}
          <div>Usage: {metrics.cpu.percent.toFixed(1)}%</div>
        </div>
      }>
        <div className="flex items-center space-x-1 px-2 py-1 rounded hover:bg-gray-700/50 transition-colors">
          <Cpu className={`w-4 h-4 ${getColorForPercent(metrics.cpu.percent)}`} />
          <MiniProgress value={metrics.cpu.percent} />
          <span className={`text-xs ${getColorForPercent(metrics.cpu.percent)}`}>
            {metrics.cpu.percent.toFixed(0)}%
          </span>
        </div>
      </Tooltip>

      {/* Memory Usage */}
      <Tooltip content={
        <div className="space-y-1">
          <div className="font-semibold">Memory Usage</div>
          <div>Total: {formatBytes(metrics.memory.total)}</div>
          <div>Used: {formatBytes(metrics.memory.used)}</div>
          <div>Available: {formatBytes(metrics.memory.available)}</div>
          <div>Swap: {metrics.memory.swap.percent.toFixed(1)}% ({formatBytes(metrics.memory.swap.used)})</div>
          <div>Usage: {metrics.memory.percent.toFixed(1)}%</div>
        </div>
      }>
        <div className="flex items-center space-x-1 px-2 py-1 rounded hover:bg-gray-700/50 transition-colors">
          <MemoryStick className={`w-4 h-4 ${getColorForPercent(metrics.memory.percent)}`} />
          <MiniProgress value={metrics.memory.percent} />
          <span className={`text-xs ${getColorForPercent(metrics.memory.percent)}`}>
            {metrics.memory.percent.toFixed(0)}%
          </span>
        </div>
      </Tooltip>

      {/* Disk Usage */}
      <Tooltip content={
        <div className="space-y-1">
          <div className="font-semibold">Disk Usage</div>
          <div>Total: {formatBytes(metrics.disk.total)}</div>
          <div>Used: {formatBytes(metrics.disk.used)}</div>
          <div>Free: {formatBytes(metrics.disk.free)}</div>
          <div>Read: {formatBytes(metrics.disk.io.read_bytes)}</div>
          <div>Write: {formatBytes(metrics.disk.io.write_bytes)}</div>
          <div>Usage: {metrics.disk.percent.toFixed(1)}%</div>
        </div>
      }>
        <div className="flex items-center space-x-1 px-2 py-1 rounded hover:bg-gray-700/50 transition-colors">
          <HardDrive className={`w-4 h-4 ${getColorForPercent(metrics.disk.percent)}`} />
          <MiniProgress value={metrics.disk.percent} />
          <span className={`text-xs ${getColorForPercent(metrics.disk.percent)}`}>
            {metrics.disk.percent.toFixed(0)}%
          </span>
        </div>
      </Tooltip>

      {/* Network Status */}
      <Tooltip content={
        <div className="space-y-1">
          <div className="font-semibold">Network Activity</div>
          <div>Interfaces: {metrics.network.interfaces.length}</div>
          <div>Connections: {metrics.network.connections}</div>
          <div>Sent: {formatBytes(metrics.network.bytes_sent)}</div>
          <div>Received: {formatBytes(metrics.network.bytes_recv)}</div>
          {metrics.network.interfaces.map(iface => (
            <div key={iface.name}>
              {iface.name}: {iface.ip} {iface.is_wifi ? '📶' : '🔌'}
            </div>
          ))}
        </div>
      }>
        <div className="flex items-center space-x-1 px-2 py-1 rounded hover:bg-gray-700/50 transition-colors">
          {metrics.network.interfaces.some(i => i.is_wifi) ? (
            <Wifi className="w-4 h-4 text-green-400" />
          ) : (
            <Network className="w-4 h-4 text-blue-400" />
          )}
          <span className="text-xs text-gray-300">
            {metrics.network.connections > 0 ? 'Connected' : 'No Connection'}
          </span>
        </div>
      </Tooltip>

      {/* Battery Status */}
      {metrics.battery && (
        <Tooltip content={
          <div className="space-y-1">
            <div className="font-semibold">Battery Status</div>
            <div>Level: {metrics.battery.percent.toFixed(1)}%</div>
            <div>Status: {metrics.battery.plugged ? 'Charging' : 'Discharging'}</div>
            {metrics.battery.time_left && metrics.battery.time_left > 0 && (
              <div>Time Left: {Math.floor(metrics.battery.time_left / 3600)}h {Math.floor((metrics.battery.time_left % 3600) / 60)}m</div>
            )}
          </div>
        }>
          <div className="flex items-center space-x-1 px-2 py-1 rounded hover:bg-gray-700/50 transition-colors">
            <Battery className={`w-4 h-4 ${getColorForPercent(100 - metrics.battery.percent)}`} />
            <div className="relative w-6 h-3 border border-gray-400 rounded-sm flex items-center">
              <motion.div
                className={`h-2 rounded-sm ${getProgressColor(100 - metrics.battery.percent)}`}
                initial={{ width: 0 }}
                animate={{ width: `${metrics.battery.percent}%` }}
                transition={{ duration: 0.5 }}
                style={{ maxWidth: '20px' }}
              />
            </div>
            <span className={`text-xs ${getColorForPercent(100 - metrics.battery.percent)}`}>
              {metrics.battery.percent.toFixed(0)}%
            </span>
            {metrics.battery.plugged && (
              <Zap className="w-3 h-3 text-yellow-400" />
            )}
          </div>
        </Tooltip>
      )}

      {/* System Uptime */}
      <Tooltip content={
        <div className="space-y-1">
          <div className="font-semibold">System Information</div>
          <div>Host: {metrics.system.hostname}</div>
          <div>Platform: {metrics.system.platform}</div>
          <div>Processes: {metrics.system.process_count}</div>
          <div>Uptime: {formatUptime(metrics.system.uptime)}</div>
          <div>Boot: {new Date(metrics.system.boot_time).toLocaleTimeString()}</div>
        </div>
      }>
        <div className="flex items-center space-x-1 px-2 py-1 rounded hover:bg-gray-700/50 transition-colors">
          <Server className="w-4 h-4 text-gray-400" />
          <span className="text-xs text-gray-300">
            {formatUptime(metrics.system.uptime)}
          </span>
        </div>
      </Tooltip>

      {/* System Clock */}
      <Tooltip content={
        <div className="space-y-1">
          <div className="font-semibold">System Time</div>
          <div>Local Time: {new Date().toLocaleString()}</div>
          <div>Uptime: {formatUptime(metrics.system.uptime)}</div>
          <div>Last Update: {new Date(metrics.timestamp).toLocaleTimeString()}</div>
        </div>
      }>
        <div className="flex items-center space-x-1 px-2 py-1 rounded hover:bg-gray-700/50 transition-colors">
          <Clock className="w-4 h-4 text-gray-300" />
          <span className="text-sm text-gray-300 font-mono">
            {currentTime}
          </span>
        </div>
      </Tooltip>

      {/* Settings */}
      <Tooltip content="System Settings">
        <button
          onClick={onSettingsClick}
          className="p-1 rounded hover:bg-gray-700/50 transition-colors"
        >
          <Settings className="w-4 h-4 text-gray-400 hover:text-gray-300 transition-colors" />
        </button>
      </Tooltip>

      {/* Power */}
      <Tooltip content="Power Options">
        <button
          onClick={onPowerClick}
          className="p-1 rounded hover:bg-red-600/20 transition-colors"
        >
          <Power className="w-4 h-4 text-gray-400 hover:text-red-400 transition-colors" />
        </button>
      </Tooltip>
    </div>
  );
};

export default SystemTray;