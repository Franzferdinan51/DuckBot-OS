import React, { useEffect, useState } from 'react'
import { Routes, Route, useLocation } from 'react-router-dom'
import { QueryClientProvider, QueryClient } from '@tanstack/react-query'
import { Layout } from '@components/Layout'
import { Dashboard } from '@components/Dashboard'
import { Services } from '@components/Services'
import { Agents } from '@components/Agents'
import { Chat } from '@components/Chat'
import { Automation } from '@components/Automation'
import { Settings } from '@components/Settings'
import { CostTrackingDashboard } from '@components/cost'
import { useAppStore } from '@stores/useAppStore'
import { initElectronListeners } from '@lib/electron'
import { ThemeProvider } from '@components/theme-provider'

// Create query client
const queryClient = new QueryClient()

function AppContent() {
  const location = useLocation()
  const { theme, setTheme, initialize } = useAppStore()
  const [isInitialized, setIsInitialized] = useState(false)

  useEffect(() => {
    // Initialize app
    const initializeApp = async () => {
      await initialize()
      setIsInitialized(true)
    }
    initializeApp()
  }, [initialize])

  useEffect(() => {
    // Initialize Electron event listeners
    if (isInitialized) {
      const cleanup = initElectronListeners()
      return cleanup
    }
  }, [isInitialized])

  useEffect(() => {
    // Apply theme
    if (theme === 'dark') {
      document.documentElement.classList.add('dark')
    } else if (theme === 'light') {
      document.documentElement.classList.remove('dark')
    } else {
      const isDark = window.matchMedia('(prefers-color-scheme: dark)').matches
      document.documentElement.classList.toggle('dark', isDark)
    }
  }, [theme])

  if (!isInitialized) {
    return (
      <div className="flex h-screen items-center justify-center bg-background">
        <div className="loading-skeleton h-8 w-8 rounded-full animate-spin" />
      </div>
    )
  }

  return (
    <div className="h-screen bg-background text-foreground">
      <Layout>
        <Routes location={location}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/services" element={<Services />} />
          <Route path="/agents" element={<Agents />} />
          <Route path="/chat" element={<Chat />} />
          <Route path="/automation" element={<Automation />} />
          <Route path="/costs" element={<CostTrackingDashboard />} />
          <Route path="/costs/overview" element={<CostTrackingDashboard />} />
          <Route path="/costs/transactions" element={<CostTrackingDashboard />} />
          <Route path="/costs/budget" element={<CostTrackingDashboard />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="*" element={<Dashboard />} />
        </Routes>
      </Layout>
    </div>
  )
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider defaultTheme="dark" storageKey="duckbot-theme">
        <AppContent />
      </ThemeProvider>
    </QueryClientProvider>
  )
}

export default App