import React, { useState, useEffect, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useSystem } from '../../contexts/SystemContext';
import TRELLISService from '../../services/trellisService';
import { TRELLISAssetViewer, AssetPreview } from './TRELLISAssetViewer';
import TRELLISProjectManager from './TRELLISProjectManager';
import TRELLISConfig from './TRELLISConfig';

// 3D Viewer Component
const ThreeDViewer = ({ modelUrl, className = '' }) => {
  const canvasRef = useRef(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!modelUrl || !canvasRef.current) return;

    const loadModel = async () => {
      try {
        setIsLoading(true);
        setError(null);

        // Load Three.js dynamically
        const THREE = await import('three');
        const { OrbitControls } = await import('three/examples/jsm/controls/OrbitControls');
        const { GLTFLoader } = await import('three/examples/jsm/loaders/GLTFLoader');

        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(75, canvasRef.current.clientWidth / canvasRef.current.clientHeight, 0.1, 1000);
        const renderer = new THREE.WebGLRenderer({ canvas: canvasRef.current, antialias: true });

        renderer.setSize(canvasRef.current.clientWidth, canvasRef.current.clientHeight);
        renderer.setClearColor(0x1a1a1a);

        // Add lighting
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
        scene.add(ambientLight);
        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
        directionalLight.position.set(10, 10, 5);
        scene.add(directionalLight);

        // Load model
        const loader = new GLTFLoader();
        const gltf = await loader.loadAsync(modelUrl);
        scene.add(gltf.scene);

        // Center and scale model
        const box = new THREE.Box3().setFromObject(gltf.scene);
        const center = box.getCenter(new THREE.Vector3());
        gltf.scene.position.sub(center);

        const size = box.getSize(new THREE.Vector3());
        const maxDim = Math.max(size.x, size.y, size.z);
        const scale = 2 / maxDim;
        gltf.scene.scale.multiplyScalar(scale);

        camera.position.z = 5;

        // Add controls
        const controls = new OrbitControls(camera, renderer.domElement);
        controls.enableDamping = true;
        controls.dampingFactor = 0.05;

        // Animation loop
        const animate = () => {
          requestAnimationFrame(animate);
          controls.update();
          renderer.render(scene, camera);
        };
        animate();

        setIsLoading(false);
      } catch (err) {
        console.error('Failed to load 3D model:', err);
        setError('Failed to load 3D model');
        setIsLoading(false);
      }
    };

    loadModel();

    return () => {
      // Cleanup
      if (canvasRef.current) {
        const context = canvasRef.current.getContext('webgl');
        if (context) {
          context.getExtension('WEBGL_lose_context')?.loseContext();
        }
      }
    };
  }, [modelUrl]);

  return (
    <div className={`relative bg-slate-800 rounded-lg overflow-hidden ${className}`}>
      <canvas
        ref={canvasRef}
        className="w-full h-full"
        style={{ minHeight: '300px' }}
      />
      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center bg-slate-900/80">
          <div className="text-center">
            <div className="animate-spin w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full mx-auto mb-2"></div>
            <p className="text-white text-sm">Loading 3D model...</p>
          </div>
        </div>
      )}
      {error && (
        <div className="absolute inset-0 flex items-center justify-center bg-slate-900/80">
          <div className="text-center text-red-400">
            <p className="text-sm">{error}</p>
          </div>
        </div>
      )}
    </div>
  );
};

