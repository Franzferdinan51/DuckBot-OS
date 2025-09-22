import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Upload, Download, Trash2, Edit, Eye, Plus, FolderOpen,
  FileText, Database, Settings, RefreshCw, CheckCircle, XCircle,
  AlertCircle, Clock, Hash, Tag, Calendar, User, BarChart3,
  Activity, Zap, Filter, Search, MoreHorizontal, Archive,
  Folder, File, Image, Video, Music, Code, BookOpen, Globe,
  HardDrive, Cpu, Network, Cloud, Server, Shield
} from 'lucide-react';

// Management Actions
const ACTIONS = {
  UPLOAD: 'upload',
  DELETE: 'delete',
  EDIT: 'edit',
  INDEX: 'index',
  OPTIMIZE: 'optimize',
  BACKUP: 'backup',
  RESTORE: 'restore',
  EXPORT: 'export'
};

// Document Status
const DOCUMENT_STATUS = {
  PENDING: 'pending',
  INDEXING: 'indexing',
  INDEXED: 'indexed',
  ERROR: 'error',
  ARCHIVED: 'archived'
};

// Index Status
const INDEX_STATUS = {
  ACTIVE: 'active',
  BUILDING: 'building',
  OPTIMIZING: 'optimizing',
  ERROR: 'error',
  MAINTENANCE: 'maintenance'
};

// Process Types
const PROCESS_TYPES = {
  INDEXING: 'indexing',
  OPTIMIZATION: 'optimization',
  BACKUP: 'backup',
  MAINTENANCE: 'maintenance'
};

