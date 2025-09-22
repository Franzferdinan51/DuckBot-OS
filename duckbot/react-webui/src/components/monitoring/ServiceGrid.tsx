import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useTheme } from '../../theme/ThemeContext';
import ServiceCard from './ServiceCard';
import { ServiceStatus } from '../../types/dashboard';
import { Activity, RefreshCw, Filter } from 'lucide-react';

interface ServiceGridProps {
  services?: ServiceStatus[];
  onServiceAction?: (serviceId: string, action: string) => void;
  autoRefresh?: boolean;
  refreshInterval?: number;
}

const ServiceGrid: React.FC<ServiceGridProps> = ({
  services: initialServices,
  onServiceAction,
  autoRefresh = true,
  refreshInterval = 5000,
}) => {
  const { colors } = useTheme();
  const [services, setServices] = useState<ServiceStatus[]>(initialServices || mockServices);
  const [loading, setLoading] = useState(false);
  const [filter, setFilter] = useState<'all' | 'running' | 'stopped' | 'error'>('all');
  const [categoryFilter, setCategoryFilter] = useState<string>('all');

  // Mock services data
  const mockServices: ServiceStatus[] = [
    {
      id: 'lm-studio',
      name: 'LM Studio Server',
      status: 'running',
      cpu: 12,
      memory: 2048,
      uptime: '2h 34m',
      lastUpdated: new Date(),
      category: 'core',
      description: 'Local AI model hosting server for Qwen and other models',
      port: 1234,
      healthScore: 95,
    },
    {
      id: 'ai-manager',
      name: 'AI Provider Manager',
      status: 'running',
      cpu: 8,
      memory: 512,
      uptime: '2h 34m',
      lastUpdated: new Date(),
      category: 'core',
      description: 'Unified integration across multiple AI providers',
      healthScore: 88,
    },
    {
      id: 'bytebot',
      name: 'Desktop Automation',
      status: 'running',
      cpu: 15,
      memory: 768,
      uptime: '1h 45m',
      lastUpdated: new Date(),
      category: 'integration',
      description: 'Natural language control for Windows applications',
      healthScore: 92,
    },
    {
      id: 'archon',
      name: 'Multi-Agent Framework',
      status: 'stopped',
      cpu: 0,
      memory: 0,
      lastUpdated: new Date(),
      category: 'integration',
      description: 'Coordination and knowledge sharing between AI agents',
      healthScore: 0,
    },
    {
      id: 'mcp-server',
      name: 'MCP Server',
      status: 'running',
      cpu: 5,
      memory: 256,
      uptime: '2h 30m',
      lastUpdated: new Date(),
      category: 'enhanced',
      description: 'Model Context Protocol server for AI integration',
      port: 8789,
      healthScore: 97,
    },
    {
      id: 'webui',
      name: 'Enhanced WebUI',
      status: 'running',
      cpu: 18,
      memory: 1024,
      uptime: '2h 34m',
      lastUpdated: new Date(),
      category: 'enhanced',
      description: 'Professional web dashboard for DuckBot management',
      port: 8787,
      healthScore: 85,
    },
  ];

  const filteredServices = services.filter(service => {
    const statusMatch = filter === 'all' || service.status === filter;
    const categoryMatch = categoryFilter === 'all' || service.category === categoryFilter;
    return statusMatch && categoryMatch;
  });

  const refreshServices = async () => {
    setLoading(true);
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));

      // In a real app, this would fetch from the backend
      const updatedServices = mockServices.map(service => ({
        ...service,
        cpu: Math.max(0, service.cpu + (Math.random() - 0.5) * 10),
        memory: Math.max(0, service.memory + Math.floor((Math.random() - 0.5) * 100)),
        healthScore: Math.min(100, Math.max(0, service.healthScore + (Math.random() - 0.5) * 10)),
        lastUpdated: new Date(),
      }));

      setServices(updatedServices);
    } catch (error) {
      console.error('Error refreshing services:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(refreshServices, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [autoRefresh, refreshInterval]);

  const categories = Array.from(new Set(services.map(s => s.category)));

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <Activity size={24} style={{ color: colors.primary }} />
          <div>
            <h2 className="text-xl font-bold" style={{ color: colors.text }}>
              Service Monitor
            </h2>
            <p className="text-sm" style={{ color: colors.textSecondary }}>
              {filteredServices.length} services active
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          {/* Category Filter */}
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="px-3 py-1 rounded-lg border text-sm"
            style={{
              backgroundColor: colors.background,
              borderColor: colors.border,
              color: colors.text,
            }}
          >
            <option value="all">All Categories</option>
            {categories.map(category => (
              <option key={category} value={category}>
                {category.charAt(0).toUpperCase() + category.slice(1)}
              </option>
            ))}
          </select>

          {/* Status Filter */}
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value as any)}
            className="px-3 py-1 rounded-lg border text-sm"
            style={{
              backgroundColor: colors.background,
              borderColor: colors.border,
              color: colors.text,
            }}
          >
            <option value="all">All Status</option>
            <option value="running">Running</option>
            <option value="stopped">Stopped</option>
            <option value="error">Error</option>
          </select>

          {/* Refresh Button */}
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={refreshServices}
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

      {/* Service Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <AnimatePresence>
          {filteredServices.map((service, index) => (
            <motion.div
              key={service.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ delay: index * 0.05 }}
            >
              <ServiceCard
                service={service}
                onAction={(action) => {
                  onServiceAction?.(service.id, action);
                  if (action === 'restart') {
                    // Simulate restart
                    setServices(prev => prev.map(s =>
                      s.id === service.id
                        ? { ...s, status: 'starting' as const }
                        : s
                    ));
                    setTimeout(() => {
                      setServices(prev => prev.map(s =>
                        s.id === service.id
                          ? { ...s, status: 'running' as const, uptime: '0m' }
                          : s
                      ));
                    }, 3000);
                  }
                }}
              />
            </motion.div>
          ))}
        </AnimatePresence>
      </div>

      {filteredServices.length === 0 && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-center py-12"
        >
          <Filter size={48} style={{ color: colors.textSecondary, opacity: 0.3 }} />
          <p className="mt-4 text-sm" style={{ color: colors.textSecondary }}>
            No services match the current filters
          </p>
        </motion.div>
      )}
    </div>
  );
};

export default ServiceGrid;