# DuckBot Hugging Face Model Downloader

A comprehensive model downloading system for DuckBot's training infrastructure, providing robust Hugging Face model downloading with authentication, format conversion, caching, and validation.

## Features

### Core Functionality
- **Robust Model Downloading**: Reliable downloading from Hugging Face Hub with resume support
- **Authentication Support**: Full support for private models and API tokens
- **Format Conversion**: Automatic conversion from Hugging Face to GGUF format
- **Progress Tracking**: Real-time download progress with speed and ETA calculations
- **Model Validation**: Comprehensive integrity and compatibility checking
- **Intelligent Caching**: Smart caching system with metadata management
- **Training Integration**: Seamless integration with existing training infrastructure

### Advanced Features
- **Download Queue**: Priority-based download queue management
- **Model Statistics**: Comprehensive statistics and reporting
- **Format Support**: Multiple model formats (Hugging Face, GGUF, GGML, SafeTensors)
- **Quantization Options**: Support for various quantization levels
- **Checksum Verification**: SHA256 checksum verification for integrity
- **Model Compatibility**: Training-specific compatibility checking
- **Automatic Cleanup**: Configurable cache cleanup and model management

## Installation

### Requirements
```bash
pip install huggingface_hub transformers torch safetensors pydantic
```

### Optional Dependencies
```bash
# For GGUF conversion
pip install sentencepiece

# llama.cpp for conversion (install separately)
# Follow: https://github.com/ggerganov/llama.cpp
```

## Quick Start

### Basic Usage

```python
from huggingface_downloader import ModelDownloader, ModelDownloadConfig

# Create downloader
downloader = ModelDownloader()

# Download a model
config = ModelDownloadConfig(
    model_id="facebook/opt-125m",
    convert_to_gguf=True,
    gguf_quantization="q4_0"
)

def progress_callback(info):
    print(f"Progress: {info}")

model_path = downloader.download_model("facebook/opt-125m", config, progress_callback)
print(f"Model downloaded to: {model_path}")
```

### Training Integration

```python
from training_integration import TrainingModelManager

# Create training model manager
manager = TrainingModelManager()

# Download model for training
def download_callback(info):
    print(f"Download status: {info['status']}")

manager.download_model_for_training(
    "bert-base-uncased",
    callback=download_callback
)

# List available models
models = manager.get_available_models()
for model in models:
    print(f"{model['model_id']} - {model['size_mb']} MB")

# Get model path for training
model_path = manager.get_model_path("bert-base-uncased")
if model_path:
    # Use model_path in training
    pass
```

## Configuration

### Configuration File
Create a `config/downloader_config.json` file:

```json
{
  "huggingface": {
    "token": null,
    "endpoint": null,
    "max_workers": 4,
    "timeout": 300,
    "retry_attempts": 3
  },
  "download": {
    "chunk_size": 1048576,
    "max_retries": 3,
    "retry_delay": 1.0,
    "resume_download": true,
    "force_download": false
  },
  "cache": {
    "default_dir": "~/.cache/duckbot_models",
    "max_cache_size_gb": 100,
    "cache_cleanup_days": 30
  },
  "conversion": {
    "convert_to_gguf": false,
    "default_quantization": "q4_0",
    "llama_cpp_path": null
  },
  "validation": {
    "validate_checksums": true,
    "validate_structure": true,
    "skip_files_on_error": false,
    "test_model_loading": false
  },
  "security": {
    "token_env_var": "HUGGINGFACE_TOKEN",
    "allow_private_models": true,
    "verify_ssl": true
  }
}
```

### Environment Variables
```bash
# Hugging Face authentication
export HUGGINGFACE_TOKEN="your_token_here"

# Cache directory (optional)
export DUCKBOT_CACHE_DIR="/path/to/cache"

# Custom llama.cpp path (optional)
export LLAMA_CPP_PATH="/path/to/llama.cpp"
```

## API Reference

### ModelDownloader Class

#### Core Methods
- `download_model(model_id, config, progress_callback)` - Download a model
- `search_models(query, limit, model_type)` - Search for models
- `get_model_info(model_id)` - Get detailed model information
- `get_download_progress(model_id)` - Get download progress
- `cancel_download(model_id)` - Cancel a download
- `get_cached_models()` - List cached models
- `clear_cache(model_id)` - Clear cache

#### Configuration
- `ModelDownloadConfig` - Configuration dataclass with extensive options
- `ConfigManager` - Configuration management and validation

### TrainingModelManager Class

#### Core Methods
- `download_model_for_training(model_id, config, priority, callback)` - Download for training
- `get_available_models()` - List available models
- `get_model_path(model_id)` - Get model path
- `validate_model_for_training(model_id, requirements)` - Validate for training
- `get_training_models_by_type(model_type)` - Get models by type
- `get_model_statistics()` - Get usage statistics

#### Queue Management
- Automatic priority-based queue processing
- Progress callbacks with user data
- Download status tracking

### ModelValidator Class

#### Validation Methods
- `validate_model_structure(model_path)` - Validate model structure
- `validate_gguf_model(model_path)` - Validate GGUF format
- `check_model_compatibility(model_path, requirements)` - Check compatibility
- `verify_checksums(model_path, checksums)` - Verify checksums
- `validate_model_loading(model_path)` - Test model loading

