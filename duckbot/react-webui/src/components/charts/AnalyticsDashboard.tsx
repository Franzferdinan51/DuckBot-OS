import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useTheme } from '../../theme/ThemeContext';
import MetricsChart from './MetricsChart';
import {
  BarChart3,
  TrendingUp,
  Activity,
  Zap,
  Cpu,
  HardDrive,
  RefreshCw,
  Download,
  Calendar,
  Filter
} from 'lucide-react';

interface AnalyticsDashboardProps {
  className?: string;
  timeRange?: '1h' | '24h' | '7d' | '30d';
  autoRefresh?: boolean;
  refreshInterval?: number;
}

const AnalyticsDashboard: React.FC<AnalyticsDashboardProps> = ({
  className,
  timeRange = '1h',
  autoRefresh = true,
  refreshInterval = 10000,
}) => {
  const { colors } = useTheme();
  const [metricsData, setMetricsData] = useState<any>({});
  const [loading, setLoading] = useState(false);

  // Generate mock time series data
  const generateTimeSeriesData = (baseValue: number, variance: number, points: number = 20) => {
    const now = new Date();
    return Array.from({ length: points }, (_, i) => {
      const time = new Date(now.getTime() - (points - i - 1) * (60 * 60 * 1000 / points));
      return {
        time: time.toISOString(),
        value: Math.max(0, baseValue + (Math.random() - 0.5) * variance),
      };
    });
  };

  // Generate mock data
  const generateMockData = () => {
    const now = new Date();

    return {
      cpu: generateTimeSeriesData(45, 15),
      memory: generateTimeSeriesData(65, 20),
      disk: generateTimeSeriesData(80, 5),
      network: {
        download: generateTimeSeriesData(12, 8),
        upload: generateTimeSeriesData(3, 2),
      },
      responseTime: generateTimeSeriesData(250, 100),
      successRate: generateTimeSeriesData(95, 5),
      agentActivity: [
        { name: 'Qwen 30B', value: 35, color: colors.primary },
        { name: 'ByteBot', value: 25, color: colors.success },
        { name: 'System Monitor', value: 20, color: colors.warning },
        { name: 'Others', value: 20, color: colors.textSecondary },
      ],
      serviceHealth: [
        { name: 'LM Studio', value: 98, color: colors.success },
        { name: 'AI Manager', value: 92, color: colors.success },
        { name: 'WebUI', value: 87, color: colors.warning },
        { name: 'MCP Server', value: 95, color: colors.success },
      ],
      errorDistribution: [
        { name: 'Network', value: 3, color: colors.error },
        { name: 'Memory', value: 2, color: colors.warning },
        { name: 'Timeout', value: 1, color: colors.warning },
        { name: 'Other', value: 1, color: colors.textSecondary },
      ],
    };
  };

  const refreshData = async () => {
    setLoading(true);
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      setMetricsData(generateMockData());
    } catch (error) {
      console.error('Error refreshing analytics data:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refreshData();
    if (autoRefresh) {
      const interval = setInterval(refreshData, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [autoRefresh, refreshInterval, timeRange]);

  const statsCards = [
    {
      label: 'Avg Response Time',
      value: '245ms',
      change: '-12ms',
      trend: 'down',
      icon: Zap,
      color: colors.success,
    },
    {
      label: 'Success Rate',
      value: '96.2%',
      change: '+2.1%',
      trend: 'up',
      icon: Activity,
      color: colors.success,
    },
    {
      label: 'Active Agents',
      value: '4',
      change: '+1',
      trend: 'up',
      icon: Cpu,
      color: colors.primary,
    },
    {
      label: 'Error Rate',
      value: '0.8%',
      change: '-0.3%',
      trend: 'down',
      icon: TrendingUp,
      color: colors.success,
    },
  ];

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <BarChart3 size={24} style={{ color: colors.primary }} />
          <div>
            <h2 className="text-xl font-bold" style={{ color: colors.text }}>
              Analytics Dashboard
            </h2>
            <p className="text-sm" style={{ color: colors.textSecondary }}>
              System performance and usage analytics
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          {/* Time Range Selector */}
          <select
            value={timeRange}
            onChange={(e) => console.log('Time range changed:', e.target.value)}
            className="px-3 py-2 rounded-lg border text-sm"
            style={{
              backgroundColor: colors.background,
              borderColor: colors.border,
              color: colors.text,
            }}
          >
            <option value="1h">Last Hour</option>
            <option value="24h">Last 24 Hours</option>
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
          </select>

          {/* Export Button */}
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="flex items-center space-x-2 px-3 py-2 rounded-lg border text-sm"
            style={{
              backgroundColor: colors.background,
              borderColor: colors.border,
              color: colors.text,
            }}
          >
            <Download size={16} />
            <span>Export</span>
          </motion.button>

          {/* Refresh Button */}
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={refreshData}
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
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {statsCards.map((stat, index) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className="p-4 rounded-lg border"
            style={{
              backgroundColor: colors.surface,
              borderColor: colors.border,
            }}
          >
            <div className="flex items-center justify-between mb-2">
              <stat.icon size={20} style={{ color: stat.color }} />
              <span className="text-xs font-medium px-2 py-1 rounded-full"
                    style={{
                      backgroundColor: stat.change.startsWith('+') ? `${colors.success}20` : `${colors.error}20`,
                      color: stat.change.startsWith('+') ? colors.success : colors.error,
                    }}>
                    {stat.change}
                  </span>
            </div>
            <h3 className="text-lg font-bold" style={{ color: colors.text }}>
              {stat.value}
            </h3>
            <p className="text-sm" style={{ color: colors.textSecondary }}>
              {stat.label}
            </p>
          </motion.div>
        ))}
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* System Resources */}
        <div className="p-4 rounded-lg border"
             style={{ backgroundColor: colors.surface, borderColor: colors.border }}>
          <MetricsChart
            type="area"
            title="System Resources"
            description="CPU and Memory usage over time"
            data={metricsData.cpu?.map((cpu: any, i: number) => ({
              time: cpu.time,
              cpu: cpu.value,
              memory: metricsData.memory?.[i]?.value || 0,
            })) || []}
            dataKeys={[
              { key: 'cpu', name: 'CPU %', color: colors.primary },
              { key: 'memory', name: 'Memory %', color: colors.success },
            ]}
            unit="%"
            threshold={{
              value: 80,
              color: colors.error,
              label: 'Warning Threshold',
            }}
          />
        </div>

        {/* Network Traffic */}
        <div className="p-4 rounded-lg border"
             style={{ backgroundColor: colors.surface, borderColor: colors.border }}>
          <MetricsChart
            type="line"
            title="Network Traffic"
            description="Download and upload speeds"
            data={metricsData.network?.download?.map((download: any, i: number) => ({
              time: download.time,
              download: download.value,
              upload: metricsData.network?.upload?.[i]?.value || 0,
            })) || []}
            dataKeys={[
              { key: 'download', name: 'Download', color: colors.primary },
              { key: 'upload', name: 'Upload', color: colors.success },
            ]}
            unit=" Mbps"
          />
        </div>

        {/* Response Time */}
        <div className="p-4 rounded-lg border"
             style={{ backgroundColor: colors.surface, borderColor: colors.border }}>
          <MetricsChart
            type="line"
            title="Response Time"
            description="Average system response times"
            data={metricsData.responseTime || []}
            dataKeys={[
              { key: 'value', name: 'Response Time', color: colors.warning },
            ]}
            unit="ms"
            threshold={{
              value: 500,
              color: colors.error,
              label: 'Slow Response',
            }}
          />
        </div>

        {/* Success Rate */}
        <div className="p-4 rounded-lg border"
             style={{ backgroundColor: colors.surface, borderColor: colors.border }}>
          <MetricsChart
            type="area"
            title="Success Rate"
            description="System operation success rates"
            data={metricsData.successRate || []}
            dataKeys={[
              { key: 'value', name: 'Success Rate', color: colors.success },
            ]}
            unit="%"
            threshold={{
              value: 90,
              color: colors.warning,
              label: 'Minimum Target',
            }}
          />
        </div>

        {/* Agent Activity Distribution */}
        <div className="p-4 rounded-lg border"
             style={{ backgroundColor: colors.surface, borderColor: colors.border }}>
          <MetricsChart
            type="pie"
            title="Agent Activity Distribution"
            description="Resource usage by AI agents"
            data={metricsData.agentActivity || []}
            dataKeys={metricsData.agentActivity?.map((agent: any) => ({
              key: 'value',
              name: agent.name,
              color: agent.color,
            })) || []}
            unit="%"
          />
        </div>

        {/* Service Health */}
        <div className="p-4 rounded-lg border"
             style={{ backgroundColor: colors.surface, borderColor: colors.border }}>
          <MetricsChart
            type="bar"
            title="Service Health Scores"
            description="Current health status of all services"
            data={metricsData.serviceHealth?.map((service: any) => ({
              name: service.name,
              value: service.value,
            })) || []}
            dataKeys={metricsData.serviceHealth?.map((service: any) => ({
              key: 'value',
              name: service.name,
              color: service.color,
            })) || []}
            unit="%"
            threshold={{
              value: 85,
              color: colors.warning,
              label: 'Health Threshold',
            }}
          />
        </div>
      </div>

      {/* Error Analysis */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="p-4 rounded-lg border"
             style={{ backgroundColor: colors.surface, borderColor: colors.border }}>
          <MetricsChart
            type="pie"
            title="Error Distribution"
            description="Types of system errors encountered"
            data={metricsData.errorDistribution || []}
            dataKeys={metricsData.errorDistribution?.map((error: any) => ({
              key: 'value',
              name: error.name,
              color: error.color,
            })) || []}
            showLegend={true}
          />
        </div>

        <div className="p-4 rounded-lg border"
             style={{ backgroundColor: colors.surface, borderColor: colors.border }}>
          <h3 className="text-lg font-semibold mb-4" style={{ color: colors.text }}>
            Performance Insights
          </h3>
          <div className="space-y-3">
            {[
              {
                type: 'success',
                title: 'Optimal Performance',
                description: 'System response times are within acceptable ranges',
              },
              {
                type: 'warning',
                title: 'Memory Usage High',
                description: 'Consider investigating memory optimization opportunities',
              },
              {
                type: 'info',
                title: 'Agent Efficiency',
                description: 'AI agents are performing well with good success rates',
              },
            ].map((insight, index) => (
              <div
                key={index}
                className="p-3 rounded-lg border-l-4"
                style={{
                  backgroundColor: colors.background,
                  borderColor: 'transparent',
                  borderLeftColor: insight.type === 'success' ? colors.success :
                                  insight.type === 'warning' ? colors.warning :
                                  insight.type === 'error' ? colors.error : colors.info,
                }}
              >
                <h4 className="font-medium text-sm" style={{ color: colors.text }}>
                  {insight.title}
                </h4>
                <p className="text-xs mt-1" style={{ color: colors.textSecondary }}>
                  {insight.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AnalyticsDashboard;