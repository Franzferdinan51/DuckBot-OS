import { useEffect } from 'react'
import { useAppStore } from '@stores/useAppStore'
import { ServiceStatus, SystemMetrics, Agent, CostData, Alert, BudgetData, CostExportOptions } from '@types'

export function initElectronListeners() {
  const {
    updateService,
    updateMetrics,
    updateAgent,
    addAlert,
    setError
  } = useAppStore.getState()

  if (!window.electronAPI) {
    console.warn('Electron API not available')
    return () => {}
  }

  const cleanupServiceUpdate = window.electronAPI.onServiceUpdate((event, service: ServiceStatus) => {
    updateService(service)

    // Add alerts for important service changes
    if (service.status === 'error') {
      addAlert({
        type: 'error',
        title: 'Service Error',
        message: `${service.name} encountered an error: ${service.lastError}`
      })
    } else if (service.status === 'running') {
      addAlert({
        type: 'success',
        title: 'Service Started',
        message: `${service.name} is now running`
      })
    }
  })

  const cleanupMetricsUpdate = window.electronAPI.onSystemMetricsUpdate((event, metrics: SystemMetrics) => {
    updateMetrics(metrics)

    // Check for high resource usage
    if (metrics.cpu.usage > 90) {
      addAlert({
        type: 'warning',
        title: 'High CPU Usage',
        message: `CPU usage is at ${metrics.cpu.usage.toFixed(1)}%`
      })
    }

    if (metrics.memory.percentage > 90) {
      addAlert({
        type: 'warning',
        title: 'High Memory Usage',
        message: `Memory usage is at ${metrics.memory.percentage.toFixed(1)}%`
      })
    }
  })

  const cleanupAgentUpdate = window.electronAPI.onAgentUpdate((event, data: any) => {
    updateAgent(data.agent)

    if (data.action === 'error') {
      addAlert({
        type: 'error',
        title: 'Agent Error',
        message: `Agent ${data.agent.name} encountered an error: ${data.error}`
      })
    }
  })

  const cleanupLogUpdate = window.electronAPI.onLogUpdate((event, log) => {
    // Handle critical log messages
    if (log.type === 'error') {
      addAlert({
        type: 'error',
        title: 'Service Log Error',
        message: `${log.service}: ${log.data}`
      })
    }
  })

  const cleanupCostUpdate = window.electronAPI.onCostUpdate((event, costData: CostData) => {
    const store = useAppStore.getState()
    store.updateCostData(costData)

    // Check for high costs
    if (costData.today > 10) {
      addAlert({
        type: 'warning',
        title: 'High Daily Cost',
        message: `Today's API costs: $${costData.today.toFixed(2)}`
      })
    }
  })

  return () => {
    cleanupServiceUpdate()
    cleanupMetricsUpdate()
    cleanupAgentUpdate()
    cleanupLogUpdate()
    cleanupCostUpdate()
  }
}

