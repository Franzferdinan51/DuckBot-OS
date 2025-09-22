import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useTheme } from '../../theme/ThemeContext';
import { AgentInstance } from '../../types/dashboard';
import {
  Bot,
  Brain,
  Zap,
  Settings,
  Play,
  Pause,
  RotateCcw,
  MessageSquare,
  BarChart3,
  Activity,
  MoreVertical,
  CheckCircle,
  Clock,
  AlertTriangle
} from 'lucide-react';

interface AgentCardProps {
  agent: AgentInstance;
  onInteract: (agentId: string) => void;
  onConfigure: (agentId: string) => void;
  onStart?: (agentId: string) => void;
  onStop?: (agentId: string) => void;
  onRestart?: (agentId: string) => void;
}

const AgentCard: React.FC<AgentCardProps> = ({
  agent,
  onInteract,
  onConfigure,
  onStart,
  onStop,
  onRestart,
}) => {
  const { colors, spacing } = useTheme();
  const [showActions, setShowActions] = useState(false);
  const [expanded, setExpanded] = useState(false);

  const getStatusColor = (status: AgentInstance['status']) => {
    switch (status) {
      case 'active': return colors.success;
      case 'processing': return colors.warning;
      case 'idle': return colors.textSecondary;
      case 'error': return colors.error;
      case 'offline': return colors.border;
      default: return colors.textSecondary;
    }
  };

  const getStatusIcon = (status: AgentInstance['status']) => {
    switch (status) {
      case 'active': return <Activity size={16} className="animate-pulse" />;
      case 'processing': return <Zap size={16} className="animate-pulse" />;
      case 'idle': return <Clock size={16} />;
      case 'error': return <AlertTriangle size={16} />;
      case 'offline': return <Pause size={16} />;
      default: return <Activity size={16} />;
    }
  };

  const getTypeIcon = (type: AgentInstance['type']) => {
    switch (type) {
      case 'ai': return <Brain size={16} />;
      case 'automation': return <Zap size={16} />;
      case 'monitoring': return <BarChart3 size={16} />;
      case 'specialist': return <Bot size={16} />;
      default: return <Bot size={16} />;
    }
  };

  const getTypeColor = (type: AgentInstance['type']) => {
    switch (type) {
      case 'ai': return colors.primary;
      case 'automation': return colors.warning;
      case 'monitoring': return colors.success;
      case 'specialist': return colors.secondary;
      default: return colors.textSecondary;
    }
  };

  const canStart = agent.status === 'idle' || agent.status === 'offline';
  const canStop = agent.status === 'active' || agent.status === 'processing';

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
          {/* Agent Icon */}
          <div className="flex items-center justify-center w-10 h-10 rounded-lg"
               style={{ backgroundColor: `${getTypeColor(agent.type)}20` }}>
            {getTypeIcon(agent.type)}
            <span className="sr-only">{agent.type}</span>
          </div>

          {/* Agent Info */}
          <div className="flex-1">
            <h3 className="font-semibold text-sm" style={{ color: colors.text }}>
              {agent.name}
            </h3>
            <div className="flex items-center space-x-2 mt-1">
              <div className="flex items-center space-x-1">
                {getStatusIcon(agent.status)}
                <span className="text-xs capitalize" style={{ color: getStatusColor(agent.status) }}>
                  {agent.status}
                </span>
              </div>
              <span className="text-xs" style={{ color: getTypeColor(agent.type) }}>
                • {agent.type}
              </span>
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
                {canStart && onStart && (
                  <button
                    onClick={() => handleAction('start')}
                    className="w-full flex items-center space-x-2 px-3 py-2 text-left hover:bg-opacity-10 transition-colors"
                    style={{ color: colors.success }}
                  >
                    <Play size={14} />
                    <span className="text-sm">Start</span>
                  </button>
                )}
                {canStop && onStop && (
                  <button
                    onClick={() => handleAction('stop')}
                    className="w-full flex items-center space-x-2 px-3 py-2 text-left hover:bg-opacity-10 transition-colors"
                    style={{ color: colors.error }}
                  >
                    <Pause size={14} />
                    <span className="text-sm">Stop</span>
                  </button>
                )}
                {onRestart && (
                  <button
                    onClick={() => handleAction('restart')}
                    className="w-full flex items-center space-x-2 px-3 py-2 text-left hover:bg-opacity-10 transition-colors"
                    style={{ color: colors.warning }}
                  >
                    <RotateCcw size={14} />
                    <span className="text-sm">Restart</span>
                  </button>
                )}
                <button
                  onClick={() => handleAction('interact')}
                  className="w-full flex items-center space-x-2 px-3 py-2 text-left hover:bg-opacity-10 transition-colors"
                  style={{ color: colors.primary }}
                >
                  <MessageSquare size={14} />
                  <span className="text-sm">Interact</span>
                </button>
                <button
                  onClick={() => handleAction('configure')}
                  className="w-full flex items-center space-x-2 px-3 py-2 text-left hover:bg-opacity-10 transition-colors"
                  style={{ color: colors.textSecondary }}
                >
                  <Settings size={14} />
                  <span className="text-sm">Configure</span>
                </button>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* Current Task */}
      {agent.currentTask && (
        <div className="mb-3 p-2 rounded text-xs"
             style={{ backgroundColor: `${colors.primary}10`, color: colors.primary }}>
          <div className="flex items-center space-x-2">
            <Zap size={12} />
            <span className="truncate">{agent.currentTask}</span>
          </div>
        </div>
      )}

      {/* Capabilities */}
      <div className="mb-3">
        <div className="flex flex-wrap gap-1">
          {agent.capabilities.slice(0, 3).map((capability, index) => (
            <span
              key={index}
              className="px-2 py-1 rounded text-xs"
              style={{
                backgroundColor: colors.background,
                color: colors.textSecondary,
                border: `1px solid ${colors.border}`,
              }}
            >
              {capability}
            </span>
          ))}
          {agent.capabilities.length > 3 && (
            <span className="px-2 py-1 rounded text-xs"
                  style={{
                    backgroundColor: colors.background,
                    color: colors.textSecondary,
                    border: `1px solid ${colors.border}`,
                  }}>
              +{agent.capabilities.length - 3} more
            </span>
          )}
        </div>
      </div>

      {/* Performance Metrics */}
      <div className="grid grid-cols-3 gap-3 mb-3">
        <div className="text-center">
          <div className="text-xs font-medium mb-1" style={{ color: colors.text }}>
            {agent.performance.tasksCompleted}
          </div>
          <span className="text-xs" style={{ color: colors.textSecondary }}>Tasks</span>
        </div>
        <div className="text-center">
          <div className="flex items-center justify-center space-x-1 mb-1">
            <CheckCircle size={10} style={{ color: colors.success }} />
            <span className="text-xs font-medium" style={{ color: colors.text }}>
              {agent.performance.successRate}%
            </span>
          </div>
          <span className="text-xs" style={{ color: colors.textSecondary }}>Success</span>
        </div>
        <div className="text-center">
          <div className="text-xs font-medium mb-1" style={{ color: colors.text }}>
            {agent.performance.averageResponseTime}ms
          </div>
          <span className="text-xs" style={{ color: colors.textSecondary }}>Avg Time</span>
        </div>
      </div>

      {/* Resource Usage */}
      <div className="space-y-2 mb-3">
        <div className="flex justify-between text-xs">
          <span style={{ color: colors.textSecondary }}>CPU: {agent.resources.cpu}%</span>
          <span style={{ color: colors.textSecondary }}>Memory: {agent.resources.memory}MB</span>
        </div>
        <div className="flex space-x-2">
          <div className="flex-1 h-1 rounded-full overflow-hidden bg-opacity-20"
               style={{ backgroundColor: colors.border }}>
            <div
              className="h-full rounded-full"
              style={{
                width: `${agent.resources.cpu}%`,
                backgroundColor: agent.resources.cpu > 80 ? colors.error : colors.warning,
              }}
            />
          </div>
          <div className="flex-1 h-1 rounded-full overflow-hidden bg-opacity-20"
               style={{ backgroundColor: colors.border }}>
            <div
              className="h-full rounded-full"
              style={{
                width: `${(agent.resources.memory / 1024) * 100}%`,
                backgroundColor: agent.resources.memory > 512 ? colors.error : colors.primary,
              }}
            />
          </div>
        </div>
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
              <div>
                <h4 className="text-xs font-semibold mb-1" style={{ color: colors.textSecondary }}>
                  All Capabilities:
                </h4>
                <div className="flex flex-wrap gap-1">
                  {agent.capabilities.map((capability, index) => (
                    <span
                      key={index}
                      className="px-2 py-1 rounded text-xs"
                      style={{
                        backgroundColor: colors.background,
                        color: colors.textSecondary,
                        border: `1px solid ${colors.border}`,
                      }}
                    >
                      {capability}
                    </span>
                  ))}
                </div>
              </div>
              <div className="flex justify-between text-xs">
                <span style={{ color: colors.textSecondary }}>Last Activity:</span>
                <span style={{ color: colors.text }}>
                  {agent.lastActivity.toLocaleString()}
                </span>
              </div>
              <div className="flex justify-between text-xs">
                <span style={{ color: colors.textSecondary }}>Agent ID:</span>
                <span style={{ color: colors.textSecondary }} className="font-mono">
                  {agent.id}
                </span>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};

const handleAction = (action: string) => {
  console.log(`Action: ${action}`);
};

export default AgentCard;