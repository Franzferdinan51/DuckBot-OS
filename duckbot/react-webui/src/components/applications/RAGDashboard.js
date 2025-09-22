import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Search, Database, FileText, Upload, Download, Settings, BarChart3,
  Activity, TrendingUp, Users, Clock, Zap, AlertCircle, CheckCircle,
  XCircle, RefreshCw, Filter, Eye, Edit, Trash2, Plus, ExternalLink
} from 'lucide-react';
import { LineChart, Line, AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

// RAG System Status Types
const RAG_STATUS = {
  READY: 'ready',
  INDEXING: 'indexing',
  SEARCHING: 'searching',
  ERROR: 'error',
  MAINTENANCE: 'maintenance',
  UPDATING: 'updating'
};

// Document Types
const DOCUMENT_TYPES = {
  PDF: 'pdf',
  TXT: 'txt',
  DOCX: 'docx',
  MD: 'md',
  HTML: 'html',
  JSON: 'json',
  CSV: 'csv'
};

// Embedding Providers
const EMBEDDING_PROVIDERS = {
  OPENAI: 'openai',
  LOCAL: 'local',
  HUGGINGFACE: 'huggingface',
  COHERE: 'cohere'
};

const RAGDashboard = ({ onClose }) => {
  // RAG System State
  const [ragStatus, setRagStatus] = useState(RAG_STATUS.READY);
  const [systemMetrics, setSystemMetrics] = useState({
    totalDocuments: 0,
    indexedDocuments: 0,
    totalChunks: 0,
    averageChunkSize: 0,
    indexSize: 0,
    lastIndexTime: null,
    searchCount: 0,
    averageSearchTime: 0,
    cacheHitRate: 0
  });

  // Search Analytics
  const [searchAnalytics, setSearchAnalytics] = useState({
    totalSearches: 0,
    averageResponseTime: 0,
    topQueries: [],
    searchTrends: [],
    userSatisfaction: 0
  });

  // Document Management
  const [documents, setDocuments] = useState([]);
  const [indexes, setIndexes] = useState([]);
  const [activeProcesses, setActiveProcesses] = useState([]);

  // Configuration
  const [config, setConfig] = useState({
    embedding: {
      provider: EMBEDDING_PROVIDERS.LOCAL,
      model: 'all-MiniLM-L6-v2',
      chunkSize: 512,
      chunkOverlap: 50,
      batchSize: 32
    },
    search: {
      topK: 5,
      scoreThreshold: 0.7,
      useHybridSearch: true,
      enableReranking: true,
      maxResults: 10
    },
    performance: {
      enableCaching: true,
      cacheSize: 1000,
      cacheTTL: 3600,
      enableParallel: true,
      maxParallel: 4
    }
  });

  // UI State
  const [selectedTab, setSelectedTab] = useState('overview');
  const [timeRange, setTimeRange] = useState('24h');
  const [searchQuery, setSearchQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  // Chart data
  const [performanceData, setPerformanceData] = useState([]);
  const [searchVolumeData, setSearchVolumeData] = useState([]);

  // Initialize dashboard
  useEffect(() => {
    initializeDashboard();
    startMonitoring();
  }, []);

  const initializeDashboard = useCallback(async () => {
    setIsLoading(true);
    try {
      // Load system metrics
      await loadSystemMetrics();

      // Load documents
      await loadDocuments();

      // Load indexes
      await loadIndexes();

      // Load analytics
      await loadAnalytics();

      // Load configuration
      await loadConfiguration();
    } catch (error) {
      console.error('Failed to initialize RAG dashboard:', error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const startMonitoring = useCallback(() => {
    // Update metrics every 5 seconds
    const metricsInterval = setInterval(async () => {
      await loadSystemMetrics();
      updatePerformanceData();
    }, 5000);

    // Update search analytics every 30 seconds
    const analyticsInterval = setInterval(async () => {
      await loadAnalytics();
    }, 30000);

    return () => {
      clearInterval(metricsInterval);
      clearInterval(analyticsInterval);
    };
  }, []);

  const loadSystemMetrics = async () => {
    try {
      const response = await fetch('http://localhost:8787/api/rag/metrics');
      if (response.ok) {
        const metrics = await response.json();
        setSystemMetrics(metrics);
      }
    } catch (error) {
      console.error('Failed to load system metrics:', error);
    }
  };

  const loadDocuments = async () => {
    try {
      const response = await fetch('http://localhost:8787/api/rag/documents');
      if (response.ok) {
        const docs = await response.json();
        setDocuments(docs);
      }
    } catch (error) {
      console.error('Failed to load documents:', error);
    }
  };

  const loadIndexes = async () => {
    try {
      const response = await fetch('http://localhost:8787/api/rag/indexes');
      if (response.ok) {
        const idxs = await response.json();
        setIndexes(idxs);
      }
    } catch (error) {
      console.error('Failed to load indexes:', error);
    }
  };

  const loadAnalytics = async () => {
    try {
      const response = await fetch('http://localhost:8787/api/rag/analytics');
      if (response.ok) {
        const analytics = await response.json();
        setSearchAnalytics(analytics);
      }
    } catch (error) {
      console.error('Failed to load analytics:', error);
    }
  };

  const loadConfiguration = async () => {
    try {
      const response = await fetch('http://localhost:8787/api/rag/config');
      if (response.ok) {
        const conf = await response.json();
        setConfig(conf);
      }
    } catch (error) {
      console.error('Failed to load configuration:', error);
    }
  };

  const updatePerformanceData = () => {
    const timestamp = new Date().toLocaleTimeString();
    const newDataPoint = {
      time: timestamp,
      responseTime: Math.random() * 100 + 20,
      throughput: Math.floor(Math.random() * 50) + 10,
      memory: Math.random() * 60 + 20,
      cpu: Math.random() * 40 + 10
    };

    setPerformanceData(prev => {
      const updated = [...prev, newDataPoint];
      return updated.slice(-20);
    });
  };

  const startIndexing = async (documentIds) => {
    setRagStatus(RAG_STATUS.INDEXING);

    const process = {
      id: Date.now().toString(),
      type: 'indexing',
      status: 'running',
      progress: 0,
      documents: documentIds,
      startTime: new Date()
    };

    setActiveProcesses(prev => [...prev, process]);

    try {
      const response = await fetch('http://localhost:8787/api/rag/index', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ documentIds })
      });

      if (response.ok) {
        // Simulate progress updates
        for (let i = 0; i <= 100; i += 10) {
          await new Promise(resolve => setTimeout(resolve, 200));
          setActiveProcesses(prev => prev.map(p =>
            p.id === process.id ? { ...p, progress: i } : p
          ));
        }

        setActiveProcesses(prev => prev.filter(p => p.id !== process.id));
        setRagStatus(RAG_STATUS.READY);
        await loadSystemMetrics();
      }
    } catch (error) {
      console.error('Indexing failed:', error);
      setActiveProcesses(prev => prev.filter(p => p.id !== process.id));
      setRagStatus(RAG_STATUS.ERROR);
    }
  };

  const optimizeIndex = async (indexId) => {
    try {
      const response = await fetch(`http://localhost:8787/api/rag/indexes/${indexId}/optimize`, {
        method: 'POST'
      });

      if (response.ok) {
        await loadIndexes();
        await loadSystemMetrics();
      }
    } catch (error) {
      console.error('Index optimization failed:', error);
    }
  };

  const clearCache = async () => {
    try {
      const response = await fetch('http://localhost:8787/api/rag/cache/clear', {
        method: 'POST'
      });

      if (response.ok) {
        await loadSystemMetrics();
      }
    } catch (error) {
      console.error('Cache clear failed:', error);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case RAG_STATUS.READY: return 'text-green-400';
      case RAG_STATUS.INDEXING: return 'text-blue-400';
      case RAG_STATUS.SEARCHING: return 'text-purple-400';
      case RAG_STATUS.ERROR: return 'text-red-400';
      case RAG_STATUS.MAINTENANCE: return 'text-yellow-400';
      case RAG_STATUS.UPDATING: return 'text-orange-400';
      default: return 'text-gray-400';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case RAG_STATUS.READY: return <CheckCircle className="w-4 h-4" />;
      case RAG_STATUS.INDEXING: return <RefreshCw className="w-4 h-4 animate-spin" />;
      case RAG_STATUS.SEARCHING: return <Search className="w-4 h-4" />;
      case RAG_STATUS.ERROR: return <XCircle className="w-4 h-4" />;
      case RAG_STATUS.MAINTENANCE: return <AlertCircle className="w-4 h-4" />;
      case RAG_STATUS.UPDATING: return <TrendingUp className="w-4 h-4" />;
      default: return <Activity className="w-4 h-4" />;
    }
  };

  const formatBytes = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatTime = (seconds) => {
    if (seconds < 60) return `${seconds.toFixed(1)}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds.toFixed(0)}s`;
  };

  // Chart colors
  const chartColors = {
    responseTime: '#8884d8',
    throughput: '#82ca9d',
    memory: '#ffc658',
    cpu: '#ff7300'
  };

  const renderOverviewTab = () => (
    <div className="space-y-6">
      {/* Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-slate-800 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-medium text-slate-400">System Status</h3>
            <div className={getStatusColor(ragStatus)}>
              {getStatusIcon(ragStatus)}
            </div>
          </div>
          <div className="text-2xl font-bold text-white capitalize">{ragStatus}</div>
        </div>

        <div className="bg-slate-800 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-medium text-slate-400">Documents</h3>
            <FileText className="w-4 h-4 text-blue-400" />
          </div>
          <div className="text-2xl font-bold text-white">{systemMetrics.totalDocuments}</div>
          <div className="text-xs text-slate-400">{systemMetrics.indexedDocuments} indexed</div>
        </div>

        <div className="bg-slate-800 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-medium text-slate-400">Search Performance</h3>
            <Zap className="w-4 h-4 text-yellow-400" />
          </div>
          <div className="text-2xl font-bold text-white">{formatTime(systemMetrics.averageSearchTime)}</div>
          <div className="text-xs text-slate-400">{systemMetrics.searchCount} searches</div>
        </div>

        <div className="bg-slate-800 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-medium text-slate-400">Index Size</h3>
            <Database className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-2xl font-bold text-white">{formatBytes(systemMetrics.indexSize)}</div>
          <div className="text-xs text-slate-400">{systemMetrics.totalChunks} chunks</div>
        </div>
      </div>

      {/* Performance Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-slate-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Response Time Trend</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={performanceData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#475569" />
                <XAxis dataKey="time" stroke="#94a3b8" />
                <YAxis stroke="#94a3b8" />
                <Tooltip
                  contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569' }}
                  labelStyle={{ color: '#f1f5f9' }}
                />
                <Line type="monotone" dataKey="responseTime" stroke={chartColors.responseTime} strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-slate-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4">System Resource Usage</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={performanceData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#475569" />
                <XAxis dataKey="time" stroke="#94a3b8" />
                <YAxis stroke="#94a3b8" />
                <Tooltip
                  contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569' }}
                  labelStyle={{ color: '#f1f5f9' }}
                />
                <Area type="monotone" dataKey="memory" stackId="1" stroke={chartColors.memory} fill={chartColors.memory} fillOpacity={0.6} />
                <Area type="monotone" dataKey="cpu" stackId="1" stroke={chartColors.cpu} fill={chartColors.cpu} fillOpacity={0.6} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Active Processes */}
      {activeProcesses.length > 0 && (
        <div className="bg-slate-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Active Processes</h3>
          <div className="space-y-3">
            {activeProcesses.map(process => (
              <div key={process.id} className="bg-slate-700 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <div>
                    <h4 className="font-medium text-white capitalize">{process.type}</h4>
                    <p className="text-sm text-slate-400">
                      Started at {new Date(process.startTime).toLocaleTimeString()}
                    </p>
                  </div>
                  <div className="flex items-center space-x-2">
                    <div className="text-sm text-white">{process.progress}%</div>
                    <RefreshCw className="w-4 h-4 text-blue-400 animate-spin" />
                  </div>
                </div>
                <div className="w-full bg-slate-600 rounded-full h-2">
                  <div
                    className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${process.progress}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );

  const renderDocumentsTab = () => (
    <div className="space-y-6">
      {/* Document Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-slate-800 rounded-lg p-4">
          <h3 className="text-sm font-medium text-slate-400 mb-1">Total Documents</h3>
          <div className="text-2xl font-bold text-white">{documents.length}</div>
        </div>
        <div className="bg-slate-800 rounded-lg p-4">
          <h3 className="text-sm font-medium text-slate-400 mb-1">Indexed Documents</h3>
          <div className="text-2xl font-bold text-white">{systemMetrics.indexedDocuments}</div>
        </div>
        <div className="bg-slate-800 rounded-lg p-4">
          <h3 className="text-sm font-medium text-slate-400 mb-1">Average Chunks</h3>
          <div className="text-2xl font-bold text-white">{systemMetrics.averageChunkSize}</div>
        </div>
      </div>

      {/* Document List */}
      <div className="bg-slate-800 rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-white">Documents</h3>
          <button className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm">
            <Plus className="w-4 h-4 mr-2 inline" />
            Upload Document
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-700">
                <th className="text-left py-2 px-4 text-slate-400">Name</th>
                <th className="text-left py-2 px-4 text-slate-400">Type</th>
                <th className="text-left py-2 px-4 text-slate-400">Size</th>
                <th className="text-left py-2 px-4 text-slate-400">Status</th>
                <th className="text-left py-2 px-4 text-slate-400">Chunks</th>
                <th className="text-left py-2 px-4 text-slate-400">Last Updated</th>
                <th className="text-left py-2 px-4 text-slate-400">Actions</th>
              </tr>
            </thead>
            <tbody>
              {documents.slice(0, 10).map(doc => (
                <tr key={doc.id} className="border-b border-slate-700 hover:bg-slate-700/50">
                  <td className="py-2 px-4 text-white">{doc.name}</td>
                  <td className="py-2 px-4 text-slate-400">{doc.type}</td>
                  <td className="py-2 px-4 text-slate-400">{formatBytes(doc.size)}</td>
                  <td className="py-2 px-4">
                    <span className={`px-2 py-1 rounded text-xs ${
                      doc.indexed ? 'bg-green-600 text-white' : 'bg-yellow-600 text-white'
                    }`}>
                      {doc.indexed ? 'Indexed' : 'Pending'}
                    </span>
                  </td>
                  <td className="py-2 px-4 text-white">{doc.chunks || 0}</td>
                  <td className="py-2 px-4 text-slate-400">
                    {new Date(doc.lastUpdated).toLocaleDateString()}
                  </td>
                  <td className="py-2 px-4">
                    <div className="flex space-x-2">
                      <button className="text-blue-400 hover:text-blue-300">
                        <Eye className="w-4 h-4" />
                      </button>
                      <button className="text-green-400 hover:text-green-300">
                        <RefreshCw className="w-4 h-4" />
                      </button>
                      <button className="text-red-400 hover:text-red-300">
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );

  const renderIndexesTab = () => (
    <div className="space-y-6">
      {/* Index Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-slate-800 rounded-lg p-4">
          <h3 className="text-sm font-medium text-slate-400 mb-1">Total Indexes</h3>
          <div className="text-2xl font-bold text-white">{indexes.length}</div>
        </div>
        <div className="bg-slate-800 rounded-lg p-4">
          <h3 className="text-sm font-medium text-slate-400 mb-1">Index Size</h3>
          <div className="text-2xl font-bold text-white">{formatBytes(systemMetrics.indexSize)}</div>
        </div>
        <div className="bg-slate-800 rounded-lg p-4">
          <h3 className="text-sm font-medium text-slate-400 mb-1">Total Chunks</h3>
          <div className="text-2xl font-bold text-white">{systemMetrics.totalChunks}</div>
        </div>
        <div className="bg-slate-800 rounded-lg p-4">
          <h3 className="text-sm font-medium text-slate-400 mb-1">Cache Hit Rate</h3>
          <div className="text-2xl font-bold text-white">{(systemMetrics.cacheHitRate * 100).toFixed(1)}%</div>
        </div>
      </div>

      {/* Index List */}
      <div className="bg-slate-800 rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-white">Indexes</h3>
          <div className="flex space-x-2">
            <button
              onClick={clearCache}
              className="px-4 py-2 bg-orange-600 hover:bg-orange-700 text-white rounded-lg text-sm"
            >
              Clear Cache
            </button>
            <button className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg text-sm">
              <Plus className="w-4 h-4 mr-2 inline" />
              Create Index
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {indexes.map(index => (
            <div key={index.id} className="bg-slate-700 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <h4 className="font-medium text-white">{index.name}</h4>
                <div className={`px-2 py-1 rounded text-xs ${
                  index.status === 'active' ? 'bg-green-600' : 'bg-yellow-600'
                } text-white`}>
                  {index.status}
                </div>
              </div>

              <div className="space-y-1 text-xs text-slate-400">
                <div>Documents: {index.documentCount}</div>
                <div>Chunks: {index.chunkCount}</div>
                <div>Size: {formatBytes(index.size)}</div>
                <div>Created: {new Date(index.createdAt).toLocaleDateString()}</div>
              </div>

              <div className="mt-3 flex space-x-2">
                <button
                  onClick={() => optimizeIndex(index.id)}
                  className="flex-1 px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded text-xs"
                >
                  Optimize
                </button>
                <button className="flex-1 px-3 py-1 bg-slate-600 hover:bg-slate-700 text-white rounded text-xs">
                  Settings
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  const renderAnalyticsTab = () => (
    <div className="space-y-6">
      {/* Search Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-slate-800 rounded-lg p-4">
          <h3 className="text-sm font-medium text-slate-400 mb-1">Total Searches</h3>
          <div className="text-2xl font-bold text-white">{searchAnalytics.totalSearches}</div>
        </div>
        <div className="bg-slate-800 rounded-lg p-4">
          <h3 className="text-sm font-medium text-slate-400 mb-1">Avg Response Time</h3>
          <div className="text-2xl font-bold text-white">{formatTime(searchAnalytics.averageResponseTime)}</div>
        </div>
        <div className="bg-slate-800 rounded-lg p-4">
          <h3 className="text-sm font-medium text-slate-400 mb-1">User Satisfaction</h3>
          <div className="text-2xl font-bold text-white">{(searchAnalytics.userSatisfaction * 100).toFixed(1)}%</div>
        </div>
        <div className="bg-slate-800 rounded-lg p-4">
          <h3 className="text-sm font-medium text-slate-400 mb-1">Success Rate</h3>
          <div className="text-2xl font-bold text-white">94.2%</div>
        </div>
      </div>

      {/* Top Queries */}
      <div className="bg-slate-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Top Search Queries</h3>
        <div className="space-y-2">
          {searchAnalytics.topQueries?.map((query, index) => (
            <div key={index} className="flex items-center justify-between p-3 bg-slate-700 rounded-lg">
              <div className="flex items-center space-x-3">
                <div className="text-sm text-white bg-slate-600 rounded px-2 py-1">
                  #{index + 1}
                </div>
                <div className="text-white">{query.query}</div>
              </div>
              <div className="flex items-center space-x-4 text-sm text-slate-400">
                <span>{query.count} searches</span>
                <span>{(query.satisfaction * 100).toFixed(1)}% satisfaction</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  const renderSettingsTab = () => (
    <div className="space-y-6">
      {/* Embedding Settings */}
      <div className="bg-slate-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Embedding Configuration</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm text-slate-400 mb-2">Provider</label>
            <select
              value={config.embedding.provider}
              onChange={(e) => setConfig(prev => ({
                ...prev,
                embedding: { ...prev.embedding, provider: e.target.value }
              }))}
              className="w-full bg-slate-700 text-white rounded px-3 py-2 border border-slate-600"
            >
              {Object.entries(EMBEDDING_PROVIDERS).map(([key, value]) => (
                <option key={value} value={value}>{key}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm text-slate-400 mb-2">Model</label>
            <input
              type="text"
              value={config.embedding.model}
              onChange={(e) => setConfig(prev => ({
                ...prev,
                embedding: { ...prev.embedding, model: e.target.value }
              }))}
              className="w-full bg-slate-700 text-white rounded px-3 py-2 border border-slate-600"
            />
          </div>
          <div>
            <label className="block text-sm text-slate-400 mb-2">Chunk Size</label>
            <input
              type="number"
              value={config.embedding.chunkSize}
              onChange={(e) => setConfig(prev => ({
                ...prev,
                embedding: { ...prev.embedding, chunkSize: parseInt(e.target.value) }
              }))}
              className="w-full bg-slate-700 text-white rounded px-3 py-2 border border-slate-600"
            />
          </div>
          <div>
            <label className="block text-sm text-slate-400 mb-2">Chunk Overlap</label>
            <input
              type="number"
              value={config.embedding.chunkOverlap}
              onChange={(e) => setConfig(prev => ({
                ...prev,
                embedding: { ...prev.embedding, chunkOverlap: parseInt(e.target.value) }
              }))}
              className="w-full bg-slate-700 text-white rounded px-3 py-2 border border-slate-600"
            />
          </div>
        </div>
      </div>

      {/* Search Settings */}
      <div className="bg-slate-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Search Configuration</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm text-slate-400 mb-2">Top K Results</label>
            <input
              type="number"
              value={config.search.topK}
              onChange={(e) => setConfig(prev => ({
                ...prev,
                search: { ...prev.search, topK: parseInt(e.target.value) }
              }))}
              className="w-full bg-slate-700 text-white rounded px-3 py-2 border border-slate-600"
            />
          </div>
          <div>
            <label className="block text-sm text-slate-400 mb-2">Score Threshold</label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              value={config.search.scoreThreshold}
              onChange={(e) => setConfig(prev => ({
                ...prev,
                search: { ...prev.search, scoreThreshold: parseFloat(e.target.value) }
              }))}
              className="w-full"
            />
            <div className="text-xs text-slate-400">{config.search.scoreThreshold}</div>
          </div>
        </div>
        <div className="mt-4 space-y-3">
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={config.search.useHybridSearch}
              onChange={(e) => setConfig(prev => ({
                ...prev,
                search: { ...prev.search, useHybridSearch: e.target.checked }
              }))}
              className="rounded text-blue-600"
            />
            <span className="text-sm text-slate-300">Enable Hybrid Search</span>
          </label>
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={config.search.enableReranking}
              onChange={(e) => setConfig(prev => ({
                ...prev,
                search: { ...prev.search, enableReranking: e.target.checked }
              }))}
              className="rounded text-blue-600"
            />
            <span className="text-sm text-slate-300">Enable Reranking</span>
          </label>
        </div>
      </div>

      {/* Performance Settings */}
      <div className="bg-slate-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Performance Settings</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm text-slate-400 mb-2">Cache Size</label>
            <input
              type="number"
              value={config.performance.cacheSize}
              onChange={(e) => setConfig(prev => ({
                ...prev,
                performance: { ...prev.performance, cacheSize: parseInt(e.target.value) }
              }))}
              className="w-full bg-slate-700 text-white rounded px-3 py-2 border border-slate-600"
            />
          </div>
          <div>
            <label className="block text-sm text-slate-400 mb-2">Max Parallel</label>
            <input
              type="number"
              value={config.performance.maxParallel}
              onChange={(e) => setConfig(prev => ({
                ...prev,
                performance: { ...prev.performance, maxParallel: parseInt(e.target.value) }
              }))}
              className="w-full bg-slate-700 text-white rounded px-3 py-2 border border-slate-600"
            />
          </div>
        </div>
        <div className="mt-4 space-y-3">
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={config.performance.enableCaching}
              onChange={(e) => setConfig(prev => ({
                ...prev,
                performance: { ...prev.performance, enableCaching: e.target.checked }
              }))}
              className="rounded text-blue-600"
            />
            <span className="text-sm text-slate-300">Enable Caching</span>
          </label>
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={config.performance.enableParallel}
              onChange={(e) => setConfig(prev => ({
                ...prev,
                performance: { ...prev.performance, enableParallel: e.target.checked }
              }))}
              className="rounded text-blue-600"
            />
            <span className="text-sm text-slate-300">Enable Parallel Processing</span>
          </label>
        </div>
      </div>
    </div>
  );

  return (
    <div className="h-full flex flex-col bg-slate-900 text-white">
      {/* Header */}
      <div className="flex items-center justify-between p-4 bg-slate-800 border-b border-slate-700">
        <div className="flex items-center space-x-2">
          <Database className="w-6 h-6 text-purple-400" />
          <h2 className="text-xl font-semibold">RAG Dashboard</h2>
          <div className={`px-2 py-1 rounded text-xs ${getStatusColor(ragStatus)} bg-slate-700`}>
            {ragStatus.toUpperCase()}
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            className="px-3 py-1 bg-slate-700 text-white rounded text-sm border border-slate-600"
          >
            <option value="1h">Last Hour</option>
            <option value="24h">Last 24 Hours</option>
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
          </select>
          <button
            onClick={initializeDashboard}
            disabled={isLoading}
            className="p-2 bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
          <button
            onClick={onClose}
            className="px-3 py-1 bg-slate-600 hover:bg-slate-700 rounded-lg text-sm"
          >
            ✕
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar */}
        <div className="w-64 bg-slate-800 border-r border-slate-700">
          <div className="p-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-400" />
              <input
                type="text"
                placeholder="Search..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-3 py-2 bg-slate-700 text-white rounded-lg text-sm border border-slate-600"
              />
            </div>
          </div>

          <nav className="px-2 pb-4">
            {[
              { id: 'overview', label: 'Overview', icon: BarChart3 },
              { id: 'documents', label: 'Documents', icon: FileText },
              { id: 'indexes', label: 'Indexes', icon: Database },
              { id: 'analytics', label: 'Analytics', icon: TrendingUp },
              { id: 'settings', label: 'Settings', icon: Settings }
            ].map(item => {
              const Icon = item.icon;
              return (
                <button
                  key={item.id}
                  onClick={() => setSelectedTab(item.id)}
                  className={`w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-sm transition-colors ${
                    selectedTab === item.id
                      ? 'bg-blue-600 text-white'
                      : 'text-slate-300 hover:bg-slate-700'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </nav>
        </div>

        {/* Content Area */}
        <div className="flex-1 overflow-y-auto p-6">
          {isLoading ? (
            <div className="flex items-center justify-center h-64">
              <RefreshCw className="w-8 h-8 text-blue-400 animate-spin" />
              <span className="ml-3 text-slate-400">Loading RAG Dashboard...</span>
            </div>
          ) : (
            <AnimatePresence mode="wait">
              <motion.div
                key={selectedTab}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.2 }}
              >
                {selectedTab === 'overview' && renderOverviewTab()}
                {selectedTab === 'documents' && renderDocumentsTab()}
                {selectedTab === 'indexes' && renderIndexesTab()}
                {selectedTab === 'analytics' && renderAnalyticsTab()}
                {selectedTab === 'settings' && renderSettingsTab()}
              </motion.div>
            </AnimatePresence>
          )}
        </div>
      </div>
    </div>
  );
};

export default RAGDashboard;