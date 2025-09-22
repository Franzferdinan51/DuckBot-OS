# DeepCode Usage Examples

This directory contains comprehensive examples demonstrating how to use the DeepCode integration in DuckBot for various scenarios and use cases.

## Directory Structure

```
examples/deepcode_usage/
├── README.md                           # This file
├── command_line_examples.py           # Command line interface examples
├── api_examples.py                    # Programmatic API examples
├── webui_integration.py              # WebUI integration examples
└── config_examples/                   # Configuration examples (if needed)
```

## Example Categories

### 1. Command Line Examples (`command_line_examples.py`)

Demonstrates using DeepCode from the command line interface with various configurations:

- **Paper2Code Basic Example**: Convert research papers to production-ready code
- **Text2Web React Example**: Generate React applications from text descriptions
- **Text2Backend API Example**: Create REST APIs from natural language
- **Batch Processing Example**: Process multiple tasks simultaneously
- **Custom Template Example**: Use custom templates for specialized projects

#### Running Command Line Examples

```bash
# Run all examples
python command_line_examples.py

# Run specific examples (modify the main() function)
python command_line_examples.py
```

### 2. API Examples (`api_examples.py`)

Shows how to integrate DeepCode into other applications using the programmatic API:

- **Basic API Usage**: Simple API calls and error handling
- **Web App Generation**: Complete web application generation
- **Backend API Generation**: REST API and backend system generation
- **MCP Server Usage**: Using MCP (Model Context Protocol) servers
- **Batch Processing**: Automated batch processing workflows
- **Error Handling**: Comprehensive error handling patterns

#### Key Classes

- `DeepCodeAPIClient`: High-level API client for DeepCode
- `DeepCodeMCPClient`: MCP (Model Context Protocol) client

#### Running API Examples

```bash
# Run all API examples
python api_examples.py
```

### 3. WebUI Integration Examples (`webui_integration.py`)

Demonstrates integration with the DuckBot WebUI for seamless user experience:

- **Session Management**: User sessions and task tracking
- **Real-time Updates**: WebSocket-based real-time progress updates
- **File Management**: File preview and download functionality
- **Template Management**: Custom template creation and management
- **User Statistics**: Usage statistics and history tracking

#### Key Classes

- `DeepCodeWebUI`: WebUI integration class
- WebSocket event handlers
- REST API endpoints

#### Running WebUI Examples

```bash
# Run WebUI integration example
python webui_integration.py
```

## Common Usage Patterns

### 1. Basic Paper2Code Workflow

```python
from launcher_modules.deepcode.deepcode_integration import DuckBotDeepCodeIntegration

async def basic_paper2code():
    deepcode = DuckBotDeepCodeIntegration()

    result = await deepcode.paper2code(
        paper_description="Research paper content...",
        config={
            "include_tests": True,
            "include_documentation": True,
            "target_language": "python"
        }
    )

    # Wait for completion
    final_status = await deepcode.wait_for_completion(result['task_id'])

    if final_status['status'] == 'completed':
        print(f"Generated {len(final_status['generated_files'])} files")
```

### 2. Web Application Generation

```python
async def generate_web_app():
    deepcode = DuckBotDeepCodeIntegration()

    result = await deepcode.text2web(
        description="Create a task management app with authentication...",
        config={
            "framework": "react",
            "include_auth": True,
            "include_database": True,
            "backend_framework": "fastapi"
        }
    )

    # Monitor progress
    while True:
        status = await deepcode.get_task_status(result['task_id'])
        print(f"Progress: {status['progress']}%")

        if status['status'] in ['completed', 'failed']:
            break

        await asyncio.sleep(2)
```

### 3. Backend API Generation

```python
async def generate_backend_api():
    deepcode = DuckBotDeepCodeIntegration()

    result = await deepcode.text2backend(
        description="Create a REST API for e-commerce platform...",
        config={
            "framework": "fastapi",
            "include_auth": True,
            "include_database": True,
            "include_docs": True
        }
    )

    # Handle completion
    final_status = await deepcode.wait_for_completion(result['task_id'])
    return final_status
```

### 4. Batch Processing

