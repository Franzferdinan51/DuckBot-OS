import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';

const ComfyUIConfig = ({ onClose, config, onSave }) => {
  const [localConfig, setLocalConfig] = useState(config || {});
  const [activeTab, setActiveTab] = useState('general');
  const [testingConnection, setTestingConnection] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState(null);

  // Configuration tabs
  const tabs = [
    { id: 'general', name: 'General', icon: '⚙️' },
    { id: 'models', name: 'Models', icon: '🧠' },
    { id: 'performance', name: 'Performance', icon: '⚡' },
    { id: 'advanced', name: 'Advanced', icon: '🔧' }
  ];

  // Initialize config
  useEffect(() => {
    if (!localConfig.comfyuiPath) {
      setLocalConfig(prev => ({
        ...prev,
        comfyuiPath: 'C:/ComfyUI',
        gpuMemoryLimit: 80,
        maxConcurrentWorkflows: 3,
        autoStartServer: true,
        enableGPUMode: true,
        defaultModels: {
          checkpoint: 'v1-5-pruned.ckpt',
          vae: 'vae-ft-mse-840000-ema-pruned.ckpt',
          upscale: '4x-UltraSharp.pth'
        },
        performance: {
          lowVramMode: false,
          medVramOptimizations: true,
          fp16Mode: true,
          forceFallbackCpu: false
        }
      }));
    }
  }, [localConfig]);

  // Test ComfyUI connection
  const testConnection = async () => {
    setTestingConnection(true);
    try {
      const response = await fetch(`${localConfig.apiBaseUrl || 'http://localhost:8188'}/system_stats`);
      if (response.ok) {
        setConnectionStatus({ success: true, message: 'Connection successful!' });
      } else {
        setConnectionStatus({ success: false, message: 'Connection failed' });
      }
    } catch (error) {
      setConnectionStatus({ success: false, message: 'Connection failed' });
    } finally {
      setTestingConnection(false);
    }
  };

  // Handle config change
  const handleConfigChange = (path, value) => {
    setLocalConfig(prev => {
      const newConfig = { ...prev };
      const keys = path.split('.');
      let current = newConfig;

      for (let i = 0; i < keys.length - 1; i++) {
        if (!current[keys[i]]) {
          current[keys[i]] = {};
        }
        current = current[keys[i]];
      }

      current[keys[keys.length - 1]] = value;
      return newConfig;
    });
  };

  // Save configuration
  const handleSave = () => {
    onSave(localConfig);
    onClose();
  };

  // Render general settings
  const renderGeneralSettings = () => (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-slate-300 mb-1">ComfyUI Installation Path</label>
        <input
          type="text"
          value={localConfig.comfyuiPath || ''}
          onChange={(e) => handleConfigChange('comfyuiPath', e.target.value)}
          className="w-full p-2 bg-slate-700 text-white rounded border border-slate-600 focus:border-blue-500 focus:outline-none"
          placeholder="C:/ComfyUI"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-slate-300 mb-1">API Base URL</label>
        <input
          type="text"
          value={localConfig.apiBaseUrl || 'http://localhost:8188'}
          onChange={(e) => handleConfigChange('apiBaseUrl', e.target.value)}
          className="w-full p-2 bg-slate-700 text-white rounded border border-slate-600 focus:border-blue-500 focus:outline-none"
          placeholder="http://localhost:8188"
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-1">GPU Memory Limit (%)</label>
          <input
            type="number"
            min="50"
            max="95"
            value={localConfig.gpuMemoryLimit || 80}
            onChange={(e) => handleConfigChange('gpuMemoryLimit', parseInt(e.target.value))}
            className="w-full p-2 bg-slate-700 text-white rounded border border-slate-600 focus:border-blue-500 focus:outline-none"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-300 mb-1">Max Concurrent Workflows</label>
          <select
            value={localConfig.maxConcurrentWorkflows || 3}
            onChange={(e) => handleConfigChange('maxConcurrentWorkflows', parseInt(e.target.value))}
            className="w-full p-2 bg-slate-700 text-white rounded border border-slate-600 focus:border-blue-500 focus:outline-none"
          >
            {[1, 2, 3, 4, 5].map(num => (
              <option key={num} value={num}>{num}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="flex items-center space-x-4">
        <label className="flex items-center space-x-2">
          <input
            type="checkbox"
            checked={localConfig.autoStartServer || false}
            onChange={(e) => handleConfigChange('autoStartServer', e.target.checked)}
            className="rounded"
          />
          <span className="text-sm text-slate-300">Auto-start server</span>
        </label>

        <label className="flex items-center space-x-2">
          <input
            type="checkbox"
            checked={localConfig.enableGPUMode || false}
            onChange={(e) => handleConfigChange('enableGPUMode', e.target.checked)}
            className="rounded"
          />
          <span className="text-sm text-slate-300">Enable GPU mode</span>
        </label>
      </div>

      <div className="pt-4 border-t border-slate-700">
        <button
          onClick={testConnection}
          disabled={testingConnection}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded font-medium disabled:opacity-50"
        >
          {testingConnection ? 'Testing...' : 'Test Connection'}
        </button>

        {connectionStatus && (
          <div className={`mt-2 text-sm ${
            connectionStatus.success ? 'text-green-400' : 'text-red-400'
          }`}>
            {connectionStatus.message}
          </div>
        )}
      </div>
    </div>
  );

  // Render model settings
  const renderModelSettings = () => (
    <div className="space-y-4">
      <h3 className="text-lg font-medium text-white mb-4">Default Models</h3>

      <div>
        <label className="block text-sm font-medium text-slate-300 mb-1">Checkpoint Model</label>
        <input
          type="text"
          value={localConfig.defaultModels?.checkpoint || ''}
          onChange={(e) => handleConfigChange('defaultModels.checkpoint', e.target.value)}
          className="w-full p-2 bg-slate-700 text-white rounded border border-slate-600 focus:border-blue-500 focus:outline-none"
          placeholder="v1-5-pruned.ckpt"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-slate-300 mb-1">VAE Model</label>
        <input
          type="text"
          value={localConfig.defaultModels?.vae || ''}
          onChange={(e) => handleConfigChange('defaultModels.vae', e.target.value)}
          className="w-full p-2 bg-slate-700 text-white rounded border border-slate-600 focus:border-blue-500 focus:outline-none"
          placeholder="vae-ft-mse-840000-ema-pruned.ckpt"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-slate-300 mb-1">Upscale Model</label>
        <input
          type="text"
          value={localConfig.defaultModels?.upscale || ''}
          onChange={(e) => handleConfigChange('defaultModels.upscale', e.target.value)}
          className="w-full p-2 bg-slate-700 text-white rounded border border-slate-600 focus:border-blue-500 focus:outline-none"
          placeholder="4x-UltraSharp.pth"
        />
      </div>

      <div className="pt-4 border-t border-slate-700">
        <h4 className="text-md font-medium text-white mb-3">Available Models</h4>
        <div className="grid grid-cols-2 gap-2">
          {[
            'v1-5-pruned.ckpt',
            'SDXL Base 1.0.safetensors',
            'epicrealism.safetensors',
            'deliberate.safetensors'
          ].map(model => (
            <div
              key={model}
              className="p-2 bg-slate-700 rounded text-xs text-slate-300 hover:bg-slate-600 cursor-pointer"
              onClick={() => handleConfigChange('defaultModels.checkpoint', model)}
            >
              {model}
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  // Render performance settings
  const renderPerformanceSettings = () => (
    <div className="space-y-4">
      <h3 className="text-lg font-medium text-white mb-4">Performance Optimization</h3>

      <div className="space-y-3">
        <label className="flex items-center space-x-2">
          <input
            type="checkbox"
            checked={localConfig.performance?.lowVramMode || false}
            onChange={(e) => handleConfigChange('performance.lowVramMode', e.target.checked)}
            className="rounded"
          />
          <span className="text-sm text-slate-300">Low VRAM mode (saves memory)</span>
        </label>

        <label className="flex items-center space-x-2">
          <input
            type="checkbox"
            checked={localConfig.performance?.medVramOptimizations || true}
            onChange={(e) => handleConfigChange('performance.medVramOptimizations', e.target.checked)}
            className="rounded"
          />
          <span className="text-sm text-slate-300">Medium VRAM optimizations</span>
        </label>

        <label className="flex items-center space-x-2">
          <input
            type="checkbox"
            checked={localConfig.performance?.fp16Mode || true}
            onChange={(e) => handleConfigChange('performance.fp16Mode', e.target.checked)}
            className="rounded"
          />
          <span className="text-sm text-slate-300">FP16 mode (faster, less memory)</span>
        </label>

        <label className="flex items-center space-x-2">
          <input
            type="checkbox"
            checked={localConfig.performance?.forceFallbackCpu || false}
            onChange={(e) => handleConfigChange('performance.forceFallbackCpu', e.target.checked)}
            className="rounded"
          />
          <span className="text-sm text-slate-300">Force fallback to CPU</span>
        </label>
      </div>

      <div className="pt-4 border-t border-slate-700">
        <h4 className="text-md font-medium text-white mb-3">Recommended Settings</h4>
        <div className="space-y-2 text-xs text-slate-400">
          <div className="p-2 bg-slate-800 rounded">
            <div className="font-medium text-slate-300">High-end GPU (8GB+ VRAM)</div>
            <div>Disable Low VRAM mode, enable FP16</div>
          </div>
          <div className="p-2 bg-slate-800 rounded">
            <div className="font-medium text-slate-300">Mid-range GPU (4-8GB VRAM)</div>
            <div>Enable Low VRAM mode, enable FP16</div>
          </div>
          <div className="p-2 bg-slate-800 rounded">
            <div className="font-medium text-slate-300">Low-end GPU (2-4GB VRAM)</div>
            <div>Enable Low VRAM mode, force CPU fallback</div>
          </div>
        </div>
      </div>
    </div>
  );

  // Render advanced settings
  const renderAdvancedSettings = () => (
    <div className="space-y-4">
      <h3 className="text-lg font-medium text-white mb-4">Advanced Configuration</h3>

      <div>
        <label className="block text-sm font-medium text-slate-300 mb-1">Additional Arguments</label>
        <textarea
          value={localConfig.additionalArgs || ''}
          onChange={(e) => handleConfigChange('additionalArgs', e.target.value)}
          className="w-full p-2 bg-slate-700 text-white rounded border border-slate-600 focus:border-blue-500 focus:outline-none"
          rows={3}
          placeholder="--disable-ipex-opt --force-fp32"
        />
        <p className="text-xs text-slate-400 mt-1">Additional command line arguments for ComfyUI</p>
      </div>

      <div>
        <label className="block text-sm font-medium text-slate-300 mb-1">Output Directory</label>
        <input
          type="text"
          value={localConfig.outputDir || ''}
          onChange={(e) => handleConfigChange('outputDir', e.target.value)}
          className="w-full p-2 bg-slate-700 text-white rounded border border-slate-600 focus:border-blue-500 focus:outline-none"
          placeholder="output"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-slate-300 mb-1">Input Directory</label>
        <input
          type="text"
          value={localConfig.inputDir || ''}
          onChange={(e) => handleConfigChange('inputDir', e.target.value)}
          className="w-full p-2 bg-slate-700 text-white rounded border border-slate-600 focus:border-blue-500 focus:outline-none"
          placeholder="input"
        />
      </div>

      <div className="pt-4 border-t border-slate-700">
        <h4 className="text-md font-medium text-white mb-3">Custom Nodes</h4>
        <div className="space-y-2">
          <button className="w-full p-2 bg-slate-700 hover:bg-slate-600 text-white rounded text-sm">
            Install Custom Node Manager
          </button>
          <button className="w-full p-2 bg-slate-700 hover:bg-slate-600 text-white rounded text-sm">
            Browse Custom Nodes
          </button>
        </div>
      </div>

      <div className="pt-4 border-t border-slate-700">
        <h4 className="text-md font-medium text-white mb-3">Danger Zone</h4>
        <div className="space-y-2">
          <button className="w-full p-2 bg-red-700 hover:bg-red-600 text-white rounded text-sm">
            Reset Configuration
          </button>
          <button className="w-full p-2 bg-red-700 hover:bg-red-600 text-white rounded text-sm">
            Clear All Models Cache
          </button>
        </div>
      </div>
    </div>
  );

  return (
    <div className="h-full flex flex-col bg-slate-900 text-white">
      {/* Header */}
      <div className="flex items-center justify-between p-4 bg-slate-800 border-b border-slate-700">
        <div className="flex items-center space-x-2">
          <span className="text-2xl">⚙️</span>
          <h2 className="text-xl font-semibold">ComfyUI Configuration</h2>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={handleSave}
            className="px-3 py-1 rounded text-sm bg-green-600 hover:bg-green-700"
          >
            Save
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
      <div className="flex border-b border-slate-700">
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center space-x-2 px-4 py-2 text-sm font-medium transition-colors ${
              activeTab === tab.id
                ? 'text-blue-400 border-b-2 border-blue-400'
                : 'text-slate-400 hover:text-slate-300'
            }`}
          >
            <span>{tab.icon}</span>
            <span>{tab.name}</span>
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="flex-1 p-4 overflow-y-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          {activeTab === 'general' && renderGeneralSettings()}
          {activeTab === 'models' && renderModelSettings()}
          {activeTab === 'performance' && renderPerformanceSettings()}
          {activeTab === 'advanced' && renderAdvancedSettings()}
        </motion.div>
      </div>
    </div>
  );
};

export default ComfyUIConfig;