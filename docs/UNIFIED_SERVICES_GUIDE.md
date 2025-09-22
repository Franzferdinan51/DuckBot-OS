# DuckBot Unified Services Integration Guide

## Overview

This guide provides comprehensive instructions for setting up and using the unified ComfyUI, TRELLIS, and VibeVoice integration in DuckBot Enhanced v4.2.

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Service Setup](#service-setup)
5. [Usage](#usage)
6. [API Reference](#api-reference)
7. [WebUI Dashboard](#webui-dashboard)
8. [Troubleshooting](#troubleshooting)
9. [Advanced Features](#advanced-features)

## System Requirements

### Minimum Requirements
- **OS**: Windows 10/11 or Linux with WSL2
- **Python**: 3.8+ (3.11+ recommended)
- **RAM**: 8GB minimum (16GB+ recommended)
- **Storage**: 20GB free space
- **GPU**: NVIDIA GPU with 4GB+ VRAM (recommended for ComfyUI/TRELLIS)

### Software Dependencies
- Git
- Node.js (for WebUI components)
- CUDA Toolkit (for GPU acceleration)
- Docker (optional, for containerized deployment)

## Installation

### 1. Clone and Setup Repository

```bash
git clone <repository-url>
cd DuckBot-Consolidated-v4.2
pip install -r requirements.txt
```

### 2. Install Service Dependencies

#### ComfyUI Dependencies
```bash
# Install PyTorch with CUDA support
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Install ComfyUI (if not already installed)
git clone https://github.com/comfyanonymous/ComfyUI.git C:/ComfyUI
cd C:/ComfyUI
pip install -r requirements.txt
```

#### TRELLIS Dependencies
```bash
# Install 3D processing libraries
pip install trimesh open3d pymeshlab

# Install TRELLIS (if available)
# Note: TRELLIS installation may vary based on availability
git clone https://github.com/Microsoft/TRELLIS.git C:/TRELLIS
cd C:/TRELLIS
pip install -r requirements.txt
```

#### VibeVoice Dependencies
```bash
# Install audio processing libraries
pip install soundfile librosa pydub

# Install FastAPI for VibeVoice server
pip install fastapi uvicorn aiofiles
```

### 3. Install DuckBot Unified Services

```bash
# Install the unified services
pip install -e .

# Or install in development mode
cd duckbot
pip install -e .
```

## Configuration

### 1. Configuration File

The main configuration file is located at `config/unified_services_config.json`:

```json
{
  "comfyui": {
    "path": "C:/ComfyUI",
    "api_url": "http://localhost:8188",
    "enabled": true,
    "auto_start": true,
    "gpu_memory_limit": 0.8,
    "max_concurrent_workflows": 3
  },
  "trellis": {
    "path": "C:/TRELLIS",
    "api_url": "http://localhost:8288",
    "enabled": true,
    "auto_start": true,
    "max_concurrent_generations": 2
  },
  "vibevoice": {
    "api_url": "http://localhost:8000",
    "enabled": true,
    "auto_start": true,
    "batch_processing": true
  }
}
```

### 2. Environment Variables

Create or update `.env` file:

```env
# Unified Services Configuration
ENABLE_COMFYUI=true
ENABLE_TRELLIS=true
ENABLE_VIBEVOICE=true
UNIFIED_CONFIG_PATH=config/unified_services_config.json

# Service Ports
COMFYUI_PORT=8188
TRELLIS_PORT=8288
VIBEVOICE_PORT=8000
WEBUI_PORT=8787

# Resource Management
GPU_MEMORY_LIMIT=0.8
MAX_CONCURRENT_WORKFLOWS=3
MAX_CONCURRENT_3D_GENERATIONS=2

# Security (Optional)
API_KEY_REQUIRED=false
CORS_ENABLED=true
RATE_LIMITING_ENABLED=false
```

## Service Setup

### 1. ComfyUI Setup

#### Manual Setup
```bash
# Navigate to ComfyUI directory
cd C:/ComfyUI

# Start ComfyUI server
python main.py --port 8188 --listen 127.0.0.1
```

#### Automatic Setup (via DuckBot)
```bash
# Use DuckBot to manage ComfyUI
python start_unified_services.py --mode background
```

#### Verification
```bash
# Check ComfyUI status
curl http://localhost:8188/system_stats
```

### 2. TRELLIS Setup

#### Manual Setup
```bash
# Navigate to TRELLIS directory
cd C:/TRELLIS

# Start TRELLIS server
python app.py --port 8288 --host 127.0.0.1
```

#### Automatic Setup (via DuckBot)
```bash
# TRELLIS will be managed by DuckBot unified services
python start_unified_services.py
```

#### Verification
```bash
# Check TRELLIS status
curl http://localhost:8288/health
```

### 3. VibeVoice Setup

#### Manual Setup
```bash
# Navigate to VibeVoice directory (if separate)
cd /path/to/vibevoice

# Start VibeVoice server
python server.py --port 8000
```

#### Automatic Setup (via DuckBot)
```bash
# VibeVoice will be managed by DuckBot unified services
python start_unified_services.py
```

#### Verification
```bash
# Check VibeVoice status
curl http://localhost:8000/voices
```

## Usage

### 1. Starting Services

#### Background Mode (Recommended)
```bash
# Start all services in background with WebUI
python start_unified_services.py --mode background
```

#### Foreground Mode
```bash
# Start services with console output
python start_unified_services.py --mode foreground
```

#### Custom Configuration
```bash
# Use custom configuration file
python start_unified_services.py --config path/to/config.json
```

### 2. WebUI Dashboard

Access the unified services dashboard at:
```
http://localhost:8787/api/unified/dashboard
```

The dashboard provides:
- Real-time service status monitoring
- Service management controls
- Performance metrics
- Configuration management
- Cross-service workflow creation

### 3. API Usage

#### ComfyUI Workflow Execution
```bash
curl -X POST http://localhost:8787/api/unified/comfyui/execute \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_type": "text_to_image",
    "parameters": {
      "prompt": "A beautiful landscape",
      "seed": 42
    }
  }'
```

#### TRELLIS 3D Asset Generation
```bash
curl -X POST http://localhost:8787/api/unified/trellis/generate \
  -H "Content-Type: application/json" \
  -d '{
    "asset_type": "text_to_3d",
    "parameters": {
      "text_prompt": "A modern chair",
      "resolution": 512
    },
    "output_format": "gaussians"
  }'
```

#### VibeVoice Speech Generation
```bash
curl -X POST http://localhost:8787/api/unified/vibevoice/generate \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Hello, this is a test message",
    "speakers": ["en-alice"],
    "style": "conversational"
  }'
```

#### Multimodal Workflow Creation
```bash
curl -X POST http://localhost:8787/api/unified/multimodal-workflow \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Create a story with images and narration",
    "requirements": {
      "style": "educational",
      "include_images": true,
      "include_3d": false,
      "include_audio": true
    }
  }'
```

### 4. Python API Usage

```python
import asyncio
from duckbot.integrations.unified_service_manager import unified_service_manager

async def example_usage():
    # Initialize services
    await unified_service_manager.initialize_all()

    # Generate image with ComfyUI
    image_result = await unified_service_manager.execute_comfyui_workflow(
        workflow_type="text_to_image",
        parameters={"prompt": "A beautiful sunset"}
    )

    # Generate 3D asset with TRELLIS
    asset_result = await unified_service_manager.generate_3d_asset(
        asset_type="text_to_3d",
        parameters={"text_prompt": "A simple cube"},
        output_format="gaussians"
    )

    # Generate speech with VibeVoice
    voice_result = await unified_service_manager.generate_voice_content(
        content="Hello from DuckBot unified services!",
        speakers=["en-alice"]
    )

    # Create multimodal workflow
    workflow_result = await unified_service_manager.create_multimodal_workflow(
        description="Create educational content about space",
        requirements={"style": "educational"}
    )

    return {
        "image": image_result,
        "asset": asset_result,
        "voice": voice_result,
        "workflow": workflow_result
    }

# Run the example
result = asyncio.run(example_usage())
print(result)
```

## API Reference

### Unified Services API

#### GET /api/unified/status
Get unified status of all services

**Response:**
```json
{
  "services": {
    "comfyui": {
      "initialized": true,
      "healthy": true,
      "available_workflows": [...]
    },
    "trellis": {
      "initialized": true,
      "healthy": true,
      "available_asset_types": [...]
    },
    "vibevoice": {
      "initialized": true,
      "healthy": true,
      "available_voices": [...]
    }
  },
  "performance": {
    "total_requests": 100,
    "successful_requests": 95,
    "failed_requests": 5
  }
}
```

#### POST /api/unified/comfyui/execute
Execute ComfyUI workflow

**Parameters:**
- `workflow_type` (string): Type of workflow to execute
- `parameters` (object): Workflow parameters
- `output_dir` (string, optional): Output directory

#### POST /api/unified/trellis/generate
Generate 3D asset with TRELLIS

**Parameters:**
- `asset_type` (string): Type of asset to generate
- `parameters` (object): Generation parameters
- `output_format` (string): Output format (gaussians, meshes, radiance_fields)

#### POST /api/unified/vibevoice/generate
Generate speech with VibeVoice

**Parameters:**
- `content` (string): Text to convert to speech
- `speakers` (array, optional): Speaker voices
- `style` (string): Voice style

#### POST /api/unified/multimodal-workflow
Create cross-service workflow

**Parameters:**
- `description` (string): Workflow description
- `requirements` (object): Workflow requirements

## WebUI Dashboard

### Dashboard Features

#### Service Status Cards
- Real-time health monitoring
- Service availability indicators
- Quick access to service management

#### Performance Monitoring
- Request count and success rate
- Average response time tracking
- Resource usage monitoring

#### Service Management
- Start/stop individual services
- Configuration management
- Log viewing and debugging

#### Workflow Management
- Create multimodal workflows
- Monitor workflow execution
- View workflow history and results

### Dashboard Sections

1. **Service Overview**: Status cards for all three services
2. **Performance Metrics**: Charts and statistics
3. **Multimodal Workflows**: Cross-service workflow creation
4. **Service Controls**: Individual service management
5. **Configuration**: Global and per-service settings

## Troubleshooting

### Common Issues

#### 1. Services Not Starting
**Symptoms**: Services show as offline in dashboard

**Solutions:**
- Check service installation paths in configuration
- Verify required dependencies are installed
- Check port availability (8188, 8288, 8000)
- Review service logs for errors

#### 2. GPU Memory Issues
**Symptoms**: ComfyUI/TRELLIS workflows failing with memory errors

**Solutions:**
- Reduce `gpu_memory_limit` in configuration
- Close other GPU-intensive applications
- Reduce workflow complexity/batch size
- Consider CPU-only mode if GPU unavailable

#### 3. API Timeouts
**Symptoms**: API requests timing out

**Solutions:**
- Increase timeout values in client code
- Check service health and restart if needed
- Reduce request complexity
- Verify network connectivity

#### 4. VibeVoice Not Generating Audio
**Symptoms**: Voice generation fails or produces no output

**Solutions:**
- Verify VibeVoice server is running
- Check API endpoint connectivity
- Validate text format and speaker selection
- Review VibeVoice server logs

### Debug Commands

#### Check Service Status
```bash
curl http://localhost:8787/api/unified/status
```

#### Test Individual Services
```bash
# ComfyUI
curl http://localhost:8188/system_stats

# TRELLIS
curl http://localhost:8288/health

# VibeVoice
curl http://localhost:8000/voices
```

#### View Logs
```bash
# DuckBot logs
tail -f logs/duckbot.log

# ComfyUI logs (if running separately)
tail -f C:/ComfyUI/comfyui.log

# System resource usage
nvidia-smi  # GPU usage
htop        # System usage
```

### Performance Optimization

#### GPU Memory Management
```json
{
  "comfyui": {
    "gpu_memory_limit": 0.7,
    "max_concurrent_workflows": 2
  },
  "trellis": {
    "max_concurrent_generations": 1
  }
}
```

#### Response Time Optimization
```json
{
  "unified": {
    "health_check_interval": 60,
    "resource_monitoring": true,
    "auto_restart_services": false
  }
}
```

## Advanced Features

### 1. Custom Workflow Templates

Add custom ComfyUI workflow templates:

```python
# In duckbot/integrations/comfyui_integration.py
def _get_custom_workflow(self):
    return {
        "1": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": "your-custom-model.ckpt"}
        },
        # Add your custom workflow nodes
    }
```

### 2. Cross-Service Pipelines

Create complex workflows combining multiple services:

```python
async def advanced_content_creation():
    # Generate concept image
    concept_image = await unified_service_manager.execute_comfyui_workflow(
        "text_to_image",
        {"prompt": "Futuristic cityscape"}
    )

    # Convert to 3D model
    city_model = await unified_service_manager.generate_3d_asset(
        "image_to_3d",
        {"input_image": concept_image["output_files"][0]}
    )

    # Generate narration
    narration = await unified_service_manager.generate_voice_content(
        "Welcome to the city of tomorrow...",
        ["en-carter"],
        "narrative"
    )

    return {
        "concept": concept_image,
        "model": city_model,
        "narration": narration
    }
```

### 3. Batch Processing

Process multiple items efficiently:

```python
async def batch_image_generation(prompts):
    tasks = []
    for prompt in prompts:
        task = unified_service_manager.execute_comfyui_workflow(
            "text_to_image",
            {"prompt": prompt}
        )
        tasks.append(task)

    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results
```

### 4. Service Health Monitoring

Implement custom health checks:

```python
async def custom_health_check():
    status = await unified_service_manager.get_unified_status()

    # Check custom metrics
    for service_name, service_data in status["services"].items():
        if not service_data["healthy"]:
            # Implement custom alerting
            await send_alert(f"{service_name} is unhealthy")

    return status
```

## Security Considerations

### 1. API Security
- Set `API_KEY_REQUIRED=true` in production
- Implement proper authentication
- Use HTTPS in production environments
- Validate all input parameters

### 2. Resource Management
- Monitor memory and CPU usage
- Implement request rate limiting
- Set reasonable concurrency limits
- Clean up temporary files regularly

### 3. Network Security
- Firewall service ports appropriately
- Use CORS restrictions
- Implement proper logging
- Monitor for suspicious activity

## Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

### Testing
Run the comprehensive test suite:

```bash
python tests/test_unified_services.py
```

### Code Style
- Follow PEP 8 guidelines
- Use type hints where appropriate
- Add comprehensive docstrings
- Include error handling for all operations

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the GitHub issues
3. Check service logs
4. Contact the development team

---

This guide provides comprehensive information for setting up and using the DuckBot Unified Services integration. For the most up-to-date information, please refer to the GitHub repository and official documentation.