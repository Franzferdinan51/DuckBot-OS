import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';

const LoadingScreen = ({ message = "Loading DuckBot AI OS..." }) => {
  const [progress, setProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState(0);
  
  const steps = [
    "Initializing AI Operating System...",
    "Connecting to DuckBot WebUI...",
    "Loading AI Models...",
    "Checking LM Studio Connection...",
    "Verifying OpenRouter Status...",
    "Starting System Services...",
    "Loading Desktop Environment...",
    "Finalizing Setup..."
  ];

  useEffect(() => {
    const interval = setInterval(() => {
      setProgress(prev => {
        const newProgress = prev + Math.random() * 15;
        
        // Update current step based on progress
        const stepIndex = Math.floor((newProgress / 100) * steps.length);
        setCurrentStep(Math.min(stepIndex, steps.length - 1));
        
        return Math.min(newProgress, 95);
      });
    }, 200);

    // Complete loading after a reasonable time
    const completeTimer = setTimeout(() => {
      setProgress(100);
      setCurrentStep(steps.length - 1);
    }, 3000);

    return () => {
      clearInterval(interval);
      clearTimeout(completeTimer);
    };
  }, []);

  return (
    <div className="loading-screen h-screen w-screen bg-slate-900 flex items-center justify-center relative overflow-hidden">
      {/* Animated Background */}
      <div className="absolute inset-0 opacity-20">
        <div className="grid-bg h-full w-full"></div>
      </div>
      
      {/* Neural Network Animation */}
      <div className="absolute inset-0 pointer-events-none">
        {[...Array(20)].map((_, i) => (
          <motion.div
            key={i}
            className="absolute w-2 h-2 bg-blue-400 rounded-full opacity-60"
            style={{
              left: `${Math.random() * 100}%`,
              top: `${Math.random() * 100}%`,
            }}
            animate={{
              scale: [0.5, 1.5, 0.5],
              opacity: [0.3, 0.8, 0.3],
            }}
            transition={{
              duration: 2 + Math.random() * 2,
              repeat: Infinity,
              delay: Math.random() * 2,
            }}
          />
        ))}
      </div>

      {/* Main Loading Content */}
      <div className="glass-strong rounded-2xl p-8 max-w-md w-full mx-4 text-center relative z-10">
        {/* Logo/Icon */}
        <motion.div
          className="mb-8"
          animate={{ rotate: 360 }}
          transition={{ duration: 8, repeat: Infinity, ease: "linear" }}
        >
          <div className="w-20 h-20 mx-auto bg-gradient-to-r from-blue-500 to-cyan-500 rounded-2xl flex items-center justify-center text-3xl font-bold text-white">
            🤖
          </div>
        </motion.div>

        {/* Title */}
        <motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-2xl font-bold text-white mb-2"
        >
          DuckBot AI OS
        </motion.h1>
        
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="text-slate-300 text-sm mb-8"
        >
          Advanced AI Desktop Environment
        </motion.p>

        {/* Progress Bar */}
        <div className="mb-6">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm text-slate-400">Progress</span>
            <span className="text-sm text-blue-400 font-mono">{Math.round(progress)}%</span>
          </div>
          
          <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
            <motion.div
              className="h-full bg-gradient-to-r from-blue-500 to-cyan-500 rounded-full"
              initial={{ width: 0 }}
              animate={{ width: `${progress}%` }}
              transition={{ duration: 0.3 }}
            />
          </div>
        </div>

        {/* Current Step */}
        <motion.div
          key={currentStep}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center"
        >
          <p className="text-sm text-slate-300 mb-4">
            {steps[currentStep] || message}
          </p>
          
          {/* Loading Animation */}
          <div className="flex justify-center items-center space-x-1">
            {[...Array(3)].map((_, i) => (
              <motion.div
                key={i}
                className="w-2 h-2 bg-cyan-400 rounded-full"
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
        </motion.div>

        {/* System Info */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1 }}
          className="mt-8 pt-6 border-t border-slate-700"
        >
          <div className="grid grid-cols-2 gap-4 text-xs text-slate-400">
            <div className="text-center">
              <div className="text-cyan-400 font-semibold">React WebUI</div>
              <div>v3.1.0</div>
            </div>
            <div className="text-center">
              <div className="text-cyan-400 font-semibold">DuckBot Core</div>
              <div>v3.0.6+</div>
            </div>
          </div>
        </motion.div>

        {/* Features Preview */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 1.5 }}
          className="mt-6 text-xs text-slate-500"
        >
          <div className="flex flex-wrap justify-center gap-2">
            {[
              "AI Chat", "LM Studio", "OpenRouter", "ByteBot", "Archon", "RAG", "Cost Analytics"
            ].map((feature, index) => (
              <motion.span
                key={feature}
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 2 + index * 0.1 }}
                className="bg-slate-800/50 px-2 py-1 rounded text-cyan-400"
              >
                {feature}
              </motion.span>
            ))}
          </div>
        </motion.div>
      </div>

      {/* Floating Elements */}
      <div className="absolute inset-0 pointer-events-none">
        {[...Array(8)].map((_, i) => (
          <motion.div
            key={i}
            className="absolute text-4xl opacity-10"
            style={{
              left: `${10 + (i * 12)}%`,
              top: `${20 + Math.sin(i) * 30}%`,
            }}
            animate={{
              y: [-20, 20, -20],
              rotate: [0, 5, -5, 0],
            }}
            transition={{
              duration: 4 + Math.random() * 2,
              repeat: Infinity,
              delay: i * 0.5,
            }}
          >
            {['🤖', '🧠', '⚡', '🔮', '💫', '🌐', '📊', '🎯'][i]}
          </motion.div>
        ))}
      </div>
    </div>
  );
};

export default LoadingScreen;