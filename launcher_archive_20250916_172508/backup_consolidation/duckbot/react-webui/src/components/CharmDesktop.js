import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useSystem } from '../contexts/SystemContext';
import { useAI } from '../contexts/AIContext';
import { useAuth } from '../contexts/AuthContext';

// Import Charm ecosystem components
import { 
  CharmInterface, 
  CharmBox, 
  CharmText, 
  GumSelect, 
  GumInput, 
  CharmLogger,
  useCharmState,
  CharmColors 
} from './CharmInterface';

// Import all applications
import Taskbar from './Taskbar';
import AIAssistant from './applications/AIAssistant';
import Avatar3D from './applications/Avatar3D';
import SystemMonitor from './applications/SystemMonitor';
import FileManager from './applications/FileManager';
import Terminal from './applications/Terminal';
import { NeuralBackground } from './NeuralBackground';

const CharmDesktop = () => {
  const { systemStatus, getSystemHealth } = useSystem();
  const { currentModel, isThinking } = useAI();
  const { user } = useAuth();

  // Charm-enhanced desktop state
  const [charmMode, setCharmMode] = useCharmState('charm_mode', true);
  const [currentView, setCurrentView] = useCharmState('desktop_view', 'desktop');
  const [systemLogs, setSystemLogs] = useCharmState('system_logs', []);
  const [notifications, setNotifications] = useCharmState('notifications', []);
  
  // Desktop state
  const [openApps, setOpenApps] = useState([]);
  const [activeApp, setActiveApp] = useState(null);
  const [desktopApps] = useState([
    {
      id: 'ai-assistant',
      name: 'AI Assistant',
      icon: '🤖',
      component: AIAssistant,
      category: 'ai',
      description: 'Chat with DuckBot AI with full Charm UI integration',
      autoStart: true,
      charmEnabled: true
    },
    {
      id: 'avatar-3d',
      name: '3D Avatar',
      icon: '🦆',
      component: Avatar3D,
      category: 'ai',
      description: 'Interactive 3D AI companion with Charm animations',
      autoStart: false,
      charmEnabled: true
    },
    {
      id: 'system-monitor',
      name: 'System Monitor',
      icon: '📊',
      component: SystemMonitor,
      category: 'system',
      description: 'Beautiful system monitoring with Charm components',
      charmEnabled: true
    },
    {
      id: 'charm-terminal',
      name: 'Charm Terminal',
      icon: '💻',
      component: CharmTerminalApp,
      category: 'dev',
      description: 'Full Charm ecosystem terminal interface',
      charmEnabled: true
    },
    {
      id: 'file-manager',
      name: 'Files',
      icon: '📁',
      component: FileManager,
      category: 'system',
      description: 'File management with Charm styling'
    },
    {
      id: 'settings',
      name: 'Settings',
      icon: '⚙️',
      component: CharmSettingsApp,
      category: 'system',
      description: 'System configuration with Charm interface',
      charmEnabled: true
    }
  ]);

  // Window management
  const [windows, setWindows] = useState([]);
  const [nextZIndex, setNextZIndex] = useState(1000);

  // System monitoring with Charm logging
  useEffect(() => {
    const interval = setInterval(() => {
      const health = getSystemHealth();
      const timestamp = new Date().toISOString();
      
      if (health.overall !== 'excellent') {
        addLog({
          level: health.overall === 'good' ? 'warn' : 'error',
          message: `System health: ${health.overall} (${health.runningServices}/${health.totalServices} services)`,
          timestamp
        });
      }
      
      // Add CPU/Memory warnings
      if (systemStatus.cpu > 80) {
        addLog({
          level: 'warn',
          message: `High CPU usage: ${systemStatus.cpu}%`,
          timestamp
        });
      }
      
      const memoryPercent = (systemStatus.memory.used / systemStatus.memory.total) * 100;
      if (memoryPercent > 85) {
        addLog({
          level: 'warn',
          message: `High memory usage: ${Math.round(memoryPercent)}%`,
          timestamp
        });
      }
    }, 5000);
    
    return () => clearInterval(interval);
  }, [systemStatus]);

  const addLog = (log) => {
    setSystemLogs(prev => [...prev.slice(-99), log]); // Keep last 100 logs
  };

  const addNotification = (notification) => {
    const id = Date.now().toString();
    const newNotification = { id, ...notification, timestamp: new Date().toISOString() };
    setNotifications(prev => [...prev, newNotification]);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
      setNotifications(prev => prev.filter(n => n.id !== id));
    }, 5000);
  };

  // Auto-start essential applications
  useEffect(() => {
    const autoStartApps = desktopApps.filter(app => app.autoStart);
    autoStartApps.forEach(app => {
      if (!openApps.find(a => a.id === app.id)) {
        openApplication(app);
      }
    });
  }, []);

  const openApplication = (app) => {
    const existingApp = openApps.find(a => a.id === app.id);
    
    if (existingApp) {
      focusWindow(app.id);
      return;
    }

    const newWindow = {
      id: app.id,
      title: app.name,
      component: app.component,
      icon: app.icon,
      zIndex: nextZIndex,
      x: Math.random() * 200 + 100,
      y: Math.random() * 100 + 80,
      width: 900,
      height: 600,
      minimized: false,
      maximized: false,
      charmEnabled: app.charmEnabled || false
    };

    setOpenApps(prev => [...prev, app]);
    setWindows(prev => [...prev, newWindow]);
    setActiveApp(app.id);
    setNextZIndex(prev => prev + 1);
    
    addLog({
      level: 'info',
      message: `Opened application: ${app.name}`,
      timestamp: new Date().toISOString()
    });
  };

  const closeApplication = (appId) => {
    const app = openApps.find(a => a.id === appId);
    
    setOpenApps(prev => prev.filter(app => app.id !== appId));
    setWindows(prev => prev.filter(window => window.id !== appId));
    
    if (activeApp === appId) {
      const remainingWindows = windows.filter(w => w.id !== appId);
      if (remainingWindows.length > 0) {
        const topWindow = remainingWindows.reduce((prev, current) => 
          prev.zIndex > current.zIndex ? prev : current
        );
        setActiveApp(topWindow.id);
      } else {
        setActiveApp(null);
      }
    }
    
    if (app) {
      addLog({
        level: 'info',
        message: `Closed application: ${app.name}`,
        timestamp: new Date().toISOString()
      });
    }
  };

  const focusWindow = (windowId) => {
    const newZIndex = nextZIndex;
    setWindows(prev => prev.map(window => 
      window.id === windowId 
        ? { ...window, zIndex: newZIndex, minimized: false }
        : window
    ));
    setActiveApp(windowId);
    setNextZIndex(prev => prev + 1);
  };

  const toggleCharmMode = () => {
    setCharmMode(!charmMode);
    addNotification({
      type: 'info',
      title: 'Interface Mode',
      message: `Switched to ${!charmMode ? 'Charm' : 'Standard'} interface mode`,
    });
  };

  // Render views
  const renderDesktopView = () => (
    <div className="desktop gradient-bg-primary grid-bg h-screen w-screen overflow-hidden relative">
      <NeuralBackground />
      
      {/* Charm Mode Toggle */}
      <motion.div 
        className="absolute top-4 left-4 z-50"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
      >
        <CharmBox border={true} theme="accent" padding={true}>
          <div className="flex items-center gap-3">
            <CharmText variant="small" theme="muted">Interface:</CharmText>
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={toggleCharmMode}
              className="px-3 py-1 rounded font-mono text-sm font-medium transition-colors duration-150"
              style={{
                backgroundColor: charmMode ? CharmColors.accent : CharmColors.muted,
                color: CharmColors.background,
              }}
            >
              {charmMode ? '🎨 Charm' : '📱 Standard'}
            </motion.button>
          </div>
        </CharmBox>
      </motion.div>
      
      {/* Desktop Grid */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="grid grid-cols-12 gap-4 p-8 h-full">
          {/* Charm-enhanced Desktop Apps Grid */}
          <div className="col-span-2 space-y-6">
            <CharmAppCategory 
              title="🤖 AI TOOLS" 
              apps={desktopApps.filter(app => app.category === 'ai')}
              openApps={openApps}
              onAppOpen={openApplication}
              charmMode={charmMode}
            />
            
            <CharmAppCategory 
              title="⚙️ SYSTEM" 
              apps={desktopApps.filter(app => app.category === 'system')}
              openApps={openApps}
              onAppOpen={openApplication}
              charmMode={charmMode}
            />
            
            <CharmAppCategory 
              title="💻 DEVELOPMENT" 
              apps={desktopApps.filter(app => app.category === 'dev')}
              openApps={openApps}
              onAppOpen={openApplication}
              charmMode={charmMode}
            />
          </div>
          
          {/* Main Desktop Area */}
          <div className="col-span-10 relative">
            {charmMode ? (
              <>
                <CharmSystemStatus />
                <CharmAIStatus />
                <CharmNotifications notifications={notifications} />
              </>
            ) : (
              <>
                <SystemStatusWidget />
                <AIStatusWidget />
              </>
            )}
          </div>
        </div>
      </div>

      {/* Windows */}
      <AnimatePresence>
        {windows.map(window => (
          <CharmWindowContainer
            key={window.id}
            window={window}
            isActive={activeApp === window.id}
            charmMode={charmMode}
            onFocus={() => focusWindow(window.id)}
            onClose={() => closeApplication(window.id)}
          />
        ))}
      </AnimatePresence>

      {/* Enhanced Taskbar */}
      <Taskbar 
        openApps={openApps}
        activeApp={activeApp}
        onAppClick={focusWindow}
        onAppClose={closeApplication}
        desktopApps={desktopApps}
        onAppOpen={openApplication}
        charmMode={charmMode}
      />
    </div>
  );

  const renderSystemView = () => (
    <CharmInterface
      title="System Overview"
      subtitle="Complete system monitoring and management"
      onBack={() => setCurrentView('desktop')}
      actions={[
        { icon: '🔄', label: 'Refresh', onClick: () => window.location.reload() },
        { icon: '⚙️', label: 'Settings', onClick: () => setCurrentView('settings') }
      ]}
    >
      <div className="grid grid-cols-2 gap-6">
        <CharmSystemStatus expanded={true} />
        <CharmLogger 
          logs={systemLogs} 
          onClear={() => setSystemLogs([])} 
        />
      </div>
    </CharmInterface>
  );

  // Main render logic
  if (!charmMode) {
    // Fallback to standard desktop when Charm mode is disabled
    return renderDesktopView();
  }

  switch (currentView) {
    case 'system':
      return renderSystemView();
    case 'settings':
      return (
        <CharmInterface
          title="Settings"
          subtitle="Configure your DuckBot experience"
          onBack={() => setCurrentView('desktop')}
        >
          <CharmSettingsContent />
        </CharmInterface>
      );
    default:
      return renderDesktopView();
  }
};

