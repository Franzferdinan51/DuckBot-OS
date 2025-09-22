import React, { useState, useCallback, useRef, useEffect } from 'react';
import DuckBotOS from './desktop/DuckBotOS';
import { AIService } from '../services/duckbotService';
import { githubService } from '../services/githubService';
import { Settings, Minimize2 } from 'lucide-react';

interface DuckBotOSEnhancedProps {
  // Optional props for customization
  wallpaperUrl?: string;
  enableElectronFeatures?: boolean;
}

const DuckBotOSEnhanced: React.FC<DuckBotOSEnhancedProps> = ({
  wallpaperUrl = "https://picsum.photos/1920/1080?grayscale&blur=1&seed=duckbot",
  enableElectronFeatures = true
}) => {
  // Settings state
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [settings, setSettings] = useState({
    apiProvider: 'duckbot',
    duckbotUrl: 'http://localhost:8787',
    duckbotToken: null,
    lmStudioUrl: 'http://localhost:1234',
    lmStudioModel: '',
    openRouterApiKey: '',
    openRouterModel: 'google/gemma-2-9b-it:free',
    speechVoiceURI: null,
    useVibeVoice: true,
    githubToken: '',
  });
  const [tempSettings, setTempSettings] = useState(settings);
  const [voices, setVoices] = useState([]);
  const [connectionStatus, setConnectionStatus] = useState('disconnected');

  // Refs
  const aiServiceRef = useRef(new AIService());

  // Load settings from localStorage
  useEffect(() => {
    try {
      const storedSettings = localStorage.getItem('duckbotClippySettings');
      if (storedSettings) {
        const parsedSettings = JSON.parse(storedSettings);
        const newSettings = {
          apiProvider: parsedSettings.apiProvider || 'duckbot',
          duckbotUrl: parsedSettings.duckbotUrl || 'http://localhost:8787',
          duckbotToken: parsedSettings.duckbotToken || null,
          lmStudioUrl: parsedSettings.lmStudioUrl || 'http://localhost:1234',
          lmStudioModel: parsedSettings.lmStudioModel || '',
          openRouterApiKey: parsedSettings.openRouterApiKey || '',
          openRouterModel: parsedSettings.openRouterModel || 'google/gemma-2-9b-it:free',
          speechVoiceURI: parsedSettings.speechVoiceURI || null,
          useVibeVoice: parsedSettings.useVibeVoice !== undefined ? parsedSettings.useVibeVoice : true,
          githubToken: parsedSettings.githubToken || '',
        };

        setSettings(newSettings);
        setTempSettings(newSettings);

        // Configure GitHub service if token is available
        if (newSettings.githubToken) {
          githubService.setToken(newSettings.githubToken);
        }
      }
    } catch (error) {
      console.error("Failed to load settings from localStorage:", error);
    }
  }, []);

  // Initialize speech synthesis voices
  useEffect(() => {
    const populateVoiceList = () => {
      const availableVoices = window.speechSynthesis.getVoices();
      const englishVoices = availableVoices.filter(voice => voice.lang.startsWith('en'));
      setVoices(englishVoices);
    };

    populateVoiceList();
    if (window.speechSynthesis.onvoiceschanged !== undefined) {
      window.speechSynthesis.onvoiceschanged = populateVoiceList;
    }
  }, []);

  // Test AI connection
  useEffect(() => {
    let isMounted = true;
    let timeoutId: NodeJS.Timeout;

    const testConnection = async () => {
      if (!isMounted) return;

      setConnectionStatus('connecting');

      try {
        const service = aiServiceRef.current;

        if (settings.apiProvider === 'duckbot') {
          service.getDuckBotService().setBaseUrl(settings.duckbotUrl);
          service.getDuckBotService().setToken(settings.duckbotToken);
          const isConnected = await service.getDuckBotService().testConnection();
          if (isMounted) {
            setConnectionStatus(isConnected ? 'connected' : 'disconnected');
          }
        } else if (settings.apiProvider === 'lmstudio') {
          service.getLMStudioService().setBaseUrl(settings.lmStudioUrl);
          const isConnected = await service.getLMStudioService().testConnection();
          if (isMounted) {
            setConnectionStatus(isConnected ? 'connected' : 'disconnected');
          }
        } else if (settings.apiProvider === 'openrouter') {
          service.getOpenRouterService().setApiKey(settings.openRouterApiKey);
          const isConnected = await service.getOpenRouterService().testConnection();
          if (isMounted) {
            setConnectionStatus(isConnected ? 'connected' : 'disconnected');
          }
        }
      } catch (error) {
        console.error('Connection test failed:', error);
        if (isMounted) {
          setConnectionStatus('disconnected');
        }
      }
    };

    // Debounce connection testing to prevent rapid re-testing
    timeoutId = setTimeout(testConnection, 500);

    return () => {
      isMounted = false;
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
    };
  }, [settings.apiProvider, settings.duckbotUrl, settings.duckbotToken, settings.lmStudioUrl, settings.openRouterApiKey]);

  const handleSaveSettings = () => {
    setSettings(tempSettings);
    try {
      localStorage.setItem('duckbotClippySettings', JSON.stringify(tempSettings));

      // Update GitHub service if token changed
      if (tempSettings.githubToken !== settings.githubToken) {
        githubService.setToken(tempSettings.githubToken);
      }
    } catch (error) {
      console.error("Failed to save settings to localStorage:", error);
    }
    setIsSettingsOpen(false);
  };

  const handleMinimizeToTray = () => {
    if (enableElectronFeatures && window.electronAPI?.minimizeToTray) {
      window.electronAPI.minimizeToTray();
    }
  };

  // Handle system tray actions
  const handleSystemTraySettings = () => {
    setIsSettingsOpen(true);
  };

  const handleSystemTrayPower = () => {
    if (enableElectronFeatures && window.electronAPI?.quit) {
      window.electronAPI.quit();
    }
  };

  // Handle app open/close events
  const handleAppOpen = useCallback((appId: string) => {
    console.log(`App opened: ${appId}`);
    // Additional app initialization logic here
  }, []);

  const handleWindowClose = useCallback((appId: string) => {
    console.log(`App closed: ${appId}`);
    // Additional app cleanup logic here
  }, []);

  return (
    <div className="w-full h-full">
      {/* Settings Modal */}
      {isSettingsOpen && (
        <div className="fixed inset-0 z-[2000] flex items-center justify-center bg-black bg-opacity-80" onClick={() => setIsSettingsOpen(false)}>
          <div className="bg-gray-800 rounded-lg shadow-xl p-6 w-full max-w-md text-white border border-gray-700" onClick={(e) => e.stopPropagation()}>
            <h2 className="text-2xl font-bold mb-6">DuckBotOS Settings</h2>

            <div className="space-y-6 max-h-96 overflow-y-auto">
              {/* API Provider Selection */}
              <div>
                <label className="block mb-2 font-semibold">AI Provider</label>
                <div className="grid grid-cols-3 gap-2">
                  {['duckbot', 'lmstudio', 'openrouter'].map(provider => (
                    <button
                      key={provider}
                      onClick={() => setTempSettings({...tempSettings, apiProvider: provider})}
                      className={`py-2 px-3 rounded text-sm font-medium transition-colors ${
                        tempSettings.apiProvider === provider
                          ? 'bg-teal-600 text-white'
                          : 'bg-gray-700 hover:bg-gray-600'
                      }`}
                    >
                      {provider === 'duckbot' ? 'DuckBot' : provider === 'lmstudio' ? 'LM Studio' : 'OpenRouter'}
                    </button>
                  ))}
                </div>
              </div>

              {/* GitHub Token */}
              <div>
                <label htmlFor="github-token" className="block mb-2 font-semibold">GitHub Token (Optional)</label>
                <input
                  id="github-token"
                  type="password"
                  value={tempSettings.githubToken}
                  onChange={(e) => setTempSettings({...tempSettings, githubToken: e.target.value})}
                  className="w-full p-2 bg-gray-700 rounded border border-gray-600 focus:outline-none focus:ring-2 focus:ring-teal-500"
                  placeholder="ghp_xxx..."
                />
                <p className="text-xs text-gray-400 mt-1">
                  Required for GitHub repository management features
                </p>
              </div>

              {/* Provider-specific settings */}
              {tempSettings.apiProvider === 'duckbot' && (
                <div className="space-y-4">
                  <div>
                    <label htmlFor="duckbot-url" className="block mb-2 font-semibold">DuckBot URL</label>
                    <input
                      id="duckbot-url"
                      type="text"
                      value={tempSettings.duckbotUrl}
                      onChange={(e) => setTempSettings({...tempSettings, duckbotUrl: e.target.value})}
                      className="w-full p-2 bg-gray-700 rounded border border-gray-600 focus:outline-none focus:ring-2 focus:ring-teal-500"
                      placeholder="http://localhost:8787"
                    />
                  </div>
                  <div className="p-3 bg-gray-900 rounded-md border border-gray-600">
                    <p className="text-sm text-gray-300">
                      Connection Status: <span className={`font-medium ${connectionStatus === 'connected' ? 'text-green-400' : connectionStatus === 'connecting' ? 'text-yellow-400' : 'text-red-400'}`}>
                        {connectionStatus}
                      </span>
                    </p>
                  </div>
                </div>
              )}

              {/* VibeVoice TTS Toggle */}
              <div>
                <label className="flex items-center mb-2 font-semibold">
                  <input
                    type="checkbox"
                    checked={tempSettings.useVibeVoice}
                    onChange={(e) => setTempSettings({ ...tempSettings, useVibeVoice: e.target.checked })}
                    className="mr-2 text-teal-600 bg-gray-700 border-gray-600 rounded focus:ring-teal-500 focus:ring-2"
                  />
                  Use VibeVoice TTS (DuckBot)
                </label>
                <p className="text-xs text-gray-400">
                  {tempSettings.useVibeVoice
                    ? "High-quality multi-speaker TTS via DuckBot's VibeVoice integration"
                    : "Using browser's built-in speech synthesis"}
                </p>
              </div>

              {/* Voice Selection */}
              <div>
                <label htmlFor="voice-select" className="block mb-2 font-semibold">
                  {tempSettings.useVibeVoice ? "Fallback Voice" : "Browser Voice Selection"}
                </label>
                <select
                  id="voice-select"
                  value={tempSettings.speechVoiceURI || ''}
                  onChange={(e) => setTempSettings({ ...tempSettings, speechVoiceURI: e.target.value })}
                  className="w-full p-2 bg-gray-700 rounded border border-gray-600 focus:outline-none focus:ring-2 focus:ring-teal-500"
                  disabled={voices.length === 0}
                >
                  <option value="">Browser Default</option>
                  {voices.map(voice => (
                    <option key={voice.voiceURI} value={voice.voiceURI}>
                      {`${voice.name} (${voice.lang})`}
                    </option>
                  ))}
                </select>
                {voices.length === 0 && <p className="text-xs text-gray-400 mt-1">Loading voices...</p>}
              </div>
            </div>

            <div className="flex justify-end gap-4 mt-8">
              <button onClick={() => { setIsSettingsOpen(false); setTempSettings(settings); }} className="px-4 py-2 bg-gray-600 hover:bg-gray-500 rounded-lg transition-colors">Cancel</button>
              <button onClick={handleSaveSettings} className="px-4 py-2 bg-teal-600 hover:bg-teal-500 rounded-lg transition-colors font-semibold">Save</button>
            </div>
          </div>
        </div>
      )}

      {/* Main DuckBotOS Interface */}
      <DuckBotOS
        wallpaperUrl={wallpaperUrl}
        autoOpenApps={['assistant']}
        onAppOpen={handleAppOpen}
        onWindowClose={handleWindowClose}
      />

      {/* System tray integration */}
      {enableElectronFeatures && (
        <div className="fixed top-4 right-4 z-50">
          {window.electronAPI && (
            <button
              onClick={handleMinimizeToTray}
              className="p-2 bg-gray-800/80 backdrop-blur-sm rounded-lg hover:bg-gray-700/80 transition-colors"
              title="Minimize to tray"
            >
              <Minimize2 className="w-5 h-5 text-gray-300" />
            </button>
          )}
        </div>
      )}

      {/* Connection status indicator */}
      <div className="fixed top-4 left-4 z-50">
        <div className={`px-3 py-2 rounded-lg text-sm font-medium backdrop-blur-sm ${
          connectionStatus === 'connected'
            ? 'bg-green-600/80 text-white'
            : connectionStatus === 'connecting'
            ? 'bg-yellow-600/80 text-white'
            : 'bg-red-600/80 text-white'
        }`}>
          AI Service: {connectionStatus}
        </div>
      </div>
    </div>
  );
};

export default DuckBotOSEnhanced;