import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useTheme } from '../../theme/ThemeContext';
import { AutomationCommand } from '../../types/dashboard';
import {
  Zap,
  Play,
  Square,
  Settings,
  Terminal,
  MousePointer,
  Keyboard,
  Monitor,
  Folder,
  Browser,
  MessageSquare,
  Star,
  Search,
  Filter,
  Clock,
  CheckCircle,
  AlertTriangle,
  MoreVertical,
  Plus,
  Save,
  Trash2
} from 'lucide-react';

interface AutomationPanelProps {
  commands?: AutomationCommand[];
  onCommandExecute?: (commandId: string, parameters: any) => void;
  autoRefresh?: boolean;
  refreshInterval?: number;
}

const AutomationPanel: React.FC<AutomationPanelProps> = ({
  commands: initialCommands,
  onCommandExecute,
  autoRefresh = true,
  refreshInterval = 5000,
}) => {
  const { colors } = useTheme();
  const [commands, setCommands] = useState<AutomationCommand[]>(initialCommands || mockCommands);
  const [selectedCommand, setSelectedCommand] = useState<AutomationCommand | null>(null);
  const [commandParameters, setCommandParameters] = useState<Record<string, any>>({});
  const [isExecuting, setIsExecuting] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState<string>('all');
  const [executionHistory, setExecutionHistory] = useState<any[]>([]);
  const [showHistory, setShowHistory] = useState(false);

  // Mock commands data
  const mockCommands: AutomationCommand[] = [
    {
      id: 'open-application',
      name: 'Open Application',
      description: 'Launch any Windows application by name',
      category: 'application',
      parameters: {
        appName: {
          type: 'string',
          required: true,
          description: 'Name of the application to open',
        },
        waitForReady: {
          type: 'boolean',
          required: false,
          description: 'Wait for application to be ready',
          default: true,
        },
      },
      lastUsed: new Date(Date.now() - 30 * 60 * 1000),
      successRate: 98.5,
      isFavorite: true,
    },
    {
      id: 'type-text',
      name: 'Type Text',
      description: 'Type text into the active window',
      category: 'input',
      parameters: {
        text: {
          type: 'string',
          required: true,
          description: 'Text to type',
        },
        speed: {
          type: 'select',
          required: false,
          description: 'Typing speed',
          options: ['slow', 'medium', 'fast'],
          default: 'medium',
        },
      },
      lastUsed: new Date(Date.now() - 15 * 60 * 1000),
      successRate: 96.2,
      isFavorite: true,
    },
    {
      id: 'mouse-click',
      name: 'Mouse Click',
      description: 'Perform mouse click at specified coordinates',
      category: 'mouse',
      parameters: {
        x: {
          type: 'number',
          required: true,
          description: 'X coordinate',
        },
        y: {
          type: 'number',
          required: true,
          description: 'Y coordinate',
        },
        button: {
          type: 'select',
          required: false,
          description: 'Mouse button',
          options: ['left', 'right', 'middle'],
          default: 'left',
        },
      },
      lastUsed: new Date(Date.now() - 45 * 60 * 1000),
      successRate: 99.1,
      isFavorite: false,
    },
    {
      id: 'take-screenshot',
      name: 'Take Screenshot',
      description: 'Capture screenshot of screen or specific region',
      category: 'screen',
      parameters: {
        region: {
          type: 'string',
          required: false,
          description: 'Region to capture (format: x,y,width,height)',
        },
        savePath: {
          type: 'string',
          required: false,
          description: 'Path to save screenshot',
        },
      },
      lastUsed: new Date(Date.now() - 60 * 60 * 1000),
      successRate: 100.0,
      isFavorite: true,
    },
    {
      id: 'wait-for-element',
      name: 'Wait for Element',
      description: 'Wait for UI element to appear on screen',
      category: 'waiting',
      parameters: {
        selector: {
          type: 'string',
          required: true,
          description: 'Element selector or description',
        },
        timeout: {
          type: 'number',
          required: false,
          description: 'Timeout in seconds',
          default: 30,
        },
      },
      lastUsed: new Date(Date.now() - 20 * 60 * 1000),
      successRate: 94.8,
      isFavorite: false,
    },
    {
      id: 'read-text',
      name: 'Read Text',
      description: 'Read text from screen using OCR',
      category: 'ocr',
      parameters: {
        region: {
          type: 'string',
          required: false,
          description: 'Region to read text from',
        },
        language: {
          type: 'string',
          required: false,
          description: 'Language for OCR',
          default: 'en',
        },
      },
      lastUsed: new Date(Date.now() - 90 * 60 * 1000),
      successRate: 89.3,
      isFavorite: false,
    },
  ];

  const categories = Array.from(new Set(commands.map(c => c.category)));
  const filteredCommands = commands.filter(command => {
    const matchesSearch = command.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         command.description.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = categoryFilter === 'all' || command.category === categoryFilter;
    return matchesSearch && matchesCategory;
  });

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'application': return Monitor;
      case 'input': return Keyboard;
      case 'mouse': return MousePointer;
      case 'screen': return Monitor;
      case 'waiting': return Clock;
      case 'ocr': return MessageSquare;
      default: return Terminal;
    }
  };

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'application': return colors.primary;
      case 'input': return colors.success;
      case 'mouse': return colors.warning;
      case 'screen': return colors.info;
      case 'waiting': return colors.secondary;
      case 'ocr': return colors.error;
      default: return colors.textSecondary;
    }
  };

  const executeCommand = async () => {
    if (!selectedCommand) return;

    setIsExecuting(true);
    try {
      // Simulate command execution
      await new Promise(resolve => setTimeout(resolve, 2000));

      const result = {
        id: Date.now().toString(),
        commandId: selectedCommand.id,
        commandName: selectedCommand.name,
        parameters: { ...commandParameters },
        timestamp: new Date(),
        status: Math.random() > 0.1 ? 'success' : 'error',
        duration: Math.floor(Math.random() * 3000) + 500,
        error: Math.random() > 0.1 ? null : 'Simulated error for testing',
      };

      setExecutionHistory(prev => [result, ...prev.slice(0, 19)]);
      onCommandExecute?.(selectedCommand.id, commandParameters);

      // Show success notification
      if (result.status === 'success') {
        console.log(`Command executed successfully: ${selectedCommand.name}`);
      }
    } catch (error) {
      console.error('Error executing command:', error);
    } finally {
      setIsExecuting(false);
    }
  };

  const selectCommand = (command: AutomationCommand) => {
    setSelectedCommand(command);
    // Initialize parameters with defaults
    const defaults: Record<string, any> = {};
    Object.entries(command.parameters).forEach(([key, param]) => {
      if (param.default !== undefined) {
        defaults[key] = param.default;
      }
    });
    setCommandParameters(defaults);
  };

  const updateParameter = (key: string, value: any) => {
    setCommandParameters(prev => ({
      ...prev,
      [key]: value,
    }));
  };

  const toggleFavorite = (commandId: string) => {
    setCommands(prev => prev.map(cmd =>
      cmd.id === commandId ? { ...cmd, isFavorite: !cmd.isFavorite } : cmd
    ));
  };

  const renderParameterInput = (key: string, param: any) => {
    const value = commandParameters[key] || param.default;

    switch (param.type) {
      case 'string':
        return (
          <input
            type="text"
            value={value}
            onChange={(e) => updateParameter(key, e.target.value)}
            className="w-full px-3 py-2 rounded border focus:outline-none focus:ring-2"
            style={{
              backgroundColor: colors.background,
              borderColor: colors.border,
              color: colors.text,
              focusRingColor: colors.primary,
            }}
            placeholder={param.description}
          />
        );
      case 'number':
        return (
          <input
            type="number"
            value={value}
            onChange={(e) => updateParameter(key, Number(e.target.value))}
            className="w-full px-3 py-2 rounded border focus:outline-none focus:ring-2"
            style={{
              backgroundColor: colors.background,
              borderColor: colors.border,
              color: colors.text,
              focusRingColor: colors.primary,
            }}
            placeholder={param.description}
          />
        );
      case 'boolean':
        return (
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={value}
              onChange={(e) => updateParameter(key, e.target.checked)}
              className="rounded"
            />
            <span className="text-sm" style={{ color: colors.textSecondary }}>
              {param.description}
            </span>
          </label>
        );
      case 'select':
        return (
          <select
            value={value}
            onChange={(e) => updateParameter(key, e.target.value)}
            className="w-full px-3 py-2 rounded border focus:outline-none focus:ring-2"
            style={{
              backgroundColor: colors.background,
              borderColor: colors.border,
              color: colors.text,
              focusRingColor: colors.primary,
            }}
          >
            {param.options?.map((option: string) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        );
      default:
        return null;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <Zap size={24} style={{ color: colors.primary }} />
          <div>
            <h2 className="text-xl font-bold" style={{ color: colors.text }}>
              Desktop Automation
            </h2>
            <p className="text-sm" style={{ color: colors.textSecondary }}>
              Control your desktop with natural language commands
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => setShowHistory(!showHistory)}
            className="p-2 rounded-lg border"
            style={{
              backgroundColor: colors.background,
              borderColor: colors.border,
              color: colors.textSecondary,
            }}
          >
            <Clock size={18} />
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
            <span className="text-sm font-medium">New Command</span>
          </motion.button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Command List */}
        <div className="lg:col-span-2">
          {/* Search and Filters */}
          <div className="flex items-center space-x-3 mb-4">
            <div className="relative flex-1">
              <Search
                size={16}
                className="absolute left-3 top-1/2 transform -translate-y-1/2"
                style={{ color: colors.textSecondary }}
              />
              <input
                type="text"
                placeholder="Search commands..."
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
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              className="px-3 py-2 rounded-lg border text-sm"
              style={{
                backgroundColor: colors.background,
                borderColor: colors.border,
                color: colors.text,
              }}
            >
              <option value="all">All Categories</option>
              {categories.map(category => (
                <option key={category} value={category}>
                  {category.charAt(0).toUpperCase() + category.slice(1)}
                </option>
              ))}
            </select>
          </div>

          {/* Commands Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <AnimatePresence>
              {filteredCommands.map((command, index) => {
                const Icon = getCategoryIcon(command.category);
                const isSelected = selectedCommand?.id === command.id;

                return (
                  <motion.div
                    key={command.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -20 }}
                    transition={{ delay: index * 0.05 }}
                    whileHover={{ y: -2 }}
                    className={`p-3 rounded-lg border cursor-pointer transition-all ${
                      isSelected ? 'ring-2' : ''
                    }`}
                    style={{
                      backgroundColor: colors.surface,
                      borderColor: isSelected ? colors.primary : colors.border,
                      boxShadow: isSelected ? `0 0 0 3px ${colors.primary}20` : 'none',
                    }}
                    onClick={() => selectCommand(command)}
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-start space-x-2">
                        <div className="flex items-center justify-center w-8 h-8 rounded"
                             style={{ backgroundColor: `${getCategoryColor(command.category)}20` }}>
                          <Icon size={16} style={{ color: getCategoryColor(command.category) }} />
                        </div>
                        <div className="flex-1">
                          <h3 className="font-semibold text-sm" style={{ color: colors.text }}>
                            {command.name}
                          </h3>
                          <span className="text-xs capitalize"
                                style={{ color: getCategoryColor(command.category) }}>
                            {command.category}
                          </span>
                        </div>
                      </div>
                      <div className="flex items-center space-x-1">
                        {command.isFavorite && (
                          <Star size={14} fill={colors.warning} style={{ color: colors.warning }} />
                        )}
                        <motion.button
                          whileHover={{ scale: 1.1 }}
                          whileTap={{ scale: 0.9 }}
                          onClick={(e) => {
                            e.stopPropagation();
                            toggleFavorite(command.id);
                          }}
                          className="p-1 rounded"
                        >
                          <Star
                            size={14}
                            fill={command.isFavorite ? colors.warning : 'none'}
                            style={{ color: command.isFavorite ? colors.warning : colors.textSecondary }}
                          />
                        </motion.button>
                      </div>
                    </div>

                    <p className="text-xs mb-3 line-clamp-2" style={{ color: colors.textSecondary }}>
                      {command.description}
                    </p>

                    <div className="flex items-center justify-between text-xs">
                      <span style={{ color: colors.textSecondary }}>
                        {Object.keys(command.parameters).length} parameters
                      </span>
                      <div className="flex items-center space-x-1">
                        <CheckCircle
                          size={12}
                          style={{ color: command.successRate >= 95 ? colors.success : colors.warning }}
                        />
                        <span style={{ color: colors.textSecondary }}>
                          {command.successRate.toFixed(1)}%
                        </span>
                      </div>
                    </div>
                  </motion.div>
                );
              })}
            </AnimatePresence>
          </div>

          {filteredCommands.length === 0 && (
            <div className="text-center py-12">
              <Search size={48} style={{ color: colors.textSecondary, opacity: 0.3 }} />
              <p className="mt-4 text-sm" style={{ color: colors.textSecondary }}>
                No commands match your search
              </p>
            </div>
          )}
        </div>

        {/* Command Execution Panel */}
        <div className="space-y-4">
          {/* Selected Command */}
          {selectedCommand ? (
            <div className="p-4 rounded-lg border"
                 style={{ backgroundColor: colors.surface, borderColor: colors.border }}>
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold" style={{ color: colors.text }}>
                  {selectedCommand.name}
                </h3>
                <div className="flex items-center space-x-1">
                  <CheckCircle
                    size={16}
                    style={{ color: selectedCommand.successRate >= 95 ? colors.success : colors.warning }}
                  />
                  <span className="text-sm" style={{ color: colors.textSecondary }}>
                    {selectedCommand.successRate.toFixed(1)}%
                  </span>
                </div>
              </div>

              <p className="text-sm mb-4" style={{ color: colors.textSecondary }}>
                {selectedCommand.description}
              </p>

              {/* Parameters */}
              <div className="space-y-3 mb-4">
                <h4 className="text-sm font-medium" style={{ color: colors.text }}>
                  Parameters
                </h4>
                {Object.entries(selectedCommand.parameters).map(([key, param]) => (
                  <div key={key}>
                    <label className="block text-xs font-medium mb-1" style={{ color: colors.textSecondary }}>
                      {key}
                      {param.required && <span className="text-red-500 ml-1">*</span>}
                    </label>
                    {renderParameterInput(key, param)}
                    <p className="text-xs mt-1" style={{ color: colors.textSecondary }}>
                      {param.description}
                    </p>
                  </div>
                ))}
              </div>

              {/* Execute Button */}
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={executeCommand}
                disabled={isExecuting}
                className="w-full flex items-center justify-center space-x-2 px-4 py-2 rounded-lg font-medium"
                style={{
                  backgroundColor: isExecuting ? colors.border : colors.primary,
                  color: isExecuting ? colors.textSecondary : colors.background,
                }}
              >
                {isExecuting ? (
                  <>
                    <Square size={16} className="animate-pulse" />
                    <span>Executing...</span>
                  </>
                ) : (
                  <>
                    <Play size={16} />
                    <span>Execute Command</span>
                  </>
                )}
              </motion.button>
            </div>
          ) : (
            <div className="p-4 rounded-lg border text-center"
                 style={{ backgroundColor: colors.surface, borderColor: colors.border }}>
              <Terminal size={32} style={{ color: colors.textSecondary, opacity: 0.5 }} />
              <p className="mt-2 text-sm" style={{ color: colors.textSecondary }}>
                Select a command to configure and execute
              </p>
            </div>
          )}

          {/* Quick Stats */}
          <div className="p-4 rounded-lg border"
               style={{ backgroundColor: colors.surface, borderColor: colors.border }}>
            <h4 className="text-sm font-medium mb-3" style={{ color: colors.text }}>
              Quick Stats
            </h4>
            <div className="space-y-2 text-xs">
              <div className="flex justify-between">
                <span style={{ color: colors.textSecondary }}>Total Commands:</span>
                <span style={{ color: colors.text }}>{commands.length}</span>
              </div>
              <div className="flex justify-between">
                <span style={{ color: colors.textSecondary }}>Favorites:</span>
                <span style={{ color: colors.text }}>
                  {commands.filter(c => c.isFavorite).length}
                </span>
              </div>
              <div className="flex justify-between">
                <span style={{ color: colors.textSecondary }}>Avg Success Rate:</span>
                <span style={{ color: colors.text }}>
                  {(commands.reduce((sum, c) => sum + c.successRate, 0) / commands.length).toFixed(1)}%
                </span>
              </div>
              <div className="flex justify-between">
                <span style={{ color: colors.textSecondary }}>Executions Today:</span>
                <span style={{ color: colors.text }}>{executionHistory.length}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Execution History */}
      {showHistory && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="p-4 rounded-lg border"
          style={{ backgroundColor: colors.surface, borderColor: colors.border }}
        >
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold" style={{ color: colors.text }}>
              Execution History
            </h3>
            <button
              onClick={() => setExecutionHistory([])}
              className="text-sm"
              style={{ color: colors.textSecondary }}
            >
              Clear History
            </button>
          </div>

          <div className="space-y-2 max-h-64 overflow-y-auto">
            {executionHistory.length === 0 ? (
              <p className="text-center text-sm py-4" style={{ color: colors.textSecondary }}>
                No execution history yet
              </p>
            ) : (
              executionHistory.map((execution) => (
                <div
                  key={execution.id}
                  className="p-3 rounded border-l-4"
                  style={{
                    backgroundColor: colors.background,
                    borderColor: 'transparent',
                    borderLeftColor: execution.status === 'success' ? colors.success : colors.error,
                  }}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="font-medium text-sm" style={{ color: colors.text }}>
                        {execution.commandName}
                      </h4>
                      <p className="text-xs mt-1" style={{ color: colors.textSecondary }}>
                        {execution.timestamp.toLocaleTimeString()} • {execution.duration}ms
                      </p>
                    </div>
                    {execution.status === 'success' ? (
                      <CheckCircle size={16} style={{ color: colors.success }} />
                    ) : (
                      <AlertTriangle size={16} style={{ color: colors.error }} />
                    )}
                  </div>
                  {execution.error && (
                    <p className="text-xs mt-1" style={{ color: colors.error }}>
                      {execution.error}
                    </p>
                  )}
                </div>
              ))
            )}
          </div>
        </motion.div>
      )}
    </div>
  );
};

export default AutomationPanel;