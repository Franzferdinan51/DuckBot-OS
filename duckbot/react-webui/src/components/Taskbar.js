import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useSystem } from '../contexts/SystemContext';
import { useAI } from '../contexts/AIContext';
import { useAuth } from '../contexts/AuthContext';

const Taskbar = ({ openApps, activeApp, onAppClick, onAppClose, desktopApps, onAppOpen }) => {
  const { systemStatus, networkStatus } = useSystem();
  const { currentModel, isThinking } = useAI();
  const { user } = useAuth();
  const [currentTime, setCurrentTime] = useState(new Date());
  const [showSystemMenu, setShowSystemMenu] = useState(false);
  const [showAppsMenu, setShowAppsMenu] = useState(false);

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const getSystemHealthColor = () => {
    if (systemStatus.status === 'running') return 'text-green-400';
    if (systemStatus.status === 'warning') return 'text-yellow-400';
    return 'text-red-400';
  };

  const getNetworkIcon = () => {
    return networkStatus === 'online' ? '🌐' : '📶';
  };

  return (
    <div className="taskbar fixed bottom-0 left-0 right-0 h-14 glass-strong border-t border-slate-600 flex items-center px-4 z-50">
      {/* System Menu Button */}
      <div className="relative">
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={() => setShowSystemMenu(!showSystemMenu)}
          className="flex items-center space-x-2 px-3 py-2 rounded-lg bg-gradient-to-r from-blue-500 to-cyan-500 text-white font-semibold hover:from-blue-600 hover:to-cyan-600"
        >
          <span className="text-lg">🤖</span>
          <span className="text-sm">DuckBot</span>
        </motion.button>

        {/* System Menu */}
        {showSystemMenu && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="absolute bottom-16 left-0 glass-strong rounded-lg p-3 min-w-48 border border-slate-600"
          >
            <div className="space-y-2">
              <div className="text-xs text-slate-400 font-semibold mb-2">SYSTEM</div>
              
              <button
                onClick={() => {
                  onAppOpen(desktopApps.find(app => app.id === 'system-monitor'));
                  setShowSystemMenu(false);
                }}
                className="w-full text-left px-3 py-2 rounded text-sm text-white hover:bg-slate-700 flex items-center space-x-2"
              >
                <span>📊</span>
                <span>System Monitor</span>
              </button>
              
              <button
                onClick={() => {
                  onAppOpen(desktopApps.find(app => app.id === 'service-manager'));
                  setShowSystemMenu(false);
                }}
                className="w-full text-left px-3 py-2 rounded text-sm text-white hover:bg-slate-700 flex items-center space-x-2"
              >
                <span>⚙️</span>
                <span>Services</span>
              </button>
              
              <button
                onClick={() => {
                  onAppOpen(desktopApps.find(app => app.id === 'settings'));
                  setShowSystemMenu(false);
                }}
                className="w-full text-left px-3 py-2 rounded text-sm text-white hover:bg-slate-700 flex items-center space-x-2"
              >
                <span>⚙️</span>
                <span>Settings</span>
              </button>

              <div className="border-t border-slate-600 my-2"></div>
              
              <div className="text-xs text-slate-400 font-semibold mb-2">AI TOOLS</div>
              
              <button
                onClick={() => {
                  onAppOpen(desktopApps.find(app => app.id === 'model-manager'));
                  setShowSystemMenu(false);
                }}
                className="w-full text-left px-3 py-2 rounded text-sm text-white hover:bg-slate-700 flex items-center space-x-2"
              >
                <span>🧠</span>
                <span>Model Manager</span>
              </button>
              
              <button
                onClick={() => {
                  onAppOpen(desktopApps.find(app => app.id === 'rag-manager'));
                  setShowSystemMenu(false);
                }}
                className="w-full text-left px-3 py-2 rounded text-sm text-white hover:bg-slate-700 flex items-center space-x-2"
              >
                <span>📚</span>
                <span>Knowledge Base</span>
              </button>
              
              <button
                onClick={() => {
                  onAppOpen(desktopApps.find(app => app.id === 'cost-dashboard'));
                  setShowSystemMenu(false);
                }}
                className="w-full text-left px-3 py-2 rounded text-sm text-white hover:bg-slate-700 flex items-center space-x-2"
              >
                <span>💰</span>
                <span>Cost Analytics</span>
              </button>
            </div>
          </motion.div>
        )}
      </div>

      {/* Separator */}
      <div className="w-px h-8 bg-slate-600 mx-3"></div>

      {/* App Launcher */}
      <div className="relative">
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={() => setShowAppsMenu(!showAppsMenu)}
          className="flex items-center space-x-2 px-3 py-2 rounded-lg bg-slate-700 hover:bg-slate-600 text-white"
        >
          <span>📱</span>
          <span className="text-sm">Apps</span>
        </motion.button>

        {/* Apps Menu */}
        {showAppsMenu && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="absolute bottom-16 left-0 glass-strong rounded-lg p-3 min-w-64 border border-slate-600"
          >
            <div className="grid grid-cols-3 gap-2">
              {desktopApps.map(app => (
                <button
                  key={app.id}
                  onClick={() => {
                    onAppOpen(app);
                    setShowAppsMenu(false);
                  }}
                  className="flex flex-col items-center p-2 rounded text-xs text-white hover:bg-slate-700 transition-colors"
                >
                  <span className="text-2xl mb-1">{app.icon}</span>
                  <span>{app.name}</span>
                </button>
              ))}
            </div>
          </motion.div>
        )}
      </div>

      {/* Open Apps */}
      <div className="flex-1 flex items-center space-x-1 mx-4">
        {openApps.map(app => (
          <motion.button
            key={app.id}
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            exit={{ scale: 0 }}
            onClick={() => onAppClick(app.id)}
            onContextMenu={(e) => {
              e.preventDefault();
              onAppClose(app.id);
            }}
            className={`flex items-center space-x-2 px-3 py-2 rounded-lg text-sm transition-all ${
              activeApp === app.id
                ? 'bg-blue-500/30 border border-blue-500 text-blue-300'
                : 'bg-slate-700 hover:bg-slate-600 text-white'
            }`}
          >
            <span>{app.icon}</span>
            <span className="max-w-24 truncate">{app.name}</span>
            {activeApp === app.id && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onAppClose(app.id);
                }}
                className="text-red-400 hover:text-red-300 ml-1"
              >
                ✕
              </button>
            )}
          </motion.button>
        ))}
      </div>

      {/* System Status */}
      <div className="flex items-center space-x-4">
        {/* AI Status */}
        <div className="flex items-center space-x-2 text-xs">
          <div className={`w-2 h-2 rounded-full ${isThinking ? 'bg-yellow-400 animate-pulse' : 'bg-green-400'}`}></div>
          <span className="text-slate-300">
            {currentModel ? currentModel.name.split(' ')[0] : 'No AI'}
          </span>
        </div>

        {/* Network Status */}
        <div className="flex items-center space-x-1 text-xs">
          <span>{getNetworkIcon()}</span>
          <span className={networkStatus === 'online' ? 'text-green-400' : 'text-red-400'}>
            {networkStatus}
          </span>
        </div>

        {/* System Health */}
        <div className="flex items-center space-x-1 text-xs">
          <span>💻</span>
          <span className={getSystemHealthColor()}>
            {systemStatus.status || 'Unknown'}
          </span>
        </div>

        {/* CPU Usage */}
        {systemStatus.cpu !== undefined && (
          <div className="flex items-center space-x-1 text-xs">
            <span>🔥</span>
            <span className="text-slate-300">{systemStatus.cpu}%</span>
          </div>
        )}

        {/* Memory Usage */}
        {systemStatus.memory && (
          <div className="flex items-center space-x-1 text-xs">
            <span>🧠</span>
            <span className="text-slate-300">
              {Math.round((systemStatus.memory.used / systemStatus.memory.total) * 100)}%
            </span>
          </div>
        )}

        {/* User */}
        <div className="flex items-center space-x-1 text-xs">
          <span>👤</span>
          <span className="text-slate-300">{user?.name || 'User'}</span>
        </div>

        {/* Time */}
        <div className="text-sm text-white font-mono">
          {currentTime.toLocaleTimeString()}
        </div>

        {/* Date */}
        <div className="text-xs text-slate-300">
          {currentTime.toLocaleDateString()}
        </div>
      </div>

      {/* Click outside handlers */}
      {(showSystemMenu || showAppsMenu) && (
        <div 
          className="fixed inset-0 z-[-1]" 
          onClick={() => {
            setShowSystemMenu(false);
            setShowAppsMenu(false);
          }}
        />
      )}
    </div>
  );
};

export default Taskbar;