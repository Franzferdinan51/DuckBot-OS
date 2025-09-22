import React, { useState, useCallback, useEffect } from 'react';
import { WindowInstance } from './types';
import { APPS } from './apps';
import Desktop from './Desktop';
import Shelf from './Shelf';
import Window from './Window';
import Launcher from './Launcher';
import QuickSettings from './QuickSettings';
import './Desktop.css';

interface DuckBotOSProps {
  // Optional props for customization
  wallpaperUrl?: string;
  autoOpenApps?: string[];
  onWindowClose?: (appId: string) => void;
  onAppOpen?: (appId: string) => void;
}

const DuckBotOS: React.FC<DuckBotOSProps> = ({
  wallpaperUrl = "https://picsum.photos/1920/1080?grayscale&blur=2",
  autoOpenApps = ['assistant'],
  onWindowClose,
  onAppOpen
}) => {
  const [windows, setWindows] = useState<WindowInstance[]>([]);
  const [activeWindowId, setActiveWindowId] = useState<string | null>(null);
  const [nextZIndex, setNextZIndex] = useState<number>(10);
  const [isLauncherVisible, setLauncherVisible] = useState(false);
  const [isQuickSettingsVisible, setQuickSettingsVisible] = useState(false);
  const [currentWallpaperUrl, setCurrentWallpaperUrl] = useState(() => {
    // Try to load saved wallpaper from localStorage
    if (typeof window !== 'undefined') {
      const savedWallpaper = localStorage.getItem('duckbot-wallpaper-current');
      if (savedWallpaper) {
        try {
          const wallpaperData = JSON.parse(savedWallpaper);
          return wallpaperData.url || wallpaperUrl;
        } catch (error) {
          console.error('Error loading saved wallpaper:', error);
        }
      }
    }
    return wallpaperUrl;
  });

  // Open an application
  const openApp = useCallback((appId: string) => {
    const appDef = APPS.find(app => app.id === appId);
    if (!appDef) return;

    // Check if app is already open and not minimized
    const existingWindow = windows.find(w => w.appId === appId && !w.isMinimized);
    if (existingWindow) {
      focusWindow(existingWindow.id);
      return;
    }

    // Create new window
    const newWindow: WindowInstance = {
      id: `${appId}-${Date.now()}`,
      appId,
      title: appDef.title,
      x: Math.random() * 200 + 50,
      y: Math.random() * 200 + 50,
      width: appDef.defaultSize?.width || 800,
      height: appDef.defaultSize?.height || 600,
      zIndex: nextZIndex,
      isMinimized: false,
      isMaximized: false,
    };

    setWindows(prev => [...prev, newWindow]);
    setActiveWindowId(newWindow.id);
    setNextZIndex(prev => prev + 1);
    setLauncherVisible(false);

    // Notify parent component
    onAppOpen?.(appId);
  }, [windows, nextZIndex, onAppOpen]);

  // Auto-open specified apps on mount
  useEffect(() => {
    autoOpenApps.forEach(appId => {
      setTimeout(() => openApp(appId), 500 * (autoOpenApps.indexOf(appId) + 1));
    });
  }, [autoOpenApps, openApp]);

  // Focus a window
  const focusWindow = useCallback((windowId: string) => {
    if (activeWindowId === windowId) return;

    setWindows(prev =>
      prev.map(w =>
        w.id === windowId ? { ...w, zIndex: nextZIndex, isMinimized: false } : w
      )
    );
    setActiveWindowId(windowId);
    setNextZIndex(prev => prev + 1);
  }, [activeWindowId, nextZIndex]);

  // Close a window
  const closeWindow = useCallback((windowId: string) => {
    setWindows(prev => {
      const newWindows = prev.filter(w => w.id !== windowId);
      const closedWindow = prev.find(w => w.id === windowId);

      // Handle active window update within the same state update
      if (activeWindowId === windowId) {
        const remainingWindows = newWindows.filter(w => !w.isMinimized);
        const newActiveId = remainingWindows.length > 0
          ? [...remainingWindows].sort((a, b) => b.zIndex - a.zIndex)[0].id
          : null;

        // Use setTimeout to avoid batching issues
        setTimeout(() => setActiveWindowId(newActiveId), 0);
      }

      // Notify parent component after state update
      if (closedWindow) {
        setTimeout(() => onWindowClose?.(closedWindow.appId), 0);
      }

      return newWindows;
    });
  }, [activeWindowId, onWindowClose]);

  // Update window state
  const updateWindowState = useCallback((windowId: string, updates: Partial<WindowInstance>) => {
    setWindows(prev =>
      prev.map(w => (w.id === windowId ? { ...w, ...updates } : w))
    );
  }, []);

  // Toggle window minimize
  const toggleMinimize = useCallback((windowId: string) => {
    const window = windows.find(w => w.id === windowId);
    if (!window) return;

    if (window.isMinimized) {
      focusWindow(windowId);
    } else {
      updateWindowState(windowId, { isMinimized: true });
      if (activeWindowId === windowId) {
        // Use setTimeout to ensure state update completes before checking windows
        setTimeout(() => {
          const otherWindows = windows.filter(w => w.id !== windowId && !w.isMinimized);
          const topWindow = otherWindows.sort((a, b) => b.zIndex - a.zIndex)[0];
          setActiveWindowId(topWindow ? topWindow.id : null);
        }, 0);
      }
    }
  }, [windows, activeWindowId, updateWindowState, focusWindow]);

  // Toggle window maximize
  const toggleMaximize = useCallback((windowId: string) => {
    const window = windows.find(w => w.id === windowId);
    if (!window) return;
    updateWindowState(windowId, { isMaximized: !window.isMaximized });
    focusWindow(windowId);
  }, [updateWindowState, focusWindow]);

  // Get app definition by ID
  const getAppById = useCallback((appId: string) => {
    return APPS.find(app => app.id === appId);
  }, []);

  // Handle wallpaper change
  const handleWallpaperChange = useCallback((wallpaper: { url: string; name?: string; category?: string; id?: string; isCustom?: boolean }) => {
    const newWallpaperUrl = wallpaper.url;
    setCurrentWallpaperUrl(newWallpaperUrl);

    // Save to localStorage for persistence
    localStorage.setItem('duckbot-wallpaper-current', JSON.stringify({
      id: wallpaper.id,
      url: wallpaper.url,
      name: wallpaper.name,
      category: wallpaper.category,
      isCustom: wallpaper.isCustom
    }));
  }, []);

  // Global keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Ctrl/Cmd + Space: Open launcher
      if ((event.ctrlKey || event.metaKey) && event.code === 'Space') {
        event.preventDefault();
        setLauncherVisible(v => !v);
      }

      // Alt + Tab: Switch windows
      if (event.altKey && event.code === 'Tab') {
        event.preventDefault();
        const nonMinimizedWindows = windows.filter(w => !w.isMinimized);
        if (nonMinimizedWindows.length > 1) {
          const currentIndex = nonMinimizedWindows.findIndex(w => w.id === activeWindowId);
          const nextIndex = (currentIndex + 1) % nonMinimizedWindows.length;
          focusWindow(nonMinimizedWindows[nextIndex].id);
        }
      }

      // Ctrl/Cmd + W: Close active window
      if ((event.ctrlKey || event.metaKey) && event.code === 'KeyW' && activeWindowId) {
        event.preventDefault();
        closeWindow(activeWindowId);
      }

      // Ctrl/Cmd + M: Minimize active window
      if ((event.ctrlKey || event.metaKey) && event.code === 'KeyM' && activeWindowId) {
        event.preventDefault();
        toggleMinimize(activeWindowId);
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [windows, activeWindowId, focusWindow, closeWindow, toggleMinimize]);

  return (
    <div className="relative w-screen h-screen overflow-hidden bg-gray-900">
      {/* Desktop Background */}
      <Desktop wallpaperUrl={currentWallpaperUrl}>
        {/* Windows */}
        {windows.map(win => {
          const app = getAppById(win.appId);
          if (!app) return null;

          return (
            <Window
              key={win.id}
              instance={win}
              isActive={win.id === activeWindowId}
              onClose={() => closeWindow(win.id)}
              onFocus={() => focusWindow(win.id)}
              onUpdate={updates => updateWindowState(win.id, updates)}
              onMinimize={() => toggleMinimize(win.id)}
              onMaximize={() => toggleMaximize(win.id)}
            >
              <app.component />
            </Window>
          );
        })}
      </Desktop>

      {/* App Launcher */}
      <Launcher
        isVisible={isLauncherVisible}
        setVisible={setLauncherVisible}
        onOpenApp={openApp}
      />

      {/* Quick Settings Panel */}
      <QuickSettings
        isVisible={isQuickSettingsVisible}
        setVisible={setQuickSettingsVisible}
        onWallpaperChange={handleWallpaperChange}
        currentWallpaper={currentWallpaperUrl}
        connectionStatus="connected"
      />

      {/* Shelf/Dock */}
      <Shelf
        openWindows={windows}
        onAppClick={focusWindow}
        onLauncherClick={() => setLauncherVisible(v => !v)}
        onOpenApp={openApp}
        activeWindowId={activeWindowId}
        onQuickSettingsClick={() => setQuickSettingsVisible(v => !v)}
      />
    </div>
  );
};

export default DuckBotOS;