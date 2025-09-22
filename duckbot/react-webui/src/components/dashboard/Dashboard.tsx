import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useTheme } from '../../theme/ThemeContext';
import DashboardLayout from '../layout/DashboardLayout';
import ServiceGrid from '../monitoring/ServiceGrid';
import AgentManager from '../agents/AgentManager';
import SystemMonitor from '../monitoring/SystemMonitor';
import {
  Activity,
  Bot,
  Zap,
  DollarSign,
  Settings,
  Home,
  MessageSquare,
  BarChart3,
  Database,
  Monitor,
  TrendingUp,
  AlertCircle,
  CheckCircle
} from 'lucide-react';
import { DashboardLayout as DashboardLayoutType } from '../../types/dashboard';

interface DashboardProps {
  className?: string;
}

const Dashboard: React.FC<DashboardProps> = ({ className }) => {
  const { colors } = useTheme();
  const [activeView, setActiveView] = useState<string>('dashboard');
  const [layout, setLayout] = useState<DashboardLayoutType>({
    sidebar: { collapsed: false, width: 240 },
    panels: {
      monitoring: true,
      agents: true,
      automation: true,
      costs: true,
    },
    windows: {},
  });

  // Mock data and state
  const [alerts, setAlerts] = useState([
    {
      id: '1',
      type: 'warning' as const,
      title: 'High Memory Usage',
      message: 'System memory usage is at 85%',
      timestamp: new Date(Date.now() - 5 * 60 * 1000),
      source: 'System Monitor',
      isRead: false,
      severity: 'high' as const,
    },
    {
      id: '2',
      type: 'success' as const,
      title: 'Service Started',
      message: 'Desktop Automation service is running',
      timestamp: new Date(Date.now() - 15 * 60 * 1000),
      source: 'Service Manager',
      isRead: true,
      severity: 'medium' as const,
    },
  ]);

  const navigation = [
    { id: 'dashboard', label: 'Dashboard', icon: Home },
    { id: 'monitoring', label: 'System Monitor', icon: Monitor },
    { id: 'agents', label: 'AI Agents', icon: Bot },
    { id: 'automation', label: 'Automation', icon: Zap },
    { id: 'conversations', label: 'Conversations', icon: MessageSquare },
    { id: 'analytics', label: 'Analytics', icon: BarChart3 },
    { id: 'storage', label: 'Memory & Storage', icon: Database },
    { id: 'costs', label: 'Cost Tracking', icon: DollarSign },
  ];

  const renderContent = () => {
    switch (activeView) {
      case 'monitoring':
        return (
          <div className="col-span-full">
            <SystemMonitor showDetails={true} />
          </div>
        );
      case 'agents':
        return (
          <div className="col-span-full">
            <AgentManager />
          </div>
        );
      case 'dashboard':
      default:
        return (
          <>
            {/* Overview Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
              {[
                { label: 'Active Services', value: '5/6', icon: Activity, color: colors.success, change: '+1' },
                { label: 'AI Agents', value: '4', icon: Bot, color: colors.primary, change: '+1' },
                { label: 'System Health', value: '92%', icon: CheckCircle, color: colors.success, change: '+2%' },
                { label: 'Alerts', value: '2', icon: AlertCircle, color: colors.warning, change: '-1' },
              ].map((card, index) => (
                <motion.div
                  key={card.label}
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
                    <card.icon size={20} style={{ color: card.color }} />
                    <span className="text-xs font-medium px-2 py-1 rounded-full"
                          style={{
                            backgroundColor: card.change.startsWith('+') ? `${colors.success}20` : `${colors.error}20`,
                            color: card.change.startsWith('+') ? colors.success : colors.error,
                          }}>
                      {card.change}
                    </span>
                  </div>
                  <h3 className="text-lg font-bold" style={{ color: colors.text }}>
                    {card.value}
                  </h3>
                  <p className="text-sm" style={{ color: colors.textSecondary }}>
                    {card.label}
                  </p>
                </motion.div>
              ))}
            </div>

            {/* Main Content Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Services Section */}
              <ServiceGrid />

              {/* Quick Actions */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
                className="p-4 rounded-lg border"
                style={{
                  backgroundColor: colors.surface,
                  borderColor: colors.border,
                }}
              >
                <h3 className="text-lg font-semibold mb-4" style={{ color: colors.text }}>
                  Quick Actions
                </h3>
                <div className="grid grid-cols-2 gap-3">
                  {[
                    { label: 'Start Local Mode', icon: Zap, color: colors.primary },
                    { label: 'Run Diagnostics', icon: Activity, color: colors.success },
                    { label: 'View Logs', icon: Database, color: colors.warning },
                    { label: 'System Settings', icon: Settings, color: colors.textSecondary },
                  ].map((action, index) => (
                    <motion.button
                      key={action.label}
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      className="flex items-center space-x-2 p-3 rounded-lg border text-left"
                      style={{
                        backgroundColor: colors.background,
                        borderColor: colors.border,
                        color: colors.text,
                      }}
                    >
                      <action.icon size={18} style={{ color: action.color }} />
                      <span className="text-sm font-medium">{action.label}</span>
                    </motion.button>
                  ))}
                </div>
              </motion.div>

              {/* System Metrics */}
              <SystemMonitor showDetails={false} />

              {/* Recent Alerts */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.5 }}
                className="p-4 rounded-lg border"
                style={{
                  backgroundColor: colors.surface,
                  borderColor: colors.border,
                }}
              >
                <h3 className="text-lg font-semibold mb-4" style={{ color: colors.text }}>
                  Recent Alerts
                </h3>
                <div className="space-y-3">
                  {alerts.slice(0, 3).map((alert) => (
                    <div
                      key={alert.id}
                      className="p-3 rounded-lg border-l-4"
                      style={{
                        backgroundColor: colors.background,
                        borderColor: 'transparent',
                        borderLeftColor: alert.type === 'warning' ? colors.warning : colors.success,
                      }}
                    >
                      <div className="flex items-start justify-between">
                        <div>
                          <h4 className="font-medium text-sm" style={{ color: colors.text }}>
                            {alert.title}
                          </h4>
                          <p className="text-xs mt-1" style={{ color: colors.textSecondary }}>
                            {alert.message}
                          </p>
                          <p className="text-xs mt-1" style={{ color: colors.textSecondary }}>
                            {alert.source} • {alert.timestamp.toLocaleTimeString()}
                          </p>
                        </div>
                        {!alert.isRead && (
                          <span className="w-2 h-2 rounded-full"
                                style={{ backgroundColor: alert.type === 'warning' ? colors.warning : colors.success }} />
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </motion.div>
            </div>
          </>
        );
    }
  };

  return (
    <DashboardLayout
      layout={layout}
      onLayoutChange={setLayout}
      className={className}
    >
      {/* Page Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="flex items-center justify-center w-10 h-10 rounded-lg"
                 style={{ backgroundColor: `${colors.primary}20` }}>
              {navigation.find(item => item.id === activeView)?.icon({ size: 24, style: { color: colors.primary } }) || (
                <Home size={24} style={{ color: colors.primary }} />
              )}
            </div>
            <div>
              <h1 className="text-2xl font-bold" style={{ color: colors.text }}>
                {navigation.find(item => item.id === activeView)?.label || 'Dashboard'}
              </h1>
              <p className="text-sm" style={{ color: colors.textSecondary }}>
                {activeView === 'dashboard' && 'System overview and quick access to controls'}
                {activeView === 'monitoring' && 'Real-time system performance and health monitoring'}
                {activeView === 'agents' && 'Manage and monitor AI agents and their performance'}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 gap-6">
        {renderContent()}
      </div>
    </DashboardLayout>
  );
};

export default Dashboard;