// Charm-enhanced components
const CharmAppCategory = ({ title, apps, openApps, onAppOpen, charmMode }) => (
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    className="space-y-3"
  >
    <CharmText variant="small" theme="accent" style={{ textTransform: 'uppercase', letterSpacing: '0.05em' }}>
      {title}
    </CharmText>
    {apps.map(app => (
      <CharmDesktopIcon
        key={app.id}
        app={app}
        isOpen={openApps.some(a => a.id === app.id)}
        onClick={() => onAppOpen(app)}
        charmMode={charmMode}
      />
    ))}
  </motion.div>
);

const CharmDesktopIcon = ({ app, isOpen, onClick, charmMode }) => (
  <motion.div
    className="pointer-events-auto cursor-pointer group"
    whileHover={{ scale: 1.05 }}
    whileTap={{ scale: 0.95 }}
    onClick={onClick}
  >
    <CharmBox
      border={true}
      theme={app.charmEnabled ? "primary" : "muted"}
      style={{
        background: isOpen 
          ? `${CharmColors.primary}20` 
          : 'transparent',
        borderWidth: '1px',
        padding: '0.75rem',
        transition: 'all 0.2s ease',
      }}
    >
      <div className="flex items-center gap-3">
        <span className="text-lg">{app.icon}</span>
        <div>
          <CharmText variant="small" theme="text" style={{ fontWeight: '500' }}>
            {app.name}
          </CharmText>
          {app.charmEnabled && (
            <div className="flex items-center gap-1">
              <span style={{ color: CharmColors.accent, fontSize: '0.6rem' }}>✨</span>
              <CharmText variant="small" theme="accent" style={{ fontSize: '0.6rem' }}>
                CHARM
              </CharmText>
            </div>
          )}
        </div>
      </div>
    </CharmBox>
  </motion.div>
);

