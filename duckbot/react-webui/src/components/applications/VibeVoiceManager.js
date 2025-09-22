import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const VibeVoiceManager = ({ onClose }) => {
  const [vibevoiceStatus, setVibevoiceStatus] = useState({
    running: false,
    port: 8190,
    version: '2.1.0',
    models: [],
    voices: [],
    activeSessions: [],
    systemResources: {
      cpu: 0,
      memory: 0,
      gpu: 0
    }
  });

  const [selectedVoice, setSelectedVoice] = useState(null);
  const [ttsQueue, setTtsQueue] = useState([]);
  const [ttsHistory, setTtsHistory] = useState([]);
  const [settings, setSettings] = useState({
    autoOptimize: true,
    qualityPreset: 'balanced',
    maxConcurrentTTS: 3,
    enableEmotionalTone: true,
    enableVoiceCloning: false,
    defaultLanguage: 'en',
    streamingEnabled: true
  });

  const [newTTSRequest, setNewTTSRequest] = useState({
    text: '',
    voice: 'en-alice',
    language: 'en',
    emotion: 'neutral',
    speed: 1.0,
    pitch: 1.0,
    useSSML: false
  });

  const [voiceCloning, setVoiceCloning] = useState({
    samples: [],
    isTraining: false,
    trainingProgress: 0,
    clonedVoices: []
  });

  // Initialize VibeVoice connection
  useEffect(() => {
    checkVibevoiceStatus();
    const interval = setInterval(checkVibevoiceStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  const checkVibevoiceStatus = async () => {
    try {
      const response = await fetch('http://localhost:8190/status');
      if (response.ok) {
        const status = await response.json();
        setVibevoiceStatus(status);
      } else {
        setVibevoiceStatus(prev => ({ ...prev, running: false }));
      }
    } catch (error) {
      setVibevoiceStatus(prev => ({ ...prev, running: false }));
    }
  };

  const startVibevoice = async () => {
    try {
      const response = await fetch('http://localhost:8787/api/vibevoice/start', {
        method: 'POST'
      });

      if (response.ok) {
        setTimeout(checkVibevoiceStatus, 3000);
      }
    } catch (error) {
      console.error('Failed to start VibeVoice:', error);
    }
  };

  const stopVibevoice = async () => {
    try {
      const response = await fetch('http://localhost:8190/stop', {
        method: 'POST'
      });

      if (response.ok) {
        setVibevoiceStatus(prev => ({ ...prev, running: false }));
      }
    } catch (error) {
      console.error('Failed to stop VibeVoice:', error);
    }
  };

  const submitTTSRequest = async () => {
    if (!newTTSRequest.text.trim()) return;

    const request = {
      id: Date.now().toString(),
      ...newTTSRequest,
      status: 'queued',
      submittedAt: new Date(),
      progress: 0
    };

    setTtsQueue(prev => [...prev, request]);

    try {
      const response = await fetch('http://localhost:8190/tts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newTTSRequest)
      });

      if (response.ok) {
        const result = await response.json();
        const updatedRequest = { ...request, serverRequestId: result.request_id };

        setTtsQueue(prev => prev.map(r => r.id === request.id ? updatedRequest : r));
        monitorTTSProgress(updatedRequest);
      }
    } catch (error) {
      setTtsQueue(prev => prev.map(r =>
        r.id === request.id ? { ...r, status: 'error', error: error.message } : r
      ));
    }

    setNewTTSRequest(prev => ({ ...prev, text: '' }));
  };

  const monitorTTSProgress = (request) => {
    const interval = setInterval(async () => {
      try {
        const response = await fetch(`http://localhost:8190/tts/${request.serverRequestId}`);
        if (response.ok) {
          const status = await response.json();

          setTtsQueue(prev => prev.map(r =>
            r.id === request.id ? { ...r, ...status } : r
          ));

          if (status.status === 'completed' || status.status === 'error') {
            clearInterval(interval);

            if (status.status === 'completed') {
              setTtsHistory(prev => [status, ...prev.slice(0, 49)]);
              setTtsQueue(prev => prev.filter(r => r.id !== request.id));
            }
          }
        }
      } catch (error) {
        clearInterval(interval);
        setTtsQueue(prev => prev.map(r =>
          r.id === request.id ? { ...r, status: 'error', error: 'Connection failed' } : r
        ));
      }
    }, 1000);
  };

  const playAudio = async (requestId) => {
    const request = ttsHistory.find(r => r.id === requestId);
    if (!request || !request.audioUrl) return;

    try {
      const audio = new Audio(request.audioUrl);
      await audio.play();
    } catch (error) {
      console.error('Failed to play audio:', error);
    }
  };

  const downloadAudio = async (requestId) => {
    const request = ttsHistory.find(r => r.id === requestId);
    if (!request || !request.audioUrl) return;

    try {
      const response = await fetch(request.audioUrl);
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `vibevoice_${requestId}.wav`;
        a.click();
        window.URL.revokeObjectURL(url);
      }
    } catch (error) {
      console.error('Failed to download audio:', error);
    }
  };

  const startVoiceCloning = async () => {
    if (voiceCloning.samples.length < 3) {
      alert('Please provide at least 3 voice samples for cloning');
      return;
    }

    setVoiceCloning(prev => ({ ...prev, isTraining: true, trainingProgress: 0 }));

    try {
      const response = await fetch('http://localhost:8190/voice-clone/train', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ samples: voiceCloning.samples })
      });

      if (response.ok) {
        const result = await response.json();

        // Simulate training progress
        const progressInterval = setInterval(() => {
          setVoiceCloning(prev => {
            const newProgress = prev.trainingProgress + 10;
            if (newProgress >= 100) {
              clearInterval(progressInterval);
              return { ...prev, isTraining: false, trainingProgress: 100, clonedVoices: [...prev.clonedVoices, result.voice_id] };
            }
            return { ...prev, trainingProgress: newProgress };
          });
        }, 500);
      }
    } catch (error) {
      setVoiceCloning(prev => ({ ...prev, isTraining: false }));
      console.error('Failed to start voice cloning:', error);
    }
  };

  const addVoiceSample = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    try {
      const formData = new FormData();
      formData.append('sample', file);

      const response = await fetch('http://localhost:8190/voice-clone/sample', {
        method: 'POST',
        body: formData
      });

      if (response.ok) {
        const result = await response.json();
        setVoiceCloning(prev => ({
          ...prev,
          samples: [...prev.samples, { id: result.sample_id, name: file.name, duration: result.duration }]
        }));
      }
    } catch (error) {
      console.error('Failed to add voice sample:', error);
    }
  };

  const optimizeSettings = async () => {
    try {
      const response = await fetch('http://localhost:8190/optimize', {
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
      await fetch('http://localhost:8190/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newSettings)
      });

      setSettings(newSettings);
    } catch (error) {
      console.error('Failed to update settings:', error);
    }
  };

  const testVoice = async (voiceId) => {
    const testText = "Hello! This is a test of the VibeVoice text-to-speech system.";

    try {
      const response = await fetch('http://localhost:8190/tts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: testText,
          voice: voiceId,
          language: 'en',
          emotion: 'happy'
        })
      });

      if (response.ok) {
        const result = await response.json();
        const audio = new Audio(result.audioUrl);
        await audio.play();
      }
    } catch (error) {
      console.error('Failed to test voice:', error);
    }
  };

  const getEmotionColor = (emotion) => {
    const colors = {
      neutral: 'text-gray-400',
      happy: 'text-yellow-400',
      sad: 'text-blue-400',
      angry: 'text-red-400',
      surprised: 'text-purple-400',
      calm: 'text-green-400'
    };
    return colors[emotion] || 'text-gray-400';
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
            <h1 className="text-2xl font-bold text-white">VibeVoice Manager</h1>
            <p className="text-slate-400 mt-1">Advanced Text-to-Speech & Voice Cloning</p>
          </div>
          <div className="flex items-center space-x-4">
            {vibevoiceStatus.running ? (
              <button
                onClick={stopVibevoice}
                className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors"
              >
                ⏹️ Stop VibeVoice
              </button>
            ) : (
              <button
                onClick={startVibevoice}
                className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors"
              >
                ▶️ Start VibeVoice
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
            <div className={`w-3 h-3 rounded-full ${vibevoiceStatus.running ? 'bg-green-400' : 'bg-red-400'}`} />
            <span className="text-sm text-slate-300">
              Status: {vibevoiceStatus.running ? 'Running' : 'Stopped'}
            </span>
          </div>
          <span className="text-sm text-slate-300">Port: {vibevoiceStatus.port}</span>
          <span className="text-sm text-slate-300">Version: {vibevoiceStatus.version}</span>
          <span className="text-sm text-slate-300">
            Sessions: {vibevoiceStatus.activeSessions.length}
          </span>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {/* System Resources */}
        <div className="glass-strong rounded-lg p-6">
          <h2 className="text-xl font-bold text-white mb-4">System Resources</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {Object.entries(vibevoiceStatus.systemResources).map(([resource, value]) => (
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
          {/* TTS Generation */}
          <div className="glass-strong rounded-lg p-6">
            <h2 className="text-xl font-bold text-white mb-4">Text-to-Speech</h2>

            {/* New TTS Request Form */}
            <div className="glass-medium rounded-lg p-4 mb-4">
              <h3 className="font-semibold text-white mb-3">New TTS Request</h3>
              <div className="space-y-3">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1">
                    Text
                  </label>
                  <textarea
                    value={newTTSRequest.text}
                    onChange={(e) => setNewTTSRequest(prev => ({ ...prev, text: e.target.value }))}
                    placeholder="Enter text to convert to speech..."
                    className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white text-sm resize-none"
                    rows={3}
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-1">
                      Voice
                    </label>
                    <select
                      value={newTTSRequest.voice}
                      onChange={(e) => setNewTTSRequest(prev => ({ ...prev, voice: e.target.value }))}
                      className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white text-sm"
                    >
                      {vibevoiceStatus.voices.map(voice => (
                        <option key={voice.id} value={voice.id}>
                          {voice.name} ({voice.language})
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-1">
                      Emotion
                    </label>
                    <select
                      value={newTTSRequest.emotion}
                      onChange={(e) => setNewTTSRequest(prev => ({ ...prev, emotion: e.target.value }))}
                      className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white text-sm"
                    >
                      <option value="neutral">Neutral</option>
                      <option value="happy">Happy</option>
                      <option value="sad">Sad</option>
                      <option value="angry">Angry</option>
                      <option value="surprised">Surprised</option>
                      <option value="calm">Calm</option>
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-1">
                      Speed
                    </label>
                    <input
                      type="range"
                      min="0.5"
                      max="2.0"
                      step="0.1"
                      value={newTTSRequest.speed}
                      onChange={(e) => setNewTTSRequest(prev => ({ ...prev, speed: parseFloat(e.target.value) }))}
                      className="w-full"
                    />
                    <div className="text-xs text-slate-400">{newTTSRequest.speed}x</div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-1">
                      Pitch
                    </label>
                    <input
                      type="range"
                      min="0.5"
                      max="2.0"
                      step="0.1"
                      value={newTTSRequest.pitch}
                      onChange={(e) => setNewTTSRequest(prev => ({ ...prev, pitch: parseFloat(e.target.value) }))}
                      className="w-full"
                    />
                    <div className="text-xs text-slate-400">{newTTSRequest.pitch}x</div>
                  </div>
                </div>

                <button
                  onClick={submitTTSRequest}
                  disabled={!newTTSRequest.text.trim() || ttsQueue.length >= settings.maxConcurrentTTS}
                  className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-600 text-white rounded transition-colors"
                >
                  🎵 Generate Speech
                </button>
              </div>
            </div>

            {/* TTS Queue */}
            <div className="space-y-3">
              <h3 className="font-semibold text-white">Active Requests</h3>
              {ttsQueue.length === 0 ? (
                <div className="text-center text-slate-400 py-4">
                  No active requests
                </div>
              ) : (
                ttsQueue.map(request => (
                  <div key={request.id} className="glass-medium rounded-lg p-3">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center space-x-2">
                        <span className={`text-sm ${getStatusColor(request.status)}`}>
                          {request.status === 'running' ? '🔄' : request.status === 'queued' ? '⏳' : '❌'}
                        </span>
                        <span className="text-sm font-medium text-white capitalize">
                          {request.status}
                        </span>
                      </div>
                      <span className={`text-xs ${getEmotionColor(request.emotion)}`}>
                        {request.emotion}
                      </span>
                    </div>

                    <div className="text-sm text-slate-300 mb-2 truncate">
                      {request.text}
                    </div>

                    {request.status === 'running' && request.progress > 0 && (
                      <div className="mt-2">
                        <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
                          <span>Progress</span>
                          <span>{Math.round(request.progress)}%</span>
                        </div>
                        <div className="w-full bg-slate-700 rounded-full h-2">
                          <div
                            className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                            style={{ width: `${request.progress}%` }}
                          />
                        </div>
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Voice Library */}
          <div className="glass-strong rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold text-white">Voice Library</h2>
              <span className="text-sm text-slate-400">
                {vibevoiceStatus.voices.length} voices
              </span>
            </div>

            <div className="space-y-3 max-h-96 overflow-y-auto">
              {vibevoiceStatus.voices.map(voice => (
                <div key={voice.id} className="glass-medium rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <div>
                      <h3 className="font-semibold text-white">{voice.name}</h3>
                      <p className="text-sm text-slate-400">{voice.description}</p>
                    </div>
                    <button
                      onClick={() => testVoice(voice.id)}
                      className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded text-xs transition-colors"
                    >
                      ▶️ Test
                    </button>
                  </div>

                  <div className="grid grid-cols-2 gap-2 text-xs text-slate-400">
                    <span>Language: {voice.language}</span>
                    <span>Gender: {voice.gender}</span>
                    <span>Age: {voice.age}</span>
                    <span>Style: {voice.style}</span>
                  </div>

                  <div className="flex flex-wrap gap-1 mt-2">
                    {voice.emotions?.map(emotion => (
                      <span key={emotion} className={`text-xs px-2 py-1 rounded ${getEmotionColor(emotion)} bg-slate-700/50`}>
                        {emotion}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Voice Cloning */}
        <div className="glass-strong rounded-lg p-6">
          <h2 className="text-xl font-bold text-white mb-4">Voice Cloning</h2>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div>
              <h3 className="font-semibold text-white mb-3">Create Voice Clone</h3>

              {voiceCloning.isTraining ? (
                <div className="glass-medium rounded-lg p-4">
                  <div className="text-center">
                    <div className="text-lg font-semibold text-white mb-2">Training Voice Model</div>
                    <div className="text-sm text-slate-400 mb-4">
                      This may take a few minutes...
                    </div>
                    <div className="w-full bg-slate-700 rounded-full h-4 mb-2">
                      <div
                        className="bg-purple-500 h-4 rounded-full transition-all duration-500"
                        style={{ width: `${voiceCloning.trainingProgress}%` }}
                      />
                    </div>
                    <div className="text-sm text-slate-400">
                      {voiceCloning.trainingProgress}% complete
                    </div>
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="glass-medium rounded-lg p-4">
                    <div className="flex items-center justify-between mb-3">
                      <span className="text-sm font-medium text-white">Voice Samples</span>
                      <span className="text-xs text-slate-400">
                        {voiceCloning.samples.length}/10 (minimum 3)
                      </span>
                    </div>

                    <div className="space-y-2 mb-3">
                      {voiceCloning.samples.length === 0 ? (
                        <div className="text-center text-slate-400 py-4 text-sm">
                          No samples uploaded yet
                        </div>
                      ) : (
                        voiceCloning.samples.map(sample => (
                          <div key={sample.id} className="flex items-center justify-between p-2 bg-slate-800/50 rounded">
                            <div>
                              <div className="text-sm text-white">{sample.name}</div>
                              <div className="text-xs text-slate-400">{sample.duration}s</div>
                            </div>
                            <button className="text-red-400 hover:text-red-300 text-xs">
                              ✕
                            </button>
                          </div>
                        ))
                      )}
                    </div>

                    <label className="block w-full px-4 py-2 bg-slate-600 hover:bg-slate-700 text-white rounded text-center text-sm cursor-pointer transition-colors">
                      📁 Upload Sample
                      <input
                        type="file"
                        accept="audio/*"
                        onChange={addVoiceSample}
                        className="hidden"
                        disabled={voiceCloning.samples.length >= 10}
                      />
                    </label>
                  </div>

                  <button
                    onClick={startVoiceCloning}
                    disabled={voiceCloning.samples.length < 3}
                    className="w-full px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-slate-600 text-white rounded transition-colors"
                  >
                    🧬 Clone Voice
                  </button>
                </div>
              )}
            </div>

            <div>
              <h3 className="font-semibold text-white mb-3">Your Cloned Voices</h3>

              {voiceCloning.clonedVoices.length === 0 ? (
                <div className="glass-medium rounded-lg p-8 text-center">
                  <div className="text-slate-400 mb-2">No cloned voices yet</div>
                  <div className="text-sm text-slate-500">
                    Upload voice samples and train a model to get started
                  </div>
                </div>
              ) : (
                <div className="space-y-3">
                  {voiceCloning.clonedVoices.map(voiceId => (
                    <div key={voiceId} className="glass-medium rounded-lg p-4">
                      <div className="flex items-center justify-between mb-2">
                        <div>
                          <h4 className="font-semibold text-white">Cloned Voice {voiceId.slice(0, 8)}</h4>
                          <p className="text-sm text-slate-400">Custom trained voice</p>
                        </div>
                        <div className="flex space-x-2">
                          <button
                            onClick={() => testVoice(voiceId)}
                            className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded text-xs transition-colors"
                          >
                            ▶️ Test
                          </button>
                          <button className="px-3 py-1 bg-red-600 hover:bg-red-700 text-white rounded text-xs transition-colors">
                            🗑️ Delete
                          </button>
                        </div>
                      </div>

                      <div className="flex items-center space-x-4 text-xs text-slate-400">
                        <span>Quality: High</span>
                        <span>Training Date: Recently</span>
                        <span>Status: Ready</span>
                      </div>
                    </div>
                  ))}
                </div>
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
                  <label className="block text-sm text-slate-300 mb-1">Max Concurrent TTS</label>
                  <input
                    type="number"
                    value={settings.maxConcurrentTTS}
                    onChange={(e) => updateSettings({ ...settings, maxConcurrentTTS: parseInt(e.target.value) })}
                    min="1"
                    max="10"
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
              <h3 className="font-semibold text-white mb-3">Advanced Features</h3>
              <div className="space-y-3">
                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={settings.enableEmotionalTone}
                    onChange={(e) => updateSettings({ ...settings, enableEmotionalTone: e.target.checked })}
                    className="rounded text-blue-600"
                  />
                  <span className="text-sm text-slate-300">Emotional tone support</span>
                </label>

                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={settings.enableVoiceCloning}
                    onChange={(e) => updateSettings({ ...settings, enableVoiceCloning: e.target.checked })}
                    className="rounded text-blue-600"
                  />
                  <span className="text-sm text-slate-300">Voice cloning</span>
                </label>

                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={settings.streamingEnabled}
                    onChange={(e) => updateSettings({ ...settings, streamingEnabled: e.target.checked })}
                    className="rounded text-blue-600"
                  />
                  <span className="text-sm text-slate-300">Streaming TTS</span>
                </label>

                <div>
                  <label className="block text-sm text-slate-300 mb-1">Default Language</label>
                  <select
                    value={settings.defaultLanguage}
                    onChange={(e) => updateSettings({ ...settings, defaultLanguage: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white text-sm"
                  >
                    <option value="en">English</option>
                    <option value="es">Spanish</option>
                    <option value="fr">French</option>
                    <option value="de">German</option>
                    <option value="ja">Japanese</option>
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
                    VibeVoice is deeply integrated with DuckBot for natural conversations and emotional responses.
                  </div>
                </div>

                <div className="p-3 bg-slate-800/50 rounded-lg">
                  <div className="text-sm text-slate-300 mb-2">Workflow Support</div>
                  <div className="text-xs text-slate-400">
                    Use VibeVoice in cross-service workflows for automated voice-over and audio generation.
                  </div>
                </div>

                <div className="p-3 bg-slate-800/50 rounded-lg">
                  <div className="text-sm text-slate-300 mb-2">Smart Adaptation</div>
                  <div className="text-xs text-slate-400">
                    AI automatically adapts voice parameters based on context and content type.
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

export default VibeVoiceManager;