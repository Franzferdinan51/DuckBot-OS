import React from 'react'
import { Outlet } from 'react-router-dom'
import { Sidebar } from './ui/sidebar'
import { Header } from './ui/header'
import { AlertContainer } from './ui/alert'
import { useAppStore } from '@stores/useAppStore'

export function Layout() {
  const { sidebarOpen } = useAppStore()

  return (
    <div className="flex h-screen bg-background">
      <Sidebar />

      <div className={`flex-1 flex flex-col overflow-hidden ${sidebarOpen ? 'ml-64' : 'ml-0'} transition-all duration-300`}>
        <Header />

        <main className="flex-1 overflow-auto p-6">
          <div className="max-w-7xl mx-auto">
            <Outlet />
          </div>
        </main>
      </div>

      <AlertContainer />
    </div>
  )
}