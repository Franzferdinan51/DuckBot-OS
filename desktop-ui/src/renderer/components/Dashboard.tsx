import React from 'react'
import { useAppStore } from '@stores/useAppStore'
import { Activity, Cpu, MemoryStick, DollarSign } from 'lucide-react'

export function Dashboard() {
  const { services, metrics, costData } = useAppStore()

  const runningServices = Object.values(services).filter(s => s.status === 'running').length
  const totalServices = Object.keys(services).length

  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground">
            Monitor your DuckBot ecosystem status and performance
          </p>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <div className="bg-surface border border-border rounded-lg p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Services</p>
              <p className="text-2xl font-bold">{runningServices}/{totalServices}</p>
              <p className="text-xs text-muted-foreground">Running services</p>
            </div>
            <Activity className="h-8 w-8 text-blue-600" />
          </div>
        </div>

        <div className="bg-surface border border-border rounded-lg p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-muted-foreground">CPU Usage</p>
              <p className="text-2xl font-bold">{metrics ? `${metrics.cpu.usage.toFixed(1)}%` : 'N/A'}</p>
              <p className="text-xs text-muted-foreground">{metrics?.cpu.cores || 0} cores</p>
            </div>
            <Cpu className="h-8 w-8 text-green-600" />
          </div>
        </div>

        <div className="bg-surface border border-border rounded-lg p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Memory</p>
              <p className="text-2xl font-bold">{metrics ? `${metrics.memory.percentage.toFixed(1)}%` : 'N/A'}</p>
              <p className="text-xs text-muted-foreground">{metrics ? formatBytes(metrics.memory.used) : 'N/A'}</p>
            </div>
            <MemoryStick className="h-8 w-8 text-purple-600" />
          </div>
        </div>

        <div className="bg-surface border border-border rounded-lg p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-muted-foreground">API Costs</p>
              <p className="text-2xl font-bold">{costData ? `$${costData.today.toFixed(2)}` : 'N/A'}</p>
              <p className="text-xs text-muted-foreground">Today's usage</p>
            </div>
            <DollarSign className="h-8 w-8 text-orange-600" />
          </div>
        </div>
      </div>

      <div className="bg-surface border border-border rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4">Service Status</h2>
        <div className="space-y-2">
          {Object.entries(services).map(([name, service]) => (
            <div key={name} className="flex items-center justify-between p-3 bg-background rounded-md">
              <span className="font-medium capitalize">{name.replace('_', ' ')}</span>
              <span className={`px-2 py-1 rounded text-xs ${
                service.status === 'running' ? 'bg-green-100 text-green-800' :
                service.status === 'error' ? 'bg-red-100 text-red-800' :
                'bg-gray-100 text-gray-800'
              }`}>
                {service.status}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}