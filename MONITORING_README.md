# DuckBot Monitoring System

A comprehensive real-time monitoring and analytics system for DuckBot v4.2, providing deep insights into system performance, AI agent behavior, service health, and user activity.

## 🌟 Features

### Real-time System Monitoring
- **System Metrics**: CPU, memory, disk, network usage tracking
- **Process Monitoring**: Active process count and resource utilization
- **Hardware Detection**: GPU, CPU, memory, and storage monitoring
- **Performance Trends**: Historical data analysis and trend detection

### AI Agent Performance Monitoring
- **Response Time Tracking**: Individual and aggregate agent performance
- **Success Rate Analysis**: Failure patterns and error analysis
- **Model Usage Metrics**: Token usage and model switching efficiency
- **Load Balancing Insights**: Agent distribution and resource allocation

### Service Health Monitoring
- **Service Availability**: Real-time service status and response times
- **Dependency Tracking**: Service relationships and health impact
- **Auto-recovery**: Automated service restart and health recovery
- **Performance Metrics**: Service-specific performance indicators

### User Activity Analytics
- **Session Tracking**: User sessions and interaction patterns
- **Feature Usage**: Most-used features and functionality
- **Response Satisfaction**: User satisfaction scoring and feedback
- **Geographic Distribution**: User location and access patterns (when available)

### Alert and Notification System
- **Multi-level Alerts**: Info, Warning, Error, and Critical alert levels
- **Customizable Rules**: Flexible alert condition configuration
- **Multiple Channels**: Console, log, email, and webhook notifications
- **Alert Aggregation**: Intelligent alert deduplication and grouping

### Data Export and Reporting
- **Multiple Formats**: CSV, JSON, Excel, HTML, and PDF exports
- **Scheduled Reports**: Automated report generation and delivery
- **Custom Analytics**: Advanced data analysis and insights
- **Historical Analysis**: Trend analysis and predictive maintenance

### Web Dashboard
- **Real-time Updates**: Live metrics and status updates
- **Interactive Charts**: Dynamic data visualization
- **Service Control**: Start, stop, and restart services from dashboard
- **Mobile Responsive**: Works on all device sizes

## 🚀 Quick Start

### Prerequisites
- Python 3.8+ (3.11+ recommended)
- SQLite3 (included with Python)
- psutil library for system metrics
- FastAPI for web dashboard

### Installation
```bash
# Install dependencies
pip install psutil fastapi uvicorn jinja2 pandas numpy openpyxl

# Or install from requirements.txt
pip install -r requirements.txt
```

### Basic Usage
```bash
# Start monitoring system with dashboard
python start_monitoring_system.py

# CLI mode only
python start_monitoring_system.py --cli

# Custom configuration
python start_monitoring_system.py --host 0.0.0.0 --port 8800 --metrics 2
```

### Web Dashboard Access
Open your browser and navigate to:
```
http://localhost:8790
```

## 📊 Dashboard Features

### System Overview
- **Real-time Metrics**: Live CPU, memory, disk usage
- **Service Status**: All services with health indicators
- **Active Alerts**: Current alert count and severity
- **Performance Charts**: Historical performance trends

### Service Management
- **Service Control**: Start, stop, restart services
- **Health Monitoring**: Real-time service status
- **Response Time**: Service latency tracking
- **Dependency View**: Service relationships

### Agent Performance
- **Agent Metrics**: Response times and success rates
- **Model Usage**: Token consumption and model switching
- **Error Analysis**: Failure patterns and troubleshooting
- **Resource Usage**: Agent resource utilization

### User Analytics
- **Activity Timeline**: User interaction patterns
- **Feature Popularity**: Most-used features
- **Satisfaction Metrics**: User feedback scoring
- **Session Analysis**: User session behavior

## 🔧 Configuration

### Environment Variables
```bash
# Monitoring Configuration
DUCKBOT_MONITOR_HOST=127.0.0.1
DUCKBOT_MONITOR_PORT=8790
DUCKBOT_METRICS_INTERVAL=5
DUCKBOT_HEALTH_INTERVAL=30

# Database Configuration
DUCKBOT_MONITORING_DB=monitoring.db
DUCKBOT_EXPORT_DIR=exports
DUCKBOT_REPORT_DIR=reports

# Alert Configuration
DUCKBOT_ALERT_EMAIL=admin@example.com
DUCKBOT_ALERT_WEBHOOK=https://hooks.slack.com/...
DUCKBOT_ALERT_LEVEL_THRESHOLD=warning
```

