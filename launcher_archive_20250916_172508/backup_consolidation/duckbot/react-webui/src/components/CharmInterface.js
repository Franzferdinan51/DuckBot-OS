import React, { useState, useEffect, useRef, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

// Charm-inspired color palette
const CharmColors = {
  primary: '#7C3AED',      // Purple
  secondary: '#10B981',    // Green
  accent: '#F59E0B',       // Amber
  error: '#EF4444',        // Red
  warning: '#F59E0B',      // Amber
  success: '#10B981',      // Green
  info: '#3B82F6',         // Blue
  muted: '#6B7280',        // Gray
  text: '#F3F4F6',         // Light gray
  background: '#1F2937',   // Dark gray
  surface: '#374151',      // Medium gray
  border: '#4B5563',       // Border gray
};

// Charm-inspired styling system (React implementation of Lipgloss)
const createCharmStyle = (styles = {}) => {
  const baseStyle = {
    color: CharmColors.text,
    fontSize: '14px',
    fontFamily: 'ui-monospace, SFMono-Regular, monospace',
    ...styles
  };
  
  return baseStyle;
};

// Bubbletea-inspired component architecture
class CharmComponent {
  constructor(initialState = {}) {
    this.state = initialState;
    this.subscriptions = new Set();
  }
  
  // Model-View-Update pattern
  update(message, currentState) {
    // Override in subclasses
    return { ...currentState };
  }
  
  view(state) {
    // Override in subclasses
    return null;
  }
  
  // Command handling
  handleCommand(command, ...args) {
    // Override in subclasses
    return Promise.resolve();
  }
  
  subscribe(callback) {
    this.subscriptions.add(callback);
    return () => this.subscriptions.delete(callback);
  }
  
  emit(message) {
    this.subscriptions.forEach(callback => callback(message));
  }
}

// Gum-inspired interactive components
const GumSelect = ({ options, onSelect, label, theme = 'primary' }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [selected, setSelected] = useState(null);
  const [highlightedIndex, setHighlightedIndex] = useState(0);
  const dropdownRef = useRef(null);
  
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (!isOpen) return;
      
      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault();
          setHighlightedIndex((prev) => 
            prev < options.length - 1 ? prev + 1 : 0
          );
          break;
        case 'ArrowUp':
          e.preventDefault();
          setHighlightedIndex((prev) => 
            prev > 0 ? prev - 1 : options.length - 1
          );
          break;
        case 'Enter':
          e.preventDefault();
          handleSelect(options[highlightedIndex]);
          break;
        case 'Escape':
          setIsOpen(false);
          break;
      }
    };
    
    if (isOpen) {
      window.addEventListener('keydown', handleKeyDown);
      return () => window.removeEventListener('keydown', handleKeyDown);
    }
  }, [isOpen, highlightedIndex, options]);
  
  const handleSelect = (option) => {
    setSelected(option);
    setIsOpen(false);
    onSelect(option);
  };
  
  const themeColors = {
    primary: CharmColors.primary,
    secondary: CharmColors.secondary,
    accent: CharmColors.accent,
  };
  
  return (
    <div className="relative">
      {label && (
        <label className="block mb-2 text-sm font-medium" style={{ color: CharmColors.text }}>
          {label}
        </label>
      )}
      
      <motion.button
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-4 py-3 text-left border-2 rounded-lg focus:outline-none focus:ring-2 transition-all duration-200"
        style={{
          backgroundColor: CharmColors.surface,
          borderColor: isOpen ? themeColors[theme] : CharmColors.border,
          color: CharmColors.text,
        }}
      >
        <div className="flex items-center justify-between">
          <span className="font-mono">
            {selected ? selected.label || selected : 'Select an option...'}
          </span>
          <motion.svg
            animate={{ rotate: isOpen ? 180 : 0 }}
            transition={{ duration: 0.2 }}
            className="w-5 h-5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </motion.svg>
        </div>
      </motion.button>
      
      <AnimatePresence>
        {isOpen && (
          <motion.div
            ref={dropdownRef}
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.2 }}
            className="absolute z-50 w-full mt-1 border-2 rounded-lg shadow-xl"
            style={{
              backgroundColor: CharmColors.surface,
              borderColor: themeColors[theme],
              maxHeight: '200px',
              overflowY: 'auto',
            }}
          >
            {options.map((option, index) => (
              <motion.div
                key={index}
                whileHover={{ backgroundColor: `${themeColors[theme]}20` }}
                onClick={() => handleSelect(option)}
                className={`px-4 py-3 cursor-pointer font-mono transition-colors duration-150 ${
                  index === highlightedIndex ? 'bg-opacity-20' : ''
                }`}
                style={{
                  color: CharmColors.text,
                  backgroundColor: index === highlightedIndex ? `${themeColors[theme]}20` : 'transparent',
                }}
              >
                <div className="flex items-center">
                  {index === highlightedIndex && (
                    <span className="mr-2" style={{ color: themeColors[theme] }}>▶</span>
                  )}
                  <span>{option.label || option}</span>
                </div>
              </motion.div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

const GumInput = ({ placeholder, onSubmit, theme = 'primary', type = 'text', label }) => {
  const [value, setValue] = useState('');
  const [focused, setFocused] = useState(false);
  const inputRef = useRef(null);
  
  const handleSubmit = (e) => {
    e.preventDefault();
    if (value.trim()) {
      onSubmit(value);
      setValue('');
    }
  };
  
  const themeColor = {
    primary: CharmColors.primary,
    secondary: CharmColors.secondary,
    accent: CharmColors.accent,
  }[theme];
  
  return (
    <div>
      {label && (
        <label className="block mb-2 text-sm font-medium" style={{ color: CharmColors.text }}>
          {label}
        </label>
      )}
      
      <form onSubmit={handleSubmit}>
        <motion.div
          animate={{
            borderColor: focused ? themeColor : CharmColors.border,
            boxShadow: focused ? `0 0 0 3px ${themeColor}20` : 'none',
          }}
          transition={{ duration: 0.2 }}
          className="relative"
        >
          <input
            ref={inputRef}
            type={type}
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onFocus={() => setFocused(true)}
            onBlur={() => setFocused(false)}
            placeholder={placeholder}
            className="w-full px-4 py-3 border-2 rounded-lg focus:outline-none font-mono transition-all duration-200"
            style={{
              backgroundColor: CharmColors.surface,
              borderColor: 'transparent',
              color: CharmColors.text,
            }}
          />
          
          {value && (
            <motion.button
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.8 }}
              type="submit"
              className="absolute right-2 top-1/2 transform -translate-y-1/2 p-1 rounded-full hover:bg-opacity-20 transition-colors duration-150"
              style={{
                color: themeColor,
                backgroundColor: `${themeColor}10`,
              }}
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
              </svg>
            </motion.button>
          )}
        </motion.div>
      </form>
    </div>
  );
};

// Harmonica-inspired spring animations
const useSpringAnimation = (targetValue, config = {}) => {
  const [value, setValue] = useState(0);
  const animationRef = useRef(null);
  const velocityRef = useRef(0);
  
  const { stiffness = 300, damping = 30, mass = 1 } = config;
  
  useEffect(() => {
    const animate = () => {
      const displacement = value - targetValue;
      const springForce = -stiffness * displacement;
      const dampingForce = -damping * velocityRef.current;
      
      const acceleration = (springForce + dampingForce) / mass;
      velocityRef.current += acceleration * 0.016; // 60fps
      const newValue = value + velocityRef.current * 0.016;
      
      setValue(newValue);
      
      // Continue animation if not at rest
      if (Math.abs(displacement) > 0.001 || Math.abs(velocityRef.current) > 0.001) {
        animationRef.current = requestAnimationFrame(animate);
      }
    };
    
    animationRef.current = requestAnimationFrame(animate);
    
    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [targetValue, stiffness, damping, mass, value]);
  
  return value;
};

// Lipgloss-inspired styling components
const CharmBox = ({ children, style, border = false, padding = true, margin = false, theme = 'primary', ...props }) => {
  const themeColors = {
    primary: CharmColors.primary,
    secondary: CharmColors.secondary,
    accent: CharmColors.accent,
  };
  
  const boxStyle = {
    ...(padding && { padding: '1rem' }),
    ...(margin && { margin: '0.5rem' }),
    ...(border && {
      border: `2px solid ${themeColors[theme]}`,
      borderRadius: '8px',
    }),
    backgroundColor: CharmColors.surface,
    color: CharmColors.text,
    fontFamily: 'ui-monospace, SFMono-Regular, monospace',
    ...style,
  };
  
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      style={boxStyle}
      {...props}
    >
      {children}
    </motion.div>
  );
};

// Glamour-inspired markdown-style text rendering
const CharmText = ({ children, variant = 'body', theme = 'primary', ...props }) => {
  const variants = {
    h1: { fontSize: '2rem', fontWeight: 'bold', marginBottom: '1rem' },
    h2: { fontSize: '1.5rem', fontWeight: 'bold', marginBottom: '0.75rem' },
    h3: { fontSize: '1.25rem', fontWeight: 'bold', marginBottom: '0.5rem' },
    body: { fontSize: '1rem', lineHeight: '1.5' },
    small: { fontSize: '0.875rem', color: CharmColors.muted },
    code: { 
      fontSize: '0.875rem', 
      fontFamily: 'ui-monospace, SFMono-Regular, monospace',
      backgroundColor: CharmColors.background,
      padding: '0.25rem 0.5rem',
      borderRadius: '4px',
    },
  };
  
  const themeColors = {
    primary: CharmColors.primary,
    secondary: CharmColors.secondary,
    accent: CharmColors.accent,
    muted: CharmColors.muted,
  };
  
  const textStyle = {
    color: themeColors[theme] || CharmColors.text,
    ...variants[variant],
  };
  
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.2 }}
      style={textStyle}
      {...props}
    >
      {children}
    </motion.div>
  );
};

