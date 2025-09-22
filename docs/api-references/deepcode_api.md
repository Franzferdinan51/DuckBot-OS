# DeepCode API Reference

This document provides comprehensive API reference documentation for the DeepCode integration in DuckBot.

## Overview

The DeepCode API provides programmatic access to the HKUDS DeepCode capabilities for Open Agentic Coding, including:

- Paper2Code: Convert research papers to production-ready code
- Text2Web: Generate complete web applications from text descriptions
- Text2Backend: Create backend systems from natural language
- Custom Templates: Specialized project generation
- Performance Optimization: Advanced optimization features

## Core Classes

### DuckBotDeepCodeIntegration

The main integration class for DeepCode functionality.

```python
class DuckBotDeepCodeIntegration:
    """Main DeepCode integration class for DuckBot ecosystem."""

    async def paper2code(
        self,
        paper_description: str,
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Convert research paper to production-ready code.

        Args:
            paper_description: Content or description of the research paper
            config: Configuration options for code generation

        Returns:
            Dictionary containing task information and status
        """

    async def text2web(
        self,
        description: str,
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate complete web application from text description.

        Args:
            description: Natural language description of the web application
            config: Configuration options for web generation

        Returns:
            Dictionary containing task information and status
        """

    async def text2backend(
        self,
        description: str,
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate backend system from text description.

        Args:
            description: Natural language description of the backend system
            config: Configuration options for backend generation

        Returns:
            Dictionary containing task information and status
        """

    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get the status of a specific task.

        Args:
            task_id: ID of the task to check

        Returns:
            Dictionary containing task status information
        """
```

## API Methods

### Paper2Code

#### Method: `paper2code()`

Converts research papers to production-ready code with comprehensive features.

**Parameters:**
- `paper_description` (str): Content or description of the research paper
- `config` (Optional[Dict[str, Any]]): Configuration options

**Configuration Options:**
```python
config = {
    # AI Model Settings
    "model": "qwen3-coder",           # AI model to use
    "temperature": 0.2,                # Response temperature
    "max_tokens": 4000,               # Maximum response tokens
    "confidence_threshold": 0.75,      # Minimum confidence level

    # Output Settings
    "output_format": "production_ready",  # Output format
    "target_language": "python",       # Target programming language
    "code_style": "clean",             # Code style preference

    # Features
    "include_tests": True,             # Include unit tests
    "include_documentation": True,    # Include documentation
    "include_examples": True,          # Include usage examples
    "include_error_handling": True,    # Include error handling
    "include_type_hints": True,        # Include type hints

    # Quality Assurance
    "enable_validation": True,         # Enable code validation
    "enable_security_analysis": True,  # Enable security analysis
    "code_quality_threshold": 0.8,     # Minimum code quality

    # Performance
    "enable_caching": True,            # Enable result caching
    "parallel_processing": False,      # Enable parallel processing
    "max_concurrent_tasks": 1          # Maximum concurrent tasks
}
```

**Response:**
```python
{
    "task_id": "task_123456",
    "status": "submitted",
    "output_path": "/path/to/output",
    "estimated_duration": 300,
    "created_at": "2024-01-01T12:00:00Z"
}
```

**Example:**
```python
deepcode = DuckBotDeepCodeIntegration()

paper_description = """
This paper presents a novel approach to sentiment analysis using transformer-based models.
The model combines BERT architecture with attention mechanisms to achieve state-of-the-art
performance on sentiment classification tasks.
"""

result = await deepcode.paper2code(
    paper_description=paper_description,
    config={
        "include_tests": True,
        "include_documentation": True,
        "target_language": "python"
    }
)
```

### Text2Web

#### Method: `text2web()`

Generates complete web applications from text descriptions.

**Parameters:**
- `description` (str): Natural language description of the web application
- `config` (Optional[Dict[str, Any]]): Configuration options

