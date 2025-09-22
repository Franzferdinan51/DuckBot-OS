#!/usr/bin/env python3
"""
Test suite for the training integration module
"""

import os
import sys
import json
import tempfile
import shutil
import unittest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import logging

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from training_integration import (
    TrainingModelManager,
    ModelDownloadRequest,
    ModelSource,
    ModelInfo,
    integrate_with_trainer
)

class TestTrainingModelManager(unittest.TestCase):
    """Test the TrainingModelManager class"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "test_config.json"

        # Create test config
        config = {
            "cache": {
                "default_dir": self.temp_dir
            }
        }
        with open(self.config_path, 'w') as f:
            json.dump(config, f)

        self.manager = TrainingModelManager(str(self.config_path))

    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_initialization(self):
        """Test manager initialization"""
        self.assertIsNotNone(self.manager.config_manager)
        self.assertIsNotNone(self.manager.downloader)
        self.assertIsNotNone(self.manager.validator)
        self.assertIsInstance(self.manager.models, dict)
        self.assertIsInstance(self.manager.download_queue, list)

    def test_download_model_for_training(self):
        """Test downloading a model for training"""
        callback = Mock()

        # Mock the downloader
        mock_model_path = Path(self.temp_dir) / "test_model"
        mock_model_path.mkdir()
        (mock_model_path / "config.json").write_text('{"model_type": "test"}')

        with patch.object(self.manager.downloader, 'download_model', return_value=str(mock_model_path)):
            with patch.object(self.manager.validator, 'validate_model_structure', return_value={
                "valid": True,
                "issues": [],
                "warnings": [],
                "model_info": {}
            }):
                result = self.manager.download_model_for_training(
                    "test/model",
                    callback=callback
                )

                self.assertTrue(result)
                callback.assert_called()

    def test_get_available_models(self):
        """Test getting list of available models"""
        # Add a test model
        model_path = Path(self.temp_dir) / "test_model"
        model_path.mkdir()
        (model_path / "config.json").write_text('{"model_type": "test"}')

        model_info = ModelInfo(
            model_id="test/model",
            source=ModelSource.CACHE,
            path=model_path,
            format_type="huggingface",
            size_mb=10.0,
            validation_result={"valid": True, "issues": [], "warnings": []},
            download_time=1234567890,
            metadata={}
        )

        self.manager.models["test/model"] = model_info

        # Get available models
        models = self.manager.get_available_models()

        self.assertEqual(len(models), 1)
        self.assertEqual(models[0]["model_id"], "test/model")
        self.assertEqual(models[0]["source"], "cache")
        self.assertTrue(models[0]["valid"])

    def test_get_model_path(self):
        """Test getting model path"""
        model_path = Path(self.temp_dir) / "test_model"
        model_path.mkdir()

        model_info = ModelInfo(
            model_id="test/model",
            source=ModelSource.LOCAL,
            path=model_path,
            format_type="huggingface",
            size_mb=10.0,
            validation_result={"valid": True, "issues": [], "warnings": []},
            download_time=1234567890,
            metadata={}
        )

        self.manager.models["test/model"] = model_info

        # Get model path
        path = self.manager.get_model_path("test/model")
        self.assertEqual(path, model_path)

        # Test non-existent model
        path = self.manager.get_model_path("nonexistent/model")
        self.assertIsNone(path)

    def test_validate_model_for_training(self):
        """Test validating a model for training"""
        model_path = Path(self.temp_dir) / "test_model"
        model_path.mkdir()
        (model_path / "config.json").write_text('{"model_type": "bert", "architectures": ["BertModel"]}')

        model_info = ModelInfo(
            model_id="test/model",
            source=ModelSource.HUGGINGFACE,
            path=model_path,
            format_type="huggingface",
            size_mb=10.0,
            validation_result={"valid": True, "issues": [], "warnings": []},
            download_time=1234567890,
            metadata={}
        )

        self.manager.models["test/model"] = model_info

        # Validate with requirements
        requirements = {
            "model_type": "bert",
            "architecture": "BertModel"
        }

        result = self.manager.validate_model_for_training("test/model", requirements)

        self.assertTrue(result["valid"])
        self.assertTrue(result["compatible"])

        # Test non-existent model
        result = self.manager.validate_model_for_training("nonexistent/model")
        self.assertFalse(result["valid"])
        self.assertEqual(result["error"], "Model not found")

    def test_remove_model(self):
        """Test removing a model"""
        model_path = Path(self.temp_dir) / "test_model"
        model_path.mkdir()
        (model_path / "config.json").write_text('{"model_type": "test"}')

        model_info = ModelInfo(
            model_id="test/model",
            source=ModelSource.CACHE,
            path=model_path,
            format_type="huggingface",
            size_mb=10.0,
            validation_result={"valid": True, "issues": [], "warnings": []},
            download_time=1234567890,
            metadata={}
        )

        self.manager.models["test/model"] = model_info

        # Remove model
        result = self.manager.remove_model("test/model")

        self.assertTrue(result)
        self.assertNotIn("test/model", self.manager.models)

        # Test removing non-existent model
        result = self.manager.remove_model("nonexistent/model")
        self.assertFalse(result)

    def test_get_download_status(self):
        """Test getting download status"""
        # Test already downloaded model
        model_path = Path(self.temp_dir) / "test_model"
        model_path.mkdir()

        model_info = ModelInfo(
            model_id="test/model",
            source=ModelSource.CACHE,
            path=model_path,
            format_type="huggingface",
            size_mb=10.0,
            validation_result={"valid": True, "issues": [], "warnings": []},
            download_time=1234567890,
            metadata={}
        )

        self.manager.models["test/model"] = model_info

        status = self.manager.get_download_status("test/model")
        self.assertEqual(status["status"], "completed")
        self.assertEqual(status["model_id"], "test/model")

        # Test queued model
        request = ModelDownloadRequest(
            model_id="queued/model",
            source=ModelSource.HUGGINGFACE,
            priority=1
        )

        self.manager.download_queue.append(request)

        status = self.manager.get_download_status("queued/model")
        self.assertEqual(status["status"], "queued")
        self.assertEqual(status["priority"], 1)

        # Test non-existent model
        status = self.manager.get_download_status("nonexistent/model")
        self.assertIsNone(status)

    def test_get_training_models_by_type(self):
        """Test getting models by training type"""
        # Add test models
        for i, (model_type, architecture) in enumerate([
            ("bert", "BertModel"),
            ("gpt2", "GPT2LMHeadModel"),
            ("roberta", "RobertaModel")
        ]):
            model_path = Path(self.temp_dir) / f"model_{i}"
            model_path.mkdir()
            (model_path / "config.json").write_text(
                json.dumps({"model_type": model_type, "architectures": [architecture]})
            )

            model_info = ModelInfo(
                model_id=f"test/model_{i}",
                source=ModelSource.CACHE,
                path=model_path,
                format_type="huggingface",
                size_mb=10.0,
                validation_result={
                    "valid": True,
                    "issues": [],
                    "warnings": [],
                    "model_info": {"model_type": model_type, "architecture": architecture}
                },
                download_time=1234567890,
                metadata={}
            )

            self.manager.models[f"test/model_{i}"] = model_info

        # Get bert models
        bert_models = self.manager.get_training_models_by_type("bert")
        self.assertEqual(len(bert_models), 1)
        self.assertEqual(bert_models[0]["model_id"], "test/model_0")

        # Get gpt2 models
        gpt2_models = self.manager.get_training_models_by_type("gpt2")
        self.assertEqual(len(gpt2_models), 1)
        self.assertEqual(gpt2_models[0]["model_id"], "test/model_1")

    def test_get_model_statistics(self):
        """Test getting model statistics"""
        # Add test models
        for i in range(3):
            model_path = Path(self.temp_dir) / f"model_{i}"
            model_path.mkdir()
            (model_path / "config.json").write_text('{"model_type": "test"}')

            model_info = ModelInfo(
                model_id=f"test/model_{i}",
                source=ModelSource.CACHE,
                path=model_path,
                format_type="huggingface",
                size_mb=10.0 * (i + 1),
                validation_result={"valid": True, "issues": [], "warnings": []},
                download_time=1234567890 + i,
                metadata={}
            )

            self.manager.models[f"test/model_{i}"] = model_info

        # Add queued download
        request = ModelDownloadRequest(
            model_id="queued/model",
            source=ModelSource.HUGGINGFACE,
            priority=1
        )
        self.manager.download_queue.append(request)

        # Get statistics
        stats = self.manager.get_model_statistics()

        self.assertEqual(stats["total_models"], 3)
        self.assertEqual(stats["total_size_mb"], 60.0)  # 10 + 20 + 30
        self.assertEqual(stats["valid_models"], 3)
        self.assertEqual(stats["compatible_models"], 3)
        self.assertEqual(stats["queue_size"], 1)
        self.assertEqual(stats["format_distribution"]["huggingface"], 3)

class TestModelDownloadRequest(unittest.TestCase):
    """Test ModelDownloadRequest dataclass"""

    def test_default_values(self):
        """Test default request values"""
        request = ModelDownloadRequest(
            model_id="test/model",
            source=ModelSource.HUGGINGFACE
        )

        self.assertEqual(request.model_id, "test/model")
        self.assertEqual(request.source, ModelSource.HUGGINGFACE)
        self.assertIsNone(request.config)
        self.assertEqual(request.priority, 0)
        self.assertIsNone(request.callback)
        self.assertIsNone(request.user_data)

    def test_with_values(self):
        """Test request with custom values"""
        callback = Mock()
        request = ModelDownloadRequest(
            model_id="test/model",
            source=ModelSource.LOCAL,
            config={"convert_to_gguf": True},
            priority=5,
            callback=callback,
            user_data={"key": "value"}
        )

        self.assertEqual(request.model_id, "test/model")
        self.assertEqual(request.source, ModelSource.LOCAL)
        self.assertEqual(request.config, {"convert_to_gguf": True})
        self.assertEqual(request.priority, 5)
        self.assertEqual(request.callback, callback)
        self.assertEqual(request.user_data, {"key": "value"})

class TestIntegrationHelpers(unittest.TestCase):
    """Test integration helper functions"""

    def test_integrate_with_trainer(self):
        """Test trainer integration"""
        # Mock trainer
        trainer = Mock()

        # Integrate
        manager = integrate_with_trainer(trainer)

        # Check methods were added
        self.assertTrue(hasattr(trainer, 'download_model'))
        self.assertTrue(hasattr(trainer, 'get_model_path'))
        self.assertTrue(hasattr(trainer, 'list_available_models'))

        # Check manager was returned
        self.assertIsInstance(manager, TrainingModelManager)

class TestEndToEnd(unittest.TestCase):
    """End-to-end integration tests"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "test_config.json"

        config = {
            "cache": {
                "default_dir": self.temp_dir
            }
        }
        with open(self.config_path, 'w') as f:
            json.dump(config, f)

        self.manager = TrainingModelManager(str(self.config_path))

    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_full_download_workflow(self):
        """Test complete download workflow"""
        callback_results = []

        def callback(info):
            callback_results.append(info)

        # Mock successful download
        mock_model_path = Path(self.temp_dir) / "downloaded_model"
        mock_model_path.mkdir()
        (mock_model_path / "config.json").write_text('{"model_type": "bert", "architectures": ["BertModel"]}')

        with patch.object(self.manager.downloader, 'download_model', return_value=str(mock_model_path)):
            with patch.object(self.manager.validator, 'validate_model_structure', return_value={
                "valid": True,
                "issues": [],
                "warnings": [],
                "model_info": {"model_type": "bert", "architecture": "BertModel"}
            }):
                # Start download
                result = self.manager.download_model_for_training(
                    "facebook/bert-base-uncased",
                    callback=callback
                )

                self.assertTrue(result)

                # Check download was queued
                self.assertEqual(len(self.manager.download_queue), 1)

                # Process queue (simulated)
                request = self.manager.download_queue.pop(0)
                self.manager._download_model(request)

                # Check model is now available
                self.assertIn("facebook/bert-base-uncased", self.manager.models)

                # Check model is in available models list
                available_models = self.manager.get_available_models()
                self.assertEqual(len(available_models), 1)
                self.assertEqual(available_models[0]["model_id"], "facebook/bert-base-uncased")

                # Check validation
                validation_result = self.manager.validate_model_for_training(
                    "facebook/bert-base-uncased",
                    {"model_type": "bert"}
                )
                self.assertTrue(validation_result["valid"])
                self.assertTrue(validation_result["compatible"])

if __name__ == '__main__':
    # Configure logging for tests
    logging.basicConfig(level=logging.DEBUG)

    # Run tests
    unittest.main(verbosity=2)