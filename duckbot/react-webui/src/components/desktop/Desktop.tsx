import React from 'react';
import { DesktopProps } from './types';

const Desktop: React.FC<DesktopProps> = ({ children, wallpaperUrl }) => {
  // Dynamic wallpaper with DuckBot theme
  const defaultWallpaper = "https://picsum.photos/1920/1080?grayscale&blur=1&seed=duckbot";
  const wallpaper = wallpaperUrl || defaultWallpaper;

  return (
    <div className="relative w-full h-full overflow-hidden">
      {/* Background */}
      <div
        className="absolute inset-0 w-full h-full bg-cover bg-center bg-no-repeat"
        style={{
          backgroundImage: `url(${wallpaper})`,
          filter: 'contrast(1.1) brightness(0.9)'
        }}
      />

      {/* Overlay for better readability */}
      <div className="absolute inset-0 bg-gradient-to-br from-black/20 via-transparent to-black/40" />

      {/* Desktop content area */}
      <div className="absolute inset-0 z-10">
        {children}
      </div>

      {/* Ambient lighting effect */}
      <div className="absolute top-0 left-0 w-full h-full pointer-events-none">
        <div className="absolute top-10 left-10 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl" />
        <div className="absolute bottom-20 right-20 w-80 h-80 bg-purple-500/10 rounded-full blur-3xl" />
      </div>
    </div>
  );
};

export default Desktop;