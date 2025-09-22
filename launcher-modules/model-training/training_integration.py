#!/usr/bin/env python3
"""
Model Training Integration with Hugging Face Downloader
Integrates the Hugging Face model downloader with the existing training infrastructure.
"""

import os
import sys
import json
import logging
import asyncio
import threading
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from huggingface_downloader import (
    ModelDownloader,
    ModelDownloadConfig,
    DownloadStatus,
    ModelValidator,
    ConfigManager
)

class ModelSource(Enum):
    """Model source types"""
    HUGGINGFACE = "huggingface"
    LOCAL = "local"
    CACHE = "cache"

@dataclass
class ModelDownloadRequest:
    """Request for model download"""
    model_id: str
    source: ModelSource
    config: Optional[Dict[str, Any]] = None
    priority: int = 0  # Higher numbers = higher priority
    callback: Optional[Callable] = None
    user_data: Optional[Dict[str, Any]] = None

@dataclass
class ModelInfo:
    """Information about a downloaded model"""
    model_id: str
    source: ModelSource
    path: Path
    format_type: str
    size_mb: float
    validation_result: Dict[str, Any]
    download_time: float
    metadata: Dict[str, Any]

class TrainingModelManager:
    """Manages models for training, integrating with Hugging Face downloader"""

    def __init__(self, config_path: Optional[str] = None):
        self.config_manager = ConfigManager(config_path)
        self.downloader = ModelDownloader()
        self.validator = ModelValidator()

        self.models: Dict[str, ModelInfo] = {}
        self.download_queue: List[ModelDownloadRequest] = []
        self.active_downloads: Dict[str, threading.Thread] = {}
        self.lock = threading.Lock()

        self.logger = logging.getLogger('DuckBot.TrainingModelManager')
        self.logger.setLevel(logging.INFO)

        # Setup logging
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

        # Load existing models from cache
        self._load_cached_models()

        # Start queue processor
        self.queue_processor = threading.Thread(target=self._process_download_queue, daemon=True)
        self.queue_processor.start()

    def _load_cached_models(self):
        """Load models from cache"""
        cached_models = self.downloader.get_cached_models()
        for model_info in cached_models:
            model_path = Path(model_info["path"])
            if model_path.exists():
                # Basic validation
                validation_result = self.validator.validate_model_structure(model_path)

                model = ModelInfo(
                    model_id=model_info["model_id"],
                    source=ModelSource.CACHE,
                    path=model_path,
                    format_type=model_info["format"],
                    size_mb=float(model_info["size_mb"]),
                    validation_result=validation_result,
                    download_time=model_info.get("timestamp", 0),
                    metadata=model_info
                )

                self.models[model_info["model_id"]] = model
                self.logger.info(f"Loaded cached model: {model_info['model_id']}")

    def download_model_for_training(
        self,
        model_id: str,
        config: Optional[Dict[str, Any]] = None,
        priority: int = 0,
        callback: Optional[Callable] = None
    ) -> bool:
        """Download a model for training purposes"""

        # Check if model is already available
        if model_id in self.models:
            model_info = self.models[model_id]
            if model_info.validation_result.get("valid", False):
                self.logger.info(f"Model already available: {model_id}")
                if callback:
                    callback({
                        "status": "already_available",
                        "model_id": model_id,
                        "path": str(model_info.path)
                    })
                return True

        # Create download request
        request = ModelDownloadRequest(
            model_id=model_id,
            source=ModelSource.HUGGINGFACE,
            config=config or {},
            priority=priority,
            callback=callback
        )

        # Add to queue
        with self.lock:
            self.download_queue.append(request)
            # Sort by priority (descending)
            self.download_queue.sort(key=lambda x: x.priority, reverse=True)

        self.logger.info(f"Added model to download queue: {model_id}")
        return True

    def get_available_models(self) -> List[Dict[str, Any]]:
        """Get list of available models"""
        models_list = []
        for model_id, model_info in self.models.items():
            model_dict = {
                "model_id": model_id,
                "source": model_info.source.value,
                "path": str(model_info.path),
                "format": model_info.format_type,
                "size_mb": model_info.size_mb,
                "valid": model_info.validation_result.get("valid", False),
                "compatible": model_info.validation_result.get("compatible", True),
                "issues": model_info.validation_result.get("issues", []),
                "warnings": model_info.validation_result.get("warnings", []),
                "download_time": model_info.download_time
            }
            models_list.append(model_dict)

        return models_list

    def get_model_path(self, model_id: str) -> Optional[Path]:
        """Get path to a downloaded model"""
        model_info = self.models.get(model_id)
        return model_info.path if model_info else None

    def validate_model_for_training(self, model_id: str, requirements: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Validate a model for training suitability"""
        model_info = self.models.get(model_id)
        if not model_info:
            return {"valid": False, "error": "Model not found"}

        # Start with existing validation result
        result = model_info.validation_result.copy()

        # Check training-specific requirements
        if requirements:
            compatibility_result = self.validator.check_model_compatibility(
                model_info.path, requirements
            )
            result["compatible"] = compatibility_result["compatible"]
            result["training_issues"] = compatibility_result["issues"]
            result["training_warnings"] = compatibility_result["warnings"]

        return result

    def remove_model(self, model_id: str) -> bool:
        """Remove a model from the system"""
        model_info = self.models.get(model_id)
        if not model_info:
            return False

        try:
            # Remove from cache
            self.downloader.clear_cache(model_id)

            # Remove from memory
            del self.models[model_id]

            self.logger.info(f"Removed model: {model_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to remove model {model_id}: {e}")
            return False

    def get_download_status(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get download status for a model"""
        # Check if model is already downloaded
        if model_id in self.models:
            return {
                "status": "completed",
                "model_id": model_id,
                "progress": 100.0
            }

        # Check if model is in active downloads
        progress = self.downloader.get_download_progress(model_id)
        if progress:
            return progress

        # Check if model is in queue
        with self.lock:
            for request in self.download_queue:
                if request.model_id == model_id:
                    return {
                        "status": "queued",
                        "model_id": model_id,
                        "priority": request.priority
                    }

        return None

    def _process_download_queue(self):
        """Process the download queue"""
        while True:
            try:
                with self.lock:
                    if not self.download_queue:
                        # Queue is empty, wait
                        continue

                    # Get highest priority request
                    request = self.download_queue.pop(0)

                # Download the model
                self._download_model(request)

            except Exception as e:
                self.logger.error(f"Error processing download queue: {e}")
                import time
                time.sleep(1)  # Prevent busy waiting

    def _download_model(self, request: ModelDownloadRequest):
        """Download a single model"""
        try:
            self.logger.info(f"Starting download: {request.model_id}")

            # Get download config
            download_config_dict = self.config_manager.get_download_config_for_model(
                request.model_id, request.config
            )

            # Create download config object
            download_config = ModelDownloadConfig(**download_config_dict)

            # Progress callback
            def progress_callback(info):
                self.logger.debug(f"Download progress {request.model_id}: {info}")
                if request.callback:
                    request.callback({
                        "status": "downloading",
                        "model_id": request.model_id,
                        "progress": info,
                        "user_data": request.user_data
                    })

            # Download the model
            model_path = self.downloader.download_model(
                request.model_id, download_config, progress_callback
            )

            if model_path:
                # Validate the downloaded model
                validation_result = self.validator.validate_model_structure(model_path)

                # Get model size
                total_size = sum(f.stat().st_size for f in model_path.rglob('*') if f.is_file())
                size_mb = total_size / (1024 * 1024)

                # Create model info
                model_info = ModelInfo(
                    model_id=request.model_id,
                    source=request.source,
                    path=model_path,
                    format_type="huggingface" if not download_config.convert_to_gguf else "gguf",
                    size_mb=size_mb,
                    validation_result=validation_result,
                    download_time=asyncio.get_event_loop().time() if asyncio.get_event_loop().is_running() else time.time(),
                    metadata={"config": download_config_dict}
                )

                # Store model info
                with self.lock:
                    self.models[request.model_id] = model_info

                self.logger.info(f"Successfully downloaded and validated: {request.model_id}")

                # Call callback
                if request.callback:
                    request.callback({
                        "status": "completed",
                        "model_id": request.model_id,
                        "path": str(model_path),
                        "validation": validation_result,
                        "user_data": request.user_data
                    })

            else:
                self.logger.error(f"Download failed: {request.model_id}")
                if request.callback:
                    request.callback({
                        "status": "failed",
                        "model_id": request.model_id,
                        "error": "Download failed",
                        "user_data": request.user_data
                    })

        except Exception as e:
            self.logger.error(f"Download error for {request.model_id}: {e}")
            if request.callback:
                request.callback({
                    "status": "failed",
                    "model_id": request.model_id,
                    "error": str(e),
                    "user_data": request.user_data
                })

    def get_training_models_by_type(self, model_type: str) -> List[Dict[str, Any]]:
        """Get models suitable for specific training type"""
        suitable_models = []

        for model_id, model_info in self.models.items():
            validation = model_info.validation_result

            # Check if model is valid and has model type info
            if validation.get("valid", False):
                model_info_dict = validation.get("model_info", {})
                if model_info_dict.get("model_type") == model_type:
                    suitable_models.append({
                        "model_id": model_id,
                        "path": str(model_info.path),
                        "architecture": model_info_dict.get("architecture"),
                        "size_mb": model_info.size_mb,
                        "compatible": validation.get("compatible", True)
                    })

        return suitable_models

    def get_model_statistics(self) -> Dict[str, Any]:
        """Get statistics about downloaded models"""
        total_models = len(self.models)
        total_size_mb = sum(model.size_mb for model in self.models.values())

        valid_models = sum(1 for model in self.models.values()
                         if model.validation_result.get("valid", False))

        compatible_models = sum(1 for model in self.models.values()
                              if model.validation_result.get("compatible", True))

        format_counts = {}
        for model in self.models.values():
            format_type = model.format_type
            format_counts[format_type] = format_counts.get(format_type, 0) + 1

        return {
            "total_models": total_models,
            "total_size_mb": round(total_size_mb, 2),
            "total_size_gb": round(total_size_mb / 1024, 2),
            "valid_models": valid_models,
            "compatible_models": compatible_models,
            "format_distribution": format_counts,
            "queue_size": len(self.download_queue),
            "active_downloads": len(self.active_downloads)
        }

    def cleanup_old_models(self, max_age_days: int = 30):
        """Clean up old models from cache"""
        import time
        current_time = time.time()
        max_age_seconds = max_age_days * 24 * 60 * 60

        models_to_remove = []
        for model_id, model_info in self.models.items():
            if current_time - model_info.download_time > max_age_seconds:
                models_to_remove.append(model_id)

        for model_id in models_to_remove:
            self.remove_model(model_id)
            self.logger.info(f"Cleaned up old model: {model_id}")

def create_training_model_manager(config_path: Optional[str] = None) -> TrainingModelManager:
    """Create and return a training model manager instance"""
    return TrainingModelManager(config_path)

# Example usage and integration helpers
def integrate_with_trainer(trainer_instance):
    """Integrate the model manager with an existing trainer instance"""
    manager = TrainingModelManager()

    # Add model management methods to trainer
    def download_model(model_id, config=None, callback=None):
        return manager.download_model_for_training(model_id, config, callback=callback)

    def get_model_path(model_id):
        return manager.get_model_path(model_id)

    def list_available_models():
        return manager.get_available_models()

    # Attach methods to trainer
    trainer.download_model = download_model
    trainer.get_model_path = get_model_path
    trainer.list_available_models = list_available_models

    return manager

if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)

    manager = TrainingModelManager()

    # Download a model
    def download_callback(info):
        print(f"Download callback: {info}")

    manager.download_model_for_training(
        "facebook/opt-125m",
        callback=download_callback
    )

    # List available models
    models = manager.get_available_models()
    print(f"Available models: {len(models)}")

    # Get statistics
    stats = manager.get_model_statistics()
    print(f"Model statistics: {stats}")