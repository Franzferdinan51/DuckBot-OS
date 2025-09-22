import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import TRELLISService from '../../services/trellisService';

const ProjectCreationModal = ({ onClose, onSave }) => {
  const [projectData, setProjectData] = useState({
    name: '',
    description: '',
    type: 'general',
    tags: [],
    settings: {
      quality: 'medium',
      resolution: 512,
      enableGPU: true
    }
  });

  const [tagInput, setTagInput] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const projectTypes = [
    { id: 'general', name: 'General', icon: '📁', description: 'General 3D project' },
    { id: 'characters', name: 'Characters', icon: '👤', description: 'Character design and modeling' },
    { id: 'environments', name: 'Environments', icon: '🌍', description: 'Environmental scenes and landscapes' },
    { id: 'props', name: 'Props', icon: '🎭', description: 'Props and objects' },
    { id: 'architecture', name: 'Architecture', icon: '🏛️', description: 'Buildings and structures' },
    { id: 'vehicles', name: 'Vehicles', icon: '🚗', description: 'Cars, aircraft, and machinery' }
  ];

  const handleAddTag = () => {
    if (tagInput.trim() && !projectData.tags.includes(tagInput.trim())) {
      setProjectData(prev => ({
        ...prev,
        tags: [...prev.tags, tagInput.trim()]
      }));
      setTagInput('');
    }
  };

  const handleRemoveTag = (tagToRemove) => {
    setProjectData(prev => ({
      ...prev,
      tags: prev.tags.filter(tag => tag !== tagToRemove)
    }));
  };

  const handleSubmit = async () => {
    if (!projectData.name.trim()) {
      alert('Project name is required');
      return;
    }

    setIsSubmitting(true);
    try {
      await onSave(projectData);
      onClose();
    } catch (error) {
      console.error('Failed to create project:', error);
      alert('Failed to create project: ' + error.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-75">
      <div className="bg-slate-900 rounded-lg w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-slate-700">
          <h3 className="text-xl font-semibold text-white">Create New Project</h3>
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
        <div className="p-6 space-y-6">
          {/* Basic Info */}
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Project Name *
            </label>
            <input
              type="text"
              value={projectData.name}
              onChange={(e) => setProjectData(prev => ({ ...prev, name: e.target.value }))}
              className="w-full p-3 bg-slate-800 text-white rounded-lg border border-slate-600 focus:border-blue-500 focus:outline-none"
              placeholder="Enter project name..."
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Description
            </label>
            <textarea
              value={projectData.description}
              onChange={(e) => setProjectData(prev => ({ ...prev, description: e.target.value }))}
              rows={3}
              className="w-full p-3 bg-slate-800 text-white rounded-lg border border-slate-600 focus:border-blue-500 focus:outline-none"
              placeholder="Describe your project..."
            />
          </div>

          {/* Project Type */}
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-3">
              Project Type
            </label>
            <div className="grid grid-cols-2 gap-3">
              {projectTypes.map(type => (
                <button
                  key={type.id}
                  onClick={() => setProjectData(prev => ({ ...prev, type: type.id }))}
                  className={`p-4 rounded-lg border text-left transition-all ${
                    projectData.type === type.id
                      ? 'border-blue-500 bg-blue-500/20'
                      : 'border-slate-600 hover:border-slate-500 bg-slate-800'
                  }`}
                >
                  <div className="flex items-center space-x-3">
                    <span className="text-2xl">{type.icon}</span>
                    <div>
                      <div className="text-white font-medium">{type.name}</div>
                      <div className="text-slate-400 text-xs">{type.description}</div>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Tags */}
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Tags
            </label>
            <div className="flex space-x-2 mb-2">
              <input
                type="text"
                value={tagInput}
                onChange={(e) => setTagInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleAddTag()}
                className="flex-1 p-2 bg-slate-800 text-white rounded-lg border border-slate-600 focus:border-blue-500 focus:outline-none"
                placeholder="Add tags..."
              />
              <button
                onClick={handleAddTag}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-white"
              >
                Add
              </button>
            </div>
            <div className="flex flex-wrap gap-2">
              {projectData.tags.map(tag => (
                <span
                  key={tag}
                  className="px-3 py-1 bg-blue-600 text-white text-sm rounded-full flex items-center space-x-1"
                >
                  <span>{tag}</span>
                  <button
                    onClick={() => handleRemoveTag(tag)}
                    className="text-blue-200 hover:text-white"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </span>
              ))}
            </div>
          </div>

          {/* Default Settings */}
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-3">
              Default Generation Settings
            </label>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs text-slate-400 mb-1">Quality</label>
                <select
                  value={projectData.settings.quality}
                  onChange={(e) => setProjectData(prev => ({
                    ...prev,
                    settings: { ...prev.settings, quality: e.target.value }
                  }))}
                  className="w-full p-2 bg-slate-800 text-white rounded border border-slate-600 focus:border-blue-500 focus:outline-none"
                >
                  <option value="draft">Draft</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                  <option value="ultra">Ultra</option>
                </select>
              </div>
              <div>
                <label className="block text-xs text-slate-400 mb-1">Resolution</label>
                <select
                  value={projectData.settings.resolution}
                  onChange={(e) => setProjectData(prev => ({
                    ...prev,
                    settings: { ...prev.settings, resolution: parseInt(e.target.value) }
                  }))}
                  className="w-full p-2 bg-slate-800 text-white rounded border border-slate-600 focus:border-blue-500 focus:outline-none"
                >
                  <option value={256}>256x256</option>
                  <option value={512}>512x512</option>
                  <option value={768}>768x768</option>
                  <option value={1024}>1024x1024</option>
                </select>
              </div>
            </div>
            <div className="mt-3">
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={projectData.settings.enableGPU}
                  onChange={(e) => setProjectData(prev => ({
                    ...prev,
                    settings: { ...prev.settings, enableGPU: e.target.checked }
                  }))}
                  className="rounded"
                />
                <span className="text-sm text-white">Enable GPU acceleration</span>
              </label>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex justify-end space-x-3 p-6 border-t border-slate-700">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg text-gray-300 hover:text-white"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={isSubmitting || !projectData.name.trim()}
            className={`px-6 py-2 rounded-lg font-medium ${
              isSubmitting || !projectData.name.trim()
                ? 'bg-gray-600 cursor-not-allowed'
                : 'bg-blue-600 hover:bg-blue-700'
            }`}
          >
            {isSubmitting ? 'Creating...' : 'Create Project'}
          </button>
        </div>
      </div>
    </div>
  );
};

const ProjectDetail = ({ project, onClose, onUpdate, onDelete, trellisService }) => {
  const [activeTab, setActiveTab] = useState('overview');
  const [projectAssets, setProjectAssets] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isEditing, setIsEditing] = useState(false);
  const [editData, setEditData] = useState({});

  useEffect(() => {
    if (project) {
      setEditData({
        name: project.name,
        description: project.description,
        tags: project.tags || []
      });
      loadProjectAssets();
    }
  }, [project]);

  const loadProjectAssets = async () => {
    if (!project) return;

    setIsLoading(true);
    try {
      const response = await trellisService.getAssets({ project_id: project.id });
      setProjectAssets(response.assets || []);
    } catch (error) {
      console.error('Failed to load project assets:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSaveEdit = async () => {
    try {
      await onUpdate(project.id, editData);
      setIsEditing(false);
    } catch (error) {
      console.error('Failed to update project:', error);
      alert('Failed to update project: ' + error.message);
    }
  };

  const handleDeleteProject = async () => {
    if (confirm('Are you sure you want to delete this project? This action cannot be undone.')) {
      try {
        await onDelete(project.id);
        onClose();
      } catch (error) {
        console.error('Failed to delete project:', error);
        alert('Failed to delete project: ' + error.message);
      }
    }
  };

  const stats = {
    totalAssets: projectAssets.length,
    totalSize: projectAssets.reduce((sum, asset) => sum + (asset.file_size || 0), 0),
    lastUpdated: project.updated_at ? new Date(project.updated_at) : null,
    types: projectAssets.reduce((acc, asset) => {
      acc[asset.type] = (acc[asset.type] || 0) + 1;
      return acc;
    }, {})
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-75">
      <div className="bg-slate-900 rounded-lg w-full max-w-6xl h-full max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 bg-slate-800 border-b border-slate-700">
          <div className="flex items-center space-x-3">
            {isEditing ? (
              <input
                type="text"
                value={editData.name}
                onChange={(e) => setEditData(prev => ({ ...prev, name: e.target.value }))}
                className="text-xl font-semibold bg-slate-700 text-white rounded px-3 py-1 border border-slate-600"
              />
            ) : (
              <h3 className="text-xl font-semibold text-white">{project.name}</h3>
            )}
            <div className="flex space-x-2">
              {project.type && (
                <span className="px-2 py-1 bg-slate-700 text-white text-xs rounded-full">
                  {project.type}
                </span>
              )}
            </div>
          </div>
          <div className="flex items-center space-x-2">
            {isEditing ? (
              <>
                <button
                  onClick={() => setIsEditing(false)}
                  className="px-3 py-1 bg-gray-600 hover:bg-gray-700 rounded text-sm"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSaveEdit}
                  className="px-3 py-1 bg-blue-600 hover:bg-blue-700 rounded text-sm"
                >
                  Save
                </button>
              </>
            ) : (
              <>
                <button
                  onClick={() => setIsEditing(true)}
                  className="px-3 py-1 bg-slate-600 hover:bg-slate-500 rounded text-sm"
                >
                  Edit
                </button>
                <button
                  onClick={handleDeleteProject}
                  className="px-3 py-1 bg-red-600 hover:bg-red-700 rounded text-sm"
                >
                  Delete
                </button>
                <button
                  onClick={onClose}
                  className="text-gray-400 hover:text-white"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </>
            )}
          </div>
        </div>

        {/* Tabs */}
        <div className="flex bg-slate-800 border-b border-slate-700">
          {['overview', 'assets', 'timeline', 'settings'].map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-2 text-sm font-medium transition-colors ${
                activeTab === tab
                  ? 'bg-blue-600 text-white'
                  : 'text-slate-300 hover:bg-slate-700 hover:text-white'
              }`}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {activeTab === 'overview' && (
            <div className="space-y-6">
              {/* Description */}
              <div>
                <h4 className="text-lg font-semibold text-white mb-3">Description</h4>
                {isEditing ? (
                  <textarea
                    value={editData.description}
                    onChange={(e) => setEditData(prev => ({ ...prev, description: e.target.value }))}
                    rows={4}
                    className="w-full p-3 bg-slate-800 text-white rounded-lg border border-slate-600 focus:border-blue-500 focus:outline-none"
                  />
                ) : (
                  <p className="text-slate-300">{project.description || 'No description provided'}</p>
                )}
              </div>

              {/* Stats */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="bg-slate-800 rounded-lg p-4">
                  <div className="text-2xl font-bold text-blue-400">{stats.totalAssets}</div>
                  <div className="text-slate-400 text-sm">Total Assets</div>
                </div>
                <div className="bg-slate-800 rounded-lg p-4">
                  <div className="text-2xl font-bold text-green-400">
                    {(stats.totalSize / 1024 / 1024).toFixed(1)} MB
                  </div>
                  <div className="text-slate-400 text-sm">Total Size</div>
                </div>
                <div className="bg-slate-800 rounded-lg p-4">
                  <div className="text-2xl font-bold text-purple-400">
                    {Object.keys(stats.types).length}
                  </div>
                  <div className="text-slate-400 text-sm">Asset Types</div>
                </div>
                <div className="bg-slate-800 rounded-lg p-4">
                  <div className="text-2xl font-bold text-orange-400">
                    {stats.lastUpdated ? stats.lastUpdated.toLocaleDateString() : 'N/A'}
                  </div>
                  <div className="text-slate-400 text-sm">Last Updated</div>
                </div>
              </div>

              {/* Asset Type Distribution */}
              {Object.keys(stats.types).length > 0 && (
                <div>
                  <h4 className="text-lg font-semibold text-white mb-3">Asset Distribution</h4>
                  <div className="bg-slate-800 rounded-lg p-4">
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      {Object.entries(stats.types).map(([type, count]) => (
                        <div key={type} className="text-center">
                          <div className="text-xl font-bold text-white">{count}</div>
                          <div className="text-slate-400 text-sm capitalize">{type}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* Tags */}
              <div>
                <h4 className="text-lg font-semibold text-white mb-3">Tags</h4>
                <div className="flex flex-wrap gap-2">
                  {(project.tags || []).map(tag => (
                    <span
                      key={tag}
                      className="px-3 py-1 bg-blue-600 text-white text-sm rounded-full"
                    >
                      {tag}
                    </span>
                  ))}
                  {(!project.tags || project.tags.length === 0) && (
                    <p className="text-slate-400 text-sm">No tags assigned</p>
                  )}
                </div>
              </div>
            </div>
          )}

          {activeTab === 'assets' && (
            <div>
              <div className="flex justify-between items-center mb-4">
                <h4 className="text-lg font-semibold text-white">Project Assets</h4>
                <button className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm">
                  Add Asset
                </button>
              </div>

              {isLoading ? (
                <div className="text-center py-12">
                  <div className="animate-spin w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full mx-auto mb-4"></div>
                  <p className="text-slate-400">Loading assets...</p>
                </div>
              ) : projectAssets.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {projectAssets.map(asset => (
                    <div key={asset.id} className="bg-slate-800 rounded-lg p-4 border border-slate-700">
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
                      <h5 className="font-medium text-white text-sm truncate mb-1">
                        {asset.name || 'Untitled Asset'}
                      </h5>
                      <p className="text-slate-400 text-xs mb-2">
                        {asset.type} • {asset.format}
                      </p>
                      <div className="flex justify-between items-center">
                        <span className="text-xs text-slate-500">
                          {asset.file_size ? `${(asset.file_size / 1024 / 1024).toFixed(1)} MB` : 'Unknown'}
                        </span>
                        <button className="text-blue-400 hover:text-blue-300 text-xs">
                          View
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12">
                  <div className="text-6xl mb-4">📦</div>
                  <p className="text-slate-400 text-lg">No assets yet</p>
                  <p className="text-slate-500 text-sm mt-1">Generate or import assets to add them to this project</p>
                </div>
              )}
            </div>
          )}

          {activeTab === 'timeline' && (
            <div>
              <h4 className="text-lg font-semibold text-white mb-4">Project Timeline</h4>
              <div className="space-y-4">
                <div className="bg-slate-800 rounded-lg p-4 border-l-4 border-blue-500">
                  <div className="flex justify-between items-start mb-2">
                    <div>
                      <h5 className="font-medium text-white">Project Created</h5>
                      <p className="text-slate-400 text-sm">
                        {project.created_at ? new Date(project.created_at).toLocaleString() : 'Unknown'}
                      </p>
                    </div>
                  </div>
                </div>
                {projectAssets.slice(0, 10).map((asset, index) => (
                  <div key={asset.id} className="bg-slate-800 rounded-lg p-4 border-l-4 border-green-500">
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <h5 className="font-medium text-white">Asset Added: {asset.name}</h5>
                        <p className="text-slate-400 text-sm">
                          {asset.type} • {asset.format}
                        </p>
                      </div>
                      <span className="text-slate-500 text-sm">
                        {asset.created_at ? new Date(asset.created_at).toLocaleDateString() : 'Unknown'}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'settings' && (
            <div className="space-y-6">
              <div>
                <h4 className="text-lg font-semibold text-white mb-4">Project Settings</h4>
                <div className="bg-slate-800 rounded-lg p-4 space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">
                      Default Quality
                    </label>
                    <select
                      value={project.settings?.quality || 'medium'}
                      className="w-full p-2 bg-slate-700 text-white rounded border border-slate-600 focus:border-blue-500 focus:outline-none"
                    >
                      <option value="draft">Draft</option>
                      <option value="medium">Medium</option>
                      <option value="high">High</option>
                      <option value="ultra">Ultra</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">
                      Default Resolution
                    </label>
                    <select
                      value={project.settings?.resolution || 512}
                      className="w-full p-2 bg-slate-700 text-white rounded border border-slate-600 focus:border-blue-500 focus:outline-none"
                    >
                      <option value={256}>256x256</option>
                      <option value={512}>512x512</option>
                      <option value={768}>768x768</option>
                      <option value={1024}>1024x1024</option>
                    </select>
                  </div>
                  <div>
                    <label className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        checked={project.settings?.enableGPU !== false}
                        className="rounded"
                        readOnly
                      />
                      <span className="text-sm text-white">Enable GPU acceleration</span>
                    </label>
                  </div>
                </div>
              </div>

              <div>
                <h4 className="text-lg font-semibold text-white mb-4">Export Options</h4>
                <div className="bg-slate-800 rounded-lg p-4">
                  <button className="w-full p-3 bg-blue-600 hover:bg-blue-700 rounded-lg text-white font-medium">
                    Export Project Package
                  </button>
                  <p className="text-slate-400 text-xs mt-2">
                    Export all assets and project data as a compressed package
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const TRELLISProjectManager = ({ trellisService }) => {
  const [projects, setProjects] = useState([]);
  const [selectedProject, setSelectedProject] = useState(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [viewMode, setViewMode] = useState('grid');

  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    setIsLoading(true);
    try {
      const response = await trellisService.getProjects();
      setProjects(response.projects || []);
    } catch (error) {
      console.error('Failed to load projects:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateProject = async (projectData) => {
    try {
      const newProject = await trellisService.createProject(projectData);
      setProjects(prev => [newProject, ...prev]);
      setShowCreateModal(false);
    } catch (error) {
      console.error('Failed to create project:', error);
      throw error;
    }
  };

  const handleUpdateProject = async (projectId, updateData) => {
    try {
      // This would be implemented with actual update API
      setProjects(prev => prev.map(p =>
        p.id === projectId ? { ...p, ...updateData } : p
      ));
    } catch (error) {
      console.error('Failed to update project:', error);
      throw error;
    }
  };

  const handleDeleteProject = async (projectId) => {
    try {
      // This would be implemented with actual delete API
      setProjects(prev => prev.filter(p => p.id !== projectId));
    } catch (error) {
      console.error('Failed to delete project:', error);
      throw error;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-xl font-semibold text-white">3D Projects</h3>
        <div className="flex items-center space-x-3">
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
            onClick={() => setShowCreateModal(true)}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-white font-medium"
          >
            New Project
          </button>
        </div>
      </div>

      {/* Projects Display */}
      {isLoading ? (
        <div className="text-center py-12">
          <div className="animate-spin w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full mx-auto mb-4"></div>
          <p className="text-slate-400">Loading projects...</p>
        </div>
      ) : projects.length > 0 ? (
        viewMode === 'grid' ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {projects.map(project => (
              <motion.div
                key={project.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-slate-800 rounded-lg p-6 border border-slate-700 hover:border-slate-600 cursor-pointer transition-colors"
                onClick={() => setSelectedProject(project)}
              >
                <div className="flex items-center justify-between mb-4">
                  <div className="text-3xl">
                    {project.type === 'characters' ? '👤' :
                     project.type === 'environments' ? '🌍' :
                     project.type === 'props' ? '🎭' :
                     project.type === 'architecture' ? '🏛️' :
                     project.type === 'vehicles' ? '🚗' : '📁'}
                  </div>
                  <div className="text-slate-400 text-xs">
                    {project.asset_count || 0} assets
                  </div>
                </div>
                <h4 className="font-semibold text-white mb-2 truncate">
                  {project.name}
                </h4>
                <p className="text-slate-400 text-sm mb-3 line-clamp-2">
                  {project.description || 'No description'}
                </p>
                <div className="flex flex-wrap gap-1 mb-3">
                  {(project.tags || []).slice(0, 3).map(tag => (
                    <span key={tag} className="px-2 py-1 bg-slate-700 text-slate-300 text-xs rounded-full">
                      {tag}
                    </span>
                  ))}
                  {(project.tags || []).length > 3 && (
                    <span className="px-2 py-1 bg-slate-700 text-slate-400 text-xs rounded-full">
                      +{(project.tags || []).length - 3}
                    </span>
                  )}
                </div>
                <div className="flex justify-between items-center text-xs text-slate-500">
                  <span>
                    Updated {project.updated_at ? new Date(project.updated_at).toLocaleDateString() : 'Never'}
                  </span>
                  <span className="text-blue-400 hover:text-blue-300">
                    Open →
                  </span>
                </div>
              </motion.div>
            ))}
          </div>
        ) : (
          <div className="bg-slate-800 rounded-lg border border-slate-700 overflow-hidden">
            <table className="w-full">
              <thead className="bg-slate-700">
                <tr>
                  <th className="text-left p-4 text-sm font-medium text-white">Project</th>
                  <th className="text-left p-4 text-sm font-medium text-white">Type</th>
                  <th className="text-left p-4 text-sm font-medium text-white">Assets</th>
                  <th className="text-left p-4 text-sm font-medium text-white">Last Updated</th>
                  <th className="text-left p-4 text-sm font-medium text-white">Actions</th>
                </tr>
              </thead>
              <tbody>
                {projects.map(project => (
                  <tr key={project.id} className="border-t border-slate-700 hover:bg-slate-750">
                    <td className="p-4">
                      <div>
                        <div className="text-white font-medium">{project.name}</div>
                        <div className="text-slate-400 text-sm">{project.description || 'No description'}</div>
                      </div>
                    </td>
                    <td className="p-4">
                      <span className="text-white capitalize">{project.type || 'general'}</span>
                    </td>
                    <td className="p-4">
                      <span className="text-white">{project.asset_count || 0}</span>
                    </td>
                    <td className="p-4">
                      <span className="text-white">
                        {project.updated_at ? new Date(project.updated_at).toLocaleDateString() : 'Never'}
                      </span>
                    </td>
                    <td className="p-4">
                      <button
                        onClick={() => setSelectedProject(project)}
                        className="text-blue-400 hover:text-blue-300 text-sm"
                      >
                        Open
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )
      ) : (
        <div className="text-center py-12">
          <div className="text-6xl mb-4">📁</div>
          <p className="text-slate-400 text-lg">No projects yet</p>
          <p className="text-slate-500 text-sm mt-1">Create your first 3D project to organize your assets</p>
          <button
            onClick={() => setShowCreateModal(true)}
            className="mt-4 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-white font-medium"
          >
            Create Project
          </button>
        </div>
      )}

      {/* Modals */}
      <AnimatePresence>
        {showCreateModal && (
          <ProjectCreationModal
            onClose={() => setShowCreateModal(false)}
            onSave={handleCreateProject}
          />
        )}
        {selectedProject && (
          <ProjectDetail
            project={selectedProject}
            onClose={() => setSelectedProject(null)}
            onUpdate={handleUpdateProject}
            onDelete={handleDeleteProject}
            trellisService={trellisService}
          />
        )}
      </AnimatePresence>
    </div>
  );
};

export default TRELLISProjectManager;