## Model Formats and Conversion

### Supported Formats
- **Hugging Face**: Standard Hugging Face format (.bin, .safetensors)
- **GGUF**: GPT-Generated Unified Format (converted)
- **GGML**: GPT-Generated Model Language (legacy)
- **SafeTensors**: Safe tensor format

### GGUF Quantization Options
- `f32` - 32-bit float (no quantization)
- `f16` - 16-bit float
- `q8_0` - 8-bit quantization
- `q5_1`, `q5_0` - 5-bit quantization
- `q4_1`, `q4_0` - 4-bit quantization
- `q3_k`, `q4_k`, `q5_k`, `q6_k`, `q8_k` - K-quant variants

### Conversion Setup
1. Install llama.cpp: https://github.com/ggerganov/llama.cpp
2. Set `llama_cpp_path` in configuration
3. Enable `convert_to_gguf` and set `gguf_quantization`

## Authentication

### Hugging Face Token
1. Get token from: https://huggingface.co/settings/tokens
2. Set as environment variable or in config file
3. Required for private models

### Private Models
- Full support for gated/private models
- Automatic access checking
- Token validation and error handling

## Caching System

### Cache Structure
```
~/.cache/duckbot_models/
├── cache_metadata.json      # Cache metadata
├── model_id_revision/       # Model directories
│   ├── config.json
│   ├── pytorch_model.bin
│   └── ...
└── model_id_revision.gguf  # GGUF converted models
```

### Cache Management
- Automatic metadata tracking
- Size-based cleanup
- Time-based expiration
- Manual cache clearing

## Integration with Training Infrastructure

### Direct Integration
```python
# Integrate with existing trainer
from training_integration import integrate_with_trainer

manager = integrate_with_trainer(trainer_instance)

# Now trainer has:
# - download_model()
# - get_model_path()
# - list_available_models()
```

### Model Requirements for Training
```python
requirements = {
    "model_type": "bert",
    "architecture": "BertModel",
    "min_vocab_size": 30000,
    "max_model_size_gb": 10
}

validation_result = manager.validate_model_for_training(
    "bert-base-uncased",
    requirements
)
```

## Error Handling

### Common Issues
1. **Authentication Errors**: Check HUGGINGFACE_TOKEN
2. **Network Issues**: Enable resume_download
3. **Permission Errors**: Check cache directory permissions
4. **Memory Issues**: Reduce max_workers
5. **Conversion Errors**: Verify llama.cpp installation

### Logging
```python
import logging
logging.basicConfig(level=logging.INFO)

# Debug logging for troubleshooting
logger = logging.getLogger('DuckBot.ModelDownloader')
logger.setLevel(logging.DEBUG)
```

## Performance Optimization

### Download Optimization
- Increase `max_workers` for faster downloads
- Use `resume_download` for reliability
- Set appropriate `chunk_size` (1MB default)
- Enable parallel file downloads

### Cache Optimization
- Monitor cache size with `get_model_statistics()`
- Configure `max_cache_size_gb` appropriately
- Use automatic cleanup with `cache_cleanup_days`

### System Resources
- Monitor memory usage during downloads
- Adjust worker count based on system capabilities
- Use SSD for cache directory for better performance

## Testing

### Run Test Suite
```bash
# Basic tests
python test_model_downloader.py

# Integration tests
python test_training_integration.py

# Comprehensive testing
python -m pytest tests/ -v
```

### Test Coverage
- Unit tests for all core classes
- Integration tests for training workflows
- Mock testing for network operations
- Error scenario testing

## Security Considerations

### Token Security
- Never log or print tokens
- Use environment variables for sensitive data
- Regularly rotate tokens
- Limit token permissions

### File Security
- Verify checksums for all downloads
- Validate file integrity before use
- Use safe download directories
- Clean up temporary files

## Troubleshooting

### Common Solutions

**Download Fails**
- Check internet connection
- Verify model exists on Hugging Face
- Check token permissions for private models
- Increase timeout values

**GGUF Conversion Fails**
- Verify llama.cpp installation
- Check convert.py location
- Ensure sufficient disk space
- Verify model compatibility

**Cache Issues**
- Clear cache with `clear_cache()`
- Check disk space
- Verify directory permissions
- Check cache configuration

### Debug Commands
```bash
# Check cache contents
python -c "from training_integration import TrainingModelManager; m = TrainingModelManager(); print(m.get_model_statistics())"

# Test model download
python huggingface_downloader.py facebook/opt-125m --list-cached

# Validate model
python -c "from huggingface_downloader import ModelValidator; v = ModelValidator(); print(v.validate_model_structure(Path('path/to/model')))"
```

## Contributing

### Development Setup
1. Install development dependencies
2. Create virtual environment
3. Run tests before committing
4. Follow code style guidelines

### Code Style
- Follow PEP 8
- Add type hints
- Include docstrings
- Write comprehensive tests

## License

This component is part of DuckBot Enhanced v4.2 and follows the same license terms.

## Support

For issues and questions:
1. Check troubleshooting section
2. Review test examples
3. Check DuckBot documentation
4. Create issue in repository