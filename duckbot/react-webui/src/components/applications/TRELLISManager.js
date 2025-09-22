import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const TRELLISManager = ({ onClose }) => {
  const [trellisStatus, setTrellisStatus] = useState({
    running: false,
    port: 8189,
    version: '1.0.0',
    models: [],
    jobs: [],
    systemResources: {
      gpu: 0,
      memory: 0,
      disk: 0
    }
  });

  const [selectedModel, setSelectedModel] = useState(null);
  const [generationQueue, setGenerationQueue] = useState([]);
  const [generationHistory, setGenerationHistory] = useState([]);
  const [settings, setSettings] = useState({
    autoOptimize: true,
    qualityPreset: 'balanced',
    maxConcurrentJobs: 2,
    outputFormat: 'glb',
    enableTexturing: true,
    textureResolution: '1024'
  });

  const [newJob, setNewJob] = useState({
    type: 'text_to_3d',
    prompt: '',
    model: 'trellis',
    quality: 'medium',
    iterations: 25
  });

  // Initialize TRELLIS connection
  useEffect(() => {
    checkTrellisStatus();
    const interval = setInterval(checkTrellisStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  const checkTrellisStatus = async () => {
    try {
      const response = await fetch('http://localhost:8189/status');
      if (response.ok) {
        const status = await response.json();
        setTrellisStatus(status);
      } else {
        setTrellisStatus(prev => ({ ...prev, running: false }));
      }
    } catch (error) {
      setTrellisStatus(prev => ({ ...prev, running: false }));
    }
  };

  const startTrellis = async () => {
    try {
      const response = await fetch('http://localhost:8787/api/trellis/start', {
        method: 'POST'
      });

      if (response.ok) {
        setTimeout(checkTrellisStatus, 3000);
      }
    } catch (error) {
      console.error('Failed to start TRELLIS:', error);
    }
  };

  const stopTrellis = async () => {
    try {
      const response = await fetch('http://localhost:8189/stop', {
        method: 'POST'
      });

      if (response.ok) {
        setTrellisStatus(prev => ({ ...prev, running: false }));
      }
    } catch (error) {
      console.error('Failed to stop TRELLIS:', error);
    }
  };

  const submitGenerationJob = async () => {
    if (!newJob.prompt.trim()) return;

    const job = {
      id: Date.now().toString(),
      ...newJob,
      status: 'queued',
      submittedAt: new Date(),
      progress: 0
    };

    setGenerationQueue(prev => [...prev, job]);

    try {
      const response = await fetch('http://localhost:8189/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newJob)
      });

      if (response.ok) {
        const result = await response.json();
        const updatedJob = { ...job, serverJobId: result.job_id };

        setGenerationQueue(prev => prev.map(j => j.id === job.id ? updatedJob : j));
        monitorJobProgress(updatedJob);
      }
    } catch (error) {
      setGenerationQueue(prev => prev.map(j =>
        j.id === job.id ? { ...j, status: 'error', error: error.message } : j
      ));
    }

    setNewJob(prev => ({ ...prev, prompt: '' }));
  };

  const monitorJobProgress = (job) => {
    const interval = setInterval(async () => {
      try {
        const response = await fetch(`http://localhost:8189/job/${job.serverJobId}`);
        if (response.ok) {
          const status = await response.json();

          setGenerationQueue(prev => prev.map(j =>
            j.id === job.id ? { ...j, ...status } : j
          ));

          if (status.status === 'completed' || status.status === 'error') {
            clearInterval(interval);

            if (status.status === 'completed') {
              setGenerationHistory(prev => [status, ...prev.slice(0, 49)]);
              setGenerationQueue(prev => prev.filter(j => j.id !== job.id));
            }
          }
        }
      } catch (error) {
        clearInterval(interval);
        setGenerationQueue(prev => prev.map(j =>
          j.id === job.id ? { ...j, status: 'error', error: 'Connection failed' } : j
        ));
      }
    }, 2000);
  };

  const downloadModel = async (jobId) => {
    const job = generationHistory.find(j => j.id === jobId);
    if (!job || !job.outputFile) return;

    try {
      const response = await fetch(`http://localhost:8189/download/${job.outputFile}`);
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = job.outputFile;
        a.click();
        window.URL.revokeObjectURL(url);
      }
    } catch (error) {
      console.error('Failed to download model:', error);
    }
  };

  const optimizeSettings = async () => {
    try {
      const response = await fetch('http://localhost:8189/optimize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings)
      });

      if (response.ok) {
        const optimized = await response.json();
        setSettings(prev => ({ ...prev, ...optimized }));
      }
    } catch (error) {
      console.error('Failed to optimize settings:', error);
    }
  };

  const updateSettings = async (newSettings) => {
    try {
      await fetch('http://localhost:8189/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newSettings)
      });

      setSettings(newSettings);
    } catch (error) {
      console.error('Failed to update settings:', error);
    }
  };

  const previewModel = (job) => {
    if (job.previewImage) {
      window.open(`http://localhost:8189/preview/${job.previewImage}`, '_blank');
    }
  };

  const getQualityColor = (quality) => {
    switch (quality) {
      case 'low': return 'text-red-400';
      case 'medium': return 'text-yellow-400';
      case 'high': return 'text-green-400';
      case 'ultra': return 'text-blue-400';
      default: return 'text-gray-400';
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'running': return 'text-blue-400 animate-pulse';
      case 'completed': return 'text-green-400';
      case 'error': return 'text-red-400';
      case 'queued': return 'text-yellow-400';
      default: return 'text-gray-400';
    }
  };

  return (
    <div className="h-full w-full bg-slate-900/95 rounded-lg flex flex-col">
      {/* Header */}
      <div className="p-6 border-b border-slate-700">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white">TRELLIS 3D Manager</h1>
            <p className="text-slate-400 mt-1">AI-Powered 3D Model Generation</p>
          </div>
          <div className="flex items-center space-x-4">
            {trellisStatus.running ? (
              <button
                onClick={stopTrellis}
                className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors"
              >
                ⏹️ Stop TRELLIS
              </button>
            ) : (
              <button
                onClick={startTrellis}
                className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors"
              >
                ▶️ Start TRELLIS
              </button>
            )}
            <button
              onClick={onClose}
              className="px-4 py-2 bg-slate-600 hover:bg-slate-700 text-white rounded-lg transition-colors"
            >
              ✕
            </button>
          </div>
        </div>

        {/* Status Bar */}
        <div className="mt-4 flex items-center space-x-6">
          <div className="flex items-center space-x-2">
            <div className={`w-3 h-3 rounded-full ${trellisStatus.running ? 'bg-green-400' : 'bg-red-400'}`} />
            <span className="text-sm text-slate-300">
              Status: {trellisStatus.running ? 'Running' : 'Stopped'}
            </span>
          </div>
          <span className="text-sm text-slate-300">Port: {trellisStatus.port}</span>
          <span className="text-sm text-slate-300">Version: {trellisStatus.version}</span>
          <span className="text-sm text-slate-300">
            Queue: {generationQueue.length} jobs
          </span>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {/* System Resources */}
        <div className="glass-strong rounded-lg p-6">
          <h2 className="text-xl font-bold text-white mb-4">System Resources</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {Object.entries(trellisStatus.systemResources).map(([resource, value]) => (
              <div key={resource} className="glass-medium rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-semibold text-white capitalize">{resource}</h3>
                  <div className={`w-3 h-3 rounded-full ${
                    value > 80 ? 'bg-red-400' : value > 60 ? 'bg-yellow-400' : 'bg-green-400'
                  }`} />
                </div>
                <div className="text-2xl font-bold text-white">{value}%</div>
                <div className="w-full bg-slate-700 rounded-full h-2 mt-2">
                  <div
                    className={`h-2 rounded-full transition-all duration-300 ${
                      value > 80 ? 'bg-red-400' : value > 60 ? 'bg-yellow-400' : 'bg-green-400'
                    }`}
                    style={{ width: `${value}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Generation Queue */}
          <div className="glass-strong rounded-lg p-6">
            <h2 className="text-xl font-bold text-white mb-4">Generation Queue</h2>

            {/* New Job Form */}
            <div className="glass-medium rounded-lg p-4 mb-4">
              <h3 className="font-semibold text-white mb-3">New 3D Generation Job</h3>
              <div className="space-y-3">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1">
                    Prompt
                  </label>
                  <textarea
                    value={newJob.prompt}
                    onChange={(e) => setNewJob(prev => ({ ...prev, prompt: e.target.value }))}
                    placeholder="Describe the 3D model you want to generate..."
                    className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white text-sm resize-none"
                    rows={3}
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-1">
                      Quality
                    </label>
                    <select
                      value={newJob.quality}
                      onChange={(e) => setNewJob(prev => ({ ...prev, quality: e.target.value }))}
                      className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white text-sm"
                    >
                      <option value="low">Low (Fast)</option>
                      <option value="medium">Medium (Balanced)</option>
                      <option value="high">High (Quality)</option>
                      <option value="ultra">Ultra (Best)</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-1">
                      Iterations
                    </label>
                    <input
                      type="number"
                      value={newJob.iterations}
                      onChange={(e) => setNewJob(prev => ({ ...prev, iterations: parseInt(e.target.value) }))}
                      min="10"
                      max="100"
                      className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white text-sm"
                    />
                  </div>
                </div>

                <button
                  onClick={submitGenerationJob}
                  disabled={!newJob.prompt.trim() || generationQueue.length >= settings.maxConcurrentJobs}
                  className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-600 text-white rounded transition-colors"
                >
                  🎨 Generate 3D Model
                </button>
              </div>
            </div>

            {/* Queue List */}
            <div className="space-y-3">
              {generationQueue.length === 0 ? (
                <div className="text-center text-slate-400 py-8">
                  No jobs in queue
                </div>
              ) : (
                generationQueue.map(job => (
                  <div key={job.id} className="glass-medium rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center space-x-2">
                        <span className={`text-sm ${getStatusColor(job.status)}`}>
                          {job.status === 'running' ? '🔄' : job.status === 'queued' ? '⏳' : '❌'}
                        </span>
                        <span className="text-sm font-medium text-white capitalize">
                          {job.status}
                        </span>
                      </div>
                      <span className={`text-xs ${getQualityColor(job.quality)}`}>
                        {job.quality}
                      </span>
                    </div>

                    <div className="text-sm text-slate-300 mb-2">{job.prompt}</div>

                    {job.status === 'running' && job.progress > 0 && (
                      <div className="mt-2">
                        <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
                          <span>Progress</span>
                          <span>{Math.round(job.progress)}%</span>
                        </div>
                        <div className="w-full bg-slate-700 rounded-full h-2">
                          <div
                            className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                            style={{ width: `${job.progress}%` }}
                          />
                        </div>
                      </div>
                    )}

                    {job.error && (
                      <div className="text-xs text-red-400 mt-2">
                        Error: {job.error}
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Generation History */}
          <div className="glass-strong rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold text-white">Generation History</h2>
              <span className="text-sm text-slate-400">
                {generationHistory.length} models
              </span>
            </div>

            <div className="space-y-3 max-h-96 overflow-y-auto">
              {generationHistory.length === 0 ? (
                <div className="text-center text-slate-400 py-8">
                  No generation history yet
                </div>
              ) : (
                generationHistory.map(job => (
                  <div key={job.id} className="glass-medium rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center space-x-2">
                        <span className="text-green-400">✓</span>
                        <span className="text-sm font-medium text-white">Completed</span>
                      </div>
                      <span className="text-xs text-slate-400">
                        {new Date(job.completedAt).toLocaleString()}
                      </span>
                    </div>

                    <div className="text-sm text-slate-300 mb-3">{job.prompt}</div>

                    <div className="flex items-center justify-between text-xs text-slate-400 mb-3">
                      <span>Quality: <span className={getQualityColor(job.quality)}>{job.quality}</span></span>
                      <span>Iterations: {job.iterations}</span>
                      <span>Time: {Math.round((job.completedAt - job.submittedAt) / 1000)}s</span>
                    </div>

                    <div className="flex space-x-2">
                      {job.previewImage && (
                        <button
                          onClick={() => previewModel(job)}
                          className="flex-1 px-3 py-1 bg-slate-600 hover:bg-slate-700 text-white rounded text-xs transition-colors"
                        >
                          👁️ Preview
                        </button>
                      )}
                      <button
                        onClick={() => downloadModel(job.id)}
                        className="flex-1 px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded text-xs transition-colors"
                      >
                        📥 Download
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Settings */}
        <div className="glass-strong rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-white">Settings & Optimization</h2>
            <button
              onClick={optimizeSettings}
              className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded text-sm transition-colors"
            >
              🤖 Auto-Optimize
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div>
              <h3 className="font-semibold text-white mb-3">Performance Settings</h3>
              <div className="space-y-3">
                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={settings.autoOptimize}
                    onChange={(e) => updateSettings({ ...settings, autoOptimize: e.target.checked })}
                    className="rounded text-blue-600"
                  />
                  <span className="text-sm text-slate-300">Auto-optimize performance</span>
                </label>

                <div>
                  <label className="block text-sm text-slate-300 mb-1">Max Concurrent Jobs</label>
                  <input
                    type="number"
                    value={settings.maxConcurrentJobs}
                    onChange={(e) => updateSettings({ ...settings, maxConcurrentJobs: parseInt(e.target.value) })}
                    min="1"
                    max="8"
                    className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white text-sm"
                  />
                </div>

                <div>
                  <label className="block text-sm text-slate-300 mb-1">Quality Preset</label>
                  <select
                    value={settings.qualityPreset}
                    onChange={(e) => updateSettings({ ...settings, qualityPreset: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white text-sm"
                  >
                    <option value="fast">Fast (Low Quality)</option>
                    <option value="balanced">Balanced</option>
                    <option value="quality">Quality (Slow)</option>
                  </select>
                </div>
              </div>
            </div>

            <div>
              <h3 className="font-semibold text-white mb-3">Output Settings</h3>
              <div className="space-y-3">
                <div>
                  <label className="block text-sm text-slate-300 mb-1">Output Format</label>
                  <select
                    value={settings.outputFormat}
                    onChange={(e) => updateSettings({ ...settings, outputFormat: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white text-sm"
                  >
                    <option value="glb">GLB (Recommended)</option>
                    <option value="obj">OBJ</option>
                    <option value="fbx">FBX</option>
                    <option value="stl">STL</option>
                  </select>
                </div>

                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={settings.enableTexturing}
                    onChange={(e) => updateSettings({ ...settings, enableTexturing: e.target.checked })}
                    className="rounded text-blue-600"
                  />
                  <span className="text-sm text-slate-300">Enable texturing</span>
                </label>

                <div>
                  <label className="block text-sm text-slate-300 mb-1">Texture Resolution</label>
                  <select
                    value={settings.textureResolution}
                    onChange={(e) => updateSettings({ ...settings, textureResolution: e.target.value })}
                    disabled={!settings.enableTexturing}
                    className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white text-sm disabled:opacity-50"
                  >
                    <option value="512">512px</option>
                    <option value="1024">1024px</option>
                    <option value="2048">2048px</option>
                    <option value="4096">4096px</option>
                  </select>
                </div>
              </div>
            </div>

            <div>
              <h3 className="font-semibold text-white mb-3">AI Integration</h3>
              <div className="space-y-3">
                <div className="p-3 bg-slate-800/50 rounded-lg">
                  <div className="text-sm text-slate-300 mb-2">DuckBot Integration</div>
                  <div className="text-xs text-slate-400">
                    TRELLIS is integrated with DuckBot for intelligent prompt optimization and model enhancement.
                  </div>
                </div>

                <div className="p-3 bg-slate-800/50 rounded-lg">
                  <div className="text-sm text-slate-300 mb-2">Workflow Support</div>
                  <div className="text-xs text-slate-400">
                    Use TRELLIS in cross-service workflows for automated text-to-3D pipelines.
                  </div>
                </div>

                <div className="p-3 bg-slate-800/50 rounded-lg">
                  <div className="text-sm text-slate-300 mb-2">Smart Optimization</div>
                  <div className="text-xs text-slate-400">
                    AI automatically adjusts parameters based on your prompt complexity and hardware.
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TRELLISManager;