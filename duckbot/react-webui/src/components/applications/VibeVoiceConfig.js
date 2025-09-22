import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const VibeVoiceConfig = ({ onClose }) => {
  // State for basic settings
  const [settings, setSettings] = useState({
    api_url: 'http://localhost:8000',
    enable_vibevoice: true,
    auto_download: true,
    default_voice: 'en-alice',
    default_style: 'conversational',
    default_emotion: 'neutral',
    default_speed: 'normal',
    default_pitch: 'normal',
    audio_quality: 'high',
    output_format: 'wav',
    max_duration: 300,
    queue_size: 10,
    auto_cleanup: true,
    cleanup_days: 30
  });

  // State for voice models
  const [voiceModels, setVoiceModels] = useState([]);
  const [selectedModel, setSelectedModel] = useState(null);
  const [modelSettings, setModelSettings] = useState({
    temperature: 0.7,
    top_k: 50,
    top_p: 0.9,
    repetition_penalty: 1.0,
    max_tokens: 512
  });

  // State for audio processing
  const [audioSettings, setAudioSettings] = useState({
    sample_rate: 44100,
    channels: 1,
    bit_depth: 16,
    compression: 'none',
    noise_reduction: true,
    volume_normalization: true,
    silence_removal: false,
    fade_in: 0.1,
    fade_out: 0.1
  });

  // State for advanced features
  const [advancedSettings, setAdvancedSettings] = useState({
    enable_websocket: true,
    enable_batch_processing: true,
    enable_emotional_control: true,
    enable_multi_speaker: true,
    enable_real_time: false,
    enable_api_access: true,
    api_key: '',
    max_concurrent_requests: 5,
    timeout_duration: 60,
    retry_attempts: 3,
    cache_enabled: true,
    cache_size: 1000,
    log_level: 'info'
  });

  // State for system integration
  const [integrationSettings, setIntegrationSettings] = useState({
    duckbot_integration: true,
    discord_bot_integration: false,
    web_ui_integration: true,
    desktop_notifications: true,
    system_tray_icon: true,
    auto_start: false,
    backup_settings: true,
    backup_location: '',
    telemetry_enabled: false
  });

  // State for UI preferences
  const [uiSettings, setUiSettings] = useState({
    theme: 'dark',
    language: 'en',
    date_format: 'mm/dd/yyyy',
    time_format: '12h',
    show_advanced_options: false,
    compact_mode: false,
    auto_save: true,
    auto_save_interval: 30,
    keyboard_shortcuts: true,
    tooltips_enabled: true
  });

  // State for testing and diagnostics
  const [testResults, setTestResults] = useState(null);
  const [isTesting, setIsTesting] = useState(false);
  const [logs, setLogs] = useState([]);

  // Load settings on mount
  useEffect(() => {
    loadSettings();
    loadVoiceModels();
  }, []);

  const loadSettings = async () => {
    try {
      const response = await fetch('http://localhost:8000/config');
      if (response.ok) {
        const data = await response.json();
        setSettings(prev => ({ ...prev, ...data }));
        setAudioSettings(prev => ({ ...prev, ...data.audio_settings }));
        setAdvancedSettings(prev => ({ ...prev, ...data.advanced_settings }));
        setIntegrationSettings(prev => ({ ...prev, ...data.integration_settings }));
        setUiSettings(prev => ({ ...prev, ...data.ui_settings }));
      }
    } catch (error) {
      console.error('Failed to load settings:', error);
    }
  };

  const loadVoiceModels = async () => {
    try {
      const response = await fetch('http://localhost:8000/models');
      if (response.ok) {
        const data = await response.json();
        setVoiceModels(data.models || []);
      }
    } catch (error) {
      console.error('Failed to load voice models:', error);
    }
  };

  const saveSettings = async () => {
    try {
      const config = {
        ...settings,
        audio_settings: audioSettings,
        advanced_settings: advancedSettings,
        integration_settings: integrationSettings,
        ui_settings: uiSettings
      };

      const response = await fetch('http://localhost:8000/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
      });

      if (response.ok) {
        addLog('Settings saved successfully', 'success');
      } else {
        addLog('Failed to save settings', 'error');
      }
    } catch (error) {
      console.error('Failed to save settings:', error);
      addLog('Failed to save settings: ' + error.message, 'error');
    }
  };

  const testConnection = async () => {
    setIsTesting(true);
    addLog('Testing VibeVoice connection...', 'info');

    try {
      const response = await fetch(`${settings.api_url}/health`, {
        method: 'GET',
        timeout: 10000
      });

      if (response.ok) {
        const health = await response.json();
        setTestResults({
          success: true,
          status: health.status,
          response_time: health.response_time,
          available_voices: health.available_voices,
          message: 'Connection successful'
        });
        addLog('Connection test successful', 'success');
      } else {
        setTestResults({
          success: false,
          message: `HTTP ${response.status}: ${response.statusText}`
        });
        addLog(`Connection test failed: HTTP ${response.status}`, 'error');
      }
    } catch (error) {
      setTestResults({
        success: false,
        message: error.message
      });
      addLog('Connection test failed: ' + error.message, 'error');
    } finally {
      setIsTesting(false);
    }
  };

  const testVoiceGeneration = async () => {
    addLog('Testing voice generation...', 'info');

    try {
      const response = await fetch(`${settings.api_url}/generate/test`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: 'Hello, this is a test of the VibeVoice system.',
          speaker: settings.default_voice,
          style: settings.default_style
        })
      });

      if (response.ok) {
        const result = await response.json();
        addLog('Voice generation test successful', 'success');
        return result;
      } else {
        addLog('Voice generation test failed', 'error');
        return null;
      }
    } catch (error) {
      addLog('Voice generation test failed: ' + error.message, 'error');
      return null;
    }
  };

  const resetSettings = async () => {
    try {
      const response = await fetch('http://localhost:8000/config/reset', {
        method: 'POST'
      });

      if (response.ok) {
        await loadSettings();
        addLog('Settings reset to defaults', 'success');
      }
    } catch (error) {
      addLog('Failed to reset settings: ' + error.message, 'error');
    }
  };

  const exportSettings = () => {
    const config = {
      settings,
      audioSettings,
      advancedSettings,
      integrationSettings,
      uiSettings,
      exported_at: new Date().toISOString()
    };

    const blob = new Blob([JSON.stringify(config, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'vibevoice_config.json';
    document.body.appendChild(a);
    a.click();
    URL.revokeObjectURL(url);
    document.body.removeChild(a);

    addLog('Settings exported successfully', 'success');
  };

  const importSettings = (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const config = JSON.parse(e.target.result);
        setSettings(prev => ({ ...prev, ...config.settings }));
        setAudioSettings(prev => ({ ...prev, ...config.audioSettings }));
        setAdvancedSettings(prev => ({ ...prev, ...config.advancedSettings }));
        setIntegrationSettings(prev => ({ ...prev, ...config.integration_settings }));
        setUiSettings(prev => ({ ...prev, ...config.uiSettings }));
        addLog('Settings imported successfully', 'success');
      } catch (error) {
        addLog('Failed to import settings: Invalid file format', 'error');
      }
    };
    reader.readAsText(file);
  };

  const addLog = (message, type = 'info') => {
    setLogs(prev => [...prev, {
      timestamp: new Date().toISOString(),
      message,
      type
    }]);
  };

  const clearLogs = () => {
    setLogs([]);
  };

  const restartService = async () => {
    addLog('Restarting VibeVoice service...', 'info');

    try {
      const response = await fetch('http://localhost:8000/restart', {
        method: 'POST'
      });

      if (response.ok) {
        addLog('VibeVoice service restarted successfully', 'success');
      } else {
        addLog('Failed to restart VibeVoice service', 'error');
      }
    } catch (error) {
      addLog('Failed to restart service: ' + error.message, 'error');
    }
  };

  const updateVoiceModel = async (modelId, enabled) => {
    try {
      await fetch(`http://localhost:8000/models/${modelId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled })
      });

      setVoiceModels(prev => prev.map(model =>
        model.id === modelId ? { ...model, enabled } : model
      ));

      addLog(`Voice model ${enabled ? 'enabled' : 'disabled'}`, 'success');
    } catch (error) {
      addLog('Failed to update voice model: ' + error.message, 'error');
    }
  };

  return (
    <div className="h-full flex flex-col bg-slate-900">
      {/* Header */}
      <div className="bg-slate-800 border-b border-slate-700 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="text-2xl">⚙️</div>
            <div>
              <h2 className="text-xl font-bold text-white">VibeVoice Configuration</h2>
              <p className="text-sm text-slate-400">Configure VibeVoice settings and preferences</p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={saveSettings}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded text-white font-medium"
            >
              Save Settings
            </button>
            <button
              onClick={resetSettings}
              className="px-4 py-2 bg-slate-600 hover:bg-slate-700 rounded text-white font-medium"
            >
              Reset
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-auto">
        <div className="grid grid-cols-12 gap-4 p-4">
          {/* Left Column - Basic Settings */}
          <div className="col-span-4 space-y-4">
            {/* Basic Settings */}
            <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
              <h3 className="text-lg font-semibold text-white mb-4">Basic Settings</h3>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1">
                    API URL
                  </label>
                  <input
                    type="text"
                    value={settings.api_url}
                    onChange={(e) => setSettings(prev => ({ ...prev, api_url: e.target.value }))}
                    className="w-full p-2 bg-slate-700 border border-slate-600 rounded text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={settings.enable_vibevoice}
                    onChange={(e) => setSettings(prev => ({ ...prev, enable_vibevoice: e.target.checked }))}
                    className="rounded border-slate-500 text-blue-600 focus:ring-blue-500"
                  />
                  <label className="text-sm text-white">Enable VibeVoice</label>
                </div>

                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={settings.auto_download}
                    onChange={(e) => setSettings(prev => ({ ...prev, auto_download: e.target.checked }))}
                    className="rounded border-slate-500 text-blue-600 focus:ring-blue-500"
                  />
                  <label className="text-sm text-white">Auto-download generated audio</label>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1">
                    Default Voice
                  </label>
                  <select
                    value={settings.default_voice}
                    onChange={(e) => setSettings(prev => ({ ...prev, default_voice: e.target.value }))}
                    className="w-full p-2 bg-slate-700 border border-slate-600 rounded text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="en-alice">Alice (Female)</option>
                    <option value="en-carter">Carter (Male)</option>
                    <option value="en-david">David (Male)</option>
                    <option value="en-emily">Emily (Female)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1">
                    Default Style
                  </label>
                  <select
                    value={settings.default_style}
                    onChange={(e) => setSettings(prev => ({ ...prev, default_style: e.target.value }))}
                    className="w-full p-2 bg-slate-700 border border-slate-600 rounded text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="conversational">Conversational</option>
                    <option value="professional">Professional</option>
                    <option value="narrative">Narrative</option>
                    <option value="news">News</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1">
                    Audio Quality
                  </label>
                  <select
                    value={settings.audio_quality}
                    onChange={(e) => setSettings(prev => ({ ...prev, audio_quality: e.target.value }))}
                    className="w-full p-2 bg-slate-700 border border-slate-600 rounded text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="low">Low (Fast)</option>
                    <option value="medium">Medium (Balanced)</option>
                    <option value="high">High (Quality)</option>
                    <option value="ultra">Ultra (Best)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1">
                    Output Format
                  </label>
                  <select
                    value={settings.output_format}
                    onChange={(e) => setSettings(prev => ({ ...prev, output_format: e.target.value }))}
                    className="w-full p-2 bg-slate-700 border border-slate-600 rounded text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="wav">WAV (Uncompressed)</option>
                    <option value="mp3">MP3 (Compressed)</option>
                    <option value="ogg">OGG (Open Format)</option>
                    <option value="flac">FLAC (Lossless)</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Connection Test */}
            <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
              <h3 className="text-lg font-semibold text-white mb-4">Connection Test</h3>

              <div className="space-y-3">
                <button
                  onClick={testConnection}
                  disabled={isTesting}
                  className="w-full py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-600 disabled:cursor-not-allowed rounded text-white font-medium"
                >
                  {isTesting ? 'Testing...' : 'Test Connection'}
                </button>

                {testResults && (
                  <div className={`p-3 rounded ${
                    testResults.success ? 'bg-green-900/50 border border-green-700' : 'bg-red-900/50 border border-red-700'
                  }`}>
                    <div className="text-sm">
                      <div className="font-medium text-white mb-1">
                        {testResults.success ? '✅ Connection Successful' : '❌ Connection Failed'}
                      </div>
                      <div className="text-slate-300 text-xs">
                        {testResults.message}
                      </div>
                      {testResults.response_time && (
                        <div className="text-slate-300 text-xs mt-1">
                          Response time: {testResults.response_time}ms
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Service Actions */}
            <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
              <h3 className="text-lg font-semibold text-white mb-4">Service Actions</h3>

              <div className="space-y-2">
                <button
                  onClick={restartService}
                  className="w-full py-2 bg-yellow-600 hover:bg-yellow-700 rounded text-white font-medium"
                >
                  Restart Service
                </button>
                <button
                  onClick={exportSettings}
                  className="w-full py-2 bg-green-600 hover:bg-green-700 rounded text-white font-medium"
                >
                  Export Settings
                </button>
                <label className="block">
                  <input
                    type="file"
                    accept=".json"
                    onChange={importSettings}
                    className="hidden"
                    id="import-settings"
                  />
                  <div className="w-full py-2 bg-purple-600 hover:bg-purple-700 rounded text-white font-medium text-center cursor-pointer">
                    Import Settings
                  </div>
                </label>
              </div>
            </div>
          </div>

          {/* Middle Column - Advanced Settings */}
          <div className="col-span-4 space-y-4">
            {/* Voice Models */}
            <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
              <h3 className="text-lg font-semibold text-white mb-4">Voice Models</h3>

              <div className="space-y-3 max-h-64 overflow-y-auto">
                {voiceModels.map(model => (
                  <div key={model.id} className="bg-slate-700 rounded p-3">
                    <div className="flex items-center justify-between mb-2">
                      <div>
                        <div className="text-sm font-medium text-white">{model.name}</div>
                        <div className="text-xs text-slate-400">
                          {model.language} • {model.gender} • {model.size}
                        </div>
                      </div>
                      <label className="flex items-center">
                        <input
                          type="checkbox"
                          checked={model.enabled}
                          onChange={(e) => updateVoiceModel(model.id, e.target.checked)}
                          className="rounded border-slate-500 text-blue-600 focus:ring-blue-500"
                        />
                      </label>
                    </div>
                    <div className="text-xs text-slate-400">
                      Quality: {model.quality} • Uses: {model.usage_count || 0}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Audio Processing */}
            <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
              <h3 className="text-lg font-semibold text-white mb-4">Audio Processing</h3>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1">
                    Sample Rate
                  </label>
                  <select
                    value={audioSettings.sample_rate}
                    onChange={(e) => setAudioSettings(prev => ({ ...prev, sample_rate: parseInt(e.target.value) }))}
                    className="w-full p-2 bg-slate-700 border border-slate-600 rounded text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="22050">22.05 kHz</option>
                    <option value="44100">44.1 kHz</option>
                    <option value="48000">48 kHz</option>
                    <option value="96000">96 kHz</option>
                  </select>
                </div>

                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={audioSettings.noise_reduction}
                    onChange={(e) => setAudioSettings(prev => ({ ...prev, noise_reduction: e.target.checked }))}
                    className="rounded border-slate-500 text-blue-600 focus:ring-blue-500"
                  />
                  <label className="text-sm text-white">Noise Reduction</label>
                </div>

                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={audioSettings.volume_normalization}
                    onChange={(e) => setAudioSettings(prev => ({ ...prev, volume_normalization: e.target.checked }))}
                    className="rounded border-slate-500 text-blue-600 focus:ring-blue-500"
                  />
                  <label className="text-sm text-white">Volume Normalization</label>
                </div>

                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={audioSettings.silence_removal}
                    onChange={(e) => setAudioSettings(prev => ({ ...prev, silence_removal: e.target.checked }))}
                    className="rounded border-slate-500 text-blue-600 focus:ring-blue-500"
                  />
                  <label className="text-sm text-white">Silence Removal</label>
                </div>

                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-1">
                      Fade In (s)
                    </label>
                    <input
                      type="number"
                      step="0.1"
                      min="0"
                      max="5"
                      value={audioSettings.fade_in}
                      onChange={(e) => setAudioSettings(prev => ({ ...prev, fade_in: parseFloat(e.target.value) }))}
                      className="w-full p-2 bg-slate-700 border border-slate-600 rounded text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-1">
                      Fade Out (s)
                    </label>
                    <input
                      type="number"
                      step="0.1"
                      min="0"
                      max="5"
                      value={audioSettings.fade_out}
                      onChange={(e) => setAudioSettings(prev => ({ ...prev, fade_out: parseFloat(e.target.value) }))}
                      className="w-full p-2 bg-slate-700 border border-slate-600 rounded text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Advanced Features */}
            <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
              <h3 className="text-lg font-semibold text-white mb-4">Advanced Features</h3>

              <div className="space-y-4">
                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={advancedSettings.enable_websocket}
                    onChange={(e) => setAdvancedSettings(prev => ({ ...prev, enable_websocket: e.target.checked }))}
                    className="rounded border-slate-500 text-blue-600 focus:ring-blue-500"
                  />
                  <label className="text-sm text-white">Enable WebSocket</label>
                </div>

                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={advancedSettings.enable_batch_processing}
                    onChange={(e) => setAdvancedSettings(prev => ({ ...prev, enable_batch_processing: e.target.checked }))}
                    className="rounded border-slate-500 text-blue-600 focus:ring-blue-500"
                  />
                  <label className="text-sm text-white">Batch Processing</label>
                </div>

                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={advancedSettings.enable_emotional_control}
                    onChange={(e) => setAdvancedSettings(prev => ({ ...prev, enable_emotional_control: e.target.checked }))}
                    className="rounded border-slate-500 text-blue-600 focus:ring-blue-500"
                  />
                  <label className="text-sm text-white">Emotional Control</label>
                </div>

                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={advancedSettings.enable_api_access}
                    onChange={(e) => setAdvancedSettings(prev => ({ ...prev, enable_api_access: e.target.checked }))}
                    className="rounded border-slate-500 text-blue-600 focus:ring-blue-500"
                  />
                  <label className="text-sm text-white">API Access</label>
                </div>

                {advancedSettings.enable_api_access && (
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-1">
                      API Key
                    </label>
                    <input
                      type="password"
                      value={advancedSettings.api_key}
                      onChange={(e) => setAdvancedSettings(prev => ({ ...prev, api_key: e.target.value }))}
                      className="w-full p-2 bg-slate-700 border border-slate-600 rounded text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                )}

                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1">
                    Max Concurrent Requests
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="20"
                    value={advancedSettings.max_concurrent_requests}
                    onChange={(e) => setAdvancedSettings(prev => ({ ...prev, max_concurrent_requests: parseInt(e.target.value) }))}
                    className="w-full p-2 bg-slate-700 border border-slate-600 rounded text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Right Column - Integration and Logs */}
          <div className="col-span-4 space-y-4">
            {/* System Integration */}
            <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
              <h3 className="text-lg font-semibold text-white mb-4">System Integration</h3>

              <div className="space-y-4">
                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={integrationSettings.duckbot_integration}
                    onChange={(e) => setIntegrationSettings(prev => ({ ...prev, duckbot_integration: e.target.checked }))}
                    className="rounded border-slate-500 text-blue-600 focus:ring-blue-500"
                  />
                  <label className="text-sm text-white">DuckBot Integration</label>
                </div>

                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={integrationSettings.discord_bot_integration}
                    onChange={(e) => setIntegrationSettings(prev => ({ ...prev, discord_bot_integration: e.target.checked }))}
                    className="rounded border-slate-500 text-blue-600 focus:ring-blue-500"
                  />
                  <label className="text-sm text-white">Discord Bot Integration</label>
                </div>

                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={integrationSettings.web_ui_integration}
                    onChange={(e) => setIntegrationSettings(prev => ({ ...prev, web_ui_integration: e.target.checked }))}
                    className="rounded border-slate-500 text-blue-600 focus:ring-blue-500"
                  />
                  <label className="text-sm text-white">Web UI Integration</label>
                </div>

                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={integrationSettings.desktop_notifications}
                    onChange={(e) => setIntegrationSettings(prev => ({ ...prev, desktop_notifications: e.target.checked }))}
                    className="rounded border-slate-500 text-blue-600 focus:ring-blue-500"
                  />
                  <label className="text-sm text-white">Desktop Notifications</label>
                </div>

                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={integrationSettings.auto_start}
                    onChange={(e) => setIntegrationSettings(prev => ({ ...prev, auto_start: e.target.checked }))}
                    className="rounded border-slate-500 text-blue-600 focus:ring-blue-500"
                  />
                  <label className="text-sm text-white">Auto-start on Boot</label>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1">
                    Backup Location
                  </label>
                  <input
                    type="text"
                    value={integrationSettings.backup_location}
                    onChange={(e) => setIntegrationSettings(prev => ({ ...prev, backup_location: e.target.value }))}
                    placeholder="Default backup location"
                    className="w-full p-2 bg-slate-700 border border-slate-600 rounded text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>
            </div>

            {/* UI Preferences */}
            <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
              <h3 className="text-lg font-semibold text-white mb-4">UI Preferences</h3>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1">
                    Theme
                  </label>
                  <select
                    value={uiSettings.theme}
                    onChange={(e) => setUiSettings(prev => ({ ...prev, theme: e.target.value }))}
                    className="w-full p-2 bg-slate-700 border border-slate-600 rounded text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="dark">Dark</option>
                    <option value="light">Light</option>
                    <option value="system">System</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1">
                    Language
                  </label>
                  <select
                    value={uiSettings.language}
                    onChange={(e) => setUiSettings(prev => ({ ...prev, language: e.target.value }))}
                    className="w-full p-2 bg-slate-700 border border-slate-600 rounded text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="en">English</option>
                    <option value="es">Spanish</option>
                    <option value="fr">French</option>
                    <option value="de">German</option>
                  </select>
                </div>

                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={uiSettings.compact_mode}
                    onChange={(e) => setUiSettings(prev => ({ ...prev, compact_mode: e.target.checked }))}
                    className="rounded border-slate-500 text-blue-600 focus:ring-blue-500"
                  />
                  <label className="text-sm text-white">Compact Mode</label>
                </div>

                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={uiSettings.auto_save}
                    onChange={(e) => setUiSettings(prev => ({ ...prev, auto_save: e.target.checked }))}
                    className="rounded border-slate-500 text-blue-600 focus:ring-blue-500"
                  />
                  <label className="text-sm text-white">Auto-save Settings</label>
                </div>

                {uiSettings.auto_save && (
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-1">
                      Auto-save Interval (seconds)
                    </label>
                    <input
                      type="number"
                      min="10"
                      max="300"
                      value={uiSettings.auto_save_interval}
                      onChange={(e) => setUiSettings(prev => ({ ...prev, auto_save_interval: parseInt(e.target.value) }))}
                      className="w-full p-2 bg-slate-700 border border-slate-600 rounded text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                )}
              </div>
            </div>

            {/* Logs */}
            <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-white">Activity Logs</h3>
                <button
                  onClick={clearLogs}
                  className="text-xs text-red-400 hover:text-red-300"
                >
                  Clear
                </button>
              </div>

              <div className="h-48 overflow-y-auto bg-slate-900 rounded p-2 space-y-1">
                {logs.length === 0 ? (
                  <p className="text-slate-400 text-sm text-center py-8">No logs yet</p>
                ) : (
                  logs.map((log, index) => (
                    <div key={index} className="text-xs p-2 rounded bg-slate-800">
                      <div className="flex items-center justify-between">
                        <span className={`font-medium ${
                          log.type === 'success' ? 'text-green-400' :
                          log.type === 'error' ? 'text-red-400' :
                          log.type === 'warning' ? 'text-yellow-400' :
                          'text-blue-400'
                        }`}>
                          {log.message}
                        </span>
                        <span className="text-slate-400">
                          {new Date(log.timestamp).toLocaleTimeString()}
                        </span>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default VibeVoiceConfig;