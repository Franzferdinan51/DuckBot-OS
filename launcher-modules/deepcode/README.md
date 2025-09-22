# DuckBot DeepCode CLI

A comprehensive command-line interface for DeepCode integration with the DuckBot ecosystem, providing Paper2Code, Text2Web, and Text2Backend capabilities.

## Features

- **Paper2Code**: Convert research papers to production-ready code
- **Text2Web**: Generate complete web applications from text descriptions
- **Text2Backend**: Create backend systems from natural language descriptions
- **Interactive Configuration Wizard**: Easy setup and configuration
- **Template Management**: Pre-built templates for common use cases
- **Real-time Monitoring**: Track task progress and status
- **Health Checks**: System diagnostics and recommendations
- **Service Management**: Start and manage DeepCode services
- **DuckBot Integration**: Seamless integration with DuckBot ecosystem

## Installation

The DeepCode CLI is included with DuckBot Enhanced v4.2. No additional installation is required.

## Quick Start

### 1. Configuration

```bash
# Run the interactive configuration wizard
python start_deepcode.py config
```

### 2. Health Check

```bash
# Check system health and dependencies
python start_deepcode.py health
```

### 3. View Templates

```bash
# List available templates
python start_deepcode.py templates
```

## Commands

### `paper2code` - Process Research Papers

Convert research papers to production-ready code.

```bash
# Basic usage
python start_deepcode.py paper2code research_paper.pdf

# With custom output directory
python start_deepcode.py paper2code research_paper.pdf -o ./my_project

# With task configuration
python start_deepcode.py paper2code research_paper.pdf -t config.json

# Follow progress in real-time
python start_deepcode.py paper2code research_paper.pdf -f
```

### `text2web` - Generate Web Applications

Generate complete web applications from text descriptions.

```bash
# Basic usage
python start_deepcode.py text2web "Create a dashboard application with user authentication"

# With custom output directory
python start_deepcode.py text2web "Create a CRUD app" -o ./web_app

# With task configuration
python start_deepcode.py text2web "Create a portfolio website" -t config.json

# Follow progress in real-time
python start_deepcode.py text2web "Create a blog platform" -f
```

### `text2backend` - Generate Backend Systems

Create backend systems from natural language descriptions.

```bash
# Basic usage
python start_deepcode.py text2backend "Create a REST API for user management"

# With custom output directory
python start_deepcode.py text2backend "Create a microservice architecture" -o ./backend

# With task configuration
python start_deepcode.py text2backend "Create a data processing API" -t config.json

# Follow progress in real-time
python start_deepcode.py text2backend "Create an authentication service" -f
```

### `status` - Check Task Status

Monitor and manage tasks.

```bash
# List all tasks
python start_deepcode.py status

# Check specific task
python start_deepcode.py status TASK_ID

# Filter by task type
python start_deepcode.py status --type paper2code

# Filter by status
python start_deepcode.py status --status completed

# Show detailed information
python start_deepcode.py status TASK_ID -d
```

### `config` - Configuration Wizard

Interactive configuration setup.

```bash
# Run configuration wizard
python start_deepcode.py config
```

The wizard will guide you through:
- Basic configuration (output directory, concurrent tasks, timeout)
- Quality settings (validation, testing, thresholds)
- Integration settings (DuckBot integration, cost tracking)
- API key configuration

### `service` - Start DeepCode Service

Run DeepCode as a background service.

```bash
# Start service on default port (8790)
python start_deepcode.py service

# Start service on custom port
python start_deepcode.py service -p 8080
```

### `templates` - List Available Templates

View available templates for different task types.

```bash
# List all templates
python start_deepcode.py templates

# Filter by template type
python start_deepcode.py templates --type paper2code
python start_deepcode.py templates --type text2web
python start_deepcode.py templates --type text2backend
```

### `health` - Health Check

Perform system diagnostics.

```bash
# Run health check
python start_deepcode.py health
```

## Configuration

### Configuration File

The CLI uses a JSON configuration file located at `config/deepcode_config.json`:

