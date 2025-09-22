import React from 'react';
import { AppDefinition } from './types';
import { ThreeScene } from '../components/ThreeScene';
import GitHubRepositoryManager from '../GitHubRepositoryManager';
import ChatUIApp from './ChatUIApp';
// import GeminiChat from '../applications/GeminiChat'; // Temporarily disabled due to parsing issue
import { Brain, GitBranch, MessageSquare, Cpu, HardDrive, Network, Palette, Code, Terminal, Zap, Settings, Gamepad2, Music, Camera, Calendar, Calculator, Globe, FileText, Image, Video, Database, Shield, Monitor, Smartphone, Cloud, Download, Upload, Star, Clock, TrendingUp, Users, Sparkles } from 'lucide-react';

// Icon Components for DuckBotOS
export const DuckBotIcon: React.FC<{ className?: string }> = ({ className }) => (
  <div className={className}>
    <Brain className="w-full h-full text-yellow-400" />
  </div>
);

export const AssistantIcon: React.FC<{ className?: string }> = ({ className }) => (
  <div className={className}>
    <MessageSquare className="w-full h-full text-blue-400" />
  </div>
);

export const GitHubIcon: React.FC<{ className?: string }> = ({ className }) => (
  <div className={className}>
    <GitBranch className="w-full h-full text-green-400" />
  </div>
);

export const AIBrainIcon: React.FC<{ className?: string }> = ({ className }) => (
  <div className={className}>
    <Brain className="w-full h-full text-purple-400" />
  </div>
);

export const SystemMonitorIcon: React.FC<{ className?: string }> = ({ className }) => (
  <div className={className}>
    <Cpu className="w-full h-full text-red-400" />
  </div>
);

export const FileManagerIcon: React.FC<{ className?: string }> = ({ className }) => (
  <div className={className}>
    <HardDrive className="w-full h-full text-orange-400" />
  </div>
);

export const NetworkIcon: React.FC<{ className?: string }> = ({ className }) => (
  <div className={className}>
    <Network className="w-full h-full text-cyan-400" />
  </div>
);

export const SettingsIcon: React.FC<{ className?: string }> = ({ className }) => (
  <div className={className}>
    <Palette className="w-full h-full text-pink-400" />
  </div>
);

export const CodeEditorIcon: React.FC<{ className?: string }> = ({ className }) => (
  <div className={className}>
    <Code className="w-full h-full text-teal-400" />
  </div>
);

export const TerminalIcon: React.FC<{ className?: string }> = ({ className }) => (
  <div className={className}>
    <Terminal className="w-full h-full text-gray-400" />
  </div>
);

export const LauncherIcon: React.FC<{ className?: string }> = ({ className }) => (
  <div className={className}>
    <Zap className="w-full h-full text-yellow-400" />
  </div>
);

export const QuickSettingsIcon: React.FC<{ className?: string }> = ({ className }) => (
  <div className={className}>
    <Settings className="w-full h-full text-gray-300" />
  </div>
);

export const GeminiIcon: React.FC<{ className?: string }> = ({ className }) => (
  <div className={className}>
    <Sparkles className="w-full h-full text-purple-400" />
  </div>
);

