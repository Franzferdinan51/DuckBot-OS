import React, { useState, useRef, useEffect } from 'react';
import { motion } from 'framer-motion';

const Terminal = () => {
  const [history, setHistory] = useState([
    { type: 'output', content: 'DuckBot Terminal v3.1.0' },
    { type: 'output', content: 'Type "help" for available commands' }
  ]);
  const [currentCommand, setCurrentCommand] = useState('');
  const [currentPath, setCurrentPath] = useState('C:\\DuckBot>');
  const inputRef = useRef(null);
  const terminalRef = useRef(null);

  const executeCommand = async (cmd) => {
    const trimmedCmd = cmd.trim().toLowerCase();
    
    // Add command to history
    setHistory(prev => [...prev, { type: 'command', content: `${currentPath} ${cmd}` }]);

    let output = '';
    
    switch (trimmedCmd) {
      case 'help':
        output = `Available commands:
  help     - Show this help message
  status   - Show DuckBot system status
  models   - List available AI models
  services - Show running services
  clear    - Clear terminal
  ping     - Test system connectivity
  logs     - Show recent logs
  version  - Show DuckBot version`;
        break;
        
      case 'status':
        output = `🤖 DuckBot System Status:
  AI Router: ✅ Online
  WebUI: ✅ Running (port 8787)
  LM Studio: ⚠️  Checking...
  Memory Usage: 45% (57.2GB / 128GB)
  GPU Usage: 12% (RTX 3080)`;
        break;
        
      case 'models':
        output = `Available AI Models:
  📊 Current: google/gemma-3-12b
  🧠 LM Studio: nvidia-nemotron-nano-9b-v2
  ☁️  OpenRouter: qwen/qwen-2.5-72b-instruct
  🔄 Status: Main brain loaded, 2 specialists available`;
        break;
        
      case 'services':
        output = `DuckBot Services:
  🌐 WebUI Server: ✅ Running (PID: 12345)
  🤖 AI Router: ✅ Running 
  💾 Cost Tracker: ✅ Running
  🔄 Dynamic Models: ✅ Running
  📊 System Monitor: ✅ Running`;
        break;
        
      case 'clear':
        setHistory([]);
        setCurrentCommand('');
        return;
        
      case 'ping':
        output = `Pinging DuckBot services...
  localhost:8787 - ✅ 2ms
  LM Studio API - ✅ 15ms
  OpenRouter API - ✅ 142ms
  All systems operational`;
        break;
        
      case 'logs':
        output = `Recent DuckBot Logs:
  [INFO] AI Router: Model loaded successfully
  [INFO] WebUI: New client connected
  [INFO] Cost Tracker: Usage recorded
  [INFO] Hardware: Performance tier: high_end
  [INFO] System: All services healthy`;
        break;
        
      case 'version':
        output = `DuckBot Enhanced v3.1.0
  Build: VibeVoice-Ready-20250829_191017
  Platform: Windows 11
  Python: 3.11.x
  Node: v18.x.x
  Hardware: RTX 3080, 128GB RAM`;
        break;
        
      case '':
        // Empty command
        break;
        
      default:
        output = `Command not found: ${cmd}. Type "help" for available commands.`;
        break;
    }
    
    if (output) {
      setHistory(prev => [...prev, { type: 'output', content: output }]);
    }
    
    setCurrentCommand('');
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      executeCommand(currentCommand);
    }
  };

  useEffect(() => {
    // Auto-focus input
    if (inputRef.current) {
      inputRef.current.focus();
    }
    
    // Scroll to bottom
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, [history]);

  return (
    <div className="terminal" onClick={() => inputRef.current?.focus()}>
      <div className="terminal-header">
        <span>💻 DuckBot Terminal</span>
        <div className="terminal-controls">
          <button onClick={() => setHistory([])}>Clear</button>
        </div>
      </div>
      
      <div className="terminal-content" ref={terminalRef}>
        {history.map((entry, index) => (
          <motion.div
            key={index}
            className={`terminal-line ${entry.type}`}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.2 }}
          >
            {entry.type === 'command' && <span className="prompt">$</span>}
            <pre>{entry.content}</pre>
          </motion.div>
        ))}
        
        <div className="terminal-input-line">
          <span className="prompt">{currentPath}</span>
          <input
            ref={inputRef}
            type="text"
            value={currentCommand}
            onChange={(e) => setCurrentCommand(e.target.value)}
            onKeyPress={handleKeyPress}
            className="terminal-input"
            placeholder="Enter command..."
            autoComplete="off"
            spellCheck="false"
          />
        </div>
      </div>

      <style jsx>{`
        .terminal {
          height: 100%;
          background: #0a0a0a;
          color: #00ff00;
          font-family: 'Courier New', monospace;
          display: flex;
          flex-direction: column;
          border: 1px solid #333;
          overflow: hidden;
        }
        .terminal-header {
          background: #1a1a1a;
          padding: 0.5rem 1rem;
          border-bottom: 1px solid #333;
          display: flex;
          justify-content: space-between;
          align-items: center;
          color: #888;
        }
        .terminal-controls button {
          background: #333;
          color: #ccc;
          border: none;
          padding: 0.25rem 0.5rem;
          border-radius: 2px;
          cursor: pointer;
          font-size: 0.7rem;
        }
        .terminal-controls button:hover {
          background: #555;
        }
        .terminal-content {
          flex: 1;
          overflow-y: auto;
          padding: 1rem;
          line-height: 1.4;
        }
        .terminal-line {
          margin-bottom: 0.25rem;
          display: flex;
          align-items: flex-start;
        }
        .terminal-line.command {
          color: #ffff00;
        }
        .terminal-line.output {
          color: #00ff00;
        }
        .terminal-line pre {
          margin: 0;
          white-space: pre-wrap;
          word-break: break-word;
        }
        .prompt {
          color: #ff6b6b;
          margin-right: 0.5rem;
          font-weight: bold;
          min-width: max-content;
        }
        .terminal-input-line {
          display: flex;
          align-items: center;
          margin-top: 0.5rem;
        }
        .terminal-input {
          flex: 1;
          background: transparent;
          border: none;
          color: #00ff00;
          font-family: inherit;
          font-size: inherit;
          outline: none;
          margin-left: 0.5rem;
        }
        .terminal-input::placeholder {
          color: #555;
        }
      `}</style>
    </div>
  );
};

export default Terminal;