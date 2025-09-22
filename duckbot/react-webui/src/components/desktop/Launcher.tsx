import React, { useRef, useEffect, useState, useCallback } from 'react';
import { LauncherProps } from './types';
import { APPS, APP_CATEGORIES } from './apps';
import { Search, ArrowLeft, Brain, Sparkles, Clock } from 'lucide-react';

const Launcher: React.FC<LauncherProps> = ({ isVisible, setVisible, onOpenApp }) => {
  const launcherRef = useRef<HTMLDivElement>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [selectedIndex, setSelectedIndex] = useState(0);

  // Filter apps based on search and category
  const filteredApps = APPS.filter(app => {
    const matchesSearch = app.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         app.description?.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory = selectedCategory === 'all' || app.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  // Handle click outside to close
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (launcherRef.current && !launcherRef.current.contains(event.target as Node)) {
        const shelf = document.getElementById('shelf');
        if (shelf && shelf.contains(event.target as Node)) {
          return;
        }
        setVisible(false);
      }
    };

    if (isVisible) {
      document.addEventListener('mousedown', handleClickOutside);
      // Reset state when opening
      setSearchQuery('');
      setSelectedCategory('all');
      setSelectedIndex(0);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isVisible, setVisible]);

  // Handle keyboard navigation
  useEffect(() => {
    if (!isVisible) return;

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setVisible(false);
        return;
      }

      if (event.key === 'ArrowDown') {
        event.preventDefault();
        setSelectedIndex(prev => (prev + 1) % filteredApps.length);
      } else if (event.key === 'ArrowUp') {
        event.preventDefault();
        setSelectedIndex(prev => (prev - 1 + filteredApps.length) % filteredApps.length);
      } else if (event.key === 'Enter' && filteredApps[selectedIndex]) {
        onOpenApp(filteredApps[selectedIndex].id);
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isVisible, setVisible, onOpenApp, filteredApps, selectedIndex]);

  if (!isVisible) return null;

  return (
    <div
      ref={launcherRef}
      className="absolute bottom-16 left-1/2 -translate-x-1/2 w-[95vw] max-w-4xl h-auto max-h-[75vh] bg-gray-800/90 backdrop-blur-2xl rounded-2xl border border-gray-700/50 shadow-2xl animate-fade-in-up"
    >
      {/* Animation styles */}
      <style>{`
        @keyframes fade-in-up {
          from {
            opacity: 0;
            transform: translate(-50%, 20px);
          }
          to {
            opacity: 1;
            transform: translate(-50%, 0);
          }
        }
        .animate-fade-in-up {
          animation: fade-in-up 0.3s ease-out forwards;
        }
      `}</style>

      {/* Header */}
      <div className="p-6 border-b border-gray-700/50">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-semibold text-gray-200">Applications</h2>
          <button
            onClick={() => setVisible(false)}
            className="p-2 rounded-lg hover:bg-gray-700/50 transition-colors"
            aria-label="Close launcher"
          >
            <ArrowLeft className="w-5 h-5 text-gray-400" />
          </button>
        </div>

        {/* Search Bar */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            placeholder="Search applications..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-3 bg-gray-700/50 border border-gray-600/50 rounded-lg text-gray-200 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
            autoFocus
          />
        </div>
      </div>

      {/* Category Filter */}
      <div className="px-6 py-3 border-b border-gray-700/50">
        <div className="flex items-center space-x-2 overflow-x-auto">
          <button
            onClick={() => setSelectedCategory('all')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors whitespace-nowrap ${
              selectedCategory === 'all'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-700/50 text-gray-300 hover:bg-gray-700'
            }`}
          >
            All Apps ({APPS.length})
          </button>
          {Object.entries(APP_CATEGORIES).map(([key, label]) => {
            const count = APPS.filter(app => app.category === key).length;
            return (
              <button
                key={key}
                onClick={() => setSelectedCategory(key)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors whitespace-nowrap ${
                  selectedCategory === key
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-700/50 text-gray-300 hover:bg-gray-700'
                }`}
              >
                {label} ({count})
              </button>
            );
          })}
        </div>
      </div>

      {/* App Grid */}
      <div className="p-6 overflow-y-auto max-h-[50vh]">
        {filteredApps.length === 0 ? (
          <div className="text-center py-8">
            <div className="text-gray-400 text-lg mb-2">No applications found</div>
            <div className="text-gray-500 text-sm">Try adjusting your search or category filter</div>
          </div>
        ) : (
          <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6 gap-6">
            {filteredApps.map((app, index) => (
              <div
                key={app.id}
                className={`flex flex-col items-center gap-3 text-center cursor-pointer group p-4 rounded-xl transition-all duration-200 ${
                  index === selectedIndex
                    ? 'bg-blue-600/20 border border-blue-500/50'
                    : 'hover:bg-gray-700/50'
                }`}
                onClick={() => onOpenApp(app.id)}
                onMouseEnter={() => setSelectedIndex(index)}
              >
                <div className={`w-16 h-16 rounded-2xl flex items-center justify-center transition-all duration-200 ${
                  index === selectedIndex
                    ? 'bg-blue-600 text-white scale-110 shadow-lg shadow-blue-500/30'
                    : 'bg-gray-700 group-hover:bg-gray-600 text-gray-300 group-hover:text-white group-hover:scale-105'
                }`}>
                  {React.cloneElement(app.icon as React.ReactElement, { className: "w-8 h-8" })}
                </div>
                <div className="space-y-1">
                  <span className={`text-sm font-medium transition-colors ${
                    index === selectedIndex
                      ? 'text-blue-400'
                      : 'text-gray-300 group-hover:text-white'
                  }`}>
                    {app.title}
                  </span>
                  {app.description && (
                    <span className="text-xs text-gray-500 line-clamp-2">
                      {app.description}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="px-6 py-3 border-t border-gray-700/50">
        <div className="flex items-center justify-between text-sm text-gray-400">
          <div>{filteredApps.length} application{filteredApps.length !== 1 ? 's' : ''} found</div>
          <div className="flex items-center space-x-4">
            <span>↑↓ Navigate</span>
            <span>↵ Open</span>
            <span>Esc Close</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Launcher;