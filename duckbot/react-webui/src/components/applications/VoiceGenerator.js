import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { DragDropContext, Droppable, Draggable } from 'react-beautiful-dnd';

const VoiceGenerator = ({ onClose }) => {
  // State for voice generation
  const [voices, setVoices] = useState([]);
  const [selectedVoice, setSelectedVoice] = useState('en-alice');
  const [generationMode, setGenerationMode] = useState('single');
  const [textInput, setTextInput] = useState('');
  const [emotion, setEmotion] = useState('neutral');
  const [style, setStyle] = useState('conversational');
  const [speed, setSpeed] = useState('normal');
  const [pitch, setPitch] = useState('normal');

  // State for multi-speaker conversations
  const [conversation, setConversation] = useState([
    { id: 1, speaker: 'en-alice', text: 'Hello, how are you today?' },
    { id: 2, speaker: 'en-carter', text: 'I\'m doing well, thank you for asking!' }
  ]);

  // State for emotional variants
  const [emotionVariants, setEmotionVariants] = useState([
    { emotion: 'happy', intensity: 0.8, enabled: true },
    { emotion: 'sad', intensity: 0.6, enabled: false },
    { emotion: 'angry', intensity: 0.7, enabled: false },
    { emotion: 'surprised', intensity: 0.9, enabled: false },
    { emotion: 'neutral', intensity: 0.5, enabled: true }
  ]);

  // State for batch processing
  const [batchItems, setBatchItems] = useState([]);
  const [batchProgress, setBatchProgress] = useState(0);

  // State for podcast generation
  const [podcastStructure, setPodcastStructure] = useState({
    title: 'Generated Podcast',
    intro: { speaker: 'host', text: 'Welcome to our podcast episode!' },
    segments: [
      {
        id: 1,
        type: 'monologue',
        speaker: 'host',
        title: 'Introduction',
        text: 'Today we\'ll be discussing an interesting topic...'
      },
      {
        id: 2,
        type: 'interview',
        title: 'Guest Interview',
        conversation: [
          { speaker: 'host', text: 'Tell us about your experience.' },
          { speaker: 'guest', text: 'It\'s been quite a journey...' }
        ]
      }
    ],
    outro: { speaker: 'host', text: 'Thanks for listening!' }
  });

  // State for audio playback
  const [generatedAudio, setGeneratedAudio] = useState([]);
  const [currentlyPlaying, setCurrentlyPlaying] = useState(null);
  const audioRef = useRef(null);

  // Load available voices
  useEffect(() => {
    loadVoices();
  }, []);

  const loadVoices = async () => {
    try {
      const response = await fetch('http://localhost:8000/voices');
      if (response.ok) {
        const data = await response.json();
        setVoices(data.voices || []);
      }
    } catch (error) {
      console.error('Failed to load voices:', error);
    }
  };

  const handleSingleGeneration = async () => {
    if (!textInput.trim()) return;

    try {
      const response = await fetch('http://localhost:8000/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: textInput,
          speaker: selectedVoice,
          style,
          emotion,
          speed,
          pitch
        })
      });

      if (response.ok) {
        const result = await response.json();
        if (result.success) {
          setGeneratedAudio(prev => [...prev, {
            id: Date.now(),
            type: 'single',
            text: textInput,
            speaker: selectedVoice,
            audioUrl: result.audio_url,
            duration: result.duration,
            created: new Date().toISOString()
          }]);
          setTextInput('');
        }
      }
    } catch (error) {
      console.error('Generation failed:', error);
    }
  };

  const handleConversationGeneration = async () => {
    try {
      const response = await fetch('http://localhost:8000/generate/conversation', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          conversation: conversation.map(turn => ({
            speaker: turn.speaker,
            text: turn.text
          })),
          style
        })
      });

      if (response.ok) {
        const result = await response.json();
        if (result.success) {
          setGeneratedAudio(prev => [...prev, {
            id: Date.now(),
            type: 'conversation',
            text: conversation.map(t => `${t.speaker}: ${t.text}`).join('\n'),
            speakers: conversation.map(t => t.speaker),
            audioUrl: result.audio_url,
            duration: result.duration,
            created: new Date().toISOString()
          }]);
        }
      }
    } catch (error) {
      console.error('Conversation generation failed:', error);
    }
  };

  const handleEmotionalVariantsGeneration = async () => {
    const enabledVariants = emotionVariants.filter(v => v.enabled);
    if (!textInput.trim() || enabledVariants.length === 0) return;

    const results = [];
    for (const variant of enabledVariants) {
      try {
        const response = await fetch('http://localhost:8000/generate/emotional', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            text: textInput,
            speaker: selectedVoice,
            emotion: variant.emotion,
            intensity: variant.intensity,
            style
          })
        });

        if (response.ok) {
          const result = await response.json();
          results.push({
            id: Date.now() + Math.random(),
            type: 'emotional',
            text: textInput,
            speaker: selectedVoice,
            emotion: variant.emotion,
            intensity: variant.intensity,
            audioUrl: result.audio_url,
            duration: result.duration,
            created: new Date().toISOString()
          });
        }
      } catch (error) {
        console.error(`Failed to generate ${variant.emotion} variant:`, error);
      }
    }

    setGeneratedAudio(prev => [...prev, ...results]);
  };

  const handlePodcastGeneration = async () => {
    try {
      const response = await fetch('http://localhost:8000/generate/podcast', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(podcastStructure)
      });

      if (response.ok) {
        const result = await response.json();
        if (result.success) {
          setGeneratedAudio(prev => [...prev, ...result.audio_files.map(file => ({
            id: Date.now() + Math.random(),
            type: 'podcast',
            segmentType: file.type,
            title: file.title,
            audioUrl: file.file,
            duration: file.duration || 0,
            created: new Date().toISOString()
          }))]);
        }
      }
    } catch (error) {
      console.error('Podcast generation failed:', error);
    }
  };

  const playAudio = (audioUrl, id) => {
    if (audioRef.current) {
      audioRef.current.pause();
    }

    const audio = new Audio(audioUrl);
    audioRef.current = audio;
    setCurrentlyPlaying(id);

    audio.play();
    audio.onended = () => setCurrentlyPlaying(null);
  };

  const stopAudio = () => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
      setCurrentlyPlaying(null);
    }
  };

  const downloadAudio = async (audioUrl, filename) => {
    try {
      const response = await fetch(audioUrl);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename || 'audio.wav';
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Download failed:', error);
    }
  };

  const addConversationTurn = () => {
    setConversation(prev => [...prev, {
      id: Date.now(),
      speaker: 'en-alice',
      text: ''
    }]);
  };

  const updateConversationTurn = (id, field, value) => {
    setConversation(prev => prev.map(turn =>
      turn.id === id ? { ...turn, [field]: value } : turn
    ));
  };

  const removeConversationTurn = (id) => {
    setConversation(prev => prev.filter(turn => turn.id !== id));
  };

  const onDragEnd = (result) => {
    if (!result.destination) return;

    const items = Array.from(conversation);
    const [reorderedItem] = items.splice(result.source.index, 1);
    items.splice(result.destination.index, 0, reorderedItem);

    setConversation(items);
  };

  const toggleEmotionVariant = (emotion) => {
    setEmotionVariants(prev => prev.map(v =>
      v.emotion === emotion ? { ...v, enabled: !v.enabled } : v
    ));
  };

  const updateEmotionIntensity = (emotion, intensity) => {
    setEmotionVariants(prev => prev.map(v =>
      v.emotion === emotion ? { ...v, intensity } : v
    ));
  };

  const addPodcastSegment = (type) => {
    const newSegment = {
      id: Date.now(),
      type,
      title: `New ${type} segment`,
      speaker: 'host',
      text: '',
      ...(type === 'interview' && { conversation: [] })
    };

    setPodcastStructure(prev => ({
      ...prev,
      segments: [...prev.segments, newSegment]
    }));
  };

  const updatePodcastSegment = (id, field, value) => {
    setPodcastStructure(prev => ({
      ...prev,
      segments: prev.segments.map(segment =>
        segment.id === id ? { ...segment, [field]: value } : segment
      )
    }));
  };

  const removePodcastSegment = (id) => {
    setPodcastStructure(prev => ({
      ...prev,
      segments: prev.segments.filter(segment => segment.id !== id)
    }));
  };

  return (
    <div className="h-full flex flex-col bg-slate-900">
      {/* Header */}
      <div className="bg-slate-800 border-b border-slate-700 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="text-2xl">🎙️</div>
            <div>
              <h2 className="text-xl font-bold text-white">Voice Generator</h2>
              <p className="text-sm text-slate-400">Advanced voice generation and synthesis</p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <select
              value={generationMode}
              onChange={(e) => setGenerationMode(e.target.value)}
              className="px-3 py-1 bg-slate-700 border border-slate-600 rounded text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="single">Single Voice</option>
              <option value="conversation">Conversation</option>
              <option value="emotional">Emotional Variants</option>
              <option value="podcast">Podcast</option>
            </select>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-auto p-4">
        <div className="grid grid-cols-12 gap-4 h-full">
          {/* Left Column - Generation Controls */}
          <div className="col-span-8 space-y-4">
            {/* Single Voice Generation */}
            {generationMode === 'single' && (
              <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
                <h3 className="text-lg font-semibold text-white mb-4">Single Voice Generation</h3>

                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-1">
                      Voice
                    </label>
                    <select
                      value={selectedVoice}
                      onChange={(e) => setSelectedVoice(e.target.value)}
                      className="w-full p-2 bg-slate-700 border border-slate-600 rounded text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      {voices.map(voice => (
                        <option key={voice.id} value={voice.id}>
                          {voice.name} ({voice.language})
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-1">
                      Style
                    </label>
                    <select
                      value={style}
                      onChange={(e) => setStyle(e.target.value)}
                      className="w-full p-2 bg-slate-700 border border-slate-600 rounded text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="conversational">Conversational</option>
                      <option value="professional">Professional</option>
                      <option value="emotional">Emotional</option>
                      <option value="narrative">Narrative</option>
                      <option value="news">News</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-1">
                      Emotion
                    </label>
                    <select
                      value={emotion}
                      onChange={(e) => setEmotion(e.target.value)}
                      className="w-full p-2 bg-slate-700 border border-slate-600 rounded text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="neutral">Neutral</option>
                      <option value="happy">Happy</option>
                      <option value="sad">Sad</option>
                      <option value="angry">Angry</option>
                      <option value="surprised">Surprised</option>
                      <option value="fearful">Fearful</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-1">
                      Speed
                    </label>
                    <select
                      value={speed}
                      onChange={(e) => setSpeed(e.target.value)}
                      className="w-full p-2 bg-slate-700 border border-slate-600 rounded text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="slow">Slow</option>
                      <option value="normal">Normal</option>
                      <option value="fast">Fast</option>
                    </select>
                  </div>
                </div>

                <div className="mb-4">
                  <label className="block text-sm font-medium text-slate-300 mb-1">
                    Text to Speech
                  </label>
                  <textarea
                    value={textInput}
                    onChange={(e) => setTextInput(e.target.value)}
                    placeholder="Enter text to convert to speech..."
                    className="w-full p-3 bg-slate-700 border border-slate-600 rounded text-white focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                    rows={6}
                  />
                </div>

                <button
                  onClick={handleSingleGeneration}
                  disabled={!textInput.trim()}
                  className="w-full py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-600 disabled:cursor-not-allowed rounded text-white font-medium transition-colors"
                >
                  Generate Voice
                </button>
              </div>
            )}

            {/* Conversation Generation */}
            {generationMode === 'conversation' && (
              <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-white">Multi-Speaker Conversation</h3>
                  <button
                    onClick={addConversationTurn}
                    className="px-3 py-1 bg-green-600 hover:bg-green-700 rounded text-white text-sm"
                  >
                    + Add Speaker
                  </button>
                </div>

                <DragDropContext onDragEnd={onDragEnd}>
                  <Droppable droppableId="conversation">
                    {(provided) => (
                      <div
                        {...provided.droppableProps}
                        ref={provided.innerRef}
                        className="space-y-3 mb-4"
                      >
                        {conversation.map((turn, index) => (
                          <Draggable key={turn.id} draggableId={turn.id.toString()} index={index}>
                            {(provided) => (
                              <div
                                ref={provided.innerRef}
                                {...provided.draggableProps}
                                {...provided.dragHandleProps}
                                className="bg-slate-700 rounded p-3"
                              >
                                <div className="flex items-center space-x-2 mb-2">
                                  <div className="text-slate-400">≡</div>
                                  <select
                                    value={turn.speaker}
                                    onChange={(e) => updateConversationTurn(turn.id, 'speaker', e.target.value)}
                                    className="flex-1 p-1 bg-slate-600 border border-slate-500 rounded text-white text-sm"
                                  >
                                    {voices.map(voice => (
                                      <option key={voice.id} value={voice.id}>
                                        {voice.name}
                                      </option>
                                    ))}
                                  </select>
                                  {conversation.length > 2 && (
                                    <button
                                      onClick={() => removeConversationTurn(turn.id)}
                                      className="text-red-400 hover:text-red-300"
                                    >
                                      ×
                                    </button>
                                  )}
                                </div>
                                <textarea
                                  value={turn.text}
                                  onChange={(e) => updateConversationTurn(turn.id, 'text', e.target.value)}
                                  placeholder="Enter dialogue..."
                                  className="w-full p-2 bg-slate-600 border border-slate-500 rounded text-white text-sm resize-none"
                                  rows={2}
                                />
                              </div>
                            )}
                          </Draggable>
                        ))}
                        {provided.placeholder}
                      </div>
                    )}
                  </Droppable>
                </DragDropContext>

                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-1">
                      Style
                    </label>
                    <select
                      value={style}
                      onChange={(e) => setStyle(e.target.value)}
                      className="w-full p-2 bg-slate-700 border border-slate-600 rounded text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="conversational">Conversational</option>
                      <option value="interview">Interview</option>
                      <option value="debate">Debate</option>
                      <option value="storytelling">Storytelling</option>
                    </select>
                  </div>
                </div>

                <button
                  onClick={handleConversationGeneration}
                  disabled={conversation.some(t => !t.text.trim())}
                  className="w-full py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-600 disabled:cursor-not-allowed rounded text-white font-medium transition-colors"
                >
                  Generate Conversation
                </button>
              </div>
            )}

            {/* Emotional Variants Generation */}
            {generationMode === 'emotional' && (
              <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
                <h3 className="text-lg font-semibold text-white mb-4">Emotional Voice Variants</h3>

                <div className="mb-4">
                  <label className="block text-sm font-medium text-slate-300 mb-1">
                    Base Text
                  </label>
                  <textarea
                    value={textInput}
                    onChange={(e) => setTextInput(e.target.value)}
                    placeholder="Enter text to generate with different emotions..."
                    className="w-full p-3 bg-slate-700 border border-slate-600 rounded text-white focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                    rows={4}
                  />
                </div>

                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-1">
                      Voice
                    </label>
                    <select
                      value={selectedVoice}
                      onChange={(e) => setSelectedVoice(e.target.value)}
                      className="w-full p-2 bg-slate-700 border border-slate-600 rounded text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      {voices.map(voice => (
                        <option key={voice.id} value={voice.id}>
                          {voice.name} ({voice.language})
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="mb-4">
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Emotional Variants
                  </label>
                  <div className="grid grid-cols-1 gap-2">
                    {emotionVariants.map(variant => (
                      <div key={variant.emotion} className="bg-slate-700 rounded p-3">
                        <div className="flex items-center justify-between mb-2">
                          <label className="flex items-center space-x-2">
                            <input
                              type="checkbox"
                              checked={variant.enabled}
                              onChange={() => toggleEmotionVariant(variant.emotion)}
                              className="rounded border-slate-500 text-blue-600 focus:ring-blue-500"
                            />
                            <span className="text-white capitalize">{variant.emotion}</span>
                          </label>
                          {variant.enabled && (
                            <div className="flex items-center space-x-2">
                              <input
                                type="range"
                                min="0"
                                max="1"
                                step="0.1"
                                value={variant.intensity}
                                onChange={(e) => updateEmotionIntensity(variant.emotion, parseFloat(e.target.value))}
                                className="w-20"
                              />
                              <span className="text-slate-300 text-sm">
                                {Math.round(variant.intensity * 100)}%
                              </span>
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <button
                  onClick={handleEmotionalVariantsGeneration}
                  disabled={!textInput.trim() || !emotionVariants.some(v => v.enabled)}
                  className="w-full py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-600 disabled:cursor-not-allowed rounded text-white font-medium transition-colors"
                >
                  Generate Emotional Variants
                </button>
              </div>
            )}

            {/* Podcast Generation */}
            {generationMode === 'podcast' && (
              <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-white">Podcast Episode</h3>
                  <button
                    onClick={() => addPodcastSegment('monologue')}
                    className="px-3 py-1 bg-green-600 hover:bg-green-700 rounded text-white text-sm"
                  >
                    + Add Segment
                  </button>
                </div>

                <div className="mb-4">
                  <label className="block text-sm font-medium text-slate-300 mb-1">
                    Podcast Title
                  </label>
                  <input
                    type="text"
                    value={podcastStructure.title}
                    onChange={(e) => setPodcastStructure(prev => ({ ...prev, title: e.target.value }))}
                    className="w-full p-2 bg-slate-700 border border-slate-600 rounded text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Enter podcast title..."
                  />
                </div>

                <div className="mb-4">
                  <label className="block text-sm font-medium text-slate-300 mb-1">
                    Introduction
                  </label>
                  <textarea
                    value={podcastStructure.intro.text}
                    onChange={(e) => setPodcastStructure(prev => ({
                      ...prev,
                      intro: { ...prev.intro, text: e.target.value }
                    }))}
                    placeholder="Welcome to our podcast..."
                    className="w-full p-2 bg-slate-700 border border-slate-600 rounded text-white focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                    rows={2}
                  />
                </div>

                <div className="mb-4">
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Segments
                  </label>
                  <div className="space-y-3 max-h-60 overflow-y-auto">
                    {podcastStructure.segments.map(segment => (
                      <div key={segment.id} className="bg-slate-700 rounded p-3">
                        <div className="flex items-center justify-between mb-2">
                          <input
                            type="text"
                            value={segment.title}
                            onChange={(e) => updatePodcastSegment(segment.id, 'title', e.target.value)}
                            className="flex-1 p-1 bg-slate-600 border border-slate-500 rounded text-white text-sm mr-2"
                            placeholder="Segment title..."
                          />
                          <button
                            onClick={() => removePodcastSegment(segment.id)}
                            className="text-red-400 hover:text-red-300"
                          >
                            ×
                          </button>
                        </div>

                        {segment.type === 'monologue' && (
                          <textarea
                            value={segment.text}
                            onChange={(e) => updatePodcastSegment(segment.id, 'text', e.target.value)}
                            placeholder="Monologue content..."
                            className="w-full p-2 bg-slate-600 border border-slate-500 rounded text-white text-sm resize-none"
                            rows={3}
                          />
                        )}

                        {segment.type === 'interview' && (
                          <div className="space-y-2">
                            {segment.conversation?.map((turn, idx) => (
                              <div key={idx} className="flex items-center space-x-2">
                                <select
                                  value={turn.speaker}
                                  onChange={(e) => {
                                    const newConversation = [...segment.conversation];
                                    newConversation[idx].speaker = e.target.value;
                                    updatePodcastSegment(segment.id, 'conversation', newConversation);
                                  }}
                                  className="p-1 bg-slate-600 border border-slate-500 rounded text-white text-xs"
                                >
                                  <option value="host">Host</option>
                                  <option value="guest">Guest</option>
                                </select>
                                <input
                                  type="text"
                                  value={turn.text}
                                  onChange={(e) => {
                                    const newConversation = [...segment.conversation];
                                    newConversation[idx].text = e.target.value;
                                    updatePodcastSegment(segment.id, 'conversation', newConversation);
                                  }}
                                  placeholder="Dialogue..."
                                  className="flex-1 p-1 bg-slate-600 border border-slate-500 rounded text-white text-sm"
                                />
                              </div>
                            ))}
                            <button
                              onClick={() => {
                                const newConversation = [...(segment.conversation || []), { speaker: 'host', text: '' }];
                                updatePodcastSegment(segment.id, 'conversation', newConversation);
                              }}
                              className="text-xs text-blue-400 hover:text-blue-300"
                            >
                              + Add Turn
                            </button>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>

                <div className="mb-4">
                  <label className="block text-sm font-medium text-slate-300 mb-1">
                    Outro
                  </label>
                  <textarea
                    value={podcastStructure.outro.text}
                    onChange={(e) => setPodcastStructure(prev => ({
                      ...prev,
                      outro: { ...prev.outro, text: e.target.value }
                    }))}
                    placeholder="Thanks for listening..."
                    className="w-full p-2 bg-slate-700 border border-slate-600 rounded text-white focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                    rows={2}
                  />
                </div>

                <button
                  onClick={handlePodcastGeneration}
                  className="w-full py-2 bg-blue-600 hover:bg-blue-700 rounded text-white font-medium transition-colors"
                >
                  Generate Podcast Episode
                </button>
              </div>
            )}
          </div>

          {/* Right Column - Generated Audio */}
          <div className="col-span-4 space-y-4">
            <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-white">Generated Audio</h3>
                <span className="text-sm text-slate-400">
                  {generatedAudio.length} files
                </span>
              </div>

              <div className="space-y-3 max-h-96 overflow-y-auto">
                {generatedAudio.length === 0 ? (
                  <p className="text-slate-400 text-center py-8">
                    No audio generated yet
                  </p>
                ) : (
                  generatedAudio.map(audio => (
                    <div key={audio.id} className="bg-slate-700 rounded p-3">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex-1">
                          <div className="text-sm font-medium text-white">
                            {audio.title || `${audio.type} generation`}
                          </div>
                          <div className="text-xs text-slate-400">
                            {audio.speaker && `Voice: ${audio.speaker}`}
                            {audio.emotion && ` • Emotion: ${audio.emotion}`}
                            {audio.duration && ` • Duration: ${audio.duration}s`}
                          </div>
                        </div>
                        <div className="flex items-center space-x-1">
                          <button
                            onClick={() => playAudio(audio.audioUrl, audio.id)}
                            disabled={currentlyPlaying === audio.id}
                            className={`p-1 rounded ${
                              currentlyPlaying === audio.id ? 'bg-red-600' : 'bg-blue-600 hover:bg-blue-700'
                            } text-white`}
                          >
                            {currentlyPlaying === audio.id ? '⏸️' : '▶️'}
                          </button>
                          <button
                            onClick={() => downloadAudio(audio.audioUrl, `${audio.type}_${audio.id}.wav`)}
                            className="p-1 bg-green-600 hover:bg-green-700 rounded text-white"
                          >
                            💾
                          </button>
                        </div>
                      </div>
                      {audio.text && (
                        <p className="text-xs text-slate-400 mt-2 line-clamp-2">
                          {audio.text}
                        </p>
                      )}
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Audio Player */}
            {currentlyPlaying && (
              <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
                <h3 className="text-lg font-semibold text-white mb-3">Now Playing</h3>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={stopAudio}
                    className="p-2 bg-red-600 hover:bg-red-700 rounded text-white"
                  >
                    ⏹️
                  </button>
                  <div className="flex-1">
                    <div className="text-sm text-white">Audio playback</div>
                    <div className="text-xs text-slate-400">Click stop to end playback</div>
                  </div>
                </div>
              </div>
            )}

            {/* Export Options */}
            <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
              <h3 className="text-lg font-semibold text-white mb-3">Export Options</h3>
              <div className="space-y-2">
                <button
                  onClick={() => {
                    // Export all audio files
                    generatedAudio.forEach(audio => {
                      downloadAudio(audio.audioUrl, `${audio.type}_${audio.id}.wav`);
                    });
                  }}
                  disabled={generatedAudio.length === 0}
                  className="w-full py-2 bg-green-600 hover:bg-green-700 disabled:bg-slate-600 disabled:cursor-not-allowed rounded text-white text-sm"
                >
                  Export All Audio Files
                </button>
                <button
                  onClick={() => {
                    // Create project file
                    const projectData = {
                      generatedAudio,
                      settings: {
                        selectedVoice,
                        style,
                        emotion,
                        speed
                      },
                      created: new Date().toISOString()
                    };
                    const blob = new Blob([JSON.stringify(projectData, null, 2)], { type: 'application/json' });
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = 'voice_generator_project.json';
                    a.click();
                    URL.revokeObjectURL(url);
                  }}
                  disabled={generatedAudio.length === 0}
                  className="w-full py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-600 disabled:cursor-not-allowed rounded text-white text-sm"
                >
                  Save Project
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default VoiceGenerator;