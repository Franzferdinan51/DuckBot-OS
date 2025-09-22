import React, { useState, useEffect } from 'react';
import { X, Settings, Key, Brain, Cpu, HardDrive, Shield, Bell, Zap, Palette, Save } from 'lucide-react';

interface EnhancedSettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (settings: any) => void;
  currentSettings?: any;
}

interface SettingsSection {
  id: string;
  title: string;
  icon: React.ReactNode;
  description: string;
}

const SETTINGS_SECTIONS: SettingsSection[] = [
  {
    id: 'general',
    title: 'General',
    icon: <Settings className="w-5 h-5" />,
    description: 'Basic application settings'
  },
  {
    id: 'ai',
    title: 'AI Configuration',
    icon: <Brain className="w-5 h-5" />,
    description: 'AI model and routing settings'
  },
  {
    id: 'api',
    title: 'API Keys',
    icon: <Key className="w-5 h-5" />,
    description: 'Configure service API keys'
  },
  {
    id: 'system',
    title: 'System',
    icon: <Cpu className="w-5 h-5" />,
    description: 'Performance and hardware settings'
  },
  {
    id: 'storage',
    title: 'Storage',
    icon: <HardDrive className="w-5 h-5" />,
    description: 'Cache and data management'
  },
  {
    id: 'privacy',
    title: 'Privacy',
    icon: <Shield className="w-5 h-5" />,
    description: 'Privacy and security settings'
  },
  {
    id: 'notifications',
    title: 'Notifications',
    icon: <Bell className="w-5 h-5" />,
    description: 'Alert and notification preferences'
  },
  {
    id: 'appearance',
    title: 'Appearance',
    icon: <Palette className="w-5 h-5" />,
    description: 'Theme and display settings'
  },
  {
    id: 'advanced',
    title: 'Advanced',
    icon: <Zap className="w-5 h-5" />,
    description: 'Advanced and experimental features'
  }
];