**Configuration Options:**
```python
config = {
    # Framework Settings
    "framework": "react",               # Target framework
    "version": "18.0",                 # Framework version
    "language": "typescript",           # Programming language
    "styling": "tailwind",              # CSS framework

    # Features
    "include_auth": True,               # Include authentication
    "include_database": True,          # Include database integration
    "include_responsive": True,         # Responsive design
    "include_accessibility": True,      # Accessibility features
    "include_pwa": True,               # Progressive Web App

    # Backend
    "backend_framework": "fastapi",    # Backend framework
    "database": "postgresql",          # Database type
    "include_api_docs": True,          # API documentation

    # Development
    "include_docker": True,             # Docker support
    "include_ci_cd": True,              # CI/CD pipeline
    "include_testing": True,            # Test suite

    # UI Components
    "include_navigation": True,         # Navigation component
    "include_forms": True,              # Form components
    "include_tables": True,             # Table components
    "include_charts": True,             # Chart components

    # Performance
    "enable_optimization": True,        # Performance optimization
    "enable_lazy_loading": True,        # Lazy loading
    "enable_code_splitting": True       # Code splitting
}
```

**Response:**
```python
{
    "task_id": "task_789012",
    "status": "submitted",
    "output_path": "/path/to/webapp",
    "framework": "react",
    "estimated_duration": 600,
    "created_at": "2024-01-01T12:00:00Z"
}
```

**Example:**
```python
deepcode = DuckBotDeepCodeIntegration()

web_description = """
Create a task management web application with user authentication, task creation/editing,
due dates, progress tracking, team collaboration, and responsive design.
"""

result = await deepcode.text2web(
    description=web_description,
    config={
        "framework": "react",
        "include_auth": True,
        "include_database": True,
        "backend_framework": "fastapi"
    }
)
```

### Text2Backend

#### Method: `text2backend()`

Creates backend systems from natural language descriptions.

**Parameters:**
- `description` (str): Natural language description of the backend system
- `config` (Optional[Dict[str, Any]]): Configuration options

**Configuration Options:**
```python
config = {
    # Architecture
    "framework": "fastapi",             # Backend framework
    "architecture": "microservices",    # Architecture pattern
    "include_database": True,          # Database integration
    "include_auth": True,               # Authentication

    # API Features
    "include_rest_api": True,           # REST API endpoints
    "include_graphql": False,           # GraphQL support
    "include_websockets": True,         # WebSocket support
    "include_openapi": True,            # OpenAPI documentation

    # Database
    "database": "postgresql",          # Database type
    "orm": "sqlalchemy",               # ORM framework
    "include_migrations": True,        # Database migrations
    "include_seeding": True,           # Data seeding

    # Security
    "include_jwt": True,                # JWT authentication
    "include_oauth": True,              # OAuth support
    "include_rate_limiting": True,      # Rate limiting
    "include_cors": True,               # CORS support

    # Features
    "include_caching": True,            # Caching layer
    "include_monitoring": True,         # Monitoring and logging
    "include_testing": True,            # Test suite
    "include_validation": True          # Input validation
}
```

**Response:**
```python
{
    "task_id": "task_345678",
    "status": "submitted",
    "output_path": "/path/to/backend",
    "framework": "fastapi",
    "estimated_duration": 450,
    "created_at": "2024-01-01T12:00:00Z"
}
```

**Example:**
```python
deepcode = DuckBotDeepCodeIntegration()

backend_description = """
Create a REST API for an e-commerce platform with user management, product catalog,
order processing, payment integration, and inventory management.
"""

result = await deepcode.text2backend(
    description=backend_description,
    config={
        "framework": "fastapi",
        "include_auth": True,
        "include_database": True,
        "include_monitoring": True
    }
)
```

### Task Status

#### Method: `get_task_status()`

Retrieves the current status of a submitted task.

**Parameters:**
- `task_id` (str): ID of the task to check

**Response:**
```python
{
    "task_id": "task_123456",
    "status": "completed",              # submitted, processing, completed, failed
    "progress": 100,                   # Progress percentage (0-100)
    "current_step": "Finalizing files", # Current processing step
    "message": "Task completed successfully",
    "created_at": "2024-01-01T12:00:00Z",
    "updated_at": "2024-01-01T12:15:00Z",
    "duration": 900,                   # Duration in seconds
    "generated_files": [               # List of generated files
        "main.py",
        "requirements.txt",
        "tests/test_main.py",
        "docs/README.md"
    ],
    "output_path": "/path/to/output",
    "error": None                      # Error message if failed
}
```

