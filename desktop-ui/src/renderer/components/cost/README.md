# Cost Tracking Dashboard Component

The `CostTrackingDashboard` component provides comprehensive AI cost monitoring, budget management, and optimization features for the DuckBot ecosystem.

## Features

### Cost Overview
- **Real-time cost monitoring** with total spending and budget tracking
- **Trend analysis** showing cost growth patterns over time
- **Efficiency scoring** based on cost-per-token and usage patterns
- **Budget utilization** with visual progress indicators

### Cost Breakdown
- **Provider-specific tracking** for OpenAI, Anthropic, Qwen, and local models
- **Service categorization** (Chat, Automation, Monitoring, Analysis)
- **Interactive charts** using Recharts for data visualization
- **Time-range filtering** (24h, 7d, 30d, 90d, 1y)

### Budget Management
- **Configurable budgets** with daily, monthly, and yearly limits
- **Alert thresholds** for proactive cost management
- **Real-time notifications** when approaching budget limits
- **Rollover options** for unused budget amounts

### Cost Optimization
- **AI-powered recommendations** for cost reduction
- **Implementation suggestions** with estimated savings
- **Priority-based optimization** (High, Medium, Low)
- **One-click optimization** implementation

### Analytics & Reporting
- **Usage pattern analysis** with peak hour identification
- **Cost forecasting** with confidence intervals
- **Export functionality** in multiple formats (CSV, JSON, PDF, Excel)
- **Historical trend analysis** with comparative metrics

### Real-time Alerts
- **Budget warnings** when approaching limits
- **Cost spike detection** for unusual spending patterns
- **Inefficiency alerts** for suboptimal resource usage
- **Actionable notifications** with direct response options

## Usage

### Basic Implementation

```tsx
import { CostTrackingDashboard } from '@/components/cost'

function App() {
  return (
    <div className="h-screen">
      <CostTrackingDashboard />
    </div>
  )
}
```

### Integration with App Store

The component integrates with the existing DuckBot state management:

```tsx
import { useAppStore } from '@/stores/useAppStore'
import { useElectron } from '@/lib/electron'

function CostPage() {
  const { costData } = useAppStore()
  const { refreshCostData, updateBudgetSettings } = useElectron()

  return (
    <CostTrackingDashboard />
  )
}
```

## Data Structure

### CostData Interface

```typescript
interface CostData {
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
```

### ProviderCostData

```typescript
interface ProviderCostData {
  name: string
  total: number
  today: number
  thisMonth: number
  thisYear: number
  transactionCount: number
  avgCostPerRequest: number
  avgTokensPerRequest: number
  trend: 'up' | 'down' | 'stable'
  trendPercentage: number
}
```

## WebSocket Integration

The component listens for real-time cost updates:

```typescript
const { lastMessage } = useWebSocket('cost-updates')

useEffect(() => {
  if (lastMessage?.type === 'cost-update') {
    refreshCostData()
  }
}, [lastMessage, refreshCostData])
```

## API Integration

### Available Functions

```typescript
// Refresh cost data
await refreshCostData()

// Update budget settings
await updateBudgetSettings(budgetData)

// Export cost data
await exportCostData(exportOptions)

// Dismiss cost alerts
await dismissCostAlert(alertId)

// Implement optimizations
await implementOptimization(optimizationId)
```

## Configuration

### Budget Settings

```typescript
const budgetSettings: BudgetData = {
  monthly: 200,
  daily: 20,
  alertThreshold: 0.8,
  hardLimit: 1.0,
  period: 'monthly',
  rollover: false,
  notifications: true
}
```

### Export Options

```typescript
const exportOptions: CostExportOptions = {
  format: 'csv',
  dateRange: {
    start: subDays(new Date(), 30),
    end: new Date()
  },
  includeTransactions: true,
  includeForecasts: true,
  includeOptimizations: true,
  groupBy: 'provider'
}
```

## Styling

The component uses Tailwind CSS with a consistent design system:

- **Color-coded indicators** for different states (green, yellow, red)
- **Responsive layout** that works on all screen sizes
- **Dark mode support** with automatic theme switching
- **Accessible design** with proper contrast and focus states

## Performance

### Optimizations

- **Debounced updates** to prevent excessive re-renders
- **Memoized calculations** for analytics data
- **Virtual scrolling** for large transaction lists
- **Efficient chart rendering** with Recharts

### Data Caching

- **Local state management** for frequently accessed data
- **WebSocket updates** for real-time synchronization
- **Lazy loading** for historical data

## Browser Support

- **Chrome/Edge 90+**
- **Firefox 88+**
- **Safari 14+**
- **Electron 12+**

## Dependencies

- **React 18+**
- **Recharts 2.10+**
- **Tailwind CSS 3+**
- **Radix UI components**
- **Lucide React icons**
- **date-fns** for date formatting

## Contributing

1. Follow the established TypeScript patterns
2. Use the existing utility functions for formatting
3. Maintain consistency with the design system
4. Add appropriate TypeScript interfaces for new features
5. Include comprehensive error handling for API calls

## Testing

The component includes:
- **Mock data generation** for development
- **Error boundary protection**
- **Loading state management**
- **Fallback UI components**

## Future Enhancements

- **Machine learning predictions** for cost optimization
- **Multi-currency support**
- **Team/organization cost allocation**
- **Automated cost reduction rules**
- **Integration with billing APIs**
- **Custom dashboard widgets**