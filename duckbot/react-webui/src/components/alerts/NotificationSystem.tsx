import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useTheme } from '../../theme/ThemeContext';
import {
  Bell,
  X,
  CheckCircle,
  AlertTriangle,
  Info,
  XCircle,
  Clock,
  Settings,
  Filter,
  MoreVertical,
  ExternalLink,
  Archive,
  Trash2
} from 'lucide-react';

interface NotificationSystemProps {
  className?: string;
  position?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left';
  maxVisible?: number;
  autoClose?: boolean;
  autoCloseDelay?: number;
}

interface Notification {
  id: string;
  type: 'success' | 'warning' | 'error' | 'info';
  title: string;
  message: string;
  timestamp: Date;
  source: string;
  action?: {
    label: string;
    onClick: () => void;
    icon?: React.ReactNode;
  };
  persistent?: boolean;
  read?: boolean;
  severity?: 'low' | 'medium' | 'high' | 'critical';
}

const NotificationSystem: React.FC<NotificationSystemProps> = ({
  className,
  position = 'top-right',
  maxVisible = 5,
  autoClose = true,
  autoCloseDelay = 5000,
}) => {
  const { colors } = useTheme();
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [showPanel, setShowPanel] = useState(false);
  const [filter, setFilter] = useState<'all' | 'unread' | 'type'>('all');
  const [typeFilter, setTypeFilter] = useState<'all' | 'success' | 'warning' | 'error' | 'info'>('all');

  // Generate mock notifications
  const generateMockNotifications = (): Notification[] => [
    {
      id: '1',
      type: 'success',
      title: 'Service Recovery Complete',
      message: 'LM Studio service has been successfully restarted and is now operating normally.',
      timestamp: new Date(Date.now() - 2 * 60 * 1000),
      source: 'Service Manager',
      severity: 'medium',
    },
    {
      id: '2',
      type: 'warning',
      title: 'High Memory Usage Detected',
      message: 'System memory usage is at 85%. Consider closing unused applications or services.',
      timestamp: new Date(Date.now() - 5 * 60 * 1000),
      source: 'System Monitor',
      severity: 'high',
      action: {
        label: 'View Details',
        onClick: () => console.log('View memory details'),
        icon: <ExternalLink size={14} />
      }
    },
    {
      id: '3',
      type: 'error',
      title: 'API Rate Limit Exceeded',
      message: 'OpenAI API rate limit has been reached. Switching to fallback provider.',
      timestamp: new Date(Date.now() - 10 * 60 * 1000),
      source: 'AI Provider Manager',
      severity: 'high',
      persistent: true,
    },
    {
      id: '4',
      type: 'info',
      title: 'Cost Optimization Applied',
      message: 'Automatically switched to local models for routine tasks, saving ~$2.50 today.',
      timestamp: new Date(Date.now() - 15 * 60 * 1000),
      source: 'Cost Tracker',
      severity: 'low',
    },
    {
      id: '5',
      type: 'success',
      title: 'Agent Deployment Successful',
      message: 'New AI agent "Code Reviewer" has been deployed and is active.',
      timestamp: new Date(Date.now() - 20 * 60 * 1000),
      source: 'Agent Manager',
      severity: 'medium',
    }
  ];

  useEffect(() => {
    // Initialize with mock notifications
    setNotifications(generateMockNotifications());

    // Simulate real-time notifications
    const interval = setInterval(() => {
      if (Math.random() > 0.7) {
        const newNotification: Notification = {
          id: Date.now().toString(),
          type: ['success', 'warning', 'error', 'info'][Math.floor(Math.random() * 4)] as any,
          title: 'System Update',
          message: 'A new system event has occurred.',
          timestamp: new Date(),
          source: 'System',
          severity: ['low', 'medium', 'high'][Math.floor(Math.random() * 3)] as any,
        };
        setNotifications(prev => [newNotification, ...prev.slice(0, maxVisible - 1)]);
      }
    }, 30000);

    return () => clearInterval(interval);
  }, [maxVisible]);

  // Auto-close notifications
  useEffect(() => {
    if (!autoClose) return;

    const timer = setInterval(() => {
      setNotifications(prev =>
        prev.filter(notification =>
          notification.persistent ||
          Date.now() - notification.timestamp.getTime() < autoCloseDelay
        )
      );
    }, 1000);

    return () => clearInterval(timer);
  }, [autoClose, autoCloseDelay]);

  const removeNotification = (id: string) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  };

  const markAsRead = (id: string) => {
    setNotifications(prev =>
      prev.map(n => n.id === id ? { ...n, read: true } : n)
    );
  };

  const markAllAsRead = () => {
    setNotifications(prev => prev.map(n => ({ ...n, read: true })));
  };

  const clearAll = () => {
    setNotifications([]);
  };

  const getFilteredNotifications = () => {
    let filtered = notifications;

    if (filter === 'unread') {
      filtered = filtered.filter(n => !n.read);
    }

    if (typeFilter !== 'all') {
      filtered = filtered.filter(n => n.type === typeFilter);
    }

    return filtered;
  };

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'success': return <CheckCircle size={20} />;
      case 'warning': return <AlertTriangle size={20} />;
      case 'error': return <XCircle size={20} />;
      case 'info': return <Info size={20} />;
      default: return <Info size={20} />;
    }
  };

  const getNotificationColor = (type: string) => {
    switch (type) {
      case 'success': return colors.success;
      case 'warning': return colors.warning;
      case 'error': return colors.error;
      case 'info': return colors.info;
      default: return colors.textSecondary;
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return colors.error;
      case 'high': return colors.warning;
      case 'medium': return colors.info;
      case 'low': return colors.textSecondary;
      default: return colors.textSecondary;
    }
  };

  const unreadCount = notifications.filter(n => !n.read).length;

  const getPositionClasses = () => {
    switch (position) {
      case 'top-right': return 'top-4 right-4';
      case 'top-left': return 'top-4 left-4';
      case 'bottom-right': return 'bottom-4 right-4';
      case 'bottom-left': return 'bottom-4 left-4';
      default: return 'top-4 right-4';
    }
  };

  return (
    <>
      {/* Notification Bell */}
      <div className={`relative ${className}`}>
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={() => setShowPanel(!showPanel)}
          className="relative p-2 rounded-lg border"
          style={{
            backgroundColor: colors.background,
            borderColor: colors.border,
            color: colors.textSecondary,
          }}
        >
          <Bell size={20} />
          {unreadCount > 0 && (
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              className="absolute -top-1 -right-1 w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold"
              style={{ backgroundColor: colors.error, color: colors.background }}
            >
              {unreadCount > 9 ? '9+' : unreadCount}
            </motion.div>
          )}
        </motion.button>
      </div>

      {/* Notification Panel */}
      <AnimatePresence>
        {showPanel && (
          <>
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black bg-opacity-50 z-40"
              onClick={() => setShowPanel(false)}
            />

            {/* Panel */}
            <motion.div
              initial={{ opacity: 0, x: position.includes('right') ? 100 : -100 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: position.includes('right') ? 100 : -100 }}
              className={`fixed z-50 w-96 max-h-[80vh] ${getPositionClasses()}`}
              style={{ backgroundColor: colors.surface, borderColor: colors.border }}
            >
              {/* Header */}
              <div className="p-4 border-b flex items-center justify-between" style={{ borderColor: colors.border }}>
                <div className="flex items-center space-x-3">
                  <Bell size={20} style={{ color: colors.primary }} />
                  <div>
                    <h3 className="font-bold" style={{ color: colors.text }}>Notifications</h3>
                    <p className="text-xs" style={{ color: colors.textSecondary }}>
                      {unreadCount} unread of {notifications.length} total
                    </p>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={markAllAsRead}
                    className="p-1 rounded text-xs"
                    style={{ color: colors.textSecondary }}
                    disabled={unreadCount === 0}
                  >
                    Mark all read
                  </motion.button>
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={clearAll}
                    className="p-1 rounded text-xs"
                    style={{ color: colors.textSecondary }}
                    disabled={notifications.length === 0}
                  >
                    Clear all
                  </motion.button>
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => setShowPanel(false)}
                    className="p-1 rounded"
                    style={{ color: colors.textSecondary }}
                  >
                    <X size={16} />
                  </motion.button>
                </div>
              </div>

              {/* Filters */}
              <div className="p-3 border-b flex items-center space-x-2" style={{ borderColor: colors.border }}>
                <select
                  value={filter}
                  onChange={(e) => setFilter(e.target.value as any)}
                  className="px-2 py-1 rounded text-xs border"
                  style={{
                    backgroundColor: colors.background,
                    borderColor: colors.border,
                    color: colors.text,
                  }}
                >
                  <option value="all">All</option>
                  <option value="unread">Unread</option>
                </select>
                <select
                  value={typeFilter}
                  onChange={(e) => setTypeFilter(e.target.value as any)}
                  className="px-2 py-1 rounded text-xs border"
                  style={{
                    backgroundColor: colors.background,
                    borderColor: colors.border,
                    color: colors.text,
                  }}
                >
                  <option value="all">All Types</option>
                  <option value="success">Success</option>
                  <option value="warning">Warning</option>
                  <option value="error">Error</option>
                  <option value="info">Info</option>
                </select>
              </div>

              {/* Notifications List */}
              <div className="overflow-y-auto max-h-[60vh]">
                {getFilteredNotifications().length === 0 ? (
                  <div className="p-8 text-center">
                    <Bell size={48} style={{ color: colors.border, opacity: 0.5 }} />
                    <p className="mt-2 text-sm" style={{ color: colors.textSecondary }}>
                      No notifications found
                    </p>
                  </div>
                ) : (
                  getFilteredNotifications().map((notification) => (
                    <motion.div
                      key={notification.id}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, x: 100 }}
                      className={`p-4 border-b hover:bg-opacity-50 transition-colors cursor-pointer ${!notification.read ? 'font-medium' : ''}`}
                      style={{
                        borderColor: colors.border,
                        backgroundColor: !notification.read ? `${colors.primary}10` : 'transparent',
                      }}
                      onClick={() => markAsRead(notification.id)}
                    >
                      <div className="flex items-start space-x-3">
                        <div style={{ color: getNotificationColor(notification.type) }}>
                          {getNotificationIcon(notification.type)}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-start justify-between mb-1">
                            <h4 className="text-sm font-medium truncate" style={{ color: colors.text }}>
                              {notification.title}
                            </h4>
                            <div className="flex items-center space-x-2 ml-2">
                              <span className="text-xs px-1 py-0.5 rounded capitalize"
                                    style={{
                                      backgroundColor: `${getSeverityColor(notification.severity || 'low')}20`,
                                      color: getSeverityColor(notification.severity || 'low'),
                                    }}>
                                    {notification.severity || 'low'}
                                  </span>
                              <motion.button
                                whileHover={{ scale: 1.1 }}
                                whileTap={{ scale: 0.9 }}
                                onClick={(e) => {
                                  e.stopPropagation();
                                  removeNotification(notification.id);
                                }}
                                className="p-1 rounded opacity-50 hover:opacity-100"
                                style={{ color: colors.textSecondary }}
                              >
                                <X size={12} />
                              </motion.button>
                            </div>
                          </div>
                          <p className="text-xs mb-2" style={{ color: colors.textSecondary }}>
                            {notification.message}
                          </p>
                          <div className="flex items-center justify-between">
                            <div className="flex items-center space-x-2 text-xs" style={{ color: colors.textSecondary }}>
                              <Clock size={12} />
                              <span>{notification.timestamp.toLocaleTimeString()}</span>
                              <span>•</span>
                              <span>{notification.source}</span>
                            </div>
                            {notification.action && (
                              <motion.button
                                whileHover={{ scale: 1.05 }}
                                whileTap={{ scale: 0.95 }}
                                onClick={(e) => {
                                  e.stopPropagation();
                                  notification.action?.onClick();
                                }}
                                className="flex items-center space-x-1 px-2 py-1 rounded text-xs"
                                style={{
                                  backgroundColor: colors.primary,
                                  color: colors.background,
                                }}
                              >
                                {notification.action.icon}
                                <span>{notification.action.label}</span>
                              </motion.button>
                            )}
                          </div>
                        </div>
                      </div>
                    </motion.div>
                  ))
                )}
              </div>

              {/* Footer */}
              <div className="p-3 border-t flex items-center justify-between" style={{ borderColor: colors.border }}>
                <div className="flex items-center space-x-2">
                  <Settings size={14} style={{ color: colors.textSecondary }} />
                  <span className="text-xs" style={{ color: colors.textSecondary }}>
                    Notification Settings
                  </span>
                </div>
                <span className="text-xs" style={{ color: colors.textSecondary }}>
                  Auto-close: {autoClose ? 'Enabled' : 'Disabled'}
                </span>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>

      {/* Toast Notifications */}
      <div className={`fixed ${getPositionClasses()} z-50 space-y-2 pointer-events-none`}>
        <AnimatePresence>
          {notifications.slice(0, maxVisible).map((notification) => (
            <motion.div
              key={notification.id}
              initial={{ opacity: 0, y: -20, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -20, scale: 0.95 }}
              className="pointer-events-auto"
            >
              <div className="flex items-center space-x-3 p-4 rounded-lg shadow-lg min-w-[300px] max-w-md"
                   style={{ backgroundColor: colors.surface, borderColor: getNotificationColor(notification.type) }}
              >
                <div style={{ color: getNotificationColor(notification.type) }}>
                  {getNotificationIcon(notification.type)}
                </div>
                <div className="flex-1">
                  <h4 className="font-medium text-sm" style={{ color: colors.text }}>
                    {notification.title}
                  </h4>
                  <p className="text-xs" style={{ color: colors.textSecondary }}>
                    {notification.message}
                  </p>
                </div>
                <motion.button
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.9 }}
                  onClick={() => removeNotification(notification.id)}
                  className="p-1 rounded"
                  style={{ color: colors.textSecondary }}
                >
                  <X size={14} />
                </motion.button>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </>
  );
};

export default NotificationSystem;