# DuckBot Configuration Management System

## Overview

DuckBot v4.2 features a comprehensive centralized configuration management system that eliminates hard-coded values scattered throughout startup scripts and provides a unified approach to managing all service configurations, feature flags, and environment-specific settings.

## Architecture

### Core Components

1. **Centralized Configuration File** (`config/duckbot_config.yaml`)
   - Single source of truth for all configuration
   - YAML-based for human readability
   - Hierarchical structure with inheritance

2. **Configuration Manager** (`config/config_manager.py`)
   - Python class for managing configuration lifecycle
   - Dynamic port allocation and conflict resolution
   - Environment-specific overrides
   - Validation and error handling

3. **Environment-Specific Files** (`config/environments/`)
   - `development.yaml` - Development environment settings
   - `production.yaml` - Production environment settings
   - `local.yaml` - Local/offline environment settings

4. **Configuration Utility** (`utils/config_utility.py`)
   - Command-line interface for configuration management
   - Service status monitoring
   - Configuration validation and testing

## Key Features

### 🎯 Centralized Service Management
- All service definitions in one place
- Consistent configuration patterns
- Dynamic port allocation with conflict resolution
- Service health monitoring and status tracking

### 🌍 Environment-Specific Configurations
- Development, production, and local environment profiles
- Automatic environment detection
- Configuration inheritance and overrides
- Feature flags per environment

### 🔧 Smart Port Management
- Automatic port allocation within defined ranges
- Conflict detection and resolution
- Reserved port protection
- Service-specific port ranges

### ✅ Configuration Validation
- Comprehensive validation checks
- Port conflict detection
- Required service verification
- AI provider configuration validation

### 🚀 Feature Flag System
- Centralized feature toggles
- Environment-specific feature sets
- Runtime feature enablement/disablement
- Feature dependency management

## File Structure

```
config/
├── duckbot_config.yaml              # Main configuration file
├── config_manager.py               # Configuration manager class
├── environments/
│   ├── development.yaml            # Development environment
│   ├── production.yaml             # Production environment
│   └── local.yaml                  # Local environment
├── ai_config.json                  # AI provider settings (legacy)
├── ecosystem_config.yaml           # Service settings (legacy)
├── vibevoice_config.yaml           # VibeVoice settings (legacy)
└── livekit_config.yaml             # LiveKit settings (legacy)

utils/
├── config_utility.py               # Command-line configuration utility

launcher/
└── START_ENHANCED_CONFIG.bat       # Enhanced launcher with config management

templates/
└── start_service_template.bat      # Service launcher template

tests/
└── test_config_system.py           # Configuration system tests
```

## Configuration Structure

### Main Configuration File

```yaml
# System-wide settings
system:
  name: "DuckBot Enhanced v4.2"
  version: "4.2"
  log_level: "INFO"

# Service definitions
services:
  webui:
    enabled: true
    name: "Enhanced WebUI Dashboard"
    default_host: "127.0.0.1"
    default_port: 8787
    health_endpoint: "/enhanced/health"
    startup_script: "duckbot.enhanced_webui"
    environment_vars:
      DUCKBOT_WEBUI_PORT: "{port}"
      DUCKBOT_WEBUI_HOST: "{host}"

# Feature flags
features:
  webui_enabled: true
  monitoring_enabled: true
  local_ai_enabled: true
  local_only_mode: false

# Hardware settings
hardware:
  min_ram_gb: 4
  max_concurrent_services: 10
  gpu_enabled: true
```

### Environment Overrides

```yaml
# config/environments/development.yaml
system:
  debug_mode: true
  log_level: "DEBUG"

features:
  debug_mode: true
  developer_tools: true
  telemetry_enabled: true
```

## Usage

### Command-Line Interface

#### Basic Commands

```bash
# Show current configuration
python utils/config_utility.py show

# List all services
python utils/config_utility.py list

# Check service status
python utils/config_utility.py status

# Validate configuration
python utils/config_utility.py validate
```

#### Advanced Commands

```bash
# Export configuration to JSON
python utils/config_utility.py export --output config.json

# Start a specific service
python utils/config_utility.py start webui --background

# Set environment
python utils/config_utility.py set-env production

# Toggle feature flags
python utils/config_utility.py toggle webui_enabled --save

# Create configuration backup
python utils/config_utility.py backup

# Restore from backup
python utils/config_utility.py restore config/backup_config_20250916_120000.yaml
```

