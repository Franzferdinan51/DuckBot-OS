// Core Types for DuckBot Desktop UI
export interface SystemMetrics {
  cpu: {
    usage: number;
    temperature?: number;
    cores: number;
  };
  memory: {
    usage: number;
    total: number;
    available: number;
    used: number;
  };
  disk: {
    usage: number;
    total: number;
    free: number;
  };
  network: {
    downloadSpeed: number;
    uploadSpeed: number;
    latency: number;
    status: 'connected' | 'disconnected' | 'error';
  };
  gpu?: {
    usage: number;
    temperature: number;
    memory: {
      usage: number;
      total: number;
      used: number;
    };
  };
}

export interface ServiceStatus {
  id: string;
  name: string;
  status: 'running' | 'stopped' | 'error' | 'starting' | 'stopping';
  cpu: number;
  memory: number;
  uptime?: string;
  lastUpdated: Date;
  category: 'core' | 'integration' | 'enhanced' | 'agent';
  description: string;
  port?: number;
  healthScore: number; // 0-100
}

export interface AgentInstance {
  id: string;
  name: string;
  type: 'ai' | 'automation' | 'monitoring' | 'specialist';
  status: 'idle' | 'active' | 'processing' | 'error' | 'offline';
  capabilities: string[];
  currentTask?: string;
  performance: {
    tasksCompleted: number;
    successRate: number;
    averageResponseTime: number;
  };
  lastActivity: Date;
  resources: {
    cpu: number;
    memory: number;
  };
}

export interface Conversation {
  id: string;
  title: string;
  agent: string;
  messages: Message[];
  createdAt: Date;
  updatedAt: Date;
  tags: string[];
  isPinned: boolean;
  context?: {
    sessionId: string;
    memoryUsed: number;
  };
}

export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  metadata?: {
    tokens?: number;
    cost?: number;
    model?: string;
    confidence?: number;
  };
}

export interface CostTracking {
  totalCost: number;
  currentSession: number;
  dailyLimit: number;
  monthlyLimit: number;
  byProvider: Record<string, {
    cost: number;
    tokens: number;
    requests: number;
  }>;
  byModel: Record<string, {
    cost: number;
    tokens: number;
    requests: number;
  }>;
  predictions: {
    projectedDaily: number;
    projectedMonthly: number;
    recommendations: string[];
  };
}

export interface Alert {
  id: string;
  type: 'info' | 'warning' | 'error' | 'success';
  title: string;
  message: string;
  timestamp: Date;
  source: string;
  action?: {
    label: string;
    callback: () => void;
  };
  isRead: boolean;
  severity: 'low' | 'medium' | 'high' | 'critical';
}

export interface AutomationCommand {
  id: string;
  name: string;
  description: string;
  category: string;
  parameters: Record<string, {
    type: 'string' | 'number' | 'boolean' | 'select';
    required: boolean;
    description: string;
    options?: string[];
    default?: any;
  }>;
  lastUsed?: Date;
  successRate: number;
  isFavorite: boolean;
}

export interface NotificationSettings {
  enabled: boolean;
  sound: boolean;
  desktop: boolean;
  types: {
    alerts: boolean;
    agents: boolean;
    services: boolean;
    costs: boolean;
  };
  quietHours: {
    enabled: boolean;
    start: string; // HH:mm format
    end: string;   // HH:mm format
  };
}

export interface ThemeSettings {
  mode: 'dark' | 'light' | 'system';
  accent: string;
  fontSize: 'small' | 'medium' | 'large';
  animations: boolean;
  density: 'comfortable' | 'compact' | 'spacious';
}

export interface DashboardLayout {
  sidebar: {
    collapsed: boolean;
    width: number;
  };
  panels: {
    monitoring: boolean;
    agents: boolean;
    automation: boolean;
    costs: boolean;
  };
  windows: {
    [appId: string]: {
      position: { x: number; y: number };
      size: { width: number; height: number };
      minimized: boolean;
      maximized: boolean;
    };
  };
}

// WebSocket Event Types
export interface SystemUpdate {
  type: 'metrics' | 'services' | 'agents' | 'alerts';
  timestamp: Date;
  data: any;
}

export interface WebSocketMessage {
  type: string;
  payload: any;
  timestamp: Date;
}

// Component Props
export interface DashboardProps {
  className?: string;
  children?: React.ReactNode;
}

export interface ServiceCardProps {
  service: ServiceStatus;
  onAction: (action: 'start' | 'stop' | 'restart' | 'logs') => void;
}

export interface AgentCardProps {
  agent: AgentInstance;
  onInteract: (agentId: string) => void;
  onConfigure: (agentId: string) => void;
}

export interface MetricChartProps {
  data: Array<{ time: Date; value: number }>;
  metric: string;
  unit: string;
  color: string;
  threshold?: number;
}

export interface CostWidgetProps {
  costData: CostTracking;
  onLimitChange: (type: 'daily' | 'monthly', value: number) => void;
}

export interface NotificationToastProps {
  notification: Alert;
  onDismiss: (id: string) => void;
  onAction: (id: string) => void;
}

export interface ConfigEditorProps {
  config: any;
  onSave: (config: any) => void;
  onValidate: (config: any) => boolean;
  schema?: any;
}