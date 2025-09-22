#!/usr/bin/env python3
"""
DuckBot Model Download Configuration Manager
Handles loading, validation, and management of download configurations.
"""

import os
import json
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, asdict
from enum import Enum

class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"

@dataclass
class HuggingFaceConfig:
    """Hugging Face specific configuration"""
    token: Optional[str] = None
    endpoint: str = "https://huggingface.co"
    cache_dir: Optional[str] = None
    default_cache_dir: str = "~/.cache/duckbot_models"
    max_workers: int = 4
    timeout: int = 300
    retry_attempts: int = 3
    retry_delay: int = 5

@dataclass
class DownloadConfig:
    """Download behavior configuration"""
    resume_download: bool = True
    force_download: bool = False
    local_files_only: bool = False
    validate_checksum: bool = True
    chunk_size: int = 1048576  # 1MB
    max_concurrent_downloads: int = 3

@dataclass
class ConversionConfig:
    """Model conversion configuration"""
    convert_to_gguf: bool = False
    gguf_quantization: Optional[str] = None
    llama_cpp_path: Optional[str] = None
    auto_find_llama_cpp: bool = True
    supported_quantizations: List[str] = None

    def __post_init__(self):
        if self.supported_quantizations is None:
            self.supported_quantizations = [
                "q4_0", "q4_1", "q5_0", "q5_1",
                "q8_0", "q8_1", "f16", "f32"
            ]

@dataclass
class CacheConfig:
    """Cache management configuration"""
    enabled: bool = True
    max_cache_size_gb: int = 100
    cache_cleanup_days: int = 30
    auto_cleanup: bool = True
    metadata_file: str = "cache_metadata.json"

@dataclass
class SecurityConfig:
    """Security configuration"""
    verify_ssl: bool = True
    allow_insecure_connections: bool = False
    token_env_var: str = "HUGGINGFACE_TOKEN"
    allow_public_models: bool = True

@dataclass
class LoggingConfig:
    """Logging configuration"""
    level: str = "INFO"
    file: str = "model_downloader.log"
    max_size_mb: int = 10
    backup_count: int = 5
    enable_console: bool = True

@dataclass
class UIConfig:
    """User interface configuration"""
    show_progress_bar: bool = True
    progress_bar_format: str = "{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]"
    enable_rich_output: bool = True
    color_scheme: Dict[str, str] = None

    def __post_init__(self):
        if self.color_scheme is None:
            self.color_scheme = {
                "downloading": "blue",
                "completed": "green",
                "failed": "red",
                "paused": "yellow"
            }

@dataclass
class DefaultsConfig:
    """Default download settings"""
    revision: str = "main"
    model_type: str = "huggingface"
    download_patterns: List[str] = None
    ignore_patterns: List[str] = None

    def __post_init__(self):
        if self.download_patterns is None:
            self.download_patterns = [
                "*.json", "*.bin", "*.safetensors", "*.py", "*.txt", "*.md",
                "config.json", "tokenizer.json", "tokenizer_config.json", "special_tokens_map.json"
            ]
        if self.ignore_patterns is None:
            self.ignore_patterns = [
                "*.git*", "*.DS_Store", "Thumbs.db", "*.pyc", "__pycache__"
            ]

@dataclass
class ModelDownloadConfig:
    """Complete model download configuration"""
    huggingface: HuggingFaceConfig = None
    download: DownloadConfig = None
    conversion: ConversionConfig = None
    cache: CacheConfig = None
    security: SecurityConfig = None
    logging: LoggingConfig = None
    ui: UIConfig = None
    defaults: DefaultsConfig = None

    def __post_init__(self):
        if self.huggingface is None:
            self.huggingface = HuggingFaceConfig()
        if self.download is None:
            self.download = DownloadConfig()
        if self.conversion is None:
            self.conversion = ConversionConfig()
        if self.cache is None:
            self.cache = CacheConfig()
        if self.security is None:
            self.security = SecurityConfig()
        if self.logging is None:
            self.logging = LoggingConfig()
        if self.ui is None:
            self.ui = UIConfig()
        if self.defaults is None:
            self.defaults = DefaultsConfig()

