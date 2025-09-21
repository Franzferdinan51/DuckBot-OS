// Service Management Types
export interface ServiceStatus {
  name: string
  status: 'running' | 'stopped' | 'error' | 'starting' | 'stopping'
  pid?: number
  port?: number
  uptime: number
  lastError?: string
  cpu?: number
  memory?: number
}

export interface SystemMetrics {
  cpu: {
    usage: number
    cores: number
    temperature?: number
  }
  memory: {
    total: number
    used: number
    available: number
    percentage: number
  }
  disk: {
    total: number
    used: number
    available: number
    percentage: number
  }
  network: {
    download: number
    upload: number
    latency: number
  }
  timestamp: Date
}

export interface CostData {
  total: number
  byProvider: Record<string, number>
  byService: Record<string, number>
  today: number
  thisMonth: number
  transactions: CostTransaction[]
}

// Cost Tracking Types
export interface CostData {
  total: number
  byProvider: Record<string, ProviderCostData>
  byService: Record<string, ServiceCostData>
  today: number
  thisMonth: number
  thisYear: number
  budget?: BudgetData
  transactions: CostTransaction[]
  alerts: CostAlert[]
  forecasts: CostForecast[]
}

export interface ProviderCostData {
  name: string
  total: number
  today: number
  thisMonth: number
  thisYear: number
  transactionCount: number
  avgCostPerRequest: number
  avgTokensPerRequest: number
  lastTransaction?: Date
  trend: 'up' | 'down' | 'stable'
  trendPercentage: number
}

export interface ServiceCostData {
  name: string
  category: 'chat' | 'automation' | 'monitoring' | 'analysis' | 'other'
  total: number
  today: number
  thisMonth: number
  thisYear: number
  transactionCount: number
  avgCostPerRequest: number
  peakUsageHours: number[]
  efficiency: number
}

export interface CostTransaction {
  id: string
  provider: string
  service: string
  cost: number
  timestamp: Date
  tokens?: number
  requestType: string
  responseTime: number
  success: boolean
  metadata?: Record<string, any>
}

export interface BudgetData {
  monthly: number
  daily: number
  alertThreshold: number
  hardLimit: number
  period: 'daily' | 'weekly' | 'monthly'
  rollover: boolean
  notifications: boolean
}

export interface CostAlert {
  id: string
  type: 'budget_warning' | 'budget_exceeded' | 'cost_spike' | 'inefficient_usage'
  severity: 'low' | 'medium' | 'high' | 'critical'
  title: string
  message: string
  timestamp: Date
  resolved: boolean
  action?: {
    label: string
    callback: () => void
  }
  metadata?: Record<string, any>
}

export interface CostForecast {
  period: 'day' | 'week' | 'month' | 'year'
  predicted: number
  confidence: number
  factors: string[]
  recommendation: string
  trend: 'increasing' | 'decreasing' | 'stable'
}

export interface CostOptimization {
  id: string
  type: 'provider_switch' | 'model_optimization' | 'batch_requests' | 'caching' | 'quota_management'
  title: string
  description: string
  potentialSavings: number
  implementationDifficulty: 'low' | 'medium' | 'high'
  priority: 'low' | 'medium' | 'high'
  status: 'pending' | 'implemented' | 'dismissed'
  steps: string[]
}

export interface CostExportOptions {
  format: 'csv' | 'json' | 'pdf' | 'excel'
  dateRange: {
    start: Date
    end: Date
  }
  includeTransactions: boolean
  includeForecasts: boolean
  includeOptimizations: boolean
  groupBy: 'provider' | 'service' | 'date' | 'none'
}

export interface CostAnalytics {
  totalCost: number
  avgDailyCost: number
  costGrowthRate: number
  mostExpensiveProvider: string
  mostExpensiveService: string
  peakUsageHours: number[]
  efficiencyScore: number
  costPerToken: number
  budgetUtilization: number
}

export interface CostTransaction {
  id: string
  provider: string
  service: string
  cost: number
  timestamp: Date
  tokens?: number
}

// AI Configuration Types
export interface AIConfig {
  providers: {
    openai?: ProviderConfig
    anthropic?: ProviderConfig
    qwen?: ProviderConfig
    lm_studio?: ProviderConfig
  }
  services: {
    webui?: ServiceConfig
    monitoring?: ServiceConfig
    automation?: ServiceConfig
  }
  features: {
    local_only: boolean
    cost_tracking: boolean
    memory_persistence: boolean
    agent_coordination: boolean
  }
}

