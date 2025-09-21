import React, { useState, useEffect } from 'react';
import { AgentManagementDashboard } from './AgentManagementDashboard';
import {
  Agent,
  AgentTask,
  AgentCoordination,
  AgentMetrics,
  AgentActivity,
  AgentConfig
} from '@/types';

// Example data for demonstration
const sampleAgents: Agent[] = [
  {
    id: 'agent-001',
    name: 'Code Reviewer',
    type: 'coding',
    status: 'active',
    description: 'Specialized in code analysis and review',
    capabilities: ['code_review', 'bug_detection', 'performance_analysis'],
    provider: 'lm_studio',
    model: 'qwen3-coder-30b',
    performance: {
      tasks_completed: 156,
      success_rate: 0.94,
      avg_response_time: 1250,
      cpu_usage: 45,
      memory_usage: 2048,
      tokens_processed: 1250000,
      cost_incurred: 12.50
    },
    created_at: new Date('2024-01-15'),
    last_activity: new Date(),
    health_score: 85,
    config: {
      max_concurrent_tasks: 5,
      timeout_ms: 30000,
      retry_count: 3,
      priority: 'normal',
      resource_limits: {
        max_cpu: 80,
        max_memory: 4096,
        max_tokens: 200000
      },
      auto_scale: true,
      scale_config: {
        min_instances: 1,
        max_instances: 3,
        scale_up_threshold: 80,
        scale_down_threshold: 20
      }
    }
  },
  {
    id: 'agent-002',
    name: 'Research Assistant',
    type: 'research',
    status: 'busy',
    description: 'AI research and data analysis specialist',
    capabilities: ['web_search', 'data_analysis', 'report_generation'],
    provider: 'openai',
    model: 'gpt-4',
    performance: {
      tasks_completed: 89,
      success_rate: 0.97,
      avg_response_time: 2100,
      cpu_usage: 67,
      memory_usage: 3072,
      tokens_processed: 890000,
      cost_incurred: 45.20
    },
    created_at: new Date('2024-01-20'),
    last_activity: new Date(),
    health_score: 92
  },
  {
    id: 'agent-003',
    name: 'Automation Bot',
    type: 'automation',
    status: 'active',
    description: 'Desktop automation and workflow execution',
    capabilities: ['ui_automation', 'file_operations', 'workflow_execution'],
    provider: 'anthropic',
    model: 'claude-3-sonnet',
    performance: {
      tasks_completed: 234,
      success_rate: 0.88,
      avg_response_time: 800,
      cpu_usage: 34,
      memory_usage: 1536,
      tokens_processed: 750000,
      cost_incurred: 28.90
    },
    created_at: new Date('2024-01-10'),
    last_activity: new Date(),
    health_score: 78
  },
  {
    id: 'agent-004',
    name: 'System Monitor',
    type: 'analysis',
    status: 'active',
    description: 'Real-time system monitoring and alerting',
    capabilities: ['system_monitoring', 'performance_analysis', 'alerting'],
    provider: 'lm_studio',
    model: 'qwen3-coder-30b',
    performance: {
      tasks_completed: 445,
      success_rate: 0.99,
      avg_response_time: 450,
      cpu_usage: 23,
      memory_usage: 1024,
      tokens_processed: 450000,
      cost_incurred: 8.75
    },
    created_at: new Date('2024-01-05'),
    last_activity: new Date(),
    health_score: 95
  }
];

const sampleTasks: AgentTask[] = [
  {
    id: 'task-001',
    agent_id: 'agent-001',
    type: 'code_review',
    input: { repository: 'duckbot-webui', files: ['AgentManagementDashboard.tsx'] },
    status: 'running',
    created_at: new Date(Date.now() - 300000),
    priority: 'high',
    retry_count: 0,
    dependencies: []
  },
  {
    id: 'task-002',
    agent_id: 'agent-002',
    type: 'research',
    input: { query: 'AI agent coordination patterns', depth: 'comprehensive' },
    status: 'pending',
    created_at: new Date(Date.now() - 600000),
    priority: 'normal',
    retry_count: 0,
    dependencies: ['task-001']
  },
  {
    id: 'task-003',
    agent_id: 'agent-003',
    type: 'automation',
    input: { workflow: 'system_backup', target: 'database' },
    status: 'completed',
    created_at: new Date(Date.now() - 1800000),
    completed_at: new Date(Date.now() - 1200000),
    duration: 450000,
    priority: 'normal',
    retry_count: 0,
    dependencies: []
  }
];

const sampleCoordinations: AgentCoordination[] = [
  {
    id: 'coord-001',
    coordinator_id: 'agent-004',
    participant_ids: ['agent-001', 'agent-002', 'agent-003'],
    task_type: 'system_optimization',
    status: 'coordinating',
    messages: [],
    shared_context: { goal: 'optimize system performance', constraints: ['minimize_cost', 'maximize_efficiency'] },
    created_at: new Date(Date.now() - 900000)
  }
];

