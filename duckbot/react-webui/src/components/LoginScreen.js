import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { useAuth } from '../contexts/AuthContext';
import toast from 'react-hot-toast';

const LoginScreen = () => {
  const { login } = useAuth();
  const [token, setToken] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showTokenHelp, setShowTokenHelp] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    
    if (!token.trim()) {
      toast.error('Please enter your DuckBot token');
      return;
    }

    setIsLoading(true);
    const success = await login(token.trim());
    
    if (!success) {
      setIsLoading(false);
    }
  };

  const handleQuickConnect = () => {
    // Try to connect to default WebUI URL to get token
    window.location.href = 'http://localhost:8787';
  };

  return (
    <div className="login-screen h-screen w-screen bg-slate-900 flex items-center justify-center relative overflow-hidden">
      {/* Animated Background */}
      <div className="absolute inset-0 opacity-20">
        <div className="grid-bg h-full w-full"></div>
      </div>

      {/* Floating Neural Nodes */}
      <div className="absolute inset-0 pointer-events-none">
        {[...Array(15)].map((_, i) => (
          <motion.div
            key={i}
            className="absolute w-3 h-3 bg-blue-400/30 rounded-full"
            style={{
              left: `${Math.random() * 100}%`,
              top: `${Math.random() * 100}%`,
            }}
            animate={{
              scale: [0.5, 1.2, 0.5],
              opacity: [0.2, 0.6, 0.2],
            }}
            transition={{
              duration: 3 + Math.random() * 2,
              repeat: Infinity,
              delay: Math.random() * 2,
            }}
          />
        ))}
      </div>

      {/* Main Login Form */}
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ duration: 0.5 }}
        className="glass-strong rounded-3xl p-10 max-w-md w-full mx-4 relative z-10"
      >
        {/* Header */}
        <div className="text-center mb-8">
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.2, type: "spring", stiffness: 200 }}
            className="w-24 h-24 mx-auto mb-6 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-2xl flex items-center justify-center text-4xl shadow-xl"
          >
            🤖
          </motion.div>
          
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="text-3xl font-bold text-white mb-2"
          >
            DuckBot AI OS
          </motion.h1>
          
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="text-slate-300"
          >
            Advanced AI Desktop Environment
          </motion.p>
        </div>

        {/* Login Form */}
        <form onSubmit={handleLogin} className="space-y-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
          >
            <label className="block text-sm font-medium text-slate-300 mb-2">
              DuckBot WebUI Token
            </label>
            <input
              type="password"
              value={token}
              onChange={(e) => setToken(e.target.value)}
              placeholder="Enter your authentication token..."
              className="input-field"
              disabled={isLoading}
            />
            
            {/* Token Help */}
            <div className="mt-2">
              <button
                type="button"
                onClick={() => setShowTokenHelp(!showTokenHelp)}
                className="text-xs text-blue-400 hover:text-blue-300 transition-colors"
              >
                Where do I find my token? {showTokenHelp ? '−' : '+'}
              </button>
              
              {showTokenHelp && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  className="mt-2 p-3 bg-slate-800/50 rounded-lg text-xs text-slate-300"
                >
                  <p className="mb-2">To get your DuckBot token:</p>
                  <ol className="list-decimal list-inside space-y-1 text-slate-400">
                    <li>Start DuckBot WebUI (START_ENHANCED_DUCKBOT.bat)</li>
                    <li>Look for the token in the console output</li>
                    <li>Or visit: http://localhost:8787</li>
                    <li>The token will be in the URL or displayed on screen</li>
                  </ol>
                </motion.div>
              )}
            </div>
          </motion.div>

          {/* Login Button */}
          <motion.button
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6 }}
            type="submit"
            disabled={isLoading}
            className="btn-primary w-full flex items-center justify-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <>
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                  className="w-5 h-5 border-2 border-white border-t-transparent rounded-full"
                />
                <span>Connecting...</span>
              </>
            ) : (
              <>
                <span>🚀</span>
                <span>Launch AI OS</span>
              </>
            )}
          </motion.button>

          {/* Quick Connect */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.7 }}
            className="text-center"
          >
            <div className="text-xs text-slate-400 mb-3">Or</div>
            <button
              type="button"
              onClick={handleQuickConnect}
              className="btn-secondary text-sm"
            >
              Open DuckBot WebUI
            </button>
          </motion.div>
        </form>

        {/* Features Preview */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.8 }}
          className="mt-8 pt-6 border-t border-slate-700"
        >
          <div className="text-xs text-slate-400 text-center mb-4">
            Powered by DuckBot v3.0.6+ with integrated features:
          </div>
          
          <div className="grid grid-cols-2 gap-3 text-xs">
            <div className="flex items-center space-x-2">
              <span className="text-blue-400">🤖</span>
              <span className="text-slate-300">AI Chat & Routing</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-purple-400">🧠</span>
              <span className="text-slate-300">LM Studio Integration</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-cyan-400">🌐</span>
              <span className="text-slate-300">OpenRouter Support</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-green-400">📚</span>
              <span className="text-slate-300">RAG Knowledge Base</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-yellow-400">🎯</span>
              <span className="text-slate-300">Desktop Automation</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-pink-400">💰</span>
              <span className="text-slate-300">Cost Analytics</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-orange-400">📊</span>
              <span className="text-slate-300">System Monitoring</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-indigo-400">⚙️</span>
              <span className="text-slate-300">Service Management</span>
            </div>
          </div>
        </motion.div>

        {/* Version Info */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1 }}
          className="mt-6 text-center text-xs text-slate-500"
        >
          <div className="flex justify-center space-x-4">
            <span>React WebUI v3.1.0</span>
            <span>•</span>
            <span>DuckBot Core v3.0.6+</span>
          </div>
          <div className="mt-1">
            Inspired by ByteBot, Archon OS & LLM-OS
          </div>
        </motion.div>
      </motion.div>

      {/* Decorative Elements */}
      <div className="absolute top-10 left-10 text-6xl opacity-5">🤖</div>
      <div className="absolute top-20 right-20 text-4xl opacity-5">🧠</div>
      <div className="absolute bottom-20 left-20 text-5xl opacity-5">⚡</div>
      <div className="absolute bottom-10 right-10 text-3xl opacity-5">🔮</div>
    </div>
  );
};

export default LoginScreen;