export interface ProviderConfig {
  enabled: boolean
  api_key?: string
  model?: string
  base_url?: string
  max_tokens?: number
  temperature?: number
  local?: boolean
}

export interface ServiceConfig {
  enabled: boolean
  port?: number
  host?: string
  config?: Record<string, any>
}

// Agent Types
export interface Agent {
  id: string
  name: string
  type: 'coding' | 'research' | 'automation' | 'analysis' | 'general' | 'coordination' | 'specialist'
  status: 'active' | 'idle' | 'busy' | 'error' | 'offline' | 'scaling' | 'maintenance'
  description: string
  capabilities: string[]
  provider: string
  model?: string
  performance?: {
    tasks_completed: number
    success_rate: number
    avg_response_time: number
    cpu_usage: number
    memory_usage: number
    tokens_processed: number
    cost_incurred: number
  }
  created_at: Date
  last_activity?: Date
  health_score: number
  config?: AgentConfig
  deployment?: AgentDeployment
}

export interface AgentConfig {
  max_concurrent_tasks: number
  timeout_ms: number
  retry_count: number
  priority: 'low' | 'normal' | 'high' | 'critical'
  resource_limits: {
    max_cpu: number
    max_memory: number
    max_tokens: number
  }
  auto_scale: boolean
  scale_config: {
    min_instances: number
    max_instances: number
    scale_up_threshold: number
    scale_down_threshold: number
  }
}

export interface AgentDeployment {
  instance_id: string
  host: string
  port: number
  region?: string
  version: string
  health_check_url?: string
  metrics_url?: string
}

export interface AgentTask {
  id: string
  agent_id: string
  type: string
  input: any
  output?: any
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled' | 'retrying'
  created_at: Date
  completed_at?: Date
  error?: string
  duration?: number
  priority: 'low' | 'normal' | 'high' | 'critical'
  retry_count: number
  assigned_to?: string[]
  dependencies?: string[]
  metadata?: Record<string, any>
}

export interface AgentCoordination {
  id: string
  coordinator_id: string
  participant_ids: string[]
  task_type: string
  status: 'forming' | 'coordinating' | 'executing' | 'completed' | 'failed'
  messages: AgentMessage[]
  shared_context: any
  created_at: Date
  completed_at?: Date
}

export interface AgentMessage {
  id: string
  from_agent_id: string
  to_agent_id?: string
  content: any
  type: 'task_assignment' | 'status_update' | 'data_request' | 'result_sharing' | 'coordination'
  timestamp: Date
  delivered: boolean
  read: boolean
}

export interface AgentMetrics {
  agent_id: string
  timestamp: Date
  cpu_usage: number
  memory_usage: number
  response_time: number
  throughput: number
  error_rate: number
  active_connections: number
  queue_size: number
  health_score: number
}

export interface AgentActivity {
  id: string
  agent_id: string
  action: string
  details: any
  level: 'info' | 'warning' | 'error' | 'debug'
  timestamp: Date
  duration?: number
  result?: 'success' | 'failure' | 'pending'
}

// Chat Types
export interface ChatMessage {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  provider?: string
  model?: string
  tokens?: number
  cost?: number
  timestamp: Date
  metadata?: Record<string, any>
}

export interface Conversation {
  id: string
  title: string
  messages: ChatMessage[]
  created_at: Date
  updated_at: Date
  provider?: string
  model?: string
  tags?: string[]
}

// Automation Types
export interface AutomationCommand {
  id: string
  name: string
  description: string
  command: string
  parameters?: Record<string, any>
  category: string
  enabled: boolean
  schedule?: string
  created_at: Date
  last_run?: Date
  next_run?: Date
  run_count: number
  success_rate: number
}

export interface AutomationExecution {
  id: string
  command_id: string
  parameters: Record<string, any>
  status: 'pending' | 'running' | 'completed' | 'failed'
  started_at: Date
  completed_at?: Date
  output?: any
  error?: string
  duration?: number
}

// Enhanced Automation Types
export interface AutomationWorkflow {
  id: string
  name: string
  description: string
  version: string
  status: 'draft' | 'active' | 'paused' | 'archived' | 'error'
  triggers: WorkflowTrigger[]
  steps: WorkflowStep[]
  variables: WorkflowVariable[]
  dependencies: string[]
  created_at: Date
  updated_at: Date
  last_executed?: Date
  execution_count: number
  success_rate: number
  average_duration: number
  tags: string[]
  author: string
  permissions: WorkflowPermission[]
}

