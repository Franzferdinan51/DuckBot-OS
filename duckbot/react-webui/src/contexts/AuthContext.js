import React, { createContext, useContext, useState, useEffect } from 'react';
import toast from 'react-hot-toast';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);

  // Get DuckBot WebUI token from URL or localStorage
  useEffect(() => {
    const initAuth = async () => {
      try {
        // Check URL for token parameter
        const urlParams = new URLSearchParams(window.location.search);
        const urlToken = urlParams.get('token');
        
        // Check localStorage for stored token
        const storedToken = localStorage.getItem('duckbot_token');
        
        const authToken = urlToken || storedToken;
        
        if (authToken) {
          // Validate token with DuckBot WebUI
          const isValid = await validateToken(authToken);
          if (isValid) {
            setToken(authToken);
            setIsAuthenticated(true);
            setUser({
              name: 'DuckBot User',
              role: 'Administrator',
              permissions: ['all']
            });
            
            // Store token in localStorage
            localStorage.setItem('duckbot_token', authToken);
            
            // Clean URL if token was in URL
            if (urlToken) {
              const newUrl = window.location.pathname;
              window.history.replaceState({}, document.title, newUrl);
            }
            
            toast.success('Successfully authenticated with DuckBot WebUI');
          } else {
            // Invalid token
            localStorage.removeItem('duckbot_token');
            toast.error('Invalid authentication token');
          }
        }
      } catch (error) {
        console.error('Authentication initialization failed:', error);
        toast.error('Authentication initialization failed');
      } finally {
        setIsLoading(false);
      }
    };

    initAuth();
  }, []);

  const validateToken = async (token) => {
    try {
      // Attempt to fetch system status to validate token
      const response = await fetch('/api/status', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      return response.ok;
    } catch (error) {
      console.error('Token validation failed:', error);
      return false;
    }
  };

  const login = async (authToken) => {
    try {
      setIsLoading(true);
      
      const isValid = await validateToken(authToken);
      if (isValid) {
        setToken(authToken);
        setIsAuthenticated(true);
        setUser({
          name: 'DuckBot User',
          role: 'Administrator',
          permissions: ['all']
        });
        
        localStorage.setItem('duckbot_token', authToken);
        toast.success('Login successful');
        return true;
      } else {
        toast.error('Invalid authentication token');
        return false;
      }
    } catch (error) {
      console.error('Login failed:', error);
      toast.error('Login failed');
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    setIsAuthenticated(false);
    setToken(null);
    setUser(null);
    localStorage.removeItem('duckbot_token');
    toast.success('Logged out successfully');
  };

  // API call helper with authentication
  const apiCall = async (endpoint, options = {}) => {
    const defaultOptions = {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
        ...options.headers
      }
    };

    try {
      const response = await fetch(endpoint, { ...options, headers: defaultOptions.headers });
      
      if (response.status === 401) {
        // Token expired or invalid
        logout();
        throw new Error('Authentication expired');
      }
      
      return response;
    } catch (error) {
      if (error.message === 'Authentication expired') {
        throw error;
      }
      
      // Network or other error
      console.error('API call failed:', error);
      throw error;
    }
  };

  const value = {
    isAuthenticated,
    isLoading,
    user,
    token,
    login,
    logout,
    apiCall
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};