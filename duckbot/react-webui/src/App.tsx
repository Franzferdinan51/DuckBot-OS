import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { ThemeProvider } from './theme/ThemeContext';
import Dashboard from './components/dashboard/Dashboard';
import ThemeSettings from './components/settings/ThemeSettings';
import './App.css';

// Electron-specific declarations
declare global {
  interface Window {
    require: (module: string) => any;
  }
}

const App: React.FC = () => {
  // Initialize electron APIs if available
  useEffect(() => {
    if (window.require) {
      const { ipcRenderer } = window.require('electron');

      // Listen for theme changes from system
      ipcRenderer.on('theme-change', (event: any, theme: string) => {
        console.log('Theme changed:', theme);
      });

      // Listen for system updates
      ipcRenderer.on('system-update', (event: any, data: any) => {
        console.log('System update:', data);
      });

      return () => {
        ipcRenderer.removeAllListeners('theme-change');
        ipcRenderer.removeAllListeners('system-update');
      };
    }
  }, []);

  return (
    <ThemeProvider>
      <Router>
        <div className="App">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/settings/theme" element={<ThemeSettings />} />
          </Routes>

          {/* Toast notifications */}
          <Toaster
            position="top-right"
            toastOptions={{
              duration: 4000,
              style: {
                background: 'var(--color-surface)',
                color: 'var(--color-text)',
                border: '1px solid var(--color-border)',
                borderRadius: '8px',
              },
              success: {
                iconTheme: {
                  primary: 'var(--color-success)',
                  secondary: 'var(--color-surface)',
                },
              },
              error: {
                iconTheme: {
                  primary: 'var(--color-error)',
                  secondary: 'var(--color-surface)',
                },
              },
            }}
          />
        </div>
      </Router>
    </ThemeProvider>
  );
};

export default App;