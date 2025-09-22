import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Code,
  FileText,
  Globe,
  Server,
  Settings,
  Play,
  Pause,
  RotateCcw,
  Trash2,
  Download,
  Eye,
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle,
  BarChart3,
  Activity,
  Zap,
  Database,
  Cpu,
  HardDrive
} from 'lucide-react';
import { useDeepCode } from '../../services/deepcodeService';

// Main DeepCode Dashboard Component
const DeepCodeDashboard = ({ onClose }) => {
  const {
    service,
    status,
    jobs,
    isLoading,
    error,
    wsConnection,
    loadJobs,
    createPaper2CodeJob,
    createText2WebJob,
    createText2BackendJob,
    cancelJob,
    deleteJob,
    getJobOutput,
  } = useDeepCode();

  // Local state
  const [activeTab, setActiveTab] = useState('overview');
  const [selectedJob, setSelectedJob] = useState(null);
  const [showJobOutput, setShowJobOutput] = useState(false);
  const [jobOutput, setJobOutput] = useState(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Initialize
  useEffect(() => {
    loadJobs({ limit: 50 });
  }, []);

  // Refresh data
  const refreshData = useCallback(async () => {
    setIsRefreshing(true);
    try {
      await loadJobs({ limit: 50 });
    } finally {
      setIsRefreshing(false);
    }
  }, [loadJobs]);

  // Handle job output view
  const handleViewOutput = useCallback(async (job) => {
    try {
      const output = await getJobOutput(job.id);
      setJobOutput(output);
      setSelectedJob(job);
      setShowJobOutput(true);
    } catch (error) {
      console.error('Failed to get job output:', error);
    }
  }, [getJobOutput]);

  // Format date
  const formatDate = useCallback((dateString) => {
    return new Date(dateString).toLocaleString();
  }, []);

  // Get status icon
  const getStatusIcon = useCallback((jobStatus) => {
    switch (jobStatus) {
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'failed':
        return <XCircle className="w-4 h-4 text-red-500" />;
      case 'processing':
        return <Activity className="w-4 h-4 text-blue-500 animate-pulse" />;
      default:
        return <Clock className="w-4 h-4 text-yellow-500" />;
    }
  }, []);

  // Get job type icon
  const getJobTypeIcon = useCallback((jobType) => {
    switch (jobType) {
      case 'paper2code':
        return <FileText className="w-5 h-5" />;
      case 'text2web':
        return <Globe className="w-5 h-5" />;
      case 'text2backend':
        return <Server className="w-5 h-5" />;
      default:
        return <Code className="w-5 h-5" />;
    }
  }, []);

  // Stats calculation
  const stats = {
    total: jobs.length,
    pending: jobs.filter(j => j.status === 'pending').length,
    processing: jobs.filter(j => j.status === 'processing').length,
    completed: jobs.filter(j => j.status === 'completed').length,
    failed: jobs.filter(j => j.status === 'failed').length,
  };

  // Quick actions
  const quickActions = [
    {
      id: 'paper2code',
      title: 'Paper to Code',
      description: 'Convert research papers to executable code',
      icon: FileText,
      color: 'from-purple-500 to-pink-500',
      action: () => setActiveTab('paper2code'),
    },
    {
      id: 'text2web',
      title: 'Text to Web',
      description: 'Generate web applications from natural language',
      icon: Globe,
      color: 'from-blue-500 to-cyan-500',
      action: () => setActiveTab('text2web'),
    },
    {
      id: 'text2backend',
      title: 'Text to Backend',
      description: 'Create backend systems from descriptions',
      icon: Server,
      color: 'from-green-500 to-teal-500',
      action: () => setActiveTab('text2backend'),
    },
  ];

  // Render overview tab
  const renderOverview = () => (
    <div className="space-y-6">
      {/* Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Total Jobs</p>
              <p className="text-2xl font-bold text-white">{stats.total}</p>
            </div>
            <BarChart3 className="w-8 h-8 text-blue-500" />
          </div>
        </div>

        <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Processing</p>
              <p className="text-2xl font-bold text-blue-400">{stats.processing}</p>
            </div>
            <Activity className="w-8 h-8 text-blue-500 animate-pulse" />
          </div>
        </div>

        <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Completed</p>
              <p className="text-2xl font-bold text-green-400">{stats.completed}</p>
            </div>
            <CheckCircle className="w-8 h-8 text-green-500" />
          </div>
        </div>

        <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Failed</p>
              <p className="text-2xl font-bold text-red-400">{stats.failed}</p>
            </div>
            <XCircle className="w-8 h-8 text-red-500" />
          </div>
        </div>
      </div>

      {/* System Status */}
      {status && (
        <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
          <h3 className="text-white font-medium mb-4 flex items-center">
            <Cpu className="w-5 h-5 mr-2" />
            System Status
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-gray-400 text-sm">CPU Usage</div>
              <div className="text-white font-medium">{status.system_resources.cpu_usage}%</div>
              <div className="w-full bg-gray-700 rounded-full h-2 mt-1">
                <div
                  className="bg-blue-500 h-2 rounded-full"
                  style={{ width: `${status.system_resources.cpu_usage}%` }}
                />
              </div>
            </div>
            <div className="text-center">
              <div className="text-gray-400 text-sm">Memory Usage</div>
              <div className="text-white font-medium">{status.system_resources.memory_usage}%</div>
              <div className="w-full bg-gray-700 rounded-full h-2 mt-1">
                <div
                  className="bg-green-500 h-2 rounded-full"
                  style={{ width: `${status.system_resources.memory_usage}%` }}
                />
              </div>
            </div>
            <div className="text-center">
              <div className="text-gray-400 text-sm">Disk Usage</div>
              <div className="text-white font-medium">{status.system_resources.disk_usage}%</div>
              <div className="w-full bg-gray-700 rounded-full h-2 mt-1">
                <div
                  className="bg-yellow-500 h-2 rounded-full"
                  style={{ width: `${status.system_resources.disk_usage}%` }}
                />
              </div>
            </div>
            <div className="text-center">
              <div className="text-gray-400 text-sm">Queue Size</div>
              <div className="text-white font-medium">{status.queue_size}</div>
              <div className="text-sm text-gray-400">jobs pending</div>
            </div>
          </div>
        </div>
      )}

      {/* Quick Actions */}
      <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
        <h3 className="text-white font-medium mb-4">Quick Actions</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {quickActions.map((action) => (
            <button
              key={action.id}
              onClick={action.action}
              className="bg-gradient-to-r from-gray-700 to-gray-600 hover:from-gray-600 hover:to-gray-500 rounded-lg p-4 text-left transition-all duration-200 border border-gray-600 hover:border-gray-500"
            >
              <div className={`w-10 h-10 rounded-lg bg-gradient-to-r ${action.color} flex items-center justify-center mb-3`}>
                <action.icon className="w-5 h-5 text-white" />
              </div>
              <h4 className="text-white font-medium mb-1">{action.title}</h4>
              <p className="text-gray-400 text-sm">{action.description}</p>
            </button>
          ))}
        </div>
      </div>

      {/* Recent Jobs */}
      <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-white font-medium flex items-center">
            <Clock className="w-5 h-5 mr-2" />
            Recent Jobs
          </h3>
          <button
            onClick={refreshData}
            disabled={isRefreshing}
            className="p-2 text-gray-400 hover:text-white transition-colors disabled:opacity-50"
          >
            <RotateCcw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
          </button>
        </div>

        <div className="space-y-2">
          {jobs.slice(0, 10).map((job) => (
            <div
              key={job.id}
              className="flex items-center justify-between p-3 bg-gray-700 rounded-lg hover:bg-gray-600 transition-colors"
            >
              <div className="flex items-center space-x-3">
                {getJobTypeIcon(job.type)}
                <div>
                  <div className="text-white font-medium">{job.type}</div>
                  <div className="text-gray-400 text-sm">Created {formatDate(job.created_at)}</div>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                {getStatusIcon(job.status)}
                <button
                  onClick={() => handleViewOutput(job)}
                  className="p-1 text-gray-400 hover:text-white transition-colors"
                  title="View Output"
                >
                  <Eye className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}

          {jobs.length === 0 && (
            <div className="text-center py-8">
              <Code className="w-12 h-12 text-gray-500 mx-auto mb-4" />
              <p className="text-gray-400">No jobs yet. Create your first job to get started!</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );

  // Render jobs tab
  const renderJobs = () => (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-white font-medium">All Jobs</h3>
        <button
          onClick={refreshData}
          disabled={isRefreshing}
          className="p-2 text-gray-400 hover:text-white transition-colors disabled:opacity-50"
        >
          <RotateCcw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
        </button>
      </div>

      <div className="space-y-2">
        {jobs.map((job) => (
          <motion.div
            key={job.id}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-gray-800 rounded-lg p-4 border border-gray-700"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                {getJobTypeIcon(job.type)}
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="text-white font-medium capitalize">{job.type}</span>
                    {getStatusIcon(job.status)}
                  </div>
                  <div className="text-gray-400 text-sm">
                    Created: {formatDate(job.created_at)}
                    {job.updated_at !== job.created_at && (
                      <span className="ml-2">&bull; Updated: {formatDate(job.updated_at)}</span>
                    )}
                  </div>
                </div>
              </div>

              <div className="flex items-center space-x-2">
                {job.status === 'processing' && (
                  <div className="text-blue-400 text-sm">{job.progress}%</div>
                )}
                {job.status === 'completed' && (
                  <button
                    onClick={() => handleViewOutput(job)}
                    className="p-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
                    title="View Output"
                  >
                    <Eye className="w-4 h-4" />
                  </button>
                )}
                {job.status === 'processing' && (
                  <button
                    onClick={() => cancelJob(job.id)}
                    className="p-2 bg-yellow-600 hover:bg-yellow-700 rounded-lg transition-colors"
                    title="Cancel Job"
                  >
                    <Pause className="w-4 h-4" />
                  </button>
                )}
                {(job.status === 'completed' || job.status === 'failed') && (
                  <button
                    onClick={() => deleteJob(job.id)}
                    className="p-2 bg-red-600 hover:bg-red-700 rounded-lg transition-colors"
                    title="Delete Job"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                )}
              </div>
            </div>

            {job.status === 'processing' && (
              <div className="mt-3">
                <div className="w-full bg-gray-700 rounded-full h-2">
                  <div
                    className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${job.progress}%` }}
                  />
                </div>
              </div>
            )}

            {job.error && (
              <div className="mt-3 p-2 bg-red-900/30 border border-red-700 rounded text-red-400 text-sm">
                {job.error}
              </div>
            )}
          </motion.div>
        ))}

        {jobs.length === 0 && (
          <div className="text-center py-8">
            <Code className="w-12 h-12 text-gray-500 mx-auto mb-4" />
            <p className="text-gray-400">No jobs found. Create a new job to get started!</p>
          </div>
        )}
      </div>
    </div>
  );

  return (
    <div className="h-full bg-gray-900 flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-gray-700 bg-gray-800">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Code className="w-6 h-6 text-purple-400" />
            <h2 className="text-white text-xl font-semibold">DeepCode Dashboard</h2>
          </div>
          <div className="flex items-center space-x-2">
            {status && (
              <div className={`flex items-center space-x-2 px-3 py-1 rounded-full text-sm ${
                status.server_available
                  ? 'bg-green-900/30 text-green-400 border border-green-700'
                  : 'bg-red-900/30 text-red-400 border border-red-700'
              }`}>
                <div className={`w-2 h-2 rounded-full ${
                  status.server_available ? 'bg-green-400' : 'bg-red-400'
                }`} />
                {status.server_available ? 'Connected' : 'Disconnected'}
              </div>
            )}
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-white transition-colors"
            >
              <XCircle className="w-6 h-6" />
            </button>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-gray-700 bg-gray-800">
        {[
          { id: 'overview', label: 'Overview', icon: BarChart3 },
          { id: 'jobs', label: 'Jobs', icon: Activity },
          { id: 'paper2code', label: 'Paper2Code', icon: FileText },
          { id: 'text2web', label: 'Text2Web', icon: Globe },
          { id: 'text2backend', label: 'Text2Backend', icon: Server },
          { id: 'settings', label: 'Settings', icon: Settings },
        ].map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center space-x-2 px-4 py-3 border-b-2 transition-colors ${
                activeTab === tab.id
                  ? 'border-purple-500 text-purple-400 bg-purple-500/10'
                  : 'border-transparent text-gray-400 hover:text-white hover:bg-gray-700/50'
              }`}
            >
              <Icon className="w-4 h-4" />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* Content Area */}
      <div className="flex-1 overflow-y-auto p-6">
        {error && (
          <div className="mb-4 p-4 bg-red-900/30 border border-red-700 rounded text-red-400">
            {error}
          </div>
        )}

        {activeTab === 'overview' && renderOverview()}
        {activeTab === 'jobs' && renderJobs()}

        {/* Placeholder tabs for specific components */}
        {['paper2code', 'text2web', 'text2backend'].includes(activeTab) && (
          <div className="text-center py-8">
            <Code className="w-12 h-12 text-gray-500 mx-auto mb-4" />
            <h3 className="text-white text-lg font-medium mb-2">
              {activeTab === 'paper2code' && 'Paper2Code'}
              {activeTab === 'text2web' && 'Text2Web'}
              {activeTab === 'text2backend' && 'Text2Backend'}
            </h3>
            <p className="text-gray-400 mb-4">
              {activeTab === 'paper2code' && 'Convert research papers to executable code'}
              {activeTab === 'text2web' && 'Generate web applications from natural language'}
              {activeTab === 'text2backend' && 'Create backend systems from descriptions'}
            </p>
            <p className="text-gray-500 text-sm">
              Specific {activeTab} component coming soon...
            </p>
          </div>
        )}

        {activeTab === 'settings' && (
          <div className="text-center py-8">
            <Settings className="w-12 h-12 text-gray-500 mx-auto mb-4" />
            <h3 className="text-white text-lg font-medium mb-2">DeepCode Settings</h3>
            <p className="text-gray-400 mb-4">Configure DeepCode server settings and preferences</p>
            <p className="text-gray-500 text-sm">Settings component coming soon...</p>
          </div>
        )}
      </div>

      {/* Job Output Modal */}
      <AnimatePresence>
        {showJobOutput && selectedJob && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-80">
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              className="bg-gray-800 rounded-lg shadow-xl w-full max-w-4xl max-h-[80vh] border border-gray-700"
            >
              <div className="p-4 border-b border-gray-700 flex items-center justify-between">
                <h3 className="text-white font-medium">
                  {selectedJob.type} Output - {selectedJob.id}
                </h3>
                <button
                  onClick={() => setShowJobOutput(false)}
                  className="text-gray-400 hover:text-white transition-colors"
                >
                  <XCircle className="w-5 h-5" />
                </button>
              </div>
              <div className="p-4 overflow-y-auto max-h-[60vh]">
                <pre className="text-gray-300 text-sm bg-gray-900 p-4 rounded overflow-x-auto">
                  {JSON.stringify(jobOutput, null, 2)}
                </pre>
              </div>
              <div className="p-4 border-t border-gray-700 flex justify-end space-x-2">
                <button
                  onClick={() => setShowJobOutput(false)}
                  className="px-4 py-2 bg-gray-600 hover:bg-gray-500 rounded-lg transition-colors"
                >
                  Close
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default DeepCodeDashboard;