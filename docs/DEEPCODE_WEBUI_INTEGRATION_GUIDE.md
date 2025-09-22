# DeepCode WebUI Integration Guide

## Overview

The DeepCode WebUI integration provides a comprehensive web-based interface for DuckBot's AI-powered development capabilities. This integration includes:

- **Web Dashboard**: Modern, responsive web interface for all DeepCode features
- **REST API**: Complete RESTful API for all DeepCode operations
- **WebSocket Support**: Real-time updates and live monitoring
- **Authentication & Authorization**: Secure access control with role-based permissions
- **File Management**: Upload and processing of research papers and documents
- **Task Management**: Create, monitor, and manage AI-powered development tasks
- **Agent Coordination**: Monitor and manage AI agents
- **MCP Server Integration**: Manage Model Context Protocol servers

## Architecture

### Components

1. **DeepCode WebUI Service** (`duckbot/services/deepcode_webui_service.py`)
   - FastAPI-based REST API server
   - WebSocket support for real-time updates
   - Integration with existing DuckBot services
   - Authentication and authorization middleware

2. **Authentication Integration** (`duckbot/services/deepcode_auth_integration.py`)
   - JWT-based authentication
   - Role-based access control
   - API key management
   - Session management

3. **Web Interface** (`webui/main/deepcode_dashboard.html`)
   - Modern, responsive HTML interface
   - Real-time updates via WebSocket
   - Mobile-friendly design
   - Dark mode support

4. **Frontend Assets**
   - CSS styles (`duckbot/static/deepcode-styles.css`)
   - JavaScript (`duckbot/static/deepcode-ui.js`)
   - Chart.js for data visualization

5. **Templates** (`duckbot/templates/deepcode/`)
   - Jinja2 templates for server-side rendering
   - Reusable base template
   - Dynamic content injection

## Features

### 1. Paper2Code Integration

- **Upload**: Drag-and-drop or click-to-upload research papers
- **Analysis**: AI-powered analysis of research papers
- **Code Generation**: Generate production-ready code from papers
- **Format Support**: PDF, DOC, DOCX, TXT, MD

### 2. Text2Web

- **Framework Support**: React, Vue.js, Angular, Svelte, Next.js
- **Styling Options**: Tailwind CSS, Bootstrap, Material UI, Chakra UI
- **Project Generation**: Complete web applications from text descriptions
- **Code Quality**: Optimized, production-ready code

### 3. Text2Backend

- **Language Support**: Python, Node.js, Go, Rust
- **Framework Options**: FastAPI, Flask, Express, NestJS, Gin, Axum
- **Database Integration**: PostgreSQL, MySQL, MongoDB, SQLite, Redis
- **API Generation**: Complete REST APIs with documentation

### 4. Agent Management

- **Agent Types**: Paper Analyzer, Code Generator, Quality Assurance, Project Manager
- **Real-time Monitoring**: Live status updates and performance metrics
- **Task Assignment**: Automatic task distribution and load balancing
- **Performance Analytics**: Charts and statistics for agent performance

### 5. MCP Server Management

- **Server Types**: Document Analysis, Code Generation, Web Scaffolding, Backend Generation, Quality Assurance
- **Connection Management**: Start, stop, and monitor MCP servers
- **Health Monitoring**: Real-time server status and performance metrics
- **Configuration**: Dynamic server configuration and scaling

## Installation and Setup

### Prerequisites

- Python 3.8+
- FastAPI and related dependencies
- Node.js (for frontend development, optional)
- Modern web browser with WebSocket support

### Installation

1. **Install Dependencies**
   ```bash
   pip install fastapi uvicorn jinja2 pydantic python-multipart
   pip install chart.js  # For data visualization
   ```

2. **Create Directories**
   ```bash
   mkdir -p uploads/deepcode logs
   ```

3. **Start the Service**
   ```bash
   # Using the launcher script
   launcher/START_DEEPCODE_WEBUI.bat

   # Or directly with Python
   python -m duckbot.services.deepcode_webui_service --host 127.0.0.1 --port 8790
   ```

### Configuration

#### Environment Variables

