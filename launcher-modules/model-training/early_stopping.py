#!/usr/bin/env python3
"""
Early Stopping and Model Checkpointing System for DuckBot Training
Provides intelligent early stopping and automatic model checkpointing based on training metrics.
"""

import os
import sys
import json
import time
import shutil
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple, Any, Callable
from enum import Enum
from pathlib import Path
import sqlite3
import numpy as np
from contextlib import contextmanager

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    import torch
    import torch.nn as nn
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    import tensorflow as tf
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False

class MetricDirection(Enum):
    """Direction of metric improvement"""
    MINIMIZE = "minimize"  # Lower is better (loss, error)
    MAXIMIZE = "maximize"  # Higher is better (accuracy, f1)

class CheckpointStrategy(Enum):
    """Checkpoint saving strategies"""
    BEST_ONLY = "best_only"           # Only save best model
    ALL_IMPROVEMENTS = "all"          # Save all improvements
    INTERVAL = "interval"             # Save at regular intervals
    BEST_AND_INTERVAL = "both"         # Save best + regular intervals

@dataclass
class EarlyStoppingConfig:
    """Configuration for early stopping"""
    patience: int = 10
    min_delta: float = 0.001
    monitor_metric: str = "val_loss"
    metric_direction: MetricDirection = MetricDirection.MINIMIZE
    restore_best_weights: bool = True
    baseline: Optional[float] = None
    min_epochs: int = 5
    start_from_epoch: int = 0
    verbose: bool = True

@dataclass
class CheckpointConfig:
    """Configuration for model checkpointing"""
    save_dir: str = "checkpoints"
    strategy: CheckpointStrategy = CheckpointStrategy.BEST_AND_INTERVAL
    interval_epochs: int = 5
    max_checkpoints: int = 5
    save_optimizer_state: bool = True
    save_training_state: bool = True
    compress_checkpoints: bool = True
    checkpoint_format: str = "pt"  # pt, h5, safetensors
    include_metadata: bool = True
    backup_on_save: bool = False

@dataclass
class CheckpointMetadata:
    """Metadata for saved checkpoints"""
    checkpoint_id: str
    timestamp: datetime
    epoch: int
    step: int
    metrics: Dict[str, float]
    model_config: Dict[str, Any]
    training_config: Dict[str, Any]
    is_best: bool = False
    file_size: Optional[int] = None
    compressed: bool = False
    checksum: Optional[str] = None

class EarlyStoppingState:
    """Manages early stopping state and logic"""

    def __init__(self, config: EarlyStoppingConfig):
        self.config = config
        self.wait_count = 0
        self.best_metric = float('inf') if config.metric_direction == MetricDirection.MINIMIZE else float('-inf')
        self.best_epoch = 0
        self.best_weights = None
        self.history = []
        self.should_stop = False
        self.stopped_epoch = None

    def update(self, current_metric: float, epoch: int) -> bool:
        """Update early stopping state and return if should stop"""
        if epoch < self.config.start_from_epoch:
            return False

        self.history.append(current_metric)

        # Check if improvement occurred
        improved = self._is_improvement(current_metric)

        if improved:
            self.wait_count = 0
            self.best_metric = current_metric
            self.best_epoch = epoch
            if self.config.verbose:
                print(f"Early stopping: Metric improved to {current_metric:.6f} at epoch {epoch}")
        else:
            self.wait_count += 1
            if self.config.verbose:
                print(f"Early stopping: No improvement, wait count: {self.wait_count}/{self.config.patience}")

        # Check if should stop
        if self.wait_count >= self.config.patience and epoch >= self.config.min_epochs:
            self.should_stop = True
            self.stopped_epoch = epoch
            if self.config.verbose:
                print(f"Early stopping triggered at epoch {epoch}")
                print(f"Best metric: {self.best_metric:.6f} at epoch {self.best_epoch}")

        return self.should_stop

    def _is_improvement(self, current_metric: float) -> bool:
        """Check if current metric is improvement over best"""
        if self.config.metric_direction == MetricDirection.MINIMIZE:
            return current_metric < (self.best_metric - self.config.min_delta)
        else:
            return current_metric > (self.best_metric + self.config.min_delta)

    def get_state(self) -> Dict[str, Any]:
        """Get current state for serialization"""
        return {
            'wait_count': self.wait_count,
            'best_metric': self.best_metric,
            'best_epoch': self.best_epoch,
            'history': self.history,
            'should_stop': self.should_stop,
            'stopped_epoch': self.stopped_epoch
        }

    def load_state(self, state: Dict[str, Any]):
        """Load state from serialized data"""
        self.wait_count = state['wait_count']
        self.best_metric = state['best_metric']
        self.best_epoch = state['best_epoch']
        self.history = state['history']
        self.should_stop = state['should_stop']
        self.stopped_epoch = state['stopped_epoch']