### Python API

```python
from config.config_manager import get_config_manager, Environment

# Initialize configuration manager
config_manager = get_config_manager(environment=Environment.DEVELOPMENT)

# Get service configuration
webui_config = config_manager.get_service_config('webui')

# Allocate port for service
port = config_manager.allocate_port('webui')

# Get environment variables
env_vars = config_manager.get_service_environment('webui')

# Check feature flag
if config_manager.get_feature_flag('local_only_mode'):
    print("Running in local-only mode")

# Validate configuration
issues = config_manager.validate_config()
if issues:
    print("Configuration issues found:")
    for issue in issues:
        print(f"  - {issue}")
```

### Batch Script Integration

```batch
@echo off
set DUCKBOT_ENV=development
set SERVICE_NAME=webui

python utils/config_utility.py start %SERVICE_NAME% --background
```

## Service Configuration

### Service Properties

Each service in the configuration supports the following properties:

```yaml
service_name:
  enabled: true                    # Whether service is active
  name: "Display Name"           # Human-readable name
  default_host: "127.0.0.1"      # Default host address
  default_port: 8000             # Default port number
  health_endpoint: "/health"     # Health check endpoint
  startup_script: "module.path"  # Python module to start
  startup_args: ["--option"]     # Additional startup arguments
  external_service: false        # Is this an external service?
  startup_check: false          # Check if service is running?
  required: false                # Is this service required?
  environment_vars: {}          # Environment variables
```

### Environment Variables

Services support template-based environment variables:

```yaml
environment_vars:
  SERVICE_PORT: "{port}"         # Substituted with allocated port
  SERVICE_HOST: "{host}"         # Substituted with service host
  SERVICE_URL: "http://{host}:{port}"  # Combined URL
```

## Port Management

### Port Ranges

The system defines port ranges for different service types:

```yaml
ports:
  webui_range: [8780, 8799]        # WebUI services
  ai_services_range: [8700, 8779]  # AI services
  external_services_range: [8000, 8099]  # External services
  database_range: [5400, 5500]     # Database services
  monitoring_range: [9000, 9099]  # Monitoring services
```

### Port Allocation

```python
# Allocate default port
port = config_manager.allocate_port('webui')

# Allocate specific port (if available)
port = config_manager.allocate_port('webui', 8788)

# Release port
config_manager.release_port(port)
```

## Environment Management

### Environment Detection

The system automatically detects the environment based on:

1. `DUCKBOT_ENV` environment variable
2. `AI_LOCAL_ONLY_MODE` environment variable
3. Default: development

### Environment Profiles

#### Development Environment
- Debug mode enabled
- Relaxed security settings
- All services enabled
- Verbose logging

#### Production Environment
- Debug mode disabled
- Strict security settings
- Essential services only
- Optimized logging

#### Local Environment
- Offline mode enabled
- Local AI only
- Minimal external dependencies
- Privacy-focused settings

## Feature Flags

### Available Features

```yaml
features:
  # Core Features
  webui_enabled: true
  monitoring_enabled: true
  terminal_enabled: true

  # AI Features
  ai_routing_enabled: true
  local_ai_enabled: true
  cloud_ai_enabled: true
  multi_agent_enabled: true

  # Privacy Features
  local_only_mode: false
  telemetry_enabled: false
  analytics_enabled: true

  # Development Features
  debug_mode: false
  developer_tools: false
  testing_mode: false
```

### Feature Flag Usage

```python
# Check feature flag
if config_manager.get_feature_flag('local_only_mode'):
    # Enable local-only behavior
    pass

# Toggle feature at runtime
config_manager.config_data['features']['debug_mode'] = True
```

## Configuration Validation

### Validation Checks

The system performs comprehensive validation:

1. **Port Conflicts**: Detects duplicate port usage
2. **Required Services**: Ensures required services are enabled
3. **AI Providers**: Verifies at least one AI provider is enabled
4. **Service Dependencies**: Checks service prerequisites
5. **Environment Consistency**: Validates environment-specific settings

### Running Validation

```bash
# Validate configuration
python utils/config_utility.py validate

# Check specific environment
python utils/config_utility.py validate --env production
```

