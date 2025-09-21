# DuckBot Desktop UI - Development Guide

## Quick Start

### Prerequisites
- Node.js 18+ and npm
- Python 3.8+ (for DuckBot services)
- LM Studio (for local AI models)

### Setup
```bash
# Install dependencies
npm install

# Start development environment
npm run dev

# This will start:
# - Electron main process (TypeScript compilation)
# - React development server (Vite)
# - Hot reload for both processes
```

## Development Commands

### Development
```bash
npm run dev          # Start development environment
npm run build        # Build for production
npm run preview      # Preview production build
```

### Code Quality
```bash
npm run lint         # Run ESLint
npm run lint:fix     # Fix ESLint issues
npm run type-check   # Run TypeScript compiler
```

### Electron Packaging
```bash
npm run package      # Package for current platform
npm run make         # Create distribution packages
npm run publish      # Publish to GitHub Releases
```

## Architecture

### Main Process (`src/main/`)
- **main.ts**: Entry point with app lifecycle management
- **preload.ts**: Secure API exposure to renderer
- **services/**: DuckBot service integration
- **tray/**: System tray functionality
- **menu/**: Application menu configuration

### Renderer Process (`src/renderer/`)
- **components/**: React components
- **hooks/**: Custom React hooks
- **lib/**: Utility functions
- **stores/**: Zustand state management
- **types/**: TypeScript definitions

### Key Integration Points
- **IPC Communication**: Secure main/renderer communication
- **WebSocket Server**: Real-time service updates
- **Service Manager**: DuckBot service lifecycle
- **System Monitoring**: Hardware metrics collection

## Component Development

### Creating New Components
1. Create component in `src/renderer/components/`
2. Use TypeScript interfaces for props
3. Follow existing patterns and styling
4. Add to appropriate module exports

### Example Component Structure
```tsx
// src/renderer/components/MyComponent.tsx
import React from 'react'
import { cn } from '@/lib/utils'

interface MyComponentProps {
  title: string
  className?: string
}

export function MyComponent({ title, className }: MyComponentProps) {
  return (
    <div className={cn("base-styles", className)}>
      <h2>{title}</h2>
    </div>
  )
}
```

### State Management
Use Zustand for state management:

```tsx
// src/renderer/stores/useMyStore.ts
import { create } from 'zustand'

interface MyStoreState {
  count: number
  increment: () => void
}

export const useMyStore = create<MyStoreState>((set) => ({
  count: 0,
  increment: () => set((state) => ({ count: state.count + 1 }))
}))
```

### Custom Hooks
Create reusable hooks for complex logic:

```tsx
// src/renderer/hooks/useMyHook.ts
import { useState, useEffect } from 'react'

export function useMyHook() {
  const [data, setData] = useState(null)

  useEffect(() => {
    // Hook logic
  }, [])

  return { data }
}
```

## Service Integration

### Adding New Services
1. Update `DuckBotServiceManager.ts`
2. Add service to initialization list
3. Implement start/stop logic
4. Add WebSocket event handlers

### Example Service Addition
```typescript
// In DuckBotServiceManager
private initializeServices(): void {
  // Add new service
  this.services.set('my_service', {
    name: 'my_service',
    status: 'stopped',
    uptime: 0,
    port: 3000
  })
}

private getServiceCommand(serviceName: string) {
  const commands = {
    // Add new service command
    my_service: { command: 'python', args: ['my_script.py'] }
  }
  return commands[serviceName]
}
```

## WebSocket Integration

### Event Handling
The WebSocket server handles:
- Service status updates
- System metrics
- Agent coordination
- Automation results
- Cost tracking

### Client Communication
```tsx
// Using the useWebSocket hook
const { isConnected, startService, stopService } = useWebSocket()

// Start a service
startService('webui')

// Listen for events
socket.on('service-update', (service) => {
  // Handle service update
})
```

## Styling

### Tailwind CSS
- Use utility classes for styling
- Follow component composition patterns
- Maintain consistent spacing and colors

### Theme Support
- Built-in dark/light theme support
- System theme detection
- Persistent theme preferences

### Custom Components
Use Radix UI primitives with custom styling:

```tsx
import * as Switch from '@radix-ui/react-switch'

export function StyledSwitch({ checked, onCheckedChange }) {
  return (
    <Switch.Root checked={checked} onCheckedChange={onCheckedChange}>
      <Switch.Thumb />
    </Switch.Root>
  )
}
```

## Testing

### Unit Testing
```bash
# Install testing dependencies
npm install --save-dev jest @testing-library/react

# Run tests
npm test
```

### E2E Testing
```bash
# Install Playwright
npm install --save-dev @playwright/test

# Run E2E tests
npm run test:e2e
```

## Debugging

### Main Process Debugging
- Use Chrome DevTools with `main.ts`
- Add console.log statements
- Use VS Code debugger

### Renderer Process Debugging
- Browser DevTools (F12)
- React Developer Tools
- Redux DevTools (for state)

### Common Issues
- **Module not found**: Check imports and path aliases
- **TypeScript errors**: Ensure type definitions are correct
- **IPC errors**: Verify preload script and context isolation
- **WebSocket issues**: Check server status and connection

## Performance

### Optimization Tips
- Use React.memo for expensive components
- Implement virtual scrolling for large lists
- Debounce rapid user inputs
- Use useCallback and useMemo hooks
- Optimize chart rendering with canvas

### Memory Management
- Clean up event listeners in useEffect
- Use WeakMap/WeakSet for large datasets
- Implement pagination for data fetching
- Clear intervals and timeouts

## Deployment

### Build Process
```bash
# Production build
npm run build

# Package for distribution
npm run make

# Sign builds (macOS/Windows)
npm run sign
```

### Release Process
1. Update version in package.json
2. Create release notes
3. Run build and package commands
4. Upload to distribution platform
5. Test installation process

## Contributing

### Git Workflow
1. Create feature branch from main
2. Make changes with small, focused commits
3. Pull request for code review
4. Merge to main after approval

### Code Standards
- TypeScript strict mode
- ESLint configuration
- Prettier formatting
- Conventional commits

### Documentation
- Update component documentation
- Add JSDoc comments for public APIs
- Include examples in README files
- Update type definitions