```bash
# Service Configuration
DEEPCODE_HOST=127.0.0.1
DEEPCODE_PORT=8790
DEEPCODE_LOG_LEVEL=INFO

# Security Configuration
DEEPCODE_SECRET_KEY=your-secret-key-here
DEEPCODE_ACCESS_TOKEN_EXPIRE_MINUTES=30
DEEPCODE_REFRESH_TOKEN_EXPIRE_DAYS=7

# File Upload Configuration
DEEPCODE_MAX_FILE_SIZE=104857600  # 100MB
DEEPCODE_UPLOAD_DIR=uploads/deepcode
```

#### Configuration Files

Create a `config/deepcode_config.json` file:

```json
{
  "service": {
    "host": "127.0.0.1",
    "port": 8790,
    "log_level": "INFO"
  },
  "security": {
    "secret_key": "your-secret-key",
    "access_token_expire_minutes": 30,
    "refresh_token_expire_days": 7
  },
  "upload": {
    "max_file_size": 104857600,
    "allowed_types": [".pdf", ".doc", ".docx", ".txt", ".md"],
    "upload_dir": "uploads/deepcode"
  },
  "features": {
    "paper2code": {
      "enabled": true,
      "max_pages": 100
    },
    "text2web": {
      "enabled": true,
      "supported_frameworks": ["react", "vue", "angular", "svelte", "next"]
    },
    "text2backend": {
      "enabled": true,
      "supported_frameworks": ["fastapi", "flask", "express", "nestjs", "gin", "axum"]
    }
  }
}
```

## Usage

### Web Interface

1. **Access the Dashboard**
   - Open `http://localhost:8790/deepcode` in your browser
   - Login with default credentials (admin/admin)

2. **Navigate Features**
   - **Overview**: System status and quick actions
   - **Paper2Code**: Upload and analyze research papers
   - **Text2Web**: Generate web applications
   - **Text2Backend**: Generate backend services
   - **Agents**: Monitor and manage AI agents
   - **MCP Servers**: Manage MCP server connections

### API Usage

#### Authentication

```bash
# Login and get access token
curl -X POST "http://localhost:8790/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin"

# Use token for authenticated requests
curl -X GET "http://localhost:8790/api/deepcode/status" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### Task Management

```bash
# Create a new task
curl -X POST "http://localhost:8790/api/deepcode/tasks" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "text2web",
    "description": "Create a todo application",
    "priority": "medium",
    "parameters": {
      "framework": "react",
      "styling": "tailwind"
    }
  }'

# Get all tasks
curl -X GET "http://localhost:8790/api/deepcode/tasks" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### File Upload

```bash
# Upload a research paper
curl -X POST "http://localhost:8790/api/deepcode/upload-paper" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "file=@research_paper.pdf"
```

### WebSocket Usage

```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:8790/ws/deepcode');

// Listen for messages
ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Received:', data);
};

// Send messages
ws.send(JSON.stringify({
    type: 'ping'
}));
```

## Security

### Authentication Methods

1. **JWT Tokens**: Bearer token authentication
2. **API Keys**: For programmatic access
3. **Session Management**: For web interface

### Role-Based Access Control

- **Admin**: Full access to all features
- **Developer**: Access to code generation and deployment
- **Analyst**: Access to analysis and monitoring
- **Viewer**: Read-only access

### Permission System

- `paper:upload` - Upload research papers
- `paper:analyze` - Analyze uploaded papers
- `paper:generate` - Generate code from papers
- `web:generate` - Generate web applications
- `web:deploy` - Deploy web applications
- `backend:generate` - Generate backend services
- `backend:deploy` - Deploy backend services
- `agent:create` - Create new agents
- `agent:manage` - Manage existing agents
- `agent:view` - View agent information
- `mcp:manage` - Manage MCP servers
- `mcp:view` - View MCP server information
- `system:config` - Configure system settings
- `system:monitor` - Monitor system status
- `user:manage` - Manage users

## Monitoring and Logging

### Logs

- Service logs: `logs/deepcode.log`
- Error logs: `logs/deepcode_errors.log`
- Access logs: `logs/deepcode_access.log`

### Monitoring

- **Health Check**: `GET /health`
- **System Status**: `GET /api/deepcode/status`
- **Metrics**: WebSocket real-time updates
- **Performance Charts**: Built-in performance monitoring

### Alerts

- Service failure notifications
- High resource usage warnings
- Task failure alerts
- Security event notifications

## Testing

### Unit Tests

