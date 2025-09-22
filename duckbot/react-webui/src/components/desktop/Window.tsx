import React, { useState, useRef, useEffect, useCallback } from 'react';
import { WindowProps } from './types';
import { Minimize2, Maximize2, X, RotateCcw } from 'lucide-react';

type ResizeDirection = 'n' | 'ne' | 'e' | 'se' | 's' | 'sw' | 'w' | 'nw';

const Window: React.FC<WindowProps> = ({
  instance,
  isActive,
  children,
  onClose,
  onFocus,
  onUpdate,
  onMinimize,
  onMaximize,
}) => {
  const { x, y, width, height, zIndex, title, isMinimized, isMaximized } = instance;
  const [isDragging, setIsDragging] = useState(false);
  const [isResizing, setIsResizing] = useState(false);
  const [resizeDirection, setResizeDirection] = useState<ResizeDirection | null>(null);
  const [hoverDirection, setHoverDirection] = useState<ResizeDirection | null>(null);
  const [isAnimating, setIsAnimating] = useState(false);
  const dragOffset = useRef({ x: 0, y: 0 });
  const resizeStart = useRef({ x: 0, y: 0, width: 0, height: 0 });
  const windowRef = useRef<HTMLDivElement>(null);
  const animationFrameRef = useRef<number | null>(null);

  // Handle window dragging
  const handleMouseDown = (e: React.MouseEvent<HTMLDivElement>) => {
    if ((e.target as HTMLElement).closest('.window-control')) return;
    onFocus();
    if (isMaximized) return;

    setIsDragging(true);
    dragOffset.current = {
      x: e.clientX - x,
      y: e.clientY - y,
    };
  };

  // Handle window resizing
  const handleResizeMouseDown = (direction: ResizeDirection, e: React.MouseEvent) => {
    e.stopPropagation();
    if (isMaximized) return;

    setIsResizing(true);
    setResizeDirection(direction);
    resizeStart.current = {
      x: e.clientX,
      y: e.clientY,
      width: width,
      height: height,
    };
    onFocus();
  };

  // Mouse move handler for dragging and resizing with performance optimization
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (animationFrameRef.current) return; // Skip if already queued

      animationFrameRef.current = requestAnimationFrame(() => {
        if (isDragging) {
          onUpdate({
            x: Math.max(0, Math.min(window.innerWidth - width, e.clientX - dragOffset.current.x)),
            y: Math.max(0, Math.min(window.innerHeight - height, e.clientY - dragOffset.current.y)),
          });
        } else if (isResizing && resizeDirection) {
          const deltaX = e.clientX - resizeStart.current.x;
          const deltaY = e.clientY - resizeStart.current.y;

          const { newWidth, newHeight, newX, newY } = calculateResizeDimensions(
            resizeDirection,
            deltaX,
            deltaY,
            resizeStart.current.width,
            resizeStart.current.height,
            x,
            y
          );

          onUpdate({ x: newX, y: newY, width: newWidth, height: newHeight });
        }
        animationFrameRef.current = null;
      });
    };

    const handleMouseUp = () => {
      setIsDragging(false);
      setIsResizing(false);
      setResizeDirection(null);
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
        animationFrameRef.current = null;
      }
    };

    if (isDragging || isResizing) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [isDragging, isResizing, resizeDirection, onUpdate, calculateResizeDimensions, x, y, width, height]);

  // Cursor detection for resize handles
  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (isMaximized || isDragging || isResizing) return;

    const rect = windowRef.current?.getBoundingClientRect();
    if (!rect) return;

    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const edgeThreshold = 6;

    let direction: ResizeDirection | null = null;

    // Corner detection (highest priority)
    if (x <= edgeThreshold && y <= edgeThreshold) {
      direction = 'nw';
    } else if (x >= rect.width - edgeThreshold && y <= edgeThreshold) {
      direction = 'ne';
    } else if (x <= edgeThreshold && y >= rect.height - edgeThreshold) {
      direction = 'sw';
    } else if (x >= rect.width - edgeThreshold && y >= rect.height - edgeThreshold) {
      direction = 'se';
    }
    // Edge detection
    else if (x <= edgeThreshold) {
      direction = 'w';
    } else if (x >= rect.width - edgeThreshold) {
      direction = 'e';
    } else if (y <= edgeThreshold) {
      direction = 'n';
    } else if (y >= rect.height - edgeThreshold) {
      direction = 's';
    }

    setHoverDirection(direction);
  }, [isMaximized, isDragging, isResizing]);

  // Handle mouse leave to clear hover state
  const handleMouseLeave = useCallback(() => {
    setHoverDirection(null);
  }, []);

  // Resize helper function with better constraints
  const calculateResizeDimensions = useCallback((
    direction: ResizeDirection,
    deltaX: number,
    deltaY: number,
    startWidth: number,
    startHeight: number,
    startX: number,
    startY: number
  ) => {
    const minWidth = 300;
    const minHeight = 200;
    const maxWidth = window.innerWidth - 50;
    const maxHeight = window.innerHeight - 100;

    let newWidth = startWidth;
    let newHeight = startHeight;
    let newX = startX;
    let newY = startY;

    switch (direction) {
      case 'n':
        newHeight = Math.max(minHeight, Math.min(maxHeight, startHeight - deltaY));
        newY = Math.max(0, Math.min(startY + startHeight - minHeight, startY + deltaY));
        break;
      case 's':
        newHeight = Math.max(minHeight, Math.min(maxHeight, startHeight + deltaY));
        break;
      case 'e':
        newWidth = Math.max(minWidth, Math.min(maxWidth, startWidth + deltaX));
        break;
      case 'w':
        newWidth = Math.max(minWidth, Math.min(maxWidth, startWidth - deltaX));
        newX = Math.max(0, Math.min(startX + startWidth - minWidth, startX + deltaX));
        break;
      case 'ne':
        newWidth = Math.max(minWidth, Math.min(maxWidth, startWidth + deltaX));
        newHeight = Math.max(minHeight, Math.min(maxHeight, startHeight - deltaY));
        newY = Math.max(0, Math.min(startY + startHeight - minHeight, startY + deltaY));
        break;
      case 'se':
        newWidth = Math.max(minWidth, Math.min(maxWidth, startWidth + deltaX));
        newHeight = Math.max(minHeight, Math.min(maxHeight, startHeight + deltaY));
        break;
      case 'sw':
        newWidth = Math.max(minWidth, Math.min(maxWidth, startWidth - deltaX));
        newHeight = Math.max(minHeight, Math.min(maxHeight, startHeight + deltaY));
        newX = Math.max(0, Math.min(startX + startWidth - minWidth, startX + deltaX));
        break;
      case 'nw':
        newWidth = Math.max(minWidth, Math.min(maxWidth, startWidth - deltaX));
        newHeight = Math.max(minHeight, Math.min(maxHeight, startHeight - deltaY));
        newX = Math.max(0, Math.min(startX + startWidth - minWidth, startX + deltaX));
        newY = Math.max(0, Math.min(startY + startHeight - minHeight, startY + deltaY));
        break;
    }

    return { newWidth, newHeight, newX, newY };
  }, []);

  // Get cursor style based on current state
  const getCursorStyle = () => {
    if (isDragging) return 'cursor-move';
    if (isResizing && resizeDirection) {
      return `cursor-${resizeDirection}-resize`;
    }
    if (hoverDirection) {
      return `cursor-${hoverDirection}-resize`;
    }
    return '';
  };

  // Window classes for styling and animations
  const windowClasses = [
    'absolute bg-gray-800 dark:bg-gray-900 rounded-lg shadow-2xl flex flex-col border',
    'transition-all duration-300 ease-out transform-gpu',
    'select-none',
    isActive ? 'border-blue-500/50 shadow-blue-500/30 ring-1 ring-blue-500/20' : 'border-gray-700/50 shadow-black/50',
    isMinimized ? 'opacity-0 scale-90 -translate-y-full pointer-events-none' : 'opacity-100 scale-100',
    isDragging ? 'cursor-move shadow-blue-500/20' : '',
    getCursorStyle(),
    isMaximized ? 'rounded-none' : '',
  ].filter(Boolean).join(' ');

  // Window styles
  const maximizedStyles = { top: 0, left: 0, width: '100%', height: 'calc(100% - 3.5rem)' };
  const normalStyles = { top: `${y}px`, left: `${x}px`, width: `${width}px`, height: `${height}px` };

  return (
    <div
      ref={windowRef}
      className={windowClasses}
      style={{
        ...(isMaximized ? maximizedStyles : normalStyles),
        zIndex,
      }}
      onMouseDown={onFocus}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
    >
      {/* Title Bar */}
      <div
        className={`h-8 px-3 flex items-center justify-between rounded-t-lg select-none cursor-move ${
          isActive ? 'bg-gray-700/90' : 'bg-gray-700/70'
        } backdrop-blur-sm`}
        onMouseDown={handleMouseDown}
        onDoubleClick={onMaximize}
      >
        <div className="flex items-center space-x-2">
          <div className={`w-3 h-3 rounded-full ${isActive ? 'bg-green-400' : 'bg-gray-500'}`} />
          <span className="text-sm font-medium text-gray-200 truncate">{title}</span>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={onMinimize}
            className="window-control w-3 h-3 rounded-full bg-yellow-500 hover:bg-yellow-600 transition-colors"
            title="Minimize"
          >
            <Minimize2 className="w-2 h-2 text-white opacity-0 group-hover:opacity-100" />
          </button>
          <button
            onClick={onMaximize}
            className="window-control w-3 h-3 rounded-full bg-green-500 hover:bg-green-600 transition-colors"
            title={isMaximized ? "Restore" : "Maximize"}
          >
            <Maximize2 className="w-2 h-2 text-white opacity-0 group-hover:opacity-100" />
          </button>
          <button
            onClick={onClose}
            className="window-control w-3 h-3 rounded-full bg-red-500 hover:bg-red-600 transition-colors"
            title="Close"
          >
            <X className="w-2 h-2 text-white opacity-0 group-hover:opacity-100" />
          </button>
        </div>
      </div>

      {/* Window Content */}
      <div className="flex-grow overflow-auto bg-gray-900 rounded-b-lg">
        {children}
      </div>

      {/* Enhanced Resize Handles */}
      {!isMaximized && !isMinimized && (
        <>
          {/* Corner resize handles */}
          <div
            className="absolute top-0 left-0 w-4 h-4 z-10 group"
            onMouseDown={(e) => handleResizeMouseDown('nw', e)}
          >
            <div className="absolute inset-0 rounded-tl-lg transition-all duration-200 ease-out
              bg-transparent hover:bg-blue-500/40 active:bg-blue-500/60
              border-t-2 border-l-2 border-transparent hover:border-blue-400/60" />
          </div>
          <div
            className="absolute top-0 right-0 w-4 h-4 z-10 group"
            onMouseDown={(e) => handleResizeMouseDown('ne', e)}
          >
            <div className="absolute inset-0 rounded-tr-lg transition-all duration-200 ease-out
              bg-transparent hover:bg-blue-500/40 active:bg-blue-500/60
              border-t-2 border-r-2 border-transparent hover:border-blue-400/60" />
          </div>
          <div
            className="absolute bottom-0 left-0 w-4 h-4 z-10 group"
            onMouseDown={(e) => handleResizeMouseDown('sw', e)}
          >
            <div className="absolute inset-0 rounded-bl-lg transition-all duration-200 ease-out
              bg-transparent hover:bg-blue-500/40 active:bg-blue-500/60
              border-b-2 border-l-2 border-transparent hover:border-blue-400/60" />
          </div>
          <div
            className="absolute bottom-0 right-0 w-4 h-4 z-10 group"
            onMouseDown={(e) => handleResizeMouseDown('se', e)}
          >
            <div className="absolute inset-0 rounded-br-lg transition-all duration-200 ease-out
              bg-transparent hover:bg-blue-500/40 active:bg-blue-500/60
              border-b-2 border-r-2 border-transparent hover:border-blue-400/60" />
          </div>

          {/* Edge resize handles */}
          <div
            className="absolute top-0 left-4 right-4 h-2 z-10 group"
            onMouseDown={(e) => handleResizeMouseDown('n', e)}
          >
            <div className="absolute inset-0 transition-all duration-200 ease-out
              bg-transparent hover:bg-blue-500/30 active:bg-blue-500/50
              border-t-2 border-transparent hover:border-blue-400/50" />
          </div>
          <div
            className="absolute bottom-0 left-4 right-4 h-2 z-10 group"
            onMouseDown={(e) => handleResizeMouseDown('s', e)}
          >
            <div className="absolute inset-0 transition-all duration-200 ease-out
              bg-transparent hover:bg-blue-500/30 active:bg-blue-500/50
              border-b-2 border-transparent hover:border-blue-400/50" />
          </div>
          <div
            className="absolute left-0 top-4 bottom-4 w-2 z-10 group"
            onMouseDown={(e) => handleResizeMouseDown('w', e)}
          >
            <div className="absolute inset-0 transition-all duration-200 ease-out
              bg-transparent hover:bg-blue-500/30 active:bg-blue-500/50
              border-l-2 border-transparent hover:border-blue-400/50" />
          </div>
          <div
            className="absolute right-0 top-4 bottom-4 w-2 z-10 group"
            onMouseDown={(e) => handleResizeMouseDown('e', e)}
          >
            <div className="absolute inset-0 transition-all duration-200 ease-out
              bg-transparent hover:bg-blue-500/30 active:bg-blue-500/50
              border-r-2 border-transparent hover:border-blue-400/50" />
          </div>

          {/* Resize indicator overlay */}
          {isResizing && (
            <div className="absolute inset-0 bg-blue-500/10 pointer-events-none z-20 transition-opacity duration-150" />
          )}
        </>
      )}
    </div>
  );
};

