import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { cn, formatUptime, formatBytes, getStatusColor } from '@/lib/utils';
import {
  Play,
  Square,
  RotateCcw,
  Settings,
  FileText,
  AlertTriangle,
  CheckCircle,
  Clock,
  Activity,
  Cpu,
  MemoryStick,
  HardDrive,
  Wifi,
  Search,
  Filter,
  MoreHorizontal,
  Terminal,
  Zap
} from 'lucide-react';
import { ServiceStatus } from '@/types';

interface ServiceGridProps {
  services: ServiceStatus[];
  onServiceAction: (serviceName: string, action: 'start' | 'stop' | 'restart' | 'logs') => Promise<void>;
}

interface ServiceCardProps {
  service: ServiceStatus;
  onAction: (action: 'start' | 'stop' | 'restart' | 'logs') => Promise<void>;
}

export function ServiceGrid({ services, onServiceAction }: ServiceGridProps) {
  const [filteredServices, setFilteredServices] = useState<ServiceStatus[]>(services);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [categoryFilter, setCategoryFilter] = useState<string>('all');
  const [selectedService, setSelectedService] = useState<ServiceStatus | null>(null);
  const [serviceLogs, setServiceLogs] = useState<string[]>([]);

  useEffect(() => {
    let filtered = services;

    // Search filter
    if (searchTerm) {
      filtered = filtered.filter(service =>
        service.name.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Status filter
    if (statusFilter !== 'all') {
      filtered = filtered.filter(service => service.status === statusFilter);
    }

    // Category filter
    if (categoryFilter !== 'all') {
      filtered = filtered.filter(service => {
        if (categoryFilter === 'core') {
          return ['lm_studio', 'webui', 'monitoring', 'ai_router'].includes(service.name);
        } else if (categoryFilter === 'integration') {
          return ['bytebot', 'archon', 'mcp_server', 'vibevoice'].includes(service.name);
        } else if (categoryFilter === 'enhanced') {
          return ['enhanced_webui', 'monitoring_dashboard', 'intelligent_agents'].includes(service.name);
        }
        return true;
      });
    }

    setFilteredServices(filtered);
  }, [services, searchTerm, statusFilter, categoryFilter]);

  const handleServiceAction = async (serviceName: string, action: 'start' | 'stop' | 'restart' | 'logs') => {
    try {
      await onServiceAction(serviceName, action);

      if (action === 'logs') {
        // Fetch logs for the service
        const logs = await window.electronAPI.getServiceLogs(serviceName);
        setServiceLogs(logs);
        const service = services.find(s => s.name === serviceName);
        if (service) setSelectedService(service);
      }
    } catch (error) {
      console.error(`Failed to ${action} service ${serviceName}:`, error);
    }
  };

  const getStatusStats = () => {
    const running = services.filter(s => s.status === 'running').length;
    const stopped = services.filter(s => s.status === 'stopped').length;
    const error = services.filter(s => s.status === 'error').length;
    const total = services.length;

    return { running, stopped, error, total };
  };

  const stats = getStatusStats();

  return (
    <div className="space-y-6">
      {/* Header and controls */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-foreground">Services</h2>
          <p className="text-muted-foreground">Manage and monitor DuckBot ecosystem services</p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              services.forEach(service => {
                if (service.status !== 'running') {
                  handleServiceAction(service.name, 'start');
                }
              });
            }}
          >
            <Play className="w-4 h-4 mr-2" />
            Start All
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              services.forEach(service => {
                if (service.status === 'running') {
                  handleServiceAction(service.name, 'stop');
                }
              });
            }}
          >
            <Square className="w-4 h-4 mr-2" />
            Stop All
          </Button>
        </div>
      </div>

      {/* Stats cards */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Total Services</p>
                <p className="text-2xl font-bold">{stats.total}</p>
              </div>
              <Activity className="w-8 h-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Running</p>
                <p className="text-2xl font-bold text-green-600">{stats.running}</p>
              </div>
              <CheckCircle className="w-8 h-8 text-green-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Stopped</p>
                <p className="text-2xl font-bold text-gray-600">{stats.stopped}</p>
              </div>
              <Square className="w-8 h-8 text-gray-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Errors</p>
                <p className="text-2xl font-bold text-red-600">{stats.error}</p>
              </div>
              <AlertTriangle className="w-8 h-8 text-red-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <Input
                  placeholder="Search services..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-full sm:w-[180px]">
                <SelectValue placeholder="Filter by status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="running">Running</SelectItem>
                <SelectItem value="stopped">Stopped</SelectItem>
                <SelectItem value="error">Error</SelectItem>
                <SelectItem value="starting">Starting</SelectItem>
                <SelectItem value="stopping">Stopping</SelectItem>
              </SelectContent>
            </Select>
            <Select value={categoryFilter} onValueChange={setCategoryFilter}>
              <SelectTrigger className="w-full sm:w-[180px]">
                <SelectValue placeholder="Filter by category" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Categories</SelectItem>
                <SelectItem value="core">Core Services</SelectItem>
                <SelectItem value="integration">Integration</SelectItem>
                <SelectItem value="enhanced">Enhanced</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Service grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredServices.map((service) => (
          <ServiceCard
            key={service.name}
            service={service}
            onAction={(action) => handleServiceAction(service.name, action)}
          />
        ))}
      </div>

      {filteredServices.length === 0 && (
        <Card>
          <CardContent className="p-8 text-center">
            <Activity className="w-12 h-12 mx-auto mb-4 text-muted-foreground opacity-50" />
            <h3 className="text-lg font-semibold mb-2">No services found</h3>
            <p className="text-muted-foreground mb-4">
              Try adjusting your search or filter criteria
            </p>
            <Button onClick={() => {
              setSearchTerm('');
              setStatusFilter('all');
              setCategoryFilter('all');
            }}>
              Clear Filters
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Service logs dialog */}
      <Dialog open={!!selectedService} onOpenChange={() => setSelectedService(null)}>
        <DialogContent className="max-w-4xl max-h-[80vh]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <FileText className="w-5 h-5" />
              {selectedService?.name} - Logs
            </DialogTitle>
            <DialogDescription>
              Service logs and diagnostic information
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            {/* Service info */}
            {selectedService && (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 p-4 bg-muted rounded-lg">
                <div>
                  <p className="text-sm text-muted-foreground">Status</p>
                  <Badge className={getStatusColor(selectedService.status)}>
                    {selectedService.status}
                  </Badge>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">PID</p>
                  <p className="text-sm font-medium">{selectedService.pid || 'N/A'}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Port</p>
                  <p className="text-sm font-medium">{selectedService.port || 'N/A'}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Uptime</p>
                  <p className="text-sm font-medium">
                    {selectedService.uptime ? formatUptime(selectedService.uptime) : 'N/A'}
                  </p>
                </div>
              </div>
            )}

            {/* Logs */}
            <div className="bg-black text-green-400 p-4 rounded-lg font-mono text-sm h-96 overflow-y-auto">
              {serviceLogs.length > 0 ? (
                serviceLogs.map((log, index) => (
                  <div key={index} className="mb-1">
                    <span className="text-gray-500">
                      [{new Date().toLocaleTimeString()}]
                    </span>{' '}
                    {log}
                  </div>
                ))
              ) : (
                <div className="text-gray-500 text-center mt-8">
                  No logs available
                </div>
              )}
            </div>

            {/* Actions */}
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setSelectedService(null)}>
                Close
              </Button>
              <Button onClick={() => selectedService && handleServiceAction(selectedService.name, 'restart')}>
                <RotateCcw className="w-4 h-4 mr-2" />
                Restart Service
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}

