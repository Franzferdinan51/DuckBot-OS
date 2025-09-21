import React from 'react'
import ReactDOM from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import './index.css'

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
})

// Type definitions for Electron API
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

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </QueryClientProvider>
  </React.StrictMode>,
)