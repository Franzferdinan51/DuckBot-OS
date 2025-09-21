import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { cn } from '@/lib/utils';
import {
  Search,
  Bell,
  Settings,
  User,
  Menu,
  Maximize2,
  Minimize2,
  X,
  Plus,
  Command,
  Palette,
  HelpCircle,
  Github
} from 'lucide-react';

interface HeaderProps {
  onMenuClick: () => void;
  isDarkMode: boolean;
  onThemeToggle: () => void;
}

interface Notification {
  id: string;
  type: 'info' | 'warning' | 'error' | 'success';
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
}

export function Header({ onMenuClick, isDarkMode, onThemeToggle }: HeaderProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [showNotifications, setShowNotifications] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [isMaximized, setIsMaximized] = useState(false);

  const navigate = useNavigate();

  useEffect(() => {
    // Simulate receiving notifications
    const mockNotifications: Notification[] = [
      {
        id: '1',
        type: 'success',
        title: 'Service Started',
        message: 'LM Studio service started successfully',
        timestamp: new Date().toISOString(),
        read: false
      },
      {
        id: '2',
        type: 'warning',
        title: 'High Memory Usage',
        message: 'System memory usage is above 80%',
        timestamp: new Date(Date.now() - 5 * 60 * 1000).toISOString(),
        read: false
      },
      {
        id: '3',
        type: 'info',
        title: 'AI Agent Update',
        message: 'New AI agent model available',
        timestamp: new Date(Date.now() - 15 * 60 * 1000).toISOString(),
        read: true
      }
    ];
    setNotifications(mockNotifications);
  }, []);

  const unreadCount = notifications.filter(n => !n.read).length;

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    // Implement search functionality
    console.log('Searching for:', searchQuery);
  };

  const markAsRead = (id: string) => {
    setNotifications(prev =>
      prev.map(n => n.id === id ? { ...n, read: true } : n)
    );
  };

  const markAllAsRead = () => {
    setNotifications(prev => prev.map(n => ({ ...n, read: true })));
  };

  const handleWindowAction = (action: 'minimize' | 'maximize' | 'close') => {
    if (window.electronAPI) {
      window.electronAPI[action]();
    }
  };

  const quickActions = [
    { name: 'New Chat', icon: MessageSquare, action: () => navigate('/conversations') },
    { name: 'Start Service', icon: Plus, action: () => navigate('/services') },
    { name: 'Run Command', icon: Terminal, action: () => navigate('/automation') },
    { name: 'View Logs', icon: FileText, action: () => navigate('/monitoring/logs') }
  ];

  return (
    <header className="h-16 bg-surface border-b border-border flex items-center justify-between px-4 lg:px-6">
      {/* Left side - Mobile menu and search */}
      <div className="flex items-center space-x-4 flex-1">
        {/* Mobile menu button */}
        <button
          onClick={onMenuClick}
          className="lg:hidden p-2 hover:bg-accent rounded-lg transition-colors"
        >
          <Menu className="w-5 h-5 text-muted-foreground" />
        </button>

        {/* Search bar */}
        <form onSubmit={handleSearch} className="flex-1 max-w-md">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search services, agents, commands..."
              className="w-full pl-10 pr-4 py-2 bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent text-sm"
            />
          </div>
        </form>

        {/* Quick actions */}
        <div className="hidden md:flex items-center space-x-2">
          {quickActions.slice(0, 2).map((action) => (
            <button
              key={action.name}
              onClick={action.action}
              className="p-2 hover:bg-accent rounded-lg transition-colors group"
              title={action.name}
            >
              <action.icon className="w-4 h-4 text-muted-foreground group-hover:text-foreground" />
            </button>
          ))}
        </div>
      </div>

      {/* Right side - Actions */}
      <div className="flex items-center space-x-2">
        {/* Window controls (Windows/Linux) */}
        {process.platform !== 'darwin' && (
          <div className="hidden lg:flex items-center space-x-1">
            <button
              onClick={() => handleWindowAction('minimize')}
              className="p-2 hover:bg-accent rounded transition-colors"
              title="Minimize"
            >
              <Minimize2 className="w-4 h-4 text-muted-foreground" />
            </button>
            <button
              onClick={() => {
                setIsMaximized(!isMaximized);
                handleWindowAction('maximize');
              }}
              className="p-2 hover:bg-accent rounded transition-colors"
              title={isMaximized ? 'Restore' : 'Maximize'}
            >
              {isMaximized ? (
                <Minimize2 className="w-4 h-4 text-muted-foreground transform rotate-45" />
              ) : (
                <Maximize2 className="w-4 h-4 text-muted-foreground" />
              )}
            </button>
            <button
              onClick={() => handleWindowAction('close')}
              className="p-2 hover:bg-destructive hover:text-destructive-foreground rounded transition-colors"
              title="Close"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* Notifications */}
        <div className="relative">
          <button
            onClick={() => setShowNotifications(!showNotifications)}
            className="relative p-2 hover:bg-accent rounded-lg transition-colors"
          >
            <Bell className="w-5 h-5 text-muted-foreground" />
            {unreadCount > 0 && (
              <span className="absolute top-1 right-1 w-2 h-2 bg-destructive rounded-full"></span>
            )}
          </button>

          {/* Notifications dropdown */}
          {showNotifications && (
            <div className="absolute right-0 mt-2 w-80 bg-surface border border-border rounded-lg shadow-lg z-50">
              <div className="p-4 border-b border-border">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-semibold text-foreground">Notifications</h3>
                  {unreadCount > 0 && (
                    <button
                      onClick={markAllAsRead}
                      className="text-xs text-primary hover:underline"
                    >
                      Mark all as read
                    </button>
                  )}
                </div>
              </div>
              <div className="max-h-96 overflow-y-auto">
                {notifications.length === 0 ? (
                  <div className="p-4 text-center text-muted-foreground text-sm">
                    No notifications
                  </div>
                ) : (
                  notifications.map((notification) => (
                    <div
                      key={notification.id}
                      className={cn(
                        'p-4 border-b border-border hover:bg-accent cursor-pointer transition-colors',
                        !notification.read && 'bg-accent/30'
                      )}
                      onClick={() => markAsRead(notification.id)}
                    >
                      <div className="flex items-start space-x-3">
                        <div className={cn(
                          'w-2 h-2 rounded-full mt-2',
                          notification.type === 'success' && 'bg-green-500',
                          notification.type === 'warning' && 'bg-yellow-500',
                          notification.type === 'error' && 'bg-red-500',
                          notification.type === 'info' && 'bg-blue-500'
                        )} />
                        <div className="flex-1">
                          <h4 className="text-sm font-medium text-foreground">
                            {notification.title}
                          </h4>
                          <p className="text-xs text-muted-foreground mt-1">
                            {notification.message}
                          </p>
                          <p className="text-xs text-muted-foreground mt-2">
                            {new Date(notification.timestamp).toLocaleString()}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>

        {/* Settings */}
        <button
          onClick={() => navigate('/settings')}
          className="p-2 hover:bg-accent rounded-lg transition-colors"
          title="Settings"
        >
          <Settings className="w-5 h-5 text-muted-foreground" />
        </button>

        {/* Help */}
        <button
          onClick={() => navigate('/help')}
          className="p-2 hover:bg-accent rounded-lg transition-colors"
          title="Help"
        >
          <HelpCircle className="w-5 h-5 text-muted-foreground" />
        </button>

        {/* User menu */}
        <div className="relative">
          <button
            onClick={() => setShowUserMenu(!showUserMenu)}
            className="p-2 hover:bg-accent rounded-lg transition-colors"
          >
            <div className="w-6 h-6 bg-primary rounded-full flex items-center justify-center">
              <User className="w-4 h-4 text-primary-foreground" />
            </div>
          </button>

          {/* User menu dropdown */}
          {showUserMenu && (
            <div className="absolute right-0 mt-2 w-48 bg-surface border border-border rounded-lg shadow-lg z-50">
              <div className="p-4 border-b border-border">
                <p className="text-sm font-medium text-foreground">DuckBot User</p>
                <p className="text-xs text-muted-foreground">v4.2.0</p>
              </div>
              <div className="p-2">
                <button
                  onClick={onThemeToggle}
                  className="w-full flex items-center space-x-3 px-3 py-2 rounded-lg hover:bg-accent transition-colors text-left"
                >
                  <Palette className="w-4 h-4 text-muted-foreground" />
                  <span className="text-sm text-foreground">
                    {isDarkMode ? 'Light Mode' : 'Dark Mode'}
                  </span>
                </button>
                <a
                  href="https://github.com"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center space-x-3 px-3 py-2 rounded-lg hover:bg-accent transition-colors"
                >
                  <Github className="w-4 h-4 text-muted-foreground" />
                  <span className="text-sm text-foreground">GitHub</span>
                </a>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}

// Helper components
const MessageSquare = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
  </svg>
);

const Terminal = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
  </svg>
);

const FileText = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
  </svg>
);