// Main Charm Interface Component (integrates all Charm concepts)
const CharmInterface = ({ children, title, subtitle, onBack, actions = [] }) => {
  const [isVisible, setIsVisible] = useState(false);
  const [currentTime, setCurrentTime] = useState(new Date());
  
  useEffect(() => {
    setIsVisible(true);
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);
  
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: isVisible ? 1 : 0 }}
      transition={{ duration: 0.5 }}
      className="h-full w-full overflow-hidden"
      style={{ backgroundColor: CharmColors.background }}
    >
      {/* Header */}
      <CharmBox
        border={true}
        theme="primary"
        style={{
          background: `linear-gradient(135deg, ${CharmColors.primary}20, ${CharmColors.secondary}20)`,
          borderRadius: '0 0 1rem 1rem',
          marginBottom: '1rem',
        }}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            {onBack && (
              <motion.button
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.9 }}
                onClick={onBack}
                className="p-2 rounded-lg hover:bg-opacity-20 transition-colors duration-150"
                style={{ backgroundColor: `${CharmColors.primary}10` }}
              >
                <svg 
                  className="w-5 h-5" 
                  fill="none" 
                  stroke={CharmColors.primary} 
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
              </motion.button>
            )}
            
            <div>
              <CharmText variant="h2" theme="primary">
                🦆 {title || 'DuckBot Charm Interface'}
              </CharmText>
              {subtitle && (
                <CharmText variant="small" theme="muted">
                  {subtitle}
                </CharmText>
              )}
            </div>
          </div>
          
          <div className="flex items-center gap-4">
            {/* Actions */}
            {actions.map((action, index) => (
              <motion.button
                key={index}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={action.onClick}
                className="px-4 py-2 rounded-lg font-mono font-medium transition-colors duration-150"
                style={{
                  backgroundColor: CharmColors.accent,
                  color: CharmColors.background,
                }}
              >
                {action.icon} {action.label}
              </motion.button>
            ))}
            
            {/* Clock */}
            <CharmText variant="small" theme="muted">
              {currentTime.toLocaleTimeString()}
            </CharmText>
          </div>
        </div>
      </CharmBox>
      
      {/* Content */}
      <div className="px-6 pb-6 h-full overflow-y-auto">
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.2, duration: 0.5 }}
        >
          {children}
        </motion.div>
      </div>
    </motion.div>
  );
};

