# AI Agent Management Dashboard

A comprehensive React TypeScript component for managing and monitoring AI agents in the DuckBot ecosystem. This component provides real-time visibility into agent status, performance metrics, task management, and coordination activities.

## Features

### 🤖 Agent Management
- **Agent Overview Dashboard**: Real-time status and health monitoring of all AI agents
- **Agent Cards**: Detailed view of each agent with performance metrics and controls
- **Agent Configuration**: Advanced configuration for scaling, resource limits, and timeouts
- **Agent Lifecycle Management**: Start, stop, restart, and scale agents as needed

### 📊 Performance Monitoring
- **Real-time Metrics**: CPU usage, memory consumption, response times, and throughput
- **Health Scoring**: Comprehensive health assessment for each agent
- **Performance Analytics**: Success rates, task completion statistics, and cost tracking
- **Resource Monitoring**: Track token usage, costs, and resource utilization

### 🎯 Task Management
- **Task Queue Management**: View and manage agent task queues
- **Task Lifecycle**: Cancel, retry, or reassign tasks as needed
- **Priority Management**: Handle task priorities and dependencies
- **Task Analytics**: Track completion rates, durations, and success metrics

### 🤝 Agent Coordination
- **Coordination Dashboard**: Monitor multi-agent coordination activities
- **Message Tracking**: View agent-to-agent communication patterns
- **Collaboration Visualization**: See how agents work together on complex tasks
- **Coordination Metrics**: Track coordination success rates and efficiency

### 🔧 Advanced Features
- **Auto-scaling**: Configure automatic scaling based on workload
- **Resource Limits**: Set CPU, memory, and token limits per agent
- **Retry Configuration**: Configure retry policies and timeouts
- **Real-time Updates**: WebSocket integration for live data updates

## Component Architecture

### Main Component: `AgentManagementDashboard`

```typescript
interface AgentManagementDashboardProps {
  agents: Agent[];                    // Array of agents to manage
  tasks: AgentTask[];                 // Array of agent tasks
  coordinations: AgentCoordination[];  // Multi-agent coordination activities
  metrics: AgentMetrics[];             // Performance metrics
  activities: AgentActivity[];         // Recent agent activities
  onAgentAction: (agentId: string, action: AgentAction) => Promise<void>;
  onTaskAction: (taskId: string, action: TaskAction) => Promise<void>;
  onAgentConfigure: (agentId: string, config: AgentConfig) => Promise<void>;
}
```

### Key Sub-Components

- **AgentCard**: Individual agent display with metrics and controls
- **TaskQueue**: Task management interface
- **CoordinationView**: Multi-agent coordination visualization
- **AgentConfigurationDialog**: Configuration interface for agent settings

## Type Definitions

The component uses comprehensive TypeScript interfaces for type safety:

```typescript
// Core Agent Types
interface Agent {
  id: string;
  name: string;
  type: 'coding' | 'research' | 'automation' | 'analysis' | 'general' | 'coordination' | 'specialist';
  status: 'active' | 'idle' | 'busy' | 'error' | 'offline' | 'scaling' | 'maintenance';
  description: string;
  capabilities: string[];
  provider: string;
  model?: string;
  performance?: AgentPerformance;
  health_score: number;
  config?: AgentConfig;
  deployment?: AgentDeployment;
}

interface AgentConfig {
  max_concurrent_tasks: number;
  timeout_ms: number;
  retry_count: number;
  priority: 'low' | 'normal' | 'high' | 'critical';
  resource_limits: ResourceLimits;
  auto_scale: boolean;
  scale_config: ScaleConfig;
}

interface AgentMetrics {
  agent_id: string;
  timestamp: Date;
  cpu_usage: number;
  memory_usage: number;
  response_time: number;
  throughput: number;
  error_rate: number;
  active_connections: number;
  queue_size: number;
  health_score: number;
}
```

## Usage Examples

### Basic Usage

```typescript
import { AgentManagementDashboard } from '@/components/agents';

function App() {
  return (
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
  );
}
```

### With Real-time Updates

```typescript
import { useState, useEffect } from 'react';
import { AgentManagementDashboard } from '@/components/agents';
import { useWebSocket } from '@/hooks/useWebSocket';

function AgentDashboard() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [tasks, setTasks] = useState<AgentTask[]>([]);
  const [metrics, setMetrics] = useState<AgentMetrics[]>([]);

  const { lastMessage } = useWebSocket('ws://localhost:8789/ws');

  useEffect(() => {
    if (lastMessage) {
      const data = JSON.parse(lastMessage.data);
      if (data.type === 'agent_update') {
        setAgents(prev => updateAgent(prev, data.agent));
      } else if (data.type === 'metrics_update') {
        setMetrics(prev => [...prev, data.metrics]);
      }
    }
  }, [lastMessage]);

  return (
    <AgentManagementDashboard
      agents={agents}
      tasks={tasks}
      coordinations={[]}
      metrics={metrics}
      activities={[]}
      onAgentAction={handleAgentAction}
      onTaskAction={handleTaskAction}
      onAgentConfigure={handleAgentConfigure}
    />
  );
}
```