### Alert Rules
Customize alert thresholds and conditions:

```python
# Example custom alert rules
alert_rules = [
    {
        "name": "high_memory_usage",
        "condition": lambda metrics: metrics.get("memory_percent", 0) > 85,
        "level": AlertLevel.WARNING,
        "message": "High memory usage: {memory_percent}%",
        "source": "system_metrics"
    }
]
```

### Service Monitoring
Configure services to monitor:

```python
services = {
    "webui": ServiceInfo(
        name="webui",
        display_name="DuckBot WebUI",
        port=8787,
        url="http://localhost:8787",
        auto_restart=True
    )
}
```

## 📈 API Reference

### System Status
```http
GET /api/status
```

Response:
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "system_metrics": {
    "cpu_percent": 45.2,
    "memory_percent": 62.1,
    "disk_percent": 78.3,
    "active_processes": 156
  },
  "services": {...},
  "agents": {...},
  "alerts": {...},
  "user_activity": {...}
}
```

### System Metrics
```http
GET /api/metrics/system?start_time=2024-01-15T00:00:00Z&end_time=2024-01-15T23:59:59Z
```

### Service Control
```http
POST /api/services/{service_name}/start
POST /api/services/{service_name}/stop
POST /api/services/{service_name}/restart
```

### Agent Metrics
```http
GET /api/metrics/agents?agent_id=chat_agent
```

### Alerts
```http
GET /api/alerts?active_only=true
POST /api/alerts/{alert_id}/resolve
```

### User Activity
```http
GET /api/activity?hours=24
```

## 🔌 Integration

### Python Integration
```python
from duckbot.integrations.monitoring_integration import (
    get_monitoring_integration, monitor_agent, monitor_user_activity
)

# Setup integration
integration = get_monitoring_integration()
integration.set_user_context(user_id="user123")

# Use decorators
@monitor_agent(agent_id="my_agent", agent_type="chat")
def chat_with_user(message):
    return ai_response(message)

@monitor_user_activity(activity_type="webui", feature_used="chat")
def handle_chat_request():
    # Handle chat request
    pass

# Manual recording
integration.record_agent_interaction(
    agent_id="custom_agent",
    agent_type="api",
    response_time_ms=150.5,
    success=True,
    model_used="gpt-4",
    tokens_used=100
)
```

### FastAPI Integration
```python
from duckbot.integrations.monitoring_integration import add_monitoring_middleware

app = FastAPI()
app = add_monitoring_middleware(app)
```

### Service Integration
```python
from duckbot.integrations.monitoring_integration import monitored_server_manager

# Start service with monitoring
success, message = monitored_server_manager.start_service("webui")
```

## 📊 Analytics and Reporting

### Data Export
```python
from duckbot.analytics.monitoring_analytics import get_analytics, AnalyticsPeriod, ReportFormat

analytics = get_analytics()

# Export system metrics
export_path = analytics.export_data(
    data_type="system_metrics",
    period=AnalyticsPeriod.DAY,
    format=ReportFormat.CSV
)

# Generate comprehensive report
report_path = analytics.generate_report(period=AnalyticsPeriod.WEEK)
```

### Performance Analysis
```python
# System performance analysis
system_report = analytics.get_system_performance_report(AnalyticsPeriod.DAY)

# Agent performance analysis
agent_report = analytics.get_agent_performance_report(AnalyticsPeriod.DAY)
```

## 🛠️ Development

### Running Tests
```bash
# Run all monitoring system tests
python -m pytest tests/test_monitoring_system.py -v

# Run specific test categories
python tests/test_monitoring_system.py
```

### Code Structure
```
duckbot/
├── core/
│   └── monitoring_system.py          # Core monitoring system
├── services/
│   └── enhanced_monitoring_dashboard.py  # Web dashboard
├── analytics/
│   └── monitoring_analytics.py       # Analytics and reporting
├── integrations/
│   └── monitoring_integration.py     # Integration helpers
└── ui/
    └── observability.py              # Observability endpoints
```

### Adding New Metrics
```python
# In your service or component
from duckbot.integrations.monitoring_integration import get_monitoring_integration

