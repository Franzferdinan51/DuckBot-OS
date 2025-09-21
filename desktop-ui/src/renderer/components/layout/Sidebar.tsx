import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { cn } from '@/lib/utils';
import {
  Home,
  Settings,
  Activity,
  Bot,
  Zap,
  MessageSquare,
  DollarSign,
  Bell,
  BarChart3,
  Database,
  Shield,
  Palette,
  Github,
  HelpCircle,
  LogOut,
  ChevronDown,
  ChevronRight,
  Plus,
  Users,
  Cpu,
  Globe,
  Terminal,
  FileText
} from 'lucide-react';

interface SidebarProps {
  open: boolean;
  onClose: () => void;
  isDarkMode: boolean;
  onThemeToggle: () => void;
}

interface NavigationItem {
  name: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: number;
  description?: string;
  children?: NavigationItem[];
}

const navigation: NavigationItem[] = [
  {
    name: 'Dashboard',
    href: '/',
    icon: Home,
    description: 'System overview and quick actions'
  },
  {
    name: 'Services',
    href: '/services',
    icon: Activity,
    description: 'Manage DuckBot services',
    badge: 0
  },
  {
    name: 'AI Agents',
    href: '/agents',
    icon: Bot,
    description: 'Coordinate AI agents and tasks',
    children: [
      { name: 'Active Agents', href: '/agents/active', icon: Users },
      { name: 'Agent Tasks', href: '/agents/tasks', icon: Terminal },
      { name: 'Performance', href: '/agents/performance', icon: BarChart3 }
    ]
  },
  {
    name: 'Automation',
    href: '/automation',
    icon: Zap,
    description: 'Desktop automation and commands',
    children: [
      { name: 'Commands', href: '/automation/commands', icon: Terminal },
      { name: 'Workflows', href: '/automation/workflows', icon: FileText },
      { name: 'Schedule', href: '/automation/schedule', icon: Clock }
    ]
  },
  {
    name: 'Monitoring',
    href: '/monitoring',
    icon: BarChart3,
    description: 'System metrics and performance',
    children: [
      { name: 'System Metrics', href: '/monitoring/system', icon: Cpu },
      { name: 'Service Logs', href: '/monitoring/logs', icon: FileText },
      { name: 'Performance', href: '/monitoring/performance', icon: Activity }
    ]
  },
  {
    name: 'Conversations',
    href: '/conversations',
    icon: MessageSquare,
    description: 'AI chat history and memory',
    badge: 0
  },
  {
    name: 'Cost Tracking',
    href: '/costs',
    icon: DollarSign,
    description: 'AI costs and optimization',
    children: [
      { name: 'Overview', href: '/costs/overview', icon: BarChart3 },
      { name: 'Transactions', href: '/costs/transactions', icon: Database },
      { name: 'Budget', href: '/costs/budget', icon: DollarSign }
    ]
  },
  {
    name: 'Notifications',
    href: '/notifications',
    icon: Bell,
    description: 'System alerts and notifications',
    badge: 0
  }
];

const bottomNavigation: NavigationItem[] = [
  {
    name: 'Settings',
    href: '/settings',
    icon: Settings,
    description: 'Application preferences'
  },
  {
    name: 'Help',
    href: '/help',
    icon: HelpCircle,
    description: 'Documentation and support'
  }
];