const CharmSystemStatus = ({ expanded = false }) => {
  const { systemStatus, getSystemHealth } = useSystem();
  const health = getSystemHealth();
  
  return (
    <motion.div
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      className="absolute top-4 right-4 pointer-events-auto"
    >
      <CharmBox border={true} theme="secondary" padding={true}>
        <div className="flex items-center gap-3 mb-3">
          <CharmText variant="h3" theme="secondary">
            📊 System Status
          </CharmText>
          <motion.div
            animate={{ scale: [1, 1.2, 1] }}
            transition={{ duration: 2, repeat: Infinity }}
            className="w-3 h-3 rounded-full"
            style={{
              backgroundColor: health.overall === 'excellent' ? CharmColors.success :
                              health.overall === 'good' ? CharmColors.warning :
                              health.overall === 'poor' ? CharmColors.accent : CharmColors.error
            }}
          />
        </div>
        
        <div className="space-y-2 font-mono text-sm min-w-48">
          <div className="flex justify-between">
            <CharmText variant="small" theme="muted">Services</CharmText>
            <CharmText variant="small" theme="text">
              {health.runningServices}/{health.totalServices}
            </CharmText>
          </div>
          <div className="flex justify-between">
            <CharmText variant="small" theme="muted">CPU</CharmText>
            <CharmText variant="small" theme={systemStatus.cpu > 80 ? "error" : "text"}>
              {systemStatus.cpu}%
            </CharmText>
          </div>
          <div className="flex justify-between">
            <CharmText variant="small" theme="muted">Memory</CharmText>
            <CharmText variant="small" theme="text">
              {Math.round((systemStatus.memory.used / systemStatus.memory.total) * 100)}%
            </CharmText>
          </div>
          {systemStatus.gpu > 0 && (
            <div className="flex justify-between">
              <CharmText variant="small" theme="muted">GPU</CharmText>
              <CharmText variant="small" theme="text">
                {systemStatus.gpu}%
              </CharmText>
            </div>
          )}
        </div>
      </CharmBox>
    </motion.div>
  );
};

