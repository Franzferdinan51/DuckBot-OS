import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { Send, Mic, MicOff, Settings, Trash2, Download, Bot, User, Sparkles } from 'lucide-react';

interface Message {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  isGenerating?: boolean;
  model?: string;
}

interface GeminiChatProps {
  onClose?: () => void;
  onMinimize?: () => void;
  onMaximize?: () => void;
}

const GeminiChat: React.FC<GeminiChatProps> = ({ onClose, onMinimize, onMaximize }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [model, setModel] = useState('gemini-2.0-flash');
  const [systemPrompt, setSystemPrompt] = useState('You are Gemini, a helpful AI assistant integrated with DuckBotOS. Be concise, helpful, and engaging.');
  const [temperature, setTemperature] = useState(0.7);
  const [maxTokens, setMaxTokens] = useState(2048);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!inputMessage.trim()) return;

    const userMessage: Message = {
      role: 'user',
      content: inputMessage,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    // Simulate AI response (replace with actual Gemini API call)
    setTimeout(() => {
      const assistantMessage: Message = {
        role: 'assistant',
        content: 'I understand your message. This is a placeholder response as the Gemini integration needs to be configured with your API key.',
        timestamp: new Date(),
        isGenerating: false,
        model: model,
      };

      setMessages(prev => [...prev, assistantMessage]);
      setIsLoading(false);
    }, 1000);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const clearChat = () => {
    setMessages([]);
  };

  const exportChat = () => {
    const chatData = messages.map(msg =>
      `${msg.role.toUpperCase()} [${msg.timestamp.toLocaleString()}]:\n${msg.content}`
    ).join('\n\n');

    const blob = new Blob([chatData], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `gemini-chat-${new Date().toISOString().split('T')[0]}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.9 }}
      className="fixed inset-4 bg-gray-900 rounded-lg shadow-2xl border border-gray-700 flex flex-col z-50"
    >
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-700">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
            <Bot className="w-5 h-5 text-white" />
          </div>
          <div>
            <h2 className="text-white font-semibold">Gemini Chat</h2>
            <p className="text-gray-400 text-sm">AI Assistant</p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={clearChat}
            className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
            title="Clear Chat"
          >
            <Trash2 className="w-4 h-4 text-gray-400" />
          </button>
          <button
            onClick={exportChat}
            className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
            title="Export Chat"
          >
            <Download className="w-4 h-4 text-gray-400" />
          </button>
          <button
            onClick={onMinimize}
            className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
            title="Minimize"
          >
            <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
            </svg>
          </button>
          <button
            onClick={onClose}
            className="p-2 hover:bg-red-500 rounded-lg transition-colors"
            title="Close"
          >
            <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        <AnimatePresence>
          {messages.length === 0 && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="text-center text-gray-400 py-8"
            >
              <Sparkles className="w-12 h-12 mx-auto mb-4 text-blue-500" />
              <h3 className="text-lg font-semibold mb-2">Welcome to Gemini Chat</h3>
              <p>Start a conversation with the AI assistant</p>
            </motion.div>
          )}

          {messages.map((message, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[80%] rounded-lg p-3 ${
                  message.role === 'user'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-800 text-gray-100'
                }`}
              >
                <div className="flex items-center space-x-2 mb-1">
                  {message.role === 'user' ? (
                    <User className="w-4 h-4" />
                  ) : (
                    <Bot className="w-4 h-4" />
                  )}
                  <span className="text-xs opacity-75">
                    {message.role === 'user' ? 'You' : 'Gemini'}
                  </span>
                  <span className="text-xs opacity-50">
                    {message.timestamp.toLocaleTimeString()}
                  </span>
                </div>
                <div className="text-sm">
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
                          <code className={className} {...props}>
                            {children}
                          </code>
                        );
                      },
                    }}
                  >
                    {message.content}
                  </ReactMarkdown>
                </div>
              </div>
            </motion.div>
          ))}

          {isLoading && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex justify-start"
            >
              <div className="bg-gray-800 rounded-lg p-3">
                <div className="flex items-center space-x-2">
                  <Bot className="w-4 h-4 text-blue-500" />
                  <span className="text-sm text-gray-300">Gemini is thinking...</span>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-4 border-t border-gray-700">
        <div className="flex items-end space-x-2">
          <div className="flex-1">
            <textarea
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type your message..."
              className="w-full bg-gray-800 text-white rounded-lg px-4 py-2 pr-12 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
              rows={1}
              disabled={isLoading}
            />
          </div>
          <button
            onClick={() => setIsListening(!isListening)}
            className={`p-2 rounded-lg transition-colors ${
              isListening ? 'bg-red-500 text-white' : 'bg-gray-700 text-gray-400 hover:bg-gray-600'
            }`}
            disabled={isLoading}
          >
            {isListening ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
          </button>
          <button
            onClick={handleSend}
            disabled={!inputMessage.trim() || isLoading}
            className="p-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
      </div>
    </motion.div>
  );
};

export default GeminiChat;