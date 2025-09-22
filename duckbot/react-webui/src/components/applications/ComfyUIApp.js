import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useSystem } from '../../contexts/SystemContext';

// ComfyUI Application Component
const ComfyUIApp = ({ onClose }) => {
  const { comfyuiStatus, startComfyUI, stopComfyUI, restartComfyUI, getComfyUIStats } = useSystem();

  // Local state
  const [selectedWorkflow, setSelectedWorkflow] = useState('text_to_image');
  const [workflowParams, setWorkflowParams] = useState({});
  const [executionQueue, setExecutionQueue] = useState([]);
  const [activeWorkflows, setActiveWorkflows] = useState([]);
  const [results, setResults] = useState([]);
  const [config, setConfig] = useState({
    gpuMemoryLimit: 80,
    maxConcurrentWorkflows: 3,
    autoStartServer: true,
    enableGPUMode: true
  });

  // Workflow templates
  const workflowTemplates = [
    {
      id: 'text_to_image',
      name: 'Text to Image',
      description: 'Generate images from text prompts',
      icon: '🎨',
      category: 'generation',
      parameters: [
        { name: 'prompt', type: 'textarea', label: 'Prompt', required: true, default: 'A beautiful landscape' },
        { name: 'negative_prompt', type: 'textarea', label: 'Negative Prompt', default: 'ugly, blurry' },
        { name: 'width', type: 'number', label: 'Width', default: 512, min: 256, max: 1024 },
        { name: 'height', type: 'number', label: 'Height', default: 512, min: 256, max: 1024 },
        { name: 'steps', type: 'number', label: 'Steps', default: 20, min: 1, max: 50 },
        { name: 'cfg_scale', type: 'number', label: 'CFG Scale', default: 7, min: 1, max: 20 },
        { name: 'seed', type: 'number', label: 'Seed', default: -1 }
      ]
    },
    {
      id: 'image_to_image',
      name: 'Image to Image',
      description: 'Transform existing images',
      icon: '🖼️',
      category: 'processing',
      parameters: [
        { name: 'input_image', type: 'file', label: 'Input Image', required: true, accept: 'image/*' },
        { name: 'prompt', type: 'textarea', label: 'Prompt', required: true },
        { name: 'negative_prompt', type: 'textarea', label: 'Negative Prompt', default: 'ugly, blurry' },
        { name: 'denoise', type: 'range', label: 'Denoise Strength', default: 0.75, min: 0, max: 1, step: 0.01 },
        { name: 'steps', type: 'number', label: 'Steps', default: 20, min: 1, max: 50 },
        { name: 'cfg_scale', type: 'number', label: 'CFG Scale', default: 7, min: 1, max: 20 }
      ]
    },
    {
      id: 'upscaling',
      name: 'Image Upscaling',
      description: 'Enhance image resolution',
      icon: '🔍',
      category: 'enhancement',
      parameters: [
        { name: 'input_image', type: 'file', label: 'Input Image', required: true, accept: 'image/*' },
        { name: 'scale_factor', type: 'select', label: 'Scale Factor', options: ['2x', '4x', '8x'], default: '4x' },
        { name: 'model', type: 'select', label: 'Upscale Model', options: ['4x-UltraSharp', 'ESRGAN_4x', 'RealESRGAN_x4'], default: '4x-UltraSharp' }
      ]
    },
    {
      id: 'inpainting',
      name: 'Inpainting',
      description: 'Edit specific image regions',
      icon: '🎭',
      category: 'editing',
      parameters: [
        { name: 'input_image', type: 'file', label: 'Input Image', required: true, accept: 'image/*' },
        { name: 'mask_image', type: 'file', label: 'Mask Image', required: true, accept: 'image/*' },
        { name: 'prompt', type: 'textarea', label: 'Prompt', required: true },
        { name: 'negative_prompt', type: 'textarea', label: 'Negative Prompt', default: 'ugly, blurry' },
        { name: 'steps', type: 'number', label: 'Steps', default: 20, min: 1, max: 50 }
      ]
    },
    {
      id: 'controlnet',
      name: 'ControlNet',
      description: 'Controlled image generation',
      icon: '🎛️',
      category: 'controlled_generation',
      parameters: [
        { name: 'control_image', type: 'file', label: 'Control Image', required: true, accept: 'image/*' },
        { name: 'control_type', type: 'select', label: 'Control Type', options: ['canny', 'depth', 'pose', 'normal'], default: 'canny' },
        { name: 'prompt', type: 'textarea', label: 'Prompt', required: true },
        { name: 'negative_prompt', type: 'textarea', label: 'Negative Prompt', default: 'ugly, blurry' },
        { name: 'control_strength', type: 'range', label: 'Control Strength', default: 1.0, min: 0, max: 1, step: 0.1 },
        { name: 'steps', type: 'number', label: 'Steps', default: 20, min: 1, max: 50 }
      ]
    }
  ];

  // Initialize workflow parameters
  useEffect(() => {
    const template = workflowTemplates.find(t => t.id === selectedWorkflow);
    if (template) {
      const initialParams = {};
      template.parameters.forEach(param => {
        initialParams[param.name] = param.default || '';
      });
      setWorkflowParams(initialParams);
    }
  }, [selectedWorkflow]);

  // Update active workflows periodically
  useEffect(() => {
    const interval = setInterval(async () => {
      const stats = await getComfyUIStats();
      if (stats && stats.activeWorkflows) {
        setActiveWorkflows(stats.activeWorkflows);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [getComfyUIStats]);

  // Handle parameter changes
  const handleParamChange = useCallback((paramName, value) => {
    setWorkflowParams(prev => ({
      ...prev,
      [paramName]: value
    }));
  }, []);

  // Execute workflow
  const executeWorkflow = useCallback(async () => {
    const template = workflowTemplates.find(t => t.id === selectedWorkflow);
    if (!template) return;

    // Validate required parameters
    const missingParams = template.parameters
      .filter(p => p.required && (!workflowParams[p.name] || workflowParams[p.name] === ''))
      .map(p => p.label);

    if (missingParams.length > 0) {
      alert(`Missing required parameters: ${missingParams.join(', ')}`);
      return;
    }

    // Add to execution queue
    const queueItem = {
      id: Date.now().toString(),
      workflowType: selectedWorkflow,
      parameters: workflowParams,
      status: 'queued',
      timestamp: new Date().toISOString()
    };

    setExecutionQueue(prev => [...prev, queueItem]);

    // Simulate workflow execution (in real implementation, this would call the backend)
    setTimeout(() => {
      setExecutionQueue(prev => prev.map(item =>
        item.id === queueItem.id ? { ...item, status: 'running' } : item
      ));

      // Simulate completion
      setTimeout(() => {
        const result = {
          id: queueItem.id,
          workflowType: selectedWorkflow,
          parameters: workflowParams,
          status: 'completed',
          timestamp: new Date().toISOString(),
          outputFiles: [
            `generated_${Date.now()}.png`
          ],
          executionTime: Math.random() * 30 + 10 // 10-40 seconds
        };

        setResults(prev => [result, ...prev]);
        setExecutionQueue(prev => prev.filter(item => item.id !== queueItem.id));
      }, Math.random() * 20000 + 5000); // 5-25 seconds
    }, 1000);
  }, [selectedWorkflow, workflowParams, workflowTemplates]);

  // Server control functions
  const handleStartServer = useCallback(async () => {
    await startComfyUI();
  }, [startComfyUI]);

  const handleStopServer = useCallback(async () => {
    await stopComfyUI();
  }, [stopComfyUI]);

  const handleRestartServer = useCallback(async () => {
    await restartComfyUI();
  }, [restartComfyUI]);

  // Render parameter input
  const renderParameterInput = (param) => {
    const value = workflowParams[param.name] || param.default || '';

    switch (param.type) {
      case 'textarea':
        return (
          <textarea
            className="w-full p-2 bg-slate-700 text-white rounded border border-slate-600 focus:border-blue-500 focus:outline-none"
            rows={3}
            value={value}
            onChange={(e) => handleParamChange(param.name, e.target.value)}
            placeholder={param.label}
          />
        );
      case 'number':
        return (
          <input
            type="number"
            className="w-full p-2 bg-slate-700 text-white rounded border border-slate-600 focus:border-blue-500 focus:outline-none"
            value={value}
            onChange={(e) => handleParamChange(param.name, parseFloat(e.target.value))}
            min={param.min}
            max={param.max}
          />
        );
      case 'range':
        return (
          <div className="flex items-center space-x-2">
            <input
              type="range"
              className="flex-1"
              value={value}
              onChange={(e) => handleParamChange(param.name, parseFloat(e.target.value))}
              min={param.min}
              max={param.max}
              step={param.step || 0.1}
            />
            <span className="text-white text-sm w-12 text-right">{value}</span>
          </div>
        );
      case 'select':
        return (
          <select
            className="w-full p-2 bg-slate-700 text-white rounded border border-slate-600 focus:border-blue-500 focus:outline-none"
            value={value}
            onChange={(e) => handleParamChange(param.name, e.target.value)}
          >
            {param.options.map(option => (
              <option key={option} value={option}>{option}</option>
            ))}
          </select>
        );
      case 'file':
        return (
          <input
            type="file"
            className="w-full p-2 bg-slate-700 text-white rounded border border-slate-600 focus:border-blue-500 focus:outline-none"
            accept={param.accept}
            onChange={(e) => handleParamChange(param.name, e.target.files[0])}
          />
        );
      default:
        return (
          <input
            type="text"
            className="w-full p-2 bg-slate-700 text-white rounded border border-slate-600 focus:border-blue-500 focus:outline-none"
            value={value}
            onChange={(e) => handleParamChange(param.name, e.target.value)}
            placeholder={param.label}
          />
        );
    }
  };

  return (
    <div className="h-full flex flex-col bg-slate-900 text-white">
      {/* Header */}
      <div className="flex items-center justify-between p-4 bg-slate-800 border-b border-slate-700">
        <div className="flex items-center space-x-2">
          <span className="text-2xl">🎨</span>
          <h2 className="text-xl font-semibold">ComfyUI Manager</h2>
          <div className={`px-2 py-1 rounded text-xs ${
            comfyuiStatus.isRunning ? 'bg-green-600' : 'bg-red-600'
          }`}>
            {comfyuiStatus.isRunning ? 'Running' : 'Stopped'}
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={handleStartServer}
            disabled={comfyuiStatus.isRunning}
            className={`px-3 py-1 rounded text-sm ${
              comfyuiStatus.isRunning
                ? 'bg-green-700 cursor-not-allowed'
                : 'bg-green-600 hover:bg-green-700'
            }`}
          >
            Start
          </button>
          <button
            onClick={handleStopServer}
            disabled={!comfyuiStatus.isRunning}
            className={`px-3 py-1 rounded text-sm ${
              !comfyuiStatus.isRunning
                ? 'bg-red-700 cursor-not-allowed'
                : 'bg-red-600 hover:bg-red-700'
            }`}
          >
            Stop
          </button>
          <button
            onClick={handleRestartServer}
            className="px-3 py-1 rounded text-sm bg-yellow-600 hover:bg-yellow-700"
          >
            Restart
          </button>
          <button
            onClick={onClose}
            className="px-3 py-1 rounded text-sm bg-gray-600 hover:bg-gray-700"
          >
            ✕
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Panel - Dashboard */}
        <div className="w-80 bg-slate-800 border-r border-slate-700 flex flex-col">
          {/* System Status */}
          <div className="p-4 border-b border-slate-700">
            <h3 className="text-sm font-semibold mb-3 text-slate-300">System Status</h3>
            <div className="space-y-2 text-xs">
              <div className="flex justify-between">
                <span className="text-slate-400">Server Status</span>
                <span className={comfyuiStatus.isRunning ? 'text-green-400' : 'text-red-400'}>
                  {comfyuiStatus.isRunning ? 'Online' : 'Offline'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Port</span>
                <span className="text-white">{comfyuiStatus.port || '8188'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">GPU Usage</span>
                <span className="text-white">{comfyuiStatus.gpuUsage || '0'}%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">VRAM</span>
                <span className="text-white">{comfyuiStatus.gpuMemory || '0'}/{comfyuiStatus.gpuMemoryTotal || '0'} GB</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Active Workflows</span>
                <span className="text-white">{activeWorkflows.length}</span>
              </div>
            </div>
          </div>

          {/* Resource Management */}
          <div className="p-4 border-b border-slate-700">
            <h3 className="text-sm font-semibold mb-3 text-slate-300">Resource Management</h3>
            <div className="space-y-3">
              <div>
                <label className="text-xs text-slate-400">GPU Memory Limit</label>
                <div className="flex items-center space-x-2">
                  <input
                    type="range"
                    min="50"
                    max="95"
                    value={config.gpuMemoryLimit}
                    onChange={(e) => setConfig(prev => ({ ...prev, gpuMemoryLimit: parseInt(e.target.value) }))}
                    className="flex-1"
                  />
                  <span className="text-xs text-white">{config.gpuMemoryLimit}%</span>
                </div>
              </div>
              <div>
                <label className="text-xs text-slate-400">Max Concurrent Workflows</label>
                <select
                  value={config.maxConcurrentWorkflows}
                  onChange={(e) => setConfig(prev => ({ ...prev, maxConcurrentWorkflows: parseInt(e.target.value) }))}
                  className="w-full p-1 bg-slate-700 text-white rounded text-xs border border-slate-600"
                >
                  {[1, 2, 3, 4, 5].map(num => (
                    <option key={num} value={num}>{num}</option>
                  ))}
                </select>
              </div>
              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="enableGPUMode"
                  checked={config.enableGPUMode}
                  onChange={(e) => setConfig(prev => ({ ...prev, enableGPUMode: e.target.checked }))}
                  className="rounded"
                />
                <label htmlFor="enableGPUMode" className="text-xs text-slate-300">Enable GPU Mode</label>
              </div>
            </div>
          </div>

          {/* Active Workflows */}
          <div className="p-4 border-b border-slate-700 flex-1 overflow-hidden">
            <h3 className="text-sm font-semibold mb-3 text-slate-300">Active Workflows</h3>
            <div className="space-y-2 overflow-y-auto max-h-40">
              <AnimatePresence>
                {activeWorkflows.map(workflow => (
                  <motion.div
                    key={workflow.id}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -10 }}
                    className="p-2 bg-slate-700 rounded text-xs"
                  >
                    <div className="flex justify-between items-center">
                      <span className="text-white font-medium">{workflow.type}</span>
                      <span className={`px-1 rounded ${
                        workflow.status === 'running' ? 'bg-yellow-600' : 'bg-green-600'
                      }`}>
                        {workflow.status}
                      </span>
                    </div>
                    <div className="text-slate-400 mt-1">
                      {workflow.progress && `${Math.round(workflow.progress)}%`}
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>
          </div>

          {/* Execution Queue */}
          <div className="p-4 flex-1 overflow-hidden">
            <h3 className="text-sm font-semibold mb-3 text-slate-300">Execution Queue</h3>
            <div className="space-y-2 overflow-y-auto max-h-40">
              <AnimatePresence>
                {executionQueue.map(item => (
                  <motion.div
                    key={item.id}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -10 }}
                    className="p-2 bg-slate-700 rounded text-xs"
                  >
                    <div className="flex justify-between items-center">
                      <span className="text-white font-medium">{item.workflowType}</span>
                      <span className={`px-1 rounded ${
                        item.status === 'queued' ? 'bg-blue-600' : 'bg-yellow-600'
                      }`}>
                        {item.status}
                      </span>
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>
              {executionQueue.length === 0 && (
                <div className="text-center text-slate-500 text-xs py-4">
                  No queued workflows
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Right Panel - Workflow Interface */}
        <div className="flex-1 flex flex-col">
          {/* Workflow Selection */}
          <div className="p-4 border-b border-slate-700">
            <h3 className="text-sm font-semibold mb-3 text-slate-300">Workflow Templates</h3>
            <div className="grid grid-cols-5 gap-2">
              {workflowTemplates.map(template => (
                <button
                  key={template.id}
                  onClick={() => setSelectedWorkflow(template.id)}
                  className={`p-3 rounded-lg border text-center transition-all ${
                    selectedWorkflow === template.id
                      ? 'border-blue-500 bg-blue-500/20'
                      : 'border-slate-600 hover:border-slate-500 bg-slate-800'
                  }`}
                >
                  <div className="text-2xl mb-1">{template.icon}</div>
                  <div className="text-xs text-white font-medium">{template.name}</div>
                  <div className="text-xs text-slate-400 mt-1">{template.category}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Workflow Configuration */}
          <div className="flex-1 flex">
            {/* Parameters */}
            <div className="w-96 p-4 border-r border-slate-700 overflow-y-auto">
              <h3 className="text-sm font-semibold mb-3 text-slate-300">Parameters</h3>
              <div className="space-y-4">
                {workflowTemplates
                  .find(t => t.id === selectedWorkflow)
                  ?.parameters.map(param => (
                    <div key={param.name}>
                      <label className="block text-xs text-slate-400 mb-1">
                        {param.label}
                        {param.required && <span className="text-red-400 ml-1">*</span>}
                      </label>
                      {renderParameterInput(param)}
                    </div>
                  ))}
              </div>

              <button
                onClick={executeWorkflow}
                disabled={executionQueue.length >= config.maxConcurrentWorkflows}
                className={`w-full mt-4 py-2 px-4 rounded font-medium text-sm transition-all ${
                  executionQueue.length >= config.maxConcurrentWorkflows
                    ? 'bg-gray-600 cursor-not-allowed'
                    : 'bg-blue-600 hover:bg-blue-700'
                }`}
              >
                Execute Workflow
              </button>
            </div>

            {/* Results Preview */}
            <div className="flex-1 p-4 overflow-y-auto">
              <h3 className="text-sm font-semibold mb-3 text-slate-300">Results</h3>
              <div className="space-y-4">
                <AnimatePresence>
                  {results.map(result => (
                    <motion.div
                      key={result.id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -20 }}
                      className="bg-slate-800 rounded-lg p-4 border border-slate-700"
                    >
                      <div className="flex justify-between items-start mb-2">
                        <div>
                          <h4 className="text-white font-medium">{result.workflowType}</h4>
                          <p className="text-xs text-slate-400">
                            {new Date(result.timestamp).toLocaleString()}
                          </p>
                        </div>
                        <div className="flex items-center space-x-2">
                          <span className="text-xs text-slate-400">
                            {result.executionTime.toFixed(1)}s
                          </span>
                          <span className={`px-2 py-1 rounded text-xs ${
                            result.status === 'completed' ? 'bg-green-600' : 'bg-red-600'
                          }`}>
                            {result.status}
                          </span>
                        </div>
                      </div>

                      <div className="grid grid-cols-3 gap-2 mt-3">
                        {result.outputFiles.map((file, index) => (
                          <div key={index} className="bg-slate-700 rounded p-2">
                            <div className="aspect-square bg-slate-600 rounded mb-1 flex items-center justify-center">
                              <span className="text-2xl">🖼️</span>
                            </div>
                            <p className="text-xs text-slate-400 truncate">{file}</p>
                            <button className="text-xs text-blue-400 hover:text-blue-300 mt-1">
                              Download
                            </button>
                          </div>
                        ))}
                      </div>
                    </motion.div>
                  ))}
                </AnimatePresence>

                {results.length === 0 && (
                  <div className="text-center text-slate-500 py-8">
                    <div className="text-4xl mb-2">🎨</div>
                    <p className="text-sm">No results yet</p>
                    <p className="text-xs mt-1">Execute a workflow to see results here</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ComfyUIApp;