// Hook for Electron API
export function useElectron() {
  const {
    services,
    loading,
    setError,
    addAlert,
    updateService,
    updateMetrics,
    updateCostData,
    updateAgents,
    updateConversations,
    setActiveConversation,
    addMessage
  } = useAppStore()

  const startService = async (serviceName: string) => {
    try {
      const result = await window.electronAPI.startService(serviceName)
      if (result.success) {
        updateService({ ...services[serviceName], status: 'starting' })
        addAlert({
          type: 'info',
          title: 'Starting Service',
          message: `${serviceName} is starting...`
        })
      }
      return result
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to start service'
      setError(errorMessage)
      addAlert({
        type: 'error',
        title: 'Service Start Failed',
        message: errorMessage
      })
      throw error
    }
  }

  const stopService = async (serviceName: string) => {
    try {
      const result = await window.electronAPI.stopService(serviceName)
      if (result.success) {
        updateService({ ...services[serviceName], status: 'stopping' })
        addAlert({
          type: 'info',
          title: 'Stopping Service',
          message: `${serviceName} is stopping...`
        })
      }
      return result
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to stop service'
      setError(errorMessage)
      addAlert({
        type: 'error',
        title: 'Service Stop Failed',
        message: errorMessage
      })
      throw error
    }
  }

  const restartService = async (serviceName: string) => {
    try {
      addAlert({
        type: 'info',
        title: 'Restarting Service',
        message: `${serviceName} is restarting...`
      })
      const result = await window.electronAPI.restartService(serviceName)
      return result
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to restart service'
      setError(errorMessage)
      addAlert({
        type: 'error',
        title: 'Service Restart Failed',
        message: errorMessage
      })
      throw error
    }
  }

  const refreshSystemMetrics = async () => {
    try {
      const metrics = await window.electronAPI.getSystemMetrics()
      updateMetrics(metrics)
      return metrics
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to get metrics'
      setError(errorMessage)
      throw error
    }
  }

  const refreshCostData = async () => {
    try {
      const costData = await window.electronAPI.getCostData()
      updateCostData(costData)
      return costData
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to get cost data'
      setError(errorMessage)
      throw error
    }
  }

  const executeAutomation = async (command: string, params?: any) => {
    try {
      const result = await window.electronAPI.executeAutomation(command, params)
      addAlert({
        type: 'success',
        title: 'Automation Executed',
        message: `Command "${command}" executed successfully`
      })
      return result
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to execute automation'
      setError(errorMessage)
      addAlert({
        type: 'error',
        title: 'Automation Failed',
        message: errorMessage
      })
      throw error
    }
  }

  const sendMessage = async (message: string, provider?: string) => {
    try {
      const response = await window.electronAPI.sendMessage(message, provider)
      if (activeConversation) {
        addMessage(response)
      }
      return response
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to send message'
      setError(errorMessage)
      throw error
    }
  }

  const controlAgent = async (agentId: string, action: string, params?: any) => {
    try {
      const result = await window.electronAPI.controlAgent(agentId, action, params)
      addAlert({
        type: 'info',
        title: 'Agent Action',
        message: `Agent ${agentId} ${action} action executed`
      })
      return result
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to control agent'
      setError(errorMessage)
      addAlert({
        type: 'error',
        title: 'Agent Control Failed',
        message: errorMessage
      })
      throw error
    }
  }

  const updateConfig = async (key: string, value: any) => {
    try {
      await window.electronAPI.updateConfig(key, value)
      addAlert({
        type: 'success',
        title: 'Configuration Updated',
        message: `${key} updated successfully`
      })
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to update config'
      setError(errorMessage)
      addAlert({
        type: 'error',
        title: 'Configuration Update Failed',
        message: errorMessage
      })
      throw error
    }
  }

  const showNotification = (title: string, body: string, silent = false) => {
    window.electronAPI.showNotification({ title, body, silent })
  }

  const updateBudgetSettings = async (budget: BudgetData) => {
    try {
      await window.electronAPI.updateBudgetSettings(budget)
      addAlert({
        type: 'success',
        title: 'Budget Updated',
        message: 'Budget settings have been updated successfully'
      })
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to update budget'
      setError(errorMessage)
      addAlert({
        type: 'error',
        title: 'Budget Update Failed',
        message: errorMessage
      })
      throw error
    }
  }

  const exportCostData = async (options: CostExportOptions) => {
    try {
      const result = await window.electronAPI.exportCostData(options)
      addAlert({
        type: 'success',
        title: 'Export Complete',
        message: 'Cost data exported successfully'
      })
      return result
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to export cost data'
      setError(errorMessage)
      addAlert({
        type: 'error',
        title: 'Export Failed',
        message: errorMessage
      })
      throw error
    }
  }

  const dismissCostAlert = async (alertId: string) => {
    try {
      await window.electronAPI.dismissCostAlert(alertId)
      // Update local state to remove the alert
      const store = useAppStore.getState()
      const currentCostData = store.costData
      if (currentCostData?.alerts) {
        store.updateCostData({
          ...currentCostData,
          alerts: currentCostData.alerts.map(alert =>
            alert.id === alertId ? { ...alert, resolved: true } : alert
          )
        })
      }
    } catch (error) {
      console.error('Failed to dismiss cost alert:', error)
    }
  }

  const implementOptimization = async (optimizationId: string) => {
    try {
      const result = await window.electronAPI.implementOptimization(optimizationId)
      addAlert({
        type: 'success',
        title: 'Optimization Implemented',
        message: 'Cost optimization has been applied successfully'
      })
      return result
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to implement optimization'
      setError(errorMessage)
      addAlert({
        type: 'error',
        title: 'Optimization Failed',
        message: errorMessage
      })
      throw error
    }
  }

  return {
    startService,
    stopService,
    restartService,
    refreshSystemMetrics,
    refreshCostData,
    executeAutomation,
    sendMessage,
    controlAgent,
    updateConfig,
    showNotification,
    updateBudgetSettings,
    exportCostData,
    dismissCostAlert,
    implementOptimization,
    loading
  }
}