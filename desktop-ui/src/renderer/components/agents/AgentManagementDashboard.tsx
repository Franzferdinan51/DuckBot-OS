import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { cn, formatUptime, formatBytes, getStatusColor } from '@/lib/utils';
import {
  Play,
  Pause,
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
  Zap,
  Bot,
  Users,
  Network,
  BarChart3,
  TrendingUp,
  TrendingDown,
  Minus,
  Plus,
  RefreshCw,
  MessageSquare,
  Layers,
  Scale,
  Target,
  Timer,
  DollarSign,
  Hash,
  Monitor,
  Globe,
  Database,
  Wrench,
  Shield,
  Zap as Bolt
} from 'lucide-react';
import {
  Agent,
  AgentTask,
  AgentCoordination,
  AgentMessage,
  AgentMetrics,
  AgentActivity,
  AgentConfig
} from '@/types';

interface AgentManagementDashboardProps {
  agents: Agent[];
  tasks: AgentTask[];
  coordinations: AgentCoordination[];
  metrics: AgentMetrics[];
  activities: AgentActivity[];
  onAgentAction: (agentId: string, action: 'start' | 'stop' | 'restart' | 'scale' | 'configure') => Promise<void>;
  onTaskAction: (taskId: string, action: 'cancel' | 'retry' | 'reassign') => Promise<void>;
  onAgentConfigure: (agentId: string, config: AgentConfig) => Promise<void>;
}

interface AgentCardProps {
  agent: Agent;
  onAction: (action: 'start' | 'stop' | 'restart' | 'scale' | 'configure') => Promise<void>;
  metrics?: AgentMetrics;
}

interface TaskQueueProps {
  tasks: AgentTask[];
  agents: Agent[];
  onTaskAction: (taskId: string, action: 'cancel' | 'retry' | 'reassign') => Promise<void>;
}

interface CoordinationViewProps {
  coordinations: AgentCoordination[];
  agents: Agent[];
}

