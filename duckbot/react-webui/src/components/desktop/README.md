# DuckBotOS Desktop UI Components

This directory contains the enhanced desktop OS-like interface components for DuckBot, inspired by chroma-web-os design patterns.

## Components Overview

### Core Components

#### DuckBotOS (`DuckBotOS.tsx`)
- Main orchestrator component that manages the entire desktop interface
- Handles window lifecycle, app launching, and global state
- Integrates all sub-components (Desktop, Shelf, Window, Launcher)

#### Desktop (`Desktop.tsx`)
- Background wallpaper and ambient lighting effects
- Container for all window instances
- Supports dynamic wallpaper URLs

#### Window (`Window.tsx`)
- Draggable, resizable window management system
- Minimize, maximize, close functionality
- Z-index management for overlapping windows
- Corner resize handles
- Title bar with window controls

#### Shelf (`Shelf.tsx`)
- Bottom dock with app launching capabilities
- Pinned and running app indicators
- System tray integration (WiFi, battery, volume, clock, settings)
- Active window highlighting

#### Launcher (`Launcher.tsx`)
- Full-screen app launcher with fade-in-up animations
- Search functionality with real-time filtering
- Category-based app organization
- Keyboard navigation support (↑↓, Enter, Esc)
- Grid-based app layout with hover effects

### App Components

#### ThreeAssistantApp (`apps.tsx`)
- Enhanced 3D assistant with interaction tracking
- Loading progress indicators
- Control overlays for user guidance

#### ChatUIApp (`ChatUIApp.tsx`)
- Full-featured chat interface for DuckBot
- Message history with timestamps
- Voice input support
- Quick action buttons
- Typing indicators and loading states

#### SystemMonitorApp (`apps.tsx`)
- System performance monitoring
- Real-time metrics display
- Resource usage visualization

#### FileManagerApp (`apps.tsx`)
- File system navigation interface
- Project organization tools
- AI model file management

## Key Features

### Window Management
- **Drag & Drop**: Click and drag window title bars to move windows
- **Resize**: Corner handles for resizing windows
- **Minimize/Maximize**: Full window state management
- **Z-Index**: Automatic focus management with proper layering
- **Multi-window**: Support for multiple concurrent app instances

### App Launcher
- **Keyboard Shortcuts**:
  - `Ctrl/Cmd + Space`: Open/Close launcher
  - `Alt + Tab`: Switch between windows
  - `Ctrl/Cmd + W`: Close active window
  - `Ctrl/Cmd + M`: Minimize active window
- **Search**: Real-time app search by name and description
- **Categories**: Filter apps by type (AI, Development, Productivity, System)
- **Grid Layout**: Responsive app grid with hover animations

### System Integration
- **Settings Modal**: Comprehensive settings for AI providers, voices, and preferences
- **System Tray**: Status indicators for WiFi, battery, volume, and time
- **Connection Status**: Real-time AI service connection monitoring
- **Electron Integration**: Support for system tray, minimize to tray, and quit functions

### Visual Design
- **Dark Theme**: Modern dark interface with DuckBot branding
- **Glassmorphism**: Backdrop blur effects for modern aesthetics
- **Smooth Animations**: Fade-in-up launcher and window transitions
- **Responsive Design**: Adapts to different screen sizes
- **Accessibility**: Proper ARIA labels and keyboard navigation

## Usage

### Basic Usage
```tsx
import DuckBotOS from './desktop/DuckBotOS';

function App() {
  return (
    <DuckBotOS
      wallpaperUrl="https://example.com/wallpaper.jpg"
      autoOpenApps={['assistant', 'chat']}
      onAppOpen={(appId) => console.log('App opened:', appId)}
      onWindowClose={(appId) => console.log('App closed:', appId)}
    />
  );
}
```

### Enhanced Usage with Settings
```tsx
import DuckBotOSEnhanced from './components/DuckBotOSEnhanced';

function App() {
  return (
    <DuckBotOSEnhanced
      wallpaperUrl="https://example.com/wallpaper.jpg"
      enableElectronFeatures={true}
    />
  );
}
```

## App Definitions

Apps are defined in `apps.tsx` with the following structure:

```tsx
{
  id: 'app-id',
  title: 'App Title',
  icon: <AppIcon />,
  component: AppComponent,
  isPinned: true, // Show in shelf by default
  defaultSize: { width: 800, height: 600 },
  category: 'ai' | 'development' | 'productivity' | 'system',
  description: 'App description for launcher'
}
```

## Styling

The components use Tailwind CSS classes with custom CSS for specific animations:

```css
/* Fade-in-up animation for launcher */
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
```

## Browser Compatibility

- Modern browsers with CSS Grid and Flexbox support
- Web Speech API for voice features (optional)
- Three.js for 3D assistant (requires WebGL)

## Performance

- Efficient window management with React hooks
- Optimized re-rendering with proper key management
- Lazy loading of 3D models and heavy assets
- Cleanup of event listeners and Three.js resources

## Future Enhancements

- [ ] Window snapping and tiling
- [ ] Virtual desktops/workspaces
- [ ] App notifications system
- [ ] File drag-and-drop between windows
- [ ] Global keyboard shortcuts manager
- [ ] Theme customization
- [ ] Plugin system for third-party apps