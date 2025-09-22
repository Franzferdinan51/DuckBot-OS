import React, { useState, useEffect, useCallback } from 'react';
import {
  Settings, Database, Search, Brain, Cpu, Network, Shield,
  Save, RefreshCw, TestTube, Download, Upload, FileText,
  CheckCircle, XCircle, AlertCircle, Info, Zap, BarChart3,
  Sliders, Key, Globe, Server, HardDrive, Activity, Users,
  Filter, Hash, Target, Layers, Workflow, ZapOff, Play,
  Pause, RotateCcw, Trash2, Plus, Minus, Eye, EyeOff,
  ChevronDown, ChevronUp, HelpCircle
} from 'lucide-react';

// Configuration Categories
const CONFIG_CATEGORIES = {
  EMBEDDING: 'embedding',
  SEARCH: 'search',
  PERFORMANCE: 'performance',
  SECURITY: 'security',
  INTEGRATION: 'integration',
  ADVANCED: 'advanced'
};

// Embedding Providers
const EMBEDDING_PROVIDERS = {
  OPENAI: 'openai',
  LOCAL: 'local',
  HUGGINGFACE: 'huggingface',
  COHERE: 'cohere',
  ANTHROPIC: 'anthropic',
  GOOGLE: 'google'
};

// Search Strategies
const SEARCH_STRATEGIES = {
  VECTOR: 'vector',
  HYBRID: 'hybrid',
  KEYWORD: 'keyword',
  SEMANTIC: 'semantic',
  FULLTEXT: 'fulltext'
};

// Performance Profiles
const PERFORMANCE_PROFILES = {
  BALANCED: 'balanced',
  SPEED: 'speed',
  QUALITY: 'quality',
  MEMORY: 'memory'
};