export interface WorkflowTrigger {
  id: string
  type: 'manual' | 'schedule' | 'event' | 'webhook' | 'api' | 'file' | 'system'
  config: TriggerConfig
  enabled: boolean
  conditions?: TriggerCondition[]
}

export interface TriggerConfig {
  schedule?: string // cron expression
  event?: string
  webhook_url?: string
  api_endpoint?: string
  file_pattern?: string
  system_event?: string
  parameters?: Record<string, any>
}

export interface TriggerCondition {
  field: string
  operator: 'equals' | 'contains' | 'greater_than' | 'less_than' | 'regex'
  value: any
}

export interface WorkflowStep {
  id: string
  name: string
  type: 'action' | 'condition' | 'loop' | 'parallel' | 'delay' | 'notification' | 'integration'
  action: StepAction
  inputs: Record<string, any>
  outputs?: Record<string, any>
  conditions?: StepCondition[]
  retry_config?: RetryConfig
  timeout_ms: number
  position: StepPosition
  dependencies: string[]
  on_success?: string[]
  on_failure?: string[]
}

export interface StepAction {
  type: 'bytebot' | 'ui_tars' | 'browser_use' | 'system' | 'api' | 'file' | 'ai' | 'custom'
  service: string
  command: string
  parameters: Record<string, any>
  validation?: StepValidation
}

export interface StepValidation {
  required: string[]
  rules: ValidationRule[]
}

export interface ValidationRule {
  field: string
  type: 'required' | 'type' | 'range' | 'regex' | 'custom'
  condition: any
  message: string
}

export interface StepCondition {
  field: string
  operator: string
  value: any
}

export interface RetryConfig {
  max_attempts: number
  delay_ms: number
  backoff_multiplier: number
  max_delay_ms: number
}

export interface StepPosition {
  x: number
  y: number
  width?: number
  height?: number
}

export interface WorkflowVariable {
  name: string
  type: 'string' | 'number' | 'boolean' | 'object' | 'array' | 'date'
  value?: any
  default?: any
  description?: string
  required: boolean
  source: 'input' | 'output' | 'static' | 'computed'
}

export interface WorkflowPermission {
  user_id: string
  role: 'owner' | 'editor' | 'viewer' | 'executor'
  permissions: string[]
}

export interface WorkflowExecution {
  id: string
  workflow_id: string
  trigger_id?: string
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled' | 'paused'
  inputs: Record<string, any>
  outputs?: Record<string, any>
  current_step?: string
  error?: string
  started_at: Date
  completed_at?: Date
  duration?: number
  steps: StepExecution[]
  logs: ExecutionLog[]
  metrics: ExecutionMetrics
  artifacts: ExecutionArtifact[]
}

export interface StepExecution {
  id: string
  step_id: string
  status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped' | 'retried'
  inputs: Record<string, any>
  outputs?: Record<string, any>
  error?: string
  started_at: Date
  completed_at?: Date
  duration?: number
  retry_count: number
  logs: ExecutionLog[]
  artifacts: ExecutionArtifact[]
}

export interface ExecutionLog {
  id: string
  level: 'debug' | 'info' | 'warning' | 'error'
  message: string
  timestamp: Date
  step_id?: string
  data?: any
}

export interface ExecutionMetrics {
  total_steps: number
  completed_steps: number
  failed_steps: number
  total_duration: number
  average_step_duration: number
  memory_usage: number
  cpu_usage: number
  network_calls: number
  api_calls: number
  cost: number
}

export interface ExecutionArtifact {
  id: string
  name: string
  type: 'file' | 'screenshot' | 'log' | 'data' | 'report'
  url?: string
  content?: string
  size?: number
  created_at: Date
}

export interface ScheduledTask {
  id: string
  name: string
  workflow_id: string
  schedule: string
  enabled: boolean
  next_run: Date
  last_run?: Date
  timezone: string
  parameters: Record<string, any>
  execution_history: ScheduledTaskExecution[]
  created_at: Date
  updated_at: Date
}

export interface ScheduledTaskExecution {
  id: string
  scheduled_time: Date
  actual_time: Date
  status: 'success' | 'failed' | 'skipped'
  execution_id?: string
  error?: string
}