const CharmAIStatus = () => {
  const { currentModel, isThinking, providers } = useAI();
  
  return (
    <motion.div
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.1 }}
      className="absolute top-4 right-72 pointer-events-auto"
    >
      <CharmBox border={true} theme="primary" padding={true}>
        <div className="flex items-center gap-3 mb-3">
          <CharmText variant="h3" theme="primary">
            🤖 AI Status
          </CharmText>
          <motion.div
            animate={{ 
              scale: isThinking ? [1, 1.3, 1] : [1],
              backgroundColor: isThinking ? [CharmColors.warning, CharmColors.accent, CharmColors.warning] : [CharmColors.success]
            }}
            transition={{ duration: isThinking ? 0.5 : 0, repeat: isThinking ? Infinity : 0 }}
            className="w-3 h-3 rounded-full"
          />
        </div>
        
        <div className="space-y-2 font-mono text-sm min-w-48">
          <div className="flex justify-between">
            <CharmText variant="small" theme="muted">Model</CharmText>
            <CharmText variant="small" theme="text" style={{ maxWidth: '120px' }}>
              {currentModel?.name || 'None'}
            </CharmText>
          </div>
          <div className="flex justify-between">
            <CharmText variant="small" theme="muted">LM Studio</CharmText>
            <CharmText variant="small" theme={
              providers.lmStudio?.status === 'connected' ? 'success' :
              providers.lmStudio?.status === 'error' ? 'error' : 'muted'
            }>
              {providers.lmStudio?.status || 'unknown'}
            </CharmText>
          </div>
          <div className="flex justify-between">
            <CharmText variant="small" theme="muted">OpenRouter</CharmText>
            <CharmText variant="small" theme={
              providers.openRouter?.status === 'connected' ? 'success' :
              providers.openRouter?.status === 'free-mode' ? 'info' :
              providers.openRouter?.status === 'error' ? 'error' : 'muted'
            }>
              {providers.openRouter?.status || 'unknown'}
            </CharmText>
          </div>
          <div className="flex justify-between">
            <CharmText variant="small" theme="muted">Status</CharmText>
            <CharmText variant="small" theme={isThinking ? "accent" : "success"}>
              {isThinking ? 'Thinking...' : 'Ready'}
            </CharmText>
          </div>
        </div>
      </CharmBox>
    </motion.div>
  );
};

