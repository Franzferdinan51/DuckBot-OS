import React from 'react'
import { useAppStore } from '@stores/useAppStore'
import { Activity, CheckCircle, Square, AlertTriangle } from 'lucide-react'

interface ServiceStatus {
  name: string
  status: 'running' | 'stopped' | 'error' | 'starting' | 'stopping'
  description?: string
  pid?: number
  port?: number
  uptime?: number
  cpu?: number
  memory?: number
  lastError?: string
}

export const ServiceGrid = () => {
  const { services } = useAppStore()

  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running': return 'bg-green-100 text-green-800'
      case 'stopped': return 'bg-gray-100 text-gray-800'
      case 'error': return 'bg-red-100 text-red-800'
      case 'starting': return 'bg-yellow-100 text-yellow-800'
      case 'stopping': return 'bg-yellow-100 text-yellow-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running': return <CheckCircle className="w-4 h-4 text-green-500" />
      case 'error': return <AlertTriangle className="w-4 h-4 text-red-500" />
      default: return <Activity className="w-4 h-4 text-gray-500" />
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-foreground">Services</h2>
          <p className="text-muted-foreground">Manage and monitor DuckBot ecosystem services</p>
        </div>
      </div>

      <div className="grid gap-4">
        {Object.entries(services).map(([name, service]) => (
          <div key={name} className="bg-surface border border-border rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                {getStatusIcon(service.status)}
                <div>
                  <h3 className="text-lg font-semibold capitalize">
                    {name.replace('_', ' ')}
                  </h3>
                  <p className="text-sm text-muted-foreground">
                    {service.description || `${name.replace('_', ' ')} service`}
                  </p>
                </div>
              </div>
              <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(service.status)}`}>
                {service.status}
              </span>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <span className="text-muted-foreground">CPU:</span>
                <span className="ml-1 font-medium">
                  {service.cpu ? `${service.cpu.toFixed(1)}%` : 'N/A'}
                </span>
              </div>
              <div>
                <span className="text-muted-foreground">Memory:</span>
                <span className="ml-1 font-medium">
                  {service.memory ? formatBytes(service.memory) : 'N/A'}
                </span>
              </div>
              {service.port && (
                <div>
                  <span className="text-muted-foreground">Port:</span>
                  <span className="ml-1 font-medium">{service.port}</span>
                </div>
              )}
              {service.pid && (
                <div>
                  <span className="text-muted-foreground">PID:</span>
                  <span className="ml-1 font-medium">{service.pid}</span>
                </div>
              )}
            </div>

            {service.lastError && (
              <div className="mt-3 p-3 bg-red-50 dark:bg-red-900/20 rounded border border-red-200 dark:border-red-800">
                <div className="flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-red-500" />
                  <span className="text-sm text-red-600 dark:text-red-400">
                    {service.lastError}
                  </span>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}