import React from 'react'
import { Bell, Search, User } from 'lucide-react'

export const Header = () => {
  return (
    <header className="h-16 bg-surface border-b border-border flex items-center justify-between px-6">
      <div className="flex items-center space-x-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground" size={20} />
          <input
            type="text"
            placeholder="Search..."
            className="pl-10 pr-4 py-2 w-64 bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
          />
        </div>
      </div>

      <div className="flex items-center space-x-4">
        <button className="p-2 rounded-md hover:bg-muted transition-colors">
          <Bell size={20} />
        </button>
        <button className="p-2 rounded-md hover:bg-muted transition-colors">
          <User size={20} />
        </button>
      </div>
    </header>
  )
}