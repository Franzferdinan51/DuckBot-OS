import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Settings,
  Server,
  Database,
  Brain,
  Shield,
  Globe,
  Key,
  Save,
  RotateCcw,
  TestTube,
  Activity,
  Monitor,
  Cpu,
  HardDrive,
  Wifi,
  Zap,
  BarChart3,
  FileText,
  Code,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Info,
  Download,
  Upload
} from 'lucide-react';
import { useDeepCode } from '../../services/deepcodeService';

// Configuration sections
const CONFIG_SECTIONS = [
  { id: 'server', name: 'Server Settings', icon: Server },
  { id: 'models', name: 'AI Models', icon: Brain },
  { id: 'security', name: 'Security', icon: Shield },
  { id: 'performance', name: 'Performance', icon: Zap },
  { id: 'integrations', name: 'Integrations', icon: Globe },
  { id: 'advanced', name: 'Advanced', icon: Settings }
];

// Default configuration
const DEFAULT_CONFIG = {
  server: {
    host: 'localhost',
    port: 8790,
    use_https: false,
    timeout: 30000,
    max_retries: 3,
    retry_delay: 1000
  },
  models: {
    default_model: 'qwen3-coder',
    fallback_model: 'gpt-4',
    temperature: 0.2,
    max_tokens: 4000,
    top_p: 0.9,
    top_k: 50,
    streaming: true,
    cache_enabled: true
  },
  security: {
    enable_auth: true,
    api_key_required: false,
    rate_limiting: {
      enabled: true,
      requests_per_minute: 60,
      requests_per_hour: 1000
    },
    cors_enabled: true,
    allowed_origins: ['*'],
    enable_logging: true,
    log_level: 'INFO'
  },
  performance: {
    max_concurrent_jobs: 5,
    job_timeout: 300000,
    memory_limit_mb: 4096,
    cpu_limit_percent: 80,
    enable_caching: true,
    cache_ttl: 3600,
    parallel_processing: true,
    optimization_level: 'balanced'
  },
  integrations: {
    github: {
      enabled: false,
      token: '',
      default_branch: 'main',
      auto_commit: false
    },
    gitlab: {
      enabled: false,
      token: '',
      default_branch: 'main',
      auto_commit: false
    },
    webhooks: {
      enabled: true,
      secret: '',
      allowed_events: ['job.completed', 'job.failed']
    }
  },
  advanced: {
    debug_mode: false,
    enable_telemetry: false,
    custom_templates_dir: '',
    output_dir: './deepcode_output',
    temp_cleanup_interval: 3600,
    max_log_files: 10,
    log_file_size_mb: 50
  }
};

