import React, { createContext, useContext, useState, useEffect } from 'react';
import { useAuth } from './AuthContext';
import toast from 'react-hot-toast';

const SystemContext = createContext();

export const useSystem = () => {
  const context = useContext(SystemContext);
  if (!context) {
    throw new Error('useSystem must be used within a SystemProvider');
  }
  return context;
};

export const SystemProvider = ({ children }) => {
  const { apiCall, isAuthenticated } = useAuth();
  const [systemStatus, setSystemStatus] = useState({
    status: 'unknown',
    services: [],
    uptime: 0,
    memory: { used: 0, total: 0 },
    cpu: 0,
    gpu: 0
  });
  const [isLoading, setIsLoading] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(null);
  const [networkStatus, setNetworkStatus] = useState('online');

  // Service management state
  const [services, setServices] = useState([
    {
      id: 'duckbot-webui',
      name: 'DuckBot WebUI',
      status: 'running',
      port: 8787,
      url: 'http://localhost:8787',
      description: 'Main DuckBot Web Interface',
      critical: true,
      category: 'core'
    },
    {
      id: 'duckbot-ai-router',
      name: 'AI Router',
      status: 'running',
      description: 'Intelligent AI model routing system',
      critical: true,
      category: 'ai'
    },
    {
      id: 'lm-studio',
      name: 'LM Studio',
      status: 'unknown',
      port: 1234,
      url: 'http://localhost:1234',
      description: 'Local AI model server',
      critical: false,
      category: 'ai'
    },
    {
      id: 'comfyui',
      name: 'ComfyUI',
      status: 'unknown',
      port: 8188,
      url: 'http://localhost:8188',
      description: 'Image generation system',
      critical: false,
      category: 'media'
    },
    {
      id: 'n8n',
      name: 'n8n Automation',
      status: 'unknown',
      port: 5678,
      url: 'http://localhost:5678',
      description: 'Workflow automation',
      critical: false,
      category: 'automation'
    },
    {
      id: 'jupyter',
      name: 'Jupyter Lab',
      status: 'unknown',
      port: 8889,
      url: 'http://localhost:8889',
      description: 'Data analysis notebooks',
      critical: false,
      category: 'dev'
    }
  ]);

  // Network connectivity monitoring
  useEffect(() => {
    const checkNetworkStatus = () => {
      setNetworkStatus(navigator.onLine ? 'online' : 'offline');
    };

    window.addEventListener('online', checkNetworkStatus);
    window.addEventListener('offline', checkNetworkStatus);

    return () => {
      window.removeEventListener('online', checkNetworkStatus);
      window.removeEventListener('offline', checkNetworkStatus);
    };
  }, []);

  // Fetch system status
  const fetchSystemStatus = async () => {
    if (!isAuthenticated) return;

    try {
      setIsLoading(true);
      const response = await apiCall('/api/status');
      
      if (response.ok) {
        const data = await response.json();
        setSystemStatus({
          status: data.status || 'running',
          services: data.services || [],
          uptime: data.uptime || 0,
          memory: data.memory || { used: 0, total: 0 },
          cpu: data.cpu_usage || 0,
          gpu: data.gpu_usage || 0
        });
        setLastUpdate(new Date());
      }
    } catch (error) {
      console.error('Failed to fetch system status:', error);
      toast.error('Failed to update system status');
    } finally {
      setIsLoading(false);
    }
  };

  // Fetch service statuses
  const fetchServiceStatuses = async () => {
    if (!isAuthenticated) return;

    try {
      // Check each service individually
      const servicePromises = services.map(async (service) => {
        if (service.url) {
          try {
            const response = await fetch(service.url, { 
              method: 'HEAD',
              timeout: 5000,
              mode: 'no-cors' // Handle CORS issues
            });
            return { ...service, status: 'running' };
          } catch (error) {
            return { ...service, status: 'stopped' };
          }
        }
        return service;
      });

      const updatedServices = await Promise.all(servicePromises);
      setServices(updatedServices);
    } catch (error) {
      console.error('Failed to check service statuses:', error);
    }
  };

  // Start service
  const startService = async (serviceId) => {
    try {
      const response = await apiCall(`/api/services/${serviceId}/start`, {
        method: 'POST'
      });

      if (response.ok) {
        toast.success(`Started ${serviceId}`);
        await fetchServiceStatuses();
        return true;
      } else {
        const error = await response.text();
        toast.error(`Failed to start ${serviceId}: ${error}`);
        return false;
      }
    } catch (error) {
      console.error(`Failed to start service ${serviceId}:`, error);
      toast.error(`Failed to start ${serviceId}`);
      return false;
    }
  };

  // Stop service
  const stopService = async (serviceId) => {
    try {
      const response = await apiCall(`/api/services/${serviceId}/stop`, {
        method: 'POST'
      });

      if (response.ok) {
        toast.success(`Stopped ${serviceId}`);
        await fetchServiceStatuses();
        return true;
      } else {
        const error = await response.text();
        toast.error(`Failed to stop ${serviceId}: ${error}`);
        return false;
      }
    } catch (error) {
      console.error(`Failed to stop service ${serviceId}:`, error);
      toast.error(`Failed to stop ${serviceId}`);
      return false;
    }
  };

  // Restart service
  const restartService = async (serviceId) => {
    try {
      const response = await apiCall(`/api/services/${serviceId}/restart`, {
        method: 'POST'
      });

      if (response.ok) {
        toast.success(`Restarted ${serviceId}`);
        await fetchServiceStatuses();
        return true;
      } else {
        const error = await response.text();
        toast.error(`Failed to restart ${serviceId}: ${error}`);
        return false;
      }
    } catch (error) {
      console.error(`Failed to restart service ${serviceId}:`, error);
      toast.error(`Failed to restart ${serviceId}`);
      return false;
    }
  };

  // Get system health
  const getSystemHealth = () => {
    const runningServices = services.filter(s => s.status === 'running').length;
    const totalServices = services.length;
    const criticalServices = services.filter(s => s.critical && s.status === 'running').length;
    const totalCriticalServices = services.filter(s => s.critical).length;

    let health = 'excellent';
    if (criticalServices < totalCriticalServices) {
      health = 'critical';
    } else if (runningServices < totalServices * 0.8) {
      health = 'poor';
    } else if (runningServices < totalServices * 0.9) {
      health = 'good';
    }

    return {
      overall: health,
      runningServices,
      totalServices,
      criticalServices,
      totalCriticalServices,
      percentage: Math.round((runningServices / totalServices) * 100)
    };
  };

  // Auto-refresh system status
  useEffect(() => {
    if (isAuthenticated) {
      fetchSystemStatus();
      fetchServiceStatuses();

      const interval = setInterval(() => {
        fetchSystemStatus();
        fetchServiceStatuses();
      }, 30000); // Update every 30 seconds

      return () => clearInterval(interval);
    }
  }, [isAuthenticated]);

  const value = {
    systemStatus,
    services,
    isLoading,
    lastUpdate,
    networkStatus,
    fetchSystemStatus,
    fetchServiceStatuses,
    startService,
    stopService,
    restartService,
    getSystemHealth
  };

  return (
    <SystemContext.Provider value={value}>
      {children}
    </SystemContext.Provider>
  );
};