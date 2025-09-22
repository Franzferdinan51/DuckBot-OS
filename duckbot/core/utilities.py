#!/usr/bin/env python3
"""
DuckBot Consolidated Utilities v4.2
Unified utilities module combining common utility functions

This module consolidates the most commonly used utility functions from:
- Backup and packaging utilities
- Unicode handling utilities  
- AI provider setup utilities
- System diagnostics utilities
- File management utilities
- Configuration utilities

Features:
- Unified interface for all common utilities
- Backward compatibility with existing utility scripts
- Enhanced error handling and logging
- Cross-platform compatibility
- Performance optimizations
"""

import os
import sys
import json
import zipfile
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import subprocess
import shutil

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('duckbot_utilities.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class DuckBotUtilities:
    """Consolidated utilities for DuckBot system"""
    
    def __init__(self):
        self.backup_config = {
            "exclude_patterns": [
                # AI Model directories
                '/models/',
                '\\\\models\\\\',
                '/checkpoints/',
                '\\\\checkpoints\\\\',
                '/lora/',
                '\\\\lora\\\\',
                '/vae/',
                '\\\\vae\\\\',
                '/embeddings/',
                '\\\\embeddings\\\\',
                '/controlnet/',
                '\\\\controlnet\\\\',
                # Model file extensions
                '.ckpt',
                '.safetensors',
                '.pt',
                '.pth',
                '.bin',
                # Large cache/temp files
                '__pycache__',
                '.pyc',
                '.pyo',
                'node_modules',
                '.git',
                '.gitignore',
                # Log files and temp data
                '.log',
                '.tmp',
                '.temp',
                '/temp/',
                '\\\\temp\\\\',
                '/logs/',
                '\\\\logs\\\\',
                # Virtual environments
                '/venv/',
                '\\\\venv\\\\',
                '/env/',
                '\\\\env\\\\',
                # IDE files
                '.vscode',
                '.idea',
                # Large datasets
                '/datasets/',
                '\\\\datasets\\\\',
            ],
            "compress_level": 6,
            "buffer_size": 65536
        }
        
        self.unicode_config = {
            "encoding": "utf-8",
            "errors": "replace"
        }
        
        self.ai_providers = {
            "lm_studio": {
                "name": "LM Studio (Local)",
                "url": "http://localhost:1234/v1",
                "models": [
                    "openai/gpt-oss-20b",
                    "qwen/qwen3-coder:free",
                    "deepseek/deepseek-r1:free"
                ]
            },
            "openrouter": {
                "name": "OpenRouter (Cloud)",
                "url": "https://openrouter.ai/api/v1",
                "models": [
                    "qwen/qwen3-coder:free",
                    "deepseek/deepseek-r1-0528:free",
                    "moonshotai/kimi-k2:free",
                    "z-ai/glm-4.5-air:free"
                ]
            }
        }

    # ============================================================================
    # BACKUP AND PACKAGING UTILITIES
    # ============================================================================

    def should_exclude_path(self, path_str: str) -> bool:
        """Check if a path should be excluded from backup operations"""
        path_lower = path_str.lower()
        return any(pattern.lower() in path_lower for pattern in self.backup_config["exclude_patterns"])

    def create_backup_zip(self, 
                         source_dir: Optional[Union[str, Path]] = None,
                         output_path: Optional[Union[str, Path]] = None,
                         exclude_patterns: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Create comprehensive backup zip excluding large files
        
        Args:
            source_dir: Source directory to backup (defaults to current directory)
            output_path: Output zip file path (auto-generated if not provided)
            exclude_patterns: Additional patterns to exclude
            
        Returns:
            Dict with backup statistics and status
        """
        try:
            # Set defaults
            if source_dir is None:
                source_dir = Path.cwd()
            else:
                source_dir = Path(source_dir)
                
            if output_path is None:
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                output_path = Path.home() / f"DuckBot-Backup-{timestamp}.zip"
            else:
                output_path = Path(output_path)
                
            # Update exclude patterns if provided
            if exclude_patterns:
                self.backup_config["exclude_patterns"].extend(exclude_patterns)
            
            logger.info(f"Creating backup: {output_path}")
            logger.info(f"Source directory: {source_dir}")
            
            included_count = 0
            excluded_count = 0
            total_size = 0
            
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED, 
                               compresslevel=self.backup_config["compress_level"]) as zipf:
                for root, dirs, files in os.walk(source_dir):
                    # Filter out excluded directories
                    dirs[:] = [d for d in dirs if not self.should_exclude_path(os.path.join(root, d))]
                    
                    for file in files:
                        file_path = os.path.join(root, file)
                        
                        if self.should_exclude_path(file_path):
                            excluded_count += 1
                            continue
                        
                        try:
                            # Get relative path for zip
                            rel_path = os.path.relpath(file_path, source_dir)
                            
                            # Add to zip
                            zipf.write(file_path, rel_path)
                            included_count += 1
                            
                            # Track size
                            total_size += os.path.getsize(file_path)
                            
                            if included_count % 100 == 0:
                                logger.info(f"Processed {included_count} files...")
                                
                        except Exception as e:
                            logger.warning(f"Could not add {file_path}: {e}")
                            excluded_count += 1
            
            result = {
                "success": True,
                "output_path": str(output_path),
                "included_files": included_count,
                "excluded_files": excluded_count,
                "total_size_bytes": total_size,
                "zip_size_bytes": os.path.getsize(output_path) if output_path.exists() else 0,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            logger.info(f"Backup created successfully: {result['output_path']}")
            return result
            
        except Exception as e:
            logger.error(f"Backup creation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "output_path": str(output_path) if 'output_path' in locals() else "unknown"
            }

    def create_simple_backup(self, 
                           source_dir: Optional[Union[str, Path]] = None,
                           backup_name: Optional[str] = None) -> Dict[str, Any]:
        """Create simple backup without exclusions"""
        try:
            if source_dir is None:
                source_dir = Path.cwd()
            else:
                source_dir = Path(source_dir)
                
            if backup_name is None:
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                backup_name = f"DuckBot-Simple-Backup-{timestamp}.zip"
                
            backup_path = Path(backup_name)
            
            logger.info(f"Creating simple backup: {backup_path}")
            
            # Use shutil.make_archive for simplicity
            base_name = str(backup_path.with_suffix(''))
            format = 'zip'
            root_dir = str(source_dir)
            
            archive_path = shutil.make_archive(base_name, format, root_dir)
            
            result = {
                "success": True,
                "output_path": archive_path,
                "size_bytes": os.path.getsize(archive_path),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            logger.info(f"Simple backup created: {result['output_path']}")
            return result
            
        except Exception as e:
            logger.error(f"Simple backup failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    # ============================================================================
    # UNICODE HANDLING UTILITIES
    # ============================================================================

    def setup_unicode_environment(self) -> bool:
        """Setup proper Unicode encoding for console output"""
        try:
            if os.name == 'nt':  # Windows
                # Set UTF-8 encoding for console output
                os.environ['PYTHONIOENCODING'] = self.unicode_config["encoding"]
                
                # Enable UTF-8 mode in Python 3.7+
                if hasattr(sys, 'set_int_max_str_digits'):
                    os.environ['PYTHONUTF8'] = '1'
            
            # Configure stdout/stderr encoding
            if hasattr(sys.stdout, 'reconfigure'):
                sys.stdout.reconfigure(encoding=self.unicode_config["encoding"])
                sys.stderr.reconfigure(encoding=self.unicode_config["encoding"])
                
            logger.info("Unicode environment configured successfully")
            return True
            
        except Exception as e:
            logger.error(f"Unicode setup failed: {e}")
            return False

    def fix_unicode_issues(self, text: str) -> str:
        """Fix Unicode encoding issues in text"""
        try:
            # Try to encode/decode with proper handling
            encoded = text.encode(self.unicode_config["encoding"], errors=self.unicode_config["errors"])
            decoded = encoded.decode(self.unicode_config["encoding"], errors=self.unicode_config["errors"])
            return decoded
        except Exception as e:
            logger.warning(f"Unicode fix failed: {e}")
            # Return original text as fallback
            return text

    # ============================================================================
    # AI PROVIDER SETUP UTILITIES
    # ============================================================================

    def setup_ai_provider(self, provider: str = "lm_studio") -> Dict[str, Any]:
        """
        Setup AI provider configuration
        
        Args:
            provider: Provider to setup ("lm_studio" or "openrouter")
            
        Returns:
            Dict with configuration and status
        """
        try:
            if provider not in self.ai_providers:
                raise ValueError(f"Unsupported provider: {provider}")
                
            provider_info = self.ai_providers[provider]
            config = {
                "provider": provider,
                "model_name": provider_info["models"][0],  # Default model
                "max_tokens": 1500,
                "temperature": 0.3,
                "auto_action_enabled": True,
                "monitoring_interval": 30,
                "decision_confidence_threshold": 0.7
            }
            
            # Provider-specific configuration
            if provider == "lm_studio":
                config.update({
                    "lm_studio_url": provider_info["url"],
                    "model_name": "openai/gpt-oss-20b"
                })
            elif provider == "openrouter":
                # For OpenRouter, we would typically prompt for API key
                # In this consolidated version, we'll just set defaults
                config.update({
                    "openrouter_api_key": "your_openrouter_api_key_here",  # Placeholder
                    "openrouter_url": provider_info["url"],
                    "model_name": "qwen/qwen3-coder:free"
                })
            
            # Add common settings
            config.update({
                "conversation_history_limit": 50,
                "report_interval": 300,
                "_setup_timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            })
            
            logger.info(f"AI provider {provider} configured successfully")
            return {
                "success": True,
                "provider": provider,
                "config": config
            }
            
        except Exception as e:
            logger.error(f"AI provider setup failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "provider": provider
            }

    def get_available_ai_models(self, provider: str = "lm_studio") -> List[str]:
        """Get list of available models for a provider"""
        if provider in self.ai_providers:
            return self.ai_providers[provider]["models"]
        return []

    def test_ai_provider_connection(self, provider: str = "lm_studio", config: Optional[Dict] = None) -> Dict[str, Any]:
        """Test connection to AI provider"""
        try:
            if config is None:
                setup_result = self.setup_ai_provider(provider)
                if not setup_result["success"]:
                    return setup_result
                config = setup_result["config"]
            
            # Test connection based on provider
            if provider == "lm_studio":
                import requests
                url = config.get("lm_studio_url", "http://localhost:1234/v1")
                response = requests.get(f"{url}/models", timeout=5)
                success = response.status_code == 200
                
            elif provider == "openrouter":
                # For OpenRouter, check if API key is set
                api_key = config.get("openrouter_api_key", "")
                success = bool(api_key and api_key != "your_openrouter_api_key_here")
                
            else:
                success = False
            
            return {
                "success": success,
                "provider": provider,
                "message": "Connection successful" if success else "Connection failed"
            }
            
        except Exception as e:
            logger.error(f"AI provider connection test failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "provider": provider
            }

    # ============================================================================
    # SYSTEM DIAGNOSTICS UTILITIES
    # ============================================================================

    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        try:
            import psutil
            
            # CPU info
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # Memory info
            memory = psutil.virtual_memory()
            
            # Disk info
            disk = psutil.disk_usage('/')
            
            # Network info
            net_io = psutil.net_io_counters()
            
            status = {
                "cpu": {
                    "percent": cpu_percent,
                    "count": cpu_count,
                    "frequency": psutil.cpu_freq().current if psutil.cpu_freq() else 0
                },
                "memory": {
                    "total_gb": memory.total / (1024**3),
                    "available_gb": memory.available / (1024**3),
                    "percent": memory.percent
                },
                "disk": {
                    "total_gb": disk.total / (1024**3),
                    "free_gb": disk.free / (1024**3),
                    "percent": (disk.used / disk.total) * 100
                },
                "network": {
                    "bytes_sent_mb": net_io.bytes_sent / (1024**2),
                    "bytes_recv_mb": net_io.bytes_recv / (1024**2)
                },
                "boot_time": psutil.boot_time(),
                "timestamp": time.time()
            }
            
            logger.info("System status retrieved successfully")
            return status
            
        except ImportError:
            logger.warning("psutil not available for system status")
            return {
                "error": "psutil module not available",
                "cpu": {"percent": 0, "count": 0},
                "memory": {"total_gb": 0, "available_gb": 0, "percent": 0},
                "disk": {"total_gb": 0, "free_gb": 0, "percent": 0}
            }
        except Exception as e:
            logger.error(f"System status retrieval failed: {e}")
            return {
                "error": str(e)
            }

    def get_python_environment_info(self) -> Dict[str, Any]:
        """Get Python environment information"""
        try:
            import platform
            import sys
            
            info = {
                "python_version": platform.python_version(),
                "python_implementation": platform.python_implementation(),
                "platform": platform.platform(),
                "architecture": platform.architecture()[0],
                "machine": platform.machine(),
                "processor": platform.processor(),
                "system": platform.system(),
                "release": platform.release(),
                "executable": sys.executable,
                "prefix": sys.prefix,
                "base_prefix": sys.base_prefix,
                "path": sys.path,
                "modules": list(sys.modules.keys())
            }
            
            logger.info("Python environment info retrieved")
            return info
            
        except Exception as e:
            logger.error(f"Python environment info failed: {e}")
            return {
                "error": str(e)
            }

    # ============================================================================
    # FILE MANAGEMENT UTILITIES
    # ============================================================================

    def safe_delete_file(self, file_path: Union[str, Path]) -> bool:
        """Safely delete a file with error handling"""
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
                logger.info(f"File deleted: {file_path}")
                return True
            else:
                logger.info(f"File not found: {file_path}")
                return True
        except Exception as e:
            logger.error(f"Failed to delete file {file_path}: {e}")
            return False

    def safe_copy_file(self, source: Union[str, Path], destination: Union[str, Path]) -> bool:
        """Safely copy a file with error handling"""
        try:
            src = Path(source)
            dst = Path(destination)
            
            if not src.exists():
                logger.error(f"Source file not found: {source}")
                return False
                
            # Create destination directory if needed
            dst.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.copy2(src, dst)
            logger.info(f"File copied: {source} -> {destination}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to copy file {source} -> {destination}: {e}")
            return False

    def find_files_by_pattern(self, directory: Union[str, Path], pattern: str) -> List[str]:
        """Find files matching a pattern"""
        try:
            directory = Path(directory)
            files = []
            
            for file_path in directory.rglob(pattern):
                files.append(str(file_path))
                
            logger.info(f"Found {len(files)} files matching pattern: {pattern}")
            return files
            
        except Exception as e:
            logger.error(f"File search failed: {e}")
            return []

    # ============================================================================
    # CONFIGURATION UTILITIES
    # ============================================================================

    def load_json_config(self, config_file: Union[str, Path]) -> Dict[str, Any]:
        """Load JSON configuration file"""
        try:
            config_path = Path(config_file)
            if not config_path.exists():
                logger.warning(f"Config file not found: {config_file}")
                return {}
                
            with open(config_path, 'r', encoding=self.unicode_config["encoding"]) as f:
                config = json.load(f)
                
            logger.info(f"Configuration loaded: {config_file}")
            return config
            
        except Exception as e:
            logger.error(f"Failed to load config {config_file}: {e}")
            return {}

    def save_json_config(self, config: Dict[str, Any], config_file: Union[str, Path]) -> bool:
        """Save JSON configuration file"""
        try:
            config_path = Path(config_file)
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_path, 'w', encoding=self.unicode_config["encoding"]) as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
                
            logger.info(f"Configuration saved: {config_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save config {config_file}: {e}")
            return False

    def merge_configs(self, base_config: Dict[str, Any], override_config: Dict[str, Any]) -> Dict[str, Any]:
        """Merge two configuration dictionaries"""
        try:
            merged = base_config.copy()
            
            def deep_merge(base, override):
                for key, value in override.items():
                    if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                        deep_merge(base[key], value)
                    else:
                        base[key] = value
            
            deep_merge(merged, override_config)
            
            logger.info("Configs merged successfully")
            return merged
            
        except Exception as e:
            logger.error(f"Config merge failed: {e}")
            # Return base config as fallback
            return base_config

# ============================================================================
# GLOBAL UTILITY FUNCTIONS
# ============================================================================

# Create global instance
utilities = DuckBotUtilities()

# Export convenience functions
def create_backup(source_dir: Optional[Union[str, Path]] = None,
                 output_path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
    """Create backup zip"""
    return utilities.create_backup_zip(source_dir, output_path)

def create_simple_backup(source_dir: Optional[Union[str, Path]] = None,
                        backup_name: Optional[str] = None) -> Dict[str, Any]:
    """Create simple backup"""
    return utilities.create_simple_backup(source_dir, backup_name)

def setup_unicode() -> bool:
    """Setup Unicode environment"""
    return utilities.setup_unicode_environment()

def setup_ai_provider(provider: str = "lm_studio") -> Dict[str, Any]:
    """Setup AI provider"""
    return utilities.setup_ai_provider(provider)

def get_system_status() -> Dict[str, Any]:
    """Get system status"""
    return utilities.get_system_status()

def get_python_info() -> Dict[str, Any]:
    """Get Python environment info"""
    return utilities.get_python_environment_info()

def load_config(config_file: Union[str, Path]) -> Dict[str, Any]:
    """Load JSON configuration"""
    return utilities.load_json_config(config_file)

def save_config(config: Dict[str, Any], config_file: Union[str, Path]) -> bool:
    """Save JSON configuration"""
    return utilities.save_json_config(config, config_file)

# ============================================================================
# COMMAND LINE INTERFACE
# ============================================================================

def main():
    """Main CLI interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description="DuckBot Consolidated Utilities")
    parser.add_argument("command", choices=[
        "backup", "simple-backup", "unicode-setup", "ai-setup", 
        "system-status", "python-info", "merge-configs"
    ], help="Utility command to run")
    
    # Backup arguments
    parser.add_argument("--source", "-s", help="Source directory for backup")
    parser.add_argument("--output", "-o", help="Output file for backup")
    parser.add_argument("--backup-name", help="Backup name for simple backup")
    
    # AI setup arguments
    parser.add_argument("--provider", "-p", default="lm_studio", 
                       choices=["lm_studio", "openrouter"], help="AI provider to setup")
    
    # Config arguments
    parser.add_argument("--base-config", help="Base configuration file for merging")
    parser.add_argument("--override-config", help="Override configuration file for merging")
    parser.add_argument("--output-config", help="Output configuration file for merging")
    
    args = parser.parse_args()
    
    try:
        if args.command == "backup":
            result = create_backup(args.source, args.output)
            print(json.dumps(result, indent=2))
            
        elif args.command == "simple-backup":
            result = create_simple_backup(args.source, args.backup_name)
            print(json.dumps(result, indent=2))
            
        elif args.command == "unicode-setup":
            success = setup_unicode()
            print(f"Unicode setup: {'SUCCESS' if success else 'FAILED'}")
            
        elif args.command == "ai-setup":
            result = setup_ai_provider(args.provider)
            print(json.dumps(result, indent=2))
            
        elif args.command == "system-status":
            result = get_system_status()
            print(json.dumps(result, indent=2))
            
        elif args.command == "python-info":
            result = get_python_info()
            print(json.dumps(result, indent=2))
            
        elif args.command == "merge-configs":
            if args.base_config and args.override_config:
                base = load_config(args.base_config)
                override = load_config(args.override_config)
                merged = utilities.merge_configs(base, override)
                
                if args.output_config:
                    save_config(merged, args.output_config)
                    print(f"Merged config saved to: {args.output_config}")
                else:
                    print(json.dumps(merged, indent=2))
            else:
                print("Error: --base-config and --override-config required for merge-configs")
                return 1
                
        return 0
        
    except Exception as e:
        logger.error(f"Command failed: {e}")
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())