export function Sidebar({ open, onClose, isDarkMode, onThemeToggle }: SidebarProps) {
  const location = useLocation();
  const [expandedItems, setExpandedItems] = useState<string[]>([]);

  const toggleExpanded = (name: string) => {
    setExpandedItems(prev =>
      prev.includes(name)
        ? prev.filter(item => item !== name)
        : [...prev, name]
    );
  };

  const isActive = (href: string) => {
    return location.pathname === href || location.pathname.startsWith(href + '/');
  };

  return (
    <>
      {/* Mobile sidebar */}
      <div className={cn(
        'fixed inset-y-0 left-0 z-50 w-64 bg-surface border-r border-border transform transition-transform duration-200 lg:hidden',
        open ? 'translate-x-0' : '-translate-x-full'
      )}>
        <div className="flex h-full flex-col">
          {/* Logo and close button */}
          <div className="flex h-16 items-center justify-between px-6 border-b border-border">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
                <Bot className="w-5 h-5 text-primary-foreground" />
              </div>
              <span className="text-lg font-semibold text-foreground">DuckBot</span>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-accent rounded-lg transition-colors"
            >
              <X className="w-5 h-5 text-muted-foreground" />
            </button>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-4 py-6 space-y-2 overflow-y-auto">
            {navigation.map((item) => (
              <NavigationItemComponent
                key={item.name}
                item={item}
                isActive={isActive(item.href)}
                isExpanded={expandedItems.includes(item.name)}
                onToggleExpand={() => toggleExpanded(item.name)}
                onClose={onClose}
              />
            ))}
          </nav>

          {/* Bottom navigation */}
          <div className="px-4 py-4 border-t border-border space-y-2">
            {bottomNavigation.map((item) => (
              <NavigationItemComponent
                key={item.name}
                item={item}
                isActive={isActive(item.href)}
                onClose={onClose}
              />
            ))}
          </div>
        </div>
      </div>

      {/* Desktop sidebar */}
      <div className="hidden lg:fixed lg:inset-y-0 lg:left-0 lg:z-40 lg:w-72 lg:bg-surface lg:border-r lg:border-border">
        <div className="flex h-full flex-col">
          {/* Logo */}
          <div className="flex h-16 items-center px-6 border-b border-border">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-br from-primary to-primary/60 rounded-xl flex items-center justify-center shadow-lg">
                <Bot className="w-6 h-6 text-primary-foreground" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-foreground">DuckBot</h1>
                <p className="text-xs text-muted-foreground">v4.2.0</p>
              </div>
            </div>
          </div>

          {/* System status bar */}
          <div className="px-6 py-4 border-b border-border">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-foreground">System Status</span>
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                <span className="text-xs text-muted-foreground">Online</span>
              </div>
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-4 py-6 space-y-1 overflow-y-auto">
            {navigation.map((item) => (
              <NavigationItemComponent
                key={item.name}
                item={item}
                isActive={isActive(item.href)}
                isExpanded={expandedItems.includes(item.name)}
                onToggleExpand={() => toggleExpanded(item.name)}
              />
            ))}
          </nav>

          {/* Bottom section */}
          <div className="px-4 py-4 border-t border-border space-y-1">
            {bottomNavigation.map((item) => (
              <NavigationItemComponent
                key={item.name}
                item={item}
                isActive={isActive(item.href)}
              />
            ))}

            {/* Theme toggle */}
            <button
              onClick={onThemeToggle}
              className="w-full flex items-center space-x-3 px-3 py-2 rounded-lg hover:bg-accent transition-colors group"
            >
              <Palette className="w-5 h-5 text-muted-foreground group-hover:text-foreground" />
              <span className="text-sm font-medium text-foreground">
                {isDarkMode ? 'Light Mode' : 'Dark Mode'}
              </span>
            </button>

            {/* External links */}
            <a
              href="https://github.com"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center space-x-3 px-3 py-2 rounded-lg hover:bg-accent transition-colors group"
            >
              <Github className="w-5 h-5 text-muted-foreground group-hover:text-foreground" />
              <span className="text-sm font-medium text-foreground">GitHub</span>
            </a>
          </div>
        </div>
      </div>
    </>
  );
}

interface NavigationItemComponentProps {
  item: NavigationItem;
  isActive: boolean;
  isExpanded?: boolean;
  onToggleExpand?: () => void;
  onClose?: () => void;
}

function NavigationItemComponent({
  item,
  isActive,
  isExpanded,
  onToggleExpand,
  onClose
}: NavigationItemComponentProps) {
  const Icon = item.icon;
  const hasChildren = item.children && item.children.length > 0;

  if (hasChildren) {
    return (
      <div className="space-y-1">
        <button
          onClick={() => {
            onToggleExpand?.();
            onClose?.();
          }}
          className={cn(
            'w-full flex items-center justify-between px-3 py-2 rounded-lg transition-colors group',
            isActive
              ? 'bg-accent text-accent-foreground'
              : 'hover:bg-accent text-muted-foreground hover:text-foreground'
          )}
        >
          <div className="flex items-center space-x-3">
            <Icon className="w-5 h-5" />
            <span className="text-sm font-medium">{item.name}</span>
            {item.badge !== undefined && item.badge > 0 && (
              <span className="px-2 py-1 text-xs bg-destructive text-destructive-foreground rounded-full">
                {item.badge}
              </span>
            )}
          </div>
          {isExpanded ? (
            <ChevronDown className="w-4 h-4" />
          ) : (
            <ChevronRight className="w-4 h-4" />
          )}
        </button>

        {isExpanded && (
          <div className="ml-4 space-y-1">
            {item.children.map((child) => (
              <Link
                key={child.name}
                to={child.href}
                onClick={onClose}
                className={cn(
                  'flex items-center space-x-3 px-3 py-2 rounded-lg transition-colors group',
                  location.pathname === child.href
                    ? 'bg-accent text-accent-foreground'
                    : 'hover:bg-accent text-muted-foreground hover:text-foreground'
                )}
              >
                <child.icon className="w-4 h-4" />
                <span className="text-sm">{child.name}</span>
              </Link>
            ))}
          </div>
        )}
      </div>
    );
  }

  return (
    <Link
      to={item.href}
      onClick={onClose}
      className={cn(
        'flex items-center space-x-3 px-3 py-2 rounded-lg transition-colors group',
        isActive
          ? 'bg-accent text-accent-foreground'
          : 'hover:bg-accent text-muted-foreground hover:text-foreground'
      )}
      title={item.description}
    >
      <Icon className="w-5 h-5" />
      <span className="text-sm font-medium">{item.name}</span>
      {item.badge !== undefined && item.badge > 0 && (
        <span className="ml-auto px-2 py-1 text-xs bg-destructive text-destructive-foreground rounded-full">
          {item.badge}
        </span>
      )}
    </Link>
  );
}

// Helper components
const X = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
  </svg>
);

const Clock = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);