# DuckBot Desktop UI

A professional desktop application for managing the DuckBot AI ecosystem, built with Electron, React, and TypeScript.

## Features

### 🎯 Core Functionality
- **Real-time Service Management**: Monitor and control all DuckBot services
- **AI Agent Coordination**: Manage specialized AI agents and their tasks
- **System Monitoring**: Track CPU, memory, disk, and network metrics
- **Cost Tracking**: Monitor API costs and usage across providers
- **Desktop Automation**: Execute automation commands and scripts
- **Conversation Management**: Chat with AI providers and manage conversations

### 🏗️ Architecture
- **Electron Main Process**: Service management and IPC communication
- **React Renderer**: Modern UI with TypeScript and Tailwind CSS
- **WebSocket Integration**: Real-time updates and bidirectional communication
- **State Management**: Zustand with persistence for global app state
- **Component Library**: Radix UI components with custom styling

### 🎨 UI/UX Features
- **Dark/Light Theme**: System-aware theme support
- **Responsive Design**: Works on various screen sizes
- **Real-time Updates**: Live metrics and status updates
- **Professional Dashboard**: Clean, modern interface
- **System Tray Integration**: Background operation support

## Technology Stack

### Frontend
- **Electron 28+**: Cross-platform desktop application framework
- **React 18**: UI library with modern hooks
- **TypeScript**: Type-safe development
- **Vite**: Fast build tool and development server
- **Tailwind CSS**: Utility-first CSS framework
- **Radix UI**: Headless UI components
- **Recharts**: Chart library for data visualization
- **Zustand**: Lightweight state management
- **Socket.io**: Real-time WebSocket communication

### Backend Integration
- **IPC Communication**: Secure main/renderer process communication
- **WebSocket Server**: Real-time service updates
- **Service Manager**: DuckBot service lifecycle management
- **System Monitoring**: Hardware metrics and performance tracking

## Project Structure

```
desktop-ui/
├── src/
│   ├── main/                 # Electron main process
│   │   ├── main.ts          # Main entry point
│   │   ├── preload.ts       # Preload script
│   │   ├── services/        # Service management
│   │   ├── tray/            # System tray
│   │   └── menu/            # Application menu
│   ├── renderer/            # React renderer process
│   │   ├── components/     # React components
│   │   ├── hooks/          # Custom React hooks
│   │   ├── lib/            # Utility functions
│   │   ├── stores/         # State management
│   │   ├── types/          # TypeScript definitions
│   │   └── App.tsx         # Main App component
│   └── assets/             # Static assets
├── dist/                   # Build output
├── package.json           # Dependencies and scripts
├── vite.config.ts         # Vite configuration
├── tailwind.config.js     # Tailwind CSS configuration
└── tsconfig.json          # TypeScript configuration
```

## Development

### Prerequisites
- Node.js 18+ and npm/yarn
- Python 3.8+ (for DuckBot services)
- LM Studio (for local AI models)

### Installation
```bash
# Clone the repository
git clone <repository-url>
cd desktop-ui

# Install dependencies
npm install

# Install DuckBot dependencies (in parent directory)
cd ..
npm install
```

### Development Commands
```bash
# Start development server with hot reload
npm run dev

# Build for production
npm run build

# Package the application
npm run make

# Lint code
npm run lint

# Type check
npm run type-check
```

### Configuration
The application reads configuration from:
- `config/ai_config.json` - AI provider settings
- `config/ecosystem_config.yaml` - Service configuration
- Electron store for UI preferences

## Key Components

### Service Management
- **DuckBotServiceManager**: Manages DuckBot service lifecycle
- **Service Grid**: Visual service status and controls
- **Real-time Updates**: WebSocket-based status updates

### Monitoring Dashboard
- **System Metrics**: CPU, memory, disk, network tracking
- **Performance Charts**: Historical data visualization
- **Alert System**: Threshold-based notifications

### AI Integration
- **Agent Management**: Coordinate specialized AI agents
- **Chat Interface**: Multi-provider chat functionality
- **Cost Tracking**: API usage and cost monitoring

### Automation
- **Command Execution**: Run automation scripts
- **Scheduling**: Scheduled task management
- **Results Tracking**: Execution history and logs

## Architecture Overview

### Main Process
The Electron main process handles:
- Service lifecycle management
- System monitoring and metrics
- WebSocket server for real-time updates
- IPC communication with renderer
- System tray and menu integration

### Renderer Process
The React renderer provides:
- Modern, responsive UI components
- Real-time data visualization
- State management with persistence
- WebSocket client integration
- User interactions and controls

### Communication Patterns
- **IPC**: Secure main/renderer communication
- **WebSocket**: Real-time bidirectional updates
- **State Store**: Centralized state management
- **Event System**: Decoupled component communication

## Production Deployment

### Building
```bash
# Build the application
npm run build

# Package for distribution
npm run make

# Create installers
npm run package
```

### Distribution
The build process creates platform-specific packages:
- Windows: `.exe` installer (Squirrel)
- macOS: `.dmg` disk image
- Linux: `.deb`, `.rpm`, `.AppImage`

### Updates
The application includes:
- Auto-update functionality
- Update checking and download
- User notification system
- Seamless installation process

## Contributing

1. Follow the existing code style and patterns
2. Use TypeScript for type safety
3. Write tests for new functionality
4. Update documentation as needed
5. Follow Git commit message conventions

## License

This project is licensed under the MIT License.