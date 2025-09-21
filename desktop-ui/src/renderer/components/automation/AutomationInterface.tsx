import React, { useState, useEffect, useCallback } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useWebSocket } from '@hooks/useWebSocket'
import { useAppStore } from '@stores/useAppStore'
import { useElectron } from '@lib/electron'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from './ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs'
import { Button } from './ui/button'
import { Input } from './ui/input'
import { Badge } from './ui/badge'
import { Progress } from './ui/progress'
import { Alert, AlertDescription } from './ui/alert'
import { ScrollArea } from './ui/scroll-area'
import {
  Play,
  Pause,
  Square,
  Settings,
  Plus,
  Trash2,
  Edit,
  Download,
  Upload,
  Zap,
  Bot,
  Clock,
  AlertTriangle,
  CheckCircle,
  Activity,
  Command,
  Calendar,
  Monitor,
  Cpu,
  MemoryStick,
  HardDrive,
  Network,
  FileText,
  Terminal,
  Workflow,
  Users,
  Database,
  Server,
  Wrench,
  RefreshCw,
  Save,
  Send,
  X,
  Eye,
  EyeOff,
  Copy,
  RotateCcw,
  MoreHorizontal,
  ChevronDown,
  ChevronRight,
  GripVertical,
  PlusCircle,
  MinusCircle,
} from 'lucide-react'
import { StatsCard } from './ui/stats-card'
import {
  AutomationWorkflow,
  WorkflowExecution,
  AutomationService,
  ScheduledTask,
  AutomationStats,
  AutomationLog,
  WorkflowBuilderState,
  StepAction,
} from '@types/index'

interface AutomationInterfaceProps {
  className?: string
}

