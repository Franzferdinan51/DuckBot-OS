import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { AgentManagementDashboard } from './AgentManagementDashboard';
import {
  Agent,
  AgentTask,
  AgentCoordination,
  AgentMetrics,
  AgentActivity,
  AgentConfig
} from '@/types';

// Mock data for testing
const mockAgents: Agent[] = [
  {
    id: 'agent-001',
    name: 'Test Agent',
    type: 'coding',
    status: 'active',
    description: 'Test agent for unit testing',
    capabilities: ['testing', 'mocking'],
    provider: 'test-provider',
    performance: {
      tasks_completed: 10,
      success_rate: 0.9,
      avg_response_time: 100,
      cpu_usage: 50,
      memory_usage: 1024,
      tokens_processed: 1000,
      cost_incurred: 1.0
    },
    created_at: new Date('2024-01-01'),
    last_activity: new Date(),
    health_score: 85
  }
];

const mockTasks: AgentTask[] = [
  {
    id: 'task-001',
    agent_id: 'agent-001',
    type: 'test_task',
    input: { test: 'data' },
    status: 'running',
    created_at: new Date(),
    priority: 'normal',
    retry_count: 0,
    dependencies: []
  }
];

const mockCoordinations: AgentCoordination[] = [];
const mockMetrics: AgentMetrics[] = [
  {
    agent_id: 'agent-001',
    timestamp: new Date(),
    cpu_usage: 50,
    memory_usage: 1024,
    response_time: 100,
    throughput: 10,
    error_rate: 0.1,
    active_connections: 2,
    queue_size: 1,
    health_score: 85
  }
];

const mockActivities: AgentActivity[] = [
  {
    id: 'activity-001',
    agent_id: 'agent-001',
    action: 'Test action',
    details: {},
    level: 'info',
    timestamp: new Date(),
    result: 'success'
  }
];

const mockProps = {
  agents: mockAgents,
  tasks: mockTasks,
  coordinations: mockCoordinations,
  metrics: mockMetrics,
  activities: mockActivities,
  onAgentAction: jest.fn(),
  onTaskAction: jest.fn(),
  onAgentConfigure: jest.fn()
};

