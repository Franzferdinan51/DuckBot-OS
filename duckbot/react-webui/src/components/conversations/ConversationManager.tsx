import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useTheme } from '../../theme/ThemeContext';
import { Conversation, Message } from '../../types/dashboard';
import {
  MessageSquare,
  Search,
  Filter,
  Tag,
  Clock,
  Pin,
  MoreVertical,
  Trash2,
  Star,
  Download,
  Brain,
  Database,
  BarChart3,
  RefreshCw,
  Plus,
  Eye,
  Edit
} from 'lucide-react';

interface ConversationManagerProps {
  conversations?: Conversation[];
  onConversationSelect?: (conversationId: string) => void;
  onConversationDelete?: (conversationId: string) => void;
  onConversationPin?: (conversationId: string) => void;
  autoRefresh?: boolean;
  refreshInterval?: number;
}

const ConversationManager: React.FC<ConversationManagerProps> = ({
  conversations: initialConversations,
  onConversationSelect,
  onConversationDelete,
  onConversationPin,
  autoRefresh = true,
  refreshInterval = 5000,
}) => {
  const { colors } = useTheme();
  const [conversations, setConversations] = useState<Conversation[]>(initialConversations || mockConversations);
  const [selectedConversation, setSelectedConversation] = useState<Conversation | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [tagFilter, setTagFilter] = useState<string>('');
  const [sortBy, setSortBy] = useState<'recent' | 'name' | 'duration'>('recent');
  const [showPinnedOnly, setShowPinnedOnly] = useState(false);
  const [loading, setLoading] = useState(false);

  // Mock conversations data
  const mockConversations: Conversation[] = [
    {
      id: '1',
      title: 'Architecture Design Discussion',
      agent: 'Qwen 3 Coder 30B',
      messages: [
        {
          id: '1',
          role: 'user',
          content: 'Design a microservices architecture for the AI system',
          timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000),
          metadata: { tokens: 45, model: 'qwen-30b', confidence: 0.95 },
        },
        {
          id: '2',
          role: 'assistant',
          content: 'I\'ll design a comprehensive microservices architecture...',
          timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000 + 30000),
          metadata: { tokens: 1200, cost: 0.024, model: 'qwen-30b', confidence: 0.92 },
        },
      ],
      createdAt: new Date(Date.now() - 2 * 60 * 60 * 1000),
      updatedAt: new Date(Date.now() - 2 * 60 * 60 * 1000 + 30000),
      tags: ['architecture', 'design', 'microservices'],
      isPinned: true,
      context: {
        sessionId: 'session_001',
        memoryUsed: 256,
      },
    },
    {
      id: '2',
      title: 'Performance Optimization Session',
      agent: 'System Monitor',
      messages: [
        {
          id: '3',
          role: 'user',
          content: 'Analyze current system performance and suggest optimizations',
          timestamp: new Date(Date.now() - 4 * 60 * 60 * 1000),
          metadata: { tokens: 28, model: 'system-monitor', confidence: 0.88 },
        },
        {
          id: '4',
          role: 'assistant',
          content: 'Based on current metrics, here are the key optimization areas...',
          timestamp: new Date(Date.now() - 4 * 60 * 60 * 1000 + 45000),
          metadata: { tokens: 890, cost: 0.018, model: 'system-monitor', confidence: 0.91 },
        },
      ],
      createdAt: new Date(Date.now() - 4 * 60 * 60 * 1000),
      updatedAt: new Date(Date.now() - 4 * 60 * 60 * 1000 + 45000),
      tags: ['performance', 'optimization', 'analysis'],
      isPinned: false,
      context: {
        sessionId: 'session_002',
        memoryUsed: 128,
      },
    },
    {
      id: '3',
      title: 'Desktop Automation Commands',
      agent: 'ByteBot',
      messages: [
        {
          id: '5',
          role: 'user',
          content: 'Show me available automation commands',
          timestamp: new Date(Date.now() - 6 * 60 * 60 * 1000),
          metadata: { tokens: 12, model: 'bytebot', confidence: 0.95 },
        },
        {
          id: '6',
          role: 'assistant',
          content: 'Here are the available desktop automation commands...',
          timestamp: new Date(Date.now() - 6 * 60 * 60 * 1000 + 20000),
          metadata: { tokens: 456, cost: 0.009, model: 'bytebot', confidence: 0.97 },
        },
      ],
      createdAt: new Date(Date.now() - 6 * 60 * 60 * 1000),
      updatedAt: new Date(Date.now() - 6 * 60 * 60 * 1000 + 20000),
      tags: ['automation', 'commands', 'desktop'],
      isPinned: true,
      context: {
        sessionId: 'session_003',
        memoryUsed: 64,
      },
    },
    {
      id: '4',
      title: 'Cost Analysis and Budget Planning',
      agent: 'Cost Optimizer',
      messages: [
        {
          id: '7',
          role: 'user',
          content: 'Review current AI usage costs and suggest budget optimizations',
          timestamp: new Date(Date.now() - 8 * 60 * 60 * 1000),
          metadata: { tokens: 35, model: 'cost-optimizer', confidence: 0.89 },
        },
        {
          id: '8',
          role: 'assistant',
          content: 'Based on your usage patterns, here are my recommendations...',
          timestamp: new Date(Date.now() - 8 * 60 * 60 * 1000 + 60000),
          metadata: { tokens: 1024, cost: 0.021, model: 'cost-optimizer', confidence: 0.93 },
        },
      ],
      createdAt: new Date(Date.now() - 8 * 60 * 60 * 1000),
      updatedAt: new Date(Date.now() - 8 * 60 * 60 * 1000 + 60000),
      tags: ['costs', 'budget', 'optimization', 'analysis'],
      isPinned: false,
      context: {
        sessionId: 'session_004',
        memoryUsed: 192,
      },
    },
  ];

  const filteredConversations = conversations.filter(conv => {
    const matchesSearch = conv.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         conv.agent.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         conv.tags.some(tag => tag.toLowerCase().includes(searchTerm.toLowerCase()));
    const matchesTag = !tagFilter || conv.tags.includes(tagFilter);
    const matchesPinned = !showPinnedOnly || conv.isPinned;

    return matchesSearch && matchesTag && matchesPinned;
  });

  const sortedConversations = [...filteredConversations].sort((a, b) => {
    switch (sortBy) {
      case 'recent':
        return new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime();
      case 'name':
        return a.title.localeCompare(b.title);
      case 'duration':
        return (b.updatedAt.getTime() - b.createdAt.getTime()) - (a.updatedAt.getTime() - a.createdAt.getTime());
      default:
        return 0;
    }
  });

  const allTags = Array.from(new Set(conversations.flatMap(c => c.tags)));
  const agents = Array.from(new Set(conversations.map(c => c.agent)));

  const totalMessages = conversations.reduce((sum, conv) => sum + conv.messages.length, 0);
  const totalTokens = conversations.reduce((sum, conv) =>
    sum + conv.messages.reduce((msgSum, msg) => msgSum + (msg.metadata?.tokens || 0), 0), 0
  );
  const totalCost = conversations.reduce((sum, conv) =>
    sum + conv.messages.reduce((msgSum, msg) => msgSum + (msg.metadata?.cost || 0), 0), 0
  );

  const selectConversation = (conversation: Conversation) => {
    setSelectedConversation(conversation);
    onConversationSelect?.(conversation.id);
  };

  const deleteConversation = (conversationId: string) => {
    setConversations(prev => prev.filter(c => c.id !== conversationId));
    if (selectedConversation?.id === conversationId) {
      setSelectedConversation(null);
    }
    onConversationDelete?.(conversationId);
  };

  const togglePin = (conversationId: string) => {
    setConversations(prev => prev.map(c =>
      c.id === conversationId ? { ...c, isPinned: !c.isPinned } : c
    ));
    onConversationPin?.(conversationId);
  };

  const formatDuration = (start: Date, end: Date) => {
    const diff = end.getTime() - start.getTime();
    const minutes = Math.floor(diff / (1000 * 60));
    const hours = Math.floor(minutes / 60);
    if (hours > 0) {
      return `${hours}h ${minutes % 60}m`;
    }
    return `${minutes}m`;
  };

  const formatMemory = (bytes: number) => {
    const sizes = ['B', 'KB', 'MB', 'GB'];
    if (bytes === 0) return '0 B';
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <MessageSquare size={24} style={{ color: colors.primary }} />
          <div>
            <h2 className="text-xl font-bold" style={{ color: colors.text }}>
              Conversation History
            </h2>
            <p className="text-sm" style={{ color: colors.textSecondary }}>
              {conversations.length} conversations • {totalMessages} messages • {formatMemory(totalTokens * 4)}
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="flex items-center space-x-2 px-3 py-2 rounded-lg text-sm"
            style={{
              backgroundColor: colors.background,
              borderColor: colors.border,
              color: colors.text,
            }}
          >
            <Download size={16} />
            <span>Export</span>
          </motion.button>

          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="flex items-center space-x-2 px-3 py-2 rounded-lg"
            style={{
              backgroundColor: colors.primary,
              color: colors.background,
            }}
          >
            <Plus size={16} />
            <span>New Chat</span>
          </motion.button>
        </div>
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {[
          { label: 'Total Conversations', value: conversations.length, icon: MessageSquare, color: colors.primary },
          { label: 'Total Messages', value: totalMessages.toLocaleString(), icon: MessageSquare, color: colors.success },
          { label: 'AI Tokens Used', value: totalTokens.toLocaleString(), icon: Brain, color: colors.warning },
          { label: 'Total Cost', value: `$${totalCost.toFixed(3)}`, icon: BarChart3, color: colors.error },
        ].map((stat, index) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className="p-3 rounded-lg border"
            style={{
              backgroundColor: colors.surface,
              borderColor: colors.border,
            }}
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs" style={{ color: colors.textSecondary }}>
                  {stat.label}
                </p>
                <p className="text-lg font-bold" style={{ color: colors.text }}>
                  {stat.value}
                </p>
              </div>
              <stat.icon size={20} style={{ color: stat.color }} />
            </div>
          </motion.div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Conversation List */}
        <div className="lg:col-span-2 space-y-4">
          {/* Filters */}
          <div className="flex items-center space-x-3">
            <div className="relative flex-1">
              <Search
                size={16}
                className="absolute left-3 top-1/2 transform -translate-y-1/2"
                style={{ color: colors.textSecondary }}
              />
              <input
                type="text"
                placeholder="Search conversations..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-3 py-2 rounded-lg border focus:outline-none focus:ring-2"
                style={{
                  backgroundColor: colors.background,
                  borderColor: colors.border,
                  color: colors.text,
                  focusRingColor: colors.primary,
                }}
              />
            </div>

            <select
              value={tagFilter}
              onChange={(e) => setTagFilter(e.target.value)}
              className="px-3 py-2 rounded-lg border text-sm"
              style={{
                backgroundColor: colors.background,
                borderColor: colors.border,
                color: colors.text,
              }}
            >
              <option value="">All Tags</option>
              {allTags.map(tag => (
                <option key={tag} value={tag}>{tag}</option>
              ))}
            </select>

            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as any)}
              className="px-3 py-2 rounded-lg border text-sm"
              style={{
                backgroundColor: colors.background,
                borderColor: colors.border,
                color: colors.text,
              }}
            >
              <option value="recent">Most Recent</option>
              <option value="name">By Name</option>
              <option value="duration">By Duration</option>
            </select>
          </div>

          {/* Toggle Pinned */}
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => setShowPinnedOnly(!showPinnedOnly)}
            className={`flex items-center space-x-2 px-3 py-2 rounded-lg text-sm ${
              showPinnedOnly ? 'bg-opacity-20' : ''
            }`}
            style={{
              backgroundColor: showPinnedOnly ? `${colors.primary}20` : colors.background,
              color: showPinnedOnly ? colors.primary : colors.textSecondary,
            }}
          >
            <Pin size={16} />
            <span>Show Pinned Only</span>
          </motion.button>

          {/* Conversation List */}
          <div className="space-y-3 max-h-96 overflow-y-auto">
            <AnimatePresence>
              {sortedConversations.map((conversation, index) => (
                <motion.div
                  key={conversation.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  transition={{ delay: index * 0.05 }}
                  whileHover={{ y: -2 }}
                  className={`p-4 rounded-lg border cursor-pointer transition-all ${
                    selectedConversation?.id === conversation.id ? 'ring-2' : ''
                  }`}
                  style={{
                    backgroundColor: colors.surface,
                    borderColor: selectedConversation?.id === conversation.id ? colors.primary : colors.border,
                    boxShadow: selectedConversation?.id === conversation.id ? `0 0 0 3px ${colors.primary}20` : 'none',
                  }}
                  onClick={() => selectConversation(conversation)}
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-1">
                        {conversation.isPinned && (
                          <Pin size={14} fill={colors.warning} style={{ color: colors.warning }} />
                        )}
                        <h3 className="font-semibold text-sm" style={{ color: colors.text }}>
                          {conversation.title}
                        </h3>
                      </div>
                      <p className="text-xs" style={{ color: colors.textSecondary }}>
                        with {conversation.agent}
                      </p>
                    </div>
                    <div className="flex items-center space-x-1">
                      <span className="text-xs px-2 py-1 rounded-full"
                            style={{
                              backgroundColor: colors.background,
                              color: colors.textSecondary,
                            }}>
                        {conversation.messages.length} messages
                      </span>
                    </div>
                  </div>

                  {/* Tags */}
                  <div className="flex flex-wrap gap-1 mb-2">
                    {conversation.tags.slice(0, 3).map((tag, tagIndex) => (
                      <span
                        key={tagIndex}
                        className="text-xs px-2 py-1 rounded-full"
                        style={{
                          backgroundColor: `${colors.primary}20`,
                          color: colors.primary,
                        }}
                      >
                        {tag}
                      </span>
                    ))}
                    {conversation.tags.length > 3 && (
                      <span className="text-xs px-2 py-1 rounded-full"
                            style={{
                              backgroundColor: colors.background,
                              color: colors.textSecondary,
                            }}>
                        +{conversation.tags.length - 3}
                      </span>
                    )}
                  </div>

                  {/* Metadata */}
                  <div className="flex items-center justify-between text-xs">
                    <div className="flex items-center space-x-3">
                      <span style={{ color: colors.textSecondary }}>
                        {formatDuration(conversation.createdAt, conversation.updatedAt)}
                      </span>
                      {conversation.context?.memoryUsed && (
                        <span style={{ color: colors.textSecondary }}>
                          {formatMemory(conversation.context.memoryUsed)}
                        </span>
                      )}
                    </div>
                    <span style={{ color: colors.textSecondary }}>
                      {conversation.updatedAt.toLocaleDateString()}
                    </span>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>

          {sortedConversations.length === 0 && (
            <div className="text-center py-12">
              <MessageSquare size={48} style={{ color: colors.textSecondary, opacity: 0.3 }} />
              <p className="mt-4 text-sm" style={{ color: colors.textSecondary }}>
                No conversations match your filters
              </p>
            </div>
          )}
        </div>

        {/* Conversation Details */}
        <div className="space-y-4">
          {selectedConversation ? (
            <div className="p-4 rounded-lg border"
                 style={{ backgroundColor: colors.surface, borderColor: colors.border }}>
              {/* Header */}
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="font-semibold" style={{ color: colors.text }}>
                    {selectedConversation.title}
                  </h3>
                  <p className="text-sm" style={{ color: colors.textSecondary }}>
                    with {selectedConversation.agent}
                  </p>
                </div>
                <div className="flex items-center space-x-2">
                  <motion.button
                    whileHover={{ scale: 1.1 }}
                    whileTap={{ scale: 0.9 }}
                    onClick={() => togglePin(selectedConversation.id)}
                    className="p-1 rounded"
                  >
                    <Pin
                      size={16}
                      fill={selectedConversation.isPinned ? colors.warning : 'none'}
                      style={{ color: selectedConversation.isPinned ? colors.warning : colors.textSecondary }}
                    />
                  </motion.button>
                  <motion.button
                    whileHover={{ scale: 1.1 }}
                    whileTap={{ scale: 0.9 }}
                    onClick={() => deleteConversation(selectedConversation.id)}
                    className="p-1 rounded"
                    style={{ color: colors.error }}
                  >
                    <Trash2 size={16} />
                  </motion.button>
                </div>
              </div>

              {/* Tags */}
              <div className="mb-4">
                <div className="flex flex-wrap gap-1">
                  {selectedConversation.tags.map((tag, index) => (
                    <span
                      key={index}
                      className="text-xs px-2 py-1 rounded-full"
                      style={{
                        backgroundColor: `${colors.primary}20`,
                        color: colors.primary,
                      }}
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              </div>

              {/* Messages */}
              <div className="space-y-3 max-h-64 overflow-y-auto mb-4">
                {selectedConversation.messages.map((message, index) => (
                  <div
                    key={message.id}
                    className={`p-3 rounded-lg ${
                      message.role === 'user' ? 'ml-8' : 'mr-8'
                    }`}
                    style={{
                      backgroundColor: message.role === 'user' ? colors.background : `${colors.primary}10`,
                    }}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-medium" style={{ color: colors.text }}>
                        {message.role === 'user' ? 'You' : selectedConversation.agent}
                      </span>
                      <span className="text-xs" style={{ color: colors.textSecondary }}>
                        {message.timestamp.toLocaleTimeString()}
                      </span>
                    </div>
                    <p className="text-sm" style={{ color: colors.text }}>
                      {message.content}
                    </p>
                    {message.metadata && (
                      <div className="flex items-center space-x-3 mt-2 text-xs"
                           style={{ color: colors.textSecondary }}>
                        {message.metadata.tokens && (
                          <span>{message.metadata.tokens} tokens</span>
                        )}
                        {message.metadata.cost && (
                          <span>${message.metadata.cost.toFixed(4)}</span>
                        )}
                        {message.metadata.confidence && (
                          <span>Confidence: {(message.metadata.confidence * 100).toFixed(0)}%</span>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>

              {/* Actions */}
              <div className="flex items-center space-x-2">
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  className="flex items-center space-x-2 px-3 py-2 rounded-lg text-sm flex-1"
                  style={{
                    backgroundColor: colors.primary,
                    color: colors.background,
                  }}
                >
                  <MessageSquare size={14} />
                  <span>Continue Chat</span>
                </motion.button>
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  className="flex items-center space-x-2 px-3 py-2 rounded-lg border text-sm"
                  style={{
                    backgroundColor: colors.background,
                    borderColor: colors.border,
                    color: colors.text,
                  }}
                >
                  <Download size={14} />
                  <span>Export</span>
                </motion.button>
              </div>
            </div>
          ) : (
            <div className="p-4 rounded-lg border text-center"
                 style={{ backgroundColor: colors.surface, borderColor: colors.border }}>
              <MessageSquare size={32} style={{ color: colors.textSecondary, opacity: 0.5 }} />
              <p className="mt-2 text-sm" style={{ color: colors.textSecondary }}>
                Select a conversation to view details
              </p>
            </div>
          )}

          {/* Memory Usage */}
          <div className="p-4 rounded-lg border"
               style={{ backgroundColor: colors.surface, borderColor: colors.border }}>
            <h4 className="font-semibold mb-3" style={{ color: colors.text }}>
              Memory Usage
            </h4>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span style={{ color: colors.textSecondary }}>Total Sessions:</span>
                <span style={{ color: colors.text }}>{conversations.length}</span>
              </div>
              <div className="flex justify-between">
                <span style={{ color: colors.textSecondary }}>Memory Used:</span>
                <span style={{ color: colors.text }}>
                  {formatMemory(conversations.reduce((sum, c) => sum + (c.context?.memoryUsed || 0), 0))}
                </span>
              </div>
              <div className="flex justify-between">
                <span style={{ color: colors.textSecondary }}>Avg per Session:</span>
                <span style={{ color: colors.text }}>
                  {formatMemory(conversations.reduce((sum, c) => sum + (c.context?.memoryUsed || 0), 0) / conversations.length || 0)}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ConversationManager;