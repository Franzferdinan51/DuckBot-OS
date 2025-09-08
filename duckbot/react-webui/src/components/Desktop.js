import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useSystem } from '../contexts/SystemContext';
import { useAI } from '../contexts/AIContext';
import { useAuth } from '../contexts/AuthContext';

// Import all applications
import Taskbar from './Taskbar';
import AIAssistant from './applications/AIAssistant';
import Avatar3D from './applications/Avatar3D';
import SystemMonitor from './applications/SystemMonitor';
import FileManager from './applications/FileManager';
import Terminal from './applications/Terminal';
import ModelManager from './applications/ModelManager';
import CostDashboard from './applications/CostDashboard';
import RAGManager from './applications/RAGManager';
import ServiceManager from './applications/ServiceManager';
import DesktopAutomation from './applications/DesktopAutomation';
import CodeEditor from './applications/CodeEditor';
import Settings from './applications/Settings';
import LogViewer from './applications/LogViewer';
import { NeuralBackground } from './NeuralBackground';

const Desktop = () => {
  const { systemStatus, getSystemHealth } = useSystem();
  const { currentModel, isThinking } = useAI();
  const { user } = useAuth();

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
      description: 'Chat with DuckBot AI models',
      autoStart: true
    },
    {
      id: 'avatar-3d',
      name: '3D Avatar',
      icon: '🦆',
      component: Avatar3D,
      category: 'ai',
      description: 'Interactive 3D AI companion with voice and animation',
      autoStart: false
    },
    {
      id: 'system-monitor',
      name: 'System Monitor',
      icon: '📊',
      component: SystemMonitor,
      category: 'system',
      description: 'Monitor system performance and health'
    },
    {
      id: 'model-manager',
      name: 'Model Manager',
      icon: '🧠',
      component: ModelManager,
      category: 'ai',
      description: 'Manage AI models and providers'
    },
    {
      id: 'service-manager',
      name: 'Services',
      icon: '⚙️',
      component: ServiceManager,
      category: 'system',
      description: 'Manage DuckBot services'
    },
    {
      id: 'rag-manager',
      name: 'Knowledge Base',
      icon: '📚',
      component: RAGManager,
      category: 'ai',
      description: 'Manage RAG knowledge base and document indexing'
    },
    {
      id: 'cost-dashboard',
      name: 'Cost Analytics',
      icon: '💰',
      component: CostDashboard,
      category: 'analytics',
      description: 'Monitor AI usage costs and analytics'
    },
    {
      id: 'desktop-automation',
      name: 'Desktop Control',
      icon: '🎯',
      component: DesktopAutomation,
      category: 'automation',
      description: 'ByteBot desktop automation and control'
    },
    {
      id: 'file-manager',
      name: 'Files',
      icon: '📁',
      component: FileManager,
      category: 'system',
      description: 'Browse and manage files'
    },
    {
      id: 'terminal',
      name: 'Terminal',
      icon: '💻',
      component: Terminal,
      category: 'dev',
      description: 'Command line interface'
    },
    {
      id: 'code-editor',
      name: 'Code Editor',
      icon: '📝',
      component: CodeEditor,
      category: 'dev',
      description: 'Advanced code editor with AI assistance'
    },
    {
      id: 'log-viewer',
      name: 'Logs',
      icon: '📋',
      component: LogViewer,
      category: 'system',
      description: 'View system and application logs'
    },
    {
      id: 'settings',
      name: 'Settings',
      icon: '⚙️',
      component: Settings,
      category: 'system',
      description: 'System configuration and preferences'
    }
  ]);

  // Window management
  const [windows, setWindows] = useState([]);
  const [nextZIndex, setNextZIndex] = useState(1000);

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
      // Bring to front
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
      maximized: false
    };

    setOpenApps(prev => [...prev, app]);
    setWindows(prev => [...prev, newWindow]);
    setActiveApp(app.id);
    setNextZIndex(prev => prev + 1);
  };

  const closeApplication = (appId) => {
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

  const minimizeWindow = (windowId) => {
    setWindows(prev => prev.map(window => 
      window.id === windowId 
        ? { ...window, minimized: !window.minimized }
        : window
    ));
  };

  const maximizeWindow = (windowId) => {
    setWindows(prev => prev.map(window => 
      window.id === windowId 
        ? { 
            ...window, 
            maximized: !window.maximized,
            x: window.maximized ? window.x : 0,
            y: window.maximized ? window.y : 0,
            width: window.maximized ? window.width : window.innerWidth,
            height: window.maximized ? window.height : window.innerHeight - 60
          }
        : window
    ));
  };

  const moveWindow = (windowId, deltaX, deltaY) => {
    setWindows(prev => prev.map(window => 
      window.id === windowId 
        ? { 
            ...window, 
            x: Math.max(0, Math.min(window.innerWidth - window.width, window.x + deltaX)),
            y: Math.max(0, Math.min(window.innerHeight - window.height, window.y + deltaY))
          }
        : window
    ));
  };

  const resizeWindow = (windowId, deltaWidth, deltaHeight) => {
    setWindows(prev => prev.map(window => 
      window.id === windowId 
        ? { 
            ...window, 
            width: Math.max(400, Math.min(window.innerWidth, window.width + deltaWidth)),
            height: Math.max(300, Math.min(window.innerHeight - 60, window.height + deltaHeight))
          }
        : window
    ));
  };

  return (
    <div className="desktop gradient-bg-primary grid-bg h-screen w-screen overflow-hidden relative">
      {/* Neural Network Background */}
      <NeuralBackground />
      
      {/* Desktop Grid */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="grid grid-cols-12 gap-4 p-8 h-full">
          {/* Desktop Apps Grid */}
          <div className="col-span-2 space-y-6">
            {desktopApps
              .filter(app => app.category === 'ai')
              .map(app => (
                <DesktopIcon
                  key={app.id}
                  app={app}
                  isOpen={openApps.some(a => a.id === app.id)}
                  onClick={() => openApplication(app)}
                />
              ))}
            
            <div className="text-xs text-slate-400 font-semibold mt-8 mb-2">SYSTEM</div>
            {desktopApps
              .filter(app => app.category === 'system')
              .map(app => (
                <DesktopIcon
                  key={app.id}
                  app={app}
                  isOpen={openApps.some(a => a.id === app.id)}
                  onClick={() => openApplication(app)}
                />
              ))}
            
            <div className="text-xs text-slate-400 font-semibold mt-8 mb-2">DEVELOPMENT</div>
            {desktopApps
              .filter(app => app.category === 'dev')
              .map(app => (
                <DesktopIcon
                  key={app.id}
                  app={app}
                  isOpen={openApps.some(a => a.id === app.id)}
                  onClick={() => openApplication(app)}
                />
              ))}
            
            <div className="text-xs text-slate-400 font-semibold mt-8 mb-2">AUTOMATION</div>
            {desktopApps
              .filter(app => app.category === 'automation')
              .map(app => (
                <DesktopIcon
                  key={app.id}
                  app={app}
                  isOpen={openApps.some(a => a.id === app.id)}
                  onClick={() => openApplication(app)}
                />
              ))}
          </div>
          
          {/* Main Desktop Area */}
          <div className="col-span-10 relative">
            {/* System Status Widget */}
            <SystemStatusWidget />
            
            {/* AI Status Widget */}
            <AIStatusWidget />
          </div>
        </div>
      </div>

      {/* Windows */}
      <AnimatePresence>
        {windows.map(window => (
          <WindowContainer
            key={window.id}
            window={window}
            isActive={activeApp === window.id}
            onFocus={() => focusWindow(window.id)}
            onClose={() => closeApplication(window.id)}
            onMinimize={() => minimizeWindow(window.id)}
            onMaximize={() => maximizeWindow(window.id)}
            onMove={(deltaX, deltaY) => moveWindow(window.id, deltaX, deltaY)}
            onResize={(deltaWidth, deltaHeight) => resizeWindow(window.id, deltaWidth, deltaHeight)}
          />
        ))}
      </AnimatePresence>

      {/* Taskbar */}
      <Taskbar 
        openApps={openApps}
        activeApp={activeApp}
        onAppClick={focusWindow}
        onAppClose={closeApplication}
        desktopApps={desktopApps}
        onAppOpen={openApplication}
      />
    </div>
  );
};

// Desktop Icon Component
const DesktopIcon = ({ app, isOpen, onClick }) => (
  <motion.div
    className={`desktop-icon pointer-events-auto cursor-pointer group ${
      isOpen ? 'opacity-80' : ''
    }`}
    whileHover={{ scale: 1.05 }}
    whileTap={{ scale: 0.95 }}
    onClick={onClick}
  >
    <div className="glass-strong rounded-xl p-4 text-center transition-all duration-200 group-hover:neon-blue">
      <div className="text-2xl mb-2">{app.icon}</div>
      <div className="text-xs font-medium text-white">{app.name}</div>
    </div>
  </motion.div>
);

// System Status Widget
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
        {systemStatus.gpu > 0 && (
          <div className="flex justify-between">
            <span className="text-slate-300">GPU</span>
            <span className="text-white">{systemStatus.gpu}%</span>
          </div>
        )}
      </div>
    </motion.div>
  );
};

// AI Status Widget
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
          <span className="text-slate-300">LM Studio</span>
          <span className={`text-white ${
            providers.lmStudio.status === 'connected' ? 'text-green-400' :
            providers.lmStudio.status === 'error' ? 'text-red-400' : 'text-slate-400'
          }`}>
            {providers.lmStudio.status}
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-slate-300">OpenRouter</span>
          <span className={`text-white ${
            providers.openRouter.status === 'connected' ? 'text-green-400' :
            providers.openRouter.status === 'free-mode' ? 'text-blue-400' :
            providers.openRouter.status === 'error' ? 'text-red-400' : 'text-slate-400'
          }`}>
            {providers.openRouter.status}
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-slate-300">Status</span>
          <span className="text-white">{isThinking ? 'Thinking...' : 'Ready'}</span>
        </div>
      </div>
    </motion.div>
  );
};

// Window Container Component
const WindowContainer = ({ 
  window, 
  isActive, 
  onFocus, 
  onClose, 
  onMinimize, 
  onMaximize, 
  onMove, 
  onResize 
}) => {
  const dragRef = useRef(null);
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });

  const Component = window.component;

  if (window.minimized) return null;

  return (
    <motion.div
      initial={{ scale: 0.8, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      exit={{ scale: 0.8, opacity: 0 }}
      className={`window-container absolute glass-strong rounded-lg overflow-hidden shadow-2xl ${
        isActive ? 'neon-blue' : ''
      }`}
      style={{
        left: window.x,
        top: window.y,
        width: window.width,
        height: window.height,
        zIndex: window.zIndex
      }}
      onClick={onFocus}
    >
      {/* Window Header */}
      <div
        ref={dragRef}
        className="window-header bg-slate-800/90 px-4 py-2 flex items-center justify-between cursor-move border-b border-slate-600"
        onMouseDown={(e) => {
          setIsDragging(true);
          setDragStart({ x: e.clientX - window.x, y: e.clientY - window.y });
        }}
      >
        <div className="flex items-center space-x-2">
          <span className="text-lg">{window.icon}</span>
          <span className="text-sm font-medium text-white">{window.title}</span>
        </div>
        
        <div className="flex items-center space-x-1">
          <button
            onClick={(e) => { e.stopPropagation(); onMinimize(); }}
            className="w-6 h-6 rounded bg-yellow-500 hover:bg-yellow-600 flex items-center justify-center text-black text-xs"
          >
            −
          </button>
          <button
            onClick={(e) => { e.stopPropagation(); onMaximize(); }}
            className="w-6 h-6 rounded bg-green-500 hover:bg-green-600 flex items-center justify-center text-black text-xs"
          >
            □
          </button>
          <button
            onClick={(e) => { e.stopPropagation(); onClose(); }}
            className="w-6 h-6 rounded bg-red-500 hover:bg-red-600 flex items-center justify-center text-white text-xs"
          >
            ✕
          </button>
        </div>
      </div>
      
      {/* Window Content */}
      <div className="window-content h-full bg-slate-900/95">
        <Component onClose={onClose} />
      </div>
    </motion.div>
  );
};

export default Desktop;