export default Window;

// Custom CSS for smooth cursor transitions
const customStyles = `
  /* Custom cursor classes for smooth transitions */
  .cursor-n-resize { cursor: n-resize !important; }
  .cursor-ne-resize { cursor: ne-resize !important; }
  .cursor-e-resize { cursor: e-resize !important; }
  .cursor-se-resize { cursor: se-resize !important; }
  .cursor-s-resize { cursor: s-resize !important; }
  .cursor-sw-resize { cursor: sw-resize !important; }
  .cursor-w-resize { cursor: w-resize !important; }
  .cursor-nw-resize { cursor: nw-resize !important; }
  .cursor-move { cursor: move !important; }

  /* Smooth cursor transitions */
  .window-resize-handle {
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  }

  /* Resize handle hover effects */
  .resize-handle-hover {
    background: linear-gradient(45deg, rgba(59, 130, 246, 0.3), rgba(59, 130, 246, 0.1));
    backdrop-filter: blur(2px);
  }

  /* Active resize state */
  .resize-active {
    background: linear-gradient(45deg, rgba(59, 130, 246, 0.5), rgba(59, 130, 246, 0.2));
    backdrop-filter: blur(4px);
  }
`;

// Add styles to document head
if (typeof document !== 'undefined' && !document.getElementById('window-resize-styles')) {
  const styleElement = document.createElement('style');
  styleElement.id = 'window-resize-styles';
  styleElement.textContent = customStyles;
  document.head.appendChild(styleElement);
}