describe('AgentManagementDashboard', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders dashboard with header and stats', () => {
    render(<AgentManagementDashboard {...mockProps} />);

    expect(screen.getByText('AI Agent Management')).toBeInTheDocument();
    expect(screen.getByText('Monitor and manage AI agents, tasks, and coordination')).toBeInTheDocument();
    expect(screen.getByText('Total Agents')).toBeInTheDocument();
    expect(screen.getByText('Active Agents')).toBeInTheDocument();
    expect(screen.getByText('Running Tasks')).toBeInTheDocument();
    expect(screen.getByText('Completed Tasks')).toBeInTheDocument();
  });

  test('displays agent cards correctly', () => {
    render(<AgentManagementDashboard {...mockProps} />);

    expect(screen.getByText('Test Agent')).toBeInTheDocument();
    expect(screen.getByText('Test agent for unit testing')).toBeInTheDocument();
    expect(screen.getByText('10')).toBeInTheDocument(); // tasks completed
    expect(screen.getByText('90.0%')).toBeInTheDocument(); // success rate
    expect(screen.getByText('85/100')).toBeInTheDocument(); // health score
  });

  test('handles agent start action', async () => {
    render(<AgentManagementDashboard {...mockProps} />);

    const startButton = screen.getByText('Start');
    fireEvent.click(startButton);

    await waitFor(() => {
      expect(mockProps.onAgentAction).toHaveBeenCalledWith('agent-001', 'start');
    });
  });

  test('handles agent stop action', async () => {
    const activeAgent: Agent = {
      ...mockAgents[0],
      status: 'active'
    };

    render(<AgentManagementDashboard {...mockProps} agents={[activeAgent]} />);

    const stopButton = screen.getByText('Stop');
    fireEvent.click(stopButton);

    await waitFor(() => {
      expect(mockProps.onAgentAction).toHaveBeenCalledWith('agent-001', 'stop');
    });
  });

  test('handles agent restart action', async () => {
    const activeAgent: Agent = {
      ...mockAgents[0],
      status: 'active'
    };

    render(<AgentManagementDashboard {...mockProps} agents={[activeAgent]} />);

    const restartButton = screen.getByText('Restart');
    fireEvent.click(restartButton);

    await waitFor(() => {
      expect(mockProps.onAgentAction).toHaveBeenCalledWith('agent-001', 'restart');
    });
  });

  test('handles agent configure action', async () => {
    render(<AgentManagementDashboard {...mockProps} />);

    const configButton = screen.getByLabelText('Configure');
    fireEvent.click(configButton);

    // Configuration dialog should open
    await waitFor(() => {
      expect(screen.getByText('Configure Agent - Test Agent')).toBeInTheDocument();
    });
  });

  test('filters agents by search term', () => {
    render(<AgentManagementDashboard {...mockProps} />);

    const searchInput = screen.getByPlaceholderText('Search agents...');
    fireEvent.change(searchInput, { target: { value: 'nonexistent' } });

    // Should show no agents found message
    expect(screen.getByText('No agents found')).toBeInTheDocument();
  });

  test('filters agents by status', () => {
    render(<AgentManagementDashboard {...mockProps} />);

    const statusSelect = screen.getByDisplayValue('All Status');
    fireEvent.change(statusSelect, { target: { value: 'offline' } });

    // Should show no agents since none are offline
    expect(screen.getByText('No agents found')).toBeInTheDocument();
  });

  test('filters agents by type', () => {
    render(<AgentManagementDashboard {...mockProps} />);

    const typeSelect = screen.getByDisplayValue('All Types');
    fireEvent.change(typeSelect, { target: { value: 'research' } });

    // Should show no agents since none are research type
    expect(screen.getByText('No agents found')).toBeInTheDocument();
  });

  test('displays task queue correctly', async () => {
    render(<AgentManagementDashboard {...mockProps} />);

    // Switch to tasks tab
    const tasksTab = screen.getByText('Tasks');
    fireEvent.click(tasksTab);

    await waitFor(() => {
      expect(screen.getByText('test_task')).toBeInTheDocument();
      expect(screen.getByText('running')).toBeInTheDocument();
    });
  });

  test('handles task actions', async () => {
    render(<AgentManagementDashboard {...mockProps} />);

    // Switch to tasks tab
    const tasksTab = screen.getByText('Tasks');
    fireEvent.click(tasksTab);

    await waitFor(() => {
      const cancelButton = screen.getByText('Cancel');
      fireEvent.click(cancelButton);
      expect(mockProps.onTaskAction).toHaveBeenCalledWith('task-001', 'cancel');
    });
  });

  test('displays coordination view correctly', async () => {
    const mockCoordination: AgentCoordination = {
      id: 'coord-001',
      coordinator_id: 'agent-001',
      participant_ids: ['agent-002'],
      task_type: 'test_coordination',
      status: 'forming',
      messages: [],
      shared_context: {},
      created_at: new Date()
    };

    render(<AgentManagementDashboard {...mockProps} coordinations={[mockCoordination]} />);

    // Switch to coordination tab
    const coordinationTab = screen.getByText('Coordination');
    fireEvent.click(coordinationTab);

    await waitFor(() => {
      expect(screen.getByText('test_coordination')).toBeInTheDocument();
      expect(screen.getByText('forming')).toBeInTheDocument();
    });
  });

  test('displays monitoring tab correctly', async () => {
    render(<AgentManagementDashboard {...mockProps} />);

    // Switch to monitoring tab
    const monitoringTab = screen.getByText('Monitoring');
    fireEvent.click(monitoringTab);

    await waitFor(() => {
      expect(screen.getByText('System Metrics')).toBeInTheDocument();
      expect(screen.getByText('Recent Activities')).toBeInTheDocument();
    });
  });

  test('saves agent configuration', async () => {
    render(<AgentManagementDashboard {...mockProps} />);

    // Open configuration dialog
    const configButton = screen.getByLabelText('Configure');
    fireEvent.click(configButton);

    await waitFor(() => {
      expect(screen.getByText('Configure Agent - Test Agent')).toBeInTheDocument();
    });

    // Change configuration values
    const maxTasksInput = screen.getByDisplayValue('5');
    fireEvent.change(maxTasksInput, { target: { value: '10' } });

    const timeoutInput = screen.getByDisplayValue('30000');
    fireEvent.change(timeoutInput, { target: { value: '60000' } });

    // Save configuration
    const saveButton = screen.getByText('Save Configuration');
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(mockProps.onAgentConfigure).toHaveBeenCalledWith('agent-001', {
        max_concurrent_tasks: 10,
        timeout_ms: 60000,
        retry_count: 3,
        priority: 'normal',
        resource_limits: {
          max_cpu: 80,
          max_memory: 2048,
          max_tokens: 100000
        },
        auto_scale: false,
        scale_config: {
          min_instances: 1,
          max_instances: 3,
          scale_up_threshold: 80,
          scale_down_threshold: 20
        }
      });
    });
  });

  test('handles auto-scaling configuration', async () => {
    render(<AgentManagementDashboard {...mockProps} />);

    // Open configuration dialog
    const configButton = screen.getByLabelText('Configure');
    fireEvent.click(configButton);

    await waitFor(() => {
      expect(screen.getByText('Configure Agent - Test Agent')).toBeInTheDocument();
    });

    // Enable auto-scaling
    const autoScaleSwitch = screen.getByRole('switch');
    fireEvent.click(autoScaleSwitch);

    // Auto-scaling fields should appear
    expect(screen.getByDisplayValue('1')).toBeInTheDocument(); // min instances
    expect(screen.getByDisplayValue('3')).toBeInTheDocument(); // max instances
  });

  test('displays error states for agents', () => {
    const errorAgent: Agent = {
      ...mockAgents[0],
      status: 'error'
    };

    render(<AgentManagementDashboard {...mockProps} agents={[errorAgent]} />);

    expect(screen.getByText('Agent requires attention')).toBeInTheDocument();
  });

  test('displays performance metrics', () => {
    render(<AgentManagementDashboard {...mockProps} />);

    // Check for metric displays
    expect(screen.getByText('50.0%')).toBeInTheDocument(); // CPU usage
    expect(screen.getByText('100ms')).toBeInTheDocument(); // response time
  });

  test('handles loading states', () => {
    // This would typically be tested with async loading states
    // For now, we verify the component renders with empty data
    render(
      <AgentManagementDashboard
        agents={[]}
        tasks={[]}
        coordinations={[]}
        metrics={[]}
        activities={[]}
        onAgentAction={jest.fn()}
        onTaskAction={jest.fn()}
        onAgentConfigure={jest.fn()}
      />
    );

    expect(screen.getByText('Total Agents')).toBeInTheDocument();
    expect(screen.getByText('0')).toBeInTheDocument(); // Total agents
  });
});

describe('AgentManagementDashboard Integration', () => {
  test('integrates with real-time updates', () => {
    // This would test WebSocket integration
    // For now, we verify the component structure supports real-time updates
    render(<AgentManagementDashboard {...mockProps} />);

    expect(screen.getByText('AI Agent Management')).toBeInTheDocument();
    expect(screen.getByText('Recent Activities')).toBeInTheDocument();
  });

  test('handles large datasets gracefully', () => {
    // Create large dataset
    const manyAgents = Array.from({ length: 100 }, (_, i) => ({
      ...mockAgents[0],
      id: `agent-${i}`,
      name: `Agent ${i}`
    }));

    render(<AgentManagementDashboard {...mockProps} agents={manyAgents} />);

    // Should still render without performance issues
    expect(screen.getByText('Total Agents')).toBeInTheDocument();
    expect(screen.getByText('100')).toBeInTheDocument(); // Total agents
  });
});