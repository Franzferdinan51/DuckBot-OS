import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Activity, CheckCircle, XCircle, RefreshCw, Server, Globe, Database } from 'lucide-react';

const ServiceStatus = () => {
  const [serviceConfig, setServiceConfig] = useState(null);
  const [mcpStatus, setMcpStatus] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Load service configuration
    const loadConfig = async () => {
      try {
        if (window.electronAPI) {
          const config = await window.electronAPI.getServiceConfig();
          setServiceConfig(config);
        }
      } catch (error) {
        console.error('Failed to load service config:', error);
      }
    };

    loadConfig();
  }, []);

  useEffect(() => {
    // Listen for service configuration updates
    const handleServiceConfig = (event, config) => {
      setServiceConfig(config);
      setLoading(false);
    };

    const handleMcpStatus = (event, status) => {
      setMcpStatus(status);
    };

    if (window.electronAPI) {
      window.electronAPI.onServiceConfig(handleServiceConfig);
      window.electronAPI.onMcpStatus(handleMcpStatus);
    }

    return () => {
      if (window.electronAPI) {
        window.electronAPI.removeListener('service-config', handleServiceConfig);
        window.electronAPI.removeListener('mcp-status', handleMcpStatus);
      }
    };
  }, []);

  const restartMCPServer = async () => {
    try {
      if (window.electronAPI) {
        const result = await window.electronAPI.restartMCPServer();
        if (result.success) {
          alert('MCP server restart initiated. The orchestrator will handle the restart automatically.');
        } else {
          alert('Failed to restart MCP server: ' + result.message);
        }
      }
    } catch (error) {
      console.error('Failed to restart MCP server:', error);
      alert('Failed to restart MCP server: ' + error.message);
    }
  };

  const getStatusBadge = (serviceName, status) => {
    if (!status) {
      return <Badge variant="secondary">Unknown</Badge>;
    }

    if (status.status === 'healthy') {
      return <Badge variant="default" className="bg-green-500">Healthy</Badge>;
    } else {
      return <Badge variant="destructive">Unhealthy</Badge>;
    }
  };

  const getServiceIcon = (serviceName) => {
    switch (serviceName) {
      case 'mcp_server':
        return <Server className="h-5 w-5" />;
      case 'react_server':
        return <Globe className="h-5 w-5" />;
      case 'webui_backend':
        return <Database className="h-5 w-5" />;
      default:
        return <Activity className="h-5 w-5" />;
    }
  };

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            Service Status
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center p-8">
            <RefreshCw className="h-8 w-8 animate-spin" />
            <span className="ml-2">Loading service status...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            Service Status
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {serviceConfig?.services && Object.entries(serviceConfig.services).map(([serviceName, config]) => (
              <div key={serviceName} className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex items-center gap-3">
                  {getServiceIcon(serviceName)}
                  <div>
                    <h3 className="font-semibold">{serviceName.replace('_', ' ').toUpperCase()}</h3>
                    <p className="text-sm text-muted-foreground">
                      Port: {config.port} | URL: {config.url}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {serviceName === 'mcp_server' && getStatusBadge(serviceName, mcpStatus)}
                  {serviceName === 'react_server' && <Badge variant="default">Running</Badge>}
                  {serviceName === 'webui_backend' && <Badge variant="default">Running</Badge>}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {serviceConfig?.services?.mcp_server && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Server className="h-5 w-5" />
              MCP Server Management
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-semibold">MCP Server Status</h3>
                  <p className="text-sm text-muted-foreground">
                    {mcpStatus?.status === 'healthy'
                      ? 'Server is running and responding to health checks'
                      : 'Server is not responding to health checks'
                    }
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  {getStatusBadge('mcp_server', mcpStatus)}
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={restartMCPServer}
                    disabled={loading}
                  >
                    <RefreshCw className="h-4 w-4 mr-2" />
                    Restart
                  </Button>
                </div>
              </div>

              {mcpStatus?.error && (
                <div className="p-3 bg-destructive/10 border border-destructive rounded-md">
                  <p className="text-sm font-medium text-destructive">Error Details:</p>
                  <p className="text-sm text-muted-foreground">{mcpStatus.error}</p>
                </div>
              )}

              <div className="text-xs text-muted-foreground">
                <p>MCP Server URL: {serviceConfig.services.mcp_server.url}</p>
                <p>Health Endpoint: {serviceConfig.services.mcp_server.url}/health</p>
                <p>Last Updated: {new Date().toLocaleString()}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default ServiceStatus;