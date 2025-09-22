import React, { useState, useEffect } from 'react';
import AppWithRouting from './AppWithRouting.tsx';
import AppDesktop from './AppDesktop.tsx';

const AppSwitcher: React.FC = () => {
  const [interfaceMode, setInterfaceMode] = useState<'classic' | 'desktop'>('desktop');

  // Load interface preference from localStorage
  useEffect(() => {
    try {
      const savedMode = localStorage.getItem('duckbotInterfaceMode');
      if (savedMode === 'classic' || savedMode === 'desktop') {
        setInterfaceMode(savedMode);
      }
    } catch (error) {
      console.error("Failed to load interface mode preference:", error);
    }
  }, []);

  // Save interface preference
  const handleModeChange = (mode: 'classic' | 'desktop') => {
    setInterfaceMode(mode);
    try {
      localStorage.setItem('duckbotInterfaceMode', mode);
    } catch (error) {
      console.error("Failed to save interface mode preference:", error);
    }
  };

  return (
    <div className="w-full h-full">
      {/* Mode Switcher (only in development or when enabled) */}
      {process.env.NODE_ENV === 'development' && (
        <div className="fixed top-4 left-1/2 -translate-x-1/2 z-50">
          <div className="bg-gray-800/90 backdrop-blur-sm rounded-lg p-2 flex items-center space-x-2 border border-gray-700">
            <button
              onClick={() => handleModeChange('classic')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                interfaceMode === 'classic'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              Classic Interface
            </button>
            <button
              onClick={() => handleModeChange('desktop')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                interfaceMode === 'desktop'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              Desktop OS Interface
            </button>
          </div>
        </div>
      )}

      {/* Render selected interface */}
      {interfaceMode === 'desktop' ? <AppDesktop /> : <AppWithRouting />}
    </div>
  );
};

export default AppSwitcher;