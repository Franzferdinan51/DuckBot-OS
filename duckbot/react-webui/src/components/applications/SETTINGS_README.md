# DuckBotOS Settings Application

## Overview

The enhanced Settings application for DuckBotOS provides comprehensive system configuration options with a modern, professional interface. It follows DuckBotOS design patterns and integrates seamlessly with the window system.

## Features

### 🎨 Appearance
- **Theme Settings**: Switch between Light and Dark themes
- **Accent Colors**: Choose from 8 different accent colors
- **Interface Options**: Toggle transparency effects, animations, and compact mode
- **Font Size**: Adjust text size from Small to Extra Large
- **Wallpaper**: Select desktop backgrounds

### 🖥️ Display
- **Resolution**: Configure screen resolution (up to 4K support)
- **Scaling**: Adjust display scaling from 100% to 200%
- **Refresh Rate**: Set monitor refresh rate (60Hz to 240Hz)
- **Multiple Monitors**: Support for multi-display setups
- **Night Light**: Blue light filter with intensity control

### 🔊 Sound
- **Volume Controls**: Master and notification volume sliders
- **Mute Options**: System-wide mute toggle
- **Audio Devices**: Configure input/output devices
- **System Sounds**: Toggle system sound effects

### ⚙️ System
- **Startup Options**: Auto-start and background services
- **Performance**: Hardware acceleration and system preferences
- **Updates**: Automatic update management
- **Advanced**: Developer mode and experimental features

### 🌐 Network
- **Connection Management**: Wi-Fi, Ethernet, and VPN controls
- **Proxy Settings**: HTTP/HTTPS proxy configuration
- **Network Status**: Real-time connection monitoring

### 👤 Accounts
- **User Profile**: Account information and avatar
- **Sync Settings**: Cloud synchronization options
- **Security**: Password and 2FA management
- **Data Export**: Account data backup and export

### 🔒 Privacy
- **Data Collection**: Analytics and error reporting controls
- **Permissions**: Camera, microphone, and location access
- **Privacy Controls**: Comprehensive privacy settings

### 🔔 Notifications
- **Alert Preferences**: Desktop and sound notifications
- **Do Not Disturb**: Focus mode toggle
- **Preview Options**: Notification preview settings

### 💾 Storage
- **Storage Management**: Disk usage monitoring
- **Cache Control**: Temporary file management
- **Auto-cleanup**: Automatic storage optimization
- **Backup**: Cloud and local backup options

### ℹ️ About
- **System Information**: Hardware and software details
- **Version Info**: Build and update information
- **Updates**: Check for system updates
- **Documentation**: System information and help

## Technical Implementation

### Architecture
- **Component Structure**: Modular React components
- **State Management**: Local state with localStorage persistence
- **Styling**: DuckBotOS design system with glass morphism effects
- **Responsive**: Adapts to different window sizes

### Integration
- **Window System**: Integrates with DuckBotOS window management
- **System Context**: Connects to system information and status
- **Settings Persistence**: Saves to localStorage for user preferences
- **Real-time Updates**: Live preview of changes

### Key Components
- **Settings Navigation**: Sidebar with category navigation
- **Section Content**: Dynamic content rendering per category
- **Form Controls**: Various input types and toggles
- **Action Buttons**: Save, reset, and cancel operations

## Usage

1. **Launch**: Click the Settings icon on the desktop
2. **Navigate**: Use the sidebar to switch between categories
3. **Configure**: Adjust settings using the provided controls
4. **Save**: Click "Save Changes" to apply settings
5. **Reset**: Use "Reset to Defaults" to restore original settings

## Dependencies

- React 18.2.0+
- Lucide React Icons
- Framer Motion (animations)
- React Hot Toast (notifications)

## File Structure

```
Settings.js                 # Main Settings component
SettingsModal.jsx          # Modal version for popups
SettingsContext.js         # Settings context provider
SettingsUtils.js           # Utility functions
```

## Customization

The Settings application can be extended by:

1. **Adding Sections**: Define new section objects in the sections array
2. **Custom Controls**: Create specialized form controls
3. **Theme Integration**: Add custom theme options
4. **System Integration**: Connect to additional system APIs

## Notes

- Settings are automatically saved to localStorage
- Changes take effect immediately after saving
- Some settings may require application restart
- System information updates in real-time
- Network and storage features require appropriate permissions