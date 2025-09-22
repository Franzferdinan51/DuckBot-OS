# DuckBot v4.2 Developer Contribution Guidelines

## Table of Contents
- [Getting Started](#getting-started)
- [Development Environment Setup](#development-environment-setup)
- [Code Style and Quality](#code-style-and-quality)
- [Testing Guidelines](#testing-guidelines)
- [Pull Request Process](#pull-request-process)
- [Code Review Process](#code-review-process)
- [Release Process](#release-process)
- [Documentation Standards](#documentation-standards)
- [Issue Reporting](#issue-reporting)
- [Feature Requests](#feature-requests)

## Getting Started

### Prerequisites

Before contributing to DuckBot, ensure you have the following:

- **Python 3.8+** (3.11+ recommended)
- **Git** installed and configured
- **GitHub account** with proper setup
- **Development environment** with IDE/Editor
- **Basic understanding** of async/await patterns
- **Familiarity** with FastAPI, asyncio, and web development

### Fork and Clone

1. **Fork the repository**
   ```bash
   # Navigate to https://github.com/your-username/DuckBot-Consolidated-v4.2
   # Click "Fork" button
   ```

2. **Clone your fork**
   ```bash
   git clone https://github.com/your-username/DuckBot-Consolidated-v4.2.git
   cd DuckBot-Consolidated-v4.2
   ```

3. **Add upstream remote**
   ```bash
   git remote add upstream https://github.com/original-username/DuckBot-Consolidated-v4.2.git
   ```

### Development Branch

1. **Create a feature branch**
   ```bash
   # Create new branch from main/master
   git checkout -b feature/your-feature-name main
   ```

2. **Keep your branch updated**
   ```bash
   # Sync with upstream
   git fetch upstream
   git merge upstream/main
   ```

## Development Environment Setup

### 1. Python Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r docs/requirements.txt

# Install development dependencies
pip install -r docs/requirements-dev.txt
```

### 2. Pre-commit Hooks

```bash
# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Run pre-commit manually
pre-commit run --all-files
```

### 3. Development Tools

```bash
# Install code formatting tools
pip install black isort ruff

# Install type checking tools
pip install mypy

# Install testing tools
pip install pytest pytest-asyncio pytest-cov
```

### 4. IDE Configuration

#### VS Code Setup

```json
// .vscode/settings.json
{
    "python.defaultInterpreterPath": "./venv/Scripts/python.exe",
    "python.linting.enabled": true,
    "python.linting.mypyEnabled": true,
    "python.formatting.provider": "black",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.fixAll": true
    },
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": [
        "tests"
    ]
}
```

#### PyCharm Setup

1. **Open project in PyCharm**
2. **Configure Python interpreter** to use venv
3. **Enable pytest** in Settings → Tools → Python Integrated Tools
4. **Configure code inspection** to use mypy and flake8

## Code Style and Quality

### 1. Python Code Style

Follow PEP 8 with the following exceptions:

```python
# Good
async def process_request(request: Request) -> Response:
    """Process incoming request."""
    try:
        data = await request.json()
        result = await handle_data(data)
        return Response(result)
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        raise
```

### 2. Type Hints

Use type hints for all functions and methods:

```python
from typing import Dict, List, Optional, Union
from datetime import datetime

class User:
    def __init__(self, user_id: str, name: str, email: str):
        self.user_id = user_id
        self.name = name
        self.email = email

    async def get_preferences(self) -> Dict[str, Union[str, bool]]:
        """Get user preferences."""
        return {"theme": "dark", "notifications": True}
```

### 3. Docstrings

Use Google-style docstrings:

```python
def calculate_fibonacci(n: int) -> int:
    """Calculate the nth Fibonacci number.

    Args:
        n: The position in the Fibonacci sequence (1-based).

    Returns:
        The nth Fibonacci number.

    Raises:
        ValueError: If n is less than 1.
    """
    if n < 1:
        raise ValueError("n must be greater than or equal to 1")

    if n <= 2:
        return 1

    return calculate_fibonacci(n - 1) + calculate_fibonacci(n - 2)
```

### 4. Error Handling

```python
# Good error handling
async def process_file(file_path: str) -> Dict[str, Any]:
    """Process a file and return structured data."""
    try:
        async with aiofiles.open(file_path, 'r') as f:
            content = await f.read()

        data = json.loads(content)
        return await validate_and_process(data)

    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        raise FileProcessingError(f"File not found: {file_path}")

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in file {file_path}: {e}")
        raise FileProcessingError(f"Invalid JSON format: {e}")

    except Exception as e:
        logger.error(f"Unexpected error processing file {file_path}: {e}")
        raise FileProcessingError(f"Processing failed: {e}")
```

### 5. Async/Await Patterns

```python
# Good async patterns
class DataProcessor:
    def __init__(self):
        self.queue = asyncio.Queue()
        self.processing = False

    async def start_processing(self):
        """Start processing data from queue."""
        self.processing = True
        while self.processing:
            try:
                data = await asyncio.wait_for(
                    self.queue.get(),
                    timeout=1.0
                )
                await self.process_data(data)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error processing data: {e}")

    async def process_data(self, data: Dict[str, Any]):
        """Process individual data item."""
        # Implement data processing logic
        pass
```

## Testing Guidelines

### 1. Test Structure

```
tests/
├── unit/
│   ├── test_core_modules.py
│   ├── test_integrations.py
│   └── test_services.py
├── integration/
│   ├── test_api_endpoints.py
│   ├── test_workflows.py
│   └── test_agent_coordination.py
├── performance/
│   ├── test_load.py
│   ├── test_memory.py
│   └── test_concurrency.py
└── fixtures/
    ├── test_data.json
    ├── mock_responses.py
    └── test_config.yaml
```

### 2. Unit Tests

```python
# Example unit test
import pytest
from unittest.mock import AsyncMock, MagicMock
from duckbot.core.ai_provider_manager import AIProviderManager

class TestAIProviderManager:
    @pytest.fixture
    def ai_manager(self):
        return AIProviderManager()

    @pytest.mark.asyncio
    async def test_route_request_success(self, ai_manager):
        """Test successful request routing."""
        # Setup
        ai_manager.router = AsyncMock()
        ai_manager.router.route_request.return_value = "Mock response"

        # Test
        result = await ai_manager.route_request(
            prompt="Test prompt",
            task_type="test"
        )

        # Assert
        assert result == "Mock response"
        ai_manager.router.route_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_route_request_failure(self, ai_manager):
        """Test request routing failure."""
        # Setup
        ai_manager.router = AsyncMock()
        ai_manager.router.route_request.side_effect = Exception("Route failed")

        # Test & Assert
        with pytest.raises(Exception, match="Route failed"):
            await ai_manager.route_request(
                prompt="Test prompt",
                task_type="test"
            )
```

### 3. Integration Tests

```python
# Example integration test
import pytest
import aiohttp
from duckbot.enhanced_webui import EnhancedWebUI

class TestWebUIIntegration:
    @pytest.fixture
    async def webui_app(self):
        """Create test WebUI application."""
        webui = EnhancedWebUI()
        app = await webui.create_app()
        yield app
        await webui.stop()

    @pytest.mark.asyncio
    async def test_health_endpoint(self, webui_app):
        """Test health check endpoint."""
        async with aiohttp.test_client.TestClient(webui_app) as client:
            response = await client.get("/health")
            assert response.status == 200
            data = await response.json()
            assert data["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_chat_endpoint(self, webui_app):
        """Test chat endpoint."""
        async with aiohttp.test_client.TestClient(webui_app) as client:
            response = await client.post(
                "/api/v1/chat",
                json={
                    "message": "Hello",
                    "model": "test"
                }
            )
            assert response.status == 200
            data = await response.json()
            assert "response" in data
```

### 4. Performance Tests

```python
# Example performance test
import pytest
import asyncio
import time
from duckbot.core.rate_limit import RateLimiter

class TestRateLimiterPerformance:
    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """Test rate limiter under concurrent load."""
        limiter = RateLimiter()

        async def make_request(request_id):
            return await limiter.check_rate_limit(f"user_{request_id}", 10, 60)

        # Test 100 concurrent requests
        tasks = [make_request(i) for i in range(100)]
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        duration = time.time() - start_time

        assert duration < 1.0  # Should complete in under 1 second
        assert all(results)  # All requests should be within limits
```

### 5. Test Coverage

```bash
# Run tests with coverage
pytest --cov=duckbot --cov-report=html --cov-report=term-missing

# Generate coverage report
coverage html
```

### 6. Test Data

```python
# tests/fixtures/test_data.py
import pytest
from typing import Dict, Any

@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "user_id": "test_user_123",
        "name": "Test User",
        "email": "test@example.com",
        "preferences": {
            "theme": "dark",
            "language": "en",
            "notifications": True
        }
    }

@pytest.fixture
def sample_ai_response():
    """Sample AI response for testing."""
    return {
        "response": "This is a test response",
        "model": "test-model",
        "tokens_used": 25,
        "confidence": 0.95
    }
```

## Pull Request Process

### 1. PR Checklist

Before submitting a pull request, ensure:

- [ ] **Code follows style guidelines** (black, isort, mypy)
- [ ] **All tests pass** locally and in CI
- [ ] **Test coverage is maintained or improved**
- [ ] **Documentation is updated** if necessary
- [ ] **Changelog is updated** for new features
- [ ] **Performance impact is considered**
- [ ] **Security implications are reviewed**
- [ ] **Breaking changes are documented**

### 2. PR Template

```markdown
## Pull Request Description

### Summary
Brief description of changes made.

### Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

### Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing performed
- [ ] Performance testing performed

### Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review of code completed
- [ ] Documentation updated if necessary
- [ ] No breaking changes (or breaking changes documented)
- [ ] All tests passing

### Related Issues
Closes #123
Related to #456
```

### 3. PR Submission

```bash
# Commit changes
git add .
git commit -m "feat: add new feature description

- Add feature X
- Improve performance of Y
- Fix bug in Z

Closes #123"

# Push to your fork
git push origin feature/your-feature-name

# Create PR via GitHub
# Or use GitHub CLI
gh pr create --title "Add new feature" --body "PR description"
```

## Code Review Process

### 1. Review Guidelines

When reviewing code, check:

- **Functionality**: Does the code work as intended?
- **Performance**: Is the code efficient and scalable?
- **Security**: Are there any security vulnerabilities?
- **Maintainability**: Is the code easy to understand and maintain?
- **Testing**: Are tests comprehensive and appropriate?
- **Documentation**: Is the code well-documented?
- **Error Handling**: Are edge cases properly handled?

### 2. Review Comments

```markdown
## Code Review Comments

### Positive Feedback
- ✅ Good implementation of async patterns
- ✅ Comprehensive test coverage
- ✅ Clear documentation

### Suggestions for Improvement
- 💡 Consider using `asyncio.gather()` for concurrent operations
- 💡 Add more detailed error handling for network failures
- 💡 Consider adding performance metrics

### Required Changes
- 🔧 Fix the type hint on line 45
- 🔧 Add unit test for edge case scenario
- 🔧 Update import statement to use absolute path
```

### 3. Review Process

1. **Self-review** the code before submission
2. **Automated checks** run in CI pipeline
3. **Peer review** by at least one maintainer
4. **Final review** by project lead
5. **Merge** when all requirements are met

## Release Process

### 1. Version Management

DuckBot follows Semantic Versioning (SemVer):

- **Major version**: Breaking changes
- **Minor version**: New features (backward compatible)
- **Patch version**: Bug fixes (backward compatible)

### 2. Release Checklist

```bash
# Update version numbers
# duckbot/__init__.py
__version__ = "4.2.1"

# Update changelog
# CHANGELOG.md
## [4.2.1] - 2024-01-15
### Fixed
- Fixed memory leak in AI provider manager
- Fixed race condition in service manager
- Fixed type hints in core modules

### Updated documentation
- Updated API reference for new endpoints
- Added troubleshooting guide

# Create release
git tag -a v4.2.1 -m "Release v4.2.1"
git push origin v4.2.1

# Build and publish
python setup.py sdist bdist_wheel
twine upload dist/*
```

### 3. Release Announcement

```markdown
## DuckBot v4.2.1 Released

### What's New
- Improved performance and stability
- Fixed critical bugs
- Updated documentation

### Installation
```bash
pip install duckbot==4.2.1
```

### Upgrade
```bash
pip install --upgrade duckbot==4.2.1
```

### Documentation
- [Release Notes](https://docs.duckbot.com/releases/v4.2.1)
- [Migration Guide](https://docs.duckbot.com/migration/v4.2.1)
```

## Documentation Standards

### 1. Code Documentation

```python
# Module docstring
"""
DuckBot Core AI Provider Manager

This module provides unified management of AI providers including:
- Local model management
- Cloud API integration
- Dynamic routing and fallback
- Cost tracking and optimization
"""

# Class docstring
class AIProviderManager:
    """Manages AI provider connections and request routing.

    This class provides a unified interface for interacting with multiple
    AI providers, including local models and cloud APIs. It handles:
    - Provider registration and configuration
    - Request routing and load balancing
    - Error handling and fallback mechanisms
    - Performance monitoring and optimization

    Attributes:
        providers (Dict[str, BaseAIProvider]): Registered AI providers
        router (AIRouter): Request routing logic
        cache (ResponseCache): Response caching system
    """

    def __init__(self):
        """Initialize the AI provider manager."""
        pass
```

### 2. API Documentation

```markdown
## API Reference

### `AIProviderManager.route_request()`

Route AI request to appropriate provider.

**Parameters:**
- `prompt` (str): User prompt/question
- `task_type` (str): Type of task (code, reasoning, creative, etc.)
- `**kwargs`: Additional parameters

**Returns:**
- `str`: AI response

**Raises:**
- `ValueError`: If prompt is empty or invalid
- `ProviderError`: If no suitable provider is available

**Example:**
```python
response = await ai_manager.route_request(
    prompt="Write a Python function",
    task_type="code",
    model="qwen3-coder"
)
```
```

### 3. README Documentation

```markdown
# DuckBot v4.2

[![Build Status](https://img.shields.io/github/workflow/status/username/DuckBot/CI.svg)](https://github.com/username/DuckBot/actions)
[![Coverage](https://img.shields.io/codecov/c/github/username/DuckBot.svg)](https://codecov.io/gh/username/DuckBot)
[![PyPI](https://img.shields.io/pypi/v/duckbot.svg)](https://pypi.org/project/duckbot/)
[![Python](https://img.shields.io/pypi/pyversions/duckbot.svg)](https://pypi.org/project/duckbot/)

DuckBot is an AI-powered operating system with desktop automation, multi-agent coordination, and cross-platform integration.

## Features

- 🤖 **Multi-Agent Framework**: Specialized AI agents for different tasks
- 🖥️ **Desktop Automation**: Natural language control of Windows applications
- 💾 **Memory & Learning**: Persistent conversation memory and adaptation
- 🌐 **Cross-Platform**: Windows, WSL, and Docker integration
- 🔒 **Privacy-First**: Complete local-only mode available
```

## Issue Reporting

### 1. Bug Report Template

```markdown
## Bug Report

### Environment
- **DuckBot Version**: 4.2.0
- **Python Version**: 3.11.0
- **Operating System**: Windows 11
- **LM Studio Version**: 0.2.15 (if applicable)

### Bug Description
A clear and concise description of the bug.

### Steps to Reproduce
1. Start DuckBot with `START_ENHANCED_DUCKBOT.bat`
2. Navigate to WebUI at http://localhost:8787
3. Send message "Hello, how are you?"
4. System crashes with error message

### Expected Behavior
The system should respond with a greeting message.

### Actual Behavior
System crashes with the following error:
```
Traceback (most recent call last):
  File "duckbot/enhanced_webui.py", line 123, in handle_chat
    response = await ai_manager.route_request(...)
ValueError: Invalid response format
```

### Additional Context
- This only happens when using local models
- Works fine with cloud providers
- Error occurs approximately 50% of the time
```

### 2. Feature Request Template

```markdown
## Feature Request

### Summary
Add support for custom AI model providers

### Problem Statement
Currently, DuckBot only supports a limited set of AI providers. Users want to integrate their own custom AI models and APIs.

### Proposed Solution
1. Create a plugin system for AI providers
2. Provide base classes for custom provider implementation
3. Add configuration options for custom providers
4. Include examples and documentation

### Alternatives Considered
- Manual modification of core code (not maintainable)
- External proxy service (adds complexity)

### Additional Context
- Would enable integration with custom fine-tuned models
- Useful for enterprise deployments with proprietary models
- Should maintain backward compatibility
```

### 3. Performance Issue Template

```markdown
## Performance Issue

### Environment
- **DuckBot Version**: 4.2.0
- **Hardware**: 16GB RAM, RTX 3060 8GB
- **Python Version**: 3.11.0
- **Operating System**: Windows 11

### Performance Problem
The system becomes slow when multiple agents are running simultaneously.

### Metrics
- Memory usage increases from 2GB to 12GB within 10 minutes
- CPU usage spikes to 100% during model loading
- Response time increases from 1s to 30s

### Steps to Reproduce
1. Start 3 different agents
2. Assign tasks to all agents
3. Monitor system performance

### Expected Behavior
- Memory usage should remain under 8GB
- CPU usage should not exceed 80%
- Response time should stay under 5s
```

## Community Guidelines

### 1. Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help newcomers and answer questions
- Follow project standards and guidelines
- Report security issues privately

### 2. Communication Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and discussions
- **Discord Server**: Real-time chat and community support
- **Documentation**: Official guides and references

### 3. Contributing Levels

- **First-time Contributors**: Start with good first issues
- **Regular Contributors**: Work on feature enhancements
- **Maintainers**: Review code and manage releases
- **Core Team**: Architectural decisions and project direction

## Getting Help

### 1. Documentation

- [User Guide](../user-guides/)
- [API Reference](../api-references/)
- [Developer Guide](./)
- [Troubleshooting](../troubleshooting/)

### 2. Community Support

- [GitHub Discussions](https://github.com/username/DuckBot/discussions)
- [Discord Server](https://discord.gg/duckbot)
- [Stack Overflow](https://stackoverflow.com/questions/tagged/duckbot)

### 3. Contact Maintainers

For urgent issues or security concerns:
- Email: security@duckbot.com
- Create a private GitHub issue with "Security" label

---

Thank you for contributing to DuckBot! Your help makes this project better for everyone.