```json
{
  "api_keys": {
    "brave": "your_api_key_here"
  },
  "max_concurrent_tasks": 3,
  "timeout_seconds": 3600,
  "enable_validation": true,
  "enable_testing": true,
  "output_dir": "./deepcode_output",
  "artifact_format": "zip",
  "code_quality_threshold": 0.8,
  "test_coverage_threshold": 0.7,
  "enable_ast_analysis": true,
  "enable_duckbot_integration": true,
  "auto_register_models": true,
  "enable_cost_tracking": true
}
```

### Environment Variables

You can also configure DeepCode using environment variables:

```bash
# Basic configuration
export DEEPCODE_OUTPUT_DIR="./deepcode_output"
export DEEPCODE_MAX_CONCURRENT_TASKS=3
export DEEPCODE_TIMEOUT_SECONDS=3600

# Quality settings
export DEEPCODE_ENABLE_VALIDATION=true
export DEEPCODE_ENABLE_TESTING=true
export DEEPCODE_CODE_QUALITY_THRESHOLD=0.8

# API keys
export DEEPCODE_BRAVE_API_KEY="your_api_key_here"
```

## Templates

### Paper2Code Templates

- **ml_algorithm**: Machine learning algorithm implementation
- **data_processing**: Data processing pipeline
- **computer_vision**: Computer vision model

### Text2Web Templates

- **dashboard**: Analytics dashboard
- **crud_app**: CRUD web application
- **portfolio**: Portfolio website

### Text2Backend Templates

- **rest_api**: REST API service
- **microservice**: Microservice architecture
- **data_api**: Data processing API

## Output Structure

Generated projects follow a consistent structure:

```
deepcode_output/
├── task_id/
│   ├── main.py           # Main implementation
│   ├── utils.py           # Utility functions
│   ├── algorithms.py      # Algorithm implementations
│   ├── requirements.txt  # Python dependencies
│   ├── README.md         # Documentation
│   └── tests/            # Test files
└── logs/
    ├── deepcode.log      # Application logs
    └── tasks/            # Task-specific logs
```

## Integration with DuckBot

The DeepCode CLI integrates seamlessly with the DuckBot ecosystem:

- **Service Management**: Automatic registration with DuckBot service manager
- **Monitoring**: Integration with DuckBot monitoring system
- **Cost Tracking**: Usage and cost monitoring
- **AI Provider**: Access to DuckBot's AI provider manager
- **Logging**: Unified logging with DuckBot's logging system

## Examples

### Example 1: Process a Research Paper

```bash
# Configure DeepCode
python start_deepcode.py config

# Process a research paper
python start_deepcode.py paper2code ml_research.pdf -f

# Check status
python start_deepcode.py status
```

### Example 2: Generate a Web Application

```bash
# Generate a dashboard application
python start_deepcode.py text2web "Create a real-time analytics dashboard with charts" -o ./dashboard

# Monitor progress
python start_deepcode.py status --follow
```

### Example 3: Create a Backend API

```bash
# Generate a REST API
python start_deepcode.py text2backend "Create a user management API with JWT authentication" -o ./api

# Start DeepCode service
python start_deepcode.py service
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed
   ```bash
   pip install -r requirements.txt
   ```

2. **Permission Errors**: Check file permissions for output directory
   ```bash
   chmod -R 755 ./deepcode_output
   ```

3. **Port Conflicts**: Change service port if default port is in use
   ```bash
   python start_deepcode.py service -p 8080
   ```

### Health Check

Run the health check to diagnose issues:
```bash
python start_deepcode.py health
```

### Logs

Check logs for detailed error information:
```bash
# Application logs
tail -f ./deepcode_output/logs/deepcode.log

# Task-specific logs
ls -la ./deepcode_output/logs/tasks/
```

## Support

For issues and support:
1. Check the health check output
2. Review the logs
3. Ensure all dependencies are installed
4. Verify configuration settings
5. Check DuckBot ecosystem status

## License

This CLI is part of DuckBot Enhanced v4.2 and is subject to the same license terms.