const DeepCodeConfig = () => {
  const [activeSection, setActiveSection] = useState('server');
  const [config, setConfig] = useState(DEFAULT_CONFIG);
  const [isTesting, setIsTesting] = useState(false);
  const [testResults, setTestResults] = useState(null);
  const [hasChanges, setHasChanges] = useState(false);
  const [showResetConfirm, setShowResetConfirm] = useState(false);
  const [showImportExport, setShowImportExport] = useState(false);

  const {
    service,
    isLoading,
    error
  } = useDeepCode();

  // Load configuration on mount
  useEffect(() => {
    loadConfiguration();
  }, []);

  const loadConfiguration = async () => {
    try {
      const savedConfig = localStorage.getItem('deepcode_config');
      if (savedConfig) {
        setConfig(JSON.parse(savedConfig));
      }
    } catch (error) {
      console.error('Error loading configuration:', error);
    }
  };

  const saveConfiguration = async () => {
    try {
      await service.updateConfig(config);
      localStorage.setItem('deepcode_config', JSON.stringify(config));
      setHasChanges(false);
      setTestResults({
        type: 'success',
        message: 'Configuration saved successfully'
      });
    } catch (error) {
      setTestResults({
        type: 'error',
        message: 'Failed to save configuration'
      });
    }
  };

  const handleConfigChange = useCallback((section, field, value) => {
    setConfig(prev => ({
      ...prev,
      [section]: {
        ...prev[section],
        [field]: value
      }
    }));
    setHasChanges(true);
  }, []);

  const handleNestedConfigChange = useCallback((section, subsection, field, value) => {
    setConfig(prev => ({
      ...prev,
      [section]: {
        ...prev[section],
        [subsection]: {
          ...prev[section][subsection],
          [field]: value
        }
      }
    }));
    setHasChanges(true);
  }, []);

  const testServerConnection = async () => {
    setIsTesting(true);
    setTestResults(null);

    try {
      const result = await service.testConnection();
      setTestResults({
        type: 'success',
        message: 'Server connection successful',
        details: result
      });
    } catch (error) {
      setTestResults({
        type: 'error',
        message: 'Server connection failed',
        details: error.message
      });
    } finally {
      setIsTesting(false);
    }
  };

  const resetConfiguration = () => {
    setConfig(DEFAULT_CONFIG);
    setHasChanges(true);
    setShowResetConfirm(false);
  };

  const exportConfiguration = () => {
    const dataStr = JSON.stringify(config, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'deepcode-config.json';
    link.click();
    URL.revokeObjectURL(url);
  };

  const importConfiguration = (event) => {
    const file = event.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const importedConfig = JSON.parse(e.target.result);
          setConfig(importedConfig);
          setHasChanges(true);
          setShowImportExport(false);
          setTestResults({
            type: 'success',
            message: 'Configuration imported successfully'
          });
        } catch (error) {
          setTestResults({
            type: 'error',
            message: 'Invalid configuration file'
          });
        }
      };
      reader.readAsText(file);
    }
  };

  const renderServerSection = () => (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium mb-2">Host</label>
          <input
            type="text"
            value={config.server.host}
            onChange={(e) => handleConfigChange('server', 'host', e.target.value)}
            className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-2">Port</label>
          <input
            type="number"
            value={config.server.port}
            onChange={(e) => handleConfigChange('server', 'port', parseInt(e.target.value))}
            className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white"
          />
        </div>
      </div>

      <div className="flex items-center space-x-4">
        <label className="flex items-center space-x-2">
          <input
            type="checkbox"
            checked={config.server.use_https}
            onChange={(e) => handleConfigChange('server', 'use_https', e.target.checked)}
            className="rounded"
          />
          <span>Use HTTPS</span>
        </label>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <div>
          <label className="block text-sm font-medium mb-2">Timeout (ms)</label>
          <input
            type="number"
            value={config.server.timeout}
            onChange={(e) => handleConfigChange('server', 'timeout', parseInt(e.target.value))}
            className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-2">Max Retries</label>
          <input
            type="number"
            value={config.server.max_retries}
            onChange={(e) => handleConfigChange('server', 'max_retries', parseInt(e.target.value))}
            className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-2">Retry Delay (ms)</label>
          <input
            type="number"
            value={config.server.retry_delay}
            onChange={(e) => handleConfigChange('server', 'retry_delay', parseInt(e.target.value))}
            className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white"
          />
        </div>
      </div>
    </div>
  );

  const renderModelsSection = () => (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium mb-2">Default Model</label>
          <select
            value={config.models.default_model}
            onChange={(e) => handleConfigChange('models', 'default_model', e.target.value)}
            className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white"
          >
            <option value="qwen3-coder">Qwen3 Coder</option>
            <option value="gpt-4">GPT-4</option>
            <option value="claude-3">Claude 3</option>
            <option value="gemini-pro">Gemini Pro</option>
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium mb-2">Fallback Model</label>
          <select
            value={config.models.fallback_model}
            onChange={(e) => handleConfigChange('models', 'fallback_model', e.target.value)}
            className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white"
          >
            <option value="gpt-4">GPT-4</option>
            <option value="qwen3-coder">Qwen3 Coder</option>
            <option value="claude-3">Claude 3</option>
            <option value="gemini-pro">Gemini Pro</option>
          </select>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <div>
          <label className="block text-sm font-medium mb-2">Temperature</label>
          <input
            type="number"
            step="0.1"
            min="0"
            max="2"
            value={config.models.temperature}
            onChange={(e) => handleConfigChange('models', 'temperature', parseFloat(e.target.value))}
            className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-2">Max Tokens</label>
          <input
            type="number"
            value={config.models.max_tokens}
            onChange={(e) => handleConfigChange('models', 'max_tokens', parseInt(e.target.value))}
            className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-2">Top P</label>
          <input
            type="number"
            step="0.1"
            min="0"
            max="1"
            value={config.models.top_p}
            onChange={(e) => handleConfigChange('models', 'top_p', parseFloat(e.target.value))}
            className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white"
          />
        </div>
      </div>

      <div className="flex items-center space-x-6">
        <label className="flex items-center space-x-2">
          <input
            type="checkbox"
            checked={config.models.streaming}
            onChange={(e) => handleConfigChange('models', 'streaming', e.target.checked)}
            className="rounded"
          />
          <span>Enable Streaming</span>
        </label>
        <label className="flex items-center space-x-2">
          <input
            type="checkbox"
            checked={config.models.cache_enabled}
            onChange={(e) => handleConfigChange('models', 'cache_enabled', e.target.checked)}
            className="rounded"
          />
          <span>Enable Caching</span>
        </label>
      </div>
    </div>
  );

  const renderSecuritySection = () => (
    <div className="space-y-6">
      <div className="space-y-4">
        <h3 className="text-lg font-semibold">Authentication</h3>
        <div className="flex items-center space-x-6">
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={config.security.enable_auth}
              onChange={(e) => handleConfigChange('security', 'enable_auth', e.target.checked)}
              className="rounded"
            />
            <span>Enable Authentication</span>
          </label>
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={config.security.api_key_required}
              onChange={(e) => handleConfigChange('security', 'api_key_required', e.target.checked)}
              className="rounded"
            />
            <span>Require API Key</span>
          </label>
        </div>
      </div>

      <div className="space-y-4">
        <h3 className="text-lg font-semibold">Rate Limiting</h3>
        <div className="flex items-center space-x-4 mb-4">
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={config.security.rate_limiting.enabled}
              onChange={(e) => handleNestedConfigChange('security', 'rate_limiting', 'enabled', e.target.checked)}
              className="rounded"
            />
            <span>Enable Rate Limiting</span>
          </label>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-2">Requests per Minute</label>
            <input
              type="number"
              value={config.security.rate_limiting.requests_per_minute}
              onChange={(e) => handleNestedConfigChange('security', 'rate_limiting', 'requests_per_minute', parseInt(e.target.value))}
              className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">Requests per Hour</label>
            <input
              type="number"
              value={config.security.rate_limiting.requests_per_hour}
              onChange={(e) => handleNestedConfigChange('security', 'rate_limiting', 'requests_per_hour', parseInt(e.target.value))}
              className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white"
            />
          </div>
        </div>
      </div>

      <div className="space-y-4">
        <h3 className="text-lg font-semibold">CORS & Logging</h3>
        <div className="flex items-center space-x-6">
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={config.security.cors_enabled}
              onChange={(e) => handleConfigChange('security', 'cors_enabled', e.target.checked)}
              className="rounded"
            />
            <span>Enable CORS</span>
          </label>
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={config.security.enable_logging}
              onChange={(e) => handleConfigChange('security', 'enable_logging', e.target.checked)}
              className="rounded"
            />
            <span>Enable Logging</span>
          </label>
        </div>
        <div>
          <label className="block text-sm font-medium mb-2">Log Level</label>
          <select
            value={config.security.log_level}
            onChange={(e) => handleConfigChange('security', 'log_level', e.target.value)}
            className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white"
          >
            <option value="DEBUG">DEBUG</option>
            <option value="INFO">INFO</option>
            <option value="WARN">WARN</option>
            <option value="ERROR">ERROR</option>
          </select>
        </div>
      </div>
    </div>
  );

  const renderPerformanceSection = () => (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium mb-2">Max Concurrent Jobs</label>
          <input
            type="number"
            value={config.performance.max_concurrent_jobs}
            onChange={(e) => handleConfigChange('performance', 'max_concurrent_jobs', parseInt(e.target.value))}
            className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-2">Job Timeout (ms)</label>
          <input
            type="number"
            value={config.performance.job_timeout}
            onChange={(e) => handleConfigChange('performance', 'job_timeout', parseInt(e.target.value))}
            className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white"
          />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium mb-2">Memory Limit (MB)</label>
          <input
            type="number"
            value={config.performance.memory_limit_mb}
            onChange={(e) => handleConfigChange('performance', 'memory_limit_mb', parseInt(e.target.value))}
            className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-2">CPU Limit (%)</label>
          <input
            type="number"
            value={config.performance.cpu_limit_percent}
            onChange={(e) => handleConfigChange('performance', 'cpu_limit_percent', parseInt(e.target.value))}
            className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white"
          />
        </div>
      </div>

      <div className="flex items-center space-x-6">
        <label className="flex items-center space-x-2">
          <input
            type="checkbox"
            checked={config.performance.enable_caching}
            onChange={(e) => handleConfigChange('performance', 'enable_caching', e.target.checked)}
            className="rounded"
          />
          <span>Enable Caching</span>
        </label>
        <label className="flex items-center space-x-2">
          <input
            type="checkbox"
            checked={config.performance.parallel_processing}
            onChange={(e) => handleConfigChange('performance', 'parallel_processing', e.target.checked)}
            className="rounded"
          />
          <span>Parallel Processing</span>
        </label>
      </div>

      <div>
        <label className="block text-sm font-medium mb-2">Optimization Level</label>
        <select
          value={config.performance.optimization_level}
          onChange={(e) => handleConfigChange('performance', 'optimization_level', e.target.value)}
          className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white"
        >
          <option value="minimal">Minimal</option>
          <option value="balanced">Balanced</option>
          <option value="aggressive">Aggressive</option>
          <option value="maximum">Maximum</option>
        </select>
      </div>
    </div>
  );

  const renderIntegrationsSection = () => (
    <div className="space-y-6">
      <div className="space-y-4">
        <h3 className="text-lg font-semibold">GitHub Integration</h3>
        <div className="flex items-center space-x-4">
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={config.integrations.github.enabled}
              onChange={(e) => handleNestedConfigChange('integrations', 'github', 'enabled', e.target.checked)}
              className="rounded"
            />
            <span>Enable GitHub</span>
          </label>
        </div>
        {config.integrations.github.enabled && (
          <div className="space-y-4 pl-6">
            <div>
              <label className="block text-sm font-medium mb-2">GitHub Token</label>
              <input
                type="password"
                value={config.integrations.github.token}
                onChange={(e) => handleNestedConfigChange('integrations', 'github', 'token', e.target.value)}
                className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white"
              />
            </div>
            <div className="flex items-center space-x-6">
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={config.integrations.github.auto_commit}
                  onChange={(e) => handleNestedConfigChange('integrations', 'github', 'auto_commit', e.target.checked)}
                  className="rounded"
                />
                <span>Auto Commit</span>
              </label>
            </div>
          </div>
        )}
      </div>

      <div className="space-y-4">
        <h3 className="text-lg font-semibold">Webhooks</h3>
        <div className="flex items-center space-x-4">
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={config.integrations.webhooks.enabled}
              onChange={(e) => handleNestedConfigChange('integrations', 'webhooks', 'enabled', e.target.checked)}
              className="rounded"
            />
            <span>Enable Webhooks</span>
          </label>
        </div>
        {config.integrations.webhooks.enabled && (
          <div className="space-y-4 pl-6">
            <div>
              <label className="block text-sm font-medium mb-2">Webhook Secret</label>
              <input
                type="password"
                value={config.integrations.webhooks.secret}
                onChange={(e) => handleNestedConfigChange('integrations', 'webhooks', 'secret', e.target.value)}
                className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white"
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );

  const renderAdvancedSection = () => (
    <div className="space-y-6">
      <div className="flex items-center space-x-6">
        <label className="flex items-center space-x-2">
          <input
            type="checkbox"
            checked={config.advanced.debug_mode}
            onChange={(e) => handleConfigChange('advanced', 'debug_mode', e.target.checked)}
            className="rounded"
          />
          <span>Debug Mode</span>
        </label>
        <label className="flex items-center space-x-2">
          <input
            type="checkbox"
            checked={config.advanced.enable_telemetry}
            onChange={(e) => handleConfigChange('advanced', 'enable_telemetry', e.target.checked)}
            className="rounded"
          />
          <span>Enable Telemetry</span>
        </label>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium mb-2">Custom Templates Directory</label>
          <input
            type="text"
            value={config.advanced.custom_templates_dir}
            onChange={(e) => handleConfigChange('advanced', 'custom_templates_dir', e.target.value)}
            className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white"
            placeholder="Path to custom templates"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-2">Output Directory</label>
          <input
            type="text"
            value={config.advanced.output_dir}
            onChange={(e) => handleConfigChange('advanced', 'output_dir', e.target.value)}
            className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white"
            placeholder="./deepcode_output"
          />
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <div>
          <label className="block text-sm font-medium mb-2">Cleanup Interval (s)</label>
          <input
            type="number"
            value={config.advanced.temp_cleanup_interval}
            onChange={(e) => handleConfigChange('advanced', 'temp_cleanup_interval', parseInt(e.target.value))}
            className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-2">Max Log Files</label>
          <input
            type="number"
            value={config.advanced.max_log_files}
            onChange={(e) => handleConfigChange('advanced', 'max_log_files', parseInt(e.target.value))}
            className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-2">Log File Size (MB)</label>
          <input
            type="number"
            value={config.advanced.log_file_size_mb}
            onChange={(e) => handleConfigChange('advanced', 'log_file_size_mb', parseInt(e.target.value))}
            className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white"
          />
        </div>
      </div>
    </div>
  );

  const renderSectionContent = () => {
    switch (activeSection) {
      case 'server': return renderServerSection();
      case 'models': return renderModelsSection();
      case 'security': return renderSecuritySection();
      case 'performance': return renderPerformanceSection();
      case 'integrations': return renderIntegrationsSection();
      case 'advanced': return renderAdvancedSection();
      default: return null;
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white p-6">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">DeepCode Configuration</h1>
          <p className="text-gray-400">Configure DeepCode server settings, models, security, and performance options</p>
        </div>

        <div className="flex gap-6">
          {/* Sidebar */}
          <div className="w-64 bg-gray-800 rounded-lg p-4">
            <nav className="space-y-2">
              {CONFIG_SECTIONS.map((section) => (
                <button
                  key={section.id}
                  onClick={() => setActiveSection(section.id)}
                  className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${
                    activeSection === section.id
                      ? 'bg-blue-600 text-white'
                      : 'text-gray-300 hover:bg-gray-700'
                  }`}
                >
                  <section.icon size={20} />
                  <span>{section.name}</span>
                </button>
              ))}
            </nav>
          </div>

          {/* Main Content */}
          <div className="flex-1 bg-gray-800 rounded-lg p-6">
            <div className="mb-6 flex items-center justify-between">
              <h2 className="text-2xl font-semibold">
                {CONFIG_SECTIONS.find(s => s.id === activeSection)?.name}
              </h2>

              <div className="flex items-center space-x-3">
                <button
                  onClick={testServerConnection}
                  disabled={isTesting}
                  className="flex items-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors disabled:opacity-50"
                >
                  <TestTube size={16} />
                  <span>{isTesting ? 'Testing...' : 'Test Connection'}</span>
                </button>

                <button
                  onClick={() => setShowImportExport(!showImportExport)}
                  className="flex items-center space-x-2 px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
                >
                  <Upload size={16} />
                  <span>Import/Export</span>
                </button>

                <button
                  onClick={() => setShowResetConfirm(true)}
                  className="flex items-center space-x-2 px-4 py-2 bg-red-600 hover:bg-red-700 rounded-lg transition-colors"
                >
                  <RotateCcw size={16} />
                  <span>Reset</span>
                </button>

                <button
                  onClick={saveConfiguration}
                  disabled={!hasChanges || isLoading}
                  className="flex items-center space-x-2 px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg transition-colors disabled:opacity-50"
                >
                  <Save size={16} />
                  <span>{isLoading ? 'Saving...' : 'Save'}</span>
                </button>
              </div>
            </div>

            {/* Import/Export Panel */}
            <AnimatePresence>
              {showImportExport && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="mb-6 p-4 bg-gray-700 rounded-lg"
                >
                  <div className="flex items-center space-x-4">
                    <button
                      onClick={exportConfiguration}
                      className="flex items-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
                    >
                      <Download size={16} />
                      <span>Export Config</span>
                    </button>
                    <div>
                      <input
                        type="file"
                        accept=".json"
                        onChange={importConfiguration}
                        className="hidden"
                        id="import-config"
                      />
                      <label
                        htmlFor="import-config"
                        className="flex items-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors cursor-pointer"
                      >
                        <Upload size={16} />
                        <span>Import Config</span>
                      </label>
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Test Results */}
            <AnimatePresence>
              {testResults && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className={`mb-6 p-4 rounded-lg ${
                    testResults.type === 'success'
                      ? 'bg-green-900 border border-green-700'
                      : 'bg-red-900 border border-red-700'
                  }`}
                >
                  <div className="flex items-center space-x-2">
                    {testResults.type === 'success' ? (
                      <CheckCircle size={20} className="text-green-400" />
                    ) : (
                      <XCircle size={20} className="text-red-400" />
                    )}
                    <span className="font-medium">{testResults.message}</span>
                  </div>
                  {testResults.details && (
                    <p className="mt-2 text-sm opacity-80">{testResults.details}</p>
                  )}
                </motion.div>
              )}
            </AnimatePresence>

            {/* Reset Confirmation */}
            <AnimatePresence>
              {showResetConfirm && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="mb-6 p-4 bg-yellow-900 border border-yellow-700 rounded-lg"
                >
                  <div className="flex items-center space-x-2 mb-4">
                    <AlertTriangle size={20} className="text-yellow-400" />
                    <span className="font-medium">Reset Configuration</span>
                  </div>
                  <p className="mb-4">Are you sure you want to reset all settings to default values? This action cannot be undone.</p>
                  <div className="flex items-center space-x-3">
                    <button
                      onClick={resetConfiguration}
                      className="px-4 py-2 bg-red-600 hover:bg-red-700 rounded-lg transition-colors"
                    >
                      Yes, Reset
                    </button>
                    <button
                      onClick={() => setShowResetConfirm(false)}
                      className="px-4 py-2 bg-gray-600 hover:bg-gray-700 rounded-lg transition-colors"
                    >
                      Cancel
                    </button>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Configuration Content */}
            <div className="space-y-6">
              {renderSectionContent()}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DeepCodeConfig;