export function AutomationInterface({ className }: AutomationInterfaceProps) {
  const queryClient = useQueryClient()
  const { lastMessage, sendMessage } = useWebSocket('automation')
  const { services } = useAppStore()
  const { executeAutomation } = useElectron()

  // State management
  const [activeTab, setActiveTab] = useState('workflows')
  const [selectedWorkflow, setSelectedWorkflow] = useState<AutomationWorkflow | null>(null)
  const [isEditingWorkflow, setIsEditingWorkflow] = useState(false)
  const [workflowBuilderState, setWorkflowBuilderState] = useState<WorkflowBuilderState>({
    workflow: {},
    selectedStep: null,
    isEditing: false,
    isRunning: false,
    zoom: 1,
    pan: { x: 0, y: 0 },
    showGrid: true,
    snapToGrid: true,
  })
  const [commandInput, setCommandInput] = useState('')
  const [executionLogs, setExecutionLogs] = useState<AutomationLog[]>([])
  const [isExecuting, setIsExecuting] = useState(false)

  // Mock data for development
  const mockStats: AutomationStats = {
    total_workflows: 24,
    active_workflows: 8,
    total_executions: 156,
    successful_executions: 142,
    failed_executions: 14,
    average_execution_time: 2.3,
    total_cost: 12.45,
    services_running: 3,
    scheduled_tasks: 12,
    templates_available: 18,
  }

  const mockWorkflows: AutomationWorkflow[] = [
    {
      id: '1',
      name: 'Daily Backup',
      description: 'Automated daily system backup with notification',
      version: '1.0.0',
      status: 'active',
      triggers: [{
        id: 't1',
        type: 'schedule',
        config: { schedule: '0 2 * * *' },
        enabled: true,
      }],
      steps: [],
      variables: [],
      dependencies: [],
      created_at: new Date(),
      updated_at: new Date(),
      last_executed: new Date(),
      execution_count: 45,
      success_rate: 0.95,
      average_duration: 180000,
      tags: ['backup', 'daily', 'critical'],
      author: 'system',
      permissions: [],
    },
    {
      id: '2',
      name: 'Web Scraping Pipeline',
      description: 'Extract data from multiple websites and process results',
      version: '2.1.0',
      status: 'draft',
      triggers: [{
        id: 't2',
        type: 'manual',
        config: {},
        enabled: true,
      }],
      steps: [],
      variables: [],
      dependencies: [],
      created_at: new Date(),
      updated_at: new Date(),
      execution_count: 0,
      success_rate: 0,
      average_duration: 0,
      tags: ['scraping', 'data', 'web'],
      author: 'user',
      permissions: [],
    },
  ]

  const mockServices: AutomationService[] = [
    {
      id: 'bytebot',
      name: 'ByteBot',
      type: 'bytebot',
      status: 'running',
      version: '1.0.0',
      capabilities: [
        'Natural language task execution',
        'Desktop automation',
        'Screenshot capture',
        'Application control',
        'File operations',
        'Web automation',
      ],
      commands: ['execute_task', 'capture_screenshot', 'open_application', 'type_text', 'click_element'],
      config: { endpoint: 'http://localhost:8080' },
      metrics: {
        uptime_ms: 86400000,
        requests_total: 234,
        requests_successful: 225,
        requests_failed: 9,
        average_response_time: 450,
        error_rate: 0.038,
        cpu_usage: 12.5,
        memory_usage: 256,
        last_check: new Date(),
      },
      health_check: {
        enabled: true,
        interval_ms: 30000,
        timeout_ms: 5000,
      },
    },
    {
      id: 'ui_tars',
      name: 'UI-TARS',
      type: 'ui_tars',
      status: 'running',
      version: '0.9.2',
      capabilities: [
        'Visual UI automation',
        'Element detection',
        'Screen analysis',
        'Multi-step workflows',
        'Cross-application support',
      ],
      commands: ['detect_elements', 'analyze_screen', 'execute_workflow', 'train_model'],
      config: { model: 'ui-tars-vision' },
      metrics: {
        uptime_ms: 72000000,
        requests_total: 156,
        requests_successful: 148,
        requests_failed: 8,
        average_response_time: 680,
        error_rate: 0.051,
        cpu_usage: 18.7,
        memory_usage: 512,
        last_check: new Date(),
      },
      health_check: {
        enabled: true,
        interval_ms: 30000,
        timeout_ms: 10000,
      },
    },
  ]

  const mockScheduledTasks: ScheduledTask[] = [
    {
      id: '1',
      name: 'Daily Backup',
      workflow_id: '1',
      schedule: '0 2 * * *',
      enabled: true,
      next_run: new Date(Date.now() + 24 * 60 * 60 * 1000),
      last_run: new Date(),
      timezone: 'UTC',
      parameters: { compression: true, notifications: true },
      execution_history: [],
      created_at: new Date(),
      updated_at: new Date(),
    },
    {
      id: '2',
      name: 'Weekly Report',
      workflow_id: '3',
      schedule: '0 9 * * 1',
      enabled: true,
      next_run: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000),
      last_run: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000),
      timezone: 'UTC',
      parameters: { format: 'pdf', recipients: ['team@company.com'] },
      execution_history: [],
      created_at: new Date(),
      updated_at: new Date(),
    },
  ]

  // Query functions
  const fetchWorkflows = useCallback(async (): Promise<AutomationWorkflow[]> => {
    // In production, this would fetch from the backend
    return mockWorkflows
  }, [])

  const fetchServices = useCallback(async (): Promise<AutomationService[]> => {
    // In production, this would fetch from the backend
    return mockServices
  }, [])

  const fetchScheduledTasks = useCallback(async (): Promise<ScheduledTask[]> => {
    // In production, this would fetch from the backend
    return mockScheduledTasks
  }, [])

  const fetchStats = useCallback(async (): Promise<AutomationStats> => {
    // In production, this would fetch from the backend
    return mockStats
  }, [])

  const fetchExecutionLogs = useCallback(async (): Promise<AutomationLog[]> => {
    // In production, this would fetch from the backend
    return executionLogs
  }, [executionLogs])

  // React Query hooks
  const { data: workflows, isLoading: isLoadingWorkflows } = useQuery({
    queryKey: ['automation', 'workflows'],
    queryFn: fetchWorkflows,
    refetchInterval: 30000,
  })

  const { data: automationServices, isLoading: isLoadingServices } = useQuery({
    queryKey: ['automation', 'services'],
    queryFn: fetchServices,
    refetchInterval: 10000,
  })

  const { data: scheduledTasks, isLoading: isLoadingTasks } = useQuery({
    queryKey: ['automation', 'scheduled'],
    queryFn: fetchScheduledTasks,
    refetchInterval: 30000,
  })

  const { data: stats, isLoading: isLoadingStats } = useQuery({
    queryKey: ['automation', 'stats'],
    queryFn: fetchStats,
    refetchInterval: 30000,
  })

  const { data: logs, isLoading: isLoadingLogs } = useQuery({
    queryKey: ['automation', 'logs'],
    queryFn: fetchExecutionLogs,
    refetchInterval: 5000,
  })

  // Mutations
  const executeCommandMutation = useMutation({
    mutationFn: async (command: string) => {
      setIsExecuting(true)
      try {
        const result = await executeAutomation(command)

        // Add execution log
        const newLog: AutomationLog = {
          id: Date.now().toString(),
          timestamp: new Date(),
          level: result.success ? 'info' : 'error',
          source: 'user',
          message: command,
          data: result,
        }

        setExecutionLogs(prev => [newLog, ...prev.slice(0, 99)]) // Keep last 100 logs
        return result
      } finally {
        setIsExecuting(false)
      }
    },
    onSuccess: (result) => {
      if (result.success) {
        // Refresh relevant data
        queryClient.invalidateQueries({ queryKey: ['automation', 'stats'] })
        queryClient.invalidateQueries({ queryKey: ['automation', 'logs'] })
      }
    },
  })

  // WebSocket handlers
  useEffect(() => {
    if (lastMessage) {
      try {
        const data = JSON.parse(lastMessage.data)

        switch (data.type) {
          case 'workflow_execution_update':
            queryClient.invalidateQueries({ queryKey: ['automation', 'workflows'] })
            queryClient.invalidateQueries({ queryKey: ['automation', 'stats'] })
            break
          case 'service_status_change':
            queryClient.invalidateQueries({ queryKey: ['automation', 'services'] })
            break
          case 'automation_log':
            setExecutionLogs(prev => [data.log, ...prev.slice(0, 99)])
            break
          case 'workflow_step_update':
            // Update workflow builder state if this workflow is being edited
            if (selectedWorkflow && data.workflowId === selectedWorkflow.id) {
              setWorkflowBuilderState(prev => ({
                ...prev,
                workflow: {
                  ...prev.workflow,
                  steps: data.steps || prev.workflow.steps,
                },
              }))
            }
            break
        }
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error)
      }
    }
  }, [lastMessage, selectedWorkflow, queryClient])

  // Command execution
  const handleExecuteCommand = () => {
    if (!commandInput.trim()) return

    executeCommandMutation.mutate(commandInput)
    setCommandInput('')
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleExecuteCommand()
    }
  }

  // Workflow actions
  const handleCreateWorkflow = () => {
    const newWorkflow: Partial<AutomationWorkflow> = {
      name: 'New Workflow',
      description: 'Describe your workflow',
      version: '1.0.0',
      status: 'draft',
      triggers: [],
      steps: [],
      variables: [],
      dependencies: [],
      created_at: new Date(),
      updated_at: new Date(),
      execution_count: 0,
      success_rate: 0,
      average_duration: 0,
      tags: [],
      author: 'user',
      permissions: [],
    }

    setSelectedWorkflow(newWorkflow as AutomationWorkflow)
    setIsEditingWorkflow(true)
    setActiveTab('builder')
  }

  const handleEditWorkflow = (workflow: AutomationWorkflow) => {
    setSelectedWorkflow(workflow)
    setIsEditingWorkflow(true)
    setWorkflowBuilderState(prev => ({
      ...prev,
      workflow,
      selectedStep: null,
      isEditing: true,
    }))
    setActiveTab('builder')
  }

  const handleDeleteWorkflow = (workflowId: string) => {
    if (confirm('Are you sure you want to delete this workflow?')) {
      // In production, this would delete from the backend
      queryClient.invalidateQueries({ queryKey: ['automation', 'workflows'] })
    }
  }

  const handleSaveWorkflow = () => {
    if (!selectedWorkflow) return

    // In production, this would save to the backend
    setIsEditingWorkflow(false)
    setSelectedWorkflow(null)
    queryClient.invalidateQueries({ queryKey: ['automation', 'workflows'] })
  }

  // Service actions
  const handleToggleService = (serviceId: string) => {
    // In production, this would start/stop the service
    queryClient.invalidateQueries({ queryKey: ['automation', 'services'] })
  }

  const handleRestartService = (serviceId: string) => {
    // In production, this would restart the service
    queryClient.invalidateQueries({ queryKey: ['automation', 'services'] })
  }

  // Scheduled task actions
  const handleToggleTask = (taskId: string) => {
    // In production, this would enable/disable the task
    queryClient.invalidateQueries({ queryKey: ['automation', 'scheduled'] })
  }

  // Utility functions
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running':
      case 'active':
        return 'default'
      case 'stopped':
      case 'paused':
      case 'draft':
        return 'secondary'
      case 'error':
        return 'destructive'
      case 'starting':
        return 'outline'
      default:
        return 'secondary'
    }
  }

  const formatDuration = (ms: number) => {
    if (ms < 1000) return `${ms}ms`
    if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`
    if (ms < 3600000) return `${(ms / 60000).toFixed(1)}m`
    return `${(ms / 3600000).toFixed(1)}h`
  }

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const getStepIcon = (action: StepAction) => {
    switch (action.type) {
      case 'bytebot':
        return <Bot className="h-4 w-4" />
      case 'ui_tars':
        return <Monitor className="h-4 w-4" />
      case 'browser_use':
        return <Network className="h-4 w-4" />
      case 'system':
        return <Server className="h-4 w-4" />
      case 'api':
        return <Database className="h-4 w-4" />
      case 'file':
        return <FileText className="h-4 w-4" />
      case 'ai':
        return <Cpu className="h-4 w-4" />
      default:
        return <Wrench className="h-4 w-4" />
    }
  }

  if (isLoadingWorkflows || isLoadingServices || isLoadingStats) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-2" />
          <p className="text-sm text-muted-foreground">Loading automation interface...</p>
        </div>
      </div>
    )
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Automation</h1>
          <p className="text-muted-foreground">
            Manage workflows, schedule tasks, and monitor automation performance
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={() => queryClient.invalidateQueries()}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
          {activeTab === 'workflows' && (
            <Button onClick={handleCreateWorkflow}>
              <Plus className="h-4 w-4 mr-2" />
              New Workflow
            </Button>
          )}
        </div>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <StatsCard
            title="Total Workflows"
            value={stats.total_workflows.toString()}
            description={`${stats.active_workflows} active`}
            icon={Workflow}
            color="text-blue-600"
          />
          <StatsCard
            title="Success Rate"
            value={`${((stats.successful_executions / stats.total_executions) * 100).toFixed(1)}%`}
            description={`${stats.failed_executions} failed`}
            icon={CheckCircle}
            color="text-green-600"
          />
          <StatsCard
            title="Avg Duration"
            value={formatDuration(stats.average_execution_time * 1000)}
            description="Per execution"
            icon={Clock}
            color="text-purple-600"
          />
          <StatsCard
            title="Running Services"
            value={`${stats.services_running}/3`}
            description="Automation services"
            icon={Activity}
            color="text-orange-600"
          />
        </div>
      )}

      {/* Main Content Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="workflows">Workflows</TabsTrigger>
          <TabsTrigger value="builder">Builder</TabsTrigger>
          <TabsTrigger value="terminal">Terminal</TabsTrigger>
          <TabsTrigger value="scheduler">Scheduler</TabsTrigger>
          <TabsTrigger value="monitoring">Monitoring</TabsTrigger>
        </TabsList>

        <TabsContent value="workflows" className="space-y-4">
          <div className="grid gap-4">
            {workflows?.map((workflow) => (
              <Card key={workflow.id}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle className="flex items-center gap-2">
                        <Workflow className="h-5 w-5" />
                        {workflow.name}
                        <Badge variant={getStatusColor(workflow.status)}>
                          {workflow.status}
                        </Badge>
                      </CardTitle>
                      <CardDescription>{workflow.description}</CardDescription>
                    </div>
                    <div className="flex items-center gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleEditWorkflow(workflow)}
                      >
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleDeleteWorkflow(workflow.id)}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div>
                      <span className="font-medium">Executions:</span>
                      <p className="text-muted-foreground">{workflow.execution_count}</p>
                    </div>
                    <div>
                      <span className="font-medium">Success Rate:</span>
                      <p className="text-muted-foreground">
                        {(workflow.success_rate * 100).toFixed(1)}%
                      </p>
                    </div>
                    <div>
                      <span className="font-medium">Avg Duration:</span>
                      <p className="text-muted-foreground">
                        {formatDuration(workflow.average_duration)}
                      </p>
                    </div>
                    <div>
                      <span className="font-medium">Last Run:</span>
                      <p className="text-muted-foreground">
                        {workflow.last_executed
                          ? workflow.last_executed.toLocaleDateString()
                          : 'Never'
                        }
                      </p>
                    </div>
                  </div>
                  <div className="flex flex-wrap gap-1 mt-3">
                    {workflow.tags.map((tag) => (
                      <Badge key={tag} variant="outline" className="text-xs">
                        {tag}
                      </Badge>
                    ))}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="builder" className="space-y-4">
          {selectedWorkflow ? (
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      <Edit className="h-5 w-5" />
                      {selectedWorkflow.name}
                    </CardTitle>
                    <CardDescription>Workflow Builder</CardDescription>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button variant="outline" onClick={() => setIsEditingWorkflow(!isEditingWorkflow)}>
                      {isEditingWorkflow ? <Eye className="h-4 w-4" /> : <Edit className="h-4 w-4" />}
                      {isEditingWorkflow ? 'View' : 'Edit'}
                    </Button>
                    <Button onClick={handleSaveWorkflow}>
                      <Save className="h-4 w-4 mr-2" />
                      Save
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {/* Workflow Info */}
                  {isEditingWorkflow && (
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="text-sm font-medium">Name</label>
                        <Input
                          value={selectedWorkflow.name}
                          onChange={(e) => setSelectedWorkflow({
                            ...selectedWorkflow,
                            name: e.target.value
                          })}
                        />
                      </div>
                      <div>
                        <label className="text-sm font-medium">Description</label>
                        <Input
                          value={selectedWorkflow.description}
                          onChange={(e) => setSelectedWorkflow({
                            ...selectedWorkflow,
                            description: e.target.value
                          })}
                        />
                      </div>
                    </div>
                  )}

                  {/* Builder Canvas */}
                  <div className="border rounded-lg p-4 min-h-[400px] bg-muted/50 relative">
                    <div className="text-center text-muted-foreground py-8">
                      <Workflow className="h-12 w-12 mx-auto mb-2 opacity-50" />
                      <p>Drag and drop workflow steps here</p>
                      <p className="text-sm">Connect steps to create automation flows</p>
                    </div>

                    {/* Zoom Controls */}
                    <div className="absolute bottom-4 right-4 flex items-center gap-2">
                      <Button variant="outline" size="sm">
                        <MinusCircle className="h-4 w-4" />
                      </Button>
                      <span className="text-sm">100%</span>
                      <Button variant="outline" size="sm">
                        <PlusCircle className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>

                  {/* Step Library */}
                  <div>
                    <h3 className="text-sm font-medium mb-2">Step Library</h3>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                      <Button variant="outline" className="h-20 flex flex-col">
                        <Bot className="h-6 w-6 mb-1" />
                        <span className="text-xs">ByteBot</span>
                      </Button>
                      <Button variant="outline" className="h-20 flex flex-col">
                        <Monitor className="h-6 w-6 mb-1" />
                        <span className="text-xs">UI-TARS</span>
                      </Button>
                      <Button variant="outline" className="h-20 flex flex-col">
                        <Network className="h-6 w-6 mb-1" />
                        <span className="text-xs">Browser</span>
                      </Button>
                      <Button variant="outline" className="h-20 flex flex-col">
                        <FileText className="h-6 w-6 mb-1" />
                        <span className="text-xs">File Ops</span>
                      </Button>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent className="flex items-center justify-center py-12">
                <div className="text-center">
                  <Workflow className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                  <h3 className="text-lg font-medium mb-2">No Workflow Selected</h3>
                  <p className="text-muted-foreground mb-4">
                    Select a workflow to edit or create a new one
                  </p>
                  <Button onClick={handleCreateWorkflow}>
                    <Plus className="h-4 w-4 mr-2" />
                    Create Workflow
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="terminal" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Terminal className="h-5 w-5" />
                Automation Terminal
              </CardTitle>
              <CardDescription>
                Execute automation commands and see real-time output
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Command Input */}
              <div className="flex gap-2">
                <Input
                  value={commandInput}
                  onChange={(e) => setCommandInput(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Enter automation command..."
                  disabled={isExecuting}
                  className="flex-1"
                />
                <Button
                  onClick={handleExecuteCommand}
                  disabled={isExecuting || !commandInput.trim()}
                >
                  {isExecuting ? (
                    <RefreshCw className="h-4 w-4 animate-spin" />
                  ) : (
                    <Send className="h-4 w-4" />
                  )}
                </Button>
              </div>

              {/* Execution Logs */}
              <ScrollArea className="h-[400px] w-full border rounded-md p-4 bg-black text-green-400 font-mono text-sm">
                {logs?.map((log) => (
                  <div key={log.id} className="mb-2 last:mb-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-gray-500">
                        [{log.timestamp.toLocaleTimeString()}]
                      </span>
                      <Badge
                        variant={log.level === 'error' ? 'destructive' :
                                log.level === 'warning' ? 'outline' : 'default'}
                        className="text-xs"
                      >
                        {log.level.toUpperCase()}
                      </Badge>
                    </div>
                    <div className="break-all">{log.message}</div>
                    {log.data && (
                      <pre className="text-gray-400 text-xs mt-1 overflow-x-auto">
                        {JSON.stringify(log.data, null, 2)}
                      </pre>
                    )}
                  </div>
                ))}
                {(!logs || logs.length === 0) && (
                  <div className="text-gray-500 text-center py-8">
                    No execution logs yet. Run a command to see output.
                  </div>
                )}
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="scheduler" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Calendar className="h-5 w-5" />
                Scheduled Tasks
              </CardTitle>
              <CardDescription>
                Manage automated task scheduling and cron jobs
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {scheduledTasks?.map((task) => (
                  <div key={task.id} className="flex items-center justify-between p-4 border rounded-lg">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <h4 className="font-medium">{task.name}</h4>
                        <Badge variant={task.enabled ? 'default' : 'secondary'}>
                          {task.enabled ? 'Enabled' : 'Disabled'}
                        </Badge>
                      </div>
                      <p className="text-sm text-muted-foreground mb-1">
                        Schedule: {task.schedule}
                      </p>
                      <div className="flex items-center gap-4 text-xs text-muted-foreground">
                        <span>Next: {task.next_run.toLocaleString()}</span>
                        <span>Timezone: {task.timezone}</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleToggleTask(task.id)}
                      >
                        {task.enabled ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
                      </Button>
                      <Button variant="outline" size="sm">
                        <Edit className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                ))}
                {(!scheduledTasks || scheduledTasks.length === 0) && (
                  <div className="text-center py-8 text-muted-foreground">
                    No scheduled tasks configured yet.
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="monitoring" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            {/* Services Status */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Activity className="h-5 w-5" />
                  Services Status
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {automationServices?.map((service) => (
                    <div key={service.id} className="flex items-center justify-between p-3 border rounded-lg">
                      <div className="flex items-center gap-3">
                        <div className={`p-2 rounded-lg ${
                          service.status === 'running' ? 'bg-green-100 text-green-700' :
                          service.status === 'error' ? 'bg-red-100 text-red-700' :
                          'bg-gray-100 text-gray-700'
                        }`}>
                          {service.type === 'bytebot' && <Bot className="h-4 w-4" />}
                          {service.type === 'ui_tars' && <Monitor className="h-4 w-4" />}
                          {service.type === 'browser_use' && <Network className="h-4 w-4" />}
                        </div>
                        <div>
                          <h4 className="font-medium">{service.name}</h4>
                          <p className="text-sm text-muted-foreground">
                            Version {service.version}
                          </p>
                        </div>
                      </div>
                      <div className="text-right">
                        <Badge variant={getStatusColor(service.status)}>
                          {service.status}
                        </Badge>
                        <div className="text-xs text-muted-foreground mt-1">
                          {formatDuration(service.metrics.uptime_ms)} uptime
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Performance Metrics */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Cpu className="h-5 w-5" />
                  Performance Metrics
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {automationServices?.map((service) => (
                    <div key={service.id} className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium">{service.name}</span>
                        <span className="text-sm text-muted-foreground">
                          {service.metrics.error_rate.toFixed(1)}% error rate
                        </span>
                      </div>
                      <div className="space-y-2">
                        <div className="flex items-center justify-between text-xs">
                          <span>CPU Usage</span>
                          <span>{service.metrics.cpu_usage.toFixed(1)}%</span>
                        </div>
                        <Progress value={service.metrics.cpu_usage} className="h-2" />

                        <div className="flex items-center justify-between text-xs">
                          <span>Memory</span>
                          <span>{formatBytes(service.metrics.memory_usage)}</span>
                        </div>
                        <Progress
                          value={(service.metrics.memory_usage / 1024) * 100}
                          className="h-2"
                        />

                        <div className="flex items-center justify-between text-xs">
                          <span>Response Time</span>
                          <span>{service.metrics.average_response_time.toFixed(0)}ms</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}