import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import TRELLISService from '../../services/trellisService';

const TRELLISConfig = ({ onClose, onSave }) => {
  const trellisService = useRef(new TRELLISService()).current;

  // Configuration state
  const [config, setConfig] = useState({
    // Server settings
    serverUrl: 'http://localhost:8000',
    apiKey: '',

    // Generation settings
    defaultResolution: 512,
    defaultQuality: 'medium',
    enableGPU: true,
    maxConcurrentJobs: 2,
    timeoutSeconds: 300,

    // Output settings
    outputPath: './output/trellis',
    defaultFormat: 'glb',
    autoDownload: false,
    includeMetadata: true,

    // Performance settings
    gpuMemoryLimit: 80,
    cpuThreads: 4,
    enableOptimization: true,
    cacheResults: true,

    // Advanced settings
    enableExperimental: false,
    loggingLevel: 'info',
    maxModelSize: 100, // MB
    enableWebUI: true
  });

  const [presets, setPresets] = useState([]);
  const [isTesting, setIsTesting] = useState(false);
  const [testResult, setTestResult] = useState(null);
  const [systemInfo, setSystemInfo] = useState(null);
  const [activeTab, setActiveTab] = useState('basic');

  // Load configuration on mount
  useEffect(() => {
    loadConfiguration();
    loadPresets();
    loadSystemInfo();
  }, []);

  const loadConfiguration = async () => {
    try {
      const savedConfig = localStorage.getItem('trellis-config');
      if (savedConfig) {
        const parsed = JSON.parse(savedConfig);
        setConfig(prev => ({ ...prev, ...parsed }));
      }

      const serverConfig = await trellisService.getConfiguration();
      if (serverConfig) {
        setConfig(prev => ({ ...prev, ...serverConfig }));
      }
    } catch (error) {
      console.error('Failed to load configuration:', error);
    }
  };

  const loadPresets = async () => {
    try {
      const response = await trellisService.getPresets();
      setPresets(response.presets || []);
    } catch (error) {
      console.error('Failed to load presets:', error);
    }
  };

  const loadSystemInfo = async () => {
    try {
      const info = await trellisService.getSystemInfo();
      setSystemInfo(info);
    } catch (error) {
      console.error('Failed to load system info:', error);
    }
  };

  const handleTestConnection = async () => {
    setIsTesting(true);
    setTestResult(null);

    try {
      // Update service configuration
      trellisService.baseURL = config.serverUrl;
      trellisService.apiKey = config.apiKey;

      const result = await trellisService.testConnection();
      setTestResult({
        success: true,
        message: 'Connection successful',
        details: result
      });

      // Reload system info after successful connection
      loadSystemInfo();
    } catch (error) {
      setTestResult({
        success: false,
        message: 'Connection failed',
        error: error.message
      });
    } finally {
      setIsTesting(false);
    }
  };

  const handleSaveConfig = async () => {
    try {
      // Save to localStorage
      localStorage.setItem('trellis-config', JSON.stringify(config));

      // Try to save to server if connected
      try {
        await trellisService.updateConfiguration(config);
      } catch (error) {
        console.warn('Failed to save configuration to server:', error);
      }

      if (onSave) {
        onSave(config);
      }

      // Show success message
      alert('Configuration saved successfully!');
    } catch (error) {
      console.error('Failed to save configuration:', error);
      alert('Failed to save configuration: ' + error.message);
    }
  };

  const handleApplyPreset = (preset) => {
    setConfig(prev => ({
      ...prev,
      ...preset.settings
    }));
  };

  const handleResetToDefaults = () => {
    if (confirm('Are you sure you want to reset all settings to defaults?')) {
      setConfig({
        serverUrl: 'http://localhost:8000',
        apiKey: '',
        defaultResolution: 512,
        defaultQuality: 'medium',
        enableGPU: true,
        maxConcurrentJobs: 2,
        timeoutSeconds: 300,
        outputPath: './output/trellis',
        defaultFormat: 'glb',
        autoDownload: false,
        includeMetadata: true,
        gpuMemoryLimit: 80,
        cpuThreads: 4,
        enableOptimization: true,
        cacheResults: true,
        enableExperimental: false,
        loggingLevel: 'info',
        maxModelSize: 100,
        enableWebUI: true
      });
    }
  };

  return (
    <div className="h-full flex flex-col bg-slate-900 text-white">
      {/* Header */}
      <div className="flex items-center justify-between p-4 bg-slate-800 border-b border-slate-700">
        <div className="flex items-center space-x-2">
          <span className="text-2xl">⚙️</span>
          <h2 className="text-xl font-semibold">TRELLIS Configuration</h2>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={handleResetToDefaults}
            className="px-3 py-1 rounded text-sm bg-gray-600 hover:bg-gray-700"
          >
            Reset Defaults
          </button>
          <button
            onClick={onClose}
            className="px-3 py-1 rounded text-sm bg-gray-600 hover:bg-gray-700"
          >
            ✕
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex bg-slate-800 border-b border-slate-700">
        {['basic', 'generation', 'performance', 'advanced'].map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 text-sm font-medium transition-colors ${
              activeTab === tab
                ? 'bg-blue-600 text-white'
                : 'text-slate-300 hover:bg-slate-700 hover:text-white'
            }`}
          >
            {tab.charAt(0).toUpperCase() + tab.slice(1)}
          </button>
        ))}
      </div>

      {/* Configuration Content */}
      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-4xl mx-auto space-y-6">
          {/* Connection Test Section */}
          <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
            <h3 className="text-lg font-semibold mb-4">Connection Test</h3>
            <div className="flex items-center space-x-4">
              <button
                onClick={handleTestConnection}
                disabled={isTesting}
                className={`px-4 py-2 rounded font-medium ${
                  isTesting
                    ? 'bg-yellow-600 cursor-not-allowed'
                    : 'bg-blue-600 hover:bg-blue-700'
                }`}
              >
                {isTesting ? 'Testing...' : 'Test Connection'}
              </button>
              {testResult && (
                <div className={`px-3 py-2 rounded text-sm ${
                  testResult.success ? 'bg-green-600' : 'bg-red-600'
                }`}>
                  {testResult.message}
                </div>
              )}
            </div>
          </div>

          {/* System Information */}
          {systemInfo && (
            <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
              <h3 className="text-lg font-semibold mb-4">System Information</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <span className="text-slate-400">TRELLIS Version:</span>
                  <div className="text-white">{systemInfo.version || 'Unknown'}</div>
                </div>
                <div>
                  <span className="text-slate-400">Python:</span>
                  <div className="text-white">{systemInfo.python_version || 'Unknown'}</div>
                </div>
                <div>
                  <span className="text-slate-400">PyTorch:</span>
                  <div className="text-white">{systemInfo.pytorch_version || 'Unknown'}</div>
                </div>
                <div>
                  <span className="text-slate-400">CUDA:</span>
                  <div className="text-white">{systemInfo.cuda_version || 'N/A'}</div>
                </div>
              </div>
            </div>
          )}

          {/* Basic Configuration */}
          {activeTab === 'basic' && (
            <div className="space-y-4">
              <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
                <h3 className="text-lg font-semibold mb-4">Server Settings</h3>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">
                      Server URL
                    </label>
                    <input
                      type="text"
                      value={config.serverUrl}
                      onChange={(e) => setConfig(prev => ({ ...prev, serverUrl: e.target.value }))}
                      className="w-full p-2 bg-slate-700 text-white rounded border border-slate-600 focus:border-blue-500 focus:outline-none"
                      placeholder="http://localhost:8000"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">
                      API Key (Optional)
                    </label>
                    <input
                      type="password"
                      value={config.apiKey}
                      onChange={(e) => setConfig(prev => ({ ...prev, apiKey: e.target.value }))}
                      className="w-full p-2 bg-slate-700 text-white rounded border border-slate-600 focus:border-blue-500 focus:outline-none"
                      placeholder="Enter API key if required"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">
                      Output Path
                    </label>
                    <input
                      type="text"
                      value={config.outputPath}
                      onChange={(e) => setConfig(prev => ({ ...prev, outputPath: e.target.value }))}
                      className="w-full p-2 bg-slate-700 text-white rounded border border-slate-600 focus:border-blue-500 focus:outline-none"
                      placeholder="./output/trellis"
                    />
                  </div>
                </div>
              </div>

              <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
                <h3 className="text-lg font-semibold mb-4">Output Settings</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">
                      Default Format
                    </label>
                    <select
                      value={config.defaultFormat}
                      onChange={(e) => setConfig(prev => ({ ...prev, defaultFormat: e.target.value }))}
                      className="w-full p-2 bg-slate-700 text-white rounded border border-slate-600 focus:border-blue-500 focus:outline-none"
                    >
                      <option value="glb">GLB (Binary glTF)</option>
                      <option value="gltf">glTF (JSON)</option>
                      <option value="obj">OBJ (Wavefront)</option>
                      <option value="stl">STL (Stereolithography)</option>
                      <option value="ply">PLY (Stanford)</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">
                      Default Resolution
                    </label>
                    <select
                      value={config.defaultResolution}
                      onChange={(e) => setConfig(prev => ({ ...prev, defaultResolution: parseInt(e.target.value) }))}
                      className="w-full p-2 bg-slate-700 text-white rounded border border-slate-600 focus:border-blue-500 focus:outline-none"
                    >
                      <option value={256}>256x256</option>
                      <option value={512}>512x512</option>
                      <option value={768}>768x768</option>
                      <option value={1024}>1024x1024</option>
                    </select>
                  </div>
                </div>
                <div className="mt-4 space-y-3">
                  <label className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={config.autoDownload}
                      onChange={(e) => setConfig(prev => ({ ...prev, autoDownload: e.target.checked }))}
                      className="rounded"
                    />
                    <span className="text-sm">Auto-download generated assets</span>
                  </label>
                  <label className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={config.includeMetadata}
                      onChange={(e) => setConfig(prev => ({ ...prev, includeMetadata: e.target.checked }))}
                      className="rounded"
                    />
                    <span className="text-sm">Include metadata in exports</span>
                  </label>
                  <label className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={config.enableWebUI}
                      onChange={(e) => setConfig(prev => ({ ...prev, enableWebUI: e.target.checked }))}
                      className="rounded"
                    />
                    <span className="text-sm">Enable Web UI preview</span>
                  </label>
                </div>
              </div>
            </div>
          )}

          {/* Generation Configuration */}
          {activeTab === 'generation' && (
            <div className="space-y-4">
              <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
                <h3 className="text-lg font-semibold mb-4">Generation Settings</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">
                      Default Quality
                    </label>
                    <select
                      value={config.defaultQuality}
                      onChange={(e) => setConfig(prev => ({ ...prev, defaultQuality: e.target.value }))}
                      className="w-full p-2 bg-slate-700 text-white rounded border border-slate-600 focus:border-blue-500 focus:outline-none"
                    >
                      <option value="draft">Draft (Fast)</option>
                      <option value="medium">Medium (Balanced)</option>
                      <option value="high">High (Quality)</option>
                      <option value="ultra">Ultra (Best)</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">
                      Max Concurrent Jobs
                    </label>
                    <input
                      type="number"
                      min="1"
                      max="10"
                      value={config.maxConcurrentJobs}
                      onChange={(e) => setConfig(prev => ({ ...prev, maxConcurrentJobs: parseInt(e.target.value) }))}
                      className="w-full p-2 bg-slate-700 text-white rounded border border-slate-600 focus:border-blue-500 focus:outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">
                      Timeout (seconds)
                    </label>
                    <input
                      type="number"
                      min="30"
                      max="1800"
                      value={config.timeoutSeconds}
                      onChange={(e) => setConfig(prev => ({ ...prev, timeoutSeconds: parseInt(e.target.value) }))}
                      className="w-full p-2 bg-slate-700 text-white rounded border border-slate-600 focus:border-blue-500 focus:outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">
                      Max Model Size (MB)
                    </label>
                    <input
                      type="number"
                      min="10"
                      max="1000"
                      value={config.maxModelSize}
                      onChange={(e) => setConfig(prev => ({ ...prev, maxModelSize: parseInt(e.target.value) }))}
                      className="w-full p-2 bg-slate-700 text-white rounded border border-slate-600 focus:border-blue-500 focus:outline-none"
                    />
                  </div>
                </div>
              </div>

              <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
                <h3 className="text-lg font-semibold mb-4">Presets</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                  {presets.length > 0 ? (
                    presets.map(preset => (
                      <button
                        key={preset.id}
                        onClick={() => handleApplyPreset(preset)}
                        className="p-3 bg-slate-700 hover:bg-slate-600 rounded-lg text-left transition-colors"
                      >
                        <div className="font-medium text-white text-sm">{preset.name}</div>
                        <div className="text-slate-400 text-xs mt-1">{preset.description}</div>
                      </button>
                    ))
                  ) : (
                    <div className="col-span-full text-center text-slate-500 py-4">
                      No presets available
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Performance Configuration */}
          {activeTab === 'performance' && (
            <div className="space-y-4">
              <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
                <h3 className="text-lg font-semibold mb-4">Resource Management</h3>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">
                      GPU Memory Limit (%)
                    </label>
                    <div className="flex items-center space-x-3">
                      <input
                        type="range"
                        min="10"
                        max="95"
                        value={config.gpuMemoryLimit}
                        onChange={(e) => setConfig(prev => ({ ...prev, gpuMemoryLimit: parseInt(e.target.value) }))}
                        className="flex-1"
                      />
                      <span className="text-white w-12 text-right">{config.gpuMemoryLimit}%</span>
                    </div>
                    <p className="text-xs text-slate-400 mt-1">
                      Maximum percentage of GPU memory to use for 3D generation
                    </p>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">
                      CPU Threads
                    </label>
                    <input
                      type="number"
                      min="1"
                      max="32"
                      value={config.cpuThreads}
                      onChange={(e) => setConfig(prev => ({ ...prev, cpuThreads: parseInt(e.target.value) }))}
                      className="w-full p-2 bg-slate-700 text-white rounded border border-slate-600 focus:border-blue-500 focus:outline-none"
                    />
                    <p className="text-xs text-slate-400 mt-1">
                      Number of CPU threads to use for processing
                    </p>
                  </div>

                  <div className="space-y-3">
                    <label className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        checked={config.enableGPU}
                        onChange={(e) => setConfig(prev => ({ ...prev, enableGPU: e.target.checked }))}
                        className="rounded"
                      />
                      <span className="text-sm">Enable GPU acceleration</span>
                    </label>
                    <label className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        checked={config.enableOptimization}
                        onChange={(e) => setConfig(prev => ({ ...prev, enableOptimization: e.target.checked }))}
                        className="rounded"
                      />
                      <span className="text-sm">Enable automatic optimization</span>
                    </label>
                    <label className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        checked={config.cacheResults}
                        onChange={(e) => setConfig(prev => ({ ...prev, cacheResults: e.target.checked }))}
                        className="rounded"
                      />
                      <span className="text-sm">Cache generation results</span>
                    </label>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Advanced Configuration */}
          {activeTab === 'advanced' && (
            <div className="space-y-4">
              <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
                <h3 className="text-lg font-semibold mb-4">Advanced Settings</h3>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">
                      Logging Level
                    </label>
                    <select
                      value={config.loggingLevel}
                      onChange={(e) => setConfig(prev => ({ ...prev, loggingLevel: e.target.value }))}
                      className="w-full p-2 bg-slate-700 text-white rounded border border-slate-600 focus:border-blue-500 focus:outline-none"
                    >
                      <option value="debug">Debug</option>
                      <option value="info">Info</option>
                      <option value="warning">Warning</option>
                      <option value="error">Error</option>
                    </select>
                  </div>

                  <div className="space-y-3">
                    <label className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        checked={config.enableExperimental}
                        onChange={(e) => setConfig(prev => ({ ...prev, enableExperimental: e.target.checked }))}
                        className="rounded"
                      />
                      <span className="text-sm">Enable experimental features</span>
                      <span className="text-xs text-red-400">(May be unstable)</span>
                    </label>
                  </div>

                  <div className="p-3 bg-red-900/20 border border-red-700 rounded-lg">
                    <h4 className="text-red-400 font-medium text-sm mb-2">Experimental Features Warning</h4>
                    <p className="text-xs text-red-300">
                      Enabling experimental features may cause instability or unexpected behavior.
                      Use at your own risk and ensure you have backups of important data.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Footer */}
      <div className="flex justify-end items-center p-4 bg-slate-800 border-t border-slate-700">
        <button
          onClick={onClose}
          className="px-4 py-2 rounded text-sm bg-gray-600 hover:bg-gray-700 mr-3"
        >
          Cancel
        </button>
        <button
          onClick={handleSaveConfig}
          className="px-4 py-2 rounded text-sm bg-blue-600 hover:bg-blue-700 font-medium"
        >
          Save Configuration
        </button>
      </div>
    </div>
  );
};

export default TRELLISConfig;