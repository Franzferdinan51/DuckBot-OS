import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Line, Bar, Doughnut } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
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
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

const VibeVoiceDashboard = ({ onClose }) => {
  const [serviceStatus, setServiceStatus] = useState({
    available: false,
    connected: false,
    api_url: 'http://localhost:8000',
    response_time: 0,
    health_check: 'unknown'
  });

  const [voiceLibrary, setVoiceLibrary] = useState([]);
  const [generationQueue, setGenerationQueue] = useState([]);
  const [activeProjects, setActiveProjects] = useState([]);
  const [resourceUsage, setResourceUsage] = useState({
    cpu: 0,
    memory: 0,
    gpu: 0,
    active_generations: 0
  });

  const [stats, setStats] = useState({
    total_generations: 0,
    success_rate: 0,
    average_duration: 0,
    voices_used: 0,
    daily_usage: []
  });

  const [selectedVoice, setSelectedVoice] = useState('en-alice');
  const [generationText, setGenerationText] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [audioPlayer, setAudioPlayer] = useState(null);
  const [currentAudio, setCurrentAudio] = useState(null);

  const wsRef = useRef(null);
  const statusInterval = useRef(null);

  // Initialize WebSocket connection for real-time updates
  useEffect(() => {
    const connectWebSocket = () => {
      try {
        wsRef.current = new WebSocket('ws://localhost:8000/ws');

        wsRef.current.onopen = () => {
          console.log('VibeVoice WebSocket connected');
        };

        wsRef.current.onmessage = (event) => {
          const data = JSON.parse(event.data);
          handleWebSocketMessage(data);
        };

        wsRef.current.onclose = () => {
          console.log('VibeVoice WebSocket disconnected');
          setTimeout(connectWebSocket, 5000);
        };

        wsRef.current.onerror = (error) => {
          console.error('VibeVoice WebSocket error:', error);
        };
      } catch (error) {
        console.error('Failed to connect VibeVoice WebSocket:', error);
      }
    };

    connectWebSocket();

    // Start status polling
    statusInterval.current = setInterval(checkServiceStatus, 10000);

    // Load initial data
    loadVoiceLibrary();
    loadActiveProjects();
    loadStats();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (statusInterval.current) {
        clearInterval(statusInterval.current);
      }
    };
  }, []);

  const handleWebSocketMessage = (data) => {
    switch (data.type) {
      case 'queue_update':
        setGenerationQueue(data.queue);
        break;
      case 'resource_update':
        setResourceUsage(data.resources);
        break;
      case 'generation_complete':
        handleGenerationComplete(data);
        break;
      case 'service_status':
        setServiceStatus(prev => ({ ...prev, ...data.status }));
        break;
    }
  };

  const checkServiceStatus = async () => {
    try {
      const response = await fetch(`${serviceStatus.api_url}/health`);
      if (response.ok) {
        const health = await response.json();
        setServiceStatus(prev => ({
          ...prev,
          available: true,
          connected: true,
          health_check: health.status || 'healthy',
          response_time: health.response_time || 0
        }));
      } else {
        setServiceStatus(prev => ({
          ...prev,
          available: false,
          connected: false,
          health_check: 'unhealthy'
        }));
      }
    } catch (error) {
      setServiceStatus(prev => ({
        ...prev,
        available: false,
        connected: false,
        health_check: 'error'
      }));
    }
  };

  const loadVoiceLibrary = async () => {
    try {
      const response = await fetch(`${serviceStatus.api_url}/voices`);
      if (response.ok) {
        const voices = await response.json();
        setVoiceLibrary(voices.voices || []);
      }
    } catch (error) {
      console.error('Failed to load voice library:', error);
    }
  };

  const loadActiveProjects = async () => {
    try {
      const response = await fetch(`${serviceStatus.api_url}/projects`);
      if (response.ok) {
        const projects = await response.json();
        setActiveProjects(projects.projects || []);
      }
    } catch (error) {
      console.error('Failed to load active projects:', error);
    }
  };

  const loadStats = async () => {
    try {
      const response = await fetch(`${serviceStatus.api_url}/stats`);
      if (response.ok) {
        const statsData = await response.json();
        setStats(statsData);
      }
    } catch (error) {
      console.error('Failed to load stats:', error);
    }
  };

  const handleGenerationComplete = (data) => {
    if (data.success) {
      // Update queue
      setGenerationQueue(prev => prev.filter(item => item.task_id !== data.task_id));

      // Update stats
      setStats(prev => ({
        ...prev,
        total_generations: prev.total_generations + 1,
        success_rate: ((prev.total_generations + 1) / (prev.total_generations + 1)) * 100
      }));

      // Auto-play if enabled
      if (data.audio_url) {
        setCurrentAudio(data.audio_url);
      }
    }
  };

  const generateVoice = async () => {
    if (!generationText.trim() || isGenerating) return;

    setIsGenerating(true);
    try {
      const response = await fetch(`${serviceStatus.api_url}/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text: generationText,
          speaker: selectedVoice,
          style: 'conversational',
          emotion: 'neutral'
        }),
      });

      if (response.ok) {
        const result = await response.json();
        if (result.task_id) {
          // Add to queue
          setGenerationQueue(prev => [...prev, {
            task_id: result.task_id,
            text: generationText.substring(0, 50) + '...',
            speaker: selectedVoice,
            status: 'queued',
            created_at: new Date().toISOString()
          }]);
          setGenerationText('');
        }
      } else {
        console.error('Generation failed');
      }
    } catch (error) {
      console.error('Generation error:', error);
    } finally {
      setIsGenerating(false);
    }
  };

  const playAudio = (audioUrl) => {
    if (audioPlayer) {
      audioPlayer.pause();
    }

    const player = new Audio(audioUrl);
    player.play();
    setAudioPlayer(player);
    setCurrentAudio(audioUrl);

    player.onended = () => {
      setAudioPlayer(null);
      setCurrentAudio(null);
    };
  };

  const stopAudio = () => {
    if (audioPlayer) {
      audioPlayer.pause();
      setAudioPlayer(null);
      setCurrentAudio(null);
    }
  };

  const downloadAudio = async (audioUrl, filename) => {
    try {
      const response = await fetch(audioUrl);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename || 'vibevoice_audio.wav';
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Download failed:', error);
    }
  };

  // Chart data
  const usageChartData = {
    labels: stats.daily_usage.map(d => d.date),
    datasets: [
      {
        label: 'Generations',
        data: stats.daily_usage.map(d => d.count),
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        fill: true,
      },
    ],
  };

  const voiceUsageData = {
    labels: voiceLibrary.slice(0, 6).map(v => v.name),
    datasets: [
      {
        label: 'Usage Count',
        data: voiceLibrary.slice(0, 6).map(v => v.usage_count || 0),
        backgroundColor: [
          'rgba(59, 130, 246, 0.8)',
          'rgba(16, 185, 129, 0.8)',
          'rgba(245, 158, 11, 0.8)',
          'rgba(239, 68, 68, 0.8)',
          'rgba(139, 92, 246, 0.8)',
          'rgba(236, 72, 153, 0.8)',
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
            <div className="text-2xl">🎤</div>
            <div>
              <h2 className="text-xl font-bold text-white">VibeVoice Studio</h2>
              <p className="text-sm text-slate-400">Multi-speaker AI voice generation</p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <div className={`w-3 h-3 rounded-full ${
              serviceStatus.connected ? 'bg-green-400 animate-pulse' : 'bg-red-400'
            }`} />
            <span className="text-sm text-slate-300">
              {serviceStatus.connected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-auto p-4">
        <div className="grid grid-cols-12 gap-4 h-full">
          {/* Left Column - Quick Generation */}
          <div className="col-span-4 space-y-4">
            {/* Quick Generation Panel */}
            <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
              <h3 className="text-lg font-semibold text-white mb-3">Quick Generation</h3>

              <div className="space-y-3">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1">
                    Voice
                  </label>
                  <select
                    value={selectedVoice}
                    onChange={(e) => setSelectedVoice(e.target.value)}
                    className="w-full p-2 bg-slate-700 border border-slate-600 rounded text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    {voiceLibrary.map(voice => (
                      <option key={voice.id} value={voice.id}>
                        {voice.name} ({voice.language})
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1">
                    Text to Speech
                  </label>
                  <textarea
                    value={generationText}
                    onChange={(e) => setGenerationText(e.target.value)}
                    placeholder="Enter text to convert to speech..."
                    className="w-full p-2 bg-slate-700 border border-slate-600 rounded text-white focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                    rows={4}
                  />
                </div>

                <button
                  onClick={generateVoice}
                  disabled={isGenerating || !generationText.trim() || !serviceStatus.connected}
                  className="w-full py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-600 disabled:cursor-not-allowed rounded text-white font-medium transition-colors"
                >
                  {isGenerating ? 'Generating...' : 'Generate Voice'}
                </button>
              </div>
            </div>

            {/* Service Status */}
            <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
              <h3 className="text-lg font-semibold text-white mb-3">Service Status</h3>

              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-slate-300">Status</span>
                  <span className={`text-white ${
                    serviceStatus.health_check === 'healthy' ? 'text-green-400' :
                    serviceStatus.health_check === 'warning' ? 'text-yellow-400' : 'text-red-400'
                  }`}>
                    {serviceStatus.health_check}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-300">Response Time</span>
                  <span className="text-white">{serviceStatus.response_time}ms</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-300">Available Voices</span>
                  <span className="text-white">{voiceLibrary.length}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-300">Active Generations</span>
                  <span className="text-white">{resourceUsage.active_generations}</span>
                </div>
              </div>
            </div>

            {/* Resource Usage */}
            <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
              <h3 className="text-lg font-semibold text-white mb-3">Resource Usage</h3>

              <div className="space-y-3">
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-slate-300">CPU</span>
                    <span className="text-white">{resourceUsage.cpu}%</span>
                  </div>
                  <div className="w-full bg-slate-700 rounded-full h-2">
                    <div
                      className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${resourceUsage.cpu}%` }}
                    />
                  </div>
                </div>

                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-slate-300">Memory</span>
                    <span className="text-white">{resourceUsage.memory}%</span>
                  </div>
                  <div className="w-full bg-slate-700 rounded-full h-2">
                    <div
                      className="bg-green-500 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${resourceUsage.memory}%` }}
                    />
                  </div>
                </div>

                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-slate-300">GPU</span>
                    <span className="text-white">{resourceUsage.gpu}%</span>
                  </div>
                  <div className="w-full bg-slate-700 rounded-full h-2">
                    <div
                      className="bg-purple-500 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${resourceUsage.gpu}%` }}
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Center Column - Queue and Projects */}
          <div className="col-span-4 space-y-4">
            {/* Generation Queue */}
            <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
              <h3 className="text-lg font-semibold text-white mb-3">Generation Queue</h3>

              <div className="space-y-2 max-h-60 overflow-y-auto">
                {generationQueue.length === 0 ? (
                  <p className="text-slate-400 text-sm text-center py-4">No items in queue</p>
                ) : (
                  generationQueue.map((item, index) => (
                    <div key={item.task_id} className="bg-slate-700 rounded p-3">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm font-medium text-white">
                          {item.speaker}
                        </span>
                        <span className={`text-xs px-2 py-1 rounded ${
                          item.status === 'processing' ? 'bg-yellow-500 text-white' :
                          item.status === 'completed' ? 'bg-green-500 text-white' :
                          'bg-slate-600 text-slate-300'
                        }`}>
                          {item.status}
                        </span>
                      </div>
                      <p className="text-xs text-slate-400">{item.text}</p>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Active Projects */}
            <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
              <h3 className="text-lg font-semibold text-white mb-3">Active Projects</h3>

              <div className="space-y-2 max-h-60 overflow-y-auto">
                {activeProjects.length === 0 ? (
                  <p className="text-slate-400 text-sm text-center py-4">No active projects</p>
                ) : (
                  activeProjects.map(project => (
                    <div key={project.id} className="bg-slate-700 rounded p-3">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium text-white">
                          {project.name}
                        </span>
                        <span className="text-xs text-slate-400">
                          {project.progress}%
                        </span>
                      </div>
                      <div className="w-full bg-slate-600 rounded-full h-1 mb-2">
                        <div
                          className="bg-blue-500 h-1 rounded-full transition-all duration-300"
                          style={{ width: `${project.progress}%` }}
                        />
                      </div>
                      <p className="text-xs text-slate-400">
                        {project.voice_count} voices • {project.duration}s
                      </p>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Recent Audio */}
            <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
              <h3 className="text-lg font-semibold text-white mb-3">Recent Audio</h3>

              <div className="space-y-2 max-h-40 overflow-y-auto">
                {/* This would show recently generated audio files */}
                <p className="text-slate-400 text-sm text-center py-4">No recent audio</p>
              </div>
            </div>
          </div>

          {/* Right Column - Analytics */}
          <div className="col-span-4 space-y-4">
            {/* Statistics */}
            <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
              <h3 className="text-lg font-semibold text-white mb-3">Statistics</h3>

              <div className="grid grid-cols-2 gap-4 mb-4">
                <div className="bg-slate-700 rounded p-3 text-center">
                  <div className="text-2xl font-bold text-blue-400">
                    {stats.total_generations}
                  </div>
                  <div className="text-xs text-slate-400">Total Generations</div>
                </div>
                <div className="bg-slate-700 rounded p-3 text-center">
                  <div className="text-2xl font-bold text-green-400">
                    {stats.success_rate.toFixed(1)}%
                  </div>
                  <div className="text-xs text-slate-400">Success Rate</div>
                </div>
                <div className="bg-slate-700 rounded p-3 text-center">
                  <div className="text-2xl font-bold text-yellow-400">
                    {stats.average_duration.toFixed(1)}s
                  </div>
                  <div className="text-xs text-slate-400">Avg Duration</div>
                </div>
                <div className="bg-slate-700 rounded p-3 text-center">
                  <div className="text-2xl font-bold text-purple-400">
                    {stats.voices_used}
                  </div>
                  <div className="text-xs text-slate-400">Voices Used</div>
                </div>
              </div>

              <div className="h-40">
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
              <h3 className="text-lg font-semibold text-white mb-3">Voice Usage</h3>

              <div className="h-40">
                <Bar
                  data={voiceUsageData}
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

            {/* Audio Player */}
            {currentAudio && (
              <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
                <h3 className="text-lg font-semibold text-white mb-3">Audio Player</h3>

                <div className="flex items-center space-x-2">
                  <button
                    onClick={stopAudio}
                    className="p-2 bg-red-600 hover:bg-red-700 rounded text-white"
                  >
                    ⏹️
                  </button>
                  <div className="flex-1">
                    <div className="text-sm text-slate-300">Now Playing</div>
                    <div className="text-xs text-slate-400">Generated audio</div>
                  </div>
                  <button
                    onClick={() => downloadAudio(currentAudio)}
                    className="p-2 bg-blue-600 hover:bg-blue-700 rounded text-white"
                  >
                    💾
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default VibeVoiceDashboard;