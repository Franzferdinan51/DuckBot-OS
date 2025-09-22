export interface WindowInstance {
  id: string;
  appId: string;
  title: string;
  x: number;
  y: number;
  width: number;
  height: number;
  zIndex: number;
  isMinimized: boolean;
  isMaximized: boolean;
}

export interface AppDefinition {
  id: string;
  title: string;
  icon: React.ReactNode;
  component: React.ComponentType;
  isPinned: boolean;
  defaultSize?: {
    width: number;
    height: number;
  };
  category?: 'productivity' | 'ai' | 'development' | 'system' | 'communication';
  description?: string;
}

export interface DesktopProps {
  children: React.ReactNode;
  wallpaperUrl?: string;
}

export interface ShelfProps {
  openWindows: WindowInstance[];
  onAppClick: (windowId: string) => void;
  onLauncherClick: () => void;
  onOpenApp: (appId: string) => void;
  activeWindowId: string | null;
  onQuickSettingsClick: () => void;
}

export interface WindowProps {
  instance: WindowInstance;
  isActive: boolean;
  children: React.ReactNode;
  onClose: () => void;
  onFocus: () => void;
  onUpdate: (updates: Partial<WindowInstance>) => void;
  onMinimize: () => void;
  onMaximize: () => void;
}

export interface LauncherProps {
  isVisible: boolean;
  setVisible: (visible: boolean) => void;
  onOpenApp: (appId: string) => void;
}

export interface SystemTrayProps {
  onSettingsClick?: () => void;
  onPowerClick?: () => void;
}