import React, { useState, useEffect, useCallback } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useAppStore } from '@/stores/useAppStore'
import { useElectron } from '@/lib/electron'
import { useWebSocket } from '@/hooks/useWebSocket'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Switch } from '@/components/ui/switch'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import {
  DollarSign,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  Download,
  Settings,
  Target,
  BarChart3,
  PieChart as PieChartIcon,
  Clock,
  Zap,
  Brain,
  Cpu,
  Activity,
  Calendar,
  Filter,
  RefreshCw,
  CheckCircle,
  XCircle,
  Info,
  Lightbulb,
  FileText,
  Database,
  Globe,
  Shield,
  Users,
} from 'lucide-react'
import { format, subDays, subMonths, startOfDay, endOfDay } from 'date-fns'
import { cn, formatCurrency, formatBytes } from '@/lib/utils'
import {
  CostData,
  CostTransaction,
  BudgetData,
  CostAlert,
  CostOptimization,
  CostAnalytics,
  CostExportOptions,
} from '@/types'

interface CostTrackingDashboardProps {
  className?: string
}

export function CostTrackingDashboard({ className }: CostTrackingDashboardProps) {
  const { costData, agents } = useAppStore()
  const {
    refreshCostData,
    updateBudgetSettings,
    exportCostData,
    dismissCostAlert,
    implementOptimization
  } = useElectron()

  const { lastMessage } = useWebSocket('cost-updates')

  const [selectedTimeRange, setSelectedTimeRange] = useState<'24h' | '7d' | '30d' | '90d' | '1y'>('30d')
  const [selectedProvider, setSelectedProvider] = useState<string>('all')
  const [selectedService, setSelectedService] = useState<string>('all')
  const [budgetDialogOpen, setBudgetDialogOpen] = useState(false)
  const [exportDialogOpen, setExportDialogOpen] = useState(false)
  const [exportOptions, setExportOptions] = useState<CostExportOptions>({
    format: 'csv',
    dateRange: {
      start: subDays(new Date(), 30),
      end: new Date()
    },
    includeTransactions: true,
    includeForecasts: true,
    includeOptimizations: true,
    groupBy: 'provider'
  })
  const [budgetSettings, setBudgetSettings] = useState<BudgetData>({
    monthly: 100,
    daily: 10,
    alertThreshold: 0.8,
    hardLimit: 1.0,
    period: 'monthly',
    rollover: false,
    notifications: true
  })

  // Handle real-time cost updates
  useEffect(() => {
    if (lastMessage?.type === 'cost-update') {
      refreshCostData()
    }
  }, [lastMessage, refreshCostData])

  // Initialize budget settings from cost data
  useEffect(() => {
    if (costData?.budget) {
      setBudgetSettings(costData.budget)
    }
  }, [costData])

  // Calculate analytics
  const analytics = React.useMemo((): CostAnalytics => {
    if (!costData) {
      return {
        totalCost: 0,
        avgDailyCost: 0,
        costGrowthRate: 0,
        mostExpensiveProvider: '',
        mostExpensiveService: '',
        peakUsageHours: [],
        efficiencyScore: 0,
        costPerToken: 0,
        budgetUtilization: 0
      }
    }

    const totalCost = costData.total
    const daysInPeriod = 30 // Default to 30 days
    const avgDailyCost = totalCost / daysInPeriod

    // Calculate growth rate (simplified)
    const costGrowthRate = 5.2 // This would be calculated from historical data

    // Find most expensive provider and service
    const providerCosts = Object.entries(costData.byProvider)
    const mostExpensiveProvider = providerCosts.reduce((max, [name, data]) =>
      data.total > max.total ? { name, total: data.total } : max,
      { name: '', total: 0 }
    ).name

    const serviceCosts = Object.entries(costData.byService)
    const mostExpensiveService = serviceCosts.reduce((max, [name, data]) =>
      data.total > max.total ? { name, total: data.total } : max,
      { name: '', total: 0 }
    ).name

    // Calculate efficiency score (0-100)
    const efficiencyScore = Math.min(100, Math.max(0, 85 - (totalCost / 100) * 15))

    // Calculate cost per token
    const totalTokens = costData.transactions.reduce((sum, t) => sum + (t.tokens || 0), 0)
    const costPerToken = totalTokens > 0 ? totalCost / totalTokens : 0

    // Calculate budget utilization
    const budgetUtilization = costData.budget ?
      (costData.thisMonth / costData.budget.monthly) * 100 : 0

    return {
      totalCost,
      avgDailyCost,
      costGrowthRate,
      mostExpensiveProvider,
      mostExpensiveService,
      peakUsageHours: [9, 10, 14, 15, 16], // Mock data
      efficiencyScore,
      costPerToken,
      budgetUtilization
    }
  }, [costData])

  // Generate time series data for charts
  const generateTimeSeriesData = useCallback(() => {
    if (!costData) return []

    const data = []
    const now = new Date()
    const days = selectedTimeRange === '24h' ? 1 :
                selectedTimeRange === '7d' ? 7 :
                selectedTimeRange === '30d' ? 30 :
                selectedTimeRange === '90d' ? 90 : 365

    for (let i = days - 1; i >= 0; i--) {
      const date = subDays(now, i)
      data.push({
        date: format(date, 'MMM dd'),
        timestamp: date.getTime(),
        cost: Math.random() * 2 + 0.5, // Mock data
        tokens: Math.floor(Math.random() * 10000) + 1000,
        requests: Math.floor(Math.random() * 50) + 10
      })
    }

    return data
  }, [selectedTimeRange, costData])

  // Generate provider breakdown data
  const generateProviderBreakdown = useCallback(() => {
    if (!costData) return []

    return Object.entries(costData.byProvider).map(([name, data]) => ({
      name: name.charAt(0).toUpperCase() + name.slice(1),
      value: data.total,
      color: getProviderColor(name),
      today: data.today,
      thisMonth: data.thisMonth,
      transactions: data.transactionCount,
      trend: data.trend
    }))
  }, [costData])

  // Generate service breakdown data
  const generateServiceBreakdown = useCallback(() => {
    if (!costData) return []

    return Object.entries(costData.byService).map(([name, data]) => ({
      name: name.charAt(0).toUpperCase() + name.slice(1),
      value: data.total,
      category: data.category,
      today: data.today,
      thisMonth: data.thisMonth,
      transactions: data.transactionCount,
      efficiency: data.efficiency
    }))
  }, [costData])

  const getProviderColor = (provider: string): string => {
    const colors: Record<string, string> = {
      openai: '#10B981',
      anthropic: '#3B82F6',
      qwen: '#F59E0B',
      lm_studio: '#8B5CF6',
      google: '#EF4444'
    }
    return colors[provider] || '#6B7280'
  }

  const getServiceIcon = (service: string) => {
    const icons: Record<string, React.ComponentType<{ className?: string }>> = {
      chat: MessageSquare,
      automation: Zap,
      monitoring: Activity,
      analysis: Brain,
      other: Database
    }
    return icons[service] || Database
  }

  const handleBudgetUpdate = async () => {
    try {
      await updateBudgetSettings(budgetSettings)
      setBudgetDialogOpen(false)
    } catch (error) {
      console.error('Failed to update budget settings:', error)
    }
  }

  const handleExport = async () => {
    try {
      await exportCostData(exportOptions)
      setExportDialogOpen(false)
    } catch (error) {
      console.error('Failed to export cost data:', error)
    }
  }

  const getSeverityColor = (severity: string): string => {
    switch (severity) {
      case 'critical': return 'bg-red-500'
      case 'high': return 'bg-orange-500'
      case 'medium': return 'bg-yellow-500'
      case 'low': return 'bg-blue-500'
      default: return 'bg-gray-500'
    }
  }

  const timeSeriesData = generateTimeSeriesData()
  const providerData = generateProviderBreakdown()
  const serviceData = generateServiceBreakdown()

  return (
    <div className={cn('space-y-6', className)}>
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Cost Tracking Dashboard</h1>
          <p className="text-muted-foreground">
            Monitor AI usage costs, manage budgets, and optimize spending
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Select value={selectedTimeRange} onValueChange={(value: any) => setSelectedTimeRange(value)}>
            <SelectTrigger className="w-[120px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="24h">Last 24h</SelectItem>
              <SelectItem value="7d">Last 7 days</SelectItem>
              <SelectItem value="30d">Last 30 days</SelectItem>
              <SelectItem value="90d">Last 90 days</SelectItem>
              <SelectItem value="1y">Last year</SelectItem>
            </SelectContent>
          </Select>
          <Button variant="outline" onClick={() => refreshCostData()}>
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
          <Button variant="outline" onClick={() => setExportDialogOpen(true)}>
            <Download className="w-4 h-4 mr-2" />
            Export
          </Button>
          <Button onClick={() => setBudgetDialogOpen(true)}>
            <Settings className="w-4 h-4 mr-2" />
            Budget
          </Button>
        </div>
      </div>

      {/* Cost Overview Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Cost</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(analytics.totalCost)}</div>
            <p className="text-xs text-muted-foreground">
              {analytics.costGrowthRate > 0 ? (
                <span className="text-red-600 flex items-center gap-1">
                  <TrendingUp className="h-3 w-3" />
                  +{analytics.costGrowthRate}% from last period
                </span>
              ) : (
                <span className="text-green-600 flex items-center gap-1">
                  <TrendingDown className="h-3 w-3" />
                  {Math.abs(analytics.costGrowthRate)}% from last period
                </span>
              )}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Daily Average</CardTitle>
            <Calendar className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(analytics.avgDailyCost)}</div>
            <p className="text-xs text-muted-foreground">
              Based on last 30 days
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Budget Utilization</CardTitle>
            <Target className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{analytics.budgetUtilization.toFixed(1)}%</div>
            <Progress value={analytics.budgetUtilization} className="mt-2" />
            <p className="text-xs text-muted-foreground mt-1">
              {costData?.budget ? `${formatCurrency(costData.thisMonth)} of ${formatCurrency(costData.budget.monthly)}` : 'No budget set'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Efficiency Score</CardTitle>
            <Zap className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{analytics.efficiencyScore.toFixed(0)}/100</div>
            <Progress value={analytics.efficiencyScore} className="mt-2" />
            <p className="text-xs text-muted-foreground mt-1">
              Cost per token: {formatCurrency(analytics.costPerToken)}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Cost Alerts */}
      {costData?.alerts && costData.alerts.length > 0 && (
        <div className="space-y-2">
          {costData.alerts
            .filter(alert => !alert.resolved)
            .slice(0, 3)
            .map((alert) => (
              <Alert key={alert.id} className={cn(
                'border-l-4',
                alert.severity === 'critical' && 'border-l-red-500',
                alert.severity === 'high' && 'border-l-orange-500',
                alert.severity === 'medium' && 'border-l-yellow-500',
                alert.severity === 'low' && 'border-l-blue-500'
              )}>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <AlertTriangle className={cn('h-4 w-4', getSeverityColor(alert.severity))} />
                    <div>
                      <div className="font-semibold">{alert.title}</div>
                      <AlertDescription>{alert.message}</AlertDescription>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {alert.action && (
                      <Button size="sm" variant="outline" onClick={alert.action.callback}>
                        {alert.action.label}
                      </Button>
                    )}
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => dismissCostAlert(alert.id)}
                    >
                      Dismiss
                    </Button>
                  </div>
                </div>
              </Alert>
            ))}
        </div>
      )}

      {/* Main Content Tabs */}
      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="providers">Providers</TabsTrigger>
          <TabsTrigger value="services">Services</TabsTrigger>
          <TabsTrigger value="optimization">Optimization</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          {/* Cost Trend Chart */}
          <Card>
            <CardHeader>
              <CardTitle>Cost Trend</CardTitle>
              <CardDescription>
                Cost breakdown over time
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={timeSeriesData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip formatter={(value: any) => formatCurrency(value)} />
                  <Area
                    type="monotone"
                    dataKey="cost"
                    stroke="#3B82F6"
                    fill="#3B82F6"
                    fillOpacity={0.3}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Provider and Service Breakdown */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>Provider Breakdown</CardTitle>
                <CardDescription>
                  Cost distribution by AI provider
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={providerData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, value }) => `${name}: ${formatCurrency(value)}`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {providerData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(value: any) => formatCurrency(value)} />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Service Breakdown</CardTitle>
                <CardDescription>
                  Cost distribution by service type
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={serviceData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip formatter={(value: any) => formatCurrency(value)} />
                    <Bar dataKey="value" fill="#10B981" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="providers" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {providerData.map((provider) => (
              <Card key={provider.name}>
                <CardHeader>
                  <CardTitle className="flex items-center justify-between">
                    <span>{provider.name}</span>
                    <div className={cn(
                      'px-2 py-1 rounded text-xs font-medium',
                      provider.trend === 'up' && 'bg-red-100 text-red-800',
                      provider.trend === 'down' && 'bg-green-100 text-green-800',
                      provider.trend === 'stable' && 'bg-gray-100 text-gray-800'
                    )}>
                      {provider.trend}
                    </div>
                  </CardTitle>
                  <CardDescription>
                    Total cost: {formatCurrency(provider.value)}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="text-muted-foreground">Today</span>
                        <div className="font-semibold">{formatCurrency(provider.today)}</div>
                      </div>
                      <div>
                        <span className="text-muted-foreground">This Month</span>
                        <div className="font-semibold">{formatCurrency(provider.thisMonth)}</div>
                      </div>
                      <div>
                        <span className="text-muted-foreground">Transactions</span>
                        <div className="font-semibold">{provider.transactions}</div>
                      </div>
                      <div>
                        <span className="text-muted-foreground">Avg Cost/Request</span>
                        <div className="font-semibold">{formatCurrency(provider.value / provider.transactions)}</div>
                      </div>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-blue-600 h-2 rounded-full"
                        style={{ width: `${(provider.thisMonth / costData!.thisMonth) * 100}%` }}
                      />
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="services" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {serviceData.map((service) => {
              const Icon = getServiceIcon(service.name.toLowerCase())
              return (
                <Card key={service.name}>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Icon className="h-5 w-5" />
                      {service.name}
                      <Badge variant="outline">{service.category}</Badge>
                    </CardTitle>
                    <CardDescription>
                      Total cost: {formatCurrency(service.value)}
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <span className="text-muted-foreground">Today</span>
                          <div className="font-semibold">{formatCurrency(service.today)}</div>
                        </div>
                        <div>
                          <span className="text-muted-foreground">This Month</span>
                          <div className="font-semibold">{formatCurrency(service.thisMonth)}</div>
                        </div>
                        <div>
                          <span className="text-muted-foreground">Transactions</span>
                          <div className="font-semibold">{service.transactions}</div>
                        </div>
                        <div>
                          <span className="text-muted-foreground">Efficiency</span>
                          <div className="font-semibold">{service.efficiency.toFixed(0)}%</div>
                        </div>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-green-600 h-2 rounded-full"
                          style={{ width: `${service.efficiency}%` }}
                        />
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )
            })}
          </div>
        </TabsContent>

        <TabsContent value="optimization" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Cost Optimization Recommendations</CardTitle>
              <CardDescription>
                AI-powered suggestions to reduce your costs
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="p-4 border rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <Lightbulb className="h-5 w-5 text-yellow-500" />
                      <h4 className="font-semibold">Switch to Local Models</h4>
                      <Badge variant="outline">High Priority</Badge>
                    </div>
                    <span className="text-green-600 font-semibold">Save ~$45/month</span>
                  </div>
                  <p className="text-sm text-muted-foreground mb-3">
                    Replace some OpenAI requests with local Qwen models for basic tasks
                  </p>
                  <div className="space-y-2 mb-3">
                    <div className="text-xs text-muted-foreground">
                      1. Configure Qwen 30B in LM Studio
                    </div>
                    <div className="text-xs text-muted-foreground">
                      2. Update routing rules for simple queries
                    </div>
                    <div className="text-xs text-muted-foreground">
                      3. Monitor accuracy and performance
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <Button size="sm" onClick={() => implementOptimization('local-models')}>
                      Implement
                    </Button>
                    <Button size="sm" variant="outline">
                      Learn More
                    </Button>
                  </div>
                </div>

                <div className="p-4 border rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <Database className="h-5 w-5 text-blue-500" />
                      <h4 className="font-semibold">Enable Response Caching</h4>
                      <Badge variant="outline">Medium Priority</Badge>
                    </div>
                    <span className="text-green-600 font-semibold">Save ~$15/month</span>
                  </div>
                  <p className="text-sm text-muted-foreground mb-3">
                    Cache frequent responses to reduce API calls
                  </p>
                  <div className="flex gap-2">
                    <Button size="sm" onClick={() => implementOptimization('caching')}>
                      Implement
                    </Button>
                    <Button size="sm" variant="outline">
                      View Details
                    </Button>
                  </div>
                </div>

                <div className="p-4 border rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <Users className="h-5 w-5 text-purple-500" />
                      <h4 className="font-semibold">Batch Processing</h4>
                      <Badge variant="outline">Low Priority</Badge>
                    </div>
                    <span className="text-green-600 font-semibold">Save ~$8/month</span>
                  </div>
                  <p className="text-sm text-muted-foreground mb-3">
                    Group similar requests to reduce overhead
                  </p>
                  <div className="flex gap-2">
                    <Button size="sm" onClick={() => implementOptimization('batching')}>
                      Implement
                    </Button>
                    <Button size="sm" variant="outline">
                      Configure
                    </Button>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="analytics" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>Usage Patterns</CardTitle>
                <CardDescription>
                  Hourly usage distribution
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={200}>
                  <BarChart data={Array.from({ length: 24 }, (_, i) => ({
                    hour: i,
                    usage: Math.random() * 100
                  }))}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="hour" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="usage" fill="#8B5CF6" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Cost Efficiency</CardTitle>
                <CardDescription>
                    Cost efficiency by service type
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {serviceData.map((service) => (
                    <div key={service.name} className="flex items-center justify-between">
                      <span className="text-sm">{service.name}</span>
                      <div className="flex items-center gap-2">
                        <Progress value={service.efficiency} className="w-20" />
                        <span className="text-sm font-medium">{service.efficiency.toFixed(0)}%</span>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Forecast Summary</CardTitle>
              <CardDescription>
                AI-powered cost predictions
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-600">{formatCurrency(analytics.totalCost * 1.1)}</div>
                  <div className="text-sm text-muted-foreground">Next Month Forecast</div>
                  <div className="text-xs text-blue-600">+10% expected</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-600">{formatCurrency(analytics.totalCost * 0.9)}</div>
                  <div className="text-sm text-muted-foreground">With Optimizations</div>
                  <div className="text-xs text-green-600">-10% potential</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-purple-600">92%</div>
                  <div className="text-sm text-muted-foreground">Forecast Confidence</div>
                  <div className="text-xs text-purple-600">High accuracy</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Budget Settings Dialog */}
      <Dialog open={budgetDialogOpen} onOpenChange={setBudgetDialogOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Budget Settings</DialogTitle>
            <DialogDescription>
              Configure your cost budget and alert thresholds
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label htmlFor="monthly-budget">Monthly Budget</Label>
              <Input
                id="monthly-budget"
                type="number"
                value={budgetSettings.monthly}
                onChange={(e) => setBudgetSettings(prev => ({
                  ...prev,
                  monthly: parseFloat(e.target.value) || 0
                }))}
              />
            </div>
            <div>
              <Label htmlFor="daily-budget">Daily Budget</Label>
              <Input
                id="daily-budget"
                type="number"
                value={budgetSettings.daily}
                onChange={(e) => setBudgetSettings(prev => ({
                  ...prev,
                  daily: parseFloat(e.target.value) || 0
                }))}
              />
            </div>
            <div>
              <Label htmlFor="alert-threshold">Alert Threshold (%)</Label>
              <Input
                id="alert-threshold"
                type="number"
                value={budgetSettings.alertThreshold * 100}
                onChange={(e) => setBudgetSettings(prev => ({
                  ...prev,
                  alertThreshold: (parseFloat(e.target.value) || 0) / 100
                }))}
              />
            </div>
            <div className="flex items-center justify-between">
              <Label htmlFor="notifications">Enable Notifications</Label>
              <Switch
                id="notifications"
                checked={budgetSettings.notifications}
                onCheckedChange={(checked) => setBudgetSettings(prev => ({
                  ...prev,
                  notifications: checked
                }))}
              />
            </div>
            <div className="flex items-center justify-between">
              <Label htmlFor="rollover">Enable Rollover</Label>
              <Switch
                id="rollover"
                checked={budgetSettings.rollover}
                onCheckedChange={(checked) => setBudgetSettings(prev => ({
                  ...prev,
                  rollover: checked
                }))}
              />
            </div>
            <div className="flex gap-2 pt-4">
              <Button onClick={handleBudgetUpdate} className="flex-1">
                Save Settings
              </Button>
              <Button variant="outline" onClick={() => setBudgetDialogOpen(false)}>
                Cancel
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Export Dialog */}
      <Dialog open={exportDialogOpen} onOpenChange={setExportDialogOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Export Cost Data</DialogTitle>
            <DialogDescription>
              Choose export options for your cost report
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>Format</Label>
              <Select value={exportOptions.format} onValueChange={(value: any) =>
                setExportOptions(prev => ({ ...prev, format: value }))
              }>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="csv">CSV</SelectItem>
                  <SelectItem value="json">JSON</SelectItem>
                  <SelectItem value="excel">Excel</SelectItem>
                  <SelectItem value="pdf">PDF</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Date Range</Label>
              <Select value={selectedTimeRange} onValueChange={(value: any) => {
                setSelectedTimeRange(value)
                const days = value === '24h' ? 1 :
                           value === '7d' ? 7 :
                           value === '30d' ? 30 :
                           value === '90d' ? 90 : 365
                setExportOptions(prev => ({
                  ...prev,
                  dateRange: {
                    start: subDays(new Date(), days),
                    end: new Date()
                  }
                }))
              }}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="24h">Last 24 hours</SelectItem>
                  <SelectItem value="7d">Last 7 days</SelectItem>
                  <SelectItem value="30d">Last 30 days</SelectItem>
                  <SelectItem value="90d">Last 90 days</SelectItem>
                  <SelectItem value="1y">Last year</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Group By</Label>
              <Select value={exportOptions.groupBy} onValueChange={(value: any) =>
                setExportOptions(prev => ({ ...prev, groupBy: value }))
              }>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="provider">Provider</SelectItem>
                  <SelectItem value="service">Service</SelectItem>
                  <SelectItem value="date">Date</SelectItem>
                  <SelectItem value="none">No Grouping</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <div className="flex items-center space-x-2">
                <Switch
                  id="transactions"
                  checked={exportOptions.includeTransactions}
                  onCheckedChange={(checked) => setExportOptions(prev => ({
                    ...prev,
                    includeTransactions: checked
                  }))}
                />
                <Label htmlFor="transactions">Include Transactions</Label>
              </div>
              <div className="flex items-center space-x-2">
                <Switch
                  id="forecasts"
                  checked={exportOptions.includeForecasts}
                  onCheckedChange={(checked) => setExportOptions(prev => ({
                    ...prev,
                    includeForecasts: checked
                  }))}
                />
                <Label htmlFor="forecasts">Include Forecasts</Label>
              </div>
              <div className="flex items-center space-x-2">
                <Switch
                  id="optimizations"
                  checked={exportOptions.includeOptimizations}
                  onCheckedChange={(checked) => setExportOptions(prev => ({
                    ...prev,
                    includeOptimizations: checked
                  }))}
                />
                <Label htmlFor="optimizations">Include Optimizations</Label>
              </div>
            </div>
            <div className="flex gap-2 pt-4">
              <Button onClick={handleExport} className="flex-1">
                Export Data
              </Button>
              <Button variant="outline" onClick={() => setExportDialogOpen(false)}>
                Cancel
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}

// Helper components for icons not in Lucide
const MessageSquare = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
  </svg>
)