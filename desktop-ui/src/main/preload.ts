import { contextBridge, ipcRenderer } from 'electron'

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electronAPI', {
  // Service management
  getSystemStatus: () => ipcRenderer.invoke('get-system-status'),
  startService: (serviceName: string) => ipcRenderer.invoke('start-service', serviceName),
  stopService: (serviceName: string) => ipcRenderer.invoke('stop-service', serviceName),
  restartService: (serviceName: string) => ipcRenderer.invoke('restart-service', serviceName),
  getServiceLogs: (serviceName: string) => ipcRenderer.invoke('get-service-logs', serviceName),
  getSystemMetrics: () => ipcRenderer.invoke('get-system-metrics'),
  getCostData: () => ipcRenderer.invoke('get-cost-data'),

  // AI configuration
  getAIConfig: () => ipcRenderer.invoke('get-ai-config'),
  updateAIConfig: (config: any) => ipcRenderer.invoke('update-ai-config', config),

  // Automation
  executeAutomation: (command: string, params?: any) =>
    ipcRenderer.invoke('execute-automation', command, params),

  // Conversation management
  getConversations: () => ipcRenderer.invoke('get-conversations'),
  sendMessage: (message: string, provider?: string) =>
    ipcRenderer.invoke('send-message', message, provider),

  // Agent management
  getAgents: () => ipcRenderer.invoke('get-agents'),
  controlAgent: (agentId: string, action: string, params?: any) =>
    ipcRenderer.invoke('control-agent', agentId, action, params),

  // Configuration
  getConfig: () => ipcRenderer.invoke('get-config'),
  updateConfig: (key: string, value: any) =>
    ipcRenderer.invoke('update-config', key, value),
  resetConfig: () => ipcRenderer.invoke('reset-config'),

  // File operations
  openFileDialog: (options: any) => ipcRenderer.invoke('open-file-dialog', options),
  saveFileDialog: (options: any) => ipcRenderer.invoke('save-file-dialog', options),
  openExternal: (url: string) => ipcRenderer.invoke('open-external', url),

  // Notifications
  showNotification: (options: any) => ipcRenderer.invoke('show-notification', options),

  // Event listeners
  onServiceUpdate: (callback: (event: any, data: any) => void) => {
    ipcRenderer.on('service-update', callback)
    return () => ipcRenderer.removeListener('service-update', callback)
  },

  onSystemMetricsUpdate: (callback: (event: any, data: any) => void) => {
    ipcRenderer.on('system-metrics-update', callback)
    return () => ipcRenderer.removeListener('system-metrics-update', callback)
  },

  onAgentUpdate: (callback: (event: any, data: any) => void) => {
    ipcRenderer.on('agent-update', callback)
    return () => ipcRenderer.removeListener('agent-update', callback)
  },

  onLogUpdate: (callback: (event: any, data: any) => void) => {
    ipcRenderer.on('log-update', callback)
    return () => ipcRenderer.removeListener('log-update', callback)
  },

  onCostUpdate: (callback: (event: any, data: any) => void) => {
    ipcRenderer.on('cost-update', callback)
    return () => ipcRenderer.removeListener('cost-update', callback)
  }
})

// Type definitions for the exposed API
declare global {
  interface Window {
    electronAPI: {
      getSystemStatus: () => Promise<any>
      startService: (serviceName: string) => Promise<any>
      stopService: (serviceName: string) => Promise<any>
      restartService: (serviceName: string) => Promise<any>
      getServiceLogs: (serviceName: string) => Promise<any>
      getSystemMetrics: () => Promise<any>
      getCostData: () => Promise<any>
      getAIConfig: () => Promise<any>
      updateAIConfig: (config: any) => Promise<any>
      executeAutomation: (command: string, params?: any) => Promise<any>
      getConversations: () => Promise<any[]>
      sendMessage: (message: string, provider?: string) => Promise<any>
      getAgents: () => Promise<any[]>
      controlAgent: (agentId: string, action: string, params?: any) => Promise<any>
      getConfig: () => Promise<any>
      updateConfig: (key: string, value: any) => Promise<boolean>
      resetConfig: () => Promise<void>
      openFileDialog: (options: any) => Promise<any>
      saveFileDialog: (options: any) => Promise<any>
      openExternal: (url: string) => Promise<void>
      showNotification: (options: any) => Promise<void>
      onServiceUpdate: (callback: (event: any, data: any) => void) => () => void
      onSystemMetricsUpdate: (callback: (event: any, data: any) => void) => () => void
      onAgentUpdate: (callback: (event: any, data: any) => void) => () => void
      onLogUpdate: (callback: (event: any, data: any) => void) => () => void
      onCostUpdate: (callback: (event: any, data: any) => void) => () => void
    }
  }
}