// Skate-inspired state management hook
const useCharmState = (key, initialValue) => {
  const [state, setState] = useState(() => {
    try {
      const stored = localStorage.getItem(`charm_${key}`);
      return stored ? JSON.parse(stored) : initialValue;
    } catch (error) {
      console.warn('Failed to load state from localStorage:', error);
      return initialValue;
    }
  });
  
  const updateState = (newState) => {
    setState(newState);
    try {
      localStorage.setItem(`charm_${key}`, JSON.stringify(newState));
    } catch (error) {
      console.warn('Failed to save state to localStorage:', error);
    }
  };
  
  return [state, updateState];
};

// Log-inspired logging component
const CharmLogger = ({ logs = [], maxLogs = 100, onClear }) => {
  const [filter, setFilter] = useState('');
  const [level, setLevel] = useState('all');
  
  const filteredLogs = useMemo(() => {
    return logs
      .filter(log => {
        const matchesFilter = !filter || log.message.toLowerCase().includes(filter.toLowerCase());
        const matchesLevel = level === 'all' || log.level === level;
        return matchesFilter && matchesLevel;
      })
      .slice(-maxLogs);
  }, [logs, filter, level, maxLogs]);
  
  const levelColors = {
    debug: CharmColors.muted,
    info: CharmColors.info,
    warn: CharmColors.warning,
    error: CharmColors.error,
  };
  
  return (
    <CharmBox border={true} theme="secondary">
      <div className="flex items-center justify-between mb-4">
        <CharmText variant="h3" theme="secondary">
          📝 System Logs
        </CharmText>
        
        <div className="flex gap-2">
          <GumSelect
            options={[
              { label: 'All Levels', value: 'all' },
              { label: 'Debug', value: 'debug' },
              { label: 'Info', value: 'info' },
              { label: 'Warning', value: 'warn' },
              { label: 'Error', value: 'error' },
            ]}
            onSelect={(option) => setLevel(option.value)}
            theme="secondary"
          />
          
          {onClear && (
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={onClear}
              className="px-3 py-1 rounded text-sm"
              style={{ backgroundColor: CharmColors.error, color: CharmColors.text }}
            >
              Clear
            </motion.button>
          )}
        </div>
      </div>
      
      <GumInput
        placeholder="Filter logs..."
        onSubmit={setFilter}
        theme="secondary"
      />
      
      <div 
        className="mt-4 max-h-64 overflow-y-auto font-mono text-sm"
        style={{ backgroundColor: CharmColors.background, borderRadius: '0.5rem', padding: '1rem' }}
      >
        {filteredLogs.length === 0 ? (
          <CharmText variant="small" theme="muted">
            No logs match your filter criteria
          </CharmText>
        ) : (
          filteredLogs.map((log, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.05 }}
              className="flex items-center gap-3 py-1 border-b border-opacity-20"
              style={{ borderColor: CharmColors.border }}
            >
              <span style={{ color: levelColors[log.level] || CharmColors.text }}>
                [{log.level.toUpperCase()}]
              </span>
              <span className="text-xs" style={{ color: CharmColors.muted }}>
                {new Date(log.timestamp).toLocaleTimeString()}
              </span>
              <span style={{ color: CharmColors.text }}>
                {log.message}
              </span>
            </motion.div>
          ))
        )}
      </div>
    </CharmBox>
  );
};

export {
  CharmInterface,
  CharmBox,
  CharmText,
  GumSelect,
  GumInput,
  CharmLogger,
  useSpringAnimation,
  useCharmState,
  CharmColors,
  createCharmStyle,
  CharmComponent,
};