export interface AutomationService {
  id: string
  name: string
  type: 'bytebot' | 'ui_tars' | 'browser_use' | 'ai' | 'system' | 'api' | 'custom'
  status: 'running' | 'stopped' | 'error' | 'starting'
  endpoint?: string
  version: string
  capabilities: string[]
  commands: string[]
  config: Record<string, any>
  metrics: ServiceMetrics
  health_check: {
    enabled: boolean
    interval_ms: number
    timeout_ms: number
  }
}

export interface ServiceMetrics {
  uptime_ms: number
  requests_total: number
  requests_successful: number
  requests_failed: number
  average_response_time: number
  error_rate: number
  cpu_usage: number
  memory_usage: number
  last_check: Date
}

export interface AutomationTemplate {
  id: string
  name: string
  description: string
  category: string
  icon: string
  tags: string[]
  workflow: Partial<AutomationWorkflow>
  parameters: TemplateParameter[]
  estimated_duration: number
  difficulty: 'beginner' | 'intermediate' | 'advanced'
  author: string
  downloads: number
  rating: number
  created_at: Date
}

export interface TemplateParameter {
  name: string
  type: string
  required: boolean
  default?: any
  description: string
  example?: any
}

export interface AutomationStats {
  total_workflows: number
  active_workflows: number
  total_executions: number
  successful_executions: number
  failed_executions: number
  average_execution_time: number
  total_cost: number
  services_running: number
  scheduled_tasks: number
  templates_available: number
}

export interface AutomationLog {
  id: string
  timestamp: Date
  level: 'debug' | 'info' | 'warning' | 'error'
  source: 'workflow' | 'service' | 'system' | 'user'
  message: string
  data?: any
  execution_id?: string
  workflow_id?: string
  service_id?: string
}

export interface WorkflowBuilderState {
  workflow: Partial<AutomationWorkflow>
  selectedStep: string | null
  isEditing: boolean
  isRunning: boolean
  zoom: number
  pan: { x: number; y: number }
  showGrid: boolean
  snapToGrid: boolean
}

export interface DropZone {
  id: string
  type: 'input' | 'output' | 'connection'
  stepId: string
  position: { x: number; y: number }
  acceptedTypes: string[]
}

// Log Types
export interface LogEntry {
  id: string
  service: string
  type: 'stdout' | 'stderr' | 'info' | 'warning' | 'error'
  data: string
  timestamp: Date
  level?: 'debug' | 'info' | 'warn' | 'error'
}

// Configuration Types
export interface AppConfig {
  windowBounds: {
    width: number
    height: number
  }
  theme: 'light' | 'dark' | 'system'
  autoStart: boolean
  minimizeToTray: boolean
  notifications: boolean
  services: {
    lmStudioUrl: string
    webuiPort: number
    monitoringPort: number
  }
  features: {
    autoUpdate: boolean
    telemetry: boolean
    debugMode: boolean
  }
}

// UI Component Types
export interface NavigationItem {
  name: string
  href: string
  icon: string
  badge?: number
  description?: string
}

export interface StatCard {
  title: string
  value: string | number
  change?: number
  changeType?: 'increase' | 'decrease'
  icon: string
  color: string
}

export interface ChartDataPoint {
  timestamp: Date
  value: number
  label?: string
}

export interface Alert {
  id: string
  type: 'info' | 'warning' | 'error' | 'success'
  title: string
  message: string
  timestamp: Date
  action?: {
    label: string
    onClick: () => void
  }
  dismissible?: boolean
}

// WebSocket Event Types
export interface WebSocketEvent {
  type: string
  data: any
  timestamp: Date
}

// API Response Types
export interface ApiResponse<T> {
  success: boolean
  data?: T
  error?: string
  message?: string
  timestamp: Date
}

// Form Types
export interface FormField {
  name: string
  label: string
  type: 'text' | 'number' | 'select' | 'checkbox' | 'switch' | 'textarea' | 'password'
  required?: boolean
  placeholder?: string
  description?: string
  options?: Array<{ value: string; label: string }>
  validation?: {
    min?: number
    max?: number
    pattern?: string
    custom?: (value: any) => string | null
  }
}

export interface FormSection {
  title: string
  fields: FormField[]
  description?: string
}

// Error Types
export interface AppError {
  code: string
  message: string
  details?: any
  timestamp: Date
  stack?: string
}