**Example:**
```python
status = await deepcode.get_task_status("task_123456")

if status["status"] == "completed":
    print(f"Task completed with {len(status['generated_files'])} files")
    print(f"Output directory: {status['output_path']}")
elif status["status"] == "failed":
    print(f"Task failed: {status['error']}")
else:
    print(f"Task progress: {status['progress']}%")
```

## MCP Servers

### DocumentAnalysisMCPServer

Server for document analysis and processing.

```python
class DocumentAnalysisMCPServer:
    """MCP server for document analysis."""

    async def analyze_document(self, document_path: str) -> Dict[str, Any]:
        """Analyze document for content extraction.

        Args:
            document_path: Path to the document

        Returns:
            Document analysis results
        """

    async def extract_paper_content(self, document_path: str) -> Dict[str, Any]:
        """Extract research paper content.

        Args:
            document_path: Path to the paper

        Returns:
            Extracted paper content and metadata
        """
```

### CodeGenerationMCPServer

Server for code generation tasks.

```python
class CodeGenerationMCPServer:
    """MCP server for code generation."""

    async def generate_code(self, prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate code from prompt and context.

        Args:
            prompt: Code generation prompt
            context: Context information

        Returns:
            Generated code and metadata
        """

    async def optimize_code(self, code: str, language: str) -> Dict[str, Any]:
        """Optimize existing code.

        Args:
            code: Code to optimize
            language: Programming language

        Returns:
            Optimized code and improvements
        """
```

### WebScaffoldingMCPServer

Server for web application scaffolding.

```python
class WebScaffoldingMCPServer:
    """MCP server for web scaffolding."""

    async def scaffold_application(self, description: str, framework: str) -> Dict[str, Any]:
        """Scaffold web application structure.

        Args:
            description: Application description
            framework: Target framework

        Returns:
            Scaffolded application structure
        """

    async def generate_components(self, description: str, framework: str) -> Dict[str, Any]:
        """Generate UI components.

        Args:
            description: Component description
            framework: Target framework

        Returns:
            Generated components
        """
```

### BackendGenerationMCPServer

Server for backend system generation.

```python
class BackendGenerationMCPServer:
    """MCP server for backend generation."""

    async def generate_backend(self, description: str, architecture: str) -> Dict[str, Any]:
        """Generate backend system structure.

        Args:
            description: Backend description
            architecture: Target architecture

        Returns:
            Generated backend structure
        """

    async def generate_apis(self, description: str, framework: str) -> Dict[str, Any]:
        """Generate API endpoints.

        Args:
            description: API description
            framework: Target framework

        Returns:
            Generated API endpoints
        """
```

## Configuration Management

### Environment Variables

DeepCode supports several environment variables for configuration:

```bash
# AI Model Configuration
DEEPCODE_MODEL="qwen3-coder"
DEEPCODE_TEMPERATURE=0.2
DEEPCODE_MAX_TOKENS=4000
DEEPCODE_CONFIDENCE_THRESHOLD=0.75

# Performance Settings
DEEPCODE_ENABLE_CACHING=true
DEEPCODE_PARALLEL_PROCESSING=true
DEEPCODE_MAX_CONCURRENT_TASKS=3

# Output Settings
DEEPCODE_OUTPUT_FORMAT="production_ready"
DEEPCODE_INCLUDE_TESTS=true
DEEPCODE_INCLUDE_DOCUMENTATION=true

# Security Settings
DEEPCODE_ENABLE_SECURITY_ANALYSIS=true
DEEPCODE_CODE_QUALITY_THRESHOLD=0.8
```

### Configuration Files

DeepCode uses YAML configuration files for different scenarios:

