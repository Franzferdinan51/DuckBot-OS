import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { ServiceStatus, SystemMetrics, CostData, Agent, Conversation, AppConfig, Alert } from '@types'

interface AppState {
  // UI State
  theme: 'light' | 'dark' | 'system'
  sidebarOpen: boolean
  loading: boolean
  error: string | null
  alerts: Alert[]

  // System State
  services: Record<string, ServiceStatus>
  metrics: SystemMetrics | null
  costData: CostData | null
  agents: Agent[]
  conversations: Conversation[]
  activeConversation: Conversation | null

  // UI Preferences
  config: AppConfig

  // Actions
  setTheme: (theme: 'light' | 'dark' | 'system') => void
  toggleSidebar: () => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  addAlert: (alert: Omit<Alert, 'id' | 'timestamp'>) => void
  removeAlert: (id: string) => void
  clearAlerts: () => void

  // Service Actions
  updateService: (service: ServiceStatus) => void
  updateServices: (services: Record<string, ServiceStatus>) => void
  updateMetrics: (metrics: SystemMetrics) => void
  updateCostData: (costData: CostData) => void
  updateAgents: (agents: Agent[]) => void
  updateAgent: (agent: Agent) => void
  updateConversations: (conversations: Conversation[]) => void
  setActiveConversation: (conversation: Conversation | null) => void
  addMessage: (message: any) => void

  // Config Actions
  updateConfig: (config: Partial<AppConfig>) => void
  resetConfig: () => void

  // Initialize
  initialize: () => Promise<void>
}

export const useAppStore = create<AppState>()(
  persist(
    (set, get) => ({
      // Initial State
      theme: 'dark',
      sidebarOpen: true,
      loading: false,
      error: null,
      alerts: [],

      services: {},
      metrics: null,
      costData: null,
      agents: [],
      conversations: [],
      activeConversation: null,

      config: {
        windowBounds: { width: 1400, height: 900 },
        theme: 'dark',
        autoStart: false,
        minimizeToTray: false,
        notifications: true,
        services: {
          lmStudioUrl: 'http://localhost:1234',
          webuiPort: 8787,
          monitoringPort: 8789
        },
        features: {
          autoUpdate: true,
          telemetry: false,
          debugMode: false
        }
      },

      // Actions
      setTheme: (theme) => set({ theme }),
      toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
      setLoading: (loading) => set({ loading }),
      setError: (error) => set({ error }),
      addAlert: (alert) => {
        const newAlert: Alert = {
          id: crypto.randomUUID(),
          timestamp: new Date(),
          ...alert
        }
        set((state) => ({
          alerts: [...state.alerts, newAlert]
        }))

        // Auto-remove alerts after 10 seconds
        setTimeout(() => {
          get().removeAlert(newAlert.id)
        }, 10000)
      },
      removeAlert: (id) => set((state) => ({
        alerts: state.alerts.filter(alert => alert.id !== id)
      })),
      clearAlerts: () => set({ alerts: [] }),

      // Service Actions
      updateService: (service) => set((state) => ({
        services: {
          ...state.services,
          [service.name]: service
        }
      })),
      updateServices: (services) => set({ services }),
      updateMetrics: (metrics) => set({ metrics }),
      updateCostData: (costData) => set({ costData }),
      updateAgents: (agents) => set({ agents }),
      updateAgent: (agent) => set((state) => ({
        agents: state.agents.map(a => a.id === agent.id ? agent : a)
      })),
      updateConversations: (conversations) => set({ conversations }),
      setActiveConversation: (conversation) => set({ activeConversation: conversation }),
      addMessage: (message) => set((state) => {
        if (!state.activeConversation) return state

        const updatedConversation = {
          ...state.activeConversation,
          messages: [...state.activeConversation.messages, message],
          updated_at: new Date()
        }

        return {
          activeConversation: updatedConversation,
          conversations: state.conversations.map(conv =>
            conv.id === updatedConversation.id ? updatedConversation : conv
          )
        }
      }),

      // Config Actions
      updateConfig: (newConfig) => set((state) => ({
        config: { ...state.config, ...newConfig }
      })),
      resetConfig: () => set({
        config: {
          windowBounds: { width: 1400, height: 900 },
          theme: 'dark',
          autoStart: false,
          minimizeToTray: false,
          notifications: true,
          services: {
            lmStudioUrl: 'http://localhost:1234',
            webuiPort: 8787,
            monitoringPort: 8789
          },
          features: {
            autoUpdate: true,
            telemetry: false,
            debugMode: false
          }
        }
      }),

      // Initialize
      initialize: async () => {
        const state = get()
        state.setLoading(true)

        try {
          // Load configuration from Electron
          if (window.electronAPI) {
            const config = await window.electronAPI.getConfig()
            state.updateConfig(config)

            // Load initial data
            const [services, metrics, costData, agents, conversations] = await Promise.all([
              window.electronAPI.getSystemStatus(),
              window.electronAPI.getSystemMetrics(),
              window.electronAPI.getCostData(),
              window.electronAPI.getAgents(),
              window.electronAPI.getConversations()
            ])

            state.updateServices(services)
            state.updateMetrics(metrics)
            state.updateCostData(costData)
            state.updateAgents(agents)
            state.updateConversations(conversations)
          }
        } catch (error) {
          state.setError(error instanceof Error ? error.message : 'Failed to initialize app')
        } finally {
          state.setLoading(false)
        }
      }
    }),
    {
      name: 'duckbot-desktop-storage',
      partialize: (state) => ({
        theme: state.theme,
        sidebarOpen: state.sidebarOpen,
        config: state.config
      })
    }
  )
)