import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useTheme } from '../../theme/ThemeContext';
import { ServiceStatus } from '../../types/dashboard';
import {
  Play,
  Square,
  RotateCcw,
  FileText,
  Settings,
  AlertTriangle,
  CheckCircle,
  Clock,
  Zap,
  Server,
  Activity,
  MoreVertical
} from 'lucide-react';

interface ServiceCardProps {
  service: ServiceStatus;
  onAction: (action: 'start' | 'stop' | 'restart' | 'logs' | 'settings') => void;
}

const ServiceCard: React.FC<ServiceCardProps> = ({ service, onAction }) => {
  const { colors, spacing } = useTheme();
  const [showActions, setShowActions] = useState(false);
  const [expanded, setExpanded] = useState(false);

  const getStatusColor = (status: ServiceStatus['status']) => {
    switch (status) {
      case 'running': return colors.success;
      case 'stopped': return colors.textSecondary;
      case 'error': return colors.error;
      case 'starting': return colors.warning;
      case 'stopping': return colors.warning;
      default: return colors.textSecondary;
    }
  };

  const getStatusIcon = (status: ServiceStatus['status']) => {
    switch (status) {
      case 'running': return <CheckCircle size={16} />;
      case 'stopped': return <Square size={16} />;
      case 'error': return <AlertTriangle size={16} />;
      case 'starting': return <Clock size={16} />;
      case 'stopping': return <Clock size={16} />;
      default: return <Activity size={16} />;
    }
  };

  const getHealthColor = (healthScore: number) => {
    if (healthScore >= 80) return colors.success;
    if (healthScore >= 60) return colors.warning;
    return colors.error;
  };

  const handleAction = (action: 'start' | 'stop' | 'restart' | 'logs' | 'settings') => {
    onAction(action);
    setShowActions(false);
  };

  return (
    <motion.div
      whileHover={{ y: -2 }}
      className="p-4 rounded-lg border cursor-pointer"
      style={{
        backgroundColor: colors.surface,
        borderColor: colors.border,
      }}
      onClick={() => setExpanded(!expanded)}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-start space-x-3">
          {/* Service Icon */}
          <div className="flex items-center justify-center w-10 h-10 rounded-lg"
               style={{ backgroundColor: `${colors.primary}20` }}>
            <Server size={20} style={{ color: colors.primary }} />
          </div>

          {/* Service Info */}
          <div className="flex-1">
            <h3 className="font-semibold text-sm" style={{ color: colors.text }}>
              {service.name}
            </h3>
            <div className="flex items-center space-x-2 mt-1">
              <div className="flex items-center space-x-1">
                {getStatusIcon(service.status)}
                <span className="text-xs capitalize" style={{ color: getStatusColor(service.status) }}>
                  {service.status}
                </span>
              </div>
              {service.port && (
                <span className="text-xs" style={{ color: colors.textSecondary }}>
                  :{service.port}
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Actions Menu */}
        <div className="relative">
          <motion.button
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
            onClick={(e) => {
              e.stopPropagation();
              setShowActions(!showActions);
            }}
            className="p-1 rounded hover:bg-opacity-20 transition-colors"
            style={{ color: colors.textSecondary }}
          >
            <MoreVertical size={16} />
          </motion.button>

          <AnimatePresence>
            {showActions && (
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                className="absolute right-0 mt-1 w-48 rounded-lg shadow-lg border z-10"
                style={{
                  backgroundColor: colors.surface,
                  borderColor: colors.border,
                }}
              >
                {service.status === 'stopped' && (
                  <button
                    onClick={() => handleAction('start')}
                    className="w-full flex items-center space-x-2 px-3 py-2 text-left hover:bg-opacity-10 transition-colors"
                    style={{ color: colors.success }}
                  >
                    <Play size={14} />
                    <span className="text-sm">Start</span>
                  </button>
                )}
                {service.status === 'running' && (
                  <>
                    <button
                      onClick={() => handleAction('stop')}
                      className="w-full flex items-center space-x-2 px-3 py-2 text-left hover:bg-opacity-10 transition-colors"
                      style={{ color: colors.error }}
                    >
                      <Square size={14} />
                      <span className="text-sm">Stop</span>
                    </button>
                    <button
                      onClick={() => handleAction('restart')}
                      className="w-full flex items-center space-x-2 px-3 py-2 text-left hover:bg-opacity-10 transition-colors"
                      style={{ color: colors.warning }}
                    >
                      <RotateCcw size={14} />
                      <span className="text-sm">Restart</span>
                    </button>
                  </>
                )}
                <button
                  onClick={() => handleAction('logs')}
                  className="w-full flex items-center space-x-2 px-3 py-2 text-left hover:bg-opacity-10 transition-colors"
                  style={{ color: colors.textSecondary }}
                >
                  <FileText size={14} />
                  <span className="text-sm">View Logs</span>
                </button>
                <button
                  onClick={() => handleAction('settings')}
                  className="w-full flex items-center space-x-2 px-3 py-2 text-left hover:bg-opacity-10 transition-colors"
                  style={{ color: colors.textSecondary }}
                >
                  <Settings size={14} />
                  <span className="text-sm">Settings</span>
                </button>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* Description */}
      <p className="text-xs mb-3 line-clamp-2" style={{ color: colors.textSecondary }}>
        {service.description}
      </p>

      {/* Metrics */}
      <div className="grid grid-cols-3 gap-3 mb-3">
        <div className="text-center">
          <div className="flex items-center justify-center space-x-1 mb-1">
            <Zap size={12} style={{ color: colors.textSecondary }} />
            <span className="text-xs font-medium" style={{ color: colors.text }}>
              {service.cpu}%
            </span>
          </div>
          <span className="text-xs" style={{ color: colors.textSecondary }}>CPU</span>
        </div>
        <div className="text-center">
          <div className="text-xs font-medium mb-1" style={{ color: colors.text }}>
            {service.memory}MB
          </div>
          <span className="text-xs" style={{ color: colors.textSecondary }}>Memory</span>
        </div>
        <div className="text-center">
          <div className="flex items-center justify-center space-x-1 mb-1">
            <Activity size={12} style={{ color: getHealthColor(service.healthScore) }} />
            <span className="text-xs font-medium" style={{ color: getHealthColor(service.healthScore) }}>
              {service.healthScore}%
            </span>
          </div>
          <span className="text-xs" style={{ color: colors.textSecondary }}>Health</span>
        </div>
      </div>

      {/* Health Bar */}
      <div className="w-full h-2 rounded-full overflow-hidden mb-3"
           style={{ backgroundColor: colors.border }}>
        <motion.div
          className="h-full rounded-full"
          style={{ backgroundColor: getHealthColor(service.healthScore) }}
          initial={{ width: 0 }}
          animate={{ width: `${service.healthScore}%` }}
          transition={{ duration: 0.5 }}
        />
      </div>

      {/* Expanded Details */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="border-t pt-3"
            style={{ borderColor: colors.border }}
          >
            <div className="space-y-2">
              <div className="flex justify-between text-xs">
                <span style={{ color: colors.textSecondary }}>Category:</span>
                <span style={{ color: colors.text }} className="capitalize">
                  {service.category}
                </span>
              </div>
              {service.uptime && (
                <div className="flex justify-between text-xs">
                  <span style={{ color: colors.textSecondary }}>Uptime:</span>
                  <span style={{ color: colors.text }}>{service.uptime}</span>
                </div>
              )}
              <div className="flex justify-between text-xs">
                <span style={{ color: colors.textSecondary }}>Last Updated:</span>
                <span style={{ color: colors.text }}>
                  {service.lastUpdated.toLocaleTimeString()}
                </span>
              </div>
              <div className="flex justify-between text-xs">
                <span style={{ color: colors.textSecondary }}>Service ID:</span>
                <span style={{ color: colors.textSecondary }} className="font-mono">
                  {service.id}
                </span>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};

export default ServiceCard;