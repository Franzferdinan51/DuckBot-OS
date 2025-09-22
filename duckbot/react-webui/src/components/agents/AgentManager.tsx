import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useTheme } from '../../theme/ThemeContext';
import AgentCard from './AgentCard';
import { AgentInstance } from '../../types/dashboard';
import {
  Bot,
  Plus,
  Search,
  Filter,
  Activity,
  RefreshCw,
  Grid,
  List,
  Brain,
  Zap,
  BarChart3,
  Cpu
} from 'lucide-react';

interface AgentManagerProps {
  agents?: AgentInstance[];
  onAgentAction?: (agentId: string, action: string) => void;
  autoRefresh?: boolean;
  refreshInterval?: number;
}

const AgentManager: React.FC<AgentManagerProps> = ({
  agents: initialAgents,
  onAgentAction,
  autoRefresh = true,
  refreshInterval = 3000,
}) => {
  const { colors } = useTheme();
  const [agents, setAgents] = useState<AgentInstance[]>(initialAgents || mockAgents);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');

  // Mock agents data
  const mockAgents: AgentInstance[] = [
    {
      id: 'qwen-30b',
      name: 'Qwen 3 Coder 30B',
      type: 'ai',
      status: 'active',
      capabilities: [
        'Code Generation',
        'Architecture Design',
        'Debugging',
        'Documentation',
        'Performance Optimization'
      ],
      currentTask: 'Analyzing system architecture',
      performance: {
        tasksCompleted: 1247,
        successRate: 96.5,
        averageResponseTime: 450,
      },
      lastActivity: new Date(),
      resources: {
        cpu: 35,
        memory: 8192,
      },
    },
    {
      id: 'bytebot-automation',
      name: 'ByteBot Automation',
      type: 'automation',
      status: 'active',
      capabilities: [
        'UI Automation',
        'File Operations',
        'Application Control',
        'Process Management',
        'System Commands'
      ],
      currentTask: 'Processing desktop automation queue',
      performance: {
        tasksCompleted: 892,
        successRate: 98.2,
        averageResponseTime: 120,
      },
      lastActivity: new Date(),
      resources: {
        cpu: 15,
        memory: 512,
      },
    },
    {
      id: 'system-monitor',
      name: 'System Monitor',
      type: 'monitoring',
      status: 'active',
      capabilities: [
        'Resource Monitoring',
        'Performance Analysis',
        'Alert Management',
        'Health Checks',
        'Metrics Collection'
      ],
      currentTask: 'Monitoring system health',
      performance: {
        tasksCompleted: 3456,
        successRate: 99.8,
        averageResponseTime: 25,
      },
      lastActivity: new Date(),
      resources: {
        cpu: 8,
        memory: 256,
      },
    },
    {
      id: 'cost-optimizer',
      name: 'Cost Optimizer',
      type: 'specialist',
      status: 'idle',
      capabilities: [
        'Cost Analysis',
        'Budget Management',
        'Usage Optimization',
        'Provider Comparison',
        'Recommendation Engine'
      ],
      performance: {
        tasksCompleted: 156,
        successRate: 94.3,
        averageResponseTime: 320,
      },
      lastActivity: new Date(Date.now() - 5 * 60 * 1000),
      resources: {
        cpu: 0,
        memory: 128,
      },
    },
    {
      id: 'archon-coordinator',
      name: 'Archon Coordinator',
      type: 'ai',
      status: 'processing',
      capabilities: [
        'Agent Coordination',
        'Task Distribution',
        'Resource Allocation',
        'Knowledge Sharing',
        'Conflict Resolution'
      ],
      currentTask: 'Coordinating multi-agent task execution',
      performance: {
        tasksCompleted: 423,
        successRate: 92.1,
        averageResponseTime: 180,
      },
      lastActivity: new Date(),
      resources: {
        cpu: 25,
        memory: 1024,
      },
    },
    {
      id: 'conversation-analyst',
      name: 'Conversation Analyst',
      type: 'ai',
      status: 'offline',
      capabilities: [
        'Conversation Analysis',
        'Pattern Recognition',
        'Intent Detection',
        'Context Management',
        'Memory Optimization'
      ],
      performance: {
        tasksCompleted: 2156,
        successRate: 95.8,
        averageResponseTime: 280,
      },
      lastActivity: new Date(Date.now() - 30 * 60 * 1000),
      resources: {
        cpu: 0,
        memory: 0,
      },
    },
  ];

  const filteredAgents = agents.filter(agent => {
    const matchesSearch = agent.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         agent.capabilities.some(cap =>
                           cap.toLowerCase().includes(searchTerm.toLowerCase())
                         );
    const matchesType = typeFilter === 'all' || agent.type === typeFilter;
    const matchesStatus = statusFilter === 'all' || agent.status === statusFilter;

    return matchesSearch && matchesType && matchesStatus;
  });

  const refreshAgents = async () => {
    setLoading(true);
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 800));

      // Update agent statuses and metrics
      const updatedAgents = mockAgents.map(agent => ({
        ...agent,
        performance: {
          ...agent.performance,
          tasksCompleted: agent.performance.tasksCompleted + Math.floor(Math.random() * 5),
          successRate: Math.min(100, Math.max(0, agent.performance.successRate + (Math.random() - 0.5) * 2)),
        },
        resources: agent.status !== 'offline' ? {
          cpu: Math.max(0, agent.resources.cpu + (Math.random() - 0.5) * 10),
          memory: Math.max(0, agent.resources.memory + Math.floor((Math.random() - 0.5) * 200)),
        } : agent.resources,
        lastActivity: agent.status !== 'offline' ? new Date() : agent.lastActivity,
      }));

      setAgents(updatedAgents);
    } catch (error) {
      console.error('Error refreshing agents:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(refreshAgents, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [autoRefresh, refreshInterval]);

  const agentTypes = Array.from(new Set(agents.map(a => a.type)));
  const agentStatuses = Array.from(new Set(agents.map(a => a.status)));

  const stats = {
    total: agents.length,
    active: agents.filter(a => a.status === 'active').length,
    processing: agents.filter(a => a.status === 'processing').length,
    totalTasks: agents.reduce((sum, a) => sum + a.performance.tasksCompleted, 0),
    avgSuccessRate: agents.reduce((sum, a) => sum + a.performance.successRate, 0) / agents.length,
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <Brain size={24} style={{ color: colors.primary }} />
          <div>
            <h2 className="text-xl font-bold" style={{ color: colors.text }}>
              AI Agent Manager
            </h2>
            <p className="text-sm" style={{ color: colors.textSecondary }}>
              {stats.active} active, {stats.processing} processing agents
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          {/* View Mode Toggle */}
          <div className="flex items-center space-x-1 p-1 rounded-lg border"
               style={{ borderColor: colors.border }}>
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => setViewMode('grid')}
              className={`p-1 rounded ${
                viewMode === 'grid' ? 'bg-opacity-20' : ''
              }`}
              style={{
                backgroundColor: viewMode === 'grid' ? `${colors.primary}20` : 'transparent',
                color: viewMode === 'grid' ? colors.primary : colors.textSecondary,
              }}
            >
              <Grid size={16} />
            </motion.button>
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => setViewMode('list')}
              className={`p-1 rounded ${
                viewMode === 'list' ? 'bg-opacity-20' : ''
              }`}
              style={{
                backgroundColor: viewMode === 'list' ? `${colors.primary}20` : 'transparent',
                color: viewMode === 'list' ? colors.primary : colors.textSecondary,
              }}
            >
              <List size={16} />
            </motion.button>
          </div>

          {/* Add Agent Button */}
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="flex items-center space-x-2 px-3 py-2 rounded-lg"
            style={{
              backgroundColor: colors.primary,
              color: colors.background,
            }}
          >
            <Plus size={16} />
            <span className="text-sm font-medium">Add Agent</span>
          </motion.button>

          {/* Refresh Button */}
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={refreshAgents}
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

      {/* Statistics */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        {[
          { label: 'Total Agents', value: stats.total, icon: Bot, color: colors.primary },
          { label: 'Active', value: stats.active, icon: Activity, color: colors.success },
          { label: 'Processing', value: stats.processing, icon: Cpu, color: colors.warning },
          { label: 'Tasks Completed', value: stats.totalTasks.toLocaleString(), icon: Zap, color: colors.secondary },
          { label: 'Avg Success', value: `${stats.avgSuccessRate.toFixed(1)}%`, icon: BarChart3, color: colors.info },
        ].map((stat, index) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className="p-3 rounded-lg border"
            style={{
              backgroundColor: colors.surface,
              borderColor: colors.border,
            }}
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs" style={{ color: colors.textSecondary }}>
                  {stat.label}
                </p>
                <p className="text-lg font-bold" style={{ color: colors.text }}>
                  {stat.value}
                </p>
              </div>
              <stat.icon size={20} style={{ color: stat.color }} />
            </div>
          </motion.div>
        ))}
      </div>

      {/* Filters */}
      <div className="flex items-center space-x-4">
        {/* Search */}
        <div className="relative flex-1 max-w-md">
          <Search
            size={16}
            className="absolute left-3 top-1/2 transform -translate-y-1/2"
            style={{ color: colors.textSecondary }}
          />
          <input
            type="text"
            placeholder="Search agents and capabilities..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-3 py-2 rounded-lg border focus:outline-none focus:ring-2"
            style={{
              backgroundColor: colors.background,
              borderColor: colors.border,
              color: colors.text,
              focusRingColor: colors.primary,
            }}
          />
        </div>

        {/* Type Filter */}
        <select
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
          className="px-3 py-2 rounded-lg border text-sm"
          style={{
            backgroundColor: colors.background,
            borderColor: colors.border,
            color: colors.text,
          }}
        >
          <option value="all">All Types</option>
          {agentTypes.map(type => (
            <option key={type} value={type}>
              {type.charAt(0).toUpperCase() + type.slice(1)}
            </option>
          ))}
        </select>

        {/* Status Filter */}
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="px-3 py-2 rounded-lg border text-sm"
          style={{
            backgroundColor: colors.background,
            borderColor: colors.border,
            color: colors.text,
          }}
        >
          <option value="all">All Status</option>
          {agentStatuses.map(status => (
            <option key={status} value={status}>
              {status.charAt(0).toUpperCase() + status.slice(1)}
            </option>
          ))}
        </select>
      </div>

      {/* Agent Grid/List */}
      <div className={viewMode === 'grid'
        ? "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
        : "space-y-4"
      }>
        {filteredAgents.map((agent, index) => (
          <motion.div
            key={agent.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.05 }}
          >
            <AgentCard
              agent={agent}
              onInteract={(agentId) => {
                onAgentAction?.(agentId, 'interact');
                console.log(`Interacting with agent: ${agentId}`);
              }}
              onConfigure={(agentId) => {
                onAgentAction?.(agentId, 'configure');
                console.log(`Configuring agent: ${agentId}`);
              }}
              onStart={(agentId) => {
                onAgentAction?.(agentId, 'start');
                console.log(`Starting agent: ${agentId}`);
              }}
              onStop={(agentId) => {
                onAgentAction?.(agentId, 'stop');
                console.log(`Stopping agent: ${agentId}`);
              }}
              onRestart={(agentId) => {
                onAgentAction?.(agentId, 'restart');
                console.log(`Restarting agent: ${agentId}`);
              }}
            />
          </motion.div>
        ))}
      </div>

      {filteredAgents.length === 0 && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-center py-12"
        >
          <Filter size={48} style={{ color: colors.textSecondary, opacity: 0.3 }} />
          <p className="mt-4 text-sm" style={{ color: colors.textSecondary }}>
            No agents match the current filters
          </p>
        </motion.div>
      )}
    </div>
  );
};

export default AgentManager;