## Migration Guide

### From Hard-coded Scripts

**Before:**
```batch
REM Old launcher with hard-coded values
python -m duckbot.enhanced_webui --host 127.0.0.1 --port 8787
python -m ai_ecosystem_manager --host 127.0.0.1 --port 8789
```

**After:**
```batch
REM New launcher with configuration management
set DUCKBOT_ENV=development
python utils/config_utility.py start webui --background
python utils/config_utility.py start monitoring --background
```

### From Legacy Configuration Files

1. **Backup existing configurations**
2. **Create new `duckbot_config.yaml`**
3. **Migrate service definitions**
4. **Update scripts to use new system**
5. **Test thoroughly**

## Best Practices

### Configuration Management

1. **Use environment-specific files** for different deployment scenarios
2. **Validate configuration** before starting services
3. **Use feature flags** for optional functionality
4. **Document configuration changes** with comments
5. **Back up configurations** before making changes

### Service Configuration

1. **Define all services** in the main configuration file
2. **Use meaningful service names** and descriptions
3. **Set appropriate defaults** for ports and hosts
4. **Define health check endpoints** for all services
5. **Use template variables** for environment variables

### Port Management

1. **Define port ranges** for different service types
2. **Use dynamic port allocation** to avoid conflicts
3. **Reserve well-known ports** (80, 443, etc.)
4. **Test port availability** before deployment
5. **Document port usage** in service configurations

## Troubleshooting

### Common Issues

#### Port Conflicts
```bash
# Check port usage
python utils/config_utility.py validate

# See allocated ports
python utils/config_utility.py show | grep "port"
```

#### Service Not Starting
```bash
# Check service configuration
python utils/config_utility.py list

# Verify service status
python utils/config_utility.py status
```

#### Configuration Errors
```bash
# Validate configuration
python utils/config_utility.py validate

# Check environment settings
python utils/config_utility.py show --env production
```

### Debug Mode

Enable debug mode for detailed logging:

```bash
set DUCKBOT_ENV=development
python utils/config_utility.py start webui --background
```

## Integration Examples

### Custom Launcher Script

```python
#!/usr/bin/env python3
import os
from config.config_manager import get_config_manager, Environment

def main():
    # Initialize configuration
    config_manager = get_config_manager(environment=Environment.DEVELOPMENT)

    # Start essential services
    essential_services = ['webui', 'monitoring', 'terminal']

    for service_name in essential_services:
        if config_manager.is_service_available(service_name):
            port = config_manager.allocate_port(service_name)
            env_vars = config_manager.get_service_environment(service_name)

            # Set environment variables
            for key, value in env_vars.items():
                os.environ[key] = value

            # Start service
            print(f"Starting {service_name} on port {port}")
            # ... service startup logic ...

if __name__ == "__main__":
    main()
```

### Service Health Monitoring

```python
#!/usr/bin/env python3
from config.config_manager import get_config_manager

def monitor_services():
    config_manager = get_config_manager()
    services = config_manager.get_enabled_services()

    for service_name in services.keys():
        available = config_manager.is_service_available(service_name)
        url = config_manager.get_service_url(service_name)

        status = "✓" if available else "✗"
        print(f"{status} {service_name}: {url}")

if __name__ == "__main__":
    monitor_services()
```

## Testing

### Running Tests

```bash
# Run configuration system tests
python tests/test_config_system.py

# Run specific test categories
python -m pytest tests/test_config_system.py::TestDuckBotConfigManager::test_port_allocation
```

### Test Coverage

The test suite covers:
- Configuration loading and validation
- Service management and port allocation
- Environment detection and overrides
- Feature flag functionality
- Integration scenarios
- Error handling and edge cases

## Contributing

### Adding New Services

1. **Define service** in `config/duckbot_config.yaml`
2. **Add environment-specific overrides** if needed
3. **Update tests** to cover new service
4. **Test configuration validation**
5. **Update documentation**

### Configuration Changes

1. **Test changes** in development environment
2. **Validate configuration** using the utility
3. **Update affected scripts**
4. **Run comprehensive tests**
5. **Document changes**

## License

This configuration management system is part of DuckBot v4.2 and follows the same license terms as the main project.

---

For more information, see the [DuckBot Documentation](README.md) or join the community discussions.