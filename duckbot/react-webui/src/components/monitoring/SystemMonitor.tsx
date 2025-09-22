import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useTheme } from '../../theme/ThemeContext';
import { SystemMetrics } from '../../types/dashboard';
import {
  Cpu,
  HardDrive,
  Wifi,
  Activity,
  Zap,
  MemoryStick,
  Thermometer,
  Monitor,
  RefreshCw,
  AlertTriangle,
  CheckCircle
} from 'lucide-react';

interface SystemMonitorProps {
  metrics?: SystemMetrics;
  autoRefresh?: boolean;
  refreshInterval?: number;
  showDetails?: boolean;
}

const SystemMonitor: React.FC<SystemMonitorProps> = ({
  metrics: initialMetrics,
  autoRefresh = true,
  refreshInterval = 2000,
  showDetails = true,
}) => {
  const { colors } = useTheme();
  const [metrics, setMetrics] = useState<SystemMetrics>(initialMetrics || mockMetrics);
  const [loading, setLoading] = useState(false);
  const [expandedMetrics, setExpandedMetrics] = useState<string[]>([]);

  // Mock metrics data
  const mockMetrics: SystemMetrics = {
    cpu: {
      usage: 45,
      temperature: 65,
      cores: 8,
    },
    memory: {
      usage: 67,
      total: 16384,
      available: 5440,
      used: 10944,
    },
    disk: {
      usage: 82,
      total: 1000000,
      free: 180000,
    },
    network: {
      downloadSpeed: 12.5,
      uploadSpeed: 3.2,
      latency: 15,
      status: 'connected',
    },
    gpu: {
      usage: 35,
      temperature: 72,
      memory: {
        usage: 68,
        total: 8192,
        used: 5568,
      },
    },
  };

  const refreshMetrics = async () => {
    setLoading(true);
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 500));

      // Generate realistic fluctuations
      const updatedMetrics = {
        cpu: {
          ...metrics.cpu,
          usage: Math.max(0, Math.min(100, metrics.cpu.usage + (Math.random() - 0.5) * 10)),
          temperature: Math.max(40, Math.min(90, metrics.cpu.temperature + (Math.random() - 0.5) * 5)),
        },
        memory: {
          ...metrics.memory,
          usage: Math.max(0, Math.min(100, metrics.memory.usage + (Math.random() - 0.5) * 5)),
          used: Math.max(0, Math.min(metrics.memory.total, metrics.memory.used + Math.floor((Math.random() - 0.5) * 200))),
          available: Math.max(0, metrics.memory.total - metrics.memory.used),
        },
        disk: {
          ...metrics.disk,
          usage: Math.max(0, Math.min(100, metrics.disk.usage + (Math.random() - 0.5) * 2)),
          free: Math.max(0, metrics.disk.total - (metrics.disk.total * metrics.disk.usage / 100)),
        },
        network: {
          ...metrics.network,
          downloadSpeed: Math.max(0, metrics.network.downloadSpeed + (Math.random() - 0.5) * 5),
          uploadSpeed: Math.max(0, metrics.network.uploadSpeed + (Math.random() - 0.5) * 2),
          latency: Math.max(1, Math.min(200, metrics.network.latency + (Math.random() - 0.5) * 10)),
        },
        gpu: metrics.gpu ? {
          ...metrics.gpu,
          usage: Math.max(0, Math.min(100, metrics.gpu.usage + (Math.random() - 0.5) * 15)),
          temperature: Math.max(50, Math.min(85, metrics.gpu.temperature + (Math.random() - 0.5) * 3)),
          memory: {
            ...metrics.gpu.memory,
            usage: Math.max(0, Math.min(100, metrics.gpu.memory.usage + (Math.random() - 0.5) * 10)),
            used: Math.max(0, Math.min(metrics.gpu.memory.total, metrics.gpu.memory.used + Math.floor((Math.random() - 0.5) * 100))),
          },
        } : undefined,
      };

      setMetrics(updatedMetrics);
    } catch (error) {
      console.error('Error refreshing metrics:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(refreshMetrics, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [autoRefresh, refreshInterval]);

  const formatBytes = (bytes: number): string => {
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    if (bytes === 0) return '0 B';
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
  };

  const getStatusColor = (usage: number): string => {
    if (usage >= 90) return colors.error;
    if (usage >= 75) return colors.warning;
    return colors.success;
  };

  const getTemperatureColor = (temp: number): string => {
    if (temp >= 80) return colors.error;
    if (temp >= 70) return colors.warning;
    return colors.success;
  };

  const getNetworkStatusColor = (status: string): string => {
    switch (status) {
      case 'connected': return colors.success;
      case 'disconnected': return colors.textSecondary;
      case 'error': return colors.error;
      default: return colors.textSecondary;
    }
  };

  const toggleMetric = (metric: string) => {
    setExpandedMetrics(prev =>
      prev.includes(metric)
        ? prev.filter(m => m !== metric)
        : [...prev, metric]
    );
  };

  const MetricCard = ({ title, value, unit, icon, color, details, isExpanded }: {
    title: string;
    value: number;
    unit: string;
    icon: React.ReactNode;
    color: string;
    details?: React.ReactNode;
    isExpanded: boolean;
  }) => (
    <motion.div
      whileHover={{ y: -2 }}
      className="p-4 rounded-lg border cursor-pointer"
      style={{
        backgroundColor: colors.surface,
        borderColor: colors.border,
      }}
      onClick={() => toggleMetric(title.toLowerCase())}
    >
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-3">
          <div className="flex items-center justify-center w-8 h-8 rounded-lg"
               style={{ backgroundColor: `${color}20` }}>
            {icon}
          </div>
          <div>
            <h3 className="font-semibold text-sm" style={{ color: colors.text }}>
              {title}
            </h3>
            <div className="flex items-center space-x-2">
              <span className="text-lg font-bold" style={{ color }}>
                {value}
              </span>
              <span className="text-sm" style={{ color: colors.textSecondary }}>
                {unit}
              </span>
            </div>
          </div>
        </div>
        <motion.div
          animate={{ rotate: isExpanded ? 180 : 0 }}
          className="text-xs"
          style={{ color: colors.textSecondary }}
        >
          ▼
        </motion.div>
      </div>

      {/* Progress Bar */}
      <div className="w-full h-2 rounded-full overflow-hidden mb-3"
           style={{ backgroundColor: colors.border }}>
        <motion.div
          className="h-full rounded-full"
          style={{ backgroundColor: color }}
          initial={{ width: 0 }}
          animate={{ width: `${Math.min(100, value)}%` }}
          transition={{ duration: 0.5 }}
        />
      </div>

      {/* Expanded Details */}
      <AnimatePresence>
        {isExpanded && details && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="border-t pt-3"
            style={{ borderColor: colors.border }}
          >
            {details}
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <Activity size={24} style={{ color: colors.primary }} />
          <div>
            <h2 className="text-xl font-bold" style={{ color: colors.text }}>
              System Monitor
            </h2>
            <p className="text-sm" style={{ color: colors.textSecondary }}>
              Real-time system performance metrics
            </p>
          </div>
        </div>

        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={refreshMetrics}
          disabled={loading}
          className="p-2 rounded-lg border"
          style={{
            backgroundColor: colors.background,
            borderColor: colors.border,
            color: colors.textSecondary,
          }}
        >
          <RefreshCw
            size={18}
            className={loading ? 'animate-spin' : ''}
          />
        </motion.button>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* CPU */}
        <MetricCard
          title="CPU"
          value={metrics.cpu.usage}
          unit="%"
          icon={<Cpu size={20} style={{ color: getStatusColor(metrics.cpu.usage) }} />}
          color={getStatusColor(metrics.cpu.usage)}
          isExpanded={expandedMetrics.includes('cpu')}
          details={
            <div className="space-y-2 text-xs">
              <div className="flex justify-between">
                <span style={{ color: colors.textSecondary }}>Cores:</span>
                <span style={{ color: colors.text }}>{metrics.cpu.cores}</span>
              </div>
              <div className="flex justify-between">
                <span style={{ color: colors.textSecondary }}>Temperature:</span>
                <span style={{ color: getTemperatureColor(metrics.cpu.temperature) }}>
                  {metrics.cpu.temperature}°C
                </span>
              </div>
              <div className="flex items-center space-x-1">
                <Thermometer size={12} style={{ color: getTemperatureColor(metrics.cpu.temperature) }} />
                <div className="flex-1 h-1 rounded-full overflow-hidden bg-opacity-20"
                     style={{ backgroundColor: colors.border }}>
                  <div
                    className="h-full rounded-full"
                    style={{
                      width: `${(metrics.cpu.temperature / 100) * 100}%`,
                      backgroundColor: getTemperatureColor(metrics.cpu.temperature),
                    }}
                  />
                </div>
              </div>
            </div>
          }
        />

        {/* Memory */}
        <MetricCard
          title="Memory"
          value={metrics.memory.usage}
          unit="%"
          icon={<MemoryStick size={20} style={{ color: getStatusColor(metrics.memory.usage) }} />}
          color={getStatusColor(metrics.memory.usage)}
          isExpanded={expandedMetrics.includes('memory')}
          details={
            <div className="space-y-2 text-xs">
              <div className="flex justify-between">
                <span style={{ color: colors.textSecondary }}>Used:</span>
                <span style={{ color: colors.text }}>
                  {formatBytes(metrics.memory.used)}
                </span>
              </div>
              <div className="flex justify-between">
                <span style={{ color: colors.textSecondary }}>Available:</span>
                <span style={{ color: colors.text }}>
                  {formatBytes(metrics.memory.available)}
                </span>
              </div>
              <div className="flex justify-between">
                <span style={{ color: colors.textSecondary }}>Total:</span>
                <span style={{ color: colors.text }}>
                  {formatBytes(metrics.memory.total)}
                </span>
              </div>
            </div>
          }
        />

        {/* Disk */}
        <MetricCard
          title="Disk"
          value={metrics.disk.usage}
          unit="%"
          icon={<HardDrive size={20} style={{ color: getStatusColor(metrics.disk.usage) }} />}
          color={getStatusColor(metrics.disk.usage)}
          isExpanded={expandedMetrics.includes('disk')}
          details={
            <div className="space-y-2 text-xs">
              <div className="flex justify-between">
                <span style={{ color: colors.textSecondary }}>Used:</span>
                <span style={{ color: colors.text }}>
                  {formatBytes(metrics.disk.total - metrics.disk.free)}
                </span>
              </div>
              <div className="flex justify-between">
                <span style={{ color: colors.textSecondary }}>Free:</span>
                <span style={{ color: colors.text }}>
                  {formatBytes(metrics.disk.free)}
                </span>
              </div>
              <div className="flex justify-between">
                <span style={{ color: colors.textSecondary }}>Total:</span>
                <span style={{ color: colors.text }}>
                  {formatBytes(metrics.disk.total)}
                </span>
              </div>
            </div>
          }
        />

        {/* Network */}
        <MetricCard
          title="Network"
          value={metrics.network.downloadSpeed}
          unit="Mbps"
          icon={<Wifi size={20} style={{ color: getNetworkStatusColor(metrics.network.status) }} />}
          color={getNetworkStatusColor(metrics.network.status)}
          isExpanded={expandedMetrics.includes('network')}
          details={
            <div className="space-y-2 text-xs">
              <div className="flex justify-between">
                <span style={{ color: colors.textSecondary }}>Upload:</span>
                <span style={{ color: colors.text }}>
                  {metrics.network.uploadSpeed.toFixed(1)} Mbps
                </span>
              </div>
              <div className="flex justify-between">
                <span style={{ color: colors.textSecondary }}>Latency:</span>
                <span style={{ color: colors.text }}>
                  {metrics.network.latency}ms
                </span>
              </div>
              <div className="flex justify-between">
                <span style={{ color: colors.textSecondary }}>Status:</span>
                <span style={{ color: getNetworkStatusColor(metrics.network.status) }}>
                  {metrics.network.status}
                </span>
              </div>
            </div>
          }
        />

        {/* GPU */}
        {metrics.gpu && (
          <MetricCard
            title="GPU"
            value={metrics.gpu.usage}
            unit="%"
            icon={<Monitor size={20} style={{ color: getStatusColor(metrics.gpu.usage) }} />}
            color={getStatusColor(metrics.gpu.usage)}
            isExpanded={expandedMetrics.includes('gpu')}
            details={
              <div className="space-y-2 text-xs">
                <div className="flex justify-between">
                  <span style={{ color: colors.textSecondary }}>Temperature:</span>
                  <span style={{ color: getTemperatureColor(metrics.gpu.temperature) }}>
                    {metrics.gpu.temperature}°C
                  </span>
                </div>
                <div className="flex justify-between">
                  <span style={{ color: colors.textSecondary }}>Memory:</span>
                  <span style={{ color: colors.text }}>
                    {metrics.gpu.memory.usage}%
                  </span>
                </div>
                <div className="flex justify-between">
                  <span style={{ color: colors.textSecondary }}>Memory Used:</span>
                  <span style={{ color: colors.text }}>
                    {formatBytes(metrics.gpu.memory.used)}
                  </span>
                </div>
              </div>
            }
          />
        )}
      </div>

      {/* System Summary */}
      {showDetails && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="p-4 rounded-lg border"
          style={{
            backgroundColor: colors.surface,
            borderColor: colors.border,
          }}
        >
          <h3 className="font-semibold mb-3" style={{ color: colors.text }}>
            System Health Summary
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="flex items-center space-x-2">
              <CheckCircle size={16} style={{ color: colors.success }} />
              <span className="text-sm" style={{ color: colors.textSecondary }}>
                System running normally
              </span>
            </div>
            <div className="flex items-center space-x-2">
              <Zap size={16} style={{ color: colors.warning }} />
              <span className="text-sm" style={{ color: colors.textSecondary }}>
                {metrics.disk.usage > 80 ? 'Disk space low' : 'Resource usage optimal'}
              </span>
            </div>
            <div className="flex items-center space-x-2">
              <Activity size={16} style={{ color: colors.primary }} />
              <span className="text-sm" style={{ color: colors.textSecondary }}>
                {metrics.network.status === 'connected' ? 'Network connected' : 'Network issues'}
              </span>
            </div>
          </div>
        </motion.div>
      )}
    </div>
  );
};

export default SystemMonitor;