const sampleMetrics: AgentMetrics[] = [
  {
    agent_id: 'agent-001',
    timestamp: new Date(),
    cpu_usage: 45,
    memory_usage: 2048,
    response_time: 1250,
    throughput: 12.5,
    error_rate: 0.06,
    active_connections: 5,
    queue_size: 2,
    health_score: 85
  },
  {
    agent_id: 'agent-002',
    timestamp: new Date(),
    cpu_usage: 67,
    memory_usage: 3072,
    response_time: 2100,
    throughput: 8.2,
    error_rate: 0.03,
    active_connections: 8,
    queue_size: 5,
    health_score: 92
  }
];

const sampleActivities: AgentActivity[] = [
  {
    id: 'activity-001',
    agent_id: 'agent-001',
    action: 'Started code review task',
    details: { task_id: 'task-001', repository: 'duckbot-webui' },
    level: 'info',
    timestamp: new Date(Date.now() - 300000),
    result: 'success'
  },
  {
    id: 'activity-002',
    agent_id: 'agent-002',
    action: 'Queue research task',
    details: { query: 'AI agent coordination patterns', priority: 'normal' },
    level: 'info',
    timestamp: new Date(Date.now() - 600000),
    result: 'success'
  },
  {
    id: 'activity-003',
    agent_id: 'agent-003',
    action: 'Completed automation workflow',
    details: { workflow: 'system_backup', duration: 450000 },
    level: 'info',
    timestamp: new Date(Date.now() - 1200000),
    result: 'success'
  },
  {
    id: 'activity-004',
    agent_id: 'agent-004',
    action: 'Health check failed',
    details: { service: 'monitoring', error: 'Connection timeout' },
    level: 'warning',
    timestamp: new Date(Date.now() - 1800000),
    result: 'failure'
  }
];

export function AgentManagementExample() {
  const [agents, setAgents] = useState<Agent[]>(sampleAgents);
  const [tasks, setTasks] = useState<AgentTask[]>(sampleTasks);
  const [coordinations, setCoordinations] = useState<AgentCoordination[]>(sampleCoordinations);
  const [metrics, setMetrics] = useState<AgentMetrics[]>(sampleMetrics);
  const [activities, setActivities] = useState<AgentActivity[]>(sampleActivities);

  // Simulate real-time updates
  useEffect(() => {
    const interval = setInterval(() => {
      // Update metrics
      setMetrics(prev => prev.map(metric => ({
        ...metric,
        timestamp: new Date(),
        cpu_usage: Math.max(10, Math.min(90, metric.cpu_usage + (Math.random() - 0.5) * 10)),
        memory_usage: Math.max(500, Math.min(4096, metric.memory_usage + (Math.random() - 0.5) * 100)),
        response_time: Math.max(200, Math.min(3000, metric.response_time + (Math.random() - 0.5) * 200)),
        health_score: Math.max(50, Math.min(100, metric.health_score + (Math.random() - 0.5) * 5))
      })));

      // Add random activities
      const randomAgent = agents[Math.floor(Math.random() * agents.length)];
      const newActivity: AgentActivity = {
        id: `activity-${Date.now()}`,
        agent_id: randomAgent.id,
        action: 'Heartbeat check',
        details: { status: 'healthy' },
        level: 'debug',
        timestamp: new Date(),
        result: 'success'
      };

      setActivities(prev => [newActivity, ...prev.slice(0, 19)]);
    }, 5000);

    return () => clearInterval(interval);
  }, [agents]);

  const handleAgentAction = async (agentId: string, action: 'start' | 'stop' | 'restart' | 'scale' | 'configure') => {
    console.log(`Agent action: ${action} for agent ${agentId}`);

    setAgents(prev => prev.map(agent => {
      if (agent.id === agentId) {
        switch (action) {
          case 'start':
            return { ...agent, status: 'active' as const };
          case 'stop':
            return { ...agent, status: 'offline' as const };
          case 'restart':
            return { ...agent, status: 'active' as const };
          case 'scale':
            return { ...agent, status: 'scaling' as const };
          case 'configure':
            return agent;
          default:
            return agent;
        }
      }
      return agent;
    }));
  };

  const handleTaskAction = async (taskId: string, action: 'cancel' | 'retry' | 'reassign') => {
    console.log(`Task action: ${action} for task ${taskId}`);

    setTasks(prev => prev.map(task => {
      if (task.id === taskId) {
        switch (action) {
          case 'cancel':
            return { ...task, status: 'cancelled' as const };
          case 'retry':
            return { ...task, status: 'retrying' as const };
          case 'reassign':
            return { ...task, status: 'pending' as const };
          default:
            return task;
        }
      }
      return task;
    }));
  };

  const handleAgentConfigure = async (agentId: string, config: AgentConfig) => {
    console.log(`Configure agent ${agentId} with config:`, config);

    setAgents(prev => prev.map(agent => {
      if (agent.id === agentId) {
        return { ...agent, config };
      }
      return agent;
    }));
  };

  return (
    <div className="container mx-auto p-6">
      <AgentManagementDashboard
        agents={agents}
        tasks={tasks}
        coordinations={coordinations}
        metrics={metrics}
        activities={activities}
        onAgentAction={handleAgentAction}
        onTaskAction={handleTaskAction}
        onAgentConfigure={handleAgentConfigure}
      />
    </div>
  );
}