// TRELLIS Application Component
const TRELLISApp = ({ onClose }) => {
  const trellisService = useRef(new TRELLISService()).current;

  // State management
  const [trellisStatus, setTrellisStatus] = useState({
    isRunning: false,
    version: '',
    gpuUsage: 0,
    gpuMemory: 0,
    gpuMemoryTotal: 0,
    activeJobs: 0,
    queuedJobs: 0
  });

  const [selectedTab, setSelectedTab] = useState('dashboard');
  const [generationMode, setGenerationMode] = useState('text-to-3d');
  const [generationParams, setGenerationParams] = useState({});
  const [activeProjects, setActiveProjects] = useState([]);
  const [recentAssets, setRecentAssets] = useState([]);
  const [jobQueue, setJobQueue] = useState([]);
  const [config, setConfig] = useState({
    outputPath: './output',
    maxResolution: 1024,
    quality: 'high',
    enableGPU: true,
    autoOptimize: true,
    formatPreference: 'glb'
  });

  const [showConfigModal, setShowConfigModal] = useState(false);

  // Generation modes configuration
  const generationModes = [
    {
      id: 'text-to-3d',
      name: 'Text to 3D',
      description: 'Generate 3D models from text descriptions',
      icon: '📝',
      parameters: [
        { name: 'prompt', type: 'textarea', label: 'Prompt', required: true, default: 'A detailed 3D model of...' },
        { name: 'style', type: 'select', label: 'Style', options: ['realistic', 'stylized', 'low-poly', 'sculpted'], default: 'realistic' },
        { name: 'resolution', type: 'number', label: 'Resolution', default: 512, min: 256, max: 1024 },
        { name: 'quality', type: 'select', label: 'Quality', options: ['draft', 'medium', 'high'], default: 'medium' },
        { name: 'seed', type: 'number', label: 'Seed', default: -1 }
      ]
    },
    {
      id: 'image-to-3d',
      name: 'Image to 3D',
      description: 'Convert 2D images to 3D models',
      icon: '🖼️',
      parameters: [
        { name: 'input_image', type: 'file', label: 'Input Image', required: true, accept: 'image/*' },
        { name: 'depth_estimation', type: 'checkbox', label: 'Enable Depth Estimation', default: true },
        { name: 'mesh_resolution', type: 'number', label: 'Mesh Resolution', default: 512, min: 256, max: 1024 },
        { name: 'smoothness', type: 'range', label: 'Smoothness', default: 0.5, min: 0, max: 1, step: 0.1 }
      ]
    },
    {
      id: 'mesh-refinement',
      name: 'Mesh Refinement',
      description: 'Optimize and enhance existing 3D meshes',
      icon: '🔧',
      parameters: [
        { name: 'input_mesh', type: 'file', label: 'Input Mesh', required: true, accept: '.obj,.glb,.gltf,.stl' },
        { name: 'target_polygons', type: 'number', label: 'Target Polygons', default: 10000 },
        { name: 'decimation_method', type: 'select', label: 'Decimation Method', options: ['quadric', 'clustering', 'vertex'], default: 'quadric' },
        { name: 'smooth_iterations', type: 'number', label: 'Smooth Iterations', default: 3, min: 0, max: 10 },
        { name: 'preserve_features', type: 'checkbox', label: 'Preserve Features', default: true }
      ]
    },
    {
      id: 'style-transfer',
      name: 'Style Transfer',
      description: 'Apply artistic styles to 3D models',
      icon: '🎨',
      parameters: [
        { name: 'input_mesh', type: 'file', label: 'Input Mesh', required: true, accept: '.obj,.glb,.gltf' },
        { name: 'style_prompt', type: 'textarea', label: 'Style Description', required: true, default: 'Artistic style description...' },
        { name: 'style_strength', type: 'range', label: 'Style Strength', default: 0.8, min: 0, max: 1, step: 0.1 },
        { name: 'preserve_geometry', type: 'checkbox', label: 'Preserve Base Geometry', default: true }
      ]
    },
    {
      id: 'slat-generation',
      name: 'SLAT Generation',
      description: 'Generate SLAT representations for efficient rendering',
      icon: '🌐',
      parameters: [
        { name: 'input_mesh', type: 'file', label: 'Input Mesh', required: true, accept: '.obj,.glb,.gltf' },
        { name: 'voxel_resolution', type: 'number', label: 'Voxel Resolution', default: 256, min: 64, max: 512 },
        { name: 'compression_level', type: 'select', label: 'Compression', options: ['low', 'medium', 'high'], default: 'medium' },
        { name: 'include_attributes', type: 'checkbox', label: 'Include Attributes', default: true }
      ]
    }
  ];

  // Initialize TRELLIS service
  useEffect(() => {
    const initializeTRELLIS = async () => {
      try {
        const status = await trellisService.getStatus();
        setTrellisStatus(prev => ({ ...prev, ...status }));
      } catch (error) {
        console.error('Failed to initialize TRELLIS:', error);
      }
    };

    initializeTRELLIS();
  }, [trellisService]);

  // Update job queue periodically
  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const queue = await trellisService.getJobQueue();
        setJobQueue(queue.jobs || []);
        setTrellisStatus(prev => ({
          ...prev,
          activeJobs: queue.active || 0,
          queuedJobs: queue.queued || 0
        }));
      } catch (error) {
        console.error('Failed to update job queue:', error);
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [trellisService]);

  // Load recent assets
  useEffect(() => {
    const loadRecentAssets = async () => {
      try {
        const assets = await trellisService.getAssets({ limit: 10, sort: 'created_at', order: 'desc' });
        setRecentAssets(assets.assets || []);
      } catch (error) {
        console.error('Failed to load recent assets:', error);
      }
    };

    loadRecentAssets();
  }, [trellisService]);

  // Handle parameter changes
  const handleParamChange = useCallback((paramName, value) => {
    setGenerationParams(prev => ({
      ...prev,
      [paramName]: value
    }));
  }, []);

  // Execute generation
  const executeGeneration = useCallback(async () => {
    const modeConfig = generationModes.find(m => m.id === generationMode);
    if (!modeConfig) return;

    // Validate required parameters
    const missingParams = modeConfig.parameters
      .filter(p => p.required && (!generationParams[p.name] || generationParams[p.name] === ''))
      .map(p => p.label);

    if (missingParams.length > 0) {
      alert(`Missing required parameters: ${missingParams.join(', ')}`);
      return;
    }

    try {
      let result;
      switch (generationMode) {
        case 'text-to-3d':
          result = await trellisService.generateTextTo3D(generationParams.prompt, {
            style: generationParams.style,
            resolution: generationParams.resolution,
            quality: generationParams.quality,
            seed: generationParams.seed
          });
          break;
        case 'image-to-3d':
          result = await trellisService.generateImageTo3D(generationParams.input_image, {
            depth_estimation: generationParams.depth_estimation,
            mesh_resolution: generationParams.mesh_resolution,
            smoothness: generationParams.smoothness
          });
          break;
        case 'mesh-refinement':
          result = await trellisService.refineMesh(generationParams.input_mesh, {
            target_polygons: generationParams.target_polygons,
            decimation_method: generationParams.decimation_method,
            smooth_iterations: generationParams.smooth_iterations,
            preserve_features: generationParams.preserve_features
          });
          break;
        case 'style-transfer':
          result = await trellisService.applyStyleTransfer(
            generationParams.input_mesh,
            generationParams.style_prompt,
            {
              style_strength: generationParams.style_strength,
              preserve_geometry: generationParams.preserve_geometry
            }
          );
          break;
        case 'slat-generation':
          result = await trellisService.generateSLAT(generationParams.input_mesh, {
            voxel_resolution: generationParams.voxel_resolution,
            compression_level: generationParams.compression_level,
            include_attributes: generationParams.include_attributes
          });
          break;
      }

      if (result && result.jobId) {
        // Add to job queue display
        setJobQueue(prev => [{
          id: result.jobId,
          type: generationMode,
          status: 'queued',
          progress: 0,
          created_at: new Date().toISOString(),
          ...result
        }, ...prev]);
      }

      // Refresh recent assets
      setTimeout(() => {
        trellisService.getAssets({ limit: 10, sort: 'created_at', order: 'desc' })
          .then(assets => setRecentAssets(assets.assets || []))
          .catch(console.error);
      }, 2000);

    } catch (error) {
      console.error('Generation failed:', error);
      alert(`Generation failed: ${error.message}`);
    }
  }, [generationMode, generationParams, trellisService]);

  // Render parameter input
  const renderParameterInput = (param) => {
    const value = generationParams[param.name] || param.default || '';

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
      case 'checkbox':
        return (
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={value}
              onChange={(e) => handleParamChange(param.name, e.target.checked)}
              className="rounded"
            />
            <span className="text-white text-sm">{param.label}</span>
          </label>
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
            type={param.type || 'text'}
            className="w-full p-2 bg-slate-700 text-white rounded border border-slate-600 focus:border-blue-500 focus:outline-none"
            value={value}
            onChange={(e) => handleParamChange(param.name, e.target.value)}
            placeholder={param.label}
            min={param.min}
            max={param.max}
          />
        );
    }
  };

  return (
    <div className="h-full flex flex-col bg-slate-900 text-white">
      {/* Header */}
      <div className="flex items-center justify-between p-4 bg-slate-800 border-b border-slate-700">
        <div className="flex items-center space-x-2">
          <span className="text-2xl">🌐</span>
          <h2 className="text-xl font-semibold">TRELLIS 3D Asset Generation</h2>
          <div className={`px-2 py-1 rounded text-xs ${
            trellisStatus.isRunning ? 'bg-green-600' : 'bg-red-600'
          }`}>
            {trellisStatus.isRunning ? 'Connected' : 'Offline'}
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setShowConfigModal(true)}
            className="px-3 py-1 rounded text-sm bg-slate-600 hover:bg-slate-500"
            title="Configuration"
          >
            ⚙️
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
        {['dashboard', 'generation', 'projects', 'assets', 'queue'].map(tab => (
          <button
            key={tab}
            onClick={() => setSelectedTab(tab)}
            className={`px-4 py-2 text-sm font-medium transition-colors ${
              selectedTab === tab
                ? 'bg-blue-600 text-white'
                : 'text-slate-300 hover:bg-slate-700 hover:text-white'
            }`}
          >
            {tab.charAt(0).toUpperCase() + tab.slice(1)}
          </button>
        ))}
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-hidden">
        {selectedTab === 'dashboard' && (
          <div className="p-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 overflow-y-auto">
            {/* System Status Card */}
            <div className="bg-slate-800 rounded-lg p-6">
              <h3 className="text-lg font-semibold mb-4 flex items-center">
                <span className="mr-2">🖥️</span>
                System Status
              </h3>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-slate-400">Server Status</span>
                  <span className={trellisStatus.isRunning ? 'text-green-400' : 'text-red-400'}>
                    {trellisStatus.isRunning ? 'Online' : 'Offline'}
                  </span>
                </div>
                {trellisStatus.version && (
                  <div className="flex justify-between">
                    <span className="text-slate-400">Version</span>
                    <span className="text-white">{trellisStatus.version}</span>
                  </div>
                )}
                <div className="flex justify-between">
                  <span className="text-slate-400">GPU Usage</span>
                  <span className="text-white">{trellisStatus.gpuUsage || 0}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">VRAM</span>
                  <span className="text-white">
                    {trellisStatus.gpuMemory || 0}/{trellisStatus.gpuMemoryTotal || 0} GB
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Active Jobs</span>
                  <span className="text-white">{trellisStatus.activeJobs || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Queued Jobs</span>
                  <span className="text-white">{trellisStatus.queuedJobs || 0}</span>
                </div>
              </div>
            </div>

            {/* Quick Actions Card */}
            <div className="bg-slate-800 rounded-lg p-6">
              <h3 className="text-lg font-semibold mb-4 flex items-center">
                <span className="mr-2">⚡</span>
                Quick Actions
              </h3>
              <div className="grid grid-cols-2 gap-3">
                {generationModes.slice(0, 4).map(mode => (
                  <button
                    key={mode.id}
                    onClick={() => {
                      setSelectedTab('generation');
                      setGenerationMode(mode.id);
                    }}
                    className="p-3 bg-slate-700 hover:bg-slate-600 rounded-lg text-center transition-colors"
                  >
                    <div className="text-2xl mb-1">{mode.icon}</div>
                    <div className="text-xs text-white">{mode.name}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* Recent Assets Card */}
            <div className="bg-slate-800 rounded-lg p-6">
              <h3 className="text-lg font-semibold mb-4 flex items-center">
                <span className="mr-2">📦</span>
                Recent Assets
              </h3>
              <div className="space-y-2 max-h-48 overflow-y-auto">
                {recentAssets.length > 0 ? (
                  recentAssets.slice(0, 5).map(asset => (
                    <div key={asset.id} className="flex items-center justify-between p-2 bg-slate-700 rounded">
                      <div className="flex items-center space-x-2">
                        <span className="text-lg">🎲</span>
                        <div>
                          <div className="text-white text-sm font-medium truncate max-w-32">
                            {asset.name || 'Untitled Asset'}
                          </div>
                          <div className="text-slate-400 text-xs">
                            {asset.type || 'Unknown'} • {new Date(asset.created_at).toLocaleDateString()}
                          </div>
                        </div>
                      </div>
                      <button
                        onClick={() => setSelectedTab('assets')}
                        className="text-blue-400 hover:text-blue-300 text-xs"
                      >
                        View
                      </button>
                    </div>
                  ))
                ) : (
                  <div className="text-center text-slate-500 py-4">
                    <p className="text-sm">No recent assets</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {selectedTab === 'generation' && (
          <div className="flex h-full">
            {/* Left Panel - Generation Controls */}
            <div className="w-96 bg-slate-800 border-r border-slate-700 flex flex-col">
              <div className="p-4 border-b border-slate-700">
                <h3 className="text-sm font-semibold mb-3 text-slate-300">Generation Mode</h3>
                <div className="grid grid-cols-1 gap-2">
                  {generationModes.map(mode => (
                    <button
                      key={mode.id}
                      onClick={() => setGenerationMode(mode.id)}
                      className={`p-3 rounded-lg border text-left transition-all ${
                        generationMode === mode.id
                          ? 'border-blue-500 bg-blue-500/20'
                          : 'border-slate-600 hover:border-slate-500 bg-slate-700'
                      }`}
                    >
                      <div className="flex items-center space-x-2">
                        <span className="text-xl">{mode.icon}</span>
                        <div>
                          <div className="text-white font-medium text-sm">{mode.name}</div>
                          <div className="text-slate-400 text-xs">{mode.description}</div>
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              </div>

              <div className="p-4 flex-1 overflow-y-auto">
                <h3 className="text-sm font-semibold mb-3 text-slate-300">Parameters</h3>
                <div className="space-y-4">
                  {generationModes
                    .find(m => m.id === generationMode)
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
                  onClick={executeGeneration}
                  className="w-full mt-6 py-3 px-4 rounded font-medium bg-blue-600 hover:bg-blue-700 transition-colors"
                >
                  Generate 3D Asset
                </button>
              </div>
            </div>

            {/* Right Panel - Preview and Results */}
            <div className="flex-1 flex flex-col">
              <div className="p-4 border-b border-slate-700">
                <h3 className="text-sm font-semibold text-slate-300">Preview</h3>
              </div>
              <div className="flex-1 p-4">
                <div className="bg-slate-800 rounded-lg h-full flex items-center justify-center">
                  <div className="text-center">
                    <div className="text-6xl mb-4">🌐</div>
                    <p className="text-slate-400">Configure parameters and click Generate to create a 3D asset</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {selectedTab === 'projects' && (
          <div className="p-6">
            <TRELLISProjectManager trellisService={trellisService} />
          </div>
        )}

        {selectedTab === 'assets' && (
          <div className="p-6">
            <TRELLISAssetViewer
              assets={recentAssets}
              onAssetSelect={(asset) => console.log('Selected asset:', asset)}
              onDelete={(assetId) => console.log('Delete asset:', assetId)}
              onRefresh={async () => {
                const assets = await trellisService.getAssets({ limit: 10, sort: 'created_at', order: 'desc' });
                setRecentAssets(assets.assets || []);
              }}
            />
          </div>
        )}

        {selectedTab === 'queue' && (
          <div className="p-6">
            <h3 className="text-lg font-semibold mb-6">Generation Queue</h3>

            <div className="space-y-3">
              {jobQueue.length > 0 ? (
                jobQueue.map(job => (
                  <div key={job.id} className="bg-slate-800 rounded-lg p-4 border border-slate-700">
                    <div className="flex justify-between items-center mb-2">
                      <div className="flex items-center space-x-3">
                        <span className="text-xl">
                          {generationModes.find(m => m.id === job.type)?.icon || '⚙️'}
                        </span>
                        <div>
                          <h4 className="font-medium text-white">{job.type}</h4>
                          <p className="text-slate-400 text-xs">
                            {new Date(job.created_at).toLocaleString()}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span className={`px-2 py-1 rounded text-xs ${
                          job.status === 'completed' ? 'bg-green-600' :
                          job.status === 'running' ? 'bg-yellow-600' :
                          job.status === 'failed' ? 'bg-red-600' : 'bg-blue-600'
                        }`}>
                          {job.status}
                        </span>
                        {job.status === 'running' && (
                          <button className="text-red-400 hover:text-red-300 text-xs">
                            Cancel
                          </button>
                        )}
                      </div>
                    </div>

                    {job.progress !== undefined && (
                      <div className="mt-2">
                        <div className="flex justify-between text-xs text-slate-400 mb-1">
                          <span>Progress</span>
                          <span>{Math.round(job.progress * 100)}%</span>
                        </div>
                        <div className="w-full bg-slate-700 rounded-full h-2">
                          <div
                            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                            style={{ width: `${job.progress * 100}%` }}
                          />
                        </div>
                      </div>
                    )}
                  </div>
                ))
              ) : (
                <div className="text-center py-12">
                  <div className="text-6xl mb-4">⏳</div>
                  <p className="text-slate-400">Queue is empty</p>
                  <p className="text-slate-500 text-sm mt-1">Generate 3D assets to see them in the queue</p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Configuration Modal */}
      <AnimatePresence>
        {showConfigModal && (
          <TRELLISConfig
            onClose={() => setShowConfigModal(false)}
            onSave={(newConfig) => {
              console.log('Configuration saved:', newConfig);
              setConfig(prev => ({ ...prev, ...newConfig }));
            }}
          />
        )}
      </AnimatePresence>
    </div>
  );
};

export default TRELLISApp;