function ServiceCard({ service, onAction }: ServiceCardProps) {
  const [isLoading, setIsLoading] = useState(false);

  const handleAction = async (action: 'start' | 'stop' | 'restart' | 'logs') => {
    setIsLoading(true);
    try {
      await onAction(action);
    } finally {
      setIsLoading(false);
    }
  };

  const getServiceIcon = (serviceName: string) => {
    const iconMap: Record<string, React.ComponentType<{ className?: string }>> = {
      lm_studio: Cpu,
      webui: Activity,
      monitoring: BarChart3,
      ai_router: Zap,
      bytebot: Terminal,
      archon: Bot,
      mcp_server: Server,
      vibevoice: Volume2,
      enhanced_webui: Monitor,
      monitoring_dashboard: BarChart3,
      intelligent_agents: Users,
      browser_use: Globe,
      automation: Zap,
      cost_tracker: DollarSign,
      memory_system: Database,
      hardware_detector: Cpu
    };
    return iconMap[serviceName] || Activity;
  };

  const Icon = getServiceIcon(service.name);

  return (
    <Card className="transition-all hover:shadow-lg">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className={cn(
              'p-2 rounded-lg',
              service.status === 'running' ? 'bg-green-100 text-green-600 dark:bg-green-900/20' :
              service.status === 'error' ? 'bg-red-100 text-red-600 dark:bg-red-900/20' :
              'bg-gray-100 text-gray-600 dark:bg-gray-900/20'
            )}>
              <Icon className="w-5 h-5" />
            </div>
            <div>
              <CardTitle className="text-lg capitalize">
                {service.name.replace('_', ' ')}
              </CardTitle>
              <CardDescription className="text-sm">
                {service.description || `${service.name.replace('_', ' ')} service`}
              </CardDescription>
            </div>
          </div>
          <Badge className={getStatusColor(service.status)}>
            {service.status}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="pt-0">
        <div className="space-y-4">
          {/* Service metrics */}
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-muted-foreground">CPU:</span>
              <span className="ml-1 font-medium">
                {service.cpu ? `${service.cpu.toFixed(1)}%` : 'N/A'}
              </span>
            </div>
            <div>
              <span className="text-muted-foreground">Memory:</span>
              <span className="ml-1 font-medium">
                {service.memory ? formatBytes(service.memory) : 'N/A'}
              </span>
            </div>
            {service.port && (
              <div>
                <span className="text-muted-foreground">Port:</span>
                <span className="ml-1 font-medium">{service.port}</span>
              </div>
            )}
            {service.uptime && (
              <div>
                <span className="text-muted-foreground">Uptime:</span>
                <span className="ml-1 font-medium">
                  {formatUptime(service.uptime)}
                </span>
              </div>
            )}
          </div>

          {/* Service controls */}
          <div className="flex gap-2">
            {service.status === 'running' ? (
              <>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => handleAction('restart')}
                  disabled={isLoading}
                  className="flex-1"
                >
                  <RotateCcw className="w-4 h-4 mr-1" />
                  Restart
                </Button>
                <Button
                  size="sm"
                  variant="destructive"
                  onClick={() => handleAction('stop')}
                  disabled={isLoading}
                  className="flex-1"
                >
                  <Square className="w-4 h-4 mr-1" />
                  Stop
                </Button>
              </>
            ) : (
              <Button
                size="sm"
                onClick={() => handleAction('start')}
                disabled={isLoading}
                className="flex-1"
              >
                <Play className="w-4 h-4 mr-1" />
                Start
              </Button>
            )}
            <Button
              size="sm"
              variant="outline"
              onClick={() => handleAction('logs')}
              disabled={isLoading}
            >
              <FileText className="w-4 h-4" />
            </Button>
          </div>

          {/* Error indicator */}
          {service.status === 'error' && service.lastError && (
            <div className="flex items-center gap-2 p-2 bg-red-50 dark:bg-red-900/20 rounded border border-red-200 dark:border-red-800">
              <AlertTriangle className="w-4 h-4 text-red-500" />
              <span className="text-sm text-red-600 dark:text-red-400 truncate">
                {service.lastError}
              </span>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

// Helper components
const BarChart3 = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
  </svg>
);

const Server = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01" />
  </svg>
);

const Volume2 = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
  </svg>
);

const Monitor = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
  </svg>
);

const Users = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
  </svg>
);

const Globe = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

const Database = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 4s8-1.79 8-4M4 7c0-2.21 3.582-4 4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s8-1.79 8-4m0 5c0 2.21-3.582 4-8 4s8-1.79 8-4" />
  </svg>
);