- `config/deepcode_examples/paper2code_basic.yaml` - Basic Paper2Code configuration
- `config/deepcode_examples/paper2code_advanced.yaml` - Advanced Paper2Code configuration
- `config/deepcode_examples/text2web_basic.yaml` - Basic Text2Web configuration
- `config/deepcode_examples/text2web_advanced.yaml` - Advanced Text2Web configuration
- `config/deepcode_examples/text2backend_basic.yaml` - Basic Text2Backend configuration
- `config/deepcode_examples/text2backend_advanced.yaml` - Advanced Text2Backend configuration
- `config/deepcode_examples/custom_ml_template.yaml` - ML project template
- `config/deepcode_examples/custom_api_template.yaml` - API project template
- `config/deepcode_examples/performance_optimization.yaml` - Performance optimization settings

## Error Handling

### Common Errors

#### ValidationError
```python
try:
    result = await deepcode.paper2code("")
except ValidationError as e:
    print(f"Validation error: {e.message}")
    print(f"Field: {e.field}")
    print(f"Expected: {e.expected}")
```

#### TaskTimeoutError
```python
try:
    result = await deepcode.get_task_status("task_id")
    await deepcode.wait_for_completion("task_id", timeout=300)
except TaskTimeoutError as e:
    print(f"Task timed out: {e.task_id}")
    print(f"Timeout: {e.timeout} seconds")
```

#### ResourceLimitError
```python
try:
    result = await deepcode.text2web(description, config)
except ResourceLimitError as e:
    print(f"Resource limit exceeded: {e.resource}")
    print(f"Current: {e.current}")
    print(f"Limit: {e.limit}")
```

### Error Response Format

```python
{
    "error": {
        "type": "ValidationError",
        "message": "Paper description cannot be empty",
        "field": "paper_description",
        "code": "EMPTY_DESCRIPTION"
    },
    "task_id": null,
    "status": "failed"
}
```

## Performance Optimization

### Caching

DeepCode supports intelligent caching to improve performance:

```python
config = {
    "enable_caching": True,
    "cache_ttl": 3600,        # Cache TTL in seconds
    "cache_strategy": "smart", # Caching strategy
    "cache_warming": True     # Pre-warm cache
}
```

### Parallel Processing

Enable parallel processing for faster execution:

```python
config = {
    "parallel_processing": True,
    "max_concurrent_tasks": 3,
    "task_scheduler": "priority_based"
}
```

### Resource Management

Configure resource limits and optimization:

```python
config = {
    "memory_optimization": True,
    "cpu_optimization": True,
    "gpu_optimization": True,
    "max_memory_mb": 8192,
    "max_cpu_usage": 0.8
}
```

## WebSocket Events

### Real-time Updates

DeepCode provides WebSocket events for real-time progress updates:

```javascript
// WebSocket connection
const ws = new WebSocket('ws://localhost:8787/deepcode/ws');

// Task progress event
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);

    if (data.type === 'task_progress') {
        console.log(`Progress: ${data.data.progress}%`);
        console.log(`Step: ${data.data.current_step}`);
    }

    if (data.type === 'task_completed') {
        console.log('Task completed!');
        console.log(`Files: ${data.data.generated_files.length}`);
    }
};

// Submit task
ws.send(JSON.stringify({
    type: 'submit_task',
    task_type: 'paper2code',
    content: paper_description,
    config: config
}));
```

### Event Types

- `task_submitted` - Task has been submitted
- `task_progress` - Progress update
- `task_completed` - Task completed successfully
- `task_failed` - Task failed
- `task_cancelled` - Task was cancelled

## Security Considerations

### Input Validation

All inputs are validated and sanitized:

```python
# Automatic input validation
result = await deepcode.paper2code(malicious_input)
# Will raise ValidationError for malicious content
```

### Rate Limiting

API calls are rate limited to prevent abuse:

```python
config = {
    "enable_rate_limiting": True,
    "max_requests_per_minute": 60,
    "max_requests_per_hour": 1000
}
```

### Data Privacy

DeepCode ensures data privacy and security:

- No data persistence beyond task completion
- Secure communication channels
- Input sanitization and validation
- No logging of sensitive information

## Integration Examples

### Basic Integration