## Integration with DuckBot Ecosystem

### Backend Integration

The component integrates with the DuckBot backend through several mechanisms:

1. **IPC Communication**: Uses Electron's IPC for service management
2. **WebSocket Updates**: Real-time updates via WebSocket connections
3. **REST API**: Fallback for data fetching and configuration updates

### Service Manager Integration

```typescript
// Example backend service integration
class AgentServiceManager {
  async getAgents(): Promise<Agent[]> {
    return await window.electronAPI.getAgents();
  }

  async startAgent(agentId: string): Promise<void> {
    await window.electronAPI.startAgent(agentId);
  }

  async configureAgent(agentId: string, config: AgentConfig): Promise<void> {
    await window.electronAPI.configureAgent(agentId, config);
  }

  async getAgentMetrics(agentId: string): Promise<AgentMetrics[]> {
    return await window.electronAPI.getAgentMetrics(agentId);
  }
}
```

## Configuration

### Environment Variables

The component respects the following environment variables:

```bash
# WebSocket Configuration
WEBSOCKET_URL=ws://localhost:8789/ws

# API Configuration
API_BASE_URL=http://localhost:8789/api

# Update Frequency
METRICS_UPDATE_INTERVAL=5000
ACTIVITY_UPDATE_INTERVAL=2000

# UI Configuration
MAX_AGENTS_PER_PAGE=12
MAX_ACTIVITIES_DISPLAY=50
```

### Styling Configuration

The component uses Tailwind CSS with customizable theme variables:

```css
/* Agent status colors */
.agent-active { @apply bg-green-100 text-green-600; }
.agent-busy { @apply bg-yellow-100 text-yellow-600; }
.agent-error { @apply bg-red-100 text-red-600; }
.agent-offline { @apply bg-gray-100 text-gray-600; }

/* Metric thresholds */
.metric-good { @apply text-green-600; }
.metric-warning { @apply text-yellow-600; }
.metric-critical { @apply text-red-600; }
```

## Error Handling

The component includes comprehensive error handling:

```typescript
// Error boundaries for component stability
<ErrorBoundary fallback={<AgentManagementError />}>
  <AgentManagementDashboard {...props} />
</ErrorBoundary>

// Graceful degradation for missing data
const agents = data?.agents || [];
const metrics = data?.metrics || [];
const activities = data?.activities || [];
```

## Performance Considerations

### Optimization Features

1. **Virtual Scrolling**: For large agent lists
2. **Memoization**: React.memo for expensive components
3. **Debounced Updates**: Prevent excessive re-renders
4. **Lazy Loading**: Load data on demand

### Memory Management

```typescript
// Cleanup intervals and subscriptions
useEffect(() => {
  const interval = setInterval(updateMetrics, 5000);
  return () => clearInterval(interval);
}, []);

// Limit activity history
const [activities, setActivities] = useState<AgentActivity[]>([]);
const addActivity = (activity: AgentActivity) => {
  setActivities(prev => [activity, ...prev].slice(0, 100));
};
```

## Testing

### Component Testing

```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import { AgentManagementDashboard } from './AgentManagementDashboard';

test('renders agent cards correctly', () => {
  const agents = [mockAgent];
  render(<AgentManagementDashboard {...mockProps} agents={agents} />);

  expect(screen.getByText(mockAgent.name)).toBeInTheDocument();
  expect(screen.getByText(mockAgent.description)).toBeInTheDocument();
});

test('handles agent actions', async () => {
  const onAgentAction = jest.fn();
  render(<AgentManagementDashboard {...mockProps} onAgentAction={onAgentAction} />);

  fireEvent.click(screen.getByText('Start'));
  expect(onAgentAction).toHaveBeenCalledWith('agent-001', 'start');
});
```

## Accessibility

The component follows WCAG 2.1 guidelines:

- **Keyboard Navigation**: Full keyboard support
- **Screen Reader Support**: ARIA labels and roles
- **Color Contrast**: Sufficient contrast ratios
- **Focus Management**: Visible focus indicators

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Dependencies

### Required Dependencies

```json
{
  "react": "^18.0.0",
  "react-dom": "^18.0.0",
  "lucide-react": "^0.263.1",
  "tailwindcss": "^3.3.0",
  "radix-ui": "^1.0.0"
}
```

### Optional Dependencies

```json
{
  "recharts": "^2.8.0",  // For advanced charts
  "framer-motion": "^10.12.0",  // For animations
  "react-query": "^3.39.0"  // For data fetching
}
```

## Contributing

1. Follow the established component patterns
2. Maintain TypeScript type safety
3. Add comprehensive tests for new features
4. Update documentation for API changes
5. Ensure accessibility compliance

## License

This component is part of the DuckBot project and follows the same license terms.