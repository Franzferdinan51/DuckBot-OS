import React from 'react';
import { motion } from 'framer-motion';
import { useTheme } from '../../theme/ThemeContext';
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
  Monitor
} from 'lucide-react';

interface SidebarProps {
  panels: Record<string, boolean>;
  onTogglePanel: (panel: string) => void;
  width: number;
}

const Sidebar: React.FC<SidebarProps> = ({ panels, onTogglePanel, width }) => {
  const { colors, spacing } = useTheme();

  const navigationItems = [
    { id: 'dashboard', label: 'Dashboard', icon: Home, active: true },
    { id: 'monitoring', label: 'System Monitor', icon: Monitor },
    { id: 'agents', label: 'AI Agents', icon: Bot },
    { id: 'automation', label: 'Automation', icon: Zap },
    { id: 'conversations', label: 'Conversations', icon: MessageSquare },
    { id: 'analytics', label: 'Analytics', icon: BarChart3 },
    { id: 'storage', label: 'Memory & Storage', icon: Database },
    { id: 'costs', label: 'Cost Tracking', icon: DollarSign },
  ];

  const togglePanel = (panelId: string) => {
    onTogglePanel(panelId);
  };

  return (
    <div className="flex flex-col h-full" style={{ width }}>
      {/* Logo/Branding */}
      <div className="p-6 border-b" style={{ borderColor: colors.border }}>
        <div className="flex items-center space-x-3">
          <div className="flex items-center justify-center w-10 h-10 rounded-lg"
               style={{ backgroundColor: colors.primary }}>
            <Activity size={24} style={{ color: colors.background }} />
          </div>
          <div>
            <h1 className="font-bold text-lg" style={{ color: colors.text }}>
              DuckBot
            </h1>
            <p className="text-xs" style={{ color: colors.textSecondary }}>
              Enhanced v4.2
            </p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto py-4">
        <div className="px-3 mb-6">
          <p className="text-xs font-semibold uppercase tracking-wider mb-3"
             style={{ color: colors.textSecondary }}>
            Navigation
          </p>
          <div className="space-y-1">
            {navigationItems.map((item) => (
              <motion.button
                key={item.id}
                whileHover={{ x: 4 }}
                whileTap={{ scale: 0.98 }}
                className={`w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-left transition-colors ${
                  item.active ? 'bg-opacity-20' : 'hover:bg-opacity-10'
                }`}
                style={{
                  backgroundColor: item.active ? `${colors.primary}20` : 'transparent',
                  color: item.active ? colors.primary : colors.textSecondary,
                }}
                onClick={() => togglePanel(item.id)}
              >
                <item.icon size={18} />
                <span className="font-medium">{item.label}</span>
              </motion.button>
            ))}
          </div>
        </div>

        {/* Panel Toggles */}
        <div className="px-3 mb-6">
          <p className="text-xs font-semibold uppercase tracking-wider mb-3"
             style={{ color: colors.textSecondary }}>
            Dashboard Panels
          </p>
          <div className="space-y-2">
            {Object.entries(panels).map(([panelId, isVisible]) => (
              <motion.label
                key={panelId}
                className="flex items-center justify-between px-3 py-2 rounded-lg cursor-pointer hover:bg-opacity-10"
                style={{ backgroundColor: 'transparent' }}
                whileHover={{ backgroundColor: `${colors.border}20` }}
              >
                <span className="text-sm" style={{ color: colors.textSecondary }}>
                  {panelId.charAt(0).toUpperCase() + panelId.slice(1)}
                </span>
                <div className="relative">
                  <input
                    type="checkbox"
                    checked={isVisible}
                    onChange={() => togglePanel(panelId)}
                    className="sr-only"
                  />
                  <div className={`w-10 h-6 rounded-full transition-colors ${
                    isVisible ? 'bg-opacity-100' : 'bg-opacity-30'
                  }`}
                       style={{ backgroundColor: isVisible ? colors.primary : colors.border }}>
                    <motion.div
                      className="absolute top-1 w-4 h-4 bg-white rounded-full shadow-md"
                      animate={{ left: isVisible ? 32 : 8 }}
                      transition={{ type: 'spring', stiffness: 500, damping: 30 }}
                    />
                  </div>
                </div>
              </motion.label>
            ))}
          </div>
        </div>

        {/* Quick Actions */}
        <div className="px-3">
          <p className="text-xs font-semibold uppercase tracking-wider mb-3"
             style={{ color: colors.textSecondary }}>
            Quick Actions
          </p>
          <div className="space-y-1">
            <motion.button
              whileHover={{ x: 4 }}
              whileTap={{ scale: 0.98 }}
              className="w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-left"
              style={{ color: colors.textSecondary }}
            >
              <Activity size={18} />
              <span className="text-sm">System Diagnostics</span>
            </motion.button>
            <motion.button
              whileHover={{ x: 4 }}
              whileTap={{ scale: 0.98 }}
              className="w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-left"
              style={{ color: colors.textSecondary }}
            >
              <BarChart3 size={18} />
              <span className="text-sm">Performance Report</span>
            </motion.button>
          </div>
        </div>
      </nav>

      {/* Settings */}
      <div className="p-4 border-t" style={{ borderColor: colors.border }}>
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          className="w-full flex items-center space-x-3 px-3 py-2 rounded-lg"
          style={{
            backgroundColor: `${colors.surfaceLight}`,
            color: colors.textSecondary
          }}
        >
          <Settings size={18} />
          <span className="text-sm font-medium">Settings</span>
        </motion.button>
      </div>
    </div>
  );
};

export default Sidebar;