const CharmNotifications = ({ notifications }) => (
  <div className="absolute top-4 left-4 space-y-2 pointer-events-auto z-40">
    <AnimatePresence>
      {notifications.map(notification => (
        <motion.div
          key={notification.id}
          initial={{ opacity: 0, x: -100 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -100 }}
          transition={{ type: "spring", stiffness: 300, damping: 30 }}
        >
          <CharmBox border={true} theme="accent" padding={true}>
            <div className="flex items-center gap-3 min-w-64">
              <span className="text-lg">
                {notification.type === 'error' ? '❌' : 
                 notification.type === 'warning' ? '⚠️' : 
                 notification.type === 'success' ? '✅' : 'ℹ️'}
              </span>
              <div>
                <CharmText variant="small" theme="text" style={{ fontWeight: '600' }}>
                  {notification.title}
                </CharmText>
                <CharmText variant="small" theme="muted">
                  {notification.message}
                </CharmText>
              </div>
            </div>
          </CharmBox>
        </motion.div>
      ))}
    </AnimatePresence>
  </div>
);

const CharmWindowContainer = ({ window, isActive, charmMode, onFocus, onClose }) => {
  const Component = window.component;

  if (window.minimized) return null;

  return (
    <motion.div
      initial={{ scale: 0.8, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      exit={{ scale: 0.8, opacity: 0 }}
      className={`absolute overflow-hidden shadow-2xl ${
        charmMode ? '' : 'glass-strong rounded-lg'
      }`}
      style={{
        left: window.x,
        top: window.y,
        width: window.width,
        height: window.height,
        zIndex: window.zIndex,
        ...(charmMode && {
          backgroundColor: CharmColors.surface,
          border: `2px solid ${isActive ? CharmColors.primary : CharmColors.border}`,
          borderRadius: '12px',
        })
      }}
      onClick={onFocus}
    >
      {/* Charm Window Header */}
      {charmMode ? (
        <div 
          className="px-4 py-3 flex items-center justify-between cursor-move border-b"
          style={{ 
            backgroundColor: CharmColors.background,
            borderColor: CharmColors.border 
          }}
        >
          <div className="flex items-center gap-3">
            <span className="text-lg">{window.icon}</span>
            <CharmText variant="body" theme="text" style={{ fontWeight: '500' }}>
              {window.title}
            </CharmText>
            {window.charmEnabled && (
              <div className="flex items-center gap-1">
                <span style={{ color: CharmColors.accent, fontSize: '0.75rem' }}>✨</span>
                <CharmText variant="small" theme="accent" style={{ fontSize: '0.75rem' }}>
                  CHARM
                </CharmText>
              </div>
            )}
          </div>
          
          <div className="flex items-center gap-2">
            <motion.button
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
              onClick={(e) => { e.stopPropagation(); onClose(); }}
              className="w-8 h-8 rounded-full flex items-center justify-center font-mono font-bold transition-colors duration-150"
              style={{
                backgroundColor: CharmColors.error,
                color: CharmColors.background,
              }}
            >
              ✕
            </motion.button>
          </div>
        </div>
      ) : (
        <div className="window-header bg-slate-800/90 px-4 py-2 flex items-center justify-between cursor-move border-b border-slate-600">
          <div className="flex items-center space-x-2">
            <span className="text-lg">{window.icon}</span>
            <span className="text-sm font-medium text-white">{window.title}</span>
          </div>
          <div className="flex items-center space-x-1">
            <button
              onClick={(e) => { e.stopPropagation(); onClose(); }}
              className="w-6 h-6 rounded bg-red-500 hover:bg-red-600 flex items-center justify-center text-white text-xs"
            >
              ✕
            </button>
          </div>
        </div>
      )}
      
      {/* Window Content */}
      <div className="h-full" style={{ 
        backgroundColor: charmMode ? CharmColors.background : 'rgba(15, 23, 42, 0.95)'
      }}>
        {window.charmEnabled && charmMode ? (
          <div style={{ backgroundColor: CharmColors.background, height: '100%', padding: '1rem' }}>
            <Component onClose={onClose} charmMode={true} />
          </div>
        ) : (
          <Component onClose={onClose} />
        )}
      </div>
    </motion.div>
  );
};

// Placeholder components for Charm-enhanced apps
const CharmTerminalApp = ({ charmMode, onClose }) => (
  <CharmInterface
    title="Charm Terminal"
    subtitle="Full ecosystem terminal interface"
    onBack={onClose}
  >
    <CharmBox border={true} theme="primary">
      <CharmText variant="h2" theme="primary">
        🚀 Charm Terminal Interface
      </CharmText>
      <CharmText variant="body" theme="text">
        This is where the full Charm ecosystem terminal interface would be integrated,
        connecting to the Python charm_ecosystem.py and charm_terminal_ui.py components.
      </CharmText>
    </CharmBox>
  </CharmInterface>
);

const CharmSettingsApp = ({ charmMode, onClose }) => (
  <CharmInterface
    title="Settings"
    subtitle="Configure your DuckBot experience"
    onBack={onClose}
  >
    <CharmSettingsContent />
  </CharmInterface>
);

const CharmSettingsContent = () => {
  const [settings, setSettings] = useCharmState('app_settings', {
    theme: 'dark',
    animations: true,
    notifications: true,
    autoStart: true,
  });

  return (
    <div className="space-y-6">
      <CharmBox border={true} theme="secondary">
        <CharmText variant="h3" theme="secondary">🎨 Interface</CharmText>
        <div className="space-y-4 mt-4">
          <GumSelect
            label="Theme"
            options={[
              { label: 'Dark Theme', value: 'dark' },
              { label: 'Light Theme', value: 'light' },
              { label: 'Auto', value: 'auto' }
            ]}
            onSelect={(option) => setSettings({ ...settings, theme: option.value })}
            theme="secondary"
          />
          
          <div className="flex items-center gap-3">
            <input
              type="checkbox"
              id="animations"
              checked={settings.animations}
              onChange={(e) => setSettings({ ...settings, animations: e.target.checked })}
              style={{ accentColor: CharmColors.secondary }}
            />
            <label htmlFor="animations" style={{ color: CharmColors.text }}>
              Enable animations
            </label>
          </div>
        </div>
      </CharmBox>
      
      <CharmBox border={true} theme="accent">
        <CharmText variant="h3" theme="accent">🔔 Notifications</CharmText>
        <div className="space-y-4 mt-4">
          <div className="flex items-center gap-3">
            <input
              type="checkbox"
              id="notifications"
              checked={settings.notifications}
              onChange={(e) => setSettings({ ...settings, notifications: e.target.checked })}
              style={{ accentColor: CharmColors.accent }}
            />
            <label htmlFor="notifications" style={{ color: CharmColors.text }}>
              Enable system notifications
            </label>
          </div>
        </div>
      </CharmBox>
    </div>
  );
};

// Legacy components (kept for compatibility)
const SystemStatusWidget = () => {
  const { systemStatus, getSystemHealth } = useSystem();
  const health = getSystemHealth();
  
  return (
    <motion.div
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      className="absolute top-4 right-4 glass-strong rounded-lg p-4 min-w-64 pointer-events-auto"
    >
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-white">System Status</h3>
        <div className={`w-3 h-3 rounded-full ${
          health.overall === 'excellent' ? 'bg-green-400' :
          health.overall === 'good' ? 'bg-yellow-400' :
          health.overall === 'poor' ? 'bg-orange-400' : 'bg-red-400'
        }`} />
      </div>
      
      <div className="space-y-2 text-xs">
        <div className="flex justify-between">
          <span className="text-slate-300">Services</span>
          <span className="text-white">{health.runningServices}/{health.totalServices}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-slate-300">CPU</span>
          <span className="text-white">{systemStatus.cpu}%</span>
        </div>
        <div className="flex justify-between">
          <span className="text-slate-300">Memory</span>
          <span className="text-white">{Math.round((systemStatus.memory.used / systemStatus.memory.total) * 100)}%</span>
        </div>
      </div>
    </motion.div>
  );
};

const AIStatusWidget = () => {
  const { currentModel, isThinking, providers } = useAI();
  
  return (
    <motion.div
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.1 }}
      className="absolute top-4 right-72 glass-strong rounded-lg p-4 min-w-64 pointer-events-auto"
    >
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-white">AI Status</h3>
        <div className={`w-3 h-3 rounded-full ${isThinking ? 'bg-yellow-400 animate-pulse' : 'bg-green-400'}`} />
      </div>
      
      <div className="space-y-2 text-xs">
        <div className="flex justify-between">
          <span className="text-slate-300">Model</span>
          <span className="text-white truncate max-w-32">{currentModel?.name || 'None'}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-slate-300">Status</span>
          <span className="text-white">{isThinking ? 'Thinking...' : 'Ready'}</span>
        </div>
      </div>
    </motion.div>
  );
};

export default CharmDesktop;