// App Components
const ThreeAssistantApp: React.FC = () => {
  const [isModelLoaded, setIsModelLoaded] = React.useState(false);
  const [loadProgress, setLoadProgress] = React.useState(0);
  const [morphTargetDictionary, setMorphTargetDictionary] = React.useState<any>(null);
  const [interactionCount, setInteractionCount] = React.useState(0);
  const sceneRef = React.useRef<any>(null);

  const handleModelLoad = React.useCallback((dictionary: any) => {
    setIsModelLoaded(true);
    setMorphTargetDictionary(dictionary);
  }, []);

  const handleLoadProgress = React.useCallback((progress: number) => {
    setLoadProgress(progress);
  }, []);

  const handleInteraction = React.useCallback(() => {
    setInteractionCount(prev => prev + 1);
  }, []);

  return (
    <div className="w-full h-full bg-gradient-to-b from-gray-800 to-gray-900 relative">
      {/* Loading overlay */}
      {!isModelLoaded && (
        <div className="absolute inset-0 z-20 flex items-center justify-center bg-black bg-opacity-75">
          <div className="text-center">
            <div className="text-white text-xl font-semibold mb-2">
              Loading 3D Assistant...
            </div>
            <div className="text-yellow-400 text-lg">
              {loadProgress}%
            </div>
            <div className="text-gray-400 text-sm mt-2">
              Your 3D AI assistant is getting ready
            </div>
          </div>
        </div>
      )}

      {/* Controls overlay */}
      {isModelLoaded && (
        <div className="absolute top-4 left-4 z-10">
          <div className="bg-gray-800/80 backdrop-blur-sm rounded-lg p-3 border border-gray-700">
            <h3 className="text-white text-sm font-semibold mb-2">3D Assistant Controls</h3>
            <div className="space-y-1 text-xs text-gray-300">
              <div>• Click and drag to rotate view</div>
              <div>• Scroll to zoom in/out</div>
              <div>• Interactions: {interactionCount}</div>
            </div>
          </div>
        </div>
      )}

      {/* 3D Scene */}
      <ThreeScene ref={sceneRef} onModelLoad={handleModelLoad} onLoadProgress={handleLoadProgress} />

      {/* Interaction area overlay */}
      {isModelLoaded && (
        <div className="absolute bottom-4 right-4 z-10">
          <button
            onClick={handleInteraction}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
          >
            Interact with Assistant
          </button>
        </div>
      )}
    </div>
  );
};

const ChatApp: React.FC = () => {
  const [isLoading, setIsLoading] = React.useState(false);
  const [isListening, setIsListening] = React.useState(false);

  const handleSend = React.useCallback(async (msg: string) => {
    setIsLoading(true);
    try {
      // Simulate AI response
      await new Promise(resolve => setTimeout(resolve, 1000));
      console.log('Message sent:', msg);
    } finally {
      setIsLoading(false);
    }
  }, []);

  return (
    <ChatUIApp
      onSend={handleSend}
      isLoading={isLoading}
      onMicClick={() => setIsListening(!isListening)}
      isListening={isListening}
      onSettingsClick={() => {}}
      connectionStatus="connected"
      currentProvider="duckbot"
    />
  );
};

const SystemMonitorApp: React.FC = () => (
  <div className="w-full h-full bg-gray-900 p-4">
    <h2 className="text-white text-xl font-semibold mb-4">System Monitor</h2>
    <div className="grid grid-cols-2 gap-4">
      <div className="bg-gray-800 p-4 rounded-lg">
        <h3 className="text-gray-300 font-medium">CPU Usage</h3>
        <div className="text-2xl font-bold text-green-400">45%</div>
      </div>
      <div className="bg-gray-800 p-4 rounded-lg">
        <h3 className="text-gray-300 font-medium">Memory</h3>
        <div className="text-2xl font-bold text-blue-400">3.2 GB</div>
      </div>
      <div className="bg-gray-800 p-4 rounded-lg">
        <h3 className="text-gray-300 font-medium">Network</h3>
        <div className="text-2xl font-bold text-cyan-400">Active</div>
      </div>
      <div className="bg-gray-800 p-4 rounded-lg">
        <h3 className="text-gray-300 font-medium">Services</h3>
        <div className="text-2xl font-bold text-purple-400">8 Running</div>
      </div>
    </div>
  </div>
);

const FileManagerApp: React.FC = () => (
  <div className="w-full h-full bg-gray-900 p-4">
    <h2 className="text-white text-xl font-semibold mb-4">File Manager</h2>
    <div className="space-y-2">
      <div className="bg-gray-800 p-3 rounded-lg flex items-center space-x-3">
        <HardDrive className="w-5 h-5 text-orange-400" />
        <span className="text-gray-300">Documents</span>
      </div>
      <div className="bg-gray-800 p-3 rounded-lg flex items-center space-x-3">
        <Code className="w-5 h-5 text-teal-400" />
        <span className="text-gray-300">Projects</span>
      </div>
      <div className="bg-gray-800 p-3 rounded-lg flex items-center space-x-3">
        <Brain className="w-5 h-5 text-purple-400" />
        <span className="text-gray-300">AI Models</span>
      </div>
    </div>
  </div>
);

const SettingsApp: React.FC = () => (
  <div className="w-full h-full bg-gray-900 flex flex-col">
    {/* Header with fixed height */}
    <div className="p-4 pb-2">
      <h2 className="text-white text-xl font-semibold">DuckBotOS Settings</h2>
    </div>

    {/* Scrollable content area */}
    <div className="flex-1 overflow-y-auto px-4 pb-4">
      <div className="space-y-4">
        <div className="bg-gray-800 p-4 rounded-lg">
          <h3 className="text-gray-300 font-medium mb-3">Appearance</h3>
          <div className="space-y-3">
            <label className="flex items-center space-x-3">
              <input type="checkbox" className="rounded w-4 h-4 text-blue-600 bg-gray-700 border-gray-600 focus:ring-blue-500" />
              <span className="text-gray-300">Dark Mode</span>
            </label>
            <label className="flex items-center space-x-3">
              <input type="checkbox" className="rounded w-4 h-4 text-blue-600 bg-gray-700 border-gray-600 focus:ring-blue-500" defaultChecked />
              <span className="text-gray-300">Animations</span>
            </label>
            <label className="flex items-center space-x-3">
              <input type="checkbox" className="rounded w-4 h-4 text-blue-600 bg-gray-700 border-gray-600 focus:ring-blue-500" defaultChecked />
              <span className="text-gray-300">Transparency Effects</span>
            </label>
          </div>
        </div>

        <div className="bg-gray-800 p-4 rounded-lg">
          <h3 className="text-gray-300 font-medium mb-3">AI Settings</h3>
          <div className="space-y-3">
            <label className="flex items-center space-x-3">
              <input type="checkbox" className="rounded w-4 h-4 text-blue-600 bg-gray-700 border-gray-600 focus:ring-blue-500" defaultChecked />
              <span className="text-gray-300">Voice Assistant</span>
            </label>
            <label className="flex items-center space-x-3">
              <input type="checkbox" className="rounded w-4 h-4 text-blue-600 bg-gray-700 border-gray-600 focus:ring-blue-500" defaultChecked />
              <span className="text-gray-300">3D Avatar</span>
            </label>
            <label className="flex items-center space-x-3">
              <input type="checkbox" className="rounded w-4 h-4 text-blue-600 bg-gray-700 border-gray-600 focus:ring-blue-500" />
              <span className="text-gray-300">Auto-save Conversations</span>
            </label>
            <label className="flex items-center space-x-3">
              <input type="checkbox" className="rounded w-4 h-4 text-blue-600 bg-gray-700 border-gray-600 focus:ring-blue-500" defaultChecked />
              <span className="text-gray-300">Real-time Responses</span>
            </label>
          </div>
        </div>

        <div className="bg-gray-800 p-4 rounded-lg">
          <h3 className="text-gray-300 font-medium mb-3">System</h3>
          <div className="space-y-3">
            <label className="flex items-center space-x-3">
              <input type="checkbox" className="rounded w-4 h-4 text-blue-600 bg-gray-700 border-gray-600 focus:ring-blue-500" defaultChecked />
              <span className="text-gray-300">Start on System Boot</span>
            </label>
            <label className="flex items-center space-x-3">
              <input type="checkbox" className="rounded w-4 h-4 text-blue-600 bg-gray-700 border-gray-600 focus:ring-blue-500" />
              <span className="text-gray-300">Background Services</span>
            </label>
            <label className="flex items-center space-x-3">
              <input type="checkbox" className="rounded w-4 h-4 text-blue-600 bg-gray-700 border-gray-600 focus:ring-blue-500" defaultChecked />
              <span className="text-gray-300">Automatic Updates</span>
            </label>
          </div>
        </div>

        <div className="bg-gray-800 p-4 rounded-lg">
          <h3 className="text-gray-300 font-medium mb-3">Privacy</h3>
          <div className="space-y-3">
            <label className="flex items-center space-x-3">
              <input type="checkbox" className="rounded w-4 h-4 text-blue-600 bg-gray-700 border-gray-600 focus:ring-blue-500" />
              <span className="text-gray-300">Analytics Collection</span>
            </label>
            <label className="flex items-center space-x-3">
              <input type="checkbox" className="rounded w-4 h-4 text-blue-600 bg-gray-700 border-gray-600 focus:ring-blue-500" defaultChecked />
              <span className="text-gray-300">Error Reporting</span>
            </label>
            <label className="flex items-center space-x-3">
              <input type="checkbox" className="rounded w-4 h-4 text-blue-600 bg-gray-700 border-gray-600 focus:ring-blue-500" defaultChecked />
              <span className="text-gray-300">Local Processing Only</span>
            </label>
          </div>
        </div>

        <div className="bg-gray-800 p-4 rounded-lg">
          <h3 className="text-gray-300 font-medium mb-3">Notifications</h3>
          <div className="space-y-3">
            <label className="flex items-center space-x-3">
              <input type="checkbox" className="rounded w-4 h-4 text-blue-600 bg-gray-700 border-gray-600 focus:ring-blue-500" defaultChecked />
              <span className="text-gray-300">Desktop Notifications</span>
            </label>
            <label className="flex items-center space-x-3">
              <input type="checkbox" className="rounded w-4 h-4 text-blue-600 bg-gray-700 border-gray-600 focus:ring-blue-500" />
              <span className="text-gray-300">Sound Effects</span>
            </label>
            <label className="flex items-center space-x-3">
              <input type="checkbox" className="rounded w-4 h-4 text-blue-600 bg-gray-700 border-gray-600 focus:ring-blue-500" defaultChecked />
              <span className="text-gray-300">System Alerts</span>
            </label>
          </div>
        </div>

        <div className="bg-gray-800 p-4 rounded-lg">
          <h3 className="text-gray-300 font-medium mb-3">Advanced</h3>
          <div className="space-y-3">
            <label className="flex items-center space-x-3">
              <input type="checkbox" className="rounded w-4 h-4 text-blue-600 bg-gray-700 border-gray-600 focus:ring-blue-500" />
              <span className="text-gray-300">Developer Mode</span>
            </label>
            <label className="flex items-center space-x-3">
              <input type="checkbox" className="rounded w-4 h-4 text-blue-600 bg-gray-700 border-gray-600 focus:ring-blue-500" />
              <span className="text-gray-300">Experimental Features</span>
            </label>
            <label className="flex items-center space-x-3">
              <input type="checkbox" className="rounded w-4 h-4 text-blue-600 bg-gray-700 border-gray-600 focus:ring-blue-500" defaultChecked />
              <span className="text-gray-300">Hardware Acceleration</span>
            </label>
          </div>
        </div>

        <div className="bg-gray-800 p-4 rounded-lg">
          <h3 className="text-gray-300 font-medium mb-3">API Keys & Services</h3>
          <div className="space-y-3">
            <div className="text-sm text-gray-400 mb-2">Configure your AI service API keys:</div>
            <button className="w-full bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors">
              Configure OpenRouter API Key
            </button>
            <button className="w-full bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg transition-colors">
              Configure Discord Token
            </button>
            <button className="w-full bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg transition-colors">
              Configure GitHub Token
            </button>
          </div>
        </div>

        <div className="bg-gray-800 p-4 rounded-lg">
          <h3 className="text-gray-300 font-medium mb-3">Storage & Cache</h3>
          <div className="space-y-3">
            <div className="text-sm text-gray-400">
              Cache Size: <span className="text-white">245 MB</span>
            </div>
            <div className="text-sm text-gray-400">
              Conversations: <span className="text-white">127</span>
            </div>
            <button className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg transition-colors">
              Clear Cache
            </button>
            <button className="bg-orange-600 hover:bg-orange-700 text-white px-4 py-2 rounded-lg transition-colors">
              Export Data
            </button>
          </div>
        </div>

        <div className="bg-gray-800 p-4 rounded-lg">
          <h3 className="text-gray-300 font-medium mb-3">About</h3>
          <div className="space-y-2 text-sm text-gray-400">
            <div>DuckBotOS v4.2</div>
            <div>Enhanced AI Operating System</div>
            <div>© 2024 DuckBot Project</div>
            <div className="pt-2">
              <button className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors text-sm">
                Check for Updates
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
);