```python
async def batch_processing():
    deepcode = DuckBotDeepCodeIntegration()

    tasks = [
        ("paper2code", "Research paper on ML...", {"include_tests": True}),
        ("text2web", "Blog application description...", {"framework": "react"}),
        ("text2backend", "User management API...", {"framework": "fastapi"})
    ]

    results = []
    for task_type, content, config in tasks:
        if task_type == "paper2code":
            result = await deepcode.paper2code(content, config)
        elif task_type == "text2web":
            result = await deepcode.text2web(content, config)
        elif task_type == "text2backend":
            result = await deepcode.text2backend(content, config)

        results.append(result)

    # Wait for all tasks to complete
    for result in results:
        await deepcode.wait_for_completion(result['task_id'])

    return results
```

## Configuration Examples

### Basic Configuration

```python
config = {
    "model": "qwen3-coder",
    "temperature": 0.2,
    "max_tokens": 4000,
    "include_tests": True,
    "include_documentation": True
}
```

### Advanced Configuration

```python
config = {
    "model": "qwen3-coder",
    "temperature": 0.2,
    "max_tokens": 8000,
    "confidence_threshold": 0.85,

    # Features
    "include_tests": True,
    "include_documentation": True,
    "include_examples": True,
    "include_error_handling": True,
    "include_type_hints": True,

    # Quality Assurance
    "enable_validation": True,
    "enable_security_analysis": True,
    "code_quality_threshold": 0.9,

    # Performance
    "enable_caching": True,
    "parallel_processing": True,
    "max_concurrent_tasks": 3,

    # Output
    "output_format": "enterprise_ready",
    "target_language": "python",
    "code_style": "enterprise_ready"
}
```

## Error Handling

### Basic Error Handling

```python
try:
    result = await deepcode.paper2code(paper_content, config)
except ValidationError as e:
    print(f"Validation error: {e}")
except TaskTimeoutError as e:
    print(f"Task timed out: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

### Advanced Error Handling

```python
async def safe_paper2code(paper_content, config, timeout=300):
    try:
        result = await deepcode.paper2code(paper_content, config)

        # Wait for completion with timeout
        final_status = await deepcode.wait_for_completion(
            result['task_id'],
            timeout=timeout
        )

        if final_status['status'] == 'completed':
            return final_status
        else:
            raise Exception(f"Task failed: {final_status.get('error')}")

    except ValidationError as e:
        print(f"Input validation failed: {e}")
        return None
    except TaskTimeoutError as e:
        print(f"Task timed out after {timeout} seconds")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None
```

## Performance Optimization

### Enable Caching

```python
config = {
    "enable_caching": True,
    "cache_ttl": 3600,        # 1 hour
    "cache_strategy": "smart"
}
```

### Enable Parallel Processing

```python
config = {
    "parallel_processing": True,
    "max_concurrent_tasks": 3
}
```

### Resource Optimization

```python
config = {
    "memory_optimization": True,
    "cpu_optimization": True,
    "gpu_optimization": True,
    "max_memory_mb": 8192
}
```

## Integration Patterns

### 1. Asynchronous Processing

```python
import asyncio
from launcher_modules.deepcode.deepcode_integration import DuckBotDeepCodeIntegration

class DeepCodeProcessor:
    def __init__(self):
        self.deepcode = DuckBotDeepCodeIntegration()
        self.tasks = {}

    async def submit_task(self, task_type, content, config):
        result = await self.deepcode.paper2code(content, config)
        self.tasks[result['task_id']] = {
            'type': task_type,
            'status': 'submitted',
            'submitted_at': asyncio.get_event_loop().time()
        }
        return result['task_id']

    async def monitor_tasks(self):
        while self.tasks:
            for task_id, task_info in self.tasks.items():
                status = await self.deepcode.get_task_status(task_id)
                task_info.update(status)

                if status['status'] in ['completed', 'failed']:
                    del self.tasks[task_id]

            await asyncio.sleep(5)
```

### 2. Callback-based Processing

```python
class DeepCodeProcessor:
    def __init__(self):
        self.deepcode = DuckBotDeepCodeIntegration()
        self.callbacks = {}

    def register_callback(self, task_id, callback):
        self.callbacks[task_id] = callback

    async def process_with_callback(self, task_type, content, config, callback):
        result = await self.deepcode.paper2code(content, config)
        self.register_callback(result['task_id'], callback)

        # Monitor and call callback
        while True:
            status = await self.deepcode.get_task_status(result['task_id'])
            if status['status'] in ['completed', 'failed']:
                callback(status)
                break
            await asyncio.sleep(2)