class ConfigManager:
    """Manages model download configuration"""

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = Path(config_path or self._get_default_config_path())
        self.config: Optional[ModelDownloadConfig] = None
        self.logger = logging.getLogger('DuckBot.ConfigManager')
        self._load_config()

    def _get_default_config_path(self) -> Path:
        """Get default configuration file path"""
        script_dir = Path(__file__).parent
        return script_dir / "config" / "model_download_config.json"

    def _load_config(self):
        """Load configuration from file"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    if self.config_path.suffix.lower() in ['.yaml', '.yml']:
                        data = yaml.safe_load(f)
                    else:
                        data = json.load(f)

                self.config = self._dict_to_config(data)
                self.logger.info(f"Loaded configuration from {self.config_path}")
            else:
                self.config = ModelDownloadConfig()
                self.logger.info("Using default configuration")
                self.save_config()  # Save default config

        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            self.config = ModelDownloadConfig()

    def _dict_to_config(self, data: Dict[str, Any]) -> ModelDownloadConfig:
        """Convert dictionary to configuration object"""
        config = ModelDownloadConfig()

        # Load HuggingFace config
        if 'huggingface' in data:
            hf_data = data['huggingface']
            config.huggingface = HuggingFaceConfig(**hf_data)

        # Load Download config
        if 'download' in data:
            dl_data = data['download']
            config.download = DownloadConfig(**dl_data)

        # Load Conversion config
        if 'conversion' in data:
            conv_data = data['conversion']
            config.conversion = ConversionConfig(**conv_data)

        # Load Cache config
        if 'cache' in data:
            cache_data = data['cache']
            config.cache = CacheConfig(**cache_data)

        # Load Security config
        if 'security' in data:
            sec_data = data['security']
            config.security = SecurityConfig(**sec_data)

        # Load Logging config
        if 'logging' in data:
            log_data = data['logging']
            config.logging = LoggingConfig(**log_data)

        # Load UI config
        if 'ui' in data:
            ui_data = data['ui']
            config.ui = UIConfig(**ui_data)

        # Load Defaults config
        if 'defaults' in data:
            defaults_data = data['defaults']
            config.defaults = DefaultsConfig(**defaults_data)

        return config

    def save_config(self, config_path: Optional[str] = None):
        """Save configuration to file"""
        save_path = Path(config_path or self.config_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            config_dict = asdict(self.config)

            with open(save_path, 'w', encoding='utf-8') as f:
                if save_path.suffix.lower() in ['.yaml', '.yml']:
                    yaml.dump(config_dict, f, default_flow_style=False, indent=2)
                else:
                    json.dump(config_dict, f, indent=2)

            self.logger.info(f"Saved configuration to {save_path}")

        except Exception as e:
            self.logger.error(f"Failed to save configuration: {e}")
            raise

    def get_config(self) -> ModelDownloadConfig:
        """Get current configuration"""
        return self.config

    def update_config(self, updates: Dict[str, Any]):
        """Update configuration with new values"""
        try:
            # Convert nested updates to appropriate objects
            for section, values in updates.items():
                if hasattr(self.config, section):
                    section_config = getattr(self.config, section)
                    for key, value in values.items():
                        if hasattr(section_config, key):
                            setattr(section_config, key, value)
                        else:
                            self.logger.warning(f"Unknown config key: {section}.{key}")
                else:
                    self.logger.warning(f"Unknown config section: {section}")

            self.logger.info("Configuration updated")

        except Exception as e:
            self.logger.error(f"Failed to update configuration: {e}")
            raise

    def get_huggingface_token(self) -> Optional[str]:
        """Get Hugging Face token from config or environment"""
        token = self.config.huggingface.token
        if not token:
            # Try environment variable
            token = os.getenv(self.config.security.token_env_var)
        return token

    def get_cache_dir(self) -> str:
        """Get cache directory path"""
        cache_dir = self.config.huggingface.cache_dir
        if not cache_dir:
            cache_dir = os.path.expanduser(self.config.huggingface.default_cache_dir)
        return cache_dir

    def is_valid_quantization(self, quantization: str) -> bool:
        """Check if quantization method is supported"""
        return quantization.lower() in [
            q.lower() for q in self.config.conversion.supported_quantizations
        ]

    def get_supported_quantizations(self) -> List[str]:
        """Get list of supported quantization methods"""
        return self.config.conversion.supported_quantizations.copy()

    def setup_logging(self):
        """Setup logging based on configuration"""
        log_config = self.config.logging

        # Create logs directory
        log_file = Path(log_config.file)
        log_file.parent.mkdir(parents=True, exist_ok=True)

        # Configure logging
        logging.basicConfig(
            level=getattr(logging, log_config.level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(
                    log_file,
                    maxBytes=log_config.max_size_mb * 1024 * 1024,
                    backupCount=log_config.backup_count,
                    encoding='utf-8'
                )
            ]
        )

        # Add console handler if enabled
        if log_config.enable_console:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(getattr(logging, log_config.level))
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(formatter)
            logging.getLogger('').addHandler(console_handler)

    def validate_config(self) -> List[str]:
        """Validate configuration and return list of issues"""
        issues = []

        # Validate HuggingFace config
        hf_config = self.config.huggingface
        if hf_config.max_workers < 1:
            issues.append("max_workers must be at least 1")
        if hf_config.timeout < 1:
            issues.append("timeout must be at least 1 second")
        if hf_config.retry_attempts < 0:
            issues.append("retry_attempts cannot be negative")

        # Validate Download config
        dl_config = self.config.download
        if dl_config.chunk_size < 1024:
            issues.append("chunk_size must be at least 1024 bytes")
        if dl_config.max_concurrent_downloads < 1:
            issues.append("max_concurrent_downloads must be at least 1")

        # Validate Cache config
        cache_config = self.config.cache
        if cache_config.max_cache_size_gb < 1:
            issues.append("max_cache_size_gb must be at least 1")
        if cache_config.cache_cleanup_days < 1:
            issues.append("cache_cleanup_days must be at least 1")

        # Validate Conversion config
        conv_config = self.config.conversion
        if conv_config.gguf_quantization and not self.is_valid_quantization(conv_config.gguf_quantization):
            issues.append(f"Unsupported quantization: {conv_config.gguf_quantization}")

        # Validate Logging config
        log_config = self.config.logging
        if log_config.max_size_mb < 1:
            issues.append("max_size_mb must be at least 1")
        if log_config.backup_count < 0:
            issues.append("backup_count cannot be negative")

        # Validate log level
        try:
            getattr(logging, log_config.level)
        except AttributeError:
            issues.append(f"Invalid log level: {log_config.level}")

        return issues

    def get_download_config_for_model(
        self,
        model_id: str,
        overrides: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get download configuration for a specific model"""
        # Start with defaults
        config = {
            "model_id": model_id,
            "token": self.get_huggingface_token(),
            "cache_dir": self.get_cache_dir(),
            "revision": self.config.defaults.revision,
            "max_workers": self.config.huggingface.max_workers,
            "resume_download": self.config.download.resume_download,
            "force_download": self.config.download.force_download,
            "local_files_only": self.config.download.local_files_only,
            "validate_checksum": self.config.download.validate_checksum,
            "convert_to_gguf": self.config.conversion.convert_to_gguf,
            "gguf_quantization": self.config.conversion.gguf_quantization,
            "allow_patterns": self.config.defaults.download_patterns,
            "ignore_patterns": self.config.defaults.ignore_patterns
        }

        # Apply overrides
        if overrides:
            config.update(overrides)

        return config

    def export_config(self, output_path: str, format: str = "json"):
        """Export configuration to file"""
        output_file = Path(output_path)

        try:
            config_dict = asdict(self.config)

            with open(output_file, 'w', encoding='utf-8') as f:
                if format.lower() == 'yaml':
                    yaml.dump(config_dict, f, default_flow_style=False, indent=2)
                else:
                    json.dump(config_dict, f, indent=2)

            self.logger.info(f"Exported configuration to {output_file}")

        except Exception as e:
            self.logger.error(f"Failed to export configuration: {e}")
            raise

    def import_config(self, input_path: str):
        """Import configuration from file"""
        input_file = Path(input_path)

        if not input_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {input_file}")

        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                if input_file.suffix.lower() in ['.yaml', '.yml']:
                    data = yaml.safe_load(f)
                else:
                    data = json.load(f)

            self.config = self._dict_to_config(data)
            self.logger.info(f"Imported configuration from {input_file}")

        except Exception as e:
            self.logger.error(f"Failed to import configuration: {e}")
            raise

