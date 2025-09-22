import React from 'react';
import { ShelfProps } from './types';
import { APPS } from './apps';
import SystemTray from './SystemTray';
import { LauncherIcon, QuickSettingsIcon } from './apps';

const Shelf: React.FC<ShelfProps> = ({
  openWindows,
  onAppClick,
  onLauncherClick,
  onOpenApp,
  activeWindowId,
  onQuickSettingsClick
}) => {
  const pinnedApps = APPS.filter(app => app.isPinned);
  const openAndNotPinned = openWindows.filter(win => !APPS.find(app => app.id === win.appId)?.isPinned);

  const getAppIcon = (appId: string) => {
    return APPS.find(app => app.id === appId)?.icon;
  };

  const getAppTitle = (appId: string) => {
    return APPS.find(app => app.id === appId)?.title || '';
  };

  const handleAppIconClick = (appId: string) => {
    const openWindow = openWindows.find(w => w.appId === appId);
    if (openWindow) {
      onAppClick(openWindow.id);
    } else {
      onOpenApp(appId);
    }
  };

  return (
    <div
      id="shelf"
      className="fixed bottom-0 left-0 right-0 h-14 bg-gray-900/80 backdrop-blur-xl border-t border-gray-800/50 flex items-center justify-between px-3 z-[1000]"
    >
      {/* Left side - App icons */}
      <div className="flex items-center gap-2">
        {/* Launcher button */}
        <button
          onClick={onLauncherClick}
          className="group relative w-10 h-10 rounded-full flex items-center justify-center bg-gradient-to-br from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 transition-all duration-200 shadow-lg"
          aria-label="App Launcher"
        >
          <LauncherIcon className="w-6 h-6 text-white" />
          <div className="absolute inset-0 rounded-full bg-white/20 scale-0 group-hover:scale-100 transition-transform duration-200" />
        </button>

        {/* Quick Settings button */}
        <button
          onClick={onQuickSettingsClick}
          className="group relative w-10 h-10 rounded-full flex items-center justify-center bg-gray-700/50 hover:bg-gray-600/70 transition-all duration-200 hover:scale-110"
          aria-label="Quick Settings"
        >
          <QuickSettingsIcon className="w-6 h-6 text-gray-300 group-hover:text-white" />
          <div className="absolute inset-0 rounded-full bg-white/10 scale-0 group-hover:scale-100 transition-transform duration-200" />
        </button>

        {/* Pinned apps */}
        {pinnedApps.map(app => (
          <div key={app.id} className="relative group">
            <button
              onClick={() => handleAppIconClick(app.id)}
              className="group/app w-10 h-10 rounded-full flex items-center justify-center bg-gray-700/50 hover:bg-gray-600/70 transition-all duration-200 hover:scale-110"
              aria-label={`Open ${app.title}`}
            >
              <div className="w-7 h-7 text-white">
                {React.cloneElement(app.icon as React.ReactElement, { className: "w-full h-full" })}
              </div>
            </button>

            {/* Running indicator */}
            {openWindows.some(w => w.appId === app.id) && (
              <div className={`absolute bottom-0 left-1/2 -translate-x-1/2 w-4 h-1 rounded-full transition-colors ${
                openWindows.some(w => w.appId === app.id && w.id === activeWindowId)
                  ? 'bg-blue-400 shadow-blue-400/50'
                  : 'bg-gray-400'
              }`} />
            )}

            {/* Tooltip */}
            <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 bg-gray-800 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap">
              {app.title}
              {app.description && (
                <div className="text-gray-400 text-xs mt-1">{app.description}</div>
              )}
            </div>
          </div>
        ))}

        {/* Open unpinned apps */}
        {openAndNotPinned.map(win => (
          <div key={win.id} className="relative group">
            <button
              onClick={() => onAppClick(win.id)}
              className="group/app w-10 h-10 rounded-full flex items-center justify-center bg-gray-700/50 hover:bg-gray-600/70 transition-all duration-200 hover:scale-110"
              aria-label={`Focus ${win.title}`}
            >
              <div className="w-7 h-7 text-white">
                {React.cloneElement(getAppIcon(win.appId) as React.ReactElement, { className: "w-full h-full" })}
              </div>
            </button>

            {/* Active indicator */}
            <div className={`absolute bottom-0 left-1/2 -translate-x-1/2 w-4 h-1 rounded-full transition-colors ${
              win.id === activeWindowId
                ? 'bg-blue-400 shadow-blue-400/50'
                : 'bg-gray-400'
            }`} />

            {/* Tooltip */}
            <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 bg-gray-800 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap">
              {win.title}
              <div className="text-gray-400 text-xs mt-1">Click to focus</div>
            </div>
          </div>
        ))}
      </div>

      {/* Right side - System tray */}
      <SystemTray />
    </div>
  );
};

export default Shelf;