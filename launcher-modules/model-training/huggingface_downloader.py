#!/usr/bin/env python3
"""
DuckBot Hugging Face Model Downloader
Provides robust model downloading capabilities with authentication,
progress tracking, format conversion, and caching.
"""

import os
import sys
import json
import yaml
import time
import hashlib
import logging
import threading
import asyncio
import requests
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
import pydantic
from pydantic import BaseModel, Field, validator

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from huggingface_hub import (
        HfApi,
        snapshot_download,
        hf_hub_download,
        login,
        whoami,
        model_info,
        list_models,
        HfFolder
    )
    from huggingface_hub.utils import (
        HfHubHTTPError,
        RepositoryNotFoundError,
        EntryNotFoundError
    )
    import transformers
    import torch
    import safetensors
except ImportError as e:
    raise ImportError(f"Required packages missing. Install with: pip install huggingface_hub transformers torch safetensors pydantic. Missing: {e}")

class DownloadStatus(Enum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CONVERTING = "converting"
    CACHED = "cached"

class ModelFormat(Enum):
    HUGGINGFACE = "huggingface"
    GGUF = "gguf"
    GGML = "ggml"
    SAFETENSORS = "safetensors"

@dataclass
class ModelDownloadConfig:
    """Configuration for model downloading"""
    model_id: str
    revision: Optional[str] = None
    token: Optional[str] = None
    local_files_only: bool = False
    cache_dir: Optional[str] = None
    allow_patterns: Optional[List[str]] = None
    ignore_patterns: Optional[List[str]] = None
    max_workers: int = 4
    resume_download: bool = True
    force_download: bool = False
    proxies: Optional[Dict[str, str]] = None
    endpoint: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    convert_to_gguf: bool = False
    gguf_quantization: Optional[str] = None  # e.g., "q4_0", "q5_1", "q8_0"
    validate_checksum: bool = True

@dataclass
class DownloadProgress:
    """Download progress tracking"""
    model_id: str
    status: DownloadStatus
    total_size: int = 0
    downloaded_size: int = 0
    download_speed: float = 0.0
    eta_seconds: float = 0.0
    current_file: str = ""
    total_files: int = 0
    completed_files: int = 0
    error_message: Optional[str] = None
    start_time: float = 0.0
    completion_time: Optional[float] = None

class HuggingFaceAuth:
    """Handles Hugging Face authentication"""

    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv("HUGGINGFACE_TOKEN")
        self.api = HfApi(token=self.token)
        self._validate_token()

    def _validate_token(self):
        """Validate the authentication token"""
        if self.token:
            try:
                user_info = whoami(token=self.token)
                logging.info(f"Authenticated as: {user_info['name']}")
            except Exception as e:
                logging.warning(f"Token validation failed: {e}")
        else:
            logging.info("No Hugging Face token provided - public models only")

    def get_user_info(self) -> Optional[Dict[str, Any]]:
        """Get current user information"""
        if not self.token:
            return None

        try:
            return whoami(token=self.token)
        except Exception as e:
            logging.error(f"Failed to get user info: {e}")
            return None

    def has_access_to_model(self, model_id: str) -> bool:
        """Check if user has access to a specific model"""
        try:
            info = model_info(model_id, token=self.token)
            return not info.gated or bool(self.token)
        except Exception as e:
            logging.error(f"Failed to check model access: {e}")
            return False

    def login_with_token(self, token: str) -> bool:
        """Login with a new token"""
        try:
            login(token)
            self.token = token
            self.api = HfApi(token=token)
            logging.info("Successfully logged in with new token")
            return True
        except Exception as e:
            logging.error(f"Login failed: {e}")
            return False

class ModelCacheManager:
    """Manages model caching and storage"""

    def __init__(self, cache_dir: Optional[str] = None):
        self.cache_dir = Path(cache_dir or os.path.expanduser("~/.cache/duckbot_models"))
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.cache_dir / "cache_metadata.json"
        self.lock = threading.Lock()
        self._load_metadata()

    def _load_metadata(self):
        """Load cache metadata from disk"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    self.metadata = json.load(f)
            except Exception as e:
                logging.warning(f"Failed to load cache metadata: {e}")
                self.metadata = {}
        else:
            self.metadata = {}

    def _save_metadata(self):
        """Save cache metadata to disk"""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f, indent=2)
        except Exception as e:
            logging.error(f"Failed to save cache metadata: {e}")

    def get_cached_model_path(self, model_id: str, revision: str = "main") -> Optional[Path]:
        """Get path to cached model if it exists"""
        cache_key = f"{model_id}_{revision}"
        with self.lock:
            if cache_key in self.metadata:
                cache_path = Path(self.metadata[cache_key]["path"])
                if cache_path.exists():
                    return cache_path
                else:
                    # Remove stale metadata
                    del self.metadata[cache_key]
                    self._save_metadata()
        return None

    def add_to_cache(self, model_id: str, revision: str, path: Path, format_type: str = "huggingface"):
        """Add model to cache"""
        cache_key = f"{model_id}_{revision}"
        with self.lock:
            self.metadata[cache_key] = {
                "path": str(path),
                "model_id": model_id,
                "revision": revision,
                "format": format_type,
                "timestamp": time.time(),
                "size": self._get_directory_size(path)
            }
            self._save_metadata()

    def _get_directory_size(self, path: Path) -> int:
        """Calculate total size of directory"""
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                try:
                    total_size += os.path.getsize(file_path)
                except OSError:
                    continue
        return total_size

    def list_cached_models(self) -> List[Dict[str, Any]]:
        """List all cached models"""
        with self.lock:
            models = []
            for cache_key, info in self.metadata.items():
                cache_path = Path(info["path"])
                if cache_path.exists():
                    size_mb = info["size"] / (1024 * 1024)
                    models.append({
                        "model_id": info["model_id"],
                        "revision": info["revision"],
                        "format": info["format"],
                        "path": str(cache_path),
                        "size_mb": f"{size_mb:.1f}",
                        "timestamp": info["timestamp"]
                    })
            return models

    def clear_cache(self, model_id: Optional[str] = None):
        """Clear cache for specific model or all models"""
        with self.lock:
            if model_id:
                # Clear specific model
                keys_to_remove = [k for k in self.metadata.keys() if k.startswith(model_id)]
                for key in keys_to_remove:
                    cache_path = Path(self.metadata[key]["path"])
                    if cache_path.exists():
                        shutil.rmtree(cache_path)
                    del self.metadata[key]
            else:
                # Clear all cache
                for info in self.metadata.values():
                    cache_path = Path(info["path"])
                    if cache_path.exists():
                        shutil.rmtree(cache_path)
                self.metadata = {}

            self._save_metadata()

class GGUFConverter:
    """Handles conversion of Hugging Face models to GGUF format"""

    def __init__(self, llama_cpp_path: Optional[str] = None):
        self.llama_cpp_path = llama_cpp_path or self._find_llama_cpp()

    def _find_llama_cpp(self) -> Optional[str]:
        """Find llama.cpp installation"""
        common_paths = [
            "/usr/local/bin",
            "/opt/llama.cpp",
            Path.home() / "llama.cpp",
            Path.cwd() / "llama.cpp"
        ]

        for path in common_paths:
            convert_script = Path(path) / "convert.py"
            if convert_script.exists():
                return str(path)

        return None

    def can_convert(self) -> bool:
        """Check if conversion is possible"""
        return bool(self.llama_cpp_path)

    def convert_to_gguf(
        self,
        model_path: Path,
        output_path: Path,
        quantization: Optional[str] = None,
        progress_callback: Optional[callable] = None
    ) -> bool:
        """Convert Hugging Face model to GGUF format"""

        if not self.can_convert():
            logging.error("llama.cpp not found - cannot convert to GGUF")
            return False

        try:
            convert_script = Path(self.llama_cpp_path) / "convert.py"
            if not convert_script.exists():
                logging.error(f"convert.py not found at {convert_script}")
                return False

            # Prepare command
            cmd = [
                sys.executable, str(convert_script),
                str(model_path),
                "--outfile", str(output_path)
            ]

            if quantization:
                cmd.extend(["--outtype", quantization])

            # Run conversion
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )

            # Monitor progress
            for line in process.stdout:
                if progress_callback:
                    progress_callback(line.strip())
                logging.info(f"Conversion: {line.strip()}")

            process.wait()

            if process.returncode == 0:
                logging.info(f"Successfully converted to GGUF: {output_path}")
                return True
            else:
                logging.error(f"Conversion failed with return code: {process.returncode}")
                return False

        except Exception as e:
            logging.error(f"Conversion failed: {e}")
            return False

class ModelDownloader:
    """Main model downloader class"""

    def __init__(self, config: Optional[ModelDownloadConfig] = None):
        self.config = config or ModelDownloadConfig(model_id="")
        self.auth = HuggingFaceAuth(config.token if config else None)
        self.cache_manager = ModelCacheManager(config.cache_dir if config else None)
        self.converter = GGUFConverter()
        self.download_progress: Dict[str, DownloadProgress] = {}
        self.active_downloads: Dict[str, threading.Thread] = {}
        self.lock = threading.Lock()

        # Setup logging
        self.logger = logging.getLogger('DuckBot.ModelDownloader')
        self.logger.setLevel(logging.INFO)

        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def download_model(
        self,
        model_id: str,
        config: Optional[ModelDownloadConfig] = None,
        progress_callback: Optional[callable] = None
    ) -> Optional[Path]:
        """Download a model from Hugging Face"""

        config = config or self.config
        config.model_id = model_id

        # Check cache first
        if not config.force_download:
            cached_path = self.cache_manager.get_cached_model_path(
                model_id, config.revision or "main"
            )
            if cached_path:
                self.logger.info(f"Model found in cache: {cached_path}")
                return cached_path

        # Create progress tracking
        progress = DownloadProgress(
            model_id=model_id,
            status=DownloadStatus.PENDING,
            start_time=time.time()
        )

        with self.lock:
            self.download_progress[model_id] = progress

        try:
            # Start download in background thread
            def download_thread():
                try:
                    self._download_model_threaded(config, progress, progress_callback)
                except Exception as e:
                    with self.lock:
                        progress.status = DownloadStatus.FAILED
                        progress.error_message = str(e)
                    self.logger.error(f"Download failed: {e}")

            thread = threading.Thread(target=download_thread, daemon=True)
            thread.start()

            with self.lock:
                self.active_downloads[model_id] = thread

            # Wait for completion
            thread.join()

            # Return result
            if progress.status == DownloadStatus.COMPLETED:
                # Return the cached path
                cached_path = self.cache_manager.get_cached_model_path(
                    model_id, config.revision or "main"
                )
                return cached_path
            else:
                return None

        except Exception as e:
            self.logger.error(f"Download failed: {e}")
            return None

    def _download_model_threaded(
        self,
        config: ModelDownloadConfig,
        progress: DownloadProgress,
        progress_callback: Optional[callable] = None
    ):
        """Internal download method running in thread"""

        with self.lock:
            progress.status = DownloadStatus.DOWNLOADING

        try:
            # Check access
            if not self.auth.has_access_to_model(config.model_id):
                raise Exception(f"No access to model: {config.model_id}")

            # Prepare download parameters
            download_kwargs = {
                "repo_id": config.model_id,
                "revision": config.revision,
                "local_files_only": config.local_files_only,
                "cache_dir": config.cache_dir,
                "resume_download": config.resume_download,
                "force_download": config.force_download,
                "proxies": config.proxies,
                "endpoint": config.endpoint,
                "headers": config.headers,
                "max_workers": config.max_workers,
                "tqdm_class": self._create_progress_callback(progress, progress_callback)
            }

            if config.token:
                download_kwargs["token"] = config.token

            if config.allow_patterns:
                download_kwargs["allow_patterns"] = config.allow_patterns

            if config.ignore_patterns:
                download_kwargs["ignore_patterns"] = config.ignore_patterns

            # Download model
            model_path = snapshot_download(**download_kwargs)

            # Convert to GGUF if requested
            if config.convert_to_gguf:
                with self.lock:
                    progress.status = DownloadStatus.CONVERTING

                output_path = Path(model_path).parent / f"{Path(model_path).name}.gguf"

                def conversion_callback(line):
                    if progress_callback:
                        progress_callback({
                            "model_id": config.model_id,
                            "status": "converting",
                            "message": line
                        })

                if self.converter.convert_to_gguf(
                    Path(model_path),
                    output_path,
                    config.gguf_quantization,
                    conversion_callback
                ):
                    # Add to cache with GGUF format
                    self.cache_manager.add_to_cache(
                        config.model_id,
                        config.revision or "main",
                        output_path,
                        "gguf"
                    )

                    # Clean up original model
                    shutil.rmtree(model_path)
                else:
                    raise Exception("GGUF conversion failed")
            else:
                # Add to cache with original format
                self.cache_manager.add_to_cache(
                    config.model_id,
                    config.revision or "main",
                    Path(model_path),
                    "huggingface"
                )

            # Update progress
            with self.lock:
                progress.status = DownloadStatus.COMPLETED
                progress.completion_time = time.time()

            self.logger.info(f"Successfully downloaded: {config.model_id}")

        except Exception as e:
            with self.lock:
                progress.status = DownloadStatus.FAILED
                progress.error_message = str(e)
            raise

    def _create_progress_callback(self, progress: DownloadProgress, user_callback: Optional[callable]):
        """Create tqdm callback for progress tracking"""

        class ProgressCallback:
            def __init__(self, progress, user_callback):
                self.progress = progress
                self.user_callback = user_callback
                self.start_time = time.time()

            def __call__(self, current, total, unit_scale=True, unit=None):
                with progress._lock if hasattr(progress, '_lock') else progress.lock:
                    self.progress.downloaded_size = current
                    self.progress.total_size = total

                    if total > 0:
                        self.progress.status = DownloadStatus.DOWNLOADING

                        # Calculate speed
                        elapsed = time.time() - self.start_time
                        if elapsed > 0:
                            self.progress.download_speed = current / elapsed

                        # Calculate ETA
                        if self.progress.download_speed > 0:
                            remaining = total - current
                            self.progress.eta_seconds = remaining / self.progress.download_speed

                if self.user_callback:
                    self.user_callback({
                        "model_id": self.progress.model_id,
                        "status": self.progress.status.value,
                        "downloaded": current,
                        "total": total,
                        "speed": self.progress.download_speed,
                        "eta": self.progress.eta_seconds
                    })

        # Add lock to progress if not present
        if not hasattr(progress, '_lock'):
            progress._lock = threading.Lock()

        return ProgressCallback(progress, user_callback)

    def get_download_progress(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get download progress for a model"""
        with self.lock:
            if model_id in self.download_progress:
                progress = self.download_progress[model_id]
                return {
                    "model_id": progress.model_id,
                    "status": progress.status.value,
                    "total_size": progress.total_size,
                    "downloaded_size": progress.downloaded_size,
                    "download_speed": progress.download_speed,
                    "eta_seconds": progress.eta_seconds,
                    "current_file": progress.current_file,
                    "total_files": progress.total_files,
                    "completed_files": progress.completed_files,
                    "error_message": progress.error_message,
                    "start_time": progress.start_time,
                    "completion_time": progress.completion_time
                }
        return None

    def list_active_downloads(self) -> List[Dict[str, Any]]:
        """List all active downloads"""
        with self.lock:
            active_downloads = []
            for model_id, progress in self.download_progress.items():
                if progress.status in [DownloadStatus.DOWNLOADING, DownloadStatus.PENDING]:
                    active_downloads.append({
                        "model_id": model_id,
                        "status": progress.status.value,
                        "downloaded_size": progress.downloaded_size,
                        "total_size": progress.total_size,
                        "download_speed": progress.download_speed
                    })
            return active_downloads

    def pause_download(self, model_id: str) -> bool:
        """Pause a download"""
        # Note: huggingface_hub doesn't support pausing mid-download
        # This would require more complex implementation
        self.logger.warning("Pause functionality not implemented - use resume_download=True")
        return False

    def cancel_download(self, model_id: str) -> bool:
        """Cancel a download"""
        with self.lock:
            if model_id in self.active_downloads:
                # Note: Thread cancellation is complex, this is a simplified approach
                self.logger.info(f"Canceling download for {model_id}")
                progress = self.download_progress.get(model_id)
                if progress:
                    progress.status = DownloadStatus.FAILED
                    progress.error_message = "Download canceled by user"
                return True
        return False

    def search_models(
        self,
        query: str,
        limit: int = 10,
        model_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search for models on Hugging Face"""
        try:
            models = list_models(
                search=query,
                limit=limit,
                token=self.auth.token
            )

            results = []
            for model in models:
                model_info = {
                    "id": model.id,
                    "author": model.author,
                    "downloads": model.downloads,
                    "likes": model.likes,
                    "tags": model.tags,
                    "pipeline_tag": model.pipeline_tag,
                    "library_name": model.library_name,
                    "created_at": model.created_at.isoformat() if model.created_at else None
                }

                # Filter by model type if specified
                if model_type:
                    if model_type.lower() in [tag.lower() for tag in model.tags]:
                        results.append(model_info)
                else:
                    results.append(model_info)

            return results

        except Exception as e:
            self.logger.error(f"Model search failed: {e}")
            return []

    def get_model_info(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a model"""
        try:
            info = model_info(model_id, token=self.auth.token)

            return {
                "id": info.id,
                "author": info.author,
                "sha": info.sha,
                "last_modified": info.last_modified.isoformat() if info.last_modified else None,
                "tags": info.tags,
                "pipeline_tag": info.pipeline_tag,
                "library_name": info.library_name,
                "downloads": info.downloads,
                "likes": info.likes,
                "model_index": info.model_index,
                "card_data": info.card_data,
                "siblings": [{"filename": s.rfilename, "size": s.size} for s in info.siblings] if info.siblings else [],
                "gated": info.gated,
                "private": info.private
            }

        except Exception as e:
            self.logger.error(f"Failed to get model info: {e}")
            return None

    def get_cached_models(self) -> List[Dict[str, Any]]:
        """Get list of cached models"""
        return self.cache_manager.list_cached_models()

    def clear_cache(self, model_id: Optional[str] = None):
        """Clear model cache"""
        self.cache_manager.clear_cache(model_id)
        self.logger.info(f"Cleared cache for model: {model_id}" if model_id else "Cleared all cache")

    def validate_downloaded_model(self, model_path: Path, validate_loading: bool = False) -> Dict[str, Any]:
        """Validate a downloaded model"""
        validator = ModelValidator()

        # Determine model format
        if model_path.is_file() and model_path.suffix.lower() == '.gguf':
            return validator.validate_gguf_model(model_path)
        else:
            validation_result = validator.validate_model_structure(model_path)

            # Check compatibility with training requirements
            requirements = {
                "model_type": "auto",  # Will be determined from config
                "architecture": "AutoModel",
                "min_vocab_size": 1000,
                "max_model_size_gb": 50
            }

            compatibility_result = validator.check_model_compatibility(model_path, requirements)
            validation_result["compatible"] = compatibility_result["compatible"]
            validation_result["issues"].extend(compatibility_result["issues"])
            validation_result["warnings"].extend(compatibility_result["warnings"])

            # Test model loading if requested
            if validate_loading:
                loading_result = validator.validate_model_loading(model_path)
                validation_result["can_load"] = loading_result["can_load"]
                validation_result["loading_errors"] = loading_result["errors"]
                validation_result["loading_warnings"] = loading_result["warnings"]

            return validation_result

class ModelValidator:
    """Validates model integrity and structure"""

    def __init__(self):
        self.logger = logging.getLogger('DuckBot.ModelValidator')

    def validate_model_structure(self, model_path: Path) -> Dict[str, Any]:
        """Validate the basic structure of a downloaded model"""
        validation_result = {
            "valid": True,
            "issues": [],
            "warnings": [],
            "model_info": {}
        }

        try:
            # Check if directory exists
            if not model_path.exists():
                validation_result["valid"] = False
                validation_result["issues"].append("Model directory does not exist")
                return validation_result

            # Check for essential files
            essential_files = ["config.json"]
            for file_name in essential_files:
                file_path = model_path / file_name
                if not file_path.exists():
                    validation_result["valid"] = False
                    validation_result["issues"].append(f"Missing essential file: {file_name}")

            # Validate config.json if it exists
            config_path = model_path / "config.json"
            if config_path.exists():
                try:
                    with open(config_path, 'r') as f:
                        config = json.load(f)

                    validation_result["model_info"]["model_type"] = config.get("model_type")
                    validation_result["model_info"]["architecture"] = config.get("architectures", ["Unknown"])[0] if config.get("architectures") else "Unknown"

                    # Check for required config fields
                    required_fields = ["model_type"]
                    for field in required_fields:
                        if field not in config:
                            validation_result["warnings"].append(f"Missing config field: {field}")

                except Exception as e:
                    validation_result["valid"] = False
                    validation_result["issues"].append(f"Invalid config.json: {e}")

            # Check for model weights
            weight_files = list(model_path.glob("*.bin")) + list(model_path.glob("*.safetensors"))
            if not weight_files:
                validation_result["warnings"].append("No weight files found")

            # Calculate total size
            total_size = sum(f.stat().st_size for f in model_path.rglob('*') if f.is_file())
            validation_result["model_info"]["total_size_bytes"] = total_size
            validation_result["model_info"]["total_size_mb"] = round(total_size / (1024 * 1024), 2)

            # Check file integrity for weight files
            for weight_file in weight_files:
                try:
                    # Basic file integrity check
                    with open(weight_file, 'rb') as f:
                        f.read(1024)  # Try to read first KB
                except Exception as e:
                    validation_result["warnings"].append(f"Weight file may be corrupted: {weight_file.name} - {e}")

        except Exception as e:
            validation_result["valid"] = False
            validation_result["issues"].append(f"Validation error: {e}")

        return validation_result

    def validate_gguf_model(self, model_path: Path) -> Dict[str, Any]:
        """Validate GGUF format model"""
        validation_result = {
            "valid": True,
            "issues": [],
            "warnings": [],
            "model_info": {}
        }

        try:
            if not model_path.exists():
                validation_result["valid"] = False
                validation_result["issues"].append("GGUF file does not exist")
                return validation_result

            # Basic GGUF header validation
            with open(model_path, 'rb') as f:
                header = f.read(4)
                if header != b'GGUF':
                    validation_result["valid"] = False
                    validation_result["issues"].append("Invalid GGUF header")

            # Get file size
            file_size = model_path.stat().st_size
            validation_result["model_info"]["file_size_bytes"] = file_size
            validation_result["model_info"]["file_size_mb"] = round(file_size / (1024 * 1024), 2)

            # Check if file is readable
            try:
                with open(model_path, 'rb') as f:
                    f.seek(0, 2)  # Seek to end
                    f.seek(0)  # Seek back to beginning
            except Exception as e:
                validation_result["warnings"].append(f"GGUF file read issue: {e}")

        except Exception as e:
            validation_result["valid"] = False
            validation_result["issues"].append(f"GGUF validation error: {e}")

        return validation_result

    def check_model_compatibility(self, model_path: Path, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Check if model meets specific requirements"""
        compatibility_result = {
            "compatible": True,
            "issues": [],
            "warnings": []
        }

        try:
            # Load model config
            config_path = model_path / "config.json"
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = json.load(f)

                # Check model type
                if "model_type" in requirements:
                    if config.get("model_type") != requirements["model_type"]:
                        compatibility_result["compatible"] = False
                        compatibility_result["issues"].append(
                            f"Model type mismatch: expected {requirements['model_type']}, got {config.get('model_type')}"
                        )

                # Check architecture
                if "architecture" in requirements:
                    architectures = config.get("architectures", [])
                    if requirements["architecture"] not in architectures:
                        compatibility_result["warnings"].append(
                            f"Architecture may not be optimal: expected {requirements['architecture']}, got {architectures}"
                        )

                # Check vocabulary size
                if "min_vocab_size" in requirements:
                    vocab_size = config.get("vocab_size", 0)
                    if vocab_size < requirements["min_vocab_size"]:
                        compatibility_result["warnings"].append(
                            f"Vocabulary size may be too small: {vocab_size} < {requirements['min_vocab_size']}"
                        )

                # Check model size
                if "max_model_size_gb" in requirements:
                    total_size = sum(f.stat().st_size for f in model_path.rglob('*') if f.is_file())
                    max_size_bytes = requirements["max_model_size_gb"] * 1024 * 1024 * 1024
                    if total_size > max_size_bytes:
                        compatibility_result["warnings"].append(
                            f"Model size exceeds limit: {total_size / (1024**3):.2f} GB > {requirements['max_model_size_gb']} GB"
                        )

        except Exception as e:
            compatibility_result["compatible"] = False
            compatibility_result["issues"].append(f"Compatibility check error: {e}")

        return compatibility_result

    def verify_checksums(self, model_path: Path, checksums: Dict[str, str]) -> Dict[str, Any]:
        """Verify file checksums against expected values"""
        checksum_result = {
            "valid": True,
            "verified_files": [],
            "failed_files": [],
            "missing_files": []
        }

        try:
            for filename, expected_checksum in checksums.items():
                file_path = model_path / filename

                if not file_path.exists():
                    checksum_result["missing_files"].append(filename)
                    checksum_result["valid"] = False
                    continue

                # Calculate checksum
                actual_checksum = self._calculate_file_checksum(file_path)

                if actual_checksum == expected_checksum:
                    checksum_result["verified_files"].append(filename)
                else:
                    checksum_result["failed_files"].append({
                        "filename": filename,
                        "expected": expected_checksum,
                        "actual": actual_checksum
                    })
                    checksum_result["valid"] = False

        except Exception as e:
            checksum_result["valid"] = False
            checksum_result["failed_files"].append({
                "filename": "general",
                "error": str(e)
            })

        return checksum_result

    def _calculate_file_checksum(self, file_path: Path, algorithm: str = "sha256") -> str:
        """Calculate checksum for a file"""
        hash_func = hashlib.new(algorithm)

        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_func.update(chunk)

        return hash_func.hexdigest()

    def validate_model_loading(self, model_path: Path) -> Dict[str, Any]:
        """Test if model can be loaded by transformers library"""
        loading_result = {
            "can_load": False,
            "warnings": [],
            "errors": [],
            "model_info": {}
        }

        try:
            # Try to load the model
            from transformers import AutoModel, AutoConfig

            config = AutoConfig.from_pretrained(str(model_path))
            loading_result["model_info"]["config_loaded"] = True
            loading_result["model_info"]["model_type"] = config.model_type
            loading_result["model_info"]["architecture"] = config.architectures[0] if config.architectures else "Unknown"

            # Try to load the actual model (this might require significant memory)
            try:
                model = AutoModel.from_pretrained(str(model_path))
                loading_result["can_load"] = True
                loading_result["model_info"]["model_loaded"] = True
                loading_result["model_info"]["num_parameters"] = sum(p.numel() for p in model.parameters())

                # Clean up
                del model
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()

            except Exception as e:
                loading_result["warnings"].append(f"Model loading test failed (may be due to memory): {e}")

        except Exception as e:
            loading_result["errors"].append(f"Model validation failed: {e}")

        return loading_result

class ConfigManager:
    """Manages configuration for the model downloader"""

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or Path(__file__).parent / "config" / "downloader_config.json"
        self.config = self._load_default_config()
        self._load_config()

    def _load_default_config(self):
        """Load default configuration"""
        return {
            "huggingface": {
                "token": None,
                "endpoint": None,
                "max_workers": 4,
                "timeout": 300,
                "retry_attempts": 3
            },
            "download": {
                "chunk_size": 1024 * 1024,  # 1MB chunks
                "max_retries": 3,
                "retry_delay": 1.0,
                "resume_download": True,
                "force_download": False
            },
            "cache": {
                "default_dir": os.path.expanduser("~/.cache/duckbot_models"),
                "max_cache_size_gb": 100,
                "cache_cleanup_days": 30
            },
            "conversion": {
                "convert_to_gguf": False,
                "default_quantization": "q4_0",
                "llama_cpp_path": None
            },
            "validation": {
                "validate_checksums": True,
                "validate_structure": True,
                "skip_files_on_error": False,
                "test_model_loading": False
            },
            "security": {
                "token_env_var": "HUGGINGFACE_TOKEN",
                "allow_private_models": True,
                "verify_ssl": True
            }
        }

    def _load_config(self):
        """Load configuration from file"""
        if Path(self.config_path).exists():
            try:
                with open(self.config_path, 'r') as f:
                    file_config = json.load(f)
                    self._merge_config(file_config)
            except Exception as e:
                logging.warning(f"Failed to load config file: {e}")

    def _merge_config(self, file_config: Dict[str, Any]):
        """Merge file configuration with defaults"""
        def merge_dict(default: Dict, override: Dict) -> Dict:
            result = default.copy()
            for key, value in override.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = merge_dict(result[key], value)
                else:
                    result[key] = value
            return result

        self.config = merge_dict(self.config, file_config)

    def save_config(self):
        """Save current configuration to file"""
        try:
            # Ensure directory exists
            Path(self.config_path).parent.mkdir(parents=True, exist_ok=True)

            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            logging.error(f"Failed to save config: {e}")

    def get_huggingface_token(self) -> Optional[str]:
        """Get Hugging Face token from config or environment"""
        token = self.config["huggingface"]["token"]
        if not token:
            token = os.getenv(self.config["security"]["token_env_var"])
        return token

    def get_cache_dir(self) -> str:
        """Get cache directory"""
        return self.config["cache"]["default_dir"]

    def is_valid_quantization(self, quantization: str) -> bool:
        """Check if quantization is valid"""
        valid_quantizations = self.get_supported_quantizations()
        return quantization.lower() in [q.lower() for q in valid_quantizations]

    def get_supported_quantizations(self) -> List[str]:
        """Get list of supported quantizations"""
        return [
            "f32", "f16", "q8_0", "q5_1", "q5_0", "q4_1", "q4_0",
            "q3_k", "q4_k", "q5_k", "q6_k", "q8_k"
        ]

    def validate_config(self) -> List[str]:
        """Validate current configuration and return issues"""
        issues = []

        # Validate numeric ranges
        if self.config["huggingface"]["max_workers"] <= 0:
            issues.append("max_workers must be positive")

        if self.config["huggingface"]["timeout"] <= 0:
            issues.append("timeout must be positive")

        if not (512 * 1024 <= self.config["download"]["chunk_size"] <= 10 * 1024 * 1024):
            issues.append("chunk_size should be between 512KB and 10MB")

        # Validate paths
        if self.config["conversion"]["llama_cpp_path"]:
            if not Path(self.config["conversion"]["llama_cpp_path"]).exists():
                issues.append("llama_cpp_path does not exist")

        return issues

    def get_download_config_for_model(self, model_id: str, overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get download configuration for a specific model"""
        config = {
            "model_id": model_id,
            "token": self.get_huggingface_token(),
            "cache_dir": self.get_cache_dir(),
            "max_workers": self.config["huggingface"]["max_workers"],
            "resume_download": self.config["download"]["resume_download"],
            "force_download": self.config["download"]["force_download"],
            "convert_to_gguf": self.config["conversion"]["convert_to_gguf"],
            "gguf_quantization": self.config["conversion"]["default_quantization"],
            "validate_checksum": self.config["validation"]["validate_checksums"]
        }

        # Apply overrides
        if overrides:
            config.update(overrides)

        return config

def main():
    """Main entry point for testing"""
    import argparse

    parser = argparse.ArgumentParser(description="DuckBot Hugging Face Model Downloader")
    parser.add_argument("model_id", help="Hugging Face model ID")
    parser.add_argument("--token", help="Hugging Face access token")
    parser.add_argument("--revision", help="Model revision")
    parser.add_argument("--cache-dir", help="Cache directory")
    parser.add_argument("--convert-gguf", action="store_true", help="Convert to GGUF format")
    parser.add_argument("--quantization", help="GGUF quantization (e.g., q4_0, q5_1, q8_0)")
    parser.add_argument("--list-cached", action="store_true", help="List cached models")
    parser.add_argument("--clear-cache", help="Clear cache (specific model or 'all')")
    parser.add_argument("--search", help="Search for models")

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(level=logging.INFO)

    downloader = ModelDownloader()

    if args.list_cached:
        cached = downloader.get_cached_models()
        print("Cached models:")
        for model in cached:
            print(f"  {model['model_id']} ({model['format']}, {model['size_mb']} MB)")
        return

    if args.clear_cache:
        downloader.clear_cache(args.clear_cache if args.clear_cache.lower() != 'all' else None)
        return

    if args.search:
        results = downloader.search_models(args.search)
        print(f"Search results for '{args.search}':")
        for model in results:
            print(f"  {model['id']} - {model.get('author', 'Unknown')} ({model.get('downloads', 0)} downloads)")
        return

    # Download model
    config = ModelDownloadConfig(
        model_id=args.model_id,
        token=args.token,
        revision=args.revision,
        cache_dir=args.cache_dir,
        convert_to_gguf=args.convert_gguf,
        gguf_quantization=args.quantization
    )

    def progress_callback(info):
        print(f"Progress: {info}")

    print(f"Downloading model: {args.model_id}")
    result = downloader.download_model(args.model_id, config, progress_callback)

    if result:
        print(f"Model downloaded to: {result}")
    else:
        print("Download failed")

if __name__ == "__main__":
    main()