const RAGConfig = ({ onClose }) => {
  // Configuration State
  const [activeSection, setActiveSection] = useState(CONFIG_CATEGORIES.EMBEDDING);
  const [config, setConfig] = useState({
    embedding: {
      provider: EMBEDDING_PROVIDERS.LOCAL,
      model: 'all-MiniLM-L6-v2',
      apiKey: '',
      baseUrl: '',
      chunkSize: 512,
      chunkOverlap: 50,
      batchSize: 32,
      maxTokens: 8192,
      dimensions: 384,
      normalize: true,
      cacheEmbeddings: true
    },
    search: {
      strategy: SEARCH_STRATEGIES.HYBRID,
      topK: 5,
      scoreThreshold: 0.7,
      maxResults: 10,
      enableReranking: true,
      rerankerModel: 'cross-encoder/ms-marco-MiniLM-L-6-v2',
      enableFiltering: true,
      enableFaceting: true,
      enableSynonyms: true,
      fuzzySearch: true,
      fuzzyThreshold: 0.8
    },
    performance: {
      profile: PERFORMANCE_PROFILES.BALANCED,
      enableCaching: true,
      cacheSize: 1000,
      cacheTTL: 3600,
      enableParallel: true,
      maxParallel: 4,
      connectionPoolSize: 10,
      timeout: 30000,
      maxRetries: 3,
      backoffStrategy: 'exponential',
      preloadIndexes: true,
      warmupQueries: true
    },
    security: {
      enableAuthentication: false,
      apiKeyRequired: false,
      allowedOrigins: ['*'],
      rateLimit: {
        enabled: true,
        requestsPerMinute: 60,
        burstLimit: 10
      },
      encryption: {
        enabled: false,
        algorithm: 'AES-256-GCM',
        keyRotationDays: 90
      },
      audit: {
        enabled: true,
        logLevel: 'info',
        retentionDays: 30
      }
    },
    integration: {
      apis: {
        rest: true,
        graphql: false,
        websocket: true
      },
      webhooks: {
        enabled: false,
        url: '',
        events: ['document.indexed', 'search.performed', 'error']
      },
      monitoring: {
        enabled: true,
        metrics: ['performance', 'usage', 'errors'],
        exportInterval: 300
      }
    },
    advanced: {
      debug: false,
      verboseLogging: false,
      experimentalFeatures: false,
      customPreprocessors: [],
      customPostprocessors: [],
      plugins: {
        enabled: false,
        directory: './plugins',
        autoLoad: true
      },
      optimization: {
        autoOptimize: true,
        optimizeInterval: 86400,
        analyzeQueries: true,
        suggestImprovements: true
      }
    }
  });

  // UI State
  const [hasChanges, setHasChanges] = useState(false);
  const [isTesting, setIsTesting] = useState(false);
  const [testResults, setTestResults] = useState(null);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [validationErrors, setValidationErrors] = useState({});
  const [showResetConfirm, setShowResetConfirm] = useState(false);

  // Load configuration on mount
  useEffect(() => {
    loadConfiguration();
  }, []);

  const loadConfiguration = useCallback(async () => {
    try {
      const response = await fetch('http://localhost:8787/api/rag/config');
      if (response.ok) {
        const loadedConfig = await response.json();
        setConfig(loadedConfig);
      }
    } catch (error) {
      console.error('Failed to load configuration:', error);
    }
  }, []);

  const saveConfiguration = useCallback(async () => {
    try {
      // Validate configuration
      const errors = validateConfiguration();
      if (Object.keys(errors).length > 0) {
        setValidationErrors(errors);
        return;
      }

      const response = await fetch('http://localhost:8787/api/rag/config', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
      });

      if (response.ok) {
        setHasChanges(false);
        setValidationErrors({});
        alert('Configuration saved successfully!');
      } else {
        alert('Failed to save configuration');
      }
    } catch (error) {
      console.error('Failed to save configuration:', error);
      alert('Failed to save configuration');
    }
  }, [config]);

  const testConfiguration = useCallback(async () => {
    setIsTesting(true);
    try {
      const response = await fetch('http://localhost:8787/api/rag/config/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
      });

      if (response.ok) {
        const results = await response.json();
        setTestResults(results);
      } else {
        setTestResults({ success: false, errors: ['Configuration test failed'] });
      }
    } catch (error) {
      console.error('Test failed:', error);
      setTestResults({ success: false, errors: [error.message] });
    } finally {
      setIsTesting(false);
    }
  }, [config]);

  const validateConfiguration = () => {
    const errors = {};

    // Validate embedding configuration
    if (!config.embedding.model) {
      errors.embedding = errors.embedding || {};
      errors.embedding.model = 'Model is required';
    }
    if (config.embedding.chunkSize < 1 || config.embedding.chunkSize > 2000) {
      errors.embedding = errors.embedding || {};
      errors.embedding.chunkSize = 'Chunk size must be between 1 and 2000';
    }

    // Validate search configuration
    if (config.search.topK < 1 || config.search.topK > 100) {
      errors.search = errors.search || {};
      errors.search.topK = 'Top K must be between 1 and 100';
    }
    if (config.search.scoreThreshold < 0 || config.search.scoreThreshold > 1) {
      errors.search = errors.search || {};
      errors.search.scoreThreshold = 'Score threshold must be between 0 and 1';
    }

    // Validate performance configuration
    if (config.performance.cacheSize < 0) {
      errors.performance = errors.performance || {};
      errors.performance.cacheSize = 'Cache size must be non-negative';
    }
    if (config.performance.maxParallel < 1 || config.performance.maxParallel > 32) {
      errors.performance = errors.performance || {};
      errors.performance.maxParallel = 'Max parallel must be between 1 and 32';
    }

    return errors;
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

  const resetConfiguration = useCallback(() => {
    setShowResetConfirm(true);
  }, []);

  const handleResetConfirm = useCallback(() => {
    loadConfiguration();
    setHasChanges(false);
    setValidationErrors({});
    setShowResetConfirm(false);
  }, [loadConfiguration]);

  const handleResetCancel = useCallback(() => {
    setShowResetConfirm(false);
  }, []);

  const exportConfiguration = useCallback(() => {
    const dataStr = JSON.stringify(config, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `rag-config-${new Date().toISOString().split('T')[0]}.json`;
    link.click();
    URL.revokeObjectURL(url);
  }, [config]);

  const importConfiguration = useCallback(async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      const text = await file.text();
      const importedConfig = JSON.parse(text);
      setConfig(importedConfig);
      setHasChanges(true);
      alert('Configuration imported successfully!');
    } catch (error) {
      alert('Failed to import configuration: Invalid file format');
    }
    event.target.value = '';
  }, []);

  const renderEmbeddingConfig = () => (
    <div className="space-y-6">
      {/* Provider Selection */}
      <div className="bg-slate-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Embedding Provider</h3>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          {Object.entries(EMBEDDING_PROVIDERS).map(([key, value]) => (
            <button
              key={value}
              onClick={() => handleConfigChange('embedding', 'provider', value)}
              className={`p-4 rounded-lg border-2 transition-colors ${
                config.embedding.provider === value
                  ? 'border-blue-500 bg-blue-500/20'
                  : 'border-slate-600 hover:border-slate-500 bg-slate-700'
              }`}
            >
              <div className="text-lg mb-2">{key === 'LOCAL' ? '🏠' : '🌐'}</div>
              <div className="text-white font-medium">{key}</div>
              <div className="text-xs text-slate-400 mt-1">{value}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Model Configuration */}
      <div className="bg-slate-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Model Configuration</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm text-slate-400 mb-2">Model Name</label>
            <input
              type="text"
              value={config.embedding.model}
              onChange={(e) => handleConfigChange('embedding', 'model', e.target.value)}
              className={`w-full bg-slate-700 text-white rounded px-3 py-2 border ${
                validationErrors.embedding?.model ? 'border-red-500' : 'border-slate-600'
              } focus:border-blue-500 focus:outline-none`}
            />
            {validationErrors.embedding?.model && (
              <p className="text-red-400 text-xs mt-1">{validationErrors.embedding.model}</p>
            )}
          </div>
          <div>
            <label className="block text-sm text-slate-400 mb-2">Dimensions</label>
            <input
              type="number"
              value={config.embedding.dimensions}
              onChange={(e) => handleConfigChange('embedding', 'dimensions', parseInt(e.target.value))}
              className="w-full bg-slate-700 text-white rounded px-3 py-2 border border-slate-600 focus:border-blue-500 focus:outline-none"
            />
          </div>
          {config.embedding.provider !== EMBEDDING_PROVIDERS.LOCAL && (
            <>
              <div>
                <label className="block text-sm text-slate-400 mb-2">API Key</label>
                <div className="relative">
                  <input
                    type={showAdvanced ? 'text' : 'password'}
                    value={config.embedding.apiKey}
                    onChange={(e) => handleConfigChange('embedding', 'apiKey', e.target.value)}
                    className="w-full bg-slate-700 text-white rounded px-3 py-2 pr-10 border border-slate-600 focus:border-blue-500 focus:outline-none"
                  />
                  <button
                    onClick={() => setShowAdvanced(!showAdvanced)}
                    className="absolute right-2 top-1/2 transform -translate-y-1/2 text-slate-400 hover:text-white"
                  >
                    {showAdvanced ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>
              <div>
                <label className="block text-sm text-slate-400 mb-2">Base URL</label>
                <input
                  type="text"
                  value={config.embedding.baseUrl}
                  onChange={(e) => handleConfigChange('embedding', 'baseUrl', e.target.value)}
                  className="w-full bg-slate-700 text-white rounded px-3 py-2 border border-slate-600 focus:border-blue-500 focus:outline-none"
                  placeholder="https://api.example.com"
                />
              </div>
            </>
          )}
        </div>
      </div>

      {/* Chunking Configuration */}
      <div className="bg-slate-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Chunking Strategy</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm text-slate-400 mb-2">Chunk Size</label>
            <input
              type="number"
              value={config.embedding.chunkSize}
              onChange={(e) => handleConfigChange('embedding', 'chunkSize', parseInt(e.target.value))}
              className={`w-full bg-slate-700 text-white rounded px-3 py-2 border ${
                validationErrors.embedding?.chunkSize ? 'border-red-500' : 'border-slate-600'
              } focus:border-blue-500 focus:outline-none`}
            />
            {validationErrors.embedding?.chunkSize && (
              <p className="text-red-400 text-xs mt-1">{validationErrors.embedding.chunkSize}</p>
            )}
          </div>
          <div>
            <label className="block text-sm text-slate-400 mb-2">Chunk Overlap</label>
            <input
              type="number"
              value={config.embedding.chunkOverlap}
              onChange={(e) => handleConfigChange('embedding', 'chunkOverlap', parseInt(e.target.value))}
              className="w-full bg-slate-700 text-white rounded px-3 py-2 border border-slate-600 focus:border-blue-500 focus:outline-none"
            />
          </div>
          <div>
            <label className="block text-sm text-slate-400 mb-2">Batch Size</label>
            <input
              type="number"
              value={config.embedding.batchSize}
              onChange={(e) => handleConfigChange('embedding', 'batchSize', parseInt(e.target.value))}
              className="w-full bg-slate-700 text-white rounded px-3 py-2 border border-slate-600 focus:border-blue-500 focus:outline-none"
            />
          </div>
        </div>
        <div className="mt-4 space-y-3">
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={config.embedding.normalize}
              onChange={(e) => handleConfigChange('embedding', 'normalize', e.target.checked)}
              className="rounded text-blue-600"
            />
            <span className="text-sm text-slate-300">Normalize embeddings</span>
          </label>
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={config.embedding.cacheEmbeddings}
              onChange={(e) => handleConfigChange('embedding', 'cacheEmbeddings', e.target.checked)}
              className="rounded text-blue-600"
            />
            <span className="text-sm text-slate-300">Cache embeddings</span>
          </label>
        </div>
      </div>
    </div>
  );

  const renderSearchConfig = () => (
    <div className="space-y-6">
      {/* Search Strategy */}
      <div className="bg-slate-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Search Strategy</h3>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          {Object.entries(SEARCH_STRATEGIES).map(([key, value]) => (
            <button
              key={value}
              onClick={() => handleConfigChange('search', 'strategy', value)}
              className={`p-4 rounded-lg border-2 transition-colors ${
                config.search.strategy === value
                  ? 'border-blue-500 bg-blue-500/20'
                  : 'border-slate-600 hover:border-slate-500 bg-slate-700'
              }`}
            >
              <div className="text-lg mb-2">
                {value === 'vector' ? '🔍' : value === 'hybrid' ? '🎯' : value === 'keyword' ? '🔑' : value === 'semantic' ? '🧠' : '📄'}
              </div>
              <div className="text-white font-medium capitalize">{key}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Search Parameters */}
      <div className="bg-slate-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Search Parameters</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm text-slate-400 mb-2">Top K Results</label>
            <input
              type="number"
              value={config.search.topK}
              onChange={(e) => handleConfigChange('search', 'topK', parseInt(e.target.value))}
              className={`w-full bg-slate-700 text-white rounded px-3 py-2 border ${
                validationErrors.search?.topK ? 'border-red-500' : 'border-slate-600'
              } focus:border-blue-500 focus:outline-none`}
            />
            {validationErrors.search?.topK && (
              <p className="text-red-400 text-xs mt-1">{validationErrors.search.topK}</p>
            )}
          </div>
          <div>
            <label className="block text-sm text-slate-400 mb-2">Score Threshold</label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              value={config.search.scoreThreshold}
              onChange={(e) => handleConfigChange('search', 'scoreThreshold', parseFloat(e.target.value))}
              className="w-full"
            />
            <div className="text-xs text-slate-400 mt-1">{config.search.scoreThreshold}</div>
            {validationErrors.search?.scoreThreshold && (
              <p className="text-red-400 text-xs mt-1">{validationErrors.search.scoreThreshold}</p>
            )}
          </div>
          <div>
            <label className="block text-sm text-slate-400 mb-2">Max Results</label>
            <input
              type="number"
              value={config.search.maxResults}
              onChange={(e) => handleConfigChange('search', 'maxResults', parseInt(e.target.value))}
              className="w-full bg-slate-700 text-white rounded px-3 py-2 border border-slate-600 focus:border-blue-500 focus:outline-none"
            />
          </div>
        </div>
      </div>

      {/* Advanced Search Features */}
      <div className="bg-slate-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Advanced Features</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h4 className="text-white font-medium mb-3">Reranking</h4>
            <div className="space-y-3">
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={config.search.enableReranking}
                  onChange={(e) => handleConfigChange('search', 'enableReranking', e.target.checked)}
                  className="rounded text-blue-600"
                />
                <span className="text-sm text-slate-300">Enable reranking</span>
              </label>
              {config.search.enableReranking && (
                <div>
                  <label className="block text-sm text-slate-400 mb-2">Reranker Model</label>
                  <select
                    value={config.search.rerankerModel}
                    onChange={(e) => handleConfigChange('search', 'rerankerModel', e.target.value)}
                    className="w-full bg-slate-700 text-white rounded px-3 py-2 border border-slate-600"
                  >
                    <option value="cross-encoder/ms-marco-MiniLM-L-6-v2">MiniLM (default)</option>
                    <option value="cross-encoder/ms-marco-TinyBERT-L-6">TinyBERT</option>
                    <option value="cross-encoder/quora-distilroberta-base">Quora DistilRoBERTa</option>
                  </select>
                </div>
              )}
            </div>
          </div>

          <div>
            <h4 className="text-white font-medium mb-3">Enhanced Search</h4>
            <div className="space-y-3">
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={config.search.enableFiltering}
                  onChange={(e) => handleConfigChange('search', 'enableFiltering', e.target.checked)}
                  className="rounded text-blue-600"
                />
                <span className="text-sm text-slate-300">Enable filtering</span>
              </label>
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={config.search.enableFaceting}
                  onChange={(e) => handleConfigChange('search', 'enableFaceting', e.target.checked)}
                  className="rounded text-blue-600"
                />
                <span className="text-sm text-slate-300">Enable faceting</span>
              </label>
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={config.search.enableSynonyms}
                  onChange={(e) => handleConfigChange('search', 'enableSynonyms', e.target.checked)}
                  className="rounded text-blue-600"
                />
                <span className="text-sm text-slate-300">Enable synonyms</span>
              </label>
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={config.search.fuzzySearch}
                  onChange={(e) => handleConfigChange('search', 'fuzzySearch', e.target.checked)}
                  className="rounded text-blue-600"
                />
                <span className="text-sm text-slate-300">Enable fuzzy search</span>
              </label>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  const renderPerformanceConfig = () => (
    <div className="space-y-6">
      {/* Performance Profile */}
      <div className="bg-slate-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Performance Profile</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {Object.entries(PERFORMANCE_PROFILES).map(([key, value]) => (
            <button
              key={value}
              onClick={() => handleConfigChange('performance', 'profile', value)}
              className={`p-4 rounded-lg border-2 transition-colors ${
                config.performance.profile === value
                  ? 'border-blue-500 bg-blue-500/20'
                  : 'border-slate-600 hover:border-slate-500 bg-slate-700'
              }`}
            >
              <div className="text-lg mb-2">
                {value === 'balanced' ? '⚖️' : value === 'speed' ? '🚀' : value === 'quality' ? '🎯' : '💾'}
              </div>
              <div className="text-white font-medium capitalize">{key}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Caching Configuration */}
      <div className="bg-slate-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Caching</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm text-slate-400 mb-2">Cache Size</label>
            <input
              type="number"
              value={config.performance.cacheSize}
              onChange={(e) => handleConfigChange('performance', 'cacheSize', parseInt(e.target.value))}
              className={`w-full bg-slate-700 text-white rounded px-3 py-2 border ${
                validationErrors.performance?.cacheSize ? 'border-red-500' : 'border-slate-600'
              } focus:border-blue-500 focus:outline-none`}
            />
            {validationErrors.performance?.cacheSize && (
              <p className="text-red-400 text-xs mt-1">{validationErrors.performance.cacheSize}</p>
            )}
          </div>
          <div>
            <label className="block text-sm text-slate-400 mb-2">Cache TTL (seconds)</label>
            <input
              type="number"
              value={config.performance.cacheTTL}
              onChange={(e) => handleConfigChange('performance', 'cacheTTL', parseInt(e.target.value))}
              className="w-full bg-slate-700 text-white rounded px-3 py-2 border border-slate-600 focus:border-blue-500 focus:outline-none"
            />
          </div>
          <div>
            <label className="block text-sm text-slate-400 mb-2">Connection Pool Size</label>
            <input
              type="number"
              value={config.performance.connectionPoolSize}
              onChange={(e) => handleConfigChange('performance', 'connectionPoolSize', parseInt(e.target.value))}
              className="w-full bg-slate-700 text-white rounded px-3 py-2 border border-slate-600 focus:border-blue-500 focus:outline-none"
            />
          </div>
        </div>
        <div className="mt-4 space-y-3">
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={config.performance.enableCaching}
              onChange={(e) => handleConfigChange('performance', 'enableCaching', e.target.checked)}
              className="rounded text-blue-600"
            />
            <span className="text-sm text-slate-300">Enable caching</span>
          </label>
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={config.performance.enableParallel}
              onChange={(e) => handleConfigChange('performance', 'enableParallel', e.target.checked)}
              className="rounded text-blue-600"
            />
            <span className="text-sm text-slate-300">Enable parallel processing</span>
          </label>
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={config.performance.preloadIndexes}
              onChange={(e) => handleConfigChange('performance', 'preloadIndexes', e.target.checked)}
              className="rounded text-blue-600"
            />
            <span className="text-sm text-slate-300">Preload indexes</span>
          </label>
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={config.performance.warmupQueries}
              onChange={(e) => handleConfigChange('performance', 'warmupQueries', e.target.checked)}
              className="rounded text-blue-600"
            />
            <span className="text-sm text-slate-300">Warmup queries</span>
          </label>
        </div>
      </div>

      {/* Resource Management */}
      <div className="bg-slate-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Resource Management</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm text-slate-400 mb-2">Max Parallel Requests</label>
            <input
              type="number"
              value={config.performance.maxParallel}
              onChange={(e) => handleConfigChange('performance', 'maxParallel', parseInt(e.target.value))}
              className={`w-full bg-slate-700 text-white rounded px-3 py-2 border ${
                validationErrors.performance?.maxParallel ? 'border-red-500' : 'border-slate-600'
              } focus:border-blue-500 focus:outline-none`}
            />
            {validationErrors.performance?.maxParallel && (
              <p className="text-red-400 text-xs mt-1">{validationErrors.performance.maxParallel}</p>
            )}
          </div>
          <div>
            <label className="block text-sm text-slate-400 mb-2">Timeout (ms)</label>
            <input
              type="number"
              value={config.performance.timeout}
              onChange={(e) => handleConfigChange('performance', 'timeout', parseInt(e.target.value))}
              className="w-full bg-slate-700 text-white rounded px-3 py-2 border border-slate-600 focus:border-blue-500 focus:outline-none"
            />
          </div>
          <div>
            <label className="block text-sm text-slate-400 mb-2">Max Retries</label>
            <input
              type="number"
              value={config.performance.maxRetries}
              onChange={(e) => handleConfigChange('performance', 'maxRetries', parseInt(e.target.value))}
              className="w-full bg-slate-700 text-white rounded px-3 py-2 border border-slate-600 focus:border-blue-500 focus:outline-none"
            />
          </div>
        </div>
        <div className="mt-4">
          <label className="block text-sm text-slate-400 mb-2">Backoff Strategy</label>
          <select
            value={config.performance.backoffStrategy}
            onChange={(e) => handleConfigChange('performance', 'backoffStrategy', e.target.value)}
            className="w-full bg-slate-700 text-white rounded px-3 py-2 border border-slate-600"
          >
            <option value="exponential">Exponential</option>
            <option value="linear">Linear</option>
            <option value="fixed">Fixed</option>
          </select>
        </div>
      </div>
    </div>
  );

  const renderSecurityConfig = () => (
    <div className="space-y-6">
      {/* Authentication */}
      <div className="bg-slate-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Authentication</h3>
        <div className="space-y-3">
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={config.security.enableAuthentication}
              onChange={(e) => handleConfigChange('security', 'enableAuthentication', e.target.checked)}
              className="rounded text-blue-600"
            />
            <span className="text-sm text-slate-300">Enable authentication</span>
          </label>
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={config.security.apiKeyRequired}
              onChange={(e) => handleConfigChange('security', 'apiKeyRequired', e.target.checked)}
              className="rounded text-blue-600"
            />
            <span className="text-sm text-slate-300">Require API key</span>
          </label>
        </div>
      </div>

      {/* Rate Limiting */}
      <div className="bg-slate-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Rate Limiting</h3>
        <div className="space-y-3">
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={config.security.rateLimit.enabled}
              onChange={(e) => handleNestedConfigChange('security', 'rateLimit', 'enabled', e.target.checked)}
              className="rounded text-blue-600"
            />
            <span className="text-sm text-slate-300">Enable rate limiting</span>
          </label>
          {config.security.rateLimit.enabled && (
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-slate-400 mb-2">Requests per minute</label>
                <input
                  type="number"
                  value={config.security.rateLimit.requestsPerMinute}
                  onChange={(e) => handleNestedConfigChange('security', 'rateLimit', 'requestsPerMinute', parseInt(e.target.value))}
                  className="w-full bg-slate-700 text-white rounded px-3 py-2 border border-slate-600 focus:border-blue-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-sm text-slate-400 mb-2">Burst limit</label>
                <input
                  type="number"
                  value={config.security.rateLimit.burstLimit}
                  onChange={(e) => handleNestedConfigChange('security', 'rateLimit', 'burstLimit', parseInt(e.target.value))}
                  className="w-full bg-slate-700 text-white rounded px-3 py-2 border border-slate-600 focus:border-blue-500 focus:outline-none"
                />
              </div>
            </div>
          )}
        </div>
      </div>

      {/* CORS Configuration */}
      <div className="bg-slate-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">CORS Configuration</h3>
        <div>
          <label className="block text-sm text-slate-400 mb-2">Allowed Origins</label>
          <textarea
            value={config.security.allowedOrigins.join('\n')}
            onChange={(e) => handleConfigChange('security', 'allowedOrigins', e.target.value.split('\n').filter(Boolean))}
            className="w-full bg-slate-700 text-white rounded px-3 py-2 border border-slate-600 focus:border-blue-500 focus:outline-none h-24 resize-none"
            placeholder="https://example.com&#10;https://app.example.com"
          />
        </div>
      </div>

      {/* Encryption */}
      <div className="bg-slate-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Encryption</h3>
        <div className="space-y-3">
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={config.security.encryption.enabled}
              onChange={(e) => handleNestedConfigChange('security', 'encryption', 'enabled', e.target.checked)}
              className="rounded text-blue-600"
            />
            <span className="text-sm text-slate-300">Enable encryption</span>
          </label>
          {config.security.encryption.enabled && (
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-slate-400 mb-2">Algorithm</label>
                <select
                  value={config.security.encryption.algorithm}
                  onChange={(e) => handleNestedConfigChange('security', 'encryption', 'algorithm', e.target.value)}
                  className="w-full bg-slate-700 text-white rounded px-3 py-2 border border-slate-600"
                >
                  <option value="AES-256-GCM">AES-256-GCM</option>
                  <option value="AES-128-GCM">AES-128-GCM</option>
                  <option value="ChaCha20-Poly1305">ChaCha20-Poly1305</option>
                </select>
              </div>
              <div>
                <label className="block text-sm text-slate-400 mb-2">Key rotation (days)</label>
                <input
                  type="number"
                  value={config.security.encryption.keyRotationDays}
                  onChange={(e) => handleNestedConfigChange('security', 'encryption', 'keyRotationDays', parseInt(e.target.value))}
                  className="w-full bg-slate-700 text-white rounded px-3 py-2 border border-slate-600 focus:border-blue-500 focus:outline-none"
                />
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Audit Logging */}
      <div className="bg-slate-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Audit Logging</h3>
        <div className="space-y-3">
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={config.security.audit.enabled}
              onChange={(e) => handleNestedConfigChange('security', 'audit', 'enabled', e.target.checked)}
              className="rounded text-blue-600"
            />
            <span className="text-sm text-slate-300">Enable audit logging</span>
          </label>
          {config.security.audit.enabled && (
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-slate-400 mb-2">Log level</label>
                <select
                  value={config.security.audit.logLevel}
                  onChange={(e) => handleNestedConfigChange('security', 'audit', 'logLevel', e.target.value)}
                  className="w-full bg-slate-700 text-white rounded px-3 py-2 border border-slate-600"
                >
                  <option value="debug">Debug</option>
                  <option value="info">Info</option>
                  <option value="warn">Warning</option>
                  <option value="error">Error</option>
                </select>
              </div>
              <div>
                <label className="block text-sm text-slate-400 mb-2">Retention (days)</label>
                <input
                  type="number"
                  value={config.security.audit.retentionDays}
                  onChange={(e) => handleNestedConfigChange('security', 'audit', 'retentionDays', parseInt(e.target.value))}
                  className="w-full bg-slate-700 text-white rounded px-3 py-2 border border-slate-600 focus:border-blue-500 focus:outline-none"
                />
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );

  const renderIntegrationConfig = () => (
    <div className="space-y-6">
      {/* API Configuration */}
      <div className="bg-slate-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">API Endpoints</h3>
        <div className="space-y-3">
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={config.integration.apis.rest}
              onChange={(e) => handleNestedConfigChange('integration', 'apis', 'rest', e.target.checked)}
              className="rounded text-blue-600"
            />
            <span className="text-sm text-slate-300">REST API</span>
          </label>
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={config.integration.apis.graphql}
              onChange={(e) => handleNestedConfigChange('integration', 'apis', 'graphql', e.target.checked)}
              className="rounded text-blue-600"
            />
            <span className="text-sm text-slate-300">GraphQL API</span>
          </label>
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={config.integration.apis.websocket}
              onChange={(e) => handleNestedConfigChange('integration', 'apis', 'websocket', e.target.checked)}
              className="rounded text-blue-600"
            />
            <span className="text-sm text-slate-300">WebSocket API</span>
          </label>
        </div>
      </div>

      {/* Webhooks */}
      <div className="bg-slate-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Webhooks</h3>
        <div className="space-y-3">
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={config.integration.webhooks.enabled}
              onChange={(e) => handleNestedConfigChange('integration', 'webhooks', 'enabled', e.target.checked)}
              className="rounded text-blue-600"
            />
            <span className="text-sm text-slate-300">Enable webhooks</span>
          </label>
          {config.integration.webhooks.enabled && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm text-slate-400 mb-2">Webhook URL</label>
                <input
                  type="url"
                  value={config.integration.webhooks.url}
                  onChange={(e) => handleNestedConfigChange('integration', 'webhooks', 'url', e.target.value)}
                  className="w-full bg-slate-700 text-white rounded px-3 py-2 border border-slate-600 focus:border-blue-500 focus:outline-none"
                  placeholder="https://your-webhook-url.com/endpoint"
                />
              </div>
              <div>
                <label className="block text-sm text-slate-400 mb-2">Events</label>
                <div className="space-y-2">
                  {config.integration.webhooks.events.map((event, index) => (
                    <label key={index} className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        checked={true}
                        onChange={() => {/* Event selection would need more complex state */}}
                        className="rounded text-blue-600"
                      />
                      <span className="text-sm text-slate-300">{event}</span>
                    </label>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Monitoring */}
      <div className="bg-slate-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Monitoring & Metrics</h3>
        <div className="space-y-3">
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={config.integration.monitoring.enabled}
              onChange={(e) => handleNestedConfigChange('integration', 'monitoring', 'enabled', e.target.checked)}
              className="rounded text-blue-600"
            />
            <span className="text-sm text-slate-300">Enable monitoring</span>
          </label>
          {config.integration.monitoring.enabled && (
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-slate-400 mb-2">Export interval (seconds)</label>
                <input
                  type="number"
                  value={config.integration.monitoring.exportInterval}
                  onChange={(e) => handleNestedConfigChange('integration', 'monitoring', 'exportInterval', parseInt(e.target.value))}
                  className="w-full bg-slate-700 text-white rounded px-3 py-2 border border-slate-600 focus:border-blue-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-sm text-slate-400 mb-2">Metrics</label>
                <div className="space-y-2">
                  {config.integration.monitoring.metrics.map((metric, index) => (
                    <label key={index} className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        checked={true}
                        className="rounded text-blue-600"
                      />
                      <span className="text-sm text-slate-300 capitalize">{metric}</span>
                    </label>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );

  const renderAdvancedConfig = () => (
    <div className="space-y-6">
      {/* Debug Options */}
      <div className="bg-slate-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Debug & Logging</h3>
        <div className="space-y-3">
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={config.advanced.debug}
              onChange={(e) => handleConfigChange('advanced', 'debug', e.target.checked)}
              className="rounded text-blue-600"
            />
            <span className="text-sm text-slate-300">Enable debug mode</span>
          </label>
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={config.advanced.verboseLogging}
              onChange={(e) => handleConfigChange('advanced', 'verboseLogging', e.target.checked)}
              className="rounded text-blue-600"
            />
            <span className="text-sm text-slate-300">Verbose logging</span>
          </label>
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={config.advanced.experimentalFeatures}
              onChange={(e) => handleConfigChange('advanced', 'experimentalFeatures', e.target.checked)}
              className="rounded text-blue-600"
            />
            <span className="text-sm text-slate-300">Experimental features</span>
          </label>
        </div>
      </div>

      {/* Plugins */}
      <div className="bg-slate-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Plugins</h3>
        <div className="space-y-3">
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={config.advanced.plugins.enabled}
              onChange={(e) => handleNestedConfigChange('advanced', 'plugins', 'enabled', e.target.checked)}
              className="rounded text-blue-600"
            />
            <span className="text-sm text-slate-300">Enable plugins</span>
          </label>
          {config.advanced.plugins.enabled && (
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-slate-400 mb-2">Plugin directory</label>
                <input
                  type="text"
                  value={config.advanced.plugins.directory}
                  onChange={(e) => handleNestedConfigChange('advanced', 'plugins', 'directory', e.target.value)}
                  className="w-full bg-slate-700 text-white rounded px-3 py-2 border border-slate-600 focus:border-blue-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="flex items-center space-x-2 mt-6">
                  <input
                    type="checkbox"
                    checked={config.advanced.plugins.autoLoad}
                    onChange={(e) => handleNestedConfigChange('advanced', 'plugins', 'autoLoad', e.target.checked)}
                    className="rounded text-blue-600"
                  />
                  <span className="text-sm text-slate-300">Auto-load plugins</span>
                </label>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Auto-optimization */}
      <div className="bg-slate-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Auto-optimization</h3>
        <div className="space-y-3">
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={config.advanced.optimization.autoOptimize}
              onChange={(e) => handleNestedConfigChange('advanced', 'optimization', 'autoOptimize', e.target.checked)}
              className="rounded text-blue-600"
            />
            <span className="text-sm text-slate-300">Auto-optimize system</span>
          </label>
          {config.advanced.optimization.autoOptimize && (
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-slate-400 mb-2">Optimize interval (hours)</label>
                <input
                  type="number"
                  value={config.advanced.optimization.optimizeInterval / 3600}
                  onChange={(e) => handleNestedConfigChange('advanced', 'optimization', 'optimizeInterval', parseInt(e.target.value) * 3600)}
                  className="w-full bg-slate-700 text-white rounded px-3 py-2 border border-slate-600 focus:border-blue-500 focus:outline-none"
                />
              </div>
            </div>
          )}
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={config.advanced.optimization.analyzeQueries}
              onChange={(e) => handleNestedConfigChange('advanced', 'optimization', 'analyzeQueries', e.target.checked)}
              className="rounded text-blue-600"
            />
            <span className="text-sm text-slate-300">Analyze query patterns</span>
          </label>
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={config.advanced.optimization.suggestImprovements}
              onChange={(e) => handleNestedConfigChange('advanced', 'optimization', 'suggestImprovements', e.target.checked)}
              className="rounded text-blue-600"
            />
            <span className="text-sm text-slate-300">Suggest improvements</span>
          </label>
        </div>
      </div>
    </div>
  );

  // Configuration sections
  const sections = [
    { id: CONFIG_CATEGORIES.EMBEDDING, label: 'Embedding', icon: Brain, description: 'Embedding models and chunking' },
    { id: CONFIG_CATEGORIES.SEARCH, label: 'Search', icon: Search, description: 'Search algorithms and parameters' },
    { id: CONFIG_CATEGORIES.PERFORMANCE, label: 'Performance', icon: Zap, description: 'Caching and resource management' },
    { id: CONFIG_CATEGORIES.SECURITY, label: 'Security', icon: Shield, description: 'Authentication and encryption' },
    { id: CONFIG_CATEGORIES.INTEGRATION, label: 'Integration', icon: Network, description: 'APIs and webhooks' },
    { id: CONFIG_CATEGORIES.ADVANCED, label: 'Advanced', icon: Settings, description: 'Debug and experimental features' }
  ];

  return (
    <div className="h-full flex flex-col bg-slate-900 text-white">
      {/* Header */}
      <div className="flex items-center justify-between p-4 bg-slate-800 border-b border-slate-700">
        <div className="flex items-center space-x-3">
          <Settings className="w-6 h-6 text-orange-400" />
          <h2 className="text-xl font-semibold">RAG Configuration</h2>
          {hasChanges && (
            <span className="text-xs bg-yellow-600 text-white px-2 py-1 rounded">
              Unsaved changes
            </span>
          )}
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={testConfiguration}
            disabled={isTesting}
            className="px-3 py-1 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-700 rounded-lg text-sm"
          >
            {isTesting ? <RefreshCw className="w-4 h-4 animate-spin" /> : <TestTube className="w-4 h-4" />}
            Test
          </button>
          <button
            onClick={exportConfiguration}
            className="px-3 py-1 bg-slate-700 hover:bg-slate-600 rounded-lg text-sm"
          >
            <Download className="w-4 h-4" />
          </button>
          <label className="px-3 py-1 bg-slate-700 hover:bg-slate-600 rounded-lg text-sm cursor-pointer">
            <Upload className="w-4 h-4" />
            <input
              type="file"
              accept=".json"
              onChange={importConfiguration}
              className="hidden"
            />
          </label>
          <button
            onClick={resetConfiguration}
            className="px-3 py-1 bg-slate-700 hover:bg-slate-600 rounded-lg text-sm"
          >
            <RotateCcw className="w-4 h-4" />
          </button>
          <button
            onClick={onClose}
            className="px-3 py-1 bg-slate-600 hover:bg-slate-700 rounded-lg text-sm"
          >
            ✕
          </button>
        </div>
      </div>

      {/* Test Results */}
      {testResults && (
        <div className={`p-4 border-b ${
          testResults.success ? 'bg-green-900/30 border-green-700' : 'bg-red-900/30 border-red-700'
        }`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              {testResults.success ? (
                <CheckCircle className="w-5 h-5 text-green-400" />
              ) : (
                <XCircle className="w-5 h-5 text-red-400" />
              )}
              <span className={testResults.success ? 'text-green-300' : 'text-red-300'}>
                {testResults.success ? 'Configuration test successful' : 'Configuration test failed'}
              </span>
            </div>
            <button
              onClick={() => setTestResults(null)}
              className="text-slate-400 hover:text-white"
            >
              ✕
            </button>
          </div>
          {testResults.errors && testResults.errors.length > 0 && (
            <div className="mt-2 text-sm text-red-300">
              <ul className="list-disc list-inside">
                {testResults.errors.map((error, index) => (
                  <li key={index}>{error}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar */}
        <div className="w-64 bg-slate-800 border-r border-slate-700 overflow-y-auto">
          <div className="p-2 space-y-1">
            {sections.map(section => {
              const Icon = section.icon;
              return (
                <button
                  key={section.id}
                  onClick={() => setActiveSection(section.id)}
                  className={`w-full text-left p-3 rounded-lg flex items-center space-x-3 transition-colors ${
                    activeSection === section.id
                      ? 'bg-blue-600 text-white'
                      : 'text-slate-300 hover:bg-slate-700'
                  }`}
                >
                  <Icon className="w-4 h-4 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <div className="font-medium text-sm">{section.label}</div>
                    <div className="text-xs opacity-75 truncate">{section.description}</div>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Content Area */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Section Header */}
          <div className="p-4 border-b border-slate-700 bg-slate-800">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-white text-lg font-semibold">
                  {sections.find(s => s.id === activeSection)?.label} Configuration
                </h3>
                <p className="text-slate-400 text-sm">
                  {sections.find(s => s.id === activeSection)?.description}
                </p>
              </div>
            </div>
          </div>

          {/* Scrollable Content */}
          <div className="flex-1 overflow-y-auto p-6">
            {activeSection === CONFIG_CATEGORIES.EMBEDDING && renderEmbeddingConfig()}
            {activeSection === CONFIG_CATEGORIES.SEARCH && renderSearchConfig()}
            {activeSection === CONFIG_CATEGORIES.PERFORMANCE && renderPerformanceConfig()}
            {activeSection === CONFIG_CATEGORIES.SECURITY && renderSecurityConfig()}
            {activeSection === CONFIG_CATEGORIES.INTEGRATION && renderIntegrationConfig()}
            {activeSection === CONFIG_CATEGORIES.ADVANCED && renderAdvancedConfig()}
          </div>

          {/* Footer */}
          <div className="p-4 border-t border-slate-700 bg-slate-800">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2 text-sm text-slate-400">
                <HelpCircle className="w-4 h-4" />
                <span>Changes may require restart to take effect</span>
              </div>
              <div className="flex space-x-3">
                <button
                  onClick={resetConfiguration}
                  className="px-4 py-2 text-slate-300 hover:text-white transition-colors"
                >
                  Reset to Defaults
                </button>
                <button
                  onClick={onClose}
                  className="px-4 py-2 text-slate-300 hover:text-white transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={saveConfiguration}
                  disabled={!hasChanges}
                  className={`px-4 py-2 rounded-lg flex items-center space-x-2 transition-colors ${
                    hasChanges
                      ? 'bg-blue-600 hover:bg-blue-700 text-white'
                      : 'bg-slate-600 text-slate-400 cursor-not-allowed'
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

      {/* Reset Confirmation Dialog */}
      {showResetConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-slate-800 rounded-lg p-6 max-w-md w-full mx-4">
            <div className="flex items-center space-x-3 mb-4">
              <AlertCircle className="w-6 h-6 text-yellow-400" />
              <h3 className="text-lg font-semibold">Reset Configuration</h3>
            </div>
            <p className="text-slate-300 mb-6">
              Are you sure you want to reset all settings to defaults? This action cannot be undone.
            </p>
            <div className="flex justify-end space-x-3">
              <button
                onClick={handleResetCancel}
                className="px-4 py-2 bg-slate-600 hover:bg-slate-700 rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleResetConfirm}
                className="px-4 py-2 bg-red-600 hover:bg-red-700 rounded-lg transition-colors"
              >
                Reset
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default RAGConfig;