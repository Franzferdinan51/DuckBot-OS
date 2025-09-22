import React, { useRef, useEffect, useState } from 'react';
import WallpaperManager from './WallpaperManager';

interface Wallpaper {
  id: string;
  name: string;
  url: string;
  category: string;
  isCustom?: boolean;
}

interface QuickSettingsProps {
  isVisible: boolean;
  setVisible: (visible: boolean) => void;
  onWallpaperChange?: (wallpaper: Wallpaper) => void;
  currentWallpaper?: string;
  connectionStatus?: string;
}

const QuickSettings: React.FC<QuickSettingsProps> = ({
  isVisible,
  setVisible,
  onWallpaperChange,
  currentWallpaper,
  connectionStatus = 'disconnected'
}) => {
  const panelRef = useRef<HTMLDivElement>(null);
  const [brightness, setBrightness] = useState(80);
  const [volume, setVolume] = useState(50);
  const [wifiEnabled, setWifiEnabled] = useState(true);
  const [bluetoothEnabled, setBluetoothEnabled] = useState(false);
  const [notificationsEnabled, setNotificationsEnabled] = useState(true);
  const [isWallpaperManagerVisible, setIsWallpaperManagerVisible] = useState(false);

  const wallpapers = [
    { id: 'quick-abstract', name: 'Abstract', url: 'https://picsum.photos/1920/1080?random=1', category: 'abstract' },
    { id: 'quick-nature', name: 'Nature', url: 'https://picsum.photos/1920/1080?random=2', category: 'nature' },
    { id: 'quick-city', name: 'City', url: 'https://picsum.photos/1920/1080?random=3', category: 'city' },
    { id: 'quick-grayscale', name: 'Grayscale', url: 'https://picsum.photos/1920/1080?grayscale', category: 'minimal' },
    { id: 'quick-space', name: 'Space', url: 'https://picsum.photos/1920/1080?random=4', category: 'space' },
    { id: 'quick-minimal', name: 'Minimal', url: 'https://picsum.photos/1920/1080?random=5', category: 'minimal' },
  ];

  // Load saved wallpaper from localStorage on mount
  useEffect(() => {
    const savedWallpaper = localStorage.getItem('duckbot-wallpaper-current');
    if (savedWallpaper) {
      try {
        const wallpaperData = JSON.parse(savedWallpaper);
        onWallpaperChange?.(wallpaperData);
      } catch (error) {
        console.error('Error loading saved wallpaper:', error);
      }
    }
  }, []);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (panelRef.current && !panelRef.current.contains(event.target as Node)) {
        const shelf = document.getElementById('shelf');
        if (shelf && shelf.contains(event.target as Node)) {
          return;
        }
        setVisible(false);
      }
    };

    if (isVisible) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isVisible, setVisible]);

  if (!isVisible) return null;

  const IconBtn: React.FC<{children: React.ReactNode, active?: boolean, onClick?: () => void}> = ({children, active, onClick}) => (
    <button
      onClick={onClick}
      className={`w-12 h-12 rounded-full flex items-center justify-center transition-colors ${
        active ? 'bg-blue-500 text-white' : 'bg-gray-200/20 hover:bg-gray-200/40 text-gray-200'
      }`}
    >
      {children}
    </button>
  );

  return (
    <div
      ref={panelRef}
      className="absolute bottom-16 right-2 w-80 bg-gray-800/90 backdrop-blur-2xl rounded-2xl p-4 shadow-2xl z-[1500] animate-fade-in border border-gray-700/50"
    >
      <style jsx>{`
        @keyframes fade-in {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .animate-fade-in {
          animation: fade-in 0.2s ease-out forwards;
        }
      `}</style>

      {/* User Profile Section */}
      <div className="flex items-center justify-between pb-4 border-b border-white/10">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center">
            <span className="text-white font-semibold">DB</span>
          </div>
          <div>
            <p className="font-semibold text-white">DuckBot User</p>
            <p className="text-xs text-gray-400">AI Assistant Ready</p>
          </div>
        </div>
        <div className="flex gap-2">
          <button className="w-8 h-8 rounded-full bg-gray-500/50 hover:bg-gray-500/80 flex items-center justify-center transition-colors">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M3 5a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM3 10a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM3 15a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clipRule="evenodd" />
            </svg>
          </button>
          <button className="w-8 h-8 rounded-full bg-gray-500/50 hover:bg-gray-500/80 flex items-center justify-center transition-colors">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
              <path d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" />
            </svg>
          </button>
        </div>
      </div>

      {/* Connection Status */}
      <div className="py-3 border-b border-white/10">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm text-gray-300">AI Service</span>
          <span className={`text-xs px-2 py-1 rounded-full ${
            connectionStatus === 'connected' ? 'bg-green-500/20 text-green-400' :
            connectionStatus === 'connecting' ? 'bg-yellow-500/20 text-yellow-400' :
            'bg-red-500/20 text-red-400'
          }`}>
            {connectionStatus}
          </span>
        </div>
      </div>

      {/* Quick Toggles */}
      <div className="grid grid-cols-4 gap-3 py-4">
        <IconBtn active={wifiEnabled} onClick={() => setWifiEnabled(!wifiEnabled)}>
          <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.111 16.404a5.5 5.5 0 017.778 0M12 20h.01m-7.08-7.071a10 10 0 0114.142 0M18.364 5.636a15 15 0 010 21.213" />
          </svg>
        </IconBtn>
        <IconBtn active={bluetoothEnabled} onClick={() => setBluetoothEnabled(!bluetoothEnabled)}>
          <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5.636 18.364a9 9 0 010-12.728m12.728 0a9 9 0 010 12.728m-9.9-2.829a4 4 0 100-5.656 4 4 0 000 5.656z" />
          </svg>
        </IconBtn>
        <IconBtn active={notificationsEnabled} onClick={() => setNotificationsEnabled(!notificationsEnabled)}>
          <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
          </svg>
        </IconBtn>
        <IconBtn>
          <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zm4 8a4 4 0 11-8 0 4 4 0 018 0zm-.464 4.95l.707.707a1 1 0 001.414-1.414l-.707-.707a1 1 0 00-1.414 1.414zm2.12-10.607a1 1 0 010 1.414l-.706.707a1 1 0 11-1.414-1.414l.707-.707a1 1 0 011.414 0zM17 11a1 1 0 100-2h-1a1 1 0 100 2h1zm-7 4a1 1 0 011 1v1a1 1 0 11-2 0v-1a1 1 0 011-1zM5.05 6.464A1 1 0 106.465 5.05l-.708-.707a1 1 0 00-1.414 1.414l.707.707zm-.707 10.607a1 1 0 011.414 0l.707-.707a1 1 0 11-1.414 1.414l-.707.707a1 1 0 01-1.414 0zM4 11a1 1 0 100-2H3a1 1 0 000 2h1z" clipRule="evenodd" />
          </svg>
        </IconBtn>
      </div>

      {/* Sliders */}
      <div className="space-y-4 pb-4 border-b border-white/10">
        <div className="flex items-center gap-3">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-gray-400" viewBox="0 0 20 20" fill="currentColor">
            <path d="M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zm4 8a4 4 0 11-8 0 4 4 0 018 0z" />
          </svg>
          <input
            type="range"
            min="0"
            max="100"
            value={brightness}
            onChange={(e) => setBrightness(parseInt(e.target.value))}
            className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer slider"
          />
          <span className="text-xs text-gray-400 w-8">{brightness}%</span>
        </div>

        <div className="flex items-center gap-3">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-gray-400" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M9.383 3.076A1 1 0 0110 4v12a1 1 0 01-1.707.707L4.586 13H2a1 1 0 01-1-1V8a1 1 0 011-1h2.586l3.707-3.707a1 1 0 011.09-.217zM14.657 2.929a1 1 0 011.414 0A9.972 9.972 0 0119 10a9.972 9.972 0 01-2.929 7.071 1 1 0 01-1.414-1.414A7.971 7.971 0 0017 10c0-2.21-.894-4.208-2.343-5.657a1 1 0 010-1.414zm-2.829 2.828a1 1 0 011.415 0A5.983 5.983 0 0115 10a5.984 5.984 0 01-1.757 4.243 1 1 0 01-1.415-1.415A3.984 3.984 0 0013 10a3.983 3.983 0 00-1.172-2.828 1 1 0 010-1.415z" clipRule="evenodd" />
          </svg>
          <input
            type="range"
            min="0"
            max="100"
            value={volume}
            onChange={(e) => setVolume(parseInt(e.target.value))}
            className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer slider"
          />
          <span className="text-xs text-gray-400 w-8">{volume}%</span>
        </div>
      </div>

      {/* Wallpaper Selection */}
      <div className="py-4">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-medium text-gray-300">Wallpaper</h3>
          <button
            onClick={() => setIsWallpaperManagerVisible(true)}
            className="text-xs text-blue-400 hover:text-blue-300 transition-colors flex items-center gap-1"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10 5a1 1 0 011 1v3h3a1 1 0 110 2h-3v3a1 1 0 11-2 0v-3H6a1 1 0 110-2h3V6a1 1 0 011-1z" clipRule="evenodd" />
            </svg>
            More
          </button>
        </div>
        <div className="grid grid-cols-3 gap-2">
          {wallpapers.map(wp => (
            <div
              key={wp.name}
              className="cursor-pointer group"
              onClick={() => onWallpaperChange?.(wp)}
            >
              <img
                src={wp.url}
                alt={wp.name}
                className={`w-full h-16 object-cover rounded-md border-2 transition-all ${
                  currentWallpaper === wp.url
                    ? 'border-blue-500 shadow-lg shadow-blue-500/25'
                    : 'border-transparent group-hover:border-blue-500'
                }`}
              />
              <p className="text-xs text-gray-400 text-center mt-1 group-hover:text-gray-300 transition-colors">
                {wp.name}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Wallpaper Manager */}
      <WallpaperManager
        isVisible={isWallpaperManagerVisible}
        onClose={() => setIsWallpaperManagerVisible(false)}
        onWallpaperSelect={onWallpaperChange || (() => {})}
        currentWallpaper={currentWallpaper}
      />

      {/* Quick Actions */}
      <div className="pt-3 flex justify-between items-center">
        <button className="text-xs text-gray-400 hover:text-gray-300 transition-colors">
          Settings
        </button>
        <div className="text-xs text-gray-500">
          DuckBotOS v4.2
        </div>
      </div>
    </div>
  );
};

export default QuickSettings;