```python
import asyncio
from launcher_modules.deepcode.deepcode_integration import DuckBotDeepCodeIntegration

async def main():
    deepcode = DuckBotDeepCodeIntegration()

    # Submit paper2code task
    result = await deepcode.paper2code(
        paper_description="Research paper content...",
        config={"include_tests": True}
    )

    # Wait for completion
    final_status = await deepcode.wait_for_completion(result['task_id'])

    if final_status['status'] == 'completed':
        print("Success!")
        print(f"Generated files: {len(final_status['generated_files'])}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Advanced Integration

```python
import asyncio
from launcher_modules.deepcode.deepcode_integration import DuckBotDeepCodeIntegration

class MyApplication:
    def __init__(self):
        self.deepcode = DuckBotDeepCodeIntegration()
        self.config = {
            "model": "qwen3-coder",
            "temperature": 0.2,
            "include_tests": True,
            "include_documentation": True,
            "enable_caching": True,
            "parallel_processing": True
        }

    async def process_research_paper(self, paper_content):
        """Process research paper and generate code."""
        try:
            result = await self.deepcode.paper2code(
                paper_description=paper_content,
                config=self.config
            )

            # Monitor progress
            while True:
                status = await self.deepcode.get_task_status(result['task_id'])

                if status['status'] == 'completed':
                    return status
                elif status['status'] == 'failed':
                    raise Exception(f"Task failed: {status.get('error')}")

                await asyncio.sleep(2)

        except Exception as e:
            print(f"Error processing paper: {e}")
            return None
```

## Best Practices

### Configuration Management

1. **Use Configuration Files**: Store configurations in YAML files for better management
2. **Environment Variables**: Use environment variables for sensitive data
3. **Validation**: Always validate configuration before use
4. **Default Values**: Provide sensible defaults for all options

### Error Handling

1. **Try-Catch Blocks**: Always wrap API calls in try-catch blocks
2. **Timeout Handling**: Implement timeout handling for long-running tasks
3. **Retry Logic**: Implement retry logic for transient failures
4. **Logging**: Log errors and exceptions for debugging

### Performance

1. **Caching**: Enable caching for repeated operations
2. **Parallel Processing**: Use parallel processing for batch operations
3. **Resource Management**: Monitor and manage resource usage
4. **Optimization**: Use performance optimization features

### Security

1. **Input Validation**: Always validate and sanitize inputs
2. **Rate Limiting**: Implement rate limiting to prevent abuse
3. **Data Privacy**: Ensure data privacy and security
4. **Authentication**: Use authentication and authorization where needed

## Troubleshooting

### Common Issues

#### Task Not Starting
- Check if the DeepCode service is running
- Verify configuration parameters
- Check system resources (memory, CPU)

#### Task Timing Out
- Increase timeout values
- Check for resource constraints
- Enable performance optimization

#### Poor Code Quality
- Adjust temperature and confidence thresholds
- Enable validation and security analysis
- Use advanced configuration options

### Debug Mode

Enable debug mode for detailed logging:

```python
import logging

logging.basicConfig(level=logging.DEBUG)
deepcode = DuckBotDeepCodeIntegration()
```

### Performance Monitoring

Monitor performance metrics:

```python
config = {
    "enable_monitoring": True,
    "enable_profiling": True,
    "enable_metrics": True
}
```

## Version Information

### Current Version: 1.0.0

### Changelog

#### v1.0.0 (2024-01-01)
- Initial release
- Paper2Code functionality
- Text2Web functionality
- Text2Backend functionality
- MCP server integration
- Performance optimization
- Security features

### Dependencies

- Python 3.8+
- FastAPI 0.100.0+
- Pydantic 2.0+
- SQLAlchemy 2.0+
- Redis (optional, for caching)
- PostgreSQL (optional, for database)

### Support

For support and issues:
- GitHub Issues: [DuckBot Repository]
- Documentation: [DeepCode Integration Guide]
- Examples: [DeepCode Usage Examples]

---

This API reference provides comprehensive documentation for the DeepCode integration in DuckBot. For additional information, refer to the integration guide and usage examples.