def main():
    """Main entry point for configuration management"""
    import argparse

    parser = argparse.ArgumentParser(description="DuckBot Model Download Configuration Manager")
    parser.add_argument("--config", help="Configuration file path")
    parser.add_argument("--validate", action="store_true", help="Validate configuration")
    parser.add_argument("--export", help="Export configuration to file")
    parser.add_argument("--import", dest="import_file", help="Import configuration from file")
    parser.add_argument("--show", action="store_true", help="Show current configuration")
    parser.add_argument("--set-token", help="Set Hugging Face token")
    parser.add_argument("--list-quantizations", action="store_true", help="List supported quantizations")

    args = parser.parse_args()

    # Initialize config manager
    config_manager = ConfigManager(args.config)

    if args.validate:
        issues = config_manager.validate_config()
        if issues:
            print("Configuration issues found:")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print("Configuration is valid")
        return

    if args.export:
        config_manager.export_config(args.export)
        print(f"Configuration exported to {args.export}")
        return

    if args.import_file:
        config_manager.import_config(args.import_file)
        print(f"Configuration imported from {args.import_file}")
        return

    if args.show:
        config = config_manager.get_config()
        print("Current configuration:")
        print(json.dumps(asdict(config), indent=2))
        return

    if args.set_token:
        config_manager.update_config({
            "huggingface": {"token": args.set_token}
        })
        config_manager.save_config()
        print("Hugging Face token updated")
        return

    if args.list_quantizations:
        quantizations = config_manager.get_supported_quantizations()
        print("Supported quantizations:")
        for q in quantizations:
            print(f"  - {q}")
        return

    # Show basic info
    config = config_manager.get_config()
    print(f"Cache directory: {config_manager.get_cache_dir()}")
    print(f"Hugging Face token: {'Set' if config_manager.get_huggingface_token() else 'Not set'}")
    print(f"Max workers: {config.huggingface.max_workers}")
    print(f"Convert to GGUF: {config.conversion.convert_to_gguf}")

if __name__ == "__main__":
    main()