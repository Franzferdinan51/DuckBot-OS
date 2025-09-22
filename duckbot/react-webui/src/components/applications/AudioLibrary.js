import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Line, Pie } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

const AudioLibrary = ({ onClose }) => {
  // State for audio library
  const [audioFiles, setAudioFiles] = useState([]);
  const [folders, setFolders] = useState([
    { id: 'generated', name: 'Generated Audio', count: 0, icon: '🎵' },
    { id: 'podcasts', name: 'Podcasts', count: 0, icon: '🎙️' },
    { id: 'voices', name: 'Voice Presets', count: 0, icon: '🎤' },
    { id: 'projects', name: 'Projects', count: 0, icon: '📁' },
    { id: 'favorites', name: 'Favorites', count: 0, icon: '⭐' }
  ]);

  const [currentFolder, setCurrentFolder] = useState('generated');
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState('created');
  const [sortOrder, setSortOrder] = useState('desc');

  // State for voice presets
  const [voicePresets, setVoicePresets] = useState([]);
  const [editingPreset, setEditingPreset] = useState(null);
  const [newPreset, setNewPreset] = useState({
    name: '',
    voice: 'en-alice',
    style: 'conversational',
    emotion: 'neutral',
    speed: 'normal',
    pitch: 'normal',
    description: ''
  });

  // State for audio player
  const [currentlyPlaying, setCurrentlyPlaying] = useState(null);
  const [audioPlayer, setAudioPlayer] = useState(null);
  const [playbackProgress, setPlaybackProgress] = useState(0);
  const [playbackDuration, setPlaybackDuration] = useState(0);

  // State for batch operations
  const [batchMode, setBatchMode] = useState(false);
  const [exportFormat, setExportFormat] = useState('wav');

  // State for analytics
  const [analytics, setAnalytics] = useState({
    totalFiles: 0,
    totalDuration: 0,
    storageUsed: 0,
    voicesUsed: {},
    formats: {},
    dailyUsage: []
  });

  const audioContextRef = useRef(null);

  // Load audio files and presets
  useEffect(() => {
    loadAudioFiles();
    loadVoicePresets();
    loadAnalytics();
  }, [currentFolder]);

  const loadAudioFiles = async () => {
    try {
      const response = await fetch(`http://localhost:8000/audio/library/${currentFolder}`);
      if (response.ok) {
        const data = await response.json();
        setAudioFiles(data.files || []);
        updateFolderCounts(data.files || []);
      }
    } catch (error) {
      console.error('Failed to load audio files:', error);
    }
  };

  const loadVoicePresets = async () => {
    try {
      const response = await fetch('http://localhost:8000/voices/presets');
      if (response.ok) {
        const data = await response.json();
        setVoicePresets(data.presets || []);
      }
    } catch (error) {
      console.error('Failed to load voice presets:', error);
    }
  };

  const loadAnalytics = async () => {
    try {
      const response = await fetch('http://localhost:8000/audio/analytics');
      if (response.ok) {
        const data = await response.json();
        setAnalytics(data);
      }
    } catch (error) {
      console.error('Failed to load analytics:', error);
    }
  };

  const updateFolderCounts = (files) => {
    const counts = {
      generated: files.filter(f => f.type === 'generated').length,
      podcasts: files.filter(f => f.type === 'podcast').length,
      voices: files.filter(f => f.type === 'voice_preset').length,
      projects: files.filter(f => f.type === 'project').length,
      favorites: files.filter(f => f.favorite).length
    };

    setFolders(prev => prev.map(folder => ({
      ...folder,
      count: counts[folder.id] || 0
    })));
  };

  const playAudio = async (file) => {
    try {
      if (audioPlayer) {
        audioPlayer.pause();
      }

      const player = new Audio(file.audioUrl);
      setAudioPlayer(player);
      setCurrentlyPlaying(file.id);

      player.play();

      player.ontimeupdate = () => {
        setPlaybackProgress(player.currentTime);
      };

      player.onloadedmetadata = () => {
        setPlaybackDuration(player.duration);
      };

      player.onended = () => {
        setCurrentlyPlaying(null);
        setPlaybackProgress(0);
        setPlaybackDuration(0);
      };

    } catch (error) {
      console.error('Failed to play audio:', error);
    }
  };

  const stopAudio = () => {
    if (audioPlayer) {
      audioPlayer.pause();
      setAudioPlayer(null);
      setCurrentlyPlaying(null);
      setPlaybackProgress(0);
      setPlaybackDuration(0);
    }
  };

  const toggleFavorite = async (fileId) => {
    try {
      await fetch(`http://localhost:8000/audio/favorite/${fileId}`, {
        method: 'POST'
      });

      setAudioFiles(prev => prev.map(file =>
        file.id === fileId ? { ...file, favorite: !file.favorite } : file
      ));
    } catch (error) {
      console.error('Failed to toggle favorite:', error);
    }
  };

  const deleteFile = async (fileId) => {
    try {
      await fetch(`http://localhost:8000/audio/file/${fileId}`, {
        method: 'DELETE'
      });

      setAudioFiles(prev => prev.filter(file => file.id !== fileId));
      setSelectedFiles(prev => prev.filter(id => id !== fileId));
    } catch (error) {
      console.error('Failed to delete file:', error);
    }
  };

  const deleteSelectedFiles = async () => {
    try {
      await Promise.all(selectedFiles.map(fileId =>
        fetch(`http://localhost:8000/audio/file/${fileId}`, { method: 'DELETE' })
      ));

      setAudioFiles(prev => prev.filter(file => !selectedFiles.includes(file.id)));
      setSelectedFiles([]);
    } catch (error) {
      console.error('Failed to delete selected files:', error);
    }
  };

  const downloadFile = async (file, format = 'wav') => {
    try {
      const response = await fetch(`${file.audioUrl}?format=${format}`);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${file.name}.${format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Failed to download file:', error);
    }
  };

  const downloadSelectedFiles = async () => {
    try {
      const filesToDownload = audioFiles.filter(file => selectedFiles.includes(file.id));

      for (const file of filesToDownload) {
        await downloadFile(file, exportFormat);
      }
    } catch (error) {
      console.error('Failed to download selected files:', error);
    }
  };

  const createVoicePreset = async () => {
    try {
      const response = await fetch('http://localhost:8000/voices/presets', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newPreset)
      });

      if (response.ok) {
        const created = await response.json();
        setVoicePresets(prev => [...prev, created]);
        setNewPreset({
          name: '',
          voice: 'en-alice',
          style: 'conversational',
          emotion: 'neutral',
          speed: 'normal',
          pitch: 'normal',
          description: ''
        });
      }
    } catch (error) {
      console.error('Failed to create voice preset:', error);
    }
  };

  const updateVoicePreset = async (presetId, updates) => {
    try {
      const response = await fetch(`http://localhost:8000/voices/presets/${presetId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates)
      });

      if (response.ok) {
        const updated = await response.json();
        setVoicePresets(prev => prev.map(preset =>
          preset.id === presetId ? updated : preset
        ));
        setEditingPreset(null);
      }
    } catch (error) {
      console.error('Failed to update voice preset:', error);
    }
  };

  const deleteVoicePreset = async (presetId) => {
    try {
      await fetch(`http://localhost:8000/voices/presets/${presetId}`, {
        method: 'DELETE'
      });

      setVoicePresets(prev => prev.filter(preset => preset.id !== presetId));
    } catch (error) {
      console.error('Failed to delete voice preset:', error);
    }
  };

  const applyVoicePreset = (preset) => {
    // This would typically update the voice generator settings
    console.log('Applying preset:', preset);
    // Implement preset application logic
  };

  const filteredFiles = audioFiles.filter(file =>
    file.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (file.description && file.description.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  const sortedFiles = [...filteredFiles].sort((a, b) => {
    let aVal = a[sortBy];
    let bVal = b[sortBy];

    if (sortBy === 'created') {
      aVal = new Date(aVal);
      bVal = new Date(bVal);
    }

    if (sortOrder === 'asc') {
      return aVal > bVal ? 1 : -1;
    } else {
      return aVal < bVal ? 1 : -1;
    }
  });

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDuration = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // Chart data
  const usageChartData = {
    labels: analytics.dailyUsage.map(d => d.date),
    datasets: [
      {
        label: 'Files Generated',
        data: analytics.dailyUsage.map(d => d.files),
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        fill: true,
      },
    ],
  };

  const formatDistributionData = {
    labels: Object.keys(analytics.formats),
    datasets: [
      {
        data: Object.values(analytics.formats),
        backgroundColor: [
          'rgba(59, 130, 246, 0.8)',
          'rgba(16, 185, 129, 0.8)',
          'rgba(245, 158, 11, 0.8)',
          'rgba(239, 68, 68, 0.8)',
        ],
      },
    ],
  };

  return (
    <div className="h-full flex flex-col bg-slate-900">
      {/* Header */}
      <div className="bg-slate-800 border-b border-slate-700 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="text-2xl">🎵</div>
            <div>
              <h2 className="text-xl font-bold text-white">Audio Library</h2>
              <p className="text-sm text-slate-400">Manage and organize your voice content</p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <span className="text-sm text-slate-300">
              {analytics.totalFiles} files • {formatFileSize(analytics.storageUsed)}
            </span>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-auto p-4">
        <div className="grid grid-cols-12 gap-4 h-full">
          {/* Left Column - Folders and Presets */}
          <div className="col-span-3 space-y-4">
            {/* Folders */}
            <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
              <h3 className="text-lg font-semibold text-white mb-3">Folders</h3>
              <div className="space-y-2">
                {folders.map(folder => (
                  <button
                    key={folder.id}
                    onClick={() => setCurrentFolder(folder.id)}
                    className={`w-full flex items-center justify-between p-2 rounded transition-colors ${
                      currentFolder === folder.id
                        ? 'bg-blue-600 text-white'
                        : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                    }`}
                  >
                    <div className="flex items-center space-x-2">
                      <span>{folder.icon}</span>
                      <span className="text-sm">{folder.name}</span>
                    </div>
                    <span className="text-xs">{folder.count}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Voice Presets */}
            <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-lg font-semibold text-white">Voice Presets</h3>
                <button
                  onClick={() => setEditingPreset('new')}
                  className="text-blue-400 hover:text-blue-300"
                >
                  +
                </button>
              </div>

              {editingPreset === 'new' && (
                <div className="mb-3 p-3 bg-slate-700 rounded space-y-2">
                  <input
                    type="text"
                    placeholder="Preset name"
                    value={newPreset.name}
                    onChange={(e) => setNewPreset(prev => ({ ...prev, name: e.target.value }))}
                    className="w-full p-1 bg-slate-600 border border-slate-500 rounded text-white text-sm"
                  />
                  <select
                    value={newPreset.voice}
                    onChange={(e) => setNewPreset(prev => ({ ...prev, voice: e.target.value }))}
                    className="w-full p-1 bg-slate-600 border border-slate-500 rounded text-white text-sm"
                  >
                    <option value="en-alice">Alice</option>
                    <option value="en-carter">Carter</option>
                    <option value="en-david">David</option>
                    <option value="en-emily">Emily</option>
                  </select>
                  <button
                    onClick={createVoicePreset}
                    className="w-full py-1 bg-green-600 hover:bg-green-700 rounded text-white text-sm"
                  >
                    Create
                  </button>
                </div>
              )}

              <div className="space-y-2 max-h-64 overflow-y-auto">
                {voicePresets.map(preset => (
                  <div key={preset.id} className="bg-slate-700 rounded p-2">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium text-white">{preset.name}</span>
                      <div className="flex items-center space-x-1">
                        <button
                          onClick={() => applyVoicePreset(preset)}
                          className="text-xs text-green-400 hover:text-green-300"
                        >
                          Apply
                        </button>
                        <button
                          onClick={() => setEditingPreset(preset.id)}
                          className="text-xs text-blue-400 hover:text-blue-300"
                        >
                          Edit
                        </button>
                        <button
                          onClick={() => deleteVoicePreset(preset.id)}
                          className="text-xs text-red-400 hover:text-red-300"
                        >
                          ×
                        </button>
                      </div>
                    </div>
                    <div className="text-xs text-slate-400">
                      {preset.voice} • {preset.style} • {preset.emotion}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Center Column - File Browser */}
          <div className="col-span-6 space-y-4">
            {/* Search and Controls */}
            <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
              <div className="flex items-center space-x-2 mb-3">
                <input
                  type="text"
                  placeholder="Search audio files..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="flex-1 p-2 bg-slate-700 border border-slate-600 rounded text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                  className="p-2 bg-slate-700 border border-slate-600 rounded text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="created">Date</option>
                  <option value="name">Name</option>
                  <option value="duration">Duration</option>
                  <option value="size">Size</option>
                </select>
                <button
                  onClick={() => setSortOrder(prev => prev === 'asc' ? 'desc' : 'asc')}
                  className="p-2 bg-slate-700 hover:bg-slate-600 rounded text-white"
                >
                  {sortOrder === 'asc' ? '↑' : '↓'}
                </button>
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => setBatchMode(!batchMode)}
                    className={`px-3 py-1 rounded text-sm ${
                      batchMode
                        ? 'bg-blue-600 text-white'
                        : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                    }`}
                  >
                    {batchMode ? 'Exit Batch' : 'Batch Mode'}
                  </button>
                  {batchMode && selectedFiles.length > 0 && (
                    <>
                      <button
                        onClick={downloadSelectedFiles}
                        className="px-3 py-1 bg-green-600 hover:bg-green-700 rounded text-white text-sm"
                      >
                        Download ({selectedFiles.length})
                      </button>
                      <button
                        onClick={deleteSelectedFiles}
                        className="px-3 py-1 bg-red-600 hover:bg-red-700 rounded text-white text-sm"
                      >
                        Delete ({selectedFiles.length})
                      </button>
                    </>
                  )}
                </div>

                {batchMode && (
                  <select
                    value={exportFormat}
                    onChange={(e) => setExportFormat(e.target.value)}
                    className="p-1 bg-slate-700 border border-slate-600 rounded text-white text-sm"
                  >
                    <option value="wav">WAV</option>
                    <option value="mp3">MP3</option>
                    <option value="ogg">OGG</option>
                  </select>
                )}
              </div>
            </div>

            {/* File List */}
            <div className="bg-slate-800 rounded-lg border border-slate-700 flex-1 overflow-hidden">
              <div className="h-full overflow-y-auto">
                {sortedFiles.length === 0 ? (
                  <div className="text-center py-12 text-slate-400">
                    <div className="text-4xl mb-4">🎵</div>
                    <p>No audio files found</p>
                    <p className="text-sm">Generate some voice content to get started</p>
                  </div>
                ) : (
                  <div className="divide-y divide-slate-700">
                    {sortedFiles.map(file => (
                      <div key={file.id} className="p-4 hover:bg-slate-700/50 transition-colors">
                        <div className="flex items-center space-x-3">
                          {batchMode && (
                            <input
                              type="checkbox"
                              checked={selectedFiles.includes(file.id)}
                              onChange={(e) => {
                                if (e.target.checked) {
                                  setSelectedFiles(prev => [...prev, file.id]);
                                } else {
                                  setSelectedFiles(prev => prev.filter(id => id !== file.id));
                                }
                              }}
                              className="rounded border-slate-500 text-blue-600 focus:ring-blue-500"
                            />
                          )}

                          <div className="flex-1">
                            <div className="flex items-center justify-between mb-1">
                              <h4 className="text-sm font-medium text-white">{file.name}</h4>
                              <div className="flex items-center space-x-2">
                                <span className="text-xs text-slate-400">
                                  {formatDuration(file.duration)}
                                </span>
                                <span className="text-xs text-slate-400">
                                  {formatFileSize(file.size)}
                                </span>
                                <button
                                  onClick={() => toggleFavorite(file.id)}
                                  className="text-yellow-400 hover:text-yellow-300"
                                >
                                  {file.favorite ? '★' : '☆'}
                                </button>
                              </div>
                            </div>

                            <div className="flex items-center justify-between">
                              <div className="text-xs text-slate-400">
                                {file.voice && `Voice: ${file.voice}`}
                                {file.emotion && ` • ${file.emotion}`}
                                {file.style && ` • ${file.style}`}
                              </div>
                              <div className="flex items-center space-x-1">
                                <button
                                  onClick={() => playAudio(file)}
                                  disabled={currentlyPlaying === file.id}
                                  className={`p-1 rounded ${
                                    currentlyPlaying === file.id ? 'bg-red-600' : 'bg-blue-600 hover:bg-blue-700'
                                  } text-white`}
                                >
                                  {currentlyPlaying === file.id ? '⏸️' : '▶️'}
                                </button>
                                <button
                                  onClick={() => downloadFile(file, exportFormat)}
                                  className="p-1 bg-green-600 hover:bg-green-700 rounded text-white"
                                >
                                  💾
                                </button>
                                <button
                                  onClick={() => deleteFile(file.id)}
                                  className="p-1 bg-red-600 hover:bg-red-700 rounded text-white"
                                >
                                  🗑️
                                </button>
                              </div>
                            </div>
                          </div>
                        </div>

                        {currentlyPlaying === file.id && (
                          <div className="mt-3">
                            <div className="w-full bg-slate-600 rounded-full h-1 mb-1">
                              <div
                                className="bg-blue-500 h-1 rounded-full transition-all duration-300"
                                style={{ width: `${(playbackProgress / playbackDuration) * 100}%` }}
                              />
                            </div>
                            <div className="text-xs text-slate-400">
                              {formatDuration(playbackProgress)} / {formatDuration(playbackDuration)}
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Right Column - Analytics and Info */}
          <div className="col-span-3 space-y-4">
            {/* Storage Analytics */}
            <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
              <h3 className="text-lg font-semibold text-white mb-3">Storage Analytics</h3>

              <div className="space-y-3 mb-4">
                <div className="flex justify-between text-sm">
                  <span className="text-slate-300">Total Files</span>
                  <span className="text-white">{analytics.totalFiles}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-slate-300">Total Duration</span>
                  <span className="text-white">{formatDuration(analytics.totalDuration)}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-slate-300">Storage Used</span>
                  <span className="text-white">{formatFileSize(analytics.storageUsed)}</span>
                </div>
              </div>

              <div className="h-32">
                <Pie
                  data={formatDistributionData}
                  options={{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                      legend: { display: false }
                    }
                  }}
                />
              </div>
            </div>

            {/* Usage Trends */}
            <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
              <h3 className="text-lg font-semibold text-white mb-3">Usage Trends</h3>
              <div className="h-32">
                <Line
                  data={usageChartData}
                  options={{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                      legend: { display: false }
                    },
                    scales: {
                      y: { beginAtZero: true }
                    }
                  }}
                />
              </div>
            </div>

            {/* Voice Usage */}
            <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
              <h3 className="text-lg font-semibold text-white mb-3">Top Voices</h3>
              <div className="space-y-2">
                {Object.entries(analytics.voicesUsed || {})
                  .sort(([,a], [,b]) => b - a)
                  .slice(0, 5)
                  .map(([voice, count]) => (
                    <div key={voice} className="flex justify-between text-sm">
                      <span className="text-slate-300">{voice}</span>
                      <span className="text-white">{count} files</span>
                    </div>
                  ))}
              </div>
            </div>

            {/* Quick Actions */}
            <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
              <h3 className="text-lg font-semibold text-white mb-3">Quick Actions</h3>
              <div className="space-y-2">
                <button className="w-full py-2 bg-blue-600 hover:bg-blue-700 rounded text-white text-sm">
                  Backup Library
                </button>
                <button className="w-full py-2 bg-green-600 hover:bg-green-700 rounded text-white text-sm">
                  Export Playlist
                </button>
                <button className="w-full py-2 bg-purple-600 hover:bg-purple-700 rounded text-white text-sm">
                  Import Audio
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AudioLibrary;