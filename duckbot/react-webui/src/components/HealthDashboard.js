import React, { useState, useEffect, useCallback } from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Badge,
} from "@/components/ui/badge";
import {
  Alert,
  AlertDescription,
} from "@/components/ui/alert";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs";
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import {
  Activity,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Clock,
  TrendingUp,
  TrendingDown,
  Cpu,
  HardDrive,
  Wifi,
  Zap,
  Database,
  RefreshCw,
  Server,
  Brain,
  Settings,
  Target,
} from 'lucide-react';

const HealthDashboard = () => {
  const [systemStatus, setSystemStatus] = useState(null);
  const [serviceHealth, setServiceHealth] = useState({});
  const [systemMetrics, setSystemMetrics] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [analyticsData, setAnalyticsData] = useState({
    trends: {},
    predictions: {},
    recommendations: [],
    model_accuracy: {}
  });
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState(new Date());

  // Fetch system status
  const fetchSystemStatus = useCallback(async () => {
    try {
      const response = await fetch('http://localhost:8787/api/health/status');
      if (response.ok) {
        const data = await response.json();
        setSystemStatus(data);
      }
    } catch (error) {
      console.error('Error fetching system status:', error);
    }
  }, []);

  // Fetch service health
  const fetchServiceHealth = useCallback(async () => {
    try {
      const response = await fetch('http://localhost:8787/api/health/services');
      if (response.ok) {
        const data = await response.json();
        setServiceHealth(data);
      }
    } catch (error) {
      console.error('Error fetching service health:', error);
    }
  }, []);

  // Fetch system metrics
  const fetchSystemMetrics = useCallback(async () => {
    try {
      const response = await fetch('http://localhost:8787/api/health/metrics');
      if (response.ok) {
        const data = await response.json();
        setSystemMetrics(data.slice(-60)); // Last 60 data points
      }
    } catch (error) {
      console.error('Error fetching system metrics:', error);
    }
  }, []);

  // Fetch alerts
  const fetchAlerts = useCallback(async () => {
    try {
      const response = await fetch('http://localhost:8787/api/health/alerts');
      if (response.ok) {
        const data = await response.json();
        setAlerts(data.slice(-10)); // Last 10 alerts
      }
    } catch (error) {
      console.error('Error fetching alerts:', error);
    }
  }, []);

  // Fetch analytics data
  const fetchAnalyticsData = useCallback(async () => {
    try {
      const response = await fetch('http://localhost:8001/api/analytics/summary');
      if (response.ok) {
        const data = await response.json();
        setAnalyticsData(data);
      }
    } catch (error) {
      console.error('Error fetching analytics data:', error);
      // Fallback data
      setAnalyticsData({
        trends: {},
        predictions: {},
        recommendations: [],
        model_accuracy: {}
      });
    }
  }, []);

  // Initial data fetch
  useEffect(() => {
    const fetchData = async () => {
      await Promise.all([
        fetchSystemStatus(),
        fetchServiceHealth(),
        fetchSystemMetrics(),
        fetchAlerts(),
        fetchAnalyticsData()
      ]);
      setLoading(false);
    };

    fetchData();

    // Set up periodic refresh
    const interval = setInterval(() => {
      fetchData();
      setLastUpdate(new Date());
    }, 5000); // Refresh every 5 seconds

    return () => clearInterval(interval);
  }, [fetchSystemStatus, fetchServiceHealth, fetchSystemMetrics, fetchAlerts, fetchAnalyticsData]);

  // Manual refresh
  const refreshData = () => {
    setLoading(true);
    Promise.all([
      fetchSystemStatus(),
      fetchServiceHealth(),
      fetchSystemMetrics(),
      fetchAlerts(),
      fetchAnalyticsData()
    ]).then(() => {
      setLoading(false);
      setLastUpdate(new Date());
    });
  };

  // Status badge component
  const StatusBadge = ({ status }) => {
    const variants = {
      healthy: 'default',
      unhealthy: 'destructive',
      degraded: 'secondary',
      unknown: 'outline',
    };

    const icons = {
      healthy: <CheckCircle className="w-3 h-3" />,
      unhealthy: <XCircle className="w-3 h-3" />,
      degraded: <AlertTriangle className="w-3 h-3" />,
      unknown: <Clock className="w-3 h-3" />,
    };

    return (
      <Badge variant={variants[status]} className="flex items-center gap-1">
        {icons[status]}
        {status}
      </Badge>
    );
  };

  // Severity badge component
  const SeverityBadge = ({ severity }) => {
    const variants = {
      critical: 'destructive',
      warning: 'default',
      info: 'secondary',
    };

    const colors = {
      critical: 'bg-red-500',
      warning: 'bg-yellow-500',
      info: 'bg-blue-500',
    };

    return (
      <Badge variant={variants[severity]} className={`${colors[severity]} text-white`}>
        {severity}
      </Badge>
    );
  };

  // Format timestamp
  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString();
  };

  // Get status color for charts
  const getStatusColor = (status) => {
    const colors = {
      healthy: '#22c55e',
      unhealthy: '#ef4444',
      degraded: '#f59e0b',
      unknown: '#6b7280',
    };
    return colors[status] || '#6b7280';
  };

  // Calculate uptime percentage
  const calculateUptime = (history) => {
    if (!history || history.length === 0) return 0;
    const healthyCount = history.filter(h => h.status === 'healthy').length;
    return Math.round((healthyCount / history.length) * 100);
  };

  if (loading && !systemStatus) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-8 h-8 animate-spin" />
        <span className="ml-2">Loading health dashboard...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">System Health Dashboard</h1>
          <p className="text-muted-foreground">
            Real-time monitoring and performance metrics
          </p>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-sm text-muted-foreground">
            Last updated: {formatTime(lastUpdate)}
          </span>
          <button
            onClick={refreshData}
            className="flex items-center gap-2 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* System Overview Cards */}
      {systemStatus && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Services</CardTitle>
              <Server className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{systemStatus.total_services}</div>
              <p className="text-xs text-muted-foreground">
                {systemStatus.healthy_services} healthy, {systemStatus.unhealthy_services} unhealthy
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">System Status</CardTitle>
              <Activity className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <StatusBadge status={systemStatus.healthy_services === systemStatus.total_services ? 'healthy' : 'degraded'} />
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Active Alerts</CardTitle>
              <AlertTriangle className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {alerts.filter(a => !a.resolved).length}
              </div>
              <p className="text-xs text-muted-foreground">
                {alerts.filter(a => a.severity === 'critical').length} critical
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Monitoring</CardTitle>
              <Database className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <Badge variant={systemStatus.monitoring_active ? 'default' : 'secondary'}>
                {systemStatus.monitoring_active ? 'Active' : 'Inactive'}
              </Badge>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Main Content Tabs */}
      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="services">Services</TabsTrigger>
          <TabsTrigger value="metrics">Performance</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
          <TabsTrigger value="alerts">Alerts</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          {/* Service Health Overview */}
          <Card>
            <CardHeader>
              <CardTitle>Service Health Overview</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {Object.entries(serviceHealth).map(([serviceName, service]) => (
                  <Card key={serviceName} className="border-l-4" style={{ borderLeftColor: getStatusColor(service.status) }}>
                    <CardHeader className="pb-3">
                      <div className="flex items-center justify-between">
                        <CardTitle className="text-lg">{serviceName}</CardTitle>
                        <StatusBadge status={service.status} />
                      </div>
                    </CardHeader>
                    <CardContent className="pt-0">
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span>Response Time:</span>
                          <span>{service.response_time?.toFixed(2)}s</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Restarts:</span>
                          <span>{service.restart_count || 0}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Last Check:</span>
                          <span>{formatTime(service.last_check)}</span>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Recent Alerts */}
          <Card>
            <CardHeader>
              <CardTitle>Recent Alerts</CardTitle>
            </CardHeader>
            <CardContent>
              {alerts.length === 0 ? (
                <p className="text-muted-foreground text-center py-4">No recent alerts</p>
              ) : (
                <div className="space-y-3">
                  {alerts.slice(0, 5).map((alert) => (
                    <Alert key={alert.id} className={`${alert.resolved ? 'opacity-50' : ''}`}>
                      <AlertTriangle className="h-4 w-4" />
                      <AlertDescription>
                        <div className="flex items-center justify-between">
                          <div>
                            <div className="flex items-center gap-2 mb-1">
                              <SeverityBadge severity={alert.severity} />
                              <span className="font-medium">{alert.message}</span>
                            </div>
                            <div className="text-sm text-muted-foreground">
                              {alert.service_name && `Service: ${alert.service_name} • `}
                              {formatTime(alert.timestamp)}
                            </div>
                          </div>
                          {alert.resolved && (
                            <Badge variant="outline">Resolved</Badge>
                          )}
                        </div>
                      </AlertDescription>
                    </Alert>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="services" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Service Details</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Service</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Response Time</TableHead>
                    <TableHead>Restarts</TableHead>
                    <TableHead>Last Check</TableHead>
                    <TableHead>Uptime</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {Object.entries(serviceHealth).map(([serviceName, service]) => (
                    <TableRow key={serviceName}>
                      <TableCell className="font-medium">{serviceName}</TableCell>
                      <TableCell>
                        <StatusBadge status={service.status} />
                      </TableCell>
                      <TableCell>{service.response_time?.toFixed(3)}s</TableCell>
                      <TableCell>{service.restart_count || 0}</TableCell>
                      <TableCell>{formatTime(service.last_check)}</TableCell>
                      <TableCell>{calculateUptime(service.history || [])}%</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="metrics" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* CPU Usage Chart */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Cpu className="h-5 w-5" />
                  CPU Usage
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={200}>
                  <LineChart data={systemMetrics}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                      dataKey="timestamp"
                      tickFormatter={formatTime}
                      fontSize={12}
                    />
                    <YAxis fontSize={12} />
                    <Tooltip
                      labelFormatter={formatTime}
                      formatter={(value) => [`${value}%`, 'CPU Usage']}
                    />
                    <Line
                      type="monotone"
                      dataKey="cpu_percent"
                      stroke="#8884d8"
                      strokeWidth={2}
                      dot={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Memory Usage Chart */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Database className="h-5 w-5" />
                  Memory Usage
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={200}>
                  <AreaChart data={systemMetrics}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                      dataKey="timestamp"
                      tickFormatter={formatTime}
                      fontSize={12}
                    />
                    <YAxis fontSize={12} />
                    <Tooltip
                      labelFormatter={formatTime}
                      formatter={(value) => [`${value}%`, 'Memory Usage']}
                    />
                    <Area
                      type="monotone"
                      dataKey="memory_percent"
                      stroke="#82ca9d"
                      fill="#82ca9d"
                      fillOpacity={0.6}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Service Response Times */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Zap className="h-5 w-5" />
                  Service Response Times
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={200}>
                  <BarChart data={systemMetrics}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                      dataKey="timestamp"
                      tickFormatter={formatTime}
                      fontSize={12}
                    />
                    <YAxis fontSize={12} />
                    <Tooltip
                      labelFormatter={formatTime}
                      formatter={(value) => [`${value}s`, 'Response Time']}
                    />
                    <Bar dataKey="response_time" fill="#ffc658" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Service Status Distribution */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Wifi className="h-5 w-5" />
                  Service Status Distribution
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={200}>
                  <PieChart>
                    <Pie
                      data={Object.entries(serviceHealth).map(([name, service]) => ({
                        name,
                        value: 1,
                        status: service.status
                      }))}
                      cx="50%"
                      cy="50%"
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                      label={({ name, status }) => name}
                    >
                      {Object.entries(serviceHealth).map(([name, service], index) => (
                        <Cell key={`cell-${index}`} fill={getStatusColor(service.status)} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="analytics" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Trend Analysis */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <TrendingUp className="h-5 w-5" />
                  Performance Trends
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {Object.entries(analyticsData.trends || {}).map(([service, trends]) => (
                    <div key={service} className="border rounded-lg p-4">
                      <h4 className="font-semibold mb-2">{service}</h4>
                      <div className="space-y-2">
                        {Object.entries(trends).map(([metric, trend]) => (
                          <div key={metric} className="flex items-center justify-between">
                            <span className="text-sm text-muted-foreground">{metric}</span>
                            <div className="flex items-center gap-2">
                              <Badge
                                variant={trend.direction === 'increasing' ? 'destructive' :
                                       trend.direction === 'decreasing' ? 'default' : 'secondary'}
                                className="text-xs"
                              >
                                {trend.direction}
                              </Badge>
                              <span className="text-xs text-muted-foreground">
                                Strength: {(trend.strength * 100).toFixed(0)}%
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Predictions */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Brain className="h-5 w-5" />
                  Performance Predictions
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {Object.entries(analyticsData.predictions || {}).map(([service, predictions]) => (
                    <div key={service} className="border rounded-lg p-4">
                      <h4 className="font-semibold mb-2">{service}</h4>
                      <div className="space-y-2">
                        {Object.entries(predictions).map(([metric, prediction]) => (
                          <div key={metric} className="text-sm">
                            <div className="flex items-center justify-between mb-1">
                              <span className="font-medium">{metric}</span>
                              <Badge variant="outline" className="text-xs">
                                {(prediction.confidence * 100).toFixed(0)}% confidence
                              </Badge>
                            </div>
                            <div className="text-xs text-muted-foreground">
                              Next values: {prediction.values?.slice(0, 3).map(v => v.toFixed(2)).join(', ')}...
                            </div>
                            <div className="text-xs text-blue-600 mt-1">
                              {prediction.recommendation}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Optimization Recommendations */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Settings className="h-5 w-5" />
                Optimization Recommendations
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {analyticsData.recommendations?.length > 0 ? (
                  analyticsData.recommendations.map((rec, index) => (
                    <Alert key={index} className={rec.priority === 'critical' ? 'border-red-200' :
                                                      rec.priority === 'high' ? 'border-orange-200' :
                                                      'border-blue-200'}>
                      <AlertTriangle className="h-4 w-4" />
                      <AlertDescription>
                        <div className="space-y-2">
                          <div className="flex items-center justify-between">
                            <span className="font-semibold">{rec.service_name}</span>
                            <Badge variant={rec.priority === 'critical' ? 'destructive' :
                                          rec.priority === 'high' ? 'default' : 'secondary'}>
                              {rec.priority} priority
                            </Badge>
                          </div>
                          <p className="text-sm">{rec.description}</p>
                          <div className="space-y-1">
                            <p className="text-xs font-medium">Recommended actions:</p>
                            <ul className="text-xs space-y-1 ml-4">
                              {rec.actions?.map((action, actionIndex) => (
                                <li key={actionIndex} className="list-disc">• {action}</li>
                              ))}
                            </ul>
                          </div>
                        </div>
                      </AlertDescription>
                    </Alert>
                  ))
                ) : (
                  <p className="text-muted-foreground text-center py-4">
                    No optimization recommendations at this time
                  </p>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Model Accuracy */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Target className="h-5 w-5" />
                Prediction Model Accuracy
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {Object.entries(analyticsData.model_accuracy || {}).map(([service, accuracy]) => (
                  <div key={service} className="border rounded-lg p-4">
                    <h4 className="font-semibold mb-2">{service}</h4>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-muted-foreground">Accuracy</span>
                        <span className="font-medium">{(accuracy.accuracy * 100).toFixed(1)}%</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-muted-foreground">Mean Error</span>
                        <span className="font-medium">{accuracy.mean_error?.toFixed(2)}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-muted-foreground">Samples</span>
                        <span className="font-medium">{accuracy.sample_size || 0}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="alerts" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Alert History</CardTitle>
            </CardHeader>
            <CardContent>
              {alerts.length === 0 ? (
                <p className="text-muted-foreground text-center py-4">No alerts</p>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Time</TableHead>
                      <TableHead>Severity</TableHead>
                      <TableHead>Message</TableHead>
                      <TableHead>Service</TableHead>
                      <TableHead>Status</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {alerts.map((alert) => (
                      <TableRow key={alert.id}>
                        <TableCell>{formatTime(alert.timestamp)}</TableCell>
                        <TableCell>
                          <SeverityBadge severity={alert.severity} />
                        </TableCell>
                        <TableCell>{alert.message}</TableCell>
                        <TableCell>{alert.service_name || 'System'}</TableCell>
                        <TableCell>
                          {alert.resolved ? (
                            <Badge variant="outline">Resolved</Badge>
                          ) : (
                            <Badge variant="destructive">Active</Badge>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default HealthDashboard;