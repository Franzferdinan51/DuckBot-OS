import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useTheme } from '../../theme/ThemeContext';
import {
  Menu,
  Search,
  Bell,
  Wifi,
  Battery,
  Volume2,
  Maximize2,
  Minimize2,
  X
} from 'lucide-react';

interface HeaderProps {
  onToggleSidebar: () => void;
  sidebarCollapsed: boolean;
}

const Header: React.FC<HeaderProps> = ({ onToggleSidebar, sidebarCollapsed }) => {
  const { colors, spacing } = useTheme();
  const [searchExpanded, setSearchExpanded] = useState(false);
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [quickSettingsOpen, setQuickSettingsOpen] = useState(false);
  const [maximized, setMaximized] = useState(false);

  // Mock system status
  const systemStatus = {
    wifi: { connected: true, signal: 85 },
    battery: { level: 72, charging: false },
    volume: 65,
    time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
  };

  const notifications = [
    {
      id: '1',
      type: 'warning' as const,
      title: 'High Memory Usage',
      message: 'System memory usage is at 85%',
      timestamp: new Date(Date.now() - 5 * 60 * 1000),
    },
    {
      id: '2',
      type: 'info' as const,
      title: 'Agent Update',
      message: 'AI Agent Qwen-30B is now available',
      timestamp: new Date(Date.now() - 15 * 60 * 1000),
    },
    {
      id: '3',
      type: 'success' as const,
      title: 'Service Started',
      message: 'Desktop Automation service is running',
      timestamp: new Date(Date.now() - 30 * 60 * 1000),
    },
  ];

  const handleMaximize = () => {
    setMaximized(!maximized);
    if (window.require) {
      const { ipcRenderer } = window.require('electron');
      ipcRenderer.send(maximized ? 'unmaximize' : 'maximize');
    }
  };

  return (
    <header className="flex items-center justify-between px-4 py-2 border-b"
            style={{ borderColor: colors.border, backgroundColor: colors.surface }}>

      {/* Left Section */}
      <div className="flex items-center space-x-4">
        {/* Sidebar Toggle */}
        <motion.button
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.9 }}
          onClick={onToggleSidebar}
          className="p-2 rounded-lg hover:bg-opacity-20 transition-colors"
          style={{ color: colors.textSecondary }}
        >
          <Menu size={20} />
        </motion.button>

        {/* Search */}
        <div className="relative">
          <AnimatePresence>
            {searchExpanded ? (
              <motion.div
                initial={{ width: 0, opacity: 0 }}
                animate={{ width: 320, opacity: 1 }}
                exit={{ width: 0, opacity: 0 }}
                className="relative"
              >
                <input
                  type="text"
                  placeholder="Search apps, commands, settings..."
                  className="w-full px-4 py-2 pl-10 rounded-lg border focus:outline-none focus:ring-2"
                  style={{
                    backgroundColor: colors.background,
                    borderColor: colors.border,
                    color: colors.text,
                    focusRingColor: colors.primary,
                  }}
                  autoFocus
                  onBlur={() => setSearchExpanded(false)}
                />
                <Search
                  size={18}
                  className="absolute left-3 top-1/2 transform -translate-y-1/2"
                  style={{ color: colors.textSecondary }}
                />
              </motion.div>
            ) : (
              <motion.button
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.9 }}
                onClick={() => setSearchExpanded(true)}
                className="p-2 rounded-lg hover:bg-opacity-20 transition-colors"
                style={{ color: colors.textSecondary }}
              >
                <Search size={20} />
              </motion.button>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* Center Section - Title */}
      <div className="flex-1 text-center">
        <h1 className="text-lg font-semibold" style={{ color: colors.text }}>
          DuckBot Control Center
        </h1>
      </div>

      {/* Right Section */}
      <div className="flex items-center space-x-2">
        {/* System Status Indicators */}
        <div className="flex items-center space-x-3 px-3 py-1 rounded-lg"
             style={{ backgroundColor: colors.background }}>

          {/* WiFi */}
          <div className="flex items-center space-x-1" style={{ color: colors.textSecondary }}>
            <Wifi size={16} fill={systemStatus.wifi.connected ? 'currentColor' : 'none'} />
            <span className="text-xs">{systemStatus.wifi.signal}%</span>
          </div>

          {/* Volume */}
          <div className="flex items-center space-x-1" style={{ color: colors.textSecondary }}>
            <Volume2 size={16} />
          </div>

          {/* Battery */}
          <div className="flex items-center space-x-1" style={{ color: colors.textSecondary }}>
            <Battery size={16} />
            <span className="text-xs">{systemStatus.battery.level}%</span>
          </div>

          {/* Time */}
          <span className="text-xs font-medium" style={{ color: colors.text }}>
            {systemStatus.time}
          </span>
        </div>

        {/* Notifications */}
        <div className="relative">
          <motion.button
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
            onClick={() => setNotificationsOpen(!notificationsOpen)}
            className="relative p-2 rounded-lg hover:bg-opacity-20 transition-colors"
            style={{ color: colors.textSecondary }}
          >
            <Bell size={20} />
            {notifications.length > 0 && (
              <span className="absolute top-1 right-1 w-2 h-2 rounded-full"
                    style={{ backgroundColor: colors.error }} />
            )}
          </motion.button>

          {/* Notifications Dropdown */}
          <AnimatePresence>
            {notificationsOpen && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 10 }}
                className="absolute right-0 mt-2 w-80 rounded-lg shadow-lg border"
                style={{
                  backgroundColor: colors.surface,
                  borderColor: colors.border,
                  zIndex: 1000,
                }}
              >
                <div className="p-3 border-b" style={{ borderColor: colors.border }}>
                  <h3 className="font-semibold" style={{ color: colors.text }}>
                    Notifications
                  </h3>
                </div>
                <div className="max-h-96 overflow-y-auto">
                  {notifications.map((notification) => (
                    <div
                      key={notification.id}
                      className="p-3 border-b hover:bg-opacity-10 transition-colors cursor-pointer"
                      style={{ borderColor: colors.border }}
                    >
                      <div className="flex items-start space-x-3">
                        <div className={`w-2 h-2 rounded-full mt-1 ${
                          notification.type === 'error' ? 'bg-red-500' :
                          notification.type === 'warning' ? 'bg-yellow-500' :
                          notification.type === 'success' ? 'bg-green-500' :
                          'bg-blue-500'
                        }`} />
                        <div className="flex-1">
                          <h4 className="font-medium text-sm" style={{ color: colors.text }}>
                            {notification.title}
                          </h4>
                          <p className="text-xs" style={{ color: colors.textSecondary }}>
                            {notification.message}
                          </p>
                          <p className="text-xs mt-1" style={{ color: colors.textSecondary }}>
                            {notification.timestamp.toLocaleTimeString()}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Window Controls (Electron) */}
        {window.require && (
          <div className="flex items-center space-x-1">
            <motion.button
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
              onClick={() => window.require('electron').ipcRenderer.send('minimize')}
              className="p-2 rounded hover:bg-opacity-20 transition-colors"
              style={{ color: colors.textSecondary }}
            >
              <Minimize2 size={16} />
            </motion.button>
            <motion.button
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
              onClick={handleMaximize}
              className="p-2 rounded hover:bg-opacity-20 transition-colors"
              style={{ color: colors.textSecondary }}
            >
              {maximized ? <Minimize2 size={16} /> : <Maximize2 size={16} />}
            </motion.button>
            <motion.button
              whileHover={{ scale: 1.1, backgroundColor: colors.error }}
              whileTap={{ scale: 0.9 }}
              onClick={() => window.require('electron').ipcRenderer.send('close')}
              className="p-2 rounded hover:bg-opacity-20 transition-colors"
              style={{ color: colors.textSecondary }}
            >
              <X size={16} />
            </motion.button>
          </div>
        )}
      </div>
    </header>
  );
};

export default Header;