import React from 'react'
import { useNavigate } from 'react-router-dom'
import { cn } from '@lib/utils'
import {
  LayoutDashboard,
  Settings,
  Bot,
  MessageSquare,
  Zap,
  DollarSign,
  ChevronLeft,
  ChevronRight
} from 'lucide-react'

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Services', href: '/services', icon: Settings },
  { name: 'Agents', href: '/agents', icon: Bot },
  { name: 'Chat', href: '/chat', icon: MessageSquare },
  { name: 'Automation', href: '/automation', icon: Zap },
  { name: 'Costs', href: '/costs', icon: DollarSign },
]

interface SidebarProps {
  className?: string
}

export const Sidebar: React.FC<SidebarProps> = ({ className }) => {
  const navigate = useNavigate()
  const [sidebarOpen, setSidebarOpen] = React.useState(true)

  return (
    <div className={cn(
      "w-64 bg-surface border-r border-border h-full flex flex-col",
      className
    )}>
      <div className="flex items-center justify-between p-4 border-b border-border">
        <h1 className="text-xl font-bold text-foreground">DuckBot</h1>
        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="p-2 rounded-md hover:bg-muted transition-colors"
        >
          {sidebarOpen ? <ChevronLeft size={20} /> : <ChevronRight size={20} />}
        </button>
      </div>

      <nav className="flex-1 p-4 space-y-2">
        {navigation.map((item) => {
          const Icon = item.icon
          return (
            <button
              key={item.name}
              onClick={() => navigate(item.href)}
              className="w-full flex items-center space-x-3 px-3 py-2 rounded-md hover:bg-muted transition-colors text-left"
            >
              <Icon size={20} />
              <span>{item.name}</span>
            </button>
          )
        })}
      </nav>
    </div>
  )
}