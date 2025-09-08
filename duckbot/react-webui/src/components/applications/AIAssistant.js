import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAI } from '../../contexts/AIContext';
import { useAuth } from '../../contexts/AuthContext';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import toast from 'react-hot-toast';

const AIAssistant = ({ onClose }) => {
  const { 
    currentModel, 
    isThinking, 
    conversations, 
    activeConversation, 
    sendMessage, 
    createNewConversation,
    models 
  } = useAI();
  const { apiCall } = useAuth();

  // Local state
  const [message, setMessage] = useState('');
  const [taskKind, setTaskKind] = useState('auto');
  const [riskLevel, setRiskLevel] = useState('low');
  const [conversation, setConversation] = useState([]);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [streamingResponse, setStreamingResponse] = useState('');
  
  // RAG and Knowledge Base
  const [ragQuery, setRagQuery] = useState('');
  const [ragResults, setRagResults] = useState(null);
  const [showRAG, setShowRAG] = useState(false);
  
  // Voice and TTS
  const [enableTTS, setEnableTTS] = useState(false);
  const [voiceScript, setVoiceScript] = useState('');
  const [selectedVoice, setSelectedVoice] = useState('default');
  
  // Settings from original WebUI
  const [enhancedMode, setEnhancedMode] = useState(true);
  const [contextLength, setContextLength] = useState(4096);
  
  // Refs
  const messagesEndRef = useRef(null);
  const messageInputRef = useRef(null);

  // Task types from original DuckBot WebUI
  const taskTypes = [
    { value: 'auto', label: '🤖 Auto (Intelligent Routing)', description: 'Let DuckBot choose the best approach' },
    { value: 'code', label: '💻 Code Analysis', description: 'Programming and code-related tasks' },
    { value: 'reasoning', label: '🧠 Reasoning', description: 'Complex problem-solving and analysis' },
    { value: 'summary', label: '📝 Summary', description: 'Summarization and key points' },
    { value: 'long_form', label: '📄 Long-form', description: 'Detailed explanations and content' },
    { value: 'json_format', label: '🔧 JSON Format', description: 'Structured data responses' },
    { value: 'policy', label: '⚖️ Policy', description: 'Compliance and policy analysis' },
    { value: 'arbiter', label: '⚡ Arbiter', description: 'Comparison and decision making' },
    { value: 'status', label: '📊 Status', description: 'System status and quick responses' }
  ];

  const riskLevels = [
    { value: 'low', label: '🟢 Low Risk', description: 'Safe operations only' },
    { value: 'medium', label: '🟡 Medium Risk', description: 'Limited system operations' },
    { value: 'high', label: '🔴 High Risk', description: 'Full system access allowed' }
  ];

  const voices = [
    { value: 'default', label: 'Default Voice' },
    { value: 'alloy', label: 'Alloy (Professional)' },
    { value: 'echo', label: 'Echo (Warm)' },
    { value: 'fable', label: 'Fable (Friendly)' },
    { value: 'onyx', label: 'Onyx (Deep)' },
    { value: 'nova', label: 'Nova (Energetic)' },
    { value: 'shimmer', label: 'Shimmer (Gentle)' }
  ];

  useEffect(() => {
    scrollToBottom();
  }, [conversation, streamingResponse]);

  useEffect(() => {
    // Load conversation from active conversation
    if (activeConversation) {
      setConversation(activeConversation.messages || []);
    }
  }, [activeConversation]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // Main chat function - integrates all original WebUI features
  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!message.trim() || isThinking) return;

    const userMessage = {
      role: 'user',
      content: message.trim(),
      timestamp: new Date(),
      taskKind,
      riskLevel
    };

    setConversation(prev => [...prev, userMessage]);
    const currentMessage = message;
    setMessage('');

    try {
      // Use the AI context's sendMessage with full DuckBot integration
      const response = await sendMessage(currentMessage, {
        kind: taskKind,
        risk: riskLevel,
        enhanced: enhancedMode,
        context: {
          contextLength,
          enableTTS,
          voice: selectedVoice
        }
      });

      if (response) {
        const aiMessage = {
          role: 'assistant',
          content: response,
          timestamp: new Date(),
          model: currentModel?.name || 'Unknown',
          taskKind,
          riskLevel
        };
        setConversation(prev => [...prev, aiMessage]);

        // Handle TTS if enabled
        if (enableTTS && response) {
          handleTTS(response);
        }
      }
    } catch (error) {
      console.error('Chat error:', error);
      const errorMessage = {
        role: 'system',
        content: `Error: ${error.message}`,
        timestamp: new Date(),
        isError: true
      };
      setConversation(prev => [...prev, errorMessage]);
    }
  };

  // RAG Search function from original WebUI
  const handleRAGSearch = async () => {
    if (!ragQuery.trim()) return;

    try {
      const response = await apiCall('/api/rag/search', {
        method: 'POST',
        body: JSON.stringify({
          q: ragQuery,
          top_k: 10
        })
      });

      if (response.ok) {
        const results = await response.json();
        setRagResults(results);
        toast.success('RAG search completed');
      } else {
        toast.error('RAG search failed');
      }
    } catch (error) {
      console.error('RAG search error:', error);
      toast.error('RAG search error');
    }
  };

  // Voice/TTS function from original WebUI
  const handleTTS = async (text) => {
    try {
      const response = await apiCall('/api/voice/synthesize', {
        method: 'POST',
        body: JSON.stringify({
          text: text.substring(0, 1000), // Limit text length
          voice: selectedVoice
        })
      });

      if (response.ok) {
        const audioBlob = await response.blob();
        const audioUrl = URL.createObjectURL(audioBlob);
        const audio = new Audio(audioUrl);
        audio.play();
        toast.success('Voice synthesis completed');
      }
    } catch (error) {
      console.error('TTS error:', error);
      toast.error('Voice synthesis failed');
    }
  };

  // Voice script generation from original WebUI
  const handleVoiceScript = async () => {
    if (!voiceScript.trim()) return;

    try {
      const response = await apiCall('/api/voice/script', {
        method: 'POST',
        body: JSON.stringify({
          script: voiceScript,
          voice: selectedVoice
        })
      });

      if (response.ok) {
        const result = await response.json();
        toast.success('Voice script generated');
        
        // Add to conversation
        const scriptMessage = {
          role: 'assistant',
          content: result.enhanced_script || result.script,
          timestamp: new Date(),
          isVoiceScript: true
        };
        setConversation(prev => [...prev, scriptMessage]);
      }
    } catch (error) {
      console.error('Voice script error:', error);
      toast.error('Voice script generation failed');
    }
  };

  // Clear conversation
  const handleClearConversation = () => {
    setConversation([]);
    createNewConversation();
    toast.success('Conversation cleared');
  };

  // Export conversation
  const handleExportConversation = () => {
    const exportData = {
      conversation,
      model: currentModel?.name,
      timestamp: new Date().toISOString(),
      settings: {
        taskKind,
        riskLevel,
        enhancedMode,
        contextLength
      }
    };

    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `duckbot-conversation-${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success('Conversation exported');
  };

  return (
    <div className="ai-assistant h-full flex flex-col bg-slate-900">
      {/* Header */}
      <div className="flex-shrink-0 bg-slate-800 p-4 border-b border-slate-700">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="text-2xl">🤖</div>
            <div>
              <h2 className="text-lg font-semibold text-white">AI Assistant</h2>
              <div className="text-xs text-slate-400">
                Model: {currentModel?.name || 'None'} | 
                Task: {taskTypes.find(t => t.value === taskKind)?.label} |
                Risk: {riskLevels.find(r => r.value === riskLevel)?.label}
              </div>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setShowAdvanced(!showAdvanced)}
              className={`btn-secondary text-xs ${showAdvanced ? 'bg-blue-500/20' : ''}`}
            >
              ⚙️ Advanced
            </button>
            <button
              onClick={() => setShowRAG(!showRAG)}
              className={`btn-secondary text-xs ${showRAG ? 'bg-green-500/20' : ''}`}
            >
              📚 RAG
            </button>
            <button
              onClick={handleClearConversation}
              className="btn-secondary text-xs text-orange-400"
            >
              🗑️ Clear
            </button>
          </div>
        </div>

        {/* Advanced Settings */}
        <AnimatePresence>
          {showAdvanced && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="mt-4 p-4 bg-slate-700/50 rounded-lg space-y-3"
            >
              <div className="grid grid-cols-2 gap-4">
                {/* Task Type */}
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Task Type</label>
                  <select
                    value={taskKind}
                    onChange={(e) => setTaskKind(e.target.value)}
                    className="w-full bg-slate-600 border border-slate-500 rounded px-2 py-1 text-xs text-white"
                  >
                    {taskTypes.map(type => (
                      <option key={type.value} value={type.value}>
                        {type.label}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Risk Level */}
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Risk Level</label>
                  <select
                    value={riskLevel}
                    onChange={(e) => setRiskLevel(e.target.value)}
                    className="w-full bg-slate-600 border border-slate-500 rounded px-2 py-1 text-xs text-white"
                  >
                    {riskLevels.map(risk => (
                      <option key={risk.value} value={risk.value}>
                        {risk.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4">
                {/* Enhanced Mode */}
                <div>
                  <label className="flex items-center space-x-2 text-xs text-slate-300">
                    <input
                      type="checkbox"
                      checked={enhancedMode}
                      onChange={(e) => setEnhancedMode(e.target.checked)}
                      className="rounded"
                    />
                    <span>Enhanced Mode</span>
                  </label>
                </div>

                {/* TTS */}
                <div>
                  <label className="flex items-center space-x-2 text-xs text-slate-300">
                    <input
                      type="checkbox"
                      checked={enableTTS}
                      onChange={(e) => setEnableTTS(e.target.checked)}
                      className="rounded"
                    />
                    <span>Text-to-Speech</span>
                  </label>
                </div>

                {/* Voice Selection */}
                {enableTTS && (
                  <div>
                    <select
                      value={selectedVoice}
                      onChange={(e) => setSelectedVoice(e.target.value)}
                      className="w-full bg-slate-600 border border-slate-500 rounded px-2 py-1 text-xs text-white"
                    >
                      {voices.map(voice => (
                        <option key={voice.value} value={voice.value}>
                          {voice.label}
                        </option>
                      ))}
                    </select>
                  </div>
                )}
              </div>

              {/* Voice Script Generator */}
              {enableTTS && (
                <div className="border-t border-slate-600 pt-3">
                  <label className="block text-xs font-medium text-slate-300 mb-1">Voice Script Generator</label>
                  <div className="flex space-x-2">
                    <input
                      type="text"
                      value={voiceScript}
                      onChange={(e) => setVoiceScript(e.target.value)}
                      placeholder="Enter script for voice generation..."
                      className="flex-1 bg-slate-600 border border-slate-500 rounded px-2 py-1 text-xs text-white"
                    />
                    <button
                      onClick={handleVoiceScript}
                      className="btn-primary text-xs px-3"
                    >
                      Generate
                    </button>
                  </div>
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>

        {/* RAG Search */}
        <AnimatePresence>
          {showRAG && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="mt-4 p-4 bg-green-500/10 rounded-lg border border-green-500/30"
            >
              <div className="flex items-center space-x-2 mb-3">
                <span className="text-sm font-medium text-green-400">📚 RAG Knowledge Search</span>
              </div>
              
              <div className="flex space-x-2">
                <input
                  type="text"
                  value={ragQuery}
                  onChange={(e) => setRagQuery(e.target.value)}
                  placeholder="Search knowledge base..."
                  className="flex-1 bg-slate-600 border border-slate-500 rounded px-3 py-1 text-sm text-white"
                  onKeyPress={(e) => e.key === 'Enter' && handleRAGSearch()}
                />
                <button
                  onClick={handleRAGSearch}
                  className="btn-primary text-sm px-4"
                >
                  Search
                </button>
              </div>

              {/* RAG Results */}
              {ragResults && (
                <div className="mt-3 max-h-32 overflow-y-auto">
                  <div className="text-xs text-green-400 mb-2">
                    Found {ragResults.results?.length || 0} results
                  </div>
                  {ragResults.results?.map((result, index) => (
                    <div key={index} className="mb-2 p-2 bg-slate-800/50 rounded text-xs">
                      <div className="text-slate-300 mb-1">
                        {result.metadata?.source || 'Unknown source'}
                      </div>
                      <div className="text-slate-400">
                        {result.content?.substring(0, 150)}...
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {conversation.length === 0 && (
          <div className="text-center text-slate-400 mt-8">
            <div className="text-4xl mb-4">🤖</div>
            <h3 className="text-lg font-semibold mb-2">Welcome to DuckBot AI Assistant</h3>
            <p className="text-sm mb-4">
              Integrated with all DuckBot WebUI features including RAG, TTS, and advanced task routing.
            </p>
            <div className="grid grid-cols-2 gap-2 text-xs max-w-md mx-auto">
              <div className="bg-slate-800/50 p-2 rounded">💻 Code Analysis</div>
              <div className="bg-slate-800/50 p-2 rounded">🧠 Reasoning Tasks</div>
              <div className="bg-slate-800/50 p-2 rounded">📚 RAG Search</div>
              <div className="bg-slate-800/50 p-2 rounded">🔊 Voice Synthesis</div>
            </div>
          </div>
        )}

        {conversation.map((msg, index) => (
          <MessageBubble key={index} message={msg} />
        ))}

        {isThinking && (
          <div className="flex items-center space-x-2 text-slate-400">
            <div className="flex space-x-1">
              {[...Array(3)].map((_, i) => (
                <motion.div
                  key={i}
                  className="w-2 h-2 bg-blue-400 rounded-full"
                  animate={{
                    scale: [1, 1.5, 1],
                    opacity: [0.5, 1, 0.5],
                  }}
                  transition={{
                    duration: 1,
                    repeat: Infinity,
                    delay: i * 0.2,
                  }}
                />
              ))}
            </div>
            <span className="text-sm">DuckBot is thinking...</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="flex-shrink-0 bg-slate-800 p-4 border-t border-slate-700">
        <form onSubmit={handleSendMessage} className="flex space-x-2">
          <input
            ref={messageInputRef}
            type="text"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Ask DuckBot anything... (supports all WebUI features)"
            className="flex-1 input-field"
            disabled={isThinking}
          />
          <button
            type="submit"
            disabled={isThinking || !message.trim()}
            className="btn-primary px-6 disabled:opacity-50"
          >
            {isThinking ? '⏳' : '🚀'} Send
          </button>
          <button
            type="button"
            onClick={handleExportConversation}
            className="btn-secondary"
            title="Export Conversation"
          >
            📥
          </button>
        </form>
        
        <div className="mt-2 text-xs text-slate-400 text-center">
          Task: {taskTypes.find(t => t.value === taskKind)?.description} | 
          Risk: {riskLevels.find(r => r.value === riskLevel)?.description} |
          Model: {currentModel?.name || 'Not selected'}
        </div>
      </div>
    </div>
  );
};

// Message Bubble Component
const MessageBubble = ({ message }) => {
  const isUser = message.role === 'user';
  const isSystem = message.role === 'system';
  const isError = message.isError;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}
    >
      <div
        className={`max-w-2xl px-4 py-3 rounded-lg ${
          isUser
            ? 'bg-blue-600 text-white'
            : isSystem
            ? isError
              ? 'bg-red-500/20 border border-red-500 text-red-300'
              : 'bg-slate-700 text-slate-300'
            : 'bg-slate-700 text-white'
        }`}
      >
        {/* Message Header */}
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center space-x-2">
            <span className="text-xs font-semibold">
              {isUser ? '👤 You' : isSystem ? '🔧 System' : '🤖 DuckBot'}
            </span>
            {message.taskKind && (
              <span className="text-xs bg-slate-600 px-2 py-1 rounded">
                {message.taskKind}
              </span>
            )}
            {message.model && (
              <span className="text-xs bg-blue-500/30 px-2 py-1 rounded">
                {message.model}
              </span>
            )}
          </div>
          <span className="text-xs opacity-60">
            {message.timestamp?.toLocaleTimeString()}
          </span>
        </div>

        {/* Message Content */}
        <div className="prose prose-sm max-w-none text-white">
          {isSystem ? (
            <pre className="whitespace-pre-wrap text-xs">{message.content}</pre>
          ) : (
            <ReactMarkdown
              components={{
                code({ node, inline, className, children, ...props }) {
                  const match = /language-(\w+)/.exec(className || '');
                  return !inline && match ? (
                    <SyntaxHighlighter
                      style={oneDark}
                      language={match[1]}
                      PreTag="div"
                      {...props}
                    >
                      {String(children).replace(/\n$/, '')}
                    </SyntaxHighlighter>
                  ) : (
                    <code className="bg-slate-600 px-1 py-0.5 rounded text-sm" {...props}>
                      {children}
                    </code>
                  );
                }
              }}
            >
              {message.content}
            </ReactMarkdown>
          )}
        </div>

        {/* Voice Script Indicator */}
        {message.isVoiceScript && (
          <div className="mt-2 text-xs text-blue-400 flex items-center space-x-1">
            <span>🔊</span>
            <span>Voice Script Generated</span>
          </div>
        )}
      </div>
    </motion.div>
  );
};

export default AIAssistant;