```bash
# Run all tests
python -m pytest tests/test_deepcode_webui.py -v

# Run specific test categories
python -m pytest tests/test_deepcode_webui.py::TestDeepCodeWebUIService -v
python -m pytest tests/test_deepcode_webui.py::TestDeepCodeAuthIntegration -v
```

### Integration Tests

```bash
# Run integration tests
python -m pytest tests/test_deepcode_webui.py -m integration -v
```

### Load Testing

```bash
# Run load tests (requires additional setup)
python -m pytest tests/test_deepcode_webui.py -k "load" -v
```

## Troubleshooting

### Common Issues

1. **Service Won't Start**
   - Check if port 8790 is available
   - Verify Python dependencies are installed
   - Check logs for error messages

2. **Authentication Failures**
   - Verify username and password
   - Check if tokens are expired
   - Verify secret key configuration

3. **WebSocket Connection Issues**
   - Check firewall settings
   - Verify WebSocket support in browser
   - Check network connectivity

4. **File Upload Failures**
   - Check file size limits
   - Verify file format support
   - Check disk space

### Debug Mode

```bash
# Start service in debug mode
python -m duckbot.services.deepcode_webui_service --host 127.0.0.1 --port 8790 --debug --reload
```

### Log Analysis

```bash
# View service logs
tail -f logs/deepcode.log

# View error logs
tail -f logs/deepcode_errors.log

# Filter for specific errors
grep "ERROR" logs/deepcode.log
```

## Integration with DuckBot Ecosystem

### Service Manager Integration

The DeepCode WebUI service integrates with DuckBot's Unified Service Manager:

```python
from duckbot.core.service_manager import UnifiedServiceManager

# Register DeepCode service
service_manager = UnifiedServiceManager()
deepcode_service = service_manager.register_service(
    name="deepcode_webui",
    service_type=ServiceType.WEBUI,
    start_command="python -m duckbot.services.deepcode_webui_service",
    port=8790
)
```

### Monitoring Integration

Integrates with DuckBot's monitoring system:

```python
from duckbot.core.monitoring_system import MonitoringSystem

monitoring = MonitoringSystem()
monitoring.add_metric("deepcode_tasks_completed", "counter")
monitoring.add_metric("deepcode_active_agents", "gauge")
monitoring.add_metric("deepcode_api_requests", "counter")
```

### Cost Management Integration

Tracks API usage and costs:

```python
from duckbot.core.cost_management import CostTracker

cost_tracker = CostTracker()
cost_tracker.track_usage("deepcode_api", "paper2code", 1)
cost_tracker.track_usage("deepcode_api", "text2web", 1)
```

## Performance Optimization

### Caching

- Redis for session storage
- File upload caching
- API response caching
- Static asset caching

### Database Optimization

- Connection pooling
- Query optimization
- Index optimization
- Data archiving

### Load Balancing

- Horizontal scaling support
- Load balancing configuration
- High availability setup
- Failover mechanisms

## Future Enhancements

### Planned Features

1. **Enhanced UI/UX**
   - Improved mobile experience
   - Dark mode enhancements
   - Accessibility improvements
   - Performance optimizations

2. **Advanced Features**
   - Collaborative development
   - Version control integration
   - CI/CD pipeline integration
   - Multi-tenant support

3. **AI Enhancements**
   - Improved code quality
   - Better error handling
   - Enhanced pattern recognition
   - Multi-language support

4. **Monitoring & Analytics**
   - Advanced analytics dashboard
   - Performance metrics
   - Usage statistics
   - Predictive maintenance

## Contributing

### Development Setup

1. Fork the repository
2. Create a feature branch
3. Install development dependencies
4. Make changes
5. Run tests
6. Submit pull request

### Code Style

- Follow PEP 8 guidelines
- Use type hints
- Write comprehensive tests
- Document all public APIs

### Testing Requirements

- Unit tests for all new features
- Integration tests for complex workflows
- Performance tests for critical paths
- Security tests for authentication/authorization

## License

This integration is part of the DuckBot project and is subject to the same license terms.

## Support

For issues and questions:
- Create an issue on the DuckBot repository
- Check the documentation
- Review existing issues
- Contact the development team

---

*This integration enhances DuckBot's capabilities with a comprehensive web interface for AI-powered development, making advanced features accessible through an intuitive, modern web platform.*