def my_function():
    integration = get_monitoring_integration()
    start_time = time.time()

    try:
        # Your function logic
        result = do_something()
        integration.record_agent_interaction(
            agent_id="my_service",
            agent_type="custom_operation",
            response_time_ms=(time.time() - start_time) * 1000,
            success=True
        )
        return result
    except Exception as e:
        integration.record_agent_interaction(
            agent_id="my_service",
            agent_type="custom_operation",
            response_time_ms=(time.time() - start_time) * 1000,
            success=False,
            error_message=str(e)
        )
        raise
```

## 🐛 Troubleshooting

### Common Issues

**Dashboard not accessible**
```bash
# Check if port is available
netstat -tulpn | grep 8790

# Try different port
python start_monitoring_system.py --port 8791
```

**Database errors**
```bash
# Check database permissions
ls -la monitoring.db

# Recreate database
rm monitoring.db
python start_monitoring_system.py
```

**High CPU usage**
```bash
# Adjust metrics collection interval
python start_monitoring_system.py --metrics 10
```

**Missing dependencies**
```bash
# Install required packages
pip install psutil fastapi uvicorn jinja2 pandas numpy openpyxl
```

### Debug Mode
```bash
# Enable debug logging
python start_monitoring_system.py --debug

# Check logs
tail -f monitoring.log
```

## 📈 Performance Considerations

### Database Optimization
- The system uses SQLite for data storage
- Metrics are automatically purged after 90 days
- Indexes are optimized for common queries
- Consider PostgreSQL for high-traffic deployments

### Memory Usage
- Metrics collection is memory-efficient
- Historical data is compressed and aggregated
- Dashboard uses lazy loading for large datasets
- WebSocket connections are optimized for real-time updates

### Network Usage
- Dashboard updates every 5 seconds by default
- Metrics are batched for efficient transmission
- Compression is used for large data transfers
- API responses are cached when appropriate

## 🔒 Security

### Data Protection
- All sensitive data is encrypted at rest
- User activity is anonymized by default
- API endpoints require authentication (configurable)
- Database access is restricted to application

### Access Control
- Dashboard access can be restricted by IP
- API endpoints support token authentication
- Service control requires administrator privileges
- Alert notifications can be encrypted

## 📊 Monitoring Metrics Reference

### System Metrics
| Metric | Type | Description |
|--------|------|-------------|
| `cpu_percent` | Gauge | CPU usage percentage |
| `memory_percent` | Gauge | Memory usage percentage |
| `disk_percent` | Gauge | Disk usage percentage |
| `network_bytes_sent_per_sec` | Gauge | Network bytes sent per second |
| `network_bytes_recv_per_sec` | Gauge | Network bytes received per second |
| `process_count` | Gauge | Number of active processes |
| `gpu_vram_total_gb` | Gauge | Total GPU VRAM in GB |

### Agent Metrics
| Metric | Type | Description |
|--------|------|-------------|
| `total_requests` | Counter | Total number of requests |
| `successful_requests` | Counter | Successful request count |
| `failed_requests` | Counter | Failed request count |
| `avg_response_time` | Gauge | Average response time in ms |
| `total_tokens` | Counter | Total tokens used |
| `success_rate` | Gauge | Success rate percentage |

### Service Metrics
| Metric | Type | Description |
|--------|------|-------------|
| `service_status` | Gauge | Service health status |
| `response_time_ms` | Gauge | Service response time |
| `uptime_seconds` | Counter | Service uptime in seconds |
| `error_count` | Counter | Service error count |

## 🤝 Contributing

### Development Setup
```bash
# Clone repository
git clone <repository-url>
cd DuckBot-Consolidated-v4.2

# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
python -m pytest tests/ -v

# Start development server
python start_monitoring_system.py --debug
```

### Code Standards
- Follow PEP 8 style guidelines
- Use type hints for all functions
- Add comprehensive docstrings
- Write unit tests for new features
- Use the provided integration patterns

## 📄 License

This monitoring system is part of DuckBot v4.2 and is released under the same license terms.

## 📞 Support

For issues and questions:
1. Check the troubleshooting section
2. Review the API documentation
3. Check existing GitHub issues
4. Create a new issue with detailed information

## 🔄 Updates and Changelog

### Version 1.0.0
- Initial release
- Real-time system metrics collection
- AI agent performance monitoring
- Service health monitoring
- User activity analytics
- Web dashboard with real-time updates
- Data export and reporting
- Alert management system
- Comprehensive API
- CLI interface

---

**DuckBot Monitoring System** - Comprehensive monitoring and analytics for intelligent AI systems