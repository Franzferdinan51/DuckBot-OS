import React, { createContext, useContext, useState, useEffect } from 'react';
import { useAuth } from './AuthContext';
import toast from 'react-hot-toast';

const AIContext = createContext();

export const useAI = () => {
  const context = useContext(AIContext);
  if (!context) {
    throw new Error('useAI must be used within an AIProvider');
  }
  return context;
};

export const AIProvider = ({ children }) => {
  const { apiCall, isAuthenticated } = useAuth();
  
  // AI Model Management
  const [models, setModels] = useState([]);
  const [currentModel, setCurrentModel] = useState(null);
  const [modelLoading, setModelLoading] = useState(false);
  
  // Provider Status
  const [providers, setProviders] = useState({
    lmStudio: {
      status: 'disconnected',
      url: 'http://localhost:1234',
      models: [],
      lastCheck: null
    },
    openRouter: {
      status: 'disconnected',
      apiKey: null,
      models: [],
      lastCheck: null
    },
    duckbot: {
      status: 'connected',
      models: [
        { id: 'duckbot-auto', name: 'DuckBot Auto Router', provider: 'duckbot', capabilities: ['chat', 'code', 'reasoning'] },
        { id: 'duckbot-code', name: 'DuckBot Code Specialist', provider: 'duckbot', capabilities: ['code', 'debug'] },
        { id: 'duckbot-reasoning', name: 'DuckBot Reasoning', provider: 'duckbot', capabilities: ['reasoning', 'analysis'] },
        { id: 'duckbot-summary', name: 'DuckBot Summary', provider: 'duckbot', capabilities: ['summary', 'extraction'] },
        { id: 'duckbot-qwen', name: 'DuckBot Qwen Enhanced', provider: 'duckbot', capabilities: ['code', 'reasoning', 'enhanced'] }
      ],
      lastCheck: new Date()
    }
  });
  
  // Conversation Management
  const [conversations, setConversations] = useState([]);
  const [activeConversation, setActiveConversation] = useState(null);
  const [isThinking, setIsThinking] = useState(false);
  
  // RAG and Knowledge Base
  const [ragStats, setRagStats] = useState({
    totalDocuments: 0,
    totalChunks: 0,
    indexSize: '0 MB',
    lastUpdated: null
  });
  
  // Cost Tracking
  const [costData, setCostData] = useState({
    daily: 0,
    monthly: 0,
    total: 0,
    breakdown: {}
  });

  // Initialize AI system
  useEffect(() => {
    if (isAuthenticated) {
      initializeAI();
    }
  }, [isAuthenticated]);

  const initializeAI = async () => {
    try {
      await Promise.all([
        loadModels(),
        checkProviderStatus(),
        loadRAGStats(),
        loadCostData()
      ]);
    } catch (error) {
      console.error('AI initialization failed:', error);
    }
  };

  // Load available models from all providers
  const loadModels = async () => {
    try {
      setModelLoading(true);
      const allModels = [];
      
      // Add DuckBot models
      allModels.push(...providers.duckbot.models);
      
      // Check LM Studio models
      if (providers.lmStudio.status === 'connected') {
        allModels.push(...providers.lmStudio.models);
      }
      
      // Check OpenRouter models
      if (providers.openRouter.status === 'connected') {
        allModels.push(...providers.openRouter.models);
      }
      
      setModels(allModels);
      
      // Set default model if none selected
      if (!currentModel && allModels.length > 0) {
        setCurrentModel(allModels.find(m => m.id === 'duckbot-auto') || allModels[0]);
      }
    } catch (error) {
      console.error('Failed to load models:', error);
      toast.error('Failed to load AI models');
    } finally {
      setModelLoading(false);
    }
  };

  // Check provider connection status
  const checkProviderStatus = async () => {
    const updatedProviders = { ...providers };
    
    // Check LM Studio
    try {
      const lmResponse = await fetch(`${providers.lmStudio.url}/v1/models`, {
        method: 'GET',
        timeout: 5000
      });
      
      if (lmResponse.ok) {
        const lmData = await lmResponse.json();
        updatedProviders.lmStudio = {
          ...updatedProviders.lmStudio,
          status: 'connected',
          models: lmData.data?.map(model => ({
            id: `lmstudio/${model.id}`,
            name: model.id.split('/').pop().replace(/-/g, ' '),
            originalId: model.id,
            provider: 'lmstudio',
            context: model.context_length || 4096
          })) || [],
          lastCheck: new Date()
        };
      } else {
        updatedProviders.lmStudio.status = 'error';
      }
    } catch (error) {
      updatedProviders.lmStudio.status = 'disconnected';
    }
    
    // Check OpenRouter (basic connectivity)
    try {
      updatedProviders.openRouter.status = providers.openRouter.apiKey ? 'connected' : 'free-mode';
      updatedProviders.openRouter.lastCheck = new Date();
    } catch (error) {
      updatedProviders.openRouter.status = 'error';
    }
    
    setProviders(updatedProviders);
  };

  // Load RAG statistics
  const loadRAGStats = async () => {
    try {
      const response = await apiCall('/api/rag/stats');
      if (response.ok) {
        const stats = await response.json();
        setRagStats(stats);
      }
    } catch (error) {
      console.error('Failed to load RAG stats:', error);
    }
  };

  // Load cost data
  const loadCostData = async () => {
    try {
      const response = await apiCall('/api/cost/summary');
      if (response.ok) {
        const costs = await response.json();
        setCostData(costs);
      }
    } catch (error) {
      console.error('Failed to load cost data:', error);
    }
  };

  // Send message to AI
  const sendMessage = async (message, options = {}) => {
    if (!currentModel) {
      toast.error('No AI model selected');
      return null;
    }

    try {
      setIsThinking(true);
      
      const payload = {
        message,
        model: currentModel.id,
        kind: options.kind || 'auto',
        risk: options.risk || 'low',
        stream: options.stream || false,
        context: options.context || {}
      };

      const response = await apiCall('/api/chat', {
        method: 'POST',
        body: JSON.stringify(payload)
      });

      if (response.ok) {
        const result = await response.json();
        
        // Update conversation
        if (activeConversation) {
          updateConversation(activeConversation.id, {
            messages: [
              ...activeConversation.messages,
              { role: 'user', content: message, timestamp: new Date() },
              { role: 'assistant', content: result.response, timestamp: new Date(), model: currentModel.id }
            ]
          });
        } else {
          // Create new conversation
          createNewConversation([
            { role: 'user', content: message, timestamp: new Date() },
            { role: 'assistant', content: result.response, timestamp: new Date(), model: currentModel.id }
          ]);
        }
        
        return result.response;
      } else {
        const error = await response.text();
        toast.error(`AI request failed: ${error}`);
        return null;
      }
    } catch (error) {
      console.error('Failed to send message:', error);
      toast.error('Failed to send message to AI');
      return null;
    } finally {
      setIsThinking(false);
    }
  };

  // Create new conversation
  const createNewConversation = (messages = []) => {
    const newConversation = {
      id: Date.now().toString(),
      title: messages.length > 0 ? generateConversationTitle(messages[0].content) : 'New Conversation',
      messages,
      model: currentModel?.id,
      created: new Date(),
      updated: new Date()
    };
    
    setConversations(prev => [newConversation, ...prev]);
    setActiveConversation(newConversation);
    return newConversation;
  };

  // Update conversation
  const updateConversation = (conversationId, updates) => {
    setConversations(prev => prev.map(conv => 
      conv.id === conversationId 
        ? { ...conv, ...updates, updated: new Date() }
        : conv
    ));
    
    if (activeConversation?.id === conversationId) {
      setActiveConversation(prev => ({ ...prev, ...updates, updated: new Date() }));
    }
  };

  // Generate conversation title from first message
  const generateConversationTitle = (firstMessage) => {
    if (!firstMessage) return 'New Conversation';
    
    const words = firstMessage.split(' ').slice(0, 6);
    return words.join(' ') + (firstMessage.split(' ').length > 6 ? '...' : '');
  };

  // Switch AI model
  const switchModel = (model) => {
    setCurrentModel(model);
    toast.success(`Switched to ${model.name}`);
  };

  // Configure provider
  const configureProvider = async (providerName, config) => {
    try {
      const response = await apiCall(`/api/providers/${providerName}/configure`, {
        method: 'POST',
        body: JSON.stringify(config)
      });

      if (response.ok) {
        await checkProviderStatus();
        await loadModels();
        toast.success(`${providerName} configured successfully`);
        return true;
      } else {
        const error = await response.text();
        toast.error(`Failed to configure ${providerName}: ${error}`);
        return false;
      }
    } catch (error) {
      console.error(`Failed to configure ${providerName}:`, error);
      toast.error(`Failed to configure ${providerName}`);
      return false;
    }
  };

  // Execute desktop task (ByteBot integration)
  const executeDesktopTask = async (task) => {
    try {
      const response = await apiCall('/api/desktop/execute', {
        method: 'POST',
        body: JSON.stringify({ task, model: currentModel?.id })
      });

      if (response.ok) {
        const result = await response.json();
        toast.success('Desktop task executed successfully');
        return result;
      } else {
        const error = await response.text();
        toast.error(`Desktop task failed: ${error}`);
        return null;
      }
    } catch (error) {
      console.error('Failed to execute desktop task:', error);
      toast.error('Failed to execute desktop task');
      return null;
    }
  };

  // Search knowledge base (Archon-inspired)
  const searchKnowledge = async (query, strategies = ['rag', 'semantic']) => {
    try {
      const response = await apiCall('/api/rag/search', {
        method: 'POST',
        body: JSON.stringify({ query, strategies })
      });

      if (response.ok) {
        const results = await response.json();
        return results;
      } else {
        const error = await response.text();
        toast.error(`Knowledge search failed: ${error}`);
        return null;
      }
    } catch (error) {
      console.error('Failed to search knowledge base:', error);
      toast.error('Failed to search knowledge base');
      return null;
    }
  };

  const value = {
    // Models and Providers
    models,
    currentModel,
    providers,
    modelLoading,
    
    // Conversations
    conversations,
    activeConversation,
    isThinking,
    
    // Data
    ragStats,
    costData,
    
    // Actions
    sendMessage,
    createNewConversation,
    updateConversation,
    switchModel,
    configureProvider,
    executeDesktopTask,
    searchKnowledge,
    loadModels,
    checkProviderStatus
  };

  return (
    <AIContext.Provider value={value}>
      {children}
    </AIContext.Provider>
  );
};