const TerminalApp: React.FC = () => (
  <div className="w-full h-full bg-black p-4 font-mono">
    <div className="text-green-400">
      <div>$ DuckBotOS Terminal v1.0</div>
      <div>$ System initialized and ready</div>
      <div className="flex items-center">
        <span>$ </span>
        <input
          type="text"
          className="bg-transparent border-none outline-none flex-1 text-green-400"
          placeholder="Type commands..."
        />
      </div>
    </div>
  </div>
);

// App Definitions
export const APPS: AppDefinition[] = [
  {
    id: 'assistant',
    title: '3D Assistant',
    icon: <AssistantIcon />,
    component: ThreeAssistantApp,
    isPinned: true,
    defaultSize: { width: 800, height: 600 },
    category: 'ai',
    description: 'Interactive 3D AI assistant'
  },
  {
    id: 'chat',
    title: 'AI Chat',
    icon: <DuckBotIcon />,
    component: ChatApp,
    isPinned: true,
    defaultSize: { width: 500, height: 700 },
    category: 'ai',
    description: 'Chat with AI assistant'
  },
  {
    id: 'gemini',
    title: 'GeminiChat',
    icon: <GeminiIcon />,
    // component: GeminiChat, // Temporarily disabled due to parsing issue
    component: () => <div className="p-4 text-white">GeminiChat temporarily disabled</div>,
    isPinned: true,
    defaultSize: { width: 700, height: 800 },
    category: 'ai',
    description: 'Chat with Google Gemini AI'
  },
  {
    id: 'github',
    title: 'GitHub Manager',
    icon: <GitHubIcon />,
    component: GitHubRepositoryManager,
    isPinned: true,
    defaultSize: { width: 1024, height: 768 },
    category: 'development',
    description: 'Manage GitHub repositories'
  },
  {
    id: 'monitor',
    title: 'System Monitor',
    icon: <SystemMonitorIcon />,
    component: SystemMonitorApp,
    isPinned: false,
    defaultSize: { width: 600, height: 500 },
    category: 'system',
    description: 'Monitor system performance'
  },
  {
    id: 'files',
    title: 'File Manager',
    icon: <FileManagerIcon />,
    component: FileManagerApp,
    isPinned: false,
    defaultSize: { width: 700, height: 500 },
    category: 'productivity',
    description: 'Manage files and projects'
  },
  {
    id: 'settings',
    title: 'Settings',
    icon: <SettingsIcon />,
    component: SettingsApp,
    isPinned: false,
    defaultSize: { width: 650, height: 500 },
    category: 'system',
    description: 'System preferences'
  },
  {
    id: 'terminal',
    title: 'Terminal',
    icon: <TerminalIcon />,
    component: TerminalApp,
    isPinned: false,
    defaultSize: { width: 700, height: 500 },
    category: 'development',
    description: 'Command line interface'
  }
];

// App categories for launcher organization
export const APP_CATEGORIES = {
  ai: 'AI & Assistant',
  development: 'Development',
  productivity: 'Productivity',
  system: 'System'
} as const;