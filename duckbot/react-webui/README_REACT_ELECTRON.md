# DuckBot React + Electron Development Setup

## Overview

This document describes the enhanced React + Electron development setup for DuckBot, featuring automatic port allocation, fallback mechanisms, and robust startup sequences.

## Quick Start

### Method 1: Integrated Startup (Recommended)

```bash
# Start both React and Electron together
npm run start:all

# Or using the Node.js script directly
node start-react-electron.js

# Using the Windows batch file
START_REACT_ELECTRON.bat
```

### Method 2: Manual Startup

```bash
# Start React development server first
npm run start:react

# Then start Electron in another terminal
npm run start:electron
```

### Method 3: Development Mode

```bash
# Start React with dev tools and auto-reload
npm run dev

# Start Electron with React integration
npm run electron:dev
```

## Features

### 🔧 Smart Port Management
- **Automatic Port Detection**: Finds available ports starting from 3000
- **Port Fallback**: Automatically tries alternative ports if default is occupied
- **Environment Sync**: Updates `.env.development.local` with the selected port
- **Custom Port Support**: Use `--port 3001` to specify a custom port

### 🛡️ Robust Error Handling
- **Retry Logic**: Automatically retries failed connections (up to 10 times)
- **Graceful Fallbacks**: Falls back to built HTML if dev server fails
- **Process Monitoring**: Monitors both React and Electron processes
- **Clean Shutdown**: Properly terminates all processes on exit

### 🚀 Enhanced Development Experience
- **Hot Reload**: Full hot-reload support for React development
- **Dev Tools**: Automatic DevTools opening in Electron
- **Status Monitoring**: Real-time status updates and logging
- **Cross-Platform**: Works on Windows, macOS, and Linux

## Configuration

### Environment Variables

The `.env.development.local` file is automatically managed:

```env
DANGEROUSLY_DISABLE_HOST_CHECK=true
HOST=localhost
PORT=3000
HTTPS=false
BROWSER=none
```

### Custom Configuration

You can customize the startup behavior:

```javascript
// In start-react-electron.js
const launcher = new ReactElectronLauncher();

// Custom port
launcher.reactPort = 3001;

// Custom timeouts
launcher.startupTimeout = 60000; // 60 seconds
launcher.retryDelay = 3000; // 3 seconds between retries
```

## Command Line Options

```bash
node start-react-electron.js [options]

Options:
  --react-only          Start only React development server
  --electron-only       Start only Electron app (requires React server running)
  --port <number>       Specify port number (default: 3000)
  --help, -h           Show this help message

Examples:
  node start-react-electron.js           # Start both React and Electron
  node start-react-electron.js --react-only  # Start only React server
  node start-react-electron.js --port 3001     # Use custom port
```

## Troubleshooting

### Common Issues

#### 1. "Port already in use" error
**Solution**: The script automatically handles this by finding an available port. If you need a specific port, use `--port <number>`.

#### 2. "Failed to load React app" in Electron
**Solution**: The script includes multiple fallback mechanisms:
- Retries connection up to 10 times
- Falls back to built HTML file
- Shows a helpful error page with troubleshooting steps

#### 3. React server not starting
**Solution**: Check that Node.js is installed and dependencies are available:
```bash
node --version
npm install
```

#### 4. Electron app not starting
**Solution**: Ensure the React server is running first, or use the integrated startup script.

### Debug Mode

Enable detailed logging by setting the environment variable:
```bash
DEBUG=duckbot-react-electron node start-react-electron.js
```

## Architecture

### Component Overview

1. **ReactElectronLauncher** (`start-react-electron.js`)
   - Main orchestrator for React + Electron startup
   - Handles port allocation and process management
   - Provides command-line interface

2. **Enhanced Electron Main** (`electron-main.js`)
   - Dynamic port support via `REACT_PORT` environment variable
   - Retry logic for React server connection
   - Multiple fallback mechanisms

3. **Preload Script** (`preload.js`)
   - Secure bridge between Electron and React
   - Comprehensive API for system integration
   - Rate limiting and input validation

4. **React Application** (`src/`)
   - Full-featured React application with TypeScript support
   - Multiple interface modes (Classic/Desktop OS)
   - Integration with DuckBot backend services

### Startup Sequence

1. **Port Allocation**: Find available starting from port 3000
2. **Environment Setup**: Update `.env.development.local` with selected port
3. **React Server**: Start React development server with hot reload
4. **Health Check**: Wait for React server to respond
5. **Electron Launch**: Start Electron app with dynamic port configuration
6. **Monitoring**: Monitor both processes and handle errors

## Development Workflow

### 1. Development
```bash
# Start in development mode
npm run start:all

# Or with custom port
node start-react-electron.js --port 3001
```

### 2. Building
```bash
# Build React app for production
npm run build

# Build Electron app
npm run electron:build
```

### 3. Testing
```bash
# Run React tests
npm test

# Test individual components
npm run test:components
```

## Integration with DuckBot

### Backend Services

The React app integrates with various DuckBot backend services:

- **Enhanced WebUI**: System management dashboard
- **AI Services**: Multiple AI provider integration
- **WebSocket**: Real-time communication
- **File System**: File and directory operations
- **Process Management**: Service lifecycle management

### API Usage

```javascript
// Example of using the preload API in React
if (window.electronAPI) {
  // Start a service
  await window.electronAPI.startService('enhanced_webui');

  // Get system metrics
  const metrics = await window.electronAPI.getSystemMetrics();

  // Listen for updates
  window.electronAPI.onSystemStatusUpdated((status) => {
    console.log('System status:', status);
  });
}
```

## Performance Optimization

### Development Performance
- **Hot Reload**: Fast development iteration
- **Source Maps**: Full debugging support
- **Optimized Bundling**: Efficient build process
- **Memory Management**: Automatic cleanup

### Production Optimization
- **Code Splitting**: Optimized loading
- **Tree Shaking**: Unused code elimination
- **Asset Optimization**: Compressed and optimized assets
- **Caching**: Efficient caching strategies

## Security Considerations

### Preload Script Security
- **Input Validation**: All inputs are sanitized
- **Rate Limiting**: Prevents abuse of APIs
- **Service Whitelisting**: Only allowed services can be started
- **Context Isolation**: Secure separation between main and renderer processes

### Environment Security
- **No Hardcoded Secrets**: All secrets via environment variables
- **Secure File Operations**: Validated file paths and operations
- **Process Isolation**: Separate processes for different components

## Contributing

### Development Setup
1. Install dependencies: `npm install`
2. Start development server: `npm run start:all`
3. Make changes and test with hot reload
4. Run tests: `npm test`
5. Build for production: `npm run build`

### Code Style
- Use TypeScript for new components
- Follow ESLint configuration
- Include JSDoc comments for public APIs
- Test all new features

## License

This project is part of the DuckBot ecosystem and follows the same license terms.