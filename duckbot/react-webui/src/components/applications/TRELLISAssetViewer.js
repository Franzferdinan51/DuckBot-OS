import React, { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import TRELLISService from '../../services/trellisService';

const AssetPreview = ({ asset, onClose, onDownload, onEdit }) => {
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [viewMode, setViewMode] = useState('3d');
  const [modelUrl, setModelUrl] = useState(null);
  const canvasRef = useRef(null);
  const animationRef = useRef(null);

  useEffect(() => {
    if (asset && asset.preview_url) {
      setModelUrl(asset.preview_url);
    } else if (asset && asset.file_url) {
      setModelUrl(asset.file_url);
    }
  }, [asset]);

  useEffect(() => {
    if (!modelUrl || !canvasRef.current || viewMode !== '3d') return;

    const loadModel = async () => {
      try {
        setIsLoading(true);
        setError(null);

        const THREE = await import('three');
        const { OrbitControls } = await import('three/examples/jsm/controls/OrbitControls');
        const { GLTFLoader } = await import('three/examples/jsm/loaders/GLTFLoader');

        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0x1a1a1a);

        const camera = new THREE.PerspectiveCamera(
          75,
          canvasRef.current.clientWidth / canvasRef.current.clientHeight,
          0.1,
          1000
        );

        const renderer = new THREE.WebGLRenderer({
          canvas: canvasRef.current,
          antialias: true,
          alpha: true
        });
        renderer.setSize(canvasRef.current.clientWidth, canvasRef.current.clientHeight);
        renderer.shadowMap.enabled = true;
        renderer.shadowMap.type = THREE.PCFSoftShadowMap;

        // Enhanced lighting setup
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
        scene.add(ambientLight);

        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
        directionalLight.position.set(10, 10, 5);
        directionalLight.castShadow = true;
        directionalLight.shadow.camera.near = 0.1;
        directionalLight.shadow.camera.far = 50;
        directionalLight.shadow.camera.left = -10;
        directionalLight.shadow.camera.right = 10;
        directionalLight.shadow.camera.top = 10;
        directionalLight.shadow.camera.bottom = -10;
        scene.add(directionalLight);

        const fillLight = new THREE.DirectionalLight(0x4169e1, 0.3);
        fillLight.position.set(-10, 5, -5);
        scene.add(fillLight);

        // Add grid
        const gridHelper = new THREE.GridHelper(20, 20, 0x444444, 0x222222);
        scene.add(gridHelper);

        // Load model
        const loader = new GLTFLoader();
        const gltf = await loader.loadAsync(modelUrl);

        // Add model to scene
        const model = gltf.scene;
        scene.add(model);

        // Setup model properties
        model.traverse((child) => {
          if (child.isMesh) {
            child.castShadow = true;
            child.receiveShadow = true;

            // Enhanced materials
            if (child.material) {
              child.material.envMapIntensity = 1;
              if (child.material.roughness !== undefined) {
                child.material.roughness = Math.max(0.1, child.material.roughness);
              }
              if (child.material.metalness !== undefined) {
                child.material.metalness = Math.max(0.1, child.material.metalness);
              }
            }
          }
        });

        // Center and scale model
        const box = new THREE.Box3().setFromObject(model);
        const center = box.getCenter(new THREE.Vector3());
        const size = box.getSize(new THREE.Vector3());
        const maxDim = Math.max(size.x, size.y, size.z);
        const scale = 4 / maxDim;

        model.position.sub(center);
        model.scale.multiplyScalar(scale);

        camera.position.set(5, 3, 5);
        camera.lookAt(0, 0, 0);

        // Setup controls
        const controls = new OrbitControls(camera, renderer.domElement);
        controls.enableDamping = true;
        controls.dampingFactor = 0.05;
        controls.screenSpacePanning = false;
        controls.minDistance = 2;
        controls.maxDistance = 20;
        controls.maxPolarAngle = Math.PI / 2;

        // Animation loop
        const animate = () => {
          animationRef.current = requestAnimationFrame(animate);

          // Gentle rotation
          if (model) {
            model.rotation.y += 0.005;
          }

          controls.update();
          renderer.render(scene, camera);
        };

        animate();
        setIsLoading(false);

        // Handle resize
        const handleResize = () => {
          if (!canvasRef.current) return;
          camera.aspect = canvasRef.current.clientWidth / canvasRef.current.clientHeight;
          camera.updateProjectionMatrix();
          renderer.setSize(canvasRef.current.clientWidth, canvasRef.current.clientHeight);
        };

        window.addEventListener('resize', handleResize);

        return () => {
          window.removeEventListener('resize', handleResize);
          if (animationRef.current) {
            cancelAnimationFrame(animationRef.current);
          }
          if (renderer) {
            renderer.dispose();
          }
        };
      } catch (err) {
        console.error('Failed to load 3D model:', err);
        setError('Failed to load 3D model');
        setIsLoading(false);
      }
    };

    loadModel();
  }, [modelUrl, viewMode]);

  const handleDownload = useCallback(async (format) => {
    if (onDownload) {
      await onDownload(asset.id, format);
    }
  }, [asset, onDownload]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-90">
      <div className="bg-slate-900 rounded-lg w-full max-w-6xl h-full max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 bg-slate-800 border-b border-slate-700">
          <div className="flex items-center space-x-3">
            <h3 className="text-xl font-semibold text-white">
              {asset?.name || 'Asset Preview'}
            </h3>
            <div className="flex space-x-2">
              <button
                onClick={() => setViewMode('3d')}
                className={`px-3 py-1 rounded text-sm ${
                  viewMode === '3d' ? 'bg-blue-600' : 'bg-slate-600 hover:bg-slate-500'
                }`}
              >
                3D View
              </button>
              <button
                onClick={() => setViewMode('info')}
                className={`px-3 py-1 rounded text-sm ${
                  viewMode === 'info' ? 'bg-blue-600' : 'bg-slate-600 hover:bg-slate-500'
                }`}
              >
                Info
              </button>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 flex overflow-hidden">
          {viewMode === '3d' && (
            <div className="flex-1 relative">
              <canvas
                ref={canvasRef}
                className="w-full h-full"
              />
              {isLoading && (
                <div className="absolute inset-0 flex items-center justify-center bg-slate-900/80">
                  <div className="text-center">
                    <div className="animate-spin w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full mx-auto mb-4"></div>
                    <p className="text-white text-lg">Loading 3D model...</p>
                  </div>
                </div>
              )}
              {error && (
                <div className="absolute inset-0 flex items-center justify-center bg-slate-900/80">
                  <div className="text-center text-red-400">
                    <p className="text-lg">{error}</p>
                  </div>
                </div>
              )}
            </div>
          )}

          {viewMode === 'info' && (
            <div className="flex-1 p-6 overflow-y-auto">
              <div className="space-y-6">
                {/* Asset Details */}
                <div>
                  <h4 className="text-lg font-semibold text-white mb-3">Asset Information</h4>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <span className="text-slate-400 text-sm">Name:</span>
                      <p className="text-white">{asset?.name || 'Untitled'}</p>
                    </div>
                    <div>
                      <span className="text-slate-400 text-sm">Type:</span>
                      <p className="text-white">{asset?.type || 'Unknown'}</p>
                    </div>
                    <div>
                      <span className="text-slate-400 text-sm">Format:</span>
                      <p className="text-white">{asset?.format || 'Unknown'}</p>
                    </div>
                    <div>
                      <span className="text-slate-400 text-sm">Size:</span>
                      <p className="text-white">
                        {asset?.file_size ? `${(asset.file_size / 1024 / 1024).toFixed(2)} MB` : 'Unknown'}
                      </p>
                    </div>
                    <div>
                      <span className="text-slate-400 text-sm">Created:</span>
                      <p className="text-white">
                        {asset?.created_at ? new Date(asset.created_at).toLocaleString() : 'Unknown'}
                      </p>
                    </div>
                    <div>
                      <span className="text-slate-400 text-sm">Modified:</span>
                      <p className="text-white">
                        {asset?.updated_at ? new Date(asset.updated_at).toLocaleString() : 'Unknown'}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Generation Parameters */}
                {asset?.generation_params && (
                  <div>
                    <h4 className="text-lg font-semibold text-white mb-3">Generation Parameters</h4>
                    <div className="bg-slate-800 rounded-lg p-4">
                      <pre className="text-slate-300 text-sm overflow-x-auto">
                        {JSON.stringify(asset.generation_params, null, 2)}
                      </pre>
                    </div>
                  </div>
                )}

                {/* Tags and Categories */}
                <div>
                  <h4 className="text-lg font-semibold text-white mb-3">Tags</h4>
                  <div className="flex flex-wrap gap-2">
                    {asset?.tags?.map((tag, index) => (
                      <span
                        key={index}
                        className="px-3 py-1 bg-blue-600 text-white text-sm rounded-full"
                      >
                        {tag}
                      </span>
                    ))}
                    {(!asset?.tags || asset.tags.length === 0) && (
                      <p className="text-slate-400 text-sm">No tags assigned</p>
                    )}
                  </div>
                </div>

                {/* Description */}
                {asset?.description && (
                  <div>
                    <h4 className="text-lg font-semibold text-white mb-3">Description</h4>
                    <p className="text-slate-300">{asset.description}</p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Actions Panel */}
          <div className="w-80 bg-slate-800 border-l border-slate-700 p-4 flex flex-col">
            <h4 className="text-lg font-semibold text-white mb-4">Actions</h4>

            <div className="space-y-3 flex-1">
              <button
                onClick={() => onEdit?.(asset)}
                className="w-full p-3 bg-blue-600 hover:bg-blue-700 rounded-lg text-white font-medium transition-colors"
              >
                Edit Asset
              </button>

              <div>
                <h5 className="text-sm font-medium text-slate-300 mb-2">Download As</h5>
                <div className="grid grid-cols-2 gap-2">
                  {['glb', 'gltf', 'obj', 'stl', 'ply'].map(format => (
                    <button
                      key={format}
                      onClick={() => handleDownload(format)}
                      className="p-2 bg-slate-700 hover:bg-slate-600 rounded text-sm text-white transition-colors"
                    >
                      {format.toUpperCase()}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <h5 className="text-sm font-medium text-slate-300 mb-2">Quick Actions</h5>
                <div className="space-y-2">
                  <button className="w-full p-2 bg-slate-700 hover:bg-slate-600 rounded text-sm text-white text-left transition-colors">
                    📋 Copy to Clipboard
                  </button>
                  <button className="w-full p-2 bg-slate-700 hover:bg-slate-600 rounded text-sm text-white text-left transition-colors">
                    🔗 Share Asset
                  </button>
                  <button className="w-full p-2 bg-slate-700 hover:bg-slate-600 rounded text-sm text-white text-left transition-colors">
                    📊 View Analytics
                  </button>
                </div>
              </div>
            </div>

            <div className="pt-4 border-t border-slate-700">
              <p className="text-xs text-slate-400">
                Asset ID: {asset?.id || 'Unknown'}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

const TRELLISAssetViewer = ({ assets, onAssetSelect, onDelete, onRefresh }) => {
  const [selectedAsset, setSelectedAsset] = useState(null);
  const [viewMode, setViewMode] = useState('grid');
  const [sortBy, setSortBy] = useState('created_at');
  const [sortOrder, setSortOrder] = useState('desc');
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('all');

  const filteredAndSortedAssets = React.useMemo(() => {
    let filtered = assets;

    // Apply search filter
    if (searchTerm) {
      filtered = filtered.filter(asset =>
        asset.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        asset.description?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        asset.tags?.some(tag => tag.toLowerCase().includes(searchTerm.toLowerCase()))
      );
    }

    // Apply type filter
    if (filterType !== 'all') {
      filtered = filtered.filter(asset => asset.type === filterType);
    }

    // Apply sorting
    filtered.sort((a, b) => {
      let aVal = a[sortBy] || '';
      let bVal = b[sortBy] || '';

      if (sortBy === 'created_at' || sortBy === 'updated_at') {
        aVal = new Date(aVal);
        bVal = new Date(bVal);
      } else if (sortBy === 'file_size') {
        aVal = parseFloat(aVal) || 0;
        bVal = parseFloat(bVal) || 0;
      }

      if (sortOrder === 'asc') {
        return aVal > bVal ? 1 : -1;
      } else {
        return aVal < bVal ? 1 : -1;
      }
    });

    return filtered;
  }, [assets, searchTerm, filterType, sortBy, sortOrder]);

  const handleDownload = useCallback(async (assetId, format) => {
    try {
      // This would be implemented with the actual TRELLIS service
      console.log(`Downloading asset ${assetId} as ${format}`);
      alert(`Asset ${assetId} downloaded as ${format.toUpperCase()}`);
    } catch (error) {
      console.error('Download failed:', error);
      alert('Download failed: ' + error.message);
    }
  }, []);

  return (
    <div className="space-y-4">
      {/* Controls */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <div className="relative">
            <input
              type="text"
              placeholder="Search assets..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 pr-4 py-2 bg-slate-700 text-white rounded-lg border border-slate-600 focus:border-blue-500 focus:outline-none w-64"
            />
            <svg className="absolute left-3 top-2.5 w-5 h-5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>

          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="px-3 py-2 bg-slate-700 text-white rounded-lg border border-slate-600 focus:border-blue-500 focus:outline-none"
          >
            <option value="all">All Types</option>
            <option value="generated">Generated</option>
            <option value="imported">Imported</option>
            <option value="processed">Processed</option>
          </select>

          <select
            value={`${sortBy}-${sortOrder}`}
            onChange={(e) => {
              const [field, order] = e.target.value.split('-');
              setSortBy(field);
              setSortOrder(order);
            }}
            className="px-3 py-2 bg-slate-700 text-white rounded-lg border border-slate-600 focus:border-blue-500 focus:outline-none"
          >
            <option value="created_at-desc">Newest First</option>
            <option value="created_at-asc">Oldest First</option>
            <option value="name-asc">Name (A-Z)</option>
            <option value="name-desc">Name (Z-A)</option>
            <option value="file_size-desc">Size (Large to Small)</option>
            <option value="file_size-asc">Size (Small to Large)</option>
          </select>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => setViewMode('grid')}
            className={`p-2 rounded ${
              viewMode === 'grid' ? 'bg-blue-600' : 'bg-slate-700 hover:bg-slate-600'
            }`}
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
            </svg>
          </button>
          <button
            onClick={() => setViewMode('list')}
            className={`p-2 rounded ${
              viewMode === 'list' ? 'bg-blue-600' : 'bg-slate-700 hover:bg-slate-600'
            }`}
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
          <button
            onClick={onRefresh}
            className="px-3 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg text-white transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </button>
        </div>
      </div>

      {/* Assets Display */}
      {filteredAndSortedAssets.length > 0 ? (
        viewMode === 'grid' ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {filteredAndSortedAssets.map(asset => (
              <motion.div
                key={asset.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-slate-800 rounded-lg p-4 border border-slate-700 hover:border-slate-600 transition-colors cursor-pointer"
                onClick={() => setSelectedAsset(asset)}
              >
                <div className="aspect-square bg-slate-700 rounded-lg mb-3 flex items-center justify-center">
                  {asset.preview_url ? (
                    <img
                      src={asset.preview_url}
                      alt={asset.name}
                      className="w-full h-full object-cover rounded-lg"
                    />
                  ) : (
                    <span className="text-4xl">🎲</span>
                  )}
                </div>
                <h4 className="font-medium text-white text-sm truncate mb-1">
                  {asset.name || 'Untitled Asset'}
                </h4>
                <p className="text-slate-400 text-xs mb-2">
                  {asset.type || 'Unknown'} • {asset.format || 'glb'}
                </p>
                <div className="flex justify-between items-center">
                  <span className="text-xs text-slate-500">
                    {asset.file_size ? `${(asset.file_size / 1024 / 1024).toFixed(1)} MB` : 'Unknown'}
                  </span>
                  <div className="flex space-x-1">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelectedAsset(asset);
                      }}
                      className="text-blue-400 hover:text-blue-300 text-xs"
                    >
                      View
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onDelete?.(asset.id);
                      }}
                      className="text-red-400 hover:text-red-300 text-xs"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        ) : (
          <div className="bg-slate-800 rounded-lg border border-slate-700 overflow-hidden">
            <table className="w-full">
              <thead className="bg-slate-700">
                <tr>
                  <th className="text-left p-3 text-sm font-medium text-white">Name</th>
                  <th className="text-left p-3 text-sm font-medium text-white">Type</th>
                  <th className="text-left p-3 text-sm font-medium text-white">Format</th>
                  <th className="text-left p-3 text-sm font-medium text-white">Size</th>
                  <th className="text-left p-3 text-sm font-medium text-white">Created</th>
                  <th className="text-left p-3 text-sm font-medium text-white">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredAndSortedAssets.map(asset => (
                  <tr key={asset.id} className="border-t border-slate-700 hover:bg-slate-750">
                    <td className="p-3">
                      <div className="text-white text-sm font-medium">{asset.name || 'Untitled'}</div>
                      <div className="text-slate-400 text-xs">{asset.description || 'No description'}</div>
                    </td>
                    <td className="p-3">
                      <span className="text-white text-sm">{asset.type || 'Unknown'}</span>
                    </td>
                    <td className="p-3">
                      <span className="text-white text-sm uppercase">{asset.format || 'glb'}</span>
                    </td>
                    <td className="p-3">
                      <span className="text-white text-sm">
                        {asset.file_size ? `${(asset.file_size / 1024 / 1024).toFixed(1)} MB` : 'Unknown'}
                      </span>
                    </td>
                    <td className="p-3">
                      <span className="text-white text-sm">
                        {asset.created_at ? new Date(asset.created_at).toLocaleDateString() : 'Unknown'}
                      </span>
                    </td>
                    <td className="p-3">
                      <div className="flex space-x-2">
                        <button
                          onClick={() => setSelectedAsset(asset)}
                          className="text-blue-400 hover:text-blue-300 text-sm"
                        >
                          View
                        </button>
                        <button
                          onClick={() => onDelete?.(asset.id)}
                          className="text-red-400 hover:text-red-300 text-sm"
                        >
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )
      ) : (
        <div className="text-center py-12">
          <div className="text-6xl mb-4">📦</div>
          <p className="text-slate-400 text-lg">No assets found</p>
          <p className="text-slate-500 text-sm mt-1">
            {searchTerm || filterType !== 'all'
              ? 'Try adjusting your search or filters'
              : 'Generate or import your first 3D asset to get started'
            }
          </p>
        </div>
      )}
    </div>
  );
};

export { TRELLISAssetViewer, AssetPreview };