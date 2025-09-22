import React, { useState, useRef, useEffect } from 'react';
import { Send, Mic, Volume2, VolumeX, Settings, MoreVertical, Bot, User } from 'lucide-react';

interface Message {
  id: string;
  text: string;
  sender: 'user' | 'ai';
  timestamp: Date;
}

interface ChatUIAppProps {
  onSend: (message: string) => void;
  isLoading?: boolean;
  isListening?: boolean;
  onMicClick?: () => void;
  onSettingsClick?: () => void;
  onMinimizeClick?: () => void;
  connectionStatus?: string;
  currentProvider?: string;
  className?: string;
}

const ChatUIApp: React.FC<ChatUIAppProps> = ({
  onSend,
  isLoading = false,
  isListening = false,
  onMicClick,
  onSettingsClick,
  onMinimizeClick,
  connectionStatus = 'disconnected',
  currentProvider = 'duckbot',
  className = ''
}) => {
  const [message, setMessage] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [isMuted, setIsMuted] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Add welcome message
  useEffect(() => {
    if (messages.length === 0) {
      setMessages([{
        id: '1',
        text: "Hello! I'm DuckBot, your AI assistant. How can I help you today?",
        sender: 'ai',
        timestamp: new Date()
      }]);
    }
  }, [messages.length]);

  const handleSend = async () => {
    if (!message.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      text: message,
      sender: 'user',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    const messageToSend = message;
    setMessage('');

    try {
      await onSend(messageToSend);

      // Simulate AI response (in real implementation, this would come from the parent)
      setTimeout(() => {
        const aiMessage: Message = {
          id: (Date.now() + 1).toString(),
          text: `I understand you said: "${messageToSend}". This is a simulated response - in the full implementation, this would connect to the actual DuckBot AI service.`,
          sender: 'ai',
          timestamp: new Date()
        };
        setMessages(prev => [...prev, aiMessage]);
      }, 1000);
    } catch (error) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: `Sorry, there was an error processing your request: ${error instanceof Error ? error.message : 'Unknown error'}`,
        sender: 'ai',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className={`w-full h-full flex flex-col bg-gray-900 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-700 bg-gray-800/50 backdrop-blur-sm">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-500 rounded-lg flex items-center justify-center">
            <Bot className="w-5 h-5 text-white" />
          </div>
          <div>
            <h2 className="text-white font-semibold">DuckBot Chat</h2>
            <div className="flex items-center space-x-2">
              <div className={`w-2 h-2 rounded-full ${
                connectionStatus === 'connected' ? 'bg-green-400' :
                connectionStatus === 'connecting' ? 'bg-yellow-400' : 'bg-red-400'
              }`} />
              <span className="text-xs text-gray-400">
                {currentProvider} • {connectionStatus}
              </span>
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => setIsMuted(!isMuted)}
            className="p-2 rounded-lg hover:bg-gray-700/50 transition-colors"
            title={isMuted ? "Unmute" : "Mute"}
          >
            {isMuted ? <VolumeX className="w-4 h-4 text-gray-400" /> : <Volume2 className="w-4 h-4 text-gray-400" />}
          </button>
          {onSettingsClick && (
            <button
              onClick={onSettingsClick}
              className="p-2 rounded-lg hover:bg-gray-700/50 transition-colors"
              title="Settings"
            >
              <Settings className="w-4 h-4 text-gray-400" />
            </button>
          )}
          {onMinimizeClick && (
            <button
              onClick={onMinimizeClick}
              className="p-2 rounded-lg hover:bg-gray-700/50 transition-colors"
              title="Minimize"
            >
              <MoreVertical className="w-4 h-4 text-gray-400" />
            </button>
          )}
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-grow overflow-y-auto p-4 space-y-4">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[70%] rounded-lg px-4 py-3 ${
                msg.sender === 'user'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-800 text-gray-100'
              }`}
            >
              <div className="flex items-center space-x-2 mb-1">
                {msg.sender === 'ai' ? (
                  <Bot className="w-4 h-4 text-blue-400" />
                ) : (
                  <User className="w-4 h-4 text-gray-400" />
                )}
                <span className="text-xs opacity-70">
                  {msg.sender === 'ai' ? 'DuckBot' : 'You'} • {formatTime(msg.timestamp)}
                </span>
              </div>
              <div className="text-sm whitespace-pre-wrap">{msg.text}</div>
            </div>
          </div>
        ))}

        {/* Loading indicator */}
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-gray-800 rounded-lg px-4 py-3">
              <div className="flex items-center space-x-2">
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
                <span className="text-sm text-gray-400">DuckBot is thinking...</span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-4 border-t border-gray-700 bg-gray-800/50 backdrop-blur-sm">
        <div className="flex items-end space-x-2">
          <div className="flex-grow relative">
            <textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type your message..."
              className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              rows={1}
              disabled={isLoading}
              style={{ minHeight: '44px', maxHeight: '120px' }}
            />
          </div>

          <div className="flex items-center space-x-2">
            {onMicClick && (
              <button
                onClick={onMicClick}
                disabled={isLoading}
                className={`p-3 rounded-lg transition-colors ${
                  isListening
                    ? 'bg-red-600 hover:bg-red-700 text-white'
                    : isLoading
                    ? 'bg-gray-700 text-gray-500 cursor-not-allowed'
                    : 'bg-gray-700 hover:bg-gray-600 text-gray-300'
                }`}
                title={isListening ? "Stop listening" : "Voice input"}
              >
                <Mic className="w-5 h-5" />
              </button>
            )}

            <button
              onClick={handleSend}
              disabled={!message.trim() || isLoading}
              className={`p-3 rounded-lg transition-colors ${
                !message.trim() || isLoading
                  ? 'bg-gray-700 text-gray-500 cursor-not-allowed'
                  : 'bg-blue-600 hover:bg-blue-700 text-white'
              }`}
              title="Send message"
            >
              <Send className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="flex items-center justify-between mt-2">
          <div className="flex items-center space-x-2">
            <span className="text-xs text-gray-500">Quick actions:</span>
            <button
              onClick={() => setMessage("Help me with coding")}
              className="text-xs text-blue-400 hover:text-blue-300 transition-colors"
            >
              Coding
            </button>
            <button
              onClick={() => setMessage("Generate an image")}
              className="text-xs text-blue-400 hover:text-blue-300 transition-colors"
            >
              Generate Image
            </button>
            <button
              onClick={() => setMessage("Check system status")}
              className="text-xs text-blue-400 hover:text-blue-300 transition-colors"
            >
              System Status
            </button>
          </div>

          <div className="text-xs text-gray-500">
            Press Enter to send, Shift+Enter for new line
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatUIApp;