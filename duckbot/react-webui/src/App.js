import React, { useState, useEffect, useRef } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import './App.css';

// Import components
import Desktop from './components/Desktop';
import LoginScreen from './components/LoginScreen';
import LoadingScreen from './components/LoadingScreen';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { SystemProvider } from './contexts/SystemContext';
import { AIProvider } from './contexts/AIContext';

const AppContent = () => {
  const { isAuthenticated, isLoading } = useAuth();
  const [systemReady, setSystemReady] = useState(false);

  useEffect(() => {
    if (isAuthenticated && !isLoading) {
      // Initialize system after authentication
      const timer = setTimeout(() => {
        setSystemReady(true);
      }, 2000);
      return () => clearTimeout(timer);
    }
  }, [isAuthenticated, isLoading]);

  if (isLoading) {
    return <LoadingScreen message="Initializing DuckBot AI OS..." />;
  }

  if (!isAuthenticated) {
    return <LoginScreen />;
  }

  if (!systemReady) {
    return <LoadingScreen message="Loading AI OS Desktop Environment..." />;
  }

  return (
    <Routes>
      <Route path="/" element={<Desktop />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
};

const App = () => {
  return (
    <Router>
      <AuthProvider>
        <SystemProvider>
          <AIProvider>
            <div className="App">
              <AppContent />
              <Toaster 
                position="top-right"
                toastOptions={{
                  duration: 4000,
                  style: {
                    background: '#1e293b',
                    color: '#fff',
                    border: '1px solid #334155'
                  },
                  success: {
                    iconTheme: {
                      primary: '#10b981',
                      secondary: '#fff'
                    }
                  },
                  error: {
                    iconTheme: {
                      primary: '#ef4444',
                      secondary: '#fff'
                    }
                  }
                }}
              />
            </div>
          </AIProvider>
        </SystemProvider>
      </AuthProvider>
    </Router>
  );
};

export default App;