```

### 3. Queue-based Processing

```python
import asyncio
from collections import deque

class DeepCodeQueue:
    def __init__(self, max_concurrent=3):
        self.deepcode = DuckBotDeepCodeIntegration()
        self.queue = deque()
        self.active_tasks = {}
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def add_task(self, task_type, content, config):
        task = {
            'type': task_type,
            'content': content,
            'config': config,
            'future': asyncio.Future()
        }
        self.queue.append(task)
        return task['future']

    async def process_queue(self):
        while True:
            if self.queue and len(self.active_tasks) < self.max_concurrent:
                task = self.queue.popleft()
                asyncio.create_task(self._process_task(task))
            await asyncio.sleep(1)

    async def _process_task(self, task):
        async with self.semaphore:
            try:
                if task['type'] == 'paper2code':
                    result = await self.deepcode.paper2code(
                        task['content'],
                        task['config']
                    )

                final_status = await self.deepcode.wait_for_completion(
                    result['task_id']
                )

                task['future'].set_result(final_status)

            except Exception as e:
                task['future'].set_exception(e)
```

## Testing

### Unit Testing

```python
import pytest
from unittest.mock import Mock, patch

class TestDeepCodeIntegration:
    @pytest.fixture
    def deepcode(self):
        from launcher_modules.deepcode.deepcode_integration import DuckBotDeepCodeIntegration
        return DuckBotDeepCodeIntegration()

    @pytest.mark.asyncio
    async def test_paper2code_basic(self, deepcode):
        with patch.object(deepcode, 'paper2code') as mock_method:
            mock_method.return_value = {'task_id': 'test_task', 'status': 'submitted'}

            result = await deepcode.paper2code("test content")

            assert result['task_id'] == 'test_task'
            assert result['status'] == 'submitted'
```

### Integration Testing

```python
@pytest.mark.asyncio
async def test_full_workflow():
    deepcode = DuckBotDeepCodeIntegration()

    # Submit task
    result = await deepcode.paper2code(
        "Test research paper content",
        {"include_tests": True}
    )

    # Wait for completion
    final_status = await deepcode.wait_for_completion(result['task_id'])

    # Verify results
    assert final_status['status'] == 'completed'
    assert len(final_status['generated_files']) > 0
    assert any('test_' in f for f in final_status['generated_files'])
```

## Best Practices

### 1. Configuration Management

- Use configuration files for complex setups
- Validate configuration before use
- Provide sensible defaults
- Use environment variables for sensitive data

### 2. Error Handling

- Always handle potential errors
- Implement retry logic for transient failures
- Log errors appropriately
- Provide meaningful error messages

### 3. Performance

- Enable caching for repeated operations
- Use parallel processing for batch operations
- Monitor resource usage
- Optimize based on use case

### 4. Security

- Validate and sanitize all inputs
- Use appropriate authentication
- Follow least privilege principle
- Monitor for suspicious activity

## Troubleshooting

### Common Issues

1. **Tasks Not Starting**
   - Check if DeepCode service is running
   - Verify configuration parameters
   - Check system resources

2. **Tasks Timing Out**
   - Increase timeout values
   - Check resource constraints
   - Enable performance optimization

3. **Poor Code Quality**
   - Adjust AI model parameters
   - Enable validation features
   - Use advanced configuration

### Debug Mode

```python
import logging

logging.basicConfig(level=logging.DEBUG)
deepcode = DuckBotDeepCodeIntegration()
```

### Performance Monitoring

```python
config = {
    "enable_monitoring": True,
    "enable_profiling": True,
    "enable_metrics": True
}
```

## Contributing

When contributing new examples:

1. **Follow the existing patterns and structure**
2. **Include comprehensive documentation**
3. **Add error handling**
4. **Test your examples thoroughly**
5. **Update this README as needed**

## Support

For support and questions:
- Check the main DeepCode Integration Guide
- Review the API documentation
- Open an issue in the DuckBot repository
- Join the community discussions

---

These examples provide a comprehensive foundation for using DeepCode in various scenarios. Adapt them to your specific needs and requirements.