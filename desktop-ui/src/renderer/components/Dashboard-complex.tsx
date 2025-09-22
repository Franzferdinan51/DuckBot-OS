import React, { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useAppStore } from '@stores/useAppStore'
import { useElectron } from '@lib/electron'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from './ui/card'
import {
  Badge,
  BadgeProps,
} from './ui/badge'
import { Button } from './ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs'
import {
  Activity,
  Cpu,
  HardDrive,
  MemoryStick,
  Network,
  DollarSign,
  Bot,
  MessageSquare,
  Settings,
  Zap,
  AlertTriangle,
  CheckCircle,
  Clock,
  TrendingUp,
  TrendingDown,
  Play,
  Square,
  RotateCcw,
} from 'lucide-react'
import { StatsCard } from './ui/stats-card'
import { ServiceGrid } from './ui/service-grid'
import { ResourceChart } from './ui/resource-chart'
import { CostChart } from './ui/cost-chart'

export function Dashboard() {
  const { services, metrics, costData, agents } = useAppStore()
  const { refreshSystemMetrics, refreshCostData, startService, stopService, restartService } = useElectron()
  const [selectedTimeRange, setSelectedTimeRange] = useState<'1h' | '24h' | '7d'>('1h')

  // Refresh data periodically
  useEffect(() => {
    const interval = setInterval(() => {
      refreshSystemMetrics()
      refreshCostData()
    }, 30000) // Refresh every 30 seconds

    return () => clearInterval(interval)
  }, [refreshSystemMetrics, refreshCostData])

  // Calculate statistics
  const runningServices = Object.values(services).filter(s => s.status === 'running').length
  const totalServices = Object.keys(services).length
  const activeAgents = agents.filter(a => a.status === 'active').length
  const totalAgents = agents.length

  const getStatusColor = (status: string): BadgeProps['variant'] => {
    switch (status) {
      case 'running': return 'default'
      case 'stopped': return 'secondary'
      case 'error': return 'destructive'
      case 'starting': return 'outline'
      case 'stopping': return 'outline'
      default: return 'secondary'
    }
  }

  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const formatUptime = (uptime: number): string => {
    const now = Date.now()
    const diff = now - uptime
    const hours = Math.floor(diff / (1000 * 60 * 60))
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60))
    return hours > 0 ? `${hours}h ${minutes}m` : `${minutes}m`
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground">
            Monitor your DuckBot ecosystem status and performance
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            onClick={() => refreshSystemMetrics()}
            className="gap-2"
          >
            <RotateCcw className="h-4 w-4" />
            Refresh
          </Button>
          <Button
            onClick={() => {
              Object.entries(services).forEach(([name, service]) => {
                if (service.status !== 'running') {
                  startService(name)
                }
              })
            }}
            className="gap-2"
          >
            <Play className="h-4 w-4" />
            Start All
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatsCard
          title="Services"
          value={`${runningServices}/${totalServices}`}
          description="Running services"
          icon={Activity}
          color="text-blue-600"
        />
        <StatsCard
          title="CPU Usage"
          value={metrics ? `${metrics.cpu.usage.toFixed(1)}%` : 'N/A'}
          description={`${metrics?.cpu.cores || 0} cores`}
          icon={Cpu}
          color="text-green-600"
        />
        <StatsCard
          title="Memory"
          value={metrics ? `${metrics.memory.percentage.toFixed(1)}%` : 'N/A'}
          description={metrics ? formatBytes(metrics.memory.used) : 'N/A'}
          icon={MemoryStick}
          color="text-purple-600"
        />
        <StatsCard
          title="API Costs"
          value={costData ? `$${costData.today.toFixed(2)}` : 'N/A'}
          description="Today's usage"
          icon={DollarSign}
          color="text-orange-600"
        />
      </div>

      {/* Main Content Tabs */}
      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="services">Services</TabsTrigger>
          <TabsTrigger value="agents">Agents</TabsTrigger>
          <TabsTrigger value="performance">Performance</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            {/* System Status */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Activity className="h-5 w-5" />
                  System Status
                </CardTitle>
                <CardDescription>
                  Real-time system health and service status
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">CPU Usage</span>
                    <div className="flex items-center gap-2">
                      <div className="w-24 bg-secondary rounded-full h-2">
                        <div
                          className="bg-blue-600 h-2 rounded-full transition-all"
                          style={{ width: `${metrics?.cpu.usage || 0}%` }}
                        />
                      </div>
                      <span className="text-sm text-muted-foreground">
                        {metrics?.cpu.usage.toFixed(1)}%
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">Memory Usage</span>
                    <div className="flex items-center gap-2">
                      <div className="w-24 bg-secondary rounded-full h-2">
                        <div
                          className="bg-purple-600 h-2 rounded-full transition-all"
                          style={{ width: `${metrics?.memory.percentage || 0}%` }}
                        />
                      </div>
                      <span className="text-sm text-muted-foreground">
                        {metrics?.memory.percentage.toFixed(1)}%
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">Disk Usage</span>
                    <div className="flex items-center gap-2">
                      <div className="w-24 bg-secondary rounded-full h-2">
                        <div
                          className="bg-green-600 h-2 rounded-full transition-all"
                          style={{ width: `${metrics?.disk.percentage || 0}%` }}
                        />
                      </div>
                      <span className="text-sm text-muted-foreground">
                        {metrics?.disk.percentage.toFixed(1)}%
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">Active Agents</span>
                    <span className="text-sm text-muted-foreground">
                      {activeAgents}/{totalAgents}
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Recent Activity */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Clock className="h-5 w-5" />
                  Recent Activity
                </CardTitle>
                <CardDescription>
                  Latest system events and service changes
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {Object.entries(services)
                    .filter(([_, service]) => service.status === 'running')
                    .slice(0, 5)
                    .map(([name, service]) => (
                      <div key={name} className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <CheckCircle className="h-4 w-4 text-green-500" />
                          <span className="text-sm font-medium capitalize">
                            {name.replace('_', ' ')}
                          </span>
                        </div>
                        <div className="flex items-center gap-2">
                          <Badge variant={getStatusColor(service.status)}>
                            {service.status}
                          </Badge>
                          <span className="text-xs text-muted-foreground">
                            {service.uptime ? formatUptime(service.uptime) : 'N/A'}
                          </span>
                        </div>
                      </div>
                    ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Resource Chart */}
          <Card>
            <CardHeader>
              <CardTitle>System Performance</CardTitle>
              <CardDescription>
                CPU and memory usage over time
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ResourceChart timeRange={selectedTimeRange} />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="services">
          <ServiceGrid />
        </TabsContent>

        <TabsContent value="agents">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {agents.map((agent) => (
              <Card key={agent.id} className="agent-card">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="flex items-center gap-2">
                      <Bot className="h-5 w-5" />
                      {agent.name}
                    </CardTitle>
                    <Badge variant={agent.status === 'active' ? 'default' : 'secondary'}>
                      {agent.status}
                    </Badge>
                  </div>
                  <CardDescription>{agent.description}</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div>
                      <span className="text-sm font-medium">Type</span>
                      <p className="text-sm text-muted-foreground capitalize">{agent.type}</p>
                    </div>
                    <div>
                      <span className="text-sm font-medium">Provider</span>
                      <p className="text-sm text-muted-foreground">{agent.provider}</p>
                    </div>
                    {agent.performance && (
                      <div className="grid grid-cols-2 gap-2">
                        <div>
                          <span className="text-sm font-medium">Tasks</span>
                          <p className="text-sm text-muted-foreground">
                            {agent.performance.tasks_completed}
                          </p>
                        </div>
                        <div>
                          <span className="text-sm font-medium">Success Rate</span>
                          <p className="text-sm text-muted-foreground">
                            {(agent.performance.success_rate * 100).toFixed(1)}%
                          </p>
                        </div>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="performance">
          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>API Costs</CardTitle>
                <CardDescription>
                  Cost breakdown by provider and service
                </CardDescription>
              </CardHeader>
              <CardContent>
                <CostChart />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>System Metrics</CardTitle>
                <CardDescription>
                  Detailed system performance metrics
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <span className="text-sm font-medium">CPU Temperature</span>
                      <p className="text-2xl font-bold">
                        {metrics?.cpu.temperature ? `${metrics.cpu.temperature.toFixed(1)}°C` : 'N/A'}
                      </p>
                    </div>
                    <div>
                      <span className="text-sm font-medium">Network Latency</span>
                      <p className="text-2xl font-bold">
                        {metrics?.network.latency ? `${metrics.network.latency.toFixed(1)}ms` : 'N/A'}
                      </p>
                    </div>
                  </div>
                  <div>
                    <span className="text-sm font-medium">Disk Usage</span>
                    <p className="text-lg">
                      {metrics ? `${formatBytes(metrics.disk.used)} / ${formatBytes(metrics.disk.total)}` : 'N/A'}
                    </p>
                  </div>
                  <div>
                    <span className="text-sm font-medium">Memory Available</span>
                    <p className="text-lg">
                      {metrics ? formatBytes(metrics.memory.available) : 'N/A'}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}