export function AgentManagementDashboard({
  agents,
  tasks,
  coordinations,
  metrics,
  activities,
  onAgentAction,
  onTaskAction,
  onAgentConfigure
}: AgentManagementDashboardProps) {
  const [filteredAgents, setFilteredAgents] = useState<Agent[]>(agents);
  const [filteredTasks, setFilteredTasks] = useState<AgentTask[]>(tasks);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  const [selectedTask, setSelectedTask] = useState<AgentTask | null>(null);
  const [agentActivities, setAgentActivities] = useState<AgentActivity[]>(activities);
  const [agentMetrics, setAgentMetrics] = useState<AgentMetrics[]>(metrics);
  const [isConfiguring, setIsConfiguring] = useState(false);
  const [configData, setConfigData] = useState<Partial<AgentConfig>>({});

  useEffect(() => {
    let filtered = agents;

    if (searchTerm) {
      filtered = filtered.filter(agent =>
        agent.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        agent.description.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    if (statusFilter !== 'all') {
      filtered = filtered.filter(agent => agent.status === statusFilter);
    }

    if (typeFilter !== 'all') {
      filtered = filtered.filter(agent => agent.type === typeFilter);
    }

    setFilteredAgents(filtered);
  }, [agents, searchTerm, statusFilter, typeFilter]);

  useEffect(() => {
    let filtered = tasks;

    if (statusFilter !== 'all') {
      filtered = filtered.filter(task => task.status === statusFilter);
    }

    setFilteredTasks(filtered);
  }, [tasks, statusFilter]);

  const getAgentStats = () => {
    const active = agents.filter(a => a.status === 'active').length;
    const busy = agents.filter(a => a.status === 'busy').length;
    const idle = agents.filter(a => a.status === 'idle').length;
    const error = agents.filter(a => a.status === 'error').length;
    const total = agents.length;

    const totalTasks = tasks.length;
    const runningTasks = tasks.filter(t => t.status === 'running').length;
    const completedTasks = tasks.filter(t => t.status === 'completed').length;

    return { active, busy, idle, error, total, totalTasks, runningTasks, completedTasks };
  };

  const getAgentMetrics = (agentId: string) => {
    return agentMetrics.find(m => m.agent_id === agentId);
  };

  const getAgentTasks = (agentId: string) => {
    return tasks.filter(t => t.agent_id === agentId);
  };

  const getAgentActivities = (agentId: string) => {
    return activities.filter(a => a.agent_id === agentId);
  };

  const handleAgentConfigure = async (agent: Agent) => {
    setSelectedAgent(agent);
    setConfigData(agent.config || {});
    setIsConfiguring(true);
  };

  const saveAgentConfig = async () => {
    if (selectedAgent && configData) {
      await onAgentConfigure(selectedAgent.id, configData as AgentConfig);
      setIsConfiguring(false);
      setSelectedAgent(null);
    }
  };

  const stats = getAgentStats();

  return (
    <div className="space-y-6">
      {/* Header and controls */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-foreground">AI Agent Management</h2>
          <p className="text-muted-foreground">Monitor and manage AI agents, tasks, and coordination</p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => agents.forEach(agent => {
              if (agent.status !== 'active') onAgentAction(agent.id, 'start');
            })}
          >
            <Play className="w-4 h-4 mr-2" />
            Start All
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => agents.forEach(agent => {
              if (agent.status === 'active') onAgentAction(agent.id, 'stop');
            })}
          >
            <Square className="w-4 h-4 mr-2" />
            Stop All
          </Button>
        </div>
      </div>

      {/* Stats cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Total Agents</p>
                <p className="text-2xl font-bold">{stats.total}</p>
              </div>
              <Bot className="w-8 h-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Active Agents</p>
                <p className="text-2xl font-bold text-green-600">{stats.active}</p>
              </div>
              <CheckCircle className="w-8 h-8 text-green-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Running Tasks</p>
                <p className="text-2xl font-bold text-blue-600">{stats.runningTasks}</p>
              </div>
              <Activity className="w-8 h-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Completed Tasks</p>
                <p className="text-2xl font-bold text-purple-600">{stats.completedTasks}</p>
              </div>
              <Target className="w-8 h-8 text-purple-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main content tabs */}
      <Tabs defaultValue="agents" className="space-y-4">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="agents">Agents</TabsTrigger>
          <TabsTrigger value="tasks">Tasks</TabsTrigger>
          <TabsTrigger value="coordination">Coordination</TabsTrigger>
          <TabsTrigger value="monitoring">Monitoring</TabsTrigger>
        </TabsList>

        {/* Agents Tab */}
        <TabsContent value="agents" className="space-y-4">
          {/* Filters */}
          <Card>
            <CardContent className="p-4">
              <div className="flex flex-col sm:flex-row gap-4">
                <div className="flex-1">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                    <Input
                      placeholder="Search agents..."
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
                    <SelectItem value="active">Active</SelectItem>
                    <SelectItem value="idle">Idle</SelectItem>
                    <SelectItem value="busy">Busy</SelectItem>
                    <SelectItem value="error">Error</SelectItem>
                    <SelectItem value="offline">Offline</SelectItem>
                    <SelectItem value="scaling">Scaling</SelectItem>
                  </SelectContent>
                </Select>
                <Select value={typeFilter} onValueChange={setTypeFilter}>
                  <SelectTrigger className="w-full sm:w-[180px]">
                    <SelectValue placeholder="Filter by type" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Types</SelectItem>
                    <SelectItem value="coding">Coding</SelectItem>
                    <SelectItem value="research">Research</SelectItem>
                    <SelectItem value="automation">Automation</SelectItem>
                    <SelectItem value="analysis">Analysis</SelectItem>
                    <SelectItem value="coordination">Coordination</SelectItem>
                    <SelectItem value="specialist">Specialist</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>

          {/* Agent grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredAgents.map((agent) => (
              <AgentCard
                key={agent.id}
                agent={agent}
                onAction={(action) => onAgentAction(agent.id, action)}
                metrics={getAgentMetrics(agent.id)}
              />
            ))}
          </div>
        </TabsContent>

        {/* Tasks Tab */}
        <TabsContent value="tasks">
          <TaskQueue
            tasks={filteredTasks}
            agents={agents}
            onTaskAction={onTaskAction}
          />
        </TabsContent>

        {/* Coordination Tab */}
        <TabsContent value="coordination">
          <CoordinationView
            coordinations={coordinations}
            agents={agents}
          />
        </TabsContent>

        {/* Monitoring Tab */}
        <TabsContent value="monitoring" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* System Metrics */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <BarChart3 className="w-5 h-5" />
                  System Metrics
                </CardTitle>
                <CardDescription>Overall system performance metrics</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {agentMetrics.slice(0, 5).map((metric) => (
                  <div key={`${metric.agent_id}-${metric.timestamp}`} className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>CPU Usage</span>
                      <span>{metric.cpu_usage.toFixed(1)}%</span>
                    </div>
                    <Progress value={metric.cpu_usage} className="h-2" />
                    <div className="flex justify-between text-sm">
                      <span>Memory Usage</span>
                      <span>{metric.memory_usage.toFixed(1)}%</span>
                    </div>
                    <Progress value={metric.memory_usage} className="h-2" />
                    <div className="flex justify-between text-sm">
                      <span>Response Time</span>
                      <span>{metric.response_time.toFixed(0)}ms</span>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>

            {/* Recent Activities */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Activity className="w-5 h-5" />
                  Recent Activities
                </CardTitle>
                <CardDescription>Latest agent activities and events</CardDescription>
              </CardHeader>
              <CardContent className="space-y-2 max-h-96 overflow-y-auto">
                {activities.slice(0, 10).map((activity) => (
                  <div key={activity.id} className="flex items-start gap-3 p-2 rounded border">
                    <div className={cn(
                      'p-1 rounded',
                      activity.level === 'error' ? 'bg-red-100 text-red-600' :
                      activity.level === 'warning' ? 'bg-yellow-100 text-yellow-600' :
                      activity.level === 'info' ? 'bg-blue-100 text-blue-600' :
                      'bg-gray-100 text-gray-600'
                    )}>
                      {activity.level === 'error' ? <AlertTriangle className="w-4 h-4" /> :
                       activity.level === 'warning' ? <AlertTriangle className="w-4 h-4" /> :
                       <CheckCircle className="w-4 h-4" />}
                    </div>
                    <div className="flex-1">
                      <p className="text-sm font-medium">{activity.action}</p>
                      <p className="text-xs text-muted-foreground">
                        {new Date(activity.timestamp).toLocaleTimeString()}
                      </p>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>

      {/* Agent Configuration Dialog */}
      <Dialog open={isConfiguring} onOpenChange={setIsConfiguring}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Settings className="w-5 h-5" />
              Configure Agent - {selectedAgent?.name}
            </DialogTitle>
            <DialogDescription>
              Configure agent settings and scaling parameters
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            {/* Basic Configuration */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold">Basic Configuration</h3>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="maxConcurrentTasks">Max Concurrent Tasks</Label>
                  <Input
                    id="maxConcurrentTasks"
                    type="number"
                    value={configData.max_concurrent_tasks || 5}
                    onChange={(e) => setConfigData(prev => ({...prev, max_concurrent_tasks: parseInt(e.target.value)}))}
                  />
                </div>

                <div>
                  <Label htmlFor="timeoutMs">Timeout (ms)</Label>
                  <Input
                    id="timeoutMs"
                    type="number"
                    value={configData.timeout_ms || 30000}
                    onChange={(e) => setConfigData(prev => ({...prev, timeout_ms: parseInt(e.target.value)}))}
                  />
                </div>

                <div>
                  <Label htmlFor="retryCount">Retry Count</Label>
                  <Input
                    id="retryCount"
                    type="number"
                    value={configData.retry_count || 3}
                    onChange={(e) => setConfigData(prev => ({...prev, retry_count: parseInt(e.target.value)}))}
                  />
                </div>

                <div>
                  <Label htmlFor="priority">Priority</Label>
                  <Select value={configData.priority || 'normal'} onValueChange={(value) => setConfigData(prev => ({...prev, priority: value}))}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="low">Low</SelectItem>
                      <SelectItem value="normal">Normal</SelectItem>
                      <SelectItem value="high">High</SelectItem>
                      <SelectItem value="critical">Critical</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </div>

            {/* Resource Limits */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold">Resource Limits</h3>

              <div className="grid grid-cols-3 gap-4">
                <div>
                  <Label htmlFor="maxCpu">Max CPU (%)</Label>
                  <Input
                    id="maxCpu"
                    type="number"
                    value={configData.resource_limits?.max_cpu || 80}
                    onChange={(e) => setConfigData(prev => ({
                      ...prev,
                      resource_limits: {...prev.resource_limits, max_cpu: parseInt(e.target.value)}
                    }))}
                  />
                </div>

                <div>
                  <Label htmlFor="maxMemory">Max Memory (MB)</Label>
                  <Input
                    id="maxMemory"
                    type="number"
                    value={configData.resource_limits?.max_memory || 2048}
                    onChange={(e) => setConfigData(prev => ({
                      ...prev,
                      resource_limits: {...prev.resource_limits, max_memory: parseInt(e.target.value)}
                    }))}
                  />
                </div>

                <div>
                  <Label htmlFor="maxTokens">Max Tokens</Label>
                  <Input
                    id="maxTokens"
                    type="number"
                    value={configData.resource_limits?.max_tokens || 100000}
                    onChange={(e) => setConfigData(prev => ({
                      ...prev,
                      resource_limits: {...prev.resource_limits, max_tokens: parseInt(e.target.value)}
                    }))}
                  />
                </div>
              </div>
            </div>

            {/* Auto Scaling */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold">Auto Scaling</h3>
                <Switch
                  checked={configData.auto_scale || false}
                  onCheckedChange={(checked) => setConfigData(prev => ({...prev, auto_scale: checked}))}
                />
              </div>

              {configData.auto_scale && (
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="minInstances">Min Instances</Label>
                    <Input
                      id="minInstances"
                      type="number"
                      value={configData.scale_config?.min_instances || 1}
                      onChange={(e) => setConfigData(prev => ({
                        ...prev,
                        scale_config: {...prev.scale_config, min_instances: parseInt(e.target.value)}
                      }))}
                    />
                  </div>

                  <div>
                    <Label htmlFor="maxInstances">Max Instances</Label>
                    <Input
                      id="maxInstances"
                      type="number"
                      value={configData.scale_config?.max_instances || 3}
                      onChange={(e) => setConfigData(prev => ({
                        ...prev,
                        scale_config: {...prev.scale_config, max_instances: parseInt(e.target.value)}
                      }))}
                    />
                  </div>

                  <div>
                    <Label htmlFor="scaleUpThreshold">Scale Up Threshold (%)</Label>
                    <Input
                      id="scaleUpThreshold"
                      type="number"
                      value={configData.scale_config?.scale_up_threshold || 80}
                      onChange={(e) => setConfigData(prev => ({
                        ...prev,
                        scale_config: {...prev.scale_config, scale_up_threshold: parseInt(e.target.value)}
                      }))}
                    />
                  </div>

                  <div>
                    <Label htmlFor="scaleDownThreshold">Scale Down Threshold (%)</Label>
                    <Input
                      id="scaleDownThreshold"
                      type="number"
                      value={configData.scale_config?.scale_down_threshold || 20}
                      onChange={(e) => setConfigData(prev => ({
                        ...prev,
                        scale_config: {...prev.scale_config, scale_down_threshold: parseInt(e.target.value)}
                      }))}
                    />
                  </div>
                </div>
              )}
            </div>

            {/* Actions */}
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setIsConfiguring(false)}>
                Cancel
              </Button>
              <Button onClick={saveAgentConfig}>
                Save Configuration
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}

function AgentCard({ agent, onAction, metrics }: AgentCardProps) {
  const [isLoading, setIsLoading] = useState(false);
  const agentTasks = []; // This would be passed as prop or fetched
  const agentActivities = []; // This would be passed as prop or fetched

  const handleAction = async (action: 'start' | 'stop' | 'restart' | 'scale' | 'configure') => {
    setIsLoading(true);
    try {
      await onAction(action);
    } finally {
      setIsLoading(false);
    }
  };

  const getAgentIcon = (agentType: string) => {
    const iconMap: Record<string, React.ComponentType<{ className?: string }>> = {
      coding: Terminal,
      research: Search,
      automation: Zap,
      analysis: BarChart3,
      general: Bot,
      coordination: Users,
      specialist: Shield
    };
    return iconMap[agentType] || Bot;
  };

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      active: 'bg-green-100 text-green-600 dark:bg-green-900/20',
      idle: 'bg-gray-100 text-gray-600 dark:bg-gray-900/20',
      busy: 'bg-yellow-100 text-yellow-600 dark:bg-yellow-900/20',
      error: 'bg-red-100 text-red-600 dark:bg-red-900/20',
      offline: 'bg-gray-100 text-gray-600 dark:bg-gray-900/20',
      scaling: 'bg-blue-100 text-blue-600 dark:bg-blue-900/20',
      maintenance: 'bg-orange-100 text-orange-600 dark:bg-orange-900/20'
    };
    return colors[status] || 'bg-gray-100 text-gray-600 dark:bg-gray-900/20';
  };

  const getHealthScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const Icon = getAgentIcon(agent.type);

  return (
    <Card className="transition-all hover:shadow-lg">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className={cn('p-2 rounded-lg', getStatusColor(agent.status))}>
              <Icon className="w-5 h-5" />
            </div>
            <div>
              <CardTitle className="text-lg">{agent.name}</CardTitle>
              <CardDescription className="text-sm">{agent.description}</CardDescription>
            </div>
          </div>
          <Badge className={getStatusColor(agent.status)}>
            {agent.status}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="pt-0 space-y-4">
        {/* Agent metrics */}
        {agent.performance && (
          <div className="grid grid-cols-2 gap-2 text-sm">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Tasks:</span>
              <span>{agent.performance.tasks_completed}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Success:</span>
              <span>{(agent.performance.success_rate * 100).toFixed(1)}%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Response:</span>
              <span>{agent.performance.avg_response_time.toFixed(0)}ms</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Health:</span>
              <span className={getHealthScoreColor(agent.health_score)}>
                {agent.health_score}/100
              </span>
            </div>
          </div>
        )}

        {/* Real-time metrics */}
        {metrics && (
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">CPU:</span>
              <span>{metrics.cpu_usage.toFixed(1)}%</span>
            </div>
            <Progress value={metrics.cpu_usage} className="h-1" />
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Memory:</span>
              <span>{metrics.memory_usage.toFixed(1)}%</span>
            </div>
            <Progress value={metrics.memory_usage} className="h-1" />
          </div>
        )}

        {/* Agent controls */}
        <div className="flex gap-1">
          {agent.status === 'active' ? (
            <>
              <Button
                size="sm"
                variant="outline"
                onClick={() => handleAction('restart')}
                disabled={isLoading}
                className="flex-1"
              >
                <RotateCcw className="w-3 h-3 mr-1" />
                Restart
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => handleAction('stop')}
                disabled={isLoading}
                className="flex-1"
              >
                <Square className="w-3 h-3 mr-1" />
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
              <Play className="w-3 h-3 mr-1" />
              Start
            </Button>
          )}
          <Button
            size="sm"
            variant="outline"
            onClick={() => handleAction('configure')}
            disabled={isLoading}
          >
            <Settings className="w-3 h-3" />
          </Button>
        </div>

        {/* Error indicator */}
        {agent.status === 'error' && (
          <div className="flex items-center gap-2 p-2 bg-red-50 dark:bg-red-900/20 rounded border border-red-200 dark:border-red-800">
            <AlertTriangle className="w-4 h-4 text-red-500" />
            <span className="text-sm text-red-600 dark:text-red-400">
              Agent requires attention
            </span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function TaskQueue({ tasks, agents, onTaskAction }: TaskQueueProps) {
  const getAgentName = (agentId: string) => {
    const agent = agents.find(a => a.id === agentId);
    return agent?.name || agentId;
  };

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      pending: 'bg-gray-100 text-gray-600',
      running: 'bg-blue-100 text-blue-600',
      completed: 'bg-green-100 text-green-600',
      failed: 'bg-red-100 text-red-600',
      cancelled: 'bg-orange-100 text-orange-600',
      retrying: 'bg-yellow-100 text-yellow-600'
    };
    return colors[status] || 'bg-gray-100 text-gray-600';
  };

  const getPriorityColor = (priority: string) => {
    const colors: Record<string, string> = {
      low: 'bg-gray-100 text-gray-600',
      normal: 'bg-blue-100 text-blue-600',
      high: 'bg-orange-100 text-orange-600',
      critical: 'bg-red-100 text-red-600'
    };
    return colors[priority] || 'bg-gray-100 text-gray-600';
  };

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {tasks.map((task) => (
          <Card key={task.id}>
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-sm">{task.type}</CardTitle>
                  <CardDescription className="text-xs">
                    {getAgentName(task.agent_id)}
                  </CardDescription>
                </div>
                <div className="flex gap-1">
                  <Badge className={getStatusColor(task.status)}>
                    {task.status}
                  </Badge>
                  <Badge className={getPriorityColor(task.priority)}>
                    {task.priority}
                  </Badge>
                </div>
              </div>
            </CardHeader>
            <CardContent className="pt-0 space-y-2">
              <div className="text-xs text-muted-foreground space-y-1">
                <div>Created: {new Date(task.created_at).toLocaleString()}</div>
                {task.duration && <div>Duration: {task.duration}ms</div>}
                {task.retry_count > 0 && <div>Retries: {task.retry_count}</div>}
              </div>

              <div className="flex gap-1">
                {task.status === 'running' && (
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => onTaskAction(task.id, 'cancel')}
                    className="text-xs"
                  >
                    Cancel
                  </Button>
                )}
                {task.status === 'failed' && (
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => onTaskAction(task.id, 'retry')}
                    className="text-xs"
                  >
                    Retry
                  </Button>
                )}
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => onTaskAction(task.id, 'reassign')}
                  className="text-xs"
                >
                  Reassign
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

function CoordinationView({ coordinations, agents }: CoordinationViewProps) {
  const getAgentName = (agentId: string) => {
    const agent = agents.find(a => a.id === agentId);
    return agent?.name || agentId;
  };

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      forming: 'bg-gray-100 text-gray-600',
      coordinating: 'bg-blue-100 text-blue-600',
      executing: 'bg-yellow-100 text-yellow-600',
      completed: 'bg-green-100 text-green-600',
      failed: 'bg-red-100 text-red-600'
    };
    return colors[status] || 'bg-gray-100 text-gray-600';
  };

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {coordinations.map((coordination) => (
          <Card key={coordination.id}>
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-sm">{coordination.task_type}</CardTitle>
                  <CardDescription className="text-xs">
                    Coordinator: {getAgentName(coordination.coordinator_id)}
                  </CardDescription>
                </div>
                <Badge className={getStatusColor(coordination.status)}>
                  {coordination.status}
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="pt-0 space-y-2">
              <div className="text-xs text-muted-foreground">
                <div>Participants: {coordination.participant_ids.map(getAgentName).join(', ')}</div>
                <div>Messages: {coordination.messages.length}</div>
                <div>Created: {new Date(coordination.created_at).toLocaleString()}</div>
              </div>

              <div className="flex items-center gap-1">
                <Users className="w-3 h-3 text-muted-foreground" />
                <span className="text-xs">
                  {coordination.participant_ids.length} agents coordinating
                </span>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}