const RAGManagement = ({ onClose }) => {
  // Management State
  const [activeTab, setActiveTab] = useState('documents');
  const [selectedItems, setSelectedItems] = useState(new Set());
  const [bulkAction, setBulkAction] = useState(null);

  // Documents
  const [documents, setDocuments] = useState([]);
  const [documentStats, setDocumentStats] = useState({
    total: 0,
    indexed: 0,
    pending: 0,
    error: 0,
    archived: 0,
    totalSize: 0
  });

  // Indexes
  const [indexes, setIndexes] = useState([]);
  const [indexStats, setIndexStats] = useState({
    total: 0,
    active: 0,
    building: 0,
    totalSize: 0,
    totalChunks: 0
  });

  // Processes
  const [activeProcesses, setActiveProcesses] = useState([]);
  const [processHistory, setProcessHistory] = useState([]);

  // Upload
  const [uploadQueue, setUploadQueue] = useState([]);
  const [isUploading, setIsUploading] = useState(false);

  // UI State
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState({
    status: 'all',
    type: 'all',
    dateRange: 'all',
    source: 'all'
  });
  const [sortBy, setSortBy] = useState('date');
  const [sortOrder, setSortOrder] = useState('desc');
  const [showAdvanced, setShowAdvanced] = useState(false);

  // Performance Monitoring
  const [performanceMetrics, setPerformanceMetrics] = useState({
    indexingSpeed: 0,
    searchLatency: 0,
    throughput: 0,
    errorRate: 0,
    systemLoad: 0
  });

  // Initialize management interface
  useEffect(() => {
    initializeManagement();
    startPerformanceMonitoring();
  }, []);

  const initializeManagement = useCallback(async () => {
    await Promise.all([
      loadDocuments(),
      loadIndexes(),
      loadActiveProcesses(),
      loadProcessHistory(),
      loadPerformanceMetrics()
    ]);
  }, []);

  const startPerformanceMonitoring = useCallback(() => {
    const interval = setInterval(async () => {
      await loadPerformanceMetrics();
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  const loadDocuments = useCallback(async () => {
    try {
      const response = await fetch('http://localhost:8787/api/rag/documents');
      if (response.ok) {
        const data = await response.json();
        setDocuments(data.documents);
        setDocumentStats(data.stats);
      }
    } catch (error) {
      console.error('Failed to load documents:', error);
    }
  }, []);

  const loadIndexes = useCallback(async () => {
    try {
      const response = await fetch('http://localhost:8787/api/rag/indexes');
      if (response.ok) {
        const data = await response.json();
        setIndexes(data.indexes);
        setIndexStats(data.stats);
      }
    } catch (error) {
      console.error('Failed to load indexes:', error);
    }
  }, []);

  const loadActiveProcesses = useCallback(async () => {
    try {
      const response = await fetch('http://localhost:8787/api/rag/processes/active');
      if (response.ok) {
        const processes = await response.json();
        setActiveProcesses(processes);
      }
    } catch (error) {
      console.error('Failed to load active processes:', error);
    }
  }, []);

  const loadProcessHistory = useCallback(async () => {
    try {
      const response = await fetch('http://localhost:8787/api/rag/processes/history');
      if (response.ok) {
        const history = await response.json();
        setProcessHistory(history);
      }
    } catch (error) {
      console.error('Failed to load process history:', error);
    }
  }, []);

  const loadPerformanceMetrics = useCallback(async () => {
    try {
      const response = await fetch('http://localhost:8787/api/rag/performance');
      if (response.ok) {
        const metrics = await response.json();
        setPerformanceMetrics(metrics);
      }
    } catch (error) {
      console.error('Failed to load performance metrics:', error);
    }
  }, []);

  // Document Management Functions
  const handleFileUpload = useCallback(async (files) => {
    const newFiles = Array.from(files).map(file => ({
      id: Date.now() + Math.random(),
      name: file.name,
      size: file.size,
      type: file.type,
      status: DOCUMENT_STATUS.PENDING,
      progress: 0,
      file: file
    }));

    setUploadQueue(prev => [...prev, ...newFiles]);

    if (!isUploading) {
      processUploadQueue();
    }
  }, [isUploading]);

  const processUploadQueue = useCallback(async () => {
    if (uploadQueue.length === 0 || isUploading) return;

    setIsUploading(true);
    const fileToUpload = uploadQueue[0];

    try {
      const formData = new FormData();
      formData.append('file', fileToUpload.file);

      // Simulate upload progress
      for (let progress = 0; progress <= 100; progress += 10) {
        await new Promise(resolve => setTimeout(resolve, 200));
        setUploadQueue(prev => prev.map(f =>
          f.id === fileToUpload.id ? { ...f, progress } : f
        ));
      }

      const response = await fetch('http://localhost:8787/api/rag/documents/upload', {
        method: 'POST',
        body: formData
      });

      if (response.ok) {
        const result = await response.json();
        setDocuments(prev => [result, ...prev]);
        setDocumentStats(prev => ({
          ...prev,
          total: prev.total + 1,
          pending: prev.pending + 1,
          totalSize: prev.totalSize + fileToUpload.size
        }));
      }
    } catch (error) {
      console.error('Upload failed:', error);
    } finally {
      setUploadQueue(prev => prev.slice(1));
      setIsUploading(false);
    }
  }, [uploadQueue, isUploading]);

  const indexDocuments = useCallback(async (documentIds) => {
    const process = {
      id: Date.now().toString(),
      type: PROCESS_TYPES.INDEXING,
      status: 'running',
      progress: 0,
      documents: documentIds,
      startTime: new Date()
    };

    setActiveProcesses(prev => [...prev, process]);

    try {
      const response = await fetch('http://localhost:8787/api/rag/documents/index', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ documentIds })
      });

      if (response.ok) {
        // Simulate progress updates
        for (let i = 0; i <= 100; i += 5) {
          await new Promise(resolve => setTimeout(resolve, 100));
          setActiveProcesses(prev => prev.map(p =>
            p.id === process.id ? { ...p, progress: i } : p
          ));
        }

        setActiveProcesses(prev => prev.filter(p => p.id !== process.id));
        await loadDocuments();
        await loadIndexes();
      }
    } catch (error) {
      console.error('Indexing failed:', error);
      setActiveProcesses(prev => prev.filter(p => p.id !== process.id));
    }
  }, []);

  const deleteDocuments = useCallback(async (documentIds) => {
    try {
      const response = await fetch('http://localhost:8787/api/rag/documents/delete', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ documentIds })
      });

      if (response.ok) {
        setDocuments(prev => prev.filter(doc => !documentIds.includes(doc.id)));
        setSelectedItems(prev => {
          const newSet = new Set(prev);
          documentIds.forEach(id => newSet.delete(id));
          return newSet;
        });
        await loadDocuments();
      }
    } catch (error) {
      console.error('Delete failed:', error);
    }
  }, []);

  const exportDocuments = useCallback(async (documentIds) => {
    try {
      const response = await fetch('http://localhost:8787/api/rag/documents/export', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ documentIds })
      });

      if (response.ok) {
        // Create download link for the exported file
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `rag-documents-export-${new Date().toISOString().split('T')[0]}.zip`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
      }
    } catch (error) {
      console.error('Export failed:', error);
    }
  }, []);

  const archiveDocuments = useCallback(async (documentIds) => {
    try {
      const response = await fetch('http://localhost:8787/api/rag/documents/archive', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ documentIds })
      });

      if (response.ok) {
        // Update documents to show they are archived
        setDocuments(prev => prev.map(doc =>
          documentIds.includes(doc.id)
            ? { ...doc, status: 'archived', archivedAt: new Date().toISOString() }
            : doc
        ));
        setSelectedItems(prev => {
          const newSet = new Set(prev);
          documentIds.forEach(id => newSet.delete(id));
          return newSet;
        });
        await loadDocuments();
      }
    } catch (error) {
      console.error('Archive failed:', error);
    }
  }, []);

  // Index Management Functions
  const createIndex = useCallback(async (config) => {
    try {
      const response = await fetch('http://localhost:8787/api/rag/indexes', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
      });

      if (response.ok) {
        await loadIndexes();
      }
    } catch (error) {
      console.error('Index creation failed:', error);
    }
  }, []);

  const optimizeIndex = useCallback(async (indexId) => {
    const process = {
      id: Date.now().toString(),
      type: PROCESS_TYPES.OPTIMIZATION,
      status: 'running',
      progress: 0,
      indexId,
      startTime: new Date()
    };

    setActiveProcesses(prev => [...prev, process]);

    try {
      const response = await fetch(`http://localhost:8787/api/rag/indexes/${indexId}/optimize`, {
        method: 'POST'
      });

      if (response.ok) {
        for (let i = 0; i <= 100; i += 10) {
          await new Promise(resolve => setTimeout(resolve, 300));
          setActiveProcesses(prev => prev.map(p =>
            p.id === process.id ? { ...p, progress: i } : p
          ));
        }

        setActiveProcesses(prev => prev.filter(p => p.id !== process.id));
        await loadIndexes();
      }
    } catch (error) {
      console.error('Optimization failed:', error);
      setActiveProcesses(prev => prev.filter(p => p.id !== process.id));
    }
  }, []);

  const deleteIndex = useCallback(async (indexId) => {
    try {
      const response = await fetch(`http://localhost:8787/api/rag/indexes/${indexId}`, {
        method: 'DELETE'
      });

      if (response.ok) {
        await loadIndexes();
      }
    } catch (error) {
      console.error('Index deletion failed:', error);
    }
  }, []);

  // Bulk Operations
  const performBulkAction = useCallback(async (action, items) => {
    switch (action) {
      case ACTIONS.INDEX:
        await indexDocuments(items);
        break;
      case ACTIONS.DELETE:
        await deleteDocuments(items);
        break;
      case ACTIONS.EXPORT:
        await exportDocuments(items);
        break;
      case ACTIONS.ARCHIVE:
        await archiveDocuments(items);
        break;
      default:
        console.warn('Unknown bulk action:', action);
    }

    setSelectedItems(new Set());
    setBulkAction(null);
  }, [indexDocuments, deleteDocuments]);

  // Utility Functions
  const getStatusIcon = (status) => {
    switch (status) {
      case DOCUMENT_STATUS.INDEXED:
      case INDEX_STATUS.ACTIVE:
        return <CheckCircle className="w-4 h-4 text-green-400" />;
      case DOCUMENT_STATUS.INDEXING:
      case INDEX_STATUS.BUILDING:
      case INDEX_STATUS.OPTIMIZING:
        return <RefreshCw className="w-4 h-4 text-blue-400 animate-spin" />;
      case DOCUMENT_STATUS.ERROR:
      case INDEX_STATUS.ERROR:
        return <XCircle className="w-4 h-4 text-red-400" />;
      case DOCUMENT_STATUS.PENDING:
        return <Clock className="w-4 h-4 text-yellow-400" />;
      case INDEX_STATUS.MAINTENANCE:
        return <Shield className="w-4 h-4 text-purple-400" />;
      default:
        return <AlertCircle className="w-4 h-4 text-gray-400" />;
    }
  };

  const getFileIcon = (fileType) => {
    if (fileType.startsWith('image/')) return <Image className="w-5 h-5" />;
    if (fileType.startsWith('video/')) return <Video className="w-5 h-5" />;
    if (fileType.startsWith('audio/')) return <Music className="w-5 h-5" />;
    if (fileType.includes('text') || fileType.includes('document')) return <FileText className="w-5 h-5" />;
    if (fileType.includes('code') || fileType.includes('script')) return <Code className="w-5 h-5" />;
    return <File className="w-5 h-5" />;
  };

  const formatBytes = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString();
  };

  // Filter and sort documents
  const filteredDocuments = documents
    .filter(doc => {
      if (filters.status !== 'all' && doc.status !== filters.status) return false;
      if (filters.type !== 'all' && !doc.type.includes(filters.type)) return false;
      if (searchQuery && !doc.name.toLowerCase().includes(searchQuery.toLowerCase())) return false;
      return true;
    })
    .sort((a, b) => {
      const modifier = sortOrder === 'asc' ? 1 : -1;
      switch (sortBy) {
        case 'name':
          return a.name.localeCompare(b.name) * modifier;
        case 'size':
          return (a.size - b.size) * modifier;
        case 'date':
          return (new Date(a.createdAt) - new Date(b.createdAt)) * modifier;
        case 'status':
          return a.status.localeCompare(b.status) * modifier;
        default:
          return 0;
      }
    });

  // Render different tabs
  const renderDocumentsTab = () => (
    <div className="space-y-6">
      {/* Document Stats */}
      <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
        <div className="bg-slate-800 rounded-lg p-4">
          <div className="flex items-center space-x-2 mb-2">
            <FileText className="w-4 h-4 text-blue-400" />
            <span className="text-sm text-slate-400">Total</span>
          </div>
          <div className="text-xl font-bold text-white">{documentStats.total}</div>
        </div>
        <div className="bg-slate-800 rounded-lg p-4">
          <div className="flex items-center space-x-2 mb-2">
            <CheckCircle className="w-4 h-4 text-green-400" />
            <span className="text-sm text-slate-400">Indexed</span>
          </div>
          <div className="text-xl font-bold text-white">{documentStats.indexed}</div>
        </div>
        <div className="bg-slate-800 rounded-lg p-4">
          <div className="flex items-center space-x-2 mb-2">
            <Clock className="w-4 h-4 text-yellow-400" />
            <span className="text-sm text-slate-400">Pending</span>
          </div>
          <div className="text-xl font-bold text-white">{documentStats.pending}</div>
        </div>
        <div className="bg-slate-800 rounded-lg p-4">
          <div className="flex items-center space-x-2 mb-2">
            <XCircle className="w-4 h-4 text-red-400" />
            <span className="text-sm text-slate-400">Errors</span>
          </div>
          <div className="text-xl font-bold text-white">{documentStats.error}</div>
        </div>
        <div className="bg-slate-800 rounded-lg p-4">
          <div className="flex items-center space-x-2 mb-2">
            <Archive className="w-4 h-4 text-purple-400" />
            <span className="text-sm text-slate-400">Archived</span>
          </div>
          <div className="text-xl font-bold text-white">{documentStats.archived}</div>
        </div>
        <div className="bg-slate-800 rounded-lg p-4">
          <div className="flex items-center space-x-2 mb-2">
            <HardDrive className="w-4 h-4 text-orange-400" />
            <span className="text-sm text-slate-400">Size</span>
          </div>
          <div className="text-xl font-bold text-white">{formatBytes(documentStats.totalSize)}</div>
        </div>
      </div>

      {/* Upload Area */}
      <div className="bg-slate-800 rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-white">Upload Documents</h3>
          <label className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg cursor-pointer">
            <Plus className="w-4 h-4 mr-2 inline" />
            Choose Files
            <input
              type="file"
              multiple
              className="hidden"
              onChange={(e) => handleFileUpload(e.target.files)}
            />
          </label>
        </div>

        {/* Upload Queue */}
        {uploadQueue.length > 0 && (
          <div className="space-y-2 mb-4">
            {uploadQueue.map(file => (
              <div key={file.id} className="flex items-center justify-between p-3 bg-slate-700 rounded-lg">
                <div className="flex items-center space-x-3">
                  {getFileIcon(file.type)}
                  <div>
                    <div className="text-white text-sm">{file.name}</div>
                    <div className="text-slate-400 text-xs">{formatBytes(file.size)}</div>
                  </div>
                </div>
                <div className="flex items-center space-x-3">
                  <div className="flex items-center space-x-2">
                    <div className="w-24 bg-slate-600 rounded-full h-2">
                      <div
                        className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${file.progress}%` }}
                      />
                    </div>
                    <span className="text-xs text-slate-400">{file.progress}%</span>
                  </div>
                  {getStatusIcon(file.status)}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Document List */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-400" />
              <input
                type="text"
                placeholder="Search documents..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10 pr-4 py-2 bg-slate-700 text-white rounded-lg border border-slate-600 w-64"
              />
            </div>
            {selectedItems.size > 0 && (
              <div className="flex items-center space-x-2">
                <span className="text-sm text-slate-400">{selectedItems.size} selected</span>
                <select
                  value={bulkAction || ''}
                  onChange={(e) => setBulkAction(e.target.value || null)}
                  className="px-3 py-1 bg-slate-700 text-white rounded text-sm"
                >
                  <option value="">Bulk action...</option>
                  <option value={ACTIONS.INDEX}>Index</option>
                  <option value={ACTIONS.DELETE}>Delete</option>
                  <option value={ACTIONS.EXPORT}>Export</option>
                  <option value={ACTIONS.ARCHIVE}>Archive</option>
                </select>
                {bulkAction && (
                  <button
                    onClick={() => performBulkAction(bulkAction, Array.from(selectedItems))}
                    className="px-3 py-1 bg-green-600 hover:bg-green-700 text-white rounded text-sm"
                  >
                    Execute
                  </button>
                )}
              </div>
            )}
          </div>

          <div className="flex items-center space-x-2">
            <select
              value={filters.status}
              onChange={(e) => setFilters(prev => ({ ...prev, status: e.target.value }))}
              className="px-3 py-1 bg-slate-700 text-white rounded text-sm"
            >
              <option value="all">All Status</option>
              <option value={DOCUMENT_STATUS.PENDING}>Pending</option>
              <option value={DOCUMENT_STATUS.INDEXING}>Indexing</option>
              <option value={DOCUMENT_STATUS.INDEXED}>Indexed</option>
              <option value={DOCUMENT_STATUS.ERROR}>Error</option>
              <option value={DOCUMENT_STATUS.ARCHIVED}>Archived</option>
            </select>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="px-3 py-1 bg-slate-700 text-white rounded text-sm"
            >
              <option value="date">Date</option>
              <option value="name">Name</option>
              <option value="size">Size</option>
              <option value="status">Status</option>
            </select>
            <select
              value={sortOrder}
              onChange={(e) => setSortOrder(e.target.value)}
              className="px-3 py-1 bg-slate-700 text-white rounded text-sm"
            >
              <option value="desc">Descending</option>
              <option value="asc">Ascending</option>
            </select>
          </div>
        </div>

        {/* Document Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-700">
                <th className="text-left py-2 px-4">
                  <input
                    type="checkbox"
                    checked={selectedItems.size === filteredDocuments.length}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedItems(new Set(filteredDocuments.map(d => d.id)));
                      } else {
                        setSelectedItems(new Set());
                      }
                    }}
                    className="rounded"
                  />
                </th>
                <th className="text-left py-2 px-4 text-slate-400">Name</th>
                <th className="text-left py-2 px-4 text-slate-400">Type</th>
                <th className="text-left py-2 px-4 text-slate-400">Size</th>
                <th className="text-left py-2 px-4 text-slate-400">Status</th>
                <th className="text-left py-2 px-4 text-slate-400">Created</th>
                <th className="text-left py-2 px-4 text-slate-400">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredDocuments.map(doc => (
                <tr key={doc.id} className="border-b border-slate-700 hover:bg-slate-700/50">
                  <td className="py-2 px-4">
                    <input
                      type="checkbox"
                      checked={selectedItems.has(doc.id)}
                      onChange={(e) => {
                        const newSet = new Set(selectedItems);
                        if (e.target.checked) {
                          newSet.add(doc.id);
                        } else {
                          newSet.delete(doc.id);
                        }
                        setSelectedItems(newSet);
                      }}
                      className="rounded"
                    />
                  </td>
                  <td className="py-2 px-4">
                    <div className="flex items-center space-x-2">
                      {getFileIcon(doc.type)}
                      <span className="text-white">{doc.name}</span>
                    </div>
                  </td>
                  <td className="py-2 px-4 text-slate-400">{doc.type || 'Unknown'}</td>
                  <td className="py-2 px-4 text-slate-400">{formatBytes(doc.size)}</td>
                  <td className="py-2 px-4">
                    <div className="flex items-center space-x-2">
                      {getStatusIcon(doc.status)}
                      <span className="text-white capitalize">{doc.status}</span>
                    </div>
                  </td>
                  <td className="py-2 px-4 text-slate-400">{formatDate(doc.createdAt)}</td>
                  <td className="py-2 px-4">
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => indexDocuments([doc.id])}
                        disabled={doc.status === DOCUMENT_STATUS.INDEXING}
                        className="text-blue-400 hover:text-blue-300 disabled:text-slate-600"
                      >
                        <Database className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => window.open(doc.url, '_blank')}
                        className="text-green-400 hover:text-green-300"
                      >
                        <Eye className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => deleteDocuments([doc.id])}
                        className="text-red-400 hover:text-red-300"
                      >
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
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <div className="bg-slate-800 rounded-lg p-4">
          <div className="flex items-center space-x-2 mb-2">
            <Database className="w-4 h-4 text-blue-400" />
            <span className="text-sm text-slate-400">Total</span>
          </div>
          <div className="text-xl font-bold text-white">{indexStats.total}</div>
        </div>
        <div className="bg-slate-800 rounded-lg p-4">
          <div className="flex items-center space-x-2 mb-2">
            <CheckCircle className="w-4 h-4 text-green-400" />
            <span className="text-sm text-slate-400">Active</span>
          </div>
          <div className="text-xl font-bold text-white">{indexStats.active}</div>
        </div>
        <div className="bg-slate-800 rounded-lg p-4">
          <div className="flex items-center space-x-2 mb-2">
            <RefreshCw className="w-4 h-4 text-blue-400 animate-spin" />
            <span className="text-sm text-slate-400">Building</span>
          </div>
          <div className="text-xl font-bold text-white">{indexStats.building}</div>
        </div>
        <div className="bg-slate-800 rounded-lg p-4">
          <div className="flex items-center space-x-2 mb-2">
            <HardDrive className="w-4 h-4 text-orange-400" />
            <span className="text-sm text-slate-400">Size</span>
          </div>
          <div className="text-xl font-bold text-white">{formatBytes(indexStats.totalSize)}</div>
        </div>
        <div className="bg-slate-800 rounded-lg p-4">
          <div className="flex items-center space-x-2 mb-2">
            <Hash className="w-4 h-4 text-purple-400" />
            <span className="text-sm text-slate-400">Chunks</span>
          </div>
          <div className="text-xl font-bold text-white">{indexStats.totalChunks.toLocaleString()}</div>
        </div>
      </div>

      {/* Index Management */}
      <div className="bg-slate-800 rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-white">Index Management</h3>
          <button
            onClick={() => createIndex({ name: `Index-${Date.now()}`, type: 'vector' })}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg"
          >
            <Plus className="w-4 h-4 mr-2 inline" />
            Create Index
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {indexes.map(index => (
            <div key={index.id} className="bg-slate-700 rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <h4 className="font-medium text-white">{index.name}</h4>
                <div className="flex items-center space-x-2">
                  {getStatusIcon(index.status)}
                  <span className="text-xs text-slate-400 capitalize">{index.status}</span>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2 text-xs text-slate-400 mb-3">
                <div>
                  <span className="text-slate-500">Documents:</span>
                  <span className="text-white ml-1">{index.documentCount}</span>
                </div>
                <div>
                  <span className="text-slate-500">Chunks:</span>
                  <span className="text-white ml-1">{index.chunkCount}</span>
                </div>
                <div>
                  <span className="text-slate-500">Size:</span>
                  <span className="text-white ml-1">{formatBytes(index.size)}</span>
                </div>
                <div>
                  <span className="text-slate-500">Created:</span>
                  <span className="text-white ml-1">{formatDate(index.createdAt)}</span>
                </div>
              </div>

              <div className="flex space-x-2">
                <button
                  onClick={() => optimizeIndex(index.id)}
                  disabled={index.status === INDEX_STATUS.OPTIMIZING}
                  className="flex-1 px-3 py-1 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-600 text-white rounded text-sm"
                >
                  Optimize
                </button>
                <button className="flex-1 px-3 py-1 bg-slate-600 hover:bg-slate-700 text-white rounded text-sm">
                  Backup
                </button>
                <button
                  onClick={() => deleteIndex(index.id)}
                  className="px-3 py-1 bg-red-600 hover:bg-red-700 text-white rounded text-sm"
                >
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  const renderProcessesTab = () => (
    <div className="space-y-6">
      {/* Active Processes */}
      <div className="bg-slate-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Active Processes</h3>
        <div className="space-y-3">
          {activeProcesses.length === 0 ? (
            <div className="text-center py-8 text-slate-400">
              No active processes
            </div>
          ) : (
            activeProcesses.map(process => (
              <div key={process.id} className="bg-slate-700 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <div>
                    <h4 className="font-medium text-white capitalize">{process.type}</h4>
                    <p className="text-sm text-slate-400">
                      Started at {new Date(process.startTime).toLocaleString()}
                    </p>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="text-sm text-white">{process.progress}%</span>
                    <RefreshCw className="w-4 h-4 text-blue-400 animate-spin" />
                  </div>
                </div>
                <div className="w-full bg-slate-600 rounded-full h-2">
                  <div
                    className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${process.progress}%` }}
                  />
                </div>
                {process.documents && (
                  <div className="mt-2 text-xs text-slate-400">
                    Processing {process.documents.length} documents
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>

      {/* Process History */}
      <div className="bg-slate-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Process History</h3>
        <div className="space-y-2">
          {processHistory.slice(0, 10).map((process, index) => (
            <div key={index} className="flex items-center justify-between p-3 bg-slate-700 rounded-lg">
              <div className="flex items-center space-x-3">
                {getStatusIcon(process.status)}
                <div>
                  <div className="text-white text-sm capitalize">{process.type}</div>
                  <div className="text-xs text-slate-400">
                    {new Date(process.startTime).toLocaleString()}
                  </div>
                </div>
              </div>
              <div className="text-xs text-slate-400">
                Duration: {process.duration || 'N/A'}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  const renderPerformanceTab = () => (
    <div className="space-y-6">
      {/* Performance Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <div className="bg-slate-800 rounded-lg p-4">
          <div className="flex items-center space-x-2 mb-2">
            <Zap className="w-4 h-4 text-yellow-400" />
            <span className="text-sm text-slate-400">Index Speed</span>
          </div>
          <div className="text-xl font-bold text-white">{performanceMetrics.indexingSpeed.toFixed(1)}</div>
          <div className="text-xs text-slate-400">docs/sec</div>
        </div>
        <div className="bg-slate-800 rounded-lg p-4">
          <div className="flex items-center space-x-2 mb-2">
            <Activity className="w-4 h-4 text-blue-400" />
            <span className="text-sm text-slate-400">Search Latency</span>
          </div>
          <div className="text-xl font-bold text-white">{performanceMetrics.searchLatency.toFixed(0)}</div>
          <div className="text-xs text-slate-400">ms</div>
        </div>
        <div className="bg-slate-800 rounded-lg p-4">
          <div className="flex items-center space-x-2 mb-2">
            <BarChart3 className="w-4 h-4 text-green-400" />
            <span className="text-sm text-slate-400">Throughput</span>
          </div>
          <div className="text-xl font-bold text-white">{performanceMetrics.throughput.toFixed(0)}</div>
          <div className="text-xs text-slate-400">req/sec</div>
        </div>
        <div className="bg-slate-800 rounded-lg p-4">
          <div className="flex items-center space-x-2 mb-2">
            <XCircle className="w-4 h-4 text-red-400" />
            <span className="text-sm text-slate-400">Error Rate</span>
          </div>
          <div className="text-xl font-bold text-white">{(performanceMetrics.errorRate * 100).toFixed(2)}%</div>
          <div className="text-xs text-slate-400">of requests</div>
        </div>
        <div className="bg-slate-800 rounded-lg p-4">
          <div className="flex items-center space-x-2 mb-2">
            <Cpu className="w-4 h-4 text-purple-400" />
            <span className="text-sm text-slate-400">System Load</span>
          </div>
          <div className="text-xl font-bold text-white">{performanceMetrics.systemLoad.toFixed(1)}%</div>
          <div className="text-xs text-slate-400">CPU usage</div>
        </div>
      </div>

      {/* System Health */}
      <div className="bg-slate-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">System Health</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h4 className="text-white font-medium mb-3">Resource Usage</h4>
            <div className="space-y-3">
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-slate-400">CPU</span>
                  <span className="text-white">{Math.round(performanceMetrics.systemLoad)}%</span>
                </div>
                <div className="w-full bg-slate-700 rounded-full h-2">
                  <div
                    className="bg-purple-500 h-2 rounded-full"
                    style={{ width: `${performanceMetrics.systemLoad}%` }}
                  />
                </div>
              </div>
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-slate-400">Memory</span>
                  <span className="text-white">65%</span>
                </div>
                <div className="w-full bg-slate-700 rounded-full h-2">
                  <div className="bg-blue-500 h-2 rounded-full" style={{ width: '65%' }} />
                </div>
              </div>
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-slate-400">Disk I/O</span>
                  <span className="text-white">42%</span>
                </div>
                <div className="w-full bg-slate-700 rounded-full h-2">
                  <div className="bg-orange-500 h-2 rounded-full" style={{ width: '42%' }} />
                </div>
              </div>
            </div>
          </div>

          <div>
            <h4 className="text-white font-medium mb-3">Performance Alerts</h4>
            <div className="space-y-2">
              {performanceMetrics.errorRate > 0.05 && (
                <div className="flex items-center space-x-2 p-2 bg-red-900/30 rounded-lg">
                  <XCircle className="w-4 h-4 text-red-400" />
                  <span className="text-sm text-red-300">
                    High error rate detected ({(performanceMetrics.errorRate * 100).toFixed(2)}%)
                  </span>
                </div>
              )}
              {performanceMetrics.searchLatency > 500 && (
                <div className="flex items-center space-x-2 p-2 bg-yellow-900/30 rounded-lg">
                  <AlertCircle className="w-4 h-4 text-yellow-400" />
                  <span className="text-sm text-yellow-300">
                    High search latency ({performanceMetrics.searchLatency.toFixed(0)}ms)
                  </span>
                </div>
              )}
              {performanceMetrics.systemLoad > 80 && (
                <div className="flex items-center space-x-2 p-2 bg-orange-900/30 rounded-lg">
                  <Cpu className="w-4 h-4 text-orange-400" />
                  <span className="text-sm text-orange-300">
                    High system load ({performanceMetrics.systemLoad.toFixed(1)}%)
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="h-full flex flex-col bg-slate-900 text-white">
      {/* Header */}
      <div className="flex items-center justify-between p-4 bg-slate-800 border-b border-slate-700">
        <div className="flex items-center space-x-3">
          <Settings className="w-6 h-6 text-green-400" />
          <h2 className="text-xl font-semibold">RAG Management</h2>
          {activeProcesses.length > 0 && (
            <span className="text-sm text-slate-400">
              {activeProcesses.length} active process{activeProcesses.length !== 1 ? 'es' : ''}
            </span>
          )}
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setShowAdvanced(!showAdvanced)}
            className={`px-3 py-1 rounded text-sm ${
              showAdvanced ? 'bg-blue-600' : 'bg-slate-700 hover:bg-slate-600'
            }`}
          >
            Advanced
          </button>
          <button
            onClick={initializeManagement}
            className="p-2 bg-slate-700 hover:bg-slate-600 rounded-lg"
          >
            <RefreshCw className="w-4 h-4" />
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
          <nav className="p-2">
            {[
              { id: 'documents', label: 'Documents', icon: FileText, count: documentStats.total },
              { id: 'indexes', label: 'Indexes', icon: Database, count: indexStats.total },
              { id: 'processes', label: 'Processes', icon: Activity, count: activeProcesses.length },
              { id: 'performance', label: 'Performance', icon: BarChart3 }
            ].map(item => {
              const Icon = item.icon;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm transition-colors ${
                    activeTab === item.id
                      ? 'bg-blue-600 text-white'
                      : 'text-slate-300 hover:bg-slate-700'
                  }`}
                >
                  <div className="flex items-center space-x-3">
                    <Icon className="w-4 h-4" />
                    <span>{item.label}</span>
                  </div>
                  {item.count !== undefined && (
                    <span className="bg-slate-600 px-2 py-1 rounded text-xs">
                      {item.count}
                    </span>
                  )}
                </button>
              );
            })}
          </nav>
        </div>

        {/* Content Area */}
        <div className="flex-1 overflow-y-auto p-6">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.2 }}
            >
              {activeTab === 'documents' && renderDocumentsTab()}
              {activeTab === 'indexes' && renderIndexesTab()}
              {activeTab === 'processes' && renderProcessesTab()}
              {activeTab === 'performance' && renderPerformanceTab()}
            </motion.div>
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
};

export default RAGManagement;