class ModelCheckpointManager:
    """Manages model checkpointing and storage"""

    def __init__(self, config: CheckpointConfig):
        self.config = config
        self.save_dir = Path(config.save_dir)
        self.save_dir.mkdir(parents=True, exist_ok=True)
        self.checkpoints = {}
        self.best_checkpoint_id = None

        # Initialize database
        self.db_path = self.save_dir / "checkpoints.db"
        self._init_database()

        # Load existing checkpoints
        self._load_existing_checkpoints()

    def _init_database(self):
        """Initialize checkpoint database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS checkpoints (
                    checkpoint_id TEXT PRIMARY KEY,
                    timestamp TEXT,
                    epoch INTEGER,
                    step INTEGER,
                    metrics TEXT,
                    is_best BOOLEAN,
                    file_path TEXT,
                    file_size INTEGER,
                    compressed BOOLEAN,
                    checksum TEXT,
                    metadata TEXT
                )
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_epoch ON checkpoints(epoch)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_is_best ON checkpoints(is_best)
            """)

    def _load_existing_checkpoints(self):
        """Load existing checkpoints from disk"""
        checkpoint_files = list(self.save_dir.glob("checkpoint_*.pt"))
        checkpoint_files.extend(list(self.save_dir.glob("checkpoint_*.h5")))

        for checkpoint_file in checkpoint_files:
            checkpoint_id = checkpoint_file.stem.replace("checkpoint_", "")
            try:
                metadata = self._load_metadata(checkpoint_file)
                if metadata:
                    self.checkpoints[checkpoint_id] = metadata
                    if metadata.is_best:
                        self.best_checkpoint_id = checkpoint_id
            except Exception as e:
                logging.warning(f"Failed to load checkpoint metadata for {checkpoint_file}: {e}")

    def save_checkpoint(self, model: Any, optimizer: Any, scheduler: Any,
                       epoch: int, step: int, metrics: Dict[str, float],
                       training_config: Dict[str, Any], is_best: bool = False) -> str:
        """Save model checkpoint"""
        checkpoint_id = f"ckpt_{epoch}_{step}_{int(time.time())}"

        # Create checkpoint directory
        checkpoint_dir = self.save_dir / checkpoint_id
        checkpoint_dir.mkdir(exist_ok=True)

        # Prepare checkpoint data
        checkpoint_data = {
            'epoch': epoch,
            'step': step,
            'model_state_dict': self._get_model_state(model),
            'metrics': metrics,
            'timestamp': datetime.now().isoformat()
        }

        if self.config.save_optimizer_state and optimizer is not None:
            checkpoint_data['optimizer_state_dict'] = self._get_optimizer_state(optimizer)

        if self.config.save_training_state and scheduler is not None:
            checkpoint_data['scheduler_state_dict'] = self._get_scheduler_state(scheduler)

        # Save checkpoint
        checkpoint_path = checkpoint_dir / f"checkpoint.{self.config.checkpoint_format}"
        self._save_checkpoint_data(checkpoint_data, checkpoint_path)

        # Create metadata
        metadata = CheckpointMetadata(
            checkpoint_id=checkpoint_id,
            timestamp=datetime.now(),
            epoch=epoch,
            step=step,
            metrics=metrics,
            model_config=self._get_model_config(model),
            training_config=training_config,
            is_best=is_best,
            file_size=checkpoint_path.stat().st_size,
            compressed=self.config.compress_checkpoints
        )

        # Save metadata
        self._save_metadata(metadata, checkpoint_dir)

        # Update database
        self._save_to_database(metadata, checkpoint_path)

        # Update best checkpoint
        if is_best:
            self.best_checkpoint_id = checkpoint_id

        # Manage checkpoint count
        self._manage_checkpoint_count()

        return checkpoint_id

    def load_checkpoint(self, checkpoint_id: str) -> Dict[str, Any]:
        """Load checkpoint data"""
        checkpoint_dir = self.save_dir / checkpoint_id
        checkpoint_path = checkpoint_dir / f"checkpoint.{self.config.checkpoint_format}"

        if not checkpoint_path.exists():
            raise FileNotFoundError(f"Checkpoint not found: {checkpoint_path}")

        return self._load_checkpoint_data(checkpoint_path)

    def get_best_checkpoint(self) -> Optional[str]:
        """Get ID of best checkpoint"""
        return self.best_checkpoint_id

    def list_checkpoints(self) -> List[CheckpointMetadata]:
        """List all available checkpoints"""
        return list(self.checkpoints.values())

    def delete_checkpoint(self, checkpoint_id: str):
        """Delete a checkpoint"""
        checkpoint_dir = self.save_dir / checkpoint_id
        if checkpoint_dir.exists():
            shutil.rmtree(checkpoint_dir)

        if checkpoint_id in self.checkpoints:
            del self.checkpoints[checkpoint_id]

        if checkpoint_id == self.best_checkpoint_id:
            self.best_checkpoint_id = None

        # Remove from database
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM checkpoints WHERE checkpoint_id = ?", (checkpoint_id,))

    def _get_model_state(self, model: Any) -> Dict[str, Any]:
        """Get model state dict"""
        if TORCH_AVAILABLE and hasattr(model, 'state_dict'):
            return model.state_dict()
        elif TENSORFLOW_AVAILABLE and hasattr(model, 'get_weights'):
            return {'weights': model.get_weights()}
        else:
            return {}

    def _get_optimizer_state(self, optimizer: Any) -> Dict[str, Any]:
        """Get optimizer state dict"""
        if TORCH_AVAILABLE and hasattr(optimizer, 'state_dict'):
            return optimizer.state_dict()
        else:
            return {}

    def _get_scheduler_state(self, scheduler: Any) -> Dict[str, Any]:
        """Get scheduler state dict"""
        if TORCH_AVAILABLE and hasattr(scheduler, 'state_dict'):
            return scheduler.state_dict()
        else:
            return {}

    def _get_model_config(self, model: Any) -> Dict[str, Any]:
        """Get model configuration"""
        config = {}
        if hasattr(model, 'config'):
            config.update(model.config)
        if hasattr(model, '__dict__'):
            for key, value in model.__dict__.items():
                if not key.startswith('_'):
                    try:
                        config[key] = str(value)
                    except:
                        config[key] = f"<{type(value).__name__}>"
        return config

    def _save_checkpoint_data(self, data: Dict[str, Any], path: Path):
        """Save checkpoint data to file"""
        if self.config.checkpoint_format == 'pt' and TORCH_AVAILABLE:
            torch.save(data, path)
        elif self.config.checkpoint_format == 'h5' and TENSORFLOW_AVAILABLE:
            # Convert to TensorFlow format
            tf_model = tf.keras.Model.from_config(data.get('model_config', {}))
            if 'weights' in data:
                tf_model.set_weights(data['weights'])
            tf_model.save(path)
        else:
            # Fallback to JSON
            with open(path.with_suffix('.json'), 'w') as f:
                json.dump(data, f, indent=2, default=str)

    def _load_checkpoint_data(self, path: Path) -> Dict[str, Any]:
        """Load checkpoint data from file"""
        if self.config.checkpoint_format == 'pt' and TORCH_AVAILABLE:
            return torch.load(path, map_location='cpu')
        elif self.config.checkpoint_format == 'h5' and TENSORFLOW_AVAILABLE:
            return tf.keras.models.load_model(path)
        else:
            # Fallback to JSON
            json_path = path.with_suffix('.json')
            if json_path.exists():
                with open(json_path, 'r') as f:
                    return json.load(f)
            else:
                return {}

    def _save_metadata(self, metadata: CheckpointMetadata, checkpoint_dir: Path):
        """Save checkpoint metadata"""
        metadata_path = checkpoint_dir / "metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(asdict(metadata), f, indent=2, default=str)

    def _load_metadata(self, checkpoint_dir: Path) -> Optional[CheckpointMetadata]:
        """Load checkpoint metadata"""
        metadata_path = checkpoint_dir / "metadata.json"
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                data = json.load(f)
                # Convert timestamp back to datetime
                data['timestamp'] = datetime.fromisoformat(data['timestamp'])
                return CheckpointMetadata(**data)
        return None

    def _save_to_database(self, metadata: CheckpointMetadata, checkpoint_path: Path):
        """Save checkpoint info to database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO checkpoints (
                    checkpoint_id, timestamp, epoch, step, metrics, is_best,
                    file_path, file_size, compressed, checksum, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                metadata.checkpoint_id,
                metadata.timestamp.isoformat(),
                metadata.epoch,
                metadata.step,
                json.dumps(metadata.metrics),
                metadata.is_best,
                str(checkpoint_path),
                metadata.file_size,
                metadata.compressed,
                metadata.checksum,
                json.dumps(asdict(metadata), default=str)
            ))

    def _manage_checkpoint_count(self):
        """Manage maximum number of checkpoints"""
        if len(self.checkpoints) > self.config.max_checkpoints:
            # Sort by epoch and delete oldest
            sorted_checkpoints = sorted(self.checkpoints.values(), key=lambda x: x.epoch)
            to_delete = len(self.checkpoints) - self.config.max_checkpoints

            for i in range(to_delete):
                checkpoint = sorted_checkpoints[i]
                if checkpoint.checkpoint_id != self.best_checkpoint_id:
                    self.delete_checkpoint(checkpoint.checkpoint_id)

class TrainingCallback:
    """Base class for training callbacks"""

    def on_epoch_start(self, epoch: int, logs: Dict[str, Any]):
        """Called at the start of an epoch"""
        pass

    def on_epoch_end(self, epoch: int, logs: Dict[str, Any]):
        """Called at the end of an epoch"""
        pass

    def on_batch_start(self, batch: int, logs: Dict[str, Any]):
        """Called at the start of a batch"""
        pass

    def on_batch_end(self, batch: int, logs: Dict[str, Any]):
        """Called at the end of a batch"""
        pass

    def on_train_start(self, logs: Dict[str, Any]):
        """Called at the start of training"""
        pass

    def on_train_end(self, logs: Dict[str, Any]):
        """Called at the end of training"""
        pass

class EarlyStoppingCallback(TrainingCallback):
    """Early stopping callback"""

    def __init__(self, config: EarlyStoppingConfig):
        self.config = config
        self.state = EarlyStoppingState(config)

    def on_epoch_end(self, epoch: int, logs: Dict[str, Any]):
        """Check early stopping condition"""
        if self.config.monitor_metric in logs:
            current_metric = logs[self.config.monitor_metric]
            should_stop = self.state.update(current_metric, epoch)

            if should_stop and self.config.restore_best_weights:
                # Signal to restore best weights
                logs['restore_best_weights'] = True
                logs['best_epoch'] = self.state.best_epoch

    def get_state(self) -> Dict[str, Any]:
        """Get current state"""
        return self.state.get_state()

    def load_state(self, state: Dict[str, Any]):
        """Load state"""
        self.state.load_state(state)

class ModelCheckpointCallback(TrainingCallback):
    """Model checkpointing callback"""

    def __init__(self, config: CheckpointConfig, checkpoint_manager: ModelCheckpointManager):
        self.config = config
        self.checkpoint_manager = checkpoint_manager
        self.best_metric = float('inf')
        self.last_save_epoch = 0

    def on_epoch_end(self, epoch: int, logs: Dict[str, Any]):
        """Save checkpoint based on strategy"""
        current_loss = logs.get('loss', 0)
        current_metrics = {k: v for k, v in logs.items() if isinstance(v, (int, float))}

        should_save = False
        is_best = False

        if self.config.strategy in [CheckpointStrategy.BEST_ONLY, CheckpointStrategy.BEST_AND_INTERVAL]:
            if current_loss < self.best_metric:
                self.best_metric = current_loss
                is_best = True
                should_save = True

        if self.config.strategy in [CheckpointStrategy.INTERVAL, CheckpointStrategy.BEST_AND_INTERVAL]:
            if epoch - self.last_save_epoch >= self.config.interval_epochs:
                should_save = True
                self.last_save_epoch = epoch

        if self.config.strategy == CheckpointStrategy.ALL_IMPROVEMENTS:
            should_save = True

        if should_save:
            # In real implementation, you'd pass the actual model, optimizer, etc.
            # For now, we'll simulate with None values
            checkpoint_id = self.checkpoint_manager.save_checkpoint(
                model=None,
                optimizer=None,
                scheduler=None,
                epoch=epoch,
                step=logs.get('step', 0),
                metrics=current_metrics,
                training_config={},
                is_best=is_best
            )

            if is_best:
                print(f"✓ Saved best checkpoint: {checkpoint_id}")
            else:
                print(f"✓ Saved checkpoint: {checkpoint_id}")

class EarlyStoppingCheckpointManager:
    """Main manager for early stopping and checkpointing"""

    def __init__(self,
                 early_stopping_config: EarlyStoppingConfig = None,
                 checkpoint_config: CheckpointConfig = None):

        self.early_stopping_config = early_stopping_config or EarlyStoppingConfig()
        self.checkpoint_config = checkpoint_config or CheckpointConfig()

        # Initialize components
        self.early_stopping_state = EarlyStoppingState(self.early_stopping_config)
        self.checkpoint_manager = ModelCheckpointManager(self.checkpoint_config)

        # Initialize callbacks
        self.early_stopping_callback = EarlyStoppingCallback(self.early_stopping_config)
        self.checkpoint_callback = ModelCheckpointCallback(self.checkpoint_config, self.checkpoint_manager)

        self.callbacks = [self.early_stopping_callback, self.checkpoint_callback]

    def add_callback(self, callback: TrainingCallback):
        """Add custom callback"""
        self.callbacks.append(callback)

    def on_epoch_start(self, epoch: int, logs: Dict[str, Any]):
        """Handle epoch start"""
        for callback in self.callbacks:
            callback.on_epoch_start(epoch, logs)

    def on_epoch_end(self, epoch: int, logs: Dict[str, Any]):
        """Handle epoch end"""
        for callback in self.callbacks:
            callback.on_epoch_end(epoch, logs)

    def on_batch_start(self, batch: int, logs: Dict[str, Any]):
        """Handle batch start"""
        for callback in self.callbacks:
            callback.on_batch_start(batch, logs)

    def on_batch_end(self, batch: int, logs: Dict[str, Any]):
        """Handle batch end"""
        for callback in self.callbacks:
            callback.on_batch_end(batch, logs)

    def on_train_start(self, logs: Dict[str, Any]):
        """Handle training start"""
        for callback in self.callbacks:
            callback.on_train_start(logs)

    def on_train_end(self, logs: Dict[str, Any]):
        """Handle training end"""
        for callback in self.callbacks:
            callback.on_train_end(logs)

    def should_stop(self) -> bool:
        """Check if training should stop"""
        return self.early_stopping_state.should_stop

    def get_best_epoch(self) -> int:
        """Get best epoch number"""
        return self.early_stopping_state.best_epoch

    def get_best_checkpoint(self) -> Optional[str]:
        """Get best checkpoint ID"""
        return self.checkpoint_manager.get_best_checkpoint()

    def get_state(self) -> Dict[str, Any]:
        """Get current state for persistence"""
        return {
            'early_stopping': self.early_stopping_callback.get_state(),
            'checkpoints': {
                checkpoint_id: asdict(metadata)
                for checkpoint_id, metadata in self.checkpoint_manager.checkpoints.items()
            }
        }

    def load_state(self, state: Dict[str, Any]):
        """Load state from persistence"""
        if 'early_stopping' in state:
            self.early_stopping_callback.load_state(state['early_stopping'])

# Example usage
def demo_early_stopping():
    """Demonstrate early stopping functionality"""
    print("🎯 Early Stopping and Checkpointing Demo")
    print("=" * 50)

    # Create manager with default config
    manager = EarlyStoppingCheckpointManager()

    # Simulate training epochs
    print("\n🚀 Simulating training with early stopping...")

    training_logs = []
    for epoch in range(20):
        # Simulate decreasing loss with some noise
        base_loss = 2.0 * (0.85 ** epoch) + np.random.normal(0, 0.05)
        val_loss = base_loss * 1.2 + np.random.normal(0, 0.03)

        logs = {
            'epoch': epoch,
            'loss': float(base_loss),
            'val_loss': float(val_loss),
            'accuracy': float(0.9 - base_loss * 0.1),
            'val_accuracy': float(0.85 - val_loss * 0.1)
        }

        print(f"Epoch {epoch:2d}: loss={base_loss:.4f}, val_loss={val_loss:.4f}, "
              f"accuracy={logs['accuracy']:.4f}, val_accuracy={logs['val_accuracy']:.4f}")

        # Handle epoch end
        manager.on_epoch_end(epoch, logs)
        training_logs.append(logs)

        # Check if should stop
        if manager.should_stop():
            print(f"\n⏹️  Early stopping triggered at epoch {epoch}")
            print(f"Best epoch: {manager.get_best_epoch()}")
            break

    print(f"\n📊 Training Summary:")
    print(f"Total epochs: {len(training_logs)}")
    print(f"Best epoch: {manager.get_best_epoch()}")

    # Show checkpoints
    checkpoints = manager.checkpoint_manager.list_checkpoints()
    print(f"\n💾 Checkpoints created: {len(checkpoints)}")
    for checkpoint in checkpoints[-3:]:  # Show last 3
        print(f"  • {checkpoint.checkpoint_id}: epoch={checkpoint.epoch}, "
              f"loss={checkpoint.metrics.get('loss', 'N/A'):.4f}, "
              f"best={checkpoint.is_best}")

    # Show best checkpoint
    best_checkpoint = manager.get_best_checkpoint()
    if best_checkpoint:
        print(f"\n🏆 Best checkpoint: {best_checkpoint}")

    return manager

if __name__ == "__main__":
    demo_early_stopping()