const EnhancedSettingsModal: React.FC<EnhancedSettingsModalProps> = ({
  isOpen,
  onClose,
  onSave,
  currentSettings = {}
}) => {
  const [activeSection, setActiveSection] = useState('general');
  const [settings, setSettings] = useState(currentSettings);
  const [hasChanges, setHasChanges] = useState(false);

  useEffect(() => {
    setSettings(currentSettings);
    setHasChanges(false);
  }, [currentSettings]);

  const handleSettingChange = (key: string, value: any) => {
    setSettings(prev => ({ ...prev, [key]: value }));
    setHasChanges(true);
  };

  const handleSave = () => {
    onSave(settings);
    setHasChanges(false);
    onClose();
  };

  const handleCancel = () => {
    setSettings(currentSettings);
    setHasChanges(false);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-gray-800 rounded-lg shadow-2xl w-full max-w-6xl h-[90vh] max-h-[900px] flex overflow-hidden">
        {/* Sidebar */}
        <div className="w-64 bg-gray-900 border-r border-gray-700 flex flex-col">
          <div className="p-4 border-b border-gray-700">
            <div className="flex items-center space-x-2">
              <Settings className="w-6 h-6 text-blue-400" />
              <h2 className="text-white text-lg font-semibold">Settings</h2>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-2">
            {SETTINGS_SECTIONS.map(section => (
              <button
                key={section.id}
                onClick={() => setActiveSection(section.id)}
                className={`w-full text-left p-3 rounded-lg mb-1 flex items-center space-x-3 transition-colors ${
                  activeSection === section.id
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-300 hover:bg-gray-700'
                }`}
              >
                <span className="flex-shrink-0">{section.icon}</span>
                <div>
                  <div className="font-medium text-sm">{section.title}</div>
                  <div className="text-xs opacity-75">{section.description}</div>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Main Content Area */}
        <div className="flex-1 flex flex-col">
          {/* Header */}
          <div className="p-4 border-b border-gray-700 bg-gray-800">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-white text-xl font-semibold">
                  {SETTINGS_SECTIONS.find(s => s.id === activeSection)?.title}
                </h3>
                <p className="text-gray-400 text-sm">
                  {SETTINGS_SECTIONS.find(s => s.id === activeSection)?.description}
                </p>
              </div>
              <button
                onClick={onClose}
                className="text-gray-400 hover:text-white transition-colors"
              >
                <X className="w-6 h-6" />
              </button>
            </div>
          </div>

          {/* Scrollable Content */}
          <div className="flex-1 overflow-y-auto p-6">
            <div className="space-y-6">
              {/* General Settings */}
              {activeSection === 'general' && (
                <>
                  <div className="bg-gray-700 rounded-lg p-4">
                    <h4 className="text-white font-medium mb-3">Interface</h4>
                    <div className="space-y-3">
                      <label className="flex items-center space-x-3">
                        <input
                          type="checkbox"
                          checked={settings.darkMode || false}
                          onChange={(e) => handleSettingChange('darkMode', e.target.checked)}
                          className="rounded w-4 h-4 text-blue-600 bg-gray-600 border-gray-500"
                        />
                        <span className="text-gray-300">Dark Mode</span>
                      </label>
                      <label className="flex items-center space-x-3">
                        <input
                          type="checkbox"
                          checked={settings.animations || false}
                          onChange={(e) => handleSettingChange('animations', e.target.checked)}
                          className="rounded w-4 h-4 text-blue-600 bg-gray-600 border-gray-500"
                        />
                        <span className="text-gray-300">Animations</span>
                      </label>
                      <label className="flex items-center space-x-3">
                        <input
                          type="checkbox"
                          checked={settings.compactMode || false}
                          onChange={(e) => handleSettingChange('compactMode', e.target.checked)}
                          className="rounded w-4 h-4 text-blue-600 bg-gray-600 border-gray-500"
                        />
                        <span className="text-gray-300">Compact Mode</span>
                      </label>
                    </div>
                  </div>

                  <div className="bg-gray-700 rounded-lg p-4">
                    <h4 className="text-white font-medium mb-3">Startup</h4>
                    <div className="space-y-3">
                      <label className="flex items-center space-x-3">
                        <input
                          type="checkbox"
                          checked={settings.autoStartAssistant || false}
                          onChange={(e) => handleSettingChange('autoStartAssistant', e.target.checked)}
                          className="rounded w-4 h-4 text-blue-600 bg-gray-600 border-gray-500"
                        />
                        <span className="text-gray-300">Auto-start 3D Assistant</span>
                      </label>
                      <label className="flex items-center space-x-3">
                        <input
                          type="checkbox"
                          checked={settings.startMinimized || false}
                          onChange={(e) => handleSettingChange('startMinimized', e.target.checked)}
                          className="rounded w-4 h-4 text-blue-600 bg-gray-600 border-gray-500"
                        />
                        <span className="text-gray-300">Start Minimized</span>
                      </label>
                    </div>
                  </div>
                </>
              )}

              {/* AI Configuration */}
              {activeSection === 'ai' && (
                <>
                  <div className="bg-gray-700 rounded-lg p-4">
                    <h4 className="text-white font-medium mb-3">Model Selection</h4>
                    <div className="space-y-3">
                      <div>
                        <label className="block text-gray-300 text-sm mb-1">Main AI Model</label>
                        <select
                          value={settings.mainModel || 'qwen/qwen3-coder:free'}
                          onChange={(e) => handleSettingChange('mainModel', e.target.value)}
                          className="w-full bg-gray-600 text-white rounded px-3 py-2 border border-gray-500"
                        >
                          <option value="qwen/qwen3-coder:free">Qwen 3 Coder (Free)</option>
                          <option value="qwen/qwq-32b:free">QWQ-32B (Free)</option>
                          <option value="anthropic/claude-3-sonnet">Claude 3 Sonnet</option>
                          <option value="openai/gpt-4">GPT-4</option>
                        </select>
                      </div>
                      <div>
                        <label className="block text-gray-300 text-sm mb-1">Routing Mode</label>
                        <select
                          value={settings.routingMode || 'cloud_first'}
                          onChange={(e) => handleSettingChange('routingMode', e.target.value)}
                          className="w-full bg-gray-600 text-white rounded px-3 py-2 border border-gray-500"
                        >
                          <option value="cloud_first">Cloud First</option>
                          <option value="local_first">Local First</option>
                          <option value="local_only">Local Only</option>
                        </select>
                      </div>
                    </div>
                  </div>

                  <div className="bg-gray-700 rounded-lg p-4">
                    <h4 className="text-white font-medium mb-3">AI Features</h4>
                    <div className="space-y-3">
                      <label className="flex items-center space-x-3">
                        <input
                          type="checkbox"
                          checked={settings.voiceAssistant || false}
                          onChange={(e) => handleSettingChange('voiceAssistant', e.target.checked)}
                          className="rounded w-4 h-4 text-blue-600 bg-gray-600 border-gray-500"
                        />
                        <span className="text-gray-300">Voice Assistant</span>
                      </label>
                      <label className="flex items-center space-x-3">
                        <input
                          type="checkbox"
                          checked={settings.realTimeResponses || false}
                          onChange={(e) => handleSettingChange('realTimeResponses', e.target.checked)}
                          className="rounded w-4 h-4 text-blue-600 bg-gray-600 border-gray-500"
                        />
                        <span className="text-gray-300">Real-time Responses</span>
                      </label>
                      <label className="flex items-center space-x-3">
                        <input
                          type="checkbox"
                          checked={settings.autoSaveConversations || false}
                          onChange={(e) => handleSettingChange('autoSaveConversations', e.target.checked)}
                          className="rounded w-4 h-4 text-blue-600 bg-gray-600 border-gray-500"
                        />
                        <span className="text-gray-300">Auto-save Conversations</span>
                      </label>
                    </div>
                  </div>
                </>
              )}

              {/* API Keys */}
              {activeSection === 'api' && (
                <>
                  <div className="bg-gray-700 rounded-lg p-4">
                    <h4 className="text-white font-medium mb-3">Service API Keys</h4>
                    <div className="space-y-3">
                      <div>
                        <label className="block text-gray-300 text-sm mb-1">OpenRouter API Key</label>
                        <input
                          type="password"
                          value={settings.openRouterApiKey || ''}
                          onChange={(e) => handleSettingChange('openRouterApiKey', e.target.value)}
                          placeholder="sk-or-..."
                          className="w-full bg-gray-600 text-white rounded px-3 py-2 border border-gray-500"
                        />
                      </div>
                      <div>
                        <label className="block text-gray-300 text-sm mb-1">Discord Token</label>
                        <input
                          type="password"
                          value={settings.discordToken || ''}
                          onChange={(e) => handleSettingChange('discordToken', e.target.value)}
                          placeholder="Bot token..."
                          className="w-full bg-gray-600 text-white rounded px-3 py-2 border border-gray-500"
                        />
                      </div>
                      <div>
                        <label className="block text-gray-300 text-sm mb-1">GitHub Token</label>
                        <input
                          type="password"
                          value={settings.githubToken || ''}
                          onChange={(e) => handleSettingChange('githubToken', e.target.value)}
                          placeholder="ghp_..."
                          className="w-full bg-gray-600 text-white rounded px-3 py-2 border border-gray-500"
                        />
                      </div>
                    </div>
                  </div>
                </>
              )}

              {/* Add more sections as needed */}
              {activeSection !== 'general' && activeSection !== 'ai' && activeSection !== 'api' && (
                <div className="bg-gray-700 rounded-lg p-6 text-center">
                  <Settings className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                  <h4 className="text-white font-medium mb-2">Coming Soon</h4>
                  <p className="text-gray-400">
                    The {SETTINGS_SECTIONS.find(s => s.id === activeSection)?.title.toLowerCase()} settings
                    are under development and will be available soon.
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Footer */}
          <div className="p-4 border-t border-gray-700 bg-gray-800">
            <div className="flex items-center justify-between">
              <div className="text-sm text-gray-400">
                {hasChanges && (
                  <span className="text-yellow-400">● Unsaved changes</span>
                )}
              </div>
              <div className="flex space-x-3">
                <button
                  onClick={handleCancel}
                  className="px-4 py-2 text-gray-300 hover:text-white transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSave}
                  disabled={!hasChanges}
                  className={`px-4 py-2 rounded-lg flex items-center space-x-2 transition-colors ${
                    hasChanges
                      ? 'bg-blue-600 hover:bg-blue-700 text-white'
                      : 'bg-gray-600 text-gray-400 cursor-not-allowed'
                  }`}
                >
                  <Save className="w-4 h-4" />
                  <span>Save Changes</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EnhancedSettingsModal;