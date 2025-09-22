# DuckBot Model Training Module

A comprehensive module for training and fine-tuning AI models with support for both GGUF quantized models and Hugging Face transformer models. Features an enhanced AutoTrain-like interface for ease of use.

## Features

- **GGUF Model Support**: Train and fine-tune GGUF quantized models
- **Hugging Face Integration**: Download and train models from Hugging Face
- **Multiple Training Methods**: 
  - LoRA (Low-Rank Adaptation) for efficient fine-tuning
  - Full fine-tuning for maximum customization
  - Knowledge distillation for model compression
  - Continued pre-training for domain adaptation
- **Enhanced AutoTrain-like Interface**: User-friendly interface similar to Hugging Face AutoTrain
- **Web UI Interface**: Modern web-based interface for managing training workflows
- **Electron Launcher Integration**: Seamlessly starts from the main DuckBot launcher
- **Standalone Operation**: Works independently or integrated with DuckBot
- **REST API**: REST API for programmatic access
- **RAG Support**: Built-in Retrieval Augmented Generation capabilities

## Installation

The module automatically installs required dependencies when launched from the batch file:

```bash
pip install -r requirements.txt
```

## Usage

### From Command Line

```bash
# List available models
python model_trainer.py --list-models

# Download a Hugging Face model
python model_trainer.py --download meta-llama/Llama-2-7b-chat-hf

# Train with configuration file
python model_trainer.py --config training_config.json

# Train with command line parameters
python model_trainer.py --model my_model.gguf --dataset my_dataset.json --output trained_model

# Start web UI
python model_trainer.py --web-ui
```

### From Electron Launcher

The module is automatically integrated into the DuckBot Electron launcher as "Model Training Studio".

### Web UI

Start the web UI server:
```bash
python ui_server.py
```

Then access the UI at `http://localhost:8080/enhanced_autotrain_ui.html`

## Configuration

### Training Configuration File

Create a JSON configuration file for complex training setups:

```json
{
  "model_path": "hf:meta-llama/Llama-2-7b-chat-hf",
  "model_type": "hf_transformers",
  "training_method": "lora",
  "dataset_path": "datasets/my_dataset.json",
  "output_dir": "trained_models/my_trained_model",
  "epochs": 3,
  "learning_rate": 3e-4,
  "batch_size": 4,
  "gradient_accumulation_steps": 4,
  "max_seq_length": 512,
  "lora_r": 8,
  "lora_alpha": 16,
  "lora_dropout": 0.1,
  "use_4bit": true,
  "save_steps": 500,
  "logging_steps": 50,
  "eval_steps": 500,
  "warmup_steps": 100,
  "weight_decay": 0.01,
  "max_grad_norm": 1.0,
  "push_to_hub": false,
  "chat_template": "none",
  "distributed_backend": "ddp",
  "mixed_precision": "fp16",
  "optimizer": "adamw_torch",
  "scheduler": "linear",
  "target_modules": "all-linear",
  "block_size": 1024,
  "model_max_length": 2048
}
```

## Supported Models

### GGUF Models
- Supports all GGUF quantized models
- Efficient training with llama.cpp backend

### Hugging Face Models
- All transformer-based models from Hugging Face
- Automatic download and caching

## Training Methods

### LoRA (Low-Rank Adaptation)
Efficient fine-tuning method that adapts large models with a small number of parameters.

### Full Fine-tuning
Traditional approach that updates all model parameters.

### Knowledge Distillation
Transfer knowledge from a larger "teacher" model to a smaller "student" model.

### Continued Pre-training
Continue training a pre-trained model on domain-specific data.

## Directory Structure

```
launcher-modules/
└── model-training/
    ├── model_trainer.py         # Main training module
    ├── ui_server.py             # Web UI server
    ├── enhanced_autotrain_ui.html # Enhanced AutoTrain-like web interface
    ├── autotrain_ui.html        # Standard AutoTrain web interface
    ├── module.py                # Module configuration for DuckBot launcher
    ├── config.json              # Module configuration
    ├── requirements.txt         # Python dependencies
    ├── START_MODEL_TRAINING.bat # Batch launcher
    ├── START_FROM_ELECTRON.bat  # Electron launcher integration
    ├── sample_dataset.json      # Sample training data
    ├── sample_training_config.json # Sample configuration
    ├── models/                  # Downloaded models
    ├── datasets/                # Training datasets
    └── trained_models/          # Output directory for trained models
```

## Integration with DuckBot

The module is fully integrated with the DuckBot ecosystem:

1. Appears as a startup mode in the Electron launcher
2. Uses the same configuration system as other DuckBot modules
3. Shares logging and monitoring infrastructure
4. Can be managed through the modular launcher system
5. Provides REST API for programmatic access

## API Endpoints

The module provides a REST API for integration with other systems:

- `GET /api/config` - Get module configuration
- `GET /api/models` - List available models
- `GET /api/projects` - List training projects
- `GET /api/status` - Get training status
- `POST /api/projects` - Create new project
- `POST /api/train` - Start training
- `POST /api/stop` - Stop training

## Troubleshooting

### Common Issues

1. **Missing Dependencies**: Run the batch file to automatically install required packages
2. **Model Not Found**: Ensure models are in the `models/` directory or use full paths
3. **GPU Memory Issues**: Reduce batch size or enable quantization
4. **Hugging Face Download Failures**: Check internet connection and API tokens

### Logs

Training logs are saved to `logs/model_trainer.log` and displayed in the Web UI.

## Contributing

Contributions are welcome! Please submit issues and pull requests to the main DuckBot repository.

## License

This module is part of the DuckBot project and is licensed under the same terms.